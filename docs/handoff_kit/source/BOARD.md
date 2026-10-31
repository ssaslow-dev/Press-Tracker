# Task board — tracker rebuild (updated 2026-10-30)

New tracker: https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv ("AJG Press Coverage Tracker"). Old "(Copy)" untouched: https://claude.ai/artifact/UCat3jW8cViL37pHTTt6JA
Sheet task (scheduled, fired by the tracker): trig_01WRLX437wg7VRViGUTKei8R, runs on Sammy's Mac, auto approval.

| # | Task | Owner | Status |
|---|---|---|---|
| T1 | Workbook prep (Role col, Topic/Bills/Reach filled, 101 old stories added) | coordinator | DONE — committed to Mac, sha256 verified; backup in Backups/ |
| T2 | build_data.py (sheet → data/rows/idmap/covcols) | coordinator | DONE |
| T3 | Display JS (reprints by Story ID, Story ID keys, Confirmed removed) | agent-display | DONE — 18/18 browser checks |
| T4 | Update button JS (Coverage-format rows, dedupe vs all rows, TSV) | agent-update | DONE — 32/32 checks |
| T5 | Sheet task script + prompt | agent-sheettask | DONE — tests incl. temp-ID and link cases |
| T6 | Merge, assemble, publish new tracker | coordinator | DONE — v6 published |
| T7 | Independent acceptance check | agent-verify | ONCE, last — slim spec: build/acceptance_check_final.md |
| T8 | Create scheduled task, wire into tracker | coordinator | DONE |
| T9 | Ask Sammy about the reprint regroup (Audit plan LIGHT/FULL/Part 2+3) | coordinator | after T7 |

Open items for Sammy: 19 Role conflicts (work/prep_report.json); Topic 'Unassigned' on 1,056 NewsBank-only stories; Reach blank on 862; outlet names display "The X"; 820 old tracker stories now appear inside another story's reprint list; green font for new fills (confirm).

## Phase 2 — new additions brought up to the old stories' standard (Sammy, 2026-10-27)
Order: texts first → tone / translations / authors in parallel → one sheet write → viewer copies + rebuild → recheck.
| # | Task | Owner | Status |
|---|---|---|---|
| T10 | Extract NewsBank article texts from the 329 batch PDFs, map to Article IDs | agent-nbtext | RUNNING (resumed) |
| T11 | Find saved copies for ~453 tracker/ProQuest originals without one | agent-trackercopies | 11 found in tracker (other codes); Mac search BLOCKED; 7 borderline listed |
| T12 | Rate tone for the 1,302 untoned originals (TONE_GUIDE.md), split across agents | agent-tone-1..4 | waits on T10/T11 |
| T13 | Translations for 75 non-English stories without an English headline / 82 without English text; author fills from NewsBank headers | agent-translate | waits on T10 |
| T14 | One workbook write (blanks only, green), then saved copies into the viewer (articles/*.json + manifest by Story ID) and republish | coordinator | waits on T12/T13 |
Sheet task stays PAUSED until T14 + acceptance pass.
| T13b | English headlines (53 ready, 10 flagged) | agent-headlines | DONE |
| T15 | Reach proposals for 241 outlets (862 stories) — for Sammy approval, not written | agent-reach | DONE, awaiting approval |
| T16 | make_copies.py: texts → viewer copies keyed by Story ID | coordinator | DONE (tested: 11 tracker + 1 NewsBank sample) |
| T17 | Fetch publisher pages for 192 untoned no-copy tracker stories (TinyFish) + one-pass tone/topic/bills/author | agent-fetch-1, agent-fetch-2 | RUNNING (Sammy approved) |
| T18 | Rename Desktop/Tracker library HTMLs to Article IDs | agent-rename | DONE: 3,294 of 3,317 renamed; 23 ambiguous (work/rename_ambiguous.csv); 8 identical pairs (work/library_duplicates.csv) for Sammy |
| T10b | NewsBank texts, relaunched with all fields captured in one pass | agent-nbtext2 | RUNNING |
| T19 | make_tone_jobs.py (batches for parallel tone agents) + apply_fills.py (one blanks-only write of all results, Originals mirrored, verified) | coordinator | DONE; dry run on copy: 64 headlines + 13 translations, 0 existing changed |
| T10 (done) | NewsBank texts: 1,750/1,751 NB originals have text; 21 originals don't mention Gabriel (texts/nb_no_gabriel.csv); 31 vetted bylines; 14 language mismatches | agent-nbtext2 | DONE |
| T11 (done) | Missing tracker copies: 38 found (11 tracker, 26 Desktop, 1 zip); 415 none anywhere | agent-trackercopies | DONE |
| T20 | One-read tone pass | agent-tone-1..10 | DONE: 1,148/1,148 (784 Neutral, 248 Positive, 35 Negative, 15 Very positive, 4 Very negative; 21 flagged) |
| FIX | v1 prep made 101 duplicate originals (multi-code cells) — redone from backup, committed, 98 Desktop files re-renamed | coordinator | DONE |
| T21 | Review queue page for Sammy (324 items; answers saved in its db 'decisions' collection) https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB | coordinator | PUBLISHED, awaiting Sammy |
| T22 | Gabriel bill list from leginfo (443 measures) + bills tab decided (63 add, 1 not) | agent-leginfo | DONE; Bills backfill pending (use leginfo list) |
## Phase 3 — IDs, file names, authors (Sammy, 2026-10-27)
| # | Task | Owner | Status |
|---|---|---|---|
| T23 | ID map (old→new Article/Print/Story IDs) + migrate_ids.py + tracker codebase update (build_data, JS, sheet task, tests, CONTRACT proposal) | agent-ids | RUNNING |
| T24 | Author completeness: saved copies first, then TinyFish → out/author_fills.csv | agent-authors | RUNNING |
| T25 | Split NewsBank batch PDFs per article → work/nb_split/<old aid>.pdf | agent-nbsplit | RUNNING |
| T26 | Inventory tracker-saved sources not in Desktop library (ProQuest text, pdf/, articles/) → work/library_new/ | agent-libinventory | RUNNING |
| T27 | Rename whole Desktop library to new names + add T25/T26 files + filename map | agent-librename | ON HOLD (Sammy) — with the ID migration |
| T28 | Reprint regroup (90% rule, Audit plan) → proposed changes for Sammy | agent-regroup | RUNNING |
T27 (library rename) now also waits on T28 + Sammy's approval.
| T25 | NewsBank split | agent-nbsplit | DONE: 5,574 files in work/nb_split (+541 print_pages, default: add to library); index nb_split_index.csv |
| T26 | Library gap inventory | agent-libinventory | DONE: 6 PDFs (fmt ws) + 37 image-embedded HTML replacements in work/library_new; old copies move to `_replaced/` (add-only rule); jg-d83455 → nb-01307 (rename_map entry points to a removed dup row) |
| T29 | Press-release classifier (relaunch; first attempt left no output) | agent-pressrelease | RUNNING |
| T30 | Split bylines → Author 1..N + Author title; editorial boards → "<Outlet> Editorial Board" | agent-authorsplit | RUNNING (tracker JS patch applied after T23) |
| T23 | ID map + migrate_ids.py + codebase | agent-ids | DONE (tests: update 39/39, display 22/22 + 18/18, sheet task 19/19). Final step: rerun make_id_map.py on the final pre-migration workbook; librename uses that map; T30 JS patch goes on current js_merged.js (don't rerun patch_ids.py); sheet task saved pages → Desktop/Tracker library/<year>/ (per DECISIONS); republish pipeline copies. CONTRACT change proposed in status/agent-ids.md |
| T29 | Press-release classifier | agent-pressrelease | DONE: 497 yes (348 Original, 149 Reprint), 71 borderline → queue 13-pressrelease, 335 stories release-only (drop from tracker). Build changes in work/out/press_release_build.md (apply_fills verify must allow the new column). Release Originals → handled in T28 regroup |
| T24 | Authors | agent-authors | TinyFish PAUSED by Sammy; writing results so far; remainder in out/author_tinyfish_remaining.json |
| T28 | Reprint regroup | agent-regroup | ABANDONED by Sammy — outputs in work/abandoned_regroup/ (do not use) |
| T14a | Interim write of settled results to sheet + tracker rebuild/republish | agent-write1 | RUNNING |
| T31 | Regroup Part 3 check | agent-regroup-verify | moot (regroup abandoned); review page v9 labels kept |
| T32 | Clean saved HTMLs (10 buckets) | agent-clean-1..10 | DONE — all 3,497 processed; html_clean/ complete; playbook updated |
| T33 | Regroup by long text streaks (≥25-word runs cover ≥90% of both) on cleaned texts → proposals | agent-regroup2 | waits on T32 |
| T30 | Author 1..8 + Author title split; per-author tracker links | agent-authorsplit | DONE (tested on copies). Apply AFTER agent-write1 publishes: build/author_columns_patch.md; 49 queue items in out/author_split_review.json (unpublished) |
| T30b | Board names now follow the Original row → RERUN run_split.py after the T33 regroup is applied (Originals may change), before the final write | final-write agent | note |
| T34 | FINAL PASS (one write + one publish), spec in DECISIONS "final pass is queued" | agent-final | QUEUED — starts when T32 cleaning, T33 regroup (Sammy-approved), links patch are done |
| T35 | Links patch (CSL + publisher only, ProQuest style) | agent-links | DONE, approved (CSL_DERIVE on); applied in the final pass (composes with T30) |
| T36 | Delete error copies + RETRY – TinyFish placeholders (final pass, after T32) | agent-final | QUEUED |
| T37 | Merge bucket cleaners → code/clean_html.py + rules JSON; wire into sheet task + Update button | agent-cleaner-merge | QUEUED after T32, goes into the final pass |
| T38 | Sync Project docs library/{README,DECISIONS,CONTRACT,BOARD}.md from lib/ | agent-docsync | RUNNING |
| T39 | Sweep for outside-article-only Gabriel | — | CANCELLED (Sammy); deletion uses rows already flagged by buckets |
| T40 | Search index + viewer copies from cleaned text (make_copies source switch + test) | agent-searchfix | QUEUED after bucket 2 (into final pass) |

## Execution order (set 2026-10-27 08:50Z — avoid redundancy)
A. Finish bucket 2 cleaning (resume agent-clean-2). Everything below reads all 10 buckets.
B (parallel, after A):
  B1 agent-consolidate — one pass over all html_checks/meta_fills/clean logs → final lists: sheet fills; Language + Gabriel-mention corrections; error copies (→ RETRY – TinyFish + _to_delete); deletions (California Files 13 rows + comment/teaser/tag-only rows the buckets flagged); "not Jesse Gabriel" rows (e.g. Vistazo Gabriel Ugarte) for Sammy; one combined list for Sammy. Read-only; no writes.
  B2 agent-code — ONE code agent for all remaining code changes, on copies, composed with patch_links.py + author patches: merged cleaner (T37) wired into sheet task + Update button; skips (californiafiles.org; Gabriel only outside article); viewer copies + search index from cleaned text (T40); sheet-task prompt fixes (story count excludes press releases; mark new wire finds as releases; saved pages → Desktop library). All suites + new tests.
C. agent-regroup2 (after B1): string-of-text regroup on cleaned texts, EXCLUDING B1's deletion and error-copy rows → proposals → Sammy approval. (T33)
D. FINAL PASS (after C approved + B2): one write [fills → corrections → deletions → error-copy placeholders → approved regroup → author split rerun → make_id_map + ID migration] → library [to _to_delete; rename incl. _original_html; add nb splits + library_new] → File name columns → rebuild with all patches → ONE publish → slim acceptance check → sheet task supervised run, then re-enable.
Cancelled/superseded: T39 sweep, copycheck, old regroup.
| B1 | Consolidate bucket findings | agent-consolidate | DONE — work/final/ (fills 1,517, corrections 164, error copies 57 files, deletions 29, regroup_exclude 84, sammy_list.md) |
| B2 | All remaining code changes | agent-code | DONE — code/apply_all_patches.py + build/final_build.md; all suites pass; cleaner 99.26% = buckets |
| C | Streak regroup (proposals) | agent-regroup2 | RUNNING |
| T41 | TinyFish retry of 57 bad copies + declutter → staged replacements | agent-retry | RUNNING |
| C2 | Independent check of regroup2 (100-row sample) | agent-regroup2-verify | RUNNING |
| C3 | Write 209 regroup2 items to review queue (Sammy approved) | agent-queuewrite | RUNNING |
| D1-4 | Auto-decide review queue (4 agents by tab) | agent-decide-{reach,pr,authors,regroup} | RUNNING |
| C4 | regroup2 v2: apply the independent check's fixes; new queue items only | agent-regroup2 | RUNNING (approval still pending Sammy) |
| T41 | TinyFish retry | agent-retry | DONE: 29 replaced (staged work/retry/clean), 7 BLOCKED, 18 RETRY (10 wrong page, 7 ToI no Gabriel, 1 incomplete); results work/final/retry_results.csv |
| C4 | regroup2 v2 | agent-regroup2 | DONE: 1,623 rows change (1,420 high/115 med/88 low); 4,563 stories; 134 new queue items → being written as 14-regroup-3 by agent-decide-regroup. Final pass uses regroup2_v2_changes.csv |
| T42 | BLOCKED marks (206) + 156 fetched-but-unflagged copies → final write | final pass | READY: work/final/blocked_marks.csv |
| T43 | Fetch 466 reprint-list links (2 agents) → clean → library | agent-reprintfetch-1/2 | RUNNING |
| T44 | Regroup delta for newly fetched reprint rows | — | waits on T43 + regroup-final |
| C5 | Regroup approved by Sammy (incl. 19 recommendations) | — | APPROVED — final pass applies regroup_final.csv + T44 delta |
| T45 | Fold the reprint-fetch agents' find-mode fixes (Healthline headline, KQED dump, Tags/Related tails, prev/next teasers, appended comments) into code/clean_html.py + rules; rerun cleaner tests | agent-code (resume) | after T43 half 1 |
| T43 | Fetch reprint links | agent-reprintfetch-1/2 | DONE: 419 saved (incl. 9 pre-existing), 31 BLOCKED, 16 RETRY; results work/final/reprint_fetch_results_{1,2}.csv |
| T44 | Regroup delta + bake in 19 approvals + byline fills | agent-regroup-final | RUNNING |
| T45 | Cleaner find-mode fixes | agent-code | RUNNING |
| T45 | Cleaner find-mode fixes | agent-code | DONE (library 99.26%, reprint-fetch 92.1% with all diffs explained; all suites pass) |
| F1 | Final pass stage 1: final workbook on a copy + library plan | agent-final-F1 | RUNNING |
| F1b | Carry-over + rating jobs for new stories, then re-apply + re-migrate | agent-final-F1 | RUNNING |
| F1r | Rate 622 Originals lacking Tone/Topic (4 agents) | agent-rate-1..4 | RUNNING |
| F1 | Final pass stage 1 | agent-final-F1 | DONE — final.xlsx sha ce2da658…; 9,503 rows, 4,500 stories; library plan replays cleanly |
| F2 | Library operations on the Mac | agent-final-F2 | RUNNING |
| F4a | Tracker build + all suites on final.xlsx (no publish) | agent-final-F4 | RUNNING (parallel with F2) |
| F4a | Tracker build + suites + fixes | agent-final-F4 | DONE — publish tree ready (2 publishes); final.xlsx now a6f54716… |
| F3 | Commit final workbook | — | waits for Mac + F2 |
| F2 | Library operations | agent-final-F2 | DONE — 10,931 ops, listing == plan |
| F3 | Commit final workbook | agent-final-F3 | DONE — Mac sha a6f54716…; backup in Backups/ |
| F4b | Rebuild with automations + publish | — | waits on agent-code |
| AUTO | 7 automations + leginfo bill list/check, browser cleaner removed | agent-code | DONE (all suites pass) |
| F4b | Rebuild + publish | agent-final-F4 | RUNNING |
| F4b | Rebuild + publish | agent-final-F4 | DONE — tracker v8 (1793119028-42ac), 4,130 stories, all suites pass; ~5 MB size headroom left |
| F5 | Acceptance check (live) | agent-acceptance | RUNNING |
| F5 | Acceptance check | agent-acceptance | DONE — pass except AB 130 filter option + 4 retired Reach labels (fixing) |
| F7 | Fixes + prune in one publish | agent-final-F4 (+ prune plan) | waits on pubwrite + prune phase 1 |
| F6 | Publisher fills + Lee override + AB 130 + flatten colors + red rows | agent-pubwrite | DONE — Mac sha bfc0bab9…; 2,563 red rows |
| F7 | Combined publish: rebuild from bfc0bab9 + acceptance fixes + prune + Manage patch | agent-final-F4 | waits on agent-manage |
| F7 | Combined republish (spec build/final_pass_F7.md) | agent-final-F4 | waits on Pasadena dates write |
| F9 | Pasadena Now dates + 9 reprints + bylines | agent-paswrite | DONE — Mac sha 1bc70516…; 4,491 stories |
| F7 | Combined republish | agent-final-F4 | RUNNING |
| F10 | Rename the 9 Pasadena/Altadena library files (+ backups) to their new r/s names and update File name cells | — | QUEUED after F7 publish |
| INS | Six insight features | agent-insights (UI) + agent-billstatus (data) | RUNNING |
| TOK | Token cuts + docs + master move | agent-code | DONE — tracker v11 (1793123501-bc1f); master = Desktop/Tracker library (sha 069ae154…); scheduled task still disabled with OLD prompt (needs new short prompt + Exa removed) |
| BILLS | Bill milestones (273 bills, 1,895 milestones) | agent-billstatus | DONE — work/out/bill_milestones.{json,csv}; 'Bills' sheet tab write queued after the Chrome sheet write |
| INS | Insights tab (5 views) | agent-insights + 5 feature agents | DONE — tracker v12 (1793128073-069f); Bills sheet tab still to write |
| PR-UPD | Update button: look for new press releases (a46 + Jewish Caucus: chair tenure or names him) and append to the Press releases tab | queued | after Story travel v14 publish + Press releases tab write |
| PHASE-B note | Integrator (agent-tabs) must also: ship release full texts as a separate published file (data/release_texts.json or index form, from code/release_texts.json, merged never shrunk) loaded lazily by the Releases tab; the Update button / sheet task appends each new release's text and the rebuild regenerates + publishes that file; prove a pipeline-only rebuild produces it byte-equal. (Sammy 2026-10-27) | queued |
| NEXT-REGROUP | On the next full regroup/rerun: re-match existing stories with the 90-day text window and merge stories split by the old ±7-day window (known: AP Nazi-looted art s00044/s04300/s04685/s04686); show merge list to Sammy before changing Story IDs | queued (Sammy 2026-10-27) |
| FOLLOW-UPS | After v19: (1) language check on agent-newoutlets' 185 rows (all labelled English; some Spanish pages); (2) suspicious saved copies 08480 (42 words), 08984 (40), 09203 (34,512) — check/replace copies; (3) agent-relcopies sheet write + next build (release copies, pr codes); (4) "Uses release text" tag design; (5) next full regroup with 90-day text window | queued |
| POST-V19 ORDER | 1) DONE relcopies3 (master 1fae6a32) → 2) DONE instructions2 (4q OUTLETRULES, tabs removed, master 30543809) → [then] relcopies3: wire 4o, sheet write (pr codes), docs → 2) instructions Phase 2 FIRST (D1–D6 additions incl. OUTLETRULES into sheet_task/docs; tab archive + removal write) → 3) backendclean code fold/split/homes (patch steps retired; stable sources) → 4) buttonopt Phase 2 LAST, on the folded sources (so nothing is re-layered on top of the optimized code) → 5) workspace/Mac moves → 6) build + publish v20 | in progress |
| V20 SEQUENCE (current) | in parallel now: agent-calmatters (sheet write, origin fixes) + agent-backendclean2 (fold/split/homes/moves) + agent-photos (diagnosis) → then ONE v20 code agent on the folded sources: AVDATE fixes+AV sheet write, map parity, entity header redesign, tone labels, photos fix, calmatters root fix → then agent-buttonopt Phase 2 LAST → build + publish v20 | in progress |
- 2026-10-28 backendclean2 DONE (fold/split/homes/moves; proof byte-equal; 4 stale releases.test.js expectations + test_auto "same story twice" → fix in v20). v20 code pass launched: v20-maps, v20-tabsui, v20-photos, v20-origin-av, v20-docs (ownership in build/V20_BRIEF.md). Pending specs: avshow, previewclean (AV only), relrelated → integrate after. buttonopt Phase 2 LAST.
- 2026-10-28: v20 LIVE (versions 1793170519-1fa0 step 1, 1793170541-a64f page; index f3ee5393…, master 4d7fb37c…). Tests 869/869 harness, REORG 62/62, copies 16/16, sheet_task 50/50, auto 35/35. Artifact storage ~250/256MB. Next: v21 queue in build/phaseB_inbox.md; scheduled task still DISABLED pending Sammy's approval of work/tmp_agent-buttonopt2/scheduled_prompt.md.
- 2026-10-28 v20 BUILD DONE (agent-v20-final, 06:45Z): v20 code pass (maps, tabsui, photos, origin-av, docs) + BUTTONOPT-v1 (Update button Phase 2) + NOSHOWCHAN-v1 folded; apply_all + --check OK; LIB index f3ee5393… = pipeline index (shell.html), 15/15 blocks equal; master 4d7fb37c…. NOT yet published (live = v19 1793153876-e0f4); draft publish.json predates the channel edits → regenerate from build/pub/pipeline before publishing. Docs (README, CONTRACT, DECISIONS, BOARD, TONE_GUIDE, clean_playbook) copied to Mac Tracker library/_docs, old copies mv-archived to _archive/_docs_pre_v20_2026-10-28 (agent-v20-projdocs).
- 2026-10-28 RP-FINAL (rp-final) BUILD DONE, STAGED: RELPLAN handoffs + coordinator corrections + RUNCONFIRM / PICKALL / CORNER-v4 / TIMEAXIS / HIDEUNVERIFIED. Page 736d1e12…e61a (LIB = PIPELINE). Tests: harness 887/0, REORG 62/62, copies 16/16, sheet_task 50/50, auto 35/35, relbutton 44/44, relmatch 50, relthread 26, relcopy 26+8, AV 80/75/0, confirm 56/56. Sheet staged 99dc03d9… (outputs copy for SendUserFile), NOT committed; publish plan work/tmp_rp-final/publish.json; NEXT (main): commit sheet (rule 7) → write work/RPFINAL_COMMITTED → publish → handoff kit → df-write.
- 2026-10-28 df-write DONE: master e97fef6c… (date fills, 15 verified reprints, 118 → Removed, unconfirmed hidden). rp-final rebuilding on it; then independent pre-publish review; then publish. Reprint rebuild: audit + origins recs done, scheme pending.
- 2026-10-28: v21 LIVE (version 1793220623-9df2, page 884d7efc…, master e97fef6c…). Independent pre-publish review: PUBLISH (0 wrong release links in 186 checked).
- 2026-10-28: v22 execution order fixed in build/V22_ORDER.md (code order, single write with ordered steps: removals → copy repairs → regroup → new rows → outlets → tags remapped to post-swap Originals → mentions/depth → print tab → derived). Update button not to be pressed until v22.
- 2026-10-28 coordinator: copies answers logged (COPIES-v1); dates designer+auditor running; libsync agent started.
- 2026-10-28 dates-designer done (tmp_dates_design: 146 date changes, UTC shift main class, 8 needs-Sammy). Waiting on blind auditor before synthesis.
- 2026-10-28 dates synthesis: DATES-v1 decided; dates-apply + copies-apply agents started.
- 2026-10-28 Sammy: start v22. v22-int started on section B (code); C waits for dates-apply + copies-apply.
- 2026-10-28 copies-apply done (164-cell plan, 40 new copies, 202 OCR sidecars, copy_check patch → v22-int); Sammy decided E/F/no-Gabriel.
- 2026-10-28 Sammy: max parallel. Started nocopy-links, origin-fetch, recall-rows (C4 row prep) and c-dryrun (rehearse section C on a copy). Running: v22-int (B), dates-apply.
- 2026-10-28 Sammy: queue-decider (Fable) deciding all queue items that aren't genuinely unclear; c-dryrun told decisions will change.
- 2026-10-28 nocopy-links done (32 adds); recall-rows done (24 rows, IDs 10301–10324/s04901+); OWNED-v1 decided.
- 2026-10-28 origin-fetch done (61 rows; 52 duplicate existing rows → merges); c-dryrun done (apply_c.py validated). Started dup-merges + nocopy2. Bug: openpyxl delete_rows leaves hyperlinks → v22-int.
- 2026-10-28 Sammy approved 3 checks: link-audit (past misplaced hyperlinks), print-check (1,443 unmatched print rows), blind spot-check of queue-decider (starts when its decisions land).
- 2026-10-28 Sammy: scheduled tab reviews (Reporters, Outlets, Press releases, Bills, Story travel) right after v22, alongside tracker-numbers audit → v23.
- 2026-10-28 nocopy2 done: 22 rows (10601–10622), 15 merges → dup-merges.
- 2026-10-28 print-check done: move safe (0/129 wrong); PRINTTAB-v1. Subagent's findings.md write was refused; content kept in DECISIONS/BOARD.
- 2026-10-28 Sammy: Home + Data added to tracker-numbers audit; Clips one-agent check — all after v22.
- 2026-10-28 Sammy: final backend code review (designer + blind auditor) after v23 → final publish + handoff kit.
- 2026-10-28 dates-apply done (246 Date, 170 Edition, Date source all rows; patches → v22-int B5); dates-p5 (Sonnet) fetching last 383 rows.
- 2026-10-28 queue-decider done: 866/868 decided (by claude-agent), 40/40 self-check; 4 open (own YouTube = OWNED-v1 out; tags-301 District/community approved by Sammy's tag answer; uvreprint-001 + CNN cluster stay open). Blind spot-check (70) started; v22 C waits for it.
- 2026-10-28 TOKENS-v1: AGENT_BRIEF.md written; shared-data (Sonnet) building code/shared_data.py.
- 2026-10-28 link-audit: 0 misplaced hyperlinks on master + all 16 backups; execute_removals never ran on the master (bug is real but caused no damage). Fix still goes in v22.
- 2026-10-28 dup-merges done: 140 merges decided (supersede some queue items; precedence in V22_ORDER). Inputs now waiting only on: v22-int (B), queue spot-check, dates-p5, shared-data.
- 2026-10-28 queue-decider dates addendum: 36/37 date reviews + 6 early stories decided; agreed with the US Fed News swap rejection.
- 2026-10-28 queue-spotcheck: 0/70 confirmed errors (95% CI 0–5%), 90% agreement; apply in v22 except verify (hold).
- 2026-10-28 v22-int B done (all suites pass; button parity on all today's rules). GO for C prep/rehearsal; commit waits for Mac bridge + dates-p5.
- 2026-10-28 dates-p5 done (30 more Date fixes, 17/17 hand-checked). Mac bridge back. v22-int: validate → rule-7 write → build → suites; publish waits for independent review.
- 2026-10-28 Sammy: no duplicative final checks; v22 publishes after suites + smoke; numbers/Clips/independent review moved to the end.
- 2026-10-29 Sammy: FORMAT-v1 added to v23.
- 2026-10-29 Sammy: kit + library refresh only at the end.
- 2026-10-29 Sammy: podcast/radio search additions deferred; reminder scheduled (~3h) to raise when v23 scope is set.
- 2026-10-29 efficient order written (V22_ORDER bottom): v23 reviews start after v22 write+build; one question batch now; final checks merged into one verification agent.
- 2026-10-29 v22 write 1 committed (698927c0); SF Chronicle reversal + all 14 outlet answers → small 2nd write in v22, then publish.
- 2026-10-29 v22 LIVE: version 1793236038-04e6; master 49baead0 (after writes 698927c0 → 49baead0). Update button usable again. v23 leftovers: 4 Daily News/LA Daily News same-paper stories, 16 Politico rows National/Trade, 3 Q12 rows off Coverage.
- 2026-10-29 v23 wave started (Sammy: start v23; usage 74%).
- 2026-10-29 v23-travel done (2 fixes + 1 tweak patched; 63 stories with early pickups; 330 pickup outlets lack location → outlets agent; 10 Originals 3+ days after a pickup → leftovers). NOTE build/pub is stale; current page work/tmp_v22-int/srv22 — agents told.
- 2026-10-29 v23-bills done: 4 fixes (ghost bill tags from old index, HR regex, resolutions 'Adopted', 04564 → AB 1548), tweaks (12 reprint bill mismatches, 3 budget_act flags, HR titles, s03877); NEEDS APPROVAL: 64 Budget Act bills clutter (facet/default-hide) + stalled rule.
- 2026-10-29 ~01:00Z: Sammy's 5-hour limit hit; 8 v23 agents stopped mid-work (state saved). Resume scheduled 02:05Z via SendMessage (not new agents). Done so far: travel, bills.
- 2026-10-29 v23-rules done (paywall patch + 12 tests; wireblend detector + 13 tests; 8 blends in backfill).
- 2026-10-29 v23-rep-audit done: byline 3.5% wrong (credit-as-author 84 rows), 7 unmerged pairs, employer display wrong on 20% of sampled entries (AFFIL-v1 gaps, ignores reporter_employment.csv), counts 0 errors. Awaiting designer for synthesis.
- v23-outlets done; outlet-loc (Haiku) running.
- 2026-10-29 v23-rel-audit done: precision 83% (96% belongs in some tier), recall ~87%; P1 standing quotes in 2 releases (116 wrong links); P2 later wave window; P4 13 stories with month-precision dates from OLD_INDEX; sheet Related counts differ for 36/244. Awaiting rel-design.
- outlet-loc done: 48 high applied in v23; 67 medium/low left blank.
- v23-rel-design done; press-release synthesis written (build/V23_SYNTH.md).
- v23-leftovers done (137 cells + 30 regroup rows; 3 open). Waiting: rep-design, type.
- rep-design done; reporters synthesis written; rep-lookup (Haiku) running.
- 2026-10-29 all v23 reviews in; Sammy answered 8 questions; v23-int starting.
- 2026-10-29 chain-cands (Sonnet) building candidate list; Haiku lookups next.
- 2026-10-29 chain-lookup done: 152 bylines, 64 high/27 medium/61 low (work/tmp_chainorig/lookup/employers.csv). Follow-up write after v23 publishes: high-confidence employers only (+ medium where consistent with sheet tenures).
- CHAINORIG scoped to button fix + 10 high stories (follow-up after v23).
- 2026-10-29 v23 LIVE 1793253083-a884, master 9384bd66. chainorig-fix (v23.1) started. For the final code review: tab-test fixtures don't exclude List-only stories (fixture drift), test_relbutton fixture failure, HR bill titles, 2 Q12 authors, 05356 print file link, 3 open leftovers.
- 2026-10-29 v24 LIVE 1793254317-dd29 (chain originators: 4 merges into existing USA TODAY/KFF/AP stories + LAT 10629), master fc1cd788. Final stage starting.
- 2026-10-29 final-lookups done: 20 Assembly HR titles (leginfo) + 2 Q12 names → final write. Waiting on code-design + code-audit.
- 2026-10-29 code-audit done: 4 HIGH bugs (Removed tab not in ID scan → ID reuse; Removed not in dedupe → removed stories re-added by Update; duplicate placeholders if Add clicked twice; swap-then-held leaves no Original), 2 MED tested+patched, M7/M8 run-doc/concurrency, L9–L12. Sammy told to hold Update until the final publish.
- 2026-10-29 code-design done; FINAL_SYNTH written; final integrator starting.
- 2026-10-29 FINAL LIVE 1793258418-fc0a (final-int), master 4e63f34c. Code review fixes in; suites 29/29; TABS 860/893 on refreshed fixtures (33 pinned to v18). HELD: s04630 removal (lawyer = Assemblymember pre-office) → Sammy. Next: handoff kit + library archive.
- 2026-10-29 FINAL live 1793258418-fc0a, master 4e63f34c. Next: final verification (Fable) + tab-test debt (Sonnet) in parallel; then kit + library + docs.
- 2026-10-29 tabtests done: TABS harness 903/903 on final fixtures, run_all 29/29 green; no real page bugs. Remaining: final-verify (stopped: out of credits, resume), handoff kit, library refresh, docs sync.
- 2026-10-29 final-verify progress noted in work/tmp_final_verify/PROGRESS.md (only the live==build check done; rerun fresh after the aggregator write).
- 2026-10-29 Sammy: PAUSED the final verification and the handoff kit; remind him periodically (scheduled daily reminder; also mention when other work finishes). Library refresh + docs sync continue.
- 2026-10-29 Sammy: also PAUSED library Work archive refresh + Project docs sync (local DECISIONS/BOARD still updated); all four in the daily reminder.
- 2026-10-29 agg-orig v2 ready (61 items, 95.1% clean); waiting for the Quoted publish, then go.
- 2026-10-29 v25 Quoted + RELBADGE live 1793296460-a31d, master 8f923a97 (verified on Mac 6.8MB). Incident: a commit reused the master's file name and overwrote it with a stale file; restored from backup by the agent. Rule: staged commit names must be unique. agg-orig given go (button patches + write + publish).
- 2026-10-29 agg-orig live 1793299218-727c, master 78f04abe (aggregator originals fixed, CNN rows fixed, button rules). Sharing review refused (non-allowed media: svg/vtt data URIs) → share-clean agent (Sonnet) fixing at source.
- 2026-10-29 share-clean live 1793300168-5dbc (MEDIAGATE-v1: no svg/vtt/odd media; test in run_all). Sammy to retry sharing.
- 2026-10-29 SHOWNET-v1 live 1793301567-f39f, master cb5395d4. TODO next write: KFI AM 640 Reach → California regional & local (Q13 proposal said so; the record's 'Trade, advocacy & blogs' contradicts it).
- 2026-10-29 OPEDS-v1: audit done (10 OK, 9 FIX, 15 not op-eds, 1 new reprint); write pending (Mac bridge offline) — rehearsed out.xlsx in work/tmp_opeds/w/. Sammy: keep published byline order on co-authored op-eds.
- 2026-10-29 MEDIAGATE-v2 live 1793309223-c3a5 (copies static-only; 56 svg→png, 11 posters kept). Sammy to retry sharing. Pending: op-ed write (Mac offline) + its covRole code publish.
- 2026-10-29 OPEDS-v1 write committed by coordinator: cb5395d4 → ef4e7a58 (backup 'BACKUP before opeds write 2026-10-29'; verified on Mac). Build/publish pending (oped-check agent).
- 2026-10-29 SHARE PROBE: test A published (page only, no files, no capabilities) https://claude.ai/artifact/5hfnMn72f3GonX5TKn3HiY. Next: B = + data/ + articles/; C = + img/ + pdf/; D = + capabilities.
- 2026-10-29 SHARE PROBE: A (10.5MB page) 'too large or complex'; B (1.8MB, data blocks removed) SHARED OK → cause = page size. C = data loaded from data/*.json via sync XHR bootstrap, full 3,687 stories, no copies/photos/connectors: https://claude.ai/artifact/CcdPhHKPp4gMqw24fy4rsp — awaiting Sammy's share test.
- 2026-10-30 STATUS: live tracker 1793351414-4ff2 (FINALCHECK-v1), master 75eb6b32, shareable viewer 6vhKKcNX… 1793351438-e9a0. Since 10-29: OPEDS-v1, MEDIAGATE-v2, SPREADTAG-v1, VIEWER-v1, DEPTHQ-v1, LOOSEENDS-v1/REACHFIX-v1, RELDOTS-v1, TVLINKS-v1, FNOUN-v1, FINALCHECK-v1. HANDOFF.md, CONTRACT.md, README.md updated; kit regenerated; Work archive refresh see HANDOFF changelog. Open for Sammy: HANDOFF 8.1 D11.
- 2026-10-30 library Work archive refresh done: Work archive/2026-10-30 (46,093 files, all sha OK).
- 2026-10-30 STATUS (kit regen): live tracker 1793387365-be18 (REVIEW4, WEBLOOKUPS-v1, LEARN-v1, DATABASIS-v1, img repack; 153 files, 203.1 MB), viewer 6vhKKcNX… 1793387420-969c, master bd2d84ea…9ab04e. Open for Sammy: wire-blend pickups A5; 09721, 01734, 06948, 06949; 8 medium date fixes (work/out/web_dates_2026-10-30.csv); 04889; Korea Daily Times home city; 19 blank reaches; stray empty file Tracker library/.probe_w. Sheet task still DISABLED pending prompt approval + one supervised run; TinyFish needs re-authorizing. Handoff kit regenerated.
