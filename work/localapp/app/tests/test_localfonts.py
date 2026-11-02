"""LOCALFONTS-v1 tests: the PC page and its saved-copy viewer make no request to Google Fonts or any other host, and the bundled fonts really load.
    python3 -I -m unittest discover -s work/localapp/app/tests -p "test_localfonts.py" -v      (needs the Linux test build; node + Playwright at /opt/node-tools)

Page      the real page in Chromium: every request that is not for 127.0.0.1 is recorded (and refused: nothing leaves the machine). A saved copy
          with no remote photo is opened in the viewer frame. Expected: zero outside requests, from the page and from the frame; Roboto Slab (500-800)
          and Public Sans (400-700, and 400 italic in the frame) load from /fonts/ with latin and latin-ext faces; the frame's policy allows
          font-src 'self' only; the Google hosts appear nowhere in the served page or in the pipeline's shell and tracker.js.
Files     the font folder in the build equals work/localapp/fonts/files (licences included)."""
import json
import re
import shutil
import sys
import unittest
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import support as T  # noqa: E402
from test_photolink import DATA_PNG, OPEN_JS, open_expr  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_localfonts'
FONTS_SRC = T.REPO / 'work' / 'localapp' / 'fonts' / 'files'

# latin-ext characters (Lodz, s with acute, Czech r with caron) go to the latin-ext face; the rest to latin
PAGE = ('<html><head><title>t</title></head><body><div>Test Gazette · 2026-10-01<br>https://news.example.test/2026/fonts<br>Saved 2026-11-02</div>'
        f'<h1>FONTS viewer test Łódź</h1><h2>Second heading</h2><p>Jesse Gabriel spoke at length about the plan, <em>in italics</em> and <b>bold</b>. Řeřicha.</p>'
        f'<figure><img src="{DATA_PNG}" alt="embedded"><figcaption>Embedded caption</figcaption></figure></body></html>')

CHECK_JS = """async (specs, doc) => {
  doc = doc || document;
  const out = {};
  for (const [k, spec, text] of specs) {
    try { const l = await doc.fonts.load(spec, text); out[k] = l.map(f => f.family + '|' + f.weight + '|' + f.style + '|' + f.status); } catch (e) { out[k] = 'error ' + e; }
  }
  await doc.fonts.ready;
  out.faces = [...doc.fonts].map(f => f.family.replace(/"/g, '') + '|' + f.weight + '|' + f.style + '|' + f.status);
  const h = doc.querySelector('.tile b,h2.sec,h3.sec'); out.headFamily = h ? doc.defaultView.getComputedStyle(h).fontFamily : null;
  out.bodyFamily = doc.defaultView.getComputedStyle(doc.body).fontFamily;
  return out;
}"""

SLAB = [500, 600, 700, 800]
SANS = [400, 500, 600, 700]


def specs():
    s = []
    for w in SLAB:
        s += [[f'slab-{w}', f'{w} 16px "Roboto Slab"', 'Abc'], [f'slab-ext-{w}', f'{w} 16px "Roboto Slab"', 'Łódź']]
    for w in SANS:
        s += [[f'sans-{w}', f'{w} 16px "Public Sans"', 'Abc'], [f'sans-ext-{w}', f'{w} 16px "Public Sans"', 'Łódź']]
    s += [['sans-italic', 'italic 400 16px "Public Sans"', 'Abc'], ['sans-italic-ext', 'italic 400 16px "Public Sans"', 'Łódź']]
    return s


def frame_expr(hl):
    # open the copy like a person does, then run the same check on the viewer frame's own document (from the parent: the frame has no script of its own)
    return ("(async () => { const r = await (%s)(%s); const f = document.querySelector('#doc iframe'); if (!f) return {open: r};"
            " const d = f.contentDocument; const res = await (%s)(%s, d); res.open = {csp: r.csp, sandbox: r.sandbox};"
            " const el = d.querySelector('h1'); res.h1Family = el ? f.contentWindow.getComputedStyle(el).fontFamily : null; return res; })()"
            ) % (OPEN_JS, json.dumps(hl), CHECK_JS, json.dumps(specs()))


@unittest.skipUnless(T.BUILD.is_dir(), 'no test build')
class Page(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        shutil.rmtree(BASE, ignore_errors=True)
        BASE.mkdir(parents=True)
        cls.root = T.make_work(BASE, 'reader', 'reader')
        man = json.loads((cls.root / 'data' / 'copies' / 'articles' / 'manifest.json').read_text())['articles']
        cls.sid = next(k for k, v in man.items() if v.endswith('/2026.json') and not k.startswith('pr'))
        shard = cls.root / 'data' / 'copies' / 'articles' / '2026.json'
        d = json.loads(shard.read_text(encoding='utf-8'))
        d[cls.sid] = PAGE
        tmp = shard.with_name('2026.new')
        tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        shard.unlink()                      # the work copy is hard-linked to the build: replace, never write into it
        tmp.rename(shard)
        html = (cls.root / 'data' / 'site' / 'index.html').read_text(encoding='utf-8')
        cls.html = html
        rows = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S).group(1))
        cls.hl = next(r['hl'] for r in rows if r['id'] == cls.sid)
        cls.srv = T.Server(cls.root).start()
        steps = [{'op': 'intercept', 'rules': []}, {'op': 'goto'},
                 {'op': 'eval', 'name': 'page', 'expr': '(%s)(%s)' % (CHECK_JS, json.dumps(specs()))},
                 {'op': 'eval', 'name': 'frame', 'expr': frame_expr(cls.hl)},
                 {'op': 'screenshot', 'path': str(T.SHOTS / 'localfonts_view.png')}]
        cls.out = T.ui(cls.srv, steps, 'localfonts')

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def test_no_request_to_any_other_host(self):
        r = self.out['results']
        self.assertNotIn('crash', r, r)
        self.assertEqual([e['url'] for e in self.out['external']], [], 'the page and the viewer frame requested a non-127.0.0.1 address')
        self.assertEqual([e for e in self.out['errors'] if 'Content Security Policy' not in e], [], self.out['errors'])

    def test_google_hosts_are_nowhere(self):
        for name, txt in (('served page', self.html),
                          ('pipeline shell.html', (T.BUILD / 'app' / 'pipeline' / 'shell.html').read_text(encoding='utf-8')),
                          ('pipeline tracker.js', (T.BUILD / 'app' / 'pipeline' / 'tracker.js').read_text(encoding='utf-8'))):
            self.assertNotIn('fonts.googleapis', txt, name)
            self.assertNotIn('fonts.gstatic', txt, name)
        self.assertIn('<link rel="stylesheet" href="/fonts/fonts.css">', self.html)
        self.assertNotIn('rel="preconnect"', self.html.split('</head>')[0])

    def _loaded(self, res, key, family, weight, style='normal'):
        got = res[key]
        self.assertIsInstance(got, list, (key, got))
        self.assertIn(f'{family}|{weight}|{style}|loaded', got, (key, got))

    def test_page_fonts_load(self):
        res = self.out['results']['page']
        for w in SLAB:
            self._loaded(res, f'slab-{w}', 'Roboto Slab', w)
            self._loaded(res, f'slab-ext-{w}', 'Roboto Slab', w)
        for w in SANS:
            self._loaded(res, f'sans-{w}', 'Public Sans', w)
            self._loaded(res, f'sans-ext-{w}', 'Public Sans', w)
        self.assertIn('Roboto Slab', res['headFamily'])
        self.assertIn('Public Sans', res['bodyFamily'])
        self.assertFalse([f for f in res['faces'] if f.endswith('|error')], res['faces'])
        self.assertEqual(sum(1 for f in res['faces'] if f.startswith('Roboto Slab|')), 8)
        self.assertEqual(sum(1 for f in res['faces'] if f.startswith('Public Sans|')), 10)

    def test_viewer_frame_fonts_load_and_policy_is_self_only(self):
        res = self.out['results']['frame']
        self.assertNotIn('error', res.get('open', {}), res)
        csp = res['open']['csp']
        self.assertIn("font-src 'self'", csp)
        self.assertIn("style-src 'unsafe-inline' 'self'", csp)
        self.assertNotIn('googleapis', csp)
        self.assertNotIn('gstatic', csp)
        for w in (600, 700):
            self._loaded(res, f'slab-{w}', 'Roboto Slab', w)
            self._loaded(res, f'slab-ext-{w}', 'Roboto Slab', w)
        for w in (400, 600):
            self._loaded(res, f'sans-{w}', 'Public Sans', w)
            self._loaded(res, f'sans-ext-{w}', 'Public Sans', w)
        self._loaded(res, 'sans-italic', 'Public Sans', 400, 'italic')
        self._loaded(res, 'sans-italic-ext', 'Public Sans', 400, 'italic')
        self.assertIn('Roboto Slab', res['h1Family'])

    def test_server_serves_the_fonts(self):
        for name in ('fonts.css', 'roboto-slab-latin-700-normal.woff2', 'public-sans-latin-400-italic.woff2', 'LICENSE-roboto-slab', 'LICENSE-public-sans'):
            with urllib.request.urlopen(self.srv.base + '/fonts/' + name, timeout=60) as r:
                self.assertEqual(r.status, 200, name)
                if name.endswith('.woff2'):
                    self.assertEqual(r.headers.get('Content-Type'), 'font/woff2')
                    self.assertEqual(r.read(4), b'wOF2')

    def test_build_fonts_equal_the_repository_fonts(self):
        built = {p.name: p.read_bytes() for p in (T.BUILD / 'data' / 'site' / 'fonts').iterdir()}
        src = {p.name: p.read_bytes() for p in FONTS_SRC.iterdir() if p.suffix != '.json'}
        self.assertEqual(built, src)
        self.assertTrue(any(n.startswith('LICENSE') for n in built))


if __name__ == '__main__':
    unittest.main()
