#!/usr/bin/env python3
"""T23: migrate the Coverage workbook to the new ID scheme (DECISIONS 2026-10-27 + amendment).
Runs as the LAST step of the single final workbook write (after all fills, which stay keyed by old IDs).

    python3 -I migrate_ids.py --xlsx IN.xlsx --idmap id_map.csv --out OUT.xlsx --report report.json \
        [--filemap filename_map.csv] [--dup dup_id_map.json] [--docs]

- id_map.csv: from make_id_map.py, built from THIS workbook (row, old ids, status must match row for row,
  or the script stops: regenerate the map, and the filename map with it).
- Adds "Old Article ID" and "Old Print Article ID" (last columns of Coverage) holding the old ids.
- Rewrites Article ID, Print Article ID (plain 5-digit numbers) and Story ID (jg-NNNNN -> sNNNNN).
- --filemap CSV (old_aid, column, new_filename) from agent-librename: replaces the whole File name / File name 2 cell
  of the row whose old Article ID or old Print Article ID = old_aid.
- Text references to old ids (nb-/ws-/pq-NNNNN, jg-NNNNN) in any other cell of any tab are rewritten (ids removed as
  duplicates are mapped through --dup). File name columns are only changed by --filemap; references left in them are
  reported. Tracker story code (6-hex legacy codes) is never touched.
- --docs: also rewrites the four scheme-description cells on Reprint info / Audit plan (exact old text required).
- Originals is rebuilt from Coverage (Original rows, Coverage order, minus "Search lookup (Oct 26)").
- Every rewritten or new cell gets green font 000B8A3E; other font attributes are kept.
- Verification (pandas + openpyxl): every other cell is unchanged in value and font, every id maps 1:1.
  Exit 2 if verification fails.
"""
import argparse, copy, csv, json, re, sys
import openpyxl
from openpyxl.styles.colors import Color
from openpyxl.utils import get_column_letter

GREEN = '000B8A3E'
SKIP_IN_ORIGINALS = {'Search lookup (Oct 26)'}
ID_COLS = ('Article ID', 'Print Article ID', 'Story ID')
NEW_COLS = ('Old Article ID', 'Old Print Article ID')
NEVER_TEXT = {'Tracker story code', 'Article ID', 'Print Article ID', 'Story ID', *NEW_COLS}
AID_RX = re.compile(r'\b(?:nb|ws|pq)-\d{5}\b')
SID_RX = re.compile(r'\bjg-\d{5}\b')
NEW_AID = re.compile(r'^\d{5}$')
NEW_SID = re.compile(r'^s\d{5}$')

DOCS = {  # (tab, cell): (exact old text, new text)
    ('Reprint info', 'A8'): ('Story ID (jg-NNNNN)', 'Story ID (sNNNNN)'),
    ('Reprint info', 'B9'): (
        'Unique per row. Prefix = where the row came from: nb- NewsBank, pq- ProQuest (via tracker), ws- web search (tracker scrape, tracker reprint list, or rows found by web search).',
        'Unique per row: a plain 5-digit number (00001…), one sequence over Article IDs and Print Article IDs in sheet order (2026-10-27). '
        'Where the row came from is in Data Source; the old prefixed ID (nb- NewsBank, pq- ProQuest via tracker, ws- web search) is kept in '
        '"Old Article ID" / "Old Print Article ID". Original/Reprint stays in its own column; the o/r suffix appears only in library file names '
        '(e.g. nb00034o-s00012.pdf).'),
    ('Audit plan', 'B15'): (
        "Story ID format jg-NNNNN; Article ID prefixes match Data Source (nb-/pq-/ws-) and are unique; exactly one Original per story; # of reprints matches the rows (distinct outlets minus the original's); Originals tab matches Coverage exactly.",
        "Story ID format sNNNNN; Article IDs and Print Article IDs are 5-digit numbers, unique across both columns, and map 1:1 to Old Article ID / Old Print Article ID; "
        "exactly one Original per story; # of reprints matches the rows (distinct outlets minus the original's); Originals tab matches Coverage exactly."),
    ('Audit plan', 'B29'): (
        'A "Change log" tab with one row per change: Article ID, column, old value, new value, rule applied, evidence (e.g. "96% / 94% shared text with nb-01234"), date.',
        'A "Change log" tab with one row per change: Article ID, column, old value, new value, rule applied, evidence (e.g. "96% / 94% shared text with 01234"), date.'),
}


def s(v):
    return '' if v is None else str(v).strip()


def green(cell):
    f = copy.copy(cell.font)
    f.color = Color(rgb=GREEN)
    cell.font = f


def load_map(path):
    rows = list(csv.DictReader(open(path, encoding='utf-8')))
    aid, sid = {}, {}
    for r in rows:
        aid[r['old_article_id']] = r['new_article_id']
        if r['old_print_article_id']:
            aid[r['old_print_article_id']] = r['new_print_article_id']
        if r['old_story_id']:
            if sid.get(r['old_story_id'], r['new_story_id']) != r['new_story_id']:
                raise SystemExit(f"story {r['old_story_id']} maps to two new ids")
            sid[r['old_story_id']] = r['new_story_id']
    return rows, aid, sid


def rebuild_originals(wb, ws, hdr):
    """Same as sheet_task.rebuild_originals (kept in step)."""
    if 'Originals' in wb.sheetnames:
        old = wb['Originals']; idx = wb.sheetnames.index('Originals')
        widths = {k: v.width for k, v in old.column_dimensions.items()}
        wb.remove(old)
    else:
        idx, widths = 1, {}
    o = wb.create_sheet('Originals', idx)
    ci = {h: i + 1 for i, h in enumerate(hdr)}
    cols = [i + 1 for i, h in enumerate(hdr) if h and h not in SKIP_IN_ORIGINALS]
    rows = [1] + [r for r in range(2, ws.max_row + 1) if ws.cell(r, ci['Original or reprint']).value == 'Original']
    for oi, r in enumerate(rows, start=1):
        for oc, c in enumerate(cols, start=1):
            sc, d = ws.cell(r, c), o.cell(oi, oc)
            d.value = sc.value
            d._style = copy.copy(sc._style)
    for oc, c in enumerate(cols, start=1):
        L = get_column_letter(oc)
        w = ws.column_dimensions[get_column_letter(c)].width or widths.get(L)
        if w:
            o.column_dimensions[L].width = w
    o.freeze_panes = 'C2'
    o.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{len(rows)}'
    return len(rows) - 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', required=True); ap.add_argument('--idmap', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--report', required=True)
    ap.add_argument('--filemap'); ap.add_argument('--dup'); ap.add_argument('--docs', action='store_true')
    ap.add_argument('--no-verify', action='store_true')
    a = ap.parse_args(argv)
    if a.out == a.xlsx:
        sys.exit('refusing to overwrite the input workbook')
    rows, amap, smap = load_map(a.idmap)
    tmap_a, tmap_s = dict(amap), dict(smap)          # for text references (incl. removed duplicate ids)
    if a.dup:
        dup = json.load(open(a.dup, encoding='utf-8'))
        for old, keep in dup.get('aid', {}).items():
            if old not in tmap_a and keep in amap: tmap_a[old] = amap[keep]
        for old, keep in dup.get('sid', {}).items():
            if old not in tmap_s and keep in smap: tmap_s[old] = smap[keep]

    wb = openpyxl.load_workbook(a.xlsx)
    ws = wb['Coverage']
    hdr = [c.value for c in ws[1]]
    if any(h in hdr for h in NEW_COLS):
        sys.exit('workbook already has Old Article ID columns: already migrated?')
    ci = {h: i + 1 for i, h in enumerate(hdr) if h}
    rep = {'rows': 0, 'rewritten': {c: 0 for c in ID_COLS}, 'old_cols_written': 0, 'file_names': 0,
           'filemap_unknown': [], 'text_refs': {}, 'text_cells': [], 'text_unmapped': [], 'filename_refs_left': 0,
           'docs': [], 'problems': []}

    # ---- 1. the map must describe this workbook row for row
    live = [r for r in range(2, ws.max_row + 1) if s(ws.cell(r, ci['Article ID']).value)]
    if len(live) != len(rows):
        sys.exit(f'id_map has {len(rows)} rows, workbook {len(live)}: regenerate id_map.csv (and the filename map)')
    for r, m in zip(live, rows):
        got = (str(r), s(ws.cell(r, ci['Article ID']).value), s(ws.cell(r, ci['Print Article ID']).value),
               s(ws.cell(r, ci['Story ID']).value), s(ws.cell(r, ci['Original or reprint']).value))
        want = (m['row'], m['old_article_id'], m['old_print_article_id'], m['old_story_id'], m['status'])
        if got != want:
            sys.exit(f'id_map does not match the workbook at row {r}: {got} vs {want}: regenerate id_map.csv')
    rep['rows'] = len(rows)

    # ---- 2. new columns (appended after the last column, styled like it)
    last = len(hdr)
    for k, name in enumerate(NEW_COLS, start=1):
        c = last + k
        h = ws.cell(1, c); h.value = name; h._style = copy.copy(ws.cell(1, last)._style)
        ws.column_dimensions[get_column_letter(c)].width = 14
        for r in range(2, ws.max_row + 1):
            ws.cell(r, c)._style = copy.copy(ws.cell(r, last)._style)
        ci[name] = c
    hdr = hdr + list(NEW_COLS)
    ws.auto_filter.ref = f'A1:{get_column_letter(len(hdr))}{ws.max_row}'

    # ---- 3. ids
    changed = set()   # (row, col) of cells this script set
    for r, m in zip(live, rows):
        for col, old_key, new_key in (('Article ID', 'old_article_id', 'new_article_id'),
                                      ('Print Article ID', 'old_print_article_id', 'new_print_article_id'),
                                      ('Story ID', 'old_story_id', 'new_story_id')):
            if not m[old_key]:
                continue
            cell = ws.cell(r, ci[col]); cell.value = m[new_key]; green(cell)
            changed.add((r, ci[col])); rep['rewritten'][col] += 1
        for col, key in (('Old Article ID', 'old_article_id'), ('Old Print Article ID', 'old_print_article_id')):
            if m[key]:
                cell = ws.cell(r, ci[col]); cell.value = m[key]; green(cell)
                changed.add((r, ci[col])); rep['old_cols_written'] += 1

    # ---- 4. file names
    fcols = [h for h in hdr if h and h.startswith('File name')]
    if a.filemap:
        row_of = {}
        for r, m in zip(live, rows):
            row_of[m['old_article_id']] = r
            if m['old_print_article_id']:
                row_of[m['old_print_article_id']] = r
        for fm in csv.DictReader(open(a.filemap, encoding='utf-8')):
            r = row_of.get(s(fm['old_aid'])); col = s(fm['column'])
            if r is None or col not in fcols:
                rep['filemap_unknown'].append(fm); continue
            cell = ws.cell(r, ci[col]); cell.value = s(fm['new_filename']); green(cell)
            changed.add((r, ci[col])); rep['file_names'] += 1

    # ---- 5. text references in every other cell, every tab except Originals (rebuilt)
    def sub(text):
        n = [0]
        def fa(mo):
            v = tmap_a.get(mo.group(0))
            if v is None: rep['text_unmapped'].append(mo.group(0)); return mo.group(0)
            n[0] += 1; return v
        def fs(mo):
            v = tmap_s.get(mo.group(0))
            if v is None: rep['text_unmapped'].append(mo.group(0)); return mo.group(0)
            n[0] += 1; return v
        return SID_RX.sub(fs, AID_RX.sub(fa, text)), n[0]
    doc_cells = {(t, c) for t, c in DOCS} if a.docs else set()
    if a.docs:
        for (t, c), (old, new) in DOCS.items():
            if t not in wb.sheetnames:   # OUTLETRULES-v1: Reprint info / Audit plan retired 2026-10-28
                rep['problems'].append(f'--docs: tab {t} not in the workbook (retired 2026-10-28), skipped'); continue
            cell = wb[t][c]
            if cell.value == old:
                cell.value = new; green(cell); rep['docs'].append(f'{t}!{c}')
            else:
                rep['problems'].append(f'--docs: {t}!{c} text differs from expected, left as is')
    for t in wb.sheetnames:
        if t == 'Originals':
            continue
        sh = wb[t]
        th = [c.value for c in sh[1]] if t == 'Coverage' else None
        for row in sh.iter_rows():
            for cell in row:
                if not isinstance(cell.value, str) or (t, cell.coordinate) in doc_cells:
                    continue
                h = th[cell.column - 1] if th else None
                if h in NEVER_TEXT:
                    continue
                if not (AID_RX.search(cell.value) or SID_RX.search(cell.value)):
                    continue
                if h in fcols:
                    if (cell.row, cell.column) not in changed:
                        rep['filename_refs_left'] += 1
                    continue
                new, n = sub(cell.value)
                if n:
                    cell.value = new; green(cell)
                    if t == 'Coverage': changed.add((cell.row, cell.column))
                    key = f'{t}!{h}' if h else t
                    rep['text_refs'][key] = rep['text_refs'].get(key, 0) + n
                    rep['text_cells'].append(f'{t}!{cell.coordinate}')

    # ---- 6. Originals
    rep['originals'] = rebuild_originals(wb, ws, hdr)
    wb.save(a.out)
    rep['text_unmapped'] = sorted(set(rep['text_unmapped']))
    if not a.no_verify:
        rep['verify'] = verify(a.xlsx, a.out, rows, tmap_a, tmap_s, a, rep)
    json.dump(rep, open(a.report, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
    short = {k: (len(v) if isinstance(v, list) and k != 'problems' else v) for k, v in rep.items()}
    print(json.dumps(short, indent=1, default=str)[:4000])
    return 0 if rep.get('verify', {}).get('ok', True) and not rep['problems'] else 2


def _col(c):
    return None if c is None else (c.type, c.rgb if c.type == 'rgb' else None, c.theme if c.type == 'theme' else None,
                                   c.indexed if c.type == 'indexed' else None, c.tint)


def fkey(cell):
    f, fl = cell.font, cell.fill
    return (f.name, f.sz, f.b, f.i, f.u, f.strike, f.vertAlign, _col(f.color),
            fl.fill_type, _col(fl.fgColor), cell.number_format, cell.alignment.wrap_text, cell.alignment.horizontal)


def verify(before, after, rows, tmap_a, tmap_s, a, rep):
    import pandas as pd
    probs = []
    B = pd.read_excel(before, sheet_name=None, dtype=str, header=None)
    A = pd.read_excel(after, sheet_name=None, dtype=str, header=None)
    if list(B) != list(A):
        probs.append(f'tab order changed: {list(B)} -> {list(A)}')
    fm = {}
    if a.filemap:
        for x in csv.DictReader(open(a.filemap, encoding='utf-8')):
            fm[(x['old_aid'].strip(), x['column'].strip())] = x['new_filename'].strip()

    def subtext(t):
        t = AID_RX.sub(lambda m: tmap_a.get(m.group(0), m.group(0)), t)
        return SID_RX.sub(lambda m: tmap_s.get(m.group(0), m.group(0)), t)
    docs = {(t, c): v for (t, c), v in DOCS.items()} if a.docs else {}

    # Coverage, cell by cell
    b, x = B['Coverage'].fillna(''), A['Coverage'].fillna('')
    bh, xh = list(b.iloc[0]), list(x.iloc[0])
    if xh != bh + list(NEW_COLS):
        probs.append('Coverage header: expected old header + Old Article ID, Old Print Article ID')
    if len(b) != len(x):
        probs.append(f'Coverage rows {len(b)} -> {len(x)}')
    m_by_row = {int(m['row']): m for m in rows}
    n_cells = 0
    for i in range(1, min(len(b), len(x))):
        m = m_by_row.get(i + 1)
        old_aid = b.iat[i, bh.index('Article ID')]
        for j, h in enumerate(bh):
            bv, xv = b.iat[i, j], x.iat[i, j]
            n_cells += 1
            if m and h == 'Article ID': want = m['new_article_id']
            elif m and h == 'Print Article ID': want = m['new_print_article_id']
            elif m and h == 'Story ID': want = m['new_story_id']
            elif h in ('File name', 'File name 2') and m and (
                    (m['old_article_id'], h) in fm or (m['old_print_article_id'] and (m['old_print_article_id'], h) in fm)):
                want = fm.get((m['old_article_id'], h)) or fm.get((m['old_print_article_id'], h))
            elif h in NEVER_TEXT or (h and h.startswith('File name')): want = bv
            else: want = subtext(bv)
            if xv != want:
                probs.append(f'Coverage r{i + 1} {h}: {bv[:50]!r} -> {xv[:50]!r} (want {want[:50]!r})')
        if m:
            if x.iat[i, len(bh)] != m['old_article_id'] or x.iat[i, len(bh) + 1] != m['old_print_article_id']:
                probs.append(f'Coverage r{i + 1}: Old Article ID columns wrong')
    # 1:1
    na, ns = x[xh.index('Article ID')][1:], x[xh.index('Print Article ID')][1:]
    allnew = [v for v in list(na) + list(ns) if v]
    oldall = [v for v in list(x[len(bh)][1:]) + list(x[len(bh) + 1][1:]) if v]
    if len(allnew) != len(set(allnew)): probs.append('new Article/Print IDs not unique')
    if len(oldall) != len(set(oldall)): probs.append('old Article/Print IDs not unique')
    if not all(NEW_AID.match(v) for v in allnew): probs.append('a new Article/Print ID is not 5 digits')
    if len(allnew) != len(oldall): probs.append('old/new id counts differ')
    pairs = {}
    for o_, n_ in zip(list(x[len(bh)][1:]) + list(x[len(bh) + 1][1:]), list(na) + list(ns)):
        if o_ or n_:
            if not (o_ and n_): probs.append(f'unpaired id {o_!r}/{n_!r}')
            pairs[o_] = n_
    if sorted(int(v) for v in allnew) != list(range(1, len(allnew) + 1)): probs.append('new numbers not a gapless 1..N sequence')
    sb, sx = b[bh.index('Story ID')][1:], x[xh.index('Story ID')][1:]
    sp = {}
    for o_, n_ in zip(sb, sx):
        if o_:
            if not NEW_SID.match(n_) or n_[1:] != o_[3:]: probs.append(f'story {o_} -> {n_}')
            if sp.setdefault(o_, n_) != n_: probs.append(f'story {o_} maps to two ids')
    if len(set(sp.values())) != len(sp): probs.append('two old stories share a new Story ID')
    # Originals mirrors Coverage originals
    o = A['Originals'].fillna('')
    co = x[x[xh.index('Original or reprint')] == 'Original']
    keep = [j for j, h in enumerate(xh) if h not in SKIP_IN_ORIGINALS]
    if len(o) - 1 != len(co) or list(o.iloc[0]) != [xh[j] for j in keep]:
        probs.append('Originals shape/header does not mirror Coverage')
    elif not (o.iloc[1:].values == co.iloc[:, keep].values).all():
        probs.append('Originals values do not mirror Coverage originals')
    # old Originals == new Originals except ids/new cols (same mapping)
    ob = B['Originals'].fillna('')
    if len(ob) == len(o):
        obh = list(ob.iloc[0])
        for j, h in enumerate(obh):
            jj = list(o.iloc[0]).index(h) if h in list(o.iloc[0]) else None
            if jj is None: probs.append(f'Originals lost column {h}'); continue
            if h in ID_COLS or (h and h.startswith('File name')): continue
            diff = (ob.iloc[1:, j].map(subtext if h not in NEVER_TEXT else (lambda v: v)).values != o.iloc[1:, jj].values).sum()
            if diff: probs.append(f'Originals {h}: {diff} cells differ beyond id rewrites')
    # other tabs: unchanged apart from text references / docs
    from openpyxl.utils import get_column_letter as gl
    for t in B:
        if t in ('Coverage', 'Originals'): continue
        bb, aa = B[t].fillna(''), A[t].fillna('')
        if bb.shape != aa.shape: probs.append(f'{t} shape changed'); continue
        for i in range(bb.shape[0]):
            for j in range(bb.shape[1]):
                coord = f'{gl(j + 1)}{i + 1}'
                want = docs[(t, coord)][1] if (t, coord) in docs and bb.iat[i, j] == docs[(t, coord)][0] else subtext(bb.iat[i, j])
                if aa.iat[i, j] != want: probs.append(f'{t}!{coord} changed unexpectedly')
    # fonts: every Coverage cell not rewritten keeps its font; rewritten ones are green
    wb0 = openpyxl.load_workbook(before); wb1 = openpyxl.load_workbook(after)
    w0, w1 = wb0['Coverage'], wb1['Coverage']
    fb = 0; fg = 0
    for r in range(1, w0.max_row + 1):
        for c in range(1, len(bh) + 1):
            c0, c1 = w0.cell(r, c), w1.cell(r, c)
            if c0.value != c1.value:
                if not (c1.font.color is not None and c1.font.color.rgb == GREEN): fg += 1
                f0, f1 = c0.font, c1.font
                if (f0.name, f0.sz, f0.b, f0.i) != (f1.name, f1.sz, f1.b, f1.i): fb += 1
            elif fkey(c0) != fkey(c1):
                fb += 1
    if fb: probs.append(f'{fb} Coverage cells changed font/fill/format unexpectedly')
    if fg: probs.append(f'{fg} rewritten Coverage cells are not green')
    for t in wb0.sheetnames:
        if t in ('Coverage', 'Originals'): continue
        for row in wb0[t].iter_rows():
            for c0 in row:
                c1 = wb1[t][c0.coordinate]
                if c0.value == c1.value and fkey(c0) != fkey(c1): probs.append(f'{t}!{c0.coordinate} font changed')
    return {'ok': not probs, 'problems': probs[:60], 'n_problems': len(probs), 'coverage_cells_checked': n_cells,
            'ids_paired': len(pairs), 'stories': len(sp)}


if __name__ == '__main__':
    sys.exit(main())
