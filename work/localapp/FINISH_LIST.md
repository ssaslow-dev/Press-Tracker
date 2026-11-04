# Finish list: every loose end until the project is done (FINISH-v1)

One list for everything left. Claude keeps it current after every step and reports from it. "Sammy" = needs you; "Claude" = done for you. Nothing counts as done until it is ticked here.

## A. Windows switch-over

| # | Item | Who | Status |
|---|---|---|---|
| A1 | Fable review of the code that writes the workbook and library (work/saver/REVIEW_3.md) | Claude | done 2026-11-04 (7 findings) |
| A2 | Fix its findings, rerun every test and the end-to-end check, rebuild the zip, resend | Claude | done 2026-11-04 (7 findings fixed, all suites and chain check green, zip rebuilt: sha256 e2fa191a) |
| A3 | Send IT the updated note (work/localapp/IT_NOTE_APP.md, with the new zip's fingerprint) | Sammy | after the final zip (B3) |
| A4 | Dress rehearsal on the office PC with yesterday's copy (setup + Switch-over changes screen, on a spare folder) | Sammy | skipped: the real run doubles as it (PC copy only) |
| A5 | Switch-over day (PLAN.md checklist): Mac fingerprint list, copy, unzip, keeper role, Set up from the Mac library, Switch-over changes screen | Sammy + Claude | in progress: setup done (12,682 files checked), Switch-over changes applying |
| A6 | Decide 01920 and 03486 | Sammy | done: 01920 remove (after switch-over, A13); 03486 author fixed via 06_author_03486.csv on the screen |
| A13 | Move 01920 to the Removed tab through a save | Claude + Sammy | after A5 |
| A7 | Move the Update station to the office claude.ai account (station/MOVE_TO_OFFICE.md) | Sammy + Claude | on the day |
| A8 | First real Update run with Claude and TinyFish: station -> update folder -> Bring in update -> Save | Sammy | on the day |
| A9 | Refresh files for each colleague | Sammy | on the day |
| A10 | Old tracker: stop Update and saves (kept read-only) | Sammy | on the day |
| A11 | 431 stories have a saved copy in the library that the shipped article data lacks (seen at setup 2026-11-04): build the article data from the keeper's own library on the PC so every saved copy opens | Claude | to do (not blocking) |
| A12 | Switch-over screen wording: the fixes step says "Blanks only" although approved overwrites (pages, cleared authors, Edition) are included | Claude | with D1 |
| A14 | Switch-over apply on the office PC stopped with PermissionError(13, 'Access is denied') before any step finished (2026-11-04); the error message must name the file and step (station_cli catch-all drops e.filename) | Claude | diagnosing with Sammy |

## B. Mac version (MACAPP-v1)

| # | Item | Who | Status |
|---|---|---|---|
| B1 | Mac starts: unzip, self-check, Open Anyway, Safari | Sammy | done 2026-11-04 |
| B2 | Test kit (small data copy) and checklist part 2; Mac fixes prepared (accented names, hidden files, Safari unzip message, wording) | Claude | done 2026-11-04 |
| B3 | Mac fixes put into the shared code, then the final Windows and Mac zips | Claude | done 2026-11-04: fixes a-d in the shared code; both final zips built (Windows sha256 e7655931, Mac sha256 2cabb2d5) |
| B4 | Data test on the Mac with the kit (setup, View original, for-Update file, refresh file) | Sammy | done 2026-11-04: everything works |
| B4b | Mac upload tests: bring in the test update zip and Save; load the for-Update file into the station | Sammy | ready now |
| B5 | Mac and Windows swap a refresh file both ways | Sammy | with A4 (office PC rehearsal) |
| B6 | Final Mac zip from the finished code | Claude | built, pending Sammy's B4/B5 tests (AJG_Tracker_mac_final.zip, 165.5 MB, sha256 2cabb2d54954e2f1d29ccd5b7eb12a7e2a2bff423646182b0caad16450a81bbc) |

## C. Read-only HTML preview

| # | Item | Who | Status |
|---|---|---|---|
| C1 | Build the preview file and check it against the tracker | Claude | done 2026-11-04 (Chromium checked; Safari/Firefox by Sammy) |
| C2 | Decide who gets it (if colleagues: version without tone ratings and notes) | Sammy | done 2026-11-04: keep tone ratings (the version already sent) |

## D. After switch-over

| # | Item | Who | Status |
|---|---|---|---|
| D1 | Small update removing the one-time Switch-over screen's code (its "Add a fixes file" wording also misled: the approved fixes are built in) | Claude | after A5 |
| D2 | Repo snapshot in data/ replaced by (or retired for) the switched-over data, per SWITCHOVER-v1 | Claude | after A5 |
| D3 | Last cleanup: outdated code and decisions archived, CLAUDE.md and handoff brought up to date for any future Claude | Claude | last |

## E. Open decisions for Sammy (none block the switch-over)

- E1 Online read-only copy for colleagues (the preview, C, may cover this).
- E2 ~585 Page cells hold NewsBank scan positions instead of printed page numbers; ~250 can't be checked automatically.
- E3 Common Sense Media's two posts are kept as coverage; revisit only if organisation advocacy blogs should be excluded.
- E4 Older items carried from the old tracker (CLAUDE.md "Open decisions"): A5 wire-blend pickups; 4 F7 rows (09721, 01734, 06948, 06949); 8 medium-confidence date fixes; 4 thin saved copies; Patch rows 00740 and 04889; Korea Daily Times; the 7 NOBLOGS rows; the Independent story's date; blank Tone/Topic on Newsroom America and Organiser.
