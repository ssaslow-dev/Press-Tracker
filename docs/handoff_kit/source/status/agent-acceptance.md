# agent-acceptance log
- 2026-10-27 start. Read spec (build/acceptance_check_final.md), DECISIONS.md, final_pass/F4/manifest.json (Version 8, 1793119028-42ac).
- Downloaded all 109 published files (index.html sha = F4 manifest). Served locally; Playwright with mocked window.claude (db/mcp/sample/downloads in-browser only). No real writes, no trigger fired, no Exa.
- Check 1 PASS (4,130 stories; only console error = sandbox-blocked Google Fonts).
- Check 2 PASS 50/50 (web 14, NewsBank text 10, ProQuest 10, print PDF 8, TinyFish 8). Skipped: 184 BLOCKED, 25 RETRY. 0 empty copies among 3,830 badges.
- Check 3: reach PASS except retired 'Spanish-language & ethnic' on 4 stories; authors PASS; topic PASS; bills FAIL (AB 130 option, 3 stories from sheet Bills); links PASS; search PASS; Update dry run PASS; old jg- PASS.
- Report: final_pass/F5/acceptance_report.md. Done.
