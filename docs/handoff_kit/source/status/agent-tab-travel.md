# agent-tab-travel — Story travel tab module (TABS-v1)

## Log
- Read build/tabs_contract.md (all), status/agent-tabs.md, code/tabs_tracker.js, build/insights/story_travel.js + story_travel_data.py, DECISIONS (Restructure entry and the 2026-10-27 lines), harness/stub/_framework.test.js.
- Data check: 905 stories carry reps (2,815 reprint rows). Reps carry outlet/date/county/state/hl/links but no Medium or Language; the sheet has Medium on 2,774 and Language on 2,658 of those rows -> travel_data.py (per reprint Article ID).
- Wrote build/tabs/travel_data.py (tab-travel block: Medium + Language per reprint Article ID, 2,774 rows, 39,629 bytes), build/tabs/travel.js (~28 KB, node --check OK), build/tabs/test/travel.test.js, build/tabs/travel.md.
- Coordinator addendum (bill links): bill numbers on the story page go through ctx.billLink(bill, {date}) when present, else `<a data-bill data-date>`; tested.
- Harness note: with the module injected after load (not assembled into srv/index.html), any reload with a #story-travel hash falls back to Home (framework drops TB.pend at DOMContentLoaded), so URL round-trip tests can't pass that way. Also the shared srv/index.html (rebuilt 23:50) carries an OLDER travel.js. Tests therefore run on a private page: work/tmp_agent-tab-travel/mksrv.py then SRV=<that>/srv MOD=travel NO_DATA=1.
- Result: 108/108 (54 at 1400, 54 at 390). Screenshots light/dark x 1400/390 in work/tmp_agent-tab-travel/shots/.
- Framework asks: (1) page spec option to skip Data's chart and the stories list (chart:false/list:false) and an after(el, ctx) hook - the module now inserts its cards after the head card from a queueMicrotask and sets hidden on .tbe-chart and the page's .grid-clips; (2) search tab with custom rows has no sort control on desktop (.tt-sort hidden > 760 px), so this tab uses columns with a Clips-form first cell; (3) until ctx.billLink lands, the tracker's global [data-bill] click handler sends a bill click to Clips.
