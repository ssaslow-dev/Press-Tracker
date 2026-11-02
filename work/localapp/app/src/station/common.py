"""Shared helpers of the PC station layer (wrapper code around the finished pieces; nothing here edits them).
Standard library only. Everything stays inside the tracker folder (GOVIT-v1)."""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

APP = Path(__file__).resolve().parent.parent          # <root>/app
ROOT = APP.parent                                     # <root>  (the "AJG Tracker" folder)
for _d in ('updatefolder', 'saver', 'server'):
    if str(APP / _d) not in sys.path:
        sys.path.insert(0, str(APP / _d))

STALE_MINUTES = 30
WORKBOOK_NAME = 'AJG Coverage - NewsBank.xlsx'


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def stamp() -> str:
    return utc_now().strftime('%Y%m%dT%H%M%SZ')


def layout(root=None):
    from layout import PCLayout
    return PCLayout(root or ROOT)


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


_sha_cache: dict = {}


def cached_sha(p: Path) -> str | None:
    """sha256 of a file, recomputed only when size or mtime moved"""
    try:
        st = p.stat()
    except OSError:
        return None
    key = (str(p), st.st_size, st.st_mtime_ns)
    if key not in _sha_cache:
        _sha_cache.clear()
        _sha_cache[key] = sha256_file(p)
    return _sha_cache[key]


def atomic_write(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.part{os.getpid()}')
    with open(tmp, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_copy(src: Path, dst: Path) -> None:
    atomic_write(dst, Path(src).read_bytes())


def keep_old(path: Path, keep_dir: Path) -> Path | None:
    """copy the file about to be replaced into keep_dir (never delete, SAVE_RULES add-only spirit); returns the copy"""
    path = Path(path)
    if not path.is_file():
        return None
    keep_dir.mkdir(parents=True, exist_ok=True)
    t = keep_dir / path.name
    n = 2
    while t.exists():
        t = keep_dir / f'{path.stem} ({n}){path.suffix}'
        n += 1
    t.write_bytes(path.read_bytes())
    return t


# ---------------------------------------------------------------- the station's own lock (one writer across PCs)


class AppLockBusy(Exception):
    def __init__(self, info, age):
        super().__init__('locked')
        self.info, self.age = info or {}, age


class AppLock:
    """<state>/app.lock, created exclusively (works across PCs on a share, like the saver's own lock). Held for a whole preview,
    save (with the page and shard sync after it) or page rebuild, so a second PC never reads files while they are being replaced.
    Older than STALE_MINUTES: moved aside to <state>/logs/ and taken over. Released by a move, never a delete."""

    def __init__(self, state: Path, what: str):
        self.state, self.what = Path(state), what
        self.path = self.state / 'app.lock'
        self.token = os.urandom(8).hex()
        self.held = False

    def info(self):
        return read_lock(self.path)

    def acquire(self):
        self.state.mkdir(parents=True, exist_ok=True)
        for attempt in (1, 2):
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                info = self.info()
                age = lock_age_minutes(self.path, info)
                if age is not None and age < STALE_MINUTES or attempt == 2:
                    raise AppLockBusy(info, age)
                logs = self.state / 'logs'
                logs.mkdir(parents=True, exist_ok=True)
                try:
                    os.replace(self.path, logs / f'app.stale.{stamp()}.{self.token}')
                except OSError:
                    pass
                continue
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump({'what': self.what, 'host': socket.gethostname(), 'pid': os.getpid(), 'at': utc_now().isoformat(timespec='seconds'),
                           'token': self.token}, f)
            self.held = True
            return self

    def release(self):
        if not self.held:
            return
        self.held = False
        info = self.info()
        if info and info.get('token') == self.token:
            logs = self.state / 'logs'
            logs.mkdir(parents=True, exist_ok=True)
            try:
                os.replace(self.path, logs / f'app.lock.{self.what}.{stamp()}')
            except OSError:
                pass

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *a):
        self.release()


def read_lock(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def lock_age_minutes(p: Path, info=None):
    at = None
    try:
        at = datetime.fromisoformat(str((info or {}).get('at')).replace('Z', '+00:00'))
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        try:
            at = datetime.fromtimestamp(Path(p).stat().st_mtime, timezone.utc)
        except OSError:
            return None
    return (utc_now() - at).total_seconds() / 60


def lock_status(state: Path) -> dict:
    """what the panel shows: is a save (or the station) holding a lock right now, and who"""
    out = {'held': False}
    for name, label in (('saver.lock', 'a save'), ('app.lock', 'the tracker')):
        p = Path(state) / name
        if p.exists():
            info = read_lock(p) or {}
            age = lock_age_minutes(p, info)
            if age is not None and age >= STALE_MINUTES:
                out.setdefault('stale', []).append(name)
                continue
            out.update(held=True, by=info.get('host') or 'another PC', since=info.get('at'), age_minutes=None if age is None else round(age, 1),
                       what=label)
            break
    return out


def busy_line(info: dict, age) -> str:
    who = (info or {}).get('host') or 'another PC'
    when = f' (started {int(age)} minutes ago)' if age is not None else ''
    return (f'Another save is running on {who}{when}. Wait a few minutes, then try again. '
            'Nothing was changed.')


# ---------------------------------------------------------------- ledger / workbook state


def read_ledger(state: Path) -> list:
    p = Path(state) / 'ledger.jsonl'
    out = []
    try:
        for line in p.read_text(encoding='utf-8').splitlines():
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def baseline(state: Path):
    for e in reversed(read_ledger(state)):
        if e.get('verb') in ('init', 'save', 'confirm'):
            return e
    return None


def excel_open(wb: Path) -> bool:
    if (wb.parent / ('~$' + wb.name)).exists():
        return True
    # Windows only: Excel holds the file open, so opening it for writing is refused
    if os.name == 'nt':
        try:
            with open(wb, 'r+b'):
                pass
        except PermissionError:
            return True
        except OSError:
            return False
    return False


def workbook_state(lay) -> dict:
    wb = lay.workbook
    st = {'name': wb.name, 'exists': wb.is_file()}
    if not wb.is_file():
        return st
    s = wb.stat()
    sha = cached_sha(wb)
    base = baseline(lay.state)
    st.update(bytes=s.st_size, modified=datetime.fromtimestamp(s.st_mtime, timezone.utc).isoformat(timespec='seconds'), sha256=sha,
              excel_open=excel_open(wb))
    if base is None:
        st['baseline'] = 'missing'
    elif base.get('after_sha') != sha:
        st['baseline'] = 'changed'
        st['baseline_sha256'] = base.get('after_sha')
    elif not base.get('confirmed', True):
        st['baseline'] = 'unconfirmed'
    else:
        st['baseline'] = 'ok'
    return st
