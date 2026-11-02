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
