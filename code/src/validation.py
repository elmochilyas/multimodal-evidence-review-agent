"""Validation logic for output rows and output CSV."""

import csv
from typing import Any, Dict, List, Optional, Tuple

from src.constants import (
    BOOLEAN_FIELDS,
    BOOLEAN_VALUES,
    CLAIM_OBJECT_VALUES,
    CLAIM_STATUS_VALUES,
    ISSUE_TYPE_VALUES,
    OBJECT_PART_VALUES,
    OUTPUT_COLUMNS,
    RISK_FLAG_VALUES,
    SEVERITY_VALUES,
)
from src.io_utils import get_image_ids


def validate_output_row(row: Dict[str, Any], input_row: Optional[Dict[str, str]] = None) -> Tuple[bool, List[str]]:
    """Validate a single output row against all schema rules.

    Returns (is_valid, list_of_errors).
    """
    errors: List[str] = []

    # Required fields present
    for col in OUTPUT_COLUMNS:
        if col not in row:
            errors.append(f"Missing required field: {col}")

    # Exact column set
    extra = set(row.keys()) - set(OUTPUT_COLUMNS)
    if extra:
        errors.append(f"Unexpected extra fields: {sorted(extra)}")

    # claim_object
    claim_object = str(row.get("claim_object", ""))
    if claim_object not in CLAIM_OBJECT_VALUES:
        errors.append(
            f"Invalid claim_object '{claim_object}', must be one of {sorted(CLAIM_OBJECT_VALUES)}"
        )

    # claim_status
    claim_status = str(row.get("claim_status", ""))
    if claim_status not in CLAIM_STATUS_VALUES:
        errors.append(
            f"Invalid claim_status '{claim_status}', must be one of {sorted(CLAIM_STATUS_VALUES)}"
        )

    # issue_type
    issue_type = str(row.get("issue_type", ""))
    if issue_type not in ISSUE_TYPE_VALUES:
        errors.append(
            f"Invalid issue_type '{issue_type}', must be one of {sorted(ISSUE_TYPE_VALUES)}"
        )

    # object_part (claim_object-specific)
    object_part = str(row.get("object_part", ""))
    if claim_object in OBJECT_PART_VALUES:
        if object_part not in OBJECT_PART_VALUES[claim_object]:
            errors.append(
                f"Invalid object_part '{object_part}' for claim_object '{claim_object}', "
                f"must be one of {sorted(OBJECT_PART_VALUES[claim_object])}"
            )
    elif object_part not in {"unknown"}:
        errors.append(
            f"Invalid object_part '{object_part}' for unknown claim_object '{claim_object}'"
        )

    # severity
    severity = str(row.get("severity", ""))
    if severity not in SEVERITY_VALUES:
        errors.append(
            f"Invalid severity '{severity}', must be one of {sorted(SEVERITY_VALUES)}"
        )

    # boolean fields (true/false strings)
    for field in BOOLEAN_FIELDS:
        value = str(row.get(field, ""))
        if value not in BOOLEAN_VALUES:
            errors.append(
                f"Invalid {field} '{value}', must be one of {sorted(BOOLEAN_VALUES)}"
            )

    # risk_flags: semicolon-separated allowed flags or none
    risk_flags = str(row.get("risk_flags", ""))
    if risk_flags != "none":
        flags = [f.strip() for f in risk_flags.split(";") if f.strip()]
        if not flags:
            errors.append("risk_flags cannot be empty; use 'none' if no flags apply")
        else:
            invalid = set(flags) - RISK_FLAG_VALUES
            if invalid:
                errors.append(
                    f"Invalid risk_flags: {sorted(invalid)}, allowed values: {sorted(RISK_FLAG_VALUES)}"
                )

    # supporting_image_ids: semicolon-separated image IDs or none
    supporting = str(row.get("supporting_image_ids", ""))
    if supporting != "none":
        ids = [i.strip() for i in supporting.split(";") if i.strip()]
        if not ids:
            errors.append(
                "supporting_image_ids cannot be empty; use 'none' if no images support the decision"
            )
        elif input_row is not None:
            valid_ids = set(get_image_ids(input_row.get("image_paths", "")))
            invalid_ids = set(ids) - valid_ids
            if invalid_ids:
                errors.append(
                    f"supporting_image_ids contain invalid image IDs: {sorted(invalid_ids)}"
                )

    return len(errors) == 0, errors


def validate_output_csv(
    output_path: str,
    input_path: str,
) -> Tuple[bool, List[str], int]:
    """Validate the full output CSV against the input CSV.

    Returns (is_valid, list_of_errors, row_count).
    """
    from src.io_utils import load_claims

    errors: List[str] = []

    input_rows = load_claims(input_path)
    expected_count = len(input_rows)

    # Read output CSV with all 14 columns
    output_rows: List[Dict[str, str]] = []
    with open(output_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != OUTPUT_COLUMNS:
            errors.append(
                f"Output header mismatch.\nExpected: {OUTPUT_COLUMNS}\nGot: {reader.fieldnames}"
            )
        for row in reader:
            output_rows.append({col: (row.get(col) or "").strip() for col in OUTPUT_COLUMNS})

    if len(output_rows) != expected_count:
        errors.append(
            f"Output row count mismatch: expected {expected_count}, got {len(output_rows)}"
        )

    for idx, output_row in enumerate(output_rows):
        # Map back to input row by position
        input_row = input_rows[idx] if idx < len(input_rows) else None
        row_valid, row_errors = validate_output_row(output_row, input_row)
        if not row_valid:
            for err in row_errors:
                errors.append(f"Row {idx + 1}: {err}")

    return len(errors) == 0, errors, len(output_rows)
