# GEOMAP-v1 handoff (agent-v20-maps, 2026-10-28) — edits in files I don't own

Done in my files (code/tracker/14_county_map.js, 52_us_map.js; apply_all run): one map component `geoMap(host, spec)` for CA counties
and US states (shared paint/scale/legend, hover preview, click-to-pin, keyboard, Esc, Top list + Show all, Format picker, empty state),
state rules (`gmOutletPlace`, `stateItems`, `statesOf`, `stateRank`, `geoUsModel`, `geoUsOutlets`), legacy svg entry `gmDrawCounty`.
Data now renders BOTH maps through it (CA card + a new "Coverage outside California by state" card). Until the edits below land,
old 53 still draws the outlet-list / travel maps its own way and Data's state map falls back to an Outlet filter on click.

## Apply (one command, idempotent, anchor-checked; run when v20-tabsui is done with 53_tabs.js / 01_authors.js)
    python3 -I work/tmp_agent-v20-maps/handoff_apply.py .     # from lib/, then apply_all
Edits it makes:
- code/tracker/02_state.js (no v20 owner): FACETS gets `{key:'state', label:'State', …}` after County; `S.sel.state`.
- code/tracker/01_authors.js (v20-tabsui): `vals(r,'state') = statesOf(r)`, `valuesOf('state') = stateRank()`.
- code/tracker/53_tabs.js (v20-tabsui): removes MAPFIX tbMapLift, the insDrawCountyMap wrapper, the #caMap click/mouseup handlers,
  USMAP-v1 TB_US_NAT/tbOutModel/tbUsMap/tbDataUs and the renderCountyMap wrap (all folded into geoMap); ctx gets
  `usMap → geoUsOutlets(+page scope)`, `outModel → geoUsModel`, `drawCountyMap → gmDrawCounty`, new `geoMap(+page scope)`;
  LINKSCOPE comment no longer says a state is unfilterable. (Map CSS lines .tb-usmap/#caMap in the tabs-css block are now dead; optional cleanup.)
- build/tabs/travel.js: "Where it ran" = `ctx.geoMap(.tv-cmap, {geo:'ca', rows:[r]})` + `ctx.usMap(.tv-us, outlets, {rows:[r]})`
  (identical widgets; w.map rule and USMAP-v1 >5 threshold kept).
- build/tabs/outlets.js: list state map counts the listed outlets' clips (`rows`).
Verified on a scratch tree = current lib + this script: work/tmp_agent-v20-maps/src/test.js 81/81 PASS (1400 light+dark, 390).

## Tests to update (behaviour changed by design; owner of build/tests/tabs)
- _framework.test.js USMAP block: "click a state lists its sources" (.tb-us-sel) → now pins a preview (`.cmap-tip.pinned`, expand =
  [data-tbclip] with `state`). "Data: state map under the county map" (#tbUsData, sources) → Data's map is `#gmUs`, counts CLIPS
  (stateItems over Data's rows); count check = `#gmUs svg path.on` aria-label numbers vs stateItems. Threshold tests (5/6) still hold.
- travel.test.js: `.tv-cmap path.on` and `.tv-us[data-show]` kept; unchanged.

## Docs (v20-docs)
- CONTRACT LINKSCOPE line "Values Clips cannot filter (a state) stay text" → states are filterable (Clips State facet, GEOMAP-v1).
- DECISIONS line (suggested): "GEOMAP-v1 (Sammy fd56a06d): one map component for CA counties and US states everywhere (Data, Outlets
  list, Story travel): same hover preview, click-to-pin + expand to Clips (Data keeps its period and filters; entity pages carry
  LINKSCOPE scope), legend/scale, keyboard/Esc, Top list + Show all, empty state. Data's state map counts out-of-state clips (as the
  county map counts local clips). Clips gains a State filter (out-of-state regional/local outlets; CA, national, wires have none)."
