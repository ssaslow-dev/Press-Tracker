# Extract of the OLD Project handoff ("claude/AJG Project - Handoff Memory.md", written 2026-10-26), with main's notes
Merge whatever is still true into HANDOFF.md, as background/history and inventory. Mark anything superseded. DECISIONS wins on conflicts.

## Still-true background
- Earlier chats (Oct 16–23):
  - "Jesse Gabriel news mentions" built Jesse_Gabriel_Mentions.xlsx (742 stories) from web search, ProQuest exports and deep dives.
  - "Chrome mentions" grew it to 1,265+ and saved reader-view HTML to a "Gabriel press archive" folder (~840 files named "Date - Publication - Headline", under ~/Desktop/Tracker library/), plus 488 ProQuest PDFs.
- Sites that block Claude, so don't work around them: LA Times, Politico, NYT, WaPo, Sac Bee, Center Square, Daily News, SF Chronicle, OC Register.
- NewsBank download (Oct 24–26): 6,539 results for "Jesse Gabriel" in 329 batch PDFs of 20 with APA citations.
  - Files: unnumbered, (1)–(100), then 228 named "NewsBank Multiple Articles - <timestamp>.pdf"; (92) duplicates (90).
  - Companion workbook "Gabriel Print Editions - Companion.xlsx" in ~/Documents/Gabriel press PDFs. Tabs: Print Editions (AJG-P#### codes, 2,133 pages after removals P0457/P1126/P2136/P2137), All PDF Items, Removed, About. Codes never change and are never reused.
  - His pre-office coverage is kept: ASUC president 2002–03, DACA lawyer 2017, LA Jewish Federation / Jewish Journal.
- pdftotext drops the hyphen after the 7-digit julian date in NewsBank docrefs; reinsert as %40\d{7}-HEX16.
- NewsBank text format: begins "Author: … Section: … N Words / OpenURL Link" and ends with a copyright line plus "Citation (apa Style)". Key texts by "PDF name#position".
- AJG Combined Coverage.xlsx and "NewsBank vs Tracker - Crosswalk.xlsx" are superseded. A TinyFish chat once wrote lookups into Combined by mistake; don't build on it.
- Master-sheet build phases C–F (Oct 26):
  - Article ID per row and Story ID per story; NewsBank outlet style ("Sacramento Bee, The"); Medium uses the tracker's categories; bylines are people only.
  - NewsBank data wins; the tracker fills blanks.
  - Web+Print merges (217 pairs; Print Article ID / Print date / … columns); Web+Print editions are exempt from the reprint rule.
  - ID prefixes nb-/pq-/ws- (ts- renamed ws-); now the library naming in DECISIONS.
- Workbook rebuild styling: header navy 132A4A, white bold; freeze panes at C2; autofilter; column widths. Edit cells in place with openpyxl so formatting survives. Always rebuild the Originals tab from Coverage after a change.
  - Font colors historically marked provenance (blue/green/orange/red). A later DECISIONS line says new writes are BLACK; check DECISIONS before applying colors.
- Clutter rule: set aside only certain clutter (NewsBank header/citation block, the tracker's "Saved YYYY-MM-DD" header, "Text of the ProQuest PDF…", "Print edition: pages…"). No broad phrase triggers, since they delete real syndicated text.
- Sammy-style rules from the old doc:
  - "Do only the ones you are 99% sure on."
  - Ask before expensive or ambiguous work; he often asks "how long would it take" first.
  - Use a scalpel.
  - If something is obviously a mistake you may break a rule to fix it, but say so.
  - His latest instruction wins.
  - No internet research to fill gaps unless he asks.
- TinyFish costs: search and fetch are free on his plan; browser automation is about $0.016 per step; deep research is $2 per run, so avoid it.
- The file-transfer bridge can return cached old copies. Stage, then confirm it's current (sha/size); commit from a NEW uniquely named output file with expectedMtimeMs; verify the sha on the Mac with device_bash shasum -a 256. (README rule 7 covers this; check it.)
- Print pages carry no text. About 1,471 NewsBank print pages had no Story ID as of Oct 26; options were a "Likely article" column or reading the pages via Chrome. Check DECISIONS/BOARD for the current status. Clipping workflow: Project memory newsbank-print-clipping (copied in handoff_ctx_main.md).

## Superseded by later work (mention only as history)
- The old tracker copy artifact dc44cdfe… and its trigger trig_01Wg3NS6hNteZq4hwQTRcDay.
- The "reprint rule not yet applied" status: it was applied later (see DECISIONS: 25-word runs ≥90% of both texts, 90-day text window, etc.).
- The tracker rebuild plan: done (v19/v20).

## New memory facts (2026-10-28)
- Sammy is moving jobs and plans to copy the project to a new Claude account later; the handoff is not happening yet.
- He wants the handoff documentation kept continuously updated as the tool changes.
