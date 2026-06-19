"""Review logic for producing evidence review decisions."""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.cache import ModelResponseCache
from src.constants import OUTPUT_COLUMNS
from src.model_provider import MockProvider, create_provider
from src.model_review import review_claim_with_model


@dataclass
class ReviewConfig:
    """Configuration for the reviewer."""

    mode: str = "baseline"
    provider_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.0
    cache_dir: str = ".cache/model_responses"
    use_cache: bool = True
    base_dir: str = "."
    evidence_requirements: Optional[List[Dict[str, str]]] = None
    user_history: Optional[Dict[str, Dict[str, str]]] = None


def _get_user_history_summary(
    user_id: str, user_history: Optional[Dict[str, Dict[str, str]]]
) -> Optional[str]:
    if not user_history:
        return None
    row = user_history.get(user_id)
    if not row:
        return None
    summary = row.get("history_summary", "").strip()
    flags = row.get("history_flags", "").strip()
    parts: List[str] = []
    if summary:
        parts.append(summary)
    if flags and flags.lower() != "none":
        parts.append(f"History flags: {flags}")
    return " ".join(parts) if parts else None


def review_claim_baseline(claim_row: Dict[str, str]) -> Dict[str, Any]:
    """Produce a safe baseline output row without image review."""
    return {
        "user_id": claim_row["user_id"],
        "image_paths": claim_row["image_paths"],
        "user_claim": claim_row["user_claim"],
        "claim_object": claim_row["claim_object"],
        "evidence_standard_met": "false",
        "evidence_standard_met_reason": (
            "Visual review has not yet confirmed sufficient evidence for the claim."
        ),
        "risk_flags": "manual_review_required",
        "issue_type": "unknown",
        "object_part": "unknown",
        "claim_status": "not_enough_information",
        "claim_status_justification": (
            "Baseline reviewer requires model/image review before confirming the claim."
        ),
        "supporting_image_ids": "none",
        "valid_image": "false",
        "severity": "unknown",
    }


def _review_claim_with_config(
    claim_row: Dict[str, str], config: ReviewConfig
) -> Dict[str, Any]:
    """Review a single claim using the configured mode."""
    mode = config.mode.lower().strip()

    if mode == "baseline":
        return review_claim_baseline(claim_row)

    # Determine provider
    if mode == "mock":
        provider: Any = MockProvider()
    else:
        # live or any other value -> use configured provider, defaulting to mock if unset
        provider = create_provider(
            provider_name=config.provider_name,
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            temperature=config.temperature,
        )

    cache = ModelResponseCache(config.cache_dir) if config.use_cache else None
    history_summary = _get_user_history_summary(
        claim_row.get("user_id", ""), config.user_history
    )

    return review_claim_with_model(
        claim_row,
        provider=provider,
        cache=cache,
        evidence_requirements=config.evidence_requirements,
        user_history_summary=history_summary,
        user_history=config.user_history,
        base_dir=config.base_dir,
    )


def review_claims(
    claims: List[Dict[str, str]],
    config: Optional[ReviewConfig] = None,
) -> List[Dict[str, Any]]:
    """Review a list of claims and return output rows."""
    cfg = config or ReviewConfig()
    return [_review_claim_with_config(claim, cfg) for claim in claims]


def ensure_output_schema(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure every row contains exactly the output columns in order."""
    return [{col: str(row.get(col, "")) for col in OUTPUT_COLUMNS} for row in rows]
