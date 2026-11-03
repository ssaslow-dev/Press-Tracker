"""OTHERFILES-v1: the saver's diff lets the "Other files" cell of a row GROW (append only) and refuses every other change to it.
Synthetic workbooks. Run: python3 -I -m unittest discover -s work/saver/tests -t work/saver/tests"""
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


def sheets(cell1='nb10001o-s00001.pdf', col=True):
    s = base_sheets()
    if col:
        for tab in ('Coverage', 'Originals'):
            s[tab][0].append('Other files')
            for r in s[tab][1]:
                r.append(None)
            s[tab][1][0][-1] = cell1
    return s


def wb(s):
    N[0] += 1
    return make_wb(Path(T.name) / f'o{N[0]}.xlsx', s, {})


def cmp(before, after, result=None):
    return D.compare(before, after, result, None, derived_rel=DERIVED, new_ok=NEW_OK)


def set_cell(s, v):
    for tab in ('Coverage', 'Originals'):
        s[tab][1][0][-1] = v
    return s


class OtherFiles(unittest.TestCase):
    def res(self, *names, aid='10001'):
        return {'other_files': [{'aid': aid, 'names': list(names), 'before': 'x'}]}

    def test_the_column_existing_before_and_after_changes_nothing(self):
        rep = cmp(wb(sheets()), wb(sheets()))
        self.assertEqual(rep.problems, [])

    def test_filling_a_blank_other_files_cell_is_a_blank_fill(self):
        rep = cmp(wb(sheets(None)), wb(sheets('pq10001o-s00001.pdf')), self.res('pq10001o-s00001.pdf'))
        self.assertEqual(rep.problems, [])

    def test_append_of_the_reported_name_is_allowed(self):
        b = wb(sheets('nb10001o-s00001.pdf'))
        a = wb(sheets('nb10001o-s00001.pdf; pq10001o-s00001.pdf'))
        rep = cmp(b, a, self.res('pq10001o-s00001.pdf'))
        self.assertEqual(rep.problems, [])
        self.assertEqual(sorted(c.allowed_by for c in rep.changes), ['other_files_append', 'other_files_append'])   # Coverage and its Originals mirror

    def test_append_without_a_report_is_refused(self):
        b = wb(sheets('nb10001o-s00001.pdf'))
        a = wb(sheets('nb10001o-s00001.pdf; pq10001o-s00001.pdf'))
        rep = cmp(b, a)
        self.assertEqual({p.kind for p in rep.problems}, {'cell_changed'})

    def test_append_of_another_name_than_reported_is_refused(self):
        b = wb(sheets('nb10001o-s00001.pdf'))
        a = wb(sheets('nb10001o-s00001.pdf; evil.pdf'))
        self.assertTrue(cmp(b, a, self.res('pq10001o-s00001.pdf')).problems)

    def test_replacing_a_name_is_refused(self):
        b = wb(sheets('nb10001o-s00001.pdf'))
        a = wb(sheets('nb10001r-s00001.pdf'))
        self.assertTrue(cmp(b, a, self.res('nb10001r-s00001.pdf')).problems)

    def test_removing_a_name_is_refused(self):
        b = wb(sheets('nb10001o-s00001.pdf; pq10001o-s00001.pdf'))
        a = wb(sheets('pq10001o-s00001.pdf'))
        self.assertTrue(cmp(b, a, self.res('x.pdf')).problems)
        a2 = wb(sheets(None))
        self.assertTrue(cmp(b, a2, self.res('x.pdf')).problems)

    def test_reordering_is_refused(self):
        b = wb(sheets('a.pdf; b.pdf'))
        a = wb(sheets('b.pdf; a.pdf; c.pdf'))
        self.assertTrue(cmp(b, a, self.res('c.pdf')).problems)

    def test_the_report_for_another_row_does_not_cover_this_row(self):
        b = wb(sheets('a.pdf'))
        a = wb(sheets('a.pdf; c.pdf'))
        self.assertTrue(cmp(b, a, self.res('c.pdf', aid='10002')).problems)

    def test_two_passes_report_the_same_append_once(self):
        al = D.Allow.from_results(self.res('c.pdf'), self.res('c.pdf'))
        self.assertEqual(al.other_files, {'10001': ['c.pdf']})

    def test_no_other_column_may_grow_this_way(self):
        s = sheets('a.pdf')
        b = wb(s)
        s2 = sheets('a.pdf')
        s2['Coverage'][1][0][3] = 'Headline one; more'
        self.assertTrue(cmp(b, wb(s2), self.res('more')).problems)

    def test_adding_the_column_in_a_save_is_still_a_header_change(self):
        rep = cmp(wb(sheets(col=False)), wb(sheets()))
        self.assertIn('header_changed', {p.kind for p in rep.problems})


if __name__ == '__main__':
    unittest.main()
