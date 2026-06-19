"""Input/output utilities for CSV files and image paths."""

import csv
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.constants import (
    CLAIM_COLUMNS,
    EVIDENCE_REQUIREMENT_COLUMNS,
    OUTPUT_COLUMNS,
    USER_HISTORY_COLUMNS,
)


def load_claims(path: str) -> List[Dict[str, str]]:
    """Load claims.csv into a list of dicts."""
    return _load_csv(path, CLAIM_COLUMNS)


def load_user_history(path: str) -> Dict[str, Dict[str, str]]:
    """Load user_history.csv and index by user_id."""
    rows = _load_csv(path, USER_HISTORY_COLUMNS)
    return {row["user_id"]: row for row in rows}


def load_evidence_requirements(path: str) -> List[Dict[str, str]]:
    """Load evidence_requirements.csv into a list of dicts."""
    return _load_csv(path, EVIDENCE_REQUIREMENT_COLUMNS)


def load_csv(path: str) -> List[Dict[str, str]]:
    """Load a CSV file and return all columns for each row."""
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    rows: List[Dict[str, str]] = []
    with resolved.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV file is empty or has no header: {path}")

        for raw_row in reader:
            row = {col: (value or "").strip() for col, value in raw_row.items()}
            rows.append(row)

    return rows


def _load_csv(path: str, expected_columns: List[str]) -> List[Dict[str, str]]:
    """Generic CSV loader that checks required columns are present."""
    rows = load_csv(path)
    if not rows:
        return []

    missing = set(expected_columns) - set(rows[0].keys())
    if missing:
        raise ValueError(
            f"CSV {path} missing expected columns: {sorted(missing)}"
        )

    return [{col: row[col] for col in expected_columns} for row in rows]


def split_image_paths(image_paths: str) -> List[str]:
    """Split semicolon-separated image paths into a list."""
    if not image_paths:
        return []
    return [p.strip() for p in image_paths.split(";") if p.strip()]


def extract_image_id(image_path: str) -> str:
    """Extract image ID (filename without extension) from a path."""
    return Path(image_path).stem


def get_image_ids(image_paths: str) -> List[str]:
    """Extract image IDs from semicolon-separated image paths."""
    return [extract_image_id(p) for p in split_image_paths(image_paths)]


def resolve_image_path(
    image_path: str, base_dir: Optional[str] = None
) -> Tuple[str, bool]:
    """Resolve an image path relative to base_dir or the current working directory.

    Returns the resolved absolute path and whether the file exists.
    """
    path = Path(image_path)
    if base_dir is not None:
        base = Path(base_dir)
        if not path.is_absolute():
            path = base / path
    return str(path.resolve()), path.exists()


def write_output_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    """Write output rows to CSV with the exact required column order."""
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)

    with resolved.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in rows:
            output_row = {col: str(row.get(col, "")) for col in OUTPUT_COLUMNS}
            writer.writerow(output_row)
