# F3 — commit the final workbook to Sammy's Mac
File to commit: L/final_pass/F1/final.xlsx, sha256 MUST be a6f547167cb5cf0f415504d09209260e221667cf5d68b4e340b8b4b918e35488 (check first).
1. Mac reachable; F2 finished and verified (L/final_pass/F2/F2_report.md says 0 missing / 0 unexpected / 0 mismatches) — else STOP.
2. No Excel lock file `~$AJG Coverage - NewsBank.xlsx` in Documents/Gabriel press PDFs — else STOP and report "Sammy needs to close Excel".
3. Stage the current Mac workbook; its sha256 must equal e1c70819c0d463aa302c096f6a4b17ce1a2d18390e3bcf5da73033711c3307f1 — else STOP (someone edited it).
4. Back it up into Backups/ as "AJG Coverage - NewsBank BACKUP before final pass 2026-10-27.xlsx" (verify sha).
5. Copy final.xlsx to /mnt/user-data/outputs/<unique name>, commit it over the workbook with device_commit_files using expectedMtimeMs from step 3; verify the sha256 on the Mac equals a6f54716…
6. Copy final.xlsx to L/work/coverage_current.xlsx (keep the old as coverage_pre_final.xlsx). Write L/final_pass/F3/F3_report.md.
