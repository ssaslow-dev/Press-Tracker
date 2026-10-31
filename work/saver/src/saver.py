#!/usr/bin/env python3
"""saver.py: "save the last run to the sheet" as one program (SAVER_SPEC.md, SAVE_RULES.md).

PART 1 of the build: `init`, `confirm` and `preview`. `save` (backup, atomic swap, library moves, ledger entry, rebuild) is NOT built yet;
`save` exits 4 with a refusal-shaped result and writes nothing.

preview runs spec section 3 steps 1 to 9 and writes only under --out and --state/logs (plus the process lock in --state). It never writes
the master, its folder, the library or the backups folder. It has no network code; the pipeline subprocesses run with their proxies pointed
at a dead port (saver_steps.offline_env), so the one place the pipeline can fetch (photos of new saves) cannot.

Python 3.11+, pathlib, no shell-outs (subprocess only runs sys.executable on pipeline scripts)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import saver_diff as D       # noqa: E402
import saver_steps as S      # noqa: E402

EXIT_OK, EXIT_REFUSED, EXIT_NOTHING, EXIT_BAD = 0, 2, 3, 4
LOCK_MINUTES = 30
TOKEN_MINUTES = 30
JUDGMENT_CAP = 200
REVIEW_CAP = 50

# prompt step 5 "Run doc review" lists (first 50 each, only the non-empty ones)
REVIEW_KEYS = ('print_pages', 'backfill_finds', 'conflicts', 'removed', 'removal_failed', 'held', 'duplicates', 'unknown_story', 'skipped',
               'pages_error', 'pages_flagged', 'reprint_check', 'reprint_failed', 'reprint_untested', 'origin_added', 'origin_wanted',
               'origin_unverified', 'outlet_unresolved', 'reach', 'gabriel_unclear', 'date_fixes', 'date_review', 'av_date_review',
               'av_date_fixes', 'av_show_to_channel', 'releases_new', 'releases_flagged', 'releases_skipped', 'releases_untestable',
               'releases_review', 'releases_unmarked', 'releases_dual', 'release_copies', 'origin_swaps', 'origin_nocopy', 'origin_merge',
               'nocopy_finds', 'print_counterpart', 'wire_blend', 'outlet_untyped', 'outlet_new', 'unverified_hits', 'placeholder_reused',
               'origin_swaps_undone', 'retry_cleared', 'nocopy_filled', 'queue_applied', 'queue_conflicts')
# SPEC 7.3 judgment items that sheet_task already lists under the same key; the saver adds needs_fetch, name_collision,
# release_candidates_missing itself. nocopy_rows_without_copy has no key of that name in result.json: it is filled from `nocopy_finds`.
JUDGMENT_KEYS = ('origin_wanted', 'conflicts', 'date_review', 'av_date_review', 'reprint_untested', 'reprint_check', 'outlet_unresolved',
                 'outlet_new', 'outlet_untyped', 'gabriel_unclear', 'unknown_story', 'held', 'print_pages', 'backfill_finds', 'queue_conflicts')


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
        p = sub.add_parser(verb, help='what a save would do, writing nothing' if verb == 'preview' else 'NOT BUILT in part 1')
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
        if verb == 'save':
            p.add_argument('--token')
            p.add_argument('--master-is-local', action='store_true')
            p.add_argument('--no-rebuild', action='store_true')
    return ap


def emit(result: dict, json_path, code: int) -> int:
    result['exit_code'] = code
    try:
        if json_path:
            Path(json_path).parent.mkdir(parents=True, exist_ok=True)
            write_json(Path(json_path), result)
    except OSError as e:
        result['json_write_error'] = repr(e)[:200]
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


def run_preview(a) -> tuple:
    """returns (result dict, exit code). Raises Refuse for anything that stops the run."""
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
    result = None
    try:
        # --- step 2: process lock; the library lock of the manual procedure (read only here)
        lock.acquire()
        libl = lib / '.sheet_task.lock'
        warnings = []
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
            warnings.append(f'stale library lock {libl.name} ({age:.0f} min old) ignored; preview does not move it')
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
        return res, EXIT_OK
    finally:
        try:
            lock.release()
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


def cmd_save(a) -> int:
    e = Refuse('BAD_ARGS', 'save is not built yet (part 1 builds init, confirm and preview). Nothing was changed.', {}, EXIT_BAD)
    res = refusal_result('save', a.run, a.today or la_today(), e)
    return emit(res, a.json, EXIT_BAD)


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
