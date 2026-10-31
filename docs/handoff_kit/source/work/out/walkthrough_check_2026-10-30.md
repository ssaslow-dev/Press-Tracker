# Walkthrough check, 2026-10-30

Tracker: `build_last/pipe_index.html`, served from a copy of `review_serve` (port 8811) and driven with Playwright. Sources: speaker notes (Claude Doc) and guide deck. Nothing was edited or published.

Status: OK = works as described; DIFF = works but the result differs; BROKEN = does not do what the page says.

## Cross-cutting findings

1. Search is now word matching ("all words, any order"). Quotes make no difference. Several single-result searches now return several rows.
2. List-only mentions are excluded from headline counts by default (INCL-v1). Most numbers in the notes were on the "all 3,672 logged" basis, so Politico 183 is now 178, AB 418 495 is now 454, and so on. Today the log holds 3,672 stories: 3,518 counted plus 154 list-only.
3. BROKEN (inconsistent state): the Data tab changes basis on its first control change. On a fresh load it says 3,518 stories (Politico 178, Spanish 163, national 511). After touching any Chart options control (Interval, From) it says 3,672 (Politico 183, Spanish 176, national 517); quarter totals shift too (3,457 since 2017 becomes 3,607). Nothing about the list-only setting changed. Notes should quote one basis, and the flip should be fixed before the demo. Below, "fresh" = fresh load, "after control" = after a control change.
4. "All time" is labelled "All dates".

## Steps and search strings

| Step | Instruction | What happened | Current value | Proposed wording | Status |
|---|---|---|---|---|---|
| Pre | Data tab, range "All time" | Opens on "Data: All coverage since 1993"; dropdown reads "All dates". | "All dates" | "date range set to All dates" | DIFF |
| Pre / 0:00 | Clips, `space station`: "one result, the 1993 LA Daily News story" | 22 of 3,672. The 1993 story ("YOUTH CAMP PIQUES INTEREST IN SCIENCE - SPACE STATION DESIGN", Apr 28, 1993, District & Valley) is the last row; the rest are noise. | 22 results | Search `space station design` (verify it returns only the 1993 story) or say "22 matches; the 1993 story is the last one." | DIFF |
| Pre / 0:35 | Clips, `Glock ban faces court challenge`, open Akron Beacon Journal row, then Story travel | 1 result (Oct 21, 2025, 48 reprints). "How it spread ›" opens Story travel: "Picked up by 48 outlets in 1 day", 51 copies. No spread curve on this page (all pickups on day 0 and 1); it shows the US map, top states (Florida 5, Michigan 5) and the pickup ladder. | 48 outlets | Drop "show the spread curve"; say "48 outlets in one day; here is the map." | 48 OK; curve step DIFF |
| Pre / 0:35 | Clips, `wants Peeps to change`, open AP row, then Story travel | 9 results, not 1. AP row ("The Associated Press News Service", Apr 7, 2023, 44 reprints) is among them. Story travel: 44 outlets in 3 days, furthest The Independent (London); curve and map both present. | 44 | Mention that the search returns 9 stories. | OK |
| Pre / 1:25 | Clips, `fresh legal fight over Nazi-looted art`: "42 pickups, including overseas" | 1 result: AP, Sep 19, 2026. Story travel: 44 outlets in 22 days (46 copies); furthest is KRON 4 (San Francisco County). No international outlet in the pickup ladder (28 out-of-state sources in 17 states). | 44; no overseas pickup | "44 pickups." Drop "including overseas" for this story. | DIFF |
| Pre / 2:15 | Bills, `AB 418` | 1 of 287 bills (Budget Act bills hidden by default). | works | Unchanged | OK |
| Pre / 2:15 | Press releases, `Landmark Legislation Banning Dangerous Food Additives` (Oct 7, 2023) | 11 of 241 releases match; the Oct 7, 2023 row is the 9th. Page: 72 related stories + 6 possibly related; ran it: 1. | 72 (+6 possibly) | "Pick the Oct 7, 2023 row (9th of 11)." | DIFF |
| Pre / 2:15 | Press releases, `Help Holocaust Survivors Recover Stolen Art` (Mar 28, 2024) | 3 results; Mar 28, 2024 is the third. Page: "Ran the release 4" (Contra Costa News, San Diego Jewish World, US Fed News...), 8 related, AB 2867. | works | Unchanged | OK |
| 3:00 | Outlets, `Politico`, first and latest story | 5 outlets match; first row is Politico (178 stories, first Jan 4, 2018, last Oct 5, 2026, full list on page). | works | Unchanged | OK |
| 4:10 | Reporters, `Ryan Torok`: "47 stories for the Jewish Journal"; open his page | 1 result; his page works when you click the name. 43 stories (Dec 17, 2014 to May 19, 2026): 34 Jewish Journal, 7 J. The Jewish News of Northern California. | 43 total / 34 | "43 stories, 34 of them in the Jewish Journal." | DIFF |
| 4:10 | Clips, "Quoted filter: 1,770" | No top-level filter named "Quoted". How Gabriel appears has Direct quote > Yes = 1,697 (his own words) and Mention depth > Quoted = 1,084 (a different measure). | 1,697 | "Filters, Direct quote, Yes: 1,697 stories." | DIFF |
| 0:00 | Data chart: "peak bar September 2026, 176, busiest month ever" | Default chart is Coverage by quarter (peak 210). Months need Chart options > Interval > Month. Busiest month is Sep 2023 (156); Sep 2026 is 145 (fresh) or 150 (after control). | Sep 2023, 156 | "Busiest month: September 2023, 156 stories." | DIFF (claim wrong) |
| 0:00 | "One story in 2013" | True only after Chart options > From 1993 (default From 2017 hides it). | 1 | Add the From 1993 setup. | OK with setup |
| 0:00 | "805 in 2023" | 726 (quarter sum, fresh); 740 after control and in Clips date filter 2023. | 726 to 740 | "About 740 in 2023." | DIFF |
| 1:25 | AB 418 timeline | Introduced Feb 2, 2023; signed Oct 7, 2023; latest story Oct 15, 2026; weekly chart with milestones. | works | Unchanged | OK |
| 1:25 | `AB 1264`, `AB 2316` | One result each: 273 and 258 stories. | 273 / 258 | See numbers | DIFF |
| 3:30 | County map, reach, format, languages | All present (Format = the Medium selector). Values differ, see numbers. | see numbers | See numbers | OK / numbers DIFF |
| 3:30 | "68 states and countries, including England and Israel" | 68 not reproducible. Outlets' County-or-state filter lists 134 options (50 California counties, 82 others); Data's map shows 45 states plus 13 clips outside the US. England (11) and Israel (12) are present. | not reproducible | "Outlets in dozens of states and countries, including England and Israel." | DIFF |
| 2:15 | "244 releases, 178 led to coverage" | 241 releases; 99 run by outlets; 180 with related stories. | 241 / 180 | "241 releases, 180 with related stories." | DIFF |

## Numbers to update

| Item | Notes / deck | Now |
|---|---|---|
| Stories on file | about 3,700 / 3,700 | 3,518 counted (3,672 incl. 154 list-only); "about 3,500" |
| Outlets | 1,300+ | 1,170 (Outlets tab) |
| Languages | 15 | 13 non-English (fresh), 14 (after control) |
| Spanish / Chinese / Korean | 178 / 106 / 48 | 163 / 102 / 41 (fresh); 176 / 103 / 47 (after control) |
| Most reprinted (Glock) | 48 | 48 (unchanged) |
| Peeps | 44 | 44 (unchanged) |
| Nazi-looted art | 42 | 44 |
| AB 418 / 1264 / 2316 | 495 / 295 / 286 | 454 / 273 / 258 |
| Three food bills combined | 857 | 798 (Clips filter, each once, includes list-only); "nearly 800" |
| Release coverage | 74 | 72 (+6 possibly related) |
| Releases / with coverage | 244 / 178 | 241 / 180 |
| Busiest month | Sep 2026, 176 | Sep 2023, 156 |
| 2023 stories | 805 | 726 to 740 |
| Outlets ranking | Politico 183, Sac Bee 155, CalMatters 106, LA Times 105, Jewish Journal 101 | Outlets tab by stories: Politico 178, Sac Bee 163 (153 originals), LA Daily News 152, Yahoo News 144, CalMatters 108, LA Times 108 (104 originals). Data brief: Politico 178, Sac Bee 153, LA Times 104 |
| Reach: CA local / statewide / national / international | 1,007 / 810 / 592 / 167 | 1,006 / 807 / 511 / 215 (fresh); 1,080 / 818 / 517 / 223 (after control) |
| Ryan Torok | 47 | 43 (34 Jewish Journal) |
| Quoted in own words | 1,770 | 1,697 |
| States and countries | 68 | not reproducible |
| "Figures as of" | Oct 29 | Newest story is Oct 27; re-date if re-pulled |
| Oldest story | 1993, LA Daily News | unchanged (Apr 28, 1993) |

## Deck-only checks

- "The tabs" slide: the eight tab names match the page.
- "Clips" slide: filters by date, issue, bill, tone, outlet, language, format all exist.
- "Good to know" slide: list-only wording matches the INCL-v1 rule.
- "What it is" slide: 3,700, 1,300+ and 15 languages no longer match.

## Minor

- AB 418 shows 456 in the Clips Bills filter and 454 on the Bills tab (Clips includes list-only).
- No page errors in any run.
