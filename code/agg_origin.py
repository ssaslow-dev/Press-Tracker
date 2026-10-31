"""agg_origin.py - AGGORIGIN-v1 (agg-orig 2026-10-29; coordinator + Sammy): an aggregator / syndicator find is never the Original.
Pure functions (no I/O except reading outlet_rules.json through reprint_rule), used by sheet_task.Sheet.agg_origin_step and by
the tests. The Update button path (tracker JS) mirrors provider_credit() in 41_update_search.js (AGGORIGIN block).

  provider_credit(text, url='', links=(), head='')  -> [{outlet, how, evidence, house}]  who the page says it came from
  yahoo_unit(url, outlet='')                         -> 'Yahoo Life' / 'Yahoo News Hong Kong' ... or ''  (Yahoo's own editorial units)
  release_repost_reason(obj, text='')                -> reason string or ''  (a repost of an organization's / official's own release)
  resolve(find, text, links, rows, employer=None)    -> decision dict {action, outlet, how, evidence, row, note}
        action: 'known'   the credited originator is already a sheet row (row=...): the text rule (reprint_check) decides the merge;
                          below the text rule the find is kept with a Team note naming the credit (no credit-only merge)
                'wanted'  the originator is credited (or is the byline's employer) but has no row: the originator is fetched by the
                          Update button (_origin) or listed as an `origin` review item; the find is kept with a Team note meanwhile
                'unit'    Yahoo's own editorial unit: the Outlet becomes the unit (a publisher, not an aggregator)
                'unknown' no identifiable source: kept, Team note "Originator unknown ..."
                'none'    the find is not from an aggregator
"""
import re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import reprint_rule as RR
except Exception:   # pragma: no cover
    RR = None

REASON_RELEASE = "repost of an organization's own release, not press coverage"
TEAM_UNKNOWN = 'Originator unknown: aggregator-hosted piece kept as Original (no identifiable source in the saved text).'

_NAME = r"([A-Z0-9][\w&.'’:+ -]{1,48}?)"
_END = r"(?=\s*(?:[.,;:)\]|\n]|\s-\s|\s—|$|\sand\s|\sfor\s))"
FORMS = [
    ('read the original article on', re.compile(r"read the original (?:article|story|post|report) (?:on|at|from|in)\s+(?:the\s+)?" + _NAME + _END, re.I)),
    ('originally appeared/published', re.compile(r"originally\s+(?:appeared|published|ran|posted)\s+(?:in|on|at|by|with)\s+(?:the\s+)?" + _NAME + _END, re.I)),
    ('first appeared on', re.compile(r"(?:appeared|published|ran)\s+first\s+(?:in|on|at|by)\s+(?:the\s+)?" + _NAME + _END, re.I)),
    ('see at <outlet>', re.compile(r"\bSee at\s+([A-Z][A-Za-z0-9&.' -]{2,24}?)(?=\s*(?:[.,\n]|$))")),
    ('republished from', re.compile(r"republished\s+(?:from|with permission (?:from|of))\s+(?:the\s+)?" + _NAME + _END, re.I)),
    ('story courtesy of', re.compile(r"(?:story|article|photo|video)\s+courtesy\s+of\s+(?:the\s+)?" + _NAME + _END, re.I)),
]
DATELINE = re.compile(r"\(\s*([A-Z][A-Z0-9]{2,9})(\.COM)?\s*\)\s*[—–-]")          # (FOX40.COM) — / (KTLA) —
READ_MORE = re.compile(r"(?:read more|full story|continue reading|originally (?:posted|published))\s*(?:at|on|here)?\s*:?\s*(?:https?://)?(?:www\.)?([a-z0-9][a-z0-9.-]*\.[a-z]{2,})", re.I)
YAHOO_BRAND = re.compile(r"profiles\.yahoo\.com/brands/([a-z0-9-]+)", re.I)
HOUSE = re.compile(r"Copyright\s+\d{4}\s+(Nexstar Media|Sinclair|Gray Media|Scripps|Hearst Television|Tegna)", re.I)
GENERIC = {'yahoo', 'yahoo news', 'yahoo life', 'msn', 'aol', 'newsbreak', 'smartnews', 'google news', 'apple news', 'dnyuz', 'ground news',
           'flipboard', 'headtopics', 'the original', 'original', 'here', 'source', 'us', 'our', 'cnet button'}
BRAND_NAMES = {'food-wine': 'Food & Wine', 'allrecipes': 'Allrecipes', 'patch': 'Patch', 'ktxl-sacramento': 'FOX40', 'ktla': 'KTLA',
               'business-insider': 'Business Insider', 'the-independent': 'The Independent', 'cnet': 'CNET', 'delish': 'Delish',
               'los-angeles-times': 'Los Angeles Times', 'the-cool-down': 'The Cool Down'}
HOST_NAMES = {'fox40.com': 'FOX40', 'ktla.com': 'KTLA', 'latimes.com': 'Los Angeles Times', 'cnet.com': 'CNET', 'foodandwine.com': 'Food & Wine',
              'allrecipes.com': 'Allrecipes', 'delish.com': 'Delish', 'vcstar.com': 'Ventura County Star', 'cbsnews.com': 'CBS News',
              'cnn.com': 'CNN', 'nbcnews.com': 'NBC News', 'businessinsider.com': 'Business Insider', 'patch.com': 'Patch',
              'thecooldown.com': 'The Cool Down', 'the-independent.com': 'The Independent', 'ktvu.com': 'KTVU FOX 2', 'sfchronicle.com': 'San Francisco Chronicle',
              'sacbee.com': 'Sacramento Bee, The', 'apnews.com': 'Associated Press', 'npr.org': 'NPR', 'usatoday.com': 'USA TODAY'}
YAHOO_UNITS = [   # (host regex, path regex or None, unit outlet) - applied ONLY when the page names no other provider
    (re.compile(r'^hk\.news\.yahoo\.com$|^hk\.yahoo\.com$'), None, 'Yahoo News Hong Kong'),
    (re.compile(r'^tw\.news\.yahoo\.com$|^tw\.yahoo\.com$'), None, 'Yahoo News Taiwan'),
    (re.compile(r'^es-us\.[a-z.-]*yahoo\.com$|^es\.vida-estilo\.yahoo\.com$|^es-us\.vida-estilo\.yahoo\.com$'), None, 'Yahoo Vida y Estilo'),
    (re.compile(r'^(?:www\.)?yahoo\.com$'), re.compile(r'^/lifestyle/'), 'Yahoo Life'),
]
AGG_NAMES = re.compile(r'^(yahoo|msn|aol|newsbreak|smartnews|dnyuz|ground news|flipboard|headtopics|newser|nate news|sohu)\b', re.I)


def _key(o):
    return RR.outlet_key(o) if RR else re.sub(r'[^a-z0-9]+', ' ', str(o).lower()).strip()


def is_aggregator(outlet, city=''):
    """the outlet type table says aggregator (a Yahoo editorial unit, once in the table, is national - not an aggregator)"""
    if not outlet:
        return False
    if RR is not None:
        t = RR.TYPE_TABLE.get(RR.outlet_key(outlet, city))
        if t:
            return t[0] == 'aggregator'
        return RR.classify_outlet(outlet)[0] == 'aggregator'
    return bool(AGG_NAMES.search(outlet))


def _clean(name):
    n = re.sub(r'\s+', ' ', str(name)).strip(' .,:;-—|')
    n = re.sub(r'(?i)^(the\s+)(?=[A-Z])', r'\1', n)
    n = re.sub(r'(?i)\s*(?:\.|\bwhere\b|\bwith\b|\bat\b)\s*.*$', '', n) if len(n) > 30 else n
    return n.strip(' .,:;-—|')


def provider_credit(text, url='', links=(), head=''):
    """outlets the page says it came from, strongest first. Never returns an aggregator or a generic word."""
    t = str(text or '')
    out, seen = [], set()

    def add(name, how, ev, house=False):
        name = _clean(name)
        if not name or len(name) < 2 or name.lower() in GENERIC or is_aggregator(name) or AGG_NAMES.search(name):
            return
        k = _key(name)
        if k in seen:
            return
        seen.add(k)
        out.append({'outlet': name, 'how': how, 'evidence': ev[:140], 'house': house})
    for lk in links or ():
        m = YAHOO_BRAND.search(str(lk))
        if m:
            slug = m.group(1).lower()
            add(BRAND_NAMES.get(slug) or slug.replace('-', ' ').title(), 'Yahoo provider (brand profile)', str(lk))
    for how, rx in FORMS:
        for m in rx.finditer(t):
            add(m.group(1), how, m.group(0))
    m = DATELINE.search(t[:700])
    if m:
        add(m.group(1), 'dateline (%s)' % m.group(0).strip('()—–- '), m.group(0))
    for m in READ_MORE.finditer(t):
        h = m.group(1).lower().lstrip('www.')
        nm = HOST_NAMES.get(h) or HOST_NAMES.get('.'.join(h.split('.')[-2:]))
        if nm:
            add(nm, 'read-more link host', m.group(0))
    for m in HOUSE.finditer(t):
        out.append({'outlet': m.group(1).title(), 'how': 'copyright line (station group)', 'evidence': m.group(0), 'house': True})
    # AOL / MSN provider logo: a short outlet-name line at the very top ("Delish\n\nDanielle Harling\n\nWed, March 22, 2023")
    first = [x.strip() for x in str(head or t[:300]).splitlines() if x.strip()][:3]
    for x in first:
        if len(x.split()) <= 4 and x in BRAND_NAMES.values():
            add(x, 'provider logo line', x)
    return out


def yahoo_unit(url, outlet=''):
    """Yahoo's own editorial unit for a Yahoo URL, '' when none (the generic Yahoo News page stays an aggregator)"""
    m = re.match(r'https?://([^/]+)(/[^?#]*)?', str(url or ''))
    if not m:
        return ''
    host, path = m.group(1).lower(), m.group(2) or '/'
    for hrx, prx, unit in YAHOO_UNITS:
        if hrx.search(host) and (prx is None or prx.search(path)):
            return unit
    return ''


RELEASE_PATTERNS = [
    re.compile(r"(?i)(?:content )?(?:is )?adapted from (?:materials|a (?:press )?release|information) provided by"),
    re.compile(r"(?i)^\W*(?:SACRAMENTO|LOS ANGELES|WASHINGTON)\s*[–—-]\s*(?:Governor|Gov\.)\s+[A-Z][a-z]+ [A-Z][a-z]+\s+(?:today\s+)?(?:announced|signed|issued)"),
    re.compile(r"(?i)\bFOR IMMEDIATE RELEASE\b"),
    re.compile(r"(?i)^\W*(?:press release|news release)\b"),
]
RELEASE_AUTHORS = re.compile(r'^\s*(?:ca\.gov|gov\.ca\.gov|governor of california|office of the governor|[a-z .&-]*\(press office\))\s*$', re.I)
RELEASE_HOSTS = re.compile(r'(^|\.)(gov\.ca\.gov|ca\.gov|mwdh2o\.com|senate\.ca\.gov|assembly\.ca\.gov)$', re.I)


def release_repost_reason(obj, text=''):
    """Reason string when the find re-posts an organization's or official's own release (agency post, Governor's release) on an
    aggregator or social-style page; '' otherwise. A real news story that quotes a release is not held: the release forms must
    open the text (or the byline/host must be the issuer) and the outlet must be an aggregator or an official host."""
    outlet = str(obj.get('Outlet') or '')
    by = str(obj.get('Author / byline') or '')
    link = str(obj.get('Publisher link') or '')
    host = (re.match(r'https?://([^/]+)', link) or [None, ''])[1]
    agg = is_aggregator(outlet, str(obj.get('Outlet city') or ''))
    head = str(text or '')[:900]
    if RELEASE_AUTHORS.search(by) and (agg or RELEASE_HOSTS.search(host)):
        return REASON_RELEASE
    if agg or RELEASE_HOSTS.search(host):
        # the Governor's / an agency's text opening, or the adapted-from line anywhere
        for i, rx in enumerate(RELEASE_PATTERNS):
            if rx.search(str(text or '') if i == 0 else head):
                return REASON_RELEASE
    return ''


def resolve(find, text='', links=(), rows=(), employer=None, window_days=3):
    """decision for one find (see module docstring). rows: dicts of the sheet (Article ID, Story ID, Outlet, Outlet city, Date,
    Headline, Original or reprint). employer: callable(find) -> outlet name of the byline's employer on the story date, or ''."""
    outlet = str(find.get('Outlet') or '')
    url = str(find.get('Publisher link') or '')
    if not is_aggregator(outlet, str(find.get('Outlet city') or '')):
        return {'action': 'none'}
    cred = provider_credit(text, url, links)
    cred = [c for c in cred if not c.get('house')] or cred
    how_pref = None
    if not cred and employer:
        e = employer(find) or ''
        if e and not is_aggregator(e):
            cred = [{'outlet': e, 'how': 'byline employer (reporter_record)', 'evidence': str(find.get('Author / byline') or ''), 'house': False}]
    for c in cred:
        if c.get('house'):
            continue
        hit = _find_row(c['outlet'], find, rows, window_days)
        if hit:
            return {'action': 'known', 'outlet': c['outlet'], 'how': c['how'], 'evidence': c['evidence'], 'row': hit,
                    'note': 'Credited to %s (%s); text rule not met - not merged.' % (c['outlet'], c['how'])}
        return {'action': 'wanted', 'outlet': c['outlet'], 'how': c['how'], 'evidence': c['evidence'], 'row': None,
                'note': 'Credited to %s (%s); originator page not yet on record - fetch it (Update button) or add it no-copy.' % (c['outlet'], c['how'])}
    unit = yahoo_unit(url, outlet)
    if unit:
        return {'action': 'unit', 'outlet': unit, 'how': 'Yahoo editorial unit (no other provider named)', 'evidence': url, 'row': None,
                'note': ''}
    return {'action': 'unknown', 'outlet': '', 'how': '', 'evidence': '', 'row': None, 'note': TEAM_UNKNOWN}


def _find_row(outlet, find, rows, days):
    k = _key(outlet)
    d0 = RR.todate(find.get('Date')) if RR else None
    h0 = str(find.get('Headline') or '')
    for r in rows:
        if _key(r.get('Outlet') or '') != k:
            continue
        d1 = RR.todate(r.get('Date')) if RR else None
        if d0 and d1 and abs((d0 - d1).days) > days:
            continue
        if RR is not None and hasattr(RR, 'headline_sim') and RR.headline_sim(h0, str(r.get('Headline') or '')) >= 0.6:
            return r
        if _norm(h0) == _norm(r.get('Headline') or ''):
            return r
    return None


def _norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()
