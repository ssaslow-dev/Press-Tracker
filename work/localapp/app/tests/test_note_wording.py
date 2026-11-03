"""NOTE-v1: the "Team note" feature is called "Note" in everything people see. The spreadsheet column keeps its header "Team note".
    AJG_TEST_BUILD=<fresh linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_note_wording.py -v
Checks, in the real page (Chromium) of a keeper copy: no visible text, tooltip, placeholder or label says "team note" (any case) on the main routes, the story sheet,
the Manage panes (Data checks among them), the Tracker files panel and the Clips filter list; a note typed in the story sheet is still kept (db/notes);
a note entered with Edit details still lands in the edits and "Save my edits" still writes it into the Team note column of the workbook.
"""
import json
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402
import test_pcedits as P  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_note_wording'
K = None
S = {}

SCAN = ("const sl = ms => new Promise(r => setTimeout(r, ms));"
        " const scan = () => { const out = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);"
        "  for (let n = w.nextNode(); n; n = w.nextNode()) { const pe = n.parentElement; if (pe && !/^(SCRIPT|STYLE|TEMPLATE)$/.test(pe.tagName)) out.push(n.nodeValue); }"
        "  document.querySelectorAll('[title],[placeholder],[aria-label],[alt],option').forEach(e => { ['title', 'placeholder', 'aria-label', 'alt'].forEach(a => { if (e.getAttribute(a)) out.push(e.getAttribute(a)); }); if (e.tagName === 'OPTION') out.push(e.textContent); });"
        "  return out.filter(t => /team[\\s-]*notes?/i.test(t)); };")


def setUpModule():
    global K
    if not T.BUILD.is_dir():
        raise unittest.SkipTest('no test build')
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    K = T.Server(T.make_work(BASE, 'keeper', 'keeper')).start()
    S['wb0'] = T.sha(P.wbfile(K))
    S['rem'], S['edit'], S['conf'], S['spare'] = P.pick_stories(K)


def tearDownModule():
    if K:
        K.stop()


class NoteWording(unittest.TestCase):
    maxDiff = None

    def test_01_no_visible_team_note(self):
        sid, hl = S['edit'][0], S['edit'][1]['Headline']
        routes = ['#clips', '#reporters', '#outlets', '#press-releases', '#bills', '#story-travel', '#press-releases/pr00208', '#outlets/politico']
        steps = [{'op': 'goto'}]
        for i, h in enumerate(routes):
            steps.append({'op': 'eval', 'name': 'route%d' % i, 'expr': "(async () => { %s location.hash = %s; await sl(2500); return scan(); })()" % (SCAN, json.dumps(h))})
        # the story sheet (opened from Clips), with the Edit details form
        steps.append({'op': 'eval', 'name': 'sheet', 'expr': P.js_open(sid, hl, SCAN + " const a = scan(); const sh = document.querySelector('#sheet'); return [a, !!document.querySelector('#tnote'), sh ? (document.querySelector('label[for=tnote]') || {}).textContent : null];")})
        steps.append({'op': 'eval', 'name': 'form', 'expr': P.js_open(sid, hl, SCAN + " const b = document.querySelector('#sheet [data-editstory]'); b.click(); await sl(600); const f = document.querySelector('#sheet .log-form'); return [scan(), f ? [...f.querySelectorAll('label.wide > span')].map(x => x.textContent) : null];")})
        # the Clips filter list and the Manage panes
        steps.append({'op': 'eval', 'name': 'filters', 'expr': "(async () => { %s location.hash = '#clips'; await sl(2000); const o = [...document.querySelectorAll('option, [data-flt], .chip, button')].map(x => x.textContent.trim()).filter(t => /note/i.test(t)); return [scan(), o]; })()" % SCAN})
        steps.append({'op': 'eval', 'name': 'manage', 'expr': "(async () => { %s document.getElementById('updBtn').click(); await sl(1200); const res = [scan()]; const tabs = [...document.querySelectorAll('#mgTabs [data-mg]')]; const names = tabs.map(t => t.textContent.trim());"
                   " for (const t of tabs) { t.click(); await sl(900); res.push(scan()); } return [res, names]; })()" % SCAN})
        steps.append({'op': 'open_panel'})
        steps.append({'op': 'panel', 'name': 'files'})
        out = T.ui(K, steps, 'note01')
        r = out['results']
        self.assertNotIn('crash', r, r)
        for i, h in enumerate(routes):
            self.assertEqual(r['route%d' % i], [], h)
        self.assertEqual(r['sheet'][0], [], 'story sheet')
        self.assertTrue(r['sheet'][1], 'the note box is there')
        self.assertEqual(r['sheet'][2], 'Note')
        self.assertEqual(r['form'][0], [], 'edit form')
        self.assertIn('Note', r['form'][1])
        self.assertEqual(r['filters'][0], [], 'clips')
        self.assertIn('Has a note', ' | '.join(r['filters'][1]), r['filters'][1])
        self.assertEqual([x for x in r['manage'][0] if x], [], 'manage panes ' + str(r['manage'][1]))
        self.assertNotRegex(r['files'], r'(?i)team note')
        self.assertEqual(out['errors'], [], out['errors'])

    def test_02_note_still_works_and_save_my_edits_fills_the_team_note_column(self):
        sid, hl = S['edit'][0], S['edit'][1]['Headline']
        spare, shl = S['spare'][0], S['spare'][1]['Headline']
        out = T.ui(K, [{'op': 'goto'},
                       # a note typed in the story sheet
                       {'op': 'eval', 'name': 'typed', 'expr': P.js_open(spare, shl, "const t = document.getElementById('tnote'); t.value = 'sheet note NOTE-v1'; t.dispatchEvent(new Event('input', {bubbles: true})); await sl(2000); return [t.value, (document.getElementById('tnoteMeta') || {}).textContent];")},
                       # a note entered with Edit details
                       {'op': 'eval', 'name': 'edit', 'expr': P.js_edit(sid, hl, 'note', 'edit note NOTE-v1')},
                       {'op': 'wait', 'ms': 6500}],
                    'note02')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertEqual(r['typed'][0], 'sheet note NOTE-v1', r['typed'])
        self.assertNotRegex(r['typed'][1] or '', r'(?i)team note')
        self.assertEqual(r['edit'], 'ok', r)
        db = K.root / 'data' / 'db'
        notes = [json.loads(f.read_text()) for f in (db / 'notes').glob('*.json')] if (db / 'notes').is_dir() else []
        self.assertTrue(any('sheet note NOTE-v1' in json.dumps(n) for n in notes), notes)
        docs = P.edit_docs(K)
        self.assertIn(sid, docs, docs)
        self.assertIn('edit note NOTE-v1', json.dumps(docs[sid]), docs[sid])
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'click', 'text': 'Save my edits'},
                       {'op': 'wait_text', 'text': ['If you press Save', 'Nothing new', 'did not finish'], 'timeout': 900000, 'name': 'prev'},
                       {'op': 'mark'}, {'op': 'eval', 'name': 'clicked', 'expr': "(() => { const b = document.querySelector('#ajgf-edits-save'); if (!b || b.disabled) return false; b.click(); return true; })()"},
                       {'op': 'wait_text', 'text': ['Saved.', 'Not saved'], 'timeout': 1200000, 'name': 'saved'}], 'note02b')
        r = out['results']
        self.assertEqual(r['saved'], 'Saved.', r.get('saved_panel'))
        row = P.coverage(K)['Coverage'][sid][0]
        self.assertIn('edit note NOTE-v1', str(row.get('Team note')), row.get('Team note'))
        import openpyxl
        wb = openpyxl.load_workbook(P.wbfile(K), read_only=True)
        hdr = [c for c in next(wb['Coverage'].iter_rows(values_only=True))]
        wb.close()
        self.assertIn('Team note', hdr, 'the spreadsheet column keeps its header')


if __name__ == '__main__':
    unittest.main()
