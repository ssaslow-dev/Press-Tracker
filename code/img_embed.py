#!/usr/bin/env python3
"""img_embed.py - photos in saved copies (PHOTOS-v2, agent-v20-photos, 2026-10-28; DECISIONS 2026-10-28 "EMBED all real photos").

The tracker's viewer shows a saved copy in a sandboxed srcdoc iframe that inherits the page CSP (img-src self/data/blob):
a remote <img src="https://…"> never loads. So every photo a copy shows must be embedded, and every photo that cannot be
fetched is dropped (its caption kept) so the viewer never shows a broken icon or an empty frame.

One image format everywhere (the cache agent-imgfetch built, work/img_cache/):
  <sha256 of the stored bytes>.jpg   largest candidate <= 1000 px wide (srcset / lazy attrs / <picture><source>), resized to
                                     1000 px wide when larger, JPEG q75 progressive, alpha on white (small GIF/SVG kept as is)
  manifest.json / manifest.csv       one record per fetched <img> (kind, story_id, aid, copy_file, img_index, orig_url,
                                     final_url, status ok|cloudflare|403|404|…, file, flag …)
  worklist.json                      the candidate URLs tried for each record (same order as manifest.json)

Used by:
  make_copies.py   CacheIndex(...).lookup(urls) -> cached file for an <img>; resolve_page() embeds / drops every <img>
  sheet_task.py    (Update button save step, handoff work/tmp_agent-v20-photos/handoff.md) embed_page(): fetch at save time,
                   same cache format, appends to the manifest; returns the page with data: photos and dropped failures
No workaround of blocks: Cloudflare challenges, 401/402/403 are recorded as failures, never retried another way.
"""
import base64, csv, hashlib, html as H, io, json, os, re, threading, time
from urllib.parse import urljoin, urlsplit

IMG = re.compile(r'<img\b[^>]*>', re.I)
LAZY = ['data-src', 'data-lazy-src', 'data-original', 'data-gl-src', 'data-url', 'data-hi-res-src', 'data-full-src',
        'data-orig-file', 'data-large-file', 'data-medium-file']
LAZYSS = ['srcset', 'data-srcset', 'data-lazy-srcset', 'data-gl-srcset']
MAX_W = 1000
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
# drop these even when they load: ad buttons, tracking pixels, site logos (DECISIONS: drop only ads/pixels/logos)
JUNK = re.compile(r'3lift\.com|doubleclick|googlesyndication|adservice|/pixel|/beacon|facebook\.com/tr|scorecardresearch|'
                  r'quantserve|/logo[s]?[/_.-]|[-_]logo\b|logo[-_]|gravatar\.com/avatar|avatar|/emoji/|feedburner|/badge|'
                  r'\bad\.gt/|monu\.delivery|broadstreetads|adnxs\.com|openx\.net|pubmatic|rubiconproject|adsrvr|tapad\.com|'
                  r'd\.turn\.com|sonobi|360yield|smartadserver|contextweb|1rx\.io|Newsletter-Graphic|Sustaining_Donor|digAd|'
                  r'Everyday-Injustice-600', re.I)
SKIP_FLAG = re.compile(r'skip|small \(<60px\)', re.I)


def attr(tag, name):
    m = re.search(r'\s' + re.escape(name) + r'\s*=\s*("([^"]*)"|\'([^\']*)\'|([^\s>]+))', tag, re.I)
    if not m:
        return None
    return H.unescape(m.group(2) if m.group(2) is not None else (m.group(3) if m.group(3) is not None else m.group(4)))


def parse_srcset(s):
    out = []
    if not s:
        return out
    for part in re.split(r',\s+(?=\S)', s.strip()):   # URLs may contain commas (cloudinary): split on ", " only
        bits = part.strip().split()
        if not bits:
            continue
        u, d = bits[0].rstrip(','), bits[1] if len(bits) > 1 else ''
        m = re.match(r'(\d+)w$', d)
        out.append((u, int(m.group(1)) if m else None))
    return out


def picture_sources(page, pos):
    st = page.rfind('<picture', 0, pos)
    if st < 0 or page.rfind('</picture>', st, pos) >= 0:
        return []
    return re.findall(r'<source\b[^>]*>', page[st:pos], re.I)


LOCAL = re.compile(r'^(?:pdf|img)/[^:]+$')


def is_remote(u):
    return bool(u) and not u.startswith(('data:', 'blob:', 'jgimg:'))


def mangled(u, base):
    """KTLA / Mother Jones saves: src = '<article URL>/<width>' (the page URL, not an image)"""
    if not u or not base:
        return False
    b = base.split('#')[0].split('?')[0].rstrip('/')
    return bool(re.match(re.escape(b) + r'/\d{2,4}/?$', u.split('?')[0]))


def candidates(page, m, base=''):
    """the URLs an <img> (regex match m in page) could be fetched from, best first: srcset entries <= 1000w (largest first),
    else the smallest wider one; then lazy attrs, src and width-less srcset entries. Relative URLs resolved against base."""
    t = m.group(0)
    ss, singles = [], []
    for a in LAZYSS:
        ss += [(a, u, w) for u, w in parse_srcset(attr(t, a))]
    for s in picture_sources(page, m.start()):
        for a in ('srcset', 'data-srcset'):
            ss += [('source ' + a, u, w) for u, w in parse_srcset(attr(s, a))]
    for a in ['src'] + LAZY:
        v = (attr(t, a) or '').strip()
        if is_remote(v):
            singles.append((a, v, None))
    res = lambda u: urljoin(base, u) if base else u
    wc = [(a, res(u), w) for a, u, w in ss if is_remote(u) and w]
    under = sorted([c for c in wc if c[2] <= MAX_W], key=lambda c: -c[2])
    ordered = under or sorted(wc, key=lambda c: c[2])
    lz = [(a, res(u), w) for a, u, w in singles if a != 'src']
    sr = [(a, res(u), w) for a, u, w in singles if a == 'src' and not mangled(res(u), base)]
    nw = [(a, res(u), w) for a, u, w in ss if is_remote(u) and not w]
    ordered = ordered + (lz + sr + nw if wc else sr + lz + nw)
    seen, out = set(), []
    for c in ordered:
        if c[1] in seen or not re.match(r'https?://', c[1]):
            continue
        seen.add(c[1])
        out.append(c)
    return out


def ukey(u):
    """URL match key: unescaped, no scheme, no fragment"""
    u = H.unescape(u or '').strip().split('#')[0]
    return re.sub(r'^https?:', '', u)


# ---------------------------------------------------------------- cache
class CacheIndex:
    """URL -> cached image file (work/img_cache). Built from manifest.json + worklist.json: every candidate URL of a fetched
    record maps to its file; records flagged skip (ads, logos, < 60 px) map to None (= drop)."""

    def __init__(self, cache_dir):
        self.dir = cache_dir
        self.by_url, self.failed = {}, {}
        man = os.path.join(cache_dir, 'manifest.json')
        wl = os.path.join(cache_dir, 'worklist.json')
        recs = json.load(open(man, encoding='utf-8')) if os.path.exists(man) else []
        items = json.load(open(wl, encoding='utf-8')) if os.path.exists(wl) else []
        for k, r in enumerate(recs):
            urls = [r.get('orig_url'), r.get('final_url')] + [c[1] for c in (r.get('cands') or [])]
            if k < len(items) and items[k].get('sid') == r.get('story_id') and items[k].get('i') == r.get('img_index'):
                urls += [c[1] for c in items[k].get('cands') or []]
            f = r.get('file') or ''
            ok = r.get('status') == 'ok' and f and not SKIP_FLAG.search(r.get('flag') or '')
            for u in urls:
                if not u:
                    continue
                key = ukey(u)
                if ok:
                    self.by_url[key] = os.path.join(cache_dir, os.path.basename(f))
                elif key not in self.by_url:
                    self.failed[key] = r.get('status') or 'failed'

    def lookup(self, urls):
        for u in urls:
            p = self.by_url.get(ukey(u))
            if p and os.path.exists(p):
                return p
        return None

    def status(self, urls):
        for u in urls:
            s = self.failed.get(ukey(u))
            if s:
                return s
        return 'not fetched'


def data_uri(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.svg':   # MEDIAGATE-v1: sharing accepts only JPEG/PNG/GIF/WebP images; an svg is rendered to PNG (None: dropped)
        import media_gate
        u = media_gate.svg_bytes_to_png_uri(open(path, 'rb').read())
        return u            # None when it cannot be rendered: the caller drops the image
    mime = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.png': 'image/png'}.get(ext, 'image/jpeg')
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode('ascii')


# ---------------------------------------------------------------- page rewrite
SET_ATTRS = re.compile(r'\s(?:srcset|sizes|data-srcset|data-lazy-srcset|data-gl-srcset|loading|' + '|'.join(re.escape(a) for a in LAZY) +
                       r')\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)
SRC_ATTR = re.compile(r'\ssrc\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)


def set_src(tag, src):
    """the tag with src=src and no srcset/lazy attributes (a srcset would make the browser fetch a remote URL)"""
    t = SET_ATTRS.sub('', tag)
    if SRC_ATTR.search(t):
        return SRC_ATTR.sub(lambda _: f' src="{src}"', t, count=1)
    return re.sub(r'^<img\b', f'<img src="{src}"', t, flags=re.I)


def resolve_page(page, resolve, base=''):
    """Every <img> in page: resolve(cands, tag) returns a src to keep (data: URI, jgimg: ref or local path) or None to drop.
    Images already embedded (data:/jgimg:) are kept, minus remote srcset. Dropped images take their <picture> and an
    emptied <figure>/<a>/wrapper with them; a figcaption with text stays. Returns (page, stats)."""
    st = {'kept': 0, 'embedded': 0, 'dropped': 0, 'dropped_urls': []}
    out, last = [], 0
    for m in IMG.finditer(page):
        t = m.group(0)
        src = (attr(t, 'src') or '').strip()
        new = None
        if src.startswith(('data:', 'jgimg:')):
            new = set_src(t, H.escape(src, quote=True)) if re.search(r'srcset|data-src', t, re.I) else t
            st['kept'] += 1
        else:
            # files published next to the tracker (pdf/<code>/pN.jpg page images): a local path, never resolved against the site
            cands = [('src', src, None)] if LOCAL.match(src) else candidates(page, m, base)
            if not cands and src and not re.match(r'(https?:)?//', src) and not src.startswith(('blob:', 'about:')):
                cands = [('src', src, None)]   # site-relative / local path (pdf page images): let the resolver decide
            got = resolve(cands, t) if cands else None
            if got:
                new = set_src(t, got)
                st['embedded'] += 1
            else:
                st['dropped'] += 1
                st['dropped_urls'].append((cands[0][1] if cands else src)[:300])
        out.append(page[last:m.start()])
        out.append(new if new is not None else '<!--jg-img-dropped-->')
        last = m.end()
    out.append(page[last:])
    page = ''.join(out)
    # remote <source> elements never load either
    page = re.sub(r'<source\b[^>]*\bsrcset\s*=\s*["\']?\s*(?:https?:)?//[^>]*>', '', page, flags=re.I)
    if st['dropped']:
        page = prune_dropped(page)
    return page, st


_FILL = r'(?:\s|&nbsp;|<br\s*/?>|<source\b[^>]*>|<!--jg-img-dropped-->)*'
EMPTY_WRAP = re.compile(r'<(picture|figure|a|div|span|p|noscript|button)\b[^>]*>' + _FILL + r'<!--jg-img-dropped-->' + _FILL + r'</\1\s*>', re.I)


def prune_dropped(page):
    """remove the marker and every wrapper it alone leaves empty (no text, no media), climbing up a few levels; wrappers
    that hold anything else (a figcaption with text, another photo) stay (DECISIONS: captions kept)"""
    for _ in range(8):
        new = EMPTY_WRAP.sub('<!--jg-img-dropped-->', page)
        if new == page:
            break
        page = new
    return page.replace('<!--jg-img-dropped-->', '')


# ---------------------------------------------------------------- fetch (save time)
def _session():
    import requests
    s = requests.Session()
    px = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if px:
        s.proxies = {'http': px, 'https': px}
    ca = os.environ.get('JG_IMG_CA') or ('/root/.ccr/ca-bundle.crt' if os.path.exists('/root/.ccr/ca-bundle.crt') else None)
    if ca:
        s.verify = ca
    return s


def _cf(r, body):
    return r.headers.get('cf-mitigated') == 'challenge' or (r.status_code in (403, 503) and (
        b'Just a moment' in body[:5000] or b'challenge-platform' in body[:20000] or b'cf-chl' in body[:20000]))


def normalize(body):
    """bytes -> (stored bytes, ext, source format, (w, h)); raises on non-images"""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = 200_000_000
    head = body[:600].lstrip().lower()
    if head.startswith(b'<svg') or (head.startswith(b'<?xml') and b'<svg' in body[:2000].lower()):
        if len(body) <= 60_000:   # MEDIAGATE-v1: stored as PNG (2x), never svg
            import media_gate
            u = media_gate.svg_bytes_to_png_uri(body)
            if not u:
                raise ValueError('svg cannot be converted to PNG')
            png = base64.b64decode(u.split(',', 1)[1])
            from PIL import Image
            return png, 'png', 'svg', Image.open(io.BytesIO(png)).size
        raise ValueError('svg too large')
    im = Image.open(io.BytesIO(body))
    fmt = im.format
    im.load()
    w, h = im.size
    if fmt == 'GIF' and len(body) <= 150_000 and w <= MAX_W:
        return body, 'gif', fmt, (w, h)
    if getattr(im, 'n_frames', 1) > 1:
        im.seek(0)
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
        im = im.convert('RGBA')
        bg = Image.new('RGB', im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[3])
        im = bg
    elif im.mode != 'RGB':
        im = im.convert('RGB')
    if w > MAX_W:
        im = im.resize((MAX_W, max(1, round(h * MAX_W / w))), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, 'JPEG', quality=75, optimize=True, progressive=True)
    return b.getvalue(), 'jpg', fmt, im.size


def fetch_one(cands, referer, cache_dir, session=None, timeout=20):
    """try up to 4 candidates; returns a manifest-style record (status ok + file, or the first failure)"""
    s = session or _session()
    ref = referer or ('%s://%s/' % (urlsplit(cands[0][1]).scheme, urlsplit(cands[0][1]).netloc) if cands else '')
    rec = {'orig_attr': cands[0][0] if cands else '', 'orig_url': cands[0][1] if cands else '', 'final_url': '', 'status': '',
           'http': '', 'detail': '', 'bytes': 0, 'orig_bytes': 0, 'src_format': '', 'wxh': '', 'sha': '', 'file': '', 'tried': 0,
           'cands': [list(c) for c in cands]}
    if not cands:
        rec.update(status='no-url', detail='no usable URL in the page')
        return rec
    fails = []
    for a, u, w in cands[:4]:
        rec['tried'] += 1
        if JUNK.search(u):
            fails.append(('junk', u, '', 'ad/pixel/logo'))
            continue
        try:
            r = s.get(u, headers={'User-Agent': UA, 'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
                                  'Accept-Language': 'en-US,en;q=0.9', 'Referer': ref}, timeout=timeout, allow_redirects=True)
        except Exception as e:
            fails.append(('conn', u, '', repr(e)[:150]))
            continue
        body = r.content
        if _cf(r, body):
            fails.append(('cloudflare', u, r.status_code, 'challenge'))
            continue
        if r.status_code >= 400:
            fails.append((str(r.status_code) if r.status_code in (403, 404) else 'http%d' % r.status_code, u, r.status_code, ''))
            continue
        try:
            data, ext, fmt, size = normalize(body)
        except Exception as e:
            fails.append(('not-image', u, r.status_code, repr(e)[:150]))
            continue
        if size and (size[0] < 60 or size[1] < 40):
            fails.append(('small', u, r.status_code, '%dx%d' % size))
            continue
        sha = hashlib.sha256(data).hexdigest()
        fn = f'{sha}.{ext}'
        p = os.path.join(cache_dir, fn)
        if not os.path.exists(p):
            os.makedirs(cache_dir, exist_ok=True)
            open(p + '.tmp', 'wb').write(data)
            os.replace(p + '.tmp', p)
        rec.update(orig_attr=a, final_url=r.url, status='ok', http=r.status_code, bytes=len(data), orig_bytes=len(body),
                   src_format=fmt, wxh='%dx%d' % size if size else '', sha=sha, file='work/img_cache/' + fn,
                   detail=('fallback after: ' + '; '.join(f[0] for f in fails)) if fails else '')
        return rec
    f0 = fails[0]
    rec.update(status=f0[0], final_url=f0[1], http=f0[2], detail=' | '.join(f'{f[0]} {f[3]}' for f in fails)[:300])
    return rec


_lock = threading.Lock()


def append_manifest(cache_dir, recs):
    """add save-time records to manifest.json/.csv (+ worklist.json, kept index-aligned)"""
    with _lock:
        mp, wp, cp = (os.path.join(cache_dir, n) for n in ('manifest.json', 'worklist.json', 'manifest.csv'))
        man = json.load(open(mp, encoding='utf-8')) if os.path.exists(mp) else []
        wl = json.load(open(wp, encoding='utf-8')) if os.path.exists(wp) else []
        cols = list(man[0].keys()) if man else ['kind', 'story_id', 'aid', 'copy_file', 'img_index', 'is_lead', 'cause_broken',
                                                'orig_attr', 'orig_url', 'final_url', 'status', 'http', 'detail', 'bytes',
                                                'orig_bytes', 'src_format', 'wxh', 'sha', 'file', 'tried', 'flag']
        for r in recs:
            cands = r.pop('cands', [])
            row = {c: r.get(c, '') for c in cols}
            man.append(row)
            wl.append({'kind': row.get('kind', ''), 'sid': row.get('story_id', ''), 'i': row.get('img_index', ''), 'cands': cands})
        json.dump(man, open(mp + '.tmp', 'w', encoding='utf-8'), indent=0)
        os.replace(mp + '.tmp', mp)
        json.dump(wl, open(wp + '.tmp', 'w', encoding='utf-8'), indent=0)
        os.replace(wp + '.tmp', wp)
        with open(cp + '.tmp', 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
            w.writeheader()
            w.writerows(man)
        os.replace(cp + '.tmp', cp)


def embed_page(page, base_url, cache_dir, story_id='', aid='', copy_file='', kind='story', fetch=True, session=None):
    """Update button save step: every <img> of a newly saved page -> embedded data: photo (cache hit, else fetched now and
    cached in the same format) or dropped (ads/pixels/logos, failures; captions kept). Returns (page, report)."""
    idx = CacheIndex(cache_dir)
    new_recs = []
    s = session

    def res(cands, tag):
        nonlocal s
        if any(JUNK.search(c[1]) for c in cands[:1]):
            return None
        p = idx.lookup([c[1] for c in cands])
        if p:
            return data_uri(p)
        if not fetch or not any(re.match(r'https?://', c[1]) for c in cands):
            return None
        s = s or _session()
        r = fetch_one(cands, base_url, cache_dir, s)
        r.update(kind=kind, story_id=story_id, aid=aid, copy_file=copy_file, img_index=len(new_recs), is_lead=int(not new_recs),
                 cause_broken='save-time fetch', flag='')
        new_recs.append(r)
        if r['status'] == 'ok':
            p = os.path.join(cache_dir, os.path.basename(r['file']))
            for c in cands:
                idx.by_url[ukey(c[1])] = p
            return data_uri(p)
        return None
    out, st = resolve_page(page, res, base_url)
    try:   # MEDIAGATE-v1: no <track>, no svg/other disallowed data: media in a saved page
        import media_gate
        out = media_gate.clean_html(out)
    except ImportError:
        pass
    if new_recs:
        append_manifest(cache_dir, [dict(r) for r in new_recs])
    st['fetched'] = sum(1 for r in new_recs if r['status'] == 'ok')
    st['failed'] = [(r['status'], r['orig_url'][:200]) for r in new_recs if r['status'] != 'ok']
    st['waiting'] = 0
    return out, st


def unresolved(page):
    """build gate: <img> srcs that would not load in the viewer (anything but data:/jgimg:, and pdf page paths given)"""
    bad = []
    for m in IMG.finditer(page):
        t = m.group(0)
        src = (attr(t, 'src') or '').strip()
        if not src.startswith(('data:', 'jgimg:')) or re.search(r'\ssrcset\s*=', t, re.I):
            bad.append(src[:200] or '(empty src)')
    return bad


if __name__ == '__main__':
    import argparse, sys
    ap = argparse.ArgumentParser(description='embed photos in one saved page (same cache format as make_copies uses)')
    ap.add_argument('inp')
    ap.add_argument('out')
    ap.add_argument('--url', default='')
    ap.add_argument('--cache', required=True)
    ap.add_argument('--sid', default='')
    ap.add_argument('--aid', default='')
    ap.add_argument('--no-fetch', action='store_true')
    a = ap.parse_args()
    page, st = embed_page(open(a.inp, encoding='utf-8', errors='replace').read(), a.url, a.cache, a.sid, a.aid, a.inp,
                          fetch=not a.no_fetch)
    open(a.out, 'w', encoding='utf-8').write(page)
    st.pop('dropped_urls', None)
    print(json.dumps(st))
    sys.exit(0)
