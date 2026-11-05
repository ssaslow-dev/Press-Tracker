"""ORIGLINKS-v1 (patch 31): a save rebuilds the Originals tab from Coverage; hyperlinks on Originals must survive (the switch-over put 43 there and the
first real save refused with 'Originals: hyperlinks dropped 43 -> 0'). Uses the repo snapshot workbook (data/). Fast (about 20 s).

    python3 -I work/localapp/app/tests/test_originals_links.py -v"""
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_printread_ocr as P  # noqa: E402

REPO = P.REPO
CHAIN = P.CHAIN + ['31_sheet_task_originals_links']
WB = next((REPO / 'data').rglob('AJG Coverage - NewsBank.xlsx'), None)


def load():
    P.CHAIN = CHAIN
    return P.load()


class Stub:
    def __init__(self, wb):
        self.wb, self.ws = wb, wb['Coverage']
        self.hdr = [c.value for c in self.ws[1]]
        self.col = {h: i + 1 for i, h in enumerate(self.hdr) if h}
        self.last_row = self.ws.max_row

    def get(self, r, col):
        return self.ws.cell(r, self.col[col]).value


@unittest.skipIf(WB is None, 'no snapshot workbook in data/')
class OriginalsLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = load()

    def test_links_survive_rebuild(self):
        import openpyxl
        d = Path(tempfile.mkdtemp())
        src = d / 'before.xlsx'
        shutil.copy2(WB, src)
        wb = openpyxl.load_workbook(src)
        s = Stub(wb)
        o = wb['Originals']
        oh = [c.value for c in o[1]]
        ai, ui = oh.index('Article ID') + 1, oh.index('Publisher link') + 1
        # like the switch-over: links put on both tabs for some rows, and on Originals only for others
        cov_rows = {str(s.ws.cell(r, s.col['Article ID']).value): r for r in range(2, s.last_row + 1)}
        both = only = 0
        for r in range(2, o.max_row + 1):
            aid, url = str(o.cell(r, ai).value), o.cell(r, ui).value
            if not (url and str(url).startswith('http')) or o.cell(r, ui).hyperlink is not None:
                continue
            if both < 20:
                o.cell(r, ui).hyperlink = url
                s.ws.cell(cov_rows[aid], s.col['Publisher link']).hyperlink = url
                both += 1
            elif only < 23:
                o.cell(r, ui).hyperlink = url
                only += 1
            else:
                break
        wb.save(src)
        n_before = self.st._vt_hyperlinks(src)['Originals']
        self.assertGreaterEqual(n_before, 43)
        wb = openpyxl.load_workbook(src)
        self.st.rebuild_originals(Stub(wb))
        out = d / 'after.xlsx'
        wb.save(out)
        n_after = self.st._vt_hyperlinks(out)['Originals']
        self.assertGreaterEqual(n_after, n_before)
        # each old link is still on the same story and column, same target
        b = openpyxl.load_workbook(src)['Originals']
        a = openpyxl.load_workbook(out)['Originals']

        def links(ws):
            h = [c.value for c in ws[1]]
            k = h.index('Article ID')
            return {(str(row[k].value), h[c.column - 1]): c.hyperlink.target for row in ws.iter_rows(min_row=2) for c in row if c.hyperlink is not None}
        lb, la = links(b), links(a)
        self.assertTrue(set(lb.items()) <= set(la.items()), [k for k in lb if la.get(k) != lb[k]][:5])
        shutil.rmtree(d, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
