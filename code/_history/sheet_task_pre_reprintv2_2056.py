#!/usr/bin/env python3
"""sheet_task.py - apply tracker results to the Coverage workbook (T5).

Pure and offline: reads a JSON export of the tracker's db collections and a copy of
AJG Coverage - NewsBank.xlsx, writes a new workbook and a result JSON. No network.

    python3 -I sheet_task.py --db db_export.json --xlsx in.xlsx --out out.xlsx \
        --result result.json [--pages-dir DIR] [--today YYYY-MM-DD]

db export format (each collection: {doc_id: doc}):
    {"runs": {...}, "edits": {...}, "tones": {...}, "authors": {...},
     "translations": {...}, "pages": {...}, "reprints": {...}}

Rules (README.md / DECISIONS.md / CONTRACT.md):
  * blanks only: an existing non-blank cell is never changed. A value that differs
    from an existing one is reported in `conflicts`, never written.
    Exception: "# of reprints" on Original rows whose story gained reprint rows is
    recomputed (derived count; old -> new reported in `reprint_counts`).
  * every value written is in the default (automatic black) font (DECISIONS 102; was green 000B8A3E until OUTLETRULES-v1).
  * new rows get real IDs: next free after the max across ALL rows. New ID scheme (after the 2026-10-27
    migration; detected from the sheet): Article ID = next number in the single 5-digit sequence over Article ID
    and Print Article ID (no suffix), Story ID = next sNNNNN (never below s04297: s04196-s04296 belonged to
    removed duplicates). Old scheme (before the migration): ws-NNNNN / jg-NNNNN.
    Placeholders: NEW-<run>-<n> / sNEW-<run>-<n> (old pages: ws-NEW-... / jg-NEW-...). Ids saved under the old
    scheme (run `ids`, docs keyed jg-NNNNN, old Article IDs) are mapped through the sheet's Old Article ID
    columns and jg-NNNNN -> sNNNNN (--idmap wins for removed duplicates).
  * removal requests (edits {removed: true}) are EXECUTED (DECISIONS 2026-10-28 buttonopt line): every row of the story
    moves to the "Removed" tab (From tab, Reason removed, Removed on, Category, the Coverage columns, the A/V tab row as text),
    with its library files listed for _to_delete/. Other edits that only conflict are reported once (`edits_reported`).
  * every reprint the Update button proposes (a find the string-of-text rule turns into a Reprint, a reprint of a story on
    record, an originator's copy) is judged here by reprint_rule.py (BUTTONOPT-v1); the page never decides by text.
  * appended rows the tracker won't show (press releases, reprints of one) get the red row font (DECISIONS 102).
  * the Originals tab is rebuilt from Coverage (Original rows, Coverage order,
    Coverage columns minus "Search lookup (Oct 26)").
  * after writing, pandas verifies that no previously non-blank cell changed.
"""
import argparse, copy, datetime, json, re, sys
from urllib.parse import urlsplit

import openpyxl
from openpyxl.styles import Font

# CLEAN-v1 (agent-code, 2026-10-27): saved pages are cleaned with the library's rules before they are saved
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))   # -I drops the script dir
try:
    import clean_html as CH          # clean_html.py + clean_rules.json are published next to this script
    CH_ERR = ''
except Exception as _e:              # pages then wait in the shared store for the next run
    CH, CH_ERR = None, repr(_e)
RETRY = 'RETRY – TinyFish'
# AUTO-v1 sheet_task (agent-code, 2026-10-27): the manual steps of 2026-10-27 for new finds (see Task.reprint_check etc.)
BLOCKED = 'BLOCKED – TinyFish'   # DECISIONS 2026-10-27: blocked / paywall / login pages; other bad pages keep RETRY
try:
    import reprint_rule as RR        # the regroup's string-of-text reprint rule (reprint_rule.py next to this script)
except Exception as _e:
    RR = None
try:
    import release_rule as REL       # RELCHECK-v2: the release text rule (release_rule.py next to this script)
except Exception as _e:
    REL = None
# RELTAB-v1 sheet_task: layout of the "Press releases" tab, one value per cell (reltab.py next to this script)
try:
    import reltab as RT
    try:
        import relpage as RPG   # RELCOPIES-v1 sheet_task: a release page -> the tab's facts, exactly as the existing rows were made
    except Exception:
        RPG = None
except Exception as _e:
    RT = None
try:
    import relcopy as RC             # RELBUTTON-v1: near-copy + wire headline-prefix copy rules (relcopy.py next to this script)
except Exception:
    RC = None
# AVTAB-v1 sheet_task: "Audio & video details" tab (avtab.py next to this script)
try:
    import avtab as AV
except Exception as _e:
    AV = None
try:
    import img_embed as IE           # PHOTOS-v2 F6: photos embedded in every new saved copy at save time
except Exception:
    IE = None
try:
    import av_display_clean as AVC   # AVPREVIEW-v1 fix B: cleaned display copy of new Audio & video saves
except Exception:
    AVC = None
try:
    from authorsplit import parse_byline as _parse_byline   # Author 1..N + Author title (author_canon applies at build)
except Exception:
    _parse_byline = None
# DECISIONS 2026-10-27: California Files (californiafiles.org) is never added
SKIP_HOSTS = re.compile(r'(^|\.)californiafiles\.org$', re.I)
# DECISIONS 2026-10-27 "pure press releases": release wires and press-release pages -> 'Press release' = Yes
PR_HOSTS = re.compile(r'(^|\.)(prnewswire\.com|businesswire\.com|globenewswire\.com|einpresswire\.com|einnews\.com|prweb\.com|'
                      r'accesswire\.com|newswire\.com|publicnow\.com|targetednews\.com|contify\.com|m2\.com|asmdc\.org|'
                      r'assembly\.ca\.gov|cision\.com|prlog\.org|openpr\.com)$', re.I)
PR_OUTLETS = re.compile(r'^(the\s+)?(pr newswire|business wire|globe ?newswire|targeted news service|u\.?s\.? fed news|publicnow|'
                        r'enp newswire|m2 ?presswire|contify|ein presswire|accesswire|prweb|newswire\.com|cision)\b', re.I)


def host_of(u):
    return re.sub(r'^www\.', '', re.sub(r'^[a-z]+://', '', str(u or '').strip().lower()).split('/')[0].split(':')[0])


# F7-v1 (DECISIONS, Pasadena entry): Pasadena Now / Altadena Now dates come from the 'Published on <weekday>, <date>'
# line under the headline, never the site header date or TinyFish's published_date.
PAGE_DATE_HOSTS = re.compile(r'(^|\.)(pasadenanow|altadenanow)\.com$', re.I)
_PUB_ON = re.compile(r'Published on\s+(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\s*,?\s+([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})', re.I)
_MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


def published_on(html):
    """'Published on Thursday, March 6, 2025' -> '2025-03-06' (tags stripped first); '' if absent"""
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', str(html or '')).replace('&nbsp;', ' '))
    m = _PUB_ON.search(t)
    if not m or m.group(1)[:3].lower() not in _MONTHS:
        return ''
    return f"{m.group(3)}-{_MONTHS.index(m.group(1)[:3].lower()) + 1:02d}-{int(m.group(2)):02d}"


def is_press_release(vals):
    return bool(PR_HOSTS.search(host_of(vals.get('Publisher link'))) or PR_OUTLETS.match(str(vals.get('Outlet') or '').strip()))

# TOKENS-v1 (Sammy 2026-10-27): the master workbook lives in the Desktop library; Excel's lock file and backups too.
# The NewsBank batch PDFs stay in ~/Documents/Gabriel press PDFs/. --check-only prints these for the run.
MASTER_XLSX = '~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx'
MASTER_LOCK = '~/Desktop/Tracker library/~$AJG Coverage - NewsBank.xlsx'
BACKUPS_DIR = '~/Desktop/Tracker library/Backups/'
SKIP_IN_ORIGINALS = {'Search lookup (Oct 26)'}
PLACEHOLDER_AID = re.compile(r'^(ws-)?NEW-')
PLACEHOLDER_SID = re.compile(r'^(jg-|s)NEW-')
OLD_SID = re.compile(r'^jg-\d{5}$')
NEW_SID = re.compile(r'^s\d{5}$')
NEW_AID = re.compile(r'^\d{5}$')
OLD_AID = re.compile(r'^(nb|ws|pq)-\d{5}$')
RESERVED_S_MAX = 4296   # s04196-s04296: Story IDs of the 101 removed duplicates (work/dup_id_map.json)

# tracker edit field -> Coverage column
EDIT_MAP = {'date': 'Date', 'outlet': 'Outlet', 'hl': 'Headline', 'link': 'Publisher link',
            'author': 'Author / byline', 'topic': 'Topic', 'bills': 'Bills', 'reach': 'Reach',
            'media': 'Medium', 'role': 'Role', 'lang': 'Language'}
EDIT_UNSUPPORTED = {'also': 'reprints are rows now; add/remove reprint rows instead',
                    'conf': 'Confirmed was dropped from the tracker'}


def blank(v):
    return v is None or (isinstance(v, str) and v.strip() == '')


def norm_url(u):
    """Exact mirror of build_data.py's norm_url (keep the two in sync)."""
    u = str(u if u is not None else '').strip()
    if not u.startswith('http'):
        return ''
    u = re.sub(r'^https?://(www\.)?', '', u.lower()).split('#')[0]
    host = u.split('/')[0]
    # NewsBank / proxy / Google links identify the article only in the query string: keep it
    if not re.search(r'newsbank|oclc|google\.|proquest', host):
        u = u.split('?')[0]
    return u.rstrip('/')


def is_search_link(u, status=None):
    """Google search links ("Search link only") don't identify an article: never use them for dedupe."""
    if status and str(status).strip().lower() == 'search link only':
        return True
    return bool(re.match(r'^https?://(www\.)?google\.[a-z.]+/search', str(u or '').strip(), re.I))


def identity_links(get):
    """Normalized identity links of a row; `get(col)` returns a cell value."""
    out = []
    for c in ('Publisher link', 'NewsBank article link', 'ProQuest link'):
        v = get(c)
        if c == 'Publisher link' and is_search_link(v, get('Link status')):
            continue
        if is_search_link(v):
            continue
        k = norm_url(v)
        if k:
            out.append(k)
    return out


# OUTLETRULES-v1 (agent-instructions2, 2026-10-28): outlet matching rules from the retired "Reprint info" tab, kept in
# outlet_rules.json next to this script (feeds, aliases, generic names by city, keep_separate test pairs). Missing file =
# the normalization below without extra rules.
import os as _os, unicodedata as _ud


def _load_outlet_rules():
    try:
        return json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'outlet_rules.json'), encoding='utf-8'))
    except (OSError, ValueError):
        return {}


OUTLET_RULES = _load_outlet_rules()


def _outlet_base(s):
    """lower case, accents folded, "Today's Edition" (with or without parentheses), ": Blogs", ", The" and a leading "The"
    removed, punctuation -> space"""
    s = str(s or '').replace('\u2019', "'").replace('\u2018', "'")
    s = _ud.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().strip()
    s = re.sub(r"\s*:\s*blogs\s*$", '', s)
    s = re.sub(r"\s*\(?\btoday'?s edition\b\)?", '', s)
    s = re.sub(r",\s*the(?=\s*(?::|/|$))", '', s)
    s = re.sub(r"^the\s+", '', s.strip())
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def norm_outlet(s, city=''):
    """one key per outlet (OUTLETRULES-v1): feeds fold to their outlet, generic names are one outlet per Outlet city
    ("times@london"), aliases (outlet_rules.json) map variants to the outlet's key"""
    b = _outlet_base(s)
    if not b:
        return ''
    R = OUTLET_RULES
    for pre, key in (R.get('feeds') or {}).items():
        if b == pre or b.startswith(pre + ' '):
            return key
    k = b
    if b in set(R.get('generic_needs_city') or ()):
        c = _outlet_base(city)
        if c:
            k = b + '@' + c
    return (R.get('aliases') or {}).get(k, k)


# BUTTONOPT-v1: cells that belong on Originals only (DECISIONS 110(3)/167), outlet columns filled by outlet consensus,
# bare site addresses, Medium by page type (only values the sheet already uses; blankfill rootfix A)
ORIGINAL_ONLY = ('Tone', 'Tone note', 'Tone rated by', 'Topic', 'Bills', '# of reprints')
OUTLET_FILLS = ('Medium', 'Publisher', 'Outlet city', 'Outlet county', 'Outlet state')
BARE_HOST = re.compile(r'^[\w.-]+\.(com|org|edu|net|info|news|co|tv|fm|us|gov)(/.*)?$', re.I)
MEDIUM_RULES = [
    (re.compile(r'(^|\.)(podcasts\.apple\.com|open\.spotify\.com|podbean\.com|omny\.fm|simplecast\.com|buzzsprout\.com|megaphone\.fm|iheart\.com)$'), 'Podcast'),
    (re.compile(r'(^|\.)(kqed\.org|kcrw\.com|npr\.org|laist\.com|kpcc\.org|capradio\.org|kvpr\.org|kpbs\.org|kclu\.org|kazu\.org|kxjz\.org|kcbx\.org|kvcr\.org)$'), 'Radio'),
    (re.compile(r'(^|\.)([kw][a-z]{3}(tv|\d+)?\.(com|tv)|(abc|nbc|cbs|fox)[a-z0-9]*\.com|ktla\.com|10news\.com|telemundo[a-z0-9]*\.com|univision\.com)$'), 'TV'),
    (re.compile(r'(^|\.)(dailykos\.com|substack\.com|medium\.com|blogspot\.com|wordpress\.com)$'), 'Newsletter or blog'),
    (re.compile(r'(^|\.)(patch\.com)$|\.edu$'), 'Online news'),
]


def medium_by_page(link, outlet=''):
    h = host_of(link)
    if not h:
        return ''
    if re.search(r'\.edu$', h) and re.search(r'daily|sundial|student|gazette|bruin|trojan|aggie|mustang', str(outlet or ''), re.I):
        return 'Student newspaper'
    for rx, m in MEDIUM_RULES:
        if rx.search(h):
            return m
    return ''


def norm_val(v):
    if v is None:
        return ''
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        v = v.strftime('%Y-%m-%d')
    return re.sub(r'\s+', ' ', str(v)).strip()


class Sheet:
    def __init__(self, path):
        self.wb = openpyxl.load_workbook(path)
        self.ws = self.wb['Coverage']
        self.hdr = [c.value for c in self.ws[1]]
        self.col = {h: i + 1 for i, h in enumerate(self.hdr) if h}
        self.rows = {}            # Article ID -> row number
        self.story_rows = {}      # Story ID -> [row numbers]
        self.links = {}           # normalized link -> Article ID
        self.codes = {}           # old tracker code (jg- + 6 hex) -> Story ID
        self.max_ws = 0
        self.max_jg = 0
        self.max_num = 0          # new scheme: last number of the single Article ID / Print Article ID sequence
        self.max_s = RESERVED_S_MAX
        self.old_ids = {}         # new scheme: old Article ID / old Print Article ID -> new
        self.new_scheme = 'Old Article ID' in self.col or any(
            NEW_AID.match(str(self.ws.cell(r, self.col['Article ID']).value or '').strip())
            for r in range(2, min(self.ws.max_row, 50) + 1))
        for r in range(2, self.ws.max_row + 1):
            aid = self.get(r, 'Article ID')
            if blank(aid):
                continue
            self.rows[aid] = r
            m = re.match(r'^ws-(\d+)$', aid)
            if m:
                self.max_ws = max(self.max_ws, int(m.group(1)))
            for c, oc in (('Article ID', 'Old Article ID'), ('Print Article ID', 'Old Print Article ID')):
                v = str(self.get(r, c) or '').strip()
                if NEW_AID.match(v):
                    self.max_num = max(self.max_num, int(v))
                    o = str(self.get(r, oc) or '').strip()
                    if o:
                        self.old_ids[o] = v
            sid = self.get(r, 'Story ID')
            if not blank(sid):
                self.story_rows.setdefault(sid, []).append(r)
                m = re.match(r'^jg-(\d+)$', sid)
                if m:
                    self.max_jg = max(self.max_jg, int(m.group(1)))
                m = re.match(r'^s(\d{5})$', sid)
                if m:
                    self.max_s = max(self.max_s, int(m.group(1)))
            for k in identity_links(lambda c, r=r: self.get(r, c)):
                self.links.setdefault(k, aid)
            cell = self.get(r, 'Tracker story code')
            if not blank(cell) and not blank(sid):
                # a cell can hold several codes ("jg-a; jg-b"); Original rows win over reprint rows
                for code in re.findall(r'jg-[0-9a-f]{6}', str(cell).lower()):
                    if code not in self.codes or self.get(r, 'Original or reprint') == 'Original':
                        self.codes[code] = sid
        self.last_row = self.ws.max_row

    def get(self, r, col):
        c = self.col.get(col)
        return self.ws.cell(r, c).value if c else None

    def original_row(self, sid):
        for r in self.story_rows.get(sid, []):
            if self.get(r, 'Original or reprint') == 'Original':
                return r
        return None

    def put(self, r, col, val):
        cell = self.ws.cell(r, self.col[col])
        cell.value = val
        f = copy.copy(cell.font)
        cell.font = Font(name=f.name, sz=f.sz, b=f.b, i=f.i, u=f.u, strike=f.strike,
                         vertAlign=f.vertAlign)   # OUTLETRULES-v1: default black (DECISIONS 102), was color=GREEN

    def append_row(self):
        src = self.last_row
        self.last_row += 1
        r = self.last_row
        for c in range(1, len(self.hdr) + 1):
            s = self.ws.cell(src, c)
            d = self.ws.cell(r, c)
            d._style = copy.copy(s._style)
            d.value = None
        if src in self.ws.row_dimensions and self.ws.row_dimensions[src].height:
            self.ws.row_dimensions[r].height = self.ws.row_dimensions[src].height
        return r


class Task:
    def __init__(self, sheet, db, today):
        self.s = sheet
        self.db = db
        self.today = today
        self.res = {'at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'runs': {},
                    'conflicts': [], 'applied': [], 'duplicates': [], 'unsupported': [],
                    'removals_requested': [], 'unknown_story': [], 'edits_clear': [],
                    'edits_keep': [], 'reprint_counts': {}, 'pages': [], 'counts': {},
                    # CLEAN-v1: finds not added, pages not saved, pages kept as they were, press releases marked
                    'skipped': [], 'pages_error': [], 'pages_skipped': [], 'pages_flagged': [], 'press_releases': [],
                    # AUTO-v1: finds turned into reprints, reach and author fills, unclear Gabriels, bills from leginfo
                    'reprint_check': [], 'reach': [], 'authors_split': [], 'gabriel_unclear': [], 'bills_new': [],
                    'date_fixes': [], 'date_review': []}   # F7-v1
        self.res.update({'releases_new': [], 'releases_flagged': [], 'releases_skipped': []})   # RELCHECK-v1
        self.res.update({'releases_untestable': []})   # RELCHECK-v2
        # RELBUTTON-v1: copies to check by hand (near copies below the auto bar, copies filed under another story, dual posts),
        # untestable wire rows unmarked, derived tab columns recomputed, review-queue items, what relmatch --update re-matches
        self.res.update({'releases_review': [], 'releases_unmarked': [], 'releases_dual': [], 'related_cols': {},
                         'queue': {'nearcopy': [], 'billtags': []}, 'relmatch': {'releases': [], 'stories': []}})
        self._rel_pass = {}       # RELBUTTON-v1: placeholder Article ID of a release-search find -> the copy test it passed
        # BUTTONOPT-v1: pages to delete from the store, reprints judged here, originators, held rows, removals, reported edits
        self.res.update({'pages_drop': [], 'reprint_untested': [], 'reprint_failed': [], 'origin_added': [], 'origin_unverified': [],
                         'outlet_unresolved': [], 'held': [], 'removed': [], 'removal_failed': [], 'edits_reported': [],
                         'red_rows': [], 'av_date_review': [], 'tones_skipped': []})
        self.removals = []        # BUTTONOPT-v1: story ids to move to the Removed tab (executed last)
        self.img_cache = None     # PHOTOS-v2 F6 (--img-cache)
        self.saved_html = {}      # Article ID -> the saved (cleaned, photos embedded) page of this run
        self.release_texts = self.library_dir = self.pages_dir = None   # RELCHECK-v2
        self.page_checks = {}     # CLEAN-v1: page doc id -> clean/check result (cached)
        # AUTO-v1: page doc -> the reprint row a find became; tracker copies (--copies); bills file (--bills); caches
        self.page_target, self.copies_dir, self.bills_path = {}, None, None
        self._rules = self._origs = self._reach = self._manifest = None
        self._shards = {}
        self.ids = {}             # placeholder (story or article) -> real id
        self.idmap = {}           # old code -> Story ID (optional --idmap, lower-cased keys)
        # placeholders resolved by earlier task runs (their run docs carry `ids`)
        for run in (db.get('runs') or {}).values():
            for k, v in ((run or {}).get('ids') or {}).items():
                self.ids.setdefault(k, v)
        self._norm_preloaded = True
        self.touched_stories = set()
        self.written = 0
        self.first_new_row = sheet.last_row   # rows after this were appended by this run

    # ---------- helpers ----------
    def next_aid(self):
        if self.s.new_scheme:
            self.s.max_num += 1
            return '%05d' % self.s.max_num
        self.s.max_ws += 1
        return 'ws-%05d' % self.s.max_ws

    def next_sid(self):
        if self.s.new_scheme:
            self.s.max_s += 1
            return 's%05d' % self.s.max_s
        self.s.max_jg += 1
        return 'jg-%05d' % self.s.max_jg

    def real_sid(self, sid):
        return bool((NEW_SID if self.s.new_scheme else OLD_SID).match(sid or ''))

    def norm_id(self, v):
        """An id saved before the ID migration -> its id now (new scheme only)."""
        v = (v or '').strip()
        if not self.s.new_scheme:
            return v
        if OLD_AID.match(v):
            return self.s.old_ids.get(v, v)
        if OLD_SID.match(v):
            return self.idmap.get(v) or 's' + v[3:]
        return v

    def norm_preloaded(self):
        if self._norm_preloaded:
            self.ids = {k: self.norm_id(v) for k, v in self.ids.items()}
            self._norm_preloaded = False

    def resolve_sid(self, sid):
        """jg-NEW-* -> the real jg assigned for it (this execution or an earlier run's `ids`);
        jg- + 6 hex (temporary/old tracker code) -> Story ID of the row whose Tracker story code
        matches (sheet first, then --idmap). Real Story IDs pass through; after the
        migration a legacy jg-NNNNN becomes its sNNNNN."""
        sid = (sid or '').strip()
        if sid in self.ids:
            return self.ids[sid]
        if re.match(r'^jg-[0-9a-f]{6}$', sid, re.I):
            k = sid.lower()
            return self.s.codes.get(k) or self.idmap.get(k) or sid
        return self.norm_id(sid)   # legacy jg-NNNNN -> sNNNNN after the migration

    def fill(self, r, col, val, why, key):
        """Blanks-only write. Returns 'written' | 'same' | 'conflict' | 'nocol'."""
        if col not in self.s.col:
            self.res['unsupported'].append({'key': key, 'column': col, 'why': 'column not in sheet'})
            return 'nocol'
        if blank(val):
            return 'same'
        cur = self.s.get(r, col)
        if blank(cur):
            self.s.put(r, col, val)
            self.written += 1
            self.res['applied'].append({'aid': self.s.get(r, 'Article ID'), 'column': col,
                                        'value': norm_val(val)[:200], 'from': why})
            return 'written'
        if norm_val(cur).lower() == norm_val(val).lower():
            return 'same'
        self.res['conflicts'].append({'aid': self.s.get(r, 'Article ID'),
                                      'story': self.s.get(r, 'Story ID'), 'column': col,
                                      'sheet': norm_val(cur)[:300], 'tracker': norm_val(val)[:300],
                                      'from': why})
        return 'conflict'

    # ---------- new rows from runs ----------
    def add_row(self, obj, run_id, kind):
        link_keys = identity_links(lambda c: obj.get(c))
        dup = next((self.s.links[k] for k in link_keys if k and k in self.s.links), None)
        ph_aid = obj.get('Article ID') or ''
        ph_sid = obj.get('Story ID') or ''
        if dup:
            self.res['duplicates'].append({'run': run_id, 'placeholder': ph_aid, 'existing': dup,
                                           'link': obj.get('Publisher link', '')})
            if ph_aid:
                self.ids[ph_aid] = dup
            if PLACEHOLDER_SID.match(ph_sid) and ph_sid not in self.ids:
                self.ids[ph_sid] = self.s.get(self.s.rows[dup], 'Story ID') or ''
            return None
        if kind == 'Original':
            # a new original always gets a fresh jg-NNNNN unless its placeholder was already resolved;
            # a temporary jg- + 6 hex code is never written as a Story ID
            sid = self.ids.get(ph_sid)
            if not sid:
                sid = ph_sid if self.real_sid(ph_sid) and self.s.original_row(ph_sid) is None else self.next_sid()
                if not blank(ph_sid) and not self.real_sid(ph_sid):
                    self.ids[ph_sid] = sid
        else:
            sid = self.resolve_sid(ph_sid)
            if not self.real_sid(sid) or self.s.original_row(sid) is None:
                self.res['unknown_story'].append({'run': run_id, 'placeholder': ph_aid, 'story': ph_sid,
                                                  'why': 'reprint of a story not in the sheet'})
                return None
        vals = {k: v for k, v in obj.items() if not str(k).startswith('_')}
        if kind == 'Reprint':   # BUTTONOPT-v1 (S2, DECISIONS 110(3)/167): Tone, Topic and Bills are on Originals only
            for c in ORIGINAL_ONLY:
                vals.pop(c, None)
        held = self.resolve_outlet(vals, obj, kind, run_id, ph_aid)   # BUTTONOPT-v1 (blankfill rootfix A/B)
        if held:
            return None
        aid = self.next_aid()
        if ph_aid:
            self.ids[ph_aid] = aid
        r = self.s.append_row()
        vals.update({'Article ID': aid, 'Story ID': sid, 'Original or reprint': kind,
                     'Data Source': obj.get('Data Source') or 'Web search (TinyFish)'})
        self.date_check(vals, obj, run_id, ph_aid, aid)   # F7-v1
        d = norm_val(vals.get('Date'))
        if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            vals['Date'] = d
            vals.setdefault('Year', int(d[:4]))
        if isinstance(vals.get('Bills'), list):
            vals['Bills'] = '; '.join(vals['Bills'])
        if kind == 'Original':
            vals['# of reprints'] = 0
        self.auto_fill_row(vals, obj, kind, sid, run_id, ph_aid)   # AUTO-v1: Reach (outlet consensus), Author 1..N + title
        if kind == 'Reprint' and 'Author title' in self.s.col:   # DECISIONS 2026-10-28 (reporter affiliation): the Original's title
            o = self.s.original_row(sid)
            t = norm_val(self.s.get(o, 'Author title')) if o else ''
            if t:
                vals['Author title'] = t
            else:
                vals.pop('Author title', None)
        if 'Press release' in self.s.col and is_press_release(vals):   # CLEAN-v1
            vals['Press release'] = 'Yes'
            self.res['press_releases'].append({'run': run_id, 'placeholder': ph_aid, 'aid': aid, 'outlet': vals.get('Outlet', ''),
                                               'link': vals.get('Publisher link', '')})
        for col, v in vals.items():
            if col in self.s.col and not blank(v):
                self.s.put(r, col, v)
                self.written += 1
        self.s.rows[aid] = r
        self.s.story_rows.setdefault(sid, []).append(r)
        for code in re.findall(r'jg-[0-9a-f]{6}', str(obj.get('Tracker story code') or '').lower()):   # CLEAN-v1
            self.s.codes.setdefault(code, sid)
        for k in link_keys:
            if k:
                self.s.links.setdefault(k, aid)
        self.touched_stories.add(sid)
        if obj.get('_auto_reprint'):   # AUTO-v1: the find's saved page belongs to this reprint row, not the story's Original
            for k in re.findall(r'jg-[0-9a-f]{6}', str(obj.get('Tracker story code') or '').lower()) + [ph_aid, obj.get('_ph_sid') or '']:
                if k:
                    self.page_target[k] = aid
        if obj.get('_page'):   # BUTTONOPT-v1: a reprint's / originator's own page (pages doc rp-/og-/temp code) is saved as this row's copy
            self.page_target[str(obj['_page'])] = aid
        return aid

    def date_check(self, vals, obj, run_id, ph_aid, aid):
        """F7-v1: Pasadena/Altadena Now -> the page's 'Published on' date; a date equal to the fetch date that only
        TinyFish's published_date gave is reported for review (never changed)."""
        d = norm_val(vals.get('Date'))[:10]
        e = {'run': run_id, 'placeholder': ph_aid, 'aid': aid, 'outlet': vals.get('Outlet', ''),
             'link': vals.get('Publisher link', ''), 'date': d}
        if PAGE_DATE_HOSTS.search(host_of(vals.get('Publisher link', ''))):
            pid = self.page_doc_id(obj)
            p = ((self.db.get('pages') or {}).get(pid) or {}) if pid else {}
            pd = published_on(' '.join(str(p.get(k) or '') for k in ('publine', 'clean', 'scoped', 'html')))
            if pd:
                if pd != d:
                    vals['Date'], vals['Year'] = pd, int(pd[:4])
                    self.res['date_fixes'].append(dict(e, new=pd, why='Published on line'))
                return
            if str(obj.get('_date_src') or '') == 'page':
                return   # the Update button read the line when it fetched the page
            self.res['date_review'].append(dict(e, why='Pasadena/Altadena Now page without a "Published on" line: date not confirmed'))
            return
        if str(obj.get('_date_check') or '') == 'yes' or (str(obj.get('_date_src') or '') == 'tinyfish'
                                                         and d and d in (self.today, getattr(self, '_run_day', ''))):
            self.res['date_review'].append(dict(e, why="date equals the fetch date and comes only from TinyFish's published_date"))
            return
        # BUTTONOPT-v1 (AVDATE item 3): Podcast / Radio / TV / Video pages often show the save day, not the air day: +-3 days
        if AV is not None and str(vals.get('Medium') or '').strip() in AV.MEDIA and str(obj.get('_date_src') or '') != 'page' and d:
            near = [x for x in (self.today, getattr(self, '_run_day', '')) if x and RR is not None and RR.todate(x) and RR.todate(d)
                    and abs((RR.todate(x) - RR.todate(d)).days) <= 3]
            if near:
                self.res['date_review'].append(dict(e, why='Audio/video row dated within 3 days of the fetch day: check the air date'))

    def apply_runs(self):
        for run_id, run in sorted((self.db.get('runs') or {}).items(), key=lambda kv: (kv[1] or {}).get('at', '')):
            run = run or {}
            rows = run.get('rows') or []
            self._run_day = str(run.get('at') or '')[:10]   # F7-v1: the fetch date of this run's finds
            if not rows or run_done(run):
                continue  # nothing proposed, or already applied in an earlier task run (ids, or a sheet line: BUTTONOPT-v1 S1)
            before = dict(self.ids)
            added = []
            rows = [dict(o) for o in rows]
            rows = self.drop_skipped(rows, run_id)   # CLEAN-v1: californiafiles.org; Gabriel only outside the article
            rows = self.check_reprint_rows(rows, run_id)   # BUTTONOPT-v1 (A-B1): the page's reprints, by the text rule
            rows = self.origin_rows(rows, run_id)   # BUTTONOPT-v1 (ORIGINCREDIT): originators' copies as candidate Originals
            rows = self.reprint_check(rows, run_id)   # AUTO-v1: new finds that are reprints of a story by text
            rows = self.origin_settle(rows, run_id)   # BUTTONOPT-v1: originators no find attached to are not added
            for kind in ('Original', 'Reprint'):
                for obj in rows:
                    if (obj.get('Original or reprint') or 'Original') == kind:
                        aid = self.add_row(obj, run_id, kind)
                        if aid:
                            added.append(aid)
            ids = {k: v for k, v in self.ids.items() if k not in before}
            self.res['runs'][run_id] = {'ids': ids, 'added': added}

    def apply_reprint_docs(self):
        """rp- docs from the reprints collection (hand-added reprints)."""
        for rid, d in (self.db.get('reprints') or {}).items():
            d = d or {}
            if d.get('aid'):
                continue  # already written
            obj = {'Article ID': 'rp:' + rid, 'Story ID': d.get('story', ''), 'Outlet': d.get('outlet', ''),
                   'Publisher link': d.get('link', ''), 'Date': d.get('date', ''),
                   'Headline': d.get('hl', ''), 'Link status': 'Publisher URL' if d.get('link') else ''}
            aid = self.add_row(obj, 'reprints/' + rid, 'Reprint')
            if aid:
                self.res['runs'].setdefault('_reprints', {'ids': {}, 'added': []})
                self.res['runs']['_reprints']['ids']['rp:' + rid] = aid
                self.res['runs']['_reprints']['added'].append(aid)

    # ---------- per-story fills ----------
    def story_row(self, doc_id, coll):
        sid = self.resolve_sid(doc_id)
        r = self.s.original_row(sid)
        if r is None:
            self.res['unknown_story'].append({'collection': coll, 'id': doc_id})
        return r

    def apply_tones(self):
        for sid, t in (self.db.get('tones') or {}).items():
            t = t or {}
            if sid in self.page_target:   # TOKENS-v1: tone is for Originals only; this find became a reprint
                self.res['tones_skipped'].append({'key': sid, 'why': 'the find was written as a Reprint row'})
                continue
            r = self.story_row(sid, 'tones')
            if r is None or blank(t.get('tone')) or t.get('tone') == 'Not rated':
                continue
            if r > self.first_new_row and not blank(self.s.get(r, 'Tone')):   # BUTTONOPT-v1 (S3): the new row carries its tone
                self.res['tones_skipped'].append({'key': sid, 'why': 'the new row carries the tone already'})
                continue
            by = (t.get('by') or 'Claude').strip()
            rated = (t.get('rated') or self.today)[:10]
            who = f'Claude, from tracker ({rated})' if by == 'Claude' else f'{by} ({rated})'
            st = self.fill(r, 'Tone', t['tone'], 'tones', sid)
            if st == 'same' and not blank(self.s.get(r, 'Tone rated by')):
                continue   # BUTTONOPT-v1 (S3): the same tone already rated (e.g. "from article excerpt" by the Update button): no conflict
            if st != 'conflict':
                self.fill(r, 'Tone note', t.get('why', ''), 'tones', sid)
                self.fill(r, 'Tone rated by', who, 'tones', sid)

    def apply_authors(self):
        for sid, a in (self.db.get('authors') or {}).items():
            r = self.story_row(sid, 'authors')
            if r is not None:
                if self.fill(r, 'Author / byline', (a or {}).get('author', ''), 'authors', sid) == 'written':
                    self.split_authors(r)   # AUTO-v1

    def apply_translations(self):
        for sid, t in (self.db.get('translations') or {}).items():
            t = t or {}
            r = self.story_row(sid, 'translations')
            if r is None:
                continue
            self.fill(r, 'Translated Headline', t.get('hl', ''), 'translations', sid)
            self.fill(r, 'Story in English', t.get('text', ''), 'translations', sid)
            if t.get('lang'):
                self.fill(r, 'Language', t['lang'], 'translations', sid)

    def apply_edits(self):
        for sid, e in (self.db.get('edits') or {}).items():
            e = e or {}
            if e.get('removed'):   # BUTTONOPT-v1 (Sammy: removal requests execute): moved to the Removed tab at the end of the run
                self.res['removals_requested'].append({'story': sid, 'at': e.get('at', '')})
                self.removals.append((sid, e.get('at', '')))
                continue
            if e.get('reported') and str(e.get('reported')) >= str(e.get('at') or ''):
                self.res['edits_keep'].append(sid)   # already reported to Sammy; nothing new in it (BUTTONOPT-v1 S1)
                continue
            r = self.story_row(sid, 'edits')
            if r is None:
                self.res['edits_keep'].append(sid)
                self.res['edits_reported'].append({'id': sid, 'at': e.get('at', '')})
                continue
            states = []
            for k, v in e.items():
                if k in ('at', 'bills_off'):
                    continue
                if k in EDIT_UNSUPPORTED:
                    self.res['unsupported'].append({'key': sid, 'field': k, 'why': EDIT_UNSUPPORTED[k]})
                    states.append('conflict')
                    continue
                col = EDIT_MAP.get(k)
                if not col:
                    continue
                if k == 'bills':
                    v = '; '.join(b for b in (v if isinstance(v, list) else str(v).split(';'))
                                  if b and not str(b).startswith('-'))
                if k == 'lang' and str(v).lower() == 'english':
                    v = 'English'
                st = self.fill(r, col, v, 'edits', sid)
                if k == 'media' and st == 'written':   # BUTTONOPT-v1: an edit that makes a row Podcast/Radio/TV/Video -> AV tab row
                    self._medium_edited = getattr(self, '_medium_edited', []) + [r]
                if k == 'date' and st == 'written' and re.match(r'^\d{4}', str(v)):
                    self.fill(r, 'Year', int(str(v)[:4]), 'edits', sid)
                states.append(st)
            if 'conflict' in states:
                self.res['edits_keep'].append(sid)
                self.res['edits_reported'].append({'id': sid, 'at': e.get('at', '')})   # step 5 writes reported: <at> on the doc
            else:
                self.res['edits_clear'].append(sid)

    # ---------- pages (CLEAN-v1) ----------
    def page_doc_id(self, obj):
        """the pages doc of a proposed row: keyed by the find's temporary code (Tracker story code) or a placeholder"""
        pages = self.db.get('pages') or {}
        keys = [str(obj.get('_page') or '')]   # BUTTONOPT-v1: a reprint's / originator's own pages doc
        own = (obj.get('Original or reprint') or 'Original') == 'Original' or obj.get('_auto_reprint')   # a reprint row's code / Story ID name its story
        keys += re.findall(r'jg-[0-9a-f]{6}', str(obj.get('Tracker story code') or '').lower()) if own else []
        keys += [obj.get('Article ID') or '', (obj.get('_ph_sid') or obj.get('Story ID') or '') if own else '']
        return next((k for k in keys if k and k in pages), None)

    def check_page(self, pid, row):
        """clean the page doc's copies (article-scoped first, then the full clean copy) and judge them:
        ok -> save the cleaned page; skip -> Gabriel only outside the article; error -> not saved (RETRY)"""
        if pid in self.page_checks:
            return self.page_checks[pid]
        p = (self.db.get('pages') or {}).get(pid) or {}
        best = None
        for key in ('scoped', 'clean'):
            body = p.get(key) or ''
            if not body.strip():
                continue
            page = self.page_html(p, body, row)
            res = CH.clean_page(page, p.get('url', '') or row.get('Publisher link', ''), row.get('Outlet', ''), row, mode='find')
            verdict, reason = CH.page_check(res, page)
            cand = {'verdict': verdict, 'reason': reason, 'source': key, 'page': page, 'html': res['html'],
                    'status': res['status'], 'flags': res['flags'], 'removed': len(res['removed']),
                    'words': [res.get('words_before'), res.get('words_after')], 'header': res['header']}
            rank = {'ok': 0, 'skip': 1, 'error': 2}[verdict]
            if best is None or rank < {'ok': 0, 'skip': 1, 'error': 2}[best['verdict']]:
                best = cand
            if verdict == 'ok':
                break
        self.page_checks[pid] = best
        return best

    def page_html(self, p, body, row):
        """the page as the library keeps it: title, a metadata header (Outlet · Date, URL, Saved date) and the body.
        The cleaner removes the header lines that match the sheet and keeps (and reports) the ones that don't."""
        import html as _h
        url = p.get('url', '') or row.get('Publisher link', '')
        hdr = [x for x in (f"{row.get('Outlet', '')} · {norm_val(row.get('Date', ''))[:10]}" if row.get('Outlet') and row.get('Date') else '',
                           url, f'Saved {self.today}') if x]
        div = '<div>' + '<br>'.join(_h.escape(x) for x in hdr) + '</div>'
        m = re.search(r'<body[^>]*>', body, re.I)
        if m:
            return body[:m.end()] + div + body[m.end():]
        return (f'<!doctype html><html><head><meta charset="utf-8"><title>{_h.escape(p.get("title", "") or row.get("Headline", "") or "")}</title></head>'
                f'<body>{div}{body}</body></html>')

    def drop_skipped(self, rows, run_id):
        """CLEAN-v1: rows not added. californiafiles.org finds; finds whose saved page names Gabriel only outside the
        article (reader comments, teasers, tags), checked on the cleaned page; and the reprint rows of such a story."""
        out, gone = [], set()
        for obj in rows:
            why = None
            if SKIP_HOSTS.search(host_of(obj.get('Publisher link'))) or norm_val(obj.get('Outlet')).lower() == 'california files':
                why = 'californiafiles.org: never added (DECISIONS 2026-10-27)'
            elif CH is not None and hasattr(CH, 'skip_url') and CH.skip_url(obj.get('Publisher link'), self.rules()):   # AUTO-v1
                why = 'database, results or listing page: never added (DECISIONS 2026-10-27)'
            elif obj.get('_release') and (obj.get('Original or reprint') or 'Original') == 'Original':   # RELBUTTON-v1
                why = self.release_find_check(obj, run_id)
            elif (obj.get('Original or reprint') or 'Original') == 'Original' and CH is not None:
                pid = self.page_doc_id(obj)
                chk = self.check_page(pid, obj) if pid else None
                if chk and chk['verdict'] == 'skip':
                    why = chk['reason']
                elif chk and hasattr(CH, 'jesse_check') and (chk['verdict'] == 'ok' or chk['reason'].startswith('no Gabriel')):
                    why = self.wrong_gabriel(chk, obj, run_id)   # AUTO-v1: Jesse Gabriel only
            if why:
                self.res['skipped'].append({'run': run_id, 'placeholder': obj.get('Article ID', ''), 'story': obj.get('Story ID', ''),
                                            'code': str(obj.get('Tracker story code') or ''),
                                            'outlet': obj.get('Outlet', ''), 'link': obj.get('Publisher link', ''), 'why': why})
                if (obj.get('Original or reprint') or 'Original') == 'Original' and obj.get('Story ID'):
                    gone.add(obj['Story ID'])
                continue
            out.append(obj)
        keep = []
        for obj in out:
            if obj.get('Original or reprint') == 'Reprint' and obj.get('Story ID') in gone:
                self.res['skipped'].append({'run': run_id, 'placeholder': obj.get('Article ID', ''), 'story': obj.get('Story ID', ''),
                                            'outlet': obj.get('Outlet', ''), 'link': obj.get('Publisher link', ''),
                                            'why': 'reprint of a skipped story'})
                continue
            keep.append(obj)
        return keep

    def apply_pages(self, pages_dir):
        """Each waiting page: cleaned with the library's rules (clean_html.py), saved as <year>/<file> (the library
        folder Desktop/Tracker library/<year>/) with the original as _original_html/<year>/<file>. Error pages (not the
        article, no body, no Gabriel, paywall/login/404) are not saved: File name 'RETRY – TinyFish', Saved Copy? = No.
        A page naming Gabriel only outside the article is not saved (its row was skipped when the find came in)."""
        import os
        if not (self.db.get('pages') or {}):
            return
        if CH is None:
            self.res['pages_note'] = f'clean_html.py could not be loaded ({CH_ERR}); pages left waiting'
            return
        for pid, p in (self.db.get('pages') or {}).items():
            p = p or {}
            target = self.norm_id(self.page_target.get(pid) or self.ids.get(pid, pid))   # AUTO-v1: finds that became reprints
            aid = None
            if target in self.s.rows:
                aid = target
            else:
                r = self.s.original_row(self.resolve_sid(target))
                if r:
                    aid = self.s.get(r, 'Article ID')
            if not aid:
                if any(pid in (x.get('story'), x.get('placeholder')) or pid in x.get('code', '') for x in self.res['skipped']) \
                   or re.match(r'^(rp|og)-', pid) or pid in self.res['pages_drop']:
                    self.res['pages_drop'].append(pid)   # BUTTONOPT-v1 (S1): a skipped find's / unused candidate's page: deleted from the store
                else:
                    self.res['unknown_story'].append({'collection': 'pages', 'id': pid})
                continue
            if not ((p.get('scoped') or '').strip() or (p.get('clean') or '').strip()):
                continue
            r = self.s.rows[aid]
            row = {c: norm_val(self.s.get(r, c)) for c in ('Outlet', 'Date', 'Headline', 'Publisher link', 'NewsBank article link', 'ProQuest link')}
            chk = self.check_page(pid, row)
            if self.s.new_scheme:   # library naming: ws<Article ID><o|r>-s<Story ID>.html (DECISIONS 2026-10-27)
                suf = {'Original': 'o', 'Reprint': 'r'}.get(self.s.get(r, 'Original or reprint'), '')
                st = str(self.s.get(r, 'Story ID') or '').strip()
                fname = f'ws{aid}{suf}' + (f'-{st}' if st else '') + '.html'
            else:
                fname = f'{aid}.html'
            d = norm_val(self.s.get(r, 'Date'))
            year = d[:4] if re.match(r'^\d{4}', d) else str(self.s.get(r, 'Year') or '')[:4] or self.today[:4]
            info = {'page': pid, 'aid': aid, 'file': f'{year}/{fname}', 'url': p.get('url', ''), 'source': chk['source'],
                    'status': chk['status'], 'flags': chk['flags'], 'removed': chk['removed'], 'words': chk['words'],
                    'header_conflicts': chk['header']['conflicts']}
            if chk['verdict'] == 'skip':
                self.res['pages_skipped'].append(dict(info, why=chk['reason']))
                continue
            if chk['verdict'] == 'error' and aid in self._rel_pass_aids() and str(chk['reason']).startswith('no Gabriel') and chk.get('html'):
                chk = dict(chk, verdict='ok')   # RELBUTTON-v1: a copy of a release (passed the text / near-copy rule) need not name him
            if chk['verdict'] == 'error':
                self.fill(r, 'File name', BLOCKED if chk['reason'] in getattr(CH, 'BLOCKED_REASONS', ()) else RETRY, 'pages', pid)   # AUTO-v1
                self.fill(r, 'Saved Copy?', 'No', 'pages', pid)
                self.res['pages_error'].append(dict(info, why=chk['reason']))
                continue
            html_out = chk['html']
            if IE is not None and self.img_cache:   # PHOTOS-v2 F6: photos embedded at save time; unloadable ones dropped, captions kept
                try:
                    html_out, ist = IE.embed_page(html_out, p.get('url', '') or row.get('Publisher link', ''), self.img_cache,
                                                  story_id=str(self.s.get(r, 'Story ID') or ''), aid=aid, copy_file=f'{year}/{fname}')
                    info['photos'] = {'embedded': ist.get('embedded', 0) + ist.get('kept', 0), 'dropped': ist.get('dropped', 0),
                                      'fetched': ist.get('fetched', 0), 'failed': ist.get('failed', [])[:10]}
                except Exception as _e:
                    info['photos'] = {'error': repr(_e)[:200]}
            self.saved_html[aid] = html_out
            if pages_dir:
                os.makedirs(os.path.join(pages_dir, year), exist_ok=True)
                with open(os.path.join(pages_dir, year, fname), 'w', encoding='utf-8') as f:
                    f.write(html_out)
                if chk['html'] != chk['page']:   # the original, as the library keeps it (Tracker library/_original_html/)
                    os.makedirs(os.path.join(pages_dir, '_original_html', year), exist_ok=True)
                    with open(os.path.join(pages_dir, '_original_html', year, fname), 'w', encoding='utf-8') as f:
                        f.write(chk['page'])
                    info['original'] = f'_original_html/{year}/{fname}'
            if 'big_removal' in chk['flags'] or 'long_block' in chk['flags']:
                self.res['pages_flagged'].append(info)
            self.fill(r, 'Saved Copy?', 'Yes', 'pages', pid)
            self.fill(r, 'File type', 'HTML', 'pages', pid)
            self.fill(r, 'File name', fname, 'pages', pid)
            self.fill_counts(r, chk, pid)   # AUTO-v1: Word count (CJK by character), Mentions "Gabriel" (any script)
            self.res['pages'].append(info)

    # ---------- AUTO-v1: reprint check, Jesse Gabriel only, reach, authors, counts, bills (DECISIONS 2026-10-27) ----------
    def rules(self):
        if self._rules is None:
            self._rules = CH.load_rules() if CH is not None else {}
        return self._rules

    def page_text(self, html):
        from bs4 import BeautifulSoup
        return CH.norm(' '.join(b.text for b in CH.extract_blocks(CH.body_of(BeautifulSoup(html or '', 'html.parser')))))

    def wrong_gabriel(self, chk, obj, run_id):
        """Jesse Gabriel only: a page naming only another Gabriel, or no Gabriel in any script, is skipped (reason);
        a bare "Gabriel" with nothing to tell which one is kept and reported (gabriel_unclear)."""
        t = str(obj.get('Headline') or '') + '\n' + self.page_text(chk['html'])
        v = CH.jesse_check(t, self.rules())
        if v == 'other':
            m = CH.rx(self.rules()['other_gabriel']).search(t)
            return f"another Gabriel, not Jesse Gabriel ({m.group(0) if m else 'other Gabriel'})"
        if v == 'none':
            return 'no Jesse Gabriel on the page in any script'
        if v == 'unclear':
            self.res['gabriel_unclear'].append({'run': run_id, 'placeholder': obj.get('Article ID', ''), 'outlet': obj.get('Outlet', ''),
                                                'link': obj.get('Publisher link', ''), 'why': 'a bare "Gabriel" with no sign which one: kept, check it'})
        return None

    def originals(self):
        if self._origs is None:
            cols = ('Article ID', 'Story ID', 'Date', 'Headline', 'Outlet', 'Author / byline', 'Press release', 'Data Source', 'Edition')
            self._origs = [dict({c: norm_val(self.s.get(r, c)) for c in cols}, _row=r) for r in range(2, self.s.last_row + 1)
                           if self.s.get(r, 'Original or reprint') == 'Original' and not blank(self.s.get(r, 'Story ID'))]
        return self._origs

    def copy_html(self, sid):
        """the tracker's saved copy of a story (articles/manifest.json + articles/<year>.json from the published tracker)"""
        import os
        if not self.copies_dir:
            return None
        if self._manifest is None:
            try:
                self._manifest = json.load(open(os.path.join(self.copies_dir, 'articles', 'manifest.json'), encoding='utf-8')).get('articles', {})
            except Exception:
                self._manifest = {}
        f = self._manifest.get(sid)
        if not f:
            return None
        if f not in self._shards:
            try:
                self._shards[f] = json.load(open(os.path.join(self.copies_dir, f), encoding='utf-8'))
            except Exception:
                self._shards[f] = {}
        return self._shards[f].get(sid)

    def compare(self, find, ftext, orig, otext):
        """the regroup's rule: text when both sides have it, else headline + author; None = cannot tell (stays Original)"""
        if ftext and otext:
            v = RR.text_verdict([RR.version(*ftext)], [RR.version(*otext)])
            if v is not None:
                return v
        ha = RR.headline_author(find, orig)
        if ha['verifiable']:
            return {'ok': ha['ok'], 'conf': 'medium', 'mode': 'headline+author', 'm': None}
        return None

    def reprint_check(self, rows, run_id):
        """A new find (Original row of this run) whose cleaned page passes the string-of-text rule against an Original in the
        sheet (or an earlier-ranked new find of this run) dated within +-7 days with overlapping headline words becomes a
        Reprint of that story; its own reprint rows follow it. Low-confidence passes (clutter / edge lines set aside) are
        converted and reported. A find that ranks before the existing Original in the originals order is reported only:
        the sheet's existing cells are never changed."""
        finds = [o for o in rows if (o.get('Original or reprint') or 'Original') == 'Original']
        if not finds:
            return rows
        if RR is None or CH is None:
            self.res['reprint_check'].append({'run': run_id, 'note': 'reprint_rule.py or clean_html.py not loaded: finds not checked'})
            return rows
        texts = {}
        for o in finds:
            pid = self.page_doc_id(o)
            chk = self.check_page(pid, o) if pid else None
            texts[id(o)] = RR.html_text(chk['html']) if chk and chk['verdict'] == 'ok' else None
        # ORIGINCREDIT-v1 (handoff 2): a service credited by any find of this run ranks first (tier 0); a find whose credit line /
        # byline names a service, or that carries an originator's copy, is tested against every Original in the window (no
        # headline prefilter)
        tx = lambda o: (texts.get(id(o)) or ('',))[0] if texts.get(id(o)) else ''
        cred = RR.origin_credits(finds, {id(o): tx(o) for o in finds})[0] if hasattr(RR, 'origin_credits') else frozenset()
        rk = (lambda x: RR.rank(x, credited=cred)) if cred else RR.rank
        kept = []
        for o in sorted(finds, key=rk):
            ft = texts[id(o)]
            best = None
            credited = bool(o.get('_origin') or o.get('_og_of') or (hasattr(RR, 'credit_of') and RR.credit_of(o, tx(o))))
            cands = (RR.candidates(o, self.originals(), credited=True) + RR.candidates(o, kept, credited=True)) if credited \
                else (RR.candidates(o, self.originals()) + RR.candidates(o, kept))
            for c in cands:
                if '_text' in c:
                    ot = c['_text']
                else:
                    h = self.copy_html(c['Story ID'])
                    ot = RR.html_text(h) if h else None
                v = self.compare(o, ft, c, ot)
                if v and v['ok']:
                    key = (v['conf'] == 'high', v['mode'] != 'headline+author', min(v['m']['raw']) if v.get('m') else 0)
                    if best is None or key > best[0]:
                        best = (key, c, v, ot is not None)
            if best is None:
                kept.append(dict(o, _text=ft))
                continue
            _, c, v, had = best
            ph, target = o.get('Story ID') or '', c['Story ID']
            for r2 in rows:
                if r2 is not o and ph and r2.get('Story ID') == ph:
                    r2['Story ID'] = target
            # the same story from an outlet the story already has (another link to the same article): not added
            same = ({norm_outlet(self.s.get(x, 'Outlet'), self.s.get(x, 'Outlet city')) for x in self.s.story_rows.get(target, [])}
                    | {norm_outlet(c.get('Outlet'), c.get('Outlet city'))})   # OUTLETRULES-v1: city for generic names
            if norm_outlet(o.get('Outlet'), o.get('Outlet city')) in same - {''}:
                o['_dup'] = True
                if ph and not self.real_sid(ph):
                    self.ids[ph] = target
                self.res['skipped'].append({'run': run_id, 'placeholder': o.get('Article ID', ''), 'story': ph, 'code': str(o.get('Tracker story code') or ''),
                                            'outlet': o.get('Outlet', ''), 'link': o.get('Publisher link', ''),
                                            'why': f"same story and outlet as {c.get('Article ID', '')} ({v['mode']}): another link to an article already in the sheet"})
                continue
            o.update({'Original or reprint': 'Reprint', 'Story ID': target, '_auto_reprint': True, '_ph_sid': ph})
            o.pop('# of reprints', None)
            e = {'run': run_id, 'placeholder': o.get('Article ID', ''), 'code': str(o.get('Tracker story code') or ''),
                 'outlet': o.get('Outlet', ''), 'link': o.get('Publisher link', ''), 'headline': o.get('Headline', ''),
                 'story': target, 'original': c.get('Article ID', ''), 'original_outlet': c.get('Outlet', ''),
                 'mode': v['mode'], 'conf': v['conf'],
                 'coverage': round(min(v['m'][{'text': 'raw', 'text-clutter': 'clut', 'text-edge': 'edge'}[v['mode']]]), 3) if v.get('m') else None}
            if v['conf'] == 'low':
                e['note'] = 'low confidence: passes only with clutter or edge lines set aside; check it'
            if rk(o) < rk(c) and '_text' not in c:   # an existing Original (a find of this run ranked later is never first)
                e['order'] = (f"under the originals order this find ({RR.tier(o, credited=cred)[1]}) would be the Original, not {c.get('Outlet', '')} "
                              f"({RR.tier(c, credited=cred)[1]}); the existing Original was kept (cells are never changed): Sammy to decide")
            self.res['reprint_check'].append(e)
        return [r for r in rows if not r.get('_dup')]

    # ---------- BUTTONOPT-v1 (A-B1): the page's reprint rows, judged by the string-of-text rule ----------
    def story_ref(self, sid, rows):
        """(dict of the story's Original for headline_author, its text versions or None) for a sheet story or one new in this run"""
        cols = ('Article ID', 'Story ID', 'Date', 'Headline', 'Outlet', 'Author / byline')
        for o in rows:
            if o.get('Story ID') == sid and (o.get('Original or reprint') or 'Original') == 'Original':
                pid = self.page_doc_id(o)
                chk = self.check_page(pid, o) if pid else None
                return {c: norm_val(o.get(c)) for c in cols}, (RR.html_text(chk['html']) if chk and chk['verdict'] == 'ok' else None)
        r = self.s.original_row(sid)
        if r is None:
            return None, None
        h = self.copy_html(sid)
        return {c: norm_val(self.s.get(r, c)) for c in cols}, (RR.html_text(h) if h else None)

    def check_reprint_rows(self, rows, run_id):
        """A Reprint row the Update button proposed (a find with a story's headline, or a copy of a story found in the same run):
        its page (pages doc `_page`) is compared with the story's copy by the string-of-text rule (90 days), or by headline + same
        people (7 days) when either has no text. Fails with its own text -> it becomes a new story (an Original find, checked like
        every other find); no text to tell -> kept as a Reprint and listed (reprint_untested)."""
        if RR is None or CH is None:
            return rows
        n = 0
        for o in rows:
            if (o.get('Original or reprint') or 'Original') != 'Reprint' or o.get('_auto_reprint'):
                continue
            sid0 = str(o.get('Story ID') or '')
            sid = sid0 if PLACEHOLDER_SID.match(sid0) else self.resolve_sid(sid0)
            orig, ot = self.story_ref(sid, rows)
            if orig is None:
                continue   # add_row reports a reprint of a story not in the sheet
            pid = str(o.get('_page') or '')
            chk = self.check_page(pid, o) if pid and pid in (self.db.get('pages') or {}) else None
            ft = RR.html_text(chk['html']) if chk and chk['verdict'] == 'ok' else None
            v = self.compare(o, ft, orig, ot)
            if v and v['ok'] and v.get('m') is not None:
                d1, d2 = RR.todate(o.get('Date')), RR.todate(orig.get('Date'))
                if d1 and d2 and abs((d1 - d2).days) > RR.TEXT_WINDOW_DAYS:
                    v = dict(v, ok=False)
            e = {'run': run_id, 'placeholder': o.get('Article ID', ''), 'outlet': o.get('Outlet', ''), 'link': o.get('Publisher link', ''),
                 'headline': o.get('Headline', ''), 'story': sid, 'original': orig.get('Article ID', ''), 'original_outlet': orig.get('Outlet', '')}
            if v is not None and v.get('m') is not None:
                e['coverage'] = round(min(v['m']['raw']), 3)
            if v is not None and v['ok']:
                e.update(mode=v['mode'], conf=v['conf'])
                self.res.setdefault('reprint_confirmed', []).append(e)
            elif v is not None and ft:
                n += 1
                o.update({'Original or reprint': 'Original', 'Story ID': f'sNEW-{run_id}-rp{n}', '# of reprints': 0})
                self.res['reprint_failed'].append(dict(e, why=f"not the same text as the story ({v['mode']}): added as a story of its own"))
            else:
                self.res['reprint_untested'].append(dict(e, why=('no text to compare (its page ' + ('could not be read' if pid else 'was not saved')
                                                                 + (', the story has no saved copy' if ot is None else '') + ') and no byline to match: kept as a reprint, check it')))
        return rows

    # ---------- BUTTONOPT-v1 (ORIGINCREDIT-v1 handoff, rootfix B): originators' copies the Update button found ----------
    def origin_rows(self, rows, run_id):
        """a find's `_origin` candidates (the wire / credited outlet / aggregator source copy, pages doc og-xxxxxx) not on record
        become candidate Original rows; reprint_check then makes the find a Reprint of one whose text passes (the credited service
        ranks first). A candidate already on record needs nothing: the find is tested against every Original in the window."""
        out = list(rows)
        pages = self.db.get('pages') or {}
        for o in rows:
            og = o.get('_origin')
            if not isinstance(og, dict) or (o.get('Original or reprint') or 'Original') != 'Original':
                continue
            ph = str(o.get('Article ID') or '')
            if og.get('how') == 'translation of':
                for c in og.get('cands') or []:
                    self.res['origin_unverified'].append({'run': run_id, 'placeholder': ph, 'outlet': o.get('Outlet', ''), 'origin': c.get('url', ''),
                                                          'why': 'possible translation of this page: the text rule cannot compare languages, check it'})
                    self.res['pages_drop'].append(c.get('page', ''))
                continue
            for i, c in enumerate(og.get('cands') or []):
                url = str(c.get('url') or '')
                if not url.startswith('http') or any(k in self.s.links for k in identity_links(lambda col: url if col == 'Publisher link' else None)) \
                   or any(norm_url(x.get('Publisher link')) == norm_url(url) for x in out) or not (pages.get(c.get('page')) or {}).get('clean'):
                    self.res['pages_drop'].append(c.get('page', ''))
                    continue
                t = str(c.get('title') or o.get('Headline') or '')
                out.append({'Article ID': f'{ph}-og{i + 1}', 'Story ID': f's{ph}-og{i + 1}', 'Original or reprint': 'Original',
                            'Data Source': o.get('Data Source') or 'Web search (TinyFish)', 'Date': c.get('date') or o.get('Date', ''),
                            'Outlet': c.get('outlet') or og.get('service', ''), 'Headline': t, 'Edition': 'Web', 'Language': o.get('Language') or 'English',
                            'Role': 'Named in headline' if re.search('gabriel', t, re.I) else 'Mentioned in story', 'Publisher link': url,
                            'Link status': 'Publisher URL', '_page': c.get('page'), '_og_of': ph, '_og_how': og.get('how', ''), '_date_src': 'tinyfish'})
        return out

    def origin_settle(self, rows, run_id):
        """an originator candidate stays (as the Original) only when a find of this run became its Reprint by the text rule"""
        keep = []
        for o in rows:
            if not o.get('_og_of'):
                keep.append(o)
                continue
            sid = o.get('Story ID')
            got = [x for x in rows if x is not o and x.get('_auto_reprint') and x.get('Story ID') == sid]
            e = {'run': run_id, 'placeholder': o['_og_of'], 'origin': o.get('Publisher link', ''), 'outlet': o.get('Outlet', ''), 'how': o.get('_og_how', '')}
            if got and (o.get('Original or reprint') or 'Original') == 'Original':
                keep.append(o)
                self.res['origin_added'].append(dict(e, reprints=[x.get('Article ID', '') for x in got]))
            else:
                self.res['origin_unverified'].append(dict(e, why='its text did not pass the string-of-text rule against the find: not added'))
                self.res['pages_drop'].append(o.get('_page', ''))
        return keep

    def reach_for(self, outlet, city=''):   # OUTLETRULES-v1: city for generic names
        """(consensus Reach of the outlet's rows in the sheet, [distinct values]); consensus = one tag set (order ignored)"""
        if self._reach is None:
            self._reach = {}
            for r in range(2, self.s.last_row + 1):
                v = norm_val(self.s.get(r, 'Reach'))
                if v:
                    d = self._reach.setdefault(norm_outlet(self.s.get(r, 'Outlet'), self.s.get(r, 'Outlet city')), {})
                    k = frozenset(x.strip() for x in v.split(';') if x.strip())
                    d.setdefault(k, {}).setdefault(v, 0)
                    d[k][v] += 1
        d = self._reach.get(norm_outlet(outlet, city), {})
        if len(d) == 1:
            forms = next(iter(d.values()))
            return max(forms, key=lambda f: forms[f]), list(forms)
        return '', sorted(f for forms in d.values() for f in forms)

    # ---------- BUTTONOPT-v1: outlet name, Medium and place fills for new rows (work/tmp_agent-blankfill/rootfix.md A/B) ----------
    def outlet_index(self):
        """norm_outlet key -> {column: {value: n}} over the sheet's rows; host of Publisher link -> {Outlet: n}"""
        if getattr(self, '_oidx', None) is None:
            self._oidx, self._hidx = {}, {}
            for r in range(2, self.s.last_row + 1):
                o = self.s.get(r, 'Outlet')
                if blank(o):
                    continue
                d = self._oidx.setdefault(norm_outlet(o, self.s.get(r, 'Outlet city')), {})
                for c in OUTLET_FILLS:
                    v = norm_val(self.s.get(r, c))
                    if v:
                        d.setdefault(c, {}).setdefault(v, 0)
                        d[c][v] += 1
                h = host_of(self.s.get(r, 'Publisher link'))
                if h and not BARE_HOST.match(norm_val(o)):
                    self._hidx.setdefault(h, {}).setdefault(norm_val(o), 0)
                    self._hidx[h][norm_val(o)] += 1
        return self._oidx, self._hidx

    def resolve_outlet(self, vals, obj, kind, run_id, ph_aid):
        """Outlet: a bare address or URL becomes the name the sheet uses for that site, else the page's og:site_name (NewsBank style);
        Medium / Publisher / Outlet city / county / state: blanks filled only when every row of the outlet agrees; Medium then
        from the page type (still unknown: written blank and listed). An Original whose Outlet stays a bare site address is held
        (not written; listed in `held` with the row, for Sammy to add by hand)."""
        oidx, hidx = self.outlet_index()
        why = []
        out = norm_val(vals.get('Outlet'))
        if not out or BARE_HOST.match(out) or out.lower().startswith('http'):
            h = host_of(vals.get('Publisher link')) or host_of(out)
            name = max(hidx.get(h, {}).items(), key=lambda kv: kv[1])[0] if hidx.get(h) else ''
            if not name:
                pid = self.page_doc_id(obj)
                p = ((self.db.get('pages') or {}).get(pid) or {}) if pid else {}
                m = re.search(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']{2,80})["\']|<meta[^>]+content=["\']([^"\']{2,80})["\'][^>]+property=["\']og:site_name', str(p.get('clean') or ''), re.I)
                name = (m.group(1) or m.group(2)).strip() if m else ''
                if name and BARE_HOST.match(name):
                    name = ''
                if name:
                    mt = re.match(r'^The\s+(.+)$', name)
                    name = mt.group(1) + ', The' if mt else name
            if name:
                vals['Outlet'] = name
                self.res['outlet_unresolved'].append({'run': run_id, 'placeholder': ph_aid, 'outlet': out, 'written': name, 'why': 'site address replaced by its name'})
            else:
                why.append(f'Outlet is a site address ({out or "blank"}) with no name in the sheet or on the page')
        d = oidx.get(norm_outlet(vals.get('Outlet'), vals.get('Outlet city')), {})
        for c in OUTLET_FILLS:
            if c in self.s.col and blank(vals.get(c)) and len(d.get(c, {})) == 1:
                vals[c] = next(iter(d[c]))
        if 'Medium' in self.s.col and blank(vals.get('Medium')):
            vals['Medium'] = medium_by_page(vals.get('Publisher link'), vals.get('Outlet'))
            if blank(vals.get('Medium')):   # written, listed for review (the Update button always proposes one for a find)
                self.res['outlet_unresolved'].append({'run': run_id, 'placeholder': ph_aid, 'kind': kind, 'outlet': vals.get('Outlet', ''),
                                                      'link': vals.get('Publisher link', ''), 'why': 'Medium unknown (the outlet has no single Medium in the sheet, page type not recognised): check it'})
        if why:
            e = {'run': run_id, 'placeholder': ph_aid, 'kind': kind, 'outlet': vals.get('Outlet', ''), 'link': vals.get('Publisher link', ''), 'why': '; '.join(why)}
            if kind == 'Original':
                self.res['held'].append(dict(e, row={k: norm_val(v)[:500] for k, v in vals.items() if not blank(v)}))
                return True
            self.res['outlet_unresolved'].append(e)
        return False

    def auto_fill_row(self, vals, obj, kind, sid, run_id, ph_aid):
        """new row: Reach from the outlet's consensus (else blank); Author 1..N + Author title from the byline"""
        if 'Reach' in self.s.col:
            cons, seen = self.reach_for(vals.get('Outlet'), vals.get('Outlet city'))
            prop = norm_val(vals.get('Reach'))
            vals['Reach'] = cons
            tags = lambda s: {x.strip() for x in str(s or '').split(';') if x.strip()}
            if prop and tags(prop) != tags(cons):
                self.res['reach'].append({'run': run_id, 'placeholder': ph_aid, 'outlet': vals.get('Outlet', ''), 'tracker': prop,
                                          'written': cons, 'why': 'the outlet’s Reach in the sheet' if cons else
                                          ('the outlet’s rows disagree: ' + ' | '.join(seen) if seen else 'outlet has no Reach in the sheet: left blank')})
        if 'Author 1' in self.s.col and _parse_byline and not blank(vals.get('Author / byline')):
            self.split_into(vals, kind, sid, vals.get('Outlet'), run_id, ph_aid)

    def split_into(self, vals, kind, sid, outlet, run_id, key):
        o = self.s.original_row(sid) if kind == 'Reprint' else None
        board = norm_val(self.s.get(o, 'Outlet')) if o else norm_val(outlet)   # editorial boards: the Original's outlet
        p = _parse_byline(str(vals.get('Author / byline')), board)
        n = sum(1 for c in self.s.col if re.fullmatch(r'Author \d+', str(c)))
        e = {'run': run_id, 'key': key, 'byline': norm_val(vals.get('Author / byline'))[:200], 'authors': p['authors'], 'title': p['title'],
             'confidence': p['confidence']}
        if len(p['authors']) > n:
            e['why'] = f'needs {len(p["authors"])} Author columns, the sheet has {n}: not written'
        else:
            for i, a in enumerate(p['authors'], 1):
                vals[f'Author {i}'] = a
            if p['title'] and 'Author title' in self.s.col:
                vals['Author title'] = p['title']
        self.res['authors_split'].append(e)

    def split_authors(self, r):
        """a byline written by the authors collection on an existing row: split it too (blank Author cells only)"""
        if 'Author 1' not in self.s.col or not _parse_byline:
            return
        vals = {'Author / byline': self.s.get(r, 'Author / byline')}
        self.split_into(vals, self.s.get(r, 'Original or reprint'), self.s.get(r, 'Story ID'), self.s.get(r, 'Outlet'), 'authors',
                        self.s.get(r, 'Article ID'))
        for c, v in vals.items():
            if c != 'Author / byline':
                self.fill(r, c, v, 'authors', self.s.get(r, 'Article ID'))

    def fill_counts(self, r, chk, pid):
        """Word count (CJK by character) and Mentions "Gabriel" in text (non-Latin forms too) of the saved, cleaned page"""
        if RR is not None:
            t = RR.html_text(chk['html'])[0].replace('\x01', ' ').replace('\x02', ' ')
        else:
            t = self.page_text(chk['html'])
        self.fill(r, 'Word count', CH.nwords(t), 'pages', pid)
        self.fill(r, 'Mentions "Gabriel" in text', 'Yes' if CH.gab_re(self.rules()).search(t) else 'No', 'pages', pid)

    def apply_bills(self):
        """bills the Update button's leginfo check found (run docs' bills_new) are appended to gabriel_bills_leginfo.json
        (--bills, the pipeline copy), once each (bill + session)"""
        new = [b for run in (self.db.get('runs') or {}).values() for b in ((run or {}).get('bills_new') or []) if isinstance(b, dict) and b.get('bill')]
        if not new:
            return
        if not self.bills_path:
            self.res['bills_note'] = f'{len(new)} new bills in run docs but no --bills file: not saved'
            return
        try:
            data = json.load(open(self.bills_path, encoding='utf-8'))
        except Exception as e:
            self.res['bills_note'] = f'could not read {self.bills_path}: {e!r}'
            return
        have = {(str(b.get('bill')), str(b.get('session', ''))[:9]) for b in data.get('rows', [])}
        for b in new:
            k = (str(b['bill']).strip(), str(b.get('session', ''))[:9])
            if k in have or not re.fullmatch(r'\d{4}-\d{4}', k[1]):
                continue
            have.add(k)
            row = {f: str(b.get(f, ''))[:400] for f in ('bill', 'leginfo_measure', 'session', 'title', 'role', 'status', 'url', 'source')}
            row['confirmed_leginfo'] = True
            row['source'] = row['source'] or f'leginfo (Update button, {self.today})'
            data.setdefault('rows', []).append(row)
            self.res['bills_new'].append(row)
        if self.res['bills_new']:
            json.dump(data, open(self.bills_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


    # RELCHECK-v1 sheet_task: official releases the Update button found (run docs' releases_new) -> "Press releases" tab
    def apply_releases(self):
        new, seen = [], set()
        for rid, run in sorted((self.db.get('runs') or {}).items()):
            if ((run or {}).get('sheet') or {}).get('at'):
                continue
            for x in (run or {}).get('releases_new') or []:
                if isinstance(x, dict) and str(x.get('url', '')).startswith('http') and x['url'] not in seen:
                    seen.add(x['url']); new.append(x)
        if not new:
            return
        wb = self.s.wb
        if 'Press releases' not in wb.sheetnames:
            self.res['releases_skipped'].append({'why': 'no "Press releases" tab', 'n': len(new)}); return
        ws = wb['Press releases']; H = {c.value: c.column for c in ws[1] if c.value}
        # BUTTONOPT-v1: the tab is RELTAB (one value per cell); the RELCHECK-v1 16-column layout path is retired
        # RELBUTTON-v1: columns found under their RELCOPIES-v2 names or their old ones (reltab.col); the derived Related count /
        # Related story IDs may be missing (a tab staged before the rename)
        if RT is None or not RT.is_new_layout(H) or any(RT.col(H, c) is None for c in RT.COLS
                                                         if c not in getattr(RT, 'RELCOPY_COLS', ()) + (getattr(RT, 'REL_N', ''), getattr(RT, 'REL_IDS', ''))):
            self.res['releases_skipped'].append({'why': 'the Press releases tab is not in the RELTAB layout (or reltab.py not loaded)', 'n': len(new)}); return
        have = {str(ws.cell(r, H['URL']).value or '').strip().rstrip('/').lower() for r in range(2, ws.max_row + 1)}
        cu, cd = RT.col(H, 'Also on caucus site (URL)'), RT.col(H, 'Also on caucus site (date)')
        have |= {str(ws.cell(r, cu).value or '').strip().rstrip('/').lower() for r in range(2, ws.max_row + 1)} if cu else set()   # RELBUTTON-v1 (#6)
        new = self._rel_dual(new, ws, H, have)   # RELBUTTON-v1 (#6): one row per release posted on both sites
        # RELCHECK-v2 sheet_task: rows are matched by the release text rule (release_rule.py), not by headline
        texts = REL.load_texts(self.release_texts) if (REL is not None and getattr(self, 'release_texts', None)) else {}
        n_texts = len(texts)
        for x in sorted(new, key=lambda x: (str(x.get('date', '')), x['url'])):
            url, d, title = x['url'].strip(), str(x.get('date', ''))[:10], str(x.get('title', '')).strip()
            if url.rstrip('/').lower() in have:
                continue
            caucus = x.get('src') == 'caucus' or 'jewishcaucus' in url
            if caucus and d and d < '2020-11-18':
                self.res['releases_skipped'].append({'url': url, 'why': 'Jewish Caucus release before his chair tenure'}); continue
            # RELCOPIES-v1 sheet_task: the page (run doc `html` = the article, else its markdown `text`) parsed like the existing rows
            _pg = RPG.parse(str(x.get('html') or x.get('text') or ''), title, 'caucus' if caucus else 'office') \
                if (RPG is not None and (x.get('html') or x.get('text'))) else None
            body = _pg['body'] if (_pg and _pg['body']) else self._rel_body(str(x.get('text') or ''), title)
            rel = {'url': url, 'date': d, 'title': title, 'dek': ((_pg or {}).get('dek') or str(x.get('dek', ''))).strip(), 'body': body,
                   'src': 'caucus' if caucus else 'office'}
            if body:
                texts[url] = rel
            if REL is None or RR is None or not body:
                hv = []
                self.res['releases_skipped'].append({'url': url, 'why': 'release text rule not run (' + ('no release text' if not body else 'release_rule.py not loaded') + '): no Coverage rows matched'})
            else:
                hv = self.release_rows(rel)
            hits = [r for r, _ in hv]
            sids = []
            for r, v in hv:
                sid = str(self.s.get(r, 'Story ID') or '').strip()
                if self.fill(r, 'Press release', 'Yes', 'release text rule' if v.get('mode') not in ('nearcopy', 'title') else 'release copy rule (' + v['mode'] + ')', url) == 'written':
                    self.res['releases_flagged'].append({'aid': self.s.get(r, 'Article ID'), 'story': sid, 'release': title[:200], 'url': url,
                                                         'mode': v['mode'], 'conf': v['conf'], 'pct': REL.pct(v)})
                if not self._rel_link_ok(r, hits):   # RELBUTTON-v1 (backend review #4)
                    self._rel_misfiled(r, sid, title, url); continue
                if sid and sid not in sids:
                    sids.append(sid)
            hits = [r for r in hits if str(self.s.get(r, 'Story ID') or '').strip() in sids]
            bills = []
            for m in re.finditer(r'\b(AB|SB|ACA|SCA|ACR|SCR|AJR|SJR|HR|SR)\s*-?\s*(\d{1,4})\b', body):
                b = f'{m.group(1)} {int(m.group(2))}'
                if b not in bills:
                    bills.append(b)
            quoted = 'Yes' if re.search(r'(said|says|stated)\s+(Assembly(member| Budget Chair)?|Assemblymember|Budget Chair|Asm\.?)?\s*(Jesse\s+)?Gabriel|Gabriel\s+(said|says|stated)', body) else ''
            cm = re.search(r'(?i)contact:?\s*([^\n]{3,160})', body)   # BUTTONOPT-v1 (S6): "CONTACT:" too
            note = f"Added by the Update button's release check ({self.today})" + ('' if body else '; release page not read')
            vals = RT.row_values(d, title, str(x.get('dek', '')).strip(), caucus, url, bills, quoted, RT.officials(body),
                                 cm.group(1).strip() if cm else '', len(body.split()) if body else '', sids,
                                 len(hits) if hits else '', note)   # RELTAB-v1 sheet_task: one value per cell
            if _pg:   # RELCOPIES-v1 sheet_task: the whole RELTAB cleanup, the way the existing rows were made
                vals = RT.row_values(d, title, rel['dek'], caucus, url, _pg['bills'], 'Yes' if _pg['quoted'] else 'No', RT.officials(body),
                                     _pg['contact'], _pg['words'], sids, len(hits) if hits else '', note)
                vals['Release type'] = _pg['type']
                vals['Issue'] = self._rel_topic(sids) or RPG.issue_for(url, _pg['issue'])
                if caucus:
                    vals['Caucus release names Gabriel'] = 'Yes' if _pg['named'] else 'No'
            if 'Release ID' in H:   # RELCOPIES-v1 sheet_task: Release ID + the release's library copy (cleaned like an article)
                prid = self.next_prid(ws, H, texts)
                vals['Release ID'] = prid
                fn = self.save_release_copy(prid, d, title, str(x.get('dek', '')).strip(), x, caucus, url, body)
                if 'Saved Copy?' in H:
                    vals['Saved Copy?'] = 'Yes' if fn else 'No'
                if 'File name' in H:
                    vals['File name'] = fn
                if url in texts:
                    texts[url]['prid'] = prid
            r = ws.max_row + 1
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c)._style = copy.copy(ws.cell(r - 1, c)._style)
            if x.get('also_caucus') and cu:   # RELBUTTON-v1 (#6): the caucus copy of an office release
                vals['Also on caucus site (URL)'] = x['also_caucus'].get('url', '')
                vals['Also on caucus site (date)'] = RT.to_date(x['also_caucus'].get('date')) or ''
                have.add(str(x['also_caucus'].get('url', '')).rstrip('/').lower())
            for k, v in vals.items():
                c = RT.col(H, k)   # RELBUTTON-v1: current or old column name
                if c is None:
                    continue
                ws.cell(r, c).value = v if v != '' else None
                if k in RT.DATE_COLS and v:
                    ws.cell(r, c).number_format = 'yyyy-mm-dd'
            ws.cell(r, H['URL']).hyperlink = url
            self._rel_counts(ws, H, r)   # RELBUTTON-v1: Copies (rows) / First copy date from the copies
            have.add(url.rstrip('/').lower())
            self._rel_new_urls = getattr(self, '_rel_new_urls', set()) | {url}   # BUTTONOPT-v1 (S5): matched here; apply_release_finds skips it
            self.res['releases_new'].append({'date': d, 'title': title[:200], 'url': url, 'in_tracker': bool(sids), 'stories': sids,
                                             'prid': vals.get('Release ID', '')})   # RELCOPIES-v1
        if ws.auto_filter.ref:
            from openpyxl.utils import get_column_letter
            ws.auto_filter.ref = f'A1:{get_column_letter(ws.max_column)}{ws.max_row}'
        if REL is not None and getattr(self, 'release_texts', None) and len(texts) > n_texts:   # RELCHECK-v2: new release texts
            REL.save_texts(self.release_texts, texts)
            self.res['release_texts_changed'] = len(texts) - n_texts

    # RELCOPIES-v1 sheet_task: Release IDs (prNNNNN: max on the tab or in release_texts.json + 1; never reused) and release copies
    def _rel_topic(self, sids):
        """a release linked to tracker stories takes the Topic of the first one's Original (build_table.py rule)"""
        for sid in sids or []:
            r = self.s.original_row(sid)
            t = str(self.s.get(r, 'Topic') or '').strip() if r else ''
            if t:
                return t
        return ''

    def next_prid(self, ws, H, texts):
        if getattr(self, '_prid_next', None) is None:
            n = 0
            for rr in range(2, ws.max_row + 1):
                m = re.match(r'^pr(\d{5})$', str(ws.cell(rr, H['Release ID']).value or '').strip())
                if m:
                    n = max(n, int(m.group(1)))
            for t in (texts or {}).values():
                m = re.match(r'^pr(\d{5})$', str((t or {}).get('prid', '')))
                if m:
                    n = max(n, int(m.group(1)))
            self._prid_next = n + 1
        p = f'pr{self._prid_next:05d}'
        self._prid_next += 1
        return p

    def save_release_copy(self, prid, d, title, dek, x, caucus, url, body):
        """the release page as the library keeps it (title, header div, <h1>, the release), cleaned with clean_html.py in library
        mode (clean_rules.json site rules for gabriel.asmdc.org / jewishcaucus), photos' src made absolute; saved to
        <pages-dir>/Press releases/<year>/<prid>.html, the uncleaned page to <pages-dir>/_original_html/Press releases/<year>/.
        Returns the file name, or '' (no release text, no --pages-dir, cleaner not loaded)."""
        import os, html as _h
        self.res.setdefault('release_copies', [])
        pages_dir = getattr(self, 'pages_dir', None)
        if not body or not pages_dir or CH is None:
            self.res['release_copies'].append({'prid': prid, 'url': url, 'file': '', 'why': 'no release text' if not body else
                                               ('no --pages-dir' if not pages_dir else 'clean_html.py not loaded')})
            return ''
        year = d[:4] if re.match(r'^\d{4}', d or '') else self.today[:4]
        src = 'California Legislative Jewish Caucus' if caucus else "Gabriel's office (gabriel.asmdc.org)"
        e = _h.escape
        art = str(x.get('html') or '').strip()   # the article HTML as fetched (the library's raw page keeps it as is)
        if not art:
            paras = [p.strip() for p in re.split(r'\n\s*\n', body) if p.strip()]
            if len(paras) < 2:
                paras = [p.strip() for p in body.split('\n') if p.strip()]
            art = (f'<h3 class="subtitle">{e(dek)}</h3>' if dek else '') + ''.join(f'<p>{e(p)}</p>' for p in paras)
        page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{e(title)}</title></head><body>'
                f'<div>{e(src)} · {d}<br>{e(url)}<br>Saved {self.today}</div><h1>{e(title)}</h1>\n' + (art if art.lstrip().startswith('<article') else f'<article>{art}</article>') + '\n</body></html>')
        res = CH.clean_page(page, url, src, {'Outlet': src, 'Date': d, 'Publisher link': url, 'Headline': title}, self.rules(), mode='library')
        base = (re.match(r'^(https?://[^/]+)', url) or [None, ''])[1] if url else ''
        out = re.sub(r'(<img\b[^>]*?\bsrc=")(/[^"]*)"', lambda m: m.group(1) + base + m.group(2) + '"', res['html']) if base else res['html']
        fname = f'{prid}.html'
        ph = None
        if IE is not None and self.img_cache:   # PHOTOS-v2 F6: the release copy's photos embedded too
            try:
                out, ist = IE.embed_page(out, url, self.img_cache, story_id=prid, aid=prid, copy_file=f'Press releases/{year}/{fname}', kind='release')
                ph = {'embedded': ist.get('embedded', 0) + ist.get('kept', 0), 'dropped': ist.get('dropped', 0), 'failed': ist.get('failed', [])[:10]}
            except Exception as _e:
                ph = {'error': repr(_e)[:200]}
        os.makedirs(os.path.join(pages_dir, 'Press releases', year), exist_ok=True)
        with open(os.path.join(pages_dir, 'Press releases', year, fname), 'w', encoding='utf-8') as f:
            f.write(out)
        os.makedirs(os.path.join(pages_dir, '_original_html', 'Press releases', year), exist_ok=True)
        with open(os.path.join(pages_dir, '_original_html', 'Press releases', year, fname), 'w', encoding='utf-8') as f:
            f.write(page)
        self.res['release_copies'].append({'prid': prid, 'url': url, 'file': f'Press releases/{year}/{fname}',
                                           'original': f'_original_html/Press releases/{year}/{fname}', 'status': res['status'], 'flags': res['flags'],
                                           **({'photos': ph} if ph else {})})
        self.saved_html['release:' + prid] = out
        return fname

    # RELCHECK-v2 sheet_task: the release text rule (Sammy 2026-10-27) - a row carries an official release only when its saved
    # text passes the reprint string-of-text rule against the release text; no text = untestable (listed, never marked)
    def row_versions(self, r):
        import os
        vs = []
        year = str(self.s.get(r, 'Date') or '')[:4]
        for col in ('File name', 'File name 2'):
            fn = str(self.s.get(r, col) or '').strip()
            if not fn or '–' in fn or fn.startswith('articles/') or not re.search(r'\.(html?|pdf)$', fn, re.I):
                continue
            for base in (getattr(self, 'pages_dir', None), getattr(self, 'library_dir', None)):
                p = os.path.join(base, year, fn) if base else ''
                if p and os.path.exists(p):
                    vs += REL.file_versions(p)
                    break
        if not REL.usable([v for v in vs if v.get('label') != 'excerpt']) and self.s.get(r, 'Original or reprint') == 'Original':
            h = self.copy_html(str(self.s.get(r, 'Story ID') or '').strip())
            if h:
                vs += REL.page_versions(h)
        return vs   # EXCERPT-v1: REL.match filters short normal versions itself and keeps excerpt versions

    def release_rows(self, rel):
        """Coverage rows (1 day before .. 30 days after the release) whose text passes against this release ->
        [(row, verdict)]; prefilter: headline words overlap, or an Original with a tracker copy"""
        rr = REL.releases({rel['url']: rel})
        hits = []
        for r in range(2, self.s.last_row + 1):
            if not REL.in_window(self.s.get(r, 'Date'), rel['date']):
                continue
            hl = str(self.s.get(r, 'Headline') or '')
            over = REL.title_near(hl, rel['title'])
            if not (over or (self.s.get(r, 'Original or reprint') == 'Original' and self.copies_dir) or r > self.first_new_row):
                continue
            vs = self.row_versions(r)
            m = REL.match(vs, rr)
            if m == 'untestable':
                w = self._wire_copy(r, [dict(rel)]) if r > self.first_new_row else None   # RELBUTTON-v1: PublicNow title rule
                if w:
                    hits.append((r, w)); continue
                if over:
                    self.res['releases_untestable'].append({'aid': self.s.get(r, 'Article ID'), 'outlet': self.s.get(r, 'Outlet'),
                                                            'release': rel['title'][:200], 'url': rel['url'], 'why': 'no saved text'})
                continue
            if m:
                hits.append((r, m['verdict']))
            elif r > self.first_new_row or self.s.get(r, 'Original or reprint') == 'Original':
                nc = self._near_copy(r, vs, rr)   # RELBUTTON-v1: RELCOPIES-v2 near copies
                if nc:
                    hits.append((r, nc))
        return hits

    # ---------- RELBUTTON-v1 (rp-button, 2026-10-28): copy rules for new rows, tab columns, dual posts, review queue ----------
    def _near_copy(self, r, vs, rels):
        """relcopy.near_copy against the releases in the row's window: 'copy' -> a verdict like the text rule's (mode 'nearcopy');
        'review' -> listed (releases_review + a review-queue item), never marked. None otherwise."""
        if RC is None or not vs:
            return None
        best = None
        for x in rels:
            if not REL.in_window(self.s.get(r, 'Date'), x['date']):
                continue
            v = RC.near_copy(vs, x)
            if v and (best is None or (v['verdict'] == 'copy', v['rel_share']) > (best[0]['verdict'] == 'copy', best[0]['rel_share'])):
                best = (v, x)
        if not best:
            return None
        v, x = best
        if v['verdict'] == 'copy':
            return {'ok': True, 'conf': 'medium', 'mode': 'nearcopy', 'm': {'raw': (v['story_share'], v['rel_share'])}, '_rel': x}
        self._nearcopy_review(r, x, v)
        return None

    def _nearcopy_review(self, r, x, v):
        sid = str(self.s.get(r, 'Story ID') or '').strip()
        prid = self._prid_of(x['url'])
        key = f'{prid or x["url"]}:{sid}'
        if any(q['key'] == key for q in self.res['queue']['nearcopy']):
            return
        self.res['releases_review'].append({'aid': self.s.get(r, 'Article ID'), 'story': sid, 'release': x['title'][:200], 'url': x['url'],
                                            'why': f"near copy: {round(100 * v['rel_share'])}% of the release, {round(100 * v['story_share'])}% of the story (below the 85% auto bar; check by hand)"})
        self._queue_nearcopy(sid, prid or x['url'], x, v['story_share'], v['rel_share'], 'the near-copy rule (relcopy.py)')

    def _queue_nearcopy(self, sid, prid, x, story_share, rel_share, how):
        r = self.s.original_row(sid)
        g = (lambda c: norm_val(self.s.get(r, c))) if r else (lambda c: '')
        d, rd = g('Date')[:10], str(x.get('date', ''))[:10]
        lag = (RR.todate(d) - RR.todate(rd)).days if (RR is not None and RR.todate(d) and RR.todate(rd)) else None
        q = self.res['queue']['nearcopy']
        q.append({'cat': 'nearcopy', 'conf': 'low' if story_share >= 0.8 else 'medium', 'id': f'nearcopy-{self._qtag()}-{len(q):03d}',
                  'key': f'{prid}:{sid}', 'title': f"{sid} {g('Outlet')} ({d}): {round(100 * story_share)}% release text from {prid}",
                  'detail': f"{sid} · {g('Outlet')} · {d} · \"{g('Headline')[:110]}\" · {round(100 * story_share)}% of the story is release text"
                            f" · {prid} ({rd}{'' if lag is None else f', lag {lag:+d} d'}) \"{str(x.get('title', ''))[:100]}\""
                            + (f" · the story covers {round(100 * rel_share)}% of the release" if rel_share is not None else '')
                            + f" · found by {how} in the Update button run of {self.today}"
                            + f" · 'Count as a copy' makes it a pickup of {prid} (Press release = Yes, left out of the story counts); 'Keep as a story' keeps it in the tracker labelled \"Runs the release (edited)\"",
                  'options': [f'Count as a copy of {prid}', 'Keep as a story'], 'proposed': 'Keep as a story'})

    def _qtag(self):
        return re.sub(r'\D', '', self.res.get('at', ''))[:12] or self.today.replace('-', '')

    def _prid_of(self, url):
        ws, H = self._rel_tab()
        if ws is None or 'Release ID' not in H:
            return ''
        if getattr(self, '_prid_by_url', None) is None or len(self._prid_by_url) < ws.max_row - 1:
            self._prid_by_url = {str(ws.cell(t, H['URL']).value or '').strip(): str(ws.cell(t, H['Release ID']).value or '').strip()
                                 for t in range(2, ws.max_row + 1)}
        return self._prid_by_url.get(str(url or '').strip(), '')

    def _wire_copy(self, r, rels):
        """relcopy.wire_title_copy for a release-wire row with no saved text: a verdict (mode 'title') or None"""
        if RC is None or not RC.is_wire(self.s.get(r, 'Outlet'), self.s.get(r, 'Publisher link')):
            return None
        x = RC.wire_title_copy(self.s.get(r, 'Headline'), self.s.get(r, 'Date'), rels)
        if not x:
            return None
        return {'ok': True, 'conf': 'medium', 'mode': 'title', 'm': {'raw': (1.0, 1.0)}, '_rel': x}   # pct 100: headline = title prefix

    def _rel_link_ok(self, r, passing=()):
        """backend review #4: a passing Reprint row links its Story ID only when that story's Original carries the release too
        (Press release = Yes, or passing in the same test); otherwise the copy is filed under another story"""
        if self.s.get(r, 'Original or reprint') != 'Reprint':
            return True
        o = self.s.original_row(str(self.s.get(r, 'Story ID') or '').strip())
        return bool(o) and (o in passing or str(self.s.get(o, 'Press release') or '').strip().lower() == 'yes')

    def _rel_misfiled(self, r, sid, title, url):
        self.res['releases_review'].append({'aid': self.s.get(r, 'Article ID'), 'story': sid, 'release': title[:200], 'url': url,
                                            'why': 'copy filed under another story: a Reprint of a story whose Original does not carry this release '
                                                   '(marked Press release = Yes, not linked; give the row its own Story ID)'})

    def _copy_ids(self, ws, H, tr):
        out = []
        for i in range(1, (RT.N_TID if RT is not None else 2) + 1):
            c = RT.col(H, f'{RT.COPY_ID} {i}')
            if c:
                out += [t.strip() for t in str(ws.cell(tr, c).value or '').replace(',', ';').split(';') if t.strip()]
        return out

    def _pr_rows(self):
        """Story ID -> dates of its Press release = Yes rows; Story IDs with a row that is not (tracker stories)"""
        pr, tracker = {}, set()
        for rr in range(2, self.s.last_row + 1):
            sid = str(self.s.get(rr, 'Story ID') or '').strip()
            if not sid:
                continue
            if str(self.s.get(rr, 'Press release') or '').strip().lower() == 'yes':
                pr.setdefault(sid, []).append(self.s.get(rr, 'Date'))
            else:
                tracker.add(sid)
        return pr, tracker

    def _rel_counts(self, ws, H, tr, pr=None):
        """RELCOPIES-v2 derived cells of one release from its copies: Has copies, Copies (rows), First copy date (if different).
        Returns the number of cells changed."""
        if RT is None or not hasattr(RT, 'first_copy_date'):
            return 0
        pr = pr if pr is not None else self._pr_rows()[0]
        ids = self._copy_ids(ws, H, tr)
        runs = [d for s in ids for d in pr.get(s, [])]
        want = {RT.HAS_COPIES: 'Yes' if ids else 'No', RT.N_COPIES: len(runs) if ids else None,
                RT.FIRST_COPY: RT.first_copy_date(ws.cell(tr, H['Date']).value, runs) or None}
        n = 0
        for k, v in want.items():
            c = RT.col(H, k)
            if c is None:
                continue
            cur = ws.cell(tr, c).value
            if norm_val(cur)[:10] != norm_val(v)[:10] if k == RT.FIRST_COPY else norm_val(cur) != norm_val(v):
                ws.cell(tr, c).value = v
                if k == RT.FIRST_COPY and v:
                    ws.cell(tr, c).number_format = 'yyyy-mm-dd'
                n += 1
        return n

    def apply_related_cols(self, state):
        """Copies (rows) / First copy date / Has copies from the copies, and Related count / Related story IDs from
        release_related.json (RELCOPIES-v2 contract; tier-1 types, reltab.RELATED_TYPES), recomputed for every release on the tab.
        `state` = the release_related.json dict (or its path); None -> the Related columns are left as they are."""
        ws, H = self._rel_tab()
        if ws is None or RT is None or 'Release ID' not in H or not hasattr(RT, 'related_values'):
            return
        if isinstance(state, str):
            try:
                state = json.load(open(state, encoding='utf-8'))
            except Exception as _e:
                self.res['related_cols'] = {'error': f'release_related.json not read: {_e!r}'[:200]}
                state = None
        rel = (state or {}).get('rel') if isinstance(state, dict) else None
        pr, tracker = self._pr_rows()
        copy_sids = {s for tr in range(2, ws.max_row + 1) for s in self._copy_ids(ws, H, tr)}
        cn, ci = RT.col(H, RT.REL_N), RT.col(H, RT.REL_IDS)
        st = {'copies_cells': 0, 'related_cells': 0, 'releases': 0, 'links': 0,
              'state': (state or {}).get('version', '') if isinstance(state, dict) else '', 'columns': bool(cn and ci)}
        for tr in range(2, ws.max_row + 1):
            prid = str(ws.cell(tr, H['Release ID']).value or '').strip()
            if not prid:
                continue
            st['releases'] += 1
            st['copies_cells'] += self._rel_counts(ws, H, tr, pr)
            if rel is None or not (cn and ci):
                continue
            v = RT.related_values(rel.get(prid, []), exclude=copy_sids | set(pr) - tracker, known=tracker)
            st['links'] += v[RT.REL_N]
            for c, val in ((cn, v[RT.REL_N]), (ci, v[RT.REL_IDS] or None)):
                if norm_val(ws.cell(tr, c).value) != norm_val(val):
                    ws.cell(tr, c).value = val
                    st['related_cells'] += 1
        self.res['related_cols'] = st

    def _rel_dual(self, new, ws, H, have):
        """backend review #6: one tab row per release posted on both sites. A caucus item with the normalized title of an office
        item of this run (or of an office row on the tab) within 3 days: its URL/date go to that row's "Also on caucus site" (blank
        cells only) and it gets no row of its own. Office items whose caucus copy is already a tab row: listed for review."""
        key = lambda t: re.sub(r'[^a-z0-9]+', ' ', str(t or '').lower().replace('’', '').replace("'", '')).strip()
        near = lambda a, b: bool(RR is not None and RR.todate(a) and RR.todate(b) and abs((RR.todate(a) - RR.todate(b)).days) <= 3)
        cu, cd = RT.col(H, 'Also on caucus site (URL)'), RT.col(H, 'Also on caucus site (date)')
        rows = [(t, key(ws.cell(t, H['Title']).value), RT.iso(ws.cell(t, H['Date']).value), str(ws.cell(t, H['Source']).value or '').lower())
                for t in range(2, ws.max_row + 1)]
        office = [x for x in new if not (x.get('src') == 'caucus' or 'jewishcaucus' in str(x.get('url', '')))]
        out = list(office)
        for x in new:
            if x in office:
                continue
            u, k, d = str(x['url']).strip(), key(x.get('title')), str(x.get('date', ''))[:10]
            if u.rstrip('/').lower() in have:
                continue
            o = next((y for y in office if key(y.get('title')) == k and near(y.get('date'), d)), None)
            if o:
                o.setdefault('also_caucus', {'url': u, 'date': d})
                self.res['releases_dual'].append({'url': u, 'office': o['url'], 'how': 'same run'}); continue
            t = next((t for t, tk, td, src in rows if tk == k and near(td, d) and 'office' in src), None)
            if t:
                done = []
                if cu and not str(ws.cell(t, cu).value or '').strip():
                    ws.cell(t, cu).value = u; ws.cell(t, cu).hyperlink = u; done.append('URL')
                if cd and not ws.cell(t, cd).value and RT.to_date(d):
                    ws.cell(t, cd).value = RT.to_date(d); ws.cell(t, cd).number_format = 'yyyy-mm-dd'; done.append('date')
                have.add(u.rstrip('/').lower())
                self.res['releases_dual'].append({'url': u, 'office': str(ws.cell(t, H['URL']).value or ''),
                                                  'prid': str(ws.cell(t, H['Release ID']).value or '') if 'Release ID' in H else '',
                                                  'how': 'tab row' + (' (Also on caucus site ' + ' + '.join(done) + ' filled)' if done else ' (already filled)')})
                continue
            out.append(x)
        for x in list(out):
            if x in office:
                k, d = key(x.get('title')), str(x.get('date', ''))[:10]
                t = next((t for t, tk, td, src in rows if tk == k and near(td, d) and 'caucus' in src and 'office' not in src), None)
                if t:
                    out.remove(x)
                    self.res['releases_review'].append({'url': x['url'], 'release': str(x.get('title', ''))[:200],
                                                        'why': 'office posting of a release already on the tab as a caucus row '
                                                               f"({ws.cell(t, H['Release ID']).value if 'Release ID' in H else 'row ' + str(t)}): not added; merge by hand (Source = office, caucus URL in Also on caucus site)"})
        return out

    def _new_release_texts(self):
        """queued new releases (run docs' releases_new) as release_rule entries {url: {date, title, dek, body}}"""
        out = {}
        for rid, run in sorted((self.db.get('runs') or {}).items()):
            if ((run or {}).get('sheet') or {}).get('at'):
                continue
            for x in (run or {}).get('releases_new') or []:
                if not isinstance(x, dict) or not str(x.get('url', '')).startswith('http') or x.get('dup_of'):
                    continue
                title = str(x.get('title', '')).strip()
                caucus = x.get('src') == 'caucus' or 'jewishcaucus' in x['url']
                pg = RPG.parse(str(x.get('html') or x.get('text') or ''), title, 'caucus' if caucus else 'office') \
                    if (RPG is not None and (x.get('html') or x.get('text'))) else None
                body = pg['body'] if (pg and pg['body']) else self._rel_body(str(x.get('text') or ''), title)
                if body:
                    out[x['url'].strip()] = {'date': str(x.get('date', ''))[:10], 'title': title, 'dek': ((pg or {}).get('dek') or '').strip(), 'body': body}
        return out

    def release_find_check(self, obj, run_id):
        """backend review #3: a find of the release pickup search (_release {prid, url}; it may not name him) is kept when its page
        passes the release text rule or the near-copy rule against an in-scope release dated -1..+30 days from it (marked later by
        apply_release_finds), or when it names Jesse Gabriel (ordinary coverage; relmatch links it). Otherwise it is skipped and
        listed in releases_skipped. Returns the skip reason or None."""
        info = obj.get('_release') if isinstance(obj.get('_release'), dict) else {}
        pid = self.page_doc_id(obj)
        chk = self.check_page(pid, obj) if (pid and CH is not None) else None
        if chk and chk.get('html') and REL is not None and RR is not None:
            if getattr(self, '_relscope', None) is None:
                t = dict(REL.load_texts(self.release_texts) if getattr(self, 'release_texts', None) else {})
                t = {u: x for u, x in t.items() if not (x.get('src') == 'caucus' and str(x.get('date', ''))[:10] < (getattr(RT, 'TENURE', '2020-11-18')))}
                t.update(self._new_release_texts())
                self._relscope = REL.releases(t)
            cand = [x for x in self._relscope if REL.in_window(obj.get('Date'), x['date'])]
            cand.sort(key=lambda x: x['url'] != info.get('url'))
            vs = REL.page_versions(chk['html'])
            m = REL.match(vs, cand) if cand else None
            hit = None
            if m and m != 'untestable':
                hit = {'url': m['release']['url'], 'title': m['release']['title'], 'verdict': m['verdict']}
            elif RC is not None and cand:
                best = None
                for x in cand:
                    v = RC.near_copy(vs, x)
                    if v and v['verdict'] == 'copy' and (best is None or v['rel_share'] > best[0]['rel_share']):
                        best = (v, x)
                if best:
                    hit = {'url': best[1]['url'], 'title': best[1]['title'],
                           'verdict': {'ok': True, 'conf': 'medium', 'mode': 'nearcopy', 'm': {'raw': (best[0]['story_share'], best[0]['rel_share'])}}}
            if hit:
                self._rel_pass[obj.get('Article ID') or ''] = hit
                return None
        if chk and chk['verdict'] == 'ok' and self.wrong_gabriel(chk, obj, run_id) is None:
            return None   # names him: ordinary coverage (relmatch --stories relates it to the release)
        why = 'release search hit, not a copy and not naming him' if chk else 'release search hit with no page to test'
        self.res['releases_skipped'].append({'run': run_id, 'placeholder': obj.get('Article ID', ''), 'link': obj.get('Publisher link', ''),
                                             'outlet': obj.get('Outlet', ''), 'release': info.get('prid') or info.get('url', ''), 'why': why})
        return why

    def _rel_pass_aids(self):
        return {self.ids.get(k, k): v for k, v in self._rel_pass.items() if k}

    def unmark_untestable_wire(self):
        """backend review #5 (RELCOPIES-v2 contract): a row this run marked Press release = Yes because of its host / outlet
        (is_press_release), with no saved text and no release whose title it starts (wire title rule), is not a copy of his
        releases and is unmarked (it is this run's own write); listed in releases_unmarked"""
        marked = {x.get('aid') for x in self.res.get('press_releases', [])}
        linked = {x.get('aid') for x in self.res.get('releases_flagged', [])}
        for aid in sorted(a for a in marked - linked if a in self.s.rows):
            r = self.s.rows[aid]
            if str(self.s.get(r, 'Press release') or '').strip().lower() != 'yes':
                continue
            if REL is not None and REL.usable([v for v in self.row_versions(r) if v.get('label') != 'excerpt']):
                continue   # it has text: another issuer's release (DECISIONS 35) stays marked
            self.s.put(r, 'Press release', None)
            self.res['applied'] = [x for x in self.res['applied'] if not (x.get('aid') == aid and x.get('column') == 'Press release')]
            self.res['releases_unmarked'].append({'aid': aid, 'outlet': self.s.get(r, 'Outlet'), 'link': self.s.get(r, 'Publisher link'),
                                                  'why': 'release wire row with no saved text that starts no release title (not a copy of his releases)'})

    def queue_after(self, state, stories, prev_queue=None):
        """RELBUTTON-v1 (rp-queue's shapes, cats nearcopy / billtags): review-queue items for this run's stories after relmatch
        --update. nearcopy = their release_related.json rows of type `nearcopy` (>= 60% of the story is release text) plus the
        sheet pass's near-copy reviews; billtags = their tier-1 text / quote / topic rows to a release naming one of his bills of
        that session while the story's Bills are blank (proposed Add only when the story text names the bill, same session, he
        authored it). Returns {doc id: {"list": [...]}} for the review queue's "items" collection."""
        rel = (state or {}).get('rel') or {}
        stories = set(stories or [])
        ws, H = self._rel_tab()
        tab = {}
        if ws is not None and 'Release ID' in H:
            for t in range(2, ws.max_row + 1):
                p = str(ws.cell(t, H['Release ID']).value or '').strip()
                if p:
                    bills = [str(ws.cell(t, H[f'Bill {i}']).value or '').strip() for i in range(1, 7) if f'Bill {i}' in H]
                    if 'Bills (more)' in H:
                        bills += [b.strip() for b in str(ws.cell(t, H['Bills (more)']).value or '').split(';')]
                    tab[p] = {'date': RT.iso(ws.cell(t, H['Date']).value), 'title': str(ws.cell(t, H['Title']).value or ''),
                              'bills': [b for b in bills if b], 'url': str(ws.cell(t, H['URL']).value or '')}
        q = {'nearcopy': [x for x in (prev_queue or {}).get('nearcopy', [])], 'billtags': []}
        self.res['queue'] = q
        have = {x['key'] for x in q['nearcopy']}
        pr, tracker = self._pr_rows()
        binfo = {}
        try:
            for b in json.load(open(self.bills_path, encoding='utf-8')).get('rows', []) if self.bills_path else []:
                binfo.setdefault(b['bill'], []).append(b)
        except Exception:
            pass
        sess = lambda d: (lambda y: f'{y}-{y + 1}')(int(d[:4]) if int(d[:4]) % 2 else int(d[:4]) - 1) if re.match(r'^\d{4}', d or '') else ''
        cand = {}
        for prid, rows in rel.items():
            for x in rows:
                sid, typ, lag = x[0], x[1], (x[2] if len(x) > 2 else None)
                if sid not in stories or sid not in tracker:
                    continue
                if typ == 'nearcopy' and f'{prid}:{sid}' not in have and prid in tab:
                    have.add(f'{prid}:{sid}')
                    self._queue_nearcopy(sid, prid, tab[prid], 0.6, None, 'relmatch (nearcopy tier: at least 60% of the story is release text)')
                if typ in ('text', 'quote', 'topic') and prid in tab and tab[prid]['bills']:
                    cand.setdefault(sid, []).append((prid, typ, lag))
        EVN = {'text': 'uses the release text', 'quote': 'quotes the release', 'topic': 'same week, same subject'}
        for sid in sorted(cand):
            o = self.s.original_row(sid)
            if o is None or norm_val(self.s.get(o, 'Bills')):
                continue
            g = lambda c: norm_val(self.s.get(o, c))
            d = g('Date')[:10]
            txt = '\n'.join(x for x in (g('Headline'), g('Translated Headline'), g('Story in English'), self._story_text(sid)) if x)
            bills, info = [], {}
            for prid, typ, lag in cand[sid]:
                for b in tab[prid]['bills']:
                    bi = next((x for x in binfo.get(b, []) if x.get('session') == sess(tab[prid]['date'])), None)
                    if b in info or not bi:
                        continue
                    p, n = (b.split() + [''])[:2]
                    pfx = {'AB': r'(?:AB|A\.\s?B\.|Assembly\s+Bill)', 'SB': r'(?:SB|S\.\s?B\.|Senate\s+Bill)', 'ACR': r'(?:ACR|Assembly\s+Concurrent\s+Resolution)',
                           'ACA': r'(?:ACA|Assembly\s+Constitutional\s+Amendment)', 'AJR': r'(?:AJR|Assembly\s+Joint\s+Resolution)'}.get(p, re.escape(p))
                    m = re.search(r'(?<![A-Za-z])' + pfx + r'\s*(?:No\.?\s*)?-?\s*' + re.escape(n) + r'\b', txt, re.I) if n else None
                    auth = str(bi.get('role', '')).startswith('author') or bi.get('role') == 'principal coauthor'
                    info[b] = {'prid': prid, 'typ': typ, 'lag': lag, 'named': m.group(0) if m else '', 'same': sess(d) == sess(tab[prid]['date']), 'auth': auth, 'bi': bi}
                    bills.append(b)
            if not bills:
                continue
            named = [b for b in bills if info[b]['named'] and info[b]['same'] and info[b]['auth']]
            bills = named + [b for b in bills if b not in named]
            multi = len(bills) > 1
            prop = [f'Add {b} to {sid}' for b in named] if named else ['Leave untagged']
            ev = ' | '.join(f"{p} ({tab[p]['date']}, {', '.join(tab[p]['bills'])}) \"{tab[p]['title'][:90]}\": {EVN.get(t, t)}" + ('' if l is None else f', lag {l:+d} d')
                            for p, t, l in cand[sid][:4])
            bl = ' · '.join(f"{b} ({str(info[b]['bi'].get('title', '')).rstrip('.')})" + ('' if info[b]['auth'] else f" [Gabriel {info[b]['bi'].get('role', '')}]") + ': '
                            + (f"story text names it (\"{info[b]['named']}\")" if info[b]['named'] else 'not named in story text')
                            + ('' if info[b]['same'] else ' · different session from the story') for b in bills[:6])
            it = {'cat': 'billtags', 'conf': 'high' if named else 'medium', 'id': f'billtag-{self._qtag()}-{len(q["billtags"]):03d}', 'key': sid,
                  'title': f"{sid} {g('Outlet')} ({d}): tag {' / '.join(bills[:3])}?" + (' — named in text' if named else ''),
                  'detail': f"{sid} · {g('Outlet')} · {d} · \"{g('Headline')[:110]}\" · Bills now blank · related to a bill release: {ev} · {bl}"
                            + ' · proposal: ' + (f"add {' + '.join(named)} (the story names {'them' if len(named) > 1 else 'it'})" if named else 'leave untagged unless you know the bill (story text does not name it)')
                            + f' · found by the Update button run of {self.today} · an Add writes the bill into Bills for this story (all its rows)',
                  'options': [f'Add {b} to {sid}' for b in bills][:max(6, len(named))] + ['Leave untagged'],
                  'proposed': prop if multi else prop[0]}
            if multi:
                it['multi'] = True
            q['billtags'].append(it)
        tag = self._qtag()
        return {f'{tag}-{k}': {'list': v} for k, v in q.items() if v}

    def _story_text(self, sid):
        """the story's saved text: its Original's file in --pages-dir / --library, else the tracker copy (--copies)"""
        o = self.s.original_row(sid)
        if o is None or REL is None or RR is None:
            return ''
        vs = self.row_versions(o)
        if vs:
            return ' '.join(vs[0]['raw']) if isinstance(vs[0].get('raw'), list) else ''
        return ''

    def relmatch_lists(self):
        """what the prompt passes to relmatch --update: this run's new releases and the stories that are new or gained a saved copy"""
        rel = [x['prid'] for x in self.res.get('releases_new', []) if x.get('prid')]
        st = []
        for v in self.res.get('runs', {}).values():
            for aid in v.get('added', []):
                r = self.s.rows.get(aid)
                if r and self.s.get(r, 'Original or reprint') == 'Original':
                    st.append(str(self.s.get(r, 'Story ID') or '').strip())
        for p in self.res.get('pages', []):
            r = self.s.rows.get(p.get('aid'))
            if r and self.s.get(r, 'Original or reprint') == 'Original':
                st.append(str(self.s.get(r, 'Story ID') or '').strip())
        self.res['relmatch'] = {'releases': rel, 'stories': sorted({s for s in st if s})}

    def _rel_tab(self):
        wb = self.s.wb
        if 'Press releases' not in wb.sheetnames:
            return None, None
        ws = wb['Press releases']
        return ws, {c.value: c.column for c in ws[1] if c.value}

    def _rel_mark(self, r, url, title, v, ws, H, tr):
        sid = str(self.s.get(r, 'Story ID') or '').strip()
        how = 'release text rule' if v.get('mode') not in ('nearcopy', 'title') else 'release copy rule (' + v['mode'] + ')'
        f = self.fill(r, 'Press release', 'Yes', how, url)
        if f not in ('written', 'same'):   # RELBUTTON-v1: a row already Yes (a wire find marked on arrival) is linked too
            return
        if any(x.get('aid') == self.s.get(r, 'Article ID') and x.get('url') == url for x in self.res['releases_flagged']):
            return
        self.res['releases_flagged'].append({'aid': self.s.get(r, 'Article ID'), 'story': sid, 'release': title[:200], 'url': url,
                                             'mode': v['mode'], 'conf': v['conf'], 'pct': REL.pct(v)})
        if ws is None or tr is None or RT is None:
            return
        # RELBUTTON-v1: RELCOPIES-v2 column names ("Copy story ID 1/2", "Has copies", "Copies (rows)", "First copy date (if
        # different)") or the old ones ("Tracker release ID 1/2", "In tracker", ...), via reltab.col
        cols = [RT.col(H, f'{RT.COPY_ID} {i}') for i in range(1, RT.N_TID + 1)]
        if any(c is None for c in cols):   # BUTTONOPT-v1: RELTAB layout only (the 16-column path is retired)
            return
        if not self._rel_link_ok(r):   # backend review #4
            self._rel_misfiled(r, sid, title, url)
            return
        k = RT.N_TID   # RELTAB-v1 sheet_task: one story per copy-ID column, the rest joined in the last
        ids = self._copy_ids(ws, H, tr)
        if sid and sid not in ids:
            ids.append(sid)
        for i in range(1, k + 1):
            ws.cell(tr, cols[i - 1]).value = (ids[i - 1] if i < k else '; '.join(ids[k - 1:])) if len(ids) >= i else None
        self._rel_counts(ws, H, tr)   # Has copies, Copies (rows), First copy date: recomputed from the copies

    def apply_release_finds(self):
        """new rows of this run whose saved page passes the release text rule against an in-scope official release (tab,
        dated 1 day after .. 30 days before the row) -> Press release = Yes (blanks only) + the tab's link columns"""
        if REL is None or RR is None or not getattr(self, 'release_texts', None) or self.s.last_row <= self.first_new_row:
            return
        texts = REL.load_texts(self.release_texts)
        ws, H = self._rel_tab()
        if ws is None or not texts:
            self.unmark_untestable_wire()   # RELBUTTON-v1
            return
        scope, allrows = {}, {}
        for tr in range(2, ws.max_row + 1):
            u = str(ws.cell(tr, H['URL']).value or '').strip()
            src, d = str(ws.cell(tr, H['Source']).value or '').lower(), str(ws.cell(tr, H['Date']).value or '')[:10]
            if 'caucus' in src and 'office' not in src and d < '2020-11-18':
                continue
            if u in texts:
                allrows[u] = tr
                if u not in getattr(self, '_rel_new_urls', set()):   # BUTTONOPT-v1 (S5): new releases were matched already
                    scope[u] = tr
        rels = REL.releases(texts, set(scope))
        allrels = REL.releases(texts, set(allrows))   # RELBUTTON-v1: release-search passes + wire titles test this run's new ones too
        done = {x.get('aid') for x in self.res['releases_flagged']}
        passed = self._rel_pass_aids()
        for r in range(self.first_new_row + 1, self.s.last_row + 1):
            aid = self.s.get(r, 'Article ID')
            if aid in done:
                continue
            if aid in passed and passed[aid]['url'] in allrows:   # RELBUTTON-v1: a release-search find that passed in drop_skipped
                x = passed[aid]
                self._rel_mark(r, x['url'], x['title'], x['verdict'], ws, H, allrows[x['url']])
                continue
            cand = [x for x in rels if REL.in_window(self.s.get(r, 'Date'), x['date'])]
            vs = self.row_versions(r)
            m = REL.match(vs, cand) if cand else None
            if m == 'untestable' or (not cand and not REL.usable([v for v in vs if v.get('label') != 'excerpt'])):
                w = self._wire_copy(r, allrels)   # RELBUTTON-v1: PublicNow-style truncated title (RELCOPIES-v2 wire rule)
                if w:
                    x = w['_rel']
                    self._rel_mark(r, x['url'], x['title'], w, ws, H, allrows.get(x['url']))
                    continue
                hl = str(self.s.get(r, 'Headline') or '')
                x = next((x for x in cand if REL.title_near(hl, x['title'])), None)
                if x:
                    self.res['releases_untestable'].append({'aid': self.s.get(r, 'Article ID'), 'outlet': self.s.get(r, 'Outlet'),
                                                            'release': x['title'][:200], 'url': x['url'], 'why': 'no saved text'})
                continue
            if m:
                x = m['release']
                self._rel_mark(r, x['url'], x['title'], m['verdict'], ws, H, scope.get(x['url']))
                continue
            nc = self._near_copy(r, vs, [x for x in allrels if x['url'] in scope or x['url'] in allrows])   # RELBUTTON-v1
            if nc:
                x = nc['_rel']
                self._rel_mark(r, x['url'], x['title'], nc, ws, H, allrows.get(x['url']))
        self.unmark_untestable_wire()   # RELBUTTON-v1 (backend review #5)

    @staticmethod
    def _rel_body(text, title):
        """the release text from the page's markdown: from the title on, without the site's sidebar"""
        t = text
        i = t.find(title[:40]) if title else -1
        if i >= 0:
            t = t[i + len(title):]
        for stop in ('\n## Search', '\n## Connect', '\n## Offices', '\n#### Pagination', '\nShare this'):
            j = t.find(stop)
            if j > 0:
                t = t[:j]
        return re.sub(r'[#*_>\[\]]+', ' ', t).strip()

    # AVTAB-v1 sheet_task: every Podcast/Radio/TV/Video row this run added gets an "Audio & video details" row
    # BUTTONOPT-v1: also rows an edit turned into one (Medium), and any such row of a touched story that has no tab row
    # (every path that adds AV rows; AVDATE item 3); Channel + Show (AVSHOW-v1); a station video page never dates a row;
    # Episode / Broadcast segment / Video clip saves get a cleaned display copy (AVPREVIEW-v1 fix B)
    def _load_av_channels(self):
        """NOSHOWCHAN-v1: every Channel value already in the "Audio & video details" tab"""
        ch = set()
        if 'Audio & video details' in self.s.wb.sheetnames:
            ws = self.s.wb['Audio & video details']
            hdr = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
            if 'Channel' in hdr:
                i = hdr.index('Channel')
                ch = {str(x[i]).strip() for x in ws.iter_rows(min_row=2, values_only=True) if x and len(x) > i and x[i]}
        self._av_channels = tuple(sorted(ch)) or ('',)
        return self._av_channels

    def apply_av(self):
        self.res.setdefault('av_rows', []); self.res.setdefault('av_skipped', [])
        added = [a for k, v in self.res['runs'].items() for a in (v or {}).get('added', [])]
        added += [self.s.get(r, 'Article ID') for r in getattr(self, '_medium_edited', [])]
        if AV is not None and 'Audio & video details' in self.s.wb.sheetnames:   # touched stories' AV rows without a tab row
            have = {str(x[0]).strip() for x in self.s.wb['Audio & video details'].iter_rows(min_row=2, max_col=1, values_only=True) if x and x[0]}
            for sid in self.touched_stories:
                for r in self.s.story_rows.get(sid, []):
                    a = self.s.get(r, 'Article ID')
                    if a not in have and a not in added and str(self.s.get(r, 'Medium') or '').strip() in AV.MEDIA:
                        added.append(a)
        if not added:
            return
        if AV is None:
            self.res['av_skipped'].append({'why': 'avtab.py not loaded', 'n': len(added)}); return
        ph = {}      # real Article ID -> placeholder, and the run doc's av values
        extra = {}
        for rid, run in (self.db.get('runs') or {}).items():
            for p, real in ((self.res['runs'].get(rid) or {}).get('ids') or {}).items():
                ph[real] = p
            for p, vals in ((run or {}).get('av') or {}).items():
                extra[p] = vals or {}
        page_of = {x['aid']: x for x in self.res.get('pages', [])}
        rows = []
        for aid in dict.fromkeys(added):
            r = self.s.rows.get(aid)
            if not r or str(self.s.get(r, 'Medium') or '').strip() not in AV.MEDIA:
                continue
            cells = {c: self.s.get(r, c) for c in self.s.col}
            pi = page_of.get(aid) or {}
            pid = pi.get('page') or ph.get(aid)
            chk = self.page_checks.get(pid) if pid else None
            html = (chk or {}).get('html', '') if (chk or {}).get('verdict') == 'ok' else ''
            try:
                out = AV.extract(cells, html, '', src='Update button ' + self.today, today=self.today)
            except TypeError:
                out = AV.extract(cells, html, '', src='Update button ' + self.today)
            for c, v in (extra.get(ph.get(aid, ''), {}) or {}).items():
                if c in AV.COLS and v not in ('', None) and not out.get(c) and c not in ('Article ID', 'Story ID', 'Medium'):
                    out[c] = v
            clip = AV.archive_clip(cells.get('Publisher link'))   # AVTAB-v2 sheet_task: Coverage Date = Pacific air date
            if clip and out.get('Air/publish date'):
                cur = AV.s(cells.get('Date'))[:10]
                air = out['Air/publish date']
                if cur != air:
                    self.s.put(r, 'Date', air)
                    if 'Year' in self.s.col:
                        self.s.put(r, 'Year', int(air[:4]))
                    out['Notes'] = '; '.join(x for x in [n for n in out['Notes'].split('; ') if "clip ID's UTC date" not in n]
                                             + [f'Coverage Date set to the air date (clip ID UTC date {cur})'] if x)
                    self.res.setdefault('av_date_fixes', []).append({'aid': aid, 'old': cur, 'new': air})
            # AVTAB-v3 (AVDATE item 3): a station video page never dates a row, nor does the save day
            if hasattr(AV, 'station_video') and AV.station_video(cells, out.get('Item type', '')) and not out.get('Air/publish date'):
                d = AV.s(cells.get('Date'))[:10]
                if d and RR is not None and RR.todate(d) and abs((RR.todate(d) - RR.todate(self.today)).days) <= 3:
                    self.res['av_date_review'].append({'aid': aid, 'date': d, 'link': AV.s(cells.get('Publisher link')),
                                                       'why': "station video page: the Coverage Date is the save day, not the clip's air date; check it"})
            if hasattr(AV, 'guard_show'):   # NOSHOWCHAN-v1: a channel/station/network name never sits in Show/program
                mv = AV.guard_show(out, AV.s(cells.get('Outlet')), getattr(self, '_av_channels', None) or self._load_av_channels())
                if mv:
                    self.res.setdefault('av_show_to_channel', []).append({'aid': aid, 'value': mv})
            rows.append(out)
            e = {'aid': aid, 'type': out['Item type'], 'role': out['His role'], 'transcript': out['Transcript kind'],
                 'channel': out.get('Channel', ''), 'show': out.get('Show/program', '')}
            self.res['av_rows'].append(e)
            # Sammy 2026-10-28: no channel -> Channel stays blank and is not listed for review (av_no_channel retired)
            # AVPREVIEW-v1 fix B: the viewer copy of a new AV save is the display-cleaned page (library file stays as clean_html made it)
            if AVC is not None and out.get('Item type') in ('Episode', 'Broadcast segment', 'Video clip') and aid in self.saved_html and pi:
                try:
                    dh = AVC.clean(self.saved_html[aid], AV.s(cells.get('Language')) or 'English')[0]
                    sid = AV.s(cells.get('Story ID'))
                    if getattr(self, 'pages_dir', None) and sid:
                        import os
                        os.makedirs(os.path.join(self.pages_dir, '_display'), exist_ok=True)
                        with open(os.path.join(self.pages_dir, '_display', sid + '.html'), 'w', encoding='utf-8') as f:
                            f.write(dh)
                        pi['display'] = f'_display/{sid}.html'
                    self.saved_html['display:' + aid] = dh
                except Exception as _e:
                    pi['display_error'] = repr(_e)[:200]
        if rows:
            AV.write_tab(self.s.wb, rows)

    # ---------- BUTTONOPT-v1: removal requests execute (Sammy 2026-10-28) ----------
    def execute_removals(self):
        """every row of a story removed in the tracker moves to the "Removed" tab (the A/V tab row with it, as text); its library
        files are listed for the run to move to _to_delete/. Runs last; the sheet's row index is not used afterwards."""
        if not self.removals:
            return
        wb = self.s.wb
        if 'Removed' not in wb.sheetnames:
            for sid, at in self.removals:
                self.res['removal_failed'].append({'story': sid, 'why': 'no "Removed" tab in the workbook'})
                self.res['edits_keep'].append(sid)
            return
        rm = wb['Removed']
        RH = [c.value for c in rm[1]]
        av = wb['Audio & video details'] if 'Audio & video details' in wb.sheetnames else None
        avh = [c.value for c in av[1]] if av is not None else []
        rows = []
        for key, at in self.removals:
            sid = self.resolve_sid(key)
            rs = sorted(self.s.story_rows.get(sid, []))
            if not rs:   # already moved (by hand or an earlier run): nothing to do, the request is cleared
                self.res['removed'].append({'story': key, 'sid': sid, 'rows': [], 'note': 'no Coverage rows with this Story ID (already removed)'})
                self.res['edits_clear'].append(key)
                continue
            moved = []
            for r in rs:
                vals = {c: self.s.get(r, c) for c in self.s.col}
                aid = norm_val(vals.get('Article ID'))
                other = ''
                if av is not None:
                    for ar in range(av.max_row, 1, -1):
                        if norm_val(av.cell(ar, 1).value) == aid:
                            other = 'Audio & video details: ' + ' | '.join(f'{h}={norm_val(av.cell(ar, i + 1).value)}' for i, h in enumerate(avh)
                                                                            if h and not blank(av.cell(ar, i + 1).value))
                            av.delete_rows(ar)
                            break
                line = {'From tab': 'Coverage', 'Removed on': self.today, 'Category': '5 removed in the tracker',
                        'Reason removed': f"Removed in the tracker (Remove story, {str(at)[:10]}); moved by the Update button's sheet task ({self.today}).",
                        'Other tab row (as removed)': other or None}
                line.update({c: v for c, v in vals.items() if c in RH})
                n = rm.max_row + 1
                for ci, h in enumerate(RH, start=1):
                    c = rm.cell(n, ci)
                    c._style = copy.copy(rm.cell(n - 1, ci)._style)
                    c.value = line.get(h)
                year = norm_val(vals.get('Date'))[:4] or norm_val(vals.get('Year'))[:4]
                files = [f'{year}/{norm_val(vals.get(c))}' for c in ('File name', 'File name 2')
                         if re.search(r'\.(html?|pdf)$', norm_val(vals.get(c)), re.I)]
                moved.append({'aid': aid, 'files': files, 'originals': [f'_original_html/{f}' for f in files if f.endswith('.html')]})
                rows.append(r)
            self.res['removed'].append({'story': key, 'sid': sid, 'rows': moved})
            self.res['edits_clear'].append(key)
        for r in sorted(set(rows), reverse=True):
            self.s.ws.delete_rows(r)
        self.s.last_row -= len(set(rows))
        self.s.rows, self.s.story_rows = {}, {}   # row numbers shifted: index again (Article ID / Story ID only)
        for r in range(2, self.s.last_row + 1):
            aid, sid = self.s.get(r, 'Article ID'), self.s.get(r, 'Story ID')
            if not blank(aid):
                self.s.rows[aid] = r
            if not blank(sid):
                self.s.story_rows.setdefault(sid, []).append(r)
        self.first_new_row -= sum(1 for r in set(rows) if r <= self.first_new_row)

    # ---------- BUTTONOPT-v1: red row font on appended rows the tracker won't show (DECISIONS 102) ----------
    def mark_red(self):
        red = Font(color='00C00000')
        pr = lambda r: str(self.s.get(r, 'Press release') or '').strip().lower() == 'yes'
        cand = set(range(self.first_new_row + 1, self.s.last_row + 1)) | {self.s.rows.get(x['aid']) for x in self.res.get('releases_flagged', [])}
        for r in sorted(x for x in cand if x):
            kind = self.s.get(r, 'Original or reprint')
            o = self.s.original_row(self.s.get(r, 'Story ID')) if kind == 'Reprint' else r
            if not (pr(r) or kind not in ('Original', 'Reprint') or o is None or pr(o)):
                continue
            for c in range(1, len(self.s.hdr) + 1):
                cell = self.s.ws.cell(r, c)
                f = copy.copy(cell.font)
                cell.font = Font(name=f.name, sz=f.sz, b=f.b, i=f.i, u=f.u, strike=f.strike, vertAlign=f.vertAlign, color=red.color)
            self.res['red_rows'].append(self.s.get(r, 'Article ID'))

    # ---------- BUTTONOPT-v1 (T4): the tracker's viewer copies of this run's saves, merged into the staged articles shards ----------
    def copies_out(self, out_dir):
        """--copies-out DIR: articles/<shard>.json + manifest.json (+ releases.json) from --copies with this run's new copies added
        (a story's copy = its Original's saved page, the display copy for AV saves; release copies keyed by Release ID). Only the
        files that changed are written; result `copies_changed` lists them for step 7."""
        import os
        if not (out_dir and self.copies_dir):
            return
        try:
            man = json.load(open(os.path.join(self.copies_dir, 'articles', 'manifest.json'), encoding='utf-8'))
        except Exception as _e:
            self.res['copies_note'] = f'no articles/manifest.json in --copies ({_e!r}): copies not added'
            return
        arts, changed = man.setdefault('articles', {}), {}

        def shard(name):
            if name not in changed:
                try:
                    changed[name] = json.load(open(os.path.join(self.copies_dir, 'articles', name), encoding='utf-8'))
                except Exception:
                    changed[name] = {}
            return changed[name]
        for x in self.res.get('pages', []):
            r = self.s.rows.get(x['aid'])
            if not r or self.s.get(r, 'Original or reprint') != 'Original':
                continue
            sid = norm_val(self.s.get(r, 'Story ID'))
            html = self.saved_html.get('display:' + x['aid']) or self.saved_html.get(x['aid'])
            if not sid or not html or sid in arts:
                continue
            year = x['file'].split('/')[0]
            names = sorted({v.split('/')[-1] for v in arts.values() if re.match(rf'^{year}(-\d+)?\.json$', v.split('/')[-1])},
                           key=lambda n: int((re.search(r'-(\d+)\.json$', n) or [0, 1])[1]))
            name = names[-1] if names else f'{year}.json'
            shard(name)[sid] = html
            arts[sid] = f'articles/{name}'
        rnames = sorted({v.split('/')[-1] for v in arts.values() if re.match(r'^releases(-\d+)?\.json$', v.split('/')[-1])},
                        key=lambda n: int((re.search(r'-(\d+)\.json$', n) or [0, 1])[1]))
        for x in self.res.get('release_copies', []):
            html = self.saved_html.get('release:' + x.get('prid', ''))
            if html and x['prid'] not in arts:
                name = rnames[-1] if rnames else 'releases.json'
                shard(name)[x['prid']] = html
                arts[x['prid']] = f'articles/{name}'
        if not changed:
            return
        os.makedirs(os.path.join(out_dir, 'articles'), exist_ok=True)
        for name, d in changed.items():
            json.dump(d, open(os.path.join(out_dir, 'articles', name), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        json.dump(man, open(os.path.join(out_dir, 'articles', 'manifest.json'), 'w'), separators=(',', ':'))
        self.res['copies_changed'] = ['articles/' + n for n in sorted(changed)] + ['articles/manifest.json']

    # ---------- derived ----------
    def recount(self):
        """Delta update: existing count + new distinct outlets (not the original's, not already
        in the story). Outlets are matched by norm_outlet with the row's Outlet city (outlet_rules.json,
        OUTLETRULES-v1: aliases, editions, feeds, generic names by city; the former Reprint info tab rules)."""
        for sid in sorted(self.touched_stories):
            o = self.s.original_row(sid)
            if o is None:
                continue
            rows = self.s.story_rows.get(sid, [])
            old_rows = [r for r in rows if r <= self.first_new_row]
            new_rows = [r for r in rows if r > self.first_new_row and self.s.get(r, 'Original or reprint') == 'Reprint']
            no = lambda r: norm_outlet(self.s.get(r, 'Outlet'), self.s.get(r, 'Outlet city'))   # OUTLETRULES-v1
            seen = {no(r) for r in old_rows} | {no(o)}
            add = {no(r) for r in new_rows} - seen - {''}
            cur = self.s.get(o, '# of reprints')
            base = 0 if blank(cur) else int(float(cur))
            n = base + len(add)
            if blank(cur) or n != base:
                self.s.put(o, '# of reprints', n)
                self.res['reprint_counts'][sid] = {'old': cur, 'new': n, 'new_outlets': sorted(add)}

    def run(self, pages_dir=None):
        self.pages_dir = pages_dir   # RELCHECK-v2
        self.norm_preloaded()
        self.apply_runs()
        self.apply_reprint_docs()
        self.apply_tones()
        self.apply_authors()
        self.apply_translations()
        self.apply_edits()
        self.apply_pages(pages_dir)
        self.apply_bills()   # AUTO-v1
        self.apply_releases()   # RELCHECK-v1
        self.apply_release_finds()   # RELCHECK-v2
        self.apply_related_cols(getattr(self, 'release_related', None))   # RELBUTTON-v1: Copies (rows) / First copy date / Related
        self.apply_av()   # AVTAB-v1
        self.recount()
        self.mark_red()   # BUTTONOPT-v1 (DECISIONS 102)
        self.execute_removals()   # BUTTONOPT-v1: last (row numbers shift)
        seen = set()   # BUTTONOPT-v1 (S5): one untestable entry per row and release
        self.res['releases_untestable'] = [x for x in self.res['releases_untestable'] if (x.get('aid'), x.get('url')) not in seen and not seen.add((x.get('aid'), x.get('url')))]
        self.res['pages_drop'] = sorted({p for p in self.res['pages_drop'] if p})
        self.relmatch_lists()   # RELBUTTON-v1
        return self.res


def rebuild_originals(sheet):
    wb, ws = sheet.wb, sheet.ws
    if 'Originals' in wb.sheetnames:
        old = wb['Originals']
        idx = wb.sheetnames.index('Originals')
        widths = {k: v.width for k, v in old.column_dimensions.items()}
        wb.remove(old)
    else:
        idx, widths = 1, {}
    o = wb.create_sheet('Originals', idx)
    cols = [i + 1 for i, h in enumerate(sheet.hdr) if h and h not in SKIP_IN_ORIGINALS]
    rows = [1] + [r for r in range(2, sheet.last_row + 1) if sheet.get(r, 'Original or reprint') == 'Original']
    for oi, r in enumerate(rows, start=1):
        for oc, c in enumerate(cols, start=1):
            s = ws.cell(r, c)
            d = o.cell(oi, oc)
            d.value = s.value
            d._style = copy.copy(s._style)
    from openpyxl.utils import get_column_letter
    for oc, c in enumerate(cols, start=1):
        L = get_column_letter(oc)
        w = ws.column_dimensions[get_column_letter(c)].width or widths.get(L)
        if w:
            o.column_dimensions[L].width = w
    o.freeze_panes = 'C2'
    o.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{len(rows)}'
    ws.auto_filter.ref = f'A1:{get_column_letter(len(sheet.hdr))}{sheet.last_row}'
    return len(rows) - 1


def verify(before_path, after_path, res):
    import pandas as pd
    b = pd.read_excel(before_path, sheet_name='Coverage', dtype=object)
    a = pd.read_excel(after_path, sheet_name='Coverage', dtype=object)
    problems = []
    if list(a.columns[:len(b.columns)]) != list(b.columns):
        problems.append('column order changed')
    a_idx = a.set_index('Article ID')
    allowed = {(sid, '# of reprints') for sid in res['reprint_counts']}
    removed = {x['aid'] for e in res.get('removed', []) for x in e.get('rows', [])}   # BUTTONOPT-v1: moved to the Removed tab
    if removed:
        try:
            rm = pd.read_excel(after_path, sheet_name='Removed', dtype=object)
            miss = removed - set(rm['Article ID'].dropna().astype(str))
            if miss:
                problems.append(f'removed rows not on the Removed tab: {sorted(miss)[:5]}')
        except Exception as _e:
            problems.append(f'Removed tab unreadable: {_e!r}'[:200])
    old_ids = set(b['Article ID'].dropna().astype(str))
    for _, row in a[~a['Article ID'].astype(str).isin(old_ids)].iterrows():   # BUTTONOPT-v1 (blankfill rootfix C)
        if row.get('Original or reprint') == 'Original':
            o = norm_val(row.get('Outlet'))
            if not o or BARE_HOST.match(o):
                problems.append(f"{row.get('Article ID')}: new Original with a blank Outlet or a site address as Outlet ({o!r})")
    for _, row in b.iterrows():
        aid = row['Article ID']
        if pd.isna(aid):
            continue
        if aid not in a_idx.index:
            if aid not in removed:
                problems.append(f'{aid}: row missing')
            continue
        ar = a_idx.loc[aid]
        for c in b.columns:
            if c == 'Article ID' or pd.isna(row[c]):
                continue
            if (row.get('Story ID'), c) in allowed:
                continue
            if norm_val(row[c]) != norm_val(ar[c]):
                problems.append(f'{aid} / {c}: {norm_val(row[c])[:60]!r} -> {norm_val(ar[c])[:60]!r}')
    # Originals tab mirrors Coverage originals
    o = pd.read_excel(after_path, sheet_name='Originals', dtype=object)
    co = a[a['Original or reprint'] == 'Original']
    if len(o) != len(co) or list(o['Article ID']) != list(co['Article ID']):
        problems.append('Originals tab does not match Coverage originals')
    ids = pd.concat([a['Article ID'], a['Print Article ID']]).dropna().astype(str)
    dup = ids[ids.duplicated()]
    if len(dup):
        problems.append(f'duplicate Article IDs: {list(dup)[:5]}')
    return {'ok': not problems, 'problems': problems[:50], 'rows_before': len(b), 'rows_after': len(a),
            'originals': len(o)}


def run_done(run):
    """BUTTONOPT-v1 (S1): a run was applied when it has ids or a sheet line (a run whose rows were all skipped keeps ids {})"""
    run = run or {}
    return bool(run.get('ids')) or bool((run.get('sheet') or {}).get('at'))


def has_work(db):
    """TOKENS-v1: anything for the sheet task to write? (runs not yet applied, bills from the Update button, edits not yet
    reported, hand-added reprints not yet written, pages waiting). No -> the run stops before staging the workbook.
    BUTTONOPT-v1 (S1): applied = ids or a sheet line; an edit already reported (reported >= at) is not work."""
    runs = (db.get('runs') or {}).values()
    why = {'runs': sum(1 for r in runs if (r or {}).get('rows') and not run_done(r)),
           'bills': sum(1 for r in runs if (r or {}).get('bills_new') and not ((r or {}).get('sheet') or {}).get('at')),
           'releases': sum(1 for r in runs if (r or {}).get('releases_new') and not ((r or {}).get('sheet') or {}).get('at')),   # RELCHECK-v1
           'edits': sum(1 for e in (db.get('edits') or {}).values() if (e or {}).get('removed') or not ((e or {}).get('reported') and str(e['reported']) >= str((e or {}).get('at') or ''))),
           'reprints': sum(1 for d in (db.get('reprints') or {}).values() if not (d or {}).get('aid')),
           'pages': len(db.get('pages') or {})}
    return any(why.values()), why


def load_db(path=None, db_dir=None):
    """BUTTONOPT-v1 (T1): the db from ArtifactData `list` output written with out_dir (DIR/<collection>/<doc id>.json, or
    DIR/<collection>.json holding {doc id: doc} or a list of {id, data}), so the task never reads the docs into context"""
    import os, glob
    if not db_dir:
        return json.load(open(path, encoding='utf-8'))
    db = {}
    for c in ('runs', 'edits', 'tones', 'authors', 'translations', 'pages', 'reprints'):
        d = db.setdefault(c, {})
        for f in sorted(glob.glob(os.path.join(db_dir, c, '*.json'))):
            try:
                d[os.path.basename(f)[:-5]] = json.load(open(f, encoding='utf-8'))
            except ValueError:
                pass
        f = os.path.join(db_dir, c + '.json')
        if os.path.exists(f):
            x = json.load(open(f, encoding='utf-8'))
            if isinstance(x, dict) and isinstance(x.get('docs') or x.get('items'), list):
                x = x.get('docs') or x.get('items')
            if isinstance(x, list):
                x = {str(e.get('id') or e.get('doc_id')): (e.get('data') if isinstance(e.get('data'), dict) else e) for e in x if isinstance(e, dict)}
            d.update(x or {})
    if path:
        json.dump(db, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
    return db


def copies_needed(db, sheet=None):
    """BUTTONOPT-v1 (S4): the articles shards the reprint and release checks read: years of finds' dates +-90 days (REPRINT90),
    of their stories (reprint rows), and of queued releases' dates -14..+90 days (release rule -1..+30, RELRELATED pre -14, +90)"""
    import datetime as _d
    yrs = set()
    def span(d, a, b):
        t = RR.todate(d) if RR is not None else None
        if t:
            yrs.update(range((t + _d.timedelta(days=a)).year, (t + _d.timedelta(days=b)).year + 1))
    for run in (db.get('runs') or {}).values():
        if run_done(run):
            continue
        for o in (run or {}).get('rows') or []:
            span(o.get('Date'), -90, 90)
            if sheet is not None and o.get('Original or reprint') == 'Reprint':
                r = sheet.original_row(str(o.get('Story ID') or ''))
                if r:
                    span(norm_val(sheet.get(r, 'Date')), 0, 0)
            for c in ((o.get('_origin') or {}).get('cands') or []) if isinstance(o.get('_origin'), dict) else []:
                span(c.get('date'), -90, 90)
        for x in (run or {}).get('releases_new') or []:
            if isinstance(x, dict):
                span(str(x.get('date', ''))[:10], -14, 90)   # RELBUTTON-v1 (backend review #12): `pre` needs -14
    return ['articles/manifest.json'] + [f'articles/{y}.json' for y in sorted(yrs)]


def release_candidates(db, sheet):   # RELCHECK-v2
    """library files (<year>/<file>) of Coverage rows dated 1 day before .. 30 days after a queued new release whose headline
    overlaps it: stage these into --library so the text rule can read them"""
    if REL is None or RR is None:
        return []
    rels = []
    for rid, run in sorted((db.get('runs') or {}).items()):
        if ((run or {}).get('sheet') or {}).get('at'):
            continue
        rels += [x for x in (run or {}).get('releases_new') or [] if isinstance(x, dict)]
    out = []
    for r in range(2, sheet.last_row + 1):
        hl, d = str(sheet.get(r, 'Headline') or ''), sheet.get(r, 'Date')
        if not any(REL.in_window(d, str(x.get('date', ''))[:10]) and REL.title_near(hl, str(x.get('title', ''))) for x in rels):
            continue
        for col in ('File name', 'File name 2'):
            fn = str(sheet.get(r, col) or '').strip()
            if fn and re.search(r'\.(html?|pdf)$', fn, re.I):
                p = str(d or '')[:4] + '/' + fn
                if p not in out:
                    out.append(p)
    return out


def sheet_line(res):
    """BUTTONOPT-v1: the run's one-line report, built once (was three string-replace passes)"""
    c, n = res['counts'], lambda k: len(res.get(k) or [])
    pl = lambda k, w, ws=None: f"{k} {w if k == 1 else (ws or w + 's')}"
    parts = [pl(c['rows_added'], 'row') + ' added', pl(n('applied'), 'cell') + ' filled']
    add = lambda k, txt: parts.append(txt) if k else None
    add(n('conflicts'), f"{n('conflicts')} conflicts left for Sammy")
    add(n('removed'), f"{sum(len(x['rows']) for x in res['removed'])} rows of {n('removed')} removed stories moved to the Removed tab")
    add(n('removal_failed'), f"{n('removal_failed')} removals not done (see review)")
    add(n('skipped'), f"{n('skipped')} finds skipped (California Files, listing pages, other Gabriels or Gabriel only outside the article)")
    add(n('held'), f"{n('held')} finds held: outlet or format unknown (see review)")
    add(n('pages_error'), f"{n('pages_error')} pages not saved (RETRY or BLOCKED – TinyFish)")
    rc = c.get('reprint_check', 0)
    add(rc, f"{rc} finds written as reprints (same text as another story)" + (f" ({c['reprint_check_low']} low confidence, see review)" if c.get('reprint_check_low') else ''))
    add(n('reprint_failed'), f"{n('reprint_failed')} proposed reprints added as stories of their own (not the same text)")
    add(n('reprint_untested'), f"{n('reprint_untested')} reprints with no text to test (see review)")
    add(n('origin_added'), f"{n('origin_added')} originating outlets added as the Original")
    add(n('bills_new'), f"{n('bills_new')} new bills from leginfo")
    add(n('releases_new'), f"{n('releases_new')} new official press releases on the Press releases tab"
        + (f" ({n('releases_flagged')} Coverage rows marked Press release = Yes, see review)" if n('releases_flagged') else ''))
    add(n('releases_untestable'), f"{n('releases_untestable')} rows near a release with no saved text to test (see review)")
    add(n('releases_review'), f"{n('releases_review')} release copies to check by hand (see review)")   # RELBUTTON-v1
    add(n('releases_unmarked'), f"{n('releases_unmarked')} wire rows with no text unmarked (not his releases)")
    add(n('releases_dual'), f"{n('releases_dual')} caucus copies of office releases merged")
    dr = n('date_review') + n('av_date_review')
    add(dr, f"{dr} dates to check (see review)")
    add(n('av_rows'), f"{n('av_rows')} rows on the Audio & video details tab")
    return ', '.join(parts) + '.'


def after_relmatch(a):
    """RELBUTTON-v1: --after-relmatch STATE --xlsx OUT1 --out OUT2 --result R2 [--prev-result R1] [--pages-dir] [--library]
    [--copies] [--bills]. Press releases tab: Has copies / Copies (rows) / First copy date / Related count / Related story IDs
    recomputed; review-queue docs (result.queue_docs) for this run's stories. Coverage is verified unchanged. Exit 2 = verify failed."""
    if not (a.xlsx and a.out and a.result):
        sys.exit('--after-relmatch needs --xlsx, --out and --result')
    if a.out == a.xlsx:
        sys.exit('refusing to overwrite the input workbook; write to a new file')
    prev = json.load(open(a.prev_result, encoding='utf-8')) if a.prev_result else {}
    sheet = Sheet(a.xlsx)
    task = Task(sheet, {}, a.today)
    task.pages_dir, task.library_dir, task.copies_dir, task.bills_path = a.pages_dir, a.library, a.copies, a.bills
    task.first_new_row = sheet.last_row
    state = json.load(open(a.after_relmatch, encoding='utf-8'))
    task.apply_related_cols(state)
    docs = task.queue_after(state, (prev.get('relmatch') or {}).get('stories', []), prev.get('queue'))
    sheet.wb.save(a.out)
    res = {'at': task.res['at'], 'related_cols': task.res['related_cols'], 'queue_docs': docs,
           'queue_counts': {k: len(v) for k, v in task.res['queue'].items()}, 'reprint_counts': {}, 'removed': []}
    res['verify'] = verify(a.xlsx, a.out, res)
    json.dump(res, open(a.result, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
    print(json.dumps({'related_cols': res['related_cols'], 'queue': res['queue_counts'], 'verify': res['verify']}, indent=1, default=str))
    return 0 if res['verify']['ok'] else 2


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', help='db export {collection: {doc_id: doc}} (with --db-dir: where to save the assembled export)')
    ap.add_argument('--db-dir', help='BUTTONOPT-v1 (T1): ArtifactData list output folder (<collection>/<doc id>.json); read instead of --db')
    ap.add_argument('--xlsx')
    ap.add_argument('--out')
    ap.add_argument('--result')
    ap.add_argument('--check-only', action='store_true', help='print whether anything is queued (TOKENS-v1); exit 0 = work, 3 = nothing')
    ap.add_argument('--copies-needed', action='store_true', help='BUTTONOPT-v1 (S4): print the articles shards to stage into --copies and exit')
    ap.add_argument('--pages-dir')
    ap.add_argument('--today', default=datetime.date.today().isoformat())
    ap.add_argument('--idmap', help='idmap.json from build_data.py (old code -> Story ID), optional fallback')
    ap.add_argument('--copies', help='folder holding the tracker\'s articles/manifest.json + articles/<year>.json (AUTO-v1 reprint check)')
    ap.add_argument('--copies-out', help='BUTTONOPT-v1 (T4): write the changed articles/*.json + manifest (this run\'s new copies added) here')
    ap.add_argument('--img-cache', help='PHOTOS-v2 F6: image cache folder (img_embed.py format); photos of new saves are embedded')
    ap.add_argument('--bills', help='gabriel_bills_leginfo.json to append new bills to (AUTO-v1; the pipeline copy)')
    ap.add_argument('--release-texts', help='release_texts.json (RELCHECK-v2; the pipeline copy, new releases appended)')
    ap.add_argument('--library', help='folder with staged library files <year>/<file> for the release text rule (RELCHECK-v2)')
    ap.add_argument('--release-candidates', action='store_true', help='print the library files (<year>/<file>) to stage for --library and exit (RELCHECK-v2)')
    ap.add_argument('--release-related', help='RELBUTTON-v1: release_related.json (the pipeline copy, as before this run): the tab\'s Related count / Related story IDs are recomputed from it')
    ap.add_argument('--after-relmatch', metavar='STATE', help='RELBUTTON-v1: second pass after relmatch --update: recompute the tab\'s derived columns from STATE '
                    '(release_related.json) and write review-queue items for --prev-result\'s stories; only the Press releases tab changes')
    ap.add_argument('--prev-result', help='RELBUTTON-v1 (with --after-relmatch): result.json of the main pass (its relmatch lists and near-copy queue)')
    a = ap.parse_args(argv)
    if a.after_relmatch:
        return after_relmatch(a)
    if not (a.db or a.db_dir):
        sys.exit('--db or --db-dir is required')
    db = load_db(a.db if not a.db_dir else (a.db or None), a.db_dir)
    # TOKENS-v1 sheet_task: nothing queued -> stop (no workbook, no rebuild, no republish)
    work, why = has_work(db)
    if a.check_only:
        print(json.dumps({'work': work, 'queued': why, 'master': MASTER_XLSX, 'lock': MASTER_LOCK, 'backups': BACKUPS_DIR}))
        return 0 if work else 3
    if a.copies_needed:
        print(json.dumps(copies_needed(db, Sheet(a.xlsx) if a.xlsx else None)))
        return 0
    if a.release_candidates:   # RELCHECK-v2: rows near a queued release whose saved copy the text rule needs
        if not a.xlsx:
            sys.exit('--release-candidates needs --xlsx')
        print(json.dumps(release_candidates(db, Sheet(a.xlsx))))
        return 0
    if not (a.xlsx and a.out and a.result):
        sys.exit('--xlsx, --out and --result are required unless --check-only')
    if a.out == a.xlsx:
        sys.exit('refusing to overwrite the input workbook; write to a new file')
    sheet = Sheet(a.xlsx)
    task = Task(sheet, db, a.today)
    task.copies_dir, task.bills_path = a.copies, a.bills   # AUTO-v1
    task.release_texts, task.library_dir = a.release_texts, a.library   # RELCHECK-v2
    task.img_cache = a.img_cache   # PHOTOS-v2 F6
    task.release_related = a.release_related   # RELBUTTON-v1
    if a.idmap:
        task.idmap = {str(k).lower(): v for k, v in json.load(open(a.idmap, encoding='utf-8')).items()}
    res = task.run(a.pages_dir)
    task.copies_out(a.copies_out)   # BUTTONOPT-v1 (T4)
    n_orig = rebuild_originals(sheet)
    sheet.wb.save(a.out)
    res['counts'] = {'rows_added': sum(len(v['added']) for v in res['runs'].values()),
                     'cells_filled': len(res['applied']), 'conflicts': len(res['conflicts']),
                     'duplicates': len(res['duplicates']), 'removals_requested': len(res['removals_requested']),
                     'pages': len(res['pages']), 'reprint_counts_changed': len(res['reprint_counts']),
                     'originals': n_orig}
    res['counts'].update({'next_aid': '%05d' % (sheet.max_num + 1), 'next_s': 's%05d' % (sheet.max_s + 1)}
                         if sheet.new_scheme else {'next_ws': sheet.max_ws + 1, 'next_jg': sheet.max_jg + 1})
    # CLEAN-v1: the tracker leaves press releases out (build_data.py), so step 8 compares with this count
    res['counts']['tracker_stories'] = sum(1 for r in range(2, sheet.last_row + 1)
                                           if sheet.get(r, 'Original or reprint') == 'Original'
                                           and str(sheet.get(r, 'Press release') or '').strip().lower() != 'yes')
    res['counts'].update({k: len(res.get(k) or []) for k in (
        'skipped', 'pages_error', 'pages_skipped', 'pages_flagged', 'press_releases', 'gabriel_unclear', 'authors_split', 'bills_new',
        'date_fixes', 'date_review', 'av_rows', 'pages_drop', 'reprint_failed', 'reprint_untested', 'origin_added', 'origin_unverified',
        'held', 'outlet_unresolved', 'removed', 'edits_reported', 'red_rows', 'av_date_review')})
    res['counts'].update({'reprint_check': sum(1 for x in res['reprint_check'] if x.get('mode')),   # AUTO-v1
                          'reprint_check_low': sum(1 for x in res['reprint_check'] if x.get('conf') == 'low'),
                          'reprint_check_order': sum(1 for x in res['reprint_check'] if x.get('order')),
                          'reach_changed': len(res['reach'])})
    res['verify'] = verify(a.xlsx, a.out, res)
    res['sheet_stories'] = sorted(task.touched_stories)
    res['sheet_line'] = sheet_line(res)
    json.dump(res, open(a.result, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
    print(json.dumps({'counts': res['counts'], 'verify': res['verify'], 'line': res['sheet_line']}, indent=1, default=str))
    return 0 if res['verify']['ok'] else 2


if __name__ == '__main__':
    sys.exit(main())
