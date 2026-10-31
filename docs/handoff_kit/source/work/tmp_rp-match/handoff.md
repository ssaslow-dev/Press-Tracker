# rp-match handoff (files I do not own)

1. code/apply_all_patches.py `merge_rel_related` (coordinator / rp-final). It is add-only by Story ID and keeps the pipeline
   copy's header. With RELRELATED-v3 that loses the type changes on existing rows: 103 `possible` -> `bill`, 23 `text` ->
   `nearcopy`, 11 `topic` -> `bill`, and the version stays "RELRELATED-v2". Suggested fix: when src["version"] > dst["version"]
   (or always), take src's row for every (release, Story ID) present in src (keep dst-only rows, the Update button's adds), set
   dst version = src version, and dedupe by Story ID. Otherwise pipeline/release_related.json keeps 152 "possibly" rows.
   Simplest for the v20 build: copy code/release_related.json over pipeline/release_related.json (it was regenerated from
   the full data and every story the pipeline holds; the pipeline copy has no rows the full run lacks today: 1,216 pairs =
   the v2 full run).
2. code/reltab.py (rp-copies): RELATED_TYPES = text, quote, bill, topic, pre, later, nearcopy -> should be the tier-1 set
   {text, nearcopy, quote, bill, topic, pre, anchor}; `later`/`laterquote` are tier 3 (not related). Better:
   `{t for t, n in relmatch.TIER.items() if n == 1}`.
3. code/tracker/01_authors.js (rp-reverse): add `anchor` (tier 1) and `laterquote` (tier 3, uses the release's words) to
   REL_RANK / REL_EV (/ REL_FROM for laterquote).
4. build/tabs/releases.js (rp-ui): prep() must route `later` / `laterquote` rows into a "Later coverage" section (today every
   non-`possible` row lands in Related); EV + evCount() need `nearcopy`, `anchor`.
5. code/sheet_task_prompt.md (rp-button): the relmatch step is unchanged; it may add `--bills-leginfo pipeline/gabriel_bills_leginfo.json`
   (default already resolves next to pipeline/relmatch.py). Pass every articles year the run read; stories of years not
   passed keep their rows.
