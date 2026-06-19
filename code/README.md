# Multi-Modal Evidence Review Agent

A Python CLI system that verifies damage claims using submitted images, claim conversations, user history, and minimum evidence requirements.

## Milestone 1: Pipeline + Schema + Baseline Reviewer

This milestone proves the project structure, CSV I/O, strict output schema validation, and a safe baseline reviewer that produces valid placeholder rows without calling any model.

### Setup

```bash
pip install -r requirements.txt
```

### Run the baseline reviewer

```bash
python main.py --input ../dataset/claims.csv --output ../output.csv
```

This produces `output.csv` with one row per input row. In Milestone 1, every row is a safe placeholder:

- `evidence_standard_met=false`
- `claim_status=not_enough_information`
- `issue_type=unknown`
- `object_part=unknown`
- `severity=unknown`
- `valid_image=false`
- `supporting_image_ids=none`
- `risk_flags=manual_review_required`

> **Warning:** The baseline reviewer is intentionally not the final answer. It is a pipeline placeholder used to validate schema, CLI, and evaluation workflow before adding vision-based review in later milestones.

### Validate the output

```bash
python -m src.validate_output --input ../dataset/claims.csv --output ../output.csv
```

### Run tests

```bash
python -m pytest
```

## Milestone 2: Evaluation Workflow and Baseline Failure Analysis

Run the evaluation workflow against the labeled sample claims to measure baseline performance and identify where the system needs to improve.

### Run evaluation

```bash
python evaluation/evaluate.py --sample ../dataset/sample_claims.csv --report evaluation/evaluation_report.md
```

This command:

- Loads `dataset/sample_claims.csv` (inputs + expected outputs)
- Generates predictions using the current reviewer pipeline
- Compares predictions against expected labels
- Prints per-field and exact-row accuracy to the console
- Writes a Markdown report to `evaluation/evaluation_report.md`

### What the baseline measures

Because the baseline does not inspect images or extract claims, it is expected to match only the rows where the expected answer is the safe placeholder (`not_enough_information`, `unknown`, etc.). The evaluation report shows exactly which fields and rows fail, guiding the next improvements.

## Milestone 3: VLM Review Abstraction, Structured Output, Retry/Fallback, and Caching

This milestone adds a minimal but robust vision-model integration layer. It keeps the baseline path intact so the system remains safe even when no API key is configured.

### Run modes

The CLI and evaluation runner support three modes:

- `baseline` — no model calls; produces safe placeholder rows (default)
- `mock` — uses a fake provider for no-cost smoke tests
- `live` — calls a vision-capable model via the configured provider

```bash
# Baseline (default, no API key needed)
python main.py --input ../dataset/claims.csv --output ../output.csv --mode baseline

# Mock smoke test (no API key needed)
python main.py --input ../dataset/sample_claims.csv --output evaluation/sample_predictions.csv --mode mock --limit 3

# Live VLM run (requires API key configuration)
python main.py --input ../dataset/sample_claims.csv --output evaluation/sample_predictions.csv --mode live --limit 3
```

### Configuration

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

### Caching

Live model responses are cached in `.cache/model_responses/` by default. The cache key covers claim data, image paths, model name, and prompt version. To disable caching:

```bash
python main.py --input ../dataset/claims.csv --output ../output.csv --mode live --no-cache
```

Do not commit cache files.

### Project layout (after Milestone 3)

```text
code/
├── main.py                     # CLI entry point
├── requirements.txt            # pytest, openai
├── README.md                   # This file
├── src/
│   ├── __init__.py
│   ├── cache.py                # Model response cache
│   ├── constants.py            # Allowed enum values and output columns
│   ├── evaluation_metrics.py   # Evaluation comparison utilities
│   ├── image_utils.py          # Image loading and base64 encoding
│   ├── io_utils.py             # CSV loaders, image path helpers, output writer
│   ├── model_provider.py       # Mock + OpenAI-compatible providers
│   ├── model_review.py         # Model call orchestration, retry, fallback
│   ├── prompts.py              # Evidence review prompt templates
│   ├── reviewer.py             # Baseline + model review dispatcher
│   ├── validation.py           # Strict output schema/enums validator
│   └── validate_output.py      # Standalone validation CLI
├── evaluation/
│   ├── evaluate.py             # Evaluation runner CLI
│   └── evaluation_report.md    # Generated evaluation report
└── tests/
    ├── conftest.py
    ├── test_cli.py
    ├── test_evaluation_metrics.py
    ├── test_io_utils.py
    ├── test_model_review.py
    ├── test_reviewer.py
    └── test_validation.py
```

### Environment variables

No API keys are required to run tests, baseline mode, or mock mode. For live VLM mode, configure:

```bash
export MODEL_PROVIDER=openai_compatible
export OPENAI_API_KEY="your-key-here"
export VISION_MODEL="gpt-4o"
```

Never commit secrets to the repository.
