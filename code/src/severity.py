"""Deterministic severity calibration layer for evidence review outputs.

The vision model tends to overestimate severity by one level. This module
adjusts the model-provided severity using the other predicted labels and the
user's claim text, without hardcoding any sample rows or user identifiers.
"""

import re
from typing import Dict

from src.constants import SEVERITY_VALUES


# Wording that suggests minor / cosmetic damage.
_MINOR_WORDS = {
    "minor",
    "small",
    "tiny",
    "light",
    "slight",
    "superficial",
    "cosmetic",
    "hairline",
    "fine",
    "little",
    "minimal",
    "scuff",
    "scuffed",
    "chip",
    "chipped",
}

# Wording that suggests severe / major damage.
_SEVERE_WORDS = {
    "severe",
    "deep",
    "extensive",
    "shattered",
    "unusable",
    "major",
    "large",
    "huge",
    "significant",
    "catastrophic",
    "destroyed",
    "broken",
    "smashed",
    "crushed",
    "massive",
    "widespread",
    "safety",
    "dangerous",
    "critical",
}


_RE_MINOR = re.compile(r"\b(" + "|".join(map(re.escape, _MINOR_WORDS)) + r")\b", re.IGNORECASE)
_RE_SEVERE = re.compile(r"\b(" + "|".join(map(re.escape, _SEVERE_WORDS)) + r")\b", re.IGNORECASE)


def _claim_has_minor_wording(claim_text: str) -> bool:
    return bool(_RE_MINOR.search(claim_text))


def _claim_has_severe_wording(claim_text: str) -> bool:
    return bool(_RE_SEVERE.search(claim_text))


def calibrate_severity(review: Dict[str, str], claim_row: Dict[str, str]) -> str:
    """Return a calibrated severity value based on predicted labels and claim text.

    The model-provided severity is respected only when it aligns with the
    calibration rules; otherwise it is adjusted downward/upward to the rule-
    based value.
    """
    claim_status = str(review.get("claim_status", "")).strip().lower()
    issue_type = str(review.get("issue_type", "")).strip().lower()
    claim_text = str(claim_row.get("user_claim", "")).lower()

    # Rule 1: insufficient information -> unknown.
    if claim_status == "not_enough_information":
        return "unknown"

    # Rule 2 & 3: no visible damage / contradicted with no damage -> none.
    if issue_type == "none":
        return "none"
    if claim_status == "contradicted":
        return "none"

    # Rule 4: supported visible damage.
    if claim_status == "supported":
        has_minor = _claim_has_minor_wording(claim_text)
        has_severe = _claim_has_severe_wording(claim_text)

        # Minor cosmetic issues default to low.
        if issue_type in {"scratch", "stain"}:
            if has_severe:
                return "medium"
            return "low"

        # Torn packaging: low if minor, high if severe, else medium.
        if issue_type == "torn_packaging":
            if has_minor:
                return "low"
            if has_severe:
                return "high"
            return "medium"

        # Glass shatter is always high.
        if issue_type == "glass_shatter":
            return "high"

        # Crack calibration: windshield cracks default to medium because they are
        # repair-relevant and potentially safety-relevant; downgrade only with
        # explicit severe wording. Non-windshield cracks become low only when the
        # claim text explicitly uses minor/hairline/tiny/small/light.
        if issue_type == "crack":
            object_part = str(review.get("object_part", "")).strip().lower()
            if object_part == "windshield":
                if has_severe:
                    return "high"
                return "medium"
            explicit_minor = {"minor", "hairline", "tiny", "small", "light"}
            if any(word in claim_text for word in explicit_minor):
                return "low"
            return "medium"

        # Default repairable damage types: medium unless clearly minor or severe.
        if issue_type in {
            "dent",
            "broken_part",
            "crushed_packaging",
            "water_damage",
            "missing_part",
        }:
            if has_minor:
                return "low"
            if has_severe:
                return "high"
            return "medium"

    # Fallback: keep model severity if it is valid.
    model_severity = str(review.get("severity", "")).strip().lower()
    if model_severity in SEVERITY_VALUES:
        return model_severity
    return "unknown"
