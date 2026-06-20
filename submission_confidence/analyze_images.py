"""Analyze test images for manual inspection support."""
import csv
import os
from pathlib import Path
from PIL import Image

BASE = Path("C:/Users/Pc/Desktop/hackaton/hackerrank-orchestrate-june26")
TEST_IMG = BASE / "dataset" / "images" / "test"
OUTPUT = BASE / "output.csv"

def load_csv(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))

output = load_csv(OUTPUT)

def img_info(path):
    try:
        with Image.open(path) as im:
            size = im.size
            fmt = im.format or "UNKNOWN"
            kb = os.path.getsize(path) // 1024
            return (size[0], size[1]), fmt, kb
    except Exception as e:
        return None, str(e), 0

selected = {
    # 10 cars
    "case_001": "front bumper + left headlight damaged",
    "case_004": "windshield shattered by stone",
    "case_005": "side mirror missing/broken",
    "case_006": "hood hail dents",
    "case_007": "rear bumper dent",
    "case_008": "headlight broken",
    "case_010": "door dent + rear bumper damage",
    "case_011": "taillight cracked",
    "case_041": "blue car front bumper damaged",
    "case_051": "black car door dented",
    # 10 laptops
    "case_017": "laptop screen crack",
    "case_018": "keyboard liquid damage",
    "case_019": "hinge broken + screen crack",
    "case_020": "trackpad cracked",
    "case_025": "missing keyboard keys",
    "case_026": "laptop body crack",
    "case_027": "screen liquid stain",
    "case_028": "hinge damage",
    "case_044": "laptop screen broken (stock photo)",
    "case_056": "laptop corner dent",
    # 10 packages
    "case_029": "package corner crushed",
    "case_030": "package torn seal",
    "case_031": "wet box + unreadable label",
    "case_032": "missing product inside",
    "case_034": "damaged label",
    "case_036": "water damage + instruction note",
    "case_037": "crushed packaging",
    "case_038": "inside item broken",
    "case_048": "package crushed + instruction",
    "case_055": "package seal torn + instruction",
}

# Map case_id -> user_id
claims_map = {}
with open(BASE / "dataset" / "claims.csv", encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        paths = row['image_paths']
        case_id = None
        for part in paths.split(';'):
            p = Path(part)
            if p.parent.name.startswith('case_'):
                case_id = p.parent.name
                break
        if case_id:
            claims_map[case_id] = row['user_id']

output_map = {}
for r in output:
    uid = r['user_id']
    output_map[uid] = r

all_results = []

for case_id, claim_desc in selected.items():
    case_dir = TEST_IMG / case_id
    uid = claims_map.get(case_id, "UNKNOWN")
    
    print(f"\n{'='*80}")
    print(f"CASE: {case_id} | USER: {uid}")
    print(f"Claim: {claim_desc}")
    
    img_details = []
    if case_dir.exists():
        imgs = sorted(str(p.name) for p in case_dir.iterdir() if p.is_file() and not p.name.startswith('.'))
        for img_name in imgs:
            img_path = case_dir / img_name
            wh, fmt_or_err, kb = img_info(img_path)
            if isinstance(wh, tuple):
                desc = f"{img_name} ({wh[0]}x{wh[1]}, {fmt_or_err}, {kb}KB)"
            else:
                desc = f"{img_name} (ERROR: {fmt_or_err})"
            print(f"  Image: {desc}")
            img_details.append(desc)
    else:
        print(f"  WARNING: Directory not found")
        img_details.append("DIR NOT FOUND")
    
    pred = output_map.get(uid)
    if pred:
        print(f"\n  PREDICTION:")
        print(f"    claim_status: {pred['claim_status']}")
        print(f"    issue_type: {pred['issue_type']}")
        print(f"    object_part: {pred['object_part']}")
        print(f"    severity: {pred['severity']}")
        print(f"    evidence_standard_met: {pred['evidence_standard_met']}")
        print(f"    risk_flags: {pred['risk_flags']}")
        print(f"    supporting_image_ids: {pred['supporting_image_ids']}")
        print(f"    valid_image: {pred['valid_image']}")
        j = pred['claim_status_justification']
        print(f"    justification: {j[:150]}...")
        er = pred['evidence_standard_met_reason']
        print(f"    evidence_reason: {er[:150]}...")
        
        # Suspicion analysis
        flags = pred['risk_flags']
        cs = pred['claim_status']
        suspicious = []
        
        if 'wrong_object' in flags: suspicious.append("wrong_object detected")
        if 'non_original_image' in flags: suspicious.append("non-original image")
        if 'claim_mismatch' in flags and cs == 'supported': suspicious.append("mismatch flagged but supported!")
        if 'manual_review_required' not in flags and uid in {'user_005', 'user_037', 'user_040', 'user_016'}:
            suspicious.append("high-risk user but no manual_review flag")
        if cs == 'supported' and pred['issue_type'] == 'none':
            suspicious.append("supported with no issue")
        if cs == 'supported' and pred['valid_image'] == 'false':
            suspicious.append("supported with invalid image")
        if pred['evidence_standard_met'] == 'true' and pred['supporting_image_ids'] == 'none':
            suspicious.append("evidence_met=true but no supporting images")
        
        if suspicious:
            print(f"  ** SUSPICIOUS: {'; '.join(suspicious)}")
        
        all_results.append({
            'case': case_id,
            'user': uid,
            'claim_desc': claim_desc,
            'images': '; '.join(img_details),
            'claim_status': pred['claim_status'],
            'issue_type': pred['issue_type'],
            'object_part': pred['object_part'],
            'severity': pred['severity'],
            'evidence_standard_met': pred['evidence_standard_met'],
            'risk_flags': pred['risk_flags'],
            'supporting_image_ids': pred['supporting_image_ids'],
            'valid_image': pred['valid_image'],
            'justification': pred['claim_status_justification'],
            'evidence_reason': pred['evidence_standard_met_reason'],
            'suspicious': '; '.join(suspicious) if suspicious else 'none',
        })
    else:
        print(f"  WARNING: No prediction found for {uid}")
    print()

print("="*60)
print(f"Total inspected: {len(all_results)}")
print(f"Suspicious rows: {sum(1 for r in all_results if r['suspicious'] != 'none')}")
print("="*60)
