"""Press-release pickup block (Insights > Press releases). v3 = RELRULE-v1 (agent-relrule, 2026-10-27); v3.1 = RELTAB-v1
(agent-reltab, 2026-10-28): reads the split "Press releases" tab layout as well as the old one; block unchanged.
v3.2 = RELCOPIES-v2 (rp-copies, 2026-10-28): reads the renamed copy columns ("Copy story ID 1..2", was "Tracker release ID
1..2"); a release's copies = the Press release = Yes rows of those stories, which now also include near-copies of the
release text and wire reposts whose headline is the release title cut short (code/relcopy.py); block shape unchanged.

RELRULE-v1 (Sammy 2026-10-27: "Use the same standard for determine if something is a release as you do for a reprint"):
  a Coverage row carries an official release only when its saved text passes the reprint string-of-text rule against the
  release text (code/release_rule.py). The sheet task and agent-relrule keep the tab's Tracker release ID to exactly the
  stories whose rows pass; this block links releases ONLY through that column (plus REL for the 5 releases with no official
  posting). The curated REL table of v1/v2, the exact-title join and the headline auto-rule are retired.


build(cov, data, ctx) -> {"v":1, "rel":[...]} for <script id="ins-release_pickup">.

Which releases count (Sammy: "Gabriel's own/office/caucus releases"):
  Only Coverage rows with Press release = 'Yes', grouped into releases (one release = one or more
  Story IDs that carry the same release text). A release is IN when its issuer is
    o  Gabriel's Assembly office: release text distributed by the Assembly Democratic Caucus
       (asmdc.org; US Fed News / PublicNow header "California State Assembly Democratic Caucus
       issued...") or posted by an outlet verbatim, where Gabriel is the lead actor (his bill, his
       statement, his event). Joint releases where he is a named lead (e.g. with AG Bonta, with
       Asm. Nazarian) count.
    b  his office as Assembly Budget Committee chair (budget statements; ACA 20 rainy-day fund).
    c  the California Legislative Jewish Caucus, from Nov 2020 (when he became chair; co-chair
       2023-25, chair again 2026). Earlier caucus releases were led by Sen. Allen -> out.
  OUT: the Governor's, Attorney General's, other members' or caucus-wide releases that merely list
  his bill; advocacy-group releases (EWG, Consumer Reports, Everytown, JPAC / Jewish California,
  CAA, SWC...), corporate/PR-wire releases that mention him.
  Classification was done by reading each release's text (Oct 27, 2026); the curated table below
  is authoritative for every Press-release story that existed then (REVIEWED). Press-release rows
  in stories added later are auto-included only when the headline names him
  ('Assemblymember/Asm./Budget Chair [Jesse] Gabriel') or the Legislative Jewish Caucus -> flag a=1.
Release date = earliest dated row of the release (wire copy usually runs the same day).
Follow-up original reporting is computed in the browser from D (same bill, else same issue, 0-7 days).

RELEASES-v2 (2026-10-27, Sammy: the official "Press releases" tab is plugged in everywhere):
  The workbook's "Press releases" tab (official releases from gabriel.asmdc.org and the Jewish Caucus site) is the
  authority for which Press-release stories are releases and for their official date, title and URL:
  - scope: Gabriel's office rows always; Jewish Caucus rows only from his chair tenure (Date >= 2020-11-18) - Sammy
    2026-10-27 "2 no": pre-tenure caucus releases don't count even when they name him (rows stay on the tab, noted).
  - a tab row's "Tracker release ID" ("sNNNNN" or "sNNNNN; sNNNNN") links it to Press-release stories; a REL group with
    one of those stories takes the official URL/date/title; otherwise the stories become a release with the issuer
    from the tab (Jewish Caucus -> c; "Budget Chair" in the title -> b; else o). This is what brings in the 15
    releases of Sammy's "1 yes" (14 newly flagged stories + s01893, AB 2020, which the review had left out).
  - Press-release stories after the review that match an in-scope official title exactly (normalized) join it too.
  - official releases with no Press-release story are listed with no runs ("No pickup found").
  Release date = the official date when linked, else the earliest run. Block v2 adds per release
  [url, official title, source code] and "src"/"n_off"/"n_scope" counts.
"""
import re
from collections import Counter
TENURE = "2020-11-18"   # Jewish Caucus chair from this date (co-chair 2023-26, chair 2026)

# key: [story ids], issuer, bills (None = use sheet Bills column), issue (None = sheet Topic)
REL = [   # RELRULE-v1: only the releases with no official posting (no official text to test); every other release is
          # linked through the "Press releases" tab's Tracker release ID, which the release text rule maintains
    (["s02061"], "c", [], "Antisemitism / Jewish community"),
    (["s02140"], "c", [], "Antisemitism / Jewish community"),
    (["s02158"], "c", [], "Antisemitism / Jewish community"),
    (["s02549"], "c", ["AB 715"], "Antisemitism / Jewish community"),
    (["s03045"], "o", [], "Antisemitism / Jewish community"),
]

# RELRULE-v1: the headline auto-rule (AUTO_HL) and the exact-title join are gone: a story joins an official release only
# through the tab's Tracker release ID (set by the release text rule, release_rule.py).


def _date(s):
    s = (s or "").strip()[:10]
    return s if re.match(r"^\d{4}-\d{2}-\d{2}$", s) else ""


def _title(rows):
    """Headline of the earliest row, preferring one that is not ALL CAPS / not truncated."""
    hs = [(r["date"] or "9999", (r["hl"] or "").strip()) for r in rows if (r["hl"] or "").strip()]
    hs.sort()
    def good(h):
        letters = [c for c in h if c.isalpha()]
        upper = letters and sum(c.isupper() for c in letters) / len(letters) > 0.8
        return not upper and "..." not in h and not h.endswith("…")
    for _, h in hs:
        if good(h):
            return h
    if hs:
        h = hs[0][1]
        return h.title() if h.isupper() else h
    return ""


def _bills(s):
    out = []
    for b in re.split(r"[;,]\s*", s or ""):
        b = b.strip()
        if b and b not in out:
            out.append(b)
    return out


def _norm(t):
    return re.sub(r"[^a-z0-9]+", " ", str(t or "").lower().replace("\u2019", "'")).strip()


def _tab_rows(df):
    """RELTAB-v1 (agent-reltab 2026-10-28): the tab's rows as dicts with the OLD column names, from either layout. The new
    layout (code/reltab.py) has one value per cell: Bill 1..6 + "Bills (more)", Tracker release ID 1..2, Source = one site
    plus "Also on caucus site (URL)", Date a real date (read_sheet gives "YYYY-MM-DD 00:00:00")."""
    cols = list(df.columns)
    # RELCOPIES-v2 (rp-copies 2026-10-28): "Tracker release ID 1..2" renamed "Copy story ID 1..2"; both names read
    tid = "Copy story ID" if "Copy story ID 1" in cols else "Tracker release ID"
    new = "Bill 1" in cols and (tid + " 1") in cols
    out = []
    for _, r in df.iterrows():
        g = lambda c: "" if str(r.get(c, "")).strip().lower() == "nan" else str(r.get(c, "") if r.get(c, "") is not None else "").strip()
        if not new:
            out.append({c: g(c) for c in cols}); continue
        num = lambda p, n, more: [x for x in [g(f"{p} {i}") for i in range(1, n + 1)] if x] + [x.strip() for x in g(more).split(";") if x.strip()]
        src = g("Source") + ("; Jewish Caucus" if g("Also on caucus site (URL)") and "caucus" not in g("Source").lower() else "")
        d = {c: g(c) for c in cols}
        d.update({"Source": src, "Date": g("Date")[:10], "Bills mentioned": "; ".join(num("Bill", 6, "Bills (more)")),
                  "Tracker release ID": "; ".join(x for x in (g(tid + " 1"), g(tid + " 2")) if x)})
        out.append(d)
    return out


def official(ctx):
    """In-scope rows of the "Press releases" tab: [{date,title,url,iss,bills,topic,sids,quoted,source}], plus counts."""
    rs = (ctx or {}).get("read_sheet")
    df = rs("Press releases") if rs else None
    if df is None or not len(df) or "URL" not in df.columns:
        return None, 0
    out = []
    for r in _tab_rows(df):                # RELTAB-v1: old or new tab layout
        src, d = str(r.get("Source", "")).strip(), _date(str(r.get("Date", "")))
        office, caucus = "office" in src.lower(), "caucus" in src.lower()
        if caucus and not office and d < TENURE:
            continue                      # pre-tenure caucus release: out of scope (Sammy 2026-10-27)
        title = str(r.get("Title", "")).strip()
        iss = "c" if caucus and not office else ("b" if re.search(r"budget chair", title, re.I) else "o")
        sids = [x.strip() for x in re.split(r"[;,\s]+", str(r.get("Tracker release ID", ""))) if re.match(r"^s\d{5}$", x.strip())]
        out.append({"date": d, "title": title, "url": str(r.get("URL", "")).strip(), "iss": iss,
                    "bills": _bills(str(r.get("Bills mentioned", ""))), "topic": str(r.get("Issue", "")).strip(), "sids": sids,
                    "prid": str(r.get("Release ID", "") or "").strip()})   # RELCOPIES-v1: the tab's Release ID
    official.known = sorted(str(u).strip() for u in df["URL"] if str(u).strip())   # every tab URL (incl. out of scope)
    # RELBUTTON-v1 (backend #6, rp-final 2026-10-28): a dual-posted release's caucus URL is known too (41 relKnown never re-finds it)
    ac = "Also on caucus site (URL)"
    if ac in df.columns:
        official.known = sorted(set(official.known) | {str(u).strip() for u in df[ac]
                                                       if str(u).strip() and str(u).strip().lower() not in ("nan", "none")})
    return out, len(df)


def build(cov, data, ctx):
    need = ["Article ID", "Story ID", "Original or reprint", "Date", "Outlet", "Headline", "Bills", "Topic", "Press release"]
    for c in need:
        if c not in cov.columns:
            return None
    pr = cov[cov["Press release"].astype(str).str.strip().str.lower() == "yes"]
    by_sid = {}
    for _, r in pr.iterrows():
        sid = str(r["Story ID"]).strip()
        if not sid:
            continue
        by_sid.setdefault(sid, []).append({
            "aid": str(r["Article ID"]).strip(), "outlet": str(r["Outlet"]).strip(),
            "date": _date(r["Date"]), "kind": "R" if str(r["Original or reprint"]).startswith("Reprint") else "O",
            "hl": str(r["Headline"]).strip(), "bills": str(r["Bills"]).strip(), "topic": str(r["Topic"]).strip(),
        })

    groups = []
    used = set()
    for sids, iss, bills, topic in REL:
        rows = [x for s in sids for x in by_sid.get(s, [])]
        used.update(sids)
        if rows:
            groups.append((sids, iss, bills, topic, rows, 0))
    # RELEASES-v2: the official tab links stories to releases (and brings in its listed stories)
    off, n_tab = official(ctx)
    link = {}                              # group index -> official row
    if off:
        gi = {sid: i for i, g in enumerate(groups) for sid in g[0]}
        for o in off:
            hit = [gi[x] for x in o["sids"] if x in gi]
            if hit:
                link.setdefault(hit[0], o); continue
            rows = [x for sd in o["sids"] for x in by_sid.get(sd, [])]
            if rows:
                used.update(o["sids"]); groups.append((sorted(o["sids"]), o["iss"], o["bills"] or None, o["topic"] or None, rows, 0))
                gi.update({sd: len(groups) - 1 for sd in o["sids"]}); link[len(groups) - 1] = o
    rel = []
    for gidx, (sids, iss, bills, topic, rows, auto) in enumerate(groups):
        o = link.get(gidx)
        if bills is None:
            bills = []
            for x in rows:
                for b in _bills(x["bills"]):
                    if b not in bills:
                        bills.append(b)
        if topic is None:
            tc = Counter(x["topic"] for x in rows if x["topic"] and x["topic"] != "None")
            topic = tc.most_common(1)[0][0] if tc else ""
        dates = sorted(x["date"] for x in rows if x["date"])
        d0 = dates[0] if dates else ""
        # one entry per row: [aid, outlet, date, kind]; sorted by date then outlet
        rr = sorted(([x["aid"], x["outlet"], x["date"], x["kind"]] for x in rows),
                    key=lambda t: (t[2] or "9999", t[1].lower(), t[0]))
        title = _title(rows)
        if o:                                  # official date, title, URL win
            d0, title = o["date"] or d0, o["title"] or title
        rel.append([sids[0], d0, iss, title, sorted(bills, key=lambda b: (len(b), b)), topic, auto, sorted(sids), rr,
                    o["url"] if o else "", 1 if o else 0, o.get("prid", "") if o else ""])
    linked = {id(o) for o in link.values()}
    for k, o in enumerate(sorted((o for o in (off or []) if id(o) not in linked), key=lambda o: (o["date"], o["url"]))):
        rel.append(["off%03d" % k, o["date"], o["iss"], o["title"], sorted(o["bills"], key=lambda b: (len(b), b)), o["topic"], 0, [], [], o["url"], 1, o.get("prid", "")])
    rel.sort(key=lambda t: (t[1] or "0000", t[0]), reverse=True)
    return {"v": 2, "cols": ["key", "date", "iss", "title", "bills", "topic", "auto", "sids", "rows", "url", "official", "prid"],
            "rowcols": ["aid", "outlet", "date", "kind"], "rel": rel, "src": "sheet:Press releases" if off else "",
            "n_tab": n_tab, "n_scope": len(off or []), "tenure": TENURE,
            "known": sorted(set(getattr(official, "known", [])) - {o["url"] for o in (off or [])}) if off else []}


if __name__ == "__main__":  # local check: python3 release_pickup_data.py XLSX OUT.json
    import sys, json
    import pandas as pd
    cov = pd.read_excel(sys.argv[1], sheet_name="Coverage", dtype=str).fillna("")
    out = build(cov, [], {"read_sheet": lambda n: pd.read_excel(sys.argv[1], sheet_name=n, dtype=str).fillna("")})
    s = json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    open(sys.argv[2], "w").write(s)
    print(len(out["rel"]), "releases,", len(s), "bytes")
