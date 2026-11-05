# Audit log: the two user guides (2026-11-05)

Guides: `AJG Tracker - User Guide.pdf` (38 pages) and `AJG Tracker - Updating with the Update station.pdf` (16 pages; the older file with a capital S was removed). Style matched to `NewsBank_Download_Guide.pdf`: same fonts (Roboto Slab headings, Public Sans text, from `work/localapp/fonts`), navy cover block, letter-spaced section labels, navy rule under each heading, amber-edged callouts, navy tables, framed screenshots with gray captions, amber highlight boxes, footer with the guide name and page number.

## The Fable audits were not run

The brief asked for a blind Fable audit after each section, run with the Agent tool. This session had no Agent tool: a tool search found none, and no other tool can start a Fable reviewer that could read these files. So no Fable audit took place.

In its place I did a self-review of every section against the brief's four questions:

1. Is it clear to a non-programmer?
2. Is it accurate against what the screenshots show?
3. Can the screenshots be read when printed?
4. Does it match the style guide?

This is weaker than a blind review, because I wrote the text and know how it was made. A Fable audit of the two PDFs is still worth running before Sammy prints them.

## Self-review findings and what changed

| Section | Finding | Change |
|---|---|---|
| All screenshots | Screenshots of narrow panels (Tracker files, preview, refresh) were stretched to full width, so their text printed about 15 pt, much larger than the rest. Tall ones ran off the page. | All panel screenshots now print at one fixed width (4.4 in), so they are the same scale as each other. Other images have a height limit, so none splits across pages. |
| Tabs 4 to 8, Data | The list-tab and Data screenshots were taken 1040 px wide, so their table text printed at about 6 pt. | Retaken 940 px wide, the narrowest width at which every column still shows (860 px cut off the Negative column). Each tab now has its own sub-heading, which also removes the half-empty pages. |
| Story panel | The numbered tags covered the first letters of the date, the facts line and the badges. Tag 9 (translation) was lost off the bottom of the crop. Tag 7 covered both the Note box and the mention bar. The second key list started at 1 while the tags read 6 to 9. | Tags moved outside the boxes. Tag 9 is anchored at the top. Box 7 is drawn around the note field only. The second list now starts at 6. |
| View original | Only the first of the two "View original" links was boxed. The figure sat alone on a nearly empty page. | Both links are boxed. The block moved to the "Full-page view" page. |
| Clips | The Export menu crop showed stray page text. The ticked-rows bar crop showed blurred table text behind it. | Both are cropped to the element itself. |
| Data | The chart crop began with a strip of the card above it. | Trimmed. |
| Preview (Bring in update) | The real preview runs three pages long, because of a long list of renamed files. | Split into "top of the preview" and "end of the preview" crops. The save result is cut down with a dashed break. Each caption says what was left out. |
| Update station: How it works | The full dialog, shrunk to fit a page, printed at about 5 pt. | Shows the top of the dialog at full width. The caption lists what the rest covers. |
| Update station: PDF boxes | The NewsBank and ProQuest boxes side by side printed too small. They are mostly empty drop zones. | The NewsBank box is shown full width. The caption says the ProQuest box looks the same. |
| Accuracy | "Edits fill blanks only" was missing at first. A test edit of a filled field (outlet spelling) showed that the save keeps the workbook's value and only reports the edit. | Added "Edits fill empty fields only" with the Excel route for changing filled values. The Save my edits example shows that exact message. |
| Accuracy | The tone "Change" menu writes to this copy's own data folder, never to the workbook or a refresh file. | The guide says the change shows in your copy only. |
| Accuracy | Checked against the program: the Spreadsheet button downloads `AJG Coverage - NewsBank.xlsx`; the reader panel offers "Bring in refresh file" plus "Make for Update file"; Repairs lists four buttons. | Text matches the screenshots. |
| Clarity | Terms defined where first used: workbook, library, saved copy, keeper, reader, "for Update" file, update folder, refresh file, .zip, CSV, fingerprint, TinyFish, 127.0.0.1. One troubleshooting row about "port 8765" was reworded into plain words. | Done. |
| Guide 2 vs the NewsBank guide | The station's own How it works text says to search "Jesse Gabriel" and sort newest first. The NewsBank Download Guide uses a saved search, oldest first, starting one week before the newest story. | Guide 2 points to the Download Guide and says to follow it where the two differ. |

## How the screenshots were made (for whoever updates the guides)

- **PC tracker:** an isolated copy of the Linux test tracker, built with `cp -al` and then given real copies of `data/workbook`, `state`, `db`, `site`, `copies` and `updates`. Folder: `scratchpad/guides/tc`, deleted afterwards. In that copy I made one edit, removed one story, brought in `sammyzip5/u.zip` (warning, then Use it anyway, preview, Save) and made one refresh file. The original test copy was not touched: its workbook fingerprint is still bc21c9fb.
- **Update station:** the built `dist/index.html`, run in a scratch copy of the test harness at deviceScaleFactor 2. The "finished run" is the canned run from `station_test.js`, with made-up stories; the guide's caption says so. Step 3 uses the run document `run-mw3tx5atiai.json`.
- **Licensed text:** article text in saved copies and translations is blurred. Only headlines show.

## Observations for the project (not changed; no code was touched)

- **Station:** while a run is going, Step 2 shows the old tracker's long paragraph. It begins "Each story is credited…" and tells you to "ask Claude in chat to save the last run to the sheet" and use "Refresh from files". The STREAMLINE-v1 hide in `station.js` (line 782) does not seem to apply during the run. The guide's screenshot is cropped above it.
- **Station:** How it works says to "sort newest first", while the NewsBank Download Guide says Oldest. One of them should be brought in line.

## Round 2: the blind Fable audit (FABLE_AUDIT.md), applied 2026-11-05

The coordinator ran a blind Fable audit of both PDFs; its findings are in `FABLE_AUDIT.md`. All the recommendations below were applied except the few listed under "Skipped". Afterwards both guides were rebuilt and every page was checked at 70 dpi.

**New screenshots.** All of them were retaken from a fresh isolated copy of the test tracker, after one real save in that copy (an edit, a removal, `u.zip` brought in with Use it anyway, then Save, then a refresh file). Counts and fingerprints therefore agree across pages: 3,689 stories, fingerprint 41315fe0. The Update station shots come from the current build (`build_station.py`; the build output did not change) in the harness, with the PC-made file `for_update_202611052016_41315fe0.json`. The checklist now reads "Keep them for the update folder". The test copy was deleted afterwards and the original test tracker is untouched (still bc21c9fb, keeper).

| Audit item | Change |
|---|---|
| A1.1 legibility | Wide pages were recaptured at narrower window widths (820-940 px), so the app's text prints larger. Close-up crops follow the style guide's "one overview, then zoom" pattern: masthead buttons, Home tiles, story panel parts 3-5. The Edit form is split into two crops. The reporter page is shot at 700 px. Panel screenshots print at one fixed width. |
| A1.2 half-empty pages | Sections now flow on (no forced page break) wherever a page was more than half empty. Tables were moved next to their screenshots (Manage, Repairs). |
| A1.3, A1.4, B1.3 | Claude and TinyFish are defined in both word lists and at first use. The Update guide now has its own word list. |
| A1.5 | The contents table has page numbers, filled in automatically from the rendered PDF. The cheat sheets give page numbers too. The contents now sit on page 1 and the word list on page 2. |
| A1.6 | Section titles are 18 pt and the small labels above them 7.4 pt, as in the NewsBank guide. The cover title is 22 pt. |
| A1.7 | Footers match the cover titles. "Update station" (lower-case s) is used everywhere, including the file name. |
| A1.8 | Data agree across pages. A note on page 1 says the pictures come from a test copy. |
| A2-A3 | The keeper is named (currently Sammy). Added "(PC offline: text still there)", "not on the shared drive: it does not run from there", and a "layout.json and anything else: leave it" row. The black-window drawing now has the same navy frame as the screenshots. |
| A4-A5 | The Manage number is called an example that changes. The tone bar has its own crop. The Filters crop shows the Issue group, with the Export menu beside it. Crops end at row edges. The ticked-rows bar was taken at full width. The filter list was shortened. |
| A6 | No more see-through edge on the story panel. Tone "Change" is described as your copy only, with the fix route via the workbook. The full-page view is shown at half width with its text beside it. Both View original links are boxed with padding. The Edit form's note is quoted in the caption. |
| A7 | The chart crop includes Chart options and Show the numbers. The 14 Data sections are a two-column list. Table crops end at row edges. "Picked up" and LegInfo are defined. "Map … (not shown)" is noted. |
| A8.2 | One callout explains "conflicts left for Sammy": cells left for the keeper. |
| A8.3 | Bring in update: the older-workbook warning is now its own step (Use it anyway / Do not use it), then the preview, then Save / Do not use this update. Both guides match the screenshots. |
| A6.7, A8.4, D2 | Neither guide says to fix "items that need a person" with Edit details any more. A table explains what each kind means. It says the save already wrote them, that you check the row afterwards, and that the keeper fixes filled values in Excel and then uses Accept the workbook. |
| A8.5-A8.9 | A callout after Save covers refresh files and the new "for Update" file. The save result is now two crops cut cleanly between lines. `db\_applied\edits` is explained. The workbook tab names are listed. "(keeper only)" is added to the parts list. |
| A9.1, D1 | Refresh files go by the shared drive, OneDrive or a USB stick, not email or Teams. The caption points out that the program's own message still mentions email and Teams. |
| A9.2-A9.5 | Reader steps say to use the .zip itself. Readers don't need the "for Update" file. Repairs uses the exact button names and the "their edits become part of the tracker" warning. |
| A10 | Dragging a folder is explained. The by-hand install says it takes minutes and that role.json comes along. Problems now include "Save is grayed out" and "No workbook yet", and the port row says to look for another tracker window first. The cheat sheet gains Save my edits and page numbers. |
| B1.1 | The Update guide names its parts by place ("On the PC", "In the station · Step 2") and keeps only the station's own Step 1/2/3. The overview table and cheat sheet match. |
| B1.2, B4.3 | Stale station screenshots were replaced (file name, checklist label). |
| B2 | Page 1 points to the NewsBank Download Guide. The link prints in link blue. The first-time Claude and TinyFish permission steps are written out. A sign-in row was added to Problems. |
| B4 | The confirm box is cropped to the dialog alone. The running shot shows the Stop button. LegInfo is explained in the caption. The How it works crop is shorter. |
| B5.1, D3 | The "station says newest first" remark is gone. The guide simply follows the NewsBank Download Guide (Sort by Oldest), which the station's text now also says. |
| B5.3-B5.4 | "Unlinked print pages" is called a workbook tab. The caption explains "Add to the update". |
| B7, C | The PC pages in both guides were fixed the same way. B7.2's reprint sentence was copied into the User Guide. "Close Excel" is added for colleagues. |
| B8.2 | Cheat-sheet wording: "When the zip is downloaded", "In the Update station (its Steps 1-3)". |

**Skipped or changed, and why**
- A3.1 (a real screenshot of the black window): it can only be captured on the office PC. The drawing stays, framed like the screenshots and labelled as a drawing.
- A8.2 second half (change the program's "left for Sammy" wording): that is a code change, outside this job. The guide explains the phrase instead.
- A9.1's suggestion that a later refresh file is "small enough for email": the coordinator asked for the shared drive, OneDrive or USB only. Neither guide mentions email.
- B7.1's idea of shrinking the Update guide's PC pages to "see the User Guide": kept stand-alone, because Sammy may print only the Update guide. The texts now match.
- A8.1 "Data checks crop to five rows": it shows its four rows, which is all the test data has.

## Round 3: Update station guide rebuilt, then Fable audit applied (FABLE_AUDIT_UPDATE_GUIDE.md, 2026-11-05)

The guide was redone for the newest station (no date to pick, "Search all time", one-line reminders, full English translations, office-PC block). The blind Fable audit of that draft was then applied. The guide is now 18 pages (the audit's draft was 20). Station shots were retaken from a fresh `build_station.py` build, at deviceScaleFactor 2 and a 700 px window. Harness copy and shot script: `scratchpad/g3/harness2.js`, `shots_700.js`.

**Applied**

| # | Change |
|---|---|
| 1 | Keeps the current station link and adds the line "New link (if the station moves to another claude.ai account): ____". The sign-in wording is now "the claude.ai account that owns the station" (pages 2, 5, Problems). |
| 2 | The "press again to start" shot is real. The harness copy exempts the 6-second timer from its 100x speed-up, so the label shows by itself. Step 2 now says "within about 6 seconds" and that the button reads "Searching all time…" during a run. The Problems row says the same. |
| 3 | One line under the page-1 table says the screenshots come from several test runs, so codes and counts differ, and that the zip's code should match the "for Update" file's code. The p16 result shot has the fingerprint line and the "0 file name(s)" line cut out (the caption says two lines were cut). A running-number note was added to the refresh caption. The station and PC test data were not re-staged. |
| 4 | The older-workbook warning now leads with the clean fix (Do not use it, make a new file, rerun). "Use it anyway" comes second, only when you cannot rerun and the only change was your own edit. The Problems row matches. |
| 5 | Safari: Download step and Problems row now say to use Chrome, or turn off "Open 'safe' files after downloading", and to press "Download the last one again". |
| 6 | "Load a different file" clears the page, and closing or reloading the tab does the same. Added to Step 1, the Problems row, and a note under "Before you start" ("download before you close the tab"). |
| 7 | Left-out rules: a web find dated more than a month before the search start is left out (not in Search all time), and so is an undated reprint of an older story. The guide says the left-out rows are kept in the update folder's record of the run and are NOT listed in the PC preview. This is the coordinator's correction to the audit, which said they were listed. |
| 8 | The "How it works" screenshot page is gone. A paragraph points to the button and says to trust the page if the guide and page differ, because the station text was rewritten after the draft. |
| 9 | Page 5 now shows only the empty drop box, full width. The half-width orientation shot is dropped. |
| 10 | Orange outlines are added on the station shots: drop box, "File made" line, Search all time, Stop, Download update folder, NewsBank drop box and Add to the update. |
| 11 | Automatic mode: the shots are retaken with it on. Page 10 says it is on unless switched off and the station remembers the choice in that browser (checked in `station.js`, `S.auto` and `ajg_station_auto`). |
| 13 | The preview bullet now uses the on-screen phrase "cells where the update disagrees with the workbook (the workbook keeps its value)". The bold-line bullet no longer claims "your own waiting edits". |
| 15 | The tab wording is now "keep the station tab open and visible, don't minimise or switch tab, keep the computer awake; other programs beside it are fine". |
| 16 | PDFs and a running search: they wait with Automatic mode on; with it off, press Add to the update again afterwards. |
| 17 | The TinyFish row quotes the real red messages from `station.js` and gives the full fix. |
| 18 | "0 file name(s)…" is cut from the p16 shot. Explained "full_0002" as a running number in the refresh caption. |
| 19 | Words table and "Before you start" now share page 2. Problems and the cheat sheet share the last page. The How it works page is gone. The unused confirm-box picture was also dropped (described in text). Result: 18 pages. |
| 20 | The "Move the file" row is folded into "Make the file". |
| 21 | The file-name meaning (year, month, day, hour, minute) is stated. |
| 22 | The PC window is now "the black command window (the one the tracker opened)". |
| 23 | The red "File made" line (over 7 days or no date) is mentioned. |

**Skipped or changed, and why**

- **12 (Permissions menu pictures):** I cannot capture the artifact page's Permissions menu or the allow prompt outside claude.ai. I added the exact connector name "TinyFish", where the menu is, and that the station shows a red message if a permission is missing.
- **10 (outlines on PC screenshots):** I cannot redraw the PC panel shots without rerunning the PC tracker, so only station shots got outlines. Zebra-striped table rows were not added.
- **14 (where the "run notes" are):** I could not find where the PC puts them. The caption now ties the line to the "Items that need a person" list in the preview, and the text says the result lists them again after the save. It does not name a file.
- **3 (re-stage):** I used the one-line disclaimer, not a full re-stage, because the PC shots need the PC tracker.

## Round 3b: Update station guide, three changes from Sammy (2026-11-05)

The guide is now 17 pages (it was 18). Page references were re-checked: the build resolves every "page N" reference and none is left as "?".

1. **Office-PC block removed.** The whole flow is now on the office PC. Removed:
   - the "Office PCs can't open the Update station yet" box and its carry-over steps;
   - the "Find a computer that can open the Update station" item in Before you start;
   - the "carry it to another computer" and "copy the .zip back to the office PC" wording (overview table, Make step 5, Download step, cheat sheet);
   - the Problems row about the page not opening on the office PC;
   - the "office PC can't open the station" sentence in the cheat-sheet Remember box.
   The Safari/Mac advice was dropped too (download step and the ".zip" Problems row), because the office PCs run Windows and Edge, so it no longer applies.
2. **Account.** The station link line now says it runs under the office's claude.ai account, ajgdistrict@gmail.com. The sign-in wording (Open the station, Problems row) is "sign in to claude.ai with ajgdistrict@gmail.com". The "New link (if the station moves)" fill-in line stays.
3. **Cover.** The eyebrow is now "Staff guide · Assemblymember Jesse Gabriel press coverage" (no parenthesis).

Layout: "Make the 'for Update' file" now continues on page 3 instead of starting a new page, so the page left half empty by the removed box is gone. Page 3 is still about half full before the next section.

## Round 4 (User Guide): second blind Fable audit (FABLE_AUDIT_USER_GUIDE_2.md) and Sammy's changes, 2026-11-05

The User Guide went from 38 to 32 pages. I checked every page at 70 dpi. The companion guide was not touched. The test tracker was not rerun; this round used the existing screenshots, recropped where needed.

**Applied**

| Item | Change |
|---|---|
| 1 | The "Conflicts left for Sammy" callout is gone, and so is "messages name Sammy" in the word list. A line under the preview table now uses the 4.3 wording: "conflicts left for the keeper to decide". |
| 2 | The older-workbook warning now leads with the clean fix (Do not use it, new "for Update" file, run the station again). Use it anyway is offered only if you cannot rerun and the only change was your own edit. This is the companion guide's wording, both in the steps and in Problems. |
| 3 | The refresh screenshot is cut above the old message line. The caption quotes the 4.3 message: "on the shared drive, OneDrive or a USB stick (it can be too big for email or Teams)". |
| 4 | New block "A new colleague's first copy": unzip, "No workbook yet", the keeper makes a FULL refresh file from Repairs, the colleague brings it in. Also linked from the refresh page, the "No workbook yet" problem row and the cheat sheet. |
| 5 | Replaced by Sammy's instruction (below). |
| 6 | A navy "On a Mac" callout covers the first start (Terminal unzip, `bash "AJG Tracker/Start Tracker.command"`, Open Anyway) and the Terminal window. The install page has a Mac line (Install update.command, Return). The cheat sheet names Install update.command. |
| 7 | Text now says "29 in the picture". The close-up is widened to include Spreadsheet and tag 2, and cropped above the tab bar. |
| 8 | Page references fixed: Story travel and "What happens to your edits" now have their own anchors. |
| 9 | The ticked-rows bar is cropped inside its own edges. |
| 10 | Pages are much fuller. Forced page breaks remain only before Words, Start, Home, Tracker files and the cheat sheet. Panel screenshots now float beside their text at 3.75 in. The preview's top and end crops sit side by side. The full Home shot is split into the tiles crop and the Needs attention crop. The tracker-folder table moved to "Where your files live". |
| 11 | Each wide screenshot is printed at the width its browser width needs for body text of about 7 pt or more. The Reporters table is no longer shrunk. Captions say "(shown small; nothing in it needs reading)" for the full-page view and "(the table lists the buttons)" for Repairs. |
| 12 | Three Repairs buttons are marked "(keeper only)", and a line says "On a reader copy, Repairs holds only Rebuild the page." |
| 13 | Backups: "The newest three are kept; older ones are moved to _to_delete inside backups." |
| 14 | Both places now say "(or your usual browser if Edge is not on the PC)". |
| 15 | Problems has new rows for "Another save is running" and "The tracker says the update was already saved". |
| 16 | The warning caption explains its older fingerprint, with a page reference to the save. |
| 18 | The QQ…QQ anchors are used only in a check render. They are removed from the final PDF, and its text layer has none (checked with pdftotext). The anchors are positioned so removing them does not move the layout, and the build checks that page numbers stay the same. |
| 19 | The Views paragraph stays together with the figures after it. The story-panel close-up ends at a word boundary. The lower-panel crop starts at the tone box. |

**Sammy's changes (they override the coordinator's earlier note and audit item 5)**
- The guide does not say that office PCs can't open the Update station. There is no blocked-address text and no "use another computer" advice.
- The guide names the station's account: it runs on the office's claude.ai account ajgdistrict@gmail.com, and you sign in with it to open the station. This appears in the word list, the "for Update" step and the cheat sheet.
- The cover label is now "Staff guide · Assemblymember Jesse Gabriel press coverage".

**Not changed in the guide**
- Item 17 is about the program's own wording. Manage's "Add saved pages" text says tone and author are saved for everyone, which is not true on the PC. That needs a code change, so I am passing it to the builder.
- Item 5 is superseded by Sammy's instruction above.
- Page 4 keeps about a third blank, because Home starts on a new page. Without that break, the Home heading was left alone at the foot of the page.
- A few panel screenshots still have one line of small gray text at about 6.9 pt (the panel's "small" text). The main text in every screenshot is 7 pt or more.
