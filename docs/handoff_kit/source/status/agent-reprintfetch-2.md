# agent-reprintfetch-2 (T43, half 2)

- 2026-10-27T10:12Z started. Read README, DECISIONS (T43 entry 2026-10-27, blocked/retry placeholders, Gabriel incl. non-Latin, San Gabriel, californiafiles skip, outside-article rule), build/clean_playbook.md, status/agent-code.md, status/agent-retry.md (precedent).
- Targets: 233 rows of work/final/reprint_fetch_targets.csv with half=2. No californiafiles.org rows in this half.
  - 7 blocked-known (hosts in work/final/blocked_marks.csv: dailynews.com x3, localnewsmatters.org, expressnews.com, politico.com, laprogressive.com): not fetched.
  - 5 already had a library file before this run (ws-00620 2024, ws-00660 2024, ws-01527 2026, ws-01988 2025, ws-02914 2023): not fetched, not overwritten, recorded as saved with the existing file.
  - 221 fetched with TinyFish fetch_content (html format), 10 URLs per call, >=52 s between calls (<=12 fetches/min); 23 calls, 10:12-10:34Z (one batch re-fetched once with links on, so the result was saved to a file).
- Cleaning: code/clean_html.py clean_page(..., mode='find') with the sheet row (coverage_current.xlsx), then page_check. Pages wrapped like agent-retry (library header div + h1 from the fetched title when the fragment has none).
  Post-passes in work/tmp_agent-reprintfetch-2/build.py, all playbook rules the find-mode cleaner did not apply (mostly because the >35% guard kept the page as it was):
  - California Healthline x3: the page's only h1 was the republish box at the end, so find:head would have dropped the whole article; those h1s were demoted and the fetched title used as h1 (nothing removed then except via Related Topics tail on ws-00797).
  - KQED x2 (ws-00918, ws-02665): tail from "lower waypointnext waypoint" (player + window.__INITIAL_STATE__ JSON dump, 12-14k words).
  - Tail markers after the last Gabriel prose block: "Tags" (Desert Review, Phila. Tribune, IV Press ws-02715, SMDJ ws-03509), "Post a comment as Guest" (SMDJ ws-00494), "Related Topics" (CHL ws-00797, Epoch ws-00969); SMDJ Prev/Next teasers (ws-03509).
  - Daily Republic ws-00790: appended reader comment section removed.
- Saved add-only to the Mac via device_commit_files (existence re-checked for all 410 target paths just before; none existed): 205 cleaned pages to Tracker library/<year>/<aid>.html and 205 fetched pages to Tracker library/_original_html/<year>/<aid>.html. Mac scratch only in $HOME/mnt/outputs (rf2_existing.txt, rf2_mac_sha.txt). Cleaned copies also in work/html_clean/<year>/<aid>.html (205 new; none existed). library_adds.csv: 205 rows appended (staged_path /mnt/user-data/outputs/rf2/lib/...).
- Results: work/final/reprint_fetch_results_2.csv (233 rows; cols aid,sid,url,result,placeholder,library_file,words,byline_found,note).
  saved 210 (205 new + 5 pre-existing) | blocked 10 | blocked-known 7 | error 3 | incomplete 2 | no-gabriel 1 | wrong-page 0.
  Placeholders: BLOCKED – TinyFish 17, RETRY – TinyFish 6, blank 210.
  - blocked: fox40 403 (ws-00534), ktla 403 x2 (ws-02428, ws-03046), dailyjournal.com 403 (ws-02099), dailybreeze login_required x2 (ws-00929, ws-03064), Times of Israel jewishchronicle bot_blocked (ws-00115), LA Sentinel bot_blocked (ws-02722), Washington Examiner paywall x2 (ws-00414, ws-00901).
  - error (RETRY): lite.aol.com 404 (ws-00072), aol 404 (ws-00852), newsnationnow invalid_url (ws-03449).
  - incomplete (RETRY): NBC Bay Area video page with no article text (ws-00537); KTLA 4-paragraph teaser of an LA Times story (ws-03841).
  - no-gabriel (RETRY): Press Democrat ws-03454 fetched in full (641 words), Gabriel not named.
  - byline_found filled for 169 saved rows (TinyFish author field; ijpr author URLs turned into names).
- Judgment calls: headline variants accepted when the URL slug and story match (ws-00016, 00453, 00758, 00862, 00987, 01136, 01428, 02344, 03155 retitled "CA Assembly approves bill to ban key ingredients in Skittles…", 03246). Short but complete items kept: smmirror ws-01280 (165 words), NPR via ijpr ws-03237 (214), Patch ws-03658 (222), SMDJ ws-03509 (225).

## Self-check
- Every saved page: page_check 'ok', Gabriel in the cleaned article text (Gabriel regex from clean_rules), headline match >= 0.76 (one 0.38 checked by hand: ws-03155).
- Playwright render (work/tmp_agent-reprintfetch-2/shot_*.png): ws-00547, ws-00918, ws-03509, ws-00078, ws-02715: all render, text + Gabriel present, no JSON dump / comment / calendar chrome left.
- SHA-256 of all 410 Mac files (205 library + 205 _original_html) vs the container copies: listing digest identical (fb74bfc3…c6502), 410/410 match.
