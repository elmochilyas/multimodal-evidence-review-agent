# Evidence Review Evaluation Report

**Sample file:** `../dataset/sample_claims.csv`
**Mode:** `live`
**Sample row count:** 20
**Run timestamp:** 2026-06-19 10:46:24 Morocco Daylight Time

## Summary Metrics

- **Exact row accuracy:** 30.00%

## Per-Field Accuracy

| Field | Accuracy |
|---|---|
| evidence_standard_met | 95.00% |
| risk_flags | 65.00% |
| issue_type | 55.00% |
| object_part | 80.00% |
| claim_status | 85.00% |
| valid_image | 95.00% |
| severity | 50.00% |
| supporting_image_ids | 90.00% |

## Failure Summary

| Field | Mismatched Rows |
|---|---|
| evidence_standard_met | 1 (8) |
| risk_flags | 7 (5, 6, 7, 8, 14, 19, 20) |
| issue_type | 9 (4, 5, 6, 8, 11, 13, 14, 19, 20) |
| object_part | 4 (5, 8, 16, 19) |
| claim_status | 3 (14, 19, 20) |
| valid_image | 1 (8) |
| severity | 10 (5, 8, 10, 12, 13, 14, 15, 16, 19, 20) |
| supporting_image_ids | 2 (8, 20) |

## Failure Categories

| Category | Row Count |
|---|---|
| claim_extraction | 10 |
| visual_review | 3 |
| evidence_standard | 1 |
| risk_flags | 7 |
| severity | 10 |
| formatting | 2 |

## Validation

All predicted rows passed schema and enum validation.

## Operational Analysis

- **Mode:** live
- **Model calls for sample processing:** 20
- **Model calls for test processing:** TBD after full test run
- **Images processed:** TBD
- **Approximate cost:** TBD after model pricing is applied
- **Latency/runtime:** 85.3443s for 20 sample rows
- **TPM/RPM considerations:** Sequential processing keeps rate-limit usage low. Retry is enabled for invalid JSON/enum outputs. Caching avoids repeated identical calls.
- **Batching/throttling/caching/retry:** Responses are cached per claim + image set + model + prompt version. Invalid outputs trigger one repair retry before safe fallback.
