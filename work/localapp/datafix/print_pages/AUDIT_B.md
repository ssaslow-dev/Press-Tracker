# Audit of class B: should chain evidence alone make new Reprint rows?

Independent check (Fable, 2026-11-04) of the 277 "Unlinked print pages" rows that `match_print_pages.py` matched as likely reprints at chain sister papers (class B). Read-only: workbook copy `0bccc1fc`, `details.csv`, `proposals.csv`, the script, `code/reprint_rule.py`, DECISIONS tags REPRINT90-v1, REPRINT-v2, PRINTTAB-v1, HIDEUNVERIFIED-v1 and the 2026-10-27 clipping-run notes.

## Verdict

**None of the 277 pages becomes a Reprint row now.** `approved_B.csv` is empty (header only). All 277 stay in the Unlinked tab as a clip-and-check list, with the 26 "high" pages first.

## Why

1. **The rules give no way to call a page a Reprint without seeing it.** A Reprint needs the text test (runs of 25 identical words covering 90% of both texts, within 90 days: REPRINT90-v1) or, with no text, the same headline and the same people within 7 days. These pages have no text, no headline and no byline. Chain syndication is not a recorded basis, and PRINTTAB-v1 already decided this exact point: the 1,443 pointers left Coverage because they have no headline or text, with "clip by priority later." The chain pattern was known then (the older "Likely counterpart" column). Nothing new has been learned since; only the counting is more careful.

2. **We do not know what the item on the page is, only that the name is on the page somewhere.** That is the difference from the headline-and-people fallback, where at least the item itself has been seen. The Unlinked population is full of non-story mentions: 109 election-results pages (class C), 862 pages nobody can place (class D). A page can carry a brief, a results table, a letter, a caption or a second story on the same subject. Busy news days, exactly when every sister paper runs the known story, are also when other Gabriel items run. Examples from the "high" set:
   - **s00610, 2024-06-23 (6 pages, the spot check).** The pattern fits well: Daily Breeze and Press-Telegram have the story on p.10 and a page hit on p.11 (the jump), and the four LA-group papers (Daily News, Star-News, SGV Tribune, Whittier) have hits on p.11 only; the three Inland papers all on p.46. That is what shared SCNG layout predicts. But the state budget deal was announced on Saturday 2024-06-22, and the Assembly budget chair is quoted in budget stories; a Sunday business page could carry a budget item instead. The tracker holds no SCNG budget-deal story that weekend, which is not proof none ran: the same papers also hold no article record for the story the pages are being matched to, although NewsBank carried their article text that month (Daily News has 6 print rows within 45 days). The evidence cannot tell those two cases apart.
   - **s00480, 2024-12-03, Denver Post p.4.** Eight sister papers ran the Bay Area News Group story on p.1. The Denver Post has only two NewsBank print rows in the whole tracker (the 2026 one is the AP Nazi-art story), and the AP special-session story (s00479, 21 rows) ran in print that same day in the Fresno and Merced e-editions. The page is at least as likely AP as BANG. The script's "only candidate story" means only candidate among sister papers; it never considers wire or nonprofit stories that any paper can run.
   - **s00930, 2023-09-10, Marin IJ p.4.** The Coupal op-ed ran at seven SCNG papers on p.5. But that was end-of-session weekend: AP's gun-tax story (the Assemblymember's own bill, 14 rows), AP's X lawsuit (22), AP food chemicals (13) all ran 09-07 to 09-10. A Sunday p.4 state page in Marin could be any of them.
   - **s00044, 2026-09-20, Daily Camera and Times-Call.** Probably the AP story, but the clipping run already showed what chain guesses miss: Denver Post 09-20 and Daily Times 10-11, both "AP Nazi-looted art" by chain logic, turned out on clipping to be trimmed versions that the rule at the time made new Originals (s04685, s04686; merged later only after the containment rule). The row data (headline, byline, word count) was different from the Original in every case.

3. **How often the chain rule is right, measured on the tracker's own verified print rows.** I replayed the rule on 1,191 text-verified NewsBank print rows at chain papers (hide the row, ask what the sister papers on that exact date predict): "high" tier (3 or more sisters, one candidate) 347 right, 9 wrong (97%); "medium" tier (1 or 2 sisters) 182 right, 45 wrong (80%). Those numbers are an upper bound for the Unlinked pages, because the verified rows are the pages NewsBank had article text for; the Unlinked pages are the ones it did not, which leans toward non-article mentions. Even taken at face value, 26 high pages means about one wrong row, and 90 medium pages about 18 wrong rows, with no way to know which.

4. **Wrong rows cost more than missing rows.** A wrong Reprint row is a false fact ("Whittier Daily News printed this on 2024-06-23, p.11") shown on the story, counted in "# of reprints", outlet pages, maps, Story travel and CSV exports; it has no copy and no text, so no later check can catch it; and once a row exists, nobody clips the page. The proposal also writes the Original's headline into the new row, marked "replace at clip," which later becomes a filled cell the fill-blanks rule protects. Sammy's own precedent points the same way: reprint claims that could not be verified were hidden (HIDEUNVERIFIED-v1), not shown. A missing row costs a slightly low reprint count on a story the tracker already has, at a sister paper of a chain the story already shows; the page stays listed with its best guess and can be added the proper way in a minute per page.

## Counts

| | High | Medium | Low | Total |
|---|---|---|---|---|
| Class B pages | 26 | 90 | 161 | 277 |
| Approved as Reprint rows now | 0 | 0 | 0 | **0** |
| Stay as clip-and-check | 26 | 90 | 161 | 277 |

Other facts found on the way:
- 12 low pages are dated before their story's Original; adding them would force Original swaps on no evidence.
- 63 low pages rest on the wire rule alone (out-of-state paper, no sister paper, one widely carried AP story within 3 days). That is a guess about the subject, not a match.
- 98 low pages have a sister paper within 3 days but none on the page date.
- 7 "pages" are one printing counted twice (a paper and its "Today's Edition" e-edition on the same date, e.g. Fresno Bee p.16 and Fresno Bee Today's Edition p.199, 2025-08-17): the proposals would make two rows for one reprint.
- 147 of the 277 pages are out-of-state papers (mostly low).

## What to do with the list

Clip, then let the rule decide. The NewsBank "Download Full Page" PDF gives the headline and byline; under Sammy's 2026-10-27 clipping rule (skip OCR; headline plus people, or matched text) each page then becomes a Reprint, an edition, a new Original, or not coverage, on evidence. Suggested order, strongest first:
1. s00206 (Bass re-election, 2025-12-14, four LA-group papers all p.4), s00492 (Assembly races, 2024-10-24, two pages), s00610 (2024-06-23, nine pages counting the Daily Breeze, Press-Telegram and Register jump pages, which sit in classes D and A-jump), s04461 (Holocaust Museum, 2023-11-19, three pages), s01389 (Oroville 2021-05-29), s00309 (Fresno Bee 2025-08-17, one clip covers both editions). One clip per cluster is likely to settle the cluster, since SCNG zone papers share pages.
2. s00044 (two Colorado pages), s00480 (five pages, Denver Post last), s00930 (Marin IJ).
3. The 90 medium pages, then the 98 low pages with a sister within 3 days. The 63 wire-rule pages and the 12 pre-Original pages last, if at all.

Risks of this verdict: a few dozen real reprints at sister papers stay uncounted until someone clips them, and clipping was paused in October because it took too long. That is a known, visible gap in a tab built for it, not a hidden error in Coverage.
