# agent-libadds — library add-only commit (2026-10-27)

Scope: rows in work/library_adds_pending.csv not under tlib_rated1/tlib_rated2 (53 rows: 52 tlib_fetch1, 1 tlib_fetch2).
Pre-checks: all 53 staged files present in container, sha256 matched CSV, device_path = Tracker library/<year>/<aid>.html.

## Committed + verified: 51
device_commit_files, 3 calls (25/25/1), no force, 0 rejected. Mac shasum -a 256 matched CSV sha256 for all 51
(Mac hashes saved: work/libadds_mac_sha.txt). Rows moved to work/library_adds.csv (46 -> 97 lines, CRLF kept).

## Skipped (target already exists on Mac) — left in pending, NOT overwritten
- nb-00573 (2025, tlib_fetch2): Mac sha 4b845091... != CSV 7a815eee... (different content on Mac)
- nb-03826 (2019, tlib_fetch1): Mac sha b74c9460... != CSV b3f94840... (different content on Mac)
Needs a decision (keep Mac copy vs replace); no action taken.

## Failed: 0

## Not touched
tlib_rated2 rows (12 at time of rewrite, incl. ones appended during run) left in pending for their own agents.
Pending was re-read at rewrite time and written atomically; backups in scratchpad/pending_backup_libadds.csv and adds_backup_libadds.csv.
Note: a first verify command failed harmlessly (shell variable bug made bash try to exec the .html files -> Permission denied; nothing modified); reran correctly.
