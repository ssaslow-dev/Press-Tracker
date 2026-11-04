"""REVIEW_3 (checkpoint 3, round 3): the PC build's patched sheet_task handles a run's `extra_copies` (ORIGCOPIES-v1 / OTHERFILES-v1) TWICE:
patch 24 (`apply_print_pages` -> `_extra_copy`) and patch 25 (`apply_extra_copies`) both read `run.extra_copies`, so one PDF from the Update
station lands twice in the library (`nb<id>o-s<story>.pdf` and `...-v2.pdf`) and the row's "Other files" cell names both.

The test applies the app patches to a copy of code/ exactly as assemble_app.py does, runs `saver.py preview` (nothing is written to the master)
on a one-row mini workbook with an "Other files" column and a run that carries one extra copy, and expects ONE file and ONE name.

    cd work/saver && python3 -I -m unittest discover -s tests/review3 -t tests/review3 -p test_review3_extracopies.py -v
"""
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = HERE.parent
SAVER_DIR = TESTS.parent
SRC = SAVER_DIR / 'src'
REPO = SAVER_DIR.parent.parent
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(TESTS))
from wbhelp import pipeline_source   # noqa: E402

SAVER = SRC / 'saver.py'
APP = REPO / 'work' / 'localapp' / 'app'
MASTER = 'AJG Coverage - NewsBank.xlsx'
EXAMPLE_DB = REPO / 'build' / 'tests' / 'sheet_task' / 'fixtures' / 'example_db.json'
MINI = REPO / 'build' / 'tests' / 'sheet_task' / 'audit' / 'mini.py'
# the sheet_task patches of the PC build, in assemble_app.copy_app_code's order
SHEET_PATCHES = ('05_sheet_task_photolink', '09_sheet_task_nbpdf', '12_sheet_task_pqpdf', '14_sheet_task_pq_outlet_aliases', '19_sheet_task_reserved_ids',
                 '22_sheet_task_prjudge2', '24_sheet_task_printpages', '25_sheet_task_otherfiles', '28_sheet_task_prcolor')
STUB_BUILD = ("import sys, os\nos.makedirs(sys.argv[3], exist_ok=True)\n"
              "for n in ('data', 'rows', 'idmap', 'covcols'):\n    open(os.path.join(sys.argv[3], n + '.json'), 'w').write('{}')\n")

TMP = tempfile.TemporaryDirectory()
ROOT = Path(TMP.name)
PIPE = ROOT / 'pipeline'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha(b):
    return hashlib.sha256(b).hexdigest()


def good_pdf() -> bytes:
    from pypdf import PdfWriter
    w = PdfWriter()
    w.add_blank_page(595, 842)
    w.add_metadata({'/Title': 'A story'})
    b = io.BytesIO()
    w.write(b)
    return b.getvalue()


def setUpModule():
    AA = load(APP / 'assemble_app.py', 'assemble_app')
    shutil.copytree(pipeline_source(), PIPE, ignore=shutil.ignore_patterns('docs', '__pycache__', '*.pyc', '_history', 'tracker', 'fetch2',
                                                                          'billstatus', 'fetch_rated1'))
    (PIPE / 'build_data.py').write_text(STUB_BUILD, encoding='utf-8')
    (PIPE / 'relmatch.py').write_text('import sys\n', encoding='utf-8')
    shutil.copy2(APP / 'patches' / 'photolink.py', PIPE / 'photolink.py')
    shutil.copy2(REPO / 'work' / 'localapp' / 'winpack' / 'patches' / 'pdftext_pypdf.py', PIPE / 'pdftext_pypdf.py')
    for n in SHEET_PATCHES:
        AA.patched_copy(PIPE / 'sheet_task.py', PIPE / 'sheet_task.py', APP / 'patches' / (n + '.patch'))
    subprocess.run([sys.executable, '-I', str(SAVER_DIR / 'tools' / 'pipeline_sha.py'), str(PIPE)], check=True, capture_output=True)


def cli(*args):
    p = subprocess.run([sys.executable, '-I', str(SAVER), *map(str, args)], capture_output=True, text=True, encoding='utf-8',
                       env=dict(os.environ, AJG_NO_NETWORK='1'))
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {'raw': p.stdout[-2000:], 'err': p.stderr[-3000:]}
    return p.returncode, res


class ExtraCopyOnce(unittest.TestCase):
    def setUp(self):
        import openpyxl
        mini = load(MINI, 'mini')
        self.d = ROOT / 'e2e'
        shutil.rmtree(self.d, ignore_errors=True)
        self.d.mkdir()
        row = {'Article ID': '10001', 'Story ID': 's00001', 'Original or reprint': 'Original', 'Date': '2026-10-01', 'Year': '2026',
               'Outlet': 'Old Gazette', 'Headline': 'Old story', 'Publisher link': 'https://old.example.com/a'}
        self.master = Path(mini.make(str(self.d / MASTER), [mini.row(**row)]))
        wb = openpyxl.load_workbook(self.master)          # OTHERFILES-v1: the column exists after switch-over day
        for tab in ('Coverage', 'Originals'):
            ws = wb[tab]
            ws.cell(1, ws.max_column + 1).value = 'Other files'
        wb.save(self.master)
        wb.close()
        self.db = self.d / 'db'
        ex = json.loads(EXAMPLE_DB.read_text(encoding='utf-8'))
        for coll, docs in ex.items():
            if isinstance(docs, dict):
                (self.db / coll).mkdir(parents=True, exist_ok=True)
                for k, v in docs.items():
                    (self.db / coll / f'{k}.json').write_text(json.dumps(v), encoding='utf-8')
        pdf = good_pdf()
        (self.db / 'files').mkdir()
        (self.db / 'files' / 'nb-aaaaaaaaaaaaaaaa.pdf').write_bytes(pdf)
        run = json.loads((self.db / 'runs' / 'run-example1.json').read_text(encoding='utf-8'))
        # exactly what the Update station's NewsBank box writes (station/src/newsbank.js: run.extra_copies {aid, fmt, file, pdf_sha256, docref, story, cells})
        run['extra_copies'] = [{'aid': '10001', 'fmt': 'nb', 'file': 'files/nb-aaaaaaaaaaaaaaaa.pdf', 'pdf_sha256': sha(pdf), 'docref': 'news/abc', 'story': 's00001',
                                'cells': {'Section': 'A', 'NewsBank article link': 'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=news/abc'}}]
        (self.db / 'runs' / 'run-example1.json').write_text(json.dumps(run), encoding='utf-8')
        for sub in ('library', 'backups', 'copies/articles'):
            (self.d / sub).mkdir(parents=True)
        (self.d / 'copies' / 'articles' / 'manifest.json').write_text('{"articles":{}}')
        self.state = self.d / 'state'
        code, res = cli('init', '--workbook', self.master, '--state', self.state, '--sha', sha(self.master.read_bytes()))
        self.assertEqual(code, 0, res)

    def preview(self, out):
        return cli('preview', '--workbook', self.master, '--db', self.db, '--pipeline', PIPE, '--copies', self.d / 'copies', '--library', self.d / 'library',
                   '--backups', self.d / 'backups', '--out', out, '--state', self.state, '--today', '2026-10-30')

    def test_one_extra_copy_gives_one_library_file_and_one_name(self):
        import openpyxl
        out = self.d / 'out1'
        code, res = self.preview(out)
        self.assertEqual(code, 0, res)
        r1 = json.loads((out / 'result.json').read_text(encoding='utf-8'))
        pdfs = sorted(p.name for p in (out / 'pages' / '_original_pdf' / '2026').glob('*.pdf')) if (out / 'pages' / '_original_pdf' / '2026').is_dir() else []
        wb = openpyxl.load_workbook(out / 'out1.xlsx', read_only=True)
        ws = wb['Coverage']
        rows = list(ws.iter_rows(values_only=True))
        hdr = list(rows[0])
        cell = next(r for r in rows[1:] if str(r[hdr.index('Article ID')]) == '10001')[hdr.index('Other files')]
        wb.close()
        detail = {'pdfs': pdfs, 'other_files_cell': cell, 'extra_copies (patch 24)': r1.get('extra_copies'), 'extra_copies_saved (patch 25)': r1.get('extra_copies_saved'),
                  'other_files (patch 25)': r1.get('other_files')}
        self.assertEqual(pdfs, ['nb10001o-s00001.pdf'], detail)
        self.assertEqual(str(cell or '').strip(), 'nb10001o-s00001.pdf', detail)
        self.assertEqual(len(r1.get('extra_copies') or []) + len(r1.get('extra_copies_saved') or []), 1, 'the one extra copy is handled once: ' + json.dumps(detail, default=str)[:800])

    def test_a_row_that_already_lists_a_file_can_still_take_an_extra_copy(self):
        """the same update against a row whose "Other files" cell already names a file (any row that got an extra copy in an earlier update):
        the second handling appends a second name sheet_task does not report, and the saver's OTHERFILES-v1 append rule refuses the whole save"""
        import openpyxl
        wb = openpyxl.load_workbook(self.master)
        for tab in ('Coverage', 'Originals'):
            ws = wb[tab]
            hdr = [c.value for c in ws[1]]
            ws.cell(2, hdr.index('Other files') + 1).value = 'pq10001o-s00001.pdf'
        wb.save(self.master)
        wb.close()
        code, res = cli('init', '--workbook', self.master, '--state', self.state, '--sha', sha(self.master.read_bytes()))
        self.assertEqual(code, 0, res)
        code, res = self.preview(self.d / 'out2')
        self.assertEqual((code, res.get('refusal')), (0, None), {'line': res.get('line'), 'refusal': res.get('refusal'), 'disallowed': (res.get('diff') or {}).get('disallowed')})


if __name__ == '__main__':
    unittest.main()
