# SAVER_SPEC: `saver.py` build spec (for the Sonnet builder)

Companion to SAVE_RULES.md (Sammy's rules; it wins on policy). Source of the procedure: `L/code/sheet_task_prompt.md` (the 7 steps and rules 1 to 9). Rule tags cited, not restated: rule 7 (README; HANDOFF 6.1), REQ-9, QUEUEAPPLY-v1, LEARN-v1, NOSCHED-v1, NOBLOGS-v1, FREEONLY-v1, COLDSTART-F1, AUDIT F8/F9, RELBUTTON-v1, VERIFYTABS-v1. Earlier draft reused where it holds: `L/work/desktop_plan/BUILD_NOTES.md` section 4 (save order, lock, backup, diff allow-list) and section 3 (never delete; move to `_applied/`).

Nothing under `L/code` or `L/build` is edited. The saver calls `sheet_task.py` and the other pipeline scripts as subprocesses, exactly as the prompt does; it adds no data rule of its own. Where this spec and `sheet_task.py`'s behaviour differ, the builder reports it instead of patching either.

## 0. Scope: storage-agnostic

The saver sees only local paths. Who puts files there and takes them back is an **adapter** (section 8). The saver never knows whether `--workbook` is the master on this disk, a mirror of the Mac file, a git checkout or an artifact download.

Runs on Windows and Linux, Python 3.11+, `pathlib` only, no shell-outs to Unix tools (`shasum`, `mv`, `date`, `cp` all become `hashlib`, `shutil.move`, `zoneinfo`, `shutil.copy2`). Every subprocess is `[sys.executable, "-I", script, ...]` with `cwd` = the pipeline folder's parent, as the prompt runs them from the working folder with `pipeline/` relative. Network: none from the saver itself. The only network traffic is inside `sheet_task.py` (photo downloads via `img_embed.py` when `--img-cache` is given), and the lookup cache is consulted first by passing `--lookup-cache` / `--lookup-cache-out` (LEARN-v1). `result.fetch_plan.fetch` is surfaced, never acted on.

## 1. CLI

```
saver.py init    --workbook W --state S --sha SHA [--note TEXT]
saver.py preview --workbook W --db D [--queue Q] --pipeline P --copies C --library LIB --backups B --out O --state S [--today YYYY-MM-DD] [--run RUN_ID] [--refresh] [--idmap FILE] [--img-cache DIR] [--json FILE]
saver.py save    (same arguments as preview) [--token TOKEN] [--master-is-local] [--no-rebuild]
saver.py confirm --state S --sha SHA [--note TEXT]
```

| Argument | Meaning |
|---|---|
| `--workbook W` | The master (or its local mirror). Read in preview; replaced atomically in save. Its folder is where the Excel `~$` lock is looked for. |
| `--db D` | Folder in ArtifactData `list` layout: `runs/`, `pages/`, `edits/`, `reprints/`, `tones/`, `authors/`, `translations/` with `<doc id>.json` each (prompt step 1). A single `db.json` export is also accepted (`--db file.json`). |
| `--queue Q` | Folder with `items/`, `decisions/`, `applied/` (QUEUEAPPLY-v1). Optional; absent = no queue items applied, and `result.queue_applied` must then be empty. |
| `--pipeline P` | The published `pipeline/` files on disk (prompt Fixed facts list). Must contain `PIPELINE.sha256` (one line per file); the saver verifies every listed file and refuses on a mismatch or a missing file (final-int: a missing rule module silently turns a rule off). |
| `--copies C` | Folder holding `articles/manifest.json` and the `articles/<year>.json` shards. The saver runs `--copies-needed` and refuses if a named shard is missing. |
| `--library LIB` | The Tracker library root: `<year>/`, `_original_html/`, `Press releases/`, `_to_delete/`. Release candidates are read from it; new pages are added to it; removals are moved inside it. |
| `--backups B` | Where the backup copy goes. Usually `LIB/Backups`, passed separately so an adapter can put backups elsewhere. |
| `--out O` | Working and output folder for this invocation. Created empty; refused if it exists and is not empty. |
| `--state S` | Folder with `ledger.jsonl`, `saver.lock`, `logs/`. Default `W.parent / ".saver"`. Must travel with the master (section 5). |
| `--today` | Calendar date in America/Los_Angeles (AUDIT F9). Default: computed with `zoneinfo`. Refused if it is later than today in that zone. |
| `--run RUN_ID` | Save this run. Default: the newest run doc with rows / queued bills / releases and no `sheet.written: true` (prompt header; `sheet_task.sheet_applied`). |
| `--refresh` | Continue when nothing is queued (prompt step 1 "A refresh always continues"). |
| `--token` | Preview token; if given, save refuses unless its own fresh diff reproduces it (section 6). |
| `--master-is-local` | `W` is the master itself; the ledger entry is confirmed at once. Without it the entry stays `confirmed: false` until `confirm`. |
| `--no-rebuild` | Skip section 2 step 6. |
| `--json FILE` | Where to write the result (default `O/saver_result.json`). Also printed to stdout as the last line. |

Exit codes: `0` done (preview produced, or save written and confirmed-or-pending); `2` refused, nothing written (result carries `refusal`); `3` nothing queued and no `--refresh` (save writes the "Nothing new to write." writeback only); `4` bad arguments or unreadable inputs; `5` written and verified, but a post-commit step failed (rebuild); `6` written, but the writeback bundle or log could not be written (adapter must read the result from stdout).

## 2. Step mapping: prompt step -> saver / adapter / Claude

| Prompt step | Who | Saver behaviour |
|---|---|---|
| Header: pick the run, say its id | saver | `--run` or newest undone run; `result.run`. Claude says the id in chat. |
| 1 Read the database (ArtifactData `list` -> `db/`, `queue/`) | **adapter** | Saver consumes `--db`, `--queue`. |
| 1 `--check-only` (exit 3 = nothing queued) | saver | Exit 3 unless `--refresh`; writeback bundle has `sheet: {written: true, line: "Nothing new to write."}` for the run. No backup, no lock beyond this check. |
| Rule 1 Excel open / lock | saver | Section 4. |
| 2 Stage the workbook, note mtimeMs, confirm size/mtime, copy to `in.xlsx`, commit backup | adapter stages; saver does the rest | Section 5 (sha ledger replaces mtime). Backup written to `--backups` with a unique name; its sha must equal the master's. |
| 3 Read pipeline files | **adapter** | Saver verifies `PIPELINE.sha256`. |
| 3 `--copies-needed`, stage shards | adapter stages; saver checks | Refusal `INPUT_MISSING` if a shard is absent. |
| 3 `releases_new` items with neither `html` nor `text` -> TinyFish fetch | **Claude** | Saver refuses with `NEEDS_FETCH` listing `{run, url, title}`; Claude fetches (cache first, LEARN-v1), writes `html` into the run doc copy under `--db`, re-runs. Never fetched by the saver. |
| 3 `--release-candidates`, stage `<year>/<file>` | saver | Reads them from `--library` directly (no copy); passes `--library LIB`. |
| 3 main run (the long command) | saver | Verbatim flags + `--lookup-cache P/lookup_cache.json --lookup-cache-out O/lookup_cache.out.json`, `--queue Q` if given, `--idmap` if given. Exit 2 -> refusal `VERIFY_FAILED` with `result.verify.problems`. |
| 3 `build_data.py`, copy `copies_out/` over `copies/articles/`, `relmatch.py` when lists non-empty, `--after-relmatch` second pass | saver | Verbatim. `copies/articles` is first copied from `--copies` into `O/copies/` so the input folder is never modified. `release_related.json` is updated in `O/pipeline_out/`, never in `--pipeline`. Exit 2 -> `VERIFY_FAILED`. |
| Fixed facts `origin_wanted` (CHAINORIG-v1: search, fetch, add Original) | **Claude**, after the save | Listed under `judgment.origin_wanted`. Saver adds nothing. |
| 4 Commit workbook with expectedMtimeMs, `shasum` | saver (local) + adapter (remote) | Section 5. |
| 4 Pages add-only into the library; `_display/` never | saver | `shutil.copy2`; existing name -> `review.name_collision`, file skipped (SAVE_RULES Q3). |
| 4 Removals `mv` to `_to_delete/` | saver | `shutil.move` to `LIB/_to_delete/<same relative path>`; a line per move in `LIB/_to_delete/_moves_<date>.tsv`. |
| 5 Write back (runs `sheet`, `ids`, edits, reprints, pages deletes, review lists, queue `applied` / `items`) | **adapter**, from `O/writeback.json` | Saver composes the exact documents (section 7). REQ-9: the adapter applies `written: true` only after `confirm` (or `--master-is-local`). The prompt's `delete` of pages/edits docs is the adapter's; the saver recommends a move to `_applied/` (BUILD_NOTES 3) and lists the ids. |
| 6 Rebuild (`tabs_data --only releases`, `assemble`, `data/sheet.json`) | saver (optional) | Into `O/site/`. Failure after commit -> exit 5, `site_rebuilt: false`. |
| 7 Publish | **adapter / Claude** | `result.publish` lists what changed: `index.html`, `copies_changed`, `data/sheet.json`, and the conditional pipeline files (outlets, lookup_cache, bills, release_texts, release_related) with their shas. |
| Rule 5 / 7 / 8 / 9 (no web, NOBLOGS, FREEONLY, NOSCHED) | all | Saver has no network code, no scheduler code, no credential handling. `result.skipped` is passed through; the saver never adds or removes a row. |

Judgment items (section 7.3) are surfaced, never resolved. The saver contains no heuristics: if a decision is not in `result.json` or `result2.json`, it is not made.

## 3. Save order (one function, one state machine)

`preview` runs steps 1 to 9 and stops; `save` runs 1 to 14. Any failure returns `refusal` and runs the cleanup (lock release). Steps 1 to 9 write only under `O/` and `S/logs/`.

1. Parse and validate paths; `O` empty; `--today` sane; `S` exists or is created (`init` must have run: `ledger.jsonl` present, else refusal `NO_LEDGER`).
2. Process lock: create `S/saver.lock` with `O_EXCL` containing `{pid, run, at, host}`; exists and younger than 30 min -> `LOCKED`; older -> moved to `S/logs/stale.lock.<at>` and retried once (AUDIT F8 window).
3. Excel check: `W.parent / ("~$" + W.name)` exists -> `EXCEL_OPEN`; `open(W, "r+b")` raises `PermissionError` -> `EXCEL_OPEN` (Windows; on Linux and macOS only the `~$` test is informative, documented).
4. Identity: `sha256(W)` must equal the last ledger entry's `after_sha` and that entry must be `confirmed: true` -> else `SHA_MISMATCH` (both shas in the line) or `UNCONFIRMED_PREVIOUS`. Size and mtime logged.
5. Inputs: `PIPELINE.sha256` verified; `--db` assembled by `sheet_task.py --db-dir D --db O/db.json --check-only` (exit 3 handled per section 1); release items needing fetch -> `NEEDS_FETCH`; `--copies-needed` shards present; `--release-candidates` files present in `LIB` (missing ones go to `review.release_candidates_missing`, not a refusal: sheet_task marks them untestable).
6. Copy `W` -> `O/in.xlsx` (sha re-checked after copy), `--copies` -> `O/copies/`, `--pipeline` -> `O/pipeline/` (read-only inputs are never written).
7. Apply: the prompt's step 3 commands against `O/`. Exit 2 in either pass -> `VERIFY_FAILED`.
8. Independent diff (section 6): `O/in.xlsx` vs the `--after-relmatch` output. Any disallowed change -> `OVERWRITE`; count mismatch -> `ROWCOUNT`; foreign Article ID -> `FOREIGN_ROW`.
9. Compose `preview.json`, `diff.tsv`, `writeback.json` (not yet applicable), `token`. **preview exits here.**
10. Token check (if `--token`).
11. Backup: `shutil.copy2(W, B / backup_name)`; `sha256(backup) == before_sha` else `BACKUP_FAILED` (the copy is left in place, named as a backup, harmless).
12. Commit: copy the output to `W.parent / out_name` (unique, never `W.name`; incident 2026-10-29), sha it, `os.replace(tmp, W)`; re-read `sha256(W)` == `after_sha` else `COMMIT_FAILED` (the backup is the recovery; the line names it). Then pages add-only, then removals. A failure in pages/removals after the workbook replace is reported as `written: true` with `library_partial: true` and the list of what did not land; the workbook is not rolled back (rolling back would be a second overwrite).
13. Ledger append (section 5), `S/logs/save-<run>-<at>.log`, `lookup_cache.out.json` kept in `O/` for the adapter to publish (the saver does not overwrite `--pipeline`'s cache).
14. Rebuild into `O/site/` unless `--no-rebuild`. Release the lock (move to `S/logs/lock.<run>.<at>`, never delete).

## 4. Locks

- Process lock: `S/saver.lock`, `O_EXCL`, 30-minute staleness, moved not deleted (rule 3 of the prompt; BUILD_NOTES 4.10).
- Library lock for cross-session visibility: the prompt's `LIB/.sheet_task.lock` (`<run id> <UTC time>`) is also written at step 2 and moved to `LIB/_to_delete/.sheet_task.lock.<run id>` at the end, so a manual session following the old prompt still sees it.
- Limitation to state in the README: two sessions working on two mirrors of the same master do not see each other's locks. The ledger sha (section 5) plus the adapter's compare-and-swap on return (section 8) is what prevents a lost update there.

## 5. Checksum ledger and names

`S/ledger.jsonl`, append-only, one JSON object per line:

```json
{"at": "2026-10-30T22:31:04Z", "verb": "save", "run": "run-mvvcnrpbuuz",
 "before_sha": "e52815d5…", "after_sha": "bc21c9fb…", "backup": "AJG Coverage - NewsBank BACKUP before run run-mvvcnrpbuuz 2026-10-30 1531.xlsx",
 "out_name": "AJG Coverage - NewsBank SAVED run-mvvcnrpbuuz 20261030T223104Z.xlsx",
 "rows_before": 8177, "rows_after": 8193, "rows_added": 16, "cells_filled": 73, "confirmed": false, "confirmed_at": null}
```

- `init` writes the first line (`verb: "init"`, `after_sha` = the sha given, `confirmed: true`). Seed: the DECISIONS line of the last rule-7 write (today e52815d5… per REVIEW4-DATA-v1, or whatever the adapter reads from the master at migration).
- `confirm --sha X` appends `{"verb": "confirm", "after_sha": X, "confirmed": true}` only if X equals the last unconfirmed entry's `after_sha`; otherwise exit 2 with both shas (the adapter pushed the wrong file).
- The "last recorded sha" is the `after_sha` of the last line whose verb is `init`, `save` or `confirm`.
- The ledger lives with the master (`W.parent/.saver/` by default) so a foreign edit is caught wherever the master moves. If the store cannot hold dot-folders (an artifact), the adapter passes `--state` and is responsible for round-tripping it with the workbook.

Names (all `W.stem`-based, so a renamed master keeps working):
- backup: `<stem> BACKUP before run <run id> <YYYY-MM-DD HHMM local>.xlsx` (the DECISIONS convention; the prompt's `<stem> <mtime>.xlsx` is dropped: not unique across sync tools and not human-readable);
- output: `<stem> SAVED <run id> <UTC compact>.xlsx` in `O/` and, briefly, beside `W` as the replace source;
- never `W.name` for any intermediate file.

## 6. Independent diff and allow-list

Done by the saver with `openpyxl` (`read_only=True`, values only, plus a hyperlink count per sheet from a second non-read-only pass or `_vt_hyperlinks`-style zip inspection). It is **in addition to** `sheet_task.verify` / `verify_tabs`, not a replacement; both must pass. Reference implementation of the shape: `scratchpad/runsave/fastdiff.py` (values, `added | filled | changed`).

`O/diff.tsv` columns: `sheet, row, key, column, kind, old, new, allowed_by`. `key` = Article ID (Coverage, Originals, Audio & video details, Removed, Unlinked print pages), Release ID or URL (Press releases), first four columns (Bills).

Allowed `changed` cells (a non-blank value that differs), each tagged in `allowed_by`:

| Tag | Where | Source |
|---|---|---|
| `reprint_count` | Coverage and Originals, column "# of reprints", rows whose Story ID is in `result.reprint_counts` | prompt rule 2 |
| `origin_swap` | cells in `result.origin_swaps[].cells` | REPRINT-v2 |
| `retry_cleared` | `File name`, `Saved Copy?` of `result.retry_cleared[].aid` | AUDIT F5 |
| `queue_applied` | cells in `result.queue_applied[].cells` | QUEUEAPPLY-v1 |
| `removed_move` | a Coverage / A&V row missing after, whose aid is in `result.removed[].rows[].aid`, and present on Removed | BUTTONOPT-v1 |
| `rel_derived` | Press releases columns in `sheet_task.VT_DERIVED_REL` (Has copies, Copies (rows), First copy date (if different), Related count, Related story IDs, In tracker, …: import the constant, do not copy the list) | RELTAB / RELBUTTON-v1 (the real save of 2026-10-30 changed 10 such cells; the prompt's rule 2 omits them) |
| `originals_mirror` | the Originals tab as a whole: it is rebuilt from Coverage; its rows are compared by Article ID with the same rules as Coverage | HANDOFF 6.1 step 5 |

Anything else -> `OVERWRITE`, first 20 cells in the line, all in `diff.tsv`. `filled` (blank -> value) is always allowed; `added` rows are allowed on Coverage, Originals and `VT_NEW_OK` tabs only.

Count rules (`ROWCOUNT`): `rows_after == rows_before + rows_added - len(removed aids)` on Coverage, using `result.verify` numbers and the saver's own count (both); `result2.verify.rows_after == result.verify.rows_after`; Originals row count == Coverage rows with "Original"; no sheet lost or reordered; header rows identical; hyperlink count per sheet not lower.

Foreign rows (`FOREIGN_ROW`): the set of Article IDs on Coverage after minus before must be a subset of the IDs sheet_task assigned this run: values of `result.runs[*].ids` that match `^\d{5}$`, plus aids in `result.origin_added[]`, `result.origin_nocopy[]`, `result.nocopy_finds[]`, `result.agg_origin[]`, `result.releases_*` rows (collect every `aid` key under those lists). The builder confirms the exact key set against the three replay fixtures and records it in a constant with a comment; an ID that appears nowhere in `result.json` is a refusal, not a warning.

Preview token: `sha256(run_id + before_sha + sha256(diff.tsv))[:16]`, written to `preview.json`, valid 30 minutes (checked from `preview.json`'s `at`).

## 7. Result JSON

`O/saver_result.json` (also last stdout line), same shape for preview and save:

```json
{"verb": "save", "ok": true, "run": "run-mvvcnrpbuuz", "at": "…Z", "today": "2026-10-30",
 "written": true, "confirmed": false, "line": "16 rows added, 73 cells filled, …",
 "refusal": null,
 "workbook": {"path": "…", "before_sha": "…", "after_sha": "…", "backup": "…", "out_name": "…", "size_before": 6854113, "size_after": 6864976},
 "diff": {"rows_added": {"Coverage": 16, "Originals": 9, "Audio & video details": 4, "Press releases": 0},
          "cells_filled": {"Coverage": 432, "Originals": 269, "Audio & video details": 28, "Press releases": 3},
          "cells_changed": {"reprint_count": 8, "rel_derived": 10}, "tabs_touched": ["Coverage", "Originals", "Audio & video details", "Press releases"],
          "tsv": "O/diff.tsv", "token": "…"},
 "verify": {"pass1": {…result.verify…}, "pass2": {…result2.verify…}},
 "library": {"pages_added": ["2026/ws10650o-s04929.html", …], "pages_collided": [], "removed_moved": [], "partial": false},
 "judgment": {…section 7.3…},
 "review": {…prompt step 5 lists, first 50 each, only non-empty…},
 "writeback": "O/writeback.json",
 "publish": {"index_html": "O/site/index.html", "copies_changed": [...], "sheet_json": "O/site/data/sheet.json",
             "pipeline_files": {"lookup_cache.json": {"path": "O/lookup_cache.out.json", "sha": "…", "changed": true}, "outlets.json": {"changed": false}, …}},
 "fetch_plan": {"fetch": [], "answered": {}}, "lookups_new": 5,
 "site_rebuilt": true, "log": "S/logs/save-run-mvvcnrpbuuz-….log", "exit_code": 0}
```

### 7.1 Refusal

`refusal: {"code": "SHA_MISMATCH", "line": "Not written: the workbook changed since the last save (expected e52815d5…, found 1a2b3c4d…). …", "detail": {…}}`. Codes: `NO_LEDGER`, `UNCONFIRMED_PREVIOUS`, `SHA_MISMATCH`, `EXCEL_OPEN`, `LOCKED`, `INPUT_MISSING`, `PIPELINE_MISMATCH`, `NEEDS_FETCH`, `VERIFY_FAILED`, `OVERWRITE`, `ROWCOUNT`, `FOREIGN_ROW`, `TOKEN_STALE`, `BACKUP_FAILED`, `COMMIT_FAILED`, `BAD_ARGS`. The `line` always starts "Not written: " and is the text the adapter writes to the run doc's `sheet.line` (REQ-9 keeps the run queued). Lines for the three the prompt already words (Excel open, lock, verify) reuse the prompt's wording.

### 7.2 Writeback bundle `O/writeback.json`

Exactly the documents prompt step 5 writes, composed by the saver, applied by the adapter after confirmation:

```json
{"apply_after_confirm": true,
 "runs": {"run-…": {"ids": {…}, "sheet": {"at": "…", "written": true, "line": "…", "stories": [...], "translations": [], "bills": [], "newbills": [...]},
                    "review": {…lists…}}},
 "edits_delete_or_archive": [...ids...], "edits_reported": {"<id>": "<at>"},
 "reprints_aid": {"<doc id>": "10657"},
 "pages_delete_or_archive": [...ids from result.pages/.pages_error/.pages_skipped (.page) and .pages_drop...],
 "queue_applied": {"<id>": {"at", "run", "choice", "done"}}, "queue_items": {…result2.queue_docs…},
 "on_refusal": {"runs": {"run-…": {"sheet": {"at": "…", "written": false, "line": "Not written: …"}}}}}
```

On refusal only `on_refusal` is filled. The saver never writes `written: true` anywhere itself.

### 7.3 Judgment items (never guessed)

`judgment` carries, each as a list of small dicts with `run`, ids, link and the `why` sheet_task gave: `needs_fetch` (releases without html), `origin_wanted` (CHAINORIG-v1), `name_collision` (page file already in the library), `conflicts`, `date_review`, `av_date_review`, `reprint_untested`, `reprint_check`, `outlet_unresolved`, `outlet_new`, `outlet_untyped`, `gabriel_unclear`, `unknown_story`, `held`, `print_pages` (REQ-11), `backfill_finds` (REQ-13), `queue_conflicts`, `release_candidates_missing`, `fetch_plan.fetch`, `nocopy_rows_without_copy` (blog-like rows sheet_task lists under NOBLOGS, for Sammy to decide). Claude reads this list and acts (fetch, ask Sammy, add a find through the tracker); the saver's job ends at listing.

## 8. Adapter interface

An adapter is anything that produces the input folders and returns the outputs. Contract:

**In (before `saver.py`):** `W` (bytes identical to the store's current master; adapter records the store's own version marker: Mac `mtimeMs`, git commit, artifact `base_version`), `D` and `Q` (one JSON per doc, ArtifactData `list` layout), `P` with `PIPELINE.sha256`, `C` (shards named by `--copies-needed`; the adapter may call `saver.py preview` once to learn them, or run `sheet_task.py --copies-needed` itself), `LIB` (for a remote library: only the release-candidate files and the target folders need to exist locally; pages are add-only so a partial mirror is fine, but then the collision check is only as good as the mirror), `B`, empty `O`, `S` (with the ledger that travelled with the master).

**Out (after exit 0 / 5 / 6):** push `W` back under the store's compare-and-swap (`expectedMtimeMs`, git fast-forward only, artifact `base_version`); on rejection the store moved: do not retry blindly; re-fetch and re-run from the start (the ledger will then refuse with `SHA_MISMATCH` unless the foreign change is accepted with `init`). Verify the store's sha equals `workbook.after_sha`, then `saver.py confirm --sha`. Push `B/<backup>` (verify sha = `before_sha`), `library.pages_added` (add-only at the store too), `library.removed_moved` (moves), the `S` folder, `publish.*`, and apply `writeback.json` (`written: true` only after confirm). Everything checked by sha256 both ways; the adapter's own log lists path, bytes, sha for each transfer.

Not an adapter concern: any data rule, any retry that changes content, any delete.

## 9. Tests

All under `L/work/saver/tests/`, `python3 -I -m pytest` or plain scripts in the `run_all.sh` style; fixtures copied, never pointing into `L/work` live files.

Unit (synthetic 3-tab workbook + `build/tests/sheet_task/fixtures/example_db.json`): happy path (ledger chain, backup sha, diff allowed, lock moved); `~$` present; file held open `r+b` by the test (Windows semantics simulated with a flag on Linux); `SHA_MISMATCH`; `UNCONFIRMED_PREVIOUS` then `confirm`; `NO_LEDGER`; exit 3 with and without `--refresh`; `VERIFY_FAILED` (feed a tampered output via a stub `sheet_task.py` on `PYTHONPATH`? no: run the real one against a workbook pre-edited so verify fails); `OVERWRITE` (inject a changed cell into the pass-2 output with openpyxl before the diff step via a test hook `SAVER_TEST_TAMPER`); `ROWCOUNT`; `FOREIGN_ROW`; stale token; two concurrent invocations; page name collision; removal move with `_moves_` log; `--today` in the future refused; `PIPELINE_MISMATCH`; `O` not empty refused; `--copies` shard missing.

**Replay harness** (`tests/replay.py`): for each past save folder, build the inputs from what it already contains and require the saver's `--after-relmatch` output to match the hand-made result **cell for cell** (values, by sheet / row / column; sheet order; header rows), allowing only documented timestamp fields:

| Fixture | Inputs present | Expected output | Notes |
|---|---|---|---|
| `scratchpad/runsave/` | `in.xlsx`, `db/`, `queue/`, `pipeline/`, `copies/`, `pages/`, `result.json`, `result2.json`, `--today 2026-10-30` (from `result.at`) | `AJG Coverage - NewsBank STAGED run-mvvcnrpbuuz save 2026-10-30.xlsx` | The real save. `base1.xlsx` / `base_result.json` are an earlier pass of the same run; not a target. Expected diff vs `in.xlsx`: 750 lines, 18 `changed` all allowed (`work/out/runsave_changes_2026-10-30.csv`). |
| `scratchpad/coldstart/rehearsal/` | `in.xlsx`, `db.json`, `copies/`, `pages/`, `result.json`, `result2.json`, pipeline = `cp/` | `out2.xlsx` (and `out1.xlsx` for pass 1) | Cold-start rehearsal; `out1p.xlsx` / `resultp.json` are a variant pass, check their flags in `ps.json` before using. |
| `L/work/tmp_agent-buttonopt/dry/` | `in.xlsx`, `db.json`..`db3b.json`, `pages/`, `pipe/`, `result*.json` | `out.xlsx`, `out2.xlsx`, `out3.xlsx` | Older pipeline version: run with its own `pipe/`, expect pass-1 equality only; mark as `xfail` if the then-current `sheet_task.py` is not in `pipe/`. |

The fixtures have no `PIPELINE.sha256`; the harness generates one over the fixture's own pipeline folder (`tools/pipeline_sha.py`) and seeds a ledger with `init --sha sha256(in.xlsx)` into a temp `--state` before each replay.

Timestamp fields excluded from the equality: none in cells (sheet_task writes `--today`, not a clock); `result.at` / `result2.at`; `docProps/core.xml` inside the xlsx (never compare bytes or shas of workbooks, only cells). Photos: run replays with `--img-cache` pointing at the fixture's `img_cache/` so no download happens; if a replay would need the network, the harness fails with a clear message rather than fetching.

Also run `L/build/tests/run_all.sh` unchanged before and after: the saver must not change its results (it imports nothing from the saver).

## 10. Files to create (all under `L/work/saver/`)

| File | Purpose | Est. hours |
|---|---|---|
| `saver.py` | CLI, state machine (section 3), locks, ledger, backup/commit, writeback bundle, result JSON | 6 |
| `saver_diff.py` | openpyxl diff, allow-list, counts, foreign-row check, `diff.tsv`, token | 3 |
| `saver_steps.py` | the subprocess calls of prompt step 3 and 6 with their exact flags; pipeline sha check | 2 |
| `tests/test_saver.py`, `tests/fixtures/` | unit cases above | 4 |
| `tests/replay.py` | replay harness over the three fixtures | 3 |
| `README.md` | one page: arguments, exit codes, adapter contract pointer, limitations (locks across mirrors, Linux Excel detection) | 1 |
| `PIPELINE.sha256` generator (`tools/pipeline_sha.py`) | writes the file from a pipeline folder; the adapter ships it | 0.5 |

About 20 agent hours (Sonnet), plus a Fable review pass of `saver.py` and `saver_diff.py` line by line before the first supervised save (BUILD_NOTES phase 3 plan stands).

## 11. Open points for the builder to report, not decide

- Whether `sheet_task.py` writes any cell from a clock other than `--today` (grep found none; confirm on the replays).
- The exact set of `result.json` keys that can introduce a new Article ID (section 6, `FOREIGN_ROW`).
- Whether `img_embed.py` can be told to use the cache only (`--img-cache` with no network) so replays and offline saves are deterministic; if not, document that photos of new saves may be missing offline and that the workbook is unaffected.
- `--queue` absent but the db has decided items: the saver passes no `--queue`, so sheet_task applies nothing; confirm `result.queue_applied` is then empty and say so in the result.
