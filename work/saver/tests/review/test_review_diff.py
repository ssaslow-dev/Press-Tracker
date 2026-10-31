"""Independent review tests for saver_diff.py (REVIEW_1.md). Each test asserts what SAVE_RULES.md requires; a FAILING test here is a
finding, not a broken test. Do not "fix" these tests to pass; fix the code or record the exception in SAVE_RULES.md.

Run:  cd L/work/saver && python3 -I -m unittest discover -s tests/review -t tests/review -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'src'))
sys.path.insert(0, str(HERE.parent))

import saver_diff as D   # noqa: E402
from wbhelp import make_wb, base_sheets   # noqa: E402

DERIVED = {'Has copies', 'Copies (rows)', 'Related count', 'Related story IDs'}
NEW_OK = {'Press releases', 'Audio & video details', 'Removed'}
T = tempfile.TemporaryDirectory()
N = [0]


def wb(sheets, links=None):
    N[0] += 1
    return make_wb(Path(T.name) / f'r{N[0]}.xlsx', sheets, links or {})


def cmp(before, after, result=None, result2=None):
    return D.compare(before, after, result, result2, derived_rel=DERIVED, new_ok=NEW_OK)


def kinds(rep):
    return sorted({p.kind for p in rep.problems})


def moved_sheets(aid='10002'):
    """base sheets with Coverage/Originals/A&V row `aid` gone and a Removed row for it"""
    s = base_sheets()
    row = next(r for r in s['Coverage'][1] if r[0] == aid)
    s['Coverage'][1] = [r for r in s['Coverage'][1] if r[0] != aid]
    s['Originals'][1] = [r for r in s['Originals'][1] if r[0] != aid]
    s['Audio & video details'][1] = [r for r in s['Audio & video details'][1] if r[0] != aid]
    s['Removed'][1].append([row[0], 'Coverage'])
    return s


class RowIdentity(unittest.TestCase):
    """SAVE_RULES line 23/25: a filled cell may not change; a key row may not go missing."""

    def test_rows_reordered_on_coverage_is_reported(self):
        # Two Coverage rows swap places (and Originals with them, so the mirror check stays quiet). Every filled cell at rows 2 and 3
        # now holds a different value than before; the diff matches by Article ID and reports nothing at all.
        s = base_sheets()
        s['Coverage'][1][0], s['Coverage'][1][1] = s['Coverage'][1][1], s['Coverage'][1][0]
        s['Originals'][1][0], s['Originals'][1][1] = s['Originals'][1][1], s['Originals'][1][0]
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertTrue(rep.problems or rep.changes, 'a reorder of Coverage rows is invisible to the diff')

    def test_duplicate_article_id_one_copy_deleted(self):
        b = base_sheets()
        b['Coverage'][1].append(['10001', 'Reprint', 's00001', 'Duplicate of one', 'Oakland', None, 'd.html', 'Yes'])
        s = base_sheets()    # the duplicate is gone
        rep = cmp(wb(b), wb(s))
        self.assertIn('row_missing', kinds(rep))

    def test_duplicate_article_id_rows_swapped_and_one_edited(self):
        b = base_sheets()
        b['Coverage'][1].append(['10001', 'Reprint', 's00001', 'Duplicate of one', 'Oakland', None, 'd.html', 'Yes'])
        s = base_sheets()
        s['Coverage'][1].insert(0, ['10001', 'Reprint', 's00001', 'Duplicate of one EDITED', 'Oakland', None, 'd.html', 'Yes'])
        rep = cmp(wb(b), wb(s))
        self.assertIn('cell_changed', kinds(rep))

    def test_blank_id_row_overwritten(self):
        b = base_sheets()
        b['Coverage'][1].append([None, 'Reprint', 's00001', 'No id yet', 'Oakland', None, None, None])
        s = base_sheets()
        s['Coverage'][1].append([None, 'Reprint', 's00009', 'Something else', 'Oakland', None, None, None])
        rep = cmp(wb(b), wb(s))
        self.assertIn('cell_changed', kinds(rep))

    def test_blank_id_row_deleted(self):
        b = base_sheets()
        b['Coverage'][1].append([None, 'Reprint', 's00001', 'No id yet', 'Oakland', None, None, None])
        rep = cmp(wb(b), wb(base_sheets()))
        self.assertIn('row_missing', kinds(rep))

    def test_article_id_retyped_int_to_str_still_matches_and_edit_is_seen(self):
        b = base_sheets()
        b['Coverage'][1][0][0] = 10001          # number in the master
        b['Originals'][1][0][0] = 10001
        s = base_sheets()                       # string after, plus an edit
        s['Coverage'][1][0][3] = 'Edited'
        rep = cmp(wb(b), wb(s))
        self.assertIn('cell_changed', kinds(rep))
        self.assertTrue(any(c.key == '10001' and c.column == 'Headline' for c in rep.disallowed()))

    def test_bool_to_number_coercion_is_a_change(self):
        # same() canonicalises and Python's True == 1: a TRUE cell rewritten as 1 is reported as unchanged.
        b = base_sheets()
        b['Coverage'][1][0][7] = True
        b['Originals'][1][0][7] = True
        s = base_sheets()
        s['Coverage'][1][0][7] = 1
        s['Originals'][1][0][7] = 1
        rep = cmp(wb(b), wb(s))
        self.assertIn('cell_changed', kinds(rep), 'TRUE -> 1 passed as identical')

    def test_merge_over_filled_cells_is_a_change(self):
        import openpyxl
        p = wb(base_sheets())
        w2 = openpyxl.load_workbook(str(p))
        w2['Coverage'].merge_cells('D2:E2')      # Headline + Place of row 10001; E2 is blanked by the merge
        q = Path(T.name) / 'merged.xlsx'
        w2.save(str(q))
        rep = cmp(p, q)
        self.assertIn('cell_changed', kinds(rep))


class Hyperlinks(unittest.TestCase):
    """SAVE_RULES line 25: a hyperlink may not go missing."""

    def test_hyperlink_target_rewritten_is_reported(self):
        # The cell keeps its text and keeps *a* hyperlink, but the link now points somewhere else. The diff only counts link presence.
        links_b = {('Coverage', 2, 6): 'https://example.org/a.html'}
        links_a = {('Coverage', 2, 6): 'https://example.org/WRONG.html'}
        rep = cmp(wb(base_sheets(), links_b), wb(base_sheets(), links_a))
        self.assertTrue(rep.problems or rep.changes, 'a hyperlink whose target changed is invisible to the diff')

    def test_hyperlink_of_a_moved_row_must_land_on_removed(self):
        # Row 10002 moves to Removed (allowed) but its Publisher link hyperlink is not carried: the hyperlink is gone from the workbook.
        res = {'removed': [{'story': 's00002', 'rows': [{'aid': '10002'}]}]}
        links_b = {('Coverage', 3, 6): 'https://example.org/b.html'}
        rep = cmp(wb(base_sheets(), links_b), wb(moved_sheets(), {}), res)
        self.assertIn('hyperlink_lost', kinds(rep))

    def test_header_row_hyperlink_lost_is_reported(self):
        links_b = {('Coverage', 1, 6): 'https://example.org/help'}
        rep = cmp(wb(base_sheets(), links_b), wb(base_sheets(), {}))
        self.assertIn('hyperlink_lost', kinds(rep))


class AllowListBreadth(unittest.TestCase):
    """SAVE_RULES line 23: the exceptions are exactly the recorded ones."""

    def test_reprint_count_cleared_is_not_the_recorded_count(self):
        # sheet_task recorded new=3 for s00001; the file has the count *blanked*. SPEC 6: allowed when the value is the recorded one.
        b = base_sheets()
        b['Coverage'][1][0][5] = 2
        b['Originals'][1][0][5] = 2
        s = base_sheets()      # '# of reprints' now None
        res = {'reprint_counts': {'s00001': {'old': 2, 'new': 3}}}
        rep = cmp(wb(b), wb(s), res)
        self.assertIn('cell_changed', kinds(rep), 'clearing a reprint count was allowed as reprint_count')

    def test_new_av_row_with_an_id_sheet_task_did_not_assign(self):
        # SAVE_RULES line 24 is not limited to Coverage: "A new row's Article ID is not one sheet_task.py assigned in this run."
        s = base_sheets()
        s['Audio & video details'][1].append(['77777', 'Smuggled show'])
        rep = cmp(wb(base_sheets()), wb(s), {'runs': {'r': {'ids': {}, 'added': []}}})
        self.assertEqual(rep.refusal() and rep.refusal()[0], 'FOREIGN_ROW')

    def test_new_removed_row_for_an_id_nothing_removed(self):
        # a Removed row appears for an Article ID that is neither in result.removed nor was on any tab before
        s = base_sheets()
        s['Removed'][1].append(['77777', 'Coverage'])
        rep = cmp(wb(base_sheets()), wb(s), {'removed': []})
        self.assertTrue(rep.problems, 'a Removed row with an unknown Article ID was accepted')

    def test_removed_move_needs_a_row_that_landed_this_run(self):
        # 10002 was ALREADY on Removed before (an earlier removal; the story was re-added later). result.removed lists it again, the
        # Coverage row vanishes, nothing new lands on Removed: the current row's content is lost, and the diff calls it a move.
        b = base_sheets()
        b['Removed'][1].append(['10002', 'Coverage'])
        s = moved_sheets()         # Removed has the one old row; Coverage/Originals/A&V rows gone
        res = {'removed': [{'story': 's00002', 'rows': [{'aid': '10002'}]}]}
        rep = cmp(wb(b), wb(s), res)
        self.assertTrue(rep.problems, 'a "move" that added nothing to Removed was accepted')

    def test_blank_fill_on_other_tabs_is_allowed(self):
        # SAVE_RULES: fills are allowed; recorded so the reader knows the diff lets a run fill blanks on every tab (Unlinked print
        # pages here). Not a finding; a boundary the rules accept.
        b = base_sheets()
        b['Unlinked print pages'][1][0][1] = None
        s = base_sheets()
        rep = cmp(wb(b), wb(s))
        self.assertEqual(rep.problems, [])
        self.assertEqual([(c.sheet, c.allowed_by) for c in rep.changes], [('Unlinked print pages', 'blank_fill')])


class Mirrors(unittest.TestCase):
    def test_originals_row_vanishes_while_coverage_still_original(self):
        s = base_sheets()
        s['Originals'][1].pop(1)
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertIn('row_missing', kinds(rep))

    def test_original_demoted_without_a_swap_record(self):
        s = base_sheets()
        s['Coverage'][1][1][1] = 'Reprint'
        s['Originals'][1].pop(1)
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertIn('cell_changed', kinds(rep))

    def test_both_duplicates_vanish_when_result_lists_one(self):
        b = base_sheets()
        b['Coverage'][1].append(['10002', 'Reprint', 's00002', 'Dup two', None, None, None, None])
        s = moved_sheets()
        res = {'removed': [{'story': 's00002', 'rows': [{'aid': '10002'}]}]}
        rep = cmp(wb(b), wb(s), res)
        self.assertTrue(rep.problems)


if __name__ == '__main__':
    unittest.main()
