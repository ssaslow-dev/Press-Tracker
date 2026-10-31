# agent-links — status log
- 2026-10-27T05:01:16Z started; read README/DECISIONS/CONTRACT/BOARD/agent-display/agent-ids; snapshot js_merged.js + build_data.py into work/tmp_agent-links/ (orig copies)
- 05:01:49 inventory of 7 link columns done; scope change received (only sheet links from NewsBank/ProQuest/publisher's own site)
- 05:02:34 final scope: CSL links + publisher's own links only
- 05:07:53 code/patch_links.py written (3 JS + 4 build_data anchored edits, idempotent verified); blocks built pre/post migration; analysis: 63 originals with no listed link (986 if CSL links are not derived for NewsBank article links)
- 05:25:20 re-snapshot v7 (write1) files: patch applies; composes with agent-authorsplit in either order (byte-identical). Suites on copies: links 23/23, display 18/18, reach 8/8, authors 16/16, update 39/39. Handover: build/links_patch.md, code/patch_links.py, build/test_links/. No shared build file edited, nothing published.
- Questions for Sammy (in links_patch.md): derive CSL for NewsBank article/print-edition links (no CSL column in sheet; 63 vs 781 originals with no link); own-site judgement calls; 15 Print Article IDs with no link.
