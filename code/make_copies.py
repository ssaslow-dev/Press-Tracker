"""Viewer copies (articles/*.json + manifest) for the tracker's saved-copy viewer and its full-text search.

T40 (agent-code, 2026-10-27; DECISIONS "the tracker's full-text search must use the CLEANED article text"):
  python3 -I make_copies.py SRC COVERAGE.xlsx OUT_DIR --clean work/html_clean --nb work/texts/nb \
      [--img-map build/clean/img_map.json] [--errors work/final/error_copies.csv] [--deletions work/final/deletions.csv] \
      [--sidmap work/sid_map.json] [--skip sid,sid] [--report report.json]
  Rebuilds every copy from scratch:
  - a story's copy is its CLEANED library HTML (work/html_clean/<year>/<old Article ID>.html, keyed through the sheet;
    the Original row's file first, then the story's other rows in sheet order). Never texts/tracker, fetch caches or
    the copies already published (SRC is read only to report what changed).
  - stories with no cleaned HTML get the NewsBank PDF text copy (texts/nb/<Article ID>.json) of their Original row.
  - error copies (error_copies.csv: library file -> RETRY – TinyFish) are never used; deleted stories (deletions.csv)
    and press-release-only stories (Press release = Yes on the Original) get no copy.
  - photos: data: images are moved out of the page into img/<n>.json and referenced as src="jgimg:<n>/<key>" (the
    viewer's existing fillImgs). Images that are already in the published img/0..15.json shards (img_map.json, matched
    byte for byte by position against the old tracker copy) reuse those refs; the rest go to new shards img/100.json…
  - PHOTOS-v2 (agent-v20-photos, 2026-10-28; --img-cache work/img_cache [--pdf-restore work/img_cache/pdf_restore]): every
    remote <img> (src/srcset/lazy attrs/<picture>) is embedded from the image cache (img_embed.py; same format the Update
    button's save step writes) and then externalized like any data: photo; an image that is not in the cache (failed fetch,
    ad, pixel, logo) is DROPPED with the <picture>/<figure>/link wrapper it leaves empty (captions kept), so the viewer never
    shows a broken icon. Pruned PDF page images (pdf/<code>/pN.jpg) found in --pdf-restore are embedded and their copy's
    "Full print edition (PDF)" link (meta jg-pdf content) is dropped (DECISIONS 2026-10-28). Build gate: report
    img_gate.unresolved lists every <img> that would still not load (exit 3 with --img-strict).
  - ORIGIN ROOT FIX D (rootfix.md): the story copy is the Original's own HTML, then the Original's NewsBank/ProQuest text,
    and only then another row's HTML (a reprint's page never stands in while the Original has text).
  - AVPREVIEW-v1 fix A (work/tmp_agent-previewclean/spec.md): copies of Audio & video stories (AV tab Item type Episode /
    Broadcast segment / Video clip on the Original) get av_display_clean.py (rules av_rules.json, next to this file); their
    NewsBank text copies carry no PDF caption / citation lines. Article copies are untouched.
  Output: OUT/articles/<year>.json (split <year>-2.json… above 12 MB), OUT/articles/manifest.json, OUT/img/1NN.json,
  report (counts, dropped, sizes). The tracker's search index reads only these copies (indexSaved -> manifest).

Legacy mode (no --clean; T14/T23 behaviour, kept for old runs): add texts/tracker + NewsBank copies to SRC's copies.
ID migration (T23): works on the workbook before or after it (Old Article ID columns; jg-NNNNN -> sNNNNN, --sidmap).
"""
import sys, os, json, glob, html, argparse, re, csv, hashlib
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I drops the script folder: img_embed / av_display_clean sit here

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('cov'); ap.add_argument('out')
ap.add_argument('--nb'); ap.add_argument('--tracker'); ap.add_argument('--sidmap')
ap.add_argument('--skip', default='')
ap.add_argument('--clean', help='folder of cleaned library HTML (<year>/<old Article ID>.html) -> rebuild mode (T40)')
ap.add_argument('--clean-extra', action='append', default=[], help='FINALCHECK-v1 D4: more folders of cleaned library HTML (<year>/<name>.html), read after --clean; '
               'default (none given): work/tmp_recall_rows/copies next to --clean when it exists (the recall-rows library adds)')
ap.add_argument('--img-map'); ap.add_argument('--errors'); ap.add_argument('--deletions'); ap.add_argument('--report')
ap.add_argument('--shard-mb', type=float, default=12.0)
ap.add_argument('--img-cache', help='PHOTOS-v2: image cache folder (img_embed.py format: <sha>.jpg + manifest.json + worklist.json)')
ap.add_argument('--pdf-restore', help='PHOTOS-v2: restored PDF page images <code>/pN.jpg (embedded; their PDF links dropped)')
ap.add_argument('--img-strict', action='store_true', help='PHOTOS-v2 build gate: exit 3 when any copy keeps an image that cannot load')
ap.add_argument('--no-av-clean', action='store_true', help='AVPREVIEW-v1: skip the AV display cleanup')
ap.add_argument('--releases', help='RELCOPIES-v1: cleaned press-release copies <year>/prNNNNN.html (work/html_clean/press_releases) '
                '-> articles/releases.json keyed by Release ID')
a = ap.parse_args()
SKIP = set(x for x in a.skip.split(',') if x)

C = pd.read_excel(a.cov, sheet_name='Coverage', dtype=str).fillna('')
from reprint_rule import hide_unverified   # HIDEUNVERIFIED-v1: a hidden row never supplies a story's copy
import reprint_rule as RR                   # REPRINT-v2: wrong-copy guard (copy_mismatch / wrong_copies.csv)
C = hide_unverified(C)
NEW = 'Old Article ID' in C.columns            # the workbook has been migrated to the new IDs
OLD_AID = {}
if NEW:
    for c_old, c_new in (('Old Article ID', 'Article ID'), ('Old Print Article ID', 'Print Article ID')):
        if c_old in C.columns:
            OLD_AID.update({o: n for o, n in zip(C[c_old], C[c_new]) if o})
SIDMAP = json.load(open(a.sidmap)) if a.sidmap else {}


def sid_now(k):
    if NEW and re.match(r'^jg-\d{5}$', k): return SIDMAP.get(k) or 's' + k[3:]
    return k


O = C[C['Original or reprint'] == 'Original'].drop_duplicates('Story ID').set_index('Story ID')
by_aid = C.set_index('Article ID')


def year_of(sid):
    y = str(O.loc[sid, 'Year'])[:4] if sid in O.index else ''
    y = y if re.match(r'^\d{4}$', y) else str(O.loc[sid, 'Date'])[:4] if sid in O.index else ''
    return y if re.match(r'^\d{4}$', y) else 'undated'


def nb_page(t, r, av=False):
    """AVPREVIEW-v1: av=True (Audio & video stories) leaves out the PDF caption, the word count and the citation"""
    e = html.escape
    paras = [p.strip() for p in re.split(r'\n\s*\n', t.get('text', '')) if p.strip()]
    if len(paras) < 2: paras = [p.strip() for p in t.get('text', '').split('\n') if p.strip()]
    meta = ' · '.join(x for x in [r['Outlet'], r['Date'], t.get('section') and f"Section: {t['section']}", r['Page'] and f"Page {r['Page']}", not av and t.get('words') and f"{t['words']} words"] if x)
    by = t.get('author') or r['Author / byline']
    body = ''.join(f'<p>{e(p)}</p>' for p in paras)
    cite = f'<p class="pdf-cap">{e(t["citation"])}</p>' if t.get('citation') and not av else ''
    return (f'<html><head><title>{e(r["Headline"] or t.get("headline", ""))}</title></head><body><article class="jg-pdf-text">'
            + ('' if av else f'<p class="pdf-cap">Text of the NewsBank PDF{" (item " + str(t["pos"]) + ")" if t.get("pos") else ""}</p>') +
            f'<h1>{e(r["Headline"] or t.get("headline", ""))}</h1>' + (f'<p class="byline">By {e(by)}</p>' if by else '') +
            f'<p class="pdf-cap">{e(meta)}</p>{body}{cite}</article></body></html>')


def nb_texts():
    out = {}
    if a.nb:
        for f in sorted(glob.glob(os.path.join(a.nb, '*.json'))):
            t = json.load(open(f, encoding='utf-8'))
            aid = t.get('aid') or os.path.basename(f)[:-5]
            aid = OLD_AID.get(aid, aid)
            if aid not in by_aid.index:   # NAMING-v2: the current Article ID from the clip's library name (nb05457r-s00044.pdf)
                m = re.match(r'^(?:nb|ws|pq)(\d{5})[or]?', os.path.basename(str(t.get('pdf') or '')))
                if m and m.group(1) in by_aid.index: aid = m.group(1)
            if aid in by_aid.index and t.get('text'):
                out[aid] = t
    return out


def write_out(arts, man, extra_files=None):
    os.makedirs(os.path.join(a.out, 'articles'), exist_ok=True)
    for yf, d in arts.items():
        json.dump(d, open(os.path.join(a.out, 'articles', yf), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump(man, open(os.path.join(a.out, 'articles', 'manifest.json'), 'w'), separators=(',', ':'))


if not a.clean:
    # ------------------------------------------------------------ legacy mode (T14 / T23)
    arts = {}
    for f in glob.glob(os.path.join(a.src, 'articles', '*.json')):
        if f.endswith('manifest.json'): continue
        arts[os.path.basename(f)] = json.load(open(f, encoding='utf-8'))
    man = json.load(open(os.path.join(a.src, 'articles', 'manifest.json')))
    added = {'skipped_listed': 0, 'tracker': 0, 'newsbank': 0, 'skipped_existing': 0, 'skipped_no_row': 0, 'rekeyed_legacy': 0}
    if NEW:
        for k in [k for k in man['articles'] if re.match(r'^jg-\d{5}$', k)]:
            n = sid_now(k); yf = man['articles'].pop(k).split('/')[-1]
            page = arts.get(yf, {}).pop(k, None)
            if n not in man['articles'] and page is not None:
                arts[yf][n] = page; man['articles'][n] = f'articles/{yf}'; added['rekeyed_legacy'] += 1

    def add(sid, page, kind):
        if sid in SKIP: added['skipped_listed'] += 1; return
        if sid in man['articles'] or (sid in O.index and any(c in man['articles'] for c in re.findall(r'jg-[0-9a-f]{6}', O.loc[sid, 'Tracker story code']))):
            added['skipped_existing'] += 1; return
        yf = f'{year_of(sid)}.json'
        arts.setdefault(yf, {})[sid] = page
        man['articles'][sid] = f'articles/{yf}'
        added[kind] += 1
    if a.tracker:
        for f in sorted(glob.glob(os.path.join(a.tracker, '*.html'))):
            sid = sid_now(os.path.basename(f)[:-5])
            if sid not in O.index: added['skipped_no_row'] += 1; continue
            add(sid, open(f, encoding='utf-8').read(), 'tracker')
    for aid, t in nb_texts().items():
        r = by_aid.loc[aid]
        if r['Original or reprint'] != 'Original': continue
        add(r['Story ID'], nb_page(t, r), 'newsbank')
    write_out(arts, man)
    print(json.dumps(added), 'files:', len(arts), 'total MB:', round(sum(os.path.getsize(os.path.join(a.out, 'articles', f)) for f in os.listdir(os.path.join(a.out, 'articles'))) / 1e6, 1))
    sys.exit(0)

# ---------------------------------------------------------------- rebuild from the cleaned library (T40)
rep = {'mode': 'clean', 'copies': 0, 'from_clean': 0, 'from_newsbank_text': 0, 'stories': 0,
       'dropped': {'deleted_story': [], 'press_release_story': [], 'error_copy_files': [], 'no_clean_copy': [], 'wrong_copy': []},
       'wrong_copy_suspect': [],   # REPRINT-v2: title shares no word with the row headline (reported, kept)
       'images': {'reused_published': 0, 'new': 0, 'new_bytes': 0}, 'blob_refs_dropped': {'refs': 0, 'stories': []}, 'files': []}


def stem_aid(stem):
    """NAMING-v2 (agent-tabs 2026-10-28): old names carry the OLD Article ID ("nb-04130", "ws-02304 (jg-190321)"); current
    library names are <nb|pq|ws><Article ID><o|r>-s<Story ID> (README), e.g. ws09735o-s04701, nb05457r-s00044 -> '09735'"""
    m = re.search(r'((?:nb|ws|pq)-\d{5})', stem)
    if m: return m.group(1)
    m = re.match(r'^(?:nb|ws|pq)(\d{5})[or]?(?:-s\d{5})?(?:-v\d+)?$', stem.split('/')[-1])   # FINALCHECK-v1 D4: a re-cleaned file is <name>-v2.html
    return m.group(1) if m else ''


def stem_sid(stem):
    m = re.search(r'-(s\d{5})(?:-v\d+)?$', stem.split('/')[-1])
    return m.group(1) if m else ''


def lib_stem(path):
    m = re.search(r'Tracker library/(?:_original_html/)?(\d{4}|undated)/([^/]+)\.html$', path or '')
    return f'{m.group(1)}/{m.group(2)}' if m else ''


ERR = set()
if a.errors and os.path.exists(a.errors):
    for r in csv.DictReader(open(a.errors, encoding='utf-8')):
        st = lib_stem(r.get('library_file', ''))
        if st: ERR.add(st)
DEL = set()
if a.deletions and os.path.exists(a.deletions):
    for r in csv.DictReader(open(a.deletions, encoding='utf-8')):
        if r.get('sid'): DEL.add(sid_now(r['sid']) if NEW else r['sid'])
        a_ = OLD_AID.get(r.get('aid', ''), r.get('aid', ''))
        if a_ in by_aid.index: DEL.add(by_aid.loc[a_, 'Story ID'] if not isinstance(by_aid.loc[a_, 'Story ID'], pd.Series) else by_aid.loc[a_, 'Story ID'].iloc[0])
IMGMAP = json.load(open(a.img_map)) if a.img_map and os.path.exists(a.img_map) else {}

# cleaned files by current Article ID / old tracker code
files_by_aid, files_by_code, files_by_sid = {}, {}, {}
_extra = list(a.clean_extra) or [x for x in [os.path.join(os.path.dirname(os.path.abspath(a.clean)), 'tmp_recall_rows', 'copies')] if os.path.isdir(x)]
_clean_files = [(a.clean, f) for f in sorted(glob.glob(os.path.join(a.clean, '*', '*.html')))]
_seen_stems = {os.path.relpath(f, a.clean)[:-5] for _, f in _clean_files}
for _x in _extra:   # FINALCHECK-v1 D4: a name already in --clean wins
    _clean_files += [(_x, f) for f in sorted(glob.glob(os.path.join(_x, '*', '*.html'))) if os.path.relpath(f, _x)[:-5] not in _seen_stems]
for _root, f in _clean_files:
    stem = os.path.relpath(f, _root)[:-5]
    aid0 = stem_aid(stem)
    if aid0:
        aid = OLD_AID.get(aid0, aid0)
        # "ws-02304 (jg-190321)" duplicates: the plain name wins
        # RENAME-v1 (origin root fix, 2026-10-28): a file renamed in the sheet can sit in html_clean under its old AND new name
        # (ws02249o-s04423 / ws02249r-s00639); the name whose -s<Story ID> matches the row's current Story ID wins
        cur_sid = ''
        if aid in by_aid.index:
            _s = by_aid.loc[aid, 'Story ID']
            cur_sid = _s if isinstance(_s, str) else _s.iloc[0]
        fits = lambda st: stem_sid(st) == cur_sid
        if aid not in files_by_aid or '(' in files_by_aid[aid][0] or (fits(stem) and not fits(files_by_aid[aid][0])):
            files_by_aid[aid] = (stem, f)
        if stem_sid(stem) and (not cur_sid or fits(stem)):   # NAMING-v2; a stale -s<old Story ID> name is not that story's file
            files_by_sid.setdefault(stem_sid(stem), []).append((stem, f))
    else:
        m = re.search(r'(jg-[0-9a-f]{6})', stem)
        if m: files_by_code.setdefault(m.group(1), (stem, f))

PR = 'Press release' in C.columns
rows_by_story = {}
for r in C.to_dict('records'):
    if r['Story ID']: rows_by_story.setdefault(r['Story ID'], []).append(r)

NBT = nb_texts()
arts, man = {}, {'articles': {}}
IMG = {}            # key -> data uri (new shards)
IMG_SRC = re.compile(r'(<img\b[^>]*?\bsrc=")(data:[^"]+)(")')


BLOB_ATTR = re.compile(r'\s(?:src|srcset|poster|href|data-src)="blob:[^"]*"', re.I)   # F4: saved-page blob: URLs never load


def drop_blobs(page, sid):
    """F4 (2026-10-27): blob: URLs in a saved page point into the original browser session; the viewer can't load them
    and the browser logs "Not allowed to load local resource". The attribute is dropped, the element kept."""
    page, n = BLOB_ATTR.subn('', page)
    if n:
        rep['blob_refs_dropped']['refs'] += n; rep['blob_refs_dropped']['stories'].append(sid)
    return page


def externalize(page, stem):
    m = IMGMAP.get(stem, {})

    def sub(mo):
        u = mo.group(2)
        k = hashlib.sha1(u.encode()).hexdigest()[:16]
        if k in m:
            rep['images']['reused_published'] += 1
            return mo.group(1) + m[k] + mo.group(3)
        if k not in IMG:
            IMG[k] = u
            rep['images']['new'] += 1
            rep['images']['new_bytes'] += len(u)
        return mo.group(1) + 'jgimg:@/' + k + mo.group(3)      # shard number filled in below
    return IMG_SRC.sub(sub, page)


# ---------------------------------------------------------------- PHOTOS-v2: embed cached photos, drop the rest
IE = None
if a.img_cache:
    import img_embed as IE
    CACHE = IE.CacheIndex(a.img_cache)
rep['photos'] = {'pages': 0, 'kept_embedded': 0, 'embedded_from_cache': 0, 'pdf_pages_restored': 0, 'pdf_links_dropped': [],
                 'dropped': 0, 'dropped_by_status': {}, 'local_kept': 0, 'pages_with_drops': 0}
rep['img_gate'] = {'unresolved': [], 'local_paths': 0}
HDR_URL_RX = re.compile(r'<div>[^<]{0,300}?<br\s*/?>\s*(https?://[^<\s]+)\s*<br\s*/?>\s*Saved', re.I)


import media_gate as MG       # MEDIAGATE-v1: only JPEG/PNG/GIF/WebP images (MP4/WebM, MP3/WAV) may be embedded
rep['media_gate'] = {}


def media(page):
    return MG.clean_html(page, rep['media_gate'])


VIDEO_RX = re.compile(r'<video(?=[\s>/])(?:[^>"\']|"[^"]*"|\'[^\']*\')*>', re.I)
POSTER_RX = re.compile(r'\sposter\s*=\s*("[^"]*"|\'[^\']*\')', re.I)
rep['posters'] = {'videos': 0, 'kept_as_img': 0, 'fetched': 0, 'dropped': 0}


def posterize(page, sid, base):
    """MEDIAGATE-v2: a <video> with a poster frame keeps the poster as a static <img> (resolved from the cache by photos(), fetched
    once when missing; dropped, and counted, when it cannot be obtained). The <video> itself is removed by media_gate."""
    def sub(mo):
        rep['posters']['videos'] += 1
        pm = POSTER_RX.search(mo.group(0))
        u = html.unescape(pm.group(1)[1:-1]).strip() if pm else ''
        if not re.match(r'https?://', u):
            rep['posters']['dropped'] += 1
            return mo.group(0)
        if not CACHE.lookup([u]):
            try:
                r = IE.fetch_one([('poster', u, 0)], base, a.img_cache, timeout=15)
                if r['status'] == 'ok':
                    IE.append_manifest(a.img_cache, [dict(r, kind='poster', story_id=sid, aid='', copy_file='', img_index=0, is_lead=0,
                                                          cause_broken='mediagate poster', flag='')])
                    CACHE.by_url[IE.ukey(u)] = os.path.join(a.img_cache, os.path.basename(r['file']))
                    rep['posters']['fetched'] += 1
            except Exception:
                pass
        if not CACHE.lookup([u]):
            rep['posters']['dropped'] += 1
            return mo.group(0)
        rep['posters']['kept_as_img'] += 1
        return '<img src="%s" alt="">' % html.escape(u, quote=True) + mo.group(0)
    return VIDEO_RX.sub(sub, page)


def photos(page, sid, base=''):
    """PHOTOS-v2: every <img> of a copy -> embedded from the cache (data: URI; externalize() moves it to img/1NN.json) or dropped"""
    if IE is None:
        return page
    m = HDR_URL_RX.search(page[:3000])
    base = (m.group(1) if m else '') or base
    page = posterize(page, sid, base)
    ph, restored = rep['photos'], []

    def res(cands, tag):
        u0 = cands[0][1]
        if not re.match(r'(https?:)?//', u0):            # local path: pdf page images, other published files
            mm = re.match(r'^pdf/(jg-[0-9a-f]{6})/(p\d+\.jpg)$', u0)
            if mm and a.pdf_restore and os.path.exists(os.path.join(a.pdf_restore, mm.group(1), mm.group(2))):
                restored.append(u0); ph['pdf_pages_restored'] += 1
                return IE.data_uri(os.path.join(a.pdf_restore, mm.group(1), mm.group(2)))
            if mm or u0.startswith(('pdf/', 'img/')):
                ph['local_kept'] += 1
                return html.escape(u0, quote=True)
            return None
        f = CACHE.lookup([c[1] for c in cands])
        if f:
            ph['embedded_from_cache'] += 1
            return IE.data_uri(f)
        st = CACHE.status([c[1] for c in cands])
        ph['dropped_by_status'][st] = ph['dropped_by_status'].get(st, 0) + 1
        return None
    page, st = IE.resolve_page(page, res, base)
    ph['pages'] += 1; ph['kept_embedded'] += st['kept']; ph['dropped'] += st['dropped']
    ph['pages_with_drops'] += bool(st['dropped'])
    if st['dropped_urls']:
        ph.setdefault('dropped_list', []).append([sid, st['dropped_urls'][:20]])
    if st['dropped']:   # images with no URL at all (src="") never reach res()
        ph['dropped_by_status']['no url (src empty)'] = ph['dropped_by_status'].get('no url (src empty)', 0) + \
            sum(1 for u in st['dropped_urls'] if not re.match(r'(https?:)?//', u) and not u.startswith('pdf/'))
    if restored:   # DECISIONS 2026-10-28: restore the page images, drop the "Full print edition (PDF)" link
        page = re.sub(r'(<meta name="jg-pdf" content=")[^"]*(")', r'\1\2', page, count=1)
        ph['pdf_links_dropped'].append(sid)
    return page


def gate(page, sid):
    if IE is None:
        return
    for u in IE.unresolved(page):
        if re.match(r'^(pdf|img)/', u):
            rep['img_gate']['local_paths'] += 1
        else:
            rep['img_gate']['unresolved'].append([sid, u])


# ---------------------------------------------------------------- AVPREVIEW-v1 fix A: AV display cleanup
AVC, AV_ITEM = None, set()
rep['avpreview'] = {'copies': 0, 'changed': 0, 'removed_words': 0, 'flags': {}, 'changed_sids': []}
if not a.no_av_clean:
    try:
        import av_display_clean as AVC
        _AVT = pd.read_excel(a.cov, sheet_name='Audio & video details', dtype=str).fillna('')
        AV_ITEM = {r['Story ID'] for r in _AVT.to_dict('records')
                   if r['Item type'] in ('Episode', 'Broadcast segment', 'Video clip') and r['Story ID'] in O.index
                   and r['Article ID'] == O.loc[r['Story ID'], 'Article ID']}
    except Exception as _e:
        AVC, AV_ITEM = None, set(); rep['avpreview_error'] = repr(_e)


def av_clean(sid, page):
    if not AVC or sid not in AV_ITEM:
        return page
    out, r = AVC.clean(page, str(O.loc[sid].get('Language', '') or 'English') or 'English')
    rep['avpreview']['copies'] += 1
    if not (r['removed'] or r['rewritten'] or r.get('inserted')):
        out = page   # nothing to clean: the copy stays byte-identical (no re-serialization)
    if out != page:
        rep['avpreview']['changed'] += 1; rep['avpreview']['changed_sids'].append(sid)
        rep['avpreview']['removed_words'] += sum(x[2] for x in r['removed'])
    if r['flags']:
        rep['avpreview']['flags'][sid] = r['flags']
    return out


def nb_row(aid):
    return by_aid.loc[aid] if not isinstance(by_aid.loc[aid], pd.DataFrame) else by_aid.loc[aid].iloc[0]


pages = {}
rep['copy_order'] = {'original_html': 0, 'original_text': 0, 'other_row_html': 0, 'other_row_text': 0,
                     'original_text_over_reprint_html': []}
for sid in O.index:
    if not sid or sid in SKIP:
        continue
    o = O.loc[sid]
    if sid in DEL:
        rep['dropped']['deleted_story'].append(sid); continue
    if PR and str(o.get('Press release', '')).strip().lower() == 'yes':
        rep['dropped']['press_release_story'].append(sid); continue
    rep['stories'] += 1
    rows = sorted(rows_by_story.get(sid, []), key=lambda r: (r['Original or reprint'] != 'Original',))
    orig_rows = [r for r in rows if r['Original or reprint'] == 'Original'] or rows[:1]
    orig_aids = {r.get(c) for r in orig_rows for c in ('Article ID', 'Print Article ID') if r.get(c)}
    cand = []
    for r in rows:
        for c in ('Article ID', 'Print Article ID'):
            if r.get(c) and r[c] in files_by_aid:
                cand.append(files_by_aid[r[c]])
    for code in re.findall(r'jg-[0-9a-f]{6}', str(o.get('Tracker story code', '')).lower()):
        if code in files_by_code:
            cand.append(files_by_code[code])
    cand += [x for x in sorted(files_by_sid.get(sid, []), key=lambda x: (not re.search(r'\d{5}o-s', x[0]), x[0])) if x not in cand]   # NAMING-v2: files named for this Story ID
    for x in [x for x in cand if x[0] in ERR]:
        rep['dropped']['error_copy_files'].append(x[0])
    cand = [x for x in cand if x[0] not in ERR]
    # REPRINT-v2 wrong-copy guard: a file whose Article ID row it cannot belong to (wrong_copies.csv; a ProQuest/NewsBank PDF text on a
    # web row; a title sharing no word with the row's headline) never supplies a story's copy
    keep_c = []
    for x in cand:
        a0 = stem_aid(x[0]); a0 = OLD_AID.get(a0, a0) if a0 else ''
        if a0 and a0 in by_aid.index:
            try:
                head = open(x[1], encoding='utf-8', errors='replace').read(4000)
            except OSError:
                head = ''
            mt = re.search(r'<title>(.*?)</title>', head, re.S | re.I)
            title = html.unescape(mt.group(1)).strip() if mt else ''
            why = RR.copy_mismatch(nb_row(a0).to_dict(), title, 'nb' if 'jg-pdf-text' in head else 'html')
            if why:
                rep['dropped']['wrong_copy'].append([sid, x[0], why]); continue
            sus = RR.copy_suspect(nb_row(a0).to_dict(), title)
            if sus:
                rep['wrong_copy_suspect'].append([sid, x[0], sus])
        keep_c.append(x)
    cand = keep_c
    # ORIGIN ROOT FIX D: the Original's own HTML (its Article ID / Print Article ID file, or its <aid>o-s<sid> name) first,
    # then the Original's NewsBank/ProQuest text, then any other row's HTML, then another row's text
    is_orig = lambda st: stem_aid(st) and (OLD_AID.get(stem_aid(st), stem_aid(st)) in orig_aids)
    own = [x for x in cand if is_orig(x[0])]   # legacy tracker copies (jg- code names, shared across stories) are not the Original's own
    other = [x for x in cand if x not in own]
    oaid = o.get('Article ID', '')
    own_text = next((x for x in [oaid] + [r.get('Article ID') for r in orig_rows] if x in NBT and x not in RR.WRONG_COPIES), None)
    other_text = next((r.get('Article ID') for r in rows if r.get('Article ID') in NBT and r.get('Article ID') not in RR.WRONG_COPIES), None)
    av = sid in AV_ITEM
    pub = str(o.get('Publisher link', '') or '')
    if own or (not own_text and other):
        chosen = (own or other)[0]
        page = av_clean(sid, drop_blobs(externalize(media(photos(open(chosen[1], encoding='utf-8', errors='replace').read(), sid, pub)), chosen[0]), sid))
        gate(page, sid)
        pages[sid] = page; rep['from_clean'] += 1; rep['files'].append([sid, chosen[0]])
        rep['copy_order']['original_html' if own else 'other_row_html'] += 1
        continue
    aid = own_text or other_text
    if aid:
        pages[sid] = av_clean(sid, nb_page(NBT[aid], nb_row(aid), av))
        rep['from_newsbank_text'] += 1; rep['files'].append([sid, 'texts/nb/' + aid])
        rep['copy_order']['original_text' if own_text else 'other_row_text'] += 1
        if own_text and other:
            rep['copy_order']['original_text_over_reprint_html'].append([sid, other[0][0]])
        continue
    rep['dropped']['no_clean_copy'].append(sid)

# RELCOPIES-v1 make_copies: official press-release copies (Tracker library/Press releases/<year>/<prid>.html, cleaned like an
# article) keyed by Release ID in articles/releases.json; the Press releases tab opens them in the story panel's viewer.
# RELIMG-v1 (rp-ui 2026-10-28, backend review #7): their photos leave the page like story photos: data: images go to the
# img/1NN.json shards as jgimg: refs (queued after every story image, so the story shards' refs do not move); a photo wider
# than REL_IMG_W px is downscaled to that width (JPEG quality REL_IMG_Q) when that makes it smaller. The page text is
# byte-identical; only <img src> values change.
REL_IMG_W, REL_IMG_Q = 1200, 75
rep['release_images'] = {'refs': 0, 'downscaled': 0, 'bytes_before': 0, 'bytes_after': 0}


def _shrink(u):
    """data: URI -> the same photo at most REL_IMG_W px wide (JPEG), or u unchanged (narrow, undecodable, or not smaller)"""
    import base64, io
    mo = re.match(r'data:(image/[a-z+.-]+);base64,(.*)$', u, re.S)
    if not mo:
        return u
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(base64.b64decode(mo.group(2))))
        if im.width <= REL_IMG_W:
            return u
        if im.mode not in ('RGB', 'L'):
            im = im.convert('RGB')
        im = im.resize((REL_IMG_W, max(1, round(im.height * REL_IMG_W / im.width))), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=REL_IMG_Q, optimize=True)
        v = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return u
    if len(v) >= len(u):
        return u
    rep['release_images']['downscaled'] += 1
    return v


def rel_externalize(page):
    def sub(mo):
        u = _shrink(mo.group(2))
        ri = rep['release_images']
        ri['refs'] += 1; ri['bytes_before'] += len(mo.group(2)); ri['bytes_after'] += len(u)
        k = hashlib.sha1(u.encode()).hexdigest()[:16]
        if k not in IMG:
            IMG[k] = u
            rep['images']['new'] += 1
            rep['images']['new_bytes'] += len(u)
        return mo.group(1) + 'jgimg:@/' + k + mo.group(3)      # shard number filled in below
    return IMG_SRC.sub(sub, page)


REL_PAGES = {}
if a.releases and os.path.isdir(a.releases):
    for _f in sorted(glob.glob(os.path.join(a.releases, '*', 'pr[0-9][0-9][0-9][0-9][0-9].html'))):
        _pid = os.path.basename(_f)[:-5]
        _page = drop_blobs(media(photos(open(_f, encoding='utf-8', errors='replace').read(), _pid)), _pid)   # PHOTOS-v2 + MEDIAGATE-v1
        gate(_page, _pid)
        REL_PAGES[_pid] = rel_externalize(_page)

# image shards: new images in img/100.json, 101.json … (<= shard size)
shard, size, n = {}, 0, 100
where = {}
for k, u in IMG.items():
    if size + len(u) > a.shard_mb * 1e6 and shard:
        os.makedirs(os.path.join(a.out, 'img'), exist_ok=True)
        json.dump(shard, open(os.path.join(a.out, 'img', f'{n}.json'), 'w'), separators=(',', ':'))
        n += 1; shard, size = {}, 0
    shard[k] = u; size += len(u); where[k] = n
if shard:
    os.makedirs(os.path.join(a.out, 'img'), exist_ok=True)
    json.dump(shard, open(os.path.join(a.out, 'img', f'{n}.json'), 'w'), separators=(',', ':'))
for sid, page in pages.items():
    pages[sid] = re.sub(r'jgimg:@/([0-9a-f]{16})', lambda mo: f'jgimg:{where[mo.group(1)]}/{mo.group(1)}', page)
for _pid, page in REL_PAGES.items():   # RELIMG-v1
    REL_PAGES[_pid] = re.sub(r'jgimg:@/([0-9a-f]{16})', lambda mo: f'jgimg:{where[mo.group(1)]}/{mo.group(1)}', page)

# year shards, split above the size limit
by_year = {}
for sid in sorted(pages):
    by_year.setdefault(year_of(sid), []).append(sid)
for y, sids in sorted(by_year.items()):
    part, size, k = {}, 0, 1
    for sid in sids:
        b = len(pages[sid].encode('utf-8'))
        if part and size + b > a.shard_mb * 1e6:
            arts[f'{y}.json' if k == 1 else f'{y}-{k}.json'] = part; k += 1; part, size = {}, 0
        part[sid] = pages[sid]; size += b
    if part:
        arts[f'{y}.json' if k == 1 else f'{y}-{k}.json'] = part
for yf, d in arts.items():
    for sid in d:
        man['articles'][sid] = f'articles/{yf}'
rep['copies'] = len(man['articles'])
# RELIMG-v1 (rp-ui, backend review #7): the release pages are built before the image shards (see "RELCOPIES-v1
# make_copies" above) and filed into articles/releases.json here
rep['release_copies'] = 0
if REL_PAGES:
    _rp, _size, _k = {}, 0, 1
    for _pid in REL_PAGES:   # glob order, as before
        _page = REL_PAGES[_pid]
        _b = len(_page.encode('utf-8'))
        if _rp and _size + _b > a.shard_mb * 1e6:
            arts['releases.json' if _k == 1 else f'releases-{_k}.json'] = _rp; _k += 1; _rp, _size = {}, 0
        _rp[_pid] = _page; _size += _b; rep['release_copies'] += 1
    if _rp:
        arts['releases.json' if _k == 1 else f'releases-{_k}.json'] = _rp
    for _yf in [x for x in arts if x.startswith('releases')]:
        for _pid in arts[_yf]:
            man['articles'][_pid] = f'articles/{_yf}'
# MEDIAGATE-v1 belt: nothing disallowed may reach the output (pages, release pages, photo shards); exit 4 otherwise
_bad = []
for _yf, _d in arts.items():
    for _k, _p in _d.items():
        _bad += [(_yf, _k, t) for t, _ in MG.scan(_p)]
for _k, _u in IMG.items():
    if not MG.allowed_data(_u):
        _bad.append(('img', _k, MG.mime_of(_u)))
rep['media_gate']['leftover'] = len(_bad)
if _bad:
    print('MEDIA GATE: %d disallowed media left, first: %s' % (len(_bad), _bad[:5]), file=sys.stderr)
    sys.exit(4)
write_out(arts, man)
# what changed against the published copies
try:
    old = json.load(open(os.path.join(a.src, 'articles', 'manifest.json')))['articles']
    code_sid = {}
    for sid, o in O.iterrows():
        for code in re.findall(r'jg-[0-9a-f]{6}', str(o.get('Tracker story code', '')).lower()):
            code_sid.setdefault(code, sid)
    old_sids = {code_sid.get(k, sid_now(k)) for k in old}
    rep['vs_published'] = {'published_keys': len(old), 'published_stories': len(old_sids),
                           'now': len(man['articles']), 'gone': sorted(s for s in old_sids - set(man['articles']) if s)[:400],
                           'gone_count': len({s for s in old_sids - set(man['articles']) if s}),
                           'new_count': len(set(man['articles']) - old_sids)}
except Exception as e:
    rep['vs_published'] = {'error': repr(e)}
sizes = {f: os.path.getsize(os.path.join(a.out, 'articles', f)) for f in os.listdir(os.path.join(a.out, 'articles'))}
if os.path.isdir(os.path.join(a.out, 'img')):
    sizes.update({'img/' + f: os.path.getsize(os.path.join(a.out, 'img', f)) for f in os.listdir(os.path.join(a.out, 'img'))})
rep['sizes_mb'] = {k: round(v / 1e6, 2) for k, v in sorted(sizes.items())}
rep['total_mb'] = round(sum(sizes.values()) / 1e6, 1)
for k in list(rep['dropped']):
    rep['dropped'][k + '_count'] = len(rep['dropped'][k])
rep['img_gate']['unresolved_count'] = len(rep['img_gate']['unresolved'])
if a.report:
    json.dump(rep, open(a.report, 'w'), indent=1)
print(json.dumps({k: rep[k] for k in ('copies', 'stories', 'from_clean', 'from_newsbank_text', 'release_copies', 'release_images', 'images', 'total_mb')} |
                 {'dropped': {k: v for k, v in rep['dropped'].items() if k.endswith('_count')}}))
if IE is not None:
    print(json.dumps({'photos': {k: v for k, v in rep['photos'].items() if k != 'dropped_list'}, 'img_gate': {'unresolved': rep['img_gate']['unresolved_count'], 'local_paths': rep['img_gate']['local_paths']},
                      'avpreview': {k: v for k, v in rep['avpreview'].items() if k != 'changed_sids'},
                      'copy_order': {k: (len(v) if isinstance(v, list) else v) for k, v in rep['copy_order'].items()}}))
    if a.img_strict and rep['img_gate']['unresolved_count']:
        print('IMG GATE: %d images would not load' % rep['img_gate']['unresolved_count'], file=sys.stderr)
        sys.exit(3)
