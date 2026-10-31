# agent-authors (T24) — status log
- 2026-10-27 start. Read README/DECISIONS/CONTRACT/BOARD/TONE_GUIDE. Inputs: work/coverage_current.xlsx (Coverage, old IDs). Helpers: work/tmp_agent-authors/.
- Scope: 2,645 Original/Reprint rows with blank Author / byline; 418 covered by texts/nb_author_fills.csv → 2,227 to resolve.
- Saved copies read once: Desktop library (3,497 HTMLs, header/meta/JSON-LD/By-lines extracted on the Mac → compact index), texts/tracker, artifact articles json, NB texts, prior fetch outputs + fetch_cache. 417 rows resolved from saved copies; 62 reprints inherit from original (same headline).
- TinyFish queue: 995 rows with live publisher URL (Originals first); skipped hosts known to block/paywall (jweekly, abc10, publicnow, politicopro, stateaffairs, sfchronicle/sfgate, google search links, prior errors) and 34 archive.org TV transcripts (no bylines).
- 04:50 coordinator: add authors / titles columns (Author 1..N split, '<Outlet> Editorial Board' counts as name). Will do at assembly.
- PAUSED TinyFish per Sammy/coordinator after 100 of 946 queued rows (≈190 URL fetches incl. byline-selector passes; no workaround of blocks/paywalls). Remainder: work/out/author_tinyfish_remaining.json (846 rows, resumable; helpers tmp_agent-authors/batch.py, extract_tf.py, proc2.py, assemble.py).
## Outputs
- work/out/author_fills.csv — 530 rows: aid (OLD id), sid, row_type, author (full byline text; "Name, Title" when a title exists), authors (names in order, " | "), titles (same order, " | ", blank if none), kind, source, evidence, note.
  By source: desktop 349, original (same-headline inheritance) 71, tinyfish 70 (42 live this pass + 28 from earlier fetch passes/cache), nb_text 29, article_json 9, tracker_html 2.
  By kind: person 220, staff 174, wire 72, organization 64. No editorial-board bylines found among these rows.
- work/out/author_none.csv — 1,697 rows: status none_found 851 (all sources checked, listed per row) / pending_tinyfish 846.
- work/out/author_pass_extras.csv — 1,334 rows with blank Word count or Tone where this pass read the text (word count from Desktop copy or live page; mentions_gabriel for live pages) — reuse instead of re-reading.
- work/texts/authors_fetch/<aid>.html — 63 live-page copies (viewer/search reuse). Desktop library adds: 2 NEW files (2017/nb-04029.html, 2024/ws-02836.html), sha256 verified on Mac, logged in work/library_adds.csv; the other 61 fetched pages already existed (add-only, not overwritten).
## For Sammy / checks
- Role: nb-04029 is a 2017 Jewish Journal op-ed BY Jesse Gabriel (signature line). ws-01786, ws-03651 (and ws-01466 Bauer-Kahan) are San Diego Jewish World reposted press releases whose SDJW byline names Gabriel/Bauer-Kahan — the byline→Op-ed rule would misfire; decide.
- Outlet house bylines (CC News, ECT, VNG, eJP, MMR, TFL, WLJ) recorded as staff, as given.
- Not done (TinyFish paused): CJK reporter-name scan of saved Desktop copies for Chinese/Korean outlets could add a few more persons without fetching.
## Self-check
- Counts above; 40 random rows spot-checked against evidence (2 samples of 20): all bylines match evidence; fixed during review: CC News misclassified as person, "About WordPress"/"La Nacion"/"The Triplicate" not persons, nbsp in names, Korean '대한 기자' false match. One known imperfection: ws-02922 title "Trending News Reporter" not split out (author "Joyann Jeffrey").
