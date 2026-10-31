"""Shared mini-workbook builder for the code-audit tests (a copy, never the master).
Coverage + Removed (+ optional Unlinked print pages / AV) tabs with the columns sheet_task.py touches."""
import json, os, subprocess, sys, tempfile
import openpyxl

L = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))   # build/tests/sheet_task/audit -> L
ST = os.environ.get('ST') or os.path.join(L, 'code', 'sheet_task.py')
OUT = os.environ.get('AUDIT_OUT') or tempfile.mkdtemp(prefix='audit_')   # test outputs, never the master
os.makedirs(OUT, exist_ok=True)

COLS = ['Article ID', 'Old Article ID', 'Story ID', 'Original or reprint', 'Data Source', 'Saved Copy?', 'File type', 'File name',
        'File name 2', 'Date', 'Year', 'Date source', 'Outlet', 'Publisher', 'Outlet city', 'Outlet county', 'Outlet state', 'Medium',
        'Format', 'Reach', 'Language', 'Headline', 'Author / byline', 'Edition', 'Print Article ID', 'Old Print Article ID',
        'Word count', 'Mentions "Gabriel" in text', '# of reprints', 'Topic', 'Bills', 'Tone', 'Tone note', 'Tone rated by',
        'Team note', 'Publisher link', 'Link status', 'ProQuest link', 'NewsBank article link', 'Tracker story code', 'Role',
        'Press release', 'Mention depth']
RM_COLS = ['From tab', 'Reason removed', 'Removed on', 'Category', 'Other tab row (as removed)'] + COLS

ARTICLE = ('<html><head><title>T1</title></head><body><h1>Gabriel bill test story one</h1>' + ''.join(
    f'<p>Paragraph {i}: Assemblymember Jesse Gabriel said the bill would help families across the state, and lawmakers '
    f'debated the measure for several hours before the vote on Monday afternoon in Sacramento.</p>' for i in range(6)) +
    '</body></html>')


def row(**kw):
    return {c: kw.get(c, None) for c in COLS}


def make(path, cov_rows, removed_rows=()):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Coverage'
    ws.append(COLS)
    for r in cov_rows:
        ws.append([r.get(c) for c in COLS])
    o = wb.create_sheet('Originals'); o.append(COLS)
    for r in cov_rows:
        if r.get('Original or reprint') == 'Original':
            o.append([r.get(c) for c in COLS])
    rm = wb.create_sheet('Removed'); rm.append(RM_COLS)
    for r in removed_rows:
        rm.append([r.get(c) for c in RM_COLS])
    wb.save(path)
    return path


def run(db, xin, name, extra=(), today='2026-10-29'):
    dbp = os.path.join(OUT, name + '_db.json'); json.dump(db, open(dbp, 'w'))
    out, res = os.path.join(OUT, name + '.xlsx'), os.path.join(OUT, name + '.json')
    p = subprocess.run([sys.executable, '-I', ST, '--db', dbp, '--xlsx', xin, '--out', out, '--result', res,
                        '--pages-dir', os.path.join(OUT, name + '_pages'), '--today', today, *extra], capture_output=True, text=True)
    if p.returncode not in (0, 2):
        sys.exit(p.stderr[-3000:])
    return out, json.load(open(res)), p.returncode


def cov(path):
    ws = openpyxl.load_workbook(path)['Coverage']
    hdr = [c.value for c in ws[1]]
    return [dict(zip(hdr, [c.value for c in ws[r]])) for r in range(2, ws.max_row + 1)]
