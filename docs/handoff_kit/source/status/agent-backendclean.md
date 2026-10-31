# agent-backendclean — generalized back-end cleaning (structure + housekeeping; not the Update button runtime = agent-buttonopt)

## 2026-10-28 PHASE 1 (read-only audit + plan)
- started; read README, DECISIONS (all), CONTRACT, BOARD, apply_all_patches.py
- status/agent-buttonopt.md did not exist at start; will re-check before Phase 2
- plan: work/tmp_agent-backendclean/plan.md
- 02:0xZ coordinator asked for a split; no Agent tool -> proposed 4-area split; main launched agent-bc-workspace / -docs / -maclib; I keep area 1 (code) + merge
- 02:10Z code audit -> work/tmp_agent-backendclean/code_audit.md (C1-C10). Facts: all 15 anchor steps are no-ops (marker skips); only real
  syncs are tabs_tracker.js+us_map.js / reorg_tracker.js / insights_shell.js blocks + bills/release_texts merges + pipeline copy.
- COORDINATION with agent-buttonopt (I do not edit its files): ownership boundary proposed = js_merged.js lines ~1942-3536 (update:
  outlets on record, update: TinyFish..., the two header buttons, Update log) + sheet_task.py + sheet_task_prompt.md are buttonopt's.
  Handed over for buttonopt to decide: recredit() unused (js l.2381); tfClean pass-through calls in Update (CLEAN-v2 leftovers);
  Exa history comment l.2268; norm_url triple copy (sheet_task copy); sheet_task mints 'jg-%05d' at l.310 before norm_id; old-scheme
  docstrings. Proposal C2 (split js_merged.js into code/tracker/NN_*.js, concatenated byte-equal) would give buttonopt its own files.
- Constraint for area 2: build + live tests depend on work/tmp_agent-code/suite, tmp_agent-tabs (harness hblocks), tmp_agent-relrule/v18_ex25
  (BASE page), tmp_agent-v19finish (build.sh), tmp_agent-relcopies2 -> must stay in place until C9 gives them a stable home.
- 02:15Z SendMessage to agent-bc-workspace / agent-buttonopt not reachable -> notes in work/tmp_agent-backendclean/notes_for_agents.md
- 02:2xZ sibling audits landed (workspace_audit.md + moves_container.tsv, docs_audit.md + drafts/, maclib_audit.md + orphans_*.csv);
  merged into work/tmp_agent-backendclean/plan.md (tiers, risks, proofs, 9 decisions for Sammy/coordinator, Phase 2 split). Summary sent to main.
- PHASE 1 DONE. Waiting for go-ahead (after v19 publish + 4o/4p). Nothing moved, edited or published.
