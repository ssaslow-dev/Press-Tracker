# Insights tab — contract for the feature agents (agent-insights, 2026-10-27)

L = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib

Scope (DECISIONS 2026-10-27): five features — the digest (#6) is DROPPED. One new top-level tab, uncluttered.
agent-insights owns the shell, wiring, entry points, integration test and the ONE publish. Each feature agent writes
ONLY its own files under `L/build/insights/` (listed below). Never edit `code/*`, `build/js_merged.js`, `build/test_*`,
the workbook, or another agent's files. Never publish. No Exa.

| id (file stem) | label in sub-nav | DECISIONS feature |
|---|---|---|
| `release_pickup` | Press releases | (1) which outlets ran each Gabriel release, lag, original reporting within 7 days |
| `bill_timeline` | Bills | (2) per-bill stories over time + leginfo milestone markers |
| `story_travel` | Story travel | (3) original + reprints on a timeline (+ county map if reused) + top sources feeding reprints |
| `reporters` | Reporters | (4) outreach list, people only, CSV export |
| `tone_topic` | Tone by issue | (5) tone by topic over time |

Order in the sub-nav = the order of this table.

## 1. Files each feature agent writes

```
L/build/insights/<id>.js           the view (required)
L/build/insights/<id>_data.py      only if the view needs data the page doesn't have (optional)
L/build/insights/test/<id>.test.js its Playwright test (required)
L/build/insights/<id>.md           5–15 lines: what it shows, data used, decisions/assumptions, test result
```
Status log: `L/status/agent-<id>.md` (or the name the coordinator gave you). Hand back to the coordinator; agent-insights
integrates.

## 2. Page structure (owned by the shell)

- Header nav gets a 4th tab after Data: `<button role="tab" id="tab-in" data-tab="in">Insights</button>`.
- `<section id="view-in" hidden>` holds:
  - `.card.pad.in-bar`: `<h2 class="sec">Insights</h2>` + caption, and the sub-nav
    `<div class="seg in-nav" id="inNav" role="tablist">` — one `<button data-in="<id>" aria-pressed>` per registered view
    (same look as the existing `.seg` controls, e.g. "Most years covering him / New in the last 12 months").
  - `<div id="inBody">` — ONE container; the active view renders into its own child `<div class="in-view" data-in="<id>">`.
    Only the active view's div is visible; a view is rendered the first time it's shown and again when `ctx.refresh()`
    is called or the data changes (Update/refresh adds stories → shell re-renders the active view).
- URL hash: `#insights` → first view; `#insights/<id>` → that view; `#insights/<id>?k=v&k2=v2` → params passed to the
  view (see `ctx.params`). The shell keeps the hash in sync via `ctx.setParams()`.
- The Insights tab ignores the Clips/Data period filter by default: views use ALL of `ctx.D` unless they offer their own
  control. (Views may offer their own small controls inside their own card header.)

## 3. Module interface

Plain script (no ES modules / imports; it is inlined into the page as `<script id="ins-js-<id>">` after the main
script). Wrap it in an IIFE, `"use strict"`, define nothing global, and register once:

```js
(function(){ "use strict";
  AJGInsights.register({
    id: 'reporters',            // = file stem
    label: 'Reporters',         // sub-nav text (from the table above)
    render(el, ctx){ ... },     // draw into el (an empty div you own); may be called again: rebuild el.innerHTML
    destroy(){ ... }            // optional: remove listeners on document/window you added
  });
})();
```
- `render` must be synchronous or return a Promise; it must not throw on empty data (show `<div class="empty">…</div>`).
- Put listeners on `el` (event delegation), not on `document`, unless you remove them in `destroy`.
- Do not touch DOM outside `el`, except through ctx helpers (story panel, Clips navigation, tooltip, toast).
- Render budget: < 300 ms on the full data (4,121 stories) on a laptop. Memoize per `ctx.version`.
- Keep each file small (aim < 25 KB, hard cap 40 KB unminified).

## 4. `ctx` — what the shell gives every view (read-only)

Data
| name | what |
|---|---|
| `ctx.D` | the story records (array; one per Original; fields per CONTRACT.md + `authors`, `akinds`, `atitle`, `pick` = live reprint count, `reps`, `tone`, `topic`, `bills`, `county`, `rc`, `reach`, `media`, `role`, `lang`, `date`, `prec`) — do NOT mutate |
| `ctx.byId(id)` | record by Story ID |
| `ctx.rows()` | the `rows` dedupe index over ALL sheet rows, decoded to objects `{aid,sid,kind,outlet,date,hl,links}` (cached) |
| `ctx.bills()` | `billsinfo.rows` (leginfo list: `{bill, session, title, role, status}`) |
| `ctx.block(name)` | parsed `<script id="ins-<name>" type="application/json">` built from your `<name>_data.py` (null if absent) |
| `ctx.version` | integer, bumps when D changes (memo key) |
| `ctx.TODAY`, `ctx.LAST` | today's ISO date; date of the newest day-dated story |

Vocabulary / order
`ctx.TONE_ORDER` (['Very positive','Positive','Neutral','Negative','Very negative','Not rated']), `ctx.RANK` (topic,
media, pub, role, reach, tone orders), `ctx.REACH_ORDER`, `ctx.rated(r)` (tone is rated), `ctx.reachTags(r)`,
`ctx.billName(b)`, `ctx.countiesOf(r)`, `ctx.authorKey(a)`, `ctx.canonAuthors(list)`, `ctx.authorKind(a)`
(person|staff|board|wire|org, from `akinds`).

Formatting
`ctx.esc`, `ctx.fmt` (thousands), `ctx.pl(n, one, many)`, `ctx.iso(date)`, `ctx.addDays(iso, n)`,
`ctx.monthName('YYYY-MM')`, `ctx.dateLabel(r)` (respects prec), `ctx.daysBetween(isoA, isoB)`.

Colour (CSS custom properties — always use these strings, never hex)
- `ctx.colorFor(key, value)` → `var(--sN)` / `var(--tvp)` … (same colour the rest of the tracker uses for that issue,
  outlet, tone…). Tone: `--tvp --tp --tn --tng --tvn` (very pos … very neg), `--tnr` not rated.
- Single-series bars `var(--bar)`; sequential ramp `var(--q1)`…`var(--q6)`; text `--ink --ink-2 --ink-3`; rules
  `--line --line-2`; panels `--panel --panel-2`; accent `--accent`; good/warn `--good --warn`.

Chart helpers (the ones the Data tab uses — use them so charts match)
`ctx.niceMax(v)`, `ctx.barPath(x,y0,y1,bw,roundTop)`, `ctx.axis(svgOpen, W, H, m, ymax, suffix)` (grid + y labels),
`ctx.barList(el, key, items, foot)` (horizontal bars, items `{k, v, label, tip}`; clicking one filters Clips by
`key`=k when key is a Clips facet), `ctx.reporterBars(el, rows, limit)`, `ctx.showTip(evt, html)` / `ctx.hideTip()`
(tooltip markup: `<div class="th">title</div><div class="row"><span class="l">label</span><b>value</b></div>
<div class="foot">hint</div>`), `ctx.drawCountyMap(svgEl, counts, opts)` — reuse of the Data tab's California map
(counts = Map county→n; opts `{onClick(county), tip(county)}`); available only if the shell can factor it out cleanly —
check `ctx.drawCountyMap` exists before using it.

Navigation / actions
| name | what |
|---|---|
| `ctx.openStory(id, order?)` | opens the existing story panel (side sheet) for a Story ID |
| `ctx.clips(filters)` | jump to Clips with filters, e.g. `{author:'Jane Doe'}`, `{bills:'AB 1127'}`, `{topic:'Guns', tone:'Negative'}`; keys = Clips facet keys (topic, bills, reach, role, media, pub, author, county, lang, tone) |
| `ctx.params` | object of the hash params for this view (e.g. `{id:'s00228'}`, `{author:'Jane Doe'}`) |
| `ctx.setParams(obj)` | update the hash params without re-rendering |
| `ctx.go(viewId, params)` | switch to another Insights view |
| `ctx.saveFile(filename, blobOrString)` | downloads capability (falls back to a browser download) — use for CSV |
| `ctx.csv(rows, cols)` | CSV text (BOM, quoted, CRLF) from rows + `[[header, key or fn], …]` |
| `ctx.copy(text, okMsg, btn)` | clipboard with the tracker's "Copied!" button effect |
| `ctx.toast(msg)` | toast |
| `ctx.refresh()` | re-render this view |

## 5. Shared style rules (match the Data tab exactly)

- Layout: each view is a stack of `.card` blocks; a chart card is `<div class="card chartcard">`, a list/text card is
  `<div class="card pad">`. Two side by side: wrap in `<div class="two">`. Gap between cards = what `.rp-sec` uses
  (wrap your view in `<div class="in-sec">` — the shell styles it like `.rp-sec`).
- Card head: `<h2 class="sec">Title</h2><div class="cap">One-sentence caption: what it shows + "Click … to …".</div>`.
  Section intro if needed: `<div class="rp-h"><h2>…</h2><p>…</p></div>`.
- Controls inside a card: `<div class="an-controls"><label>Group by<select class="sel">…</select></label></div>`;
  toggles: `.seg` buttons with `aria-pressed`; text buttons: `.btn` (primary action `.btn.primary`, at most one per
  view); inline links: `.linkbtn`. Tables: inside `<div class="tablewrap">` with `<table class="db">` look, or the
  compact `details.dt` table style ("Show the numbers").
- Fonts: inherit — headings already use `--f-display` (Roboto Slab) via `h2.sec`; body `--f-body`. No new fonts, no
  new font sizes below 11.5px.
- Charts: inline SVG, `viewBox` sized to the container width (`el.clientWidth`, min 300), height 180–300; margins like
  the Data tab (`{l:34-40, r:6-8, t:8-16, b:24-26}`); y gridlines via `ctx.axis`; bars with `ctx.barPath` (3px rounded
  top), single series in `var(--bar)`; baseline `<line class="base">`; year labels at the bottom; hover = invisible
  `<rect class="hit">` per band + `ctx.showTip`; click = drill to Clips or open the story. Legends: `<div class="legend">`
  with `<span class="it"><span class="sw" style="background:…"></span>Label</span>`.
- Milestone/event markers (bills): thin vertical rule in `var(--ink-3)` dashed + small label in `--ink-2`, 11.5px.
- Max 8 colours in one chart; group the rest as "Other" `var(--sother)`. Never encode meaning by colour alone (label or
  tooltip too). Dark mode works automatically if you only use the tokens.
- Wording: plain, short, sentence case; "story/stories", "reprint", "outlet", "issue" (not "topic") in the UI; dates
  like the rest of the tracker (`ctx.dateLabel`). No emojis.
- Mobile: must not overflow at 375px wide (the shell checks).
- No new buttons outside your view. The ONLY entry points elsewhere are the shell's: story panel → "Trace this story"
  (`#insights/story_travel?id=<Story ID>`) and the author link in the story panel → "Outreach list"
  (`#insights/reporters?author=<name>`). `story_travel` must honour `params.id`; `reporters` must honour
  `params.author` (scroll to + highlight that row).

## 6. Data-block conventions (only when the page lacks the data)

- Prefer computing in the browser from `ctx.D`, `ctx.rows()`, `ctx.bills()`.
- Press releases are NOT in `D` (build_data drops `Press release = Yes` rows as entries and reprints); release data
  needs `release_pickup_data.py`. Milestones for bills come from `L/work/out/bill_milestones.json`
  (agent-billstatus; may not exist yet → wire it, render "Milestones not loaded yet" when null).
- `L/build/insights/<id>_data.py` defines exactly:
  ```python
  def build(cov, data, ctx):  # -> JSON-serialisable object, or None (no block)
      ...
  ```
  `cov` = pandas DataFrame of the Coverage sheet (`pd.read_excel(xlsx, sheet_name='Coverage', dtype=str).fillna('')`,
  the same frame build_data reads); `data` = the list of story records build_data wrote (data.json); `ctx` = dict
  `{'xlsx': path, 'lib': L, 'blocks_dir': path, 'today': 'YYYY-MM-DD', 'read_sheet': fn(sheet_name)->DataFrame or None}`
  (`read_sheet('Bills')` for a future Bills tab). No network, no writes, standard library + pandas only, deterministic
  output (sorted keys/lists), runs in < 10 s.
- The shell's `code/insights_data.py XLSX BLOCKS_DIR` (integrator-owned) imports each `<id>_data.py`, writes
  `BLOCKS_DIR/ins_<id>.json`, and assemble adds `<script id="ins-<id>" type="application/json">`. Size cap per block:
  150 KB (use short keys, arrays not objects, Story IDs/Article IDs instead of repeated text). Page budget is tight
  (~46 MB artifact headroom; index.html is ~9.1 MB).
- If a new sheet tab is needed (e.g. "Bills"), describe columns and source in your `<id>.md`; the coordinator does the
  sheet write. Until then read the JSON file via a fallback path in ctx (`ctx['lib']`).
- The sheet task rebuilds the tracker from `pipeline/` on Refresh — the integrator ships your `.js` and `_data.py` there
  too, so they must run unchanged in that context (no paths outside `ctx`).

## 7. Testing

Test page (built by agent-insights from the live v9 data, shell included, NO feature modules):
`L/build/insights/test/srv/index.html` (+ `srv/articles/manifest.json` stub). Blocks from `final_pass/F7/build/blocks`
+ any `ins_*.json` you produce (put yours in `L/build/insights/test/blocks/ins_<id>.json` — the harness injects it).

Harness: `cd L/build/insights/test && NODE_PATH=/opt/npm-tools/node_modules MOD=<id> node harness.js`
- serves `srv/`, stubs `window.claude` (db/downloads), loads the page, injects `../<id>.js` (and `blocks/ins_<id>.json`
  if present), opens `#insights/<id>`, then runs `require('./<id>.test.js')(page, ok, h)`; prints PASS/FAIL lines and
  exits 1 on any FAIL. Viewports: 1400×1000 then 375×800.
- `h` = `{ open(params) → navigate to the view with params, view → ElementHandle of your .in-view, errors → page errors so
  far, downloads → files passed to saveFile [{filename, text}], clipboard → last copied text, data → D length }`.
- Every test file must check at least: renders with no page errors; non-empty with real data; the numbers it shows for
  2–3 hand-checked cases equal an independent computation from `srv/blocks` (read the JSON in Node, not from the page);
  click-throughs (story panel / Clips) work; no horizontal overflow at 375px; empty-data case (h.open with a filter /
  param that yields nothing) shows `.empty`; any param entry point (`id`, `author`) works.
- Harness self-check: `MOD=_shell node harness.js` (shell alone: tab, sub-nav, hash routing, entry points).

Integration (agent-insights): all five modules + blocks into the real build → harness `MOD=all` (each test again on the
integrated page) + display suite + sheet-task rebuild check; then ONE publish.

## 8. Hand-back checklist (feature agents)
- [ ] `<id>.js` registers once, no globals, no edits outside your files
- [ ] `<id>_data.py` (if any) follows §6, block ≤ 150 KB, deterministic
- [ ] `test/<id>.test.js` passes via the harness at both viewports
- [ ] `<id>.md` written; status log updated with test result and block size

## 9. Shell notes (added 18:1xZ, after the shell self-check passed 38/38)
- Shell = `build/insights/_shell/` (shell.js, patch_insights.py, insights_assemble.py, insights_data.py,
  build_testpage.sh). Names starting with `_` in build/insights are reserved for the integrator; assemble includes every
  other `build/insights/<id>.js` (not `*.test.js`) as a view, in sub-nav order. Sub-folders (e.g. your scratch
  `test_<id>/`) are ignored by the build.
- Chart SVGs go inside `<div class="chart">` — that wrapper gives the Data tab's grid, text, `.hit` and `.base` styles.
- `ctx.authorKind(a)` returns 'person' when a name has no recorded kind.
- Harness picks a free port by itself (several agents can run it at once); `PORT=` to force one.
- If the test page is stale (after the integrator rebuilds the tracker JS), rerun
  `build/insights/_shell/build_testpage.sh` — only the integrator needs to; feature agents just run the harness.
- The view a user opens sticks; with no choice the first view in sub-nav order shows. Deep links
  `#insights/<id>?k=v` work on page load too.
