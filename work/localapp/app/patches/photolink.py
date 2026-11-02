"""photolink.py - PHOTOLINK-v1 (Sammy, 2026-11-02): the PC tracker's saved copies keep their photos as LINKS.

This file is added to the PC copy of the pipeline folder by assemble_app.py (it is not part of code/). img_embed.embed_page() hands the
page to link_page() when the environment says AJG_LINK_PHOTOS=1 (set by the tracker's own wrappers); the program itself never fetches
anything: no requests, no sockets, no cache lookup. Edge loads the images when a saved copy is opened.

What link_page does to a saved page (after clean_html has cut the article):
  1. removes <script> elements, then
  2. for every <img>: picks ONE address (an absolute https URL; an http URL only when the image has no https address, and that is
     recorded), preferring the largest srcset entry up to 1,000 px wide (img_embed.candidates: PHOTOS-v2), drops the srcset / lazy-load
     attributes, sets referrerpolicy="no-referrer" and loading="lazy";
  3. drops what img_embed already classifies as ads, tracking pixels, logos and avatars (img_embed.JUNK), declared 1-pixel images and
     images declared smaller than 60 x 40 px; an image that is dropped takes its empty wrapper with it, a caption stays;
  4. runs media_gate.clean_html (MEDIAGATE-v1/v2: no <svg>, <video>, <audio>, <iframe>, <object>, <picture> ...; an <img> whose address ends
     in svg, avif, bmp ... is dropped). Embedded photos (data: / jgimg:) and published local paths (pdf/..., img/...) are kept as they are.
Returns (page, stats) like img_embed.embed_page.
"""
import html as H
import re

import img_embed as IE
import media_gate as MG

MAX_URL = 2000
BAD_CHARS = re.compile(r'[\s<>"\'`\x00-\x1f\x7f]')
SCRIPT_PAIR = re.compile(r'<script(?=[\s>/])(?:[^>"\']|"[^"]*"|\'[^\']*\')*>.*?</script\s*>', re.I | re.S)
SCRIPT_TAG = re.compile(r'</?script(?=[\s>/])(?:[^>"\']|"[^"]*"|\'[^\']*\')*>', re.I)
DROP_ATTRS = re.compile(r'\s(?:referrerpolicy|loading|crossorigin|decoding|fetchpriority|on[a-z]+)\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)


def _int(v):
    m = re.match(r'^\s*(\d{1,5})\s*(?:px)?\s*$', v or '')
    return int(m.group(1)) if m else None


def _pick(cands):
    """(url, http_only) from the candidates (best first): the first usable https one, else the first usable http one"""
    ok = []
    for _, u, _w in cands:
        u = u.split('#')[0]
        if not re.match(r'https?://[^/\s]', u, re.I) or len(u) > MAX_URL or BAD_CHARS.search(u) or MG.BADURL.search(u.split('?')[0]):
            continue
        ok.append(u)
    https = [u for u in ok if u[:6].lower() == 'https:']
    if https:
        return https[0], False
    return (ok[0], True) if ok else (None, False)


def _finish(tag):
    """the tag with no srcset / lazy attributes left over, no event handlers, and referrerpolicy + loading set"""
    t = DROP_ATTRS.sub('', IE.SET_ATTRS.sub('', tag))
    return t[:-1].rstrip('/').rstrip() + ' referrerpolicy="no-referrer" loading="lazy">'


def link_page(page, base_url=''):
    st = {'kept': 0, 'embedded': 0, 'linked': 0, 'dropped': 0, 'dropped_urls': [], 'http_only': [], 'junk': 0, 'small': 0,
          'scripts_removed': 0, 'fetched': 0, 'failed': [], 'waiting': 0}
    page, n = SCRIPT_PAIR.subn('', page)
    page, k = SCRIPT_TAG.subn('', page)
    st['scripts_removed'] = n + k
    base = base_url or 'https:'
    out, last = [], 0
    for m in MG.IMG_RX.finditer(page):
        t = m.group(0)
        src = (IE.attr(t, 'src') or '').strip()
        new, why = None, ''
        placeholder = bool(re.match(r'data:image/(?:gif|svg)', src, re.I)) and len(src) < 400    # a 1-pixel lazy-load stand-in, not a photo
        if src.startswith(('data:', 'jgimg:')) and not placeholder:
            new = _finish(t)
            st['kept'] += 1
        elif IE.LOCAL.match(src):
            new = _finish(IE.set_src(t, H.escape(src, quote=True)))
            st['kept'] += 1
        else:
            cands = IE.candidates(page, m, base)
            w, h = _int(IE.attr(t, 'width')), _int(IE.attr(t, 'height'))
            url, http_only = _pick(cands)
            if url is None:
                why = 'no usable address'
            elif IE.JUNK.search(url) or (cands and IE.JUNK.search(cands[0][1])):
                why, st['junk'] = 'ad, pixel, logo or avatar', st['junk'] + 1
            elif (w is not None and w < 60) or (h is not None and h < 40):
                why, st['small'] = 'declared too small', st['small'] + 1
            else:
                new = _finish(IE.set_src(t, H.escape(url, quote=True)))
                st['linked'] += 1
                st['embedded'] += 1
                if http_only:
                    st['http_only'].append(url[:300])
            if new is None:
                st['dropped'] += 1
                st['dropped_urls'].append((cands[0][1] if cands else src or '(empty src)')[:300] + ' [' + why + ']')
        out.append(page[last:m.start()])
        out.append(new if new is not None else '<!--jg-img-dropped-->')
        last = m.end()
    out.append(page[last:])
    page = ''.join(out)
    if st['dropped']:
        page = IE.prune_dropped(page)
    mg = {}
    page = MG.clean_html(page, mg)
    st['media_gate'] = mg
    st['media_leftover'] = len(MG.scan(page))
    return page, st
