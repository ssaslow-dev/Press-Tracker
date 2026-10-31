# agent-relpre: RELRELATED-v2 (pre-release coverage), 2026-10-28
## Files changed
- code/relmatch.py: VERSION RELRELATED-v2; type `pre` (LABEL "Covered the announcement before the release"), PRE_WIN (-14,-1), name_pairs / dollar_figures / milestones helpers, Index._pre_anchors, pre_evidence, _nearer_bill_release, _explained_by_earlier; match_all pool starts at -14; CSV column "Before-release evidence". v1 types unchanged and take precedence.
- work/tmp_agent-relrelated/test_relmatch.py: now imports code/relmatch.py; v1 test "text before release" moved to -15 days (and asserts -10 = pre); 16 new tests (class Pre: s01827→pr00244 synthetic whole-issue text, partner, passage locality, 14-day edge, month-dated, intro-before-signing exclusion, anticipatory headlines, earlier-release text, nearer bill release, topic floor, no-bill subject path, match_all/to_state; class RealPre: real s01827→pr00244 on the v20 build). 30 tests pass (label regression included).
- code/release_related.json: full run on work/build_last/lib/index.html + work/tmp_agent-v20-final/srv/articles. Backup of the v1 file: scratchpad relpre/release_related.v1.backup.json. Pair CSV: scratchpad relpre/related_v2.csv.
- Incremental --update (--releases pr00244 --stories s02162 on a state missing them) is byte-identical to the full run.
## Results
- +4 related links on 4 releases; 0 removed; related 1,060 → 1,064, possibly 152 unchanged; releases with related 174 → 176.
- Hand-check: all 4 gains correct (s02162 = preview of the Day of Service event the release reports; borderline but same event). Stress test with a 90-day window: 8 links, 7 correct (pr00063 Breed Street Shul budget stories −15..−24 d; wrong: pr00009/s01601 −29 d), so the 14-day cap matters. ~45 near misses in −14..−1 reviewed: all excluded ones were earlier-milestone or anticipatory coverage (e.g. "Which bills will Newsom sign?", "awaits Newsom's decision", Assembly passage before signing).
## Handoff (not my files)
- build/tabs/releases.js: EV has no 'pre' key and evCount() lists only text/quote/bill/topic, so pre rows show in the list with no label and are not counted in the caption. Add EV.pre = 'covered the announcement before the release' and 'pre' to the evCount list; the caption's window text should mention "up to 14 days before". lagTxt already prints "−9 days".
- spec 4e check "No release page lists a story dated before the release −1 day" is superseded (pre rows go to −14).
- apply_all merge_rel_related adds the 4 rows to pipeline/release_related.json but keeps its header version "RELRELATED-v1" (header fields only added when missing).
- s01827 date: verified Oct 15, 2026 (no sheet change).
