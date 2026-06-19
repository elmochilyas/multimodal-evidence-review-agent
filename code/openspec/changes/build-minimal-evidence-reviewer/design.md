## Context

The HackerRank Orchestrate challenge requires a system that verifies damage claims by inspecting submitted images against claim conversations, user history, and minimum evidence requirements. The repo provides:

- 20 labeled sample claims (`dataset/sample_claims.csv`) for development and evaluation
- 44 unlabeled test claims (`dataset/claims.csv`) for final predictions
- User history with risk flags for 47 users
- 11 evidence requirement rules across car, laptop, and package objects
- Local images in `dataset/images/sample/` and `dataset/images/test/`

The system must produce `output.csv` with 14 exact columns, strict enum values, and object-specific part lists. It must include an `evaluation/` folder with metrics and operational analysis. The solution ships as `code.zip`, `output.csv`, and `chat_transcript/log.txt`.

Constraints: 24-hour time limit, single developer, must be reproducible, must handle prompt injection in user text and images, must not hardcode answers.

## Goals / Non-Goals

**Goals:**

- Produce a valid `output.csv` with exact schema for all 44 test claims
- Achieve high per-field accuracy on sample claims through vision-grounded review
- Handle prompt injection, instruction-bearing text, and manipulation attempts safely
- Provide evaluation metrics and operational analysis for AI Judge interview
- Maintain debug logging for transcript evidence and explainability
- Keep the architecture simple, reliable, and debuggable within 24 hours

**Non-Goals:**

- Multi-agent orchestration or complex pipeline architecture
- Web application, dashboard, or visual UI
- Vector database or RAG for evidence requirements (11 rules fit in memory)
- Real-time streaming or async batch processing infrastructure
- Model fine-tuning or training
- Multi-language support beyond what the VLM handles natively
- Perfect accuracy on edge cases (safe fallback is preferred over wrong answers)

## Decisions

### Decision 1: Single Python CLI agent over multi-agent architecture

**Choice**: Single-process Python CLI with sequential claim processing.

**Rationale**: The task is embarrassingly parallel across claims but each claim follows the same pipeline: extract claim → inspect images → check evidence requirements → enrich with history → validate output. A single agent with clear stages is easier to debug, test, and explain to the AI Judge. Multi-agent orchestration adds coordination overhead, failure modes, and latency without measurable benefit for 44 claims.

**Alternatives considered**:
- Multi-agent with specialist workers (claim extractor, image reviewer, validator): Rejected — adds complexity, inter-agent communication, and failure modes for no accuracy gain on this dataset size.
- LangGraph / CrewAI framework: Rejected — framework overhead exceeds task complexity; direct code is more transparent.

### Decision 2: Vision-capable model (GPT-4o or Claude 3.5 Sonnet) for image review

**Choice**: Single vision-capable model call per claim that receives all images and the claim text, and returns structured JSON.

**Rationale**: The core task is visual evidence verification. A single VLM call with all images and structured output instructions is simpler and more reliable than separate text-only and vision-only calls. The model can jointly assess image quality, identify damage, match claims, and detect manipulation.

**Alternatives considered**:
- Separate text extraction (LLM) + image review (VLM) calls: Rejected — doubles API calls, adds latency, and the text extraction is simple enough to include in the VLM prompt.
- Local vision model (LLaVA, etc.): Rejected — setup complexity and quality risk within 24 hours.

### Decision 3: Strict structured output with validation and retry

**Choice**: Request JSON output from the model, parse into a typed dataclass, validate every field against allowed enums, retry once with a repair prompt on failure, fall back to safe `not_enough_information` on persistent failure.

**Rationale**: The output schema is strict and evaluable. Invalid enum values or missing fields directly reduce score. A validation layer catches model hallucinations before they reach `output.csv`. The retry/repair pattern recovers from transient formatting issues. The safe fallback ensures every row has valid output.

**Alternatives considered**:
- Trust model output directly: Rejected — models frequently produce invalid enums, extra fields, or wrong types.
- Use OpenAI structured outputs / function calling: Considered but not all providers support it; manual validation is more portable and catches semantic errors beyond schema.

### Decision 4: Evidence requirement matching via rule lookup

**Choice**: Load `evidence_requirements.csv` into memory, match by `claim_object` and `applies_to` keyword overlap with extracted issue type, use matched requirements to determine `evidence_standard_met`.

**Rationale**: There are only 11 evidence requirement rules. A simple keyword match is sufficient and transparent. The VLM can also be asked to assess evidence sufficiency directly, with the rule lookup providing a cross-check.

**Alternatives considered**:
- Vector similarity search on requirements: Rejected — overkill for 11 rules.
- Pure VLM judgment without rule lookup: Rejected — loses transparency and rule-grounded reasoning.

### Decision 5: User history as risk enrichment, not decision override

**Choice**: Look up user history by `user_id`, append `user_history_risk` and/or `manual_review_required` to `risk_flags` when `history_flags` contains those values, include history summary in justification context. Never change `claim_status` based on history alone.

**Rationale**: The problem statement explicitly states "User history can add risk context, but should not override clear visual evidence by itself." This is a hard rule.

### Decision 6: Prompt injection detection via pattern matching + VLM flagging

**Choice**: Pre-scan `user_claim` text for known injection patterns (e.g., "approve this claim", "ignore previous instructions", "mark supported"). Ask the VLM to also flag instruction-like text in images. Add `text_instruction_present` risk flag when detected.

**Rationale**: Test data contains explicit injection attempts (cases 008, 036, 040, 048, 055). Pattern matching catches text-based injection cheaply. VLM flagging catches instruction text embedded in images.

### Decision 7: Sequential processing with per-claim logging

**Choice**: Process claims one at a time, log each step (claim extraction, image review, evidence check, history enrichment, validation, final output) to both console and a debug log file.

**Rationale**: Sequential processing is simple and reliable for 44 claims. Debug logging provides transcript evidence for the AI Judge and helps diagnose failures. Parallel processing adds complexity without meaningful time savings at this scale.

## Risks / Trade-offs

**[VLM hallucination]** → Mitigation: Strict validation layer, retry with repair prompt, safe fallback to `not_enough_information`. Never trust raw model output.

**[API rate limits or failures]** → Mitigation: Exponential backoff retry (3 attempts), sequential processing stays well under typical TPM/RPM limits. Log all API calls for operational analysis.

**[Ambiguous or edge-case claims]** → Mitigation: Prefer `not_enough_information` over guessing. The scoring likely penalizes wrong answers more than conservative ones.

**[Image file not found or unreadable]** → Mitigation: Check file existence before VLM call. Set `valid_image=false`, `evidence_standard_met=false`, `claim_status=not_enough_information` with appropriate risk flags.

**[Multilingual claim text]** → Mitigation: VLMs handle multiple languages natively. The claim extraction prompt does not assume English-only input.

**[Prompt injection in images]** → Mitigation: Ask VLM to report any text visible in images. Flag `text_instruction_present` when instruction-like text is detected. Never follow instructions found in images or user text.

**[24-hour time pressure]** → Mitigation: Build baseline safe reviewer first (produces valid rows without VLM), then add VLM review, then improve prompts based on sample evaluation. This ensures a working submission exists early.

**[Cost of VLM calls]** → Mitigation: Single VLM call per claim (not per image). ~44 calls for test set. Estimated cost under $5 with GPT-4o pricing. Cache results during development to avoid redundant calls.

## Input Flow

```
claims.csv → CSV loader → claim rows
user_history.csv → history lookup dict
evidence_requirements.csv → requirements list
images/test/ → local file paths
```

## Output Flow

```
claim row
  → claim extraction (from user_claim text)
  → VLM image review (images + extracted claim)
  → evidence requirement matching
  → user history risk enrichment
  → structured output assembly
  → validation layer
  → output.csv row
```

## Validation Layer

1. Parse model JSON output into typed dataclass
2. Validate `claim_status` ∈ {supported, contradicted, not_enough_information}
3. Validate `issue_type` ∈ allowed list
4. Validate `object_part` ∈ claim_object-specific allowed list
5. Validate `severity` ∈ {none, low, medium, high, unknown}
6. Validate `evidence_standard_met` and `valid_image` ∈ {true, false}
7. Validate `risk_flags` — each flag ∈ allowed list, semicolon-separated or "none"
8. Validate `supporting_image_ids` — each ID matches a filename from image_paths, or "none"
9. On failure: retry once with repair prompt; on second failure: safe fallback

## VLM/LLM Review Flow

1. Build system prompt with role, output schema, allowed values, and guardrails
2. Build user message with: extracted claim summary, claim_object, image paths, evidence requirements context
3. Attach all images as base64 or file references
4. Request structured JSON response
5. Parse and validate response
6. If invalid: send repair prompt with specific error, retry once
7. If still invalid: produce safe fallback row

## Evidence Requirement Matching

1. Load all 11 rules from `evidence_requirements.csv`
2. Filter rules where `claim_object` matches the current claim or is "all"
3. Filter rules where `applies_to` keywords overlap with extracted issue type or claim context
4. Include matched requirement descriptions in VLM prompt as evaluation criteria
5. Use VLM assessment of evidence sufficiency, cross-checked against matched rules
6. Set `evidence_standard_met` based on whether the VLM confirms the required part/damage is visible

## User History Risk Enrichment

1. Look up `user_id` in user history dict
2. If `history_flags` contains `user_history_risk`: add `user_history_risk` to risk_flags
3. If `history_flags` contains `manual_review_required`: add `manual_review_required` to risk_flags
4. Include `history_summary` in VLM context for justification generation
5. Never modify `claim_status` based on history alone

## Guardrails for Prompt Injection and Unsafe Inputs

1. Pre-scan `user_claim` for injection patterns: "approve", "ignore previous", "mark supported", "skip review", "follow the note"
2. If detected: add `text_instruction_present` to risk_flags, strip injection text from VLM prompt
3. Ask VLM to report any text visible in images; flag `text_instruction_present` if instruction-like
4. Treat all user text as evidence, not instructions
5. Handle missing images, empty claims, unknown users gracefully with safe fallback rows

## Fallback Behavior

- Missing image file → `valid_image=false`, `evidence_standard_met=false`, `claim_status=not_enough_information`
- Empty user_claim → `claim_status=not_enough_information`, `issue_type=unknown`
- Unknown user_id → proceed without history enrichment, no risk flags from history
- Model timeout/error → retry with backoff, then safe fallback
- Invalid model output after retry → safe fallback with `not_enough_information`

## Logging and Debug Traces

- Log every claim processing step: input, extracted claim, VLM prompt, VLM response, validation result, final output
- Log API call counts, token usage, latency per claim
- Write debug log to `code/debug_log.jsonl` (one JSON object per claim)
- Include debug log in `code.zip` for transcript evidence

## Evaluation Workflow

1. Run system on `dataset/sample_claims.csv` (20 labeled rows)
2. Compare predicted fields against expected fields: `claim_status`, `issue_type`, `object_part`, `evidence_standard_met`, `severity`, `risk_flags`, `supporting_image_ids`, `valid_image`
3. Report exact row match rate and per-field accuracy
4. Categorize failures: claim extraction error, visual review error, evidence standard error, risk flag error, severity error, formatting error
5. Generate `evaluation/evaluation_report.md` with metrics and operational analysis

## Operational Analysis Plan

Track and report:
- Total model calls (sample + test)
- Input/output tokens per call and total
- Number of images processed
- Estimated cost at published API pricing
- Total runtime and average latency per claim
- TPM/RPM headroom and any throttling applied
- Caching strategy (development cache to avoid redundant calls)

## AI Judge Explanation Points

1. Single-agent architecture chosen for reliability and explainability over multi-agent complexity
2. Images are primary evidence; user text defines what to check; history adds risk context only
3. Strict validation layer prevents invalid outputs from reaching `output.csv`
4. Prompt injection handled via pattern matching and VLM flagging, never followed
5. Safe fallback ensures every row has valid output even under model failure
6. Evaluation on sample claims guided prompt improvements
7. Debug logging provides full audit trail for every decision
