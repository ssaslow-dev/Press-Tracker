"""station_cli.py: the jobs behind the "Tracker files" panel. One verb per run; the last stdout line is one JSON object.

    python -B -X utf8 -I app/station/station_cli.py VERB --root ROOT [options]

Verbs: make | inspect --zip F | preview --update ID | save --update ID --token T | reject --update ID | init --sha SHA | rebuild

Wrapper around the finished pieces (APP-WRAP): updatefolder/make_for_update.py and take_update.py start their children with
`python -I` only; here their `subprocess` is replaced by a shim that adds `-B -X utf8` (UTF-8 on Windows, no .pyc written on a
share), AJG_NO_NETWORK=1 (winpack patch 02) and AJG_LINK_PHOTOS=1 (PHOTOLINK-v1: app/patches 04, 05; saved copies keep their photos as links). Temporary files go to data/tmp (inside the tracker folder). No shell, no network.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C          # noqa: E402  (also puts app/updatefolder, app/saver, app/server on sys.path)
import plain                # noqa: E402
import post_save            # noqa: E402
import refresh as R         # noqa: E402

PY_FLAGS = ['-B', '-X', 'utf8', '-I']


class _SubprocessShim:
    """stands in for `subprocess` inside take_update / make_for_update"""

    def __getattr__(self, k):
        return getattr(subprocess, k)

    def run(self, cmd, *a, **kw):
        cmd = list(cmd)
        if cmd and cmd[0] == sys.executable:
            rest = cmd[1:]
            if rest[:1] == ['-I']:
                rest = rest[1:]
            cmd = [cmd[0]] + PY_FLAGS + rest
        env = dict(kw.get('env') or os.environ)
        env['AJG_NO_NETWORK'] = '1'
        env['AJG_LINK_PHOTOS'] = '1'      # PHOTOLINK-v1: no --img-cache; the saver's photo step keeps remote <img> as links (patches 04, 05)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        kw['env'] = env
        return subprocess.run(cmd, *a, **kw)


def boot(lay):
    os.environ['AJG_NO_NETWORK'] = '1'
    os.environ['AJG_LINK_PHOTOS'] = '1'
    tmp = lay.data / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(tmp)
    import make_for_update as MFU
    import take_update as TU
    MFU.subprocess = _SubprocessShim()
    TU.subprocess = _SubprocessShim()
    return MFU, TU


def out(obj, code=0):
    print(json.dumps(obj, default=str, ensure_ascii=True))
    return code


def py(args, cwd, timeout=1800):
    return subprocess.run([sys.executable] + PY_FLAGS + [str(a) for a in args], cwd=str(cwd), capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=timeout, env=dict(os.environ, AJG_NO_NETWORK='1', AJG_LINK_PHOTOS='1', PYTHONDONTWRITEBYTECODE='1'))


# ---------------------------------------------------------------- verbs


def do_make(lay, MFU, a):
    legacy = lay.pipeline / 'legacy_index.html'
    argv = ['--app-root', str(lay.root)] + (['--legacy', str(legacy)] if legacy.is_file() else [])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = MFU.main(argv)
    try:
        res = json.loads(buf.getvalue().strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {'ok': False, 'error': 'the file maker gave no result'}
    if not res.get('ok'):
        return out({'ok': False, 'line': plain.make_failed(res)}, 1)
    p = Path(res['path'])
    return out({'ok': True, 'name': p.name, 'bytes': res['bytes'], 'stories': res['stories'], 'workbook_sha256': res['workbook_sha256'],
                'notes': res.get('notes') or [], 'line': plain.make_done(res, p.name)})


def preview_job(lay, TU, uid, accept):
    try:
        with C.AppLock(lay.state, 'preview'):
            pv = TU.preview(lay, uid, accept_mismatch=accept)
    except C.AppLockBusy as e:
        return {'ok': False, 'locked': True, 'update_id': uid, 'line': C.busy_line(e.info, e.age)}
    return plain.preview_result(pv, uid)


def already_saved(lay, runs):
    """B10 (HANDOFF_PC_APP 5): a run id the saver's ledger, the local db or a finished update already holds must not be taken in twice
    (a crash between the workbook commit and the write-back would otherwise let it be applied again and duplicate link-less rows)"""
    runs = set(runs or [])
    hit = {}
    for e in C.read_ledger(lay.state):
        if e.get('verb') == 'save' and e.get('run') in runs:
            hit[e['run']] = e.get('at')
    for r in runs:
        try:
            doc = json.loads((lay.db / 'runs' / f'{r}.json').read_text(encoding='utf-8'))
            if (doc.get('sheet') or {}).get('written'):
                hit.setdefault(r, (doc.get('sheet') or {}).get('at'))
        except (OSError, ValueError):
            pass
    done = lay.updates / 'done'
    for m in sorted(done.glob('*/manifest.json')) if done.is_dir() else []:
        try:
            for r in json.loads(m.read_text(encoding='utf-8')).get('runs') or []:
                if r in runs:
                    hit.setdefault(r, m.parent.name[:15])
        except (OSError, ValueError):
            pass
    return hit


def refuse_saved_line(hit):
    r = sorted(hit)[0]
    return (f'This update (run {r}) was already saved into the workbook ({hit[r] or "earlier"}). Taking it in a second time could add the same '
            'stories twice, so it was refused. Nothing was changed. Make a new "for Update" file and run the Update station again.')


def do_inspect(lay, TU, a):
    import formats as F
    try:
        r = TU.inspect_update(a.zip, lay)
    except F.UpdateRefused as e:
        return out({'ok': False, 'refused': e.code, 'line': plain.zip_refused(e)}, 7)
    except (OSError, ValueError) as e:
        return out({'ok': False, 'line': f'The update file could not be read: {e}'[:300]}, 4)
    hit = already_saved(lay, r['runs'])
    if hit:
        try:
            TU.reject(lay, r['update_id'])
        except OSError:
            pass
        return out({'ok': False, 'refused': 'ALREADY_SAVED', 'line': refuse_saved_line(hit)}, 7)
    res = {'ok': True, 'update_id': r['update_id'], 'fingerprint': r['fingerprint'], 'runs': r['runs'], 'files': r['files'],
           'created_at': r['manifest'].get('created_at')}
    if not r['proceed']:
        res.update(stage='needs_confirm', line=plain.fingerprint_line(r['fingerprint']))
        return out(res)
    res.update(preview_job(lay, TU, r['update_id'], False))
    res['stage'] = 'previewed' if res.get('ok') else 'refused'
    return out(res)


def do_preview(lay, TU, a):
    try:
        return out(preview_job(lay, TU, a.update, a.accept_mismatch))
    except FileNotFoundError:
        return out({'ok': False, 'line': 'That update is no longer waiting. Bring it in again.'}, 4)
    except TU.FingerprintMismatch as e:
        return out({'ok': False, 'line': plain.fingerprint_line(e.args[1] if len(e.args) > 1 else {})}, 8)


def do_save(lay, TU, a):
    try:
        mf = json.loads((lay.updates / 'staging' / a.update / 'manifest.json').read_text(encoding='utf-8'))
        hit = already_saved(lay, mf.get('runs'))
        if hit:
            return out({'ok': False, 'written': False, 'line': refuse_saved_line(hit)}, 2)
    except (OSError, ValueError):
        pass
    try:
        with C.AppLock(lay.state, 'save'):
            res = TU.save(lay, a.update, a.token, accept_mismatch=a.accept_mismatch, rebuild=True)
            if res.get('written'):
                res['sync'] = post_save.sync(lay, dict(res, update_id=a.update))
                if not res.get('site_rebuilt'):          # the saver's rebuild failed or was skipped: build the page the plain way
                    try:
                        res['page_rebuild'] = rebuild_page(lay)
                    except Exception as e:               # noqa: BLE001  (reported, never hidden)
                        res['page_rebuild'] = {'ok': False, 'error': repr(e)[:300]}
    except C.AppLockBusy as e:
        return out({'ok': False, 'locked': True, 'written': False, 'line': C.busy_line(e.info, e.age)})
    except FileNotFoundError:
        return out({'ok': False, 'written': False, 'line': 'That update is no longer waiting. Bring it in again.'}, 4)
    except TU.FingerprintMismatch as e:
        return out({'ok': False, 'written': False, 'line': plain.fingerprint_line(e.args[1] if len(e.args) > 1 else {})}, 8)
    return out(plain.save_result(res))


def do_reject(lay, TU, a):
    try:
        p = TU.reject(lay, a.update)
    except OSError as e:
        return out({'ok': False, 'line': f'Could not set the update aside: {e}'[:200]}, 4)
    return out({'ok': True, 'line': 'The update was set aside (kept in updates/rejected, not deleted). Nothing was changed.'})


def do_init(lay, TU, a):
    wb = lay.workbook
    if not wb.is_file():
        return out({'ok': False, 'line': 'The workbook is not in the data folder.'}, 4)
    if C.excel_open(wb):
        return out({'ok': False, 'line': 'Excel has the workbook open. Close it (and save if you want to keep your edits), then try again.'}, 2)
    sha = C.sha256_file(wb)
    if a.sha and a.sha != sha:
        return out({'ok': False, 'line': 'The workbook changed again while you were looking at this. Close this box and look again.'}, 2)
    try:
        with C.AppLock(lay.state, 'init'):
            r = TU.init_baseline(lay, note='accepted in the tracker on ' + socket.gethostname())
    except C.AppLockBusy as e:
        return out({'ok': False, 'locked': True, 'line': C.busy_line(e.info, e.age)})
    if r['exit_code'] != 0:
        return out({'ok': False, 'line': 'The workbook could not be accepted: ' + (r.get('stdout') or r.get('stderr') or '')[-200:]}, 2)
    return out({'ok': True, 'sha256': sha, 'line': f'Done. The tracker now treats this workbook (fingerprint {sha[:8]}) as the starting point.'})


def rebuild_page(lay) -> dict:
    """the manual procedure's step 6 without a save: build_data + assemble from the pipeline copy, exactly as build.sh's pipeline-only build"""
    import base64
    import shutil
    import saver_steps as S
    v = S.verify_pipeline(lay.pipeline)
    if v['missing'] or v['mismatch']:
        raise RuntimeError(f"the pipeline folder does not match PIPELINE.sha256 (missing {v['missing'][:3]}, changed {v['mismatch'][:3]})")
    with tempfile.TemporaryDirectory(prefix='rebuild_') as t:
        t = Path(t)
        S.copy_pipeline(lay.pipeline, t / 'pipeline')
        wb = t / 'committed.xlsx'
        shutil.copy2(lay.workbook, wb)
        sha = C.sha256_file(wb)
        if sha != C.sha256_file(lay.workbook):
            raise RuntimeError('the workbook changed while it was being copied')
        r = py(['pipeline/build_data.py', 'committed.xlsx', 'pipeline/legacy_index.html', 'blocks/', 'pipeline/sid_map.json'], t)
        if r.returncode:
            raise RuntimeError('build_data failed: ' + (r.stderr or r.stdout)[-300:])
        r = py(['pipeline/assemble.py', 'pipeline/shell.html', 'blocks/', 'pipeline/tracker.js', 'index.html'], t)
        if r.returncode:
            raise RuntimeError('assemble failed: ' + (r.stderr or r.stdout)[-300:])
        stamp = C.stamp()
        keep = lay.data / 'site_replaced' / stamp
        C.keep_old(lay.data / 'site' / 'index.html', keep)
        C.keep_old(lay.data / 'site' / 'data' / 'sheet.json', keep)
        C.atomic_copy(t / 'index.html', lay.data / 'site' / 'index.html')
        sj = json.dumps({'filename': lay.workbook.name, 'b64': base64.b64encode(wb.read_bytes()).decode('ascii')})
        C.atomic_write(lay.data / 'site' / 'data' / 'sheet.json', sj.encode('utf-8'))
        rt = lay.pipeline / 'release_texts.json'
        if rt.is_file():
            C.atomic_copy(rt, lay.data / 'site' / 'data' / 'release_texts.json')
    return {'ok': True, 'workbook_sha256': sha}


def _reader_only_line(what):
    return f'This copy of the tracker is a reader copy, so it does not {what}. Only the keeper copy does.'


def do_refresh_make(lay, TU, a):
    try:
        with C.AppLock(lay.state, 'refresh_make'):
            r = R.make(lay, full=a.full)
    except C.AppLockBusy as e:
        return out({'ok': False, 'locked': True, 'line': C.busy_line(e.info, e.age)})
    except R.RefreshRefused as e:
        return out({'ok': False, 'line': e.msg}, 2)
    kind = 'full refresh (everything, for a new person)' if r['kind'] == 'full' else 'refresh (what changed since the last one)'
    r['line'] = f'Made the {kind}: {r["name"]} ({r["bytes"] / 1e6:.1f} MB, {r["library_files"]} library files, workbook fingerprint {r["workbook_sha256"][:8]}).'
    return out(dict(r, ok=True))


def do_refresh_take(lay, TU, a):
    def init_fn(note):
        return TU.init_baseline(lay, note=note)['exit_code']
    try:
        with C.AppLock(lay.state, 'refresh_take'):
            r = R.take(lay, a.zip, init_fn)
    except C.AppLockBusy as e:
        return out({'ok': False, 'locked': True, 'line': C.busy_line(e.info, e.age)})
    except R.RefreshRefused as e:
        return out({'ok': False, 'refused': e.code, 'line': e.msg + (' Nothing was changed.' if e.code not in ('COMMIT_FAILED', 'LEDGER') else '')}, 7)
    except (OSError, zipfile.BadZipFile) as e:
        return out({'ok': False, 'line': f'The refresh file could not be read: {e}'[:300]}, 4)
    lines = [f'Workbook replaced (new fingerprint {r["workbook_sha256"][:8]}).']
    if r['backup']:
        lines.append(f'Backup of your old workbook: {r["backup"]}')
    lines.append(f'{r["library_added"]} library files added' + (f', {r["library_skipped"]} were already here' if r['library_skipped'] else '') + '.')
    lines.append(f'{r["site_files"]} page files replaced. Your notes and saved views were not touched.')
    return out(dict(r, ok=True, line=f'Refresh {r["seq"]} is in.', lines=lines))


def do_rebuild(lay, TU, a):
    try:
        with C.AppLock(lay.state, 'rebuild'):
            res = rebuild_page(lay)
    except C.AppLockBusy as e:
        return out({'ok': False, 'locked': True, 'line': C.busy_line(e.info, e.age)})
    except Exception as e:                                # noqa: BLE001
        return out({'ok': False, 'line': 'The tracker page could not be rebuilt: ' + str(e)[:300]}, 2)
    return out({'ok': True, 'line': 'The tracker page was rebuilt from the workbook as it is now.', **res})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('verb', choices=['make', 'inspect', 'preview', 'save', 'reject', 'init', 'rebuild', 'refresh_make', 'refresh_take'])
    ap.add_argument('--root', required=True)
    ap.add_argument('--zip')
    ap.add_argument('--update')
    ap.add_argument('--token')
    ap.add_argument('--sha')
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--accept-mismatch', action='store_true')
    a = ap.parse_args(argv)
    lay = C.layout(a.root)
    MFU, TU = boot(lay)
    if R.role(lay) != 'keeper' and a.verb in ('inspect', 'preview', 'save', 'reject', 'init'):
        return out({'ok': False, 'written': False, 'line': _reader_only_line('take in updates or accept the workbook')}, 2)
    try:
        return {'make': lambda: do_make(lay, MFU, a), 'inspect': lambda: do_inspect(lay, TU, a), 'preview': lambda: do_preview(lay, TU, a),
                'save': lambda: do_save(lay, TU, a), 'reject': lambda: do_reject(lay, TU, a), 'init': lambda: do_init(lay, TU, a),
                'rebuild': lambda: do_rebuild(lay, TU, a), 'refresh_make': lambda: do_refresh_make(lay, TU, a),
                'refresh_take': lambda: do_refresh_take(lay, TU, a)}[a.verb]()
    except Exception as e:                                # noqa: BLE001
        return out({'ok': False, 'line': 'Something unexpected went wrong: ' + repr(e)[:300]}, 1)


if __name__ == '__main__':
    sys.exit(main())
