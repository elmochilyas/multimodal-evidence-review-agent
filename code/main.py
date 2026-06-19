"""CLI entry point for the multi-modal evidence review agent."""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from src.io_utils import (
    load_claims,
    load_evidence_requirements,
    load_user_history,
    write_output_csv,
)
from src.reviewer import ReviewConfig, review_claims


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify damage claims using images, conversations, and history."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input claims CSV file (e.g., ../dataset/claims.csv).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the output CSV file (e.g., ../output.csv).",
    )
    parser.add_argument(
        "--user-history",
        default="../dataset/user_history.csv",
        help="Path to user_history.csv.",
    )
    parser.add_argument(
        "--evidence-requirements",
        default="../dataset/evidence_requirements.csv",
        help="Path to evidence_requirements.csv.",
    )
    parser.add_argument(
        "--mode",
        choices=["baseline", "mock", "live"],
        default=os.environ.get("MODEL_MODE", "baseline"),
        help="Review mode: baseline (no model), mock (fake provider), or live (VLM).",
    )
    parser.add_argument(
        "--model-provider",
        default=os.environ.get("MODEL_PROVIDER", "mock"),
        help="Model provider name for live mode (mock or openai_compatible).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("VISION_MODEL", None),
        help="Vision model name for live mode.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=float(os.environ.get("MODEL_TEMPERATURE", "0.0")),
        help="Sampling temperature for live model calls.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N claims (useful for smoke tests).",
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
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    """Run the evidence review pipeline."""
    args = parse_args(argv)

    input_path = args.input
    output_path = args.output

    # Load inputs
    claims = load_claims(input_path)
    user_history = load_user_history(args.user_history)
    evidence_requirements = load_evidence_requirements(args.evidence_requirements)

    if args.limit is not None and args.limit > 0:
        claims = claims[: args.limit]

    # Determine base directory for resolving relative image paths.
    # CSV image paths are relative to the dataset/ directory.
    base_dir = str(Path(input_path).parent)

    config = ReviewConfig(
        mode=args.mode,
        provider_name=args.model_provider,
        model=args.model,
        temperature=args.temperature,
        cache_dir=args.cache_dir,
        use_cache=not args.no_cache,
        base_dir=base_dir,
        evidence_requirements=evidence_requirements,
        user_history=user_history,
    )

    output_rows = review_claims(claims, config)

    # Write output
    write_output_csv(output_path, output_rows)

    print(f"Processed {len(output_rows)} claims in '{args.mode}' mode.")
    print(f"Output written to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
