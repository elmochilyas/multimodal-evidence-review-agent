"""Tests for the CLI entry point."""

from pathlib import Path

from main import main


def test_cli_writes_output_csv(tmp_path: Path) -> None:
    input_path = Path(__file__).parent / "data" / "claims.csv"
    output_path = tmp_path / "output.csv"

    code = main(["--input", str(input_path), "--output", str(output_path)])
    assert code == 0
    assert output_path.exists()

    text = output_path.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    assert len(lines) == 3  # header + 2 data rows
    assert lines[0].startswith("user_id,image_paths,user_claim,claim_object,")


def test_cli_baseline_mode(tmp_path: Path) -> None:
    input_path = Path(__file__).parent / "data" / "claims.csv"
    output_path = tmp_path / "output.csv"

    code = main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--mode",
            "baseline",
        ]
    )
    assert code == 0
    text = output_path.read_text(encoding="utf-8")
    assert "not_enough_information" in text


def test_cli_limit_flag(tmp_path: Path) -> None:
    input_path = Path(__file__).parent / "data" / "claims.csv"
    output_path = tmp_path / "output.csv"

    code = main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--mode",
            "baseline",
            "--limit",
            "1",
        ]
    )
    assert code == 0
    text = output_path.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    assert len(lines) == 2  # header + 1 data row
