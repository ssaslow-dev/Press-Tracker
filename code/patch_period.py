#!/usr/bin/env python3
"""PERIOD-v1 (agent-relrule, 2026-10-27; Sammy: "Make the press desk have variable time periods"). Idempotent; apply_all 4l.
  python3 -I patch_period.py --js build/js_merged.js --views build/insights
Tracker JS: the block code/period_shell.js (shared period bar, ctx.period / ctx.inPeriod, URL + per-viewer memory, event
  "ajg:period") between its markers, before the boot section (refreshed when the source changes).
Views (anchored edits, marker PERIOD-v1 per file): release_pickup.js (releases dated in the period; tiles incl. the
  before/after stat over them; summary line; a deep-linked release outside the period stays listed), bill_timeline.js
  (stories and leginfo milestones in the period; bills with any activity in it; summary line), story_travel.js (stories
  whose original date is in the period; pickers and counts follow; a deep-linked story outside it is still shown, noted).
  Pitch (code/reorg_pitch.js, installed by patch_reorg.py) reads ctx.period itself."""
import argparse, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
BOOT = '/* ---------- boot ---------- */'
START, END = '/* ---------- PERIOD-v1 (agent-relrule', '/* ---------- /PERIOD-v1 ---------- */'
MARK = 'PERIOD-v1'

VIEWS = {
 'release_pickup.js': [
  ("    var years = [], topics = [];\n",
   "    // PERIOD-v1: only releases dated in the Press desk period (a deep-linked release stays listed)\n"
   "    var PH = (ctx.period && ctx.period.phrase) || 'across all dates', relAll = rel;\n"
   "    rel = rel.filter(function(x){ return !ctx.inPeriod || ctx.inPeriod(x.date) || (p.id && x.key === p.id); });\n"
   "    var years = [], topics = [];\n"),
  ("Click a release to see the outlets, the follow-up stories and the official release.</div></div>';\n",
   "Click a release to see the outlets, the follow-up stories and the official release.</div></div>';\n"
   "    if (n) h += '<div class=\"pd-sum\">' + ctx.esc(ctx.pl(n, 'release', 'releases') + ' ' + PH + ((year || topic || pick) ? ' (with the filters below)' : '') + ': ' + np + ' picked up, ' + ctx.pl(list.reduce(function(s,x){ return s + x.rows.length; }, 0), 'copy', 'copies') + (p.id && ctx.inPeriod && !ctx.inPeriod(((rel.filter(function(x){ return x.key === p.id; })[0]) || {}).date || '') ? '; the release you opened is outside this period' : '') + '.') + '</div>';   // PERIOD-v1\n"),
  ("'<div class=\"card pad\"><div class=\"empty\">No releases match this year and issue.</div></div></div>'",
   "'<div class=\"card pad\"><div class=\"empty\">' + ctx.esc(relAll.length && !rel.length ? 'No official release is dated ' + PH + '. Choose a longer period above.' : 'No releases ' + PH + ' match this year, issue and pickup choice.') + '</div></div></div>'"),
 ],
 'bill_timeline.js': [
  ("function build(ctx){\n  if (memo && memo.v === ctx.version) return memo;\n",
   "function build(ctx){\n  const PK = ctx.version + '|' + JSON.stringify(ctx.period || {}), inP = ctx.inPeriod || (() => true);   // PERIOD-v1\n  if (memo && memo.v === PK) return memo;\n"),
  ("  const groups = new Map();\n",
   "  ms.forEach(m => { m.ev = m.ev.filter(e => inP(e.date)); });   // PERIOD-v1: milestones in the period\n  const groups = new Map();\n"),
  ("    if (!r.date) return;\n    const ses = pickSes(bill, r.date)",
   "    if (!r.date || !inP(r.date)) return;   // PERIOD-v1: stories in the period\n    const ses = pickSes(bill, r.date)"),
  ("  const list = [...groups.values()].map(g => {\n",
   "  ms.forEach((m, k) => { if (m.ev.length && !groups.has(k)){ const [bill, ses] = k.split('|'); groups.set(k, {bill, ses, rs: []}); } });   // PERIOD-v1: bills with leginfo activity only\n"
   "  const list = [...groups.values()].map(g => {\n"),
  ("  memo = {v: ctx.version, list, hasBlock: !!blk};", "  memo = {v: PK, list, hasBlock: !!blk};"),
  ("  if (!list.length){ el.innerHTML = '<div class=\"in-sec\"><div class=\"card pad\"><div class=\"empty\">No stories are tagged with a bill yet.</div></div></div>'; return; }",
   "  const PH = (ctx.period && ctx.period.phrase) || 'across all dates';   // PERIOD-v1\n"
   "  if (!list.length){ el.innerHTML = `<div class=\"in-sec\"><div class=\"card pad\"><div class=\"empty\">No bill had coverage or leginfo activity ${ctx.esc(PH)}. Choose a longer period above.</div></div></div>`; return; }"),
  ("    <div class=\"cap\">Stories per week mentioning the bill, with its leginfo milestones. Hover a week for counts; click it to list that week's stories.</div>\n",
   "    <div class=\"pd-sum\">${ctx.esc(ctx.pl(list.length, 'bill', 'bills') + ' had coverage or leginfo activity ' + PH + ': ' + ctx.pl(list.reduce((s, x) => s + x.n, 0), 'story', 'stories') + ', ' + ctx.pl(list.reduce((s, x) => s + (x.ms ? x.ms.ev.length : 0), 0), 'milestone', 'milestones') + '.')}</div>\n"
   "    <div class=\"cap\">Stories per week mentioning the bill, with its leginfo milestones, in the period chosen above. Hover a week for counts; click it to list that week's stories.</div>\n"),
  ("<div class=\"cap\">Bills with coverage, most covered first.", "<div class=\"cap\">Bills with coverage or leginfo activity in the period, most covered first."),
 ],
 'story_travel.js': [
  ("  function build(ctx){\n    if (memo && memo.v === ctx.version) return memo;\n",
   "  function build(ctx){\n    const PK = ctx.version + '|' + JSON.stringify(ctx.period || {});   // PERIOD-v1\n    if (memo && memo.v === PK) return memo;\n"),
  ("String(r.hl || '').trim() && !X[r.id])", "String(r.hl || '').trim() && !X[r.id] && (!ctx.inPeriod || ctx.inPeriod(r.date)))"),
  ("    memo = { v: ctx.version, stories,", "    memo = { v: PK, stories,"),
  ("    if (!ctx.D.length || !M.stories.length){ el.innerHTML = '<div class=\"in-sec\"><div class=\"card pad\"><div class=\"empty\">No reprints in the data yet.</div></div></div>'; return; }",
   "    const PH = (ctx.period && ctx.period.phrase) || 'across all dates';   // PERIOD-v1\n"
   "    if (!ctx.D.length || (!M.stories.length && !(st.id && ctx.byId(st.id)))){ el.innerHTML = `<div class=\"in-sec\"><div class=\"card pad\"><div class=\"empty\">No story first published ${ctx.esc(PH)} was reprinted by another outlet. Choose a longer period above.</div></div></div>`; return; }"),
  ("Hover a dot for the outlet; click it to open the story.</div>\n",
   "Hover a dot for the outlet; click it to open the story.</div>\n"
   "  <div class=\"pd-sum\">${ctx.esc(ctx.pl(M.stories.length, 'story', 'stories') + ' first published ' + PH + (M.stories.length === 1 ? ' was' : ' were') + ' reprinted by other outlets.' + (ctx.inPeriod && !ctx.inPeriod(r.date) ? ' The story shown ran ' + ctx.dateLabel(r) + ', outside this period.' : ''))}</div>\n"),
 ],
}


def patch_js(path, log):
    s0 = s = open(path, encoding='utf-8').read()
    blk = open(os.path.join(HERE, 'period_shell.js'), encoding='utf-8').read().rstrip('\n') + '\n'
    if START in s:
        i = s.index(START); j = s.index(END, i) + len(END) + 1
        if s[i:j] != blk:
            s = s[:i] + blk + s[j:]; log.append('js: period block refreshed')
    else:
        if s.count(BOOT) != 1:
            raise SystemExit('js: boot anchor')
        s = s.replace(BOOT, blk + BOOT); log.append('js: period block inserted')
    if s != s0:
        open(path, 'w', encoding='utf-8').write(s)
    else:
        log.append('js: unchanged')


def patch_views(vdir, log):
    for fn, R in VIEWS.items():
        p = os.path.join(vdir, fn)
        if not os.path.exists(p):
            log.append(f'views: {fn} missing - skipped'); continue
        s = open(p, encoding='utf-8').read()
        if MARK in s:
            log.append(f'views: {fn} unchanged'); continue
        for a, b in R:
            if s.count(a) != 1:
                raise SystemExit(f'{fn}: anchor found {s.count(a)}x: {a[:90]}')
            s = s.replace(a, b)
        open(p, 'w', encoding='utf-8').write(s); log.append(f'views: {fn} patched')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--js'); ap.add_argument('--views'); a = ap.parse_args()
    log = []
    if a.js: patch_js(a.js, log)
    if a.views: patch_views(a.views, log)
    print('\n'.join(log))
