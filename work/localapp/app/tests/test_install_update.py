"""A16: install a new version over an existing tracker folder without touching data\\ (station/install_update.py).
    AJG_TEST_BUILD=<linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_install_update.py -v
Source = a copy of the build without data\\ whose app code has one changed file; target = a working copy with data (hard links, the library is never written).
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
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

    def test_path_with_spaces_split_into_pieces(self):
        """A dragged-in folder whose path has a space can reach the installer split in two (seen on the office PC, 2026-11-05)."""
        spaced = self.tgt.parent.parent / 'old dir' / 'AJG Tracker'
        spaced.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(self.tgt), str(spaced))
        a, b = str(spaced).split(' ', 1)
        out = self.run_iu(a, b, '--check')
        self.assertNotIn('Give the folder', str(out or ''), out)
        out = self.run_iu('"' + str(spaced) + '"', '--check')
        self.assertNotIn('Give the folder', str(out or ''), out)

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
            if Path(a) == self.tgt / 'python':                 # python\ stays held: the app\ moves worked, undo them
                raise PermissionError(13, 'Access is denied')
            return real(a, b)
        self.iu.FR.rename = flaky
        try:
            r = self.run_iu(self.tgt)
        finally:
            self.iu.FR.rename = real
        self.assertIn('Windows would not let go', str(r))
        self.assertIn('(python', str(r))                        # says which folder was held
        self.assertGreater(len(n), 20)                          # it waited (many tries) before giving up
        self.assertEqual(sha(self.tgt / 'app/station/common.py'), old)      # old program back
        self.assertTrue((self.tgt / 'python').exists())
        self.assertEqual(fingerprint(self.tgt / 'data'), self.data0)
        self.assertEqual([p.name for p in self.tgt.iterdir() if '.new-' in p.name], [])

    def test_held_folder_released_later_is_waited_out(self):
        real = self.iu.FR.rename
        n = []

        def slow(a, b):
            if Path(a) == self.tgt / 'app' and len(n) < 5:      # held for a while (virus scan), then let go
                n.append(1)
                raise PermissionError(13, 'Access is denied')
            return real(a, b)
        self.iu.FR.rename = slow
        try:
            r = self.run_iu(self.tgt)
        finally:
            self.iu.FR.rename = real
        self.assertEqual(r, 0)
        self.assertEqual(fingerprint(self.tgt / 'data'), self.data0)

    def test_windows_vs_mac_refused(self):
        shutil.rmtree(self.src / 'python', ignore_errors=True) if False else None
        (self.tgt / 'python').rename(self.tgt / 'python-arm64')
        self.assertIn('different computers', str(self.run_iu(self.tgt)))


class InstallOverVersion1Layout(unittest.TestCase):
    """Version 3 installed straight over a version-1 tracker: no installer files in the old folder, a finished switch-over in data\\, two hand-replaced station files,
    and precompiled .pyc files that do not check their source (unchecked-hash). The old app\\ and python\\ are moved away as a whole, so a stale .pyc cannot shadow
    the new code, and the new app\\ ships no .pyc of its own for the program parts."""

    def setUp(self):
        shutil.rmtree(BASE, ignore_errors=True)
        BASE.mkdir(parents=True)
        self.src = make_source(BASE / 'new' / 'AJG Tracker', 'NEW-VERSION')
        self.tgt = BASE / 'v1' / 'AJG Tracker'
        self.tgt.parent.mkdir(parents=True)
        shutil.copytree(T.BUILD, self.tgt, symlinks=True, copy_function=os.link)
        for rel in ('Install update.cmd', 'Install update.command', 'app/station/install_update.py', 'app/APP_FILES.sha256', 'app/station/selfcheck.py'):
            (self.tgt / rel).unlink(missing_ok=True)          # a version-1 folder has no installer
        for d in ('workbook', 'state', 'db'):
            (self.tgt / 'data' / d).mkdir(parents=True, exist_ok=True)
        for rel, content in (('data/workbook/AJG Coverage - NewsBank.xlsx', b'workbook-bytes' * 50), ('data/state/switchover.json', json.dumps({'finished_at': '2026-11-03T12:00:00'}).encode()),
                             ('data/state/ledger.jsonl', b'{"verb": "init"}\n')):
            p = self.tgt / rel
            p.unlink(missing_ok=True)       # the copy is made of hard links: never write into a file that is also the build's
            p.write_bytes(content)
        for rel in ('app/station/station_cli.py', 'app/station/rename_files.py'):      # the two hand-replaced files
            p = self.tgt / rel
            b = p.read_bytes()
            p.unlink()
            p.write_bytes(b + b'\n# HAND-REPLACED\n')
        shutil.rmtree(self.tgt / 'app' / 'station' / '__pycache__', ignore_errors=True)       # deleted by hand, as on his PC
        import py_compile
        self.stale = []
        for d in ('server', 'saver', 'updatefolder', 'station'):
            folder = self.tgt / 'app' / d
            src = folder / ('common.py' if d == 'station' else next(p.name for p in sorted(folder.glob('*.py'))))
            tmp = BASE / f'stale_{d}.py'
            tmp.write_text('STALE_PYC = True\n')
            pyc = folder / '__pycache__' / (src.stem + '.cpython-%d%d.pyc' % sys.version_info[:2])
            pyc.parent.mkdir(exist_ok=True)
            py_compile.compile(str(tmp), cfile=str(pyc), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
            self.stale.append((folder, src.stem))
        self.iu = load_iu()
        self.iu.SRC = self.src
        self.iu.FR._sleep = lambda s: None
        self.data0 = fingerprint(self.tgt / 'data')

    def tearDown(self):
        shutil.rmtree(BASE, ignore_errors=True)

    def stale_wins(self, root, folder_rel, mod):
        """True when importing `mod` from that folder picks the stale precompiled copy (a marker only the stale file has)"""
        code = f"import sys; sys.path.insert(0, {str(root / folder_rel)!r}); import {mod}; print(hasattr({mod}, 'STALE_PYC'))"
        r = subprocess.run([str(root / 'python' / 'bin' / 'python'), '-B', '-I', '-c', code], capture_output=True, text=True, cwd=root)
        return r.stdout.strip() == 'True'

    def test_stale_pyc_cannot_shadow_the_new_code(self):
        for folder, mod in self.stale:                                  # the trap is real: before the install the stale copy wins
            self.assertTrue(self.stale_wins(self.tgt, folder.relative_to(self.tgt), mod), str(folder))
        r = self.iu.main([str(self.tgt)])
        self.assertEqual(r, 0)
        for folder, mod in self.stale:
            self.assertFalse(self.stale_wins(self.tgt, folder.relative_to(self.tgt), mod), str(folder))
        self.assertTrue((self.tgt / 'app/station/common.py').read_text().rstrip().endswith('# NEW-VERSION'))
        self.assertNotIn('HAND-REPLACED', (self.tgt / 'app/station/station_cli.py').read_text())
        self.assertNotIn('HAND-REPLACED', (self.tgt / 'app/station/rename_files.py').read_text())
        for d in ('server', 'saver', 'updatefolder', 'station', 'pipeline'):
            self.assertEqual(list((self.tgt / 'app' / d).rglob('*.pyc')), [], d + ' ships no precompiled copies of its own')
        pv = next((self.tgt / '_previous_version').iterdir())
        self.assertTrue(any((pv / 'app' / 'server' / '__pycache__').glob('*.pyc')), 'the old precompiled copies are kept with the old program, not deleted')
        self.assertTrue((pv / 'app' / 'station' / 'station_cli.py').read_text().endswith('# HAND-REPLACED\n'))

    def test_data_untouched_and_installer_files_arrive(self):
        self.assertEqual(self.iu.main([str(self.tgt)]), 0)
        self.assertEqual(fingerprint(self.tgt / 'data'), self.data0)
        self.assertTrue((self.tgt / 'app/station/install_update.py').is_file())
        self.assertTrue((self.tgt / 'app/APP_FILES.sha256').is_file())
        self.assertEqual(json.loads((self.tgt / 'data/state/switchover.json').read_text())['finished_at'], '2026-11-03T12:00:00')


if __name__ == '__main__':
    unittest.main()
