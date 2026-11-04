"""A15: Windows briefly holds just-written files, so a rename or replace fails with PermissionError 13 "Access is denied". One shared wait-and-retry
(fs_retry.py, reached as station.common.retry_busy) is used for every replace/rename/move. These tests fake a busy file on Linux.
    python3 -I -m unittest discover -s work/localapp/app/tests -p test_retry_busy.py -v
"""
import json
import os
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
for d in (REPO / 'work/saver/src', REPO / 'work/localapp/updatefolder', REPO / 'work/localapp/app/src/station', REPO / 'work/localapp/server'):
    sys.path.insert(0, str(d))
import common as C  # noqa: E402
import fs_retry as FR  # noqa: E402
import refresh as R  # noqa: E402
import rename_files as RF  # noqa: E402


class Busy:
    """make os.replace / os.rename fail with PermissionError for the first n calls; no real waiting"""

    def __init__(self, n, kind=PermissionError):
        self.n, self.kind, self.calls, self.slept = n, kind, 0, []

    def __enter__(self):
        self.real = (os.replace, os.rename, FR._sleep)
        real_replace, real_rename = self.real[0], self.real[1]

        def wrap(real):
            def f(*a, **k):
                self.calls += 1
                if self.calls <= self.n:
                    raise self.kind(13, 'Access is denied')
                return real(*a, **k)
            return f
        os.replace, os.rename, FR._sleep = wrap(real_replace), wrap(real_rename), self.slept.append
        return self

    def __exit__(self, *a):
        os.replace, os.rename, FR._sleep = self.real


class RetryHelper(unittest.TestCase):
    def test_copies_are_identical(self):
        a = (REPO / 'work/saver/src/fs_retry.py').read_bytes()
        self.assertEqual(a, (REPO / 'work/localapp/updatefolder/fs_retry.py').read_bytes())

    def test_waits_then_succeeds(self):
        n = []

        def f():
            n.append(1)
            if len(n) < 4:
                raise PermissionError(13, 'Access is denied')
            return 'ok'
        slept = []
        old, FR._sleep = FR._sleep, slept.append
        try:
            self.assertEqual(FR.retry_busy(f), 'ok')
        finally:
            FR._sleep = old
        self.assertEqual(len(n), 4)
        self.assertEqual(len(slept), 3)

    def test_gives_up_after_about_ten_seconds(self):
        slept = []
        old, FR._sleep = FR._sleep, slept.append
        try:
            with self.assertRaises(PermissionError):
                FR.retry_busy(lambda: (_ for _ in ()).throw(PermissionError(13, 'x')))
        finally:
            FR._sleep = old
        self.assertEqual(len(slept), FR.TRIES - 1)
        self.assertTrue(9 <= sum(slept) <= 13, sum(slept))

    def test_only_permission_errors_are_retried(self):
        n = []
        with self.assertRaises(FileNotFoundError):
            FR.retry_busy(lambda: n.append(1) or (_ for _ in ()).throw(FileNotFoundError('gone')))
        with self.assertRaises(OSError):
            FR.retry_busy(lambda: n.append(1) or (_ for _ in ()).throw(OSError(5, 'disk')))
        self.assertEqual(len(n), 2)

    def test_station_reaches_it(self):
        self.assertIs(C.retry_busy, FR.retry_busy)


class Paths(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.d = Path(self.t.name)

    def tearDown(self):
        self.t.cleanup()

    def test_atomic_write(self):
        with Busy(3) as b:
            C.atomic_write(self.d / 'a.json', b'hello')
        self.assertEqual((self.d / 'a.json').read_bytes(), b'hello')
        self.assertEqual(b.calls, 4)

    def test_atomic_write_gives_permission_error_when_still_busy(self):
        with Busy(99):
            with self.assertRaises(PermissionError):
                C.atomic_write(self.d / 'a.json', b'x')
        self.assertFalse((self.d / 'a.json').exists())

    def test_rename_step(self):
        lib = self.d / 'lib'
        (lib / '2026').mkdir(parents=True)
        (lib / '2026' / 'old1.html').write_text('1')
        (lib / '2026' / 'old2.html').write_text('2')
        lay = types.SimpleNamespace(library=lib)
        pl = {'renames': [{'old': 'old1.html', 'new': 'new1.html', 'year': '2026'}, {'old': 'old2.html', 'new': 'new2.html', 'year': '2026'}]}
        with Busy(5) as b:        # the first five moves fail once-ish; each is retried
            RF.move_files(lay, pl, self.d / 'journal.json')
        self.assertEqual(sorted(p.name for p in (lib / '2026').iterdir()), ['new1.html', 'new2.html'])
        self.assertEqual(json.loads((self.d / 'journal.json').read_text())[0]['state'], 'done')
        self.assertGreater(b.calls, 5)

    def test_refresh_extract(self):
        z = self.d / 'r.zip'
        import hashlib
        body = b'abc' * 100
        with zipfile.ZipFile(z, 'w') as zf:
            zf.writestr('x/file.bin', body)
        with zipfile.ZipFile(z) as zf:
            with Busy(3) as b:
                R._extract(zf, zf.getinfo('x/file.bin'), self.d / 'out' / 'file.bin', hashlib.sha256(body).hexdigest())
        self.assertEqual((self.d / 'out' / 'file.bin').read_bytes(), body)
        self.assertGreaterEqual(b.calls, 4)

    def test_move_into_kept_folder(self):
        f = self.d / 'a.html'
        f.write_text('x')
        (self.d / 'kept').mkdir()
        import shutil
        real = shutil.move

        def flaky(src, dst):
            flaky.n += 1
            if flaky.n < 3:
                raise PermissionError(13, 'Access is denied')
            return real(src, dst)
        flaky.n = 0
        shutil.move = flaky
        old, FR._sleep = FR._sleep, lambda s: None
        try:
            C.move_file(f, self.d / 'kept' / 'a.html')
        finally:
            shutil.move, FR._sleep = real, old
        self.assertTrue((self.d / 'kept' / 'a.html').is_file())
        self.assertFalse(f.exists())

    def test_server_store(self):
        import server as SRV
        db = SRV.Store(str(self.d / 'db'))
        old, SRV.time.sleep = SRV.time.sleep, lambda s: None
        try:
            with Busy(3) as b:
                db.set('notes', 'n1', {'a': 1})
                self.assertEqual(b.calls, 4)
            with Busy(2):
                self.assertTrue(db.delete('notes', 'n1'))
        finally:
            SRV.time.sleep = old
        self.assertFalse(db.counts().get('notes'))


if __name__ == '__main__':
    unittest.main()
