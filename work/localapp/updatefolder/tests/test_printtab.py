"""PRINTPAGES-v1 / ORIGCOPIES-v1: the for-Update file carries (a) a `files` column in the rows block and (b) one kind-'P' row per "Unlinked print pages" row with a
print-page link (make_for_update.extend_rows), so the station recognises print pages and rows that already hold a NewsBank PDF. Uses the snapshot workbook in data/ (skipped without it)."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
WB = REPO / 'data' / 'AJG Coverage - NewsBank.xlsx'


@unittest.skipUnless(WB.is_file(), 'no snapshot workbook')
class PrintTab(unittest.TestCase):
    def test_extend_rows(self):
        import make_for_update as M
        wb = WB
        def check(n, ok, x=''):
            self.assertTrue(ok, n + ' -> ' + str(x))
        import openpyxl
        w = openpyxl.load_workbook(wb, read_only=True, data_only=True)
        cov = list(w['Coverage'].iter_rows(values_only=True)); ch = cov[0]; ci = {h: i for i, h in enumerate(ch)}
        sample = [r for r in cov[1:200] if r[ci['Article ID']]]
        block = {'cols': ['aid', 'sid', 'kind', 'outlet', 'date', 'hl', 'links'], 'rows': [[str(r[ci['Article ID']]), str(r[ci['Story ID']] or ''), 'O', str(r[ci['Outlet']] or ''), '', '', []] for r in sample], 'next': {'aid': 1}}
        out = M.extend_rows(block, wb)
        up = list(w['Unlinked print pages'].iter_rows(values_only=True)); ui = {h: i for i, h in enumerate(up[0])}
        want = [r for r in up[1:] if r[ui['Article ID']] and (r[ui['NewsBank print-page link']] or r[ui['NewsBank print article link']])]
        prow = [r for r in out['rows'] if r[2] == 'P']
        check('the rows block gains a `files` column, one value per row', out['cols'][-1] == 'files' and all(len(r) == len(out['cols']) for r in out['rows']), out['cols'])
        check('one kind-P row per Unlinked print pages row with a print-page link (%d)' % len(want), len(prow) == len(want) and len(want) > 1000, (len(prow), len(want)))
        one = next(r for r in prow if r[0] == '05432')
        check('row 05432: Inland Valley Daily Bulletin, 2026-10-04, its print-page link', one[3] == 'Inland Valley Daily Bulletin' and one[4] == '2026-10-04' and 'docref=image/v2%3A183FBD71DC75BC70' in one[6][0], one)
        withfile = [r for r in out['rows'] if r[2] != 'P' and r[-1]]
        check('Coverage rows carry their saved-copy names (File name; File name 2; Other files) in `files`', len(withfile) > 50 and any(r[-1].lower().endswith('.pdf') for r in withfile) and any('nb' in r[-1] for r in withfile), len(withfile))
        check('no article text anywhere in the added data (names and links only)', all(len(str(r[-1])) < 400 for r in out['rows']))
        again = M.extend_rows(out, wb)
        check('running it twice changes nothing', again is out or again == out)

if __name__ == '__main__':
    unittest.main()
