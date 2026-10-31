# agent-f11 — move F10 files to their row's Year folder (2026-10-27)

Lightweight fix. Nothing deleted, no workbook change (File name cells have no folder).

Years read from work/coverage_current.xlsx (Coverage, col Year). Preflight: all 14 sources present in 2026/, no targets existed.

| Article | File | Old folder | New folder |
|---|---|---|---|
| 06955 | ws06955r-s00330.html | 2026 | 2025 |
| 06957 | ws06957r-s00331.html | 2026 | 2025 |
| 06958 | ws06958r-s00582.html | 2026 | 2024 |
| 06963 | ws06963r-s00611.html | 2026 | 2024 |
| 06965 | ws06965r-s00263.html | 2026 | 2025 |
| 06966 | ws06966r-s00787.html | 2026 | 2023 |
| 06967 | ws06967r-s00290.html | 2026 | 2025 |

Unchanged (folder already matches Year): 07114 (2026), 07586 (2025).

Each move done in both `Tracker library/` and `_original_html/` with `mv -n`; all target folders already existed. Logged as op `7,move` (14 lines) in `Tracker library/_rename_log_2026-10-27.csv` with post-move sha256 (log now 10,964 lines).
