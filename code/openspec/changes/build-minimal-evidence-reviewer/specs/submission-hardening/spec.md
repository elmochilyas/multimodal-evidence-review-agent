## ADDED Requirements

### Requirement: Final dry run produces valid output.csv
The system SHALL pass a final dry run where `python main.py --input ../dataset/claims.csv --output ../output.csv` completes successfully and produces a valid `output.csv`.

#### Scenario: Dry run completes without errors
- **WHEN** the main command is run from a clean checkout
- **THEN** it SHALL exit with code 0 and produce `output.csv` at the specified path

#### Scenario: Dry run output passes all validation
- **WHEN** the dry run `output.csv` is validated
- **THEN** it SHALL have exact columns in exact order, one row per input row, all enum fields valid, object parts matching claim_object-specific lists, and supporting_image_ids referencing valid IDs or "none"

### Requirement: README documents setup and usage
The system SHALL include a README inside `code/` that explains setup, environment variables, run commands, evaluation, and final output.

#### Scenario: README explains environment variables
- **WHEN** a user reads the README
- **THEN** it SHALL list all required environment variables (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`) with descriptions

#### Scenario: README explains run commands
- **WHEN** a user reads the README
- **THEN** it SHALL include the exact commands to run the system and the evaluation

### Requirement: Transcript logging captures development reasoning
The system SHALL produce debug logging that captures development reasoning, architecture decisions, and evaluation results for the chat transcript submission.

#### Scenario: Debug log captures claim processing steps
- **WHEN** the system processes a claim
- **THEN** the debug log SHALL record: input data, extracted claim, VLM prompt, VLM response, validation result, and final output for that claim

#### Scenario: Debug log does not contain secrets
- **WHEN** the debug log is written
- **THEN** it SHALL NOT contain API keys, tokens, or other secrets

### Requirement: code.zip packaging is clean
The submitted `code.zip` SHALL include all necessary files and exclude prohibited content.

#### Scenario: code.zip includes required files
- **WHEN** `code.zip` is created
- **THEN** it SHALL contain: `main.py`, `evaluation/`, `requirements.txt`, `README.md`, and all source modules

#### Scenario: code.zip excludes prohibited content
- **WHEN** `code.zip` is created
- **THEN** it SHALL NOT contain: virtualenvs, `node_modules/`, `__pycache__/`, `dataset/`, image files, `.env` files, or build artifacts

### Requirement: No secrets committed to repository
The system SHALL NOT have any API keys, tokens, or secrets committed to any file in the repository.

#### Scenario: No secrets in source files
- **WHEN** the repository is inspected for secrets
- **THEN** no file SHALL contain hardcoded API keys, tokens, or credentials

#### Scenario: .env file not committed
- **WHEN** a `.env` file exists locally for development
- **THEN** it SHALL be listed in `.gitignore` and SHALL NOT be included in `code.zip`

### Requirement: No absolute local paths in output
The system SHALL NOT include absolute local filesystem paths in `output.csv` or any committed configuration files.

#### Scenario: Output contains no absolute paths
- **WHEN** `output.csv` is generated
- **THEN** no field SHALL contain absolute paths like `C:\Users\...` or `/home/user/...`
