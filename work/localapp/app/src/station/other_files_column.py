"""other_files_column.py: OTHERFILES-v1. A one-time step for switch-over day (checklist step 5d): add one empty column "Other files" as the last
column of the Coverage tab and of the Originals tab (the Originals tab mirrors Coverage, minus "Search lookup (Oct 26)").

    preview(lay)               -> what would change (read only), with a token
    apply(lay, token, init_fn) -> backup, staged workbook, its own check, swap, ledger; returns the result

Command line (keeper only; the app's station_cli.py can call the same functions):
    python -I other_files_column.py preview --root <AJG Tracker folder>
    python -I other_files_column.py apply   --root <AJG Tracker folder> --token <token from preview>

Why it is not a normal save: a save refuses a changed header row (SAVE_RULES: the header never changes in a save). This step is the one recorded
exception, so it is checked on its own, before anything is replaced:
  * backup first (rule 7), checksum verified; the staged workbook gets a unique name; Excel must be closed; no save may be running;
  * the staged file must differ from the master in exactly one way: the new header cell and one empty cell per row, on Coverage and Originals.
    Every other cell of every tab is the same (values, formulas), every hyperlink is on the same cell with the same target, the header of
    the new column has the same look as the column before it (font, fill, border, alignment, number format), every new cell has the look of
    the cell to its left in its row (so a red or purple row stays red or purple), the column is as wide as the one before it, and the
    auto-filter, frozen panes, tab order and the other tabs' headers are unchanged. Any other difference refuses the whole step;
  * the ledger gets a line (verb add_other_files_column, before/after sha, backup name) and then the ledger's usual `init`, so the changed
    workbook is the baseline and the next save sees the column on both sides.
Running it twice is harmless: a workbook that already has the column on both tabs is refused with "nothing to do".
Standard library plus openpyxl (the saver's own reader is reused for the check).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

if __package__ in (None, ''):        # run as a script with -I: the sibling modules are in this folder
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

COLUMN = 'Other files'
COVERAGE, ORIGINALS = 'Coverage', 'Originals'
TABS = (COVERAGE, ORIGINALS)


class OtherFilesRefused(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code, self.msg = code, msg


def _s(v) -> str:
    return '' if v is None else str(v).strip()


def _header_of(ws) -> list:
    hdr = [_s(c.value) for c in ws[1]]
    while hdr and not hdr[-1]:
        hdr.pop()
    return hdr


def _tabs_info(wb_path: Path) -> dict:
    import openpyxl
    wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=False)
    try:
        out = {}
        for n in TABS:
            if n in wb.sheetnames:
                ws = wb[n]
                hdr = _header_of(ws)
                out[n] = {'header': hdr, 'rows': max(ws.max_row - 1, 0), 'has': COLUMN in hdr, 'last': hdr[-1] if hdr else ''}
        return out
    finally:
        wb.close()


def plan(lay) -> dict:
    wb = lay.workbook
    if not wb.is_file():
        raise OtherFilesRefused('NO_WORKBOOK', 'The workbook is not in the data folder.')
    info = _tabs_info(wb)
    if COVERAGE not in info:
        raise OtherFilesRefused('NO_COVERAGE', 'The workbook has no Coverage tab.')
    sha = C.sha256_file(wb)
    todo = [n for n in TABS if n in info and not info[n]['has']]
    tok = hashlib.sha256(json.dumps([sha, todo, COLUMN]).encode()).hexdigest()[:16]
    return {'workbook_sha256': sha, 'tabs': {n: {'columns': len(v['header']), 'rows': v['rows'], 'already_has': v['has'], 'last_column': v['last']} for n, v in info.items()},
            'todo': todo, 'token': tok}


def preview(lay) -> dict:
    p = plan(lay)
    n = len(p['todo'])
    lines = [f'A new empty column "{COLUMN}" would be added as the last column of: ' + ', '.join(p['todo']) + '.' if n else 'Nothing to do: the column is already there.',
             'It would look like the column before it (header and every row, so coloured rows stay coloured) and nothing else in the workbook changes.',
             'A backup is made first and the new workbook is checked against the old one before it replaces it.']
    p.update(ok=True, can_apply=n > 0, headline=(f'Add the "{COLUMN}" column' if n else 'The column is already there'), lines=lines)
    try:
        d = lay.state / 'other_files_column'
        d.mkdir(parents=True, exist_ok=True)
        pf = d / f'preview-{C.stamp()}.json'
        pf.write_text(json.dumps(p, indent=1), encoding='utf-8')
    except OSError:
        pass
    return p


# ---------------------------------------------------------------- making the staged workbook

def add_column(book, tabs=TABS) -> dict:
    """add the empty column as the last one of each tab that lacks it (in an openpyxl workbook). Returns {tab: column number}."""
    from openpyxl.utils import get_column_letter
    done = {}
    for n in tabs:
        if n not in book.sheetnames:
            continue
        ws = book[n]
        hdr = _header_of(ws)
        if COLUMN in hdr:
            continue
        last = len(hdr)
        new = last + 1
        for r in range(1, ws.max_row + 1):
            src, dst = ws.cell(r, last), ws.cell(r, new)
            dst._style = copy.copy(src._style)
            if r == 1:
                dst.value = COLUMN
        L_old, L_new = get_column_letter(last), get_column_letter(new)
        w = ws.column_dimensions[L_old].width
        if w:
            ws.column_dimensions[L_new].width = w
        if ws.auto_filter.ref:
            ws.auto_filter.ref = f'A1:{L_new}{ws.max_row}'
        done[n] = new
    return done


def _hyperlinks(path: Path) -> dict:
    """{sheet name: sorted [(cell ref, target)]} from the sheet XML (an internal location counts as its target)"""
    from html import unescape
    out = {}
    z = zipfile.ZipFile(path)
    try:
        wbx = z.read('xl/workbook.xml').decode('utf-8', 'ignore')
        rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8', 'ignore')
        tgt = {}
        for m in re.finditer(r'<Relationship\b[^>]*>', rels):
            t = m.group(0)
            i, g = re.search(r'\bId="([^"]+)"', t), re.search(r'\bTarget="([^"]+)"', t)
            if i and g:
                tgt[i.group(1)] = g.group(1)
        for m in re.finditer(r'<sheet\b[^>]*>', wbx):
            t = m.group(0)
            n, r = re.search(r'\bname="([^"]*)"', t), re.search(r'\br:id="([^"]+)"', t)
            if not (n and r and r.group(1) in tgt):
                continue
            tp = tgt[r.group(1)].lstrip('/')
            tp = tp if tp.startswith('xl/') else 'xl/' + tp
            xml = z.read(tp).decode('utf-8', 'ignore')
            rel_t = {}
            rp = tp.replace('worksheets/', 'worksheets/_rels/') + '.rels'
            if rp in z.namelist():
                for mm in re.finditer(r'<Relationship\b[^>]*>', z.read(rp).decode('utf-8', 'ignore')):
                    tt = mm.group(0)
                    ii, gg = re.search(r'\bId="([^"]+)"', tt), re.search(r'\bTarget="([^"]*)"', tt)
                    if ii and gg:
                        rel_t[ii.group(1)] = unescape(gg.group(1))
            links = []
            for h in re.finditer(r'<hyperlink\b[^>]*>', xml):
                ht = h.group(0)
                ref = re.search(r'\bref="([^"]+)"', ht)
                rid = re.search(r'\br:id="([^"]+)"', ht)
                loc = re.search(r'\blocation="([^"]*)"', ht)
                links.append((ref.group(1) if ref else '', rel_t.get(rid.group(1), '') if rid else ('#' + unescape(loc.group(1)) if loc else '')))
            out[unescape(n.group(1))] = sorted(links)
    finally:
        z.close()
    return out


def _style_sig(cell) -> tuple:
    f, fl, b, a = cell.font, cell.fill, cell.border, cell.alignment
    return (f.name, f.sz, f.b, f.i, f.u, f.strike, getattr(f.color, 'rgb', None) if f.color is not None else None, getattr(f.color, 'theme', None) if f.color is not None else None,
            fl.fill_type, getattr(fl.fgColor, 'rgb', None), getattr(fl.fgColor, 'theme', None), b.left.style, b.right.style, b.top.style, b.bottom.style,
            a.horizontal, a.vertical, a.wrap_text, cell.number_format)


def check_staged(before: Path, after: Path, expect_tabs) -> list:
    """the step's own check. Returns the problems (an empty list = the staged file differs from the master only by the new column on `expect_tabs`)."""
    import openpyxl
    bad = []
    bk = openpyxl.load_workbook(before, read_only=False, data_only=False)
    ak = openpyxl.load_workbook(after, read_only=False, data_only=False)
    try:
        if bk.sheetnames != ak.sheetnames:
            return [f'the tabs changed: {bk.sheetnames} -> {ak.sheetnames}']
        for n in bk.sheetnames:
            wb_, wa = bk[n], ak[n]
            hb, ha = _header_of(wb_), _header_of(wa)
            if n in expect_tabs:
                if ha != hb + [COLUMN]:
                    bad.append(f'{n}: the header is not the old one plus "{COLUMN}" ({len(hb)} -> {len(ha)} columns)')
                    continue
                k = len(hb)
                if wa.max_row != wb_.max_row:
                    bad.append(f'{n}: {wb_.max_row} rows before, {wa.max_row} after')
                    continue
                if _style_sig(wa.cell(1, k + 1)) != _style_sig(wa.cell(1, k)):
                    bad.append(f'{n}: the new header cell does not look like the one before it')
                from openpyxl.utils import get_column_letter as gl
                if (wa.column_dimensions[gl(k + 1)].width or None) != (wa.column_dimensions[gl(k)].width or None):
                    bad.append(f'{n}: the new column is not as wide as the one before it')
                if wb_.freeze_panes != wa.freeze_panes:
                    bad.append(f'{n}: frozen panes changed')
                if wb_.auto_filter.ref and wa.auto_filter.ref != f'A1:{gl(k + 1)}{wa.max_row}':
                    bad.append(f'{n}: auto-filter is {wa.auto_filter.ref!r}, expected the old one widened by one column')
                wide = k
            else:
                if hb != ha:
                    bad.append(f'{n}: the header row changed')
                    continue
                if wa.max_row != wb_.max_row or wa.max_column != wb_.max_column:
                    bad.append(f'{n}: its size changed')
                    continue
                if wb_.freeze_panes != wa.freeze_panes or (wb_.auto_filter.ref or '') != (wa.auto_filter.ref or ''):
                    bad.append(f'{n}: frozen panes or auto-filter changed')
                wide = wb_.max_column
            for r in range(1, wb_.max_row + 1):
                for c in range(1, wide + 1):
                    x, y = wb_.cell(r, c), wa.cell(r, c)
                    if x.value != y.value:
                        bad.append(f'{n} row {r} column {c}: {str(x.value)[:40]!r} -> {str(y.value)[:40]!r}')
                    elif _style_sig(x) != _style_sig(y):
                        bad.append(f'{n} row {r} column {c}: the look changed')
                if n in expect_tabs and r > 1:
                    z = wa.cell(r, wide + 1)
                    if z.value not in (None, ''):
                        bad.append(f'{n} row {r}: the new cell is not empty')
                    if _style_sig(z) != _style_sig(wa.cell(r, wide)):
                        bad.append(f'{n} row {r}: the new cell does not look like the cell to its left')
                if len(bad) > 30:
                    return bad[:30]
            for r in range(1, wb_.max_row + 1):          # row heights / hidden rows
                a, b = wb_.row_dimensions[r], wa.row_dimensions[r]
                if (a.height, a.hidden) != (b.height, b.hidden):
                    bad.append(f'{n} row {r}: height or hidden flag changed')
                    break
    finally:
        bk.close()
        ak.close()
    hb, ha = _hyperlinks(before), _hyperlinks(after)
    if hb != ha:
        for n in hb:
            if hb[n] != ha.get(n):
                bad.append(f'{n}: hyperlinks differ (before {len(hb[n])}, after {len(ha.get(n, []))})')
    return bad[:30]


# ---------------------------------------------------------------- apply

def apply(lay, token: str, init_fn) -> dict:
    """init_fn(note) -> exit code: re-seeds the saver ledger with the new workbook (the ledger's own `init`)."""
    wb = lay.workbook
    if not wb.is_file():
        raise OtherFilesRefused('NO_WORKBOOK', 'The workbook is not in the data folder.')
    if C.excel_open(wb):
        raise OtherFilesRefused('EXCEL_OPEN', 'Excel has the workbook open. Close it, then try again. Nothing was changed.')
    if (lay.state / 'saver.lock').exists():
        raise OtherFilesRefused('LOCKED', 'A save is running (or was cut off). Wait for it, then try again. Nothing was changed.')
    ws0 = C.workbook_state(lay)
    if ws0.get('baseline') != 'ok':
        raise OtherFilesRefused('BASELINE', 'The workbook is not the one the tracker last saved or accepted. Use "Accept the workbook as it is now" (Repairs) first. Nothing was changed.')
    p = plan(lay)
    if not p['todo']:
        raise OtherFilesRefused('NOTHING', f'The "{COLUMN}" column is already there. Nothing was changed.')
    if p['token'] != token:
        raise OtherFilesRefused('CHANGED', 'The workbook changed since you looked. Preview again. Nothing was changed.')
    stamp = C.stamp()
    before_sha = p['workbook_sha256']
    lay.backups.mkdir(parents=True, exist_ok=True)
    bk = lay.backups / f'{wb.stem} BACKUP before add_other_files_column {stamp}.xlsx'
    n = 2
    while bk.exists():
        bk = bk.with_name(f'{bk.stem} ({n}){bk.suffix}')
        n += 1
    shutil.copy2(wb, bk)
    if C.sha256_file(bk) != before_sha:
        raise OtherFilesRefused('BACKUP_FAILED', 'The backup could not be made correctly, so nothing was changed.')
    import openpyxl
    tmpd = lay.data / 'tmp'
    tmpd.mkdir(parents=True, exist_ok=True)
    staged = tmpd / f'{wb.stem} STAGED add_other_files_column {stamp}.xlsx'
    book = openpyxl.load_workbook(wb)
    try:
        done = add_column(book, p['todo'])
        book.save(staged)
    finally:
        book.close()
    bad = check_staged(wb, staged, p['todo'])
    if bad:
        staged.unlink(missing_ok=True)
        raise OtherFilesRefused('VERIFY_FAILED', 'The staged workbook differs from the master in more than the new column, so nothing was changed. First difference: ' + bad[0])
    after_sha = C.sha256_file(staged)
    if C.excel_open(wb) or C.sha256_file(wb) != before_sha:
        staged.unlink(missing_ok=True)
        raise OtherFilesRefused('CHANGED', 'The workbook changed or Excel opened it while the step was running. Nothing was changed.')
    try:
        os.replace(staged, wb)
    except PermissionError:
        staged.unlink(missing_ok=True)
        raise OtherFilesRefused('EXCEL_OPEN', 'The workbook is in use (Excel or a virus scanner has it). Close Excel, wait a moment, then try again. Nothing was changed.')
    if C.sha256_file(wb) != after_sha:
        raise OtherFilesRefused('COMMIT_FAILED', f'The new workbook did not check out after it was written. The backup is {bk.name}. Tell Claude; do not save.')
    at = C.utc_now().isoformat(timespec='seconds')
    rec = {'at': at, 'verb': 'add_other_files_column', 'before_sha': before_sha, 'after_sha': after_sha, 'backup': bk.name, 'tabs': p['todo'],
           'columns': done, 'confirmed': True, 'confirmed_at': at}
    ledger_err = None
    try:
        with open(lay.state / 'ledger.jsonl', 'a', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        if init_fn(f'after add_other_files_column ({", ".join(p["todo"])})') != 0:
            ledger_err = 'the tracker could not record the new workbook as its starting point'
    except OSError as e:
        ledger_err = f'ledger entry not written: {e!r}'[:200]
    logs = lay.state / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / f'add-other-files-column-{stamp}.json'
    log.write_text(json.dumps({**rec, 'checks': 'only the new empty column differs; looks, widths, filter, hyperlinks, other tabs identical'}, indent=1), encoding='utf-8')
    return {'ok': True, 'written': True, 'workbook_sha256': after_sha, 'before_sha': before_sha, 'backup': bk.name, 'tabs': p['todo'], 'log': log.name,
            'ledger_error': ledger_err}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('verb', choices=['preview', 'apply'])
    ap.add_argument('--root', required=True)
    ap.add_argument('--token', default='')
    a = ap.parse_args(argv)
    lay = C.layout(a.root)
    import station_cli as SC
    MFU, TU = SC.boot(lay)
    from station_cli import R
    if R.role(lay) != 'keeper':
        print(json.dumps({'ok': False, 'written': False, 'line': 'Only the keeper copy of the tracker can change the workbook.'}))
        return 2
    try:
        if a.verb == 'preview':
            print(json.dumps(preview(lay), indent=1))
            return 0
        with C.AppLock(lay.state, 'add_other_files_column'):
            r = apply(lay, a.token, lambda note: TU.init_baseline(lay, note=note)['exit_code'])
            try:
                r['page_rebuild'] = SC.rebuild_page(lay)
            except Exception as e:      # noqa: BLE001
                r['page_rebuild'] = {'ok': False, 'error': repr(e)[:300]}
        print(json.dumps(r, indent=1, default=str))
        return 0
    except C.AppLockBusy as e:
        print(json.dumps({'ok': False, 'locked': True, 'written': False, 'line': C.busy_line(e.info, e.age)}))
        return 2
    except OtherFilesRefused as e:
        print(json.dumps({'ok': False, 'written': e.code == 'COMMIT_FAILED', 'code': e.code, 'line': e.msg}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
