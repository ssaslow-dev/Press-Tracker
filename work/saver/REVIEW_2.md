# REVIEW_2: line-by-line safety review before the first live save (checkpoint 3)

Reviewer: Fable, 2026-11-03, repository at commit 19551dd. Read: code and rules only (CLAUDE.md hard rules, work/saver/SAVE_RULES.md with
Sammy's answers, the DECISIONS entries SAVER-RULES-v1, LIBFILES-v1 + STATIONNAMES, MULTIPC-v2, GOVIT-v1, PHOTOLINK-v1, YTBROADCAST-v1,
YTLINK-v1, NOQUEUE-v1, NEWSBANKPDF-v1, PROQUESTPDF-v1, CONTRACT.md NAMING-v2 and the run-doc schema). Builder READMEs and commit messages
were not used for conclusions.

Scope read in full: `work/saver/src/{saver,saver_diff,saver_steps}.py` (incl. `save --from-preview`); `work/localapp/updatefolder/{formats,
take_update,layout,make_for_update}.py`; `work/localapp/app/src/station/{station_server,station_cli,refresh,post_save,launcher,common}.py`;
`work/localapp/server/server.py`; `work/localapp/app/assemble_app.py` (the exactly-once patch applier) with `app/patches/*.patch`,
`photolink.py` and `winpack/patches/*`; the spots of `code/sheet_task.py` the patches touch and the ones that write files (`apply_pages`,
`execute_removals`, `fill`, `load_db`, `add_row` dedupe); `code/img_embed.py` network path; `code/date_rules.py`, `code/release_rule.py`.

Suites run by me (2026-11-03):

| suite | result |
|---|---|
| `work/saver`: `tests` | 126 tests, OK (1 skipped: the replay fixture holds the workbook and is not in the repo) |
| `work/saver`: `tests/review` (checkpoint 1) | 25 tests, OK |
| `work/localapp/updatefolder`: `tests` | 80 tests, OK |
| `work/localapp/app`: `tests` (assembled Linux build in the scratchpad, Python 3.13.18; Chromium through Playwright) | 30 tests, OK (1 skipped), 23 min; no net-guard log (see "App suite") |
| patch drift: every hunk of the 10 patches applied exactly once to today's `code/` and `work/saver/src/saver_steps.py` | OK |
| **new** `work/saver/tests/review2` | 5 tests: 4 FAIL (findings 1, 2, 3), 1 pass |
| **new** `work/localapp/updatefolder/tests/review2` | 2 tests: 2 FAIL (finding 4) |

## Verdict: fix first, then a supervised first save is safe

Two small changes in `saver.py` (findings 1 and 2) should be made before the first live save. Neither needs a design change; both have
failing tests in `tests/review2/` that will turn green. Findings 3 to 5 are low and can go in the same pass; none of them blocks a
supervised save. Nothing I found can lose data: at every step the workbook exists as either the verified backup or the verified new
master, and the library is only ever added to.

What is solid (details under "Checked and adequate"): the independent cell diff and its allow-list; backup, uniquely named staged file,
checked swap and post-swap checksum; moves instead of deletes everywhere; zip and refresh-file handling (names, sizes, hashes, links,
PDFs); reader/keeper roles; loopback-only server; no network in the program; the patch applier.

## Findings, ranked

### 1. Medium: `save --from-preview` commits the staged workbook without an independent diff

`work/saver/src/saver.py:1099-1192` (`reuse_preview`), token check at 1123-1133, staged-file check at 1151-1158; `cmd_save` 1231-1234.

Rule: SAVE_RULES "What preview shows" / step 4 ("compares result and original cell by cell") and the `--token` contract in `build_parser`
(saver.py:451): "save refuses (TOKEN_STALE) unless its own fresh diff gives the same token". The PC station always saves with
`--from-preview` (take_update.py:220-222), so the first live save will go through this path.

What the code does: the reuse path trusts three files in the preview folder: `preview_state.json` (holds `after_sha` of the staged
workbook), `diff.tsv` (the token is `sha256(run + before_sha + sha256(diff.tsv))`, saver_diff.py:317) and the staged `.xlsx`. The staged
file is checked only against `after_sha` **from the same state file**. `after_sha` is not part of the token. So a staged workbook that was
changed after the preview, together with the one number in `preview_state.json`, passes every check: same token, same diff file, same
inputs, and `commit()` copies it over the master.

Failure scenario: between preview and save (up to 30 minutes, the folder is `data/updates/work/<id>/preview-1/`), anything that rewrites
the staged `.xlsx` and `preview_state.json` consistently (a person, a sync tool restoring an older copy together with an older state file,
a mistaken hand fix) makes the save write cells the diff never saw. The result then still says "2 rows added, 9 cells filled" and exit 0.
The existing test `test_a_staged_file_changed_after_the_preview_is_not_trusted` covers only the inconsistent case (file changed, state not).

Test: `tests/review2/test_review2_save.py::ReuseTamper::test_a_consistently_edited_staged_workbook_is_not_committed` (FAILS: the master
ends up with the overwritten headline `TAMPERED`, exit 0).

Fix (cheap: seconds, not minutes): in `reuse_preview`, after the lock is held, run `D.compare(d/'in.xlsx', out_xlsx, result, result2, ...)`
again with the constants read from the preview's pipeline copy, refuse if `rep.refusal()` is set, and require
`D.preview_token(run, before_sha, rep.tsv_text()) == a.token`. That restores "save's own fresh diff" while still skipping the pipeline
passes. (Binding `after_sha` into the token is not enough on its own: the token is handed out before the save.)

### 2. Medium: the ledger is written after the library step, and an unexpected error there is reported as "Not written"

`work/saver/src/saver.py:1006` (`commit()` returns `... 'library': commit_library(job)`), `:1239-1252` (`append_ledger` after `commit`
returns), `:1297-1302` (`except Exception` with `committed` still False), `:1009-1039` (`commit_library` catches `OSError` only).

Rule: SAVE_RULES step 6 ("logs old and new checksum, backup name, counts") and "Master, library and log change together or not at
all"; the code's own comment at saver.py:1252 says the ledger entry is appended "right after the master is verified, so a crash in the
library step cannot leave it unrecorded". It is not: `commit_library` runs inside `commit()`, before the entry is appended.

Failure scenarios:
- A kill while library files are being copied (closing the tracker's black window ends every child process; a power cut; Task Manager).
  The master is the new file, the backup exists, the ledger still names the old checksum. On restart the panel shows the workbook as
  changed; the only offered way on is "Accept the workbook as it is now" (which is meant for Sammy's own Excel edits). The update is still
  in `updates/staging`, not in the ledger, not in the local db, not in `updates/done`, so `station_cli.already_saved` (:108-131) does not
  stop it from being taken in a second time. sheet_task's dedupe catches rows whose link or outlet+headline+date is already on the sheet,
  so duplicates are unlikely but not excluded (a NewsBank or ProQuest row whose headline differs from the station's extraction).
- Any non-`OSError` exception inside `commit_library` (`commit_library` is the only step after the swap that runs user-dependent code
  paths) escapes `commit()` before `committed = True`: `cmd_save` answers `written: False`, "Not written: unexpected error", exit 4, with
  no ledger entry, although the master was replaced. take_update then leaves the update in staging and does not merge the run document.

Tests: `tests/review2/test_review2_save.py::CommitOrder::test_a_kill_during_the_library_step_leaves_the_master_recorded` (FAILS: ledger
still `init`/old sha) and `::test_an_unexpected_error_in_the_library_step_still_reports_the_master_as_written` (FAILS: exit 4, written
False, no ledger entry, master replaced).

Fix: move `commit_library` out of `commit()`; in `cmd_save` the order becomes commit (swap + verify) -> `committed = True` ->
`append_ledger` -> library step wrapped in `try/except Exception` that sets `library.partial` and a `post_commit_error`. Then a crash
during the library step leaves a ledger entry and `already_saved` refuses the second take-in; the partial library is listed in the result.

### 3. Low: a `File name` cell can steer a removal move outside the library

`work/saver/src/saver.py:1027` and `:1032` (`src = lib / Path(*rel.split('/'))`, `move_unique(src, lib / '_to_delete' / ...)`), fed by
`code/sheet_task.py:3576-3579` (`execute_removals` builds `'<year>/<File name>'` from the workbook cell).

Rule: CLAUDE.md "files only inside the app folder", "the library is add-only; files that must go are moved to `_to_delete/`".

Scenario: a Coverage row whose File name cell reads `../../something.html` (a hand edit, a paste) is removed in the tracker; the save moves
`<library parent>/something.html` into the library (`lib/_to_delete/2026/../../x` resolves to `lib/x`). Confirmed by running
`commit_library` with such a path: the outside file was moved. The same holds for `pages` paths in principle, but those come from
`rglob` of the saver's own output folder and cannot contain `..` (the review test for that passes).

Test: `tests/review2/test_review2_save.py::LibraryPaths::test_a_removed_file_path_cannot_leave_the_library` (FAILS).

Fix: in `commit_library`, resolve `src` and the target and refuse (list under `removed_failed`) any path that is not inside `lib`; the same
one-line guard for `pages`.

### 4. Low: the save's child processes write temporary files outside the app folder

`work/localapp/app/src/station/station_cli.py:41-53` (`_SubprocessShim.run` sets `AJG_NO_NETWORK`, `AJG_LINK_PHOTOS` only), `:74-76`
(`py()`), `:56-66` (`boot` sets `tempfile.tempdir` for the station process only); `station_server.py:77` (`Jobs._run` env).

Rule: GOVIT-v1 "read and write only inside the app's own folder (plus files the user picks)".

What happens: `tempfile.tempdir` is per process. The save program and sheet_task are children; openpyxl writes every worksheet it saves to
`tempfile.NamedTemporaryFile(prefix='openpyxl.')` (openpyxl 3.1.5 `worksheet/_writer.py:35-41`, confirmed in the assembled build), i.e.
under `%TEMP%` on the PC (`C:\Users\<user>\AppData\Local\Temp`), removed afterwards. Each save does this for `out1.xlsx` and the pass-2
output (every tab). Not a safety problem for the data, but a plain contradiction of what the IT note promises.

Test: `work/localapp/updatefolder/tests/review2/test_review2_station.py::ChildTempFolder` (2 FAIL: no `TMP`/`TEMP`/`TMPDIR` in the
children's environment).

Fix: set `TMP`, `TEMP` and `TMPDIR` to `<root>/data/tmp` in the shim env, in `py()` and in `Jobs._run`; one line each.

### 5. Low: a crash during the post-save sync can leave the pipeline folder refusing every later save, with no way back in the panel

`work/localapp/app/src/station/post_save.py:63-82` (state files replaced one by one, `PIPELINE.sha256` rewritten at the end).

Rule: SAVE_RULES refusal list ("sheet_task.py's own verification"), saver.py:700-704 (`PIPELINE_MISMATCH` refuses before anything else);
`station_cli.rebuild_page` (:233-235) refuses the same way.

Scenario: the save has been written and recorded (ledger OK). While `post_save.sync` replaces `app/pipeline/outlets.json`, `release_
texts.json` ... the process dies before `write_pipeline_sha`. From then on every preview, save and "Rebuild the page" refuses with
"pipeline files differ from PIPELINE.sha256", and nothing in the panel repairs it (the old files are in `data/state/pipeline_replaced/
<stamp>/`, the fix is to copy them back or regenerate the list by hand). The window is well under a second, so no test; listed because the
stuck state has no in-app exit.

Fix: either write the list first from the hashes of the files about to land and then replace the files (a crash then leaves "list newer
than files", which `verify_pipeline` could accept when every mismatching file equals its copy in the newest `pipeline_replaced` folder), or
add a panel action "Repair the pipeline list" that runs `pipeline_sha.py` after the user confirms.

## What a user sees after a crash at each step of a PC save, and whether data can be lost

Order: panel "Save" -> `station_cli.do_save` (AppLock) -> `take_update.save` -> `saver.py save` -> `take_update` merge/finish ->
`post_save.sync`. "Data" = workbook, library, ledger. Nothing is deleted at any step; the only `unlink`s in scope are the program's own
`.part` and tmp files (refresh.py:292,341; server.py:141; make_for_update.py:196-198).

| crash point | state left behind | what the user sees next | data loss |
|---|---|---|---|
| before the saver starts | `app.lock` left | "Another save is running on <host> ... wait" for up to 30 min, then the stale lock is moved aside | none |
| saver pipeline passes (preview part) | `saver.lock`, `library/.sheet_task.lock`, partial `preview-1/` folder | LOCKED for 30 min; stale locks moved to `state/logs/` and `library/_to_delete/`, never deleted | none |
| after the backup (`commit` step 11) | one extra backup (never trimmed: not in the ledger) | as above | none |
| staged copy written beside the master | a `... SAVED <run> <time>.xlsx` file next to the master (lesser note 1) | as above | none |
| right after `os.replace` (atomic on NTFS) | master = new; ledger = old; library untouched | panel: "the workbook changed", only "Accept the workbook" offered; the update can be taken in again (finding 2) | none (backup verified) |
| during the library copy | as above, library partial | same as above | none |
| after `append_ledger` | ledger OK; library complete; update still in `staging`; local db without the run doc; page not rebuilt | "This update (run X) was already saved" on any re-take; "Rebuild the page" fixes the page; the next for-Update file lacks this run's `searched_to`, so the station searches that window again and the save dedupes | none |
| `merge_into_local_db` / `finish` / `check_names_after` | partial local db, staging or done folder | as above; the kept update folder may not be renamed (informational only) | none |
| `post_save.sync` | page/shards partly replaced (old copies in `site_replaced/`, `copies/_replaced/`); pipeline list possibly stale (finding 5) | page may show old data until "Rebuild"; worst case PIPELINE_MISMATCH on everything until repaired by hand | none |

Reader side (`refresh.take`): a crash after the workbook swap and before `init_fn` leaves the reader's ledger at the old checksum and
`refresh_applied.json` unwritten; the same refresh can be applied again (workbook rewritten with the same bytes, library skipped, site
replaced again) and that run re-seeds the ledger. No loss; the reader cannot save anyway.

## Checked and adequate

- **Fill blanks only.** `sheet_task.fill` (code/sheet_task.py:889-903) writes blanks only and lists conflicts. Independently, `saver_diff.
  compare` refuses any non-blank cell that changes or is cleared unless one of the recorded exceptions names it: `# of reprints` equal to
  the recorded new count (reprint_counts), origin swap cells, RETRY/BLOCKED cells, queue cells (unused: NOQUEUE-v1), YTBROADCAST-v1 cells
  only when the new value is "Broadcast segment" / Video -> TV|Radio and sheet_task listed the cell in `yt_attached`, A/V `Item type` for
  those rows, and the Press releases derived columns (`VT_DERIVED_REL`, read from sheet_task's source by ast, never copied). Row counts
  (after = before + added - moved), Originals mirror, every hyperlink's presence and target, tabs, headers, row order and foreign Article
  IDs are refused. The NewsBank/ProQuest patches (09, 12) and the alias patch (14) write only through `fill`.
- **Workbook write path** (saver.py:947-1006): staged name never the master's name; lock ownership re-checked; master checksum re-checked
  before the backup, after the backup and just before the swap; Excel re-checked; backup verified against the pre-recorded checksum; a
  staged name already beside the master is refused, never overwritten; `os.replace`; the master's checksum verified after the swap with
  the backup named in the message. Refresh (refresh.py:276-296) follows the same pattern for readers.
- **No deletes of user data.** Library removals go to `library/_to_delete/` with a `_moves_<date>.tsv` line; backups beyond three to
  `backups/_to_delete/`; locks to `state/logs/` or `library/_to_delete/`; db documents to `db/_deleted/`, `_replaced/`, `_archived/`; page
  and shard replacements keep the old file under `site_replaced/` and `copies/_replaced/`; refused updates go to `updates/rejected/`.
- **Update zip** (formats.py): allow-listed names only (manifest, `db/<7 collections>/<id>.json`, `files/<id>.pdf`, `library/...` by the
  NAMING-v2 schema); no `..`, absolute, drive, backslash, control characters or surrounding spaces; Windows reserved names refused;
  case-insensitive duplicates refused; symlink and non-regular entries refused; encrypted or oddly compressed entries refused; zip, entry,
  total, count and ratio caps; each entry read with a hard cap and must equal its header size; the manifest must list exactly the entries
  with matching sha256 and size; every library file must be claimed exactly once by the names block with exactly the schema path; a PDF
  must be the one its pages document names (same sha256), and is refused if it carries JavaScript, launch/open actions, embedded files,
  forms, encryption, rich media (hex-escaped names and object streams decoded, plus a pypdf object walk). Entries are written as plain
  files under `updates/staging/<id>/` (no `extract`), so nothing can land elsewhere or as a link.
- **Refresh zip** (refresh.py): four kinds with extension allow-lists, one workbook at the top matching the fingerprint, html only as
  `site/index.html`, reserved names and `..` refused, caps and ratio, every entry hashed before anything is written; a reader refuses an
  older-or-equal `seq` and an incremental file whose `base_seq` is beyond what it has (no roll-back, no skipped refresh); a keeper refuses
  to take one; the library is add-only (existing names skipped and counted). Notes, views and edits never travel.
- **Roles** (MULTIPC-v2): `station_server._station` and `_upload` refuse keeper-only verbs for a reader and `refresh_take` for the keeper;
  `station_cli.main` refuses again; `refresh.make/take` refuse a third time. The page cannot change `data/role.json`: the store writes only
  `data/db/<collection>/<id>.json` with validated names (server.py:38-43). (Editing `role.json` by hand is the intended way to appoint a
  keeper; worth one line in the READ ME.)
- **Server**: binds 127.0.0.1 only, fresh token per launch, Host/Origin checked, static files confined by realpath, no listings, ids
  validated incl. reserved names, body cap, delete = move. Station endpoints add role checks, strict regexes for file and update ids, a
  one-at-a-time job runner plus the cross-process `app.lock`.
- **Network**: no socket, urllib or requests use in the saver, update-folder or station code (only `gethostname` and the loopback server).
  Pipeline subprocesses run with every proxy variable pointed at a dead port and `NO_PROXY` removed (saver_steps.offline_env), plus
  `AJG_NO_NETWORK=1` (winpack patch 02: `img_embed` never imports `requests`). PHOTOLINK-v1 pages keep one https address per photo,
  strip scripts, set `referrerpolicy="no-referrer" loading="lazy"`, pass the media gate; the server sends `Referrer-Policy: no-referrer`
  on everything. The app suite's net guard (every python process of the build refuses and logs non-loopback connections) left no log.
- **Names** (LIBFILES-v1, STATIONNAMES): IDs come only from sheet_task; the station's names are checked after the save and only the copy
  kept with the update is renamed (take_update.reconcile_names), never the workbook or the library, which the save wrote from the same
  names. The pages the save writes are the ones committed; the zip's `library/` HTML is never used as a source.
- **Reuse of a preview** (apart from finding 1): refused after 30 minutes, after a save (state renamed `.used`), for another program
  version, pipeline list, workbook path or checksum, update zip, db, library collision set, date, environment, or when any preview file
  changed; locks, Excel, ledger and master checksum are re-checked under the lock.
- **Windows**: `os.replace` onto a file Excel or a scanner holds fails and is reported with the master untouched (tested); exclusive-create
  locks with tokens, stale after 30 min, released by a move; `-X utf8` and explicit `encoding='utf-8'` on every child and file;
  `newline='\n'` on the ledger and logs; no path in scope exceeds ~150 characters under a normal app-folder depth.
- **Patch applier** (assemble_app.py:74-101): every hunk must match exactly once or the build stops; applied to copies via a new file and
  `os.replace`; the order of 09/12/14 on sheet_task.py is fixed in code. All ten patches match today's sources.
- **Double take-in**: `station_cli.already_saved` checks the ledger, the local db run documents and `updates/done` before inspect and save.

## Lesser notes (no rule broken, worth a line each)

1. `commit()` leaves the staged copy beside the master when `os.replace` fails (saver.py:997-1000); harmless but confusing. Move it into
   `--out` under `rejected ...` as the checksum-mismatch branch already does (:994).
2. Antivirus holds: a sharing violation on `os.replace` refuses at once. A short retry (3-5 tries over a few seconds, then refuse) would
   avoid a false "COMMIT_FAILED" on a slow scanner. The backup stays and nothing is lost either way.
3. While the panel is open the status poll calls `excel_open`, which on Windows opens the workbook for writing every 5 s (common.py:231-
   238, panel.js:71). Polling pauses while a job runs (`state.busy`), so it cannot collide with the swap; keep it that way.
4. `Jobs._run` kills only `station_cli.py` on its 2-hour timeout (station_server.py:79); the saver grandchild keeps running under its own
   lock. The message "was stopped" should say it may still be finishing.
5. Reader backups (`BACKUP before refresh N`) are never trimmed (refresh.py:279-288): about 7 MB per refresh. Add the saver's keep-3 rule.
6. SAVE_RULES answer 5, second half (pre-saver backups moved to `Backups/_to_delete/` after the first confirmed live save) is not
   implemented; `trim_backups` only ever touches backups the ledger names (saver.py:929-944). Safe side; either build it or record the
   deviation.
7. The PC's own "Remove story" edits never reach a save: `station_cli.do_save` calls `TU.save` without `include_local_edits` (:184,
   take_update.py:163-175). The for-Update file does list them (`edits_removed`), so the station will not re-add those stories, but the
   rows stay on Coverage. Decide and record (NOQUEUE-v1 does not cover removals).
   **Resolved 2026-11-03 (PCEDITS-v1):** saves and previews include the pending edits and removals by default; "Save my edits (N)" saves them alone; used-up docs move to `db/_applied/edits/`.
8. `reuse_preview` checks the inputs, pipeline and preview files (saver.py:1134-1165) before taking the lock (:1172). Move those checks
   under the lock; cheap.
9. `refresh.take`: if Excel opens the workbook between the check (:291) and `os.replace` (:294), the PermissionError surfaces as "The
   refresh file could not be read" (station_cli.py:290) and the staged `.part` stays beside the workbook. Catch it and word it.
10. The patched `run_script` passes `-X utf8 -I` but not `-B` (winpack patch 03); under `-I` the `PYTHONDONTWRITEBYTECODE` variable is
    ignored, so `__pycache__` folders appear in the preview's pipeline copy. Inside the app folder, harmless; add `-B`.
11. `Also on caucus site (date)` / `(URL)` are in `VT_DERIVED_REL`, so a change to those two Press-release cells is allowed as "derived".
    If they are ever hand-entered, the allow-list is one column too wide; a sheet_task question, not a saver one.
12. CLAUDE.md still says "use `--no-rebuild` until the rebuild has run once": the station saves with `rebuild=True` and the app suite
    exercises it on the Linux build; after the first supervised save that line can go.

## App suite

`cd work/localapp/app && python3 -I -m unittest discover -s tests -t tests` against the assembled Linux test build in the scratchpad
(`app_build/linux/AJG Tracker`, Python 3.13.18, pinned wheels as BUILD_INFO.json): **30 tests, OK (1 skipped), 1368 s.** The flow
tests (update preview/save through the panel in Chromium, keeper-to-reader refresh round trip, reader refusals, locked concurrent
save, tampered/older/gap refresh files, Excel-open and lock banners, accept-after-hand-edit, LIBFILES names and folders with a second
update whose numbers were taken) all pass, and the net guard installed by the suite left no log in any work copy: no process of the
app tried a non-loopback connection or name lookup.
