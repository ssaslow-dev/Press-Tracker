"""Match the workbook's "Unlinked print pages" rows to tracker stories.  READ-ONLY: reads the workbook copy, writes only
proposals.csv, details.csv and summary.json next to this script.  Nothing is applied anywhere.

Evidence available per page: outlet, date, page number, NewsBank citation, "Likely counterpart" (older, looser guess).
No page has a headline or text (none clipped), so the text test (reprint_rule) cannot run on any of them; every match
rests on outlet + date + page + syndication pattern.  Run:  python3 -I match_print_pages.py
"""
import os, sys, csv, json, re, collections, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from common import load_coverage, s, aid, ROOT
sys.path.insert(0, ROOT + '/code')
import reprint_rule as rr

_, COV = load_coverage('Coverage')
_, UNL = load_coverage('Unlinked print pages')

def dt(v):
    v = s(v)[:10]
    try: return datetime.date.fromisoformat(v)
    except Exception: return None

for r in COV + UNL:
    r['_k'] = rr.outlet_key(r.get('Outlet'), r.get('Outlet city'))
    r['_d'] = [d for d in (dt(r.get('Date')), dt(r.get('Print date'))) if d]
    r['_aid'] = aid(r)

COV = [r for r in COV if s(r.get('Story ID'))]
by_story = collections.defaultdict(list)
for r in COV: by_story[s(r['Story ID'])].append(r)
orig = {}
for sid, rows in by_story.items():
    o = [r for r in rows if s(r.get('Original or reprint')) == 'Original']
    orig[sid] = o[0] if o else rows[0]
by_key = collections.defaultdict(list)
for r in COV: by_key[r['_k']].append(r)
by_house = collections.defaultdict(list)
for r in COV:
    h = rr.row_house(r)
    if h: by_house[h].append(r)

def dist(r, P):
    return min((abs((d - P).days) for d in r['_d']), default=99)

def pageeq(r, pg):
    import re
    a = re.findall(r'\d+', s(r.get('Page'))); b = re.findall(r'\d+', pg)
    return bool(a and b and a[0] == b[0])

def has_print(r):
    return bool(s(r.get('Print Article ID')) or s(r.get('NewsBank print-page link')) or s(r.get('Print date')))

def fmt_rows(rs):
    return ', '.join(f"{x['_aid']}({s(x.get('Date'))[5:]},{s(x.get('Edition')) or '-'})" for x in rs[:3])

CLUSTER = collections.Counter(); CLUSTER_DATE = collections.Counter()
for _u in UNL:
    _p = dt(_u.get('Date')); CLUSTER_DATE[str(_p)] += 1
    _h = s(_u.get('Publisher')) or rr.row_house(_u)
    if _h: CLUSTER[(str(_p), _h)] += 1
# California statewide election days (primary + general), the days whose next morning papers print results
ELECTIONS = [datetime.date(*x) for x in [(2018,6,5),(2018,11,6),(2020,3,3),(2020,11,3),(2022,6,7),(2022,11,8),(2024,3,5),(2024,11,5),(2026,6,2)]]
CLAIMED = {}
OUT, DET = [], []
def prop(tab, key, col, val, cls, conf, ev):
    OUT.append([tab, key, col, val, cls, conf, ev])

for u in UNL:
    P = dt(u.get('Date')); pg = s(u.get('Page')); k = u['_k']; ua = u['_aid']
    cp = s(u.get('Likely counterpart'))
    rec = dict(id=ua, outlet=s(u.get('Outlet')), date=str(P), page=pg, citation_headline='(none: citation has no headline)',
               likely_counterpart=cp, cls='D', conf='low', story='', row='', why='')
    same = [r for r in by_key.get(k, []) if dist(r, P) <= 3]
    exact = [r for r in same if dist(r, P) == 0]
    pool = exact or same
    pool = sorted(pool, key=lambda r: (dist(r, P), not pageeq(r, pg)))
    sids = []
    for r in pool:
        if s(r['Story ID']) not in sids: sids.append(s(r['Story ID']))
    if pool:
        R = pool[0]; sid = s(R['Story ID']); d0 = dist(R, P); rk = R['_aid']
        rec.update(story=sid, row=rk)
        eq = pageeq(R, pg)
        isprint = s(R.get('Edition')) in ('Print', 'Web + Print') or has_print(R)
        link_blank = not s(R.get('NewsBank print-page link'))
        fills = {'Print Article ID': ua, 'Print date': str(P), 'Page': pg,
                 'NewsBank print-page link': s(u.get('NewsBank print-page link')),
                 'NewsBank print page article link via CA State Library': s(u.get('NewsBank print page article link via CA State Library')),
                 'Newsbank APA citation (print page)': s(u.get('Newsbank APA citation (print page)')),
                 'Old Print Article ID': s(u.get('Old Article ID'))}
        def emit(conf, why, skip=()):
            for c, v in fills.items():
                if c in skip: continue
                if v and not s(R.get(c)): prop('Coverage', rk, c, v, 'A', conf, why)
        base = f"same outlet ({s(R.get('Outlet'))}) row {rk} of {sid}, {R.get('Edition') or 'edition blank'}, dated {R.get('Date')}" + (f", print date {R.get('Print date')}" if R.get('Print date') else '')
        if isprint:
            own = s(R.get('Print Article ID'))
            if eq and d0 == 0:
                why = f"{base}: same page ({pg}) as the row's own print record: " + ("the row has no print-page link yet, this record supplies it" if link_blank else "a second NewsBank record of a page the row already links")
                rec.update(cls='A', conf='high', why=why)
                emit('high', why, skip=('Print Article ID', 'Print date', 'Page', 'Old Print Article ID'))
                prop('Unlinked print pages', ua, '(row)', f'retire: duplicate record of the page row {rk} already holds', 'A', 'high', why)
            elif not own and not s(R.get('Page')) and link_blank and d0 == 0 and len(sids) == 1:
                why = f"{base}: row has no page number and no print-page link yet; one story at this paper that day"
                rec.update(cls='A', conf='medium', why=why)
                emit('medium', why, skip=('Print Article ID', 'Print date', 'Old Print Article ID'))
                prop('Unlinked print pages', ua, '(row)', f'retire after the fills on {rk}', 'A', 'medium', why)
            elif (not own or True) and len(sids) == 1 and d0 == 0 and re.findall(r'\d+', s(R.get('Page'))) and int(re.findall(r'\d+', s(R.get('Page')))[0]) == 1 and re.findall(r'\d+', pg) and int(re.findall(r'\d+', pg)[0]) > 1:
                why = f"{base}: row's story starts on p.1 (front page); this is p.{pg} of the same issue, and the paper has only this one story that day: probably the jump page"
                rec.update(cls='A-jump', conf='medium', why=why)
                prop('Unlinked print pages', ua, '(note)', f'keep; after clipping attach as print original (jump page) of row {rk}: _original_pdf/{str(P)[:4]}/{rk}_p{pg}.pdf', 'A-jump', 'medium', why)
            else:
                rec.update(cls='D', conf='low', why=f"{base}: row already holds p.{s(R.get('Page')) or '?'}{' and its own print link' if not link_blank else ''}; this is p.{pg}: jump page of the same story, or another article" + (f" ({len(sids)} stories that day)" if len(sids) > 1 else ''))
        else:
            if eq and d0 == 0: conf = 'high'
            elif d0 == 0 and len(sids) == 1: conf = 'medium'
            elif d0 <= 1 and len(sids) == 1: conf = 'medium'
            else: conf = 'low'
            if len(sids) > 1 and not (eq and d0 == 0): conf = 'low'
            why = (f"{base}; page {'matches' if eq else 'row has ' + (s(R.get('Page')) or 'none') + ', page has ' + pg}; "
                   f"{len(sids)} candidate story(ies) at this paper within 3 days; row has no print edition yet")
            if rk in CLAIMED:
                rec.update(cls='D', conf='low', why=f"{base}: row {rk} is already the match of page {CLAIMED[rk]} (one print edition per row); this is another page of that paper and date: jump page or another article")
                DET.append(rec); continue
            CLAIMED[rk] = ua
            rec.update(cls='A', conf=conf, why=why)
            emit(conf, why)
            ed = s(R.get('Edition'))
            if not ed: prop('Coverage', rk, 'Edition', 'Web + Print', 'A', conf, why)
            elif ed == 'Web': prop('Coverage', rk, 'Edition', 'Web + Print', 'A', conf, 'NOT A BLANK (Edition is Web today): only with a recorded decision; ' + why)
            prop('Unlinked print pages', ua, '(row)', f'remove after the fills on {rk}', 'A', conf, why)
    else:
        # sister papers (same house), other outlet keys, within 3 days
        house = rr.row_house(u)
        sib = [r for r in by_house.get(house, []) if r['_k'] != k and dist(r, P) <= 3] if house else []
        st = collections.defaultdict(list)
        for r in sib: st[s(r['Story ID'])].append(r)
        def score(item):
            sid, rs = item
            return (-sum(1 for r in rs if dist(r, P) == 0), min(dist(r, P) for r in rs), -len(rs))
        cands = sorted(st.items(), key=score)
        ex_c = [c for c in cands if any(dist(r, P) == 0 for r in c[1])]
        if ex_c: cands = ex_c
        # same outlet already in the story but on a date > 3 days away?
        if cands:
            sid, rs = cands[0]
            ex = sum(1 for r in rs if dist(r, P) == 0)
            O = orig[sid]; od = dt(O.get('Date'))
            sameout = [r for r in by_story[sid] if r['_k'] == k]
            rec.update(story=sid, row='')
            if sameout:
                rec.update(cls='D', conf='low', why=f"{s(u.get('Outlet'))} already has a row in {sid} ({sameout[0]['_aid']}, {sameout[0].get('Date')}) on a different date: check before adding")
            elif len(cands) > 1:
                rec.update(cls='D', conf='low', why=f"{len(cands)} stories ran at sister papers within 3 days ({', '.join(c for c, _ in cands[:4])}); best {sid} ({ex} sister rows on {P})")
            else:
                conf = 'high' if ex >= 3 else 'medium' if ex >= 1 else 'low'
                early = od and P < od
                why = (f"sister paper(s) {', '.join(sorted({s(r.get('Outlet')) for r in rs})[:3])} ran {sid} ('{s(O.get('Headline'))[:70]}') on {', '.join(sorted({str(r.get('Date')) for r in rs}))}"
                       f" ({ex} on the page date); only candidate story; this paper has no row for it"
                       f"{'; page is dated BEFORE the story Original (' + str(od) + '): Original swap to be decided by the save program' if early else ''}; no text on either side")
                rec.update(cls='B', conf=conf, why=why)
                new = 'NEW:' + ua
                row = {'Article ID': ua, 'Story ID': sid, 'Original or reprint': 'Reprint', 'Data Source': 'Newsbank', 'Date': str(P), 'Year': P.year,
                       'Date source': 'print edition', 'Outlet': s(u.get('Outlet')), 'Publisher': s(u.get('Publisher')), 'Outlet city': s(u.get('Outlet city')),
                       'Outlet county': s(u.get('Outlet county')), 'Outlet state': s(u.get('Outlet state')), 'Medium': 'Newspaper', 'Format': 'Print',
                       'Edition': 'Print', 'Page': pg, 'Headline': s(O.get('Headline')) + '  [copied from the Original; replace at clip]',
                       'NewsBank print-page link': s(u.get('NewsBank print-page link')),
                       'NewsBank print page article link via CA State Library': s(u.get('NewsBank print page article link via CA State Library')),
                       'Newsbank APA citation (print page)': s(u.get('Newsbank APA citation (print page)')), 'Old Article ID': s(u.get('Old Article ID'))}
                for c, v in row.items():
                    if s(v): prop('Coverage', new, c, v, 'B', conf, why)
                prop('Unlinked print pages', ua, '(row)', 'move to Coverage as the new row (same Article ID)', 'B', conf, why)
        else:
            pub = s(u.get('Publisher')); dkey = (str(P), pub or house)
            n_cl = CLUSTER[dkey] if (pub or house) else 0
            wire = [sid for sid, rows in by_story.items() if len(rows) >= 8 and orig[sid]['_d'] and 0 <= (P - orig[sid]['_d'][0]).days <= 3
                    and rr.row_type(orig[sid]) in ('wire', 'distributor')]
            elect = [e for e in ELECTIONS if 0 <= (P - e).days <= 2]
            st_ = s(u.get('Outlet state'))
            if elect and CLUSTER_DATE[str(P)] >= 5:
                rec.update(cls='C', conf='low', why=f"{P} is {(P - elect[0]).days} day(s) after the {elect[0]} election and {CLUSTER_DATE[str(P)]} unlinked pages from different papers share the date; no tracker story at this paper: most likely an election-results page (results tables are not coverage, INCL-v1). Clip one to confirm")
            elif len(wire) == 1 and st_ != 'CA':
                sid = wire[0]; O = orig[sid]
                rec.update(cls='B', conf='low', story=sid, why=f"no row at this paper or its sisters; one widely carried wire story ran just before ({sid}, {O.get('Outlet')}, {O.get('Date')}, {len(by_story[sid])} rows: '{s(O.get('Headline'))[:60]}'); out-of-state paper; no text")
                new = 'NEW:' + ua
                for c, v in {'Article ID': ua, 'Story ID': sid, 'Original or reprint': 'Reprint', 'Data Source': 'Newsbank', 'Date': str(P), 'Year': P.year, 'Date source': 'print edition', 'Outlet': s(u.get('Outlet')), 'Publisher': s(u.get('Publisher')), 'Outlet city': s(u.get('Outlet city')), 'Outlet county': s(u.get('Outlet county')), 'Outlet state': st_, 'Medium': 'Newspaper', 'Format': 'Print', 'Edition': 'Print', 'Page': pg, 'NewsBank print-page link': s(u.get('NewsBank print-page link')), 'NewsBank print page article link via CA State Library': s(u.get('NewsBank print page article link via CA State Library')), 'Newsbank APA citation (print page)': s(u.get('Newsbank APA citation (print page)')), 'Old Article ID': s(u.get('Old Article ID'))}.items():
                    if s(v): prop('Coverage', new, c, v, 'B', 'low', rec['why'])
                prop('Unlinked print pages', ua, '(row)', 'move to Coverage as the new row (same Article ID) ONLY after a clip confirms', 'B', 'low', rec['why'])
            else:
                extra = ''
                if n_cl >= 5: extra += f"; {n_cl} pages from the same publisher/chain on this date: probably ONE syndicated piece (clip one page, link all)"
                if len(wire) > 1: extra += f"; {len(wire)} wire stories ran just before ({', '.join(wire[:3])})"
                rec.update(cls='D', conf='low', why='no tracker row at this paper or a sister paper within 3 days' + extra)
    DET.append(rec)

with open(os.path.join(HERE, 'proposals.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['tab', 'row key', 'column', 'new value', 'class', 'confidence', 'evidence']); w.writerows(OUT)
cols = ['id', 'outlet', 'date', 'page', 'citation_headline', 'likely_counterpart', 'cls', 'conf', 'story', 'row', 'why']
with open(os.path.join(HERE, 'details.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, cols, extrasaction='ignore'); w.writeheader(); w.writerows(DET)
cnt = collections.Counter((d['cls'], d['conf']) for d in DET)
agree = collections.Counter()
for d in DET:
    cp = d['likely_counterpart']
    agree[(d['cls'], cp.split(':')[0].split('(')[0].strip() if cp else '')] += 1
json.dump({'n': len(DET), 'by_class_conf': {f'{a}/{b}': n for (a, b), n in sorted(cnt.items())},
           'class_vs_likely': {f'{a} | {b}': n for (a, b), n in sorted(agree.items())}, 'proposal_lines': len(OUT)},
          open(os.path.join(HERE, 'summary.json'), 'w'), indent=1)
print(json.dumps(json.load(open(os.path.join(HERE, 'summary.json'))), indent=1))
