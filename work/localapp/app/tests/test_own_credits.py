"""OWNCREDIT-v1 (patch 32): in reprint_check, a find's credit signal is its own credits, not the pooled credits of every find in the run.
First real update (2026-11-05): San Mateo credited CalMatters, so an AP story in the Newtown Bee (0% shared text) became a Reprint of CalMatters.

    python3 -I work/localapp/app/tests/test_own_credits.py -v"""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'code'))
import reprint_rule as RR  # noqa: E402

CALM = ('The question Proposition 2 poses to California voters is simple: should the state be able to save more money when its economy '
        'is booming? The ballot measure would raise the cap on the rainy day fund and let lawmakers set aside more of the windfall from '
        'AI-driven capital gains. ') * 4
SANMATEO = 'By Yue Stella Yu CalMatters. ' + CALM
AP = ('LOS ANGELES (AP) - Jewish heirs of Holocaust victims and their representatives have filed two lawsuits in California seeking the '
      'return of artworks they say were looted by the Nazis. California Assemblyman Jesse Gabriel wrote Assembly Bill 2867, signed in '
      'September, which lets victims or their heirs recover art seized during the Holocaust. ') * 4

orig = {'Article ID': '00009', 'Story ID': 's00002', 'Outlet': 'CALmatters', 'Date': '2026-10-23', 'Language': 'English',
        'Author / byline': 'Yue Stella Yu', 'Original or reprint': 'Original'}
sm = {'Article ID': 'N2', 'Outlet': 'San Mateo Daily Journal, The', 'Date': '2026-10-26', 'Language': 'English', 'Author / byline': 'Yue Stella Yu CalMatters'}
nb = {'Article ID': 'N6', 'Outlet': 'Newtown Bee, The', 'Date': '2026-10-30', 'Language': 'English', 'Author / byline': ''}


class OwnCredits(unittest.TestCase):
    def verdict(self, a, b):
        return RR.text_verdict([RR.version(a)], [RR.version(b)])

    def test_pooled_credit_wrongly_links_ap_story(self):
        run = RR.origin_credits([sm, nb], {id(sm): SANMATEO, id(nb): AP})[0]
        pc = RR.pair_class(orig, nb, self.verdict(AP, CALM), run, None, {id(nb): AP})
        self.assertEqual(pc['kind'], 'reprint')          # the bug the patch avoids (pooled credits)

    def test_own_credit_keeps_ap_story_its_own(self):
        own = RR.origin_credits([nb], {id(nb): AP})[0]
        pc = RR.pair_class(orig, nb, self.verdict(AP, CALM), own, None, {id(nb): AP})
        self.assertNotEqual(pc['kind'], 'reprint', pc)

    def test_patch_uses_own_credits(self):
        p = (REPO / 'work/localapp/app/patches/32_sheet_task_own_credits.patch').read_text(encoding='utf-8')
        self.assertIn('+                    pc = RR.pair_class(c, o, v, own_cred,', p)


if __name__ == '__main__':
    unittest.main()
