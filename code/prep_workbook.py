"""T1 workbook prep (coordinator). Usage: python3 -I prep_workbook.py IN.xlsx OLD_MENTIONS.xlsx OUT.xlsx REPORT.json
- adds Role column (end of Coverage and Originals)
- fills Topic / Bills / Reach / Role on Original rows from the old tracker Stories tab (blanks only)
- appends old tracker stories that have no Coverage row, plus their reprint-list rows
- mirrors changes into Originals; updates Reprint info notes
New values in green 000B8A3E; tracker story codes in red 00C00000 (existing conventions).
"""
import sys, re, json, copy, datetime
import openpyxl, pandas as pd
from openpyxl.styles import Font

IN, OLD, OUT, REP = sys.argv[1:5]
GREEN, RED = '000B8A3E', '00C00000'
wb = openpyxl.load_workbook(IN)
ws = wb['Coverage']; wo = wb['Originals']
hdr = [c.value for c in ws[1]]; ohdr = [c.value for c in wo[1]]
col = {h: i + 1 for i, h in enumerate(hdr)}; ocol = {h: i + 1 for i, h in enumerate(ohdr)}

S = pd.read_excel(OLD, sheet_name='Stories').fillna('')
old = {r['Story code']: r for _, r in S.iterrows()}

def blank(v): return v is None or (isinstance(v, str) and not v.strip())

def put(sheet, r, c, v, color=GREEN):
    cell = sheet.cell(r, c)
    if not blank(cell.value): return False
    cell.value = v
    f = copy.copy(cell.font) if cell.font else Font()
    cell.font = Font(name=f.name, size=f.size, bold=f.bold, italic=f.italic, color=color)
    return True

def add_header(sheet, name):
    c = sheet.max_column + 1
    src = sheet.cell(1, c - 1); dst = sheet.cell(1, c)
    dst.value = name; dst.font = copy.copy(src.font); dst.fill = copy.copy(src.fill)
    dst.alignment = copy.copy(src.alignment); dst.border = copy.copy(src.border)
    sheet.column_dimensions[openpyxl.utils.get_column_letter(c)].width = 20
    return c

col['Role'] = add_header(ws, 'Role'); ocol['Role'] = add_header(wo, 'Role')

def derive_role(byline, hl, hl_en):
    if re.search(r'jesse\s+gabriel|gabriel,\s*jesse', str(byline), re.I): return 'Op-ed by Gabriel'
    if re.search(r'gabriel', f'{hl} {hl_en}', re.I): return 'Named in headline'
    return 'Mentioned in story'

rep = {'role_written': 0, 'role_conflicts': [], 'tags': {'Topic': 0, 'Bills': 0, 'Reach': 0}, 'added_originals': [], 'added_reprints': 0}
orig_rows = {}  # aid -> row index in Coverage
codes_in_sheet = set()
maxn = {'nb': 0, 'pq': 0, 'ws': 0}; maxjg = 0
for r in range(2, ws.max_row + 1):
    aid = ws.cell(r, col['Article ID']).value
    if not aid: continue
    p, n = aid.split('-'); maxn[p] = max(maxn[p], int(n))
    sid = ws.cell(r, col['Story ID']).value
    if sid: maxjg = max(maxjg, int(sid.split('-')[1]))
    cell = ws.cell(r, col['Tracker story code']).value or ''
    codes = re.findall(r'jg-[0-9a-f]{6}', str(cell))  # a cell can hold several codes ("jg-a; jg-b")
    codes_in_sheet.update(codes)
    if ws.cell(r, col['Original or reprint']).value != 'Original': continue
    orig_rows[aid] = r
    code = next((c for c in codes if c in old), codes[0] if codes else None)
    o = old.get(code)
    d = derive_role(ws.cell(r, col['Author / byline']).value, ws.cell(r, col['Headline']).value, ws.cell(r, col['Translated Headline']).value)
    if o is not None and o['How Gabriel appears'] and o['How Gabriel appears'] != d:
        rep['role_conflicts'].append({'aid': aid, 'sid': sid, 'code': code, 'derived': d, 'old_tracker': o['How Gabriel appears'],
                                      'byline': ws.cell(r, col['Author / byline']).value, 'headline': ws.cell(r, col['Headline']).value})
    elif put(ws, r, col['Role'], d): rep['role_written'] += 1
    if o is not None:
        for k in ('Topic', 'Bills', 'Reach'):
            if o[k] and put(ws, r, col[k], o[k]): rep['tags'][k] += 1

# ---- old tracker stories with no Coverage row
MON = {m: i for i, m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], 1)}
def parse_rep(item):
    m = re.match(r'^(.*?)\s*\((\w{3})\w*\.? (\d{1,2}), (\d{4})\)$', item.strip())
    if m and m.group(2)[:3] in MON:
        return m.group(1).strip(), f'{m.group(4)}-{MON[m.group(2)[:3]]:02d}-{int(m.group(3)):02d}'
    return item.strip(), ''
missing = [o for c, o in old.items() if c not in codes_in_sheet]
missing.sort(key=lambda o: str(o['Date']))
manifest = json.load(open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', 'work', 'old_manifest.json')))['articles']
nxt = {'ws': maxn['ws'] + 1, 'pq': maxn['pq'] + 1}; jg = maxjg + 1

def append(vals, red_code=True):
    r = ws.max_row + 1
    for k, v in vals.items():
        if blank(v): continue
        put(ws, r, col[k], v, RED if (k == 'Tracker story code' and red_code) else GREEN)
    return r

for o in missing:
    pq = str(o['Source']).startswith('ProQuest')
    p = 'pq' if pq else 'ws'; aid = f'{p}-{nxt[p]:05d}'; nxt[p] += 1
    sid = f'jg-{jg:05d}'; jg += 1
    code = o['Story code']
    reps = [x for x in str(o['Reprinted in']).split(';') if x.strip() and not re.search(r'not (found|identified)', x, re.I)]
    reps = [parse_rep(x) for x in reps]
    outlet = re.sub(r'\s*\(\+\d+ more\)$', '', str(o['Outlet']))
    distinct = {n for n, _ in reps if n and n != outlet}
    d = str(o['Date'])[:10]
    yr = int(o['Year']) if str(o['Year']).strip() else ''
    vals = {
        'Article ID': aid, 'Story ID': sid, 'Original or reprint': 'Original',
        'Data Source': 'ProQuest' if pq else 'Tracker scrape',
        'Saved Copy?': 'Yes' if code in manifest else 'No',
        'File type': ('ProQuest pdf' if pq else 'scraped html') if code in manifest else '',
        'File name': f"{manifest[code]} ({code})" if code in manifest else '',
        'Date': d, 'Year': yr, 'Outlet': outlet, 'Publisher': o['Publisher'],
        'Outlet county': o['County'], 'Medium': o['Media type'], 'Reach': o['Reach'],
        'Language': o['Language'] or 'English', 'Headline': o['Headline'],
        'Translated Headline': o['Headline in English'], 'Story in English': o['Story in English'],
        'Author / byline': o['Author'], 'Edition': 'Web' if not pq else '',
        '# of reprints': len(distinct), 'Topic': o['Topic'], 'Bills': o['Bills'],
        'Tone': o['Tone'], 'Tone note': o['Tone note'], 'Tone rated by': o['Tone rated by'], 'Team note': o['Team note'],
        'Publisher link': o['Publisher link'] or o['Link'], 'Link status': o['Link status'],
        'ProQuest link': o['ProQuest direct link'], 'ProQuest via CA State Library': o['CA State Library link'],
        'Tracker story code': code, 'Role': o['How Gabriel appears'],
    }
    r = append(vals)
    rep['added_originals'].append({'aid': aid, 'sid': sid, 'code': code, 'date': d, 'outlet': outlet, 'source': o['Source'], 'reprints': len(reps)})
    for name, rd in reps:
        a2 = f'ws-{nxt["ws"]:05d}'; nxt['ws'] += 1
        append({'Article ID': a2, 'Story ID': sid, 'Original or reprint': 'Reprint', 'Data Source': 'Tracker reprint list',
                'Saved Copy?': 'No', 'Outlet': name, 'Date': rd, 'Year': int(rd[:4]) if rd else '', 'Tracker story code': code})
        rep['added_reprints'] += 1

# ---- mirror into Originals: fill existing original rows, append new originals (same columns by name)
oaid = {wo.cell(r, ocol['Article ID']).value: r for r in range(2, wo.max_row + 1)}
for r in range(2, ws.max_row + 1):
    if ws.cell(r, col['Original or reprint']).value != 'Original': continue
    aid = ws.cell(r, col['Article ID']).value
    orow = oaid.get(aid) or wo.max_row + 1
    for h, oc in ocol.items():
        v = ws.cell(r, col[h]).value
        if blank(v): continue
        src_color = ws.cell(r, col[h]).font.color.rgb if ws.cell(r, col[h]).font and ws.cell(r, col[h]).font.color else None
        if aid in oaid:
            if h in ('Topic', 'Bills', 'Reach', 'Role'): put(wo, orow, oc, v)
        else:
            put(wo, orow, oc, v, src_color if isinstance(src_color, str) else GREEN)
    if aid not in oaid: oaid[aid] = orow

ws.auto_filter.ref = f"A1:{openpyxl.utils.get_column_letter(ws.max_column)}{ws.max_row}"
wo.auto_filter.ref = f"A1:{openpyxl.utils.get_column_letter(wo.max_column)}{wo.max_row}"

# ---- Reprint info notes (OUTLETRULES-v1: the tab was retired 2026-10-28; skipped when it is not in the workbook)
wi = wb['Reprint info'] if 'Reprint info' in wb.sheetnames else None
for r in (range(1, wi.max_row + 1) if wi is not None else ()):
    k = wi.cell(r, 1).value
    if k == 'Leave empty':
        wi.cell(r, 2).value = '"In Tracker?". Topic, Bills and Reach are filled from the old tracker (Sammy, 2026-10-26); Tone and tone notes may be filled from the tracker.'
    if k == 'Last updated':
        wi.cell(r, 2).value = datetime.date.today().isoformat()
    if k == '# of reprints':
        wi.insert_rows(r + 1)
        wi.cell(r + 1, 1).value = 'Role'
        wi.cell(r + 1, 2).value = ('On Original rows: how Gabriel appears — "Op-ed by Gabriel" (byline names Jesse Gabriel), '
                                   '"Named in headline" (headline or translated headline names Gabriel), else "Mentioned in story". '
                                   'Left blank where the old tracker disagreed; those cases are listed for review.')
        for c in (1, 2):
            wi.cell(r + 1, c).font = copy.copy(wi.cell(r, c).font); wi.cell(r + 1, c).alignment = copy.copy(wi.cell(r, c).alignment)
        break

wb.save(OUT)
rep['next'] = {'ws': nxt['ws'], 'pq': nxt['pq'], 'jg': jg}
json.dump(rep, open(REP, 'w'), indent=1, default=str)
print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in rep.items()}, default=str))
