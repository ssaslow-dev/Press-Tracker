# agent-v20-maps — GEOMAP-v1: US state map = the CA county map's component (Sammy comment fd56a06d)
## Log
- 04:3xZ read V20_BRIEF, README, DECISIONS, CONTRACT, inbox item, backendclean2 status. Pre-change copies + SHAs: work/tmp_agent-v20-maps/pre/.
- Found 3 map implementations: Data #caMap (14), insDrawCountyMap+tbMapLift (50/53), tbUsMap (53; counted sources, click listed outlets).
- Wrote geoMap (14) + state rules (52); Data renders CA + US through it. Edits outside my files → handoff_apply.py + handoff.md.
- Behaviour notes: Data go-to-Clips now keeps Data's period AND active filters (so Clips = the stories the map counted; old county
  click cleared filters). A redraw (phones fire resize on scroll → Data re-render) keeps the pinned preview. Frozen shape = accent
  outline, fill unchanged (the MAPFIX brightness washed light shades to white).
- 04:58Z apply_all on lib: js_merged rebuilt (32 parts), node --check ok, pipeline refreshed.
## Self-check
- Scratch build (blocks from work/coverage_current.xlsx; tracker = current lib + handoff_apply): src/test.js 81 PASS / 0 FAIL at
  1400 light, 1400 dark (shots), 390: per map (CA, US) shapes/legend/Top 10 + Show all/Format; hover preview "Name · N clips" +
  lift; click pins (dialog, aria-pressed, frozen); second click / Esc / click-away unpin; focus previews, Enter pins + focuses
  expand; Show all = every shape; expand → Clips with county/state filter and story count = preview's distinct stories; Top row →
  Clips; Format narrows. Clips State facet has values; Story travel CA+US both geoMap, state expand → Clips filtered by state;
  Outlets list map is geoMap; no horizontal overflow; no page errors.
- Lib-only (my files, old 53): Data renders, no errors, old #tbUsData hidden, state click falls back to Outlet filter.
- Shots: work/tmp_agent-v20-maps/shots/ (sidebyside_data_{1400,1400_dark,390}.png, sidebyside_pinned_{1400,390}.png, hover_*, pinned_*,
  travel_*, outlets_list_us_*, clips_state_*).
## Handoff
- work/tmp_agent-v20-maps/handoff.md (apply script, test updates, docs line).
