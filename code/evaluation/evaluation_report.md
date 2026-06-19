# Evidence Review Evaluation Report

**Sample file:** `../dataset/sample_claims.csv`
**Mode:** `live`
**Sample row count:** 3
**Run timestamp:** 2026-06-19 09:37:00 Morocco Daylight Time

## Summary Metrics

- **Exact row accuracy:** 100.00%

## Per-Field Accuracy

| Field | Accuracy |
|---|---|
| evidence_standard_met | 100.00% |
| risk_flags | 100.00% |
| issue_type | 100.00% |
| object_part | 100.00% |
| claim_status | 100.00% |
| valid_image | 100.00% |
| severity | 100.00% |
| supporting_image_ids | 100.00% |

## Failure Summary

| Field | Mismatched Rows |
|---|---|
| evidence_standard_met | 0 () |
| risk_flags | 0 () |
| issue_type | 0 () |
| object_part | 0 () |
| claim_status | 0 () |
| valid_image | 0 () |
| severity | 0 () |
| supporting_image_ids | 0 () |

## Failure Categories

| Category | Row Count |
|---|---|
| claim_extraction | 0 |
| visual_review | 0 |
| evidence_standard | 0 |
| risk_flags | 0 |
| severity | 0 |
| formatting | 0 |

## Validation

All predicted rows passed schema and enum validation.

## Operational Analysis

- **Mode:** live
- **Model calls for sample processing:** 3
- **Model calls for test processing:** TBD after full test run
- **Images processed:** TBD
- **Approximate cost:** TBD after model pricing is applied
- **Latency/runtime:** 14.0627s for 3 sample rows
- **TPM/RPM considerations:** Sequential processing keeps rate-limit usage low. Retry is enabled for invalid JSON/enum outputs. Caching avoids repeated identical calls.
- **Batching/throttling/caching/retry:** Responses are cached per claim + image set + model + prompt version. Invalid outputs trigger one repair retry before safe fallback.
