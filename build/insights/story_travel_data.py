"""story_travel_data.py — block "ins-story_travel" for the Story travel insight (contract §6: build(cov, data, ctx)).

Why: story records carry Reach on the Original only; reprints (rep objects) have outlet/state/county but no Reach,
and ~96% of reprint rows in the sheet have a blank Reach cell. The timeline colours every reprint by Reach, so
each reprint outlet needs one. Nothing is written back to the sheet.

Order of evidence (first hit wins):
  1. the reprint row's own Reach cell (Coverage, by Article ID)                       -> "a" (only when it differs from "o")
  2. same-outlet consensus over every sheet row with a Reach (most common value)      -> "o"
  3. same-publisher consensus (the row's Publisher)                                   -> "o"
  4. outlet state: a US state other than CA/DC -> 'Out-of-state local'; a non-US place -> 'International'
                                                                                      -> "o" + listed in "inf" (shown as inferred)
  5. otherwise nothing -> the view shows "Not classified".
The retired label 'Spanish-language & ethnic' is never output (DECISIONS 103). Ties break alphabetically.

Block: {"o": {outlet: reach}, "a": {aid: reach}, "inf": [outlet, ...], "n": {outlet: source name}, "x": {Story ID: why}}

TRAVEL-v2 (2026-10-27, Sammy: "the data is cluttered and I think it's using old file names"):
  "n"  source names for the originals' outlets, from the CURRENT sheet only (never the old tracker's carried-over "pub",
       which was keyed by old jg- codes): the AP wire feeds -> "Associated Press"; spelling variants that differ only in
       case or a leading "The" (CALmatters / CalMatters, The Denver Gazette / Denver Gazette) -> one spelling (the
       sheet's Publisher value when it names the same outlet, else the most common spelling); NewsBank's
       "X, The/The X on Sunday" -> "The X". Only names that change are listed.
  "x"  stories left out of the Story picker (still in the tracker): "own" = every reprint ran in the original's own
       outlet (didn't travel); "dup:<Story ID>" = the same headline on the same day as a story with more reprints.
"""
import collections, re

US = set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA '
         'RI SC SD TN TX UT VT VA WA WV WI WY DC PR USA US'.split())
RETIRED = 'Spanish-language & ethnic'


def _top(c):
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def build(cov, data, ctx):
    oc, pc, byaid = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter), {}
    for aid, outlet, pub, reach in zip(cov['Article ID'], cov['Outlet'], cov['Publisher'], cov['Reach']):
        aid, reach = str(aid).strip(), str(reach).strip()
        if aid:
            byaid[aid.zfill(5)] = (str(pub).strip(), reach)
        if not reach or RETIRED in reach:
            continue
        if outlet:
            oc[outlet][reach] += 1
        if pub:
            pc[pub][reach] += 1
    o, a, inf = {}, {}, set()
    reps = [rp for s in data for rp in (s.get('reps') or [])]
    for rp in reps:
        out = rp.get('outlet') or ''
        if not out or out in o:
            continue
        pub = byaid.get(str(rp.get('aid') or ''), ('', ''))[0]
        st = str(rp.get('state') or '').strip()
        if out in oc:
            o[out] = _top(oc[out])
        elif pub and pub in pc:
            o[out] = _top(pc[pub])
        elif st and st not in US:
            o[out] = 'International'; inf.add(out)
        elif st in US and st not in ('CA', 'DC', 'USA', 'US'):
            o[out] = 'Out-of-state local'; inf.add(out)
    for rp in reps:
        own = byaid.get(str(rp.get('aid') or ''), ('', ''))[1]
        if own and RETIRED not in own and o.get(rp.get('outlet')) != own:
            a[rp['aid']] = own
    n, x = _names(cov, data), _excluded(data)
    return {'o': dict(sorted(o.items())), 'a': dict(sorted(a.items())), 'inf': sorted(inf), 'n': n, 'x': x}


def _disp(o):  # build_data's display form: "Sacramento Bee, The" -> "The Sacramento Bee"
    o = str(o).strip(); m = re.match(r'^(.*), (The|La|El|Los|Las|Le|Les|Die|Der|Il)$', o)
    return f'{m.group(2)} {m.group(1)}' if m else o


AP = re.compile(r'^(the )?associated press\b|^ap\b', re.I)


def _key(o):
    return re.sub(r'^the\s+', '', re.sub(r'\s+', ' ', o.strip().lower()))


def _names(cov, data):
    spell, pubs = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for outlet, pub in zip(cov['Outlet'], cov['Publisher']):
        d = _disp(outlet)
        if d:
            spell[_key(d)][d] += 1
            if str(pub).strip() and _key(str(pub)) == _key(d):
                pubs[_key(d)][str(pub).strip()] += 1
    out = {}
    for r in data:
        if not r.get('reps'):
            continue
        raw = r.get('outlet') or ''
        m = re.match(r'^(.*), The/(.*)$', raw)
        if AP.search(raw):
            name = 'Associated Press'
        elif m:
            name = 'The ' + m.group(1).strip()
        else:
            k = _key(raw)
            name = _top(pubs[k]) if pubs.get(k) else (_top(spell[k]) if spell.get(k) else raw)
        if name and name != raw:
            out[raw] = name
    return dict(sorted(out.items()))


def _hkey(h):
    return re.sub(r'[^a-z0-9]', '', str(h).lower())[:50]


def _excluded(data):
    x, seen = {}, collections.defaultdict(list)
    for r in data:
        reps = r.get('reps') or []
        if not reps:
            continue
        other = {p.get('outlet') for p in reps} - {r.get('outlet')}
        if not other:
            x[r['id']] = 'own'; continue
        if r.get('prec') == 'day' and _hkey(r.get('hl')):
            seen[(_hkey(r.get('hl')), r.get('date'))].append((len(other), r['id']))
    for grp in seen.values():
        if len(grp) > 1:
            keep = sorted(grp, key=lambda t: (-t[0], t[1]))[0][1]
            for _, sid in grp:
                if sid != keep:
                    x[sid] = 'dup:' + keep
    return dict(sorted(x.items()))


if __name__ == '__main__':  # standalone: python3 -I story_travel_data.py XLSX DATA_JSON OUT_JSON
    import json, sys
    import pandas as pd
    cov = pd.read_excel(sys.argv[1], sheet_name='Coverage', dtype=str).fillna('')
    res = build(cov, json.load(open(sys.argv[2])), {})
    txt = json.dumps(res, ensure_ascii=False, separators=(',', ':'))
    open(sys.argv[3], 'w').write(txt)
    print(len(res['o']), 'outlets,', len(res['a']), 'row overrides,', len(res['inf']), 'inferred,', len(res['n']), 'names,', len(res['x']), 'left out,', len(txt.encode()), 'bytes')
