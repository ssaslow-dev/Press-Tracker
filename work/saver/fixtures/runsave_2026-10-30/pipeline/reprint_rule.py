"""reprint_rule.py - the string-of-text reprint rule as one shared module (agent-code, 2026-10-27).

Same rule as the approved regroup (work/tmp_agent-regroup2/regroup_v2.py, DECISIONS 2026-10-27 "regroup by long streaks
of matching text"): two texts are the same story when runs of >= 25 identical consecutive words (>= 40 characters for
Chinese/Japanese/Korean, counted by character) cover >= 90% of BOTH texts. Tokens: NFKC, hyphenated words joined (also
across line breaks, "-\\n\\n"), apostrophes and in-number periods/commas dropped, accents folded, lowercase; CJK one token
per character. NewsBank clutter (the logged patterns) and photo captions count when matched and are ignored when
unmatched (low/medium confidence); unmatched leading/trailing lines of <= 120 words each end (<= 30% together) may be set
aside (edge pass: low confidence). No text on either side: headline + author rule (same headline and same people).

Used by sheet_task.py for new finds: a find whose text passes against an existing Original (date within +-90 days -
REPRINT90-v1, Sammy 2026-10-27 - headline words overlapping) is a Reprint of that story; the no-text fallback (same
headline + same people) and the OCR near-miss link keep the +-7-day window; the originals order (releases, aggregators, reprint-list rows
never first; then wire/originating service, own byline, earlier date, NewsBank over web, web over print) only reports a
find that would rank before the existing Original (the sheet's existing cells are never changed).

REPRINT-v2 (reprint-code, 2026-10-28; build/REPRINT_PLAN.md): one outlet-type table (outlet_rules.json "types" + "services")
replaces the WIRE / AGG / CREDIT / SERVICES lists; originals order v2 = eligibility (unverified never; releases, aggregators,
distributors, PR services, uncredited reprint-list rows) -> credited service (ORIGINCREDIT + RSS / Original Location /
Copyright / station-dateline forms) -> the reporter's employer on the story date (reporters.py; ranks inside a grouping only)
-> originator-type outlet -> own byline -> date (never a same-house date-only swap). pair_class() holds the matrix cells:
AV <-> text and AV <-> AV are never reprints (second platform / re-air = an edition), same outlet = an edition (Web + Print),
wire <-> wire never (own distributor only), containment (a credited text >= 90% inside the longer) = Reprint, a translation
= Reprint when credited and <= 2 days. candidates() prefilters by type pair. copy_mismatch() is the wrong-copy guard.
"""
import datetime, re, unicodedata

THR = 0.90
# HIDEUNVERIFIED-v1 (Sammy decision 2026-10-28, rp-final): Coverage rows whose "Original or reprint" is "Reprint (unverified)" are
# hidden from the tracker everywhere (reprint lists, outlet / reporter pages, Story travel, counts, maps, CSVs, search). They stay in
# the sheet and in the Update button's dedupe index (rows block), so a run never re-adds them. ONE predicate for every builder.
UNVERIFIED = 'Reprint (unverified)'
def is_unverified(v):
    return str(v if v is not None else '').strip().lower() == UNVERIFIED.lower()
def hide_unverified(df):
    """the Coverage frame without "Reprint (unverified)" rows (unchanged when the column is missing)"""
    col = 'Original or reprint'
    if df is None or col not in getattr(df, 'columns', []): return df
    return df[~df[col].map(is_unverified)]
MINW = 50
WINDOW_DAYS = 7          # headline + people fallback and OCR near-miss link (no text match)
TEXT_WINDOW_DAYS = 90    # REPRINT90-v1: candidates for the string-of-text test (Sammy 2026-10-27)
CJK = re.compile('[぀-ヿ㐀-䶿一-鿿豈-﫿가-힯ᄀ-ᇿ㄰-㆏]')
TOK = re.compile('[぀-ヿ㐀-䶿一-鿿豈-﫿가-힯ᄀ-ᇿ㄰-㆏]|[^\\W_]+')


def norm_tokens(s):
    s = unicodedata.normalize('NFKC', s or '')
    s = s.replace('­', '')
    s = re.sub(r'(?<=\w)[-‐‑]\s*(?=\w)', '', s)       # hyphenated words, incl. line-break hyphens "-\n\n"
    s = re.sub(r"(?<=\w)['’ʼ](?=\w)", '', s)
    s = re.sub(r'(?<=\w)[.,](?=\w)', '', s)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = unicodedata.normalize('NFC', s).lower()
    return TOK.findall(s)


def is_cjk(toks):
    if not toks:
        return False
    return sum(1 for t in toks if len(t) == 1 and CJK.match(t)) / len(toks) >= 0.5


# NewsBank / wire clutter (the regroup's logged patterns): counted when matched, ignored when unmatched
STRIP_RULES = [
    ('calmatters_legislators', re.compile(r'Learn more about legislators mentioned in this story\.?(?:\s*\n+\s*[^\n]{0,120}?(?:Democrat|Republican|Independent),\s*(?:State\s+)?(?:Assembly|Senate)[^\n]{0,60}?\([^)\n]{0,40}\))*', re.I)),
    ('calmatters_newsletter', re.compile(r'(?:\d\.\s*)?Just the right amount of news(?:\s*\d\.\s*Just the right amount of news)?(?:\s*\d\.\s*Get California.s most essential headlines without feeling overwhelmed\.?)*(?:\s*\n+\s*\d\.\s*Get California.s most essential headlines without feeling overwhelmed\.?)*', re.I)),
    ('photo_caption_jpg', re.compile(r'(?:^[^\n.]{0,25}\s[-:]\s*)?\S*\.(?:jpe?g|JPE?G)(?:[^\n.!?]{0,400}[.!?]?)', re.M)),
    ('related_articles_box', re.compile(r'Related Articles\b[^\n]*', re.I)),
    ('html_tag', re.compile(r'</?[a-zA-Z][^<>\n]{0,400}>')),
    ('share_widget', re.compile(r'\b(?:Share this(?: article| story)?:?|Click to share on \w+|Share on (?:Facebook|Twitter|X|LinkedIn|WhatsApp|Email)|(?:(?:Facebook|Twitter|X|Instagram|TikTok|YouTube|WhatsApp|LinkedIn|Email|Print|Reddit|Pinterest|Flipboard)[,\s]+){3,}(?:Facebook|Twitter|X|Instagram|TikTok|YouTube|WhatsApp|LinkedIn|Email|Print|Reddit|Pinterest|Flipboard)\b)', re.I)),
    ('wire_contact', re.compile(r'^\s*(?:MEDIA\s+)?CONTACTO?S?\s*:(?:[^\n"“]*(?:@[\w.-]+|\(?\d{3}\)?[-. ]\s?\d{3}[-.]?\d{4}|\d{3}-\d{7}|\d{7,})|[^\n"“]{0,150}$)', re.M | re.I)),
    ('wire_hashes', re.compile(r'(?<!\S)#{3}(?!\S)')),
    ('wire_immediate', re.compile(r'\bFOR IMMEDIATE RELEASE\b:?', re.I)),
    ('wire_tns_category', re.compile(r'\((?:News Release|Press Release); [^)\n]{0,400}\)')),
    ('wire_tns_query', re.compile(r'For any query with respect to this article[^\n]*', re.I)),
    ('wire_tns_leadin', re.compile(r'^[^\n]{0,160}\[Category:[^\]\n]*\][^\n]{0,200}?(?:posted|issued|released|published) the following[^:\n]{0,120}:\s*(?:\*{3})?', re.M)),
    ('calmatters_language_link', re.compile(r'Lea esta historia en espa[ñn]ol|Read this story in English', re.I)),
    ('calmatters_member_box', re.compile(r'(?:\d\.\s*)?Become a CalMatters member today[^.\n]*\.?')),
    ('calmatters_signup_box', re.compile(r'Stay up-to-date with free briefings on topics that matter to all Californians\.\s*Subscribe to CalMatters today for nonprofit news in your inbox\.?'
        r'|Be prepared for California.s general election: Sign up for our election newsletter[^.\n]*\.?'
        r'|Sign up for WeeklyMatters[^.\n]*\.?'
        r'|(?:Keeping up with your California representatives felt impossible before\.\s*)?(?:Now you can watch them like a hawk:\s*)?Sign up for My Legislator[^.\n]*\.?'
        r'|Subscribe to CalMatters newsletters here\.?'
        r'|Sign up for (?:our|their) [^.\n]{0,40}newsletters?[^.\n]{0,120}\.?')),
    ('wire_syndigate', re.compile(r'Provided by SyndiGate Media Inc\.?\s*\(Syndigate\.info\)\.?', re.I)),
]


def _segments(text):
    spans = []
    for name, rx in STRIP_RULES:
        for m in rx.finditer(text):
            if m.group(0).strip():
                spans.append((m.start(), m.end()))
    spans.sort()
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    segs, pos = [], 0
    for a, b in merged:
        if a > pos:
            segs.append((text[pos:a], False))
        segs.append((text[a:b], True))
        pos = b
    if pos < len(text):
        segs.append((text[pos:], False))
    return segs


def version(text, kind='html', label=''):
    """kind 'nb' (NewsBank/wire text: clutter patterns flagged) or 'html' (cleaned page text; captions marked with
    \\x01...\\x02 are flagged)."""
    raw, mask = [], []
    if kind == 'nb':
        for seg, fl in _segments(text):
            tk = norm_tokens(seg)
            raw += tk
            mask += [fl] * len(tk)
    else:
        depth = 0
        for part in re.split('([\x01\x02])', text or ''):
            if part == '\x01':
                depth += 1
                continue
            if part == '\x02':
                depth = max(0, depth - 1)
                continue
            tk = norm_tokens(part)
            raw += tk
            mask += [depth > 0] * len(tk)
    return {'label': label, 'raw': raw, 'mask': mask, 'strip': [t for t, f in zip(raw, mask) if not f]}


def html_text(html):
    """Text of a cleaned page for the rule (as the regroup read the library): header lines, title and the h1 before
    the article start are dropped; photo captions flagged; NewsBank text copies ("Text of the NewsBank PDF") read as
    NewsBank text. Returns (text, kind)."""
    from bs4 import BeautifulSoup
    s = BeautifulSoup(html or '', 'html.parser')
    nb = bool(s.find(class_='jg-pdf-text'))
    title = s.title.get_text(' ', strip=True) if s.title else ''
    if s.title:
        s.title.decompose()
    for t in s(['script', 'style', 'noscript', 'img', 'svg', 'head']):
        t.decompose()
    if nb:
        for p in s.find_all(class_='pdf-cap'):
            p.decompose()
        if s.h1:
            s.h1.decompose()
        for p in s.find_all(class_='byline'):
            p.decompose()
        return '\n\n'.join(p.get_text(' ', strip=True) for p in s.find_all('p')), 'nb'
    for fc in s.find_all('figcaption'):
        fc.insert(0, '\x01')
        fc.append('\x02')
    lines = [re.sub(r'\s+', ' ', l).strip() for l in s.get_text('\n').split('\n')]
    lines = [l for l in lines if l]
    h1 = s.h1.get_text(' ', strip=True) if s.h1 else ''
    keep, started = [], False
    for l in lines:
        hdr = (re.fullmatch(r'Saved \d{4}-\d{2}-\d{2}.*', l) or re.match(r'Text of the ProQuest PDF', l)
               or re.match(r'Print edition: pages?', l) or (title and l == title) or (h1 and l == h1)
               or re.match(r'^.{1,140} · (\d{4}(-\d\d){0,2}|undated)$', l) or re.match(r'^https?://\S+$', l))
        if hdr and not started:
            continue
        if len(l.split()) >= 12:
            started = True
        keep.append(l)
    return '\n'.join(keep), 'html'


# ---------------- coverage ----------------
def _cov(a, b, k, key):
    ta, tb = a[key], b[key]
    hb = {tuple(tb[i:i + k]) for i in range(len(tb) - k + 1)}
    n = len(ta)
    diff = [0] * (n + 1)
    for i in range(n - k + 1):
        if tuple(ta[i:i + k]) in hb:
            diff[i] += 1
            diff[i + k] -= 1
    cov, c = [], 0
    for i in range(n):
        c += diff[i]
        cov.append(c > 0)
    return cov


def measure(va, vb):
    """coverage of both texts: raw, clutter-aware, edge (lines set aside); k = 25 words / 40 CJK characters"""
    k = 40 if (is_cjk(va['raw']) or is_cjk(vb['raw'])) else 25
    if len(va['raw']) < k or len(vb['raw']) < k:
        return None
    ca, cb = _cov(va, vb, k, 'raw'), _cov(vb, va, k, 'raw')
    raw = (sum(ca) / len(ca), sum(cb) / len(cb))

    def masked(cov, mask):
        den = sum(1 for c, m in zip(cov, mask) if c or not m)
        return sum(cov) / den if den else 0.0
    m1 = (masked(ca, va['mask']), masked(cb, vb['mask']))
    if len(va['strip']) >= k and len(vb['strip']) >= k and (any(va['mask']) or any(vb['mask'])):
        sa = _cov({'x': va['strip']}, {'x': vb['strip']}, k, 'x')
        sb = _cov({'x': vb['strip']}, {'x': va['strip']}, k, 'x')
        m2 = (sum(sa) / max(1, len(sa)), sum(sb) / max(1, len(sb)))
    else:
        m2 = (0, 0)
    clut = m1 if min(m1) >= min(m2) else m2

    def edge(cov, v):
        n = len(cov)
        L = 0
        while L < n and not cov[L]:
            L += 1
        Tn = 0
        while Tn < n - L and not cov[n - 1 - Tn]:
            Tn += 1
        ign, drop = [], 0
        cap = 400 if k == 40 else 120
        if 0 < L <= cap:
            drop += L
            ign.append(('leading', ' '.join(v['raw'][:L])))
        if 0 < Tn <= cap:
            drop += Tn
            ign.append(('trailing', ' '.join(v['raw'][n - Tn:])))
        if drop > 0.3 * n or n - drop <= 0:
            return sum(cov) / n, []
        lo = L if 0 < L <= cap else 0
        hi = n - (Tn if 0 < Tn <= cap else 0)
        flag_unm = sum(1 for i in range(lo, hi) if v['mask'][i] and not cov[i])
        den = n - drop - flag_unm
        return (sum(cov) / den if den > 0 else 0.0), ign
    ea, ia = edge(ca, va)
    eb, ib = edge(cb, vb)
    return {'raw': raw, 'clut': clut, 'edge': (ea, eb), 'edge_ign': ia + ib, 'k': k, 'n': (len(va['raw']), len(vb['raw']))}   # WIREBLEND-v1: n = token counts


def text_verdict(va_list, vb_list):
    """best pair of versions -> None (no usable text) or dict(ok, conf, mode, m)"""
    best = None
    for va in va_list:
        for vb in vb_list:
            if len(va['raw']) < MINW or len(vb['raw']) < MINW:
                continue
            m = measure(va, vb)
            if m is None:
                continue
            sc = (min(m['raw']) >= THR, min(m['clut']) >= THR, min(m['edge']) >= THR, min(m['raw']), min(m['clut']))
            if best is None or sc > best[0]:
                best = (sc, m)
    if best is None:
        return None
    m = best[1]
    if min(m['raw']) >= THR:
        return {'ok': True, 'conf': 'high', 'mode': 'text', 'm': m}
    if min(m['clut']) >= THR:
        return {'ok': True, 'conf': 'low', 'mode': 'text-clutter', 'm': m}
    if min(m['edge']) >= THR:
        return {'ok': True, 'conf': 'low', 'mode': 'text-edge', 'm': m}
    return {'ok': False, 'conf': 'medium' if max(min(m['raw']), min(m['clut']), min(m['edge'])) >= 0.85 else 'high',
            'mode': 'text', 'm': m}


# ---------------- headline + author ----------------
def nh(h):
    h = unicodedata.normalize('NFKC', h or '').lower()
    h = re.sub('[‘’“”\'"`]', '', h)
    h = re.sub(r'[^\w\s]', ' ', h)
    return ' '.join(h.split())


TITLE_W = re.compile(r'\b(staff|writers?|correspondents?|reporters?|editors?|columnists?|contributors?|special to|bureau chief|chief|news service|columnista|redacci\w*)\b', re.I)


def people(by):
    by = (by or '').split(';')[0]
    by = re.sub(r'^\s*by\s+', '', by, flags=re.I)
    out = set()
    for p in re.split(r',|\band\b|&|/|\by\b', by):
        p = p.strip()
        if p and not TITLE_W.search(p) and nh(p):
            out.add(nh(p))
    return frozenset(out)


def headline_author(a, b):
    """a, b: dicts with Headline, Author / byline (and Date). REPRINT90-v1: dated more than WINDOW_DAYS apart -> not the
    same story by this fallback (only a text match links across up to TEXT_WINDOW_DAYS)"""
    da, db = todate(a.get('Date')), todate(b.get('Date'))
    if da and db and abs((da - db).days) > WINDOW_DAYS:
        return {'ok': False, 'verifiable': True, 'why': 'out of the 7-day window for headline + author'}
    ha, hb = nh(a.get('Headline')), nh(b.get('Headline'))
    pa, pb = people(a.get('Author / byline')), people(b.get('Author / byline'))
    if not ha or not hb or not pa or not pb:
        return {'ok': False, 'verifiable': False}
    return {'ok': ha == hb and pa == pb, 'verifiable': True}


# ---------------- candidates + originals order ----------------
STOP = set('a an the of to in on for and or with at by from as is are be was were it its that this new over after before about into out up says say said will can could would should not no ca calif california state bill law gabriel jesse assembly assemblymember'.split())


def hwords(h):
    return {w for w in nh(h).split() if w not in STOP and len(w) > 2}


def todate(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v if isinstance(v, datetime.date) and not isinstance(v, datetime.datetime) else v.date()
    m = re.match(r'(\d{4})-(\d\d)-(\d\d)', str(v or ''))
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def headline_overlap(a, b):
    wa, wb = hwords(a), hwords(b)
    sh = len(wa & wb)
    return sh >= 3 or (sh >= 2 and sh / max(1, len(wa | wb)) >= 0.5)


def onorm(o):
    o = (o or '').lower()
    o = re.sub(r"today's edition|: blogs|\bthe\b|[^\w\s]", ' ', o)
    return ' '.join(o.split())


# ================= REPRINT-v2 (reprint-code, 2026-10-28; build/REPRINT_PLAN.md, Sammy's 4 answers) =================
# One outlet-type table (outlet_rules.json "types": key -> [type, house]) replaces the WIRE / AGG / CREDIT / SERVICES hand
# lists. The originating services an ORIGINCREDIT credit can name live in outlet_rules.json "services". The table is read
# from the JSON next to this script; an outlet missing from it is classified by classify_outlet() (name / Medium /
# publisher rules ported from the reprint-logic scheme) and sheet_task lists it (outlet_untyped).
import json as _json, os as _os

TYPES = ['wire', 'nonprofit', 'prservice', 'aggregator', 'distributor', 'chain', 'independent', 'station', 'network', 'podcast', 'magazine', 'blog',
         'trade', 'institution', 'foreign', 'national', 'other']
NEVER_ORIGINAL = frozenset({'aggregator', 'prservice', 'distributor'})   # never the Original while another eligible row exists
ORIGINATOR = frozenset({'wire', 'nonprofit', 'national', 'network'})      # originator-type outlets (tier 2)
REDISTRIBUTOR = frozenset({'aggregator', 'distributor', 'station', 'chain', 'foreign'})   # type-pair prefilter: tested against every originator
TRANSLATION_DAYS = 2
SIBLING_DAYS = 7


def _load_rules():
    for p in (_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'outlet_rules.json'),):
        try:
            return _json.load(open(p, encoding='utf-8'))
        except (OSError, ValueError):
            pass
    return {}


RULES = _load_rules()
TYPE_TABLE = RULES.get('types') or {}
AV_ITEMS = frozenset(RULES.get('av_items') or ['Broadcast segment', 'Episode', 'Video clip'])
BLOCKED_HOSTS = tuple(RULES.get('blocked_hosts') or ())
HOUSE_CREDITS = tuple(RULES.get('house_credits') or ())
STATION_CALLS = {k.upper(): v for k, v in (RULES.get('station_calls') or {}).items()}   # call letters -> outlet key

# SERVICES: (canonical, outlet-key regex, credit regex, case-sensitive credit). From the JSON; the v1 list is the fallback.
_SERVICES_V1 = [
    ('CalMatters', r'calmatters', r'calmatters', False),
    ('Associated Press', r'associated press|^ap$|^ap ', r'associated press|\(AP\)', False),
    ('The Center Square', r'center square', r'center square', False),
    ('States Newsroom', r'states newsroom|stateline', r'states newsroom|stateline', False),
    ('CNN', r'^cnn\b', r'CNN Wire|CNN Newsource|\(CNN\)', True),
    ('KFF Health News', r'kff health news|kaiser health news', r'kff health news|kaiser health news', False),
    ('EdSource', r'edsource', r'edsource', False),
    ('Jewish Telegraphic Agency', r'jewish telegraphic|^jta\b', r'jewish telegraphic agency|\bJTA\b', True),
    ('City News Service', r'(?<!bay )city news service|mynewsla', r'(?<!bay )city news service(?!,\s*b\.)|mynewsla', False),
    ('Bay City News', r'bay city news|local news matters', r'bay city news|city news service,\s*b\.', False),
    ('Capital & Main', r'capital (?:&|and) main', r'capital (?:&|and) main', False),
    ('Los Angeles Times', r'^los angeles times', r'los angeles times', False),
    ('Religion News Service', r'religion news service', r'religion news service', False),
    ('Cronkite News', r'cronkite news', r'cronkite news', False),
    ('UPI', r'\bupi\b|united press international', r'\bUPI\b|united press international', True),
    ('Jewish News Syndicate', r'jewish news syndicate|^jns\b', r'jewish news syndicate|\bJNS\b', True),
    ('Courthouse News Service', r'courthouse news', r'courthouse news', False),
    ('Yonhap', r'yonhap', r'yonhap', False),
]
SERVICES = [(n, v['outlet'], v['credit'], bool(v.get('cs'))) for n, v in (RULES.get('services') or {}).items()] or _SERVICES_V1
_SVC_RX = {n: (re.compile(ro, re.I), re.compile(rc, 0 if cs else re.I)) for n, ro, rc, cs in SERVICES}


def _norm_outlet_fn():
    """sheet_task.norm_outlet when it can be imported (same folder), else a minimal normalizer with the JSON feeds/aliases"""
    try:
        from sheet_task import norm_outlet as f
        return f
    except Exception:
        pass
    R = RULES

    def f(s, city=''):
        s = unicodedata.normalize('NFKD', str(s or '').replace('’', "'")).encode('ascii', 'ignore').decode().lower().strip()
        s = re.sub(r"\s*:\s*blogs\s*$", '', s)
        s = re.sub(r"\s*\(?\btoday'?s edition\b\)?", '', s)
        s = re.sub(r",\s*the(?=\s*(?::|/|$))", '', s)
        s = re.sub(r"^the\s+", '', s.strip())
        b = re.sub(r'[^a-z0-9]+', ' ', s).strip()
        for pre, key in (R.get('feeds') or {}).items():
            if b == pre or b.startswith(pre + ' '):
                return key
        k = b
        if b in set(R.get('generic_needs_city') or ()):
            c = re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', str(city or '')).encode('ascii', 'ignore').decode().lower()).strip()
            if c:
                k = b + '@' + c
        return (R.get('aliases') or {}).get(k, k)
    return f


_NORM = None


def outlet_key(outlet, city=''):
    global _NORM
    if _NORM is None:
        _NORM = _norm_outlet_fn()
    return _NORM(outlet, city)


# --- rule classifier for outlets not in the table (ported from work/tmp_reprintlogic/otype.py; overrides live in the table) ---
_RX = lambda s: re.compile(s, re.I)
_T_PRSERVICE = _RX(r"pr newswire|prnewswire|business wire|businesswire|globenewswire|globe newswire|targeted news service|us fed news|u\.s\. fed news|publicnow|"
                   r"public now|enp newswire|m2 presswire|m2 pharma|contify|tendersinfo|plus media|plusmedia|us official news|hispanic pr|u\.s\. newswire|us newswire|"
                   r"accesswire|einpresswire|ein presswire|newsfile|prweb|pr web|marketscreener|news bites|impact news service|states news service|ascribe|newsrx|"
                   r"^press release|presswire|openpr|newswire$|newswires$")
_T_AGG = _RX(r"^yahoo|^msn\b|^aol\b|newsbreak|newstex|syndigate|^sohu|^nate\b|nate news|^daum|^naver|^google news|flipboard|smartnews|ground news|^bing\b|headtopics|"
             r"head topics|newsnow|pressreader|^muckrack|^feedspot|^opera news|^upday|^inkl|^apple news|aboluowang|^newser|^drudge|^realclearpolitics|^rawstory|^raw story|"
             r"^mixed times|^news\s*break|california local news|dnyuz|ce noticias|^latam\b|news from the states|crispy news|\[your\]news")
_T_DISTRIB = _RX(r"tca (?:news|regional)|tribune content agency|tribune news service|u-wire|university wire")
_T_WIRE = _RX(r"associated press|^ap\b|^ap:|city news service|bay city news|local news matters|mynewsla|jewish telegraphic|^jta\b|\bupi\b|united press|cnn wire|"
              r"cnn newsource|yonhap|newsis|china news service|armenpress|jns\b|jewish news syndicate|^reuters|bloomberg news|efe\b|agencia|^dpa\b|^afp\b|"
              r"religion news service|news service$|newsource|^wire\b|catholic news agency|^ani\b|cronkite news|healthday|california black media")
_T_NONPROFIT = _RX(r"calmatters|edsource|kff health|kaiser health|california healthline|capital (?:&|and) main|courthouse news|propublica|chalkbeat|the markup|"
                   r"the 19th|inewsource|voice of (?:san diego|oc)|the trace|grist|high country news|civil eats|the appeal|bolts|states newsroom|stateline|"
                   r"center square|san jose spotlight|stocktonia|new lede|calo news|the conversation")
_T_NETWORK = _RX(r"^(?:cnn|fox news|fox business|nbc news|cbs news|abc news|npr|pbs(?: newshour)?|msnbc|cnbc|c-span|telemundo|noticias telemundo|univision(?: noticias)?|"
                 r"newsmax|bbc(?: news)?|al jazeera|bloomberg(?: tv)?|scripps news|newsnation|verify|the national desk|spectrum news(?: 1)?|newsy|one america|oan|cbc(?: radio)?|sky news)\b")
_T_PODCAST = _RX(r"podcast|^(?:the )?[\w' ]+ show$|commune|pro bono happy hour|connectopod")
_T_MAGAZINE = _RX(r"newsweek|\bmagazine\b|new yorker|the atlantic|\btime\b|rolling stone|vanity fair|lamag|los angeles magazine|food & wine|consumer reports|\bmag$|forbes|fortune|"
                  r"the nation$|national review|reason|the american prospect|jacobin|the week\b|variety|hollywood reporter|billboard|esquire|mother jones|the economist|sunset")
_T_BLOG = _RX(r"playbook|daily kos|knock la|citywatch|la progressive|bearing arms|substack|blog|newsletter|medium\.com|cool down|one green planet|county politics|huffpost|"
              r"breitbart|daily caller|daily wire|the federalist|townhall|redstate|hotair|pj media|free beacon|the blaze|gateway pundit|salon|slate|vox\b|axios|semafor|puck|"
              r"the bulwark|common dreams|truthout|alternet|nationofchange|the intercept|the defender|palisadian|patch$|nextdoor|reddit|streetsblog|curbed|urbanize|"
              r"yo! venice|westside today|hoodline|davis vanguard|california globe")
_T_TRADE = _RX(r"food safety|agri-pulse|mondaq|politico pro|state affairs|bloomberg law|law\.com|the recorder|daily journal$|national law review|food(?:navigator|service|dive| business| processing)|"
               r"supply side|baking business|meat\+poultry|new hope|guns\.com|shooting news|bond buyer|government technology|govtech|governing|capitol weekly|inside (?:cal )?epa|insideepa|"
               r"climate extra|business journal|jd supra|lexology|law360|ammoland|nutraingredients|progressive grocer|restaurant|realtor|housing wire|bisnow|the real deal|"
               r"ed ?week|education week|inside higher ed|modern healthcare|fierce|medpage|pharma|biospace|endpoints|regulatory focus|utility dive|canary media|e&e|ag ?alert|"
               r"american banker|coindesk|techcrunch|the verge|ars technica|cnet|zdnet|venturebeat|gizmodo|engadget|adweek|ad age|digiday|prweek|legal|lawyer|attorney|"
               r"biz ?journal|crain|\btrade\b|nonprofit quarterly|chronicle of philanthropy|jewish insider|ejewishphilanthropy|tax notes|govexec|route fifty|pluribus|hr dive|labor notes|lawfare|abasto")
_T_INSTITUTION = _RX(r"university|college|\bucla\b|\bucsd\b|\bucsf\b|\bcsun\b|\busc\b|berkeley|stanford|newsroom|\.edu\b|\.gov\b|city of |county of |department|caucus|governor|"
                     r"attorney general|district attorney|office of|association|council|coalition|foundation|institute|center for|federation|league|chamber of commerce|union|alliance|"
                     r"committee|campaign|action fund|environmental voters|consumers association|sierra club|aclu|\badl\b|anti-defamation|jewish federation|hillel|aipac|j street|jpac|ballotpedia|codepink")
_T_FOREIGN = _RX(r"el pa[ií]s|infobae|naci[oó]n, la|clar[ií]n|sing tao|world journal|epoch times|\bntd\b|sound of hope|korea daily|korea times|chosun|joongang|hankyoreh|nguoi|viet bao|"
                 r"jerusalem post|times of israel|haaretz|arutz sheva|israel national news|israel hayom|ynet|hebrew news|world israel news|independent, the|the independent|daily mail|mailonline|"
                 r"guardian|\bbbc\b|telegraph, the|le monde|figaro|spiegel|el mundo|mundo, el|la vanguardia|exc[eé]lsior|reforma|milenio|el universal|globo|folha|xinhua|cctv|global times|"
                 r"south china morning|al jazeera|asharq|armenpress|azatutyun|mirror-spectator|asbarez|hetq|news\.am|iranwire|radio farda|kayhan|vinetur|la opini[oó]n|opinion, la|"
                 r"la raza|impremedia|toronto|montreal|vancouver|globe and mail|national post|india times|hindustan|times of india|ndtv|philippine|inquirer|rappler|manila|asian journal|"
                 r"straits times|japan times|asahi|yomiuri|nikkei|nhk|notimex|prensa latina|el nuevo herald|diario|peri[oó]dico|noticias|jewishpostandnews|ctvnews|jewish chronicle")
_T_NATIONAL = _RX(r"new york times|washington post|los angeles times|wall street journal|usa today|new york post|washington times|the hill|hill, the|^politico$|boston globe|"
                  r"philadelphia inquirer|miami herald|dallas morning|star tribune|atlanta journal|detroit free|daily beast|buzzfeed|roll call|the daily|business insider|"
                  r"washington examiner|financial times|marketwatch|barron|usnews|u\.s\. news|^stat$|the dispatch|the free press|deseret")
_T_CHAIN_PUB = _RX(r"southern california news group|bay area news group|medianews|digital first|alden|mcclatchy|lee enterprises|hearst|gannett|times-journal|santa maria news media|"
                   r"tribune publishing|nexstar|sinclair|tegna|scripps|gray television|news corp|advance local|cnhi|adams publishing|ogden|paxton|boone|wick communications|"
                   r"sound publishing|wehco|imperial valley news media|san fernando valley sun|feather publishing|weeklys|cleveland jewish publi|clarity media|aim media|dmg media|"
                   r"axel springer|nant capital|sonoma media|times-shamrock|shaw media|forum communications|cox media|graham media|audacy|iheart|cumulus|salem media|entercom|patch media")
_T_CHAIN_NAME = _RX(r"orange county register|press-enterprise|daily breeze|press-telegram|daily news$|daily bulletin|star-news|whittier daily|san gabriel valley tribune|redlands daily facts|"
                    r"sun, the|mercury news|east bay times|marin independent|lake county record|santa cruz sentinel|monterey county herald|times-standard|times-herald|ukiah daily|"
                    r"daily democrat|enterprise-record|red bluff daily|willits news|mendocino beacon|fort bragg advocate|paradise post|oroville mercury|vallejo times|sacramento bee|"
                    r"fresno bee|modesto bee|merced sun-star|san luis obispo tribune|tribune, the|napa valley register|santa maria times|lompoc record|santa ynez valley|hanford sentinel|"
                    r"desert sun|record, the|recordnet|visalia times|salinas californian|ventura county star|redding record|san francisco chronicle|sfgate|houston chronicle|"
                    r"san diego union|today's edition|daily herald|columbus dispatch|arizona republic|chicago tribune|baltimore sun|orlando sentinel|virginian-pilot|hartford courant|"
                    r"sun sentinel|morning call|tennessean|greenville news|florida today|asbury park|statesman journal|burlington free|montgomery advertiser")
_CALL = re.compile(r"\b[KW][A-Z]{2,3}\b")


def classify_outlet(outlet, medium='', publisher='', lang=''):
    """(type, how) for an outlet NOT in the table: the scheme's name / Medium / publisher rules (otype.py, 2026-10-28)"""
    o = str(outlet or '').strip()
    if not o:
        return 'other', 'blank outlet'
    m, p, lg = str(medium or ''), str(publisher or ''), str(lang or '')
    if _T_PRSERVICE.search(o):
        return 'prservice', 'name: press-release service'
    if _T_DISTRIB.search(o):
        return 'distributor', 'name: distributor'
    if _T_AGG.search(o):
        return 'aggregator', 'name: aggregator/portal'
    if m == 'Podcast' or (_T_PODCAST.search(o) and m in ('Podcast', 'Radio', '', 'Video')):
        return 'podcast', 'medium/name: podcast'
    if _T_NONPROFIT.search(o):
        return 'nonprofit', 'name: nonprofit originator'
    if _T_WIRE.search(o) or m == 'Wire':
        return 'wire', 'name/medium: wire'
    if _T_NETWORK.search(o) and m in ('TV', 'Radio', 'Online news', 'Video', ''):
        return 'network', 'name: network'
    if m in ('TV', 'Radio') or _CALL.search(o) or re.match(r'^(?:ABC|CBS|NBC|FOX|CW|PBS) ?-? ?\d', o):
        return 'station', 'medium/call letters: station'
    if m == 'Student newspaper' or (_T_INSTITUTION.search(o) and m in ('', 'Online news', 'Newsletter or blog')):
        return 'institution', 'medium/name: institution'
    if _T_NATIONAL.search(o):
        return 'national', 'name: national'
    if m == 'Trade press' or _T_TRADE.search(o):
        return 'trade', 'medium/name: trade press'
    if m == 'Magazine' or _T_MAGAZINE.search(o):
        return 'magazine', 'medium/name: magazine'
    if m == 'Newsletter or blog' or _T_BLOG.search(o):
        return 'blog', 'medium/name: blog/newsletter'
    if (lg and lg != 'English') or _T_FOREIGN.search(o):
        return 'foreign', 'language/name: non-English or foreign-based'
    if _T_CHAIN_PUB.search(p) or _T_CHAIN_NAME.search(o):
        return 'chain', 'publisher/name: chain paper'
    if m in ('Newspaper', 'Online news'):
        return 'independent', 'medium: ' + m.lower() + ', no chain'
    return 'other', 'no rule matched'


def outlet_type(outlet, city='', medium='', publisher='', lang=''):
    """-> (type, house, how). The table first (by outlet key), else the rule classifier (house from the publisher)."""
    k = outlet_key(outlet, city)
    v = TYPE_TABLE.get(k)
    if v:
        return v[0], v[1] if len(v) > 1 else '', 'table'
    t, how = classify_outlet(outlet, medium, publisher, lang)
    return t, (str(publisher or '').strip() if _T_CHAIN_PUB.search(str(publisher or '')) else ''), how


def row_type(x):
    """type of a sheet row (dict); a precomputed '_otype' wins"""
    if x.get('_otype'):
        return x['_otype']
    return outlet_type(x.get('Outlet'), x.get('Outlet city'), x.get('Medium'), x.get('Publisher'), x.get('Language'))[0]


def row_house(x):
    if '_house' in x:
        return x['_house'] or ''
    return outlet_type(x.get('Outlet'), x.get('Outlet city'), x.get('Medium'), x.get('Publisher'), x.get('Language'))[1]


def row_key(x):
    return x.get('_okey') or outlet_key(x.get('Outlet'), x.get('Outlet city'))


def same_house(a, b):
    """same outlet key, or the same publisher group (never a date-only Original swap between them)"""
    ka, kb = row_key(a), row_key(b)
    if ka and ka == kb:
        return True
    sa, sb = service_of_outlet(a.get('Outlet'), ka), service_of_outlet(b.get('Outlet'), kb)
    if sa and sa == sb:
        return True
    ha, hb = row_house(a), row_house(b)
    return bool(ha) and ha == hb


def is_av_item(x):
    """an AV tab item (Broadcast segment / Episode / Video clip) is never a reprint and never reprinted. The item type comes from
    the AV tab ('_av_item'); without it, Podcast / Video rows count as items and TV / Radio rows as web stories."""
    it = str(x.get('_av_item') or '').strip()
    if it:
        return it in AV_ITEMS
    return str(x.get('Medium') or '').strip() in ('Podcast', 'Video')


def is_blocked_host(url):
    h = re.sub(r'^https?://(www\.)?', '', str(url or '').lower()).split('/')[0]
    return any(h == b or h.endswith('.' + b) for b in BLOCKED_HOSTS)


# ---------------- ORIGINCREDIT (v1 agent-v20-origin-av; v2 credit forms, reprint-code 2026-10-28) ----------------
# A credit line / byline / NewsBank author / section / dateline that names an originating service, on ANY row of the
# story, forces that service's row first in the originals order (tier 0). v2 adds the RSS footer forms ("The post X
# appeared first on JNS.org", "first appeared on"), "Original Location: … Washington Examiner", "Copyright 2024 NPR",
# station datelines "(KTLA) —", and "produced by KFF Health News"-style lines already in v1.
CREDIT_LINE = re.compile(r"(?:originally (?:published|appeared|ran) (?:by|in|on|at)|first (?:published|appeared|ran) (?:by|in|on|at)|"
                         r"(?:appeared|published|ran) first (?:by|in|on|at)|"
                         r"republished (?:from|with permission (?:from|of))|(?:story|article|report|piece) (?:was|is) (?:produced|published|reported|written|provided) by|"
                         r"[Rr]ead the original (?:article|story|post) (?:on|at|from|in)|See at|[Rr]ead more (?:at|on)|"   # AGGORIGIN-v1: Yahoo / MSN provider lines, CNET button
                         r"distributed by|is part of|courtesy of|via)\s+(?:the\s+)?([A-Z][\w&.'’ -]{2,40}|[a-z]+\.org|[a-z]+\.com)")
ORIG_LOCATION = re.compile(r"Original Location:?\s*([^\n]{0,300})", re.I)
COPYRIGHT_SVC = re.compile(r"(?:Copyright|©)\s*(?:\(c\)\s*)?(?:\d{4}(?:\s*[-–]\s*\d{4})?\s*)?(NPR|HealthDay|Jewish Telegraphic Agency|JTA|JNS|CalMatters|The Associated Press|Associated Press)\b")
STATION_DATELINE = re.compile(r"\(((?:[KW][A-Z]{2,3}|FOX\d{1,2})(?:-TV)?)(?:\.COM)?\)\s*[—–-]")   # AGGORIGIN-v1: "(FOX40.COM) —"


def service_of_outlet(o, key=None):
    k = key if key is not None else outlet_key(o)
    for n, (ro, _) in _SVC_RX.items():
        if ro.search(k or ''):
            return n
    return None


def _station_service(call):
    """a station dateline "(KTLA) —" names the station itself as the originating service (canonical = call letters)"""
    call = call.upper().replace('-TV', '')
    return 'STATION:' + call


def service_matches_outlet(service, outlet, key=None):
    if service.startswith('STATION:'):
        k = (key if key is not None else outlet_key(outlet)) or ''
        call = service[8:]
        return k == STATION_CALLS.get(call, '') or call.lower() in k.split(' ')
    return service_of_outlet(outlet, key) == service


def credit_of(row, text=''):
    """originating services named by this row -> {service: [evidence, ...]}. Signals: byline / Author title ("X, CalMatters",
    "X | CalMatters"), the NewsBank APA author, a CalMatters section, a credit line in the text (v1 forms + the v2 RSS
    "appeared first on", "Original Location", "Copyright NPR"), an "(AP) —" / "(CNN) —" / "(KTLA) —" dateline. A row never
    credits its own outlet's service; house names (SCNG, BANG, McClatchy, TNS) are not services."""
    out = {}
    key = row_key(row)
    own = service_of_outlet(row.get('Outlet'), key)
    by = ' '.join(str(row.get(k) or '') for k in ('Author / byline', 'Author title'))
    apa = str(row.get('Newsbank APA citation (article)') or '').split('(')[0]
    sec = str(row.get('Section') or '')
    t = text or ''
    for n, (_, rc) in _SVC_RX.items():
        if rc.search(by):
            out.setdefault(n, []).append('byline: ' + by.strip()[:80])
        elif rc.search(apa):
            out.setdefault(n, []).append('NewsBank author: ' + apa.strip()[:80])
        if n == 'CalMatters' and re.search('calmatters', sec, re.I):
            out.setdefault(n, []).append('section: ' + sec[:60])
    for m in CREDIT_LINE.finditer(t):
        for n, (_, rc) in _SVC_RX.items():
            if rc.search(m.group(1)):
                out.setdefault(n, []).append('credit line: "' + m.group(0)[:90] + '"')
    for m in ORIG_LOCATION.finditer(t):
        for n, (_, rc) in _SVC_RX.items():
            if rc.search(m.group(1)):
                out.setdefault(n, []).append('Original Location: "' + m.group(1)[:90] + '"')
    for m in COPYRIGHT_SVC.finditer(t):
        for n, (_, rc) in _SVC_RX.items():
            if rc.search(m.group(1)):
                out.setdefault(n, []).append('copyright line: "' + m.group(0)[:60] + '"')
    head = t[:600]
    if re.search(r'\(AP\)\s*[—–-]', head):
        out.setdefault('Associated Press', []).append('dateline (AP)')
    if re.search(r'\(CNN\)\s*[—–-]', head):
        out.setdefault('CNN', []).append('dateline (CNN)')
    m = STATION_DATELINE.search(head)
    if m:
        sv = _station_service(m.group(1))
        if not service_matches_outlet(sv, row.get('Outlet'), key):
            out.setdefault(sv, []).append('dateline (%s)' % m.group(1))
    out.pop(own, None)
    for sv in list(out):
        if sv.startswith('STATION:') and service_matches_outlet(sv, row.get('Outlet'), key):
            out.pop(sv)
    return out


def story_credits(rows, texts=None):
    """credits over every row of a story (any row's evidence counts) -> {service: [evidence]}; texts: {id(row) or Article ID: text}"""
    texts = texts or {}
    out = {}
    for r in rows:
        tx = texts.get(r.get('Article ID')) or texts.get(id(r)) or ''
        for n, ev in credit_of(r, tx).items():
            out.setdefault(n, []).extend(f"{r.get('Article ID', '')} {r.get('Outlet', '')}: {e}" for e in ev)
    return out


def _weak(e, n):
    """evidence 'AID Outlet: byline: <text>' whose byline is only the service's name (no person)"""
    if ': byline: ' not in e or n not in _SVC_RX:
        return False
    by = e.split(': byline: ', 1)[1]
    rest = _SVC_RX[n][1].sub(' ', by)
    rest = re.sub(r'(?i)\b(the|by|and|staff|wire|reports?|news|service|from|via)\b|[^\w]', ' ', rest)
    return not rest.strip()


def origin_credits(rows, texts=None):
    """the services that rank first (tier 0) in this story -> (frozenset, {service: [evidence]}).
    - A strong credit (credit line, dateline, NewsBank author, section, or a byline naming the service next to a person) counts from any row.
    - A weak credit (byline = only the service's name, e.g. a station's "Associated Press" byline) shows who DISTRIBUTED the copy:
      it counts only when no other service has a row in the story.
    - Distribution: an AP state-wire row whose byline names the same person as another service's row credits that other service."""
    ev = story_credits(rows, texts)
    svc_rows = {}
    for r in rows:
        sv = service_of_outlet(r.get('Outlet'), row_key(r))
        if sv:
            svc_rows.setdefault(sv, []).append(r)
    out = set()
    for n, es in ev.items():
        strong = [e for e in es if not _weak(e, n)]
        if strong or not (set(svc_rows) - {n}):
            out.add(n)
    for ap in svc_rows.get('Associated Press', []):
        if not re.search(r'(?i)state wire', ap.get('Outlet') or ''):
            continue
        pa = people(ap.get('Author / byline'))
        for sv, rs in svc_rows.items():
            if sv == 'Associated Press' or not pa:
                continue
            if any(pa & people(r.get('Author / byline')) for r in rs):
                out.add(sv)
                ev.setdefault(sv, []).append(f"{ap.get('Article ID', '')} {ap.get('Outlet', '')}: AP row carries the {sv} reporter's byline")
    if 'Associated Press' in out and len(out) > 1 and not any('byline' not in e for e in ev.get('Associated Press', [])):
        out.discard('Associated Press')
    return frozenset(out), ev


def byline_credits_other(x):
    """the byline / Author title names another outlet or service (tier 5): any service credit, or a non-house outlet name"""
    return bool(credit_of(x))


# ---------------- originals order v2 ----------------
def tier(x, mostly_reprint=None, credited=frozenset(), home=None):
    """(tier, why). 0 credited originating service · 1 the reporter's employer on the story date (home = outlet key or
    {key: evidence}) · 2 originator-type outlet (wire, nonprofit, national, network) · 3 own byline · 4 no byline ·
    5 byline credits another outlet. `mostly_reprint` is accepted and ignored (retired, REPRINT-v2)."""
    o = x.get('Outlet') or ''
    key = row_key(x)
    sv = service_of_outlet(o, key)
    for c in credited or ():
        if service_matches_outlet(c, o, key):
            return 0, 'credited originating service (' + (sv or c.replace('STATION:', '')) + ')'
    if home:
        hk, hev = (home, '') if isinstance(home, str) else (home.get('key', ''), home.get('why', ''))
        if hk and (hk == key or (service_of_outlet('', hk) and service_of_outlet('', hk) == sv)):
            return 1, "reporter's employer" + (' (' + hev + ')' if hev else '')
    if credit_of(x):
        return 5, 'byline credits another outlet'
    if row_type(x) in ORIGINATOR:
        return 2, 'originating-type outlet (' + row_type(x) + ')'
    if home:
        hk = home if isinstance(home, str) else home.get('key', '')
        if hk and same_house(x, {'Outlet': hk, '_okey': hk, '_house': home.get('house', '') if isinstance(home, dict) else ''}):
            return 2, "reporter's employer's house"
    if people(x.get('Author / byline')):
        return 3, 'own byline'
    return 4, 'no byline'


def rank(x, mostly_reprint=None, credited=frozenset(), home=None):
    """originals order v2 (REPRINT-v2): eligibility (unverified never; Press release = Yes; aggregator / distributor /
    PR-service rows; reprint-list rows unless credited) → tier → earlier date → NewsBank over web → web over print."""
    if is_unverified(x.get('Original or reprint')):
        return (9, 9, datetime.date(2100, 1, 1), 1, 1)
    rel = str(x.get('Press release') or '').strip().lower() == 'yes'
    t, why = tier(x, credited=credited, home=home)
    typ = row_type(x)
    elig = 2 if rel else 3 if typ in NEVER_ORIGINAL else 4 if x.get('Data Source') == 'Tracker reprint list' and t != 0 else 0
    d = todate(x.get('Date')) or datetime.date(2100, 1, 1)
    src = 0 if x.get('Data Source') == 'Newsbank' else 1
    ed = 1 if x.get('Edition') == 'Print' else 0
    return (elig, t, d, src, ed)


def choose_original(rows, texts=None, home=None, current=None):
    """REPRINT-v2: the row that should be the Original among `rows` (dicts of one story). home: reporter home ({key, why, house}
    or key) from reporters.home_of over the story. Returns dict(best, credited, ranks, swap, why): swap is True when `current`
    (the row now marked Original) should give way — never for a same-house pair that differs on date alone."""
    cred, ev = origin_credits(rows, texts)
    ranked = sorted(rows, key=lambda r: rank(r, credited=cred, home=home))
    best = ranked[0]
    out = {'best': best, 'credited': cred, 'credit_evidence': ev, 'ranks': {r.get('Article ID', ''): rank(r, credited=cred, home=home) for r in rows},
           'swap': False, 'why': ''}
    if current is None or current is best or current.get('Article ID') == best.get('Article ID'):
        return out
    rb, rc = out['ranks'][best.get('Article ID', '')], out['ranks'][current.get('Article ID', '')]
    if rb[0] >= 9 or (rb[0] == rc[0] == 3):   # never swap one aggregator / PR-service row for another: the originator is missing
        return out
    if rb[:2] == rc[:2] and same_house(best, current):
        out['why'] = 'same house, same tier: date-only difference, no swap'
        return out
    if same_house(best, current) and rb[1] == 1 and isinstance(home, dict) and home.get('weight', 0) < 99:
        # inside one house the sheet-derived home is circular (sibling papers run the same byline); only a web-verified tenure decides
        r2 = sorted(rows, key=lambda r: rank(r, credited=cred))
        if r2[0] is current or rank(r2[0], credited=cred)[:2] == rank(current, credited=cred)[:2]:
            out['why'] = 'same house: sheet-derived reporter home is circular, no swap'
            return out
    why = []
    if rb[1] == 0: why.append('credited originating service: ' + ', '.join(sorted(c.replace('STATION:', '') for c in cred)))
    if rb[1] == 1: why.append(tier(best, credited=cred, home=home)[1])
    if rc[0] == 3: why.append(f'current Original is a {row_type(current)} row (never first)')
    if rc[0] == 2: why.append('current Original is a press-release copy')
    if rc[1] == 5: why.append("current Original's byline credits another outlet")
    if rb[:2] != rc[:2] and not why: why.append(f'originals order: {tier(best, credited=cred, home=home)[1]} over {tier(current, credited=cred, home=home)[1]}')
    if rb[:2] == rc[:2]: why.append('same tier, earlier date / NewsBank over web')
    out['swap'] = True
    out['class_swap'] = rb[:2] != rc[:2]   # a class difference (eligibility or tier), not date only
    out['why'] = '; '.join(why)
    return out


# ---------------- type-pair candidate prefilter ----------------
def candidates(find, originals, days=TEXT_WINDOW_DAYS, credited=False):
    """originals: dicts of sheet Original rows. Window +-days (REPRINT90-v1). Prefilter: a credited find, or a find at a
    redistributor-type outlet (aggregator, distributor, station, chain, foreign) against an originator-type or service
    Original, needs no headline overlap (REPRINT-v2 type-pair prefilter: missing originators get tested); other pairs need
    overlapping headline words. AV items are never candidates for text rows and vice versa."""
    d = todate(find.get('Date'))
    if not d:
        return []
    ft = row_type(find)
    fav = is_av_item(find)
    out = []
    for o in originals:
        od = todate(o.get('Date'))
        if not od or abs((d - od).days) > days:
            continue
        if is_av_item(o) != fav:
            continue
        ot = row_type(o)
        if credited or headline_overlap(find.get('Headline'), o.get('Headline')) or \
           (ft in REDISTRIBUTOR and (ot in ORIGINATOR or service_of_outlet(o.get('Outlet'), row_key(o)))):
            out.append(o)
    return out


# ---------------- containment + pair classes (the matrix "cells") ----------------
def containment(m):
    """m = measure(va, vb) -> (contained, short_cov, long_cov, which) : the shorter text lies >= THR inside the longer (edge-aware)
    while the longer is covered < THR. which = 'a' when a is the contained (shorter) text."""
    if not m:
        return False, 0.0, 0.0, ''
    ea, eb = m['edge']
    ra, rb = m['raw']
    ca, cb = max(ea, ra), max(eb, rb)
    if ca >= THR and cb < THR:
        return True, ca, cb, 'a'
    if cb >= THR and ca < THR:
        return True, cb, ca, 'b'
    return False, max(ca, cb), min(ca, cb), ''


def translated_headline_sim(a, b):
    """similarity of two rows' headlines across languages, using the Translated Headline / English headline of each side;
    None when neither side has an English form to compare"""
    def eng(x):
        if str(x.get('Language') or '').strip() in ('', 'English'):
            return x.get('Headline') or ''
        return x.get('Translated Headline') or ''
    ha, hb = eng(a), eng(b)
    if not ha or not hb:
        return None
    return max(headline_sim(ha, hb), 1.0 if headline_overlap(ha, hb) else 0.0 if len(hwords(ha) & hwords(hb)) < 2 else 0.5)


def pair_class(orig, other, verdict=None, credited=None, home_of=None, texts=None):
    """REPRINT-v2 decision for "is `other` a Reprint of `orig`?" -> dict(kind, note, conf).
    kinds: 'reprint' (grouped) · 'edition' (same outlet web/print/feed/second platform: one row, Web + Print) · 'never'
    (AV ↔ text, AV ↔ AV, wire ↔ other wire, PR-service ↔ newsroom) · 'translation' (credited, <= 2 days: a Reprint) ·
    'own' (its own story). verdict: text_verdict result (None = no usable text). credited: origin_credits set of the story.
    home_of: callable(row) -> (outlet key, evidence) from reporters.home_of (None = no reporter data)."""
    oav, bav = is_av_item(orig), is_av_item(other)
    ko, kb = row_key(orig), row_key(other)
    to, tb = row_type(orig), row_type(other)
    if oav or bav:
        if oav and bav and (ko == kb or same_house(orig, other)):
            return {'kind': 'edition', 'note': 'same AV item on a second platform / re-air: an edition of one row', 'conf': 'high'}
        if oav and bav:
            return {'kind': 'never', 'note': 'an AV item is never a reprint of another AV item (re-air / re-upload = edition of one row; a dub = its own story)', 'conf': 'high'}
        if verdict and verdict.get('ok') and verdict.get('conf') == 'high':
            # the item's page carries the full article text: the same transcript / article on a second platform of the same house is
            # an edition; at another outlet it is the text being reprinted (KTLA video page -> Yahoo copy)
            if same_house(orig, other):
                return {'kind': 'edition', 'note': 'same transcript / text on a second platform of the same outlet: an edition of one row', 'conf': 'high'}
            return {'kind': 'reprint', 'note': 'the AV item\'s page carries the article text and it passes the text rule (' + verdict.get('mode', 'text') + ')', 'conf': 'medium'}
        return {'kind': 'never', 'note': 'AV ↔ text is never a reprint (a web write-up of a segment is its own story)', 'conf': 'high'}
    if to == 'wire' and tb == 'wire' and not same_house(orig, other):
        return {'kind': 'never', 'note': 'a wire never reprints another wire (own distributor only)', 'conf': 'high'}
    pr = lambda x: str(x.get('Press release') or '').strip().lower() == 'yes'
    if (to == 'prservice') != (tb == 'prservice') and not (pr(orig) and pr(other)):
        return {'kind': 'never', 'note': 'a press-release service text at a newsroom is a release copy (relcopy / release_rule), not a reprint', 'conf': 'high'}
    lo, lb = str(orig.get('Language') or '').strip(), str(other.get('Language') or '').strip()
    do, db = todate(orig.get('Date')), todate(other.get('Date'))
    gap = abs((do - db).days) if do and db else None
    cr_b = credit_of(other, (texts or {}).get(other.get('Article ID')) or (texts or {}).get(id(other)) or '')
    credits_orig = any(service_matches_outlet(c, orig.get('Outlet'), ko) for c in cr_b) or (
        credited and any(service_matches_outlet(c, orig.get('Outlet'), ko) for c in credited) and bool(cr_b))
    same_people = bool(people(orig.get('Author / byline')) & people(other.get('Author / byline')))
    if lo and lb and lo != lb:   # (checked before the same-outlet rule: a paper's own translation is a translation, not an edition)
        if verdict and verdict.get('ok') and verdict.get('conf') == 'high':
            return {'kind': 'reprint', 'note': 'same text (%s) although the Language cells differ (%s / %s): one Language cell is wrong' % (verdict.get('mode', 'text'), lo, lb), 'conf': 'medium', 'lang_fix': True}
        hs = translated_headline_sim(orig, other)
        if (credits_orig or same_people) and gap is not None and gap <= TRANSLATION_DAYS and (hs is None and credits_orig or hs is not None and hs >= 0.5):
            return {'kind': 'translation', 'note': f'translation of the {lo} original ({"credit" if credits_orig else "same byline"}, {gap} d' + (f', translated headline {hs:.2f}' if hs is not None else '') + '): a Reprint', 'conf': 'medium'}
        return {'kind': 'own', 'note': 'another language: no credit / same byline + matching translated headline within 2 days: its own story', 'conf': 'medium'}
    if ko and ko == kb:
        return {'kind': 'edition', 'note': 'same outlet (web + print / Today\'s Edition / feed): one Web + Print row, not a reprint', 'conf': 'high'}
    if verdict and verdict.get('ok'):
        return {'kind': 'reprint', 'note': 'same text (' + verdict.get('mode', 'text') + ')', 'conf': verdict.get('conf', 'high')}
    if verdict and verdict.get('m'):
        cont, sc, lc, which = containment(verdict['m'])
        if cont and which == 'a' and (credits_orig or same_people):   # `other` (a) lies inside the Original's text
            return {'kind': 'reprint', 'note': f'trimmed credited copy: {sc:.0%} of it lies in the {orig.get("Outlet", "")} text ({lc:.0%} of that text)', 'conf': 'medium', 'contained': True}
        if cont and which == 'a':
            return {'kind': 'own', 'note': f'trimmed copy ({sc:.0%} inside the longer text) with no credit: check it', 'conf': 'low', 'contained': True}
        if cont and which == 'b' and tb in NEVER_ORIGINAL:   # the whole Original lies inside an aggregator's longer page: page clutter
            return {'kind': 'reprint', 'note': f'aggregator copy carrying the whole text ({sc:.0%}) plus page clutter', 'conf': 'medium', 'contained': True}
        # v22 (coordinator 2026-10-28): containment is symmetric. The whole Original lies inside a LATER-FOUND longer text that
        # credits it, carries the same people, or that the Original credits (Mondaq 01386 = 100% inside the Jones Day alert
        # 10317): one story; reprint_check / the regroup then apply the originals order v2 (choose_original) to say which row is
        # the Original. No credit and no shared byline: listed, not grouped (as for the forward direction).
        bl = blend_cell(orig, other, verdict, credits_orig, (texts or {}).get(other.get('Article ID')) or (texts or {}).get(id(other)) or '')   # WIREBLEND-v1
        if bl:
            return bl
        if cont and which == 'b':
            cr_o = credit_of(orig, (texts or {}).get(orig.get('Article ID')) or (texts or {}).get(id(orig)) or '')
            credits_other = any(service_matches_outlet(c, other.get('Outlet'), kb) for c in cr_o)
            if credits_orig or credits_other or same_people:
                return {'kind': 'reprint', 'note': f'the whole {orig.get("Outlet", "")} text ({sc:.0%}) lies inside the longer {other.get("Outlet", "")} text '
                                                   f'({lc:.0%} of it; {"same people" if same_people else "credit"}): one story, the originals order decides the Original',
                        'conf': 'medium', 'contained': True, 'reverse': True}
            # no credit / shared byline: fall through to the second signals below (sibling, credit window, reporter home)
        # text differs: second signals
        if same_house(orig, other) and same_people and gap is not None and gap <= SIBLING_DAYS:
            return {'kind': 'reprint', 'note': 'sibling outlet, same reporter, <= 7 days: edited re-run', 'conf': 'low'}
        if credits_orig and gap is not None and gap <= TEXT_WINDOW_DAYS:
            return {'kind': 'reprint', 'note': 'byline / credit names the originating service, text trimmed or rewritten', 'conf': 'low'}
        if home_of:
            hk, hev = home_of(other)
            if hk and service_matches_outlet(service_of_outlet('', hk) or '', orig.get('Outlet'), ko) and to in ORIGINATOR and gap is not None and gap <= SIBLING_DAYS:
                return {'kind': 'reprint', 'note': 'reprint byline is a reporter of the originating outlet (' + hev + ')', 'conf': 'low'}
        return {'kind': 'own', 'note': 'text rule fails and no accepted second signal: its own story', 'conf': 'medium'}
    if verdict and verdict.get('mode') == 'headline+author':
        return {'kind': 'reprint' if verdict.get('ok') else 'own', 'note': 'headline + people (no text)', 'conf': 'medium'}
    return {'kind': 'own', 'note': 'no text to compare', 'conf': 'low'}


# ---------------- wrong-copy guard (REPRINT_PLAN 9) ----------------
def _load_wrong_copies():
    """wrong_copies.csv next to this script: Article ID -> reason (saved copies known to hold another article's text)"""
    import csv as _csv
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'wrong_copies.csv')
    try:
        return {r['aid'].strip(): r.get('reason', '') for r in _csv.DictReader(open(p, encoding='utf-8')) if r.get('aid')}
    except OSError:
        return {}


WRONG_COPIES = _load_wrong_copies()


def copy_mismatch(row, title='', kind='html', text=''):
    """A saved copy that cannot be this row's article -> reason, else ''. Hard rules only (the copy is dropped from matching and
    from the viewer): (a) listed in wrong_copies.csv; (b) a text whose dateline names another outlet's station while the row is a
    wire (an AP row holding a station page). Soft doubts go through copy_suspect()."""
    aid = str(row.get('Article ID') or '').strip()
    if aid in WRONG_COPIES:
        return 'listed in wrong_copies.csv: ' + WRONG_COPIES[aid]
    if text:
        m = STATION_DATELINE.search(text[:600])
        if m and row_type(row) == 'wire' and not service_matches_outlet(_station_service(m.group(1)), row.get('Outlet')):
            return 'text opens with a %s dateline but the row is a wire' % m.group(1)
    return ''


def copy_suspect(row, title='', kind='html'):
    """A saved copy that may not be this row's article -> reason, else '' (reported, not dropped): a page title sharing no word with
    the row's headline (both >= 3 content words; AV rows excluded, their pages are titled by show and date; print rows excluded,
    their print headline differs from the web title by design)."""
    if str(row.get('Medium') or '').strip() in ('Podcast', 'Radio', 'TV', 'Video') or str(row.get('Edition') or '').strip() == 'Print':
        return ''
    hw, tw = hwords(row.get('Headline')), hwords(title)
    if len(hw) >= 3 and len(tw) >= 3 and not (hw & tw) and headline_sim(row.get('Headline'), title) < 0.35:
        return 'page title shares no words with the row headline: "%s"' % str(title)[:80]
    return ''


# ---------------- OCR-tolerant option (OCRTOL-v1, agent-clip 2026-10-27; DECISIONS "decide all near misses for OCR
# automatically") ----------------
# Opt-in only: the default rule above is unchanged. For OCR text (NewsBank print-page clips, or any OCR source the
# Update button reads), tokens of >= 4 characters that differ by edit distance <= 1 count as equal, common OCR swaps
# (rn/m, l/1/i/|, o/0) are folded, and merged/split words are repaired against the other text's vocabulary; then the
# same 25-word-run / 90%-of-both test runs. Near misses that still fall short are linked by headline + author + date.
NEAR_LO = 0.60
HL_SIM = 0.80


def _ed1(a, b):
    """edit distance <= 1"""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:] if la < lb else a[i + 1:] == b[i + 1:]


def ocr_fold(t):
    """fold common OCR confusions inside a word token (number tokens are left alone)"""
    if t.isdigit() or not any(ch.isalpha() for ch in t):
        return t
    t = t.replace('rn', 'm').replace('|', 'l')
    return t.translate(str.maketrans({'1': 'l', 'i': 'l', '0': 'o'}))


def _repair(toks, vocab):
    """merged / split words: split a token missing from vocab into two vocab words; join a pair whose concatenation is
    in vocab while one part is not"""
    out, i, n = [], 0, len(toks)
    while i < n:
        t = toks[i]
        if i + 1 < n and t + toks[i + 1] in vocab and (t not in vocab or toks[i + 1] not in vocab):
            out.append(t + toks[i + 1]); i += 2; continue
        if t not in vocab and len(t) >= 6:
            sp = next(((t[:j], t[j:]) for j in range(2, len(t) - 1) if t[:j] in vocab and t[j:] in vocab), None)
            if sp:
                out.extend(sp); i += 1; continue
        out.append(t); i += 1
    return out


def ocr_tolerant_pair(va, vb):
    """return copies of versions va (OCR side) and vb with tolerant canonical tokens"""
    fa = [ocr_fold(t) for t in va['raw']]
    fb = [ocr_fold(t) for t in vb['raw']]
    vocab_b = set(fb)
    fa = _repair(fa, vocab_b)
    fb = _repair(fb, set(fa))
    # map tokens >= 4 chars of A onto a vocab-B token at edit distance <= 1 (bucket by length and first/last char)
    byk = {}
    for w in vocab_b:
        if len(w) >= 4:
            byk.setdefault((len(w), w[0]), []).append(w)
            byk.setdefault((len(w), w[-1]), []).append(w)
    cache = {}

    def canon(t):
        if len(t) < 4 or t in vocab_b:
            return t
        if t in cache:
            return cache[t]
        hit = None
        for L_ in (len(t) - 1, len(t), len(t) + 1):
            for key in ((L_, t[0]), (L_, t[-1])):
                for w in byk.get(key, ()):
                    if _ed1(t, w):
                        hit = w; break
                if hit: break
            if hit: break
        cache[t] = hit or t
        return cache[t]
    fa = [canon(t) for t in fa]
    mk = lambda raw, label: {'label': label, 'raw': raw, 'mask': [False] * len(raw), 'strip': raw}
    return mk(fa, va.get('label', '') + '~ocr'), mk(fb, vb.get('label', '') + '~ocr')


def text_verdict_ocr(ocr_list, other_list):
    """OCR-tolerant verdict: plain rule first; if not ok, re-test with tolerant tokens. Adds 'tolerant': True when the
    tolerant pass decided it. Same return shape as text_verdict."""
    v = text_verdict(ocr_list, other_list)
    if v and v['ok']:
        return v
    best = None
    for a in ocr_list:
        for b in other_list:
            if len(a['raw']) < MINW or len(b['raw']) < MINW:
                continue
            ta, tb = ocr_tolerant_pair(a, b)
            m = measure(ta, tb)
            if m and (best is None or min(m['raw']) > min(best['raw'])):
                best = m
    if best and min(best['raw']) >= THR:
        return {'ok': True, 'conf': 'low', 'mode': 'ocr-tolerant', 'm': best, 'tolerant': True}
    if v is None and best is None:
        return None
    if best and (v is None or min(best['raw']) > max(min(v['m']['raw']), min(v['m']['clut']), min(v['m']['edge']))):
        return {'ok': False, 'conf': 'medium', 'mode': 'ocr-tolerant', 'm': best, 'tolerant': True}
    return v


def best_cov(v):
    m = v['m']
    return max(min(m['raw']), min(m['clut']), min(m['edge']))


def headline_sim(a, b):
    import difflib
    return difflib.SequenceMatcher(None, nh(a), nh(b)).ratio()


def ocr_near_miss_link(find, cand, verdict):
    """Step 2 of the OCR near-miss rule: verdict is a failed text_verdict_ocr result whose best coverage is in
    [NEAR_LO, THR). find/cand: dicts with Headline (find may carry 'Print headline' alternatives as a list under
    'headlines'), Author / byline, Date. Returns (linked: bool, evidence: str)."""
    hs = [find.get('Headline')] + list(find.get('headlines') or [])
    sim = max(headline_sim(h, cand.get('Headline')) for h in hs if h) if any(hs) else 0.0
    pa, pb = people(find.get('Author / byline')), people(cand.get('Author / byline'))
    same_auth = (pa == pb) if (pa or pb) else True
    da, db = todate(find.get('Date')), todate(cand.get('Date'))
    near_date = bool(da and db and abs((da - db).days) <= WINDOW_DAYS)
    ok = sim >= HL_SIM and same_auth and near_date
    ev = f"headline {sim:.2f} + {'same author' if (pa or pb) else 'no byline either'}" if ok else \
         f"no link: headline {sim:.2f}, author {'same' if same_auth else 'differs'}, date {'ok' if near_date else 'out of window'}"
    return ok, ev


def decide_ocr(find_versions, find, cands):
    """Full OCR rule for one find against candidate stories.
    cands: list of (row_dict, versions). Returns dict(kind='link'|'new', row, evidence, verdict)."""
    best = None
    for row, vs in cands:
        v = text_verdict_ocr(find_versions, vs) if vs and find_versions else None
        if v and v['ok']:
            ev = 'text %.0f%%' % (100 * best_cov(v)) if not v.get('tolerant') else 'auto (OCR near miss): tolerant %.0f%%' % (100 * min(v['m']['raw']))
            cand = {'kind': 'link', 'row': row, 'evidence': ev + ' (OCR)', 'verdict': v, 'score': (2, best_cov(v))}
        elif v and best_cov(v) >= NEAR_LO:
            ok, ev = ocr_near_miss_link(find, row, v)
            cand = {'kind': 'link' if ok else 'new', 'row': row, 'evidence': ('auto: ' if ok else '') + ev + ' (near miss %.0f%%, OCR)' % (100 * best_cov(v)), 'verdict': v, 'score': (1 if ok else 0, best_cov(v))}
        else:
            ha = headline_author(find, row)
            if not (v and v.get('m')) and ha['verifiable'] and ha['ok']:
                cand = {'kind': 'link', 'row': row, 'evidence': 'headline + people', 'verdict': v, 'score': (1.5, 0)}
            else:
                continue
        if best is None or cand['score'] > best['score']:
            best = cand
    if best is None or best['kind'] != 'link':
        return {'kind': 'new', 'row': None, 'evidence': best['evidence'] if best else 'no candidate passed', 'verdict': best and best['verdict']}
    return best


# OCRTOL-v1b (agent-clip 2026-10-27): print-page OCR text carries jump lines ("See GABRIEL on Page A7", "Continued on
# A6", "From Page 1") and short all-caps labels (jump headlines, kickers, section labels) that are not article text.
OCR_JUMP = re.compile(r"^\s*(?:(?:see|turn to)\s+[\w'’ .-]{1,40}?(?:,|\s+on)?\s+(?:page|pg\.?|p\.)\s*[A-Z]?\d+\b.*|continued (?:on|from)\b.*|from (?:page|pg\.?)\s*[A-Z]?\d+\b.*|jumps? to\b.*)$", re.I)


def ocr_clean_text(text):
    """drop jump lines and short ALL-CAPS label lines/paragraphs (<= 6 words) from OCR text before the OCR-tolerant test"""
    out = []
    for line in re.split(r'(\n+)', text or ''):
        s = line.strip()
        if s and not line.startswith('\n'):
            letters = [c for c in s if c.isalpha()]
            if OCR_JUMP.match(s) or (letters and len(s.split()) <= 6 and all(not c.islower() for c in letters) and len(letters) >= 3):
                continue
        out.append(line)
    return re.sub(r'\n{3,}', '\n\n', ''.join(out)).strip()


# ---------------- COPYCHECK-v1 (copies-apply 2026-10-28, DECISIONS COPIES-v1): save-time copy identity check R1-R7 -------------
# copy_check(row, page, hosts=None, story_rows=None, held=None) -> (verdict 'ok'|'flag'|'reject', reasons, extra). Lives in
# copy_check.py (published next to this script); copy_mismatch() keeps the hard list. Used by sheet_task.check_page.
try:
    from copy_check import copy_check, outlet_hosts, VERSION as COPYCHECK_VERSION   # noqa: F401
except Exception:   # an older pipeline without copy_check.py: the check is skipped, never fatal
    copy_check = None


# ---------------- WIREBLEND-v1 (Sammy 2026-10-29) ----------------
# "Staff and wire reports": a paper's own story that wraps local reporting around wire paragraphs. It stays its own story (the paper's
# Original, never a Reprint) with a "uses wire copy" note and a link to the wire story, and counts toward the wire story's pickups.
# Cell: a non-wire newsroom's text that contains a wire Original's text in part (>= BLEND_LO of the wire words and >= BLEND_MIN_WORDS
# matched words) while NOT passing the reprint rule (both texts >= THR). Signals: the paper's row/text credits that wire service
# (credit_of), or carries a blend phrase. The whole wire text inside a longer paper text with local additions (wire coverage >= THR,
# paper coverage < THR) is a blend too: it overrides the v22 reverse-containment grouping for a wire Original and a newsroom.
BLEND_LO = 0.25
BLEND_MIN_WORDS = 60
BLEND_NOT = frozenset({'wire', 'prservice', 'aggregator', 'distributor'})
BLEND_PHRASE = re.compile(r"(?:staff,? (?:and )?(?:wire|news service)s? (?:reports?|services?)|(?:and|with) wire (?:reports?|services?)|"
                          r"(?:the )?(?:associated press|reuters|city news service|bay city news|upi|jta) (?:also )?contribut\w+|"
                          r"contribut\w+ (?:to this report )?(?:by|from) (?:the )?(?:associated press|reuters|city news service|bay city news))", re.I)


def blend_phrase(row, text=''):
    by = ' '.join(str(row.get(k) or '') for k in ('Author / byline', 'Author title'))
    m = BLEND_PHRASE.search(by) or BLEND_PHRASE.search((text or '')[:1500] + ' ' + (text or '')[-1200:])
    return m.group(0)[:60] if m else ''


def _pure_wire_copy(orig, other, phrase):
    """the newsroom row carries the wire's own copy rather than a blend: no blend phrase and a byline that is empty, only a service
    name ("By Associated Press", "Staff report" under a wire dateline) or only people who are the wire story's own reporters"""
    if phrase:
        return False
    by = str(other.get('Author / byline') or '')
    po, pw = people(by), people(orig.get('Author / byline'))
    fz = lambda ps: {unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower().split()[-1][:4] for x in ps if x.split()}
    if po and pw and fz(po) & fz(pw):
        return True                                   # same reporters (spelling / accents ignored)
    if re.search(r"(?i)\b(?:staff|[A-Z][a-z]+ [A-Z][a-z]+)\s+and\s+(?:the\s+)?(?:associated press|city news service|bay city news|reuters|jta|wire)\b", by):
        return False                                  # "Jane Doe and The Associated Press": the paper's reporter + the wire
    if any(rc.search(by) for _, (ro, rc) in _SVC_RX.items()):
        return True                                   # "Adam Beam, Associated Press": the wire's own copy under its reporter's name
    rest = by
    for _, (ro, rc) in _SVC_RX.items():
        rest = rc.sub(' ', rest)
    rest = re.sub(r"(?i)\b(by|and|the|staff|wire|reports?|news|service|services|from|via|writers?|press|associated|city|bay|of|for|special|to)\b|[^\w]", ' ', rest)
    return not rest.strip() or not po


def blend_cell(orig, other, verdict, credits_orig, other_text=''):
    """orig: a wire-type Original row; other: the newsroom row (find or sheet row); verdict: text_verdict(other, orig) result.
    -> {'kind': 'blend', 'note', 'conf', 'wire_cov', 'paper_cov', 'matched'} or None"""
    if row_type(orig) != 'wire' or row_type(other) in BLEND_NOT or is_av_item(other) or is_av_item(orig) or same_house(orig, other):
        return None
    if str(other.get('Press release') or '').strip().lower() == 'yes' or not verdict or not verdict.get('m'):
        return None
    m = verdict['m']
    pcov, wcov = m['raw'][0], max(m['raw'][1], m['edge'][1])
    if min(m['raw']) >= THR or not m.get('n'):
        return None                                   # both texts >= 90%: the reprint rule's job
    matched = int(round(wcov * m['n'][1]))
    phrase = blend_phrase(other, other_text)
    if wcov < BLEND_LO or matched < BLEND_MIN_WORDS or not (credits_orig or phrase) or _pure_wire_copy(orig, other, phrase):
        return None
    by = ' '.join(str(other.get(k) or '') for k in ('Author / byline', 'Author title'))
    conf = 'high' if BLEND_PHRASE.search(by) else 'medium' if phrase else 'low'   # phrase in the byline > phrase in the text > a credit / dateline only
    return {'kind': 'blend', 'note': f'blended story: {wcov:.0%} of the {orig.get("Outlet", "")} wire text ({matched} words) inside a text that is {pcov:.0%} wire; '
                                     + ('credits the service' if credits_orig else f'blend phrase "{phrase}"') + ': its own story, uses wire copy',
            'conf': conf, 'wire_cov': round(wcov, 3), 'paper_cov': round(pcov, 3), 'matched': matched}
