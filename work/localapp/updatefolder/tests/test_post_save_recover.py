"""REVIEW_2 finding 5: a kill between replacing the pipeline state files and rewriting PIPELINE.sha256 is repaired on the next start."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
UF = HERE.parent
LOCALAPP = UF.parent
for p in (UF, LOCALAPP.parent.parent / 'work' / 'saver' / 'src', LOCALAPP / 'server', LOCALAPP / 'app' / 'src' / 'station'):
    sys.path.insert(0, str(p))

import post_save as PS          # noqa: E402
import refresh as RF            # noqa: E402
from layout import PCLayout     # noqa: E402


class Killed(BaseException):
    pass


def make(root):
    lay = PCLayout(root)
    lay.pipeline.mkdir(parents=True)
    (lay.pipeline / 'outlets.json').write_text('{"old": 1}')
    (lay.pipeline / 'release_texts.json').write_text('{"old": 2}')
    (lay.pipeline / 'sheet_task.py').write_text('# code')
    PS.write_pipeline_sha(lay.pipeline)
    out = root / 'saver_out'
    (out / 'pipeline').mkdir(parents=True)
    (out / 'pipeline' / 'outlets.json').write_text('{"new": 1}')
    (out / 'pipeline' / 'release_texts.json').write_text('{"new": 2}')
    res = {'out_dir': str(out), 'publish': {'pipeline_files': {
        'outlets.json': {'changed': True, 'path': str(out / 'pipeline' / 'outlets.json')},
        'release_texts.json': {'changed': True, 'path': str(out / 'pipeline' / 'release_texts.json')}}}}
    return lay, res


def matches(lay):
    return (lay.pipeline / 'PIPELINE.sha256').read_text(encoding='utf-8') == PS._sha_text(lay.pipeline)


class Recover(unittest.TestCase):
    def test_normal_sync_leaves_a_consistent_list_and_no_marker(self):
        lay, res = make(Path(tempfile.mkdtemp()))
        rep = PS.sync(lay, res)
        self.assertEqual(rep['errors'], [])
        self.assertTrue(matches(lay))
        self.assertFalse((lay.state / PS.PENDING).exists())
        self.assertIn('new', (lay.pipeline / 'outlets.json').read_text())
        self.assertIsNone(PS.recover(lay))

    def test_a_kill_between_the_files_and_the_list_is_repaired(self):
        lay, res = make(Path(tempfile.mkdtemp()))
        real = PS.write_pipeline_sha

        def die(pipe):
            raise Killed()
        PS.write_pipeline_sha = die
        try:
            with self.assertRaises(Killed):
                PS.sync(lay, res)
        finally:
            PS.write_pipeline_sha = real
        self.assertFalse(matches(lay), 'the half-done state must exist for this test to mean anything')
        note = PS.recover(lay)
        self.assertTrue(matches(lay))
        self.assertEqual(sorted(note['recovered']), ['outlets.json', 'release_texts.json'])
        self.assertEqual(json.loads((lay.pipeline / 'outlets.json').read_text()), {'old': 1})
        self.assertFalse((lay.state / PS.PENDING).exists())
        # the new copies are kept aside, nothing deleted
        self.assertTrue(list((lay.state / 'pipeline_replaced').glob('*-recovered/outlets.json')))

    def test_a_kill_after_the_list_is_written_keeps_the_new_files(self):
        lay, res = make(Path(tempfile.mkdtemp()))
        PS.sync(lay, res)
        # put the marker back as if the process died right after the list was written
        (lay.state / PS.PENDING).write_text(json.dumps({'stamp': 'x'}))
        PS.recover(lay)
        self.assertIn('new', (lay.pipeline / 'outlets.json').read_text())
        self.assertTrue(matches(lay))
        self.assertFalse((lay.state / PS.PENDING).exists())


class ReaderBackups(unittest.TestCase):
    def test_keeps_the_newest_three_and_moves_the_rest(self):
        lay = PCLayout(Path(tempfile.mkdtemp()))
        lay.backups.mkdir(parents=True)
        wb = lay.workbook
        names = [f'{wb.stem} BACKUP before refresh {n} 2026-11-0{n} 1000.xlsx' for n in range(1, 6)]
        for n in names + ['somebody-else.xlsx']:
            (lay.backups / n).write_bytes(b'x')
        moved = RF.trim_refresh_backups(lay, wb)
        self.assertEqual(sorted(moved), sorted(names[:2]))
        self.assertTrue(all((lay.backups / '_to_delete' / n).is_file() for n in names[:2]))
        self.assertTrue(all((lay.backups / n).is_file() for n in names[2:] + ['somebody-else.xlsx']))


if __name__ == '__main__':
    unittest.main()
