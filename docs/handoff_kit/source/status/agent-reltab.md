# agent-reltab — Press releases tab cleanup (Sammy 2026-10-28)
## Log
- start: read README, DECISIONS, CONTRACT, releasecheck/relrule status.
- audit + design: work/tmp_agent-reltab/design.md (written before any change); transform.py -> new_rows.json + value_map.csv.
- code: code/reltab.py (new, pipeline file), code/patch_reltab.py (apply_all 4m: sheet_task RELCHECK-v3 + prompt RELTAB-v1/v1b),
  build/insights/release_pickup_data.py v3.1 and build/tabs/releases_data.py (_tab_rows: either layout), apply_all wiring
  (4m, helper copy, PIPELINE reltab.py). Pre-edit copies in work/tmp_agent-reltab/pre/. apply_all run: pipeline refreshed
  (sheet_task.py, reltab.py, sheet_task_prompt.md); second run: nothing refreshed, targets unchanged.
  NOTE for agent-tab-releases: I edited build/tabs/releases_data.py (only _tab_rows + the loop line); block "r" field 4
  (co-issuers) now holds the cleaned names, legislators first; "c" unchanged.
- tests: block rebuilt from new sheet byte-identical to old (241 rel, 85 picked up, 109 copies, n_tab 244, n_scope 236);
  tab-releases block: c identical, r differs only in field 4 for 84 releases (cleaned names); dry.py 17/17 (new layout append
  with 8 names / 8 bills, overflow, real date, contact split, Tracker release ID 1 = s01453, _rel_mark into own column,
  old layout still appends); release_pickup harness 72/72 against v18_ex25/srv (its embedded block == the new block).
  The lib's own build/insights/test/srv + blocks are stale (14/68 with the old block, 38/68 with the current) - pre-existing,
  not caused by this change.
- sheet write: Mac master verified e0890672...ef8b, no ~$ lock, backup committed to Backups/ (sha verified), new master
  committed with expectedMtimeMs 1793145148105; Mac sha 0846cd57fc5eaf43895033062dbbeef812092a7aec39d7d144d215c5165571ae
  = staged. check.py: other tabs 944,936 cells 0 differences; 3,458 old values mapped, 4,053 target cells verified, 0 failures,
  1 dropped (logged non-person token); 0 unmapped old cells. work/coverage_current.xlsx = new; previous = coverage_pre_reltab.xlsx.
- docs: CONTRACT section "Press releases tab layout (RELTAB-v1)"; DECISIONS entry appended. Mac _docs copy not refreshed (coordinator).
- Questions for Sammy: (1) name canonicalization (93 tokens) and the dropped non-person token - OK? (2) "Assemblymember
  Rodriguez" (2025, D-Ontario, row 2025-...) left as written (probably Michelle Rodriguez, not guessed). (3) Tracker date
  (earliest pickup) / Before text rule are history columns - keep or drop?
