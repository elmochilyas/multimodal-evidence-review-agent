# Architecture

## Overview

The Evidence Review Agent follows a **single-agent pipeline architecture**. A single vision-language model (VLM) performs all evidence review tasks: claim extraction, image inspection, evidence sufficiency checking, risk flagging, and decision generation. Deterministic guardrails handle post-processing and schema validation.

## Pipeline

```text
┌──────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  claims.csv  │────▶│  Claim Extractor │────▶│  Image Loader       │
│  user_claim  │     │  (parse          │     │  (Pillow: normalize,│
│  image_paths │     │   conversation)  │     │   encode as data    │
│  claim_object│     │                  │     │   URL for VLM)      │
└──────────────┘     └──────────────────┘     └──────────┬──────────┘
                                                          │
┌──────────────┐     ┌──────────────────┐                 │
│user_history  │────▶│  Risk Context    │                 │
│.csv          │     │  (attach history │                 │
│              │     │   summary +      │                 │
│              │     │   risk flags)    │                 │
└──────────────┘     └──────────────────┘                 │
                                                          ▼
┌──────────────┐     ┌──────────────────────────────────────────┐
│ evidence_    │────▶│  VLM Evidence Reviewer                    │
│ requirements │     │  (src/model_review.py)                    │
│ .csv         │     │  - Inspects images + claim + history      │
│              │     │  - Checks evidence requirements           │
│              │     │  - Identifies issue type, part, severity  │
│              │     │  - Produces structured JSON decision      │
└──────────────┘     └──────────────────┬───────────────────────┘
                                         ▼
                ┌─────────────────────────────────────────┐
                │  Deterministic Post-Processing           │
                │  (src/post_processing.py)                │
                │  - Fixes contradictions                  │
                │  - Validates evidence gaps               │
                │  - Calibrates severity                   │
                └──────────────────┬──────────────────────┘
                                    ▼
                ┌─────────────────────────────────────────┐
                │  Schema / Enum Validator                 │
                │  (src/validation.py)                     │
                │  - Checks enum-safe values               │
                │  - Validates column presence             │
                │  - Ensures boolean fields are correct    │
                └──────────────────┬──────────────────────┘
                                    ▼
                ┌─────────────────────────────────────────┐
                │  CSV Writer                              │
                │  (src/io_utils.py)                       │
                │  - Writes output.csv with exact columns  │
                └─────────────────────────────────────────┘
```

## Component Details

### 1. Input Loading (`src/io_utils.py`)
Loads three CSV files: claims, user history, and evidence requirements. Image paths are resolved relative to the dataset directory.

### 2. Claim Extraction
The user claim column contains a chat conversation. The system must extract the actual damage claim — what object part is damaged, what type of damage, and any additional context.

### 3. Image Loading (`src/image_utils.py`)
Each image is opened with Pillow, EXIF-oriented, converted to RGB, and JPEG-encoded into a data URL. This ensures consistent image format regardless of the source.

### 4. VLM Evidence Review (`src/model_review.py`)
The core review function:
- Builds a prompt from the claim, images, evidence requirements, and user history
- Sends the prompt to a vision-capable model
- Parses the structured JSON response
- Retries on failure with safe fallback

### 5. Post-Processing (`src/post_processing.py`)
Deterministic guardrails that:
- Fix contradictory evidence assignments
- Detect package contents claims with only exterior photos
- Apply conservative label changes only when unambiguous

### 6. Severity Calibration (`src/severity.py`)
Deterministic severity assignment based on issue type, claim status, and object type.

### 7. Validation (`src/validation.py`)
Strict schema and enum validation ensuring every output row meets the required contract.

### 8. CSV Output (`src/io_utils.py`)
Writes the final output with exact column order and quoting rules.

## Key Design Decisions

- **Single-agent**: One VLM handles all reasoning. No multi-agent orchestration needed.
- **Deterministic guardrails**: Post-processing and validation are rule-based, not AI-driven.
- **Conservative fallbacks**: Any failure produces a safe row (not_enough_information, manual_review_required).
- **Images before text**: The system prioritizes visual evidence over the user's claim statement.
