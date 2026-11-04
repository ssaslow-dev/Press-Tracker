"""PARITYTEST-v1: the live tracker's own files against the PC tracker, same workbook, same clicks; outcomes compared.

    python3 -I work/localapp/paritytest/run_paritytest.py [--build "…/AJG Tracker"] [--live-site DIR] [--out DIR] [--only a,b] [--vp 1440x900]

Reference = the live tracker's published files (fetched read-only into --live-site, built from the same workbook as the PC build), served by a plain static
server on 127.0.0.1 with an in-memory stand-in for the live tracker's database (parity.js MOCK); the live artifact and its database are never touched.
The reference page gets the recorded layout exceptions the PC build applies (TIDY-v1, patches 15 to 18) and nothing else.
Candidate = the PC build's launcher on a hard-linked working copy (the build is never written). Tests: lookcheck/parity.js (search, dates, facets, sort, views,
story sheet, saved copies, notes, history, routes, downloads, every tab table) plus paritytest/extra.js (edits, notes and views in the stand-in storage,
Manage panel, every tab, links and photos, reprint groups, exports). Allowed differences: paritytest/allowed.json (each with its reason).
Exit code 0 when no un-allowed difference. Results: OUT/parity/*.json and OUT/parity/summary.
"""
import tempfile
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LC = REPO / 'work' / 'localapp' / 'lookcheck'
SCRATCH = Path(os.environ.get('AJG_SCRATCH') or os.path.join(tempfile.gettempdir(), 'ajg_scratch'))
sys.path.insert(0, str(LC))
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'app' / 'tests'))
import run_lookcheck as RL  # noqa: E402  (free_port, wait_http)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, default=SCRATCH / 'paritytest_out')
    ap.add_argument('--build', type=Path, default=SCRATCH / 'app_build_pt' / 'linux' / 'AJG Tracker')
    ap.add_argument('--live-site', type=Path, default=SCRATCH / 'live_v65')
    ap.add_argument('--vp', default='1440x900')
    ap.add_argument('--only', default='')
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
    port = RL.free_port()
    live = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=refx, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ref = f'http://127.0.0.1:{port}/index.html'
    env = dict(os.environ, PLAYWRIGHT_MODULE='/opt/node-tools/node_modules/playwright')
    extra = ['--extra', str(HERE / 'extra.js'), '--allow', str(HERE / 'allowed.json')]
    names = a.only.split(',') if a.only else subprocess.run(['node', str(LC / 'parity.js'), '--list', '--out', str(a.out)] + extra, env=env, capture_output=True, text=True).stdout.strip().split(',')
    assert names and all(names), 'could not list the interactions'
    (a.out / 'parity').mkdir(parents=True, exist_ok=True)
    (a.out / 'parity' / f'{a.vp}_summary.json').unlink(missing_ok=True)
    bad = 0
    try:
        assert RL.wait_http(ref), 'reference server did not start'
        for name in names:
            # the PC side keeps its database in files: every interaction gets a fresh copy of the build's data (the reference's stand-in starts empty each time)
            work = a.out / '_pc'
            shutil.rmtree(work, ignore_errors=True)
            srv = T.Server(T.make_work(work, 'w', 'keeper')).start()
            left = [str(f.relative_to(work)) for f in (work / 'w' / 'AJG Tracker' / 'data' / 'db').rglob('*') if f.is_file()]
            if left:
                print('WARNING: the PC data copy was not empty before', name, left[:5], flush=True)
            try:
                cmd = ['node', str(LC / 'parity.js'), '--ref', ref, '--pc', srv.base + '/', '--out', str(a.out), '--vp', a.vp, '--only', name] + extra
                bad += subprocess.run(cmd, env=env).returncode != 0
            finally:
                srv.stop()
                shutil.rmtree(work, ignore_errors=True)
    finally:
        live.terminate()
    print('PARITYTEST:', 'FAIL, %d interaction(s) with un-allowed differences' % bad if bad else 'PASS')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
