import csv

with open('output_locked_before_final_audit.csv', encoding='utf-8') as f:
    locked = list(csv.DictReader(f))
with open('output.csv', encoding='utf-8') as f:
    final = list(csv.DictReader(f))

diffs = 0
for i, (l, f) in enumerate(zip(locked, final)):
    row_diffs = [(col, l[col], f[col]) for col in l if l[col] != f[col]]
    if row_diffs:
        diffs += 1
        print(f'Row {i+1} (user={l["user_id"]}):')
        for col, lv, fv in row_diffs:
            print(f'  {col}:')
            print(f'    locked: {lv[:80]}')
            print(f'    final:  {fv[:80]}')

print(f'\nTotal differing rows: {diffs}/{len(locked)}')
