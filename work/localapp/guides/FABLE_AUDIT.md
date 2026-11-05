# Blind audit of the two printed guides

Audited 2026-11-05 by Fable, from the PDFs only (rendered at 110 and 300 dpi, every page read), against the NewsBank Download Guide as the style standard. A few facts were checked against the source in `work/localapp/` where a claim looked risky; those checks are marked "(checked in source)". Nothing was edited.

Print sizes below were measured on the 300-dpi render and calibrated against the body text (10.6 pt). "About N pt" means the size that text will have on US Letter paper.

## Verdicts

- **AJG Tracker - User Guide.pdf (37 pages):** Good bones and the right voice, but not ready to print. Three pieces of advice contradict each other or the program (edits and "Items that need a person", email for an 855 MB file, two button pairs described as one), 11 screenshots carry text that prints at 4-6 pt, four crops are visibly broken, and about a third of the pages are more than half blank. One revision pass fixes all of it.
- **AJG Tracker - Updating with the Update Station.pdf (15 pages):** Close to ready. Clear steps and the best screenshots of the two. Fix the two-numbering-systems problem (guide steps 1-7 vs the station's own Step 1-3), replace two stale screenshots (old file name, old checklist label), and drop the line that tells readers the station's own help text is wrong (it no longer is).

Everything else is polish. Both guides match the style guide well on fonts, colours, callouts, tables, footer and cheat sheet.

---

## A. User Guide (`AJG Tracker - User Guide.pdf`)

### A1. Cross-cutting (whole guide)

1. **Pages 5-21, screenshot text too small to print.** Measured sizes in the full-width app screenshots: story meta lines and badges (p5, p6, p8) about 6-7 pt; the full-page story view (p11) about 5 pt; Edit story form labels and its bottom note (p13) about 6 pt and 5.5 pt; reporter-page labels (p17) about 5.5 pt; chart sublines and axis labels (p15, p18) about 5.5 pt; Manage data-check sublines (p21) about 5.5 pt; table body text (p16, p17) about 7 pt. The style guide's rule, by example, is: one full-width shot for orientation, then zoomed crops of the part the text is about (its p5-p7 crops print at 8-12 pt). Change: for each of pages 5, 8, 11, 13, 15, 16, 17, 18, 21, replace the single full-width shot with a tighter crop of just the region the callouts or text discuss (or add one), captured at a narrower browser width so the app's text is larger relative to the page. Keep full-width shots only where the layout itself is the point (p4 top band, p6 Clips tools).
2. **Pages 2, 7, 12, 14, 15, 18, 19, 20, 22, 25, 27, 28, 29, 33: more than half the page is blank.** The style guide also leaves white space, but these are caused by page breaks pushing one screenshot or one table onto its own page (p12 is one small screenshot and 80% white; p22 is one table; p28 is one screenshot with no heading; p33 the same). Change: either allow the Repairs screenshot (p33) and the Save result (p28) to share a page with the text that discusses them by shrinking the screenshot, or set the HTML so a screenshot and its caption may break onto the next page together with the paragraph before them. Target: no page with less than one third of its area used, except the last page of a section.
3. **"Claude" is never defined.** The guide says "When Claude sends a new version" (p34), "send it to Claude" (p36), "If Claude says to rebuild" (p34). A new staffer does not know whether Claude is a person, a vendor or the AI. Change: add a row to "Words used in this guide" (p1): "Claude: the AI assistant that built and maintains the tracker. When the guide says 'send it to Claude', it means paste it into the office's Claude conversation (ask the keeper)." Same for the Update station guide (see B1.3).
4. **"TinyFish" appears in a screenshot with no explanation** (p21, "Tracker update 2026-10-21 (all-time TinyFish search)"). Change: add to the word table or to the p21 caption: "TinyFish is the web-search service the Update station uses."
5. **Contents (p2) has no page numbers.** On paper that is the one thing a contents page is for. Change: add page numbers; and consider putting the Contents on p1 below the cover block and moving "Words used in this guide" to p2, so the reader sees the map first.
6. **Headings and kickers are larger than the style guide.** Section titles are 28 px (21 pt) against the style guide's 24 px (18 pt); kickers are 9.3 px against 8 px. Body, captions, tables, callouts and footer match. Change: set `h1` to 24px and the kicker to 8px so both guides and the NewsBank guide look like one set on the shelf.
7. **Footer wording differs between the two guides and from the file names.** User Guide footer: "Using the AJG Press Tracker"; Update guide footer: "Updating with the Update Station" (capital S, while the cover and every sentence say "Update station"); files are named "AJG Tracker - User Guide" and "AJG Tracker - Updating with the Update Station". Change: use one short footer each, matching the cover titles, and lower-case "station" everywhere.
8. **Screenshots come from different data states.** Home (p5) says 3,681 stories, newest Oct 28; Clips (p6) says 3,689 stories with a story dated Nov 4; the Tracker files panel (p23) shows fingerprint bc21c9fb but the for-Update file (p24) and the reader panel (p31) show d2d774e5. A careful reader will wonder which is right. Change: recapture p5 (and p16-p20 if convenient) after the p28 save so the counts and fingerprints agree, or add one sentence on p1: "Screenshots were taken on different days, so counts and fingerprints differ between pages."

### A2. Cover and page 1-2

1. **p1, word table, "Keeper".** "The one person who brings in new stories and saves them" is clear. Add who that is today ("currently Sammy"), because the program's own messages name him (see A7.2).
2. **p2, navy callout "The program stays on your PC".** Good and matches the style guide's navy callout. Minor: "One exception: newer saved copies show their photos from the news site" could add "(the PC must be online for the pictures to appear; the text is always there)". The same fact is on p36 ("Photos are missing in a saved copy"), so link them.

### A3. Starting and closing the tracker (p3)

1. **p3, "black window" box is a drawing, not a screenshot.** The caption says "drawn from the program's own messages" (and the text matches `launcher.py`, checked in source). That is honest, but the style guide uses only real screenshots, with a navy frame. Change: capture the real window once on the office PC; if that is not possible, keep the drawing but make its frame match the other screenshots (navy 2 px border, rounded corners) rather than the grey title bar.
2. **p3, step 1.** "Keep the folder on your own PC (for example on the Desktop), not on the shared drive" is important and well placed. Add why in five words: "(it does not run from there)".
3. **p3, table "What is in the tracker folder".** The source layout also has `layout.json` at the top level (checked in `assemble_app.py`). Either list it ("a settings file; leave it") or add one row "Anything else: leave it alone."

### A4. The top of the page (p4)

1. **p4, callouts 1-5.** All five numbers match their keys. Good.
2. **p4, callout 4 text.** "The number counts things worth a look, such as pages without a tone rating" — the screenshot shows 21; p21's Data checks shows 20 pages waiting plus other items. Fine, but say "for example 21 in the picture" so the reader knows the number changes.
3. **p4, second screenshot.** The orange highlight around "LAST UPDATED NOV. 5, 2026" prints at about 7 pt, right on the limit; acceptable because the caption repeats it.

### A5. Home and Clips (p5-p8)

1. **p5, screenshot cut off mid-section.** The caption promises "the tone bar" but the crop ends at the "Tone, last 90 days" header, with the bar itself cut off. Change: extend the crop to include the bar, or drop "and the tone bar" from the caption and show the bar as a second, tighter crop next to the bullet that explains it.
2. **p5, bullet "The four tiles compare the last 30 days and this year with the same period before."** The tiles' sublines ("vs. 151 the 30 days before", "vs. 568 by Oct 28, 2025") print at about 5 pt. Zoom one tile as a small crop (like the style guide's p5 crop) so the reader can see the arrow and percent being described.
3. **p6, callouts 1-5.** Numbers match keys. Callout 1's list of filter groups ("issue, bills, reach, how Gabriel appears, mention depth, direct quote, medium, format, outlet, reporter, county, state, language and tone") is 14 items in one sentence. Change: "Opens a panel of filters, one group per heading (issue, bills, reach, outlet, reporter, tone and more)."
4. **p7, layout.** The Filters panel is a very tall, narrow crop beside a loosely cropped Export menu, with the whole lower right empty, and the heading says "Search, filters and the table" though the table is on p8. Change: crop the Filters panel to the Issue group only (its first eight rows), place the Export menu beside it, and start "Reading the table" on the same page.
5. **p7, Export menu screenshot.** Loose crop: the "All dates / Compact" buttons and a sliver of the table show behind. Crop to the menu alone (its navy frame already highlights it).
6. **p8, first screenshot.** Bottom edge cuts through the second story's badge row ("Quoted · Saved copy · Very positive" half visible). Crop at the row boundary.
7. **p8, "Two stories ticked" bar.** The bar was captured at a narrow width, so "Clear" wraps onto a second line, and under the bar a strip of blurred page text shows through (visible at print size as a smudge). Change: recapture at normal width (one line of buttons) and crop to the bar's edges.
8. **p8, "Reading the table" bullets.** Good. Add "Reprints" definition link: "(see Story travel, p20)".

### A6. The story panel (p9-p13)

1. **p9, screenshot left edge.** The page behind the panel shows through on the left (a column of cut-off letters "MBER", "Ga", "elta", "s and"). Crop at the panel's left edge, as the p10 crop nearly does.
2. **p9 callouts 1-5 and p10 callouts 6-9.** All match. Good that numbering continues across the two pages.
3. **p10, callout 6 vs p13.** Callout 6 says a tone change "shows in your copy of the tracker only; it is not written into the workbook." But the Edit story form (p13) has a Tone field, and p13 says form edits "go into the workbook with the next update". A reader cannot tell whether changing tone through the form reaches the workbook. Change: say which it is in both places (for example "To change the tone for everyone, use Edit details; the Change menu is a personal note"), after confirming in the save program which fields the edit path writes.
4. **p11, full-page view screenshot.** Prints at about 5 pt throughout; nothing in it is readable on paper. Since the caption's point is only "details on the left, the story on the right", shrink it to half width and let "Edit details" and "View original" text sit beside it, which also pulls the p12 screenshot back onto p11.
5. **p12, highlight box clips the text.** The orange box's left edge overlaps the "V" of "View original" (checked at 300 dpi). Move the box 4-6 px left or pad it.
6. **p13, Edit story form.** Labels print at about 6 pt and the two-line note at the bottom of the form at about 5.5 pt, yet the caption says "The note at the bottom says where the change goes" — the reader cannot read it. Change: quote the note in the caption, or add a zoomed crop of the two buttons and the note.
7. **p13, bullet 3 "Edits fill empty fields only".** This is the most important rule on the page and it is right. But p27 then says "fix any of them [items that need a person, including '7 dates to check'] with Edit details or in the workbook". A date to check is already filled in, so an Edit-details change to it will not reach the workbook (the workbook keeps its own value; the preview on p26 shows exactly this happening to s01674). Change p27 to: "Fix a wrong value in the workbook itself (Excel, then Repairs > Accept the workbook as it is now); use Edit details only to fill something blank." See A8.4.

### A7. Data and the five list tabs (p14-p20)

1. **p14, "The brief" screenshot.** The bullets print at about 7.5 pt; acceptable. Add "Written from the stories below. Copy it into an email or memo." into the caption since that subline is 5 pt.
2. **p15, chart crop too tight at the bottom.** "▶ Chart options" is cut in half at the bottom edge, and "Show the numbers", which the caption names, is not in the picture at all. Change: extend the crop to include both links, or remove them from the caption.
3. **p15, paragraph listing the sections.** Fourteen section names in one 5-line sentence. Change: a two-column bulleted list, one section per line, with the one-line "Wherever you see a number or a bar, click it" kept as the last sentence.
4. **p16, Reporters table.** Last row cut mid-cell ("of Greater Los"). Crop at a row boundary. Same on p17 (Outlets table, last row cut; reporter page cut at "Outlets 2") and p19 (Bills table, sixth row half visible). If the cut is meant to show "the list continues", fade it or crop cleanly; a half row reads as a mistake on paper.
5. **p17, reporter page.** The labels ("Outlets", "Title", "Top issues", "Bills", "Press releases", "Stories", "Tone average"...) print at about 5.5 pt, so the caption is doing all the work. Change: show the page at the width of one column (the panel is narrow in the app anyway) so it prints at about 8 pt.
6. **p18, Press releases chart.** The x-axis year labels are cut in half at the bottom edge (checked at 300 dpi). Extend the crop by 12 px.
7. **p18, text under the chart.** "A release's page has Read release (the release text), who it was joint with, and the stories related to it" is clear. Define "picked up" the first time: it is used on p18 ("80% picked up") before its definition in the next paragraph.
8. **p19, Bills.** Text and screenshot agree (Filters badge 1, "Budget Act bills Left out" tag). Good. "LegInfo" in the text should be "LegInfo (the Legislature's bill website)".
9. **p20, Story travel.** Caption mentions "a map and a list" that are not shown; fine, but say "(not shown)".

### A8. Manage, Tracker files, Bring in an update (p21-p28)

1. **p21, two Manage screenshots.** The Data checks shot is half empty white space (crop too loose); the Update log shot's entries print at about 6.5 pt. Change: crop Data checks to its five rows; put the four-part table (now alone on p22) under the screenshots on p21.
2. **p26 and p29, the program says "1 conflicts left for Sammy".** The preview text hard-codes a first name. In a guide for staff, a reader asks "who is Sammy?" (and the plural "1 conflicts" and "1 rows" read as typos). Change: in the guide, add to the p26 caption "Sammy is the keeper; 'conflicts left for Sammy' means cells the save did not decide." Better: change the program message to "left for the keeper" and recapture (outside this audit's scope, but worth a note to the builder).
3. **p25, step 4 does not match the screenshot.** Steps 1-4 end with "Press Save, or Do not use this update", but the only screenshot on the page shows a different pair, "Use it anyway / Do not use it", from the warning state, and the warning is explained only after the steps. Change: make the warning its own step: "2a. If a yellow warning says the update was made from a different version of the workbook, read it; press Use it anyway to go on, or Do not use it." Then step 3 "Read the preview (next page)", step 4 "Press Save or Do not use this update". The Update station guide (p9) already does this correctly.
4. **p27, "fix any of them with Edit details or in the workbook."** See A6.7: contradicts "Edits fill empty fields only" (p13). Change as proposed there.
5. **p27, "When you press Save", step 3.** "Make a refresh file for your colleagues (step 4), and a new 'for Update' file before the next Update station run" is the right reminder. Make it an orange callout like p24's "Make a new one after every save", so it is not lost at the end of a numbered list.
6. **p28, spliced screenshot.** The dashed "cut here" line runs through the middle of a line of text ("Your edits made in this tracker, saved together with it: 1" is half visible above the dashes; checked at 300 dpi). Change: cut at line boundaries, with 6-8 px of white above and below the dashed rule; or show the top and bottom as two separate crops with one caption.
7. **p28, result text names "db\\_applied\\edits".** Leave it in the screenshot but add to the caption: "('db\\_applied\\edits' is a folder inside data; you never need to open it)."
8. **p26, intro paragraph.** Good. Add after "rows added to each tab of the workbook": "(Coverage, Originals, Removed, Unlinked print pages)" so the names in the screenshot have a home.
9. **p23, "The four steps" sidebar.** Clear. Add to step 2 "(keeper only)" and move the "fingerprint" definition to the "Words used in this guide" table on p1 (it is used on p23, p24, p25, p28, p31).

### A9. Save my edits, Refresh files, Repairs (p29-p33)

1. **p30, step 3 and p13 (Update guide): "Pass it to the others by the shared drive, email or Teams."** The screenshot right below shows the first refresh file is 855.7 MB. No office email will carry that, and Teams may refuse it too. Change: "Pass it to the others by the shared drive. A later (short) refresh file is small enough for email or Teams; the first, full one is not."
2. **p30, reader steps.** Good and short. Add step 4: "If the page says 'That is not a .zip file', drop the zip itself, not an unzipped folder" or point to p36.
3. **p31, reader panel.** The crop is good and legible. Caption says "no Bring in update, Save my edits or Make refresh file", which is right. Add that readers also have "Make 'for Update' file" but do not need it.
4. **p32-p33, Repairs.** The table on p32 and the screenshot on p33 say the same thing twice, with the screenshot's button names differing slightly from the table ("Make a full refresh file (for a new person)" vs "Make a FULL refresh file"; "Rebuild the tracker page" vs "Rebuild the page"). Change: keep the table, use the button labels exactly as printed on the buttons ("Accept the workbook as it is now", "Make a FULL refresh file", "Rebuild the page", "Rebuild saved copies"), and shrink the screenshot to half width beside it on one page.
5. **p32, "Accept the workbook as it is now".** Add the warning the program itself shows (checked in source): "If another person edited it, their edits become part of the tracker."

### A10. Installing, Where your files live, Problems, Cheat sheet (p34-p37)

1. **p34, step 4.** "drag the folder you use now ... into the black window and press Enter" is the one step a non-programmer may not picture. Add: "(dragging a folder onto a black window pastes its location as text; that is all the installer needs)".
2. **p34, "By hand, if the installer won't run", step 3.** "Copy the whole data folder from your old tracker folder into the new folder, replacing the empty one there" — for an 855 MB library this takes minutes; say so, and say "Move, do not copy, if you are short of disk space" only if that is safe. Also note that `role.json` lives in data, so the role comes along.
3. **p35, table.** Matches the source layout (checked). "db: Your notes, saved views, tone changes and waiting edits" quietly confirms A6.3 (tone changes stay local). Good.
4. **p36, Problems and fixes.** Every quoted message matches the program text (checked in source). Two additions: "Save is grayed out" (it is in the Update guide's table, p14, but not here) and "The page says 'No workbook yet'" (a reader copy that was unzipped fresh; the READ ME FIRST file covers it).
5. **p37, cheat sheet.** Matches the style guide's two-box layout. Add "Save my edits" to the Keeper box as an optional step, and page numbers in each line ("p24") since this is the page people will tape to the monitor.

---

## B. Update station guide (`AJG Tracker - Updating with the Update Station.pdf`)

### B1. Cross-cutting

1. **Two step-numbering systems collide.** The guide numbers the job 1-7 (p1 table; page kickers "STEP 3 · IN THE UPDATE STATION", "STEP 5", "STEP 6"), but the station's own page is labelled Step 1 / Step 2 / Step 3, and every screenshot shows those labels: the guide's Step 3 page shows a box headed "STEP 2 Update" (p5-p6), the guide's Step 5 page shows "STEP 3 Download the update folder" (p8), and the station's help text in the p4 screenshot says "Download the folder in step 3". Change: keep the station's numbers as the only numbers. Name the guide's parts by place instead: "On the PC: make the file", "Station Step 1: load the file", "Station Step 2: Update", "Also: add PDFs", "Station Step 3: download", "On the PC: bring in and save", "On the PC: refresh files". Update the p1 table and the p15 cheat sheet to match.
2. **The station screenshots show two different versions of the station.** p3 shows a file named `for_update_0bccc1fc.json` (an old test file; the PC names files `for_update_<datetime>_<fingerprint>.json`, as p2 and the source say), with 3,707 stories; p5's checklist says "Save them in the tracker" while p6's says "Keep them for the update folder" (the current label; checked in source). Change: recapture p3 and p5 from the published station with a real for-Update file so the file name matches p2 and the checklist matches p6.
3. **"Claude" and "TinyFish" are used from p2 on without definition.** p2 says "TinyFish is the free web search the station uses", good; do the same for Claude in the first sentence that uses it ("Claude, the AI that reads each result, ...") and add both to a short word list on p1, since this guide has none.
4. **Footer "Updating with the Update Station".** See A1.7.
5. **Style match.** Cover, kickers, headings, navy and orange callouts, tables, captions, footer and cheat sheet all follow the style guide. Heading and kicker sizes are the same as the User Guide's, slightly larger than the style guide's (A1.6).

### B2. Cover, How the job works, Before you start (p1-p2)

1. **p1, table step 4 "Add PDFs (optional)".** Good. Add "(NewsBank: see the separate NewsBank Download Guide)" so the three printed guides reference each other on page 1.
2. **p1, "Open the Update station" button plus URL.** Right call to print the URL under the button (the style guide prints only the button). The URL is in light grey at about 8 pt; make it the normal link blue so it survives a photocopy.
3. **p2, step 4.** "Allow Claude and TinyFish for the station page the first time (see 'If something is blocked' in the station's How it works)" sends a first-time user into the app to find help. Put the two-line answer here instead (it is already on p14: Permissions menu, including sending pictures; TinyFish connected in Settings > Connectors).
4. **p2, screenshot and callout.** Identical to User Guide p24: good consistency.

### B3. Open the station and load the file (p3-p4)

1. **p3, second screenshot.** Stale file name (B1.2). Also "File made Nov 3, 2026, 5:10 AM" is two days before the guide's other screenshots; fine once recaptured.
2. **p3, step 3.** "The search starts the day before the newest story, so there is no date to pick" is exactly the right reassurance. Keep.
3. **p4, callouts 1 and 2.** Match. The How it works window is legible (about 8 pt). The caption lists "Automatic mode", which is first explained on p7; add "(p7)".

### B4. Press Update database (p5-p6)

1. **p5, confirm-box screenshot.** Enlarged to about 14 pt, with the page behind it showing as grey slabs and a stray "K" at the left edge. Crop to the white dialog only and show it at half width beside the steps.
2. **p5, caption "Stop ends the run early."** No Stop button is in the picture (the station does have one during a run; checked in source). Either extend the crop to include it or move the sentence to "If the run ends early" on p6.
3. **p5, step 3 vs screenshot.** The step lists "keep them for the update folder"; the screenshot's fourth line says "Save them in the tracker" (B1.2). Recapture.
4. **p6, screenshot line "LegInfo check skipped".** Unexplained. Add to the caption: "(LegInfo is the Legislature's bill site; the check looks up bill numbers and is skipped in a test run)" or crop it out.
5. **p6, "What the search does for you".** Repeats the p4 How it works text almost word for word. Keep it here (it is where the reader needs it) and shorten the p4 screenshot to the first two paragraphs.

### B5. Add NewsBank and ProQuest PDFs (p7)

1. **p7, step 1: "Where the station's short How it works text differs (it says to sort newest first), follow the Download Guide."** The station's text now says "Sort by: Oldest" (checked in `station/src/station.html`), so this sentence is out of date and, worse, tells readers the program's own help is wrong. Delete it.
2. **p7, step 1.** "It says to start one week before the newest story in the tracker; the station shows that date in Step 1 as Newest story." Good cross-reference to the NewsBank guide's p4. Keep.
3. **p7, the three bullets after the screenshot.** "A page it can't place goes to 'Unlinked print pages' in the workbook" is important and should also appear in the User Guide where that tab is first named (A8.8).
4. **p7, screenshot.** Legible; "Add to the update" is greyed out in the picture. Say in the caption "(the button wakes up once a PDF is dropped)".

### B6. Download the update folder (p8)

1. **p8.** Both screenshots are legible and match the text (file name pattern, "_v2", "Download the last one again"). Good page. Only nit: the second screenshot's grey detail line ("71 KB · 1 files · made from workbook 0bccc1fc...") prints at about 6.5 pt; it is not needed.

### B7. On the PC: bring in, preview, items, after the save, refresh (p9-p13)

1. **p9-p13 duplicate User Guide p25-p30** with the same screenshots. That is fine for a stand-alone printed guide, but the two texts have drifted: p9 handles the warning as a step (correct), User Guide p25 does not (A8.3); p11 says "check them afterwards and fix any with Edit details" (same problem as A6.7); p13 says email for the 855 MB file (A9.1). Change: fix all three the same way in both guides, and consider making these pages a shorter "see the User Guide, p25-p30" with only the warning and the Save button shown.
2. **p10, second bullet.** "The tracker compares the article texts to make the final call on what is a reprint, and gives the new files their final numbers" is the clearest sentence either guide has on reprints. Copy it into the User Guide p26.
3. **p12, "The line at the top of the page says 'Last updated' with today's date".** True (User Guide p4 shows it). Good.
4. **p13, step 4.** Good. Add "Close Excel first" for the colleague, as the User Guide p30 does.

### B8. Problems and fixes, Cheat sheet (p14-p15)

1. **p14.** Good table; all quoted messages match the program (checked). Add one row for the most likely first-day problem: "The station page asks me to sign in" → "Sign in to claude.ai with the office account; the keeper has it."
2. **p15, cheat sheet "On the PC" step 2: "(After the station)".** Reads oddly on a card. Change to "When the zip is downloaded:". Right-hand box: rename to "In the Update station (its Steps 1-3)" per B1.1.
3. **p15, "Remember" callout.** Good; it is the three rules that matter.

---

## C. Inconsistencies between the two guides

1. Numbering: the Update guide's Steps 1-7 vs the station's Steps 1-3 vs the User Guide's Tracker files steps 1-4 (B1.1). A reader holding both guides meets three "Step 2"s.
2. The warning on bringing in an update is a step in the Update guide (p9) but an afterthought in the User Guide (p25) (A8.3).
3. "Fix with Edit details" advice (User Guide p27, Update guide p11) vs "Edits fill empty fields only" (User Guide p13) (A6.7).
4. Footer titles and the capital "Station" (A1.7).
5. The Update guide has no word list; the User Guide's p1 list defines "Update station", "Update folder", "Refresh file" and "'for Update' file", which the Update guide uses from its first page. Add a four-row list to the Update guide's p1 or a line "Words are defined in the User Guide, p1."
6. The User Guide says the for-Update file "takes about a minute" (p24) and so does the Update guide (p2); both match the program text (checked). Good.

## D. Things that are risky to tell a user (summary)

1. Email an 855 MB refresh file (User Guide p30, Update guide p13).
2. Fix "items that need a person" with Edit details (User Guide p27, Update guide p11): the change will silently stay local for any filled cell.
3. "The station's help says to sort newest first; ignore it" (Update guide p7): no longer true, and it erodes trust in the program's own text.
4. "Press Save, or Do not use this update" as step 4 under a screenshot showing "Use it anyway / Do not use it" (User Guide p25): the user may press "Use it anyway" thinking it is Save.
5. "Restart the PC and try again" for the port-in-use message (User Guide p36): on a government PC a restart can take ten minutes; add "First check for another black tracker window (the line above it) and close that."
