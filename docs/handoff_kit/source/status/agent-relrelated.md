# agent-relrelated: release page "Related stories" (Sammy comment eb3d0330)
## Rules: no Exa, no publishing, no edits to code/ or build/ (agent-backendclean2 owns them); work in work/tmp_agent-relrelated/.
## Log
- 04:3xZ Read README, DECISIONS (release rule L136, EXCERPT L142, reprint window L158, "Uses release text" deferred L170), phaseB_inbox, relpage.py, relcopies2/3 logs (patch_relcopies.py is not in code/ any more; relcopies3 log read). Data: work/tmp_agent-relcopies3/tb/srv (v19 + Release IDs) index blocks + articles/*.json + code/release_texts.json (load.py → data.pkl).
- Cause: build/tabs/releases.js related() (= pipeline/tabs/releases.js) = same bill anywhere in the 2-year session, or the same Issue ±30 days; `uses` never filled. Measured (measure.py): 241 releases, 188 with lists, 12,959 rows, 92.0% without evidence; 48% predate the release.
- Rule RELRELATED-v1 (relmatch.py): text / quote / bill / topic, plus a "possible" tier; thresholds calibrated on round-1 labels (cos 0.14, headline 0.10, topic 0.25, text cosine floor 0.10).
- Hand checks: 30 releases (sample_keys.json, labels_round1.txt) + 14 holdout releases (holdout_keys.json, labels_round2.txt). v19 precision 8.2% / 14.1% pooled → new 98.8% / 100%; recall ≈89% / 94%. afterprec.py reproduces this.
- Outputs: spec.md, relmatch.py, test_relmatch.py (14 pass), out/related_v20.csv (1,212 rows: 1,059 related + 153 possibly), out/release_related.json (state, keyed by Release ID). Incremental --update was checked byte-equal against the full run.
- Queued: phaseB_inbox "RELEASE RELATED STORIES (Sammy comment eb3d0330)".
## Handoff
- Implementation lands in code/ and pipeline/ per spec.md §4 (owner: whoever takes v20 after backendclean2). Open for Sammy: keep text matches 31–90 days after the release (73 pairs) or cut the window to 30 days.
- 05:0xZ IMPLEMENTED (coordinator: Sammy approved, 90-day window kept; ownership releases.js / releases_data.py / code/relmatch.py).
  - Wrote code/relmatch.py, code/release_related.json and build/pub/pipeline/release_related.json; edited build/tabs/releases_data.py (tab-releases "rel") and build/tabs/releases.js (related list, Possibly related, Bill coverage counts).
  - Test page work/tmp_agent-relrelated/tb/srv: screenshots shots/*.png, no page errors.
  - Handoffs in work/tmp_agent-relrelated/handoff.md: apply_all PIPELINE → final build; step 6 → buttonopt.
