"""Consolidation step 2 (LASTUPDATED-v1, VIEWORIG-v1 option B / PRINTORIG-v1, CHAINCHECK-v1 follow-up a), in the real page and server of a fresh Linux build.
    AJG_TEST_BUILD=<fresh linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_step2.py -v

  1  Pacific dates by hand (summer and winter time, the changeover hour)
  2  LASTUPDATED: a keeper copy shows "Last updated <date>" under the masthead subtitle, same style (class, font, size, colour as the subtitle's own lines); a copy with
     no saving ledger entry shows nothing; the refresh file carries the date and a reader copy that takes it in shows the same line
  3  VIEWORIG: a print original named <Article ID>_p16-21.pdf in the library: the page rebuild lists it, the story sheet shows "View original" (pages 16-21), the file is
     served as a PDF; other names, other folders and a path trick are not served; a story with no such file has no button; a NewsBank text PDF name never makes one
  4  a refresh job that stops moving is reported to the page ('stalled'), then stopped; its half-written file and lock are put away; nothing is left running
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
sys.path.insert(0, str(HERE.parent / 'src' / 'station'))
import support as T  # noqa: E402
import test_pcedits as P  # noqa: E402
import common as C  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_step2'
K = R = None
S = {}


def setUpModule():
    global K, R
    if not T.BUILD.is_dir():
        raise unittest.SkipTest('no test build')
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    K = T.Server(T.make_work(BASE, 'keeper', 'keeper')).start()


def tearDownModule():
    for s in (K, R):
        if s:
            s.stop()


class Pacific(unittest.TestCase):
    def test_1_pacific_dates(self):
        f = C.pacific_date
        self.assertEqual(f('2026-07-01T06:59:00Z'), '2026-06-30')      # PDT = UTC-7
        self.assertEqual(f('2026-07-01T07:00:00Z'), '2026-07-01')
        self.assertEqual(f('2026-11-03T07:30:00+00:00'), '2026-11-02')     # PST = UTC-8
        self.assertEqual(f('2026-03-08T07:59:00Z'), '2026-03-07')      # 23:59 PST
        self.assertEqual(f('2026-03-08T09:59:00Z'), '2026-03-08')      # 01:59 PST, the last minute before the change
        self.assertEqual(f('2026-03-08T10:00:00Z'), '2026-03-08')      # 03:00 PDT
        self.assertEqual(f('2026-11-01T08:59:00Z'), '2026-11-01')      # 01:59 PDT
        self.assertEqual(f('2026-11-01T09:00:00Z'), '2026-11-01')      # 01:00 PST
        self.assertEqual(f('2026-11-01T07:59:00Z'), '2026-11-01')
        self.assertEqual(f('garbage'), '')


def mast(s, extra=''):
    return T.ui(s, [{'op': 'goto', 'wait': 3000}, {'op': 'wait', 'ms': 1500}, {'op': 'eval', 'name': 'm', 'expr':
        "(() => { const sl = document.getElementById('subline'), lu = document.getElementById('ajg-lastupd'); const cs = e => { const c = getComputedStyle(e); return [c.fontSize, c.fontFamily, c.color, c.textTransform, c.letterSpacing, c.lineHeight].join('|'); };"
        " return { sub: sl && sl.innerText, lu: lu && lu.innerText, same: sl && lu ? cs(sl) === cs(lu) : null, h: sl && sl.getBoundingClientRect().height, img: (document.querySelector('.brand img') || {}).height }; })()"}] + (extra or []), 'step2_mast')['results']['m']


class LastUpdated(unittest.TestCase):
    def test_2a_keeper(self):
        none = mast(K)
        self.assertIsNone(none['lu'], 'no saving ledger entry yet: nothing shown')
        led = K.root / 'data' / 'state' / 'ledger.jsonl'
        with open(led, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'at': '2026-11-03T07:30:00+00:00', 'verb': 'drop_unverified', 'after_sha': 'x'}) + '\n')
        m = mast(K)
        self.assertEqual(m['lu'].lower(), 'last updated nov. 2, 2026', m)
        self.assertTrue(m['same'], 'same font, size, colour and letter spacing as the subtitle')
        self.assertLessEqual(m['h'], int(m['img']) + 1, 'the three lines fit beside the logo without making the masthead taller')

    def test_2b_refresh_carries_it_to_a_reader(self):
        global R
        r = K.job('refresh_make', {'full': True}, timeout=900)
        self.assertTrue(r.get('ok'), r)
        import zipfile
        z = zipfile.ZipFile(r['path'])
        man = json.loads(z.read('manifest.json'))
        z.close()
        self.assertEqual(man.get('last_updated'), '2026-11-02')
        R = T.Server(T.make_work(BASE, 'reader', 'reader')).start()
        shutil.copy2(r['path'], R.root / 'data' / 'updates' / 'refresh_incoming' / Path(r['path']).name)
        r2 = R.job('refresh_take', {'file': Path(r['path']).name}, timeout=1200)
        self.assertTrue(r2.get('ok'), r2)
        S['wb_ok'] = True
        m = mast(R)
        self.assertEqual(m['lu'].lower(), 'last updated nov. 2, 2026', m)
        shutil.rmtree(r['path'], ignore_errors=True) if Path(r['path']).is_dir() else Path(r['path']).unlink()


class ViewOriginal(unittest.TestCase):
    def test_3_print_original(self):
        cov = P.coverage(K)['Coverage']
        pick = [(sid, rows[0]) for sid, rows in cov.items() if len(rows) == 1 and str(rows[0].get('Date') or '')[:4] == '2026' and rows[0].get('Headline') and rows[0].get('Article ID')
                and str(rows[0].get('Original or reprint')) == 'Original']
        (sid, row), (sid2, row2) = pick[0], pick[1]
        aid = str(row['Article ID'])
        d = K.root / 'data' / 'library' / '_original_pdf' / '2026'
        d.mkdir(parents=True, exist_ok=True)
        pdf = b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n'
        (d / f'{aid}_p16-21.pdf').write_bytes(pdf)
        (d / f'{aid}_p22.pdf').write_bytes(pdf)
        (d / f'nb{str(row2["Article ID"])}o-s{sid2[1:]}.pdf').write_bytes(pdf)        # a NewsBank text PDF: never a "View original"
        r = K.job('rebuild', {}, timeout=1200)
        self.assertTrue(r.get('ok'), r)
        html = (K.root / 'data' / 'site' / 'index.html').read_text(encoding='utf-8')
        self.assertIn(f'{aid}_p16-21.pdf', html, 'the rebuilt page lists the print original')
        self.assertIn(f'{aid}_p22.pdf', html)
        self.assertNotIn('"f":"2026/nb' + str(row2['Article ID']), html.replace(' ', ''), 'a NewsBank text PDF is never a print original')
        # the file is served; other names and paths are not
        self.assertEqual(K.get(f'/library/_original_pdf/2026/{aid}_p16-21.pdf')[:5], b'%PDF-')
        import urllib.error
        for bad in (f'/library/_original_pdf/2026/nb{str(row2["Article ID"])}o-s{sid2[1:]}.pdf', '/library/_original_pdf/2026/../../workbook/x.xlsx', '/library/2026/x.pdf',
                    f'/library/_original_pdf/2026/{aid}_p16-21.html', '/library/_original_pdf/20x6/00001_p1.pdf', f'/library/_original_pdf/%2e%2e/2026/{aid}_p22.pdf'):
            with self.assertRaises(urllib.error.HTTPError, msg=bad) as cm:
                K.get(bad)
            self.assertEqual(cm.exception.code, 404, bad)
        # the story sheet in the page
        out = T.ui(K, [{'op': 'goto', 'wait': 3000}, {'op': 'eval', 'name': 'a', 'expr': P.js_open(sid, row['Headline'], "const l = [...document.querySelectorAll('#sheet [data-lk=po]')]; return [l.map(a => a.textContent), l.map(a => a.getAttribute('href')), l.map(a => a.target)];")},
                       {'op': 'eval', 'name': 'b', 'expr': P.js_open(sid2, row2['Headline'], "return document.querySelectorAll('#sheet [data-lk=po]').length;")}], 'step2_vo')
        a = out['results']['a']
        self.assertEqual(len(a[0]), 2, a)
        self.assertTrue(all('View original' in t for t in a[0]) and any('16-21' in t for t in a[0]) and any('page 22' in t for t in a[0]), a)
        self.assertIn(f'/library/_original_pdf/2026/{aid}_p16-21.pdf', a[1])
        self.assertEqual(set(a[2]), {'_blank'})
        self.assertEqual(out['results']['b'], 0, 'a story without a print original has no button')
        self.assertEqual([e for e in out['errors'] if 'http 404' in e], [], out['errors'])


class Stalled(unittest.TestCase):
    def test_4_stalled_refresh_is_reported_and_stopped(self):
        os.environ.update(AJG_TEST_HANG='refresh_make', AJG_TEST_STALL_WARN='3', AJG_TEST_STALL_KILL='9')
        try:
            H = T.Server(T.make_work(BASE, 'hang', 'keeper')).start()
        finally:
            for k in ('AJG_TEST_HANG', 'AJG_TEST_STALL_WARN', 'AJG_TEST_STALL_KILL'):
                os.environ.pop(k, None)
        try:
            st, j = H.call('POST', '/_local/station/refresh_make', {'full': True})
            self.assertEqual(st, 200, j)
            seen_stalled, res, t0 = False, None, time.time()
            while time.time() - t0 < 60:
                _, g = H.call('GET', '/_local/station/job/' + j['job'])
                if g.get('stalled'):
                    seen_stalled = True
                if g['state'] == 'done':
                    res = g['result']
                    break
                time.sleep(0.5)
            self.assertTrue(seen_stalled, 'the page was told the job had stopped moving before it was stopped')
            self.assertIsNotNone(res, 'the job ended')
            self.assertFalse(res['ok'])
            self.assertTrue(res.get('stalled'))
            self.assertIn('Nothing was changed', res['line'])
            self.assertEqual(list((H.root / 'data' / 'refresh_out').glob('*.part')), [])
            self.assertFalse((H.root / 'data' / 'state' / 'app.lock').exists(), 'the stopped job\'s lock is put away')
            self.assertTrue(list((H.root / 'data' / 'state' / 'logs').glob('app.lock.stopped.*')))
            _, s = H.call('GET', '/_local/station/status')
            self.assertFalse((s.get('lock') or {}).get('held'))
            self.assertIsNone(s['job'] and s['job'].get('state') == 'running' or None)
        finally:
            H.stop()


if __name__ == '__main__':
    unittest.main()
