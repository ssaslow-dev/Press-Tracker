# Project memory files of the old account (copied 2026-10-28 by agent-handoffkit)

The new account has no memory. These are the two project memory files of the old "AJG Mentions Database" Project
(memory paths /projects/01a1413e-6231-75bd-9079-fa4237b5738f/areas/…), verbatim. Re-create them as memory on the new account.

## areas/ajg-coverage-workbook.md
description: Which Gabriel press-coverage spreadsheet Sammy means by "the main sheet"; read before updating coverage workbooks
aliases: AJG coverage sheet, main excel sheet, AJG Coverage - NewsBank

- [stated] "The main excel sheet" / "the AJG coverage sheet" means AJG Coverage - NewsBank.xlsx (in ~/Documents/Gabriel press PDFs), not AJG Combined Coverage.xlsx
- [stated] Since 2026-10-27 the working master copy lives in ~/Desktop/Tracker library/ (moved there to work off of it); the Documents copy is no longer updated
- [stated] Moving jobs; plans to copy the AJG tracker project to a new Claude account later (handoff not yet happening as of 2026-10-28)
- [stated] Wants the project's handoff documentation kept continuously updated as the tool changes

## areas/newsbank-print-clipping.md
description: Process for clipping NewsBank print-edition pages for the "Jesse Gabriel" search and the companion spreadsheet; read before resuming clipping
aliases: Gabriel print clippings, NewsBank clipping, AJG print editions

- [stated] asked to remember this clipping process; paused 2026-10-25 after AJG-P0002 (resume at AJG-P0003)
- [stated] Goal: clip the entire article Gabriel is featured in on every NewsBank print-page result not saved in the batch PDFs; name each clip by its unique code; keep a companion spreadsheet with all metadata (dates, pages, bylines, links, citation) so clips can be matched to the PDFs
- [stated] Files live in ~/Documents/Gabriel press PDFs: batch PDFs "NewsBank Multiple Articles (N).pdf" (20 results each, APA citations), clips AJG-P####.pdf, spreadsheet "Gabriel Print Editions - Companion.xlsx" (tabs: Print Editions, All PDF Items, About)
- [stated] Codes: AJG-P#### assigned in PDF order (unnumbered file = 0, then (1), (2)…) by position in each PDF; later batches get the next codes; existing codes never change. First build covered PDFs 0–50 = 407 print pages
- [stated] Spreadsheet columns: Source with trailing parenthetical removed; separate Outlet location column (city, ST; city taken from NewsBank's city line when the paper lists only a state); Page column next to them
- [stated] Spreadsheet updated from new PDFs on request: keep existing rows/codes untouched, append new unique print docrefs with next codes, flag re-downloaded duplicates in All PDF Items Notes. After (100) Chrome names batches "NewsBank Multiple Articles - <timestamp>.pdf"; order them by time after (100). Download complete: 329 PDFs (unnumbered, (1)–(100), 228 timestamped) = all 6,539 unique results; 2,137 print pages (AJG-P0001–P2137); (92) duplicates (90)
- [stated] Asked to eliminate anything clearly not the correct Jesse Gabriel: removed rows go to a "Removed" tab with reason; removed print codes are retired, not reused (2026-10-26: P0457, P1126, P2136, P2137 removed; 2,133 print pages remain). Keep his pre-office coverage (UC Berkeley ASUC president 2002–03, DACA lawyer 2017, LA Jewish Federation / Jewish Journal)
- [stated] Print pages in PDFs: title "Paper: Page N", only citation + docref=image/v2… link. pdftotext drops hyphen after the 7-digit julian date in docrefs; reinsert (%40\d{7}-HEX16). Open via CA State Library proxy host infoweb-newsbank-com.castatelib.idm.oclc.org
- [stated] Headline/byline for print pages come from the matched full-text article (same date + page; High = same paper, Possible = sibling chain paper) or, if none, are read off the clip
- Clip workflow (Claude in Chrome, ~2 min per clip):
  1. Navigate to proxied docref; JS: click .actions-bar__button--search, then "Search Page", focus .nbcore-openseadragon__highlight-search-terms; type "Gabriel" with real keystrokes + Return (form requestSubmit breaks the page; JS-set value returns 0 matches). Highlights = .nbcore-openseadragon__highlight-instance
  2. Set window.__clipName='AJG-P####.pdf' and hook HTMLAnchorElement.prototype.click to set this.download=__clipName (this names the saved file); click .actions-bar__button--clip then .actions-bar__print_ha--clip (Select Clip) to get the box; scroll canvas into view
  3. Click Fit to Screen with a real click (~1313,92); JS fit is ignored
  4. Screenshot, find article containing the highlight; drag .selection-box corner handles with real drags. Drags move ~0.8 of the mouse delta: aim = start + (target − start)/0.8; verify with getBoundingClientRect and nudge
  5. Click Download PDF; in modal check input.multidocs__cite--checkbox, set select to APA, JS-click button.modal-document-citation__submit; file lands in the folder as the code
- [stated] Don't override iframe src or other request hooks — that blocked the download
- [stated] A separate chat's batch download run shares the NewsBank session; clipping does not touch result selections
- [stated] Plans to eventually combine the NewsBank companion spreadsheet data with the AJG Press Coverage Tracker artifact's data
- [stated] 2026-10-27 update: clipping now goes into the Tracker library (not AJG-P codes) via CA State Library NewsBank links; always save the entire page he is on plus every page the article spills over to (no selection box); OCR on; OCR near-miss reprint matches decided automatically
