## ADDED Requirements

### Requirement: Strict output validation for all enum fields
The system SHALL validate every output row against the allowed enum values before writing to `output.csv`.

#### Scenario: Invalid claim_status detected
- **WHEN** the model returns a `claim_status` value not in {supported, contradicted, not_enough_information}
- **THEN** the validation layer SHALL reject the output and trigger a retry or fallback

#### Scenario: Invalid issue_type detected
- **WHEN** the model returns an `issue_type` value not in the allowed list
- **THEN** the validation layer SHALL reject the output and trigger a retry or fallback

#### Scenario: Invalid object_part for claim_object
- **WHEN** the model returns an `object_part` not in the allowed list for the given `claim_object`
- **THEN** the validation layer SHALL reject the output and trigger a retry or fallback

#### Scenario: Invalid severity detected
- **WHEN** the model returns a `severity` value not in {none, low, medium, high, unknown}
- **THEN** the validation layer SHALL reject the output and trigger a retry or fallback

### Requirement: Retry with repair prompt on invalid output
The system SHALL retry the model call once with a repair prompt when validation fails, specifying the exact fields that are invalid.

#### Scenario: Successful retry after invalid output
- **WHEN** the first model response has an invalid `issue_type` and the repair prompt specifies the error
- **THEN** the system SHALL retry and accept the corrected response if valid

#### Scenario: Failed retry falls back to safe default
- **WHEN** the retry also produces invalid output
- **THEN** the system SHALL produce a safe fallback row with `claim_status=not_enough_information`, `issue_type=unknown`, `object_part=unknown`, `severity=unknown`

### Requirement: Safe fallback for model failures
The system SHALL produce a valid output row even when the model call fails entirely (timeout, error, rate limit).

#### Scenario: Model API timeout
- **WHEN** the model API does not respond within the timeout period
- **THEN** the system SHALL produce a safe fallback row with valid schema and `claim_status=not_enough_information`

#### Scenario: Model API returns error
- **WHEN** the model API returns an HTTP error (429, 500, etc.)
- **THEN** the system SHALL retry with exponential backoff up to 3 times, then produce a safe fallback row

### Requirement: Prompt injection detection in user text
The system SHALL scan `user_claim` text for known injection patterns and flag them.

#### Scenario: Detect approval instruction in text
- **WHEN** `user_claim` contains phrases like "approve this claim", "mark supported", "ignore previous instructions", "skip manual review"
- **THEN** the system SHALL add `text_instruction_present` to `risk_flags` and SHALL NOT follow the instruction

#### Scenario: Detect manipulation instruction in text
- **WHEN** `user_claim` contains phrases like "follow the note", "accept this quickly or I will", "escalate publicly"
- **THEN** the system SHALL add `text_instruction_present` to `risk_flags` and SHALL NOT follow the instruction

### Requirement: text_instruction_present handling for instruction-bearing images
The system SHALL detect instruction-like text visible in submitted images and flag it.

#### Scenario: Image contains approval instruction text
- **WHEN** a submitted image contains visible text instructing the reviewer to approve or accept the claim
- **THEN** the system SHALL add `text_instruction_present` to `risk_flags` and SHALL NOT follow the instruction in the image

### Requirement: Authenticity flagging for suspicious images
The system SHALL flag images that appear edited, synthetic, screenshot-like, or reused.

#### Scenario: Screenshot-like image detected
- **WHEN** a submitted image appears to be a screenshot rather than an original photo
- **THEN** `risk_flags` SHALL include `non_original_image`

#### Scenario: Possibly manipulated image
- **WHEN** a submitted image shows signs of editing or manipulation
- **THEN** `risk_flags` SHALL include `possible_manipulation`

### Requirement: Safe handling of malformed inputs
The system SHALL produce valid output rows even for malformed or incomplete inputs.

#### Scenario: Missing image file
- **WHEN** an image path in `image_paths` does not exist on disk
- **THEN** the system SHALL set `valid_image=false`, `evidence_standard_met=false`, `claim_status=not_enough_information`, and produce a valid output row

#### Scenario: Empty user_claim
- **WHEN** `user_claim` is empty or contains only whitespace
- **THEN** the system SHALL produce a valid output row with `claim_status=not_enough_information` and `issue_type=unknown`

#### Scenario: Unknown user_id not in history
- **WHEN** `user_id` does not exist in `user_history.csv`
- **THEN** the system SHALL proceed without history enrichment and produce a valid output row

### Requirement: supporting_image_ids validation
The system SHALL validate that every image ID in `supporting_image_ids` corresponds to an actual image in the row's `image_paths`.

#### Scenario: Invalid supporting image ID
- **WHEN** `supporting_image_ids` contains an ID that does not match any image in `image_paths`
- **THEN** the validation layer SHALL correct it to `none` or remove the invalid ID

### Requirement: No hardcoded labels or file-specific answers
The system SHALL NOT contain any hardcoded output values tied to specific claim IDs, user IDs, image filenames, or row numbers.

#### Scenario: System generalizes to unseen claims
- **WHEN** the system processes a claim it has never seen before
- **THEN** the output SHALL be generated dynamically from the input data and model review, not from a pre-computed lookup
