"""TIDY-v1 (Sammy, 2026-11-03): the PC tracker's layout fixes and the Tracker files panel, checked in the real page (Chromium) of a fresh Linux build.
    AJG_TEST_BUILD=<fresh linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_tidy.py -v      (about 5 minutes; no workbook is written)

  Page   1  the navy table header meets the card border (no pale pixel column next to navy at the left and right edge), at rest and pinned, light and dark,
            1440 and 960 wide, on every list tab and the release and outlet pages (pixel sampling)
         2  Outlets and Reporters: no sideways scroll at 960 (and 1100, 1440); heading, search and Export inside the window
         3  Top issues cells: one non-breaking item per line, no line starting with a comma, the count on its issue's line
         4  headings line up with their tables, Back/Forward as tall as Spreadsheet and Manage, tab text lower by the 1 px fix, Home tile labels at one height
         6  Manage opens on the Update log, "Find & refresh" is hidden, and none of the Update-era phrases is left in Manage, Data checks or the story sheet
  Panel  5  Tracker files is a masthead button directly left of Manage with Manage's class, height, font and radius, for keeper and reader; no floating button;
            the panel opens under the masthead without touching the masthead buttons; Manage and Tracker files never stay open together; the warning is a dot
         7  keeper panel: 1 for Update, 2 bring in update, 3 save my edits, 4 one "Make refresh file" button; "Repairs" is closed and holds Accept the workbook,
            a full refresh file and Rebuild the page; the reader panel has no keeper steps; a first refresh is full on its own (refresh.py _needs_full)
"""
import json
import shutil
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'src' / 'station'))
import support as T  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_tidy'
K = R = None
S = {}
NAVY = (19, 42, 74)
PALE = {(211, 218, 228), (36, 52, 77)}
BANNED = ['Update database', 'Refresh from files', 'ask Claude in chat', 'Rated by Claude', 'Claude rates', 'Desktop/Tracker library', 'on the Mac', 'Press Update',
          'Open this tracker in Claude', 'save the last run to the sheet', 'scheduled', 'for the team', 'shared with everyone']


def setUpModule():
    global K, R
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    K = T.Server(T.make_work(BASE, 'keeper', 'keeper')).start()
    R = T.Server(T.make_work(BASE, 'reader', 'reader')).start()


def tearDownModule():
    for s in (K, R):
        if s:
            s.stop()


class TidyPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        import subprocess
        out = BASE / 'page'
        p = subprocess.run(['node', str(HERE / 'tidy_page.js'), K.base, str(out)], capture_output=True, text=True, timeout=1500,
                           env=dict(os.environ, PLAYWRIGHT_MODULE='/opt/node-tools/node_modules/playwright'))
        if p.returncode:
            raise RuntimeError(p.stderr[-800:])
        cls.res = json.loads(p.stdout.strip().splitlines()[-1])
        cls.out = out

    def test_1_header_meets_the_card_border(self):
        from PIL import Image
        bad, n = [], 0
        for k, tables in self.res['edges'].items():
            im = Image.open(self.out / f'{k}.png').convert('RGB')
            for t in tables:
                l, tp, r, bt = t['th']
                cl, ct, cr, cb = t['card']
                if tp < 0 or bt > im.height - 1:
                    continue
                ym = int((tp + bt) / 2)
                n += 1
                for x in (round(cl), round(cr) - 1):                 # the card's own left and right pixel column
                    px = im.getpixel((x, ym))
                    if px != NAVY:
                        bad.append((k, t['cls'][:20], x, px))
                for x in range(round(cl) - 1, round(cl) + 3):
                    if im.getpixel((x, ym)) in PALE:
                        bad.append((k, 'pale', x))
                if 'rest' in k:                                       # the top of the card is navy too (not a pale line) at the middle of the header
                    top = im.getpixel((int((l + r) / 2), round(tp) - 1))
                    if top != NAVY:
                        bad.append((k, 'top', top))
        self.assertGreater(n, 28, 'header rows sampled')
        self.assertEqual(bad, [], bad[:8])

    def test_1b_corners_rounded_at_rest_square_pinned(self):
        from PIL import Image
        for k, tables in self.res['edges'].items():
            im = Image.open(self.out / f'{k}.png').convert('RGB')
            t = next((t for t in tables if t['th'][1] >= 0 and t['th'][3] < im.height - 1), None)
            if not t:
                continue
            cl, ct = t['card'][0], t['card'][1]
            tp = t['th'][1]
            corner = im.getpixel((round(cl), round(tp) - 1 if 'rest' in k else round(tp)))
            if 'rest' in k:
                self.assertNotEqual(corner, NAVY, f'{k}: the card corner stays rounded at rest (the corner pixel is the page, not navy)')
            elif t['stuck']:
                self.assertEqual(im.getpixel((round(cl), round(tp) + 1)), NAVY, f'{k}: square while pinned')

    def test_2_no_sideways_scroll(self):
        for k, m in self.res['outlets'].items():
            self.assertLessEqual(m['sw'], m['cw'], (k, m))
            self.assertLessEqual(m['table'], m['cardInner'] + 0.5, ('table wider than its card: columns would be cut off', k, m))
            for key in ('head', 'h1', 'search', 'exp'):
                if m[key] is not None:
                    self.assertLessEqual(m[key], m['cw'] + 0.5, (k, key, m))

    def test_3_top_issues_cells(self):
        for k, m in self.res['issues'].items():
            self.assertGreater(m['n'], 20, (k, m))
            self.assertEqual((m['comma'], m['wrapped'], m['rowsWithComma']), (0, 0, 0), (k, m))
            if 'outlets' in k:
                self.assertEqual(m['countAlone'], 0, (k, m))

    def test_4_alignment(self):
        a = self.res['align']
        h = a['headLeft']
        self.assertAlmostEqual(h['h1'], h['card'], delta=0.1, msg=h)
        self.assertAlmostEqual(h['cap'], h['card'], delta=0.1, msg=h)
        self.assertAlmostEqual(h['filters'], h['card'], delta=0.1, msg=h)
        m = a['masthead']
        for key in ('back', 'fwd', 'tf'):
            self.assertAlmostEqual(m[key], m['sheet'], delta=0.1, msg=m)
        self.assertAlmostEqual(m['manage'], m['sheet'], delta=0.1, msg=m)
        self.assertEqual(a['tabPad'], ['7px', '5px'])
        self.assertEqual(len(set(self.res['tiles'])), 1, self.res['tiles'])

    def test_6_wording(self):
        w = self.res['wording']
        tabs = {k: (vis, pr) for k, vis, pr in w['manageTabs']}
        self.assertFalse(tabs['upd'][0], 'Find & refresh is hidden')
        self.assertEqual(w['firstOpen'][0], 'log', 'Manage opens on the Update log')
        self.assertNotIn('Find & refresh', w['firstOpen'][1].split('Update log')[0])
        for where, text in list(w['texts'].items()) + [('sheet', w['sheet'])]:
            for ph in BANNED:
                self.assertNotIn(ph, text, f'{where}: leftover Update-era wording')
        self.assertIn('Tone is rated from the saved copy when a story is added.', w['texts']['defs'])
        self.assertIn('data\\library\\<year>\\', w['texts']['saved'])


STEP_GEOM = """(() => { const f = x => +x.toFixed(2); const q = s => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(), c = getComputedStyle(e);
  return { x: f(r.x), y: f(r.y), r: f(r.right), b: f(r.bottom), w: f(r.width), h: f(r.height), cls: e.className, fs: c.fontSize, fw: c.fontWeight, ff: c.fontFamily, br: c.borderRadius, pos: c.position, par: e.parentElement.className, next: e.nextElementSibling && e.nextElementSibling.id }; };
  return { tf: q('#ajgf-btn'), mg: q('#updBtn'), acts: q('header .hdr-acts'), mast: q('header.mast'), panel: q('#ajgf'), fixed: [...document.querySelectorAll('button')].filter(e => getComputedStyle(e).position === 'fixed').map(e => e.id || e.textContent.trim().slice(0, 20)),
    dotHidden: (document.querySelector('#ajgf-btn .tf-dot') || {}).hidden, upd: !document.querySelector('#upd').hidden, boxOpen: document.querySelector('#ajgf').classList.contains('open') }; })()"""
STEP_PANEL = """(() => { const box = document.querySelector('#ajgf'), rep = box.querySelector('#ajgf-repairs');
  const inRep = e => rep && rep.contains(e);
  const btns = [...box.querySelectorAll('button')].map(b => ({ t: b.textContent.trim(), rep: inRep(b), dis: b.disabled }));
  return { heads: [...box.querySelectorAll('h3')].filter(h => !inRep(h)).map(h => h.textContent.trim()), repHeads: rep ? [...rep.querySelectorAll('h3')].map(h => h.textContent.trim()) : null,
    repOpen: rep ? rep.open : null, btns, text: box.innerText }; })()"""


class TidyPanel(unittest.TestCase):
    def geom(self, server, extra=None):
        steps = [{'op': 'goto', 'wait': 3500}] + (extra or []) + [{'op': 'eval', 'name': 'g', 'expr': STEP_GEOM}]
        out = T.ui(server, steps, 'tidy_geom')
        self.assertEqual(out['errors'], [], out['errors'])
        return out['results']['g']

    def test_5_masthead_button_keeper_and_reader(self):
        for name, s in (('keeper', K), ('reader', R)):
            g = self.geom(s)
            tf, mg = g['tf'], g['mg']
            self.assertIsNotNone(tf, name)
            self.assertEqual(tf['next'], 'updBtn', f'{name}: directly left of Manage')
            self.assertIn('hdr-acts', tf['par'])
            self.assertIn('upd-btn', tf['cls'])
            self.assertAlmostEqual(tf['h'], mg['h'], delta=0.05)
            self.assertAlmostEqual(tf['y'], mg['y'], delta=0.05)
            self.assertEqual((tf['fs'], tf['fw'], tf['ff'], tf['br']), (mg['fs'], mg['fw'], mg['ff'], mg['br']))
            self.assertLess(tf['r'], mg['x'])
            self.assertEqual(g['fixed'], [], f'{name}: no floating button')
            self.assertTrue(g['dotHidden'], f'{name}: no warning, no dot')

    def test_5b_panel_under_the_masthead_and_one_panel_at_a_time(self):
        g = self.geom(K, [{'op': 'open_panel'}])
        self.assertTrue(g['boxOpen'])
        self.assertGreaterEqual(g['panel']['y'], g['mast']['b'], 'the panel starts under the masthead')
        self.assertLessEqual(g['panel']['y'] - g['mast']['b'], 8)
        self.assertEqual(g['panel']['pos'], 'fixed')
        self.assertGreater(g['panel']['b'], 400)
        # Manage open -> Tracker files closes it; Tracker files open -> Manage closes it
        g = self.geom(K, [{'op': 'click_sel', 'sel': '#updBtn'}, {'op': 'wait', 'ms': 800}, {'op': 'eval', 'name': 'x', 'expr': "document.querySelector('#ajgf-btn').click()"}, {'op': 'wait', 'ms': 800}])   # the Manage panel covers the masthead's right side, so its own button is clicked by script
        self.assertTrue(g['boxOpen'] and not g['upd'], g)
        g = self.geom(K, [{'op': 'open_panel'}, {'op': 'click_sel', 'sel': '#updBtn'}, {'op': 'wait', 'ms': 800}])
        self.assertTrue(g['upd'] and not g['boxOpen'], g)

    def test_7_keeper_panel(self):
        out = T.ui(K, [{'op': 'goto', 'wait': 3000}, {'op': 'open_panel'}, {'op': 'eval', 'name': 'p', 'expr': STEP_PANEL}], 'tidy_kp')
        p = out['results']['p']
        self.assertEqual(p['heads'], ['1. Make "for Update" file', '2. Bring in update', '3. Save my edits (0)', '4. Make refresh file (for the other copies)'], p['heads'])
        self.assertFalse(p['repOpen'], 'Repairs is closed')
        SW = ('Check the files', 'Remove unverified reprints', 'Set up again from the Mac library', 'Set up from the Mac library', 'Switch-over changes')   # one-time switch-over items; they live in the Switch-over changes screen
        rh = [h for h in p['repHeads'] if not h.startswith(SW)]
        self.assertEqual(rh, ['Accept the workbook as it is now', 'Make a full refresh file (for a new person)', 'Rebuild the tracker page'])
        outside = [b['t'] for b in p['btns'] if not b['rep']]
        self.assertEqual([t for t in outside if 'refresh' in t.lower()], ['Make refresh file'], 'one refresh button outside Repairs')
        inside = [b['t'] for b in p['btns'] if b['rep'] and not b['t'].startswith(SW)]
        self.assertEqual(inside, ['Accept the workbook as it is now', 'Make a FULL refresh file', 'Rebuild the page'])
        self.assertNotIn('5.', ' '.join(p['heads'])); self.assertNotIn('6.', ' '.join(p['heads']))

    def test_7b_reader_panel(self):
        out = T.ui(R, [{'op': 'goto', 'wait': 3000}, {'op': 'open_panel'}, {'op': 'eval', 'name': 'p', 'expr': STEP_PANEL}], 'tidy_rp')
        p = out['results']['p']
        self.assertEqual(p['heads'], ['1. Make "for Update" file', '2. Bring in refresh file'], p['heads'])
        self.assertEqual(p['repHeads'], ['Rebuild the tracker page'])
        self.assertNotIn('Accept the workbook', p['text'])
        self.assertNotIn('Make refresh file', p['text'])

    def test_5c_warning_is_a_dot_and_opens_repairs(self):
        wb = next((K.root / 'data' / 'workbook').glob('*.xlsx'))
        orig = wb.read_bytes()
        try:
            with open(wb, 'ab') as f:
                f.write(b'\0')                                         # "someone changed it outside the tracker"
            out = T.ui(K, [{'op': 'goto', 'wait': 3000}, {'op': 'wait', 'ms': 1500}, {'op': 'eval', 'name': 'g0', 'expr': STEP_GEOM}, {'op': 'open_panel'}, {'op': 'wait', 'ms': 800},
                           {'op': 'eval', 'name': 'p', 'expr': STEP_PANEL}], 'tidy_dot')
            r = out['results']
            self.assertFalse(r['g0']['dotHidden'], 'the dot shows while the workbook differs from the one the tracker saved')
            self.assertEqual(r['g0']['fixed'], [])
            self.assertTrue(r['p']['repOpen'], 'Repairs opens by itself when the workbook needs accepting')
            self.assertIn('open Repairs below and use "Accept the workbook as it is now"', r['p']['text'].replace('\n', ' '))
        finally:
            wb.write_bytes(orig)


class RefreshAuto(unittest.TestCase):
    """refresh._needs_full: when the plain "Make refresh file" has to carry everything"""

    def lay(self, tmp: Path, ledger_verbs, logs, pages=()):
        (tmp / 'state' / 'logs').mkdir(parents=True)
        (tmp / 'state' / 'ledger.jsonl').write_text(''.join(json.dumps({'verb': v}) + '\n' for v in ledger_verbs))
        for i, (at, added) in enumerate(logs):
            (tmp / 'state' / 'logs' / f'save-{i}.log').write_text(json.dumps({'at': at, 'library': {'pages_added': added}}))
        (tmp / 'library' / '2026').mkdir(parents=True)
        for p in pages:
            (tmp / 'library' / p).write_text('x')
        return types.SimpleNamespace(state=tmp / 'state', library=tmp / 'library')

    def test_cases(self):
        import tempfile
        import refresh as R_
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            st = {'last_seq': 0}
            self.assertIn('first refresh', R_._needs_full(self.lay(d / 'a', ['init'], []), st))
            st = {'last_seq': 2, 'last_at': '2026-11-01T00:00:00Z', 'shards': {}}
            self.assertIn('no record', R_._needs_full(self.lay(d / 'b', ['init', 'save'], []), st))
            st = {'last_seq': 2, 'last_at': '2026-11-01T00:00:00Z', 'shards': {'2026.json': 'x'}}
            ok = self.lay(d / 'c', ['init', 'save', 'save'], [('2026-11-02T00:00:00Z', ['2026/ws1.html'])], ['2026/ws1.html'])
            self.assertEqual(R_._needs_full(ok, st), '')
            gap = self.lay(d / 'e', ['init', 'save', 'save', 'save'], [('2026-11-02T00:00:00Z', ['2026/ws1.html'])], ['2026/ws1.html'])
            self.assertIn('no record of the pages', R_._needs_full(gap, st))
            gone = self.lay(d / 'f', ['init', 'save', 'save'], [('2026-11-02T00:00:00Z', ['2026/ws1.html'])], [])
            self.assertIn('no longer in the library', R_._needs_full(gone, st))
            none = self.lay(d / 'g', ['init', 'save'], [])
            self.assertEqual(R_._needs_full(none, st), '', 'no save since the last refresh file: nothing to carry, an incremental one is complete')


if __name__ == '__main__':
    unittest.main()
