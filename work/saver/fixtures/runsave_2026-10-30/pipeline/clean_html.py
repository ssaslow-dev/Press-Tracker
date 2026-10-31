#!/usr/bin/env python3
"""clean_html.py - the merged saved-page cleaner (T37, agent-code, 2026-10-27).

One cleaner for every saved HTML page: the 3,497 library files the ten cleaning buckets did by hand (T32) and every
page the tracker's Update button / sheet task saves from now on (DECISIONS 2026-10-27 "future TinyFish finds get the
same cleaning"). The rules are data, in clean_rules.json next to this file (generic rules + per-site rules keyed by
host and outlet name); the tracker page runs a JavaScript port of the same algorithm on the same JSON
(code/clean_html.js, embedded in the tracker as the `cleanrules` block). Read build/clean_playbook.md before adding rules.

Scalpel, not a broom: only what is clearly not the article goes (related/more-stories lists, ads, newsletter/subscribe
/paywall prompts, cookie banners, nav, share widgets, comments, footers, promo boxes). When in doubt, keep.

Algorithm (identical in the JS port):
 1. Parse; split the page into text BLOCKS: runs of text inside one block-level element, split at <br>.
 2. Header lines (the library's first <div>: "Outlet · date", URL, "Saved …"): with the sheet row given, a line whose
    value equals the sheet is removed; a line that differs is kept and reported as a conflict; a line for a blank
    sheet cell is kept and reported as a fill; "Saved …" lines are kept.
 3. Rules, in this order, mark blocks for removal: drop (elements by tag/class/id), head (everything before the
    article's h1), cut (start..end), tail (from a marker to the end), section (a heading + the teaser lines after it),
    kill (whole block), strip (part of a block). Generic rules apply to every page, site rules to pages of that site.
    Per-file overrides (clean_overrides.json, library files only) replay the buckets' one-off decisions.
 4. Safety: a block of >= 40 words of prose is kept (flag long_block) unless the rule allows long removals; if more
    than 35% of the words would go the page is left as it was (flag big_removal) unless allowed; Gabriel (incl. other
    scripts: 가브리엘, Габриэл, גבריאל, 加布里埃尔/爾 …) is checked before and after: if every mention would be removed
    the result says gabriel_outside_article (library: the blocks naming him are kept and the file flagged; finds: the
    sheet task SKIPs the find, DECISIONS 2026-10-27).
 5. Error page check (finds): no body / under 60 words / no Gabriel at all / paywall-login-404 stub -> error.

Usage:
  python3 -I clean_html.py IN.html OUT.html [--url U] [--outlet O] [--sheet-json ROW.json] [--report R.json]
  python3 -I clean_html.py --batch LIST.tsv --out-dir DIR --report R.json [--overrides clean_overrides.json]
     (LIST.tsv: stem<TAB>input path<TAB>url<TAB>outlet; the sheet row may be given as a JSON column 5)
As a module:  from clean_html import clean_page, page_check
"""
import argparse, hashlib, json, os, re, sys, unicodedata

from bs4 import BeautifulSoup, NavigableString, Tag, Comment, Doctype, ProcessingInstruction, Declaration, CData

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = '1.0'

BLOCK_TAGS = {'address', 'article', 'aside', 'blockquote', 'body', 'caption', 'center', 'dd', 'details', 'dialog', 'dir',
              'div', 'dl', 'dt', 'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
              'header', 'hgroup', 'hr', 'html', 'li', 'main', 'menu', 'nav', 'ol', 'p', 'pre', 'section', 'summary',
              'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'ul', 'legend', 'option', 'select', 'button'}
SKIP_TAGS = {'script', 'style', 'template', 'noscript', 'head', 'title', 'meta', 'link', 'iframe', 'object', 'svg',
             'math', 'canvas', 'audio', 'video', 'source', 'track', 'textarea', 'input'}
WS = re.compile('[ \t\n\r\f\v\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+')
CJK = re.compile('[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]')
WORD = re.compile('[A-Za-z0-9\u00c0-\u024f\u0370-\u03ff\u0400-\u04ff\u0530-\u058f\u0590-\u05ff\u0600-\u06ff\u0e00-\u0e7f\u1e00-\u1eff]+')
HDR_OUTLET_DATE = re.compile(r'^(.{1,140}?) · ((?:\d{4}(?:-\d\d){0,2})|undated|n\.d\.)$')
HDR_URL = re.compile(r'^https?://\S+$')
HDR_SAVED = re.compile(r'^Saved \d{4}-\d\d-\d\d\b.*$')


def norm(t):
    return WS.sub(' ', t or '').strip()


def nwords(t):
    """Words for the removal checks: Latin/Cyrillic/… words + one per CJK/kana/hangul character."""
    t = t or ''
    return len(WORD.findall(CJK.sub(' ', t))) + len(CJK.findall(t))


def h12(t):
    return hashlib.sha1(norm(t).encode('utf-8')).hexdigest()[:12]


def img_key(src):
    """key of an image for the img rules: sha1 of its src (data: URIs included), 12 hex"""
    return hashlib.sha1((src or '').replace('&amp;', '&').strip().encode('utf-8')).hexdigest()[:12]


def load_rules(path=None):
    return json.load(open(path or os.path.join(HERE, 'clean_rules.json'), encoding='utf-8'))


def load_overrides(path=None):
    p = path or os.path.join(HERE, 'clean_overrides.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


_RX = {}


def rx(p):
    """Rule patterns are JS-compatible regex sources; a leading (?i) = case-insensitive (the JS port maps it to 'i')."""
    r = _RX.get(p)
    if r is None:
        flags = 0
        src = p
        if src.startswith('(?i)'):
            flags, src = re.I, src[4:]
        r = _RX[p] = re.compile(src, flags)
    return r


def full(p, t):
    return rx(p).fullmatch(t) is not None


def lkey(t):
    """bucket-10 style key: lowercase, digit runs -> #"""
    return re.sub(r'\d+', '#', t.lower())


# ---------------------------------------------------------------- blocks
class Block:
    __slots__ = ('i', 'nodes', 'text', 'tag', 'el', 'hdr', 'why', 'keep_why', 'pat')

    def __init__(self, i, nodes, text, tag, el):
        self.i, self.nodes, self.text, self.tag, self.el = i, nodes, text, tag, el
        self.hdr = None      # header line kind: 'od' (outlet · date), 'url', 'saved'
        self.why = None      # rule id that removes it
        self.keep_why = None
        self.pat = None      # the pattern that matched (for the log and the learner)


def is_el(n):
    return isinstance(n, Tag)


def is_text(n):
    return isinstance(n, NavigableString) and not isinstance(n, (Comment, Doctype, ProcessingInstruction, Declaration, CData))


def node_text(n):
    if is_text(n):
        return str(n)
    if is_el(n):
        if n.name in SKIP_TAGS:
            return ''
        return ''.join(node_text(c) for c in n.children)
    return ''


def has_block(el, cache):
    k = id(el)
    if k in cache:
        return cache[k]
    r = False
    for c in el.children:
        if is_el(c) and c.name not in SKIP_TAGS and (c.name in BLOCK_TAGS or c.name == 'br' or has_block(c, cache)):
            r = True
            break
    cache[k] = r
    return r


def extract_blocks(root):
    """Blocks in document order. Same walk as blocksOf() in clean_html.js."""
    out, cache = [], {}

    def flush(run, parent):
        t = norm(''.join(node_text(n) for n in run))
        if t:
            out.append(Block(len(out), list(run), t, parent.name if is_el(parent) else '', parent))
        run.clear()

    def walk(el):
        run = []
        for c in list(el.children):
            if is_text(c):
                run.append(c)
            elif is_el(c):
                if c.name == 'br':
                    run.append(c)
                    flush(run, el)
                elif c.name in SKIP_TAGS:
                    run.append(c)
                elif c.name in BLOCK_TAGS or has_block(c, cache):
                    flush(run, el)
                    walk(c)
                else:
                    run.append(c)
        flush(run, el)

    walk(root)
    return out


def body_of(soup):
    return soup.body or soup.find('html') or soup


def mark_header(blocks, body):
    """Header lines: blocks inside the first element child of <body> when it is a <div> holding the library's
    metadata lines."""
    first = next((c for c in body.children if is_el(c)), None)
    if first is None or first.name != 'div':
        return
    inside = [b for b in blocks if b.el is first]
    kinds = []
    for b in inside:
        k = 'saved' if HDR_SAVED.match(b.text) else 'url' if HDR_URL.match(b.text) else 'od' if HDR_OUTLET_DATE.match(b.text) else None
        kinds.append(k)
    if any(kinds) and all(kinds):
        for b, k in zip(inside, kinds):
            b.hdr = k


# ---------------------------------------------------------------- rules
def site_rules(rules, url='', outlet=''):
    host = re.sub(r'^www\.', '', re.sub(r'^[a-z]+://', '', (url or '').strip().lower()).split('/')[0].split(':')[0])
    on = norm_outlet(outlet)
    by_host, by_outlet = [], []
    for key, s in rules.get('sites', {}).items():
        if host and any(host == h or host.endswith('.' + h) for h in s.get('hosts', [])):
            by_host.append(key)
        elif on and on in [norm_outlet(o) for o in s.get('outlets', [])]:
            by_outlet.append(key)
    # the page's own site wins; the outlet name is used only when no site matches the address
    return by_host or by_outlet


def norm_outlet(s):
    s = unicodedata.normalize('NFKD', (s or '')).lower().strip()
    s = re.sub(r'[̀-ͯ]', '', s)
    s = re.sub(r',\s*the$|^the\s+', '', s)
    return re.sub(r'[^a-z0-9\u0080-￿]+', ' ', s).strip()


def merged(rules, keys):
    """generic + every matching site's rules, each entry tagged with its source for the log."""
    g = rules.get('generic', {})
    m = {k: [(p, 'generic') for p in g.get(k, [])] for k in ('kill', 'lkill', 'tail', 'ltail', 'strip', 'section', 'cut', 'drop', 'img')}
    m['head'] = []
    m['allow_long'] = False
    m['allow_big'] = False
    skip = set()
    for key in keys:
        s = rules['sites'][key]
        for k in ('kill', 'lkill', 'tail', 'ltail', 'strip', 'section', 'cut', 'drop', 'img'):
            m[k] += [(p, key) for p in s.get(k, [])]
        if s.get('head'):
            m['head'].append((s['head'], key))
        m['allow_long'] = m['allow_long'] or bool(s.get('allow_long'))
        m['allow_big'] = m['allow_big'] or bool(s.get('allow_big'))
        skip |= set(s.get('skip_generic', []))
    if skip:
        for k in ('kill', 'tail', 'strip', 'section', 'drop'):
            m[k] = [(p, src) for p, src in m[k] if not (src == 'generic' and p in skip)]
    return m


def drop_match(el, d):
    """d = {"tag": regex?, "attr": "class"|"id"|…, "re": regex} (all given parts must match)."""
    if d.get('tag') and not full(d['tag'], el.name or ''):
        return False
    if d.get('attr'):
        v = el.get(d['attr'])
        if v is None:
            return False
        v = ' '.join(v) if isinstance(v, list) else str(v)
        if not rx(d['re']).search(v):
            return False
    return True


def inside(el, anc):
    p = el
    while p is not None:
        if p is anc:
            return True
        p = p.parent
    return False


def block_in(b, el):
    return all(inside(n, el) for n in b.nodes)


def is_teaser(t, maxw):
    return nwords(t) <= maxw and not re.search(r'[.!?。！？]["”’)]?$', t)


def decide(blocks, m, ov):
    """Mark blocks for removal (b.why = rule id). Returns the strip edits [(block, pattern, src)]."""
    body = [b for b in blocks if not b.hdr]
    if not body:
        return []
    # drop: element rules
    for d, src in m['drop']:
        for b in body:
            if b.why:
                continue
            p = b.el
            while p is not None and getattr(p, 'name', None) not in (None, '[document]', 'body', 'html'):
                if drop_match(p, d):
                    b.why, b.pat = 'drop:' + src, json.dumps(d)
                    break
                p = p.parent
            if not b.why:
                for n in b.nodes:
                    if is_el(n) and drop_match(n, d) and node_text(n).strip() and norm(node_text(n)) == b.text:
                        b.why, b.pat = 'drop:' + src, json.dumps(d)
                        break
    # head: everything before the article's first h1 (site rule) / before a given block (file override)
    if ov.get('head'):
        j = next((k for k, b in enumerate(body) if h12(b.text) == ov['head']), None)
        if j:
            for b in body[:j]:
                if not b.why:
                    b.why, b.pat = 'head:file', ov['head']
    for h, src in m['head']:
        j = next((k for k, b in enumerate(body) if b.tag == 'h1'), None) if h == 'h1' else \
            next((k for k, b in enumerate(body) if full(h, b.text)), None)
        if j:
            for b in body[:j]:
                if not b.why:
                    b.why, b.pat = 'head:' + src, h
    # where the article starts: the tail and section rules never fire on or before it
    start = next((k for k, b in enumerate(body) if b.tag == 'h1' and not b.why), 0)
    # cut: [start, end|null, include_end]
    for c, src in m['cut']:
        a_re, z_re, inc = c[0], c[1], (c[2] if len(c) > 2 else False)
        k = start + 1 if start else 0
        while k < len(body):
            if full(a_re, body[k].text):
                z = None
                if z_re:
                    z = next((q for q in range(k + 1, len(body)) if full(z_re, body[q].text)), None)
                    if z is None:
                        k += 1
                        continue
                end = len(body) if z is None else (z + 1 if inc else z)
                for b in body[k:end]:
                    if not b.why:
                        b.why, b.pat = 'cut:' + src, json.dumps(c, ensure_ascii=False)
                k = end
            else:
                k += 1
    # tail: first marker after the start -> to the end
    cut_at = None
    for k in range(start + 1 if start else 1, len(body)):
        t = body[k].text
        lk = None
        for p, src in m['tail']:
            if full(p, t):
                cut_at = (k, 'tail:' + src, p)
                break
        if cut_at is None and m['ltail']:
            lk = lkey(t)
            for p, src in m['ltail']:
                if full(p, lk):
                    cut_at = (k, 'tail:' + src, 'L:' + p)
                    break
        if cut_at:
            break
    if ov.get('tail'):
        k = next((k for k, b in enumerate(body) if h12(b.text) == ov['tail']), None)
        if k is not None and (cut_at is None or k < cut_at[0]):
            cut_at = (k, 'tail:file', ov['tail'])
    if cut_at:
        for b in body[cut_at[0]:]:
            if not b.why:
                b.why, b.pat = cut_at[1], cut_at[2]
    # section: heading + following teaser lines
    for s, src in m['section']:
        pat, maxw = (s, 25) if isinstance(s, str) else (s[0], s[1])
        k = start + 1 if start else 0
        while k < len(body):
            if not body[k].why and full(pat, body[k].text):
                body[k].why, body[k].pat = 'section:' + src, pat
                q = k + 1
                while q < len(body) and is_teaser(body[q].text, maxw) and not body[q].hdr:
                    if not body[q].why:
                        body[q].why, body[q].pat = 'section:' + src, pat
                    q += 1
                k = q
            else:
                k += 1
    # kill: whole blocks
    for b in body:
        if b.why:
            continue
        for p, src in m['kill']:
            if full(p, b.text):
                b.why, b.pat = 'kill:' + src, p
                break
        if not b.why and m['lkill']:
            lk = lkey(b.text)
            for p, src in m['lkill']:
                if full(p, lk):
                    b.why, b.pat = 'kill:' + src, 'L:' + p
                    break
    if ov.get('kill_nth'):   # the n-th block with this text (when the same text is also kept elsewhere)
        seen = {}
        want = {(hh, n) for hh, n in ov['kill_nth']}
        for b in body:
            hh = h12(b.text)
            n = seen.get(hh, 0)
            seen[hh] = n + 1
            if not b.why and (hh, n) in want:
                b.why, b.pat = 'kill:file', hh
    if ov.get('kill'):
        ks = set(ov['kill'])
        for b in body:
            if not b.why and h12(b.text) in ks:
                b.why, b.pat = 'kill:file', h12(b.text)
    # strip: parts of blocks
    edits = []
    for b in body:
        if b.why:
            continue
        for p, src in m['strip']:
            if rx(p).search(b.text):
                edits.append((b, p, src))
    for hb, p in ov.get('strip', []):
        for b in body:
            if not b.why and h12(b.text) == hb:
                edits.append((b, p, 'file'))
    return edits


# INCL-v1 (2026-10-28): Latin form case-insensitive (CC captions "JESSE GABRIEL", results tables, all-caps heads),
# hyphenated line breaks ("Ga-\nbriel"); "San Gabriel" (any case) and Gabrielle/Gabriela still excluded; 加布里爾/尔 added
GAB_DEFAULT = (r'(?<![A-Za-z])(?<![Ss][Aa][Nn] )[Gg][Aa](?:-\s*)?[Bb][Rr][Ii][Ee][Ll](?![A-Za-z])|가브리엘|Габриэл|Габриел|גבריאל|'
               r'加布里埃[尔爾]|加布尔|加布里爾|加布里尔|蓋博|盖博|جسی گابریل|گابریل|Ջեսի Գաբրիել|Գաբրիել')


def gab_re(rules):
    return rx(rules.get('gabriel') or GAB_DEFAULT)


def strip_block(b, pattern):
    """Remove the parts of a block matching pattern. A whole inline element whose text matches goes; otherwise the
    match is found in the block's text (its text nodes joined, so a match may span several inline elements) and those
    characters are cut from the text nodes they sit in."""
    r = rx(pattern)
    done = False
    for n in list(b.nodes):
        if is_el(n) and n.parent is not None and n.name not in SKIP_TAGS and norm(node_text(n)) and \
                r.fullmatch(norm(node_text(n))):
            n.extract()
            done = True
    if done:
        b.nodes = [n for n in b.nodes if n.parent is not None]
        return True
    texts = []

    def collect(n):
        if is_text(n):
            texts.append(n)
        elif is_el(n) and n.name not in SKIP_TAGS:
            for c in n.children:
                collect(c)
    for n in b.nodes:
        if n.parent is not None:
            collect(n)
    raw = ''.join(str(t) for t in texts)
    spans = [(m.start(), m.end()) for m in r.finditer(raw) if m.end() > m.start()]
    if not spans:
        return False
    pos = 0
    for t in texts:
        s0 = str(t)
        a, z = pos, pos + len(s0)
        pos = z
        keep = []
        for k, ch in enumerate(s0):
            g = a + k
            if not any(x <= g < y for x, y in spans):
                keep.append(ch)
        new = ''.join(keep)
        if new != s0:
            nn = NavigableString(new)
            t.replace_with(nn)
            b.nodes = [nn if x is t else x for x in b.nodes]
            done = True
    return done


# ---------------------------------------------------------------- header lines vs sheet
def norm_url(u):
    """Mirror of build_data.py / sheet_task.py norm_url."""
    u = str(u if u is not None else '').strip()
    if not u.startswith('http'):
        return ''
    u = re.sub(r'^https?://(www\.)?', '', u.lower()).split('#')[0]
    host = u.split('/')[0]
    if not re.search(r'newsbank|oclc|google\.|proquest', host):
        u = u.split('?')[0]
    return u.rstrip('/')


def header_decision(b, sheet, aliases=None):
    """-> ('remove'|'keep'|'fill'|'conflict', detail). aliases: header outlet name -> sheet outlet names that are
    the same outlet (rules['outlet_aliases'], normalized names)."""
    if b.hdr == 'saved':
        return 'keep', 'saved line (no column)'
    if not sheet:
        return 'keep', 'no sheet row'
    if b.hdr == 'url':
        links = [sheet.get(c, '') for c in ('Publisher link', 'NewsBank article link', 'ProQuest link', 'Link')]
        links = [norm_url(x) for x in links if x]
        if not links:
            return 'fill', {'column': 'Publisher link', 'value': b.text}
        return ('remove', 'url = sheet') if norm_url(b.text) in links else ('conflict', {'column': 'Publisher link', 'sheet': sheet.get('Publisher link', ''), 'file': b.text})
    m = HDR_OUTLET_DATE.match(b.text)
    o, d = m.group(1).strip(), m.group(2)
    so, sd = str(sheet.get('Outlet', '') or ''), str(sheet.get('Date', '') or '')[:10]
    if not so or not sd:
        return 'fill', {'column': 'Outlet' if not so else 'Date', 'value': o if not so else d}
    same = norm_outlet(o) == norm_outlet(so) or norm_outlet(so) in (aliases or {}).get(norm_outlet(o), [])
    if same and d in ('undated', 'n.d.'):
        return 'remove', 'outlet = sheet, header carries no date'   # DATES-v1: an undated header never contradicts the sheet
    if same and (d == sd or (len(d) < 10 and sd.startswith(d))):
        return 'remove', 'outlet+date = sheet'
    return 'conflict', {'column': 'Outlet/Date', 'sheet': f'{so} · {sd}', 'file': b.text}


# ---------------------------------------------------------------- main entry
def clean_page(html, url='', outlet='', sheet=None, rules=None, overrides=None, stem=None, mode='library'):
    """Clean one page. Returns a dict:
      html        the cleaned page (the input unchanged when nothing is removed or a safety check blocks it)
      status      'cleaned' | 'unchanged' | 'flagged' (kept as is, see flags) | 'kept' (override: never clean)
      flags       list: big_removal, long_block, gabriel_outside_article, no_gabriel
      removed     [{rule, text}] blocks removed;  stripped [{rule, pattern, text}]
      header      {removed: [...], kept: [...], fills: [...], conflicts: [...]}
      words_before, words_after, gabriel_before, gabriel_after
    mode 'library' (saved library file) or 'find' (a new page from the Update button / sheet task)."""
    rules = rules if rules is not None else load_rules()
    ov = (overrides or {}).get(stem or '', {}) if overrides else {}
    res = {'version': VERSION, 'status': 'unchanged', 'flags': [], 'removed': [], 'stripped': [],
           'header': {'removed': [], 'kept': [], 'fills': [], 'conflicts': []}, 'sites': []}
    soup = BeautifulSoup(html, 'html.parser')
    body = body_of(soup)
    img_fixed = fix_imgs(body, url) if mode == 'find' else 0   # PHOTOS-v2 F1: new saves keep a fetchable photo URL
    if img_fixed:
        res['img_fixed'] = img_fixed
    blocks = extract_blocks(body)
    mark_header(blocks, body)
    G = gab_re(rules)
    all_text = ' '.join(b.text for b in blocks)
    res['words_before'] = nwords(' '.join(b.text for b in blocks if not b.hdr))
    res['gabriel_before'] = bool(G.search(all_text))
    if ov.get('keep'):
        res.update(status='kept', html=html, words_after=res['words_before'], gabriel_after=res['gabriel_before'])
        return res
    keys = site_rules(rules, url, outlet)
    res['sites'] = keys
    m = merged(rules, keys)
    limits = rules.get('limits', {})
    long_w = limits.get('long_block_words', 40)
    max_frac = limits.get('max_removed_frac', 0.35)
    allow_long = m['allow_long'] or bool(ov.get('force')) or bool(ov.get('allow_long'))
    allow_big = m['allow_big'] or bool(ov.get('force')) or bool(ov.get('allow_big'))
    edits = decide(blocks, m, ov)
    safe = set()   # removals exempt from the safety checks (find mode)
    if mode == 'find' and rules.get('find'):
        outside_phase(blocks, rules['find'], G)   # comment sections / end-of-page related lists: outside the article
        # T45: a tail cut that starts after the last paragraph naming Gabriel is safe: it is exempt from the 40-word and
        # 35% checks (TownNews 'Tags', The Hill 'More News', KQED player dump …)
        _body = [b for b in blocks if not b.hdr]
        _lg = max([k for k, b in enumerate(_body) if gab_prose(G, b.text)] or [-1])
        if _lg >= 0:
            for k, b in enumerate(_body):
                if k > _lg and b.why and (b.why.startswith('tail:') or b.why.startswith('find:tail_safe')):
                    safe.add(id(b))
    # safety: long prose blocks are kept unless the rule set allows long removals
    for b in blocks:
        if b.why and not allow_long and not b.why.endswith(':file') and b.why != 'find:outside' and id(b) not in safe and nwords(b.text) >= long_w and \
                re.search(r'[.!?。！？]', b.text):
            b.keep_why, b.why = 'long_block:' + b.why, None
            if 'long_block' not in res['flags']:
                res['flags'].append('long_block')
    # Gabriel: if every mention would go, keep the blocks naming him and flag
    kept_text = ' '.join(b.text for b in blocks if not b.why and not b.hdr)
    if res['gabriel_before'] and G.search(' '.join(b.text for b in blocks if not b.hdr)) and not G.search(kept_text):
        res['flags'].append('gabriel_outside_article')
        res['gabriel_outside'] = [{'rule': b.why, 'text': b.text[:300]} for b in blocks if b.why and G.search(b.text)]
        if mode == 'library' and not ov.get('gabriel_ok'):
            for b in blocks:
                if b.why and G.search(b.text):
                    b.keep_why, b.why = 'gabriel:' + b.why, None
    if not res['gabriel_before']:
        res['flags'].append('no_gabriel')
    # header lines
    hdr_remove = []
    for b in blocks:
        if b.hdr:
            act, det = header_decision(b, sheet, rules.get('outlet_aliases'))
            if ov.get('hdr_keep') and h12(b.text) in ov['hdr_keep']:
                act = 'keep'
            elif ov.get('hdr_remove') and h12(b.text) in ov['hdr_remove']:
                act, det = 'remove', 'file override'
            if act == 'remove':
                hdr_remove.append(b)
                res['header']['removed'].append(b.text)
            else:
                res['header']['kept'].append(b.text)
                if act == 'fill':
                    res['header']['fills'].append(det)
                elif act == 'conflict':
                    res['header']['conflicts'].append(det)
    # size check
    gone = sum(nwords(b.text) for b in blocks if b.why and not b.hdr and b.why != 'find:outside' and id(b) not in safe)
    if res['words_before'] and gone / res['words_before'] > max_frac and not allow_big:
        res['flags'].append('big_removal')
        res['would_remove'] = round(gone / res['words_before'], 3)
        for b in blocks:
            if b.why and b.why != 'find:outside' and id(b) not in safe:
                b.keep_why, b.why = 'big_removal:' + b.why, None
        edits = []
    # TinyFish-format pages (mode 'find', and library re-fetches): generic rules for the page chrome around the
    # article (agent-retry post-pass, folded in). Runs after the safety checks, removes whole blocks only, never a
    # block naming Gabriel ("San Gabriel" is not a mention).
    if mode == 'find' and rules.get('find'):
        _title = str((sheet or {}).get('Headline') or '') or (soup.title.get_text(' ') if soup.title else '')
        find_phase(blocks, rules['find'], ov, G, res, _title)
    # apply
    changed = False
    parents = []
    # removed teaser items take their thumbnails: media inside the element of a removed tail/cut/section block, when
    # every block in that element is removed
    tail_media = []
    kept_els = set()
    for b in blocks:
        if not b.why and b.el is not None:
            p = b.el
            while p is not None:
                kept_els.add(id(p))
                p = p.parent
    for b in blocks:
        if b.why and b.why.split(':')[0] in ('tail', 'cut', 'section') and b.el is not None and \
                b.el.name not in ('body', 'html', 'main', 'article') and id(b.el) not in kept_els:
            tail_media += [e for e in b.el.find_all(MEDIA_TAGS)]
    for b in blocks:
        if b.why:
            res['removed'].append({'rule': b.why, 'text': b.text[:300]})
            keep_media = b.why.startswith('kill:')
            for n in b.nodes:
                if n.parent is None:
                    continue
                if keep_media and is_el(n) and (n.name in MEDIA_TAGS or n.find(MEDIA_TAGS)):
                    # a UI line next to a photo ("Press enter or click to view image in full size"): the photo stays
                    if n.name not in MEDIA_TAGS:
                        for t in [d for d in n.descendants if is_text(d)]:
                            t.extract()
                    continue
                parents.append(n.parent)
                n.extract()
            changed = True
    for e in tail_media:
        if e.parent is not None:
            parents.append(e.parent)
            e.extract()
            changed = True
    for b in hdr_remove:
        for n in b.nodes:
            parents.append(n.parent)
            n.extract()
        changed = True
    # images: ads and promo graphics known by their src (img rules; file overrides)
    imgs = {k: src for k, src in m['img']}
    nth = {}
    for k in ov.get('img', []):
        if isinstance(k, list):          # [key, [occurrences]]: only those copies of a repeated image
            nth[k[0]] = set(k[1])
            imgs[k[0]] = 'file'
        else:
            imgs[k] = 'file'
    if imgs:
        seen = {}
        for im in body.find_all('img'):
            k = img_key(im.get('src', ''))
            n = seen.get(k, 0)
            seen[k] = n + 1
            if k in nth and n not in nth[k]:
                continue
            if k in imgs and im.parent is not None:
                res['removed'].append({'rule': 'img:' + imgs[k], 'text': '[img ' + k + ']'})
                parents.append(im.parent)
                im.extract()
                changed = True
    for b, p, src in edits:
        if b.why:
            continue
        before = b.text
        if strip_block(b, p):
            res['stripped'].append({'rule': 'strip:' + src, 'pattern': p, 'text': before[:300]})
            changed = True
    if mode == 'find' and (rules.get('find') or {}).get('tidy') and tidy_empty(body):
        changed = True
    changed = changed or bool(img_fixed)
    if changed:
        prune_empty(parents)
        out = str(soup)
        res['status'] = 'cleaned'
    else:
        out = html
        res['status'] = 'flagged' if res['flags'] and any(f in res['flags'] for f in ('big_removal',)) else 'unchanged'
    try:   # MEDIAGATE-v1: no <track> and no svg/other disallowed data: media in a saved page
        import media_gate as _MG
        out = _MG.clean_html(out)
    except ImportError:
        pass
    res['html'] = out
    after = extract_blocks(body_of(BeautifulSoup(out, 'html.parser'))) if changed else blocks
    res['words_after'] = nwords(' '.join(b.text for b in after if not (b.hdr if not changed else HDR_SAVED.match(b.text))))
    res['gabriel_after'] = bool(G.search(' '.join(b.text for b in after)))
    if res['status'] == 'cleaned' and ('long_block' in res['flags'] or 'gabriel_outside_article' in res['flags']):
        res['status'] = 'cleaned'   # cleaned, with the kept blocks listed in flags
    return res


LAZY_SRC = ('data-src', 'data-lazy-src', 'data-original', 'data-gl-src', 'data-hi-res-src', 'data-full-src', 'data-orig-file',
            'data-large-file', 'data-url')
LAZY_SET = ('data-srcset', 'data-lazy-srcset', 'data-gl-srcset')


def fix_imgs(body, url=''):
    """PHOTOS-v2 F1 (agent-v20-photos 2026-10-28), find mode only: give every <img> of a new save a src the save step can
    fetch (img_embed.embed_page). A placeholder or empty src takes the lazy-load URL (data-src …) or the largest srcset
    entry; a src that is the article URL + a width ("…/article-slug/864", KTLA / Mother Jones saves) is replaced the same
    way (or dropped with no alternative); relative src/srcset become absolute against the page URL. Query strings (Arc
    resizer ?auth=…, cloudinary params) are kept exactly as given. Returns the number of tags changed."""
    from urllib.parse import urljoin
    n = 0
    page = (url or '').split('#')[0].split('?')[0].rstrip('/')
    for im in body.find_all('img'):
        src = (im.get('src') or '').strip()
        before = dict(im.attrs)
        mangled = bool(page) and re.match(re.escape(page) + r'/\d{2,4}/?$', src.split('?')[0] or '')
        placeholder = not src or src.startswith('data:image/gif') or src.startswith('data:image/svg') or src == 'about:blank'
        if placeholder or mangled:
            alt = next((im.get(a).strip() for a in LAZY_SRC if (im.get(a) or '').strip()), '')
            if not alt:
                ss = next((im.get(a) for a in ('srcset',) + LAZY_SET if (im.get(a) or '').strip()), '')
                best = None
                for part in re.split(r',\s+(?=\S)', ss.strip()) if ss else []:
                    bits = part.split()
                    if not bits:
                        continue
                    w = re.match(r'(\d+)w$', bits[1]) if len(bits) > 1 else None
                    w = int(w.group(1)) if w else 0
                    if best is None or (w <= 1000 and w > best[1]) or (best[1] > 1000 and w < best[1]):
                        best = (bits[0].rstrip(','), w)
                alt = best[0] if best else ''
            if alt:
                im['src'] = alt
            elif mangled:
                del im['src']
        for a in ('src',) + LAZY_SRC:
            v = (im.get(a) or '').strip()
            if url and v and not re.match(r'^(?:[a-z][a-z0-9+.-]*:|//)', v, re.I):
                im[a] = urljoin(url, v)
        for a in ('srcset',) + LAZY_SET:
            v = im.get(a)
            if url and v and re.search(r'(?:^|,\s+)(?!(?:https?:)?//|data:)\S', v):
                im[a] = ', '.join(' '.join([urljoin(url, p.split()[0])] + p.split()[1:]) for p in re.split(r',\s+(?=\S)', v.strip()) if p.split())
        if dict(im.attrs) != before:
            n += 1
    return n


def gab_prose(G, t):
    """a paragraph naming Gabriel (not a tag, not a script/JSON dump that repeats the page)"""
    return bool(G.search(t)) and 5 < nwords(t) <= 1500 and not re.match(r'^\s*(window\.|var |\{|\[)', t)


def outside_phase(blocks, f, G=None):
    """rules['find']: a comment section (marker -> end of page) or an end-of-page related/more-stories list (marker ->
    end, only when every block after it is teaser-sized) is outside the article. Removed even when it names Gabriel,
    so a page naming him only there is flagged gabriel_outside_article (the find is skipped).
    comments_strong ("17 thoughts on ...", "Leave a Reply", "Comments are closed."): anywhere after 150 words of text;
    comments / related (bare "Comments", "Related", "More stories" ...): only in the second half of the page; a related
    list only when nothing after it is long and at least half of it is short lines."""
    art = [b for b in blocks if not b.hdr]
    if not art:
        return
    h1 = next((i for i, b in enumerate(art) if b.tag == 'h1'), 0)
    maxw = f.get('teaser_words', 70)
    minpos = f.get('min_position', 0.5)
    minw = f.get('min_words_before', 150)
    # T45 tail_safe: markers (Tags, Post a comment as Guest, Related Topics, KQED player …) cut to the end when every
    # paragraph naming Gabriel is above them
    if G is not None and f.get('tail_safe'):
        lg = max([k for k, b in enumerate(art) if gab_prose(G, b.text)] or [-1])
        if lg >= 0:
            ts = next((k for k in range(lg + 1, len(art)) if any(full(p, art[k].text) for p in f['tail_safe'])), None)
            if ts is not None:
                for b in art[ts:]:
                    if not b.why or b.why.startswith('kill:'):
                        b.why, b.pat = 'find:tail_safe', art[ts].text[:80]
    for i in range(h1 + 1 if h1 else 1, len(art)):
        t = art[i].text
        strong = any(full(p, t) for p in f.get('comments_strong', []))
        weak = not strong and any(full(p, t) for p in f.get('comments', []))
        rel = not strong and not weak and any(full(p, t) for p in f.get('related', []))
        if not (strong or weak or rel):
            continue
        if nwords(' '.join(b.text for b in art[:i] if not b.why)) < minw:
            continue
        if (weak or rel) and i < minpos * len(art):
            continue
        if rel:   # a teaser list: nothing long after it, and at least half of it short lines (headlines, dates, "Read more")
            rest = [nwords(b.text) for b in art[i + 1:]]
            if not rest or max(rest) > maxw or sum(1 for n in rest if n <= f.get('short_words', 6)) < 0.5 * len(rest):
                continue
        for b in art[i:]:
            if not b.why or b.why.startswith('kill:'):
                b.why, b.pat = 'find:outside', t[:80]
        return


def _simt(a, b):
    """headline similarity: 1 when one contains the other (and they are of similar length), else shared-word Jaccard"""
    a, b = norm_outlet(a), norm_outlet(b)
    if not a or not b:
        return 0
    if a in b or b in a:
        return 1.0 if min(len(a), len(b)) >= 0.6 * max(len(a), len(b)) else 0.8
    A, B = set(a.split()), set(b.split())
    return len(A & B) / len(A | B)


def article_h1(art, title):
    """T45: the article's h1 = the one matching the headline/title, else the first h1. No head cut when the h1 sits
    below the article (over 300 words and a quarter of the page before it), or when an unmatched h1 comes after
    article prose (a block of 30+ words with a sentence end)."""
    h1s = [i for i, b in enumerate(art) if b.tag == 'h1']
    if not h1s:
        return None
    best = max(h1s, key=lambda i: _simt(art[i].text, title)) if title else h1s[0]
    matched = bool(title) and _simt(art[best].text, title) >= 0.6
    ah = best if matched else h1s[0]
    before = sum(nwords(b.text) for b in art[:ah])
    total = sum(nwords(b.text) for b in art) or 1
    if before > 300 and before > 0.25 * total:        # an h1 below the article (republish box, sidebar)
        return None
    if not matched and any(nwords(b.text) >= 30 and re.search(r'[.!?。！？]', b.text) for b in art[:ah]):
        return None                                    # an unmatched h1 (subhead) after the opening paragraphs
    return ah


def find_phase(blocks, f, ov, G, res, title=''):
    """rules['find']: head 'h1' (everything before the article's first h1; file overrides find_start / find_keephead),
    tail markers, kill patterns, the title repeated just below the h1. Blocks naming Gabriel are kept."""
    art = [b for b in blocks if not b.hdr and not b.why]
    if not art:
        return
    drop = {}
    h1s = [i for i, b in enumerate(art) if b.tag == 'h1']
    ah = article_h1(art, title)
    if ov.get('find_start'):
        si = next((i for i, b in enumerate(art) if b.text.startswith(ov['find_start'])), None)
        if si is not None:
            for i in range(si):
                if not (h1s and (i == h1s[0] or (i == h1s[0] + 1 and art[i].text.startswith('By ')))):
                    drop[i] = 'find:head'
    elif ah is not None and f.get('head') == 'h1':
        for i in range(ov.get('find_keephead', 0), ah):
            drop[i] = 'find:head'
    first = ah if ah is not None else 0
    for sec in f.get('section', []):   # T45: [heading, max words, max blocks]: a heading + the short teaser lines after it
        for i, b in enumerate(art):
            if full(sec[0], b.text):
                drop.setdefault(i, 'find:section')
                for k in range(i + 1, min(len(art), i + 1 + sec[2])):
                    if nwords(art[k].text) > sec[1]:
                        break
                    drop.setdefault(k, 'find:section')
    ti = next((i for i, b in enumerate(art) if i > first and any(full(p, b.text) for p in f.get('tail', []))), None)
    if ti is not None:
        for i in range(ti, len(art)):
            drop.setdefault(i, 'find:tail')
    rt = f.get('repeat_title', 0)
    for i, b in enumerate(art):
        if any(full(p, b.text) for p in f.get('kill', [])):
            drop.setdefault(i, 'find:kill')
        if rt and ah is not None and i != ah and b.text == art[ah].text and i < ah + rt:
            drop.setdefault(i, 'find:title')
    kept = []
    for i, why in sorted(drop.items()):
        if f.get('protect_gabriel', True) and G.search(art[i].text):
            kept.append(art[i].text[:120])
            continue
        art[i].why, art[i].pat = why, why
    if kept:
        res['find_kept_gabriel'] = kept


TIDY_FORM = ['input', 'button', 'select', 'textarea']
TIDY_EMPTY = ['li', 'ul', 'ol', 'figure', 'figcaption', 'section', 'i']


def tidy_empty(body):
    """form controls, and list/figure/section/i elements left with no text and no media (TinyFish pages)"""
    n = 0
    for t in body.find_all(TIDY_FORM):
        t.decompose()
        n += 1
    for _ in range(3):
        for t in body.find_all(TIDY_EMPTY):
            if t.parent is not None and not t.get_text(strip=True) and not t.find(['img', 'picture', 'video', 'iframe', 'svg', 'table']):
                t.decompose()
                n += 1
    return n


MEDIA = ['img', 'picture', 'video', 'audio', 'iframe', 'svg', 'canvas', 'object', 'embed', 'table', 'hr']
MEDIA_TAGS = ['img', 'picture', 'video', 'audio', 'iframe', 'svg', 'canvas', 'object', 'embed']


def prune_empty(parents):
    """Elements left with no text and no media because their content was removed go too (climbing up); each is
    replaced by a space so the words around it stay apart. Elements that were already empty are left alone."""
    todo = list(parents)
    seen = set()
    while todo:
        el = todo.pop()
        if el is None or id(el) in seen or el.parent is None or el.name in ('body', 'html', '[document]', 'head'):
            continue
        seen.add(id(el))
        if norm(node_text(el)) or el.find(MEDIA) or el.name in MEDIA:
            continue
        par = el.parent
        el.replace_with(NavigableString(' '))
        todo.append(par)


# ---------------------------------------------------------------- Jesse Gabriel only; listing pages (AUTO-v1)
def jesse_check(text, rules=None):
    """'jesse' when the text names Jesse Gabriel (any script; "Assemblymember Gabriel", "Gabriel (D-", "(Gabriel)"; a bare
    "Gabriel" in a legislative context), 'other' when it names only another Gabriel (Ugarte, Petek, Dillard, Lerner, San
    Gabriel …), 'unclear' for a bare "Gabriel" with no context, 'none' when no Gabriel at all."""
    rules = rules if rules is not None else load_rules()
    t = text or ''
    if rules.get('jesse') and rx(rules['jesse']).search(t):
        # INCL-v1: a "Jesse/Jessie Gabriel" who is someone else (BakerHostetler securities lawyer, "Ms Jesse Gabriel") is
        # 'other' unless the text also has a title or context that is his (Assemblymember, (D-, Encino, Gibson Dunn, ASUC ...)
        if rules.get('other_jesse') and rx(rules['other_jesse']).search(t) and not (
                rules.get('jesse_strong') and rx(rules['jesse_strong']).search(t)):
            return 'other'
        return 'jesse'
    other = bool(rules.get('other_gabriel') and rx(rules['other_gabriel']).search(t))
    if gab_re(rules).search(t):
        # a bare "Gabriel" ("Gabriel said") counts as him in a legislative context unless another Gabriel is named
        if not other and rules.get('jesse_context') and rx(rules['jesse_context']).search(t):
            return 'jesse'
        return 'other' if other else 'unclear'
    return 'other' if other else 'none'


def skip_url(url, rules=None):
    """the pattern when url is a database/results/listing page that is never added (rules['skip_urls'])"""
    rules = rules if rules is not None else load_rules()
    u = str(url or '').strip()
    return next((p for p in rules.get('skip_urls', []) if rx(p).search(u)), None)


# ---------------------------------------------------------------- page check for new finds
STUB = re.compile(r'subscribe to (continue|read)|already a subscriber|sign in to (continue|read)|create a free account to|'
                  r'verify you are human|access denied|just a moment|enable javascript and cookies|page not found|404 not found|'
                  r"this page (isn't|is not) available|you have reached your (free )?(article|story) limit|subscriber\? click here to log ?in|log ?in/register your account", re.I)
# AUTO-v1: which stub it is (DECISIONS 2026-10-27: blocked / paywall / login -> 'BLOCKED – TinyFish', anything else 'RETRY – TinyFish')
STUB_PAY = re.compile(r'subscribe to (continue|read)|already a subscriber|sign in to (continue|read)|create a free account to|'
                      r'you have reached your (free )?(article|story) limit|subscriber\? click here to log ?in|log ?in/register your account', re.I)
STUB_BOT = re.compile(r'verify you are human|access denied|just a moment|enable javascript and cookies', re.I)
BLOCKED_REASONS = ('paywall or login page', 'blocked by the site (bot check or access denied)')


def page_check(res, html_in=None, rules=None):
    """Verdict for a page found by the Update button (DECISIONS 2026-10-27):
      'ok'       save it (cleaned)
      'skip'     Gabriel is named only outside the article (comments, teasers, tags) -> not added
      'error'    not the article / no body / no Gabriel / paywall or error page -> not saved; File name 'BLOCKED – TinyFish'
                 when the reason is in BLOCKED_REASONS (paywall, login, bot wall), else 'RETRY – TinyFish'
    The stub test comes first (AUTO-v1): a paywall page is BLOCKED even when its teaser is too short or lacks Gabriel.
    Returns (verdict, reason)."""
    if 'gabriel_outside_article' in res['flags']:
        return 'skip', 'Gabriel is named only outside the article (comments, teasers or tags)'
    if html_in is not None:
        t = norm(' '.join(b.text for b in extract_blocks(body_of(BeautifulSoup(res['html'], 'html.parser')))))
        if nwords(t) < 250 and STUB.search(t):
            if STUB_PAY.search(t):
                return 'error', BLOCKED_REASONS[0]
            if STUB_BOT.search(t):
                return 'error', BLOCKED_REASONS[1]
            return 'error', 'error page (not found)'
    if not res.get('gabriel_before'):
        return 'error', 'no Gabriel on the page (not the article)'
    if res.get('words_after', 0) < 60:
        return 'error', 'no article body (under 60 words)'
    return 'ok', ''


# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('inp', nargs='?')
    ap.add_argument('out', nargs='?')
    ap.add_argument('--url', default='')
    ap.add_argument('--outlet', default='')
    ap.add_argument('--sheet-json')
    ap.add_argument('--rules')
    ap.add_argument('--overrides')
    ap.add_argument('--stem')
    ap.add_argument('--mode', default='library', choices=['library', 'find'])
    ap.add_argument('--batch')
    ap.add_argument('--out-dir')
    ap.add_argument('--report')
    a = ap.parse_args(argv)
    rules = load_rules(a.rules)
    ovs = load_overrides(a.overrides) if a.overrides else {}
    reps = []
    jobs = []
    if a.batch:
        for line in open(a.batch, encoding='utf-8'):
            p = line.rstrip('\n').split('\t')
            if len(p) < 2 or not p[0]:
                continue
            jobs.append((p[0], p[1], p[2] if len(p) > 2 else '', p[3] if len(p) > 3 else '',
                         json.loads(p[4]) if len(p) > 4 and p[4] else None, os.path.join(a.out_dir, p[0] + '.html')))
    else:
        sheet = json.load(open(a.sheet_json, encoding='utf-8')) if a.sheet_json else None
        jobs.append((a.stem or '', a.inp, a.url, a.outlet, sheet, a.out))
    for stem, inp, url, outlet, sheet, out in jobs:
        html = open(inp, encoding='utf-8', errors='replace').read()
        r = clean_page(html, url, outlet, sheet, rules, ovs, stem, a.mode)
        if out:
            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            open(out, 'w', encoding='utf-8').write(r['html'])
        r['stem'] = stem
        if a.mode == 'find':   # CLIFIX-v1: page_check reads r['html'], so it runs before the pop (single-file find mode raised KeyError)
            r['verdict'], r['reason'] = page_check(r, html)
        r.pop('html', None)
        reps.append(r)
    if a.report:
        json.dump(reps if a.batch else reps[0], open(a.report, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if not a.batch:
        x = reps[0]
        print(json.dumps({k: x[k] for k in ('status', 'flags', 'words_before', 'words_after', 'sites') if k in x} |
                         {'removed': len(x['removed']), 'verdict': x.get('verdict')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
