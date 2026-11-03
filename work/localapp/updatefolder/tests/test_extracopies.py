"""OTHERFILES-v1 / ORIGCOPIES-v1: a run document's `extra_copies` name PDFs (files/<id>.pdf) that are another original copy of a story already in the tracker.
The same PDF checks apply as for a story PDF (checksum, safety, nothing unlisted).

    cd work/localapp/updatefolder && python3 -I -m unittest discover -s tests -t . -p "test_extracopies.py" -v
"""
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import formats as F            # noqa: E402
import take_update as TU       # noqa: E402
from layout import PCLayout    # noqa: E402
from test_nbpdf import good_pdf, evil   # noqa: E402

WB_SHA = 'b' * 64


def make(tmp: Path, extras: dict, *, sha_override=None, drop_file=False, extra_unlisted=None) -> Path:
    db = tmp / 'db'
    (db / 'runs').mkdir(parents=True)
    (db / 'files').mkdir()
    items = []
    for fid, b in extras.items():
        if not drop_file:
            (db / 'files' / f'{fid}.pdf').write_bytes(b)
        items.append({'aid': '00124', 'fmt': 'pq', 'file': f'files/{fid}.pdf', 'pdf_sha256': sha_override or hashlib.sha256(b).hexdigest()})
    for fid, b in (extra_unlisted or {}).items():
        (db / 'files' / f'{fid}.pdf').write_bytes(b)
    (db / 'runs' / 'run-x1.json').write_text(json.dumps({'at': '2026-11-03T10:00:00Z', 'mode': 'newsbank', 'status': 'done', 'rows': [], 'extra_copies': items}))
    return F.pack_update_zip(tmp / 'u.zip', db, WB_SHA)


class ExtraCopies(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.tmp = Path(self.t.name)
        self.lay = PCLayout(self.tmp / 'app')

    def tearDown(self):
        self.t.cleanup()

    def refused(self, zp, code):
        with self.assertRaises(F.UpdateRefused) as c:
            TU.inspect_update(zp, self.lay)
        self.assertEqual(c.exception.code, code, c.exception.msg)
        stg = self.lay.updates / 'staging'
        self.assertFalse(stg.exists() and any(stg.iterdir()), 'a refused update must leave nothing in staging')

    def test_good_extra_copy_is_staged_where_the_save_looks(self):
        b = good_pdf(2)
        r = TU.inspect_update(make(self.tmp, {'pq-aaaaaaaaaaaaaaaa': b}), self.lay)
        self.assertEqual((Path(r['stage']) / 'db' / 'files' / 'pq-aaaaaaaaaaaaaaaa.pdf').read_bytes(), b)

    def test_wrong_checksum_is_refused(self):
        self.refused(make(self.tmp, {'pq-aaaaaaaaaaaaaaaa': good_pdf()}, sha_override='0' * 64), 'HASH_MISMATCH')

    def test_missing_file_is_refused(self):
        self.refused(make(self.tmp, {'pq-aaaaaaaaaaaaaaaa': good_pdf()}, drop_file=True), 'MISSING_FILE')

    def test_a_pdf_no_run_names_is_refused(self):
        self.refused(make(self.tmp, {'pq-aaaaaaaaaaaaaaaa': good_pdf()}, extra_unlisted={'pq-bbbbbbbbbbbbbbbb': good_pdf(3)}), 'UNLISTED_FILE')

    def test_dangerous_pdf_is_refused(self):
        self.refused(make(self.tmp, {'pq-aaaaaaaaaaaaaaaa': evil('openaction')}), 'BAD_PDF')

    def test_a_path_in_the_file_field_is_refused(self):
        db = self.tmp / 'db'
        (db / 'runs').mkdir(parents=True)
        (db / 'runs' / 'run-x1.json').write_text(json.dumps({'at': '2026-11-03T10:00:00Z', 'mode': 'newsbank', 'status': 'done', 'rows': [],
                                                           'extra_copies': [{'aid': '00124', 'fmt': 'pq', 'file': '../../evil.pdf', 'pdf_sha256': 'c' * 64}]}))
        self.refused(F.pack_update_zip(self.tmp / 'u.zip', db, WB_SHA), 'BAD_PDF')


if __name__ == '__main__':
    unittest.main()
