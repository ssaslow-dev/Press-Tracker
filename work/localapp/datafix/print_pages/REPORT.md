# Unlinked print pages: which tracker story is each one? (check only, nothing applied)

Data: workbook copy `0bccc1fc` (2026-11-03), tab "Unlinked print pages" (1,443 rows) against Coverage (8,222 rows). Nothing in the workbook, library or tracker was touched. Files here: `match_print_pages.py` (the script), `proposals.csv` (one line per proposed change, 6,549 lines), `details.csv` (one line per page with its class and evidence), `summary.json`.

## What these 1,443 rows are, in plain words

Each row is a NewsBank "full page" record: outlet, date, page number and a citation such as `(2026, October 4). Inland Valley Daily Bulletin (Ontario, CA), p. 15.` That is all. **None has a headline, an author, text or a clipped PDF** (the "Full Page" headline you may remember is only the station's label for new ones; the 1,443 old rows have a blank Headline and the citation holds no headline). The library has no scans or OCR for any of them (the 31 page PDFs in `_original_pdf/2026` belong to other, already-linked rows). So **the text test (reprint_rule) could not be run on a single page**. Every match below rests on outlet + date + page + how the story was syndicated. That is why almost nothing is "certain".

By year: 2023 (395), 2024 (302), 2025 (276), 2026 (223), 2020 (104), and 100 older. 837 are California papers. Mostly Sacramento Bee, the SCNG papers (Daily News, Daily Breeze, Press-Telegram, Press-Enterprise ...) and McClatchy "Today's Edition" e-editions.

## Counts

| Class | Meaning | High | Medium | Low | Total |
|---|---|---|---|---|---|
| A | print edition of a row the same outlet already has | 10 | 22 | 25 | 57 |
| A-jump | probably the inside (jump) page of a front-page story the outlet already has | 0 | 138 | 0 | 138 |
| B | reprint of a tracked story at a paper with no row | 26 | 90 | 161 | 277 |
| C | probably not coverage (election-results pages) | 0 | 0 | 109 | 109 |
| D | unsure | 0 | 0 | 862 | 862 |
| | | 36 | 250 | 1,157 | 1,443 |

Only 36 pages (2.5%) reach high confidence, 286 (20%) are high or medium. Over half (862) cannot be matched on the evidence at hand, mostly because the paper has no row at all near the date.

How high / medium / low were decided:
- High, A: same outlet, same date, and the same page number as the row's own print record. High, B: three or more sister papers of the same chain ran the story on that very date, it is the only candidate story, and this paper has no row.
- Medium: one candidate story, date agrees (A: web row dated the same day or the day before; B: at least one sister paper on that date; A-jump: the row's story is on p.1 and this is a later page that same day, only one story at the paper).
- Low: several candidate stories, or the dates only agree within 3 days.

## A. Print edition of a row the outlet already has (57 pages, 57 distinct rows)

**High (10).** Each is a second NewsBank record for the very page the tracker row already carries (same paper, same date, same page). The rows lack their print-page link, so these records supply it. Proposed: fill the three blank link/citation cells on the row, retire the Unlinked row (proposals.csv, class A/high).

| Unlinked | Outlet | Date | Page | Tracker row (story) |
|---|---|---|---|---|
| 05481 | Sacramento Bee | 2026-09-08 | 4 | 00206 (s00057) |
| 05561 | Sacramento Bee | 2026-06-14 | 11 | 00470 (s00114) |
| 05602 | Sacramento Bee | 2026-05-29 | 4 | 00498 (s00123) |
| 05693 | Sacramento Bee | 2025-10-20 | 10 | 00896 (s04326) |
| 05800 | Merced Sun-Star | 2025-08-17 | 16 | 01146 (s00309) |
| 05902 | Sacramento Bee | 2025-01-31 | 1 | 01499 (s00415) |
| 06027 | Buffalo News | 2024-12-04 | 2 | 01722 (s04384) |
| 06097 | Modesto Bee | 2024-10-02 | 3 | 01827 (s00510) |
| 06136 | Modesto Bee | 2024-07-04 | 6 | 02074 (s02960) |
| 06144 | Sacramento Bee | 2024-06-30 | 7 | 02081 (s00593) |

**Medium (22), low (25).** The outlet has a web-only row for the story near the date and no print edition yet. Proposed (web + print one-row rule): Print Article ID = the page's Article ID, Print date, Page, the three NewsBank print-page cells, Old Print Article ID, all blank-only. One catch: on 35 of these rows Edition says "Web" (not blank). Changing it to "Web + Print" is not a blank fill, so those lines are marked `NOT A BLANK` in the evidence and need a recorded decision (or the Edition left alone). Example: 06323 Mercury News 2023-09-27 p.5 with row 03097 (s00882, web, 09-28); 06520 East Bay Times 2023-04-27 p.32 with row 03649 (s01025).

## A-jump. Inside pages of stories the outlet already has (138 pages, medium)

420 pages are for a paper and date where the tracker already holds that paper's print edition of a story (at another page). In 138 of them the row's story is on page 1 and this is a later page of the same issue, the paper's only such story that day: almost certainly the jump page (Daily News, Pasadena Star-News, Daily Breeze, Sun, Sacramento Bee ...). Example: 06500 Pasadena Star-News 2023-05-30 p.7, row 03543 (s04508, p.1). No cell is filled; the proposal is to keep the page and, once clipped, save it as the row's print original `_original_pdf/<year>/<row Article ID>_p<page>.pdf` (PRINTORIG-v1). The other 282 stay D (the row's page is not 1, or the paper has several stories that day).

## B. Reprints at papers with no row (277 pages, 72 stories)

The paper has no row for the story, but sister papers of the same chain (SCNG, Bay Area News Group/MediaNews, McClatchy, Lee, Gannett, Tribune/Hearst) ran it around that date. Proposed: a new Coverage row (same Article ID as the page, moved from the Unlinked tab) with Story ID, Original or reprint = Reprint, Data Source Newsbank, Date (page date), Date source "print edition", outlet details copied from the page row, Medium Newspaper, Format Print, Edition Print, Page, the three NewsBank print-page cells. Headline is copied from the story's Original and marked "replace at clip" (the page has none). 12 of these pages are dated before the story's current Original; the save program's originals order must decide any swap.

**High (26)**, every one with 3+ same-chain papers on the page date:
- 06159 / 06161 / 06163 / 06165 / 06166 / 06167: Inland Valley Daily Bulletin, Los Angeles Daily News, San Gabriel Valley Tribune, Press-Enterprise, The Sun, Whittier Daily News, 2024-06-23, story s00610.
- 05683 to 05686: Daily News, Pasadena Star-News, SGV Tribune, Whittier, 2025-12-14 p.4, s00206 (Bass re-election).
- 06034, 06038, 06039, 06040, 06041: Marin IJ, Santa Cruz Sentinel, Daily Democrat, Denver Post, Monterey County Herald, 2024-12-03, s00480.
- 06282, 06284, 06285 (s04461, 2023-11-19); 06059, 06060 (s00492, 2024-10-24); 05458, 05461 (Daily Camera, Daily Times-Call, 2026-09-20, s00044 the AP story); 05798, 05799 (Fresno Bee, 2025-08-17, s00309); 06378 (Marin IJ, 2023-09-10, s00930); 06716 (Oroville Mercury-Register, 2021-05-29, s01389).

Medium (90) and low (161): same pattern with fewer sister papers on the exact date, or a one-candidate wire story (AP) in an out-of-state paper (low). Most common stories: s01052 (AP Peeps story, 10 pages), s00764, s00427, s00610, s00480.

Caution: without text, "the sister papers ran it" does not prove this paper ran it on that page; the page may carry a different Gabriel mention. Under the existing rules a Reprint needs the text test, which only clipping can supply (clip, OCR, test, as the 28 earlier clips did). Apply B/high only if Sammy accepts this evidence; otherwise treat B as a clip-priority list.

## C. Probably not coverage (109 pages, all low)

All on the day after a California election (2020-11-04: 79 pages; 2018-11-07: 21; 2026-06-02: 9), from papers with no tracker story that day, when dozens of papers print results tables that list candidates. Results tables are not coverage (INCL-v1). Stay in the Unlinked tab. Clip one or two to confirm.

## D. Unsure (862 pages)

- 361 papers with no row at that paper, a sister paper or a wire story within 3 days (many out of state). 206 of those sit in big same-day clusters from one chain (e.g. 29 McClatchy e-editions on 2024-12-12, 2024-12-08, 2024-10-20, 2025-07-02, 2025-09-16): almost certainly one syndicated piece each, whose Original is not in the tracker. Clip one page per cluster and the rest can be linked.
- 282 same paper and date as a tracker row that already has its own print page (different page): jump page or another article.
- 165 with several candidate stories at sister papers (e.g. 5 stories on 2023-09-27).
- 54 others (a paper already in the story on a different date, or a second page for a row that another page already matched).
- The older "Likely counterpart" column agrees with this picture: 449 rows said "same paper + date" (my result: 41 A, 138 A-jump, 269 D, 1 B); 707 said "none" (452 D, 169 B, 86 C).

## The East Bay Times / Mercury News pages (audit issue 1)

Those two pages (Nov 1 and Nov 3, 2026, reprints of s01903) are newer than this workbook copy and are not in the Unlinked tab, so they are not in these counts. They show what text would settle: neither paper is a sister of the LA Times, so the sister-paper test here could not have found them; only the page image (or OCR) can. They are the model case for B once clipped.

## How this would be applied on switch-over day

1. Re-run `match_print_pages.py` against the real workbook then (new rows, new IDs and fills since 0bccc1fc change the matches). Nothing in proposals.csv is applied from this copy.
2. Sammy decides per class: A/high and B/high first (36 pages); A medium/low and the 35 "Edition Web" lines need his OK; A-jump, C and D wait for clipping.
3. Preview through the save program (all saver checks, blank cells only; each new Reprint row gets the text test once clipped, otherwise it is held back or marked unverified). Moves from the Unlinked tab keep their Article ID, so the ID sequence is untouched.
4. Backup of the master first, staged uniquely named file, commit, verify sha256, Excel closed (rule 7). Print originals for A-jump pages go to `_original_pdf/<year>/<id>_p<page>.pdf`, add-only.
5. One-writer rule: this is a separate write from the first real save.

## Top findings

- 1,443 pages, and none has a headline or text: the match can only be by outlet, date, page and chain. 10 are certain duplicates of pages the tracker already holds (fill 3 blank cells each); 26 are very likely reprints by chain; 138 are probably jump pages.
- 109 look like election-results pages (not coverage), 862 cannot be placed. The biggest single time-saver is clipping one page per same-day chain cluster (about 10 clusters, over 200 pages).
- 35 of the A proposals would change a filled "Edition" cell, so they need a decision, not a blank fill.
