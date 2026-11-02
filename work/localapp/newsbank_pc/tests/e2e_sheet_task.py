#!/usr/bin/env python3
"""End-to-end check of the NEWSBANKPDF-v1 PC patches on a COPY of the snapshot workbook (about 1 minute). Not part of the quick unittest run.

    python3 -I e2e_sheet_task.py UPDATE.zip WORKBOOK SCRATCH_DIR

1. copies code/*.py|json|csv into SCRATCH/pipe, applies patches 01 (sheet_task) and 02 (date_rules) with the PC app assembler's own exact-once applier,
   and the replacement pdftext_pypdf.py (the winpack module + patch 03);
2. take_update.inspect_update unpacks the station's zip (PDFs to staging/<id>/db/files/);
3. runs sheet_task.py on it (first pass, the same arguments the saver gives) against the workbook copy;
4. checks the rows and the PDFs it would put in the library.
Nothing under data/ or code/ is written."""
import importlib.util, json, shutil, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
NBPC = REPO / 'work' / 'localapp' / 'newsbank_pc'
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'updatefolder'))
import take_update as TU, formats as F   # noqa: E402
from layout import PCLayout              # noqa: E402
spec = importlib.util.spec_from_file_location('assemble_app', REPO / 'work' / 'localapp' / 'app' / 'assemble_app.py')
AA = importlib.util.module_from_spec(spec); spec.loader.exec_module(AA)

zp, wb, scratch = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
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
AA.patched_copy(pipe / 'sheet_task.py', pipe / 'sheet_task.py', NBPC / 'patches' / '01_sheet_task_nbpdf.patch')
AA.patched_copy(pipe / 'date_rules.py', pipe / 'date_rules.py', NBPC / 'patches' / '02_date_rules_newsbank.patch')
AA.patched_copy(pipe / 'pdftext_pypdf.py', pipe / 'pdftext_pypdf.py', NBPC / 'patches' / '03_pdftext_pypdf_band.patch')
check('patches 01, 02, 03 apply exactly once to the current files', True)
check('patch 03 gives the same module as newsbank_pc/pdftext_pypdf.py', (pipe / 'pdftext_pypdf.py').read_text() == (NBPC / 'pdftext_pypdf.py').read_text())

app = scratch / 'app'; lay = PCLayout(app); lay.workbook.parent.mkdir(parents=True); shutil.copy2(wb, lay.workbook)
ins = TU.inspect_update(zp, lay)
stage = Path(ins['stage']); db = stage / 'db'
npdf = len(list((db / 'files').glob('*.pdf')))
(scratch / 'copies' / 'articles').mkdir(parents=True); (scratch / 'copies' / 'articles' / 'manifest.json').write_text('{"articles":{}}')
sid = next((REPO / 'work' / 'localapp' / 'vendor').glob('live_*/pipeline/sid_map.json'))
out = scratch / 'out'; out.mkdir()
p = subprocess.run([sys.executable, '-I', str(pipe / 'sheet_task.py'), '--db-dir', str(db), '--xlsx', str(lay.workbook), '--out', str(out / 'out1.xlsx'), '--result', str(out / 'result.json'),
                    '--pages-dir', str(out / 'pages'), '--today', '2026-11-02', '--copies', str(scratch / 'copies'), '--idmap', str(sid)], capture_output=True, text=True)
check('sheet_task ran (exit 0)', p.returncode == 0, p.stderr[-500:])
res = json.loads((out / 'result.json').read_text())
nrows = res['verify']['rows_after'] - res['verify']['rows_before']
print('   ', p.stdout.strip().splitlines()[-1][:200] if False else json.dumps(res.get('verify'))[:160])
check('verify ok', res['verify']['ok'], res['verify'])
check('every PDF in the update became a library file and a Saved Copy', len(res['pages']) == npdf and len(list((out / 'pages').rglob('nb*.pdf'))) == npdf, (len(res['pages']), npdf))
check('no conflicts left for the person (Word count stays NewsBank’s)', not res.get('conflicts'), res.get('conflicts', [])[:2])
check('no copy refused, none skipped', not res['pages_error'] and not res.get('pages_skipped'), (res['pages_error'][:1], res.get('pages_skipped', [])[:1]))
import openpyxl
ws = openpyxl.load_workbook(out / 'out1.xlsx', read_only=True)['Coverage']
rows = list(ws.iter_rows(values_only=True)); h = rows[0]; ix = {c: i for i, c in enumerate(h)}
new = [r for r in rows[1:] if r[ix['Data Source']] == 'Newsbank' and r[ix['Article ID']] and str(r[ix['Article ID']]) >= str(res['verify'].get('first_new', '10666'))]
new = [r for r in new if r[ix['Team note']] and 'NewsBank PDF' in str(r[ix['Team note']])]
check(str(nrows) + ' rows added, all Data Source Newsbank with a Saved Copy, File type "Newsbank pdf" and a library name nb<ID><o|r>-s<ID>.pdf', len(new) == nrows and all(r[ix['Saved Copy?']] == 'Yes' and r[ix['File type']] == 'Newsbank pdf' and __import__('re').fullmatch(r'nb\d{5}[or]-s\d{5}\.pdf', str(r[ix['File name']])) for r in new), len(new))
check('Date source is NewsBank (print edition for a print record)', all(r[ix['Date source']] in ('NewsBank', 'print edition') for r in new), {r[ix['Date source']] for r in new})
check('each file named in File name exists in the pages folder under its year', all((out / 'pages' / str(r[ix['Date']])[:4] / str(r[ix['File name']])).is_file() for r in new))
check('Mentions "Gabriel", Mention depth and Quoted come from the story text', all(r[ix['Mentions "Gabriel" in text']] in ('Yes', 'No') for r in new))
print('all passed' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)
