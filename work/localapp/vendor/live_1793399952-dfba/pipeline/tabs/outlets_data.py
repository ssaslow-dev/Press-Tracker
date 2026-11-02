"""Outlets tab block tab_outlets (agent-tab-outlets, TABS-v1): the sheet's own outlet attributes per canonical outlet.

build(cov, data, ctx) -> {"v": 2, "k": [distinct values], "o": {canonical outlet -> [reach, medium, language, county, state,
city, rows]}} where the six attributes are indexes into "k" (0 = "" blank). Only outlets that appear in the tracker's
stories or their reprints (data.json) are listed.
Why: tracker stories (data.json) carry Reach / Format / Language / County only for the story's ORIGINAL outlet; reprint
rows (r.reps) carry county and state only. Outlets that only ran reprints would have no reach, format or language. The
Coverage sheet has these columns on every row, so this block takes, per canonical outlet, the most common non-blank value
of each column over all its Coverage rows (tie: alphabetical). Canonical names are the framework's (tab-common,
build/tabs/_common_data.py: Outlet display form, case/accent/"The" variants merged, AP wire feeds -> Associated Press,
"Daily News" rows published by SCNG -> Los Angeles Daily News per Article ID), so ctx.outlet() in the page agrees.
Deterministic, standard library + pandas only, no network, no writes. ~60 KB."""
import os, collections, importlib.util

_COLS = ['Reach', 'Medium', 'Language', 'Outlet county', 'Outlet state', 'Outlet city']


def _common():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_common_data.py')
    spec = importlib.util.spec_from_file_location('tab_outlets_common', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _record_lookup():
    """OUTLETS-v23: code/outlets.json via sheet_task.norm_outlet (pipeline copy sits next to tabs/). -> (norm_outlet fn, records) or (None, {})"""
    try:
        import sys
        d = os.path.dirname(os.path.abspath(__file__))
        for up in (os.path.join(d, '..'), os.path.join(d, '..', '..', 'code')):
            if os.path.exists(os.path.join(up, 'sheet_task.py')):
                sys.path.insert(0, up)
                import sheet_task as ST
                return ST.norm_outlet, ST.OUTLETS
    except Exception:
        pass
    return None, {}


def build(cov, data, ctx):
    if 'Outlet' not in cov.columns:
        return None
    cm = _common()
    common = cm.build(cov, data, ctx) or {}
    n, a = common.get('n', {}), common.get('a', {})

    def canon(aid, raw):
        raw = str(raw or '').strip()
        if not raw:
            return ''
        if aid in a:
            return a[aid]
        return n.get(raw) or n.get(cm.disp(raw)) or cm.disp(raw)

    col = lambda k: cov[k] if k in cov.columns else [''] * len(cov)
    agg = collections.defaultdict(lambda: [collections.Counter() for _ in _COLS])
    rows = collections.Counter()
    for aid, raw, *vals in zip(cov['Article ID'], cov['Outlet'], *[col(k) for k in _COLS]):
        c = canon(str(aid).strip(), raw)
        if not c:
            continue
        rows[c] += 1
        for i, v in enumerate(vals):
            v = str(v or '').strip()
            if v:
                agg[c][i][v] += 1
    # OUTLETS-v23: blanks the sheet's rows leave (reprint rows carry no Reach; many reprint-only outlets have none at all) come from the
    # outlet's record in code/outlets.json (the same record the Update button fills new rows from); a foreign outlet with no state
    # takes the record's country as its place
    nk, REC = _record_lookup()
    if nk and REC:
        recs = collections.defaultdict(collections.Counter)
        for aid, raw, city in zip(cov['Article ID'], cov['Outlet'], col('Outlet city')):
            c = canon(str(aid).strip(), raw)
            if c:
                recs[c][nk(raw, city)] += 1
        for c, a in agg.items():
            # REVIEW4-LEFTOVERS: a record keyed by the outlet's domain ("opb org", "wnct com") counts for "OPB" / "WNCT"
            rk = next((k2 for k, _ in recs[c].most_common() for k2 in (k, k + ' com', k + ' org', k + ' net') if k2 in REC and not REC[k2].get('alias_of')), None)
            rec = REC.get(rk) if rk else None
            if not rec:
                continue
            # REVIEW4-LEFTOVERS: with several record keys under one outlet the old code left Reach blank; use the common reach when the records agree,
            # else the top record's when it holds >= 60% of the outlet's rows
            _rs = {tuple(REC[k].get('reach') or []) for k in recs[c] if k in REC and REC[k].get('reach')}
            _top = recs[c].most_common(1)[0][1] / max(1, sum(recs[c].values()))
            fb = [('; '.join(rec.get('reach') or []) if len(recs[c]) == 1 or len(_rs) == 1 or _top >= 0.6 else ''), rec.get('medium') or '', rec.get('language') or '',
                  rec.get('county') or '', rec.get('state') or ('' if rec.get('country') in ('', 'US', None) else rec['country']) or ('No home county' if rec.get('home') == 'none' else ''), rec.get('city') or '']   # v23: location_fill_plan no-home marks
            for i, v in enumerate(fb):
                if v and not a[i]:
                    a[i][v] += 1
    used = set()
    for r in data or []:
        used.add(canon(str(r.get('aid') or '').strip(), r.get('outlet')))
        for p in r.get('reps') or []:
            used.add(canon(str(p.get('aid') or '').strip(), p.get('outlet')))
    top = lambda cnt: sorted(cnt.items(), key=lambda x: (-x[1], x[0]))[0][0] if cnt else ''
    vals = {c: [top(x) for x in agg[c]] for c in agg if c in used}
    keys = [''] + sorted({v for vs in vals.values() for v in vs if v})
    ix = {v: i for i, v in enumerate(keys)}
    out = {c: [ix[v] for v in vals[c]] + [rows[c]] for c in sorted(vals)}
    return {'v': 2, 'k': keys, 'o': out}
