"""drop_unverified.py: DROPUNVERIFIED-v1. A one-time step for switch-over: the Coverage rows whose "Original or reprint" is
"Reprint (unverified)" are deleted for good (not moved to the Removed tab), with their Audio & video rows and their saved files.

    preview(lay)               -> what would go (read only), with a token
    apply(lay, token, init_fn) -> backup, staged workbook, independent check, swap, reserved ids, ledger, files; returns the result

Why it is not a normal save: a save refuses lost rows (SAVE_RULES). This step is the one allowed exception, so it is checked on its own:
  * backup first (rule 7), checksum verified; the staged workbook gets a unique name and is checked with the save program's own independent
    diff (saver_diff.compare): the ONLY differences allowed are exactly the planned Coverage and Audio & video rows missing; any other
    change to any tab, any hyperlink or the header refuses the whole step before anything is replaced;
  * the Originals tab is not touched (unverified rows are reprints); the Removed tab is not touched;
  * the Article IDs (and Story IDs) of the deleted rows stay reserved: data/state/reserved_ids.json holds floors that sheet_task (patch 19) and
    build_data (patch 20) read through AJG_RESERVED_IDS, so the next number the save assigns is above them. The file is written BEFORE the swap
    (a crash then reserves too much, never too little);
  * the saved files that belong to those rows are deleted (Sammy's explicit request: the "unless Sammy asks" case of the add-only rule), only
    inside data/library, and only when no other row of any tab names the file. Each deletion is listed in data/state/logs/drop-unverified-*.json
    (with the file's sha256), which a refresh file carries to the readers (refresh.py "deleted").
Standard library plus openpyxl (the saver's own reader is reused for the check).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import common as C

UNVERIFIED = 'reprint (unverified)'
COVERAGE, AV_TAB = 'Coverage', 'Audio & video details'
FILE_COLS = ('File name', 'File name 2', 'Transcript file')
FILE_LOOKS = re.compile(r'\.[A-Za-z0-9]{2,5}$')
SKIP_TOP = ('Press releases', '_to_delete', '_docs', 'Backups', 'Work archive', '_archive')
RESERVED_FILE = 'reserved_ids.json'


class DropRefused(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code, self.msg = code, msg


def reserved_path(lay) -> Path:
    return lay.state / RESERVED_FILE


def _s(v) -> str:
    return '' if v is None else str(v).strip()


# ---------------------------------------------------------------- reading the workbook

def _read_tabs(wb_path: Path) -> dict:
    """{tab: (header, [(row number, {column: value})])} for every tab (read only)"""
    import openpyxl
    wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=False)
    try:
        out = {}
        for ws in wb.worksheets:
            it = ws.iter_rows(values_only=True)
            hdr = [_s(h) for h in next(it, ())]
            rows = []
            for n, r in enumerate(it, start=2):
                if all(x is None or _s(x) == '' for x in r):
                    continue
                rows.append((n, {h: r[i] for i, h in enumerate(hdr) if h and i < len(r)}))
            out[ws.title] = (hdr, rows)
        return out
    finally:
        wb.close()


def _num(v) -> int:
    m = re.fullmatch(r'(?:nb-|ws-|pq-)?(\d{5})', _s(v))
    return int(m.group(1)) if m else 0


def _snum(v) -> int:
    m = re.fullmatch(r's(\d{5})', _s(v))
    return int(m.group(1)) if m else 0


def _file_names(row: dict) -> list:
    out = []
    for c in FILE_COLS:
        v = _s(row.get(c))
        if v and FILE_LOOKS.search(v) and '/' not in v and '\\' not in v:
            out.append(v)
    return out


def _library_index(lib: Path) -> dict:
    """{file name: [paths under data/library]} for the year folders, _original_html/<year>, _original_pdf/<year> (not Press releases, _to_delete ...)"""
    idx: dict = {}
    if not lib.is_dir():
        return idx
    for top in sorted(lib.iterdir()):
        if not top.is_dir() or top.name in SKIP_TOP:
            continue
        if top.name in ('_original_html', '_original_pdf'):
            dirs = [d for d in sorted(top.iterdir()) if d.is_dir() and d.name != 'Press releases']
        elif re.fullmatch(r'\d{4}', top.name):
            dirs = [top]
        else:
            continue
        for d in dirs:
            for f in d.iterdir():
                if f.is_file():
                    idx.setdefault(f.name, []).append(f)
    return idx


def plan(lay) -> dict:
    """the whole plan from the workbook as it is now (read only)"""
    wb = lay.workbook
    if not wb.is_file():
        raise DropRefused('NO_WORKBOOK', 'The workbook is not in the data folder.')
    tabs = _read_tabs(wb)
    if COVERAGE not in tabs:
        raise DropRefused('NO_COVERAGE', 'The workbook has no Coverage tab.')
    _, cov = tabs[COVERAGE]
    drop = [(n, r) for n, r in cov if _s(r.get('Original or reprint')).lower() == UNVERIFIED]
    aids = [_s(r.get('Article ID')) for _, r in drop]
    aidset = set(aids)
    av = [(n, r) for n, r in tabs.get(AV_TAB, ([], []))[1] if _s(r.get('Article ID')) in aidset]
    rows = [{'aid': _s(r.get('Article ID')), 'sid': _s(r.get('Story ID')), 'outlet': _s(r.get('Outlet')), 'headline': _s(r.get('Headline'))[:140],
             'row': n} for n, r in drop]
    # ids to keep reserved
    art = max([_num(r.get('Article ID')) for _, r in drop] + [_num(r.get('Print Article ID')) for _, r in drop] + [0])
    sto = max([_snum(r.get('Story ID')) for _, r in drop] + [0])
    # files: named in the dropped rows, or named after their Article ID (the library's schema: <nb|pq|ws><Article ID><o|r>-s<Story ID>[-vN].<ext>,
    # <Article ID>_p<page>.pdf, and an .ocr.txt beside a PDF)
    lib_idx = _library_index(lay.library)
    wanted = {}
    for _, r in drop:
        for nm in _file_names(r):
            wanted.setdefault(nm, 'named in its row')
    pats = [re.compile(r'^(?:(?:nb|pq|ws)%s[or]?(?:-s\d{5})?(?:-v\d+)?\.[A-Za-z0-9.]+|%s_p\d+\.pdf)$' % (a, a)) for a in aidset if re.fullmatch(r'\d{5}', a)]
    for nm in lib_idx:
        if any(p.match(nm) for p in pats):
            wanted.setdefault(nm, 'named after its Article ID')
    # every file name still named by a remaining row of any tab
    dropped_rows = {(COVERAGE, n) for n, _ in drop} | {(AV_TAB, n) for n, _ in av}
    held: dict = {}
    for tab, (hdr, rws) in tabs.items():
        for n, r in rws:
            if (tab, n) in dropped_rows:
                continue
            for c in r:
                if c in FILE_COLS or 'File name' in c or c == 'Transcript file':
                    v = _s(r.get(c))
                    if v:
                        held.setdefault(v, f'{tab} row {n}')
    files = []
    for nm, why in sorted(wanted.items()):
        for p in lib_idx.get(nm, []):
            rel = p.relative_to(lay.library).as_posix()
            if nm in held:
                files.append({'path': rel, 'action': 'keep', 'why': f'still named by {held[nm]}'})
            else:
                files.append({'path': rel, 'action': 'delete', 'why': why, 'bytes': p.stat().st_size})
    not_found = sorted(nm for nm in wanted if nm not in lib_idx)
    wb_sha = C.sha256_file(wb)
    tok = hashlib.sha256(json.dumps([wb_sha, sorted(aids), [f['path'] for f in files if f['action'] == 'delete']]).encode()).hexdigest()[:16]
    return {'workbook_sha256': wb_sha, 'rows': rows, 'av_rows': [{'aid': _s(r.get('Article ID')), 'row': n, 'title': _s(r.get('Episode/segment title'))[:100]}
                                                                for n, r in av],
            'article_floor': art, 'story_floor': sto, 'files': files, 'files_not_in_library': not_found, 'token': tok,
            'tab_rows': {t: len(v[1]) for t, v in tabs.items()}}


def preview(lay) -> dict:
    p = plan(lay)
    n, nav = len(p['rows']), len(p['av_rows'])
    dele = [f for f in p['files'] if f['action'] == 'delete']
    keep = [f for f in p['files'] if f['action'] == 'keep']
    lines = [f'{n} Coverage rows are "Reprint (unverified)" and would be deleted for good (not moved to the Removed tab).',
             f'{nav} Audio & video rows of the same Article IDs would go with them.',
             f'{len(dele)} saved files would be deleted from the library' + (f'; {len(keep)} would be kept because another row still names them' if keep else '') + '.',
             f'Their Article IDs (up to {p["article_floor"]:05d}) and Story IDs (up to s{p["story_floor"]:05d}) stay reserved: later saves never reuse them.',
             'Every other cell of every tab stays exactly as it is; the Originals and Removed tabs are not touched. A backup is made first.']
    p.update(ok=True, can_drop=n > 0, headline=(f'{n} unverified reprints would be removed' if n else 'No unverified reprints in the workbook'), lines=lines)
    if not n:
        p['lines'] = ['Nothing to remove: no Coverage row says "Reprint (unverified)".']
    try:
        d = lay.state / 'drop_unverified'
        d.mkdir(parents=True, exist_ok=True)
        pf = d / f'preview-{C.stamp()}.json'
        pf.write_text(json.dumps(p, indent=1), encoding='utf-8')
        p['preview_file'] = str(pf.relative_to(lay.root)).replace('/', '\\') if os.name == 'nt' else str(pf.relative_to(lay.root))
    except OSError:
        pass
    return p


# ---------------------------------------------------------------- deleting rows (one pass, links kept on their rows)

def delete_rows_batch(ws, rows) -> None:
    """The effect of sheet_task.delete_rows_keep_links on every row of `rows` (1-based), in one pass over the cells instead of one pass per row:
    the cells below move up by the number of removed rows above them, each moved cell's hyperlink ref is re-anchored to its cell, and the row
    dimensions (height, hidden flag, outline) move with their rows. (openpyxl's own delete_rows builds every empty cell of the sheet each time.)"""
    import bisect
    D = sorted(set(int(r) for r in rows))
    if not D:
        return
    new = {}
    for (r, c), cell in ws._cells.items():
        i = bisect.bisect_left(D, r)
        if i < len(D) and D[i] == r:
            continue
        nr = r - i
        if nr != r:
            cell.row = nr
        new[(nr, c)] = cell
    ws._cells = new
    dims = ws.row_dimensions
    old = {k: dims[k] for k in list(dims.keys()) if isinstance(k, int)}
    for k in list(old):
        del dims[k]
    for k, d in sorted(old.items()):
        i = bisect.bisect_left(D, k)
        if i < len(D) and D[i] == k:
            continue
        nk = k - i
        d.index = nk
        dims[nk] = d
    for cell in ws._cells.values():
        h = cell.hyperlink
        if h is not None and h.ref != cell.coordinate:
            h.ref = cell.coordinate
    ws._current_row = ws.max_row


# ---------------------------------------------------------------- apply

def _merge_reserved(lay, p, now) -> dict:
    cur = {}
    rp = reserved_path(lay)
    try:
        cur = json.loads(rp.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        cur = {}
    ids = sorted(set(str(x) for x in cur.get('article_ids') or []) | {r['aid'] for r in p['rows']})
    sids = sorted(set(str(x) for x in cur.get('story_ids') or []) | {r['sid'] for r in p['rows'] if r['sid']})
    ent = list(cur.get('entries') or []) + [{'at': now, 'verb': 'drop_unverified', 'n_rows': len(p['rows']), 'article_floor': p['article_floor'],
                                             'story_floor': p['story_floor']}]
    doc = {'format': 1, 'about': 'Numbers of rows deleted for good. The next Article ID / Story ID is always above these floors (sheet_task patch 19, build_data patch 20).',
           'article_floor': max(int(cur.get('article_floor') or 0), p['article_floor']), 'story_floor': max(int(cur.get('story_floor') or 0), p['story_floor']),
           'article_ids': ids, 'story_ids': sids, 'entries': ent}
    C.atomic_write(rp, json.dumps(doc, indent=1).encode('utf-8'))
    return doc


def _check_staged(lay, before: Path, after: Path, p: dict) -> list:
    """the independent check: the only differences between the master and the staged file are the planned rows missing. Returns the problems."""
    import saver_diff as D
    import saver_steps as SS
    consts = SS.read_sheet_task_constants(lay.pipeline / 'sheet_task.py')
    rep = D.compare(before, after, None, None, derived_rel=consts['VT_DERIVED_REL'], new_ok=consts['VT_NEW_OK'])
    want = {(COVERAGE, r['aid']) for r in p['rows']} | {(AV_TAB, r['aid']) for r in p['av_rows']}
    want_n = {}
    for t, a in [(COVERAGE, r['aid']) for r in p['rows']] + [(AV_TAB, r['aid']) for r in p['av_rows']]:
        want_n[(t, a)] = want_n.get((t, a), 0) + 1
    got_n, bad = {}, []
    for c in rep.changes:
        a = c.key.split('#')[0]
        if c.kind == 'missing' and c.sheet in (COVERAGE, AV_TAB) and (c.sheet, a) in want:
            got_n[(c.sheet, a)] = got_n.get((c.sheet, a), 0) + 1
        else:
            bad.append(f'{c.sheet} row {c.row} {c.key} {c.column}: {c.kind}')
    for pr in rep.problems:
        if not (pr.kind == 'row_missing' and any(pr.text.startswith(f'{t}: row missing after: {a}') for (t, a) in want)):
            bad.append(f'{pr.code} {pr.text}'[:200])
    if got_n != want_n:
        bad.append(f'the rows missing are not exactly the planned ones (planned {sum(want_n.values())}, missing {sum(got_n.values())})')
    for t in set(rep.rows_before) | set(rep.rows_after):
        exp = rep.rows_before.get(t, 0) - sum(v for (tt, _), v in want_n.items() if tt == t)
        if rep.rows_after.get(t) != exp:
            bad.append(f'{t}: {rep.rows_after.get(t)} rows after, expected {exp}')
    if rep.sheets_before != rep.sheets_after:
        bad.append('the tabs changed')
    return bad[:30]


def apply(lay, token: str, init_fn, shared_backup=None) -> dict:
    """init_fn(note) -> exit code: re-seeds the saver ledger with the new workbook (the ledger's own `init`)."""
    wb = lay.workbook
    if not wb.is_file():
        raise DropRefused('NO_WORKBOOK', 'The workbook is not in the data folder.')
    if C.excel_open(wb):
        raise DropRefused('EXCEL_OPEN', 'Excel has the workbook open. Close it, then try again. Nothing was changed.')
    if (lay.state / 'saver.lock').exists():
        raise DropRefused('LOCKED', 'A save is running (or was cut off). Wait for it, then try again. Nothing was changed.')
    ws0 = C.workbook_state(lay)
    if ws0.get('baseline') != 'ok':
        raise DropRefused('BASELINE', 'The workbook is not the one the tracker last saved or accepted. Use "Accept the workbook as it is now" (Repairs) first. Nothing was changed.')
    p = plan(lay)
    if not p['rows']:
        raise DropRefused('NOTHING', 'There are no unverified reprints to remove. Nothing was changed.')
    if p['token'] != token:
        raise DropRefused('CHANGED', 'The workbook or the list changed since you looked. Press "Remove unverified reprints" again to see the current list. Nothing was changed.')
    stamp = C.stamp()
    before_sha = p['workbook_sha256']
    # 1. backup (rule 7)
    if shared_backup is not None:       # the Switch-over changes screen made the one backup of the whole session (switchover.py)
        bk = Path(shared_backup)
    else:
        lay.backups.mkdir(parents=True, exist_ok=True)
        bk = lay.backups / f'{wb.stem} BACKUP before drop_unverified {stamp}.xlsx'
        n = 2
        while bk.exists():
            bk = bk.with_name(f'{bk.stem} ({n}){bk.suffix}')
            n += 1
        shutil.copy2(wb, bk)
        if C.sha256_file(bk) != before_sha:
            raise DropRefused('BACKUP_FAILED', 'The backup could not be made correctly, so nothing was changed.')
    # 2. the staged workbook (unique name, the app's own temp folder on the same drive)
    import openpyxl
    tmpd = lay.data / 'tmp'
    tmpd.mkdir(parents=True, exist_ok=True)
    staged = tmpd / f'{wb.stem} STAGED drop_unverified {stamp}.xlsx'
    book = openpyxl.load_workbook(wb)
    try:
        hdr = {_s(c.value): i + 1 for i, c in enumerate(book[COVERAGE][1]) if c.value}
        del_rows = [r['row'] for r in p['rows']]
        # the planned row numbers come from the read-only pass; make sure the same rows are where the plan says
        for r in p['rows']:
            ws = book[COVERAGE]
            if _s(ws.cell(r['row'], hdr['Article ID']).value) != r['aid'] or _s(ws.cell(r['row'], hdr['Original or reprint']).value).lower() != UNVERIFIED:
                raise DropRefused('ROWS_MOVED', f'Coverage row {r["row"]} is not where the list says. Nothing was changed.')
        delete_rows_batch(book[COVERAGE], del_rows)
        if AV_TAB in book.sheetnames and p['av_rows']:
            ahdr = {_s(c.value): i + 1 for i, c in enumerate(book[AV_TAB][1]) if c.value}
            for r in p['av_rows']:
                if _s(book[AV_TAB].cell(r['row'], ahdr['Article ID']).value) != r['aid']:
                    raise DropRefused('ROWS_MOVED', f'Audio & video row {r["row"]} is not where the list says. Nothing was changed.')
            delete_rows_batch(book[AV_TAB], [r['row'] for r in p['av_rows']])
        book.save(staged)
    finally:
        book.close()
    # 3. the independent check of the staged file against the master
    bad = _check_staged(lay, wb, staged, p)
    if bad:
        staged.unlink(missing_ok=True)
        raise DropRefused('VERIFY_FAILED', 'The staged workbook differs from the master in more than the planned rows, so nothing was changed. First difference: ' + bad[0])
    after_sha = C.sha256_file(staged)
    # 4. reserve the numbers BEFORE the swap
    res_doc = _merge_reserved(lay, p, C.utc_now().isoformat(timespec='seconds'))
    # 5. re-check, checked swap
    if C.excel_open(wb) or C.sha256_file(wb) != before_sha:
        staged.unlink(missing_ok=True)
        raise DropRefused('CHANGED', 'The workbook changed or Excel opened it while the step was running. Nothing was changed.')
    try:
        os.replace(staged, wb)
    except PermissionError:
        staged.unlink(missing_ok=True)
        raise DropRefused('EXCEL_OPEN', 'The workbook is in use (Excel or a virus scanner has it). Close Excel, wait a moment, then try again. Nothing was changed.')
    if C.sha256_file(wb) != after_sha:
        raise DropRefused('COMMIT_FAILED', f'The new workbook did not check out after it was written. The backup is {bk.name}. Tell Claude; do not save.')
    # 6. ledger: the step's own entry, then the ledger's usual `init` so the new workbook is the baseline
    at = C.utc_now().isoformat(timespec='seconds')
    deleted_files = [f for f in p['files'] if f['action'] == 'delete']
    rec = {'at': at, 'verb': 'drop_unverified', 'before_sha': before_sha, 'after_sha': after_sha, 'backup': bk.name, 'n_rows': len(p['rows']),
           'n_av_rows': len(p['av_rows']), 'article_ids': [r['aid'] for r in p['rows']], 'story_ids': sorted({r['sid'] for r in p['rows'] if r['sid']}),
           'files_planned': [f['path'] for f in deleted_files], 'confirmed': True, 'confirmed_at': at}
    ledger_err = None
    try:
        with open(lay.state / 'ledger.jsonl', 'a', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        if init_fn(f'after drop_unverified ({len(p["rows"])} rows removed)') != 0:
            ledger_err = 'the tracker could not record the new workbook as its starting point'
    except OSError as e:
        ledger_err = f'ledger entry not written: {e!r}'[:200]
    # 7. the saved files: log first (with each file's sha256), then delete, then the log again with what happened
    logs = lay.state / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / f'drop-unverified-{stamp}.json'
    entries = []
    for f in deleted_files:
        src = lay.library / Path(*f['path'].split('/'))
        try:
            sha = C.sha256_file(src)
        except OSError:
            sha = None
        entries.append({'path': f['path'], 'sha256': sha, 'bytes': f.get('bytes'), 'deleted': False})
    doc = {'at': at, 'verb': 'drop_unverified', 'before_sha': before_sha, 'after_sha': after_sha, 'backup': bk.name, 'rows': p['rows'], 'av_rows': p['av_rows'],
           'files': entries, 'kept': [f for f in p['files'] if f['action'] == 'keep'], 'not_in_library': p['files_not_in_library'], 'status': 'started'}
    log.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding='utf-8')
    for e in entries:
        src = lay.inside(lay.library / Path(*e['path'].split('/')))
        if lay.library not in src.parents:
            e['error'] = 'outside the library'
            continue
        try:
            src.unlink()
            e['deleted'] = True
        except FileNotFoundError:
            e['error'] = 'already gone'
        except OSError as err:
            e['error'] = repr(err)[:120]
    doc['status'] = 'done'
    log.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding='utf-8')
    return {'ok': True, 'written': True, 'workbook_sha256': after_sha, 'before_sha': before_sha, 'backup': bk.name, 'n_rows': len(p['rows']),
            'n_av_rows': len(p['av_rows']), 'files_deleted': [e['path'] for e in entries if e['deleted']], 'files_failed': [e for e in entries if not e['deleted']],
            'files_kept': [f['path'] for f in doc['kept']], 'article_floor': res_doc['article_floor'], 'story_floor': res_doc['story_floor'],
            'log': log.name, 'ledger_error': ledger_err, 'rows': p['rows']}
