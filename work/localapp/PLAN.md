# The new AJG Tracker: plan

Written 2026-11-02 for Sammy. Decisions behind it: LOCALAPP-v1, UPDATEFOLDER-v1, UPDATESTATION-v1, SAMELOOK-v1 (docs/DECISIONS.md). Facts behind it: work/localapp/SURVEY.md.

## The two parts

**1. The PC tracker** (a folder on the office PC; nothing installed, never goes online)
- Opens with a double-click. The tracker appears in a browser window and looks and works like today's: Home, Clips, Trends, Insights, the press-desk tabs, the story sheet, team notes, saved views.
- Hidden: the Update button, and the tone, author and translation buttons (those jobs move to the Update station).
- Holds the workbook, the article library, the saved copies and a small private Python.
- Notes, saved views and edits you make are kept as files in the folder, where the claude.ai tracker keeps them online today. Only people using that PC see them.
- Two new buttons:
  - **Make "for Update" file**: a small file listing what the tracker already has (story details, no article text) plus the Update button's memory (which dates it already searched, saved lookups).
  - **Bring in update**: you drag in the update folder; it shows what would change (rows added, cells filled, items needing you); you click Save; it backs up, writes the workbook with every save check, adds the new pages to the library and refreshes the tracker page.

**2. The Update station** (a new, private claude.ai page; the old tracker is not touched)
- Step 1 each time: load the "for Update" file. The page reads it in your browser; it is not stored online.
- Step 2: press Update. Same code and same searches as today's button (TinyFish, free), including tone, authors and translation for each new story.
- Step 3: download the update folder (one zip).

## Each week or month

1. PC tracker: Make "for Update" file.
2. Update station: load it, press Update.
3. Download the update folder.
4. PC tracker: Bring in update, look over the preview, Save.

## Safeguards

- **Fingerprint.** The "for Update" file records the workbook's checksum; the update folder carries it. If the workbook changed since (a later save, your own Excel edit), the PC tracker warns before saving.
- **All of today's save rules** (SAVE_RULES.md): backup first, fill blanks only, refuse on any surprise, keep the 3 newest backups, never delete.
- **Reprints** are decided exactly as now: the button finds candidates by headline, link and outlet; the save compares article text on the PC (REPRINT90-v1).
- **One save path.** Until switch-over, the old tracker keeps saving to the Mac. Never feed one run to both.

## Build order

| # | Step | Who builds | Needs you |
|---|---|---|---|
| 1 | Test zip on the office PC | done | Run it, send the report |
| 2 | Copy the page's look (the "shell") and other missing build parts from the live tracker, read-only | Sonnet | No |
| 3 | Build the tracker page from the snapshot copy; check it matches the live one | Sonnet | Glance at screenshots |
| 4 | Local server and the stand-in for claude.ai storage (notes, views, edits) | Sonnet | No |
| 5 | Windows folder: private Python plus the packages the save needs; replace the two tools that do not run on Windows without installs | Sonnet | One more PC test |
| 6 | "Bring in update" and "Make for Update file", wired to the save program | Sonnet | No |
| 7 | Update station: the Update button taken out of the tracker, file in, zip out | Sonnet | Try one real update |
| 8 | End-to-end test on copies: file, station, folder, PC tracker, workbook | Sonnet, Haiku | No |
| 9 | Fable review of everything that writes the workbook | Fable | No |
| 10 | Switch-over: the Mac master and library copied to the PC, every file checked, first real save | Haiku | Yes, present |

Agent time: several days of building. The calendar is set by your PC test rounds (steps 1, 5, 7).

## Settled 2026-11-02 (SWITCHOVER-v1)

- Switch over when ready and tested (step 10 follows steps 8 and 9).
- The PC tracker starts fresh: old team notes, saved views and edit history stay in the old tracker.
- The review queue (merge decisions) moves into the PC tracker.
- An online read-only copy for colleagues: decide later.

## Switch-over day checklist (SWITCHOVER-v1; keep this list current)

Before the day: CLEANUP-v1: remove outdated or inactive code and move superseded decisions to docs/DECISIONS_ARCHIVE.md (every removal listed; all suites green after); then run CHAINCHECK-v1 (work/localapp/chaincheck/: PC for-Update file -> station -> update folder -> PC preview/save -> page -> reader refresh) on the final builds; it must pass before the final zip is sent and the station is moved.

Done to the real workbook from the Mac, never to an older copy:
1. Old tracker: stop Update and saves (it stays read-only by habit).
2. Old workspace's Claude makes `Tracker library manifest.sha256` (workbook + year folders, _original_html, _original_pdf, Press releases).
3. Sammy copies those plus the manifest to a private cloud folder, downloads it fully onto the PC Desktop.
4. Unzip the final PC tracker (empty data); Tracker files > Set up from the Mac library: every file checked against the manifest, then copied in; ledger seeded.
5. One-time changes to the new sheet, from ONE "Switch-over changes" screen (one backup first, all previews together, confirm all or step by step; shown only that once):
   a. DROPUNVERIFIED-v1: delete all "Reprint (unverified)" rows (counted fresh) and their files; IDs stay reserved.
   b. PRCOLOR-v1: recolour every Press release = Yes row purple (#7030A0); only font colour changes.
   c. PRJUDGE-v2: mark Press release = Yes on the 3 missed wire releases (01190, 01364, 00290; not 01759), and set Press release = No (font black) on the ~119 other-issuer reposts on news outlets; own-release copies untouched; 13 organisation-site posts listed for Sammy. All re-checked on the real workbook first.
6. Move the Update station to the office claude.ai account (work/localapp/station/MOVE_TO_OFFICE.md); connect TinyFish there.
7. First real update: Make "for Update" file, Update run in the station, Bring in update, preview, Save (Sammy present). This is the end-to-end test.
8. Make refresh file (full) for each colleague.
Automatic from then on (built into the save and page): PRJUDGE-v1, PRCOLOR-v1 for new rows, LIBFILES-v1 names and folders, NewsBank/ProQuest saving, PCEDITS-v1, REVIEW_2 fixes, fast save, TIDY-v1, VIEWORIG-v1.

## Consolidation round (FREEZE-v1; in this order, one builder at a time on shared PC files)
Running now (finish, then commit): tidy-up (TIDY-v1) final suite; station round (PRJUDGE-v2, NewsBank TV, Fable audit fixes 1-5); data checks (print pages, translations, outlet-name authors, NewsBank fills: reports only); CHAINCHECK-v1 build.
1. Other files column wiring (OTHERFILES-v1), then Note rename (NOTE-v1): each waits for the previous to commit.
2. PC features: LASTUPDATED-v1; VIEWORIG-v1 (option B); PRCOLOR-v1 + PRJUDGE-v2 on the save (honour the station's per-item verdict; purple for press-release rows); NewsBank PC patches from the station round (print-page rows, Unlinked print pages writer); for-Update file exports Unlinked print pages links.
3. Switch-over builder (restart from the WIP commit): Set up from the Mac library; the one "Switch-over changes" screen with every one-time step (DROPUNVERIFIED-v1, PRCOLOR-v1 recolour, PRJUDGE-v2 existing rows, OTHERFILES-v1 column, plus the data-check fixes Sammy approves).
4. Sammy reviews the data-check reports (batched questions).
5. Integration: fresh assemble; all suites (saver, review, review2, updatefolder, app, station); look check on changed routes; CHAINCHECK-v1; station republish if needed.
   Then PARITYTEST-v1, the final functionality comparison: the live tracker's files (fetched read-only, run locally with a stand-in for its storage; its database is never touched) and the final PC tracker, both built from the same workbook copy, driven side by side through every feature (each tab and route, search, filters, sorting, story sheet, reprint groups, links, notes, saved views, edits, downloads/exports, charts). Same inputs must give the same rows, counts, outputs and look; the only differences allowed are the recorded exceptions (SAMELOOK-v2 list). Any other difference is fixed or brought to Sammy. Must pass before the final zip; re-run after CLEANUP-v1.
6. CLEANUP-v1 (outdated code and decisions archived), suites again, final zip and IT note fingerprint.
7. Switch-over day (checklist above).

## After switch-over (ideas noted, not built)
(none yet)
