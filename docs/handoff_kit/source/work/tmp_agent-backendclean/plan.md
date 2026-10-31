# Back-end cleaning plan: agent-backendclean, Phase 1, 2026-10-28 ~02:20Z

Merged from four read-only audits in this folder:
- code_audit.md (area 1, me)
- workspace_audit.md + moves_container.tsv (agent-bc-workspace)
- docs_audit.md + drafts/ (agent-bc-docs)
- maclib_audit.md + orphans_*.csv (agent-bc-maclib)

Nothing has been moved, edited or published. The Update button's runtime path belongs to agent-buttonopt; items in that path are handed over, not done here.

## Headline numbers
- Disk: 252 GB filesystem, 20.4 GB free (52% used). lib = 7.8 GB, of which work/ 7.0 GB, final_pass/ 507 MB, build/ 220 MB.
- Container moves: 163 moves, 687 MB (no references anywhere, or nested srv/xlsx copies). Same disk, so **0 bytes freed**; a tar.gz of the archive would free most of it (ask Sammy).
- Mac moves: 162 moves, 434 MB (256 MB to _archive, 103 MB to _to_delete, 75 MB relocated raw PDFs).
- Orphans: sheet name with no file **172** (170 are BLOCKED/RETRY placeholders by design; **2 real**: ws09773o, ws09774o, the undated new-outlet pages never committed). Library file with no sheet row **266** (244 press releases + 12 raw jump PDFs by design; **10 real**: old jg-*.html copies). Also 2 placeholder rows still say Saved Copy? = Yes (01549, 02848) and 23 file names are shared by 2+ Coverage cells (sheet-side).
- Code: all 15 anchor-patch steps in apply_all are already no-ops. The code is folded; only the patch scripts remain as dead weight (22 files, 318 KB). The only live apply_all work is 3 block syncs, 2 merges, the pipeline copy and verify.

## Ranked items (what, gain, risk, proof)

### Tier 1, do first, mechanical and byte-equal
| # | Item | Gain | Risk | Proof |
|---|---|---|---|---|
| C9 | Stable homes for what the build depends on: L/tests/ (live suites now in work/tmp_agent-code/suite), code/build.sh (now in tmp_agent-v19finish), code/shell.html (page shell now = tmp_agent-relrule/v18_ex25/pub/index.html), tabs harness blocks out of tmp_agent-tabs | HIGH (build no longer rides on agent scratch) | LOW | build.sh from the new paths gives byte-equal blocks + index.html |
| C1 | apply_all: drop the anchor steps 1..4n (+4o/4p once landed); keep block syncs, merges, pipeline copy, verify, --check, backup. patch_*.py + make_copies_clean.py -> code/_history/patches/ (move). Standing rule reworded: edit sources directly, no new anchor patches | HIGH | LOW | old vs new apply_all on one scratch copy: every target byte-identical; second run no-op; build byte-equal |
| C2 | Split build/js_merged.js at its section markers into code/tracker/NN_*.js; concat writes js_merged.js (same name, so harnesses + pipeline unchanged). The three synced sources (tabs_tracker, reorg_tracker, insights_shell) stop existing twice. buttonopt gets the update sections as its own files | HIGH (readable sources) | LOW | concat == current js_merged.js byte-equal |
| W1 | Container archive: execute moves_container.tsv T1 (83 rows, 141 MB, zero references) + T2 (57 rows, 547 MB, nested srv/xlsx copies) into L/archive/2026-10-28/<original path>; MOVES.tsv = undo log. Re-run the 2-hour activity guard first | MED (clutter) | LOW | listing diff == MOVES.tsv; build + tests still pass |
| M1 | Mac moves (mv only): 14 Backups + old 10-26 export + 3 rename logs + stale index -> _archive (256 MB); _clip_downloads dups/superseded (111 files) + empty _tmp_clean6 -> Gabriel press PDFs/_to_delete (103 MB); 19 unkept raw jump PDFs -> Tracker library/_original_pdf/2026 (75 MB). NOT touched: 05458_p7.pdf (unprocessed clip), batch PDFs, _rename_log_2026-10-27.csv | MED | LOW (needs delete permission in Documents for cross-folder mv, else the source copy stays) | sha list before/after; orphan check re-run = unchanged |

### Tier 2, docs and names
| # | Item | Gain | Risk | Proof |
|---|---|---|---|---|
| D1 | README + CONTRACT consolidated (drafts/README.md, drafts/CONTRACT.md): every rule kept, stale ID formats/inputs/readers corrected, 2 missing shipped docs listed, rule 1 reworded to DECISIONS L27/L24/L165. Note: drafts are LONGER than live (README 3.6->6.6 KB, CONTRACT 17.9->23.2 KB) because rules that lived only in DECISIONS were pulled in | MED | LOW | rule-by-rule checklist in docs_audit |
| D2 | DECISIONS: log unchanged + "Current rules" summary on top (drafts/DECISIONS_current_rules.md, ~1,250 words); 7 superseded entries get a one-word "(superseded by Lnnn)" tag, nothing removed | MED | LOW | diff shows additions only |
| D3 | BOARD: open items only + archive section (drafts/BOARD.md); adds rows for current agents; records sheet-task re-enable state | MED | LOW | every live task id still present |
| D4 | Project copies (claude.ai library/*.md + Handoff Memory): NOT compared, no Projects tool in the sub-agent sessions. Proxy: the v19 pipeline docs/ copies already trail L (README lacks TABS-v1 para, DECISIONS lacks L173-176, CONTRACT lacks TABS-v1). Coordinator or an agent with project_read must diff + sync (T38 agent-docsync has no status file) | MED | LOW | project_read == L after sync |
| C8 | Names: README's build/ = "outputs" is wrong (tabs/, insights/, *_data.py, contracts are sources) -> fix README only, no path moves; README names code/ajg_lib.py which doesn't exist; build/sheet_task_prompt_final.md + build/sheet_task_prompt.md are dead (pipeline ships code/sheet_task_prompt.md) -> archive + drop from TARGETS; build/pub/index.html is the stale v6 page, not the live one -> archive + document where the live page comes from; stale "Press desk"/tab-in/jg- comments | MED | LOW | grep |
| C5 | Python: drop the cleanrules.json write (build_data) + load (assemble), both dead since CLEAN-v2; move one-off tools to code/_history/onetime/ (prep_workbook, extract_nb, make_tone_jobs, save_fetch, migrate_ids, make_id_map, patch_ids, patch_display, apply_fills, author_columns, relpage, fetch2/, fetch_rated1/, billstatus/) | LOW-MED | LOW | blocks byte-equal; py_compile; pipeline-only build |

### Tier 3, intended removals (index.html changes by design)
| # | Item | Gain | Risk | Proof |
|---|---|---|---|---|
| C3 | Dead Insights/Press desk views: remove ins-js release_pickup, bill_timeline, story_travel, reporters (83 KB shipped) + their tests + Press desk sub-nav + tbEmbed. KEEP tone_topic (Data › Tone by issue), all *_data.py and the ins-* data blocks (the tabs read them), the INS registry + old-link redirects | MED (-83 KB page, less JS) | MED | blocks byte-equal; index diff = only removed `<script id="ins-js-*">` + JS ranges; tabs MOD=all + insights MOD=tone_topic + REORG/no-#clips checks; #insights/#press-desk/#pitch links still land |
| C4 | Dead JS: storyLink, renderBills, tbCsvText, tbEmbed; DATATRIM's hidden #anRetired cards still rendered on every redraw (remove cards + their render calls where no other caller); CLEAN-v2 leftovers at viewer/boot sites (cleanLocal); PHONE/period: archive reorg_phone.js, patch_period.py, period_shell.js, fix the comment | MED | LOW-MED | node --check; grep zero refs; harness |
| C10 | Stale tests/harnesses -> archive: build/test_display, test_update, test_links, t5test, copies_test, insights/test_{bill_timeline,reporters,story_travel}, insights/_shell, review, blocks (v1), superseded builds + prompts. KEEP acceptance_check_final.md (cited by DECISIONS), clean/regress* (history), tabs/test, insights/test (tone_topic + harness), test_clean | MED | LOW | trimmed test set passes |
| C6 | Duplicated helpers: disp() x3 identical (build_data, authorsplit, story_travel_data; the 4th in tabs/_common_data is a variant, leave it), norm_url x3 (one is sheet_task = buttonopt), _tab_rows x2 vs reltab.legacy(), read_sheet/run/apply near-dupes in insights_* vs tabs_* -> one code/ajg_common.py pipeline file. Dates/tone are not materially duplicated | LOW-MED | MED | blocks byte-equal; sheet-task suite. Optional, skip under a minimum-risk brief |

### Decisions needed from Sammy / coordinator (found by the audits, not mine to make)
1. **Font colour conflict**: code/sheet_task.py still writes every value GREEN (GREEN='000B8A3E'); DECISIONS L102/L171 say black, red = not in tracker. Fix the code or confirm green for button-written values. [buttonopt file]
2. **Archive rule for lib/**: "never delete; moves to L/archive" exists only in this brief, not in DECISIONS. Record it before W1 runs.
3. **Compress the archive?** Moves free nothing. tar.gz of L/archive/2026-10-28 would recover ~500 MB; deletion is forbidden.
4. **coverage_pre_*.xlsx (19 files, 109 MB) + 61 idle agent folders (2.6 GB)**: every one is named in a status log, so the brief keeps them. If "own status log naming its scratch folder" counts as a record rather than a dependency, they can move too (MOVES.tsv keeps them traceable).
5. **"# of reprints" override scope**: L154 allows recompute only "through clipping"; newoutlets/cleanrows/reviewweb recomputed it too. Widen the rule or note the exceptions.
6. **The 2 undated pages** (ws09773o, ws09774o): give the rows a date, or decide on an undated/ folder, then commit the pages + originals. And set Saved Copy? = No on 01549, 02848 (placeholders).
7. **10 orphan jg-*.html** files: attach to a row (rename) or move to _to_delete; the regroup/rename owner decides.
8. **Mac Backups retention**: proposal keeps the last 5 + "before new-outlet finds" on Desktop, and "before tracker prep" + "before final pass" in Documents; archives 14.
9. **TONE_GUIDE** is stale (bill list path, coauthor rule, hard-coded rating date) and **clean_playbook** "Merged cleaner" describes the removed browser cleaner; clean_html.js is still a pipeline file. Redraft both? (not in any audit's drafting scope)

## Phase 2 split (one implementer per area, no overlapping files)
- **impl-code** (me as integrator, or one agent): C9, C1, C2, C5, C8 code parts, then C3, C4, C10, (C6). Files: code/, build/ code files, apply_all, L/tests, code/build.sh. Coordinates with buttonopt on the js split boundary (update sections ~l.1942-3536, sheet_task.py, sheet_task_prompt.md stay buttonopt's).
- **impl-workspace**: W1 moves into L/archive/2026-10-28 + MOVES.tsv; + C10/C8 build/ archive moves after impl-code says go. Files: work/, build/ non-code, final_pass/, L/archive.
- **impl-docs**: D1-D4 + README fix for C8 + DECISIONS standing-rule wording for C1 + Project copies. Files: L/*.md, build/clean_playbook.md, Project docs.
- **impl-maclib**: M1 moves (mv only) + decisions 6-8 once answered. Files: Mac only.
- **Integrator** (me): proof after impl-code: pipeline-only rebuild byte-equal (blocks) / index.html diff == intended removals only; trimmed test set: tabs MOD=all, insights MOD=tone_topic, sheet-task suite + test_auto, update test [buttonopt], apply_all idempotent (run twice), node --check/py_compile; then docs + Project copies updated.

## Order
1. Wait: v19 published, 4o (relcopies2) and 4p (buttonopt) landed. Re-run apply_all --check (must be a no-op).
2. impl-code C9 -> C1 -> C2 (byte-equal gates), in parallel impl-maclib M1 and impl-docs D1-D3 drafts finalised.
3. impl-workspace W1 (after C9 so nothing live moves).
4. impl-code C5, C8, then C3, C4, C10 (intended removals), integrator proof + tests.
5. impl-docs commits docs + pipeline docs/ + Project copies; one publish by the coordinator's publishing agent (not in this scope).
