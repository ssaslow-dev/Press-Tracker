"""Install a new version of the tracker program over an existing tracker folder, without touching data\\ (A16, DATAINFOLDER-v1).

Run from the NEW release folder (the one just unzipped), by "Install update.cmd" (Windows) or "Install update.command" (Mac):
    python -I app/station/install_update.py "<the folder of the tracker you use now>"  [--check]

What it does, in this order, and stops with a plain message at the first problem (nothing is changed before step 5):
  1. checks the target is a tracker folder (data\\ and app\\ there, same kind: Windows or Mac) and is not running
  2. checks the new files against their own list (app\\APP_FILES.sha256)
  3. checks there is room for a copy of the new program parts
  4. copies the new program parts next to the old ones (app.new..., python.new...) and checks the copies
  5. moves the old app\\ and python\\ (and old start files) into <target>\\_previous_version\\<time>\\ and puts the new ones in their place
  6. checks the result, and checks that data\\ has the same number of files and bytes as before
Only app\\, python\\ (Mac: python-arm64, python-x86_64), the start files and READ ME FIRST.txt are replaced. data\\ is never written. Nothing is deleted:
the old program parts stay in _previous_version\\ (to go back: close the tracker, put them back; or delete that folder once the new version works for you).
Standard library only. Windows holding a file for a moment (virus scanner) is waited out (fs_retry)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]            # <new release folder>
sys.path.insert(0, str(SRC / 'app' / 'saver'))
import fs_retry as FR   # noqa: E402

PROGRAM_DIRS = ('app', 'python', 'python-arm64', 'python-x86_64')
START_FILES = ('Start Tracker.cmd', 'Start Tracker.command', 'start_tracker.sh', 'READ ME FIRST.txt')
PORT = 8765


class Stop(Exception):
    pass


def say(msg=''):
    print(msg, flush=True)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def tree_stats(root: Path):
    n = size = 0
    for dp, _, fs in os.walk(root):
        for f in fs:
            try:
                size += os.path.getsize(os.path.join(dp, f))
                n += 1
            except OSError:
                pass
    return n, size


def check_target(t: Path):
    if not t.is_dir():
        raise Stop(f'That folder is not there: {t}')
    if t == SRC or SRC in t.parents or t in SRC.parents:
        raise Stop('That is the new folder itself. Give the folder of the tracker you use now (the one with your data in it).')
    if not (t / 'data').is_dir() or not (t / 'app').is_dir():
        raise Stop(f'This does not look like a tracker folder (no data\\ and app\\ inside): {t}')
    mine_win, theirs_win = (SRC / 'python').is_dir(), (t / 'python').is_dir()
    if mine_win != theirs_win:
        raise Stop('The new version and the tracker you use now are for different computers (Windows and Mac). Nothing was changed.')
    try:
        with socket.create_connection(('127.0.0.1', PORT), timeout=1):
            raise Stop('The tracker is running. Close its window (the black one) first, then run this again. Nothing was changed.')
    except OSError:
        pass
    lock = t / 'data' / 'state' / 'app.lock'
    if lock.is_file() and time.time() - lock.stat().st_mtime < 30 * 60:
        raise Stop('The tracker looks busy (a save or a job may be running). Close the tracker, wait a minute and run this again. Nothing was changed.')


def check_source():
    lst = SRC / 'app' / 'APP_FILES.sha256'
    if not lst.is_file():
        raise Stop('This new folder has no file list (app\\APP_FILES.sha256). It may not have been unzipped completely. Nothing was changed.')
    bad = []
    for ln in lst.read_text(encoding='utf-8').splitlines():
        if not ln.strip():
            continue
        h, _, rel = ln.partition('  ')
        if rel.endswith('APP_FILES.sha256'):
            continue
        p = SRC / rel
        if not p.is_file() or sha256(p) != h:
            bad.append(rel)
    if bad:
        raise Stop(f'{len(bad)} files in the new folder do not match their list (first: {bad[0]}). Unzip the new zip again, in full. Nothing was changed.')


def app_manifest(root: Path) -> dict:
    out = {}
    for ln in (root / 'app' / 'APP_FILES.sha256').read_text(encoding='utf-8').splitlines():
        if ln.strip():
            h, _, rel = ln.partition('  ')
            if not rel.endswith('APP_FILES.sha256'):
                out[rel] = h
    return out


def verify_copy(a: Path, b: Path, label: str):
    na, sa = tree_stats(a)
    nb, sb = tree_stats(b)
    if (na, sa) != (nb, sb):
        raise Stop(f'The copy of {label} did not come out the same ({nb} files, {sb} bytes, expected {na} and {sa}). Nothing was changed.')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    check_only = '--check' in argv
    argv = [a for a in argv if a != '--check']
    if not argv:
        raise Stop('Give the folder of the tracker you use now.')
    # a path with spaces can arrive split into pieces (quote marks from a drag): join them back
    t = Path(' '.join(argv).strip().strip('"').strip("'").strip()).expanduser().resolve()
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    say(f'New version:   {SRC}')
    say(f'Your tracker:  {t}')
    check_target(t)
    say('The tracker folder looks right and the tracker is not running.')
    check_source()
    say('The new files match their list.')
    items = [d for d in PROGRAM_DIRS if (SRC / d).is_dir()]
    files = [f for f in START_FILES if (SRC / f).is_file()]
    need = sum(tree_stats(SRC / d)[1] for d in items)
    free = shutil.disk_usage(t).free
    if free < need * 1.15:
        raise Stop(f'Not enough room on that drive: the copy needs about {need // 2**20} MB and {free // 2**20} MB are free. Nothing was changed.')
    say(f'Will replace: {", ".join(d + chr(92) for d in items)} and {len(files)} start files. data\\ is not touched.')
    if check_only:
        say('(--check: nothing was changed.)')
        return 0
    before = tree_stats(t / 'data')
    new_names = {}
    try:
        for d in items:        # step 4
            say(f'Copying {d}\\ ...')
            tmp = t / f'{d}.new-{stamp}'
            shutil.copytree(SRC / d, tmp, symlinks=True)
            new_names[d] = tmp
            verify_copy(SRC / d, tmp, d)
    except BaseException:
        for tmp in new_names.values():
            shutil.rmtree(tmp, ignore_errors=True)       # our own half-made copy, never anything of the person's
        raise
    prev = t / '_previous_version' / stamp
    prev.mkdir(parents=True)
    done = []          # (kind, name) moved, for undo
    try:               # step 5
        for d in items:
            if (t / d).exists():
                FR.rename(t / d, prev / d)
                done.append(('moved', d))
            FR.rename(new_names[d], t / d)
            done.append(('placed', d))
        for f in files:
            if (t / f).exists():
                shutil.copy2(t / f, prev / f)
            tmp = t / (f + f'.new-{stamp}')
            shutil.copy2(SRC / f, tmp)
            FR.replace(tmp, t / f)
        for f in ('Start Tracker.command', 'start_tracker.sh'):
            if (t / f).is_file():
                os.chmod(t / f, 0o755)
    except BaseException as e:
        say('Something went wrong; putting the old program back ...')
        for kind, d in reversed(done):
            try:
                if kind == 'placed':
                    FR.rename(t / d, t / f'{d}.failed-{stamp}')
                else:
                    FR.rename(prev / d, t / d)
            except OSError:
                pass
        for tmp in new_names.values():
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)
        if isinstance(e, PermissionError):
            raise Stop('Windows would not let go of a file in the old program. Is the tracker window closed? Wait a minute and run this again. Your data was not touched.')
        raise
    # step 6
    want = app_manifest(SRC)
    got = app_manifest(t)
    if want != got:
        raise Stop('The new program was put in place but its file list does not match. Tell Claude. Your data was not touched; the old program is in _previous_version\\' + stamp)
    for rel, h in want.items():
        if sha256(t / rel) != h:
            raise Stop(f'{rel} did not come out right. Tell Claude. The old program is in _previous_version\\' + stamp)
    after = tree_stats(t / 'data')
    if after != before:
        raise Stop(f'data\\ has {after[0]} files and {after[1]} bytes but had {before[0]} and {before[1]}. This installer does not write there: something else changed it. Tell Claude.')
    (prev / 'update.json').write_text(json.dumps({'at': stamp, 'from': str(SRC), 'replaced': items + files, 'data_files': after[0], 'data_bytes': after[1]}, indent=1), encoding='utf-8')
    say()
    say('Done. The new version is installed. Your data was not touched'
        f' (still {after[0]} files, {after[1] // 2**20} MB).')
    say('Start the tracker the way you always do.')
    say(f'The old program is kept in _previous_version\\{stamp}. You can delete that folder when the new version has worked for you.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Stop as e:
        say()
        say('Stopped: ' + str(e))
        sys.exit(2)
    except Exception as e:      # noqa: BLE001
        say()
        say('The install stopped with an unexpected problem: ' + repr(e)[:300])
        say('Your data was not touched. Tell Claude.')
        sys.exit(3)
