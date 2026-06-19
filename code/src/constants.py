"""Constants and allowed values for the evidence review system."""

from typing import Dict, List, Set

# Exact output column order
OUTPUT_COLUMNS = [
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
    "evidence_standard_met",
    "evidence_standard_met_reason",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "claim_status_justification",
    "supporting_image_ids",
    "valid_image",
    "severity",
]

# Input columns
CLAIM_COLUMNS = ["user_id", "image_paths", "user_claim", "claim_object"]
USER_HISTORY_COLUMNS = [
    "user_id",
    "past_claim_count",
    "accept_claim",
    "manual_review_claim",
    "rejected_claim",
    "last_90_days_claim_count",
    "history_flags",
    "history_summary",
]
EVIDENCE_REQUIREMENT_COLUMNS = [
    "requirement_id",
    "claim_object",
    "applies_to",
    "minimum_image_evidence",
]

# Allowed values
CLAIM_OBJECT_VALUES: Set[str] = {"car", "laptop", "package"}

CLAIM_STATUS_VALUES: Set[str] = {"supported", "contradicted", "not_enough_information"}

ISSUE_TYPE_VALUES: Set[str] = {
    "dent",
    "scratch",
    "crack",
    "glass_shatter",
    "broken_part",
    "missing_part",
    "torn_packaging",
    "crushed_packaging",
    "water_damage",
    "stain",
    "none",
    "unknown",
}

OBJECT_PART_VALUES: Dict[str, Set[str]] = {
    "car": {
        "front_bumper",
        "rear_bumper",
        "door",
        "hood",
        "windshield",
        "side_mirror",
        "headlight",
        "taillight",
        "fender",
        "quarter_panel",
        "body",
        "unknown",
    },
    "laptop": {
        "screen",
        "keyboard",
        "trackpad",
        "hinge",
        "lid",
        "corner",
        "port",
        "base",
        "body",
        "unknown",
    },
    "package": {
        "box",
        "package_corner",
        "package_side",
        "seal",
        "label",
        "contents",
        "item",
        "unknown",
    },
}

SEVERITY_VALUES: Set[str] = {"none", "low", "medium", "high", "unknown"}

RISK_FLAG_VALUES: Set[str] = {
    "none",
    "blurry_image",
    "cropped_or_obstructed",
    "low_light_or_glare",
    "wrong_angle",
    "wrong_object",
    "wrong_object_part",
    "damage_not_visible",
    "claim_mismatch",
    "possible_manipulation",
    "non_original_image",
    "text_instruction_present",
    "user_history_risk",
    "manual_review_required",
}

BOOLEAN_FIELDS: Set[str] = {"evidence_standard_met", "valid_image"}
BOOLEAN_VALUES: Set[str] = {"true", "false"}

SUPPORTED_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
