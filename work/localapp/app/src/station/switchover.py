"""switchover.py: SWITCHOVER-v1. The ONE "Switch-over changes" screen: every one-time change to the real workbook, previewed together, confirmed all at once or step by step,
shown only that once.

    1 drop_unverified  DROPUNVERIFIED-v1  the "Reprint (unverified)" rows and their files (drop_unverified.py)
    1b rename_files    RENAME-v1          library files (with their raw page and OCR text) and the File name cells brought up to NAMING-v2 (rename_files.py)
    2 prjudge          PRJUDGE-v2         other issuers' releases reposted by news outlets become Press release = No (font black, Role filled on Originals that lack one);
                                          three missed wire releases become Yes. Every row is re-checked on the real workbook first (data/prjudge_v2.json is only the candidates)
    3 prcolor          PRCOLOR-v1         every row with Press release = Yes gets purple font (#7030A0) across the row; only the font colour changes
    4 other_files      OTHERFILES-v1      the empty "Other files" column on Coverage and Originals (other_files_column.py)
    5 datafix                             fixes Sammy approved later: a proposals CSV from work/localapp/datafix/*/ loaded here. Blanks only (a filled cell is never changed unless
                                          the file has an `overwrite` column saying yes for that row), low-confidence rows left out unless asked; link cells get their hyperlink

One backup first (made once, verified, reused by every step); each step stages its own workbook, checks it cell by cell against the master (values, looks, hyperlinks, tabs, header),
swaps it in, writes its own ledger entry and records the new workbook as the baseline. The page is rebuilt once at the end. A step can be done alone; steps already done show as done.
Standard library plus openpyxl.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
import re
import shutil
from pathlib import Path

import common as C
import datafix_structural as DS
import drop_unverified as DR
import other_files_column as OF
import rename_files as RF

PURPLE = '7030A0'
COVERAGE, ORIGINALS = 'Coverage', 'Originals'
ORDER = ('drop_unverified', 'rename_files', 'prjudge', 'prcolor', 'other_files', 'datafix', 'datafix_structural')
TITLES = {'drop_unverified': 'Remove the unverified reprints', 'rename_files': 'Rename files to the naming rule (RENAME-v1)', 'prjudge': 'Press release marks (PRJUDGE-v2)', 'prcolor': 'Purple rows for press releases (PRCOLOR-v1)',
          'other_files': 'Add the "Other files" column', 'datafix': 'Apply the data-check fixes you approved',
          'datafix_structural': 'Data-check fixes that change rows (English Originals, retired print pages)'}
DATA = Path(__file__).resolve().parent / 'data'
CONF = {'high': 3, 'medium': 2, 'low': 1}


class SwitchRefused(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code, self.msg = code, msg


def _s(v) -> str:
    return '' if v is None else str(v).strip()


def _today() -> str:
    try:
        from zoneinfo import ZoneInfo
        return C.utc_now().astimezone(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d')
    except Exception:                                   # noqa: BLE001  (no time zone data on this PC: the UTC date is a day early at worst)
        return C.utc_now().strftime('%Y-%m-%d')


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode('utf-8')).hexdigest()[:16]


# ---------------------------------------------------------------- state (shown only once)

def state_path(lay) -> Path:
    return lay.state / 'switchover.json'


def load_state(lay) -> dict:
    try:
        return json.loads(state_path(lay).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_state(lay, st: dict) -> None:
    C.atomic_write(state_path(lay), json.dumps(st, indent=1, ensure_ascii=False).encode('utf-8'))


def screen_status(lay) -> dict:
    """what the panel needs: is the screen shown, and which steps are done. Shown for a keeper copy after the setup from the Mac library, until every step is done or the
    person presses 'Finished' (then never again)."""
    st = load_state(lay)
    return {'finished': bool(st.get('finished_at')), 'done': {k: v.get('at') for k, v in (st.get('steps') or {}).items()}, 'backup': (st.get('backup') or {}).get('name'),
            'datafix_files': sorted(p.name for p in (lay.data / 'switchover' / 'datafix').glob('*.csv')) if (lay.data / 'switchover' / 'datafix').is_dir() else []}


def finish(lay) -> dict:
    st = load_state(lay)
    st['finished_at'] = C.utc_now().isoformat(timespec='seconds')
    save_state(lay, st)
    return {'ok': True}


# ---------------------------------------------------------------- reading the workbook

def read_tabs(wb_path: Path, tabs=(COVERAGE, ORIGINALS, 'Press releases', 'Unlinked print pages')):
    import openpyxl
    wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)
    try:
        out = {}
        for t in tabs:
            if t not in wb.sheetnames:
                continue
            it = wb[t].iter_rows(values_only=True)
            hdr = [_s(c) for c in next(it, [])]
            out[t] = (hdr, [(i, dict(zip(hdr, r))) for i, r in enumerate(it, start=2) if r and any(v not in (None, '') for v in r)])
        return out
    finally:
        wb.close()


def _rows_by_aid(tab):
    return {_s(d.get('Article ID')): (i, d) for i, d in tab[1] if _s(d.get('Article ID'))}


def copy_story_ids(pr_tab) -> set:
    out = set()
    for _, d in pr_tab[1]:
        for k in ('Copy story ID 1', 'Copy story ID 2'):
            if _s(d.get(k)):
                out.add(_s(d[k]))
    return out


def derive_role(d: dict) -> str:
    by = ' '.join(_s(d.get(f'Author {i}')) for i in range(1, 4)) + ' ' + _s(d.get('Author / byline'))
    if re.search(r'jesse\s+gabriel|gabriel,\s*jesse', by, re.I):
        return 'Op-ed by Gabriel'
    if re.search(r'gabriel', f'{_s(d.get("Headline"))} {_s(d.get("Translated Headline"))}', re.I):
        return 'Named in headline'
    return 'Mentioned in story'


# ---------------------------------------------------------------- planning (read only)

def plan_prjudge(tabs: dict) -> dict:
    cand = json.loads((DATA / 'prjudge_v2.json').read_text(encoding='utf-8'))
    cov = tabs[COVERAGE]
    byaid = _rows_by_aid(cov)
    ori = _rows_by_aid(tabs[ORIGINALS]) if ORIGINALS in tabs else {}
    own = copy_story_ids(tabs['Press releases']) if 'Press releases' in tabs else set()
    changes, skipped, unmark, mark = [], [], [], []

    def row_changes(aid, ci, d, **kw):
        out = [dict(tab=COVERAGE, row=ci, aid=aid, **kw)]
        if aid in ori and _s(ori[aid][1].get('Original or reprint')) == 'Original':
            out.append(dict(tab=ORIGINALS, row=ori[aid][0], aid=aid, **kw))
        return out

    for it in cand['unmark']:
        aid = it['aid']
        hit = byaid.get(aid)
        why = ''
        if not hit:
            why = 'the row is not in the workbook'
        else:
            ci, d = hit
            if _s(d.get('Press release')).lower() != 'yes':
                why = 'its Press release cell is no longer Yes'
            elif _s(d.get('Story ID')) != it['sid'] or _s(d.get('Outlet')) != it['outlet'] or not _s(d.get('Headline')).startswith(it['headline'][:30]):
                why = 'the row no longer matches the list (story, outlet or headline changed)'
            elif _s(d.get('Story ID')) in own:
                why = 'it is now counted as a copy of one of the office\'s releases'
        if why:
            skipped.append({'aid': aid, 'outlet': it['outlet'], 'why': why})
            continue
        ci, d = hit
        ch = row_changes(aid, ci, d, font='', set={'Press release': 'No'}, expect={'Press release': _s(d.get('Press release'))})
        if _s(d.get('Original or reprint')) == 'Original' and not _s(d.get('Role')):
            role = derive_role(d)
            for c in ch:
                c['set']['Role'] = role
                c['expect']['Role'] = ''
        changes += ch
        unmark.append({'aid': aid, 'outlet': it['outlet'], 'headline': it['headline'], 'role': (ch[0]['set'].get('Role') or '')})
    for it in cand['mark']:
        hit = byaid.get(it['aid'])
        if not hit or _s(hit[1].get('Outlet')) != it['outlet'] or _s(hit[1].get('Press release')):
            skipped.append({'aid': it['aid'], 'outlet': it['outlet'], 'why': 'not a blank-flag row of that outlet any more' if hit else 'the row is not in the workbook'})
            continue
        changes += row_changes(it['aid'], hit[0], hit[1], set={'Press release': 'Yes'}, expect={'Press release': ''})
        mark.append({'aid': it['aid'], 'outlet': it['outlet'], 'headline': it['headline']})
    lines = []
    if unmark:
        lines.append(f'{len(unmark)} rows become Press release = No and turn black, so they show in the tracker: other issuers\' releases reposted by news and community outlets (a repost is coverage).')
        nr = sum(1 for u in unmark if u['role'])
        if nr:
            lines.append(f'{nr} of them have no Role yet: it is filled from the headline.')
    if mark:
        lines.append(f'{len(mark)} wire releases that were missed are marked Press release = Yes: ' + ', '.join(f'{m["aid"]} ({m["outlet"]})' for m in mark) + '.')
    if skipped:
        lines.append(f'{len(skipped)} listed rows are left alone because they no longer match the workbook: ' + '; '.join(f'{s["aid"]} ({s["why"]})' for s in skipped[:5]) + (' ...' if len(skipped) > 5 else '') + '.')
    lines.append(f'Not changed: {cand["own_release_copies_kept_yes"]} copies of your office\'s own releases stay Yes (they count as pickups of the release).')
    if cand['org_posts_listed']:
        lines.append(f'For you to decide, not changed: {len(cand["org_posts_listed"])} posts on organisation sites that are not releases (' + ', '.join(sorted({o["outlet"] for o in cand["org_posts_listed"]})) + ').')
    for l in cand['left_alone']:
        lines.append(f'Left alone: {l["aid"]} ({l["outlet"]}): {l["why"]}.')
    return {'changes': changes, 'n': len(unmark) + len(mark), 'lines': lines, 'unmark': unmark, 'mark': mark, 'skipped': skipped,
            'listed_org': cand['org_posts_listed'], 'digest': _digest([[c['tab'], c['aid'], c['set']] for c in changes])}


def plan_prcolor(tabs: dict, prjudge: dict | None) -> dict:
    """rows with Press release = Yes, as they will be after the PRJUDGE step (when it is part of this run)"""
    un = {c['aid'] for c in (prjudge or {}).get('changes', []) if c.get('set', {}).get('Press release') == 'No'}
    mk = {c['aid'] for c in (prjudge or {}).get('changes', []) if c.get('set', {}).get('Press release') == 'Yes'}
    changes, counts = [], {}
    for tab in (COVERAGE, ORIGINALS):
        if tab not in tabs:
            continue
        n = 0
        for i, d in tabs[tab][1]:
            aid = _s(d.get('Article ID'))
            yes = (_s(d.get('Press release')).lower() == 'yes' and aid not in un) or aid in mk
            if yes:
                changes.append(dict(tab=tab, row=i, aid=aid, font=PURPLE))
                n += 1
        counts[tab] = n
    lines = [f'Every cell of {counts.get(COVERAGE, 0)} Coverage rows' + (f' and {counts[ORIGINALS]} Originals rows' if ORIGINALS in counts else '') +
             ' with Press release = Yes gets purple font (#7030A0). Only the font colour changes. Rows the tracker hides for other reasons stay red.']
    return {'changes': changes, 'n': counts.get(COVERAGE, 0), 'lines': lines, 'counts': counts, 'digest': _digest([[c['tab'], c['aid']] for c in changes])}


def _read_proposals(path: Path):
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    rd = csv.DictReader(io.StringIO(text))
    out = []
    for r in rd:
        low = {(k or '').strip().lower(): (v or '') for k, v in r.items()}
        key = low.get('article id') or low.get('article_id') or low.get('row key') or ''
        out.append({'tab': low.get('tab') or COVERAGE, 'aid': key.strip().zfill(5) if key.strip().isdigit() else key.strip(), 'col': (low.get('column') or '').strip(),
                    'cur': (low.get('current value (blank)') if 'current value (blank)' in low else low.get('current', '')).strip(),
                    'new': (low.get('new value') if 'new value' in low else low.get('new', '')).strip(), 'conf': (low.get('confidence') or 'high').strip().lower(),
                    'overwrite': (low.get('overwrite') or '').strip().lower() in ('yes', 'y', 'true', '1')})
    return out


def plan_datafix(lay, tabs: dict, include_low: bool = False, only: list | None = None) -> dict:
    d = lay.data / 'switchover' / 'datafix'
    # the approved fixes shipped with the app (DATAFIX-v1: made by work/localapp/datafix/make_approved.py), then any file the person added
    files = sorted((DATA / 'approved').glob('*.csv')) + (sorted(d.glob('*.csv')) if d.is_dir() else [])
    if only is not None:
        files = [f for f in files if f.name in only]
    if not files:
        return {'changes': [], 'n': 0, 'lines': ['No approved fixes file has been added yet. When you have approved some data-check fixes, add the file here and look again.'], 'files': [],
                'digest': _digest([])}
    changes, skipped, per = [], {}, []
    seen = {}
    by = {t: _rows_by_aid(tabs[t]) for t in (COVERAGE, ORIGINALS) if t in tabs}
    hdr = {t: tabs[t][0] for t in by}
    for f in files:
        props = _read_proposals(f)
        n0 = len(changes)
        for p in props:
            tab, aid, col = p['tab'], p['aid'], p['col']
            why = ''
            if not aid or not col or col.startswith('(') or tab != COVERAGE:
                why = 'not a plain cell fix (a note, a row, or another tab)'
            elif CONF.get(p['conf'], 2) < (1 if include_low else 2):
                why = 'low confidence (left out)'
            elif aid not in by[COVERAGE]:
                why = 'row not in the workbook'
            elif col not in hdr[COVERAGE]:
                why = 'no such column'
            elif col in ('Article ID', 'Story ID', 'Original or reprint', 'Press release'):
                why = 'a column the fixes never touch'
            else:
                ci, row = by[COVERAGE][aid]
                cur = _s(row.get(col))
                if cur and not p['overwrite']:
                    why = 'the cell is filled (fix blanks only)' if cur != p['new'] else 'already has that value'
                elif cur == p['new']:
                    why = 'already has that value'
                elif not p['new'] and not cur:
                    why = 'nothing to write'
                elif cur and p['overwrite'] and _s(p['cur']) != cur and p['cur']:
                    why = 'the cell changed since the file was made'
                elif (aid, col) in seen and seen[(aid, col)] != p['new']:
                    why = 'two fixes disagree about this cell (neither applied)'
            if why:
                skipped[why] = skipped.get(why, 0) + 1
                continue
            if (aid, col) in seen:
                continue
            seen[(aid, col)] = p['new']
            link = col.lower().endswith('link') or ' link' in col.lower() or col.lower().startswith('newsbank') and 'link' in col.lower()
            kw = dict(set={col: p['new']}, expect={col: cur}, link=col if (link and p['new'].lower().startswith('http')) else '')
            changes.append(dict(tab=COVERAGE, row=ci, aid=aid, **kw))
            if aid in by.get(ORIGINALS, {}) and col in hdr[ORIGINALS]:
                oi, orow = by[ORIGINALS][aid]
                if _s(orow.get(col)) == cur:
                    changes.append(dict(tab=ORIGINALS, row=oi, aid=aid, **kw))
        per.append({'file': f.name, 'proposals': len(props), 'fixes': len([c for c in changes[n0:] if c['tab'] == COVERAGE])})
    lines = [f'{x["file"]}: {x["fixes"]} cell fixes out of {x["proposals"]} lines.' for x in per]
    if skipped:
        lines.append('Left out: ' + '; '.join(f'{n} ({w})' for w, n in sorted(skipped.items(), key=lambda kv: -kv[1])) + '.')
    ncov = len([c for c in changes if c['tab'] == COVERAGE])
    cols = {}
    for c in changes:
        if c['tab'] == COVERAGE:
            k = next(iter(c['set']))
            cols[k] = cols.get(k, 0) + 1
    if cols:
        lines.append('Columns: ' + ', '.join(f'{k} ({n})' for k, n in sorted(cols.items(), key=lambda kv: -kv[1])[:8]) + '. Blanks only: no filled cell changes.')
    return {'changes': changes, 'n': ncov, 'lines': lines, 'files': per, 'skipped': skipped,
            'digest': _digest([[c['tab'], c['aid'], c['set']] for c in changes])}


def preview_all(lay, only=None, include_low=False, datafix_files=None) -> dict:
    """every step's preview together. Read only. Returns {steps: [{id, title, state, n, lines, digest, can_apply}], digest}"""
    wb = lay.workbook
    if not wb.is_file():
        raise SwitchRefused('NO_WORKBOOK', 'The workbook is not in the data folder.')
    st = load_state(lay)
    done = st.get('steps') or {}
    tabs = read_tabs(wb)
    steps = []
    pj = plan_prjudge(tabs) if 'prjudge' not in done else None
    rf = RF.plan(lay) if 'rename_files' not in done else None
    pc = plan_prcolor(tabs, pj) if 'prcolor' not in done else None
    df = plan_datafix(lay, tabs, include_low, datafix_files) if 'datafix' not in done else None
    pend = {c['aid'] for c in (df or {}).get('changes', []) if 'NewsBank print-page link' in (c.get('set') or {})}
    ds = DS.plan(tabs, _today(), pending_links=pend) if 'datafix_structural' not in done else None
    for sid in ORDER:
        s = {'id': sid, 'title': TITLES[sid], 'done_at': (done.get(sid) or {}).get('at'), 'state': 'done' if sid in done else 'todo', 'n': 0, 'lines': [], 'digest': '', 'can_apply': False}
        if sid in done:
            s['lines'] = [done[sid].get('summary') or 'Done.']
        elif sid == 'drop_unverified':
            try:
                p = DR.preview(lay)
                s.update(n=len(p.get('rows') or []), lines=p['lines'], digest=_digest([r['aid'] for r in p.get('rows') or []]), can_apply=bool(p.get('can_drop')))
            except DR.DropRefused as e:
                s.update(state='blocked', lines=[e.msg])
        elif sid == 'rename_files':
            s.update(n=rf['n'], lines=rf['lines'], digest=rf['digest'], can_apply=rf['n'] > 0,
                     detail={'collisions': rf['collisions'][:50], 'missing': len(rf['missing']), 'unnamed': len(rf['unnamed']), 'shared': len(rf['shared'])})
        elif sid == 'prjudge':
            s.update(n=pj['n'], lines=pj['lines'], digest=pj['digest'], can_apply=pj['n'] > 0, detail={'unmark': pj['unmark'], 'mark': pj['mark'], 'skipped': pj['skipped'], 'org': pj['listed_org']})
        elif sid == 'prcolor':
            s.update(n=pc['n'], lines=pc['lines'], digest=pc['digest'], can_apply=pc['n'] > 0)
        elif sid == 'other_files':
            try:
                p = OF.preview(lay)
                s.update(n=len(p['todo']), lines=p['lines'], digest=_digest(p['todo']), can_apply=bool(p['todo']))
            except OF.OtherFilesRefused as e:
                s.update(state='blocked', lines=[e.msg])
        elif sid == 'datafix':
            s.update(n=df['n'], lines=df['lines'] + ['For you to decide, not changed: ' + d for d in DS.decide_lines()], digest=df['digest'], can_apply=df['n'] > 0, files=df['files'])
        elif sid == 'datafix_structural':
            s.update(n=ds['n'], lines=ds['lines'], digest=ds['digest'], can_apply=ds['n'] > 0)
        if s['state'] == 'todo' and not s['can_apply']:
            s['state'] = 'nothing'
        steps.append(s)
    ws = C.workbook_state(lay)
    blocked = ''
    if ws.get('excel_open'):
        blocked = 'Excel has the workbook open. Close it first.'
    elif ws.get('baseline') != 'ok':
        blocked = 'The workbook is not the one the tracker last saved or accepted. Use "Accept the workbook as it is now" (Repairs) first.'
    elif (lay.state / 'saver.lock').exists():
        blocked = 'A save is running (or was cut off). Wait for it first.'
    return {'ok': True, 'steps': steps, 'blocked': blocked, 'workbook_sha256': ws.get('sha256'), 'backup': (st.get('backup') or {}).get('name'),
            'digest': _digest([[s['id'], s['digest']] for s in steps]), 'all_done': all(s['state'] in ('done', 'nothing') for s in steps), 'include_low': bool(include_low)}


# ---------------------------------------------------------------- the generic cell step (apply)

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
                hdr = {h: i + 1 for i, h in enumerate(OF._header_of(bk[c['tab']]))}
                for col, v in c['set'].items():
                    want_val[(c['tab'], c['row'], hdr[col])] = v
            if 'font' in c:
                for k in range(1, bk[c['tab']].max_column + 1):
                    want_font[(c['tab'], c['row'], k)] = c['font'] or None
        for n in bk.sheetnames:
            if n in skip_tabs:
                continue
            x_, y_ = bk[n], ak[n]
            if OF._header_of(x_) != OF._header_of(y_) or (x_.max_row, x_.max_column) != (y_.max_row, y_.max_column):
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
    hb, ha = OF._hyperlinks(before), OF._hyperlinks(after)
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
        raise SwitchRefused('EXCEL_OPEN', 'Excel has the workbook open. Close it, then try again. Nothing was changed.')
    if (lay.state / 'saver.lock').exists():
        raise SwitchRefused('LOCKED', 'A save is running (or was cut off). Wait for it, then try again. Nothing was changed.')
    if C.workbook_state(lay).get('baseline') != 'ok':
        raise SwitchRefused('BASELINE', 'The workbook is not the one the tracker last saved or accepted. Use "Accept the workbook as it is now" first. Nothing was changed.')
    before_sha = C.sha256_file(wb)
    stamp = C.stamp()
    if shared_backup is None:
        lay.backups.mkdir(parents=True, exist_ok=True)
        bk = lay.backups / f'{wb.stem} BACKUP before {key} {stamp}.xlsx'
        shutil.copy2(wb, bk)
        if C.sha256_file(bk) != before_sha:
            raise SwitchRefused('BACKUP_FAILED', 'The backup could not be made correctly, so nothing was changed.')
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
                raise SwitchRefused('ROWS_MOVED', f'{c["tab"]} row {c["row"]} is not where the plan says (Article ID {c["aid"]}). Nothing was changed.')
            for col, v in (c.get('set') or {}).items():
                cell = ws.cell(c['row'], h[col])
                if _s(cell.value) != _s((c.get('expect') or {}).get(col, _s(cell.value))):
                    raise SwitchRefused('CHANGED', f'{c["tab"]} row {c["row"]} column {col} changed since you looked. Nothing was changed.')
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
        raise SwitchRefused('VERIFY_FAILED', 'The staged workbook differs from the master in more than the plan, so nothing was changed. First difference: ' + bad[0])
    after_sha = C.sha256_file(staged)
    if C.excel_open(wb) or C.sha256_file(wb) != before_sha:
        staged.unlink(missing_ok=True)
        raise SwitchRefused('CHANGED', 'The workbook changed or Excel opened it while the step was running. Nothing was changed.')
    try:
        C.replace_file(staged, wb)
    except PermissionError:
        staged.unlink(missing_ok=True)
        raise SwitchRefused('EXCEL_OPEN', 'The workbook is in use (Excel or a virus scanner has it). Close Excel, wait a moment, then try again. Nothing was changed.')
    if C.sha256_file(wb) != after_sha:
        raise SwitchRefused('COMMIT_FAILED', f'The new workbook did not check out after it was written. The backup is {bk.name}. Tell Claude; do not save.')
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


# ---------------------------------------------------------------- RENAME-v1

def rename_step(lay, pl: dict, init_fn, shared_backup=None, why='') -> dict:
    """move the files (journalled), then change the cells with the usual staged, cell-by-cell checked step; if that step refuses before the swap the files are put back"""
    key = 'rename_files'
    stamp = C.stamp()
    jpath = lay.state / f'rename_journal_{stamp}.json'
    journal = RF.move_files(lay, pl, jpath)
    try:
        r = run_cell_step(lay, key, pl['changes'], init_fn, shared_backup=shared_backup, summary=f'{pl["n"]} files renamed')
    except SwitchRefused as e:
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


# ---------------------------------------------------------------- applying (the screen's Confirm)

def _make_backup(lay) -> Path:
    """the ONE backup of the screen: made at the first confirmed step, verified, reused by every later step"""
    st = load_state(lay)
    wb = lay.workbook
    if st.get('backup'):
        p = lay.backups / st['backup']['name']
        # REVIEW_3 finding 3: reuse only while the workbook is still the one the backup holds ; else a new backup
        if p.is_file() and C.sha256_file(p) == C.sha256_file(wb):
            return p
    lay.backups.mkdir(parents=True, exist_ok=True)
    sha = C.sha256_file(wb)
    bk = lay.backups / f'{wb.stem} BACKUP before switch-over changes {C.stamp()}.xlsx'
    shutil.copy2(wb, bk)
    if C.sha256_file(bk) != sha:
        bk.unlink(missing_ok=True)
        raise SwitchRefused('BACKUP_FAILED', 'The backup could not be made correctly, so nothing was changed.')
    st['backup'] = {'name': bk.name, 'sha256': sha, 'at': C.utc_now().isoformat(timespec='seconds')}
    save_state(lay, st)
    return bk


def apply_steps(lay, ids: list, digests: dict, init_fn, include_low=False, datafix_files=None) -> dict:
    """ids: the steps to do now (all of them, or one). digests: {id: digest} from the preview the person looked at; a step whose plan changed since is refused."""
    ids = [i for i in ORDER if i in ids]
    if not ids:
        raise SwitchRefused('NOTHING', 'No step was chosen.')
    pv0 = preview_all(lay, include_low=include_low, datafix_files=datafix_files)
    if pv0['blocked']:
        raise SwitchRefused('BLOCKED', pv0['blocked'] + ' Nothing was changed.')
    for s in pv0['steps']:
        if s['id'] in ids:
            if s['state'] == 'done':
                raise SwitchRefused('DONE', f'"{s["title"]}" was already done. Nothing was changed.')
            if s['state'] == 'blocked' or not s['can_apply']:
                raise SwitchRefused('NOTHING', f'"{s["title"]}" has nothing to do or cannot run: ' + (s['lines'][0] if s['lines'] else '') + ' Nothing was changed.')
            if digests.get(s['id']) != s['digest']:
                raise SwitchRefused('CHANGED', f'The plan for "{s["title"]}" changed since you looked. Look again. Nothing was changed.')
    bk = _make_backup(lay)
    results, st = [], load_state(lay)
    for sid in ids:
        # re-plan on the workbook as it is now (an earlier step changed it); its content must be the one that was previewed
        tabs = read_tabs(lay.workbook)
        if sid == 'drop_unverified':
            p = DR.plan(lay)
            if _digest([r['aid'] for r in p['rows']]) != digests.get(sid):
                raise SwitchRefused('CHANGED', 'The list of unverified reprints changed. Look again.')
            r = DR.apply(lay, p['token'], init_fn, shared_backup=bk)
            summ = f'{r["n_rows"]} rows removed ({len(r["files_deleted"])} files deleted)'
            lines = [f'{r["n_rows"]} Coverage rows and {r["n_av_rows"]} Audio & video rows removed for good.', f'{len(r["files_deleted"])} saved files deleted from the library.']
        elif sid == 'rename_files':
            pl = RF.plan(lay)
            if pl['digest'] != digests.get(sid):
                raise SwitchRefused('CHANGED', 'The files or the workbook changed since you looked. Look again.')
            r = rename_step(lay, pl, init_fn, shared_backup=bk, why='switch-over day (RENAME-v1)')
            summ = f'{pl["n"]} files renamed, {pl["counts"].get("cells", 0)} cells updated'
            lines = [f'{pl["n"]} saved files renamed (with their raw pages and OCR texts); {pl["counts"].get("cells", 0)} File name cells updated.',
                     f'The old and new names are in the library: _renamed/{r["list"]}.'] + ([f'{len(pl["collisions"])} files were left as they are because the new name was taken (see the list).'] if pl['collisions'] else [])
        elif sid == 'datafix_structural':
            ds = DS.plan(tabs, _today())
            if ds['digest'] != digests.get(sid):
                raise SwitchRefused('CHANGED', 'The plan for the row-changing fixes changed (the cell fixes may not all have landed). Look again.')
            roles0 = RF.story_roles(lay.workbook)
            stamp = C.stamp()
            r = run_cell_step(lay, 'datafix_structural', ds['changes'], init_fn, shared_backup=bk, summary=f'{len(ds["retire"])} print pages retired, {len(ds["swaps"])} English Originals',
                              transform=DS.make_transform(ds, lay, stamp), extra_check=DS.make_check(ds), skip_tabs=('Originals', 'Unlinked print pages'))
            summ = f'{len(ds["retire"])} Unlinked print pages retired, {len(ds["swaps"])} English Originals'
            lines = ds['lines']
            rn = auto_rename(lay, init_fn, roles0, shared_backup=bk)
            if rn.get('renamed'):
                lines = lines + [f'{rn["renamed"]} saved files renamed to match the new roles (list in the library, _renamed/{rn["list"]}).']
        elif sid == 'other_files':
            p = OF.plan(lay)
            if _digest(p['todo']) != digests.get(sid):
                raise SwitchRefused('CHANGED', 'The workbook changed. Look again.')
            r = OF.apply(lay, p['token'], init_fn, shared_backup=bk)
            summ = 'column "Other files" added'
            lines = [f'The empty "Other files" column was added to: {", ".join(p["todo"])}.']
        else:
            if sid == 'prjudge':
                pl = plan_prjudge(tabs)
            elif sid == 'prcolor':
                pl = plan_prcolor(tabs, None)           # the workbook already holds the PRJUDGE result (or the person chose to skip it)
            else:
                pl = plan_datafix(lay, tabs, include_low, datafix_files)
            want = digests.get(sid)
            if sid != 'prcolor' and pl['digest'] != want:
                raise SwitchRefused('CHANGED', f'The plan for "{TITLES[sid]}" changed. Look again.')
            if sid == 'prcolor' and not pl['changes']:
                raise SwitchRefused('NOTHING', 'No Press release = Yes rows to colour.')
            summ = f'{pl["n"]} rows' if sid != 'datafix' else f'{pl["n"]} cell fixes'
            r = run_cell_step(lay, {'prjudge': 'press_release_judge', 'prcolor': 'recolor_press_releases', 'datafix': 'apply_datafix'}[sid], pl['changes'], init_fn, shared_backup=bk, summary=summ)
            lines = pl['lines']
        if r.get('ledger_error'):
            lines = lines + [r['ledger_error'] + '. Use "Accept the workbook as it is now" under Repairs.']
        st = load_state(lay)
        st.setdefault('steps', {})[sid] = {'at': C.utc_now().isoformat(timespec='seconds'), 'summary': summ, 'sha': r.get('workbook_sha256')}
        save_state(lay, st)
        results.append({'id': sid, 'title': TITLES[sid], 'ok': True, 'summary': summ, 'lines': lines})
    return {'ok': True, 'results': results, 'backup': bk.name}
