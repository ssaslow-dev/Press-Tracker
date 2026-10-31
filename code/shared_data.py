#!/usr/bin/env python3
"""shared_data: one pre-parsed snapshot of the coverage workbook + saved-copy text index.

    from shared_data import load
    d = load()
    d.coverage d.originals d.removed d.av d.unlinked_print d.press_releases d.bills  (DataFrames)
    d.text(article_id) -> cleaned plain text of the chosen saved copy ('' if none)
    d.copy_path(article_id) -> path of the chosen saved copy (None if none); d.copy_paths(aid) -> all candidates
    d.meta -> dict (source sha256, built time, row counts, text coverage)

Rebuild after each master write:  python3 shared_data.py --rebuild [path.xlsx]

Storage (L/work/shared/): tables.pkl (pickle; pyarrow absent), texts.db (sqlite, zlib-compressed text,
one row per Article ID), meta.json.  Extra columns: '<col>__href' (hyperlink target, only for columns that
have any), '_row' (Excel row number), '_hidden' (row hidden flag).

Text index (COPIES-v1: newest valid copy wins; valid = >=150 chars of cleaned text). Candidates per row:
  1. File name / File name 2 ending .html, found by basename in the copy roots below
  2. new-format library names <nb|pq|ws><AID><o|r>[-sNNNNN].html keyed by Article ID / Print Article ID
  3. old-format html_clean names <nb|pq|ws>-<OLDID>.html keyed by Old Article ID / Old Print Article ID
  4. jg-xxxxxx.html (Tracker story code, 'Tracker story code' col)
  5. NewsBank PDF text work/texts/nb/<old aid>.json
  6. (fallback only, no row-level copy) story-level pub2 viewer copy articles/<sid>.json
Roots: work/html_clean, work/texts/nb, work/tmp_agent-v20-final/pub2/articles, work/tmp_copies_apply/stage,
work/tmp_recall_rows/copies, work/tmp_origin_fetch/copies. Mtime decides; fallback (6) only if nothing else.
"""
import os, sys, re, json, glob, time, zlib, sqlite3, hashlib, pickle, html as _html, warnings
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
L = os.path.dirname(HERE)
WORK = os.path.join(L, 'work')
SHARED = os.path.join(WORK, 'shared')
DEFAULT_XLSX = os.path.join(WORK, 'coverage_current.xlsx')
TABLES = {'Coverage': 'coverage', 'Originals': 'originals', 'Removed': 'removed',
          'Audio & video details': 'av', 'AV': 'av', 'Unlinked print pages': 'unlinked_print',
          'Press releases': 'press_releases', 'Bills': 'bills'}
HTML_ROOTS = ['html_clean', 'tmp_copies_apply/stage', 'tmp_recall_rows/copies', 'tmp_origin_fetch/copies']
MINCHARS = 150


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- text cleaning
class _T(HTMLParser):
    SKIP = {'script', 'style', 'head', 'noscript', 'svg', 'template'}
    BLOCK = {'p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr', 'figcaption', 'blockquote', 'article', 'section', 'table'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.title, self._in_title = [], 0, '', False

    def handle_starttag(self, t, a):
        if t == 'title':
            self._in_title = True
        if t in self.SKIP and t != 'head':
            self.skip += 1
        elif t == 'head':
            self.skip += 1
        if t in self.BLOCK:
            self.out.append('\n')

    def handle_endtag(self, t):
        if t == 'title':
            self._in_title = False
        if t in self.SKIP:
            self.skip = max(0, self.skip - 1)
        if t in self.BLOCK:
            self.out.append('\n')

    def handle_data(self, d):
        if self._in_title:
            self.title += d
        if not self.skip:
            self.out.append(d)


def clean_text(raw):
    """HTML (or plain text) -> plain text; paragraphs separated by blank-free newlines."""
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', 'replace')
    raw = re.sub(r'<img\b[^>]*>', ' ', raw, flags=re.I)  # drop (possibly huge) data: images
    p = _T()
    try:
        p.feed(raw)
        p.close()
    except Exception:
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', raw)).strip()
    t = ''.join(p.out).replace('\xa0', ' ')
    lines = [re.sub(r'[ \t\r\f\v]+', ' ', x).strip() for x in t.split('\n')]
    return '\n'.join(x for x in lines if x)


def _clean_file(path):
    try:
        with open(path, 'rb') as f:
            return clean_text(f.read())
    except Exception:
        return ''


def _worker(item):
    key, kind, path = item
    if kind == 'nbjson':
        try:
            return key, kind, path, (json.load(open(path)).get('text') or '').strip()
        except Exception:
            return key, kind, path, ''
    return key, kind, path, _clean_file(path)


# ---------------------------------------------------------------- workbook
def read_workbook(xlsx):
    import pandas as pd, openpyxl
    wb = openpyxl.load_workbook(xlsx)  # full mode: hyperlinks + row_dimensions
    out = {}
    for ws in wb.worksheets:
        name = TABLES.get(ws.title)
        if not name:
            continue
        hdr = [c.value for c in ws[1]]
        ncol = len(hdr)
        rows, hid, hrefs = [], [], {}
        for r in range(2, ws.max_row + 1):
            vals = [ws.cell(r, c).value for c in range(1, ncol + 1)]
            for c in range(1, ncol + 1):
                h = ws.cell(r, c).hyperlink
                if h is not None:
                    hrefs.setdefault(c - 1, {})[len(rows)] = h.target or ('#' + h.location if h.location else None)
            rows.append(vals)
            hid.append(bool(ws.row_dimensions[r].hidden) if r in ws.row_dimensions else False)
        cols = [str(h) if h is not None else f'_col{i}' for i, h in enumerate(hdr)]
        df = pd.DataFrame(rows, columns=cols, dtype=object)
        for ci, m in hrefs.items():
            s = [None] * len(rows)
            for i, v in m.items():
                s[i] = v
            df[cols[ci] + '__href'] = pd.Series(s, dtype=object)
        df['_row'] = range(2, ws.max_row + 1)
        df['_hidden'] = hid
        df = df.astype(object).where(df.notna(), None)
        key = name
        if key in out and len(df) < len(out[key]):  # AV alias: keep the longer
            continue
        out[key] = df
    return out


# ---------------------------------------------------------------- text index
def _s(v):
    return '' if v is None or (isinstance(v, float) and v != v) else str(v).strip()


def build_index(cov):
    """returns (cands: {aid: [(kind, path)]}, story_fallback {sid: path-key}) before cleaning."""
    files = {}  # basename -> [paths]
    newfmt, oldfmt, jg = {}, {}, {}
    for root in HTML_ROOTS:
        for p in glob.glob(os.path.join(WORK, root, '**', '*.html'), recursive=True):
            b = os.path.basename(p)
            files.setdefault(b, []).append(p)
            m = re.match(r'^(nb|pq|ws)(\d{5})[or](?:-s\d+)?\.html$', b)
            if m:
                newfmt.setdefault(m.group(2), []).append(p)
                continue
            m = re.match(r'^(nb|pq|ws)-(\d{5})(?: \((jg-[0-9a-f]{6})\))?\.html$', b)
            if m:
                oldfmt.setdefault(f'{m.group(1)}-{m.group(2)}', []).append(p)
                if m.group(3):
                    jg.setdefault(m.group(3), []).append(p)
                continue
            m = re.match(r'^(jg-[0-9a-f]{6})\.html$', b)
            if m:
                jg.setdefault(m.group(1), []).append(p)
    cands = {}
    for _, r in cov.iterrows():
        aid = _s(r['Article ID'])
        if not aid:
            continue
        c = []
        for col in ('File name', 'File name 2'):
            fn = os.path.basename(_s(r.get(col)))
            if fn.endswith('.html'):
                c += [('html', p) for p in files.get(fn, [])]
        for col in ('Article ID', 'Print Article ID'):
            c += [('html', p) for p in newfmt.get(_s(r.get(col)), [])]
        for col in ('Old Article ID', 'Old Print Article ID'):
            o = _s(r.get(col))
            if o:
                c += [('html', p) for p in oldfmt.get(o, [])]
                j = os.path.join(WORK, 'texts', 'nb', o + '.json')
                if o.startswith('nb-') and os.path.exists(j):
                    c.append(('nbjson', j))
        tj = _s(r.get('Tracker story code'))
        if tj:
            c += [('html', p) for p in jg.get(tj, [])]
        # de-dup keep order
        seen, cc = set(), []
        for k in c:
            if k[1] not in seen:
                seen.add(k[1]); cc.append(k)
        if cc:
            cands[aid] = cc
    return cands


def build_texts(cov, db_path, log=print):
    from multiprocessing import Pool
    cands = build_index(cov)
    # story-level viewer copies as fallback
    story = {}
    for p in glob.glob(os.path.join(WORK, 'tmp_agent-v20-final', 'pub2', 'articles', '*.json')):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        if isinstance(d, dict):
            mt = os.path.getmtime(p)
            for sid, h in d.items():
                if isinstance(h, str):
                    story[sid] = (p, mt, h)
    items = {}
    for aid, cc in cands.items():
        for kind, p in cc:
            items[p] = (aid, kind)
    paths = list(items)
    log(f'cleaning {len(paths)} candidate files ...')
    with Pool(min(8, os.cpu_count() or 2)) as pool:
        res = pool.map(_worker, [(items[p][0], items[p][1], p) for p in paths], chunksize=32)
    txt = {p: t for _, _, p, t in res}
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    con.execute('create table t(aid text primary key, path text, kind text, mtime real, chars int, paths text, text blob)')
    sid_of = {_s(r['Article ID']): _s(r.get('Story ID')) for _, r in cov.iterrows()}
    n_row = n_fb = 0
    for aid in dict.fromkeys(_s(a) for a in cov['Article ID'] if _s(a)):
        valid = [(os.path.getmtime(p), k, p) for k, p in cands.get(aid, []) if len(txt.get(p, '')) >= MINCHARS]
        allp = [p for _, p in cands.get(aid, [])]
        if valid:
            mt, k, p = max(valid)
            t = txt[p]; n_row += 1
        else:
            sid = sid_of.get(aid)
            if sid in story and len(t := clean_text(story[sid][2])) >= MINCHARS:
                p, mt, k = f'{story[sid][0]}#{sid}', story[sid][1], 'story'; n_fb += 1
            else:
                if allp:
                    con.execute('insert into t values(?,?,?,?,?,?,?)', (aid, None, None, None, 0, json.dumps(allp), b''))
                continue
        con.execute('insert into t values(?,?,?,?,?,?,?)',
                    (aid, p, k, mt, len(t), json.dumps(allp or [p]), zlib.compress(t.encode('utf-8'), 6)))
    con.commit(); con.close()
    log(f'texts: {n_row} row-level, {n_fb} story-level fallback')
    return n_row, n_fb


def rebuild(xlsx=DEFAULT_XLSX, log=print):
    import pandas as pd
    t0 = time.time()
    os.makedirs(SHARED, exist_ok=True)
    xlsx = os.path.abspath(xlsx)
    sha = sha256(xlsx)
    tabs = read_workbook(xlsx)
    log(f'read workbook {time.time()-t0:.0f}s: ' + ', '.join(f'{k}={len(v)}' for k, v in tabs.items()))
    for k in ('coverage', 'originals', 'removed', 'av', 'unlinked_print', 'press_releases', 'bills'):
        tabs.setdefault(k, pd.DataFrame())
    n_row, n_fb = build_texts(tabs['coverage'], os.path.join(SHARED, 'texts.db'), log)
    cov = tabs['coverage']
    yes = cov[cov['Saved Copy?'] == 'Yes']
    con = sqlite3.connect(os.path.join(SHARED, 'texts.db'))
    have = {a for (a,) in con.execute('select aid from t where chars>0')}
    con.close()
    with_text = sum(1 for a in yes['Article ID'] if _s(a) in have)
    tmp = os.path.join(SHARED, 'tables.pkl.tmp')
    with open(tmp, 'wb') as f:
        pickle.dump(tabs, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, os.path.join(SHARED, 'tables.pkl'))
    meta = {'source': xlsx, 'source_sha256': sha, 'built_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'rows': {k: len(v) for k, v in tabs.items()}, 'storage': 'pickle',
            'text': {'row_level': n_row, 'story_fallback': n_fb, 'saved_copy_yes': len(yes),
                     'saved_copy_yes_with_text': with_text,
                     'pct': round(100 * with_text / max(1, len(yes)), 1)}}
    json.dump(meta, open(os.path.join(SHARED, 'meta.json'), 'w'), indent=1)
    log(f'done {time.time()-t0:.0f}s; Saved Copy=Yes with text: {with_text}/{len(yes)} ({meta["text"]["pct"]}%)')
    return meta


# ---------------------------------------------------------------- loading
class Data:
    def __init__(self, tabs, meta, db):
        self.__dict__.update(tabs)
        self.meta = meta
        self._db = db
        self._con = None

    def _c(self):
        if self._con is None:
            self._con = sqlite3.connect(f'file:{self._db}?mode=ro', uri=True)
        return self._con

    def text(self, aid):
        r = self._c().execute('select text from t where aid=?', (str(aid).strip(),)).fetchone()
        return zlib.decompress(r[0]).decode('utf-8') if r and r[0] else ''

    def copy_path(self, aid):
        r = self._c().execute('select path from t where aid=?', (str(aid).strip(),)).fetchone()
        return r[0] if r else None

    def copy_paths(self, aid):
        r = self._c().execute('select paths from t where aid=?', (str(aid).strip(),)).fetchone()
        return json.loads(r[0]) if r and r[0] else []


def load(shared=SHARED, check=True):
    mp = os.path.join(shared, 'meta.json')
    if not os.path.exists(mp):
        raise FileNotFoundError('no snapshot; run: python3 shared_data.py --rebuild')
    with open(mp) as f:
        meta = json.load(f)
    with open(os.path.join(shared, 'tables.pkl'), 'rb') as f:
        tabs = pickle.load(f)
    if check and os.path.exists(DEFAULT_XLSX):
        st = os.stat(DEFAULT_XLSX)
        # cheap path: only hash when size/mtime differ from what we recorded
        if meta.get('src_stat') != [st.st_size, int(st.st_mtime)]:
            cur = sha256(DEFAULT_XLSX)
            if cur != meta['source_sha256']:
                warnings.warn(f"shared_data snapshot is STALE: built from {meta['source_sha256'][:8]}, "
                              f"coverage_current.xlsx is {cur[:8]}. Run shared_data.py --rebuild", stacklevel=2)
            else:
                meta['src_stat'] = [st.st_size, int(st.st_mtime)]
                try:
                    with open(mp, 'w') as f:
                        json.dump(meta, f, indent=1)
                except OSError:
                    pass
    return Data(tabs, meta, os.path.join(shared, 'texts.db'))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--rebuild':
        rebuild(a[1] if len(a) > 1 else DEFAULT_XLSX)
    else:
        print(__doc__)
