"""N16: take_update.chain_explains / skip_saved_runs on a later, complete update folder whose earlier part was already saved (fast, no save program).

    cd work/localapp/updatefolder && python3 -I -m unittest discover -s tests -t . -p "test_partial.py" -v
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import formats as F            # noqa: E402
import take_update as TU       # noqa: E402
from layout import PCLayout    # noqa: E402
from test_nbpdf import good_pdf   # noqa: E402

X = 'a' * 64        # the workbook the for-Update file was made from


def folder(tmp: Path, with_names=True):
    """two runs: run-a (story jg-aaaaaa, a pages doc, a tone, a story PDF) and run-b (jg-bbbbbb); a shared reprint candidate rp-shared named by both"""
    db = tmp / 'db'
    for d in ('runs', 'pages', 'tones', 'authors', 'files'):
        (db / d).mkdir(parents=True, exist_ok=True)
    lib = {}
    names_items = []
    for r, code, n in (('run-a', 'jg-aaaaaa', 1), ('run-b', 'jg-bbbbbb', 2)):
        pdf = good_pdf() + b'\n%% scan ' + str(n).encode() + b'\n'
        (db / 'files' / f'pg-{n}.pdf').write_bytes(pdf)
        (db / 'runs' / f'{r}.json').write_text(json.dumps({'at': '2026-11-05T01:00:00Z', 'mode': 'find', 'status': 'done', 'stories': [code], 'reprints': [{'story': code, 'outlet': 'X'}],
                                                           'rows': [{'Article ID': f'NEW-{r}-1', 'Tracker story code': code, 'Headline': 'H ' + r}], 'print_pages': [], 'extra_copies': [], 'shared': 'rp-shared' if r == 'run-b' else ''}))
        (db / 'pages' / f'{code}.json').write_text(json.dumps({'url': 'https://x.test/' + r, 'clean': '<p>text</p>', 'nb': {'file': f'files/pg-{n}.pdf', 'pdf_sha256': hashlib.sha256(pdf).hexdigest(), 'kind': 'print_page', 'as': 'new'}}))
        (db / 'tones' / f'{code}.json').write_text(json.dumps({'tone': 'Neutral'}))
        (db / 'authors' / f'{code}.json').write_text(json.dumps({'author': 'A'}))
        lib[f'library/2026/ws1069{n}o-s0496{n}.html'] = b'<p>' + r.encode() + b'</p>'
        names_items.append({'run': r, 'row': 0, 'doc': code, 'aid': f'1069{n}', 'sid': f's0496{n}', 'kind': 'o', 'fmt': 'ws', 'year': '2026', 'copy': f'library/2026/ws1069{n}o-s0496{n}.html', 'raw': '', 'pdf': '', 'pdf_for': ''})
    (db / 'pages' / 'rp-shared.json').write_text(json.dumps({'url': 'https://x.test/shared', 'clean': '<p>s</p>'}))
    extra = {'replaces': 'u_v1.zip', 'folder_number': 2}
    if with_names:
        extra['names'] = {'version': 1, 'today': '2026-11-05', 'from_next': {'aid': 10691, 'sid': 4961, 's': 4961, 'pr': 245}, 'items': names_items, 'releases': []}
    return F.pack_update_zip(tmp / 'u_v2.zip', db, X, extra_manifest=extra, library=lib if with_names else None)


class Partial(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.lay = PCLayout(self.tmp / 'app')
        self.lay.workbook.parent.mkdir(parents=True)
        self.lay.state.mkdir(parents=True)
        self.lay.workbook.write_bytes(b'workbook after the first save')
        self.now = F.sha256_file(self.lay.workbook)

    def tearDown(self):
        self._t.cleanup()

    def ledger(self, *entries):
        (self.lay.state / 'ledger.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in entries), encoding='utf-8')

    def test_skip_keeps_only_the_unsaved_run(self):
        zp = folder(self.tmp / 'z')
        r = TU.inspect_update(zp, self.lay)
        self.assertEqual(r['runs'], ['run-a', 'run-b'])
        self.ledger({'verb': 'save', 'run': 'run-a', 'before_sha': X, 'after_sha': self.now})
        chain = TU.chain_explains(self.lay, X, r['runs'])
        self.assertEqual(len(chain), 1)
        sk = TU.skip_saved_runs(self.lay, r['update_id'], {'run-a': '2026-11-05T01:30:00Z'}, chain=chain)
        self.assertEqual(sk['runs'], ['run-b'])
        self.assertTrue(sk['fingerprint_rebased'])
        st = Path(r['stage'])
        have = sorted(str(p.relative_to(st)) for p in st.rglob('*') if p.is_file())
        self.assertIn('db/runs/run-b.json', have)
        self.assertNotIn('db/runs/run-a.json', have)
        self.assertNotIn('db/pages/jg-aaaaaa.json', have)
        self.assertNotIn('db/tones/jg-aaaaaa.json', have)
        self.assertNotIn('db/authors/jg-aaaaaa.json', have)
        self.assertIn('db/pages/jg-bbbbbb.json', have)
        self.assertIn('db/pages/rp-shared.json', have, 'a document only the unsaved run names stays; one nobody owns is not removed')
        self.assertNotIn('db/files/pg-1.pdf', have)
        self.assertIn('db/files/pg-2.pdf', have)
        self.assertNotIn('library/2026/ws10691o-s04961.html', have)
        self.assertIn('library/2026/ws10692o-s04962.html', have)
        m = json.loads((st / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(m['runs'], ['run-b'])
        self.assertEqual([i['run'] for i in m['names']['items']], ['run-b'])
        self.assertEqual(m['source']['workbook_sha256'], self.now)
        self.assertEqual(m['partial']['earlier_workbook_sha256'], X)
        self.assertEqual(list(m['partial']['skipped_runs']), ['run-a'])
        self.assertTrue(all((st / k).is_file() or k.startswith('files/') for k in m['files']), 'the manifest lists only what is still staged')
        self.assertEqual(TU.fingerprint_status(m['source']['workbook_sha256'], self.lay.workbook)['status'], 'match')

    def test_chain_refuses_anything_else(self):
        zp = folder(self.tmp / 'z')
        r = TU.inspect_update(zp, self.lay)
        runs = r['runs']
        self.assertIsNone(TU.chain_explains(self.lay, X, runs), 'no ledger: nothing explains the change')
        self.ledger({'verb': 'save', 'run': 'edits-1234', 'before_sha': X, 'after_sha': self.now})          # a "Save my edits"
        self.assertIsNone(TU.chain_explains(self.lay, X, runs))
        self.ledger({'verb': 'save', 'run': 'run-other', 'before_sha': X, 'after_sha': self.now})            # another update
        self.assertIsNone(TU.chain_explains(self.lay, X, runs))
        self.ledger({'verb': 'save', 'run': 'run-a', 'before_sha': X, 'after_sha': 'c' * 64}, {'verb': 'init', 'after_sha': self.now})   # a hand edit accepted afterwards
        self.assertIsNone(TU.chain_explains(self.lay, X, runs))
        self.ledger({'verb': 'save', 'run': 'run-a', 'before_sha': X, 'after_sha': 'c' * 64}, {'verb': 'save', 'run': 'run-b', 'before_sha': 'c' * 64, 'after_sha': self.now})
        self.assertEqual(len(TU.chain_explains(self.lay, X, runs)), 2, 'two saves of this folder\'s own runs, linked end to end')

    def test_without_chain_the_fingerprint_is_left_alone(self):
        r = TU.inspect_update(folder(self.tmp / 'z'), self.lay)
        sk = TU.skip_saved_runs(self.lay, r['update_id'], {'run-a': 'x'}, chain=None)
        self.assertFalse(sk['fingerprint_rebased'])
        m = json.loads((Path(r['stage']) / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(m['source']['workbook_sha256'], X)
        self.assertEqual(TU.fingerprint_status(m['source']['workbook_sha256'], self.lay.workbook)['status'], 'mismatch')

    def test_all_or_none_saved_is_not_for_this(self):
        r = TU.inspect_update(folder(self.tmp / 'z'), self.lay)
        with self.assertRaises(ValueError):
            TU.skip_saved_runs(self.lay, r['update_id'], {'run-a': 'x', 'run-b': 'y'})
        with self.assertRaises(ValueError):
            TU.skip_saved_runs(self.lay, r['update_id'], {})


if __name__ == '__main__':
    unittest.main()
