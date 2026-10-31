# agent-fetch-2 (T17, batch 2: 96 jobs from work/jobs/fetch_2.jsonl) — DONE 2026-10-27

Results: 96 output lines in work/out/tone_batch_fetch2.out.jsonl
- 41 pages fetched, verified (outlet + headline, mentions Gabriel), saved, and rated in the same read:
  copies in work/texts/tracker/<Story ID>.html (viewer + search) and staged for the Desktop library at
  /mnt/user-data/outputs/tlib_fetch2/<year>/<Article ID>.html (identical bytes).
  Tone: Neutral 28, Positive 12, Negative 1 (jg-01852, SupplySide on AB 2244). Also topic, bills, author, words, mentions_gabriel;
  hl_en + text_en for the 3 Spanish LA Times stories (jg-01872, jg-02673, jg-03962).
- 55 flagged, nothing saved: J. Weekly 403 (11), ABC10 bot_blocked (7), Politico Pro paywall (7), Politico bot_blocked (6),
  Politico partial page w/o Gabriel (5), State Affairs Pro paywall (3), SFGate/SF Chronicle challenge (5), video pages (2),
  login/invalid/blocked others (4), and 4 whose fetched page does NOT mention Gabriel — check those rows:
  jg-02693 (NBC LA, FDA Red No. 3), jg-03239 (Sac Bee red-dye Halloween list), jg-03813 (Daily News column; photo caption only),
  jg-03973 (CalMatters 2020 results shell).
- No workaround attempted for blocked/paywalled sites.

Notes for the coordinator
- jg-04277/ws-03961 → written under the real IDs jg-00240 / nb-00573 (local file work/texts/tracker/jg-00240.html,
  staged 2025/nb-00573.html). Nothing was ever committed under ws-03961.
- jg-02198 (E&E) rated "from article excerpt" — only 4 paragraphs fetched.
- jg-04092 (Sac Bee Influencers): saved only the Gabriel entry of a ~500-entry page.
- Desktop-library adds: Mac was offline; NOTHING committed. All 41 listed in work/library_adds_pending.csv
  (aid, sid, year, device_path, staged_path, source_url, sha256). work/library_adds.csv not created (no adds).
- Tooling (reusable): code/fetch2/extract.py (pulls fetch results from transcripts/tool-results into work/fetch_cache, keyed by URL hash),
  code/fetch2/build.py (markers + ratings → saved copy + output line), decisions in work/jobs/fetch2_dec_*.jsonl.
