"""Independent review tests for the save path (REVIEW_2.md, checkpoint 3). A FAILING test here is a finding.

Run:  cd work/saver && python3 -I -m unittest discover -s tests/review2 -t tests/review2 -v

The end-to-end cases reuse the main suite's harness (tests/test_saver_save.py: a one-row mini workbook, the example database and the
repository's code/ folder with build_data.py and relmatch.py stubbed), so a case takes the time of one or two sheet_task runs."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = HERE.parent
SRC = TESTS.parent / 'src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(TESTS))

import saver as SV                     # noqa: E402
import test_saver_save as TS           # noqa: E402  (harness only; its TestCases are not collected from here)


def setUpModule():
    TS.setUpModule()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cells(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        return {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}
    finally:
        wb.close()


class Killed(BaseException):
    """a process kill (closing the tracker's black window, a power cut): no except-clause of the program runs"""


# ---------------------------------------------------------------- the library step


class LibraryPaths(unittest.TestCase):
    def test_a_removed_file_path_cannot_leave_the_library(self):
        """CLAUDE.md hard rules: files only inside the app folder; the library is add-only and moves go to _to_delete/ only.
        The paths of a removed story's files come from the workbook's File name cells (sheet_task.execute_removals builds
        '<year>/<File name>'). A cell holding '..' makes commit_library move a file from OUTSIDE the library into it."""
        d = Path(tempfile.mkdtemp())
        lib = d / 'lib'
        (lib / '2026').mkdir(parents=True)
        outside = d / 'outside.html'
        outside.write_text('a file that is not the library\'s')
        job = {'lib': lib, 'run': 'r', 'today': '2026-11-03', 'pages': [], 'pages_dir': d / 'pages',
               'removed_files': [{'aid': '10001', 'files': ['2026/../../outside.html'], 'originals': []}]}
        out = SV.commit_library(job)
        self.assertTrue(outside.is_file(), 'a file outside the library was moved')
        self.assertFalse((lib / 'outside.html').exists())
        self.assertEqual(out['removed_moved'], [])
        self.assertTrue(out['removed_failed'] or out['removed_missing'], 'a path that leaves the library must be listed, not followed')

    def test_a_page_path_cannot_leave_the_library(self):
        """same rule for the pages a run adds: a relative path with '..' must never be written outside the library"""
        d = Path(tempfile.mkdtemp())
        lib = d / 'lib'
        lib.mkdir()
        pages = d / 'pages'
        (pages / '2026').mkdir(parents=True)
        (pages / '2026' / 'x.html').write_text('x')
        job = {'lib': lib, 'run': 'r', 'today': '2026-11-03', 'pages': ['2026/../../escaped.html'], 'pages_dir': pages,
               'removed_files': []}
        # the source does not exist under that name, so the copy fails either way; the point is where the target would be
        out = SV.commit_library(job)
        self.assertFalse((d / 'escaped.html').exists())
        self.assertEqual(out['pages_added'], [])


# ---------------------------------------------------------------- what the ledger holds when the save dies after the swap


class CommitOrder(unittest.TestCase):
    """SAVE_RULES step 6 / SPEC step 13 and saver.py's own comment at the ledger append: the ledger entry is written 'right after the
    master is verified, so a crash in the library step cannot leave it unrecorded'. In the code the library step (commit_library) runs
    INSIDE commit(), before commit() returns and before append_ledger. A kill or an unexpected exception while the library files are
    being copied leaves the master replaced and the ledger still naming the old checksum. The next preview then refuses SHA_MISMATCH,
    the panel offers 'Accept the workbook as it is now', and the update (still in staging, not in the ledger, not in the local db, not in
    updates/done) can be taken in a second time."""

    def ns(self, e, *extra):
        out = e.out()
        return SV.build_parser().parse_args([str(x) for x in e.args('save', out)] + ['--no-rebuild', '--master-is-local', *extra])

    def test_a_kill_during_the_library_step_leaves_the_master_recorded(self):
        e = TS.Env()
        before = sha(e.master)
        real = SV.commit_library

        def die(job):
            raise Killed()
        SV.commit_library = die
        try:
            with self.assertRaises(Killed):
                SV.cmd_save(self.ns(e))
        finally:
            SV.commit_library = real
        self.assertNotEqual(sha(e.master), before, 'the master was replaced before the library step')
        led = SV.read_ledger(e.state)[-1]
        self.assertEqual((led.get('verb'), led.get('after_sha')), ('save', sha(e.master)),
                         'the ledger must name the new master before the library step runs')

    def test_an_unexpected_error_in_the_library_step_still_reports_the_master_as_written(self):
        """commit_library catches OSError only. Any other exception there escapes commit() before `committed` is set: cmd_save then
        answers 'Not written: unexpected error' (exit 4, written False) although the master is already the new file, and writes no
        ledger entry."""
        e = TS.Env()
        before = sha(e.master)
        real = SV.commit_library

        def boom(job):
            raise RuntimeError('simulated: not an OSError')
        SV.commit_library = boom
        a = self.ns(e)
        try:
            code = SV.cmd_save(a)
        finally:
            SV.commit_library = real
        res = json.loads(Path(a.json or Path(a.out) / 'saver_result.json').read_text(encoding='utf-8'))
        self.assertNotEqual(sha(e.master), before, 'the master was replaced')
        self.assertTrue(res.get('written'), f'the result must say the master was written (exit {code}): {res.get("line")}')
        led = SV.read_ledger(e.state)[-1]
        self.assertEqual((led.get('verb'), led.get('after_sha')), ('save', sha(e.master)))


# ---------------------------------------------------------------- reusing a preview: what is committed must be what the diff saw


class ReuseTamper(unittest.TestCase):
    """SAVE_RULES 'What preview shows' / SAVER_SPEC section 6: a save commits the cell changes the independent diff allowed, and
    `save --token` refuses unless its own fresh diff gives the same token. With --from-preview the diff is not run again: the staged
    workbook is trusted on the strength of preview_state.json (after_sha) and the kept diff.tsv (token). Both live in the preview
    folder. An edit of the staged workbook that also updates after_sha in preview_state.json keeps the token valid, so a filled cell
    changed after the preview reaches the master without any diff having seen it."""

    def test_a_consistently_edited_staged_workbook_is_not_committed(self):
        e = TS.Env()
        out1 = e.out()
        code, pv = TS.cli(*e.args('preview', out1))
        self.assertEqual(code, 0, pv)
        token = pv['diff']['token']
        staged = [p for p in out1.iterdir() if p.name.startswith(TS.MASTER[:-5] + ' SAVED')][0]
        # overwrite a FILLED cell of the staged workbook (the diff never allowed this), then make the preview's own record agree
        import openpyxl
        wb = openpyxl.load_workbook(staged)
        ws = wb['Coverage']
        hdr = [c.value for c in ws[1]]
        col = hdr.index('Headline') + 1
        self.assertEqual(ws.cell(2, col).value, 'Old story')
        ws.cell(2, col).value = 'TAMPERED'
        wb.save(staged)
        sf = out1 / 'preview_state.json'
        st = json.loads(sf.read_text(encoding='utf-8'))
        st['ctx']['after_sha'] = sha(staged)
        st['res']['workbook']['after_sha'] = sha(staged)
        sf.write_text(json.dumps(st), encoding='utf-8')
        out2 = e.out()
        code, res = TS.cli(*e.args('save', out2), '--no-rebuild', '--master-is-local', '--token', token, '--from-preview', out1)
        head = cells(e.master)['Coverage']
        heads = [r[hdr.index('Headline')] for r in head[1:]]
        self.assertNotIn('TAMPERED', heads, f'a changed filled cell reached the master through --from-preview (exit {code}, {res.get("line")})')
        if code == 0 and res.get('written'):
            self.assertNotIn('reused_preview', res, 'a preview whose staged workbook no longer matches its diff must not be reused')


if __name__ == '__main__':
    unittest.main()
