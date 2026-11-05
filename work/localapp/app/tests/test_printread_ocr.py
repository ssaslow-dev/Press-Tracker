"""PRINTREAD-v2 follow-up (patch 30): the reprint test for a row whose text Claude read from a newspaper page is OCR-tolerant; every other row keeps the exact
test. Uses the snapshot library's s01903 text (LA Times 07053). Fast (seconds).

    python3 -I work/localapp/app/tests/test_printread_ocr.py -v"""
import importlib.util
import random
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PATCHES = REPO / 'work' / 'localapp' / 'app' / 'patches'
CHAIN = ['05_sheet_task_photolink', '09_sheet_task_nbpdf', '12_sheet_task_pqpdf', '14_sheet_task_pq_outlet_aliases', '19_sheet_task_reserved_ids',
         '22_sheet_task_prjudge2', '24_sheet_task_printpages', '25_sheet_task_otherfiles', '28_sheet_task_prcolor', '29_sheet_task_printnew',
         '30_sheet_task_printread_ocr']


def load():
    spec = importlib.util.spec_from_file_location('aa', REPO / 'work' / 'localapp' / 'app' / 'assemble_app.py')
    aa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aa)
    t = (REPO / 'code' / 'sheet_task.py').read_text(encoding='utf-8')
    for n in CHAIN:
        t = aa.apply_unified(t, (PATCHES / (n + '.patch')).read_text(encoding='utf-8'), n)
    d = Path(tempfile.mkdtemp())
    for f in (REPO / 'code').glob('*.py'):
        if f.name != 'sheet_task.py':
            (d / f.name).write_bytes(f.read_bytes())
    (d / 'sheet_task.py').write_text(t, encoding='utf-8', newline='\n')
    sys.path.insert(0, str(d))
    spec = importlib.util.spec_from_file_location('sheet_task_p30', d / 'sheet_task.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def noisy(text, seed=7, rate=0.06):
    """realistic newspaper-page reading noise: confusable letters, split and joined words, dropped letters"""
    rnd = random.Random(seed)
    sw = {'l': '1', 'I': 'l', 'rn': 'm', 'cl': 'd', 'O': '0', 'e': 'c', 'h': 'b'}
    out = []
    for w in text.split():
        if len(w) > 4 and rnd.random() < rate:
            k = rnd.choice(['swap', 'split', 'drop'])
            if k == 'swap':
                for a, b in sw.items():
                    if a in w:
                        w = w.replace(a, b, 1)
                        break
            elif k == 'split':
                i = len(w) // 2
                w = w[:i] + ' ' + w[i:]
            else:
                i = rnd.randrange(1, len(w) - 1)
                w = w[:i] + w[i + 1:]
        out.append(w)
    return ' '.join(out)


class ReadPageOCR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load()
        cls.RR = cls.m.RR
        html = (REPO / 'data' / 'library' / '2026' / 'ws07053r-s01903.html').read_text(encoding='utf-8')
        cls.orig_text = cls.RR.html_text(html)
        cls.plain = ' '.join(re.sub(r'\s+', ' ', cls.orig_text[0]).split())
        cls.orig = {'Article ID': '07053', 'Outlet': 'Los Angeles Times', 'Date': '2026-09-29', 'Headline': "California just changed the way you shop for food. Here's how",
                    'Author / byline': 'Karen Garcia'}
        cls.find = {'Article ID': 'ph1', 'Outlet': 'East Bay Times', 'Date': '2026-11-01', 'Headline': "California will add 'Non-Ultraprocessed Certified' seal to foods. What that means",
                    'Author / byline': 'Karen Garcia', 'Original or reprint': 'Reprint', '_page': 'pg1'}

    def task(self, read):
        t = self.m.Task.__new__(self.m.Task)
        nb = {'read': {'by': 'claude'}, 'source': 'page'} if read else {'kind': 'article'}
        t.db = {'pages': {'pg1': {'nb': nb}}}
        return t

    def ftext(self, s):
        return self.RR.html_text("<html><body><article><p>" + s.replace("\n", "</p><p>") + "</p></article></body></html>")

    def test_noise_passes_for_read_page_only(self):
        n = noisy(self.plain)
        self.assertNotEqual(n, self.plain)
        ft = self.ftext(n)
        exact = self.RR.text_verdict([self.RR.version(*ft)], [self.RR.version(*self.orig_text)])
        self.assertFalse(exact and exact['ok'], 'the noise must be heavy enough to fail the exact test: %r' % (exact and exact['m']['raw'],))
        v = self.task(True).compare(self.find, ft, self.orig, self.orig_text)
        self.assertTrue(v and v['ok'], v)
        # the same text on a row that is not a read page keeps the exact test (fails)
        v2 = self.task(False).compare(self.find, ft, self.orig, self.orig_text)
        self.assertFalse(v2 and v2['ok'], v2)

    def test_unrelated_article_fails(self):
        other = ('The Santa Clara County Board of Supervisors voted on Tuesday to approve a new budget for the coming fiscal year, including money for road repairs, '
                 'a new library branch and additional deputies. Supervisors said the plan balances growth with the need to keep reserves, and residents spoke for '
                 'nearly three hours about parks, transit service and the cost of housing across the valley. The budget passed on a four to one vote after a long debate '
                 'about whether to raise the county sales tax in the spring, a measure that would need approval from voters in the next general election. ') * 3
        ft = self.ftext(noisy(other))
        f = dict(self.find, Headline='County approves budget', **{'Author / byline': 'Pat Smith'})
        v = self.task(True).compare(f, ft, self.orig, self.orig_text)
        self.assertFalse(v and v['ok'], v)

    def test_clean_text_unchanged(self):
        ft = self.ftext(self.plain)
        v = self.task(True).compare(self.find, ft, self.orig, self.orig_text)
        v0 = self.task(False).compare(self.find, ft, self.orig, self.orig_text)
        self.assertTrue(v['ok'] and v0['ok'])


if __name__ == '__main__':
    unittest.main()
