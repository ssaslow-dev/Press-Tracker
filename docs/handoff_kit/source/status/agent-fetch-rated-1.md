# agent-fetch-rated-1
Jobs: lib/work/jobs/fetch_rated_1.jsonl (110). Output: lib/work/out/fetch_rated_1.out.jsonl. Decisions (markers + ratings): lib/work/fetch_rated1_decisions.jsonl.
Tools: lib/code/fetch_rated1/{extract.py (pulls TinyFish results from my transcript into work/fetch_cache), build.py, urls.py}.
Mac copies staged at /mnt/user-data/outputs/tlib_rated1/<year>/<aid>.html. Mac bridge not connected at 00:39 (2026-10-27).
- 00:39 jobs 0-11: 1 saved (ABC7 budget), 1 tag page (Daily Breeze), 10 fetch_failed (PublicNow bot_blocked; jweekly 403; Local News Matters login; jurisora/expressnews challenge pages).
- 00:42 STOPPED at 29/110 (jobs 0-28 written to the output). Saved+verified 5: jg-02068, jg-02117, jg-02172, jg-02259, jg-02566 (all agree with current tone). Not saved: 24 (20 fetch_failed, 1 tag page jg-01821, 3 partial/shell: jg-02093, jg-02125, jg-02513).
  RESUME at job index 29 (jg-02618): python3 -I code/fetch_rated1/urls.py 29 35; build.py skips sids already in the output.
  Mac never reachable -> no Desktop adds; the 5 staged copies are NOT yet in library_adds_pending.csv.
