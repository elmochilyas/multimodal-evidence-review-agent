## 1. Inspect Repo and Dataset Contracts

- [x] 1.1 Verify repo layout matches expected structure (code/main.py, code/evaluation/, dataset/ files)
  - **Goal**: Confirm all expected files and directories exist before building
  - **Files**: None (read-only inspection)
  - **Verification**: `ls` or `dir` on code/, dataset/, dataset/images/sample/, dataset/images/test/
  - **Evidence**: List of confirmed files and any missing items
  - **Decision**: Proceed if all dataset files and image directories are present

- [x] 1.2 Validate dataset CSV schemas match expected columns
  - **Goal**: Confirm claims.csv, sample_claims.csv, user_history.csv, evidence_requirements.csv have expected columns
  - **Files**: None (read-only inspection)
  - **Verification**: Read first row of each CSV and compare against input/output contracts in config.yaml
  - **Evidence**: Column lists for each CSV, any mismatches noted
  - **Decision**: Proceed if all CSVs have expected columns

- [x] 1.3 Count test claims and sample claims, verify image availability
  - **Goal**: Establish baseline counts and confirm images exist on disk
  - **Files**: None (read-only inspection)
  - **Verification**: Count rows in claims.csv (expect 44) and sample_claims.csv (expect 20). Spot-check 5 image paths from each CSV
  - **Evidence**: Row counts, image existence check results
  - **Decision**: Proceed if counts match and sampled images exist

## 2. Create Python Project Structure

- [x] 2.1 Create module structure inside code/
  - **Goal**: Establish the file layout for the solution
  - **Files**: `code/main.py`, `code/reviewer.py`, `code/models.py`, `code/validation.py`, `code/io_utils.py`, `code/prompts.py`, `code/config.py`, `code/evaluation/evaluate.py`, `code/requirements.txt`
  - **Verification**: All files exist with minimal stubs
  - **Evidence**: File listing of code/ directory
  - **Decision**: Proceed if all files are created

- [x] 2.2 Create requirements.txt with minimal dependencies
  - **Goal**: Declare third-party packages
  - **Files**: `code/requirements.txt`
  - **Verification**: `pip install -r requirements.txt` succeeds
  - **Evidence**: requirements.txt content, pip install output
  - **Decision**: Proceed if install succeeds with no errors

## 3. Implement CLI Skeleton

- [x] 3.1 Implement argparse CLI with --input and --output arguments
  - **Goal**: Create the entry point that accepts input/output paths
  - **Files**: `code/main.py`
  - **Verification**: `python main.py --help` shows usage; `python main.py --input ../dataset/claims.csv --output ../output.csv` runs without crash (may produce empty output initially)
  - **Evidence**: --help output, exit code
  - **Decision**: Proceed if CLI parses arguments correctly

## 4. Implement CSV Input Loader

- [x] 4.1 Implement claims.csv loader
  - **Goal**: Read claims.csv into a list of dicts with correct column parsing
  - **Files**: `code/io_utils.py`
  - **Verification**: Load claims.csv and print row count (expect 44) and first row fields
  - **Evidence**: Row count, sample row data
  - **Decision**: Proceed if all rows load with correct fields

- [x] 4.2 Implement user_history.csv loader with user_id indexing
  - **Goal**: Load user history into a dict keyed by user_id
  - **Files**: `code/io_utils.py`
  - **Verification**: Load user_history.csv, look up user_005, verify history_flags contains user_history_risk
  - **Evidence**: Lookup result for user_005
  - **Decision**: Proceed if lookup returns correct data

- [x] 4.3 Implement evidence_requirements.csv loader
  - **Goal**: Load all 11 evidence requirement rules into memory
  - **Files**: `code/io_utils.py`
  - **Verification**: Load evidence_requirements.csv, confirm 11 rules loaded, print first rule
  - **Evidence**: Rule count, sample rule data
  - **Decision**: Proceed if all 11 rules load correctly

- [x] 4.4 Implement image path splitting and image ID extraction
  - **Goal**: Split semicolon-separated image paths and extract image IDs from filenames
  - **Files**: `code/io_utils.py`
  - **Verification**: Split `images/test/case_001/img_1.jpg;images/test/case_001/img_2.jpg` into two paths and extract IDs `img_1`, `img_2`
  - **Evidence**: Split result and extracted IDs
  - **Decision**: Proceed if splitting and ID extraction work correctly

## 5. Implement Required Output Writer

- [x] 5.1 Implement output.csv writer with exact column order
  - **Goal**: Write output rows to CSV with the 14 required columns in exact order
  - **Files**: `code/io_utils.py`
  - **Verification**: Write a test row, read it back, confirm column order matches spec
  - **Evidence**: Written CSV header, column order comparison
  - **Decision**: Proceed if column order matches exactly

## 6. Implement Schema/Enums Validator

- [x] 6.1 Implement allowed value constants for all enum fields
  - **Goal**: Define allowed values for claim_status, issue_type, object_part (per claim_object), severity, risk_flags, evidence_standard_met, valid_image
  - **Files**: `code/models.py`
  - **Verification**: Unit test that all expected values are present in each allowed set
  - **Evidence**: Allowed value definitions, test results
  - **Decision**: Proceed if all allowed values match the spec

- [x] 6.2 Implement output row validation function
  - **Goal**: Validate a single output row against all schema rules
  - **Files**: `code/validation.py`
  - **Verification**: Test with valid row (passes), invalid claim_status (fails), invalid object_part for car (fails), invalid supporting_image_id (fails)
  - **Evidence**: Validation results for 4 test cases
  - **Decision**: Proceed if validation catches all invalid cases and passes valid ones

## 7. Implement Baseline Safe Reviewer

- [x] 7.1 Implement baseline reviewer that produces valid rows without VLM
  - **Goal**: Create a fallback that generates valid output rows with safe defaults for every claim
  - **Files**: `code/reviewer.py`
  - **Verification**: Run baseline on claims.csv, validate all 44 output rows pass schema validation
  - **Evidence**: Validation pass rate (expect 44/44)
  - **Decision**: Proceed if all rows are valid (even if accuracy is low)

## 8. Implement Model/VLM Review Abstraction

- [x] 8.1 Implement model provider abstraction (OpenAI/Anthropic interface)
  - **Goal**: Create a common interface for VLM calls that supports provider switching
  - **Files**: `code/models.py`
  - **Verification**: Instantiate provider with OPENAI_API_KEY env var, confirm provider is selected
  - **Evidence**: Provider selection output
  - **Decision**: Proceed if abstraction initializes correctly with available env vars

- [x] 8.2 Implement VLM call with image attachment and structured JSON response
  - **Goal**: Send images and prompt to VLM, receive structured JSON response
  - **Files**: `code/models.py`
  - **Verification**: Call VLM with one test image and a simple prompt, confirm JSON response is received
  - **Evidence**: VLM response JSON, token usage
  - **Decision**: Proceed if VLM returns parseable JSON with expected fields

- [x] 9.1 Design and implement the VLM system prompt for evidence review
  - **Goal**: Create a prompt that instructs the VLM to extract claims, review images, and return structured output
  - **Files**: `code/prompts.py`
  - **Verification**: Review prompt against all allowed values, decision rules, and guardrails from the spec
  - **Evidence**: Prompt text, checklist of covered requirements
  - **Decision**: Proceed if prompt covers claim extraction, image review, evidence standard, risk flags, severity, and output schema

- [ ] 9.2 Implement claim extraction from user_claim conversation text
  - **Goal**: Extract the specific damage claim (issue type, object part, description) from the conversation
  - **Files**: `code/reviewer.py`, `code/prompts.py`
  - **Verification**: Test extraction on 5 sample claims, compare extracted claims against expected issue_type and object_part
  - **Evidence**: Extraction results for 5 claims, accuracy
  - **Decision**: Proceed if extraction is correct for at least 4/5 claims

- [ ] 9.3 Implement VLM image review call with all images and extracted claim
  - **Goal**: Send all images and extracted claim to VLM, receive structured review result
  - **Files**: `code/reviewer.py`
  - **Verification**: Run VLM review on 3 sample claims with known expected outputs, compare results
  - **Evidence**: VLM review results, comparison with expected outputs
  - **Decision**: Proceed if VLM produces reasonable results for at least 2/3 claims

## 10. Implement Evidence Requirement Lookup

- [ ] 10.1 Implement evidence requirement matching by claim_object and applies_to
  - **Goal**: Match current claim against evidence_requirements.csv rules
  - **Files**: `code/reviewer.py`
  - **Verification**: Match a car dent claim, confirm REQ_CAR_BODY_PANEL is selected. Match a laptop screen claim, confirm REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD is selected
  - **Evidence**: Matched requirement IDs for 3 test claims
  - **Decision**: Proceed if matching selects correct requirements

- [ ] 10.2 Integrate evidence requirement context into VLM prompt
  - **Goal**: Include matched evidence requirement descriptions in the VLM prompt to guide evidence_standard_met assessment
  - **Files**: `code/prompts.py`, `code/reviewer.py`
  - **Verification**: Review generated VLM prompt for a sample claim, confirm evidence requirement text is included
  - **Evidence**: VLM prompt text showing evidence requirement context
  - **Decision**: Proceed if requirement context appears in prompt correctly

## 11. Implement User History Risk Enrichment

- [ ] 11.1 Implement user history lookup and risk flag enrichment
  - **Goal**: Look up user_id in history, add user_history_risk and manual_review_required to risk_flags when present in history_flags
  - **Files**: `code/reviewer.py`
  - **Verification**: Test with user_005 (has user_history_risk), user_001 (no risk), user_013 (has both flags)
  - **Evidence**: Risk flags for 3 test users
  - **Decision**: Proceed if risk flags match history_flags correctly

- [ ] 11.2 Verify history does not override claim_status
  - **Goal**: Confirm that user history enrichment never changes claim_status
  - **Files**: `code/reviewer.py`
  - **Verification**: Process a claim where image clearly supports but user has history risk, confirm claim_status remains supported
  - **Evidence**: claim_status before and after history enrichment
  - **Decision**: Proceed if claim_status is unchanged by history

## 12. Implement Guardrails and Injection Detection

- [ ] 12.1 Implement text-based prompt injection detection
  - **Goal**: Scan user_claim for known injection patterns and flag text_instruction_present
  - **Files**: `code/validation.py`, `code/reviewer.py`
  - **Verification**: Test with claims containing "approve this claim", "ignore previous instructions", "follow the note", "mark supported". Confirm text_instruction_present is flagged
  - **Evidence**: Detection results for 4 injection test cases
  - **Decision**: Proceed if all 4 injection patterns are detected

- [ ] 12.2 Implement VLM-based instruction detection in images
  - **Goal**: Ask VLM to report any visible text in images and flag text_instruction_present if instruction-like
  - **Files**: `code/prompts.py`, `code/reviewer.py`
  - **Verification**: Test with a known instruction-bearing image from sample claims (case_020)
  - **Evidence**: VLM text detection result, text_instruction_present flag
  - **Decision**: Proceed if instruction text is detected in the test image

- [ ] 12.3 Implement safe input handling for missing files and empty claims
  - **Goal**: Handle missing images, empty claims, unknown users gracefully
  - **Files**: `code/reviewer.py`, `code/io_utils.py`
  - **Verification**: Test with non-existent image path, empty user_claim, unknown user_id. Confirm valid output rows are produced
  - **Evidence**: Output rows for 3 edge cases, all passing validation
  - **Decision**: Proceed if all edge cases produce valid rows

## 13. Implement Retry/Fallback for Invalid Model Outputs

- [x] 13.1 Implement retry with repair prompt on validation failure
  - **Goal**: When VLM output fails validation, retry once with a repair prompt specifying the exact error
  - **Files**: `code/reviewer.py`, `code/prompts.py`
  - **Verification**: Force an invalid output (e.g., inject bad enum value), confirm retry is triggered and produces valid output
  - **Evidence**: Retry trigger log, corrected output
  - **Decision**: Proceed if retry mechanism recovers from invalid output

- [x] 13.2 Implement safe fallback after retry failure
  - **Goal**: If retry also fails, produce a safe fallback row with not_enough_information
  - **Files**: `code/reviewer.py`
  - **Verification**: Force both initial and retry to fail, confirm fallback row is valid
  - **Evidence**: Fallback row content, validation result
  - **Decision**: Proceed if fallback row passes all validation checks

- [ ] 13.3 Implement exponential backoff for API errors
  - **Goal**: Retry API calls with increasing delay on 429/500 errors
  - **Files**: `code/models.py`
  - **Verification**: Simulate rate limit error, confirm backoff delays increase (1s, 2s, 4s)
  - **Evidence**: Backoff timing log
  - **Decision**: Proceed if backoff works correctly

## 14. Implement Sample Evaluation Script

- [x] 14.1 Implement evaluation script that runs on sample_claims.csv
  - **Goal**: Process all 20 sample claims and compare against expected outputs
  - **Files**: `code/evaluation/evaluate.py`
  - **Verification**: Run evaluate.py, confirm it processes all 20 rows and produces comparison results
  - **Evidence**: Evaluation output showing predicted vs expected for each row
  - **Decision**: Proceed if evaluation runs end-to-end without errors

- [x] 14.2 Implement per-field accuracy metrics
  - **Goal**: Calculate and report accuracy for claim_status, issue_type, object_part, evidence_standard_met, severity, risk_flags, supporting_image_ids, valid_image
  - **Files**: `code/evaluation/evaluate.py`
  - **Verification**: Run evaluation, confirm per-field accuracy percentages are reported for all 8 fields
  - **Evidence**: Per-field accuracy table
  - **Decision**: Proceed if all 8 field accuracies are reported

- [x] 14.3 Implement failure categorization
  - **Goal**: Categorize each failure as claim extraction, visual review, evidence standard, risk flag, severity, or formatting error
  - **Files**: `code/evaluation/evaluate.py`
  - **Verification**: Run evaluation, confirm failures are categorized and counts are reported
  - **Evidence**: Failure categorization summary
  - **Decision**: Proceed if categorization covers all failure types

## 15. Implement Evaluation Report Generation

- [x] 15.1 Generate evaluation/evaluation_report.md with metrics and operational analysis
  - **Goal**: Produce a Markdown report with accuracy metrics, strategy comparison, and operational analysis
  - **Files**: `code/evaluation/evaluate.py`, `code/evaluation/evaluation_report.md`
  - **Verification**: Report exists, contains accuracy metrics, at least 2 strategies compared, operational analysis with all required metrics
  - **Evidence**: Report content summary, checklist of required sections
  - **Decision**: Proceed if report covers all required sections

- [x] 15.2 Track and report operational metrics (model calls, tokens, images, cost, latency)
  - **Goal**: Collect and report model call counts, token usage, image count, estimated cost, runtime
  - **Files**: `code/reviewer.py`, `code/evaluation/evaluate.py`
  - **Verification**: After running on sample claims, confirm all 6 operational metrics are tracked and reported
  - **Evidence**: Operational metrics values
  - **Decision**: Proceed if all metrics are available

## 16. Implement Logging and Debug Traces

- [ ] 16.1 Implement per-claim debug logging to JSONL
  - **Goal**: Log every claim processing step (input, extraction, VLM prompt/response, validation, output) to debug_log.jsonl
  - **Files**: `code/reviewer.py`, `code/main.py`
  - **Evidence**: Sample debug log entries for one claim
  - **Verification**: Process one claim, confirm debug_log.jsonl contains structured entries for each step
  - **Decision**: Proceed if log captures all processing steps

- [ ] 16.2 Ensure debug log does not contain secrets
  - **Goal**: Verify no API keys or tokens appear in debug output
  - **Files**: `code/reviewer.py`
  - **Verification**: Search debug_log.jsonl for any strings matching API key patterns
  - **Evidence**: Secret scan result (expect no matches)
  - **Decision**: Proceed if no secrets are found in logs

## 17. Implement README and Run Instructions

- [x] 17.1 Write code/README.md with setup, env vars, commands, evaluation, and output
  - **Goal**: Document how to set up, run, and evaluate the system
  - **Files**: `code/README.md`
  - **Verification**: README contains sections for: prerequisites, environment variables, run command, evaluation command, output description
  - **Evidence**: README section checklist
  - **Decision**: Proceed if all required sections are present

## 18. Implement Final Dry Run and Packaging Checks

- [x] 18.1 Run full dry run on claims.csv and validate output.csv
  - **Goal**: Execute `python main.py --input ../dataset/claims.csv --output ../output.csv` and validate the output
  - **Files**: `code/main.py`, `output.csv`
  - **Verification**: Command exits 0, output.csv has 44 rows, all rows pass validation, column order is correct
  - **Evidence**: Exit code, row count, validation results
  - **Decision**: Proceed if dry run produces valid output.csv

- [ ] 18.2 Verify no hardcoded answers, no secrets, no absolute paths
  - **Goal**: Final scan for prohibited content
  - **Files**: All files in code/
  - **Verification**: Grep for hardcoded claim IDs, API key patterns, absolute paths (C:\, /home/, /Users/)
  - **Evidence**: Scan results (expect no matches)
  - **Decision**: Proceed if no prohibited content is found

- [ ] 18.3 Verify code.zip packaging excludes prohibited content
  - **Goal**: Confirm the submission package is clean
  - **Files**: code.zip (or zip creation script)
  - **Verification**: List zip contents, confirm no virtualenvs, node_modules, __pycache__, dataset/, .env files
  - **Evidence**: Zip contents listing, prohibited content check
  - **Decision**: Proceed if packaging is clean

- [x] 18.4 Run evaluation on sample_claims.csv one final time and confirm report
  - **Goal**: Final evaluation run to ensure everything is consistent
  - **Files**: `code/evaluation/evaluate.py`, `code/evaluation/evaluation_report.md`
  - **Verification**: Evaluation runs, report is generated, metrics are reasonable
  - **Evidence**: Final evaluation metrics summary
  - **Decision**: Submission is ready when all checks pass
