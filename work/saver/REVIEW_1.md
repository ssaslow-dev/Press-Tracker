# REVIEW_1: saver_diff.py / saver.py preview path (independent review, 2026-10-31)

Scope: SAVE_RULES.md (incl. Sammy's answers), SAVER_SPEC.md sections 3 to 6, `src/saver_diff.py`, `src/saver.py`, `src/saver_steps.py`,
`tests/`, and the parts of `L/code/sheet_task.py` the diff leans on (VT_DERIVED_REL, VT_NEW_OK, result key shapes, `delete_rows_keep_links`,
`verify`). Nothing under `src/`, `L/code` or `L/build` was changed. New tests live in `tests/review/`.

## Verdict: fix first

The core of the diff is sound: a filled cell overwritten or cleared, a key row lost, a tab or header lost, a hyperlink dropped from a
matched row, a Coverage row with an ID sheet_task did not assign, duplicate IDs, blank IDs, int/str retyping, merges over filled cells,
and an Originals tab that stops mirroring Coverage are all refused (existing tests plus the 13 passing tests in `tests/review/`). The
replay of the real 2026-10-30 save reproduces the STAGED workbook cell for cell (750 diff lines, 18 allowed changes, 0 differences).

Five gaps should be closed before the write path is built on this diff: hyperlink *targets* are not compared (a known failure mode of
this very pipeline), new rows on tabs other than Coverage carry no identity check, a "move to Removed" is accepted when nothing landed on
Removed, hyperlinks of moved rows and of the header row are never checked, and the process lock can be released by a process that no
longer owns it. None of these breaks preview (preview writes nothing); all of them matter the moment `save` commits.

Test runs:
- `python3 -I -m unittest discover -s tests -t tests`: 64 tests, OK (1 skipped). pytest is not installed here; unittest is the runner.
- `SAVER_SLOW=1 ... -k tamper`: OK (113 s). The injected cell is refused as OVERWRITE.
- `tests/replay.py` (runsave fixture): workbook [1] 0 differences, [2] 750/750 lines and 18/18 allowed changes, [4] pages 0 differences,
  [6] 0 input files modified. Harness exit 1 on six result-JSON differences, none of them workbook cells: `pages/0/photos/fetched` 18 vs 0
  (the real run downloaded 18 photos; offline replay served them from `img_cache`, 0 fetch attempts), `related_cols/links` 1254 vs 1258
  and `related_cells` 0/9 swapped between pass 1 and pass 2, and two `release_related.json` entries tagged `bill` vs `text`
  (pr00230, pr00236). The builder should explain the last two; they are relmatch state, not diff behaviour.
- `tests/review/`: 25 tests, 12 fail by design (each failure is a finding below), 13 pass (negative checks that confirm coverage).

## Findings, ranked

### 1. Hyperlink targets are not compared (medium-high)
`saver_diff.py:96-129` (`_hyperlinks` records only which cells hold a `<hyperlink>`), `:417-420` (compares presence per row).
A cell that keeps its text and keeps *a* link but now points at another URL passes clean. This is not hypothetical: `sheet_task.py:509-512`
documents the v22 incident where every link below a removed row landed one row too high (65 bogus A&V links). A presence-per-row check
catches only the last row of such a shift; every interior row still "has a link". Removal moves run on every save that executes an edit.
Fix: record `(sheet, row, col) -> target` (the `r:id` relationship Target, or `location` for internal links) and compare targets for
matched rows. Test: `test_review_diff.Hyperlinks.test_hyperlink_target_rewritten_is_reported`.

### 2. New rows on tabs other than Coverage carry no identity check (medium)
`saver_diff.py:435-450` (`ok = name in new_ok or is_cov`), `:511-516` (FOREIGN_ROW computed for Coverage only).
SAVE_RULES line 24 is not limited to Coverage: "A new row's Article ID is not one sheet_task.py assigned in this run." An A&V row with an
Article ID that exists nowhere, or a Removed row for an ID that was never removed from anything, is accepted as `new_row`. SPEC section 6
scoped FOREIGN_ROW to Coverage; the rules do not. Fix: on A&V and Removed, a new row's key must be in `assigned_ids`, in Coverage after
(A&V), or in `removed_aids` (Removed). Tests: `AllowListBreadth.test_new_av_row_with_an_id_sheet_task_did_not_assign`,
`AllowListBreadth.test_new_removed_row_for_an_id_nothing_removed`.

### 3. `removed_move` accepted when nothing landed on Removed this run (medium)
`saver_diff.py:375-380` (`removed_on_tab` is every ID on the *after* Removed tab), `:405-408`.
If an ID was already on Removed from an earlier removal and the story was later re-added to Coverage, a new removal makes the Coverage row
vanish while the pre-existing Removed row satisfies the check; the current row's content is gone. The check should require that the Removed
row is *new* (present after, absent before) or that the after Removed tab has one more row for that ID than before.
Test: `AllowListBreadth.test_removed_move_needs_a_row_that_landed_this_run`.

### 4. Hyperlinks of moved rows and of the header row are never checked (medium)
`saver_diff.py:403-415` (a moved/missing row returns before the link check), `:417` (only data rows; row 1 has no entry in `sheet.rows`).
A row that moves to Removed may lose its Publisher link hyperlink entirely; the Removed row is a `new_row` and new rows are not checked for
links. SAVE_RULES line 25: "a hyperlink would go missing" is unconditional. Fix: for a `removed_move`, require the Removed row for that
ID to carry at least the before row's link targets (ties to finding 1); compare header-row links like data rows.
Tests: `Hyperlinks.test_hyperlink_of_a_moved_row_must_land_on_removed`, `Hyperlinks.test_header_row_hyperlink_lost_is_reported`.

### 5. Process lock: a stale-lock takeover lets the old holder release the new holder's lock (medium, write path)
`saver.py:148-167` (`acquire` moves a >30 min lock aside), `:175-182` (`release` moves whatever is at `self.path`), `:169-173` (`at` is
only refreshed by `set_run`, early in the run; a long pass 1 does not refresh it).
Sequence: A acquires; 31 minutes pass during pass 1; B moves A's lock aside and acquires; A finishes and `release()` moves B's lock to
logs; C acquires while B is still running. Harmless for preview, not for `save`: a process must verify it still owns the lock (pid/host in
the file) before backup/commit and before release, and refresh `at` between steps. Test:
`test_review_preview.LockOwnership.test_stale_lock_holder_does_not_release_the_new_holders_lock`.

### 6. Row reordering is invisible (medium-low)
`saver_diff.py:320-334` (rows matched by key only). Two Coverage rows swapped, with Originals swapped to match, produce zero changes and
zero problems. sheet_task appends; a reorder would be a bug or a foreign edit, and the diff would say "nothing changed". Cheap guard: the
sequence of keys of rows present on both sides must be in the same order. Test: `RowIdentity.test_rows_reordered_on_coverage_is_reported`.

### 7. `reprint_count` allows clearing the count (low-medium)
`saver_diff.py:459-463`: `rec is None or blank(new) or str(rec) == text(new)`. SPEC 6 allows the recorded new count; a blanked count for a
story in `reprint_counts` is accepted. Also `rec is None` (value not a dict) accepts any value. Test:
`AllowListBreadth.test_reprint_count_cleared_is_not_the_recorded_count`.

### 8. `TRUE` -> `1` passes as unchanged (low)
`saver_diff.py:51-65`: `_canon` keeps bools, but Python's `True == 1`. Test: `RowIdentity.test_bool_to_number_coercion_is_a_change`.

### 9. Environment-variable hook edits the pass-2 output in the production path (low, hygiene)
`saver.py:575-576`, `:647-654`. `SAVER_TEST_TAMPER` writes a cell before the diff. Aimed at a blank cell it is an allowed fill and would reach
the master in `save`. Move the hook into the tests (patch `D.compare` or post-process in the test). Test:
`test_review_preview.NoHiddenWriteHooks.test_no_environment_hook_edits_the_output_before_the_diff`.

### 10. `la_today` fallback is fixed UTC-8 (low)
`saver.py:72-77`. Without tzdata (Windows without the `tzdata` package) the fallback is a day behind between 07:00 and 08:00 UTC from March
to November, and a correct `--today` is refused as "later than today". Install `tzdata` on Windows or refuse when zoneinfo is unavailable.
Test: `test_review_preview.Dates.test_la_today_fallback_is_pacific_daylight_aware`.

## Checks reviewed and found adequate (no test written)

- Checksum ledger (`saver.py:118-122, 267-281`): last `init|save|confirm` entry, sha compared before anything else is copied, re-checked
  after the copy to `O/in.xlsx` (`:487-489`). `init` accepts any sha and only records `matches_file` (Sammy's answer 2); `confirm` refuses
  a wrong sha or an already-confirmed chain. `UNCONFIRMED_PREVIOUS` cannot be bypassed except by `init`, which is the designed override.
- Excel detection (`saver.py:252-264`): `~$` owner file plus `open(w, 'r+b')`; on Windows a file held by Excel raises PermissionError,
  which is caught. On Linux/macOS only the `~$` test is informative, as the spec documents. A read-only file attribute reports as
  EXCEL_OPEN (misleading but safe).
- Library lock `.sheet_task.lock` (`:449-463`): honoured, never moved by preview.
- Preview writes: only `--out`, `--state/saver.lock`, `--state/logs/`. The replay's step [6] found 0 input files modified. `--library` is
  passed to sheet_task but sheet_task only reads it (`sheet_task.py:2674`, `4668`). relmatch's `--update` hits `O/pipeline/`, the copy.
- Network: `saver_steps.offline_env` points every proxy variable at `127.0.0.1:9` and removes `NO_PROXY`. The one fetcher,
  `img_embed._session` (`img_embed.py:239-243`), builds a `requests.Session` and sets `s.proxies` from `HTTPS_PROXY` explicitly, so the dead
  port is used and the attempt fails at once. No other pipeline module opens a socket (`release_rule.py` shells out to `pdftotext`, not
  network). Adequate as a guard against *this* pipeline; it is not a sandbox: any future module that sets `trust_env=False`, uses raw
  sockets, or reads a different proxy variable would bypass it. PIPELINE.sha256 pinning is what makes the guard hold; if a stronger
  guarantee is wanted, run the pipeline under a network namespace (`unshare -n`) on Linux and document that Windows has no equivalent.
- Tab, header, cell-width handling: trailing blank header cells are trimmed on both sides; cells past the header width are still compared;
  a header change stops cell comparison for that tab but still refuses.

## Lesser notes (no action required to build)

- `saver_diff.py:483` ROWCOUNT "identity" is tautological: with key matching, `after == before + added - moved - missing` always holds.
  The real count protection is the cross-check against `result.verify` / `result.counts` (`:486-499`), which only runs when those keys
  exist. If a future sheet_task stops writing `verify`, the count rules go silent without a refusal.
- `saver_diff.py:357-360` tab order excludes Originals; a moved Originals tab is silent (deliberate, undocumented in SAVE_RULES).
- Bills is keyed by its first four columns (`:317`); a fill into any of them reads as row missing + row added, which refuses. Safe, and
  consistent with VT_NEW_OK excluding Bills, but a legitimate Bills fill would need a key change.
- `wb.sheetnames` includes chartsheets, `wb.worksheets` does not (`:139, 150`); a chartsheet would be refused as `tab_missing`. Safe.
- Merged-cell *un*merging and formatting, data validation, column widths, comments are not compared; the rules do not ask for them.
- Cross-platform: paths are `pathlib`, zip paths are posix, `diff.tsv` and the ledger are written with `newline='\n'` so the token is
  stable across OSes. A Windows git checkout with `autocrlf=true` would rewrite pipeline text files and trip PIPELINE_MISMATCH (adapter
  concern; correct behaviour). `~$` naming assumes a master name of 8+ characters (true for this master).
- `tests/replay.py` writes under `L/work/saver/scratch/` on every run (three folders are already there); it does not clean up.
