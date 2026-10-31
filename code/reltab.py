"""RELTAB-v1 (agent-reltab, 2026-10-28; Sammy: "clean up the press release tab ... split the data with multiple things in
one column"). Layout of the workbook's "Press releases" tab, one value per cell, and the helpers every reader and writer uses:

  COLS                the tab's columns in order (CONTRACT.md "Press releases tab layout (RELTAB-v1)")
  split_names(s, d)   a packed "Co-issuers / other members named" string -> (legislators, others), cleaned + canonical
  officials(text)     names with titles found in a release's text (RELCHECK appends; same extractor the tab was built with)
  row_values(...)     a new release -> {column: value} in the RELTAB-v1 layout (RELCHECK-v3)
  legacy(get)         any tab row (old 16-column or RELTAB-v1 layout) -> the OLD column names and joined values, so code
                      written against the old layout keeps working: Source, Bills mentioned, Co-issuers / other members
                      named, Contact, Tracker release ID, Note
  ids(get) / set_ids  the copy Story IDs of a row (either layout) / write them back (RELCHECK-v2 _rel_mark)
  col(H, name)        RELCOPIES-v2: a column's position under its current name or its pre-2026-10-28 name (RENAMED)
  related_values(...) RELCOPIES-v2: the derived "Related count" / "Related story IDs" cells of a release (release_related.json)
  first_copy_date(..) RELCOPIES-v2: the "First copy date (if different)" cell, recomputed from the copies

Standard library only; no network."""
import datetime as _dt
import re

TENURE = "2020-11-18"
OFFICE = "Gabriel's office (gabriel.asmdc.org)"
CAUCUS = "California Legislative Jewish Caucus"
N_LEG, N_OTH, N_BILL, N_TID = 6, 4, 6, 2

# RELCOPIES-v2 (rp-copies, 2026-10-28; Sammy approved the backend review #8/#11): copies of a release are not tracker
# stories, so the tab's tracker-era column names were renamed to what they hold today. Readers use these names; col() and
# is_new_layout() still accept the old ones (RENAMED) so a sheet staged before the rename keeps working.
HAS_COPIES, N_COPIES, FIRST_COPY = "Has copies", "Copies (rows)", "First copy date (if different)"
COPY_ID = "Copy story ID"                    # + " 1" .. " N_TID"
REL_N, REL_IDS = "Related count", "Related story IDs"   # derived from release_related.json, recomputed each build / Update
RENAMED = {"In tracker": HAS_COPIES, "Coverage stories linked": N_COPIES, "Tracker date (earliest pickup)": FIRST_COPY,
           "Tracker release ID 1": COPY_ID + " 1", "Tracker release ID 2": COPY_ID + " 2"}
RENAMED_BACK = {v: k for k, v in RENAMED.items()}
# RELBUTTON-v1 (rp-button, 2026-10-28): "Related" = relmatch's tier-1 types (RELRELATED-v3: text, nearcopy, quote, bill, topic,
# pre, anchor); tier 2 "possible" and tier 3 "later" / "laterquote" are not counted. Read from relmatch.TIER (one definition).
def _tier1():
    try:
        import relmatch as _RM
    except ImportError:                     # loaded by path (build/insights, build/tabs): relmatch.py sits next to this file
        import importlib.util as _iu, os as _os, sys as _sys
        _p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "relmatch.py")
        _d = _os.path.dirname(_p)
        if _d not in _sys.path:
            _sys.path.insert(0, _d)          # relmatch imports reprint_rule from the same folder
        _sp = _iu.spec_from_file_location("relmatch", _p)
        _RM = _iu.module_from_spec(_sp)
        _sp.loader.exec_module(_RM)
    return tuple(t for t, n in _RM.TIER.items() if n == 1)


RELATED_TYPES = _tier1()

# RELCOPIES-v1 (RELTAB-v2): "Release ID" (prNNNNN, permanent, first column) and the release's saved copy (Tracker library/
# Press releases/<year>/<prid>.html): "Saved Copy?" + "File name" after the official links
RELCOPY_COLS = ("Release ID", "Saved Copy?", "File name")
COLS = (["Release ID", "Date", "Title", "Subtitle/dek", "Source", "URL", "Also on caucus site (date)", "Also on caucus site (URL)",
         "Saved Copy?", "File name", "Release type", "In scope", "Issue", "Gabriel quoted", "Caucus release names Gabriel", "Word count"]
        + [f"Legislator {i}" for i in range(1, N_LEG + 1)] + ["Legislators (more)"]
        + [f"Other official {i}" for i in range(1, N_OTH + 1)] + ["Other officials (more)"]
        + ["Contact name", "Contact title", "Contact phone", "Contact email"]
        + [f"Bill {i}" for i in range(1, N_BILL + 1)] + ["Bills (more)"]
        + [HAS_COPIES] + [f"{COPY_ID} {i}" for i in range(1, N_TID + 1)]
        + [N_COPIES, FIRST_COPY, REL_N, REL_IDS, "Before text rule (In tracker / ID / runs)", "Note"])
DATE_COLS = ("Date", "Also on caucus site (date)", FIRST_COPY)
URL_COLS = ("URL", "Also on caucus site (URL)")
OLD_COLS = ["Date", "Title", "Subtitle/dek", "Source", "URL", "Release type", "Bills mentioned", "Issue", "Gabriel quoted",
            "Co-issuers / other members named", "Contact", "Word count", "In tracker", "Tracker release ID",
            "Coverage stories linked", "Note"]
WIDTHS = {"Release ID": 10, "Saved Copy?": 9, "File name": 16, "Date": 11, "Title": 60, "Subtitle/dek": 40, "Source": 24, "URL": 40, "Also on caucus site (date)": 12,
          "Also on caucus site (URL)": 30, "Release type": 15, "In scope": 8, "Issue": 24, "Gabriel quoted": 9,
          "Caucus release names Gabriel": 10, "Word count": 8, "Legislators (more)": 40, "Other officials (more)": 30,
          "Contact name": 16, "Contact title": 26, "Contact phone": 15, "Contact email": 28, "Bills (more)": 30,
          HAS_COPIES: 9, N_COPIES: 10, FIRST_COPY: 12, REL_N: 9, REL_IDS: 40,
          "Before text rule (In tracker / ID / runs)": 16, "Note": 70}
for _c in COLS:
    WIDTHS.setdefault(_c, 26 if _c.startswith(("Legislator", "Other official")) else (10 if _c.startswith("Bill ") else 11))

# ---------- names ----------
# exact tokens of the packed column (and of the extractor) -> canonical name; '' = not a person (dropped, logged)
CANON = {
    "Assembly Speaker Rendon": "Assembly Speaker Anthony Rendon", "Speaker Anthony Rendon": "Assembly Speaker Anthony Rendon",
    "Speaker Rivas": "Assembly Speaker Robert Rivas",
    "Speaker John Pérez": "Assembly Speaker John Pérez",
    "Senate President pro Tempore Atkins": "Senate President pro Tempore Toni Atkins",
    "Senate Pro Tem Toni Atkins": "Senate President pro Tempore Toni Atkins",
    "Assemblymember Bauer-Kahan": "Assemblymember Rebecca Bauer-Kahan", "Assemblymember Rebecca Bauer Kahan": "Assemblymember Rebecca Bauer-Kahan",
    "Assemblymember Juan Carillo": "Assemblymember Juan Carrillo", "Assemblymember Mike A. Gipson": "Assemblymember Mike Gipson",
    "Assemblymember Nonprofit Security Grant Program": "",
    "Attorney General Bonta": "Attorney General Rob Bonta",
    "Congresswoman Gabby Giffords": "Congresswoman Gabrielle Giffords",
    "Councilmember Martinez": "Councilmember Nury Martinez",
    "District Attorney Eric Nasarenko": "District Attorney Erik Nasarenko",
    "District Attorney Nathan J. Hochman": "District Attorney Nathan Hochman",
    "Governor Newsom": "Governor Gavin Newsom", "Governor Newson": "Governor Gavin Newsom",
    "Mayor Bass": "Mayor Karen Bass", "Mayor McCarthy": "Mayor Kevin McCarty",
    "Senator Arreguin": "Senator Jesse Arreguín", "Senator Valladeres": "Senator Suzette Martinez Valladares",
    "Senator Evan Bayh": "U.S. Senator Evan Bayh",
    "Speaker Emerita Pelosi": "Speaker Emerita Nancy Pelosi",
    "Superintendent Thurmond": "Superintendent of Public Instruction Tony Thurmond",
    "Superintendent Tony Thurmond": "Superintendent of Public Instruction Tony Thurmond",
    # run-ons of a list of titles ("Controller Malia Cohen Treasurer Fiona ...") -> the person, then the next title's person
    "Governor Gavin Newsom Lieutenant Governor": "Governor Gavin Newsom",
    "Secretary of State Shirley Weber Attorney General": "Secretary of State Shirley Weber",
    "Controller Malia Cohen Treasurer Fiona": "Controller Malia Cohen|Treasurer Fiona Ma",
    "Insurance Commissioner Ricardo Lara State Superintendent": "Insurance Commissioner Ricardo Lara",
}
# senators the extractor listed under a plural "Assemblymembers ..." (rows 2022-01-19, 2023-01-06; checked against the text)
SENATORS = {"Josh Becker", "Steve Glazer", "Bob Hertzberg", "Josh Newman", "Henry Stern", "Ben Allen", "Scott Wiener"}
LEG_RE = re.compile(r"^(Assemblymember|Senator|Assembly Speaker|Senate President pro Tempore|Assembly Majority Leader|Speaker pro Tem)\b")


def clean_name(tok):
    """one packed token -> list of canonical names (0, 1 or 2)"""
    t = re.sub(r"\s+", " ", str(tok or "")).strip()
    t = re.sub(r"^(Assemblymember|Senator)\s+(Assemblymembers?|Senators?)\s+", lambda m: ("Senator " if m.group(2).startswith("Senator") else m.group(1) + " "), t)
    t = re.sub(r"(?<=[^\W\d_]{2})\.\s.*$", "", t).rstrip(" .")                           # "Senator Evan Bayh. A", "Mayor Kevin McCarty. Protecting State"
    t = re.sub(r"^(Mayor Kevin McCarty) What Gun$", r"\1", t)               # sentence run-on ("... McCarty What Gun Violence ...")
    t = CANON.get(t, t)
    out = []
    for x in t.split("|"):
        m = re.match(r"^Assemblymember (.+)$", x)
        if m and m.group(1) in SENATORS:
            x = "Senator " + m.group(1)
        if x:
            out.append(x)
    return out


def is_legislator(name):
    return bool(LEG_RE.match(name)) and not name.startswith("U.S.")


def split_names(packed):
    """packed "a; b; c" -> (legislators, others), canonical, de-duplicated, original order"""
    leg, oth = [], []
    for tok in re.split(r";\s*", str(packed or "")):
        for n in clean_name(tok):
            lst = leg if is_legislator(n) else oth
            if n not in leg and n not in oth:
                lst.append(n)
    return leg, oth


# extractor (agent-releasecheck extract.py officials(), unchanged) for new releases
_NAME = r"[A-Z][^\W\d_]*(?:[.\'’\-][^\W\d_]+)*\.?"
_TITLES = (r"\b(Assemblymember|Assemblywoman|Assemblyman|Assembly Majority Leader|Assembly Speaker|Speaker pro Tem(?:pore)?|Speaker|"
           r"State Senator|Senator|Sen\.|Senate President pro Tempore|Senate Pro Tem|President pro Tempore|Lieutenant Governor|Lt\. Governor|Governor|Gov\.|"
           r"Attorney General|Mayor|Councilmember|Council Member|Supervisor|Congresswoman|Congressman|Representative|Rep\.|"
           r"Superintendent(?: of Public Instruction)?|Treasurer|Controller|Secretary of State|Insurance Commissioner|District Attorney)")
_TITLE_RE = re.compile(_TITLES + r"\s+(" + _NAME + r"(?:\s+(?:" + _NAME + r"|de|del|la)){0,3})")
_PLURAL = re.compile(r"\b(Assemblymembers|Senators|Assemblywomen|Assemblymen)\s+([^.;:“\"]{0,400})")
_BAD = {'Signing', 'Signs', 'AB', 'SB', 'Bill', 'Budget', 'Committee', 'Office', 'Chair', 'Pro', 'District', 'Says', 'Said',
        'Announces', 'Issues', 'Comments', 'Responds'}
_TNORM = {'Gov.': 'Governor', 'Sen.': 'Senator', 'Assemblywoman': 'Assemblymember', 'Assemblyman': 'Assemblymember',
          'State Senator': 'Senator', 'Lt. Governor': 'Lieutenant Governor', 'Council Member': 'Councilmember', 'Rep.': 'Representative',
          'Assemblymembers': 'Assemblymember', 'Assemblywomen': 'Assemblymember', 'Assemblymen': 'Assemblymember', 'Senators': 'Senator'}


def _clean(name):
    name = re.split(r"[’']s\b", name.strip())[0]
    name = re.split(r"\s+(?:and|of|the|for|to|in|on|at|D|R)\b", name)[0].strip(' .,')
    toks = name.split()
    while toks and toks[-1] in _BAD:
        toks.pop()
    return ' '.join(toks)


# AVTAB-v1 (Sammy 2026-10-28): surname-only names resolved by the district the release gives right after them. Context-bound on
# purpose: a bare "Assemblymember Rodriguez" can be Freddie (D-Pomona, to 2024), Michelle (D-Ontario) or Celeste (D-San Fernando Valley).
NAME_BY_DISTRICT = [(re.compile(r"\bAssemblymember Rodriguez(?=\s*\(D-Ontario\))"), "Assemblymember Michelle Rodriguez")]


def officials(text):
    for _rx, _full in NAME_BY_DISTRICT:   # AVTAB-v1
        text = _rx.sub(_full, text or "")
    found =[(_TNORM.get(m.group(1), m.group(1)), _clean(m.group(2))) for m in _TITLE_RE.finditer(text or "")]
    for m in _PLURAL.finditer(text or ""):
        for nm in re.findall("(" + _NAME + r"(?:\s+" + _NAME + r"){1,3})\s*\(", m.group(2)):
            found.append((_TNORM[m.group(1)], _clean(nm)))
    out = []
    for title, name in found:
        if not name or len(name) < 3 or re.search(r'\bGabriel\b', name) or name.split()[0] in _BAD | {'Assembly', 'Senate', 'State', 'California', 'The'}:
            continue
        if f"{title} {name}" not in out:
            out.append(f"{title} {name}")
    return [o for o in out if not any(f != o and f.endswith(' ' + o.split()[-1]) and len(f) > len(o) for f in out)]


# ---------- bills, contact, dates ----------
BILL_RE = re.compile(r"\b(AB|SB|ACA|SCA|ACR|SCR|AJR|SJR|HR|SR)\s*-?\s*(\d{1,4})\b")


def norm_bill(b):
    m = BILL_RE.search(str(b or "").upper())
    return f"{m.group(1)} {int(m.group(2))}" if m else str(b or "").strip()


def split_bills(packed):
    out = []
    for b in re.split(r"[;,]\s*", str(packed or "")):
        b = norm_bill(b)
        if b and b not in out:
            out.append(b)
    return out


def split_contact(s):
    """'Name, Title[, (323) 534-9800], email' -> (name, title, phone, email)"""
    parts = [p.strip() for p in str(s or "").split(",") if p.strip()]
    email = next((p for p in parts if "@" in p), "")
    phone = next((p for p in parts if re.fullmatch(r"\(?\d{3}\)?[\s.-]*\d{3}[\s.-]*\d{4}", p)), "")
    rest = [p for p in parts if p not in (email, phone)]
    return (rest[0] if rest else ""), ", ".join(rest[1:]), phone, email.lower()


def to_date(v):
    if isinstance(v, _dt.datetime):
        return v
    if isinstance(v, _dt.date):
        return _dt.datetime(v.year, v.month, v.day)
    s = str(v or "").strip()[:10]
    try:
        return _dt.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None


def iso(v):
    d = to_date(v)
    return d.strftime("%Y-%m-%d") if d else ""


def fill_numbered(vals, prefix, n, more, items):
    for i in range(n):
        vals[f"{prefix} {i + 1}"] = items[i] if i < len(items) else ""
    vals[more] = "; ".join(items[n:])


def row_values(date, title, dek, caucus, url, bills, quoted, names, contact, words, sids, hits, note):
    """a new release (RELCHECK) -> {column: value} in the RELTAB-v1 layout ('' = blank)"""
    leg, oth = [], []
    for nm in names or []:
        for n in clean_name(nm):
            if n not in leg and n not in oth:
                (leg if is_legislator(n) else oth).append(n)
    cn, ct, cp, ce = split_contact(contact)
    v = {"Date": to_date(date) or "", "Title": title, "Subtitle/dek": dek, "Source": CAUCUS if caucus else OFFICE, "URL": url,
         "Also on caucus site (date)": "", "Also on caucus site (URL)": "", "Release type": "",
         "In scope": "No" if (caucus and iso(date) and iso(date) < TENURE) else "Yes", "Issue": "", "Gabriel quoted": quoted,
         "Caucus release names Gabriel": "", "Word count": words,
         "Contact name": cn, "Contact title": ct, "Contact phone": cp, "Contact email": ce,
         HAS_COPIES: "Yes" if sids else "No", N_COPIES: hits or "", FIRST_COPY: "", REL_N: "", REL_IDS: "",
         "Before text rule (In tracker / ID / runs)": "", "Note": note}
    fill_numbered(v, "Legislator", N_LEG, "Legislators (more)", leg)
    fill_numbered(v, "Other official", N_OTH, "Other officials (more)", oth)
    fill_numbered(v, "Bill", N_BILL, "Bills (more)", [norm_bill(b) for b in bills or []])
    for i in range(N_TID):
        v[f"{COPY_ID} {i + 1}"] = sids[i] if i < len(sids) else ""
    if len(sids) > N_TID:                                   # never expected (max 2 so far); keep them, don't drop
        v[f"{COPY_ID} {N_TID}"] = "; ".join(sids[N_TID - 1:])
    return v


# ---------- readers ----------
def _s(v):
    if isinstance(v, (_dt.date, _dt.datetime)):
        return v.strftime("%Y-%m-%d")
    s = "" if v is None else str(v)
    if s.lower() == "nan":
        return ""
    return re.sub(r"\s+", " ", s).strip()


def is_new_layout(cols):
    return "Bill 1" in cols and ("Tracker release ID 1" in cols or f"{COPY_ID} 1" in cols)


def col(H, name):
    """RELCOPIES-v2: H = {header: position}; the position of `name` under its current or its old name (None if absent)"""
    if name in H:
        return H[name]
    alt = RENAMED_BACK.get(name) or RENAMED.get(name)
    return H.get(alt) if alt else None


def _get2(get, cols, name):
    """value of a column read by its current name, falling back to its old name"""
    if name in cols:
        return get(name)
    alt = RENAMED_BACK.get(name) or RENAMED.get(name)
    return get(alt) if alt and alt in cols else None


def related_values(state_rows, exclude=(), known=None):
    """RELCOPIES-v2: release_related.json rows of one release [[sid, type, lag], ...] -> {REL_N: int, REL_IDS: "s1; s2"}.
    Counts the Related tiers only (RELATED_TYPES; "possible" is left out), one per story, in date-lag order as stored;
    `exclude` = Story IDs that are copies of a release (not tracker stories); `known` = Story IDs present on Coverage."""
    out = []
    for x in state_rows or []:
        sid, typ = x[0], x[1]
        if typ not in RELATED_TYPES or sid in exclude or (known is not None and sid not in known) or sid in out:
            continue
        out.append(sid)
    return {REL_N: len(out), REL_IDS: "; ".join(out)}


def first_copy_date(release_date, copy_dates):
    """RELCOPIES-v2: earliest dated copy row, only when it differs from the release date (else "")"""
    ds = sorted(d for d in (to_date(x) for x in copy_dates) if d)
    rd = to_date(release_date)
    if not ds or (rd and ds[0] == rd):
        return ""
    return ds[0]


def _numbered(get, prefix, n, more):
    out = [_s(get(f"{prefix} {i}")) for i in range(1, n + 1)]
    out = [x for x in out if x]
    out += [x.strip() for x in _s(get(more)).split(";") if x.strip()]
    return out


def ids(get, cols):
    if is_new_layout(cols):
        raw = " ".join(_s(_get2(get, cols, f"{COPY_ID} {i}")) for i in range(1, N_TID + 1))
    else:
        raw = _s(get("Tracker release ID"))
    return [t for t in re.split(r"[;,\s]+", raw) if re.match(r"^s\d{5}$", t)]


def legacy(get, cols):
    """{old column: value} for one tab row, from either layout (get(col) -> cell value or None)"""
    if not is_new_layout(cols):
        return {c: _s(get(c)) for c in OLD_COLS}
    src = _s(get("Source"))
    if _s(get("Also on caucus site (URL)")) and "caucus" not in src.lower():
        src += "; Jewish Caucus"
    names = _numbered(get, "Legislator", N_LEG, "Legislators (more)") + _numbered(get, "Other official", N_OTH, "Other officials (more)")
    contact = ", ".join(x for x in (_s(get("Contact name")), _s(get("Contact title")), _s(get("Contact phone")), _s(get("Contact email"))) if x)
    d = {"Date": iso(get("Date")) or _s(get("Date")), "Title": _s(get("Title")), "Subtitle/dek": _s(get("Subtitle/dek")), "Source": src,
         "URL": _s(get("URL")), "Release type": _s(get("Release type")),
         "Bills mentioned": "; ".join(_numbered(get, "Bill", N_BILL, "Bills (more)")), "Issue": _s(get("Issue")),
         "Gabriel quoted": _s(get("Gabriel quoted")), "Co-issuers / other members named": "; ".join(names), "Contact": contact,
         "Word count": _s(get("Word count")), "In tracker": _s(_get2(get, cols, HAS_COPIES)), "Tracker release ID": "; ".join(ids(get, cols)),
         "Coverage stories linked": _s(_get2(get, cols, N_COPIES)), "Note": _s(get("Note"))}
    if d["Word count"].endswith(".0"):
        d["Word count"] = d["Word count"][:-2]
    if d["Coverage stories linked"].endswith(".0"):
        d["Coverage stories linked"] = d["Coverage stories linked"][:-2]
    return d


def legacy_df(df):
    """pandas DataFrame of the tab (either layout) -> DataFrame with the OLD 16 columns (strings)"""
    import pandas as pd
    cols = list(df.columns)
    return pd.DataFrame([legacy(lambda c, r=r: r.get(c, ""), cols) for _, r in df.iterrows()], columns=OLD_COLS)
