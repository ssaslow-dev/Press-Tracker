# agent-tabs — Press desk tools become main tabs (Sammy 2026-10-27) → v19

## Log
- 22:4xZ read README, DECISIONS (Restructure entry = spec + standing rule), CONTRACT, agent-relrule (v18 recipe, parked PERIOD stays parked), agent-reorg, insights_contract, the 5 views, reorg_*.js, insights_shell.js, Clips code in build/js_merged.js.
- Coordinator additions folded in: Outlets tab (+ tone average back on Reporters), outlet page and reporter page (entity pages, #outlets/<slug>, #reporters/<slug>).
- Coordinator re-plan: this agent = framework owner + integrator. PHASE A (framework only, no publish): menu + mounting + redirects, shared search-tab component, shared entity-page component, shared helpers, tab-module contract (build/tabs_contract.md), harness (build/tabs/test/), stub tab. PHASE B after the per-tab agents hand back: apply_all wiring, full tests, pipeline-rebuild proof, docs, v19 publish.
- No tab-specific code had been written when the re-plan arrived (only reading/design), so every tab is open for the tab agents.

## Phase A (framework) — done 2026-10-27 ~23:5xZ, no publish
Files (all new unless noted):
- code/tabs_tracker.js — TABS-v1 tracker block: menu (8 tabs; Press desk hidden), routing #<slug>[/<sub>]?params, page-load and
  hashchange deep links, old-link redirects (#insights[/id], #press-desk[/slug], #release_pickup|#bill_timeline|#story_travel|#pitch,
  data-ins-go entry points, win dropped), AJGTabs.register, search-tab component, entity-page component (Clips-style list +
  Data's chart + in-page search + back link), helpers (tone average, outlet names, publisher lookup, clip/link/copy icons,
  page cross-links, embed of old views), USMAP-v1 state map (+ Data county card hook), phone tab row scrolls sideways.
- code/us_map.js — US states geometry (us-atlas@3.0.1 states-albers-10m, topojson-simplify@3.0.3 weight 2; 39 KB).
- code/patch_tabs.py — idempotent: inserts USMAP geometry + TABS block before boot; Data link labels (also in
  code/reorg_tracker.js); CHART: Data renderTimeChart -> shared timeChart(rows, o) (Data output identical apart from AXIS);
  AXIS-v1: niceScale/niceMax/axisTicks (every chart axis scales to the data; empty state when all zero); assemble.py and
  build_data.py hooks for tab modules/blocks. Run twice on copies: second run "already applied"; node --check OK.
  NOT yet wired into apply_all (Phase B step 4l).
- code/tabs_assemble.py, code/tabs_data.py (pipeline files for Phase B), build/tabs/_common_data.py (tab-common block:
  canonical outlet names, Daily News/SCNG alias per row, Publisher spans, out-of-state outlets; 57 KB).
- build/tabs_contract.md — the module contract for the tab agents (incl. Sammy's later additions per tab).
- build/tabs/test/: build_testpage.sh (v18 page + patched JS + modules + blocks -> srv/index.html, srv/stub.html, srv/v18.html),
  harness.js (MOD=<id>|_framework|all; VP=desk|phone), _framework.test.js, stub.js (demo module, not shipped).
Tests: MOD=_framework 188/188 at 1400 + 390 (menu, one-line/scrolling tab row, header = v18 at 390, Home/Clips layout = v18
below the header, search/facets/counts vs independent, combined, chips, default chip ~, custom dates, sort, show more,
CSV/TSV/copy, tone average vs independent, URL round-trips, entity page header/list/search/filter/story panel/CSV/back,
entity chart counts per year + tone line vs independent, bar click filters, small-entity note, AXIS clean/different maxima +
no clipping + empty state (entity + Data), Data chart click still opens Clips, entity page never leaves the tab, USMAP
5-vs-6 threshold + per-state counts (crafted + Data), 14 old-link redirects + page-load redirects, Data links).
Known: desktop header at 1400 px goes to two rows with 8 tabs (81 -> 132 px; v18 already wrapped at <= 1280 px); content
below the header unchanged. Screenshots: work/tmp_agent-tabs/shots/framework_*.png.

## Phase B queue (integrator; from coordinator messages)
apply_all step 4l + PIPELINE (tabs_assemble.py, tabs_data.py, us_map? no: inlined; pipeline/tabs/*), ins-release_pickup
appended columns (type, quoted, dek, source), "Uses release text" tag (release_rule helper, build-time, Clips badge/filter/
panel line, release page list, 25%/50% counts, spot checks), LegInfo capitalization everywhere (views, panel, Data, prompt),
remove Home 30-day line (reorg_tracker/patch_reorg + checks), Needs-attention upkeep items -> Manage, no-#clips tests per tab,
light/dark visual pass at 1400/390 with before/after shots, DECISIONS/CONTRACT/pipeline docs, v19docs, pipeline-only rebuild
proof, publish v19 + read-back shas.

## Phase B progress
- 00:1xZ framework hooks done (billLink, chart:false/list:false/after/cards, rowAs, list.extra, desktop sort for row lists, late deep links, hasSaved/openSaved, date-aware publisherOf, outlet-name merges, CSS fixes); SPLITBILLS-v2, LEGINFO-v1, HOMELINE-off, HOMEUPKEEP-v1, ENTITIES-v1, REPRINT90-v1 (7/7 rule checks, sheet-task suite 34/34); COAUTH-v1 in bills.js; travel/outlets use the new hooks; apply_all step 4l wired (2nd run unchanged).
- 00:3xZ tab runs on the integrated page: reporters 146/146, releases 149/149, travel 108/108, bills 140/140 (tests adapted to COAUTH-v1 / SPLITBILLS-v2), adapted REORG checks 68/68.
- 00:4xZ coordinator: preview first (new separate artifact, live stays v18); full test run deferred.
- 00:5xZ apply_all now runs 4l (tabs) + 4m (reltab) + 4n (avtab) cleanly; 2nd/3rd run unchanged; `--check` fixed (copies every pipeline source, incl. work/sid_map.json). AV box (AVTAB-v1) in the story panel. Visual pass light/dark 1400/390: no console errors, no overflow (shots work/tmp_agent-tabs/shots/v19_before, v19_after); fixes: link look = Clips links, phone facts 2 columns, details.dt back to Data alignment.
- 00:5xZ PREVIEW published as a NEW artifact (live 5wHur4aRkSbAu6FscDpTjv untouched at v18): https://claude.ai/artifact/2bMQrhKHRzpK9A9qMbzAk6 version 1793148712-509c; index.html (v19 candidate built by the PIPELINE ONLY from build/pub/pipeline on master 0846cd57…, + "Preview, not live" banner, title "AJG Press Tracker (preview)") + data/release_texts.json (sha 47cd1b03… read back equal); no capabilities; read-back index differs only by one newline the publisher inserts after <body>.
- NOT done yet: ins-release_pickup appended columns + "Uses release text" tag (needs saved story texts at build time: design open), release_texts publish step in the prompt, docs (DECISIONS/CONTRACT/README/v19docs), stale insights test srv, full test run, lib-vs-pipeline byte proof, live v19 publish.
- 01:20 Preview batch built (NAVHIST, ROWLIST, SPREADRULE, CHARTRULE, DATATRIM, cleaner rules + CLIFIX). navtest 64/64. Master now f4391c78 (chrome saves); rebuilding from it.
