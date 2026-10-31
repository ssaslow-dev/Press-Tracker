# RULES REVIEW: the reprint-review method applied to other rule sets (Sammy approved, 2026-10-28)
Method per topic: a DESIGNER (reads the current rules and code, measures them on the data, proposes a rubric/rules, back-tests) and a blind AUDITOR (doesn't read the designer's folder; judges a stratified sample from the text itself; error rates and patterns). The coordinator synthesizes: what both agree on is approved, disagreements go to Sammy. All reviewers are READ-ONLY; writes happen later, one rule-7 write per wave.
Base data for every reviewer: work/coverage_current.xlsx = master e97fef6c… (don't wait for newer).

## Waves (ordered to avoid redoing work)
- **Wave 1 (now; independent of the reprint and v21 work):**
  - CONTENT TAGS: tone + Issue/Topic + bill tags in ONE pass, since the same full-text reading serves all three. Reuse the billtags recommendations in work/tmp_queuerec/recs_1b.csv and process_1.md; don't redo them.
  - INCLUSION: whether each row is about this Jesse Gabriel, and whether it's coverage (vs listings, voter guides, calendars, passing name-checks).
- **Wave 1b (after reprint-code finishes its outlet type table):** OUTLET CLASSIFICATION (Medium/Format, Reach, location), built on the new type table.
- **Wave 2 (after the reprint regroup is written):** REPORTER identity + affiliation, which needs the corrected Originals.

## Publishes
- v21 now: release work.
- v22: reprint regroup + wave 1 + 1b writes together.
- v23: wave 2.

Each wave's sheet write happens after the previous publish's data is final, to avoid rebuilding twice.

## Wave 1 decided (2026-10-28) — see DECISIONS. Execution: tags-apply + incl-apply produce DATA PLANS (CSV) + CODE PATCHES (as patch files in their dirs; NOT applied to code/ — sheet_task.py is also being changed by reprint-code). v22 integrator applies reprint-code first, then wave-1 patches, then one sheet write.

## v22 integrator TODO (from v21-post): (1) 06_story_sheet.js factline: skip empty spans / .factline>span:empty{display:none} (thread de9c2baa); (2) make_handoff_kit read publish.json `batches` layout (or emit publishes with shas); regenerate kit after v22 publish; (3) corners: Sammy to confirm on Safari (thread 9eb75f10).

## Wave 3 (Sammy 2026-10-28): (1) COVERAGE RECALL designer+auditor — now; (2) SAVED-COPY INTEGRITY designer+auditor — now; (3) DATES designer+auditor — after (2) lands; (4) TRACKER NUMBERS audit — after v22 publish. All read-only on master e97fef6c (+ v22 data for 4). New finds from (1) go to the next Update run / a find list, not written directly.

## tags-apply DONE (work/tmp_tags_apply/): plan.csv 2,476 cells on 1,290 Originals (hand-check 0/50 errors after fixes); review.csv 335 → review queue cat "tags" (with the outlet items) before v22; patches/ apply after reprint-code (re-anchor queue_after); TONE_GUIDE.new.md replaces TONE_GUIDE at v22. Open: ABX1-1/2 litigation fund (18 rows) Budget-Act or policy bill; date-fix candidates s02400, s04045, s03751 → dates wave.
