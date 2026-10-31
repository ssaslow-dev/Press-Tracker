# agent-tab-reporters — Reporters tab module (TABS-v1)

## Log
- read tabs_contract.md, status/agent-tabs.md, code/tabs_tracker.js, _common_data.py, build/insights/reporters.js (= code/reorg_pitch.js), DECISIONS (Restructure + author/staff rules), TONE_GUIDE, harness/stub/_framework.test.js.
- wrote build/tabs/reporters.js (two-level search tab + reporter page + legacy) and build/tabs/test/reporters.test.js.
- build_testpage.sh + MOD=reporters harness: 144/144 at 1400 + 390. Fixed: tone column no-wrap (td.nw); staff-marker test now searches a staff entry, since the phone shows only 25 rows.
- Coordinator addendum (bill links): Bills in the page header now go through ctx.billLink(b, {date}), falling back to <a data-bill data-date>. Test added; rebuilt and re-run: 146/146.
- Framework requests: (1) `.tbe-facts dd .linkbtn{text-align:left}`, because a long outlet name in a pageLink wraps centred ("Excelsior: Orange County Register weekly"); (2) ctx.billLink (Phase B).
- Done. Files: build/tabs/reporters.js (16 KB), build/tabs/reporters.md, build/tabs/test/reporters.test.js. No data file, no workbook writes, no publish.
