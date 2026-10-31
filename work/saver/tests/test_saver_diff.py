"""Unit tests for saver_diff.py. Synthetic workbooks only. Run: python3 -I -m unittest discover -s L/work/saver/tests -t L/work/saver/tests"""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'src'))
sys.path.insert(0, str(HERE))

import saver_diff as D   # noqa: E402
from wbhelp import make_wb, base_sheets   # noqa: E402

DERIVED = {'Has copies', 'Copies (rows)', 'Related count', 'Related story IDs'}
NEW_OK = {'Press releases', 'Audio & video details', 'Removed'}
T = tempfile.TemporaryDirectory()
N = [0]


def wb(sheets, links=None):
    N[0] += 1
    return make_wb(Path(T.name) / f'w{N[0]}.xlsx', sheets, links or {})


def cmp(before, after, result=None, result2=None):
    return D.compare(before, after, result, result2, derived_rel=DERIVED, new_ok=NEW_OK)


def codes(rep):
    return sorted({p.kind for p in rep.problems})


def mutate(fn, **kw):
    s = base_sheets()
    fn(s)
    return s


class CellRules(unittest.TestCase):
    def test_identical_is_clean(self):
        a = wb(base_sheets())
        rep = cmp(a, wb(base_sheets()))
        self.assertEqual(rep.problems, [])
        self.assertEqual(rep.changes, [])

    def test_filled_cell_changed_flags(self):
        s = base_sheets()
        s['Coverage'][1][0][3] = 'A different headline'      # row 10001, Headline
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertEqual(codes(rep), ['cell_changed'])
        self.assertEqual(rep.refusal()[0], 'OVERWRITE')
        c = rep.disallowed()[0]
        self.assertEqual((c.sheet, c.key, c.column, c.kind), ('Coverage', '10001', 'Headline', 'changed'))
        self.assertIn('NOT_ALLOWED', c.tsv())

    def test_cleared_cell_flags(self):
        s = base_sheets()
        s['Coverage'][1][0][3] = None
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertEqual(codes(rep), ['cell_changed'])

    def test_blank_fill_allowed(self):
        s = base_sheets()
        s['Coverage'][1][1][4] = 'Los Angeles'               # row 10002, Place was blank
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertEqual(rep.problems, [])
        self.assertEqual([(c.kind, c.allowed_by) for c in rep.changes], [('filled', 'blank_fill')])
        self.assertEqual(rep.summary()['cells_filled'], {'Coverage': 1})

    def test_whitespace_only_before_counts_as_blank(self):
        b = base_sheets()
        b['Coverage'][1][1][4] = '  '
        s = base_sheets()
        s['Coverage'][1][1][4] = 'Fresno'
        rep = cmp(wb(b), wb(s))
        self.assertEqual(rep.problems, [])

    def test_whitespace_edit_of_filled_cell_flags(self):
        s = base_sheets()
        s['Coverage'][1][0][3] = 'Headline one '
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertEqual(codes(rep), ['cell_changed'])

    def test_int_float_equal(self):
        b = base_sheets()
        b['Coverage'][1][0][5] = 3
        s = base_sheets()
        s['Coverage'][1][0][5] = 3.0
        rep = cmp(wb(b), wb(s))
        self.assertEqual(rep.problems, [])

    def test_reprint_count_allowed_for_recorded_story(self):
        b = base_sheets()
        b['Coverage'][1][0][5] = 3
        s = base_sheets()
        s['Coverage'][1][0][5] = 4
        res = {'reprint_counts': {'s00001': {'old': 3, 'new': 4}}}
        rep = cmp(wb(b), wb(s), res)
        self.assertEqual(rep.problems, [])
        self.assertEqual(rep.changes[0].allowed_by, 'reprint_count')
        self.assertEqual(rep.summary()['cells_changed'], {'reprint_count': 1})

    def test_reprint_count_not_allowed_for_other_story_or_wrong_value(self):
        b = base_sheets()
        b['Coverage'][1][0][5] = 3
        s = base_sheets()
        s['Coverage'][1][0][5] = 4
        self.assertEqual(codes(cmp(wb(b), wb(s), {'reprint_counts': {'s00002': {'old': 3, 'new': 4}}})), ['cell_changed'])
        self.assertEqual(codes(cmp(wb(b), wb(s), {'reprint_counts': {'s00001': {'old': 3, 'new': 9}}})), ['cell_changed'])
        self.assertEqual(codes(cmp(wb(b), wb(s), {})), ['cell_changed'])

    def test_reprint_count_column_on_other_column_not_covered(self):
        s = base_sheets()
        s['Coverage'][1][0][3] = 'X'
        res = {'reprint_counts': {'s00001': {'old': 3, 'new': 4}}}
        self.assertEqual(codes(cmp(wb(base_sheets()), wb(s), res)), ['cell_changed'])

    def test_origin_swap_retry_and_queue_cells(self):
        b = base_sheets()
        s = base_sheets()
        s['Coverage'][1][0][1] = 'Reprint'                   # Original or reprint
        s['Originals'][1] = s['Originals'][1][1:]            # a swapped-out Original leaves the Originals tab
        s['Coverage'][1][1][6] = 'f.html'                    # File name was RETRY
        s['Coverage'][1][2][7] = 'Yes'                       # Saved Copy? was No
        b['Coverage'][1][1][6] = 'RETRY – TinyFish'
        b['Coverage'][1][2][7] = 'No'
        res = {'origin_swaps': [{'old_original': '10001', 'new_original': '10009', 'cells': [['10001', 'Original or reprint']]}],
               'retry_cleared': [{'aid': '10002'}],
               'queue_applied': [{'id': 'q1', 'cells': [['10003', 'Saved Copy?']]}]}
        rep = cmp(wb(b), wb(s), res)
        self.assertEqual(rep.problems, [])
        self.assertEqual(sorted(c.allowed_by for c in rep.changes), ['origin_swap', 'originals_mirror', 'queue_applied', 'retry_cleared'])

    def test_retry_cleared_only_for_its_two_columns(self):
        s = base_sheets()
        s['Coverage'][1][1][3] = 'changed headline'
        self.assertEqual(codes(cmp(wb(base_sheets()), wb(s), {'retry_cleared': [{'aid': '10002'}]})), ['cell_changed'])

    def test_press_release_derived_columns(self):
        s = base_sheets()
        s['Press releases'][1][0][4] = 7        # Related count (derived), was 2
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertEqual(rep.problems, [])
        self.assertEqual(rep.changes[0].allowed_by, 'rel_derived')
        s2 = base_sheets()
        s2['Press releases'][1][0][2] = 'Edited title'      # not derived
        self.assertEqual(codes(cmp(wb(base_sheets()), wb(s2))), ['cell_changed'])

    def test_derived_set_applies_on_press_releases_only(self):
        s = base_sheets()
        s['Unlinked print pages'][1][0][1] = 'Other paper'
        self.assertEqual(codes(cmp(wb(base_sheets()), wb(s))), ['cell_changed'])


class RowRules(unittest.TestCase):
    def moved_sheets(self, on_removed=True):
        s = base_sheets()
        row = s['Coverage'][1].pop(1)                 # 10002 leaves Coverage
        if on_removed:
            s['Removed'][1].append([row[0], 'Coverage'])
        return s

    def test_removed_move_allowed(self):
        res = {'removed': [{'story': 's00002', 'rows': [{'aid': '10002'}]}]}
        s = self.moved_sheets()
        s['Originals'][1] = [r for r in s['Originals'][1] if r[0] != '10002']
        rep = cmp(wb(base_sheets()), wb(s), res)
        kinds = {(c.sheet, c.kind, c.allowed_by) for c in rep.changes}
        self.assertIn(('Coverage', 'moved', 'removed_move'), kinds)
        self.assertEqual(rep.problems, [])

    def test_removed_move_needs_the_removed_tab(self):
        res = {'removed': [{'story': 's00002', 'rows': [{'aid': '10002'}]}]}
        rep = cmp(wb(base_sheets()), wb(self.moved_sheets(on_removed=False)), res)
        self.assertIn('row_missing', codes(rep))

    def test_removed_move_needs_the_result(self):
        rep = cmp(wb(base_sheets()), wb(self.moved_sheets()), {})
        self.assertIn('row_missing', codes(rep))

    def test_removed_move_of_av_row_and_original_row(self):
        b = base_sheets()
        s = self.moved_sheets()
        s['Originals'][1] = [r for r in s['Originals'][1] if r[0] != '10002']
        s['Audio & video details'][1] = [r for r in s['Audio & video details'][1] if r[0] != '10002']
        res = {'removed': [{'story': 's00002', 'rows': [{'aid': '10002'}]}]}
        rep = cmp(wb(b), wb(s), res)
        self.assertEqual(rep.problems, [])
        self.assertEqual({c.sheet for c in rep.changes if c.kind == 'moved'}, {'Coverage', 'Originals', 'Audio & video details'})

    def test_removed_tab_row_never_allowed_to_vanish(self):
        b = self.moved_sheets()
        s = self.moved_sheets()
        s['Removed'][1].pop()
        res = {'removed': [{'story': 's00002', 'rows': [{'aid': '10002'}]}]}
        self.assertIn('row_missing', codes(cmp(wb(b), wb(s), res)))

    def test_bills_row_missing_flags(self):
        s = base_sheets()
        s['Bills'][1].pop(0)
        self.assertIn('row_missing', codes(cmp(wb(base_sheets()), wb(s))))

    def test_new_rows_allowed_on_coverage_press_av_removed(self):
        s = base_sheets()
        s['Coverage'][1].append(['10050', 'Original', 'sNEW', 'Fresh', None, None, None, None])
        s['Originals'][1].append(['10050', 'Original', 'sNEW', 'Fresh', None, None, None, None])
        s['Press releases'][1].append(['pr00099', 'u', 't', 'd', None])
        s['Audio & video details'][1].append(['10050', 'Show'])
        res = {'runs': {'r': {'ids': {'NEW-1': '10050'}, 'added': ['10050']}}, 'counts': {'rows_added': 1}}
        rep = cmp(wb(base_sheets()), wb(s), res)
        self.assertEqual(rep.problems, [], rep.problems)
        self.assertEqual(rep.summary()['rows_added'], {'Coverage': 1, 'Originals': 1, 'Press releases': 1, 'Audio & video details': 1})

    def test_new_row_on_bills_not_allowed(self):
        s = base_sheets()
        s['Bills'][1].append(['AB 9', 'x', 'y', 'z'])
        self.assertIn('row_added', codes(cmp(wb(base_sheets()), wb(s))))

    def test_foreign_article_id(self):
        s = base_sheets()
        s['Coverage'][1].append(['99999', 'Original', 'sNEW', 'Smuggled', None, None, None, None])
        s['Originals'][1].append(['99999', 'Original', 'sNEW', 'Smuggled', None, None, None, None])
        res = {'runs': {'r': {'ids': {'NEW-1': '10050'}, 'added': ['10050']}}}
        rep = cmp(wb(base_sheets()), wb(s), res)
        self.assertEqual(rep.refusal()[0], 'FOREIGN_ROW')
        self.assertIn('99999', rep.refusal()[1])

    def test_assigned_via_other_result_key(self):
        s = base_sheets()
        s['Coverage'][1].append(['10051', 'Original', 'sNEW', 'Orig', None, None, None, None])
        s['Originals'][1].append(['10051', 'Original', 'sNEW', 'Orig', None, None, None, None])
        rep = cmp(wb(base_sheets()), wb(s), {'origin_added': [{'aid': '10051'}]})
        self.assertEqual([p for p in rep.problems if p.code == 'FOREIGN_ROW'], [])

    def test_rowcount_against_sheet_task_numbers(self):
        s = base_sheets()
        s['Coverage'][1].append(['10050', 'Original', 's9', 'Fresh', None, None, None, None])
        s['Originals'][1].append(['10050', 'Original', 's9', 'Fresh', None, None, None, None])
        ok = {'runs': {'r': {'ids': {}, 'added': ['10050']}}, 'counts': {'rows_added': 1}, 'verify': {'rows_before': 3, 'rows_after': 4, 'originals': 4}}
        self.assertEqual(cmp(wb(base_sheets()), wb(s), ok).problems, [])
        bad = dict(ok, counts={'rows_added': 2})
        self.assertEqual(cmp(wb(base_sheets()), wb(s), bad).refusal()[0], 'ROWCOUNT')
        bad2 = dict(ok, verify={'rows_before': 3, 'rows_after': 5, 'originals': 4})
        self.assertEqual(cmp(wb(base_sheets()), wb(s), bad2).refusal()[0], 'ROWCOUNT')

    def test_pass2_rowcount_must_match_pass1(self):
        r1 = {'verify': {'rows_before': 3, 'rows_after': 3, 'originals': 3}}
        r2 = {'verify': {'rows_before': 3, 'rows_after': 4}}
        self.assertEqual(cmp(wb(base_sheets()), wb(base_sheets()), r1, r2).refusal()[0], 'ROWCOUNT')

    def test_originals_must_mirror_coverage(self):
        s = base_sheets()
        s['Originals'][1].pop()
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertIn('originals_mirror', [p.kind for p in rep.problems])

    def test_new_original_row_that_is_not_an_original_on_coverage(self):
        s = base_sheets()
        s['Originals'][1].append(['10077', 'Original', 's7', 'Stray', None, None, None, None])
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertIn('row_added', [p.kind for p in rep.problems])


class StructureRules(unittest.TestCase):
    def test_header_row_lost_flags(self):
        s = base_sheets()
        s['Bills'][0] = []
        rep = cmp(wb(base_sheets()), wb(s))
        self.assertIn('header_changed', codes(rep))
        self.assertIn('header row lost', rep.refusal()[1])

    def test_header_cell_renamed_flags(self):
        s = base_sheets()
        s['Coverage'][0][3] = 'Title'
        self.assertIn('header_changed', codes(cmp(wb(base_sheets()), wb(s))))

    def test_header_column_added_flags(self):
        s = base_sheets()
        s['Press releases'][0].append('Extra')
        self.assertIn('header_changed', codes(cmp(wb(base_sheets()), wb(s))))

    def test_tab_missing_added_and_reordered(self):
        s = base_sheets()
        del s['Bills']
        self.assertIn('tab_missing', codes(cmp(wb(base_sheets()), wb(s))))
        s = base_sheets()
        s['Scratch'] = [['a'], []]
        self.assertIn('tab_added', codes(cmp(wb(base_sheets()), wb(s))))
        b = base_sheets()
        del b['Audio & video details']
        s = base_sheets()
        self.assertEqual([p for p in cmp(wb(b), wb(s)).problems if p.kind == 'tab_added'], [])   # a tab a run may create
        s = dict(reversed(list(base_sheets().items())))
        self.assertIn('tab_order', codes(cmp(wb(base_sheets()), wb(s))))

    def test_hyperlink_kept_and_lost(self):
        links = {('Coverage', 2, 3): 'http://x/1', ('Coverage', 3, 3): 'http://x/2'}
        a = wb(base_sheets(), links)
        same_links = wb(base_sheets(), links)
        self.assertEqual(cmp(a, same_links).problems, [])
        lost = wb(base_sheets(), {('Coverage', 2, 3): 'http://x/1'})
        rep = cmp(a, lost)
        self.assertEqual(codes(rep), ['hyperlink_lost'])
        self.assertIn('Headline', rep.problems[0].text)

    def test_hyperlink_follows_its_row_when_rows_shift(self):
        links = {('Coverage', 3, 3): 'http://x/2'}                    # row 10002
        s = base_sheets()
        s['Coverage'][1].insert(0, ['10000', 'Original', 's0', 'New first', None, None, None, None])
        s['Originals'][1].insert(0, ['10000', 'Original', 's0', 'New first', None, None, None, None])
        shifted = wb(s, {('Coverage', 4, 3): 'http://x/2'})           # same row, now one lower
        res = {'runs': {'r': {'ids': {}, 'added': ['10000']}}}
        rep = cmp(wb(base_sheets(), links), shifted, res)
        self.assertEqual([p for p in rep.problems if p.kind == 'hyperlink_lost'], [])

    def test_hyperlink_gain_is_fine(self):
        rep = cmp(wb(base_sheets()), wb(base_sheets(), {('Coverage', 2, 3): 'http://x/1'}))
        self.assertEqual(rep.problems, [])


class Outputs(unittest.TestCase):
    def test_token_is_deterministic_and_sensitive(self):
        t = D.preview_token('run-1', 'abc', 'x')
        self.assertEqual(t, D.preview_token('run-1', 'abc', 'x'))
        self.assertEqual(len(t), 16)
        self.assertNotEqual(t, D.preview_token('run-1', 'abd', 'x'))
        self.assertNotEqual(t, D.preview_token('run-2', 'abc', 'x'))
        self.assertNotEqual(t, D.preview_token('run-1', 'abc', 'y'))

    def test_tsv_columns_and_refusal_text(self):
        s = base_sheets()
        for i in range(25):
            s['Coverage'][1].append([f'2{i:04d}', 'Original', 's', f'h{i}', None, None, None, None])
        rep = cmp(wb(base_sheets()), wb(s))
        lines = rep.tsv_text().splitlines()
        self.assertEqual(lines[0].split('\t'), ['sheet', 'row', 'key', 'column', 'kind', 'old', 'new', 'allowed_by'])
        self.assertTrue(all(len(l.split('\t')) == 8 for l in lines))
        b = base_sheets()
        for i in range(30):
            b['Bills'][1].append([f'AB {i}', 'a', 'b', 'c'])
        s = base_sheets()
        code, txt, detail = cmp(wb(b), wb(s)).refusal()
        self.assertEqual(code, 'OVERWRITE')
        self.assertEqual(detail['n_problems'], 30)
        self.assertIn('+10 more', txt)


if __name__ == '__main__':
    unittest.main()
