"""datafix_structural.py: DATAFIX-v1, the approved fixes that single-cell changes cannot express (made by work/localapp/datafix/make_approved.py):

  * retire Unlinked print pages rows: a NewsBank page record whose link and citation now sit on the tracker's own row (Sammy's answers 1 and 2). A row is retired only when the
    Coverage row it belongs to already has its NewsBank print-page link filled (the cell fixes ran first). The retired rows are written to a CSV in data/switchover/ (and are in the backup);
  * English Original: for s00512 and s00985 the English copy becomes the Original and the Spanish Original its translation Reprint (answer 7). Same effect as the save program's own
    Original swap (sheet_task.swap_original): Tone / Tone note / Tone rated by / Topic / Bills carry to the new Original (blank only) and are cleared on the old row, the old row
    gets Reprint and a Team note line, the new row Original; the Originals tab is then rebuilt from Coverage exactly as the save does (sheet_task.rebuild_originals). Article IDs are
    never made or changed here (IDs come only from the save); the files follow the roles afterwards (rename_files).

plan() reads only; apply goes through switchover.run_cell_step (backup, staged copy, independent check, swap, ledger) with the two hooks below.
"""
from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data'
COVERAGE, ORIGINALS, UNLINKED = 'Coverage', 'Originals', 'Unlinked print pages'
ORIGINAL_ONLY = ('Tone', 'Tone note', 'Tone rated by', 'Topic', 'Bills', '# of reprints')
SKIP_IN_ORIGINALS = {'Search lookup (Oct 26)'}


def _s(v) -> str:
    return '' if v is None else str(v).strip()


def config() -> dict:
    try:
        return json.loads((DATA / 'datafix_structural.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def decide_lines() -> list:
    return list(config().get('decide') or [])


def plan(tabs: dict, today: str, pending_links=frozenset()) -> dict:
    cfg = config()
    cov = tabs.get('Coverage')
    unl = tabs.get(UNLINKED)
    out = {'retire': [], 'swaps': [], 'changes': [], 'skipped': [], 'lines': [], 'n': 0, 'digest': ''}
    if not cov or not cfg:
        return out
    by = {_s(d.get('Article ID')): (i, d) for i, d in cov[1]}
    ukey = {_s(d.get('Article ID')): i for i, d in unl[1]} if unl else {}
    for it in cfg.get('retire_unlinked') or []:
        row = by.get(it['aid'])
        if it['key'] not in ukey:
            out['skipped'].append({'what': f'Unlinked row {it["key"]}', 'why': 'not on the tab (already retired?)'})
        elif not row:
            out['skipped'].append({'what': f'Unlinked row {it["key"]}', 'why': f'row {it["aid"]} is not in the workbook'})
        elif not _s(row[1].get('NewsBank print-page link')) and it['aid'] not in pending_links:
            out['skipped'].append({'what': f'Unlinked row {it["key"]}', 'why': f'row {it["aid"]} has no NewsBank print-page link yet (the cell fixes must run first)'})
        else:
            out['retire'].append({'key': it['key'], 'row': ukey[it['key']], 'aid': it['aid']})
    for it in cfg.get('english_original') or []:
        new, old = by.get(it['new_original']), by.get(it['old_original'])
        why = ''
        if not new or not old:
            why = 'a row is not in the workbook'
        elif _s(old[1].get('Story ID')) != it['sid'] or _s(new[1].get('Story ID')) != it['sid']:
            why = 'the rows are not both in that story any more'
        elif _s(old[1].get('Original or reprint')) != 'Original' or _s(new[1].get('Original or reprint')) != 'Reprint':
            why = 'the roles are not Spanish Original / English Reprint (already done?)'
        elif _s(new[1].get('Language')) != 'English':
            why = 'the new Original is not an English row'
        if why:
            out['skipped'].append({'what': f'{it["sid"]} English Original', 'why': why})
            continue
        (ni, nd), (oi, od) = new, old
        hdr = cov[0]
        n_set, n_exp, o_set, o_exp = {}, {}, {}, {}
        for col in ORIGINAL_ONLY:
            if col not in hdr:
                continue
            v = od.get(col)
            if _s(v) != '':
                o_set[col], o_exp[col] = '', _s(v)
                if col == '# of reprints':
                    n_set[col], n_exp[col] = v, _s(nd.get(col))        # one reprint swapped for another: the count stays
                elif _s(nd.get(col)) == '':
                    n_set[col], n_exp[col] = v, ''
        o_set['Original or reprint'], o_exp['Original or reprint'] = 'Reprint', 'Original'
        n_set['Original or reprint'], n_exp['Original or reprint'] = 'Original', 'Reprint'
        if 'Team note' in hdr:
            tn = _s(od.get('Team note'))
            o_set['Team note'] = (tn + '; ' if tn else '') + f'Reprint since {today}: {_s(nd.get("Outlet"))} (English) is the Original (DATAFIX-v1, Sammy)'
            o_exp['Team note'] = tn
        if 'Role' in hdr and not _s(nd.get('Role')) and _s(od.get('Role')):
            n_set['Role'], n_exp['Role'] = _s(od.get('Role')), ''
        out['changes'] += [dict(tab=COVERAGE, row=oi, aid=it['old_original'], set=o_set, expect=o_exp), dict(tab=COVERAGE, row=ni, aid=it['new_original'], set=n_set, expect=n_exp)]
        out['swaps'].append({'sid': it['sid'], 'new': it['new_original'], 'old': it['old_original'], 'new_outlet': _s(nd.get('Outlet')), 'old_outlet': _s(od.get('Outlet'))})
    out['n'] = len(out['retire']) + len(out['swaps'])
    if out['retire']:
        out['lines'].append(f'{len(out["retire"])} Unlinked print pages rows are retired (their link and citation are on the tracker\'s own row now). They are saved to a list in data\\switchover.')
    if out['swaps']:
        out['lines'].append('The English copy becomes the Original (the Spanish Original becomes its translation Reprint, the Originals tab is rebuilt, the files are renamed to match): ' +
                            '; '.join(f'{s["sid"]}: {s["new"]} ({s["new_outlet"]}) replaces {s["old"]} ({s["old_outlet"]})' for s in out['swaps']) + '.')
    if out['skipped']:
        out['lines'].append(f'{len(out["skipped"])} items are left alone: ' + '; '.join(f'{s["what"]} ({s["why"]})' for s in out['skipped'][:4]) + (' ...' if len(out['skipped']) > 4 else '') + '.')
    for d in decide_lines():
        out['lines'].append('For you to decide, not changed: ' + d)
    import hashlib
    out['digest'] = hashlib.sha256(json.dumps([[r['key'] for r in out['retire']], [[s['sid'], s['new'], s['old']] for s in out['swaps']]], sort_keys=True).encode()).hexdigest()[:16]
    return out


# ---------------------------------------------------------------- the two hooks for switchover.run_cell_step

def make_transform(pl: dict, lay, stamp: str):
    """called with the openpyxl book after the Coverage cell changes: retire the Unlinked rows (listed to a CSV first), then rebuild Originals from Coverage (as the save does)"""
    def transform(book):
        if pl['retire']:
            ws = book[UNLINKED]
            hdr = [c.value for c in ws[1]]
            d = Path(lay.data) / 'switchover'
            d.mkdir(parents=True, exist_ok=True)
            with open(d / f'retired_unlinked_print_pages_{stamp}.csv', 'w', encoding='utf-8', newline='') as f:
                w = csv.writer(f)
                w.writerow(['Unlinked row'] + [_s(h) for h in hdr])
                for r in sorted(pl['retire'], key=lambda x: x['row']):
                    w.writerow([r['key']] + [_s(c.value) for c in ws[r['row']]])
            for r in sorted(pl['retire'], key=lambda x: -x['row']):
                assert _s(ws.cell(r['row'], 1).value) == r['key'] or any(_s(c.value) == r['key'] for c in ws[r['row']][:3]), 'row moved'
                ws.delete_rows(r['row'])
            last = ws.max_row
            if ws.auto_filter.ref:
                from openpyxl.utils import get_column_letter
                ws.auto_filter.ref = f'A1:{get_column_letter(ws.max_column)}{last}'
        if pl['swaps']:
            _rebuild_originals(book)
    return transform


def _rebuild_originals(book):
    from openpyxl.utils import get_column_letter
    ws = book[COVERAGE]
    hdr = [c.value for c in ws[1]]
    old = book[ORIGINALS]
    idx = book.sheetnames.index(ORIGINALS)
    widths = {k: v.width for k, v in old.column_dimensions.items()}
    book.remove(old)
    o = book.create_sheet(ORIGINALS, idx)
    cols = [i + 1 for i, h in enumerate(hdr) if h and h not in SKIP_IN_ORIGINALS]
    ocol = hdr.index('Original or reprint') + 1
    last = ws.max_row
    while last > 1 and all(ws.cell(last, c).value in (None, '') for c in (1, 2)):
        last -= 1
    rows = [1] + [r for r in range(2, last + 1) if ws.cell(r, ocol).value == 'Original']
    for oi, r in enumerate(rows, start=1):
        for oc, c in enumerate(cols, start=1):
            s = ws.cell(r, c)
            d = o.cell(oi, oc)
            d.value = s.value
            d._style = copy.copy(s._style)
    for oc, c in enumerate(cols, start=1):
        w = ws.column_dimensions[get_column_letter(c)].width or widths.get(get_column_letter(oc))
        if w:
            o.column_dimensions[get_column_letter(oc)].width = w
    o.freeze_panes = 'C2'
    o.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{len(rows)}'


def make_check(pl: dict):
    """the step's own independent look at the two tabs the generic cell check skips: Unlinked = before minus the retired rows; Originals = Coverage's Original rows, cell for cell"""
    def check(before: Path, after: Path) -> list:
        import openpyxl
        bk = openpyxl.load_workbook(before, read_only=True, data_only=False)
        ak = openpyxl.load_workbook(after, read_only=True, data_only=False)
        bad = []
        try:
            def vals(wb, n):
                return [list(r) for r in wb[n].iter_rows(values_only=True)]
            if UNLINKED in bk.sheetnames:
                gone = {r['key'] for r in pl['retire']}
                exp = [r for i, r in enumerate(vals(bk, UNLINKED)) if i == 0 or _s(r[0]) not in gone]
                got = vals(ak, UNLINKED)
                norm = lambda rows: [[_s(c) for c in r] for r in rows if any(_s(c) for c in r)]
                if norm(exp) != norm(got):
                    bad.append(f'{UNLINKED}: the rows are not "before minus the retired ones"')
            cov = vals(ak, COVERAGE)
            h = cov[0]
            oc = h.index('Original or reprint')
            cols = [i for i, x in enumerate(h) if x and x not in SKIP_IN_ORIGINALS]
            exp = [[r[i] for i in cols] for k, r in enumerate(cov) if k == 0 or r[oc] == 'Original']
            got = vals(ak, ORIGINALS)
            norm = lambda rows: [[_s(c) for c in r] for r in rows if any(_s(c) for c in r)]
            if norm(exp) != norm(got):
                bad.append('Originals does not match the Original rows of Coverage')
            ids = [_s(r[0]) for r in got[1:] if _s(r[0])]
            if len(ids) != len(set(ids)):
                bad.append('Originals lists an Article ID twice')
        finally:
            bk.close()
            ak.close()
        return bad[:10]
    return check
