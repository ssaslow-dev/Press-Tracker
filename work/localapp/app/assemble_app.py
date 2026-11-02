#!/usr/bin/env python3
"""assemble_app.py: join the finished pieces into one app folder, "AJG Tracker" (and a zip).

    python3 -I work/localapp/app/assemble_app.py [--target windows|linux] [--out DIR] [options]

Reads (never writes): code/, build/, data/ (the snapshot workbook and library), work/localapp/{build,server,updatefolder,winpack,vendor},
work/saver/src. Writes only into --out. Python 3.11+ on the build machine, internet for NuGet and PyPI (unless the caches are given).

--target windows   the product: NuGet CPython 3.13.16 (as probe/build_probe.py) + win_amd64 wheels (winpack/fetch_wheels.py, hash-pinned).
--target linux     the test build: a venv stands in for python\\ (same layout, same pinned versions as Linux wheels); python313._pth is
                   replaced by a .pth file with the same effect. Used by app/tests.
Layout (FORMAT.md section 3, code under app/ through layout.json):
    AJG Tracker/  Start Tracker.cmd  READ ME FIRST.txt  layout.json
      python/      app/{site-packages,server,station,updatefolder,saver,pipeline,docs}
      data/        workbook library backups state copies/articles db queue for_update updates/{incoming,staging,work,done,rejected} site tmp
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCALAPP = HERE.parent
REPO = HERE.parents[2]
SCRATCH = Path('/tmp/claude-0/-home-user-Press-Tracker/ec7aac73-d461-552b-aaac-9f8ebc5e7581/scratchpad')
APP_NAME = 'AJG Tracker'
PYVER = '3.13.16'
NUPKG_URL = f'https://api.nuget.org/v3-flatcontainer/python/{PYVER}/python.{PYVER}.nupkg'
DROP_DIRS = {'__pycache__', 'test', 'tests', 'idlelib', 'tkinter', 'ensurepip', 'turtledemo', 'lib2to3', 'site-packages'}   # as build_probe.py
DROP_TOP = {'include', 'libs'}
DROP_FILES = {'turtle.py'}
DROP_DLL = {'_tkinter.pyd', 'tcl86t.dll', 'tk86t.dll'}
PTH_LINES = ['python313.zip', '.', 'Lib', 'DLLs', r'..\app\site-packages', 'import site']
LAYOUT_JSON = {'pipeline': 'app/pipeline', 'saver': 'app/saver/saver.py'}


def sha256(p) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def say(*a):
    print('[assemble]', *a, flush=True)


def run(cmd, **kw):
    say('$', ' '.join(str(c) for c in cmd)[:200])
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding='utf-8', errors='replace', **kw)
    if r.returncode:
        sys.stderr.write((r.stdout or '')[-3000:] + (r.stderr or '')[-3000:])
        raise SystemExit(f'failed ({r.returncode}): {cmd[0]} {cmd[1] if len(cmd) > 1 else ""}')
    return r.stdout


def crlf(b: bytes) -> bytes:
    return b.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')


# ---------------------------------------------------------------- patches (winpack/patches) applied to COPIES

def apply_unified(text: str, patch: str, what: str) -> str:
    """minimal unified-diff applier for a one-file patch: every hunk's old lines must be found exactly once (nothing is guessed)"""
    lines = text.splitlines(keepends=True)
    hunks, cur = [], None
    for ln in patch.splitlines(keepends=True):
        if ln.startswith('@@'):
            cur = []
            hunks.append(cur)
        elif cur is not None and ln[:1] in ' +-':
            cur.append(ln)
    if not hunks:
        raise SystemExit(f'{what}: patch has no hunks')
    for h in hunks:
        old = [l[1:] for l in h if l[0] in ' -']
        new = [l[1:] for l in h if l[0] in ' +']
        at = [i for i in range(len(lines) - len(old) + 1) if lines[i:i + len(old)] == old]
        if len(at) != 1:
            raise SystemExit(f'{what}: hunk matches {len(at)} places (expected exactly 1); the file changed since the patch was written')
        lines[at[0]:at[0] + len(old)] = new
    return ''.join(lines)


def patched_copy(src: Path, dst: Path, patch_file: Path):
    txt = src.read_text(encoding='utf-8')
    new = apply_unified(txt, patch_file.read_text(encoding='utf-8'), patch_file.name)
    tmp = dst.with_name(dst.name + '.new')      # a new file, never a write into the old one (copies of the folder may hard-link it)
    tmp.write_text(new, encoding='utf-8', newline='\n')
    os.replace(tmp, dst)


# ---------------------------------------------------------------- the page build (work/localapp/build) -> pipeline + site

def page_build(a) -> Path:
    out = Path(a.page_build) if a.page_build else a.out / '_pagebuild'
    if (out / 'site' / 'index.html').is_file() and (out / 'stage' / 'build' / 'pub' / 'pipeline').is_dir() and not a.rebuild_page:
        say('using the existing page build', out)
        return out
    if not a.legacy or not Path(a.legacy).is_file():
        raise SystemExit('--legacy FILE (legacy_index.html from the live tracker) is needed to build the page')
    cmd = [sys.executable, '-I', LOCALAPP / 'build' / 'build_tracker.py', '--out', out, '--legacy', a.legacy, '--xlsx', a.workbook]
    if a.live_site:
        cmd += ['--live-site', a.live_site]
    run(cmd)
    return out


# ---------------------------------------------------------------- python\ and site-packages

def get_nupkg(a) -> Path:
    cand = [Path(a.nupkg)] if a.nupkg else []
    cand.append(SCRATCH / 'probe_build' / 'download' / f'python.{PYVER}.nupkg')
    for c in cand:
        if c.is_file():
            return c
    dst = a.out / '_cache' / f'python.{PYVER}.nupkg'
    dst.parent.mkdir(parents=True, exist_ok=True)
    say('downloading', NUPKG_URL)
    urllib.request.urlretrieve(NUPKG_URL, dst)
    return dst


def build_python_windows(root: Path, a, info: dict):
    nupkg = get_nupkg(a)
    info['nupkg'] = {'file': nupkg.name, 'sha256': sha256(nupkg), 'version': PYVER, 'source': NUPKG_URL}
    pydir = root / 'python'
    with zipfile.ZipFile(nupkg) as z:
        for i in z.infolist():
            n = i.filename
            if not n.startswith('tools/') or n.endswith('/'):
                continue
            parts = n[len('tools/'):].split('/')
            if parts[0] in DROP_TOP or any(p in DROP_DIRS for p in parts[:-1]) or parts[-1] in DROP_FILES or parts[-1] in DROP_DLL or parts[-1].endswith('.pyc'):
                continue
            dest = pydir.joinpath(*parts)
            if not str(dest.resolve()).startswith(str(pydir.resolve())):
                raise SystemExit('unsafe path in nupkg: ' + n)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(i) as s, open(dest, 'wb') as d:
                shutil.copyfileobj(s, d)
    for name in ('python313._pth', 'python._pth'):     # which of the two names Windows honours is untested (README: Windows round); both say the same
        (pydir / name).write_bytes(crlf(('\n'.join(PTH_LINES) + '\n').encode()))
    if sys.version_info[:2] == (3, 13):
        run([sys.executable, '-m', 'compileall', '-q', '-j', '0', '--invalidation-mode', 'unchecked-hash', pydir / 'Lib'])


def requirements():
    pins = []
    for line in (LOCALAPP / 'winpack' / 'requirements-win.txt').read_text(encoding='utf-8').splitlines():
        m = re.match(r'^([A-Za-z0-9_.-]+==\S+)\s+--hash', line.strip())
        if m:
            pins.append(m.group(1))
    return pins


def build_python_linux(root: Path, a, info: dict):
    pydir = root / 'python'
    run([sys.executable, '-m', 'venv', '--without-pip', pydir])
    sp = next(pydir.glob('lib/python3.*/site-packages'))
    rel = os.path.relpath(root / 'app' / 'site-packages', sp)
    (sp / 'ajg.pth').write_text(rel + '\n', encoding='utf-8')     # the Linux stand-in for python313._pth's ..\app\site-packages
    info['python'] = {'venv_of': sys.version.split()[0]}


def build_site_packages(root: Path, a, info: dict):
    sp = root / 'app' / 'site-packages'
    if a.target == 'windows':
        cache = Path(a.wheel_cache) if a.wheel_cache else a.out / '_cache' / 'wheels'
        run([sys.executable, '-I', LOCALAPP / 'winpack' / 'fetch_wheels.py', '--cache', cache, '--extract', sp])
        info['wheels'] = {p.name: sha256(p) for p in sorted(cache.glob('*.whl'))}
    else:
        sp.mkdir(parents=True)
        run([sys.executable, '-m', 'pip', 'install', '--quiet', '--no-deps', '--only-binary=:all:', '--target', sp] + requirements())
        for d in list(sp.rglob('tests')):
            if d.is_dir():
                shutil.rmtree(d)
        shutil.rmtree(sp / 'bin', ignore_errors=True)
        run([sys.executable, '-m', 'compileall', '-q', '-j', '0', '--invalidation-mode', 'unchecked-hash', sp])
        info['wheels'] = {'installed_from_pypi_for_linux': requirements()}


# ---------------------------------------------------------------- app code

def copy_app_code(root: Path, pb: Path, info: dict):
    app = root / 'app'
    ign = shutil.ignore_patterns('__pycache__', '*.pyc')
    # server (finished piece, unchanged)
    (app / 'server').mkdir(parents=True)
    for f in ('server.py', 'claude_shim.js'):
        shutil.copy2(LOCALAPP / 'server' / f, app / 'server' / f)
    # updatefolder (unchanged)
    (app / 'updatefolder').mkdir()
    for f in ('formats.py', 'layout.py', 'make_for_update.py', 'take_update.py'):
        shutil.copy2(LOCALAPP / 'updatefolder' / f, app / 'updatefolder' / f)
    # saver: saver.py, saver_diff.py unchanged; saver_steps.py = patch 03 applied to a copy; pipeline_sha.py (tool) for the sha list
    (app / 'saver').mkdir()
    for f in ('saver.py', 'saver_diff.py'):
        shutil.copy2(REPO / 'work' / 'saver' / 'src' / f, app / 'saver' / f)
    patched_copy(REPO / 'work' / 'saver' / 'src' / 'saver_steps.py', app / 'saver' / 'saver_steps.py',
                 LOCALAPP / 'winpack' / 'patches' / '03_saver_steps_utf8_nonet.patch')
    shutil.copy2(REPO / 'work' / 'saver' / 'tools' / 'pipeline_sha.py', app / 'saver' / 'pipeline_sha.py')
    # station layer (this folder's src/)
    shutil.copytree(HERE / 'src' / 'station', app / 'station', ignore=ign)
    shutil.copy2(LOCALAPP / 'winpack' / 'selfcheck.py', app / 'station' / 'selfcheck.py')
    # docs for whoever opens the folder (IT, Sammy)
    (app / 'docs').mkdir()
    for src in (LOCALAPP / 'updatefolder' / 'FORMAT.md', LOCALAPP / 'IT_NOTE.md', LOCALAPP / 'winpack' / 'README.md', HERE / 'README.md'):
        if src.is_file():
            shutil.copy2(src, app / 'docs' / src.name)
    # the pipeline: the page build's published-pipeline folder + winpack patches 01 and 02 on the copy + pdftext_pypdf.py
    pipe = app / 'pipeline'
    shutil.copytree(pb / 'stage' / 'build' / 'pub' / 'pipeline', pipe, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'docs', 'PIPELINE.sha256'))
    wp = LOCALAPP / 'winpack' / 'patches'
    patched_copy(pipe / 'release_rule.py', pipe / 'release_rule.py', wp / '01_release_rule_pdftext.patch')
    patched_copy(pipe / 'img_embed.py', pipe / 'img_embed.py', wp / '02_img_embed_offline.patch')
    shutil.copy2(wp / 'pdftext_pypdf.py', pipe / 'pdftext_pypdf.py')
    # PHOTOLINK-v1: the PC keeps photos as links. Patches and the new module live next to this script (app/patches/); each patch must match exactly once.
    ap_ = HERE / 'patches'
    patched_copy(pipe / 'img_embed.py', pipe / 'img_embed.py', ap_ / '04_img_embed_photolink.patch')
    patched_copy(pipe / 'sheet_task.py', pipe / 'sheet_task.py', ap_ / '05_sheet_task_photolink.patch')
    shutil.copy2(ap_ / 'photolink.py', pipe / 'photolink.py')
    patched_copy(pipe / 'tracker.js', pipe / 'tracker.js', ap_ / '06_tracker_js_photolink.patch')    # the viewer keeps linked photos; every page rebuild uses this tracker.js
    # LOCALFONTS-v1: no Google Fonts request from the PC page or the viewer frame; the fonts are served from data\site\fonts (copy_fonts)
    patched_copy(pipe / 'shell.html', pipe / 'shell.html', ap_ / '08_shell_localfonts.patch')
    patched_copy(pipe / 'tracker.js', pipe / 'tracker.js', ap_ / '07_tracker_js_localfonts.patch')
    spec = importlib.util.spec_from_file_location('pipeline_sha', REPO / 'work' / 'saver' / 'tools' / 'pipeline_sha.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    (pipe / 'PIPELINE.sha256').write_text(m.build(pipe), encoding='utf-8', newline='\n')
    info['pipeline_files'] = sum(1 for _ in (pipe / 'PIPELINE.sha256').read_text().splitlines())
    if (REPO / '.git').exists():
        g = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True)
        info['source_commit'] = g.stdout.strip()


# ---------------------------------------------------------------- data\

DATA_DIRS = ['workbook', 'library', 'backups', 'state', 'copies/articles', 'db', 'queue', 'for_update', 'updates/incoming', 'updates/staging',
             'updates/work', 'updates/done', 'updates/rejected', 'updates/refresh_incoming', 'refresh_out', 'site/data', 'tmp']


def copy_tree(src: Path, dst: Path, hardlink=False):
    shutil.copytree(src, dst, copy_function=(os.link if hardlink else shutil.copy2), dirs_exist_ok=True)


FONTS_SRC = LOCALAPP / 'fonts' / 'google'      # SAMELOOK-v2: the files Google serves to the old tracker (fonts/fetch_google_fonts.py), not the static fontsource ones


def patch_index_fonts(idx: Path):
    """LOCALFONTS-v1: the same two patches as pipeline/shell.html and pipeline/tracker.js, on a page already built (each must match exactly once)"""
    ap_ = HERE / 'patches'
    patched_copy(idx, idx, ap_ / '08_shell_localfonts.patch')
    patched_copy(idx, idx, ap_ / '07_tracker_js_localfonts.patch')


def copy_fonts(data: Path):
    """LOCALFONTS-v1 / SAMELOOK-v2: Roboto Slab and Public Sans, the very files Google serves (fonts/fetch_google_fonts.py), with page.css (what the page asks
    for) and viewer.css (what the saved-copy frame asks for) and their licence texts, into data\\site\\fonts; served by the page server like any site file"""
    dst = data / 'site' / 'fonts'
    if not (FONTS_SRC / 'page.css').is_file():
        raise SystemExit('fonts: work/localapp/fonts/google is missing (python3 -I work/localapp/fonts/fetch_google_fonts.py)')
    if dst.is_dir():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for f in sorted(FONTS_SRC.iterdir()):
        if f.is_file() and f.suffix != '.json':
            shutil.copy2(f, dst / f.name)


def fill_data(root: Path, pb: Path, a, info: dict):
    data = root / 'data'
    for d in DATA_DIRS:
        (data / d).mkdir(parents=True, exist_ok=True)
    (data / 'role.json').write_text(json.dumps({'role': a.role}) + '\n', encoding='utf-8')
    site = pb / 'site'
    patched_copy(site / 'index.html', data / 'site' / 'index.html', HERE / 'patches' / '06_tracker_js_photolink.patch')   # PHOTOLINK-v1: the same viewer patch as pipeline/tracker.js (a rebuild makes it from there)
    patch_index_fonts(data / 'site' / 'index.html')
    copy_fonts(data)
    for f in (site / 'data').iterdir():
        shutil.copy2(f, data / 'site' / 'data' / f.name)
    if a.live_site and (Path(a.live_site) / 'img').is_dir():
        copy_tree(Path(a.live_site) / 'img', data / 'site' / 'img')
    if a.live_site and (Path(a.live_site) / 'articles').is_dir():
        copy_tree(Path(a.live_site) / 'articles', data / 'copies' / 'articles')   # the page reads them through the server's /articles/ route
    if a.data_mode != 'snapshot':
        return
    wb = Path(a.workbook)
    shutil.copy2(wb, data / 'workbook' / wb.name)
    info['workbook_sha256'] = sha256(data / 'workbook' / wb.name)
    lib = Path(a.library)
    if lib.is_dir():
        say('library: ', 'hard links' if a.library_mode == 'hardlink' else 'copy')
        copy_tree(lib, data / 'library', hardlink=a.library_mode == 'hardlink')
    # the saver's starting point (SAVE_RULES answer 2: accepting the file as it is)
    run([sys.executable, '-I', root / 'app' / 'saver' / 'saver.py', 'init', '--workbook', data / 'workbook' / wb.name, '--state', data / 'state',
         '--sha', info['workbook_sha256'], '--note', 'assemble_app.py: snapshot copy accepted as the starting point'])


# ---------------------------------------------------------------- top-level files

def top_files(root: Path, a):
    (root / 'layout.json').write_text(json.dumps(LAYOUT_JSON, indent=1) + '\n', encoding='utf-8')
    src = HERE / 'src' / 'launcher'
    (root / 'Start Tracker.cmd').write_bytes(crlf((src / 'Start Tracker.cmd').read_bytes()))
    (root / 'READ ME FIRST.txt').write_bytes(crlf((src / 'READ ME FIRST.txt').read_bytes()))
    if a.target == 'linux':
        p = root / 'start_tracker.sh'
        p.write_text('#!/bin/sh\ncd "$(dirname "$0")"\nexec python/bin/python -B -X utf8 -I app/station/launcher.py "$@"\n', encoding='utf-8')
        p.chmod(0o755)


def app_manifest(root: Path):
    """sha256 of every file of app/ except site-packages (those are the pinned wheels: hashes are in BUILD_INFO.json)"""
    lines = []
    for p in sorted((root / 'app').rglob('*')):
        rel = p.relative_to(root / 'app')
        if p.is_file() and rel.parts[0] != 'site-packages' and '__pycache__' not in rel.parts and p.suffix != '.pyc':
            lines.append(f'{sha256(p)}  app/{rel.as_posix()}')
    (root / 'app' / 'APP_FILES.sha256').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


def precompile(root: Path):
    if sys.version_info[:2] == (3, 13):
        subprocess.run([sys.executable, '-m', 'compileall', '-q', '-j', '0', '--invalidation-mode', 'unchecked-hash', str(root / 'app' / 'server'),
                        str(root / 'app' / 'station'), str(root / 'app' / 'updatefolder'), str(root / 'app' / 'saver')], capture_output=True)


def stats(root: Path):
    n = size = 0
    for p in root.rglob('*'):
        if p.is_file():
            n += 1
            size += p.stat().st_size
    return n, size


def make_zip(root: Path, zpath: Path, with_library: bool):
    skip = ('data/library/',) if not with_library else ()
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(root.rglob('*')):
            rel = p.relative_to(root.parent).as_posix()
            if p.is_dir() or any(rel.startswith(f'{APP_NAME}/{s}') for s in skip) or '/data/tmp/' in rel:
                continue
            z.write(p, rel)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--target', choices=['windows', 'linux'], default='windows')
    ap.add_argument('--out', type=Path, default=SCRATCH / 'app_build')
    ap.add_argument('--workbook', default=str(REPO / 'data' / 'AJG Coverage - NewsBank.xlsx'))
    ap.add_argument('--library', default=str(REPO / 'data' / 'library'))
    ap.add_argument('--library-mode', choices=['copy', 'hardlink'], default='copy')
    ap.add_argument('--data-mode', choices=['snapshot', 'empty'], default='snapshot', help='snapshot: data/ filled from the copies (test build)')
    ap.add_argument('--legacy', default=str(SCRATCH / 'live_pipeline' / 'pipeline' / 'legacy_index.html'))
    ap.add_argument('--live-site', default=str(SCRATCH / 'live_site'))
    ap.add_argument('--page-build', help='an existing build_tracker.py output folder to reuse (default OUT/_pagebuild, built if missing)')
    ap.add_argument('--rebuild-page', action='store_true')
    ap.add_argument('--nupkg')
    ap.add_argument('--wheel-cache')
    ap.add_argument('--code-only', action='store_true', help='re-copy only the code (app/ except site-packages, top files) into an existing build')
    ap.add_argument('--refresh-page', action='store_true', help='with --code-only: also replace data/site/index.html and data/site/data/* from the page build (a test build whose page build changed; a keeper copy that has saved keeps its own page, so never use it there)')
    ap.add_argument('--role', choices=['keeper', 'reader'], default='reader', help='role.json of this copy (MULTIPC-v2); the keeper copy is set once at setup')
    ap.add_argument('--zip', action='store_true', help='also write AJG Tracker.zip (without data/library unless --zip-library)')
    ap.add_argument('--zip-library', action='store_true')
    a = ap.parse_args(argv)
    a.out = a.out.resolve()
    work = a.out / a.target
    root = work / APP_NAME
    info = {'target': a.target, 'built_by': 'work/localapp/app/assemble_app.py'}
    if a.code_only:
        if not (root / 'app' / 'site-packages').is_dir():
            raise SystemExit('--code-only needs an existing build in ' + str(root))
        pb = page_build(a)
        for d in ('server', 'station', 'updatefolder', 'saver', 'pipeline', 'docs'):
            shutil.rmtree(root / 'app' / d, ignore_errors=True)
        copy_app_code(root, pb, info)
        idx = root / 'data' / 'site' / 'index.html'      # PHOTOLINK-v1: the page already in data\site gets the viewer patch too (once; a rebuilt page has it already)
        if idx.is_file() and 'PHOTOLINK-v1 (PC tracker)' not in idx.read_text(encoding='utf-8'):
            patched_copy(idx, idx, HERE / 'patches' / '06_tracker_js_photolink.patch')
        if idx.is_file():                                 # LOCALFONTS-v1 (same rule); a page patched by the first version (one fonts.css) is moved to page.css / viewer.css
            txt = idx.read_text(encoding='utf-8')
            if '/fonts/fonts.css' in txt:
                idx.write_text(txt.replace('href="/fonts/fonts.css"', 'href="/fonts/page.css"').replace('@import url("/fonts/fonts.css")', '@import url("/fonts/viewer.css")'), encoding='utf-8', newline='')
            elif '/fonts/page.css' not in txt:
                patch_index_fonts(idx)
        copy_fonts(root / 'data')
        if a.refresh_page:
            site = pb / 'site'
            patched_copy(site / 'index.html', root / 'data' / 'site' / 'index.html', HERE / 'patches' / '06_tracker_js_photolink.patch')
            patch_index_fonts(root / 'data' / 'site' / 'index.html')
            for f in (site / 'data').iterdir():
                tmp = root / 'data' / 'site' / 'data' / (f.name + '.new')      # replaced, never written into (hard links)
                shutil.copy2(f, tmp)
                os.replace(tmp, root / 'data' / 'site' / 'data' / f.name)
        top_files(root, a)
        precompile(root)
        app_manifest(root)
        say('code refreshed in', root)
        if a.zip:
            z = work / f'{APP_NAME}.zip'
            make_zip(root, z, a.zip_library)
            say(f'{z}: {z.stat().st_size / 1e6:.1f} MB sha256 {sha256(z)}')
        return 0
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    pb = page_build(a)
    (root / 'app').mkdir()
    (build_python_windows if a.target == 'windows' else build_python_linux)(root, a, info)
    build_site_packages(root, a, info)
    copy_app_code(root, pb, info)
    top_files(root, a)
    fill_data(root, pb, a, info)
    precompile(root)
    app_manifest(root)
    (root / 'app' / 'BUILD_INFO.json').write_text(json.dumps(info, indent=1) + '\n', encoding='utf-8')
    n, size = stats(root)
    say(f'{root}: {n} files, {size / 1e6:.1f} MB')
    if a.zip:
        z = work / f'{APP_NAME}.zip'
        make_zip(root, z, a.zip_library)
        say(f'{z}: {z.stat().st_size / 1e6:.1f} MB sha256 {sha256(z)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
