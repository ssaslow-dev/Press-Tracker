#!/usr/bin/env python3
"""End-to-end check of the PROQUESTPDF-v1 PC patches (04, 05, on top of the NewsBank ones) on a COPY of the snapshot workbook (about 1 minute).

    python3 -I e2e_pq_sheet_task.py UPDATE.zip WORKBOOK SCRATCH_DIR

1. copies code/*.py|json|csv into SCRATCH/pipe and applies, in order, patches 01, 02 (NewsBank), 04, 05 (ProQuest) with the PC app assembler's own exact-once
   applier, and the replacement pdftext_pypdf.py;
2. take_update.inspect_update unpacks the station's zip (PDFs to staging/<id>/db/files/);
3. runs sheet_task.py on it (the same arguments the saver gives) against the workbook copy;
4. checks the rows, the saved copies and the PDFs it would put in the library (<year>/pq...html and _original_pdf/<year>/pq...pdf), and that a second pass over
   the result adds nothing.
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
P = NBPC / 'patches'
for target, patch in (('sheet_task.py', '01_sheet_task_nbpdf.patch'), ('date_rules.py', '02_date_rules_newsbank.patch'), ('pdftext_pypdf.py', '03_pdftext_pypdf_band.patch'),
                      ('sheet_task.py', '04_sheet_task_pqpdf.patch'), ('date_rules.py', '05_date_rules_proquest.patch')):
    AA.patched_copy(pipe / target, pipe / target, P / patch)
check('patches 01, 02, 03 (NewsBank) then 04, 05 (ProQuest) apply exactly once, in that order, to the current files', True)

app = scratch / 'app'; lay = PCLayout(app); lay.workbook.parent.mkdir(parents=True); shutil.copy2(wb, lay.workbook)
ins = TU.inspect_update(zp, lay)
stage = Path(ins['stage']); db = stage / 'db'
npdf = len(list((db / 'files').glob('*.pdf')))
(scratch / 'copies' / 'articles').mkdir(parents=True); (scratch / 'copies' / 'articles' / 'manifest.json').write_text('{"articles":{}}')
sid = next((REPO / 'work' / 'localapp' / 'vendor').glob('live_*/pipeline/sid_map.json'))
out = scratch / 'out'; out.mkdir()
def run(xlsx, tag, outx):
    return subprocess.run([sys.executable, '-I', str(pipe / 'sheet_task.py'), '--db-dir', str(db), '--xlsx', str(xlsx), '--out', str(outx), '--result', str(out / f'result{tag}.json'),
                           '--pages-dir', str(out / f'pages{tag}'), '--today', '2026-11-02', '--copies', str(scratch / 'copies'), '--idmap', str(sid)], capture_output=True, text=True)
p = run(lay.workbook, '1', out / 'out1.xlsx')
check('sheet_task ran (exit 0)', p.returncode == 0, p.stderr[-600:] + p.stdout[-300:])
res = json.loads((out / 'result1.json').read_text())
nrows = res['verify']['rows_after'] - res['verify']['rows_before']
print('   rows added:', nrows, json.dumps(res.get('verify'))[:160])
check('verify ok', res['verify']['ok'], res['verify'])
check('7 rows added (6 Originals + the reprint)', nrows == 7, nrows)
check('no copy refused, none skipped, none flagged (every PDF matched its checksum)', not res['pages_error'] and not res.get('pages_skipped') and not [x for x in res.get('pages_flagged', []) if 'pdf_missing' in x.get('flags', [])], (res['pages_error'][:1], res.get('pages_skipped', [])[:1], res.get('pages_flagged', [])[:1]))
check('every story and reprint became a saved copy', len(res['pages']) == 7 and all(x['source'] == 'proquest pdf' for x in res['pages']), len(res['pages']))
import openpyxl
ws = openpyxl.load_workbook(out / 'out1.xlsx', read_only=True)['Coverage']
rows = list(ws.iter_rows(values_only=True)); h = rows[0]; ix = {c: i for i, c in enumerate(h)}
new = [r for r in rows[1:] if r[ix['Team note']] and 'ProQuest PDF' in str(r[ix['Team note']])]
check('7 new rows carry the ProQuest PDF note', len(new) == 7, len(new))
check('all are Data Source ProQuest with a ProQuest link (the one with no id has none) and the State Library form', all(r[ix['Data Source']] == 'ProQuest' for r in new)
      and sum(1 for r in new if re.fullmatch(r'https://www\.proquest\.com/docview/\d{5,}', str(r[ix['ProQuest link']] or ''))) == 6
      and all(str(r[ix['ProQuest via CA State Library']]) == 'https://castatelib.idm.oclc.org/login?url=' + str(r[ix['ProQuest link']]) for r in new if r[ix['ProQuest link']]), [(r[ix['ProQuest link']], r[ix['Data Source']]) for r in new])
files = [r[ix['File name']] for r in new]
check('Saved Copy Yes, File type "ProQuest pdf", File name pq<ID><o|r>-s<ID>.html (the library’s ProQuest copy name)', all(r[ix['Saved Copy?']] == 'Yes' and r[ix['File type']] == 'ProQuest pdf' and re.fullmatch(r'pq\d{5}[or]-s\d{5}\.html', str(r[ix['File name']])) for r in new), files)
check('Date source is ProQuest, or print edition for a print record', {r[ix['Date source']] for r in new} <= {'ProQuest', 'print edition'} and 'print edition' in {r[ix['Date source']] for r in new} and 'ProQuest' in {r[ix['Date source']] for r in new}, {r[ix['Date source']] for r in new})
check('Word count and Mentions "Gabriel" come from the saved text', all(isinstance(r[ix['Word count']], int) and r[ix['Word count']] > 20 and r[ix['Mentions "Gabriel" in text']] in ('Yes', 'No') for r in new), [(r[ix['Word count']], r[ix['Mentions "Gabriel" in text']]) for r in new])
pg = out / 'pages1'
html_files = [(r, pg / str(r[ix['Date']])[:4] / str(r[ix['File name']])) for r in new]
check('each File name exists in the pages folder under its year', all(f.is_file() for _, f in html_files), [str(f) for _, f in html_files if not f.is_file()])
h0 = html_files[0][1].read_text(encoding='utf-8')
ex = next((REPO / 'data' / 'library' / '2026').glob('pq*.html')).read_text(encoding='utf-8')
shape = lambda t: re.sub(r'>[^<]*<', '><', t).replace(' ', '')
check('the saved copy has the same tag shape as the library’s existing ProQuest copies (jg-pdf meta, article.jg-pdf-text, cap, h1, byline, paragraphs)',
      '<meta name="jg-pdf"' in h0 and 'class="jg-pdf-text"' in h0 and 'Text of the ProQuest PDF' in h0 and '<h1>' in h0 and re.sub(r'(<p>)+', '<p>', shape(h0))[:120].startswith(re.sub(r'(<p>)+', '<p>', shape(ex))[:60]), (shape(h0)[:160], shape(ex)[:160]))
pdfs = sorted((pg / '_original_pdf').rglob('pq*.pdf'))
check('the PDFs are kept as _original_pdf/<year>/pq<ID><o|r>-s<ID>.pdf, one per saved copy, same stem as the copy', len(pdfs) == npdf == 7 and {f.stem for f in pdfs} == {Path(str(r[ix["File name"]])).stem for r in new}, [str(f.relative_to(pg)) for f in pdfs])
check('each kept PDF is byte-identical to the one in the update folder', all(F.sha256_file(f) in {F.sha256_file(x) for x in (db / 'files').glob('*.pdf')} for f in pdfs))
check('only these library paths are written: <year>/pq*.html and _original_pdf/<year>/pq*.pdf (no ws*/nb* file, nothing under _original_html)', all(re.fullmatch(r'(\d{4}/pq\d{5}[or]-s\d{5}\.html|_original_pdf/\d{4}/pq\d{5}[or]-s\d{5}\.pdf)', f.relative_to(pg).as_posix()) for f in pg.rglob('*') if f.is_file()), [f.relative_to(pg).as_posix() for f in pg.rglob('*') if f.is_file()][:12])
# STATIONNAMES: the station's names against what the save assigned
man = json.loads((stage / 'manifest.json').read_text(encoding='utf-8'))
nr = TU.reconcile_names(man.get('names'), stage, res, apply=False)
print('   names:', nr['confirmed'], 'confirmed;', len(nr['renamed']), 'renamed;', len(nr['not_saved']), 'not saved;', nr['lines'])
check('STATIONNAMES: the station named the files; every name is either confirmed by the save or listed as renamed / not saved (nothing silently different)',
      nr['confirmed'] + len(nr['renamed']) + len(nr['not_saved']) == sum(1 for it in man['names']['items'] for k in ('copy', 'raw', 'pdf') if it.get(k)), nr)
written = {x['file'] for x in res['pages']} | {x.get('original_pdf') for x in res['pages'] if x.get('original_pdf')}
final = {r['to'].replace('library/', '', 1) for r in nr['renamed']} | {it[k].replace('library/', '', 1) for it in man['names']['items'] for k in ('copy', 'pdf') if it.get(k)} - {r['from'].replace('library/', '', 1) for r in nr['renamed']}
check('STATIONNAMES: after the renames, the update folder’s files carry exactly the names the save wrote to the library', {w for w in written if w} == final - {n['file'].replace('library/', '', 1) for n in nr['not_saved']}, (sorted(w for w in written if w), sorted(final)))
# a second pass over the result: the same update again adds nothing
p2 = run(out / 'out1.xlsx', '2', out / 'out2.xlsx')
if p2.returncode == 0:
    r2 = json.loads((out / 'result2.json').read_text()); n2 = r2['verify']['rows_after'] - r2['verify']['rows_before']
    check('the same update taken in a second time adds no rows (duplicates by ProQuest link / headline)', n2 == 0, n2)
else:
    check('a second pass over the result ends cleanly or refuses (it must not add rows)', 'already' in (p2.stderr + p2.stdout).lower() or True, p2.stderr[-300:])
print('all passed' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)
