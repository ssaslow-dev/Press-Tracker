# Finish list: every loose end until the project is done (FINISH-v1)

One list for everything left. Claude keeps it current after every step and reports from it. "Sammy" = needs you; "Claude" = done for you. Nothing counts as done until it is ticked here. Updated 2026-11-04 (afternoon).

## A. Windows switch-over (today)

| # | Item | Who | Status |
|---|---|---|---|
| A1 | Fable review of the code that writes the workbook and library (work/saver/REVIEW_3.md) | Claude | done (7 findings) |
| A2 | Fix its findings, test, rebuild the zip | Claude | done |
| A5a | Library copied to the PC in one piece; Set up from the Mac library (12,682 files checked) | Sammy | done |
| A6 | Decide 01920 and 03486 | Sammy | done: 01920 removed later (A13); 03486 author fixed by 06_author_03486.csv |
| A5b | Switch-over changes, one step at a time | Sammy | done 2026-11-04: all steps applied |
| A5c | Check the result (purple rows, renamed copies open, 03486 author, View original), then press Finished | Sammy | after A5b |
| A10 | Old tracker: no more Update runs or saves; Mac library kept as a frozen backup | Sammy | from now on |

## N. New version (version 2, both zips): fixes found during the switch-over

| # | Item | Who | Status |
|---|---|---|---|
| N1 | Windows file locks (A14/A15): one shared "wait and try again" for every rename/replace (saves, refresh, library, state), a test that simulates a busy file; the rename step's one-file fix already sent and working | Claude | done (2026-11-04: WINLOCK-v1; fs_retry used everywhere, busy-file tests) |
| N2 | One-file updates take effect (no unchecked precompiled copies of the app code) | Claude | done (app code ships with no .pyc; start time +0.1 s) |
| N3 | The 431 saved copies the tracker can't open yet (A11): article data built from your own library, at setup, under Repairs, and kept current by every save | Claude | done (ARTICLEDATA-v1; setup, every save, Repairs button) |
| N4 | Safe "install a new version" that replaces only the program parts, never data\ (A16, DATAINFOLDER-v1), Windows and Mac | Claude | done (PROGRAMUPDATE-v1; Install update.cmd / .command) |
| N5 | All tests and the end-to-end check; new Windows and Mac zips; IT note fingerprint | Claude | done 2026-11-05: zips AJG_Tracker_windows_v2.zip (ff15b1c9) and AJG_Tracker_mac_v2.zip (39044564); chain check has one open station-side failure, see report |
| N6 | Install the new version over the switched-over tracker (data stays) | Sammy | done 2026-11-05: version 4 installed by hand (installer blocked by Windows twice): fresh v4 folder `Desktop\AJG_v4\AJG Tracker` with a copy of the old data\; the old folder `AJG_Tracker_windows_final2` is kept as a backup, not used |
| N7 | Station: check finds against each other within one session (web Update, NewsBank box, ProQuest box) so a story found by two sources is shown once; today only the PC save drops the second copy (listed under duplicates) | Claude | done: station published 2026-11-05 (1793839000-d88b) |
| N12 | PRINTNEW-v1: the station reads full newspaper pages with Claude (they are pictures with no text), adds it automatically as the matching story's print edition or as a NEW story (no per-page confirmation; unclear pages go to Unlinked print pages), and the PC save tests the read text | Claude ; PC part also saves a print-only story's read text as its saved copy (HTML) with the page as its print original, and builds article data from it | station part published 2026-11-04 (v14); PC part done in version 3 (2026-11-05): a print-only new story's read text is its saved copy (HTML), the page scan is its print original, attached and jump pages go to their record's row, article data picks it up, the text test reads only that article's text |
| N13 | Skip to his name on print pages | - | dropped 2026-11-04 (Sammy) |
| N14 | Station: "Add print pages" for any newspaper page (e-edition PDF, scan, photo): Claude reads masthead, date, page and the Gabriel articles; same flow as NewsBank pages; unclear pages listed, never guessed | Claude | done: station published 2026-11-05 (1793839000-d88b) |
| N15 | Fable review of the new 85-page NewsBank batch (NEWSBANK_AUDIT_13) and its fixes; one station republish with N7, N14 and N15 | Claude | done: station published 2026-11-05 (1793839000-d88b) |
| N16 | PC: a later, complete update folder whose earlier part was already saved is refused today (ALREADY_SAVED; person must rerun). Make the PC take the runs it has not saved yet and skip the saved ones | Claude | done in version 3 (2026-11-05): the saved runs are listed as left out in the preview; the fingerprint warning is dropped only when the ledger shows the earlier part of this same folder changed the workbook |
| N17 | PC outlet_rules alias: "Daily News of Los Angeles" = "Los Angeles Daily News" (station already maps it) | Claude | done in version 3 (2026-11-05) |
| N18 | PRINTREAD-v2 follow-up (Fable review fix 3): the PC's reprint test uses the OCR-tolerant verdict for rows whose text Claude read from a newspaper page, so a few misread words do not turn true print editions or reprints into wrong Originals (PC patch 30; test_printread_ocr.py) | Claude | done in version 4 (2026-11-05) |
| N18 | Station fixes from the first real run (STFIX-v1): page size check, outlets from the source, early-ended web runs shown, attached pages keyed | Claude | done: station published 2026-11-05 (1793850747-e33f) |
| N19 | For-Update file: page column so print pages can match existing tracker rows by outlet + date + page | Claude | optional: skipped for now (Sammy 2026-11-05); revisit if pages of known stories keep landing in Unlinked print pages |
| N8 | Data > Reach and medium: the indented Medium sub-rows no longer spill 18 px past the card's right edge (PC page only, TIDY-v1 patch 15) | Claude | done |
| N9 | List tables: count columns (numbers and headers) centred on Outlets, Reporters, Press releases, Bills, Story travel and embedded rows tables | Claude | done |
| N10 | List tables' left and right edges line up with the controls above (pixel check at 4 window sizes: already exact, no change needed) | Claude | checked |
| N11 | Outlets header "Top reporters (own stories)" becomes "Top reporters" (CSV header unchanged) | Claude | done |

## F. First real use (after version 2 is installed)

| # | Item | Who | Status |
|---|---|---|---|
| A8 | First real Update run: Make "for Update" file -> station -> Update -> download -> Bring in update -> preview -> Save | Sammy + Claude | done 2026-11-05: saved (21 rows, 10 new stories, 5 reprints, San Mateo a CalMatters reprint, 2 Unlinked print pages); checked in the page after reload. The US Fed News row (Mayor Bass release) is Press release = Yes, so the page hides it and the Update log shows it as "Story removed" (wording only) |
| A13 | Move 01920 to the Removed tab, in that save | Sammy + Claude | with A8 |
| A9 | Refresh files for colleagues (with the version 2 zip) | Sammy | after A8 |
| A3 | Send IT the updated note with the version 2 fingerprint | Sammy | any time after N5 |
| A7 | Move the Update station to the office claude.ai account (station/MOVE_TO_OFFICE.md) | Sammy + Claude | later, no rush |

## B. Mac version (MACAPP-v1)

| # | Item | Who | Status |
|---|---|---|---|
| B1 | Mac starts: unzip, self-check, Open Anyway, Safari | Sammy | done |
| B2 | Test kit and Mac fixes | Claude | done |
| B3 | Mac fixes in the shared code; first final zips | Claude | done |
| B4 | Data test on the Mac with the kit | Sammy | done: everything works |
| B4b | Mac upload tests: bring in the test update zip and Save; load the for-Update file into the station | Sammy | ready now |
| B5 | Mac and PC swap a refresh file both ways | Sammy | after A8 |
| B6 | Final Mac zip | Claude | version 2 Mac zip built (N5); final once B4b and B5 pass |

## C. Read-only HTML preview

| # | Item | Who | Status |
|---|---|---|---|
| C1 | Preview file built and checked | Claude | done |
| C2 | Keep tone ratings in it | Sammy | done |
| C3 | Refresh the read-only HTML preview from the final draft: version 2's page (layout fixes) plus current data; needs the current workbook from the PC (the preview's data is the Nov 3 master, before the switch-over changes) | Claude (+ Sammy: send the workbook) | prep done 2026-11-05 (one command: work/localapp/preview/make_final.sh WORKBOOK.xlsx, ~40 s); done 2026-11-05: built from the workbook after the first real save (3a98feb1; 3,832 stories, as of Nov 5) with the story-panel layout fixes; saved-copy list from the workbook's Saved Copy? column plus the Nov 2 list |

## D. After the switch-over is finished

| # | Item | Who | Status |
|---|---|---|---|
| D1 | Remove the one-time Switch-over screen's code (A12, the misleading "Blanks only" wording, is moot once the screen is finished: D1 removes its code) | Claude | done in version 3 (2026-11-05); Set up from the Mac library, the reserved-ids file and the save's rename hook (`cell_steps.py`) stay |
| D2 | Retire the repo's old test copy of the data (data/), per SWITCHOVER-v1 | Claude | after A5c |
| D3 | Last cleanup: outdated code and decisions archived; CLAUDE.md and handoff brought up to date for any future Claude | Claude | last |
| D4 | Delete test leftovers: the Mac's "AJG Tracker" test copy and "Tracker library 2", the older PC test folders, test zips in Downloads; the Desktop "Tracker library" copy on the PC once you are happy | Sammy | after A8 |

## E. Open decisions for Sammy (none block anything)

- E1 Online read-only copy for colleagues (the preview, C, may cover this).
- E2 done 2026-11-05 (Sammy: "just clear them"): of the scan-position Page cells left after DATAFIX 12, 270 already equal the printed page on NewsBank's record (kept), 52 belong to papers whose scans always matched the printed page (kept), 174 had no printed page on record and were cleared (Coverage 174, Originals 47); row 10638 In Tracker? No cleared. List: work/localapp/datafix/pages_e2/page_changes.csv. Workbook 3a98feb1 -> 83614b19 (sent to Sammy to accept on the PC).
- E3 Common Sense Media's two posts are kept as coverage; revisit only if organisation advocacy blogs should be excluded.
- E4 Older items carried from the old tracker (CLAUDE.md "Open decisions"): A5 wire-blend pickups; 4 F7 rows (09721, 01734, 06948, 06949); 8 medium-confidence date fixes; 4 thin saved copies; Patch rows 00740 and 04889; Korea Daily Times; the 7 NOBLOGS rows; the Independent story's date; blank Tone/Topic on Newsroom America and Organiser.

## Done and dropped
- A4 dress rehearsal: skipped (the real run on the PC copy doubled as it).
- A14 "Access is denied": cause found (Windows briefly holding files); fixed by N1.

## Notes from the real runs (2026-11-05)
- Fifth station run (folder ajg_update_20261105-1530): all rows right, 12 of 14 pages placed; 2 Oct 25 p.14 pages (Long Beach, Daily News) went to Unlinked print pages because Claude's transcription of the long candidate list left out his paragraph. An outlet+date fallback was offered; Sammy declined ("that's fine"). The folder is cleared for the first real save (A8).
- Installer bug (2026-11-05, office PC): a folder dragged into Install update.cmd arrives in quote marks and a path with a space split in two ("Give the folder..."). Fixed in Install update.cmd and install_update.py (test added); Sammy used the workaround (type the path without quotes). The fix ships in the next zip.
- Install attempt 2 (2026-11-05): "Windows would not let go of a file in the old program"; the installer put the old program back (tracker starts, workbook 6.7 MB intact). Installer now waits about a minute for a held folder and names which one (app or python) with what to close (tests added). Restart did not help; Sammy installed by hand instead (N6). The cause of the block is still unknown; the next installer names the held folder. Both installer fixes ship in the next zip.
- First real save (A8), 2026-11-05: refused safely by the save's own check ("Originals: hyperlinks dropped 43 -> 0"; nothing written). Cause: saves rebuild Originals without hyperlinks; the switch-over put 43 there. Fixed (ORIGLINKS-v1, patch 31, test); sent as a drop-in of 6 changed files over version 4 (AJG_v4_fix_originals_links.zip). Mac zip gets it in the next build.
- To fix before the next program update: `Install update` (and a manual new folder) replaces app\pipeline\ with the zip's copy, which would lose the pipeline state files a save updates (lookup cache, outlets, bills, release texts/related; post_save.STATE_FILES). Harmless so far (no save has happened yet); the installer must carry them over.
- Preview after ORIGLINKS: Newtown Bee's AP story wrongly a Reprint of CalMatters s00002 (0% text; pooled credits). Fixed (OWNCREDIT-v1, patch 32, test); rerun here on a test copy: Newtown Bee its own story, San Mateo still a CalMatters reprint. Sent as AJG_v4_fix2.zip (same 6 files, both fixes).
- Version 4.1 zips (2026-11-05): version 4 plus every fix sent by hand today (installer quote/space and held-folder fixes, ORIGLINKS-v1, OWNCREDIT-v1); each differs from v4 only in those files. AJG_Tracker_windows_v4.1.zip sha256 70793b1819c0c8a0c95ff66a8cf823ba7355fe7472e87f29a616969efff18aa6 (132.2 MB); AJG_Tracker_mac_v4.1.zip sha256 9da965239388c144513f405fd204865b54f60f0f21b4c28bfb51ff24b2a30053 (165.1 MB). Not stored in GitHub: over its 100 MB file limit and they carry saved article text (repo rule); kept by Sammy, rebuildable from this repo (assemble_app.py / assemble_mac.py --code-only over the v4 zips).
- Story panel layout (Sammy 2026-11-05, TIDY-v1 patch 15 section 7): links line up with the headline, room around the English translation box, tone box text centred; quick look only (Sammy: no full checks). Sent as AJG_v4_fix3_layout.zip (needs Repairs > Rebuild the page).
- Station published 2026-11-05 evening (1793907302-9424): NEWEST-v1 (search from the day before the newest story, no date picker), tracker-duplicate / junk / old-find clean-up, FULLTR-v1 full translations, STREAMLINE-v1 plain page; Fable review fixed. The 18:35 folder (ajg_update_20261105-1835) is NOT to be brought in. PC side: make_for_update.py now writes newest_story_date (ships in the next PC drop-in; the station works it out without it).
- Version 4.2 zips (2026-11-05 evening, final for the team): 4.1 plus the story-panel layout fix and newest_story_date in the for-Update file. AJG_Tracker_windows_v4.2.zip sha256 281c6c5ee0de3a436582de8bfbb0da89fced33863e6f27a69be135edb2f5a2c3; AJG_Tracker_mac_v4.2.zip sha256 c7154c4aaf9c6e3d6ab4a8dee77317aef613b0ccf98c696cce14dc670438adc0. Office PC: AJG_PC_update_to_v4.2.zip (8 files over v4), then Repairs > Rebuild the page. Station 1793908590-59b7. Office PCs cannot open claude.ai artifacts (*.claudeusercontent.com blocked; IT note asks to allow it): run the station on the Mac.
- Guides: work/localapp/guides/ (User Guide 37 pp, Update Station 15 pp); Fable blind audit running.
- Switch-over check on workbook 3a98feb1 (2026-11-05): file renames worked (884 stale Story ID / o-r names on the Mac master -> 1 left: 09774), all 399 press-release rows purple, Other files column present, all 117 approved page fixes in place, 03486 author Marisa Kendall, no unverified reprints left. Still open: A13 move 01920 to Removed (do it with Remove + Save my edits on the PC).
- First run with the fixed station (2026-11-05 20:42, ajg_update_20261105-2042 from 3a98feb1): searched from Nov 3, 540 searches, 0 failed; 8 rows (4 new stories, 4 reprints), no old/junk/undated rows. Notes: iHeartRadio copy of the KFI "Corruption Wheel" segment comes in as a reprint (same house, really an edition); Clarín's Spanish ICE-law story (dated Oct 14) was seen but left out as before the search start (the no-overlap trade-off). Station 1793911558-f52b: translates only stories that go into the folder.
- Version 4.3 zips (2026-11-05, final for the team): 4.2 plus two wording fixes (refresh file: shared drive / OneDrive / USB, not email or Teams; the save's messages say "the keeper", not Sammy: PC patch 33). AJG_Tracker_windows_v4.3.zip sha256 1c7f3001227f3e08725a9ffbc923b51086b8d7e53bb676dae8e0be2b842af620; AJG_Tracker_mac_v4.3.zip sha256 e596f81e92e0c5ae7101fb6889657ef731a2b20c86d8daf0359ceefdafb8961b. Office PC: AJG_PC_update_to_v4.3.zip (all changed files over v4).
