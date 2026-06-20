# Development Notes

## Why a Single-Agent Architecture?

This project was built for a 24-hour hackathon (HackerRank Orchestrate June 2026). The primary requirement was reliability, not architectural novelty. A single-agent VLM architecture was chosen because:

1. **Time constraint**: Building and debugging a multi-agent system in 24 hours introduces significant risk.
2. **Deterministic guardrails matter more**: The hardest part was getting valid structured output with correct enum values — not agent orchestration.
3. **Traceability**: A single review call produces a complete decision trace. No complex inter-agent communication to debug.

## Tradeoffs

| Decision | Tradeoff |
|---|---|
| Single VLM agent | Less specialization per task, but simpler to validate and debug |
| Deterministic post-processing | Catches known patterns but misses edge cases |
| JPEG data URLs | Increases token usage but ensures consistent format |
| Mock provider default | Safer for accidental runs but requires explicit configuration for live mode |
| Prompt-based evidence review | Flexible but depends on model quality |

## What Could Be Improved

1. **Multi-model ensemble**: Run multiple VLMs and aggregate decisions for contentious claims.
2. **Image quality pre-filter**: Add a deterministic pre-processing step that rejects blurry, obstructed, or manipulated images before model review.
3. **Few-shot examples**: Include in-context examples in the prompt for edge cases.
4. **Confidence scoring**: Add a confidence score per decision to flag borderline cases.
5. **Streaming large images**: Downscale or chunk very large images to reduce token costs.
6. **Parallel batching**: Process claims concurrently for faster throughput.

## Testing Philosophy

- Unit tests cover each module independently with mock providers.
- Integration tests run the full pipeline on sample data in mock mode.
- Validation tests ensure output.csv meets the exact schema contract.
- No test depends on a live API key.

## Submission Context

The original `code/` directory was zipped as `code.zip` for submission to HackerRank. The `dataset/` and `output.csv` remain outside the zip as required by the contest rules.
