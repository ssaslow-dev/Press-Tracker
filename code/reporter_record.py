"""reporter_record.py - REPREC-v1 / REPAFF-v1: one record per reporter (code/reporters.json, like outlets.json) and THE affiliation
engine (DECISIONS V23Q, v23-int 2026-10-29; designer work/tmp_v23_rep_design + auditor work/tmp_v23_rep_audit). The Reporters tab
reads its per-story answers from the tab-reporters block (build/tabs/reporters_data.py calls affiliations()); reporters.py
(sheet_task / Update button originals order) reads the web tenures of reporters.json and applies rules A and D in home().
v23-int changes to the designer's builder: rule B window -1..+14 days and a same-day tie rule (auditor); rule C also counts byline
credits to the service and the service list gains Zenger / CBM Newswire / Tribune Content Agency (auditor); distributor rows
(relation none) count under the person's nearest staff outlet; contributor relation (Sammy: op-ed-only people = "Contributor")
= opinion section or a contributor / columnist / guest / civic title, unless the title is a staff one (staff / editor / writer / reporter); web tenures come from
reporters.json "web" (reporter_employment.csv folded in; dated rows only win, undated ones are kept as notes).

build(rows, tenure_csv) -> {key: record}
  rows: Coverage rows as dicts (Article ID, Story ID, Original or reprint, Date, Outlet, Outlet city, Author 1..9,
        Author / byline, Author title, Section, Headline, Press release, _hidden).
Identity: author_key() (authorsplit) + author_canon.csv + the extra merges in ALIAS below (credit glued to the name:
  "Sharon Udasin, JTA", "Marisa Kendall • CalMatters", truncations). One person = one key; aliases list every surface form.
Affiliation (per Original row, the row's unit = svc_key(outlet key)):
  A  chain siblings: an Original at a sibling paper of the same house (outlet type 'chain') while the person has more
     Originals at another paper of that house within +-365 days -> counts under that paper ("ran_in", not an employer)
  B  edited re-run (AFFIL-v1 a): same person, an outlet with fewer stories, dated -1..+7 days after a story of theirs at a
     bigger outlet with a similar headline -> counts under the bigger outlet
  C  service tenure (AFFIL-v1 b): a person whose top unit is a wire / originating service: their stories at a smaller
     non-service outlet inside the service tenure (+-14 days) -> the service
  D  one-off: after A-C, a single story at an outlet while another outlet has >= 2 of their stories within +-365 days ->
     relation 'contributor' (shown as "also wrote for"), not an employer. Author title / section that says contributor /
     opinion / special to -> 'contributor' as well.
  Credits: a byline or title naming a service next to the person (reporters.credits_in) -> that service, weight 3.
Tenures: per employer unit, first..last evidence date, counts; reporter_employment.csv web rows win (source 'web');
  'freelance' there = no employer. home(rec, date) -> the tenure covering the date, else the nearest within 540 days.
Flags (needs_lookup): overlap (two employers interleaved), move (>= 2 tenures), network (chain siblings only, no clear
  home paper), freelance-pattern (>= 3 houses, none with >= 3 stories), common-name (two clusters > 3 years apart)."""
import re, csv, os, sys, json, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reprint_rule as RR
import reporters as REP
from authorsplit import author_key, author_kind, fold

TODAY = datetime.date.today()
RECORD = os.path.join(HERE, 'reporters.json')
RERUN_WIN = (-1, 14)   # rule B (auditor: 7 -> 14 days)
SPAN = 540
WIRE_RX = re.compile(r'calmatters|associated press|^ap$|center square|\bupi\b|religion news service|edsource|kff health news|kaiser health news|cronkite news|'
                     r'jewish telegraphic agency|\bjta\b|city news service|bay city news|yonhap|newsis|china news service|armenpress|mynewsla|jewish news syndicate|^jns\b|'
                     r'capital (?:&|and) main|states newsroom|stateline|^cnn wire|cnn newsource|california black media|courthouse news|reuters|bloomberg|'
                     r'zenger|cbm newswire|tribune content agency', re.I)
STAFF_TITLE = re.compile(r'staff|editor|writer|reporter|correspondent|bureau|chief', re.I)
CONTRIB_TITLE = re.compile(r'contributor|contributing|special to|especial para|guest|columnist|columnista|opinion|op-ed|commentary|freelance|'
                           r'president|ceo|founder|director|executive|professor|attorney|rabbi|assemblymember|senator|mayor|council', re.I)
OPINION_SEC = re.compile(r'opinion|opinión|commentary|comment|editorial|op-ed|letters|readers', re.I)
HL_STOP = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'what', 'will', 'into', 'over', 'after', 'about', 'their', 'here', 'have', 'says', 'said', 'more', 'than', 'they', 'are', 'how', 'why', 'new'}
# identity merges beyond author_key + author_canon.csv (credit glued to the name, truncation, nickname at the same outlet)
ALIAS = {
    'sharon udasin jta': 'sharon udasin', 'sharon udasin/ jta': 'sharon udasin',
    'marisa kendall calmatters': 'marisa kendall', 'mikhail zinshteyn calmatters': 'mikhail zinshteyn',
    'yue stella yu calmatters': 'yue stella yu', 'alexei koseff calmatters': 'alexei koseff', 'tran nguyen associated press': 'tran nguyen',
    'chris nichols capradio': 'chris nichols', 'alexander nieves': 'alex nieves', 'lucia walinchus thayer': 'lucia walinchus',
    'elissa einho': 'elissa einhorn', 'gabriel lorenzo greschler': 'gabriel greschler',
}
NOT_PEOPLE = {'jesse gabriel', 'cnn newsource', 'associated press spanish', 'calmatters', 'cnn', 'newtalk', 'the vanguard at berkeley',
              'vanguard court watch interns', 'california alcohol policy alliance', 'la nacion', 'redaccion/adelante valle', 'rick sterling marcy winograd'}


def s(v): return '' if v is None or (isinstance(v, float)) else str(v).strip()


def canon_map():
    m = {}
    p = os.path.join(HERE, 'author_canon.csv')
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding='utf-8')):
            for k in r['key'].split(' ~ '):
                m[k.strip()] = author_key(r['canonical'])
    return m


def person_key(name, canon):
    k = author_key(name)
    k = canon.get(k, k)
    return ALIAS.get(k, k)


def hl_words(t):
    return {w for w in re.sub(r'[^a-z0-9 ]+', ' ', fold(t).lower()).split() if len(w) >= 3 and w not in HL_STOP}


def similar_hl(a, b):
    A, B = hl_words(a), hl_words(b)
    if not A or not B:
        return False
    o = len(A & B)
    return o >= 2 and o / max(1, min(len(A), len(B))) >= 0.4


def unit_of(row):
    ok = RR.row_key(row)
    return REP.svc_key(ok)


def house_of(ok):
    t = RR.TYPE_TABLE.get(ok)
    return (t[1] or '') if t else ''


def type_of(ok):
    t = RR.TYPE_TABLE.get(ok)
    return t[0] if t else ''


def disp(o):
    o = s(o); m = re.match(r'^(.*), (The|La|El|Los|Las|Le|Les)$', o)
    return f'{m.group(2)} {m.group(1)}' if m else o


def load_web(path=None):
    """web tenure rows by person key: reporters.json "web" (else the legacy reporter_employment.csv)"""
    out = collections.defaultdict(list)
    path = path or RECORD
    if path.endswith('.json') and os.path.exists(path):
        for r in json.load(open(path, encoding='utf-8')).get('web', []):
            out[r['key']].append(r)
        return out
    path = path if path.endswith('.csv') else os.path.join(HERE, 'reporter_employment.csv')
    if not os.path.exists(path):
        return out
    for r in csv.DictReader(open(path, encoding='utf-8')):
        if (r.get('source') or '').startswith('sheet'):
            continue
        out[r['key']].append(r)
    return out


def build(rows, web=None, top=None):
    canon = canon_map()
    web = load_web() if web is None else web
    P = collections.defaultdict(lambda: {'forms': collections.Counter(), 'orig': [], 'rep': [], 'titles': collections.Counter()})
    for r in rows:
        st = s(r.get('Original or reprint'))
        if st not in ('Original', 'Reprint'):
            continue
        if s(r.get('_hidden')) in ('1', 'True', 'true') or s(r.get('Press release')).lower() == 'yes':
            continue
        names = [s(r.get(f'Author {i}')) for i in range(1, 10)]
        names = [a for a in names if a]
        for a in names:
            if author_kind(a) != 'person':
                continue
            k = person_key(a, canon)
            if k in NOT_PEOPLE:
                continue
            P[k]['forms'][a] += 1
            (P[k]['orig'] if st == 'Original' else P[k]['rep']).append(r)
            t = s(r.get('Author title'))
            if t and st == 'Original' and len(names) == 1:
                P[k]['titles'][t] += 1
    recs = {}
    for k, p in P.items():
        recs[k] = record(k, p, web.get(k, []))
    if top:
        order = sorted(recs, key=lambda k: (-len(P[k]['orig']), -(len(P[k]['orig']) + len(P[k]['rep'])), k))
        keep = set(order[:top]) | set(web)
        recs = {k: v for k, v in recs.items() if k in keep}
    return recs


def _tie_wins(f, e, ev):
    """rule B same-day tie at equal counts (auditor): the outlet whose house is the person's most-used house, else the
    alphabetically first outlet key (deterministic)"""
    hs = collections.Counter(x['house'] or x['unit'] for x in ev if x['relation'] == 'staff')
    hf, he = hs[f['house'] or f['unit']], hs[e['house'] or e['unit']]
    return hf > he or (hf == he and f['unit'] < e['unit'])


def record(k, p, webrows):
    name = max(p['forms'].items(), key=lambda x: (x[1], len(x[0])))[0]
    ev = []   # per Original row: dict(date, aid, unit, okey, house, otype, relation, hl, why)
    for r in p['orig']:
        d = RR.todate(r.get('Date'))
        if not d:
            continue
        ok = RR.row_key(r); u = unit_of(r)
        rel = 'staff'
        t = s(r.get('Author title')); sec = s(r.get('Section'))
        if (CONTRIB_TITLE.search(t) and not STAFF_TITLE.search(t)) or (OPINION_SEC.search(sec) and not STAFF_TITLE.search(t)):
            rel = 'contributor'
        if type_of(ok) in RR.NEVER_ORIGINAL:
            rel = 'none'
        ev.append(dict(date=d, aid=s(r.get('Article ID')), unit=u, okey=ok, house=house_of(ok), otype=type_of(ok), relation=rel, hl=s(r.get('Headline')), why=''))

    credits = []
    for r in p['orig'] + p['rep']:
        d = RR.todate(r.get('Date'))
        for c in REP.credits_in(r):
            credits.append(dict(date=d, aid=s(r.get('Article ID')), unit=c))
    n = collections.Counter(e['unit'] for e in ev if e['relation'] == 'staff')
    ran_in = collections.Counter()
    # A: chain siblings of the same house
    for e in ev:
        if e['relation'] != 'staff' or e['otype'] != 'chain' or not e['house']:
            continue
        sib = [(n[f['unit']], f['unit']) for f in ev if f['relation'] == 'staff' and f['house'] == e['house'] and f['unit'] != e['unit'] and abs((f['date'] - e['date']).days) <= 365]
        if sib:
            best = max(sib)
            if best[0] > n[e['unit']] or (best[0] == n[e['unit']] and e['unit'] > best[1]):
                ran_in[e['unit']] += 1; e['why'] = f'A sibling of {best[1]}'; e['unit'] = best[1]
    n = collections.Counter(e['unit'] for e in ev if e['relation'] == 'staff')
    # B: edited re-run (headline match within -1..7 days at a bigger outlet)
    for e in ev:
        if e['relation'] != 'staff' or e['why']:
            continue
        best = None
        for f in ev:
            if f is e or f['unit'] == e['unit'] or f['relation'] != 'staff':
                continue
            gap = (e['date'] - f['date']).days
            if gap < RERUN_WIN[0] or gap > RERUN_WIN[1]:
                continue
            if not (n[f['unit']] > n[e['unit']] or (n[f['unit']] == n[e['unit']] and (f['date'] < e['date'] or (
                    f['date'] == e['date'] and _tie_wins(f, e, ev))))):
                continue
            if similar_hl(e['hl'], f['hl']) and (not best or n[f['unit']] > n[best['unit']]):
                best = f
        if best:
            ran_in[e['unit']] += 1; e['why'] = f'B re-run of {best["aid"]} at {best["unit"]}'; e['unit'] = best['unit']
    n = collections.Counter(e['unit'] for e in ev if e['relation'] == 'staff')
    # C: service tenure
    cw = collections.Counter(c['unit'] for c in credits if c['date'])   # v23-int: byline credits to a service count for rule C
    wt = lambda u: n[u] + 3 * cw[u]
    wires = sorted({u for u in list(n) + list(cw) if WIRE_RX.search(u)}, key=lambda u: (-wt(u), u))
    if wires:
        w = wires[0]; ds = [e['date'] for e in ev if e['unit'] == w and e['relation'] == 'staff'] + [c['date'] for c in credits if c['unit'] == w and c['date']]
        d0, d1 = min(ds) - datetime.timedelta(14), max(ds) + datetime.timedelta(14)
        for e in ev:
            if e['relation'] != 'staff' or e['why'] or WIRE_RX.search(e['unit']) or n[e['unit']] >= wt(w) or not (d0 <= e['date'] <= d1):
                continue
            ran_in[e['unit']] += 1; e['why'] = f'C inside {w} tenure'; e['unit'] = w
    n = collections.Counter(e['unit'] for e in ev if e['relation'] == 'staff')
    # D: one-off beside a dominant outlet -> contributor
    for e in ev:
        if e['relation'] != 'staff' or e['why'] or n[e['unit']] > 1:
            continue
        near = collections.Counter(f['unit'] for f in ev if f['relation'] == 'staff' and f['unit'] != e['unit'] and abs((f['date'] - e['date']).days) <= 365)
        if near and near.most_common(1)[0][1] >= 2:
            e['relation'] = 'contributor'; e['why'] = f'D one story beside {near.most_common(1)[0][0]}'
    # v23-int: a distributor / aggregator row (relation none) counts under the person's top staff outlet within +-365 days
    n = collections.Counter(e['unit'] for e in ev if e['relation'] == 'staff')
    for e in ev:
        if e['relation'] != 'none':
            continue
        near = collections.Counter(f['unit'] for f in ev if f['relation'] == 'staff' and abs((f['date'] - e['date']).days) <= 365)
        if near:
            u = sorted(near.items(), key=lambda x: (-x[1], x[0]))[0][0]
            ran_in[e['unit']] += 1; e['why'] = f'N distributor run of {u}'; e['unit'] = u; e['relation'] = 'staff'
    # credits
    for c in credits:
        if c['date']:
            ev.append(dict(date=c['date'], aid=c['aid'], unit=c['unit'], okey=c['unit'], house=house_of(c['unit']), otype=type_of(c['unit']), relation='staff', hl='', why='credit', weight=3))
    # tenures from the sheet
    ten = []
    for u in sorted({e['unit'] for e in ev if e['relation'] == 'staff'}):
        xs = [e for e in ev if e['unit'] == u and e['relation'] == 'staff']
        ds = sorted(e['date'] for e in xs)
        ten.append(dict(outlet=disp(RR.canonical_name(u)) if hasattr(RR, 'canonical_name') else u, key=u, house=house_of(u),
                        **{'from': ds[0].isoformat(), 'to': ds[-1].isoformat()},
                        originals=sum(1 for e in xs if e['why'] != 'credit'), credits=sum(1 for e in xs if e['why'] == 'credit'),
                        weight=sum(e.get('weight', 1) for e in xs), reassigned=sum(1 for e in xs if e['why'] and e['why'] != 'credit'),
                        source='sheet', source_url='', confidence='high' if len(xs) >= 3 else 'medium' if len(xs) == 2 else 'low'))
    ten.sort(key=lambda t: t['from'])
    contrib = collections.Counter(e['unit'] for e in ev if e['relation'] == 'contributor')
    # web rows win
    webt = []
    for r in webrows:
        o = r['outlet']
        webt.append(dict(outlet=o, key='freelance' if o == 'freelance' else (r.get('outlet_key') or RR.outlet_key(o)),
                         house=house_of(RR.outlet_key(o)) if o != 'freelance' else '',
                         **{'from': r.get('from', ''), 'to': r.get('to', '')}, originals=0, credits=0, weight=99, reassigned=0,
                         source=r.get('source', 'web'), source_url=r.get('source_url', ''), confidence=r.get('confidence') or 'verified',
                         complete=bool(r.get('complete', True))))
    flags = []
    staff_t = [t for t in ten if t['weight'] >= 2]
    if len(staff_t) >= 2:
        flags.append('move')
        for a in staff_t:
            for b in staff_t:
                if a is not b and a['from'] < b['from'] < a['to'] and b['to'] > a['from'] and a['originals'] >= 2 and b['originals'] >= 2:
                    flags.append('overlap'); break
    if ran_in and not any(e['why'].startswith('B') or e['why'].startswith('C') for e in ev) and not staff_t:
        flags.append('network')
    hs = collections.Counter(e['house'] or e['unit'] for e in ev if e['relation'] in ('staff', 'contributor'))
    if len(hs) >= 3 and max(hs.values()) < 3:
        flags.append('freelance-pattern')
    ds = sorted(e['date'] for e in ev)
    if len(staff_t) >= 2 and any((datetime.date.fromisoformat(b['from']) - datetime.date.fromisoformat(a['to'])).days > 3 * 365 for a, b in zip(staff_t, staff_t[1:])):
        flags.append('common-name?')
    return {
        'name': name, 'name_src': 'sheet majority', 'kind': 'person',
        'aliases': sorted(a for a in p['forms'] if a != name),
        'alias_keys': sorted({author_key(a) for a in p['forms']} - {k}),
        'employment': webt + ten,
        'freelance': any(t['key'] == 'freelance' for t in webt),
        'contributed_to': [{'key': u, 'stories': c} for u, c in contrib.most_common()],
        'ran_in': [{'key': u, 'stories': c} for u, c in ran_in.most_common()],
        'titles': [t for t, _ in p['titles'].most_common(3)],
        'rows_seen': len(p['orig']) + len(p['rep']), 'originals_seen': len(p['orig']),
        'first': ds[0].isoformat() if ds else '', 'last': ds[-1].isoformat() if ds else '',
        'needs_lookup': ', '.join(dict.fromkeys(flags)),
        'decided_by': 'web' if webt else 'rule', 'decided_at': TODAY.isoformat(), 'note': '',
        'contributor': bool(ev) and all(e['relation'] == 'contributor' for e in ev if e['why'] != 'credit'),
        '_ev': [dict(aid=e['aid'], date=e['date'].isoformat(), unit=e['unit'], relation=e['relation'], why=e['why']) for e in ev],
    }


def home(rec, date, span=SPAN):
    """the employer unit on a date: a web tenure covering it; else the sheet tenure covering it; else the nearest sheet
    tenure within `span` days (weight >= 2); None = freelance / unknown"""
    if not date:
        return None
    web = [t for t in rec['employment'] if t['source'] != 'sheet' and (t.get('complete', True) or t['from'])]
    for t in web:
        a = RR.todate(t['from']) or datetime.date(1990, 1, 1); b = RR.todate(t['to']) or datetime.date(2099, 1, 1)
        if a <= date <= b:
            return None if t['key'] == 'freelance' else {'key': t['key'], 'why': f"web-verified tenure ({t['source_url']})", 'weight': 99}
    if any(t.get('complete', True) for t in web):
        return None
    best = None
    for t in rec['employment']:
        if t['weight'] < 2 or t['source'] != 'sheet':   # web rows were handled above (an undated note is never a tenure)
            continue
        # v23-int fix (coordinator): an empty from / to is open-ended, never a ValueError
        a = RR.todate(t.get('from')) or datetime.date(1990, 1, 1); b = RR.todate(t.get('to')) or datetime.date(2099, 1, 1)
        gap = 0 if a <= date <= b else min(abs((date - a).days), abs((date - b).days))
        if gap > span:
            continue
        if not best or gap < best[0] or (gap == best[0] and t['weight'] > best[1]['weight']):
            best = (gap, t)
    if not best:
        return None
    return {'key': best[1]['key'], 'why': f"{rec['name']}: {best[1]['originals']} Original bylines / {best[1]['credits']} credits at {best[1]['key']} {best[1]['from']}..{best[1]['to']}", 'weight': best[1]['weight']}


def write_record(recs, web, path=RECORD, top=300):
    """reporters.json: {"version", "built", "web": [web tenure rows], "records": {key: record}} (top N people by Originals + every
    person with a web row; the per-row evidence _ev is not stored)"""
    order = sorted(recs, key=lambda k: (-recs[k]['originals_seen'], -recs[k]['rows_seen'], k))
    keep = set(order[:top]) | {r['key'] for r in web}
    out = {'version': 'REPREC-v1', 'built': TODAY.isoformat(),
           'note': 'One record per person key (author_key + author_canon.csv). web = researched tenures (dated rows win over the sheet in '
                   'reporters.py home(); complete=false rows only cover their own span; undated rows are notes). employment = web rows + '
                   'sheet tenures; ran_in = outlets that carried their Originals (rules A-C, distributor runs); contributed_to = one-off '
                   'outlets and opinion pieces ("Also wrote for"); contributor = every story of theirs is an opinion / guest piece.',
           'web': web, 'records': {k: {kk: vv for kk, vv in recs[k].items() if kk != '_ev'} for k in sorted(recs) if k in keep}}
    json.dump(out, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, sort_keys=False)
    return out


def coverage_rows(cov):
    """Coverage DataFrame -> row dicts for build()"""
    cols = [c for c in cov.columns]
    return [dict(zip(cols, (None if (isinstance(v, float) and v != v) else v for v in vals))) for vals in cov.itertuples(index=False)]


if __name__ == '__main__':
    # python3 reporter_record.py --write   (rebuilds reporters.json "records" from the shared data; keeps "web")
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--write', action='store_true'); ap.add_argument('--top', type=int, default=300)
    a = ap.parse_args()
    from shared_data import load as _load
    web = json.load(open(RECORD, encoding='utf-8')).get('web', []) if os.path.exists(RECORD) else []
    wk = collections.defaultdict(list)
    for r in web:
        wk[r['key']].append(r)
    recs = build(coverage_rows(_load().coverage), web=wk)
    if a.write:
        out = write_record(recs, web, top=a.top)
        print(len(out['records']), 'records,', len(web), 'web rows ->', RECORD)
    else:
        print(len(recs), 'people')
