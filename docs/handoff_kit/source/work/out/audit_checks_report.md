# Audit plan data checks — REPORT ONLY (agent-instructions2, 2026-10-28)

Master: AJG Coverage - NewsBank.xlsx sha256 30543809386d9165c020a4c65b041681b7ca79fae0213cde0e87e220886bcd75 (after the instruction-tab removal write), Coverage 9,789 rows. Checks from the retired "Audit plan" tab (B10, B11, B13, B14, B15) that were never run. **Nothing was changed** (Sammy 2026-10-28: report only). Outlets are grouped with sheet_task.norm_outlet(Outlet, Outlet city) = outlet_rules.json (OUTLETRULES-v1). Script: work/tmp_agent-instructions2/audit_checks.py; full output audit_checks.json.

## Headline

| Check | Result |
|---|---|
| 1. Per-outlet consistency (outlets with 2+ different non-blank values) | city 11 · county 8 · state 10 · Medium 53 · Publisher 20 outlets; CA on a non-CA outlet: 1 |
| 2. Edition vs Page | Print with no Page 0 · Web with a Page 0 · (Web + Print with no Page 94; Edition blank 3,455) |
| 3. Year ≠ Date | 0 rows (Year without Date 0, Date without Year 0) |
| 4. Print dated before web (same row) | 2 of 217 rows with both dates, both 1 day |
| 5. Generic outlet name with no city | 65 rows (Daily News 55, Independent, The 7, Times, The 2, Collegian, The 1) |
| 6. "# of reprints" vs the story's rows | 2 of 4,509 stories differ (sheet higher in both); 1 Original has a blank count with 0 reprints |
| 7. Exactly one Original per story | 4,509 stories: 0 with none, 0 with 2+ — passes |

## 1. Per-outlet consistency

Caveats: Publisher can legitimately change over time (DECISIONS: owner at each row's date, e.g. LA Times Tronc → Nant Capital), so most Publisher splits are ownership history, not errors. Folding feeds (OUTLETRULES-v1) puts every "Associated Press …" feed in one group, so AP shows New York and California bureaus. Medium splits are mostly a handful of rows on large outlets.

- **Outlet city**: 11 outlets (215 rows) carry 2+ values; 10 outlets mix blank and filled cells. Largest: associated press (128 rows: New York 84, Los Angeles 3); courier times (17 rows: Roxboro 15, New Castle 2); news tribune (16 rows: Tacoma 15, Palm Coast 1); arkansas democrat gazette (12 rows: Little Rock 6, Fayetteville 6); el pais (12 rows: Mexico City 4, Madrid 2); daily press (9 rows: Victorville 8, Newport News 1)
- **Outlet county**: 8 outlets (190 rows) carry 2+ values; 6 outlets mix blank and filled cells. Largest: associated press (128 rows: New York 84, Los Angeles 6, Santa Cruz 3, Sacramento 3); courier times (17 rows: Person 15, Henry 2); news tribune (16 rows: Pierce 15, Flagler 1); arkansas democrat gazette (12 rows: Pulaski 6, Washington 6); daily herald@arlington heights (7 rows: Cook 5, DuPage 2); daily record (6 rows: Wayne 4, Harnett 1, Fremont 1)
- **Outlet state**: 10 outlets (200 rows) carry 2+ values; 6 outlets mix blank and filled cells. Largest: associated press (128 rows: NY 84, CA 38); courier times (17 rows: NC 15, IN 2); news tribune (16 rows: WA 15, FL 1); el pais (12 rows: USA 5, Mexico 4, Spain 2); daily press (9 rows: CA 8, VA 1); daily record (6 rows: OH 4, NC 1, CO 1)
- **Medium**: 53 outlets (2,066 rows) carry 2+ values; 4 outlets mix blank and filled cells. Largest: sacramento bee (379 rows: Newspaper 378, Newsletter or blog 1); politico (213 rows: Newsletter or blog 190, Trade press 15, Online news 7); pasadena star news (140 rows: Newspaper 138, Online news 2); calmatters (132 rows: Online news 128, Newspaper 3, Newsletter or blog 1); associated press (128 rows: Wire 125, TV 2, Newspaper 1); los angeles times (120 rows: Newspaper 118, Online news 2)
- **Publisher**: 20 outlets (1,014 rows) carry 2+ values; 13 outlets mix blank and filled cells. Largest: politico (213 rows: Axel Springer 180, Capitol News Company 24); yahoo news (174 rows: Yahoo Inc. (Apollo Global Management) 164, Verizon Media 10); los angeles times (120 rows: Nant Capital (Patrick Soon-Shiong) 109, Tronc 9, Tribune Company 2); press democrat (98 rows: Sonoma Media Investments 74, MediaNews Group 24); san diego union tribune (52 rows: Southern California News Group 26, Nant Capital (Patrick Soon-Shiong) 24, Tronc 2); cbs news (39 rows: Paramount Global 24, ViacomCBS 8, CBS Corporation 5, Paramount Skydance 2)
- **CA on non-CA outlets**: associated press (NY 84, CA 38) — the CA rows are AP State Wire: California / LA bureau, so likely fine

## 2. Edition vs Page

No Print row lacks a Page and no Web row has one. 94 "Web + Print" rows have no Page (the print half may be from a source without page numbers); 3,455 rows have a blank Edition (not checked).

## 3. Year ≠ Date

None.

## 4. Print dated before web

Both are one day apart (cause not checked; a time-zone or late-night posting difference would explain it): 04502 Sacramento Bee, The (web 2021-09-28, print 2021-09-27); 05204 Vida en el Valle (web 2018-07-19, print 2018-07-18)

## 5. Generic outlet names with no Outlet city

Under OUTLETRULES-v1 these group only with other blank-city rows of the same name. "Daily News" (55, state CA) is probably the Los Angeles Daily News (not verified); "Independent, The" (7) and "Times, The" (2) cannot be placed without a city; "Collegian, The" (1). Examples: 00061 Daily News; 00090 Daily News; 00349 Times, The; 00545 Daily News; 00566 Daily News; 00612 Daily News

## 6. "# of reprints" vs the story's rows

Rule: distinct outlets of the story's Reprint rows other than the Original's (DECISIONS 154; "Reprint (unverified)" not counted), outlets per outlet_rules.json. After this write's 25 recomputes, 2 stories still differ; the outlet rules do not change their count (old and new matching agree), so they were outside the approved recompute:
- s00863 (02999 LAist): sheet 6, rows give 5 — "NPR" and "NPR: Blogs" are one outlet under both old and new matching.
- s01323 (04413 EdSource): sheet 3, rows give 2 — "San Mateo Daily Journal, The" and "San Mateo Daily Journal" are one outlet.
- 05428 (s04685): blank count, 0 reprint rows (0 would be the value).
DECISIONS 177 makes the count derived and recomputed in every write; these 3 can go into the next write if the coordinator agrees.

## 7. Exactly one Original per story

Passes (4,509 stories).

