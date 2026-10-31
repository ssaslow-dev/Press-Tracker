import os, sys, tempfile, openpyxl
L = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, os.path.join(L, 'code'))
import sheet_task as ST
H = [c.value for c in next(openpyxl.load_workbook(os.path.join(L,'work/coverage_current.xlsx'), read_only=True)['Coverage'].iter_rows(max_row=1)) if c.value]
def book(rows, print_rows=()):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Coverage'; ws.append(H)
    for d in rows: ws.append([d.get(h, '') for h in H])
    pt = wb.create_sheet('Unlinked print pages'); pt.append(H + ['Likely counterpart', 'Clip priority'])
    for d in print_rows: pt.append([d.get(h, '') for h in H] + ['', ''])
    p = tempfile.mktemp(suffix='.xlsx'); wb.save(p); return p
def blocked_find(ph='NEW-r-1', **k):
    d = {'Article ID': ph, 'Story ID': 's' + ph, 'Original or reprint': 'Original', 'Data Source': 'Web search (TinyFish)', 'Date': '2026-10-27', 'Year': 2026,
         'Outlet': 'Los Angeles Times, The', 'Headline': 'Gabriel pushes bill on wildfire insurance', 'Edition': 'Web', 'Language': 'English', 'Medium': 'Online news',
         'Publisher link': 'https://www.latimes.com/california/story/2026-10-27/gabriel-wildfire-insurance', 'Link status': 'Publisher URL', 'Saved Copy?': 'No',
         'File name': 'BLOCKED – TinyFish', 'Tracker story code': 'jg-abc123', 'Role': 'Named in headline', 'Tone': 'Neutral', '_date_src': 'snippet', 'Date source': 'search snippet (converted)'}
    d.update(k); return d
def run(p, rows, today='2026-10-29'):
    T = ST.Task(ST.Sheet(p), {'pages': {}, 'runs': {'r1': {'at': today + 'T10:00:00Z', 'rows': rows}}}, today)
    T.apply_runs(); return T
def last(T):
    s = T.s; return {c: s.get(s.last_row, c) for c in H if s.get(s.last_row, c) not in (None, '')}
