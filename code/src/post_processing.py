"""Conservative deterministic post-processing layer for evidence review outputs.

This module applies rules after VLM normalization and before final output. It is
intentionally conservative: it adds risk flags and only overrides core model
fields when the contradiction or evidence gap is unambiguous.

No sample rows, user IDs, image filenames, or expected labels are hardcoded.
"""

import re
from typing import Dict, List, Optional, Set

from src.constants import RISK_FLAG_VALUES


# Claim text patterns that indicate an attempt to force the reviewer's decision.
_PROMPT_INJECTION_PATTERNS = [
    r"approve\s+(this\s+)?claim",
    r"mark\s+(it\s+)?supported",
    r"ignore\s+(previous\s+)?instructions",
    r"ignore\s+all\s+prior\s+instructions",
    r"override\s+(the\s+)?(review|system|output)",
    r"do\s+not\s+inspect",
    r"do\s+not\s+review",
    r"trust\s+me",
    r"output\s+supported",
    r"return\s+supported",
    r"set\s+claim_status\s*=?\s*supported",
    r"follow\s+the\s+note",
]
_PROMPT_INJECTION_RE = re.compile(
    r"(" + "|".join(_PROMPT_INJECTION_PATTERNS) + r")",
    re.IGNORECASE,
)

# Strong indicators that a package claim is ABOUT contents/item, not just
# mentioning them in a support question.
_PACKAGE_CONTENTS_CLAIM_RE = re.compile(
    r"\b(contents?|item|product)s?\s+(are|is|were|was)\s+(missing|not\s+inside|absent)",
    re.IGNORECASE,
)
_PACKAGE_MISSING_RE = re.compile(
    r"\b(not\s+inside|missing\s+(from\s+)?(the\s+)?(box|package)|"
    r"could\s+not\s+find\s+(the\s+)?(item|product|contents?)|"
    r"verify\s+(that\s+)?(the\s+)?contents?\s+(are\s+)?missing)\b",
    re.IGNORECASE,
)

# Object parts that are exterior-only for packages.
_PACKAGE_EXTERIOR_PARTS = {
    "box",
    "package_corner",
    "package_side",
    "seal",
    "label",
}


def _claim_text(claim_row: Dict[str, str]) -> str:
    return str(claim_row.get("user_claim", "")).lower()


def _split_risk_flags(value: str) -> List[str]:
    """Split semicolon-separated risk flags, dropping 'none'."""
    if not value:
        return []
    return [
        f.strip().lower()
        for f in value.split(";")
        if f.strip() and f.strip().lower() != "none"
    ]


def _join_risk_flags(flags: Set[str]) -> str:
    """Join sorted risk flags; return 'none' when empty."""
    valid = sorted(f for f in flags if f in RISK_FLAG_VALUES and f != "none")
    return ";".join(valid) if valid else "none"


def _set_risk_flags(review: Dict[str, str], flags: Set[str]) -> None:
    """Merge flags into the review's risk_flags field."""
    current = set(_split_risk_flags(review.get("risk_flags", "")))
    current.update(flags)
    review["risk_flags"] = _join_risk_flags(current)


def _history_indicates_manual_review(user_history_row: Optional[Dict[str, str]]) -> bool:
    """Return True when the numeric history fields suggest elevated review need."""
    if not user_history_row:
        return False
    history_flags = str(user_history_row.get("history_flags", "")).strip().lower()
    if "manual_review_required" in history_flags:
        return True
    if "user_history_risk" not in history_flags:
        return False
    try:
        manual_review = int(user_history_row.get("manual_review_claim", "0") or "0")
        rejected = int(user_history_row.get("rejected_claim", "0") or "0")
        last_90 = int(user_history_row.get("last_90_days_claim_count", "0") or "0")
    except ValueError:
        return False
    return manual_review > 0 or rejected > 0 or last_90 >= 3


def _apply_history_risk(
    review: Dict[str, str],
    claim_row: Dict[str, str],
    user_history_row: Optional[Dict[str, str]],
) -> None:
    """Add deterministic risk flags from history_flags and numeric history.

    Never changes evidence_standard_met, valid_image, issue_type, object_part,
    claim_status, supporting_image_ids, or severity.
    """
    if not user_history_row:
        return

    history_flags = str(user_history_row.get("history_flags", "")).strip().lower()
    flags_to_add: Set[str] = set()

    if "user_history_risk" in history_flags:
        flags_to_add.add("user_history_risk")
    if "manual_review_required" in history_flags:
        flags_to_add.add("manual_review_required")
    elif _history_indicates_manual_review(user_history_row):
        flags_to_add.add("manual_review_required")

    if flags_to_add:
        _set_risk_flags(review, flags_to_add)


def _apply_prompt_injection_guardrail(
    review: Dict[str, str], claim_row: Dict[str, str]
) -> None:
    """Detect instruction-like text in the claim and ensure required flags.

    Never changes claim_status; the instruction must not drive the decision.
    """
    claim_text = _claim_text(claim_row)
    existing_flags = set(_split_risk_flags(review.get("risk_flags", "")))

    if _PROMPT_INJECTION_RE.search(claim_text):
        _set_risk_flags(review, {"text_instruction_present", "manual_review_required"})
    elif "text_instruction_present" in existing_flags:
        # Model detected an instruction in the image; ensure manual review is flagged.
        _set_risk_flags(review, {"manual_review_required"})


def _is_clear_contents_claim(claim_text: str) -> bool:
    """Return True only when the claim text is clearly about missing contents."""
    return bool(
        _PACKAGE_CONTENTS_CLAIM_RE.search(claim_text)
        or _PACKAGE_MISSING_RE.search(claim_text)
    )


def _apply_package_contents_rule(
    review: Dict[str, str], claim_row: Dict[str, str]
) -> None:
    """Handle package claims about contents/interior when images only show exterior.

    This rule triggers only when:
      - claim_object is package,
      - the claim text clearly indicates a contents/item claim,
      - the model's object_part is exterior-only or unknown,
      - the supporting images do not include contents/item.
    """
    claim_object = str(claim_row.get("claim_object", "")).strip().lower()
    if claim_object != "package":
        return

    claim_text = _claim_text(claim_row)
    if not _is_clear_contents_claim(claim_text):
        return

    object_part = str(review.get("object_part", "")).strip().lower()
    if object_part not in _PACKAGE_EXTERIOR_PARTS and object_part != "unknown":
        return

    supporting = _split_risk_flags(review.get("supporting_image_ids", ""))
    if "contents" in supporting or "item" in supporting:
        return

    review["evidence_standard_met"] = "false"
    review["claim_status"] = "not_enough_information"
    review["valid_image"] = "false"
    review["supporting_image_ids"] = "none"

    if "contents" in claim_text or "content" in claim_text:
        review["object_part"] = "contents"
    elif "item" in claim_text or "product" in claim_text:
        review["object_part"] = "item"

    issue_type = str(review.get("issue_type", "")).strip().lower()
    if issue_type != "missing_part":
        review["issue_type"] = "unknown"

    flags_to_add = {"cropped_or_obstructed", "damage_not_visible", "manual_review_required"}
    _set_risk_flags(review, flags_to_add)

    reason = "Images show exterior packaging only; cannot verify contents/item claims."
    review["evidence_standard_met_reason"] = reason
    review["claim_status_justification"] = reason


def _apply_mismatch_guardrail(
    review: Dict[str, str], claim_row: Dict[str, str]
) -> None:
    """Conservatively add mismatch risk flags without overriding claim_status.

    Only changes claim_status when the model itself already signals a mismatch
    through its own risk flags (wrong_object, wrong_object_part, claim_mismatch)
    AND the visual evidence contradicts the claim.
    """
    claim_text = _claim_text(claim_row)
    issue_type = str(review.get("issue_type", "")).strip().lower()
    claim_status = str(review.get("claim_status", "")).strip().lower()
    model_flags = set(_split_risk_flags(review.get("risk_flags", "")))

    mismatch_flags = {"wrong_object", "wrong_object_part", "claim_mismatch"}
    model_indicates_mismatch = bool(model_flags & mismatch_flags)

    # If the model itself flagged a mismatch and the claim is currently supported,
    # prefer contradicted only when the mismatch is unambiguous.
    if claim_status == "supported" and model_indicates_mismatch:
        # A visible issue on a wrong part/object is a contradiction.
        if issue_type not in {"none", "unknown"}:
            review["claim_status"] = "contradicted"
            _set_risk_flags(review, {"claim_mismatch"})
            review["claim_status_justification"] = (
                "Model flags indicate a mismatch between the claim and visible evidence."
            )
        else:
            # No visible issue means insufficient information, not a contradiction.
            review["claim_status"] = "not_enough_information"
            _set_risk_flags(review, {"damage_not_visible"})


def _normalize_risk_flags(review: Dict[str, str]) -> None:
    """Deduplicate and sort risk flags; ensure 'none' only when truly empty."""
    flags = set(_split_risk_flags(review.get("risk_flags", "")))
    review["risk_flags"] = _join_risk_flags(flags)


def apply_post_processing(
    review: Dict[str, str],
    claim_row: Dict[str, str],
    user_history_row: Optional[Dict[str, str]] = None,
) -> None:
    """Apply conservative deterministic post-processing rules."""
    _apply_history_risk(review, claim_row, user_history_row)
    _apply_prompt_injection_guardrail(review, claim_row)
    _apply_package_contents_rule(review, claim_row)
    _apply_mismatch_guardrail(review, claim_row)
    _normalize_risk_flags(review)
