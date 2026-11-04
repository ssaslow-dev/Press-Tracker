"""REVIEW_3 (checkpoint 3, round 3): failing tests for the findings on the Switch-over changes screen and the rename step.

    python3 -I -m unittest discover -s work/localapp/app/tests/review3 -t work/localapp/app/tests/review3 -p test_review3_switchover.py -v

  RenameUndo   : an error AFTER the workbook swap (here: the step's log file cannot be written) makes rename_step put the library files back
                 under their OLD names while the workbook already holds the NEW names (switchover.rename_step catches every Exception and undoes)
  StaleBackup  : the screen's ONE backup is reused in a later session although the workbook changed since (a save, an accepted Excel edit):
                 the step's ledger entry names a backup whose content is not the workbook the step started from
  Journal      : the rename journal on disk says 'planned' for every move until all are done, so after a crash mid-way (power loss, the black
                 window closed) nothing records which files are at .rnN names; there is no recovery step either
  LastUpdated  : LASTUPDATED-v1 counts "a switch-over change", but the rename and the row-changing data-fix steps are not in UPDATE_VERBS
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support3 as T   # noqa: E402

TMP = tempfile.TemporaryDirectory()
S = {}


def setUpModule():
    S['root'] = T.make_root(Path(TMP.name))
    S['C'], S['RF'], S['SW'], S['TU'] = T.load_modules(S['root'])
    S['lay'] = S['C'].layout(S['root'])


def tearDownModule():
    TMP.cleanup()


def init_fn(note):
    return S['TU'].init_baseline(S['lay'], note=note)['exit_code']


def rows_two_stale():
    """two Original rows whose saved copies carry the Reprint letter (stale after a swap), plus one correct Reprint"""
    return [T.row(**{'Article ID': '00001', 'Story ID': 's00001', 'Original or reprint': 'Original', 'Date': '2026-03-01', 'Year': 2026, 'Outlet': 'Paper A',
                     'Headline': 'Story one', 'File name': 'ws00001r-s00001.html', 'Saved Copy?': 'Yes', 'Language': 'English', 'Press release': 'No'}),
            T.row(**{'Article ID': '00002', 'Story ID': 's00002', 'Original or reprint': 'Original', 'Date': '2026-03-02', 'Year': 2026, 'Outlet': 'Paper B',
                     'Headline': 'Story two', 'File name': 'nb00002r-s00002.pdf', 'Saved Copy?': 'Yes', 'Language': 'English', 'Press release': 'No'}),
            T.row(**{'Article ID': '00003', 'Story ID': 's00001', 'Original or reprint': 'Reprint', 'Date': '2026-03-03', 'Year': 2026, 'Outlet': 'Paper C',
                     'Headline': 'Story one', 'File name': 'ws00003r-s00001.html', 'Saved Copy?': 'Yes', 'Language': 'English', 'Press release': 'No'})]


def files_two_stale():
    return {'2026/ws00001r-s00001.html': '<p>one</p>', '_original_html/2026/ws00001r-s00001.html': '<p>raw one</p>',
            '2026/nb00002r-s00002.pdf': '%PDF-1.4 two', '2026/nb00002r-s00002.ocr.txt': 'ocr two',
            '2026/ws00003r-s00001.html': '<p>three</p>', '_original_html/2026/ws00003r-s00001.html': '<p>raw three</p>'}


class RenameUndo(unittest.TestCase):
    def test_an_error_after_the_swap_leaves_workbook_and_library_agreeing(self):
        C, RF, SW, lay = S['C'], S['RF'], S['SW'], S['lay']
        wb = T.fresh_data(S['root'], rows_two_stale(), files_two_stale())
        self.assertEqual(init_fn('review3'), 0)
        pl = RF.plan(lay)
        self.assertEqual(pl['n'], 2, pl['lines'])
        # the step's own log cannot be written (state/logs is not a folder: a stand-in for a full disk or a permission problem at that moment)
        (lay.state / 'logs').write_text('not a folder', encoding='utf-8')
        try:
            SW.rename_step(lay, pl, init_fn, why='review3')
        except Exception:      # noqa: BLE001  (the step reports the error; what matters is what it leaves behind)
            pass
        cov = RF.read_rows(wb)['Coverage'][1]
        cells = {str(d['Article ID']): str(d.get('File name') or '') for _, d in cov}
        listing = T.library_listing(lay.library)
        led = [e['verb'] for e in T.ledger(S['root'])]
        # whatever happened, the workbook's File name cells and the library must agree
        for aid, name in cells.items():
            self.assertIn(f'2026/{name}', listing, {'aid': aid, 'cell': name, 'library': listing, 'ledger': led})


class StaleBackup(unittest.TestCase):
    def test_a_backup_from_an_earlier_session_is_not_reused_after_the_workbook_changed(self):
        import openpyxl
        C, SW, lay = S['C'], S['SW'], S['lay']
        wb = T.fresh_data(S['root'], rows_two_stale(), {})
        self.assertEqual(init_fn('review3'), 0)
        first = SW._make_backup(lay)                     # the screen's one backup, made in a first session (e.g. before "Do only this one")
        self.assertTrue(first.is_file())
        # a save (or an accepted Excel edit) changes the workbook between the sessions
        book = openpyxl.load_workbook(wb)
        book['Coverage'].append(T.row(**{'Article ID': '00009', 'Story ID': 's00009', 'Original or reprint': 'Original', 'Date': '2026-04-01', 'Year': 2026,
                                          'Outlet': 'Paper Z', 'Headline': 'A story saved later', 'Press release': 'No'}))
        book.save(wb)
        book.close()
        self.assertEqual(init_fn('a save happened'), 0)
        sha_before_step = T.sha(wb)
        pv = SW.preview_all(lay)
        self.assertFalse(pv['blocked'], pv['blocked'])
        st = {s['id']: s for s in pv['steps']}
        self.assertEqual(st['other_files']['state'], 'todo')
        r = SW.apply_steps(lay, ['other_files'], {'other_files': st['other_files']['digest']}, init_fn)
        self.assertTrue(r['ok'], r)
        entry = next(e for e in reversed(T.ledger(S['root'])) if e.get('verb') == 'add_other_files_column')
        self.assertEqual(entry['before_sha'], sha_before_step)
        bk = lay.backups / entry['backup']
        self.assertEqual(T.sha(bk), entry['before_sha'], 'the ledger names a backup that is not the workbook this step started from: '
                         f'{entry["backup"]} holds {T.sha(bk)[:8]}, the step started from {sha_before_step[:8]} (row 00009 is only in the latter)')


class Journal(unittest.TestCase):
    def test_the_journal_on_disk_records_every_move_as_it_happens(self):
        RF, lay = S['RF'], S['lay']
        T.fresh_data(S['root'], rows_two_stale(), files_two_stale())
        self.assertEqual(init_fn('review3'), 0)
        pl = RF.plan(lay)
        self.assertEqual(pl['n'], 2)
        jpath = lay.state / 'rename_journal_review3.json'
        real = os.rename
        calls = {'n': 0}

        def cut_off(src, dst):
            calls['n'] += 1
            if calls['n'] == 3:            # the process dies after two moves (power loss, the black window closed)
                raise KeyboardInterrupt
            return real(src, dst)
        RF.os.rename = cut_off
        try:
            with self.assertRaises(KeyboardInterrupt):
                RF.move_files(lay, pl, jpath)
        finally:
            RF.os.rename = real
        on_disk = json.loads(jpath.read_text(encoding='utf-8'))
        moved = [j for j in on_disk if j['state'] != 'planned']
        stray = [p for p in T.library_listing(lay.library) if '.rn' in p]
        self.assertTrue(stray, 'two files are sitting under temporary .rnN names')
        self.assertEqual(len(moved), 2, f'the journal must say which moves happened so they can be finished or undone; it says {[j["state"] for j in on_disk]} '
                         f'while the library holds {stray}')


class LastUpdated(unittest.TestCase):
    def test_every_switchover_step_counts_as_an_update(self):
        C = S['C']
        state = Path(TMP.name) / 'lu_state'
        shutil.rmtree(state, ignore_errors=True)
        state.mkdir()
        for verb in ('rename_files', 'datafix_structural'):
            (state / 'ledger.jsonl').write_text(json.dumps({'at': '2026-11-04T20:00:00+00:00', 'verb': verb, 'before_sha': 'a' * 64, 'after_sha': 'b' * 64, 'confirmed': True}) + '\n'
                                                + json.dumps({'at': '2026-11-04T20:00:01+00:00', 'verb': 'init', 'after_sha': 'b' * 64, 'confirmed': True}) + '\n', encoding='utf-8')
            self.assertEqual(C.last_updated(state), '2026-11-04', f'a {verb} step changed the workbook on 2026-11-04 (Pacific) but "Last updated" shows {C.last_updated(state)!r}')


if __name__ == '__main__':
    unittest.main()
