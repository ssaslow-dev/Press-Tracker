#!/usr/bin/env python3
"""OUTLETRULES-v1 (agent-instructions2, 2026-10-28; Sammy: the retired "Reprint info" / "Audit plan" tabs only FILL GAPS,
D1 approved; coordinator: new fills are default black, DECISIONS 102). Idempotent (one marker per target); apply_all step 4q,
after 4o (relcopies).

  python3 -I patch_outletrules.py --root L

Targets (each skipped when its marker is already there):
  code/sheet_task.py   norm_outlet(name, city='') reads outlet_rules.json (next to the script; built-in fallback = no extra
        rules): accents folded; "Today's Edition" with or without parentheses and ": Blogs" stripped, ", The" stripped before
        ":" / "/" / end (fixes "Sacramento Bee Today's Edition, The" and "Sacramento Bee, The: Blogs", which stayed separate
        outlets); feed prefixes (Associated Press ..., Targeted News Service ...) fold to one outlet; generic names
        (Times, Herald, Tribune ...) become "name@city" from Outlet city; aliases map variants to one key. Callers (same-outlet
        dedupe in reprint_check, Reach consensus, recount) pass the row's Outlet city. Sheet.put writes the default (black)
        font instead of green (DECISIONS 102). Docstrings re-pointed from the Reprint info tab to outlet_rules.json.
  code/sheet_task_prompt.md          pipeline file list += outlet_rules.json
  build/sheet_task_prompt_final.md   rule 4: default black font, not green
  code/apply_fills.py  comment re-pointed (Reprint info tab -> outlet_rules.json); retired one-off, behaviour unchanged
  code/prep_workbook.py, code/migrate_ids.py  retired one-offs that wrote the Reprint info / Audit plan tabs: skip a tab that
        is not in the workbook (if tab in wb.sheetnames) instead of a KeyError
(apply_all_patches.py itself carries the step-4q call, outlet_rules.json in PIPELINE and the helper copies.)
"""
import argparse, os

MARK = 'OUTLETRULES-v1'

NORM_OLD = '''def norm_outlet(s):
    s = (s or '').lower().strip()
    s = re.sub(r"\\s*:\\s*blogs$|\\s*\\(today's edition\\)$|, the$|^the\\s+", '', s)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()
'''
NORM_NEW = '''# OUTLETRULES-v1 (agent-instructions2, 2026-10-28): outlet matching rules from the retired "Reprint info" tab, kept in
# outlet_rules.json next to this script (feeds, aliases, generic names by city, keep_separate test pairs). Missing file =
# the normalization below without extra rules.
import os as _os, unicodedata as _ud


def _load_outlet_rules():
    try:
        return json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'outlet_rules.json'), encoding='utf-8'))
    except (OSError, ValueError):
        return {}


OUTLET_RULES = _load_outlet_rules()


def _outlet_base(s):
    """lower case, accents folded, "Today's Edition" (with or without parentheses), ": Blogs", ", The" and a leading "The"
    removed, punctuation -> space"""
    s = str(s or '').replace('\\u2019', "'").replace('\\u2018', "'")
    s = _ud.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().strip()
    s = re.sub(r"\\s*:\\s*blogs\\s*$", '', s)
    s = re.sub(r"\\s*\\(?\\btoday'?s edition\\b\\)?", '', s)
    s = re.sub(r",\\s*the(?=\\s*(?::|/|$))", '', s)
    s = re.sub(r"^the\\s+", '', s.strip())
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def norm_outlet(s, city=''):
    """one key per outlet (OUTLETRULES-v1): feeds fold to their outlet, generic names are one outlet per Outlet city
    ("times@london"), aliases (outlet_rules.json) map variants to the outlet's key"""
    b = _outlet_base(s)
    if not b:
        return ''
    R = OUTLET_RULES
    for pre, key in (R.get('feeds') or {}).items():
        if b == pre or b.startswith(pre + ' '):
            return key
    k = b
    if b in set(R.get('generic_needs_city') or ()):
        c = _outlet_base(city)
        if c:
            k = b + '@' + c
    return (R.get('aliases') or {}).get(k, k)
'''

ST = [
    ("  * every value written is in the existing green (000B8A3E).\n",
     "  * every value written is in the default (automatic black) font (DECISIONS 102; was green 000B8A3E until OUTLETRULES-v1).\n"),
    ("""        cell.font = Font(name=f.name, sz=f.sz, b=f.b, i=f.i, u=f.u, strike=f.strike,
                         vertAlign=f.vertAlign, color=GREEN)
""",
     """        cell.font = Font(name=f.name, sz=f.sz, b=f.b, i=f.i, u=f.u, strike=f.strike,
                         vertAlign=f.vertAlign)   # OUTLETRULES-v1: default black (DECISIONS 102), was color=GREEN
"""),
    (NORM_OLD, NORM_NEW),
    ("""            same = {norm_outlet(self.s.get(x, 'Outlet')) for x in self.s.story_rows.get(target, [])} | {norm_outlet(c.get('Outlet'))}
            if norm_outlet(o.get('Outlet')) in same - {''}:
""",
     """            same = ({norm_outlet(self.s.get(x, 'Outlet'), self.s.get(x, 'Outlet city')) for x in self.s.story_rows.get(target, [])}
                    | {norm_outlet(c.get('Outlet'), c.get('Outlet city'))})   # OUTLETRULES-v1: city for generic names
            if norm_outlet(o.get('Outlet'), o.get('Outlet city')) in same - {''}:
"""),
    ("""    def reach_for(self, outlet):
""", """    def reach_for(self, outlet, city=''):   # OUTLETRULES-v1: city for generic names
"""),
    ("""                    d = self._reach.setdefault(norm_outlet(self.s.get(r, 'Outlet')), {})
""", """                    d = self._reach.setdefault(norm_outlet(self.s.get(r, 'Outlet'), self.s.get(r, 'Outlet city')), {})
"""),
    ("""        d = self._reach.get(norm_outlet(outlet), {})
""", """        d = self._reach.get(norm_outlet(outlet, city), {})
"""),
    ("""            cons, seen = self.reach_for(vals.get('Outlet'))
""", """            cons, seen = self.reach_for(vals.get('Outlet'), vals.get('Outlet city'))
"""),
    ("""        in the story). Keeps the count built under the Reprint info rules (outlet aliases,
        editions) instead of recomputing it with a cruder outlet match.\"\"\"
""", """        in the story). Outlets are matched by norm_outlet with the row's Outlet city (outlet_rules.json,
        OUTLETRULES-v1: aliases, editions, feeds, generic names by city; the former Reprint info tab rules).\"\"\"
"""),
    ("""            seen = {norm_outlet(self.s.get(r, 'Outlet')) for r in old_rows} | {norm_outlet(self.s.get(o, 'Outlet'))}
            add = {norm_outlet(self.s.get(r, 'Outlet')) for r in new_rows} - seen - {''}
""", """            no = lambda r: norm_outlet(self.s.get(r, 'Outlet'), self.s.get(r, 'Outlet city'))   # OUTLETRULES-v1
            seen = {no(r) for r in old_rows} | {no(o)}
            add = {no(r) for r in new_rows} - seen - {''}
"""),
]
LEAN = [("`reprint_rule.py`, `release_rule.py`,", "`reprint_rule.py`, `outlet_rules.json` (OUTLETRULES-v1), `release_rule.py`,")]
FINAL = [("4. New values are written in green (000B8A3E). sheet_task.py does this.",
          "4. New values are written in the default black font (DECISIONS 102; OUTLETRULES-v1). sheet_task.py does this.")]
AF = [("(exact name, NewsBank style, or a Reprint info tab variant; generic names only with the same city) agrees.",
       "(exact name, NewsBank style, or an outlet variant now in outlet_rules.json (OUTLETRULES-v1; formerly the Reprint info\n"
       "# tab); generic names only with the same city) agrees.")]
PREP = [("""# ---- Reprint info notes
wi = wb['Reprint info']
for r in range(1, wi.max_row + 1):
""", """# ---- Reprint info notes (OUTLETRULES-v1: the tab was retired 2026-10-28; skipped when it is not in the workbook)
wi = wb['Reprint info'] if 'Reprint info' in wb.sheetnames else None
for r in (range(1, wi.max_row + 1) if wi is not None else ()):
""")]
MIG = [("""            cell = wb[t][c]
            if cell.value == old:
""", """            if t not in wb.sheetnames:   # OUTLETRULES-v1: Reprint info / Audit plan retired 2026-10-28
                rep['problems'].append(f'--docs: tab {t} not in the workbook (retired 2026-10-28), skipped'); continue
            cell = wb[t][c]
            if cell.value == old:
""")]


def _apply(path, R, mark=MARK):
    if not os.path.exists(path):
        return 'skipped (no file)'
    s = open(path, encoding='utf-8').read()
    if mark in s:
        return 'unchanged'
    for a, b in R:
        n = s.count(a)
        if n != 1:
            raise SystemExit(f'{path}: anchor found {n}x: {a[:90]!r}')
        s = s.replace(a, b)
    if mark not in s:
        s += ('' if s.endswith('\n') else '\n') + ('<!-- ' + mark + ' -->\n' if path.endswith('.md') else '# ' + mark + '\n')
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', required=True)
    a = ap.parse_args(argv)
    P = lambda rel: os.path.join(a.root, rel)
    for rel, R in (('code/sheet_task.py', ST), ('code/sheet_task_prompt.md', LEAN), ('build/sheet_task_prompt_final.md', FINAL),
                   ('code/apply_fills.py', AF), ('code/prep_workbook.py', PREP), ('code/migrate_ids.py', MIG)):
        print(f'{MARK} {rel}: {_apply(P(rel), R)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
