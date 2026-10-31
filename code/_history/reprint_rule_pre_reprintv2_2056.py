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
    return {'raw': raw, 'clut': clut, 'edge': (ea, eb), 'edge_ign': ia + ib, 'k': k}


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


def candidates(find, originals, days=TEXT_WINDOW_DAYS, credited=False):
    """originals: list of dicts (sheet rows of Original stories). Window +-days (default 90, REPRINT90-v1) and overlapping
    headlines. A candidate beyond +-WINDOW_DAYS can only link by text (headline_author refuses it).
    ORIGINCREDIT-v1: credited=True (a credit line/byline names an originating service, or the row just gained text)
    drops the headline-overlap prefilter: every Original in the window is a candidate for the text test."""
    d = todate(find.get('Date'))
    out = []
    for o in originals:
        od = todate(o.get('Date'))
        if d and od and abs((d - od).days) > days:
            continue
        if not d or not od:
            continue
        if credited or headline_overlap(find.get('Headline'), o.get('Headline')):
            out.append(o)
    return out


def onorm(o):
    o = (o or '').lower()
    o = re.sub(r"today's edition|: blogs|\bthe\b|[^\w\s]", ' ', o)
    return ' '.join(o.split())


WIRE = re.compile(r'calmatters|associated press|^ap$|center square|\bupi\b|religion news service|edsource|kff health news|kaiser health news|cronkite news|jewish telegraphic agency|\bjta\b|city news service|bay city news|yonhap|newsis|china news service|armenpress'
                  r'|mynewsla|jewish news syndicate|^jns\b|capital (?:&|and) main|states newsroom|stateline|^cnn wire|cnn newsource', re.I)   # ORIGINCREDIT-v1: + MyNewsLA (CNS), JNS, Capital & Main, States Newsroom, CNN Wire
AGG = re.compile(r'targeted news service|us fed news|u\.s\. fed news|tca news|tca regional|tribune content agency|u-wire|university wire|yahoo|\bmsn\b|\baol\b|newsbreak|newstex|contify|syndigate', re.I)
CREDIT = re.compile(r'capital (?:&|and) main|states newsroom|mynewsla|cnn wire|calmatters|associated press|\bthe associated press\b|center square|\bupi\b|religion news service|edsource|kff health news|kaiser health news|cronkite news|jewish telegraphic agency|\bjta\b|city news service|bay city news|yonhap|los angeles times|new york times|washington post|bloomberg|reuters|tribune news service|mcclatchy|sacramento bee|san francisco chronicle|mercury news|orange county register|southern california news group|bay area news group|politico|usa today|stateline|the conversation|capitol weekly|jewish news syndicate|\bjns\b|courthouse news', re.I)


# ---------------- ORIGINCREDIT-v1 (v20, agent-v20-origin-av; rootfix agent-calmatters 2026-10-28) ----------------
# A credit line / byline / NewsBank author / section / dateline that names an originating service, on ANY row of the
# story, forces that service's row first in the originals order (tier 0).
SERVICES = [  # (canonical, outlet regex, credit regex, case-sensitive credit)
    ('CalMatters', r'calmatters', r'calmatters', False),
    ('Associated Press', r'associated press|^ap$|^ap ', r'associated press|\(AP\)', False),
    ('The Center Square', r'center square', r'center square', False),
    ('States Newsroom', r'states newsroom|stateline', r'states newsroom|stateline', False),
    ('CNN', r'^cnn\b', r'CNN Wire|CNN Newsource|\(CNN\)', True),
    ('KFF Health News', r'kff health news|kaiser health news', r'kff health news|kaiser health news', False),
    ('EdSource', r'edsource', r'edsource', False),
    ('Jewish Telegraphic Agency', r'jewish telegraphic|^jta\b', r'jewish telegraphic agency|\bJTA\b', True),
    ('City News Service', r'(?<!bay )city news service|mynewsla', r'(?<!bay )city news service(?!,\s*b\.)|mynewsla', False),
    ('Bay City News', r'bay city news|local news matters', r'bay city news|city news service,\s*b\.', False),   # APA "City News Service, B." = Bay City News Service
    ('Capital & Main', r'capital (?:&|and) main', r'capital (?:&|and) main', False),
    ('Los Angeles Times', r'^los angeles times', r'los angeles times', False),
    ('Religion News Service', r'religion news service', r'religion news service', False),
    ('Cronkite News', r'cronkite news', r'cronkite news', False),
    ('UPI', r'\bupi\b|united press international', r'\bUPI\b|united press international', True),
    ('Jewish News Syndicate', r'jewish news syndicate|^jns\b', r'jewish news syndicate|\bJNS\b', True),
    ('Courthouse News Service', r'courthouse news', r'courthouse news', False),
    ('Yonhap', r'yonhap', r'yonhap', False),
]
CREDIT_LINE = re.compile(r"(?:originally (?:published|appeared|ran) (?:by|in|on|at)|first (?:published|appeared) (?:by|in|on|at)|"
                         r"republished (?:from|with permission (?:from|of))|(?:story|article|report) (?:was|is) (?:produced|published|reported|written) by|"
                         r"distributed by|is part of)\s+(?:the\s+)?([A-Z][\w&.'’ -]{2,40})")


def service_of_outlet(o):
    o = (o or '').strip().lower()
    for n, ro, _, _ in SERVICES:
        if re.search(ro, o):
            return n
    return None


def credit_of(row, text=''):
    """ORIGINCREDIT-v1: originating services named by this row -> {service: [evidence, ...]}. Signals: byline / Author
    title ("X, CalMatters", "X | CalMatters", "(CalMatters)"), the NewsBank APA author ("Stella Yu CalMatters, Y."), a
    CalMatters section, a credit line in the text ("originally appeared in", "republished from", "article was produced by",
    "is part of States Newsroom"), an "(AP) —" / "(CNN) —" dateline. A row never credits its own outlet's service."""
    out = {}
    own = service_of_outlet(row.get('Outlet'))
    by = ' '.join(str(row.get(k) or '') for k in ('Author / byline', 'Author title'))
    apa = str(row.get('Newsbank APA citation (article)') or '').split('(')[0]
    sec = str(row.get('Section') or '')
    t = text or ''
    for n, _, rc, cs in SERVICES:
        f = re.compile(rc, 0 if cs else re.I)
        if f.search(by):
            out.setdefault(n, []).append('byline: ' + by.strip()[:80])
        elif f.search(apa):
            out.setdefault(n, []).append('NewsBank author: ' + apa.strip()[:80])
        if n == 'CalMatters' and re.search('calmatters', sec, re.I):
            out.setdefault(n, []).append('section: ' + sec[:60])
    for m in CREDIT_LINE.finditer(t):
        for n, _, rc, cs in SERVICES:
            if re.search(rc, m.group(1), 0 if cs else re.I):
                out.setdefault(n, []).append('credit line: "' + m.group(0)[:90] + '"')
    if re.search(r'\(AP\)\s*[—–-]', t[:600]):
        out.setdefault('Associated Press', []).append('dateline (AP)')
    if re.search(r'\(CNN\)\s*[—–-]', t[:600]):
        out.setdefault('CNN', []).append('dateline (CNN)')
    out.pop(own, None)
    return out


def story_credits(rows, texts=None):
    """credits over every row of a story (any row's evidence counts) -> {service: [evidence]}; texts: {id(row) or
    Article ID: text}"""
    texts = texts or {}
    out = {}
    for r in rows:
        tx = texts.get(r.get('Article ID')) or texts.get(id(r)) or ''
        for n, ev in credit_of(r, tx).items():
            out.setdefault(n, []).extend(f"{r.get('Article ID', '')} {r.get('Outlet', '')}: {e}" for e in ev)
    return out


def _weak(e, n):
    """evidence 'AID Outlet: byline: <text>' whose byline is only the service's name (no person)"""
    if ': byline: ' not in e:
        return False
    by = e.split(': byline: ', 1)[1]
    rc, cs = next((x[2], x[3]) for x in SERVICES if x[0] == n)
    rest = re.sub(rc, ' ', by, flags=0 if cs else re.I)
    rest = re.sub(r'(?i)\b(the|by|and|staff|wire|reports?|news|service|from|via)\b|[^\w]', ' ', rest)
    return not rest.strip()


def origin_credits(rows, texts=None):
    """ORIGINCREDIT-v1: the services that rank first (tier 0) in this story -> (frozenset, {service: [evidence]}).
    - A strong credit (credit line, dateline, NewsBank author, section, or a byline/author title naming the service next
      to a person, e.g. "Yue Stella Yu | CalMatters") counts from any row.
    - A weak credit (byline = only the service's name, e.g. a station's "Associated Press" byline) shows who DISTRIBUTED
      the copy: it counts only when no other service has a row in the story.
    - Distribution: an Associated Press row whose byline names the same person as another service's row (AP's state
      wire carrying a CalMatters reporter's story) credits that other service."""
    ev = story_credits(rows, texts)
    svc_rows = {}
    for r in rows:
        sv = service_of_outlet(r.get('Outlet'))
        if sv:
            svc_rows.setdefault(sv, []).append(r)
    out = set()
    for n, es in ev.items():
        strong = [e for e in es if not _weak(e, n)]
        if strong or not (set(svc_rows) - {n}):
            out.add(n)
    for ap in svc_rows.get('Associated Press', []):
        if not re.search(r'(?i)state wire', ap.get('Outlet') or ''):   # AP's state wire carries member newsrooms' stories
            continue
        pa = people(ap.get('Author / byline'))
        for sv, rs in svc_rows.items():
            if sv == 'Associated Press' or not pa:
                continue
            if any(pa & people(r.get('Author / byline')) for r in rs):
                out.add(sv)
                ev.setdefault(sv, []).append(f"{ap.get('Article ID', '')} {ap.get('Outlet', '')}: AP row carries the {sv} reporter's byline")
    if 'Associated Press' in out and len(out) > 1 and not any('byline' not in e for e in ev.get('Associated Press', [])):
        out.discard('Associated Press')   # AP named only by bylines while another service is credited: AP distributed it
    return frozenset(out), ev


def tier(x, mostly_reprint=frozenset(), credited=frozenset()):
    o, by = x.get('Outlet') or '', x.get('Author / byline') or ''
    if credited and service_of_outlet(o) in credited:   # ORIGINCREDIT-v1: credited originator ranks first
        return 0, 'credited originating service (' + service_of_outlet(o) + ')'
    if AGG.search(o):
        return 5, 'aggregator/syndicator outlet'
    co = next((m.group(0) for m in CREDIT.finditer(by) if onorm(m.group(0)) not in onorm(o)), None)
    core = onorm(re.sub(r'\(.*?\)', '', o))
    own = len(core) > 3 and core in onorm(by)
    if own and not co and not WIRE.search(o):
        return 2, "byline names the row's own outlet"
    if WIRE.search(o) and not co:
        return 1, 'wire/originating service'
    if co:
        return 4, 'byline credits ' + co
    if onorm(o) in mostly_reprint:
        return 4, 'outlet mostly reprints'
    if people(by):
        return 2, 'own byline'
    return 3, 'other'


def rank(x, mostly_reprint=frozenset(), credited=frozenset()):
    """originals order: releases / aggregators never first; then tier (tier 0 = a service credited by any row of the
    story, ORIGINCREDIT-v1), earlier date, NewsBank over web, web over print"""
    rel = str(x.get('Press release') or '').strip().lower() == 'yes'
    t, why = tier(x, mostly_reprint, credited)
    # a reprint-list row of the credited originating service is eligible (the credit names it; ORIGINCREDIT-v1)
    elig = 2 if rel else 3 if AGG.search(x.get('Outlet') or '') else 4 if x.get('Data Source') == 'Tracker reprint list' and t != 0 else 0
    d = todate(x.get('Date')) or datetime.date(2100, 1, 1)
    src = 0 if x.get('Data Source') == 'Newsbank' else 1
    ed = 1 if x.get('Edition') == 'Print' else 0
    return (elig, t, d, src, ed)


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
