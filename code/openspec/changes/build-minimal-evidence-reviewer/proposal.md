## Why

The HackerRank Orchestrate June 2026 challenge requires building a multi-modal evidence review system that verifies damage claims using images, claim conversations, user history, and minimum evidence requirements. The system must produce a strict-schema `output.csv` for 44 test claims and include an evaluation workflow. A minimal, reliable, single-agent implementation maximizes correctness, reproducibility, and interview defensibility within the 24-hour time limit.

## What Changes

- Create a Python CLI evidence-review agent inside `code/` that reads `dataset/claims.csv`, inspects local images with a vision-capable model, and writes `output.csv` with the exact required schema.
- Implement CSV input loading for claims, user history, and evidence requirements.
- Implement structured output validation for all enum fields, column order, and object-specific part values.
- Implement a vision-capable model review flow that extracts claims, inspects images, and produces image-grounded decisions.
- Implement evidence requirement lookup to determine `evidence_standard_met`.
- Implement user history risk enrichment that adds risk flags without overriding visual evidence.
- Implement prompt-injection guardrails for untrusted user text and instruction-bearing images.
- Implement retry/fallback handling for invalid model outputs, defaulting to safe `not_enough_information`.
- Implement a sample evaluation script that compares predictions against `dataset/sample_claims.csv`.
- Implement evaluation report generation with operational analysis metrics.
- Implement debug logging for transcript evidence and AI Judge explainability.
- Add README with setup, environment variables, run commands, and evaluation instructions.

## Capabilities

### New Capabilities

- `project-contract`: Defines the repo layout, entry-point contract, dependency policy, and submission packaging constraints that make the solution evaluable.
- `input-output-contract`: Specifies the exact input CSV schemas (claims, user_history, evidence_requirements) and the exact output.csv column order, allowed enum values, and object-specific part lists.
- `evidence-review-agent`: Covers the core agent pipeline: claim extraction, VLM image inspection, evidence requirement matching, user history enrichment, decision logic, and structured output assembly.
- `validation-guardrails`: Covers strict output validation (enums, schema, object-part consistency), prompt-injection detection, text_instruction_present handling, authenticity flagging, and safe fallback for malformed inputs.
- `evaluation-workflow`: Covers the sample evaluation script, per-field accuracy metrics, failure categorization, evaluation report with operational analysis, and comparison of at least two strategies.
- `submission-hardening`: Covers final dry-run checks, code.zip packaging constraints, README completeness, transcript/logging readiness, and pre-submission quality gates.

### Modified Capabilities

(none — this is a greenfield implementation)

## Impact

- **Code**: All new files created inside `code/`. Entry point at `code/main.py`. Evaluation at `code/evaluation/`.
- **Dependencies**: Python 3.10+, `openai` or `anthropic` SDK (vision-capable model), `pandas` or `csv` stdlib, `Pillow` for image loading. Minimal dependency footprint.
- **APIs**: Requires one vision-capable model API key via environment variable (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`).
- **Datasets**: Reads from `../dataset/` relative to `code/`. Does not modify dataset files.
- **Output**: Writes `output.csv` at repo root. Writes `evaluation/evaluation_report.md` inside `code/evaluation/`.
- **Submission**: Produces `code.zip`, `output.csv`, and `chat_transcript/log.txt` as deliverables.
