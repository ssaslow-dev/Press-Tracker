#!/usr/bin/env python3
"""saver.py: "save the last run to the sheet" as one program (SAVER_SPEC.md, SAVE_RULES.md).

Verbs: `init` and `confirm` (the checksum ledger), `preview` (spec section 3 steps 1 to 9, writes nothing outside --out and --state) and
`save` (steps 1 to 14: the same steps 1 to 9, then token check, backup, atomic swap of the master, add-only library pages, removals moved to
_to_delete/, ledger entry, log, rebuild). `save` holds the process lock from step 2 to the end, with no gap between the preview part and the commit.

What save writes, and where: the backup copy (--backups), the master (os.replace of a uniquely named staged file beside it), library pages
(add-only), moved library files (LIB/_to_delete/), LIB/.sheet_task.lock (moved to LIB/_to_delete/ at the end), --state (ledger, logs, lock),
--out. Nothing is ever deleted; backups beyond the newest 3 the saver made are MOVED to --backups/_to_delete/.

Preview has no network code and the pipeline subprocesses run with their proxies pointed at a dead port (saver_steps.offline_env), so the one
place the pipeline can fetch (photos of new saves) cannot. The writeback bundle (O/writeback.json) is composed here and applied by the adapter;
the saver never writes a run document. Exit codes: 0 done, 2 refused (nothing written, except an already-made backup), 3 nothing queued,
4 bad arguments, 5 written but the rebuild failed, 6 written but the result or log could not be written.

Python 3.11+, pathlib, no shell-outs (subprocess only runs sys.executable on pipeline scripts)."""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import saver_diff as D       # noqa: E402
import saver_steps as S      # noqa: E402

EXIT_OK, EXIT_REFUSED, EXIT_NOTHING, EXIT_BAD, EXIT_REBUILD, EXIT_POSTWRITE = 0, 2, 3, 4, 5, 6
KEEP_BACKUPS = 3
LOCK_MINUTES = 30
TOKEN_MINUTES = 30
JUDGMENT_CAP = 200
PREVIEW_STATE = 'preview_state.json'      # what a preview leaves in its --out so a later `save --from-preview` can reuse its finished passes
PREVIEW_STATE_USED = 'preview_state.used.json'
REVIEW_CAP = 50

# prompt step 5 "Run doc review" lists (first 50 each, only the non-empty ones)
REVIEW_KEYS = ('print_pages', 'backfill_finds', 'conflicts', 'removed', 'removal_failed', 'held', 'duplicates', 'unknown_story', 'skipped',
               'pages_error', 'pages_flagged', 'reprint_check', 'reprint_failed', 'reprint_untested', 'origin_added', 'origin_wanted',
               'origin_unverified', 'outlet_unresolved', 'reach', 'gabriel_unclear', 'date_fixes', 'date_review', 'av_date_review',
               'av_date_fixes', 'av_show_to_channel', 'releases_new', 'releases_flagged', 'releases_skipped', 'releases_untestable',
               'releases_review', 'releases_unmarked', 'releases_dual', 'release_copies', 'origin_swaps', 'origin_nocopy', 'origin_merge',
               'nocopy_finds', 'print_counterpart', 'wire_blend', 'outlet_untyped', 'outlet_new', 'unverified_hits', 'placeholder_reused',
               'origin_swaps_undone', 'retry_cleared', 'nocopy_filled', 'queue_applied', 'queue_conflicts', 'yt_attached', 'yt_attach_unplaced')
# SPEC 7.3 judgment items that sheet_task already lists under the same key; the saver adds needs_fetch, name_collision,
# release_candidates_missing itself. nocopy_rows_without_copy has no key of that name in result.json: it is filled from `nocopy_finds`.
JUDGMENT_KEYS = ('origin_wanted', 'conflicts', 'date_review', 'av_date_review', 'reprint_untested', 'reprint_check', 'outlet_unresolved',
                 'outlet_new', 'outlet_untyped', 'gabriel_unclear', 'unknown_story', 'held', 'print_pages', 'backfill_finds', 'queue_conflicts',
                 'yt_attach_unplaced')


class Refuse(Exception):
    def __init__(self, code, msg, detail=None, exit_code=EXIT_REFUSED):
        super().__init__(msg)
        self.code, self.msg, self.detail, self.exit_code = code, msg, detail or {}, exit_code


# ---------------------------------------------------------------- small helpers


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(t: dt.datetime) -> str:
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_iso(s: str):
    try:
        return dt.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError):
        return None


def _us_dst(u: dt.datetime) -> bool:
    """US daylight time: from 02:00 local on the second Sunday of March to 02:00 local on the first Sunday of November"""
    y = u.year

    def nth_sunday(month, n):
        d = dt.datetime(y, month, 1)
        d += dt.timedelta(days=(6 - d.weekday()) % 7 + 7 * (n - 1))
        return d
    start = nth_sunday(3, 2) + dt.timedelta(hours=2 + 8)    # 02:00 PST expressed in UTC
    end = nth_sunday(11, 1) + dt.timedelta(hours=2 + 7)     # 02:00 PDT expressed in UTC
    return start <= u.replace(tzinfo=None) < end


def la_today() -> str:
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
    except Exception:   # no tzdata (Windows without the package): US Pacific rules computed by hand, daylight time included
        u = dt.datetime.now(dt.timezone.utc)
        return (u - (dt.timedelta(hours=7) if _us_dst(u) else dt.timedelta(hours=8))).date().isoformat()


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str) + '\n', encoding='utf-8')


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def first(lst, n):
    return list(lst or [])[:n]


# ---------------------------------------------------------------- ledger


def ledger_file(state: Path) -> Path:
    return state / 'ledger.jsonl'


def read_ledger(state: Path) -> list:
    p = ledger_file(state)
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def append_ledger(state: Path, rec: dict) -> None:
    state.mkdir(parents=True, exist_ok=True)
    with open(ledger_file(state), 'a', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        f.flush()
        os.fsync(f.fileno())


def last_recorded(entries: list):
    for e in reversed(entries):
        if e.get('verb') in ('init', 'save', 'confirm'):
            return e
    return None


# ---------------------------------------------------------------- lock (SPEC 4)


class ProcessLock:
    """S/saver.lock created with O_EXCL; younger than 30 minutes -> LOCKED, older -> moved to S/logs/stale.lock.<at> and retried once.
    Released by a move to S/logs/lock.<run>.<at> (never deleted). Every lock carries a random token: release() and check_owned() act
    only on a lock file that still holds this process's token, so a holder whose stale lock was taken over cannot release the new holder's."""

    def __init__(self, state: Path, run):
        self.state, self.run, self.path, self.held = state, run, state / 'saver.lock', False
        self.token = os.urandom(8).hex()

    def _info(self):
        try:
            return json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return None

    def _age_minutes(self):
        info = self._info()
        at = parse_iso((info or {}).get('at'))
        if at is None:
            try:
                at = dt.datetime.fromtimestamp(self.path.stat().st_mtime, dt.timezone.utc)
            except OSError:
                return None
        return (utc_now() - at).total_seconds() / 60

    def _body(self):
        return json.dumps({'pid': os.getpid(), 'run': self.run, 'at': iso(utc_now()), 'host': socket.gethostname(), 'token': self.token})

    def acquire(self):
        self.state.mkdir(parents=True, exist_ok=True)
        for attempt in (1, 2):
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                age = self._age_minutes()
                if age is not None and age < LOCK_MINUTES:
                    raise Refuse('LOCKED', f'another save was writing (lock {age:.0f} min old); ask me to save again in a few minutes.',
                                 {'lock': str(self.path), 'age_minutes': round(age, 1)})
                if attempt == 2:
                    raise Refuse('LOCKED', 'the stale lock could not be moved aside.', {'lock': str(self.path)})
                logs = self.state / 'logs'
                logs.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(self.path), str(logs / f"stale.lock.{iso(utc_now()).replace(':', '')}.{self.token}"))
                except OSError:
                    pass   # someone else moved it first; the retry decides
                continue
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(self._body())
            self.held = True
            return

    def owned(self) -> bool:
        info = self._info()
        return bool(self.held and info and info.get('token') == self.token)

    def check_owned(self):
        """call before anything that writes (backup, commit) and between long steps: the lock must still be ours"""
        if not self.owned():
            self.held = False
            raise Refuse('LOCKED', 'the process lock was taken over while this run was working; nothing more is written.', {'lock': str(self.path)})

    def refresh(self):
        """re-stamp `at` so a long step does not let the lock go stale; refuses if the lock is no longer ours"""
        self.check_owned()
        self.path.write_text(self._body(), encoding='utf-8')

    def set_run(self, run):
        self.run = run
        if self.held:
            self.refresh()

    def release(self):
        if not self.held:
            return
        self.held = False
        if not self.owned_file():
            return   # not ours any more: leave the new holder's lock alone
        logs = self.state / 'logs'
        logs.mkdir(parents=True, exist_ok=True)
        stamp = iso(utc_now()).replace(':', '')
        shutil.move(str(self.path), str(logs / f'lock.{self.run or "none"}.{stamp}'))

    def owned_file(self) -> bool:
        info = self._info()
        return bool(info and info.get('token') == self.token)


def la_stamp() -> str:
    """YYYY-MM-DD HHMM in America/Los_Angeles (backup names)"""
    try:
        from zoneinfo import ZoneInfo
        n = dt.datetime.now(ZoneInfo('America/Los_Angeles'))
    except Exception:
        u = dt.datetime.now(dt.timezone.utc)
        n = u - (dt.timedelta(hours=7) if _us_dst(u) else dt.timedelta(hours=8))
    return n.strftime('%Y-%m-%d %H%M')


def unique_path(p: Path) -> Path:
    """p if nothing is there, else 'name (2).ext', 'name (3).ext' ...: used wherever a file must never be overwritten"""
    if not p.exists():
        return p
    n = 2
    while True:
        q = p.with_name(f'{p.stem} ({n}){p.suffix}')
        if not q.exists():
            return q
        n += 1


def move_unique(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    target = unique_path(dst)
    shutil.move(str(src), str(target))
    return target


class LibLock:
    """LIB/.sheet_task.lock of the manual procedure ('<run id> <UTC time>'): written at step 2 of a save, moved to
    LIB/_to_delete/.sheet_task.lock.<run id> at the end whatever the outcome (never deleted). Only a lock holding our own text is moved."""

    def __init__(self, lib: Path, run):
        self.lib, self.run, self.path, self.text = lib, run, lib / '.sheet_task.lock', None

    def _body(self):
        return f'{self.run or "pending"} {iso(utc_now())}'

    def write(self):
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            # preview-part checks already refused a fresh lock; this one is stale (30+ minutes): set it aside, then take our own
            move_unique(self.path, self.lib / '_to_delete' / f'.sheet_task.lock.stale.{iso(utc_now()).replace(":", "")}')
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        self.text = self._body()
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(self.text)

    def ours(self) -> bool:
        try:
            return self.text is not None and self.path.read_text(encoding='utf-8') == self.text
        except OSError:
            return False

    def set_run(self, run):
        self.run = run
        if self.ours():
            self.text = self._body()
            self.path.write_text(self.text, encoding='utf-8')

    def release(self):
        if self.text is None:
            return
        ours = self.ours()
        self.text = None
        if ours:
            move_unique(self.path, self.lib / '_to_delete' / f'.sheet_task.lock.{self.run or "refresh"}')



def library_lock_check(lib: Path, keep_lock: bool) -> list:
    """the library lock of the manual procedure (read only here): a fresh one refuses (LOCKED); a stale one is noted. Returns the warnings."""
    warnings = []
    libl = lib / '.sheet_task.lock'
    if libl.is_file():
        age = (utc_now().timestamp() - libl.stat().st_mtime) / 60
        try:
            parts = libl.read_text(encoding='utf-8').split()
            t = parse_iso(parts[-1]) if parts else None
            if t:
                age = (utc_now() - t).total_seconds() / 60
        except OSError:
            pass
        if age < LOCK_MINUTES:
            raise Refuse('LOCKED', f'another save was writing (library lock {age:.0f} min old); ask me to save again in a few minutes.',
                         {'lock': str(libl)})
        warnings.append(f'stale library lock {libl.name} ({age:.0f} min old) ignored; ' +
                        ('it is set aside under _to_delete/' if keep_lock else 'preview does not move it'))
    return warnings


# ---------------------------------------------------------------- reusing a preview's finished passes (`save --from-preview`)


class NoReuse(Exception):
    """the preview in --from-preview cannot be reused; the message says why. save then runs the whole pipeline as usual."""


def saver_version() -> str:
    """a fingerprint of the save program itself (its three source files): a preview made by other code is never reused"""
    h = hashlib.sha256()
    for n in ('saver.py', 'saver_diff.py', 'saver_steps.py'):
        h.update(n.encode() + b'\0' + (Path(__file__).resolve().parent / n).read_bytes() + b'\0')
    return h.hexdigest()[:16]


def tree_sha(p) -> str:
    """sha256 over (relative path, content sha) of every file under p (a folder or one file); '' when p is None"""
    if not p:
        return ''
    p = Path(p)
    h = hashlib.sha256()
    files = [p] if p.is_file() else sorted(f for f in p.rglob('*') if f.is_file())
    for f in files:
        h.update((f.name if p.is_file() else f.relative_to(p).as_posix()).encode('utf-8') + b'\0' + S.sha256_file(f).encode() + b'\0')
    return h.hexdigest()


def stat_sha(p) -> str:
    """like tree_sha but from (relative path, size) only: for big folders the preview merely reads (copies, photo cache)"""
    if not p:
        return ''
    p = Path(p)
    h = hashlib.sha256()
    for f in sorted(f for f in p.rglob('*') if f.is_file()):
        h.update(f.relative_to(p).as_posix().encode('utf-8') + b'\0' + str(f.stat().st_size).encode() + b'\0')
    return h.hexdigest()


def cand_stamp(lib: Path, cands) -> str:
    """release candidate files the passes read from the library in place: path, size, mtime"""
    h = hashlib.sha256()
    for c in sorted(cands or []):
        f = lib / Path(*c.split('/'))
        try:
            st = f.stat()
            h.update(f'{c}\0{st.st_size}\0{st.st_mtime_ns}\0'.encode('utf-8'))
        except OSError:
            h.update(f'{c}\0missing\0'.encode('utf-8'))
    return h.hexdigest()


def reuse_inputs(a, today: str, cands, collided) -> dict:
    """everything the finished passes depend on, besides the files they leave in --out. A preview is reused only if all of it is unchanged."""
    return {'workbook': str(Path(a.workbook).resolve()), 'library': str(Path(a.library).resolve()), 'today': today,
            'run_arg': a.run or '', 'refresh': bool(a.refresh), 'source_id': getattr(a, 'source_id', None) or '',
            'pipeline_list_sha': S.sha256_file(Path(a.pipeline) / S.PIPELINE_SHA), 'saver_version': saver_version(),
            'db_sha': tree_sha(a.db), 'queue_sha': tree_sha(a.queue), 'idmap_sha': tree_sha(a.idmap), 'img_cache': stat_sha(a.img_cache),
            'copies': stat_sha(a.copies), 'candidates': cand_stamp(Path(a.library), cands), 'collided': sorted(collided),
            'env': {k: os.environ.get(k, '') for k in ('AJG_LINK_PHOTOS', 'AJG_NO_NETWORK')}}


def write_preview_state(out: Path, res: dict, ctx: dict, inputs: dict, cands) -> None:
    keys = ('run', 'today', 'out_name', 'before_sha', 'after_sha', 'pages', 'removed_files', 'token', 'rows_before', 'rows_after', 'rows_added', 'cells_filled')
    try:
        # the preview's outputs the save will use, as they are now (the pipeline copy is not among them: sheet_task updates its own copy of
        # lookup_cache.json, outlets.json ... while it runs, as it does in a full save)
        files = {'pages': tree_sha(out / 'pages'), 'writeback': S.sha256_file(out / 'writeback.json')}
        write_json(out / PREVIEW_STATE, {'format': 1, 'at': res['at'], 'inputs': inputs, 'cands': list(cands or []), 'files': files,
                                         'ctx': {k: ctx[k] for k in keys}, 'res': res})
    except OSError:
        pass       # a preview that cannot leave its state is simply not reusable


# ---------------------------------------------------------------- the preview


def build_parser():
    ap = argparse.ArgumentParser(prog='saver.py', description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='verb', required=True)

    p = sub.add_parser('init', help='seed or re-seed the checksum ledger')
    p.add_argument('--workbook', required=True)
    p.add_argument('--state', required=True)
    p.add_argument('--sha', required=True)
    p.add_argument('--note', default='')

    p = sub.add_parser('confirm', help='record that the master where it lives has the checksum of the last save')
    p.add_argument('--state', required=True)
    p.add_argument('--sha', required=True)
    p.add_argument('--note', default='')

    for verb in ('preview', 'save'):
        p = sub.add_parser(verb, help='what a save would do, writing nothing' if verb == 'preview' else
                         'run the preview steps, then back up and replace the master, add library pages, move removed files, record the checksum, rebuild')
        p.add_argument('--workbook', required=True)
        p.add_argument('--db', required=True)
        p.add_argument('--queue')
        p.add_argument('--pipeline', required=True)
        p.add_argument('--copies', required=True)
        p.add_argument('--library', required=True)
        p.add_argument('--backups', required=True)
        p.add_argument('--out', required=True)
        p.add_argument('--state')
        p.add_argument('--today')
        p.add_argument('--run')
        p.add_argument('--refresh', action='store_true')
        p.add_argument('--idmap')
        p.add_argument('--img-cache')
        p.add_argument('--json')
        p.add_argument('--source-id', help='opaque id of what the --db was made from (the update zip\'s sha256); recorded by a preview and compared by save --from-preview')
        if verb == 'save':
            p.add_argument('--from-preview', metavar='DIR', help='reuse the finished passes of the preview made in DIR (its --out) when it is still valid '
                           '(same workbook, update, pipeline, program, token, younger than 30 minutes); otherwise run everything as usual. '
                           'All of save\'s own checks (locks, Excel, checksum, backup, checked swap, ledger, library) run either way.')
            p.add_argument('--token', help='preview token; save refuses (TOKEN_STALE) unless its own fresh diff gives the same token')
            p.add_argument('--master-is-local', action='store_true', help='--workbook is the master itself: the ledger entry is confirmed at once')
            p.add_argument('--no-rebuild', action='store_true', help='skip step 14 (rebuild into OUT/site)')
    return ap


def emit(result: dict, json_path, code: int, post_commit=False) -> int:
    """write the result file, print it as the last stdout line. After the master was replaced (post_commit) a result file that cannot be
    written makes the exit code 6: the adapter must read the result from stdout."""
    result['exit_code'] = code
    try:
        if json_path:
            Path(json_path).parent.mkdir(parents=True, exist_ok=True)
            write_json(Path(json_path), result)
    except OSError as e:
        result['json_write_error'] = repr(e)[:200]
        if post_commit:
            code = result['exit_code'] = EXIT_POSTWRITE
    print(json.dumps(result, ensure_ascii=False, default=str))
    return code


def refusal_result(verb, run, today, e: Refuse) -> dict:
    line = 'Not written: ' + e.msg
    r = {'verb': verb, 'ok': False, 'run': run, 'at': iso(utc_now()), 'today': today, 'written': False, 'confirmed': False, 'line': line,
         'refusal': {'code': e.code, 'line': line, 'detail': e.detail}}
    if run:
        r['writeback'] = {'on_refusal': {'runs': {run: {'sheet': {'at': r['at'], 'written': False, 'line': line}}}}}
    return r


def sha_short(s):
    return (s or '')[:8] + '…'


def check_excel(w: Path):
    lock = w.parent / ('~$' + w.name)
    if lock.exists():
        raise Refuse('EXCEL_OPEN', 'the workbook is open in Excel. Close it and ask me to save again.', {'lock_file': str(lock)})
    try:
        if os.environ.get('SAVER_TEST_EXCEL_OPEN') == '1':   # test hook: what Windows does when Excel holds the file
            raise PermissionError('simulated')
        with open(w, 'r+b'):
            pass
    except PermissionError:
        raise Refuse('EXCEL_OPEN', 'the workbook is open in Excel. Close it and ask me to save again.', {'permission_denied': str(w)})
    except OSError as e:
        raise Refuse('BAD_ARGS', f'the workbook cannot be opened: {e!r}'[:200], {}, EXIT_BAD)


def check_identity(w: Path, state: Path) -> dict:
    entries = read_ledger(state)
    if not entries or last_recorded(entries) is None:
        raise Refuse('NO_LEDGER', f'no checksum ledger in {state}. Run saver.py init --sha <checksum of the master> first.', {'state': str(state)})
    last = last_recorded(entries)
    sha = S.sha256_file(w)
    st = w.stat()
    info = {'before_sha': sha, 'size_before': st.st_size, 'mtime_ms': int(st.st_mtime * 1000), 'expected_sha': last.get('after_sha')}
    if sha != last.get('after_sha'):
        raise Refuse('SHA_MISMATCH', f"the workbook changed since the last save (expected {sha_short(last.get('after_sha'))}, found {sha_short(sha)}). "
                     'If that is an edit of Sammy\'s own, accept the current file with saver.py init.', dict(info))
    if not last.get('confirmed'):
        raise Refuse('UNCONFIRMED_PREVIOUS', 'the last save was never confirmed where the master lives. Confirm it (saver.py confirm --sha '
                     f"{sha_short(last.get('after_sha'))}) or re-seed with init.", dict(info, last_entry=last))
    return info


def filter_db(db_arg: Path, work: Path, sheet_applied):
    """a working copy of the database in which a release item that has neither html nor text is left out (SAVE_RULES answer 4: it stays
    queued, the rest saves). Returns (db args for sheet_task, needs_fetch list). The input is never modified."""
    needs = []
    if db_arg.is_dir():
        dest = work / 'db_in'
        shutil.copytree(db_arg, dest)
        runs_dir = dest / 'runs'
        for f in sorted(runs_dir.glob('*.json')) if runs_dir.is_dir() else []:
            doc = read_json(f)
            if _strip_releases(f.stem, doc, needs, sheet_applied):
                write_json(f, doc)
        # a runs.json collection file next to the folder layout is also read by sheet_task.load_db
        rj = dest / 'runs.json'
        if rj.is_file():
            x = read_json(rj)
            docs = x if isinstance(x, dict) and not isinstance(x.get('docs') or x.get('items'), list) else None
            if docs is not None:
                changed = False
                for rid, doc in docs.items():
                    changed |= _strip_releases(rid, doc, needs, sheet_applied)
                if changed:
                    write_json(rj, docs)
        return ['--db-dir', 'db_in', '--db', 'db.json'], needs
    dest = work / 'db.json'
    db = read_json(db_arg)
    for rid, doc in (db.get('runs') or {}).items():
        _strip_releases(rid, doc, needs, sheet_applied)
    write_json(dest, db)
    return ['--db', 'db.json'], needs


def _strip_releases(rid, doc, needs, sheet_applied) -> bool:
    if not isinstance(doc, dict) or sheet_applied(doc.get('sheet')):
        return False
    keep, changed = [], False
    for x in doc.get('releases_new') or []:
        if isinstance(x, dict) and str(x.get('url', '')).startswith('http') and not (x.get('html') or x.get('text')):
            needs.append({'run': rid, 'url': x.get('url'), 'title': x.get('title')})
            changed = True
        else:
            keep.append(x)
    if changed:
        doc['releases_new'] = keep
    return changed


def pick_run(db: dict, run_arg, fns):
    runs = db.get('runs') or {}
    if run_arg:
        if run_arg not in runs:
            raise Refuse('BAD_ARGS', f'run {run_arg!r} is not in the database', {}, EXIT_BAD)
        return run_arg
    undone = [(str((d or {}).get('at') or ''), rid) for rid, d in runs.items()
              if isinstance(d, dict) and (d.get('rows') or d.get('bills_new') or d.get('releases_new')) and not fns['sheet_applied'](d.get('sheet'))]
    return max(undone)[1] if undone else None


def shard_check(work: Path, needed, copies_dir: Path):
    """--copies-needed names years by date arithmetic (+-90 days), so it can name a year the tracker has no articles for. A named shard is
    missing only if it is the manifest, or the manifest points a story at it."""
    man = copies_dir / 'articles' / 'manifest.json'
    if not man.is_file():
        return ['articles/manifest.json']
    try:
        used = set((read_json(man).get('articles') or {}).values())
    except (ValueError, AttributeError):
        return ['articles/manifest.json (unreadable)']
    return [n for n in needed if n != 'articles/manifest.json' and n in used and not (copies_dir / Path(*n.split('/'))).is_file()]


def pages_in(pages: Path):
    """relative posix paths of the library pages sheet_task wrote, by the prompt's four folders; _display/ is never committed"""
    out = []
    if not pages.is_dir():
        return out
    for p in sorted(pages.rglob('*')):
        if p.is_file():
            rel = p.relative_to(pages)
            if rel.parts[0] == '_display':
                continue
            out.append(rel.as_posix())
    return out


def ids_of_pages(result):
    out = []
    for key in ('pages', 'pages_error', 'pages_skipped'):
        out += [x.get('page') for x in result.get(key) or [] if isinstance(x, dict) and x.get('page')]
    out += [x for x in result.get('pages_drop') or [] if x]
    seen = set()
    return [x for x in out if not (x in seen or seen.add(x))]


def compose_writeback(run, result, result2, line) -> dict:
    at = result.get('at')
    runs = {}
    reprints = {}
    for rid, v in (result.get('runs') or {}).items():
        if rid == '_reprints':
            reprints = {str(k)[3:] if str(k).startswith('rp:') else str(k): val for k, val in ((v or {}).get('ids') or {}).items()}
            continue
        runs[rid] = {'ids': (v or {}).get('ids') or {},
                     'sheet': {'at': at, 'written': True, 'line': result.get('sheet_line'), 'stories': result.get('sheet_stories') or [],
                               'translations': [], 'bills': [], 'newbills': [b.get('bill') if isinstance(b, dict) else b for b in result.get('bills_new') or []]},
                     'review': {k: first(result.get(k), REVIEW_CAP) for k in REVIEW_KEYS if result.get(k)}}
    return {'apply_after_confirm': True, 'runs': runs,
            'edits_delete_or_archive': list(result.get('edits_clear') or []),
            'edits_reported': {str(x.get('id')): x.get('at') for x in result.get('edits_reported') or [] if isinstance(x, dict)},
            'reprints_aid': reprints,
            'pages_delete_or_archive': ids_of_pages(result),
            'queue_applied': {str(e.get('id')): {'at': at, 'run': e.get('run') or run, 'choice': e.get('choice'), 'done': e.get('done')}
                              for e in result.get('queue_applied') or [] if isinstance(e, dict)},
            'queue_items': (result2 or {}).get('queue_docs') or {},
            'on_refusal': {'runs': {run: {'sheet': {'at': at, 'written': False, 'line': 'Not written: <why>'}}} if run else {}}}


def photo_attempts(result) -> int:
    n = 0
    for x in result.get('pages') or []:
        ph = (x or {}).get('photos') or {}
        n += int(ph.get('fetched') or 0) + len(ph.get('failed') or [])
    return n


def run_preview(a, keep_lock=False) -> tuple:
    """Spec section 3 steps 1 to 9. Returns (result dict, exit code); raises Refuse for anything that stops the run. The process lock is
    released before returning or raising.
    keep_lock=True is the save path: the library lock file is written too, and on success the call returns (result, exit code, lock, ctx) with
    both locks still held so that save runs steps 10 to 14 under the same lock; the caller must release them. On any exception the locks are
    released here."""
    run = a.run
    today = a.today or la_today()
    w = Path(a.workbook)
    out = Path(a.out)
    state = Path(a.state) if a.state else w.parent / '.saver'
    lib, pipe, copies_src = Path(a.library), Path(a.pipeline), Path(a.copies)
    at0 = utc_now()

    # --- step 1: arguments
    try:
        dt.date.fromisoformat(today)
    except ValueError:
        raise Refuse('BAD_ARGS', f'--today {today!r} is not YYYY-MM-DD', {}, EXIT_BAD)
    if today > la_today():
        raise Refuse('BAD_ARGS', f'--today {today} is later than today in America/Los_Angeles ({la_today()})', {}, EXIT_BAD)
    for label, p, kind in (('--workbook', w, 'f'), ('--db', Path(a.db), 'e'), ('--pipeline', pipe, 'd'), ('--copies', copies_src, 'd'),
                           ('--library', lib, 'd')):
        ok = p.is_file() if kind == 'f' else (p.is_dir() if kind == 'd' else p.exists())
        if not ok:
            raise Refuse('BAD_ARGS', f'{label} {p} is not there', {}, EXIT_BAD)
    if a.queue and not Path(a.queue).is_dir():
        raise Refuse('BAD_ARGS', f'--queue {a.queue} is not a folder', {}, EXIT_BAD)
    if a.img_cache and not Path(a.img_cache).is_dir():
        raise Refuse('BAD_ARGS', f'--img-cache {a.img_cache} is not a folder', {}, EXIT_BAD)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Refuse('BAD_ARGS', f'--out {out} exists and is not empty', {}, EXIT_BAD)
    if out.resolve() == w.parent.resolve():
        raise Refuse('BAD_ARGS', '--out must not be the workbook\'s own folder', {}, EXIT_BAD)
    if not ledger_file(state).is_file():
        raise Refuse('NO_LEDGER', f'no checksum ledger in {state}. Run saver.py init --sha <checksum of the master> first.', {'state': str(state)})
    out.mkdir(parents=True, exist_ok=True)
    a._out_ready = True

    lock = ProcessLock(state, run)
    liblock = LibLock(lib, run)
    result = None
    handed_over = False
    try:
        # --- step 2: process lock; the library lock of the manual procedure (read only here)
        lock.acquire()
        warnings = library_lock_check(lib, keep_lock)
        if keep_lock:
            liblock.write()
        # --- step 3: Excel
        check_excel(w)
        # --- step 4: identity
        ident = check_identity(w, state)
        before_sha = ident['before_sha']

        # --- step 5/6: inputs (pipeline first: every script runs from the verified copy so the input folder is never written)
        try:
            pv = S.verify_pipeline(pipe)
        except FileNotFoundError:
            raise Refuse('PIPELINE_MISMATCH', f'{S.PIPELINE_SHA} is missing from {pipe}', {'pipeline': str(pipe)})
        if pv['missing'] or pv['mismatch']:
            raise Refuse('PIPELINE_MISMATCH', f"pipeline files differ from {S.PIPELINE_SHA}: missing {pv['missing'][:5]}, changed {pv['mismatch'][:5]}", pv)
        S.copy_pipeline(pipe, out / 'pipeline')
        pv2 = S.verify_pipeline(out / 'pipeline')
        if pv2['missing'] or pv2['mismatch']:
            raise Refuse('PIPELINE_MISMATCH', 'the pipeline copy differs from its list', pv2)
        st_py = out / 'pipeline' / 'sheet_task.py'
        try:
            consts = S.read_sheet_task_constants(st_py)
            fns = S.load_pure_functions(st_py)
        except (KeyError, SyntaxError, ValueError) as e:
            raise Refuse('PIPELINE_MISMATCH', f'sheet_task.py does not have the rule data the saver reads: {e}'[:300], {})
        shutil.copy2(w, out / 'in.xlsx')
        if S.sha256_file(out / 'in.xlsx') != before_sha:
            raise Refuse('SHA_MISMATCH', 'the workbook changed while it was being copied', {'before_sha': before_sha})
        logs = out / 'logs'

        db_args, needs_fetch = filter_db(Path(a.db), out, fns['sheet_applied'])
        lock.refresh()
        st = S.check_only(out, db_args, logs)
        if st.rc not in (0, 3):
            raise Refuse('BAD_ARGS', f'sheet_task --check-only failed (exit {st.rc}): {st.tail(300)}', {}, EXIT_BAD)
        db = read_json(out / 'db.json')
        run = pick_run(db, a.run, fns)
        lock.set_run(run)
        liblock.set_run(run)
        queued = S.json_of(st) or {}
        base = {'verb': 'preview', 'ok': True, 'run': run, 'at': iso(utc_now()), 'today': today, 'written': False, 'confirmed': False,
                'refusal': None, 'warnings': warnings,
                'workbook': {'path': str(w), 'before_sha': before_sha, 'after_sha': None, 'backup': None, 'out_name': None,
                             'size_before': ident['size_before'], 'size_after': None},
                'queue': {'given': bool(a.queue), 'queue_applied': 0},
                'judgment': {'needs_fetch': needs_fetch}, 'queued': queued.get('queued')}
        if st.rc == 3 and not a.refresh:
            base.update(line='Nothing new to write.', nothing_queued=True)
            base['writeback'] = {'runs': {run: {'sheet': {'at': base['at'], 'written': True, 'line': 'Nothing new to write.'}}} if run else {}}
            if keep_lock:
                handed_over = True
                return base, EXIT_NOTHING, lock, {'liblock': liblock, 'out': out, 'state': state, 'run': run}
            return base, EXIT_NOTHING

        # --- copies
        ct = S.copies_needed(out, 'db.json', logs)
        needed = S.json_of(ct) if ct.rc == 0 else None
        if not isinstance(needed, list):
            raise Refuse('BAD_ARGS', f'sheet_task --copies-needed failed: {ct.tail(300)}', {}, EXIT_BAD)
        lost = shard_check(out, needed, copies_src)
        if lost:
            raise Refuse('INPUT_MISSING', f'tracker copy files the checks read are not in --copies: {lost[:6]}', {'missing': lost, 'named': needed})
        shutil.copytree(copies_src, out / 'copies')

        # --- release candidates (library read in place; missing files are listed, not a refusal)
        rc = S.release_candidates(out, 'db.json', logs)
        cands = S.json_of(rc) if rc.rc == 0 else None
        cands = cands if isinstance(cands, list) else []
        cand_missing = [c for c in cands if not (lib / Path(*c.split('/'))).is_file()]

        # --- step 7: apply (the prompt's step 3, verbatim flags)
        if a.img_cache:
            shutil.copytree(a.img_cache, out / 'img_cache')
        q_arg = None
        if a.queue:
            shutil.copytree(a.queue, out / 'queue')
            q_arg = 'queue'
        idmap_arg = None
        if a.idmap:
            shutil.copy2(a.idmap, out / 'idmap.json')
            idmap_arg = 'idmap.json'
        (out / 'pages').mkdir()
        s1 = S.run_script(out, 'pipeline/sheet_task.py',
                          S.pass1_args(today=today, queue=q_arg, idmap=idmap_arg, library=str(lib) if cands else None,
                                       img_cache=bool(a.img_cache)), 'pass1', logs)
        if s1.rc == 2:
            res1 = read_json(out / 'result.json') if (out / 'result.json').is_file() else {}
            probs = (res1.get('verify') or {}).get('problems') or [s1.tail(300)]
            raise Refuse('VERIFY_FAILED', 'sheet_task verification failed (pass 1): ' + '; '.join(str(p) for p in probs[:5]),
                         {'pass': 1, 'verify': res1.get('verify')})
        if s1.rc != 0:
            raise Refuse('BAD_ARGS', f'sheet_task pass 1 failed (exit {s1.rc}): {s1.tail(400)}', {}, EXIT_BAD)
        result = read_json(out / 'result.json')

        lock.refresh()
        (out / 'blocks').mkdir()
        b = S.run_script(out, 'pipeline/build_data.py', S.build_data_args(), 'build_data', logs)
        if b.rc != 0:
            raise Refuse('VERIFY_FAILED' if b.rc == 2 else 'BAD_ARGS', f'build_data.py failed (exit {b.rc}): {b.tail(300)}', {'pass': 'build_data'},
                         EXIT_REFUSED if b.rc == 2 else EXIT_BAD)
        merged = S.merge_copies_out(out)
        rm_args = S.relmatch_args(result)
        relmatch_ran = False
        if rm_args:
            r = S.run_script(out, 'pipeline/relmatch.py', rm_args, 'relmatch', logs)
            if r.rc != 0:
                raise Refuse('BAD_ARGS', f'relmatch.py failed (exit {r.rc}): {r.tail(300)}', {}, EXIT_BAD)
            relmatch_ran = True
        out_name = f"{w.stem} SAVED {run or 'refresh'} {iso(utc_now()).replace('-', '').replace(':', '')}.xlsx"
        s2 = S.run_script(out, 'pipeline/sheet_task.py', S.pass2_args(today=today, out_name=out_name), 'pass2', logs)
        if s2.rc == 2:
            res2 = read_json(out / 'result2.json') if (out / 'result2.json').is_file() else {}
            probs = (res2.get('verify') or {}).get('problems') or [s2.tail(300)]
            raise Refuse('VERIFY_FAILED', 'sheet_task verification failed (pass 2): ' + '; '.join(str(p) for p in probs[:5]),
                         {'pass': 2, 'verify': res2.get('verify')})
        if s2.rc != 0:
            raise Refuse('BAD_ARGS', f'sheet_task pass 2 failed (exit {s2.rc}): {s2.tail(400)}', {}, EXIT_BAD)
        result2 = read_json(out / 'result2.json')
        out_xlsx = out / out_name
        lock.refresh()

        # --- step 8: independent diff
        rep = D.compare(out / 'in.xlsx', out_xlsx, result, result2, derived_rel=consts['VT_DERIVED_REL'], new_ok=consts['VT_NEW_OK'])
        tsv = rep.tsv_text()
        (out / 'diff.tsv').write_text(tsv, encoding='utf-8', newline='\n')
        ref = rep.refusal()
        if ref:
            raise Refuse(ref[0], ref[1], dict(ref[2], tsv=str(out / 'diff.tsv')))

        # --- step 9: compose
        after_sha = S.sha256_file(out_xlsx)
        summ = rep.summary()
        token = D.preview_token(run or '', before_sha, tsv)
        pages = pages_in(out / 'pages')
        collided = [p for p in pages if (lib / Path(*p.split('/'))).exists()]
        added = [p for p in pages if p not in collided]
        judgment = {'needs_fetch': needs_fetch,
                    'name_collision': [{'file': p} for p in collided],
                    'release_candidates_missing': cand_missing,
                    'nocopy_rows_without_copy': result.get('nocopy_finds') or []}
        for k in JUDGMENT_KEYS:
            judgment[k] = result.get(k) or []
        judgment['fetch_plan'] = {'fetch': (result.get('fetch_plan') or {}).get('fetch') or []}
        counts = {k: len(v) if isinstance(v, list) else v for k, v in judgment.items() if k != 'fetch_plan'}
        judgment = {k: (first(v, JUDGMENT_CAP) if isinstance(v, list) else v) for k, v in judgment.items()}
        review = {k: first(result.get(k), REVIEW_CAP) for k in REVIEW_KEYS if result.get(k)}
        if collided:
            review['name_collision'] = [{'file': p} for p in collided][:REVIEW_CAP]
        if needs_fetch:
            review['needs_fetch'] = needs_fetch[:REVIEW_CAP]
        fetches = photo_attempts(result)
        removed_files = [{'aid': x.get('aid'), 'files': x.get('files') or [], 'originals': x.get('originals') or []}
                         for e in result.get('removed') or [] for x in e.get('rows') or []]
        line = result.get('sheet_line') or ''
        if needs_fetch:
            line += f" {len(needs_fetch)} releases need a page fetch first and stay queued."
        wb_json = compose_writeback(run, result, result2, line)
        write_json(out / 'writeback.json', wb_json)
        pv_json = {'at': iso(utc_now()), 'run': run, 'before_sha': before_sha, 'token': token, 'valid_minutes': TOKEN_MINUTES,
                   'diff_sha': S.sha256_file(out / 'diff.tsv')}
        write_json(out / 'preview.json', pv_json)
        res = dict(base)
        res.update({
            'line': line, 'at': pv_json['at'],
            'workbook': dict(base['workbook'], after_sha=after_sha, out_name=out_name, out_path=str(out_xlsx), size_after=out_xlsx.stat().st_size),
            'diff': dict(summ, tsv=str(out / 'diff.tsv'), token=token),
            'verify': {'pass1': result.get('verify'), 'pass2': result2.get('verify')},
            'runs_processed': [k for k in (result.get('runs') or {}) if k != '_reprints'],
            'library': {'pages_added': added, 'pages_collided': collided, 'removed_moved': removed_files, 'partial': False},
            'judgment': judgment, 'judgment_counts': counts, 'review': review,
            'writeback': str(out / 'writeback.json'),
            'publish': {'copies_changed': result.get('copies_changed') or [], 'outlets_changed': bool(result.get('outlets_changed')),
                        'lookups_new': result.get('lookups_new', 0), 'bills_new': len(result.get('bills_new') or []),
                        'release_texts_changed': result.get('release_texts_changed'), 'relmatch_ran': relmatch_ran,
                        'copies_out_merged': merged},
            'fetch_plan': result.get('fetch_plan') or {'fetch': [], 'answered': {}}, 'lookups_new': result.get('lookups_new', 0),
            'photos': {'fetch_attempts_blocked_offline': fetches, 'note': 'photos not in --img-cache are dropped in the saved pages (workbook cells are unaffected)' if fetches else ''},
            'queue': {'given': bool(a.queue), 'queue_applied': len(result.get('queue_applied') or [])},
            'site_rebuilt': False,
        })
        if not a.queue and res['queue']['queue_applied']:
            raise Refuse('VERIFY_FAILED', 'queue items were applied although no --queue was given', {})
        ctx = {'liblock': liblock, 'w': w, 'lib': lib, 'backups': Path(a.backups), 'state': state, 'out': out, 'pipe': pipe, 'run': run,
               'today': today, 'out_xlsx': out_xlsx, 'out_name': out_name, 'before_sha': before_sha, 'after_sha': after_sha,
               'pages': pages, 'removed_files': removed_files, 'result': result, 'result2': result2, 'token': token,
               'rows_before': rep.rows_before.get('Coverage'), 'rows_after': rep.rows_after.get('Coverage'),
               'rows_added': summ['rows_added'].get('Coverage', 0), 'cells_filled': sum(summ['cells_filled'].values())}
        write_preview_state(out, res, ctx, reuse_inputs(a, today, cands, collided), cands)     # so a later `save --from-preview` can skip the passes
        if keep_lock:
            handed_over = True
            return res, EXIT_OK, lock, ctx
        return res, EXIT_OK
    finally:
        if not handed_over:
            for rel in (liblock.release, lock.release):
                try:
                    rel()
                except OSError:
                    pass


def cmd_preview(a) -> int:
    today = a.today or la_today()

    def jp():   # the result file goes into --out only when this invocation made (or found empty) that folder
        return a.json or (str(Path(a.out) / 'saver_result.json') if getattr(a, '_out_ready', False) else None)
    try:
        res, code = run_preview(a)
    except Refuse as e:
        return emit(refusal_result('preview', a.run, today, e), jp(), e.exit_code)
    except Exception as e:   # unreadable inputs and the like: exit 4
        res = refusal_result('preview', a.run, today, Refuse('BAD_ARGS', f'unexpected error: {e!r}'[:300], {}, EXIT_BAD))
        return emit(res, jp(), EXIT_BAD)
    _log(a, res)
    return emit(res, jp(), code)


def _log(a, res):
    state = Path(a.state) if a.state else Path(a.workbook).parent / '.saver'
    try:
        logs = state / 'logs'
        logs.mkdir(parents=True, exist_ok=True)
        (logs / f"preview-{res.get('run')}-{res['at'].replace(':', '')}.log").write_text(
            json.dumps({k: res.get(k) for k in ('run', 'at', 'today', 'line', 'diff', 'workbook')}, indent=1, default=str) + '\n', encoding='utf-8')
    except OSError:
        pass


# ---------------------------------------------------------------- the save: steps 10 to 14


def backup_name(w: Path, run) -> str:
    return f'{w.stem} BACKUP before run {run or "refresh"} {la_stamp()}.xlsx'


def saver_backup_re(w: Path):
    return re.compile(re.escape(w.stem) + r' BACKUP before run .+ (\d{4}-\d\d-\d\d \d{4})(?: \((\d+)\))?\.xlsx$')


def trim_backups(w: Path, backups: Path, state: Path, keep: int = KEEP_BACKUPS) -> list:
    """SAVE_RULES answer 5: keep the newest `keep` backups the saver made, MOVE the older ones to backups/_to_delete/ (the project never deletes).
    A backup counts as the saver's own only if its name matches the saver's pattern for this workbook AND a save entry of the ledger names it:
    the manual procedure used the same naming convention, and those files are not touched here."""
    own = {e.get('backup') for e in read_ledger(state) if e.get('verb') == 'save' and e.get('backup')}
    rx = saver_backup_re(w)
    found = []
    for f in backups.iterdir() if backups.is_dir() else []:
        m = rx.match(f.name)
        if f.is_file() and m and f.name in own:
            found.append((m.group(1), int(m.group(2) or 1), f))
    found.sort(key=lambda t: (t[0], t[1]))
    moved = []
    for _, _, f in found[:-keep] if keep else found:
        moved.append(move_unique(f, backups / '_to_delete' / f.name).name)
    return moved


def commit(job: dict, lock: ProcessLock) -> dict:
    """Steps 11 and 12 (spec section 3). `job` keys: w, out_xlsx, out_name, before_sha, after_sha, run, today, lib, backups, pages_dir, pages,
    removed_files. Raises Refuse before the master is touched (a backup already made stays, SPEC 11) or for COMMIT_FAILED after the swap.
    Returns {'backup', 'library': {...}} once the master is verified; library trouble is reported in library.partial, never raised (the master
    is not rolled back: that would be a second overwrite)."""
    w, lib = job['w'], job['lib']
    before_sha, after_sha, run = job['before_sha'], job['after_sha'], job['run']
    if job['out_name'] == w.name or not job['out_name']:
        raise Refuse('COMMIT_FAILED', 'the staged file would carry the master\'s own name. Nothing was written.', {})
    lock.check_owned()
    # nothing has been written yet: the master must still be the file the diff was made against
    pre_sha = S.sha256_file(w)
    if pre_sha != before_sha:
        raise Refuse('SHA_MISMATCH', f'the workbook changed while the save was running (expected {sha_short(before_sha)}, found {sha_short(pre_sha)}). '
                     'Nothing was written.', {'before_sha': before_sha, 'found': pre_sha})
    # step 11: backup
    backups = job['backups']
    backups.mkdir(parents=True, exist_ok=True)
    bpath = unique_path(backups / backup_name(w, run))
    try:
        shutil.copy2(w, bpath)
        bsha = S.sha256_file(bpath)
    except OSError as e:
        raise Refuse('BACKUP_FAILED', f'the backup could not be made ({e!r}). The master was not touched.'[:300], {'backup': str(bpath)})
    if bsha != before_sha:
        raise Refuse('BACKUP_FAILED', f'the backup\'s checksum ({sha_short(bsha)}) is not the master\'s ({sha_short(before_sha)}). The master was not touched.',
                     {'backup': str(bpath), 'backup_sha': bsha, 'before_sha': before_sha})
    # just before the swap: still the same file, still closed, lock still ours
    lock.check_owned()
    check_excel(w)
    now_sha = S.sha256_file(w)
    if now_sha != before_sha:
        raise Refuse('SHA_MISMATCH', f'the workbook changed while the save was running (expected {sha_short(before_sha)}, found {sha_short(now_sha)}). '
                     'The master was not touched.', {'before_sha': before_sha, 'found': now_sha, 'backup': bpath.name})
    # step 12: commit
    lock.check_owned()
    tmp = w.parent / job['out_name']
    if tmp.exists():
        raise Refuse('COMMIT_FAILED', f'{tmp.name} already exists beside the master; it is never overwritten. The master was not touched.',
                     {'staged': str(tmp), 'backup': bpath.name})
    try:
        shutil.copy2(job['out_xlsx'], tmp)
        tsha = S.sha256_file(tmp)
    except OSError as e:
        raise Refuse('COMMIT_FAILED', f'the staged workbook could not be copied beside the master ({e!r}). The master was not touched.'[:300],
                     {'backup': bpath.name})
    if tsha != after_sha:
        move_unique(tmp, job['out_xlsx'].parent / ('rejected ' + tmp.name))
        raise Refuse('COMMIT_FAILED', f'the staged copy\'s checksum ({sha_short(tsha)}) is not the output\'s ({sha_short(after_sha)}). '
                     'The master was not touched.', {'backup': bpath.name})
    try:
        os.replace(tmp, w)
    except OSError as e:
        raise Refuse('COMMIT_FAILED', f'the master could not be replaced ({e!r}). It was not changed.'[:300], {'backup': bpath.name, 'staged': str(tmp)})
    final = S.sha256_file(w)
    if final != after_sha:
        raise Refuse('COMMIT_FAILED', f'after the swap the master\'s checksum is {sha_short(final)}, not {sha_short(after_sha)}. Do not save again: '
                     f'restore from the backup "{bpath.name}" (checksum {sha_short(before_sha)}).',
                     {'backup': str(bpath), 'found_sha': final, 'expected_sha': after_sha, 'master_state': 'unverified'})
    return {'backup': bpath.name, 'backup_path': str(bpath), 'size_after': w.stat().st_size, 'library': commit_library(job)}


def commit_library(job: dict) -> dict:
    """pages add-only, then removals moved to LIB/_to_delete/. Never raises: every failure is listed and sets partial."""
    lib, run, today = job['lib'], job['run'], job['today']
    out = {'pages_added': [], 'pages_collided': [], 'pages_failed': [], 'removed_moved': [], 'removed_missing': [], 'removed_failed': [], 'partial': False}
    for rel in job['pages']:
        dst = lib / Path(*rel.split('/'))
        try:
            if dst.exists():
                out['pages_collided'].append(rel)       # SAVE_RULES answer 3: skipped and listed
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(job['pages_dir'] / Path(*rel.split('/')), dst)
            out['pages_added'].append(rel)
        except OSError as e:
            out['pages_failed'].append({'file': rel, 'error': repr(e)[:150]})
    tsv = lib / '_to_delete' / f'_moves_{today}.tsv'
    for item in job['removed_files']:
        for rel in list(item.get('files') or []) + list(item.get('originals') or []):
            src = lib / Path(*rel.split('/'))
            try:
                if not src.is_file():
                    out['removed_missing'].append({'aid': item.get('aid'), 'file': rel})
                    continue
                target = move_unique(src, lib / '_to_delete' / Path(*rel.split('/')))
                out['removed_moved'].append({'aid': item.get('aid'), 'from': rel, 'to': target.relative_to(lib).as_posix()})
                with open(tsv, 'a', encoding='utf-8', newline='\n') as f:
                    f.write('\t'.join([iso(utc_now()), str(run or 'refresh'), str(item.get('aid')), rel, target.relative_to(lib).as_posix()]) + '\n')
            except OSError as e:
                out['removed_failed'].append({'aid': item.get('aid'), 'file': rel, 'error': repr(e)[:150]})
    out['partial'] = bool(out['pages_failed'] or out['removed_failed'])
    return out


# rebuild (prompt step 6). It needs these files in the pipeline folder (the published pipeline has them; the repository's code/ folder does not).
REBUILD_NEEDS = ('tabs_data.py', 'assemble.py', 'shell.html', 'tracker.js', 'tabs')


def rebuild_site(out: Path, out_name: str, master_name: str) -> dict:
    """prompt step 6 into OUT/site/: tabs_data --only releases, assemble, data/sheet.json. Writes nothing under --pipeline or beside the master."""
    missing = [n for n in REBUILD_NEEDS if not (out / 'pipeline' / n).exists()]
    if missing:
        raise RuntimeError(f'the pipeline folder lacks {missing}, which the rebuild reads')
    logs = out / 'logs'
    for label, script, args in (('tabs_data', 'pipeline/tabs_data.py', [out_name, 'blocks', 'pipeline/tabs', '--only', 'releases']),
                                ('assemble', 'pipeline/assemble.py', ['pipeline/shell.html', 'blocks/', 'pipeline/tracker.js', 'site/index.html'])):
        if label == 'assemble':
            (out / 'site' / 'data').mkdir(parents=True, exist_ok=True)
        r = S.run_script(out, script, args, 'rebuild_' + label, logs)
        if r.rc != 0:
            raise RuntimeError(f'{script} failed (exit {r.rc}): {r.tail(300)}')
    write_json(out / 'site' / 'data' / 'sheet.json',
               {'filename': master_name, 'b64': base64.b64encode((out / out_name).read_bytes()).decode('ascii')})
    return {'index_html': str(out / 'site' / 'index.html'), 'sheet_json': str(out / 'site' / 'data' / 'sheet.json')}


def pipeline_files_changed(out: Path, pipe: Path) -> dict:
    """publish.pipeline_files: the conditional pipeline files of prompt step 7, with their shas and whether the run changed them"""
    pairs = {'lookup_cache.json': (out / 'lookup_cache.out.json', pipe / 'lookup_cache.json'),
             'outlets.json': (out / 'pipeline' / 'outlets.json', pipe / 'outlets.json'),
             'gabriel_bills_leginfo.json': (out / 'pipeline' / 'gabriel_bills_leginfo.json', pipe / 'gabriel_bills_leginfo.json'),
             'release_texts.json': (out / 'pipeline' / 'release_texts.json', pipe / 'release_texts.json'),
             'release_related.json': (out / 'pipeline' / 'release_related.json', pipe / 'release_related.json')}
    res = {}
    for name, (new, old) in pairs.items():
        if not new.is_file():
            res[name] = {'changed': False}
            continue
        ns = S.sha256_file(new)
        res[name] = {'path': str(new), 'sha': ns, 'changed': (not old.is_file()) or S.sha256_file(old) != ns}
    return res


def write_save_log(state: Path, res: dict) -> Path:
    logs = state / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    p = logs / f"save-{res.get('run') or 'refresh'}-{res['at'].replace(':', '')}.log"
    p.write_text(json.dumps({k: res.get(k) for k in ('run', 'at', 'today', 'line', 'written', 'confirmed', 'diff', 'workbook', 'library', 'refusal',
                                                      'site_rebuilt', 'rebuild_error', 'backups_moved')}, indent=1, default=str) + '\n', encoding='utf-8')
    return p


def release_all(lock, liblock):
    for rel in (liblock.release if liblock else None, lock.release if lock else None):
        if rel:
            try:
                rel()
            except OSError:
                pass


def reuse_preview(a, today: str):
    """`save --from-preview DIR` (SAVER_SPEC section 6, token window): take the preview's finished passes (sheet_task pass 1 and 2, build_data, relmatch
    and the independent diff) instead of running them again, when everything they depended on is unchanged. Returns (res, EXIT_OK, lock, ctx) like
    run_preview(keep_lock=True), working in DIR itself. Raises NoReuse (nothing held) for any reason to run the whole pipeline instead, and Refuse for
    what a full run would refuse as well (LOCKED, EXCEL_OPEN, SHA_MISMATCH ...). The locks, Excel, ledger and sha checks run here, under the lock."""
    d = Path(a.from_preview)
    sf = d / PREVIEW_STATE
    if not sf.is_file():
        raise NoReuse('that preview was already used by a save' if (d / PREVIEW_STATE_USED).is_file() else f'{d} holds no reusable preview')
    try:
        st = read_json(sf)
        pv = read_json(d / 'preview.json')
        c0, inp, res = st['ctx'], st['inputs'], st['res']
    except (OSError, ValueError, KeyError):
        raise NoReuse('the preview state is unreadable')
    if st.get('format') != 1:
        raise NoReuse('the preview state is from another format')
    w, lib, pipe = Path(a.workbook), Path(a.library), Path(a.pipeline)
    # age: the token window of SAVER_SPEC section 6, from the preview's own time stamp
    at = parse_iso(st.get('at'))
    age = (utc_now() - at).total_seconds() / 60 if at else None
    if age is None or age > TOKEN_MINUTES or age < -1:
        raise NoReuse(f'the preview is {"of unknown age" if age is None else f"{age:.0f} minutes old"} (limit {TOKEN_MINUTES})')
    # token: the caller's, the preview's, and one recomputed from the diff file kept with the preview
    if not a.token:
        raise NoReuse('no token was given')
    try:
        tsv = (d / 'diff.tsv').read_text(encoding='utf-8')
        again = D.preview_token(c0['run'] or '', c0['before_sha'], tsv)
    except OSError:
        raise NoReuse('the preview has no diff file')
    if not (a.token == c0['token'] == pv.get('token') == again):
        raise NoReuse('the token does not match the preview')
    if S.sha256_file(d / 'diff.tsv') != pv.get('diff_sha'):
        raise NoReuse('the preview\'s diff file changed')
    # the inputs the passes depended on
    now = reuse_inputs(a, today, st.get('cands'), [p for p in c0['pages'] if (lib / Path(*p.split('/'))).exists()])
    why = {'workbook': 'a different workbook file', 'library': 'a different library', 'today': 'a different date', 'run_arg': 'a different run',
           'refresh': 'a different refresh setting', 'source_id': 'the update zip changed', 'pipeline_list_sha': 'the pipeline changed',
           'saver_version': 'the save program changed', 'db_sha': 'the update\'s data changed', 'queue_sha': 'the queue changed',
           'idmap_sha': 'the id map changed', 'img_cache': 'the photo cache changed', 'copies': 'the tracker copies changed',
           'candidates': 'a release page in the library changed', 'collided': 'library files appeared or went since the preview',
           'env': 'the environment differs'}
    for k, v in inp.items():
        if now.get(k) != v:
            raise NoReuse(why.get(k, f'{k} changed'))
    try:
        pv_ = S.verify_pipeline(pipe)
    except FileNotFoundError:
        raise NoReuse('PIPELINE.sha256 is missing')
    if pv_['missing'] or pv_['mismatch']:
        raise NoReuse('pipeline files differ from their checksum list')
    out_xlsx = d / c0['out_name']
    try:
        if S.sha256_file(d / 'in.xlsx') != c0['before_sha']:
            raise NoReuse('the preview\'s copy of the workbook changed')
        if S.sha256_file(out_xlsx) != c0['after_sha']:
            raise NoReuse('the preview\'s staged workbook changed')
    except OSError:
        raise NoReuse('a file of the preview is missing')
    for need in ('writeback.json', 'result.json', 'result2.json'):
        if not (d / need).is_file():
            raise NoReuse(f'the preview has no {need}')
    if any(not (d / 'pages' / Path(*p.split('/'))).is_file() for p in c0['pages']):
        raise NoReuse('a library page of the preview is missing')
    if tree_sha(d / 'pages') != (st.get('files') or {}).get('pages') or S.sha256_file(d / 'writeback.json') != (st.get('files') or {}).get('writeback'):
        raise NoReuse('the preview\'s pages or write-back file changed')
    # under the lock, the same checks a full save makes first
    run = c0['run']
    lock = ProcessLock(Path(a.state) if a.state else w.parent / '.saver', run)
    liblock = LibLock(lib, run)
    handed = False
    try:
        lock.acquire()
        warnings = library_lock_check(lib, True)
        liblock.write()
        check_excel(w)
        ident = check_identity(w, lock.state)
        if ident['before_sha'] != c0['before_sha']:
            raise NoReuse('the workbook changed since the preview')
        lock.refresh()
        res = dict(res)
        res.update(verb='save', warnings=list(res.get('warnings') or []) + warnings,
                   reused_preview={'dir': str(d), 'preview_at': st['at'], 'age_minutes': round(age, 1),
                                   'reused': ['sheet_task pass 1', 'build_data', 'relmatch', 'sheet_task pass 2', 'independent diff'],
                                   'rechecked': ['locks', 'Excel', 'workbook checksum and ledger', 'token', 'pipeline checksums', 'inputs']})
        ctx = {k: c0[k] for k in ('run', 'today', 'out_name', 'before_sha', 'after_sha', 'pages', 'removed_files', 'token', 'rows_before',
                                  'rows_after', 'rows_added', 'cells_filled')}
        ctx.update(liblock=liblock, w=w, lib=lib, backups=Path(a.backups), state=lock.state, out=d, pipe=pipe, out_xlsx=out_xlsx)
        handed = True
        return res, EXIT_OK, lock, ctx
    finally:
        if not handed:
            release_all(lock, liblock)



def cmd_save(a) -> int:
    today = a.today or la_today()
    reused, full_reason = False, None

    def jp():
        if reused:       # the preview's own result file stays as it is
            return a.json or str(Path(a.from_preview) / 'saver_result_save.json')
        return a.json or (str(Path(a.out) / 'saver_result.json') if getattr(a, '_out_ready', False) else None)
    try:
        if getattr(a, 'from_preview', None):
            try:
                res, code, lock, ctx = reuse_preview(a, today)
                reused = True
            except NoReuse as e:
                full_reason = str(e)
        if not reused:
            res, code, lock, ctx = run_preview(a, keep_lock=True)
            if full_reason:
                res['full_run_reason'] = 'the preview was not reused: ' + full_reason
    except Refuse as e:
        r = refusal_result('save', a.run, today, e)
        if full_reason:
            r['full_run_reason'] = 'the preview was not reused: ' + full_reason
        return emit(r, jp(), e.exit_code)
    except Exception as e:
        return emit(refusal_result('save', a.run, today, Refuse('BAD_ARGS', f'unexpected error: {e!r}'[:300], {}, EXIT_BAD)), jp(), EXIT_BAD)
    liblock, out, state = ctx['liblock'], ctx['out'], ctx['state']
    res['verb'] = 'save'
    committed = False
    try:
        if code == EXIT_NOTHING:      # prompt step 1: only the "Nothing new to write." writeback; no backup, no workbook
            write_json(out / 'writeback.json', res['writeback'])
            res['writeback'] = str(out / 'writeback.json')
            _log_save(state, res)
            return emit(res, jp(), EXIT_NOTHING)
        # step 10: token (a preview's token is reproduced by save's own fresh diff, so validity is a match; no clock)
        if a.token and a.token != ctx['token']:
            raise Refuse('TOKEN_STALE', 'what a save would do now is not what the preview showed (the token differs). Run the preview again.',
                         {'given': a.token, 'now': ctx['token']})
        wbk = res['workbook']
        job = {'w': ctx['w'], 'out_xlsx': ctx['out_xlsx'], 'out_name': ctx['out_name'], 'before_sha': ctx['before_sha'], 'after_sha': ctx['after_sha'],
               'run': ctx['run'], 'today': ctx['today'], 'lib': ctx['lib'], 'backups': ctx['backups'], 'pages_dir': out / 'pages',
               'pages': ctx['pages'], 'removed_files': ctx['removed_files']}
        done = commit(job, lock)       # steps 11 and 12
        committed = True
        if reused:                     # the preview's passes belong to the workbook that was just replaced: never reusable again
            try:
                os.replace(out / PREVIEW_STATE, out / PREVIEW_STATE_USED)
            except OSError:
                pass
        at = iso(utc_now())
        rec = {'at': at, 'verb': 'save', 'run': ctx['run'], 'before_sha': ctx['before_sha'], 'after_sha': ctx['after_sha'], 'backup': done['backup'],
               'out_name': ctx['out_name'], 'rows_before': ctx['rows_before'], 'rows_after': ctx['rows_after'], 'rows_added': ctx['rows_added'],
               'cells_filled': ctx['cells_filled'], 'confirmed': bool(a.master_is_local), 'confirmed_at': at if a.master_is_local else None}
        post_error = None
        try:
            append_ledger(state, rec)  # step 13 (right after the master is verified, so a crash in the library step cannot leave it unrecorded)
        except OSError as e:
            post_error = f'ledger entry not written: {e!r}'[:200]
        res['written'] = True        # the saver's result only; the run documents' `written: true` is in writeback.json, applied by the adapter
        res['confirmed'] = bool(a.master_is_local)
        res['at'] = at
        res['workbook'] = dict(wbk, backup=done['backup'], size_after=done['size_after'])
        res['library'] = done['library']
        res['backups_moved'] = []
        try:
            res['backups_moved'] = trim_backups(ctx['w'], ctx['backups'], state)
        except OSError as e:
            res['backups_moved_error'] = repr(e)[:200]
        res['publish']['pipeline_files'] = pipeline_files_changed(out, ctx['pipe'])
        res['publish']['lookup_cache_out'] = str(out / 'lookup_cache.out.json') if (out / 'lookup_cache.out.json').is_file() else None
        if done['library']['partial']:
            res['line'] += ' LIBRARY PARTIAL: see library.pages_failed / removed_failed.'
        # step 14: rebuild
        code = EXIT_OK
        res['site_rebuilt'] = False
        if not a.no_rebuild:
            try:
                res['publish'].update(rebuild_site(out, ctx['out_name'], ctx['w'].name))
                res['site_rebuilt'] = True
            except Exception as e:
                res['rebuild_error'] = repr(e)[:400]
                res['line'] += ' The page files were not rebuilt (' + str(e)[:150] + ').'
                code = EXIT_REBUILD
        # log and result
        try:
            res['log'] = str(write_save_log(state, res))
        except OSError as e:
            post_error = (post_error or '') + f' log not written: {e!r}'[:200]
        if post_error:
            res['post_commit_error'] = post_error.strip()
            code = EXIT_POSTWRITE
        return emit(res, jp(), code, post_commit=True)
    except Refuse as e:
        r = refusal_result('save', ctx.get('run'), today, e)
        r['workbook'] = {'path': str(ctx.get('w')), 'before_sha': ctx.get('before_sha')}
        if res.get('full_run_reason'):
            r['full_run_reason'] = res['full_run_reason']
        if e.detail.get('backup'):
            r['workbook']['backup'] = Path(str(e.detail['backup'])).name
        return emit(r, jp(), e.exit_code, post_commit=committed)
    except Exception as e:
        if committed:
            res['written'] = True
            res['post_commit_error'] = repr(e)[:300]
            return emit(res, jp(), EXIT_POSTWRITE, post_commit=True)
        return emit(refusal_result('save', ctx.get('run'), today, Refuse('BAD_ARGS', f'unexpected error: {e!r}'[:300], {}, EXIT_BAD)), jp(), EXIT_BAD)
    finally:
        release_all(lock, liblock)


def _log_save(state, res):
    try:
        write_save_log(state, res)
    except OSError:
        pass


def cmd_init(a) -> int:
    state = Path(a.state)
    w = Path(a.workbook)
    sha = a.sha.lower()
    if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
        return emit({'verb': 'init', 'ok': False, 'refusal': {'code': 'BAD_ARGS', 'line': '--sha is not a sha256 hex string'}}, None, EXIT_BAD)
    now = iso(utc_now())
    rec = {'at': now, 'verb': 'init', 'workbook': w.name, 'after_sha': sha, 'note': a.note, 'confirmed': True, 'confirmed_at': now}
    if w.is_file():
        rec['file_sha_now'] = S.sha256_file(w)
        rec['matches_file'] = rec['file_sha_now'] == sha
    append_ledger(state, rec)
    return emit({'verb': 'init', 'ok': True, 'ledger': str(ledger_file(state)), 'entry': rec}, None, EXIT_OK)


def cmd_confirm(a) -> int:
    state = Path(a.state)
    entries = read_ledger(state)
    last = last_recorded(entries)
    sha = a.sha.lower()
    if last is None or last.get('confirmed') or last.get('after_sha') != sha:
        why = 'no ledger' if last is None else ('the last entry is already confirmed' if last.get('confirmed') else 'wrong file')
        return emit({'verb': 'confirm', 'ok': False, 'refusal': {'code': 'SHA_MISMATCH', 'line': f"Not confirmed: {why} (last entry after_sha "
                    f"{(last or {}).get('after_sha')}, given {sha})"}}, None, EXIT_REFUSED)
    now = iso(utc_now())
    rec = {'at': now, 'verb': 'confirm', 'after_sha': sha, 'note': a.note, 'confirmed': True, 'confirmed_at': now}
    append_ledger(state, rec)
    return emit({'verb': 'confirm', 'ok': True, 'entry': rec}, None, EXIT_OK)


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return {'init': cmd_init, 'confirm': cmd_confirm, 'preview': cmd_preview, 'save': cmd_save}[a.verb](a)


if __name__ == '__main__':
    sys.exit(main())
