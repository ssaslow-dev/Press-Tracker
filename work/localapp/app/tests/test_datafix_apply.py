"""DATAFIX-v1 on the Switch-over changes screen: the approved data fixes (cell fixes shipped in station/data/approved, the row-changing ones in datafix_structural).
    AJG_TEST_BUILD=<fresh linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_datafix_apply.py -v
Runs the station modules of the build in this process on a hard-linked working copy whose workbook is the 0bccc1fc copy ($SCRATCH/wb_0bccc1fc.xlsx, the one the proposals
were made from). Steps run in screen order: rename_files, datafix, datafix_structural (then prjudge for the 13 organisation posts).
"""
import json
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402
from test_rename import load_modules, count_files  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_datafix_apply'
S = {}


def rows_of(RF, wb):
    t = RF.read_rows(wb, ('Coverage', 'Originals', 'Unlinked print pages'))
    return {k: ({str(d['Article ID']): d for _, d in v[1]}, v[0]) for k, v in t.items()}


def setUpModule():
    shutil.rmtree(BASE, ignore_errors=True)
    root = T.make_work(BASE, 'a', 'keeper')
    S['root'] = root
    S['C'], S['RF'], S['SW'], S['TU'] = load_modules(root)
    lay = S['lay'] = S['C'].layout(root)
    wb = Path(lay.workbook)
    wb.unlink()
    shutil.copy2(T.SCRATCH / 'wb_0bccc1fc.xlsx', wb)
    assert S['TU'].init_baseline(lay, note='test: 0bccc1fc')['exit_code'] == 0


def tearDownModule():
    shutil.rmtree(BASE, ignore_errors=True)


class Datafix(unittest.TestCase):
    maxDiff = None

    def init_fn(self, note):
        return S['TU'].init_baseline(S['lay'], note=note)['exit_code']

    def test_1_preview_and_apply(self):
        lay, SW, RF = S['lay'], S['SW'], S['RF']
        before = rows_of(RF, lay.workbook)
        S['before'] = before
        pv = SW.preview_all(lay)
        st = {s['id']: s for s in pv['steps']}
        self.assertEqual(pv['blocked'], '')
        self.assertGreater(st['datafix']['n'], 800, st['datafix']['lines'])
        self.assertEqual(st['datafix_structural']['n'], 32 + 2, st['datafix_structural']['lines'])
        self.assertTrue(any('Marisa Kendall' in l for l in st['datafix']['lines']), 'the two items for Sammy are listed')
        self.assertTrue(any('01920' in l for l in st['datafix_structural']['lines']))
        files0 = count_files(Path(lay.library))
        ids = ['rename_files', 'datafix', 'datafix_structural']
        r = SW.apply_steps(lay, ids, {i: st[i]['digest'] for i in ids}, self.init_fn)
        self.assertTrue(r['ok'], r)
        self.assertEqual([x['id'] for x in r['results']], ids)
        self.assertEqual(count_files(Path(lay.library)), files0, 'no library file lost')
        S['after'] = rows_of(RF, lay.workbook)

    def test_2_cell_fixes(self):
        b, a = S['before']['Coverage'][0], S['after']['Coverage'][0]
        for aid in ('00169', '00170', '10618'):
            self.assertEqual(a[aid]['Language'], 'Spanish', aid)
        cleared = [x for x in b if str(b[x].get('Author 1') or '') and not str(a[x].get('Author 1') or '')]
        self.assertEqual(len(cleared), 14)
        # print-page fills: the 10 high rows have their link cells filled; Edition changed only where it said Web
        import csv
        fills = list(csv.DictReader(open(HERE.parent / 'src' / 'station' / 'data' / 'approved' / '01_print_pages_A.csv', encoding='utf-8')))
        edition = [f for f in fills if f['Column'] == 'Edition']
        self.assertEqual(len(edition), 22)
        done = sum(1 for f in edition if a[f['Article ID']]['Edition'] == 'Web + Print')
        self.assertGreaterEqual(done, 15)
        for f in fills:
            if f['Column'] not in ('Edition',) and not str(b[f['Article ID']].get(f['Column']) or ''):
                self.assertEqual(str(a[f['Article ID']].get(f['Column'])), f['New value'], (f['Article ID'], f['Column']))
        # no page keeps NewsBank spacing in the rows that were fixed
        pages = list(csv.DictReader(open(HERE.parent / 'src' / 'station' / 'data' / 'approved' / '05_newsbank_pages.csv', encoding='utf-8')))
        self.assertEqual(sum(1 for p in pages if str(a[p['Article ID']].get('Page')) == p['New value']), 117)
        # nothing else moved: every changed Coverage cell is in a column the fixes, the roles or the renames touch
        allowed = {'Language', 'Author 1', 'Author / byline', 'Author title', 'Author 2', 'Author 3', 'Author 4', 'Author 5', 'Author 6', 'Page', 'Section', 'Print headline', 'Edition', 'Print Article ID',
                   'Print date', 'Old Print Article ID', 'NewsBank print-page link', 'NewsBank print page article link via CA State Library', 'Newsbank APA citation (print page)',
                   'Outlet city', 'File name', 'File name 2', 'Other files', 'Original or reprint', 'Team note', 'Tone', 'Tone note', 'Tone rated by', 'Topic', 'Bills', '# of reprints', 'Role'}
        bad = set()
        for x in b:
            if x not in a:
                bad.add(('row lost', x))
                continue
            for k, v in b[x].items():
                if str(v if v is not None else '') != str(a[x].get(k) if a[x].get(k) is not None else '') and k not in allowed:
                    bad.add((x, k))
        self.assertFalse(bad, sorted(bad)[:8])
        self.assertEqual(set(b) - set(a), set())

    def test_3_structural(self):
        b, a = S['before'], S['after']
        ub, ua = b['Unlinked print pages'][0], a['Unlinked print pages'][0]
        gone = set(ub) - set(ua)
        self.assertEqual(len(gone), 32)
        self.assertEqual(set(ua) - set(ub), set())
        retired = list((Path(S['lay'].data) / 'switchover').glob('retired_unlinked_print_pages_*.csv'))
        self.assertEqual(len(retired), 1)
        for key, new_o, old_o in (('s00512', '01829', '08145'), ('s00985', '03482', '03492')):
            ca = a['Coverage'][0]
            self.assertEqual(ca[new_o]['Original or reprint'], 'Original')
            self.assertEqual(ca[old_o]['Original or reprint'], 'Reprint')
            self.assertEqual(ca[new_o]['Tone'], b['Coverage'][0][old_o]['Tone'])
            self.assertFalse(ca[old_o].get('Tone'))
            self.assertIn('is the Original', str(ca[old_o]['Team note']))
            self.assertEqual(sum(1 for d in ca.values() if d['Story ID'] == key and d['Original or reprint'] == 'Original'), 1)
            self.assertIn(new_o, a['Originals'][0])
            self.assertNotIn(old_o, a['Originals'][0])
            # the file follows the role
            nm = str(ca[new_o]['File name'])
            self.assertIn(f'{new_o}o-{key}', nm, nm)
        # Originals = Coverage's Original rows, in order
        self.assertEqual(len(a['Originals'][0]), sum(1 for d in a['Coverage'][0].values() if d['Original or reprint'] == 'Original'))

    def test_4_org_posts(self):
        lay, SW = S['lay'], S['SW']
        pv = SW.preview_all(lay)
        st = {s['id']: s for s in pv['steps']}
        self.assertEqual(len(st['prjudge']['detail']['org']), 0)
        orgs = [json.loads(l) for l in []]
        cfg = json.loads((HERE.parent / 'src' / 'station' / 'data' / 'prjudge_v2.json').read_text(encoding='utf-8'))
        mine = [u['aid'] for u in cfg['unmark'] if u.get('outlet') == 'California Apartment Association']
        self.assertTrue(mine)
        r = SW.apply_steps(S['lay'], ['prjudge'], {'prjudge': st['prjudge']['digest']}, self.init_fn)
        self.assertTrue(r['ok'], r)
        after = rows_of(S['RF'], S['lay'].workbook)['Coverage'][0]
        for aid in mine:
            self.assertEqual(after[aid]['Press release'], 'No', aid)
        self.assertEqual(S['C'].workbook_state(S['lay']).get('baseline'), 'ok')


if __name__ == '__main__':
    unittest.main()
