# agent-ins-reporters — Reporter outreach list (insights feature 4)
- 17:xx started. Contract (build/insights_contract.md) not yet written; working on data/analysis first.
- Data: data block has authors[] + akinds[] (person|staff|org|wire|board) parallel; build_data already applies author_canon.csv; tracker JS adds authorKey/ACANON normalization at runtime. Plan: people only (akind person), key via tracker authorKey (+ canon), count stories (originals), outlets, top-3 topics, avg tone (Very neg -2 .. Very pos +2, Not rated excluded), last date, Reach.
- Contract arrived. Wrote build/insights/reporters.js (13.6 KB, no block), test/reporters.test.js, reporters.md; reference test_reporters/ref_reporters.py + harness_local.js (stand-in before harness.js existed).
- Fixes during test: title-only bylines (atitle == author) leaking in as people (+6) -> skipped; mobile sort select (thead hidden on stacked layout).
- DONE: official harness MOD=reporters 64/64 PASS at 1400 and 375. Screenshots test_reporters/shot-1400.png, shot-375.png.
