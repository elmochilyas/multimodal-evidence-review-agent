# Evidence Review Evaluation Report

**Sample file:** `../dataset/sample_claims.csv`
**Mode:** `mock`
**Sample row count:** 3
**Run timestamp:** 2026-06-19 08:57:42 Morocco Daylight Time

## Summary Metrics

- **Exact row accuracy:** 0.00%

## Per-Field Accuracy

| Field | Accuracy |
|---|---|
| evidence_standard_met | 0.00% |
| risk_flags | 0.00% |
| issue_type | 0.00% |
| object_part | 0.00% |
| claim_status | 0.00% |
| valid_image | 0.00% |
| severity | 0.00% |
| supporting_image_ids | 0.00% |

## Failure Summary

| Field | Mismatched Rows |
|---|---|
| evidence_standard_met | 3 (1, 2, 3) |
| risk_flags | 3 (1, 2, 3) |
| issue_type | 3 (1, 2, 3) |
| object_part | 3 (1, 2, 3) |
| claim_status | 3 (1, 2, 3) |
| valid_image | 3 (1, 2, 3) |
| severity | 3 (1, 2, 3) |
| supporting_image_ids | 3 (1, 2, 3) |

## Failure Categories

| Category | Row Count |
|---|---|
| claim_extraction | 3 |
| visual_review | 3 |
| evidence_standard | 3 |
| risk_flags | 3 |
| severity | 3 |
| formatting | 3 |

## Validation

All predicted rows passed schema and enum validation.

## Operational Analysis

- **Mode:** mock
- **Model calls for sample processing:** 3
- **Model calls for test processing:** TBD after full test run
- **Images processed:** TBD
- **Approximate cost:** TBD after model pricing is applied
- **Latency/runtime:** 0.1648s for 3 sample rows
- **TPM/RPM considerations:** Sequential processing keeps rate-limit usage low. Retry is enabled for invalid JSON/enum outputs. Caching avoids repeated identical calls.
- **Batching/throttling/caching/retry:** Responses are cached per claim + image set + model + prompt version. Invalid outputs trigger one repair retry before safe fallback.
