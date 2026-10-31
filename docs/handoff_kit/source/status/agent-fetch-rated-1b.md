# agent-fetch-rated-1b
Job: lib/work/jobs/fetch_rated_1b.jsonl (81 = jobs 29-109 of fetch_rated_1). Output appended to lib/work/out/fetch_rated_1.out.jsonl (now 110 lines = 29 + 81; no existing line touched; backup of the pre-run file at work/tmp_fetch_rated1b/out_backup_before.jsonl).
Helpers (mine): work/tmp_fetch_rated1b/{extract.py, build.py, view.py, st.py, decisions.jsonl}. extract/build are copies of code/fetch_rated1 pointed at my transcript, the 1b job file and my decisions file; build also passes `hl_en` and fills `author` from the byline when the job has none. Fetch cache shared: work/fetch_cache.
Pacing: 10 fetch calls of at most 6 URLs, at least 60 s apart (00:45-00:56), plus 13 one-off TinyFish searches.

## Results (81)
- Known block, not fetched: 23 (GV Wire 7, J. Weekly 8, Politico Pro 3, Davis Vanguard 3, State Affairs Pro 1, SF Chronicle 1).
- Fetched: 58 jobs. Verified: 44. Saved copies: 43 (texts/tracker/<sid>.html + staged at /mnt/user-data/outputs/tlib_rated1/<year>/<aid>.html). jg-03879 was verified but not saved: it's an arrest log for a different "Jesse Gabriel".
- Rated from full text: 39 (Neutral 34, Positive 3, Negative 2).
- No Gabriel mention (flagged, not rated): 5. jg-02792 (CalMatters; he's only in a data table that wasn't fetched), jg-03137 (LAT; "Gabrielle Giffords"), jg-03879 (crime log, different person), jg-04120 (LAT; Gabriel Petek), jg-04168 (Times of Israel; sidebar not fetched).
- Failed: 14. Daily News 2 (login), OC Register 2 (login) + 1 not an article (jg-03684 sitemap page), NYT 2 (403), Business Journal 2 (bot block), WSJ 1 (401 paywall), Organic Consumers 1 (bot block), Local News Matters 1 (login), ABC10 1 (bot block), Spectrum News 1 1 (renders headline only).
- Substitute URLs (same outlet and headline): jg-02746 plus.hankyung.com (hankyung.com was bot-blocked); jg-03156 Alston & Bird HTML advisory page (the PDF was unreachable).
- Tone disagreements (6): jg-03501 Neutral→Positive, jg-03575 Neutral→Positive (an EWG guest calls him a "great leader"), jg-04102 Neutral→Negative (Fox insinuates a Planned Parenthood donation motive), jg-03538 Negative→Neutral (editorial, milder pick), jg-03724 Positive→Neutral, jg-04125 Positive→Neutral (his only appearance is an embedded tweet).
- other_bills: jg-03697 AB 1384 (climate adaptation strategy; not in gabriel_bills.json).
- Notes: 22 items are TV caption transcripts from archive.org. The saved copy is only the relevant segment, and caption errors are noted, e.g. "to radical assemblyman" in jg-02908 is likely "Democratic". Word counts for the Chinese and Korean copies are approximate (CJK tokenization).

## Desktop library
Mac reachable. 48 files in tlib_rated1. 5 already existed (the previous agent's ws-02203, ws-01627, ws-01688, ws-01751, ws-01851) and were skipped. Committed 43 new files (2 calls, no force, 0 rejected). SHA-256 of all 43 checked on the Mac: all match. Logged in work/library_adds.csv (43 rows). Nothing pending.

## Self-check
Every 1b sid is in the output exactly once. Each saved line has a texts/tracker file and a staged file. Spot-checked jg-02618 saved-copy format (div header, h1, byline, paragraphs).
