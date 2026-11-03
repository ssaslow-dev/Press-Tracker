#!/usr/bin/env python3
"""Synthetic inputs for the chain check, made with the station tests' own generators (read only, imported from work/localapp/station/tests):
  nb.pdf  one NewsBank "Multiple Articles" batch in the REAL layout (tests/nb/make_nb_pdfs.py make_real): one story the tracker does not have,
          one the tracker already has (same NewsBank docref as a row of the for-Update file)
  pq.pdf  one ProQuest export (tests/pq/make_pq_export.py) with one new article
  plan.json  what was made (headlines, docrefs, ids, dates), the oracle for the checks.

    python3 -I make_inputs.py FOR_UPDATE.json OUTDIR COPIES_DIR   (the build's data/copies)
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TESTS = REPO / 'work' / 'localapp' / 'station' / 'tests'
sys.path.insert(0, str(TESTS / 'nb'))
sys.path.insert(0, str(TESTS / 'pq'))
import make_nb_pdfs as NB   # noqa: E402
import make_pq_export as PQ  # noqa: E402

CC = 'ccmark'


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, t, a):
        if t in ('script', 'style', 'head', 'title'):
            self.skip += 1

    def handle_endtag(self, t):
        if t in ('script', 'style', 'head', 'title'):
            self.skip = max(0, self.skip - 1)
        if t in ('p', 'div', 'br', 'h1', 'h2', 'li'):
            self.out.append('\n')

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)


def html_text(h: str) -> str:
    t = _Text()
    t.feed(h)
    return ' '.join(''.join(t.out).split())


def pick_reprint_original(fu, copies: Path):
    """a story the tracker already has WITH a saved copy in the article shards the save reads (data/copies/articles): the stubbed wire copy repeats that
    text, so the PC's text test can confirm the reprint"""
    man = json.loads((copies / 'articles' / 'manifest.json').read_text(encoding='utf-8')).get('articles', {})
    cands = [s for s in fu['stories'] if s['rep'] == 0 and s['date'] >= '2026-09-01' and s['media'] != 'TV' and 'newsbank' not in (s['link'] or '').lower()
             and s['link'].startswith('http') and 40 <= len(s['hl']) <= 130 and not any(c in s['hl'] for c in '"\u201c\u201d') and s['id'] in man]
    shards = {}
    for s in sorted(cands, key=lambda s: s['date'], reverse=True):
        f = man[s['id']]
        if f not in shards:
            shards[f] = json.loads((copies / f).read_text(encoding='utf-8'))
        h = shards[f].get(s['id'])
        if h:
            t = html_text(h)
            if len(t) > 1800:
                return s, re.sub(r'^Saved \d{4}-\d{2}-\d{2} ', '', t)[:6000]
    return None, ''


def main(fu_path, out, copies):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fu = json.loads(Path(fu_path).read_text(encoding='utf-8'))
    stories = {s['aid']: s for s in fu['stories']}
    # a row the tracker has from NewsBank: the first Original with a docref and a story of its own
    known = None
    for r in fu['rows']['rows']:
        if r[2] == 'O' and r[4].startswith('2026-') and r[0] in stories and any('docref=news/' in l for l in r[6]):
            known = r
            break
    assert known, 'no NewsBank-linked Original from 2026 in the for-Update file'
    kdoc = next(l for l in known[6] if 'docref=news/' in l).split('docref=news/')[1].split('&')[0].upper()
    ks = stories[known[0]]
    y, m, d = (int(x) for x in ks['date'].split('-'))
    rs, rtext = pick_reprint_original(fu, Path(copies))
    assert rs, 'no story with a saved copy in data/copies to build the reprint from'
    nd = date.today() - timedelta(days=3)
    new_hl = 'Gabriel secures funding for Valley wildfire recovery fund, chaincheck story'
    NB.REAL = [
        dict(k='cc_new', hl=new_hl, d=(nd.year, nd.month, nd.day), src='Valley Courier Test (CA)', sec='Metro', au='Dana Whitfield', n=380, release=False,
             open=f'Assemblymember Jesse Gabriel (D-Encino) told reporters in Sacramento that the {CC}nb1 recovery fund would reach Valley families.', words=170),
        dict(k='cc_known', hl=ks['hl'], d=(y, m, d), src=f'{ks["outlet"]} (CA)', sec='News', au='', n=240, release=False,
             open='Assemblymember Jesse Gabriel (D-Encino) was named in this story, which the tracker already has.', words=110),
    ]
    orig_rhex = NB.rhex
    NB.rhex = lambda k: kdoc if k == 'cc_known' else orig_rhex(k)
    rec = []
    NB.make_real(str(out / 'nb.pdf'), 'pages', rec)
    # ProQuest: one article, with a date near today
    orig_art = PQ.art

    def art(i, seed=1):
        a = orig_art(i, seed)
        a.update(hl='Gabriel bill on school meal standards moves in Sacramento chaincheck pq', date=nd.isoformat(), mdy=f'{PQ.M.MON3[nd.month - 1]} {nd.day}, {nd.year}', docid='3499000001',
                 body=a['body'] + f' Assemblymember Jesse Gabriel said the {CC}pq1 bill would help schools.')
        return a
    PQ.art = art
    pqarts = PQ.make(str(out / 'pq.pdf'), 1, seed=9)
    plan = dict(nb=dict(new=dict(hl=new_hl, date=nd.isoformat(), outlet='Valley Courier Test', docref=orig_rhex('cc_new'), marker=CC + 'nb1'),
                        known=dict(hl=ks['hl'], aid=known[0], sid=known[1], docref=kdoc, outlet=ks['outlet'], date=ks['date'])),
                pq=dict(hl=pqarts[0]['hl'], docid=pqarts[0]['docid'], date=nd.isoformat(), outlet=pqarts[0]['outlet'], marker=CC + 'pq1'),
                rep=dict(id=rs['id'], hl=rs['hl'], date=rs['date'], outlet=rs['outlet'], text=rtext), nb_record=rec)
    (out / 'plan.json').write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in plan.items() if k not in ('nb_record', 'rep')}, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
