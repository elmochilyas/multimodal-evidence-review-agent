"""Standalone script to validate output.csv against input.csv."""

import argparse
import sys
from typing import Optional

from src.validation import validate_output_csv


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate output.csv schema and content.")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input claims CSV file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output CSV file to validate.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)
    is_valid, errors, row_count = validate_output_csv(args.output, args.input)

    print(f"Validated {row_count} output rows against {args.input}.")
    if is_valid:
        print("Output CSV is valid.")
        return 0

    print("Output CSV has validation errors:")
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
