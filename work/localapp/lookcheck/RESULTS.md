# Look and function check, v65 (SAMELOOK-v2, narrowed run 2026-11-03)

Reference: the live tracker v65 (1793674276-619d, 3,707 stories) as published, in `live_v65/` (v64 files plus the 18 that changed: index.html, data/sheet.json, articles/manifest.json, eight year shards, pipeline/{tracker.js, sheet_task.py, build_data.py, outlets.json, outlet_rules.json, recall_sources.json, release_related.json}). PC build: `assemble_app.py --target linux --role keeper` from workbook `0bccc1fc` (the v65 workbook scratch copy), page built by `build_tracker.py`, patches 01 to 14 applied exactly once, `js_merged.js` rebuilt from `code/tracker/` (its sha256 `c946f521...` equals the live v65 `pipeline/tracker.js`). Same method as README.md: same Chromium, viewports 1440x900 and 960x1040, fresh storage, fixed clock; exception applied = reference with the recorded `display:none` rule against the PC page, 0 pixels, 0 style differences, 0 font-file differences expected.

## Which routes were run, and why only those (Sammy's instruction, 2026-11-03)

Only what the 2026-11-02 and 2026-11-03 code touches was rerun: `code/tracker/00_head.js, 02_state.js, 03_overview.js, 07_charts.js, 25_avtime.js, 53_tabs.js`, `build/tabs/releases.js, bills.js, releases_data.py`, and `40_update_outlets.js, 41_update_search.js` (the Update button, hidden on the PC; no visible effect), plus the LANGADD data (25 new stories).

| route | what it covers |
|---|---|
| home | story count 3,707 (was 3,685), Home |
| clips, clips_f1 | Clips default and one filtered view |
| clips_badge_station_web | the Clips row of a broadcast story with the station's web story saved: "Saved copy (station's web story)" (02_state) |
| story_yt_clip | story sheet of a station-clip story (s04941, FOX40): "YouTube (station clip)" link (03_overview) |
| story_lang_ko_clip | story sheet of the KBS News YouTube clip (s04962), Korean text and "YouTube (station clip)" |
| story_lang_he, story_lang_zh | a Hebrew (s04942) and a Chinese (s04956) story sheet from LANGADD |
| story_av_time | a broadcast row's "Aired ..." time display (25_avtime, s02864) |
| releases | Press releases list: answer line (80% picked up), quarterly picked-up chart, Picked up column |
| releases_facets | the RELRECS facet groups opened (Outlet and Reporter, related stories; Pickup) |
| releases_quiet, releases_quiet7 | Pickup facet "Nothing after 30 days" and "Nothing after 7 days" |
| release_page_pick | a release page with the Picked up section |
| release_page_later | pr00208: Related stories, Later coverage, Possibly related (RELXLOOK-v1) |
| bills, bill_page | Bills list and one bill page (no false "No pickups") |
| data_off, data_on | Data tab charts (07_charts), list-only mentions off and on |

Function parity (same clicks and typing on both, outcomes compared): `tab_tables` (every table tab, including Press releases and Bills), `story_sheet`, `clips_facets`, `hash_routes`.

**Not rerun, and why:** reporters, outlets, story travel, the scrolled and hover states, the sort, search and density states, the saved-copy (old photos) routes, Manage, and the parity interactions clips_search, clips_dates, clips_sort, saved_views, saved_copy, team_notes, history, downloads. Their code is unchanged since the last full clean run (below). A route that failed to capture on the first pass (release_page_later, releases_facets, releases_quiet, releases_quiet7: the draft scenarios did not open the Filters panel and matched upper-case text) was fixed in `lookcheck.js` and rerun on both targets; the tables below take each route from the run that completed it.

**Last full clean run** (all 31 routes and states at both sizes, 12 parity interactions): the earlier reference (tracker v63/v64 files, workbook `bc21c9fb`), recorded in the tables of the previous version of this file (git history of `work/localapp/lookcheck/RESULTS.md`) and in README.md.


### 1440x900

| route / state | page size | differing pixels (exception applied) | % | style differences | font-file differences | differing pixels (raw, exception rectangles masked) |
|---|---|---|---|---|---|---|
| bill_page | 1440x8472 | 0 of 12,199,680 | 0.0000 | 0 of 3,204 | 0 of 1,848 | 0 (masthead spacer and button group resize, see README) |
| bills | 1440x4913 | 0 of 7,074,720 | 0.0000 | 0 of 1,129 | 0 of 960 | 0 (masthead spacer and button group resize, see README) |
| clips | 1440x4035 | 0 of 5,810,400 | 0.0000 | 0 of 2,219 | 0 of 1,360 | 0 (masthead spacer and button group resize, see README) |
| clips_badge_station_web | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,026 | 0 of 681 | 0 (masthead spacer and button group resize, see README) |
| clips_f1 | 1440x4219 | 0 of 6,075,360 | 0.0000 | 0 of 2,194 | 0 of 1,322 | 0 (masthead spacer and button group resize, see README) |
| data_off | 1440x5791 | 0 of 8,339,040 | 0.0000 | 0 of 4,353 | 0 of 2,478 | 0 (masthead spacer and button group resize, see README) |
| data_on | 1440x5819 | 0 of 8,379,360 | 0.0000 | 0 of 4,386 | 0 of 3,645 | 0 (masthead spacer and button group resize, see README) |
| home | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 120 | 0 of 259 | 10 (masthead spacer and button group resize, see README) |
| release_page_later | 1440x3059 | 0 of 4,404,960 | 0.0000 | 0 of 1,226 | 0 of 890 | 0 (masthead spacer and button group resize, see README) |
| release_page_pick | 1440x1091 | 0 of 1,571,040 | 0.0000 | 0 of 389 | 0 of 416 | 0 (masthead spacer and button group resize, see README) |
| releases | 1440x7479 | 0 of 10,769,760 | 0.0000 | 0 of 2,206 | 0 of 1,571 | 0 (masthead spacer and button group resize, see README) |
| releases_facets | 1440x7479 | 0 of 10,769,760 | 0.0000 | 0 of 2,208 | 0 of 1,572 | 0 (masthead spacer and button group resize, see README) |
| releases_quiet | 1440x4031 | 0 of 5,804,640 | 0.0000 | 0 of 1,455 | 0 of 980 | 0 (masthead spacer and button group resize, see README) |
| releases_quiet7 | 1440x4031 | 0 of 5,804,640 | 0.0000 | 0 of 1,455 | 0 of 980 | 0 (masthead spacer and button group resize, see README) |
| story_av_time | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,148 | 0 of 743 | 0 (masthead spacer and button group resize, see README) |
| story_lang_he | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,141 | 0 of 748 | 0 (masthead spacer and button group resize, see README) |
| story_lang_ko_clip | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,124 | 0 of 724 | 0 (masthead spacer and button group resize, see README) |
| story_lang_zh | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,140 | 0 of 748 | 0 (masthead spacer and button group resize, see README) |
| story_yt_clip | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,113 | 0 of 714 | 0 (masthead spacer and button group resize, see README) |


All 19 routes: 0 differing pixels, 0 style differences, 0 font-file differences with the exception applied. The raw column shows only the recorded masthead reflow (10 px at the Manage button corners on `home` at 1440x900, 1 px on `clips_badge_station_web` at 960x1040).


Function parity at 1440x900:

| interaction | steps compared | differences |
|---|---|---|
| tab_tables | 69 | 0 |
| story_sheet | 8 | 0 |
| clips_facets | 22 | 0 |
| hash_routes | 11 | 0 |


### 960x1040

| route / state | page size | differing pixels (exception applied) | % | style differences | font-file differences | differing pixels (raw, exception rectangles masked) |
|---|---|---|---|---|---|---|
| bill_page | 960x10407 | 0 of 9,990,720 | 0.0000 | 0 of 3,202 | 0 of 1,848 | 0 (masthead spacer and button group resize, see README) |
| bills | 960x5706 | 0 of 5,477,760 | 0.0000 | 0 of 1,127 | 0 of 960 | 0 (masthead spacer and button group resize, see README) |
| clips | 960x6191 | 0 of 5,943,360 | 0.0000 | 0 of 2,217 | 0 of 1,360 | 0 (masthead spacer and button group resize, see README) |
| clips_badge_station_web | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,024 | 0 of 681 | 1 (masthead spacer and button group resize, see README) |
| clips_f1 | 960x5987 | 0 of 5,747,520 | 0.0000 | 0 of 2,192 | 0 of 1,322 | 0 (masthead spacer and button group resize, see README) |
| data_off | 960x6800 | 0 of 6,528,000 | 0.0000 | 0 of 4,351 | 0 of 2,478 | 0 (masthead spacer and button group resize, see README) |
| data_on | 960x6828 | 0 of 6,554,880 | 0.0000 | 0 of 4,384 | 0 of 3,645 | 0 (masthead spacer and button group resize, see README) |
| home | 960x1055 | 0 of 1,012,800 | 0.0000 | 0 of 118 | 0 of 219 | 0 (masthead spacer and button group resize, see README) |
| release_page_later | 960x3970 | 0 of 3,811,200 | 0.0000 | 0 of 1,221 | 0 of 890 | 0 (masthead spacer and button group resize, see README) |
| release_page_pick | 960x1306 | 0 of 1,253,760 | 0.0000 | 0 of 384 | 0 of 416 | 0 (masthead spacer and button group resize, see README) |
| releases | 960x9084 | 0 of 8,720,640 | 0.0000 | 0 of 2,204 | 0 of 1,571 | 0 (masthead spacer and button group resize, see README) |
| releases_facets | 960x9084 | 0 of 8,720,640 | 0.0000 | 0 of 2,206 | 0 of 1,572 | 0 (masthead spacer and button group resize, see README) |
| releases_quiet | 960x4828 | 0 of 4,634,880 | 0.0000 | 0 of 1,453 | 0 of 980 | 0 (masthead spacer and button group resize, see README) |
| releases_quiet7 | 960x4828 | 0 of 4,634,880 | 0.0000 | 0 of 1,453 | 0 of 980 | 0 (masthead spacer and button group resize, see README) |
| story_av_time | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,143 | 0 of 743 | 0 (masthead spacer and button group resize, see README) |
| story_lang_he | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,136 | 0 of 748 | 0 (masthead spacer and button group resize, see README) |
| story_lang_ko_clip | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,119 | 0 of 724 | 0 (masthead spacer and button group resize, see README) |
| story_lang_zh | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,135 | 0 of 748 | 0 (masthead spacer and button group resize, see README) |
| story_yt_clip | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,108 | 0 of 714 | 0 (masthead spacer and button group resize, see README) |


All 19 routes: 0 differing pixels, 0 style differences, 0 font-file differences with the exception applied. The raw column shows only the recorded masthead reflow (10 px at the Manage button corners on `home` at 1440x900, 1 px on `clips_badge_station_web` at 960x1040).


Function parity at 960x1040:

| interaction | steps compared | differences |
|---|---|---|
| tab_tables | 69 | 0 |
| story_sheet | 8 | 0 |
| clips_facets | 22 | 0 |
| hash_routes | 11 | 0 |
