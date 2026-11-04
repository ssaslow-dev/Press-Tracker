"""A11: the article data (data/copies/articles) is built up from the keeper's own library.
    AJG_TEST_BUILD=<fresh linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_article_copies.py -v
Works on a hard-linked copy of the test build (snapshot workbook and library, library file names already in NAMING-v2 form).
  1. the plan finds the stories with a saved copy that the article data lacks (the snapshot has 412)
  2. rebuild adds every one it can: NewsBank PDF stories get a text copy, HTML stories their own page; existing entries are byte for byte unchanged
  3. the setup summary's "without a page copy" count falls to the stories that were skipped (listed with a reason)
  4. a second rebuild adds nothing; the station verb (what the Repairs button runs) works and says so in plain words
  5. a shard that grew was kept first in copies/_replaced; the manifest names only shards that exist
"""
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_article_copies'
S = {}


def setUpModule():
    shutil.rmtree(BASE, ignore_errors=True)
    root = T.make_work(BASE, 'a', 'keeper')
    for d in ('station', 'updatefolder', 'saver', 'server'):
        sys.path.insert(0, str(root / 'app' / d))
    import common as C
    import article_copies as AC
    import setup_mac as SM
    S.update(root=root, C=C, AC=AC, SM=SM, lay=C.layout(root))
    adir = S['lay'].copies / 'articles'
    S['before'] = {}
    for f in adir.glob('*.json'):
        if f.name != 'manifest.json':
            S['before'][f.name] = json.loads(f.read_text(encoding='utf-8'))
    S['man0'] = json.loads((adir / 'manifest.json').read_text(encoding='utf-8'))['articles']


def tearDownModule():
    shutil.rmtree(BASE, ignore_errors=True)


class ArticleCopies(unittest.TestCase):
    def test_1_plan(self):
        pl = S['AC'].plan(S['lay'])
        S['plan'] = pl
        n = len(pl['items']) + len(pl['unbuildable'])
        self.assertGreater(n, 300)
        self.assertEqual(S['SM'].summary(S['lay'])['saved_copy_stories_without_page_copy'], n)

    def test_2_rebuild(self):
        pl = S['plan'] if 'plan' in S else S['AC'].plan(S['lay'])
        r = S['AC'].rebuild(S['lay'])
        S['res'] = r
        self.assertGreater(r['added'], 300)
        self.assertEqual(r['added'] + len(r['skipped']), r['missing_before'])
        lay = S['lay']
        adir = lay.copies / 'articles'
        man = json.loads((adir / 'manifest.json').read_text(encoding='utf-8'))['articles']
        for sid, v in S['man0'].items():                      # nothing existing changed
            self.assertEqual(man[sid], v)
        shards = {}
        for sid, v in man.items():
            nm = v.split('/')[-1]
            self.assertTrue((adir / nm).is_file(), nm)
            if nm not in shards:
                shards[nm] = json.loads((adir / nm).read_text(encoding='utf-8'))
            self.assertIn(sid, shards[nm])
        for nm, old in S['before'].items():
            for sid, h in old.items():
                self.assertEqual(shards[nm][sid], h, (nm, sid))
        added = [sid for sid in man if sid not in S['man0']]
        self.assertEqual(len(added), r['added'])
        kinds = {'pdf': 0, 'html': 0}
        for sid in added:
            h = shards[man[sid].split('/')[-1]][sid]
            self.assertIn('<', h)
            kinds['pdf' if 'jg-pdf-text' in h else 'html'] += 1
        self.assertGreater(kinds['pdf'], 100)
        self.assertGreater(kinds['html'], 100)
        S['added'] = added
        for _, why in r['skipped']:
            self.assertTrue(why)

    def test_3_summary(self):
        summ = S['SM'].summary(S['lay'])
        self.assertEqual(summ['saved_copy_stories_without_page_copy'], len(S['res']['skipped']))

    def test_4_second_run_and_verb(self):
        self.assertEqual(S['AC'].rebuild(S['lay'])['added'], 0)
        root = S['root']
        p = subprocess.run([sys.executable, '-I', str(root / 'app' / 'station' / 'station_cli.py'), 'rebuild_copies', '--root', str(root)], capture_output=True, text=True, timeout=600)
        j = json.loads(p.stdout)
        self.assertTrue(j['ok'], p.stdout[:500])
        self.assertEqual(j['added'], 0)
        self.assertIn('line', j)

    def test_5_kept_and_reader(self):
        kept = list((S['lay'].copies / '_replaced').rglob('*.json'))
        self.assertTrue(kept)
        reader = T.make_work(BASE, 'r', 'reader')
        p = subprocess.run([sys.executable, '-I', str(S['root'] / 'app' / 'station' / 'station_cli.py'), 'rebuild_copies', '--root', str(reader)], capture_output=True, text=True, timeout=600)
        self.assertIn('"ok"', p.stdout)      # the server refuses a reader (403); the verb itself only touches the reader's own data


if __name__ == '__main__':
    unittest.main()
