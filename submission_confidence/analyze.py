"""Comprehensive analysis of output.csv for Submission Confidence Report."""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path("C:/Users/Pc/Desktop/hackaton/hackerrank-orchestrate-june26")
OUTPUT = BASE / "output.csv"
CLAIMS = BASE / "dataset" / "claims.csv"
SAMPLE = BASE / "dataset" / "sample_claims.csv"
HISTORY = BASE / "dataset" / "user_history.csv"
REQS = BASE / "dataset" / "evidence_requirements.csv"

def load_csv(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))

output = load_csv(OUTPUT)
claims = load_csv(CLAIMS)
sample = load_csv(SAMPLE)
history = load_csv(HISTORY)

# --- 1. Per-field value distributions ---
print("=== FIELD VALUE DISTRIBUTIONS ===")
fields = ['claim_status', 'issue_type', 'object_part', 'severity', 'evidence_standard_met', 'valid_image']
for field in fields:
    counts = Counter(r[field] for r in output)
    print(f"\n{field}:")
    for val, cnt in counts.most_common():
        print(f"  {val}: {cnt}")

print("\n\n")

# --- 2. claim_status by object type ---
print("=== CLAIM STATUS BY OBJECT TYPE ===")
for obj in ['car', 'laptop', 'package']:
    obj_claims = [r for r in output if r['claim_object'] == obj]
    counts = Counter(r['claim_status'] for r in obj_claims)
    print(f"\n{obj} ({len(obj_claims)} rows):")
    for val, cnt in counts.most_common():
        print(f"  {val}: {cnt}")

print("\n\n")

# --- 3. Risk flags analysis ---
print("=== RISK FLAGS ANALYSIS ===")
all_flags = []
row_flags = {}
for r in output:
    flags = r['risk_flags'].split(';') if r['risk_flags'] != 'none' else []
    all_flags.extend(flags)
    row_flags[r['user_id']] = flags

flag_counts = Counter(all_flags)
print("Flag distribution:")
for flag, cnt in flag_counts.most_common():
    print(f"  {flag}: {cnt}")

rows_with_manual_review = sum(1 for r in output if 'manual_review_required' in r['risk_flags'])
print(f"\nRows with manual_review_required: {rows_with_manual_review}/{len(output)} ({100*rows_with_manual_review//len(output)}%)")

# --- 4. Check for high-risk patterns ---
print("\n\n=== HIGH-RISK PATTERN DETECTION ===")
high_risk_flags = {'wrong_object', 'wrong_object_part', 'non_original_image', 
                   'possible_manipulation', 'claim_mismatch', 'blurry_image',
                   'cropped_or_obstructed', 'low_light_or_glare', 'text_instruction_present'}
for r in output:
    flags = set(r['risk_flags'].split(';'))
    high = flags & high_risk_flags
    if high:
        print(f"  {r['user_id']} ({r['claim_object']}): {', '.join(sorted(high))}")

# --- 5. Consistency checks ---
print("\n\n=== CONSISTENCY CHECKS ===")

# Check 1: contradicted + supporting_image_ids == none
contradicted_none = sum(1 for r in output if r['claim_status'] == 'contradicted' and r['supporting_image_ids'] == 'none')
print(f"Contradicted with no supporting images: {contradicted_none}")

# Check 2: supported + supporting_image_ids == none
supported_none = sum(1 for r in output if r['claim_status'] == 'supported' and r['supporting_image_ids'] == 'none')
print(f"Supported with no supporting images: {supported_none}")

# Check 3: issue_type=none + claim_status=support
issue_none_supported = sum(1 for r in output if r['issue_type'] == 'none' and r['claim_status'] == 'supported')
print(f"Issue type 'none' but claim supported: {issue_none_supported}")

# Check 4: issue_type=unknown + non-unknown part
unknown_part = sum(1 for r in output if r['issue_type'] == 'unknown' and r['object_part'] != 'unknown')
print(f"Issue type unknown with known part: {unknown_part}")

# Check 5: evidence_standard_met=true with supporting none
esm_true_none = sum(1 for r in output if r['evidence_standard_met'] == 'true' and r['supporting_image_ids'] == 'none')
print(f"evidence_standard_met=true but no supporting images: {esm_true_none}")

# Check 6: valid_image=false but claim_status=support
vf_supported = sum(1 for r in output if r['valid_image'] == 'false' and r['claim_status'] == 'supported')
print(f"valid_image=false but claim supported: {vf_supported}")

# Check 7: valid_image=false but evidence_standard_met=true
vf_esm_true = sum(1 for r in output if r['valid_image'] == 'false' and r['evidence_standard_met'] == 'true')
print(f"valid_image=false but evidence_standard_met=true: {vf_esm_true}")

# --- 6. Type-part consistency ---
print("\n\n=== ISSUE TYPE vs OBJECT PART CONSISTENCY ===")
for r in output:
    issue = r['issue_type']
    part = r['object_part']
    obj = r['claim_object']
    # Package issues with non-package parts
    if obj == 'package':
        package_parts = {'box', 'package_corner', 'package_side', 'seal', 'label', 'contents', 'item', 'unknown'}
        if part not in package_parts:
            print(f"  {r['user_id']}: package with part={part}")
    # Car issues
    if obj == 'car':
        if part == 'screen':  # common mistake
            print(f"  {r['user_id']}: car with part={part} (car has no screen!)")

# --- 7. User history risk overriding analysis ---
print("\n\n=== USER HISTORY RISK ANALYSIS ===")
history_map = {h['user_id']: h for h in history}
for r in output:
    uid = r['user_id']
    if uid in history_map:
        hist = history_map[uid]
        hist_flags = hist.get('history_flags', 'none')
        rejected = int(hist.get('rejected_claim', '0'))
        if rejected >= 3 and r['claim_status'] != 'not_enough_information':
            print(f"  {uid}: {rejected} rejected claims, status={r['claim_status']}")
    else:
        print(f"  {uid}: NOT FOUND in user_history.csv")

# --- 8. Supporting image ID analysis ---
print("\n\n=== SUPPORTING IMAGE ID ANALYSIS ===")
for r in output:
    ids = r['supporting_image_ids']
    if ids != 'none':
        id_list = ids.split(';')
        for img_id in id_list:
            if not img_id.startswith('img_'):
                print(f"  {r['user_id']}: unusual image ID format: {img_id}")

# --- 9. Justification quality ---
print("\n\n=== JUSTIFICATION QUALITY ===")
for r in output:
    just = r['claim_status_justification']
    if len(just) < 20:
        print(f"  {r['user_id']}: very short justification ({len(just)} chars): {just}")
    if 'model flags' in just.lower():
        print(f"  {r['user_id']}: generic post-processing justification")

# --- 10. Count per object type ---
obj_counts = Counter(r['claim_object'] for r in output)
print(f"\n\n=== OBJECT TYPE COUNTS ===")
for obj, cnt in obj_counts.most_common():
    print(f"  {obj}: {cnt}")

# --- Summary ---
print("\n\n=== SUMMARY ===")
total = len(output)
print(f"Total rows: {total}")
print(f"Supported: {sum(1 for r in output if r['claim_status'] == 'supported')}")
print(f"Contradicted: {sum(1 for r in output if r['claim_status'] == 'contradicted')}")
print(f"Not enough info: {sum(1 for r in output if r['claim_status'] == 'not_enough_information')}")
print(f"evidence_standard_met=true: {sum(1 for r in output if r['evidence_standard_met'] == 'true')}")
print(f"valid_image=true: {sum(1 for r in output if r['valid_image'] == 'true')}")
