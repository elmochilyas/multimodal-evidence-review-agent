"""Tests for deterministic severity calibration."""

from src.severity import calibrate_severity


def _review(
    claim_status: str,
    issue_type: str,
    severity: str,
    evidence_standard_met: str = "true",
    valid_image: str = "true",
    object_part: str = "",
) -> dict:
    return {
        "claim_status": claim_status,
        "issue_type": issue_type,
        "severity": severity,
        "evidence_standard_met": evidence_standard_met,
        "valid_image": valid_image,
        "object_part": object_part,
    }


def _claim(text: str) -> dict:
    return {"user_claim": text}


def test_supported_scratch_predicted_medium_becomes_low() -> None:
    review = _review("supported", "scratch", "medium")
    claim = _claim("Front bumper has a light scratch")
    assert calibrate_severity(review, claim) == "low"


def test_supported_dent_predicted_high_becomes_medium() -> None:
    review = _review("supported", "dent", "high")
    claim = _claim("There is a dent on the rear door")
    assert calibrate_severity(review, claim) == "medium"


def test_supported_windshield_crack_remains_medium() -> None:
    review = _review("supported", "crack", "medium", object_part="windshield")
    claim = _claim("Windshield has a crack")
    assert calibrate_severity(review, claim) == "medium"


def test_glass_shatter_remains_high() -> None:
    review = _review("supported", "glass_shatter", "high")
    claim = _claim("The glass is shattered")
    assert calibrate_severity(review, claim) == "high"


def test_contradicted_with_no_issue_becomes_none() -> None:
    review = _review("contradicted", "none", "medium")
    claim = _claim("I see no damage")
    assert calibrate_severity(review, claim) == "none"


def test_not_enough_information_becomes_unknown() -> None:
    review = _review("not_enough_information", "unknown", "medium")
    claim = _claim("Image is blurry")
    assert calibrate_severity(review, claim) == "unknown"


def test_severe_scratch_can_be_medium() -> None:
    review = _review("supported", "scratch", "low")
    claim = _claim("Deep severe scratch across the entire door")
    assert calibrate_severity(review, claim) == "medium"


def test_non_windshield_minor_hairline_crack_can_be_low() -> None:
    review = _review("supported", "crack", "medium", object_part="body")
    claim = _claim("Tiny hairline crack on the body paint")
    assert calibrate_severity(review, claim) == "low"


def test_severe_dent_can_be_high() -> None:
    review = _review("supported", "dent", "medium")
    claim = _claim("Large severe dent, door is unusable")
    assert calibrate_severity(review, claim) == "high"


def test_windshield_crack_predicted_low_becomes_medium() -> None:
    review = _review("supported", "crack", "low", object_part="windshield")
    claim = _claim("A small stone hit the windshield and left a crack")
    assert calibrate_severity(review, claim) == "medium"


def test_windshield_crack_predicted_high_becomes_medium_without_severe_wording() -> None:
    review = _review("supported", "crack", "high", object_part="windshield")
    claim = _claim("There is a crack in the windshield")
    assert calibrate_severity(review, claim) == "medium"


def test_windshield_crack_with_severe_wording_can_be_high() -> None:
    review = _review("supported", "crack", "medium", object_part="windshield")
    claim = _claim("Large severe crack spreading across the windshield")
    assert calibrate_severity(review, claim) == "high"


def test_windshield_glass_shatter_remains_high() -> None:
    review = _review("supported", "glass_shatter", "high", object_part="windshield")
    claim = _claim("The windshield is shattered")
    assert calibrate_severity(review, claim) == "high"


def test_non_windshield_crack_without_minor_wording_stays_medium() -> None:
    review = _review("supported", "crack", "medium", object_part="body")
    claim = _claim("There is a crack in the body panel")
    assert calibrate_severity(review, claim) == "medium"


def test_issue_type_none_returns_none() -> None:
    review = _review("supported", "none", "medium")
    claim = _claim("Everything looks fine")
    assert calibrate_severity(review, claim) == "none"
