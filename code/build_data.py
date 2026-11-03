"""T2: Coverage workbook -> tracker data blocks (see lib/CONTRACT.md).
Usage: python3 -I build_data.py COVERAGE.xlsx OLD_INDEX.html OUT_DIR [SID_MAP.json]
Works on the workbook before and after the ID migration (old nb-/pq-/ws- + jg-NNNNN, or new 5-digit + sNNNNN).
SID_MAP.json (optional, work/sid_map.json from make_id_map.py): legacy jg-NNNNN -> sNNNNN; entries whose number
changes (ids removed as duplicates) are added to idmap so old shared-store docs still find their story.
Writes OUT_DIR/data.json, rows.json, idmap.json, covcols.json and a build report.
OLD_INDEX.html supplies carried-over fields (src, added, prec, hl_en/text_en fallbacks) by old code.
"""
import sys, re, json, collections, os
import html as _html   # ENTITIES-v1
_hd = lambda v: _html.unescape(v) if '&' in v else v   # ENTITIES-v1: decode HTML entities in headlines
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I drops the script dir; authorsplit.py lives here
from authorsplit import parse_byline, author_kind

COV, OLDHTML, OUT = sys.argv[1:4]
SIDMAP = sys.argv[4] if len(sys.argv) > 4 else None

def old_records(path):
    h = open(path, encoding='utf-8').read()
    d = h.find('<script id="data"'); e = h.find('</script>', d)
    return {r['id']: r for r in json.loads(h[h.find('>', d) + 1:e])}

OLD = old_records(OLDHTML)
C_ALL = pd.read_excel(COV, sheet_name='Coverage', dtype=str).fillna('')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reprint_rule import hide_unverified   # HIDEUNVERIFIED-v1 (Sammy 2026-10-28): C = what the tracker shows; C_ALL = every row
C = hide_unverified(C_ALL)
covcols = list(C.columns)
# T30: Author 1..N + Author title (split of Author / byline). Rows not split yet (sheet task adds) are parsed here.
ACOLS = sorted([c for c in C.columns if re.fullmatch(r'Author \d+', c)], key=lambda c: int(c.split()[1]))
def authors_of(r, o):
    a = [str(r[c]).strip() for c in ACOLS if str(r[c]).strip()]
    if a: return a, str(r.get('Author title', '')).strip()
    b = str(r['Author / byline']).strip()
    if b: p = parse_byline(b, r['Outlet']); return p['authors'], p['title']
    old = o.get('author', '')                      # old tracker records keep "A; B"
    return [x.strip() for x in old.split(';') if x.strip()], ''

# ---- AUTHOR-CANON (agent-final-F4): same-person names from Sammy's review queue (author_canon.csv next to this file)
import csv as _csv
from authorsplit import author_key as _akey
CANON = {}
_cp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'author_canon.csv')
if os.path.exists(_cp):
    for _r in _csv.DictReader(open(_cp, encoding='utf-8')):
        for _k in _r['key'].split(' ~ '): CANON[_k.strip()] = _r['canonical'].strip()
        CANON[_akey(_r['canonical'])] = _r['canonical'].strip()
CANON_HITS = collections.Counter()
_authors_raw = authors_of
def authors_of(r, o):
    a, t = _authors_raw(r, o); out, seen = [], set()
    for x in a:
        c = CANON.get(_akey(x), x)
        if c != x: CANON_HITS[x + ' -> ' + c] += 1
        if _akey(c) in seen: continue
        seen.add(_akey(c)); out.append(c)
    return out, t
# ---- /AUTHOR-CANON
def s(v): return str(v).strip()
# ---- F7-v1: retired Reach label never output; Bills limited to Gabriel's leginfo list
RETIRED_REACH = {'Spanish-language & ethnic'}
def reach_ok(v):
    return '; '.join(t.strip() for t in str(v or '').split(';') if t.strip() and t.strip() not in RETIRED_REACH)
_BL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gabriel_bills_leginfo.json')
def _bnorm(b): return re.sub(r'\s+', ' ', str(b or '').upper().replace('.', '')).strip()
HIS_BILLS = {_bnorm(b.get('bill')) for b in json.load(open(_BL, encoding='utf-8')).get('rows', []) if b.get('bill')} if os.path.exists(_BL) else None
BILLS_DROPPED = collections.Counter()
def bills_ok(lst):
    if HIS_BILLS is None: return list(lst)
    out = [b for b in lst if _bnorm(b) in HIS_BILLS]
    for b in lst:
        if _bnorm(b) not in HIS_BILLS: BILLS_DROPPED[b] += 1
    return out
# ---- /F7-v1
def norm_hl(t): return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', s(t).lower().replace('’', "'"))).strip()
_MIRROR_LABEL = re.compile(r'^(?:qa\d+-web-vercel|amp|m|mobile|www\d+|edition|beta|staging|preview)\.')
def canon_mirror(u):   # REQ-14: same as sheet_task.canon_mirror
    m = re.match(r'^[^/]*\.cdn\.ampproject\.org/[cv]/s/(.*)$', u)
    if m: u = re.sub(r'^www\.', '', m.group(1))
    host, sl, rest = u.partition('/')
    h2 = _MIRROR_LABEL.sub('', host)
    if h2 != host and h2.count('.') >= 1: host = h2
    return host + sl + rest
def norm_url(u):
    u = s(u)
    if not u.startswith('http'): return ''
    u = canon_mirror(re.sub(r'^https?://(www\.)?', '', u.lower()).split('#')[0])
    host = u.split('/')[0]
    # NewsBank / proxy / Google links identify the article only in the query string: keep it
    # YTLINK-v1: a YouTube watch link identifies the video only in its query string (?v=ID): keep it
    if not re.search(r'newsbank|oclc|google\.|proquest|(^|\.)youtube\.com$|(^|\.)iranshahrnewsagency\.com$|(^|\.)chosundaily\.com$', host): u = u.split('?')[0]
    return u.rstrip('/')
def disp(o):  # NewsBank style "Sacramento Bee, The" -> "The Sacramento Bee" for display only
    o = s(o); m = re.match(r'^(.*), (The|La|El|Los|Las|Le|Les|Die|Der|Il)$', o)
    return f'{m.group(2)} {m.group(1)}' if m else o
def ca_county(r):
    st = s(r['Outlet state']); c = s(r['Outlet county'])
    return c if c and st in ('CA', '') else ''
def year(v):
    try: return int(float(v))
    except Exception: return None
def prec(d):
    d = s(d)
    return 'day' if re.match(r'^\d{4}-\d{2}-\d{2}$', d) else 'month' if re.match(r'^\d{4}-\d{2}$', d) else 'year' if d else 'day'

# ---- LINKS-v1 (agent-links): links the tracker lists, as [kind, url] pairs (DECISIONS 2026-10-27, final links scope).
# Listed: NewsBank / ProQuest through the California State Library (CSL) and the publisher's own link. Nothing else.
# CSL pattern: ProQuest  https://castatelib.idm.oclc.org/login?url=<ProQuest URL>   (sheet: "ProQuest via CA State Library")
#              NewsBank  https://infoweb-newsbank-com.castatelib.idm.oclc.org/<path>  (sheet: "... via CA State Library";
#              the same URL as infoweb.newsbank.com with the host swapped to the CSL proxy host)
# CSL_DERIVE: the sheet has no CSL column for "NewsBank article link" / "NewsBank print article link" (and a few rows may
# lack the CSL twin of a ProQuest / print-page link); True derives the CSL link with the same rewrite (100% of the sheet's
# existing CSL pairs follow it). False lists only CSL links written in the sheet.
CSL_DERIVE = True
CSL_PQ = 'https://castatelib.idm.oclc.org/login?url='
CSL_NB_HOST = 'infoweb-newsbank-com.castatelib.idm.oclc.org'
def csl_of(u):
    u = s(u)
    if not re.match(r'^https?://', u): return ''
    if re.match(r'^https?://castatelib\.idm\.oclc\.org/login\?url=https?://(www\.)?proquest\.com/', u) or \
       re.match(r'^https?://' + re.escape(CSL_NB_HOST) + '/', u): return u
    if not CSL_DERIVE: return ''
    if re.match(r'^https?://(www\.)?proquest\.com/', u): return CSL_PQ + u
    if re.match(r'^https?://infoweb\.newsbank\.com/', u): return re.sub(r'^https?://infoweb\.newsbank\.com/', 'https://' + CSL_NB_HOST + '/', u)
    return ''
# publisher link -> listed only when it is the outlet's own site
NOT_OWN_HOST = re.compile(r'(^|\.)(archive\.org|google\.[a-z.]+|github\.com|blob\.core\.windows\.net|tvmaze\.com|nalert\.blogspot\.com|'
                          r'nmreports\.org|oag\.ca\.gov|oclc\.org|newsbank\.com|proquest\.com)$')
AGGREGATOR = {'yahoo.com': 'yahoo', 'aol.com': 'aol', 'msn.com': 'msn', 'newsbreak.com': 'newsbreak', 'pressreader.com': 'pressreader'}
WIRE_OUTLET = re.compile(r'^(TCA (News Service|Regional News)|University Wire|U\.S\. Newswire|Contify\b|National Desk, The|California Black Media)')
NOT_OWN_PAIR = [  # (host suffix, outlet pattern): another outlet's site carrying this outlet's story
    ('abc30.com', 'Press Democrat'), ('cbsnews.com', 'Press Democrat'), ('aboluowang.com', 'Epoch Times'),
    ('clevelandjewishnews.com', 'American Israelite'), ('crbcnews.com', 'Just Food'), ('dailynews.com', 'Red Bluff'),
    ('eurweb.com', 'Oakland Post'), ('nnpa.org', '.'), ('foxnews.com', 'Charleston Gazette'), ('kpbs.org', 'CALmatters'),
    ('laist.com', 'CALmatters'), ('smdp.com', 'CALmatters'), ('ksl.com', 'Philadelphia Tribune'), ('kvia.com', '^CNN'),
    ('abc12.com', '^CNN'), ('lasentinel.net', 'Precinct Reporter'), ('sfgate.com', 'San Francisco Chronicle'),
    ('thesunreporter.com', 'Los Angeles Sentinel'), ('calonews.com', 'Calaveras'), ('eastbaytimes.com', 'Mercury News'),
    ('centerforhealthjournalism.org', 'San Francisco Public Press')]
LINK_SKIP = collections.Counter(); LINK_SKIP_ROWS = []
def url_host(u):
    m = re.match(r'^https?://([^/?#]+)', s(u)); return re.sub(r'^(www\d?|m|amp|mobile)\.', '', m.group(1).lower()) if m else ''
def own_link(u, outlet):
    h = url_host(u)
    if not h: return 'not a URL'
    if NOT_OWN_HOST.search(h): return 'not publisher: ' + NOT_OWN_HOST.search(h).group(2)
    for dom, name in AGGREGATOR.items():
        if (h == dom or h.endswith('.' + dom)) and name not in outlet.lower(): return 'aggregator: ' + dom
    if WIRE_OUTLET.search(outlet): return 'wire outlet, partner site'
    for dom, pat in NOT_OWN_PAIR:
        if (h == dom or h.endswith('.' + dom)) and re.search(pat, outlet): return 'another outlet\'s site'
    return ''
ARCHIVE_TV = re.compile(r'^https?://(www\.)?archive\.org/(details|embed)/[A-Za-z0-9-]+_\d{8}_\d{6}', re.I)  # LINKS-v2
def links_of(r):
    out, seen = [], set()
    def add(kind, u):
        if u and u not in seen: seen.add(u); out.append([kind, u])
    def skip(kind, u, why):
        LINK_SKIP[kind + ' | ' + why] += 1; LINK_SKIP_ROWS.append([r['Article ID'], r['Story ID'], r['Original or reprint'], s(r['Outlet']), kind, why, u])
    pu = s(r['Publisher link'])
    if pu and ARCHIVE_TV.match(pu): add('tv', pu)  # LINKS-v2: Internet Archive TV clip
    elif pu:
        why = own_link(pu, s(r['Outlet']))
        if why: skip('Publisher link', pu, why)
        else: add('pub', pu)
    for kind, col, csl_col in (('nb', 'NewsBank article link', None), ('nbpa', 'NewsBank print article link', None),
                               # LINKUI-v1: no NewsBank print-page (nbpg) links; the print edition (nbpa) stays
                               ('pq', 'ProQuest link', 'ProQuest via CA State Library')):
        raw = s(r[col]) if col in r else ''; sheet_csl = s(r[csl_col]) if csl_col and csl_col in r else ''
        u = csl_of(sheet_csl) or csl_of(raw)
        if u:
            add(kind, u)
            if not sheet_csl: LINK_SKIP[col + ' | listed as derived CSL link'] += 1
        elif raw: skip(col, raw, 'not via CA State Library')
        elif sheet_csl: skip(csl_col, sheet_csl, 'unrecognised CSL URL')
    return out
# ---- /LINKS-v1

# Press releases (DECISIONS 2026-10-27; spec work/out/press_release_build.md, applied in T14a): rows with
# 'Press release' = 'Yes' are left out of the tracker, as entries and as reprints. They stay in the rows index.
PR = 'Press release'
def is_pr(r): return PR in C.columns and s(r[PR]).lower() == 'yes'
data = []; report = collections.Counter(); pr_reps_by_sid = collections.Counter()
reps = collections.defaultdict(list)
for _, r in C[C['Original or reprint'] == 'Reprint'].iterrows():
    if is_pr(r): report['pr_reprints_dropped'] += 1; pr_reps_by_sid[r['Story ID']] += 1; continue
    reps[r['Story ID']].append({
        'aid': r['Article ID'], 'outlet': disp(r['Outlet']), 'date': s(r['Date']),
        'county': ca_county(r), 'state': s(r['Outlet state']),
        'link': s(r['Publisher link']) or s(r['NewsBank article link']),
        'hl': _hd(s(r['Headline'])), 'src': s(r['Data Source']), 'lk': links_of(r)})  # LINKS-v1 + ENTITIES-v1
    if 'Mention depth' in C.columns: reps[r['Story ID']][-1]['depth'] = s(r['Mention depth'])   # INCL-v1 (CONTRACT "Mention depth")
    if 'Quoted' in C.columns: reps[r['Story ID']][-1]['quoted'] = s(r['Quoted'])   # QUOTED-v1
    if 'Format' in C.columns: reps[r['Story ID']][-1]['fmt'] = s(r['Format'])   # FORMAT-v1: Article | Broadcast segment | Video clip | Audio segment | Podcast episode | Print
for k in reps: reps[k].sort(key=lambda x: (x['date'] or '9999', x['outlet'].lower()))

SRC = {'Newsbank': 'NewsBank', 'ProQuest': 'ProQuest, full text', 'Tracker scrape': 'Web, verified',
       'Web search (TinyFish)': 'Web, verified', 'Tracker reprint list': 'Web, verified'}
for _, r in C[C['Original or reprint'] == 'Original'].iterrows():
    if is_pr(r): report['pr_originals_dropped'] += 1; continue
    codes = re.findall(r'jg-[0-9a-f]{6}', s(r['Tracker story code']))  # a cell can hold several codes
    code = next((c for c in codes if c in OLD), codes[0] if codes else ''); o = OLD.get(code, {})
    rs = reps.get(r['Story ID'], [])
    outs = []
    for x in rs:
        if x['outlet'] and x['outlet'] != disp(r['Outlet']) and x['outlet'] not in outs: outs.append(x['outlet'])
    lang = s(r['Language']); lang = '' if lang in ('', 'English') else lang
    tone = s(r['Tone']) or 'Not rated'
    rec = {
        'id': r['Story ID'], 'code': code, 'aid': r['Article ID'],
        # DATES-v1 (FINALCHECK-v1 D3): the sheet Date is the only date; a blank Date is undated (date '', prec 'year', year 0), never the legacy index's scrape date
        'date': s(r['Date']), 'prec': prec(r['Date']) if s(r['Date']) else 'year',   # v23 R4: the sheet Date's own precision
        'year': (year(r['Year']) or o.get('year') or int(s(r['Date'])[:4])) if s(r['Date']) else 0,
        'outlet': disp(r['Outlet']), 'pub': o.get('pub') or disp(r['Outlet']),
        # when release reprints were dropped, recount; otherwise trust the sheet's "# of reprints"
        'rep': len(outs) if pr_reps_by_sid.get(r['Story ID']) else (int(float(r['# of reprints'])) if s(r['# of reprints']) else len(outs)),
        'reps': rs, 'also': '; '.join(outs),
        'hl': _hd(s(r['Headline']) or o.get('hl', '')),   # ENTITIES-v1
        'link': s(r['Publisher link']) or s(r['NewsBank article link']) or o.get('link', ''),
        'plink': s(r['NewsBank article link']) or o.get('plink', ''),
        'lstat': s(r['Link status']) or o.get('lstat', ''),
        'pq': s(r['ProQuest link']) or o.get('pq', ''),
        'lk': links_of(r),  # LINKS-v1
        'topic': s(r['Topic']) or o.get('topic', ''), 'issue': s(r['Topic']) or o.get('issue', ''),
        'src': o.get('src') or SRC.get(s(r['Data Source']), s(r['Data Source'])),
        'media': s(r['Medium']) or o.get('media', ''), 'added': o.get('added', ''),
        'reach': reach_ok(s(r['Reach']) or o.get('reach', '')),  # F7-v1
        'role': s(r['Role']),   # FINALCHECK-v1 D1: the sheet is the only source (no legacy / default fallback); a blank is counted in report.role_blank
        'lang': lang,
        'bills': bills_ok([b.strip() for b in re.split(r'[;,]', s(r['Bills'])) if b.strip()]),  # F7-v1; V23-BILLS: the sheet is the only source (no legacy fallback: it resurrected 24 tags the tags review cleared)
        'author': s(r['Author / byline']) or o.get('author', ''),
        'authors': authors_of(r, o)[0], 'atitle': authors_of(r, o)[1],
        'akinds': [author_kind(x) for x in authors_of(r, o)[0]],   # person|board|staff|wire|org (tracker filter grouping)
        'tone': tone, 'twhy': s(r['Tone note']) or o.get('twhy', ''),
        'tauto': s(r['Tone rated by']).startswith('Claude') if s(r['Tone rated by']) else o.get('tauto', False),
        'county': ca_county(r) or o.get('county', ''),
        'rc': sorted({x['county'] for x in rs if x['county']}),
    }
    if 'Mention depth' in C.columns: rec['depth'] = s(r['Mention depth'])   # INCL-v1: the Original row's value ('' = blank)
    if 'Quoted' in C.columns: rec['quoted'] = s(r['Quoted'])   # QUOTED-v1: 'Yes' or '' (the Original row's value)
    if 'Format' in C.columns: rec['fmt'] = s(r['Format'])   # FORMAT-v1: the Original row's value ('' = blank); the tabs / charts roll it up with Medium (r.media)
    if s(r['Translated Headline']) or o.get('hl_en'): rec['hl_en'] = _hd(s(r['Translated Headline']) or o.get('hl_en', ''))   # ENTITIES-v1
    if s(r['Story in English']) or o.get('text_en'): rec['text_en'] = s(r['Story in English']) or o.get('text_en', '')
    data.append(rec)
    report['stories'] += 1; report['with_code'] += bool(code); report['with_reps'] += bool(rs)
# blanks the old tracker never had: topic -> 'Unassigned' (old tracker's own label);
# reach is an outlet property -> use the value every other story from that outlet agrees on
by_outlet = collections.defaultdict(set)
for x in data:
    if x['reach']: by_outlet[x['outlet']].add(x['reach'])
for x in data:
    if not x['topic']: x['topic'] = x['issue'] = 'Unassigned'
    if not x['reach']:
        v = by_outlet.get(x['outlet'], set())
        if len(v) == 1: x['reach'] = next(iter(v)); report['reach_from_outlet'] += 1
        else: report['reach_blank'] += 1
# FINALCHECK-v1 D2: counters recounted from the final data (the old ones counted only part of the fallbacks); with the sheet filled these are the cells still blank in the sheet
report['topic_unassigned'] = sum(1 for x in data if x['topic'] == 'Unassigned')
report['role_blank'] = sum(1 for x in data if not x['role'])
report['undated'] = sum(1 for x in data if not x['date'])
# WIREBLEND-v1 (coordinator 2026-10-29): a blended Original ("staff and wire reports", Team note "Uses wire copy of sNNNNN") stays
# its own story and counts toward the wire story's pickups (reps entry with blend: true; the Outlets tab skips it). wireblend.py next to this file.
try:
    import wireblend as _WB
    report['wire_blend_pickups'] = _WB.add_pickups(data, C)
except ImportError:
    pass
data.sort(key=lambda x: (x['date'] or '', x['id']), reverse=True)
# AVTAB-v1 build_data: "Audio & video details" tab (avtab.py next to this script) -> rec['av'] / reps[i]['av'] + block av.json
AVB = {'v': 1, 'cols': [], 'rows': {}}
try:
    import avtab as _AV
    AVB = _AV.block(COV)
except Exception as _e:
    report['av_error'] = repr(_e)[:200]
_AV_SKIP = {'sid', 'medium', 'from'}
def _av_of(aid):
    v = AVB['rows'].get(aid)
    return {k: x for k, x in zip(AVB['cols'], v) if x and k not in _AV_SKIP} if v else None
def _yt_link(rec):   # YTBROADCAST-v1: the AV tab's YouTube link joins the link list as ['yt', url], right after the publisher / archive link
    u = (rec.get('av') or {}).get('lyoutube', '')
    if not re.match(r'^https?://', u or ''): return
    same = [p for p in rec['lk'] if p[1] == u]
    if same:   # the Publisher link is already that YouTube URL (e.g. 10315): same link, drawn with the YouTube label
        for p in same: p[0] = 'yt'
        report['yt_links'] += 1
    else:
        i = max([k + 1 for k, p in enumerate(rec['lk']) if p[0] in ('pub', 'tv')] or [0]); rec['lk'].insert(i, ['yt', u]); report['yt_links'] += 1
for _x in data:
    _a = _av_of(_x['aid'])
    if _a: _x['av'] = _a; report['av_stories'] += 1; _yt_link(_x)
    for _rp in _x['reps']:
        _a = _av_of(_rp['aid'])
        if _a: _rp['av'] = _a; report['av_reprints'] += 1; _yt_link(_rp)
_hid = set(C_ALL['Article ID']) - set(C['Article ID'])   # HIDEUNVERIFIED-v1: no AV facts for hidden rows either
AVB['rows'] = {k: v for k, v in AVB['rows'].items() if k not in _hid}; report['unverified_hidden'] = len(C_ALL) - len(C)
report['av_tab_rows'] = len(AVB['rows'])

# PRINTTAB-v1: the "Unlinked print pages" tab (NewsBank print-page pointers moved off Coverage) joins the dedupe index and the
# next-number scan, so the Update button never re-adds one of its links or reuses one of its numbers; never shown as stories
try:
    P_UN = pd.read_excel(COV, sheet_name='Unlinked print pages', dtype=str).fillna('')
    for _c in ('Article ID', 'Print Article ID', 'Story ID', 'Original or reprint', 'Outlet', 'Date', 'Headline', 'Publisher link', 'NewsBank article link', 'ProQuest link'):
        if _c not in P_UN.columns: P_UN[_c] = ''
    report['print_tab_rows'] = len(P_UN)
except Exception:
    P_UN = pd.DataFrame(columns=['Article ID', 'Print Article ID', 'Story ID', 'Original or reprint', 'Outlet', 'Date', 'Headline', 'Publisher link', 'NewsBank article link', 'ProQuest link'])
# AUDIT F1/F2: the "Removed" tab joins the dedupe index (kind 'X': the Update button treats its links and headlines as rows the sheet
# has, so a removed story is never found and added again) and the next-number scan (its Article / Story IDs are never reused)
try:
    P_RM = pd.read_excel(COV, sheet_name='Removed', dtype=str).fillna('')
    for _c in ('Article ID', 'Print Article ID', 'Story ID', 'Original or reprint', 'Outlet', 'Date', 'Headline', 'Publisher link', 'NewsBank article link', 'ProQuest link'):
        if _c not in P_RM.columns: P_RM[_c] = ''
    report['removed_tab_rows'] = len(P_RM)
except Exception:
    P_RM = pd.DataFrame(columns=['Article ID', 'Print Article ID', 'Story ID', 'Original or reprint', 'Outlet', 'Date', 'Headline', 'Publisher link', 'NewsBank article link', 'ProQuest link'])
rows = []
_parts = [C_ALL] + [t[[c for c in t.columns if c in C_ALL.columns]] for t in (P_UN, P_RM) if len(t)]
for _, r in pd.concat(_parts, ignore_index=True).fillna('').iterrows():   # HIDEUNVERIFIED-v1: the dedupe index keeps unverified rows (kind '') so Update never re-adds them
    kind = {'Original': 'O', 'Reprint': 'R'}.get(r['Original or reprint'], '')
    if _ >= len(C_ALL) + (len(P_UN) if len(P_UN) else 0): kind = 'X'   # AUDIT F2: a Removed-tab row
    links = sorted({norm_url(r[c]) for c in ('Publisher link', 'NewsBank article link', 'ProQuest link') if norm_url(r[c])})
    rows.append([r['Article ID'], r['Story ID'], kind, s(r['Outlet']), s(r['Date']), norm_hl(r['Headline']), links])
# next free numbers. Old scheme: per prefix (ws/pq/nb) + jg. New scheme: one sequence over Article ID and
# Print Article ID ("aid") + Story ID ("s"); the Update button and sheet task use these.
nums = collections.defaultdict(int)
for a in list(C_ALL['Article ID']) + list(C_ALL['Print Article ID']) + list(P_UN['Article ID']) + list(P_UN['Print Article ID']) + list(P_RM['Article ID']) + list(P_RM['Print Article ID']):   # PRINTTAB-v1; AUDIT F1: Removed too
    m = re.match(r'^(?:(nb|ws|pq)-)?(\d{5})$', s(a))
    if m: nums[m.group(1) or 'aid'] = max(nums[m.group(1) or 'aid'], int(m.group(2)))
smax = collections.defaultdict(int)
for x in list(C_ALL['Story ID']) + list(P_RM['Story ID']):   # AUDIT F1: Removed too
    m = re.match(r'^(jg-|s)(\d{5})$', s(x))
    if m: smax[m.group(1)] = max(smax[m.group(1)], int(m.group(2)))
NEXT = {'aid': nums['aid'] + 1, 's': max(smax['s'], 4296) + 1} if nums['aid'] else \
       {'ws': nums['ws'] + 1, 'pq': nums['pq'] + 1, 'jg': smax['jg-'] + 1}

idmap = {}
for pref in ('Original', 'Reprint', ''):
    for _, r in C_ALL[C_ALL['Original or reprint'] == pref].iterrows() if pref else C_ALL.iterrows():
        for c in re.findall(r'jg-[0-9a-f]{6}', s(r['Tracker story code'])):
            if r['Story ID'] and c not in idmap: idmap[c] = r['Story ID']
if SIDMAP:  # legacy Story IDs whose number changed (removed duplicates): jg-04196 -> s01596
    for k, v in json.load(open(SIDMAP, encoding='utf-8')).items():
        if re.match(r'^jg-\d{5}$', k) and v != 's' + k[3:]: idmap[k] = v

import os
os.makedirs(OUT, exist_ok=True)
def dump(name, obj): json.dump(obj, open(f'{OUT}/{name}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
dump('data', data)
# RELCOPIES-v1 build_data: next free Release ID number (prNNNNN on the "Press releases" tab) for the Update button / sheet task
try:
    _pr = pd.read_excel(COV, sheet_name='Press releases', dtype=str).fillna('')
    _prn = [int(m.group(1)) for m in (re.match(r'^pr(\d{5})$', s(v)) for v in (_pr['Release ID'] if 'Release ID' in _pr.columns else [])) if m]
    NEXT['pr'] = max(_prn) + 1 if _prn else 1
except Exception as _e:
    report['prid_error'] = repr(_e)[:200]
dump('rows', {'cols': ['aid', 'sid', 'kind', 'outlet', 'date', 'hl', 'links'], 'rows': rows,
              'next': NEXT})
dump('idmap', idmap); dump('covcols', covcols)
dump('av', AVB)   # AVTAB-v1 build_data
# CLEAN-v1: the page-cleaning rules (clean_rules.json next to this script) go into the page as a block
_cr = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clean_rules.json')
if os.path.exists(_cr):
    json.dump(json.load(open(_cr, encoding='utf-8')), open(f'{OUT}/cleanrules.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# DRIFT-2/3 (final-int 2026-10-29): one source for the Update button's skip and don't-fetch lists: clean_rules.json skip_urls
# (the sheet task's drop_skipped list) and outlet_rules.json fetch_blocked_hosts + blocked_hosts -> <script id="fetchrules">
try:
    _here = os.path.dirname(os.path.abspath(__file__))
    _cr2 = json.load(open(os.path.join(_here, 'clean_rules.json'), encoding='utf-8'))
    _or2 = json.load(open(os.path.join(_here, 'outlet_rules.json'), encoding='utf-8'))
    dump('fetchrules', {'skip_urls': [re.sub(r'^\(\?i\)', '', x) for x in _cr2.get('skip_urls') or []],
                        # REQ-11 / REQ-12 / NOBLOGS-v1 (UPDFIX-v1): print pages (e-paper) and never-coverage hosts (platform blogs, YouTube, advocacy blogs)
                        'print_page_urls': [re.sub(r'^\(\?i\)', '', x) for x in _cr2.get('print_page_urls') or []],
                        'never_coverage': [{'host': h.split('/')[0].lower(), 'prefix': '/'.join(h.split('/')[1:]).lower(), 'why': 'personal blog platform; not press'} for h in _or2.get('never_coverage_hosts') or []]
                                          + [{'host': h.lower(), 'prefix': '', 'why': str((e or {}).get('why') or 'never coverage') + ' (NOBLOGS-v1)'}
                                             for h, e in ((json.load(open(os.path.join(_here, 'lookup_cache.json'), encoding='utf-8')) if os.path.exists(os.path.join(_here, 'lookup_cache.json')) else {}).get('never_coverage_hosts') or {}).items()],
                        'never_keep': sorted({str(h).lower() for rec in (json.load(open(os.path.join(_here, 'outlets.json'), encoding='utf-8')).get('records') or {}).values() if isinstance(rec, dict) for h in (rec.get('hosts') or [])}) if os.path.exists(os.path.join(_here, 'outlets.json')) else [],
                        # NOBLOGS-v1 (judge by the OUTLET, not the link host): an outlet on record with a type other than blog (a TV station's own video on YouTube,
                        # an LA Times story with a blogspot mirror link) is kept; blog-type, unknown or blank outlets on those hosts are not coverage
                        'never_keep_outlets': sorted(k for k, rec in ((json.load(open(os.path.join(_here, 'outlets.json'), encoding='utf-8')).get('records') or {}) if os.path.exists(os.path.join(_here, 'outlets.json')) else {}).items() if isinstance(rec, dict) and str(rec.get('type') or '').lower() not in ('', 'blog')),
                        'blocked_hosts': sorted(set(_or2.get('fetch_blocked_hosts') or []) | set(_or2.get('blocked_hosts') or [])),
                        # RECALLFIX-v1: priority local outlets, TV caps, podcasts, ethnic-media outlets (recall_sources.json + ems_ca_outlets.json next to this script)
                        'recall': (lambda rs, em: dict(rs, ethnic=dict(rs.get('ethnic') or {}, outlets=[[o.get('host'), o.get('language'), o.get('region'), o.get('city'), o.get('name')] for o in (em.get('outlets') or [])])))(
                            json.load(open(os.path.join(_here, 'recall_sources.json'), encoding='utf-8')) if os.path.exists(os.path.join(_here, 'recall_sources.json')) else {},
                            json.load(open(os.path.join(_here, 'ems_ca_outlets.json'), encoding='utf-8')) if os.path.exists(os.path.join(_here, 'ems_ca_outlets.json')) else {}),
                        # LEARN-v1: code/lookup_cache.json, compact (v = verdict) so the Update button asks it before any fetch
                        **(lambda lc: {'lookups': {k: {'v': e.get('verdict')} for k, e in (lc.get('urls') or {}).items() if e.get('verdict') in ('dead', 'not_found', 'blocked')},
                                       'lookup_hosts': {h: 1 for h in (lc.get('blocked_hosts') or {})},
                                       'lookup_archive': {k: a.get('archive_url') for k, a in (lc.get('archive') or {}).items()}})(
                            json.load(open(os.path.join(_here, 'lookup_cache.json'), encoding='utf-8')) if os.path.exists(os.path.join(_here, 'lookup_cache.json')) else {})})
except Exception as _e:
    report['fetchrules_error'] = repr(_e)[:200]
# AUTO-v1 build_data: Gabriel's bills (gabriel_bills_leginfo.json next to this script, with the bills the sheet task appended
# from the Update button's leginfo check) go into the page as <script id="billsinfo">
_bl = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gabriel_bills_leginfo.json')
if os.path.exists(_bl):
    # TAGS-v1: introduced / titles / program / budget_act / topic from bills_extra.json (same folder), so the tracker's tagBills
    # and the tone prompt never tag a bill before its introduction, know popular names and the NSGP program, skip Budget Acts
    _bx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bills_extra.json')
    _ex = {(r['bill'], r['session']): r for r in (json.load(open(_bx, encoding='utf-8')).get('rows', []) if os.path.exists(_bx) else [])}
    _prog = json.load(open(_bx, encoding='utf-8')).get('programs', {}) if os.path.exists(_bx) else {}
    dump('billsinfo', {'rows': [dict({k: b.get(k, '') for k in ('bill', 'session', 'title', 'role', 'status')},
                                     **{k: _ex.get((b['bill'], b['session']), {}).get(k, d) for k, d in
                                        (('introduced', ''), ('titles', []), ('program', ''), ('budget_act', False), ('topic', None))})
                            for b in json.load(open(_bl, encoding='utf-8')).get('rows', []) if b.get('bill')],
                       'programs': _prog})
report['bills_dropped_not_leginfo'] = dict(BILLS_DROPPED)  # F7-v1
report['reach_retired_label_left'] = sum(1 for x in data if 'Spanish-language & ethnic' in x['reach'])  # F7-v1
report.update({'rows': len(rows), 'idmap': len(idmap), 'old_codes_missing_from_idmap': len(set(OLD) - set(idmap)),
               'reprint_objs': sum(len(v) for v in reps.values())})
report.update({'links ' + k: v for k, v in LINK_SKIP.items()})  # LINKS-v1
report['links no_listed_link_originals'] = sum(1 for x in data if not x['lk'])
import csv
with open(f'{OUT}/links_not_listed.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['Article ID', 'Story ID', 'Original or reprint', 'Outlet', 'Column', 'Why not listed', 'URL']); w.writerows(LINK_SKIP_ROWS)
json.dump(dict(report), open(f'{OUT}/report.json', 'w'), indent=1)
print(dict(report), {n: os.path.getsize(f'{OUT}/{n}.json') for n in ('data', 'rows', 'idmap', 'covcols')})

# INSIGHTS-v1: data blocks for the Insights views (<INS_DIR>/<id>_data.py -> OUT/ins_<id>.json)
_here = os.path.dirname(os.path.abspath(__file__))
_ins_dir = os.environ.get('INS_DIR') or next((d for d in (os.path.join(_here, 'insights'), os.path.join(_here, '..', 'build', 'insights')) if os.path.isdir(d)), '')
if _ins_dir:
    import insights_data
    print('insights blocks:', insights_data.run(COV, OUT, _ins_dir, os.path.dirname(_here), cov=C, data=data))
# TABS-v1: data blocks for the tab modules (<TABS_DIR>/_common_data.py, <id>_data.py -> OUT/tab_<id>.json)
_tabs_dir = os.environ.get('TABS_DIR') or next((d for d in (os.path.join(_here, 'tabs'), os.path.join(_here, '..', 'build', 'tabs')) if os.path.isdir(d)), '')
if _tabs_dir:
    import tabs_data
    print('tab blocks:', tabs_data.run(COV, OUT, _tabs_dir, os.path.dirname(_here), cov=C, data=data))
