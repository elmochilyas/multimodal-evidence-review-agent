"""Tests for the output validation logic."""

from src.validation import validate_output_row


def make_valid_row() -> dict:
    return {
        "user_id": "u1",
        "image_paths": "images/test/case_001/img_1.jpg",
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


def test_valid_row() -> None:
    row = make_valid_row()
    valid, errors = validate_output_row(row, row)
    assert valid, errors


def test_invalid_claim_status() -> None:
    row = make_valid_row()
    row["claim_status"] = "approved"
    valid, errors = validate_output_row(row, row)
    assert not valid
    assert any("claim_status" in e for e in errors)


def test_invalid_issue_type() -> None:
    row = make_valid_row()
    row["issue_type"] = "broken"
    valid, errors = validate_output_row(row, row)
    assert not valid
    assert any("issue_type" in e for e in errors)


def test_invalid_object_part_for_car() -> None:
    row = make_valid_row()
    row["object_part"] = "screen"  # laptop part, not car
    valid, errors = validate_output_row(row, row)
    assert not valid
    assert any("object_part" in e for e in errors)


def test_invalid_severity() -> None:
    row = make_valid_row()
    row["severity"] = "critical"
    valid, errors = validate_output_row(row, row)
    assert not valid
    assert any("severity" in e for e in errors)


def test_invalid_boolean() -> None:
    row = make_valid_row()
    row["valid_image"] = "yes"
    valid, errors = validate_output_row(row, row)
    assert not valid
    assert any("valid_image" in e for e in errors)


def test_invalid_risk_flag() -> None:
    row = make_valid_row()
    row["risk_flags"] = "made_up_flag"
    valid, errors = validate_output_row(row, row)
    assert not valid
    assert any("risk_flags" in e for e in errors)


def test_multiple_risk_flags_valid() -> None:
    row = make_valid_row()
    row["risk_flags"] = "blurry_image;user_history_risk"
    valid, errors = validate_output_row(row, row)
    assert valid, errors


def test_invalid_supporting_image_id() -> None:
    row = make_valid_row()
    row["supporting_image_ids"] = "img_99"
    valid, errors = validate_output_row(row, row)
    assert not valid
    assert any("supporting_image_ids" in e for e in errors)


def test_valid_supporting_image_id() -> None:
    row = make_valid_row()
    row["supporting_image_ids"] = "img_1"
    valid, errors = validate_output_row(row, row)
    assert valid, errors


def test_missing_field() -> None:
    row = make_valid_row()
    del row["severity"]
    valid, errors = validate_output_row(row, row)
    assert not valid
    assert any("severity" in e for e in errors)
