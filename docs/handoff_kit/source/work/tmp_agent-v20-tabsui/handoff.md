# Handoffs from agent-v20-tabsui (2026-10-28)

Changes that sit in files I don't own. The framework side is done in code/tracker/53_tabs.js.

## 1. agent-relrelated: build/tabs/releases.js (release page header, HEADER-v2)
The framework now draws every entity header with `tbHeadHtml(P)`:
- kicker
- title
- dek
- the facts in clusters (Who / What / Coverage / Links)
- a Links row with "Copy link to this page"

`P.extra` now renders in its own card (`.tbe-extra`) inside the `.tbe-head` wrapper, so test selectors `.tbe-head .tb-us` / `.tbe-head .clip` still match. The release page already works with flat `facts`: they are sorted into clusters by label. To finish Sammy's comment 8065396d, change `page.spec` in releases.js:
- `kicker: ['Press release', dl(ctx, it.date), it.src]`. That is type · date · source, so drop `['Date', …]` and `['Source', …]` from the facts.
- `dek: it.dek ? e(it.dek) : ''`. This is the one-line summary only. Move the official link out of `sub`.
- `links: [['Official release', it.url ? ctx.link(it.url, 'Official release', host) : '<span class="sub">Not posted on Gabriel’s or the Jewish Caucus’s site.</span>']]`. Keep that exact "Not posted on Gabriel…" text: releases.test.js looks for it in `.tbe-head`.
- Bills fact: wrap it as `ctx.hlist(bills.map(b => ctx.billLink(b, { date: it.date })))`. In v19 they render as plain text.
- Others named: `ctx.hlist(it.co.split(/;\s*/).map(e), 3)`, which shows the first 3 plus "+ N more" instead of a run-on sentence.
- Optional: pass explicit `groups` in this shape: `[{ key: 'who', label: 'Who', facts: [Others named, Gabriel quoted] }, { key: 'what', label: 'What', facts: [Type, Issue, Bills] }, { key: 'coverage', label: 'Coverage', facts: [Pickups, Related stories, Bill coverage] }, { key: 'links', label: 'Links', facts: [Official release, Saved copy] }]`. Also keep `facts` (the concatenation) for the harness's pageFacts.
- New ctx helpers: `ctx.hlist(items, n)`, `ctx.lines(items)`, `ctx.toneText(avg, n)`, `ctx.toneHtml(ctx.tone(rows))`, `ctx.affOf(r, author)`, `ctx.affOutlets(r)`.
- Facet blanks: the framework's `tbVals` now turns a blank single value into "Not recorded", listed last. A facet that returned '' to mean "no value" now shows "Not recorded". If one of yours should stay hidden instead, return `[]`.

## 2. main / owner of code/tracker/07_charts.js: month ticks on timeChart (Sammy comment cbaaaaef)
The entity-page "Coverage by month" chart (reporter, outlet, bill and release pages, via tbChartDraw) and Data's chart both use `timeChart`. At `iv === 'month'` it labels only the January buckets with the year (07_charts.js line ~129). Replace that line with month ticks for `iv === 'month'`:
```js
if (iv === 'month'){ const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const k = [1, 2, 3, 4, 6, 12].find(s => band * s >= 46) || 12; let end = -1e9, first = true;
  buckets.forEach((b, i) => { const mo = +b.slice(5, 7); if (k >= 12 ? mo !== 1 : (mo - 1) % k) return;
    const t = mo === 1 || first ? `${MON[mo - 1]} ${b.slice(0, 4)}` : MON[mo - 1], w = t.length * 6.4, x = m.l + i * band + band / 2;
    if (x - w / 2 < end + 8 || x + w / 2 > W) return; svg += `<text x="${x}" y="${H-8}" text-anchor="middle">${t}</text>`; end = x + w / 2; first = false; }); }
else buckets.forEach(/* the existing year / quarter labels */);
```
The same rule is already in bills.js's "Milestones and coverage" chart (MONTHAXIS-v1). Check it on a short span (e.g. #reporters/yue-stella-yu) and on a multi-year span (#outlets/ktla).

Story travel's spread curve is days after the original (day 0 …), not calendar time, so it has no month axis.

## 3. owner of code/tracker/21_manage_badge.js (Clips CSV, AVSHOW-v1)
Add two columns to `download('csv')`'s `cols`, after Format:
- `['Channel', r => r.av ? (r.av.channel || r.av.station || '') : '']`
- `['Show', r => r.av && r.av.type !== 'Web story' ? (r.av.show || '') : '']`

The tracker has the `avChannel(r)` / `avShow(r)` helpers in 01_authors.js.

## 4. Tests (final build agent: run once with the other suites)
I updated these expectations but did not run them (V20 brief: no suite runs):
- reporters.test.js
  - no default filters
  - TONELABEL text
  - AFFIL-v1 model ported into the test
  - header Outlets fact
  - the Yue Stella Yu check
- outlets.test.js
  - TONELABEL
  - the CSV "Tone avg" column is the number (2 decimals), plus new "Tone label" and "Rated stories" columns
- bills.test.js: no default filter; the old checks now open `cov=Yes` explicitly.

Pre-edit copies are in work/tmp_agent-v20-tabsui/pre/. releases.test.js and travel.test.js are untouched. Their header selectors (`.tbe-head`, `.tbe-facts > div`, `.tbe-sub`) still exist. travel.test.js reads `.tbe-sub`, and the dek still carries that class.
