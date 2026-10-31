"""RELTHREAD-v1 (rp-threads, 2026-10-28): release-to-release links, milestone labels and people for the Press releases tab.

build(releases, bills_ev, texts) -> {"th", "x", "pp"} (shape: build/relplan_contract.md "rp-threads"). Pure function;
build/tabs/releases_data.py collects the inputs (sheet "Press releases" + "Bills" tabs, release_texts.json) and calls it.

Rules (Sammy approved the RELPLAN recs 2026-10-28):
- Session: a release dated in an odd year Y is in session Y-(Y+1); even year Y: (Y-1)-Y, except December -> (Y+1)-(Y+2).
- A bill named in a release is ACTIVE for it when (bill, release session) is in the Bills tab and the release is not more
  than BG_DAYS after that bill's last milestone (finished bills: Chaptered / Died / Vetoed / Adopted). A bill the Bills tab
  has only under an EARLIER session, or one finished more than BG_DAYS before, is a BACKGROUND mention (AB 418 in the
  2024-26 food releases) and makes no thread. A bill the Bills tab doesn't carry at all (not his bill) is active, no milestones.
- Thread = all releases with the same active (bill, session), date order (a release naming two active bills is in two threads). Text links (TF-IDF cosine on the release body,
  sentences found in >= 3 releases dropped as boilerplate) of >= STRONG within the same session join threads:
  a release with no active bill INHERITS the bill (pr00091 -> ACR 51 from pr00066); two releases with disjoint active bills
  merge their bills into one thread when each has exactly one (renumbered: AB 469 -> AB 468).
- Pairs outside a shared thread: "f" follow-up / near-duplicate (<= 14 days apart, cosine >= FOLLOW), "s" similar
  (cosine >= SIMILAR any date, or a shared run of >= RUN words outside boilerplate with cosine >= RUN_COS, or a run of
  >= RUN_LONG words).
- Milestone: the Bills-tab milestone of an active bill (or the thread's bill, for an inherited one) dated release-3 ..
  release+1 days; closest first, then signed > vetoed > chaptered > floor > other > committee > introduced > died;
  clerical steps (suspense file, enrolled, inactive file, committee action) never label a release.
- People: the tab's Legislator / Other official cells, one entry per person (title dropped for the key). Joint with = named
  people joined to Gabriel in the title ("Gabriel and X", "X, Gabriel Announce") or named with him in the lead sentence's
  subject (dateline dropped, up to the first verb: "Gabriel (D-Encino), Assemblymember Irwin ..., and ... Pacheco announced").
Standard library only, deterministic."""
import math, re, datetime as dt
from collections import Counter, defaultdict

BG_DAYS = 45
STRONG = 0.60
FOLLOW = 0.35
SIMILAR = 0.45
RUN = 25
RUN_COS, RUN_LONG = 0.20, 40   # a shared run alone needs cosine >= 0.20 or >= 40 words (caucus statement intros are 25-30)
ROUNDUP = 4          # a release naming >= 4 active bills is a roundup (x.nb)
MS_BEFORE, MS_AFTER = 3, 1
RANK = {'signed': 0, 'vetoed': 1, 'chaptered': 2, 'floor': 3, 'other': 4, 'committee': 5, 'introduced': 6, 'died': 7}
STOP = set("""a an and are as at be been but by for from had has have he his in into is it its of on or our s that the their
this to was we were which who will with would not they them than then there these those also more most can may said says
today new state california assemblymember jesse gabriel d""".split())
TITLES = sorted("""Assembly Speaker|Speaker|Senate President pro Tempore|Senate Majority Leader|Assembly Majority Leader|
Assemblymember|Assemblywoman|Assemblyman|Senator|U.S. Senator|Congresswoman|Congressman|Representative|Governor|
Lieutenant Governor|Attorney General|Superintendent of Public Instruction|Secretary of State|Controller|Treasurer|
Insurance Commissioner|Mayor|Supervisor|District Attorney|Councilmember|Council President|City Attorney|Sheriff|
Chief|Rabbi|Dr.|First Partner|Secretary""".replace('\n', '').split('|'), key=len, reverse=True)


def _bn(b):
    m = re.match(r'([A-Z]+)\s*(\d+)', b)
    return (m.group(1), int(m.group(2))) if m else (b, 0)


def _d(s):
    m = re.match(r'(\d{4})-(\d\d)-(\d\d)', str(s or ''))
    return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def session(d):
    y = d.year
    s = y if y % 2 else (y + 1 if d.month == 12 else y - 1)
    return f'{s}-{s + 1}'


def split_name(full):
    """'Senator Scott Wiener' -> ('Senator', 'Scott Wiener')"""
    f = full.strip()
    for t in TITLES:
        if f.startswith(t + ' '):
            return t, f[len(t) + 1:].strip()
    return '', f


def _sentences(body):
    return [s.strip() for s in re.split(r'(?<=[.!?”"])\s+|\n+', body or '') if s.strip()]


def _norm(s):
    return ' '.join(re.findall(r'[a-z0-9]+', s.lower()))


def _clean_bodies(texts):
    """drop sentences (>= 8 words) found in >= 3 releases: bios, caucus boilerplate, contact lines"""
    sent = {k: _sentences(v) for k, v in texts.items()}
    cnt = Counter()
    for k, ss in sent.items():
        cnt.update({_norm(s) for s in ss if len(s.split()) >= 8})
    return {k: ' '.join(s for s in ss if cnt.get(_norm(s), 0) < 3) for k, ss in sent.items()}


def _vectors(bodies):
    toks = {k: [w for w in re.findall(r'[a-z0-9]+', v.lower()) if len(w) > 2 and w not in STOP] for k, v in bodies.items()}
    df = Counter()
    for t in toks.values():
        df.update(set(t))
    n = max(len(toks), 1)
    vec = {}
    for k, t in toks.items():
        tf = Counter(t)
        v = {w: (1 + math.log(c)) * math.log(n / df[w]) for w, c in tf.items() if df[w] < n}
        z = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vec[k] = {w: x / z for w, x in v.items()}
    return vec


def _cos(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(w, 0.0) for w, x in a.items())


def _runs(bodies, n=RUN):
    """pair -> words of the shorter body covered by shared n-word runs"""
    words = {k: re.findall(r'[a-z0-9]+', v.lower()) for k, v in bodies.items()}
    where = defaultdict(set)
    for k, w in words.items():
        for i in range(len(w) - n + 1):
            where[' '.join(w[i:i + n])].add(k)
    cover = defaultdict(set)
    for k, w in words.items():
        for i in range(len(w) - n + 1):
            for o in where[' '.join(w[i:i + n])]:
                if o != k:
                    cover[(k, o)].update(range(i, i + n))
    out = {}
    for (a, b), s in cover.items():
        key = (a, b) if a < b else (b, a)
        out[key] = max(out.get(key, 0), len(s))
    return out


VERB = re.compile(r"\b(announced|announce|introduced|presented|joined|released|held|hosted|unveiled|met|brought|issued|"
                  r"celebrated|secured|honored|led|called|urged|gathered|commented|praised|applauded|stood|passed|approved|"
                  r"adopted|elected|signed|signs|vetoed|vetoes|named|appointed|is|are|were|was|have|has|will|would|today|this|yesterday)\b")


def _subject(lead):
    """the lead sentence's subject (dateline dropped, up to the first verb) when it names Gabriel, else ''"""
    s = re.sub(r"^[^—–]{0,45}[—–]\s*", "", lead or "")
    s = re.sub(r"^(?:Today|Yesterday|This week|On \w+(?: \w+ \d+)?),?\s+", "", s)
    m = VERB.search(s)
    sub = s[:m.start()] if m else ""
    return sub if "Gabriel" in sub else ""


def build(releases, bills_ev, texts):
    """releases: [{"id", "date" (iso), "title", "bills": [..], "names": [(full, kind 'l'|'o')], "lead": str}]
    bills_ev: {(bill, session): {"ev": [[iso, kind, label], ...], "fin": short final status}}  (bill_timeline_data form)
    texts: {release id: body}"""
    R = {r['id']: dict(r, d=_d(r['date'])) for r in releases if _d(r['date'])}
    ids = sorted(R, key=lambda k: (R[k]['d'], k))
    by_bill = defaultdict(set)
    for (b, s) in bills_ev:
        by_bill[b].add(s)
    # 1. active bill keys per release
    act, bg = {}, {}
    for k in ids:
        r = R[k]; ses = session(r['d']); a, g = [], []
        for b in r['bills']:
            key = (b, ses)
            if key in bills_ev:
                ev = bills_ev[key]['ev']; fin = bills_ev[key].get('fin', '')
                last = max((_d(e[0]) for e in ev), default=None)
                done = fin and not fin.startswith('Pending')
                (g if done and last and (r['d'] - last).days > BG_DAYS else a).append(key)
            elif by_bill.get(b) and all(s < ses for s in by_bill[b]):
                g.append((b, min(by_bill[b], key=lambda s: s)))     # an earlier session's bill
            else:
                a.append(key)
        act[k], bg[k] = a, g
    # 2. text links
    bodies = _clean_bodies({k: texts.get(k, '') for k in ids if texts.get(k)})
    vec = _vectors(bodies)
    runs = _runs(bodies)
    tk = sorted(vec)
    cos = {}
    for i, a in enumerate(tk):
        for b in tk[i + 1:]:
            c = _cos(vec[a], vec[b])
            if c >= 0.30 or runs.get((a, b), 0) >= RUN:
                cos[(a, b)] = c
    # 3. threads: union-find over bill keys, inheritance
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for k in ids:
        for key in act[k]:
            find(key)
    how, inherit = {}, defaultdict(list)          # (release, thread-root) -> 'i'/'r' + partner, score
    for (a, b), c in sorted(cos.items()):
        if c < STRONG or session(R[a]['d']) != session(R[b]['d']):
            continue
        A, B = set(act[a]), set(act[b])
        if A & B:
            continue
        if len(A) == 1 and len(B) == 1:
            par[find(next(iter(B)))] = find(next(iter(A)))
            how[a] = ('r', b, c) if a not in how else how[a]
            how[b] = ('r', a, c) if b not in how else how[b]
        elif bool(A) != bool(B):
            src, dst = (a, b) if A else (b, a)
            inherit[dst].append((src, c))
    groups = defaultdict(set)
    for k in ids:
        for key in act[k]:
            groups[find(key)].add(k)
    for dst, lst in inherit.items():
        src, c = max(lst, key=lambda t: (t[1], t[0]))
        for key in act[src]:
            groups[find(key)].add(dst)
        how[dst] = ('i', src, c)
    same = defaultdict(set)              # threads with the same members are one thread naming all their bills
    for root, mem in groups.items():
        same[tuple(sorted(mem))].add(root)
    th, x = [], defaultdict(dict)
    for mt in sorted(same, key=lambda m: (min(R[k]['d'] for k in m), min(same[m]))):
        roots = same[mt]
        mem = sorted(mt, key=lambda k: (R[k]['d'], k))
        if len(mem) < 2:
            continue
        keys = sorted({key for k in mem for key in act[k] if find(key) in roots}, key=lambda t: (t[1], _bn(t[0])))
        bl = [b for b, _ in keys]
        rows = []
        for k in mem:
            h = how.get(k)
            own = [b for b, s in act[k] if find((b, s)) in roots]
            if h and h[0] == 'i' and not own:
                rows.append([k, 'i', h[1], round(h[2], 2)])
            elif h and h[0] == 'r' and len(set(bl)) > 1:
                rows.append([k, 'r', h[1], round(h[2], 2)])
            else:
                rows.append(k)
        ti = len(th)
        th.append([bl, keys[0][1], rows])
        for k in mem:
            x[k].setdefault('t', []).append(ti)
    for k in ids:
        if bg[k]:
            x[k]['bg'] = sorted({b for b, _ in bg[k]}, key=_bn)
        if len(act[k]) >= ROUNDUP:
            x[k]['nb'] = len(act[k])
    # 4. pairs outside a shared thread
    for (a, b), c in sorted(cos.items()):
        if set(x[a].get('t', [])) & set(x[b].get('t', [])):
            continue
        days = (R[b]['d'] - R[a]['d']).days
        rw = runs.get((a, b), 0)
        if abs(days) <= 14 and c >= FOLLOW:
            rel = 'f'
        elif c >= SIMILAR or (rw >= RUN and c >= RUN_COS) or rw >= RUN_LONG:
            rel = 's'
        else:
            continue
        x[a].setdefault('p', []).append([b, rel, round(c, 2), days, rw])
        x[b].setdefault('p', []).append([a, rel, round(c, 2), -days, rw])
    # 5. milestone label
    for k in ids:
        best = None
        r = R[k]
        keys = set(act[k])
        if not keys:     # inherited bill: label from the thread's bills
            for ti in x[k].get('t', []):
                keys |= {(b, th[ti][1]) for b in th[ti][0]}
        for key in sorted(keys):
            for e in bills_ev.get(key, {}).get('ev', []):
                if e[1] == 'other' and re.match(r'(?i)(suspense file|enrolled|inactive file|committee action)', e[2]):
                    continue       # clerical steps: no release marks them
                ed = _d(e[0])
                off = (r['d'] - ed).days if ed else None
                if off is None or off < -MS_AFTER or off > MS_BEFORE:
                    continue
                cand = (abs(off), RANK.get(e[1], 9), key[0], e[0])
                if best is None or cand < best[0]:
                    best = (cand, [key[0], e[0], e[1], e[2], off])
        if best:
            x[k]['m'] = best[1]
    # 6. people
    seen, pp, pidx = Counter(), [], {}
    for k in ids:
        for full, kind in R[k].get('names', []):
            t, nm = split_name(full)
            seen[nm] += 1
    order = sorted(seen, key=lambda n: (-seen[n], n))
    disp = {}
    for k in ids:
        for full, kind in R[k].get('names', []):
            t, nm = split_name(full)
            disp[nm] = (full, t, kind)     # latest title wins (date order)
    for n in order:
        pidx[n] = len(pp)
        pp.append([disp[n][1], n, disp[n][2], seen[n]])
    for k in ids:
        r = R[k]
        title, subj = r.get('title', ''), _subject(r.get('lead', ''))
        nn, jj = [], []
        for full, kind in r.get('names', []):
            t, nm = split_name(full)
            i = pidx[nm]
            if i in nn:
                continue
            nn.append(i)
            sur = re.escape(nm.split()[-1])
            if (re.search(rf"Gabriel\b[^.;:]{{0,60}}?(?:,|\band\b|&)[^.;:]{{0,40}}?\b{sur}\b|\b{sur}\b[^.;:]{{0,40}}?(?:,|\band\b|&)[^.;:]{{0,60}}?\bGabriel\b", title)
                    or (subj and re.search(rf"\b{sur}\b", subj))):
                jj.append(i)
        if nn:
            x[k]['n'] = nn
        if jj:
            x[k]['j'] = jj
    return {'th': th, 'x': {k: v for k, v in x.items() if v}, 'pp': pp}
