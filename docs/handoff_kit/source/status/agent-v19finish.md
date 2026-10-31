# agent-v19finish — finish v19 (took over from agent-tabs, stopped 01:20) and publish live
## Rules (coordinator, Sammy): every change first (incl docs); only node --check / py_compile while building; final build from master 573e3c85…; tests (a)(b)(c) once at the end; re-run only failed checks.
## Log
- 01:4xZ Step 1 (what agent-tabs finished; from its log, markers, timestamps, apply_all --check = clean, 2nd run unchanged):
  DONE by agent-tabs: MAPFIX-v1 (shared map hover/freeze outline, both maps), CHARTFIX-v1 (no overlaid tone line; "Tone over time"
  view, own axis + legend, n>=3), facts-grid CSS, Milestones <details> collapsed, SESSION-v1 toggle (All dates | Session only),
  LISTHEAD-v1 (clean tab header/controls), LINKRULES-v1 (authorLink, issueLink -> Clips, bill links), NAVHIST-v1, SPREADRULE-v1,
  CHARTRULE-v1, ROWLIST-v1, DATATRIM-v1 + DATAMOVE-v1 (Outlets Gone quiet / First story), CLIFIX-v1, DV + J./GV kill rules,
  NAMING-v2 in make_copies.py (current names, files by Story ID, OCR texts via pdf name, undated folder).
  LEFT: facetLink + page scope, embedded Reporters/Outlets rows, Clips panel "page ›" icons, headline->panel in Story travel list +
  "How it spread ›" in the panel, header-corner CSS, tone checkbox still allowed overlay, J. cookie/nav drop rule, newoutlet label,
  docs, final build + tests + publish.
- 02:0xZ Step 2 edits (node --check only): LINKSCOPE-v1, EMBEDROWS-v1, PAGEICON-v1, HOWSPREAD-v1, LINKRULES-v2, HLPANEL-v1,
  TONEVIEW-v1, HEADCORNER-v1 (code/tabs_tracker.js); outlets/reporters/bills/travel modules; bills SESSION-v1 "Coverage by stage";
  clean_rules.json jweekly drop (CookieYes cky-* + nav). Review queue 8yp4a5q8A8PcrQFdYcXPuB: "newoutlet" -> "New outlets" (v11, 1793151804-5d51).
- 02:1xZ Docs: DECISIONS (v19 entry incl. Data card decisions), CONTRACT ("Tracker tabs (TABS-v1)"), README pointer, build/tabs_contract.md addendum; prompt step 7 publishes data/release_texts.json (RELTEXTS-v1, via patch_tabs.py LEAN_PROMPT). Staged /mnt/user-data/outputs/v19docs (= pipeline/docs; DECISIONS 15811728…, CONTRACT 9feff778…, README d9e45b03…).
- Build: master 573e3c85…fcd (work/coverage_current.xlsx); apply_all twice (2nd run unchanged); work/tmp_agent-v19finish/build.sh.
- (a) pipeline-only rebuild (build/pub/pipeline copied to a scratch folder, run as sheet-task step 6) == lib build: 16/16 block files byte-equal, index.html equal (bf4dc267…). No differences to explain.
- (b) harness MOD=all 1400+390: _framework 188, bills 140, outlets 132, releases 149, reporters 148, travel 108 = 865/865 after fixes; REORG/Home 62/62 (work/tmp_agent-v19finish/reorg_v19b.test.js, Data checks follow DATATRIM); no-#clips checks pass in every tab. Fixes: chart empty state for all-filtered (code), bill page stage table skipped without coverage (code), release title not a bare link (LINKUI, code); tests adapted to intended v19 changes (embedded rows, list links open pages / Clips with scope, CHARTRULE sentence, LISTHEAD caption, release counts 88/112 on the new master); v18 comparison page rebuilt with the new data.
- (c) copies on the real build (make_copies NAMING-v2, 3,889 copies): s04685 OCR, s04700 podcast transcript, s04701 (09735 new-outlet Original), s01313 (J. 04391), s04423 (GV Wire 02249): manifest copy + unique-phrase Clips search finds exactly that story + panel shows the copy: 16/16 (copies_check.js). Undated 09773/09774 -> articles/undated.json.
- LIVE v19 = 1793153876-e0f4 (step 1/2 1793153733-7c3d: articles + img/100.json (union with live 100.json) on the v18 page; step 2: index + data/sheet.json + data/release_texts.json + 46 pipeline files). Capabilities carried (db, downloads, mcp TinyFish + Claude Code Remote, sample). Read-back: 75/75 files sha-equal. Preview 2bMQrhKHRzpK9A9qMbzAk6 = same index + banner, no capabilities, version 1793153934-2aaa.
- Deferred: "Uses release text" tag + extra release columns (agent-relcopies2, step 4o). Finding: s04692–s04694 (2026 podcast imports) are tagged ABX1-4 (a Jan 2025 bill) — check the tag.
