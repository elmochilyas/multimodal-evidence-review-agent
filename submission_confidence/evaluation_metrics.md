# Submission Confidence — Evaluation Metrics

## Source

Metrics are taken from `code/evaluation/evaluation_report.md`, which reflects the **last successful live VLM run** on `dataset/sample_claims.csv`.

> ⚠️ A refresh was attempted in this audit session, but the API call failed with a **connection error** in this environment. The existing report was preserved. To refresh metrics locally, run the command in the "Manual refresh" section below.

## Sample Evaluation Summary

| Metric | Value |
|---|---|
| Sample rows | 20 |
| Exact row accuracy | **30.00%** |
| `evidence_standard_met` accuracy | 95.00% |
| `risk_flags` accuracy | 65.00% |
| `issue_type` accuracy | 55.00% |
| `object_part` accuracy | 80.00% |
| `claim_status` accuracy | **85.00%** |
| `valid_image` accuracy | 95.00% |
| `severity` accuracy | 50.00% |
| `supporting_image_ids` accuracy | 90.00% |

## Failure Summary (Sample Rows)

| Field | Mismatched Rows |
|---|---|
| `evidence_standard_met` | 1 (row 8) |
| `risk_flags` | 7 (rows 5, 6, 7, 8, 14, 19, 20) |
| `issue_type` | 9 (rows 4, 5, 6, 8, 11, 13, 14, 19, 20) |
| `object_part` | 4 (rows 5, 8, 16, 19) |
| `claim_status` | 3 (rows 14, 19, 20) |
| `valid_image` | 1 (row 8) |
| `severity` | 10 (rows 5, 8, 10, 12, 13, 14, 15, 16, 19, 20) |
| `supporting_image_ids` | 2 (rows 8, 20) |

## Failure Categories

| Category | Row Count |
|---|---|
| claim_extraction | 10 |
| visual_review | 3 |
| evidence_standard | 1 |
| risk_flags | 7 |
| severity | 10 |
| formatting | 2 |

## Per-Object Breakdown

A per-object (`car` / `laptop` / `package`) breakdown is **not available** in the existing report. It requires re-running the sample evaluation with predictions saved per row.

Heuristic analysis of the final `output.csv` (test set) shows:

| Object | Supported | Contradicted | Not Enough Info |
|---|---|---|---|
| car | 7 | 9 | 1 |
| laptop | 6 | 5 | 0 |
| package | 7 | 3 | 3 |

*(Derived from `output.csv` row counts; accuracy vs. ground truth is unknown.)*

## Manual Refresh Command

Run from the `code/` directory with a working internet connection and a valid API key configured in `code/.env` or environment variables:

```powershell
python evaluation/main.py `
  --sample ../dataset/sample_claims.csv `
  --report evaluation/evaluation_report.md `
  --mode live `
  --model-provider openai_compatible `
  --no-cache `
  --predictions-out ../submission_confidence/sample_predictions.csv `
  --mismatches-out ../submission_confidence/mismatches.csv
```

Then copy `code/evaluation/evaluation_report.md` into the regenerated `code.zip`.
