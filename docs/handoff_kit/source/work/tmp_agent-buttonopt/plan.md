# Update button: ranked fix and optimization plan (agent-buttonopt, Phase 1, 2026-10-28)

Merged from map.md (B), dry_report.md (C), js_map.md (A, agent-buttonopt-js) and yield.md (D, agent-buttonopt-yield).

Owners for Phase 2:
- **JS** = implementer on code/patch_buttonopt_js.py → build/js_merged.js.
- **ST** = implementer on code/patch_buttonopt_st.py → code/sheet_task.py, code/sheet_task_prompt.md, helpers.
- **INT** = me: apply_all step 4p, tests, rebuild proof, docs.

All ST items rebase on agent-relcopies2's step 4o (it edits sheet_task.py, the prompt, make_copies and build_data). "est." means estimated.

## A. Bugs (fix first)

| # | Bug (evidence) | Fix | Owner | Risk |
|---|---|---|---|---|
| S1 | **The "nothing queued" stop never fires.** `has_work` counts removal requests and conflicted edits (never cleared), pages of skipped finds (no result list names them, so step 5 never deletes them), and runs whose rows were all skipped (`ids: {}` is falsy, so they are re-applied forever). Dry run: check-only still says "work" after write-back. **Live db: 2 removal requests (s01821, s01822) have been queued since 10-27**, so every Save to sheet / Refresh runs the full routine. | (1) The result gets `pages_drop` (pages of skipped / duplicate finds); the prompt deletes them. (2) apply_runs / has_work treat a run as done when `sheet.at` is set (not only `ids`). (3) Edits that only conflict or request removal get `reported: <at>` written back; has_work ignores edits whose `at` ≤ reported. (4) **Sammy: should removal requests now move rows to the "Removed" tab (DECISIONS 169 precedent), or stay report-only?** | ST (+JS: removeStory toast wording) | low |
| S2 | **Reprint rows carry Original-only cells.** A find turned into a Reprint by reprint_check keeps Tone, Tone note, Tone rated by, Topic (and Bills) from proposeRows (dry case 2: 10093). This breaks DECISIONS 110(3) and 167 (Tone/Topic/Bills on Originals only). | reprint_check pops those keys when it converts a find. JS: don't ask Claude for tone on items folded into reprints (A-B13). | ST, JS | low |
| S3 | **Spurious "Tone rated by" conflict on every rated find, every run.** The row carries the tone ("Claude, from article excerpt") and saveFound also writes a tones doc ("Claude, from tracker"). | JS: no tones/authors/translations docs for finds whose proposed row already carries them. ST: apply_tones skips rows this run added. | JS, ST | low |
| A-B1 | **Two reprint rules.** The page decides reprints of existing stories with the old Oct-21 rule (same headline, or 80% of 8-word shingles of the *shorter* text, no date window). The sheet task re-tests only Original finds, so those Reprint rows are never checked against DECISIONS 72/93/158 (dry case 13: 10096 added unchecked). The Update panel also tells Sammy "80%". | The page only collects reprint candidates and saves their page text (pages doc keyed by the placeholder). sheet_task.reprint_check also tests proposed Reprint rows by RR.text_verdict / headline_author (90 / 7 days). Failures become their own story, or are listed when there is no text. Then delete isReprint/hlShare/tfShingles/tfOverlap/TF_SAME_TEXT and fix the panel text. Saves verifyReprints' fetches of the story side (the task has --copies). | JS + ST | medium (changes which rows become reprints; the dry fixture covers both directions) |
| S4 | **Copies window too narrow for REPRINT90.** The prompt stages articles/<year>.json for find dates ±7 days; reprint candidates reach ±90 days. A January find misses last December's originals' text and wrongly becomes a new story. | `sheet_task.py --copies-needed` prints the shard list (finds ±90 days; releases −1…+30 days); the prompt stages exactly that list. | ST | low |
| A-B4 | **Search window loses stories.** searched_to advances even when 300 of 780 searches failed. There is no overlap for indexing lag. | since = searched_to − 7 days (known-URL filters make the overlap nearly free); advance only when ≤2% of searches failed. | JS | low |
| A-B2/B3 | A reprint whose story text can't be read becomes a new unreviewed story; exact-headline matches under 25 chars are dropped silently. | Covered by A-B1 (the task decides; no-text → review list). | JS | low |
| S5 | Release matching runs twice on new rows (apply_releases tests rows > first_new_row, then apply_release_finds re-tests them against the just-appended releases). Untestable entries are duplicated (dry: 10091 ×3). | apply_release_finds skips releases appended this run; dedupe releases_untestable by (aid, url). | ST | low |
| S6 | New-release "Contact" regex is case-sensitive ("CONTACT:" missed). | re.I | ST | none |
| S7 | A find whose only same-text Original is an OCR'd print page is never tested with the OCR-tolerant rule / near-miss link (side test: 82/78% plain, 86% tolerant). | **Sammy: should DECISIONS 153 (made for the clipping run) also apply to Update finds?** If yes: compare() uses RR.decide_ocr when the candidate's copy is OCR text. | ST | low |
| A-B6/D | outletGroups doesn't filter infoweb.newsbank.com: 241 outlets collapse onto it, and 9 real hosts are never site-searched (ocregister.com, pasadenastarnews.com, dailybreeze.com, pressdemocrat.com, sandiegouniontribune.com, …). | Add `newsbank` to the link filter. | JS | low (about +1 call, coverage gain) |
| A-B8/B9/B12 | Retry skips the rate gate. The panel builds the plan 3× per draw with a wrong since. The new-outlet trigger is too loose ("D-", "budget"). | Small fixes. | JS | low |
| (A-B5) | "Budget bills missing from leginfo" | **Rejected:** DECISIONS 98 reverses 97; budget trailer bills are not his. | none | none |

## B. Savings (ranked by tokens, then calls)

| # | Waste | Fix | Saving per run (est.) | Owner | Risk |
|---|---|---|---|---|---|
| T1 | The sheet task reads the db with ArtifactData `list` **into context** and re-types db.json. Each saved page passes through twice (clean + scoped). | Read with `out_dir` (files, not context); `sheet_task.py --db-dir DIR` assembles them; the prompt never opens them. | **about 18k tokens per saved page** (15 pages ≈ 270k) | ST | low |
| T2 | "Before any judgment call, read DECISIONS/README/CONTRACT/TONE_GUIDE/playbook" (121k chars) in a task that makes no judgment calls (rule 5). | Read DECISIONS only when a step fails in a way the prompt doesn't cover. Docs keep shipping (DECISIONS 111). | **about 30k tokens** | ST (prompt) | low; needs Sammy's OK since DECISIONS 111 asked for the read line |
| T5 | S1 makes a "nothing new" Save to sheet / Update run the whole routine. | Fix S1. | a whole sheet-task run (about 40–150k tokens + rebuild + republish) on every no-op press | ST | low |
| T3 | About 45 single `Artifact read` calls for pipeline files; small text files come back inline. | One `read` with `paths` (all files, one approval) into pipeline/; the prompt says not to open them. | about 44 calls; up to about 100k tokens if inline | ST (prompt) | low |
| T4 | Step 6 hand-edits articles/<year>.json + manifest for each saved page, and reads the published ≈10 MB index.html as the assemble base. | (a) `copies_add.py` (or sheet_task --articles-out) merges result.pages into the staged shards + manifest. (b) Ship `pipeline/shell.html` (published page with data blocks stripped); assemble from it. That also makes the pipeline-only rebuild self-contained. | about 4k output tokens per page + a 10 MB read per run | ST + INT (coordinate with 4o, which touches make_copies) | medium (shell must reproduce the page byte-equal; covered by the rebuild proof) |
| T6 | Classify prompt repeats a 10.7k-char bill list per 10-item batch (15.6k fixed header). | Tag bills locally (session-aware regex + date rule, like hasHisBill); drop the reach list (reach is overwritten by consensus); batch 20. | about 40–50% of classify tokens (≈27k → ≈14k per run) | JS | low–medium (spot-check bill tags on a week of finds) |
| T7 | Search plan: 780 base calls. D-Encino-40 (3 of 357 sweep finds came from it alone), issue words ×120 (no yield evidence; the deep plain search covers those hosts), 56 dormant/duplicate native-site searches, backfill 11 → 1 per new host, paging on short pages (`>=5` → `>=10`), the unused originCredit search for plain local finds. | D + A-F1/F2/F8 | **780 → about 520 searches (−33%), about 9 min less gate time**; −10 per new outlet; a year-crossing run 1,340 → about 1,100 | JS | low (issue words: unmeasured, see D) |
| T7b | 163 outlet hosts silent for more than 24 months are searched every run. | **Sammy's call:** monthly cadence per host (needs a per-host last-searched field) | −163 more (to about 360) | JS | real: up to about 29 stories a year if dropped outright |
| T8 | Each saved page is fetched 3× (open, pagePhotos, savePages scoped), and pagePhotos' output is lost. Wire copies are fetched twice. verifyReprints fetches same-headline reprints it never compares. | Delete pagePhotos. Store ONE page copy (scoped when it names Gabriel, else clean, capped about 150k) instead of two 400k fields. Reuse wireByText's page. Skip `_samehl` fetches + cache story text (most of this goes with A-B1). | about 5–10 fetch calls; halves page docs (also halves T1's remainder) | JS | medium for the single copy (test the cleaner on about 10 pages) |
| T9 | Release check: after apply_releases, apply_release_finds re-tests the same rows (S5); --release-candidates loads the workbook a second time (14 s). | S5. Optionally fold the candidate list into --check-only output. | CPU only, about 15 s | ST | low |
| T10 | Step-5 db write-back uses single writes. | ArtifactData `batch` (≤50 per call) | about 5–15 calls → 1–2 | ST (prompt) | none |
| T11 | Prompt text that repeats CONTRACT (release tab's 43 column list, AV tab detail, RELCHECK history labels). | Replace with "sheet_task.py fills it (reltab.py / avtab.py)". | about 2.5k chars of prompt | ST | none |

## C. Dead code and redundant layers (remove cleanly; no behaviour change)

- **JS (about 7 KB):** recredit() (no caller); CLEAN_RULES / tfClean / cleanLocal pass-throughs (inline tfStrip at 7 call sites); old reprint rule (after A-B1); pagePhotos; the duplicated originCredit comment; the stale tfpages.py / "Saved pages (TinyFish)" / Exa comments; searchPlan() folded into one cached plan.
- **Not now:** the Insights / Press-desk shell is about 15 KB. TABS-v1 still wraps it, so remove it only in a patch_tabs refactor.
- **sheet_task.py:**
  - the RELCHECK-v1 16-column "Press releases" path in apply_releases / _rel_mark (the master is RELTAB). Keep or drop per 4o's RELTAB-v2.
  - the 3-pass sheet_line string-replace build becomes one builder.
  - stale docstrings (reprint_check says ±7 days; REPRINT90 is ±90).
  - `run.av` input stays (contract) but is documented as hand-only.
- **assemble.py:** 'cleanrules' block handling (CLEAN-v2 removed it).
- **Layer order:** many patch steps rewrite the same functions (patch_clean → auto → f7 → tokens → releases → relrule → reltab → avtab). Step 4p edits the *result*, with markers, and must run last (after 4o).

## D. Expected totals (typical weekly run, 15 saved pages)

| | Now (est.) | After A–C (est.) |
|---|---|---|
| TinyFish searches | about 880 | about 560 |
| TinyFish fetches | about 25 | about 15 |
| Gate time | about 33 min | about 21 min |
| Claude in page | about 27k tokens | about 14k |
| Sheet task | about 330–450k tokens | about 30–60k |
| No-op Save to sheet | full run + republish (S1) | about 5k, stops at --check-only |

## E. Questions for Sammy (blocking only their own item)

1. **S1(4):** should removal requests execute (move rows to the Removed tab) or stay report-only (then cleared after one report)?
2. **S7:** should the OCR-tolerant / near-miss rule (DECISIONS 153) apply to Update finds?
3. **T2:** may the sheet task stop reading the docs every run (they still ship and are refreshed)?
4. **T7b:** should dormant outlets (no story in 24 months) be searched monthly instead of every run?
5. **T7 issue words:** drop all 120, or keep only politico.com + sacbee.com (12)?
