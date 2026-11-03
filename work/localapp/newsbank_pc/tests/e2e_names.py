#!/usr/bin/env python3
"""STATIONNAMES end-to-end: two update zips made by the station from the SAME for-Update file are saved one after the other (sheet_task, the same arguments the
saver gives, on a COPY of the workbook the for-Update file was made from, with the PC's patched pipeline). The first save confirms the station's names; the
second finds its numbers taken, the save gives it the next ones, and take_update.reconcile_names renames the files kept with the update and lists every change.

    python3 -I e2e_names.py ZIP_FIRST ZIP_SECOND WORKBOOK SCRATCH_DIR            (WORKBOOK = the one the for-Update file was made from)
Nothing under data/ or code/ is written."""
import importlib.util, json, re, shutil, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
NBPC = REPO / 'work' / 'localapp' / 'newsbank_pc'
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'updatefolder'))
import take_update as TU, formats as F   # noqa: E402
from layout import PCLayout              # noqa: E402
spec = importlib.util.spec_from_file_location('assemble_app', REPO / 'work' / 'localapp' / 'app' / 'assemble_app.py')
AA = importlib.util.module_from_spec(spec); spec.loader.exec_module(AA)

za, zb, wb, scratch = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
shutil.rmtree(scratch, ignore_errors=True); scratch.mkdir(parents=True)
bad = 0
def check(n, ok, x=''):
    global bad
    bad += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else '  -> ' + str(x)))

pipe = scratch / 'pipe'; pipe.mkdir()
for f in (REPO / 'code').iterdir():
    if f.is_file() and f.suffix in ('.py', '.json', '.csv'):
        shutil.copy2(f, pipe / f.name)
shutil.copy2(REPO / 'work' / 'localapp' / 'winpack' / 'patches' / 'pdftext_pypdf.py', pipe / 'pdftext_pypdf.py')
P = NBPC / 'patches'
for target, patch in (('sheet_task.py', '01_sheet_task_nbpdf.patch'), ('date_rules.py', '02_date_rules_newsbank.patch'), ('pdftext_pypdf.py', '03_pdftext_pypdf_band.patch'),
                      ('sheet_task.py', '04_sheet_task_pqpdf.patch'), ('date_rules.py', '05_date_rules_proquest.patch')):
    AA.patched_copy(pipe / target, pipe / target, P / patch)
(scratch / 'copies' / 'articles').mkdir(parents=True); (scratch / 'copies' / 'articles' / 'manifest.json').write_text('{"articles":{}}')
sid = next((REPO / 'work' / 'localapp' / 'vendor').glob('live_*/pipeline/sid_map.json'))
lay = PCLayout(scratch / 'app'); lay.workbook.parent.mkdir(parents=True); shutil.copy2(wb, lay.workbook)

def save(zp, xlsx, tag):
    ins = TU.inspect_update(zp, lay); stage = Path(ins['stage']); out = scratch / f'out{tag}'; out.mkdir()
    p = subprocess.run([sys.executable, '-I', str(pipe / 'sheet_task.py'), '--db-dir', str(stage / 'db'), '--xlsx', str(xlsx), '--out', str(out / 'out.xlsx'), '--result', str(out / 'result.json'),
                        '--pages-dir', str(out / 'pages'), '--today', '2026-11-03', '--copies', str(scratch / 'copies'), '--idmap', str(sid)], capture_output=True, text=True)
    check(f'update {tag}: sheet_task ran', p.returncode == 0, p.stderr[-500:] + p.stdout[-300:])
    return stage, json.loads((out / 'result.json').read_text()), out

stA, resA, outA = save(za, lay.workbook, 'A')
nmA = json.loads((stA / 'manifest.json').read_text())['names']
rA = TU.reconcile_names(nmA, stA, resA, apply=True)
check('first update: the station named the next free numbers, so the save confirms every name and nothing is renamed', rA['renamed'] == [] and rA['not_saved'] == [] and rA['confirmed'] > 0, rA)
written = sorted(p.relative_to(outA / 'pages').as_posix() for p in (outA / 'pages').rglob('*') if p.is_file())
check('first update: the library files the save wrote are exactly the files the station named', written == sorted(f[len('library/'):] for f in (str(p.relative_to(stA)).replace('\\', '/') for p in (stA / 'library').rglob('*') if p.is_file())), written)
stB, resB, outB = save(zb, outA / 'out.xlsx', 'B')
nmB = json.loads((stB / 'manifest.json').read_text())['names']
check('second update (made from the same for-Update file) named the same first number as the first', nmB['from_next'] == nmA['from_next'] and nmB['items'][0]['aid'] == nmA['items'][0]['aid'], (nmB['from_next'], nmA['from_next']))
before = sorted(str(p.relative_to(stB)).replace('\\', '/') for p in (stB / 'library').rglob('*') if p.is_file())
rB = TU.reconcile_names(nmB, stB, resB, apply=True)
check('second update: its numbers are moved on, every file is listed as renamed, none left under the old name',
      rB['renamed'] and rB['confirmed'] == 0 and not any((stB / Path(*r['from'].split('/'))).exists() for r in rB['renamed']) and all((stB / Path(*r['to'].split('/'))).is_file() for r in rB['renamed']), rB)
check('second update: the first free Article ID after the first update is the one it got', all(int(r['aid']) < int(re.search(r'(\d{5})', r['to'].rsplit('/', 1)[-1]).group(1)) for r in rB['renamed']) and 'Article ID' in rB['renamed'][0]['why'], rB['renamed'][:2])
writtenB = sorted(p.relative_to(outB / 'pages').as_posix() for p in (outB / 'pages').rglob('*') if p.is_file())
afterB = sorted(str(p.relative_to(stB / 'library')).replace('\\', '/') for p in (stB / 'library').rglob('*') if p.is_file())
check('second update: after the renames every file the save wrote to the library is in the update folder under the same name (workbook and library match); the rest are raw pages the save did not keep', set(writtenB) <= set(afterB) and set(afterB) - set(writtenB) == {x[len('library/'):] for x in rB['raw_not_kept']}, (writtenB, afterB, rB['raw_not_kept']))
import openpyxl
ws = openpyxl.load_workbook(outB / 'out.xlsx', read_only=True)['Coverage']; rows = list(ws.iter_rows(values_only=True)); ix = {c: i for i, c in enumerate(rows[0])}
fn = {str(r[ix['File name']]) for r in rows[1:] if r[ix['File name']]}
check('second update: every file the save wrote has its File name in the workbook', all(Path(w).name in fn for w in writtenB if not w.startswith('_original')), [Path(w).name for w in writtenB if Path(w).name not in fn][:3])
print('all passed' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)
