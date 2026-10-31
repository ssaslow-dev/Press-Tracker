# agent-libadds2 — library add-only commit, tlib_rated2 batch (2026-10-27)

Scope: 41 rows in work/library_adds_pending.csv with staged_path under /mnt/user-data/outputs/tlib_rated2/.
Skipped by instruction: nb-00573, nb-03826 (settled: keep existing Mac copies; left in pending). No tlib_rated1 rows present.
Pre-checks: all 41 staged files present, container sha256 == CSV, device_path == Tracker library/<year>/<aid>.html.
Mac reachable; `test -e` on all 41 targets: none existed; year folders 2017-2026 already present.

## Committed + verified: 41
device_commit_files, 2 calls (25/16), no force, 0 rejected. Mac sha256 matched CSV for all 41
(Mac hashes: work/libadds2_mac_sha.txt; list: work/libadds2_verified.txt).
Rows moved to work/library_adds.csv (140 -> 181 lines). Pending re-read at rewrite, written atomically: 44 -> 3 lines (header + nb-00573, nb-03826).
Backups: scratchpad/pending_backup_libadds2.csv, scratchpad/adds_backup_libadds2.csv.

## Skipped (exists): 0
## Failed: 0
Nothing else on the Mac touched (only reads: ls, test -e, sha256).
