"""PC-side tests of the NEWSBANKPDF-v1 proposals (run: cd work/localapp/newsbank_pc && python3 -I -m unittest discover -s tests -t . -v). They build their own inputs:
a synthetic NewsBank batch (the generator in work/localapp/station/tests/nb/) cut the way the station cuts it (page range + CropBox + /AJGBands)."""
import io, json, os, subprocess, sys, tempfile
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
NBPC = HERE.parent
STATION_TESTS = NBPC.parent / 'station' / 'tests' / 'nb'
sys.path.insert(0, str(NBPC))
from pypdf import PdfReader, PdfWriter  # noqa: E402
from pypdf.generic import NameObject, ArrayObject, FloatObject, TextStringObject  # noqa: E402
import pdftext_pypdf as T  # noqa: E402


_BATCH = {}


def batch_dir():
    if not _BATCH:
        d = Path(tempfile.mkdtemp(prefix='nbpdf'))
        subprocess.run([sys.executable, '-I', str(STATION_TESTS / 'make_nb_pdfs.py'), str(d)], check=True, capture_output=True)
        _BATCH['d'] = d; _BATCH['exp'] = json.loads((d / 'expected.json').read_text(encoding='utf-8'))
    return _BATCH['d'], _BATCH['exp']


def cut(src: Path, first: int, last: int, bands, dest: Path):
    """what the station does: copy pages first..last (1-based), crop shared pages, write /AJGBands"""
    r = PdfReader(str(src)); w = PdfWriter()
    for p in range(first - 1, last):
        w.add_page(r.pages[p])
    bl = []
    for i, b in bands.items():
        pg = w.pages[i]; mb = pg.mediabox
        pg.cropbox.lower_left = (float(mb.left), b['bottom']); pg.cropbox.upper_right = (float(mb.right), b['top'])
        bl.append({'i': i, 'top': b['top'], 'bottom': b['bottom']})
    w.add_metadata({'/AJGBands': json.dumps(bl)} if bl else {})
    with open(dest, 'wb') as f:
        w.write(f)


class Band(unittest.TestCase):
    def test_plain_pdf_reads_as_before(self):
        out, exp = batch_dir()
        t = T.pdf_text(str(out / 'batch_B.pdf'))      # page-aligned batch, no bands
        self.assertIn('Gabriel unveils plan', t); self.assertIn('Citation (apa Style)', t)

    def test_banded_story_excludes_neighbours(self):
        out, exp = batch_dir(); tmp_path = Path(tempfile.mkdtemp())
        items = {}
        for i in exp['batch_A']['items']: items.setdefault(i['key'], i)      # 'new1' appears twice (the repeated story): keep the first
        H = 841.89
        it = items['long2']; prv = items['new1']    # 'long2' starts mid-page 1, right below new1
        top1 = H - (prv['end_y_from_top'] + it['start_y_from_top']) / 2
        dest = tmp_path / 'long2.pdf'
        cut(out / 'batch_A.pdf', it['start_page'], it['end_page'], {0: {'top': top1, 'bottom': 0}}, dest)
        whole = T.pdf_text(str(dest))
        plain = PdfWriter(); r = PdfReader(str(out / 'batch_A.pdf'))
        for p in range(it['start_page'] - 1, it['end_page']): plain.add_page(r.pages[p])
        pp = tmp_path / 'long2_plain.pdf'; plain.write(str(pp))
        raw = T.pdf_text(str(pp))
        self.assertIn('Gabriel unveils plan', raw)       # the neighbours leak without the band
        self.assertIn('Budget chair pushes wildfire recovery', whole)
        for bad in ('Gabriel unveils plan', 'Valley Courier Test'):
            self.assertNotIn(bad, whole)
        self.assertIn('Citation (apa Style)', whole); self.assertIn('docref=news/', whole.replace('\n', ''))

    def test_unreadable_file_is_none(self):
        p = Path(tempfile.mkdtemp()) / 'x.pdf'; p.write_bytes(b'not a pdf')
        self.assertIsNone(T.pdf_text(str(p)))


if __name__ == '__main__':
    unittest.main()
