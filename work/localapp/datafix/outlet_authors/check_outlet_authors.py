"""Check 2: Author 1..9 cells that are the outlet/publisher name. Read-only. Run: python3 -I check_outlet_authors.py"""
import sys, os, re, csv, collections, json
sys.path.insert(0, '/home/user/Press-Tracker/work/localapp/datafix')
from common import *
import authorsplit as A
OUT = os.path.dirname(os.path.abspath(__file__))
h, R = load_coverage()
AC = [f'Author {i}' for i in range(1, 10)]
PERSONS = {'nadia rahman', 'noah mccashland', 'marion nestle', 'philip lempert', 'anthony cabassa', 'stephen sachs', 'carol kocivar',
           'tom kemp', 'george christopher thomas', 'jeff krasno'}   # outlets that ARE one person: the name is a real byline
WIRES = {'associated press', 'city news service', 'pr newswire', 'tribune content agency', 'bay city news foundation', 'reuters', 'bloomberg', 'afp', 'jta', 'cnn'}
STAFF_RX = re.compile(r'\b(staff|editorial board|editors?|newsroom)$')
SOFT = {'ground game la', 'los angeles county politics', 'palate shift', 'california current', 'alston bird', 'telemundo 52'}  # brand/blog labels: medium

def nk(x):
    x = A.fold(s(x)).lower(); x = re.sub(r'\([^)]*\)|: .*$', ' ', x)
    x = re.sub(r'[^a-z0-9 ]', ' ', x); x = re.sub(r'\b(the|inc|llc)\b', ' ', x); return re.sub(r'\s+', ' ', x).strip()
allo = set()
for r in R:
    for f in ('Outlet', 'Publisher'):
        if re.search(r'\((substack|medium)\)', s(r[f]), re.I): PERSONS.add(nk(r[f])); continue   # a one-person blog: the name is the writer
        for k in (nk(r[f]), nk(A.disp(r[f]))):
            if k: allo.add(k)
def own_keys(r):
    return {k for f in ('Outlet', 'Publisher') for k in (nk(r[f]), nk(A.disp(r[f]))) if k}

found = []   # one per cell
for r in R:
    on = own_keys(r)
    for c in AC:
        v = s(r[c])
        if not v: continue
        k = nk(v)
        if not k: continue
        base = STAFF_RX.sub('', k).strip()
        if k != base and base in on:
            cat = 'group-staff-or-board'          # allowed by the rules (group of people)
        elif k in on:
            cat = 'person-is-outlet' if k in PERSONS else ('wire-own' if k in WIRES else 'own-outlet')
        elif k in allo and k not in PERSONS:
            cat = 'other-org-credit'
        else: continue
        found.append((r, c, v, k, cat))
cat_cnt = collections.Counter(f[4] for f in found); print(cat_cnt)

# Reporters-tab impact: a reporter is a name in Author 1..9; stories counted from Original rows only (HANDOFF)
orig_stories = collections.defaultdict(set); orig_outlets = collections.defaultdict(collections.Counter); all_rows = collections.Counter()
for r in R:
    for c in AC:
        v = s(r[c])
        if not v: continue
        all_rows[v] += 1
        if r['Original or reprint'] == 'Original':
            orig_stories[v].add(s(r['Story ID'])); orig_outlets[v][s(r['Outlet'])] += 1
try:
    rep_json = json.load(open(ROOT + '/code/reporters.json')); rep_keys = {A.author_key(k) for k in (rep_json if isinstance(rep_json, dict) else [x.get('name', '') for x in rep_json])}
except Exception: rep_keys = set()

props = []; amb = []; per_name = collections.defaultdict(lambda: dict(cells=0, rows=set(), cat=''))
for r, c, v, k, cat in found:
    if cat == 'own-outlet':
        later = [s(r[x]) for x in AC[AC.index(c) + 1:] if s(r[x])]
        conf = 'medium' if (k in SOFT or r['Medium'] in ('Newsletter or blog', 'Trade press')) else 'high'
        ev = f"Outlet \"{s(r['Outlet'])}\", Publisher \"{s(r['Publisher'])}\", Author / byline \"{s(r['Author / byline'])}\": the cell repeats the outlet name, not a person or a group of people" + ('; later authors shift left: ' + '; '.join(later) if later else '')
        props.append(dict(tab='Coverage', article_id=aid(r), column=c, current=v, new='', confidence=conf, evidence=ev))
        d = per_name[v]; d['cells'] += 1; d['rows'].add(aid(r)); d['cat'] = cat
    elif cat in ('wire-own', 'other-org-credit'):
        amb.append(dict(category=cat, article_id=aid(r), original=r['Original or reprint'], outlet=s(r['Outlet']), publisher=s(r['Publisher']), column=c, author=v, byline=s(r['Author / byline'])))
with open(OUT + '/proposals.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['tab', 'article_id', 'column', 'current', 'new', 'confidence', 'evidence']); w.writeheader(); w.writerows(props)
with open(OUT + '/ambiguous.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['category', 'article_id', 'original', 'outlet', 'publisher', 'column', 'author', 'byline']); w.writeheader(); w.writerows(amb)
with open(OUT + '/reporters_impact.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Author cell', 'category', 'cells to clear', 'rows (all)', 'Original stories (what Reporters tab shows)', 'outlets (Originals)', 'in reporters.json'])
    for v, d in sorted(per_name.items(), key=lambda x: -x[1]['cells']):
        w.writerow([v, d['cat'], d['cells'], all_rows[v], len(orig_stories[v]), '; '.join(f'{o} ({n})' for o, n in orig_outlets[v].most_common(3)), A.author_key(v) in rep_keys])
print(len(props), 'cells to clear in', len({p['article_id'] for p in props}), 'rows;', collections.Counter(p['confidence'] for p in props))
print('ambiguous', collections.Counter((a['category'], a['author']) for a in amb).most_common(30))
print('keep: staff/board cells', cat_cnt['group-staff-or-board'], 'person', cat_cnt['person-is-outlet'])
