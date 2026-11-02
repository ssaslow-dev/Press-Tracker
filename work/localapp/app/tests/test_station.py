"""End-to-end tests of the assembled Linux test build: server, page in Chromium, panel, update flow, refresh flow.
    python3 -I -m unittest discover -s work/localapp/app/tests -p "test_station.py"      (needs the build from assemble_app.py --target linux --role keeper)
Slow (a preview and a save each take 1-3 minutes on the real workbook). Tests run in file order and share state."""
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_run'
K = R = None     # keeper / reader servers
S = {}           # shared state between the ordered tests


def setUpModule():
    global K, R
    if not T.BUILD.is_dir():
        raise unittest.SkipTest('no test build: python3 -I assemble_app.py --target linux --role keeper')
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    K = T.Server(T.make_work(BASE, 'keeper', 'keeper')).start()
    R = T.Server(T.make_work(BASE, 'reader', 'reader')).start()
    S['wb0'] = T.sha(next((K.root / 'data' / 'workbook').glob('*.xlsx')))


def tearDownModule():
    for s in (K, R):
        if s:
            s.stop()


def wbfile(s):
    return next((s.root / 'data' / 'workbook').glob('*.xlsx'))


def ledger(s):
    return [json.loads(l) for l in (s.root / 'data' / 'state' / 'ledger.jsonl').read_text().splitlines() if l.strip()]


class Flow(unittest.TestCase):
    maxDiff = None

    def test_01_page_loads_buttons_hidden_note_saved(self):
        story = None
        steps = [{'op': 'goto'},
                 {'op': 'eval', 'name': 'cap0', 'expr': "document.getElementById('helloCap').textContent"},
                 {'op': 'eval', 'name': 'idmap', 'expr': "Object.keys(JSON.parse(document.getElementById('idmap').textContent)).length"},
                 {'op': 'eval', 'name': 'rows', 'expr': "JSON.parse(document.getElementById('data').textContent).length"},
                 {'op': 'eval', 'name': 'hidden', 'expr': """(() => { const out = {}; for (const sel of ['#runFind','#runRefresh','#raStrip','#updGo','#updRefresh','#updSave','#updAdd','#updCopy','#updAgain','[data-runfind]','[data-trate]','[data-afind]','[data-trstory]']) {
                    const e = document.createElement('button'); if (sel[0]==='#') e.id = sel.slice(1); else e.setAttribute(sel.slice(1,-1), ''); document.body.appendChild(e); out[sel] = getComputedStyle(e).display; e.remove(); }
                    const d = document.createElement('button'); d.setAttribute('data-dl','csv'); document.body.appendChild(d); out['[data-dl]'] = getComputedStyle(d).display; d.remove(); return out; })()"""},
                 {'op': 'eval', 'name': 'tab', 'expr': "(() => { const e = [...document.querySelectorAll('button,a,[role=tab],nav *')].find(x => /^\\s*Clips\\s*$/.test(x.textContent) && x.offsetParent); if (e) e.click(); return !!e; })()"},
                 {'op': 'wait', 'ms': 1500},
                 {'op': 'eval', 'name': 'sid', 'expr': "(() => { const tr = document.querySelector('#tbody tr[data-id]'); const id = tr.dataset.id; tr.click(); return id; })()"},
                 {'op': 'wait', 'ms': 1500},
                 {'op': 'eval', 'name': 'typed', 'expr': "(() => { const t = document.querySelector('#tnote'); t.value = 'Test note from the PC tracker'; t.dispatchEvent(new Event('input', {bubbles:true})); return true; })()"},
                 {'op': 'wait', 'ms': 2500},
                 {'op': 'eval', 'name': 'meta', 'expr': "document.querySelector('#tnoteMeta').textContent"},
                 {'op': 'eval', 'name': 'cap1', 'expr': "document.getElementById('helloCap').textContent"},
                 {'op': 'screenshot', 'path': str(T.SHOTS / '01_page.png')}]
        out = T.ui(K, steps, '01')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertEqual(out['errors'], [], out['errors'])
        self.assertGreater(r['rows'], 3000)
        self.assertGreater(r['idmap'], 100)          # sid_map's legacy codes are in the page (HANDOFF 5: they must survive rebuilds)
        S['idmap'] = r['idmap']
        self.assertIn('stories', r['cap0'])
        S['cap0'] = r['cap0']
        for sel, disp in r['hidden'].items():
            if sel == '[data-dl]':
                self.assertNotEqual(disp, 'none', 'downloads must stay visible')
            else:
                self.assertEqual(disp, 'none', sel)
        self.assertIn('Saved for the team', r['meta'])
        self.assertEqual(r['cap0'], r['cap1'], 'counts must not flip after the first load (DATABASIS-v1)')
        f = K.root / 'data' / 'db' / 'notes' / f'{r["sid"]}.json'
        self.assertEqual(json.loads(f.read_text())['text'], 'Test note from the PC tracker')
        S['note_sid'] = r['sid']

    def test_02_make_for_update_downloads_json(self):
        dl = T.SHOTS.parent / 'for_update_download.json'
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'download', 'text': 'Make "for Update" file', 'save': str(dl), 'timeout': 400000},
                       {'op': 'panel', 'name': 'p'}, {'op': 'screenshot', 'path': str(T.SHOTS / '02_make.png')}], '02')
        self.assertNotIn('crash', out['results'], out['results'])
        d = json.loads(dl.read_text(encoding='utf-8'))
        self.assertEqual(d['format'], 'ajg-for-update')
        self.assertEqual(d['fingerprint']['workbook_sha256'], S['wb0'])
        self.assertGreater(len(d['stories']), 3000)
        self.assertNotIn('text_en', d['stories'][0])
        self.assertTrue(list((K.root / 'data' / 'for_update').glob('for_update_*.json')))

    def test_03_tampered_zip_refused_in_plain_words(self):
        good = T.make_update_zip(K.root, BASE / 'good_t.zip', 'tamper1')
        with zipfile.ZipFile(good) as z:
            ents = {i.filename: z.read(i) for i in z.infolist()}
        victim = next(n for n in ents if n.startswith('db/runs/'))
        ents[victim] = ents[victim].replace(b'Gabriel', b'Gabrie1')
        bad = BASE / 'tampered.zip'
        with zipfile.ZipFile(bad, 'w') as z:
            for n, b in ents.items():
                z.writestr(n, b)
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'drop', 'path': str(bad), 'fname': 'tampered.zip'},
                       {'op': 'wait_text', 'text': ['does not match its checksum', 'refused'], 'timeout': 120000}, {'op': 'screenshot', 'path': str(T.SHOTS / '03_tampered.png')}], '03')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertIn('Nothing was saved or changed', r['wait_text_panel'])
        self.assertEqual(list((K.root / 'data' / 'updates' / 'staging').iterdir()), [])
        self.assertEqual(T.sha(wbfile(K)), S['wb0'])

    def test_04_old_fingerprint_warns_and_use_anyway(self):
        z = T.make_update_zip(K.root, BASE / 'oldfp.zip', 'oldfp1', fake_sha='ab' * 32)
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'file', 'path': str(z)},
                       {'op': 'wait_text', 'text': ['Use it anyway'], 'timeout': 120000, 'name': 'warn'}, {'op': 'screenshot', 'path': str(T.SHOTS / '04_warn.png')},
                       {'op': 'click', 'text': 'Use it anyway'},
                       {'op': 'wait_text', 'text': ['If you press Save'], 'timeout': 900000, 'name': 'prev'},
                       {'op': 'screenshot', 'path': str(T.SHOTS / '04_preview_anyway.png')},
                       {'op': 'click', 'text': 'Do not use this update'}, {'op': 'wait', 'ms': 2500}], '04')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertIn('different version of the workbook', r['warn_panel'])
        self.assertIn('added to the Coverage tab', r['prev_panel'])
        self.assertEqual(T.sha(wbfile(K)), S['wb0'])
        self.assertTrue(list((K.root / 'data' / 'updates' / 'rejected').iterdir()), 'set aside, not deleted')

    def test_05_update_preview_save_reload_new_story(self):
        z = T.make_update_zip(K.root, BASE / 'upd1.zip', 'example1')
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'file', 'path': str(z)},
                       {'op': 'wait_text', 'text': ['If you press Save'], 'timeout': 900000, 'name': 'prev'},
                       {'op': 'screenshot', 'path': str(T.SHOTS / '05_preview.png')},
                       {'op': 'mark'}, {'op': 'click', 'text': 'Save'},
                       {'op': 'wait_text', 'text': ['Saved.', 'Not saved'], 'timeout': 1200000, 'name': 'saved'},
                       {'op': 'screenshot', 'path': str(T.SHOTS / '05_saved.png')},
                       {'op': 'wait_reload'},
                       {'op': 'eval', 'name': 'found', 'expr': "JSON.parse(document.getElementById('data').textContent).some(r => (r.hl||'').includes('Gabriel bill test story one'))"},
                       {'op': 'eval', 'name': 'cap', 'expr': "document.getElementById('helloCap').textContent"},
                       {'op': 'eval', 'name': 'idmap', 'expr': "Object.keys(JSON.parse(document.getElementById('idmap').textContent)).length"},
                       {'op': 'eval', 'name': 'tab', 'expr': "(() => { const e = [...document.querySelectorAll('button,a,[role=tab],nav *')].find(x => /^\\s*Clips\\s*$/.test(x.textContent) && x.offsetParent); if (e) e.click(); return !!e; })()"},
                       {'op': 'wait', 'ms': 1500},
                       {'op': 'eval', 'name': 'indexed', 'expr': "new Promise(res => { const t0 = Date.now(); (function w(){ if (!/Indexing/.test(document.getElementById('q').placeholder) || Date.now() - t0 > 120000) res(document.getElementById('q').placeholder); else setTimeout(w, 500); })(); })"},
                       {'op': 'eval', 'name': 'typed', 'expr': "(() => { const q = document.getElementById('q'); q.value = 'quokkaexample1'; q.dispatchEvent(new Event('input', {bubbles:true})); return true; })()"},
                       {'op': 'wait', 'ms': 2500},
                       {'op': 'eval', 'name': 'hits', 'expr': "[...document.querySelectorAll('#tbody tr[data-id]')].map(t => t.innerText.slice(0,120))"},
                       {'op': 'screenshot', 'path': str(T.SHOTS / '05_search.png')}], '05')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertEqual(r['saved'], 'Saved.', r['saved_panel'])
        self.assertIn('Backup of the old workbook', r['saved_panel'])
        self.assertTrue(r['found'], 'the new story must appear in the page after the reload')
        self.assertEqual(out['errors'], [], out['errors'])
        new = T.sha(wbfile(K))
        self.assertNotEqual(new, S['wb0'])
        bks = list((K.root / 'data' / 'backups').glob('*.xlsx'))
        self.assertEqual([T.sha(b) for b in bks], [S['wb0']])
        last = ledger(K)[-1]
        self.assertEqual((last['verb'], last['after_sha'], last['confirmed']), ('save', new, True))
        self.assertTrue((K.root / 'data' / 'db' / 'runs' / 'run-example1.json').is_file())
        self.assertTrue((K.root / 'data' / 'db' / 'notes' / f'{S["note_sid"]}.json').is_file())
        self.assertTrue(list((K.root / 'data' / 'library' / '2026').glob('ws*o-s*.html')))
        self.assertEqual(r['idmap'], S['idmap'], 'legacy codes survive the rebuild')
        self.assertIn('stories', r['cap'])
        self.assertTrue(r['hits'] and 'Gabriel bill test story one' in ' '.join(r['hits']), ('newly saved story must be found by the Clips search', r['indexed'], r['hits']))
        lib = K.root / 'data' / 'library' / '2026'
        saved = [p for p in lib.glob('ws*o-s*.html') if 'quokkaexample1' in p.read_text(encoding='utf-8', errors='replace').lower()]
        self.assertTrue(saved, 'the new page was added to the library')
        for p in saved:     # PHOTOLINK-v1: the photo stays as a link (the program fetched nothing); details in test_photolink.py
            txt = p.read_text(encoding='utf-8', errors='replace')
            self.assertIn('src="https://images.example.test/photo-example1.jpg"', txt, 'remote photos are kept as links')
            self.assertIn('referrerpolicy="no-referrer" loading="lazy"', txt)
        self.assertIn('quokkaexample1', K.get('/articles/2026.json').decode('utf-8').lower(), 'the new copy is in the shard the page reads')
        S['wb1'] = new
        S['pipeline_ok'] = (K.root / 'app' / 'pipeline' / 'PIPELINE.sha256').is_file()

    def test_05b_same_update_cannot_be_taken_in_twice(self):
        st, j = K.upload(BASE / 'upd1.zip')
        res = K.job('inspect', {'file': j['file']})
        self.assertFalse(res['ok']); self.assertEqual(res.get('refused'), 'ALREADY_SAVED'); self.assertIn('already saved', res['line'])
        self.assertEqual(T.sha(wbfile(K)), S['wb1'])

    def test_06_refresh_keeper_to_reader_round_trip(self):
        # a reader note exists before the refresh and must survive it
        (R.root / 'data' / 'db' / 'notes').mkdir(parents=True, exist_ok=True)
        (R.root / 'data' / 'db' / 'notes' / 'reader-note.json').write_text('{"text":"mine","at":"2026-11-02"}')
        (R.root / 'data' / 'db' / 'views').mkdir(parents=True, exist_ok=True)
        (R.root / 'data' / 'db' / 'views' / 'v1.json').write_text('{"name":"my view"}')
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'click', 'text': 'Make refresh file'},
                       {'op': 'wait_text', 'text': ['Made the refresh', 'could not be made', 'Another save'], 'timeout': 900000, 'name': 'mk'}], '06a')
        self.assertIn('Made the refresh', out['results']['mk'], out['results'])
        r1 = sorted((K.root / 'data' / 'refresh_out').glob('refresh_incr_*.zip'))[-1]
        S['r1'] = BASE / r1.name
        shutil.copy2(r1, S['r1'])
        with zipfile.ZipFile(r1) as z:
            names = z.namelist()
        self.assertFalse([n for n in names if n.startswith(('db/', 'notes', 'views', 'edits'))], 'no personal db docs in a refresh')
        self.assertTrue(any(n.startswith('library/2026/') for n in names), 'the page added by the save travels')
        before_sha = T.sha(wbfile(R))
        out = T.ui(R, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'panel', 'name': 'p0'}, {'op': 'file', 'path': str(S['r1'])},
                       {'op': 'mark'}, {'op': 'wait_text', 'text': ['is in.', 'Nothing was changed', 'refused'], 'timeout': 900000, 'name': 'done'},
                       {'op': 'screenshot', 'path': str(T.SHOTS / '06_reader_refresh.png')}, {'op': 'wait_reload'},
                       {'op': 'eval', 'name': 'found', 'expr': "JSON.parse(document.getElementById('data').textContent).some(r => (r.hl||'').includes('Gabriel bill test story one'))"}], '06b')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertNotIn('Bring in update', r['p0']); self.assertNotIn('Accept the workbook', r['p0'])
        self.assertIn('is in.', r['done_panel'])
        self.assertTrue(r['found'])
        self.assertEqual(out['errors'], [], out['errors'])
        self.assertEqual(T.sha(wbfile(R)), S['wb1'], 'identical workbook')
        self.assertEqual(T.sha(R.root / 'data' / 'site' / 'index.html'), T.sha(K.root / 'data' / 'site' / 'index.html'), 'identical page')
        self.assertEqual(T.sha(R.root / 'data' / 'site' / 'data' / 'sheet.json'), T.sha(K.root / 'data' / 'site' / 'data' / 'sheet.json'))
        self.assertEqual([T.sha(b) for b in (R.root / 'data' / 'backups').glob('*.xlsx')], [before_sha], 'backup first')
        newpages = [p for p in (K.root / 'data' / 'library' / '2026').glob('ws*o-s*.html')]
        for p in newpages:
            self.assertEqual(T.sha(R.root / 'data' / 'library' / '2026' / p.name), T.sha(p))
        self.assertEqual(ledger(R)[-1]['after_sha'], S['wb1'])
        self.assertEqual(json.loads((R.root / 'data' / 'db' / 'notes' / 'reader-note.json').read_text())['text'], 'mine')
        self.assertTrue((R.root / 'data' / 'db' / 'views' / 'v1.json').is_file())
        self.assertFalse((R.root / 'data' / 'db' / 'notes' / f'{S["note_sid"]}.json').exists(), "the keeper's notes are never carried")
        # the same refresh again, and the reader's own refusal to save
        st, j = R.upload(S['r1'], 'refresh')
        res = R.job('refresh_take', {'file': j['file']})
        self.assertFalse(res['ok']); self.assertEqual(res['refused'], 'OLDER'); self.assertIn('Nothing was changed', res['line'])
        self.assertEqual(T.sha(wbfile(R)), S['wb1'])

    def test_07_reader_cannot_save_or_accept(self):
        z = T.make_update_zip(R.root, BASE / 'for_reader.zip', 'rdr1')
        st, j = R.upload(z, 'update')
        self.assertEqual(st, 403)
        for verb, body in (('inspect', {'file': 'x.zip'}), ('save', {'update_id': 'x', 'token': 'abcdef12'}), ('init', {'sha': 'a' * 64}), ('refresh_make', {})):
            st, j = R.call('POST', '/_local/station/' + verb, body)
            self.assertEqual(st, 403, (verb, j))
            self.assertIn('reader copy', j['line'])
        st, j = K.call('POST', '/_local/station/refresh_take', {'file': 'x.zip'})
        self.assertEqual(st, 403)
        # even a hand-run job refuses
        p = subprocess.run([str(R.root / 'python' / 'bin' / 'python'), '-B', '-X', 'utf8', '-I', 'app/station/station_cli.py', 'init', '--root', str(R.root)],
                           cwd=R.root, capture_output=True, text=True)
        self.assertIn('reader copy', p.stdout)

    def test_08_second_update_incremental_refresh_and_concurrent_save_locked(self):
        z = T.make_update_zip(K.root, BASE / 'upd2.zip', 'second2')
        st, j = K.upload(z)
        self.assertEqual(st, 200)
        ins = K.job('inspect', {'file': j['file']})
        self.assertTrue(ins['ok'] and ins['stage'] == 'previewed', ins)
        # a second PC's tracker on the same folder (same data): two saves at the same moment
        K2 = T.Server(K.root).start()
        results = {}

        def go(name, srv):
            results[name] = srv.job('save', {'update_id': ins['update_id'], 'token': ins['token']})
        ts = [threading.Thread(target=go, args=('a', K)), threading.Thread(target=go, args=('b', K2))]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        K2.stop()
        written = [k for k, v in results.items() if v.get('written')]
        locked = [k for k, v in results.items() if not v.get('written')]
        self.assertEqual(len(written), 1, results)
        loser = results[locked[0]]
        self.assertTrue(loser.get('locked') or 'running' in json.dumps(loser) or 'no longer waiting' in json.dumps(loser), loser)
        if loser.get('locked'):
            self.assertIn('Another save is running', loser['lines'][0] if loser.get('lines') else loser.get('line', ''))
        S['wb2'] = T.sha(wbfile(K))
        self.assertNotEqual(S['wb2'], S['wb1'])
        self.assertEqual(len([e for e in ledger(K) if e['verb'] == 'save']), 2)

    def test_09_chain_older_gap_and_tampered_refresh(self):
        res = K.job('refresh_make', {})
        self.assertTrue(res['ok'], res)
        r2 = K.root / 'data' / 'refresh_out' / res['name']
        S['r2'] = BASE / r2.name
        shutil.copy2(r2, S['r2'])
        # incremental chain: reader at refresh 1 takes refresh 2
        st, j = R.upload(S['r2'], 'refresh')
        got = R.job('refresh_take', {'file': j['file']})
        self.assertTrue(got['ok'], got)
        self.assertEqual(T.sha(wbfile(R)), S['wb2'])
        self.assertEqual(T.sha(R.root / 'data' / 'site' / 'index.html'), T.sha(K.root / 'data' / 'site' / 'index.html'))
        # older refused
        st, j = R.upload(S['r1'], 'refresh')
        old = R.job('refresh_take', {'file': j['file']})
        self.assertEqual(old['refused'], 'OLDER')
        self.assertEqual(T.sha(wbfile(R)), S['wb2'])
        # a brand-new reader with refresh 2 (incremental, base = 1): gap, asks for a full one
        N = T.Server(T.make_work(BASE, 'newbie', 'reader')).start()
        try:
            st, j = N.upload(S['r2'], 'refresh')
            gap = N.job('refresh_take', {'file': j['file']})
            self.assertEqual(gap['refused'], 'GAP'); self.assertIn('full refresh', gap['line'])
            self.assertEqual(T.sha(wbfile(N)), S['wb0'])
            # tampered refresh: one byte of a library page changed after the manifest was made
            full = K.job('refresh_make', {'full': True})
            self.assertTrue(full['ok'], full)
            fz = K.root / 'data' / 'refresh_out' / full['name']
            with zipfile.ZipFile(fz) as z:
                ents = {i.filename: z.read(i) for i in z.infolist()}
            vic = next(n for n in ents if n.startswith('library/2026/'))
            ents[vic] = ents[vic] + b' '
            bad = BASE / 'tampered_refresh.zip'
            with zipfile.ZipFile(bad, 'w') as z:
                for n, b in ents.items():
                    z.writestr(n, b)
            st, j = N.upload(bad, 'refresh')
            tam = N.job('refresh_take', {'file': j['file']})
            self.assertEqual(tam['refused'], 'HASH_MISMATCH'); self.assertIn('Nothing was changed', tam['line'])
            self.assertEqual(T.sha(wbfile(N)), S['wb0'])
            self.assertEqual(list((N.root / 'data' / 'backups').glob('*')), [])
            # a refused name (a script smuggled in) is refused before anything is read
            evil = BASE / 'evil_refresh.zip'
            with zipfile.ZipFile(evil, 'w') as z:
                z.writestr('manifest.json', '{}')
                z.writestr('library/x.py', 'print(1)')
            st, j = N.upload(evil, 'refresh')
            ev = N.job('refresh_take', {'file': j['file']})
            self.assertEqual(ev['refused'], 'BAD_ENTRY')
            # and the FULL refresh does work for a new person
            st, j = N.upload(fz, 'refresh')
            ok = N.job('refresh_take', {'file': j['file']}, timeout=1800)
            self.assertTrue(ok['ok'], ok)
            self.assertEqual(T.sha(wbfile(N)), S['wb2'])
            self.assertEqual(sorted(p.name for p in (N.root / 'data' / 'library' / '2026').glob('ws*o-s*.html')),
                             sorted(p.name for p in (K.root / 'data' / 'library' / '2026').glob('ws*o-s*.html')))
        finally:
            N.stop()

    def test_10_status_banners_excel_open_and_lock(self):
        wb = wbfile(K)
        lockf = wb.with_name('~$' + wb.name)
        lockf.write_text('x')
        try:
            st, s = K.call('GET', '/_local/station/status')
            self.assertTrue(s['workbook']['excel_open'])
            res = K.job('init', {'sha': s['workbook']['sha256']})
            self.assertFalse(res['ok']); self.assertIn('Excel has the workbook open', res['line'])
            out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'panel', 'name': 'p'}], '10')
            self.assertIn('Excel has the workbook open', out['results']['p'])
        finally:
            lockf.unlink()
        (K.root / 'data' / 'state' / 'saver.lock').write_text(json.dumps({'host': 'OTHER-PC', 'at': time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime())}))
        try:
            out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'panel', 'name': 'p'}], '10b')
            self.assertIn('Another save is running (OTHER-PC', out['results']['p'])
        finally:
            (K.root / 'data' / 'state' / 'saver.lock').unlink()

    def test_11_accept_workbook_after_hand_edit(self):
        wb = wbfile(K)
        with open(wb, 'ab') as f:           # stands in for "someone changed it outside the tracker"
            f.write(b'\0')
        new = T.sha(wb)
        st, s = K.call('GET', '/_local/station/status')
        self.assertEqual(s['workbook']['baseline'], 'changed')
        out = T.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'click', 'text': 'Accept the workbook as it is now'},
                       {'op': 'wait_text', 'text': ['Are you sure?'], 'timeout': 20000}, {'op': 'screenshot', 'path': str(T.SHOTS / '11_confirm.png')},
                       {'op': 'click', 'text': 'Yes, accept it'}, {'op': 'wait_text', 'text': ['Done. The tracker now treats'], 'timeout': 120000, 'name': 'd'}], '11')
        self.assertNotIn('crash', out['results'], out['results'])
        self.assertEqual(ledger(K)[-1]['after_sha'], new)
        st, s = K.call('GET', '/_local/station/status')
        self.assertEqual(s['workbook']['baseline'], 'ok')


class Launcher(unittest.TestCase):
    def test_busy_port_and_already_running(self):
        base = BASE / 'launch'
        base.mkdir(parents=True, exist_ok=True)
        root = T.make_work(base, 'l1', 'reader')
        port = T.free_port()
        env = dict(os.environ, AJG_NO_BROWSER='1', AJG_TEST_PORT=str(port))
        cmd = [str(root / 'python' / 'bin' / 'python'), '-B', '-X', 'utf8', '-I', 'app/station/launcher.py']
        srv = T.Server(root, port).start()
        try:
            again = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(again.returncode, 0); self.assertIn('already running on this PC', again.stdout)
            other = T.make_work(base, 'l2', 'reader')
            diff = subprocess.run([str(other / 'python' / 'bin' / 'python'), '-B', '-X', 'utf8', '-I', 'app/station/launcher.py'], cwd=other, env=env,
                                  capture_output=True, text=True, timeout=60)
            self.assertEqual(diff.returncode, 3); self.assertIn('different folder', diff.stdout)
        finally:
            srv.stop()
        import socket
        port = T.free_port()
        env = dict(env, AJG_TEST_PORT=str(port))
        s = socket.socket()
        s.bind(('127.0.0.1', port))
        s.listen(1)
        try:
            busy = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(busy.returncode, 3); self.assertIn('used by another program', busy.stdout)
        finally:
            s.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
