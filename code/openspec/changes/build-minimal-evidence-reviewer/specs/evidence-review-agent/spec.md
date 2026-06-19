## ADDED Requirements

### Requirement: Claim extraction from conversation text
The system SHALL extract the specific damage claim from the `user_claim` conversation text, identifying the claimed issue type, affected object part, and damage description.

#### Scenario: Extract claim from English conversation
- **WHEN** the conversation describes "a dent on the rear bumper"
- **THEN** the system SHALL extract issue_type=dent and object_part=rear_bumper as the claimed damage

#### Scenario: Extract claim from multilingual conversation
- **WHEN** the conversation contains Hindi, Spanish, Chinese, or mixed-language text describing damage
- **THEN** the system SHALL correctly extract the claimed issue type and object part regardless of language

#### Scenario: Extract claim from verbose or confusing conversation
- **WHEN** the conversation is long, hedging, or changes direction before settling on a specific claim
- **THEN** the system SHALL extract the final stated claim, not intermediate exploratory statements

### Requirement: Vision-capable model reviews submitted images
The system SHALL send all submitted images to a vision-capable model for visual inspection and evidence assessment.

#### Scenario: Single image review
- **WHEN** a claim has one image
- **THEN** the system SHALL send that image to the VLM and request structured assessment of visible damage

#### Scenario: Multiple image review
- **WHEN** a claim has multiple images
- **THEN** the system SHALL send all images to the VLM in a single call and request per-image assessment

### Requirement: Image-grounded decision making
The system SHALL base `claim_status` decisions on visual evidence from the submitted images, not on user text assertions alone.

#### Scenario: Image supports the claim
- **WHEN** the image clearly shows the claimed damage on the claimed part
- **THEN** `claim_status` SHALL be `supported`

#### Scenario: Image contradicts the claim
- **WHEN** the image shows a different type of damage, a different part, or no damage where damage is claimed
- **THEN** `claim_status` SHALL be `contradicted`

#### Scenario: Image is insufficient
- **WHEN** the image does not show the claimed part, is too blurry, wrong angle, or shows the wrong object
- **THEN** `claim_status` SHALL be `not_enough_information`

### Requirement: Evidence requirement lookup determines evidence_standard_met
The system SHALL match the current claim against `evidence_requirements.csv` rules to assess whether the image set meets the minimum evidence standard.

#### Scenario: Evidence meets the standard
- **WHEN** the claimed object and part are visible clearly enough to inspect the claimed condition per the matched requirement
- **THEN** `evidence_standard_met` SHALL be `true`

#### Scenario: Evidence does not meet the standard
- **WHEN** the claimed object or part is not visible, or the image quality is insufficient to assess the claimed condition per the matched requirement
- **THEN** `evidence_standard_met` SHALL be `false`

### Requirement: User history adds risk context without overriding visual evidence
The system SHALL look up user history by `user_id` and add risk flags, but SHALL NOT change `claim_status` based on history alone.

#### Scenario: User with history risk and clear image evidence
- **WHEN** the user has `user_history_risk` in their history but the image clearly supports the claim
- **THEN** `claim_status` SHALL be `supported` and `risk_flags` SHALL include `user_history_risk`

#### Scenario: User with history risk and insufficient image evidence
- **WHEN** the user has `user_history_risk` and the image is insufficient
- **THEN** `claim_status` SHALL be `not_enough_information` and `risk_flags` SHALL include `user_history_risk`

#### Scenario: User not found in history
- **WHEN** the `user_id` does not exist in `user_history.csv`
- **THEN** the system SHALL proceed without history enrichment and produce no history-based risk flags

### Requirement: Risk flags are set based on image quality and context
The system SHALL detect and flag image quality issues, mismatches, and authenticity concerns.

#### Scenario: Blurry image detected
- **WHEN** a submitted image is too blurry to assess damage
- **THEN** `risk_flags` SHALL include `blurry_image`

#### Scenario: Wrong object in image
- **WHEN** the image shows a different object than the claimed one
- **THEN** `risk_flags` SHALL include `wrong_object`

#### Scenario: Claim mismatch between text and image
- **WHEN** the image shows different damage than what the user claimed
- **THEN** `risk_flags` SHALL include `claim_mismatch`

#### Scenario: Non-original image suspected
- **WHEN** the image appears to be a screenshot, edited, or not an original photo
- **THEN** `risk_flags` SHALL include `non_original_image`

### Requirement: Justifications are image-grounded and concise
The system SHALL produce short justifications that reference visible evidence and mention relevant image IDs when helpful.

#### Scenario: Supported claim justification
- **WHEN** `claim_status` is `supported`
- **THEN** `claim_status_justification` SHALL describe what is visible in the image that supports the claim

#### Scenario: Contradicted claim justification
- **WHEN** `claim_status` is `contradicted`
- **THEN** `claim_status_justification` SHALL describe what the image actually shows versus what was claimed

### Requirement: No hardcoded answers for specific claims
The system SHALL NOT contain hardcoded output values for specific claim IDs, user IDs, or image file names.

#### Scenario: System produces dynamic output
- **WHEN** the system processes any claim row
- **THEN** the output SHALL be generated dynamically from the input data and model review, not from a lookup table of pre-computed answers

### Requirement: Model abstraction allows provider switching
The system SHALL abstract the VLM/LLM call behind an interface that allows switching between providers (OpenAI, Anthropic) without changing the review pipeline.

#### Scenario: Switch from OpenAI to Anthropic
- **WHEN** the environment variable `MODEL_PROVIDER` is set to `anthropic`
- **THEN** the system SHALL use the Anthropic API instead of OpenAI without changing any other code
