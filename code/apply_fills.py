"""T14: ONE workbook write that applies every agent's results, blanks only, green font.
Usage: python3 -I apply_fills.py IN.xlsx OUT.xlsx REPORT.json [--reach-approved CSV] [--hold SIDS_FILE]
Sources (all under lib/work):
  out/tone_*.jsonl, out/tone_batch_*.out.jsonl  -> Tone, Tone note, Tone rated by, Topic, Bills (+ hl_en / text_en if given)
  out/translate_tracker.jsonl                  -> Translated Headline, Story in English
  out/headlines_nb.jsonl                       -> Translated Headline (lines with "flag" skipped)
  texts/nb/<aid>.json                          -> Author / byline (only people-looking names), Word count,
                                                  Mentions "Gabriel" in text
  --reach-approved CSV (outlet_sheet, reach)   -> Reach on Original rows of that outlet
Lines flagged (no Gabriel mention, borderline page, etc.) and sids in --hold are never written; they go to the report.
Mirrors every write into the Originals tab; verifies with pandas that no pre-existing non-blank cell changed.
T14a (agent-write1, 2026-10-27) adds, in clearly marked blocks:
  --fulltext            full-text tone OVERWRITE of excerpt/snippet tones (DECISIONS: always use the full-text tone)
  --queue JSON          review-queue decisions (work/tmp_agent-write1/queue_joined.json): Reach (blanks; relabel = override),
                        Role (blanks), Language (override, decided items only)
  --authors-csv CSV     out/author_fills.csv "Author / byline" (excludes noted/low-confidence rows and --author-skip aids)
  --pr-high-only        'Press release' = 'Yes' only for verdict yes + confidence high
  --extras              out/author_pass_extras.csv Word count / Mentions "Gabriel"
Overrides (existing values changed on purpose) are recorded in report['overrides'] and the verify step checks that
every changed pre-existing cell is one of them.
"""
import sys, os, json, glob, argparse, copy, re, collections
import openpyxl, pandas as pd
from openpyxl.styles import Font
ap = argparse.ArgumentParser(); ap.add_argument('inp'); ap.add_argument('out'); ap.add_argument('report')
ap.add_argument('--reach-approved'); ap.add_argument('--hold')
ap.add_argument('--fulltext', action='store_true'); ap.add_argument('--queue'); ap.add_argument('--authors-csv')
ap.add_argument('--author-skip', default=''); ap.add_argument('--pr-high-only', action='store_true')
ap.add_argument('--extras', action='store_true'); ap.add_argument('--hl-skip-sids', default='')
a = ap.parse_args()
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
GREEN = '000B8A3E'
hold = set(open(a.hold).read().split()) if a.hold else set()
wb = openpyxl.load_workbook(a.inp); ws = wb['Coverage']; wo = wb['Originals']
col = {c.value: i + 1 for i, c in enumerate(ws[1])}; ocol = {c.value: i + 1 for i, c in enumerate(wo[1])}
row_of = {ws.cell(r, col['Article ID']).value: r for r in range(2, ws.max_row + 1)}
orow_of = {wo.cell(r, ocol['Article ID']).value: r for r in range(2, wo.max_row + 1)}
sid_aid = {ws.cell(r, col['Story ID']).value: ws.cell(r, col['Article ID']).value for r in range(2, ws.max_row + 1)
           if ws.cell(r, col['Original or reprint']).value == 'Original'}
rep = {'written': {}, 'skipped_nonblank': 0, 'held': [], 'flagged': [], 'remapped': 0}
# rows removed in the 2026-10-27 fix: results keyed by them go to the real row
_dm = json.load(open(os.path.join(W, 'dup_id_map.json'))) if os.path.exists(os.path.join(W, 'dup_id_map.json')) else {'aid': {}, 'sid': {}}
def fix_ids(x):
    if x.get('aid') in _dm['aid']: x['aid'] = _dm['aid'][x['aid']]; rep['remapped'] += 1
    if x.get('sid') in _dm['sid']: x['sid'] = _dm['sid'][x['sid']]
    return x

def blank(v): return v is None or (isinstance(v, str) and not v.strip())
def put(aid, colname, val):
    if val in (None, '', []) or aid not in row_of or colname not in col: return
    for sheet, rows, cols in ((ws, row_of, col), (wo, orow_of, ocol)):
        if aid not in rows or colname not in cols: continue
        c = sheet.cell(rows[aid], cols[colname])
        if not blank(c.value):
            if sheet is ws: rep['skipped_nonblank'] += 1
            continue
        c.value = val; f = c.font or Font()
        c.font = Font(name=f.name, size=f.size, bold=f.bold, italic=f.italic, color=GREEN)
        if sheet is ws: rep['written'][colname] = rep['written'].get(colname, 0) + 1; FILLED.add((aid, colname))
FILLED = set()   # (aid, column) blank cells filled in this run (T14a: so a later override of them isn't counted)

# --- T14a: explicit overrides (only where DECISIONS.md / a recorded queue decision says so) ---
OVR = []   # (aid, column, old, new, reason)
def force(aid, colname, val, reason):
    if val in (None, '', []) or aid not in row_of or colname not in col: return
    for sheet, rows, cols in ((ws, row_of, col), (wo, orow_of, ocol)):
        if aid not in rows or colname not in cols: continue
        c = sheet.cell(rows[aid], cols[colname]); old = c.value
        if not blank(old) and str(old) == str(val): continue
        if sheet is ws:
            if (aid, colname) in FILLED: pass
            elif blank(old): rep['written'][colname] = rep['written'].get(colname, 0) + 1
            else: OVR.append((aid, colname, str(old), str(val), reason))
        c.value = val; f = c.font or Font()
        c.font = Font(name=f.name, size=f.size, bold=f.bold, italic=f.italic, color=GREEN)
def cellv(aid, colname): return ws.cell(row_of[aid], col[colname]).value
# --- end overrides helper ---

def lines(pattern):
    for f in sorted(glob.glob(os.path.join(W, pattern))):
        for l in open(f, encoding='utf-8'):
            if l.strip(): yield fix_ids(json.loads(l))

import re as _re
# --- T14a: Gabriel bill list = leginfo list (incl. the 63 bills-tab adds); AB 1377 decided 'not his' ---
_g = json.load(open(os.path.join(W, 'gabriel_bills_leginfo.json')))
def _nb(b): return _re.sub(r'\s+', ' ', str(b).strip().upper().replace('-', ' ')).replace('ABX1 ', 'ABX1-').replace('SBX1 ', 'SBX1-')
GB = {_nb(r['bill']) for r in _g['rows']} - {'AB 1377'}
rep['bills_dropped'] = []
def bills_of(x):
    b = x.get('bills') or []; b = b if isinstance(b, list) else _re.split(r';\s*|,\s*', b)
    ob = x.get('other_bills') or []
    if isinstance(ob, str): ob = _re.split(r';\s*|,\s*', ob)
    if 'implied only' in str(x.get('other_bills_note', '')): ob = []
    out = []
    for v in list(b) + list(ob):
        v = str(v).strip()
        if not v: continue
        if _nb(v) not in GB: rep['bills_dropped'].append({'sid': x.get('sid'), 'bill': v}); continue
        if _nb(v) not in [_nb(o) for o in out]: out.append(v)
    return '; '.join(out)
# sids whose English headline/text must not be written (already English / not a single article / open queue items)
HLSKIP = set(a.hl_skip_sids.split(',')) if a.hl_skip_sids else set()
# --- end bill list ---

# --- T14a: full-text tone OVERWRITE (DECISIONS 2026-10-27: ALWAYS use the full-text tone over a snippet tone) ---
FT_BY = 'Claude, from saved copy (2026-10-27)'
ft = rep['fulltext'] = {'overwritten_rows': 0, 'filled_blank_rows': 0, 'flagged_skipped': [], 'not_excerpt': 0}
if a.fulltext:
    for x in lines('out/fetch_rated_*.out.jsonl'):
        if 'fulltext_tone' not in x: continue
        sid = x.get('sid'); aid = x.get('aid') or sid_aid.get(sid)
        if sid in hold or aid not in row_of: continue
        if x.get('flag'): ft['flagged_skipped'].append({'sid': sid, 'aid': aid, 'flag': x['flag']}); continue
        by = str(cellv(aid, 'Tone rated by') or '')
        if blank(cellv(aid, 'Tone')):
            put(aid, 'Tone', x['fulltext_tone']); put(aid, 'Tone note', x['fulltext_why']); put(aid, 'Tone rated by', FT_BY)
            ft['filled_blank_rows'] += 1
        elif _re.search(r'excerpt|snippet', by, _re.I):
            r = 'full-text tone over excerpt tone (DECISIONS 2026-10-27)'
            force(aid, 'Tone', x['fulltext_tone'], r); force(aid, 'Tone note', x['fulltext_why'], r); force(aid, 'Tone rated by', FT_BY, r)
            ft['overwritten_rows'] += 1
        else: ft['not_excerpt'] += 1
        put(aid, 'Topic', x.get('topic')); put(aid, 'Bills', bills_of(x))
        if sid not in HLSKIP: put(aid, 'Translated Headline', x.get('hl_en'))
# --- end full-text tone ---

_tone_files = sorted(set(glob.glob(os.path.join(W, 'out/tone_*.jsonl'))) | set(glob.glob(os.path.join(W, 'out/tone_batch_*.out.jsonl'))))
_ob = {}   # other_bills_batch8.jsonl: extra Gabriel bills found by tone batch 8 after it finished
for l in open(os.path.join(W, 'out', 'other_bills_batch8.jsonl')) if os.path.exists(os.path.join(W, 'out', 'other_bills_batch8.jsonl')) else []:
    if l.strip(): y = json.loads(l); _ob[y['sid']] = y
for f in _tone_files:
  for l in open(f, encoding='utf-8'):
    if not l.strip(): continue
    x = fix_ids(json.loads(l))
    sid = x.get('sid'); aid = x.get('aid') or sid_aid.get(sid)
    if sid in hold: rep['held'].append(sid); continue
    if x.get('flag'): rep['flagged'].append({'sid': sid, 'aid': aid, 'flag': x['flag']}); continue
    if sid in _ob and not x.get('other_bills'): x['other_bills'] = _ob[sid]['other_bills']; x['other_bills_note'] = _ob[sid].get('other_bills_note', '')
    put(aid, 'Tone', x.get('tone')); put(aid, 'Tone note', x.get('why')); put(aid, 'Tone rated by', x.get('rated_by'))
    put(aid, 'Topic', x.get('topic')); put(aid, 'Bills', bills_of(x))
    if sid not in HLSKIP: put(aid, 'Translated Headline', x.get('hl_en')); put(aid, 'Story in English', x.get('text_en'))
for x in lines('out/translate_tracker.jsonl'):
    if x.get('sid') in hold or x.get('sid') in HLSKIP: continue
    if x.get('source_already_english'): rep['flagged'].append({'sid': x.get('sid'), 'aid': x.get('aid'), 'flag': 'translate: ' + str(x.get('note') or 'source already English')}); continue
    put(x.get('aid'), 'Translated Headline', x.get('hl_en')); put(x.get('aid'), 'Story in English', x.get('text_en'))
for x in lines('out/headlines_nb.jsonl'):
    if x.get('flag'): rep['flagged'].append({'sid': x.get('sid'), 'aid': x.get('aid'), 'flag': x['flag']}); continue
    if x.get('sid') in HLSKIP: continue
    put(x.get('aid'), 'Translated Headline', x.get('hl_en'))
# bylines: only the people the NewsBank-text agent vetted (is_person, 'proposed' value)
af = os.path.join(W, 'texts', 'nb_author_fills.csv')
if os.path.exists(af):
    for _, x in pd.read_csv(af, dtype=str).fillna('').iterrows():
        if x['is_person'] == 'True' and x['proposed']: put(x['aid'], 'Author / byline', x['proposed'])
for f in glob.glob(os.path.join(W, 'texts', 'nb', '*.json')):
    t = json.load(open(f)); aid = t.get('aid')
    if aid not in row_of: continue
    if t.get('words'): put(aid, 'Word count', str(t['words']))
    if t.get('page'): put(aid, 'Page', str(t['page']))
    if t.get('section'): put(aid, 'Section', str(t['section']))
    mg = t.get('mentions_gabriel')   # T14a fix: stored as the string 'True'/'False'
    if mg not in (None, ''): put(aid, 'Mentions "Gabriel" in text', 'Yes' if str(mg).lower() == 'true' else 'No')
if a.reach_approved:
    ok = pd.read_csv(a.reach_approved, dtype=str).fillna('')
    m = dict(zip(ok['outlet_sheet'], ok['reach']))
    for aid, r in row_of.items():
        if ws.cell(r, col['Original or reprint']).value == 'Original':
            o = ws.cell(r, col['Outlet']).value
            if o in m and m[o]: put(aid, 'Reach', m[o])

# --- Tracker reprint-list rows: same-outlet location/medium/language/publisher fills (agent-reprint-fills) ---
# Source: work/out/reprint_fills.csv (aid, sid, outlet, column, value, basis), built by
# work/tmp_reprint_fills/derive.py: a blank cell is filled only when every other row of the same outlet
# (exact name, NewsBank style, or an outlet variant now in outlet_rules.json (OUTLETRULES-v1; formerly the Reprint info
# tab); generic names only with the same city) agrees.
# Blanks only (put() never overwrites), green font like every other fill here. Every target is a
# "Tracker reprint list" row, which never appears on the Originals tab, so Originals is unaffected
# (put() only mirrors to Originals when the Article ID is there). Rows whose sid is in --hold are skipped.
RCOLS = {'Outlet city', 'Outlet county', 'Outlet state', 'Medium', 'Language', 'Publisher'}
rf = os.path.join(W, 'out', 'reprint_fills.csv')
if os.path.exists(rf):
    rr = rep['reprint_fills'] = {'rows_in_csv': 0, 'written': {}, 'skipped_nonblank': 0, 'held': 0,
                                 'not_reprint_list_row': 0, 'unknown_aid': 0}
    for x in pd.read_csv(rf, dtype=str).fillna('').to_dict('records'):
        x = fix_ids(x); rr['rows_in_csv'] += 1
        aid, c, v = x['aid'], x['column'], x['value']
        if aid not in row_of or c not in RCOLS or not v: rr['unknown_aid'] += 1; continue
        if x.get('sid') in hold: rr['held'] += 1; continue
        if ws.cell(row_of[aid], col['Data Source']).value != 'Tracker reprint list':
            rr['not_reprint_list_row'] += 1; continue
        if not blank(ws.cell(row_of[aid], col[c]).value): rr['skipped_nonblank'] += 1; continue
        put(aid, c, v); rr['written'][c] = rr['written'].get(c, 0) + 1
# --- end reprint-list fills ---

# --- T14a: author_fills.csv "Author / byline" (agent-authors T24), blanks only ---
# Skipped: rows with a note (page title differs from the sheet headline = lower confidence; SDJW reposted press
# releases whose byline names the issuing office) and every aid in --author-skip. Author 1..N columns NOT written.
if a.authors_csv:
    ar = rep['author_fills'] = {'rows': 0, 'skipped_note': [], 'skipped_listed': [], 'held': 0}
    askip = set(a.author_skip.split(',')) if a.author_skip else set()
    for x in pd.read_csv(a.authors_csv, dtype=str).fillna('').to_dict('records'):
        x = fix_ids(x); ar['rows'] += 1
        if x['aid'] in askip: ar['skipped_listed'].append(x['aid']); continue
        if x['note'] and 'Op-ed by Jesse Gabriel' not in x['note']: ar['skipped_note'].append(x['aid']); continue
        if x.get('sid') in hold: ar['held'] += 1; continue
        put(x['aid'], 'Author / byline', x['author'])
# --- end author_fills ---

# --- T14a: author_pass_extras.csv (word count read from the saved copy / live page; Gabriel mention on live pages) ---
if a.extras:
    for x in pd.read_csv(os.path.join(W, 'out', 'author_pass_extras.csv'), dtype=str).fillna('').to_dict('records'):
        x = fix_ids(x)
        if x.get('sid') in hold: continue
        if x['words_read'] and x['words_read'] not in ('0',): put(x['aid'], 'Word count', x['words_read'])
        if x['mentions_gabriel'].lower() in ('true', 'false'):
            put(x['aid'], 'Mentions "Gabriel" in text', 'Yes' if x['mentions_gabriel'].lower() == 'true' else 'No')
# --- end extras ---

# --- T14a: review-queue decisions (only items with a recorded decision) ---
NEWREACH = ['National', 'International', 'Statewide California', 'District & Valley', 'California regional & local',
            'Jewish press', 'Spanish-language', 'Ethnic', 'Trade, advocacy & blogs', 'Out-of-state local']
def _disp(o):
    o = str(o or '').strip(); m = _re.match(r'^(.*), (The|La|El|Los|Las|Le|Les|Die|Der|Il)$', o)
    return (f'{m.group(2)} {m.group(1)}' if m else o).lower()
if a.queue:
    Q = json.load(open(a.queue))
    qr = rep['queue'] = {'reach_items': 0, 'reach_rows_filled': 0, 'reach_rows_nonblank_kept': 0, 'relabel_items': 0,
                         'relabel_rows': 0, 'role': 0, 'role_nonblank_kept': [], 'language': 0, 'label_mapped': [],
                         'not_applied': {}}
    P = pd.read_csv(os.path.join(W, 'out', 'reach_proposals.csv'), dtype=str).fillna('')
    R = pd.read_csv(os.path.join(W, 'out', 'reach_relabel.csv'), dtype=str).fillna('')
    orig_by_outlet = {}
    orig_by_sid = {}
    for aid_, r_ in row_of.items():
        if ws.cell(r_, col['Original or reprint']).value == 'Original':
            orig_by_outlet.setdefault(_disp(ws.cell(r_, col['Outlet']).value), []).append(aid_)
            orig_by_sid[ws.cell(r_, col['Story ID']).value] = aid_
    def tags(item, d):
        ch = d['choice']; ch = ch if isinstance(ch, list) else [ch]; out = []
        for v in ch:
            if v == 'Spanish-language & ethnic':   # retired label chosen before the split
                v2 = 'Ethnic' if item['key'] == 'California Courier, The' else 'Spanish-language'
                qr['label_mapped'].append({'id': item['id'], 'from': v, 'to': v2}); v = v2
            if v in NEWREACH and v not in out: out.append(v)
        return '; '.join(out)
    for x in Q:
        it, d = x['item'], x['decision']
        if not d: continue
        cat = it['cat']
        if cat == 'reach':
            v = tags(it, d); qr['reach_items'] += 1
            pp = P[(P.outlet_sheet == it['key']) | (P.outlet_display == it['key'])]
            names = {_disp(it['key'])} | {_disp(o) for o in pp.outlet_sheet} | {_disp(o) for o in pp.outlet_display}
            for n in names:
                for aid_ in orig_by_outlet.get(n, []):
                    if blank(cellv(aid_, 'Reach')): put(aid_, 'Reach', v); qr['reach_rows_filled'] += 1
                    elif cellv(aid_, 'Reach') != v: qr['reach_rows_nonblank_kept'] += 1
        elif cat == 'relabel':   # DECISIONS 2026-10-27: explicit override for this relabel only
            v = tags(it, d); qr['relabel_items'] += 1
            sids = set()
            for z in R[R.outlet_sheet == it['key']].story_ids: sids |= set(z.split())
            for sd in sids:
                sd = _dm['sid'].get(sd, sd); aid_ = orig_by_sid.get(sd)
                if not aid_: qr.setdefault('relabel_no_original', []).append(sd); continue
                if _disp(cellv(aid_, 'Outlet')) != _disp(it['key']):   # the story's Original is another outlet
                    qr.setdefault('relabel_other_outlet', []).append({'id': it['id'], 'sid': sd, 'outlet': cellv(aid_, 'Outlet')}); continue
                force(aid_, 'Reach', v, f'Reach relabel {it["id"]} (DECISIONS 2026-10-27 Spanish-language/Ethnic/International)'); qr['relabel_rows'] += 1
        elif cat == 'role':
            if blank(cellv(it['key'], 'Role')): put(it['key'], 'Role', d['choice']); qr['role'] += 1
            elif cellv(it['key'], 'Role') != d['choice']: qr['role_nonblank_kept'].append(it['key'])
        elif cat == 'language':
            m = _re.match(r'^Change Language to (\w+)$', str(d['choice']))
            if not m: continue
            aid_ = it['key'] if it['key'] in row_of else orig_by_sid.get(_dm['sid'].get(it['key'], it['key']))
            if aid_: force(aid_, 'Language', m.group(1), f'queue decision {it["id"]}: {d["choice"]}'); qr['language'] += 1
        else:
            qr['not_applied'][cat] = qr['not_applied'].get(cat, 0) + 1
# --- end review-queue decisions ---

# --- Press release column (agent-pressrelease; DECISIONS 2026-10-27 "pure press releases are excluded") ---
# Source: work/out/press_releases.csv (old_aid, sid, outlet, headline, verdict, confidence, reason).
# verdict 'yes' -> 'Press release' = 'Yes' (green). T14a: with --pr-high-only, only confidence 'high'.
# 'borderline' -> 'Yes' only if Sammy chose the release option in the review queue (none yet). 'no' -> blank.
PR_COL = 'Press release'
PR_YES_CHOICE = 'Press release: leave out of tracker (Press release = Yes)'
for sheet, cols in ((ws, col), (wo, ocol)):
    if PR_COL not in cols:
        c = sheet.max_column + 1
        sheet.cell(1, c).value = PR_COL
        h = sheet.cell(1, c - 1)                      # copy the header style of the previous header cell
        sheet.cell(1, c).font = copy.copy(h.font); sheet.cell(1, c).fill = copy.copy(h.fill)
        sheet.cell(1, c).alignment = copy.copy(h.alignment); sheet.cell(1, c).border = copy.copy(h.border)
        cols[PR_COL] = c
prf = os.path.join(W, 'out', 'press_releases.csv')
pq = os.path.join(W, 'out', 'pressrelease_queue_decisions.json')   # optional: export of decisions for pr-* items
qdec = json.load(open(pq)) if os.path.exists(pq) else {}
rp = rep['press_release'] = {'yes_auto': 0, 'yes_queue': 0, 'yes_medium_skipped': 0, 'borderline_undecided': 0, 'unknown_aid': 0}
if os.path.exists(prf):
    for x in pd.read_csv(prf, dtype=str).fillna('').to_dict('records'):
        conf = x['confidence']
        x = fix_ids({'aid': x['old_aid'], 'sid': x['sid'], 'verdict': x['verdict']})
        if x['aid'] not in row_of: rp['unknown_aid'] += 1; continue
        if x['verdict'] == 'yes':
            if a.pr_high_only and conf != 'high': rp['yes_medium_skipped'] += 1; continue
            put(x['aid'], PR_COL, 'Yes'); rp['yes_auto'] += 1
        elif x['verdict'] == 'borderline':
            if qdec.get(x['aid']) == PR_YES_CHOICE: put(x['aid'], PR_COL, 'Yes'); rp['yes_queue'] += 1
            else: rp['borderline_undecided'] += 1
# --- end Press release ---
# --- T30 author columns (agent-authorsplit; DECISIONS 2026-10-27 "authors split into columns") ---
# Runs LAST, after every put(): inserting columns shifts column indexes, and bylines written above are split too.
# Sources: the sheet's "Author / byline"; out/author_fills.csv (T24 structured split, keeps titles) when it names the
# same people; out/author_overrides.csv (aid, authors joined " | ", title) = Sammy's 15-authors queue answers.
# Rows in --hold are split like any other row (the columns only restate the existing byline).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from author_columns import add_author_columns
_af = os.path.join(W, 'out', 'author_fills.csv')
_fills = {}
if os.path.exists(_af):
    for _x in pd.read_csv(_af, dtype=str).fillna('').to_dict('records'):
        if _x.get('authors'): _x = fix_ids(_x); _fills[_x['aid']] = _x
_ovf = os.path.join(W, 'out', 'author_overrides.csv')
_over = {}
if os.path.exists(_ovf):
    for _x in pd.read_csv(_ovf, dtype=str).fillna('').to_dict('records'):
        _x = fix_ids(_x); _over[_x['aid']] = (_x['authors'], _x.get('title', ''))
rep['author_columns'] = add_author_columns(wb, fills=_fills, overrides=_over)
# --- end author columns ---
wb.save(a.out)
# verify
A = pd.read_excel(a.inp, sheet_name=None, dtype=str); B = pd.read_excel(a.out, sheet_name=None, dtype=str)
# T14a: the new 'Press release' column is allowed (press_release_build.md); every changed pre-existing value must be
# one of the recorded overrides (OVR), counted separately.
ovr_keys = {(o[0], o[1]) for o in OVR}
rep['overrides'] = [dict(zip(('aid', 'column', 'old', 'new', 'reason'), o)) for o in OVR]
for s in ('Coverage', 'Originals'):
    x, y = A[s], B[s]
    AUTH = rep['author_columns'][s]['columns'] if rep['author_columns'][s]['inserted'] else []
    if AUTH:   # T30: Author 1..N + Author title sit right after Author / byline
        _i = list(y.columns).index('Author / byline'); assert list(y.columns)[_i + 1:_i + 1 + len(AUTH)] == AUTH, (s, 'author cols')
    new = [c for c in y.columns if c not in x.columns and c not in AUTH]
    assert new in ([], ['Press release']), (s, new)
    y_old = y[list(x.columns)]
    assert x.shape == y_old.shape and list(x.columns) == list(y_old.columns), s
    diff = (x.notna()) & (x.fillna('') != y_old.fillna(''))
    ch = int(diff.sum().sum()); bad = 0; ok = 0
    for ci, cn in enumerate(x.columns):
        for ri in diff.index[diff[cn]]:
            if (x.at[ri, 'Article ID'], cn) in ovr_keys: ok += 1
            else: bad += 1
    rep[f'{s}_existing_changed'] = ch; rep[f'{s}_existing_changed_override'] = ok; rep[f'{s}_existing_changed_unexpected'] = bad
    assert bad == 0, f'{s}: {bad} existing values changed outside the recorded overrides'
    if new: rep[f'{s}_press_release_yes'] = int((y['Press release'].fillna('') == 'Yes').sum())
rep['overrides_by_column'] = dict(collections.Counter(o[1] for o in OVR))
json.dump(rep, open(a.report, 'w'), indent=1)
print(json.dumps({k: v if not isinstance(v, list) else len(v) for k, v in rep.items()}))
