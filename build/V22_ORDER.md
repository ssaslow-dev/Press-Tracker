# v22 execution order (coordinator, 2026-10-28). The integrator MUST follow it.
Base master: e97fef6c… (no writes since). Live: v21 1793220623-9df2. Scheduled task stays DISABLED; Sammy shouldn't press Update until v22 is live (new rules aren't in the live pipeline yet).

## A. Inputs that must be final before the build starts
1. Queue decisions: only DECIDED items get applied; undecided ones carry over to v23.
2. Saved-copy review (designer + auditor) synthesized, so its repair list and save-time gates are known.
3. Dates review: optional for v22. If it isn't done, it goes to v23. Its read-only review starts after (2).

## B. Code, applied in this order (each on top of the last; re-anchor patches as needed)
1. REPRINT-v2: already in code/.
2. Tags patches: work/tmp_tags_apply/patches (re-anchor queue_after) + TONE_GUIDE.new.md.
3. Inclusion patches: work/tmp_incl_apply/patches 01–05.
4. Outlet record: code/outlets.json + outlet_record() in sheet_task (work/tmp_outlet_design).
5. Saved-copy gates: identity, date, completeness and cleanliness, plus the new cleaner rules for the template clutter.
6. Search/recall: YouTube station search, Google News feeds, OR-grouped after_date passes, name variants, late-pickup window, sister editions, AP/health-wire long tail; NewsBank refresh step and reminder (Sammy logs in).
7. UI: the depth chip + list-only filter/toggle; the factline empty-span fix (de9c2baa); make_handoff_kit reads the `batches` layout.
8. apply_all; unit suites per module.

## C. Sheet data: ONE rule-7 write, steps in this order inside the same working copy
1. Inclusion removals (71 + 3 stubs): do first, so nothing below touches rows that are leaving.
2. Saved-copy repairs (wrong/partial copies replaced or relinked; 06972, 03077, 08080, 07051 …). Copies come before anything that reads text.
3. Reprint regroup: decided merges/editions/translations/swaps/splits/verify/addorig. Apply linked groups together. Skip any whose partner items are undecided or Skipped.
4. New rows: originator fetch-adds + missing finds (recall CSVs, LA Daily News 2026-10-26). Run the REPRINT-v2 rules, inclusion rules and outlet record on them.
5. Outlet record: blank fills + the Sammy-backed corrections + decided outlet items.
6. Tags plan: REMAP by Story ID onto the post-swap Original (swaps change which row is the Original), then apply; decided tag items too.
7. Mentions recount + Mention depth: recompute AFTER the copy repairs and new rows (don't reuse the stale plan values for changed rows).
8. Move the unmatched print-page rows to their own tab (and update the readers).
9. Derived values last: "# of reprints", the Originals mirror, the Press releases related/copies columns (relmatch --update after the regroup), AV tab rows for new AV items.

## D. Build, check, publish
make_copies (image flags) → build.sh → FULL suites → independent pre-publish review → publish v22 → threads → regenerate handoff kit → docs/Project sync.

## E. After v22
- Reporter identity + affiliation review (needs the corrected Originals).
- Tracker-numbers audit.
- Remaining undecided queue items → v23.

## Added 2026-10-28 (DATES-v1, COPIES-v1)
- B5 also: date_check/normalize patches from work/tmp_dates_apply/patches (local-zone conversion, Date source, 8 sanity checks).
- C2b (after copy repairs, before regroup): date plan work/tmp_dates_apply/plan.csv (Date, Year, Date source). Early-reprint fixes that are SWAPS go into C3 with the regroup, not here.
- C2 copies: re-fetch the 19 other-edition copies; 17 teasers → Saved copy blocked, Publisher link kept; Sing Tao headlines filled; OCR text sidecars for the 202 print PDFs (library, add-only).
- C4: the 50 no-copy originators need a Publisher link lookup (search only; blocked page never opened) before they're written; text fields from their reprints.
- C1 also: the 17 rows in work/tmp_copies_apply/inclusion_handoff.csv → Removed.
- C2 = work/tmp_copies_apply/plan.csv (164 cells) + tags.csv (79) + story-level copy for the 58 F rows; C3 also merges the AP "The Latest" rows (route E) into one story.
- B5 also: route G (extract_nb kicker fix + regenerate texts/nb json for affected rows) and J (header uses publish date).

## E (Sammy 2026-10-28): TAB REVIEWS right after v22 publishes, designer + blind auditor each, read-only on the v22 master, all in parallel with the tracker-numbers audit (share its findings; don't double-check the same counts):
1. Reporters tab: identity (one person, one record; name variants), affiliation by date (employer history; freelancers), counts.
2. Outlets tab: what it shows/counts on top of the v22 outlet record (Reach, type, location rollups).
3. Press releases tab: blind audit of story↔release matching accuracy (RELRELATED-v3 tiers, pre-release window, reprint pickups), plus counts.
4. Bills tab: grouping/display of bill tags (sessions, coauthor vs author, title-only mentions), counts.
5. Story travel tab: how a story's spread is traced (reprint groups, dates, outlet locations), edge cases (editions, translations, AV).
Coordinator synthesizes; agreed fixes + Sammy's answers → v23 with the reporter affiliation work.
6. (Sammy 2026-10-28) Tracker-numbers audit explicitly covers the HOME page (headline counts, charts) and the DATA page (table + downloads match the master row for row).
7. (Sammy 2026-10-28) CLIPS tab: one-agent functional check after v22 — search/filters/sort return the right stories; each clip opens the right copy and labels (re-fetched copies, story-level copies, BLOCKED, merged stories); broken links. Re-check only when copy logic changes.

## F. FINAL (Sammy 2026-10-28), after v23 once rules + data are final: BACKEND CODE REVIEW
Designer (maps intended behavior from DECISIONS/CONTRACT against the code + tests; drift between the Update-button pipeline and the offline/integration scripts e.g. apply_c.py) + blind auditor (reads the code cold; bug hunt: rarely-run paths, openpyxl edits, IDs/links, dates, concurrency, error handling). Also dead/duplicate code, test gaps, and handoff readiness (can a newcomer run, rebuild and fix from the docs alone). Fixes conservative: correctness bugs + missing tests; restructure only where it clearly prevents errors. Full suites → one final publish → regenerate handoff kit → docs/Project sync → library Work archive refresh.
- C2 also: AV 03960 and 05177 Show page links are google.com search URLs → replace with the real show page (or blank + note); 09441 AirTalk copy is a different episode → re-fetch/RETRY.
- C3 also: work/tmp_dup_merges/merges.csv (decision=merge only, 140). Precedence where it overlaps queue decisions: dup-merges wins (it read both) — rv2addorig-004/005/038/040 become merges (no new LAT/Bee/NYT rows), rv2swap-057/060/061 and origin-147/119/123/161 are superseded; Originals per its order-v2 notes (s01903→07053, s01004/s01115→03572/03974, s01413→04678, s03108→08482). The queue's open "ofetch CNN 2023-03-23" is resolved by s01068 (CNN wire text). s03852 (10613) stays held.
- C2 also: attach the fuller fetched AP writethrus 10531/10522/10523 as the copies for 08727/01549/01715 (new files, add-only). Language fixes: 09597 Telemundo → Spanish; 02855 El Mundo, 00049 CE Noticias English — set from the copy text.
- C2b also: date flags from dup-merges (s03649/09121, s00695 print date, s00704, s00016) checked under DATES-v1 with the review items.
- C2b also: date review decisions in work/tmp_queue_decide/decisions.csv cat "dates" (19 writes incl. s04626 AP → 2018-04-03; s00806 KFF date from kffhealthnews.org); 09313 stays open.
- C3: apply all queue-decider categories EXCEPT 'verify' (2 items, 08959/03183: hold — Sammy's earlier decision set them unverified). Origins' missing credited-copy merges (AP 02353/01714-16/05342) → v23.

## CHECK POLICY (Sammy 2026-10-28): no duplicative final checks while changes are pending.
- v22 and v23: automated suites + smoke check only; no independent pre-publish deep review.
- Moved to the very END (after v23, with the code review): independent pre-publish review, tracker-numbers audit incl. Home + Data, Clips check.
- After v22 only the reviews that PRODUCE v23 changes run: the five tab reviews (Reporters, Outlets, Press releases, Bills, Story travel) + reporter affiliation. They must not re-verify v22's counts.
- v23 also: FORMAT-v1 (DECISIONS) — Format column, backfill, button, rollups; designed inside the Outlets tab review.
- Housekeeping (Sammy): handoff kit regeneration + library Work archive refresh happen once at the END, not per publish; per publish only a HANDOFF changelog line + DECISIONS.
- v23 also: PAYWALL-v1 (direct paywalled finds → no-copy rows; check current behavior first). Second search engine: dropped.
- v23 review staffing (BUDGET-v1): single agent — Outlets (+FORMAT-v1), Bills, Story travel; designer+auditor — Reporters, Press releases matching.
- v23 tab reviews: TABKEEP-v1 applies — maintain/tweak only; anything bigger goes to Sammy for approval first. Put this in every reviewer's brief.
- v23 also: WIREBLEND-v1 (blended staff-and-wire stories: note + wire pickup count; button + backfill).

## EFFICIENT ORDER FROM HERE (coordinator 2026-10-29, Sammy asked for time/token-efficient sequencing)
1. NOW (no conflict with v22-int, which owns code/ + the master): ask Sammy's remaining questions in ONE batch (outlet §5, recall §5, bill-only) so v23 never waits on answers.
2. v22: write → build → suites → publish (+ the 3 UI comment changes). No kit/library/deep review.
3. START v23 REVIEWS RIGHT AFTER THE v22 MASTER WRITE + BUILD (not after publish): they read the new master (shared_data --rebuild) and the locally built page. All in parallel: Reporters (designer+auditor, Fable), Press-release matching (designer+auditor, Fable), Outlets+FORMAT-v1 (1 agent), Bills (1), Story travel (1). Each gets AGENT_BRIEF.md + TABKEEP-v1 + "don't re-verify v22 counts".
   In the same wave, read-only design (Sonnet): PAYWALL-v1 (check current behavior → patch), WIREBLEND-v1 (detector + backfill plan), FORMAT-v1 backfill plan, v22 leftovers (26 partial merge groups, 6 edition merges, AP credited merges, open items) → plans + patches only.
4. One synthesis by the coordinator; one question batch to Sammy (only what TABKEEP says needs approval).
5. v23 integrator (one agent): apply all patches in one pass; ONE rule-7 write with every data plan (review fixes + Format + wireblend + leftovers); build; suites; publish.
6. END (once): code review (designer + blind auditor) → conservative fixes; ONE final-verification agent covering independent pre-publish review + numbers audit (Home, Data, every tab) + Clips check; final publish; handoff kit; library Work archive refresh; docs/Project sync.
Rules: MODELS-v1 — Haiku for fetch/save loops and rote steps, Sonnet for light-judgment mechanical work, Fable only for judgment; every agent loads shared data; every row-building agent dedupes against the master first; no checks that a later stage repeats.
- v23 also: TYPE-v1 font consistency pass (1 Sonnet agent, starts after the v22 build with the other v23 reviews; applied by the v23 integrator).

## FINAL STAGE (after v24 1793254317-dd29, master fc1cd788)
Inputs for the final write (one rule-7 write with the code-review fixes): s04630 → Removed (the "Jesse Gabriel" is a lawyer, INCL-v1); HR bill titles + 2 Q12 newsletter authors (final-lookups, Haiku); 05356 print file link (09930 File name 2 taken → use the next free file column or story-level note); the 3 open leftovers stay open unless the evidence lands. Code review designer + blind auditor (Fable) → conservative fixes incl. tab-test fixtures excluding List-only stories and test_relbutton's fixture. Then ONE final-verification agent (independent pre-publish review + numbers audit incl. Home/Data + Clips check) → final publish → handoff kit → library Work archive refresh → docs/Project sync.
