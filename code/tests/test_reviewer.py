"""Tests for the baseline reviewer."""

from src.reviewer import review_claim_baseline


def test_baseline_review_values() -> None:
    claim = {
        "user_id": "u1",
        "image_paths": "a.jpg",
        "user_claim": "claim text",
        "claim_object": "car",
    }
    result = review_claim_baseline(claim)
    assert result["evidence_standard_met"] == "false"
    assert result["claim_status"] == "not_enough_information"
    assert result["issue_type"] == "unknown"
    assert result["object_part"] == "unknown"
    assert result["severity"] == "unknown"
    assert result["valid_image"] == "false"
    assert result["supporting_image_ids"] == "none"
    assert result["risk_flags"] == "manual_review_required"
