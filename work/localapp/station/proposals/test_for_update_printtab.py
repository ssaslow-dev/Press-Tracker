"""PROPOSAL test (not applied to work/localapp/updatefolder): for_update_printtab.patch makes the for-Update file carry (a) a `files` column in the rows block and (b) one kind-'P' row
per "Unlinked print pages" row with a print-page link. Applies the patch to a COPY of make_for_update.py, runs extend_rows on the snapshot workbook and a stand-in rows block.
    python3 -I work/localapp/station/proposals/test_for_update_printtab.py [WORKBOOK]"""
import importlib.util, shutil, subprocess, sys, tempfile
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
wb = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / 'data' / 'AJG Coverage - NewsBank.xlsx'
bad = 0
def check(n, ok, x=''):
    global bad; bad += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else '  -> ' + str(x)))
with tempfile.TemporaryDirectory() as t:
    t = Path(t); (t / 'work' / 'localapp' / 'updatefolder').mkdir(parents=True)
    for f in (REPO / 'work' / 'localapp' / 'updatefolder').glob('*.py'):
        shutil.copy2(f, t / 'work' / 'localapp' / 'updatefolder' / f.name)
    p = subprocess.run(['patch', '-p1', '-i', str(REPO / 'work' / 'localapp' / 'station' / 'proposals' / 'for_update_printtab.patch')], cwd=t, capture_output=True, text=True)
    check('the patch applies cleanly to the current make_for_update.py', p.returncode == 0, p.stdout + p.stderr)
    d = t / 'work' / 'localapp' / 'updatefolder'; sys.path.insert(0, str(d))
    spec = importlib.util.spec_from_file_location('mfu_patched', d / 'make_for_update.py'); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    import openpyxl
    w = openpyxl.load_workbook(wb, read_only=True, data_only=True)
    cov = list(w['Coverage'].iter_rows(values_only=True)); ch = cov[0]; ci = {h: i for i, h in enumerate(ch)}
    sample = [r for r in cov[1:200] if r[ci['Article ID']]]
    block = {'cols': ['aid', 'sid', 'kind', 'outlet', 'date', 'hl', 'links'], 'rows': [[str(r[ci['Article ID']]), str(r[ci['Story ID']] or ''), 'O', str(r[ci['Outlet']] or ''), '', '', []] for r in sample], 'next': {'aid': 1}}
    out = M.extend_rows(block, wb)
    up = list(w['Unlinked print pages'].iter_rows(values_only=True)); ui = {h: i for i, h in enumerate(up[0])}
    want = [r for r in up[1:] if r[ui['Article ID']] and (r[ui['NewsBank print-page link']] or r[ui['NewsBank print article link']])]
    prow = [r for r in out['rows'] if r[2] == 'P']
    check('the rows block gains a `files` column, one value per row', out['cols'][-1] == 'files' and all(len(r) == len(out['cols']) for r in out['rows']), out['cols'])
    check('one kind-P row per Unlinked print pages row with a print-page link (%d)' % len(want), len(prow) == len(want) and len(want) > 1000, (len(prow), len(want)))
    one = next(r for r in prow if r[0] == '05432')
    check('row 05432: Inland Valley Daily Bulletin, 2026-10-04, its print-page link', one[3] == 'Inland Valley Daily Bulletin' and one[4] == '2026-10-04' and 'docref=image/v2%3A183FBD71DC75BC70' in one[6][0], one)
    withfile = [r for r in out['rows'] if r[2] != 'P' and r[-1]]
    check('Coverage rows carry their saved-copy names (File name; File name 2; Other files) in `files`', len(withfile) > 50 and any(r[-1].lower().endswith('.pdf') for r in withfile) and any('nb' in r[-1] for r in withfile), len(withfile))
    check('no article text anywhere in the added data (names and links only)', all(len(str(r[-1])) < 400 for r in out['rows']))
    again = M.extend_rows(out, wb)
    check('running it twice changes nothing', again is out or again == out)
print('all passed' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)
