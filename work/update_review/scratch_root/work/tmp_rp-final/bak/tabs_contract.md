# Tab modules — contract for the tab agents (TABS-v1, agent-tabs, 2026-10-27)

L = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib

Sammy's spec: DECISIONS.md "2026-10-27 — Restructure: Press desk tools become main tabs" plus the later additions relayed by the
coordinator (listed per tab in §9). agent-tabs owns the framework (code/tracker/53_tabs.js, formerly code/tabs_tracker.js + code/patch_tabs.py,
code/tabs_assemble.py, code/tabs_data.py, build/tabs/_common_data.py, build/tests/tabs/harness.js, _framework.test.js, stub.js)
and integrates and publishes. **Each tab agent writes ONLY its own files** (§1). Never edit code/*, build/js_merged.js,
build/insights/*, another tab's files, the workbook, or any doc. Never publish. No Exa. No workbook writes (if your tab seems to
need a sheet value, stop and say so in your status file).

## 0. Menu (fixed by the framework)

`Home · Clips · Data · Reporters · Outlets · Press releases · Bills · Story travel`. Press desk is gone.

| tab id (file stem) | label | URL slug | entity page URL | old links that redirect here (framework) |
|---|---|---|---|---|
| `reporters` | Reporters | `#reporters` | `#reporters/<slug>` | #insights, #insights/reporters, #press-desk, #press-desk/pitch, #pitch, data-ins-go="reporters" |
| `outlets` | Outlets | `#outlets` | `#outlets/<slug>` | — (new) |
| `releases` | Press releases | `#press-releases` | `#press-releases/<slug>` | #insights/release_pickup, #press-desk/releases, #release_pickup |
| `bills` | Bills | `#bills` | `#bills/<slug>` | #insights/bill_timeline, #press-desk/bills, #bill_timeline |
| `travel` | Story travel | `#story-travel` | `#story-travel/<slug>` | #insights/story_travel, #press-desk/story-travel, #story_travel, data-ins-go="story_travel" |

`win=12/24` is dropped by the framework. Old params (author, id, bill, s, range, issue, year, topic, pick) reach your module's
`legacy(params, ctx)` (§3), which turns them into your own state.

## 1. Files each tab agent writes

```
L/build/tabs/<id>.js             the module (required; plain script, IIFE, "use strict", no globals, < 40 KB)
L/build/tabs/<id>_data.py        only if the page lacks data you need (optional; §6)
L/build/tests/tabs/<id>.test.js  its test (required; §8; moved from build/tabs/test/ 2026-10-28)
L/build/tabs/<id>.md             10-25 lines: what it shows, data used, decisions/assumptions, test result, screenshots
L/status/agent-tab-<id>.md       your log
```
Helpers/scratch: `L/work/tmp_agent-tab-<id>/`. Files starting with `_` in build/tabs are the framework's.

## 2. Register

```js
(function(){ "use strict";
  AJGTabs.register({
    id: 'outlets',                 // = file stem; label and slug come from the menu table
    list: { ...search-tab spec... },   // §4: the tab's main page
    page: { ...entity-page spec... },  // §5: what a click on a row opens (#<slug>/<sub>)
    legacy: function(params, ctx){ return { params: {...state...}, sub: '' }; }   // §3, optional
  });
})();
```
`list` is required (the five tabs are search tabs). `render(el, ctx)` instead of `list` is allowed only for a fully custom page
(ask agent-tabs first).

## 3. URL state and legacy links
- The framework keeps `#<slug>[/<sub>]?<params>` in sync. Your state lives only in params (the components encode it).
- Reserved param names: `q`, `sort`, `open`, `pg`, `per`, `when`, chart keys `ci cb co cm cs cf ca ct cq`, and on entity
  pages the Clips facet keys `topic bills reach role media pub author county lang tone`. Facet keys of your list must not use
  these (use e.g. `outlet`, `iss`, `bill`, `lng`, `pubr`, `date`, `active`, `n`, `tmix`).
- `legacy(p, ctx)`: called for an old link / old entry point. Reporters: `author` (open that reporter's page if known, else
  search for the name), `issue`. Releases: `id` (story or offNNN key → that release's page), `year`, `topic`, `pick`.
  Bills: `bill`, `s` (session), `range`. Story travel: `id` (Story ID → that story's page).

## 4. The search tab (`list`) — framework component, Clips look
Search box (accent- and case-insensitive, multi-word AND, 120 ms debounce), filter rail with counts (a drawer, as in Clips;
counts = results if that value were picked, with the other filters kept), chips with remove buttons + Clear all,
result count "N of M <noun>", sortable list (table head on desktop, sort menu ≤ 760 px), Show more (step desk/phone),
Export menu (your extra copies, Copy list as TSV, Download CSV of ALL listed rows), state in the URL.

```js
list: {
  noun: ['outlet', 'outlets'], title: 'Outlets', cap: 'One sentence: what it shows. Click … to …', placeholder: 'Search outlets, publishers',
  // flat:     items(ctx) -> [item]                         (memoized by the framework per data version)
  // two-level: units(ctx) -> [story], group(units, ctx) -> [item]   (unit facets filter stories BEFORE grouping, so an
  //            item's counts, tone average, last story … are over the stories that pass the date/issue/… filters)
  key: it => it.key, text: it => 'searchable text',
  facets: [ { key, label, type: 'multi'|'one'|'date', level: 'unit'|'item', vals(x) -> string|[strings],
              order: 'count'|'alpha'|[fixed order]|fn, search: bool, limit: n, hint, open: bool, def: default value(s),
              sw: v -> css colour, note: v -> small text, label_: v -> display text,
              options (type 'one'): [{ id, label, test(x, ctx) }], any: 'label of the no-filter choice',
              date(x) -> iso | [isos] and presets (type 'date'; default ctx.dates: 30d 3m 6m 12m 24m 5y + custom from/to) } ],
  columns: [ { key, label, val(it) (sort + CSV), sort(it)?, cell(it, ctx) -> html, num, dir: default sort direction,
               csv(it)? | csv: false, csvLabel?, sortable: false? } ],     // first column = the name (put a .tt-open button in it)
  sort: { key, dir }, step: { desk: 100, phone: 25 },
  row(it, ctx) -> html            // optional: a custom row (e.g. Clips form via ctx.clipItem) instead of the table
  open: 'page' | 'detail' | '',   // 'page' -> page.slug(it) ; 'detail' -> detail(it, el, ctx) drawn under the row
  answer(res, st, ctx) -> one sentence (optional), empty(st) -> text, copies: [{ label, sub, text(res, st, ctx), ok(res) }],
  csvName(st, ctx), csvExtra: [[header, fn]]
}
```
Item facets see the grouped items; unit facets see stories. Counts are exact for both (the framework regroups per value).
Defaults (`def`) show as chips; removing one is kept in the URL as `<key>=~`.

## 5. The entity page (`page`) — framework component
`#<slug>/<sub>`: back link (returns to the list with its filters), header card, the **Coverage over time chart** (Data's chart,
shared `timeChart`, over the entity's stories: quick views volume/issues/tone/reach/formats/role/with reprints, group by,
colour by, share, average line, **tone average line** on a zoomed symmetric right axis; a click on a bar filters the list to
that period; ≤ 3 stories → a plain line instead of a chart), then a Clips-style list of the entity's stories: its own search
(also searches saved-page text), Clips' facets with counts, date select, sortable table, pager, chips, story panel on click,
Export (Copy clips list / Copy for spreadsheet / CSV, via Clips' own exporters). Links inside the list filter the page.
Nothing on these pages jumps to Clips (Sammy: no "See all in Clips" / "Open in Clips" in the tabs).

```js
page: {
  slug: (item, ctx) => ctx.slug(item.name),        // stable, readable; must round-trip through find()
  find: (sub, ctx) -> entity | null,               // independent of the list's filters (a deep link works on its own)
  spec: (entity, ctx) -> { kicker: 'Outlet', title, sub: html, facts: [[label, html]], extra: html,
                           rows: [tracker stories], noun: 'outlet', placeholder?, backLabel? }
}
```
Facts are the row's data (spec per tab in §9). Cross-links: `ctx.pageLink('outlets', ctx.slug(name), name)` (reporter page →
outlet pages, outlet page → reporter pages). A story: `<button class="linkbtn" data-tbstory="sNNNNN">` opens the story panel.
Pages without tracker stories (e.g. a release with no pickup) pass `rows: []` and put their content in `extra`.

## 6. Data
Prefer the page's data (ctx.D, ctx.rows(), ctx.bills(), ctx.block('release_pickup' | 'bill_timeline' | 'story_travel'),
ctx.block('common')). If you need more, `build/tabs/<id>_data.py` with `build(cov, data, ctx)` exactly as
build/insights_contract.md §6 (same ctx incl. `read_sheet`), written to `tab_<id>.json` and read with `ctx.block('<id>')`.
Cap 150 KB, deterministic, no network, no writes. The button rebuilds it from pipeline/tabs/ (agent-tabs ships it).

`tab-common` (framework, build/tabs/_common_data.py): cleaned outlet names and the sheet's Publisher column.
- `ctx.outlet(rawName, aid?)` → canonical outlet ("Sacramento Bee, The" → "The Sacramento Bee"; case/accent/"The" variants
  merged under the spelling the outlet uses as its own publisher (CalMatters), else the most common; AP wire feeds →
  Associated Press; ALIAS: "Daily News" rows published by Southern California News Group → Los Angeles Daily News, per row).
  Use it for every outlet name you show or group by (stories: `ctx.outlet(r.outlet, r.aid)`; reprints `ctx.outlet(p.outlet, p.aid)`).
- `ctx.publishers(outlet)` → `[{name, d0, d1, n}]` (the sheet's Publisher column as dated spans; Santa Maria Times / Lompoc
  Record / Santa Ynez Valley News rows → Santa Maria News Media as written in the sheet), `ctx.publisherOf(outlet, date?)`.
  Note: `r.pub` in data is the OLD tracker's display name, not the sheet's Publisher. Never show it as the publisher.

## 7. ctx (everything in build/insights_contract.md §4, plus)
| name | what |
|---|---|
| `ctx.tab`, `ctx.sub`, `ctx.params`, `ctx.setParams(p)`, `ctx.refresh()` | current tab, entity sub, URL params |
| `ctx.go(tab, params, sub)`, `ctx.openPage(sub)`, `ctx.back()` | navigation inside the tabs |
| `ctx.tone(rows)` | `{avg, n, text, label}`: average over RATED stories (Very negative −2 … Very positive +2), `text` like "−0.4 (n=12)", '' when none. Use it for every tone average (Reporters and Outlets must match) |
| `ctx.outlet`, `ctx.publishers`, `ctx.publisherOf` | §6 |
| `ctx.clip(r, extra, {links:false}?)` | a story exactly as Clips lists draw it (opens the story panel) + its links with copy icons |
| `ctx.clipItem(r, extra, opts)` | the non-clickable picker form (from the Insights shell) |
| `ctx.link(url, label, sub)`, `ctx.cpBtn(url)`, `ctx.storyLinks(r)` | a link with the copy icon on its LEFT (required for every link) |
| `ctx.pageLink(tab, sub, label, title)` | a button to another tab's entity page |
| `ctx.embed(viewId, el, params)` | draw an old Insights view (bill_timeline, story_travel, release_pickup, reporters) into el; its params never touch the URL. Use pieces of it only if the redesign in §9 keeps them |
| `ctx.niceScale(v, kind)`, `ctx.niceMax(v, kind)`, `ctx.axis(...)` | AXIS-v1: every chart axis scales to the data shown (kind 'count' integer ticks, 'pct' ≤ 100 but zooms, 'tone' symmetric); an all-zero chart shows `.empty` |
| `ctx.usMap(host, outlets, {onState(abbr, outlets), clickHint})` | USMAP-v1: the 50-state map (same shading/legend/hover/click as the CA county map; Alaska and Hawaii inset). `outlets` = canonical outlet names of the data shown; it draws the map only when MORE than 5 distinct out-of-state statewide/regional/local sources qualify (National/International/Trade-advocacy Reach, Wire medium and state "USA" are national: one "National outlets: N" line; outside the US: one line); otherwise one "Out of state: …" line. `onState` filters your list; returns the model. `ctx.outModel(outlets)` = the model only. Use it wherever you show the CA county map (`ctx.drawCountyMap`) |
| `ctx.fold(s)`, `ctx.slug(s)`, `ctx.dates`, `ctx.cut(months)`, `ctx.langOf(r)`, `ctx.vals(r, key)`, `ctx.FACETS` | helpers |
| `ctx.phone` | ≤ 640 px |
Do not call `ctx.clips` (no jumps to Clips from the tabs).

**Design system (hard requirement, Sammy 2026-10-27):** only the tracker's own classes (.card, .pad, .chartcard, .sec, .cap,
.seg, .linkbtn, .btn, table.db, .chip, .badge, .clip, .opt, details.facet, .legend, .cmap-legend, .empty, .note) and CSS
variables; the Clips/Data type scale and weights; right-aligned tabular counts; Data's empty states; dark mode must work (tokens
only). No inline style attributes, no one-off colours or font sizes; if you need a style the framework lacks, ask agent-tabs to
add it to the shared CSS. agent-tabs runs a light/dark visual pass at 1400/390 next to Clips and Data before publishing.
Style: build/insights_contract.md §5 (tokens only, no hex, Data look, no new fonts, sentence case, no emojis, ≤ 375 px no
overflow). Proper names as their owners write them: LegInfo (UI text; URLs unchanged), CalMatters, ProQuest, NewsBank, TinyFish.

## 8. Tests
Build the test page once per framework change: `bash build/tests/tabs/build_testpage.sh` (agent-tabs keeps it current; it puts
every module in build/tabs/ into srv/index.html). Run your tab alone:
`cd build/tests/tabs && NODE_PATH=/opt/npm-tools/node_modules MOD=<id> node harness.js` (VP=desk|phone for one viewport).
The harness runs `tabs_data.py --only <id>` when you have a `_data.py`, injects your module if the page lacks it, opens
`#<slug>`, then `require('./<id>.test.js')(page, ok, h)` at 1400×1000 and 390×844.
`h`: open(params, sub, tab) · hashGo(hash) · reload(hash) · view() · hash() · params() · count() · total() · rowKeys() ·
search(t) · facet(key, value) · facetCount(key, value) · customDate(key, from, to) · chips() · removeChip(i) · clearAll() ·
sort(key) · more() · exportCsv() · exportCopy(i?) · openRow(key) · pageTitle() · pageFacts() · pageCount() · pageTotal() ·
pageSearch(t) · pageRowIds() · back() · chartTop(sel) · chartEmpty(sel) · markNav() / leftTab() · downloads() · clipboard() ·
overflowX() · data() · block(name) · tabBlock() · fold(s) · TODAY() · shot(name) (→ work/tmp_agent-tabs/shots/) · phone.
Every test must check, at both viewports: renders, no page errors; search (case + accent); EACH facet; combined facets;
chip removal; sort; detail/page; export (CSV rows = count + header); URL round-trip (reload with the hash restores
list and page); counts recomputed in Node from srv/blocks/*.json (never read from the page) for 2–3 hand-checked cases;
legacy links from §3; the entity page (header facts vs independent values, in-page search, chart counts per year vs
independent, back link); `h.leftTab() === ''` after clicking around (never #clips); no horizontal overflow; screenshots
of list and page at both widths. Reference: build/tests/tabs/_framework.test.js and stub.js.

## 9. Per-tab spec (Sammy, 2026-10-27; coordinator relays)
**Reporters** (Pitch renamed). Units = stories (not "Op-ed by Gabriel"; Jesse Gabriel and the story's author-title strings
left out), people by `ctx.authorKey` + canon. Search name + outlet. Facets: outlet, outlet type/audience (Reach, Medium),
issue, bill, language, date range (default last 24 months), story count, tone mix, byline type with "Staff bylines" handling
(default people only, like Pitch), active within (presets + custom). Row: name, outlets, stories, last story, top issues,
**tone average (n)** (put back; ctx.tone), negative count. Copy names ("Name (Outlet)" per line), 25-row phone cap with Show
more. Click → **reporter page** `#reporters/<slug>`: facts = outlets (links to outlet pages), title(s) if the sheet has them
(r.atitle), stories, last story, top issues, bills, tone average with n, negative count; the chart; the story list.
**Outlets** (new; patterned on Reporters). One row per canonical outlet (ctx.outlet). Row: outlet, publisher
(ctx.publishers; dated spans when it changed), stories, originals vs reprints (reprints from r.reps of other stories), last
story, top issues, tone average (n), negative count, top reporters, language and county/audience where the data has them.
Facets: publisher, language, county/audience, issue, date range, story count, tone, active within. Click → **outlet page**
`#outlets/<slug>`: facts = publisher, counts, tone average, last story, top issues, reporters (links to reporter pages), links.
**Press releases** (all 241 of ins-release_pickup). Search title + dek (release body texts are 915 KB, over the 150 KB
block cap, so not searched; say so in the caption). Facets: date range, source (office / Jewish Caucus / both sites / not
posted officially), type, issue, bills, Gabriel quoted, picked up yes/no, number of pickups, outlet that ran it. Row: date,
title, source, pickups. Click → **release page**: official link + copy, type, quoted, dek, pickups as Clips-style items
(rows block: headline + link per pickup; they are not tracker stories), the before/after coverage stat, follow-up stories,
and (integrator data, Phase B) the stories that "use release text" kept separate from its copies. Type / quoted / dek come
from the sheet's Press releases tab: agent-tabs extends ins-release_pickup with appended columns in Phase B; until then
read them from your `releases_data.py` if you need them now (ask agent-tabs first, to avoid two copies).
**Bills** (bill + session items; AB 787-style numbers reused across sessions are separate rows). Search number + title.
Facets: session, final status, issue, milestone type, date range, has coverage, has release, role (author/coauthor). Row:
bill, title, session, status, stories, last activity. Click → **bill page**: header with metadata + milestones (dates and
labels), LegInfo link + copy ("LegInfo history"), related releases, the chart, the story list. No "See all in Clips".
**Story travel** (stories that ran in other outlets). Search headline, outlet, author. Facets: original date range, original
outlet, issue, reprint count, outlets it reached, language. Rows in Clips form + reprint count. Click → **story page**:
one-line summary ("Picked up by N outlets in D days; furthest: …; in-language: K"), a **spread curve** (cumulative step line of
outlets by day since the original, day 0 marked, milestone labels "5 outlets by day 2", shared auto-scaled axis), the
**pickup ladder** (one row per outlet in the order it ran: outlet → outlet page link, type chip from Reach/Medium/Language,
date and "+N days", headline if different, link with copy icon; same-outlet repeats grouped "2 copies"), and optionally
"Where it ran" (county list/map via ctx.drawCountyMap) when most counties are known. The old +1…+7 dot grid is removed.

## 10. Hand-back checklist
- [ ] module registers once, no globals, only your files changed; `node --check` passes
- [ ] `MOD=<id>` harness passes at both widths; screenshots listed in `<id>.md`
- [ ] `<id>.md` + status log written; block size if any

## Addendum (coordinator, Sammy 2026-10-27 23:50): bill links everywhere
Every bill number shown anywhere in the tracker (tab rows, entity-page headers, release rows/pages, story panel, reporter/outlet pages, Data cards, Home) is a link to that bill's page in the Bills tab (#bills/<slug>, the Bills module's slug; AB 787's two sessions resolve to their own pages by the story/release date). Exception: inside the Clips tab, clicking a bill sets the Clips bill filter instead (existing Clips behaviour). Use one shared helper, ctx.billLink(bill, {date}) → in Clips it filters, elsewhere it navigates; integrator adds it to the framework in Phase B — tab modules call it (or render <a data-bill> that the helper upgrades) rather than building their own.

## Addendum (agent-v19finish, 2026-10-28): link scope, embedded rows, page icons
- `ctx.facetLink(field, value)` / `ctx.issueLink(topic)`: attribute → Clips filtered by it; on an entity page they carry `page.scope(entity, ctx)` → `{sel:{pub|author|bills:[..]}, when?:[from,to,label], ranin?, label}` (set by the framework before `spec()`). Fields = Clips FACETS keys; anything else stays text.
- `spec().embeds: [{tab, title, cap, unit(u) | item(it), cols:[keys], limit}]`: that tab's own list rows, filtered to the page (`ctx.miniList(host, tab, o)`), drawn between the header card and the chart; nothing is drawn when no row qualifies.
- Entity-page story rows: outlet → outlet page, bill → bill page, issue/reach tags → Clips with the page's scope, author → reporter page; the filter rail still filters the page.
- Story headlines open the story panel everywhere; Story travel rows add "How it spread ›" (`.tt-open`) for the page.
