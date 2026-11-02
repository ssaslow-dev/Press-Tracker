import http.client, json, os, shutil, socket, sys, tempfile, threading, time, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import server as S


class Base(unittest.TestCase):
    tok = True
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.site = os.path.join(cls.tmp, 'site')
        cls.data = os.path.join(cls.tmp, 'data')
        os.makedirs(os.path.join(cls.site, 'articles'))
        os.makedirs(os.path.join(cls.site, 'empty'))
        open(os.path.join(cls.site, 'index.html'), 'w').write('<html><head><title>x</title></head><body><script>1</script></body></html>')
        open(os.path.join(cls.site, 'articles', 'a.json'), 'w').write('{"a":1}')
        open(os.path.join(cls.site, 'articles', 'b.webp'), 'wb').write(b'RIFF')
        open(os.path.join(cls.site, '.secret'), 'w').write('s')
        open(os.path.join(cls.tmp, 'outside.txt'), 'w').write('outside')
        cls.srv = S.TrackerServer(cls.site, cls.data, 0)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close(); shutil.rmtree(cls.tmp, ignore_errors=True)

    def req(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        h = dict(headers or {})
        if self.tok and 'X-Local-Token' not in h:
            h['X-Local-Token'] = self.srv.token
        if body is not None:
            body = json.dumps(body) if not isinstance(body, (bytes, str)) else body
        c.request(method, path, body=body, headers=h)
        r = c.getresponse(); data = r.read(); c.close()
        return r.status, dict(r.getheaders()), data

    def jreq(self, method, path, body=None):
        s, h, d = self.req(method, path, body)
        return s, (json.loads(d) if d else None)


class StaticTests(Base):
    def test_index_gets_shim_before_first_script(self):
        s, h, d = self.req('GET', '/')
        self.assertEqual(s, 200); t = d.decode()
        self.assertIn(S.SHIM_TAG, t)
        self.assertLess(t.index(S.SHIM_TAG), t.index('<script>1'))
        self.assertTrue(h['Content-Type'].startswith('text/html'))
        self.assertEqual(self.req('GET', '/index.html')[2], d)
        # file on disk is untouched
        self.assertNotIn('_local', open(os.path.join(self.site, 'index.html')).read())

    def test_shim_served(self):
        s, h, d = self.req('GET', S.SHIM_URL)
        self.assertEqual(s, 200); self.assertIn(b'window.claude', d); self.assertIn('javascript', h['Content-Type'])

    def test_types_and_etag(self):
        s, h, d = self.req('GET', '/articles/a.json'); self.assertEqual((s, d), (200, b'{"a":1}'))
        self.assertTrue(h['Content-Type'].startswith('application/json'))
        self.assertEqual(self.req('GET', '/articles/b.webp')[1]['Content-Type'], 'image/webp')
        s2, _, _ = self.req('GET', '/articles/a.json', headers={'If-None-Match': h['ETag']}); self.assertEqual(s2, 304)

    def test_no_listing_and_traversal(self):
        self.assertEqual(self.req('GET', '/articles/')[0], 404)
        self.assertEqual(self.req('GET', '/articles')[0], 404)
        self.assertEqual(self.req('GET', '/empty/')[0], 404)
        for p in ['/../outside.txt', '/%2e%2e/outside.txt', '/articles/../../outside.txt', '/..%2foutside.txt',
                  '/articles/%2e%2e/%2e%2e/outside.txt', '/%5c..%5coutside.txt', '/.secret', '/c:/windows/win.ini', '/a%00.json']:
            s = self.req('GET', p)[0]
            self.assertIn(s, (400, 403, 404), p)
        # raw (unnormalised) request line
        c = socket.create_connection(('127.0.0.1', self.port)); c.sendall(b'GET /../outside.txt HTTP/1.0\r\nHost: 127.0.0.1:%d\r\n\r\n' % self.port)
        self.assertNotIn(b'outside', c.recv(4096).split(b'\r\n\r\n', 1)[-1]); c.close()

    def test_symlink_escape(self):
        link = os.path.join(self.site, 'lnk.txt')
        try:
            os.symlink(os.path.join(self.tmp, 'outside.txt'), link)
        except (OSError, NotImplementedError):
            self.skipTest('no symlinks')
        self.assertEqual(self.req('GET', '/lnk.txt')[0], 403); os.remove(link)

    def test_host_and_method_checks(self):
        self.assertEqual(self.req('GET', '/', headers={'Host': 'evil.example'})[0], 403)
        self.assertEqual(self.req('PUT', '/_local/api/notes/x1', {'a': 1}, {'Origin': 'http://evil.example'})[0], 403)
        self.assertEqual(self.req('POST', '/')[0], 405)

    def test_token_required_for_api(self):
        self.assertEqual(self.req('GET', '/_local/status', headers={'X-Local-Token': 'wrong'})[0], 403)
        Base.tok = False
        try:
            for m, p in [('GET', '/_local/status'), ('GET', '/_local/api/notes'), ('PUT', '/_local/api/notes/z1'), ('DELETE', '/_local/api/notes/z1')]:
                self.assertEqual(self.req(m, p, {'a': 1} if m == 'PUT' else None)[0], 403, p)
            self.assertEqual(self.req('GET', S.SHIM_URL)[0], 200)  # shim holds no secret
        finally:
            Base.tok = True
        t = self.req('GET', '/')[2].decode()
        self.assertIn('window.__LOCAL_TOKEN="%s"' % self.srv.token, t)

    def test_binds_loopback_only(self):
        self.assertEqual(self.srv.server_address[0], '127.0.0.1')


class StoreTests(Base):
    def test_roundtrip_list_get_replace(self):
        self.assertEqual(self.jreq('PUT', '/_local/api/notes/00123', {'text': 'hi', 'at': '2026-11-02'})[0], 200)
        s, j = self.jreq('GET', '/_local/api/notes/00123'); self.assertEqual(j['data']['text'], 'hi')
        self.jreq('PUT', '/_local/api/notes/00123', {'text': 'replaced'})
        s, j = self.jreq('GET', '/_local/api/notes/00123'); self.assertEqual(j['data'], {'text': 'replaced'})
        self.jreq('PUT', '/_local/api/notes/jg-abc123', {'text': 'ünïcode — ok'})
        s, j = self.jreq('GET', '/_local/api/notes')
        self.assertEqual({d['id'] for d in j['docs']} >= {'00123', 'jg-abc123'}, True)
        f = os.path.join(self.data, 'db', 'notes', '00123.json')
        self.assertEqual(json.load(open(f)), {'text': 'replaced'})           # the layout load_db reads
        self.assertEqual([n for n in os.listdir(os.path.dirname(f)) if n.startswith('.')], [])  # no temp left
        self.assertEqual(self.jreq('GET', '/_local/api/notes/nope')[0], 404)
        self.assertEqual(self.jreq('GET', '/_local/api/fresh')[1]['docs'], [])

    def test_delete_moves(self):
        self.jreq('PUT', '/_local/api/views/v-1', {'name': 'x'})
        s, j = self.jreq('DELETE', '/_local/api/views/v-1'); self.assertTrue(j['deleted'])
        self.assertFalse(os.path.exists(os.path.join(self.data, 'db', 'views', 'v-1.json')))
        d = os.path.join(self.data, 'db', '_deleted', 'views')
        names = os.listdir(d); self.assertEqual(len(names), 1); self.assertTrue(names[0].startswith('v-1.'))
        self.assertEqual(json.load(open(os.path.join(d, names[0]))), {'name': 'x'})
        self.assertEqual(self.jreq('GET', '/_local/api/views/v-1')[0], 404)
        self.assertFalse(self.jreq('DELETE', '/_local/api/views/v-1')[1]['deleted'])
        # same id deleted twice keeps both copies
        self.jreq('PUT', '/_local/api/views/v-1', {'name': 'y'}); self.jreq('DELETE', '/_local/api/views/v-1')
        self.assertEqual(len(os.listdir(d)), 2)
        self.assertNotIn('_deleted', self.jreq('GET', '/_local/api/_versions')[1]['versions'])

    def test_validation(self):
        for c in ['_deleted', '..', '.x', 'a%20b', 'a%2Fb', 'x' * 65]:
            self.assertIn(self.req('GET', '/_local/api/' + c)[0], (400, 404), c)
        for i in ['..', '.hidden', 'a%2F..%2Fb', 'a%5Cb', 'con', 'nul.x', 'trail.', 'x' * 129, 'a%00b']:
            self.assertIn(self.req('PUT', '/_local/api/notes/' + i, {'a': 1})[0], (400, 404), i)
        self.assertFalse(os.path.exists(os.path.join(self.data, 'db', 'b')))
        self.assertEqual(self.req('PUT', '/_local/api/notes/ok1', '[1,2]')[0], 400)
        self.assertEqual(self.req('PUT', '/_local/api/notes/ok1', 'not json')[0], 400)
        self.assertEqual(self.req('GET', '/_local/api/notes/x/y')[0], 404)

    def test_changes_visible_via_versions(self):
        v0 = self.jreq('GET', '/_local/api/_versions?c=chg')[1]['versions']['chg']
        self.jreq('PUT', '/_local/api/chg/a1', {'n': 1})
        v1 = self.jreq('GET', '/_local/api/_versions?c=chg')[1]['versions']['chg']; self.assertNotEqual(v0, v1)
        self.jreq('PUT', '/_local/api/chg/a1', {'n': 2})
        v2 = self.jreq('GET', '/_local/api/_versions?c=chg')[1]['versions']['chg']; self.assertNotEqual(v1, v2)
        # another program writing the folder is noticed too
        time.sleep(0.01); open(os.path.join(self.data, 'db', 'chg', 'ext1.json'), 'w').write('{"x":1}')
        v3 = self.jreq('GET', '/_local/api/_versions?c=chg')[1]['versions']['chg']; self.assertNotEqual(v2, v3)
        self.jreq('DELETE', '/_local/api/chg/a1')
        v4 = self.jreq('GET', '/_local/api/_versions?c=chg')[1]['versions']['chg']; self.assertNotEqual(v3, v4)
        # a damaged file is skipped, not fatal
        open(os.path.join(self.data, 'db', 'chg', 'bad.json'), 'w').write('{oops')
        self.assertEqual([d['id'] for d in self.jreq('GET', '/_local/api/chg')[1]['docs']], ['ext1'])

    def test_big_doc_and_threads(self):
        big = {'clean': 'é' * 500000}
        self.assertEqual(self.jreq('PUT', '/_local/api/pages/p-1', big)[0], 200)
        self.assertEqual(self.jreq('GET', '/_local/api/pages/p-1')[1]['data'], big)
        def w(n): self.jreq('PUT', '/_local/api/conc/d%d' % (n % 5), {'n': n})
        ts = [threading.Thread(target=w, args=(n,)) for n in range(30)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertEqual(len(self.jreq('GET', '/_local/api/conc')[1]['docs']), 5)

    def test_status(self):
        self.jreq('PUT', '/_local/api/statuscol/s1', {'a': 1})
        s, j = self.jreq('GET', '/_local/status')
        self.assertEqual(j['version'], S.VERSION); self.assertEqual(j['data_dir'], os.path.abspath(self.data))
        self.assertEqual(j['collections']['statuscol'], 1); self.assertEqual(j['port'], self.port)


class PortTests(unittest.TestCase):
    def test_port_taken_is_reported(self):
        tmp = tempfile.mkdtemp()
        try:
            open(os.path.join(tmp, 'index.html'), 'w').write('<html></html>')
            hog = socket.socket(); hog.bind(('127.0.0.1', 0)); hog.listen(1)
            import io, contextlib
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = S.main(['--site', tmp, '--data', os.path.join(tmp, 'd'), '--port', str(hog.getsockname()[1])])
            hog.close()
            self.assertEqual(rc, 3); self.assertIn('already in use', err.getvalue())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
