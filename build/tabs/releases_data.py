"""TABS-v1 block tab-releases (agent-tab-releases, 2026-10-27): what the Press releases tab needs that ins-release_pickup
does not carry yet.

build(cov, data, ctx) -> {"v":1,
  "r": {official URL -> [release type, Gabriel quoted (Yes/No/''), dek, source code, co-issuers, word count]},
  "c": {Article ID -> [headline, publisher link, NewsBank article link, ProQuest link (CSL form if the sheet has it), Story ID]}}
- r: every row of the sheet's "Press releases" tab (in or out of scope; the module only looks up the URLs that
  ins-release_pickup lists). Source code: 'o' Gabriel's office only, 'c' Jewish Caucus only, 'oc' both sites.
- c: the Coverage rows with Press release = Yes of the stories that carry one of his releases: the tab's Tracker release
  ID plus NO_POSTING (the 5 releases with no official posting, = release_pickup_data.py REL; release copies are not tracker stories, so data.json has no headline or
  links for them). Links are raw sheet values; the tracker's linksOf() turns them into NewsBank/ProQuest via the CA State
  Library and drops NewsBank print pages, as it does for live finds.
Phase B: when agent-tabs appends type / quoted / dek / source columns to ins-release_pickup, the module reads those first
and this block can shrink to "c" (or go away if the copies' headlines and links are appended too).
RELRELATED-v1 (agent-relrelated 2026-10-28): "rel": {Release ID (prNNNNN; the 5 no-posting releases: their Story-ID key) ->
  [[Story ID, evidence type, days after the release], ...]} from release_related.json (code/relmatch.py's state file: the
  pipeline folder next to build_data.py, or <lib>/code), rows of stories not in this build's data dropped. The release page
  renders ONLY these as its related stories (type 'possible' = the collapsed "Possibly related" section).
RELTHREAD-v1 (rp-threads 2026-10-28): "thr": {"th", "x", "pp"} = code/relthread.py build() (release threads on a bill +
  session incl. renumbered / inherited bills, follow-up and similar-text pairs, milestone label, Others named / Joint with
  people). Shape: build/relplan_contract.md "rp-threads". Inputs: the tab rows, the "Bills" tab (or bill_milestones.json via
  bill_timeline_data.py), release_texts.json; relthread.py / bill_timeline_data.py are found next to the pipeline or in <lib>.
RELRECS-v1 (2026-11-02): "nw": [outlet display names] whose type in code/outlets.json is wire, distributor, prservice or aggregator
  (the page's "Picked up" leaves their related stories and copies out, FINDINGS definition D).
RELUI-v1 (rp-ui 2026-10-28, RELPLAN phase 2 + backend review #8/#9/#10):
- "rules": the ONE rules table the page's labels and ⓘ tooltips are drawn from (no thresholds typed in releases.js):
  {"t": {type: [tier, label, tag, how]}, "copy": how, "bc": [before_from, before_to, after_from, after_to], "bch": how,
  "tenure": iso}.
  label = relmatch.LABEL, tier = relmatch.TIER (1 related, 2 possibly related, 3 later coverage); tag = the row tag; how = a
  sentence built from relmatch / release_rule / relcopy / reprint_rule constants. Absent when relmatch.py can't be loaded.
- "bc": {release key -> [before, after, after_not_linked]}: tracker stories on one of the release's bills dated in the
  rules' bc windows (relmatch's: before = -7..-2, after = BILL_WIN -1..+7; the old browser count was -7..-1 / 0..+7 and
  double-counted lag -1 stories). after_not_linked = after minus the release's related / possibly related / copy stories.
- r[url][4] (co-issuers string) is emptied when "thr" carries the people (thr.x.n / pp): saves ~12 KB.
- _tab_rows reads the RELTAB-v3 names ("Copy story ID 1/2", "Has copies", "Copies (rows)") and the old ones
  (reltab.col / reltab.RENAMED when reltab.py is next to the pipeline or in <lib>/code; else the two names literally).
Deterministic (sorted keys via tabs_data.py), pandas + standard library, no network, no writes."""
import json, os, re
NO_POSTING = {"s02061", "s02140", "s02158", "s02549", "s03045"}   # release_pickup_data.py v3 REL (keep in step)


def _s(v):
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()


def _tab_rows(df):
    """RELTAB-v1 (agent-reltab 2026-10-28): the tab's rows as dicts with the OLD column names, from either layout (new layout:
    code/reltab.py; names in Legislator 1..6 / Legislators (more) / Other official 1..4 / Other officials (more), re-joined
    "; " legislators first; Source + "Also on caucus site (URL)"). RELUI-v1: copy story IDs from "Copy story ID 1..2"
    (RELTAB-v3) or "Tracker release ID 1..2" (before the rename)."""
    cols = list(df.columns)
    rt = _reltab()
    cid = [(f"{rt.COPY_ID} {i}" if rt else f"Copy story ID {i}") for i in (1, 2)]
    pick = lambda name: name if name in cols else ((rt.RENAMED_BACK.get(name) or rt.RENAMED.get(name)) if rt else
                                                   {"Copy story ID 1": "Tracker release ID 1", "Copy story ID 2": "Tracker release ID 2"}.get(name))
    ccols = [c for c in (pick(n) for n in cid) if c and c in cols]
    if not ("Bill 1" in cols and ccols):
        return [dict(x) for _, x in df.iterrows()]
    out = []
    for _, x in df.iterrows():
        g = lambda c: _s(x.get(c, "")) if _s(x.get(c, "")).lower() != "nan" else ""
        num = lambda p, n, more: [v for v in [g(f"{p} {i}") for i in range(1, n + 1)] if v] + [v.strip() for v in g(more).split(";") if v.strip()]
        d = {c: g(c) for c in cols}
        d["Source"] = g("Source") + ("; Jewish Caucus" if g("Also on caucus site (URL)") and "caucus" not in g("Source").lower() else "")
        d["Co-issuers / other members named"] = "; ".join(num("Legislator", 6, "Legislators (more)") + num("Other official", 4, "Other officials (more)"))
        d["Tracker release ID"] = "; ".join(v for v in (g(c) for c in ccols) if v)
        out.append(d)
    return out


_RT = []


def _reltab():
    """code/reltab.py (pipeline root or <lib>/code), loaded once; None when absent"""
    if not _RT:
        here = os.path.dirname(os.path.abspath(__file__))
        _RT.append(_load("reltab", [os.path.join(os.path.dirname(here), "reltab.py"),
                                    os.path.join(os.path.dirname(os.path.dirname(here)), "code", "reltab.py")]))
    return _RT[0]


def build(cov, data, ctx):
    rs = (ctx or {}).get("read_sheet")
    df = rs("Press releases") if rs else None
    r, sids = {}, set(NO_POSTING)
    if df is not None and len(df) and "URL" in df.columns:
        for x in _tab_rows(df):            # RELTAB-v1: old or new tab layout
            url = _s(x.get("URL", ""))
            if not url:
                continue
            src = _s(x.get("Source", "")).lower()
            code = ("o" if "office" in src else "") + ("c" if "caucus" in src else "")
            sids.update(t for t in re.split(r"[;,\s]+", _s(x.get("Tracker release ID", ""))) if re.match(r"^s\d{5}$", t))
            q = _s(x.get("Gabriel quoted", ""))
            r[url] = [_s(x.get("Release type", "")), q if q in ("Yes", "No") else "", _s(x.get("Subtitle/dek", "")), code,
                      _s(x.get("Co-issuers / other members named", "")), _s(x.get("Word count", "")),
                      # RELCOPIES-v1: [6] Release ID, [7] the saved copy's file name (Saved Copy? = Yes)
                      _s(x.get("Release ID", "")), _s(x.get("File name", "")) if _s(x.get("Saved Copy?", "")).lower() == "yes" else ""]
    c = {}
    if "Press release" in cov.columns and "Article ID" in cov.columns:
        pr = cov[cov["Press release"].astype(str).str.strip().str.lower() == "yes"]
        for _, x in pr.iterrows():
            aid = _s(x.get("Article ID", ""))
            if not aid or _s(x.get("Story ID", "")) not in sids:
                continue
            pq = _s(x.get("ProQuest via CA State Library", "")) or _s(x.get("ProQuest link", ""))
            c[aid] = [_s(x.get("Headline", "")), _s(x.get("Publisher link", "")), _s(x.get("NewsBank article link", "")), pq, _s(x.get("Story ID", ""))]
    rel = _related(data, ctx)
    thr = _threads(df, cov, ctx)
    if not r and not c and not rel and not thr:
        return None
    if thr and thr.get("pp"):   # RELUI-v1: the page reads Others named from thr (people table); the string is not needed
        for v in r.values():
            v[4] = ""
    rules, mods = _rules(ctx)
    out = {"v": 1, "r": r, "c": c}
    if rel:
        out["rel"] = rel
    if thr:
        out["thr"] = thr
    nw = _nonpick_outlets(ctx)
    if nw:
        out["nw"] = nw
    if rules:
        out["rules"] = rules
        bc = _bill_cov(df, cov, data, rel, sids, rules["bc"], {k: set(v.get("bg") or []) for k, v in ((thr or {}).get("x") or {}).items()})
        if bc:
            out["bc"] = bc
    return out


NONPICK_TYPES = ("wire", "distributor", "prservice", "aggregator")   # FINDINGS definition D: these outlet types are not a pickup


def _nonpick_outlets(ctx):
    """RELRECS-v1 (R1): the outlets whose stories and copies do not count as "Picked up" (FINDINGS definition D): the display names
    in code/outlets.json whose type is wire, distributor, prservice or aggregator. The page matches them against ctx.outlet(...)."""
    here = os.path.dirname(os.path.abspath(__file__))
    lib = (ctx or {}).get("lib", "") or os.path.dirname(os.path.dirname(here))
    for p in (os.path.join(os.path.dirname(here), "outlets.json"), os.path.join(lib, "code", "outlets.json")):
        if os.path.exists(p):
            try:
                recs = json.load(open(p, encoding="utf-8")).get("records", {})
            except Exception:
                return []
            return sorted({_s(v.get("name")) for v in recs.values() if isinstance(v, dict) and v.get("type") in NONPICK_TYPES and _s(v.get("name"))})
    return []


def _load(name, rel_paths):
    import importlib.util
    for p in rel_paths:
        if p and os.path.exists(p):
            spec = importlib.util.spec_from_file_location(name, p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
    return None


def _threads(df, cov, ctx):
    """RELTHREAD-v1: inputs for code/relthread.py; None when the module or the tab is missing"""
    here = os.path.dirname(os.path.abspath(__file__))
    up, lib = os.path.dirname(here), ((ctx or {}).get("lib", "") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    rt = _load("relthread", [os.path.join(up, "relthread.py"), os.path.join(lib, "code", "relthread.py")])
    bt = _load("bill_timeline_data", [os.path.join(up, "insights", "bill_timeline_data.py"),
                                       os.path.join(lib, "build", "insights", "bill_timeline_data.py")])
    if rt is None or df is None or not len(df) or "Release ID" not in df.columns:
        return None
    bev = {}
    if bt is not None:
        rs = (ctx or {}).get("read_sheet")
        bdf = rs("Bills") if rs else None
        if bdf is not None and len(bdf):
            bev = bt._rows_from_sheet(bdf)
        if not bev:
            p = next((q for q in (os.path.join(lib, "work", "out", "bill_milestones.json"),
                                  os.path.join(up, "insights", "bill_milestones.json")) if os.path.exists(q)), "")
            if p:
                bev = bt._rows_from_json(json.load(open(p, encoding="utf-8")))
    texts = {}
    for p in (os.path.join(up, "release_texts.json"), os.path.join(lib, "code", "release_texts.json")):
        if os.path.exists(p):
            try:
                texts = json.load(open(p, encoding="utf-8")).get("rel", {})
            except Exception:
                texts = {}
            break
    rels, body = [], {}
    for x in df.to_dict("records"):
        g = lambda k: _s(x.get(k, "")) if _s(x.get(k, "")).lower() != "nan" else ""
        pid = g("Release ID")
        if not pid or g("In scope") == "No":
            continue
        bills = [g(f"Bill {i}") for i in range(1, 7) if g(f"Bill {i}")] + [v.strip() for v in g("Bills (more)").split(";") if v.strip()]
        names = [(g(f"Legislator {i}"), "l") for i in range(1, 7) if g(f"Legislator {i}")] + \
                [(v.strip(), "l") for v in g("Legislators (more)").split(";") if v.strip()] + \
                [(g(f"Other official {i}"), "o") for i in range(1, 5) if g(f"Other official {i}")] + \
                [(v.strip(), "o") for v in g("Other officials (more)").split(";") if v.strip()]
        t = (texts.get(g("URL")) or {}).get("body", "") if isinstance(texts.get(g("URL")), dict) else ""
        lead = next((s for s in re.split(r"\n+|(?<=[.!?])\s+(?=[A-Z“\"])", t) if len(s.split()) >= 6), "")[:400]
        rels.append({"id": pid, "date": g("Date")[:10], "title": g("Title"), "bills": bills, "names": names, "lead": lead})
        if t:
            body[pid] = t
    # the 5 no-posting releases: their Coverage Original row (date, headline, Bills cell); no text, no names
    if "Story ID" in cov.columns:
        for sid in sorted(NO_POSTING):
            o = cov[(cov["Story ID"].astype(str) == sid) & (cov["Original or reprint"].astype(str) == "Original")] \
                if "Original or reprint" in cov.columns else cov[cov["Story ID"].astype(str) == sid]
            if len(o):
                y = o.iloc[0]
                rels.append({"id": sid, "date": _s(y.get("Date", ""))[:10], "title": _s(y.get("Headline", "")),
                             "bills": [b.strip() for b in _s(y.get("Bills", "")).split(";") if b.strip()], "names": [], "lead": ""})
    if not rels:
        return None
    return rt.build(rels, bev, body)


def _related(data, ctx):
    """RELRELATED-v1: the matcher's state, filtered to stories in this build"""
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [os.environ.get("RELRELATED_JSON", ""), os.path.join(os.path.dirname(here), "release_related.json"),
             os.path.join(((ctx or {}).get("lib", "") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "code", "release_related.json")]
    for p in cands:
        if p and os.path.exists(p):
            try:
                st = json.load(open(p, encoding="utf-8")).get("rel", {})
            except Exception:
                return {}
            ids = {d.get("id") for d in (data or []) if isinstance(d, dict)}
            return {k: [x for x in v if not ids or x[0] in ids] for k, v in st.items() if any(not ids or x[0] in ids for x in v)}
    return {}



# ---------------------------------------------------------------- RELUI-v1: the rules table and the bill-coverage counts
TAG = {"text": "Used release text", "nearcopy": "Ran it, edited", "quote": "Quoted it", "bill": "Same bill",
       "topic": "Same subject", "pre": "Before release", "anchor": "Same announcement", "possible": "Not checked",
       "later": "Later, same bill", "laterquote": "Later quote", "roundup": "Roundup", "subject": "Similar subject"}   # v23   # the row tag (one word or two; the rest is generated)


def _win(w):
    """(-1, 90) -> "1 day before to 90 days after"; (8, 30) -> "8 to 30 days after"; (-14, -1) -> "1 to 14 days before" """
    a, b = w
    dd = lambda n: f"{abs(n)} day{'s' if abs(n) != 1 else ''}"
    if a < 0 and b < 0:
        return f"{abs(b)} to {dd(a)} before"
    if a > 0:
        return f"{a} to {dd(b)} after"
    if a == 0:
        return f"the release day to {dd(b)} after"
    return f"{dd(a)} before to {dd(b)} after"


def _rules(ctx):
    """-> (rules dict, modules) from relmatch.py (+ release_rule / relcopy / reprint_rule for the copy rule); (None, None) when
    relmatch.py is not found. Every number below comes from those modules."""
    here = os.path.dirname(os.path.abspath(__file__))
    up, lib = os.path.dirname(here), ((ctx or {}).get("lib", "") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    cand = lambda n: [os.path.join(up, n), os.path.join(lib, "code", n)]
    import sys
    for d in (up, os.path.join(lib, "code")):
        if os.path.exists(os.path.join(d, "relmatch.py")) and d not in sys.path:
            sys.path.insert(0, d)
            break
    try:
        rm = _load("relmatch", cand("relmatch.py"))
    except Exception:
        rm = None
    if rm is None or not hasattr(rm, "TIER"):
        return None, None
    try:
        rr = _load("release_rule", cand("release_rule.py"))
        rc = _load("relcopy", cand("relcopy.py"))
        rp = _load("reprint_rule", cand("reprint_rule.py"))
    except Exception:
        rr = rc = rp = None
    g = lambda m, k, dflt: getattr(m, k, dflt) if m is not None else dflt
    W = lambda k, dflt: g(rm, k, dflt)
    how = {
        "text": f"shares passages of {W('RUN', 25)} or more identical words with it, dated {_win(W('TEXT_WIN', (-1, 90)))}",
        "nearcopy": f"{round(100 * W('NEAR_SHARE', 0.6))}% or more of the story is the release's own text",
        "quote": f"quotes at least {W('QMIN', 20)} words of it, dated {_win(W('QUOTE_WIN', (-1, 30)))}",
        "bill": f"carries one of its bills and is on its subject, dated {_win(W('BILL_WIN', (-1, 7)))}, or {_win(W('WAVE_WIN', (8, 30)))} when no newer release on the bill came out in between",
        "topic": f"a close match on subject that names Gabriel and shares a bill or a rare name with it, dated {_win(W('BILL_WIN', (-1, 7)))}",
        "roundup": f"uses its text (passages of {W('RUN', 25)} or more identical words) inside a roundup, newsletter or column whose headline and opening are on other subjects",
        "subject": f"a close match on subject that names Gabriel but shares no bill or rare name with it, dated {_win(W('BILL_WIN', (-1, 7)))}; not checked",
        "pre": f"reported the same announcement before it went out, dated {_win(W('PRE_WIN', (-14, -1)))}",
        "anchor": f"names the release's rare names and figures, dated {_win(W('ANCHOR_WIN', (0, 7)))}",
        "possible": f"same bill, dated {_win(W('BILL_WIN', (-1, 7)))}; the subject could not be checked (not in English, or no saved text)",
        "later": f"same bill and session, dated {_win(W('LATER_WIN', (8, 30)))}, before the next release on the bill",
        "laterquote": f"quotes at least {W('LQ_LONG', 20)} words of it, more than {W('LQ_MIN_LAG', 8) - 1} days after",
    }
    t = {k: [rm.TIER[k], rm.LABEL.get(k, k), TAG.get(k, rm.LABEL.get(k, k)), how.get(k, "")] for k in sorted(rm.TIER)}
    K, RW = g(rr, "K", 25), g(rr, "REL_WINDOW", (-1, 30))
    copy = (f"printed the release itself: runs of {K} or more identical words covering {round(100 * g(rp, 'THR', 0.9))}% of both "
            f"texts, or {round(100 * g(rc, 'NEAR_REL', 0.5))}% of a release of {g(rc, 'MIN_REL_WORDS', 250)}+ words, "
            f"dated {_win(RW)}; also release-wire reposts of its title ({', '.join(g(rc, 'WIRE_OUTLETS', ('PublicNow',)))})")
    bw = W("BILL_WIN", (-1, 7))
    rt = _reltab()
    bc = [-bw[1], bw[0] - 1, bw[0], bw[1]]
    bch = (f"every tracker story on the bill, not only the ones tied to this release: before = dated {_win(bc[:2])}, after = "
           f"dated {_win(bc[2:])}; not linked = the after stories that are not this release's related, possibly related or copy stories")
    return {"t": t, "copy": copy, "bc": bc, "bch": bch, "tenure": g(rt, "TENURE", "")}, rm


def _bill_cov(df, cov, data, rel, copy_sids, bc, bg=None):
    """{release key: [before, after, after_not_linked]} on the release's bills (tab Bill 1..6 / Bills (more); the no-posting
    releases: their Coverage Bills cell), tracker stories dated to the day only"""
    import datetime as dt
    day = lambda s: dt.date.fromisoformat(s[:10]) if s and len(s) >= 10 and re.match(r"\d{4}-\d\d-\d\d", s) else None
    by_bill = {}
    for d in data or []:
        if not isinstance(d, dict) or d.get("prec") != "day" or not day(d.get("date", "")):
            continue
        for b in d.get("bills") or []:
            by_bill.setdefault(b, []).append((day(d["date"]), d.get("id")))
    rels = []
    if df is not None and len(df) and "Release ID" in df.columns:
        for x in df.to_dict("records"):
            g = lambda k: _s(x.get(k, "")) if _s(x.get(k, "")).lower() != "nan" else ""
            if not g("Release ID"):
                continue
            bills = [g(f"Bill {i}") for i in range(1, 7) if g(f"Bill {i}")] + [v.strip() for v in g("Bills (more)").split(";") if v.strip()]
            rels.append((g("Release ID"), g("Date")[:10], bills))
    if "Story ID" in cov.columns:
        for sid in sorted(NO_POSTING):
            o = cov[cov["Story ID"].astype(str) == sid]
            if "Original or reprint" in cov.columns:
                o = o[o["Original or reprint"].astype(str) == "Original"]
            if len(o):
                y = o.iloc[0]
                rels.append((sid, _s(y.get("Date", ""))[:10], [b.strip() for b in _s(y.get("Bills", "")).split(";") if b.strip()]))
    out = {}
    for key, date, bills in rels:
        bills = [b for b in bills if b not in (bg or {}).get(key, ())]   # rp-final: background bills (thr x.bg) are not "that week's" coverage
        d0 = day(date)
        if not d0 or not bills:
            continue
        linked = {x[0] for x in (rel or {}).get(key, [])} | copy_sids
        pre, post = set(), set()
        for b in bills:
            for d, sid in by_bill.get(b, []):
                g = (d - d0).days
                if bc[0] <= g <= bc[1]:
                    pre.add(sid)
                elif bc[2] <= g <= bc[3]:
                    post.add(sid)
        out[key] = [len(pre), len(post), len(post - linked)]
    return out
