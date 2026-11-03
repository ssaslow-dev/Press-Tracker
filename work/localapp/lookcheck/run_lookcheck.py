"""SAMELOOK-v2 check: the live tracker's own published files against the PC page, side by side.

    python3 -I work/localapp/lookcheck/run_lookcheck.py [--out DIR] [--viewports 1440x900,960x1040] [--only a,b] [--no-parity] [--no-capture]
                                                        [--build "…/AJG Tracker"] [--live-site DIR]

What it does (details in README.md)
  1. serves the reference (the live tracker's files, a plain static server on 127.0.0.1) and the PC page (the PC build's own launcher, on a hard-linked
     working copy so nothing in the build is written);
  2. lookcheck.js: for every route and interaction, in the same Chromium, viewport, clock, locale and empty storage, a full-page screenshot, the computed
     styles of every visible element and the font file Chromium used for every piece of text, for the reference, the reference with the recorded
     exception applied ("refhide") and the PC page;
  3. compare.py: refhide against pc (must be 0 pixels, 0 style differences) and ref against pc with only the exception rectangles masked (shows the reflow
     the exception causes);
  4. parity.js: the same clicks and typing on both, outcomes compared (counts, lists, URLs, downloaded bytes, notes, views, Back/Forward).
Exit code 0 when everything is identical.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRATCH = Path(os.environ.get('AJG_SCRATCH') or '/tmp/claude-0/-home-user-Press-Tracker/ec7aac73-d461-552b-aaac-9f8ebc5e7581/scratchpad')
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'app' / 'tests'))


def free_port():
    import socket
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def wait_http(url, tries=100):
    for _ in range(tries):
        try:
            urllib.request.urlopen(url, timeout=3).read(10)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, default=SCRATCH / 'lookcheck_out')
    ap.add_argument('--viewports', default='1440x900,960x1040')
    ap.add_argument('--only', default='')
    ap.add_argument('--build', type=Path, default=SCRATCH / 'app_build' / 'linux' / 'AJG Tracker')
    ap.add_argument('--live-site', type=Path, default=SCRATCH / 'live_site')
    ap.add_argument('--parity-only', default='', help='parity interactions to run (default: the same list as --only, which only fits when it names parity interactions; empty = all)')
    ap.add_argument('--no-parity', action='store_true')
    ap.add_argument('--no-capture', action='store_true')
    ap.add_argument('--node', default='node')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    os.environ['AJG_TEST_BUILD'] = str(a.build)
    import support as T                                     # noqa: E402  (hard-linked working copy + launcher helpers of the app tests)
    work = a.out / '_pc'
    shutil.rmtree(work, ignore_errors=True)
    root = T.make_work(work, 'w', 'keeper')
    srv = T.Server(root).start()
    port = free_port()
    live = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=a.live_site, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ref = f'http://127.0.0.1:{port}/index.html'
    # TIDY-v1: the reference with the TIDY-v1 changes applied (the very patch files the PC build applies: app/patches 15 to 18) next to the untouched reference.
    # "refhide" (reference with the recorded exceptions) is taken from this copy, so everything outside TIDY-v1 is still compared with the live tracker's own page.
    refx_dir = a.out / '_refx'
    shutil.rmtree(refx_dir, ignore_errors=True)
    refx_dir.mkdir(parents=True)
    for f in a.live_site.iterdir():
        if f.name != 'index.html':
            os.symlink(f, refx_dir / f.name)
    import importlib.util
    spec = importlib.util.spec_from_file_location('assemble_app', REPO / 'work' / 'localapp' / 'app' / 'assemble_app.py')
    A = importlib.util.module_from_spec(spec)
    sys.modules['assemble_app'] = A
    spec.loader.exec_module(A)
    shutil.copy2(a.live_site / 'index.html', refx_dir / 'index.html')
    A.patch_index_tidy(refx_dir / 'index.html')
    portx = free_port()
    livex = subprocess.Popen([sys.executable, '-m', 'http.server', str(portx), '--bind', '127.0.0.1'], cwd=refx_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    refx = f'http://127.0.0.1:{portx}/index.html'
    env = dict(os.environ, PLAYWRIGHT_MODULE='/opt/node-tools/node_modules/playwright')
    bad = 0
    try:
        assert wait_http(ref) and wait_http(refx), 'reference server did not start'
        for vp in a.viewports.split(','):
            if not a.no_capture:
                cmd = [a.node, str(HERE / 'lookcheck.js'), '--ref', ref, '--refx', refx, '--pc', srv.base + '/', '--out', str(a.out), '--vp', vp]
                if a.only:
                    cmd += ['--only', a.only]
                print('>>', ' '.join(cmd), flush=True)
                subprocess.run(cmd, check=False, env=env)
            for name, ref_dir in (('exception_applied', 'refhide'), ('raw', 'ref')):
                cmd = [sys.executable, '-I', str(HERE / 'compare.py'), '--a', str(a.out / vp / ref_dir), '--b', str(a.out / vp / 'pc'), '--out', str(a.out / vp / ('diff_' + ref_dir)),
                       '--json', str(a.out / f'results_{vp}_{name}.json')]
                if a.only:
                    cmd += ['--only', a.only]
                print('>>', name, vp, flush=True)
                subprocess.run(cmd, check=False)
            if not a.no_parity:
                cmd = [a.node, str(HERE / 'parity.js'), '--ref', refx, '--pc', srv.base + '/', '--out', str(a.out), '--vp', vp]
                if a.parity_only:
                    cmd += ['--only', a.parity_only]
                print('>>', ' '.join(cmd), flush=True)
                bad += subprocess.run(cmd, check=False, env=env).returncode != 0
    finally:
        live.terminate()
        livex.terminate()
        srv.stop()
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
