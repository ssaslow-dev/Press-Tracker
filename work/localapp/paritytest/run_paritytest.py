"""PARITYTEST-v1: the live tracker's own files against the PC tracker, same workbook, same clicks; outcomes compared.

    python3 -I work/localapp/paritytest/run_paritytest.py [--build "…/AJG Tracker"] [--live-site DIR] [--out DIR] [--only a,b]

Reference = the live tracker's published files (fetched read-only into --live-site, built from the same workbook as the PC build), served by a plain static
server on 127.0.0.1 with an in-memory stand-in for the live tracker's database (parity.js MOCK); the live artifact and its database are never touched.
The reference page gets exactly what the PC build also applies to the page, and nothing else: the page patches 15, 16, 17 and 27 and the wording lists 18 and 21
(assemble_app.patch_index_tidy) and the rule that hides the Update, Refresh, tone, author and translation buttons. A guard compares the reference page before and
after those patches: the changed lines must be exactly the reviewed set (ref_patch_diff.json); any other change fails the run until it has been reviewed (TIDY-v1).
Candidate = the PC build's launcher on a hard-linked working copy (the build is never written). Passes (1440x900 only):
  light, keeper copy: every interaction (lookcheck/parity.js and extra.js)
  dark, keeper copy:  the page-wide ones (every tab, story sheet, tab tables, Manage)
  light, reader copy: every tab, Manage, search, story sheet (MULTIPC-v2)
Each interaction gets a fresh working copy with one save in its ledger (so "Last updated" shows) and one print original in the library (so "View original" shows).
No difference is allowed except the PC's own additions, which extra.js asserts on the PC and strips before comparing (Tracker files button, Last updated, View original);
allowed.json is empty. Exit code 0 when no interaction differs. Results: OUT/parity/*.json and the *_summary.json files.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LC = REPO / 'work' / 'localapp' / 'lookcheck'
SCRATCH = Path(os.environ.get('AJG_SCRATCH') or os.path.join(tempfile.gettempdir(), 'ajg_scratch'))
sys.path.insert(0, str(LC))
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'app' / 'tests'))
import run_lookcheck as RL  # noqa: E402  (free_port, wait_http)

LEDGER_AT = '2026-11-03T07:30:00+00:00'          # 2026-11-02 in Los Angeles
LAST_UPDATED = 'Last updated Nov. 2, 2026'
PO_AID, PO_FILE = '10651', '_original_pdf/2026/10651_p15.pdf'     # row 10651 (s04930, an Original) gets a print original
PHOTO_ID = 's02546'
PHOTO_NTH = 2          # the third photo of that copy (the first is the lead photo, which the viewer treats specially)
PHOTO_URL = 'https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png'
LIGHT_ALL = None
DARK_TESTS = ['every_tab', 'story_sheet', 'tab_tables', 'manage_panel', 'saved_copy']
READER_TESTS = ['every_tab', 'manage_panel', 'clips_search', 'story_sheet']


def ref_patch_guard(live_index: Path, patched_index: Path) -> list:
    """the lines the patches changed, and whether they are the reviewed set (ref_patch_diff.json: sha256 of the changed lines)"""
    a = live_index.read_text(encoding='utf-8').split('\n')
    b = patched_index.read_text(encoding='utf-8').split('\n')
    chg = [l for l in difflib.unified_diff(a, b, lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
    sha = hashlib.sha256('\n'.join(chg).encode('utf-8')).hexdigest()
    want = json.loads((HERE / 'ref_patch_diff.json').read_text(encoding='utf-8'))
    print(f'reference patch guard: {len(chg)} changed lines, sha256 {sha[:12]} (reviewed: {want["sha256"][:12]}, {want["lines"]} lines)', flush=True)
    if sha != want['sha256']:
        (HERE / 'ref_patch_diff.NEW.txt').write_text('\n'.join(chg), encoding='utf-8')
        return [f'the page patches changed the reference page differently from the reviewed set (now {len(chg)} lines, sha256 {sha}). The lines are in ref_patch_diff.NEW.txt. '
                f'Check each against TIDY-v1 / NOTE-v1 / VIEWORIG-v1; if they are all recorded, put the new sha256 and line count in ref_patch_diff.json.']
    return []


def prepare_pc(T, root: Path, srv, photo: bool):
    """one save in the ledger, one print original in the library (page rebuilt so the row carries it), optionally one linked photo in a saved copy"""
    data = root / 'data'
    led = data / 'state' / 'ledger.jsonl'
    t = led.read_text(encoding='utf-8')
    led.unlink()
    led.write_text(t + json.dumps({'at': LEDGER_AT, 'verb': 'drop_unverified', 'after_sha': 'x'}) + '\n', encoding='utf-8')
    f = data / 'library' / PO_FILE
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(b'%PDF-1.4\n%parity test page\n')
    r = srv.job('rebuild', timeout=900)
    assert r.get('ok'), 'the page could not be rebuilt for the test copy: ' + str(r)[:200]
    if photo:
        alter_shard(data / 'copies' / 'articles' / '2025.json')


def alter_shard(path: Path):
    d = json.loads(path.read_text(encoding='utf-8'))
    h = d[PHOTO_ID]
    spots = [m.start() for m in re.finditer(r'src="(?:jgimg|data):', h)]      # the live copies keep photos as jgimg: references (the page resolves them from img/)
    i = spots[PHOTO_NTH]
    j = h.index('"', i + 5)
    d[PHOTO_ID] = h[:i] + f'src="{PHOTO_URL}' + h[j:]
    tmp = path.with_name(path.name + '.new')
    tmp.write_text(json.dumps(d), encoding='utf-8')
    path.unlink()
    tmp.rename(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, default=SCRATCH / 'paritytest_out')
    ap.add_argument('--build', type=Path, default=SCRATCH / 'app_build_pt' / 'linux' / 'AJG Tracker')
    ap.add_argument('--live-site', type=Path, default=SCRATCH / 'live_v65')
    ap.add_argument('--vp', default='1440x900')
    ap.add_argument('--only', default='')
    ap.add_argument('--passes', default='light,dark,reader')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    os.environ['AJG_TEST_BUILD'] = str(a.build)
    import support as T  # noqa: E402
    refx = a.out / '_refx'
    shutil.rmtree(refx, ignore_errors=True)
    refx.mkdir(parents=True)
    for f in a.live_site.iterdir():
        if f.name not in ('index.html', 'pipeline', 'workbook.xlsx'):
            os.symlink(f, refx / f.name)
    import importlib.util
    spec = importlib.util.spec_from_file_location('assemble_app', REPO / 'work' / 'localapp' / 'app' / 'assemble_app.py')
    A = importlib.util.module_from_spec(spec)
    sys.modules['assemble_app'] = A
    spec.loader.exec_module(A)
    shutil.copy2(a.live_site / 'index.html', refx / 'index.html')
    A.patch_index_tidy(refx / 'index.html')
    problems = ref_patch_guard(a.live_site / 'index.html', refx / 'index.html')
    if problems:
        print('PARITYTEST: FAIL\n' + '\n'.join(problems))
        return 1
    port = RL.free_port()
    live = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=refx, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ref = f'http://127.0.0.1:{port}/index.html'
    env = dict(os.environ, PLAYWRIGHT_MODULE='/opt/node-tools/node_modules/playwright')
    extra = ['--extra', str(HERE / 'extra.js'), '--allow', str(HERE / 'allowed.json')]
    names_all = subprocess.run(['node', str(LC / 'parity.js'), '--list', '--out', str(a.out)] + extra, env=env, capture_output=True, text=True).stdout.strip().split(',')
    assert names_all and all(names_all), 'could not list the interactions'
    only = a.only.split(',') if a.only else None
    plan = []
    for ps in a.passes.split(','):
        if ps == 'light':
            plan.append(('light', 'keeper', only or names_all))
        elif ps == 'dark':
            plan.append(('dark', 'keeper', [n for n in (only or DARK_TESTS) if n in DARK_TESTS or only]))
        elif ps == 'reader':
            plan.append(('light', 'reader', [n for n in (only or READER_TESTS) if n in READER_TESTS or only]))
    (a.out / 'parity').mkdir(parents=True, exist_ok=True)
    for f in (a.out / 'parity').glob(f'{a.vp}*_summary.json'):
        f.unlink()
    bad = []
    try:
        assert RL.wait_http(ref), 'reference server did not start'
        for scheme, role, names in plan:
            for name in names:
                work = a.out / '_pc'
                shutil.rmtree(work, ignore_errors=True)
                root = T.make_work(work, 'w', role)
                srv = T.Server(root).start()
                photo = name == 'linked_photo'
                try:
                    left = [str(f.relative_to(work)) for f in (root / 'data' / 'db').rglob('*') if f.is_file()]
                    if left:
                        print('WARNING: the PC data copy was not empty before', name, left[:5], flush=True)
                    prepare_pc(T, root, srv, photo)
                    if photo:
                        import urllib.request
                        got = urllib.request.urlopen(srv.base + '/articles/2025.json').read().decode('utf-8', 'replace')
                        page = urllib.request.urlopen(srv.base + '/').read().decode('utf-8', 'replace')
                        print('PC serves the altered shard:', PHOTO_URL in got, '| page keeps linked photos (IMG_LINK):', 'const IMG_LINK' in page, flush=True)
                    e2 = dict(env, PT_LASTUPD=LAST_UPDATED if role == 'keeper' else '', PT_PO_AID=PO_AID, PT_PHOTO_ID=PHOTO_ID if photo else '')
                    art = refx / 'articles'
                    if photo:                                   # the reference gets the same altered copy
                        art.unlink()
                        art.mkdir()
                        for f in (a.live_site / 'articles').iterdir():
                            os.symlink(f, art / f.name)
                        (art / '2025.json').unlink()
                        shutil.copy2(a.live_site / 'articles' / '2025.json', art / '2025.json')
                        alter_shard(art / '2025.json')
                    cmd = ['node', str(LC / 'parity.js'), '--ref', ref, '--pc', srv.base + '/', '--out', str(a.out), '--vp', a.vp, '--only', name, '--scheme', scheme] + extra
                    print(f'-- {scheme} {role} {name}', flush=True)
                    if subprocess.run(cmd, env=e2).returncode != 0:
                        bad.append(f'{scheme}/{role}/{name}')
                finally:
                    srv.stop()
                    shutil.rmtree(work, ignore_errors=True)
                    if photo and not art.is_symlink():
                        shutil.rmtree(art)
                        os.symlink(a.live_site / 'articles', art)
    finally:
        live.terminate()
    print('PARITYTEST:', ('FAIL, differences in: ' + ', '.join(bad)) if bad else 'PASS')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
