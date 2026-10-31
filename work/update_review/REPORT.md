# Update button review: debug, optimize, rethink (2026-10-30)

Reviewer: Fable (judgment and design only). Legwork by the coordinator's Haiku agent (sources_catalog.csv), Sonnet agents (yield.md, results/REQ-*.md) and this reviewer's own reads of the code and the live database. Nothing live was changed: no publish, no workbook write, no database write, no scheduled-task change, Update not pressed. TinyFish was not available to this session (its tools were not loaded; HANDOFF already lists "needs re-authorizing"), so the two web probes used curl.

Baseline: `bash build/tests/run_all.sh` on the kit as handed over = 42 suites, fail=0, skipped=0 (tests_out/baseline_run_all.log).

## 1. One page

**What it is.** Press Update -> the browser tab runs about 700 TinyFish searches (plus deep pages) serialised at 2.1 s, fetches every candidate, screens and classifies with Claude, writes one run doc to the artifact database, fires a scheduled Claude session that reads the database, writes the master workbook on the Mac by following a 58-line prompt, rebuilds and republishes. The sheet half has never completed a live run; the search half was still running more than an hour after Sammy pressed it while this review was written.

**Top five problems**
1. **Nothing is persisted during the search (P1).** The run doc is written only at the very end of `runAll` (42_update_buttons.js:72); the "provisional" doc of CODEREVIEW F7 is written inside `saveFound` (41:979), i.e. also only after the whole search, and only when something was added. A closed tab, laptop sleep, lost connection, or a JS exception after the search (the body of `runAll` has no `catch`) loses an hour of metered TinyFish calls with no trace. The live `runs`, `clips`, `pages`, `reprints` collections were empty mid-run, exactly as the code predicts. Unconfirmed finds (`_on` false) are never saved anywhere.
2. **Silent persistence failure, then firing a ghost run (P1).** `saveRun` swallows errors and returns false; `runAll` ignores that and still calls `fire_trigger` with "Log entry: run-xxx". If the `db` capability was declined or failed, the page shows "Done", the task runs on nothing, and the finds exist only in that tab. (`fire_trigger` on the DISABLED task is also reported as "Only the tracker's owner can update the spreadsheet", a misleading message.)
3. **Every press is a backfill sweep (P1 cost/stall).** `tfPlan` searches every outlet host on record (654 hosts; undated `"Jesse Gabriel" site:host 2026`; up to 10 pages when a page is full) on every run. Right for the Oct 21 and Oct 28 backfills (0.5 unique finds per call, yield.md) but for a weekly incremental run its marginal yield is near zero while its cost is fixed: REQ-5 measured the plan on the built page: 702 searches (614 of them undated per-outlet deep items, 51 date-filtered `fresh` groups, 14 core, 6 bills, 5 reprint headlines, 5 YouTube, 4 sister), a 24.6-minute floor at 2.1 s per call before a single page is fetched, and a worst case of +5,526 calls if every deep item paged to its limit. `tfCall`'s global gate makes the "two workers" sequential, so only fewer calls can shorten it.
4. **One fetch error drops ten stories with a false reason (P2 recall).** A thrown `fetch_content` for a batch marks nothing on its candidates (41:749); the un-fetched ones are later dropped as "Gabriel isn't named in the page text" (41:765-766) and never retried. `U.failed` counts the batch as one failure, so `searched_to` can still advance.
5. **The sheet task is armed with a stale prompt and fires despite "disabled" (P1 integrity).** list_triggers shows the task `enabled: false` yet it ran (SUCCEEDED) 6 seconds after today's run doc, in auto-approval mode, with the 2026-10-27 prompt that writes `~/Documents/Gabriel press PDFs/AJG Coverage - NewsBank.xlsx` (HANDOFF: not the master) in green font with the old rules. Only the missing Mac link stopped it. On top of that `verify()` checks Coverage only (section 3, B6), and the 58-step LLM orchestration has never completed live. See section 9 M6 for the fix.
6. **Four of the 15 new Originals in today's run are wrong as proposed** (an iHeart copy of s02206, a login-walled copy of s00327, a staging-host duplicate of 01859, a personal blog) and two more need a hand (a 2028 date, an e-paper page): dedupe and date extraction, not Claude's judgment, are the weak stages (section 9). `verify()` checks Coverage, Originals and Removed reuse; the Press releases, Audio & video, Bills and Unlinked print tabs can change or lose hyperlinks and the commit still goes through. The orchestration (about 20 tool calls across ArtifactData, the Mac bridge with 45 s timeouts, SendUserFile commits, batched publishes) is re-derived by a fresh Claude session each run; the chain of local steps has never been run end to end by one script.

**Top five opportunities**
1. **Split "watch" from "backfill".** Weekly watch = date-filtered passes only (core name + native scripts, the OR-of-10 `fresh` groups over the 419 hosts active in 24 months, reprint headlines, release pickups, Google News RSS, GDELT TV): roughly 150-200 calls. The undated per-outlet sweep becomes a separate "Backfill outlets" run, monthly over active hosts and quarterly over dormant ones. Expected: about 75-80% fewer TinyFish calls per press and runs that end before anyone closes the tab.
2. **Checkpoint and resume.** A `runs/<id>` heartbeat doc at start and every 25 searches, the candidate list saved before the fetch phase, a "Resume" path on the next press. Worst case goes from "lost hour" to "lost two minutes".
3. **Move bills and TV off TinyFish.** LegInfo's author search is bot-blocked (the check is skipped every run after two 90 s tries): LegiScan's free API (30k queries/month, CC-BY) or OpenStates v3 (free key) answers it in one call. GDELT TV and GDELT DOC 2.0 (free, no key, 65 languages, one request per 5 s) can be read by the sheet task directly instead of through metered TinyFish fetches.
4. **Push feeds for the top outlets and the ethnic press.** One `fetch_content` call reads ten RSS feeds; Google Alerts delivers to RSS; the Ethnic Media Services directory (about 300 California outlets with languages) seeds the hosts a `site:` search cannot know about. This is the only cheap route to non-English coverage (2% of web finds today, yield.md).
5. **A deterministic sheet-task driver.** One `sheet_task_run.py` that executes prompt steps 1, 3 and 6 locally with a state file and prints the exact tool calls (ArtifactData batch payloads, commit list, publish map) for the LLM to copy. The prompt shrinks to "run the driver, make these calls, paste the outputs". REQ-8's rehearsal script is the first step and the first proof that the chain works.

Decisions for Sammy are in section 7.

## 2. Pipeline map

| Stage | Where | Inputs | Outputs | Cost per run | Failure modes | Tests |
|---|---|---|---|---|---|---|
| Button press, confirm | 42 `raConfirm` -> `runAll` | - | `RA.run` id | - | a busy run just opens the panel | none |
| Release check | 41 `releaseCheck` | 2 listing pages x <=2 pages, `ins-release_pickup` block | `U.newrels` (oldest 5 fetched as HTML <=40 KB) | 2-4 fetch calls + <=5 page fetches | selector change -> "listing not read" (only in `relcheck`) | test_relbutton (sheet side) |
| Plan | 41 `tfPlan` + `tfDedupe` | D (3,667 tracker stories), BILL_INFO, release texts | 702 items (REQ-5: 614 outlets-deep, 51 fresh, 14 core, 6 bill, 5 reprint, 5 youtube, 4 sister) | 0 | cached per since+size | test_recall.js |
| Search | 41 `one()` x2 workers, `tfCall` 2.1 s gate | plan | `cands` (url -> candidate), `U.reprints` | plan + deep pages, minutes = calls x 2.1 s | auth lapse -> STOP_CODES abort; `after_date` dropped for `site:` (recall vs cost); reprint items lose the late window (B5) | none for `one()` |
| New-outlet backfill | 41:692-700 | cands naming him on unknown hosts | more all-time deep items | up to 10 pages per new host | a stray host costs 10 calls | - |
| TV captions, Google News | `tvCaptions` (GDELT TV via TinyFish), `gnewsSearch` (<=10 RSS feeds, 1 call) | since | candidates | 3 calls | GDELT JSON parse; feed links resolve only on fetch | - |
| Pre-filters | 41:714-720 | cands | drop no-Gabriel-no-bill snippets; cached dead links; blocked hosts unfetched | 0 | - | test_final_int_js (lists) |
| Fetch | 41:722-758, batches of 10 | candidates | `c.page` (<=400 KB), text, date, byline | ceil(n/10) calls (+ a pass for undated hosts) | batch error -> candidates dropped with a false reason (B4) | - |
| Screen (quick tier) | `screenPrompt`, 25 per call | title + 700 chars | keep/drop | ~4k tokens per call | failure -> all kept (safe) | - |
| Classify (default tier) | `classifyPrompt`, 20 per call | 1,800 chars each | row fields, tone; bills also by `tagBills` rules | ~11k tokens per call | sampling denied -> `guessRow`, rows not auto-added and not persisted (B1) | test_opeds_js, reachguard_js |
| Origin credit | `originCredit` | finds with wire/credit/aggregator signals | `_origin` candidates + `og-` pages | 1-4 calls per such find | - | agg_origin_js |
| Page-side dedupe | `covHit`, `dupOf`, `covRepKnown` | `rows` block (all Coverage rows, Removed as kind X) | drops, reprint candidates | 0 | headline Jaccard >=0.7 within 14 d; the text rule is the sheet task's | final_int_js |
| Reprint pages | `reprintPages` | `U.reprints` | `rp-` page docs | ceil(n/10) calls | - | - |
| LegInfo | `leginfoCheck` | author-search URL | `bills_new` | 2 x 90 s, skipped every run (bot wall; review item 12-process) | 3 wasted minutes | - |
| Add / save | `saveFound` -> `clips`, `authors`, `translations`, `pages` (clean + article-scoped re-fetch), `reprints`; `proposeRows` | finds `_on` | run rows (CONTRACT "Proposed rows"), provisional run doc | ceil(n/10) fetch calls | db null -> "for this visit only" | test_final_int_js |
| Translate | `translateHeadlines` | new non-English | `translations` | sample calls | - | - |
| Run doc | `saveRun` | all of the above | `runs/run-<id>` | 1 write | swallowed errors (B1/B2) | - |
| Fire | `fire_trigger(trig_01WRLX...)` | run id | scheduled session | - | DISABLED task -> misleading text (B9) | - |
| Sheet task session | sheet_task_prompt.md steps 1-7 | db export, pipeline files, Mac master | new workbook, pages, republish | one Claude Code Remote session, >=20 tool calls | never completed live; Excel lock; Mac offline; 45 s device_bash; stale staged copy | fixtures only |
| sheet_task.py main pass | `Task.run` | db.json, in.xlsx, copies, bills, release texts, queue | out1.xlsx, result.json, pages/, copies_out/ | ~2 min on the real master | exit 2 on verify (Coverage only, B6) | 13 suites |
| build_data -> relmatch -> after-relmatch -> tabs_data -> assemble | prompt steps 3/6 | out1.xlsx, blocks | committed workbook, index.html, sheet.json | ~1 min | chain never run as one script (REQ-8) | build.sh covers the build only |
| Commit, write-back, publish | device_commit_files, ArtifactData batch, Artifact publish | | master, db `ids`/`sheet`, pages docs deleted | | failure between commit and write-back re-applies the run next time (link dedupe makes most of it idempotent; link-less rows can duplicate, B10) | none |

Cost per press (estimates; TinyFish's per-call price is not in the kit, so calls are the unit): plan-size searches (REQ-5) plus deep pages, plus 30-100 fetch calls; Claude about 60-120k input tokens on the viewer's account (screen + classify + translations); the sheet session's tokens are separate and dominated by tool traffic.

## 3. Bugs

P1 = can lose real stories, corrupt or stall; P2 = wrong data or wasted cost; P3 = cosmetic or edge.

| # | Sev | Bug | Evidence | Repro / test | Patch |
|---|---|---|---|---|---|
| B1 | P1 | No persistence during the search; no `catch` around `runAll`'s body; unconfirmed finds never saved. PATCHED: patches/REQ-2_run_persist.patch; test fails 7 of 14 checks unpatched, 13/13 pass patched; run_all fail=0 on the patched tree (results/REQ-2.md) | 42:26-99 (no catch); 43:60 `saveRun` swallows; 41:979 provisional only inside `saveFound`; live db empty mid-run (ArtifactData list of runs/pages/clips/reprints/tones/authors/notes/views: 0 docs; `edits` 5 docs from 10-27/28) | REQ-2 playwright scenarios A-C | REQ-2 (heartbeat doc, catch, `unconfirmed`, localStorage fallback) |
| B2 | P1 | Fires the scheduled task when the run doc was not saved; the "Nothing new" path hides a store failure | 42:72-86 ignores `saveRun`'s return | REQ-2 scenario B | REQ-2 |
| B3 | P1 (cost) | Every run repeats the all-time outlet sweep: 614 undated `site:` deep items (593 hosts) of a 702-item plan, 24.6 min floor, up to +5,526 calls of paging | 41:99-101, 683-685; results/REQ-5.md | REQ-5 | design D1 |
| B4 | P2 | Fetch-batch error drops up to 10 candidates with the reason "Gabriel isn't named"; failure counted once per batch | 41:749, 765-766 | REQ-6 | REQ-6 |
| B5 | P2 | Reprint headline searches send `after_date = U.since`; the 21-day late-pickup window (`minDate`) never returns anything. PATCHED: REQ-1 (one line), test fails unpatched, 8/8 patched | 41:108-112 vs 649-652 | REQ-1 | REQ-1 (one line) |
| B6 | P1 (integrity) | `verify()` ignores every tab but Coverage/Originals (+ Removed reuse); hyperlinks unverified. PATCHED: REQ-3 `verify_tabs` (8/8; the real master self-checks clean in 1.9 s; existing suites green) | sheet_task.py 4114-4182 | REQ-3 | REQ-3 |
| B7 | P2 | LegInfo check: 2 x 90 s fetch of a bot-blocked page every run, always "skipped" | 41:401-427; review item 12-process | - | LegiScan/OpenStates (section 5) |
| B8 | P2 | `has_work` treats any `pages` doc as work; an orphan `og-`/`rp-` doc makes every later run stage, write nothing and republish | sheet_task.py 4201 | REQ-7 | REQ-7 |
| B9 | P3 | `fire_trigger` on the DISABLED task reported as "Only the tracker's owner can update the spreadsheet" | 42:91-95 maps `tool_error` to the owner text | - | map a `tool_error` naming the trigger state to "The spreadsheet task is switched off" |
| B10 | P2 | Link-less rows (no-copy originators, TV clips with an empty `preview_url`) are not idempotent across a half-finished sheet run (commit done, write-back failed -> re-applied next time) | `add_row` dedupes on `identity_links` only | later | write `ids_pending` to the run doc before the commit; skip placeholders already mapped |
| B11 | P3 | `tfCall` reserves the 2.1 s slot before waiting, so two workers never overlap; the panel's "two at a time" overstates | 41:9-11 | REQ-5 | none if D1 lands |
| B12 | P3 | `U.failed` mixes search, fetch, TV and Google News failures; the 2% rule for `searched_to` is therefore not "2% of searches" | 42:73, 41:194/358/656/749 | - | count per kind |

Recurring bug classes from the brief, status in code: aggregator-as-original (`agg_origin_step`, `TF_AGG_HOSTS`, tests green); same-house editions (`outlet_rules` houses, REPRINT-v2); wrong-Gabriel (`wrong_gabriel`, screen prompt); broadcast ET dates (AVTAB-v2 / REVIEW4 F1, `localDay` zone guard); quote misses (`quoted_him`, test_quoted green); list-only (`mention_depth`); reach spreading (`reach_guard`, REACHFIX). No new regression found there; the open risks are persistence, cost and orchestration.

Live-db note: the 5 `edits` docs are harmless to the first live run: s01821/s01822 removals were already executed by hand (both on the Removed tab; `execute_removals` clears such requests), and s01921 (AB 2378), s02597 (headline) and s04738 (date) already hold those values, so they clear as "same".

## 4. Optimizations

| # | Idea | Saving (estimate) | Risk / cost |
|---|---|---|---|
| O1 | **Watch/backfill split (D1).** Weekly = `core` (14) + `fresh` OR-of-10 over active hosts with `after_date` (51) + `reprint` (5-33) + `release` (<=24) + `bill` (6) + `youtube`/`sister` (9) + Google News + GDELT TV. Backfill = today's 614-item deep outlet sweep, monthly for the 421 active hosts, quarterly for the rest, resumable | 702 (+paging) -> about 110-140 calls per press (about -80%, more once paging is counted); search phase about 5 min instead of 25+ | date-filtered `site:` searches drop undated results (Oct 21 note: 2 of 10 LA Times results kept). The monthly backfill keeps the undated sweep; A/B with per-row `found_by` (O6) |
| O2 | **Checkpoint/resume (REQ-2 + resume)** | a lost tab costs <=25 searches | <=40 small db writes per run |
| O3 | **Fetch retry (REQ-6)** | recovers up to 10 stories per transient error | +1 call per failed batch |
| O4 | **Drop the LegInfo fetch (B7)**; LegiScan/OpenStates once a week from the sheet task | -2 calls, -3 min per run | a free key the office owns |
| O5 | **Per-host "last new URL seen" cap:** a host with nothing new in 3 runs leaves the weekly plan (stays in backfill) | -20-30% of `fresh` calls over time | a dormant outlet's rare story waits for the monthly backfill |
| O6 | **Per-row `found_by` into the sheet** (column or Team note) | makes every yield question answerable (today none is, yield.md s0) | one fill-only column |
| O7 | **Claude calls:** cap `ctx` at 1,200 chars for reprint candidates (the sheet task re-judges them by text) | about -30% classify tokens | none material |
| O8 | **Run-doc size:** strip `_text` (6,000 chars per row) from the run doc; keep it in `pages` | run docs about 10x smaller; faster step 1 | check `find_text` (sheet_task.py 2810) falls back to the page doc |
| O9 | **Cadence:** weekly watch + monthly backfill; the release check runs first in every watch run | predictable TinyFish spend | none |
| O10 | **Sheet-task step 1 reads all runs every time:** query `status == 'queued'` once REQ-2's `status` exists | step 1 stops growing with history | none (no old docs exist) |
| O11 | **Concurrency:** keep one call per 2.1 s (TinyFish's ~30/min) | none safe | 429s |

## 5. New sources and approaches

From sources_catalog.csv (27 sources), work/out/missing_outlets_2026-10-30.csv (43 outlets, 9 with confirmed stories) and two probes. Any key below would be the office's; none was used here.

| Source | Cost / terms | Coverage for this tracker | Plug-in | Verdict |
|---|---|---|---|---|
| **GDELT DOC 2.0 API** | free, no key; one request per 5 s (my second call within 5 s got a 429 saying so); last 3 months; 65 languages machine-translated | online news incl. non-English; not print, not broadcast | sheet task or a daily watch pull (`"Jesse Gabriel"`, `sourcelang:`); candidates into the same fetch/classify path | adopt for the watch list and non-English; call it server-side, not from the browser (rate limit; CORS unverified) |
| **GDELT TV / Internet Archive TV News** | free | national networks + SF Bay Area; **no Los Angeles market** | already used via TinyFish; call directly from the sheet task | keep; LA broadcast stays a gap |
| **TVEyes** (or Critical Mention) | quote only; trial | TV + radio + podcasts, LA stations, 43 languages | alerts by email/API -> candidates; the only route to LA broadcast and radio | decision for Sammy (budget) |
| **YouTube Data API v3** (not in the catalog) | free key, 10,000 units/day (a search = 100) | station channels' uploads; replaces `site:youtube.com` (0 of 40) | sheet task: `search.list q="Jesse Gabriel" channelId=` for the RC_YT_STATIONS list | adopt |
| **Podcast Index API** | free key, open index | episode titles/descriptions; no transcripts | weekly `search/byperson` + episodes of shows on record | adopt (replaces the forbidden Exa podcast search) |
| **Listen Notes** (150 req/mo free) / **Taddy** (free dev tier, transcripts) | free tiers | episode search; Taddy has transcripts | same | try after Podcast Index |
| **LegiScan API** | free, 30k queries/mo, CC-BY | CA bills by sponsor | replaces the LegInfo fetch (B7) | adopt |
| **OpenStates v3** | free key | same | alternative | fine |
| **LegInfo bulk pubinfo zips** | free | authoritative | weekly diff of BILL_TBL for author = Gabriel | if LegiScan lags |
| **Google Alerts -> RSS** | free | Google's index; push | one `fetch_content` of <=10 feeds per run (same path as Google News RSS) | adopt |
| **Outlet RSS feeds** (Jewish Journal validated; missing_outlets lists Civil Eats, Palisadian-Post, The Reload, The Hill, LA Blade, Streetsblog) | free | top outlets, district weeklies | 1 call per 10 feeds, filtered by name | adopt for the ~30 busiest and the district weeklies |
| **Ethnic Media Services directory** (~300 CA outlets, form-gated PDF) | free | the in-language outlets a `site:` search cannot know | seed `outlets.json` hosts + language; native-script `site:` queries | adopt (one-time; Sammy fills the form) |
| **NewsBank / ProQuest alerts** | included in the State Library access; alert/RSS availability unverified (pages blocked) | print and wires: the "1 in 6" the web never sees | saved-search alerts to Sammy; monthly export as today | ask the State Library; keep the monthly reminder |
| Media Cloud | unverified | large source list | later | only if GDELT disappoints |
| NewsAPI.org / GNews / Mediastack | $449+/mo; free tiers forbid production or are tiny | general news; no ethnic focus | - | not over GDELT + RSS |
| Bing News API | retired Aug 2025 | - | - | no |
| Event Registry, Feedly | not readable (bot-blocked) | - | - | unknown |

Approaches:
- Push vs pull: email alerts (Google Alerts, NewsBank saved searches, TVEyes) into a dedicated inbox read through the Gmail connector works but adds a second ingestion path; RSS delivery of the same alerts through the existing one-call feed fetch is simpler. RSS first; email only where nothing else exists (NewsBank, TVEyes).
- Smarter dedupe: the 25-word-run text rule is already a shingling rule; the gap is attribution/idempotence (B10) and, later, speed. A MinHash index over `articles/*.json` would make `reprint_check` constant-time per find; not needed until runs carry hundreds of finds.
- Non-English: GDELT DOC with `sourcelang`, the EMS directory hosts with native-script `site:` queries, Google News locale feeds (add he, fa, hy, ru, vi to es/zh/ko).
- Watch list between full runs: GDELT DOC + RSS/Alerts + release check, no sweep, no deep paging: about 20 calls; could run daily from the sheet task with no browser (D2).

## 6. Design

- **D1 Two buttons, two plans.** "Update database" = watch plan (O1); "Backfill outlets" = today's sweep with a host cursor in the run doc so it resumes. Same code, a `mode` flag on `tfPlan`.
- **D2 Search on the scheduled side (big bet).** The page queues `runs/<id>` with `status: 'queued'` and the since date; the scheduled task does search + sheet in one Claude Code Remote session with TinyFish MCP, Haiku for the fetch loops (MODELS-v1), resumable, no browser open. The page keeps the review panel for `unconfirmed` items. Removes B1/B2/B11 by construction and logs every call. Cost: the task's tokens; needs the task enabled (HANDOFF D3) and TinyFish authorised for that account.
- **D3 Deterministic driver for the sheet half.** `sheet_task_run.py <workdir>`: steps 1 (assemble db from out_dir files, check-only), 3 (all local commands), 6 (rebuild), writing `state.json` after each step and `tool_plan.json` listing the ArtifactData batches, commit paths and publish map. The prompt becomes about 15 lines. REQ-8's `rehearse.sh` is its first draft.
- **D4 Verify everything (REQ-3), and verify on the Mac:** after the commit the task runs a `--verify-only before after` on the committed copy, not only on the staged output.
- **D5 Reference data first stays;** add "last new URL seen" per outlet to `outlets.json` to drive O5.

## 7. Roadmap

Quick wins (this week, no decisions needed)
1. REQ-1, REQ-2, REQ-6, REQ-7 patches + REQ-3 verify-all-tabs; run_all green; republish `pipeline/sheet_task.py` and the page.
2. B9 message fix.
3. O8 (strip `_text` from run docs) and O6 (`found_by` column) in the same publish.
4. REQ-8 rehearsal once on the real master copy; fix any prompt/flag mismatch it finds.

Medium (2-4 weeks)
5. D1 watch/backfill split, with REQ-5's plan size as the before number; one month of A/B (`found_by`) between the date-filtered `fresh` pass and the undated sweep.
6. LegiScan or OpenStates for bills; YouTube Data API for station channels; Podcast Index; Google Alerts RSS + top-outlet RSS; EMS directory seeding of non-English hosts.
7. D3 driver + a supervised first live sheet-task run (HANDOFF D3), with REQ-3 verify in place first.

Big bets (decide, then 1-2 months)
8. D2 search on the scheduled side.
9. Paid broadcast monitoring (TVEyes / Critical Mention) for LA TV and radio.

Decisions for Sammy, plainly
- Pay for TVEyes or Critical Mention (quote; typically four figures a year) to catch LA TV and radio? Without it, LA broadcast without a web clip stays uncaught.
- Create free, office-owned API keys: LegiScan (or OpenStates), YouTube Data API, Podcast Index? (No cost; minutes each.)
- Accept weekly watch + monthly backfill instead of a full sweep per press (far fewer TinyFish calls; a dormant outlet's story can wait up to a month)?
- Move the search into the scheduled task (D2) so no browser tab must stay open, at the price of the task's own token spend and enabling the task?
- Ask the State Library whether NewsBank/ProQuest saved-search alerts are available to him?
- Fill the Ethnic Media Services directory form (free) so the in-language outlet list can be seeded?


## 9. Real-world trace: Sammy's run of 2026-10-30 (run-mvvcnrpbuuz) and Prevention

**What the run did** (results/trace/runs/run-mvvcnrpbuuz.json, written 19:47:17Z; the press was before 19:25Z, so the search phase ran well over 20 minutes): 722 searches planned, 86 failed (12%, so `searched_to` did not advance and the next run repeats the window), `found_by` core 2 / fresh 1 / outlets 12 (the undated outlet sweep found 12 of the 15 stories, 10 of them older than 2026), 19 proposed rows (15 Originals, 4 Reprints), 73 dropped, 5 lookups (all blocked hosts: Marin IJ and Santa Cruz Sentinel login walls, lakeconews, two podcastrex pages), LegInfo "89 bills, none new" (so the bot wall did not bite this time), releases none new, Google News 0 items (the feed fetch returned nothing: worth a look), 10 page docs saved, every one with `scoped: ''` (the article-scoped re-fetch produced nothing for all ten; the sheet task will clean the whole-page copies). The scheduled task then ran TWICE within a minute (its `sheet.line`: no Mac tools either time) although the task is "disabled" (section M6 below). The run is still queued: `sheet` has no `at`, so `run_done` is false.

**The 19 rows: accept, fix or drop**

| # | Row | Verdict | Reason |
|---|---|---|---|
| 1 | The Independent, "New label will boost non-ultra processed foods", Date 2028-06-01 | fix date, accept | the page names him (AB 2244 seal); the date is the law's deadline "by June 1, 2028" misread as a byline date (M1); real date from metadata |
| 2 | Van Nuys News Press, "$2.5 Million to the Mid Valley Family YMCA" | accept | district outlet; the sheet task's release text rule decides Press release = Yes |
| 3 | Capitol Weekly, prison sports / AB 2204 | accept | straight coverage |
| 4 | Van Nuys News Press, faith communities / AB 395 | accept | as 2 |
| 5 | Colion Noir (mrcolionnoir.com), Glock lawsuit / AB 1127 | accept, Sammy to confirm | names him and quotes his statement; a single-author gun-rights blog: press by the standing rule ("blogs count"), Reach Trade, advocacy & blogs; whether YouTuber blogs belong is a policy call (M3) |
| 6 | Sing Tao Daily e-paper page "07_02_2026星島日報（美東版）" | fix by hand or review | the page text names 蓋博（Jesse Gabriel）and AB 1127, so it is Chinese print coverage, but the row is a flipbook page: Headline must come from the article, Format Print, Language Chinese; belongs with the print pages, not as a web Original (M2) |
| 7 | KIIS FM, "California Bill Targets Ultraprocessed Foods at the Grocery Store" | fix: Reprint/edition of s02206 | the master already has this iHeart LA copy as s02206 (Patriot LA, 2026-03-25, headline with " \| The Patriot KEIB AM 1150" suffix); not a new story (M5) |
| 8 | KFI AM 640, same | fix: edition of s02206 | same iHeart LA newsroom copy |
| 9 | The Cool Down, leftovers listicle, Date 2026-01-01 | review | no page was saved for it (the page text did not pass the full-name test), so confirm it names him; 2026-01-01 looks like a year-only date; if confirmed it is a List-only / passing mention, kept and badged under INCL-v1 |
| 10 | Tistory (why4416.tistory.com), Korean food-trend post | drop | a personal blog on a blog platform; not press (M3) |
| 11 | Marin Independent Journal (blocked), "poised to approve most significant environmental law rollbacks" | fix: Reprint of the s00327 story, not an Original | the master holds the CalMatters-syndicated story as s00327 (8 rows, "approves … rollback"); Marin IJ is a Bay Area News Group copy; no text (login wall) so the origin stage must go by headline (M5) |
| 12 | Santa Cruz Sentinel (blocked), same | fix: Reprint of s00327 | as 11 |
| 13 | Hankyung (plus.hankyung.com), 2024-12-03 | accept | Korean national daily, names 제시 가브리엘 as Budget chair on the $25M litigation fund; Language Korean, Reach International; a real backfill find (M4) |
| 14 | The Telegraph on qa5-web-vercel.telegraph.co.uk, 2024-09-29 | drop | duplicate of 01859 (s00523) on the publisher's staging mirror; link and headline dedupe both missed it (M5) |
| 15 | Los Angeles Magazine, "Did a Tweet Reveal a California Lawmaker Traveled to Maui…", 2023-08-01 | review | not in the master; no page saved; confirm the lawmaker is Jesse Gabriel before adding (wrong-Gabriel class) |
| 16 | National Law Review, AB 418 passes Assembly, 2023-05-15 | accept, label backfill | genuine missing coverage, found by the outlet sweep (M4) |
| 17 | National Law Review, food color additives bill, 2023-04-12 | accept, label backfill | as 16 |
| 18 | KEYT, reprint of s02381 (CNN ultraprocessed law) | accept | page saved; the text rule confirms the CNN Wire copy |
| 19 | The Yeshiva World, reprint of s00044 (AP Nazi-looted art) | accept | page saved; AP credit in the text |

Net: 11 accept (2 of them labelled backfill), 5 fix, 2 review, 2 drop. Of the 15 proposed Originals, 4 are wrong as proposed (KIIS, Marin IJ, Telegraph mirror, Tistory) and 2 need a hand (Sing Tao, Independent date): a 40% error rate on new Originals in one run, almost all from dedupe and date extraction, not from Claude's judgment.

**Prevention: one recommendation and one test per mistake** (specs in requests.md REQ-9 to REQ-15; "stage" = the stage that should catch it; "kind" = rule / reference data / model check)

| Mistake | Stage | Kind | Recommendation | Test |
|---|---|---|---|---|
| M1 Future date (Independent 2028-06-01) | fetch (page date extraction) + verify (sheet) | rule | `pageStamp`'s `byname` rule accepts the preposition "by" before a date; require a real byline shape ("By Name"), skip any candidate after today or before 1990 at every rule; `toRow` never keeps a date after today; sheet_task blanks a future date on a new row and lists it (date_rules check 2 only reviews it today) | REQ-10: the Independent sentence yields no stamp; "By Jane Doe October 28, 2026" still does; a 2028 row lands blank + date_review |
| M2 E-paper page filed as a story (Sing Tao) | query/pre-filter + classify | reference data (`clean_rules.json` skip_urls with kind `print_page`) + model check (prompt line) | flipbook / e-paper / page-viewer URLs are print pages: route them to a `print_pages` review list ("needs clipping", the web twin of the Unlinked print pages tab), never to a story row; the classify prompt names the case | REQ-11: the Sing Tao and an issuu URL route to `print_pages`; a normal singtaousa.com article does not |
| M3 Personal blogs and non-coverage (Tistory; Cool Down and Colion Noir are policy, not bugs) | pre-filter + sheet `drop_skipped` | reference data (`outlet_rules.json` `never_coverage_hosts`, overridable by an outlets.json record) | platform hosts with personal subdomains (tistory, blogspot, wordpress.com, wixsite, tumblr, naver blog, medium.com/@) are never press; real outlets with passing mentions stay and get List-only/Named depth as INCL-v1 says; single-author advocacy blogs stay unless Sammy excludes them (decision) | REQ-12: Tistory dropped, thecooldown.com / mrcolionnoir.com / jewishjournal.com kept; an outlets.json record rescues a journalist's Substack |
| M4 Old items re-found (NatLawReview 2023, Hankyung 2024) | query (the undated outlet sweep) | rule + design D1 | these are real missing coverage, so the sweep worked; label them (`Data Source` "…, outlet backfill", Team note, `review.backfill_finds`) so weekly runs are legible, and move the sweep to the Backfill button (D1) so the weekly run stops paying for it | REQ-13: a 2023 row from an `outlets` item gets the label; a `fresh` find does not |
| M5 Same-chain copies and mirrors as Original + Reprint (Marin IJ / Santa Cruz vs s00327; KIIS / KFI vs s02206; Telegraph staging vs 01859) | dedupe (page) + origin (sheet) | rule (URL canonicalisation; headline index on the segment before " - " / " \| "; headline test for blocked finds) + reference data (`outlet_rules.json` houses: iHeart LA stations = one house) | canonicalise mirror hosts (`qa5-web-vercel.`, `amp.`, `m.`, ampproject) in every link key; index sheet headlines by their first segment too; a blocked find (no text) is matched by headline Jaccard >= 0.8 within 7 days against existing stories before it may become a new Original; one exact-headline search for blocked finds to attach the originator; iHeart LA stations share a house so their copies are editions | REQ-14: normU equality for the staging URL; covHit finds 01859 and s02206 despite dek/suffix; same-house true for KFI/KIIS/Patriot LA; the blocked Marin IJ row becomes a Reprint of s00327 in a fixture |
| M6 The sheet step fired while "disabled" | fire (page) + task configuration | rule (page config block `taskcfg`, approved flag) + an owner action | `fire_trigger` ignores `enabled: false` (list_triggers: enabled false, last_run SUCCEEDED 19:47:23Z, permission_mode auto); the stored prompt is the Oct-27 text that writes `~/Documents/Gabriel press PDFs/AJG Coverage - NewsBank.xlsx` (not the master), green font, old steps; it ran unattended twice and was stopped only by the missing Mac link. Page: fire only when `taskcfg.approved` is true and a trigger id is set (ships false). Sammy: replace the prompt (or a guard stub) now, recreate the task with requires_local_device, TinyFish + Claude Code Remote only (no Exa), a Sonnet-class model, approval mode default until the supervised run | REQ-15: playwright: no `fire_trigger` with `approved:false`; prompt lint: the shipped prompt never names the Documents copy, green font or Exa; `trigger_check.py` against a saved list_triggers dump |

Other things the trace shows: Google News fetch returned 0 items (check the feed URLs through TinyFish; the `when:Nd` operator and locale parameters may be rejected); all 10 `scoped` copies empty (the second fetch pass is wasted when TinyFish is throttled: make it conditional on the first fetch's success and retry once); 86 failures in 722 calls means the 2% rule will rarely let `searched_to` advance under today's TinyFish reliability, so each weekly run re-searches the same window: consider advancing `searched_to` when failures are retried successfully or counting only search failures (B12).

## 7a. Patch review notes (reviewer's reading of the executor's patches)
- REQ-1: exactly the one-line change; accept.
- REQ-2: as specified plus two sensible additions (a stale-heartbeat label after 30 minutes; the sheet warning checked before the "Nothing new" return). The heartbeat uses `set`, so the executor added `RA.hbOff` + `hbFlush()` to stop a late progress write from replacing the provisional doc; that works and is tested. Simpler for a follow-up: heartbeats after the first one could use `doc.update()` (merge) and the guard would be unnecessary. Accept.
- REQ-3: keys the Bills tab on its first four columns (first column not unique), counts hyperlinks from the sheet XML per tab; header strictness means a future header change on a tab must land with the same run. Accept; note the header rule in DECISIONS when applying.
- REQ-6: two-pass fetch with a per-candidate `_fetchfail` flag and an honest reason; 12/12 patched, 8 fail unpatched; the executor's note is right that `tfCall` already retries `retryable` errors once, so this path handles the non-retryable ones (today's `tool_error`s). Accept.
- REQ-4 (informational): openpyxl round trip of the master loses nothing (no CF/DV/images/charts exist; hyperlinks 23/247/88/2 preserved); load 8.9 s, save 5.2 s. A master edited in Excel later would gain features openpyxl drops, so keep the round-trip check in the test suite.
- REQ-8: `rehearse.sh` runs prompt steps 1/3/6 end to end on the real master copy in 86 s, every exit 0, verify ok, `next.aid` consistent; no prompt/flag mismatch. The local half of the sheet task is sound; the risk is the tool half (M6).
- REQ-7: has_work counts only referenced pages docs; test fails unpatched, passes patched. Accept.
- Prevention set REQ-9 to REQ-15: specified in requests.md, not yet built.
- Note: the master working copy moved during this review (bd2d84ea -> 0159ea38, 8 rows added); nothing in this report depends on the old sha except the shared_data snapshot used for the dedupe checks in section 9 (headline presence does not change).

## 8. Evidence
- results/trace/: the live run doc and its 10 page docs (read-only copy).
- list_triggers (read-only) 2026-10-30: trig_01WRLX437wg7VRViGUTKei8R enabled=false, last_run SUCCEEDED 19:47:23Z, permission_mode auto, prompt = the 2026-10-27 text, no local device required, connectors incl. Exa.
- tests_out/baseline_run_all.log: 42 suites green.
- yield.md: query-type yield (Sonnet agent). sources_catalog.csv: 27 sources (Haiku agent). work/out/missing_outlets_2026-10-30.csv.
- requests.md: specs REQ-1..8; results/REQ-*.md as they land; patches/ + APPLY.md.
- Live db reads (read-only, ArtifactData, 2026-10-30 about 19:30Z, mid-run): tracker `runs`, `pages`, `clips`, `tones`, `authors`, `notes`, `views` = 0 docs; `edits` = 5; review queue `items` readable.
- GDELT DOC probe: HTTP 429 "limit requests to one every 5 seconds" on the second call; first call timed out at 25 s.
