"""(Staged by agent-code; apply_all_patches.py installs this file as code/make_copies.py.)
Viewer copies (articles/*.json + manifest) for the tracker's saved-copy viewer and its full-text search.

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
  Output: OUT/articles/<year>.json (split <year>-2.json… above 12 MB), OUT/articles/manifest.json, OUT/img/1NN.json,
  report (counts, dropped, sizes). The tracker's search index reads only these copies (indexSaved -> manifest).

Legacy mode (no --clean; T14/T23 behaviour, kept for old runs): add texts/tracker + NewsBank copies to SRC's copies.
ID migration (T23): works on the workbook before or after it (Old Article ID columns; jg-NNNNN -> sNNNNN, --sidmap).
"""
import sys, os, json, glob, html, argparse, re, csv, hashlib
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('cov'); ap.add_argument('out')
ap.add_argument('--nb'); ap.add_argument('--tracker'); ap.add_argument('--sidmap')
ap.add_argument('--skip', default='')
ap.add_argument('--clean', help='folder of cleaned library HTML (<year>/<old Article ID>.html) -> rebuild mode (T40)')
ap.add_argument('--img-map'); ap.add_argument('--errors'); ap.add_argument('--deletions'); ap.add_argument('--report')
ap.add_argument('--shard-mb', type=float, default=12.0)
ap.add_argument('--releases', help='RELCOPIES-v1: cleaned press-release copies <year>/prNNNNN.html (work/html_clean/press_releases) '
                '-> articles/releases.json keyed by Release ID')
a = ap.parse_args()
SKIP = set(x for x in a.skip.split(',') if x)

C = pd.read_excel(a.cov, sheet_name='Coverage', dtype=str).fillna('')
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


def nb_page(t, r):
    e = html.escape
    paras = [p.strip() for p in re.split(r'\n\s*\n', t.get('text', '')) if p.strip()]
    if len(paras) < 2: paras = [p.strip() for p in t.get('text', '').split('\n') if p.strip()]
    meta = ' · '.join(x for x in [r['Outlet'], r['Date'], t.get('section') and f"Section: {t['section']}", r['Page'] and f"Page {r['Page']}", t.get('words') and f"{t['words']} words"] if x)
    by = t.get('author') or r['Author / byline']
    body = ''.join(f'<p>{e(p)}</p>' for p in paras)
    cite = f'<p class="pdf-cap">{e(t["citation"])}</p>' if t.get('citation') else ''
    return (f'<html><head><title>{e(r["Headline"] or t.get("headline", ""))}</title></head><body><article class="jg-pdf-text">'
            f'<p class="pdf-cap">Text of the NewsBank PDF ({e(t.get("pdf", ""))}{", item " + str(t["pos"]) if t.get("pos") else ""})</p>'
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
       'dropped': {'deleted_story': [], 'press_release_story': [], 'error_copy_files': [], 'no_clean_copy': []},
       'images': {'reused_published': 0, 'new': 0, 'new_bytes': 0}, 'blob_refs_dropped': {'refs': 0, 'stories': []}, 'files': []}


def stem_aid(stem):
    """NAMING-v2 (agent-tabs 2026-10-28): old names carry the OLD Article ID ("nb-04130", "ws-02304 (jg-190321)"); current
    library names are <nb|pq|ws><Article ID><o|r>-s<Story ID> (README), e.g. ws09735o-s04701, nb05457r-s00044 -> '09735'"""
    m = re.search(r'((?:nb|ws|pq)-\d{5})', stem)
    if m: return m.group(1)
    m = re.match(r'^(?:nb|ws|pq)(\d{5})[or]?(?:-s\d{5})?$', stem.split('/')[-1])
    return m.group(1) if m else ''


def stem_sid(stem):
    m = re.search(r'-(s\d{5})$', stem.split('/')[-1])
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
for f in sorted(glob.glob(os.path.join(a.clean, '*', '*.html'))):
    stem = os.path.relpath(f, a.clean)[:-5]
    aid0 = stem_aid(stem)
    if aid0:
        aid = OLD_AID.get(aid0, aid0)
        # "ws-02304 (jg-190321)" duplicates: the plain name wins
        if aid not in files_by_aid or '(' in files_by_aid[aid][0]:
            files_by_aid[aid] = (stem, f)
        if stem_sid(stem): files_by_sid.setdefault(stem_sid(stem), []).append((stem, f))   # NAMING-v2
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


pages = {}
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
    cand = []
    for r in rows:
        for c in ('Article ID', 'Print Article ID'):
            if r.get(c) and r[c] in files_by_aid:
                cand.append(files_by_aid[r[c]])
    for code in re.findall(r'jg-[0-9a-f]{6}', str(o.get('Tracker story code', '')).lower()):
        if code in files_by_code:
            cand.append(files_by_code[code])
    cand += [x for x in sorted(files_by_sid.get(sid, []), key=lambda x: (not re.search(r'\d{5}o-s', x[0]), x[0])) if x not in cand]   # NAMING-v2: files named for this Story ID
    chosen = None
    for stem, f in cand:
        if stem in ERR:
            rep['dropped']['error_copy_files'].append(stem); continue
        chosen = (stem, f); break
    if chosen:
        page = drop_blobs(externalize(open(chosen[1], encoding='utf-8', errors='replace').read(), chosen[0]), sid)
        pages[sid] = page; rep['from_clean'] += 1; rep['files'].append([sid, chosen[0]])
        continue
    aid = o.get('Article ID', '')
    if aid not in NBT:   # NAMING-v2: else the NewsBank text (incl. OCR clips) of another row of the story, Originals first
        aid = next((r.get('Article ID') for r in rows if r.get('Article ID') in NBT), aid)
    if aid in NBT:
        pages[sid] = nb_page(NBT[aid], by_aid.loc[aid] if not isinstance(by_aid.loc[aid], pd.DataFrame) else by_aid.loc[aid].iloc[0])
        rep['from_newsbank_text'] += 1; rep['files'].append([sid, 'texts/nb/' + aid]); continue
    rep['dropped']['no_clean_copy'].append(sid)

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
# RELCOPIES-v1 make_copies: official press-release copies (Tracker library/Press releases/<year>/<prid>.html, cleaned like an
# article) keyed by Release ID in articles/releases.json; the Press releases tab opens them in the story panel's viewer
rep['release_copies'] = 0
if a.releases and os.path.isdir(a.releases):
    _rp, _size, _k = {}, 0, 1
    for _f in sorted(glob.glob(os.path.join(a.releases, '*', 'pr[0-9][0-9][0-9][0-9][0-9].html'))):
        _pid = os.path.basename(_f)[:-5]
        _page = drop_blobs(open(_f, encoding='utf-8', errors='replace').read(), _pid)
        _b = len(_page.encode('utf-8'))
        if _rp and _size + _b > a.shard_mb * 1e6:
            arts['releases.json' if _k == 1 else f'releases-{_k}.json'] = _rp; _k += 1; _rp, _size = {}, 0
        _rp[_pid] = _page; _size += _b; rep['release_copies'] += 1
    if _rp:
        arts['releases.json' if _k == 1 else f'releases-{_k}.json'] = _rp
    for _yf in [x for x in arts if x.startswith('releases')]:
        for _pid in arts[_yf]:
            man['articles'][_pid] = f'articles/{_yf}'
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
if a.report:
    json.dump(rep, open(a.report, 'w'), indent=1)
print(json.dumps({k: rep[k] for k in ('copies', 'stories', 'from_clean', 'from_newsbank_text', 'release_copies', 'images', 'total_mb')} |
                 {'dropped': {k: v for k, v in rep['dropped'].items() if k.endswith('_count')}}))
