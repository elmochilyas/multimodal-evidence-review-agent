"""Tests for io_utils loaders, image path handling, and output writer."""

import csv
from pathlib import Path

from src.constants import OUTPUT_COLUMNS
from src.io_utils import (
    extract_image_id,
    get_image_ids,
    load_claims,
    load_evidence_requirements,
    load_user_history,
    resolve_image_path,
    split_image_paths,
    write_output_csv,
)


def test_load_claims(tmp_path: Path) -> None:
    path = tmp_path / "claims.csv"
    path.write_text(
        'user_id,image_paths,user_claim,claim_object\n'
        'u1,img/a.jpg,"claim text",car\n',
        encoding="utf-8",
    )
    rows = load_claims(str(path))
    assert len(rows) == 1
    assert rows[0]["user_id"] == "u1"
    assert rows[0]["image_paths"] == "img/a.jpg"
    assert rows[0]["user_claim"] == "claim text"
    assert rows[0]["claim_object"] == "car"


def test_load_user_history(tmp_path: Path) -> None:
    data_dir = Path(__file__).parent / "data"
    history = load_user_history(str(data_dir / "user_history.csv"))
    assert "user_001" in history
    assert history["user_002"]["history_flags"] == "user_history_risk"


def test_load_evidence_requirements(tmp_path: Path) -> None:
    data_dir = Path(__file__).parent / "data"
    reqs = load_evidence_requirements(str(data_dir / "evidence_requirements.csv"))
    assert len(reqs) == 2
    assert reqs[0]["requirement_id"] == "REQ_GENERAL_OBJECT_PART"


def test_split_image_paths() -> None:
    paths = "a/b.jpg;c/d.png"
    assert split_image_paths(paths) == ["a/b.jpg", "c/d.png"]


def test_extract_image_id() -> None:
    assert extract_image_id("images/test/case_001/img_1.jpg") == "img_1"


def test_get_image_ids() -> None:
    assert get_image_ids("a/img1.jpg;b/img2.png") == ["img1", "img2"]


def test_resolve_image_path(tmp_path: Path) -> None:
    image = tmp_path / "img.jpg"
    image.write_text("")
    resolved, exists = resolve_image_path("img.jpg", str(tmp_path))
    assert exists is True
    assert "img.jpg" in resolved


def test_write_output_csv(tmp_path: Path) -> None:
    path = tmp_path / "output.csv"
    row = {
        "user_id": "u1",
        "image_paths": "a.jpg",
        "user_claim": "claim",
        "claim_object": "car",
        "evidence_standard_met": "false",
        "evidence_standard_met_reason": "reason",
        "risk_flags": "none",
        "issue_type": "unknown",
        "object_part": "unknown",
        "claim_status": "not_enough_information",
        "claim_status_justification": "justification",
        "supporting_image_ids": "none",
        "valid_image": "false",
        "severity": "unknown",
    }
    write_output_csv(str(path), [row])

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == OUTPUT_COLUMNS
        data = next(reader)
        assert data[0] == "u1"
        assert data[4] == "false"
