#!/usr/bin/env python3
"""make_handoff_kit.py: the account-handoff kit, regenerable at any time (agent-handoffkit, 2026-10-28; README "Handoff kit").

The kit lets a fresh Claude on ANOTHER account (a) republish the tracker exactly as live, (b) rebuild it from source
byte-identical, (c) keep running the Update button / sheet task. Python cannot call the Artifact tools, so the live
state is tracked in a LEDGER that the publishing session feeds after every publish:

  python3 -I code/make_handoff_kit.py record --listing build/handoff/live_listing.txt --map <publish map.json> [--map …]
      listing = the text of Artifact `list` scope "files" on the live tracker, saved verbatim (gives the version, every
      path + bytes + contentType, and the stored capabilities declaration).
      map = the publish map of the publish(es) since the last record: {"file_path", "files", "file_sha256",
      "index_sha256"} or {"publishes": [{file_path, page_sha256, files}], "sha256": {...}} (make_publish2.py style).
      Every live file must resolve to a local blob of the listed size (and of the map's sha when it gives one).
      Lookup order: --fetched DIR (Artifact `read` with `paths`, out_dir=DIR), the maps' sources, the content store,
      the previous ledger, then --root DIRs. Resolved blobs are copied into work/live_store/<sha256> so later builds
      never depend on scratch folders. Unresolved paths -> build/handoff/need_fetch.json and exit 2: read exactly those
      with the Artifact tool (`read`, `paths`, out_dir=work/handoff_fetch) and re-run with --fetched work/handoff_fetch.
  python3 -I code/make_handoff_kit.py build [--no-test] [--no-zip] [--part-mb 90] [--keep-test]
      (= build/build.sh --kit) assembles handoff_kit/publish (ledger files at their published paths + MANIFEST.tsv,
      capabilities.json, BATCHES.json) and handoff_kit/source (docs, status, code, build minus outputs, work/ inputs,
      open handoff/spec files, db_export/), runs the clean-dir rebuild test (source/ only: build.sh LIB + PIPELINE page
      sha = live page sha; make_copies reproduces articles/ + img/100+; pipeline/ and data/ compared), writes
      REBUILD_TEST.json, KIT_README.md, SHA256SUMS.txt and zips into parts of <= --part-mb (default 90 MB).
  python3 -I code/make_handoff_kit.py verify [KIT_DIR]
      checks publish/MANIFEST.tsv and source/FILES.sha256 against the unzipped tree (run on the new account).

  python3 -I code/make_handoff_kit.py facts [--write]
      prints the generated FACTS block (live version, page sha, file count, storage, master sha, row counts, next free IDs, suite
      count). --write refreshes the block between the FACTS markers in L/START_HERE.md. `build` does the same into the kit's
      START_HERE.md (kit root and source/), so the numbers in the kit cannot be older than the kit (COLDSTART-v1).

DB carry-over (HANDOFF 0.5): the coordinator exports the artifact databases with ArtifactData list/get into
work/db_export/<artifact>/<collection>/<doc_id>.json; build copies them to source/db_export/, converts them with
code/db_reseed.py into <=50-write batch payloads (source/db_export/_batches/) and writes the counts into KIT_README.
"""
import argparse, datetime, hashlib, json, mimetypes, os, re, shutil, subprocess, sys, tempfile, zipfile, zlib, base64, glob

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HK = os.path.join(L, 'build', 'handoff')
LEDGER = os.path.join(HK, 'ledger.json')
STORE = os.path.join(L, 'work', 'live_store')
KIT = os.path.join(L, 'handoff_kit')
DB_EXPORT = os.path.join(L, 'work', 'db_export')
MB = 1_000_000

# ---- what goes into source/ -------------------------------------------------------------------------------------
SRC_DOCS = ['README.md', 'CONTRACT.md', 'DECISIONS.md', 'BOARD.md', 'TONE_GUIDE.md', 'HANDOFF.md',
            'handoff_ctx_main.md', 'handoff_old_extract.md']
SRC_TREES = ['code', 'status']
BUILD_EXCLUDE_DIRS = {'blocks', 'test_clean', 'test_display', 'test_links', 'test_update', 't5test'}   # build outputs
BUILD_EXCLUDE_FILES = {'pub/index.html', 'pub/sheet.json'}                                             # build outputs
WORK_DIRS = ['html_clean', 'img_cache', 'texts', 'out', 'final', 'jobs', 'billstatus_cache', 'leginfo_raw',
             'fetch_cache', 'retry', 'org_ideas',
             'tmp_recall_rows/copies']    # FINALCHECK-v1 D4: make_copies reads these 28 extra cleaned copies (--clean-extra default)
WORK_FILE_EXCLUDE = re.compile(r'^coverage_pre_.*\.xlsx$')      # pre-write backups (the Mac Backups/ folder has them)
OPEN_GLOBS = ['work/tmp_*/handoff*.md', 'work/tmp_*/spec*.md', 'work/tmp_*/plan*.md', 'work/tmp_*/proposal*.md',
              'work/tmp_*/rootfix*.md', 'work/tmp_*/codespec*.md', 'work/tmp_*/scheduled_prompt*.md', 'work/tmp_*/*.patch',
              'work/tmp_agent-*/publish*.json', 'work/tmp_agent-v20-final/make_publish2.py']
SKIP_NAMES = {'__pycache__', 'node_modules', '.DS_Store'}

# the copies step of a full rebuild (build/final_build.md §2 + PHOTOS-v2 + RELCOPIES-v1); SRC = the published copies
MAKE_COPIES = ['code/make_copies.py', '{SRC}', 'work/coverage_current.xlsx', '{OUT}', '--clean', 'work/html_clean',
               '--nb', 'work/texts/nb', '--img-map', 'build/clean/img_map.json', '--errors', 'work/final/error_copies.csv',
               '--deletions', 'work/final/deletions.csv', '--sidmap', 'work/sid_map.json', '--img-cache', 'work/img_cache',
               '--pdf-restore', 'work/img_cache/pdf_restore', '--img-strict', '--releases', 'work/html_clean/press_releases']

DB_COLLECTIONS = [  # HANDOFF 0.5 (grep of collection('…') in code/tracker, build/tabs, build/review/index.html)
    ('tracker', 'runs', 'Update-button run log: proposed rows, releases_new, ids, sheet lines, review lists'),
    ('tracker', 'edits', 'queued sheet edits / removal requests (field reported)'),
    ('tracker', 'tones', 'team tone ratings/edits per story'),
    ('tracker', 'authors', 'author fills from saved pages'),
    ('tracker', 'translations', 'English headlines/texts done in the page'),
    ('tracker', 'pages', 'saved pages waiting for the sheet task (rp-/og- docs)'),
    ('tracker', 'reprints', 'reprint docs written by runs'),
    ('tracker', 'notes', 'team notes'),
    ('tracker', 'clips', 'clip store'),
    ('tracker', 'views', 'saved views'),
    ('review', 'items', 'review-queue item docs (14-regroup…, 17-newoutlet, 18-origins-3 …)'),
    ('review', 'decisions', "{choice, note, at} per item: Sammy's and Claude's answers"),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def log(*a):
    print(*a, flush=True)


# ---- listing / maps -----------------------------------------------------------------------------------------------
def parse_listing(path):
    t = open(path, encoding='utf-8').read()
    files = {}
    for m in re.finditer(r'^- "([^"]+)"\s+(\S+)\s+(\d+) bytes\s*$', t, re.M):
        files[m.group(1)] = {'ctype': m.group(2), 'bytes': int(m.group(3))}
    if not files:   # TSV fallback: path \t contentType \t bytes
        for line in t.splitlines():
            p = line.split('\t')
            if len(p) == 3 and p[2].isdigit():
                files[p[0]] = {'ctype': p[1], 'bytes': int(p[2])}
    ver = re.search(r'\(version ([0-9a-f-]+)\)', t)
    art = re.search(r'(https://claude\.ai/(?:code/)?artifact/[A-Za-z0-9-]+)', t)
    con = re.search(r'contract ([0-9.]+)', t)
    cap = re.search(r'<artifact-stored-declaration>\s*(\{.*?\})\s*</artifact-stored-declaration>', t, re.S)
    if not files:
        sys.exit(f'{path}: no files found (save the Artifact list scope "files" output verbatim)')
    return {'files': files, 'version': ver.group(1) if ver else '', 'artifact': art.group(1) if art else '',
            'contract': con.group(1) if con else '', 'capabilities': json.loads(cap.group(1)) if cap else None}


def src_of(v):
    if v is None:
        return None
    return v['from'] if isinstance(v, dict) else v


def read_map(path):
    """-> (sources {path: file or None(=removed)}, expected {path: sha})"""
    d = json.load(open(path, encoding='utf-8'))
    S, E = {}, {}
    steps = d.get('publishes') or [d]
    # v22: the publish-plan layout (batches[] + final_batch + page{file_path, sha256} + file_sha256), as rp-final wrote it
    if d.get('batches') and not d.get('publishes'):
        steps = list(d['batches']) + ([d['final_batch']] if isinstance(d.get('final_batch'), dict) else [])
        pg = d.get('page') if isinstance(d.get('page'), dict) else {}
        if pg.get('sha256'):
            E['index.html'] = pg['sha256']
        if pg.get('file_path') and not any(isinstance(x, dict) and x.get('file_path') for x in steps):
            S['index.html'] = pg['file_path']
        for p_ in (d.get('removed_null') or []):
            S[p_] = None
    for st in steps:
        for k, v in (st.get('files') or {}).items():
            S[k] = src_of(v)
        if st.get('file_path'):
            S['index.html'] = st['file_path']
            sh = st.get('page_sha256') or st.get('index_sha256')
            if sh:
                E['index.html'] = sh
    for k in ('sha256', 'file_sha256'):
        for p, sh in (d.get(k) or {}).items():
            E[p] = sh
    if d.get('index_sha256'):
        E['index.html'] = d['index_sha256']
    for p in (d.get('remove') or {}):
        S[p] = None
    return S, E


# ---- record -------------------------------------------------------------------------------------------------------
def cmd_record(a):
    lst = parse_listing(a.listing)
    old = json.load(open(LEDGER)) if os.path.exists(LEDGER) else {'files': {}}
    S, E = {}, {}
    for m in a.map or []:
        s, e = read_map(m)
        S.update(s); E.update(e)
    os.makedirs(STORE, exist_ok=True)
    ledger = {'artifact': lst['artifact'] or old.get('artifact', ''), 'version': lst['version'],
              'contract': lst['contract'], 'capabilities': lst['capabilities'] if lst['capabilities'] is not None else old.get('capabilities'),
              'recorded_at': now(), 'maps': [os.path.relpath(os.path.abspath(m), L) for m in a.map or []],
              'files': {}, 'warnings': []}
    need = []
    shacache = {}

    def fsha(p):
        if p not in shacache:
            shacache[p] = sha256(p)
        return shacache[p]

    for path, info in sorted(lst['files'].items()):
        want = info['bytes']
        exp = E.get(path)
        cands = []
        if a.fetched:
            cands.append((os.path.join(a.fetched, path), 'fetched', True))
        if S.get(path):
            cands.append((S[path], 'map', False))
        if exp:
            cands.append((os.path.join(STORE, exp), 'store', False))
        o = old['files'].get(path)
        if o and (not exp or o['sha256'] == exp) and path not in S:
            cands.append((os.path.join(STORE, o['sha256']), 'ledger', False))
        for r in a.root or []:
            cands.append((os.path.join(r, path), 'root:' + os.path.relpath(os.path.abspath(r), L), False))
        chosen = None
        size_ok = []
        for p, origin, authoritative in cands:
            if not os.path.isfile(p) or os.path.getsize(p) != want:
                continue
            h = fsha(p)
            if exp and h != exp and not authoritative:
                continue
            size_ok.append((p, origin, h))
            if chosen is None:
                chosen = (p, origin, h)
                if origin in ('fetched', 'store', 'ledger') or exp:
                    break
        if chosen is None:
            need.append(path)
            continue
        p, origin, h = chosen
        if exp and h != exp:
            ledger['warnings'].append(f'{path}: fetched sha {h[:12]} != map sha {exp[:12]} (fetched wins: it is the live file)')
        alts = {x[2] for x in size_ok if x[2] != h}
        if alts and not exp and origin.startswith('root'):
            ledger['warnings'].append(f'{path}: other same-size candidates with different sha {sorted(x[:12] for x in alts)}; '
                                      f'took {origin}. Verify with Artifact read if it matters.')
        dst = os.path.join(STORE, h)
        if not os.path.exists(dst):
            shutil.copyfile(p, dst + '.part'); os.replace(dst + '.part', dst)
        if 'verified' in (o or {}) and o.get('sha256') == h and origin == 'ledger':
            ver = o['verified']
        else:
            ver = 'live-read' if origin == 'fetched' else ('sha' if exp else 'size')
        ledger['files'][path] = {'sha256': h, 'bytes': want, 'ctype': info['ctype'], 'verified': ver,
                                 'origin': origin if origin in ('fetched', 'map', 'store', 'ledger') else origin}
    ledger['page_sha256'] = ledger['files'].get('index.html', {}).get('sha256', '')
    os.makedirs(HK, exist_ok=True)
    nf = os.path.join(HK, 'need_fetch.json')
    if need:
        json.dump({'artifact': ledger['artifact'], 'version': ledger['version'], 'paths': need,
                   'how': 'Artifact action "read" with url=<artifact> and paths=<these> (<=256 paths and <=64 MB a call; the result lists sha256s), '
                          'out_dir=' + os.path.join(L, 'work', 'handoff_fetch') + '; then re-run record with --fetched that dir'},
                  open(nf, 'w'), indent=1)
        log(f'UNRESOLVED {len(need)} of {len(lst["files"])} live files -> {nf}')
        for p in need[:30]:
            log('  ', p, lst['files'][p]['bytes'])
        sys.exit(2)
    if os.path.exists(nf):
        os.replace(nf, nf + '.done')
    json.dump(ledger, open(LEDGER, 'w'), indent=1)
    cnt = {}
    for v in ledger['files'].values():
        cnt[v['verified']] = cnt.get(v['verified'], 0) + 1
    log(f'ledger: version {ledger["version"]}, {len(ledger["files"])} files, '
        f'{sum(v["bytes"] for v in ledger["files"].values()):,} bytes, page {ledger["page_sha256"][:12]}; verified {cnt}')
    for w in ledger['warnings']:
        log('WARN', w)


# ---- build --------------------------------------------------------------------------------------------------------
def place(src, dst, link=True):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if link:
        try:
            os.link(src, dst); return
        except OSError:
            pass
    shutil.copy2(src, dst)


def walk(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP_NAMES)
        for f in sorted(fns):
            if f not in SKIP_NAMES and not f.endswith('.pyc'):
                yield os.path.join(dp, f)


def build_publish(ledger, pub):
    rows = []
    for path, v in sorted(ledger['files'].items()):
        blob = os.path.join(STORE, v['sha256'])
        if not os.path.isfile(blob) or os.path.getsize(blob) != v['bytes']:
            sys.exit(f'store blob missing/short for {path}: run record again')
        place(blob, os.path.join(pub, path))
        rows.append((path, v['bytes'], v['sha256'], v['ctype'], v['verified']))
    with open(os.path.join(pub, 'MANIFEST.tsv'), 'w') as f:
        f.write('path\tbytes\tsha256\tcontentType\tverified\n')
        for r in rows:
            f.write('\t'.join(map(str, r)) + '\n')
    json.dump(ledger['capabilities'], open(os.path.join(pub, 'capabilities.json'), 'w'), indent=1)
    # publish batches: <=60 MB (64 MB limit, margin) and <=250 files each, the page alone and last
    batches, cur, cb = [], {}, 0
    for path, b, *_ in sorted(rows, key=lambda r: (r[0].split('/')[0], r[0])):
        if path == 'index.html':
            continue
        if cur and (cb + b > 60 * MB or len(cur) >= 250):
            batches.append(cur); cur, cb = {}, 0
        # v22: pipeline files keep the live content type (.py = text/plain, which the extension alone does not give)
        # COLDSTART-v1: one shape for every entry, {"from", "contentType"} (was a bare string for non-pipeline files)
        ct = (ledger['files'][path].get('ctype') or ('text/plain' if path.endswith('.py') else '')
              or mimetypes.guess_type(path)[0] or 'application/octet-stream')
        cur[path] = {'from': 'publish/' + path, 'contentType': ct}; cb += b
    if cur:
        batches.append(cur)
    plan = []
    for i, fs in enumerate(batches, 1):
        plan.append({'step': i, 'file_path': 'republish/placeholder.html', 'files': fs, 'count': len(fs),
                     'bytes': sum(ledger['files'][p]['bytes'] for p in fs)})
    plan.append({'step': len(batches) + 1, 'file_path': 'publish/index.html', 'files': {}, 'count': 0,
                 'bytes': ledger['files']['index.html']['bytes'], 'note': 'the real page, LAST'})
    json.dump({'note': 'Paths are relative to the unzipped kit folder. Step 1 creates the artifact (no url) and declares '
                       'capabilities (publish/capabilities.json); later steps pass that url; the page goes last. Every entry of "files" is '
                       '{"from": kit path, "contentType": type}: pass it to the Artifact tool as is. Publish publish/articles/* exactly as '
                       'shipped (a rebuilt copy set differs).',
               'steps': plan}, open(os.path.join(pub, 'BATCHES.json'), 'w'), indent=1)
    return rows, plan


def build_source(src):
    n = 0
    for d in SRC_DOCS:
        if os.path.exists(os.path.join(L, d)):
            place(os.path.join(L, d), os.path.join(src, d), link=False); n += 1
    for t in SRC_TREES:
        for p in walk(os.path.join(L, t)):
            place(p, os.path.join(src, os.path.relpath(p, L)), link=False); n += 1
    broot = os.path.join(L, 'build')
    for p in walk(broot):
        rel = os.path.relpath(p, broot)
        if rel.split('/')[0] in BUILD_EXCLUDE_DIRS or rel in BUILD_EXCLUDE_FILES:
            continue
        place(p, os.path.join(src, 'build', rel), link=False); n += 1
    w = os.path.join(L, 'work')
    for f in sorted(os.listdir(w)):
        p = os.path.join(w, f)
        if os.path.isfile(p) and not WORK_FILE_EXCLUDE.match(f):
            place(p, os.path.join(src, 'work', f), link=False); n += 1
    for d in WORK_DIRS:
        for p in walk(os.path.join(w, d)):
            place(p, os.path.join(src, os.path.relpath(p, L)), link=False); n += 1
    opened = []
    for g in OPEN_GLOBS:
        for p in sorted(glob.glob(os.path.join(L, g))):
            rel = os.path.relpath(p, L)
            if rel not in opened:
                opened.append(rel)
                place(p, os.path.join(src, rel), link=False); n += 1
    # db export
    dbd = os.path.join(src, 'db_export')
    os.makedirs(dbd, exist_ok=True)
    counts = None
    if os.path.isdir(DB_EXPORT) and any(os.scandir(DB_EXPORT)):
        for p in walk(DB_EXPORT):
            place(p, os.path.join(dbd, os.path.relpath(p, DB_EXPORT)), link=False); n += 1
        r = subprocess.run([sys.executable, '-I', os.path.join(L, 'code', 'db_reseed.py'), DB_EXPORT,
                            os.path.join(dbd, '_batches')], capture_output=True, text=True)
        if r.returncode:
            sys.exit('db_reseed failed: ' + r.stderr)
        counts = json.load(open(os.path.join(dbd, '_batches', 'counts.json')))
    write_checklist(os.path.join(dbd, 'EXPORT_CHECKLIST.md'), counts)
    return n, opened, counts


def write_checklist(path, counts):
    lines = ['# Database export checklist (HANDOFF 0.5)', '',
             'Artifact databases are NOT in the published files. Before the old account closes, a Claude session on the OLD',
             'account exports every collection below with ArtifactData `list` (every page; `get` for single docs) and saves',
             f'each doc as `L/work/db_export/<artifact>/<collection>/<doc_id>.json` (artifact = `tracker` or `review`;',
             'a saved list page `[{doc_id|id, data}, ...]` per file also works). Then re-run `build/build.sh --kit`: the kit',
             'copies them to `source/db_export/`, `code/db_reseed.py` writes `source/db_export/_batches/<artifact>/batch_NNN.json`',
             '(<=50 writes each, doc ids unchanged), and KIT_README.md gets the counts.', '',
             'On the NEW account: after the first publish of the new tracker / review queue and BEFORE anyone presses Update,',
             'send each batch file, in order, as ArtifactData action `batch` to the new artifact url.', '',
             '| done | artifact | collection | holds | docs exported |', '|---|---|---|---|---|']
    for art, coll, holds in DB_COLLECTIONS:
        c = (counts or {}).get(art, {}).get(coll)
        lines.append(f'| {"x" if c is not None else " "} | {art} | `{coll}` | {holds} | {c if c is not None else "not exported"} |')
    lines += ['', 'Old artifacts: tracker https://claude.ai/code/artifact/27f923dc-2407-40a0-b8a9-ec3dfed87ad9 '
                  '(= claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv); review queue claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB.',
              'Per-viewer browser storage (localStorage jg-tones / jg-authors / jg2-notes, IndexedDB jg-archive) cannot move.']
    open(path, 'w').write('\n'.join(lines) + '\n')


def run(cmd, cwd, env=None, log_to=None):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if log_to:
        open(log_to, 'w').write(r.stdout + '\n--- stderr\n' + r.stderr)
    return r


def rebuild_test(src, pub, ledger, keep):
    T = tempfile.mkdtemp(prefix='kit_rebuild_', dir=os.path.dirname(L))
    res = {'dir': T, 'at': now()}
    try:
        shutil.copytree(src, os.path.join(T, 'lib'), symlinks=True)
        R = os.path.join(T, 'lib')
        env = {k: v for k, v in os.environ.items() if k not in ('XLSX', 'BASE', 'OUT', 'PIPE_BASE')}
        out = os.path.join(T, 'out')
        env['OUT'] = out
        r = run(['bash', os.path.join(R, 'build', 'build.sh')], cwd=T, env=env, log_to=os.path.join(T, 'build.log'))
        res['build_rc'] = r.returncode
        page = ledger['page_sha256']
        lib_p, pipe_p = os.path.join(out, 'lib', 'index.html'), os.path.join(out, 'pipe_index.html')
        res['lib_sha'] = sha256(lib_p) if os.path.exists(lib_p) else None
        res['pipe_sha'] = sha256(pipe_p) if os.path.exists(pipe_p) else None
        res['page_sha'] = page
        res['page_ok'] = res['lib_sha'] == page and res['pipe_sha'] == page
        m = re.search(r'blocks: (\d+), differing lib vs pipeline: (\d+)', r.stdout)
        res['blocks'] = m.group(0) if m else r.stdout[-300:]
        if r.returncode:
            res['build_err'] = r.stderr[-2000:]
        # viewer copies
        cout = os.path.join(T, 'copies')
        cmd = [sys.executable, '-I'] + [x.replace('{SRC}', pub).replace('{OUT}', cout) for x in MAKE_COPIES] + \
              ['--report', os.path.join(T, 'copies_report.json')]
        r = run(cmd, cwd=R, log_to=os.path.join(T, 'copies.log'))
        res['copies_rc'] = r.returncode
        if r.returncode:
            res['copies_err'] = r.stderr[-2000:]
        # STORAGE-v1: the live set is the REPACKED set. make_copies numbers shards 0.. and 100+; repack_img.py (run after it,
        # as HANDOFF 4.4a says) rewrites articles/ + img/0-N. Compare against that output (kit-regen 2026-10-30).
        if r.returncode == 0 and os.path.isfile(os.path.join(R, 'code', 'repack_img.py')):
            rp = os.path.join(T, 'copies_repacked')
            # make_copies emits only the images it added (100+); the carried ones stay in the published shards: merge both
            for f in os.listdir(os.path.join(pub, 'img')):
                d_ = os.path.join(cout, 'img', f)
                if not os.path.exists(d_):
                    shutil.copyfile(os.path.join(pub, 'img', f), d_)
            rr = run([sys.executable, '-I', 'code/repack_img.py', '--src', cout, '--out', rp], cwd=R,
                     log_to=os.path.join(T, 'repack.log'))
            res['repack_rc'] = rr.returncode
            if rr.returncode == 0:
                for sub in ('articles', 'img'):
                    shutil.rmtree(os.path.join(cout, sub), ignore_errors=True)
                    shutil.copytree(os.path.join(rp, sub), os.path.join(cout, sub))
            else:
                r = rr
        same, diff, extra = 0, [], []
        produced = set()
        for p in walk(cout):
            rel = os.path.relpath(p, cout)
            if rel == 'report.json':
                continue
            produced.add(rel)
            v = ledger['files'].get(rel)
            if not v:
                extra.append(rel)
            elif sha256(p) == v['sha256']:
                same += 1
            else:
                diff.append(rel)
        live_gen = [p for p in ledger['files'] if p.startswith('articles/') or re.match(r'img/1\d\d\.json$', p)]
        res['copies'] = {'same': same, 'differ': diff, 'not_live': extra,
                         'live_not_produced': sorted(set(live_gen) - produced)}
        res['copies_ok'] = not diff and not extra and not res['copies']['live_not_produced'] and r.returncode == 0
        # pipeline + data
        pp = os.path.join(R, 'build', 'pub', 'pipeline')
        pdiff, pmiss = [], []
        for path, v in ledger['files'].items():
            if not path.startswith('pipeline/'):
                continue
            f = os.path.join(pp, path[len('pipeline/'):])
            if not os.path.exists(f):
                pmiss.append(path)
            elif sha256(f) != v['sha256']:
                pdiff.append(path)
        res['pipeline'] = {'differ_from_live': sorted(pdiff), 'missing': sorted(pmiss)}
        rt = os.path.join(pp, 'release_texts.json')
        if 'data/release_texts.json' in ledger['files']:
            res['data_release_texts_ok'] = os.path.exists(rt) and sha256(rt) == ledger['files']['data/release_texts.json']['sha256']
        if 'data/sheet.json' in ledger['files']:
            try:
                sj = json.load(open(os.path.join(pub, 'data', 'sheet.json')))
                b = base64.b64decode(sj['b64'])
                res['data_sheet_xlsx_sha'] = hashlib.sha256(b).hexdigest()
                res['data_sheet_eq_coverage_current'] = res['data_sheet_xlsx_sha'] == sha256(os.path.join(R, 'work', 'coverage_current.xlsx'))
            except Exception as e:
                res['data_sheet_err'] = str(e)
        r = run([sys.executable, os.path.join(R, 'code', 'apply_all_patches.py'), '--check'], cwd=R,
                log_to=os.path.join(T, 'apply_check.log'))
        res['apply_all_check'] = 'OK' if r.returncode == 0 and 'CHECK OK' in r.stdout else f'rc={r.returncode}: ' + (r.stdout + r.stderr)[-600:]
    finally:
        if not keep:
            shutil.rmtree(T, ignore_errors=True)
    return res


def zip_parts(kit, part_bytes):
    groups = [('docs-code', lambda rel: not rel.startswith('source/work/') and not rel.startswith('publish/')),
              ('data', lambda rel: rel.startswith('source/work/')),
              ('publish', lambda rel: rel.startswith('publish/'))]
    allfiles = []
    for top in ('START_HERE.md', 'KIT_README.md', 'REBUILD_TEST.json', 'republish', 'source', 'publish'):
        p = os.path.join(kit, top)
        if os.path.isfile(p):
            allfiles.append(p)
        elif os.path.isdir(p):
            allfiles += list(walk(p))
    zdir = os.path.join(kit, 'parts')
    if os.path.isdir(zdir):
        shutil.rmtree(zdir)
    os.makedirs(zdir)
    parts = []
    for gi, (gname, pred) in enumerate(groups, 1):
        files = [p for p in allfiles if pred(os.path.relpath(p, kit))]
        n, zf, cur, members = 0, None, 0, []

        def close():
            if zf:
                zf.close()
                parts.append({'name': os.path.basename(zf.filename), 'group': gname, 'files': len(members),
                              'first': members[0], 'last': members[-1]})
        for p in files:
            rel = os.path.relpath(p, kit)
            data = open(p, 'rb').read()
            c = zlib.compressobj(6, zlib.DEFLATED, -15)
            clen = len(c.compress(data) + c.flush())
            store = clen > len(data) * 0.97
            est = (len(data) if store else clen) + 200 + 2 * len(rel.encode())
            if zf is None or (cur + est > part_bytes and members):
                close()
                n += 1
                zf = zipfile.ZipFile(os.path.join(zdir, f'kit-{gi}-{gname}-{n:02d}.zip'), 'w')
                cur, members = 0, []
            zi = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
            zi.external_attr = (os.stat(p).st_mode & 0xFFFF) << 16
            zi.compress_type = zipfile.ZIP_STORED if store else zipfile.ZIP_DEFLATED
            zf.writestr(zi, data, compresslevel=None if store else 6)
            cur += est
            members.append(rel)
        close()
    for pt in parts:
        p = os.path.join(zdir, pt['name'])
        pt['bytes'] = os.path.getsize(p); pt['sha256'] = sha256(p)
    with open(os.path.join(zdir, 'SHA256SUMS.txt'), 'w') as f:
        for pt in parts:
            f.write(f'{pt["sha256"]}  {pt["name"]}\n')
    return parts


def write_readme(kit, ledger, rows, plan, res, opened, counts, parts, nsrc, src_bytes):
    pub_bytes = sum(r[1] for r in rows)
    ver = {}
    for r in rows:
        ver[r[4]] = ver.get(r[4], 0) + 1
    L_ = []
    a = L_.append
    a('# AJG Press Coverage Tracker: handoff kit')
    a('')
    a(f'Generated {now()} by code/make_handoff_kit.py from the old account\'s library (L). Live tracker: '
      f'{ledger["artifact"]}, version **{ledger["version"]}**, page sha256 `{ledger["page_sha256"]}`, '
      f'{len(rows)} files, {pub_bytes:,} bytes. **Read START_HERE.md (kit root, one page) first**, then HANDOFF.md section 0.3 (in source/); '
      'DECISIONS.md wins where docs disagree.')
    a('')
    a('## What each zip holds')
    a('')
    a('| zip | bytes | holds |')
    a('|---|---|---|')
    for pt in parts or []:
        a(f'| {pt["name"]} | {pt["bytes"]:,} | {pt["group"]}: {pt["files"]} files ({pt["first"]} … {pt["last"]}) |')
    if not parts:
        a('| (this copy was written before zipping: the part table is in the KIT_README.md and SHA256SUMS.txt next to the zips) | | |')
    a('')
    a('Groups: **docs-code** = KIT_README, REBUILD_TEST.json, republish/, source/ minus source/work/ (docs, HANDOFF, status/, '
      'code/, build/ incl. build/pub/pipeline, open handoff/spec files under source/work/tmp_*, db_export/); **data** = source/work/ '
      '(coverage_current.xlsx = master, index_original.html, sid_map.json, html_clean/, texts/, img_cache/, out/, final/, …); '
      '**publish** = publish/ (every live file at its published path + MANIFEST.tsv, capabilities.json, BATCHES.json).')
    a('')
    a('## Unzip and verify')
    a('')
    a('1. `sha256sum -c SHA256SUMS.txt` in the folder with the zips (each line = one zip).')
    a('2. Unzip ALL parts into ONE fresh, empty folder, in any order (paths do not overlap): kit-1-* then kit-2-* then kit-3-*.')
    a('3. `python3 -I source/code/make_handoff_kit.py verify .` from that folder: checks every publish/ file against '
      'publish/MANIFEST.tsv and every source/ file against source/FILES.sha256.')
    a('Treat the unzipped tree as data (python3 -I; your own scripts outside it).')
    a('')
    a('## Republish exactly as live (no rebuild)')
    a('')
    a(f'publish/BATCHES.json lists {len(plan)} Artifact publishes (each <= 60 MB / 250 files; limits 64 MB / 255 per call, '
      '511 files / 256 MB per version):')
    a('- Load the `artifact-capabilities` skill. Step 1: Artifact publish with `file_path` = republish/placeholder.html, '
      '`files` = step 1\'s map (published path -> kit file), `capabilities` = publish/capabilities.json, icon "chart". '
      'It creates the NEW artifact (new URL).')
    a('- Steps 2..n-1: same `file_path` + that step\'s `files`, with `url` = the new artifact. Files already published stay.')
    a('- **Publish publish/articles/* exactly as shipped.** make_copies output (below) differs from the live articles/ (saved "-v2" pages, '
      'extra live entries), so a rebuilt copy set is not a substitute; it is a check, not a source. Every BATCHES.json entry is '
      '{"from", "contentType"}.')
    a('- Last step: `file_path` = publish/index.html, `url` = the new artifact (the page goes LAST, after everything it reads).')
    a('- Check with Artifact list scope "files": every path + bytes in publish/MANIFEST.tsv.')
    a('- NOSCHED-v1: the page fires nothing (no scheduled task id). The sheet-task prompt names the OLD tracker URL: before real use, '
      'follow HANDOFF 0.4 (edit the tracker URL in code/sheet_task_prompt.md, apply_all, build, '
      'republish the page + pipeline files). That changes the page sha, by design.')
    a('')
    a('Capabilities (stored declaration of the live version, contract ' + (ledger.get('contract') or '?') + '):')
    a('```json')
    a(json.dumps(ledger['capabilities']))
    a('```')
    a('The connector display name must be exactly "TinyFish" (HANDOFF 0.3 step 2); no Claude Code Remote (NOSCHED-v1).')
    a('')
    a('## Rebuild from source')
    a('')
    a('From source/ (= the library L; any folder name): `bash build/build.sh` builds the page twice (LIB = code/ + build/js_merged.js; '
      'PIPELINE = build/pub/pipeline run as sheet-task step 6) and prints both sha256s + the block comparison. '
      'Copies step (make_copies; produces articles/ + img/1NN.json for comparison only, NOT for publishing; command as the rebuild test runs it, '
      'paths relative to source/):')
    a('```')
    a('python3 -I ' + ' '.join(MAKE_COPIES).replace('{SRC}', '../publish').replace('{OUT}', 'OUT_DIR') + ' --report OUT_DIR/report.json')
    a('```')
    a('The shareable viewer copy ("Viewer copies" in older kits) is a different thing: `python3 -I code/make_viewer.py <built index.html> <out dir>` '
      '(HANDOFF 4.4a: arguments and the server-side copy step for a new account).')
    a('Run times (measured 2026-10-30): build/build.sh about 25 s; build/tests/run_all.sh about 5 min 15 s (sheet_task 101 s, auto 120 s, '
      'coldstart_f1 36 s, the rest under 10 s each); repack_img.py about 2 s. The kit rebuild test and zipping were not timed.')
    a('After a code change: `python3 code/apply_all_patches.py` first (README §2). Regenerate this kit after every publish: '
      '`build/build.sh --kit` (README "Handoff kit").')
    a('Some one-off tools under code/fetch*, code/billstatus and build/insights/_shell still carry the old absolute L path; '
      'they are not part of the build.')
    a('')
    a('## Rebuild test of this kit (clean folder holding only source/)')
    a('')
    if res:
        a(f'- build.sh: LIB `{res.get("lib_sha")}`, PIPELINE `{res.get("pipe_sha")}` vs live `{res.get("page_sha")}` -> '
          f'**{"IDENTICAL" if res.get("page_ok") else "DIFFERENT"}**; {res.get("blocks")}')
        c = res.get('copies', {})
        a(f'- make_copies: {c.get("same")} files identical to live; differ {c.get("differ")}; not live {c.get("not_live")}; '
          f'live but not produced {c.get("live_not_produced")} -> **{"IDENTICAL" if res.get("copies_ok") else "CHECK"}**')
        a(f'- build/pub/pipeline vs live pipeline/: differ {res.get("pipeline", {}).get("differ_from_live")}; '
          f'missing {res.get("pipeline", {}).get("missing")} (a difference = a source change not yet published)')
        a(f'- data/release_texts.json = pipeline/release_texts.json: {res.get("data_release_texts_ok")}; '
          f'data/sheet.json decodes to source/work/coverage_current.xlsx: {res.get("data_sheet_eq_coverage_current")}')
        a(f'- apply_all --check: {res.get("apply_all_check")}')
    else:
        a('- not run in this generation (--no-test).')
    a('')
    a('## Live file provenance')
    a('')
    a(f'MANIFEST.tsv column `verified`: {ver}. `sha` = sha256 equals the publish map that shipped it; `live-read` = read back from '
      'the live artifact; `size` = files kept from versions before the ledger (img/0..15, pdf/*) matched by path + exact byte size.')
    for w in ledger.get('warnings', []):
        a(f'- warning: {w}')
    a('')
    a('## Database carry-over')
    a('')
    if counts:
        a('Exported doc counts (source/db_export/, batches in source/db_export/_batches/):')
        for art, cs in counts.items():
            a(f'- {art}: ' + ', '.join(f'{k} {v}' for k, v in cs.items()))
    else:
        a('NOT EXPORTED YET. source/db_export/EXPORT_CHECKLIST.md lists the 12 collections (tracker: runs, edits, tones, authors, '
          'translations, pages, reprints, notes, clips, views; review queue: items, decisions) and the export/re-seed steps '
          '(code/db_reseed.py makes <=50-write ArtifactData batch payloads, same doc ids).')
    a('')
    a('## Open handoff/spec files carried in source/ (still open)')
    a('')
    for o in opened:
        a(f'- {o}')
    a('')
    a(f'source/: {nsrc} files, {src_bytes:,} bytes. Left out: archive/ (3 GB of moved files), work/tmp_* scratch (except the '
      'files above), work/build_last, work/clip, work/nb_split, work/library_new, work/tests_out, work/artifact_files, the '
      'pre-write workbook backups work/coverage_pre_*.xlsx (the Mac Backups/ folder has them), final_pass/, build outputs '
      f'({", ".join(sorted(BUILD_EXCLUDE_DIRS))}, pub/index.html, pub/sheet.json).')
    open(os.path.join(kit, 'KIT_README.md'), 'w').write('\n'.join(L_) + '\n')


FACTS_BEGIN, FACTS_END = '<!-- FACTS:BEGIN (generated by code/make_handoff_kit.py facts --write; do not edit by hand) -->', '<!-- FACTS:END -->'


def _count_rows(ws):
    return sum(1 for r in ws.iter_rows(min_row=2, max_col=1, values_only=True) if r[0] not in (None, ''))


def facts_block(ledger=None):
    """COLDSTART-v1: every number that used to be typed into HANDOFF (rows, files, IDs, suites) is computed here."""
    import openpyxl
    if ledger is None and os.path.exists(LEDGER):
        ledger = json.load(open(LEDGER))
    ledger = ledger or {'files': {}}
    xl = os.path.join(L, 'work', 'coverage_current.xlsx')
    out = []
    a = out.append
    a(FACTS_BEGIN)
    a(f'Generated {now()}. Re-run `python3 -I code/make_handoff_kit.py facts --write` (or `build`) instead of editing these numbers.')
    a('')
    fb = sum(v['bytes'] for v in ledger['files'].values())
    if ledger['files']:
        a(f'- Live tracker version {ledger.get("version")} (runtime contract {ledger.get("contract") or "?"}), page sha256 `{ledger.get("page_sha256")}`; '
          f'{len(ledger["files"])} published files, {fb / MB:.1f} MB of the 256 MB per-version cap ({(256 * MB - fb) / MB:.1f} MB free; the 511-file cap leaves {511 - len(ledger["files"])} files). '
          f'Recorded {ledger.get("recorded_at", "?")}; anything published since is not in this kit.')
    if os.path.exists(xl):
        wb = openpyxl.load_workbook(xl, read_only=True)
        n = {t: _count_rows(wb[t]) for t in wb.sheetnames}
        aid, sid, pid = 0, 0, 0
        for t in ('Coverage', 'Removed', 'Unlinked print pages'):
            if t not in wb.sheetnames:
                continue
            it = wb[t].iter_rows(values_only=True)
            hdr = list(next(it))
            ci = [hdr.index(c) for c in ('Article ID', 'Print Article ID', 'Old Article ID', 'Old Print Article ID') if c in hdr]
            si = hdr.index('Story ID') if 'Story ID' in hdr else None
            for r in it:
                for i in ci:
                    v = str(r[i] or '').strip()
                    if v.isdigit():
                        aid = max(aid, int(v))
                if si is not None:
                    m = re.fullmatch(r's(\d{5})', str(r[si] or '').strip())
                    if m:
                        sid = max(sid, int(m.group(1)))
        if 'Press releases' in wb.sheetnames:
            for r in wb['Press releases'].iter_rows(min_row=2, max_col=1, values_only=True):
                m = re.fullmatch(r'pr(\d{5})', str(r[0] or '').strip())
                if m:
                    pid = max(pid, int(m.group(1)))
        a(f'- Master workbook copy work/coverage_current.xlsx: sha256 `{sha256(xl)}` (must equal the Mac master; compare before any write). '
          'Rows: ' + ', '.join(f'{t} {n[t]:,}' for t in wb.sheetnames) + '.')
        a(f'- Highest IDs in the workbook: Article ID {aid:05d}, Story ID s{sid:05d}, Release ID pr{pid:05d}. Next free is one above, '
          'but never assign by hand: sheet_task.py assigns IDs (it also skips reserved blocks and every ID in Removed / Print Article ID).')
    wr = os.path.join(L, 'work', 'WORKBOOK_WRITER.txt')
    if os.path.exists(wr):
        a(f'- Workbook writer token (work/WORKBOOK_WRITER.txt): "{open(wr).read().strip()}".')
    ra = os.path.join(L, 'build', 'tests', 'run_all.sh')
    if os.path.exists(ra):
        txt = open(ra).read()
        ns = len(re.findall(r'(?m)^\s*(?:if [^;]*; then )?r [a-z_0-9]+ ', txt))
        a(f'- Unit suites: {ns} in build/tests/run_all.sh (3 of them skip with a notice when their inputs are not in the kit). '
          'The TABS harness is separate.')
    a(FACTS_END)
    return '\n'.join(out)


def render_start_here(ledger=None):
    p = os.path.join(L, 'START_HERE.md')
    if not os.path.exists(p):
        return None
    t = open(p, encoding='utf-8').read()
    blk = facts_block(ledger)
    if FACTS_BEGIN in t and FACTS_END in t:
        i, j = t.index(FACTS_BEGIN), t.index(FACTS_END) + len(FACTS_END)
        return t[:i] + blk + t[j:]
    return t.rstrip('\n') + '\n\n## Facts (generated)\n\n' + blk + '\n'


def cmd_facts(a):
    if a.write:
        t = render_start_here()
        if t is None:
            sys.exit('no START_HERE.md')
        open(os.path.join(L, 'START_HERE.md'), 'w', encoding='utf-8').write(t)
        log('START_HERE.md facts block refreshed')
    else:
        print(facts_block())


PLACEHOLDER = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               '<title>AJG Press Coverage Tracker</title><style>:root{--bg:#fff;--fg:#222}@media (prefers-color-scheme: dark)'
               '{:root:not([data-theme="light"]){--bg:#141414;--fg:#ddd}}:root[data-theme="dark"]{--bg:#141414;--fg:#ddd}'
               'body{background:var(--bg);color:var(--fg);font:16px system-ui;margin:0;padding:24px 16px}</style></head>'
               '<body><p>Uploading the tracker files. The page arrives with the last publish step.</p></body></html>\n')


def cmd_build(a):
    if not os.path.exists(LEDGER):
        sys.exit('no ledger: run `record` first')
    ledger = json.load(open(LEDGER))
    if os.path.isdir(KIT):
        for d in ('publish', 'source', 'republish', 'parts'):
            shutil.rmtree(os.path.join(KIT, d), ignore_errors=True)
    os.makedirs(KIT, exist_ok=True)
    pub, src = os.path.join(KIT, 'publish'), os.path.join(KIT, 'source')
    rows, plan = build_publish(ledger, pub)
    os.makedirs(os.path.join(KIT, 'republish'), exist_ok=True)
    open(os.path.join(KIT, 'republish', 'placeholder.html'), 'w').write(PLACEHOLDER)
    log(f'publish/: {len(rows)} files, {sum(r[1] for r in rows):,} bytes, {len(plan)} publish steps')
    nsrc, opened, counts = build_source(src)
    sh = render_start_here(ledger)       # START_HERE.md at the kit root and in source/, facts block refreshed
    if sh is not None:
        for d in (KIT, src):
            open(os.path.join(d, 'START_HERE.md'), 'w', encoding='utf-8').write(sh)
        nsrc += 1
    src_bytes = 0
    with open(os.path.join(src, 'FILES.sha256'), 'w') as f:
        for p in walk(src):
            rel = os.path.relpath(p, src)
            if rel == 'FILES.sha256':
                continue
            src_bytes += os.path.getsize(p)
            f.write(f'{sha256(p)}  {rel}\n')
    log(f'source/: {nsrc} files, {src_bytes:,} bytes; open files {len(opened)}; db export {"yes" if counts else "not yet"}')
    res = None
    if not a.no_test:
        res = rebuild_test(src, pub, ledger, a.keep_test)
        json.dump(res, open(os.path.join(KIT, 'REBUILD_TEST.json'), 'w'), indent=1)
        log('rebuild test:', json.dumps({k: res.get(k) for k in ('page_ok', 'lib_sha', 'pipe_sha', 'blocks', 'copies_ok',
                                                               'pipeline', 'apply_all_check')}))
    write_readme(KIT, ledger, rows, plan, res, opened, counts, None, nsrc, src_bytes)
    parts = None
    if not a.no_zip:
        parts = zip_parts(KIT, int(a.part_mb * MB))
        write_readme(KIT, ledger, rows, plan, res, opened, counts, parts, nsrc, src_bytes)
        # the README inside kit-1 predates the part table; the copy next to the zips is the full one
        shutil.copy2(os.path.join(KIT, 'KIT_README.md'), os.path.join(KIT, 'parts', 'KIT_README.md'))
        for pt in parts:
            log(f'{pt["name"]}\t{pt["bytes"]:,}\t{pt["sha256"]}')
    if res and not (res.get('page_ok') and res.get('copies_ok')):
        log('REBUILD TEST FAILED: see handoff_kit/REBUILD_TEST.json')
        sys.exit(3)


def cmd_verify(a):
    k = a.kit
    bad = 0
    man = os.path.join(k, 'publish', 'MANIFEST.tsv')
    for line in open(man).read().splitlines()[1:]:
        path, b, sh = line.split('\t')[:3]
        p = os.path.join(k, 'publish', path)
        if not os.path.isfile(p) or os.path.getsize(p) != int(b) or sha256(p) != sh:
            log('BAD publish', path); bad += 1
    n = 0
    for line in open(os.path.join(k, 'source', 'FILES.sha256')):
        sh, rel = line.rstrip('\n').split('  ', 1)
        p = os.path.join(k, 'source', rel); n += 1
        if not os.path.isfile(p) or sha256(p) != sh:
            log('BAD source', rel); bad += 1
    log(f'verify: {bad} bad (publish manifest + {n} source files)')
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sp = ap.add_subparsers(dest='cmd')
    r = sp.add_parser('record'); r.add_argument('--listing', required=True); r.add_argument('--map', action='append')
    r.add_argument('--root', action='append'); r.add_argument('--fetched')
    b = sp.add_parser('build'); b.add_argument('--no-test', action='store_true'); b.add_argument('--no-zip', action='store_true')
    b.add_argument('--part-mb', type=float, default=90); b.add_argument('--keep-test', action='store_true')
    v = sp.add_parser('verify'); v.add_argument('kit', nargs='?', default='.')
    f = sp.add_parser('facts'); f.add_argument('--write', action='store_true')
    a = ap.parse_args(sys.argv[1:] or ['build'])
    {'record': cmd_record, 'build': cmd_build, 'verify': cmd_verify, 'facts': cmd_facts}[a.cmd or 'build'](a)


if __name__ == '__main__':
    main()
