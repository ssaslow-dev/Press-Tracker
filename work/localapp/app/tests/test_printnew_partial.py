"""N12 (PC part, PRINTNEW-v1) and N16 (a later, complete update folder whose earlier part was already saved), end to end through station_cli on hard-linked
copies of the test build and a copy of the 0bccc1fc workbook. Synthetic update folders (the shapes the station writes: tests/crosssource_pageany_test.js and
newsbank_printread_test.js dumps).

    AJG_SCRATCH=<scratchpad with wb_0bccc1fc.xlsx> AJG_TEST_BUILD=<linux build, data-mode empty> python3 -I -m unittest discover -s work/localapp/app/tests -p test_printnew_partial.py -v

About 20 minutes (each inspect/preview and each save runs the whole save program). Nothing outside the scratch folder is written."""
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402
F = T.F

WB = T.SCRATCH / 'wb_0bccc1fc.xlsx'
SHA0 = '0bccc1fcaf6e5f3c9395dd80951685d4cd0a743489e1617115b3205b9303ecbc'
BASE = T.SCRATCH / 'app_build' / 'test_printnew'
OUTLET = 'Valley Gazette Test'
BODY = ('Assemblymember Jesse Gabriel (D-Encino) introduced a bill in Sacramento on Friday that would speed up clean air permits across California, saying that '
        'Californians should not wait years for clean air and that regional air districts need a firm deadline to act on every application.')


def pdf(n):
    """a valid one-page PDF (pypdf reads it; no scripts), different for every n"""
    objs = [b'<</Type/Catalog/Pages 2 0 R>>', b'<</Type/Pages/Kids[3 0 R]/Count 1>>', b'<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R>>']
    body = ('0 g 10 10 %d 20 re f' % (20 + n)).encode()
    objs.append(b'<</Length %d>>\nstream\n' % len(body) + body + b'\nendstream')
    out, offs = b'%PDF-1.4\n', []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b'%d 0 obj\n' % i + o + b'\nendobj\n'
    x = len(out)
    out += b'xref\n0 %d\n0000000000 65535 f \n' % (len(objs) + 1) + b''.join(b'%010d 00000 n \n' % o for o in offs)
    return out + b'trailer\n<</Root 1 0 R/Size %d>>\nstartxref\n%d\n%%%%EOF\n' % (len(objs) + 1, x)


def sha(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()


def pages_doc(n, headline, page, as_, batch_idx, extra=None):
    raw = pdf(n)
    clean = ('<html><head><title>%s</title></head><body><article class="jg-pdf-text"><p class="pdf-cap">Text read from the newspaper page by Claude (not NewsBank’s '
             'text): check it against the page PDF</p><h1>%s</h1><p>%s</p><p>%s</p></article></body></html>') % (headline, headline, BODY, BODY)
    nb = {'docref': '', 'url': '', 'file': f'files/pg-{n:04d}.pdf', 'pdf_sha256': sha(raw), 'pdf_bytes': len(raw), 'thin': False, 'kind': 'print_page', 'as': as_,
          'read': {'by': 'claude', 'outcome': 'new', 'text': BODY + '\n\n' + BODY, 'headline': headline, 'page': page},
          'batch': {'name': 'p.png', 'sha256': 'aabbccdd' * 8, 'index': batch_idx, 'pages': [1, 1]},
          'header': {'headline': headline, 'date': '2026-11-03', 'source': OUTLET, 'page': page}, 'flags': [], 'how': 'read', 'source': 'page'}
    nb.update(extra or {})
    return {'url': f'https://print-page.invalid/p/{n:04d}', 'title': headline, 'clean': clean, 'scoped': '', 'publine': '', 'at': '2026-11-05T01:00:00.000Z', 'nb': nb}, raw


def run_doc(n, headline, code, page='A5', print_pages=None):
    row = {'Article ID': f'NEW-run-t{n}-1', 'Story ID': f'sNEW-run-t{n}-1', 'Original or reprint': 'Original', 'Data Source': 'Print page', 'Date': '2026-11-03', 'Year': 2026,
           'Date source': 'print edition', 'Outlet': OUTLET, 'Medium': 'Newspaper', 'Format': 'Print', 'Language': 'English', 'Headline': headline,
           'Author / byline': 'By Dana Whitfield', 'Edition': 'Print', 'Section': 'Metro', 'Page': page, 'Word count': 88, 'Mentions "Gabriel" in text': 'Yes',
           '# of reprints': 0, 'Topic': 'Energy / environment', 'Tone': 'Neutral', 'Tone rated by': 'Claude, from article excerpt (2026-11-05)',
           'Team note': 'newspaper page p.png #1; read by Claude: check them', 'Tracker story code': code, 'Role': 'Named in headline', '_date_src': 'printpage',
           '_found_by': 'printpage: p.png', '_pr': {'v': 'no', 'why': 'a reporter’s story', 'by': 'Claude', 'type': 'news'}}
    return {'at': '2026-11-05T01:00:00.000Z', 'mode': 'hand', 'printpage': '2026-11-04', 'status': 'done', 'stories': [code], 'reprints': [], 'rows': [row],
            'print_pages': print_pages or [], 'print_rows': [], 'extra_copies': [], 'found_by': {'printpage': 1}, 'searched_to': '', 'since': '', 'since_manual': False, 'left': [],
            'nb': {'source': 'newspaper page PDFs and pictures', 'batches': [], 'pdfs': 1, 'links_found': 0, 'links_searched': 1}}


def build_zip(out: Path, parts, sha_src=SHA0, extra=None):
    """parts: [(n, headline, code, [extra (docs, pdf bytes) ...], print_pages)] -> one folder with a run per part"""
    d = out.with_suffix('.db')
    shutil.rmtree(d, ignore_errors=True)
    for n, headline, code, more, pps in parts:
        rid = f'run-t{n}'
        for coll, name, doc in [('runs', rid, run_doc(n, headline, code, print_pages=pps))]:
            p = d / coll / f'{name}.json'
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(doc))
        pd, raw = pages_doc(n, headline, 'A5', 'new', 1)
        (d / 'pages').mkdir(parents=True, exist_ok=True)
        (d / 'pages' / f'{code}.json').write_text(json.dumps(pd))
        (d / 'files').mkdir(parents=True, exist_ok=True)
        (d / 'files' / f'pg-{n:04d}.pdf').write_bytes(raw)
        for pid, doc, raw2 in more:
            (d / 'pages' / f'{pid}.json').write_text(json.dumps(doc))
            (d / 'files' / Path(doc['nb']['file']).name).write_bytes(raw2)
    return F.pack_update_zip(out, d, sha_src, extra_manifest=extra)


def mkwork(name):
    root = BASE / name / 'AJG Tracker'
    shutil.rmtree(BASE / name, ignore_errors=True)
    root.parent.mkdir(parents=True)
    shutil.copytree(T.BUILD, root, symlinks=True, copy_function=os.link)
    wbd = root / 'data' / 'workbook'
    shutil.rmtree(wbd, ignore_errors=True)
    wbd.mkdir(parents=True)
    shutil.copy2(WB, wbd / 'AJG Coverage - NewsBank.xlsx')
    r = cli(root, 'init', '--sha', SHA0)
    assert r.get('ok'), r
    return root


def cli(root, verb, *args):
    p = subprocess.run([str(root / 'python' / 'bin' / 'python'), '-I', 'app/station/station_cli.py', verb, '--root', str(root), *args], cwd=root,
                       capture_output=True, text=True, encoding='utf-8')
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise AssertionError('no JSON from station_cli %s: %s %s' % (verb, p.stdout[-500:], p.stderr[-800:]))


def take(root, zp):
    r = cli(root, 'inspect', '--zip', str(zp))
    return r


def save(root, r):
    return cli(root, 'save', '--update', r['update_id'], '--token', r['token'])


def rows(root):
    import openpyxl
    f = next((root / 'data' / 'workbook').glob('*.xlsx'))
    wb = openpyxl.load_workbook(f, read_only=True)
    out = {}
    for tab in ('Coverage', 'Unlinked print pages'):
        it = wb[tab].iter_rows(values_only=True)
        h = list(next(it))
        out[tab] = [dict(zip(h, r)) for r in it if r and r[0]]
    return out


def setUpModule():
    if not T.BUILD.is_dir() or not WB.is_file():
        raise unittest.SkipTest('needs the test build and $AJG_SCRATCH/wb_0bccc1fc.xlsx')
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)


def tearDownModule():
    shutil.rmtree(BASE, ignore_errors=True)


H1, H2 = 'Gabriel bill number one would speed clean air permits', 'Gabriel bill number two would cut permit waits for builders'


class PrintNewAndAttached(unittest.TestCase):
    """N12 PC part: a print-only NEW story's read text is its saved copy; page scans of new / attached / jump pages are print originals of their rows"""

    def test_new_attached_continuation(self):
        root = mkwork('pn')
        base = rows(root)
        n_cov, n_unl = len(base['Coverage']), len(base['Unlinked print pages'])
        jump, jraw = pages_doc(3, 'Jump page of one', 'A12', 'continuation', 2)
        pps = [{'as': 'continuation', 'story': '', 'item': 'aabbccdd#1', 'aid': '', 'file': jump['nb']['file'], 'url': '', 'outlet': OUTLET, 'date': '2026-11-03', 'hl': 'x', 'snippet': ''}]
        zp = build_zip(BASE / 'pn.zip', [(1, H1, 'jg-0000a1', [('pp-jump0001', jump, jraw)], pps)])
        r = take(root, zp)
        self.assertTrue(r.get('ok') and r.get('can_save'), r)
        self.assertTrue(any('saved pages added' in x or 'saved page' in x for x in r['lines']), r['lines'])
        s = save(root, r)
        self.assertTrue(s.get('written'), s)
        now = rows(root)
        self.assertEqual(len(now['Coverage']), n_cov + 1)
        self.assertEqual(len(now['Unlinked print pages']), n_unl, 'a jump page is not an Unlinked print pages row')
        row = next(x for x in now['Coverage'] if x['Headline'] == H1)
        aid, sid = str(row['Article ID']), row['Story ID']
        self.assertEqual((row['Saved Copy?'], row['File type'], row['File name']), ('Yes', 'HTML', f'ws{aid}o-{sid}.html'))
        lib = root / 'data' / 'library'
        html = (lib / '2026' / row['File name']).read_text(encoding='utf-8')
        self.assertIn('Text read from the newspaper page by Claude', html)
        self.assertIn('Assemblymember Jesse Gabriel', html)
        self.assertTrue((lib / '_original_pdf' / '2026' / f'{aid}_p5.pdf').is_file(), 'the scan of the new story is its print original')
        self.assertTrue((lib / '_original_pdf' / '2026' / f'{aid}_p12.pdf').is_file(), 'the jump page goes with the story it continues')
        self.assertEqual((lib / '_original_pdf' / '2026' / f'{aid}_p5.pdf').read_bytes(), pdf(1))
        arts = json.loads((root / 'data' / 'copies' / 'articles' / 'manifest.json').read_text(encoding='utf-8'))['articles']
        self.assertIn(sid, arts, 'article data picks up the HTML copy')


class PartialFolder(unittest.TestCase):
    """N16: a later, complete update folder whose earlier part was already saved"""

    def zips(self, tag):
        v1 = build_zip(BASE / f'{tag}_v1.zip', [(1, H1, 'jg-0000a1', [], [])])
        v2 = build_zip(BASE / f'{tag}_v2.zip', [(1, H1, 'jg-0000a1', [], []), (2, H2, 'jg-0000a2', [], [])],
                       extra={'replaces': f'{tag}_v1.zip', 'folder_number': 2})
        return v1, v2

    def test_take_only_the_unsaved_run(self):
        root = mkwork('pt1')
        v1, v2 = self.zips('pt1')
        n0 = len(rows(root)['Coverage'])
        r1 = take(root, v1)
        self.assertTrue(save(root, r1).get('written'))
        self.assertEqual(len(rows(root)['Coverage']), n0 + 1)
        r2 = take(root, v2)                     # the workbook now differs from the "for Update" file, but only by v1's save
        self.assertTrue(r2.get('ok'), r2)
        self.assertEqual(r2['stage'], 'previewed', r2)
        self.assertEqual(r2['runs'], ['run-t2'])
        self.assertEqual(list(r2['skipped_runs']), ['run-t1'])
        self.assertTrue(any('Left out' in x and 'run-t1' in x for x in r2['lines']), r2['lines'])
        self.assertTrue(any('1 row added' in x for x in r2['lines']), r2['lines'])
        self.assertEqual(r2['fingerprint']['status'], 'match')
        s2 = save(root, r2)
        self.assertTrue(s2.get('written'), s2)
        cov = rows(root)['Coverage']
        self.assertEqual(len(cov), n0 + 2)
        self.assertEqual(sum(1 for x in cov if x['Headline'] == H1), 1, 'never added twice')
        self.assertEqual(sum(1 for x in cov if x['Headline'] == H2), 1)
        # the finished folders cannot be taken again
        for z in self.zips('pt1b'):
            r = take(root, z)
            self.assertEqual(r.get('refused'), 'ALREADY_SAVED', r)
        # the library holds each page once
        self.assertEqual(len(list((root / 'data' / 'library' / '_original_pdf' / '2026').glob('*_p5.pdf'))), 2)

    def test_not_a_later_folder_is_still_refused(self):
        root = mkwork('pt2')
        v1, _ = self.zips('pt2')
        self.assertTrue(save(root, take(root, v1)).get('written'))
        plain2 = build_zip(BASE / 'pt2_plain.zip', [(1, H1, 'jg-0000a1', [], []), (2, H2, 'jg-0000a2', [], [])])     # no `replaces`: an old rule
        r = take(root, plain2)
        self.assertEqual(r.get('refused'), 'ALREADY_SAVED', r)

    def test_workbook_changed_by_something_else_asks(self):
        root = mkwork('pt3')
        v1, v2 = self.zips('pt3')
        self.assertTrue(save(root, take(root, v1)).get('written'))
        # a hand edit: the person accepts a workbook changed in Excel (the ledger gets an "init" entry, not a save of this folder)
        import openpyxl
        f = next((root / 'data' / 'workbook').glob('*.xlsx'))
        wb = openpyxl.load_workbook(f)
        wb['Coverage'].cell(2, 1).value = wb['Coverage'].cell(2, 1).value
        wb.save(f)
        self.assertTrue(cli(root, 'init', '--sha', T.sha(f)).get('ok'))
        r2 = take(root, v2)
        self.assertTrue(r2.get('ok'), r2)
        self.assertEqual(r2['stage'], 'needs_confirm', r2)           # the fingerprint warning still protects against a changed workbook
        self.assertEqual(list(r2['skipped_runs']), ['run-t1'])


class SwitchoverScreenGone(unittest.TestCase):
    """D1: the one-time Switch-over changes screen is removed. A tracker that finished the switch-over (its state file and old ledger verbs are still on disk)
    starts and answers as before; there is no screen, no verb for it, and the save's rename hook still has its machinery."""

    def test_finished_tracker_starts_and_has_no_screen(self):
        root = mkwork('d1')
        (root / 'data' / 'state' / 'switchover.json').write_text(json.dumps({'finished_at': '2026-11-03T12:00:00', 'steps': {'rename_files': {'at': 'x'}}}))
        led = root / 'data' / 'state' / 'ledger.jsonl'
        with open(led, 'a', encoding='utf-8') as f:       # the verbs the removed steps wrote still count as "the tracker was updated"
            for v in ('drop_unverified', 'add_other_files_column', 'recolor_press_releases', 'press_release_judge', 'apply_datafix', 'rename_files', 'datafix_structural'):
                f.write(json.dumps({'at': '2026-11-03T10:00:00Z', 'verb': v, 'after_sha': SHA0, 'confirmed': True}) + '\n')
        for gone in ('switchover.py', 'drop_unverified.py', 'other_files_column.py', 'datafix_structural.py'):
            self.assertFalse((root / 'app' / 'station' / gone).exists(), gone)
        self.assertFalse((root / 'app' / 'station' / 'data').exists())
        self.assertTrue((root / 'app' / 'station' / 'cell_steps.py').is_file())
        panel = (root / 'app' / 'station' / 'web' / 'panel.js').read_text(encoding='utf-8')
        self.assertNotIn('Switch-over changes', panel)
        self.assertNotIn('switch_preview', panel)
        self.assertIn('Set up from the Mac library', panel)
        s = T.Server(root).start()
        try:
            st, status = s.call('GET', '/_local/station/status')
            self.assertEqual(st, 200)
            self.assertNotIn('switchover', status)
            self.assertEqual(status['role'], 'keeper')
            for verb in ('switch_preview', 'switch_apply', 'drop_preview', 'drop_apply'):
                code, _ = s.call('POST', '/_local/station/' + verb, {})
                self.assertNotEqual(code, 200, verb)
            self.assertEqual(s.call('GET', '/_local/station/status')[0], 200)
        finally:
            s.stop()
        r = cli(root, 'setup_check')            # the setup from the Mac library is still there (it refuses here: a workbook exists, no folder given)
        self.assertIn('ok', r)


if __name__ == '__main__':
    unittest.main()
