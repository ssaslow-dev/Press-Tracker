#!/usr/bin/env python3
"""CHAINCHECK-v1: one automated end-to-end check that the PC tracker and the Update station still work together.

    python3 -I work/localapp/chaincheck/run_chaincheck.py [--pc-build DIR] [--station-html FILE] [--workbook FILE] [--published] [--scratch DIR]

Steps (README.md has the details):
  1  PC tracker: "Make for Update file" in the page, the downloaded JSON is captured
  2  Update station page loads that file (format version, story count, fingerprint, no age warning)
  3  stubbed Update (2 new web stories, 1 YouTube station clip, 1 reprint candidate) + a NewsBank PDF (real layout) + a ProQuest export, update zip downloaded
  4  PC tracker: Bring in update (fingerprint match, preview, names), Save (backup, ledger, new stories in the page, library files at their NAMING-v2 paths)
  5  Make refresh file; a reader copy brings it in and shows the same stories
  6  PASS/FAIL table, exit code, report in SCRATCH/chaincheck/last_report.md
Nothing real is touched: the workbook is a copy, the PC copy runs from a hard-linked working copy, TinyFish and Claude are canned, nothing leaves 127.0.0.1.
Exit codes: 0 all passed, 1 a check failed, 2 the check could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
import pc  # noqa: E402

DEFAULT_SCRATCH = Path('/tmp/claude-0/-home-user-Press-Tracker/ec7aac73-d461-552b-aaac-9f8ebc5e7581/scratchpad/chaincheck')
PUBLISHED_URL = 'https://claude.ai/artifact/5uGsM8yQMphjAQbKhvc5SL'

ROWS = []   # (step, check, ok, detail)
STEP = ['']


def step(name):
    STEP[0] = name
    print(f'\n== {name}', flush=True)


def check(name, ok, detail=''):
    ok = bool(ok)
    ROWS.append((STEP[0], name, ok, '' if ok else str(detail)[:600]))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  -> ' + str(detail)[:300]), flush=True)
    return ok


def run(cmd, **kw):
    print('$', ' '.join(str(c) for c in cmd)[:220], flush=True)
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding='utf-8', errors='replace', **kw)


def ledger(root: Path):
    f = root / 'data' / 'state' / 'ledger.jsonl'
    return [json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip()] if f.exists() else []


def wbfile(root: Path) -> Path:
    return next((root / 'data' / 'workbook').glob('*.xlsx'))


def coverage_count(path: Path):
    """number of data rows on the Coverage tab, and the whole text of its NewsBank link cells (to see whether a known link was added again)"""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['Coverage'] if 'Coverage' in wb.sheetnames else wb[wb.sheetnames[0]]
    n, blob = 0, []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if any(c not in (None, '') for c in row):
            n += 1
            blob.append(' '.join(str(c) for c in row if c is not None))
    wb.close()
    return n, '\n'.join(blob)


# ------------------------------------------------------------------------------------------------ set-up

def prepare(a, S: Path):
    S.mkdir(parents=True, exist_ok=True)
    info = {}
    # --- PC build
    if a.pc_build:
        build = Path(a.pc_build)
        if not (build / 'python').is_dir() and (build / 'linux' / 'AJG Tracker').is_dir():
            build = build / 'linux' / 'AJG Tracker'
        info['build_how'] = f'reused {build}'
    else:
        wb_src = Path(a.workbook) if a.workbook else (S.parent / 'wb_0bccc1fc.xlsx')
        if not wb_src.is_file():
            wb_src = REPO / 'data' / 'AJG Coverage - NewsBank.xlsx'
        orig_sha = pc.sha(wb_src)
        info['workbook_source'] = f'{wb_src} ({orig_sha[:8]})'
        info['_orig_wb'] = (wb_src, orig_sha)
        inp = S / 'build_in'
        shutil.rmtree(inp, ignore_errors=True)
        inp.mkdir(parents=True)
        shutil.copy2(wb_src, inp / 'AJG Coverage - NewsBank.xlsx')
        out = S / 'pcbuild'
        shutil.rmtree(out, ignore_errors=True)
        live = Path(a.live_site) if a.live_site else S.parent / 'live_v65'
        legacy = Path(a.legacy) if a.legacy else live / 'pipeline' / 'legacy_index.html'
        r = run([sys.executable, '-I', REPO / 'work' / 'localapp' / 'app' / 'assemble_app.py', '--target', 'linux', '--role', 'keeper', '--out', out,
                 '--workbook', inp / 'AJG Coverage - NewsBank.xlsx', '--library-mode', 'hardlink', '--live-site', live, '--legacy', legacy])
        (S / 'assemble.log').write_text(r.stdout + '\n' + r.stderr, encoding='utf-8')
        if r.returncode:
            raise RuntimeError('assembling the PC test build failed (see ' + str(S / 'assemble.log') + '): ' + (r.stderr or r.stdout)[-400:])
        build = out / 'linux' / 'AJG Tracker'
        info['build_how'] = f'assembled now in {out}'
    if not (build / 'python' / 'bin' / 'python').exists():
        raise RuntimeError(f'{build} is not a Linux test build (python/bin/python missing); build one with assemble_app.py --target linux --role keeper')
    info['build'] = build
    info['wb_sha'] = pc.sha(wbfile(build))
    # --- station page
    if a.station_html:
        page = Path(a.station_html)
        info['station_how'] = ('copy of the PUBLISHED page ' if a.published else 'file ') + str(page)
    else:
        page = REPO / 'work' / 'localapp' / 'station' / 'dist' / 'index.html'
        if not page.is_file():
            r = run([sys.executable, '-I', REPO / 'work' / 'localapp' / 'station' / 'build_station.py'])
            if r.returncode or not page.is_file():
                raise RuntimeError('building the station failed: ' + (r.stderr or r.stdout)[-400:])
        info['station_how'] = f'{page} (station dist build)'
    if not page.is_file():
        raise RuntimeError(f'station page not found: {page}')
    info['page'] = page
    info['page_sha'] = pc.sha(page)
    return info


# ------------------------------------------------------------------------------------------------ the steps

def step1(info, S, work):
    step('1 PC makes the for-Update file')
    root = pc.make_work(info['build'], work, 'keeper', 'keeper')
    K = pc.Server(root).start()
    info['K'], info['keeper_root'] = K, root
    wb0 = pc.sha(wbfile(root))
    info['wb0'] = wb0
    cov0, blob0 = coverage_count(wbfile(root))
    info['cov0'], info['blob0'] = cov0, blob0
    dl = work / 'for_update_download.json'
    dl.unlink(missing_ok=True)
    out = pc.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'download', 'text': 'Make "for Update" file', 'save': str(dl), 'timeout': 600000},
                    {'op': 'panel', 'name': 'p'}], '01', work)
    r = out['results']
    check('the page loads and the button downloads a file', 'crash' not in r and dl.is_file(), r.get('crash') or r)
    if not dl.is_file():
        return False
    name = r.get('download', '')
    fu_path = work / name
    shutil.copy2(dl, fu_path)
    info['fu_path'] = fu_path
    d = json.loads(fu_path.read_text(encoding='utf-8'))
    info['fu'] = d
    check('named for_update_<date>_<sha8>.json', name.startswith('for_update_') and name.endswith(f'_{wb0[:8]}.json'), name)
    check('format ajg-for-update, format_version 1', d.get('format') == 'ajg-for-update' and d.get('format_version') == 1, (d.get('format'), d.get('format_version')))
    check('fingerprint is the workbook sha256', d['fingerprint']['workbook_sha256'] == wb0, d['fingerprint'])
    check('story count matches the page (3,000+), no article text carried', len(d['stories']) > 3000 and 'text_en' not in d['stories'][0], len(d['stories']))
    check('also kept in data/for_update; panel says it was made', bool(list((root / 'data' / 'for_update').glob('for_update_*.json'))) and 'Made for_update_' in r.get('p', ''), r.get('p', '')[:400])
    check('no page errors', not out['errors'], out['errors'][:3])
    return True


def step23(info, S, work):
    inputs = work / 'inputs'
    r = run([sys.executable, '-I', HERE / 'make_inputs.py', info['fu_path'], inputs, info['build'] / 'data' / 'copies'])
    if r.returncode:
        step('2 make test inputs')
        check('synthetic NewsBank PDF and ProQuest export made', False, r.stderr[-500:])
        return False
    st_out = work / 'station'
    shutil.rmtree(st_out, ignore_errors=True)
    env = dict(os.environ, PLAYWRIGHT_MODULE=pc.NODE_MODULES)
    cmd = ['node', HERE / 'station_drive.js', '--page', info['page'], '--file', info['fu_path'], '--inputs', inputs, '--out', st_out]
    if info['published']:
        cmd += ['--wrap', 'no']
    p = run(cmd, env=env, timeout=1800)
    (work / 'station_driver.log').write_text(p.stdout + '\n' + p.stderr, encoding='utf-8')
    rf = st_out / 'station_results.json'
    if not rf.is_file():
        step('2 Update station loads the file')
        check('the station driver ran', False, (p.stderr or p.stdout)[-600:])
        return False
    res = json.loads(rf.read_text(encoding='utf-8'))
    for c in res['checks']:
        if c['step'] != STEP[0]:
            step(c['step'])
        check(c['name'], c['ok'], c['extra'])
    info['station_res'], info['plan'] = res, json.loads((inputs / 'plan.json').read_text(encoding='utf-8'))
    step('3 update zip contents')
    if not res.get('zip'):
        check('the update zip was downloaded', False, 'no zip')
        return False
    zp = Path(res['zip'])
    info['zip'] = zp
    z = zipfile.ZipFile(zp)
    names = z.namelist()
    man = json.loads(z.read('manifest.json'))
    info['manifest'] = man
    check('manifest: ajg-update-folder, fingerprint = the for-Update file\'s workbook', man.get('format') == 'ajg-update-folder' and man['source']['workbook_sha256'] == info['wb0'], man.get('source'))
    items = man.get('names', {}).get('items', [])
    need = [x for i in items for x in (i['copy'], i['raw'], i['pdf']) if x]
    check('names block: every library file it lists is in the zip, nothing else under library/', sorted(need) == sorted(n for n in names if n.startswith('library/')), (sorted(need), [n for n in names if n.startswith('library/')]))
    kinds = sorted((i['fmt'], i['kind']) for i in items)
    check('names: 3 web stories + 1 reprint (ws), 1 NewsBank (nb), 1 ProQuest (pq)', kinds == [('nb', 'o'), ('pq', 'o'), ('ws', 'o'), ('ws', 'o'), ('ws', 'o'), ('ws', 'r')], kinds)
    nx = info['fu']['rows']['next']
    check('names: numbers run on from the file\'s rows.next', [int(i['aid']) for i in items] == list(range(nx['aid'], nx['aid'] + len(items))), [i['aid'] for i in items])
    return True


FIND_JS = "JSON.parse(document.getElementById('data').textContent)"


def step4(info, S, work):
    step('4 PC brings in the update and saves')
    K, root = info['K'], info['keeper_root']
    zp, plan, res = info['zip'], info['plan'], info['station_res']
    wb0 = info['wb0']
    d0 = len(info['fu']['stories'])
    out = pc.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'file', 'path': str(zp)},
                    {'op': 'wait_text', 'text': ['If you press Save', 'refused', 'Use it anyway', 'Nothing was saved'], 'timeout': 1500000, 'name': 'prev'},
                    {'op': 'screenshot', 'path': str(work / 'pc_preview.png')},
                    {'op': 'mark'}, {'op': 'click', 'text': 'Save'},
                    {'op': 'wait_text', 'text': ['Saved.', 'Not saved'], 'timeout': 1800000, 'name': 'saved'},
                    {'op': 'screenshot', 'path': str(work / 'pc_saved.png')}, {'op': 'wait_reload'},
                    {'op': 'eval', 'name': 'hls', 'expr': FIND_JS + '.map(r => r.hl || "")'},
                    {'op': 'eval', 'name': 'reps', 'expr': FIND_JS + '.map(r => [r.id, (r.reps || []).map(x => x.link)])'},
                    {'op': 'eval', 'name': 'cap', 'expr': "document.getElementById('helloCap').textContent"},
                    {'op': 'eval', 'name': 'tab', 'expr': "(() => { const e = [...document.querySelectorAll('button,a,[role=tab],nav *')].find(x => /^\\s*Clips\\s*$/.test(x.textContent) && x.offsetParent); if (e) e.click(); return !!e; })()"},
                    {'op': 'wait', 'ms': 1500},
                    {'op': 'eval', 'name': 'indexed', 'expr': "new Promise(res => { const t0 = Date.now(); (function w(){ if (!/Indexing/.test(document.getElementById('q').placeholder) || Date.now() - t0 > 180000) res(document.getElementById('q').placeholder); else setTimeout(w, 500); })(); })"},
                    {'op': 'eval', 'name': 'typed', 'expr': "(() => { const q = document.getElementById('q'); q.value = 'chaincheck'; q.dispatchEvent(new Event('input', {bubbles:true})); return true; })()"},
                    {'op': 'wait', 'ms': 3000},
                    {'op': 'eval', 'name': 'hits', 'expr': "[...document.querySelectorAll('#tbody tr[data-id]')].map(t => t.innerText.slice(0,160))"},
                    {'op': 'eval', 'name': 'typed2', 'expr': "(() => { const q = document.getElementById('q'); q.value = 'ccmarkweb1'; q.dispatchEvent(new Event('input', {bubbles:true})); return true; })()"},
                    {'op': 'wait', 'ms': 3000},
                    {'op': 'eval', 'name': 'hits2', 'expr': "[...document.querySelectorAll('#tbody tr[data-id]')].map(t => t.innerText.slice(0,160))"},
                    {'op': 'screenshot', 'path': str(work / 'pc_search.png')}], '04b', work)
    r = out['results']
    prev = r.get('prev_panel', '')
    (work / 'preview_panel.txt').write_text(prev, encoding='utf-8')
    check('accepted: the fingerprint matches (no "different version" warning), nothing refused', r.get('prev') == 'If you press Save' and 'different version of the workbook' not in prev, prev[:500])
    check('preview says new rows would be added to the Coverage tab', 'added to the Coverage tab' in prev, prev[:600])
    check('preview: names confirmed (as the station named them), none renamed, none unsaved', 'were as the station named them' in prev and 'renamed to the names' not in prev and 'were not saved' not in prev and 'Not saved to the library' not in prev, prev[:1200])
    if r.get('prev') != 'If you press Save':
        return False
    info['preview'] = prev
    saved = r.get('saved_panel', '')
    (work / 'saved_panel.txt').write_text(saved, encoding='utf-8')
    check('Save finished: "Saved."', r.get('saved') == 'Saved.', saved[:600])
    check('panel names the backup of the old workbook', 'Backup of the old workbook' in saved, saved[:600])
    wb1 = pc.sha(wbfile(root))
    info['wb1'] = wb1
    check('the workbook changed', wb1 != wb0)
    bks = list((root / 'data' / 'backups').glob('*.xlsx'))
    check('a backup of the old workbook exists (same bytes as before)', [pc.sha(b) for b in bks] == [wb0], [pc.sha(b)[:8] for b in bks])
    lg = ledger(root)
    last = lg[-1] if lg else {}
    check('the ledger has the save (after_sha = new workbook, confirmed)', last.get('verb') == 'save' and last.get('after_sha') == wb1 and last.get('confirmed') is True, last)
    check('page reloaded after the save, no page errors', 'crash' not in r and not out['errors'], (r.get('crash'), out['errors'][:3]))
    # workbook rows
    cov1, blob1 = coverage_count(wbfile(root))
    man_items = info['manifest']['names']['items']
    check(f'Coverage tab grew by {len(man_items)} rows (5 stories + 1 reprint)', cov1 - info['cov0'] == len(man_items), (info['cov0'], cov1))
    kd = plan['nb']['known']['docref'].lower()
    check('the known NewsBank story was not added again (its docref appears as often as before)', blob1.lower().count(kd) == info['blob0'].lower().count(kd), (info['blob0'].lower().count(kd), blob1.lower().count(kd)))
    # stories in the page
    hls = r.get('hls') or []
    exp = [a['hl'] for a in res['expect']['web']] + [res['expect']['yt']['hl'], plan['nb']['new']['hl'], plan['pq']['hl']]
    miss = [h for h in exp if not any(h in x for x in hls)]
    check('the 5 new stories are in the page after the reload (2 web, 1 YouTube clip, 1 NewsBank, 1 ProQuest)', not miss, miss)
    check('the page has 5 more stories than the for-Update file', len(hls) == d0 + 5, (d0, len(hls)))
    ex2 = res['expect']['rep']
    rr = {i: l for i, l in (r.get('reps') or [])}
    check('the reprint is attached to the story the tracker already had', ex2['url'] in rr.get(ex2['story'], []), rr.get(ex2['story']))
    check('the known NewsBank story is still one story (headline count unchanged)', sum(1 for x in hls if plan['nb']['known']['hl'] in x) == sum(1 for x in info['fu']['stories'] if plan['nb']['known']['hl'] in x['hl']), '')
    hits, hits2 = r.get('hits') or [], r.get('hits2') or []
    check('Clips search "chaincheck" finds the new stories', len(hits) >= 5 and all(any(h in x for x in hits) for h in ['Gabriel unveils bill', 'Gabriel presenta', 'wildfire insurance', 'wildfire recovery fund', 'school meal']), (r.get('indexed'), hits))
    check('Clips search finds a word from inside the saved web copy (ccmarkweb1)', any('quokka' in x.lower() for x in hits2), (r.get('indexed'), hits2))
    # library files at the NAMING-v2 paths (the station's names; if the save gave a file another name, its own name is followed so later checks go on, and the rename itself fails a check)
    import re
    renames = dict(re.findall(r'(\S+) -> (\S+?) \(', saved))
    lib = root / 'data' / 'library'
    miss, final = [], {}
    for i in man_items:
        for key in ('copy', 'raw', 'pdf'):
            p = i[key]
            if not p:
                continue
            f = lib / p[len('library/'):]
            if not f.is_file():
                stem, ext = os.path.splitext(f.name)
                alt = f.with_name(renames.get(stem, stem) + ext) if stem in renames else None
                if alt and alt.is_file():
                    f = alt
            final[p] = f
            if not f.is_file() or f.stat().st_size < 200:
                miss.append(p)
    check('every library file is at its NAMING-v2 path (ws/nb/pq names, year folders, _original_html, _original_pdf)', not miss, miss)
    check('the save kept every name the station gave (no file renamed, none left unsaved)', not renames and 'were not saved' not in saved and 'Not saved to the library' not in saved, [saved[saved.find('renamed') - 20:saved.find('renamed') + 400] if renames else '', [l for l in saved.splitlines() if 'not saved' in l.lower() or 'Not saved' in l]])
    z = zipfile.ZipFile(zp)
    diff = [i['copy'] for i in man_items if i['copy'] and final[i['copy']].is_file() and hashlib.sha256(final[i['copy']].read_bytes()).hexdigest() != hashlib.sha256(z.read(i['copy'])).hexdigest() and not i['copy'].endswith('.html')]
    check('the saved PDFs are byte for byte the ones the station made', not diff, diff)
    check('saved copies are readable pages (the web ones carry their marker word)', any('ccmarkweb1' in final[i['copy']].read_text(encoding='utf-8', errors='replace') for i in man_items if i['fmt'] == 'ws' and i['copy'] and final[i['copy']].is_file()), '')
    info['final'] = final
    check('the run docs reached the PC db (runs)', len(list((root / 'data' / 'db' / 'runs').glob('run-*.json'))) >= 3, list((root / 'data' / 'db').glob('*')))
    check('the same zip cannot be taken in twice', second_take_refused(K, zp), '')
    return True


def second_take_refused(K, zp):
    st, j = K.call('POST', f'/_local/station/upload?kind=update&name={zp.name}', raw=zp.read_bytes())
    if st != 200:
        return False
    res = K.job('inspect', {'file': j['file']})
    return (not res.get('ok')) and res.get('refused') == 'ALREADY_SAVED'


def step5(info, S, work):
    step('5 refresh file to a reader copy')
    K, root = info['K'], info['keeper_root']
    res = info['station_res']
    out = pc.ui(K, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'click', 'text': 'Make refresh file'},
                    {'op': 'wait_text', 'text': ['Made the', 'could not be made', 'Another save'], 'timeout': 600000, 'name': 'mk'}], '05a', work)
    r = out['results']
    check('the keeper makes a refresh file', r.get('mk') == 'Made the', r.get('mk_panel', r.get('crash', ''))[:500])
    zs = sorted((root / 'data' / 'refresh_out').glob('refresh_*.zip'))
    if not zs:
        return False
    rz = work / zs[-1].name
    shutil.copy2(zs[-1], rz)
    rroot = pc.make_work(info['build'], work, 'reader', 'reader')
    R = pc.Server(rroot).start()
    info['R'] = R
    before = pc.sha(wbfile(rroot))
    check('the reader copy starts from the old workbook', before == info['wb0'], before[:8])
    out = pc.ui(R, [{'op': 'goto'}, {'op': 'open_panel'}, {'op': 'file', 'path': str(rz)}, {'op': 'mark'},
                    {'op': 'wait_text', 'text': ['is in.', 'Nothing was changed', 'refused'], 'timeout': 900000, 'name': 'done'},
                    {'op': 'wait_reload'},
                    {'op': 'eval', 'name': 'hls', 'expr': FIND_JS + '.map(r => r.hl || "")'}], '05b', work)
    r = out['results']
    check('the reader copy takes the refresh file ("is in.")', 'is in.' in r.get('done_panel', ''), r.get('done_panel', r.get('crash', ''))[-500:])
    hls = r.get('hls') or []
    plan = info['plan']
    exp = [a['hl'] for a in res['expect']['web']] + [res['expect']['yt']['hl'], plan['nb']['new']['hl'], plan['pq']['hl']]
    miss = [h for h in exp if not any(h in x for x in hls)]
    check('the reader shows the same 5 new stories', not miss and len(hls) == len(info['fu']['stories']) + 5, miss or (len(hls),))
    check('the reader\'s workbook is byte for byte the keeper\'s', pc.sha(wbfile(rroot)) == info['wb1'])
    man_items = info['manifest']['names']['items']
    miss = []
    for i in man_items:
        for key in ('copy', 'raw', 'pdf'):
            if i[key]:
                a = info['final'][i[key]]
                b = rroot / 'data' / 'library' / a.relative_to(root / 'data' / 'library')
                if not b.is_file() or pc.sha(a) != pc.sha(b):
                    miss.append(i[key])
    check('the reader has the same library files at the same paths', not miss, miss)
    check('reader page identical to the keeper\'s', pc.sha(rroot / 'data' / 'site' / 'index.html') == pc.sha(root / 'data' / 'site' / 'index.html'))
    check('no page errors on the reader', not out['errors'], out['errors'][:3])
    return True


# ------------------------------------------------------------------------------------------------ report

def report(info, S, started, crash=None):
    ok = all(r[2] for r in ROWS) and not crash and bool(ROWS)
    steps = []
    for s, n, o, d in ROWS:
        if s not in steps:
            steps.append(s)
    lines = [f'# Chain check (CHAINCHECK-v1): {"PASS" if ok else "FAIL"}', '',
             f'- run: {time.strftime("%Y-%m-%d %H:%M:%S")} ({int(time.time() - started)} s)',
             f'- workbook copy: {info.get("workbook_source", "(build as given)")}; sha256 in the PC build `{info.get("wb0", "?")[:8]}`',
             f'- PC build: {info.get("build_how", "?")}', f'- station page: {info.get("station_how", "?")} (sha256 {info.get("page_sha", "?")[:12]})',
             f'- mode: {"PUBLISHED copy" if info.get("published") else "local dist build"}']
    if crash:
        lines += ['', f'**The check could not finish:** {crash}']
    lines += ['', '| Step | Result | Checks |', '|---|---|---|']
    for s in steps:
        rs = [r for r in ROWS if r[0] == s]
        bad = [r for r in rs if not r[2]]
        lines.append(f'| {s} | {"FAIL" if bad else "PASS"} | {len(rs) - len(bad)} of {len(rs)} |')
    lines += ['', '## Every check', '', '| Step | Check | Result | Detail |', '|---|---|---|---|']
    for s, n, o, d in ROWS:
        lines.append(f'| {s} | {n} | {"PASS" if o else "FAIL"} | {d.replace("|", "/").replace(chr(10), " ")[:300]} |')
    txt = '\n'.join(lines) + '\n'
    for dest in (S / 'chaincheck', S):
        dest.mkdir(parents=True, exist_ok=True)
        (dest / 'last_report.md').write_text(txt, encoding='utf-8')
    print('\n' + '=' * 70)
    print('CHAIN CHECK:', 'PASS' if ok else 'FAIL', '\n')
    w = max([len(s) for s in steps] + [4])
    for s in steps:
        rs = [r for r in ROWS if r[0] == s]
        bad = [r for r in rs if not r[2]]
        print(f'  {"FAIL" if bad else "PASS"}  {s.ljust(w)}  {len(rs) - len(bad)}/{len(rs)}')
        for r in bad:
            print(f'          - {r[1]}: {r[3][:200]}')
    if crash:
        print('\n  could not finish:', crash)
    print('\nreport:', S / 'chaincheck' / 'last_report.md')
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--pc-build', help='an assembled Linux test build ("AJG Tracker" folder, or the --out folder that holds linux/AJG Tracker); default: assemble one from --workbook')
    ap.add_argument('--station-html', help='the station page to test (default work/localapp/station/dist/index.html, built if missing)')
    ap.add_argument('--workbook', help='the workbook copy to build the PC test build from (default: SCRATCH/../wb_0bccc1fc.xlsx). It is copied, never written.')
    ap.add_argument('--published', action='store_true', help='--station-html is a copy of the PUBLISHED page (saved with the Artifact tool\'s read action); it is served as it is, not wrapped (see README)')
    ap.add_argument('--live-site'); ap.add_argument('--legacy')
    ap.add_argument('--scratch', help='working folder (default ' + str(DEFAULT_SCRATCH) + ' or $CHAINCHECK_SCRATCH)')
    a = ap.parse_args()
    S = Path(a.scratch or os.environ.get('CHAINCHECK_SCRATCH') or DEFAULT_SCRATCH)
    if a.published and not a.station_html:
        print('--published needs --station-html FILE: save the published page first (README, "Testing the published page")', file=sys.stderr)
        return 2
    started = time.time()
    info = {'published': a.published}
    crash = None
    work = S / 'work'
    try:
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        info.update(prepare(a, S))
        orig = info.pop('_orig_wb', None)
        if step1(info, S, work):
            if step23(info, S, work):
                if step4(info, S, work):
                    step5(info, S, work)
        if orig:
            check_sha = pc.sha(orig[0]) == orig[1]
            step('6 nothing real was touched')
            check('the workbook copy given is unchanged', check_sha)
    except Exception as e:   # noqa: BLE001
        crash = f'{type(e).__name__}: {e}'
        traceback.print_exc()
    finally:
        for k in ('K', 'R'):
            if info.get(k):
                info[k].stop()
    ok = report(info, S, started, crash)
    if crash and not ROWS:
        return 2
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
