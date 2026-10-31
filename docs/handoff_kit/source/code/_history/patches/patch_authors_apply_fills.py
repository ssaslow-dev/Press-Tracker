"""T30: apply_fills.py change — Author 1..N + Author title (Coverage + Originals), green, right after "Author / byline".
Usage: python3 -I patch_apply_fills.py IN.py OUT.py   (anchors must match exactly once)
Needs code/authorsplit.py and code/author_columns.py next to apply_fills.py.
"""
import sys
src, dst = sys.argv[1:3]
t = open(src, encoding='utf-8').read()
BLOCK = '''# --- T30 author columns (agent-authorsplit; DECISIONS 2026-10-27 "authors split into columns") ---
# Runs LAST, after every put(): inserting columns shifts column indexes, and bylines written above are split too.
# Sources: the sheet's "Author / byline"; out/author_fills.csv (T24 structured split, keeps titles) when it names the
# same people; out/author_overrides.csv (aid, authors joined " | ", title) = Sammy's 15-authors queue answers.
# Rows in --hold are split like any other row (the columns only restate the existing byline).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from author_columns import add_author_columns
_af = os.path.join(W, 'out', 'author_fills.csv')
_fills = {}
if os.path.exists(_af):
    for _x in pd.read_csv(_af, dtype=str).fillna('').to_dict('records'):
        if _x.get('authors'): _x = fix_ids(_x); _fills[_x['aid']] = _x
_ovf = os.path.join(W, 'out', 'author_overrides.csv')
_over = {}
if os.path.exists(_ovf):
    for _x in pd.read_csv(_ovf, dtype=str).fillna('').to_dict('records'):
        _x = fix_ids(_x); _over[_x['aid']] = (_x['authors'], _x.get('title', ''))
rep['author_columns'] = add_author_columns(wb, fills=_fills, overrides=_over)
# --- end author columns ---
wb.save(a.out)
'''
R = [
    ("# --- end Press release ---\nwb.save(a.out)\n", "# --- end Press release ---\n" + BLOCK),
    ("    new = [c for c in y.columns if c not in x.columns]\n    assert new in ([], ['Press release']), (s, new)\n",
     "    AUTH = rep['author_columns'][s]['columns'] if rep['author_columns'][s]['inserted'] else []\n"
     "    if AUTH:   # T30: Author 1..N + Author title sit right after Author / byline\n"
     "        _i = list(y.columns).index('Author / byline'); assert list(y.columns)[_i + 1:_i + 1 + len(AUTH)] == AUTH, (s, 'author cols')\n"
     "    new = [c for c in y.columns if c not in x.columns and c not in AUTH]\n    assert new in ([], ['Press release']), (s, new)\n"),
]
for old, new in R:
    n = t.count(old)
    if n != 1: sys.exit(f'anchor found {n}x: {old[:80]!r}')
    t = t.replace(old, new)
open(dst, 'w', encoding='utf-8').write(t)
print('ok', dst)
