# Replay of the UPDFIX-v1 / NOBLOGS-v1 / SINCE-v1 rules over the existing master

Read-only test, 2026-10-30. Nothing in `code/` or `work/` was edited; the only files written are this one and `replay_hits.csv` (same folder).

## What was run

- Master: `work/coverage_current.xlsx`, sha256 `0159ea38...` (Coverage 8,177 rows, 4,088 stories-with-Original, plus Unlinked print 1,443 and Removed 328 for the dedupe index).
- `work/shared/` is STALE (built from `bd2d84ea...`, 8,169 rows). I rebuilt the snapshot into a scratch folder with `shared_data.rebuild` (SHARED pointed at the scratchpad) and used that for `d.coverage` and `d.text(aid)`. `work/shared/` itself is untouched, so the next `load()` there still warns.
- Python rules called directly: `sheet_task.never_coverage_reason`, `print_page_url`, `norm_url` / `canon_mirror`, `Task.headline_story` (bound to a stub whose `originals()` is the master's Originals, own story excluded), `reprint_rule.same_house` / `pair_class`, `dates_lib.displayed_stamp`.
- JS rules called in node, loaded the way `build/tests/update_js/test_updfix_js.js` does (vm, tracker `40_` + `41_`), but with the REAL blocks instead of the test's stubs: `build/.../rows` (9,948 sheet rows, headlines pre-normalised by `build_data.norm_hl`), `fetchrules`, `idmap`, and the real `D` (`data.json`). Functions: `pageStamp`, `neverCoverage`, `isPrintPage`, `isBackfill` / `proposeRows`, `sinceError` / `sinceKeep`, `normU` / `covNormU`, `covLoad` / `covHit`, `knownIndex`, `dupOf`.
- Every JS result was compared with the pre-UPDFIX tracker code (`handoff_kit/source/code/tracker`, 2026-10-29 23:30) so that a hit is attributed to the new rule only. For `covHit` / `knownIndex` / `dupOf` each story was tested with its own rows removed from the index, as if it were a fresh find.
- Parity checks: JS `neverCoverage` vs Python `never_coverage_reason` = same 10 rows; JS `isPrintPage` vs Python `print_page_url` = same 24 rows; JS `covNormU` vs Python `norm_url` = identical on all 5,055 links.
- Not replayable offline: the classify / screen prompt wording (REQ-11 b, NOBLOGS), the exact-headline originator search for blocked finds (needs TinyFish), `exclude_domains` on live searches.

## Counts per rule

| Rule | Hits | True | False positive | Other |
|---|---|---|---|---|
| REQ-10 future date, sheet side (`date_check`, `toRow`) on the Date column | 0 | - | 0 | no row is dated after 2026-10-30 or before 1990 |
| REQ-10 future page stamp (JS `pageStamp`) | 47 | 47 | 0 | - |
| REQ-10 byline shape (JS `BYLINE_BEFORE`), stamps no longer taken | 312 | 85 | **216** | 11 real date lines lost (see below) |
| REQ-10 Python mirror `dates_lib.displayed_stamp` | 47 still wrong | - | - | NOT UPDATED (defect) |
| REQ-11 e-paper / flipbook (JS and Python) | 24 | 24 | **0** | - |
| REQ-12 + NOBLOGS-v1 never-coverage hosts (JS and Python) | 10 | 7 | **1** | 2 judgment calls |
| REQ-13 outlet-backfill label (if re-found by an outlets search, since 2026-10-23) | 6,854 | 6,854 | **0** | label only, nothing rejected |
| SINCE-v1 (`sinceError`, `sinceKeep`) | 0 rejections | - | **0** | 3 partial dates, 441 undated rows (kept by design) |
| REQ-14 (a) mirror-host canonical form | 10 keys change, 0 merges | - | **0** | - |
| REQ-14 (b) headline first segment (find side) | 5 | 5 | **0** | row side inert (see below) |
| REQ-14 (c) iHeart LA house | 0 | - | **0** | no effect on text pairs (see below) |
| REQ-14 (d) blocked find matched by headline (`headline_story`) | 193 rows / 109 pairs | 154 rows / 87 pairs | **37 rows / 21 pairs** | 2 rows / 1 pair unclear |

Row-level detail for every hit is in `replay_hits.csv` (columns: rule, article_id, story_id, kind, date, outlet, headline, link, verdict, partner_article_id, partner_story_id, note). Verdict values: TRUE, FALSE_POSITIVE, JUDGMENT, UNCLEAR, LOST_DATELINE, TRUE_PROBLEM, LABEL_OK, EDGE, KEY_CHANGED_NO_MERGE.

## Findings that need action (ordered by impact)

1. **REQ-10 byline shape drops real bylines (216 false positives).** The new `BYLINE_BEFORE` is case-sensitive (`By`, not `by`), ASCII-only (`[A-Z][\w'.-]+` fails on TRAN NGUYEN with diacritics) and requires the date directly after the name. In the master that loses the page stamp on 216 rows whose stored Date is the page's own date line: about 100 use lowercase `by` (often `by` on its own line, `by Contributor`, `by CC News`), about 100 have outlet, section or `Published 6:05 PM PDT` between the byline and the date (`By Jenny Huh / Published 6:05 PM PDT / Sep 29, 2026`, `By Lynn La | CalMatters | date`), 11 have non-ASCII capitals. 174 of the 216 are rows where the old stamp equalled the stored Date. Effect on a fresh find: the date falls back to TinyFish metadata / Claude's reading, so `Date source` degrades from "page byline" and undated pages stay undated. Probe: `pageStamp('Headline\nby Contributor\nOctober 20, 2026')` returns nothing; `pageStamp('Headline\nBy Jane Doe\nOctober 28, 2026')` works. The rule does what it was written for on the 47 future stamps and on 85 prepositional / caption cases ("signed by Governor Newsom on October 10", "Photo by X (Aug. 15, 2025)", "by Sept. 1, 2026").
2. **Python mirror not updated.** `dates_lib.py` is unchanged since 2026-10-28; `displayed_stamp` still accepts any `\bby\b` within 40 characters and has no future / pre-1990 guard. On the master's saved texts it returns a date after today for the same 47 rows (for example 00084 gives 2029-01-01 from "by Jan. 1, 2029") and 475 `byname` stamps in all. `date_rules.page_date` and check 7 use it, and the sheet's `date_check` only blanks a future Date after the fact. The REQ-10 instruction to keep the Python and JS tests in step was not carried out.
3. **REQ-14 (b) first-segment index does nothing on the real sheet rows.** `covLoad` splits `a[ix.hl]` at " - ", " | ", " — ", " – ", but the `rows` block carries `norm_hl(...)` output (punctuation already stripped), so there is no separator to split on. `COV.hl` has exactly the same size before and after the change (5,214 keys; `COV.links` 9,233 both). The unit test passed because its fixture used raw headlines. With the real block: `covHit` still misses the Telegraph title without its dek (01859 / s00523) and the KIIS title without the Patriot suffix (07423 / s02206). The staging-host Telegraph URL is caught (by link, `how: link`). `knownIndex().hls` does work (it reads raw `D` headlines): it contains the Telegraph and KIIS first segments. The 5 new find-side hits in the table come from the find's own segment matching a normalised row headline.
4. **REQ-14 (c) iHeart LA house has no effect on text pairs.** `outlet_rules.json types` now gives KFI, KIIS, Patriot LA and the kfiam640 host the house "iheart la" (the `houses` block is documentation; no code reads it). `same_house` is now true for them, but `pair_class` only uses it for AV items, wire-vs-wire and the sibling second signal; for a text pair the "edition" result still needs the same outlet key. In the master the three groups stay Original + Reprint (s01919: KIIS Original, KFI and Patriot reprints; s02441: KFI Original, KIIS reprint). There is no cross-story pair of these stations within 14 days, so nothing is wrongly merged either. Also, the `houses.iheart la.hosts` list includes `knx.iheart.com` while the note says KNX is CBS Audacy.
5. **REQ-14 (d) headline match turns independent write-ups into Reprints (37 rows).** See the table below. The pattern: same event, similar headline, different newsroom, text overlap under 0.3 (SF Chronicle vs Food Dive, CalMatters vs Agri-Pulse, Telegraph vs LAmag, NBC Bay Area / Business Insider / ABC7 on the gas rebate), plus recurring items whose headline repeats (Targeted News Service "Legislative Update", the "Jews in the News" column). A blocked-site find (LA Times, Daily News, SF Chronicle, Bee and similar) would be filed as a Reprint of another outlet's story and never become its own Original. 154 of the 193 hits are real duplicates (same text or same wire / sibling copy), which also shows the master holds at least 87 pairs the text rule left in separate stories.
6. **NOBLOGS rescue path is empty.** The "outlets.json record listing the exact host rescues it" rule reads `records[*].hosts`; no outlets.json record has a `hosts` field (`fetchrules.never_keep` is `[]`), so a journalist's Medium page cannot be rescued today. The host list misses `user.medium.com` pages (`nadiarahman.medium.com`, `spillikinaerospace.medium.com` are in the master and are not matched).

## NOBLOGS / REQ-12: the 10 existing rows, re-checked against the CURRENT master

The list in `work/out/noblogs_existing_rows.csv` (10 rows) matches the current master exactly: same Article IDs, Story IDs, dates, outlets, headlines and links; all 10 are still Originals; the Python and JS rules select the same 10 and no others (Coverage 8,177 rows; Publisher link only). Verdicts:

| Article ID | Story | Row | Why it matches | Verdict |
|---|---|---|---|---|
| 06917 | s01777 | Jewish California, "Capitol Summit 2026 / AB 715 Lawsuit Panel", 2026-05-15 | YouTube video, no saved copy | TRUE |
| 07237 | s02050 | Why4416 blog, 2026-07-14 | Tistory | TRUE |
| 07381 | s02170 | Why4416 blog, 2026-04-08 | Tistory | TRUE |
| 07546 | s02321 | Why4416 blog, 2025-10-17 | Tistory | TRUE |
| 07681 | s02430 | Colion Noir, 2025-09-03 | mrcolionnoir.com advocacy blog | TRUE (Sammy's rule) |
| 08318 | s02975 | **Los Angeles Times**, "California lawmakers exempt their new office building from state environmental law", 2024-06-27 | link is `nalert.blogspot.com` | **FALSE POSITIVE**: a real LA Times story (Mays and Luna byline, saved text is the LA Times article); only the recorded link is a blogspot mirror. Fix the link, do not drop the row (Yahoo reprint 08319 is in the same story) |
| 08446 | s03076 | Naver Blog, 2024-03-26 | blog.naver.com personal blog | TRUE |
| 09715 | s04191 | CalStuff, 2003-05-03 | blogspot personal blog quoting the Daily Californian | TRUE |
| 10315 | s04910 | ABC7 San Francisco, "RFK Jr. align in fight against ultra-processed foods", 2025-03-19 | YouTube video | JUDGMENT: a real ABC7 segment; no ABC7 web-article row for this story exists in the master |
| 10316 | s04911 | ABC7 San Francisco, "New 1st-in-the-nation CA legislation aims to ban ultra-processed food", 2025-03-19 | YouTube video | JUDGMENT: same story as ABC7 article 07877 (s02601), so removing it loses nothing |

So: 7 true, 1 false positive, 2 judgment calls. Other tabs: only the Audio & video details tab has YouTube links beyond these (06917 again, and 09268 whose AV "YouTube link" is an extra link; its Publisher link is the synagogue's own video archive page, so the rule does not touch it). Press releases, Removed, Unlinked print pages and Bills: 0 hits.

## REQ-11 e-paper: 24 rows, all `epaper.singtaousa.com/flippingbook/...`

All 24 are Sing Tao Daily Originals (Data Source "Tracker scrape", Format Article, Language Chinese, 12 pairs of NY/SF/LA/Boston/Chicago editions for the same date). The saved copy of each is the whole e-paper page (ads, notices and several unrelated articles), the headline is one article taken from the page (and for 08363 and 08487 only a date label, "06-03" and "03-14"). They name Gabriel, so they are real print coverage but not article rows: the rule is right to treat them as print pages. 0 false positives. Before anyone removes them, note that the Unlinked print pages tab has no Sing Tao rows, so each needs a clipping row by hand. IDs: 07146 07147 07246 07247 07322 07323 07362 07446 07890 07952 07992 08033 08247 08293 08309 08363 08383 08424 08460 08487 08587 09082 09083 09127. Four pairs are the same Sing Tao story in two editions (s01980/s01981, s02059/s02060, s02121/s02122, s03611/s03612).

## REQ-10 detail

- Future dates: no Coverage row has a Date after 2026-10-30 or before 1990, so the sheet `date_check` / `toRow` guard and the 1990 floor reject nothing. JS `pageStamp` with the new `stampOk` rejects the 47 stamps that the old rule took as a byline date (deadlines such as "by June 1, 2029"; ids in the CSV, rule "future page stamp"). None of these rows' stored Date is affected.
- Byline shape: of 359 stamps the new rule stops producing (old byname stamps), 47 are future, 85 are prepositional / caption / body dates (TRUE), 216 are real bylines (FALSE POSITIVE), 11 are real date lines ("September 17, 2025 / 2 min read", "April 1, 2024 - SACRAMENTO", "(Aug. 26, 2025 / JNS)") that the old rule found only through an accidental "by" in the 40 characters before them (not a byline shape; stamp lost, stored Date right). The new rule also finds 5 stamps the old one missed (01196, 01202, 07141, 08940, 10319), all equal to the stored Date.
- Rows with a stamp lost but stored Date right matter most where the stored Date came from the page ("Date source" = page byline): 2,181 rows carry that source today.

## REQ-13 outlet-backfill label

With `U.since` = 2026-10-23, `isBackfill` is true for any row dated before 2026-04-26 if the find came from an `outlets:` search: 6,854 of 7,736 dated rows (441 rows have no Date and are never labelled). `proposeRows` over all 3,671 dated tracker stories gives the label exactly when `isBackfill` does (0 mismatches, 0 errors). 345 of the 6,854 rows already came from earlier TinyFish searches. No row is rejected. I found no row whose stored Date is wrong in a way that would mislabel it (3 rows have a page stamp more than 180 days newer than the stored Date: 08522, 08982, 09429; in each the stamp is page chrome, so the stored Date is right).

## SINCE-v1

`sinceKeep(date, date)` is true for every dated row and undated rows are kept (441), so the page-date filter drops nothing it should keep. Three rows have a partial Date (06953 "2003", 09717 "2003", 06954 "2018-07"): `sinceError` calls those values "not a real date" if typed as a Since, and `sinceKeep` compares them as strings ("2018-07" sorts before "2018-07-15").

## REQ-14 detail

- (a) Mirror hosts: 10 links change canonical form (amp.sacbee.com 01582; m.ktown.koreadaily.com 07287; five m.news.nate.com 07750 08063 08109 08111 08155; amp.seoul.co.kr 08108; m.sedaily.com 08126; m.tanpaifang.com 08564). No other row, in Coverage, Unlinked print or Removed, shares any of the new keys, so nothing is merged; 0 false positives. Tested label risks: a host called `m.com` is left alone (unit test), and no master host collides.
- (b) Five new find-side hits, all real duplicates already split across two stories in the master: 01713 (Star Tribune, s00479) and NBC Bay Area 01734 (s04915), overlap 0.58; 02620 (Independent, s04450) and AP 02619 (s00758), 0.82; 03400 (Simi Valley Acorn, s04497) and 03399 (Thousand Oaks Acorn, s00953), 1.0; 03407 (Greenberg Traurig, s04498) and 03406 (National Law Review, s00958), 0.93; 03744 (Independent) and 03737 (Courier, s01051), same AP headline but the saved text of 03737 is a different page.
- (d) The three real misses named in REQ-14, run against the master with `headline_story`: Telegraph title matches 01859 (s00523) at 1.0; KIIS title matches Patriot LA 07423 (s02206) at 1.0; the Marin IJ / Santa Cruz headline matches East Bay Times 10539 in s00327 at 0.86 (same day). So the Python side delivers what REQ-14 asked for; the page side (finding 3) does not for headline suffixes.

### REQ-14 (d) false positives (21 pairs, 37 rows; the rule would file the later or blocked find under the other row's story)

| Row A | Row B | Why not the same story |
|---|---|---|
| 00215 Just Food | 07169 The Gethsemane | own write-up vs EWG release text (0.09) |
| 00317 CALO News | 00321 USA TODAY | different text, a week apart (0.08) |
| 00640 Jewish Journal | 00641 UCLA Newsroom | article vs media roundup that cites it (0.02) |
| 00933 Telegraph | 07596 LAmag | independent (0.0) |
| 00979 India West | 07633 KCRA | independent (0.03) |
| 00997 CalMatters | 07629 Agri-Pulse | independent (0.0) |
| 01027 SF Chronicle | 07566 Food Dive | independent (0.0) |
| 01867 TNS | 01872 TNS | two different weekly Legislative Update releases |
| 01883 Culver City Observer | 08187 Courthouse News | different text (0.27) |
| 02915 Edhat | 03072 Food Safety News | independent (0.0) |
| 02998 TNS | 03083 TNS | two different legislative updates (10.7.23 / 10.8.23) |
| 03269 San Diego U-T | 08797 Epoch Times | independent (0.04) |
| 03703 National Law Review | 03706 Food Safety News | blog post vs news article (0.10) |
| 07017 Aura Scan | 07031 New Hope Network | independent (0.0) |
| 08020 ABC30 Fresno | 01714 AP | own piece vs AP (0.01) |
| 08123 QA & Food Safety | 08138 Consumer Reports | different reporting, "Six" vs "6" dyes (0.25) |
| 08797 Epoch Times | 08804 Politico | independent (0.05) |
| 09253 ABC7 SF | 09255 East County Today | rewrite (0.10) |
| 09253 ABC7 SF | 09261 Business Insider | independent (0.15) |
| 09253 ABC7 SF | 09263 NBC Bay Area | independent (0.19) |
| 09626 San Diego Jewish World | 09628 San Diego Jewish World | recurring column, Feb 14 vs Feb 10, 2019 (0.02) |

Unclear (1 pair, 2 rows): 03162 FOX40 and 08737 Wall Street Journal, gun and ammunition tax, same day, no saved text.
True pairs include the same-outlet re-runs 04257/04273 (Daily Breeze, identical text one week apart) and 04560/04573 (Santa Monica Observer), and the Jim Wood caucus release run by five Digital First papers (04203-04208).
