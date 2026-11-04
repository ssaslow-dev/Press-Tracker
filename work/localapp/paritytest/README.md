# PARITYTEST-v1: the live tracker against the PC tracker, feature by feature

Sammy: "ensure that there's a final test that compares artifact functionality to the new software." This runs the live tracker's own published files and the PC tracker side by side, on the same workbook, with the same clicks, and compares what comes out. It builds on the look check (`../lookcheck/`, which compares looks); this compares behaviour.

## Command

    export AJG_SCRATCH=<a scratch folder>          # holds the inputs below; any folder outside the repository
    python3 -I work/localapp/paritytest/run_paritytest.py [--vp 1440x900] [--only edits,every_tab] [--build "…/AJG Tracker"] [--live-site DIR]

Takes about 40 minutes. Exit code 0 and the last line `PARITYTEST: PASS` mean no un-allowed difference. Results: `$AJG_SCRATCH/paritytest_out/parity/<vp>_<test>.{ref,pc}.json` (every outcome, both sides) and `<vp>_summary.json` (differences and the allowed ones, with reasons).

Inputs (both from the SAME workbook, sha256 `0bccc1fc`):
- `--live-site` (default `$AJG_SCRATCH/live_v65`): the live tracker's published files (`index.html`, `articles/`, `copies/`, `img/`, `data/`), fetched read-only. The live artifact and its database are never touched. Served by a plain static server on 127.0.0.1.
- `--build` (default `$AJG_SCRATCH/app_build_pt/linux/AJG Tracker`): a fresh Linux test build from `assemble_app.py --target linux --role keeper --workbook <that workbook> --live-site <same live files> --legacy <live pipeline/legacy_index.html>`. Every interaction gets a fresh hard-linked copy of the build's data (so one test's edits never leak into the next); the build itself is never written.
- Same Chromium, viewport, clock (Monday 2026-11-02 19:30 Los Angeles), locale and empty browser storage for both.

## The storage swap

The live page keeps notes, saved views, edits and runs in the artifact database (`window.claude.use('db')`). Here the reference page gets an in-memory stand-in with the same calls (it survives a page reload through sessionStorage, as the live database survives one); the PC page uses its own local runtime (`server/claude_shim.js`, files on disk). The `edits` and `notes_views_storage` tests read the collections back through the page's own `window.claude` on both sides and compare the stored documents (times normalised) as well as what the page shows, before and after a reload.

## What is driven

`../lookcheck/parity.js` (search terms, every date window, every facet, sorting and page sizes, saved views, the story sheet and its Next/Previous/full-page, saved copies (old with embedded photos, 2025 with data: photos), notes, Back/Forward, URL routes, CSV/spreadsheet/copy/ticked-story exports and every tab's CSV, every tab table with its sorts and drill-downs, Data tab controls), plus `extra.js`:

| test | covers |
|---|---|
| `edits` | Edit details, save, remove a story, the Update log's pending-edit message, the stored `edits` documents, reload |
| `notes_views_storage` | a note and a saved view written and read back from storage, after a reload |
| `manage_panel` | every Manage section (Find and refresh, Update log, Saved copies, Data checks, Definitions) |
| `every_tab` | opens every tab; text, chart count, row and link counts; Home tiles; total row count |
| `links_photos` | outbound links in the first 25 rows; for ten stories (new, 2025, 2015, TV, non-English) the story sheet links and the saved copy's photo sources and anchors |
| `reprint_groups` | the stories that carry reprints and "also ran" outlets: their sheets and counts |
| `exports_more` | CSV and spreadsheet exports under a date filter |

## What the reference page gets (and the guard)

The reference page is the live page plus exactly what the PC build also does to the page, because those are the recorded exceptions: the layout and wording patches 15, 16, 17, 27 and the wording lists 18 and 21 (`assemble_app.patch_index_tidy`: TIDY-v1, NOTE-v1, VIEWORIG-v1) and the rule that hides the Update, Refresh, tone, author and translation buttons (the same rule the PC's page server adds). A **guard** diffs the reference page before and after those patches and fails the run unless the changed lines are exactly the reviewed set (`ref_patch_diff.json`: line count and sha256). A new or edited patch therefore cannot slip into both sides unnoticed: review the lines (`ref_patch_diff.NEW.txt` is written), check them against the decisions, then update the file.

## Allowed differences

None are suppressed. `allowed.json` is empty. The PC's three own additions are **asserted on the PC** and then taken out of the text before the two sides are compared (never regex-stripped on both sides):
- the Tracker files button (`#ajgf-btn`, exactly the text "Tracker files", visible; absent on the reference);
- "Last updated" (`#ajg-lastupd`, must equal the date of the ledger save the test copy carries, and be absent on a copy with no save);
- "View original" (`[data-lk="po"]` on the story that has a print original: its link must point into `/library/_original_pdf/2026/`; absent on the reference).
Everything else, including the wording and layout changes of the patches above, is the same on both sides by construction and any other difference fails.

## Passes (1440x900 only)

| pass | copy | interactions |
|---|---|---|
| light | keeper | all 21 (the 19 listed above plus `view_original` and `linked_photo`) |
| dark (`prefers-color-scheme: dark`) | keeper | every tab, story sheet, tab tables, Manage, saved copy |
| light | reader (MULTIPC-v2) | every tab, Manage, search, story sheet |

Every interaction starts from a fresh hard-linked copy of the PC build with one save in its ledger and one print original in its library (the page is rebuilt so row 00056 carries it). `linked_photo` swaps one embedded photo of a saved copy for a web address on both sides and compares the opened copy (sources, count, sandbox; whether the picture loads depends on the network and is not compared). The clipboard is emptied before each Copy and a missing Copy button fails the test.

Not covered here, by design: the Tracker files panel actions (Bring in update, Save my edits, Make refresh file, Accept the workbook) have no live counterpart; they rest on CHAINCHECK-v1 and the app tests. Widths other than 1440 are covered by the look check (`../lookcheck/`, 1440 and 960).

## Rerun rules

PARITYTEST-v1: runs in consolidation step 5 and again after CLEANUP-v1; it must pass before the final zip is sent.
