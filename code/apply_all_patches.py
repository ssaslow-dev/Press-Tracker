#!/usr/bin/env python3
"""apply_all_patches.py - bring the tracker build inputs and the published pipeline up to date in one idempotent step.

  python3 -I code/apply_all_patches.py [--root L] [--check] [--no-pipeline]
  python3 -I code/apply_all_patches.py --tracker-js OUT     (only write the concatenated tracker JS to OUT, e.g. for a harness)

Since 2026-10-28 (agent-backendclean2, DECISIONS "Button optimization + back-end cleanup") the code is edited directly in its
source files; there are no anchor patches any more. The 20 retired patch scripts (steps 1-4q: LINKS ... OUTLETRULES-v1) are in
code/_history/patches/ with a step -> feature -> DECISIONS table; every one of them was a no-op on the folded sources.

Steps, in this order, under ROOT (default: the lib folder this script sits in):
  1. tracker  build/js_merged.js := concatenation of code/tracker/NN_<section>.js in file-name order (the tracker JS source,
              one file per section; 40-43 = the Update flow). js_merged.js keeps its name because build/build.sh, the harnesses
              and the pipeline (tracker.js) read it. Edit code/tracker/, never js_merged.js: when js_merged.js was edited by
              hand since the last concatenation (sha differs from build/js_merged.js.sha256 and from the new concatenation) the
              run stops without writing anything.
  2. bills    code/gabriel_bills_leginfo.json := work/gabriel_bills_leginfo.json when that differs (AUTO-v1: never an early snapshot)
  3. pipeline build/pub/pipeline/ refreshed from the sources in PIPELINE (skip with --no-pipeline); gabriel_bills_leginfo.json and
              release_texts.json and release_related.json are MERGED, never shrunk (the sheet task appends to them); build/insights/<id>.js + <id>_data.py ->
              pipeline/insights/, build/tabs/<id>.js + <id>_data.py + _common_data.py -> pipeline/tabs/ (files gone from the
              source folder are removed there); work/out/bill_milestones.json -> pipeline/insights/; docs/ = README, DECISIONS,
              CONTRACT, TONE_GUIDE, clean_playbook
  4. verify   py_compile of every Python file the pipeline ships + apply_fills.py + build/tabs|insights/*.py, node --check
              of the tracker JS
A second run changes nothing. Before writing, build/js_merged.js (+ its .sha256 stamp) and code/gabriel_bills_leginfo.json are copied to
ROOT/work/pre_apply_all_<UTC time>/; on any failure they are restored from there and the script exits 1.
--check: run on a scratch copy, report what would change, leave ROOT untouched.
"""
import argparse, datetime, filecmp, glob, hashlib, os, py_compile, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TRACKER_DIR = 'code/tracker'
JS = 'build/js_merged.js'
JS_STAMP = 'build/js_merged.js.sha256'   # sha256 of the last js_merged.js this script wrote
TARGETS = [JS, 'code/gabriel_bills_leginfo.json']
PIPELINE = {'sheet_task.py': 'code/sheet_task.py', 'build_data.py': 'code/build_data.py', 'assemble.py': 'code/assemble.py',
            'tracker.js': JS, 'authorsplit.py': 'code/authorsplit.py', 'clean_html.py': 'code/clean_html.py',
            'clean_rules.json': 'code/clean_rules.json', 'clean_playbook.md': 'build/clean_playbook.md',
            'author_canon.csv': 'code/author_canon.csv',
            'reprint_rule.py': 'code/reprint_rule.py', 'gabriel_bills_leginfo.json': 'code/gabriel_bills_leginfo.json',   # AUTO-v1
            'release_rule.py': 'code/release_rule.py', 'release_texts.json': 'code/release_texts.json',   # RELRULE-v1
            'avtab.py': 'code/avtab.py',   # AVTAB-v1: "Audio & video details" tab (sheet_task.py and build_data.py import it)
            'reltab.py': 'code/reltab.py',   # RELTAB-v1: "Press releases" tab layout (sheet_task.py imports it)
            'sid_map.json': 'work/sid_map.json',   # SIDMAP-v1: legacy jg- codes for build_data.py's idmap in the button's rebuild
            'insights_assemble.py': 'code/insights_assemble.py', 'insights_data.py': 'code/insights_data.py',   # INSIGHTS-v1
            'tabs_assemble.py': 'code/tabs_assemble.py', 'tabs_data.py': 'code/tabs_data.py',   # TABS-v1
            'make_copies.py': 'code/make_copies.py',   # NAMING-v2: viewer copies from the library's current file names (full rebuilds)
            'relpage.py': 'code/relpage.py',   # RELCOPIES-v1 (RELCHECK-v4): a release page -> the tab's facts (sheet_task.py imports it)
            'outlet_rules.json': 'code/outlet_rules.json',   # OUTLETRULES-v1: outlet matching (sheet_task.norm_outlet reads it); REPRINT-v2: types / houses / services
            'reporters.py': 'code/reporters.py', 'reporter_employment.csv': 'code/reporter_employment.csv',   # REPRINT-v2: the reporter's employer (originals order tier 1)
            'wrong_copies.csv': 'code/wrong_copies.csv',   # REPRINT-v2: saved copies known to hold another article (make_copies / sheet_task guard)
            'billmatch.py': 'code/billmatch.py', 'bills_extra.json': 'code/bills_extra.json',   # TAGS-v1: shared names-a-bill rule (sheet_task queue_after, build_data billsinfo)
            'lookup_cache.py': 'code/lookup_cache.py', 'lookup_cache.json': 'code/lookup_cache.json',   # LEARN-v1: answered lookups; sheet_task.fetch_plan / apply_lookups, build_data fetchrules
            'recall_sources.json': 'code/recall_sources.json', 'ems_ca_outlets.json': 'code/ems_ca_outlets.json',   # RECALLFIX-v1: priority outlets / TV caps / podcasts / ethnic-media list (build_data puts them in the fetchrules block)
            'outlets.json': 'code/outlets.json',   # OUTLETREC-v1: one record per outlet (sheet_task.outlet_record)
            'copy_check.py': 'code/copy_check.py',   # COPYCHECK-v1: saved-copy gates (reprint_rule imports it; sheet_task.check_page)
            'dates_lib.py': 'code/dates_lib.py', 'date_rules.py': 'code/date_rules.py',   # DATES-v1: zones, local day, 8 checks, Date source (sheet_task imports)
            'shownet.py': 'code/shownet.py',   # SHOWNET-v1: show vs network split, un-inverted show names, broadcast headlines
            'media_gate.py': 'code/media_gate.py',   # MEDIAGATE-v1: sharing accepts only JPEG/PNG/GIF/WebP, MP4/WebM, MP3/WAV
            'img_embed.py': 'code/img_embed.py',   # PHOTOS-v2: photo cache lookup / save-time embed (make_copies, sheet_task)
            'av_display_clean.py': 'code/av_display_clean.py', 'av_rules.json': 'code/av_rules.json',   # AVPREVIEW-v1 fix A (make_copies)
            'agg_origin.py': 'code/agg_origin.py',   # AGGORIGIN-v1: aggregator finds are never the Original (sheet_task imports it in a try)
            'relmatch.py': 'code/relmatch.py',   # RELRELATED-v1: release -> related stories (Update button, --update)
            'wireblend.py': 'code/wireblend.py',   # WIREBLEND-v1: blend detection (reprint_rule / sheet_task) + build_data add_pickups
            'reporter_record.py': 'code/reporter_record.py', 'reporters.json': 'code/reporters.json',   # REPREC-v1 / REPAFF-v1: reporter record + the one affiliation engine (tab-reporters, reporters.py tenures)
            'release_related.json': 'code/release_related.json',   # RELRELATED-v1 state file: merged (newer rows replace older), never shrunk
            'relthread.py': 'code/relthread.py',   # RELTHREAD-v1: tab-releases thr (releases_data.py imports it)
            'relcopy.py': 'code/relcopy.py',   # RELCOPIES-v2: near-copy / wire-title copy rules (sheet_task.py imports it)
            'shell.html': 'build/shell/shell.html',   # BUTTONOPT T4b: page shell, data blocks stripped (code/make_shell.py); step 6 assembles from it
            'make_shell.py': 'code/make_shell.py',
            # TOKENS-v1: the lean sheet-task prompt, and the project docs the sheet task reads before judgment calls
            'sheet_task_prompt.md': 'code/sheet_task_prompt.md',
            'docs/README.md': 'README.md', 'docs/DECISIONS.md': 'DECISIONS.md', 'docs/CONTRACT.md': 'CONTRACT.md',
            'docs/TONE_GUIDE.md': 'TONE_GUIDE.md', 'docs/clean_playbook.md': 'build/clean_playbook.md'}
# 4. verify: every Python source the pipeline ships, apply_fills.py, and the tab / insights data builders
PY_CHECK = tuple(sorted({'code/apply_fills.py', 'code/apply_all_patches.py'} | {v for v in PIPELINE.values() if v.endswith('.py')}))
PY_DIRS = ('build/tabs', 'build/insights')   # <id>_data.py and _common_data.py


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def tracker_parts(root):
    return sorted(glob.glob(os.path.join(root, TRACKER_DIR, '[0-9][0-9]_*.js')))


def tracker_js(root):
    """the tracker JS = code/tracker/NN_*.js concatenated as bytes, in file-name order"""
    parts = tracker_parts(root)
    if not parts:
        raise SystemExit(f'no {TRACKER_DIR}/NN_*.js under {root}')
    return b''.join(open(p, 'rb').read() for p in parts)


def build_tracker(root, log):
    js, stamp = os.path.join(root, JS), os.path.join(root, JS_STAMP)
    new = tracker_js(root)
    new_sha = hashlib.sha256(new).hexdigest()
    if os.path.exists(js):
        cur = sha(js)
        if cur == new_sha:
            log.append(f'{JS}: unchanged ({len(tracker_parts(root))} parts)')
            if not os.path.exists(stamp) or open(stamp).read().strip() != new_sha:
                open(stamp, 'w').write(new_sha + '\n')
            return True
        last = open(stamp).read().strip() if os.path.exists(stamp) else None
        if cur != last:
            log.append(f'{JS} was edited by hand since the last concatenation (sha {cur[:12]}, last written {str(last)[:12]}): '
                       f'move the edit into {TRACKER_DIR}/ and run again (nothing written)')
            return False
    open(js, 'wb').write(new)
    open(stamp, 'w').write(new_sha + '\n')
    log.append(f'{JS}: rebuilt from {len(tracker_parts(root))} parts in {TRACKER_DIR}/')
    return True


def apply(root, log, pipeline=True):
    P = lambda rel: os.path.join(root, rel)
    # 1. tracker JS from its section files
    if not build_tracker(root, log):
        return False
    # 2. AUTO-v1: Gabriel's bill list is taken from work/gabriel_bills_leginfo.json (never an early snapshot)
    wb_, cb_ = P('work/gabriel_bills_leginfo.json'), P('code/gabriel_bills_leginfo.json')
    if os.path.exists(wb_) and (not os.path.exists(cb_) or not filecmp.cmp(wb_, cb_, shallow=False)):
        shutil.copy2(wb_, cb_)
        log.append('gabriel_bills_leginfo.json taken from work/')
    # 3. pipeline copies
    if pipeline:
        pd_ = P('build/pub/pipeline')
        os.makedirs(pd_, exist_ok=True)
        for name, rel in PIPELINE.items():
            src = P(rel) if os.path.exists(P(rel)) else os.path.join(HERE, os.path.basename(rel))
            if not os.path.exists(src) and rel.endswith('.md'):   # REPO-LOCAL: in this repository the old root's .md files live in docs/
                src = P('docs/' + {'README.md': 'TRACKER_README.md'}.get(rel, rel))
            dst = os.path.join(pd_, name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if name == 'gabriel_bills_leginfo.json' and os.path.exists(dst):   # AUTO-v1: keep bills the sheet task appended
                if merge_bills(src, dst):
                    log.append(f'pipeline/{name} merged')
                continue
            if name == 'release_texts.json' and os.path.exists(dst):   # RELRULE-v1: keep releases the sheet task appended
                if merge_rel_texts(src, dst):
                    log.append(f'pipeline/{name} merged')
                continue
            if name == 'release_related.json' and os.path.exists(dst):   # RELRELATED-v1: keep links the Update button added
                if merge_rel_related(src, dst):
                    log.append(f'pipeline/{name} merged')
                continue
            if not os.path.exists(dst) or not filecmp.cmp(src, dst, shallow=False):
                shutil.copy2(src, dst)
                log.append(f'pipeline/{name} refreshed')
        # INSIGHTS-v1: the views and their data builders (build/insights/<id>.js, <id>_data.py) ride in pipeline/insights/
        ins_src = P('build/insights')
        names = sorted(f for f in (os.listdir(ins_src) if os.path.isdir(ins_src) else [])
                       if not f.startswith('_') and not f.endswith('.test.js') and (f.endswith('_data.py') or f.endswith('.js'))
                       and os.path.isfile(os.path.join(ins_src, f)))
        for f in names:
            src, dst = os.path.join(ins_src, f), os.path.join(pd_, 'insights', f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst) or not filecmp.cmp(src, dst, shallow=False):
                shutil.copy2(src, dst); log.append(f'pipeline/insights/{f} refreshed')
        for f in (os.listdir(os.path.join(pd_, 'insights')) if os.path.isdir(os.path.join(pd_, 'insights')) else []):
            if f not in names and f != 'bill_milestones.json' and os.path.isfile(os.path.join(pd_, 'insights', f)):
                os.remove(os.path.join(pd_, 'insights', f)); log.append(f'pipeline/insights/{f} removed (no longer in build/insights)')
        # TABS-v1: the tab modules and their data builders (build/tabs/<id>.js, <id>_data.py, _common_data.py) ride in pipeline/tabs/
        tab_src = P('build/tabs')
        tnames = sorted(f for f in (os.listdir(tab_src) if os.path.isdir(tab_src) else [])
                        if os.path.isfile(os.path.join(tab_src, f)) and not f.endswith('.test.js')
                        and ((f.endswith('.js') and not f.startswith('_')) or f.endswith('_data.py')))
        for f in tnames:
            src, dst = os.path.join(tab_src, f), os.path.join(pd_, 'tabs', f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst) or not filecmp.cmp(src, dst, shallow=False):
                shutil.copy2(src, dst); log.append(f'pipeline/tabs/{f} refreshed')
        for f in (os.listdir(os.path.join(pd_, 'tabs')) if os.path.isdir(os.path.join(pd_, 'tabs')) else []):
            if f not in tnames and os.path.isfile(os.path.join(pd_, 'tabs', f)):
                os.remove(os.path.join(pd_, 'tabs', f)); log.append(f'pipeline/tabs/{f} removed (no longer in build/tabs)')
        # bill_timeline's leginfo milestones (agent-billstatus) for the sheet task's rebuilds
        bm = P('work/out/bill_milestones.json')
        if os.path.exists(bm) and os.path.isdir(os.path.join(pd_, 'insights')):
            dst = os.path.join(pd_, 'insights', 'bill_milestones.json')
            if not os.path.exists(dst) or not filecmp.cmp(bm, dst, shallow=False):
                shutil.copy2(bm, dst); log.append('pipeline/insights/bill_milestones.json refreshed')
    return True


def merge_rel_texts(src, dst):
    """RELRULE-v1: the pipeline's release texts = its own entries + any entries of src it lacks (+ RELCOPIES-v1: fields an entry
    lacks, e.g. prid); True when dst changed"""
    import json
    a, b = json.load(open(dst, encoding='utf-8')), json.load(open(src, encoding='utf-8'))
    add = {u: x for u, x in b.get('rel', {}).items() if u not in a.get('rel', {})}
    fill = 0   # RELCOPIES-v1: fields an entry lacks (prid) are taken from src; nothing is removed or overwritten
    for u, x in b.get('rel', {}).items():
        y = a.get('rel', {}).get(u)
        if isinstance(y, dict) and isinstance(x, dict):
            for k, v in x.items():
                if k not in y and v not in (None, ''):
                    y[k] = v; fill += 1
    if not add and not fill:
        return False
    a.setdefault('rel', {}).update(add)
    json.dump(a, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    return True


def merge_rel_related(src, dst):
    """RELRELATED-v3 (rp-final 2026-10-28): the pipeline's release -> related-story links = src's rows (they REPLACE dst's row
    for the same release + Story ID, so re-tiered types land) + dst-only rows (the Update button's adds), one row per Story ID
    per release; header fields (v, version) come from src when src's version is newer or dst lacks them; True when dst changed"""
    import json, re
    a, b = json.load(open(dst, encoding='utf-8')), json.load(open(src, encoding='utf-8'))
    vn = lambda d: int((re.search(r'v(\d+)$', str(d.get('version', ''))) or [0, 0])[1])
    newer = vn(b) > vn(a) or (vn(b) == vn(a) and os.path.getmtime(src) >= os.path.getmtime(dst))   # same version: the later file wins
    ra, rb, out = a.get('rel', {}), b.get('rel', {}), {}
    for k in sorted(set(ra) | set(rb)):
        lst, seen = [], set()
        prim, sec = (rb.get(k, []), ra.get(k, [])) if newer else (ra.get(k, []), rb.get(k, []))
        for x in list(prim) + list(sec):
            if x and x[0] not in seen:
                lst.append(x); seen.add(x[0])
        out[k] = lst
    c = dict(a); c['rel'] = out
    for k, v in b.items():
        if k != 'rel' and (k not in c or newer):
            c[k] = v
    if c == a:
        return False
    json.dump(c, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return True


def merge_bills(src, dst):
    """the pipeline's bill list = its own rows + any rows of src it lacks (bill + session); True when dst changed"""
    import json
    a, b = json.load(open(dst, encoding='utf-8')), json.load(open(src, encoding='utf-8'))
    key = lambda r: (str(r.get('bill')), str(r.get('session', ''))[:9])
    have = {key(r) for r in a.get('rows', [])}
    add = [r for r in b.get('rows', []) if key(r) not in have]
    if not add:
        return False
    a.setdefault('rows', []).extend(add)
    json.dump(a, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return True


def verify(root, log):
    ok = True
    extra = [os.path.relpath(p, root) for d in PY_DIRS for p in sorted(glob.glob(os.path.join(root, d, '*.py')))]
    for rel in list(PY_CHECK) + extra:
        if not os.path.exists(os.path.join(root, rel)):
            log.append(f'COMPILE FAIL {rel}: missing'); ok = False; continue
        try:
            py_compile.compile(os.path.join(root, rel), doraise=True, cfile=os.path.join(tempfile.gettempdir(), 'apc_check.pyc'))
        except py_compile.PyCompileError as e:
            log.append(f'COMPILE FAIL {rel}: {e}')
            ok = False
    log.append(f'py_compile: {len(PY_CHECK) + len(extra)} Python files checked')
    js = open(os.path.join(root, JS), encoding='utf-8').read()
    a, z = js.find('<script>') + len('<script>'), js.rfind('</script>')
    tmp = os.path.join(tempfile.mkdtemp(), 'tracker_check.js')
    open(tmp, 'w', encoding='utf-8').write(js[a:z])
    try:
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        if r.returncode != 0:
            log.append('NODE CHECK FAIL: ' + r.stderr[:800])
            ok = False
        else:
            log.append('node --check tracker JS: ok')
    except FileNotFoundError:
        log.append('node not found: JS syntax not checked')
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=os.path.dirname(HERE))
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--no-pipeline', action='store_true')
    ap.add_argument('--tracker-js', metavar='OUT', help='only write the concatenated tracker JS to OUT')
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    if a.tracker_js:
        open(a.tracker_js, 'wb').write(tracker_js(root))
        print(f'{a.tracker_js}: {len(tracker_parts(root))} parts from {os.path.join(root, TRACKER_DIR)}')
        return 0
    log = []
    if a.check:
        tmp = tempfile.mkdtemp(prefix='apply_all_check_')
        for t in TARGETS + [JS_STAMP] + ['build/pub/pipeline/' + n for n in PIPELINE] + sorted(set(PIPELINE.values())) \
                + ['work/gabriel_bills_leginfo.json', 'work/out/bill_milestones.json'] + list(PY_CHECK) \
                + [os.path.relpath(p, root) for p in tracker_parts(root)]:
            if os.path.exists(os.path.join(root, t)):
                os.makedirs(os.path.dirname(os.path.join(tmp, t)), exist_ok=True)
                shutil.copy2(os.path.join(root, t), os.path.join(tmp, t))
        for d in ('build/insights', 'build/tabs', 'build/pub/pipeline/insights', 'build/pub/pipeline/tabs'):
            if os.path.isdir(os.path.join(root, d)):
                for f in os.listdir(os.path.join(root, d)):
                    if os.path.isfile(os.path.join(root, d, f)):
                        os.makedirs(os.path.join(tmp, d), exist_ok=True)
                        shutil.copy2(os.path.join(root, d, f), os.path.join(tmp, d, f))
        before = {t: sha(os.path.join(tmp, t)) for t in TARGETS if os.path.exists(os.path.join(tmp, t))}
        ok = apply(tmp, log, not a.no_pipeline) and verify(tmp, log)
        print('\n'.join(log))
        for t in before:
            print(f"{'changes' if sha(os.path.join(tmp, t)) != before[t] else 'unchanged':9} {t}")
        print('CHECK OK' if ok else 'CHECK FAILED', '(scratch copy:', tmp + ')')
        return 0 if ok else 1
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    bdir = os.path.join(root, 'work', f'pre_apply_all_{stamp}')
    ALL = [t for t in TARGETS + [JS_STAMP] if os.path.exists(os.path.join(root, t))]
    for t in ALL:
        os.makedirs(os.path.dirname(os.path.join(bdir, t)), exist_ok=True)
        shutil.copy2(os.path.join(root, t), os.path.join(bdir, t))
    before = {t: sha(os.path.join(root, t)) for t in ALL}
    ok = apply(root, log, not a.no_pipeline) and verify(root, log)
    if not ok:
        for t in ALL:
            shutil.copy2(os.path.join(bdir, t), os.path.join(root, t))
        log.append(f'FAILED: targets restored from {bdir}')
    print('\n'.join(log))
    for t in ALL:
        print(f"{'changed' if sha(os.path.join(root, t)) != before[t] else 'unchanged':9} {t}")
    print(('OK' if ok else 'FAILED') + f' (backup: {bdir})')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
