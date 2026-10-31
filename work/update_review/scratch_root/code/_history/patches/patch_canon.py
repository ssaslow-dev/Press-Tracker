"""AUTHOR-CANON (agent-final-F4, 2026-10-27): same-person author names Sammy decided in the review queue (15-authors,
"One person"/"Merge as") are applied when the tracker data is built, so every rebuild (incl. the sheet task's) keeps them.
build_data.py reads author_canon.csv (columns item,key,canonical; key = author_key form, several joined ' ~ ') from its own
folder; an author whose author_key matches a key (or the canonical name's key) is shown under the canonical name; two
forms of one person in one byline are listed once. The sheet's Author N cells are not changed.
Usage: python3 -I patch_canon.py BUILD_DATA [PROMPT.md]   (idempotent: marker AUTHOR-CANON)"""
import sys
MARK = 'AUTHOR-CANON'
BD_ANCHOR = "def s(v): return str(v).strip()\n"
BD_BLOCK = '''# ---- AUTHOR-CANON (agent-final-F4): same-person names from Sammy's review queue (author_canon.csv next to this file)
import csv as _csv
from authorsplit import author_key as _akey
CANON = {}
_cp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'author_canon.csv')
if os.path.exists(_cp):
    for _r in _csv.DictReader(open(_cp, encoding='utf-8')):
        for _k in _r['key'].split(' ~ '): CANON[_k.strip()] = _r['canonical'].strip()
        CANON[_akey(_r['canonical'])] = _r['canonical'].strip()
CANON_HITS = collections.Counter()
_authors_raw = authors_of
def authors_of(r, o):
    a, t = _authors_raw(r, o); out, seen = [], set()
    for x in a:
        c = CANON.get(_akey(x), x)
        if c != x: CANON_HITS[x + ' -> ' + c] += 1
        if _akey(c) in seen: continue
        seen.add(_akey(c)); out.append(c)
    return out, t
# ---- /AUTHOR-CANON
'''
PR_ANCHOR = "  - `pipeline/authorsplit.py` (build_data.py imports it)\n"
PR_LINE = "  - `pipeline/author_canon.csv` (same-person author names Sammy merged; build_data.py reads it from its own folder)  <!-- AUTHOR-CANON -->\n"
a = sys.argv[1:]
t = open(a[0], encoding='utf-8').read()
if MARK in t: print('build_data: already applied')
else:
    if t.count(BD_ANCHOR) != 1 or 'def authors_of(' not in t or t.find('def authors_of(') > t.find(BD_ANCHOR):
        sys.exit('build_data: anchor not found once (or authors_of not defined before it); not patching')
    open(a[0], 'w', encoding='utf-8').write(t.replace(BD_ANCHOR, BD_BLOCK + BD_ANCHOR)); print('build_data: applied')
if len(a) > 1:
    p = open(a[1], encoding='utf-8').read()
    if MARK in p: print('prompt: already applied')
    elif p.count(PR_ANCHOR) != 1: sys.exit('prompt: anchor not found once; not patching')
    else: open(a[1], 'w', encoding='utf-8').write(p.replace(PR_ANCHOR, PR_ANCHOR + PR_LINE)); print('prompt: applied')
