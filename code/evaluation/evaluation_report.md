# Evidence Review Evaluation Report

**Sample file:** `../dataset/sample_claims.csv`
**Mode:** `live`
**Sample row count:** 20
**Run timestamp:** 2026-06-19 09:41:53 Morocco Daylight Time

## Summary Metrics

- **Exact row accuracy:** 25.00%

## Per-Field Accuracy

| Field | Accuracy |
|---|---|
| evidence_standard_met | 95.00% |
| risk_flags | 55.00% |
| issue_type | 70.00% |
| object_part | 75.00% |
| claim_status | 75.00% |
| valid_image | 90.00% |
| severity | 45.00% |
| supporting_image_ids | 85.00% |

## Failure Summary

| Field | Mismatched Rows |
|---|---|
| evidence_standard_met | 1 (18) |
| risk_flags | 9 (5, 6, 7, 8, 14, 17, 18, 19, 20) |
| issue_type | 6 (4, 5, 14, 18, 19, 20) |
| object_part | 5 (5, 8, 16, 18, 19) |
| claim_status | 5 (8, 14, 18, 19, 20) |
| valid_image | 2 (8, 18) |
| severity | 11 (5, 8, 10, 11, 12, 14, 15, 16, 18, 19, ... (1 more)) |
| supporting_image_ids | 3 (18, 19, 20) |

## Failure Categories

| Category | Row Count |
|---|---|
| claim_extraction | 8 |
| visual_review | 5 |
| evidence_standard | 1 |
| risk_flags | 9 |
| severity | 11 |
| formatting | 4 |

## Validation

All predicted rows passed schema and enum validation.

## Operational Analysis

- **Mode:** live
- **Model calls for sample processing:** 20
- **Model calls for test processing:** TBD after full test run
- **Images processed:** TBD
- **Approximate cost:** TBD after model pricing is applied
- **Latency/runtime:** 70.5123s for 20 sample rows
- **TPM/RPM considerations:** Sequential processing keeps rate-limit usage low. Retry is enabled for invalid JSON/enum outputs. Caching avoids repeated identical calls.
- **Batching/throttling/caching/retry:** Responses are cached per claim + image set + model + prompt version. Invalid outputs trigger one repair retry before safe fallback.
