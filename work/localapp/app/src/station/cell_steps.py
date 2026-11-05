"""cell_steps.py: the staged, cell-by-cell checked workbook change that the save uses after a rename (RENAME-v1) and that was once the machinery of the one-time
Switch-over changes screen (removed by D1; its code lives on here only as far as the save's rename hook needs it).

    auto_rename(lay, init_fn, before_roles)   after a save: rows whose Story ID or Original/Reprint role changed get their files renamed to match (add-only)

How a step changes the workbook: stage a copy, change the planned cells (and the planned rows' font colour), check the copy against the master cell by cell
(`check_cells`: nothing else may differ, not a value, a look, a hyperlink, a frozen pane), swap it in only if the check passes, write a ledger line, record the new
workbook as the tracker's starting point. Excel must be closed; the tracker's baseline must be ok. Nothing is deleted; files are moved with a journal that can
undo them if the workbook step refuses."""
from __future__ import annotations

import copy
import json
import re
import shutil
import zipfile
from pathlib import Path

import common as C
import rename_files as RF


class StepRefused(Exception):
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


def _norm_rgb(c):
    rgb = getattr(c, 'rgb', None) if c is not None else None
    return rgb[-6:].upper() if isinstance(rgb, str) and len(rgb) >= 6 else None


def _sig_nocolor(cell) -> tuple:
    f, fl, b, a = cell.font, cell.fill, cell.border, cell.alignment
    return (f.name, f.sz, f.b, f.i, f.u, f.strike, f.vertAlign, getattr(f.color, 'theme', None) if f.color is not None and _norm_rgb(f.color) is None else None,
            fl.fill_type, getattr(fl.fgColor, 'rgb', None), getattr(fl.fgColor, 'theme', None), b.left.style, b.right.style, b.top.style, b.bottom.style,
            a.horizontal, a.vertical, a.wrap_text, cell.number_format)


def check_cells(before: Path, after: Path, changes: list, links: list, skip_tabs=()) -> list:
    """the step's own independent check: the staged workbook equals the master except for the planned cells (values), the planned rows' font colour and the planned hyperlinks"""
    import openpyxl
    bk = openpyxl.load_workbook(before, read_only=False, data_only=False)
    ak = openpyxl.load_workbook(after, read_only=False, data_only=False)
    bad = []
    try:
        if bk.sheetnames != ak.sheetnames:
            return [f'the tabs changed: {bk.sheetnames} -> {ak.sheetnames}']
        want_val, want_font = {}, {}
        for c in changes:
            if c.get('set'):
                hdr = {h: i + 1 for i, h in enumerate(_header_of(bk[c['tab']]))}
                for col, v in c['set'].items():
                    want_val[(c['tab'], c['row'], hdr[col])] = v
            if 'font' in c:
                for k in range(1, bk[c['tab']].max_column + 1):
                    want_font[(c['tab'], c['row'], k)] = c['font'] or None
        for n in bk.sheetnames:
            if n in skip_tabs:
                continue
            x_, y_ = bk[n], ak[n]
            if _header_of(x_) != _header_of(y_) or (x_.max_row, x_.max_column) != (y_.max_row, y_.max_column):
                bad.append(f'{n}: the header or the size changed')
                continue
            if x_.freeze_panes != y_.freeze_panes or (x_.auto_filter.ref or '') != (y_.auto_filter.ref or ''):
                bad.append(f'{n}: frozen panes or auto-filter changed')
            cache_a, cache_b = {}, {}

            def info(cache, cell):
                """(look without font colour, font colour rgb, has a font colour, its theme): worked out once per distinct style (cheap per cell)"""
                st = getattr(cell, '_style', None)
                if st is None:                  # a merged-away cell has no look of its own
                    return (None, None, False, None)
                k = (st.fontId, st.fillId, st.borderId, st.numFmtId, st.alignmentId)
                v = cache.get(k)
                if v is None:
                    fc = cell.font.color
                    v = cache[k] = (_sig_nocolor(cell), _norm_rgb(fc), fc is not None, getattr(fc, 'theme', None) if fc is not None else None)
                return v
            nrows, ncols = x_.max_row, x_.max_column      # worked out once: on an editable sheet each call walks every cell
            for r in range(1, nrows + 1):
                for c in range(1, ncols + 1):
                    a, b = x_.cell(r, c), y_.cell(r, c)
                    k = (n, r, c)
                    exp = want_val.get(k, a.value)
                    if (b.value or None) != (exp or None) if isinstance(exp, str) or exp is None else b.value != exp:
                        bad.append(f'{n} row {r} column {c}: {str(a.value)[:30]!r} -> {str(b.value)[:30]!r} (expected {str(exp)[:30]!r})')
                    ia, ib = info(cache_a, a), info(cache_b, b)
                    if ia[0] != ib[0]:
                        bad.append(f'{n} row {r} column {c}: the look changed')
                    if k in want_font:
                        if ib[1] != want_font[k]:
                            bad.append(f'{n} row {r} column {c}: font colour is {ib[1]}, expected {want_font[k]}')
                    elif ia[1:] != ib[1:]:
                        bad.append(f'{n} row {r} column {c}: the font colour changed')
                if len(bad) > 20:
                    return bad[:20]
            for r in range(1, nrows + 1):
                p, q = x_.row_dimensions[r], y_.row_dimensions[r]
                if (p.height, p.hidden) != (q.height, q.hidden):
                    bad.append(f'{n} row {r}: height or hidden flag changed')
                    break
    finally:
        bk.close()
        ak.close()
    hb, ha = _hyperlinks(before), _hyperlinks(after)
    want = {n: sorted(set(map(tuple, v))) for n, v in hb.items()}
    for tab, ref, url in links:
        want[tab] = sorted(set(want.get(tab, [])) | {(ref, url)})
    for n in set(hb) | set(ha):
        if n in skip_tabs:          # that step's own check looks at these
            continue
        if sorted(ha.get(n, [])) != want.get(n, []):
            bad.append(f'{n}: hyperlinks differ from the plan (before {len(hb.get(n, []))}, after {len(ha.get(n, []))})')
    return bad[:20]


def _font_with(cell, rgb):
    from openpyxl.styles.colors import Color
    f = copy.copy(cell.font)
    f.color = Color(rgb='FF' + rgb) if rgb else None
    return f


def run_cell_step(lay, key: str, changes: list, init_fn, shared_backup=None, summary='', transform=None, extra_check=None, skip_tabs=()) -> dict:
    """stage, check, swap, ledger, init for a list of cell changes. Nothing is replaced unless the independent check passes."""
    import openpyxl
    wb = lay.workbook
    if C.excel_open(wb):
        raise StepRefused('EXCEL_OPEN', 'Excel has the workbook open. Close it, then try again. Nothing was changed.')
    if (lay.state / 'saver.lock').exists():
        raise StepRefused('LOCKED', 'A save is running (or was cut off). Wait for it, then try again. Nothing was changed.')
    if C.workbook_state(lay).get('baseline') != 'ok':
        raise StepRefused('BASELINE', 'The workbook is not the one the tracker last saved or accepted. Use "Accept the workbook as it is now" first. Nothing was changed.')
    before_sha = C.sha256_file(wb)
    stamp = C.stamp()
    if shared_backup is None:
        lay.backups.mkdir(parents=True, exist_ok=True)
        bk = lay.backups / f'{wb.stem} BACKUP before {key} {stamp}.xlsx'
        shutil.copy2(wb, bk)
        if C.sha256_file(bk) != before_sha:
            raise StepRefused('BACKUP_FAILED', 'The backup could not be made correctly, so nothing was changed.')
    else:
        bk = Path(shared_backup)
    tmpd = lay.data / 'tmp'
    tmpd.mkdir(parents=True, exist_ok=True)
    staged = tmpd / f'{wb.stem} STAGED {key} {stamp}.xlsx'
    links = []
    book = openpyxl.load_workbook(wb)
    try:
        hdrs = {}
        for c in changes:
            ws = book[c['tab']]
            h = hdrs.setdefault(c['tab'], {_s(x.value): i + 1 for i, x in enumerate(ws[1]) if x.value})
            if _s(ws.cell(c['row'], h['Article ID']).value) != c['aid']:
                raise StepRefused('ROWS_MOVED', f'{c["tab"]} row {c["row"]} is not where the plan says (Article ID {c["aid"]}). Nothing was changed.')
            for col, v in (c.get('set') or {}).items():
                cell = ws.cell(c['row'], h[col])
                if _s(cell.value) != _s((c.get('expect') or {}).get(col, _s(cell.value))):
                    raise StepRefused('CHANGED', f'{c["tab"]} row {c["row"]} column {col} changed since you looked. Nothing was changed.')
                cell.value = v
                if c.get('link') == col:
                    cell.hyperlink = v
                    links.append((c['tab'], cell.coordinate, v))
            if 'font' in c:
                for k in range(1, ws.max_column + 1):
                    cl = ws.cell(c['row'], k)
                    cl.font = _font_with(cl, c['font'])
        if transform:
            transform(book)
        book.save(staged)
    finally:
        book.close()
    bad = check_cells(wb, staged, changes, links, skip_tabs=skip_tabs)
    if not bad and extra_check:
        bad = extra_check(wb, staged)
    if bad:
        staged.unlink(missing_ok=True)
        raise StepRefused('VERIFY_FAILED', 'The staged workbook differs from the master in more than the plan, so nothing was changed. First difference: ' + bad[0])
    after_sha = C.sha256_file(staged)
    if C.excel_open(wb) or C.sha256_file(wb) != before_sha:
        staged.unlink(missing_ok=True)
        raise StepRefused('CHANGED', 'The workbook changed or Excel opened it while the step was running. Nothing was changed.')
    try:
        C.replace_file(staged, wb)
    except PermissionError:
        staged.unlink(missing_ok=True)
        raise StepRefused('EXCEL_OPEN', 'The workbook is in use (Excel or a virus scanner has it). Close Excel, wait a moment, then try again. Nothing was changed.')
    if C.sha256_file(wb) != after_sha:
        raise StepRefused('COMMIT_FAILED', f'The new workbook did not check out after it was written. The backup is {bk.name}. Tell Claude; do not save.')
    at = C.utc_now().isoformat(timespec='seconds')
    rec = {'at': at, 'verb': key, 'before_sha': before_sha, 'after_sha': after_sha, 'backup': bk.name, 'cells': sum(len(c.get('set') or {}) for c in changes),
           'rows': len({(c['tab'], c['row']) for c in changes}), 'article_ids': sorted({c['aid'] for c in changes})[:2000], 'summary': summary, 'confirmed': True, 'confirmed_at': at}
    err = None
    try:
        with open(lay.state / 'ledger.jsonl', 'a', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        if init_fn(f'after {key} ({rec["rows"]} rows)') != 0:
            err = 'the tracker could not record the new workbook as its starting point'
    except OSError as e:
        err = f'ledger entry not written: {e!r}'[:200]
    except Exception as e:      # noqa: BLE001  REVIEW_3 finding 2: the new workbook is in place; whatever fails now is reported, never raised (a caller must not undo file moves)
        err = f'the tracker could not record the new workbook as its starting point: {e!r}'[:200]
    try:
        (lay.state / 'logs').mkdir(parents=True, exist_ok=True)
        (lay.state / 'logs' / f'{key}-{stamp}.json').write_text(json.dumps({**rec, 'changes': changes}, indent=1, ensure_ascii=False), encoding='utf-8')
    except OSError as e:
        err = (err + '; ' if err else '') + f'the change log could not be written: {e!r}'[:150]
    return {'ok': True, 'workbook_sha256': after_sha, 'before_sha': before_sha, 'backup': bk.name, 'rows': rec['rows'], 'cells': rec['cells'], 'ledger_error': err}


def rename_step(lay, pl: dict, init_fn, shared_backup=None, why='') -> dict:
    """move the files (journalled), then change the cells with the usual staged, cell-by-cell checked step; if that step refuses before the swap the files are put back"""
    key = 'rename_files'
    stamp = C.stamp()
    jpath = lay.state / f'rename_journal_{stamp}.json'
    journal = RF.move_files(lay, pl, jpath)
    try:
        r = run_cell_step(lay, key, pl['changes'], init_fn, shared_backup=shared_backup, summary=f'{pl["n"]} files renamed')
    except StepRefused as e:
        if e.code != 'COMMIT_FAILED':      # COMMIT_FAILED is raised after the swap: the workbook already holds the new names, so the files stay
            RF.undo(journal)
        raise
    except Exception:
        # the point of no return is the swap inside run_cell_step; it reports every later problem in its result instead of raising, so an exception here came before it
        RF.undo(journal)
        raise
    try:
        lst = RF.write_list(lay, pl, stamp, why)
        r['list'] = lst.name
    except Exception as e:      # noqa: BLE001  the workbook and the files agree; only the old -> new list is missing
        r['list'] = ''
        r['ledger_error'] = ((r.get('ledger_error') or '') + '; ' if r.get('ledger_error') else '') + f'the old -> new list could not be written: {e!r}'[:150]
    return r


def auto_rename(lay, init_fn, before_roles: dict, shared_backup=None) -> dict:
    """RENAME-v1, the save: rows whose Story ID or Original/Reprint role changed in this save get their files renamed to match (add-only: nothing is deleted).
    before_roles = rename_files.story_roles(workbook) taken before the save. Returns {renamed, cells, list, collisions, ...}; {} when nothing changed."""
    after = RF.story_roles(lay.workbook)
    touched = {a for a, v in before_roles.items() if a in after and after[a] != v}
    if not touched:
        return {}
    pl = RF.plan(lay, only_aids=touched)
    if not pl['n']:
        return {'renamed': 0, 'collisions': pl['collisions'], 'touched': len(touched)} if pl['collisions'] else {}
    r = rename_step(lay, pl, init_fn, shared_backup=shared_backup, why='after a save or a data fix: story or role changed')
    return {'renamed': pl['n'], 'cells': pl['counts'].get('cells', 0), 'list': r['list'], 'collisions': pl['collisions'], 'touched': len(touched), 'workbook_sha256': r.get('workbook_sha256'),
            'files': [(x['old'], x['new']) for x in pl['renames']][:20]}


def auto_rename(lay, init_fn, before_roles: dict, shared_backup=None) -> dict:
    """RENAME-v1, the save: rows whose Story ID or Original/Reprint role changed in this save get their files renamed to match (add-only: nothing is deleted).
    before_roles = rename_files.story_roles(workbook) taken before the save. Returns {renamed, cells, list, collisions, ...}; {} when nothing changed."""
    after = RF.story_roles(lay.workbook)
    touched = {a for a, v in before_roles.items() if a in after and after[a] != v}
    if not touched:
        return {}
    pl = RF.plan(lay, only_aids=touched)
    if not pl['n']:
        return {'renamed': 0, 'collisions': pl['collisions'], 'touched': len(touched)} if pl['collisions'] else {}
    r = rename_step(lay, pl, init_fn, shared_backup=shared_backup, why='after a save or a data fix: story or role changed')
    return {'renamed': pl['n'], 'cells': pl['counts'].get('cells', 0), 'list': r['list'], 'collisions': pl['collisions'], 'touched': len(touched), 'workbook_sha256': r.get('workbook_sha256'),
            'files': [(x['old'], x['new']) for x in pl['renames']][:20]}
