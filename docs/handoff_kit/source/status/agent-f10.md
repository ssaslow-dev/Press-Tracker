# agent-f10 — Pasadena file-name follow-up (2026-10-27)

Lightweight fix. No Exa, no publish, nothing deleted.

## Library renames (Desktop/Tracker library, in place, same year folder; backups in _original_html/ too)
Preflight: all 18 sources present, no targets existed. Logged as op `6,rename` (18 lines) in `Tracker library/_rename_log_2026-10-27.csv` with post-move sha256.

| Article | Folder | Old | New |
|---|---|---|---|
| 06955 | 2026 | ws06955o-s01802.html | ws06955r-s00330.html |
| 06957 | 2026 | ws06957o-s01804.html | ws06957r-s00331.html |
| 06958 | 2026 | ws06958o-s01805.html | ws06958r-s00582.html |
| 06963 | 2026 | ws06963o-s01810.html | ws06963r-s00611.html |
| 06965 | 2026 | ws06965o-s01812.html | ws06965r-s00263.html |
| 06966 | 2026 | ws06966o-s01813.html | ws06966r-s00787.html |
| 06967 | 2026 | ws06967o-s01814.html | ws06967r-s00290.html |
| 07114 | 2026 | ws07114o-s01951.html | ws07114r-s01807.html |
| 07586 | 2025 | ws07586o-s02351.html | ws07586r-s01815.html |

All 9 `_original_html/<year>/` backups renamed the same way.

Note: files stay in their existing year folders; F9 changed some of these rows' Year (dates corrected), so a folder may not match the row's new Year. Not moved (out of scope).

## Workbook
- No lock file (checked before stage and before commit). Staged sha 1bc70516…8775 matched.
- Backup: `Backups/AJG Coverage - NewsBank BACKUP before F10 file-name fix 2026-10-27.xlsx` (cp -p, sha 1bc70516…).
- Edit: direct XML edit of 9 inline-string cells, Coverage G6739, G6741, G6742, G6747, G6749, G6750, G6751, G6898, G7370 (File name). Style s=20 kept (default font). Only xl/worksheets/sheet1.xml changed (43 chars); all other parts byte-identical.
- Originals: none of the 9 are on it (F9 removed them when they became Reprints); its File name columns contain none of the old names. No change.
- Commit with expectedMtimeMs 1793121115156, 0 rejected. Mac sha verified: 069ae1549f6e9ee36860f522581580205a092e3fa948cd45ea70d2042d98f240 (6,254,246 → 6,254,257 bytes).
- work/coverage_current.xlsx = new.
