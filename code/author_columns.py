"""T30: "Author 1".."Author N" + "Author title" right after "Author / byline" on Coverage and Originals.
Called from apply_fills.py after every other fill (so bylines written in the same run are split too), right before wb.save.

  add_author_columns(wb, fills=None, overrides=None) -> report dict

First run (no "Author 1" header yet): inserts N+1 columns (N = longest split) after "Author / byline" on both tabs and
fills every row that has a byline. Later runs (columns already there, e.g. after T24's TinyFish resume adds bylines):
fills only rows whose Author N / Author title cells are all blank; a row needing more than the existing N columns is
not written and is listed in report['needs_more_columns'] (add a column by hand or re-run on a fresh copy).
fills:     {old_aid: row dict of out/author_fills.csv (T24: authors, titles, kind, evidence)}; used when the sheet byline
           names the same people (keeps T24's titles), else the sheet byline is parsed
overrides: {aid: (authors joined by ' | ', title)} Sammy's review-queue answers (category 15-authors); win over the parser
New cells: green font (000B8A3E) like every other fill; headers copy the "Author / byline" header style.
Existing cells are never changed (columns are inserted, every old cell moves right unchanged).
"""
import copy, re
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter, column_index_from_string
from authorsplit import parse_byline, split_fill_row, board_outlet

GREEN = '000B8A3E'
ACOL = re.compile(r'Author \d+$')

def _insert(ws, at, n):
    """insert n columns before column index `at`, keeping widths and the autofilter range right."""
    widths = {k: (v.width, v.hidden) for k, v in ws.column_dimensions.items()}
    ws.insert_cols(at, n)
    nd = {}
    for k, (w, h) in widths.items():
        i = column_index_from_string(k); nd[get_column_letter(i + n if i >= at else i)] = (w, h)
    for k in list(ws.column_dimensions.keys()): del ws.column_dimensions[k]
    for k, (w, h) in nd.items():
        ws.column_dimensions[k].width = w; ws.column_dimensions[k].hidden = h
    if ws.auto_filter.ref:
        a, b = ws.auto_filter.ref.split(':'); m = re.match(r'([A-Z]+)(\d+)', b)
        ws.auto_filter.ref = f'{a}:{get_column_letter(column_index_from_string(m.group(1)) + n)}{m.group(2)}'

def _split_all(ws, fills, overrides):
    hdr = [c.value for c in ws[1]]
    cb, co, ca = hdr.index('Author / byline') + 1, hdr.index('Outlet') + 1, hdr.index('Article ID') + 1
    ck, cs = hdr.index('Original or reprint') + 1, hdr.index('Story ID') + 1
    orig = {}
    for r in range(2, ws.max_row + 1):   # Story ID -> Original row's outlet (editorial boards on reprints, DECISIONS 2026-10-27)
        if ws.cell(r, ck).value == 'Original' and ws.cell(r, co).value and ws.cell(r, cs).value:
            orig.setdefault(str(ws.cell(r, cs).value).strip(), str(ws.cell(r, co).value).strip())
    split = {}
    for r in range(2, ws.max_row + 1):
        b = ws.cell(r, cb).value; aid = ws.cell(r, ca).value
        if b is None or not str(b).strip(): continue
        outlet, _ = board_outlet(ws.cell(r, ck).value, ws.cell(r, co).value or '', ws.cell(r, cs).value, orig)
        if overrides and aid in overrides:
            a, t = overrides[aid]; split[aid] = ([x.strip() for x in a.split(' | ') if x.strip()], (t or '').strip())
        elif fills and aid in fills:
            p = split_fill_row(fills[aid], outlet, str(b)); split[aid] = (p['authors'], p['title'])
        else:
            p = parse_byline(str(b), outlet); split[aid] = (p['authors'], p['title'])
    return split

def add_author_columns(wb, fills=None, overrides=None):
    rep = {'needs_more_columns': []}
    split = _split_all(wb['Coverage'], fills, overrides)
    first = 'Author 1' not in [c.value for c in wb['Coverage'][1]]
    if first:
        N = max([len(a) for a, _ in split.values()] + [1])
    else:
        N = sum(1 for c in wb['Coverage'][1] if c.value and ACOL.match(str(c.value)))
    names = [f'Author {i}' for i in range(1, N + 1)] + ['Author title']
    for tab in ('Coverage', 'Originals'):
        ws = wb[tab]; hdr = [c.value for c in ws[1]]
        at = hdr.index('Author / byline') + 2; ca = hdr.index('Article ID') + 1
        if first:
            h0 = ws.cell(1, at - 1)
            _insert(ws, at, len(names))
            for j, nm in enumerate(names):
                c = ws.cell(1, at + j); c.value = nm
                c.font = copy.copy(h0.font); c.fill = copy.copy(h0.fill); c.alignment = copy.copy(h0.alignment); c.border = copy.copy(h0.border)
                ws.column_dimensions[get_column_letter(at + j)].width = 22 if j < N else 26
        else:
            assert [ws.cell(1, at + j).value for j in range(len(names))] == names, f'{tab}: Author columns not where expected'
        w = rows = 0
        for r in range(2, ws.max_row + 1):
            aid = ws.cell(r, ca).value
            if aid not in split: continue
            if any(ws.cell(r, at + j).value not in (None, '') for j in range(len(names))): continue   # already split: never change
            authors, title = split[aid]
            if len(authors) > N:
                if tab == 'Coverage': rep['needs_more_columns'].append(aid)
                continue
            src = ws.cell(r, at - 1); f = src.font or Font(); rows += 1
            for j, v in enumerate(authors + [''] * (N - len(authors)) + [title]):
                if not v: continue
                c = ws.cell(r, at + j); c.value = v
                c.font = Font(name=f.name, size=f.size, color=GREEN)
                c.alignment = copy.copy(src.alignment); c.border = copy.copy(src.border)
                w += 1
        rep[tab] = {'columns': names, 'inserted': first, 'at': get_column_letter(at), 'rows_written': rows, 'cells_written': w}
    rep['rows_with_byline'] = len(split); rep['max_authors'] = N
    return rep
