# Multi-Modal Evidence Review Agent

A Python CLI system for the HackerRank Orchestrate June 2026 challenge that verifies damage claims using submitted images, a short claim conversation, user claim history, and minimum image evidence requirements.

## Challenge objective

For every row in `dataset/claims.csv`, decide whether the submitted images support the user's claim, contradict it, or do not provide enough information. Produce `output.csv` with the exact schema and column order required by the challenge.

## Input files

| File | Purpose |
|---|---|
| `dataset/claims.csv` | One claim per row: `user_id`, `image_paths`, `user_claim`, `claim_object`. |
| `dataset/user_history.csv` | Historical claim counts and risk flags per user. |
| `dataset/evidence_requirements.csv` | Minimum image evidence checklist by object and issue family. |
| `dataset/images/test/` | Local images referenced by `claims.csv`. |
| `dataset/sample_claims.csv` | Labeled sample rows for development and evaluation. |

## Output file

`output.csv` must contain one row per input claim with these columns in order:

```text
user_id,image_paths,user_claim,claim_object,evidence_standard_met,evidence_standard_met_reason,risk_flags,issue_type,object_part,claim_status,claim_status_justification,supporting_image_ids,valid_image,severity
```

Allowed values follow `problem_statement.md` and are enforced by `src/validation.py`.

## Architecture

```text
┌─────────────────┐     ┌─────────────────────────────┐     ┌──────────────────┐
│  claims.csv     │────▶│  Single-agent VLM reviewer  │────▶│  output.csv      │
│  user_history   │     │  (src/model_review.py)      │     │                  │
│  evidence_reqs  │     └──────────────┬──────────────┘     └──────────────────┘
│  images         │                    │
└─────────────────┘     ┌──────────────▼──────────────┐
                        │  Deterministic guardrails   │
                        │  (src/post_processing.py)   │
                        │  Severity calibration       │
                        │  (src/severity.py)          │
                        └─────────────────────────────┘
```

- **Images are the primary source of truth.** Every image is opened with Pillow, EXIF-oriented, converted to RGB, and encoded as a JPEG data URL before being sent to the vision API. The user's conversation only tells the reviewer what to look for.
- **User history adds risk context only.** It contributes `user_history_risk` and `manual_review_required` flags but never overrides clear visual evidence.
- **Evidence requirements are used in both the main pipeline and evaluation.** They are injected into the model prompt so the reviewer knows the minimum evidence standard for each object/issue family.
- **Conservative guardrails.** Post-processing only changes core labels when the contradiction or evidence gap is unambiguous (wrong object/part flagged by the model, package contents claim with only exterior photos, missing supporting image IDs for contradicted claims).
- **Safe fallbacks.** Any API, parsing, image, or validation failure produces a deterministic safe row (`claim_status=not_enough_information`, `valid_image=false`, `manual_review_required`).

## Setup

```bash
pip install -r requirements.txt
```

The project requires Python 3.10+.

## Safe local API key setup

The pipeline reads secrets from environment variables. For local development, copy the example file and put your real key in `.env`:

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=your_real_key
```

On Windows (PowerShell):

```powershell
Copy-Item .env.example .env
# Edit .env and set OPENAI_API_KEY=your_real_key
```

Rules:

- Never commit `.env`, `.env.local`, or any file containing a real API key.
- Never paste API keys into chat logs, terminal output, or submission files.
- `.env` is already excluded from git and from `code.zip` by `.gitignore`.
- The program reads the key from the `OPENAI_API_KEY` environment variable (loaded from `.env` automatically by `python-dotenv`).

## Run the final pipeline

```bash
python main.py \
  --input ../dataset/claims.csv \
  --output ../output.csv \
  --mode live \
  --no-cache
```

On Windows (PowerShell):

```powershell
python main.py `
  --input ../dataset/claims.csv `
  --output ../output.csv `
  --mode live `
  --no-cache
```

## Validate the output

```bash
python -m src.validate_output --input ../dataset/claims.csv --output ../output.csv
```

## Run sample evaluation

```bash
python evaluation/evaluate.py \
  --sample ../dataset/sample_claims.csv \
  --report evaluation/evaluation_report.md \
  --mode live \
  --no-cache
```

The wrapper entry point also works:

```bash
python evaluation/main.py \
  --sample ../dataset/sample_claims.csv \
  --report evaluation/evaluation_report_check.md \
  --mode mock \
  --limit 5
```

## Run tests

```bash
python -m pytest
```

## Modes

| Mode | Description |
|---|---|
| `baseline` | No model calls; emits safe placeholder rows (default, no API key needed). |
| `mock` | Uses a configurable fake provider for no-cost smoke tests. |
| `live` | Calls a vision-capable model via the configured provider. |

## Configuration

Set via environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `MODEL_PROVIDER` | Provider type: `mock` or `openai_compatible` | `mock` |
| `MODEL_MODE` | Default CLI mode: `baseline`, `mock`, or `live` | `baseline` |
| `OPENAI_API_KEY` | API key for live mode | (none) |
| `OPENAI_BASE_URL` | Optional base URL for OpenAI-compatible endpoints | (none) |
| `VISION_MODEL` | Vision model name | `gpt-4o` |
| `MODEL_TEMPERATURE` | Sampling temperature | `0.0` |

Never commit secrets. Use environment variables or a local `.env` file that is excluded from `code.zip`.

## Project layout

```text
code/
├── main.py                     # CLI entry point
├── requirements.txt            # pytest, openai, Pillow
├── README.md                   # This file
├── src/
│   ├── cache.py                # Model response cache
│   ├── constants.py            # Allowed enum values and output columns
│   ├── evaluation_metrics.py   # Evaluation comparison utilities
│   ├── fix_output_consistency.py  # Deterministic output consistency helper
│   ├── image_utils.py          # Pillow-based image normalization
│   ├── io_utils.py             # CSV loaders, image path helpers, output writer
│   ├── model_provider.py       # Mock + OpenAI-compatible providers
│   ├── model_review.py         # Model call orchestration, retry, fallback
│   ├── post_processing.py      # Conservative deterministic guardrails
│   ├── prompts.py              # Evidence review prompt templates
│   ├── reviewer.py             # Baseline + model review dispatcher
│   ├── severity.py             # Deterministic severity calibration
│   ├── validate_output.py      # Standalone validation CLI
│   └── validation.py           # Strict output schema/enums validator
├── evaluation/
│   ├── evaluate.py             # Evaluation runner CLI
│   ├── evaluation_report.md    # Generated evaluation report
│   └── main.py                 # Thin wrapper around evaluate.py
└── tests/
    ├── conftest.py
    ├── test_cli.py
    ├── test_evaluation_metrics.py
    ├── test_image_utils.py
    ├── test_io_utils.py
    ├── test_model_review.py
    ├── test_post_processing.py
    ├── test_reviewer.py
    ├── test_severity.py
    └── test_validation.py
```

## Package a clean `code.zip`

From the repo root:

```powershell
# Clean generated artifacts
Remove-Item -Recurse -Force .cache -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force code\.cache -ErrorAction SilentlyContinue
Get-ChildItem code -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Get-ChildItem code -Recurse -Directory -Filter .pytest_cache | Remove-Item -Recurse -Force
Get-ChildItem code\evaluation -File -Filter *.csv | Remove-Item -Force
Remove-Item code\evaluation\evaluation_report_check.md -Force -ErrorAction SilentlyContinue
Remove-Item code.zip -Force -ErrorAction SilentlyContinue

# Create the zip
Compress-Archive -Path code\* -DestinationPath code.zip -Force

# Verify secrets/env files are NOT inside the zip
if (Expand-Archive code.zip -DestinationPath _zip_check_ -Force; Get-ChildItem _zip_check_ -Recurse -Include .env,.env.* -Force) { Write-Host "ERROR: .env files found in zip!" } else { Write-Host "OK: no .env files in zip." }
Remove-Item -Recurse -Force _zip_check_
```

`output.csv` must remain **outside** `code.zip`.

### What must NOT be in `code.zip`

- `dataset/` (images and CSVs)
- `.cache/` or `code/.cache/`
- `__pycache__/` or `.pytest_cache/`
- `node_modules/`
- `.venv/`, `venv/`, `env/`
- `.env` or `.env.*`
- Generated evaluation CSVs (`sample_predictions.csv`, `mismatches.csv`, etc.)
- `output.csv`, `output_locked_*.csv`
- `mock_eval_report.md`, `evaluation_report_check.md`

## Submission checklist

- [ ] `python -m pytest` passes.
- [ ] `python -m src.validate_output --input ../dataset/claims.csv --output ../output.csv` reports valid.
- [ ] `output.csv` is produced and stored outside `code.zip`.
- [ ] `code.zip` is clean (no datasets, caches, env files, node_modules, build artifacts).
- [ ] `evaluation/main.py` smoke test works.
- [ ] `%USERPROFILE%\hackerrank_orchestrate\log.txt` is up to date and contains no secrets.
