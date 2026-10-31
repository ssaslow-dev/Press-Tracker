"""Reporters tab block tab_reporters (REPAFF-v1, v23-int 2026-10-29; DECISIONS V23Q): the ONE affiliation engine's answers.

build(cov, data, ctx) -> {"v": 1, "aff": {story id: {person key: outlet}}, "p": {person key: {"also": [...], "ran": [...], "c": 1}}}
- The engine is code/reporter_record.py (the same rules ship in code/reporters.json and drive reporters.py / the Update button):
  A chain siblings pool under the house paper with most of the person's Originals (Sammy: the top paper, siblings are not employers);
  B an outlet's edited re-run (-1..+14 days, similar headline, fewer stories; same-day tie -> the person's most-used house);
  C a wire / originating-service reporter's stories at other outlets inside the service tenure (+-14 days; byline credits count)
    -> the service; those outlets are the reporter's "Ran in" list (Sammy: wire reporters: employer AP + "Ran in");
  N a distributor / aggregator run (TCA, Yahoo-type rows) -> the person's top staff outlet within +-365 days;
  D a lone story at an outlet beside >= 2 elsewhere within +-365 days, and opinion / guest pieces -> "Also wrote for" (not an employer);
  web: a dated web-verified tenure (reporters.json "web") wins for a story inside it when the person has stories at that outlet.
- aff lists only the stories whose outlet for that person differs from the story's own (canonical) outlet; person key =
  authorsplit.author_key of the story's author as data.json gives it (the tracker's authorKey).
- p[key].c = 1: every story of theirs is an opinion / guest piece (Sammy: "Contributor", counted apart from reporters).
- Wire bylines ("Associated Press" as the author): the story counts under the wire's own outlet name when the tracker has it;
  the outlets that ran the copy are the wire's "Ran in" list.
Deterministic; needs code/ (reporter_record.py, reporters.py, reprint_rule.py, authorsplit.py) on the path."""
import os, sys, json, collections, importlib.util


def _common():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_common_data.py')
    spec = importlib.util.spec_from_file_location('tab_reporters_common', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _code_dir(ctx):
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (os.path.dirname(here), os.path.join((ctx or {}).get('lib', '') or '', 'code'),
              os.path.join(os.path.dirname(os.path.dirname(here)), 'code')):
        if d and os.path.exists(os.path.join(d, 'reporter_record.py')):
            return d
    return None


def build(cov, data, ctx):
    d = _code_dir(ctx)
    if d is None or 'Outlet' not in cov.columns:
        return None
    if d not in sys.path:
        sys.path.insert(0, d)
    import reporter_record as RRec
    import reprint_rule as RR
    import reporters as REP
    from authorsplit import author_key, author_kind
    cm = _common()
    common = cm.build(cov, data, ctx) or {}
    n, a = common.get('n', {}), common.get('a', {})

    def canon(aid, raw):
        raw = str(raw or '').strip()
        if not raw:
            return ''
        if aid and aid in a:
            return a[aid]
        return n.get(raw) or n.get(cm.disp(raw)) or cm.disp(raw)

    rows = RRec.coverage_rows(cov)
    byaid = {str(r.get('Article ID') or '').strip(): r for r in rows}
    unit0, outl = {}, {}
    gmap = collections.defaultdict(collections.Counter)   # unit -> canonical outlet names (all rows)
    for aid, r in byaid.items():
        try:
            u = REP.svc_key(RR.row_key(r))
        except Exception:
            continue
        unit0[aid] = u
        outl[aid] = canon(aid, r.get('Outlet'))
        if outl[aid]:
            gmap[u][outl[aid]] += 1
    recs = RRec.build(rows)
    canon_m = RRec.canon_map()
    ev = {}   # (record key, aid) -> engine row
    for k, rec in recs.items():
        for e in rec.get('_ev', []):
            if e['why'] != 'credit':
                ev[(k, e['aid'])] = e
    names = set(n.values()) | set(outl.values())
    aff, people = {}, collections.defaultdict(lambda: {'also': collections.Counter(), 'ran': collections.Counter(), 'c': 0, 'staff': set()})
    pmap = {}   # (record key, unit) -> canonical outlet, from the person's own rows
    for (k, aid), e in ev.items():
        if aid in unit0 and outl.get(aid):
            pmap.setdefault((k, unit0[aid]), collections.Counter())[outl[aid]] += 1

    def disp_unit(k, u):
        c = pmap.get((k, u)) or gmap.get(u)
        return sorted(c.items(), key=lambda x: (-x[1], x[0]))[0][0] if c else ''

    for r in data or []:
        sid, aid = r.get('id'), str(r.get('aid') or '').strip()
        if not sid or not r.get('date'):
            continue
        so = canon(aid, r.get('outlet'))
        for au in r.get('authors') or []:
            au = str(au or '').strip()
            jk = author_key(au)
            if not jk or jk == 'jesse gabriel':
                continue
            if author_kind(au) == 'wire':
                w = canon('', au)
                if w in names and w != so:
                    aff.setdefault(sid, {})[jk] = w
                    people[jk]['ran'][so] += 1
                continue
            k = RRec.person_key(au, canon_m)
            e = ev.get((k, aid))
            if not e:
                continue
            rec = recs.get(k) or {}
            if rec.get('contributor'):
                people[jk]['c'] = 1
            if e['relation'] == 'contributor':
                if so:
                    people[jk]['also'][so] += 1
                continue
            tgt = disp_unit(k, e['unit']) if e['unit'] != unit0.get(aid) else so
            dd = RR.todate(r.get('date'))
            for t in rec.get('employment', []):   # a dated web tenure covering the story, at an outlet the person has stories at
                if t.get('source') == 'sheet' or t['key'] == 'freelance' or not (t.get('complete', True) or t.get('from')):
                    continue
                t0, t1 = RR.todate(t.get('from')), RR.todate(t.get('to'))
                if dd and (not t0 or t0 <= dd) and (not t1 or dd <= t1):
                    w = disp_unit(k, REP.svc_key(t['key']))
                    if w and (k, REP.svc_key(t['key'])) in pmap:
                        tgt = w
                    break
            people[jk]['staff'].add(tgt or so)
            if tgt and tgt != so:
                aff.setdefault(sid, {})[jk] = tgt
                if str(e.get('why', '')).startswith(('C ', 'N ')):
                    people[jk]['ran'][so] += 1
    p = {}
    for jk, v in people.items():
        x = {}
        also = {o: c for o, c in v['also'].items() if o not in v['staff']}   # an outlet they also report for is not "also wrote for"
        if also:
            x['also'] = [o for o, _ in sorted(also.items(), key=lambda z: (-z[1], z[0]))]
        if v['ran']:
            x['ran'] = [o for o, _ in sorted(v['ran'].items(), key=lambda z: (-z[1], z[0]))]
        if v['c']:
            x['c'] = 1
        if x:
            p[jk] = x
    ok_row = lambda sid, aid: aid in byaid and str(byaid[aid].get('Original or reprint') or '') == 'Original' and str(byaid[aid].get('Story ID') or '') == sid
    seen = sorted({(str(r.get('id')), str(r.get('aid') or '')) for r in data or [] if r.get('id') and r.get('date') and ok_row(str(r.get('id')), str(r.get('aid') or ''))})
    # ids: the stories this build judged, as "<Story ID digits>:<Original Article ID>" (comma-joined): a story outside it (added in the
    # page by the Update button, an Original swapped since, or a test fixture) falls back to the in-page rules
    return {'v': 1, 'aff': {k: dict(sorted(v.items())) for k, v in sorted(aff.items())}, 'p': dict(sorted(p.items())),
            'ids': ','.join((s[1:] if s.startswith('s') else s) + ':' + a for s, a in seen)}
