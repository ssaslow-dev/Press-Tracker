#!/usr/bin/env python3
"""RELTAB-v1 + RELCHECK-v3 (agent-reltab, 2026-10-28; Sammy: "clean up the press release tab ... split the data with
multiple things in one column"). Idempotent (marker per target); runs after patch_relrule.py (4k) as apply_all step 4m.
  python3 -I patch_reltab.py [--sheet-task code/sheet_task.py] [--prompt code/sheet_task_prompt.md]
sheet_task.py (RELCHECK-v3): the "Press releases" tab has one value per cell (code/reltab.py COLS: Legislator 1..6,
  Other official 1..4, Bill 1..6, Contact name/title/phone/email, Tracker release ID 1..2, real dates, In scope, ...). New
  releases are appended in that layout (names from the release text with the same extractor + canonical names the tab was
  cleaned with, bills "AB 1234", contact split, In scope); marking a Coverage row adds its story to the first free Tracker
  release ID column. The old 16-column layout still works (a sheet not yet converted)."""
import argparse, os
MARK_ST, MARK_PR = '# RELTAB-v1 sheet_task', 'RELTAB-v1'

ST_R = [
 ("""try:
    import release_rule as REL       # RELCHECK-v2: the release text rule (release_rule.py next to this script)
except Exception as _e:
    REL = None
""",
  """try:
    import release_rule as REL       # RELCHECK-v2: the release text rule (release_rule.py next to this script)
except Exception as _e:
    REL = None
# RELTAB-v1 sheet_task: layout of the "Press releases" tab, one value per cell (reltab.py next to this script)
try:
    import reltab as RT
except Exception as _e:
    RT = None
"""),
 ("""        ws = wb['Press releases']; H = {c.value: c.column for c in ws[1] if c.value}
        need = ['Date', 'Title', 'Subtitle/dek', 'Source', 'URL', 'Release type', 'Bills mentioned', 'Issue', 'Gabriel quoted',
                'Co-issuers / other members named', 'Contact', 'Word count', 'In tracker', 'Tracker release ID',
                'Coverage stories linked', 'Note']
        if any(c not in H for c in need):
""",
  """        ws = wb['Press releases']; H = {c.value: c.column for c in ws[1] if c.value}
        need = ['Date', 'Title', 'Subtitle/dek', 'Source', 'URL', 'Release type', 'Bills mentioned', 'Issue', 'Gabriel quoted',
                'Co-issuers / other members named', 'Contact', 'Word count', 'In tracker', 'Tracker release ID',
                'Coverage stories linked', 'Note']
        new_layout = RT is not None and RT.is_new_layout(H)   # RELTAB-v1 sheet_task: split layout (reltab.COLS)
        if new_layout:
            need = list(RT.COLS)
        if any(c not in H for c in need):
"""),
 ("""                    'Note': f"Added by the Update button's release check ({self.today})" + ('' if body else '; release page not read')}
            r = ws.max_row + 1
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c)._style = copy.copy(ws.cell(r - 1, c)._style)
            for k, v in vals.items():
                ws.cell(r, H[k]).value = v if v != '' else None
            ws.cell(r, H['URL']).hyperlink = url
""",
  """                    'Note': f"Added by the Update button's release check ({self.today})" + ('' if body else '; release page not read')}
            if new_layout:   # RELTAB-v1 sheet_task: one value per cell
                vals = RT.row_values(d, title, str(x.get('dek', '')).strip(), caucus, url, bills, quoted, RT.officials(body),
                                     cm.group(1).strip() if cm else '', len(body.split()) if body else '', sids,
                                     len(hits) if hits else '', vals['Note'])
            r = ws.max_row + 1
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c)._style = copy.copy(ws.cell(r - 1, c)._style)
            for k, v in vals.items():
                ws.cell(r, H[k]).value = v if v != '' else None
                if new_layout and k in RT.DATE_COLS and v:
                    ws.cell(r, H[k]).number_format = 'yyyy-mm-dd'
            ws.cell(r, H['URL']).hyperlink = url
"""),
 ("""        ids = [x.strip() for x in str(ws.cell(tr, H['Tracker release ID']).value or '').split(';') if x.strip()]
        if sid and sid not in ids:
            ids.append(sid)
        ws.cell(tr, H['In tracker']).value = 'Yes'
        ws.cell(tr, H['Tracker release ID']).value = '; '.join(ids) or None
""",
  """        if 'Tracker release ID 1' in H:   # RELTAB-v1 sheet_task: one story per Tracker release ID column
            k = RT.N_TID if RT is not None else 2
            ids = [str(ws.cell(tr, H[f'Tracker release ID {i}']).value or '').strip() for i in range(1, k + 1)]
            ids = [t for x in ids for t in x.replace(',', ';').split(';') if t.strip()]
            ids = [t.strip() for t in ids]
            if sid and sid not in ids:
                ids.append(sid)
            for i in range(1, k + 1):
                ws.cell(tr, H[f'Tracker release ID {i}']).value = (ids[i - 1] if i < k else '; '.join(ids[k - 1:])) if len(ids) >= i else None
        else:
            ids = [x.strip() for x in str(ws.cell(tr, H['Tracker release ID']).value or '').split(';') if x.strip()]
            if sid and sid not in ids:
                ids.append(sid)
            ws.cell(tr, H['Tracker release ID']).value = '; '.join(ids) or None
        ws.cell(tr, H['In tracker']).value = 'Yes'
"""),
]

PR_R = [
 ("Jewish Caucus releases count only from his chair tenure (2020-11-18).",
  "Jewish Caucus releases count only from his chair tenure (2020-11-18). The tab has one value per cell (RELTAB-v1, `reltab.py`): "
  "Date (real date), Title, Subtitle/dek, Source (one site), URL, Also on caucus site (date/URL), Release type, In scope, Issue, "
  "Gabriel quoted, Caucus release names Gabriel, Word count, Legislator 1..6 + Legislators (more), Other official 1..4 + Other "
  "officials (more), Contact name/title/phone/email, Bill 1..6 + Bills (more), In tracker, Tracker release ID 1..2, Coverage "
  "stories linked, Tracker date (earliest pickup), Before text rule, Note; sheet_task.py fills it that way — never pack several "
  "values into one cell."),
]


# RELTAB-v1b: the sheet task downloads reltab.py with the other pipeline files (sheet_task.py imports it)
MARK_PR2 = 'RELTAB-v1b'
PR2_R = [("`release_rule.py`, `release_texts.json`, ", "`release_rule.py`, `release_texts.json`, `reltab.py` (RELTAB-v1b), ")]


def _apply(path, R, mark):
    if not path or not os.path.exists(path):
        return 'skipped (no file)'
    s = open(path, encoding='utf-8').read()
    if mark in s:
        return 'unchanged'
    for a, b in R:
        n = s.count(a)
        if n != 1:
            raise SystemExit(f'{path}: anchor found {n}x: {a[:80]}')
        s = s.replace(a, b)
    if mark not in s:
        s = s + ('' if s.endswith('\n') else '\n') + ('<!-- ' + mark + ' -->\n' if path.endswith('.md') else '# ' + mark + '\n')
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet-task'); ap.add_argument('--prompt')
    a = ap.parse_args()
    if a.sheet_task: print('sheet_task:', _apply(a.sheet_task, ST_R, MARK_ST))
    if a.prompt: print('prompt:', _apply(a.prompt, PR_R, MARK_PR))
    if a.prompt: print('prompt files:', _apply(a.prompt, PR2_R, MARK_PR2))
