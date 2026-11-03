"""PCEDITS-v1: story edits and removals made in the PC tracker's page are saved into the workbook with "Save my edits" or together with an update.
    AJG_TEST_BUILD=<fresh linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_pcedits.py -v
Ordered tests sharing state (a keeper copy and a reader copy of the test build). Each preview and save takes 1-3 minutes on the real workbook.

What is checked (all in the real page in Chromium, the real server and the real save program):
  1  a story removed and a field edited in the page land in data/db/edits; the panel offers "Save my edits (2)" with a preview in plain words
  2  a save refused (Excel open; workbook changed after the preview) leaves the edits waiting and the workbook untouched
  3  Save: the story's rows move to the Removed tab ("5 removed in the tracker"), the blank cell is filled, the other cells are untouched, the edits
     docs are MOVED to db/_applied/edits (not deleted), the ledger/backup are right, the page after the reload no longer shows the story
  4  an edit that would overwrite a filled cell is not applied (the workbook keeps its value, said in the preview), and a save program that was
     made to overwrite it anyway is refused by the diff (OVERWRITE); the edit stays waiting
  5  an update brought in with pending edits saves both, and the preview of the update lists the edits
  6  a reader copy: no "Save my edits" in the panel, a one-line note instead, the server and the job both refuse
"""
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_pcedits'
K = R = None
S = {}


def wbfile(s):
    return next((s.root / 'data' / 'workbook').glob('*.xlsx'))


def ledger(s):
    return [json.loads(l) for l in (s.root / 'data' / 'state' / 'ledger.jsonl').read_text().splitlines() if l.strip()]


def edits_dir(s, sub='edits'):
    return s.root / 'data' / 'db' / sub


def edit_docs(s, sub='edits'):
    d = edits_dir(s) if sub == 'edits' else s.root / 'data' / 'db' / sub / 'edits'
    return {f.stem.split('.')[0]: json.loads(f.read_text()) for f in sorted(d.glob('*.json'))} if d.is_dir() else {}


def coverage(srv):
    """{Story ID: [row dict, ...]} of the Coverage tab and the Removed tab, read-only"""
    import openpyxl
    wb = openpyxl.load_workbook(wbfile(srv), read_only=True)
    out = {}
    for tab in ('Coverage', 'Removed'):
        rows = wb[tab].iter_rows(values_only=True)
        h = list(next(rows))
        d = {}
        for r in rows:
            r = dict(zip(h, r))
            if r.get('Story ID'):
                d.setdefault(str(r['Story ID']), []).append(r)
        out[tab] = d
    wb.close()
    return out


def pick_stories(srv):
    """three single-row stories dated 2026 with a link, a blank Bills cell and a filled Outlet: one to remove (preferably with a saved copy), one to edit
    (Bills is blank: the edit fills it), one whose filled Outlet an edit tries to change"""
    cov = coverage(srv)['Coverage']
    single = [(sid, rows[0]) for sid, rows in cov.items()
              if len(rows) == 1 and str(rows[0].get('Date') or '')[:4] == '2026' and not rows[0].get('Bills') and rows[0].get('Outlet') and rows[0].get('Headline')]
    withcopy = [x for x in single if x[1].get('Saved Copy?') == 'Yes' and x[1].get('File name')]
    rem = (withcopy or single)[0]
    rest = [x for x in single if x[0] != rem[0]]
    return rem, rest[0], rest[1], rest[2]


def setUpModule():
    global K, R
    if not T.BUILD.is_dir():
        raise unittest.SkipTest('no test build: python3 -I assemble_app.py --target linux --role keeper')
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    K = T.Server(T.make_work(BASE, 'keeper', 'keeper')).start()
    R = T.Server(T.make_work(BASE, 'reader', 'reader')).start()
    S['wb0'] = T.sha(wbfile(K))
    S['rem'], S['edit'], S['conf'], S['spare'] = pick_stories(K)


def tearDownModule():
    for s in (K, R):
        if s:
            s.stop()


def js_open(sid, hl, then=''):
    """the real page: Clips tab, search the headline, click the story's row (the page keeps its code in a closure, so the DOM is all a person has too).
    Returns 'row' (opened) or 'no row'; `then` is more code that runs with the story open."""
    return ("(async () => { const sid = %s, hl = %s; const sl = ms => new Promise(r => setTimeout(r, ms));"
            " const tab = [...document.querySelectorAll('button,a,[role=tab],nav *')].find(x => /^\\s*Clips\\s*$/.test(x.textContent) && x.offsetParent); if (tab) tab.click(); await sl(1200);"
            " const q = document.getElementById('q'); q.value = hl; q.dispatchEvent(new Event('input', {bubbles: true})); await sl(2500);"
            " const tr = document.querySelector('#tbody tr[data-id=\"' + sid + '\"]'); if (!tr) return 'no row'; tr.click(); await sl(900);"
            " %s })()" % (json.dumps(sid), json.dumps(' '.join(hl.split()[:6])), then or "return 'row';"))


def js_edit(sid, hl, field, value):
    """what a person does in the page: open the story, 'Edit details', change one field, 'Save changes'"""
    return js_open(sid, hl, "const b = document.querySelector('#sheet [data-editstory]'); if (!b) return 'no edit button';"
                   " b.click(); await sl(500); const f = document.querySelector('#sheet .log-form'); if (!f) return 'no form';"
                   " const el = f.querySelector('[data-ef=%s]'); if (!el) return 'no field'; el.value = %s; f.querySelector('[data-logsave]').click(); await sl(1500); return 'ok';"
                   % (field, json.dumps(value)))


def js_remove(sid, hl):
    return js_open(sid, hl, "const b = document.querySelector('#sheet [data-editstory]'); if (!b) return 'no edit button';"
                   " b.click(); await sl(500); const f = document.querySelector('#sheet .log-form'); if (!f) return 'no form';"
                   " f.querySelector('[data-logremove]').click(); await sl(3000); return 'ok';")


def js_sheet_text(sid, hl):
    return js_open(sid, hl, "return document.querySelector('#sheet').innerText;")


class Edits(unittest.TestCase):
    maxDiff = None

    def test_01_edits_made_in_the_page_are_offered_in_the_panel(self):
        st, s = K.call('GET', '/_local/station/status')
        self.assertEqual(s['edits_pending']['n'], 0)
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'panel', 'name': 'p0'}, {'op': 'open_panel'},
                       {'op': 'eval', 'name': 'edit', 'expr': js_edit(S['edit'][0], S['edit'][1]['Headline'], 'bills', 'AB 418')},
                       {'op': 'eval', 'name': 'rm', 'expr': js_remove(S['rem'][0], S['rem'][1]['Headline'])},
                       {'op': 'eval', 'name': 'gone', 'expr': js_open(S['rem'][0], S['rem'][1]['Headline'])},
                       {'op': 'wait', 'ms': 6500}, {'op': 'open_panel'}, {'op': 'panel', 'name': 'p1'},
                       {'op': 'eval', 'name': 'btn', 'expr': "(() => { const b = document.querySelector('#ajgf-edits-go'); return b ? [b.textContent, b.disabled] : null; })()"},
                       {'op': 'screenshot', 'path': str(T.SHOTS / 'pcedits_01_panel.png')}], 'pcedits01')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertIn('3. Save my edits (0)', r['p0'])
        self.assertEqual((r['edit'], r['rm'], r['gone']), ('ok', 'ok', 'no row'), r)
        docs = edit_docs(K)
        self.assertEqual(set(docs), {S['rem'][0], S['edit'][0]}, docs)
        self.assertTrue(docs[S['rem'][0]]['removed'])
        self.assertEqual(docs[S['edit'][0]]['bills'], ['AB 418'])
        self.assertIn('3. Save my edits (2)', r['p1'])
        self.assertEqual(r['btn'], ['Save my edits (2)', False], 'enabled when N > 0')
        self.assertEqual(T.sha(wbfile(K)), S['wb0'], 'nothing is written by merely editing in the page')
        self.assertEqual(out['errors'], [], out['errors'])

    def test_02_refused_saves_leave_the_edits_waiting(self):
        wb = wbfile(K)
        prev = K.job('edits_preview')
        self.assertTrue(prev['ok'] and prev['can_save'], prev)
        S['prev'] = prev
        self.assertTrue(prev['update_id'].startswith('edits-'))
        lines = ' | '.join(prev['lines'])
        self.assertIn('1 story removed', lines)
        self.assertIn('1 story edited', lines)
        self.assertIn('Removed tab', lines)             # the diff line: rows added to the Removed tab
        self.assertIn('blank cell', lines)               # the Bills cell
        self.assertTrue(prev['headline'].startswith('If you press Save'), prev['headline'])
        before_docs = edit_docs(K)
        # (a) Excel opens the workbook after the preview
        lockf = wb.with_name('~$' + wb.name)
        lockf.write_text('x')
        try:
            res = K.job('edits_save', {'update_id': prev['update_id'], 'token': prev['token']})
        finally:
            lockf.unlink()
        self.assertFalse(res['written'], res)
        self.assertIn('Excel has the workbook open', ' '.join(res['lines']))
        # (b) the workbook changed after the preview
        orig = wb.read_bytes()
        with open(wb, 'ab') as f:
            f.write(b'\0')
        try:
            res = K.job('edits_save', {'update_id': prev['update_id'], 'token': prev['token']})
        finally:
            wb.write_bytes(orig)
        self.assertFalse(res['written'], res)
        self.assertIn('not the one the tracker last saved', ' '.join(res['lines']))
        # (c) a made-up token
        res = K.job('edits_save', {'update_id': prev['update_id'], 'token': '0' * 16})
        self.assertFalse(res['written'], res)
        self.assertEqual(T.sha(wb), S['wb0'])
        self.assertEqual(edit_docs(K), before_docs, 'a refused save leaves every edits doc where it was')
        self.assertFalse(edit_docs(K, '_applied'))
        self.assertEqual(list((K.root / 'data' / 'backups').glob('*.xlsx')), [])

    def test_03_save_my_edits_moves_the_story_fills_the_blank_and_sets_the_docs_aside(self):
        rem_sid, edit_sid = S['rem'][0], S['edit'][0]
        before = coverage(K)
        n_cov0 = sum(len(v) for v in before['Coverage'].values())
        n_rm0 = sum(len(v) for v in before['Removed'].values())
        self.assertIn(rem_sid, before['Coverage'])
        keep = {sid: [dict(r) for r in rows] for sid, rows in before['Coverage'].items() if sid not in (rem_sid, edit_sid)}
        copy_name = S['rem'][1].get('File name')
        yr = str(S['rem'][1].get('Date'))[:4]
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'click', 'text': 'Save my edits (2)'},
                       {'op': 'wait_text', 'text': ['If you press Save', 'Nothing new', 'did not finish'], 'timeout': 900000, 'name': 'prev'},
                       {'op': 'screenshot', 'path': str(T.SHOTS / 'pcedits_03_preview.png')},
                       {'op': 'mark'}, {'op': 'eval', 'name': 'clicked', 'expr': "(() => { const b = document.querySelector('#ajgf-edits-save'); if (!b || b.disabled) return false; b.click(); return true; })()"},
                       {'op': 'wait_text', 'text': ['Saved.', 'Not saved'], 'timeout': 1200000, 'name': 'saved'},
                       {'op': 'screenshot', 'path': str(T.SHOTS / 'pcedits_03_saved.png')},
                       {'op': 'wait_reload'},
                       {'op': 'eval', 'name': 'still', 'expr': js_open(rem_sid, S['rem'][1]['Headline'])},
                       {'op': 'eval', 'name': 'bills', 'expr': js_sheet_text(edit_sid, S['edit'][1]['Headline'])},
                       {'op': 'open_panel'}, {'op': 'wait', 'ms': 1500}, {'op': 'panel', 'name': 'after'}], 'pcedits03')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertEqual(r['prev'], 'If you press Save', r['prev_panel'])
        self.assertTrue(r['clicked'])
        self.assertEqual(r['saved'], 'Saved.', r['saved_panel'])
        self.assertIn('Backup of the old workbook', r['saved_panel'])
        self.assertIn('2 edits saved and set aside', r['saved_panel'])
        self.assertEqual(r['still'], 'no row', 'the removed story is gone from the rebuilt page')
        self.assertIn('AB 418', r['bills'], 'the edit is in the rebuilt page')
        self.assertIn('3. Save my edits (0)', r['after'])
        # workbook
        after = coverage(K)
        self.assertNotIn(rem_sid, after['Coverage'])
        self.assertEqual(len(after['Removed'][rem_sid]), len(before['Coverage'][rem_sid]))
        rr = after['Removed'][rem_sid][0]
        self.assertEqual(rr['Category'], '5 removed in the tracker')
        self.assertEqual(rr['From tab'], 'Coverage')
        self.assertEqual(rr['Article ID'], S['rem'][1]['Article ID'])
        self.assertEqual(sum(len(v) for v in after['Coverage'].values()), n_cov0 - len(before['Coverage'][rem_sid]))
        self.assertEqual(sum(len(v) for v in after['Removed'].values()), n_rm0 + len(before['Coverage'][rem_sid]))
        e_before, e_after = before['Coverage'][edit_sid][0], after['Coverage'][edit_sid][0]
        self.assertFalse(e_before['Bills'])
        self.assertEqual(e_after['Bills'], 'AB 418')
        for k, v in e_before.items():
            if k != 'Bills':
                self.assertEqual(e_after[k], v, f'only the blank Bills cell may change ({k})')
        for sid, rows in keep.items():           # every other story is exactly as before (the saver's diff checks the same; this is the belt)
            self.assertEqual(after['Coverage'].get(sid), rows, sid)
        # library: add-only; the removed story's files are moved, not deleted
        lib = K.root / 'data' / 'library'
        if copy_name:
            self.assertFalse((lib / yr / copy_name).exists(), 'the removed story\'s saved copy was moved out of the year folder')
            self.assertTrue(list((lib / '_to_delete').rglob(copy_name)), 'and set aside in _to_delete, not deleted')
        # edits docs: moved, never deleted
        self.assertEqual(edit_docs(K), {})
        applied = edit_docs(K, '_applied')
        self.assertEqual(set(applied), {rem_sid, edit_sid}, applied)
        self.assertEqual(applied[edit_sid]['bills'], ['AB 418'])
        # ledger and backup
        new = T.sha(wbfile(K))
        self.assertNotEqual(new, S['wb0'])
        last = ledger(K)[-1]
        self.assertEqual((last['verb'], last['after_sha'], last['confirmed']), ('save', new, True))
        self.assertEqual([T.sha(b) for b in (K.root / 'data' / 'backups').glob('*.xlsx')], [S['wb0']])
        # no longer in the next "for Update" file's removed list, but the Removed tab keeps it
        st, s = K.call('GET', '/_local/station/status')
        self.assertEqual(s['edits_pending']['n'], 0)
        self.assertEqual(out['errors'], [], out['errors'])
        S['wb1'] = new

    def test_04_edit_of_a_filled_cell_is_not_applied_and_a_tampered_save_is_refused(self):
        sid, row = S['conf'][0], S['conf'][1]
        newname = 'Zzz Test Outlet'
        out = T.ui(K, [{'op': 'goto'}, {'op': 'eval', 'name': 'edit', 'expr': js_edit(sid, row['Headline'], 'outlet', newname)}, {'op': 'wait', 'ms': 1500}], 'pcedits04a')
        self.assertEqual(out['results']['edit'], 'ok', out)
        docs = edit_docs(K)
        self.assertEqual(set(docs), {sid}, docs)
        self.assertEqual(docs[sid]['outlet'], newname)
        # (a) the real save program: sheet_task keeps the workbook's value and says so
        prev = K.job('edits_preview')
        self.assertTrue(prev['ok'], prev)
        lines = ' | '.join(prev['lines'])
        self.assertIn('will not be applied', lines, prev)
        self.assertIn('the workbook keeps its own', lines)
        if prev.get('can_save'):
            res = K.job('edits_save', {'update_id': prev['update_id'], 'token': prev['token']})
            self.assertTrue(res['written'], res)
            cov = coverage(K)['Coverage'][sid][0]
            self.assertEqual(cov['Outlet'], row['Outlet'], 'the filled cell kept its value')
            self.assertNotEqual(cov['Outlet'], newname)
            doc = edit_docs(K)[sid]
            self.assertTrue(doc.get('reported'), 'a conflicting edit is marked reported, not applied and not lost')
            st, s = K.call('GET', '/_local/station/status')
            self.assertEqual(s['edits_pending']['n'], 0, 'a reported edit is not offered again')
            self.assertFalse(edit_docs(K, '_applied').get(sid))
            # put it back to pending for part (b)
            doc.pop('reported')
            (edits_dir(K) / f'{sid}.json').write_text(json.dumps(doc))
        else:
            self.assertEqual(edit_docs(K)[sid]['outlet'], newname, 'nothing to save: the edit simply stays')
        wb_now = T.sha(wbfile(K))
        # (b) a save program that was made to overwrite the filled cell anyway: the diff refuses it (tests/tamper_saver.py edits the pass-2 workbook)
        import openpyxl
        w = openpyxl.load_workbook(wbfile(K), read_only=True)
        h = [c.value for c in next(w['Coverage'].iter_rows(max_row=1))]
        rown = next(i for i, r in enumerate(w['Coverage'].iter_rows(values_only=True), 1) if i > 1 and str(r[h.index('Story ID')]) == sid)
        w.close()
        env = dict(os.environ, AJG_TAMPER=f'Coverage|{rown}|Outlet|{newname}', AJG_SAVER_DIR=str(K.root / 'app' / 'saver'))
        py = str(K.root / 'python' / 'bin' / 'python')
        p = subprocess.run([py, '-B', '-X', 'utf8', '-I', str(K.root / 'app' / 'updatefolder' / 'take_update.py'), 'preview', '--app-root', str(K.root),
                            '--edits-only', '--saver', str(HERE / 'tamper_saver.py')], capture_output=True, text=True, env=env, cwd=K.root)
        res = json.loads(p.stdout.strip().splitlines()[-1])
        self.assertEqual(p.returncode, 2, (p.stdout[-500:], p.stderr[-500:]))
        self.assertEqual((res.get('refusal') or {}).get('code'), 'OVERWRITE', res.get('refusal') or res.get('line'))
        self.assertEqual(T.sha(wbfile(K)), wb_now, 'nothing was written')
        self.assertIn(sid, edit_docs(K), 'the edit stays waiting')
        S['conf_pending'] = sid

    def test_05_update_brought_in_with_pending_edits_saves_both(self):
        sid = S['spare'][0]
        spare_bills = 'AB 2316'
        # a pending edit (fills a blank) next to the one left from test 4 (not applied, reported or not)
        out = T.ui(K, [{'op': 'goto'}, {'op': 'eval', 'name': 'edit', 'expr': js_edit(sid, S['spare'][1]['Headline'], 'bills', spare_bills)}, {'op': 'wait', 'ms': 1500}], 'pcedits05a')
        self.assertEqual(out['results']['edit'], 'ok', out)
        self.assertIn(sid, edit_docs(K))
        z = T.make_update_zip(K.root, BASE / 'upd_edits.zip', 'edits5')
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'file', 'path': str(z)},
                       {'op': 'wait_text', 'text': ['If you press Save'], 'timeout': 900000, 'name': 'prev'},
                       {'op': 'screenshot', 'path': str(T.SHOTS / 'pcedits_05_preview.png')},
                       {'op': 'mark'}, {'op': 'click', 'text': 'Save'},
                       {'op': 'wait_text', 'text': ['Saved.', 'Not saved'], 'timeout': 1200000, 'name': 'saved'},
                       {'op': 'wait_reload'}], 'pcedits05')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertIn('Your edits made in this tracker, saved together with it', r['prev_panel'])
        self.assertIn('2 stories edited', r['prev_panel'], 'the new edit and the one left from test 4')
        self.assertIn('will not be applied', r['prev_panel'], 'the filled-cell edit is said not to apply in the update preview too')
        self.assertEqual(r['saved'], 'Saved.', r['saved_panel'])
        cov = coverage(K)['Coverage']
        self.assertEqual(cov[sid][0]['Bills'], spare_bills, 'the edit went in with the update')
        self.assertTrue(any('edits5' in str(rows[0].get('Headline')) or 'story edits5' in str(rows[0].get('Headline')) for rows in cov.values()),
                        'and the update\'s own story is in')
        self.assertNotIn(sid, edit_docs(K))
        self.assertIn(sid, edit_docs(K, '_applied'))
        self.assertTrue(edit_docs(K)[S['conf_pending']].get('reported'), 'the filled-cell edit was not applied and is marked reported')
        self.assertNotEqual(cov[S['conf_pending']][0]['Outlet'], 'Zzz Test Outlet')
        self.assertTrue((K.root / 'data' / 'db' / 'runs' / 'run-edits5.json').is_file())
        # a second copy of this fix: the preview and the save of ONE update (both compose a db) did not collide
        work = K.root / 'data' / 'updates' / 'work'
        composed = list(work.glob('*/db_composed*'))
        self.assertGreaterEqual(len(composed), 1, 'each call made its own composed folder')
        self.assertEqual(len(composed), len({str(c) for c in composed}))
        self.assertEqual(out['errors'], [], out['errors'])

    def test_06_reader_copy_cannot_save_edits(self):
        st, s = R.call('GET', '/_local/station/status')
        self.assertIsNone(s['edits_pending'])
        for verb, body in (('edits_preview', {}), ('edits_save', {'update_id': 'edits-20261103T000000Z', 'token': 'abcdef12'})):
            st, j = R.call('POST', '/_local/station/' + verb, body)
            self.assertEqual(st, 403, (verb, j))
            self.assertIn('reader copy', j['line'])
            self.assertIn('stay in that copy', j['line'])
        # even a hand-run job refuses
        p = subprocess.run([str(R.root / 'python' / 'bin' / 'python'), '-B', '-X', 'utf8', '-I', 'app/station/station_cli.py', 'edits_preview', '--root', str(R.root)],
                           cwd=R.root, capture_output=True, text=True)
        self.assertIn('reader copy', p.stdout)
        # an edit made in a reader copy stays there
        sid = S['spare'][0]
        out = T.ui(R, [{'op': 'goto'}, {'op': 'eval', 'name': 'edit', 'expr': js_edit(sid, S['spare'][1]['Headline'], 'bills', 'AB 1')}, {'op': 'wait', 'ms': 1500},
                       {'op': 'open_panel'}, {'op': 'panel', 'name': 'p'}, {'op': 'screenshot', 'path': str(T.SHOTS / 'pcedits_06_reader.png')}], 'pcedits06')
        p_ = out['results']['p']
        self.assertNotIn('Save my edits', p_)
        self.assertIn('Stories you edit or remove here stay in this copy only', p_)
        self.assertIn(sid, edit_docs(R))
        self.assertEqual(T.sha(wbfile(R)), S['wb0'])


if __name__ == '__main__':
    unittest.main()
