# NewsBank header fills: what the saved copies can fill in (check only, nothing applied)

Folder note: `work/localapp/datafix/nb_fills/` already held another builder's files, so this check is in `nb_fills2/`.
Read-only on the workbook copy (`wb_0bccc1fc.xlsx`) and `data/library`. Nothing was written anywhere else.

## What was checked, in plain words

3,763 Coverage rows have a NewsBank PDF as their saved copy (File name or File name 2). All 3,763 files were found and read (4 processes in parallel, 3,964 PDFs including second copies).

Every saved copy still carries NewsBank's header block, inside the text, in the older layout: `Month D, YYYY | outlet label`, then `Author:`, `Section:`, `N Words`, `Page:`, `OpenURL Link`. (The newer labelled `Date:/Source:/Word Count:` layout is not in any saved copy yet; the reader handles it anyway.) 28 print-page picture copies have a different top line (`Outlet - Month D, YYYY - page N`, with the city spelled out), which is also read.

Rule followed: only cells that are blank today get a proposal. Where the header disagrees with a filled cell, the filled cell stays and the case is in `conflicts.csv`. A row whose header date is more than 3 days from its Date is treated as a different article and gets no proposals (2 rows: 01579, 02836). Edition checked against the 1,458 rows that have one: the header agrees every time. Section, city agree with filled cells on 99.9% and 100%.

## Counts (cells proposed, nothing applied)

805 rows would get something; 630 of them at high or medium confidence (313 of the 805 are Original rows, the rest Reprints).

| Column | Proposed | Confidence | Note |
|---|---|---|---|
| Section | 11 | high | e.g. `capitol_alert`, `News` copied as NewsBank gives it |
| Author / byline + Author 1 | 290 each | 116 medium, 174 low, 0 high | most blank-author headers carry an outlet or staff name, not a person |
| Author 2-6 | 11 | low | |
| Author title | 418 | 416 medium, 2 low | mostly the credit (CalMatters, Associated Press, JTA), as the sheet already does; only where Author 1 on the row already matches the header |
| Page | 92 | 88 high, 4 medium | from the print copy of a Web + Print row; "A 4" written as "A4" (medium) |
| Print headline | 15 | high | Web + Print rows; headline read from the print copy and checked letter-for-letter against its citation |
| Outlet city | 1 | low | 01917 Tri-County Independent: header says "Pike-Lackawanna-Wayne, PA", a region, not a city |
| Edition | 0 | | see below |
| Print date, Print section, Print word count | 0 | | already filled on every Web + Print row that has a NewsBank print copy |

Not proposed, on purpose: Word count (never blank here), Print Article ID (IDs are assigned only by the save program), Outlet county/state (not asked).

### Why some blank cells cannot be answered from the header
- **Edition (2,049 blank):** NewsBank's label says "Web Edition" or gives a Page number only for some records. The other 2,049 have neither, so the header does not say web or print. (Where NewsBank rows already have an Edition and no clue, it is 22 Web to 11 Print, so a guess would be wrong a third of the time.) A further 539 blank-Edition rows also carry a non-NewsBank copy; left for a person.
- **Page (2,547 blank):** web copies have no page line. Only print copies do.
- **Section (107 blank):** 96 of them have no Section line in the header.
- **Author (797 blank):** 364 headers have an Author line; the rest have none.
- **Outlet city (200 blank):** the header gives only the state, "(CA)", for nearly all of them.

## Examples
- 02757 / 04160 (Lake County Record-Bee), 05376-05381 (Jewish Insider): header "Author:" is the outlet's own name. Listed as **low**, not a person; they would not be applied.
- 00200 `Author: SFVS Staff` -> Author 1 "SFVS Staff" (medium: group byline, an author by the sheet's rule).
- 00008 `Author: Yue Stella Yu CalMatters`: Author 1 is already "Yue Stella Yu"; proposal is Author title "CalMatters" (medium).
- 00110 print copy nb00111o-s00037.pdf: Print headline "Newsom signs bills creating security protections for religious worshipers" (high).
- 00368 Print headline "Trump administration - sues to overturn - two California - gun control laws" (same dashed style the sheet already uses).
- 00419 Page "1A" from `Page: 1A` (high).

## Conflicts (filled cell kept; see conflicts.csv, 193 lines)
- **Page differs: 123.** The filled page disagrees with the header (e.g. 00953 San Diego Union-Tribune: sheet 5, header A1; 00811 Akron Beacon Journal: sheet 19, header B7). In 34 only the section letter is missing from the sheet (5 vs 5A); the other 89 are different numbers. Sacramento Bee has 40 of them. Worth a look by Sammy: these may be wrong pages. They are not fills, so nothing here touches them.
- **Author differs (info only): 46.** Filled Author 1 is a curated name where the header shows only an outlet credit ("Cal Matters", "CalMatters"); mostly fine.
- **Date 1-3 days: 19** (normal under DATES-v1, e.g. 00198 CNN 09-09 vs NewsBank 09-10). **Date more than 3 days: 2** (01579, 02836): all fills skipped on those rows.
- Section differs: 2 (02394 "Current Hot" vs header "Current Hot Topics": the sheet's value looks cut short; 03704 "Health 1199" vs "Health": the sheet has a stray word count).
- City differs from the outlet's other rows: 1 (00852 The Times: sheet London/Frankfort, header Beaver County, PA): not proposed.

How good is the author reading? Run against the 2,762 rows whose Author 1 is already filled: when the check calls a header "high", it matches the filled first author 96.6% of the time (1,314 of 1,360); "medium" 89% (604 of 680); "low" 67% (484 of 722), which is why low is kept out of anything to apply.

## What applying would change in the tracker
- 630 rows (high + medium) get a few more filled cells. No rows are added, removed, re-grouped or re-dated; no reprint, tone or topic changes. The Originals tab (a mirror) is rebuilt after.
- Author 1 / Author title feed the author filter and the Reporters list: about 116 group or staff bylines (SFVS Staff, JNS Staff...) would appear as authors, and the 416 titles attach credits to names already there.
- Page and Print headline show in the story panel for 92 and 15 print copies; Section for 11 rows.

## How it would be applied on switch-over day (not done now)
1. Re-run `build_proposals.py` on the real workbook and library (after Sammy's current master replaces this snapshot; a row that changed in the meantime drops out because its cell is no longer blank).
2. Show the result in a "Switch-over changes" screen step: counts per column, the sample, and the conflicts, with low confidence left out by default.
3. Preview in the PC save program (all its refusal checks), then back up the workbook first (rule 7), write a uniquely named staged file, commit, verify the sha256, Excel closed.
4. Rebuild the Originals mirror; record it in DECISIONS as a fill-blanks-only change.

Sammy's decisions needed: whether group bylines ("SFVS Staff") should fill Author 1; whether to review the 123 page conflicts.

## Files
- `proposals.csv` (1,130 lines: tab, Article ID, column, current value (blank), new value, confidence, evidence). Tab is Coverage; Original rows also feed the Originals mirror.
- `conflicts.csv`, `stats.json`
- Script: `extract_texts.py` (reads the PDFs, parallel), `nbhead.py` (header reader), `build_proposals.py` (rules, run both with `python3 -I`).
