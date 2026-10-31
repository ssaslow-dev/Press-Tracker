"""MEDIAGATE-v1 (share-clean, 2026-10-29): Claude's sharing review accepts only JPEG, PNG, GIF, WebP images, MP4/WebM video and
MP3/WAV audio. Every page, copy and photo the tracker publishes goes through this module so no other media type is embedded.
  clean_html(page)   saved-page HTML -> the same page with <track> elements removed, svg data: images converted to PNG (cairosvg)
                     or dropped, any other disallowed data: URI removed (attribute) or neutralised (1x1 GIF in CSS)
  svg_to_png_uri(u)  an svg data: URI -> data:image/png;base64,... (2x, <= MAX_PX px wide) or None
  allowed_data(u)    True for data: URIs of an allowed type
  Static content only (MEDIAGATE-v2): clean_html also removes every <video>, <audio>, <source>, <track>, <iframe>, <object>,
                     <embed>, <canvas> and inline <svg> element, unwraps <picture> (its <img> stays), and drops srcset / data-src
                     values that point at a non-allowed type (svg, avif, bmp, ico, tiff, ...).
  scan(text)         list of (what, offset): disallowed data: URIs, static-content violations (used by build/tests/media_gate)
"""
import re, base64, urllib.parse

ALLOWED = {'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'video/mp4', 'video/webm',
           'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/wave'}
SVG = 'image/svg' + '+xml'
GIF1 = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
MAX_PX = 1600
DATA_RX = re.compile(r'data:([A-Za-z0-9.+/_-]+)(?:;[^,"\'\s)>]*)?,', re.I)
_Q = r'(?:[^>"\']|"[^"]*"|\'[^\']*\')*'      # tag body: a ">" inside a quoted value does not end the tag
TRACK_RX = re.compile(r'<track\b' + _Q + r'>(?:\s*</track>)?', re.I)
IMG_RX = re.compile(r'<img\b' + _Q + r'>', re.I)
TAG_RX = re.compile(r'<(?!img\b)([a-z][a-z0-9-]*)\b' + _Q + r'>', re.I)
ATTR_RX = re.compile(r'\s(?:src|srcset|poster|href|data|data-src|data-lazy-src|data-original|data-srcset)\s*=\s*("[^"]*"|\'[^\']*\')', re.I)
SRC_RX = re.compile(r'(\ssrc\s*=\s*)("[^"]*"|\'[^\']*\')', re.I)


def mime_of(u):
    mo = DATA_RX.match(u.strip())
    return mo.group(1).lower() if mo else ''


def allowed_data(u):
    return mime_of(u) in ALLOWED


def _body(u):
    head, _, data = u.partition(',')
    if ';base64' in head.lower():
        return base64.b64decode(data + '=' * (-len(data) % 4))
    return urllib.parse.unquote_to_bytes(data)


def _prep_svg(b):
    """icon svgs often use CSS variables (fill:var(--primary, #000)) and have only a viewBox: resolve the variables from their
    :root rule (else the fallback) and give the root element a width/height so cairosvg can render them"""
    try:
        t = b.decode('utf-8', 'replace')
    except Exception:
        return b
    vs = dict(re.findall(r'(--[\w-]+)\s*:\s*([^;}]+)', t))
    t = re.sub(r'var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)', lambda m: (vs.get(m.group(1)) or m.group(2) or '#000').strip(), t)
    t = re.sub(r'<style\b[^>]*>.*?</style>', '', t, flags=re.S | re.I)
    m = re.search(r'<svg\b[^>]*>', t, re.I)
    if m and not re.search(r'\swidth\s*=', m.group(0), re.I):
        vb = re.search(r'viewBox\s*=\s*"([^"]+)"', m.group(0), re.I)
        if vb:
            w = vb.group(1).replace(',', ' ').split()
            if len(w) == 4:
                t = t.replace(m.group(0), m.group(0)[:-1].rstrip('/') + ' width="%s" height="%s">' % (w[2], w[3]), 1)
    return t.encode('utf-8')


def svg_bytes_to_png_uri(body):
    return svg_to_png_uri('data:' + SVG + ';base64,' + base64.b64encode(body).decode('ascii'))


def raster_to_uri(u):
    """a non-allowed raster data: image (avif, heic, bmp, tiff, ico, jxl...) -> PNG (transparency) or JPEG data: URI via Pillow, or None"""
    try:
        import io
        from PIL import Image
        for plug in ('pillow_avif', 'pillow_heif'):
            try:
                __import__(plug)
                if plug == 'pillow_heif':
                    __import__(plug).register_heif_opener()
            except Exception:
                pass
        im = Image.open(io.BytesIO(_body(u))); im.load()
        alpha = im.mode in ('RGBA', 'LA', 'PA') or (im.mode == 'P' and 'transparency' in im.info)
        b = io.BytesIO()
        if alpha:
            im.convert('RGBA').save(b, 'PNG', optimize=True); m = 'png'
        else:
            im.convert('RGB').save(b, 'JPEG', quality=80, optimize=True); m = 'jpeg'
        return 'data:image/%s;base64,%s' % (m, base64.b64encode(b.getvalue()).decode('ascii'))
    except Exception:
        return None


def svg_to_png_uri(u):
    """svg data: URI -> PNG data: URI at 2x (width capped at MAX_PX), or None when it cannot be rendered"""
    try:
        import cairosvg
        svg = _prep_svg(_body(u))
        png = cairosvg.svg2png(bytestring=svg, scale=2.0, output_width=None)
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(png))
        if im.width > MAX_PX:
            png = cairosvg.svg2png(bytestring=svg, output_width=MAX_PX)
        if im.width < 2 or im.height < 2:
            return None
        return 'data:image/png;base64,' + base64.b64encode(png).decode('ascii')
    except Exception:
        return None


def _img_tag(tag, stats):
    def sub(mo):
        q = mo.group(2)
        u = html_unescape(q[1:-1]).strip()
        if not u.lower().startswith('data:') or allowed_data(u):
            return mo.group(0)
        if mime_of(u) == SVG:
            p = svg_to_png_uri(u)
            if p:
                stats['svg_to_png'] = stats.get('svg_to_png', 0) + 1
                return mo.group(1) + '"' + p + '"'
        elif mime_of(u).startswith('image/'):
            p = raster_to_uri(u)
            if p:
                stats['raster_converted'] = stats.get('raster_converted', 0) + 1
                return mo.group(1) + '"' + p + '"'
        stats['img_dropped'] = stats.get('img_dropped', 0) + 1
        stats.setdefault('dropped_srcs', []).append(u[:60])
        return None
    m = SRC_RX.search(tag)
    if not m:
        out = tag
    else:
        r = sub(m)
        if r is None:
            return ''           # an image that cannot be converted is dropped (its caption lives outside the tag)
        out = tag[:m.start()] + r + tag[m.end():]
    return _other_attrs(out, stats, skip_src=True)


def html_unescape(s):
    import html
    return html.unescape(s)


def _other_attrs(tag, stats, skip_src=False):
    def sub(mo):
        v = mo.group(1)[1:-1]
        if skip_src and mo.group(0).lstrip().lower().startswith('src'):
            return mo.group(0)
        if 'data:' not in v.lower():
            return mo.group(0)
        bad = [m for m in DATA_RX.finditer(html_unescape(v)) if m.group(1).lower() not in ALLOWED]
        if not bad:
            return mo.group(0)
        stats['attr_removed'] = stats.get('attr_removed', 0) + 1
        return ''
    return ATTR_RX.sub(sub, tag)


BADEXT = r'(?:svg|svgz|avif|bmp|ico|tiff?|heic|heif|jxl|apng|ogg|ogv|oga|opus|m4a|aac|flac|mov|mkv|avi|m3u8|mpd|vtt|woff2?|ttf|otf)'
BADURL = re.compile(r'\.' + BADEXT + r'(?=[?#\s,]|$)', re.I)
PAIR = lambda t: re.compile(r'<%s(?=[\s>/])%s>.*?</%s\s*>' % (t, _Q, t), re.I | re.S)
PAIRS = {t: PAIR(t) for t in ('video', 'audio', 'iframe', 'object', 'canvas', 'svg')}
VOID_RX = re.compile(r'</?(?:source|track|embed|video|audio|iframe|object|canvas|svg|picture)(?=[\s>/])' + _Q + r'>', re.I)
PICTURE_RX = re.compile(r'</?picture(?=[\s>/])' + _Q + r'>', re.I)
SETATTR_RX = re.compile(r'\s(?:srcset|data-srcset|data-lazy-srcset|data-src|data-lazy-src|data-original)\s*=\s*("[^"]*"|\'[^\']*\')', re.I)
IMGSRC_RX = re.compile(r'(<img(?=[\s>/])' + _Q + r'>)', re.I)
STATIC_TAGS = ('video', 'audio', 'source', 'track', 'iframe', 'object', 'embed', 'canvas', 'svg', 'picture')
STATIC_RX = re.compile(r'<(?:%s)(?=[\s>/])' % '|'.join(STATIC_TAGS), re.I)


def _static(page, st):
    n = 0
    for t, rx in PAIRS.items():
        page, k = rx.subn('', page); n += k
    page, k = VOID_RX.subn('', page); n += k      # leftovers: <source>, <track>, <embed>, <picture> wrappers, unclosed elements
    if n:
        st['elements_removed'] = st.get('elements_removed', 0) + n

    def attrs(mo):
        tag = mo.group(1)
        def one(m):
            v = html_unescape(m.group(1)[1:-1])
            urls = [u.strip().split(' ')[0] for u in re.split(r',\s+|,(?=\s*\S+\s)', v) if u.strip()] if 'srcset' in m.group(0).lower() else [v.strip()]
            if any(BADURL.search(u.split('?')[0] + ('?' if '?' in u else '')) or BADURL.search(u) for u in urls):
                st['bad_srcs_dropped'] = st.get('bad_srcs_dropped', 0) + 1
                return ''
            return m.group(0)
        tag = SETATTR_RX.sub(one, tag)
        m = SRC_RX.search(tag)
        if m:
            u = html_unescape(m.group(2)[1:-1]).strip()
            if not u.lower().startswith(('data:', 'jgimg:')) and BADURL.search(u):
                st['img_dropped'] = st.get('img_dropped', 0) + 1
                st.setdefault('dropped_srcs', []).append(u[:100])
                return ''
        return tag
    return IMGSRC_RX.sub(attrs, page)


def clean_html(page, stats=None):
    """see module doc; stats (dict) collects counts"""
    st = stats if stats is not None else {}
    if not isinstance(page, str):
        return page
    n = len(TRACK_RX.findall(page))
    if n:
        page = TRACK_RX.sub('', page); st['track_removed'] = st.get('track_removed', 0) + n
    low = page.lower()
    if 'data:' in low:
        page = IMG_RX.sub(lambda mo: _img_tag(mo.group(0), st) if 'data:' in mo.group(0).lower() else mo.group(0), page)
        page = TAG_RX.sub(lambda mo: _other_attrs(mo.group(0), st) if 'data:' in mo.group(0).lower() else mo.group(0), page)

        def left(mo):      # CSS url(data:...), inline text: anything still disallowed
            if mo.group(1).lower() in ALLOWED:
                return mo.group(0)
            st['css_neutralised'] = st.get('css_neutralised', 0) + 1
            return None
        # CSS / leftover: replace the whole URI (up to the closing quote, paren or space) with a 1x1 GIF
        def sub2(mo):
            if mo.group(1).lower() in ALLOWED:
                return mo.group(0)
            st['css_neutralised'] = st.get('css_neutralised', 0) + 1
            return GIF1
        page = re.sub(r'data:([A-Za-z0-9.+/_-]+)(?:;[^,"\'\s)>]*)?,[^"\'\s)]*', sub2, page)
    return _static(page, st)     # after the data: handling: an svg data: image holds "<svg" text that must convert, not be cut


def scan(text):
    """[(type, offset)] for every disallowed data: URI and every <track> in a text"""
    out = [(m.group(1).lower(), m.start()) for m in DATA_RX.finditer(text) if m.group(1).lower() not in ALLOWED]
    out += [('<%s>' % m.group(0)[1:].lower(), m.start()) for m in STATIC_RX.finditer(text)]
    for m in IMGSRC_RX.finditer(text):
        for a in SRC_RX.finditer(m.group(1)):
            u = html_unescape(a.group(2)[1:-1]).strip()
            if not u.lower().startswith(('data:', 'jgimg:')) and BADURL.search(u):
                out.append(('img src ' + u[:60], m.start()))
        for a in SETATTR_RX.finditer(m.group(1)):
            if BADURL.search(html_unescape(a.group(1)[1:-1])):
                out.append(('img srcset ' + a.group(1)[:60], m.start()))
    return out
