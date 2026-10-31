# code/_history: retired code (moved 2026-10-28 by agent-backendclean2; nothing here runs)

## patches/: the anchor-patch steps of the old apply_all_patches.py
These were all no-ops on the folded sources when they were retired; their edits live in the sources now. The old apply_all is in work/tmp_agent-backendclean2/pre/code/apply_all_patches.py.

| step | script | feature marker(s) | edits now live in |
|---|---|---|---|
| 1 | patch_links.py | LINKS-v1/v2 | tracker JS, build_data.py |
| 2 | patch_authors_{build_data,apply_fills,js}.py | T30 | build_data.py, apply_fills.py, tracker JS |
| 3 | make_copies_clean.py | T40 | make_copies.py |
| 4 | patch_clean.py | CLEAN-v1 | tracker JS, sheet_task.py, assemble.py, build_data.py, prompts |
| 4b | patch_canon.py | AUTHOR-CANON | build_data.py, prompt |
| 4c | patch_auto.py | AUTO-v1 | tracker JS, sheet_task.py, assemble.py, build_data.py, prompt |
| 4d | patch_manage.py | MANAGE-v1 | tracker JS |
| 4e | patch_f7.py | F7-v1 | tracker JS, build_data, assemble, sheet_task, prompt |
| 4f | patch_tokens.py | TOKENS-v1 | tracker JS, sheet_task.py |
| 4g | patch_insights.py | INSIGHTS-v1 | tracker JS (code/tracker/50_insights_shell.js), assemble, build_data |
| 4h | patch_linkui.py | LINKUI-v1 | tracker JS, build_data, build/insights/bill_timeline.js |
| 4i | patch_releases.py | RELEASES-v2, RELCHECK-v1 | tracker JS, sheet_task.py, code/sheet_task_prompt.md |
| 4j | patch_reorg.py (+ reorg_pitch.js = build/insights/reporters.js) | REORG-v1, PHONE-v1, NOPHONE-v1 | code/tracker/51_reorg.js, build/insights |
| 4k | patch_relrule.py | RELRULE-v1, RELCHECK-v2 | tracker JS, sheet_task.py, prompt, build/insights |
| 4m | patch_reltab.py | RELTAB-v1, RELCHECK-v3 | sheet_task.py, prompt |
| 4n | patch_avtab.py | AVTAB-v1 | build_data.py, sheet_task.py, prompt |
| 4l | patch_tabs.py | TABS-v1 (+ CHART, AXIS-v1, USMAP-v1, SPLITBILLS-v2, LEGINFO-v1, ...) | code/tracker/52_us_map.js + 53_tabs.js, assemble, build_data, prompts |
| 4o | patch_relcopies.py | RELCOPIES-v1, RELTAB-v2, RELCHECK-v4 | make_copies, build_data, build/insights + build/tabs releases, reltab, sheet_task, prompt, tracker JS, clean_rules.json, release_texts.json |
| 4q | patch_outletrules.py | OUTLETRULES-v1 | sheet_task.py, prompts, apply_fills.py, prep_workbook.py, migrate_ids.py |

DECISIONS.md names each feature marker in its entry.

## pre_split/: sources that were synced into build/js_merged.js as blocks
They are now the tracker section files themselves:
- insights_shell.js → code/tracker/50_insights_shell.js (plus one trailing blank line)
- reorg_tracker.js → 51_reorg.js
- us_map.js → 52_us_map.js (inside the USMAP-v1 marker lines)
- tabs_tracker.js → 53_tabs.js

Edit the files in code/tracker/.
