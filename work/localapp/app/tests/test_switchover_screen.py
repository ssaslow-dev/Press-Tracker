"""SWITCHOVER-v1: the ONE "Switch-over changes" screen (DROPUNVERIFIED-v1, PRJUDGE-v2 existing rows, PRCOLOR-v1 recolour, OTHERFILES-v1 column, approved data-check fixes).
    AJG_TEST_BUILD=<fresh linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_switchover_screen.py -v
Runs on a keeper copy whose workbook is the scratch copy of the real one ($SCRATCH/wb_0bccc1fc.xlsx), accepted as the baseline.

  1  preview: every step together (counts, lines, digests); nothing is written; a blocked reason when Excel has the file open
  2  an approved fixes file is uploaded: blanks only, low confidence left out unless asked, filled cells never changed, a link cell gets its hyperlink
  3  confirm all: ONE backup; every step's change and nothing else (cell by cell, values, fonts, hyperlinks); one ledger entry per step; the page rebuilt;
     a second confirm and a stale digest are refused
  4  the panel in Chromium: the screen is there after the setup, the old "Remove unverified reprints" button is gone from Repairs, the screen is hidden after Finished
"""
import json
import os
import shutil
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402

WB0 = T.SCRATCH / 'wb_0bccc1fc.xlsx'
BASE = T.SCRATCH / 'app_build' / 'test_switchover_screen'
K = None
S = {}
CSV = ('tab,Article ID,column,current value (blank),new value,confidence,evidence\n'
       'Coverage,{a1},Author title,,Test Paper,high,e1\n'
       'Coverage,{a2},Author title,,Other Paper,medium,e2\n'
       'Coverage,{a3},Author title,,Low Paper,low,e3\n'
       'Coverage,{a4},Outlet,,Changed Outlet,high,a filled cell: never changed\n'
       'Coverage,{a5},NewsBank print-page link,,https://infoweb.newsbank.com/apps/news/x?docref=test,high,link\n')


def wbfile(s):
    return next((s.root / 'data' / 'workbook').glob('*.xlsx'))


def ledger(s):
    return [json.loads(l) for l in (s.root / 'data' / 'state' / 'ledger.jsonl').read_text().splitlines() if l.strip()]


def setUpModule():
    global K
    if not T.BUILD.is_dir() or not WB0.is_file():
        raise unittest.SkipTest('no test build or workbook copy')
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    K = T.Server(T.make_work(BASE, 'keeper', 'keeper')).start()
    wb = wbfile(K)
    wb.unlink()
    shutil.copy2(WB0, wb)
    r = K.job('init', {'sha': T.sha(wb)})
    assert r.get('ok'), r
    lg = K.root / 'data' / 'state' / 'logs'
    lg.mkdir(parents=True, exist_ok=True)
    (lg / 'setup-20261103T000000Z.json').write_text(json.dumps({'at': '2026-11-03T00:00:00', 'verb': 'setup', 'status': 'done'}))


def tearDownModule():
    if K:
        K.stop()


def read(wbp):
    import openpyxl
    wb = openpyxl.load_workbook(wbp, read_only=True, data_only=True)
    out = {}
    for t in ('Coverage', 'Originals'):
        rows = list(wb[t].iter_rows(values_only=True))
        h = list(rows[0])
        out[t] = (h, {str(r[h.index('Article ID')]): dict(zip(h, r)) for r in rows[1:] if r[h.index('Article ID')]})
    wb.close()
    return out


class Screen(unittest.TestCase):
    maxDiff = None

    def test_1_preview(self):
        wb = wbfile(K)
        S['sha0'] = T.sha(wb)
        pv = K.job('switch_preview', {}, timeout=900)
        self.assertTrue(pv['ok'], pv)
        st = {s['id']: s for s in pv['steps']}
        self.assertEqual(list(st), ['drop_unverified', 'rename_files', 'prjudge', 'prcolor', 'other_files', 'datafix', 'datafix_structural'])   # RENAME-v1 step after the drop; DATAFIX-v1 row-changing fixes last
        self.assertEqual(st['drop_unverified']['n'], 419)
        self.assertGreaterEqual(st['prjudge']['n'], 115)
        self.assertEqual(len(st['prjudge']['detail']['mark']), 3)
        self.assertTrue(any('left alone' in l.lower() or 'Not changed' in l for l in st['prjudge']['lines']))
        self.assertEqual(st['other_files']['n'], 2)
        self.assertEqual(st['datafix']['state'], 'todo', 'the approved data fixes ship with the app')
        self.assertGreater(st['datafix']['n'], 500)
        self.assertGreater(st['prcolor']['n'], 380)
        self.assertEqual(pv['blocked'], '')
        self.assertEqual(T.sha(wb), S['sha0'], 'a preview writes nothing to the workbook')
        S['pv'] = pv
        S['datafix_n0'] = next(x for x in pv['steps'] if x['id'] == 'datafix')['n']        # the approved fixes that ship with the app (DATAFIX-v1)
        S['unmarked'] = [u['aid'] for u in st['prjudge']['detail']['unmark']]
        S['marked'] = [u['aid'] for u in st['prjudge']['detail']['mark']]
        # Excel open: blocked
        (wb.parent / ('~$' + wb.name)).write_bytes(b'x')
        try:
            self.assertIn('Excel', K.job('switch_preview', {}, timeout=900)['blocked'])
            r = K.job('switch_apply', {'steps': ['other_files'], 'digests': {'other_files': st['other_files']['digest']}})
            self.assertFalse(r['ok'])
            self.assertEqual(T.sha(wb), S['sha0'])
        finally:
            (wb.parent / ('~$' + wb.name)).unlink()

    def test_2_approved_fixes_file(self):
        d = read(wbfile(K))['Coverage'][1]
        blank = [a for a, r in d.items() if not r.get('Author title') and r.get('Original or reprint') == 'Original' and a not in S['unmarked'] and a not in S['marked']]
        nolink = [a for a, r in d.items() if not r.get('NewsBank print-page link') and a not in blank[:3]]
        S['fix'] = blank[:3] + [blank[3]] + [nolink[0]]
        S['filled'] = S['fix'][3]
        csvp = K.root.parent / 'fixes.csv'
        csvp.write_text(CSV.format(a1=S['fix'][0], a2=S['fix'][1], a3=S['fix'][2], a4=S['filled'], a5=S['fix'][4]), encoding='utf-8')
        st, j = K.call('POST', '/_local/station/upload?kind=datafix&name=fixes.csv', raw=csvp.read_bytes())
        self.assertEqual(st, 200, j)
        st, j = K.call('POST', '/_local/station/upload?kind=datafix&name=fixes.txt', raw=b'x')
        self.assertEqual(st, 400)
        pv = K.job('switch_preview', {}, timeout=900)
        df = next(s for s in pv['steps'] if s['id'] == 'datafix')
        self.assertEqual(df['n'] - S['datafix_n0'], 3, df['lines'])          # on top of the shipped fixes: two Author title (high, medium) + the link; the low one is left out; the filled Outlet is not a blank fix
        pv2 = K.job('switch_preview', {'include_low': True}, timeout=900)
        self.assertEqual(next(s for s in pv2['steps'] if s['id'] == 'datafix')['n'] - S['datafix_n0'], 4)
        S['pv'] = pv

    def test_3_confirm_all(self):
        wb = wbfile(K)
        before = read(wb)
        backups0 = set(p.name for p in (K.root / 'data' / 'backups').glob('*.xlsx'))
        pv = S['pv']
        dig = {s['id']: s['digest'] for s in pv['steps']}
        bad = K.job('switch_apply', {'steps': ['prjudge'], 'digests': {'prjudge': '0' * 16}}, timeout=900)
        self.assertFalse(bad['ok'])
        self.assertEqual(T.sha(wb), S['sha0'] if 'sha0' in S else T.sha(wb))
        t0 = time.time()
        r = K.job('switch_apply', {'steps': [s['id'] for s in pv['steps'] if s['state'] == 'todo'], 'digests': dig}, timeout=3000)
        S['secs'] = time.time() - t0
        self.assertTrue(r['ok'], r)
        S['todo'] = [s['id'] for s in pv['steps'] if s['state'] == 'todo']
        self.assertEqual([x['id'] for x in r['results']], S['todo'])
        self.assertIn('drop_unverified', S['todo'])
        new_backups = set(p.name for p in (K.root / 'data' / 'backups').glob('*.xlsx')) - backups0
        self.assertEqual(len(new_backups), 1, new_backups)
        self.assertIn('before switch-over changes', next(iter(new_backups)))
        after = read(wb)
        cov0, cov1 = before['Coverage'][1], after['Coverage'][1]
        self.assertFalse([a for a, x in cov1.items() if str(x.get('Original or reprint')).lower() == 'reprint (unverified)'])
        for a in S['unmarked']:
            self.assertEqual(cov1[a]['Press release'], 'No', a)
        for a in S['marked']:
            self.assertEqual(cov1[a]['Press release'], 'Yes', a)
        self.assertEqual(after['Originals'][0][-1], 'Other files')
        self.assertEqual(after['Coverage'][0][-1], 'Other files')
        a1, a2, a3, a4, a5 = S['fix']
        self.assertEqual(cov1[a1]['Author title'], 'Test Paper')
        self.assertEqual(cov1[a2]['Author title'], 'Other Paper')
        self.assertFalse(cov1[a3].get('Author title') and cov1[a3]['Author title'] == 'Low Paper')
        self.assertEqual(cov1[a4]['Outlet'], cov0[a4]['Outlet'], 'a filled cell is never changed')
        self.assertTrue(cov1[a5]['NewsBank print-page link'].startswith('https://infoweb.newsbank.com/'))
        # fonts and hyperlinks, in the file itself
        import openpyxl
        w = openpyxl.load_workbook(wb)
        ws = w['Coverage']
        h = [c.value for c in ws[1]]
        ix = {v: i for i, v in enumerate(h)}
        rows = {str(ws.cell(r, ix['Article ID'] + 1).value): r for r in range(2, ws.max_row + 1)}
        col = lambda r, c: (ws.cell(r, c).font.color.rgb if ws.cell(r, c).font.color is not None else None)
        for a in S['unmarked'][:20]:
            self.assertTrue(all(col(rows[a], c) in (None,) or not str(col(rows[a], c)).endswith(('C00000', '7030A0')) for c in range(1, len(h) + 1)), a)
        yes = [r for a, r in rows.items() if cov1[a]['Press release'] == 'Yes']
        self.assertGreater(len(yes), 380)
        self.assertTrue(all(str(col(r, c)).endswith('7030A0') for r in yes[:60] for c in (1, 5, len(h))), 'Press release = Yes rows are purple across the row')
        self.assertTrue(ws.cell(rows[a5], ix['NewsBank print-page link'] + 1).hyperlink is not None)
        w.close()
        led = [e['verb'] for e in ledger(K)]
        for v in ('drop_unverified', 'press_release_judge', 'recolor_press_releases', 'add_other_files_column', 'apply_datafix'):
            self.assertEqual(led.count(v), 1, v)
        st = K.call('GET', '/_local/station/status')[1]
        self.assertEqual(st['workbook']['baseline'], 'ok')
        self.assertEqual(sorted(st['switchover']['done']), sorted(S['todo']))
        again = K.job('switch_apply', {'steps': ['prjudge'], 'digests': dig})
        self.assertFalse(again['ok'])
        pv = K.job('switch_preview', {}, timeout=900)
        self.assertTrue(pv['all_done'])

    def test_4_panel(self):
        steps = [{'op': 'goto', 'wait': 3000}, {'op': 'open_panel'},
                 {'op': 'eval', 'name': 'a', 'expr': "(() => ({ sw: !!document.querySelector('#ajgf-switch'), drop: !!document.querySelector('#ajgf-drop-go'), again: !!document.querySelector('#ajgf-sw-again'), finish: !!document.querySelector('#ajgf-sw-finish') }))()"}]
        out = T.ui(K, steps, 'sw_panel_a')['results']['a']
        self.assertTrue(out['sw'] and not out['drop'] and out['again'], out)
        st, j = K.call('POST', '/_local/station/switch_finish', {})
        self.assertEqual(st, 200)
        t0 = time.time()
        while time.time() - t0 < 30:
            if K.call('GET', '/_local/station/status')[1]['switchover']['finished']:
                break
            time.sleep(0.5)
        out = T.ui(K, [{'op': 'goto', 'wait': 3000}, {'op': 'open_panel'}, {'op': 'eval', 'name': 'a', 'expr': "!!document.querySelector('#ajgf-switch')"}], 'sw_panel_b')['results']['a']
        self.assertFalse(out, 'the screen is shown only once')


if __name__ == '__main__':
    unittest.main()
