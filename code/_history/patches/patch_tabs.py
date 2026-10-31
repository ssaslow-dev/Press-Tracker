#!/usr/bin/env python3
"""patch_tabs.py - TABS-v1 (agent-tabs, 2026-10-27): the Press desk tools become main tabs.

  python3 -I code/patch_tabs.py [--js build/js_merged.js] [--reorg code/reorg_tracker.js] [--assemble code/assemble.py]
                               [--build-data code/build_data.py]

Idempotent (every edit is skipped when its result is already there; the block is refreshed only when its source changed).
apply_all_patches.py runs it as step 4l, after 4k.
  tracker JS:    Data's renderTimeChart becomes a thin call of the shared timeChart(rows, o) (same output for Data; the
                 entity pages draw the same chart over their own stories); the TABS-v1 block (code/tabs_tracker.js: menu, routing + old-link redirects, search-tab and entity-page
                 components, shared helpers, AJGTabs.register) before the boot section; Data's two "Press desk ›" link
                 labels and one caption name the new tabs (same edits in code/reorg_tracker.js, so step 4j keeps them).
  assemble.py:   after the Insights views, the tab modules (TABS_DIR or <JS dir>/tabs/<id>.js) and blocks (tab_<id>.json)
                 via tabs_assemble.py.
  build_data.py: after the Insights blocks, the tab blocks via tabs_data.py (TABS_DIR or <here>/tabs or ../build/tabs).
"""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOOT = '/* ---------- boot ---------- */'
START, END = '/* ---------- TABS-v1 (agent-tabs', '/* ---------- /TABS-v1 ---------- */'
LABELS = [   # Data's links into the old Press desk now name the tabs they open
    ('data-ins-k="range" data-ins-v="all">Press desk › Bills</button>', 'data-ins-k="range" data-ins-v="all">Bills tab ›</button>'),
    ('data-ins-k="win" data-ins-v="24">Press desk › Pitch</button>', 'data-ins-k="win" data-ins-v="24">Reporters tab ›</button>'),
    ("Click one to see where it ran (Press desk › Story travel).", "Click one to see where it ran (Story travel tab)."),
]
ASM_ANCHOR = "print('insights:', _ins_dir, len(h))\n"
ASM_ADD = ("# TABS-v1: the tab modules (<TABS_DIR>/<id>.js) and their data blocks (BLOCKS_DIR/tab_<id>.json)\n"
           "_tabs_dir = os.environ.get('TABS_DIR') or os.path.join(os.path.dirname(os.path.abspath(JS)), 'tabs')\n"
           "import tabs_assemble\n"
           "h = tabs_assemble.apply(open(OUT, encoding='utf-8').read(), _tabs_dir, BLK)\n"
           "open(OUT, 'w', encoding='utf-8').write(h)\n"
           "print('tabs:', _tabs_dir, len(h))\n")
BD_ANCHOR = "    print('insights blocks:', insights_data.run(COV, OUT, _ins_dir, os.path.dirname(_here), cov=C, data=data))\n"
BD_ADD = ("# TABS-v1: data blocks for the tab modules (<TABS_DIR>/_common_data.py, <id>_data.py -> OUT/tab_<id>.json)\n"
          "_tabs_dir = os.environ.get('TABS_DIR') or next((d for d in (os.path.join(_here, 'tabs'), os.path.join(_here, '..', 'build', 'tabs')) if os.path.isdir(d)), '')\n"
          "if _tabs_dir:\n"
          "    import tabs_data\n"
          "    print('tab blocks:', tabs_data.run(COV, OUT, _tabs_dir, os.path.dirname(_here), cov=C, data=data))\n")

CHART_DONE = 'function timeChart(rows, o){'
CHART_EDITS = [   # inside renderTimeChart only (TABS-v1 CHART: the Data chart becomes the shared timeChart(rows, o))
    ("function renderTimeChart(rows){\n  const iv = $('#anInterval').value, bk = $('#anBreak').value, meas = $('#anMeasure').value, from = +$('#anFrom').value, pct = $('#anShow').value==='pct', showAvg = $('#anAvg').checked && !pct;\n",
     "/* TABS-v1: Data's \"Coverage over time\" chart is drawn by timeChart(rows, o), shared with the reporter and outlet pages.\n"
     "   o = the controls' values, the elements to draw into, and what a click on a bar does; Data passes its own controls and\n"
     "   its old click (open Clips on that period), so the Data tab behaves exactly as before. */\n"
     "function renderTimeChart(rows){ return timeChart(rows, { iv: $('#anInterval').value, bk: $('#anBreak').value, meas: $('#anMeasure').value, from: +$('#anFrom').value,\n"
     "  pct: $('#anShow').value==='pct', avgOn: $('#anAvg').checked, avgEl: $('#anAvg'), onlyEl: $('#anOnly'), title: $('#tsTitle'), cap: $('#tsCap'), legend: $('#tsLegend'),\n"
     "  chart: $('#tsChart'), table: $('#tsTable'), quick: true, pick: (b, iv) => {\n"
     "    if (iv==='month') setMonth(b);\n"
     "    else if (iv==='year') applyWhen('y'+b);\n"
     "    else { const yr = b.slice(0,4), q = +b.slice(-1); S.when='custom'; S.d0 = `${yr}-${String(q*3-2).padStart(2,'0')}`; S.d1 = `${yr}-${String(q*3).padStart(2,'0')}-99`; S.whenLabel = `${b.replace('-',' ')}`; }\n"
     "    go('db'); } }); }\n"
     "function timeChart(rows, o){\n"
     "  const iv = o.iv, bk = o.bk, meas = o.meas, from = o.from, pct = o.pct, showAvg = o.avgOn && !pct;\n"),
    ("  $('#anAvg').disabled = pct; $('#anAvg').parentElement.style.opacity = pct ? .5 : '';", "  o.avgEl.disabled = pct; o.avgEl.parentElement.style.opacity = pct ? .5 : '';"),
    ("const only = bk==='none' ? '' : fillOnly(bk, rows);", "const only = bk==='none' ? '' : fillOnly(bk, rows, o.onlyEl);"),
    ("  $('#anOnly').disabled = bk==='none'; $('#anOnly').parentElement.style.opacity = bk==='none' ? .5 : '';", "  o.onlyEl.disabled = bk==='none'; o.onlyEl.parentElement.style.opacity = bk==='none' ? .5 : '';"),
    ("  $('#tsTitle').textContent =", "  o.title.textContent ="),
    ("  $('#tsCap').textContent =", "  o.cap.textContent ="),
    (" + ' Click a bar to see those clips.';", " + (o.capEnd || ' Click a bar to see those clips.');"),
    ("  $('#tsLegend').innerHTML =", "  o.legend.innerHTML ="),
    (" + (showAvg ? `<span class=\"it\"><span class=\"line\"></span>${winLabel}</span>` : '');", " + (showAvg ? `<span class=\"it\"><span class=\"line\"></span>${winLabel}</span>` : '') + (o.legendExtra || '');"),
    ("const W = Math.max(300, $('#tsChart').clientWidth || 1000)", "const W = Math.max(300, o.chart.clientWidth || 1000)"),
    ("  buckets.forEach((b,i) => { svg += `<rect class=\"hit\" data-i=\"${i}\"", "  if (o.extra) svg += o.extra({ buckets, iv, rows: inRange, m, W, H, ih, band, key: r => bucketKey(r, iv) });\n  buckets.forEach((b,i) => { svg += `<rect class=\"hit\" data-i=\"${i}\""),
    ("  const el = $('#tsChart'); el.innerHTML = svg + '</svg>';", "  const el = o.chart; el.innerHTML = svg + '</svg>';"),
    ("`<div class=\"foot\">Click to see these clips</div>`); };", "`<div class=\"foot\">${o.foot || 'Click to see these clips'}</div>`); };"),
    ("  el.onclick = e => { const t = e.target.closest('.hit'); if (!t) return; hideTip(); const b = buckets[+t.dataset.i];\n"
     "    if (iv==='month') setMonth(b);\n"
     "    else if (iv==='year') applyWhen('y'+b);\n"
     "    else { const yr = b.slice(0,4), q = +b.slice(-1); S.when='custom'; S.d0 = `${yr}-${String(q*3-2).padStart(2,'0')}`; S.d1 = `${yr}-${String(q*3).padStart(2,'0')}-99`; S.whenLabel = `${b.replace('-',' ')}`; }\n"
     "    go('db'); };",
     "  el.onclick = e => { const t = e.target.closest('.hit'); if (!t) return; hideTip(); const b = buckets[+t.dataset.i]; o.pick(b, iv); };"),
    ("  $('#tsTable').innerHTML = `<table>", "  o.table.innerHTML = `<table>"),
    ("  document.querySelectorAll('.quick [data-qv]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.qv === S.qv)));\n}",
     "  if (o.quick) document.querySelectorAll('.quick [data-qv]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.qv === S.qv)));\n"
     "  return { buckets, totals, series, grid };\n}"),
]
ONLY_EDIT = ("function fillOnly(bk, rows){\n  const sel = $('#anOnly'), cur = sel.value, c = new Map();",
             "function fillOnly(bk, rows, sel){\n  sel = sel || $('#anOnly'); const cur = sel.value, c = new Map();  /* TABS-v1: the entity-page chart passes its own select */")

# AXIS-v1 (Sammy 2026-10-27: "make the y axis of all graphs variable depending on the data set"): one shared nice-scale
# helper; niceMax/axis (used by every Data chart, the Bills timeline, Story travel's day axis, simpleBars and the entity-page
# chart) scale to the data shown: max x ~1.06 headroom rounded up to 1/2/2.5/5 x 10^n, 2-5 intervals, integer ticks for counts,
# percent capped at 100 but zoomed when low, an empty state when everything is 0.
AXIS_EDITS = [
    ("function niceMax(v){ if (v<=5) return 5; const p = Math.pow(10, Math.floor(Math.log10(v))); for (const m of [1,2,2.5,4,5,10]) if (m*p >= v) return m*p; return 10*p; }",
     "/* AXIS-v1: one nice-scale helper for every chart. kind 'count' (integer ticks), 'pct' (capped at 100, zooms in when low),\n"
     "   'tone' (symmetric around 0; returns the half-span). max = data max + ~6% headroom rounded up to 1/2/2.5/5 x 10^n, 2-5 steps. */\n"
     "function niceScale(v, kind){ kind = kind || 'count'; if (!(v > 0)) return { max: 0, step: 0, n: 0, empty: true };\n"
     "  if (kind === 'tone') v = Math.max(v, 0.45);\n"
     "  const t = v * 1.06, e0 = Math.floor(Math.log10(t)) - 1;\n"
     "  for (let e = e0; e <= e0 + 3; e++) for (const m of [1, 2, 2.5, 5]){ const step = m * Math.pow(10, e);\n"
     "    if (kind === 'count' && (step < 1 || !Number.isInteger(step))) continue; if (kind === 'tone' && step < 0.1) continue;\n"
     "    const n = Math.max(kind === 'tone' ? 1 : 2, Math.ceil(t / step - 1e-9)); if (n > (kind === 'tone' ? 3 : 5)) continue;\n"
     "    let max = +(n * step).toFixed(6);\n"
     "    if (kind === 'pct' && max > 100) return { max: 100, step: 20, n: 5 };\n"
     "    if (kind === 'tone' && max > 2) return { max: 2, step: 1, n: 2 };\n"
     "    return { max, step, n }; }\n"
     "  return { max: t, step: t / 4, n: 4 }; }\n"
     "function niceMax(v, kind){ const s = niceScale(v, kind); return s.max || (kind === 'pct' ? 100 : 1); }\n"
     "/* AXIS-v1: tick count for a max from niceScale (integer steps whenever the max allows it) */\n"
     "function axisTicks(ymax){ const nice = st => { const p = Math.pow(10, Math.floor(Math.log10(st) + 1e-9)), m = st / p; return [1, 2, 2.5, 5, 10].some(x => Math.abs(m - x) < 1e-6); };\n"
     "  const intOnly = Number.isInteger(ymax) && ymax >= 2;\n"
     "  for (const n of [5, 4, 3, 2, 6]){ const st = ymax / n; if (nice(st) && (!intOnly || Number.isInteger(+st.toFixed(9)))) return n; }\n"
     "  return 4; }\n"
     "const axisLab = v => Number.isInteger(+v.toFixed(6)) ? fmt(Math.round(v)) : (+v.toFixed(2)).toString();"),
    ("  const nt = ymax % 4 === 0 ? 4 : 5; for (let i=0;i<=nt;i++){ const v = ymax*i/nt, yy = m.t + ih - (v/ymax)*ih; s += `<line x1=\"${m.l}\" x2=\"${W-m.r}\" y1=\"${yy}\" y2=\"${yy}\"></line><text x=\"${m.l-6}\" y=\"${yy+4}\" text-anchor=\"end\">${fmt(Math.round(v))}${suf||''}</text>`; }",
     "  const nt = axisTicks(ymax); for (let i=0;i<=nt;i++){ const v = ymax*i/nt, yy = m.t + ih - (v/ymax)*ih; s += `<line x1=\"${m.l}\" x2=\"${W-m.r}\" y1=\"${yy}\" y2=\"${yy}\"></line><text x=\"${m.l-6}\" y=\"${yy+4}\" text-anchor=\"end\">${axisLab(v)}${suf||''}</text>`; }  /* AXIS-v1 */"),
    ("  const ymax = pct ? (only ? Math.min(100, niceMax(Math.max(1, ...buckets.map((_,i)=>val(only,i))))) : 100) : niceMax(Math.max(1, ...totals));",
     "  const ymax = pct ? (only ? niceMax(Math.max(...buckets.map((_,i)=>val(only,i))), 'pct') : 100) : niceMax(Math.max(...totals));  /* AXIS-v1: scaled to the data shown (a stacked share is always 100) */"),
    ("  const W = Math.max(300, o.chart.clientWidth || 1000)",
     "  if (!totals.some(Boolean)){ o.chart.innerHTML = '<div class=\"empty\">Nothing to chart for these settings.</div>'; o.chart.onclick = o.chart.onmousemove = null; o.table.innerHTML = ''; return { buckets, totals, series, grid, empty: true }; }  /* AXIS-v1 */\n"
     "  const W = Math.max(300, o.chart.clientWidth || 1000)"),
    ("  const ymax = niceMax(Math.max(1,...items.map(i=>i.v))), band = iw/items.length, bw = band*.72;",
     "  if (!items.some(i => i.v)){ el.innerHTML = '<div class=\"empty\">Nothing to chart.</div>'; el.onclick = el.onmousemove = null; return; }  /* AXIS-v1 */\n"
     "  const ymax = niceMax(Math.max(...items.map(i=>i.v))), band = iw/items.length, bw = band*.72;"),
]

# Phase B (TABS-v1 integration, 2026-10-28) ------------------------------------------------------------------------------
# SPLITBILLS-v2: extraordinary-session bill numbers (ABX1-4, SBX1-1 ...) are bills too (6 stories' tags were dropped)
JS_PHASEB = [
    ("const splitBills = v => Array.isArray(v) ? v.filter(x => typeof x === 'string' && /^(AB|SB|ACA|ACR|AJR) \\d{1,4}$/.test(x)) : String(v || '').split(/[;,]/).map(x => x.trim().toUpperCase().replace(/^([A-Z]+)\\s*-?\\s*/, '$1 ')).filter(x => /^(AB|SB|ACA|ACR|AJR) \\d{1,4}$/.test(x));",
     "const BILL_RX = /^((AB|SB|ACA|ACR|AJR) \\d{1,4}|(AB|SB)X\\d{1,2}-\\d{1,4})$/;   /* SPLITBILLS-v2: + extraordinary-session numbers (ABX1-4, SBX1-1) */\n"
     "const billNorm = x => { x = String(x || '').trim().toUpperCase(); const m = /^(AB|SB)\\s*X\\s*(\\d{1,2})\\s*-\\s*(\\d{1,4})$/.exec(x); return m ? `${m[1]}X${m[2]}-${m[3]}` : x.replace(/^([A-Z]+)\\s*-?\\s*/, '$1 '); };\n"
     "const splitBills = v => Array.isArray(v) ? v.filter(x => typeof x === 'string' && BILL_RX.test(x)) : String(v || '').split(/[;,]/).map(billNorm).filter(x => BILL_RX.test(x));"),
    # LEGINFO-v1 (Sammy 2026-10-27 "use correct capitalization"): the site is LegInfo in every visible text (URLs, ids unchanged)
    ("source: `leginfo author search (Update button, ", "source: `LegInfo author search (Update button, "),
    ("U.leginfo = `leginfo: ${pl(found.length, 'bill')}", "U.leginfo = `LegInfo: ${pl(found.length, 'bill')}"),
    ("    U.leginfo = 'leginfo check skipped';", "    U.leginfo = 'LegInfo check skipped';"),
    ("U.step = 'Checking leginfo for new bills of his';", "U.step = 'Checking LegInfo for new bills of his';"),
    ("It also reads leginfo’s list of his bills", "It also reads LegInfo’s list of his bills"),
    ("Timelines with leginfo milestones for each bill:", "Timelines with LegInfo milestones for each bill:"),
    # HOMEUPKEEP-v1 (Sammy 2026-10-27 "things like this belong in the manage tab"): Home's Needs attention shows coverage
    # only; upkeep (unconfirmed finds, an out-of-date log, pages waiting for tone or authors) lives in Manage (badge counts it)
    ("  if (U.found.length) A.push(['bad', `${pl(U.found.length,'new story','new stories')} found by Update database that Claude couldn’t confirm`, 'Waiting for you to check and add them.', 'Review', 'data-mgopen=\"upd\"']);\n", ""),
    ("  if (age > 3) A.push(['warn', `No clips logged since ${dateLabel(byId.get(D.find(r=>r.date===LAST).id))}`, `That is ${pl(age,'day')}. Press Update database to check for new coverage.`, 'Update database', 'data-runfind']);\n"
     "  const pt = pendingTone().length, pa = pendingAuthor().length;\n"
     "  if (pt) A.push(['warn', `${pl(pt,'saved page')} waiting for a tone rating`, 'Press Refresh from files to have Claude rate them.', 'Open', 'data-mgopen=\"quality\"']);\n"
     "  if (pa) A.push(['warn', `${pl(pa,'saved page')} without an author checked`, 'Press Refresh from files to have Claude read the bylines.', 'Open', 'data-mgopen=\"quality\"']);\n",
     "  /* HOMEUPKEEP-v1: finds to review, an out-of-date log and pages waiting for tone or authors are in Manage */\n"),
    ("  if (!A.some(a => a[0]==='bad' || a[0]==='warn')) A.unshift(['ok', 'Nothing urgent', age <= 3 ? `The log is current through ${dateLabel(byId.get(D.find(r=>r.date===LAST).id))}, and no rated story in the last 30 days is negative.` : 'No negative coverage among rated stories in the last 30 days.', '', '']);",
     "  if (!A.some(a => a[0]==='bad' || a[0]==='warn')) A.unshift(['ok', 'Nothing urgent', 'No negative coverage among rated stories in the last 30 days.', '', '']);  /* HOMEUPKEEP-v1 */"),
    ("  const n = pendingTone().length + pendingAuthor().length + U.found.length;\n",
     "  const n = pendingTone().length + pendingAuthor().length + U.found.length + (logAge() > 3 ? 1 : 0);  /* HOMEUPKEEP-v1: + an out-of-date log */\n"),
    ("    el.innerHTML = `<p>Records worth checking in the source spreadsheet. <b>Show</b> lists them in Clips.</p><div class=\"attn\">\n",
     "    const age = logAge();  /* HOMEUPKEEP-v1: upkeep moved here from Home's Needs attention */\n"
     "    el.innerHTML = `<p>Records worth checking in the source spreadsheet. <b>Show</b> lists them in Clips.</p><div class=\"attn\">\n"
     "      ${U.found.length ? `<div class=\"attn-i\"><i class=\"bad\"></i><div><b>${pl(U.found.length,'new story','new stories')} found by Update database that Claude couldn’t confirm</b><span>Waiting for you to check and add them.</span></div><button class=\"btn\" data-mgopen=\"upd\">Review</button></div>` : ''}\n"
     "      ${age > 3 ? `<div class=\"attn-i\"><i class=\"warn\"></i><div><b>No clips logged since ${dateLabel(byId.get(D.find(r=>r.date===LAST).id))}</b><span>That is ${pl(age,'day')}. Press Update database to check for new coverage.</span></div><button class=\"btn\" data-runfind>Update database</button></div>` : ''}\n"),
    ("function drawBadge(){\n", "const logAge = () => Math.round((new Date(TODAY) - new Date(LAST)) / 864e5);  /* HOMEUPKEEP-v1 */\nfunction drawBadge(){\n"),
]
REORG_PHASEB = [
    ("Timelines with leginfo milestones for each bill:", "Timelines with LegInfo milestones for each bill:"),
    # HOMELINE-off (Sammy 2026-10-27 "remove this"): no 30-day summary line on Home (reorgHomeLine finds no #homeLine and returns)
    ("  const th = document.querySelector('#view-ov .today-head'); if (th && !$('#homeLine')) th.insertAdjacentHTML('afterend', '<div class=\"rg-line\" id=\"homeLine\"></div>');\n",
     "  /* HOMELINE-off (Sammy 2026-10-27 \"remove this\"): the 30-day summary line and its copy icon are no longer on Home */\n"),
]
VIEW_PHASEB = {'bill_timeline.js': [
    ("with its leginfo milestones. Hover", "with its LegInfo milestones. Hover"),
    ("Final status from leginfo. Click", "Final status from LegInfo. Click"),
    ("No leginfo milestones for this bill yet.", "No LegInfo milestones for this bill yet."),
    ("rel=\"noopener\">leginfo history</a>", "rel=\"noopener\">LegInfo history</a>")]}
JS_PHASEB += [REORG_PHASEB[1]]
# LINKRULES-v1: Data's "Reporters with the most stories" names link to the reporter pages
JS_PHASEB += [("$('#hWho').textContent = L.who;", "$('#hWho').innerHTML = tbWhoHtml(L.who);  /* LINKRULES-v1 */")]   # the REORG block inside the tracker JS gets the same edit, so step 4j and 4l agree on run 1
LEAN_PROMPT = [("`insights_assemble.py`, `insights_data.py`, and every file in `pipeline/insights/` (into `insights/` next to them).",
                "`insights_assemble.py`, `insights_data.py`, `tabs_assemble.py`, `tabs_data.py`, every file in `pipeline/insights/` (into `insights/` next to them) and every file in `pipeline/tabs/` (into `tabs/`; TABS-v1: assemble.py and build_data.py add the tab modules and their blocks from there)."),
               # RELTEXTS-v1 (v19): the Press releases tab searches the full release texts from data/release_texts.json next to the page
               ("also publish `release_texts.json` as `pipeline/release_texts.json` (RELCHECK-v2).",
                "also publish `release_texts.json` as `pipeline/release_texts.json` (RELCHECK-v2) AND as `data/release_texts.json` (RELTEXTS-v1: the Press releases tab's full-text search reads it next to the page).")]
PROMPT_PHASEB = [("(Gabriel's bills from leginfo;", "(Gabriel's bills from LegInfo;")]

# ENTITIES-v1: headlines are shown as written in the sheet but with HTML entities decoded ("Braun&#8217;s" -> "Braun’s")
BD_PHASEB = [
    ("import sys, re, json, collections, os\n", "import sys, re, json, collections, os\nimport html as _html   # ENTITIES-v1\n_hd = lambda v: _html.unescape(v) if '&' in v else v   # ENTITIES-v1: decode HTML entities in headlines\n"),
    ("        'hl': s(r['Headline']), 'src': s(r['Data Source']), 'lk': links_of(r)})  # LINKS-v1", "        'hl': _hd(s(r['Headline'])), 'src': s(r['Data Source']), 'lk': links_of(r)})  # LINKS-v1 + ENTITIES-v1"),
    ("        'hl': s(r['Headline']) or o.get('hl', ''),", "        'hl': _hd(s(r['Headline']) or o.get('hl', '')),   # ENTITIES-v1"),
    ("    if s(r['Translated Headline']) or o.get('hl_en'): rec['hl_en'] = s(r['Translated Headline']) or o.get('hl_en', '')", "    if s(r['Translated Headline']) or o.get('hl_en'): rec['hl_en'] = _hd(s(r['Translated Headline']) or o.get('hl_en', ''))   # ENTITIES-v1"),
]


def chart_fn(log):
    def f(s):
        if CHART_DONE in s:
            return s
        i = s.index('function renderTimeChart(rows){'); j = s.index('\nconst QV = {', i)
        body = s[i:j]
        for old, new in CHART_EDITS:
            if body.count(old) != 1:
                raise SystemExit(f'chart: anchor found {body.count(old)}x: {old[:80]!r}')
            body = body.replace(old, new)
        if "$('#" in body.split(CHART_DONE)[1]:
            raise SystemExit('chart: a Data control id is left inside timeChart')
        s = s[:i] + body + s[j:]
        if s.count(ONLY_EDIT[0]) != 1:
            raise SystemExit('chart: fillOnly anchor')
        log.append('js: renderTimeChart -> shared timeChart(rows, o)')
        return s.replace(ONLY_EDIT[0], ONLY_EDIT[1])
    return f


def edits(s, pairs, label, log):
    for old, new in pairs:
        if new in s:
            continue
        n = s.count(old)
        if n != 1:
            raise SystemExit(f'{label}: anchor found {n}x: {old[:90]!r}')
        s = s.replace(old, new); log.append(f'{label}: edit {old[:50]!r}')
    return s


def rw(path, fn, log):
    s0 = open(path, encoding='utf-8').read(); s = fn(s0)
    if s != s0:
        open(path, 'w', encoding='utf-8').write(s)
    return s != s0


US_START, US_END = '/* ---------- USMAP-v1 geometry', '/* ---------- /USMAP-v1 geometry ---------- */'


def js_fn(log):
    geo = open(os.path.join(HERE, 'us_map.js'), encoding='utf-8').read().strip()
    blk = (US_START + ' (agent-tabs): US states, Albers USA with Alaska and Hawaii inset; from code/us_map.js ---------- */\n'
           + geo + '\n' + US_END + '\n'
           + open(os.path.join(HERE, 'tabs_tracker.js'), encoding='utf-8').read().rstrip('\n') + '\n')
    def f(s):
        s = edits(s, LABELS, 'js', log)
        s = chart_fn(log)(s)
        s = edits(s, AXIS_EDITS, 'js axis', log)
        s = edits(s, JS_PHASEB, 'js phaseB', log)
        if START in s:
            i = s.index(US_START) if US_START in s else s.index(START); j = s.index(END, i) + len(END) + 1
            if s[i:j] != blk:
                s = s[:i] + blk + s[j:]; log.append('js: tabs_tracker.js block refreshed')
        else:
            if s.count(BOOT) != 1:
                raise SystemExit('js: boot anchor')
            s = s.replace(BOOT, blk + BOOT); log.append('js: tabs_tracker.js block inserted')
        return s
    return f


def add_after(anchor, add, label, log):
    def f(s):
        if add in s:
            return s
        if s.count(anchor) != 1:
            raise SystemExit(f'{label}: anchor found {s.count(anchor)}x')
        log.append(f'{label}: tabs hook added')
        return s.replace(anchor, anchor + add)
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--js'); ap.add_argument('--reorg'); ap.add_argument('--assemble'); ap.add_argument('--build-data'); ap.add_argument('--views'); ap.add_argument('--prompt'); ap.add_argument('--lean-prompt')
    a = ap.parse_args()
    log = []
    if a.reorg:
        rw(a.reorg, lambda s: edits(edits(s, LABELS, 'reorg_tracker.js', log), REORG_PHASEB, 'reorg_tracker.js', log), log)
    if a.views:
        for fn, pairs in VIEW_PHASEB.items():
            pth = os.path.join(a.views, fn)
            if os.path.exists(pth):
                rw(pth, lambda s, pairs=pairs, fn=fn: edits(s, pairs, fn, log), log)
    if a.lean_prompt and os.path.exists(a.lean_prompt):
        rw(a.lean_prompt, lambda s: edits(s, LEAN_PROMPT, 'sheet_task_prompt.md', log), log)
    if a.prompt and os.path.exists(a.prompt):
        rw(a.prompt, lambda s: edits(s, PROMPT_PHASEB, 'prompt', log), log)
    if a.js:
        rw(a.js, js_fn(log), log)
    if a.assemble:
        rw(a.assemble, add_after(ASM_ANCHOR, ASM_ADD, 'assemble.py', log), log)
    if a.build_data:
        rw(a.build_data, add_after(BD_ANCHOR, BD_ADD, 'build_data.py', log), log)
        rw(a.build_data, lambda s: edits(s, BD_PHASEB, 'build_data.py', log), log)
    print('\n'.join(log) if log else 'TABS-v1: already applied')


if __name__ == '__main__':
    main()
