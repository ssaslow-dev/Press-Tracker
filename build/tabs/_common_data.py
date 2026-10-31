"""TABS-v1 framework block tab-common (agent-tabs): cleaned outlet names and the sheet's Publisher column.

build(cov, data, ctx) -> {"v":1, "n": {raw outlet -> canonical}, "a": {Article ID -> canonical}, "p": {canonical -> [[publisher, first date, last date, rows]]}}
- Canonical outlet name (Phase B: "&" = "and", punctuation and hyphens ignored when matching, so India West / India-West and
  "Food & / Food and Environment Reporting Network" are one outlet; no doubled "The The"): the sheet's Outlet in display form ("Sacramento Bee, The" -> "The Sacramento Bee"; "Independent,
  The/The Independent on Sunday" -> "The Independent"); spellings that differ only by case, accents or a leading "The" are
  one outlet, named by the spelling the sheet's Publisher column uses for it when it names itself (CalMatters, not
  CALmatters), else its most common spelling in the sheet (tie: longer, then alphabetical); every Associated Press wire
  feed is "Associated Press" (same rules as story_travel_data.py TRAVEL-v2).
- ALIAS: names the sheet uses for the same outlet under the same Publisher (Sammy 2026-10-27: "Daily News" rows published
  by Southern California News Group are the Los Angeles Daily News). Applied per row (Article ID), so another paper
  called "Daily News" keeps its own name.
- Out-of-state outlets (o: canonical -> [state, reach, medium], only outlets whose most common non-blank "Outlet state" is
  not CA): feeds the US state map (AXIS-v1 sibling USMAP-v1) with the sheet's own Reach / Medium classification.
- Publisher: the sheet's Publisher column as written (filled for outlets with > 10 rows; Lee papers -> Santa Maria News
  Media after the 2020 sale is already in the sheet), as dated spans per canonical outlet, so an outlet that changed
  owner shows each owner with its dates. Blank Publisher cells are not counted.
- h (REPCOUNT-v1): canonical outlet -> house, for outlets that are editions of one paper (the reprint count leaves a story's own house out).
Deterministic (sorted), standard library + pandas only, no network."""
import re, unicodedata, collections

ALIAS = [('daily news', 'Southern California News Group', 'Los Angeles Daily News')]
AP = re.compile(r'^(the )?associated press\b|^ap\b', re.I)


def disp(o):
    o = re.sub(r'\s+', ' ', str(o or '')).strip()
    m = re.match(r'^(.*), The/(.*)$', o)
    if m:   # "Times, The/Sunday Times, The" and the already flipped "The Times, The/Sunday Times" -> "The Times"
        return 'The ' + re.sub(r'^the\s+', '', m.group(1).strip(), flags=re.I)
    m = re.match(r'^(.*), (The|La|El|Los|Las|Le|Les|Die|Der|Il)$', o)
    return f'{m.group(2)} {m.group(1)}' if m else o


def key(o):
    o = unicodedata.normalize('NFKD', disp(o)).encode('ascii', 'ignore').decode().lower().replace('&', ' and ')
    o = re.sub(r"[^a-z0-9']+", ' ', o).replace("'", '')   # punctuation variants are one outlet: India West / India-West
    return re.sub(r'^the\s+', '', re.sub(r'\s+', ' ', o).strip())


def _hbase(c):
    """REPCOUNT-v1 (FINALCHECK-v1): the key of an outlet's house = the paper itself, whatever edition it ran in"""
    s = unicodedata.normalize('NFKD', c).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"\s*today'?s edition\b", '', s)
    s = re.sub(r'\s*\((substack|medium)\)\s*$', '', s)
    m = re.match(r'^(.*?):\s*(.*)$', s)
    if m and re.search(r'\bedition$|^(english|spanish|portuguese|blogs)$', m.group(2).strip()):
        s = m.group(1)   # "El Pais: Mexico Edition", "NPR: Blogs"; college papers ("Collegian, The: Fresno State") keep their suffix
    s = re.sub(r',\s*the$', '', s)
    s = re.sub(r'^the\s+', '', s)
    return re.sub(r'[^a-z0-9]+', '', s)


def _sbase(c):
    """sheet_task._outlet_base: the key the sheet's "# of reprints" uses (accents, "Today's Edition", ": Blogs", ", The", leading "The")"""
    s = str(c or '').replace('\u2019', "'").replace('\u2018', "'")
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().strip()
    s = re.sub(r"\s*:\s*blogs\s*$", '', s)
    s = re.sub(r"\s*\(?\btoday'?s edition\b\)?", '', s)
    s = re.sub(r",\s*the(?=\s*(?::|/|$))", '', s)
    s = re.sub(r"^the\s+", '', s.strip())
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def _rules():
    import json, os
    d = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(d, '..', 'outlet_rules.json'), os.path.join(d, '..', '..', 'code', 'outlet_rules.json')):
        try:
            return json.load(open(p, encoding='utf-8'))
        except (OSError, ValueError):
            continue
    return {}


def house_map(names):
    """REPCOUNT-v1: canonical outlet -> house name, only for outlets that share a house with another canonical outlet:
    "The Sacramento Bee Today's Edition", the El Pais editions, FoodNavigator / FoodNavigator-USA, "NPR: Blogs", plus the outlet
    aliases the sheet already folds (outlet_rules.json aliases: "CNN Wire Service" = CNN, "Northwest Arkansas Democrat-Gazette" =
    Arkansas Democrat-Gazette). Sister papers of one chain (Fresno Bee, Modesto Bee) and city-qualified names ("The Sun (Lowell)")
    are different houses."""
    names = sorted({x for x in names if x})
    key = {x: _hbase(x) for x in names}
    ks = set(key.values())
    for x in names:
        k = key[x]
        if len(k) > 6 and k.endswith('usa') and k[:-3] in ks:
            key[x] = k[:-3]
    parent = {x: x for x in names}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[max(a, b)] = min(a, b)
    first = {}
    for x in names:
        if key[x]:
            union(x, first.setdefault(key[x], x))
    R = _rules()
    al = R.get('aliases') or {}
    gen = set(R.get('generic_needs_city') or ())   # a name several papers share ("Daily News") never folds by alias alone
    bybase = collections.defaultdict(list)
    for x in names:
        bybase[_sbase(x)].append(x)
    for x in names:
        b = _sbase(x)
        t = al.get(b)
        if t and t != b and b not in gen and t not in gen:   # the sheet folds this variant into the outlet whose key is t
            for y in bybase.get(t, []):
                union(x, y)
    g = collections.defaultdict(list)
    for x in names:
        g[find(x)].append(x)
    h = {}
    for m in g.values():
        if len(m) > 1:
            rep = sorted(m, key=lambda x: (len(x), x))[0]
            for x in m:
                h[x] = rep
    return h


def _date(s):
    s = str(s or '').strip()[:10]
    return s if re.match(r'^\d{4}(-\d{2}){0,2}$', s) else ''


def _generic():
    """OUTLETS-v23 (OUTLETQ-v1 Q14): outlet_rules.json generic_needs_city - names several papers share (The Sun, The Record...)"""
    import json, os
    d = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(d, '..', 'outlet_rules.json'), os.path.join(d, '..', '..', 'code', 'outlet_rules.json')):
        try:
            return set(json.load(open(p, encoding='utf-8')).get('generic_needs_city') or ())
        except (OSError, ValueError):
            continue
    return set()


def build(cov, data, ctx):
    if 'Outlet' not in cov.columns:
        return None
    pubcol = cov['Publisher'] if 'Publisher' in cov.columns else [''] * len(cov)
    alias = {(k, p): c for k, p, c in ALIAS}
    spell = collections.defaultdict(collections.Counter)
    rows = []
    col = lambda k: cov[k] if k in cov.columns else [''] * len(cov)
    geo = collections.defaultdict(lambda: [collections.Counter(), collections.Counter(), collections.Counter()])
    for aid, outlet, pub, d, stt, rch, med in zip(cov['Article ID'], cov['Outlet'], pubcol, cov['Date'], col('Outlet state'), col('Reach'), col('Medium')):
        if disp(outlet):
            g = geo[(str(aid).strip(), disp(outlet))]
            for i, v in enumerate((stt, rch, med)):
                if str(v or '').strip():
                    g[i][str(v).strip()] += 1
        o = disp(outlet)
        if not o:
            continue
        pub = str(pub or '').strip()
        if AP.search(o):
            spell['associated press']['Associated Press'] += 1
        else:
            spell[key(o)][o] += 1
        rows.append((str(aid).strip(), str(outlet).strip(), o, pub, _date(d)))
    selfpub = collections.defaultdict(collections.Counter)   # the outlet's own spelling when it is its own publisher
    for _, _, o, pub, _ in rows:
        if pub and key(pub) == key(o):
            selfpub[key(o)][disp(pub)] += 1
    top = lambda c: sorted(c.items(), key=lambda x: (-x[1], -len(x[0]), x[0]))[0][0]
    best = {k: top(selfpub[k]) if selfpub.get(k) else top(c) for k, c in spell.items()}
    canon = lambda o: 'Associated Press' if AP.search(disp(o)) else best.get(key(o), disp(o))
    n, a, spans = {}, {}, collections.defaultdict(lambda: collections.defaultdict(list))
    raws = {r[1] for r in rows} | {r[2] for r in rows}
    for r in data or []:
        raws.add(str(r.get('outlet') or '').strip())
        for p in r.get('reps') or []:
            raws.add(str(p.get('outlet') or '').strip())
    for raw in sorted(x for x in raws if x):
        c = canon(raw)
        if c != raw:
            n[raw] = c
    gen, cities = _generic(), {}
    for aid, city in zip(cov['Article ID'], col('Outlet city')):
        cities[str(aid).strip()] = re.sub(r'\s+', ' ', str(city or '')).strip()
    for aid, raw, o, pub, d in rows:
        c = alias.get((key(o), pub)) or canon(o)
        if (key(o), pub) in alias and aid:
            a[aid] = c
        elif key(o) in gen and cities.get(aid) and aid:   # several papers share the name: one outlet per city, "The Sun (Lowell)"
            c = f'{canon(o)} ({cities[aid]})'
            a[aid] = c
        if pub:
            spans[c][pub].append(d)
    og = collections.defaultdict(lambda: [collections.Counter(), collections.Counter(), collections.Counter()])
    for (aid, o), g in geo.items():
        c = alias.get((key(o), '')) or a.get(aid) or canon(o)
        for i in range(3):
            og[c][i].update(g[i])
    outst = {}
    for c, g in sorted(og.items()):
        stt = g[0].most_common(1)[0][0] if g[0] else ''
        if stt and stt != 'CA':
            outst[c] = [stt, g[1].most_common(1)[0][0] if g[1] else '', g[2].most_common(1)[0][0] if g[2] else '']
    p = {}
    for c, by in sorted(spans.items()):
        lst = []
        for pub, ds in by.items():
            dd = sorted(x for x in ds if x)
            lst.append([pub, dd[0] if dd else '', dd[-1] if dd else '', len(ds)])
        p[c] = sorted(lst, key=lambda x: (x[1] or '9999', x[0]))
    names = {canon(x) for x in raws} | set(a.values())
    h = house_map(names)
    return {'v': 1, 'n': n, 'a': dict(sorted(a.items())), 'p': p, 'o': outst, 'h': dict(sorted(h.items()))}
