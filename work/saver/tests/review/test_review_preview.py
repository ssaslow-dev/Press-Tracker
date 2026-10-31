"""Independent review tests for saver.py's refusal checks (REVIEW_1.md). A FAILING test here is a finding.

Run:  cd L/work/saver && python3 -I -m unittest discover -s tests/review -t tests/review -v
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent / 'src'
sys.path.insert(0, str(SRC))

import saver as SV   # noqa: E402


class LockOwnership(unittest.TestCase):
    def test_stale_lock_holder_does_not_release_the_new_holders_lock(self):
        """SAVE_RULES line 19 / SPEC 4: one save at a time. A holds the lock; its stamp ages past 30 minutes (a long pass 1 does not
        refresh it). B moves A's lock aside and takes its own. When A finishes, A.release() moves *B's* lock file to logs: B is now
        running unlocked and a third invocation C is admitted while B still runs."""
        d = Path(tempfile.mkdtemp())
        a, b, c = SV.ProcessLock(d, 'A'), SV.ProcessLock(d, 'B'), SV.ProcessLock(d, 'C')
        a.acquire()
        old = SV.utc_now() - SV.dt.timedelta(minutes=31)
        a.path.write_text(json.dumps({'pid': 1, 'run': 'A', 'at': SV.iso(old), 'host': 'h'}), encoding='utf-8')
        b.acquire()                                  # moves A's stale lock aside, takes its own
        self.assertTrue(b.path.exists())
        a.release()                                  # A thinks it still holds the lock
        self.assertTrue(b.path.exists(), "A's release moved B's lock away")
        with self.assertRaises(SV.Refuse):
            c.acquire()                              # must still be LOCKED while B runs
        b.release()

    def test_lock_at_in_the_future_is_still_honoured(self):
        d = Path(tempfile.mkdtemp())
        a = SV.ProcessLock(d, 'A')
        a.path.parent.mkdir(exist_ok=True)
        future = SV.utc_now() + SV.dt.timedelta(minutes=5)
        a.path.write_text(json.dumps({'pid': 1, 'run': 'X', 'at': SV.iso(future), 'host': 'h'}), encoding='utf-8')
        with self.assertRaises(SV.Refuse):
            a.acquire()

    def test_unreadable_lock_file_is_judged_by_mtime(self):
        d = Path(tempfile.mkdtemp())
        a = SV.ProcessLock(d, 'A')
        a.path.parent.mkdir(exist_ok=True)
        a.path.write_text('not json', encoding='utf-8')     # fresh mtime
        with self.assertRaises(SV.Refuse) as cm:
            a.acquire()
        self.assertEqual(cm.exception.code, 'LOCKED')


class NoHiddenWriteHooks(unittest.TestCase):
    def test_no_environment_hook_edits_the_output_before_the_diff(self):
        """SAVER_TEST_TAMPER lets an environment variable write a cell into the pass-2 output before the diff. A blank-cell target
        is an allowed fill, so in the save path the injected value would reach the master. Test hooks that change data belong in
        the tests, not in the program."""
        src = (SRC / 'saver.py').read_text(encoding='utf-8')
        body = src[src.index('def run_preview'):src.index('def cmd_preview')]
        self.assertNotRegex(body, r"os\.environ\.get\('SAVER_TEST_TAMPER'\)", 'run_preview alters the output on an env var')


class ExcelDetection(unittest.TestCase):
    def test_excel_owner_file_name_rule(self):
        """Excel's owner file is '~$' + name for names of 8+ characters; for shorter names Excel replaces the first one or two characters.
        The master's name is long, so '~$' + name is right for it; recorded here so a renamed short master is not assumed covered."""
        self.assertEqual(SV.check_excel.__code__.co_consts.count('~$'), 1)


class Dates(unittest.TestCase):
    def test_la_today_fallback_is_pacific_daylight_aware(self):
        """la_today() falls back to UTC-8 when tzdata is missing (Windows without the tzdata package). From March to November Los
        Angeles is UTC-7: between 07:00 and 08:00 UTC the fallback names yesterday, and a correct --today is refused as 'later than today'."""
        import datetime as dt
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo('America/Los_Angeles')
        except Exception:
            self.skipTest('no tzdata here either')
        src = (SRC / 'saver.py').read_text(encoding='utf-8')
        m = re.search(r'timedelta\(hours=(\d+)\)', src[src.index('def la_today'):src.index('def write_json')])
        self.assertIsNotNone(m)
        self.assertNotEqual(m.group(1), '8', 'fixed UTC-8 fallback ignores daylight time')


if __name__ == '__main__':
    unittest.main()
