"""NEWSBANKPDF-v1: the PC side of story PDFs in an update folder (files/<id>.pdf). Builds its own small PDFs with pypdf and zips with
formats.pack_update_zip; nothing under data/ is read.

    cd work/localapp/updatefolder && python3 -I -m unittest discover -s tests -t . -p "test_nbpdf.py" -v
"""
import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
UF = HERE.parent
sys.path.insert(0, str(UF))
import formats as F            # noqa: E402
import take_update as TU       # noqa: E402
from layout import PCLayout    # noqa: E402

from pypdf import PdfWriter    # noqa: E402
from pypdf.generic import NameObject, DictionaryObject, TextStringObject, ArrayObject  # noqa: E402

WB_SHA = 'a' * 64


def good_pdf(n_pages=1, text=None) -> bytes:
    w = PdfWriter()
    for _ in range(n_pages):
        w.add_blank_page(595, 842)
    w.add_metadata({'/Title': 'A story'})
    b = io.BytesIO(); w.write(b); return b.getvalue()


def evil(kind: str) -> bytes:
    w = PdfWriter(); w.add_blank_page(595, 842)
    if kind == 'openaction':
        js = DictionaryObject({NameObject('/S'): NameObject('/JavaScript'), NameObject('/JS'): TextStringObject('app.alert(1)')})
        w._root_object[NameObject('/OpenAction')] = w._add_object(js)
    elif kind == 'docjs':
        w.add_js('app.alert(1)')
    elif kind == 'embedded':
        w.add_attachment('payload.exe', b'MZ')
    elif kind == 'launch':
        la = DictionaryObject({NameObject('/S'): NameObject('/Launch'), NameObject('/F'): TextStringObject('cmd.exe')})
        w.pages[0][NameObject('/AA')] = DictionaryObject({NameObject('/O'): w._add_object(la)})
    elif kind == 'annot_js':
        from pypdf.annotations import Link
        a = DictionaryObject({NameObject('/Type'): NameObject('/Annot'), NameObject('/Subtype'): NameObject('/Link'),
                              NameObject('/Rect'): ArrayObject([NameObject('/x')] if False else []),
                              NameObject('/A'): DictionaryObject({NameObject('/S'): NameObject('/JavaScript'), NameObject('/JS'): TextStringObject('x')})})
        w.pages[0][NameObject('/Annots')] = ArrayObject([w._add_object(a)])
    elif kind == 'encrypted':
        w.encrypt('pw')
    b = io.BytesIO(); w.write(b); data = b.getvalue()
    if kind == 'hexname':      # /JS written as /J#53: a lexical scan for "/JS" alone would miss it
        js = DictionaryObject({NameObject('/S'): NameObject('/JavaScript'), NameObject('/JS'): TextStringObject('app.alert(1)')})
        w2 = PdfWriter(); w2.add_blank_page(595, 842); w2._root_object[NameObject('/OpenAction')] = w2._add_object(js)
        b = io.BytesIO(); w2.write(b); data = b.getvalue().replace(b'/JavaScript', b'/Java#53cript').replace(b'/JS ', b'/J#53 ').replace(b'/OpenAction', b'/Open#41ction')
    return data


def make_update(tmp: Path, pdfs: dict, *, refs=None, name='u.zip') -> Path:
    """pdfs: {file id: bytes}; every pdf gets a pages doc naming it unless refs overrides ({file id: (doc id, sha or None)})"""
    db = tmp / 'db'; (db / 'runs').mkdir(parents=True); (db / 'pages').mkdir(); (db / 'files').mkdir()
    (db / 'runs' / 'run-nb1.json').write_text(json.dumps({'at': '2026-11-02T10:00:00Z', 'mode': 'newsbank', 'newsbank': '2026-11-02', 'status': 'done', 'rows': [{'Article ID': 'NEW-run-nb1-1'}]}))
    for fid, b in pdfs.items():
        (db / 'files' / f'{fid}.pdf').write_bytes(b)
    for fid, b in pdfs.items():
        did, sha = (refs or {}).get(fid, (f'jg-{fid[-6:]}', hashlib.sha256(b).hexdigest()))
        (db / 'pages' / f'{did}.json').write_text(json.dumps({'url': 'https://infoweb.newsbank.com/x', 'title': 't', 'clean': '<p>t</p>', 'nb': {'file': f'files/{fid}.pdf', 'pdf_sha256': sha, 'docref': 'news/1'}}))
    return F.pack_update_zip(tmp / name, db, WB_SHA)


def rewrite_zip(src: Path, dst: Path, edit):
    """copy a zip, letting edit(name, bytes) -> bytes | None change or drop entries (manifest left alone: a tampering test)"""
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zo:
        for i in zi.infolist():
            b = edit(i.filename, zi.read(i))
            if b is not None:
                zo.writestr(i.filename, b)
    return dst


class PdfFormat(unittest.TestCase):
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
        pdfs = {'nb-0123456789abcdef': good_pdf(2), 'nb-fedcba9876543210': good_pdf(1)}
        zp = make_update(self.tmp, pdfs)
        with zipfile.ZipFile(zp) as z:
            names = set(z.namelist())
        self.assertIn('files/nb-0123456789abcdef.pdf', names)
        m = json.loads(zipfile.ZipFile(zp).read('manifest.json'))
        self.assertEqual(m['files']['files/nb-0123456789abcdef.pdf']['kind'], 'pdf')
        r = self.inspect(zp)
        stage = Path(r['stage'])
        for fid, b in pdfs.items():
            self.assertEqual((stage / 'db' / 'files' / f'{fid}.pdf').read_bytes(), b)    # where the saver's --db copy (and so sheet_task) finds them
        self.assertTrue((stage / 'db' / 'pages' / 'jg-abcdef.json').is_file())
        self.assertEqual(r['files'], 5)      # 2 PDFs, 2 pages docs, 1 run

    def test_reference_checker_accepts_it_too(self):
        zp = make_update(self.tmp, {'nb-0123456789abcdef': good_pdf()})
        with zipfile.ZipFile(zp) as z:
            infos = F.scan_zip(z, zp.stat().st_size)
            entries = {i.filename: F.read_entry(z, i) for i in infos}
        man = json.loads(entries.pop('manifest.json'))
        F.check_manifest(man, entries)

    def test_the_three_named_dangers_are_refused(self):
        for kind, tok in (('openaction', '/OpenAction'), ('launch', '/Launch'), ('embedded', '/EmbeddedFile')):
            with self.subTest(kind):
                tmp = self.tmp / kind; tmp.mkdir()
                e = self.refused(make_update(tmp, {'nb-aaaaaaaaaaaaaaaa': evil(kind)}), 'BAD_PDF')
                self.assertIn(tok, e.msg)
                self.assertTrue(any(tok in x for x in e.detail['problems']), e.detail)

    def test_javascript_everywhere_it_can_hide(self):
        for kind in ('docjs', 'annot_js', 'hexname', 'encrypted'):
            with self.subTest(kind):
                tmp = self.tmp / kind; tmp.mkdir()
                self.refused(make_update(tmp, {'nb-aaaaaaaaaaaaaaaa': evil(kind)}), 'BAD_PDF')

    def test_without_pypdf_the_lexical_scan_still_refuses(self):
        for kind in ('openaction', 'launch', 'embedded', 'hexname'):
            with self.subTest(kind), mock.patch.dict(sys.modules, {'pypdf': None}):
                self.assertTrue(F.pdf_problems(evil(kind)), kind)
        with mock.patch.dict(sys.modules, {'pypdf': None}):
            self.assertEqual(F.pdf_problems(good_pdf(3)), [])

    def test_a_clean_pdf_with_odd_bytes_is_not_a_false_alarm(self):
        # a page whose content stream merely holds the characters "/JS /AA /Launch": stream data is not read as names
        from pypdf.generic import DecodedStreamObject
        w = PdfWriter(); w.add_blank_page(595, 842)
        st = DecodedStreamObject(); st.set_data(b'q /JS /AA /Launch /OpenAction /EmbeddedFile Q')
        w.pages[0][NameObject('/Contents')] = w._add_object(st)
        out = io.BytesIO(); w.write(out)
        self.assertIn(b'/JS /AA /Launch', out.getvalue())
        self.assertEqual(F.pdf_problems(out.getvalue()), [])
        with mock.patch.dict(sys.modules, {'pypdf': None}):
            self.assertEqual(F.pdf_problems(out.getvalue()), [])

    def test_not_a_pdf_with_a_pdf_name(self):
        self.refused(make_update(self.tmp, {'nb-aaaaaaaaaaaaaaaa': b'MZ\x90\x00 this is a program'}), 'BAD_PDF')

    def test_a_pdf_nothing_refers_to_is_refused(self):
        zp = make_update(self.tmp, {'nb-aaaaaaaaaaaaaaaa': good_pdf()})
        z2 = self.tmp / 'u2.zip'
        extra = good_pdf(2)
        m = json.loads(zipfile.ZipFile(zp).read('manifest.json')); m['files']['files/nb-bbbbbbbbbbbbbbbb.pdf'] = {'sha256': hashlib.sha256(extra).hexdigest(), 'bytes': len(extra)}
        with zipfile.ZipFile(zp) as zi, zipfile.ZipFile(z2, 'w') as zo:
            for i in zi.infolist():
                zo.writestr(i.filename, json.dumps(m) if i.filename == 'manifest.json' else zi.read(i))
            zo.writestr('files/nb-bbbbbbbbbbbbbbbb.pdf', extra)
        self.refused(z2, 'UNLISTED_FILE')

    def test_a_named_pdf_that_is_missing(self):
        zp = make_update(self.tmp, {'nb-aaaaaaaaaaaaaaaa': good_pdf()})
        m = json.loads(zipfile.ZipFile(zp).read('manifest.json')); del m['files']['files/nb-aaaaaaaaaaaaaaaa.pdf']
        z2 = rewrite_zip(zp, self.tmp / 'u2.zip', lambda n, b: json.dumps(m).encode() if n == 'manifest.json' else None if n.endswith('.pdf') else b)
        self.refused(z2, 'MISSING_FILE')

    def test_pages_doc_with_another_checksum_than_the_file(self):
        b = good_pdf()
        self.refused(make_update(self.tmp, {'nb-aaaaaaaaaaaaaaaa': b}, refs={'nb-aaaaaaaaaaaaaaaa': ('jg-aaaaaa', 'f' * 64)}), 'HASH_MISMATCH')

    def test_edited_pdf_fails_the_manifest_checksum(self):
        zp = make_update(self.tmp, {'nb-aaaaaaaaaaaaaaaa': good_pdf()})
        z2 = rewrite_zip(zp, self.tmp / 'u2.zip', lambda n, b: b + b'\n%x' if n.endswith('.pdf') else b)
        self.refused(z2, 'HASH_MISMATCH')

    def test_pdf_names_outside_the_pattern(self):
        zp = make_update(self.tmp, {'nb-aaaaaaaaaaaaaaaa': good_pdf()})
        for bad in ('files/x.exe', 'files/sub/x.pdf', 'files/../x.pdf', 'files/CON.pdf', 'other/x.pdf', 'files/x.PDF.js'):
            with self.subTest(bad):
                ok, why = F.entry_ok(bad)
                self.assertFalse(ok, bad)

    def test_story_pdf_size_cap(self):
        info = zipfile.ZipInfo('files/nb-aaaaaaaaaaaaaaaa.pdf'); info.file_size = F.MAX_PDF_BYTES + 1
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('manifest.json', '{}')
        self.assertEqual(F.entry_cap('files/a.pdf'), F.MAX_PDF_BYTES)
        self.assertEqual(F.entry_cap('db/runs/a.json'), F.MAX_FILE_BYTES)

    def test_older_pc_rule_json_only_collections_unchanged(self):
        self.assertFalse(F.entry_ok('db/clips/x.json')[0])      # still not allowed
        self.assertTrue(F.entry_ok('db/pages/x.json')[0])


if __name__ == '__main__':
    unittest.main()
