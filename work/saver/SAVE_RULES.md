# Save rules (for Sammy to approve)

One program does "save the last run to the sheet" on files in a folder. Moving them there and back (Mac, PC, GitHub, artifact) is a separate step.

## What a save does, in order

1. Runs every check in the refusal list.
2. Records the workbook's checksum; makes a backup under a unique name.
3. Runs sheet_task.py exactly as today: lookup cache first, no other web use.
4. Compares result and original cell by cell.
5. Writes a new, uniquely named file, checks its checksum, swaps it in for the master. Adds new pages to the library (never over an existing name); moves removed stories' files to `_to_delete/`.
6. Logs old and new checksum, backup name, counts.
7. Rebuilds the page files. Publishing, and marking the run "written", happen outside it once the checksum is confirmed where the master lives.

## When it refuses to write (nothing changes, not even the backup)

- The workbook's checksum is not the last one recorded (an edit, or a sync replaced it).
- The workbook is open in Excel (lock file, or the OS refuses access).
- Another save is running, or started under 30 minutes ago and never finished.
- The last save was never confirmed where the master lives.
- sheet_task.py's own verification fails, in either pass.
- Row counts don't add up: after = before + added − moved to Removed; Originals tab must match.
- A filled cell would change, outside the recorded exceptions ("# of reprints", Removed moves, Original swap, RETRY/BLOCKED row taking its copy, decided review-queue merge, Press releases derived columns). The saver checks this itself.
- A new row's Article ID is not one sheet_task.py assigned in this run.
- A tab, header, hyperlink or key row would go missing.
- The backup's checksum, or the master's after the swap, doesn't match.

On refusal the run stays queued with one line: "Not written: <why>". Master, library and log change together or not at all.

## What preview shows

Everything a save would do, writing nothing: rows added and cells filled per tab, changed cells with the rule allowing each, pages to add, files to move, the summary line, and items needing a person (dates to check, untested reprints, wanted originals, name collisions). It holds 30 minutes while the checksum is unchanged.

## What it never does

- No schedules or background runs (NOSCHED-v1). No logins, paid sources or paywall workarounds (FREEONLY-v1).
- No web beyond the photo downloads sheet_task.py already does, cache first (LEARN-v1).
- No deletes anywhere: moves only. No file under the master's own name except the swap. Never touches `~/Documents` copies, `AJG Combined Coverage.xlsx`, `Jesse_Gabriel_Mentions.xlsx`.
- Never guesses on a judgment item; never adds a YouTube or blog row (NOBLOGS-v1).

## Sammy's answers (2026-10-31, SAVER-RULES-v1)

1. Yes: Claude may save without showing the preview when there are no judgment items and no changed cells beyond the exceptions.
2. Yes: if a checksum mismatch is Sammy's own Excel edit, Claude tells him and accepts the current file as the new baseline.
3. Yes: a page whose file name already exists in the library is skipped and listed.
4. Save everything else: a release still needing a fetch stays queued on its own; the rest of the run is saved, and that release's pickup marks are filled on a later save (fill blanks).
5. Keep only the 3 most recent backups the saver made; it removes older ones it made itself. Backups made before the saver existed (Sammy: "do what you think is best"): after the saver's first confirmed live save, all but the newest 3 of them are moved to `Backups/_to_delete/`, not deleted, so Sammy can empty that folder when he's comfortable.
6. Thirty minutes as the stale-lock age (Sammy: "do what you think is best"; a normal save takes a few minutes).
