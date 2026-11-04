"""REVIEW_3 support: a small stand-in app folder built from the repository's own sources (no assembled build, no page build, no network), with a
synthetic workbook and library, so the station modules (switchover, rename_files, drop_unverified, other_files_column, common) run as they do in
the PC tracker. Everything lives in a temporary folder; nothing in data/, code/ or the Mac files is touched."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APPSRC = HERE.parent.parent            # work/localapp/app
LOCALAPP = APPSRC.parent
REPO = LOCALAPP.parent.parent
WB_NAME = 'AJG Coverage - NewsBank.xlsx'
COLS = ['Article ID', 'Story ID', 'Original or reprint', 'Date', 'Year', 'Outlet', 'Headline', 'Translated Headline', 'Language', 'File name', 'File name 2',
        'Saved Copy?', 'Press release', 'Role', 'Author 1', 'Author / byline', 'Team note', 'Tone', 'Tone note', 'Tone rated by', 'Topic', 'Bills', '# of reprints']


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def make_root(base: Path) -> Path:
    """<base>/AJG Tracker with app/{station,updatefolder,saver,pipeline}, layout.json and an empty data folder"""
    root = base / 'AJG Tracker'
    app = root / 'app'
    shutil.copytree(APPSRC / 'src' / 'station', app / 'station', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (app / 'updatefolder').mkdir()
    for f in ('formats.py', 'layout.py', 'make_for_update.py', 'take_update.py', 'fs_retry.py'):
        shutil.copy2(LOCALAPP / 'updatefolder' / f, app / 'updatefolder' / f)
    (app / 'saver').mkdir()
    for f in ('saver.py', 'saver_diff.py', 'saver_steps.py', 'fs_retry.py'):
        shutil.copy2(REPO / 'work' / 'saver' / 'src' / f, app / 'saver' / f)
    (app / 'pipeline').mkdir()
    shutil.copy2(REPO / 'code' / 'sheet_task.py', app / 'pipeline' / 'sheet_task.py')
    (app / 'server').mkdir()
    (root / 'layout.json').write_text(json.dumps({'pipeline': 'app/pipeline', 'saver': 'app/saver/saver.py'}), encoding='utf-8')
    (root / 'data').mkdir()
    (root / 'data' / 'role.json').write_text(json.dumps({'role': 'keeper'}), encoding='utf-8')
    return root


def load_modules(root: Path):
    sys.path.insert(0, str(root / 'app' / 'station'))
    import common as C          # puts app/updatefolder, app/saver, app/server on sys.path
    import rename_files as RF
    import switchover as SW
    import take_update as TU
    return C, RF, SW, TU


def row(**kw) -> list:
    return [kw.get(c) for c in COLS]


def write_workbook(path: Path, rows: list, other_files: bool = False) -> Path:
    """Coverage + Originals (mirror of the Original rows) + the other tabs the steps read, with the columns the switch-over steps touch"""
    import openpyxl
    cols = COLS + (['Other files'] if other_files else [])
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Coverage'
    ws.append(cols)
    for r in rows:
        ws.append(list(r) + ([None] if other_files else []))
    o = wb.create_sheet('Originals')
    o.append(cols)
    for r in rows:
        if r[COLS.index('Original or reprint')] == 'Original':
            o.append(list(r) + ([None] if other_files else []))
    pr = wb.create_sheet('Press releases')
    pr.append(['Release ID', 'URL', 'Title', 'Date', 'Copy story ID 1', 'Copy story ID 2'])
    av = wb.create_sheet('Audio & video details')
    av.append(['Article ID', 'Episode/segment title', 'Transcript file'])
    rm = wb.create_sheet('Removed')
    rm.append(['Article ID', 'From tab'])
    up = wb.create_sheet('Unlinked print pages')
    up.append(['Article ID', 'Outlet', 'NewsBank print-page link'])
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(path))
    return path


def fresh_data(root: Path, rows: list, files: dict, other_files: bool = False):
    """reset data/: the workbook from `rows`, the library from `files` ({'2026/x.html': 'text', ...}); returns the workbook path"""
    data = root / 'data'
    for d in ('workbook', 'library', 'backups', 'state', 'tmp', 'switchover', 'logs'):
        shutil.rmtree(data / d, ignore_errors=True)
    wb = write_workbook(data / 'workbook' / WB_NAME, rows, other_files=other_files)
    for rel, text in files.items():
        p = data / 'library' / Path(*rel.split('/'))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
    return wb


def library_listing(lib: Path) -> list:
    return sorted(p.relative_to(lib).as_posix() for p in lib.rglob('*') if p.is_file() and '_renamed' not in p.parts)


def ledger(root: Path) -> list:
    p = root / 'data' / 'state' / 'ledger.jsonl'
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()] if p.is_file() else []
