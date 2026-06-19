"""Orchestrate model-based evidence review with validation, retry, and fallback."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.cache import ModelResponseCache
from src.constants import (
    CLAIM_STATUS_VALUES,
    ISSUE_TYPE_VALUES,
    OBJECT_PART_VALUES,
    OUTPUT_COLUMNS,
    RISK_FLAG_VALUES,
    SEVERITY_VALUES,
)
from src.image_utils import load_images_for_model
from src.io_utils import get_image_ids
from src.model_provider import ModelProvider
from src.post_processing import apply_post_processing
from src.prompts import PROMPT_VERSION, get_repair_prompt, get_system_prompt, get_user_prompt
from src.severity import calibrate_severity


class ModelReviewError(Exception):
    """Raised when model review fails and fallback is needed."""


def _extract_json(text: str) -> str:
    """Extract the first JSON object from a string, tolerating markdown fences."""
    # Remove markdown fences
    text = re.sub(r"^```json\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())

    # Find first balanced JSON object
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")

    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start=start):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"' and (i == start or text[i - 1] != "\\"):
            in_string = not in_string
            continue
        if not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

    raise ValueError("Unbalanced JSON object in response")


def _parse_model_json(response: str) -> Dict[str, Any]:
    """Parse model response into a dict."""
    json_text = _extract_json(response)
    return json.loads(json_text)


def _normalize_list_field(value: Any) -> List[str]:
    """Normalize a field that may be a string or list into a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.split(";") if v.strip()]
    return []


def _to_string(value: Any) -> str:
    """Convert a value to a lowercase string."""
    return str(value).strip().lower()


def _normalize_model_output(
    raw: Dict[str, Any],
    claim_object: str,
    valid_image_ids: List[str],
) -> Tuple[Dict[str, str], List[str]]:
    """Normalize and validate model JSON into a row-like dict.

    Returns (normalized_dict, validation_errors).
    """
    errors: List[str] = []
    out: Dict[str, str] = {}

    # evidence_standard_met
    esm = _to_string(raw.get("evidence_standard_met"))
    if esm not in {"true", "false"}:
        errors.append(f"Invalid evidence_standard_met '{esm}'")
        out["evidence_standard_met"] = "false"
    else:
        out["evidence_standard_met"] = esm

    # evidence_standard_met_reason
    reason = str(raw.get("evidence_standard_met_reason", "")).strip()
    out["evidence_standard_met_reason"] = reason or "No reason provided."

    # issue_type
    issue = _to_string(raw.get("issue_type"))
    if issue not in ISSUE_TYPE_VALUES:
        errors.append(f"Invalid issue_type '{issue}'")
        issue = "unknown"
    out["issue_type"] = issue

    # object_part
    part = _to_string(raw.get("object_part"))
    allowed_parts = OBJECT_PART_VALUES.get(claim_object, {"unknown"})
    if part not in allowed_parts:
        errors.append(f"Invalid object_part '{part}' for {claim_object}")
        part = "unknown"
    out["object_part"] = part

    # claim_status
    status = _to_string(raw.get("claim_status"))
    if status not in CLAIM_STATUS_VALUES:
        errors.append(f"Invalid claim_status '{status}'")
        status = "not_enough_information"
    out["claim_status"] = status

    # claim_status_justification
    just = str(raw.get("claim_status_justification", "")).strip()
    out["claim_status_justification"] = just or "No justification provided."

    # severity
    severity = _to_string(raw.get("severity"))
    if severity not in SEVERITY_VALUES:
        errors.append(f"Invalid severity '{severity}'")
        severity = "unknown"
    out["severity"] = severity

    # valid_image
    valid = _to_string(raw.get("valid_image"))
    if valid not in {"true", "false"}:
        errors.append(f"Invalid valid_image '{valid}'")
        valid = "false"
    out["valid_image"] = valid

    # risk_flags
    flags = _normalize_list_field(raw.get("risk_flags"))
    cleaned_flags: List[str] = []
    for flag in flags:
        flag_lc = flag.lower()
        if flag_lc in RISK_FLAG_VALUES:
            cleaned_flags.append(flag_lc)
        else:
            errors.append(f"Invalid risk_flag '{flag}'")
    if not cleaned_flags:
        cleaned_flags = ["none"]
    out["risk_flags"] = ";".join(cleaned_flags)

    # supporting_image_ids
    ids = _normalize_list_field(raw.get("supporting_image_ids"))
    cleaned_ids: List[str] = []
    valid_ids_set = set(valid_image_ids)
    for img_id in ids:
        img_id_lc = img_id.lower()
        if img_id_lc == "none":
            continue
        if img_id in valid_ids_set:
            cleaned_ids.append(img_id)
        else:
            errors.append(f"Invalid supporting_image_id '{img_id}'")
    if not cleaned_ids:
        cleaned_ids = ["none"]
    out["supporting_image_ids"] = ";".join(cleaned_ids)

    return out, errors


def _safe_fallback_row(
    claim_row: Dict[str, str],
    extra_flags: Optional[List[str]] = None,
    reason: str = "Model review failed or returned invalid output; falling back to safe defaults.",
) -> Dict[str, str]:
    """Produce a safe fallback output row."""
    flags = ["manual_review_required"]
    if extra_flags:
        flags.extend(extra_flags)
    return {
        "user_id": claim_row["user_id"],
        "image_paths": claim_row["image_paths"],
        "user_claim": claim_row["user_claim"],
        "claim_object": claim_row["claim_object"],
        "evidence_standard_met": "false",
        "evidence_standard_met_reason": reason,
        "risk_flags": ";".join(flags),
        "issue_type": "unknown",
        "object_part": "unknown",
        "claim_status": "not_enough_information",
        "claim_status_justification": "Safe fallback due to model failure or invalid output.",
        "supporting_image_ids": "none",
        "valid_image": "false",
        "severity": "unknown",
    }


def _model_output_to_full_row(
    normalized: Dict[str, str],
    claim_row: Dict[str, str],
) -> Dict[str, str]:
    """Combine normalized model output with input identity fields."""
    return {
        "user_id": claim_row["user_id"],
        "image_paths": claim_row["image_paths"],
        "user_claim": claim_row["user_claim"],
        "claim_object": claim_row["claim_object"],
        **normalized,
    }


def review_claim_with_model(
    claim_row: Dict[str, str],
    provider: ModelProvider,
    cache: Optional[ModelResponseCache] = None,
    evidence_requirements: Optional[List[Dict[str, str]]] = None,
    user_history_summary: Optional[str] = None,
    user_history: Optional[Dict[str, Dict[str, str]]] = None,
    base_dir: str = ".",
    max_retries: int = 1,
) -> Dict[str, str]:
    """Review a single claim using the vision model with retry and fallback."""
    image_ids = get_image_ids(claim_row.get("image_paths", ""))
    user_id = claim_row.get("user_id", "")
    user_history_row = user_history.get(user_id) if user_history else None
    system_prompt = get_system_prompt(claim_row.get("claim_object", ""))
    user_prompt = get_user_prompt(
        claim_row,
        image_ids,
        evidence_requirements=evidence_requirements,
        user_history_summary=user_history_summary,
    )

    data_urls, image_errors = load_images_for_model(
        claim_row.get("image_paths", ""), base_dir=base_dir
    )

    extra_flags: List[str] = []
    if image_errors:
        extra_flags.append("damage_not_visible")
        extra_flags.append("manual_review_required")

    # Try cache first
    cached_response: Optional[str] = None
    if cache is not None:
        cached_response = cache.get(
            claim_row, image_ids, provider_name(provider), PROMPT_VERSION
        )

    response: Optional[str] = cached_response

    if response is None:
        try:
            response = provider.complete(system_prompt, user_prompt, data_urls)
        except Exception as exc:
            # Model call failed entirely -> safe fallback
            return _safe_fallback_row(
                claim_row,
                extra_flags=extra_flags,
                reason=f"Model call failed: {exc}",
            )

        if cache is not None and response is not None:
            cache.set(
                claim_row, image_ids, provider_name(provider), PROMPT_VERSION, response
            )

    assert response is not None

    # Parse and normalize, with optional repair retry
    attempts = 0
    while attempts <= max_retries:
        try:
            raw = _parse_model_json(response)
            normalized, norm_errors = _normalize_model_output(
                raw, claim_row.get("claim_object", ""), image_ids
            )

            if not norm_errors:
                # Apply deterministic post-processing (history, guardrails,
                # package contents rule, mismatch detection, risk flag merge).
                apply_post_processing(normalized, claim_row, user_history_row)

                # Calibrate severity after deterministic changes to labels.
                normalized["severity"] = calibrate_severity(normalized, claim_row)

                # Add any image-related flags if model did not include them
                if extra_flags and normalized["risk_flags"] != "none":
                    existing = set(normalized["risk_flags"].split(";"))
                    existing.update(extra_flags)
                    normalized["risk_flags"] = ";".join(sorted(existing))
                elif extra_flags:
                    normalized["risk_flags"] = ";".join(sorted(extra_flags))

                # Force valid_image=false if any image was missing/unreadable
                if extra_flags:
                    normalized["valid_image"] = "false"

                return _model_output_to_full_row(normalized, claim_row)

            # Normalization errors exist; try repair if retries remain
            if attempts < max_retries:
                repair_prompt = get_repair_prompt(response, norm_errors)
                try:
                    response = provider.complete(system_prompt, repair_prompt, data_urls)
                except Exception as exc:
                    return _safe_fallback_row(
                        claim_row,
                        extra_flags=extra_flags,
                        reason=f"Model repair call failed: {exc}",
                    )
                attempts += 1
                continue
            else:
                return _safe_fallback_row(
                    claim_row,
                    extra_flags=extra_flags,
                    reason=f"Model output normalization failed: {'; '.join(norm_errors)}",
                )
        except (json.JSONDecodeError, ValueError) as exc:
            if attempts < max_retries:
                repair_prompt = get_repair_prompt(response, [f"JSON parse error: {exc}"])
                try:
                    response = provider.complete(system_prompt, repair_prompt, data_urls)
                except Exception as repair_exc:
                    return _safe_fallback_row(
                        claim_row,
                        extra_flags=extra_flags,
                        reason=f"Model repair call failed: {repair_exc}",
                    )
                attempts += 1
                continue
            else:
                return _safe_fallback_row(
                    claim_row,
                    extra_flags=extra_flags,
                    reason=f"Model output was not valid JSON: {exc}",
                )

    # Should not reach here, but defensive fallback
    return _safe_fallback_row(
        claim_row,
        extra_flags=extra_flags,
        reason="Model review exhausted all retries without a valid result.",
    )


def provider_name(provider: ModelProvider) -> str:
    """Return a deterministic name for the provider for caching purposes."""
    cls_name = provider.__class__.__name__
    if hasattr(provider, "model"):
        return f"{cls_name}:{getattr(provider, 'model')}"
    return cls_name
