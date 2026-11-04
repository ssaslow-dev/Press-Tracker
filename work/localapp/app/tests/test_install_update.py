"""A16: install a new version over an existing tracker folder without touching data\\ (station/install_update.py).
    AJG_TEST_BUILD=<linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_install_update.py -v
Source = a copy of the build without data\\ whose app code has one changed file; target = a working copy with data (hard links, the library is never written).
"""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402

REPO = HERE.parents[3]
BASE = T.SCRATCH / 'app_build' / 'test_install_update'


def load_iu():
    sys.path.insert(0, str(REPO / 'work/saver/src'))
    spec = importlib.util.spec_from_file_location('install_update_t', REPO / 'work/localapp/app/src/station/install_update.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fingerprint(root: Path):
    return sorted((str(p.relative_to(root)), p.stat().st_size) for p in root.rglob('*') if p.is_file())


def make_source(dst: Path, marker: str):
    shutil.copytree(T.BUILD, dst, symlinks=True, copy_function=os.link)
    shutil.rmtree(dst / 'data')
    f = dst / 'app' / 'station' / 'common.py'
    t = f.read_bytes()
    f.unlink()
    f.write_bytes(t + f'\n# {marker}\n'.encode())
    lst = dst / 'app' / 'APP_FILES.sha256'
    lines = []
    for ln in lst.read_text(encoding='utf-8').splitlines():
        h, _, rel = ln.partition('  ')
        lines.append(f'{sha(dst / rel)}  {rel}' if rel == 'app/station/common.py' else ln)
    lst.unlink()
    lst.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    for name in ('Install update.cmd', 'READ ME FIRST.txt'):
        pass
    return dst


class Install(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(BASE, ignore_errors=True)
        BASE.mkdir(parents=True)
        self.src = make_source(BASE / 'new' / 'AJG Tracker', 'NEW-VERSION')
        self.tgt = T.make_work(BASE, 'old', 'keeper')
        self.iu = load_iu()
        self.iu.SRC = self.src
        self.iu.FR._sleep = lambda s: None
        self.data0 = fingerprint(self.tgt / 'data')

    def tearDown(self):
        shutil.rmtree(BASE, ignore_errors=True)

    def run_iu(self, target, *extra):
        try:
            return self.iu.main([str(target), *extra])
        except self.iu.Stop as e:
            return str(e)

    def test_check_changes_nothing(self):
        before = fingerprint(self.tgt) if False else sha(self.tgt / 'app/station/common.py')
        self.assertEqual(self.run_iu(self.tgt, '--check'), 0)
        self.assertEqual(sha(self.tgt / 'app/station/common.py'), before)
        self.assertFalse((self.tgt / '_previous_version').exists())

    def test_install(self):
        old = sha(self.tgt / 'app/station/common.py')
        self.assertEqual(self.run_iu(f'"{self.tgt}"'), 0)         # quotes (drag and drop) are accepted
        self.assertTrue((self.tgt / 'app/station/common.py').read_text().rstrip().endswith('# NEW-VERSION'))
        self.assertEqual(fingerprint(self.tgt / 'data'), self.data0)       # data\ exactly as before
        pv = list((self.tgt / '_previous_version').iterdir())
        self.assertEqual(len(pv), 1)
        self.assertEqual(sha(pv[0] / 'app/station/common.py'), old)           # the old program is kept
        self.assertTrue((pv[0] / 'python').exists())
        self.assertEqual(json.loads((pv[0] / 'update.json').read_text())['data_files'], len(self.data0))
        self.assertEqual([p.name for p in self.tgt.iterdir() if '.new-' in p.name or '.failed-' in p.name], [])
        self.assertTrue((self.tgt / 'data' / 'role.json').is_file())

    def test_tampered_source_refused(self):
        (self.src / 'app/station/plain.py').unlink()
        (self.src / 'app/station/plain.py').write_text('x = 1\n')
        r = self.run_iu(self.tgt)
        self.assertIn('do not match', str(r))
        self.assertFalse((self.tgt / '_previous_version').exists())

    def test_refusals(self):
        self.assertIn('new folder itself', str(self.run_iu(self.src)))
        self.assertIn('not there', str(self.run_iu(BASE / 'nope')))
        (self.tgt / 'data' / 'state').mkdir(parents=True, exist_ok=True)
        (self.tgt / 'data' / 'state' / 'app.lock').write_text('{}')
        self.assertIn('busy', str(self.run_iu(self.tgt)))
        (self.tgt / 'data' / 'state' / 'app.lock').unlink()
        other = BASE / 'plain'
        (other / 'data').mkdir(parents=True)
        self.assertIn('does not look like', str(self.run_iu(other)))
        self.assertFalse((self.tgt / '_previous_version').exists())

    def test_busy_old_program_rolls_back(self):
        old = sha(self.tgt / 'app/station/common.py')
        real = self.iu.FR.rename
        n = []

        def flaky(a, b):
            n.append(1)
            if len(n) == 3:                                     # python\ cannot be moved: the first two moves worked, undo them
                raise PermissionError(13, 'Access is denied')
            return real(a, b)
        self.iu.FR.rename = flaky
        try:
            r = self.run_iu(self.tgt)
        finally:
            self.iu.FR.rename = real
        self.assertIn('Windows would not let go', str(r))
        self.assertEqual(sha(self.tgt / 'app/station/common.py'), old)      # old program back
        self.assertTrue((self.tgt / 'python').exists())
        self.assertEqual(fingerprint(self.tgt / 'data'), self.data0)
        self.assertEqual([p.name for p in self.tgt.iterdir() if '.new-' in p.name], [])

    def test_windows_vs_mac_refused(self):
        shutil.rmtree(self.src / 'python', ignore_errors=True) if False else None
        (self.tgt / 'python').rename(self.tgt / 'python-arm64')
        self.assertIn('different computers', str(self.run_iu(self.tgt)))


if __name__ == '__main__':
    unittest.main()
