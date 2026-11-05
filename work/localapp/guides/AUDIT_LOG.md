# Audit log: the two user guides (2026-11-05)

Guides: `AJG Tracker - User Guide.pdf` (37 pages) and `AJG Tracker - Updating with the Update Station.pdf` (15 pages). Style matched to `NewsBank_Download_Guide.pdf`: same fonts (Roboto Slab headings, Public Sans text, from `work/localapp/fonts`), navy cover block, letter-spaced section labels, navy rule under each heading, amber-edged callouts, navy tables, framed screenshots with gray captions, amber highlight boxes, footer with the guide name and page number.

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
