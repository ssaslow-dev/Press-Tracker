# v20 code pass — shared brief (coordinator, 2026-10-28)
L = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib
Read: README.md, DECISIONS.md (latest lines win), CONTRACT.md, build/phaseB_inbox.md (your items), status/agent-backendclean2.md (new code layout).
Rules:
- Code is folded: edit code/tracker/NN_*.js and source files ONLY in files you own (table below). Never edit build/js_merged.js (apply_all regenerates; guard stops on hand edits). Need a change in a file you don't own → write it to work/tmp_<you>/handoff.md and tell main; don't edit.
- Every change goes to code base + Update button (sheet task/pipeline in build/pub/pipeline via apply_all) + master sheet where data changes.
- Workbook writes: README rule 7, token work/WORKBOOK_WRITER.txt (wait until "none"), re-stage, use CURRENT master sha, backup, diff, commit expectedMtimeMs, verify, update work/coverage_current.xlsx, release, DECISIONS line.
- Library add-only; removals → _to_delete / archive via mv; never delete. No Exa. Don't publish. Don't work around paywalls/blocks.
- Do NOT run the full harness/check suites — final build agent runs them once after all changes (Sammy: no checks before all changes are made). Your own unit checks of new code are fine.
- Log in status/agent-<you>.md. Report to main briefly: what changed (files), sheet sha if written, anything left.
File ownership:
- v20-maps: 14_county_map.js, 52_us_map.js (+ their data builders)
- v20-tabsui: 00_head.js (CSS), 01_authors.js, 03_overview.js, 04_facets.js, 05_table.js, 53_tabs.js, 22_helpers.js, build/tabs/*_data.py
- v20-photos: 06_story_sheet.js, code/make_copies.py, code/clean_html.py, code/clean_rules.json, image packing/build blocks for images
- v20-origin-av: code/reprint_rule.py, AV tab code (AVTAB, wherever it lives outside the files above — if it's in 06_story_sheet.js, write handoff for v20-photos), sheet writes for AVDATE + origin
- v20-docs: README.md, CONTRACT.md wording, _docs drafts, TONE_GUIDE, clean_playbook (docs only)
- NOT in v20 code pass (button, LAST): code/sheet_task.py, 40–43_update_*.js, test_auto — agent-buttonopt Phase 2.
- Ownership change: build/tabs/releases.js + build/tabs/releases_data.py + code/relmatch.py → agent-relrelated (implementing RELRELATED-v1). v20-tabsui must not edit those two tab files.
- DOCS RULE (Sammy 2026-10-28, standing): every agent that changes code, data rules, UI or the sheet must also update L/HANDOFF.md (Changelog line + affected sections) and append a DECISIONS line; CONTRACT when shapes change. Coordinator syncs HANDOFF.md + library docs to the Project after each publish and regenerates the handoff kit.
