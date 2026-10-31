# F3: commit final workbook to Sammy's Mac

agent-final-F3, 2026-10-27. All checks passed; nothing deleted, nothing published.

| Step | Result |
|---|---|
| final.xlsx sha256 | a6f547167cb5cf0f415504d09209260e221667cf5d68b4e340b8b4b918e35488 (matches spec) |
| 1. Mac reachable, F2 verified | yes; F2_report: 0 missing / 0 unexpected / 0 sha mismatches |
| 2. Excel lock file `~$AJG Coverage - NewsBank.xlsx` | none |
| 3. Mac workbook before commit | sha e1c70819c0d463aa302c096f6a4b17ce1a2d18390e3bcf5da73033711c3307f1 (matches), mtimeMs 1793077770015, 4,002,627 bytes |
| 4. Backup | `Backups/AJG Coverage - NewsBank BACKUP before final pass 2026-10-27.xlsx` (cp -p on Mac), sha e1c70819… verified |
| 5. Commit | staged as /mnt/user-data/outputs/AJG Coverage - NewsBank FINAL F3 2026-10-27.xlsx; device_commit_files with expectedMtimeMs 1793077770015 → written, 0 rejected; Mac sha a6f547167cb5cf0f… verified, 4,360,653 bytes |
| 6. Local copies | work/coverage_pre_final.xlsx (old, e1c70819…); work/coverage_current.xlsx = final.xlsx (a6f54716…) |
