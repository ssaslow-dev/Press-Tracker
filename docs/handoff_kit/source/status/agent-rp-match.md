# agent rp-match: RELRELATED-v3 (RELPLAN Phase 1), 2026-10-28

## Files changed (owned)
- code/relmatch.py: VERSION RELRELATED-v3. New: story_ctx (per-story inputs), bills_in_tokens, session_of, own_bill_sessions,
  post_anchor, _later_ok, _leads_with, _formula_only, resolve (per-story tier-3 choice, single nearcopy), _story_pairs,
  update_stories; match_all / match_story now score each story against every release and resolve it; to_state dedupes
  by Story ID; main --update recomputes the affected stories (byte-identical to a full run); --bills-leginfo (default next to
  relmatch.py); CSV gains 6 evidence columns.
- code/release_related.json: full run on work/build_last/lib/index.html + work/tmp_agent-v20-final/srv/articles.
  Backups: work/tmp_rp-match/release_related.v2.backup.json, relmatch.v2.py, test_relmatch.v2.py. Pair CSV: work/tmp_rp-match/related_v3.csv.
- work/tmp_agent-relrelated/test_relmatch.py: 3 v1/v2 tests padded (their synthetic stories are now >60% release text =
  nearcopy), version via M.VERSION; new class V3 (20 tests: translation, bill named in text, nearcopy, anchor, later
  window/next release/own bill/lead/resolve, laterquote + formula, AV, to_state dedupe, update == full). 50 tests pass
  (hand-label regression included).
- Docs: build/relplan_contract.md "rp-match"; DECISIONS RELRELATED-v3; HANDOFF changelog + 3.3 + glossary; CONTRACT one line.
- Not run: apply_all, build.sh, harness.

## Results (v20 build, 241 releases)
| | v2 | v3 |
|---|---|---|
| Related (tier 1) | 1,064 on 176 releases | 1,223 on 180 releases (1,103 stories) |
| Possibly (tier 2) | 152 | 62 |
| Later coverage (tier 3) | – | 121 on 46 releases (later 84, laterquote 37) |
No v2 pair lost (diff work/tmp_rp-match/diff.py).

## Hand checks (precision)
- Translations: possible -> bill 103, all read: 99/103 (wrong: pr00054/s01386 belongs to pr00055; s02934 Costco roundup;
  s01174 another member's hate-crime bill; s01934 "awaited signature" the day before). New topic via translation 9/9. 96%.
- Bill named in text: first cut 38 at 34/38 (89%); added BILLTEXT_COS 0.15 on the text -> 30 kept, 29/30 (s01000 borderline).
- nearcopy: 25 at 23/25 (two were the release quoted inside a later one); one nearcopy per story -> 23/23.
- anchor: first cut 0..+14 d, 37 at 22/37 (later bill coverage, roundups); cut to 0..+7 d and text cosine >= 0.15 (or
  headline >= 0.10) for name paths -> 16/16.
- later: first cut 141, sample 40 at 35/40 (roundups, local spin-offs, other bills); added "leads with the bill or Gabriel"
  (headline or first 90 words) -> 84; tuned-sample remainder 30/31 + fresh random 30 at 29/30 = 59/61 (97%).
- laterquote: first cut 43 at 38/43 (bio formula; quotes of another member's bill description in the 2023 caucus
  priorities release); bio phrases added to FORMULA and cosine >= 0.125 -> 37 at 36/37 (s03871 Spectrum counted wrong).
- AV: transcripts (54) were already in the texts; 8-word probe found nothing new beyond s01096 (Tucker Carlson quoting
  pr00116), now `quote` (transcript quotation skips the topic floor). Same-bill-week AV: 14 unlinked, 11 roundups; short
  station summaries (<= 400 words) -> `possible` (+3, 3/3: s03004, s01820, s04682).

## Update mode
- Backend review finding 2 (duplicate rows): fixed in to_state (one row per Story ID per release) + test.
- Byte-identical: state minus pr00243 + s01874 -> --update -> == full; minus pr00116, pr00231 + s01944, s00102 -> ==;
  update on the full state is idempotent; update with only 2026.json passed (3.4 s) -> ==.

## Handoff
work/tmp_rp-match/handoff.md: apply_all merge_rel_related is add-only and would keep 137 old row types + version v2 in the
pipeline copy; reltab.RELATED_TYPES should be tier 1 (drop `later`, add `anchor`); rp-reverse add anchor/laterquote;
releases.js must route tier 3 into "Later coverage".
