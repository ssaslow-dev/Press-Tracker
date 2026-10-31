# Final acceptance check (deduplicated, Sammy 2026-10-27) — run ONCE, by an agent that hasn't seen the work

Already proven by earlier stages — do NOT repeat:
- F1: every changed cell accounted for; every File name exists in the planned library; one Original per story; migrate_ids 1:1.
- F2: the Mac library equals the planned state file-by-file (sha256); undo log written first, every op verified.
- F3: the committed workbook's sha256 = the build input (final.xlsx).
- F4: all test suites (display, reach, links, authors, update, sheet task, cleaner, search) on the build; published files = local build (sha/manifest).
So sheet↔library, sheet↔build, undo-log and per-file checks are NOT re-run.

What only a check of the LIVE published tracker can show:
1. The live page loads (no console errors) and shows the expected story count (from F4's manifest).
2. Saved copies load: open the viewer for 50 random stories across every copy type (web HTML, NewsBank text, ProQuest, print PDF, TinyFish-fetched) — loads, non-empty article text, headline matches, no console/network errors. Rows with `BLOCKED – TinyFish` / `RETRY – TinyFish` are skipped (count them only).
3. Live behaviour: Reach filters (multi-tag; new categories), per-author links (a co-written story lists both; staff bylines grouped), topic and bill filters (leginfo list; AB 130 absent), links (State Library + publisher + TV clip), search finds article phrases, Update button dry run (no writes), old jg- links still resolve.
Report pass/fail per item with examples of any failure.

## Press releases (RELEASES-v2 / RELCHECK-v1, added 2026-10-27)
4. Release data: in the live page, block `ins-release_pickup` has v 2, src "sheet:Press releases", n_scope official entries (= tab rows in scope: 236 at v16) + 5 not posted officially; the 15 releases of Sammy's "1 yes" (story IDs s04588 s01337 s01304 s01196 s01198 s01190 s01179 s01157 s00991 s00940 s00842 s00802/s00823 s03228 s03035 s01893) are in the Press releases view with runs and their official link; none of them is a Clips story; no caucus release before 2020-11-18; no duplicate URLs.
5. Release wiring: stories s01093, s01125, s01453 show "From press release: …" with the official link + copy icon in the story panel and the "From press release" badge in Clips; searching Clips for the release title finds them; the CSV download has "Press release" and "Press release link".
6. Update button release check: a dry run (no writes) reports "releases: none new" unless the official sites posted after the tab's newest dates (office 2026-10-24, caucus 2026-10-01).
