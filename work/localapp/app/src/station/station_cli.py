"""station_cli.py: the jobs behind the "Tracker files" panel. One verb per run; the last stdout line is one JSON object.

    python -B -X utf8 -I app/station/station_cli.py VERB --root ROOT [options]

Verbs: make | inspect --zip F | preview --update ID | save --update ID --token T | reject --update ID | init --sha SHA | rebuild
       edits_preview | edits_save --update ID --token T   (PCEDITS-v1: only the tracker's own pending edits and removals, no update zip)
       setup_check --folder F [--list L] | setup_run --folder F [--list L] [--repairs]   (SWITCHOVER-v1: "Set up from the Mac library")

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
import re
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
import setup_mac as SM      # noqa: E402
import cell_steps as CS   # noqa: E402  (the save's rename hook)
import rename_files as RF   # noqa: E402
import article_copies as AC   # noqa: E402

PY_FLAGS = ['-B', '-X', 'utf8', '-I']
_TMP = {'dir': None}       # set by boot(): data/tmp inside the app folder


def temp_env(env):
    """GOVIT-v1: children (the save program, sheet_task, openpyxl ...) write their temporary files only inside the app folder, not %TEMP%"""
    if _TMP['dir']:
        for k in ('TMP', 'TEMP', 'TMPDIR'):
            env[k] = _TMP['dir']
    return env


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
        env['AJG_RESERVED_IDS'] = os.environ.get('AJG_RESERVED_IDS', '')
        env['AJG_LINK_PHOTOS'] = '1'      # PHOTOLINK-v1: no --img-cache; the saver's photo step keeps remote <img> as links (patches 04, 05)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        kw['env'] = temp_env(env)
        return subprocess.run(cmd, *a, **kw)


def boot(lay):
    os.environ['AJG_NO_NETWORK'] = '1'
    os.environ['AJG_LINK_PHOTOS'] = '1'
    os.environ['AJG_PRINT_LIB'] = str(lay.library)      # PRINTORIG-v1 (patch 26): build_data lists print originals found by name in the library
    os.environ['AJG_RESERVED_IDS'] = str(lay.state / 'reserved_ids.json')     # DROPUNVERIFIED-v1: patches 19 and 20 read it (a missing file changes nothing)
    tmp = lay.data / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(tmp)
    _TMP['dir'] = str(tmp)
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
                          errors='replace', timeout=timeout, env=temp_env(dict(os.environ, AJG_NO_NETWORK='1', AJG_LINK_PHOTOS='1', PYTHONDONTWRITEBYTECODE='1')))   # (os.environ already has AJG_RESERVED_IDS from boot)


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


def preview_job(lay, TU, uid, accept, edits_only=False):
    """PCEDITS-v1: the preview includes the tracker's own pending edits and removals (data/db/edits) by default"""
    try:
        with C.AppLock(lay.state, 'preview'):
            summ = TU.edits_summary(lay)
            pv = TU.preview(lay, uid, accept_mismatch=accept, edits_only=edits_only)
    except C.AppLockBusy as e:
        return {'ok': False, 'locked': True, 'update_id': uid, 'line': C.busy_line(e.info, e.age)}
    r = plain.preview_result(pv, uid, summ)
    r['edits'] = summ
    return r


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


def skip_lines(sk):
    """N16: plain sentences for the preview about a later, complete update folder whose earlier part was already saved"""
    done = sorted(sk['skipped'])
    lines = [f'This update folder replaces an earlier one that was already saved. Left out (already in the workbook, never added twice): '
             + ', '.join(f'run {x} (saved {str(sk["skipped"][x] or "earlier")[:10]})' for x in done) + '.',
             f'Taken now: {len(sk["runs"])} run(s) that were not saved yet ({", ".join(sk["runs"])}).']
    if sk.get('rebased'):
        lines.append('The workbook differs from the "for Update" file only by the earlier saves of this same update, so no fingerprint warning is needed.')
    return lines


def do_inspect(lay, TU, a):
    import formats as F
    try:
        r = TU.inspect_update(a.zip, lay)
    except F.UpdateRefused as e:
        return out({'ok': False, 'refused': e.code, 'line': plain.zip_refused(e)}, 7)
    except (OSError, ValueError) as e:
        return out({'ok': False, 'line': f'The update file could not be read: {e}'[:300]}, 4)
    hit = already_saved(lay, r['runs'])
    skipped = None
    if hit:
        mf = r['manifest']
        later = bool(mf.get('replaces')) or int(mf.get('folder_number') or 1) > 1      # N16: a later, complete folder (its earlier part was saved)
        if later and [x for x in r['runs'] if x not in hit]:
            try:
                chain = TU.chain_explains(lay, mf['source']['workbook_sha256'], r['runs'])
                sk = TU.skip_saved_runs(lay, r['update_id'], hit, chain=chain)
            except (OSError, ValueError, KeyError) as e:
                try:
                    TU.reject(lay, r['update_id'])
                except OSError:
                    pass
                return out({'ok': False, 'refused': 'ALREADY_SAVED', 'line': refuse_saved_line(hit) + f' (The new runs could not be separated: {e!s})'[:200]}, 7)
            mf = json.loads((Path(r['stage']) / 'manifest.json').read_text(encoding='utf-8'))
            r.update(manifest=mf, runs=sk['runs'], fingerprint=TU.fingerprint_status(mf['source']['workbook_sha256'], lay.workbook))
            r['proceed'] = r['fingerprint']['status'] == 'match'
            skipped = dict(sk, rebased=sk['fingerprint_rebased'])
        else:
            try:
                TU.reject(lay, r['update_id'])
            except OSError:
                pass
            return out({'ok': False, 'refused': 'ALREADY_SAVED', 'line': refuse_saved_line(hit)}, 7)
    res = {'ok': True, 'update_id': r['update_id'], 'fingerprint': r['fingerprint'], 'runs': r['runs'], 'files': r['files'],
           'created_at': r['manifest'].get('created_at')}
    if skipped:
        res['skipped_runs'] = skipped['skipped']
        res['skip_lines'] = skip_lines(skipped)
    if not r['proceed']:
        res.update(stage='needs_confirm', line=(' '.join(res.get('skip_lines') or []) + ' ' + plain.fingerprint_line(r['fingerprint'])).strip())
        return out(res)
    res.update(preview_job(lay, TU, r['update_id'], False))
    if skipped and isinstance(res.get('lines'), list):
        res['lines'] = res['skip_lines'] + res['lines']        # the preview says plainly what was left out
    res['stage'] = 'previewed' if res.get('ok') else 'refused'
    return out(res)


def do_preview(lay, TU, a):
    try:
        return out(preview_job(lay, TU, a.update, a.accept_mismatch))
    except FileNotFoundError:
        return out({'ok': False, 'line': 'That update is no longer waiting. Bring it in again.'}, 4)
    except TU.FingerprintMismatch as e:
        return out({'ok': False, 'line': plain.fingerprint_line(e.args[1] if len(e.args) > 1 else {})}, 8)


def do_edits_preview(lay, TU, a):
    """PCEDITS-v1: "Save my edits", step 1: what the tracker's own pending edits and removals would change (no update zip)"""
    n = TU.edits_summary(lay)['n']
    if not n:
        return out({'ok': True, 'can_save': False, 'headline': 'No edits waiting', 'lines': ['Nothing edited or removed in this tracker is waiting for a save.'],
                    'needs_person': [], 'token': None, 'stage': 'previewed', 'edits': TU.edits_summary(lay)})
    uid = TU.new_edits_id(lay)
    return out(preview_job(lay, TU, uid, False, edits_only=True))


def do_save(lay, TU, a):
    edits_only = getattr(a, 'edits_only', False)
    if not edits_only:
        try:
            mf = json.loads((lay.updates / 'staging' / a.update / 'manifest.json').read_text(encoding='utf-8'))
            hit = already_saved(lay, mf.get('runs'))
            if hit:
                return out({'ok': False, 'written': False, 'line': refuse_saved_line(hit)}, 2)
        except (OSError, ValueError):
            pass
    summ = {}
    try:
        with C.AppLock(lay.state, 'save'):
            summ = TU.edits_summary(lay)
            try:
                roles0 = RF.story_roles(lay.workbook)           # RENAME-v1: who has which story and role before the save
            except Exception:                                      # noqa: BLE001  (the rename pass is skipped, the save still runs)
                roles0 = None
            res = TU.save(lay, a.update, a.token, accept_mismatch=a.accept_mismatch, rebuild=True, edits_only=edits_only)
            if res.get('written'):
                res['sync'] = post_save.sync(lay, dict(res, update_id=a.update))
                if roles0 is not None and not edits_only:
                    try:                                           # RENAME-v1: files of rows whose story or role changed get the right name (nothing is deleted)
                        res['renamed_files'] = CS.auto_rename(lay, lambda note: TU.init_baseline(lay, note=note)['exit_code'], roles0)
                        if res['renamed_files'].get('renamed'):
                            res['site_rebuilt'] = False        # the workbook changed again: build the page the plain way below
                    except Exception as e:                     # noqa: BLE001  (reported, never hidden: the save itself is done)
                        res['renamed_files'] = {'error': repr(e)[:300]}
                try:                                     # A11: any saved copy the save did not put in the article data is added from the library
                    res['article_copies'] = {k: v for k, v in AC.rebuild(lay).items() if k in ('added', 'skipped', 'shards')}
                except Exception as e:                   # noqa: BLE001  (reported, never hidden: the save itself is done)
                    res['article_copies'] = {'error': repr(e)[:300]}
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
    return out(plain.save_result(res, summ))


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
            if os.environ.get('AJG_TEST_HANG') == 'refresh_make':      # tests only: a job that stops moving (the page must be told, and the job stopped)
                import time
                time.sleep(3600)
            r = R.make(lay, full=a.full)
    except C.AppLockBusy as e:
        return out({'ok': False, 'locked': True, 'line': C.busy_line(e.info, e.age)})
    except R.RefreshRefused as e:
        return out({'ok': False, 'line': e.msg}, 2)
    kind = 'full refresh (everything, for a new person)' if r['kind'] == 'full' else 'refresh (what changed since the last one)'
    if r.get('auto_full'):      # TIDY-v1: the plain button made a full one because an incremental one could not be complete
        kind = f'full refresh file, because {r["auto_full"]}'
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
    if r.get('library_deleted') or r.get('library_delete_kept'):
        lines.append(f'{r["library_deleted"]} library files removed, as the keeper deleted them (unverified reprints)'
                     + (f'; {len(r["library_delete_kept"])} kept because this copy\'s file differs from the one the keeper deleted' if r['library_delete_kept'] else '') + '.')
    lines.append(f'{r["site_files"]} page files replaced. Your notes and saved views were not touched.')
    return out(dict(r, ok=True, line=f'Refresh {r["seq"]} is in.', lines=lines))


def do_rebuild_copies(lay, TU, a):
    """Repairs: "Rebuild saved copies from the library" (A11)"""
    try:
        with C.AppLock(lay.state, 'rebuild_copies'):
            res = AC.rebuild(lay, dry_run=bool(getattr(a, 'dry_run', False)))
    except C.AppLockBusy as e:
        return out({'ok': False, 'locked': True, 'line': C.busy_line(e.info, e.age)})
    except Exception as e:                                # noqa: BLE001
        return out({'ok': False, 'line': 'The saved copies could not be rebuilt: ' + str(e)[:300]}, 2)
    res['skipped'] = [list(x) for x in res.get('skipped') or []]
    return out({'ok': True, 'line': ' '.join(AC.lines(res)) if not res.get('dry_run') else f'{res.get("would_add", 0)} saved copies would be added.', 'lines': AC.lines(res), **res})


def do_rebuild(lay, TU, a):
    try:
        with C.AppLock(lay.state, 'rebuild'):
            res = rebuild_page(lay)
    except C.AppLockBusy as e:
        return out({'ok': False, 'locked': True, 'line': C.busy_line(e.info, e.age)})
    except Exception as e:                                # noqa: BLE001
        return out({'ok': False, 'line': 'The tracker page could not be rebuilt: ' + str(e)[:300]}, 2)
    return out({'ok': True, 'line': 'The tracker page was rebuilt from the workbook as it is now.', **res})


def _show_list(l, n=3):
    return ', '.join(l[:n]) + (f' and {len(l) - n} more' if len(l) > n else '')


def do_setup_check(lay, TU, a):
    try:
        if lay.workbook.is_file():
            return out({'ok': False, 'line': 'This tracker already has a workbook. The setup is only for an empty tracker (or Repairs, "Set up again").'}, 2)
        rep = SM.check(lay, a.folder, a.list)
    except SM.SetupRefused as e:
        return out({'ok': False, 'line': e.msg, **({'check': e.detail} if e.detail else {})}, 2)
    rep = SM.public(rep)
    head = 'Everything checks out. Ready to copy.' if rep['ok'] else 'Not ready: the folder does not match the list. Nothing was copied.'
    return out({'ok': rep['ok'], 'line': head, 'lines': rep['lines'], 'check': rep, 'stage': 'checked'})


def do_setup_run(lay, TU, a):
    try:
        with C.AppLock(lay.state, 'setup'):
            r = SM.run(lay, a.folder, a.list, repairs=a.repairs)
            note = 'set up from the Mac library on ' + socket.gethostname() + ' (workbook ' + r['workbook_sha256'][:8] + ')'
            code = TU.init_baseline(lay, note=note)['exit_code']
            if code != 0:
                return out({'ok': False, 'written': True, 'line': 'The files were copied, but the tracker could not record the workbook as its starting point. Open Repairs and use "Accept the workbook as it is now".', **r}, 2)
            try:        # A11: the article data from the keeper's own library, so every saved copy opens
                ac = AC.rebuild(lay)
            except Exception as e:                  # noqa: BLE001  (reported; Repairs has "Rebuild saved copies from the library")
                ac = {'added': 0, 'skipped': [], 'error': repr(e)[:200]}
            summ = SM.summary(lay)
            summ['article_copies'] = {k: ac.get(k) for k in ('added', 'error')} | {'skipped': len(ac.get('skipped') or [])}
            log = {'at': C.utc_now().isoformat(timespec='seconds'), 'verb': 'setup', 'folder': str(a.folder), 'list': a.list, **{k: r[k] for k in ('workbook_sha256', 'files_copied', 'files_skipped_same', 'listed', 'extra', 'extra_names', 'backup')}, 'summary': summ}
            (lay.state / 'logs').mkdir(parents=True, exist_ok=True)
            (lay.state / 'logs' / f'setup-{C.stamp()}.json').write_text(json.dumps(log, indent=1), encoding='utf-8')
            try:        # REVIEW_3 finding 5: the setup log is written BEFORE the page build, so a failed build cannot hide the screen
                rebuild_page(lay)
            except Exception as e:          # noqa: BLE001
                return out({'ok': False, 'written': True, 'line': 'The files were copied and the workbook is accepted, but the page could not be built: ' + str(e)[:200]
                            + ' Open Repairs and use "Rebuild the page".', **r}, 2)
    except C.AppLockBusy as e:
        return out({'ok': False, 'locked': True, 'line': C.busy_line(e.info, e.age)})
    except SM.SetupRefused as e:
        return out({'ok': False, 'written': False, 'line': e.msg, **({'check': e.detail} if e.detail else {})}, 2)
    lines = [f'{summ["stories"]} stories in the tracker ({summ["coverage_rows"]} Coverage rows).',
             f'{r["files_copied"]} library files copied' + (f' ({r["files_skipped_same"]} were already there)' if r['files_skipped_same'] else '') + f'; {summ["library_files"]} files in the library now.',
             f'Workbook fingerprint {r["workbook_sha256"][:8]} (all {r["listed"]} files checked against the list, and again after copying).']
    if r['extra']:
        lines.append(f'{r["extra"]} files in the Mac folder were not on the list and were not copied (first: {_show_list(r["extra_names"])}).')
    if ac.get('error'):
        lines.append('The saved copies could not be added to the article data (' + ac['error'] + '). Open Repairs and use "Rebuild saved copies from the library".')
    else:
        lines += AC.lines(ac)
    if r['backup']:
        lines.append(f'The workbook that was here before is backed up as {r["backup"]}.')
    return out({'ok': True, 'written': True, 'line': 'The tracker is set up.', 'lines': lines, 'summary': summ, **r})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('verb', choices=['make', 'inspect', 'preview', 'save', 'reject', 'init', 'rebuild', 'refresh_make', 'refresh_take', 'edits_preview', 'edits_save',
                                         'setup_check', 'setup_run', 'rebuild_copies'])
    ap.add_argument('--root', required=True)
    ap.add_argument('--zip')
    ap.add_argument('--update')
    ap.add_argument('--token')
    ap.add_argument('--sha')
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--accept-mismatch', action='store_true')
    ap.add_argument('--folder')
    ap.add_argument('--list')
    ap.add_argument('--repairs', action='store_true')
    ap.add_argument('--payload')
    a = ap.parse_args(argv)
    a.edits_only = a.verb == 'edits_save'
    lay = C.layout(a.root)
    MFU, TU = boot(lay)
    try:
        post_save.recover(lay)       # a crash inside the last post-save sync must not leave the pipeline list refusing every job (REVIEW_2 finding 5)
    except Exception:       # noqa: BLE001
        pass
    if R.role(lay) != 'keeper' and a.verb in ('inspect', 'preview', 'save', 'reject', 'init', 'edits_preview', 'edits_save', 'setup_check', 'setup_run'):
        return out({'ok': False, 'written': False, 'line': _reader_only_line('take in updates, save edits, accept the workbook, set up from the Mac library or remove unverified reprints')}, 2)
    try:
        return {'make': lambda: do_make(lay, MFU, a), 'inspect': lambda: do_inspect(lay, TU, a), 'preview': lambda: do_preview(lay, TU, a),
                'save': lambda: do_save(lay, TU, a), 'edits_preview': lambda: do_edits_preview(lay, TU, a), 'edits_save': lambda: do_save(lay, TU, a), 'reject': lambda: do_reject(lay, TU, a), 'init': lambda: do_init(lay, TU, a),
                'rebuild': lambda: do_rebuild(lay, TU, a), 'refresh_make': lambda: do_refresh_make(lay, TU, a),
                'refresh_take': lambda: do_refresh_take(lay, TU, a), 'setup_check': lambda: do_setup_check(lay, TU, a),
                'setup_run': lambda: do_setup_run(lay, TU, a), 'rebuild_copies': lambda: do_rebuild_copies(lay, TU, a)}[a.verb]()
    except Exception as e:                                # noqa: BLE001
        import traceback
        where = ' | '.join(f'{Path(f.filename).name}:{f.lineno} {f.name}' for f in traceback.extract_tb(e.__traceback__)[-4:])
        files = ' '.join(str(x) for x in (getattr(e, 'filename', None), getattr(e, 'filename2', None)) if x)
        try:
            logs = lay.state / 'logs'
            logs.mkdir(parents=True, exist_ok=True)
            (logs / f'error-{a.verb}-{C.stamp()}.txt').write_text(traceback.format_exc(), encoding='utf-8')
        except Exception:                                 # noqa: BLE001
            pass
        return out({'ok': False, 'line': 'Something unexpected went wrong: ' + repr(e)[:200] + (f' (file: {files})' if files else '') + f' [at {where}]'}, 1)


if __name__ == '__main__':
    sys.exit(main())
