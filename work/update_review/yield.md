# Update button search yield (read-only review, 2026-10-30)

No code, data or artifact was changed; Update was not pressed. TinyFish and Claude were not called.

## 0. What could and could not be measured

| Wanted | Status |
|---|---|
| Per-pass "found by" in the workbook | **Does not exist.** `shared_data.load().coverage` has no pass column. `Data Source` has 8 values only; `Search lookup (Oct 26)` is a reprint-lookup note ("Found online", "Not found online; old tracker reprint list..."), not a pass. DECISIONS 2026-10-29 RECALLOPS keeps "found_by logging (already in v22 B6)" - it is code only: `41_update_search.js` line 680 stamps `c.found_by = kind: label`, `40_update_outlets.js` line 228 carries `_found_by`, and `42_update_buttons.js` line 75 saves only a per-kind **count** (`found_by: {kind: n}`) into the run doc. No row-level pass is stored anywhere. |
| Today's run (live tracker 5wHur4aRkSbAu6FscDpTjv) | **Not readable.** ArtifactData list on `runs`, `pages`, `clips`, `reprints` returned "No documents matched". Review queue `applied` is empty. Only `edits` has rows (3 shown, dated 2026-10-27). So I have no queries, fetches, finds, false finds, duplicates, time, TinyFish or Claude counts for today. Section 3 is therefore blank by necessity, not by choice. Needed: the run doc `run-<id>` (rows, `found_by`, `left`, `searched_to`, `U.failed`, `relpick`, `gnews`) or Sammy's run summary. |
| Yield per pass, historical | Three partial sources, below. The only one with per-query attribution is the 2026-10-28 new-outlet sweep. |

## 1. Yield per search type

### 1a. Per-query attribution: new-outlet sweep (agent-newoutlets, 2026-10-28)
Computed from `work/tmp_agent-newoutlets/searches_sofar.json` (1,251 search calls = query x page), `hits_sofar.json` (1,824 hit rows) and `work/out/newoutlet_finds.csv` (357 finds). A find's URL was normalised (scheme, www, fragment, trailing slash stripped) and matched to hit URLs. All 357 matched. "Unique" = returned by one query type only.

| Query template | Distinct queries | Search calls | Finds returning it | Unique finds | Finds per call | Unique per call |
|---|---|---|---|---|---|---|
| `"Jesse Gabriel" site:<host>` | 602 | 650 | 354 | **317** | 0.54 | 0.49 |
| `"Gabriel" "D-Encino" site:<host>` | 599 | 601 | 40 | **3** | 0.07 | 0.005 |
| both returned it | | | 37 | | | |

Check: 354 + 40 - 37 = 357. 151 of 1,251 calls (12%) returned at least one find; 1,100 returned none.

Unique finds by profile (name-site 317, D-Encino 3; the 357 as one set joined to the workbook by Publisher link, 355 matched):

| Cut | Result |
|---|---|
| Original / reprint (357) | 53 / 304 (name-site unique 44 / 273; D-Encino unique 2 / 1) |
| Medium (355) | Newspaper 161, TV 118, Online news 55, Radio 10, Newsletter/blog 6, Trade 2, Student 1, Wire 1, blank 1 |
| Language (357 csv) | en 350, es 5, blank 2. Workbook: English 344, Spanish 11 |
| Reach (355) | blank 237 (not yet assigned), California regional 53, Out-of-state local 42, Trade/advocacy 13, International 6, Jewish press+Intl 2, National 1 |
| Year | 2026 49, 2025 61, 2024 73, 2023 80, 2022 24, <=2021 70 (this was an all-time backfill of new hosts, so it is not a recency yield) |

### 1b. Aggregate, no per-find attribution: Oct 21 all-time run (code comment above `TF_AGG`, 6,418 searches, 1,942 new stories, 478 reprints)
Numbers are copied from that comment; I could not recompute them (the Oct 21 run files are not in the kit, as `work/tmp_agent-buttonopt/yield.md` also notes).

| Pass | Searches | New stories | New per search |
|---|---|---|---|
| `"Jesse Gabriel" site:<outlet>` | 1,056 | 931 | 0.88 |
| Open-web `"Jesse Gabriel"` (monthly) | 118 | 273 | 2.31 |
| News-only search | n/a | 6 | n/a |
| Yahoo/AOL/MSN copies | n/a | 89 (+ many reprints) | n/a |
| `"Gabriel" "D-Encino"` on outlet sites | n/a | ~70 | n/a |
| His bills | n/a | 22 | n/a |
| Wire headlines word for word, GDELT TV | n/a | "paid off"; TV 34 | n/a |
| Dropped: name variants (Assemblymember, Asm., Budget Chair...) | 360 | 4 | 0.01 |
| Dropped: Spanish "asambleista" | 166 | 3 | 0.02 |
| Dropped: YouTube | 40 | **0** | 0 |
| Dropped: podcasts and radio | 197 | 5 | 0.03 |
| Dropped: TV station names on aggregators | 150 | 8 | 0.05 |
| Dropped: trade-press D-Encino | 290 | **0** | 0 |

Workbook cross-check of the 2,602 `Tracker scrape` rows: that is the Oct 21 run's output. 2,079 originals, 523 reprints.

### 1c. By workbook `Data Source` (all 8,169 Coverage rows; who found it, not which query)
Computed with `pd.crosstab` on `load().coverage`.

| Data Source | Rows | Orig | Repr | Notes |
|---|---|---|---|---|
| Newsbank | 3,874 | 1,584 | 2,290 | print and wire; Newspaper 2,709, Wire 473, Spanish 184, no web reach |
| Tracker scrape | 2,602 | 2,079 | 523 | web: Online news 1,314, TV 400, Trade 217, Newsletter 155; all the Chinese 120, Korean 65, Hebrew 17, Russian 20, Persian 8, Vietnamese 12 |
| Tracker reprint list | 920 | 33 | 468 (+419 unverified) | |
| Web search (TinyFish) | 397 | 75 | 322 | the sweep above plus follow-ups; Newspaper 173, TV 119, Online 77, Radio 10, Spanish 15, Korean 1 |
| ProQuest | 336 | 271 | 65 | |
| Reprint credit (no copy) | 25 | 25 | 0 | |
| Podcast search (Exa) | 14 | 14 | 0 | |
| People search (Exa) | 1 | 1 | 0 | |
| **Live Update button** | **0** | | | no `Data Source` value for it exists yet, because the sheet task is DISABLED (START_HERE, HANDOFF G2); the button has never written a row to the workbook |

## 2. What the past finds share, and what no pass has found

Common to the 357 sweep finds: English-language (98%), on a **named outlet's own site** (the site: pass cannot find a host it is not told about), mostly reprints (85%) of a wire/regional story, newspaper or TV-station web copies (78% combined), dated within the Gabriel-name-in-text window, and outlets with 1-2 stories on record. Reach is not yet set on 67%.

Never found by any web pass (evidence in parentheses):
- **Print-only NewsBank / ProQuest items**: 3,874 + 336 rows come only from Sammy's logged-in downloads. The audit (work/tmp_recall_audit/findings.md) says web search cannot see them; the page says NewsBank supplies "about 1 in 6 recent stories".
- **Broadcast with no web story**: TV 865 rows, but only web-posted stories; LA broadcast without captions or a clip is a stated gap. Video 8 rows; the audit found **0 of 5** YouTube uploads in 4 windows. YouTube 0/40 on Oct 21. The RECALL-v1 station-channel pass (5 queries) has no measured yield yet.
- **Podcasts / radio audio**: Podcast 14 rows, all from Exa (now forbidden); Radio 146, 10 from TinyFish.
- **Non-English beyond the native-script searches**: 0 Chinese, Hebrew, Russian, Persian, Vietnamese, Armenian rows from `Web search (TinyFish)`; one Korean. Audit: recall 40% for foreign-language editions (ToI French, Chosun Daily, FAM Times missed).
- **AP/Lee/Sinclair small-market reprints** (about 0% of the long tail), **Valley News Group sister editions**, **late derivative pickups** (>3 days after the event), **health-wire syndications** (25%): audit recall 60-84% by window, 74% overall (80 found by hand, 59 in the sheet). Upper bound only: the audit notes the search index is thin for 2024-25.

## 3. Today's run
Not retrievable (see section 0). Nothing is estimated here because any figure would be invented. What the plan was built to do, from the code: the default plan is about **780 base calls** (since 2026-10-24) per the 2026-10-28 plan dump in `work/tmp_agent-buttonopt/yield.md`, recommended cut to about 572; BUTTONOPT-v1 dropped issue words and D-Encino-40; RECALL-v1 added fresh OR-of-10 passes, 5 YouTube queries, 4 sister-edition queries, second-language editions, one Google News fetch (up to 10 feeds), per-release pickups (up to 8 releases x 3 searches), TV via GDELT, one leginfo fetch, release listing fetches. Candidate fetches are batches of 10 URLs; Claude screening is 20 candidates per call at the lightest tier. To fill this section: read the run doc from `runs`, plus the TinyFish usage log for the account.

## 4. Zero and near-zero yield

| Pass | Evidence | Verdict |
|---|---|---|
| YouTube (generic) | 0 of 40 searches, Oct 21 | zero; the new station-channel pass is unmeasured |
| Trade-press D-Encino | 0 of 290, Oct 21 | zero (dropped) |
| D-Encino site: (sweep) | 3 unique of 357 finds from 601 calls; 598 calls added nothing | near-zero; already dropped from the plan |
| Name variants as news search | 4 of 360 | near-zero (dropped) |
| "asambleista" | 3 of 166 | near-zero (dropped) |
| Podcasts and radio | 5 of 197 | near-zero (dropped) |
| Issue words (120/run) | never measured; dropped by BUTTONOPT-v1 | unknown |
| Native-site searches for Chinese/Vietnamese | 0 backtest loss; the English site: search covers them | redundant |
| Sweep: native-site | 3 searches, 0 results | zero |
| RECALL-v1 passes (fresh OR, sister, second-language, YouTube stations, Google News) | no `found_by` stored per row; only per-kind counts in the run doc | **cannot be assessed from workbook; today's run doc would answer it** |

## 5. Cost per real find
Only the sweep can be costed, and only in calls, not money (no TinyFish price or usage log in the kit).

| Item | Count | Basis |
|---|---|---|
| Search calls | 1,251 | searches_sofar.json |
| Fetch calls | 74 (10 URLs each) | fetch_batches.json; 731 URLs fetched (fetch_index.json), 409 saved pages (pages/) |
| Finds kept | 357 (53 originals, 304 reprints) | newoutlet_finds.csv |
| False finds (fetched, not kept) | 731 - 357 = 374 | fetched minus kept; a rough share, since some of the 731 were dedupe or non-Gabriel pages |
| TinyFish calls per find | 1,325 / 357 = **3.7**; per original 25 | 1,251 + 74 |
| Per unique find, name-site only | 650 / 317 = 2.1 search calls | |
| D-Encino site: | 601 / 3 = **200 calls per unique find** | |
| Claude (estimate, not logged) | tone/screen about 357 reads | assumption: one pass per kept find, about 2k tokens each in and 0.3k out = roughly 0.7M in / 0.1M out tokens for the 357; screening per design at 20 per call |
| Time | not recorded | the button spaces calls by TF_GAP 2.1 s: 1,325 calls is at least about 46 min |

Dollar cost per find: **not computable** from files in the kit.
