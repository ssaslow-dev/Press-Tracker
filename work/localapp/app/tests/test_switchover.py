"""SWITCHOVER-v1 / DROPUNVERIFIED-v1: "Set up from the Mac library" and "Remove unverified reprints" (keeper copy, switch-over day).
    AJG_TEST_BUILD_EMPTY=<fresh linux build made with --data-mode empty> python3 -I -m unittest discover -s work/localapp/app/tests -p test_switchover.py -v
A fake Mac "Tracker library" folder is made from the scratch copy of the 0bccc1fc workbook ($SCRATCH/wb_0bccc1fc.xlsx, 419 unverified rows) and a small
library (a subset of the repository snapshot plus synthetic files for the rows that will be dropped), with a fingerprint list in `shasum -a 256` format.

  A. the empty tracker opens and says plainly "No workbook yet: use Set up from the Mac library" (page, status, the panel in Chromium)
  B. setup refused, with nothing written anywhere, for: a missing file, a changed file, a 0-byte placeholder, a list with no workbook line, a wrong folder;
     the source folder is never changed; a reader copy cannot run it
  C. setup: every file copied and checked, extras and OS junk ignored, Backups / Work archive not copied, ledger seeded, page built, summary; a second setup is refused
  D. a first refresh file carries it all to a reader copy
  E. Remove unverified reprints: preview (counts, rows, files), refused when Excel is open / the token is wrong / the workbook changed; apply: backup, only those
     rows gone on Coverage and Audio & video (every other cell and hyperlink the same, by Article ID), Originals and Removed untouched, ledger, saved files deleted
     only when no other row names them, log; the next ids stay above the deleted ones (unit check, build_data, a real update save); a refresh file carries the
     deletions to the reader; a reader cannot run it
  F. the panel in Chromium: setup form, check, copy and set up, then the removal preview
"""
import hashlib
import json
import os
import re
import shutil
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402

REPO = T.REPO
SCR = T.SCRATCH
EMPTY = Path(os.environ.get('AJG_TEST_BUILD_EMPTY') or SCR / 'app_build_empty' / 'linux' / 'AJG Tracker')
WB0 = SCR / 'wb_0bccc1fc.xlsx'
BASE = SCR / 'app_build' / 'test_switchover'
WB_NAME = 'AJG Coverage - NewsBank.xlsx'
S = {}
K = R = None


def make_empty_work(name, role):
    root = BASE / name / 'AJG Tracker'
    shutil.copytree(EMPTY, root, symlinks=True, copy_function=os.link)
    d = root / 'data'
    (d / 'role.json').unlink()
    (d / 'role.json').write_text(json.dumps({'role': role}))
    for sub in ('tmp', 'db', 'backups', 'for_update', 'refresh_out', 'state', 'workbook', 'library', 'updates/incoming', 'updates/staging', 'updates/work',
                'updates/done', 'updates/rejected', 'updates/refresh_incoming'):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return root


def sha(p):
    return T.sha(p)


def tree_hash(folder: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(Path(folder).rglob('*')):
        h.update(p.relative_to(folder).as_posix().encode())
        if p.is_file():
            h.update(str(p.stat().st_size).encode() + sha(p).encode())
    return h.hexdigest()


def ledger(root):
    root = getattr(root, 'root', root)
    f = root / 'data' / 'state' / 'ledger.jsonl'
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.is_file() else []


def read_tabs(wb):
    """{tab: {Article ID (or key): [row dict, ...]}} plus hyperlink targets per row, read only (the save program's own reader)"""
    sys.path.insert(0, str(REPO / 'work' / 'saver' / 'src'))
    import saver_diff as D
    b = D.read_book(wb)
    out = {}
    for name, sh in b.sheets.items():
        hi = {str(h): i for i, h in enumerate(sh.header) if h}
        key = hi.get('Article ID', hi.get('Release ID', hi.get('Bill', 0)))
        d = {}
        for rn, vals in sh.rows:
            k = str(vals[key]) if key < len(vals) else ''
            d.setdefault(k, []).append({'vals': tuple(vals), 'links': dict(sh.links.get(rn, {}))})
        out[name] = {'header': sh.header, 'rows': d, 'n': len(sh.rows)}
    return out


def unverified_in(wb):
    import openpyxl
    w = openpyxl.load_workbook(wb, read_only=True)
    it = w['Coverage'].iter_rows(values_only=True)
    h = list(next(it))
    ix = {k: i for i, k in enumerate(h)}
    out = [r for r in it if str(r[ix['Original or reprint']] or '').strip() == 'Reprint (unverified)']
    w.close()
    return h, out


def build_mac(base: Path):
    """the fake Mac folder; returns (folder, list path, info)"""
    import openpyxl
    mac = base / 'Tracker library'
    shutil.rmtree(base, ignore_errors=True)
    mac.mkdir(parents=True)
    # the workbook: two changes for the tests. (1) the verified Reprint with the highest Article ID becomes "Reprint (unverified)" so the dropped ids reach
    # above everything else; (2) a remaining row names a dropped row's file, which must therefore be kept
    wb = openpyxl.load_workbook(WB0)
    ws = wb['Coverage']
    h = {c.value: i + 1 for i, c in enumerate(ws[1]) if c.value}
    best = None
    for r in range(2, ws.max_row + 1):
        if str(ws.cell(r, h['Original or reprint']).value or '').strip() == 'Reprint':
            a = str(ws.cell(r, h['Article ID']).value or '')
            if re.fullmatch(r'\d{5}', a) and (best is None or a > best[0]):
                best = (a, r)
    ws.cell(best[1], h['Original or reprint']).value = 'Reprint (unverified)'
    top_aid = best[0]
    keep_name = 'ws01111r-s00297.html'
    holder = None
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, h['Original or reprint']).value == 'Original' and not ws.cell(r, h['File name 2']).value and ws.cell(r, h['Saved Copy?']).value == 'Yes':
            ws.cell(r, h['File name 2']).value = keep_name
            holder = str(ws.cell(r, h['Article ID']).value)
            break
    wb.save(mac / WB_NAME)
    wb.close()
    hdr, unv = unverified_in(mac / WB_NAME)
    ix = {k: i for i, k in enumerate(hdr)}
    files = {}

    def put(rel, data=None, src=None):
        p = mac / Path(*rel.split('/'))
        p.parent.mkdir(parents=True, exist_ok=True)
        if src:
            shutil.copy2(src, p)
        else:
            p.write_bytes(data)
        files[rel] = p
    # real files from the repository snapshot (a small subset)
    lib = REPO / 'data' / 'library'
    for sub, n in (('2026', 25), ('_original_html/2026', 10), ('_original_pdf/2026', 5), ('Press releases/2026', 4), ('_original_html/Press releases/2026', 3)):
        d = lib / sub
        for f in sorted(d.iterdir())[:n] if d.is_dir() else []:
            if f.is_file():
                put(f'{sub}/{f.name}', src=f)
    # synthetic files for the dropped rows
    expect_delete, expect_keep = set(), set()
    for r in unv:
        aid = str(r[ix['Article ID']])
        for c in ('File name', 'File name 2'):
            nm = r[ix[c]]
            if nm and re.search(r'\.[a-z]{3,4}$', str(nm)):
                yr = str(r[ix['Date']] or '')[:4]
                yr = yr if re.fullmatch(r'20\d\d', yr) else '2020'
                for rel in (f'{yr}/{nm}', f'_original_html/{yr}/{nm}'):
                    put(rel, data=b'<html>' + rel.encode() + b'</html>')
                    (expect_keep if nm == keep_name else expect_delete).add(rel)
    # one named by the Article ID only, a print jump page, and look-alikes that must stay
    put('2024/nb08340o-s02992.pdf', data=b'%PDF synthetic')
    put('2024/nb08340o-s02992.pdf.ocr.txt', data=b'ocr text')
    put('_original_pdf/2024/08340_p3.pdf', data=b'%PDF page')
    expect_delete |= {'2024/nb08340o-s02992.pdf', '2024/nb08340o-s02992.pdf.ocr.txt', '_original_pdf/2024/08340_p3.pdf'}
    for rel in ('2024/ws083401r-s00001.html', '2024/ws0834.html', '2024/ws08340x-s00001.html'):
        put(rel, data=b'lookalike ' + rel.encode())
    # a file the list will not name, and things that are never reported or copied
    extra = {'2026/extra_not_on_the_list.html'}
    put('2026/extra_not_on_the_list.html', data=b'extra')
    (mac / 'Backups').mkdir()
    (mac / 'Backups' / 'old backup.xlsx').write_bytes(b'backup')
    (mac / 'Work archive').mkdir()
    (mac / 'Work archive' / 'scratch.txt').write_bytes(b'work')
    for junk in ('.DS_Store', '2026/.DS_Store', '2026/._junk.html', '2026/Thumbs.db', '2026/desktop.ini'):
        (mac / junk).write_bytes(b'junk')
    # the list (shasum -a 256 format, the workbook included, no Backups / Work archive, not the extra file)
    lines = [f'{sha(mac / WB_NAME)}  {WB_NAME}'] + [f'{sha(p)}  {rel}' for rel, p in sorted(files.items()) if rel not in extra]
    lst = base / 'Tracker library manifest.sha256'
    lst.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return mac, lst, {'top_aid': top_aid, 'keep_holder': holder, 'keep_name': keep_name, 'expect_delete': expect_delete, 'expect_keep': expect_keep,
                      'listed': len(lines), 'extra': extra, 'n_unverified': len(unv)}


def setUpModule():
    global K, R
    if not EMPTY.is_dir():
        raise unittest.SkipTest('no empty test build: python3 -I assemble_app.py --target linux --role keeper --data-mode empty --out <dir>')
    if not WB0.is_file():
        raise unittest.SkipTest('no scratch copy of the 0bccc1fc workbook')
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    S['mac'], S['list'], S['info'] = build_mac(BASE / 'macsrc')
    K = T.Server(make_empty_work('keeper', 'keeper')).start()
    R = T.Server(make_empty_work('reader', 'reader')).start()


def tearDownModule():
    for s in (K, R):
        if s:
            s.stop()


def data(s):
    return s.root / 'data'


def nothing_written(s):
    d = data(s)
    return (not any((d / 'workbook').glob('*')) and not any(p.is_file() for p in (d / 'library').rglob('*')) and not (d / 'state' / 'ledger.jsonl').exists()
            and not list((d / 'tmp').glob('setup_*')))


def folder_copy(name, mutate=None):
    dst = BASE / 'cases' / name
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(S['mac'], dst)
    if mutate:
        mutate(dst)
    return dst


class Switchover(unittest.TestCase):
    maxDiff = None

    # ---------------------------------------------------------------- A, B, C, D
    def test_01_empty_tracker_says_plainly_what_to_do(self):
        page = K.get('/').decode('utf-8', 'replace')
        self.assertIn('No workbook yet: use Set up from the Mac library', page)
        self.assertIn('/_local/station.js', page)
        st, s = K.call('GET', '/_local/station/status')
        self.assertFalse(s['workbook']['exists'])
        self.assertEqual(s['role'], 'keeper')
        self.assertFalse(s['setup_done'])
        # the reader copy says what is right for a reader
        out = T.ui(R, [{'op': 'goto'}, {'op': 'wait', 'ms': 1500}, {'op': 'eval', 'name': 'msg', 'expr': "document.querySelector('#ajg-nowb-msg').textContent"},
                       {'op': 'panel', 'name': 'p'}], 'so_reader_empty')
        self.assertIn('bring in the refresh file the keeper gave you', out['results']['msg'])
        self.assertNotIn('Set up from the Mac library', out['results']['p'].split('Bring in refresh file')[0].replace('No workbook yet', ''), out['results']['p'])
        # the keeper copy, in the real page
        out = T.ui(K, [{'op': 'goto'}, {'op': 'wait', 'ms': 1500}, {'op': 'eval', 'name': 'msg', 'expr': "document.querySelector('#ajg-nowb-msg').textContent"},
                       {'op': 'panel', 'name': 'p'}, {'op': 'screenshot', 'path': str(T.SHOTS / 'switchover_01_empty.png')}], 'so_empty')
        self.assertIn('No workbook yet: use Set up from the Mac library', out['results']['msg'])
        self.assertIn('Set up from the Mac library', out['results']['p'])
        self.assertIn('Check the files', out['results']['p'])
        self.assertEqual(out['errors'], [], out['errors'])

    def refused(self, srv, mac, lst, verb='setup_run', **kw):
        body = {'folder': str(mac), 'list': str(lst)}
        body.update(kw)
        res = srv.job(verb, body)
        self.assertFalse(res.get('ok'), res)
        return res

    def test_02_setup_refused_with_nothing_written(self):
        before = tree_hash(S['mac'])
        # (a) a missing file
        victim = sorted(p for p in (S['mac'] / '2026').iterdir() if p.is_file() and not p.name.startswith(('.', '_', 'extra', 'Thumbs', 'desktop')))[0].name

        def drop(d):
            (d / '2026' / victim).unlink()
        m = folder_copy('missing', drop)
        for verb in ('setup_check', 'setup_run'):
            r = self.refused(K, m, S['list'], verb)
            txt = ' '.join([r['line']] + r.get('lines', []) + (r.get('check', {}).get('lines', []) if isinstance(r.get('check'), dict) else []))
            self.assertIn('MISSING', txt, r)
            self.assertIn(victim, txt, r)
        self.assertTrue(nothing_written(K))
        # (b) a changed file
        victim2 = sorted(p for p in (S['mac'] / '_original_html' / '2026').iterdir() if p.is_file())[0].name

        def change(d):
            with open(d / '_original_html' / '2026' / victim2, 'ab') as f:
                f.write(b' ')
        m = folder_copy('changed', change)
        r = self.refused(K, m, S['list'])
        self.assertIn('DIFFERENT', r['line'] + ' '.join((r.get('check') or {}).get('lines', [])), r)
        self.assertIn(victim2, json.dumps(r))
        self.assertTrue(nothing_written(K))
        # (c) a 0-byte placeholder (a cloud file that was not downloaded)
        victim3 = sorted(p for p in (S['mac'] / '2026').iterdir() if p.is_file() and p.suffix in ('.html', '.pdf') and p.name != victim and not p.name.startswith(('.', '_', 'extra')))[1].name

        def empty(d):
            (d / '2026' / victim3).write_bytes(b'')
        m = folder_copy('placeholder', empty)
        r = self.refused(K, m, S['list'])
        self.assertIn('empty or only online', json.dumps(r), r)
        self.assertIn('downloaded', json.dumps(r))
        self.assertIn(victim3, json.dumps(r))
        self.assertTrue(nothing_written(K))
        # (d) a list with no line for the workbook
        nolist = BASE / 'cases' / 'no_wb_line.sha256'
        nolist.write_text(''.join(l + '\n' for l in S['list'].read_text().splitlines() if not l.endswith(WB_NAME)))
        r = self.refused(K, S['mac'], nolist)
        self.assertIn('no line for the workbook', r['line'])
        # (e) a wrong folder, and a missing list
        r = self.refused(K, BASE / 'no such folder', S['list'])
        self.assertIn('is not at', r['line'])
        r = self.refused(K, S['mac'], BASE / 'no such list.sha256')
        self.assertIn('fingerprint list is not at', r['line'])
        self.assertTrue(nothing_written(K))
        # (f) a listed file of a type a refresh file cannot carry would break every later refresh: refused now
        m = folder_copy('oddtype', lambda d: (d / '2024' / 'odd_file.bak').write_bytes(b'odd'))
        oddlist = BASE / 'cases' / 'odd.sha256'
        oddlist.write_text(S['list'].read_text() + f"{sha(m / '2024' / 'odd_file.bak')}  2024/odd_file.bak\n")
        r = self.refused(K, m, oddlist)
        self.assertIn('cannot pass on in refresh files', json.dumps(r))
        self.assertIn('odd_file.bak', json.dumps(r))
        self.assertTrue(nothing_written(K))
        self.assertEqual(tree_hash(S['mac']), before, 'the Mac folder is never changed')

    def test_03_a_reader_copy_cannot_run_it(self):
        st, j = R.call('POST', '/_local/station/setup_run', {'folder': str(S['mac']), 'list': str(S['list'])})
        self.assertEqual(st, 403, j)
        self.assertIn('reader copy', j['line'])
        st, j = R.call('POST', '/_local/station/drop_apply', {'token': '0' * 16})
        self.assertEqual(st, 403, j)
        st, j = R.call('POST', '/_local/station/upload?kind=manifest&name=x.sha256', raw=b'x')
        self.assertEqual(st, 403, j)
        # and the job itself refuses (the server check is not the only one)
        import subprocess
        p = subprocess.run([str(R.root / 'python' / 'bin' / 'python'), '-B', '-X', 'utf8', '-I', 'app/station/station_cli.py', 'setup_run', '--root', str(R.root),
                            '--folder=' + str(S['mac']), '--list=' + str(S['list'])], cwd=R.root, capture_output=True, text=True)
        res = json.loads(p.stdout.strip().splitlines()[-1])
        self.assertFalse(res['ok'])
        self.assertIn('reader copy', res['line'])
        self.assertTrue(nothing_written(R))

    def test_04_setup_copies_checks_and_builds_the_page(self):
        info, mac = S['info'], S['mac']
        before = tree_hash(mac)
        # the list may also be sent from the panel as a file (upload) and the list may sit inside the folder: use the upload here
        st, up = K.call('POST', '/_local/station/upload?kind=manifest&name=Tracker%20library%20manifest.sha256', raw=S['list'].read_bytes())
        self.assertEqual(st, 200, up)
        chk = K.job('setup_check', {'folder': str(mac), 'list_upload': up['file']})
        self.assertTrue(chk['ok'], chk)
        self.assertEqual(chk['check']['listed'], info['listed'])
        self.assertEqual(chk['check']['missing'] + chk['check']['different'] + chk['check']['placeholders'], 0)
        self.assertEqual(chk['check']['extra'], 1, 'the one real file the list does not name; junk, Backups and Work archive are not reported')
        self.assertEqual(chk['check']['extra_names'], sorted(info['extra']))
        self.assertTrue(nothing_written(K), 'a check writes nothing')
        res = K.job('setup_run', {'folder': str(mac), 'list_upload': up['file']}, timeout=1500)
        self.assertTrue(res['ok'], res)
        S['setup'] = res
        d = data(K)
        wbp = d / 'workbook' / WB_NAME
        self.assertEqual(sha(wbp), sha(mac / WB_NAME))
        self.assertEqual(res['workbook_sha256'], sha(wbp))
        want = {l.split('  ', 1)[1]: l.split('  ', 1)[0] for l in S['list'].read_text().splitlines() if l.strip()}
        for rel, h in want.items():
            if rel == WB_NAME:
                continue
            self.assertEqual(sha(d / 'library' / Path(*rel.split('/'))), h, rel)
        have = {p.relative_to(d / 'library').as_posix() for p in (d / 'library').rglob('*') if p.is_file()}
        self.assertEqual(have, set(want) - {WB_NAME}, 'exactly the listed library files: no extra file, no Backups, no Work archive, no junk')
        self.assertEqual(res['files_copied'], len(want) - 1)
        self.assertEqual(tree_hash(mac), before, 'copied, never moved or changed')
        led = ledger(K)
        self.assertEqual([e['verb'] for e in led], ['init'])
        self.assertEqual(led[0]['after_sha'], sha(wbp))
        self.assertIn('set up from the Mac library', led[0]['note'])
        # the page is built from the workbook: stories show, no placeholder
        page = K.get('/').decode('utf-8', 'replace')
        self.assertNotIn('ajg-nowb', page)
        self.assertGreater(len(page), 1_000_000)
        sj = json.loads((d / 'site' / 'data' / 'sheet.json').read_text())
        import base64
        self.assertEqual(hashlib.sha256(base64.b64decode(sj['b64'])).hexdigest(), sha(wbp))
        self.assertGreater(res['summary']['stories'], 4000)
        self.assertIn('stories in the tracker', ' '.join(res['lines']))
        self.assertTrue(list((d / 'state' / 'logs').glob('setup-*.json')))
        st, s = K.call('GET', '/_local/station/status')
        self.assertEqual(s['workbook']['baseline'], 'ok')
        self.assertTrue(s['setup_done'] and not s['drop_done'])
        self.assertFalse(list((d / 'tmp').glob('setup_*')), 'the staging folder is gone')
        # a second setup is refused, nothing changes
        again = K.job('setup_run', {'folder': str(mac), 'list_upload': up['file']})
        self.assertFalse(again['ok'], again)
        self.assertIn('already has a workbook', again['line'])
        self.assertEqual(sha(wbp), res['workbook_sha256'])

    def test_05_first_refresh_file_reaches_a_reader(self):
        r = K.job('refresh_make', {'full': False}, timeout=1500)
        self.assertTrue(r['ok'], r)
        self.assertEqual(r['kind'], 'full')
        S['refresh1'] = Path(r['path'])
        S['k_wb_pre'] = r['workbook_sha256']
        st, up = R.upload(S['refresh1'], 'refresh')
        self.assertEqual(st, 200, up)
        res = R.job('refresh_take', {'file': up['file']}, timeout=1500)
        self.assertTrue(res['ok'], res)
        self.assertEqual(sha(data(R) / 'workbook' / WB_NAME), S['k_wb_pre'])
        n = sum(1 for p in (data(R) / 'library').rglob('*') if p.is_file())
        self.assertEqual(n, S['setup']['files_copied'])
        for rel in S['info']['expect_delete']:
            self.assertTrue((data(R) / 'library' / Path(*rel.split('/'))).is_file(), rel)

    # ---------------------------------------------------------------- E
    def test_06_preview_lists_every_row_and_file(self):
        info = S['info']
        p = K.job('drop_preview', timeout=900)
        self.assertTrue(p['ok'] and p['can_drop'], p)
        S['preview'] = p
        hdr, unv = unverified_in(data(K) / 'workbook' / WB_NAME)
        ix = {k: i for i, k in enumerate(hdr)}
        self.assertEqual(len(p['rows']), len(unv))
        self.assertEqual(len(unv), 420, 'the 419 of 0bccc1fc plus the one this test relabelled')
        self.assertEqual({r['aid'] for r in p['rows']}, {str(r[ix['Article ID']]) for r in unv})
        for r in p['rows']:
            self.assertTrue(r['aid'] and 'outlet' in r and 'headline' in r and 'sid' in r)
        self.assertEqual(p['article_floor'], int(info['top_aid']), 'the relabelled row holds the highest Article ID of all')
        tabs = read_tabs(data(K) / 'workbook' / WB_NAME)
        av = [a for a in tabs['Audio & video details']['rows'] if a in {r['aid'] for r in p['rows']}]
        self.assertEqual(len(p['av_rows']), sum(len(tabs['Audio & video details']['rows'][a]) for a in av))
        self.assertEqual({f['path'] for f in p['files'] if f['action'] == 'delete'}, info['expect_delete'])
        self.assertEqual({f['path'] for f in p['files'] if f['action'] == 'keep'}, info['expect_keep'])
        self.assertTrue(all('still named by Coverage row' in f['why'] for f in p['files'] if f['action'] == 'keep'), p['files'])
        self.assertTrue(Path(data(K) / 'state' / 'drop_unverified').is_dir())
        self.assertIn('unverified reprints would be removed', p['headline'])

    def test_07_refused_applies_change_nothing(self):
        wb = data(K) / 'workbook' / WB_NAME
        s0, l0 = sha(wb), len(ledger(K))
        tok = S['preview']['token']
        lib0 = tree_hash(data(K) / 'library')

        def untouched():
            self.assertEqual(sha(wb), s0)
            self.assertEqual(len(ledger(K)), l0)
            self.assertEqual(list((data(K) / 'backups').glob('*')), [])
            self.assertEqual(tree_hash(data(K) / 'library'), lib0)
            self.assertFalse((data(K) / 'state' / 'reserved_ids.json').exists())
        lockf = wb.with_name('~$' + wb.name)
        lockf.write_text('x')
        try:
            r = K.job('drop_apply', {'token': tok})
        finally:
            lockf.unlink()
        self.assertFalse(r['ok'] or r.get('written'), r)
        self.assertIn('Excel has the workbook open', r['line'])
        untouched()
        r = K.job('drop_apply', {'token': '0' * 16})
        self.assertFalse(r['ok'] or r.get('written'), r)
        self.assertIn('changed since you looked', r['line'])
        untouched()
        # the workbook changed after the preview
        orig = wb.read_bytes()
        with open(wb, 'ab') as f:
            f.write(b'\0')
        try:
            r = K.job('drop_apply', {'token': tok})
        finally:
            wb.write_bytes(orig)
        self.assertFalse(r['ok'] or r.get('written'), r)
        self.assertIn('not the one the tracker last saved', r['line'])
        untouched()
        # a reader cannot run it
        st, j = R.call('POST', '/_local/station/drop_preview', {})
        self.assertEqual(st, 403, j)

    def test_08_apply_removes_exactly_those_rows(self):
        wb = data(K) / 'workbook' / WB_NAME
        before_book = BASE / 'before_drop.xlsx'
        shutil.copy2(wb, before_book)
        before = read_tabs(before_book)
        p = S['preview']
        res = K.job('drop_apply', {'token': p['token']}, timeout=1800)
        self.assertTrue(res['ok'] and res['written'], res)
        S['drop'] = res
        after = read_tabs(wb)
        dropped = {r['aid'] for r in p['rows']}
        # the backup is the workbook as it was
        bk = data(K) / 'backups' / res['backup']
        self.assertEqual(sha(bk), sha(before_book))
        self.assertEqual(res['before_sha'], sha(before_book))
        self.assertEqual(res['workbook_sha256'], sha(wb))
        # Coverage and Audio & video: exactly those Article IDs are gone; everything else is the same, cell by cell and link by link, found by Article ID
        for tab in before:
            b, a = before[tab], after[tab]
            self.assertEqual(a['header'], b['header'], tab)
            if tab in ('Coverage', 'Audio & video details'):
                self.assertEqual(set(b['rows']) - set(a['rows']), dropped & set(b['rows']), tab)
                self.assertEqual(set(a['rows']) - set(b['rows']), set(), tab)
                for k in a['rows']:
                    self.assertEqual(a['rows'][k], b['rows'][k], f'{tab} {k}: values and hyperlinks unchanged')
                self.assertEqual(a['n'], b['n'] - sum(len(b['rows'][k]) for k in dropped if k in b['rows']), tab)
            else:
                self.assertEqual(a['rows'], b['rows'], f'{tab} is untouched')
                self.assertEqual(a['n'], b['n'])
        nlinks = sum(len(r['links']) for rows in before['Coverage']['rows'].values() for r in rows)
        self.assertGreater(nlinks, 10, 'the workbook has real hyperlinks on Coverage')
        self.assertEqual(sum(len(r['links']) for rows in after['Coverage']['rows'].values() for r in rows),
                         nlinks - sum(len(r['links']) for k in dropped for r in before['Coverage']['rows'].get(k, [])))
        self.assertTrue(dropped.isdisjoint(set(after['Removed']['rows'])), 'not moved to the Removed tab')
        # the workbook still opens in the ordinary way and the hidden/visible state of the tabs is as before
        import openpyxl
        w = openpyxl.load_workbook(wb, read_only=True)
        w0 = openpyxl.load_workbook(before_book, read_only=True)
        self.assertEqual([(s.title, s.sheet_state) for s in w.worksheets], [(s.title, s.sheet_state) for s in w0.worksheets])
        w.close()
        w0.close()
        # ledger: the step's entry, then the usual init, so the new workbook is the baseline
        led = ledger(K)
        e = [x for x in led if x['verb'] == 'drop_unverified']
        self.assertEqual(len(e), 1, led)
        self.assertEqual((e[0]['before_sha'], e[0]['after_sha'], e[0]['backup']), (res['before_sha'], res['workbook_sha256'], res['backup']))
        self.assertEqual(set(e[0]['article_ids']), dropped)
        self.assertEqual(led[-1]['verb'], 'init')
        self.assertEqual(led[-1]['after_sha'], sha(wb))
        # files: exactly the planned deletions; a file another row names, and the look-alikes, stay
        info = S['info']
        lib = data(K) / 'library'
        for rel in info['expect_delete']:
            self.assertFalse((lib / Path(*rel.split('/'))).exists(), rel)
        for rel in info['expect_keep']:
            self.assertTrue((lib / Path(*rel.split('/'))).is_file(), rel)
        for rel in ('2024/ws083401r-s00001.html', '2024/ws0834.html', '2024/ws08340x-s00001.html'):
            self.assertTrue((lib / Path(*rel.split('/'))).is_file(), rel)
        self.assertEqual(set(res['files_deleted']), info['expect_delete'])
        log = json.loads((data(K) / 'state' / 'logs' / res['log']).read_text())
        self.assertEqual(log['status'], 'done')
        self.assertEqual({f['path'] for f in log['files'] if f['deleted']}, info['expect_delete'])
        self.assertTrue(all(len(f['sha256']) == 64 for f in log['files']))
        self.assertEqual(len(log['rows']), len(dropped))
        # the page was rebuilt from the new workbook
        sj = json.loads((data(K) / 'site' / 'data' / 'sheet.json').read_text())
        import base64
        self.assertEqual(hashlib.sha256(base64.b64decode(sj['b64'])).hexdigest(), sha(wb))
        st, s = K.call('GET', '/_local/station/status')
        self.assertEqual(s['workbook']['baseline'], 'ok')
        self.assertTrue(s['drop_done'])
        # a second preview finds nothing to do
        p2 = K.job('drop_preview', timeout=900)
        self.assertFalse(p2['can_drop'], p2)
        self.assertEqual(p2['rows'], [])

    def test_09_deleted_ids_stay_reserved(self):
        res = S['drop']
        info = S['info']
        rp = data(K) / 'state' / 'reserved_ids.json'
        doc = json.loads(rp.read_text())
        self.assertEqual(doc['article_floor'], int(info['top_aid']))
        self.assertEqual(set(doc['article_ids']), {r['aid'] for r in S['preview']['rows']})
        wb = data(K) / 'workbook' / WB_NAME
        py = str(K.root / 'python' / 'bin' / 'python')
        import subprocess
        code = ("import sys, os, json\n"
                "sys.path.insert(0, %r)\n"
                "import sheet_task as ST\n"
                "s = ST.Sheet(%r)\n"
                "print(json.dumps({'max_num': s.max_num, 'max_s': s.max_s}))\n") % (str(K.root / 'app' / 'pipeline'), str(wb))
        run = lambda env: json.loads(subprocess.run([py, '-B', '-I', '-c', code], capture_output=True, text=True, env=env, cwd=K.root).stdout.strip().splitlines()[-1])
        env0 = {k: v for k, v in os.environ.items() if k != 'AJG_RESERVED_IDS'}
        without = run(env0)
        withres = run(dict(env0, AJG_RESERVED_IDS=str(rp)))
        self.assertLess(without['max_num'], int(info['top_aid']), 'without the reservation the next id would be reused')
        self.assertEqual(withres['max_num'], int(info['top_aid']), 'with it, the next Article ID is the floor + 1')
        self.assertGreaterEqual(withres['max_s'], doc['story_floor'])
        # build_data (the "next free numbers" the Update station names its files with)
        out = BASE / 'bd_out'
        shutil.rmtree(out, ignore_errors=True)
        pipe = K.root / 'app' / 'pipeline'
        for env, key in ((env0, 'without'), (dict(env0, AJG_RESERVED_IDS=str(rp)), 'with')):
            o = out / key
            o.mkdir(parents=True)
            p = subprocess.run([py, '-B', '-X', 'utf8', '-I', str(pipe / 'build_data.py'), str(wb), str(pipe / 'legacy_index.html'), str(o) + '/', str(pipe / 'sid_map.json')],
                               capture_output=True, text=True, env=env, cwd=pipe)
            self.assertEqual(p.returncode, 0, p.stderr[-500:])
            nxt = json.loads((o / 'rows.json').read_text())['next']
            S['next_' + key] = nxt
        self.assertLess(S['next_without']['aid'], int(info['top_aid']) + 1)
        self.assertEqual(S['next_with']['aid'], int(info['top_aid']) + 1)

    def test_10_refresh_carries_the_deletions_to_the_reader(self):
        info = S['info']
        r = K.job('refresh_make', {'full': False}, timeout=1500)
        self.assertTrue(r['ok'], r)
        self.assertEqual(r['kind'], 'incremental', r)
        self.assertEqual(r['library_deleted'], len(info['expect_delete']))
        import zipfile
        with zipfile.ZipFile(r['path']) as z:
            man = json.loads(z.read('manifest.json'))
        self.assertEqual(man['format_version'], 2)
        self.assertEqual(set(man['deleted']), {'library/' + x for x in info['expect_delete']})
        S['refresh2'] = Path(r['path'])
        # the reader's copy of one deleted file was changed by hand: it is kept and said so
        odd = sorted(info['expect_delete'])[0]
        oddp = data(R) / 'library' / Path(*odd.split('/'))
        oddp.write_bytes(b'someone edited this copy')
        st, up = R.upload(S['refresh2'], 'refresh')
        self.assertEqual(st, 200, up)
        res = R.job('refresh_take', {'file': up['file']}, timeout=1500)
        self.assertTrue(res['ok'], res)
        self.assertEqual(sha(data(R) / 'workbook' / WB_NAME), sha(data(K) / 'workbook' / WB_NAME))
        for rel in info['expect_delete']:
            self.assertEqual((data(R) / 'library' / Path(*rel.split('/'))).exists(), rel == odd, rel)
        self.assertEqual(res['library_deleted'], len(info['expect_delete']) - 1)
        self.assertEqual(res['library_delete_kept'], [odd])
        self.assertIn('library files removed', ' '.join(res['lines']))
        for rel in info['expect_keep']:
            self.assertTrue((data(R) / 'library' / Path(*rel.split('/'))).is_file(), rel)
        self.assertTrue(list((data(R) / 'state' / 'logs').glob('refresh-deleted-*.json')))
        # a manifest that tries to delete outside the library, or a bad fingerprint, is refused before anything is written
        sys.path.insert(0, str(K.root / 'app' / 'station'))
        sys.path.insert(0, str(K.root / 'app' / 'updatefolder'))
        sys.path.insert(0, str(K.root / 'app' / 'saver'))
        import importlib
        import refresh as RF
        importlib.reload(RF)
        for bad in ({'site/index.html': 'a' * 64}, {'library/x.html': 'nothex'}, {'../x.html': 'a' * 64}):
            zp = BASE / 'badman.zip'
            with zipfile.ZipFile(S['refresh2']) as zi, zipfile.ZipFile(zp, 'w') as zo:
                for it in zi.infolist():
                    b = zi.read(it.filename)
                    if it.filename == 'manifest.json':
                        m = json.loads(b)
                        m['deleted'] = bad
                        b = json.dumps(m).encode()
                    zo.writestr(it, b)
            with self.assertRaises(RF.RefreshRefused):
                RF.verify(zp)

    def test_11_a_later_update_save_never_reuses_a_deleted_id(self):
        info = S['info']
        wb = data(K) / 'workbook' / WB_NAME
        z = T.make_update_zip(K.root, BASE / 'upd1.zip', 'example1')
        st, up = K.upload(z)
        self.assertEqual(st, 200, up)
        res = K.job('inspect', {'file': up['file']}, timeout=1800)
        self.assertTrue(res['ok'], res)
        self.assertEqual(res['stage'], 'previewed', res)
        pre = {k: v for k, v in read_tabs(wb)['Coverage']['rows'].items()}
        sv = K.job('save', {'update_id': res['update_id'], 'token': res['token']}, timeout=2400)
        self.assertTrue(sv['written'], sv)
        post = read_tabs(wb)['Coverage']['rows']
        new_ids = sorted(set(post) - set(pre))
        self.assertTrue(new_ids, 'the update added rows')
        dropped = {r['aid'] for r in S['preview']['rows']}
        self.assertTrue(all(int(a) > int(info['top_aid']) for a in new_ids if a.isdigit()), (new_ids, info['top_aid']))
        self.assertTrue(dropped.isdisjoint(new_ids))
        self.assertTrue(set(new_ids) <= {'%05d' % (int(info['top_aid']) + i) for i in range(1, 40)}, new_ids)
        self.assertEqual(new_ids[0], '%05d' % (int(info['top_aid']) + 1), 'the first new Article ID is the floor + 1')

    # ---------------------------------------------------------------- F
    def test_12_the_panel_in_chromium(self):
        U = T.Server(make_empty_work('ui', 'keeper')).start()
        try:
            def setv(i, v):
                return {'op': 'eval', 'name': 'set' + i, 'expr': "(() => { const e = document.querySelector('#%s'); e.value = %s; e.dispatchEvent(new Event('input', {bubbles: true})); return 1; })()" % (i, json.dumps(v))}
            out = T.ui(U, [{'op': 'goto'}, {'op': 'wait', 'ms': 1500}, {'op': 'panel', 'name': 'p0'},
                           setv('ajgf-folder', str(S['mac'])), setv('ajgf-list', str(S['list'])),
                           {'op': 'click', 'text': 'Check the files'},
                           {'op': 'wait_text', 'name': 'checked', 'text': ['Everything checks out'], 'timeout': 300000},
                           {'op': 'screenshot', 'path': str(T.SHOTS / 'switchover_f1_checked.png')},
                           {'op': 'click', 'text': 'Copy and set up'},
                           {'op': 'wait_text', 'name': 'done', 'text': ['The tracker is set up.'], 'timeout': 900000},
                           {'op': 'click', 'text': 'Look at the changes'},
                           {'op': 'wait_text', 'name': 'prev', 'text': ['Coverage rows are "Reprint (unverified)"'], 'timeout': 900000},
                           {'op': 'eval', 'name': 'applyDisabled', 'expr': "document.querySelector('#ajgf-sw-all').disabled"},
                           {'op': 'click_sel', 'sel': '#ajgf-sw-ok'},
                           {'op': 'eval', 'name': 'applyEnabled', 'expr': "document.querySelector('#ajgf-sw-all').disabled"},
                           {'op': 'screenshot', 'path': str(T.SHOTS / 'switchover_f2_preview.png')}], 'so_ui', timeout=3000)
            r = out['results']
            self.assertNotIn('crash', r, r)
            self.assertIn('Set up from the Mac library', r['p0'])
            self.assertIn('No workbook yet', r['p0'])
            self.assertIn('Reload the tracker', r['done_panel'])
            self.assertIn('stories in the tracker', r['done_panel'])
            self.assertIn('Switch-over changes', r['done_panel'])
            self.assertIn('420 Coverage rows are "Reprint (unverified)"', r['prev_panel'])
            self.assertNotIn('Set up again from the Mac library', r['p0'])
            self.assertTrue(r['applyDisabled'])
            self.assertFalse(r['applyEnabled'], 'ticking the box enables Confirm all')
            self.assertEqual(sha(data(U) / 'workbook' / WB_NAME), sha(S['mac'] / WB_NAME), 'previewing changes nothing')
            self.assertEqual(out['errors'], [], out['errors'])
        finally:
            U.stop()


if __name__ == '__main__':
    unittest.main()
