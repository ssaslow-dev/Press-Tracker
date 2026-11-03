"""Tests for `saver.py` init / confirm / preview that do not need a full pipeline run (the full run is tests/replay.py).
The pipeline folder is a copy of the runsave fixture's, or of the repository's code/ folder when the fixture is absent (needed for PIPELINE.sha256
and for sheet_task --check-only). SAVER_FIXTURE=<folder> points at the fixture.
SAVER_SLOW=1 also runs the tamper test (a full preview of the runsave fixture, about two minutes).

    python3 -I -m unittest discover -s L/work/saver/tests -t L/work/saver/tests"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAVER_DIR = HERE.parent
SRC = SAVER_DIR / 'src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))
import saver as SV          # noqa: E402
import saver_steps as ST    # noqa: E402
from wbhelp import make_wb, base_sheets, fixture_dir, have_fixture, pipeline_source, SKIP_NO_FIXTURE   # noqa: E402

FIXTURE = fixture_dir()     # SAVER_FIXTURE, else <repo>/../runsave (not in this repository)
SAVER = SRC / 'saver.py'
TMP = tempfile.TemporaryDirectory()
ROOT = Path(TMP.name)
PIPE = ROOT / 'pipeline'


def setUpModule():
    shutil.copytree(pipeline_source(), PIPE, ignore=shutil.ignore_patterns('docs', '__pycache__', '*.pyc'))
    subprocess.run([sys.executable, '-I', str(SAVER_DIR / 'tools' / 'pipeline_sha.py'), str(PIPE)], check=True, capture_output=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cli(*args, env=None):
    e = dict(os.environ, **(env or {}))
    p = subprocess.run([sys.executable, '-I', str(SAVER), *map(str, args)], capture_output=True, text=True, encoding='utf-8', env=e)
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {'raw': p.stdout, 'err': p.stderr}
    return p.returncode, res


class Env:
    """a throwaway master + state + folders; run docs optional"""
    n = 0

    def __init__(self, runs=None, seed=True):
        Env.n += 1
        self.d = ROOT / f'env{Env.n}'
        self.d.mkdir()
        self.master = make_wb(self.d / 'AJG Coverage - NewsBank.xlsx', base_sheets(), {})
        self.state = self.d / 'state'
        self.db = self.d / 'db'
        (self.db / 'runs').mkdir(parents=True)
        for rid, doc in (runs or {}).items():
            (self.db / 'runs' / f'{rid}.json').write_text(json.dumps(doc), encoding='utf-8')
        for d in ('copies', 'library', 'backups'):
            (self.d / d).mkdir()
        self.out = self.d / 'out'
        if seed:
            self.init(sha(self.master))

    def init(self, s):
        return cli('init', '--workbook', self.master, '--state', self.state, '--sha', s)

    def preview(self, *extra, env=None, pipeline=None, out=None):
        return cli('preview', '--workbook', self.master, '--db', self.db, '--pipeline', pipeline or PIPE, '--copies', self.d / 'copies',
                   '--library', self.d / 'library', '--backups', self.d / 'backups', '--out', out or self.out, '--state', self.state,
                   '--today', '2026-10-30', *extra, env=env)


class Ledger(unittest.TestCase):
    def test_init_confirm_chain(self):
        e = Env(seed=False)
        code, res = e.init(sha(e.master))
        self.assertEqual((code, res['ok']), (0, True))
        entries = SV.read_ledger(e.state)
        self.assertEqual([x['verb'] for x in entries], ['init'])
        self.assertTrue(entries[0]['confirmed'] and entries[0]['matches_file'])
        # a save entry is unconfirmed until confirm with the same sha
        SV.append_ledger(e.state, {'verb': 'save', 'after_sha': 'a' * 64, 'confirmed': False})
        code, res = cli('confirm', '--state', e.state, '--sha', 'b' * 64)
        self.assertEqual(code, 2)
        code, res = cli('confirm', '--state', e.state, '--sha', 'a' * 64)
        self.assertEqual((code, res['ok']), (0, True))
        self.assertEqual([x['verb'] for x in SV.read_ledger(e.state)], ['init', 'save', 'confirm'])
        self.assertEqual(cli('confirm', '--state', e.state, '--sha', 'a' * 64)[0], 2)   # nothing left to confirm

    def test_init_rejects_a_bad_sha(self):
        e = Env(seed=False)
        self.assertEqual(e.init('xyz')[0], 4)


class Refusals(unittest.TestCase):
    def test_no_ledger(self):
        e = Env(seed=False)
        code, res = e.preview()
        self.assertEqual((code, res['refusal']['code']), (2, 'NO_LEDGER'))
        self.assertTrue(res['line'].startswith('Not written: '))

    def test_sha_mismatch_and_accepting_it_with_init(self):
        e = Env()
        with open(e.master, 'ab') as f:
            f.write(b'x')   # an edit or a sync replaced the file
        code, res = e.preview()
        self.assertEqual((code, res['refusal']['code']), (2, 'SHA_MISMATCH'))
        self.assertIn(sha(e.master)[:8], res['line'])
        e.init(sha(e.master))   # Sammy's answer 2: accept the current file as the baseline
        code, res = e.preview(out=e.d / 'out2')
        self.assertNotEqual(res.get('refusal', {}) and res['refusal']['code'], 'SHA_MISMATCH')

    def test_unconfirmed_previous(self):
        e = Env()
        SV.append_ledger(e.state, {'verb': 'save', 'after_sha': sha(e.master), 'confirmed': False})
        code, res = e.preview()
        self.assertEqual((code, res['refusal']['code']), (2, 'UNCONFIRMED_PREVIOUS'))
        cli('confirm', '--state', e.state, '--sha', sha(e.master))
        code, res = e.preview(out=e.d / 'out2')
        self.assertNotEqual(res.get('refusal') and res['refusal']['code'], 'UNCONFIRMED_PREVIOUS')

    def test_excel_lock_file(self):
        e = Env()
        (e.d / '~$AJG Coverage - NewsBank.xlsx').write_bytes(b'owner')
        code, res = e.preview()
        self.assertEqual((code, res['refusal']['code']), (2, 'EXCEL_OPEN'))
        self.assertEqual(res['line'], 'Not written: the workbook is open in Excel. Close it and ask me to save again.')

    def test_excel_permission_denied_simulated(self):
        e = Env()
        code, res = e.preview(env={'SAVER_TEST_EXCEL_OPEN': '1'})
        self.assertEqual((code, res['refusal']['code']), (2, 'EXCEL_OPEN'))

    def test_fresh_lock_refuses_and_is_not_removed(self):
        e = Env()
        e.state.mkdir(exist_ok=True)
        lock = e.state / 'saver.lock'
        lock.write_text(json.dumps({'pid': 1, 'run': 'run-x', 'at': SV.iso(SV.utc_now()), 'host': 'h'}))
        code, res = e.preview()
        self.assertEqual((code, res['refusal']['code']), (2, 'LOCKED'))
        self.assertTrue(lock.exists())

    def test_stale_lock_is_moved_not_deleted(self):
        e = Env()
        lock = e.state / 'saver.lock'
        old = SV.utc_now() - SV.dt.timedelta(minutes=31)
        lock.write_text(json.dumps({'pid': 1, 'run': 'run-x', 'at': SV.iso(old), 'host': 'h'}))
        code, res = e.preview()
        self.assertNotEqual(res.get('refusal') and res['refusal']['code'], 'LOCKED')
        self.assertTrue(list((e.state / 'logs').glob('stale.lock.*')))
        self.assertFalse(lock.exists())                        # released at the end of the run
        self.assertTrue(list((e.state / 'logs').glob('lock.*')))   # moved, never deleted

    def test_library_lock_from_the_manual_procedure(self):
        e = Env()
        (e.d / 'library' / '.sheet_task.lock').write_text(f'run-old {SV.iso(SV.utc_now())}')
        code, res = e.preview()
        self.assertEqual((code, res['refusal']['code']), (2, 'LOCKED'))
        self.assertTrue((e.d / 'library' / '.sheet_task.lock').exists())   # preview does not touch it

    def test_two_acquires_one_wins(self):
        e = Env()
        a, b = SV.ProcessLock(e.state, 'r1'), SV.ProcessLock(e.state, 'r2')
        a.acquire()
        with self.assertRaises(SV.Refuse) as cm:
            b.acquire()
        self.assertEqual(cm.exception.code, 'LOCKED')
        a.release()
        b.acquire()
        b.release()

    def test_pipeline_mismatch_changed_missing_and_no_list(self):
        e = Env()
        for kind in ('changed', 'missing', 'nolist'):
            p = ROOT / f'pipe_{kind}_{e.d.name}'
            shutil.copytree(PIPE, p)
            if kind == 'changed':
                (p / 'relcopy.py').write_bytes((p / 'relcopy.py').read_bytes() + b'\n# tampered\n')
            elif kind == 'missing':
                (p / 'relmatch.py').unlink()
            else:
                (p / 'PIPELINE.sha256').unlink()
            code, res = e.preview(pipeline=p, out=e.d / f'out_{kind}')
            self.assertEqual((code, res['refusal']['code']), (2, 'PIPELINE_MISMATCH'), kind)

    def test_out_not_empty_is_refused_and_untouched(self):
        e = Env()
        e.out.mkdir()
        (e.out / 'keep.txt').write_text('x')
        code, res = e.preview()
        self.assertEqual(code, 4)
        self.assertEqual([p.name for p in e.out.iterdir()], ['keep.txt'])

    def test_today_in_the_future_is_refused(self):
        e = Env()
        code, res = cli('preview', '--workbook', e.master, '--db', e.db, '--pipeline', PIPE, '--copies', e.d / 'copies', '--library',
                        e.d / 'library', '--backups', e.d / 'backups', '--out', e.out, '--state', e.state, '--today', '2999-01-01')
        self.assertEqual(code, 4)
        self.assertIn('later than today', res['line'])

    def test_missing_inputs_are_bad_args(self):
        e = Env()
        shutil.rmtree(e.d / 'copies')
        self.assertEqual(e.preview()[0], 4)

    # test_save_is_not_built was retired when `save` was built; its checks (exit code, no backup, no write) live in test_saver_save.py


class NothingQueued(unittest.TestCase):
    def test_exit_3_without_refresh_and_nothing_written(self):
        e = Env()
        before = sha(e.master)
        code, res = e.preview()
        self.assertEqual(code, 3, res)
        self.assertEqual(res['line'], 'Nothing new to write.')
        self.assertTrue(res['nothing_queued'])
        self.assertEqual(sha(e.master), before)
        self.assertEqual(list((e.d / 'backups').iterdir()), [])
        self.assertTrue(list((e.state / 'logs').glob('lock.*')))   # lock released by a move


class Helpers(unittest.TestCase):
    def fns(self):
        return ST.load_pure_functions(PIPE / 'sheet_task.py')

    def test_filter_db_holds_back_a_release_that_needs_a_fetch(self):
        runs = {'run-a': {'at': '2026-10-30T00:00:00Z', 'rows': [{'x': 1}], 'releases_new': [
            {'url': 'https://r/1', 'title': 'no page'}, {'url': 'https://r/2', 'title': 'has html', 'html': '<p>x</p>'},
            {'url': 'https://r/3', 'title': 'has text', 'text': 'x'}]},
            'run-done': {'sheet': {'at': 'x', 'written': True}, 'releases_new': [{'url': 'https://r/9', 'title': 'old'}]}}
        e = Env(runs=runs)
        work = e.d / 'w'
        work.mkdir()
        args, needs = SV.filter_db(e.db, work, self.fns()['sheet_applied'])
        self.assertEqual(args, ['--db-dir', 'db_in', '--db', 'db.json'])
        self.assertEqual(needs, [{'run': 'run-a', 'url': 'https://r/1', 'title': 'no page'}])
        kept = json.loads((work / 'db_in' / 'runs' / 'run-a.json').read_text())
        self.assertEqual([x['url'] for x in kept['releases_new']], ['https://r/2', 'https://r/3'])
        orig = json.loads((e.db / 'runs' / 'run-a.json').read_text())
        self.assertEqual(len(orig['releases_new']), 3)     # the input is never modified
        done = json.loads((work / 'db_in' / 'runs' / 'run-done.json').read_text())
        self.assertEqual(len(done['releases_new']), 1)     # an applied run is left alone

    def test_filter_db_single_file(self):
        e = Env()
        f = e.d / 'db.json'
        f.write_text(json.dumps({'runs': {'r': {'rows': [1], 'releases_new': [{'url': 'https://r/1', 'title': 't'}]}}}))
        work = e.d / 'w2'
        work.mkdir()
        args, needs = SV.filter_db(f, work, self.fns()['sheet_applied'])
        self.assertEqual(args, ['--db', 'db.json'])
        self.assertEqual(len(needs), 1)
        self.assertEqual(json.loads((work / 'db.json').read_text())['runs']['r']['releases_new'], [])

    def test_pick_run_newest_undone(self):
        db = {'runs': {'a': {'at': '2026-10-01', 'rows': [1]}, 'b': {'at': '2026-10-03', 'rows': [1]},
                       'c': {'at': '2026-10-05', 'rows': [1], 'sheet': {'at': 'x', 'written': True}}, 'd': {'at': '2026-10-06'},
                       'e': {'at': '2026-10-04', 'rows': [1], 'sheet': {'at': 'x', 'written': False, 'line': 'Not written: x'}}}}
        self.assertEqual(SV.pick_run(db, None, self.fns()), 'e')
        self.assertEqual(SV.pick_run(db, 'a', self.fns()), 'a')
        with self.assertRaises(SV.Refuse):
            SV.pick_run(db, 'zzz', self.fns())

    def test_shard_check_ignores_years_the_tracker_has_no_articles_for(self):
        e = Env()
        arts = e.d / 'copies' / 'articles'
        arts.mkdir()
        (arts / 'manifest.json').write_text(json.dumps({'articles': {'s1': 'articles/2026.json', 's2': 'articles/2020.json'}}))
        (arts / '2026.json').write_text('{}')
        needed = ['articles/manifest.json', 'articles/2026.json', 'articles/2020.json', 'articles/2028.json']
        self.assertEqual(SV.shard_check(e.d, needed, e.d / 'copies'), ['articles/2020.json'])
        (arts / 'manifest.json').unlink()
        self.assertEqual(SV.shard_check(e.d, needed, e.d / 'copies'), ['articles/manifest.json'])

    def test_constants_come_from_sheet_task_source(self):
        c = ST.read_sheet_task_constants(PIPE / 'sheet_task.py')
        self.assertIn('Related count', c['VT_DERIVED_REL'])
        self.assertIn('Press releases', c['VT_NEW_OK'])

    def test_constants_resolve_a_named_string_constant(self):
        # PRINTPAGES-v1 (PC patch 24): VT_NEW_OK names PRINT_TAB, a module-level string
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / 'sheet_task.py'
            f.write_text("PRINT_TAB = 'Unlinked print pages'\nVT_DERIVED_REL = {'Related count'}\nVT_NEW_OK = {'Press releases', PRINT_TAB}\n", encoding='utf-8')
            c = ST.read_sheet_task_constants(f)
            self.assertEqual(c['VT_NEW_OK'], {'Press releases', 'Unlinked print pages'})
            f.write_text("VT_DERIVED_REL = {'Related count'}\nVT_NEW_OK = {'Press releases', SOMETHING_ELSE()}\n", encoding='utf-8')
            with self.assertRaises(ValueError):
                ST.read_sheet_task_constants(f)

    def test_offline_env_points_every_proxy_at_a_dead_port(self):
        env = ST.offline_env()
        self.assertTrue(all(env[k] == ST.DEAD_PROXY for k in ST.PROXY_VARS))
        self.assertNotIn('NO_PROXY', env)

    def test_relmatch_args_leave_out_empty_lists(self):
        self.assertIsNone(ST.relmatch_args({'relmatch': {'releases': [], 'stories': []}}))
        a = ST.relmatch_args({'relmatch': {'releases': [], 'stories': ['s1', 's2']}})
        self.assertNotIn('--releases', a)
        self.assertEqual(a[a.index('--stories') + 1], 's1,s2')
        b = ST.relmatch_args({'relmatch': {'releases': ['pr1'], 'stories': []}})
        self.assertNotIn('--stories', b)

    def test_pass1_args_are_the_prompts(self):
        a = ST.pass1_args(today='2026-10-30', queue='queue')
        for flag in ('--db', '--xlsx', '--out', '--result', '--pages-dir', '--copies', '--copies-out', '--img-cache', '--bills',
                     '--release-texts', '--release-related', '--queue', '--lookup-cache', '--lookup-cache-out', '--today'):
            self.assertIn(flag, a)
        self.assertNotIn('--idmap', a)
        self.assertNotIn('--library', a)

    def test_merge_copies_out_goes_into_copies_articles(self):
        e = Env()
        (e.d / 'copies_out' / 'articles').mkdir(parents=True)
        (e.d / 'copies_out' / 'articles' / '2026.json').write_text('new')
        (e.d / 'copies' / 'articles').mkdir()
        (e.d / 'copies' / 'articles' / '2026.json').write_text('old')
        self.assertEqual(ST.merge_copies_out(e.d), ['2026.json'])
        self.assertEqual((e.d / 'copies' / 'articles' / '2026.json').read_text(), 'new')
        self.assertFalse((e.d / 'copies' / 'articles' / 'articles').exists())


@unittest.skipUnless(os.environ.get('SAVER_SLOW') == '1', 'set SAVER_SLOW=1 (a full preview of the runsave fixture, about two minutes)')
@unittest.skipUnless(have_fixture(), SKIP_NO_FIXTURE)
class Slow(unittest.TestCase):
    def test_tampered_output_is_refused_as_overwrite(self):
        sys.path.insert(0, str(HERE))
        import replay
        work = Path(tempfile.mkdtemp(dir=ROOT))
        master = replay.prepare(FIXTURE, work / 'w')
        w = work / 'w'
        cli('init', '--workbook', master, '--state', w / 'state', '--sha', sha(master))
        args = ['preview', '--workbook', master, '--db', w / 'db', '--queue', w / 'queue', '--pipeline', w / 'pipeline', '--copies',
                w / 'copies', '--library', w / 'library', '--backups', w / 'backups', '--out', w / 'out', '--state', w / 'state',
                '--today', '2026-10-30', '--img-cache', w / 'img_cache_in']
        p = subprocess.run([sys.executable, '-I', str(HERE / 'tamper_driver.py'), 'Coverage|2|Headline|Tampered headline', *map(str, args)],
                           capture_output=True, text=True, encoding='utf-8')
        code, res = p.returncode, json.loads(p.stdout.strip().splitlines()[-1])
        self.assertEqual((code, res['refusal']['code']), (2, 'OVERWRITE'), res)
        self.assertIn('Headline', res['refusal']['line'])
        self.assertTrue((w / 'out' / 'diff.tsv').exists())


if __name__ == '__main__':
    unittest.main()
