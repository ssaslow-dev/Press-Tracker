#!/usr/bin/env python3
"""take_update.py: take in an update folder (zip) on the PC (FORMAT.md sections 2 and 3).

    python3 -I take_update.py inspect --app-root APP --zip UPDATE.zip
    python3 -I take_update.py preview --app-root APP --update ID [--accept-mismatch] [--today D]
    python3 -I take_update.py save    --app-root APP --update ID --token T [--accept-mismatch] [--rebuild] [--no-reuse]
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
import re
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
            p = stage / 'db' / name if F.PDF_ENTRY_RE.match(name) else stage / name     # NEWSBANKPDF-v1: files/<id>.pdf -> staging/<id>/db/files/ (the saver's --db copy carries it to sheet_task)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
        # STATIONNAMES: a PDF that travels as library/... is also put where the save looks for it (db/files/<the id its pages document names>.pdf)
        for item in (manifest.get('names') or {}).get('items') or []:
            lp, pf = item.get('pdf') or (item.get('copy') if item.get('fmt') == 'nb' else ''), item.get('pdf_for') or ''
            if lp and pf:
                dst = stage / 'db' / pf
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(entries[lp])
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


def staged_zip_sha(stage: Path) -> str:
    """the sha256 of the update zip this staged update came from (written by inspect_update)"""
    try:
        return (stage / 'zip_sha256.txt').read_text(encoding='utf-8').split()[0]
    except (OSError, IndexError):
        return ''


def latest_preview_dir(work: Path):
    """the newest preview output folder of this update that still holds a reusable preview (the saver decides whether it is valid)"""
    best = None
    for d in work.glob('preview-*'):
        sf = d / 'preview_state.json'
        if sf.is_file() and (best is None or sf.stat().st_mtime_ns > best[0]):
            best = (sf.stat().st_mtime_ns, d)
    return best[1] if best else None


def run_saver(layout: PCLayout, verb: str, update_id: str, *, accept_mismatch=False, token=None, today=None, saver=None, rebuild=False,
              include_local_edits=False, run=None, reuse_preview=True) -> dict:
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
    # NOQUEUE-v1: the review queue is gone from the PC tracker; the save is never given --queue
    zsha = staged_zip_sha(stage)
    if zsha:
        cmd += ['--source-id', zsha]       # the saver records it in a preview and compares it in a save (REUSE: same update zip)
    if today:
        cmd += ['--today', today]
    if run:
        cmd += ['--run', run]
    if verb == 'save':
        if not token:
            raise ValueError('save needs the token from the preview')
        cmd += ['--token', token, '--master-is-local']
        pdir = latest_preview_dir(work) if reuse_preview else None
        if pdir:
            cmd += ['--from-preview', str(pdir)]     # the saver reuses that preview's finished passes if it is still valid, else runs them again
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
    res['out_dir'] = str((res.get('reused_preview') or {}).get('dir') or out)     # a reused save works in the preview's own folder
    res['fingerprint'] = fp
    res['update_id'] = update_id
    return res


def preview(layout: PCLayout, update_id: str, **kw) -> dict:
    res = run_saver(layout, 'preview', update_id, **kw)
    res['names'] = check_names_after(layout.updates / 'staging' / update_id, res, apply=False)
    return res


def save(layout: PCLayout, update_id: str, token: str, **kw) -> dict:
    """Run the saver's save; on exit 0, 5 or 6 (the workbook was written) merge the run documents into the local db and move the update to
    updates/done/. Any other exit leaves the update in staging."""
    res = run_saver(layout, 'save', update_id, token=token, **kw)
    if res['exit_code'] in (0, 5, 6) and res.get('written'):
        res['local_db'] = merge_into_local_db(layout, update_id, Path(res['out_dir']))
        done = finish(layout, update_id)
        res['done_dir'] = str(done)
        res['names'] = check_names_after(done, res, apply=True)
    return res


# ---------------------------------------------------------------- file names (STATIONNAMES)


def _why_renamed(exp: str, act: str) -> str:
    """Plain words for a name that changed (both are library/ paths)."""
    pe, pa = F.lib_entry(exp), F.lib_entry(act)
    if not (pe and pa):
        return 'the save gave it another name'
    me, ma = (re.fullmatch(r'(ws|nb|pq)(\d+)([or]?)(?:-(s\d+))?(?:-v\d+)?', pe.group('stem')), re.fullmatch(r'(ws|nb|pq)(\d+)([or]?)(?:-(s\d+))?(?:-v\d+)?', pa.group('stem')))
    if not (me and ma):
        return 'the save gave it another name' if pe.group('stem') != pa.group('stem') else 'the save filed it under another year'
    why = []
    if me.group(2) != ma.group(2):
        why.append(f'Article ID {me.group(2)} -> {ma.group(2)} (that number was taken first, or a find before it was not added)')
    if me.group(4) != ma.group(4):
        why.append(f'Story ID {me.group(4) or "none"} -> {ma.group(4) or "none"}')
    if me.group(3) != ma.group(3):
        why.append('o -> r: the text test found it is a reprint of an earlier story' if (me.group(3), ma.group(3)) == ('o', 'r') else f'{me.group(3) or "-"} -> {ma.group(3) or "-"}')
    if me.group(1) != ma.group(1):
        why.append(f'{me.group(1)} -> {ma.group(1)}')
    if pe.group('year') != pa.group('year'):
        why.append(f'year folder {pe.group("year")} -> {pa.group("year")} (the save dates it differently)')
    return '; '.join(why) or 'the save gave it another name'


def move_unique_path(p: Path) -> Path:
    q, n = p, 1
    while q.exists():
        n += 1
        q = p.with_name(f'{p.stem} ({n}){p.suffix}')
    return q


def reconcile_names(names: dict, base: Path, result: dict, *, apply: bool) -> dict:
    """STATIONNAMES (LIBFILES-v1 follow-up 2). The station named every file in the update; the save assigns the real Article, Story and Release IDs and writes
    the workbook's File name columns and the library files by them. Where the two differ the SAVE'S NAME WINS: the copy of the file kept with the update
    (base/library/...) is renamed to it, and every rename is listed. Nothing in the workbook or the PC library is touched here: the save already wrote those
    by its own names, so the workbook, the library and the kept update folder agree. Files the station named that the save did not write are listed as
    `not_saved`; files the save wrote that the station had not named are counted in `unnamed`.
    Returns {confirmed, renamed:[{aid, from, to, why}], not_saved:[{file, why}], unnamed:[...], lines:[...]}. With apply=False nothing is moved."""
    out = {'confirmed': 0, 'renamed': [], 'not_saved': [], 'raw_not_kept': [], 'unnamed': [], 'applied': bool(apply), 'lines': []}
    pages = {x.get('page'): x for x in (result.get('pages') or []) if isinstance(x, dict)}
    whynot = {}
    for key in ('pages_skipped', 'pages_error'):
        for x in result.get(key) or []:
            if isinstance(x, dict) and x.get('page'):
                whynot.setdefault(x['page'], x.get('why') or key)
    rels = {x.get('url'): x for x in (result.get('release_copies') or []) if isinstance(x, dict)}
    moves, named_docs = [], set()

    def judge(exp, act, who, raw=False):
        if not exp:
            return
        if (act is None or act == '') and raw:
            out['raw_not_kept'].append(exp)      # the save kept no separate raw page (cleaning changed nothing): harmless, the file stays with the update
        elif act is None or act == '':
            out['not_saved'].append({'file': exp, 'why': who})
        elif 'library/' + act == exp:
            out['confirmed'] += 1
        else:
            moves.append((exp, 'library/' + act))

    for it in (names or {}).get('items') or []:
        if not (it.get('copy') or it.get('raw') or it.get('pdf')):
            continue
        named_docs.add(it.get('doc'))
        got = pages.get(it.get('doc'))
        if got is None:
            why = whynot.get(it.get('doc')) or 'the save did not add this story (already in the workbook, skipped, or a reprint it could not place)'
            for k in ('copy', 'raw', 'pdf'):
                if it.get(k):
                    out['not_saved'].append({'file': it[k], 'why': why})
            continue
        judge(it.get('copy'), got.get('file'), 'the save did not write this file')
        judge(it.get('raw'), got.get('original'), '', raw=True)
        judge(it.get('pdf'), got.get('original_pdf'), 'the save kept no PDF for this story')
    for r in (names or {}).get('releases') or []:
        got = rels.get(r.get('url'))
        if got is None:
            for k in ('copy', 'raw'):
                if r.get(k):
                    out['not_saved'].append({'file': r[k], 'why': 'the save did not add this release (already on the Press releases tab, or it could not be read)'})
            continue
        judge(r.get('copy'), got.get('file'), 'the save wrote no copy of this release')
        judge(r.get('raw'), got.get('original'), '', raw=True)
    out['unnamed'] = sorted({x.get('file') for k, x in pages.items() if k not in named_docs and x.get('file')})
    for exp, act in moves:
        rec = {'from': exp, 'to': act, 'why': _why_renamed(exp, act)}
        m = re.search(r'/(?:ws|nb|pq|pr)(\d+)', exp)
        rec['aid'] = m.group(1) if m else ''
        out['renamed'].append(rec)
    if apply and moves:
        # two steps, so two files that swap names do not overwrite each other
        tmp = base / '.renaming'
        tmp.mkdir(parents=True, exist_ok=True)
        staged = []
        targets = {act for _, act in moves}
        for nf in out['not_saved']:             # a file the save did not write may still sit on a name the save gave to another file: set it aside, not under a made-up name
            if nf.get('file') in targets:
                held = base / Path(*nf['file'].split('/'))
                if held.is_file():
                    aside = base / 'not_saved' / Path(*nf['file'].split('/')[1:])
                    aside.parent.mkdir(parents=True, exist_ok=True)
                    held.replace(move_unique_path(aside))
        for n, (exp, act) in enumerate(moves):
            src = base / Path(*exp.split('/'))
            if src.is_file():
                t = tmp / str(n)
                src.replace(t)
                staged.append((t, act))
        for t, act in staged:
            dst = base / Path(*act.split('/'))
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                dst = unique_dir(dst.parent, dst.name)    # cannot normally happen; never overwrite
            t.replace(dst)
        try:
            tmp.rmdir()
        except OSError:
            pass
    if out['renamed']:
        seen_st, parts = set(), []
        for r in out['renamed']:                # one entry per story: a story's copy, raw page and PDF change together
            a, b = r['from'].rsplit('/', 1)[-1].rsplit('.', 1)[0], r['to'].rsplit('/', 1)[-1].rsplit('.', 1)[0]
            if (a, b) not in seen_st:
                seen_st.add((a, b)); parts.append(f"{a} -> {b} ({r['why']})")
        out['lines'].append(f"{len(out['renamed'])} file(s) renamed to the names the save gave ({len(parts)} stories/releases): " + '; '.join(parts[:12]) + (' ...' if len(parts) > 12 else ''))
    out['lines'].append(f"{out['confirmed']} file name(s) were as the station named them." + (f" {len(out['not_saved'])} named file(s) were not saved." if out['not_saved'] else ''))
    return out


def check_names_after(where: Path, res: dict, *, apply: bool) -> dict:
    """Read the manifest kept with the update (`where` = its staging or done folder) and the save program's result, compare the names."""
    try:
        man = json.loads((where / 'manifest.json').read_text(encoding='utf-8'))
        names = man.get('names')
        if not names:
            return {'present': False, 'lines': ['This update carries no station file names (an older station).']}
        rj = Path(res.get('out_dir') or '') / 'result.json'
        if not rj.is_file():
            return {'present': True, 'error': 'the save program left no result.json to compare the names with', 'lines': []}
        out = reconcile_names(names, where, json.loads(rj.read_text(encoding='utf-8')), apply=apply)
        out['present'] = True
        if apply:
            (where / 'names_result.json').write_bytes(F.dumps_pretty(out))
        return out
    except (OSError, ValueError) as e:
        return {'present': True, 'error': repr(e)[:200], 'lines': []}


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
    ap.add_argument('--no-reuse', action='store_true', help='save: run the whole pipeline again instead of reusing the preview\'s finished passes')
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
        r = preview(lay, a.update, **kw) if a.verb == 'preview' else save(lay, a.update, a.token, rebuild=a.rebuild, reuse_preview=not a.no_reuse, **kw)
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
