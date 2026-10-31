# agent-ids (T23)
- 2026-10-27T04:33:11Z started; read README/DECISIONS/CONTRACT/BOARD
- 04:37:18 id_map.csv/aid_map/sid_map built (plain 5-digit per amendment, file_suffix col). 9,544 rows, 217 print ids, last number 09761, 0 collisions, 1,472 blank-status rows (no file suffix), 101+101 dup ids mapped through
- 04:40:58 migrate_ids.py written; test on copy (with injected note refs + 3-row test filemap + --docs): verify ok, 515,376 Coverage cells checked, 9,761 ids paired 1:1, 4,195 stories; negative test (tampered value + font) caught
- 04:42:40 build_data.py updated (both schemes; next={aid,s}; optional SID_MAP adds 101 legacy jg->s idmap entries). Pre vs post build on coverage_current: data 4,195=4,195, rows 9,544=9,544, reprint objs 3,877=3,877, identical after id mapping; idmap 4,060 old codes identical (+101 legacy)
- 04:45:44 JS: code/patch_ids.py (19 anchored edits) applied to build/js_merged.js (backup work/tmp_agent-ids/js_merged.pre_ids.js). Update tests 39/39 (32 old, updated for new formats, + 7 migration checks). Display tests 22/22 on migrated page (18 old + 4 legacy-id checks); also 18/18 with new JS on pre-migration blocks
- 04:50:01 sheet_task.py: both schemes (auto-detect), next 5-digit aid / sNNNNN (floor s04297), legacy id normalisation, library-style page names. t5test/test_ids.py 19/19 (incl. old-scheme db/db2/db3 identical to recorded results). Prompt updated (backup in tmp).
- make_copies.py: works before/after migration (legacy jg-NNNNN tracker texts, old-aid NewsBank texts via "Old Article ID", re-keys legacy manifest entries; --sidmap). Pre vs post run on the real inputs: 181 tracker + 1,215 NewsBank added, 573 skipped, manifest 4,713 = 4,713, all 24 shards identical after id mapping; re-key test 1,396 jg-NNNNN entries -> sNNNNN.
- apply_fills.py NOT touched (fills stay keyed by old ids and must run before migrate_ids; it indexes rows by Article ID, so on a migrated sheet it fails with KeyError rather than writing wrong rows).

# T23 — DONE (2026-10-27)

## Outputs
| File | What |
|---|---|
| work/id_map.csv | 9,544 rows: row, old/new Article ID, old/new Print Article ID, old/new Story ID, status, **file_suffix** (o/r/blank, for agent-librename). New IDs plain 5-digit (amendment). |
| work/aid_map.json | 9,862 old→new (9,544 Article + 217 Print + 101 removed duplicates mapped through to their surviving row) |
| work/sid_map.json | 4,296 old→new (4,195 + 101 removed duplicates, e.g. jg-04196 → s01596) |
| work/id_map_report.json | counts, blank-status list |
| code/make_id_map.py | builds the four files above from a workbook (`python3 -I make_id_map.py COVERAGE.xlsx OUT_DIR --dup work/dup_id_map.json`) |
| code/migrate_ids.py | the migration (see usage in its docstring) |
| code/patch_ids.py | re-runnable JS patch (19 anchored edits); applied to build/js_merged.js |
| code/build_data.py, code/sheet_task.py, code/make_copies.py | updated; each works on the workbook before AND after the migration |
| build/js_merged.js | patched (pre-T23 copy: work/tmp_agent-ids/js_merged.pre_ids.js) |
| build/sheet_task_prompt_final.md | IDs paragraph + page file names (pre-T23 copy in tmp) |
| build/test_update/test.js + body.js, build/test_display/test.js (+ cases_ids.json, srv_ids/), build/t5test/test_ids.py | tests (pre-T23 copies in tmp) |
Not changed: CONTRACT.md, apply_fills.py, assemble.py (no change needed), build/blocks, build/pub (published pipeline copies are stale until the next publish: pipeline/sheet_task.py, build_data.py, tracker.js must be republished with the tracker).

## Numbers
- 9,761 new numbers 00001–09761 (9,544 Article IDs + 217 Print Article IDs; each print ID right after its row's Article ID). Gapless, unique, 1:1.
- Print Article ID that is also another row's Article ID: **0** (no collisions).
- Story IDs: 4,195 jg-NNNNN → sNNNNN, same digits.
- Blank "Original or reprint": **1,472** rows (1,471 NewsBank print pages + ws-03865, AOL 2026-09-14 "Slate of bills to regulate immigration enforcement…", no Story ID) → no o/r in their file names.
- Text references rewritten on the current workbook: Reprint info 3 (B46: jg-01354, jg-03210, jg-01947), Audit plan 1 (B32: jg-01354); Coverage/notes 0 today (fills added before migration are covered by the same regex). File name columns: 0 old-id references left. With --docs, 4 scheme-description cells rewritten (Reprint info A8, B9; Audit plan B15, B29).

## How to run (final single write, LAST step)
1. After all fills/regroup/press-release/author-split writes: `python3 -I code/make_id_map.py <final pre-migration xlsx> work --dup work/dup_id_map.json` (regenerate! migrate_ids refuses a map that doesn't match the workbook row for row, incl. status and Story ID). agent-librename must build its filename map from THIS id_map.csv.
2. `python3 -I code/migrate_ids.py --xlsx <in> --idmap work/id_map.csv --filemap <librename map: old_aid,column,new_filename> --dup work/dup_id_map.json --docs --out <new unique name> --report <report.json>` (~40 s). Exit 2 = verification failed → don't commit.
3. Rebuild: `python3 -I code/build_data.py <migrated> work/index_original.html blocks/ work/sid_map.json` (4th arg adds the 101 legacy idmap entries) → assemble with build/js_merged.js. make_copies.py with `--sidmap work/sid_map.json`.

## Proposed CONTRACT.md change (for the coordinator)
- Inputs: Coverage gains two last columns **"Old Article ID"**, **"Old Print Article ID"** (after Role; covcols.json stays authoritative). Article ID / Print Article ID = plain 5-digit strings, one sequence over both columns, no prefix/suffix. Story ID = **sNNNNN**. Tracker story code unchanged (6-hex legacy codes).
- data block: `id` = Story ID (sNNNNN, 6 chars); `aid`, `reps[].aid` = 5-digit Article ID.
- rows block: `"next": {"aid": <last number + 1>, "s": <max(Story ID number, 4296) + 1>}` (old scheme kept `{ws,pq,jg}`). s04196–s04296 are reserved (numbers of the 101 removed duplicates).
- idmap block: old code → Story ID, **plus** legacy jg-NNNNN → sNNNNN where the number changed (removed duplicates). The page maps every other jg-NNNNN → sNNNNN itself (sidOf), so docs/localStorage/IndexedDB/saved copies keyed by pre-migration Story IDs keep working.
- Proposed rows (Update button): placeholders **"NEW-<run>-<n>"** (Article ID) and **"sNEW-<run>-<n>"** (Story ID). The sheet task assigns the next number in the single sequence and the next sNNNNN, writing `ids: {placeholder: real}`; it still accepts ws-NEW-/jg-NEW- placeholders and old-format ids from runs/docs made before the migration.
- Saved pages from the sheet task: `Saved pages (TinyFish)/ws<Article ID><o|r>-s<Story ID>.html`.
- Viewer copies: articles/*.json + manifest keyed by sNNNNN (legacy jg-NNNNN keys are re-keyed by make_copies; the page also falls back to them).

## For Sammy / coordinator
1. 1,472 blank-status rows get no o/r in file names (1,471 NewsBank print pages + ws-03865 AOL row, which has no status and no Story ID — probably should be a Reprint or Original of an immigration-bills story).
2. No Print Article ID collisions.
3. New Article IDs are text cells with leading zeros ("00034"); Excel may show its "number stored as text" marker. Don't convert them to numbers (leading zeros would be lost).
4. Old ID columns appended as the LAST two Coverage columns (not next to Article ID) to avoid shifting columns; say if Sammy wants them moved.
5. Order dependency: the regroup (T28) may change Story IDs/statuses → regenerate id_map.csv after it (step 1 above). If the regroup creates new Story IDs, it should number them from jg-04297 up (04196–04296 belong to the removed duplicates and map elsewhere in sid_map).
6. Sheet task folder for saved pages is still `Documents/Gabriel press PDFs/Saved pages (TinyFish)/` (only the file name changed); DECISIONS says TinyFish pages go to Desktop/Tracker library/<year>/ — the coordinator may want the task to save there instead.
7. Prose references like "same text as nb-00001" become "same text as 00001" (bare number) — that is the ID now.
8. T30 (author split) and T29 (press release) also touch build_data.py / JS: they should patch on top of the current build/js_merged.js (patch_ids.py anchors are against the pre-T23 file; don't re-run it on an already patched file).

## Self-check
- make_id_map: 9,544 rows; numbers 1..9,761 gapless; 0 collisions; aid_map 9,862 / sid_map 4,296 entries, 0 unresolved dups.
- migrate_ids on a copy of coverage_current (+ injected note refs + 3-row filemap + --docs): verify ok — 515,376 Coverage cells checked (every non-id cell identical, text refs substituted exactly), 9,761 ids paired 1:1, 4,195 stories 1:1 with same digits, Originals == Coverage originals (4,195) and == old Originals apart from ids, other tabs only the expected cells, fonts/fills/number formats unchanged on all other cells, all rewritten cells green 000B8A3E. Negative test (one tampered value + one font) → caught, exit 2.
- build_data pre vs post migration: 4,195 = 4,195 stories, 9,544 = 9,544 rows, 3,877 = 3,877 reprint objects, data and rows blocks identical after id mapping, idmap 4,060 old codes identical (+101 legacy entries), covcols + 2 columns.
- Tests: update 39/39 (the 32 existing, updated for new formats, + 7 migration checks); display 22/22 on the migrated page (18 existing + 4 legacy-id checks) and 18/18 with the new JS on the pre-migration blocks; sheet task test_ids.py 19/19 (old-scheme db/db2/db3 identical to the recorded T5 results + 16 new-scheme checks); `node --check` OK; make_copies pre/post identical after id mapping.
