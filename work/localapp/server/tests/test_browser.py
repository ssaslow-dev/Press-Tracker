import json, os, shutil, subprocess, sys, tempfile, threading, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import server as S


def node_playwright():
    node = shutil.which('node')
    if not node:
        return None, None
    for mod in (os.environ.get('PLAYWRIGHT_MODULE'), 'playwright', '/opt/node-tools/node_modules/playwright'):
        if not mod:
            continue
        r = subprocess.run([node, '-e', "require(%s)" % json.dumps(mod)], capture_output=True)
        if r.returncode == 0:
            return node, mod
    return None, None


class BrowserTest(unittest.TestCase):
    def test_page_uses_shim_like_00_head(self):
        node, mod = node_playwright()
        if not node:
            self.skipTest('node + playwright not available')
        tmp = tempfile.mkdtemp()
        srv = S.TrackerServer(os.path.join(HERE, 'testsite'), os.path.join(tmp, 'data'), 0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            env = dict(os.environ, PLAYWRIGHT_MODULE=mod)
            p = subprocess.run([node, os.path.join(HERE, 'browser_check.js'), 'http://127.0.0.1:%d' % srv.server_address[1], srv.token],
                               capture_output=True, text=True, env=env, timeout=120)
            self.assertEqual(p.returncode, 0, p.stderr)
            out = json.loads(p.stdout.strip().splitlines()[-1])
            r = out['res']
            self.assertNotIn('crash', r, r)
            self.assertEqual(out['errors'], [])
            self.assertTrue(r['hasUse'] and r['dbOk'] and r['sampleNull'] and r['mcpNull'])
            self.assertEqual(r['sampleCode'], 'not_declared')
            self.assertTrue(r['first'] and r['firstEmpty'], r)
            self.assertTrue(r['afterSet']); self.assertEqual(r['setData']['tone'], 'Positive')
            self.assertEqual(r['shape'], [True, 'function', 'string', 1])
            self.assertTrue(r['replaced'] and r['external'] and r['second'] and r['deleted'], r)
            self.assertIn(r['badId'], ('storage_error', 'not_found'))
            self.assertTrue(r['unsubQuiet']); self.assertEqual(r['errs'], 0)
            self.assertEqual(out['dl'], {'name': 'out.csv', 'text': 'a,b\n1,2\n'})
            f = os.path.join(tmp, 'data', 'db', 'tones', '00123.json')
            self.assertEqual(json.load(open(f)), {'tone': 'Negative'})
            self.assertEqual(len(os.listdir(os.path.join(tmp, 'data', 'db', '_deleted', 'views'))), 1)
        finally:
            srv.shutdown(); srv.server_close(); shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
