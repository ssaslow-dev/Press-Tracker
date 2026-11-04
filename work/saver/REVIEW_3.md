# REVIEW_3: line-by-line safety review before the first live save and the switch-over (checkpoint 3, round 3)

Reviewer: Fable, 2026-11-04, repository at commit e4c7e32 (everything since REVIEW_2's f4478af). Read: code, rules and test results only
(CLAUDE.md hard rules, work/saver/SAVE_RULES.md, work/localapp/updatefolder/FORMAT.md, and the DECISIONS entries SWITCHOVER-v1 and its plan,
DROPUNVERIFIED-v1, PRJUDGE-v2, PRCOLOR-v1, OTHERFILES-v1 / ORIGCOPIES-v1, PRINTORIG-v1 option B, VIEWORIG-v1, RENAME-v1, DATAFIX-v1 with its
follow-up and the "built into the screen" entry, LIBFILES-v1 / STATIONNAMES, NAMING-v2, LASTUPDATED-v1, PCEDITS-v1, MULTIPC-v2, PRINTTAB-v1).
Builder notes, READMEs and commit messages were not used for conclusions. Commits that landed on the branch while this review ran (e929aee to
c810e0a, MACAPP-v1: `work/localapp/macpack/` plan and test-list documents only) touch no code that writes the workbook or the library and are
not part of this review.

Read in full: `work/localapp/app/src/station/{switchover,rename_files,datafix_structural,drop_unverified,other_files_column,setup_mac,common,
station_cli,station_server,refresh,post_save,plain}.py`, `web/panel.js` (the switch-over part), `data/datafix_structural.json`, `data/prjudge_v2.json`
(shape and counts), the five approved CSVs (every line checked by script: no overwrite line with a blank "Current", no duplicate cell, 1,106 lines,
Coverage only), `work/localapp/datafix/make_approved.py`; `work/saver/src/{saver,saver_diff,saver_steps}.py` diffs; `work/localapp/updatefolder/
{formats,take_update,make_for_update}.py` diffs; PC patches 19 to 28 and newsbank_pc 07 to 09 (22 = 07, 24 = 09, byte for byte), applied in the
assembler's order to today's `code/sheet_task.py` (all nine sheet_task patches match exactly once); the sheet_task code they lean on
(`swap_original`, `rebuild_originals`, `delete_rows_keep_links`, `execute_removals`, `fill`, `put`, `next_aid`, `verify`, `load_db`, `has_work`).

Suites run by me (2026-11-04):

| suite | result |
|---|---|
| `work/saver`: `tests` (`python3 -I -m unittest discover -s tests -t tests`) | see the line at the end of this file |
| `work/saver`: `tests/review`, `tests/review2` (unittest) | see the line at the end of this file |
| `work/localapp/updatefolder`: `tests` (pytest) | 95 passed, 24 subtests passed, 79 s |
| **new** `work/saver/tests/review3/test_review3_extracopies.py` (the PC build's patched sheet_task through `saver.py preview`) | 2 tests: **2 FAIL** (finding 1) |
| **new** `work/localapp/app/tests/review3/test_review3_switchover.py` (the station modules on a stand-in app folder) | 4 tests: **4 FAIL** (findings 2, 3, 4, 6) |
| app suite (`work/localapp/app/tests`) | not run here: it needs the assembled Linux build, which needs `legacy_index.html` from the live tracker (not in the repository, no network from this session) |

Note on the runner: `python3 -I -m pytest tests -q` in `work/saver` (the command CLAUDE.md gives) collects `tests/review2` too, and that folder
imports `test_saver_save` as a harness; under pytest its module set-up runs twice and 48 tests error with "File exists: .../pipeline". The code is
fine; the unittest command above is the one that works. Worth one line in CLAUDE.md or an `--ignore`.

## Verdict: fix finding 1 and finding 2 first; then the switch-over and a supervised first save are safe

Nothing I found can lose or overwrite a row, a cell, a hyperlink or a library file: every step still goes backup (or the screen's one backup),
uniquely named staged copy, its own independent cell-by-cell check, atomic swap, checksum after the swap, ledger, `init`; files are moved or
added, never replaced; the drop step deletes exactly what DROPUNVERIFIED-v1 allows and only after the ledger entry. The one-time screen re-plans
every step on the workbook as it is at that moment and refuses when the plan or any planned cell differs from what the person looked at.

Two things should be fixed before the day, both small:

- Finding 1 is not in the switch-over screen but in the save that follows it: the PC build handles a NewsBank "extra original copy" twice, so
  the first real NewsBank update after switch-over puts every such PDF into the library twice (`nb<id>o-s<story>.pdf` and `...-v2.pdf`) and,
  as soon as a row already has an "Other files" entry, the whole update is refused. Not a loss, but the first update of the new setup would
  either duplicate files or not save.
- Finding 2 can leave the workbook and the library disagreeing on ~1,000 file names after the rename step if anything goes wrong after the
  swap (the logs folder unwritable, a full disk at that second, an unexpected error). Silent, and the same code runs after every later save
  that changed a story's role.

Findings 3 to 7 are low; none blocks a supervised run.

## Findings, ranked

### 1. Medium (operational: duplicates files and blocks saves): a run's `extra_copies` is handled by patch 24 AND patch 25

`work/localapp/app/patches/24_sheet_task_printpages.patch` (`apply_print_pages`: `for x in copies: self._extra_copy(x, pages_dir)`, and
`_extra_copy` itself) and `work/localapp/app/patches/25_sheet_task_otherfiles.patch` (`apply_extra_copies`), both called from `Task.run`
(`self.apply_print_pages(pages_dir)` right after `apply_pages`, `self.apply_extra_copies(pages_dir)` after `apply_yt_attach`). Both patches are
applied to the pipeline copy (`assemble_app.py:289-290`). The Update station writes one entry per known story (`station/src/newsbank.js:231`:
`{aid, fmt, file, pdf_sha256, docref, story, cells}`).

What happens, run on the patched sheet_task with the station's own entry shape (test `ExtraCopyOnce`):
1. `_extra_copy` (24) writes `_original_pdf/<year>/nb10001o-s00001.pdf`, appends the name to "Other files" with `self.s.put` (NOT listed in
   `res['other_files']`, which is what sheet_task's `verify` and the saver's OTHERFILES-v1 rule read), and fills the `cells`.
2. `apply_extra_copies` (25) sees that name in the row, takes `-v2`, writes the same bytes again as `nb10001o-s00001-v2.pdf`, appends it, and
   lists only `-v2` under `res['other_files']`.
3. Row with a blank "Other files" cell: the saver's diff counts the whole thing as a blank fill, so the save goes through with two files and
   `nb10001o-s00001.pdf; nb10001o-s00001-v2.pdf` in the cell (test 1 FAILS on both counts).
4. Row whose "Other files" already names a file (any row that got an extra copy in an earlier update, or `pq...` from a print edition): the
   appended part is two names where sheet_task reported one, the `other_files_append` rule says no, and the save refuses the WHOLE update with
   `OVERWRITE` (test 2 FAILS: exit 2, "The update would overwrite something already in the workbook").

Rule: ORIGCOPIES-v1 ("the PDF is saved as an extra original copy of that row, add-only"), OTHERFILES-v1 ("filled only by appending names"),
SAVE_RULES refusal list (the OTHERFILES-v1 exception is "exactly the names sheet_task lists in `other_files`").

Fix: one handler. Keep 25's `apply_extra_copies` (it reports `res['other_files']`, handles `kind: print`, `to: file2_else_other` and `-vN`),
remove the `copies` loop and `_extra_copy` from 24's `apply_print_pages`, and make 25 read the station's `cells` the way 24 did (blank-only
through `fill`; decide whether Author / byline, Word count and the citation belong in `EXTRA_FILL_OK`, since 24 filled them and 25 would not).
Also carry over 24's one good check that 25 lacks: skip the copy when the row's File name already holds the same NewsBank record
(`nb<id>...pdf`), otherwise a story whose PDF the save already keeps as its copy gets a second one under `_original_pdf`. Then add the station's
real NewsBank zip to the end-to-end test with a row that already has an "Other files" entry (neither `newsbank_pc/tests/e2e_sheet_task.py`, which
applies only patches 01-09 + 28, nor the app tests cover the two patches together).

Tests: `work/saver/tests/review3/test_review3_extracopies.py` (both FAIL).

### 2. Medium: an error after the swap makes `rename_step` undo the file moves while the workbook keeps the new names

`work/localapp/app/src/station/switchover.py:553-567` (`rename_step`: `except Exception: RF.undo(journal); raise`), with `run_cell_step`'s
post-swap work at `:529-547`: `os.replace` (529), checksum (533), ledger (540, OSError caught), `init_fn` (542, nothing caught), the step's log
`(lay.state / 'logs').mkdir(...)` and `write_text` (546-547, nothing caught). Also `auto_rename` (`:573-585`), which runs the same path after
every save whose rows changed story or role (`station_cli.py:231`) and inside the `datafix_structural` step (`:656`).

Only `SwitchRefused('COMMIT_FAILED')` is treated as "the master was replaced". Any other exception raised after line 529 (an `OSError` from the
log write: disk full, a `logs` entry that is not a folder, a permission problem; an exception out of `init_fn`; any bug) reaches the bare
`except Exception` and every file (copy, raw page, OCR text) is renamed BACK, with the ledger already holding the `rename_files` entry and the
workbook already holding the new names. On the day that is ~1,000 cells pointing at files that are not there; the page is rebuilt from that
workbook; the next `RF.plan` lists them as "not in the library: left as they are", so nothing repairs it later. No file is lost, but the
workbook and the library disagree silently. The journal on disk still says every move is `done` (undo does not re-save it).

Test: `work/localapp/app/tests/review3/test_review3_switchover.py::RenameUndo` (FAILS: cell `ws00001o-s00001.html`, library
`2026/ws00001r-s00001.html`, ledger `['init', 'rename_files', 'init']`).

Fix: have `run_cell_step` mark the point of no return (e.g. set a flag or raise a distinct exception class once `os.replace` has returned) and in
`rename_step` undo only when that point was not reached; after it, keep the files, report the error and still write the rename list. Cheap.

### 3. Low-to-medium: the screen's one backup is reused in a later session although the workbook changed since

`switchover.py:590-607` (`_make_backup`: returns the backup recorded in `state/switchover.json` whenever the file exists; it never compares it
with the workbook) and `:626` (`apply_steps` makes it once before the loop and hands it to every step as `shared_backup`).

The SWITCHOVER-v1 follow-up says "one backup first" for the screen's steps, and within one session that is what happens. But the screen is also
built for "step by step", stays until the person presses Finished, and a save or an "Accept the workbook" can happen between two sessions.
Then a later step's ledger entry names a backup whose content is not the workbook the step started from (`before_sha` and the backup's checksum
differ), the COMMIT_FAILED message ("The backup is <name>") would point at the wrong file, and the state before that step exists nowhere on disk
(the saver's own backup holds the state before the save, not after it).

Test: `test_review3_switchover.py::StaleBackup` (FAILS: the backup lacks the row a save added in between).

Fix: in `_make_backup`, make a new backup unless the workbook's checksum equals the recorded backup's checksum or the `sha` recorded for the last
finished step; record the new one. One comparison.

### 4. Low: the rename journal cannot be used after a crash, and nothing reads it anyway

`work/localapp/app/src/station/rename_files.py:240-265` (`move_files`: the journal is written with every move `planned` before the first
`os.rename` and again only after the last one), `:268-275` (`undo`, in-process only). There is no recovery function and `library_index` (`:59-71`)
does not notice `.rnN` files.

A crash between the two writes (power loss, the black window closed: ~1,000 files times up to three partners, a few seconds) leaves some files
under temporary `.rn<N>` names and some at their new names, with a journal that says `planned` for all of them. The workbook is untouched (the
step had not reached it), so nothing is lost; but the next plan simply lists those files as "not in the library", and only a person comparing the
journal with the folder can put them back.

Test: `test_review3_switchover.py::Journal` (FAILS: the journal says planned four times while `2026/nb00002r-s00002.pdf.rn0` sits in the library).

Fix: save the journal after every move (or at least after each phase), and add `rename_files.recover(journal)` that finishes or undoes from the
on-disk states, called from the station before a plan when a `rename_journal_*.json` is not marked finished.

### 5. Low: the "Switch-over changes" screen never appears if the page build fails right after the setup

`work/localapp/app/src/station/station_cli.py:384-415` (`do_setup_run`: `rebuild_page` at 394 returns at 396 on failure, the `setup-*.json` log is
written only at 399-401), `station_server.py:506` (`setup_done` = that log exists), `web/panel.js:150` (the screen needs `setup_done`).

The files are copied and the workbook accepted, "Rebuild the page" under Repairs fixes the page, but the setup log never gets written, so the
screen stays hidden. The only way in is "Set up again from the Mac library" with Repairs, which backs up and replaces the workbook. No data risk;
a stuck day. Fix: write the setup log before the page build (with the page result added after), or let `setup_done` also count a workbook plus
a ledger `init` entry whose note starts with "set up from the Mac library".

### 6. Low: two switch-over steps do not count as "Last updated"

`work/localapp/app/src/station/common.py:246` (`UPDATE_VERBS` lacks `rename_files` and `datafix_structural`), used by `last_updated` (`:275`) for
the masthead and for the date a refresh file carries. LASTUPDATED-v1 says a switch-over change counts. Test: `test_review3_switchover.py::
LastUpdated` (FAILS). Fix: add the two verbs.

### 7. Low: the drop step does not look at "Other files" when deciding that another row still needs a file

`work/localapp/app/src/station/drop_unverified.py:33` (`FILE_COLS` without "Other files") and `:147-155` (`held` reads columns named "File name"
and "Transcript file" only). On the day the column does not exist yet (it is added by the later `other_files` step), so this cannot bite; it
can if the drop step is run after a save that already wrote extra copies. The deletion is also limited to files named in the dropped row or
named after its Article ID, so the only exposure is a copy listed in another row's "Other files" under the dropped row's number. Fix: add the
column to both places; two lines.

## What I checked and found sound

- **Re-checking on the real workbook (newer rows, rows changed since the lists were made).** Every step plans from the workbook as it is now
  and the screen refuses on any difference: `plan_prjudge` requires the row, Press release still Yes, the same Story ID, outlet and headline
  prefix, and not a copy of an own release (`switchover.py:155-187`); `plan_datafix` writes blanks only unless the line says overwrite AND the
  cell still holds the line's "Current" (`:242-310`; the shipped CSVs have no overwrite line with a blank Current); `datafix_structural.plan`
  re-checks the Unlinked key, the Coverage row's link, both Story IDs, both roles and the Language (`:49-70`); `drop_unverified.plan` and
  `rename_files.plan` scan the live workbook; `apply_steps` compares each step's fresh digest with the one the person looked at (`:633-675`,
  digests carry no row numbers, so an earlier step's deletions do not invalidate them wrongly), and `run_cell_step` re-reads the Article ID at the
  planned row and every planned cell's expected value at write time (`:499-504`: ROWS_MOVED / CHANGED). Running a step twice is harmless: every
  plan comes back empty (or, for prcolor, identical) the second time, and `apply_steps` refuses a step the state marks done.
- **Each step's own independent check.** `check_cells` (`switchover.py:384-459`) loads master and staged copy and compares tabs, header, size,
  frozen panes, auto-filter, every cell's value, every cell's look (font, fill, border, alignment, number format) and font colour, row heights and
  hidden flags, and every hyperlink per tab against the plan; the planned cells may change only to the planned values, the planned rows only to the
  planned colour. `datafix_structural.make_check` covers the two tabs it skips (Unlinked = before minus the retired keys, values and hyperlinks;
  Originals = Coverage's Original rows cell for cell, hyperlinks, no duplicate Article ID). `other_files_column.check_staged` allows exactly the
  new header cell, one empty cell per row with the look of its left neighbour, width and widened filter. `drop_unverified._check_staged` reuses
  the saver's `saver_diff.compare` (keyed rows, hyperlinks, counts) and allows only the planned Coverage and A/V rows to be missing.
- **Write sequence on every step.** Excel closed (lock file, and on Windows an `r+b` probe), no `saver.lock`, baseline `ok`; checksum recorded;
  staged file under a unique name in `data/tmp` (never beside the master); check; Excel and checksum re-checked; `os.replace`; checksum after;
  ledger line; `saver init` so the new workbook is the baseline; a log with the full change list. A `PermissionError` on the swap (Excel, a
  scanner) refuses with the master untouched. The saver's own `commit` now retries the swap four times over about five seconds and moves a
  refused staged copy into `--out` (REVIEW_2 lesser notes 1 and 2 done), writes the ledger line before the library step and reports library
  trouble as `partial` with the files that did not land (finding 2 of REVIEW_2 done), guards `..` paths in `commit_library` (finding 3 done), and
  `reuse_preview` runs the independent diff again under the lock and requires the token to come out of it (finding 1 done); the station sets
  TMP/TEMP/TMPDIR to `data/tmp` for every child (finding 4 done); `post_save.recover` repairs the pipeline list after a crash in the sync window
  (finding 5 done). `read_sheet_task_constants` now resolves `PRINT_TAB` inside `VT_NEW_OK`, so the saver's diff allows the new Unlinked rows
  patch 24 writes and nothing else.
- **DROPUNVERIFIED-v1 exactly.** Rows deleted in one pass with hyperlinks re-anchored and row dimensions moved (`delete_rows_batch`); openpyxl
  collects hyperlinks from the cells at write time (`openpyxl/cell/_writer.py`), so a link on a kept row stays on it. Originals and Removed untouched.
  `reserved_ids.json` written before the swap, read by sheet_task (patch 19: floors for Article and Story IDs, plus a verify problem on any reuse)
  and by build_data (patch 20: the station's "next free numbers"). Files deleted only inside `data/library`, only when no remaining row of any tab
  names them, listed with their checksum before and after, and carried to readers in the refresh manifest where a reader deletes only a file
  whose checksum is the one the keeper deleted (`refresh.py:420-436`).
- **RENAME-v1 exactly.** A cell is renamed only when the name is a schema name that carries the row's own Article ID or Print Article ID; a
  cell naming another row's file is left alone but follows the file; `Reprint (unverified)` and rows without a real Story ID are left alone;
  two rows disagreeing, a taken new name, a taken partner name, a file in two year folders or missing: not renamed and listed; two-phase moves so a
  swap cannot collide; `os.rename` never overwrites on Windows; the OCR partner naming matches the library (`<stem>.ocr.txt`, 202 such files in the
  snapshot); the old -> new list is a new file in `_renamed/`. The workbook changes then go through `run_cell_step` with the full cell check, and a
  refusal BEFORE the swap puts every file back (verified by the undo code; the exception is finding 2).
- **DATAFIX-v1 as decided.** `make_approved.py` produces exactly the approved sets (A/high + A/medium print pages with Edition Web -> Web +
  Print as an overwrite only where it says Web; the 3 Language cells; the 14 Author 1 clears; NewsBank fills high + medium; 117 Page corrections;
  32 retirements; the two English-Original swaps; the 13 organisation posts moved into PRJUDGE-v2 unmark; 01920 and 03486 listed, not changed).
  The Unlinked rows are retired only once the row's link is filled (or planned in the same run), and the retired rows are written to a CSV first.
  The English-Original swap mirrors `sheet_task.swap_original` (carry blank-only, clear the old row, `# of reprints` stays, Team note line, Role
  fill) and rebuilds Originals the way every save does (`sheet_task.py:4848` calls `rebuild_originals` on every run, so the rebuilt tab is the
  status quo); no Article ID is made or changed.
- **PRJUDGE-v2 / PRCOLOR-v1.** 131 unmark + 3 mark candidates in `prjudge_v2.json`, 05166 left alone and listed; Role filled only on Originals
  that lack one; purple only for Press release = Yes, red rows left red; the save's `mark_red` (patch 28) colours new and flagged rows the same way;
  the station's per-item No is honoured only when the outlet-name rule would otherwise mark Yes and the row is not already Yes (patch 22), own-release
  copies untouched.
- **OTHERFILES-v1 column and the saver's rule.** The column step is a recorded header exception with its own check; the saver's
  `other_files_append` rule allows only "the old names first, unchanged, in order, then exactly what sheet_task reported" (`saver_diff.py:544-552`,
  `test_saver_otherfiles.py`). PRINTORIG-v1 option B: print originals are found by name only (`build_data` patch 26 reads `_original_pdf/<year>/
  <id>_p<pages>.pdf` from the library and the save's staged pages), the server serves only that pattern (`station_server.py:45, 200-210`), the
  viewer adds the button only when one exists (patch 27). Patch 24's Unlinked writer takes its Article ID from the one sequence, never adds a
  print-page link the tab already has, and copies the row style.
- **Setup from the Mac library.** Every listed file must be present with the listed checksum, placeholders and empty files refused, names checked
  against the refresh allow-list first (0 of the snapshot's 12,637 files would be refused), everything copied into `data/tmp/setup_<stamp>` with the
  checksum taken from the bytes written and again from the file, then put in place with `os.replace`; `data/workbook` and `data/library` are not
  written unless every file checked out; a second run refuses unless Repairs, and Repairs refuses when an existing library file differs.
- **ID assignment outside the save: none.** The screen makes or changes no Article ID or Story ID; the drop step only reserves; the station's
  numbers remain guesses the save checks and renames (unchanged `check_names_after`).
- **Readers.** Every switch-over verb, the setup, the drop and the datafix upload are refused for a reader copy by the server (`station_server.py:
  225, 289, 371`) and again by the CLI (`station_cli.py:536`); `refresh.take` adds library files, replaces page files keeping the old ones, deletes
  only checksum-matched files, and seeds its ledger.
- **Windows.** `os.replace` and `os.rename` only; `.rn<N>` temporaries in the same folder; NAME_RX is lowercase so a case-only different file is
  simply not matched, and on a case-insensitive disk `Path(dst).exists()` stops the move; paths stay short; `newline='\n'` and `encoding='utf-8'`
  everywhere; the Pacific date falls back to UTC without zoneinfo.
- **Update folder.** `check_pdfs` now also covers a run's `extra_copies` (same checksum and safety checks); the for-Update file's rows block gains
  `files` and the Unlinked rows of kind `P` for the station's print-page checks (read-only); PCEDITS-v1 composes a fresh db folder per call, moves
  used-up edits to `db/_applied/edits/`, marks reported ones and leaves an edit that changed meanwhile pending.

## Lesser notes

1. `plan_datafix` says "two fixes disagree about this cell (neither applied)" but the first of the two is applied (`switchover.py:282-289`).
2. Fix values are written as strings (`cell.value = v`), so a Page or Word count cell that held a number becomes text; the page build and the
   saver's diff both read cells as text, and sheet_task's `fill` writes strings too, so no rule breaks.
3. A rename is not carried to readers by an incremental refresh (it carries only pages added by saves); after a later `auto_rename` the readers'
   libraries keep the old names until a full refresh, which then adds the new names beside the old ones. Nothing reads reader library names today.
4. `rename_files.library_index` indexes the year folders only, so `_original_pdf/<year>/nb...pdf` and `pq...pdf` extra copies are never renamed and
   show up as "not in the library" in the rename list.
5. `auto_rename` after a save makes its own `BACKUP before rename_files` each time; those are never trimmed (the saver trims only backups a `save`
   entry names).
6. `drop_unverified.apply` writes `reserved_ids.json` before the swap by design; a refusal after that leaves the reservation (too much, never too
   little).
7. `setup_mac.run` stages a full copy of the library inside `data/tmp` before moving it into place, so the PC needs free space for the library
   twice over during the setup.
