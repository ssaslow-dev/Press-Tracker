"""PHOTOLINK-v1 tests: new saved copies keep their photos as remote <img> links; Edge loads them, the program never does.
    python3 -I -m unittest discover -s work/localapp/app/tests -p "test_photolink.py" -v      (needs the Linux test build; node + Playwright at /opt/node-tools)

LinkPage   the pipeline step on its own (patched img_embed.embed_page -> photolink.link_page), in a child python with every socket call
           and `requests` forbidden; the media gate and make_copies accept the result
Viewer     the real page in Chromium: a copy with remote photos opened in the viewer; the requests the browser WOULD make are caught
           (nothing leaves the machine) and checked: only the photo, no Referer, lazily; a broken photo disappears, its caption stays
Save       a synthetic update whose page carries real-looking remote photos goes through preview + save on the real workbook; every python
           process of the app runs under a net guard (support.install_netguard) that logs any non-loopback connection or name lookup
All hosts are on the reserved .test domain: nothing here can reach a real server."""
import base64
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import support as T  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_photolink'
PIPE = T.BUILD / 'app' / 'pipeline'
PY = T.BUILD / 'python' / 'bin' / 'python'


def png_b64(w=200, h=120):
    raw = b''.join(b'\x00' + bytes([90, 140, 200]) * w for _ in range(h))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
    return base64.b64encode(png).decode()


PNG = png_b64()
DATA_PNG = 'data:image/png;base64,' + png_b64(80, 60)

RUNNER = r'''
import json, os, sys
pipe = sys.argv[1]
sys.path.insert(0, pipe)
import socket
calls = []
def boom(*a, **k):
    calls.append(repr(a)[:80]); raise OSError('no network in this test')
socket.socket.connect = socket.socket.connect_ex = boom
socket.getaddrinfo = socket.create_connection = boom
sys.modules['requests'] = None          # `import requests` raises ImportError
import img_embed as IE, media_gate as MG
case = json.load(sys.stdin)
page, st = IE.embed_page(case['page'], case['base'], sys.argv[2])
print(json.dumps({'page': page, 'st': st, 'scan': MG.scan(page), 'socket_calls': calls}))
'''


def run_embed(page, base='https://news.example.test/2026/story', link=True):
    env = {k: v for k, v in os.environ.items() if k not in ('AJG_LINK_PHOTOS',)}
    env['AJG_NO_NETWORK'] = '1'
    if link:
        env['AJG_LINK_PHOTOS'] = '1'
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False, dir=str(T.SCRATCH)) as f:
        f.write(RUNNER)
    try:
        cache = tempfile.mkdtemp(dir=str(T.SCRATCH), prefix='cache_')
        p = subprocess.run([str(PY), '-I', f.name, str(PIPE), cache], input=json.dumps({'page': page, 'base': base}), capture_output=True, text=True,
                           env=env, timeout=120)
    finally:
        os.unlink(f.name)
        shutil.rmtree(cache, ignore_errors=True)
    if p.returncode:
        raise AssertionError(p.stderr[-1500:])
    return json.loads(p.stdout.strip().splitlines()[-1])


HEAD = '<html><head><title>t</title></head><body><div>Test Gazette · 2026-10-01<br>https://news.example.test/2026/story<br>Saved 2026-11-02</div>'
FOOT = '</body></html>'


@unittest.skipUnless(T.BUILD.is_dir(), 'no test build: python3 -I assemble_app.py --target linux --role keeper')
class LinkPage(unittest.TestCase):
    maxDiff = None

    def test_remote_photo_kept_as_one_https_link_with_caption(self):
        page = HEAD + ('<article><h1>Gabriel story</h1><p>Jesse Gabriel said so.</p><figure><picture>'
                       '<source srcset="https://images.example.test/p-2400.jpg 2400w, https://images.example.test/p-900.jpg 900w">'
                       '<img src="https://images.example.test/photo.jpg" srcset="https://images.example.test/a-400.jpg 400w, '
                       'https://images.example.test/a-800.jpg 800w, https://images.example.test/a-1600.jpg 1600w" sizes="100vw" '
                       'data-src="https://other.example.test/lazy.jpg" loading="eager" referrerpolicy="unsafe-url" onerror="x()" alt="A > B">'
                       '</picture><figcaption>The caption stays.</figcaption></figure></article>') + FOOT
        r = run_embed(page)
        out = r['page']
        self.assertEqual(r['socket_calls'], [], 'the step must not touch the network')
        self.assertEqual(out.count('<img'), 1)
        self.assertIn('src="https://images.example.test/p-900.jpg"', out, 'largest srcset entry up to 1000 px wide (900 beats 800 and the 2400 one)')
        self.assertIn('referrerpolicy="no-referrer"', out)
        self.assertIn('loading="lazy"', out)
        for gone in ('srcset', 'sizes=', 'data-src', 'unsafe-url', 'eager', 'onerror', 'other.example.test', 'a-800', 'p-2400', '<picture', '<source'):
            self.assertNotIn(gone, out)
        self.assertIn('alt="A > B"', out)
        self.assertIn('<figcaption>The caption stays.</figcaption>', out)
        self.assertEqual(r['scan'], [], 'the media gate has nothing to reject')
        self.assertEqual((r['st']['linked'], r['st']['dropped'], r['st']['fetched'], r['st']['failed']), (1, 0, 0, []))

    def test_https_preferred_http_kept_only_without_https_and_recorded(self):
        page = HEAD + ('<article><p>Jesse Gabriel.</p>'
                       '<img src="http://cdn.example.test/one.jpg" srcset="http://cdn.example.test/one-800.jpg 800w, https://cdn.example.test/one-600.jpg 600w">'
                       '<img src="http://old.example.test/two.jpg" alt="http only">'
                       '<img src="//protocol.example.test/three.jpg"></article>') + FOOT
        r = run_embed(page)
        out = r['page']
        self.assertIn('src="https://cdn.example.test/one-600.jpg"', out)
        self.assertIn('src="http://old.example.test/two.jpg"', out)
        self.assertIn('src="https://protocol.example.test/three.jpg"', out, 'protocol-relative: https')
        self.assertEqual(r['st']['http_only'], ['http://old.example.test/two.jpg'])
        self.assertNotIn('http://cdn.example.test', out)

    def test_ads_pixels_logos_dropped_wrappers_pruned_captions_kept(self):
        page = HEAD + ('<article><p>Jesse Gabriel.</p>'
                       '<div class="ad"><img src="https://ad.doubleclick.net/pixel?id=1"></div>'
                       '<img src="https://track.example.test/t.gif" width="1" height="1">'
                       '<figure><img src="https://cdn.example.test/site-logo.png"><figcaption>Logo caption</figcaption></figure>'
                       '<span><a href="https://x.example.test"><img src="https://www.facebook.com/tr?id=9&ev=PageView"></a></span>'
                       '<img src="https://cdn.example.test/tiny.jpg" width="40" height="30">'
                       '<img src="https://cdn.example.test/author-avatar.jpg">'
                       '<img src="https://cdn.example.test/real.jpg" width="640" height="480" alt="real">'
                       '<img alt="no address at all"><img src="relative-only.jpg"></article>') + FOOT
        r = run_embed(page, base='')
        out = r['page']
        self.assertEqual(out.count('<img'), 1, out)
        self.assertIn('src="https://cdn.example.test/real.jpg"', out)
        for gone in ('doubleclick', 'track.example.test', 'site-logo', 'facebook', 'tiny.jpg', 'avatar', 'relative-only', 'class="ad"', 'jg-img-dropped'):
            self.assertNotIn(gone, out)
        self.assertIn('Logo caption', out)
        self.assertEqual(r['st']['dropped'], 8)
        self.assertEqual((r['st']['junk'], r['st']['small']), (4, 2))

    def test_script_svg_video_iframe_audio_still_removed(self):
        page = HEAD + ('<article><script>window.top.__x=1</script><p>Jesse Gabriel.</p>'
                       '<svg width="10" height="10"><circle r="3"/></svg>'
                       '<video src="https://v.example.test/a.mp4" poster="https://v.example.test/poster.jpg"><track src="a.vtt"></video>'
                       '<audio src="https://v.example.test/a.mp3"></audio><iframe src="https://embed.example.test/x"></iframe>'
                       '<object data="x.swf"></object><canvas></canvas>'
                       '<img src="https://cdn.example.test/icon.svg"><img src="https://cdn.example.test/pic.avif">'
                       '<img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciLz4=">'
                       '<img src="https://cdn.example.test/ok.webp"></article><script src="https://t.example.test/x.js"></script>') + FOOT
        r = run_embed(page)
        out = r['page'].lower()
        for gone in ('<script', '<svg', '<video', '<audio', '<iframe', '<object', '<canvas', '<track', '<source', 'icon.svg', 'pic.avif', 'svg+xml', 'poster'):
            self.assertNotIn(gone, out)
        self.assertIn('src="https://cdn.example.test/ok.webp"', out)
        self.assertEqual(r['scan'], [])

    def test_embedded_and_local_images_stay_and_placeholders_are_replaced(self):
        page = HEAD + (f'<article><p>Jesse Gabriel.</p><img src="{DATA_PNG}" alt="embedded"><img src="jgimg:3/0123456789abcdef"><img src="pdf/jg-abc123/p1.jpg">'
                       '<img src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==" data-src="https://cdn.example.test/lazy.jpg">'
                       '<img src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="></article>') + FOOT
        out = run_embed(page)['page']
        self.assertEqual(out.count('<img'), 4)
        self.assertIn(DATA_PNG, out)
        self.assertIn('src="jgimg:3/0123456789abcdef"', out)
        self.assertIn('src="pdf/jg-abc123/p1.jpg"', out)
        self.assertIn('src="https://cdn.example.test/lazy.jpg"', out)

    def test_without_the_switch_the_old_offline_behaviour_is_unchanged(self):
        page = HEAD + '<article><p>Jesse Gabriel.</p><img src="https://cdn.example.test/real.jpg" alt="x"></article>' + FOOT
        r = run_embed(page, link=False)
        self.assertNotIn('real.jpg', r['page'], 'no AJG_LINK_PHOTOS: the photo step runs as before (nothing in the cache, no network: dropped)')
        self.assertEqual(r['socket_calls'], [])

    def test_make_copies_accepts_remote_img_and_does_not_exit_4(self):
        import pandas as pd
        d = Path(tempfile.mkdtemp(dir=str(T.SCRATCH), prefix='mc_'))
        try:
            page = run_embed(HEAD + ('<article><h1>Gabriel story</h1><p>Jesse Gabriel said so.</p><figure>'
                                     '<img src="https://images.example.test/photo.jpg"><figcaption>Cap</figcaption></figure></article>') + FOOT)['page']
            (d / 'clean' / '2026').mkdir(parents=True)
            (d / 'clean' / '2026' / 'ws00001o-s00001.html').write_text(page, encoding='utf-8')
            (d / 'src' / 'articles').mkdir(parents=True)
            (d / 'src' / 'articles' / 'manifest.json').write_text('{"articles":{}}')
            cols = ['Story ID', 'Article ID', 'Print Article ID', 'Original or reprint', 'Outlet', 'Date', 'Year', 'Headline', 'Tracker story code',
                    'Press release', 'Page', 'Author / byline', 'Language', 'Publisher link']
            row = ['s00001', '00001', '', 'Original', 'Test', '2026-10-01', '2026', 'Gabriel story', '', '', '', '', 'English', 'https://news.example.test/a']
            with pd.ExcelWriter(d / 'cov.xlsx') as w:
                pd.DataFrame([row], columns=cols).to_excel(w, sheet_name='Coverage', index=False)
            p = subprocess.run([str(PY), '-I', str(PIPE / 'make_copies.py'), str(d / 'src'), str(d / 'cov.xlsx'), str(d / 'out'), '--clean', str(d / 'clean'),
                                '--no-av-clean'], capture_output=True, text=True, timeout=300, env=dict(os.environ, AJG_NO_NETWORK='1'))
            self.assertEqual(p.returncode, 0, p.stderr[-800:])
            shard = json.loads((d / 'out' / 'articles' / '2026.json').read_text(encoding='utf-8'))
            self.assertIn('src="https://images.example.test/photo.jpg"', shard['s00001'])
            self.assertIn('referrerpolicy="no-referrer"', shard['s00001'])
            # what the gate still rejects stays rejected: a copy that carries an svg or a video is cleaned by the gate before the belt check,
            # and the belt (media_gate.scan) names it when it is left
            sc = subprocess.run([str(PY), '-I', '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import media_gate as M, json; '
                                 'print(json.dumps([M.scan(x) != [] for x in ["<img src=\\"https://a.example.test/p.jpg\\">", "<svg></svg>", "<video></video>", '
                                 '"<img src=\\"https://a.example.test/p.svg\\">", "<img src=\\"data:image/svg+xml;base64,AAAA\\">"]]))', str(PIPE)],
                                capture_output=True, text=True)
            self.assertEqual(json.loads(sc.stdout), [False, True, True, True, True], sc.stderr)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_patches_apply_exactly_once_only(self):
        sys.path.insert(0, str(HERE.parent))
        import assemble_app as A
        patch = (HERE.parent / 'patches' / '05_sheet_task_photolink.patch').read_text(encoding='utf-8')
        src = (PIPE / 'sheet_task.py').read_text(encoding='utf-8')
        with self.assertRaises(SystemExit):        # already applied: the old lines are gone
            A.apply_unified(src, patch, 'again')
        with self.assertRaises(SystemExit):        # a second copy of the lines: two places
            first = patch.split('@@')[2].split('\n', 1)[1]
            old = ''.join(l[1:] + '\n' for l in first.split('\n') if l[:1] in ' -')
            A.apply_unified(src + '\n' + old + '\n' + old, patch, 'twice')


VIEW_PAGE = ('<html><head><title>t</title></head><body><div>Test Gazette · 2026-10-01<br>https://news.example.test/2026/photolink<br>Saved 2026-11-02</div>'
             '<h1>PHOTOLINK viewer test</h1><p>Jesse Gabriel spoke at length about the plan.</p>'
             '<figure><img src="https://images.example.test/photo.jpg" srcset="https://other.example.test/big.jpg 2000w" data-src="https://other.example.test/lazy.jpg" '
             'referrerpolicy="unsafe-url" loading="eager" alt="A photo"><figcaption>Photo caption stays</figcaption></figure>'
             '<figure><img src="https://images.example.test/missing.jpg" alt="gone"><figcaption>Gone caption stays</figcaption></figure>'
             f'<img src="{DATA_PNG}" alt="embedded"><img src="//protocol.example.test/relative.jpg"><img src="javascript:window.parent.__pwn=1">'
             '<link rel="stylesheet" href="https://styles.example.test/x.css"><script>window.parent.__pwn=1</script>'
             '<p style="background:url(https://bg.example.test/b.png)">styled</p></body></html>')


# the tracker's code is private to the page, so the test opens a copy the way a person does: Clips tab, search for the headline, click the row
OPEN_JS = ("""async (hl) => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const rows = JSON.parse(document.getElementById('data').textContent), row = rows.find(r => (r.hl || '').includes(hl));
  if (!row) return null;
  const tab = [...document.querySelectorAll('button,a,[role=tab],nav *')].find(x => /^\\s*Clips\\s*$/.test(x.textContent) && x.offsetParent); if (tab) tab.click();
  await sleep(1500);
  const q = document.getElementById('q'); q.value = hl; q.dispatchEvent(new Event('input', { bubbles: true }));
  await sleep(3000);
  const tr = document.querySelector('#tbody tr[data-id="' + row.id + '"]'); if (!tr) return { id: row.id, error: 'row not listed' };
  tr.click();
  for (let i = 0; i < 40 && !document.querySelector('#doc iframe'); i++) await sleep(250);
  await sleep(3500);
  const f = document.querySelector('#doc iframe'); if (!f) return { id: row.id, error: 'no viewer frame' };
  const d = f.contentDocument;
  return { id: row.id, sandbox: f.getAttribute('sandbox'), csp: (d.querySelector('meta[http-equiv="Content-Security-Policy"]') || {}).content || null,
    imgs: [...d.querySelectorAll('img')].map(i => ({ src: (i.getAttribute('src') || '').slice(0, 80), rp: i.getAttribute('referrerpolicy'), lazy: i.getAttribute('loading'),
      srcset: i.hasAttribute('srcset') || i.hasAttribute('data-src'), w: i.naturalWidth })),
    caps: [...d.querySelectorAll('figcaption')].map(c => c.textContent), nonImg: d.querySelectorAll('svg,script,video,audio,iframe').length, pwn: typeof window.__pwn };
}""")


def open_expr(headline):
    return '(%s)(%s)' % (OPEN_JS, json.dumps(headline))


@unittest.skipUnless(T.BUILD.is_dir(), 'no test build')
class Viewer(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        shutil.rmtree(BASE / 'view', ignore_errors=True)
        (BASE / 'view').mkdir(parents=True)
        cls.root = T.make_work(BASE / 'view', 'reader', 'reader')
        cls.guard = T.install_netguard(cls.root)
        man = json.loads((cls.root / 'data' / 'copies' / 'articles' / 'manifest.json').read_text())['articles']
        cls.sid = next(k for k, v in man.items() if v.endswith('/2026.json') and not k.startswith('pr'))
        shard = cls.root / 'data' / 'copies' / 'articles' / '2026.json'
        d = json.loads(shard.read_text(encoding='utf-8'))
        d[cls.sid] = VIEW_PAGE
        tmp = shard.with_name('2026.new')
        tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        shard.unlink()                      # the work copy is hard-linked to the build: replace the file, never write into it
        tmp.rename(shard)
        cls.html_data = re.search(r'<script id="data" type="application/json">(.*?)</script>', (cls.root / 'data' / 'site' / 'index.html').read_text(encoding='utf-8'), re.S).group(1)
        cls.srv = T.Server(cls.root).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def test_viewer_requests_only_the_photo_without_referer_and_nothing_else_opens(self):
        rules = [{'match': 'images.example.test/photo.jpg', 'type': 'image/png', 'b64': PNG},
                 {'match': 'images.example.test/missing.jpg', 'status': 404, 'type': 'text/plain', 'body': 'no'},
                 {'match': 'control.example.test', 'type': 'image/png', 'b64': PNG}]
        hl = next(r['hl'] for r in json.loads(self.html_data) if r['id'] == self.sid)
        expr = open_expr(hl)
        control = ("new Promise(res => { const i = new Image(); i.referrerPolicy = 'unsafe-url'; i.onload = i.onerror = () => res(1); "
                   "i.src = 'https://control.example.test/c.png'; })")
        out = T.ui(self.srv, [{'op': 'intercept', 'rules': rules}, {'op': 'goto'}, {'op': 'eval', 'name': 'ctl', 'expr': control},
                              {'op': 'eval', 'name': 'view', 'expr': expr},
                              {'op': 'screenshot', 'path': str(T.SHOTS / 'photolink_view.png')}], 'photolink_view')
        r = out['results']
        self.assertNotIn('crash', r, r)
        v = r['view']
        by = {}
        for e in out['external']:
            by.setdefault(e['url'].split('?')[0], []).append(e)
        # the control proves the capture would show a Referer if one were sent
        self.assertTrue(by['https://control.example.test/c.png'][0]['referer'], 'control request must carry a Referer')
        photo = by['https://images.example.test/photo.jpg']
        self.assertEqual((len(photo), photo[0]['type']), (1, 'image'))
        self.assertIsNone(photo[0]['referer'], 'no Referer on the photo request')
        self.assertIn('https://images.example.test/missing.jpg', by)
        self.assertIsNone(by['https://images.example.test/missing.jpg'][0]['referer'])
        # nothing else was requested: no srcset or data-src alternative, no stylesheet, no CSS background, no script
        sheet = by['https://styles.example.test/x.css'][0]
        self.assertEqual(sheet['failure'], 'csp', 'a stylesheet in a saved copy is stopped by the frame\'s own policy before it leaves the browser')
        live = sorted({e['url'].split('/')[2] for e in out['external'] if e['failure'] != 'csp'})
        # LOCALFONTS-v1: the fonts come from the PC's own server now, so no font host is allowed; a CSS background image counts as an image
        allowed = {'control.example.test', 'images.example.test', 'bg.example.test'}
        self.assertTrue(set(live) <= allowed, ('unexpected hosts requested', live))
        # the viewer's frame: sandboxed without scripts, locked to images (+ fonts) by its own policy
        self.assertEqual(v['sandbox'], 'allow-same-origin allow-popups allow-popups-to-escape-sandbox')
        self.assertIn("img-src 'self' data: blob: https: http:", v['csp'])
        self.assertIn("connect-src 'none'", v['csp'])
        self.assertIn("script-src 'none'", v['csp'])
        self.assertEqual(v['pwn'], 'undefined', 'the script in a saved copy never ran (frame is sandboxed without scripts)')
        srcs = [i['src'] for i in v['imgs']]
        self.assertIn('https://images.example.test/photo.jpg', srcs)
        photo_img = next(i for i in v['imgs'] if i['src'].endswith('/photo.jpg'))
        self.assertEqual((photo_img['rp'], photo_img['lazy'], photo_img['srcset']), ('no-referrer', 'lazy', False))
        self.assertGreater(photo_img['w'], 0, 'the photo (answered by the test) was drawn')
        self.assertFalse([s for s in srcs if s.startswith('javascript') or s.startswith('//')], srcs)
        self.assertTrue([i for i in v['imgs'] if i['src'].startswith('data:image/png') and i['w'] > 0], 'an embedded photo still renders')
        self.assertNotIn('https://images.example.test/missing.jpg', srcs, 'a photo that fails to load is removed after the error')
        self.assertIn('Photo caption stays', v['caps'])
        self.assertIn('Gone caption stays', v['caps'])
        self.assertEqual([e for e in out['errors'] if 'requestfailed' not in e and '404' not in e and 'Content Security Policy' not in e and 'sandboxed' not in e], [], out['errors'])

    def test_server_sends_no_referrer_policy_and_the_program_made_no_connections(self):
        import urllib.request
        for path in ('/', '/articles/manifest.json', '/_local/station.js'):
            with urllib.request.urlopen(self.srv.base + path, timeout=60) as r:
                self.assertEqual(r.headers.get('Referrer-Policy'), 'no-referrer', path)
                self.assertIsNone(r.headers.get('Content-Security-Policy'), 'the server adds no policy of its own (nothing new opened)')
        self.assertFalse(self.guard.exists(), self.guard.read_text() if self.guard.exists() else '')


def read_ledger(root):
    return [json.loads(l) for l in (root / 'data' / 'state' / 'ledger.jsonl').read_text().splitlines() if l.strip()]


EXTRA = ('<article><h2>Photo section</h2>'
         '<figure><img src="https://images.example.test/save-photo.jpg" srcset="https://images.example.test/save-photo-480.jpg 480w, '
         'https://images.example.test/save-photo-900.jpg 900w, https://images.example.test/save-photo-2000.jpg 2000w" sizes="100vw" alt="Saved photo">'
         '<figcaption>Saved photo caption</figcaption></figure>'
         '<img src="https://ad.doubleclick.net/pixel?x=save" width="1" height="1">'
         '<img src="https://cdn.example.test/site-logo.png">'
         '<svg width="5" height="5"><circle r="2"/></svg><script>window.top.__pwn=1</script>'
         '<p>Quokkaplink searchable.</p></article>')


@unittest.skipUnless(T.BUILD.is_dir(), 'no test build')
class Save(unittest.TestCase):
    """one preview + save of a synthetic update (slow: a couple of minutes on the real workbook)"""
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        shutil.rmtree(BASE / 'save', ignore_errors=True)
        (BASE / 'save').mkdir(parents=True)
        cls.root = T.make_work(BASE / 'save', 'keeper', 'keeper')
        cls.guard = T.install_netguard(cls.root)
        cls.srv = T.Server(cls.root).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def test_save_keeps_links_and_the_page_shows_them(self):
        K = self.srv
        z = T.make_update_zip(K.root, BASE / 'save' / 'plink.zip', 'plink', extra_html=EXTRA)
        rules = [{'match': 'images.example.test/save-photo-900.jpg', 'type': 'image/png', 'b64': PNG}]
        view = open_expr('Gabriel bill test story plink')
        out = T.ui(K, [{'op': 'intercept', 'rules': rules}, {'op': 'goto'}, {'op': 'open_panel'}, {'op': 'file', 'path': str(z)},
                       {'op': 'wait_text', 'text': ['If you press Save'], 'timeout': 900000, 'name': 'prev'},
                       {'op': 'mark'}, {'op': 'click', 'text': 'Save'},
                       {'op': 'wait_text', 'text': ['Saved.', 'Not saved'], 'timeout': 1200000, 'name': 'saved'},
                       {'op': 'wait_reload'},
                       {'op': 'eval', 'name': 'view', 'expr': view},
                       {'op': 'screenshot', 'path': str(T.SHOTS / 'photolink_saved.png')}], 'photolink_save')
        r = out['results']
        self.assertNotIn('crash', r, r)
        self.assertEqual(r['saved'], 'Saved.', r['saved_panel'])
        # the library page and the shard the page reads
        lib = K.root / 'data' / 'library' / '2026'
        saved = [p for p in lib.glob('ws*o-s*.html') if 'quokkaplink' in p.read_text(encoding='utf-8', errors='replace').lower()]
        self.assertTrue(saved, 'the new page was added to the library')
        shard = K.get('/articles/2026.json').decode('utf-8')
        self.assertIn('quokkaplink', shard.lower())
        pages = [p.read_text(encoding='utf-8', errors='replace') for p in saved]
        for page in pages + [json.loads(shard)[next(k for k, v in json.loads(shard).items() if 'quokkaplink' in v.lower())]]:
            self.assertIn('src="https://images.example.test/photo-plink.jpg"', page, 'the update\'s ordinary remote photo is kept as a link')
            self.assertIn('src="https://images.example.test/save-photo-900.jpg"', page, 'largest srcset entry up to 1000 px')
            self.assertEqual(page.count('referrerpolicy="no-referrer" loading="lazy"'), 2, page[-1500:])
            for gone in ('save-photo-480', 'save-photo-2000', 'srcset', 'doubleclick', 'site-logo', '<svg', '<script', 'window.top.__pwn'):
                self.assertNotIn(gone, page)
            self.assertIn('Saved photo caption', page)
        self.assertEqual(read_ledger(K.root)[-1]['verb'], 'save')
        # the browser: the opened copy would request exactly these photos, with no Referer
        v = r['view']
        self.assertTrue(v, 'the new story is in the page')
        self.assertEqual(v['nonImg'], 0)
        self.assertEqual(v['pwn'], 'undefined')
        self.assertIn("img-src 'self' data: blob: https: http:", v['csp'])
        got = {e['url']: e for e in out['external']}
        self.assertIn('https://images.example.test/save-photo-900.jpg', got)
        self.assertIsNone(got['https://images.example.test/save-photo-900.jpg']['referer'])
        self.assertTrue(all(e['referer'] is None for e in out['external'] if 'images.example.test' in e['url']))
        self.assertFalse([u for u in got if 'doubleclick' in u or 'site-logo' in u or 'other.example' in u or '480' in u or '2000' in u], list(got))
        img = next(i for i in v['imgs'] if i['src'].endswith('save-photo-900.jpg'))
        self.assertEqual((img['rp'], img['lazy'], img['srcset']), ('no-referrer', 'lazy', False))
        self.assertGreater(img['w'], 0)
        self.assertIn('Saved photo caption', v['caps'])
        # no python process of the app (server, station_cli, saver, sheet_task, build_data) tried to leave the machine
        self.assertFalse(self.guard.exists(), self.guard.read_text() if self.guard.exists() else '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
