2026-10-28T02:01:40Z agent-instructions: Phase 1 started (read-only audit)
2026-10-28T02:01:54Z CORRECTION: target is workbook instruction tabs, not tracker. Dropped tracker search.
- Phase 1 DONE (read-only; no shared files edited, no workbook writes, no publish). Master verified 573e3c85…ffdcc, token none.
  Instruction tabs: "Reprint info" (58x2) and "Audit plan" (36x2); other 6 tabs are data. Nothing in the pipeline reads either tab (no data migration);
  only retired one-offs code/prep_workbook.py + code/migrate_ids.py --docs write them; README:24 points at Reprint info.
  Classes: a 29, b 7, c 11, d 13 (proposals D1-D6). Key finding: sheet_task.norm_outlet misses "X Today's Edition, The" and "X, The: Blogs"
  and has no alias/same-city logic -> D1 OUTLETRULES-v1 (outlet_rules.json + norm_outlet, apply_all 4p). Live contradiction: sheet_task GREEN
  fills + CONTRACT:54 vs DECISIONS 102. Audit: work/tmp_agent-instructions/audit.md. Phase 2 waits for coordinator go-ahead.
