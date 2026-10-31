# saver.py

"Save the last run to the sheet" as one program. Works on local paths only; getting the workbook in and out is a separate adapter. Windows and Linux, Python 3.11+, no installs beyond `openpyxl`. Policy: `SAVE_RULES.md` (wins). Build spec: `SAVER_SPEC.md`.

    python3 -I src/saver.py init    --workbook W --state S --sha SHA [--note TEXT]
    python3 -I src/saver.py confirm --state S --sha SHA [--note TEXT]
    python3 -I src/saver.py preview --workbook W --db D [--queue Q] --pipeline P --copies C --library LIB --backups B --out O [--state S] [options]
    python3 -I src/saver.py save    (same as preview) [--token T] [--master-is-local] [--no-rebuild]

## Arguments

| Argument | Meaning |
|---|---|
| `--workbook W` | The master (or its local mirror). Replaced only by `save`. |
| `--db D` | Database folder (`runs/`, `pages/`, `edits/` ...) or one `db.json`. |
| `--queue Q` | Review-queue folder (`items/`, `decisions/`, `applied/`). Optional. |
| `--pipeline P` | Published pipeline files plus `PIPELINE.sha256` (write it with `tools/pipeline_sha.py`). Never written. |
| `--copies C` | Folder with `articles/manifest.json` and the year shards. Never written. |
| `--library LIB` | Tracker library root. `save` adds pages and moves removed files inside it. |
| `--backups B` | Where the backup goes. |
| `--out O` | Empty working folder for this run. All outputs land here. |
| `--state S` | `ledger.jsonl`, `saver.lock`, `logs/`. Default `W.parent/.saver`. Must travel with the master. |
| `--today`, `--run`, `--refresh`, `--idmap`, `--img-cache`, `--json` | As in spec section 1. |
| `--token T` | Save refuses (`TOKEN_STALE`) unless its own fresh diff gives this token. |
| `--master-is-local` | `W` is the master itself: the ledger entry is confirmed at once. Otherwise run `confirm --sha` after the adapter has put the file where the master lives. |
| `--no-rebuild` | Skip the page rebuild. |

`init` seeds the ledger; it is also how Sammy's own Excel edit is accepted as the new baseline. A save refuses while the last save is unconfirmed.

## What save does

Steps 1 to 9 are the preview (the same code). Then, under the same lock with no gap: token check; backup (`<stem> BACKUP before run <run> <date time LA>.xlsx`, checksum verified, never overwrites); re-check of checksum and Excel; the new workbook copied beside the master under a unique name and swapped in with `os.replace`; checksum verified. Then library pages (add-only; an existing name is skipped and listed), removed stories' files moved to `LIB/_to_delete/<same path>` with a line in `_moves_<date>.tsv` (never overwritten there; a numbered name is used). Then the ledger line, the log (`S/logs/save-<run>-<time>.log`), backup retention, the rebuild. Both locks are moved, never deleted (`S/logs/lock.*`, `LIB/_to_delete/.sheet_task.lock.<run>`).

Token: valid when it matches; there is no clock, because save recomputes the diff itself. The token covers the diff of changed cells, not the workbook's bytes.

Retention: after a successful save, the newest 3 backups the saver made are kept; older ones are moved to `B/_to_delete/`. A backup counts as the saver's only if its name fits the pattern and a save entry in the ledger names it, so hand-made backups are never touched.

Failure after the swap never rolls the workbook back. A library problem sets `library.partial` and lists what did not land (`pages_failed`, `removed_failed`). A swap whose checksum is wrong is `COMMIT_FAILED` with the backup named in the line; do not save again until it is sorted out (the next run would refuse with `SHA_MISMATCH` anyway).

The result's `written: true` means the workbook was replaced. The run documents' `written: true` exists only inside `O/writeback.json`, which the adapter applies after `confirm`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Preview produced, or save written (confirmed or pending). |
| 2 | Refused. Nothing written, except a backup already made. Result has `refusal.code` and a line starting "Not written: ". |
| 3 | Nothing queued and no `--refresh`. Save writes only the "Nothing new to write." writeback. No backup. |
| 4 | Bad arguments or unreadable inputs. |
| 5 | Written and verified; the rebuild failed (`site_rebuilt: false`, `rebuild_error`). |
| 6 | Written; the result file, log or ledger line could not be written. Read the result from the last stdout line. |

Refusal codes: `NO_LEDGER`, `UNCONFIRMED_PREVIOUS`, `SHA_MISMATCH`, `EXCEL_OPEN`, `LOCKED`, `INPUT_MISSING`, `PIPELINE_MISMATCH`, `VERIFY_FAILED`, `OVERWRITE`, `ROWCOUNT`, `FOREIGN_ROW`, `TOKEN_STALE`, `BACKUP_FAILED`, `COMMIT_FAILED`, `BAD_ARGS`.

## Adapter contract

See `SAVER_SPEC.md` section 8. In: the folders above, byte-identical to the store. Out after exit 0, 5 or 6: push the workbook under the store's compare-and-swap, verify its checksum equals `workbook.after_sha`, run `confirm`, push the backup, `library.pages_added`, `library.removed_moved` (each `{aid, from, to}`), the state folder and `publish.*`, then apply `writeback.json`.

## Limitations

- Locks: two sessions on two mirrors of the same master do not see each other's locks. The ledger checksum and the adapter's compare-and-swap catch a lost update.
- Excel detection: the `~$` owner file is checked everywhere; the open-for-write test only means something on Windows. On Linux and macOS a file held open without a `~$` file is not detected. The `~$` name rule assumes a master name of 8+ characters.
- Rebuild (step 14): runs the prompt's step 6 (`tabs_data.py --only releases`, `assemble.py`, `data/sheet.json`) into `O/site/`. It needs `tabs_data.py`, `assemble.py`, `shell.html`, `tracker.js` and `tabs/` in the pipeline folder; the repository's `code/` folder has none of the last three, so the rebuild has been tested only against stub scripts, not a real published pipeline. Without those files it exits 5. Use `--no-rebuild` until it has been run once against the real pipeline.
- Photos of new saves are never downloaded (the pipeline runs with a dead proxy); pages that need a photo not in `--img-cache` are saved without it.
- The replay fixture (`tests/replay.py`, the `SAVER_SLOW` test) holds the workbook and is not in the repository: set `SAVER_FIXTURE=<folder>`. Without it those tests skip.

## Tests

    cd work/saver
    python3 -I -m unittest discover -s tests -t tests            # about a minute
    python3 -I -m unittest discover -s tests/review -t tests/review
