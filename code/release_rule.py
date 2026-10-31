"""release_rule.py - RELRULE-v1 (agent-relrule, 2026-10-27). Sammy: "Use the same standard for determine if something is a
release as you do for a reprint."

A Coverage row carries an official press release only when its saved text passes the reprint string-of-text rule
(reprint_rule.text_verdict: runs of >= 25 identical words, >= 40 CJK characters, covering >= 90% of BOTH texts; same
tokenising, clutter, caption and edge handling) against the release's own text (headline + dek + body, or body alone, since
NewsBank texts carry no headline). Window: the row is dated from 1 day before to 30 days after the release. No text on the
row = untestable: reprint_rule's no-text fallback (same headline + same people) needs a byline on both sides and releases
have none, so it never applies; untestable rows are listed for review and never marked.

Release texts live in release_texts.json ({"v":1, "rel": {url: {date, title, dek, body, src}}}), one entry per row of the
workbook's "Press releases" tab; the sheet task appends new ones.
"""
import json, os, re
import reprint_rule as RR

REL_WINDOW = (-1, 30)
K = 25

# EXCERPT-v1 (coordinator 2026-10-27, on Sammy's behalf: "Do what you think is better"): a press-release DISTRIBUTION record
# (US Fed News and similar services: "... issued the following news release:") whose body is a verbatim excerpt of the release
# counts as a copy. Verbatim = after stripping the service's header line, footer, copyright and citation, >= 90% of the row's
# remaining text lies in >= 25-word runs matching the release, and the excerpt has >= EXCERPT_MIN_WORDS words. The release side
# needs no minimum. Everything else keeps the two-sided 90% rule.
EXCERPT_MIN_WORDS = 25
DIST_HDR = re.compile(r'^[^\n]{0,300}?\b(?:issued|posted|released|published|distributed)\s+the\s+following\s+(?:news\s+|press\s+)?(?:release|statement)[^\n:]{0,80}:?[ \t]*', re.I | re.M)
DIST_CUT = re.compile(r'For any query with respect to this article|Copyright \(c\)|Copyright ©|Citation \(apa', re.I)


def excerpt_version(text):
    """the body of a distribution record (header line, footer, copyright, citation stripped), or None when the text has no
    distribution header"""
    m = DIST_HDR.search(text or '')
    if not m:
        return None
    body = DIST_CUT.split(text[m.end():])[0]
    return RR.version(body, 'html', 'excerpt')


def excerpt_cover(ev, rel):
    """share of the excerpt inside >= 25-word runs of the release (None when the excerpt is too short to count)"""
    if ev is None or len(ev['raw']) < max(EXCERPT_MIN_WORDS, K):
        return None
    best = 0.0
    for rv in rel['vers']:
        if len(rv['raw']) < K:
            continue
        cov = RR._cov(ev, rv, K, 'raw')
        best = max(best, sum(cov) / len(cov))
    return best


def load_texts(path):
    try:
        return json.load(open(path, encoding='utf-8')).get('rel', {})
    except Exception:
        return {}


def save_texts(path, rel):
    json.dump({'v': 1, 'rel': rel}, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def release_versions(title, dek, body):
    full = '\n'.join(x for x in (title, dek, body) if x)
    return [RR.version(full, 'html', 'rel:full'), RR.version(body or '', 'html', 'rel:body')]


def releases(texts, in_scope=None):
    """texts: {url: {...}} -> [{url, date, title, vers}] (only urls in in_scope when given)"""
    out = []
    for u, x in texts.items():
        if in_scope is not None and u not in in_scope:
            continue
        out.append({'url': u, 'date': str(x.get('date', ''))[:10], 'title': x.get('title', ''),
                    'vers': release_versions(x.get('title', ''), x.get('dek', ''), x.get('body', ''))})
    return out


def in_window(row_date, rel_date, window=REL_WINDOW):
    d, rd = RR.todate(row_date), RR.todate(rel_date)
    return bool(d and rd and window[0] <= (d - rd).days <= window[1])


def _grams(v):
    t = v['raw']
    return {tuple(t[i:i + K]) for i in range(len(t) - K + 1)}


def shares_run(row_versions, rel):
    """cheap prefilter: at least one 25-word run in common with the release"""
    if '_g' not in rel:
        rel['_g'] = _grams(rel['vers'][0]) | _grams(rel['vers'][1])
    for v in row_versions:
        t = v['raw']
        for i in range(len(t) - K + 1):
            if tuple(t[i:i + K]) in rel['_g']:
                return True
    return False


def title_near(headline, title):
    """cheap prefilter before reading a row's text: the headline shares at least 2 content words with the release title
    (reprint_rule.hwords), or overlaps it by reprint_rule.headline_overlap (on the 2026-10-27 audit: 96 of the 98 rows that
    pass the rule, vs 90 by headline_overlap alone; median 4 rows per release in the window)"""
    return RR.headline_overlap(headline, title) or len(RR.hwords(headline) & RR.hwords(title)) >= 2


def usable(row_versions):
    return [v for v in row_versions if len(v['raw']) >= RR.MINW]


def match(row_versions, rels):
    """best passing release -> {'release', 'verdict'}; None when none passes; 'untestable' when the row has no usable text.
    Versions labelled 'excerpt' (excerpt_version) are tested only by the EXCERPT-v1 exception, after the main rule."""
    ex = [v for v in row_versions if v.get('label') == 'excerpt']
    vs = usable([v for v in row_versions if v.get('label') != 'excerpt'])
    if not vs and not ex:
        return 'untestable'
    best = None
    for r in (rels if vs else []):
        if not shares_run(vs, r):
            continue
        v = RR.text_verdict(vs, r['vers'])
        if v and v['ok']:
            key = (v['conf'] == 'high', min(v['m']['raw']))
            if best is None or key > best[0]:
                best = (key, r, v)
    if best is None and ex:   # EXCERPT-v1
        for r in rels:
            c = max((excerpt_cover(e, r) or 0) for e in ex)
            if c >= RR.THR and (best is None or c > best[0]):
                best = (c, r, {'ok': True, 'conf': 'medium', 'mode': 'excerpt', 'm': {'raw': (c, None)}})
    return None if best is None else {'release': best[1], 'verdict': best[2]}


def pct(v):
    m = v['m']
    if v.get('mode') == 'excerpt':
        return round(100 * m['raw'][0], 1)
    return round(100 * min(m['raw']), 1)


def page_versions(html):
    """a saved (cleaned) page or tracker copy -> rule versions"""
    t, k = RR.html_text(html)
    return [RR.version(t, k, 'page')]


def file_versions(path):
    """a library file: cleaned HTML, or a NewsBank / ProQuest PDF (pdftotext, read as NewsBank text)"""
    if not path or not os.path.exists(path):
        return []
    if path.lower().endswith(('.html', '.htm')):
        h = open(path, encoding='utf-8', errors='replace').read()
        out = page_versions(h)
        ev = excerpt_version(RR.html_text(h)[0])
        return out + ([ev] if ev else [])
    if path.lower().endswith('.pdf'):
        import subprocess
        try:
            t = subprocess.run(['pdftotext', path, '-'], capture_output=True, text=True, timeout=60).stdout
        except Exception:
            return []
        ev = excerpt_version(t)
        t = re.split(r'\n\s*Citation \(apa Style\)', t)[0]     # NewsBank's citation block is not article text
        return [RR.version(t, 'nb', 'pdf')] + ([ev] if ev else [])
    return []
