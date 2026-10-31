#!/usr/bin/env python3
"""INSIGHTS-v1 (agent-insights, 2026-10-27): the Insights tab. Idempotent (marker per target).
  python3 -I patch_insights.py [--js build/js_merged.js] [--assemble code/assemble.py] [--build-data code/build_data.py]
- tracker JS: the tab shell (insights_shell.js next to this script) before the boot section + 6 anchors (setTab, render,
  resize, boot routing, story-panel entry line).
- assemble.py: after assembling, insights_assemble.apply() adds the views (<INS_DIR>/<id>.js; INS_DIR = $INS_DIR or the
  'insights' folder next to the JS file) and BLOCKS_DIR/ins_<id>.json blocks.
- build_data.py: at the end, insights_data.run() builds BLOCKS_DIR/ins_<id>.json from <INS_DIR>/<id>_data.py
  (INS_DIR = $INS_DIR, or 'insights' next to build_data.py, or ../build/insights)."""
import argparse, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MARK = 'INSIGHTS-v1'

def patch_js(path, shell_path):
    s = open(path, encoding='utf-8').read()
    shell = open(shell_path, encoding='utf-8').read()
    if '/* ---------- INSIGHTS-v1' in s:
        # already wired: keep the shell block in step with insights_shell.js (anchors are untouched)
        i = s.index('/* ---------- INSIGHTS-v1'); end = '/* ---------- /INSIGHTS-v1 shell ---------- */'
        j = s.index(end, i) + len(end)
        new = shell.rstrip('\n')
        if s[i:j] == new:
            return 'unchanged'
        open(path, 'w', encoding='utf-8').write(s[:i] + new + s[j:])
        return 'shell block updated'
    R = [
     ("/* ---------- boot ---------- */", shell + "\n/* ---------- boot ---------- */"),
     ("['ov','db','an'].forEach(k => $('#view-'+k).hidden = k!==t);", "['ov','db','an','in'].forEach(k => $('#view-'+k).hidden = k!==t);  // INSIGHTS-v1"),
     ("history.replaceState(null, '', t==='ov' ? location.pathname : '#'+({db:'clips',an:'report'}[t]));",
      "history.replaceState(null, '', t==='ov' ? location.pathname : t==='in' ? insHash() : '#'+({db:'clips',an:'report'}[t]));"),
     ("  if (S.tab==='an'){ $('#rpWhen').value = S.when==='custom' ? 'custom' : S.when; renderTrends(rows); }\n",
      "  if (S.tab==='an'){ $('#rpWhen').value = S.when==='custom' ? 'custom' : S.when; renderTrends(rows); }\n"
      "  if (S.tab==='in'){ INS.version = insSig(); insShow(INS.cur, INS.cur ? INS.params : null); }  // INSIGHTS-v1\n"),
     ("if (S.tab==='ov' || S.tab==='an') render(); }, 200); });",
      "if (S.tab==='ov' || S.tab==='an') render(); if (S.tab==='in' && INS.cur) insShow(INS.cur, INS.params, true); }, 200); });"),
     ("setTab({clips:'db', trends:'an', report:'an'}[h] || 'ov'); renderWhen(); render();",
      "const insH = insParse(h); if (insH){ INS.pending = insH.id; INS.pendingParams = insH.params; }  // INSIGHTS-v1\n"
      "setTab(insH ? 'in' : ({clips:'db', trends:'an', report:'an'}[h] || 'ov')); renderWhen(); render();"),
     ("      ${repLinks(r)}\n", "      ${repLinks(r)}\n      ${insEntry(r)}\n"),
    ]
    for a, b in R:
        n = s.count(a)
        if n != 1:
            raise SystemExit(f'{path}: anchor found {n}x: {a[:70]}')
        s = s.replace(a, b)
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'

# INSIGHTS-v1b (coordinator, from agent-ins-reporters): a story with no authors must not turn a role-only byline
# ("Contributor", "Contributing Editor", "Staff Writer", "Special to ...") into a person in the Reporter filter.
ROLE_JS = ("/* INSIGHTS-v1b: role-only bylines (byline == Author title, or a bare role) give no author */\n"
  "const ROLE_BYLINE = /^(?:(?:staff|contributing|guest|senior|special)\\s+)?(?:writer|editor|contributor|correspondent|columnist|reporter)s?$|^special to\\b/i;\n"
  "const bylineAuthors = r => { const a = String(r.author || '').trim(); return !a || (r.atitle && String(r.atitle).trim() === a) || ROLE_BYLINE.test(a) ? [] : splitAuthors(a); };\n")
def patch_js_roles(path):
    s = open(path, encoding='utf-8').read()
    if 'INSIGHTS-v1b' in s:
        return 'unchanged'
    R = [("D.forEach(r => { r.author = r.author || ''; r.atitle = r.atitle || ''; r.authors = Array.isArray(r.authors) && r.authors.length ? r.authors.map(String) : splitAuthors(r.author); });",
          ROLE_JS + "D.forEach(r => { r.author = r.author || ''; r.atitle = r.atitle || ''; r.authors = Array.isArray(r.authors) && r.authors.length ? r.authors.map(String) : bylineAuthors(r); });"),
         ("r.authors = canonAuthors(Array.isArray(r.authors) && r.authors.length ? r.authors : splitAuthors(r.author));",
          "r.authors = canonAuthors(Array.isArray(r.authors) && r.authors.length ? r.authors : bylineAuthors(r));  // INSIGHTS-v1b")]
    for a, b in R:
        n = s.count(a)
        if n != 1:
            raise SystemExit(f'{path}: anchor found {n}x: {a[:70]}')
        s = s.replace(a, b)
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'

ASM_ADD = '''
# INSIGHTS-v1: the Insights views (<INS_DIR>/<id>.js) and their data blocks (BLOCKS_DIR/ins_<id>.json)
_ins_dir = os.environ.get('INS_DIR') or os.path.join(os.path.dirname(os.path.abspath(JS)), 'insights')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import insights_assemble
h = insights_assemble.apply(open(OUT, encoding='utf-8').read(), _ins_dir, BLK)
open(OUT, 'w', encoding='utf-8').write(h)
print('insights:', _ins_dir, len(h))
'''
def patch_assemble(path):
    s = open(path, encoding='utf-8').read()
    if MARK in s:
        return 'unchanged'
    a = "open(OUT, 'w', encoding='utf-8').write(h)\nprint(OUT, len(h))\n"
    if s.count(a) != 1:
        raise SystemExit(f'{path}: anchor not found')
    s = s.replace(a, a + ASM_ADD)
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'

BD_ADD = '''
# INSIGHTS-v1: data blocks for the Insights views (<INS_DIR>/<id>_data.py -> OUT/ins_<id>.json)
_here = os.path.dirname(os.path.abspath(__file__))
_ins_dir = os.environ.get('INS_DIR') or next((d for d in (os.path.join(_here, 'insights'), os.path.join(_here, '..', 'build', 'insights')) if os.path.isdir(d)), '')
if _ins_dir:
    import insights_data
    print('insights blocks:', insights_data.run(COV, OUT, _ins_dir, os.path.dirname(_here), cov=C, data=data))
'''
def patch_build_data(path):
    s = open(path, encoding='utf-8').read()
    if MARK in s:
        return 'unchanged'
    s = s.rstrip('\n') + '\n' + BD_ADD
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--js'); ap.add_argument('--assemble'); ap.add_argument('--build-data')
    ap.add_argument('--shell', default=os.path.join(HERE, 'insights_shell.js'))
    a = ap.parse_args()
    if a.js: print('js:', patch_js(a.js, a.shell if os.path.exists(a.shell) else os.path.join(HERE, 'shell.js'))); print('js roles:', patch_js_roles(a.js))
    if a.assemble: print('assemble:', patch_assemble(a.assemble))
    if a.build_data: print('build_data:', patch_build_data(a.build_data))
