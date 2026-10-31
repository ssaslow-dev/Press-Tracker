# agent-relrule — Sammy 2026-10-27: "Use the same standard for determine if something is a release as you do for a reprint."
First pass, READ-ONLY: no workbook write, no publish, published tracker untouched, no Exa, no Mac bridge.

## Log
- Read README, DECISIONS (newest), code/reprint_rule.py, status/agent-releasecheck.md, agent-insights v16 section.
- Release texts: all 236 in-scope tab releases (office always; caucus >= 2020-11-18) already had their body in
  work/tmp_agent-releasecheck/releases.json (extract.py keeps only the Drupal body field + dek, no site chrome) -> 0
  TinyFish fetches needed. The other 5 of the 241 are tracker releases with no official posting (no text to test).
  Release versions for the rule: headline+dek+body, and body alone (NewsBank texts carry no headline).
- Row texts: the regroup's text build (work/tmp_agent-regroup2/texts_v2.pkl: NewsBank JSON + print PDF, keyed by Old Article ID)
  + each row's own cleaned copy from work/tmp_agent-final-F4/html_clean_final (fallback work/html_clean), error copies
  (final/error_copies.csv) skipped, jg- copies kept only if they pass against the row's NewsBank text (regroup vers()).
- Test: reprint_rule.text_verdict (>=25-word runs covering >=90% of BOTH; clutter, captions, edge pass) unchanged.
  Population: every Press release = Yes row (498) against every release sharing a 25-word run (+ its linked release);
  every other row dated -1..+30 days after a release whose text shares a 25-word run or whose headline overlaps
  (reprint_rule.headline_overlap). No-text fallback: reprint_rule's headline+author rule needs people on both sides;
  releases have no byline -> never verifiable -> "untestable".
- Scripts: work/tmp_agent-relrule/relrule.py (test), changes.py (proposed cells); outputs
  work/out/release_rule_results.csv (554 rows), work/out/release_rule_changes.csv; draft code change
  work/tmp_agent-relrule/proposed/RELRULE-v1_draft.py.

## Results
confirmed 88 (62 high, 26 low: 19 edge, 7 clutter) | add 10 | remove 16 | untestable 63 (12 flagged rows with no saved
text, 46 unflagged headline-overlap rows with no text, 5 rows of the 5 releases not posted officially) | flagged rows not
tied to a Gabriel release (other issuers; this rule does not decide them) 377 (95 tested-fail, 271 no shared run, 11 no text).
Remove list: 7 of 16 are US Fed News rows whose NewsBank text is the service's first-paragraph excerpt (62-93 words vs
455-714) - verbatim but fails "90% of both".
HeySoCal 02913: 84.0% row / 73.1% release -> fails (so does its original 02912, 86.4/73.1): s00842 loses release status.
Sammy's 15 + AB 2020: 10 releases confirmed (13 rows), 2 fail (s00842 carbon offsets 2 rows; s01304 04377 67.4/52.6),
3 untestable (08616, 08402 Davis Vanguard BLOCKED; 07038 AB 2020 PublicNow BLOCKED).

## Proposed (not applied): Coverage 26 cells (16 Yes->blank, 10 blank->Yes), Originals 23 mirror cells,
Press releases tab 49 cells on 24 releases (7 Yes->No, 5 No->Yes, 12 ID/count). Questions for Sammy in the report.

## Self-check
- Every flagged row classified: 88 confirmed + 16 remove + 17 untestable + 377 other-issuer = 498 = Coverage Press release = Yes. OK.
- No confirmed row matched a different release than its current link (0).
- Spot checks: nb-03175 (US Fed News) text read = header + 1 paragraph + htlive footer; ws-03362 (SDJW 09155) is a
  JPAC-written version, 0% shared runs.

## Second pass (Sammy's answers) - 2026-10-27 ~21:45Z
- US Fed News "why excerpts": 6 rows = NewsBank record itself is the short version (1-page PDFs ending with HT footer + copyright + NewsBank citation; 63-95 words; all 6 US Fed News records Feb 2022-Apr 2023 are short, others 290-1,569 words); 01759 = different release (Speaker Rivas). Not re-savable from NewsBank. Rows untouched.
- SHEET: work/tmp_agent-relrule/write_wb.py on the staged master (sha 572b8e12, no lock, mtime 1793132924801) -> wb/relrule.xlsx (sha 8dbdc7a9046fdac78be7211c5549528740ad3b67861a074b97dd9986a91857e8); diff 948,724 cells: 128 value changes = expected, 0 format changes, tabs/freeze/filters equal. NOT COMMITTED: this agent has no SendUserFile (device_commit_files needs its fileUuid) and device_bash does not reach the Mac file system. Staged for the coordinator: /mnt/user-data/outputs/relrule/ (new master + "AJG Coverage - NewsBank BACKUP before release text rule 2026-10-27.xlsx", sha 572b8e12). coverage_current.xlsx NOT updated (waits on the commit).
- CODE (apply_all; 2nd run unchanged): code/release_rule.py, code/release_texts.json (244), code/patch_relrule.py = step 4k (RELRULE-v1 JS + v1b-d CSS, RELCHECK-v2 sheet_task, prompt, SIDMAP-v1 prompt, view note), build/insights/release_pickup_data.py v3, apply_all PIPELINE += release_rule.py, release_texts.json (merged), sid_map.json; NOPHONE-v1 in code/patch_reorg.py; PITCH24-v1 in code/reorg_pitch.js + reorg_tracker.js link; tests: build/insights/test/release_pickup.test.js, reporters.test.js, work/tmp_agent-reorg/reorg.test.js (phone section -> NOPHONE checks). Pre-edit copies in work/tmp_agent-relrule/*.pre_*.
- TESTS on v18 candidate (live v17 + pipeline-only rebuild of wb/relrule.xlsx): insights MOD=all 310/310, reorg 68/68, relrule_ui 22/22, links 23/23, display 22/22 (fixture articles), sheet task suite 34/34, RELCHECK-v2 dry run 11/11, pipeline rebuild = lib build (data/idmap/rows/ins_release_pickup byte-identical; idmap 4,123), 390 px header = v16 (226 px, nav 174/39/358; only the "Press desk" label differs). relwire.js (v16) N/A: after the rule no tracker story carries a release (all copies are flagged rows). _shell harness N/A on an integrated page.
- v18 package ready (NOT published; waits on the commit): work/tmp_agent-relrule/v18/pub (index.html sha d8d11234…, data/sheet.json from relrule.xlsx, pipeline/), shas in v18/pub_shas.txt. Docs staged /mnt/user-data/outputs/v18docs/.

## Third pass (01759 unmark + EXCERPT-v1) - 2026-10-27 ~22:00Z
- EXCERPT-v1 in code/release_rule.py (DIST_HDR/DIST_CUT strip, excerpt_cover, match() fallback mode 'excerpt', file_versions adds excerpt versions); sheet_task row_versions keeps excerpt versions (patch_relrule re-applied on the pre-v2 sheet_task). EXCERPT_MIN_WORDS = 50 as specified -> only 04044 (56) and 03733 (59) pass; 04286 28, 04162 34, 03997 36, 04319 44 words. 01759 fails (56.6%). Exception changes no other row (scan of all NewsBank texts with a distribution header).
- Two variants staged (write_wb2.py, from master 572b8e12): min50 sha b34c3ce4… (143 cells: Coverage 23, Originals 19, tab 101) and min25 sha 35f97ebb… (132 cells: 23/19/90); diffs = expected, 0 format changes. Packages work/tmp_agent-relrule/v18_ex50 (index 7ab86e32…) and v18_ex25 (index fa682be5…, pipeline release_rule.py EXCERPT_MIN_WORDS = 25); each: relrule_ui 22/22, insights 310/310; dry run 14/14 incl. excerpt pass/fail; sheet task suite 34/34.

## v18 published - 2026-10-27 ~22:10Z
- Coordinator chose >=25 words; min25 master (35f97ebb…) committed by coordinator = work/coverage_current.xlsx. code/release_rule.py EXCERPT_MIN_WORDS = 25; DECISIONS open question closed; apply_all 2nd run unchanged; lib pipeline = v18_ex25 package (diff -r equal; __pycache__ dropped from the package).
- Read live v17 (1793135788-23f5) first; PUBLISHED v18 = version 1793138628-35f4 (index.html + data/sheet.json + 32 pipeline files; articles/img/pdf kept; capabilities carried forward). Read-back: all 34 published files sha-equal to the package (work/tmp_agent-relrule/readback_shas.txt). index.html fa682be5…, data/sheet.json a39dcfc2… (= master 35f97ebb…).
- Docs staged /mnt/user-data/outputs/v18docs (= pipeline/docs): DECISIONS 6e9e575a…, CONTRACT e067d28c…, README df8e02ce…, TONE_GUIDE 4091b80f…, clean_playbook 31a75743…. Mac _docs copy: coordinator.

## PERIOD-v1 (Press desk period bar) - PAUSED by Sammy 2026-10-27 ~22:35Z ("pause the press desk time period bar")
Where it stopped: code + view edits written and applied; insights harness 310/310 on the v19 candidate (with test
updates); the new browser test work/tmp_agent-relrule/period_ui.js written but NOT yet run; no DECISIONS/CONTRACT entry;
v19 NOT published.
Lib restored to v18: apply_all step 4l unwired (and its helper-copy entries removed); PERIOD block removed from
build/js_merged.js; release_pickup/bill_timeline/story_travel views reverted (exact reverse of the anchors); code/reorg_pitch.js,
build/insights/test/harness.js, reporters.test.js, bill_timeline.test.js back to their v18 versions. apply_all twice: second run
unchanged; build/pub/pipeline == published v18 pipeline (diff -r clean); js_merged == v18 tracker.js; re-assembling v18 from lib
gives index sha fa682be5… = live v18.
To resume: everything is parked in work/tmp_agent-relrule/period_parked/ (patch_period.py, period_shell.js, the PERIOD versions of
reorg_pitch.js, apply_all_patches.py, harness.js, reporters.test.js, bill_timeline.test.js, the three patched views, js_merged.js,
period_ui.js). code/patch_period.py and code/period_shell.js are still in code/ but not wired. Steps left: re-wire 4l (copy
period_parked/apply_all_patches.py hunks, or re-add the step after 4k + helper list), restore the PERIOD reorg_pitch.js and the
three test files, apply_all, run period_ui.js + harness + reorg/links/display/relrule_ui at 1400/390, DECISIONS + CONTRACT
(ctx.period/ctx.inPeriod/"ajg:period"), docs to v19docs, publish v19 from v18 (1793138628-35f4). v19 candidate build:
work/tmp_agent-relrule/v19/srv (built before the revert).
