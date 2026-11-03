#!/usr/bin/env python3
"""RELBUTTON-v1 tests (rp-button, 2026-10-28): the Update button's press-release steps in sheet_task.py on a small synthetic
workbook, in both "Press releases" tab layouts (46 columns, pre-RELCOPIES-v2 names; 48 columns, renamed + Related columns).
  - _rel_mark reads/writes the renamed columns ("Copy story ID 1/2", "Has copies", "Copies (rows)", "First copy date (if
    different)") and the old ones ("Tracker release ID 1/2", "In tracker", "Coverage stories linked", ...)
  - release-pickup search finds (_release): a copy that does not name him is kept, saved and linked; a non-copy is dropped
  - relcopy rules on new rows: near copy (auto -> linked, mode nearcopy; below the bar -> review + queue item), PublicNow title
    prefix (mode title), untestable wire row matching no release -> unmarked
  - backend review #4: a passing Reprint of a story whose Original does not carry the release -> marked, not linked, reviewed
  - backend review #6: a release posted on both sites = one row (same run, and a caucus copy of an office row on the tab)
  - Related count / Related story IDs from release_related.json (tier-1 types only, reltab.RELATED_TYPES = relmatch tier 1)
  - --after-relmatch pass: derived columns + review-queue docs (nearcopy, billtags); Coverage verified unchanged
  - copies_needed: -14..+90 days around a new release
  - JS (Chromium, mock TinyFish): releaseCheck keeps the OLDEST 5, notes the rest; relDual; releasePickups queries
Run: [ST=<sheet_task.py>] python3 -I build/tests/sheet_task/test_relbutton.py   (output in work/tests_out/sheet_task_relbutton/)"""
import json, os, random, re, shutil, subprocess, sys
import openpyxl

L = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..'))
ST = os.environ.get('ST') or os.path.join(L, 'code/sheet_task.py')
CODE = os.path.dirname(ST)
OUT = os.path.join(L, 'work/tests_out/sheet_task_relbutton')
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
sys.path.insert(0, CODE)
import reltab as RT, relmatch as RM
passed = 0


def ok(c, m):
    global passed
    if not c:
        sys.exit('FAIL: ' + m)
    passed += 1
    print('PASS', m)


# ---------- text fixtures (deterministic, no accidental 25-word overlaps between texts) ----------
VOC = [w + s for w in ('budget school water county family river harbor permit transit clinic library senior housing wildfire '
                       'museum grant council tenant worker farm market bridge canyon trail garden coast valley desert orchard '
                       'meadow station').split() for s in ('', 's', 'ing', 'ed', 'er')]


def words(seed, n):
    r = random.Random(seed)
    return [r.choice(VOC) for _ in range(n)]


def sents(ws, k=15):
    return ' '.join(' '.join(ws[i:i + k]).capitalize() + '.' for i in range(0, len(ws), k))


GAB = 'Assemblymember Jesse Gabriel (D-Encino) said the measure matters for families across the state.'
REL = {   # url: (prid, date, src, title, body)
    'https://gabriel.asmdc.org/press-release/a': ('pr00301', '2026-10-20', 'office', 'Gabriel Announces Funding for Valley Schools and Parks',
                                                   GAB + ' ' + sents(words('A', 330)) + ' The bill, Assembly Bill 1264, now goes to the Senate.'),
    'https://jewishcaucus.legislature.ca.gov/news/b': ('pr00302', '2026-10-21', 'caucus', 'Caucus Welcomes Security Grants for Community Centers',
                                                        sents(words('B', 320))),
    'https://gabriel.asmdc.org/press-release/c': ('pr00303', '2026-10-22', 'office', 'Gabriel Measure on Clinic Staffing Clears Committee',
                                                   GAB + ' ' + sents(words('C', 420))),
    'https://gabriel.asmdc.org/press-release/d': ('pr00304', '2026-10-23', 'office', 'Gabriel Bill to Protect Families From Toxic Chemicals Passes the Assembly Floor',
                                                   GAB + ' ' + sents(words('D', 300))),
}
U_A, U_B, U_C, U_D = list(REL)
BODY = {u: v[4] for u, v in REL.items()}


def page(h, body):
    paras = re.split(r'(?<=\.) ', body)
    return (f'<html><head><title>{h}</title></head><body><article><h1>{h}</h1>'
            + ''.join(f'<p>{" ".join(paras[i:i + 4])}</p>' for i in range(0, len(paras), 4)) + '</article></body></html>')


def part(u, frac):
    w = BODY[u].split()
    return ' '.join(w[:int(len(w) * frac)])


# ---------- workbook ----------
src = openpyxl.load_workbook(os.path.join(L, 'work/coverage_current.xlsx'), read_only=True)
COV = [c.value for c in next(src['Coverage'].iter_rows(max_row=1))]
src.close()
# final-codedesign 2026-10-29: the master carries the 48 renamed columns since the rp-copies write, so the old 46-column layout is
# derived from reltab (RENAMED_BACK, no Related columns) instead of read from the sheet
OLD_TAB = [RT.RENAMED_BACK.get(c, c) for c in RT.COLS if c not in (RT.REL_N, RT.REL_IDS)]
ok(len(OLD_TAB) == 46 and 'Tracker release ID 1' in OLD_TAB and 'Related count' not in OLD_TAB, 'fixture: the pre-RELCOPIES-v2 46-column layout (from reltab.RENAMED_BACK)')
NEW_TAB = list(RT.COLS)
ok(len(NEW_TAB) == 48 and 'Copy story ID 1' in NEW_TAB and 'Related count' in NEW_TAB, 'fixture: reltab.COLS = 48 renamed columns')


def build_wb(path, tab_cols):
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = 'Coverage'
    ws.append(COV)
    base = {'Data Source': 'Web search (TinyFish)', 'Edition': 'Web', 'Medium': 'Online news', 'Language': 'English', 'Link status': 'Publisher URL', '# of reprints': 0}
    rows = [
        dict(base, **{'Article ID': '09001', 'Story ID': 's00010', 'Original or reprint': 'Original', 'Date': '2026-10-20', 'Outlet': 'Daily Bugle',
                      'Headline': 'Valley council debates school budget', 'Publisher link': 'https://dailybugle.example/a'}),
        dict(base, **{'Article ID': '09002', 'Story ID': 's00011', 'Original or reprint': 'Original', 'Date': '2026-10-21', 'Outlet': 'Echo Daily',
                      'Headline': 'Harbor permits stall', 'Publisher link': 'https://echodaily.example/b'}),
        dict(base, **{'Article ID': '09003', 'Story ID': 's00012', 'Original or reprint': 'Original', 'Date': '2026-10-29', 'Outlet': 'Valley Gazette',
                      'Headline': 'Transit plan advances', 'Publisher link': 'https://valleygazette.example/c'}),
    ]
    for o in rows:
        ws.append([o.get(c) for c in COV])
    wb.create_sheet('Originals')
    p = wb.create_sheet('Press releases')
    p.append(tab_cols)
    H = {c: i + 1 for i, c in enumerate(tab_cols)}
    for u, (prid, d, s, t, b) in REL.items():
        v = RT.row_values(d, t, '', s == 'caucus', u, ['AB 1264'] if prid == 'pr00301' else [], 'Yes', [], '', len(b.split()), [], '', '')
        v['Release ID'] = prid
        r = p.max_row + 1
        for k, x in v.items():
            c = RT.col(H, k)
            if c:
                p.cell(r, c).value = x if x != '' else None
    wb.save(path)


texts = {u: {'date': d, 'title': t, 'dek': '', 'body': b, 'src': s, 'prid': prid} for u, (prid, d, s, t, b) in REL.items()}
BILLS = os.path.join(OUT, 'bills.json')
json.dump({'complete': True, 'rows': [{'bill': 'AB 1264', 'session': '2025-2026', 'title': 'Schools: parks.', 'role': 'author'}]}, open(BILLS, 'w'))   # TAGS-v1: billmatch reads the real code/gabriel_bills_leginfo.json, so the bill must be one of his (AB 1264 = AB 1264 stand-in)

# ---------- the run doc ----------
NEW_E = 'https://gabriel.asmdc.org/press-release/e'
E_TXT = '# Gabriel Statement on the Coastal Trail Agreement\n\n' + GAB + ' ' + sents(words('E', 280))
db = {'runs': {'run-rb': {'at': '2026-10-27T10:00:00Z', 'rows': [
    # 1. release-search find, a verbatim copy of the caucus release (does not name him)
    {'Article ID': 'NEW-rb-1', 'Story ID': 'sNEW-rb-1', 'Original or reprint': 'Original', 'Date': '2026-10-22', 'Outlet': 'Valley Gazette',
     'Headline': REL[U_B][3], 'Publisher link': 'https://valleygazette.example/caucus-grants', 'Data Source': 'Release pickup search (TinyFish)',
     '_release': {'prid': 'pr00302', 'url': U_B}},
    # 2. release-search find that is not a copy and does not name him
    {'Article ID': 'NEW-rb-2', 'Story ID': 'sNEW-rb-2', 'Original or reprint': 'Original', 'Date': '2026-10-22', 'Outlet': 'Desert Sun Times',
     'Headline': 'Orchard festival returns', 'Publisher link': 'https://desertsun.example/orchard', 'Data Source': 'Release pickup search (TinyFish)',
     '_release': {'prid': 'pr00302', 'url': U_B}},
    # 3. ordinary find: the release C condensed to 60% (all of the story is release text) -> near copy, auto
    {'Article ID': 'NEW-rb-3', 'Story ID': 'sNEW-rb-3', 'Original or reprint': 'Original', 'Date': '2026-10-23', 'Outlet': 'Coast Weekly',
     'Headline': 'Clinic staffing measure advances', 'Publisher link': 'https://coastweekly.example/clinic'},
    # 4. ordinary find: 60% of release A + as much own reporting -> near copy below the bar (review + queue)
    {'Article ID': 'NEW-rb-4', 'Story ID': 'sNEW-rb-4', 'Original or reprint': 'Original', 'Date': '2026-10-21', 'Outlet': 'Canyon Courier',
     'Headline': 'Schools and parks money for the valley', 'Publisher link': 'https://canyoncourier.example/parks'},
    # 5. PublicNow repost: truncated title, no text
    {'Article ID': 'NEW-rb-5', 'Story ID': 'sNEW-rb-5', 'Original or reprint': 'Original', 'Date': '2026-10-24', 'Outlet': 'PublicNow',
     'Headline': 'Gabriel Bill to Protect Families From Toxic…', 'Publisher link': 'https://www.publicnow.com/view/ABC123', 'Medium': 'Online news'},
    # 6. PR Newswire row, no text, no release -> auto-marked on arrival, then unmarked
    {'Article ID': 'NEW-rb-6', 'Story ID': 'sNEW-rb-6', 'Original or reprint': 'Original', 'Date': '2026-10-24', 'Outlet': 'PR Newswire',
     'Headline': 'Acme Corp announces quarterly results', 'Publisher link': 'https://www.prnewswire.com/news-releases/acme-1.html', 'Medium': 'Online news'},
    # 7. a Reprint of s00010 (not a copy of anything) whose page is release A verbatim -> marked, not linked (backend #4)
    {'Article ID': 'NEW-rb-7', 'Story ID': 's00010', 'Original or reprint': 'Reprint', 'Date': '2026-10-21', 'Outlet': 'Echo Daily',
     'Headline': REL[U_A][3], 'Publisher link': 'https://echodaily.example/funding', '_page': 'rp-777777'},
], 'releases_new': [
    {'src': 'office', 'url': NEW_E, 'date': '2026-10-25', 'title': 'Gabriel Statement on the Coastal Trail Agreement', 'text': E_TXT,
     'time_utc': '2026-10-25T21:30:11Z', 'time_pt': '2:30 PM PT'},   # RECALLFIX-v1 (6): the listing page's time stamp
    {'src': 'caucus', 'url': 'https://jewishcaucus.legislature.ca.gov/news/e', 'date': '2026-10-25', 'title': 'Gabriel Statement on the Coastal Trail Agreement', 'text': E_TXT},
    {'src': 'caucus', 'url': 'https://jewishcaucus.legislature.ca.gov/news/a', 'date': '2026-10-21', 'title': REL[U_A][3], 'dup_of': U_A, 'html': '', 'text': ''},
]}},
    'pages': {
        'NEW-rb-1': {'url': 'https://valleygazette.example/caucus-grants', 'title': REL[U_B][3], 'scoped': page(REL[U_B][3], BODY[U_B])},
        'NEW-rb-2': {'url': 'https://desertsun.example/orchard', 'title': 'Orchard festival', 'scoped': page('Orchard festival returns', sents(words('X', 200)))},
        'NEW-rb-3': {'url': 'https://coastweekly.example/clinic', 'title': 'Clinic', 'scoped': page('Clinic staffing measure advances', part(U_C, 0.6))},
        'NEW-rb-4': {'url': 'https://canyoncourier.example/parks', 'title': 'Parks', 'scoped': page('Schools and parks money for the valley',
                     part(U_A, 0.6) + ' ' + sents(words('Y', 200)) + ' Locals said Assembly Bill 1264 would help.')},
        'rp-777777': {'url': 'https://echodaily.example/funding', 'title': REL[U_A][3], 'scoped': page(REL[U_A][3], BODY[U_A])},
    }, 'edits': {}, 'tones': {}, 'authors': {}, 'translations': {}, 'reprints': {}}
STATE0 = {'v': 1, 'version': 'RELRELATED-v3', 'rel': {'pr00301': [['s00010', 'text', 0], ['s00011', 'bill', 1], ['s99999', 'bill', 1],
                                                                  ['s00012', 'later', 9], ['s00011', 'possible', 1]],
                                                      'pr00303': [['s00011', 'anchor', 0], ['s00012', 'laterquote', 7]]}}


def run(tag, tab_cols):
    d = os.path.join(OUT, tag); os.makedirs(d)
    xin = os.path.join(d, 'in.xlsx'); build_wb(xin, tab_cols)
    rt = os.path.join(d, 'release_texts.json'); json.dump({'v': 1, 'rel': texts}, open(rt, 'w'))
    st = os.path.join(d, 'release_related.json'); json.dump(STATE0, open(st, 'w'))
    dbp = os.path.join(d, 'db.json'); json.dump(db, open(dbp, 'w'))
    out, res = os.path.join(d, 'out.xlsx'), os.path.join(d, 'result.json')
    p = subprocess.run([sys.executable, '-I', ST, '--db', dbp, '--xlsx', xin, '--out', out, '--result', res, '--pages-dir', os.path.join(d, 'pages'),
                        '--release-texts', rt, '--release-related', st, '--bills', BILLS, '--today', '2026-10-27'], capture_output=True, text=True)
    if p.returncode not in (0, 2):
        sys.exit(p.stderr[-3000:])
    return d, out, json.load(open(res)), rt


def tab(path):
    wb = openpyxl.load_workbook(path)
    ws = wb['Press releases']
    H = {c.value: c.column for c in ws[1] if c.value}
    rows = {}
    for r in range(2, ws.max_row + 1):
        g = lambda name, r=r: (lambda c: ws.cell(r, c).value if c else None)(RT.col(H, name))
        rows[g('Release ID') or g('URL')] = g
    cov = wb['Coverage']
    CH = {c.value: c.column for c in cov[1] if c.value}
    crow = {cov.cell(r, CH['Article ID']).value: (lambda name, r=r: cov.cell(r, CH[name]).value) for r in range(2, cov.max_row + 1)}
    return rows, crow, H


for tag, cols in (('old46', OLD_TAB), ('new48', NEW_TAB)):
    d, out, r, rt = run(tag, cols)
    ok(r['verify']['ok'], f'{tag}: verify ok {r["verify"]["problems"][:3]}')
    ids = r['runs']['run-rb']['ids']
    T, C, H = tab(out)
    sid = lambda ph: ids.get(ph)
    aid = lambda ph: ids.get(ph)
    # 1. release-search copy (no Gabriel) kept, saved, linked to the caucus release
    a1, s1 = aid('NEW-rb-1'), sid('sNEW-rb-1')
    ok(a1 and C[a1]('Press release') == 'Yes' and C[a1]('Saved Copy?') == 'Yes' and C[a1]('Data Source') == 'Release pickup search (TinyFish)',
       f'{tag}: release-search copy not naming him kept, saved and marked Press release = Yes')
    g = T['pr00302']
    ok(g(f'{RT.COPY_ID} 1') == s1 and g(RT.HAS_COPIES) == 'Yes' and g(RT.N_COPIES) == 1 and str(g(RT.FIRST_COPY))[:10] == '2026-10-22',
       f'{tag}: pr00302 copy columns ({"Tracker release ID 1 / In tracker / Coverage stories linked / Tracker date" if tag == "old46" else "Copy story ID 1 / Has copies / Copies (rows) / First copy date"}) = {s1}, Yes, 1, 2026-10-22')
    # 2. release-search non-copy dropped
    ok('NEW-rb-2' not in ids and any(x.get('placeholder') == 'NEW-rb-2' and x['why'] == 'release search hit, not a copy and not naming him' for x in r['releases_skipped'])
       and any(x.get('placeholder') == 'NEW-rb-2' for x in r['skipped']), f'{tag}: release-search hit that is neither a copy nor names him: dropped, in releases_skipped')
    # 3. near copy (auto)
    a3, s3 = aid('NEW-rb-3'), sid('sNEW-rb-3')
    f3 = [x for x in r['releases_flagged'] if x['aid'] == a3]
    ok(C[a3]('Press release') == 'Yes' and f3 and f3[0]['mode'] == 'nearcopy' and T['pr00303'](f'{RT.COPY_ID} 1') == s3,
       f'{tag}: condensed release (60% of it, all of the story) = near copy: marked, mode nearcopy, linked to pr00303')
    # 4. near copy below the bar: review + queue
    a4, s4 = aid('NEW-rb-4'), sid('sNEW-rb-4')
    ok(not C[a4]('Press release') and any(x.get('aid') == a4 and x['why'].startswith('near copy') for x in r['releases_review'])
       and any(q['key'] == f'pr00301:{s4}' and q['cat'] == 'nearcopy' and q['proposed'] == 'Keep as a story' for q in r['queue']['nearcopy']),
       f'{tag}: half-release story: not marked, listed in releases_review and as a nearcopy queue item')
    # 5. PublicNow title rule
    a5, s5 = aid('NEW-rb-5'), sid('sNEW-rb-5')
    f5 = [x for x in r['releases_flagged'] if x['aid'] == a5]
    ok(C[a5]('Press release') == 'Yes' and f5 and f5[0]['mode'] == 'title' and f5[0]['url'] == U_D and T['pr00304'](f'{RT.COPY_ID} 1') == s5,
       f'{tag}: PublicNow truncated title, no text: linked to pr00304 (mode title)')
    # 6. untestable wire row matching no release: unmarked
    a6 = aid('NEW-rb-6')
    ok(not C[a6]('Press release') and any(x['aid'] == a6 for x in r['releases_unmarked']), f'{tag}: PR Newswire row, no text, no release: unmarked')
    # 7. reprint guard
    a7 = aid('NEW-rb-7')
    ok(a7 and C[a7]('Press release') == 'Yes' and 's00010' not in [T['pr00301'](f'{RT.COPY_ID} {i}') for i in (1, 2)]
       and any(x.get('aid') == a7 and x['why'].startswith('copy filed under another story') for x in r['releases_review']),
       f'{tag}: passing Reprint of s00010 (Original not a copy): marked, NOT linked, in releases_review (backend #4)')
    # dual posts
    newrows = [k for k in T if k not in ('pr00301', 'pr00302', 'pr00303', 'pr00304')]
    ok(len(newrows) == 1 and T[newrows[0]]('URL') == NEW_E and T[newrows[0]]('Also on caucus site (URL)') == 'https://jewishcaucus.legislature.ca.gov/news/e',
       f'{tag}: office + caucus posting of one release in the same run = one row, caucus URL in "Also on caucus site (URL)"')
    ok('page time stamp 2:30 PM PT (2026-10-25T21:30:11Z' in str(T[newrows[0]]('Note')) and json.load(open(rt))['rel'][NEW_E].get('time_utc') == '2026-10-25T21:30:11Z'
       and json.load(open(rt))['rel'][NEW_E].get('time_pt') == '2:30 PM PT',
       f'{tag}: RECALLFIX-v1 release time stamp: in the new row\'s Note and in release_texts.json (time_utc, time_pt); a release without one gets neither')
    ok(all('page time stamp' not in str(T[k]('Note') or '') for k in ('pr00301', 'pr00302', 'pr00303', 'pr00304')), f'{tag}: existing rows\' notes untouched by the time stamp')
    ok(T['pr00301']('Also on caucus site (URL)') == 'https://jewishcaucus.legislature.ca.gov/news/a' and str(T['pr00301']('Also on caucus site (date)'))[:10] == '2026-10-21'
       and len(r['releases_dual']) == 2, f'{tag}: caucus copy (dup_of) of the office row pr00301: Also on caucus site URL + date filled, no new row')
    ok(newrows[0] == 'pr00305' and r['relmatch']['releases'] == ['pr00305'] and {s1, s3, s4}.issubset(r['relmatch']['stories']),
       f'{tag}: result.relmatch lists the new release and the new / newly saved stories {r["relmatch"]}')
    # Related columns (tier 1 only)
    if tag == 'new48':
        ok(T['pr00301'](RT.REL_N) == 2 and T['pr00301'](RT.REL_IDS) == 's00010; s00011' and T['pr00303'](RT.REL_N) == 1 and T['pr00303'](RT.REL_IDS) == 's00011'
           and T['pr00302'](RT.REL_N) == 0 and not T['pr00302'](RT.REL_IDS),
           'new48: Related count / IDs from release_related.json: tier 1 (text, bill, anchor) counted; possible, later, laterquote and unknown stories not')
    else:
        ok(r['related_cols'].get('columns') is False and RT.col(H, RT.REL_N) is None, 'old46: no Related columns on the old tab: left alone, no error')
    # after-relmatch pass
    st2 = os.path.join(d, 'state2.json')
    json.dump({'v': 1, 'version': 'RELRELATED-v3', 'rel': dict(STATE0['rel'], pr00301=STATE0['rel']['pr00301'] + [[s4, 'text', 1]],
                                                               pr00303=STATE0['rel']['pr00303'] + [[s4, 'nearcopy', 2]])}, open(st2, 'w'))
    out2, res2 = os.path.join(d, 'out2.xlsx'), os.path.join(d, 'result2.json')
    p = subprocess.run([sys.executable, '-I', ST, '--after-relmatch', st2, '--xlsx', out, '--out', out2, '--result', res2, '--prev-result',
                        os.path.join(d, 'result.json'), '--pages-dir', os.path.join(d, 'pages'), '--bills', BILLS, '--today', '2026-10-27'], capture_output=True, text=True)
    ok(p.returncode == 0, f'{tag}: --after-relmatch exit 0 ' + p.stderr[-500:])
    r2 = json.load(open(res2))
    docs = r2['queue_docs']
    nc = [x for k, v in docs.items() if k.endswith('-nearcopy') for x in v['list']]
    bt = [x for k, v in docs.items() if k.endswith('-billtags') for x in v['list']]
    ok(r2['verify']['ok'] and {x['key'] for x in nc} == {f'pr00301:{s4}', f'pr00303:{s4}'} and len({x['id'] for x in nc + bt}) == len(nc + bt),
       f'{tag}: after pass: Coverage unchanged; nearcopy docs = the sheet pass review + relmatch nearcopy row, unique ids')
    ok(len(bt) == 1 and bt[0]['key'] == s4 and bt[0]['proposed'] == f'Add AB 1264 to {s4}' and bt[0]['conf'] == 'high',
       f'{tag}: billtags: untagged story related (text) to the AB 1264 release, story names "Assembly Bill 1264" -> proposed Add (high)')
    T2, _, _ = tab(out2)
    if tag == 'new48':
        ok(T2['pr00301'](RT.REL_N) == 3 and T2['pr00303'](RT.REL_IDS) == f's00011; {s4}', 'new48: after pass recomputes Related from the updated state')

# ---------- tier set, copies_needed ----------
ok(set(RT.RELATED_TYPES) == {t for t, n in RM.TIER.items() if n == 1} == {'text', 'nearcopy', 'quote', 'bill', 'topic', 'pre', 'anchor', 'roundup'},   # RELRELATED-v4: + roundup
   'reltab.RELATED_TYPES = relmatch tier 1 (imported, not copied)')
json.dump({'runs': {'r': {'releases_new': [{'url': 'https://x', 'date': '2026-01-05'}]}}}, open(os.path.join(OUT, 'cn.json'), 'w'))
p = subprocess.run([sys.executable, '-I', ST, '--db', os.path.join(OUT, 'cn.json'), '--copies-needed'], capture_output=True, text=True)
ok('articles/2025.json' in json.loads(p.stdout) and 'articles/2026.json' in json.loads(p.stdout), 'copies_needed: a 2026-01-05 release stages 2025 too (-14 days)')

# ---------- JS: releaseCheck oldest first, relDual, releasePickups (mock TinyFish) ----------
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
if sync_playwright is None:
    print('SKIP JS checks (playwright not installed)')
else:
    js = '\n'.join(open(os.path.join(CODE, 'tracker', f)).read() for f in ('40_update_outlets.js', '41_update_search.js'))
    stub = r'''
    var D = [], BILL_INFO = [], TODAY = '2026-10-27', LAST = '2026-10-20', LOG = { runs: [] }, RANK = { topic: [], media: [] }, REACH_ORDER = [];
    var TONE_OK = new Set(), $ = () => ({ style: {}, classList: { add(){}, remove(){}, toggle(){} }, addEventListener(){}, dataset: {} }), byId = new Map(), RA = {};
    var pl = (n, w, ws) => n + ' ' + (n === 1 ? w : (ws || w + 's')), esc = s => s;
    '''
    blk = {'rel': [['s00001', '2026-10-01', 'o', 'Old release', [], '', 0, [], [], 'https://gabriel.asmdc.org/press-releases/known', 1, 'pr00300'],
                   ['off001', '2026-10-15', 'o', 'Gabriel Measure on Clinic Staffing Clears Committee', ['AB 77'], '', 0, [], [], 'https://gabriel.asmdc.org/press-releases/c', 1, 'pr00303']],
           'known': []}
    items = ''.join(f'<article><h2><a href="/press-releases/n{i}">Release {i}</a></h2><time>October {20 - i}, 2026</time></article>' for i in range(8))
    items += '<article><h2><a href="/press-releases/known">Old release</a></h2><time>October 1, 2026</time></article>'
    caucus = ('<div class="views-row"><div class="views-field-field-news-category">Press Release</div><h3><a href="/news/c1">Release 3</a></h3><time>October 17, 2026</time></div>'
              '<div class="views-row"><div class="views-field-field-news-category">Press Release</div><h3><a href="/news/c2">Gabriel Measure on Clinic Staffing Clears Committee</a></h3><time>October 16, 2026</time></div>')
    test = r'''async () => {
      U.ctl = { signal: { aborted: false } }; U.newrels = [];
      const calls = [];
      const MCP = { callTool: async (s, tool, inp) => { calls.push([tool, inp]);
        const u = (inp.urls || [])[0] || '';
        if (/press-releases(\?|$)/.test(u)) return { payload: { results: [{ url: u, text: /page=/.test(u) ? '' : OFFICE }] } };
        if (/\/news(\?|$)/.test(u)) return { payload: { results: [{ url: u, text: /page=/.test(u) ? '' : CAUCUS }] } };
        return { payload: { results: [{ url: u, text: '<article><p>Assemblymember Jesse Gabriel said the river and harbor permits for the valley families would move forward this year in the budget talks.</p></article>' }] } }; } };
      window.tfCall = async (mcp, tool, input) => mcp.callTool('tf', tool, input);   // no rate-limit wait
      window.fetch = async () => ({ ok: true, json: async () => ({ rel: { 'https://gabriel.asmdc.org/press-releases/c': { body: 'Short intro. Assemblymember Jesse Gabriel said that the clinic staffing measure will protect patients and nurses across every county in the state this year. More.' } } }) });
      await releaseCheck(MCP);
      const o = { newrels: U.newrels.map(r => [r.url, r.date, !!r.html, r.dup_of || '', r.also_caucus ? r.also_caucus.url : '']), relcheck: U.relcheck };
      const P = await releasePickups(MCP, []);
      o.plan = P.map(x => [x.kind, x.query, x.rel.prid || x.rel.url, x.minDate, x.after_date]);
      o.dual = relDual([{ src: 'office', url: 'o1', title: 'Same Title!', date: '2026-10-20' }, { src: 'caucus', url: 'c1', title: 'same title', date: '2026-10-22' }, { src: 'caucus', url: 'c2', title: 'Other', date: '2026-10-22' }], { rels: [] });
      return o; }'''
    html = ('<!doctype html><html><head><meta charset="utf-8"></head><body><script>' + stub
            + f'var OFFICE = {json.dumps(items)}, CAUCUS = {json.dumps(caucus)};</script>'
            + f'<script type="application/json" id="ins-release_pickup">{json.dumps(blk)}</script><script>' + js + '</script></body></html>')
    hp = os.path.join(OUT, 'js_test.html'); open(hp, 'w').write(html)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
        pg.goto('file://' + hp)
        o = pg.evaluate(test)
        b.close()
    ok(not errs, 'JS: 40 + 41 load without page errors ' + str(errs[:2]))
    nr = o['newrels']
    fetched = [x for x in nr if not x[3]]
    # office listing Oct 20..13 + a known one; the block's newest office release is Oct 15 -> 6 new (Oct 15..20)
    ok([x[1] for x in fetched] == ['2026-10-15', '2026-10-16', '2026-10-17', '2026-10-18', '2026-10-19'] and '1 more waiting' in o['relcheck'],
       f'JS releaseCheck: 6 new, the OLDEST 5 fetched (was the newest 5), the 6th noted as waiting: {[x[1] for x in fetched]} / {o["relcheck"]}')
    ok(any(x[0].endswith('/n3') and x[4].endswith('/news/c1') for x in nr), 'JS releaseCheck: caucus posting of this run\'s office release rides on it (also_caucus)')
    ok(any(x[3] == 'https://gabriel.asmdc.org/press-releases/c' and not x[2] for x in nr), 'JS releaseCheck: caucus copy of an office release on the tab -> dup_of, not fetched')
    ok(o['dual']['merged'] == 1 and o['dual']['keep'][0].get('also_caucus', {}).get('url') == 'c1' and len(o['dual']['keep']) == 2,
       'JS relDual: office + caucus same title within 3 days = one item (also_caucus)')
    kinds = {x[0] for x in o['plan']}
    pc = [x for x in o['plan'] if x[2] == 'pr00303']
    ok(kinds == {'release'} and len({x[2] for x in o['plan']}) <= 8 and len(pc) == 3 and pc[0][1] == '"Gabriel Measure on Clinic Staffing Clears Committee"'
       and pc[1][1].startswith('"Assemblymember Jesse Gabriel said that the clinic') and len(pc[1][1].strip('"').split()) == 12 and pc[2][1] == '"AB 77" California'
       and pc[0][3] == '2026-10-14', f'JS releasePickups: title, 12-word sentence and bill queries per open release, from the day before it: {pc}')
    ok(not any(x[2] == 'pr00300' for x in o['plan']), 'JS releasePickups: releases older than 30 days are not searched')
print(f'ALL {passed} CHECKS PASSED')
