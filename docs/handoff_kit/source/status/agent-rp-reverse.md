# agent-rp-reverse — reverse links story/bill/reporter/outlet -> release (RELPLAN Phase 1)
## Rules: build/V20_BRIEF.md. Own: 01_authors.js RELEASES-v2 section (relOf/relLine), 53_tabs.js ctx key, build/tabs/bills.js, reporters.js, outlets.js. Not releases.js. Pre-edit copies work/tmp_rp-reverse/pre/.
## Log
- started; read RELPLAN, V20_BRIEF, relaudit 2/3/4 proposals. "From press release" line is in 01_authors.js (claimed in RELPLAN).
- DONE. Files: code/tracker/01_authors.js (RELREVERSE-v1: relIndex/relsOf/relLine + CSS), code/tracker/53_tabs.js (ctx.rels; BILLSLUG-v1 in AJGTabs.register), build/tabs/bills.js (release titles -> release page; "Press releases N ›" -> list ?bill=&date=), reporters.js + outlets.js ("Press releases" fact, 2 shown + more).
- Coverage: 1,094 tracker stories in release_related.json minus 'possible'-only ones get a panel line (942 tier-1 per audit) + copies (t[7]).
- Root cause of d38d2b91/C3: tab modules register in menu order (releases before bills), so a release page drawn on load had no billSlug; register() now clears TB.drawn and redraws when the bills module registers.
- Scratch build work/tmp_rp-reverse/build.sh (b/srv, not build/pub). Screenshots work/tmp_rp-reverse/shots/: 1_panel_s01010 (3 "from"), 1_panel_s01594 ("related"), 2_bill.png, 2_bill_header.png, 3_reporter.png, 4_outlet.png, 4_outlet_us-fed-news.png. Clicks verified: panel/bill/outlet links -> #press-releases/prNNNNN; bill count -> #press-releases?bill=AB+418 (24). No page errors.
- Not run: harness/tests (build/tests/tabs/bills|reporters|outlets .test.js may need the new fact/link). apply_all not run (final build).
- Noted, not mine: AB 418 2023-24 bill page lists 2025-26 releases that name AB 418 in background (pickSes picks the only session; rp-threads' bill+session rule could feed this).
