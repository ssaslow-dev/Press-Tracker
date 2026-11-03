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
  * REPRINT-v2 (reprint-code, 2026-10-28; build/REPRINT_PLAN.md): new rows follow the same rules as the regroup. Finds are tested
    against candidates by type pair (an aggregator / station / chain find against every originator-type Original in 90 days),
    reprint_rule.pair_class decides the cell (AV <-> text never; same outlet = edition; wire <-> wire never; containment of a
    credited trim = Reprint; a credited translation <= 2 days = Reprint), and the originals order v2 (credited service -> the
    reporter's employer, reporters.py -> originator type -> byline -> date) SWAPS the Original when the find outranks the
    existing one by class (not date alone): the old Original becomes a Reprint, Tone / Topic / Bills carry blank-only
    (`origin_swaps`; verify allows exactly those cells). Newsroom-vs-newsroom date ties are still only reported (`order`).
    A proven originator on a blocked site (LA Times, Bee, Chronicle, KTLA, Politico) is added as a no-copy Original row.
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
try:
    import lookup_cache as LC        # LEARN-v1: reference data first; this cache answers a URL before any web fetch
    LC_ERR = ''
except Exception as _e:
    LC, LC_ERR = None, repr(_e)
RETRY = 'RETRY – TinyFish'
# AUTO-v1 sheet_task (agent-code, 2026-10-27): the manual steps of 2026-10-27 for new finds (see Task.reprint_check etc.)
BLOCKED = 'BLOCKED – TinyFish'   # DECISIONS 2026-10-27: blocked / paywall / login pages; other bad pages keep RETRY
try:
    import shownet as SN             # SHOWNET-v1: the show is not the outlet
except Exception:
    SN = None
try:
    import agg_origin as AO          # AGGORIGIN-v1: an aggregator / syndicator find is never the Original
except Exception as _e:   # noqa
    AO = None
try:
    import reprint_rule as RR        # the regroup's string-of-text reprint rule (reprint_rule.py next to this script)
except Exception as _e:
    RR = None
try:
    import release_rule as REL       # RELCHECK-v2: the release text rule (release_rule.py next to this script)
except Exception as _e:
    REL = None
try:
    import reporters as REP          # REPRINT-v2: the reporter's employer on the story date (reporters.py + reporter_employment.csv)
except Exception as _e:
    REP = None
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
    import date_rules as DR          # DATES-v1: the eight date sanity checks + Date source (date_rules.py, dates_lib.py next to this script)
except Exception:
    DR = None
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


_MIRROR_LABEL = re.compile(r'^(?:qa\d+-web-vercel|amp|m|mobile|www\d+|edition|beta|staging|preview)\.')


def canon_mirror(u):
    """REQ-14 (UPDFIX-v1): a publisher's staging / amp / mobile mirror is the same page: strip a leading mirror label from the host and unwrap
    the *.cdn.ampproject.org/c/s/ wrapper. `u`: lower-case, scheme and www already removed. Keep in sync with build_data.py and the page (normU)."""
    m = re.match(r'^[^/]*\.cdn\.ampproject\.org/[cv]/s/(.*)$', u)
    if m:
        u = re.sub(r'^www\.', '', m.group(1))
    host, sl, rest = u.partition('/')
    h2 = _MIRROR_LABEL.sub('', host)
    if h2 != host and h2.count('.') >= 1:
        host = h2
    return host + sl + rest


def norm_url(u):
    """Exact mirror of build_data.py's norm_url (keep the two in sync)."""
    u = str(u if u is not None else '').strip()
    if not u.startswith('http'):
        return ''
    u = canon_mirror(re.sub(r'^https?://(www\.)?', '', u.lower()).split('#')[0])   # REQ-14: mirror hosts
    host = u.split('/')[0]
    # NewsBank / proxy / Google links identify the article only in the query string: keep it
    # YTLINK-v1: a YouTube watch link identifies the video only in its query string (?v=ID): keep it
    if not re.search(r'newsbank|oclc|google\.|proquest|(^|\.)youtube\.com$', host):
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


# ---------- FORMAT-v1 (Sammy 2026-10-29): per-row "Format" = what the row IS, separate from the outlet's Medium ----------
# Article | Broadcast segment | Video clip | Audio segment | Podcast episode | Print. The backfill (work/tmp_v23_outlets/changes.csv) reads the
# AV tab Item type, Edition and the link; a NEW row gets it here: Edition Print -> Print; link/host patterns; the AV Item type
# overrides once apply_av has extracted it (format_from_av).
FORMAT_VALUES = ('Article', 'Broadcast segment', 'Video clip', 'Audio segment', 'Podcast episode', 'Print')
_VIDEO_HOST = re.compile(r'(^|\.)(youtube\.com|youtu\.be|vimeo\.com|tiktok\.com)$')
_PODCAST_HOST = re.compile(r'(^|\.)(podcasts\.apple\.com|open\.spotify\.com|podbean\.com|omny\.fm|simplecast\.com|buzzsprout\.com|megaphone\.fm|soundcloud\.com|podcastrex\.com)$')


def format_from_av(item_type, medium=''):
    """AV tab Item type (+ the row's Medium) -> Format; '' when the Item type says nothing (the caller keeps what it has)"""
    it, med = str(item_type or '').strip(), str(medium or '').strip()
    if it == 'Broadcast segment':
        return 'Audio segment' if med == 'Radio' else 'Broadcast segment'
    if it == 'Video clip':
        return 'Video clip'
    if it == 'Episode':
        return 'Podcast episode' if med == 'Podcast' else 'Audio segment'
    if it == 'Web story':
        return 'Article'
    return ''


def format_of(vals, av_item=''):
    """FORMAT-v1: Format for a new row from what is known at creation (vals = the row's cells). AV Item type first, then Edition
    Print, then the link's host / path; everything else is an Article."""
    f = format_from_av(av_item, vals.get('Medium'))
    if f:
        return f
    if str(vals.get('Edition') or '').strip() == 'Print':
        return 'Print'
    link = str(vals.get('Publisher link') or '')
    h = host_of(link)
    if h and _VIDEO_HOST.search(h):
        return 'Video clip'
    if h and _PODCAST_HOST.search(h):
        return 'Podcast episode'
    if h and re.search(r'/(video|videos)/', link) and str(vals.get('Medium') or '').strip() in ('TV', 'Video'):
        return 'Video clip'
    return 'Article'


# ---------- OUTLETREC-v1 (wave 1b outlet design, work/tmp_outlet_design/design.md §2/§4): one record per outlet ----------
# code/outlets.json: {"records": {norm_outlet key: {name, type, house, publisher, city, county, state, country, medium,
# reach [..], reach_conf, lang_reach {Language: [..]}, variant_reach {raw-name base: [..]}, language, jewish, src, ...}}}.
# outlet_record() = the record (with the row's language / raw-name overrides resolved), else the defaulting rules (§2.2).
REACH_LABELS = ('National', 'International', 'Statewide California', 'District & Valley', 'California regional & local',
                'Jewish press', 'Spanish-language', 'Ethnic', 'Trade, advocacy & blogs', 'Out-of-state local')
US_STATES = set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI '
                'SC SD TN TX UT VT VA WA WV WI WY DC PR'.split())
SFV_CITIES = {'encino', 'van nuys', 'sherman oaks', 'woodland hills', 'tarzana', 'reseda', 'canoga park', 'winnetka', 'west hills',
              'calabasas', 'hidden hills', 'lake balboa', 'northridge', 'north hills', 'panorama city', 'chatsworth', 'granada hills',
              'studio city', 'north hollywood', 'san fernando', 'pacoima', 'sylmar', 'sun valley', 'valley village', 'toluca lake',
              'porter ranch', 'mission hills', 'arleta', 'sunland', 'tujunga', 'valley glen', 'agoura hills'}
JEWISH_RX = re.compile(r"jewish|\bjta\b|\bjns\b|^j the|^j\.|hadassah|^forward$|haaretz|jerusalem|israel|hebrew|chabad|tablet|algemeiner|"
                       r"moment magazine|^moment$|kveller|\bcjn\b|ynet|srugim|makor|arutz|7 kanal|lechaim|yeshiva|frumnews|jpac|troib|"
                       r"valley beth shalom|l chaim", re.I)
_STUDENT_RX = re.compile(r'university|college|state hornet|aggie|xpress|orion|collegian|sundial|daily cal|poly post|highlander|'
                         r'daily bruin|daily trojan|spartan|mustang', re.I)
MEDIUM_BY_TYPE = {'wire': 'Wire', 'distributor': 'Wire', 'podcast': 'Podcast', 'magazine': 'Magazine', 'trade': 'Trade press',
                  'blog': 'Newsletter or blog', 'student': 'Student newspaper'}


def _load_outlets():
    try:
        return (json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'outlets.json'), encoding='utf-8')) or {}).get('records') or {}
    except (OSError, ValueError):
        return {}


OUTLETS = _load_outlets()


def country_of(state, rec_country=''):
    s = str(state or '').strip()
    if rec_country:
        return rec_country
    if s.upper() in US_STATES or s.upper() in ('USA', 'US', 'UNITED STATES'):
        return 'US'
    return s   # a country name as given ('' = unknown)


def reach_default(otype, country, state, city, lang, name, key=''):
    """-> (reach "a; b" or '', why). design §2.2: first rule that fires wins; Statewide California is never derived"""
    jewish = bool(JEWISH_RX.search(str(name or ''))) or key in ('forward', 'algemeiner', 'moment', 'moment magazine', 'ynet', 'srugim')
    st = str(state or '').strip().upper()
    if country and country != 'US':
        if jewish:
            return 'Jewish press; International', 'rule: foreign-based Jewish press'
        if otype in ('trade', 'blog'):
            return 'Trade, advocacy & blogs; International', 'rule: foreign-based trade/blog'
        return 'International', 'rule: foreign-based -> International'
    if jewish:
        return 'Jewish press', 'rule: Jewish press (name)'
    if otype in ('network', 'national', 'wire', 'distributor', 'aggregator'):
        geo = 'National'
    elif otype == 'podcast':   # OUTLETQ-v1 (Sammy 2026-10-29): a podcast's Reach follows its station / location
        geo = (('District & Valley' if _outlet_base(city) in SFV_CITIES else 'California regional & local') if st == 'CA' else
               'Out-of-state local' if st in US_STATES else 'Trade, advocacy & blogs')
    elif otype in ('prservice', 'trade', 'blog'):
        geo = 'Trade, advocacy & blogs'
    elif otype == 'institution':
        geo = ('Trade, advocacy & blogs' if not _STUDENT_RX.search(str(name or '')) else
               ('California regional & local' if st == 'CA' else 'Out-of-state local'))
    elif otype == 'nonprofit':
        geo = 'Statewide California' if st == 'CA' else ('National' if country == 'US' else '')
    elif st == 'CA':
        geo = 'District & Valley' if _outlet_base(city) in SFV_CITIES else 'California regional & local'
    elif st in US_STATES:
        geo = 'Out-of-state local'
    else:
        geo = ''
    if not geo:
        return '', 'rule: no basis (country/state unknown)'
    if lang == 'Spanish':
        return f'Spanish-language; {geo}', 'rule: US Spanish-language outlet'
    if lang and lang != 'English':
        return f'Ethnic; {geo}', 'rule: US non-English outlet -> Ethnic'
    return geo, 'rule: type/location'


_CALLS_RX = re.compile(r'\b([KW][A-Z]{2,3})\b')


def podcast_station_reach(outlet):
    """OUTLETQ-v1 (Sammy 2026-10-29): a station's podcast ("Greater LA (KCRW)", "790 KABC", "KQED Political Breakdown") takes
    the station's Reach: an outlet record whose key starts with the call letters (radio first), else outlet_rules station_calls.
    -> (reach, why) or None"""
    for call in _CALLS_RX.findall(str(outlet or '')):
        c = call.lower()
        keys = [k for k in OUTLETS if (k == c or k.startswith(c + ' ')) and OUTLETS[k].get('medium') != 'Podcast']
        keys.sort(key=lambda k: (OUTLETS[k].get('medium') != 'Radio', len(k)))
        if not keys and (OUTLET_RULES.get('station_calls') or {}).get(call) in OUTLETS:
            keys = [OUTLET_RULES['station_calls'][call]]
        for k in keys:
            if OUTLETS[k].get('reach'):
                return '; '.join(OUTLETS[k]['reach']), f'rule: podcast of station {call} ({k})'
    return None


CA_LOCAL_LABELS = ('California regional & local', 'District & Valley')


def reach_guard(reach, rec, state='', city='', language='', name=''):
    """REACHFIX-v1 (Sammy 2026-10-29): a Reach that is a California local label ("California regional & local", "District & Valley")
    on an outlet with no California location (record or row state is not CA) is a copy of a wrong old label. When the type/location
    rule has a default and it disagrees, the rule default wins.  -> (reach, why) ; why '' when nothing changed.  Reach values Sammy
    set (record src mentions Sammy / OUTLETQ) are never touched."""
    tags = {x.strip() for x in str(reach or '').split(';') if x.strip()}
    if not tags & set(CA_LOCAL_LABELS):
        return reach, ''
    src = str(((rec or {}).get('src') or {}).get('reach', '')) + ' ' + str((rec or {}).get('decided_by', ''))
    if re.search(r'Sammy|OUTLETQ', src):
        return reach, ''
    st = str(state or (rec or {}).get('state') or '').strip().upper()
    if st == 'CA':
        return reach, ''
    ctry = country_of(st, (rec or {}).get('country', ''))
    rd, why = reach_default((rec or {}).get('type', ''), ctry, st, city or (rec or {}).get('city', ''), language or (rec or {}).get('language', ''),
                            name or (rec or {}).get('name', ''), (rec or {}).get('key', ''))
    rt = {x.strip() for x in rd.split(';') if x.strip()}
    if rd and rt != tags:
        return rd, f'REACHFIX-v1: {reach} on an outlet with no California location; rule default {rd} ({why})'
    return reach, ''


def outlet_record(outlet, city='', raw=None, language='', medium='', publisher='', state='', url=''):
    """OUTLETREC-v1 -> dict with the outlet's fields for a row: key, known (record exists), name, type, publisher, city, county,
    state, country, medium, language, reach ("a; b"), reach_src, reach_conf. `raw` = the row's raw Outlet name (variant_reach),
    `language` = the row's Language (lang_reach). For an outlet with no record the fields come from the defaulting rules."""
    key = norm_outlet(outlet, city)
    hk = (OUTLET_RULES.get('host_outlets') or {}).get(re.sub(r'^https?://([^/]+).*$', r'\1', str(url or '').lower()))   # REVIEW4-LEFTOVERS: kfiam640.iheart.com -> the KFI record
    if hk in OUTLETS and (key not in OUTLETS or key == 'iheartradio'):
        key = hk
    rec = OUTLETS.get(key)
    if rec:
        reach, src = list(rec.get('reach') or []), (rec.get('src') or {}).get('reach', '')
        vb = _outlet_base(raw if raw is not None else outlet)
        for vk, vr in (rec.get('variant_reach') or {}).items():
            if vb == vk or vb.startswith(vk + ' '):
                reach, src = list(vr), f'variant_reach {vk}'
                break
        else:
            lr = (rec.get('lang_reach') or {}).get(str(language or '').strip())
            if lr:
                reach, src = list(lr), f'lang_reach {language}'
        out = {k: rec.get(k, '') for k in ('name', 'type', 'house', 'publisher', 'city', 'county', 'state', 'country', 'medium', 'language')}
        out.update(key=key, known=True, reach='; '.join(reach), reach_src=src, reach_conf=rec.get('reach_conf', ''),
                   needs_sammy=rec.get('needs_sammy', ''))
        return out
    t, h = '', ''
    if RR is not None and hasattr(RR, 'outlet_type'):
        try:
            t, h, _how = RR.outlet_type(outlet, city, medium, publisher, language)
        except Exception:
            t, h = '', ''
    ctry = country_of(state)
    reach, why = reach_default(t, ctry, state, city, language, outlet, key)
    if t == 'podcast' or str(medium or '').strip() == 'Podcast':
        sr = podcast_station_reach(outlet)
        if sr:
            reach, why = sr
    return {'key': key, 'known': False, 'name': norm_val(outlet), 'type': t, 'house': h, 'publisher': norm_val(publisher),
            'city': norm_val(city), 'county': '', 'state': norm_val(state), 'country': ctry, 'medium': MEDIUM_BY_TYPE.get(t, ''),
            'language': norm_val(language), 'reach': reach, 'reach_src': why, 'reach_conf': 'rule' if reach else 'none', 'needs_sammy': 'new outlet'}


def delete_rows_keep_links(ws, idx, amount=1):
    """openpyxl's delete_rows moves cells up but leaves each moved cell's Hyperlink.ref at its OLD coordinate, and the writer
    writes the ref as stored: every link below a removed row lands one row too high (v22 fix; C dry run found 65 bogus AV
    links). Delete, then re-anchor every remaining hyperlink to its cell."""
    ws.delete_rows(idx, amount)
    # AUDIT F11 (final-int): openpyxl does not shift row_dimensions either: hidden flags / heights / outline levels below the
    # removed rows move up with their rows (the removed rows' own dimensions are dropped)
    dims = ws.row_dimensions
    old = {k: dims[k] for k in list(dims.keys()) if isinstance(k, int)}
    if any(k >= idx for k in old):
        for k in list(old):
            if k >= idx:
                del dims[k]
        for k, d in sorted(old.items()):
            if k < idx or k < idx + amount:
                continue
            d.index = k - amount
            dims[k - amount] = d
    for c in list(ws._cells.values()):
        h = c.hyperlink
        if h is not None and h.ref != c.coordinate:
            h.ref = c.coordinate


def norm_val(v):
    if v is None:
        return ''
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        v = v.strftime('%Y-%m-%d')
    return re.sub(r'\s+', ' ', str(v)).strip()


PRINT_TAB = 'Unlinked print pages'
# NOCOPY-v2 (Sammy 2026-10-28 + coordinator labels): credited originators with no fetchable page are no-copy Original rows
NOCOPY_SERVICES = [(re.compile(r'California Black Media|\bCBM\b'), 'California Black Media', 'No public page (members only)'),
                   (re.compile(r'City News Service|\bCNS\b'), 'City News Service', 'No public page (wire)'),
                   (re.compile(r'Bay City News'), 'Bay City News', 'No public page (wire)')]
NOCOPY_DS = 'Reprint credit (no copy)'
CREDIT_HOWS = ('credit', 'credit line', 'byline', 'dateline', 'reporter', 'wire')


# OWNED-v1 (Sammy 2026-10-28): his own channels are owned media, never coverage (mirrors isOwned() in the tracker JS)
OWNED_HOSTS = re.compile(r'(^|\.)(asmdc\.org|jessegabriel\.com|jessegabriel\.org|electjessegabriel\.com|cajewishcaucus\.org|californiajewishcaucus\.org)$', re.I)
OWNED_CHANNEL = re.compile(r'^\s*(?:(?:Assemblymember|Assembly\s*member|Assemblyman|Asm\.?)\s+)?Jesse\s+Gabriel(?:\s+for\s+Assembly)?\s*$|AsmJesseGabriel|'
                           r'JesseGabriel(?:AD46)?\b|\bAD\s?-?46\b|46th\s+Assembly\s+District|Legislative\s+Jewish\s+Caucus|'
                           r'^\s*(?:California\s+)?Assembly\s+Democrats\s*$|AsmDems', re.I)


def is_owned(row):
    u = norm_val(row.get('Publisher link')); h = host_of(u)
    if h and OWNED_HOSTS.search(h):
        return True
    if re.search(r'(^|\.)(youtube\.com|youtu\.be)$', h or '', re.I):
        if re.search(r'youtube\.com/(?:@|c/|user/)(?:AsmJesseGabriel|JesseGabriel|AsmDems|AssemblyDemocrats)', u, re.I):
            return True
        return any(OWNED_CHANNEL.search(norm_val(row.get(c))) for c in ('Outlet', 'Show', 'Channel', 'Author / byline') if norm_val(row.get(c)))
    return False


def is_station_youtube(obj):
    """YTSTATION-v1: a find the Update button took from a station's own YouTube channel (its `_av` says Details from 'YouTube page', Item type Broadcast segment, a Channel) on a TV / Radio row"""
    av = obj.get('_av')
    return (isinstance(av, dict) and norm_val(av.get('Details from')) == 'YouTube page' and norm_val(av.get('Item type')) == 'Broadcast segment'
            and bool(norm_val(av.get('Channel'))) and norm_val(obj.get('Medium')) in ('TV', 'Radio')
            and bool(re.search(r'(^|\.)(youtube\.com|youtu\.be)$', host_of(norm_val(obj.get('Publisher link'))) or '')))


def print_page_url(url, rules=None):
    """REQ-11 (UPDFIX-v1): the pattern when `url` is an e-paper / flipbook / page-viewer page (clean_rules.json print_page_urls). Such a page is
    print coverage that needs clipping, never a story row: drop_skipped routes it to `print_pages`."""
    u = str(url or '').strip()
    pats = (rules if rules is not None else (CH.load_rules() if CH is not None else {})).get('print_page_urls') or []
    return next((p for p in pats if re.search(p, u)), None)


_NC_HOSTS = None


def _never_coverage_entries():
    """REQ-12 / NOBLOGS-v1: [(host, path prefix or '', why)] from outlet_rules.json never_coverage_hosts and lookup_cache.json never_coverage_hosts"""
    global _NC_HOSTS
    if _NC_HOSTS is None:
        out = []
        for e in OUTLET_RULES.get('never_coverage_hosts') or []:
            h, _, pfx = str(e).lower().partition('/')
            out.append((h, pfx, 'personal blog platform; not press (REQ-12)'))
        try:
            cache = LC.Cache.load() if LC is not None else None
        except Exception:
            cache = None
        for h, e in ((cache.never_coverage_hosts if cache is not None else {}) or {}).items():
            out.append((h.lower(), '', str((e or {}).get('why') or 'never coverage') + ' (NOBLOGS-v1)'))
        _NC_HOSTS = out
    return _NC_HOSTS


def never_coverage_reason(url, outlet=None):
    """The reason when `url` is on a host that is never coverage (platform blogs, YouTube, advocacy blogs), else ''. An outlets.json record that lists
    the exact host in its `hosts` rescues it (a journalist's Substack / Medium)."""
    h = host_of(url)
    path = re.sub(r'^[a-z]+://[^/]+/?', '', str(url or '').strip().lower())
    if outlet:   # NOBLOGS-v1: judged by the row's OUTLET, not the link host: an outlet on record that is not a blog (a station's own video on YouTube, a newspaper's blogspot mirror link) is coverage
        rec = OUTLETS.get(norm_outlet(outlet))
        if isinstance(rec, dict) and str(rec.get('type') or '').lower() not in ('', 'blog'):
            return ''
    for host, pfx, why in _never_coverage_entries():
        if h == host or h.endswith('.' + host):
            if pfx and not path.startswith(pfx):
                continue
            if any(h in [str(x).lower() for x in (rec.get('hosts') or [])] for rec in OUTLETS.values() if isinstance(rec, dict)):
                return ''
            return why
    return ''


def nocopy_service(name):
    """(canonical service, Link status) for a credited service that publishes no public page, else None"""
    for rx, canon, ls in NOCOPY_SERVICES:
        if rx.search(str(name or '')):
            return canon, ls
    return None   # PRINTTAB-v1: NewsBank print-page pointers moved off Coverage (IDs and links stay reserved)


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
        # AUDIT F12 (final-int): the last row holding a value, not ws.max_row (a cleared, still-styled cell below the data would
        # otherwise put new rows after a gap of blank rows and copy the blanks into the Originals tab)
        lr = self.ws.max_row
        while lr > 1 and all(blank(c.value) for c in self.ws[lr]):
            lr -= 1
        self.last_row = lr
        self.read_print_tab()
        self.read_removed_tab()

    def read_removed_tab(self):
        """AUDIT F1/F2: rows on the "Removed" tab keep their numbers (Article ID / Print Article ID / Story ID are never reused:
        db docs keyed by Story ID would otherwise attach to the new story) and their links (a removed story found again by the
        Update button is dropped, not re-added)."""
        self.removed_links = {}   # normalized link -> Article ID on the Removed tab
        if 'Removed' not in self.wb.sheetnames:
            return
        rw = self.wb['Removed']
        rh = {c.value: i + 1 for i, c in enumerate(rw[1]) if c.value}
        g = lambda r, c: rw.cell(r, rh[c]).value if c in rh else None
        for r in range(2, rw.max_row + 1):
            aid = str(g(r, 'Article ID') or '').strip()
            m = re.match(r'^ws-(\d+)$', aid)
            if m:
                self.max_ws = max(self.max_ws, int(m.group(1)))
            for c in ('Article ID', 'Print Article ID'):
                v = str(g(r, c) or '').strip()
                if NEW_AID.match(v):
                    self.max_num = max(self.max_num, int(v))
            sid = str(g(r, 'Story ID') or '').strip()
            m = re.match(r'^jg-(\d+)$', sid)
            if m:
                self.max_jg = max(self.max_jg, int(m.group(1)))
            m = re.match(r'^s(\d{5})$', sid)
            if m:
                self.max_s = max(self.max_s, int(m.group(1)))
            if aid:
                for k in identity_links(lambda c, r=r: norm_val(g(r, c))):
                    self.removed_links.setdefault(k, aid)

    def read_print_tab(self):
        """PRINTTAB-v1: the "Unlinked print pages" tab's Article IDs / Print Article IDs / links are read like Coverage's, so no
        number on it is reused (max_num, max_ws, old_ids) and a find with one of its links is never re-added (links). Its rows
        are not Coverage rows: rows / story_rows / codes stay Coverage-only."""
        self.print_aids = set()
        self.print_rows = []      # PAYWALL-v1: (Article ID, Outlet, Outlet city, Date) of the print pointers, for the counterpart note
        if PRINT_TAB not in self.wb.sheetnames:
            return
        pw = self.wb[PRINT_TAB]
        ph = {c.value: i + 1 for i, c in enumerate(pw[1]) if c.value}
        g = lambda r, c: pw.cell(r, ph[c]).value if c in ph else None
        for r in range(2, pw.max_row + 1):
            aid = str(g(r, 'Article ID') or '').strip()
            if aid:
                self.print_aids.add(aid)
                self.print_rows.append((aid, str(g(r, 'Outlet') or ''), str(g(r, 'Outlet city') or ''), g(r, 'Date')))
            m = re.match(r'^ws-(\d+)$', aid)
            if m:
                self.max_ws = max(self.max_ws, int(m.group(1)))
            for c, oc in (('Article ID', 'Old Article ID'), ('Print Article ID', 'Old Print Article ID')):
                v = str(g(r, c) or '').strip()
                if NEW_AID.match(v):
                    self.max_num = max(self.max_num, int(v))
                    o = str(g(r, oc) or '').strip()
                    if o:
                        self.old_ids.setdefault(o, v)
            if aid:
                for k in identity_links(lambda c, r=r: norm_val(g(r, c))):
                    self.links.setdefault(k, aid)

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
                    'date_fixes': [], 'date_review': [], 'print_pages': [], 'backfill_finds': []}   # F7-v1; REQ-11 / REQ-13
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
        # REPRINT-v2: Original swaps made by the originals order v2, outlets the type table does not know, no-copy originators
        self.res.update({'origin_swaps': [], 'outlet_untyped': [], 'origin_nocopy': [], 'origin_wanted': []})   # + CHAINORIG-v1
        self.res.update({'outlet_new': []})   # OUTLETREC-v1: outlets with no code/outlets.json record (one queue item each)
        self.res.update({'reach_review': []})   # REACHFIX-v1: a California-local label on an outlet with no California location (rule default wins; one queue item each)
        self._reachflag = set()
        # QUEUEAPPLY-v1 (final-int 2026-10-29): decided review-queue items this task made (outlet / merge / billtags / nearcopy)
        self.res.update({'queue_applied': [], 'queue_conflicts': [], 'outlets_changed': False, 'nocopy_filled': []})
        self.queue = None         # (items, decisions, applied ids) from --queue DIR
        self._queue_counts = set()
        self._emp = self._avitems = None
        self._untyped = set()
        self._newout = set()
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
        gone = next((self.s.removed_links[k] for k in link_keys if k and k in getattr(self.s, 'removed_links', {})), None)
        if gone and not dup:   # AUDIT F2: a story Sammy removed is never re-added by a later Update
            self.unswap_original(obj)
            self.res['skipped'].append({'run': run_id, 'placeholder': ph_aid, 'story': ph_sid, 'code': str(obj.get('Tracker story code') or ''),
                                        'outlet': obj.get('Outlet', ''), 'link': obj.get('Publisher link', ''),
                                        'why': f'its link is on the Removed tab (row {gone}): removed story, not re-added'})
            return None
        if dup:
            self.unswap_original(obj)   # AUDIT F4: a swap made for a find that is not written is undone
            self.res['duplicates'].append({'run': run_id, 'placeholder': ph_aid, 'existing': dup,
                                           'link': obj.get('Publisher link', '')})
            if ph_aid:
                self.ids[ph_aid] = dup
            if PLACEHOLDER_SID.match(ph_sid) and ph_sid not in self.ids and dup in self.s.rows:   # PAYWALL-v1: a print-tab pointer has no Coverage row (was a KeyError)
                self.ids[ph_sid] = self.s.get(self.s.rows[dup], 'Story ID') or ''
            return None
        if kind == 'Original':
            # a new original always gets a fresh jg-NNNNN unless its placeholder was already resolved;
            # a temporary jg- + 6 hex code is never written as a Story ID
            sid = self.ids.get(ph_sid)
            if sid and self.s.original_row(sid) is not None:   # AUDIT F3: a placeholder reused in the same run (two Originals, one story)
                self.res.setdefault('placeholder_reused', []).append({'run': run_id, 'placeholder': ph_sid, 'story': sid, 'aid_placeholder': ph_aid,
                                                                      'why': 'its story already has an Original: this find gets a story of its own'})
                sid = None
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
            self.unswap_original(obj)   # AUDIT F4
            return None
        self.note_untyped(vals, run_id, ph_aid)   # REPRINT-v2
        aid = self.next_aid()
        if ph_aid:
            self.ids[ph_aid] = aid
        sh = getattr(self, '_show_hint', {})
        if sh.get('pending') is not None:   # SHOWNET-v1: the show split off the Outlet reaches the A/V tab row of this Article ID
            sh[aid] = sh.pop('pending')
            if SN is not None and norm_val(vals.get('Format')) in ('Broadcast segment', 'Audio segment') and SN.is_rundown(vals.get('Headline')):
                self.res.setdefault('rundown_headline', []).append({'run': run_id, 'aid': aid, 'headline': norm_val(vals.get('Headline'))[:120],
                                                                    'why': 'the Headline is the whole episode rundown: replace it with the segment he appears in ("<Show>: <topic>")'})
        r = self.s.append_row()
        vals.update({'Article ID': aid, 'Story ID': sid, 'Original or reprint': kind,
                     'Data Source': obj.get('Data Source') or 'Web search (TinyFish)'})
        self.date_check(vals, obj, run_id, ph_aid, aid)   # F7-v1
        if 'outlet backfill' in norm_val(vals.get('Data Source')).lower():   # REQ-13 (UPDFIX-v1): an old story the outlet sweep re-found; listed so weekly runs stay legible
            self.res['backfill_finds'].append({'run': run_id, 'placeholder': ph_aid, 'aid': aid, 'outlet': vals.get('Outlet', ''), 'date': norm_val(vals.get('Date'))[:10],
                                               'headline': norm_val(vals.get('Headline'))[:140], 'link': vals.get('Publisher link', '')})
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
        if 'Format' in self.s.col and blank(vals.get('Format')):   # FORMAT-v1
            vals['Format'] = format_of(vals, (obj.get('_av') or {}).get('Item type', '') if isinstance(obj.get('_av'), dict) else '')   # YTSTATION-v1: a station's YouTube find says Broadcast segment
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
        if d and re.match(r'^\d{4}-\d{2}-\d{2}$', d) and d > str(self.today)[:10]:   # REQ-10 (UPDFIX-v1): no story is dated after today; a deadline in the text was misread as a byline
            vals['Date'], vals['Year'] = '', ''
            self.res['date_review'].append(dict(e, date='', was=d, why='future date; page text misread (blanked)'))
            return
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
        if DR is not None:   # DATES-v1: the eight sanity checks (design 3.5) + "Date source"
            if self.dates_v1(vals, obj, run_id, e):
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

    def date_ctx(self, vals, obj, run_id):
        """DATES-v1: what date_rules.check_row needs to know about a new row: the story's Original and reprint dates,
        the release date of a release copy, the page text (for the Updated stamp), how the date was found."""
        sid = norm_val(vals.get('Story ID'))
        rows = self.story_rows_dicts(sid) if sid and hasattr(self, 'story_rows_dicts') else []
        orig = [r for r in rows if r.get('Original or reprint') == 'Original']
        ctx = {'run_day': getattr(self, '_run_day', '') or self.today, 'today': self.today, 'date_src': str(obj.get('_date_src') or ''),
               'has_page_date': str(obj.get('_date_src') or '') in ('page', 'claude'),
               'original_date': orig[0].get('Date', '') if orig else '', 'original_edition': orig[0].get('Edition', '') if orig else '',
               'reprint_dates': [r.get('Date', '') for r in rows if str(r.get('Original or reprint', '')).startswith('Reprint')],
               'release_date': str((obj.get('_release') or {}).get('date') or '') if isinstance(obj.get('_release'), dict) else '',
               'signed': getattr(self, '_signed_dates', None) or {}, 'page_text': ''}
        try:
            pid = self.page_doc_id(obj)
            p = ((self.db.get('pages') or {}).get(pid) or {}) if pid else {}
            ctx['page_text'] = re.sub(r'<[^>]+>', ' ', str(p.get('clean') or p.get('html') or ''))[:4000]
        except Exception:
            pass
        return ctx

    def dates_v1(self, vals, obj, run_id, e):
        """DATES-v1: run the eight checks on a new row; write Year / Date fixes and "Date source"; True when the row's date
        was blanked (check 8) so date_check stops there."""
        ctx = self.date_ctx(vals, obj, run_id)
        src = DR.source_from_update(ctx['date_src'], norm_val(vals.get('Edition')))
        blanked = False
        for f in DR.check_row(vals, ctx):
            why = f"check {f['check']}: {f['why']}"
            if f['action'] == 'blank':
                vals['Date'], vals['Year'] = '', ''
                tn = norm_val(vals.get('Team note'))
                vals['Team note'] = (tn + '; ' if tn else '') + f.get('note', DR.UNDATED_NOTE)
                src, blanked = 'undated', True
                self.res['date_fixes'].append(dict(e, new='', why=why))
            elif f['action'] == 'fix' and f['column'] == 'Date':
                vals['Date'], vals['Year'] = f['new'], int(f['new'][:4])
                src = 'page byline'
                self.res['date_fixes'].append(dict(e, new=f['new'], why=why))
            elif f['action'] == 'fix' and f['column'] == 'Year':
                vals['Year'] = int(f['new'])
            elif f['action'] == 'fix' and f['column'] == 'Date source':
                src = f['new']
            else:
                self.res['date_review'].append(dict(e, why=why, target=f.get('target', '')))
        if 'Date source' in self.s.col:
            vals['Date source'] = DR.with_precision(src, norm_val(vals.get('Date')))
        obj['_date_source'] = DR.with_precision(src, norm_val(vals.get('Date')))
        return blanked

    # ---------- PAYWALL-v1: a page found directly by the Update button that names Gabriel but cannot be saved ----------
    def nocopy_finds(self, rows, run_id):
        """PAYWALL-v1 (Sammy 2026-10-29): an Original find whose page was paywalled / blocked (the tracker sets `_nocopy_find`; File name
        BLOCKED and no pages doc also counts) is added right away as a no-copy row with the NOCOPY-v2 labels: Saved Copy? No, Link status
        "Publisher URL (blocked site, no copy)", File name BLOCKED, the link kept, a Team note; Date + Date source come from the search
        result (DATES-v1 runs in add_row). Dedupe before the row is built: same outlet + near-identical headline within 2 days of an
        existing Coverage row -> dropped (duplicates); an existing row of ANOTHER outlet with the same headline within 3 days -> kept,
        with a merge proposal (origin_merge, never a silent second story); same outlet within 2 days of an "Unlinked print pages"
        pointer -> kept, note "possible web version of Unlinked print page <id>" (res['print_counterpart']). A link already on Coverage
        or on the print tab is dropped by add_row as before."""
        out = []
        for o in rows:
            if (o.get('Original or reprint') or 'Original') != 'Original' or o.get('_og_of') or o.get('_release'):
                out.append(o)
                continue
            if not (o.get('_nocopy_find') or (norm_val(o.get('File name')) == BLOCKED and not self.page_doc_id(o))):
                out.append(o)
                continue
            o = dict(o)
            o['_nocopy_find'] = True
            ph = str(o.get('Article ID') or '')
            name = norm_outlet(o.get('Outlet'), o.get('Outlet city') or '')
            d0 = RR.todate(o.get('Date')) if RR is not None else None
            hl = str(o.get('Headline') or '')
            sim = RR.headline_sim if RR is not None and hasattr(RR, 'headline_sim') else (lambda a, b: 1.0 if norm_val(a).lower() == norm_val(b).lower() else 0.0)
            same = other = None
            for aid, r in self.s.rows.items():
                d1 = RR.todate(self.s.get(r, 'Date')) if RR is not None else None
                h2 = str(self.s.get(r, 'Headline') or '')
                if not (d0 and d1 and hl and h2) or abs((d0 - d1).days) > 3:
                    continue
                sm = sim(hl, h2)
                if norm_outlet(self.s.get(r, 'Outlet'), self.s.get(r, 'Outlet city')) == name:
                    if sm >= 0.8 and abs((d0 - d1).days) <= 2:
                        same = aid
                        break
                elif sm >= 0.9 and other is None:
                    other = aid
            if same:
                self.res['duplicates'].append({'run': run_id, 'placeholder': ph, 'existing': same, 'link': o.get('Publisher link', ''),
                                               'why': 'PAYWALL-v1: same outlet, same headline within 2 days'})
                self.ids[ph] = same
                continue
            note = []
            if other:
                self.res.setdefault('origin_merge', []).append({'run': run_id, 'placeholder': ph, 'outlet': o.get('Outlet', ''),
                    'origin': o.get('Publisher link', ''), 'existing': other, 'story': self.s.get(self.s.rows[other], 'Story ID')})
                note.append(f'same headline as {other} ({self.s.get(self.s.rows[other], "Outlet")}): merge proposed')
            for paid, pout, pcity, pdate in getattr(self.s, 'print_rows', []):
                d1 = RR.todate(pdate) if RR is not None else None
                if d0 and d1 and abs((d0 - d1).days) <= 2 and norm_outlet(pout, pcity) == name:
                    self.res.setdefault('print_counterpart', []).append({'run': run_id, 'placeholder': ph, 'print': paid, 'outlet': o.get('Outlet', '')})
                    note.append(f'possible web version of Unlinked print page {paid}')
                    break
            o['Saved Copy?'] = 'No'
            o['File name'] = BLOCKED
            if norm_val(o.get('Link status')) in ('', 'Publisher URL'):
                o['Link status'] = 'Publisher URL (blocked site, no copy)'
            tn = norm_val(o.get('Team note'))
            base = '' if 'paywalled' in tn.lower() else f'Paywalled / blocked page, added from the search result {self.today}'
            o['Team note'] = '; '.join(x for x in [tn, base] + note if x)
            self.res.setdefault('nocopy_finds', []).append({'run': run_id, 'placeholder': ph, 'outlet': o.get('Outlet', ''), 'link': o.get('Publisher link', '')})
            out.append(o)
        return out

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
            rows = self.nocopy_finds(rows, run_id)   # PAYWALL-v1: paywalled / blocked finds -> no-copy rows
            rows = self.check_reprint_rows(rows, run_id)   # BUTTONOPT-v1 (A-B1): the page's reprints, by the text rule
            rows = self.agg_origin_step(rows, run_id)   # AGGORIGIN-v1: an aggregator find's credited originator / byline employer
            rows = self.origin_rows(rows, run_id)   # BUTTONOPT-v1 (ORIGINCREDIT): originators' copies as candidate Originals
            rows = self.reprint_check(rows, run_id)   # AUTO-v1: new finds that are reprints of a story by text
            rows = self.origin_settle(rows, run_id)   # BUTTONOPT-v1: originators no find attached to are not added
            rows = self.agg_origin_notes(rows, run_id)   # AGGORIGIN-v1: Team notes on aggregator finds that stay Original
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
        if best and best['verdict'] == 'ok' and RR is not None and hasattr(RR, 'copy_mismatch'):   # REPRINT-v2 wrong-copy guard (fetch side)
            try:
                tx = RR.html_text(best['html'])[0]
                mt = re.search(r'<title>(.*?)</title>', best['html'], re.S | re.I)
                why = RR.copy_mismatch(row, mt.group(1).strip() if mt else '', 'html', tx)
            except Exception:
                why = ''
            if why:
                best = dict(best, verdict='error', reason='wrong copy: ' + why)
        if best and best['verdict'] == 'ok' and RR is not None and getattr(RR, 'copy_check', None):   # COPYCHECK-v1 (R1-R7)
            try:
                import html as _hh
                tx = RR.html_text(best['html'])[0]
                mt = re.search(r'<title>(.*?)</title>', best['html'], re.S | re.I)
                mh = re.search(r'<h1[^>]*>(.*?)</h1>', best['html'], re.S | re.I)
                cv, creasons, cextra = RR.copy_check(row, {
                    'url': p.get('url', '') or row.get('Publisher link', ''), 'canonical': p.get('canonical', ''),
                    'title': _hh.unescape(mt.group(1).strip()) if mt else '', 'h1': _hh.unescape(re.sub('<[^>]+>', '', mh.group(1))).strip() if mh else '',
                    'text': tx, 'published': p.get('published', '') or p.get('date', ''), 'kind': 'html'})
            except Exception as _e:
                cv, creasons, cextra = 'ok', ['copy_check error: %r' % (_e,)], {}
            if cv == 'reject':
                best = dict(best, verdict='error', reason='copy check: ' + '; '.join(creasons))
            else:
                best = dict(best, copy_check=cv, copy_reasons=creasons, copy_tags=cextra.get('tags', []), file_to=cextra.get('file_to', ''))
        self.page_checks[pid] = best
        return best

    def page_html(self, p, body, row):
        """the page as the library keeps it: title, a metadata header (Outlet · Date, URL, Saved date) and the body.
        The cleaner removes the header lines that match the sheet and keeps (and reports) the ones that don't."""
        import html as _h
        url = p.get('url', '') or row.get('Publisher link', '')
        # DATES-v1: the header carries the page's own date (byline / metadata / print edition) or "undated"; never a
        # scrape, save or last-modified day (copies audit finding 5)
        hd = DR.header_date(row, row.get('_date_source') or row.get('_date_src')) if DR is not None else (norm_val(row.get('Date', ''))[:10] or 'undated')
        hdr = [x for x in (f"{row.get('Outlet', '')} · {hd}" if row.get('Outlet') else '',
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
            if print_page_url(obj.get('Publisher link'), self.rules()) and (obj.get('Original or reprint') or 'Original') == 'Original':   # REQ-11
                self.res['print_pages'].append({'run': run_id, 'placeholder': obj.get('Article ID', ''), 'outlet': obj.get('Outlet', ''), 'link': obj.get('Publisher link', ''),
                                                'date': str(obj.get('Date') or '')[:10], 'headline': obj.get('Headline', ''), 'why': 'e-paper / flipbook page: print coverage, needs clipping (Unlinked print pages), not a story row'})
                if obj.get('Story ID'):
                    gone.add(obj['Story ID'])
                continue
            if SKIP_HOSTS.search(host_of(obj.get('Publisher link'))) or norm_val(obj.get('Outlet')).lower() == 'california files':
                why = 'californiafiles.org: never added (DECISIONS 2026-10-27)'
            elif is_owned(obj):
                why = 'his own channel (office / caucus site, his YouTube channel): owned media, never coverage (OWNED-v1)'
            elif not is_station_youtube(obj) and (nc_why := never_coverage_reason(obj.get('Publisher link'), obj.get('Outlet'))):   # YTSTATION-v1: a station's own YouTube clip is broadcast coverage (the channel was judged by the Update button)
                  # REQ-12 / NOBLOGS-v1 (after the owned-channel reason, which is more specific)
                why = nc_why
            elif CH is not None and hasattr(CH, 'skip_url') and CH.skip_url(obj.get('Publisher link'), self.rules()):   # AUTO-v1
                why = 'database, results or listing page: never added (DECISIONS 2026-10-27)'
            elif AO is not None and not obj.get('_release') and (obj.get('Original or reprint') or 'Original') == 'Original' \
                    and AO.release_repost_reason(obj, self.find_text(obj)):   # AGGORIGIN-v1 (4): a repost of an organization's / official's own release
                why = 'held from coverage: ' + AO.release_repost_reason(obj, self.find_text(obj))
                self.res.setdefault('release_held', []).append({'run': run_id, 'placeholder': obj.get('Article ID', ''), 'outlet': obj.get('Outlet', ''),
                                                                'link': obj.get('Publisher link', ''), 'byline': obj.get('Author / byline', ''), 'reason': AO.REASON_RELEASE})
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
            if chk.get('copy_check') == 'flag':   # COPYCHECK-v1: saved, reported for the review queue ("copy check")
                info['copy_check'] = chk.get('copy_reasons', [])
            if chk.get('copy_tags'):
                info['tags'] = chk['copy_tags']
            if 'big_removal' in chk['flags'] or 'long_block' in chk['flags'] or chk.get('copy_check') == 'flag':
                self.res['pages_flagged'].append(info)
            # AUDIT F5: a row left at RETRY / BLOCKED (Saved Copy? No) by an earlier run takes the copy now; verify allows these cells
            if norm_val(self.s.get(r, 'File name')) in (RETRY, BLOCKED) and norm_val(self.s.get(r, 'Saved Copy?')).lower() in ('', 'no'):
                self.res.setdefault('retry_cleared', []).append({'aid': aid, 'was': norm_val(self.s.get(r, 'File name')), 'file': f'{year}/{fname}'})
                for col in ('File name', 'Saved Copy?'):
                    self.s.ws.cell(r, self.s.col[col]).value = None
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
            cols = ('Article ID', 'Story ID', 'Date', 'Headline', 'Outlet', 'Outlet city', 'Medium', 'Publisher', 'Language', 'Author / byline',
                    'Author title', 'Press release', 'Data Source', 'Edition', 'Original or reprint', 'Translated Headline')
            av = self.av_items()
            self._origs = [dict({c: norm_val(self.s.get(r, c)) for c in cols if c in self.s.col}, _row=r,
                                _av_item=av.get(norm_val(self.s.get(r, 'Article ID')), ''))
                           for r in range(2, self.s.last_row + 1)
                           if self.s.get(r, 'Original or reprint') == 'Original' and not blank(self.s.get(r, 'Story ID'))]
        return self._origs

    def av_items(self):
        """REPRINT-v2: Article ID -> AV tab Item type (Broadcast segment / Episode / Video clip / Web story)"""
        if self._avitems is None:
            self._avitems = {}
            if 'Audio & video details' in self.s.wb.sheetnames:
                ws = self.s.wb['Audio & video details']
                hdr = [c.value for c in ws[1]]
                if 'Article ID' in hdr and 'Item type' in hdr:
                    ia, it = hdr.index('Article ID'), hdr.index('Item type')
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        if row and row[ia]:
                            self._avitems[norm_val(row[ia])] = norm_val(row[it]) if it < len(row) else ''
        return self._avitems

    def employment(self):
        """REPRINT-v2: reporters.Employment over the sheet (the reporter's employer on the story date), None when reporters.py is missing"""
        if self._emp is None and REP is not None:
            try:
                self._emp = REP.from_sheet(self.s)
            except Exception as _e:
                self.res['reprint_check'].append({'note': 'reporters.py failed: ' + repr(_e)[:200] + '; originals order runs without the reporter tier'})
                self._emp = False
        return self._emp or None

    def home_of(self, row):
        E = self.employment()
        return E.home_of(row) if E else (None, '')

    def story_rows_dicts(self, sid):
        """the sheet rows of a story as dicts (for origin_credits / choose_original)"""
        cols = ('Article ID', 'Story ID', 'Date', 'Headline', 'Outlet', 'Outlet city', 'Medium', 'Publisher', 'Language', 'Author / byline', 'Author title',
                'Press release', 'Data Source', 'Edition', 'Original or reprint', 'Section', 'Newsbank APA citation (article)')
        av = self.av_items()
        return [dict({c: norm_val(self.s.get(r, c)) for c in cols if c in self.s.col}, _row=r, _av_item=av.get(norm_val(self.s.get(r, 'Article ID')), ''))
                for r in self.s.story_rows.get(sid, [])]

    def note_new_outlet(self, vals, rec, run_id, ph_aid):
        """OUTLETREC-v1: an outlet with no code/outlets.json record -> listed once (queue_after makes one `outlet` item per key);
        the row is still written with the rule-proposed fields"""
        k = rec.get('key')
        if not k or k in self._newout:
            return
        self._newout.add(k)
        self.res['outlet_new'].append({'run': run_id, 'placeholder': ph_aid, 'key': k, 'outlet': norm_val(vals.get('Outlet')),
                                       'host': host_of(vals.get('Publisher link')), 'link': norm_val(vals.get('Publisher link')),
                                       'proposed': {f: rec.get(f, '') for f in ('name', 'type', 'publisher', 'city', 'county', 'state',
                                                                                'country', 'medium', 'language', 'reach')},
                                       'why': rec.get('reach_src', '')})

    def note_untyped(self, vals, run_id, ph_aid):
        """REPRINT-v2: an outlet the type table (outlet_rules.json "types") does not know is classified by rule and listed once"""
        if RR is None or not hasattr(RR, 'outlet_type'):
            return
        o = norm_val(vals.get('Outlet'))
        t, h, how = RR.outlet_type(o, vals.get('Outlet city'), vals.get('Medium'), vals.get('Publisher'), vals.get('Language'))
        if how != 'table' and o and o not in self._untyped:
            self._untyped.add(o)
            self.res['outlet_untyped'].append({'run': run_id, 'placeholder': ph_aid, 'outlet': o, 'type': t, 'how': how,
                                               'why': 'outlet not in outlet_rules.json types: classified by rule, add it to the table'})

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
        sheet (or an earlier-ranked new find of this run) dated within +-90 days becomes a Reprint of that story; its own reprint
        rows follow it. REPRINT-v2: candidates come from the type-pair prefilter (reprint_rule.candidates), the cell is decided by
        reprint_rule.pair_class (AV <-> text never, same outlet = edition, wire <-> wire never, containment of a credited trim and a
        credited translation = Reprint), and a find that outranks the existing Original by CLASS in the originals order v2
        (credited service, the reporter's employer, originator type over an aggregator / sibling / credited-away row) becomes the
        Original: the old Original turns into a Reprint (`origin_swaps`). A date-only difference between two newsrooms is only
        reported (`order`)."""
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
        tx = lambda o: (texts.get(id(o)) or ('',))[0] if texts.get(id(o)) else ''
        # ORIGINCREDIT: a service credited by any find of this run ranks first (tier 0); REPRINT-v2: + the reporter's employer
        cred = RR.origin_credits(finds, {id(o): tx(o) for o in finds})[0] if hasattr(RR, 'origin_credits') else frozenset()
        v2 = hasattr(RR, 'pair_class')
        home_cache = {}

        def home_for(o):
            k = id(o)
            if k not in home_cache:
                hk, hev = self.home_of(o)
                home_cache[k] = {'key': hk, 'why': hev, 'house': (RR.TYPE_TABLE.get(hk) or ['', ''])[1] if hk else ''} if hk else None
            return home_cache[k]
        rk = (lambda x: RR.rank(x, credited=cred, home=home_for(x))) if v2 else ((lambda x: RR.rank(x, credited=cred)) if cred else RR.rank)
        kept = []
        for o in sorted(finds, key=rk):
            ft = texts[id(o)]
            best = None
            blend = None   # WIREBLEND-v1: the best 'blend' cell against a wire Original
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
                if v2:
                    pc = RR.pair_class(c, o, v, cred, self.home_of, {id(o): tx(o)})
                    if c.get('_nocopy') and c.get('_og_of') == (o.get('Article ID') or '') and pc['kind'] != 'never':
                        # a blocked-site originator this find credits (origin_rows): no text to test; the credit is the evidence
                        pc = {'kind': 'reprint', 'note': 'credited originator on a blocked site (no copy): grouped on the credit', 'conf': 'low'}
                        v = {'ok': True, 'conf': 'low', 'mode': 'credit', 'm': None}
                    if pc['kind'] == 'edition' and not (v and v.get('ok')):
                        continue   # same outlet but not the same text: another article of that outlet
                    if pc['kind'] == 'blend':   # WIREBLEND-v1: its own story that uses wire copy; never a Reprint
                        if blend is None or pc['wire_cov'] > blend[1]['wire_cov']:
                            blend = (c, pc)
                        continue
                    if pc['kind'] not in ('reprint', 'translation', 'edition'):
                        continue
                    v = v or {'ok': True, 'conf': pc['conf'], 'mode': 'credit', 'm': None}
                    key = (pc['kind'] == 'reprint' and v.get('ok', False) and v['conf'] == 'high', (v.get('mode') or '') != 'headline+author',
                           min(v['m']['raw']) if v.get('m') else 0)
                    if best is None or key > best[0]:
                        best = (key, c, dict(v, ok=True, cell=pc), ot is not None)
                elif v and v['ok']:
                    key = (v['conf'] == 'high', v['mode'] != 'headline+author', min(v['m']['raw']) if v.get('m') else 0)
                    if best is None or key > best[0]:
                        best = (key, c, v, ot is not None)
            if best is None and ft is None:   # REQ-14 (4): a find with no text (blocked page) is matched by headline against the existing stories before it may become a new Original
                hm = self.headline_story(o)
                if hm is not None:
                    best = ((False, False, 0), hm[0], {'ok': True, 'conf': 'headline', 'mode': 'headline', 'm': None,
                                                       'cell': {'kind': 'reprint', 'note': f"no text (blocked page): headline matches {hm[0].get('Article ID', '')} ({hm[1]:.2f} on content words, {hm[2]} days apart)", 'conf': 'headline'}}, False)
            if best is None:
                if blend:   # WIREBLEND-v1: note + link to the wire story; the build counts it toward the wire story's pickups
                    c, pc = blend
                    wl = c.get('Publisher link') or c.get('NewsBank article link') or ''
                    tn = norm_val(o.get('Team note'))
                    o['Team note'] = (tn + '; ' if tn else '') + (f"Uses wire copy of {c.get('Story ID')} ({c.get('Outlet', '')}, {str(c.get('Date'))[:10]}, "
                                                                  f"{round(pc['wire_cov'] * 100)}% of the wire text){' ' + wl if wl else ''}")
                    self.res.setdefault('wire_blend', []).append({'run': run_id, 'placeholder': o.get('Article ID', ''), 'outlet': o.get('Outlet', ''),
                                                                  'wire_story': c.get('Story ID'), 'wire_aid': c.get('Article ID', ''), 'conf': pc['conf'], 'note': pc['note']})
                if v2:
                    self.central_wanted(home_for(o), o.get('Story ID') or '', [o], run_id, o)   # CHAINORIG-v1: a lone chain find whose reporter's desk has no row
                kept.append(dict(o, _text=ft))
                continue
            _, c, v, had = best
            ph, target = o.get('Story ID') or '', c['Story ID']
            for r2 in rows:
                if r2 is not o and ph and r2.get('Story ID') == ph:
                    r2['Story ID'] = target
            # the same story from an outlet the story already has (another link to the same article): not added (edition)
            same = ({norm_outlet(self.s.get(x, 'Outlet'), self.s.get(x, 'Outlet city')) for x in self.s.story_rows.get(target, [])}
                    | {norm_outlet(c.get('Outlet'), c.get('Outlet city'))})   # OUTLETRULES-v1: city for generic names
            if norm_outlet(o.get('Outlet'), o.get('Outlet city')) in same - {''}:
                o['_dup'] = True
                if ph and not self.real_sid(ph):
                    self.ids[ph] = target
                # HIDEUNVERIFIED-v1 (final-codedesign 2026-10-29): when the outlet's only row in the story is "Reprint (unverified)" (hidden,
                # no text), this find is the verification that row was waiting for: still no second row, but listed (unverified_hits)
                # instead of being written off as an edition
                uv = [x for x in self.s.story_rows.get(target, []) if RR.is_unverified(self.s.get(x, 'Original or reprint'))
                      and norm_outlet(self.s.get(x, 'Outlet'), self.s.get(x, 'Outlet city')) == norm_outlet(o.get('Outlet'), o.get('Outlet city'))]
                why = (f"same story and outlet as {c.get('Article ID', '')} ({v['mode']}): another link to an article already in the sheet (an edition, Web + Print)" if not uv else
                       f"its text passes against {c.get('Article ID', '')} ({v['mode']}) and the outlet's row {self.s.get(uv[0], 'Article ID')} in this story is Reprint (unverified): "
                       f"verify that row by hand with this link (not added as a second row)")
                self.res['skipped'].append({'run': run_id, 'placeholder': o.get('Article ID', ''), 'story': ph, 'code': str(o.get('Tracker story code') or ''),
                                            'outlet': o.get('Outlet', ''), 'link': o.get('Publisher link', ''), 'why': why})
                if uv:
                    self.res.setdefault('unverified_hits', []).append({'run': run_id, 'placeholder': o.get('Article ID', ''), 'aid': self.s.get(uv[0], 'Article ID'),
                                                                       'story': target, 'outlet': o.get('Outlet', ''), 'link': o.get('Publisher link', ''),
                                                                       'page': self.page_doc_id(o) or '', 'mode': v['mode'], 'conf': v['conf']})
                continue
            cell = v.get('cell') or {}
            e = {'run': run_id, 'placeholder': o.get('Article ID', ''), 'code': str(o.get('Tracker story code') or ''),
                 'outlet': o.get('Outlet', ''), 'link': o.get('Publisher link', ''), 'headline': o.get('Headline', ''),
                 'story': target, 'original': c.get('Article ID', ''), 'original_outlet': c.get('Outlet', ''),
                 'mode': v['mode'], 'conf': v['conf'],
                 'coverage': round(min(v['m'][{'text': 'raw', 'text-clutter': 'clut', 'text-edge': 'edge'}.get(v['mode'], 'raw')]), 3) if v.get('m') else None}
            if cell:
                e['cell'] = cell['kind'] + ': ' + cell['note']
            if v['conf'] == 'low':
                e['note'] = 'low confidence: ' + (cell.get('note') or 'passes only with clutter or edge lines set aside') + '; check it'
            # REPRINT-v2 originals order: swap by class, report date ties (a find of this run ranked later is never first)
            swapped = False
            if '_text' not in c and v2 and v.get('conf') != 'headline':   # REQ-14: a headline match never swaps the Original
                hm = home_for(o) or home_for(c)
                cm = self.central_wanted(hm, target, [o], run_id, o, e)   # CHAINORIG-v1
                if cm and isinstance(hm, dict):
                    hm = dict(hm, house='')   # the desk has no row: no "employer's house" tier for a local sibling
                ch = RR.choose_original([c, o], {id(o): tx(o)}, hm, current=c)
                if ch['swap'] and ch.get('class_swap'):
                    swapped = self.swap_original(c, o, target, ch['why'], run_id)
                    e['swap'] = ch['why']
                elif ch['swap']:
                    e['order'] = (f"under the originals order this find ({RR.tier(o, credited=cred, home=home_for(o))[1]}) would be the Original, not "
                                  f"{c.get('Outlet', '')} ({RR.tier(c, credited=cred, home=home_for(c))[1]}): {ch['why']}; the existing Original was kept (date-only difference): Sammy to decide")
            elif '_text' not in c and v.get('conf') != 'headline' and rk(o) < rk(c):
                e['order'] = (f"under the originals order this find ({RR.tier(o, credited=cred)[1]}) would be the Original, not {c.get('Outlet', '')} "
                              f"({RR.tier(c, credited=cred)[1]}); the existing Original was kept (cells are never changed): Sammy to decide")
            if not swapped:
                o.update({'Original or reprint': 'Reprint', 'Story ID': target, '_auto_reprint': True, '_ph_sid': ph})
                o.pop('# of reprints', None)
            self.res['reprint_check'].append(e)
        return [r for r in rows if not r.get('_dup')]

    def headline_story(self, o, min_j=0.8, days=7):
        """REQ-14 (4): the existing Original whose headline matches the blocked find's headline (Jaccard >= min_j on content words) within `days` days.
        -> (original row dict, jaccard, days apart) or None. Both headlines are cut at the first ' - ' / ' | ' segment as well.
        Replay fix (2026-10-30; 37 of 193 hits on the master were independent write-ups): a match is only MERGED (returned) when the two rows are of
        the same outlet house, the headline matches (Jaccard >= 0.8), within 2 days and carries the same numbers; and never when the headline
        recurs among the Originals (a weekly column or release). Different houses are never merged on a headline alone. Any other match is only flagged: `res['headline_review']` and a note on the find, no merge."""
        if RR is None:
            return None
        def toks(h):
            return {w[:-1] if len(w) > 4 and w.endswith('s') and not w.endswith('ss') else w for w in RR.hwords(h)}   # approve / approves
        seg = lambda h: re.split(r'\s+[-|\u2013\u2014]\s+', str(h or ''), maxsplit=1)[0]
        mine = [toks(o.get('Headline')), toks(seg(o.get('Headline')))]
        od = RR.todate(str(o.get('Date') or '')[:10])
        best = None
        for c in self.originals():
            cd = RR.todate(str(c.get('Date') or '')[:10])
            if not od or not cd or abs((od - cd).days) > days:
                continue
            for a in mine:
                for b in (toks(c.get('Headline')), toks(seg(c.get('Headline')))):
                    if len(a) < 4 or len(b) < 4:
                        continue
                    j = len(a & b) / len(a | b)
                    if j >= min_j and (best is None or j > best[1]):
                        best = (c, j, abs((od - cd).days))
        if best is None:
            return None
        c, j, d = best
        ct = toks(c.get('Headline'))
        recurring = sum(1 for x in self.originals() if x is not c and toks(x.get('Headline')) == ct) >= 1
        try:
            house = bool(RR.same_house(o, c))
        except Exception:
            house = False
        nums = lambda h: sorted(re.findall(r'\d+', str(h or '')))
        if house and not recurring and j >= 0.8 and d <= 2 and nums(o.get('Headline')) == nums(c.get('Headline')):
            return best
        note = f"possible duplicate of {c.get('Article ID', '')} ({c.get('Outlet', '')}, {str(c.get('Date'))[:10]}): similar headline ({j:.2f}), {'recurring headline' if recurring else ('different outlet house' if not house else 'dates or numbers differ or more than 2 days apart')}; not merged"
        self.res.setdefault('headline_review', []).append({'placeholder': o.get('Article ID', ''), 'outlet': o.get('Outlet', ''), 'other': c.get('Article ID', ''),
                                                           'other_outlet': c.get('Outlet', ''), 'jaccard': round(j, 2), 'days': d, 'recurring': recurring, 'note': note})
        tn = norm_val(o.get('Team note'))
        o['Team note'] = (tn + '; ' if tn else '') + note
        return None

    def central_wanted(self, home, sid, extra, run_id, o, e=None):
        """CHAINORIG-v1 (originals order v2 step 3): the reporter's employer on the story date is a central / national desk (USA TODAY for
        Gannett network papers, AP, ...) with no row in the story -> an originator-add is proposed (`origin_wanted`): fetch the desk's page
        for the headline; no page -> a no-copy Original (NOCOPY-v2). The Original is never moved to a local sibling for want of the desk.
        Returns the {key, house, type} when wanted, else None."""
        if REP is None or not home:
            return None
        rows = self.story_rows_dicts(sid) + [x for x in extra if x is not None]
        cm = REP.central_missing(rows, home)
        if not cm:
            return None
        if not any(w['story'] == sid and w['employer'] == cm['key'] for w in self.res['origin_wanted']):
            w = {'run': run_id, 'story': sid, 'placeholder': o.get('Article ID', ''), 'employer': cm['key'], 'house': cm['house'], 'type': cm['type'],
                 'headline': o.get('Headline', ''), 'date': str(o.get('Date') or '')[:10], 'byline': o.get('Author / byline', ''),
                 'why': (home.get('why', '') if isinstance(home, dict) else '') or 'reporter record',
                 'action': f"originator-add: search the headline on {cm['key']} and fetch the page (save the copy add-only); no page -> no-copy Original row (NOCOPY-v2); "
                           f"the story's rows become its Reprints; do not make a local sibling the Original"}
            self.res['origin_wanted'].append(w)
        if e is not None:
            e['origin_wanted'] = cm['key']
        return cm

    def swap_original(self, c, o, sid, why, run_id):
        """REPRINT-v2: the find `o` becomes the Original of story `sid`; the sheet row of `c` (the current Original) becomes a Reprint.
        Tone / Tone note / Tone rated by / Topic / Bills carry to the new Original blank-only and are cleared on the old row
        (DECISIONS 90, 110(3), 167); "# of reprints" moves with the Original and is recounted. Returns True when done."""
        r = c.get('_row') or self.s.original_row(sid)
        if r is None or 'Original or reprint' not in self.s.col:
            return False
        moved = {}
        undo = {'row': r, 'cells': {}, 'o_cols': []}   # AUDIT F4: everything needed to put the row back (unswap_original)
        for col in ORIGINAL_ONLY:
            if col in self.s.col:
                v = self.s.get(r, col)
                if not blank(v):
                    moved[col] = v
                    undo['cells'][col] = v
                    if blank(o.get(col)) and col != '# of reprints':
                        o[col] = v
                        undo['o_cols'].append(col)
                    self.s.ws.cell(r, self.s.col[col]).value = None
        undo['cells']['Original or reprint'] = self.s.get(r, 'Original or reprint')
        self.s.put(r, 'Original or reprint', 'Reprint')
        if 'Team note' in self.s.col:
            tn = norm_val(self.s.get(r, 'Team note'))
            undo['cells']['Team note'] = self.s.get(r, 'Team note')
            self.s.put(r, 'Team note', (tn + '; ' if tn else '') + f'Reprint since {self.today}: {o.get("Outlet", "")} is the Original ({why[:120]})')
        o['_swap_undo'] = undo
        o.update({'Original or reprint': 'Original', 'Story ID': sid, '_auto_original': True, '_swapped_from': c.get('Article ID', '')})
        old_n = moved.get('# of reprints', 0)
        o['# of reprints'] = (0 if blank(old_n) else int(float(old_n))) + 1   # the old Original's outlet is now a reprint outlet
        c['Original or reprint'] = 'Reprint'
        self._origs = None   # the originals list changes
        self.touched_stories.add(sid)
        self.res['origin_swaps'].append({'run': run_id, 'story': sid, 'old_original': c.get('Article ID', ''), 'old_outlet': c.get('Outlet', ''),
                                         'new_original': o.get('Article ID', ''), 'new_outlet': o.get('Outlet', ''), 'why': why,
                                         'carried': sorted(k for k in moved if k != '# of reprints'),
                                         'cells': [[c.get('Article ID', ''), col] for col in ['Original or reprint', 'Team note'] + list(moved)]})
        return True

    def unswap_original(self, o):
        """AUDIT F4: a find that swap_original made the Original is not written after all (held, duplicate link, removed story):
        the old Original row gets its kind, Team note and Tone / Topic / Bills back, and the swap is dropped from origin_swaps."""
        undo = o.pop('_swap_undo', None) if isinstance(o, dict) else None
        if not undo:
            return
        r = undo['row']
        for col, v in undo['cells'].items():
            if col in self.s.col:
                self.s.ws.cell(r, self.s.col[col]).value = v
        for col in undo['o_cols']:
            o.pop(col, None)
        o.pop('_auto_original', None)
        old = o.pop('_swapped_from', '')
        self.res['origin_swaps'] = [e for e in self.res['origin_swaps'] if not (e.get('old_original') == old and e.get('new_original') == o.get('Article ID', ''))]
        self.res.setdefault('origin_swaps_undone', []).append({'story': self.s.get(r, 'Story ID'), 'old_original': old, 'find': o.get('Article ID', '')})
        self._origs = None

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
            if hasattr(RR, 'pair_class') and (v is not None or ft):   # REPRINT-v2 cells: AV / same outlet / wire-wire / containment / translation
                pc = RR.pair_class(dict(orig, _av_item=self.av_items().get(orig.get('Article ID', ''), '')), o, v, frozenset(), self.home_of, {id(o): (ft or ('',))[0]})
                e['cell'] = pc['kind'] + ': ' + pc['note']
                if pc['kind'] in ('reprint', 'translation') and not (v and v['ok']):
                    v = dict(v or {'m': None, 'mode': 'credit'}, ok=True, conf=pc['conf'])
                elif pc['kind'] == 'never' and v is not None:
                    v = dict(v, ok=False)
                elif pc['kind'] == 'edition':
                    o['_dup'] = True
                    self.res['skipped'].append(dict(e, why='same outlet as the story\'s Original: an edition (Web + Print), not a reprint row'))
                    continue
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
        return [r for r in rows if not r.get('_dup')]

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
                has_copy = bool((pages.get(c.get('page')) or {}).get('clean'))
                svc = nocopy_service(c.get('outlet') or og.get('service'))
                credited = og.get('how') in CREDIT_HOWS and bool(c.get('outlet') or og.get('service'))
                # REPRINT-v2: an originator on a blocked site is added without a copy when the find credits it.
                # NOCOPY-v2: also a credited service with no public page (CBM members-only, CNS / BCN wire: no url), and any
                # credited originator whose page could not be fetched (bot wall, login: c.nopage)
                nocopy = (not has_copy) and credited and (
                    (hasattr(RR, 'is_blocked_host') and url.startswith('http') and RR.is_blocked_host(url)) or bool(svc) or bool(c.get('nopage')))
                if url.startswith('http'):
                    hit = next((self.s.links[k] for k in identity_links(lambda col: url if col == 'Publisher link' else None) if k in self.s.links), None)
                    gone = next((self.s.removed_links[k] for k in identity_links(lambda col: url if col == 'Publisher link' else None)
                                 if k in getattr(self.s, 'removed_links', {})), None)
                    if gone and not hit:   # AUDIT F2 (final-int): an originator on the Removed tab is not added again
                        self.res['skipped'].append({'run': run_id, 'placeholder': ph, 'outlet': c.get('outlet', ''), 'link': url,
                                                    'why': f'originator link is on the Removed tab (row {gone}): not re-added'})
                        self.res['pages_drop'].append(c.get('page', ''))
                        continue
                else:
                    hit = self.nocopy_existing(c, svc, o) if nocopy else None
                if hit:
                    # NOCOPY-v2: dedupe against EXISTING rows first: the originator is already a row (maybe of another story)
                    # -> a story merge is proposed (queue item cat "merge"), never a second row
                    self.res.setdefault('origin_merge', []).append({'run': run_id, 'placeholder': ph, 'outlet': o.get('Outlet', ''),
                                                                    'origin': url or (svc[0] if svc else c.get('outlet', '')), 'existing': hit,
                                                                    'story': self.s.get(self.s.rows[hit], 'Story ID') if hit in self.s.rows else ''})
                    self.res['pages_drop'].append(c.get('page', ''))
                    continue
                if (url.startswith('http') and any(norm_url(x.get('Publisher link')) == norm_url(url) for x in out)) or not (has_copy or nocopy) \
                   or (not url.startswith('http') and not nocopy):
                    self.res['pages_drop'].append(c.get('page', ''))
                    continue
                t = str(c.get('title') or o.get('Headline') or '')
                row = {'Article ID': f'{ph}-og{i + 1}', 'Story ID': f's{ph}-og{i + 1}', 'Original or reprint': 'Original',
                       'Data Source': o.get('Data Source') or 'Web search (TinyFish)', 'Date': c.get('date') or o.get('Date', ''),
                       'Outlet': (svc[0] if svc else '') or c.get('outlet') or og.get('service', ''), 'Headline': t, 'Edition': 'Web', 'Language': o.get('Language') or 'English',
                       'Role': 'Named in headline' if re.search('gabriel', t, re.I) else 'Mentioned in story', 'Publisher link': url,
                       'Link status': 'Publisher URL', '_page': c.get('page'), '_og_of': ph, '_og_how': og.get('how', ''), '_date_src': 'tinyfish'}
                if nocopy:
                    ls = svc[1] if svc else 'Publisher URL (blocked site, no copy)'
                    row.update({'_nocopy': True, 'Saved Copy?': 'No', 'Link status': ls, '_page': None,
                                'Team note': f'Originator added without a copy ({ls}); credited by {o.get("Outlet", "")} {self.today}'})
                    if not url.startswith('http'):
                        # NOCOPY-v2: no link -> Data Source "Reprint credit (no copy)"; text fields from the find (its reprint)
                        row.update({'Data Source': NOCOPY_DS, 'Publisher link': '', 'Date': c.get('date') or o.get('Date', ''),
                                    'Author / byline': o.get('Author / byline', ''), '_date_src': 'reprint'})   # DATES-v1 vocabulary: copied from reprint
                out.append(row)
        return out

    def nocopy_existing(self, c, svc, find):
        """NOCOPY-v2 dedupe for a no-link originator: an existing Coverage row of the same service within 3 days of the find whose
        headline matches the find's -> its Article ID (else None)"""
        name = norm_outlet(svc[0] if svc else c.get('outlet', ''))
        d0 = RR.todate(c.get('date') or find.get('Date')) if RR is not None else None
        hl = str(c.get('title') or find.get('Headline') or '')
        for aid, r in self.s.rows.items():
            if norm_outlet(self.s.get(r, 'Outlet'), self.s.get(r, 'Outlet city')) != name:
                continue
            d1 = RR.todate(self.s.get(r, 'Date')) if RR is not None else None
            if d0 and d1 and abs((d0 - d1).days) > 3:
                continue
            h2 = str(self.s.get(r, 'Headline') or '')
            if RR is not None and hasattr(RR, 'headline_sim') and RR.headline_sim(hl, h2) >= 0.8 or norm_val(h2).lower() == hl.strip().lower():
                return aid
        return None

    def origin_merge_items(self):
        """NOCOPY-v2: queue items (cat "merge") for finds whose originator is already a row of ANOTHER story"""
        out = []
        for e in self.res.get('origin_merge') or []:
            aid = self.ids.get(e['placeholder']) or e['placeholder']
            r = self.s.rows.get(aid)
            fsid = self.s.get(r, 'Story ID') if r else ''
            if not e.get('story') or fsid == e['story']:
                continue   # the find already went into the originator's story (reprint_check), nothing to merge
            out.append({'cat': 'merge', 'conf': 'medium', 'id': f'merge-{self._qtag()}-{len(out):03d}', 'key': fsid or aid,
                        'title': f"Merge {fsid or aid} ({e.get('outlet', '')}) into {e['story']}? Its credited originator is already row {e['existing']}",
                        'detail': f"The Update button found {e.get('outlet', '')} ({aid}) crediting {e.get('origin', '')}; that originator is row "
                                  f"{e['existing']} of story {e['story']}. Proposal: move {fsid or aid}'s rows into {e['story']} as Reprints "
                                  f"(the originals order v2 decides the Original).",
                        'options': [f'Merge {fsid or aid} into {e["story"]}', 'Keep separate'], 'proposed': f'Merge {fsid or aid} into {e["story"]}'})
        return out

    # ---------- QUEUEAPPLY-v1 (final-int 2026-10-29; FINAL_SYNTH "queue follow-through"): the review-queue items this task
    # made (queue_after: cat outlet / merge / billtags / nearcopy, ids <cat>-<12-digit run tag>-NNN) are read back once
    # Sammy decided them: outlet -> a code/outlets.json record + blank cells of the outlet's rows; merge -> the story's rows
    # join the target story as Reprints (sheet_task.swap_original semantics: Tone / Topic / Bills carried blank-only);
    # billtags -> Bills of the story's Original (blank only); nearcopy "Count as a copy" -> Press release = Yes on the story's
    # rows (blank only). Every action is idempotent; items already in the queue's `applied` collection are skipped; the old
    # hand-applied items (rv2*, outlet-q*, billtag-000 ...) never match the id pattern. Applied items -> result.queue_applied
    # (the prompt writes each into the review queue's `applied` collection).
    QUEUE_OWN = re.compile(r'^(merge|outlet|billtag|nearcopy)-\d{8,14}-\d{3}$')

    def apply_queue(self):
        if not self.queue:
            return
        items, dec, done = self.queue
        for iid in sorted(items):
            it = items[iid]
            if not self.QUEUE_OWN.match(iid) or iid in done or iid not in dec:
                continue
            ch = (dec[iid] or {}).get('choice')
            if ch in (None, '', []):
                continue
            chs = [str(c) for c in (ch if isinstance(ch, list) else [ch])]
            cat = it.get('cat') or iid.split('-')[0]
            e = {'id': iid, 'cat': cat, 'choice': ch, 'by': (dec[iid] or {}).get('by', ''), 'done': [], 'cells': []}
            try:
                if cat == 'outlet':
                    self._q_outlet(it, chs, e)
                elif cat == 'merge':
                    for c in chs:
                        m = re.match(r'^Merge (s\d{5}) into (s\d{5})', c)
                        if m:
                            self._q_merge(m.group(1), m.group(2), iid, e)
                elif cat == 'billtags':
                    for c in chs:
                        m = re.match(r'^Add (.+?) to (s\d{5})$', c)
                        if m:
                            self._q_bill(m.group(2), m.group(1).strip(), iid, e)
                elif cat == 'nearcopy':
                    m = re.match(r'^Count as a copy of (pr\d{5})', chs[0])
                    if m:
                        sid = str(it.get('key', '')).split(':')[-1]
                        for r in self.s.story_rows.get(sid, []):
                            if self.fill(r, 'Press release', 'Yes', f'queue {iid}: {chs[0]}', iid) == 'written':
                                e['done'].append(f"{self.s.get(r, 'Article ID')} Press release = Yes")
            except Exception as ex:   # one bad item never stops the run
                self.res['queue_conflicts'].append({'id': iid, 'why': f'not applied: {ex!r}'[:300]})
                continue
            if not e['done']:
                e['done'] = ['nothing to change (already applied, or a "keep" choice)']
            self.res['queue_applied'].append(e)

    def _q_outlet(self, it, chs, e):
        key = str(it.get('key') or '')
        reach = [c for c in chs if c in REACH_LABELS]
        if not key or not reach:
            return
        rec0 = OUTLETS.get(key)
        if rec0:
            if sorted(rec0.get('reach') or []) != sorted(reach):
                self.res['queue_conflicts'].append({'id': e['id'], 'why': f'outlets.json already has {key!r} with Reach {rec0.get("reach")}: not overwritten'})
        else:
            rec = {k: v for k, v in (it.get('record') or {}).items() if k != 'reach'}
            rec.update({'reach': reach, 'reach_conf': 'high', 'src': {'reach': f"queue {e['id']} ({e.get('by') or 'Sammy'})", 'record': 'proposed by the sheet task (OUTLETREC-v1)'}})
            path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'outlets.json')
            full = json.load(open(path, encoding='utf-8'))
            full.setdefault('records', {})[key] = rec
            tmp = path + '.tmp'
            json.dump(full, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            _os.replace(tmp, path)
            OUTLETS[key] = rec
            self.res['outlets_changed'] = True
            e['done'].append(f'outlets.json record {key}: Reach {"; ".join(reach)}')
        rec = outlet_record(key)
        for r in range(2, self.s.last_row + 1):
            if norm_outlet(self.s.get(r, 'Outlet'), self.s.get(r, 'Outlet city')) != key:
                continue
            for col, k in (('Reach', 'reach'), ('Medium', 'medium'), ('Publisher', 'publisher'), ('Outlet city', 'city'),
                           ('Outlet county', 'county'), ('Outlet state', 'state')):
                if col in self.s.col and rec.get(k) and self.fill(r, col, rec[k], f"queue {e['id']}: outlet record", e['id']) == 'written':
                    e['done'].append(f"{self.s.get(r, 'Article ID')} {col}")

    def _q_bill(self, sid, bill, iid, e):
        r = self.s.original_row(sid)
        if r is None or 'Bills' not in self.s.col:
            self.res['queue_conflicts'].append({'id': iid, 'why': f'{sid}: no Original row'})
            return
        cur = norm_val(self.s.get(r, 'Bills'))
        if bill.lower() in [x.strip().lower() for x in cur.split(';')]:
            return
        if cur:
            self.res['queue_conflicts'].append({'id': iid, 'why': f'{sid} Bills is now {cur!r}: {bill} not added (blank cells only)'})
            return
        self.s.put(r, 'Bills', bill)
        self.written += 1
        e['done'].append(f'{sid} Bills = {bill}')

    def _q_merge(self, s, ts, iid, e):
        """QUEUEAPPLY-v1: story s joins ts (the decision's target keeps its Original); s's Original becomes a Reprint"""
        rows = list(self.s.story_rows.get(s, []))
        to = self.s.original_row(ts)
        if not rows:
            return   # already merged (idempotent)
        if to is None:
            self.res['queue_conflicts'].append({'id': iid, 'why': f'merge {s} -> {ts}: {ts} has no Original row'})
            return
        note = f'Merged into {ts} on {self.today} (review queue {iid})'
        for r in rows:
            aid = self.s.get(r, 'Article ID')
            cells = ['Story ID']
            if self.s.get(r, 'Original or reprint') == 'Original':
                for col in ORIGINAL_ONLY:
                    if col in self.s.col and not blank(self.s.get(r, col)):
                        if col != '# of reprints' and blank(self.s.get(to, col)):
                            self.s.put(to, col, self.s.get(r, col))
                        self.s.ws.cell(r, self.s.col[col]).value = None
                        cells.append(col)
                self.s.put(r, 'Original or reprint', 'Reprint')
                cells.append('Original or reprint')
            self.s.put(r, 'Story ID', ts)
            if 'Team note' in self.s.col:
                tn = norm_val(self.s.get(r, 'Team note'))
                self.s.put(r, 'Team note', (tn + '; ' if tn else '') + note)
                cells.append('Team note')
            e['cells'] += [[aid, c] for c in cells]
            self.s.story_rows.setdefault(ts, []).append(r)
        self.s.story_rows.pop(s, None)
        self._origs = None
        self._queue_counts.add(ts)
        e['done'].append(f'{s} ({len(rows)} rows) merged into {ts}')

    def queue_recount(self):
        """QUEUEAPPLY-v1: "# of reprints" of a merge target = distinct reprint outlets (norm_outlet), not the Original's"""
        for ts in sorted(self._queue_counts):
            o = self.s.original_row(ts)
            if o is None:
                continue
            no = lambda r: norm_outlet(self.s.get(r, 'Outlet'), self.s.get(r, 'Outlet city'))
            n = len({no(r) for r in self.s.story_rows.get(ts, []) if self.s.get(r, 'Original or reprint') == 'Reprint'} - {no(o), ''})
            cur = self.s.get(o, '# of reprints')
            if blank(cur) or int(float(cur)) != n:
                self.s.put(o, '# of reprints', n)
                self.res['reprint_counts'][ts] = {'old': cur, 'new': n, 'new_outlets': [], 'why': 'queue merge'}

    # ---------- DRIFT-4 (final-int 2026-10-29): a no-copy originator the button added carries the cells the offline path
    # (v23 originator_add) copied from its crediting reprint: Role, Mentions, Mention depth, Author 1..9 / Author title (blanks only)
    NOCOPY_FROM_REPRINT = ('Role', 'Mentions "Gabriel" in text', 'Mention depth', 'Quoted') + tuple(f'Author {i}' for i in range(1, 10)) + ('Author title',)

    def nocopy_from_reprint(self):
        for r in range(self.first_new_row + 1, self.s.last_row + 1):
            if self.s.get(r, 'Original or reprint') != 'Original' or 'Originator added without a copy' not in norm_val(self.s.get(r, 'Team note')):
                continue
            sid = self.s.get(r, 'Story ID')
            rep = next((x for x in self.s.story_rows.get(sid, []) if x > self.first_new_row and self.s.get(x, 'Original or reprint') == 'Reprint'), None)
            if rep is None:
                continue
            same_by = norm_val(self.s.get(r, 'Author / byline')) in ('', norm_val(self.s.get(rep, 'Author / byline')))
            got = []
            for col in self.NOCOPY_FROM_REPRINT:
                if col not in self.s.col or (col.startswith('Author') and not same_by):
                    continue
                if col == 'Role' and not blank(self.s.get(rep, 'Role')) and norm_val(self.s.get(r, 'Role')) != norm_val(self.s.get(rep, 'Role')):
                    self.s.put(r, 'Role', self.s.get(rep, 'Role'))   # the row is new this run: its headline-only Role gives way to the reprint's
                    got.append(col)
                    continue
                if self.fill(r, col, self.s.get(rep, col), 'NOCOPY-v2: copied from the crediting reprint', self.s.get(rep, 'Article ID')) == 'written':
                    got.append(col)
            if got:
                self.res['nocopy_filled'].append({'aid': self.s.get(r, 'Article ID'), 'from': self.s.get(rep, 'Article ID'), 'cols': got})

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
                self.res['origin_added' if not o.get('_nocopy') else 'origin_nocopy'].append(dict(e, reprints=[x.get('Article ID', '') for x in got]))
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
        getattr(self, '_show_hint', {}).pop('pending', None)
        if SN is not None and out:   # SHOWNET-v1: "Show [Network]" -> the network; inverted show / podcast names un-inverted; talk-radio show -> its station; access labels dropped
            sp = SN.split_outlet(out, vals.get('Medium'), vals.get('Channel') or obj.get('Channel') or obj.get('_channel'))
            if sp['kind']:
                vals['Outlet'] = sp['outlet']
                self.res.setdefault('outlet_split', []).append({'run': run_id, 'placeholder': ph_aid, 'from': out, 'outlet': sp['outlet'], 'show': sp['show'], 'label': sp['label'], 'kind': sp['kind']})
                if sp['show']:
                    if not hasattr(self, '_show_hint'):
                        self._show_hint = {}
                    self._show_hint[ph_aid or ('row:' + out)] = sp
                    self._show_hint['pending'] = sp
                out = sp['outlet']
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
        # OUTLETREC-v1: blanks the sheet's consensus left open come from the outlet's record (code/outlets.json); blank cells only
        rec = outlet_record(vals.get('Outlet'), vals.get('Outlet city'), language=vals.get('Language'), medium=vals.get('Medium'),
                            publisher=vals.get('Publisher'), state=vals.get('Outlet state'), url=vals.get('Publisher link'))
        if rec['known']:
            for c, f in (('Medium', 'medium'), ('Publisher', 'publisher'), ('Outlet city', 'city'), ('Outlet county', 'county'),
                         ('Outlet state', 'state'), ('Language', 'language')):
                if c in self.s.col and blank(vals.get(c)) and rec.get(f):
                    vals[c] = rec[f]
        else:
            self.note_new_outlet(vals, rec, run_id, ph_aid)
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
            # OUTLETREC-v1 precedence: the outlet's record (variant / language overrides; not a low-confidence one) -> the sheet's
            # consensus (as before) -> the defaulting rules for an outlet with no record
            rec = outlet_record(vals.get('Outlet'), vals.get('Outlet city'), raw=vals.get('Outlet'), language=vals.get('Language'),
                                medium=vals.get('Medium'), publisher=vals.get('Publisher'), state=vals.get('Outlet state'), url=vals.get('Publisher link'))
            cons, seen = self.reach_for(vals.get('Outlet'), vals.get('Outlet city'))
            how = 'the outlet’s Reach in the sheet'
            if rec['known'] and rec['reach'] and rec.get('reach_conf') != 'low':
                cons, how = rec['reach'], f"the outlet’s record (outlets.json: {rec.get('reach_src') or 'record'})"
            elif not cons and not rec['known'] and rec['reach']:
                cons, how = rec['reach'], f"new outlet, {rec['reach_src']}"
            g_rec = (OUTLETS.get(rec.get('key')) or {}) if rec.get('known') else {}
            g_rec = dict(g_rec, key=rec.get('key'), type=rec.get('type') or g_rec.get('type', ''), country=rec.get('country') or g_rec.get('country', ''))
            cons2, g_why = reach_guard(cons, g_rec, vals.get('Outlet state') or rec.get('state'), vals.get('Outlet city') or rec.get('city'),
                                       vals.get('Language') or rec.get('language'), vals.get('Outlet'))
            if g_why:    # REACHFIX-v1: the rule default wins and the outlet goes to the review queue (once per outlet)
                k_ = rec.get('key')
                if k_ and k_ not in self._reachflag:
                    self._reachflag.add(k_)
                    self.res['reach_review'].append({'run': run_id, 'placeholder': ph_aid, 'key': k_, 'outlet': norm_val(vals.get('Outlet')),
                                                     'was': cons, 'written': cons2, 'why': g_why,
                                                     'link': norm_val(vals.get('Publisher link'))})
                cons, how = cons2, how + ' - ' + g_why
            prop = norm_val(vals.get('Reach'))
            vals['Reach'] = cons
            tags = lambda s: {x.strip() for x in str(s or '').split(';') if x.strip()}
            if prop and tags(prop) != tags(cons):
                self.res['reach'].append({'run': run_id, 'placeholder': ph_aid, 'outlet': vals.get('Outlet', ''), 'tracker': prop,
                                          'written': cons, 'why': how if cons else
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
        qd = quoted_him(t, CH.gab_re(self.rules()), self.s.get(r, 'Author / byline'))
        if 'Mention depth' in self.s.col:   # INCL-v1: derived from the same saved text; a blank result stays blank
            dep = mention_depth(t, self.s.get(r, 'Headline'), self.s.get(r, 'Author / byline'), CH.gab_re(self.rules()))
            if 'Quoted' in self.s.col:      # DEPTHQ-v1: depth and the Quoted flag agree
                dep = depthq(dep, qd, t)
            self.fill(r, 'Mention depth', dep, 'pages', pid)
        if 'Quoted' in self.s.col:   # QUOTED-v1: Yes when his own words are quoted (blank otherwise; an op-ed by him is blank)
            if qd:
                self.fill(r, 'Quoted', 'Yes', 'pages', pid)

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
            if sheet_applied((run or {}).get('sheet')):
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
            # RECALLFIX-v1 (6): the listing page's time stamp (run doc time_utc / time_pt) goes into the release doc, and below into the tab
            _tu, _tp = str(x.get('time_utc') or '').strip(), str(x.get('time_pt') or '').strip()
            if re.match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$', _tu) and not _tu.endswith('T00:00:00Z'):
                rel['time_utc'] = _tu
                if _tp:
                    rel['time_pt'] = _tp
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
            if rel.get('time_utc'):   # RECALLFIX-v1 (6): the tab has no time column, so the Note carries it (and a "Posted time (PT)" column when the tab has one)
                note += f"; page time stamp {rel.get('time_pt') or rel['time_utc']} ({rel['time_utc']}; the page's created stamp, not an e-mail send time)"
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
            if rel.get('time_pt') and H.get('Posted time (PT)'):   # RECALLFIX-v1 (6): optional column, filled only when the tab has it
                ws.cell(r, H['Posted time (PT)']).value = rel['time_pt']
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
            if sheet_applied((run or {}).get('sheet')):
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

    # ---------- AGGORIGIN-v1 (agg-orig 2026-10-29; Sammy: the Update button keeps aggregators out of the Original slot) ----------
    def find_text(self, obj):
        """plain text of a find's saved page doc (scoped, else clean), '' when none"""
        pid = self.page_doc_id(obj)
        p = (self.db.get('pages') or {}).get(pid) if pid else None
        if not p:
            return ''
        for key in ('scoped', 'clean'):
            body = p.get(key) or ''
            if body.strip():
                try:
                    return RR.html_text(body)[0] if RR is not None else re.sub(r'<[^>]+>', ' ', body)
                except Exception:
                    return re.sub(r'<[^>]+>', ' ', body)
        return ''

    def page_links(self, obj):
        pid = self.page_doc_id(obj)
        p = (self.db.get('pages') or {}).get(pid) if pid else None
        body = (p or {}).get('clean') or (p or {}).get('scoped') or ''
        return re.findall(r'href=["\']([^"\']+)', body)

    def outlet_name_of_key(self, key):
        if getattr(self, '_okeys', None) is None:
            self._okeys = {}
            for r in range(2, self.s.last_row + 1):
                o = norm_val(self.s.get(r, 'Outlet'))
                if o:
                    self._okeys.setdefault(RR.outlet_key(o, self.s.get(r, 'Outlet city')) if RR else o.lower(), o)
        return self._okeys.get(key) or str(key).title()

    def agg_origin_step(self, rows, run_id):
        """AGGORIGIN-v1: a find whose Outlet is an aggregator / syndicator (the outlet type table: Yahoo, MSN, AOL, NewsBreak, ...) is never
        left as the Original. The provider / credit line in its saved text ("originally appeared in", "Read the original article on",
        "See at CNET", the Yahoo provider link, a station dateline) or, failing that, the byline's employer (reporters.Employment) names
        the originator, then
          - the originator is already a row (this story or another): `_origin` is set so reprint_check swaps / merges by the text rule (a
            story in ANOTHER story becomes a `merge` review item through origin_merge); below the text rule the find stays, with a Team note;
          - no row: the originator is added (its page when the find carries a URL, else a NOCOPY-v2 no-copy row, Data Source "Reprint credit (no copy)");
          - Yahoo's own editorial units (Yahoo Life, Yahoo News Hong Kong, ...) become the unit's name (a publisher, not an aggregator);
          - no identifiable source: kept, Team note "Originator unknown ...".
        Rows are changed in place; decisions are listed in res['agg_origin']."""
        if AO is None or RR is None:
            return rows
        res = self.res.setdefault('agg_origin', [])
        for o in rows:
            if (o.get('Original or reprint') or 'Original') != 'Original' or o.get('_og_of') or o.get('_auto_reprint') or o.get('_release'):
                continue
            outlet = norm_val(o.get('Outlet'))
            if not AO.is_aggregator(outlet, norm_val(o.get('Outlet city'))):
                continue
            ph = str(o.get('Article ID') or '')
            if isinstance(o.get('_origin'), dict) and o['_origin'].get('cands'):
                res.append({'run': run_id, 'placeholder': ph, 'outlet': outlet, 'action': 'tracker _origin', 'originator': o['_origin'].get('service', '')})
                continue
            def employer(f):
                k, _ = self.home_of(f)
                return self.outlet_name_of_key(k) if k else ''
            d = AO.resolve(o, self.find_text(o), self.page_links(o) + [str(o.get('Publisher link') or '')], self.originals(), employer)
            a = d['action']
            e = {'run': run_id, 'placeholder': ph, 'outlet': outlet, 'action': a, 'originator': d.get('outlet', ''), 'how': d.get('how', ''), 'evidence': d.get('evidence', '')}
            if a == 'unit':
                o['Outlet'] = d['outlet']
                o['Team note'] = (norm_val(o.get('Team note')) + '; ' if norm_val(o.get('Team note')) else '') + 'Outlet set to Yahoo\'s own unit (%s).' % d['outlet']
            elif a in ('known', 'wanted'):
                o['_agg_note'] = d['note']
                o['_agg_known'] = a == 'known'
                og = {'how': 'credit', 'service': d['outlet'], 'cands': [{'outlet': d['outlet'], 'url': '', 'title': norm_val(o.get('Headline')), 'date': '', 'nopage': True}]}
                if a == 'known':
                    row = d['row']
                    og['cands'][0]['title'] = norm_val(row.get('Headline') or o.get('Headline'))
                o['_origin'] = og
                if a == 'wanted':
                    self.res['origin_wanted'].append({'run': run_id, 'story': o.get('Story ID', ''), 'placeholder': ph, 'employer': d['outlet'], 'house': '',
                                                      'type': 'aggregator find', 'headline': o.get('Headline', ''), 'date': str(o.get('Date') or '')[:10],
                                                      'byline': o.get('Author / byline', ''),
                                                      'why': 'aggregator find (%s) credits %s: %s' % (outlet, d['outlet'], d['evidence']),
                                                      'action': 'originator-add: the page is fetched when the find carries its URL, else a no-copy Original row (NOCOPY-v2); '
                                                                'the aggregator find becomes its Reprint'})
            elif a == 'unknown':
                o['_agg_note'] = d['note']
            res.append(e)
        return rows

    def agg_origin_notes(self, rows, run_id):
        """AGGORIGIN-v1: finds that stay Original although the page credits another outlet / has no identifiable source get the Team note"""
        for o in rows:
            n = o.pop('_agg_note', None)
            if not n or (o.get('Original or reprint') or 'Original') != 'Original' or o.get('_auto_reprint'):
                continue
            tn = norm_val(o.get('Team note'))
            o['Team note'] = (tn + '; ' if tn else '') + n
        return rows

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
            # TAGS-v1: the shared "names a bill" rule (billmatch.names_bills) decides what the story text names: number in any
            # form, popular title, grant program, coauthor tie; never before the introduction date; Budget Acts and
            # another-member credits come back low and are never proposed as Add
            try:
                import billmatch as _bm
                _found = _bm.names_bills(txt, _bm.pad_date(d) or d)
            except Exception as _e:
                _found = {}
                self.res.setdefault('queue_errors', []).append(f'billmatch: {_e!r}'[:200])
            for prid, typ, lag in cand[sid]:
                for b in tab[prid]['bills']:
                    bi = next((x for x in binfo.get(b, []) if x.get('session') == sess(tab[prid]['date'])), None)
                    if b in info or not bi:
                        continue
                    f = _found.get(b)
                    auth = str(bi.get('role', '')).startswith('author') or bi.get('role') == 'principal coauthor'
                    info[b] = {'prid': prid, 'typ': typ, 'lag': lag, 'named': (f['ev'][:60] if f and f['conf'] != 'low' else ''),
                               'how': (f['how'] if f else 'not named in story text'), 'low': bool(f and f['conf'] == 'low'),
                               'same': sess(d) == sess(tab[prid]['date']), 'auth': auth, 'bi': bi}
                    bills.append(b)
            for b, f in _found.items():   # bills the story names that the release did not list
                if b not in info and f['conf'] != 'low':
                    bi = next((x for x in binfo.get(b, []) if x.get('session', '')[:4] == _bm.resolve(b, _bm.pad_date(d) or d, '-' in b)[0]['session'][:4]), None) if _bm.resolve(b, _bm.pad_date(d) or d, '-' in b)[0] else None
                    if bi:
                        info[b] = {'prid': '', 'typ': 'text', 'lag': None, 'named': f['ev'][:60], 'how': f['how'], 'low': False, 'same': True,
                                   'auth': str(bi.get('role', '')).startswith('author') or bi.get('role') == 'principal coauthor', 'bi': bi}
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
                            + (f"story text names it ({info[b].get('how', 'number')}: \"{info[b]['named']}\")" if info[b]['named'] else ('low confidence: ' + info[b].get('how', '') if info[b].get('low') else 'not named in story text'))
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
        q['merge'] = self.origin_merge_items()   # NOCOPY-v2: originator already in another story -> merge proposal
        # OUTLETREC-v1: one `outlet` item per new outlet key (replaces the outlet_untyped / reach run-doc lines nobody reads)
        q['outlet'] = []
        for e in self.res.get('outlet_new') or []:
            pr_ = e.get('proposed') or {}
            pre = [x.strip() for x in str(pr_.get('reach') or '').split(';') if x.strip()]
            q['outlet'].append({'cat': 'outlet', 'conf': 'medium' if pre else 'low', 'id': f'outlet-{self._qtag()}-{len(q["outlet"]):03d}',
                                'key': e['key'], 'multi': True,
                                'title': f"New outlet: {e.get('outlet') or e['key']}" + (f" ({e['host']})" if e.get('host') else ''),
                                'detail': f"{e.get('outlet')} · {e.get('link', '')} · type {pr_.get('type') or '?'} · proposed record: "
                                          + ' · '.join(f'{k} {v}' for k, v in pr_.items() if v) + f" · {e.get('why', '')}"
                                          + ' · a decision is written into code/outlets.json at the next run, then blank cells of the outlet\'s rows are filled from it',
                                'options': list(REACH_LABELS), 'proposed': pre, 'record': pr_})
        for e in self.res.get('reach_review') or []:   # REACHFIX-v1
            q['outlet'].append({'cat': 'outlet', 'conf': 'medium', 'id': f'outlet-{self._qtag()}-{len(q["outlet"]):03d}',
                                'key': e['key'], 'multi': True,
                                'title': f"Reach check: {e.get('outlet') or e['key']} is not a California outlet",
                                'detail': f"{e.get('outlet')} · {e.get('link', '')} · the sheet's Reach for this outlet was {e.get('was')}; it has no California location, "
                                          f"so the rule default {e.get('written')} was written. {e.get('why', '')}",
                                'options': list(REACH_LABELS), 'proposed': [x.strip() for x in str(e.get('written') or '').split(';') if x.strip()]})
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
        forced = {}
        for rid, run in (self.db.get('runs') or {}).items():
            for p, real in ((self.res['runs'].get(rid) or {}).get('ids') or {}).items():
                ph[real] = p
            for p, vals in ((run or {}).get('av') or {}).items():
                extra[p] = vals or {}
            for o in (run or {}).get('rows') or []:   # YTSTATION-v1: a row's own `_av` (the Update button's station-channel find) states the item; it wins over the extract
                if isinstance(o, dict) and isinstance(o.get('_av'), dict) and o.get('Article ID'):
                    forced[o['Article ID']] = o['_av']
        page_of = {x['aid']: x for x in self.res.get('pages', [])}
        rows = []
        for aid in dict.fromkeys(added):
            r = self.s.rows.get(aid)
            if not r or str(self.s.get(r, 'Medium') or '').strip() not in AV.MEDIA:
                continue
            cells = {c: self.s.get(r, c) for c in self.s.col}
            cells['_show'] = ((getattr(self, '_show_hint', {}) or {}).get(aid) or {}).get('show', '')   # SHOWNET-v1
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
            for c, v in (forced.get(ph.get(aid, ''), {}) or {}).items():   # YTSTATION-v1
                if c in AV.COLS and v not in ('', None) and c not in ('Article ID', 'Story ID', 'Medium'):
                    out[c] = v
            clip = AV.archive_clip(cells.get('Publisher link'))   # AVTAB-v2 sheet_task: Coverage Date = Pacific air date
            if clip and out.get('Air/publish date') and r > self.first_new_row:   # rows THIS run added only: an existing Date is never changed (verify would refuse the run)
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
            if 'Format' in self.s.col and r > self.first_new_row:   # FORMAT-v1: the extracted Item type settles a NEW row's Format (the creation default was Article); existing rows keep theirs
                fa = format_from_av(out.get('Item type'), self.s.get(r, 'Medium'))
                if fa and norm_val(self.s.get(r, 'Format')) in ('', 'Article', fa):
                    self.s.put(r, 'Format', fa)
            if r > self.first_new_row and hasattr(AV, 'role_depth'):   # REVIEW4-v1 F3/F4: a guest/moderator is Featured; transcribed on-air speech is Quoted (new rows only)
                if 'Mention depth' in self.s.col and AV.role_depth(out.get('His role')) == 'Featured':
                    self.s.put(r, 'Mention depth', 'Featured')
                elif 'Mention depth' in self.s.col and 'Quoted' in self.s.col and AV.spoken_quoted(out.get('His role'), self.page_text(self.saved_html[aid]) if aid in self.saved_html else ''):
                    if norm_val(self.s.get(r, 'Mention depth')) in ('', 'Named'):
                        self.s.put(r, 'Mention depth', 'Quoted')
                if 'Quoted' in self.s.col and AV.spoken_quoted(out.get('His role'), self.page_text(self.saved_html[aid]) if aid in self.saved_html else ''):
                    self.s.put(r, 'Quoted', 'Yes')
                for prev in rows:   # F5: the same episode on another platform is ONE story; listed for the merge, never auto-folded
                    if AV.same_episode(prev, out):
                        self.res.setdefault('av_edition_candidates', []).append({'aid': aid, 'same_as': prev.get('Article ID'), 'why': 'same show + episode + date on another platform: one story, the other an edition'})
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

    def apply_yt_attach(self):
        """YTSTATION-v1 (Sammy 2026-11-02): a run doc's `attach` = [{row_link, link, title, channel, station, network, medium, ...}]: a kept station YouTube video whose outlet already has a
        story within 2 days (the same segment). Not a new story: that story becomes a broadcast story (one story, both). The tracked row's Format is set to "Broadcast segment" (an
        explicit override of fill-blanks, this case only) and a Medium of "Video" becomes the channel's TV / Radio; its saved copy and every other cell stay. On its Audio & video details
        row Item type is set to "Broadcast segment" (same override) and blank Channel / Station / Network / YouTube link are filled; a row with no AV row gets one (Item type Broadcast
        segment, Channel, Station, Network, Episode/segment title = the row's headline, YouTube link, Details from "YouTube page"). Unplaceable items: res['yt_attach_unplaced']. Idempotent."""
        self.res.setdefault('yt_attached', []); self.res.setdefault('yt_attach_unplaced', [])
        if AV is None:
            return
        seen = set()
        for rid, run in sorted((self.db.get('runs') or {}).items()):
            for a in (run or {}).get('attach') or []:
                link = norm_val(a.get('link')); key = (rid, link)
                if not link or key in seen:
                    continue
                seen.add(key)
                aid = self.s.links.get(norm_url(a.get('row_link')))
                r = self.s.rows.get(aid) if aid else None
                if r is None:
                    self.res['yt_attach_unplaced'].append({'run': rid, 'link': link, 'row_link': a.get('row_link', ''), 'why': 'the tracked story\'s row was not found'}); continue
                if norm_url(link) == norm_url(norm_val(self.s.get(r, 'Publisher link'))):
                    continue
                changed, cells = [], []
                med = norm_val(self.s.get(r, 'Medium'))
                newmed = norm_val(a.get('medium')) or 'TV'
                if 'Medium' in self.s.col and med in ('Video', ''):
                    self.s.put(r, 'Medium', newmed); cells.append('Medium'); changed.append('Medium ' + (med or 'blank') + ' -> ' + newmed); med = newmed
                if 'Format' in self.s.col and norm_val(self.s.get(r, 'Format')) != 'Broadcast segment':
                    changed.append('Format ' + (norm_val(self.s.get(r, 'Format')) or 'blank') + ' -> Broadcast segment'); self.s.put(r, 'Format', 'Broadcast segment'); cells.append('Format')
                ws = self.s.wb['Audio & video details'] if 'Audio & video details' in self.s.wb.sheetnames else None
                H = {ws.cell(1, i).value: i for i in range(1, ws.max_column + 1)} if ws is not None else {}
                ar = next((i for i in range(2, ws.max_row + 1) if norm_val(ws.cell(i, H['Article ID']).value) == str(aid)), None) if H.get('Article ID') else None
                vals = {'Channel': norm_val(a.get('channel')), 'Station': norm_val(a.get('station')), 'Network': norm_val(a.get('network')), 'YouTube link': link}
                if ar is not None:
                    if norm_val(ws.cell(ar, H['Item type']).value) != 'Broadcast segment':
                        changed.append('AV Item type ' + (norm_val(ws.cell(ar, H['Item type']).value) or 'blank') + ' -> Broadcast segment'); ws.cell(ar, H['Item type']).value = 'Broadcast segment'
                    for c, v in vals.items():
                        if v and c in H and not norm_val(ws.cell(ar, H[c]).value):
                            ws.cell(ar, H[c]).value = v; changed.append('AV ' + c)
                else:
                    row = AV.blank_row()
                    row.update({'Article ID': str(aid), 'Story ID': norm_val(self.s.get(r, 'Story ID')), 'Medium': med or newmed, 'Item type': 'Broadcast segment',
                                'Episode/segment title': norm_val(self.s.get(r, 'Headline')), 'Details from': 'YouTube page'}); row.update(vals)
                    AV.write_tab(self.s.wb, [row]); changed.append('AV row added')
                if changed:
                    self.res['yt_attached'].append({'run': rid, 'aid': str(aid), 'link': link, 'channel': a.get('channel', ''), 'cells': cells, 'changed': changed})

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
                            delete_rows_keep_links(av, ar)   # v22: links re-anchored
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
            delete_rows_keep_links(self.s.ws, r)   # v22: links re-anchored
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
        self.nocopy_from_reprint()   # DRIFT-4 (final-int)
        self.apply_queue()   # QUEUEAPPLY-v1 (final-int): decided review-queue items
        self.apply_releases()   # RELCHECK-v1
        self.apply_release_finds()   # RELCHECK-v2
        self.apply_related_cols(getattr(self, 'release_related', None))   # RELBUTTON-v1: Copies (rows) / First copy date / Related
        self.apply_av()   # AVTAB-v1
        self.apply_yt_attach()   # YTSTATION-v1: a station video that is the same segment as a tracked story
        self.recount()
        self.queue_recount()   # QUEUEAPPLY-v1
        self.mark_red()   # BUTTONOPT-v1 (DECISIONS 102)
        self.execute_removals()   # BUTTONOPT-v1: last (row numbers shift)
        seen = set()   # BUTTONOPT-v1 (S5): one untestable entry per row and release
        self.res['releases_untestable'] = [x for x in self.res['releases_untestable'] if (x.get('aid'), x.get('url')) not in seen and not seen.add((x.get('aid'), x.get('url')))]
        self.res['pages_drop'] = sorted({p for p in self.res['pages_drop'] if p})
        self.relmatch_lists()   # RELBUTTON-v1
        return self.res


# INCL-v1 (Sammy 2026-10-28): "Mention depth" column - Featured | Quoted | Named | List-only (STRICT: rosters and lists) | blank
# (no text / text never names him). Designer heuristic (work/tmp_incl_design/build_texts.py depth() + classify.py mapping).
_D_QUOTE = re.compile(r'[“"”]')
_D_NAME2 = re.compile(r'\b[A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)+\b')
_D_SUBST = re.compile(r'(?i)\b(said|says|told|authored|introduced|wrote|chair|chairs|chairman|bill|AB\s?\d|SB\s?\d|propos|announc|vote|voted|'
                   r'sponsor|tax|ban|law|legislation|measure|budget|statement|called|urged|asked|pushed|led|leads|represent|district|D-|\(D)')
_D_SAID_AFTER = re.compile(r'Gabriel[^.]{0,80}\b(said|says|told|wrote|added|noted|argued|explained|stated)\b', re.I)
_D_SAID_BEFORE = re.compile(r'\b(said|says|told|wrote|added|noted|argued|explained|stated)\b[^.]{0,40}Gabriel', re.I)
_D_BYLINE = re.compile(r'Jesse\s+Gabriel', re.I)


def _depth_sentences(t):
    t = re.sub(r'\s+', ' ', t or '')
    t = re.sub(r'\s*[•*]\s+', '\n', t)
    return [x for x in re.split(r'(?<=[.!?。！？])\s+(?=[A-Z“"(\[])|\n+|(?<=[。！？])', t) if x.strip()]


def mention_depth(text, headline, byline, G):
    """Featured: op-ed by him, his name in the headline, >=3 sentences naming him with the first in the opening quarter,
    or >=2 quoted sentences. Quoted: >=1 sentence quoting him. List-only (STRICT): every sentence naming him is a roster
    (>=5 names, >=4 commas/semicolons, nothing predicated of him in the next 150 chars). Named: anything else that names him.
    '' when there is no text or the text never names him."""
    text = text or ''
    if not text.strip():
        return ''
    ms = list(G.finditer(text))
    if not ms:
        return ''
    if _D_BYLINE.search(str(byline or '')) or G.search(str(headline or '')):
        return 'Featured'
    words = len(text.split())
    first_pos = len(text[:ms[0].start()].split()) / max(1, words)
    sents = [x for x in _depth_sentences(text) if G.search(x)]
    listy = quoted = 0
    for x in sents:
        m = G.search(x)
        if len(set(_D_NAME2.findall(x))) >= 5 and x.count(',') + x.count(';') >= 4 and not _D_SUBST.search(x[m.end():m.end() + 150]):
            listy += 1
        if _D_QUOTE.search(x) and (_D_SAID_AFTER.search(x) or _D_SAID_BEFORE.search(x)):
            quoted += 1
    if not quoted and sents and listy == len(sents):
        return 'List-only'          # a roster stays List-only however early or often it names him
    if (len(sents) >= 3 and first_pos <= 0.25) or quoted >= 2:
        return 'Featured'
    return 'Quoted' if quoted else 'Named'


# DEPTHQ-v1 (Sammy 2026-10-29): "Mention depth" and the "Quoted" flag agree. Quoted=Yes and the depth would be Named -> Quoted;
# the depth is never Quoted when quoted_him is False and the text is there (Quoted -> Named). Featured, List-only and blank are untouched.
def depthq(depth, quoted, text):
    if not (text or '').strip():
        return depth
    if quoted and depth == 'Named':
        return 'Quoted'
    if not quoted and depth == 'Quoted':
        return 'Named'
    return depth


# QUOTED-v1 (Sammy 2026-10-29): "Quoted" tag - Jesse Gabriel is DIRECTLY quoted in the story (his own words in quotation marks).
# Yes when a sentence naming him holds a quotation (“ ” " " « » „ “ 「 」 『 』 ‘ ’) attributed to him: he is the subject of the said-verb
# before or after the quote ("..." Gabriel said / Gabriel said, "..." / Gabriel: "..." / according to Gabriel), and no other
# named speaker owns it ("..." Smith said of Gabriel; Gabriel said Smith called it "..."). Op-eds BY him are blank (his own
# article, not a quote of him; they stay Featured). Pronoun follow-ups ("..." he said) do not name him and are not counted.
_Q_SPEECH_EN = (r'said|says|say|told|tells|wrote|writes|write|added|adds|noted|notes|argued|argues|explained|explains|stated|states|continued|'
                r'emphasized|emphasised|stressed|commented|comments|declared|warned|warns|acknowledged|countered|responded|replied|tweeted|'
                r'posted|remarked|insisted|insists|vowed|pledged|announced|asked|asks|urged|urges|cautioned|concluded|contended|observed|'
                r'recalled|reiterated|claimed|charged|agreed|admitted|lamented|quipped|texted|testified|predicted|promised|expressed|'
                r'proclaimed|joked|complained|called|calls|described|describes|dubbed|labeled|labelled|characterized|characterised|'
                r'branded|put\s+it|summed\s+up|opined|alleged|conceded|boasted|reflected|elaborated|clarified|maintained|suggested|'
                r'stressing|adding|noting|saying|telling|writing|released|issued|shared|sent|submitted|delivered|highlighted|highlights|calling|describing|dubbing|labeling|characterizing|emphasizing|arguing|warning|explaining|stating|declaring|insisting')
_Q_SPEECH_X = (r'sagte|sagt|erkl[aä]rte|betonte|meinte|a\s+dit|a\s+d[eé]clar[eé]|affirme|explique|souligne|d[eé]clare|dijo|dice|'
               r'afirm[oó]|afirma|declar[oó]|se[nñ]al[oó]|explic[oó]|asegur[oó]|indic[oó]|a[nñ]adi[oó]|coment[oó]|expres[oó]|manifest[oó]|'
               r'advirti[oó]|destac[oó]|record[oó]|sostuvo|dej[oó]|agreg[oó]|resalt[oó]|enfatiz[oó]|opin[oó]|insisti[oó]|'
               r'disse|afirmou|сказал|заявил|отметил|подчеркнул|добавил|בירר|אמר|הוסיף|'
               r'говорит|сказала|заявила|сообщил|сообщила|написал|написала|'
               r'אמר[הו]?|הוסיף[ה]?|ציין|ציינה|הדגיש[הו]?|טען|טענה|מסר|מסרה|כתב|כתבה|הודיע[הו]?|'
               r'nói|cho\s+biết|nhấn\s+mạnh|'
               r'گفت|اظهار\s+داشت|'
               r'ըստ|ասաց|')
_Q_SPEECH_CJK = r'表示|说道|说|称|指出|强调|认为|表达|写道|补充|提到|談到|說|表達|指出|強調|認為|補充|말했다|말했|밝혔다|밝혔|전했다|설명했다|강조했다|주장했다|述べた|語った|話した|言った|コメント'
_Q_VERB = re.compile(r'(?:(?<![A-Za-zÀ-ÿ])(?:%s|%s)(?![A-Za-zÀ-ÿ])|(?:%s))' % (_Q_SPEECH_EN, _Q_SPEECH_X.rstrip('|'), _Q_SPEECH_CJK), re.I)
_Q_VERB_SAID = re.compile(r'(?<![A-Za-zÀ-ÿ])(?:said|says|told|wrote|added|noted|asked|stated|explained|argued|according)(?![A-Za-zÀ-ÿ])', re.I)
_Q_TITLE = set('''the a an state california californian democratic democrat republican assembly assemblyman assemblymember assemblywoman assemb asm
member mr rep rep. dr sen senator jesse co-author coauthor author lead bill sponsor bill\'s budget committee chair chairman chairwoman chairperson
majority leader speaker pro tem vice former new freshman local los angeles san fernando valley woodland hills encino northridge d r by
legislator lawmaker legislation democratic-led and also who then but however meanwhile today yesterday later'''.split())
_Q_STOP = set('''meanwhile later however still also then now today yesterday tonight monday tuesday wednesday thursday friday saturday sunday
instead earlier previously separately similarly while when although because since if as according per after before during but and or so yet on in at
january february march april may june july august september october november december last next this that these those both either neither
overall indeed notably importantly'''.split())
_Q_PREP_BEFORE = set('of to with for by from against at on about told asked thanked called praised criticized urged pressed tells asks that than like'.split())
_Q_ABBR = re.compile(r'(?:\b(?:Mr|Mrs|Ms|Dr|Sen|Rep|Gov|Asm|Assemb|Lt|Gen|Sgt|St|Jr|Sr|Calif|Ca|Cal|No|vs|Inc|Co|Corp|Ave|Blvd|Dem|Reps|Sens|Prof|Atty|Supt|Hon|Cmdr|Capt|Col|Maj|Pres|Gov|U\.S|D|R|I|a\.m|p\.m)|\b[A-Z])\.$')
_Q_CJK = re.compile(r'[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]')
_Q_OPEN = {'“': '”', '„': '“', '«': '»', '「': '」', '『': '』', '‹': '›', '‘': '’'}


def _q_spans(p):
    """quotation spans (start, end, inner) in one sentence/paragraph. “ ” and " " (mixed pairs too), „ “, « », 「 」, 『 』, and
    British ‘ ’ (only when closed by ’ before a non-letter). An opener with no closer runs to the end (a quote continued
    in the next sentence)."""
    spans, i, n = [], 0, len(p)
    while i < n:
        ch = p[i]
        if ch == '"' and 0 < i < n - 1 and '\u0590' <= p[i - 1] <= '\u05ff' and '\u0590' <= p[i + 1] <= '\u05ff':
            i += 1                                       # gershayim (יו"ר), not a quotation mark
        elif ch in '“"':
            j = i + 1
            while j < n and not (p[j] in '”' or (p[j] == '"' and not (p[j - 1:j] and '\u0590' <= p[j - 1] <= '\u05ff' and j + 1 < n and '\u0590' <= p[j + 1] <= '\u05ff'))):
                j += 1
            if j >= n:   # LOOSEENDS-v1: the closing mark was lost: '"This bill will ... additives, says the author, Jesse Gabriel, who ...'
                mm = re.search(r',\s+(?:says|said)\s+(?:the\s+)?(?:bill\W?s\s+)?[a-z]+', p[i + 1:])
                if mm and mm.start() > 20:
                    j = i + 1 + mm.start()
            sp_ = (i, min(n, j + 1), p[i + 1:j])
            spans.append(sp_)
            if len(sp_[2]) > 80 and '‘' in sp_[2]:   # a block quote that holds single-quoted speech: 'said Jesse Gabriel' follows the inner marks
                for m1 in re.finditer(r'(?<![A-Za-z0-9])‘', sp_[2]):
                    m2 = re.search('’(?![A-Za-zÀ-ÿ])', sp_[2][m1.end():])
                    if m2:
                        spans.append((i + 1 + m1.start(), i + 1 + m1.end() + m2.end(), sp_[2][m1.end():m1.end() + m2.start()]))
            i = j + 1
        elif ch == '”' and not spans and i >= 12 and '“' not in p[:i] and '"' not in p[:i]:
            spans.append((0, i + 1, p[:i])); i += 1      # the opening mark was lost in the saved copy: ‘... lawn,” said Gabriel’
        elif ch == '„':
            j = i + 1
            while j < n and p[j] not in '“”':
                j += 1
            spans.append((i, min(n, j + 1), p[i + 1:j])); i = j + 1
        elif ch in '«「『‹':
            close = {'«': '»', '「': '」', '『': '』', '‹': '›'}[ch]
            j = p.find(close, i + 1)
            if j < 0:
                j = n
            spans.append((i, min(n, j + 1), p[i + 1:j])); i = j + 1
        elif ch == '‘' and (i == 0 or not p[i - 1].isalpha()):
            m = re.search('’(?![A-Za-zÀ-ÿ])', p[i + 1:])
            if m:
                j = i + 1 + m.start()
                spans.append((i, j + 1, p[i + 1:j])); i = j + 1
            else:
                i += 1
        else:
            i += 1
    return spans


def _q_words(inner):
    s = inner.strip()
    if re.search(r'[぀-ヿ㐀-鿿가-힯]', s):
        return len(re.findall(r'[぀-ヿ㐀-鿿가-힯]', s)) // 2
    return len(s.split())


def _q_him(seg, G, base=0):
    """matches of his name in seg that are him (not Peter Gabriel / Gabriel Boric / Gabriel's office)"""
    out = []
    for m in G.finditer(seg):
        a, b = m.start(), m.end()
        w = m.group(0)
        if re.match(r'[A-Za-z]', w):
            pre = seg[:a].rstrip()
            pm = re.search(r'([A-Za-zÀ-ÿ\.\-\']+)$', pre)
            if pm and pre.endswith(pm.group(1)):
                tok = pm.group(1)
                tl = tok.lower().strip('.')
                if tok[:1].isupper() and tl not in _Q_TITLE and tl not in _Q_TFINAL and tl not in _Q_STOP and not re.search(r'\d|^[A-Z]{1,4}\.?$|^[A-Z]-', tok):
                    continue          # "Peter Gabriel", "Sigmar Gabriel" (a capitalised word that is not a title or a sentence adverb before it)
            post = seg[b:]
            if re.match(r'[ \t]+[A-Z][a-zà-ÿ]{2,}', post) and not re.match(r'[ \t]+(?:Democrat|Democratic|Dem|Said|Says|Told|California|Assembly|Assemblymember|Assemblyman|Assemblywoman|Member|Chair|Chairman|Budget|Committee|Caucus|Legislative|Jewish|Speaker|Senator|Republican|State|Encino|Woodland|Northridge|Sacramento)\b', post):
                continue              # "Gabriel Boric", "Gabriel Attal"
            if re.match(r'[’\']s\s+(?:office|spokes|staff|aide|team|press|communications|chief|legislative|district)', post, re.I):
                continue              # his office speaking, not him
        out.append((a, b))
    return out


_Q_TFINAL = set('''assemblymember assemblyman assemblywoman member chair chairman chairwoman chairperson chairs co-chair co-chairs cochair
cochairs co-chairperson co-chairpersons president leader speaker senator sen rep dr mr mrs ms author sponsor democrat democratic republican candidate
legislator lawmaker caucus committee delegation jessie jess asm assemb jesse councilmember councilman councilwoman vice treasurer'''.split())


def _q_prefix_ok(pre):
    """what stands before his name inside the speaker phrase: titles, party, 'the bill's author', a coordinated list
    ('Wiener and Gabriel said') - not an unrelated person ('Peter Gabriel') and not a preposition ('a friend of Gabriel')"""
    pre = re.split(r'[,;:：]', pre)[-1]
    pre = re.split(r'\s(?:and|&|und|y|et)\s', pre)[-1]
    toks = re.findall(r"[A-Za-zÀ-ÿ0-9'’.\-]+", pre)
    while toks and toks[-1].lower().strip('.') == 'jesse':
        toks.pop()                                       # "Assemblymember Jesse Gabriel"
    if not toks:
        return True
    low = [t.lower().strip('.').replace('’', "'") for t in toks]
    if re.search(r'(?:statement|letter|release|op-ed|remarks|post)\s+(?:from|by)$', ' '.join(low)):
        return True                                      # "a statement from Gabriel said" (his own, not his office)
    if low[-1] in _Q_PREP_BEFORE or any(w in ('said', 'says', 'told', 'wrote', 'asked', 'according') for w in low):
        return False
    t = toks[-1]
    if len(toks) > 1 and t[:1].isupper() and low[-1] not in _Q_TFINAL and not re.search(r'\d|^[A-Z]{1,4}\.?$|^[A-Z]-', t):
        return False                                     # a capitalised word that is not a title right before the name: another person
    return True


def _q_unit_split(p):
    """sentences of one paragraph, without splitting inside quotation marks or after common abbreviations"""
    out, start, inq, n = [], 0, False, len(p)
    for i, ch in enumerate(p):
        if ch in '“„«「『':
            inq = True
        elif ch in '”»」』':
            inq = False
        elif ch == '"' and not (0 < i < len(p) - 1 and '\u0590' <= p[i - 1] <= '\u05ff' and '\u0590' <= p[i + 1] <= '\u05ff'):
            inq = not inq
        elif ch in '.!?。！？' and not inq:
            nxt = p[i + 1:i + 3]
            if ch in '。！？' or (nxt[:1].isspace() and re.match(r'\s+[A-Z“"(\[‘«„À-Ý]', p[i + 1:i + 3] + 'X')):
                if ch == '.' and _Q_ABBR.search(p[max(0, i - 8):i + 1]):
                    continue
                out.append(p[start:i + 1]); start = i + 1
    if p[start:].strip():
        out.append(p[start:])
    return out


def _q_after(seg, G):
    """who owns a quote, read from the text after it: True him, False someone else, None unknown (pronoun, no verb)"""
    s = re.sub(r'^[\s,;]*(?:[-—–]\s*)?', '', seg[:160])
    s = re.sub(r'\b(Mr|Mrs|Ms|Dr|Sen|Rep|Gov|Asm|Assemb|Lt|Gen|Sgt|St|Jr|Sr)\.', r'\1', s)    # LOOSEENDS-v1: "Mr. Gabriel said" is one clause
    s = re.split(r'[.!?。]\s|[“"„«「『]', s)[0]
    m = re.match(r'(?:according\s+to|per|según|selon|laut)\s+(.{0,80})', s, re.I)
    if m:
        np = m.group(1)
        hs = _q_him(np, G)
        if hs and _q_prefix_ok(np[:hs[0][0]]) and not re.search(r'(?:office|spokes|staff|aide|press|statement\s+from)', np[:hs[0][0]], re.I):
            return True
        return False if re.match(r'[A-Z]', np) else None
    # signature: "..." Assemblymember Jesse Gabriel (D-Encino), Chair of the Assembly Budget Committee and author of ACA 20.
    hs0 = _q_him(s[:80], G)
    if hs0 and not _Q_VERB.search(s) and _q_prefix_ok(s[:hs0[0][0]]) and len(s) < 160:
        tail = re.sub(r'[()\-,.:;\d]', ' ', s[hs0[0][1]:]).split()
        if all(w[:1].isupper() or w.lower() in ('of', 'the', 'and', 'for', 'in', 'a', 'an', 'on', 'to', 'author', 'chair', 'chairman', 'vice', 'member', 'sponsor', 'co-author', 'coauthor', 'at', 'from') for w in tail):
            return True
    # speaker first: "Gabriel said", "Assemblymember Jesse Gabriel, D-Encino, said
    m = re.match(r'(?P<np>[^;]{1,110}?)[\s,]*(?:%s)' % _Q_VERB.pattern, s, re.I)
    if m:
        np = m.group('np')
        hs = _q_him(np, G)
        v = _Q_VERB.search(s, len(np))
        if hs and _q_prefix_ok(np[:hs[0][0]]) and not re.search(r'(?:%s)' % _Q_VERB_SAID.pattern, np[:hs[0][0]]):
            return True
        if re.match(r'(?:he|she|they|it|I|we)\b', np.strip(), re.I) or not np.strip():
            return None
        if np.strip()[:1].islower() and not re.search(r'[A-Z]', np) and len(np) > 8 and not _Q_CJK.search(np):
            s2 = s[len(np):].lstrip(' ,')                 # "..." such as housing and climate change, said Gabriel
            m2 = re.match(r'(?:%s)\s+(?P<np>[^.;]{1,90})' % _Q_VERB.pattern, s2, re.I)
            if m2:
                n2 = re.split(r'\b(?:to|of|about|at|on|in|during|after|when|while|as|with|for|before|against|from|that)\b', m2.group('np'))[0]
                h2 = _q_him(n2, G)
                if h2 and _q_prefix_ok(n2[:h2[0][0]]):
                    return True
        if len(np.strip()) <= 8 and not np.strip()[:1].isupper() and _Q_CJK.search(seg):
            return 'V'                                   # CJK / Korean: a quote particle + verb, the subject stated before the quote
        if np.strip()[:1].isupper() and (_Q_VERB_SAID.search(s) or (v and _Q_VERB.match(s[v.start():]))):
            return False                                 # a named (capitalised) subject of the said-verb that is not him
    # verb first: "said Gabriel", "said Assemblymember Jesse Gabriel (D-Encino)"
    m = re.match(r'(?:%s)\s+(?P<np>[^.;]{1,90})' % _Q_VERB.pattern, s, re.I)
    if m:
        np = m.group('np')
        np = re.split(r'\b(?:to|of|about|at|on|in|during|after|when|while|as|with|for|before|against|from|that)\b', np)[0]
        hs = _q_him(np, G)
        if hs and _q_prefix_ok(np[:hs[0][0]]) and not re.match(r'\s*told\b', s, re.I):
            return True
        if np.strip() and not re.match(r'(?:he|she|they|it)\b', np.strip(), re.I) and re.match(r'(?:said|says|wrote|added|noted|stated|explained|argued)\b', s, re.I):
            return False
    return None


def _q_before(seg, G, nw=9):
    """does the text before the quote make him the speaker (his name ... said-verb ... quote, or 'Gabriel:')"""
    seg = seg[-260:]
    for a, b in reversed(_q_him(seg, G)):
        rest = seg[b:]
        if re.search(r'(?:according\s+to|per|según|selon|laut)\s+(?:[A-Za-z.]+\s+){0,4}$', seg[:a], re.I) and re.match(r'[^.;]{0,60}[,:]?\s*$', rest) \
                and not re.search(r'office|spokes|staff|aide|press|statement\s+from', seg[:a], re.I):
            return True
        if not _q_prefix_ok(seg[:a]):
            continue
        if re.match(r'[’\']s\b', rest) and not re.match(r'[’\']s\s+(?:statement|letter|post|tweet|message|op-ed|remarks|comments|words)', rest, re.I):
            continue
        if re.search(r'[“"„«「『]', rest):
            continue
        if re.match(r'[^.;]{0,120}?[:：—–-]\s*$', rest) and not _Q_VERB_SAID.search(rest.split(':')[0] if ':' in rest else ''):
            return True                                  # "Gabriel (D-Encino), co-founder of the group: "
        m = re.match(r'(?P<mid>[^.;:：]{0,230}?)(?:[\s,]|^)(?P<v>%s)(?P<st>[^.;]{0,%d})$' % (_Q_VERB.pattern, 150 if nw >= 4 else 50), rest, re.I | re.S)
        if m and not re.search(r'[“"„«「『”»」』]', m.group('mid')):
            st = m.group('st')
            if len(_Q_VERB.findall(st)) == 0 and not re.search(r'\b(?:he|she|they)\s+(?:said|told|says)', st):
                if not re.search(r'(?<![A-Za-zÀ-ÿ])(?:said|says|told|wrote|added|noted|stated)\b', m.group('mid'), re.I):
                    return True
    return False


def _q_unwrap(text):
    """print-OCR texts break every line at a column width (and hyphenate): join the lines of such a text back into running prose"""
    lines = [x for x in text.split('\n') if x.strip()]
    if len(lines) < 15 or sum(1 for x in lines if len(x) < 48) < 0.6 * len(lines):
        return text
    t = re.sub(r'([A-Za-zÀ-ÿ])-\n(?=[a-zà-ÿ])', r'\1', text)
    return re.sub(r'\n+', ' ', t)


def _q_real_span(inner):
    nw = _q_words(inner)
    if nw < 1 or (nw < 2 and not (inner.strip()[:1].islower() and len(inner.strip()) >= 4)):
        return False
    # scare quotes / titles: a short Title Case span with no sentence punctuation inside is a name, not speech
    ws = inner.strip().split()
    if len(ws) <= 6 and ws and all(w[:1].isupper() or w.lower() in ('of', 'the', 'and', 'for', 'to', 'a', 'in', 'on') for w in ws) \
            and not re.search(r'[,.!?]\s*$', inner.strip()) and not re.search(r'[.!?;]', inner[:-1]):
        return False
    return True


_Q_HE = re.compile(r'^[\s,;]*(?:[-—–]\s*)?he\s+(?:%s)\b' % _Q_SPEECH_EN.replace('called|calls|described|describes|dubbed|labeled|labelled|characterized|characterised|', ''), re.I)


_Q_THEY = re.compile(r'^[\s,;]*(?:[-—–]\s*)?they\s+(?:%s)\b' % _Q_SPEECH_EN.replace('called|calls|described|describes|dubbed|labeled|labelled|characterized|characterised|', ''), re.I)


_Q_HEHEAD = re.compile(r'^\s*(?:(?:But|And|Still|Yet|However|Now|Instead|Then)[,]?\s+)?He\s+(?:%s)\b' % _Q_SPEECH_EN, re.I)


def _q_continues(sent, spans, G, intro):
    """a quote with no named speaker of its own ("..." he said / no attribution at all) in the sentence right after one where
    he is the subject of a said-verb: still his words. `intro` = the previous sentence(s) make him the speaker."""
    if not intro:
        return False
    for k, (a, b, inner) in enumerate(spans):
        if intro in ('subject', 'subjectS'):             # previous sentence has him as its subject: only an explicit "He argued ..." continues
            # LOOSEENDS-v1: or the quote closes on "he said" ("..." he said.) - a pronoun attribution right after a sentence about him alone
            nxt0 = spans[k + 1][0] if k + 1 < len(spans) else len(sent)
            if intro == 'subjectS' and _q_real_span(inner) and _q_words(inner) >= 3 and _Q_HE.match(sent[b:nxt0]) and not sent[:a].strip():
                return True
            if not (_q_real_span(inner) and _Q_HEHEAD.match(sent[:a] if k == 0 else sent[:spans[0][0]])):
                continue
            return True
        if not _q_real_span(inner) or _q_words(inner) < 3:
            continue
        nxt_start = spans[k + 1][0] if k + 1 < len(spans) else len(sent)
        tail = sent[b:nxt_start]
        head = sent[(spans[k - 1][1] if k else 0):a]
        rest = (_Q_DATE.sub(' ', head) + ' ' + tail)       # LOOSEENDS-v1: a date line before a pull quote is not a speaker's name
        if re.search(r'(?<![A-Za-z])(?:she|%swe|I|it)\s+(?:%s)\b' % ('' if intro == 'saidJ' else 'they|', _Q_SPEECH_EN), rest, re.I):
            continue
        if re.search(r'(?<![A-Za-z])[A-Z][A-Za-zÀ-ÿ\'’-]+', re.sub(r'^\W+', '', rest)[1:]) and not _Q_HE.match(tail):
            continue                                     # a capitalised name in the attribution: someone else's quote
        if G.search(rest) and not _q_him(rest, G):
            continue
        if _Q_VERB_SAID.search(rest) and not (_Q_HE.match(tail) or (intro == 'saidJ' and _Q_THEY.match(tail)) or _q_before(head, G)):
            continue
        return True
    return False


_Q_DATE = re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:,?\s+\d{4})?|\b\d{4}\b')


_Q_SUBJ_OK = set('assemblymember assemblyman assemblywoman assembly member budget chair chairman chairwoman committee rep sen senator democratic democrat jesse state california mr dr asm d r'.split())


def _q_subject_prefix(pre):
    """LOOSEENDS-v1: what stands before his name (after the last comma) is only a title - he is the subject of the sentence, not
    'the bill by Gabriel'"""
    last = re.split(r'[,;:：]', pre)[-1]
    toks = [t.lower().strip('.') for t in re.findall(r"[A-Za-zÀ-ÿ.\-]+", last)]
    return all(t in _Q_SUBJ_OK for t in toks)


def _q_join(text):
    """LOOSEENDS-v1: a line wrap that falls between paragraphs. A paragraph that starts in lower case continues the one before
    ("...taxpayers,"\n\nsaid Assemblymember ..."), a quote closing on a comma ("...Brown,"\n\nAssemblyman Jesse Gabriel noted ...) and a
    paragraph ending on a bare said-verb ("..., said\n\nAssemblyman Jesse Gabriel") are one sentence."""
    # a closing mark typed as a straight/single quote right before the speaker ("...effective,' Gabriel said.")
    text = re.sub(r"([,.!?])[’'](\s+(?:[A-Z][\w.'\-]*\s+){0,4}[A-Z][\w.'\-]*\s+(?:said|says|told|wrote|added|noted)\b)", r'\1”\2', text) \
        if '“' in text else text
    text = re.sub(r"(?<![\w])‘(?=[A-Z])([^‘’“”]{20,700}?”)", r'“\1', text)       # ‘When my community ...," Gabriel said.
    text = re.sub(r'“‘([^“”]{20,900}?[.!?,]’)\s*”', r'‘\1', text)                   # a block quote that opens “‘ ... ’”: the inner marks are the quote
    if '\n' not in text:
        return text
    paras = [x.strip() for x in re.split(r'\n+', text) if x.strip()]
    out = []
    for p in paras:
        if out:
            prev = out[-1]
            if ((p[:1].islower() or p[:1] in ',;)') and not re.search(r'[:：]$', prev)) or re.search(r'[,，][”"’»」]\s*$', prev) \
                    or re.search(r'(?<![A-Za-z])(?:said|says|told|wrote|added|noted|stated|explained)\s*$', prev, re.I):
                out[-1] = prev + ' ' + p
                continue
        out.append(p)
    return '\n'.join(out)


_Q_XV = (r'said|says|told|wrote|writes|added|adds|noted|notes|stated|states|explained|explains|argued|argues|clarified|clarifies|reasoned|reasons|'
         r'emphasized|emphasised|emphasizes|stressed|stresses|declared|declares|insisted|insists|cautioned|cautions|warned|warns|observed|observes|'
         r'remarked|remarks|commented|comments|acknowledged|acknowledges|asserted|asserts|contended|contends|maintained|maintains|suggested|suggests|'
         r'announced|announces|continued|continues|concluded|concludes|reiterated|reiterates|cited|saying|stating|adding|noting|writing|explaining|'
         r'arguing|telling')
_Q_XV_RX = re.compile(r'(?<![A-Za-zÀ-ÿ])(?:%s)(?![A-Za-zÀ-ÿ])' % _Q_XV, re.I)
_Q_XSTRONG = re.compile(r'(?<![A-Za-zÀ-ÿ])(?:said|says|told|tells)(?![A-Za-zÀ-ÿ])', re.I)
_Q_XMEDIUM = re.compile(r'(?:wrote|writes|stated|states|noted|notes|explained|explains|argued|argues|added|adds|reasoned|reasons|clarified|clarifies)$', re.I)
_Q_NAMING = re.compile(r'(?:known\s+as|called|dubbed|termed|labeled|labelled|nicknamed|so-called|named|titled|the\s+term|the\s+phrase|the\s+word)\s+(?:the\s+|a\s+|an\s+)?$', re.I)
_Q_XBLOCK = re.compile(r'\b(?:by|against|about|criticiz\w*|criticis\w*|accus\w*|slamm\w*|blast\w*)\b', re.I)


_Q_NOTHIM_PRE = re.compile(r'(?:(?:office|staff|spokes\w*|aides?|team|press\s+secretary)\s+(?:of|for|to)\s+(?:[A-Za-z.\-]+\s+){0,4}$|\b(?:letter|email|e-mail|message|memo|petition|appeal|thank\s+you)\s*,?\s+to\s+.*$)', re.I)
_Q_XGROUP = re.compile(r'\b(?:members|supporters|opponents|critics|advocates|residents|officials|leaders|groups|organizations|coalition|delegation)\b(?:\s+of\b[^,;]*)?[\s,\'’]*$', re.I)


def _q_xskip(sent, a):
    """LOOSEENDS-v1: this mention of his name cannot be the speaker - it sits inside an open quotation, or he is the addressee of a
    letter / the office speaking / one name in a list of recipients"""
    pre = sent[:a]
    if pre.count('“') > pre.count('”') or pre.count('"') % 2 == 1:
        return True
    return bool(_Q_NOTHIM_PRE.search(pre[-220:]))


def _q_nodot(s):
    """abbreviation and date dots removed ('Jan. 1, 2025', 'U.S.', 'Mr.') so that a '. ' test finds real sentence ends only"""
    s = re.sub(r'\b(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|Mr|Mrs|Ms|Dr|Sen|Rep|Gov|Asm|Assemb|Lt|Gen|Sgt|St|Jr|Sr|Inc|Co|Corp|No|vs)\.', lambda m: m.group(0)[:-1], s)
    return re.sub(r'\b([A-Z])\.(?=\s?[A-Z]\b)', r'\1', s)


def _q_subject_verb(sent, G, strong=True):
    """LOOSEENDS-v1: he is the (co-)subject of a speech verb in `sent` - his name, then (a relative clause, a coordinated speaker, a
    parenthetical) and the verb, with no quote mark, semicolon, sentence end or other said-verb between. -> end index of the verb
    (in sent) of the first such reading, or -1"""
    for a, b in _q_him(sent, G):
        if not _q_prefix_ok(sent[:a]) or re.match(r'[’\']s\b', sent[b:]) or _q_xskip(sent, a):
            continue
        tail = sent[b:]
        for vm in _Q_XV_RX.finditer(tail):
            if vm.start() > 240:
                break
            if strong and not _Q_XSTRONG.match(vm.group(0)) and not _Q_XMEDIUM.match(vm.group(0)):
                continue
            gap1 = tail[:vm.start()]
            if _Q_XGROUP.search(gap1):
                continue
            if re.search(r'[“"„«「『”»」』;]', gap1) or _Q_XSTRONG.search(gap1) or _Q_XBLOCK.search(gap1) or re.search(r'[.!?]\s', _q_nodot(gap1)):
                continue
            toks = re.findall(r"[A-Za-zÀ-ÿ0-9'’.\-]+", gap1)
            if toks and toks[-1][:1].isupper() and toks[-1].lower().strip('.') not in _Q_TFINAL | {'democrats', 'republicans', 'lawmakers', 'legislators'} \
                    and not re.search(r'\d|^[A-Z]{1,4}\.?$|^[A-Z]-', toks[-1]):
                # a named person right before the verb: only a coordinated speaker ("Gabriel and Speaker Rivas said")
                if not re.fullmatch(r'(?:\s*\([^)]*\))?[\s,]*(?:and|&)\s+[^,;]{1,60}', gap1):
                    continue
            return b + vm.end()
    return -1


# 'said some Jewish delegates "now believe ..."': the quote belongs to a group the sentence introduces (LOOSEENDS-v1 spot-check, 08604)
_Q_OTHERS = re.compile(r'\s*(?:that\s+)?(?:some|many|most|several|few|other|certain|these|those|all)\s+[\w\-]+(?:\s+[\w\-]+){0,3}\s*$', re.I)


def _q_extra(text, G, byline=''):
    """LOOSEENDS-v1 (DEPTHQ-v1 finding): quotes the strict scan misses. He is the subject of a speech verb and the quote sits in the
    same sentence AFTER the verb, as a said-attributed fragment or a full quote: 'Gabriel, who coauthored both bills, said the money
    would support "especially vulnerable Californians"', 'Gabriel said in a statement, "We are ..."', 'Wiener and Gabriel said in a
    joint statement that the budget called for "caution"', 'Gabriel told the Bee that the plan "sounds about right."'. Nothing else
    speaks between his name and the quote (no other speech verb, no other named subject of the verb, no semicolon or sentence end)."""
    text = _q_join(_q_unwrap(text or ''))
    if not text.strip() or not G.search(text) or _D_BYLINE.search(str(byline or '')):
        return False
    for para in (x for x in re.split(r'\n+', text) if x.strip()):
        for sent in _q_unit_split(para):
            if not G.search(sent) or not re.search(r'[“"„«「『‘]', sent):
                continue
            for a, b in _q_him(sent, G):
                if not _q_prefix_ok(sent[:a]) or re.match(r'[’\']s\b', sent[b:]) or _q_xskip(sent, a):
                    continue
                tail = sent[b:]
                for vm in _Q_XV_RX.finditer(tail):
                    if vm.start() > 240:
                        break
                    gap1 = tail[:vm.start()]
                    if _Q_XGROUP.search(gap1):
                        continue
                    if re.search(r'[“"„«「『”»」』;]', gap1) or _Q_XSTRONG.search(gap1) or _Q_XBLOCK.search(gap1) or re.search(r'[.!?]\s', _q_nodot(gap1)):
                        continue
                    toks = re.findall(r"[A-Za-zÀ-ÿ0-9'’.\-]+", gap1)
                    if toks and toks[-1][:1].isupper() and toks[-1].lower().strip('.') not in _Q_TFINAL | {'democrats', 'republicans', 'lawmakers', 'legislators'} \
                            and not re.search(r'\d|^[A-Z]{1,4}\.?$|^[A-Z]-', toks[-1]):
                        # a named person right before the verb: only a coordinated speaker ("Gabriel and Speaker Rivas said")
                        if not re.fullmatch(r'(?:\s*\([^)]*\))?[\s,]*(?:and|&)\s+[^,;]{1,60}', gap1):
                            continue
                    seg = tail[vm.end():]
                    for qa, qb, inner in _q_spans(seg):
                        if qa > 240:
                            break
                        gap2 = seg[:qa]
                        if not _q_real_span(inner) or _q_words(inner) < 2 or _Q_NAMING.search(gap2) or _Q_OTHERS.match(gap2):
                            continue
                        g2 = re.sub(r'(?<![A-Za-z])he\s+(?:%s)' % _Q_SPEECH_EN, ' ', gap2, flags=re.I)
                        g2 = re.sub(r'\b(?:be|been|being|was|were|is|are)\s+(?:%s)\b' % _Q_SPEECH_EN, ' ', g2, flags=re.I)      # passive: "to be posted by Jan. 1"
                        g2 = re.sub(r'(?<![A-Za-z])(?:saying|stating|adding|noting|explaining|arguing|writing|telling|emphasizing|stressing|warning)\b', ' ', g2, flags=re.I)
                        if re.search(r'[;“"„«「『]', gap2) or _Q_VERB.search(g2) or re.search(r'[.!?]\s', _q_nodot(gap2)) or re.search(r'[.!?]$', _q_nodot(gap2).strip()):
                            break
                        return True
    return False


def quoted_him(text, G, byline='', continuation=True):
    """True when Jesse Gabriel is directly quoted: his own words in quotation marks, attributed to him - "..." Gabriel said /
    Gabriel said, "..." / Gabriel: "..." / "..." according to Gabriel, with no other named speaker. With `continuation`, the
    quote that follows a sentence where he is the speaker and is attributed only by "he said" (or not at all) counts too.
    False for an op-ed he wrote (byline), no text, or a text that quotes only others."""
    return _quoted_scan(text, G, byline, continuation) is not None or _q_extra(text, G, byline)


def _quoted_scan(text, G, byline='', continuation=True):
    """None, 'direct' (a sentence naming him holds the quote) or 'continued' (the quote follows his said-sentence)"""
    text = _q_join(_q_unwrap(text or ''))
    if not text.strip() or not G.search(text) or _D_BYLINE.search(str(byline or '')):
        return None
    paras = [x for x in re.split(r'\n+', text) if x.strip()]
    sents = []                                           # (paragraph index, sentence)
    for pi, para in enumerate(paras):
        for sent in _q_unit_split(para):
            sents.append((pi, sent))
    cont = False
    for si, (pi, sent) in enumerate(sents):
        spans = _q_spans(sent)
        if G.search(sent) and spans:
            for k, (a, b, inner) in enumerate(spans):
                if not _q_real_span(inner):
                    continue
                prev_end = spans[k - 1][1] if k else 0
                nxt_start = spans[k + 1][0] if k + 1 < len(spans) else len(sent)
                after = _q_after(sent[b:nxt_start], G)
                if after is True:
                    return 'direct'
                if after is False:
                    continue
                if after == 'V' and _q_him(sent[:a], G):
                    return 'direct'
                if _q_before(sent[prev_end:a], G, _q_words(inner)):
                    return 'direct'
        # lead-in paragraph ending in a colon that names him, quote opening the next paragraph
        if spans and spans[0][0] == 0 and si and sents[si - 1][0] == pi - 1 and re.search(r'[:：]$', sents[si - 1][1].rstrip()) \
                and len(sents[si - 1][1]) < 260 and _q_before(sents[si - 1][1], G) and _q_words(spans[0][2]) >= 3:
            return 'direct'
        if continuation and spans and not cont:
            # his said-sentence within the two sentences before (this paragraph or the end of the one before), nothing else said between
            intro = False
            for back in (1, 2):
                if si - back < 0 or sents[si - back][0] < pi - 2:
                    break
                prev = sents[si - back][1]
                if G.search(prev) and (_q_before(prev.rstrip(' .:;') + ' ', G) or _q_subject_verb(prev, G) >= 0
                                       or re.search(r'\bGabriel\s+(?:spoke|speaks)\b', prev)):
                    intro = 'saidJ' if re.search(r'joint\s+(?:statement|letter|release)|\bGabriel\b[^.]{0,60}\s(?:and|&)\s|\s(?:and|&)\s[^.]{0,80}\bGabriel\b', prev) else 'said'
                    break
                hp = _q_him(prev[:90], G)
                if back == 1 and hp and _q_prefix_ok(prev[:hp[0][0]]) and not re.search(r'[“"„«「『]', prev[:hp[0][0]]):
                    intro = 'subjectS' if _q_subject_prefix(prev[:hp[0][0]]) else 'subject'; break
                if G.search(prev) or _Q_VERB_SAID.search(prev) or re.search(r'[“"„«「『]', prev):
                    break
            if intro and _q_continues(sent, spans, G, intro):
                cont = True
    return 'continued' if cont else None


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


# VERIFYTABS-v1: verify() covers every tab, not only Coverage / Originals / Removed
VT_DERIVED_REL = {'Has copies', 'Copies (rows)', 'First copy date (if different)', 'Related count', 'Related story IDs', 'In tracker',
                  'Tracker release ID 1', 'Tracker release ID 2', 'Coverage stories linked', 'Tracker date (earliest pickup)',
                  'Copy story ID 1', 'Copy story ID 2', 'Also on caucus site (date)', 'Also on caucus site (URL)'}   # recomputed from the copies / relmatch on every run
VT_KEYS = {'Audio & video details': ('Article ID',), 'Removed': ('Article ID',), PRINT_TAB: ('Article ID',), 'Press releases': ('Release ID', 'URL')}
VT_NEW_OK = {'Press releases', 'Audio & video details', 'Removed'}   # tabs a run may add rows to
VT_SKIP = {'Coverage', 'Originals'}                               # checked by verify() itself
VT_MAX = 50


def _vt_hyperlinks(path):
    """hyperlink count per sheet name, from the sheet XML (read-only openpyxl does not expose them)"""
    import zipfile
    out = {}
    try:
        z = zipfile.ZipFile(path)
        wbx = z.read('xl/workbook.xml').decode('utf-8', 'ignore')
        rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8', 'ignore')
        tgt = {}
        for m in re.finditer(r'<Relationship\b[^>]*>', rels):
            t = m.group(0)
            i, g = re.search(r'\bId="([^"]+)"', t), re.search(r'\bTarget="([^"]+)"', t)
            if i and g:
                tgt[i.group(1)] = g.group(1)
        for m in re.finditer(r'<sheet\b[^>]*>', wbx):
            t = m.group(0)
            n, r = re.search(r'\bname="([^"]*)"', t), re.search(r'\br:id="([^"]+)"', t)
            if not (n and r and r.group(1) in tgt):
                continue
            from html import unescape
            tp = tgt[r.group(1)].lstrip('/')
            tp = tp if tp.startswith('xl/') else 'xl/' + tp
            out[unescape(n.group(1))] = len(re.findall(rb'<hyperlink\b', z.read(tp)))
    except Exception as _e:
        out['__error__'] = repr(_e)[:120]
    return out


def _vt_read(path, skip):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=False)
    try:
        names, tabs = list(wb.sheetnames), {}
        for ws in wb.worksheets:
            if ws.title in skip:
                continue
            rows = ws.iter_rows(values_only=True)
            hdr = next(rows, ())
            hdr = list(hdr)
            while hdr and hdr[-1] in (None, ''):
                hdr.pop()
            tabs[ws.title] = (hdr, [list(r) for r in rows])
        return names, tabs
    finally:
        wb.close()


VT_NEW_TABS_OK = frozenset({'Audio & video details', 'Press releases', 'Removed'})


def verify_tabs(before_path, after_path, res):
    """VERIFYTABS-v1: every non-blank cell of every other tab is unchanged (fill-blanks-only), no tab or key row is lost, header rows are
    identical, hyperlinks do not drop. Allowed: new rows on Press releases / Audio & video details / Removed; the Press releases
    derived columns (VT_DERIVED_REL); rows of Audio & video details moved to Removed (res['removed'][*]['rows'][*]['aid'])."""
    problems, checked = [], []
    try:
        bn, bt = _vt_read(before_path, VT_SKIP)
        an, at = _vt_read(after_path, VT_SKIP)
    except Exception as _e:
        return [f'tabs unreadable: {_e!r}'[:200]], checked
    nb = [n for n in bn if n != 'Originals']
    na = [n for n in an if n != 'Originals']
    for n in bn:
        if n not in an:
            problems.append(f'sheet missing after: {n!r}')
    new_ok = {n for n in an if n not in bn and n in VT_NEW_TABS_OK}   # UPDFIX-v1: a run may create the tabs it owns on a workbook that lacks them (test_auto's fixture has no A/V tab)
    for n in an:
        if n not in bn and n not in new_ok:
            problems.append(f'sheet added: {n!r}')
    na = [n for n in na if n not in new_ok]
    if not problems and nb != na:
        problems.append(f'sheet order changed: {nb} -> {na}')
    removed_aids = {str(x.get('aid')) for e in (res or {}).get('removed', []) for x in e.get('rows', []) if x.get('aid')}
    yt_aids = {str(e.get('aid')) for e in (res or {}).get('yt_attached', [])}   # YTSTATION-v1: Item type of these AV rows becomes Broadcast segment
    for name, (bh, brows) in bt.items():
        if name not in at:
            continue
        ah, arows = at[name]
        checked.append(name)
        if bh != ah:
            problems.append(f'{name}: header row changed ({len(bh)} -> {len(ah)} columns)')
            continue
        hi = {h: i for i, h in enumerate(bh) if h not in (None, '')}
        kcols = VT_KEYS.get(name)
        kc = [hi[k] for k in (kcols or ()) if k in hi][:1] if name == 'Press releases' else [hi[k] for k in (kcols or ()) if k in hi]
        if not kc:   # tabs without a named key (Bills): the first four columns together; duplicates are numbered in order
            kc = list(range(min(4, len(bh))))

        def keyed(rows):
            seen, out = {}, {}
            for r in rows:
                k = tuple(norm_val(r[i]) if i < len(r) else '' for i in kc)
                if name == 'Press releases' and not k[0]:   # Release ID else URL
                    ui = hi.get('URL')
                    k = (norm_val(r[ui]) if ui is not None and ui < len(r) else '',)
                if not any(k):
                    continue
                n = seen.get(k, 0)
                seen[k] = n + 1
                out[k + (n,)] = r
            return out
        bk, ak = keyed(brows), keyed(arows)
        derived = VT_DERIVED_REL if name == 'Press releases' else set()
        for k, br in bk.items():
            ar = ak.get(k)
            lab = '/'.join(x for x in k[:-1] if x)[:40]
            if ar is None:
                if name == 'Audio & video details' and k[0] in removed_aids:
                    continue
                problems.append(f'{name}: row missing after: {lab}')
                continue
            for c, h in enumerate(bh):
                if h in (None, '') or h in derived:
                    continue
                bv = norm_val(br[c]) if c < len(br) else ''
                if not bv:
                    continue
                av = norm_val(ar[c]) if c < len(ar) else ''
                if bv != av:
                    if name == 'Audio & video details' and h == 'Item type' and k[0] in yt_aids and av == 'Broadcast segment':
                        continue
                    problems.append(f'{name} / {lab} / {h}: {bv[:50]!r} -> {av[:50]!r}')
        extra = [k for k in ak if k not in bk]
        if extra and name not in VT_NEW_OK:
            problems.append(f'{name}: {len(extra)} new rows (this tab is not written by the run): {[("/".join(x for x in k[:-1] if x))[:30] for k in extra[:3]]}')
    hb, ha = _vt_hyperlinks(before_path), _vt_hyperlinks(after_path)
    for n in bn:
        if n in hb and n in ha and ha[n] < hb[n] and n != '__error__':
            problems.append(f'{n}: hyperlinks dropped {hb[n]} -> {ha[n]}')
    return problems, checked


def verify(before_path, after_path, res):
    import pandas as pd
    b = pd.read_excel(before_path, sheet_name='Coverage', dtype=object)
    a = pd.read_excel(after_path, sheet_name='Coverage', dtype=object)
    problems = []
    if list(a.columns[:len(b.columns)]) != list(b.columns):
        problems.append('column order changed')
    a_idx = a.set_index('Article ID')
    allowed = {(sid, '# of reprints') for sid in res['reprint_counts']}
    swapped = {(aid, col) for e in res.get('origin_swaps', []) for aid, col in e.get('cells', [])}   # REPRINT-v2: the old Original's cells
    swapped |= {(x['aid'], col) for x in res.get('retry_cleared', []) for col in ('File name', 'Saved Copy?')}   # AUDIT F5
    swapped |= {(str(aid), col) for e in res.get('queue_applied', []) for aid, col in e.get('cells', [])}   # QUEUEAPPLY-v1: merged rows
    swapped |= {(str(e['aid']), col) for e in res.get('yt_attached', []) for col in e.get('cells', [])}   # YTSTATION-v1: Format / Medium of a story that became a broadcast story
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
            if (row.get('Story ID'), c) in allowed or (str(aid), c) in swapped:
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
    osid = co['Story ID'].dropna().astype(str)   # AUDIT F3: one Original per story
    dup_o = osid[osid.duplicated()]
    if len(dup_o):
        problems.append(f'stories with more than one Original row: {sorted(set(dup_o))[:5]}')
    try:   # AUDIT F1: numbers on the Removed tab are never reused
        rm_all = pd.read_excel(after_path, sheet_name='Removed', dtype=object)
        rm_ids = set(pd.concat([rm_all['Article ID'], rm_all.get('Print Article ID', pd.Series(dtype=object))]).dropna().astype(str)) - removed
        # COLDSTART-F1 (2026-10-30): a Removed number that is ALREADY in the before workbook (e.g. the Print Article ID of a folded
        # Web+Print row) is not a reuse by this run; only numbers this run introduced can clash
        old_ids = set(pd.concat([b['Article ID'], b.get('Print Article ID', pd.Series(dtype=object))]).dropna().astype(str))
        clash = sorted((rm_ids & set(ids)) - old_ids)
        if clash:
            problems.append(f'Article IDs reused from the Removed tab: {clash[:5]}')
    except Exception:
        pass
    tp, tabs_checked = verify_tabs(before_path, after_path, res)   # VERIFYTABS-v1
    problems += tp
    return {'ok': not problems, 'problems': problems[:VT_MAX], 'rows_before': len(b), 'rows_after': len(a),
            'originals': len(o), 'tabs_checked': tabs_checked}


def sheet_applied(sheet):
    """REQ-9 (UPDFIX-v1): a `sheet` result closes its run only when it records a successful write. `written: true` closes it, `written: false`
    never does; a legacy `sheet` with `at` and no `written` key closes it unless its line starts with "Not written". A failed attempt
    (workbook open in Excel, lock held, verify failed) therefore leaves the run's rows queued for the next save."""
    sheet = sheet or {}
    if not sheet.get('at'):
        return False
    if 'written' in sheet:
        return sheet.get('written') is True
    return not str(sheet.get('line') or '').strip().lower().startswith('not written')


def run_done(run):
    """BUTTONOPT-v1 (S1): a run was applied when it has ids or a successful sheet result (a run whose rows were all skipped keeps ids {}).
    REQ-9: a sheet result with written:false (or a legacy "Not written" line) does not count."""
    run = run or {}
    return bool(run.get('ids')) or sheet_applied(run.get('sheet'))


def has_work(db):
    """TOKENS-v1: anything for the sheet task to write? (runs not yet applied, bills from the Update button, edits not yet
    reported, hand-added reprints not yet written, pages waiting). No -> the run stops before staging the workbook.
    BUTTONOPT-v1 (S1): applied = ids or a sheet line; an edit already reported (reported >= at) is not work."""
    runs = (db.get('runs') or {}).values()
    why = {'runs': sum(1 for r in runs if (r or {}).get('rows') and not run_done(r)),
           'bills': sum(1 for r in runs if (r or {}).get('bills_new') and not sheet_applied((r or {}).get('sheet'))),
           'releases': sum(1 for r in runs if (r or {}).get('releases_new') and not sheet_applied((r or {}).get('sheet'))),   # RELCHECK-v1
           'edits': sum(1 for e in (db.get('edits') or {}).values() if (e or {}).get('removed') or not ((e or {}).get('reported') and str(e['reported']) >= str((e or {}).get('at') or ''))),
           'reprints': sum(1 for d in (db.get('reprints') or {}).values() if not (d or {}).get('aid')),
           'pages': 0}
    # PAGESORPHAN-v1: a pages doc is work only when an undone run (or a hand-added reprint not yet written) still points at it. An og-/rp- doc
    # whose run was applied, or whose candidate was never used, is not deleted by step 5 unless listed in result.pages_drop, so one orphan used to
    # make every later run stage the workbook, write nothing and republish. Orphans are counted in why['pages_orphan'] and are not work.
    pages = db.get('pages') or {}
    refs = set()
    for r in (db.get('runs') or {}).values():
        r = r or {}
        if run_done(r):
            continue
        for o in r.get('rows') or []:
            if not isinstance(o, dict):
                continue
            for k in ('Article ID', 'Story ID', 'Tracker story code', '_page', '_ph_sid'):
                v = str(o.get(k) or '')
                if v:
                    refs.add(v)
                    refs.update(re.findall(r'jg-[0-9a-f]{6}', v.lower()))
            og = o.get('_origin')
            for c in (og.get('cands') or [] if isinstance(og, dict) else []):
                if isinstance(c, dict) and c.get('page'):
                    refs.add(str(c['page']))
    for rid, d in (db.get('reprints') or {}).items():
        if not (d or {}).get('aid'):
            refs.update({'rp-' + str(rid), str(rid), 'rp:' + str(rid), str((d or {}).get('_pageKey') or '')} - {''})   # the reprints doc may name its own pages doc (_pageKey)
    why['pages'] = sum(1 for k in pages if k in refs)
    why['pages_orphan'] = len(pages) - why['pages']
    return any(v for k, v in why.items() if k != 'pages_orphan'), why


def pacific_today():
    """AUDIT F9 (final-int): the run date on Sammy's calendar (America/Los_Angeles), not the cloud runner's UTC date"""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
    except Exception:
        return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=8)).date().isoformat()


def load_queue(qdir):
    """QUEUEAPPLY-v1: the review queue from ArtifactData `list` output (DIR/<collection>/<doc id>.json or DIR/<collection>.json):
    items (docs {"list": [item, ...]}), decisions (doc id = item id: {choice, by, note, at}), applied (doc id = item id)"""
    import os, glob
    def coll(c):
        out = {}
        for f in sorted(glob.glob(os.path.join(qdir, c, '*.json'))):
            try:
                out[os.path.basename(f)[:-5]] = json.load(open(f, encoding='utf-8'))
            except ValueError:
                pass
        f = os.path.join(qdir, c + '.json')
        if os.path.exists(f):
            x = json.load(open(f, encoding='utf-8'))
            if isinstance(x, dict) and isinstance(x.get('docs') or x.get('items'), list):
                x = x.get('docs') or x.get('items')
            if isinstance(x, list):
                x = {str(e.get('id') or e.get('doc_id')): (e.get('data') if isinstance(e.get('data'), dict) else e) for e in x if isinstance(e, dict)}
            out.update(x or {})
        return {k: (v.get('data') if isinstance(v, dict) and 'data' in v and 'choice' not in v and 'list' not in v else v) for k, v in out.items()}
    items = {}
    for doc in coll('items').values():
        for it in (doc or {}).get('list') or []:
            if isinstance(it, dict) and it.get('id'):
                items[it['id']] = it
    return items, coll('decisions'), set(coll('applied'))


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
        if sheet_applied((run or {}).get('sheet')):
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
    add(n('origin_wanted'), f"{n('origin_wanted')} stories whose reporter's employer is a central desk with no row (originator-add wanted, see review)")
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


def fetch_plan(res, cache, today=None):
    """LEARN-v1: before any web fetch the run asks the lookup cache. Returns {fetch: [url], answered: {url: reason}} over the URLs this
    run would still send to the web (retry pages and the headline-search targets of origin_wanted carry no URL, so only pages_error)."""
    urls = [str(e.get('url') or e.get('link') or '') for e in res.get('pages_error') or [] if (e.get('url') or e.get('link'))]
    if cache is None:
        return {'fetch': urls, 'answered': {}}
    go, done = cache.partition(urls, today)
    return {'fetch': go, 'answered': done}


def apply_lookups(db, cache, today=None):
    """LEARN-v1: confirmed lookups the Update page or an agent queued (run docs' `lookups`: [{url, settled, verdict, source, ...}])
    are appended to the cache. Returns the number of new entries."""
    n = 0
    if cache is None:
        return 0
    for doc in (db.get('runs') or {}).values():
        n += cache.merge_lookups((doc or {}).get('lookups') or [], today)
    return n


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
    ap.add_argument('--today', default=pacific_today(), help='run date, America/Los_Angeles (AUDIT F9, DATES-v1); the prompt passes it')
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
    ap.add_argument('--queue', help='QUEUEAPPLY-v1: review-queue ArtifactData list output folder (items/, decisions/, applied/ as <doc id>.json): decided items this task made are applied')
    ap.add_argument('--lookup-cache', help='LEARN-v1: lookup_cache.json (the pipeline copy); consulted before any web fetch (result.fetch_plan)')
    ap.add_argument('--lookup-cache-out', help='LEARN-v1: where to write the cache with this run\'s new confirmed lookups appended (default: no write)')
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
    if a.queue:
        task.queue = load_queue(a.queue)   # QUEUEAPPLY-v1
    if a.idmap:
        task.idmap = {str(k).lower(): v for k, v in json.load(open(a.idmap, encoding='utf-8')).items()}
    res = task.run(a.pages_dir)
    cache = LC.Cache.load(a.lookup_cache) if LC else None   # LEARN-v1
    res['fetch_plan'] = fetch_plan(res, cache, a.today)
    res['lookups_new'] = apply_lookups(db, cache, a.today)
    if cache is not None and a.lookup_cache_out and res['lookups_new']:
        cache.save(a.lookup_cache_out)
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
        'held', 'outlet_unresolved', 'removed', 'edits_reported', 'red_rows', 'av_date_review', 'origin_wanted')})
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
