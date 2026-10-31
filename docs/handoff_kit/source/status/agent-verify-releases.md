# agent-verify-releases — independent, read-only check of v16 press-release wiring

Date: 2026-10-27. Read-only: no code, workbook, data or artifact was changed; nothing published; no live fetches.
My scratch work (scripts, extracted blocks, screenshots, CSVs) is in `scratchpad/verifyrel/`. Builder files and v17 files were not touched.

## Sources pinned
- Workbook `L/work/coverage_current.xlsx` sha256 = **572b8e12a1d157fa77399539ac407c3bfa8e71036dfb0facb158312932bb9398** (matches the expected 572b8e12…9398). PASS
- Live page read by the Artifact tool (version 1793133203-186b): index.html sha256 3f93053a063b655e69c8616369a3770f3892171e3bef9db368a261ee4acd997e = local `work/tmp_agent-insights/v16/srv/index.html`. PASS
- Live `data/sheet.json` (the Spreadsheet download) decodes to "AJG Coverage - NewsBank.xlsx" with sha256 572b8e12…9398, the same as the master. PASS
- I rebuilt the release block myself: running `build/insights/release_pickup_data.py` on the master gives JSON identical to the `ins-release_pickup` block in the live page. PASS

## Counts (all checked against the real data)
| Where | Value |
|---|---|
| Press releases tab rows | 244 (196 office, 45 caucus, 3 office+caucus joint) |
| Out of scope (caucus-only, dated before 2020-11-18) | 8, all noted "OUT OF SCOPE", none appear in the view |
| In scope on the tab | 236: In tracker Yes 82, No 154 |
| View: all releases | 241 = 236 official + 5 releases outlets ran that aren't posted officially |
| View: picked up | 87 = 82 tab Yes + the 5 unposted ones |
| View: "No pickup found" | 154 = tab In tracker No, in scope |
| Pickup filter in the rendered page | Picked up 87, No pickup found 154 (at 1400 and 390) |
| Coverage rows with Press release = Yes | 498 rows / 396 stories |
| Originals tab with Press release = Yes | 385 = the 385 Coverage originals flagged, no differences |
| Tracker stories (data block, Clips, CSV) | 4,106 |

## 1. Tab integrity
- Duplicate URLs: none. Duplicate title+date: none. One title appears twice ("Assembly Budget Chair Gabriel Responds to Latest Revenue Forecast"), on 2024-11-20 and 2025-11-19, with different URLs. These are two real releases. PASS
- Dates: all 244 parse as ISO dates and fall between 2018-06-10 and 2026-10-24. PASS
- Tenure rule: the 8 caucus-only rows dated before 2020-11-18 carry the "OUT OF SCOPE (Sammy 2026-10-27 "2 no")" note, are In tracker = No, and are absent from the view. The view has no caucus release dated before 2020-11-18. The 9th caucus-sourced pre-tenure row (2019-10-11, "Governor Newsom Signs Legislation Establishing New Program…") has source "Gabriel's office; Jewish Caucus", so it counts as an office release and is correctly in scope. The boundary row (2020-11-18, his chair appointment) is in scope. PASS
- In tracker / Tracker release ID: all 82 Yes rows have an ID and all 162 No rows have none. Every Yes ID maps to a release in the view that has runs and the same URL, and no No row shows as picked up. Official date and title in the view equal the tab for all 236 rows. PASS
- NOTE: in 12 older rows the "Coverage stories linked" count (2–3) is higher than the number of IDs in "Tracker release ID" (1). That column lists only the release's key story, not every story grouped with it (e.g. s03675 + s03681). The view is unaffected. This predates v16.
- NOTE: 3 stories linked from the tab are only partly flagged, so they remain tracker stories that carry a release: s01453 (04758 Yes; 04759, 04760 blank), s01093 (03926 Yes; 03928 blank), s01875 (07019 Yes; 07020 blank). s01125 is also mixed. This predates v16 and is what produces the 3 "From press release" stories in Clips.

## 2. Coverage flags ↔ tab
- Tab → Coverage: every story named in a Yes row's Tracker release ID has Press release = Yes rows. PASS
- Coverage → tab: the 396 flagged stories break down as follows. This matches the builder's breakdown; I recomputed it from the workbook and the live blocks.
  - 97 in a release linked to a tab row
  - 5 in the 5 unposted releases
  - 8 tracker stories whose only flagged rows are reprints
  - 286 not in the view and not tracker stories (the release review classed them as other issuers' releases)

  So "every flagged row maps to a tab row" does not hold literally, and isn't meant to: Press release = Yes means "this row is a press release", from any issuer. NOTE
- Spot checks:
  - Copy text: 15 releases where the published bundle has a saved copy (the 14 fixes plus s00823). I compared each copy with the official release page text (cached by agent-releasecheck) using 8-word shingles. Overlap was 54–90%, and every copy is clearly the release. PASS
  - Headlines, random 15: the other 68 pairs have no saved copy in the bundle (release stories aren't published as copies), so I compared the Coverage headline, date and outlet against the release title for a random 15 (seed 7). All 15 match on subject and date (ratio 0.50–1.00). Low-ratio cases were checked by hand and are the same event, same day. PASS

## 3. The 15 approved fixes, AB 2020, and HeySoCal 02913
- The 18 Coverage rows the builder listed (04581 04468 04377 04156 04161 04139 04111 04055 03517 03518 03345 02912 02913 02770 02858 02859 08616 08402) are all Press release = Yes. 07038 (AB 2020) was already Yes. PASS
- In the rendered view, all 14 audit misses plus AB 2020 (s01893, 2026-09-29, "New California Law Protects Affordable Housing from Preventable Foreclosure": PublicNow, +1 day, official URL) show their official date, runs and official link. None of them is still a tracker story. PASS
- Counting: the audit's "actionable misses" list has 15 entries, and the 15th is AB 2020. So "15 approved fixes" = 14 + AB 2020 = 15 releases (16 stories, because the veterans release spans s00802 and s00823). If the brief meant 15 fixes plus AB 2020 as a 16th, there is no 16th. NOTE
- **HeySoCal 02913 (story s00842):**
  - Why it was flagged: the audit matched only 02912 (Pasadena Independent) by headline. The builder also flagged 02913 because it sits in the same story, "so the story isn't half a release". That goes one row beyond the audit list Sammy approved.
  - Is it a legitimate pickup? Yes. The saved copy of s00842 is the HeySoCal text ("Staff", 2023-10-10). 80% of its 8-word shingles appear in the official 2023-10-09 release: the lede, the Haya quote and the background paragraphs are near-verbatim. It does recast Gabriel's quote as "According to bill author Assemblymember Jesse Gabriel's office…". This is a lightly edited run of the release, which is the same standard as the other approved fixes.
  - Side effect: 02913 is dated 2023-10-10, two days before its own "Original" (02912, 2023-10-12). The pickup lag shows +1 day for HeySoCal.
  - Verdict: PASS (legitimate), NOTE (one row beyond the approved list)

## 4. Counts across the page
- The view shows 241 / 87 / 154, matching the tab and the block (see table). PASS
- Home: no release figure exists on Home. The rendered Home text has no line mentioning releases, so there is nothing to agree. NOTE
- Manage: no release figure exists. The only mention is the Update description ("Claude drops press releases…"). NOTE
- CSV: "Gabriel clips 2026-10-27.csv" has 4,106 story rows and 32 columns, ending with "Press release" and "Press release link". These are filled for exactly the 3 stories that carry a release (s01093, s01125, s01453), with the official URLs. The CSV is a story export: the 241 releases themselves can't be downloaded as CSV. The release list is only in the Spreadsheet download (the tab, 244 rows, sha verified). NOTE

## 5. Playwright render of the live page (index.html identical to the live version; published files served locally; claude runtime stubbed; external font requests stubbed)
- Press releases view, at 1400 and 390:
  - 241 items, 154 "No pickup found", official dates.
  - The official link "Official release ↗" has a copy button immediately to its left, on the same row. The button carries the same URL, and clicking it put that URL on the clipboard ("Copied the link" toast).
  - No horizontal scroll at either width.
  - PASS
- Story panel: searching "Assemblymember Jesse Gabriel Introduces Bill to Sustain Outdoor Dining" finds s01093 with the "From press release" badge. Opening it shows "From press release: <official title> ↗ · 2023-03-15" with the copy icon to the left of the link. PASS at 1400.
  - At 390 the line is inside the folded details: it is in the DOM but not visible until the details toggle is tapped, after which it shows. NOTE
- **Clips press-release filter: FAIL. There is none.** The filter rail has Issue, Bills, Reach, How Gabriel appears, Format, Outlet, Reporter, County, Language, Tone and Saved copy, and none is for press releases. The quick views are Last 30 days, Headlines and op-eds, National and statewide, Negative tone, With a saved copy, and the chart views; none is for press releases either. The builder's notes say so ("no press-release filter exists; badge added instead"). Only the badge exists, on the 3 carrying stories.
- Search by release title: Clips search matches a release title only for the 3 stories that carry one, which then show the badge. Searching for an actual release, such as AB 2020's title or the carbon-offsets title, gives "0 of 4,106 stories", because releases are not stories. The Press releases view has no search box. Search works as built, but you can't search for a release itself. NOTE
- CSV download: works at both widths, and the files are identical (see 4). PASS
- Console: 0 errors, 0 page errors and 0 failed requests at 1400 and 390, once every published file was served and Google Fonts was stubbed (the fonts can't be reached from this sandbox). PASS

## 6. The release before/after stat
- The "Led to original coverage" tile covers **all releases that have a bill or issue to match: 221 of the 241**, including the 136 matchable no-pickup releases. It is not limited to picked-up releases.
  - Unfiltered: 69% (152 of 221).
  - "Picked up" filter: 75% (64 of 85).
  - "No pickup found" filter: 65% (88 of 136).
- "Outlets per release" (1.3) covers only the 87 picked up. "Same-day pickup" (55%) covers dated runs.
- See the next section: some release runs that aren't flagged are counted here as "original reporting".

## 7. Update-button step (RELCHECK-v1), code read only (live pipeline/tracker.js and pipeline/sheet_task.py, which equal L/code/sheet_task.py)
- Stops at a known URL. The known set is every view URL plus the 8 out-of-scope tab URLs (block "known"). It also stops at a date older than the newest tab date for that site. PASS
- Fetches page 1 of each listing, and page 2 only when every item on page 1 is new. That is not strictly "first listing page" only. NOTE
- Scope rule: the page skips caucus items dated before 2020-11-18, and sheet_task.apply_releases skips them again ("Jewish Caucus release before his chair tenure"). Caucus listing items are filtered to category "Press release". PASS
- Blanks only:
  - The tab gets append-only rows for URLs not already present; existing rows are never rewritten.
  - The Coverage "Press release" cell is written through fill(), which is blanks-only (written / same / conflict).
  - Edge case: a headline match on a story's original row flags it as a release, which removes that story from the tracker at the next build. That happens without per-row approval; it is listed in the run review as "releases_flagged". NOTE
  - PASS
- No Exa: all calls go through tfCall → server 'TinyFish' (fetch_content, ttl 0, at most 2 listing pages per site plus at most 5 release pages per run). The only "Exa" in tracker.js is a historical comment. The page's declared MCP servers are TinyFish and Claude Code Remote only. PASS

## Finding for Sammy: release runs still counted as coverage (NOTE, decision)
The audit's "actionable misses" used exact headline matches. I scanned every published saved copy against the 154 no-pickup official releases (8-word shingles; a story counts when ≥50% of its text is the release and it ran within 60 days). That found **21 tracker stories that are mostly release text, across 16 releases currently shown as "No pickup found"**. These are the same pattern as the approved 14: small papers and HeySoCal running the release nearly verbatim. Strongest:

| Release date | Story | Outlet | Story date | Share of story that is release text |
|---|---|---|---|---|
| 2020-02-04 | s04031 | East County Today | same day | 85% |
| 2021-02-17 | s03938 | HeySoCal | | 79% |
| 2021-08-09 | s01362 | SFV Sun | | 63% |
| 2021-09-10 | s04566 | HeySoCal | | 72% |
| 2022-09-18 | s01172 | Lake County Record Bee | | 84% |
| 2023-06-29 | s00974 | Del Norte Triplicate | | 69% |
| 2023-09-07 | s00935 | Lassen County Times | | 72% |
| 2023-09-07 | s04490 | HeySoCal | | 76% |
| 2023-09-07 | s04489 | Beverly Press | | 61% |
| 2023-09-26 | s00878 | SFV Sun | | 77% |
| 2023-09-26 | s00833 | Del Norte Triplicate | | 72% |
| 2023-10-07 | s00837 | SFV Sun | | 73% |
| 2023-10-07 | s00859 | Lake County Record Bee | | 51% |
| 2023-10-18 | s00812 | Lassen County Times (caucus) | | 78% |
| 2024-03-12 | s03111 | Beverly Press | | 69% |
| 2024-04-15 | s03046 | Valley News Group | | 91% |
| 2025-08-26 | s02437 | California News Beep | | 63% |
| 2025-08-26 | s02336 | Contra Costa News | | 61% |
| 2026-09-01 | s00054 | SFV Sun | | 61% |
| 2019-02-04 | s01595 | The Acorn | | 63% |
| 2019-10-11 | s04682 | KNX News | | 60% |

Full hit list: `scratchpad/verifyrel/misshits.pkl`. A further 23 stories at 30–50% are borderline (quote-heavy reporting).

13 of these 21 are also counted as "original reporting" in the before/after tile, covering 10 releases. So the true pickup count is higher than 87 and the "led to original coverage" rate is somewhat inflated. This is not a v16 build error: v16 implemented exactly the approved list. It is a judgement call for Sammy (review these and apply the same "1 yes" treatment, or leave them).

Also seen, and left as is (probably other issuers' releases, already classed OUT):
- 01882 / 01883 (Holocaust art recovery, 2024-09-16): TNS and Culver City Observer use the Governor's wording.
- 01449 (forever chemicals, 2025-02-19, TNS): another member's wording.

## Summary
- **FAIL (1):** no Clips press-release filter exists; only a badge, on 3 stories.
- **PASS:** sha and live identity, tab integrity, tenure rule, flags ↔ tab mapping, the 15 releases incl. AB 2020, counts 241/87/154, rendering at 1400/390 with no console errors, CSV columns, copy icons left of links, the RELCHECK safeguards (known-URL stop, scope rule, blanks-only, TinyFish only).
- **NOTE:**
  - HeySoCal 02913 was flagged beyond the approved list, but it is a legitimate run.
  - No release counts exist on Home or Manage.
  - Releases can't be found through Clips search or downloaded as a release CSV.
  - At 390 the panel's release line sits behind the details toggle.
  - RELCHECK may read page 2.
  - ~16 more "No pickup found" releases have release-text runs filed as tracker stories.
