## ADDED Requirements

### Requirement: Sample evaluation script exists
The system SHALL include an evaluation script at `code/evaluation/evaluate.py` that runs the system on `dataset/sample_claims.csv` and compares predictions against expected outputs.

#### Scenario: Run evaluation on sample claims
- **WHEN** the user runs `python evaluation/evaluate.py`
- **THEN** the system SHALL process all 20 sample claims and compare predicted fields against the labeled expected outputs

### Requirement: Per-field accuracy metrics
The evaluation SHALL report exact row match rate and per-field accuracy for: `claim_status`, `issue_type`, `object_part`, `evidence_standard_met`, `severity`, `risk_flags`, `supporting_image_ids`, `valid_image`.

#### Scenario: Report per-field accuracy
- **WHEN** evaluation completes on sample claims
- **THEN** the report SHALL include accuracy percentage for each of the 8 evaluated fields

### Requirement: Failure categorization
The evaluation SHALL categorize failures by type: claim extraction error, visual review error, evidence standard error, risk flag error, severity error, and formatting error.

#### Scenario: Categorize a claim_status mismatch
- **WHEN** the predicted `claim_status` differs from the expected value
- **THEN** the failure SHALL be categorized as a visual review error

#### Scenario: Categorize a formatting error
- **WHEN** an output field contains an invalid enum value
- **THEN** the failure SHALL be categorized as a formatting error

### Requirement: Evaluation report with operational analysis
The system SHALL generate `evaluation/evaluation_report.md` containing both accuracy metrics and operational analysis.

#### Scenario: Report includes operational metrics
- **WHEN** the evaluation report is generated
- **THEN** it SHALL include: approximate model calls for sample and test processing, approximate input/output token usage, number of images processed, approximate cost to process the full test set with pricing assumptions, approximate latency/runtime, and TPM/RPM considerations

#### Scenario: Report includes strategy comparison
- **WHEN** the evaluation report is generated
- **THEN** it SHALL compare at least two strategies, prompts, or model configurations and identify the final strategy used for `output.csv`

### Requirement: Evaluation report includes batching and caching strategy
The operational analysis SHALL document any batching, throttling, caching, or retry strategy used.

#### Scenario: Document caching strategy
- **WHEN** the system uses result caching during development
- **THEN** the evaluation report SHALL describe the caching approach and its impact on API call counts

### Requirement: Evaluation uses sample_claims.csv only for development
The system SHALL use `dataset/sample_claims.csv` for evaluation and prompt improvement, and SHALL NOT use it to hardcode answers for `dataset/claims.csv`.

#### Scenario: No data leakage from sample to test
- **WHEN** the system processes `dataset/claims.csv`
- **THEN** no output values SHALL be derived from `dataset/sample_claims.csv` expected outputs
