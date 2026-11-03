"""Makes app/src/station/data/prjudge_v2.json (PRJUDGE-v2 existing rows) from work/localapp/PRESS_RELEASE_YES_REVIEW.csv and a copy of the real workbook.

    python3 -I work/localapp/app/tools/make_prjudge_list.py WORKBOOK.xlsx

The 228 "should be No" rows of the review split three ways (checked 2026-11-03 on 0bccc1fc): 96 are copies of the office's own releases (their Story ID is a Copy story ID
on the Press releases tab: they stay Yes), 13 are posts on organisation sites (listed for Sammy, not changed), 119 are other issuers' releases or reported items on news
outlets: those become No. The switch-over step re-checks every row on the real workbook at run time; this file is only the candidate list.
Also: the 3 missed wire releases to mark Yes (01190, 01364, 00290; not 01759, which Sammy un-marked on 27 Oct), and s01614 (05166), which is left alone because its
Original 05165 stays Yes (un-marking 05166 alone would leave the story hidden)."""
import csv, json, sys
from pathlib import Path
import openpyxl
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
wbp = Path(sys.argv[1])
wb = openpyxl.load_workbook(wbp, read_only=True, data_only=True)
rows = list(wb['Press releases'].iter_rows(values_only=True)); h = rows[0]
copies = {str(r[i]) for r in rows[1:] for i in (h.index('Copy story ID 1'), h.index('Copy story ID 2')) if r[i]}
cov = list(wb['Coverage'].iter_rows(values_only=True)); ch = cov[0]; ix = {c: i for i, c in enumerate(ch)}
by = {str(r[ix['Article ID']]): r for r in cov[1:] if r[ix['Article ID']]}
rv = list(csv.DictReader(open(REPO / 'work' / 'localapp' / 'PRESS_RELEASE_YES_REVIEW.csv', encoding='utf-8')))
no = [x for x in rv if x['Verdict'] == 'should be No']
item = lambda a, **k: dict(aid=a, sid=str(by[a][ix['Story ID']]), outlet=str(by[a][ix['Outlet']] or ''), headline=str(by[a][ix['Headline']] or '')[:60], kind=str(by[a][ix['Original or reprint']]), **k)
unmark, org, own, skip = [], [], 0, []
for x in no:
    a = x['Article ID']
    if x['Story ID'] in copies:
        own += 1
    elif x['Outlet type'] == 'official':
        org.append(item(a))
    elif a == '05166':
        skip.append(item(a, why='its Original 05165 stays Yes (a wire release), so the story would stay hidden; needs a decision (swap or split s01614)'))
    else:
        unmark.append(item(a))
mark = [item(a) for a in ('01190', '01364', '00290')]
doc = {'about': __doc__.split('\n')[0], 'made_from_workbook_sha': None, 'own_release_copies_kept_yes': own, 'unmark': unmark, 'mark': mark, 'org_posts_listed': org, 'left_alone': skip}
out = REPO / 'work' / 'localapp' / 'app' / 'src' / 'station' / 'data' / 'prjudge_v2.json'
out.write_text(json.dumps(doc, indent=0, ensure_ascii=False) + '\n', encoding='utf-8')
print(len(unmark), len(mark), len(org), own, len(skip))
