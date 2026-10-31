"""reporters.py - the reporter's employer on the story date (REPRINT-v2 tier 1 of the originals order; Sammy 2026-10-28:
"use reporter data to find the original outlet"). Shared by sheet_task (Update button), the regroup tooling and the tracker's
Reporters tab (AFFIL-v1 done once).

Evidence per (person, row) of the Coverage sheet:
  * explicit credit: the byline / Author title names an outlet or service next to the person ("Adam Beam, Associated Press",
    "Yue Stella Yu | CalMatters", "Karen Garcia; Los Angeles Times"): weight 3 for that outlet;
  * own-outlet byline: the person is on the byline of an ORIGINAL row at outlet X: weight 1 per story (aggregator /
    distributor / PR-service rows and rows whose byline credits another outlet give no evidence);
  * reprint byline: weight 0 (a reprint outlet is never an employer, AFFIL-v1).
home(person, date): the outlet (key) with the most weight within +-540 days of the date; None when the best weight < 2 or tied.
Web-verified tenures (reporter_employment.csv next to this script: from/to dates, source URL) win over sheet counts;
'freelance' rows mean no home at all (Ryan Torok). Hub stories (Scripps / Nexstar) go to the reporter's home station because
the station's own Originals carry the byline.

The rule only RANKS rows inside a grouping that text or credit already established; it never creates a grouping."""
import re, csv, os, sys, json, collections, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reprint_rule as RR
try:
    from authorsplit import author_key, TITLE_RX, EDITORIAL_RX
except Exception:   # minimal fallbacks (the pipeline ships authorsplit.py next to this file)
    TITLE_RX = re.compile(r'\b(staff|writer|reporter|editor|correspondent|columnist|contributor|bureau|chief)\b', re.I)
    EDITORIAL_RX = re.compile(r'editorial (?:board|staff|team)', re.I)

    def author_key(name):
        return ' '.join(re.sub(r'[^\w\s]', ' ', str(name or '').lower()).split())

SPAN_DAYS = 540
MIN_WEIGHT = 2
TENURE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reporter_employment.csv')   # legacy (folded into reporters.json)
RECORD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reporters.json')   # v23-REPREC: the reporter record ("web" tenures)
PARTIAL = set()   # v23-REPREC: person keys whose web rows are all partial (lookups covering only their own span): outside it the sheet decides
NOT_PERSON = re.compile(r'editorial|staff|news|press|service|wire|desk|team|report|bureau|association|office|\bllp\b|inc\.?$|group|network|media|'
                        r'radio|\btv\b|newsroom|times$|journal$|digest|\.com|@|gabriel|contributed|correspondent|newsource|^cnn|^calmatters|^associated press|nacion$|vanguard|interns$|alliance$|foundation$', re.I)   # v23-REPNOTPERSON
# outlet / service names that appear as credits next to a person (byline or Author title) -> outlet key
CREDIT_SVC = [(k, re.compile(rx, re.I)) for k, rx in [
    ('associated press', r'associated press|\bAP\b'), ('calmatters', r'calmatters'), ('city news service', r'city news service|\bCNS\b|mynewsla'),
    ('bay city news', r'bay city news'), ('los angeles times', r'los angeles times|\bL\.?A\.? Times'), ('sacramento bee', r'sacramento bee'),
    ('san francisco chronicle', r'san francisco chronicle|\bchronicle\b'), ('jewish telegraphic agency', r'jewish telegraphic|\bJTA\b'),
    ('jns', r'\bJNS\b|jewish news syndicate'), ('kff health news', r'kff health|kaiser health|california healthline'), ('edsource', r'edsource'),
    ('center square', r'center square'), ('states newsroom', r'states newsroom|stateline'), ('capital & main', r'capital (?:&|and) main'),
    ('cnn', r'\bCNN\b'), ('reuters', r'reuters'), ('bloomberg', r'bloomberg'), ('politico', r'politico'),
    ('new york times', r'new york times'), ('washington post', r'washington post'), ('usa today', r'usa today'),
    ('orange county register', r'orange county register|\bOC Register'), ('mercury news', r'mercury news'), ('east bay times', r'east bay times'),
    ('courthouse news service', r'courthouse news'), ('kqed', r'\bKQED\b'), ('laist', r'\bLAist\b|\bKPCC\b'), ('capradio', r'capradio|capital public radio'),
    ('npr', r'\bNPR\b'), ('hill', r'\bthe hill\b'), ('newsnation', r'newsnation'), ('scripps news', r'scripps news'), ('ktla', r'\bKTLA\b'),
    ('upi', r'\bUPI\b'), ('religion news service', r'religion news service'), ('cronkite news', r'cronkite news'), ('propublica', r'propublica'),
    ('forward', r'\bthe forward\b'), ('times of israel', r'times of israel'), ('jewish journal', r'jewish journal'), ('press democrat', r'press democrat'),
    ('fresno bee', r'fresno bee'), ('modesto bee', r'modesto bee'), ('san diego union tribune', r'union-tribune'), ('desert sun', r'desert sun'),
    ('voice of san diego', r'voice of san diego'), ('inewsource', r'inewsource'), ('san francisco standard', r'sf standard|san francisco standard'),
    ('healthday', r'healthday'), ('california black media', r'california black media'), ('washington examiner', r'washington examiner'),
    ('verify', r'\bVERIFY\b'), ('business insider', r'business insider'), ('cool down', r'the cool down'),
]]
HOUSE_WORDS = re.compile(r'southern california news group|\bSCNG\b|bay area news group|\bBANG\b|mcclatchy|medianews|tribune news service|\bTNS\b', re.I)


def is_person(a):
    a = str(a or '').strip()
    if not a or len(a.split()) < 2 or len(a) > 40:
        return False
    if NOT_PERSON.search(a) or TITLE_RX.search(a) or EDITORIAL_RX.search(a):
        return False
    return bool(re.search(r'[A-Za-zÀ-ÿ]', a))


def people_of(row):
    """[(author key, name)] of a row: Author 1..9, else the people of the free byline"""
    out = []
    for i in range(1, 10):
        a = str(row.get(f'Author {i}') or '').strip()
        if a and is_person(a):
            out.append((author_key(a), a))
    if not out:
        for p in RR.people(row.get('Author / byline')):
            if is_person(p):
                out.append((author_key(p), p))
    return out


def credits_in(row):
    """outlet keys credited next to the byline (Author / byline + Author title), excluding the row's own outlet and house names"""
    txt = ' '.join(str(row.get(k) or '') for k in ('Author / byline', 'Author title'))
    own = RR.row_key(row)
    out = []
    for k, rx in CREDIT_SVC:
        if rx.search(txt) and k not in own and not (k == 'hill' and 'hill' in own):
            out.append(k)
    return out


def svc_key(okey):
    """fold an outlet key to its service / house key when one matches (AP feeds, KFF / California Healthline, CNS / MyNewsLA)"""
    sv = RR.service_of_outlet('', okey)
    if sv:
        return RR.outlet_key(sv) if not sv.startswith('STATION:') else sv[8:].lower()
    return okey


_RECORDS = {}


def record_of(k):
    """CHAINORIG-v1: the person's record in reporters.json "records" (the v23 reporter record, REPREC-v1), {} when absent"""
    if not _RECORDS:
        try:
            _RECORDS.update(json.load(open(RECORD_FILE, encoding='utf-8')).get('records', {}))
        except Exception:
            _RECORDS['_none'] = {}
    return _RECORDS.get(k) or {}


CENTRAL_TYPES = frozenset({'national', 'wire', 'network'})   # a central / national desk: USA TODAY, AP, ...


def central_missing(rows, home):
    """CHAINORIG-v1 (originals order v2 step 3): the reporter's employer on the story date is a central / national desk
    (outlet type national / wire / network) with NO row in the story, while the story's rows are chain / network papers of the
    desk's house or other redistributors -> {key, house, type}: the originator is missing, so the Original choice must NOT fall
    to a local sibling; the caller proposes an originator-add (fetch the desk's page, else a no-copy row, NOCOPY-v2).
    rows: dicts of the story (Outlet, ...). home: reporter home ({key,...} or key)."""
    hk = home if isinstance(home, str) else (home or {}).get('key', '')
    t = RR.TYPE_TABLE.get(hk) if hk else None
    if not t or t[0] not in CENTRAL_TYPES:
        return None
    hs = RR.service_of_outlet('', hk)
    for r in rows:
        k = RR.row_key(r)
        if k == hk or (hs and RR.service_of_outlet(r.get('Outlet'), k) == hs):
            return None
    house = t[1]
    probe = {'Outlet': hk, '_okey': hk, '_house': house}
    if not any(RR.row_type(r) in RR.REDISTRIBUTOR or (house and RR.same_house(r, probe)) for r in rows):
        return None
    return {'key': hk, 'house': house, 'type': t[0]}


def never_employer(okey):
    """AGGORIGIN-v1: an aggregator / distributor / PR service is never a reporter's employer (the type table decides)"""
    t = RR.TYPE_TABLE.get(okey) if okey and okey != 'freelance' else None
    return bool(t and t[0] in RR.NEVER_ORIGINAL)


def load_tenure(path=None):
    """web-verified tenures: key -> [(outlet key, from date, to date, source url)]; 'freelance' = no home.
    v23-REPREC: read from reporters.json "web" (reporter_employment.csv folded in); a row marked complete=false (a lookup) counts
    only when dated and only over its span; undated lookup rows are notes. Falls back to the csv when reporters.json is missing."""
    out = collections.defaultdict(list)
    if path is None:
        path = RECORD_FILE if os.path.exists(RECORD_FILE) else TENURE_FILE
    if path.endswith('.json'):
        full = set()
        for r in json.load(open(path, encoding='utf-8')).get('web', []):
            if not r.get('complete', True) and not r.get('from'):
                continue
            k = r.get('key') or author_key(r.get('name', ''))
            if r.get('complete', True):
                full.add(k)
            a = RR.todate(r.get('from')) or datetime.date(1990, 1, 1)
            b = RR.todate(r.get('to')) or datetime.date(2099, 1, 1)
            ok_ = RR.outlet_key(r.get('outlet', '')) if r.get('outlet') != 'freelance' else 'freelance'
            if never_employer(ok_):   # AGGORIGIN-v1
                continue
            out[k].append((ok_, a, b, r.get('source_url', '')))
        PARTIAL.clear(); PARTIAL.update(set(out) - full)
        return out
    if not os.path.exists(path):
        return out
    for r in csv.DictReader(open(path, encoding='utf-8')):
        if (r.get('source') or '').startswith('sheet'):
            continue
        k = r.get('key') or author_key(r.get('name', ''))
        a = RR.todate(r.get('from')) or datetime.date(1990, 1, 1)
        b = RR.todate(r.get('to')) or datetime.date(2099, 1, 1)
        out[k].append((RR.outlet_key(r.get('outlet', '')) if r.get('outlet') != 'freelance' else 'freelance', a, b, r.get('source_url', '')))
    return out


class Employment:
    """reporter -> employer evidence from the Coverage rows (dicts with Original or reprint, Date, Outlet, Outlet city, Author 1..9,
    Author / byline, Author title, Article ID; optional _otype / _okey)."""

    def __init__(self, rows=(), tenure=None):
        self.ev = collections.defaultdict(list)   # person key -> [(date, outlet key, weight, kind, aid)]
        self.names = {}
        self.tenure = tenure if tenure is not None else load_tenure()
        for r in rows:
            self.add(r)

    def add(self, r):
        st = str(r.get('Original or reprint') or '')
        if st not in ('Original', 'Reprint'):
            return
        d = RR.todate(r.get('Date'))
        ok = RR.row_key(r)
        typ = RR.row_type(r)
        ppl = people_of(r)
        cr = credits_in(r)
        cr = [c for c in cr if not never_employer(c)]   # AGGORIGIN-v1
        for k, name in ppl:
            self.names.setdefault(k, name)
            for c in cr:
                self.ev[k].append((d, c, 3, 'credit', r.get('Article ID', '')))
            if st == 'Original' and not cr and typ not in RR.NEVER_ORIGINAL:
                self.ev[k].append((d, svc_key(ok), 1, 'original byline', r.get('Article ID', '')))
            elif st == 'Original':
                pass   # an Original whose byline credits another outlet is no evidence for its own outlet
            else:
                self.ev[k].append((d, svc_key(ok), 0, 'reprint byline', r.get('Article ID', '')))

    def tenure_home(self, k, d):
        for o, a, b, src in self.tenure.get(k, []):
            if d and a <= d <= b:
                return o, src
        return None, ''

    def home(self, k, date=None, span=SPAN_DAYS):
        """{'key', 'weight', 'second', 'why'} or None (freelance / no evidence / tie)"""
        t, src = self.tenure_home(k, date)
        if t == 'freelance':
            return None
        if t and never_employer(t):   # AGGORIGIN-v1
            t = None
        if t:
            return {'key': t, 'weight': 99, 'second': 0, 'why': f'{self.names.get(k, k)}: web-verified tenure ({src})'}
        if k in self.tenure and k not in PARTIAL:   # a known mover outside every tenure span: the sheet counts would be circular
            return None
        rec = record_of(k)   # CHAINORIG-v1: the v23 reporter record (reporters.json "records")
        if rec and rec.get('contributor'):
            return None      # every story of theirs is an opinion / guest piece: no employer
        w = collections.Counter()
        evs = [(d, o, wt, kind, aid) for d, o, wt, kind, aid in (self.ev.get(k) or []) if not (date and d and abs((d - date).days) > span)]
        evs = self._pool(evs)   # v23-REPRULES
        for d, o, wt, kind, aid in evs:
            w[o] += wt
        if not w:
            return None
        for o_ in [x for x in w if never_employer(x)]:   # AGGORIGIN-v1: never an aggregator
            del w[o_]
        if not w:
            return None
        o, wt = w.most_common(1)[0]
        second = w.most_common(2)[1][1] if len(w) > 1 else 0
        if wt < MIN_WEIGHT or wt <= second:
            return None
        return {'key': o, 'weight': wt, 'second': second, 'why': f"{self.names.get(k, k)}: {wt} Original bylines / credits at {o} within 18 months"}

    def _pool(self, evs):
        """# v23-REPRULES rule A: Originals at sibling papers of one house (type 'chain') pool under the house paper with the most
        of this person's Originals; rule D: a lone Original at an outlet beside >= 2 at another outlet within +-365 days is a
        contribution (weight 0). Credits (weight 3) are left alone."""
        by_house = collections.defaultdict(collections.Counter)
        for d, o, wt, kind, aid in evs:
            if kind == 'original byline':
                t = RR.TYPE_TABLE.get(o)
                if t and t[0] == 'chain' and t[1]:
                    by_house[t[1]][o] += 1
        out = []
        for d, o, wt, kind, aid in evs:
            if kind == 'original byline':
                t = RR.TYPE_TABLE.get(o)
                if t and t[0] == 'chain' and t[1] and len(by_house[t[1]]) > 1:
                    top = max(by_house[t[1]].items(), key=lambda x: (x[1], x[0] == o, x[0]))[0]
                    if top != o:
                        out.append((d, top, wt, 'original byline (sibling of ' + o + ')', aid)); continue
            out.append((d, o, wt, kind, aid))
        n = collections.Counter(o for d, o, wt, kind, aid in out if kind.startswith('original byline'))
        res = []
        for d, o, wt, kind, aid in out:
            if kind.startswith('original byline') and n[o] == 1 and d:
                near = collections.Counter(o2 for d2, o2, w2, k2, a2 in out if k2.startswith('original byline') and o2 != o and d2 and abs((d2 - d).days) <= 365)
                if near and near.most_common(1)[0][1] >= 2:
                    res.append((d, o, 0, 'contribution (one story beside ' + near.most_common(1)[0][0] + ')', aid)); continue
            res.append((d, o, wt, kind, aid))
        return res

    def is_freelance(self, k, d=None):
        return self.tenure_home(k, d)[0] == 'freelance'

    def home_rec(self, row):
        """(home outlet key or None, evidence, weight) for a row's byline people at the row's date; a byline that credits an outlet wins;
        weight 99 = web-verified tenure"""
        d = RR.todate(row.get('Date'))
        txt = ' '.join(str(row.get(k) or '') for k in ('Author / byline', 'Author title'))
        if re.search(r'california black media', txt, re.I):
            return 'california black media', 'byline credits California Black Media', 99
        for k, name in people_of(row):
            if self.is_freelance(k, d):
                return None, f'{name}: freelance, no single home', 0
            h = self.home(k, d)
            if h:
                return h['key'], h['why'], h['weight']
        return None, '', 0

    def home_of(self, row):
        """(home outlet key or None, evidence)"""
        k, why, _ = self.home_rec(row)
        return k, why

    def story_home(self, rows, current=None):
        """the reporter home over a story: the current Original's byline first, then any row's -> {'key','why','house','weight'} or None"""
        order = ([current] if current is not None else []) + [r for r in rows if r is not current]
        for r in order:
            k, why, w = self.home_rec(r)
            if k:
                return {'key': k, 'why': why, 'weight': w, 'house': RR.TYPE_TABLE.get(k, ['', ''])[1] if k in RR.TYPE_TABLE else ''}
        return None

    def table(self):
        """sheet-derived rows for reporter_employment.csv / the Reporters tab: name, key, outlet, from, to, weight, stories, credits"""
        rows = []
        for k, evs in self.ev.items():
            by = collections.defaultdict(list)
            for d, o, wt, kind, aid in evs:
                if wt > 0:
                    by[o].append((d, wt, kind, aid))
            for o, xs in by.items():
                ds = [d for d, *_ in xs if d]
                rows.append({'name': self.names.get(k, k), 'key': k, 'outlet': o, 'from': min(ds).isoformat() if ds else '', 'to': max(ds).isoformat() if ds else '',
                             'weight': sum(w for _, w, *_ in xs), 'stories': sum(1 for x in xs if str(x[2]).startswith('original byline')),
                             'credits': sum(1 for x in xs if x[2] == 'credit'), 'source': 'sheet (Original bylines + byline credits)', 'source_url': ''})
        return sorted(rows, key=lambda r: (r['name'], -r['weight']))


def from_sheet(sheet):
    """Employment built from a sheet_task.Sheet (openpyxl) - the Update button's view of the Coverage tab"""
    cols = ('Article ID', 'Original or reprint', 'Date', 'Outlet', 'Outlet city', 'Medium', 'Publisher', 'Language', 'Author / byline', 'Author title') + tuple(f'Author {i}' for i in range(1, 10))
    E = Employment()
    for r in range(2, sheet.last_row + 1):
        st = sheet.get(r, 'Original or reprint')
        if st not in ('Original', 'Reprint'):
            continue
        E.add({c: sheet.get(r, c) for c in cols if c in sheet.col})
    return E
