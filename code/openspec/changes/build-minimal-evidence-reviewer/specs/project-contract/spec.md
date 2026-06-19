## ADDED Requirements

### Requirement: Repo layout conforms expected structure
The system SHALL maintain the following directory structure: `code/main.py` as the primary entry point, `code/evaluation/` for evaluation scripts and reports, and `code/` as the root for all solution files.

#### Scenario: Entry point exists at code/main.py
- **WHEN** the evaluator inspects the submitted `code.zip`
- **THEN** a runnable `main.py` file SHALL exist at the top level of the `code/` directory

#### Scenario: Evaluation folder exists
- **WHEN** the evaluator inspects the submitted `code.zip`
- **THEN** an `evaluation/` directory SHALL exist containing `evaluate.py` and `evaluation_report.md`

### Requirement: CLI entry point accepts input and output arguments
The system SHALL accept `--input` and `--output` command-line arguments to specify the input CSV path and output CSV path.

#### Scenario: Run with explicit input and output paths
- **WHEN** the user runs `python main.py --input ../dataset/claims.csv --output ../output.csv`
- **THEN** the system SHALL read claims from the specified input path and write results to the specified output path

### Requirement: Secrets read from environment variables only
The system SHALL read all API keys and secrets from environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) and SHALL NOT hardcode any secrets in source files.

#### Scenario: API key provided via environment variable
- **WHEN** the system starts and `OPENAI_API_KEY` is set in the environment
- **THEN** the system SHALL use that key for API calls without requiring it in any config file

#### Scenario: API key missing from environment
- **WHEN** the system starts and no API key environment variable is set
- **THEN** the system SHALL exit with a clear error message indicating the missing variable

### Requirement: Dependencies are minimal and documented
The system SHALL keep Python dependencies minimal and document them in a `requirements.txt` file inside `code/`.

#### Scenario: Requirements file lists all dependencies
- **WHEN** the evaluator inspects `code/requirements.txt`
- **THEN** all third-party packages used by the solution SHALL be listed with version pins

### Requirement: code.zip excludes prohibited content
The submitted `code.zip` SHALL NOT include virtualenvs, `node_modules`, build artifacts, the `dataset/` folder, or the image corpus.

#### Scenario: code.zip does not contain dataset or virtualenv
- **WHEN** the evaluator extracts `code.zip`
- **THEN** the extracted contents SHALL NOT contain `dataset/`, `.venv/`, `venv/`, `node_modules/`, or `__pycache__/` directories
