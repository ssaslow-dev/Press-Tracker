#!/usr/bin/env python3
"""End-to-end check of the NEWSBANKPDF-v1 PC patches on a COPY of the snapshot workbook (about 1 minute). Not part of the quick unittest run.

    python3 -I e2e_sheet_task.py UPDATE.zip WORKBOOK SCRATCH_DIR

1. copies code/*.py|json|csv into SCRATCH/pipe, applies patches 01 (sheet_task) and 02 (date_rules) with the PC app assembler's own exact-once applier,
   and the replacement pdftext_pypdf.py (the winpack module + patch 03);
2. take_update.inspect_update unpacks the station's zip (PDFs to staging/<id>/db/files/);
3. runs sheet_task.py on it (first pass, the same arguments the saver gives) against the workbook copy;
4. checks the rows and the PDFs it would put in the library.
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
AA.patched_copy(pipe / 'sheet_task.py', pipe / 'sheet_task.py', NBPC / 'patches' / '01_sheet_task_nbpdf.patch')
AA.patched_copy(pipe / 'date_rules.py', pipe / 'date_rules.py', NBPC / 'patches' / '02_date_rules_newsbank.patch')
AA.patched_copy(pipe / 'pdftext_pypdf.py', pipe / 'pdftext_pypdf.py', NBPC / 'patches' / '03_pdftext_pypdf_band.patch')
AA.patched_copy(pipe / 'sheet_task.py', pipe / 'sheet_task.py', NBPC / 'patches' / '07_sheet_task_prjudge2.patch')    # PRJUDGE-v2: honours the station's No for other issuers' items
AA.patched_copy(pipe / 'date_rules.py', pipe / 'date_rules.py', NBPC / 'patches' / '08_date_rules_airdate.patch')      # NBTV-v1: Date source "air date (Pacific)"
AA.patched_copy(pipe / 'sheet_task.py', pipe / 'sheet_task.py', NBPC / 'patches' / '09_sheet_task_printpages.patch')   # PRINTPAGES-v1 / ORIGCOPIES-v1: print originals, Unlinked print pages rows, extra copies
AA.patched_copy(pipe / 'sheet_task.py', pipe / 'sheet_task.py', REPO / 'work' / 'localapp' / 'app' / 'patches' / '25_sheet_task_otherfiles.patch')   # OTHERFILES-v1: the ONE handler of a run's extra_copies (REVIEW_3 finding 1)
AA.patched_copy(pipe / 'sheet_task.py', pipe / 'sheet_task.py', REPO / 'work' / 'localapp' / 'app' / 'patches' / '28_sheet_task_prcolor.patch')   # PRCOLOR-v1: Press release = Yes rows are purple
check('patches 01, 02, 03, 07, 08, 09, 25, 28 apply exactly once to the current files', True)
check('patch 03 gives the same module as newsbank_pc/pdftext_pypdf.py', (pipe / 'pdftext_pypdf.py').read_text() == (NBPC / 'pdftext_pypdf.py').read_text())

app = scratch / 'app'; lay = PCLayout(app); lay.workbook.parent.mkdir(parents=True); shutil.copy2(wb, lay.workbook)
import openpyxl as _ox0
_b0 = _ox0.load_workbook(lay.workbook)    # after switch-over day the workbook has the "Other files" column (OTHERFILES-v1)
for _t0 in ('Coverage', 'Originals'):
    _b0[_t0].cell(1, _b0[_t0].max_column + 1).value = 'Other files'
_b0.save(lay.workbook); _b0.close()
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
_runs0 = [json.loads(f.read_text()) for f in (db / 'runs').glob('*.json')]
_nprint = sum(len(x.get('print_rows') or []) for x in _runs0); _ncopy = len({c['file'] for x in _runs0 for c in (x.get('extra_copies') or [])})
check('every story PDF in the update became a library file and a Saved Copy (the update also holds ' + str(_nprint) + ' print page PDF and ' + str(_ncopy) + ' extra-copy PDF, kept as originals below)', len(res['pages']) == npdf - _nprint - _ncopy and len(list((out / 'pages').glob('*/nb*.pdf'))) == npdf - _nprint - _ncopy, (len(res['pages']), npdf, _nprint, _ncopy))
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
# PRJUDGE-v1: a row the station judged a pure press release (Team note "press release: <reason>", Press release = Yes in the run doc) is Press release = Yes in the sheet
pr = [r for r in new if 'press release:' in str(r[ix['Team note']])]
check('PRJUDGE: the story the station judged a press release (' + str(len(pr)) + ') is Press release = Yes in the sheet, with the reason in its Team note', len(pr) >= 1 and all(r[ix['Press release']] == 'Yes' for r in pr), [(r[ix['Headline']], r[ix['Press release']]) for r in pr])
check('PRJUDGE: the other new rows are not marked (fill blanks: the station only says Yes)', all(r[ix['Press release']] in (None, '', 'No') for r in new if r not in pr), [(r[ix['Headline']], r[ix['Press release']]) for r in new if r not in pr and r[ix['Press release']] not in (None, '', 'No')][:3])
# PRCOLOR-v1: every cell of a row with Press release = Yes is purple (7030A0), not red; rows the tracker hides for other reasons stay red
_full = openpyxl.load_workbook(out / 'out1.xlsx')['Coverage']; _hd = [c.value for c in _full[1]]; _pi = _hd.index('Press release'); _ai = _hd.index('Article ID')
_prows = [r for r in range(2, _full.max_row + 1) if str(_full.cell(r, _ai + 1).value or '') in {str(x[ix['Article ID']]) for x in pr}]
_col = lambda r: {str(_full.cell(r, c).font.color.rgb if _full.cell(r, c).font and _full.cell(r, c).font.color else '') for c in range(1, len(_hd) + 1)}
check('PRCOLOR: the Press release = Yes rows the save added are purple across the whole row (' + str(len(_prows)) + ')', len(_prows) >= 1 and all(_col(r) == {'007030A0'} for r in _prows), [_col(r) for r in _prows][:2])
# PRJUDGE-v2 (patch 07): the same update with the station's verdict for the wire-named row changed to No (its text is not a release): the save must not mark it Yes by the outlet name
db2 = scratch / 'db2'; shutil.copytree(db, db2)
for rf in (db2 / 'runs').glob('*.json'):
    d = json.loads(rf.read_text())
    for o in d['rows']:
        if str(o.get('Outlet')) == 'Targeted News Service' and isinstance(o.get('_pr'), dict):
            o['_pr'] = dict(o['_pr'], v='no', why='from a release wire, but its text is not a release'); o['Press release'] = ''
    rf.write_text(json.dumps(d))
out2 = scratch / 'out2'; out2.mkdir()
p2 = subprocess.run([sys.executable, '-I', str(pipe / 'sheet_task.py'), '--db-dir', str(db2), '--xlsx', str(lay.workbook), '--out', str(out2 / 'out1.xlsx'), '--result', str(out2 / 'result.json'),
                     '--pages-dir', str(out2 / 'pages'), '--today', '2026-11-02', '--copies', str(scratch / 'copies'), '--idmap', str(sid)], capture_output=True, text=True)
check('second pass (station No for the Targeted News Service row) ran', p2.returncode == 0, p2.stderr[-500:])
res2 = json.loads((out2 / 'result.json').read_text())
ws2 = openpyxl.load_workbook(out2 / 'out1.xlsx', read_only=True)['Coverage']; r2 = list(ws2.iter_rows(values_only=True))
tns1 = [r for r in rows[1:] if str(r[ix['Outlet']]) == 'Targeted News Service' and 'Filler story 15' in str(r[ix['Headline']])]
tns2 = [r for r in r2[1:] if str(r[ix['Outlet']]) == 'Targeted News Service' and 'Filler story 15' in str(r[ix['Headline']])]
check('PRJUDGE-v2 control: the station said Yes -> Press release = Yes', len(tns1) == 1 and tns1[0][ix['Press release']] == 'Yes', [r[ix['Press release']] for r in tns1])
check('PRJUDGE-v2: the station said No -> the save does not mark it Yes by the outlet name, and says so in the result', len(tns2) == 1 and tns2[0][ix['Press release']] in (None, '', 'No') and len(res2.get('press_release_station_no', [])) == 1, ([r[ix['Press release']] for r in tns2], res2.get('press_release_station_no')))
check('PRJUDGE-v2: nothing else changed between the two passes', sum(1 for r in r2[1:] if r[ix['Press release']] == 'Yes') == sum(1 for r in rows[1:] if r[ix['Press release']] == 'Yes') - 1)
# PRINTPAGES-v1 / ORIGCOPIES-v1 (patch 09): print pages and known stories in the same update
import openpyxl as _ox
wbo = _ox.load_workbook(out / 'out1.xlsx', read_only=True)
pt = list(wbo['Unlinked print pages'].iter_rows(values_only=True)); ph = {c: i for i, c in enumerate(pt[0])}
runs_json = [json.loads(f.read_text()) for f in (db / 'runs').glob('*.json')]
want_print = sum(len(x.get('print_rows') or []) for x in runs_json); want_copies = sum(len(x.get('extra_copies') or []) for x in runs_json)
added = res.get('print_rows_added', [])
check('PRINTPAGES: every unconfirmed print page (' + str(want_print) + ') became an Unlinked print pages row with its own Article ID and its page link / citation', want_print >= 1 and len(added) == want_print and all(re.match(r'^\d{5}$', a['aid']) for a in added), (want_print, added))
newp = [r for r in pt[1:] if r[ph['Article ID']] in {a['aid'] for a in added}]
check('PRINTPAGES: those rows carry Data Source Newsbank, Date source print edition, the print-page link and the print-page citation', len(newp) == want_print and all(r[ph['Data Source']] == 'Newsbank' and r[ph['Date source']] == 'print edition' and 'docref=image' in str(r[ph['NewsBank print-page link']]) and r[ph['Newsbank APA citation (print page)']] for r in newp), [r[ph['Article ID']] for r in newp])
files_pp = [x['file'] for x in res.get('print_pages_saved', [])]
check('PRINTPAGES: each print page is kept as _original_pdf/<year>/<Article ID>_p<page>.pdf (PRINTORIG-v1 option B)', files_pp and all(re.match(r'^_original_pdf/\d{4}/\d{5}_p[0-9A-Za-z-]+\.pdf$', f) and (out / 'pages' / f).is_file() and (out / 'pages' / f).read_bytes()[:5] == b'%PDF-' for f in files_pp), files_pp)
check('PRINTPAGES: no print page was saved as a story copy (no nb*.pdf for them) and no unknown-story report', not [x for x in res.get('unknown_story', []) if str(x.get('id', '')).startswith(('pp-', 'kn-'))], res.get('unknown_story', [])[:3])
ec = res.get('extra_copies_saved', []); sk = res.get('other_files_skipped', []); _ofiles = res.get('other_files', [])
check('ORIGCOPIES: every known story\'s copy (' + str(want_copies) + ') was either kept as an extra original copy or skipped because its row already holds a NewsBank PDF; none lost silently', want_copies >= 1 and len(ec) + len(sk) == want_copies, (want_copies, len(ec), len(sk)))
check('ORIGCOPIES: a kept copy is _original_pdf/<year>/nb<Article ID><o|r>-<Story ID>.pdf, add-only; named once in "Other files" (one handler: no -v2 twin)', all(re.match(r'^_original_pdf/\d{4}/nb\d{5}[or]-s\d{5}\.pdf$', x['file']) and (out / 'pages' / x['file']).is_file() for x in ec) and len(_ofiles) == len(ec) and not [x for x in ec if '-v2' in x['file']], ec[:2])
check('ORIGCOPIES: a row that already holds a NewsBank PDF gets nothing', all('already holds' in x['why'] for x in sk), sk[:2])
print('all passed' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)
