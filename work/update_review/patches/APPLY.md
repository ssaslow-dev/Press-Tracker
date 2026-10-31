# Applying the Update-button review patches

All patches are unified diffs against `L/code` (and `L/build/tests/run_all.sh` where a suite is added). Nothing here has been applied to L/code, L/build, the master, the Mac or any artifact.

General procedure (one patch at a time, in the order below):
1. `cd L && patch -p1 --dry-run < work/update_review/patches/<file>.patch` (must apply cleanly), then without `--dry-run`.
2. Copy the patch's test file(s) from `work/update_review/patches/tests/` to the path named in the patch header (`build/tests/update_js/` for JS, `build/tests/sheet_task/` for Python) and add the `r <name> ...` line to `build/tests/run_all.sh` as the patch shows.
3. `python3 -I code/apply_all_patches.py` (rebuilds build/js_merged.js and mirrors build/pub/pipeline/; it refuses if js_merged.js was hand-edited).
4. `bash build/build.sh` then `bash build/tests/run_all.sh` (expect `fail=0`; baseline is 42 suites green, see ../tests_out/baseline_run_all.log).
5. Publish per HANDOFF 4.4: the page (index.html) for JS patches; `pipeline/sheet_task.py` and `pipeline/tracker.js` for the sheet task. Keep capabilities. Refresh the viewer copy (4.4 step 3a).
6. Append a DECISIONS line naming the patch id and the suites that cover it; keep `code/sheet_task_prompt.md`'s file list complete (no patch here adds a pipeline file).

Order and verification per patch (filled in as each lands in this folder; see ../results/REQ-<n>.md for the executor's run log):

| Patch | Bug | Files | Test | Verify |
|---|---|---|---|---|
| REQ-1_late_window.patch | B5 | code/tracker/41_update_search.js (one line) | build/tests/update_js/test_late_window_js.js | `node build/tests/update_js/test_late_window_js.js` -> ALL CHECKS PASSED |
| REQ-2_run_persist.patch | B1, B2 | code/tracker/41, 42, 43 | build/tests/update_js/test_run_persist_js.js (playwright; needs the built page) | scenarios A-C pass; run_all fail=0 |
| REQ-6_fetch_retry.patch | B4 | code/tracker/41_update_search.js | test_run_persist_js.js scenario set or its own playwright test | the find survives one failed fetch; two failures list it as skipped with the TinyFish reason |
| REQ-3_verify_tabs.patch | B6 | code/sheet_task.py | build/tests/sheet_task/test_verify_tabs.py | fixture run verify.ok; synthetic AV/Bills overwrite and dropped hyperlink fail verify |
| REQ-7_has_work_pages.patch | B8 | code/sheet_task.py | build/tests/sheet_task/test_has_work_pages.py | orphan page -> no work; referenced page -> work |
| (to build) REQ-9..15 | M1-M6 + run_done | see requests.md | per request | per request |

Known overlap: REQ-3 and REQ-7 both add one line to build/tests/run_all.sh after `r sheet_task`; the second one's run_all.sh hunk is rejected, add that line by hand (results/REQ-7.md caveat 3).

Apply order: REQ-1, REQ-2, REQ-6 (same file, hunks separated; REQ-6 applies on top of REQ-2 with offset), REQ-3, REQ-7, then the prevention set when built. Before the first live sheet-task run: Sammy replaces the scheduled task's prompt (REQ-15, owner only) — do not rely on its disabled state, fire_trigger ignores it.

Not patches, but run before the first supervised live run: `work/update_review/rehearse.sh` (REQ-8) and the openpyxl round-trip check (REQ-4).
