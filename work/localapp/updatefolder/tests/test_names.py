"""STATIONNAMES (LIBFILES-v1 follow-up 2): library/ files named by the schema in the update folder, the manifest's `names` block, and the PC's
comparison with what the save assigned. Small zips built here; no workbook is read.

    cd work/localapp/updatefolder && python3 -I -m unittest discover -s tests -t . -p "test_names.py" -v
"""
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
UF = HERE.parent
sys.path.insert(0, str(UF))
import formats as F            # noqa: E402
import take_update as TU       # noqa: E402
from layout import PCLayout    # noqa: E402
from tests.test_nbpdf import good_pdf   # noqa: E402

WB = 'c' * 64
PQ, NB = good_pdf(2), good_pdf(3)
sha = lambda b: hashlib.sha256(b).hexdigest()


def names_block(**over):
    nm = {'version': 1, 'today': '2026-11-03', 'from_next': {'aid': 10670, 's': 4942, 'pr': 245}, 'items': [
        {'run': 'run-1', 'row': 0, 'doc': 'jg-aaaaaa', 'aid': '10670', 'sid': 's04942', 'kind': 'o', 'fmt': 'ws', 'year': '2026',
         'copy': 'library/2026/ws10670o-s04942.html', 'raw': 'library/_original_html/2026/ws10670o-s04942.html', 'pdf': '', 'pdf_for': ''},
        {'run': 'run-1', 'row': 1, 'doc': 'jg-bbbbbb', 'aid': '10671', 'sid': 's04943', 'kind': 'o', 'fmt': 'nb', 'year': '2025',
         'copy': 'library/2025/nb10671o-s04943.pdf', 'raw': '', 'pdf': '', 'pdf_for': 'files/nb-0123456789abcdef.pdf'},
        {'run': 'run-1', 'row': 2, 'doc': 'jg-cccccc', 'aid': '10672', 'sid': 's04944', 'kind': 'o', 'fmt': 'pq', 'year': '2023',
         'copy': 'library/2023/pq10672o-s04944.html', 'raw': '', 'pdf': 'library/_original_pdf/2023/pq10672o-s04944.pdf', 'pdf_for': 'files/pq-fedcba9876543210.pdf'},
        {'run': 'run-1', 'row': 3, 'doc': 'rp-dddddddddddd', 'aid': '10673', 'sid': 's04930', 'kind': 'r', 'fmt': 'ws', 'year': '2026',
         'copy': 'library/2026/ws10673r-s04930.html', 'raw': '', 'pdf': '', 'pdf_for': ''}],
        'releases': [{'run': 'run-1', 'url': 'https://gabriel.asmdc.org/a', 'prid': 'pr00245', 'year': '2026',
                      'copy': 'library/Press releases/2026/pr00245.html', 'raw': 'library/_original_html/Press releases/2026/pr00245.html'}]}
    nm.update(over)
    return nm


def make_zip(tmp: Path, names=None, mutate=None, name='u.zip') -> Path:
    docs = {
        'db/runs/run-1.json': {'at': '2026-11-03T10:00:00Z', 'mode': 'find', 'status': 'done', 'rows': [{'Article ID': 'NEW-1'}]},
        'db/pages/jg-aaaaaa.json': {'url': 'https://x/a', 'title': 't', 'clean': '<p>a</p>', 'scoped': '<p>a2</p>'},
        'db/pages/jg-bbbbbb.json': {'url': 'https://infoweb.newsbank.com/x', 'title': 't', 'clean': '<p>nb</p>', 'nb': {'file': 'files/nb-0123456789abcdef.pdf', 'pdf_sha256': sha(NB), 'docref': 'd'}},
        'db/pages/jg-cccccc.json': {'url': 'https://www.proquest.com/docview/1', 'title': 't', 'clean': '<p>pq</p>', 'pq': {'file': 'files/pq-fedcba9876543210.pdf', 'pdf_sha256': sha(PQ), 'header': {}}},
        'db/pages/rp-dddddddddddd.json': {'url': 'https://y/r', 'title': 't', 'clean': '<p>r</p>'},
    }
    blobs = {n: json.dumps(d).encode() for n, d in docs.items()}
    blobs.update({'library/2026/ws10670o-s04942.html': b'<p>a2</p>', 'library/_original_html/2026/ws10670o-s04942.html': b'<p>a</p>', 'library/2025/nb10671o-s04943.pdf': NB,
                  'library/2023/pq10672o-s04944.html': b'<p>pq</p>', 'library/_original_pdf/2023/pq10672o-s04944.pdf': PQ, 'library/2026/ws10673r-s04930.html': b'<p>r</p>',
                  'library/Press releases/2026/pr00245.html': b'<p>rel</p>', 'library/_original_html/Press releases/2026/pr00245.html': b'<p>rel</p>'})
    if mutate:
        mutate(blobs)
    files = {n: {'sha256': sha(b), 'bytes': len(b)} for n, b in blobs.items()}
    man = {'format': F.FORMAT_UPDATE, 'format_version': 1, 'created_at': '2026-11-03T10:00:00Z', 'source': {'workbook_sha256': WB}, 'runs': ['run-1'], 'files': files}
    if names is not False:
        man['names'] = names if names is not None else names_block()
    zp = tmp / name
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(man))
        for n, b in blobs.items():
            z.writestr(n, b)
    return zp


class Names(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.tmp = Path(self.t.name); self.lay = PCLayout(self.tmp / 'app')

    def tearDown(self):
        self.t.cleanup()

    def refused(self, zp, code):
        with self.assertRaises(F.UpdateRefused) as c:
            TU.inspect_update(zp, self.lay)
        self.assertEqual(c.exception.code, code, c.exception.msg)
        stg = self.lay.updates / 'staging'
        self.assertFalse(stg.exists() and any(stg.iterdir()), 'a refused update leaves nothing in staging')

    # ---- the allow-list ----
    def test_schema_names_are_allowed_and_others_are_not(self):
        good = ['library/2026/ws10670o-s04942.html', 'library/2026/ws10670o-s04942-v2.html', 'library/2026/ws10670.html', 'library/_original_html/2026/pq10672r-s04944.html',
                'library/2025/nb10671o-s04943.pdf', 'library/_original_pdf/2023/pq10672o-s04944.pdf', 'library/Press releases/2026/pr00245.html',
                'library/_original_html/Press releases/2026/pr00245.html', 'library/undated/ws10670o-s04942.html']
        bad = ['library/2026/evil.exe', 'library/2026/ws10670o-s04942.js', 'library/2026/../x.html', 'library/26/ws10670o-s04942.html', 'library/2026/ws1067o-s04942.html',
               'library/2026/ws10670x-s04942.html', 'library/2026/ws10670o-s4942.html', 'library/_original_pdf/2023/ws10672o-s04944.pdf', 'library/2026/ws10670o-s04942.pdf',
               'library/_original_pdf/2023/pq10672o-s04944.html', 'library/2026/pr00245.html', 'library/Press releases/2026/ws10670o-s04942.html', 'library/Press releases/2026/pr00245.pdf',
               'library//2026/ws10670o-s04942.html', 'library/2026/sub/ws10670o-s04942.html', '/library/2026/ws10670o-s04942.html', 'library\\2026\\ws10670o-s04942.html',
               'library/2026/CON.html', 'library/_to_delete/2026/ws10670o-s04942.html', 'library/2026/ws10670o-s04942.html ']
        for n in good:
            self.assertTrue(F.entry_ok(n)[0], n)
        for n in bad:
            self.assertFalse(F.entry_ok(n)[0], n)

    def test_good_update_is_staged_with_library_files_and_pdfs_where_the_save_looks(self):
        r = TU.inspect_update(make_zip(self.tmp), self.lay); stage = Path(r['stage'])
        self.assertEqual((stage / 'library' / '2026' / 'ws10670o-s04942.html').read_bytes(), b'<p>a2</p>')
        self.assertEqual((stage / 'library' / 'Press releases' / '2026' / 'pr00245.html').read_bytes(), b'<p>rel</p>')
        self.assertEqual((stage / 'db' / 'files' / 'nb-0123456789abcdef.pdf').read_bytes(), NB)       # where sheet_task reads it
        self.assertEqual((stage / 'db' / 'files' / 'pq-fedcba9876543210.pdf').read_bytes(), PQ)
        self.assertEqual((stage / 'library' / 'Press releases' / '2026' / 'pr00245.html').exists(), True)

    def test_reference_checker_accepts_it(self):
        zp = make_zip(self.tmp)
        with zipfile.ZipFile(zp) as z:
            entries = {i.filename: F.read_entry(z, i) for i in F.scan_zip(z, zp.stat().st_size)}
        F.check_manifest(json.loads(entries.pop('manifest.json')), entries)

    # ---- the names block ----
    def test_library_files_without_a_names_block_are_refused(self):
        self.refused(make_zip(self.tmp, names=False), 'UNLISTED_FILE')

    def test_a_library_file_the_block_does_not_claim(self):
        self.refused(make_zip(self.tmp, mutate=lambda b: b.update({'library/2026/ws10699o-s04999.html': b'x'})), 'UNLISTED_FILE')

    def test_a_path_that_is_not_the_schema_name_for_its_fields(self):
        nm = names_block(); nm['items'][0]['copy'] = 'library/2026/ws10671o-s04942.html'
        self.refused(make_zip(self.tmp, names=nm, mutate=lambda b: b.update({'library/2026/ws10671o-s04942.html': b.pop('library/2026/ws10670o-s04942.html')})), 'BAD_NAMES')

    def test_the_same_file_claimed_twice(self):
        nm = names_block(); nm['items'][3]['copy'] = nm['items'][0]['copy']
        self.refused(make_zip(self.tmp, names=nm), 'BAD_NAMES')

    def test_the_same_article_id_twice(self):
        nm = names_block(); nm['items'][3]['aid'] = '10670'
        self.refused(make_zip(self.tmp, names=nm), 'BAD_NAMES')

    def test_a_named_file_the_zip_lacks(self):
        self.refused(make_zip(self.tmp, mutate=lambda b: b.pop('library/2026/ws10670o-s04942.html')), 'HASH_MISMATCH' if False else 'MISSING_FILE')

    def test_pdf_with_another_checksum_than_its_pages_doc_says(self):
        self.refused(make_zip(self.tmp, mutate=lambda b: b.update({'library/_original_pdf/2023/pq10672o-s04944.pdf': good_pdf(5)})), 'HASH_MISMATCH')

    def test_pdf_for_not_the_one_the_pages_doc_names(self):
        nm = names_block(); nm['items'][2]['pdf_for'] = 'files/pq-0000000000000000.pdf'
        self.refused(make_zip(self.tmp, names=nm), 'BAD_NAMES')

    def test_a_hostile_pdf_under_a_library_name_is_refused(self):
        from tests.test_nbpdf import evil
        e = evil('openaction') if True else b''
        def mut(b):
            b['library/_original_pdf/2023/pq10672o-s04944.pdf'] = e
        docs_fix = lambda b: None
        zp = make_zip(self.tmp, mutate=mut)
        # the pages doc still gives the good checksum, so the swap is caught either way
        self.refused(zp, 'HASH_MISMATCH')

    def test_html_must_be_utf8_text(self):
        self.refused(make_zip(self.tmp, mutate=lambda b: b.update({'library/2026/ws10670o-s04942.html': b'\xff\xfe\x00bad'})), 'BAD_HTML')

    def test_an_old_zip_without_names_or_library_still_works(self):
        def mut(b):
            for n in [n for n in b if n.startswith('library/')]:
                del b[n]
            b['files/nb-0123456789abcdef.pdf'] = NB; b['files/pq-fedcba9876543210.pdf'] = PQ
        TU.inspect_update(make_zip(self.tmp, names=False, mutate=mut), self.lay)

    def test_pack_update_zip_reference_writer(self):
        db = self.tmp / 'db'; (db / 'runs').mkdir(parents=True); (db / 'runs' / 'r.json').write_text('{"rows":[]}')
        zp = F.pack_update_zip(self.tmp / 'w.zip', db, WB, library={'library/2026/ws10670o-s04942.html': b'<p>x</p>'},
                               extra_manifest={'names': {'version': 1, 'items': [{'run': 'r', 'row': 0, 'doc': '', 'aid': '10670', 'sid': 's04942', 'kind': 'o', 'fmt': 'ws', 'year': '2026',
                                                                              'copy': 'library/2026/ws10670o-s04942.html', 'raw': '', 'pdf': '', 'pdf_for': ''}], 'releases': []}})
        with self.assertRaises(F.UpdateRefused) as c:        # a named file needs its pages document
            TU.inspect_update(zp, self.lay)
        self.assertEqual(c.exception.code, 'BAD_NAMES')


def res_for(items_saved, releases=()):
    """a stand-in for the save's result.json: {'pages': [...], 'release_copies': [...]} from (doc, file, original, original_pdf)"""
    return {'pages': [dict(page=d, file=f, **({'original': o} if o else {}), **({'original_pdf': p} if p else {})) for d, f, o, p in items_saved],
            'release_copies': [dict(url=u, file=f, original=o) for u, f, o in releases], 'pages_skipped': [], 'pages_error': []}


class Reconcile(unittest.TestCase):
    """What the PC does after the save: compare the station's names with the names the save assigned"""

    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.tmp = Path(self.t.name); self.lay = PCLayout(self.tmp / 'app')
        self.stage = Path(TU.inspect_update(make_zip(self.tmp), self.lay)['stage'])
        self.nm = names_block()

    def tearDown(self):
        self.t.cleanup()

    def saved_as_named(self):
        return res_for([('jg-aaaaaa', '2026/ws10670o-s04942.html', '_original_html/2026/ws10670o-s04942.html', ''), ('jg-bbbbbb', '2025/nb10671o-s04943.pdf', '', ''),
                        ('jg-cccccc', '2023/pq10672o-s04944.html', '', '_original_pdf/2023/pq10672o-s04944.pdf'), ('rp-dddddddddddd', '2026/ws10673r-s04930.html', '', '')],
                       [('https://gabriel.asmdc.org/a', 'Press releases/2026/pr00245.html', '_original_html/Press releases/2026/pr00245.html')])

    def test_names_that_match_are_confirmed_and_nothing_moves(self):
        r = TU.reconcile_names(self.nm, self.stage, self.saved_as_named(), apply=True)
        self.assertEqual((r['confirmed'], r['renamed'], r['not_saved']), (8, [], []))
        self.assertTrue((self.stage / 'library' / '2026' / 'ws10670o-s04942.html').is_file())

    def test_second_update_from_the_same_file_is_moved_on_and_listed(self):
        """The first update was saved first and took 10670 to 10673 and s04942 to s04944; this one, made from the same for-Update file, names the same numbers.
        The save gives it 10674 to 10677 and s04945 to s04947: the files are renamed and every rename is listed."""
        res = res_for([('jg-aaaaaa', '2026/ws10674o-s04945.html', '_original_html/2026/ws10674o-s04945.html', ''), ('jg-bbbbbb', '2025/nb10675o-s04946.pdf', '', ''),
                       ('jg-cccccc', '2023/pq10676o-s04947.html', '', '_original_pdf/2023/pq10676o-s04947.pdf'), ('rp-dddddddddddd', '2026/ws10677r-s04930.html', '', '')],
                      [('https://gabriel.asmdc.org/a', 'Press releases/2026/pr00246.html', '_original_html/Press releases/2026/pr00246.html')])
        r = TU.reconcile_names(self.nm, self.stage, res, apply=True)
        self.assertEqual(r['confirmed'], 0)
        self.assertEqual(len(r['renamed']), 8)
        self.assertIn({'from': 'library/2026/ws10670o-s04942.html', 'to': 'library/2026/ws10674o-s04945.html', 'why': r['renamed'][0]['why'], 'aid': '10670'}, r['renamed'])
        self.assertIn('Article ID 10670 -> 10674', r['renamed'][0]['why']); self.assertIn('Story ID s04942 -> s04945', r['renamed'][0]['why'])
        for to in ('library/2026/ws10674o-s04945.html', 'library/_original_html/2026/ws10674o-s04945.html', 'library/2025/nb10675o-s04946.pdf', 'library/2023/pq10676o-s04947.html',
                   'library/_original_pdf/2023/pq10676o-s04947.pdf', 'library/2026/ws10677r-s04930.html', 'library/Press releases/2026/pr00246.html'):
            self.assertTrue((self.stage / Path(*to.split('/'))).is_file(), to)
        for old in ('library/2026/ws10670o-s04942.html', 'library/Press releases/2026/pr00245.html'):
            self.assertFalse((self.stage / Path(*old.split('/'))).exists(), old)
        self.assertEqual((self.stage / 'library' / '2025' / 'nb10675o-s04946.pdf').read_bytes(), NB)       # the content went with the name
        self.assertTrue(any('renamed' in l for l in r['lines']))

    def test_original_turned_reprint_by_the_text_test(self):
        res = self.saved_as_named(); res['pages'][0]['file'] = '2026/ws10670r-s04930.html'; res['pages'][0]['original'] = '_original_html/2026/ws10670r-s04930.html'
        r = TU.reconcile_names(self.nm, self.stage, res, apply=True)
        self.assertEqual(r['confirmed'], 6)
        self.assertEqual([x['to'] for x in r['renamed']], ['library/2026/ws10670r-s04930.html', 'library/_original_html/2026/ws10670r-s04930.html'])
        self.assertIn('o -> r', r['renamed'][0]['why']); self.assertIn('Story ID s04942 -> s04930', r['renamed'][0]['why'])
        self.assertEqual((self.stage / 'library' / '2026' / 'ws10670r-s04930.html').read_bytes(), b'<p>a2</p>')

    def test_names_that_swap_do_not_overwrite_each_other(self):
        res = self.saved_as_named(); res['pages'][0]['file'] = '2026/ws10673r-s04930.html'; res['pages'][3]['file'] = '2026/ws10670o-s04942.html'
        TU.reconcile_names(self.nm, self.stage, res, apply=True)
        self.assertEqual((self.stage / 'library' / '2026' / 'ws10673r-s04930.html').read_bytes(), b'<p>a2</p>')
        self.assertEqual((self.stage / 'library' / '2026' / 'ws10670o-s04942.html').read_bytes(), b'<p>r</p>')

    def test_a_story_the_save_did_not_add_is_listed_and_its_file_stays_named_as_the_station_did(self):
        res = self.saved_as_named(); res['pages'].pop(1); res['pages_skipped'] = [{'page': 'jg-bbbbbb', 'why': 'its link is already in the workbook'}]
        r = TU.reconcile_names(self.nm, self.stage, res, apply=True)
        self.assertEqual(r['not_saved'], [{'file': 'library/2025/nb10671o-s04943.pdf', 'why': 'its link is already in the workbook'}])
        self.assertEqual(r['renamed'], [])

    def test_a_name_taken_by_a_file_that_was_not_saved_is_set_aside_not_suffixed(self):
        """the story the save skipped keeps the station's name 10670; another file is renamed onto 10670: the skipped one moves to not_saved/, nothing gets a made-up name"""
        res = self.saved_as_named(); res['pages'].pop(0); res['pages_skipped'] = [{'page': 'jg-aaaaaa', 'why': 'no article body'}]
        res['pages'][2]['file'] = '2026/ws10670o-s04942.html'          # the reprint's copy now takes the skipped story's old name
        r = TU.reconcile_names(self.nm, self.stage, res, apply=True)
        self.assertTrue(any(x['file'] == 'library/2026/ws10670o-s04942.html' for x in r['not_saved']))
        self.assertEqual((self.stage / 'library' / '2026' / 'ws10670o-s04942.html').read_bytes(), b'<p>r</p>')
        self.assertEqual((self.stage / 'not_saved' / '2026' / 'ws10670o-s04942.html').read_bytes(), b'<p>a2</p>')
        self.assertEqual([p.name for p in (self.stage / 'library' / '2026').iterdir() if p.name.endswith('-2')], [])

    def test_preview_changes_nothing(self):
        res = res_for([('jg-aaaaaa', '2026/ws10680o-s04950.html', '', '')])
        r = TU.reconcile_names(self.nm, self.stage, res, apply=False)
        self.assertTrue(r['renamed']); self.assertTrue((self.stage / 'library' / '2026' / 'ws10670o-s04942.html').is_file())
        self.assertFalse((self.stage / 'library' / '2026' / 'ws10680o-s04950.html').exists())

    def test_files_the_save_wrote_that_were_not_named_are_counted(self):
        res = self.saved_as_named(); res['pages'].append({'page': 'jg-zzzzzz', 'file': '2026/ws10690o-s04960.html'})
        r = TU.reconcile_names(self.nm, self.stage, res, apply=False)
        self.assertEqual(r['unnamed'], ['2026/ws10690o-s04960.html'])

    def test_year_folder_change_is_explained(self):
        res = self.saved_as_named(); res['pages'][0]['file'] = '2025/ws10670o-s04942.html'
        r = TU.reconcile_names(self.nm, self.stage, res, apply=False)
        self.assertIn('year folder 2026 -> 2025', r['renamed'][0]['why'])

    def test_check_names_after_writes_a_record_and_handles_missing_result(self):
        out = self.tmp / 'saver_out'; out.mkdir(); (out / 'result.json').write_text(json.dumps(self.saved_as_named()))
        r = TU.check_names_after(self.stage, {'out_dir': str(out)}, apply=True)
        self.assertTrue(r['present']); self.assertEqual(r['confirmed'], 8)
        self.assertTrue((self.stage / 'names_result.json').is_file())
        self.assertIn('error', TU.check_names_after(self.stage, {'out_dir': str(self.tmp / 'nope')}, apply=False))


if __name__ == '__main__':
    unittest.main()
