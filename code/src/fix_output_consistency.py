"""Deterministic output post-processing re-apply tool.

Re-applies the current generic post-processing rules (and the deterministic
severity calibration step that follows them in the live pipeline) to an existing
output.csv without calling any model or API.

Use this when output.csv was produced before a code rule change and cannot be
regenerated (e.g., no API access).
"""

import argparse
import csv
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from src.io_utils import OUTPUT_COLUMNS, load_claims, load_user_history
from src.post_processing import apply_post_processing
from src.severity import calibrate_severity


_REVIEW_FIELDS = [
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


def _load_output_rows(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _build_key(row: Dict[str, str]) -> tuple:
    return (row.get("user_id", ""), row.get("image_paths", ""))


def reapply_post_processing(
    output_path: str,
    claims_path: str,
    user_history_path: str,
    candidate_path: Optional[str] = None,
    in_place: bool = False,
) -> Dict[str, int]:
    """Re-apply deterministic post-processing to an existing output CSV.

    Returns a stats dict with row counts and change counts.
    """
    output_path = Path(output_path)

    claims = load_claims(claims_path)
    claims_by_key = {_build_key(row): row for row in claims}

    history_by_user = load_user_history(user_history_path)

    rows = _load_output_rows(str(output_path))
    changed = 0
    field_counts: Dict[str, int] = {field: 0 for field in _REVIEW_FIELDS}

    for row in rows:
        key = _build_key(row)
        claim_row = claims_by_key.get(key)
        if claim_row is None:
            # Defensive: keep row unchanged if the matching claim cannot be found.
            continue

        user_id = claim_row.get("user_id", "")
        history_row = history_by_user.get(user_id)

        review = {field: row.get(field, "") for field in _REVIEW_FIELDS}
        before = dict(review)

        apply_post_processing(review, claim_row, history_row)
        review["severity"] = calibrate_severity(review, claim_row)

        changed_fields = [field for field in _REVIEW_FIELDS if before[field] != review[field]]
        if changed_fields:
            changed += 1
            for field in changed_fields:
                field_counts[field] += 1
            for field in _REVIEW_FIELDS:
                row[field] = review[field]

    if candidate_path:
        with open(candidate_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote candidate with {changed} changed rows to {candidate_path}")

    if in_place:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {output_path} in place ({changed} rows changed)")

    return {
        "total_rows": len(rows),
        "changed_rows": changed,
        "field_counts": field_counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-apply deterministic post-processing to an existing output.csv"
    )
    parser.add_argument("--output", required=True, help="Path to existing output.csv")
    parser.add_argument("--input", required=True, help="Path to claims.csv")
    parser.add_argument(
        "--user-history", required=True, help="Path to user_history.csv"
    )
    parser.add_argument(
        "--candidate",
        help="Path to write the candidate output.csv (default: no candidate written)",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the input output.csv after re-applying rules",
    )
    parser.add_argument(
        "--backup",
        help="Path to back up the original output.csv before in-place overwrite",
    )
    args = parser.parse_args()

    if args.in_place and args.backup:
        shutil.copy2(args.output, args.backup)
        print(f"Backed up original output to {args.backup}")

    stats = reapply_post_processing(
        args.output,
        args.input,
        args.user_history,
        candidate_path=args.candidate,
        in_place=args.in_place,
    )

    print(f"Total rows: {stats['total_rows']}")
    print(f"Changed rows: {stats['changed_rows']}")
    if stats["changed_rows"]:
        print("Field-level changes:")
        for field, count in stats["field_counts"].items():
            if count:
                print(f"  {field}: {count}")


if __name__ == "__main__":
    main()
