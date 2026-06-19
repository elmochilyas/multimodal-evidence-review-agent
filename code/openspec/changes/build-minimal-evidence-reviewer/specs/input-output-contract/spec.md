## ADDED Requirements

### Requirement: Input claims.csv columns are read correctly
The system SHALL read `claims.csv` with exactly these input columns: `user_id`, `image_paths`, `user_claim`, `claim_object`.

#### Scenario: Load claims.csv with four columns
- **WHEN** the system reads `dataset/claims.csv`
- **THEN** each row SHALL be parsed with `user_id`, `image_paths`, `user_claim`, and `claim_object` fields

### Requirement: Multiple image paths are split by semicolon
The system SHALL split `image_paths` on semicolons to extract individual image file paths.

#### Scenario: Row with two image paths
- **WHEN** `image_paths` is `images/test/case_001/img_1.jpg;images/test/case_001/img_2.jpg`
- **THEN** the system SHALL extract two paths: `images/test/case_001/img_1.jpg` and `images/test/case_001/img_2.jpg`

### Requirement: Image ID is filename without extension
The system SHALL derive image IDs from image file paths by extracting the filename and removing the extension.

#### Scenario: Extract image ID from path
- **WHEN** the image path is `images/test/case_001/img_1.jpg`
- **THEN** the image ID SHALL be `img_1`

### Requirement: claim_object is one of car, laptop, package
The system SHALL validate that `claim_object` is one of `car`, `laptop`, or `package`.

#### Scenario: Valid claim_object values
- **WHEN** `claim_object` is `car`, `laptop`, or `package`
- **THEN** the system SHALL process the row normally

#### Scenario: Invalid claim_object value
- **WHEN** `claim_object` is not one of the allowed values
- **THEN** the system SHALL produce a safe fallback row with `claim_status=not_enough_information`

### Requirement: output.csv has exact columns in exact order
The system SHALL produce `output.csv` with exactly these 14 columns in this order: `user_id`, `image_paths`, `user_claim`, `claim_object`, `evidence_standard_met`, `evidence_standard_met_reason`, `risk_flags`, `issue_type`, `object_part`, `claim_status`, `claim_status_justification`, `supporting_image_ids`, `valid_image`, `severity`.

#### Scenario: Output CSV column order
- **WHEN** the system writes `output.csv`
- **THEN** the header row SHALL contain exactly the 14 required columns in the specified order with no extra columns

### Requirement: output.csv has one row per input row
The system SHALL produce exactly one output row for each input row in `claims.csv`.

#### Scenario: Row count matches
- **WHEN** `claims.csv` contains 44 data rows
- **THEN** `output.csv` SHALL contain exactly 44 data rows (excluding the header)

### Requirement: evidence_standard_met is true or false
The system SHALL set `evidence_standard_met` to the string `"true"` or `"false"` only.

#### Scenario: Evidence standard met value
- **WHEN** the image set is sufficient to evaluate the claim
- **THEN** `evidence_standard_met` SHALL be `"true"`

#### Scenario: Evidence standard not met value
- **WHEN** the image set is insufficient to evaluate the claim
- **THEN** `evidence_standard_met` SHALL be `"false"`

### Requirement: valid_image is true or false
The system SHALL set `valid_image` to the string `"true"` or `"false"` only.

#### Scenario: Valid image set
- **WHEN** the image set is usable for automated review
- **THEN** `valid_image` SHALL be `"true"`

#### Scenario: Invalid image set
- **WHEN** the image set is not usable for automated review
- **THEN** `valid_image` SHALL be `"false"`

### Requirement: claim_status uses allowed enum values
The system SHALL set `claim_status` to exactly one of: `supported`, `contradicted`, `not_enough_information`.

#### Scenario: Claim supported by evidence
- **WHEN** the image evidence clearly supports the user's damage claim
- **THEN** `claim_status` SHALL be `supported`

#### Scenario: Claim contradicted by evidence
- **WHEN** the image evidence clearly contradicts the user's damage claim
- **THEN** `claim_status` SHALL be `contradicted`

#### Scenario: Not enough information
- **WHEN** the image evidence is insufficient to evaluate the claim
- **THEN** `claim_status` SHALL be `not_enough_information`

### Requirement: issue_type uses allowed enum values
The system SHALL set `issue_type` to exactly one of: `dent`, `scratch`, `crack`, `glass_shatter`, `broken_part`, `missing_part`, `torn_packaging`, `crushed_packaging`, `water_damage`, `stain`, `none`, `unknown`.

#### Scenario: No issue visible
- **WHEN** the relevant part is visible and no issue is present
- **THEN** `issue_type` SHALL be `none`

#### Scenario: Issue cannot be determined
- **WHEN** the issue type cannot be determined from the images
- **THEN** `issue_type` SHALL be `unknown`

### Requirement: object_part uses claim_object-specific allowed values
The system SHALL set `object_part` to a value from the allowed list for the specific `claim_object`.

#### Scenario: Car object_part values
- **WHEN** `claim_object` is `car`
- **THEN** `object_part` SHALL be one of: `front_bumper`, `rear_bumper`, `door`, `hood`, `windshield`, `side_mirror`, `headlight`, `taillight`, `fender`, `quarter_panel`, `body`, `unknown`

#### Scenario: Laptop object_part values
- **WHEN** `claim_object` is `laptop`
- **THEN** `object_part` SHALL be one of: `screen`, `keyboard`, `trackpad`, `hinge`, `lid`, `corner`, `port`, `base`, `body`, `unknown`

#### Scenario: Package object_part values
- **WHEN** `claim_object` is `package`
- **THEN** `object_part` SHALL be one of: `box`, `package_corner`, `package_side`, `seal`, `label`, `contents`, `item`, `unknown`

### Requirement: severity uses allowed enum values
The system SHALL set `severity` to exactly one of: `none`, `low`, `medium`, `high`, `unknown`.

#### Scenario: Severity assessment
- **WHEN** the system evaluates damage severity
- **THEN** `severity` SHALL be one of the five allowed values

### Requirement: risk_flags uses allowed enum values with semicolon separation
The system SHALL set `risk_flags` to semicolon-separated values from the allowed list, or `none` if no flags apply.

#### Scenario: No risk flags
- **WHEN** no risk conditions are detected
- **THEN** `risk_flags` SHALL be `none`

#### Scenario: Multiple risk flags
- **WHEN** both blurry image and user history risk are detected
- **THEN** `risk_flags` SHALL be `blurry_image;user_history_risk`

#### Scenario: Allowed risk flag values
- **WHEN** risk flags are set
- **THEN** each flag SHALL be one of: `none`, `blurry_image`, `cropped_or_obstructed`, `low_light_or_glare`, `wrong_angle`, `wrong_object`, `wrong_object_part`, `damage_not_visible`, `claim_mismatch`, `possible_manipulation`, `non_original_image`, `text_instruction_present`, `user_history_risk`, `manual_review_required`

### Requirement: supporting_image_ids references valid image IDs or none
The system SHALL set `supporting_image_ids` to semicolon-separated image IDs that exist in the row's `image_paths`, or `none` if no image supports the decision.

#### Scenario: Single supporting image
- **WHEN** `img_1` supports the decision and the row has images `img_1` and `img_2`
- **THEN** `supporting_image_ids` SHALL be `img_1`

#### Scenario: No supporting images
- **WHEN** no image is sufficient to support the decision
- **THEN** `supporting_image_ids` SHALL be `none`

### Requirement: Local image paths are resolved relative to working directory
The system SHALL resolve image paths from `image_paths` relative to the current working directory or a configurable base path.

#### Scenario: Resolve relative image path
- **WHEN** `image_paths` contains `images/test/case_001/img_1.jpg`
- **THEN** the system SHALL resolve this path relative to the repo root or working directory to locate the actual image file

### Requirement: User history CSV is loaded correctly
The system SHALL load `user_history.csv` and index it by `user_id` for lookup.

#### Scenario: Look up user history
- **WHEN** a claim has `user_id=user_005`
- **THEN** the system SHALL retrieve the corresponding row from `user_history.csv` with all history fields

### Requirement: Evidence requirements CSV is loaded correctly
The system SHALL load `evidence_requirements.csv` and use it for evidence standard matching.

#### Scenario: Load evidence requirements
- **WHEN** the system starts
- **THEN** all 11 evidence requirement rules SHALL be loaded and available for matching
