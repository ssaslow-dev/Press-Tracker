"""PROQUESTPDF-v1: the PC side of ProQuest article PDFs in an update folder (files/<id>.pdf named by a pages doc's `pq.file`). Same safety checks as the
NewsBank story PDFs (they share formats.check_pdfs); this file proves the `pq` key is read the same way and that nothing about a ProQuest PDF can
slip past. Builds its own small PDFs with pypdf; nothing under data/ is read.

    cd work/localapp/updatefolder && python3 -I -m unittest discover -s tests -t . -p "test_pqpdf.py" -v
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
from tests.test_nbpdf import good_pdf, evil, rewrite_zip   # noqa: E402

WB_SHA = 'b' * 64


def make_update(tmp: Path, pdfs: dict, *, refs=None, nb=None, textonly=0, name='u.zip') -> Path:
    """pdfs: {file id: bytes}, each named by a `pq` pages doc (refs overrides {file id: (doc id, sha or None)}); nb: {file id: bytes} named by `nb` docs;
    textonly: that many ProQuest pages docs with no PDF at all (pq.file blank: a text copy only)"""
    db = tmp / 'db'; (db / 'runs').mkdir(parents=True); (db / 'pages').mkdir(); (db / 'files').mkdir()
    (db / 'runs' / 'run-pq1.json').write_text(json.dumps({'at': '2026-11-02T10:00:00Z', 'mode': 'hand', 'proquest': '2026-11-02', 'status': 'done', 'rows': [{'Article ID': 'NEW-run-pq1-1'}]}))
    for fid, b in list(pdfs.items()) + list((nb or {}).items()):
        (db / 'files' / f'{fid}.pdf').write_bytes(b)
    for fid, b in pdfs.items():
        did, sha = (refs or {}).get(fid, (f'jg-{fid[-6:]}', hashlib.sha256(b).hexdigest()))
        (db / 'pages' / f'{did}.json').write_text(json.dumps({'url': 'https://www.proquest.com/docview/3411000001', 'title': 't', 'clean': '<p>t</p>',
                                                              'pq': {'file': f'files/{fid}.pdf', 'pdf_sha256': sha, 'docid': '3411000001', 'header': {'headline': 't'}}}))
    for fid, b in (nb or {}).items():
        (db / 'pages' / f'jg-n{fid[-5:]}.json').write_text(json.dumps({'url': 'https://infoweb.newsbank.com/x', 'title': 't', 'clean': '<p>t</p>', 'nb': {'file': f'files/{fid}.pdf', 'pdf_sha256': hashlib.sha256(b).hexdigest(), 'docref': 'news/1'}}))
    for i in range(textonly):
        (db / 'pages' / f'jg-text0{i}0.json').write_text(json.dumps({'url': 'https://www.proquest.com/docview/0?pdf=x', 'title': 't', 'clean': '<p>t</p>', 'pq': {'file': '', 'pdf_sha256': '', 'header': {'headline': 't'}}}))
    return F.pack_update_zip(tmp / name, db, WB_SHA)


class ProQuestPdf(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.tmp = Path(self.t.name)
        self.lay = PCLayout(self.tmp / 'app')

    def tearDown(self):
        self.t.cleanup()

    def inspect(self, zp):
        return TU.inspect_update(zp, self.lay)

    def refused(self, zp, code):
        with self.assertRaises(F.UpdateRefused) as c:
            self.inspect(zp)
        self.assertEqual(c.exception.code, code, c.exception.msg)
        stg = self.lay.updates / 'staging'
        self.assertFalse(stg.exists() and any(stg.iterdir()), 'a refused update must leave nothing in staging')
        return c.exception

    def test_good_update_is_staged_with_its_pdfs(self):
        pdfs = {'pq-0123456789abcdef': good_pdf(3), 'pq-fedcba9876543210': good_pdf(1)}
        zp = make_update(self.tmp, pdfs)
        m = json.loads(zipfile.ZipFile(zp).read('manifest.json'))
        self.assertEqual(m['files']['files/pq-0123456789abcdef.pdf']['kind'], 'pdf')
        r = self.inspect(zp); stage = Path(r['stage'])
        for fid, b in pdfs.items():
            self.assertEqual((stage / 'db' / 'files' / f'{fid}.pdf').read_bytes(), b)     # where sheet_task finds them (task.db_dir/files/)
        self.assertEqual(r['files'], 5)

    def test_reference_checker_accepts_it_too(self):
        zp = make_update(self.tmp, {'pq-0123456789abcdef': good_pdf()}, nb={'nb-0123456789abcdef': good_pdf(2)})
        with zipfile.ZipFile(zp) as z:
            infos = F.scan_zip(z, zp.stat().st_size)
            entries = {i.filename: F.read_entry(z, i) for i in infos}
        man = json.loads(entries.pop('manifest.json'))
        F.check_manifest(man, entries)

    def test_a_text_copy_with_no_pdf_is_fine(self):
        r = self.inspect(make_update(self.tmp, {'pq-0123456789abcdef': good_pdf()}, textonly=2))
        self.assertEqual(r['files'], 1 + 1 + 1 + 2)

    def test_every_hostile_pdf_is_refused(self):
        for kind, tok in (('openaction', '/OpenAction'), ('launch', '/Launch'), ('embedded', '/EmbeddedFile')):
            with self.subTest(kind):
                tmp = self.tmp / kind; tmp.mkdir()
                e = self.refused(make_update(tmp, {'pq-aaaaaaaaaaaaaaaa': evil(kind)}), 'BAD_PDF')
                self.assertIn(tok, e.msg)
        for kind in ('docjs', 'annot_js', 'hexname', 'encrypted'):
            with self.subTest(kind):
                tmp = self.tmp / kind; tmp.mkdir()
                self.refused(make_update(tmp, {'pq-aaaaaaaaaaaaaaaa': evil(kind)}), 'BAD_PDF')

    def test_one_bad_pdf_refuses_the_whole_update(self):
        self.refused(make_update(self.tmp, {'pq-0123456789abcdef': good_pdf(), 'pq-aaaaaaaaaaaaaaaa': evil('openaction')}), 'BAD_PDF')

    def test_not_a_pdf_with_a_pdf_name(self):
        self.refused(make_update(self.tmp, {'pq-aaaaaaaaaaaaaaaa': b'MZ\x90\x00 this is a program'}), 'BAD_PDF')

    def test_a_pdf_nothing_refers_to_is_refused(self):
        zp = make_update(self.tmp, {'pq-aaaaaaaaaaaaaaaa': good_pdf()})
        z2 = self.tmp / 'u2.zip'; extra = good_pdf(2)
        m = json.loads(zipfile.ZipFile(zp).read('manifest.json')); m['files']['files/pq-bbbbbbbbbbbbbbbb.pdf'] = {'sha256': hashlib.sha256(extra).hexdigest(), 'bytes': len(extra)}
        with zipfile.ZipFile(zp) as zi, zipfile.ZipFile(z2, 'w') as zo:
            for i in zi.infolist():
                zo.writestr(i.filename, json.dumps(m) if i.filename == 'manifest.json' else zi.read(i))
            zo.writestr('files/pq-bbbbbbbbbbbbbbbb.pdf', extra)
        self.refused(z2, 'UNLISTED_FILE')

    def test_a_named_pdf_that_is_missing(self):
        zp = make_update(self.tmp, {'pq-aaaaaaaaaaaaaaaa': good_pdf()})
        m = json.loads(zipfile.ZipFile(zp).read('manifest.json')); del m['files']['files/pq-aaaaaaaaaaaaaaaa.pdf']
        z2 = rewrite_zip(zp, self.tmp / 'u2.zip', lambda n, b: json.dumps(m).encode() if n == 'manifest.json' else None if n.endswith('.pdf') else b)
        self.refused(z2, 'MISSING_FILE')

    def test_pages_doc_with_another_checksum_than_the_file(self):
        self.refused(make_update(self.tmp, {'pq-aaaaaaaaaaaaaaaa': good_pdf()}, refs={'pq-aaaaaaaaaaaaaaaa': ('jg-aaaaaa', 'f' * 64)}), 'HASH_MISMATCH')

    def test_a_pq_doc_may_not_name_a_path_outside_files(self):
        zp = make_update(self.tmp, {'pq-aaaaaaaaaaaaaaaa': good_pdf()})
        def edit(n, b):
            if n.startswith('db/pages/'):
                d = json.loads(b); d['pq']['file'] = 'files/../x.pdf'; return json.dumps(d).encode()
            return b
        z2 = rewrite_zip(zp, self.tmp / 'u2.zip', edit)
        # the manifest checksum of the edited page no longer matches: refused before the path is even looked at
        with self.assertRaises(F.UpdateRefused):
            self.inspect(z2)

    def test_edited_pdf_fails_the_manifest_checksum(self):
        zp = make_update(self.tmp, {'pq-aaaaaaaaaaaaaaaa': good_pdf()})
        self.refused(rewrite_zip(zp, self.tmp / 'u2.zip', lambda n, b: b + b'\n%x' if n.endswith('.pdf') else b), 'HASH_MISMATCH')

    def test_a_pq_doc_naming_a_file_the_pdf_check_would_not_allow(self):
        db = self.tmp / 'db'; (db / 'runs').mkdir(parents=True); (db / 'pages').mkdir()
        (db / 'runs' / 'run-pq1.json').write_text('{"mode":"hand"}')
        (db / 'pages' / 'jg-aaaaaa.json').write_text(json.dumps({'clean': '<p>t</p>', 'pq': {'file': 'files/evil.exe', 'pdf_sha256': 'a' * 64}}))
        zp = F.pack_update_zip(self.tmp / 'u.zip', db, WB_SHA)
        self.refused(zp, 'BAD_PDF')


if __name__ == '__main__':
    unittest.main()
