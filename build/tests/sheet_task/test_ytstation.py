#!/usr/bin/env python3
"""YTSTATION-v1 (Sammy 2026-11-02): a find from a TV / radio station's own YouTube channel is written as Medium TV, Format "Broadcast segment",
Data Source "Web search (TinyFish, YouTube station channel)", and gets its Audio & video details row (Item type Broadcast segment, Channel, Station, Network).
A YouTube link without that mark is still refused (NOBLOGS-v1).   Run: python3 -I test_ytstation.py [CODE_DIR]"""
import os, sys, json, tempfile, openpyxl
HERE = os.path.dirname(os.path.abspath(__file__))
L = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CODE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(L, 'code')
sys.path.insert(0, CODE)
import sheet_task as ST, avtab as AV
H = [c.value for c in next(openpyxl.load_workbook(os.path.join(L, 'work/coverage_current.xlsx'), read_only=True)['Coverage'].iter_rows(max_row=1)) if c.value]
n = 0
def ok(c, m):
    global n
    if not c: sys.exit('FAIL ' + m)
    n += 1; print('PASS', m)
wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Coverage'; ws.append(H)
av = wb.create_sheet('Audio & video details'); av.append(list(AV.COLS)); wb.create_sheet('Originals')
p = tempfile.mktemp(suffix='.xlsx'); wb.save(p)
URL = 'https://www.youtube.com/watch?v=P6zsjIepWaQ'
AVV = {'Item type': 'Broadcast segment', 'Channel': 'FOX 11 Los Angeles', 'Station': 'KTTV', 'Network': 'FOX', 'Episode/segment title': 'Special Report: Assemblyman Jesse Gabriel',
       'Air/publish date': '2022-03-17', 'YouTube link': URL, 'Details from': 'YouTube page'}
find = {'Article ID': 'NEW-r-1', 'Story ID': 'sNEW-r-1', 'Original or reprint': 'Original', 'Data Source': 'Web search (TinyFish, YouTube station channel)', 'Date': '2026-10-30',
        'Outlet': 'FOX 11 Los Angeles', 'Headline': 'Special Report: Assemblyman Jesse Gabriel', 'Edition': 'Web', 'Language': 'English', 'Medium': 'TV', 'Format': 'Broadcast segment',
        'Publisher link': URL, 'Link status': 'Publisher URL', '_av': AVV}
other = dict(find, **{'Article ID': 'NEW-r-2', 'Story ID': 'sNEW-r-2', 'Outlet': 'Forbes Breaking News', 'Medium': 'Online news', 'Format': 'Video clip',
                      'Publisher link': 'https://www.youtube.com/watch?v=nIKyZqVQaFo', 'Headline': 'Lawmaker calls out GOP'}); other.pop('_av')
T = ST.Task(ST.Sheet(p), {'pages': {}, 'runs': {'r1': {'at': '2026-10-30T10:00:00Z', 'rows': [find, other]}}}, '2026-10-30')
res = T.run(None)
ST.rebuild_originals(T.s)
out = tempfile.mktemp(suffix='.xlsx'); T.s.wb.save(out)
r = T.s.rows.get(res['runs']['r1']['ids']['NEW-r-1'])
ok(r is not None, 'the station YouTube find was added')
g = lambda c: T.s.get(r, c)
ok(g('Medium') == 'TV' and g('Format') == 'Broadcast segment', f"Medium TV, Format Broadcast segment (got {g('Medium')!r}, {g('Format')!r}); not Video clip")
ok(g('Data Source') == 'Web search (TinyFish, YouTube station channel)' and g('Link status') == 'Publisher URL' and g('Publisher link') == URL, 'Data Source, Link status, Publisher link')
ok(g('Outlet') == 'FOX 11 Los Angeles', 'Outlet is the station')
rows = list(openpyxl.load_workbook(out)['Audio & video details'].iter_rows(values_only=True))
hd = rows[0]; mine = [dict(zip(hd, x)) for x in rows[1:] if x[0] == g('Article ID')]
ok(len(mine) == 1, 'one Audio & video details row')
a = mine[0]
ok(a['Item type'] == 'Broadcast segment' and a['Channel'] == 'FOX 11 Los Angeles' and a['Station'] == 'KTTV' and a['Network'] == 'FOX', 'AV row: Item type, Channel, Station, Network')
ok(a['Episode/segment title'] == 'Special Report: Assemblyman Jesse Gabriel' and str(a['Air/publish date'])[:10] == '2022-03-17' and a['YouTube link'] == URL and a['Details from'] == 'YouTube page', 'AV row: title, air date, YouTube link, Details from')
ok('nIKyZqVQaFo' not in json.dumps([x for x in T.s.wb['Coverage'].iter_rows(values_only=True)], default=str), 'a YouTube find without the station mark (Forbes Breaking News) is still refused')
v = ST.verify(p, out, res)
ok(v['ok'], 'verify passes: ' + json.dumps(v['problems'][:3]))
ok(ST.format_of({'Medium': 'TV', 'Publisher link': URL}, 'Broadcast segment') == 'Broadcast segment' and ST.format_of({'Medium': 'Online news', 'Publisher link': URL}) == 'Video clip', 'format_of: the AV item type beats the youtube.com host rule; a plain YouTube link stays Video clip')

# ---- same segment as a tracked story (Sammy 2026-11-02): the story becomes a broadcast story, the video attached, no new story ----
base = {'Data Source': 'Web search (TinyFish)', 'Edition': 'Web', 'Language': 'English', 'Link status': 'Publisher URL', 'Original or reprint': 'Original', 'Medium': 'TV', 'Format': 'Article', '# of reprints': 0}
ex = [dict(base, **{'Article ID': '00100', 'Story ID': 's00100', 'Date': '2026-10-20', 'Year': 2026, 'Outlet': 'FOX 11 Los Angeles', 'Headline': 'Gas rebate debated', 'Publisher link': 'https://www.foxla.com/news/gas', 'File name': 'saved.html', 'Saved Copy?': 'Yes'}),
      dict(base, **{'Article ID': '00101', 'Story ID': 's00101', 'Date': '2026-10-20', 'Year': 2026, 'Outlet': 'KTLA', 'Medium': 'Video', 'Format': 'Video clip', 'Headline': 'Budget vote', 'Publisher link': 'https://ktla.com/news/budget'}),
      dict(base, **{'Article ID': '00102', 'Story ID': 's00102', 'Date': '2026-10-20', 'Year': 2026, 'Outlet': 'ABC7 Los Angeles', 'Headline': 'Fire bill', 'Publisher link': 'https://abc7.com/fire', 'Team note': 'checked'})]
wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Coverage'; ws.append(H)
for d in ex: ws.append([d.get(h, '') for h in H])
av = wb.create_sheet('Audio & video details'); av.append(list(AV.COLS))
ci = {c: i for i, c in enumerate(AV.COLS)}
a1 = ['00100', 's00100', 'TV', 'Video clip'] + [''] * (len(AV.COLS) - 4)                       # AV row: Item type Video clip, blank Channel / link
a2 = ['00102', 's00102', 'TV', 'Web story'] + [''] * (len(AV.COLS) - 4); a2[ci['Channel']] = 'ABC7 Los Angeles'   # AV row with a Channel already
av.append(a1); av.append(a2)
wb.create_sheet('Originals')
p2 = tempfile.mktemp(suffix='.xlsx'); wb.save(p2)
mk = lambda v, row_link, ch, st, net, med: {'row_link': row_link, 'link': 'https://www.youtube.com/watch?v=' + v, 'title': 'x', 'channel': ch, 'station': st, 'network': net, 'medium': med, 'date': '2026-10-20', 'story': 's'}
att = [mk('P6zsjIepWaQ', 'https://www.foxla.com/news/gas', 'FOX 11 Los Angeles', 'KTTV', 'FOX', 'TV'),
       mk('AAAAAAAAAAA', 'https://ktla.com/news/budget', 'KTLA 5', 'KTLA', 'CW', 'TV'),
       mk('BBBBBBBBBBB', 'https://abc7.com/fire', 'ABC7', 'KABC', 'ABC', 'TV'),
       mk('CCCCCCCCCCC', 'https://nowhere.example/none', 'KTLA 5', 'KTLA', 'CW', 'TV')]      # row not found -> listed
T2 = ST.Task(ST.Sheet(p2), {'pages': {}, 'runs': {'r2': {'at': '2026-10-30T10:00:00Z', 'attach': att}}}, '2026-10-30')
res2 = T2.run(None); ST.rebuild_originals(T2.s)
out2 = tempfile.mktemp(suffix='.xlsx'); T2.s.wb.save(out2)
w2 = openpyxl.load_workbook(out2); avr = {r[0]: dict(zip([c.value for c in w2['Audio & video details'][1]], r)) for r in w2['Audio & video details'].iter_rows(min_row=2, values_only=True)}
g2 = lambda aid, c: T2.s.get(T2.s.rows[aid], c)
ok(g2('00100', 'Format') == 'Broadcast segment' and g2('00101', 'Format') == 'Broadcast segment' and g2('00102', 'Format') == 'Broadcast segment', 'attach: each tracked story\'s Format becomes Broadcast segment (override of an Article / Video clip value)')
ok(g2('00101', 'Medium') == 'TV' and g2('00100', 'Medium') == 'TV', 'attach: Medium Video becomes TV (from the channel map); TV stays')
ok(g2('00100', 'File name') == 'saved.html' and g2('00100', 'Saved Copy?') == 'Yes' and g2('00100', 'Headline') == 'Gas rebate debated' and g2('00102', 'Team note') == 'checked', 'attach: the saved copy and every other filled cell stay')
x = avr['00100']; ok(x['Item type'] == 'Broadcast segment' and x['Channel'] == 'FOX 11 Los Angeles' and x['Station'] == 'KTTV' and x['Network'] == 'FOX' and x['YouTube link'] == att[0]['link'], 'attach: existing AV row: Item type overridden, blank Channel / Station / Network / YouTube link filled')
x = avr['00102']; ok(x['Item type'] == 'Broadcast segment' and x['Channel'] == 'ABC7 Los Angeles' and x['Station'] == 'KABC' and x['YouTube link'] == att[2]['link'], 'attach: a filled Channel is kept (blanks only), the rest filled')
x = avr.get('00101') or {}; ok(x.get('Item type') == 'Broadcast segment' and x.get('Channel') == 'KTLA 5' and x.get('Station') == 'KTLA' and x.get('Network') == 'CW' and x.get('Episode/segment title') == 'Budget vote'
   and x.get('YouTube link') == att[1]['link'] and x.get('Details from') == 'YouTube page' and x.get('Medium') == 'TV' and x.get('Story ID') == 's00101', 'attach: a row with no AV row gets one (Item type, Channel, Station, Network, title = headline, YouTube link, Details from YouTube page)')
ok(len(res2['yt_attached']) == 3 and len(res2['yt_attach_unplaced']) == 1 and 'not found' in res2['yt_attach_unplaced'][0]['why'], 'attach: 3 placed, the unfound row is listed for review')
ok(max(T2.s.rows.values()) == 4 and not res2['runs'], 'attach: no new story or Coverage row is added')
wo = w2['Originals']; oh = [c.value for c in wo[1]]; orow = [dict(zip(oh, r)) for r in wo.iter_rows(min_row=2, values_only=True) if r[oh.index('Article ID')] == '00101']
ok(orow and orow[0]['Format'] == 'Broadcast segment' and orow[0]['Medium'] == 'TV', 'attach: the Originals tab mirrors the Coverage change')
v2 = ST.verify(p2, out2, res2); ok(v2['ok'], 'attach: verify passes: ' + json.dumps(v2['problems'][:3]))
vt = ST.verify_tabs(p2, out2, res2); ok(not vt[0], 'attach: verify_tabs passes (Item type override allowed): ' + json.dumps(vt[0][:3]))
T3 = ST.Task(ST.Sheet(out2), {'pages': {}, 'runs': {'r2': {'at': '2026-10-30T10:00:00Z', 'attach': att}}}, '2026-10-30')
res3 = T3.run(None); ok(len(res3['yt_attached']) == 0, 'attach: running the same run again changes nothing')
# the reprint path: a station video that is a reprint of a tracked story is Broadcast segment with an AV row
rp = {'Article ID': 'NEW-r3-1', 'Story ID': 's00101', 'Original or reprint': 'Reprint', 'Data Source': 'Web search (TinyFish, YouTube station channel)', 'Date': '2026-10-21', 'Outlet': 'FOX 11 Los Angeles',
      'Headline': 'Budget vote, on video', 'Edition': 'Web', 'Language': 'English', 'Medium': 'TV', 'Format': 'Broadcast segment', 'Publisher link': 'https://www.youtube.com/watch?v=DDDDDDDDDDD', 'Link status': 'Publisher URL',
      '_av': dict(AVV, **{'YouTube link': 'https://www.youtube.com/watch?v=DDDDDDDDDDD'})}
T4 = ST.Task(ST.Sheet(p2), {'pages': {}, 'runs': {'r3': {'at': '2026-10-30T10:00:00Z', 'rows': [rp]}}}, '2026-10-30')
res4 = T4.run(None); r4 = T4.s.rows.get(res4['runs']['r3']['ids']['NEW-r3-1'])
ok(r4 is not None and T4.s.get(r4, 'Format') == 'Broadcast segment' and T4.s.get(r4, 'Original or reprint') == 'Reprint', 'reprint path: the station video is added as a Reprint with Format Broadcast segment (not Video clip)')
print(f'ALL {n} CHECKS PASSED')
