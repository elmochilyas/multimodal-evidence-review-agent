"""Evaluation metrics for comparing predicted and expected claim outputs."""

from typing import Dict, List, Sequence, Tuple

from src.constants import OUTPUT_COLUMNS


# Fields compared during evaluation
COMPARED_FIELDS = [
    "evidence_standard_met",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "valid_image",
    "severity",
    "supporting_image_ids",
]


def normalize_set(value: str) -> frozenset:
    """Normalize a semicolon-separated string into a frozenset of tokens."""
    if not value or value.strip().lower() == "none":
        return frozenset()
    return frozenset(part.strip() for part in value.split(";") if part.strip())


def fields_match(predicted: Dict[str, str], expected: Dict[str, str], field: str) -> bool:
    """Compare a single field between predicted and expected rows.

    Semicolon-separated fields are compared as unordered sets.
    All other fields are compared as normalized strings.
    """
    pred = str(predicted.get(field, "")).strip()
    exp = str(expected.get(field, "")).strip()

    if field in {"risk_flags", "supporting_image_ids"}:
        return normalize_set(pred) == normalize_set(exp)

    return pred == exp


def exact_row_match(predicted: Dict[str, str], expected: Dict[str, str]) -> bool:
    """Return True if all compared fields match exactly."""
    return all(
        fields_match(predicted, expected, field) for field in COMPARED_FIELDS
    )


def compute_field_accuracy(
    predicted_rows: Sequence[Dict[str, str]],
    expected_rows: Sequence[Dict[str, str]],
) -> Dict[str, float]:
    """Compute per-field accuracy across all rows."""
    if len(predicted_rows) != len(expected_rows):
        raise ValueError(
            f"Row count mismatch: {len(predicted_rows)} predicted vs {len(expected_rows)} expected"
        )

    total = len(predicted_rows)
    accuracies: Dict[str, float] = {}
    for field in COMPARED_FIELDS:
        matches = sum(
            1
            for pred, exp in zip(predicted_rows, expected_rows)
            if fields_match(pred, exp, field)
        )
        accuracies[field] = matches / total if total > 0 else 0.0
    return accuracies


def compute_exact_match_accuracy(
    predicted_rows: Sequence[Dict[str, str]],
    expected_rows: Sequence[Dict[str, str]],
) -> float:
    """Compute exact row match accuracy."""
    if len(predicted_rows) != len(expected_rows):
        raise ValueError(
            f"Row count mismatch: {len(predicted_rows)} predicted vs {len(expected_rows)} expected"
        )

    total = len(predicted_rows)
    if total == 0:
        return 0.0

    matches = sum(
        1 for pred, exp in zip(predicted_rows, expected_rows) if exact_row_match(pred, exp)
    )
    return matches / total


def compute_failure_summary(
    predicted_rows: Sequence[Dict[str, str]],
    expected_rows: Sequence[Dict[str, str]],
) -> Dict[str, List[int]]:
    """Return a mapping of field -> list of row indices (1-based) where that field mismatched."""
    failures: Dict[str, List[int]] = {field: [] for field in COMPARED_FIELDS}
    for idx, (pred, exp) in enumerate(zip(predicted_rows, expected_rows), start=1):
        for field in COMPARED_FIELDS:
            if not fields_match(pred, exp, field):
                failures[field].append(idx)
    return failures


def categorize_failure(
    predicted: Dict[str, str], expected: Dict[str, str]
) -> List[str]:
    """Categorize failures for a single row into high-level buckets."""
    categories: List[str] = []

    if not fields_match(predicted, expected, "issue_type") or not fields_match(
        predicted, expected, "object_part"
    ):
        categories.append("claim_extraction")

    if not fields_match(predicted, expected, "claim_status"):
        categories.append("visual_review")

    if not fields_match(predicted, expected, "evidence_standard_met"):
        categories.append("evidence_standard")

    if not fields_match(predicted, expected, "risk_flags"):
        categories.append("risk_flags")

    if not fields_match(predicted, expected, "severity"):
        categories.append("severity")

    if not fields_match(predicted, expected, "valid_image") or not fields_match(
        predicted, expected, "supporting_image_ids"
    ):
        categories.append("formatting")

    return categories


def compute_failure_categories(
    predicted_rows: Sequence[Dict[str, str]],
    expected_rows: Sequence[Dict[str, str]],
) -> Dict[str, int]:
    """Count how many rows fall into each failure category."""
    counts: Dict[str, int] = {
        "claim_extraction": 0,
        "visual_review": 0,
        "evidence_standard": 0,
        "risk_flags": 0,
        "severity": 0,
        "formatting": 0,
    }
    for pred, exp in zip(predicted_rows, expected_rows):
        for category in categorize_failure(pred, exp):
            counts[category] += 1
    return counts


def split_sample_rows(
    sample_rows: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Split sample_claims.csv rows into input rows and expected output rows."""
    input_rows: List[Dict[str, str]] = []
    expected_rows: List[Dict[str, str]] = []

    for row in sample_rows:
        input_row = {
            "user_id": row["user_id"],
            "image_paths": row["image_paths"],
            "user_claim": row["user_claim"],
            "claim_object": row["claim_object"],
        }
        expected_row = {col: row.get(col, "") for col in OUTPUT_COLUMNS}
        input_rows.append(input_row)
        expected_rows.append(expected_row)

    return input_rows, expected_rows
