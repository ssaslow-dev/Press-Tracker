# agent-v20-final (2026-10-28)
Pre-change copies: work/tmp_agent-v20-final/pre/.
## Done
- Master: local work/coverage_current.xlsx = Mac sha 4d7fb37c…ebf24a.
- Handoffs:
  - DECISIONS and CONTRACT got the BUTTONOPT-v1 lines (CONTRACT under "Proposed rows").
  - Stripped shell: code/make_shell.py writes build/shell/shell.html (95 KB). PIPELINE adds shell.html and make_shell.py. The prompt now reads shell.html in the paths list, and step 6 assembles from pipeline/shell.html instead of reading the published index.html. build.sh pipeline step uses shell.html (PIPE_BASE to override). Assembling from the shell is byte-equal to assembling from the full page.
  - Tabs harness: harness.js `--only` and build_testpage.sh pass RELRELATED_JSON (code/release_related.json), so tab_releases carries "rel".
  - _framework.test.js changed: USMAP "click a state" now pins the preview and the expand opens Clips with State; "Data: state map" now checks #gmUs per-state clip counts computed independently; the tone test follows TONELABEL-v1 (DECISIONS 209).
- make_copies (work/tmp_agent-v20-final/copies, report.json): 3,873 copies + 244 release copies; 0 unresolved images, 8 PDF pages restored, 340 photos dropped; 74 AV-cleaned copies.
  - 09772: header fixed in work/html_clean/2025/ws09772o-s04738.html (2026-11-18 → 2025-10-08, per DECISIONS 201). The Mac library file still has the old header line.
- relmatch full run on v20 data: 241 releases, 1,060 related + 152 possibly related (was 1,059 + 153). The 4 changed pairs are listed in the handoff. Written to code/release_related.json. The pipeline copy was replaced directly: it was identical to the old code copy, and the never-shrink merge would have kept 2 stale rows. apply_all reran with no change.
- Channel rule (coordinator msg 1) was implemented before the scope change: avtab NOSHOWCHAN-v1, sheet_task, 53_tabs panel, DECISIONS. Sheet recheck found 0 moves. Handed over to agent-v20-channel.
- Started before the scope change (dropped items):
  - Full harness MOD=all 869/869.
  - sheet_task 34/34, auto 35/35.
  - AV clean 80/75 changed/0 fails.
  - REORG 62/62.
  - copies_check 16/16, with phrases_v20.json: s04423 was merged into s00639, and s00639's text is shared with s04422 (KQED, possibly an ungrouped reprint), so s00002 was used instead.
  - Partial screenshots in work/tmp_agent-v20-final/shots.
  - Draft publish.json, built before the channel change.
- After CHANNEL_DONE, apply_all and --check both OK. build.sh: LIB index f3ee5393…0fa1d8 = PIPELINE index (from shell.html), 15/15 blocks equal. work/BUILD_DONE written. STOPPED (scope change).
- Stale: draft work/tmp_agent-v20-final/pub + publish.json predate the channel agent's avtab/sheet_task edits. Regenerate them from build/pub/pipeline before publishing.
