#!/usr/bin/env python3
"""take_update.py: take in an update folder (zip) on the PC (FORMAT.md sections 2 and 3).

    python3 -I take_update.py inspect --app-root APP --zip UPDATE.zip
    python3 -I take_update.py preview --app-root APP --update ID [--accept-mismatch] [--today D]
    python3 -I take_update.py save    --app-root APP --update ID --token T [--accept-mismatch] [--rebuild]
    python3 -I take_update.py init    --app-root APP        (accept the workbook as it is now as the baseline; saver init)

Data only (GOVIT-v1): the zip is checked against an allow-list (manifest.json and db/<collection>/<id>.json), size and file-count caps
and the manifest's checksums before anything is written. Saved HTML inside the JSON is never opened or run here. No network. Writes only
inside the app folder. Nothing is deleted: files that must go are moved.

Exit codes follow the saver (0 ok, 2 refused, 3 nothing queued, 4 bad arguments, 5/6 written with a follow-up problem); 7 = update zip refused,
8 = fingerprint mismatch not accepted.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import formats as F          # noqa: E402
from layout import PCLayout  # noqa: E402

EXIT_ZIP_REFUSED, EXIT_MISMATCH = 7, 8


class FingerprintMismatch(Exception):
    """The update was made from a different workbook than the one on this PC. Shown to the user; never skipped silently."""

    def __init__(self, msg, detail):
        super().__init__(msg)
        self.msg, self.detail = msg, detail


def unique_dir(parent: Path, name: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    p, n = parent / name, 1
    while p.exists():
        n += 1
        p = parent / f'{name}-{n}'
    return p


def move_unique(src: Path, dst_dir: Path, name: str | None = None) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    name = name or src.name
    dst, n = dst_dir / name, 1
    while dst.exists():
        n += 1
        dst = dst_dir / f'{Path(name).stem} ({n}){Path(name).suffix}'
    shutil.move(str(src), str(dst))
    return dst


# ---------------------------------------------------------------- inspect (verify, compare fingerprint, unpack)


def fingerprint_status(manifest_sha: str, workbook: Path) -> dict:
    cur = F.sha256_file(workbook) if workbook.is_file() else None
    if cur is None:
        return {'status': 'unknown', 'update': manifest_sha, 'current': None, 'message': 'The workbook is not where the tracker expects it, so the update cannot be compared with it.'}
    if cur == manifest_sha:
        return {'status': 'match', 'update': manifest_sha, 'current': cur, 'message': 'The update was made from this workbook.'}
    return {'status': 'mismatch', 'update': manifest_sha, 'current': cur,
            'message': ('This update was made from a different version of the workbook '
                        f'(update: {manifest_sha[:8]}..., workbook now: {cur[:8]}...). The workbook has changed since "for Update" was made '
                        '(a later save or an edit in Excel). Stories found may already be in the workbook, or may be missing from the update. '
                        'Make a new "for Update" file and run the Update station again, or accept this one knowingly.')}


def inspect_update(zip_path, layout: PCLayout) -> dict:
    """Verify and unpack. Raises formats.UpdateRefused (nothing is left in staging). On success returns
    {'update_id', 'stage', 'manifest', 'fingerprint': {...status...}, 'proceed': bool, 'runs': [...], 'files': n}."""
    zp = Path(zip_path)
    if not zp.is_file():
        raise F.UpdateRefused('NO_ZIP', f'{zp} is not a file')
    try:
        zf = zipfile.ZipFile(zp)
    except (zipfile.BadZipFile, OSError) as e:
        raise F.UpdateRefused('BAD_ZIP', f'not a readable zip file: {e}')
    with zf as z:
        infos = F.scan_zip(z, zp.stat().st_size)
        entries, man_b = {}, None
        for i in infos:
            try:
                b = F.read_entry(z, i)
            except (zipfile.BadZipFile, RuntimeError, OSError, EOFError) as e:
                raise F.UpdateRefused('BAD_ZIP', f'{i.filename!r} cannot be read: {e}')
            if i.filename == 'manifest.json':
                man_b = b
            else:
                entries[i.filename] = b
        try:
            manifest = json.loads(man_b.decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            raise F.UpdateRefused('BAD_MANIFEST', 'manifest.json is not valid JSON')
        F.check_manifest(manifest, entries)
    zsha = F.sha256_file(zp)
    update_id = F.utc_now_iso().replace(':', '').replace('-', '') + '-' + zsha[:8]
    stage = unique_dir(layout.updates / 'staging', update_id)
    update_id = stage.name
    stage.mkdir(parents=True)
    try:
        (stage / 'manifest.json').write_bytes(man_b)
        for name, b in entries.items():
            p = stage / 'db' / name if F.is_pdf_entry(name) else stage / name     # NEWSBANKPDF-v1: files/<id>.pdf -> staging/<id>/db/files/ (the saver's --db copy carries it to sheet_task)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
        (stage / 'zip_sha256.txt').write_text(zsha + '  ' + zp.name + '\n', encoding='utf-8')
    except OSError:
        move_unique(stage, layout.updates / 'rejected')
        raise
    fp = fingerprint_status(manifest['source']['workbook_sha256'], layout.workbook)
    return {'update_id': update_id, 'stage': str(stage), 'manifest': manifest, 'fingerprint': fp, 'proceed': fp['status'] == 'match',
            'runs': manifest.get('runs') or [], 'files': len(entries), 'zip_sha256': zsha}


def reject(layout: PCLayout, update_id: str) -> Path:
    """Move an unpacked update that the user turned down to updates/rejected/ (kept, never deleted)."""
    return move_unique(layout.updates / 'staging' / update_id, layout.updates / 'rejected')


# ---------------------------------------------------------------- saver calls


def find_saver(layout: PCLayout, saver=None) -> Path:
    for p in (saver, layout.saver, HERE.parent.parent / 'saver' / 'src' / 'saver.py'):
        if p and Path(p).is_file():
            return Path(p)
    raise FileNotFoundError('saver.py not found (looked in <app>/saver/ and the repository)')


def _stage(layout: PCLayout, update_id: str) -> Path:
    p = layout.updates / 'staging' / update_id
    if not (p / 'manifest.json').is_file():
        raise FileNotFoundError(f'no staged update {update_id}')
    return p


def _check_fingerprint(stage: Path, layout: PCLayout, accept_mismatch: bool) -> dict:
    m = json.loads((stage / 'manifest.json').read_text(encoding='utf-8'))
    fp = fingerprint_status(m['source']['workbook_sha256'], layout.workbook)
    if fp['status'] != 'match' and not accept_mismatch:
        raise FingerprintMismatch(fp['message'], fp)
    return fp


def _db_for_saver(layout: PCLayout, stage: Path, work: Path, include_local_edits: bool) -> Path:
    """The staged db folder is the saver's --db as it is. With include_local_edits, a composed copy adds the tracker's own pending edits
    (db/edits/*.json) that the update does not already carry."""
    if not include_local_edits:
        return stage / 'db'
    comp = work / 'db_composed'
    shutil.copytree(stage / 'db', comp)
    src = layout.db / 'edits'
    (comp / 'edits').mkdir(exist_ok=True)
    for f in sorted(src.glob('*.json')) if src.is_dir() else []:
        if not (comp / 'edits' / f.name).exists():
            shutil.copy2(f, comp / 'edits' / f.name)
    return comp


def run_saver(layout: PCLayout, verb: str, update_id: str, *, accept_mismatch=False, token=None, today=None, saver=None, rebuild=False,
              include_local_edits=False, run=None) -> dict:
    stage = _stage(layout, update_id)
    fp = _check_fingerprint(stage, layout, accept_mismatch)
    sv = find_saver(layout, saver)
    work = layout.updates / 'work' / update_id
    work.mkdir(parents=True, exist_ok=True)
    out = unique_dir(work, verb + '-1')
    dbp = _db_for_saver(layout, stage, work, include_local_edits)
    cmd = [sys.executable, '-I', str(sv), verb, '--workbook', str(layout.workbook), '--db', str(dbp), '--pipeline', str(layout.pipeline),
           '--copies', str(layout.copies), '--library', str(layout.library), '--backups', str(layout.backups), '--out', str(out),
           '--state', str(layout.state), '--json', str(out.with_name(out.name + '.result.json'))]
    if layout.queue.is_dir():
        cmd += ['--queue', str(layout.queue)]
    if today:
        cmd += ['--today', today]
    if run:
        cmd += ['--run', run]
    if verb == 'save':
        if not token:
            raise ValueError('save needs the token from the preview')
        cmd += ['--token', token, '--master-is-local']
        if not rebuild:
            cmd += ['--no-rebuild']
    layout.backups.mkdir(parents=True, exist_ok=True)
    layout.library.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {'ok': False, 'line': 'the save program gave no result', 'stderr': p.stderr[-800:], 'raw': p.stdout[-800:]}
    res['exit_code'] = p.returncode
    res['out_dir'] = str(out)
    res['fingerprint'] = fp
    res['update_id'] = update_id
    return res


def preview(layout: PCLayout, update_id: str, **kw) -> dict:
    return run_saver(layout, 'preview', update_id, **kw)


def save(layout: PCLayout, update_id: str, token: str, **kw) -> dict:
    """Run the saver's save; on exit 0, 5 or 6 (the workbook was written) merge the run documents into the local db and move the update to
    updates/done/. Any other exit leaves the update in staging."""
    res = run_saver(layout, 'save', update_id, token=token, **kw)
    if res['exit_code'] in (0, 5, 6) and res.get('written'):
        res['local_db'] = merge_into_local_db(layout, update_id, Path(res['out_dir']))
        res['done_dir'] = str(finish(layout, update_id))
    return res


# ---------------------------------------------------------------- after the save


def merge_into_local_db(layout: PCLayout, update_id: str, saver_out: Path) -> dict:
    """Make the update's run documents part of the tracker's own store, with what the save decided (ids, sheet.written), so the next
    "for Update" file carries the new searched_to. An existing different doc is moved to db/_replaced/ first. Edits the save consumed are
    moved to db/_archived/edits/."""
    stage = layout.updates / 'staging' / update_id
    wbk = {}
    wf = Path(saver_out) / 'writeback.json'
    if wf.is_file():
        wbk = json.loads(wf.read_text(encoding='utf-8'))
    merged, replaced = [], []
    stamp = F.utc_now_iso().replace(':', '').replace('-', '')
    (layout.db / 'runs').mkdir(parents=True, exist_ok=True)
    for f in sorted((stage / 'db' / 'runs').glob('*.json')):
        doc = json.loads(f.read_text(encoding='utf-8'))
        w = (wbk.get('runs') or {}).get(f.stem) or {}
        for k in ('ids', 'sheet', 'review'):
            if w.get(k) is not None:
                doc[k] = w[k]
        dest = layout.db / 'runs' / f.name
        if dest.exists():
            if json.loads(dest.read_text(encoding='utf-8')) == doc:
                continue
            replaced.append(str(move_unique(dest, layout.db / '_replaced' / 'runs', f'{f.stem}.{stamp}.json')))
        dest.write_bytes(F.dumps_pretty(doc))
        merged.append(f.stem)
    archived = []
    for eid in wbk.get('edits_delete_or_archive') or []:
        src = layout.db / 'edits' / f'{eid}.json'
        if src.is_file():
            archived.append(str(move_unique(src, layout.db / '_archived' / 'edits')))
    return {'runs_merged': merged, 'runs_replaced': replaced, 'edits_archived': archived}


def finish(layout: PCLayout, update_id: str, zip_path=None) -> Path:
    """Staging -> updates/done/ (a move)."""
    return move_unique(layout.updates / 'staging' / update_id, layout.updates / 'done')


def init_baseline(layout: PCLayout, note='', saver=None) -> dict:
    sv = find_saver(layout, saver)
    layout.state.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([sys.executable, '-I', str(sv), 'init', '--workbook', str(layout.workbook), '--state', str(layout.state),
                        '--sha', F.sha256_file(layout.workbook), '--note', note or 'accepted by take_update.py init'],
                       capture_output=True, text=True, encoding='utf-8')
    return {'exit_code': p.returncode, 'stdout': p.stdout[-400:], 'stderr': p.stderr[-400:]}


# ---------------------------------------------------------------- command line


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('verb', choices=['inspect', 'preview', 'save', 'init'])
    ap.add_argument('--app-root', required=True)
    ap.add_argument('--zip')
    ap.add_argument('--update')
    ap.add_argument('--token')
    ap.add_argument('--today')
    ap.add_argument('--saver')
    ap.add_argument('--accept-mismatch', action='store_true', help='go on although the update was made from a different workbook')
    ap.add_argument('--rebuild', action='store_true')
    ap.add_argument('--include-local-edits', action='store_true')
    a = ap.parse_args(argv)
    lay = PCLayout(a.app_root)
    try:
        if a.verb == 'init':
            r = init_baseline(lay, saver=a.saver)
            print(json.dumps(r))
            return r['exit_code']
        if a.verb == 'inspect':
            if not a.zip:
                ap.error('inspect needs --zip')
            r = inspect_update(a.zip, lay)
            r['manifest'] = {k: r['manifest'][k] for k in ('format_version', 'created_at', 'source', 'runs')}
            print(json.dumps(r))
            return 0 if r['proceed'] else EXIT_MISMATCH
        if not a.update:
            ap.error(f'{a.verb} needs --update')
        kw = dict(accept_mismatch=a.accept_mismatch, today=a.today, saver=a.saver, include_local_edits=a.include_local_edits)
        r = preview(lay, a.update, **kw) if a.verb == 'preview' else save(lay, a.update, a.token, rebuild=a.rebuild, **kw)
        print(json.dumps(r, default=str))
        return r['exit_code']
    except F.UpdateRefused as e:
        print(json.dumps({'ok': False, 'refused': e.code, 'line': e.msg}))
        return EXIT_ZIP_REFUSED
    except FingerprintMismatch as e:
        print(json.dumps({'ok': False, 'refused': 'FINGERPRINT_MISMATCH', 'line': e.msg, 'fingerprint': e.detail}))
        return EXIT_MISMATCH
    except (OSError, ValueError) as e:
        print(json.dumps({'ok': False, 'line': repr(e)[:300]}))
        return 4


if __name__ == '__main__':
    sys.exit(main())
