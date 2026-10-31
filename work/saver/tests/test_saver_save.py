"""Tests for the save path of saver.py (spec section 3 steps 10 to 14). Everything runs in temp folders on copies.

Two layers:
  * Commit  : saver.commit / commit_library / trim_backups / LibLock called directly with synthetic workbooks (tests/wbhelp.py).
  * EndToEnd: `saver.py save` through the CLI with the real sheet_task.py from the repository's code/ folder, a one-row mini workbook and the
    example database. build_data.py and relmatch.py are replaced by stubs in the test's own pipeline copy (the repository's code/ folder lacks
    legacy_index.html and sid_map.json, which build_data.py needs); the pipeline checksum list is regenerated over the copy.

    python3 -I -m unittest discover -s tests -t tests"""
import base64
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAVER_DIR = HERE.parent
SRC = SAVER_DIR / 'src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))
import saver as SV          # noqa: E402
from wbhelp import make_wb, base_sheets, pipeline_source, REPO   # noqa: E402

SAVER = SRC / 'saver.py'
TMP = tempfile.TemporaryDirectory()
ROOT = Path(TMP.name)
PIPE = ROOT / 'pipeline'
PIPE_RB = ROOT / 'pipeline_rb'      # PIPE plus stub rebuild inputs
MASTER = 'AJG Coverage - NewsBank.xlsx'
EXAMPLE_DB = REPO / 'build' / 'tests' / 'sheet_task' / 'fixtures' / 'example_db.json'
MINI = REPO / 'build' / 'tests' / 'sheet_task' / 'audit' / 'mini.py'

STUB_BUILD = ("import sys, os\nos.makedirs(sys.argv[3], exist_ok=True)\n"
              "for n in ('data', 'rows', 'idmap', 'covcols'):\n    open(os.path.join(sys.argv[3], n + '.json'), 'w').write('{}')\n")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pipe_sha(folder):
    subprocess.run([sys.executable, '-I', str(SAVER_DIR / 'tools' / 'pipeline_sha.py'), str(folder)], check=True, capture_output=True)


def setUpModule():
    shutil.copytree(pipeline_source(), PIPE, ignore=shutil.ignore_patterns('docs', '__pycache__', '*.pyc', '_history', 'tracker', 'fetch2',
                                                                          'billstatus', 'fetch_rated1'))
    (PIPE / 'build_data.py').write_text(STUB_BUILD, encoding='utf-8')
    (PIPE / 'relmatch.py').write_text('import sys\n', encoding='utf-8')
    pipe_sha(PIPE)
    shutil.copytree(PIPE, PIPE_RB)
    (PIPE_RB / 'tabs_data.py').write_text('import sys\n', encoding='utf-8')
    (PIPE_RB / 'assemble.py').write_text("import sys\nopen(sys.argv[4], 'w').write('<html>assembled</html>')\n", encoding='utf-8')
    (PIPE_RB / 'shell.html').write_text('<html></html>', encoding='utf-8')
    (PIPE_RB / 'tracker.js').write_text('//', encoding='utf-8')
    (PIPE_RB / 'tabs').mkdir()
    (PIPE_RB / 'tabs' / 'releases.js').write_text('//', encoding='utf-8')
    pipe_sha(PIPE_RB)


def cli(*args, env=None):
    p = subprocess.run([sys.executable, '-I', str(SAVER), *map(str, args)], capture_output=True, text=True, encoding='utf-8',
                       env=dict(os.environ, **(env or {})))
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {'raw': p.stdout, 'err': p.stderr}
    return p.returncode, res


# ---------------------------------------------------------------- commit stage, called directly


class Commit(unittest.TestCase):
    n = 0

    def setUp(self):
        Commit.n += 1
        self.d = ROOT / f'commit{Commit.n}'
        self.d.mkdir()
        self.w = make_wb(self.d / MASTER, base_sheets(), {})
        sheets = base_sheets()
        sheets['Coverage'][1].append(['10004', 'Original', 's00004', 'Headline four', 'Davis', None, 'd.html', 'Yes'])
        (self.d / 'out').mkdir()
        self.out_xlsx = make_wb(self.d / 'out' / 'SAVED x.xlsx', sheets, {})
        self.lib, self.backups, self.state = self.d / 'lib', self.d / 'backups', self.d / 'state'
        self.lib.mkdir()
        self.pages = self.d / 'out' / 'pages'
        (self.pages / '2026').mkdir(parents=True)
        (self.pages / '_original_html' / '2026').mkdir(parents=True)
        (self.pages / '2026' / 'new.html').write_text('<p>new</p>')
        (self.pages / '_original_html' / '2026' / 'new.html').write_text('<p>orig</p>')
        self.before, self.after = sha(self.w), sha(self.out_xlsx)
        SV.append_ledger(self.state, {'verb': 'init', 'after_sha': self.before, 'confirmed': True})
        self.lock = SV.ProcessLock(self.state, 'run-t')
        self.lock.acquire()
        self.addCleanup(self.lock.release)

    def job(self, **kw):
        j = {'w': self.w, 'out_xlsx': self.out_xlsx, 'out_name': 'AJG Coverage - NewsBank SAVED run-t 20261030T000000Z.xlsx',
             'before_sha': self.before, 'after_sha': self.after, 'run': 'run-t', 'today': '2026-10-30', 'lib': self.lib, 'backups': self.backups,
             'pages_dir': self.pages, 'pages': SV.pages_in(self.pages), 'removed_files': []}
        j.update(kw)
        return j

    def test_happy_path(self):
        done = SV.commit(self.job(), self.lock)
        bk = self.backups / done['backup']
        self.assertEqual(sha(bk), self.before)
        self.assertRegex(done['backup'], r'^AJG Coverage - NewsBank BACKUP before run run-t \d{4}-\d\d-\d\d \d{4}\.xlsx$')
        self.assertEqual(sha(self.w), self.after)
        self.assertEqual(sorted(p.name for p in self.d.iterdir()), ['AJG Coverage - NewsBank.xlsx', 'backups', 'lib', 'out', 'state'])   # no staged leftover
        self.assertEqual(done['library']['pages_added'], ['2026/new.html', '_original_html/2026/new.html'])
        self.assertTrue((self.lib / '2026' / 'new.html').is_file())
        self.assertFalse(done['library']['partial'])

    def test_display_folder_is_never_committed(self):
        (self.pages / '_display').mkdir()
        (self.pages / '_display' / 's1.html').write_text('x')
        self.assertNotIn('_display/s1.html', SV.pages_in(self.pages))

    def test_backup_never_overwrites(self):
        old = SV.unique_path(self.backups / 'x.xlsx')   # nothing there: same path
        self.assertEqual(old, self.backups / 'x.xlsx')
        orig = SV.la_stamp
        SV.la_stamp = lambda: '2026-10-30 1000'
        self.addCleanup(setattr, SV, 'la_stamp', orig)
        self.backups.mkdir()
        taken = self.backups / SV.backup_name(self.w, 'run-t')
        taken.write_bytes(b'someone else')
        done = SV.commit(self.job(), self.lock)
        self.assertEqual(taken.read_bytes(), b'someone else')
        self.assertTrue(done['backup'].endswith(' (2).xlsx'))
        self.assertEqual(sha(self.backups / done['backup']), self.before)

    def test_backup_failed_when_copy_differs(self):
        real = shutil.copy2

        def bad(src, dst, *a, **k):
            r = real(src, dst, *a, **k)
            if Path(dst).parent == self.backups:
                with open(dst, 'ab') as f:
                    f.write(b'x')
            return r
        SV.shutil.copy2 = bad
        try:
            with self.assertRaises(SV.Refuse) as cm:
                SV.commit(self.job(), self.lock)
        finally:
            SV.shutil.copy2 = real
        self.assertEqual(cm.exception.code, 'BACKUP_FAILED')
        self.assertEqual(sha(self.w), self.before)           # master untouched
        self.assertEqual(list(self.lib.iterdir()), [])        # library untouched

    def test_commit_failed_after_swap_names_the_backup(self):
        real = os.replace

        def corrupt(src, dst):
            Path(dst).write_bytes(b'garbage')                 # the swap "succeeds" with the wrong bytes
            Path(src).unlink()
        SV.os.replace = corrupt
        try:
            with self.assertRaises(SV.Refuse) as cm:
                SV.commit(self.job(), self.lock)
        finally:
            SV.os.replace = real
        e = cm.exception
        self.assertEqual(e.code, 'COMMIT_FAILED')
        self.assertIn('BACKUP before run run-t', e.msg)
        self.assertEqual(e.detail['master_state'], 'unverified')
        self.assertEqual(sha(next(self.backups.iterdir())), self.before)
        self.assertEqual(list(self.lib.iterdir()), [])        # no library step after a failed swap

    def test_replace_error_leaves_master_alone(self):
        real = os.replace
        SV.os.replace = lambda s, d: (_ for _ in ()).throw(PermissionError('locked'))
        try:
            with self.assertRaises(SV.Refuse) as cm:
                SV.commit(self.job(), self.lock)
        finally:
            SV.os.replace = real
        self.assertEqual(cm.exception.code, 'COMMIT_FAILED')
        self.assertEqual(sha(self.w), self.before)

    def test_master_changed_before_backup_writes_nothing(self):
        with open(self.w, 'ab') as f:
            f.write(b'x')
        with self.assertRaises(SV.Refuse) as cm:
            SV.commit(self.job(), self.lock)
        self.assertEqual(cm.exception.code, 'SHA_MISMATCH')
        self.assertFalse(self.backups.exists() and list(self.backups.iterdir()))

    def test_master_changed_between_backup_and_swap(self):
        real = SV.check_excel

        def touch(w):
            with open(w, 'ab') as f:
                f.write(b'edit')
            real(w)
        SV.check_excel = touch
        try:
            with self.assertRaises(SV.Refuse) as cm:
                SV.commit(self.job(), self.lock)
        finally:
            SV.check_excel = real
        self.assertEqual(cm.exception.code, 'SHA_MISMATCH')
        self.assertNotEqual(sha(self.w), self.after)          # not replaced
        self.assertEqual(len(list(self.backups.iterdir())), 1)   # the already-made backup stays (spec 11)
        self.assertEqual(list(self.lib.iterdir()), [])

    def test_excel_opened_just_before_swap(self):
        real = SV.check_excel

        def open_now(w):
            (w.parent / ('~$' + w.name)).write_bytes(b'x')
            real(w)
        SV.check_excel = open_now
        try:
            with self.assertRaises(SV.Refuse) as cm:
                SV.commit(self.job(), self.lock)
        finally:
            SV.check_excel = real
        self.assertEqual(cm.exception.code, 'EXCEL_OPEN')
        self.assertEqual(sha(self.w), self.before)

    def test_lock_taken_over_refuses_before_the_backup(self):
        self.lock.path.write_text(json.dumps({'pid': 1, 'run': 'other', 'at': SV.iso(SV.utc_now()), 'host': 'h', 'token': 'someone-else'}))
        with self.assertRaises(SV.Refuse) as cm:
            SV.commit(self.job(), self.lock)
        self.assertEqual(cm.exception.code, 'LOCKED')
        self.assertFalse(self.backups.exists() and list(self.backups.iterdir()))
        self.assertEqual(sha(self.w), self.before)

    def test_staged_name_that_exists_is_never_overwritten(self):
        j = self.job()
        (self.d / j['out_name']).write_bytes(b'mine')
        with self.assertRaises(SV.Refuse) as cm:
            SV.commit(j, self.lock)
        self.assertEqual(cm.exception.code, 'COMMIT_FAILED')
        self.assertEqual((self.d / j['out_name']).read_bytes(), b'mine')
        self.assertEqual(sha(self.w), self.before)

    def test_staged_name_equal_to_master_is_refused(self):
        with self.assertRaises(SV.Refuse) as cm:
            SV.commit(self.job(out_name=MASTER), self.lock)
        self.assertEqual(cm.exception.code, 'COMMIT_FAILED')
        self.assertEqual(sha(self.w), self.before)

    # ---- library
    def test_page_name_collision_is_skipped_and_listed(self):
        (self.lib / '2026').mkdir()
        (self.lib / '2026' / 'new.html').write_text('<p>already here</p>')
        done = SV.commit(self.job(), self.lock)['library']
        self.assertEqual(done['pages_collided'], ['2026/new.html'])
        self.assertEqual(done['pages_added'], ['_original_html/2026/new.html'])
        self.assertEqual((self.lib / '2026' / 'new.html').read_text(), '<p>already here</p>')

    def test_removal_is_moved_with_a_moves_line(self):
        for rel in ('2026/a.html', '_original_html/2026/a.html'):
            (self.lib / Path(rel)).parent.mkdir(parents=True, exist_ok=True)
            (self.lib / Path(rel)).write_text('x ' + rel)
        rm = [{'aid': '10001', 'files': ['2026/a.html', '2026/gone.html'], 'originals': ['_original_html/2026/a.html']}]
        lib = SV.commit(self.job(removed_files=rm), self.lock)['library']
        self.assertFalse((self.lib / '2026' / 'a.html').exists())
        self.assertEqual((self.lib / '_to_delete' / '2026' / 'a.html').read_text(), 'x 2026/a.html')
        self.assertEqual((self.lib / '_to_delete' / '_original_html' / '2026' / 'a.html').read_text(), 'x _original_html/2026/a.html')
        self.assertEqual([m['from'] for m in lib['removed_moved']], ['2026/a.html', '_original_html/2026/a.html'])
        self.assertEqual(lib['removed_missing'], [{'aid': '10001', 'file': '2026/gone.html'}])
        lines = (self.lib / '_to_delete' / '_moves_2026-10-30.tsv').read_text().splitlines()
        self.assertEqual(len(lines), 2)
        cols = lines[0].split('\t')
        self.assertEqual(cols[1:], ['run-t', '10001', '2026/a.html', '_to_delete/2026/a.html'])

    def test_move_to_delete_never_overwrites(self):
        (self.lib / '2026').mkdir()
        (self.lib / '2026' / 'a.html').write_text('new copy')
        (self.lib / '_to_delete' / '2026').mkdir(parents=True)
        (self.lib / '_to_delete' / '2026' / 'a.html').write_text('older removal')
        lib = SV.commit(self.job(removed_files=[{'aid': '1', 'files': ['2026/a.html'], 'originals': []}]), self.lock)['library']
        self.assertEqual((self.lib / '_to_delete' / '2026' / 'a.html').read_text(), 'older removal')
        self.assertEqual((self.lib / '_to_delete' / '2026' / 'a (2).html').read_text(), 'new copy')
        self.assertEqual(lib['removed_moved'][0]['to'], '_to_delete/2026/a (2).html')

    def test_library_failure_after_swap_is_partial_not_rolled_back(self):
        (self.pages / '2026' / 'new.html').unlink()          # listed but gone: the copy fails
        j = self.job(pages=['2026/new.html', '_original_html/2026/new.html'])
        done = SV.commit(j, self.lock)
        self.assertTrue(done['library']['partial'])
        self.assertEqual([x['file'] for x in done['library']['pages_failed']], ['2026/new.html'])
        self.assertEqual(done['library']['pages_added'], ['_original_html/2026/new.html'])
        self.assertEqual(sha(self.w), self.after)             # the workbook stays replaced

    # ---- backup retention
    def test_retention_keeps_three_saver_backups_and_moves_older_ones_only(self):
        self.backups.mkdir()
        stamps = ['2026-10-01 0900', '2026-10-02 0900', '2026-10-03 0900', '2026-10-04 0900', '2026-10-05 0900']
        for i, st in enumerate(stamps):
            name = f'AJG Coverage - NewsBank BACKUP before run run-{i} {st}.xlsx'
            (self.backups / name).write_bytes(b'b')
            SV.append_ledger(self.state, {'verb': 'save', 'run': f'run-{i}', 'backup': name, 'after_sha': 'a' * 64, 'confirmed': True})
        manual = 'AJG Coverage - NewsBank BACKUP before run run-manual 2026-09-01 0900.xlsx'   # same naming, made by hand: not in the ledger
        old_style = 'AJG Coverage - NewsBank 1761000000000.xlsx'
        other = 'Other Book BACKUP before run run-z 2026-01-01 0900.xlsx'
        for n in (manual, old_style, other):
            (self.backups / n).write_bytes(b'm')
        moved = SV.trim_backups(self.w, self.backups, self.state)
        self.assertEqual(sorted(moved), sorted(f'AJG Coverage - NewsBank BACKUP before run run-{i} {stamps[i]}.xlsx' for i in (0, 1)))
        left = sorted(p.name for p in self.backups.iterdir() if p.is_file())
        self.assertEqual(len(left), 6)                         # 3 saver backups + the three not made by the saver
        for n in (manual, old_style, other):
            self.assertIn(n, left)
        self.assertEqual(sorted(p.name for p in (self.backups / '_to_delete').iterdir()), sorted(moved))

    def test_retention_runs_only_after_a_successful_save_through_the_cli_flow(self):
        # commit() itself never trims: trimming is cmd_save's job after the master is verified
        self.backups.mkdir()
        for i in range(4):
            n = f'AJG Coverage - NewsBank BACKUP before run run-{i} 2026-10-0{i + 1} 0900.xlsx'
            (self.backups / n).write_bytes(b'b')
            SV.append_ledger(self.state, {'verb': 'save', 'backup': n, 'after_sha': 'a' * 64, 'confirmed': True})
        SV.commit(self.job(), self.lock)
        self.assertEqual(len(list(p for p in self.backups.iterdir() if p.is_file())), 5)

    # ---- library lock
    def test_library_lock_written_and_moved_never_deleted(self):
        ll = SV.LibLock(self.lib, 'run-t')
        ll.write()
        self.assertRegex((self.lib / '.sheet_task.lock').read_text(), r'^run-t \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$')
        ll.release()
        self.assertFalse((self.lib / '.sheet_task.lock').exists())
        self.assertTrue((self.lib / '_to_delete' / '.sheet_task.lock.run-t').is_file())

    def test_library_lock_of_someone_else_is_left_alone(self):
        ll = SV.LibLock(self.lib, 'run-t')
        ll.write()
        (self.lib / '.sheet_task.lock').write_text('run-other 2026-10-30T10:00:00Z')
        ll.release()
        self.assertTrue((self.lib / '.sheet_task.lock').is_file())


# ---------------------------------------------------------------- end to end through the CLI


def load_mini():
    os.environ.setdefault('AUDIT_OUT', str(ROOT / 'aud'))
    spec = importlib.util.spec_from_file_location('mini_wb', MINI)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Env:
    n = 0

    def __init__(self, pipeline=None, db=True, removal=False):
        Env.n += 1
        self.d = ROOT / f'e2e{Env.n}'
        self.d.mkdir()
        mini = load_mini()
        row = {'Article ID': '10001', 'Story ID': 's00001', 'Original or reprint': 'Original', 'Date': '2026-10-01', 'Year': '2026',
               'Outlet': 'Old Gazette', 'Headline': 'Old story', 'Publisher link': 'https://old.example.com/a'}
        if removal:
            row.update({'File name': 'old.html', 'Saved Copy?': 'Yes'})
        self.master = Path(mini.make(str(self.d / MASTER), [mini.row(**row)]))
        self.db = self.d / 'db'
        (self.db / 'runs').mkdir(parents=True)
        if db:
            ex = json.loads(EXAMPLE_DB.read_text(encoding='utf-8'))
            for coll, docs in ex.items():
                if isinstance(docs, dict):
                    (self.db / coll).mkdir(exist_ok=True)
                    for k, v in docs.items():
                        (self.db / coll / f'{k}.json').write_text(json.dumps(v), encoding='utf-8')
        if removal:
            (self.db / 'edits').mkdir(exist_ok=True)
            (self.db / 'edits' / 's00001.json').write_text(json.dumps({'removed': True, 'at': '2026-10-30T10:00:00Z'}))
            (self.d / 'library' / '2026').mkdir(parents=True)
            (self.d / 'library' / '_original_html' / '2026').mkdir(parents=True)
            (self.d / 'library' / '2026' / 'old.html').write_text('<p>old</p>')
            (self.d / 'library' / '_original_html' / '2026' / 'old.html').write_text('<p>orig</p>')
        (self.d / 'library').mkdir(exist_ok=True)
        (self.d / 'copies' / 'articles').mkdir(parents=True)
        (self.d / 'copies' / 'articles' / 'manifest.json').write_text('{"articles":{}}')
        (self.d / 'backups').mkdir()
        self.pipeline = pipeline or PIPE
        self.state = self.d / 'state'
        self.lib, self.backups = self.d / 'library', self.d / 'backups'
        self.n_out = 0
        cli('init', '--workbook', self.master, '--state', self.state, '--sha', sha(self.master))

    def out(self):
        self.n_out += 1
        return self.d / f'out{self.n_out}'

    def args(self, verb, out=None):
        return [verb, '--workbook', self.master, '--db', self.db, '--pipeline', self.pipeline, '--copies', self.d / 'copies', '--library', self.lib,
                '--backups', self.backups, '--out', out or self.out(), '--state', self.state, '--today', '2026-10-30']

    def save(self, *extra, **kw):
        return cli(*self.args('save', kw.get('out')), *extra)

    def untouched(self):
        return not list(self.backups.iterdir()) and not (self.lib / '.sheet_task.lock').exists()


class EndToEnd(unittest.TestCase):
    def test_happy_path_master_is_local(self):
        e = Env()
        before = sha(e.master)
        out = e.out()
        code, res = e.save('--no-rebuild', '--master-is-local', out=out)
        self.assertEqual((code, res['refusal']), (0, None), res)
        self.assertTrue(res['ok'] and res['written'] and res['confirmed'])
        wb = res['workbook']
        self.assertEqual(sha(e.master), wb['after_sha'])
        self.assertNotEqual(wb['after_sha'], before)
        self.assertEqual(sha(e.backups / wb['backup']), before)
        self.assertEqual([p.name for p in e.d.iterdir() if p.suffix == '.xlsx'], [MASTER])      # no staged file left beside the master
        led = SV.read_ledger(e.state)[-1]
        for k in ('at', 'verb', 'run', 'before_sha', 'after_sha', 'backup', 'out_name', 'rows_before', 'rows_after', 'rows_added', 'cells_filled',
                  'confirmed', 'confirmed_at'):
            self.assertIn(k, led)
        self.assertEqual((led['verb'], led['before_sha'], led['after_sha'], led['confirmed']), ('save', before, wb['after_sha'], True))
        self.assertEqual((led['rows_before'], led['rows_after'], led['rows_added']), (1, 3, 2))
        self.assertEqual(led['backup'], wb['backup'])
        # locks: moved, never deleted
        self.assertFalse((e.state / 'saver.lock').exists())
        self.assertTrue(list((e.state / 'logs').glob('lock.run-example1.*')))
        self.assertFalse((e.lib / '.sheet_task.lock').exists())
        self.assertTrue((e.lib / '_to_delete' / '.sheet_task.lock.run-example1').is_file())
        # library, log, outputs
        self.assertEqual(res['library']['pages_added'], ['2026/ws10002o-s04297.html', '_original_html/2026/ws10002o-s04297.html'])
        self.assertTrue((e.lib / '2026' / 'ws10002o-s04297.html').is_file())
        self.assertTrue(Path(res['log']).is_file())
        self.assertTrue((out / 'lookup_cache.out.json').is_file() or res['publish']['lookup_cache_out'] is None)
        wbk = json.loads((out / 'writeback.json').read_text())
        self.assertTrue(wbk['apply_after_confirm'])
        self.assertTrue(wbk['runs']['run-example1']['sheet']['written'])      # `written: true` lives only in the writeback bundle
        self.assertEqual(json.loads((out / 'saver_result.json').read_text())['exit_code'], 0)
        self.assertFalse(res['site_rebuilt'])
        self.assertEqual(res['publish']['pipeline_files']['lookup_cache.json']['changed'] in (True, False), True)

    def test_unconfirmed_until_confirm_then_a_second_save(self):
        e = Env()
        code, res = e.save('--no-rebuild')
        self.assertEqual(code, 0, res)
        self.assertFalse(res['confirmed'])
        led = SV.read_ledger(e.state)[-1]
        self.assertFalse(led['confirmed'])
        self.assertIsNone(led['confirmed_at'])
        # not confirmed where the master lives yet: the next save refuses and writes nothing
        n_backups = len(list(e.backups.iterdir()))
        code, res = e.save('--no-rebuild')
        self.assertEqual((code, res['refusal']['code']), (2, 'UNCONFIRMED_PREVIOUS'))
        self.assertEqual(len(list(e.backups.iterdir())), n_backups)
        self.assertFalse((e.lib / '.sheet_task.lock').exists())          # preview-part refusal wrote no library lock
        code, cres = cli('confirm', '--state', e.state, '--sha', led['after_sha'])
        self.assertEqual(code, 0, cres)
        # the adapter marks the run written (writeback), so the second save has nothing to do
        doc = e.db / 'runs' / 'run-example1.json'
        d = json.loads(doc.read_text())
        d['sheet'] = {'at': 'x', 'written': True, 'line': 'x'}
        doc.write_text(json.dumps(d))
        code, res = e.save('--no-rebuild')
        self.assertEqual((code, res['line']), (3, 'Nothing new to write.'))
        self.assertEqual(len(list(e.backups.iterdir())), n_backups)

    def test_second_save_after_master_is_local_needs_no_confirm(self):
        e = Env()
        self.assertEqual(e.save('--no-rebuild', '--master-is-local')[0], 0)
        code, res = e.save('--no-rebuild')
        self.assertNotIn((res.get('refusal') or {}).get('code'), ('UNCONFIRMED_PREVIOUS', 'SHA_MISMATCH'))

    def test_token_stale_writes_nothing(self):
        e = Env()
        before = sha(e.master)
        code, res = e.save('--no-rebuild', '--token', 'deadbeefdeadbeef')
        self.assertEqual((code, res['refusal']['code']), (2, 'TOKEN_STALE'))
        self.assertTrue(res['line'].startswith('Not written: '))
        self.assertEqual(sha(e.master), before)
        self.assertTrue(e.untouched())
        self.assertFalse((e.state / 'saver.lock').exists())
        self.assertEqual(len(SV.read_ledger(e.state)), 1)

    def test_token_from_preview_is_accepted(self):
        e = Env()
        code, pv = cli(*e.args('preview'))
        self.assertEqual(code, 0, pv)
        code, res = e.save('--no-rebuild', '--token', pv['diff']['token'])
        self.assertEqual((code, res['refusal']), (0, None), res)
        self.assertEqual(res['diff']['rows_added'], pv['diff']['rows_added'])   # same content; the bytes differ (xlsx timestamps), the token is over the diff

    def test_nothing_queued_writes_only_the_nothing_writeback(self):
        e = Env(db=False)
        before = sha(e.master)
        out = e.out()
        code, res = e.save('--no-rebuild', out=out)
        self.assertEqual((code, res['line']), (3, 'Nothing new to write.'))
        self.assertFalse(res['written'])
        self.assertEqual(sha(e.master), before)
        self.assertEqual(list(e.backups.iterdir()), [])
        self.assertEqual(len(SV.read_ledger(e.state)), 1)
        self.assertEqual(json.loads((out / 'writeback.json').read_text())['runs'], {})
        self.assertFalse((e.lib / '.sheet_task.lock').exists())
        self.assertTrue(list((e.state / 'logs').glob('lock.*')))

    def test_excel_open_refuses_before_any_backup(self):
        e = Env()
        (e.d / ('~$' + MASTER)).write_bytes(b'x')
        code, res = e.save('--no-rebuild')
        self.assertEqual((code, res['refusal']['code']), (2, 'EXCEL_OPEN'))
        self.assertTrue(e.untouched())

    def test_removal_moves_files_and_logs_them(self):
        e = Env(db=False, removal=True)
        code, res = e.save('--no-rebuild', '--master-is-local')
        self.assertEqual(code, 0, res)
        self.assertFalse((e.lib / '2026' / 'old.html').exists())
        self.assertEqual((e.lib / '_to_delete' / '2026' / 'old.html').read_text(), '<p>old</p>')
        self.assertEqual((e.lib / '_to_delete' / '_original_html' / '2026' / 'old.html').read_text(), '<p>orig</p>')
        lines = (e.lib / '_to_delete' / '_moves_2026-10-30.tsv').read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue((e.lib / '_to_delete' / '.sheet_task.lock.refresh').is_file())

    def test_rebuild_failure_is_exit_5_and_the_save_stands(self):
        e = Env()    # the repository's code/ folder has no shell.html, tracker.js or tabs/
        code, res = e.save('--master-is-local')
        self.assertEqual(code, 5, res)
        self.assertTrue(res['written'])
        self.assertFalse(res['site_rebuilt'])
        self.assertIn('lacks', res['rebuild_error'])
        self.assertEqual(sha(e.master), res['workbook']['after_sha'])
        self.assertEqual(SV.read_ledger(e.state)[-1]['verb'], 'save')

    def test_rebuild_writes_site_files_under_out_only(self):
        e = Env(pipeline=PIPE_RB)
        out = e.out()
        before_pipe = sha(PIPE_RB / 'PIPELINE.sha256')
        code, res = e.save('--master-is-local', out=out)
        self.assertEqual(code, 0, res)
        self.assertTrue(res['site_rebuilt'])
        self.assertEqual((out / 'site' / 'index.html').read_text(), '<html>assembled</html>')
        sj = json.loads((out / 'site' / 'data' / 'sheet.json').read_text())
        self.assertEqual(sj['filename'], MASTER)
        self.assertEqual(base64.b64decode(sj['b64']), e.master.read_bytes())
        self.assertEqual(sha(PIPE_RB / 'PIPELINE.sha256'), before_pipe)     # --pipeline is never written

    def test_unwritable_result_after_commit_is_exit_6(self):
        e = Env()
        blocker = e.d / 'blocker'
        blocker.write_text('a file, so a result path below it cannot be created')
        code, res = e.save('--no-rebuild', '--master-is-local', '--json', blocker / 'r.json')
        self.assertEqual(code, 6, res)
        self.assertTrue(res['written'])
        self.assertEqual(res['exit_code'], 6)
        self.assertEqual(sha(e.master), res['workbook']['after_sha'])

    def test_save_with_a_changed_master_is_refused(self):
        e = Env()
        with open(e.master, 'ab') as f:
            f.write(b'x')
        code, res = e.save('--no-rebuild')
        self.assertEqual((code, res['refusal']['code']), (2, 'SHA_MISMATCH'))
        self.assertTrue(e.untouched())


if __name__ == '__main__':
    unittest.main()
