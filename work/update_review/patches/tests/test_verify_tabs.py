"""VERIFYTABS-v1 (REQ-3): verify() covers every tab. Usage: python3 -I build/tests/sheet_task/test_verify_tabs.py   (exit 0 = all pass)
1. CONTRACT worked example (fixture workbook + example_db.json) with Bills / Press releases / Audio & video details tabs added: verify.ok, tabs listed.
2. same inputs; Task.apply_av also overwrites one non-blank AV cell, Task.apply_bills one Bills cell: verify not ok, both named.
3. same inputs; one hyperlink on Press releases dropped before save: problem names the tab and counts.
4. same inputs; Press releases derived cell changes (allowed), an AV row moved to Removed via res (allowed) are not problems; a Press releases row dropped is."""
import os, sys, json, tempfile, shutil, importlib
L = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(L, 'code'))
import openpyxl
import sheet_task as ST

FIX = os.path.join(L, 'build/tests/sheet_task/fixtures')
DB = os.path.join(FIX, 'example_db.json')
XLSX = os.path.join(FIX, 'work/tmp_agent-ids/migrated_current.xlsx')
IDMAP = os.path.join(FIX, 'work/tmp_agent-ids/blocks_post/idmap.json')
TMP = tempfile.mkdtemp(prefix='verify_tabs_')
fails = 0


def ok(c, m, info=''):
    global fails
    print(('PASS ' if c else 'FAIL ') + m + ('' if c else '  -- ' + str(info)[:600]))
    fails += (not c)


def augmented():
    p = os.path.join(TMP, 'in.xlsx')
    wb = openpyxl.load_workbook(XLSX)
    b = wb.create_sheet('Bills'); b.append(['Bill', 'Session', 'Date', 'Milestone', 'Detail', 'Final status'])
    for i in range(1, 6):
        b.append(['AB %d' % i, '2025-2026', '2026-01-%02d' % i, 'Introduced', 'detail %d' % i, 'Pending'])
    pr = wb.create_sheet('Press releases')
    pr.append(['Release ID', 'Date', 'Title', 'URL', 'Issue', 'Related count', 'Related story IDs'])
    for i in range(1, 4):
        pr.append(['pr-%d' % i, '2026-02-0%d' % i, 'Release %d' % i, 'https://example.test/r%d' % i, 'Issue %d' % i, 1, 's00037'])
        pr.cell(i + 1, 4).hyperlink = 'https://example.test/r%d' % i
    av = wb.create_sheet('Audio & video details'); av.append(['Article ID', 'Story ID', 'Medium', 'Item type', 'Channel'])
    for i in range(1, 4):
        av.append(['09%03d' % (900 + i), 's0000%d' % i, 'Video', 'Clip', 'Channel %d' % i])
    rm = wb.create_sheet('Removed'); rm.append(['From tab', 'Reason removed', 'Removed on', 'Category', 'Article ID'])
    wb.save(p)
    return p


def run(tag, setup=None):
    """one sheet_task.main run on the augmented workbook; returns result.json"""
    out, res = os.path.join(TMP, tag + '.xlsx'), os.path.join(TMP, tag + '.json')
    pages = os.path.join(TMP, tag + '_pages'); os.makedirs(pages, exist_ok=True)
    importlib.reload(ST)
    undo = setup(ST) if setup else None
    try:
        rc = ST.main(['--db', DB, '--xlsx', IN, '--out', out, '--result', res, '--pages-dir', pages, '--idmap', IDMAP, '--today', '2026-10-27'])
    finally:
        if undo:
            undo()
    return rc, json.load(open(res, encoding='utf-8'))


IN = augmented()
# 1 worked example
rc, r = run('base')
v = r['verify']
ok(rc == 0 and v['ok'], '1: CONTRACT worked example (with the extra tabs) verifies ok', v['problems'])
ok({'Bills', 'Press releases', 'Audio & video details', 'Removed'} <= set(v.get('tabs_checked', [])), '1: tabs_checked lists the other tabs', v.get('tabs_checked'))

# 2 a bug in apply_av / apply_bills changes existing cells
def bug_av_bills(ST_):
    oa, ob = ST_.Task.apply_av, ST_.Task.apply_bills
    def av(self):
        oa(self); ws = self.s.wb['Audio & video details']; ws['E2'].value = 'CHANGED CHANNEL'
    def bills(self):
        ob(self); ws = self.s.wb['Bills']; ws['E3'].value = 'CHANGED DETAIL'
    ST_.Task.apply_av, ST_.Task.apply_bills = av, bills
    return lambda: setattr(ST_.Task, 'apply_av', oa) or setattr(ST_.Task, 'apply_bills', ob)
rc, r = run('bug', bug_av_bills)
v = r['verify']; pr = ' | '.join(v['problems'])
ok(rc == 2 and not v['ok'], '2: verify not ok (exit 2) when AV / Bills cells change', (rc, v['problems']))
ok('Audio & video details' in pr and 'Channel' in pr, '2: AV cell change is named', pr)
ok('Bills' in pr and 'Detail' in pr, '2: Bills cell change is named', pr)

# 3 hyperlink dropped on Press releases
def drop_link(ST_):
    orig = ST_.rebuild_originals
    def rb(sheet):
        ws = sheet.wb['Press releases']; ws.cell(4, 4).hyperlink = None
        return orig(sheet)
    ST_.rebuild_originals = rb
    return lambda: setattr(ST_, 'rebuild_originals', orig)
rc, r = run('link', drop_link)
v = r['verify']; pr = ' | '.join(v['problems'])
ok(not v['ok'] and 'Press releases: hyperlinks dropped 3 -> 2' in pr, '3: dropped hyperlink on Press releases is named with counts', pr)

# 4 allowed changes pass, a lost row does not
def allowed(ST_):
    orig = ST_.rebuild_originals
    def rb(sheet):
        ws = sheet.wb['Press releases']; ws['F2'].value = 7; ws['G2'].value = 's00037; s00001'      # derived columns
        ws.append(['pr-new', '2026-10-27', 'New release', 'https://example.test/new', 'x', 0, ''])  # new row on an allowed tab
        return orig(sheet)
    ST_.rebuild_originals = rb
    return lambda: setattr(ST_, 'rebuild_originals', orig)
rc, r = run('allowed', allowed)
ok(r['verify']['ok'], '4: derived Press releases cells and a new Press releases row are not problems', r['verify']['problems'])
def lose_row(ST_):
    orig = ST_.rebuild_originals
    def rb(sheet):
        sheet.wb['Press releases'].delete_rows(3); sheet.wb['Audio & video details'].delete_rows(3)
        return orig(sheet)
    ST_.rebuild_originals = rb
    return lambda: setattr(ST_, 'rebuild_originals', orig)
rc, r = run('lost', lose_row)
pr = ' | '.join(r['verify']['problems'])
ok(not r['verify']['ok'] and 'Press releases: row missing after: pr-2' in pr and 'Audio & video details: row missing after: 09902' in pr, '4: lost Press releases and AV rows are named', pr)
shutil.rmtree(TMP, ignore_errors=True)
print('ALL %s' % ('CHECKS PASSED' if not fails else '%d FAILED' % fails))
sys.exit(1 if fails else 0)
