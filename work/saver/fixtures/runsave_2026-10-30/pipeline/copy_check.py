"""COPYCHECK-v1 (copies-apply, 2026-10-28; DECISIONS COPIES-v1; design work/tmp_copies_design/design.md section 4a).

copy_check(row, page, ...) -> (verdict, reasons, extra)
  verdict  'ok' | 'flag' (save, Team note + review item "copy check") | 'reject' (do not save under this row)
  reasons  list of 'Rn: text'
  extra    {'file_to': Article ID of another row of the same story whose outlet owns the page host (R1), 'tags': [...]}

Meant to sit in reprint_rule.py next to copy_mismatch() (patch 01) and to be called by sheet_task.check_page after
page_check says ok (patch 02), by make_copies --check-copies and by the copies apply run.

row:  dict with Article ID, Story ID, Original or reprint, Outlet, Date, Headline, Print headline, Translated Headline,
      Language, Publisher link, Medium, Data Source
page: dict with url (the fetched / final URL), canonical (og:url or <link rel=canonical>, optional), title, h1,
      text (cleaned body text), published (ISO date the page states, optional), kind ('html' | 'nb' | 'pq'),
      source_line (NewsBank / ProQuest source line, for R7), file (the library name about to be written), sha (text hash)
"""
import re
import unicodedata
import datetime
from urllib.parse import urlparse

VERSION = 'COPYCHECK-v1'

# ---------- helpers ----------
STOP = set('a an the of to in on for and or with at by from as is are be was were it its that this new over after before about '
           'into out up says say said will can could would should not no ca calif california state bill law gabriel jesse '
           'assembly assemblymember'.split())

SCRIPTS = [
    ('cjk', re.compile(r'[一-鿿㐀-䶿぀-ヿ]')),
    ('hangul', re.compile(r'[가-힯ᄀ-ᇿ]')),
    ('cyrillic', re.compile(r'[Ѐ-ӿ]')),
    ('hebrew', re.compile(r'[֐-׿]')),
    ('arabic', re.compile(r'[؀-ۿݐ-ݿ]')),
    ('armenian', re.compile(r'[԰-֏]')),
    ('latin', re.compile(r'[A-Za-zÀ-ɏ]')),
]
LANG_SCRIPT = {
    'english': 'latin', 'spanish': 'latin', 'french': 'latin', 'portuguese': 'latin', 'german': 'latin', 'italian': 'latin',
    'vietnamese': 'latin', 'tagalog': 'latin', 'dutch': 'latin', 'polish': 'latin', 'turkish': 'latin', 'indonesian': 'latin',
    'chinese': 'cjk', 'japanese': 'cjk', 'korean': 'hangul', 'russian': 'cyrillic', 'ukrainian': 'cyrillic',
    'hebrew': 'hebrew', 'arabic': 'arabic', 'persian': 'arabic', 'farsi': 'arabic', 'urdu': 'arabic', 'armenian': 'armenian',
}
STATION_HOST = re.compile(r'(^|\.)(abc7|abc7news|abc10|abc30|kcra|ktla|kron4|fox40|fox11|fox5sandiego|foxla|kxtv|kgo|kpix|'
                          r'nbclosangeles|nbcbayarea|nbcsandiego|cbsnews|kcal|ksby|kesq|kget|kmph|ksee24|kusi|10news|'
                          r'cbs8|nbcpalmsprings|kabc|kfi|kqed|kpbs|wtkr|wral)\.(com|org|tv)$')
LISTING_PATH = re.compile(r'/(page|category|tag|tags|author|topics?|search)/|/\d{4}/\d{2}/page/\d+', re.I)


def nh(h):
    h = unicodedata.normalize('NFKC', h or '').lower()
    h = re.sub('[‘’“”\'"`]', '', h)
    h = re.sub(r'[^\w\s]', ' ', h)
    return ' '.join(h.split())


def hwords(h):
    return {w for w in nh(h).split() if w not in STOP and len(w) > 2}


def headline_sim(a, b):
    import difflib
    return difflib.SequenceMatcher(None, nh(a), nh(b)).ratio()


def todate(v):
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    m = re.match(r'(\d{4})-(\d\d)-(\d\d)', str(v or ''))
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def host_of(u):
    try:
        h = urlparse(str(u or '').strip()).netloc.lower()
    except ValueError:
        return ''
    h = h.split('@')[-1].split(':')[0]
    for p in ('www.', 'amp.', 'm.', 'old.', 'edition.'):
        if h.startswith(p):
            h = h[len(p):]
    return h


def base_domain(h):
    """registrable part: last two labels (three for co.uk-style, co.il, co.kr)"""
    parts = (h or '').split('.')
    if len(parts) >= 3 and parts[-2] in ('co', 'com', 'org', 'net', 'ac', 'or', 'ne', 'go'):
        return '.'.join(parts[-3:])
    return '.'.join(parts[-2:])


def script_of(text):
    """dominant script of a text (letters counted per script); '' when < 40 letters"""
    counts = {}
    for name, rx in SCRIPTS:
        counts[name] = len(rx.findall(text or ''))
    tot = sum(counts.values())
    if tot < 40:
        return ''
    name = max(counts, key=counts.get)
    return name


def slug_words(url):
    p = urlparse(str(url or '')).path
    segs = [s for s in p.split('/') if s and not re.fullmatch(r'[\d\-_.]+|article|news|story|amp|index\.html?', s)]
    if not segs:
        return set()
    seg = max(segs, key=len)
    seg = re.sub(r'\.(html?|php|aspx?)$', '', seg)
    return {w for w in re.split(r'[-_+]+', seg.lower()) if w and w not in STOP and len(w) > 2 and not w.isdigit()
            and not re.fullmatch(r'[0-9a-f]{8,}', w)}


def nwords(text):
    t = text or ''
    cjk = len(re.findall(r'[一-鿿぀-ヿ가-힯]', t))
    return len(re.findall(r'[^\W\d_]+', re.sub(r'[一-鿿぀-ヿ가-힯]', ' ', t))) + cjk // 2


def outlet_hosts(rows):
    """Outlet -> set of hosts, from the sheet's own Publisher links (the aliases R1 accepts)"""
    out = {}
    for r in rows:
        h = host_of(r.get('Publisher link'))
        o = (r.get('Outlet') or '').strip()
        if h and o:
            out.setdefault(o, set()).add(h)
    return out


# ---------- the check ----------
def copy_check(row, page, hosts=None, story_rows=None, held=None, today=None):
    """hosts: {Outlet: {host,...}} (outlet_hosts(sheet rows) + outlet_rules hosts); story_rows: the other rows of this
    row's Story ID; held: {text sha or url: Article ID} of copies already in the library (R6)."""
    reasons, extra = [], {'tags': []}
    rej, flag = [], []
    url = page.get('canonical') or page.get('url') or ''
    ph, lh = host_of(url), host_of(row.get('Publisher link'))
    title = page.get('title') or ''
    h1 = page.get('h1') or ''
    text = page.get('text') or ''
    kind = page.get('kind') or 'html'
    lang = (row.get('Language') or 'English').strip().lower()

    # R1 host
    if kind == 'html' and ph:
        ok_hosts = {lh} | set((hosts or {}).get(row.get('Outlet') or '', set()))
        ok_bases = {base_domain(h) for h in ok_hosts if h}
        if ph not in ok_hosts and base_domain(ph) not in ok_bases:
            rej.append('R1: page host %s is not the Publisher link host %s (another outlet\'s edition)' % (ph, lh or '-'))
            for o in story_rows or []:
                if o.get('Article ID') == row.get('Article ID'):
                    continue
                oh = {host_of(o.get('Publisher link'))} | set((hosts or {}).get(o.get('Outlet') or '', set()))
                if ph in oh or base_domain(ph) in {base_domain(h) for h in oh if h}:
                    extra['file_to'] = o.get('Article ID')
                    break

    # R2 language / script
    want = LANG_SCRIPT.get(lang, '')
    got = script_of(text)
    if want and got and got != want:
        if script_of((row.get('Headline') or '') * 8) == got:
            # the sheet's own headline is in the page's script: the Language cell is what is wrong, not the copy
            flag.append('R2: Language column says %s but the row headline and page are %s script (fix Language)'
                        % (row.get('Language') or 'English', got))
            extra['language_fix'] = got
        else:
            rej.append('R2: page text is %s script but the row Language is %s' % (got, row.get('Language') or 'English'))

    # R3 headline
    heads = [h for h in (row.get('Headline'), row.get('Print headline'), row.get('Translated Headline')) if h]
    best = max([headline_sim(h, t) for h in heads for t in (title, h1) if t] or [0.0])
    shared = max([len(hwords(h) & (hwords(title) | hwords(h1))) for h in heads] or [0])
    slug = slug_words(row.get('Publisher link'))
    slug_ok = bool(slug) and len(slug & (hwords(title) | hwords(h1))) >= max(2, len(slug) // 2)
    lead = nh(text[:1500])
    lead_ok = any(hwords(h) and sum(1 for w in hwords(h) if w in lead) >= 0.5 * len(hwords(h)) for h in heads)
    r3_fail = not (best >= 0.5 or shared >= 2 or slug_ok or lead_ok)
    if r3_fail and heads and (title or h1):
        flag.append('R3: page title "%s" does not match the row headline' % (title or h1)[:80])

    # R4 date
    pd, rd = todate(page.get('published')), todate(row.get('Date'))
    r4_fail = bool(pd and rd and abs((pd - rd).days) > 7)
    if r4_fail:
        flag.append('R4: page date %s is %d days from the row date %s' % (pd, abs((pd - rd).days), rd))
    # a page dated > 7 days off must match the headline strongly (same-topic rewrites share a few words: the 08080 pattern)
    hw = max((hwords(h) for h in heads), key=len, default=set())
    r3_strong = best >= 0.8 or (hw and len(hw & (hwords(title) | hwords(h1))) >= 0.6 * len(hw))
    if r4_fail and (r3_fail or not r3_strong):
        rej.append('R3+R4: another article (date %d days off and the title is not this headline)' % abs((pd - rd).days))

    # R5 size / shape
    w = nwords(text)
    path = urlparse(url).path
    if kind == 'html' and STATION_HOST.search(ph) and '/video/' in path.lower():
        rej.append('R5: station video page (never a copy)')
    elif kind == 'html' and LISTING_PATH.search(path):
        rej.append('R5: listing / archive page')
    else:
        lines = [l for l in (text or '').split('\n') if l.strip()]
        short = sum(1 for l in lines if nwords(l) < 12)
        longp = any(nwords(l) >= 40 for l in lines)
        if w < 60:
            rej.append('R5: under 60 words (teaser / stub)')
        elif len(lines) >= 8 and short / len(lines) > 0.85 and not longp:
            rej.append('R5: mostly short lines, no paragraph of 40+ words (listing)')
        elif w < 150:
            extra['tags'].append('brief')

    # R6 identity of the file
    f = page.get('file') or ''
    if f:
        m = re.match(r'^(nb|pq|ws)(\d{5})([or])?(?:-(s\d{5}))?(?:-[\w]+)?\.\w+$', f)
        suf = {'Original': 'o', 'Reprint': 'r'}.get(row.get('Original or reprint') or '', '')
        if not m or m.group(2) != str(row.get('Article ID') or '') or (m.group(3) or '') != suf \
                or (m.group(4) or '') != (row.get('Story ID') or ''):
            rej.append('R6: file name %s is not this row\'s library name' % f)
    for key in (page.get('sha'), page.get('url')):
        if key and held and key in held and held[key] != row.get('Article ID'):
            rej.append('R6: the same page is already row %s\'s copy (record it in Team note, not File name)' % held[key])
            break

    # R7 NewsBank / ProQuest text on a web row
    if kind in ('nb', 'pq') and (row.get('Publisher link') or '').startswith('http') and \
            'print' not in (row.get('Data Source') or '').lower():
        src = nh(page.get('source_line') or '')
        out = nh(row.get('Outlet') or '')
        if src and out and out.replace('the ', '') not in src:
            rej.append('R7: %s text from "%s" on a web row of %s' % (kind, page.get('source_line'), row.get('Outlet')))

    reasons = rej + flag
    verdict = 'reject' if rej else ('flag' if flag else 'ok')
    return verdict, reasons, extra
