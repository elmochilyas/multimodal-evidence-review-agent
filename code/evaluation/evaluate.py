"""Evaluation runner for the evidence review system."""

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure code/ is importable when running from evaluation/ directory
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.evaluation_metrics import (
    COMPARED_FIELDS,
    compute_exact_match_accuracy,
    compute_failure_categories,
    compute_failure_summary,
    compute_field_accuracy,
    fields_match,
    split_sample_rows,
)
from src.io_utils import load_csv, load_evidence_requirements, load_user_history, write_output_csv
from src.reviewer import ReviewConfig, review_claims
from src.validation import validate_output_row


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate evidence review predictions against sample_claims.csv labels."
    )
    parser.add_argument(
        "--sample",
        required=True,
        help="Path to sample_claims.csv with input and expected output labels.",
    )
    parser.add_argument(
        "--user-history",
        default="../dataset/user_history.csv",
        help="Path to user_history.csv for history risk enrichment.",
    )
    parser.add_argument(
        "--evidence-requirements",
        default="../dataset/evidence_requirements.csv",
        help="Path to evidence_requirements.csv for the minimum evidence checklist.",
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Path to write the Markdown evaluation report.",
    )
    parser.add_argument(
        "--mode",
        choices=["baseline", "mock", "live"],
        default="baseline",
        help="Review mode to evaluate: baseline, mock, or live.",
    )
    parser.add_argument(
        "--model-provider",
        default=None,
        help="Model provider name for live mode.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Vision model name for live mode.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Evaluate only the first N sample rows.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable model response caching.",
    )
    parser.add_argument(
        "--cache-dir",
        default=".cache/model_responses",
        help="Directory for model response cache.",
    )
    parser.add_argument(
        "--predictions-out",
        default=None,
        help="Optional path to write predicted output rows as CSV.",
    )
    parser.add_argument(
        "--mismatches-out",
        default=None,
        help="Optional path to write per-field mismatch details as CSV.",
    )
    return parser.parse_args(argv)


def run_evaluation(
    sample_path: str,
    mode: str = "baseline",
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    limit: Optional[int] = None,
    use_cache: bool = True,
    cache_dir: str = ".cache/model_responses",
    user_history_path: str = "../dataset/user_history.csv",
    evidence_requirements_path: str = "../dataset/evidence_requirements.csv",
) -> dict:
    """Run the current reviewer on sample claims and compute metrics."""
    sample_rows = load_csv(sample_path)
    if limit is not None and limit > 0:
        sample_rows = sample_rows[:limit]

    input_rows, expected_rows = split_sample_rows(sample_rows)

    # CSV image paths are relative to the dataset/ directory.
    base_dir = str(Path(sample_path).parent)
    user_history = load_user_history(user_history_path)
    evidence_requirements = load_evidence_requirements(evidence_requirements_path)
    config = ReviewConfig(
        mode=mode,
        provider_name=provider_name,
        model=model,
        cache_dir=cache_dir,
        use_cache=use_cache,
        base_dir=base_dir,
        user_history=user_history,
        evidence_requirements=evidence_requirements,
    )

    start_time = time.perf_counter()
    predicted_rows = review_claims(input_rows, config)
    elapsed = time.perf_counter() - start_time

    # Validate each predicted row
    validation_errors: list[str] = []
    for idx, (pred, inp) in enumerate(zip(predicted_rows, input_rows), start=1):
        valid, errors = validate_output_row(pred, inp)
        if not valid:
            for err in errors:
                validation_errors.append(f"Row {idx}: {err}")

    field_accuracy = compute_field_accuracy(predicted_rows, expected_rows)
    exact_match = compute_exact_match_accuracy(predicted_rows, expected_rows)
    failure_summary = compute_failure_summary(predicted_rows, expected_rows)
    failure_categories = compute_failure_categories(predicted_rows, expected_rows)

    return {
        "sample_count": len(sample_rows),
        "predicted_rows": predicted_rows,
        "expected_rows": expected_rows,
        "field_accuracy": field_accuracy,
        "exact_match_accuracy": exact_match,
        "failure_summary": failure_summary,
        "failure_categories": failure_categories,
        "validation_errors": validation_errors,
        "elapsed_seconds": elapsed,
    }


def generate_report(results: dict, sample_path: str, mode: str = "baseline") -> str:
    """Generate the Markdown evaluation report."""
    lines: list[str] = []
    lines.append("# Evidence Review Evaluation Report")
    lines.append("")
    lines.append(f"**Sample file:** `{sample_path}`")
    lines.append(f"**Mode:** `{mode}`")
    lines.append(f"**Sample row count:** {results['sample_count']}")
    lines.append(f"**Run timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    lines.append("")

    lines.append("## Summary Metrics")
    lines.append("")
    lines.append(f"- **Exact row accuracy:** {results['exact_match_accuracy']:.2%}")
    lines.append("")

    lines.append("## Per-Field Accuracy")
    lines.append("")
    lines.append("| Field | Accuracy |")
    lines.append("|---|---|")
    for field in COMPARED_FIELDS:
        acc = results["field_accuracy"][field]
        lines.append(f"| {field} | {acc:.2%} |")
    lines.append("")

    lines.append("## Failure Summary")
    lines.append("")
    lines.append("| Field | Mismatched Rows |")
    lines.append("|---|---|")
    for field in COMPARED_FIELDS:
        rows = results["failure_summary"][field]
        count = len(rows)
        row_str = ", ".join(str(r) for r in rows[:10])
        if len(rows) > 10:
            row_str += f", ... ({len(rows) - 10} more)"
        lines.append(f"| {field} | {count} ({row_str}) |")
    lines.append("")

    lines.append("## Failure Categories")
    lines.append("")
    lines.append("| Category | Row Count |")
    lines.append("|---|---|")
    for category, count in results["failure_categories"].items():
        lines.append(f"| {category} | {count} |")
    lines.append("")

    if results["validation_errors"]:
        lines.append("## Validation Errors")
        lines.append("")
        lines.append("Predicted rows had schema/enum validation errors:")
        for err in results["validation_errors"][:20]:
            lines.append(f"- {err}")
        if len(results["validation_errors"]) > 20:
            lines.append(f"- ... and {len(results['validation_errors']) - 20} more")
        lines.append("")
    else:
        lines.append("## Validation")
        lines.append("")
        lines.append("All predicted rows passed schema and enum validation.")
        lines.append("")

    if mode == "baseline":
        lines.append("## Known Baseline Limitations")
        lines.append("")
        lines.append(
            "The current reviewer is a safe baseline that does not inspect images or "
            "extract claims. It emits the same placeholder row for every claim: "
            "`claim_status=not_enough_information`, `issue_type=unknown`, `object_part=unknown`, "
            "`severity=unknown`, `evidence_standard_met=false`, `valid_image=false`, "
            "`supporting_image_ids=none`, and `risk_flags=manual_review_required`."
        )
        lines.append("")
        lines.append(
            "As a result, it cannot correctly evaluate claims where the image evidence "
            "clearly supports or contradicts the user's claim. The primary purpose of this "
            "baseline is to prove the pipeline, schema validation, and evaluation workflow "
            "before adding vision-based review."
        )
        lines.append("")

        lines.append("## Next Targeted Improvements")
        lines.append("")
        lines.append("1. Add a vision-capable model call to inspect submitted images.")
        lines.append("2. Extract the claimed issue type and object part from the conversation.")
        lines.append("3. Match claims against evidence requirements to decide `evidence_standard_met`.")
        lines.append("4. Enrich risk flags from user history without overriding visual evidence.")
        lines.append("5. Detect prompt-injection text in user claims and images.")
        lines.append("6. Add retry/fallback logic for invalid model outputs.")
        lines.append("")

    lines.append("## Operational Analysis")
    lines.append("")
    if mode == "baseline":
        lines.append("- **Model calls for sample processing:** 0")
        lines.append("- **Model calls for test processing:** 0")
        lines.append("- **Images processed:** 0")
        lines.append("- **Approximate cost:** $0.00 (no model calls)")
        lines.append(
            f"- **Latency/runtime:** {results['elapsed_seconds']:.4f}s for {results['sample_count']} sample rows"
        )
        lines.append("- **TPM/RPM considerations:** N/A; no API calls made.")
        lines.append("- **Batching/throttling/caching/retry:** Not required for baseline mode.")
    else:
        lines.append(f"- **Mode:** {mode}")
        lines.append(f"- **Model calls for sample processing:** {results['sample_count']}")
        lines.append("- **Model calls for test processing:** TBD after full test run")
        lines.append("- **Images processed:** TBD")
        lines.append("- **Approximate cost:** TBD after model pricing is applied")
        lines.append(
            f"- **Latency/runtime:** {results['elapsed_seconds']:.4f}s for {results['sample_count']} sample rows"
        )
        lines.append(
            "- **TPM/RPM considerations:** Sequential processing keeps rate-limit usage low. "
            "Retry is enabled for invalid JSON/enum outputs. Caching avoids repeated identical calls."
        )
        lines.append(
            "- **Batching/throttling/caching/retry:** Responses are cached per claim + image set + model + prompt version. "
            "Invalid outputs trigger one repair retry before safe fallback."
        )
    lines.append("")

    return "\n".join(lines)


def write_predictions_csv(path: str, predicted_rows: list[dict]) -> None:
    """Persist predicted rows to a CSV using the standard output schema."""
    write_output_csv(path, predicted_rows)


def write_mismatches_csv(
    path: str,
    predicted_rows: list[dict],
    expected_rows: list[dict],
) -> None:
    """Persist per-field mismatches as CSV with columns row_index,user_id,field,expected,predicted."""
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)

    with resolved.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["row_index", "user_id", "field", "expected", "predicted"],
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for idx, (pred, exp) in enumerate(zip(predicted_rows, expected_rows), start=1):
            for field in COMPARED_FIELDS:
                if not fields_match(pred, exp, field):
                    writer.writerow(
                        {
                            "row_index": idx,
                            "user_id": pred.get("user_id", ""),
                            "field": field,
                            "expected": exp.get(field, ""),
                            "predicted": pred.get(field, ""),
                        }
                    )


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)

    results = run_evaluation(
        args.sample,
        mode=args.mode,
        provider_name=args.model_provider,
        model=args.model,
        limit=args.limit,
        use_cache=not args.no_cache,
        cache_dir=args.cache_dir,
        user_history_path=args.user_history,
        evidence_requirements_path=args.evidence_requirements,
    )
    report = generate_report(results, args.sample, mode=args.mode)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    if args.predictions_out:
        write_predictions_csv(args.predictions_out, results["predicted_rows"])
        print(f"Predictions written to: {args.predictions_out}")

    if args.mismatches_out:
        write_mismatches_csv(
            args.mismatches_out,
            results["predicted_rows"],
            results["expected_rows"],
        )
        print(f"Mismatches written to: {args.mismatches_out}")

    print(f"Evaluated {results['sample_count']} sample rows in '{args.mode}' mode.")
    print(f"Exact row accuracy: {results['exact_match_accuracy']:.2%}")
    print("Per-field accuracy:")
    for field in COMPARED_FIELDS:
        print(f"  {field}: {results['field_accuracy'][field]:.2%}")
    print(f"Report written to: {args.report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
