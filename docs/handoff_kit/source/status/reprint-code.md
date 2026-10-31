# reprint-code (2026-10-28) — REPRINT-v2 in code

Task: implement build/REPRINT_PLAN.md (items 1–10, Sammy's 4 answers) in code; back-test; no sheet writes.

## Done
- Working copy work/tmp_reprint_code/ (code/, gen_outlet_table.py, bt_load.py, bt_run.py, regroup_plan.csv, bt_summary.txt, texts_cache.pkl). Copied into L/code after work/PUBLISHED_V21 appeared; apply_all run twice (second run unchanged); backups code/_history/*_pre_reprintv2_2056.*.
- outlet_rules.json v2: types (1,378 keys), houses, services (36), station_calls, blocked_hosts, av_items, house_credits, alias Food Navigator.
- reprint_rule.py: see DECISIONS REPRINT-v2 line / HANDOFF 3.2. reporters.py + reporter_employment.csv. wrong_copies.csv. sheet_task.py + make_copies.py wired. apply_all PIPELINE updated.
- Tests: build/tests/reprint/test_reprint_v2.py 81/81; test_sheet_task 50/50; test_auto 35/35; test_relbutton stops at its own fixture precondition (master tab ≠ 46 old columns) — pre-existing, also with the previous code.
- Back-test (master e97fef6c): swap 51 · swap-date 6 · swap-lateral 5 · merge 198 · edition-merge 30 · edition-fold 184 · feed-duplicate 51 · translation-merge 55 · split 22 · av-split 2 · originator-add 394 (50 no-copy blocked) · verify 33 · kept-contained 36 · kept-second-signal 51 · language-check 3 · release-pair 10.

## Not done / for the regroup agent
- Nothing written to the sheet. regroup_plan.csv is the change list; merges (198 + 30 + 55 translation) go to Sammy before writing (standing request).
- The 96 aggregator-only stories with no reporter / credit evidence ("originator unknown") stay as they are, flagged.
- Copies suite (16/16) and AV clean not rerun (make_copies change is a guard only; run at the next full copies build and read `dropped.wrong_copy` / `wrong_copy_suspect`).

## Questions for Sammy
- 17 saved copies whose page title shares no word with the row headline (make_copies will report them): 06972 FOX40 "Nowruz" page holds a budget story, 03077 Spectrum News 1 — likely wrong files; the rest are print/Korean headline wording. Replace 06972 / 03077?
- Lateral swaps (both rows copies, originator missing): s04312, s04362, s04452, s04488, s04522, s04632, s04635 — apply, or wait for the originator add?
