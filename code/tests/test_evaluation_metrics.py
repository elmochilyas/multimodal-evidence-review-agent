"""Tests for evaluation metric utilities."""

from src.evaluation_metrics import (
    COMPARED_FIELDS,
    categorize_failure,
    compute_exact_match_accuracy,
    compute_failure_categories,
    compute_failure_summary,
    compute_field_accuracy,
    exact_row_match,
    fields_match,
    normalize_set,
    split_sample_rows,
)


def test_normalize_set_empty() -> None:
    assert normalize_set("") == frozenset()
    assert normalize_set("none") == frozenset()
    assert normalize_set("NONE") == frozenset()


def test_normalize_set_tokens() -> None:
    assert normalize_set("a;b;c") == frozenset({"a", "b", "c"})
    assert normalize_set("b;a;c") == frozenset({"a", "b", "c"})


def test_fields_match_scalar() -> None:
    pred = {"claim_status": "supported"}
    exp = {"claim_status": "supported"}
    assert fields_match(pred, exp, "claim_status") is True


def test_fields_match_scalar_mismatch() -> None:
    pred = {"claim_status": "supported"}
    exp = {"claim_status": "contradicted"}
    assert fields_match(pred, exp, "claim_status") is False


def test_fields_match_semicolon_set() -> None:
    pred = {"risk_flags": "b;a"}
    exp = {"risk_flags": "a;b"}
    assert fields_match(pred, exp, "risk_flags") is True


def test_fields_match_semicolon_set_mismatch() -> None:
    pred = {"risk_flags": "a"}
    exp = {"risk_flags": "a;b"}
    assert fields_match(pred, exp, "risk_flags") is False


def test_exact_row_match_all_fields() -> None:
    pred = {field: "x" for field in COMPARED_FIELDS}
    exp = {field: "x" for field in COMPARED_FIELDS}
    pred["user_id"] = exp["user_id"] = "u1"
    assert exact_row_match(pred, exp) is True


def test_exact_row_match_partial_mismatch() -> None:
    pred = {field: "x" for field in COMPARED_FIELDS}
    exp = {field: "x" for field in COMPARED_FIELDS}
    pred["claim_status"] = "supported"
    exp["claim_status"] = "contradicted"
    assert exact_row_match(pred, exp) is False


def test_compute_field_accuracy() -> None:
    preds = [
        {"claim_status": "supported", "issue_type": "dent"},
        {"claim_status": "supported", "issue_type": "scratch"},
    ]
    exps = [
        {"claim_status": "supported", "issue_type": "dent"},
        {"claim_status": "contradicted", "issue_type": "scratch"},
    ]
    acc = compute_field_accuracy(preds, exps)
    assert acc["claim_status"] == 0.5
    assert acc["issue_type"] == 1.0


def test_compute_exact_match_accuracy() -> None:
    preds = [
        {"claim_status": "supported"},
        {"claim_status": "supported"},
    ]
    exps = [
        {"claim_status": "supported"},
        {"claim_status": "contradicted"},
    ]
    assert compute_exact_match_accuracy(preds, exps) == 0.5


def test_compute_failure_summary() -> None:
    preds = [
        {"claim_status": "supported", "issue_type": "dent"},
        {"claim_status": "supported", "issue_type": "scratch"},
    ]
    exps = [
        {"claim_status": "supported", "issue_type": "dent"},
        {"claim_status": "contradicted", "issue_type": "scratch"},
    ]
    summary = compute_failure_summary(preds, exps)
    assert summary["claim_status"] == [2]
    assert summary["issue_type"] == []


def test_categorize_failure_visual_review() -> None:
    pred = {"claim_status": "supported"}
    exp = {"claim_status": "contradicted"}
    assert "visual_review" in categorize_failure(pred, exp)


def test_categorize_failure_claim_extraction() -> None:
    pred = {"issue_type": "dent", "object_part": "door"}
    exp = {"issue_type": "scratch", "object_part": "door"}
    assert "claim_extraction" in categorize_failure(pred, exp)


def test_compute_failure_categories() -> None:
    preds = [
        {"claim_status": "supported", "issue_type": "dent"},
        {"claim_status": "supported", "issue_type": "scratch"},
    ]
    exps = [
        {"claim_status": "supported", "issue_type": "dent"},
        {"claim_status": "contradicted", "issue_type": "scratch"},
    ]
    cats = compute_failure_categories(preds, exps)
    assert cats["visual_review"] == 1
    assert cats["claim_extraction"] == 0


def test_split_sample_rows() -> None:
    sample = [
        {
            "user_id": "u1",
            "image_paths": "a.jpg",
            "user_claim": "claim",
            "claim_object": "car",
            "evidence_standard_met": "true",
            "claim_status": "supported",
        }
    ]
    inputs, expected = split_sample_rows(sample)
    assert inputs[0] == {
        "user_id": "u1",
        "image_paths": "a.jpg",
        "user_claim": "claim",
        "claim_object": "car",
    }
    assert expected[0]["claim_status"] == "supported"
    assert expected[0]["evidence_standard_met"] == "true"


def test_report_generation_creates_markdown(tmp_path) -> None:
    from evaluation.evaluate import generate_report, run_evaluation

    sample_path = tmp_path / "sample.csv"
    sample_path.write_text(
        'user_id,image_paths,user_claim,claim_object,'
        'evidence_standard_met,evidence_standard_met_reason,risk_flags,issue_type,object_part,'
        'claim_status,claim_status_justification,supporting_image_ids,valid_image,severity\n'
        'u1,a.jpg,claim,car,true,,none,dent,door,supported,,img_1,true,low\n',
        encoding="utf-8",
    )

    results = run_evaluation(str(sample_path))
    report = generate_report(results, str(sample_path))

    assert "# Evidence Review Evaluation Report" in report
    assert "## Per-Field Accuracy" in report
    assert "## Operational Analysis" in report
    assert "**Model calls for sample processing:** 0" in report


def test_write_predictions_csv(tmp_path) -> None:
    from evaluation.evaluate import run_evaluation, write_predictions_csv

    sample_path = tmp_path / "sample.csv"
    sample_path.write_text(
        'user_id,image_paths,user_claim,claim_object,'
        'evidence_standard_met,evidence_standard_met_reason,risk_flags,issue_type,object_part,'
        'claim_status,claim_status_justification,supporting_image_ids,valid_image,severity\n'
        'u1,a.jpg,claim,car,true,,none,dent,door,supported,,img_1,true,low\n',
        encoding="utf-8",
    )
    predictions_path = tmp_path / "predictions.csv"

    results = run_evaluation(str(sample_path))
    write_predictions_csv(str(predictions_path), results["predicted_rows"])

    assert predictions_path.exists()
    text = predictions_path.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    assert len(lines) == 2  # header + 1 data row
    assert lines[0].startswith("user_id,image_paths,user_claim,claim_object,")
    assert "u1" in lines[1]


def test_write_mismatches_csv(tmp_path) -> None:
    from evaluation.evaluate import run_evaluation, write_mismatches_csv

    sample_path = tmp_path / "sample.csv"
    sample_path.write_text(
        'user_id,image_paths,user_claim,claim_object,'
        'evidence_standard_met,evidence_standard_met_reason,risk_flags,issue_type,object_part,'
        'claim_status,claim_status_justification,supporting_image_ids,valid_image,severity\n'
        'u1,a.jpg,claim,car,true,,none,dent,door,supported,,img_1,true,low\n'
        'u2,b.jpg,claim,car,true,,none,scratch,front_bumper,supported,,img_1,true,low\n',
        encoding="utf-8",
    )
    mismatches_path = tmp_path / "mismatches.csv"

    results = run_evaluation(str(sample_path))
    write_mismatches_csv(
        str(mismatches_path),
        results["predicted_rows"],
        results["expected_rows"],
    )

    assert mismatches_path.exists()
    text = mismatches_path.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    assert len(lines) >= 2  # header + at least one mismatch
    assert lines[0] == "row_index,user_id,field,expected,predicted"

    # Baseline mode should mismatch on most fields for every row.
    fields_with_mismatches = {line.split(",")[2] for line in lines[1:]}
    assert "severity" in fields_with_mismatches
    assert "issue_type" in fields_with_mismatches


def test_main_with_diagnostics_outputs(tmp_path) -> None:
    from evaluation.evaluate import main

    sample_path = tmp_path / "sample.csv"
    sample_path.write_text(
        'user_id,image_paths,user_claim,claim_object,'
        'evidence_standard_met,evidence_standard_met_reason,risk_flags,issue_type,object_part,'
        'claim_status,claim_status_justification,supporting_image_ids,valid_image,severity\n'
        'u1,a.jpg,claim,car,true,,none,dent,door,supported,,img_1,true,low\n',
        encoding="utf-8",
    )
    report_path = tmp_path / "report.md"
    predictions_path = tmp_path / "predictions.csv"
    mismatches_path = tmp_path / "mismatches.csv"

    code = main(
        [
            "--sample",
            str(sample_path),
            "--report",
            str(report_path),
            "--predictions-out",
            str(predictions_path),
            "--mismatches-out",
            str(mismatches_path),
        ]
    )

    assert code == 0
    assert report_path.exists()
    assert predictions_path.exists()
    assert mismatches_path.exists()
