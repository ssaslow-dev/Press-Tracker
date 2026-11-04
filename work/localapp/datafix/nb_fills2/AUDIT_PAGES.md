# Page audit: 123 rows where the sheet's Page disagrees with the saved copy's header

Independent check, 2026-11-04. Read-only on the workbook copy (`wb_0bccc1fc.xlsx`) and `data/library`. Nothing applied.
I re-read every one of the 123 PDFs myself with `pdftotext` (not through `nbhead.py`): all 122 `Page:` header lines match what `conflicts.csv` claims, and each file carries the row's outlet and print date. The 123rd (05434) is a print-page picture, see below.

## Why they differ

**The sheet holds NewsBank's scan position; the header holds the page printed on the paper.** In 120 of the 123 rows the Page cell equals the "p. N" in the row's *print-page* APA citation, which is also the `@N`+1 in the print-page link. That N is where the page image sits in NewsBank's scanned issue (page 19 of the file), not the folio printed on the page (B7). Both describe the same physical page. The two agree only in papers that number pages straight through (Orange County Register, Daily Breeze: 266 rows checked, all agree). They drift apart as soon as a paper has sections: Akron's B7 is the 19th scan because section A has 12 pages. For the Sacramento Bee the drift is not even steady: its front page 1A sits at scan position 1, 2, 5, 6, 7 or 9 depending on the issue (02029, 02290, 02367, 02652, 03173, 03199, 04015, 04502, 04838), so "6" for a Bee story is not a page anyone can find. In the 34 "letter only" cases the number happened to coincide (Bee scan 5 = page 5A) and only the section letter is missing.

Sheet-wide the Page column already mixes the two: 585 cells are scan positions (rows that only had a print-page image), ~710 are printed folios (rows whose article record gave one). The 123 are simply the rows where both exist and disagree. Rows with a scan position and no article record to compare against (about 250, e.g. Bee rows with Page 6 and no `Page:` header) cannot be checked this way; only the page image's own folio could settle them. Noted, not in scope.

Three rows have no print-page link; they are different cases:
- **00923 Bakersfield Californian:** the cell holds "A", the header "A 4". A truncated cell.
- **03089 Herald-Standard, 03757 Express-Times** (and 01266, 02374 Jerusalem Post, 02410, 03933 New York Post): header "03", "007", "05", "017", "003" is the same page with NewsBank's zero-padding. Not a real conflict.
- **05434 Orange County Register** (print-page clip, 2 pages): the article starts on page 1 and jumps to page 9; the saved clip holds both. The sheet says Page 9 and Team note "cont. p. 9", which contradict each other. The clipping convention (05441: Page 1, "cont. p. 7") puts the starting page in Page, so Page should be 1.

No row is a different edition or a wrong header: every header date matches the row's print date, and in all 123 files the article's own APA citation ("p. B7") agrees with the `Page:` line.

## Verdict

Change 117 rows to the page printed on the paper (`approved_pages.csv`, all high confidence, Overwrite yes); keep 6.

| Kind | Rows | Action |
|---|---|---|
| Scan position, different number (e.g. 19 → B7, 6 → 1A) | 87 | change |
| Scan position, section letter missing (5 → 5A) | 28 | change |
| Truncated cell (00923 "A" → A4) | 1 | change |
| Clip with jump: starting page (05434 9 → 1) | 1 | change |
| Zero-padding only (5 vs "05") | 6 | keep |

Sacramento Bee: 40 rows, all 40 changed (22 letter-only, 18 different numbers). Four Arkansas Democrat-Gazette rows get NewsBank's own "1, 3" style (front page with a jump); they are the only comma values in the column. If Sammy prefers one page per cell, use the first number and put the jump in Team note as the clips do.

## Section letters: normalise, but only spaces and zeros

Both "A6" and "6A" are how the papers print it (Tribune, Hearst and Gannett papers letter-first; McClatchy papers number-first), NewsBank copies each paper's style, and the sheet already holds 184 of one and 40 of the other. Do not flip them. Do strip NewsBank's quirks, which no paper prints: spaces ("A 4" → A4) and leading zeros ("A001" → A1, "D002" → D2, "05" → 5). `approved_pages.csv` is written that way (11 rows affected). Follow-ups for the same rule, outside this list: row 00745 (SF Chronicle, Page "A006") and the 11 zero-padded Page fills in `proposals.csv` ("A012", "A007"...), which should become A12, A7.
