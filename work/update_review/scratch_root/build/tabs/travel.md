# Story travel tab (travel.js, agent-tab-travel, TABS-v1)
- **List** (#story-travel): 853 stories that ran in at least one other outlet (canonical names via ctx.outlet; copies in the
  original's own outlet don't count; same-headline/same-day duplicates left out via ins-story_travel "x" dup:, as before).
  Rows in Clips form (clipItem, canonical outlet, "N outlets") + Original date, Outlets, Days to last pickup. Search headline /
  outlet / author. Facets: Original date (`date`), Original outlet (`outlet`), Issue (`iss`), Reprint count (`n`: 1, 2-4, 5-9,
  10+, distinct other outlets = the sheet's "# of reprints" rule), Outlets it reached (`reached`), Language (`lng`: original's
  or any pickup's). Answer sentence names the widest story. Export: Copy pickup summary, Copy list, CSV (+ Story ID, outlet,
  issue, copies, own-outlet copies, outlets in order).
- **Story page** (#story-travel/<Story ID>-<first words>): summary line "Picked up by N outlets in D days; furthest: Outlet
  (Place); in-language: K (languages)" (clauses omitted when empty); facts incl. Bills (ctx.billLink, else `<a data-bill
  data-date>` per the addendum); spread curve (cumulative step line by day since the original, day 0 rule, up to 3 milestone
  labels, AXIS-v1 niceScale/axis, at least 3 days wide, hover per day, "Show the numbers"); pickup ladder (original + one row
  per outlet in run order, outlet -> outlet page, Medium/Reach/Language badges, date, "+N days", place, headline if different,
  each copy's links with copy icon on the left, copies grouped "N copies", first 20 then "Show all", Copy/CSV export);
  Where it ran (CA county map via ctx.drawCountyMap when >= 2 counties and known counties cover >= half of the outlets not
  placed outside CA, else a county line; ctx.usMap for out-of-state). The old +1..+7 dot grid and Top sources table are removed
  (the Original outlet facet counts and the Outlets tab replace Top sources).
- "Furthest": great-circle distance between rough centroids (CA counties, US states) from the original's place (Sacramento
  when unknown); any place outside the US ranks furthest. Ranking only, never shown as a number.
- Data: ctx.D reps; tab-travel block (travel_data.py: Medium + Language of each reprint row, by Article ID; 39.6 KB);
  ins-story_travel (Reach per reprint, inferred); tab-common (names, out-of-state outlets). Fallbacks: the outlet's originals.
- Page hides the framework's Coverage-over-time card and one-row list (single story); see status file for the framework ask.
- Test: build/tabs/test/travel.test.js, 108/108 at 1400 + 390 (run against work/tmp_agent-tab-travel/srv, built by
  work/tmp_agent-tab-travel/mksrv.py = shared srv page with the current travel.js embedded).
- Screenshots: work/tmp_agent-tab-travel/shots/{list,page,page_ca}_{light,dark}_{1400,390}.png
