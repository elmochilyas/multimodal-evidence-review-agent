# Evidence Review Evaluation Report

**Sample file:** `../dataset/sample_claims.csv`
**Mode:** `live`
**Sample row count:** 20
**Run timestamp:** 2026-06-19 16:14:37 Morocco Daylight Time

## Summary Metrics

- **Exact row accuracy:** 0.00%

## Per-Field Accuracy

| Field | Accuracy |
|---|---|
| evidence_standard_met | 15.00% |
| risk_flags | 0.00% |
| issue_type | 15.00% |
| object_part | 5.00% |
| claim_status | 15.00% |
| valid_image | 10.00% |
| severity | 15.00% |
| supporting_image_ids | 10.00% |

## Failure Summary

| Field | Mismatched Rows |
|---|---|
| evidence_standard_met | 17 (1, 3, 4, 5, 7, 8, 9, 10, 11, 12, ... (7 more)) |
| risk_flags | 20 (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ... (10 more)) |
| issue_type | 17 (1, 2, 3, 4, 5, 7, 8, 9, 10, 11, ... (7 more)) |
| object_part | 19 (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ... (9 more)) |
| claim_status | 17 (1, 3, 4, 5, 7, 8, 9, 10, 11, 12, ... (7 more)) |
| valid_image | 18 (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, ... (8 more)) |
| severity | 17 (1, 3, 4, 5, 7, 8, 9, 10, 11, 12, ... (7 more)) |
| supporting_image_ids | 18 (1, 2, 3, 4, 5, 7, 8, 9, 10, 11, ... (8 more)) |

## Failure Categories

| Category | Row Count |
|---|---|
| claim_extraction | 19 |
| visual_review | 17 |
| evidence_standard | 17 |
| risk_flags | 20 |
| severity | 17 |
| formatting | 19 |

## Validation

All predicted rows passed schema and enum validation.

## Operational Analysis

- **Mode:** live
- **Model calls for sample processing:** 20
- **Model calls for test processing:** TBD after full test run
- **Images processed:** TBD
- **Approximate cost:** TBD after model pricing is applied
- **Latency/runtime:** 44.6198s for 20 sample rows
- **TPM/RPM considerations:** Sequential processing keeps rate-limit usage low. Retry is enabled for invalid JSON/enum outputs. Caching avoids repeated identical calls.
- **Batching/throttling/caching/retry:** Responses are cached per claim + image set + model + prompt version. Invalid outputs trigger one repair retry before safe fallback.
