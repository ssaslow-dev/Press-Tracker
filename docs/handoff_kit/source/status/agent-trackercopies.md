# agent-trackercopies (T11) — 2026-10-27 (final)
Targets: 453 non-NewsBank Originals with no saved copy in old_manifest (439 Tracker scrape, 14 ProQuest) — work/texts/t11_targets.csv.
Saved copies found: 38 → work/texts/tracker/<sid>.html, index work/texts/tracker_index.csv (source, method, page title/head = reusable metadata).
- 11 same-story page in the published tracker (headline match ≥0.99)
- 26 own code in ~/Desktop/Tracker library via _rename_log.csv (25 headline ≥0.9; jg-02664 0.79 wording variant, kept because it is the row's own code)
- 1 own code in the stale "Tracker library - saved HTML.zip" (jg-02896 ← jg-ac6b2e)
Borderline, NOT used (different outlet/headline from old loose grouping): 6 — work/texts/tracker_borderline.csv.
Remaining with no copy anywhere on the Mac or in the tracker: 415. The Desktop library, the 5 year zips and their index.csv hold no other target codes; the "Gabriel press archive" folder is not in any connected folder.
No overlap with fetch_1/2 jobs; nothing overwritten. Read-only on the Mac (only a temp unzip in the device VM's /tmp and outputs scratch).

!! T1 BUG for coordinator: all 101 "old stories with no Coverage row" added in T1 were DUPLICATES — each of their codes already exists in the snapshot inside a multi-code "Tracker story code" cell ("jg-a; jg-b"); T1 matched whole cells only. The workbook on the Mac now has 101 duplicate Originals (ws-03866…/pq-00343…, jg-04196…jg-04296) + 41 reprint-list rows. List: work/t1_duplicate_additions.json. Note: the Desktop library rename (_rename_log.csv) named 26 files after those duplicate Article IDs (e.g. ws-03985) instead of the existing rows' IDs.
