# agent-reprint-fills — same-outlet fills for Tracker reprint-list rows (2026-10-27)

No web, no Mac, no artifact/db, workbook not written. Input: work/coverage_current.xlsx (sha256 bad96577…, unchanged after run).

## What I found in the stopped agent's work
- Its derive.py had a NaN bug: a missing city became pandas NaN (truthy), so generic-name outlets with no city were never skipped *and* never matched. Net effect was missed fills (73 instead of 238), not wrong ones. Its 73 fills are all a subset of the new output.
- It also mapped "Collegian: CSU-Fresno" as a variant (not on the Reprint info tab) and missed "País, El" = "El País". Both fixed.
- derive.py rewritten (work/tmp_reprint_fills/derive.py). Old outputs kept as work/tmp_reprint_fills/old_*.csv.

## Matching used
Exact name; NewsBank style vs plain (", The" / ", El"), case, "Today's Edition", ": Blogs"; the Reprint info tab variants (SLO Tribune = Tribune, The [San Luis Obispo]; Excelsior; Lassen; reason.com; KPCC; Independent/Times London; El País editions; The Week editions; Daily Herald DuPage; NW Arkansas Democrat-Gazette; Collegian Delta; CNN Wire; all AP feeds; all TNS feeds; Politico Pro/Playbook). Generic = every word a stock newspaper word (Times, Herald, Daily News, Press-Enterprise...); these need a city match; target with no city -> skipped. "Press Democrat", "Mercury News" and "Week" treated as specific mastheads.

## Results (work/out/reprint_fills.csv, work/out/reprint_fill_conflicts.csv)
- 1,076 targets: 87 have no blanks; 118 have no other same-outlet row; 44 skipped (generic name, no city).
- 238 fills on 109 rows: Outlet city 62, county 3, state 3, Medium 41, Language 88, Publisher 41. 165 of them are San Luis Obispo Tribune rows (41 rows x 4 cols) via the tab's SLO Tribune = Tribune, The rule.
- 209 conflicts on 206 rows / 25 outlets: Language 201 (multi-language outlets, e.g. Yahoo News 113, Press Democrat 18, CalMatters 15, Daily Breeze 11, SD Union-Tribune 11), Medium 5, city/county/state 1 each (Associated Press).

## Self-check
- work/tmp_reprint_fills/selfcheck.py (openpyxl, separate hand-written matcher): 20 random fills 20/20 OK; also run on all 238: 238/238 OK. Every fill/conflict target is a Tracker reprint-list row with a blank cell; no duplicate (aid, column).
- code/apply_fills.py: new commented block "Tracker reprint-list rows" (blanks only, green, hold-aware, rejects non-reprint-list rows). Dry run on a copy -> build/fills_dryrun2.xlsx + build/fills_dryrun2_report.json: reprint block wrote 238 (same per-column counts), skipped_nonblank 0, held 0; Coverage_existing_changed 0, Originals_existing_changed 0. All 238 cells verified equal to the CSV value and green; none of those Article IDs is on Originals.

## For Sammy / coordinator (not decided here)
- Skipped by the generic rule but possibly fillable by hand: "Independent, The" (6 rows; tab says The Independent = London, but the sheet also has a Massillon Independent), "Daily News" (7; LA vs Palo Alto), "Daily Republic" (2; Fairfield/Solano), "Business Journal, The" (4; Fresno only on sheet), "Observer, The" (2), "Daily Journal" (3), "Collegian, The" (1).
- Language conflicts mostly reflect mislabeled languages on single rows (e.g. Daily Breeze 1 Portuguese, Press Democrat 1 Spanish, Nguoi-Viet "Portuguese") — belongs in the language review already queued.
