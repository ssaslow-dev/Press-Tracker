# agent-regroup2 (T33 / task C) — status

Started 2026-10-27. Proposals only (no workbook/Mac/artifact/queue writes).
Workbook snapshot: work/tmp_agent-regroup2/snap.xlsx (sha256 e1c70819…07f1 = coverage_current.xlsx at start).
Did not read work/abandoned_regroup/ or agent-regroup scripts.

## Log
- Read README, DECISIONS, BOARD, Reprint info + Audit plan tabs, status/agent-regroup-verify.md.
- Helpers (work/tmp_agent-regroup2/): texts.py (text build + NB clutter flags → texts.pkl, strips_log.csv [552 strips, every one logged], text_map.csv), regroup.py (single run → out/regroup2_changes.csv, out/regroup2_kept_lowconf.csv, run_state.pkl), report.py (summary + queue), selfcheck.py, show.py/story.py (inspection).
- Coordinator note applied: ws-01876, ws-02294, ws-03814 treated as deletions (also in final/deletions.csv). Final run done after this; reruns reproduce the CSVs byte-for-byte.
- Bug fixes during development (before the final run): caption regex, contact-block overreach (nb-02981), title regex that dropped "Editorial Board" bylines (made Canyon Crest Guide the jg-00334 Original — fixed).

## Result (final run)
- 8,040 rows in scope; stories 4,163 → 4,624; 1,681 rows changed (high 1,490 / medium 132 / low 59); 6,359 unchanged.
- Splits 501 rows (356 old stories); followers moving with split-off stories 263; merges 58 rows (43 stories); Originals changed 105; reprint-list → "Reprint (unverified)" 649.
- No text: 1,514 rows (649 unverified reprint-list, 419 reprint by headline+author, 285 single-row Originals, 146 split for failed/missing headline+author, 15 Originals of multi-row stories).
- Queue: 209 low-confidence items (59 changes + 149 kept-only-with-set-aside + jg-00334 Original question) in out/regroup2_queue_items.json (178 items, 196 KB) + out/regroup2_queue_items-2.json (31 items, 43 KB). Shape {"list":[{id,cat:"regroup",title,detail,proposed,options,conf,key}]}. NOT published.
- Self-check: difflib matching blocks on 40 random changes, pass/fail agreement 40/40 (selfcheck.csv).

## Questions for Sammy / coordinator
1. Setting aside unmatched leading/trailing lines of saved web copies (dek, photo credit, byline/date, tag lists) goes beyond the listed NewsBank patterns; every such case is low confidence and queued, never decided automatically. OK?
2. jg-00334: the order rule ties Excelsior vs the Register; current Excelsior kept; queued.
3. Medium-confidence Original changes (person byline vs none, "mostly reprints" outlets, web over print) are not queued; listed in regroup2_changes.csv.

## v2 run (coordinator fixes after agent-regroup2-verify) — 2026-10-27
- Scripts: texts_v2.py (+ CalMatters web chrome patterns, <figcaption> flagged), regroup_v2.py, report_v2.py, selfcheck_v2.py. v1 files kept in tmp_agent-regroup2/v1/.
- Outputs: out/regroup2_v2_changes.csv, out/regroup2_v2_kept_lowconf.csv, out/regroup2_v2_new_items.json (134 new items, regroup2-0210…0343, rows not in the v1 queue), out/regroup2_v2_diff.md, out/regroup2_v2_vs_v1.csv. Existing queue docs untouched.
- Changes: 1,623 rows changed (high 1,420 / medium 115 / low 88), 4,563 stories. All 7 strict-pass splits reverted; jg-00908 long AP rows now with nb-02320 (jg-00896); nb-01765 stays jg-00730; pq-00115 stays own story (forced not-same; my measure 87.6/95.3 vs verifier 31.6/36.7 — different texts read); Fresno Bee nb-03194 and PR Newswire nb-01008 stay Originals; ws-00665 queued.
- Self-check v2 (difflib, 40 random): 39/40 agree; ws-00858 vs nb-02320 92.2 (k-gram) vs 85.4 (difflib, repeated/reordered text) — already low and queued.
- Reruns reproduce v2 outputs byte-for-byte.
- 30 v1 queue rows now have a different proposal (list in regroup2_v2_diff.md) — agent-decide-regroup should use v2.
