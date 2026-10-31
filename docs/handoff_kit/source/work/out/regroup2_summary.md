# Reprint regroup by long text streaks (T33, agent-regroup2) — PROPOSALS ONLY

Run: one deterministic run, 2026-10-27; workbook snapshot sha256 e1c70819…07f1 (= work/coverage_current.xlsx). Nothing written to the workbook, Mac, tracker or queue.
Rule: runs of >=25 identical consecutive words (CJK: >=40 characters) must cover >=90% of BOTH texts; no usable text (<50 words) on either side → exact headline + same author. Every row tested against the Original itself (no chaining). Originals picked by the Reprint info order.

## Counts
- Rows in scope: 8040 (Coverage rows with a Story ID, minus 32 rows on the final-pass deletion list incl. ws-01876, ws-02294, ws-03814). The 1,471 NewsBank print pages with no Story ID are out of scope.
- Stories: 4163 before → 4624 after. Reprint rows: 3877 before (incl. the reprint-list rows) → 2767 after (+ 649 "Reprint (unverified)" reprint-list rows, not counted). Single-row stories: 3099 → 3569.
- Rows changed: 1681 (confidence: high 1490, medium 132, low 59). Rows unchanged: 6359.
- Splits: 501 rows leave their story (356 old stories split). Of these, 118 head a new multi-row story; their followers: 263 rows move with them.
- Merges: 58 rows join another story (43 merged stories; 43 near-duplicate group sets passed a cross-group test; 13000 candidate row pairs tested (dates within 3 days, >=3 shared headline words)).
- Originals changed: 105 stories get a new Original (105 old Originals become Reprints, incl. merges). By reason: 59 originals-order tier; 29 earlier date; 12 web over print; 5 eligibility.
- Renumbered only: 0. Reprint-list label changes (Reprint → Reprint (unverified)): 649.
- Unchecked for no text: 1514 rows have no usable text (6526 do). Outcome of those: 649 kept attached, unverified (reprint-list); 419 Reprint by exact headline + same author; 285 single-row story (Original, nothing to compare); 115 split: headline+author do not both match; 31 split: headline or author missing (cannot verify); 15 Original of a multi-row story.
- Low-confidence (queue): 209 items = 59 low-confidence changes + 149 rows kept in their story only with clutter set aside + 1 Original question (jg-00334). Files: out/regroup2_queue_items.json (178 items, 199 KB) and out/regroup2_queue_items-2.json (31 items, 44 KB). Not published.
- Kept-but-low list: out/regroup2_kept_lowconf.csv (149 rows: 126 text-edge, 14 text-clutter, 9 edition).

## The 1,076 tracker reprint-list rows
- 649: Reprint (unverified): no text, no headline+author; kept attached, not counted
- 335: Reprint, verified by exact headline + same author
- 78: own story: headline+author present but do not match
- 13: Reprint, verified by text (>=90% rule)
- 1: own story: text fails the rule
- Unverified rows stay attached to the story holding their tracker story code (else the old Original's story); never used as Originals.

## Stories whose Original is a press release (10, press_release_originals.csv)
Release rows (verdict yes, and these 10 listed Originals incl. borderline) are never picked as Original while a non-release row passes the rule against them.
- jg-00248 (release Original nb-00614, Targeted News Service, verdict yes): jg-NEW-0055: Original ws-00358 (KRCR), 1 row(s); jg-00248: Original nb-00614 (Targeted News Service) [release], 1 row(s)
- jg-00672 (release Original nb-01647, California Courier, The, verdict yes): jg-00672: Original ws-00665 (Armenian Mirror-Spectator, The), 2 row(s) — was Original; now Reprint of ws-00665 (Armenian Mirror-Spectator, The) [passes only with leading/trailing web-copy lines set aside: raw 97.3/82.9, set aside 97.
- jg-00690 (release Original nb-01681, US Fed News, verdict yes): jg-NEW-0186: Original ws-00686 (Beverly Press), 1 row(s); jg-00690: Original ws-00683 (Contra Costa News) [release], 4 row(s) — was Original; now Reprint of ws-00683 (Contra Costa News)
- jg-00873 (release Original nb-02203, Targeted News Service, verdict yes): jg-NEW-0236: Original ws-00844 (FOX 11 Los Angeles), 1 row(s); jg-00873: Original nb-02203 (Targeted News Service) [release], 1 row(s)
- jg-01030 (release Original nb-02697, CE Think Tank Newswire: English, verdict borderline): jg-01030: Original ws-00944 (Pacific Research Institute), 2 row(s) — was Original; now Reprint of ws-00944 (Pacific Research Institute)
- jg-01037 (release Original nb-02706, Chemicals Monitor Worldwide, verdict borderline): jg-01037: Original ws-00946 (Baking Business), 2 row(s); jg-NEW-0286: Original ws-00947 (Food Business News), 1 row(s) — was Original; now Reprint of ws-00946 (Baking Business)
- jg-01266 (release Original nb-03171, California Courier, The, verdict borderline): jg-NEW-0346: Original ws-01094 (Armenian Weekly, The), 1 row(s); jg-01266: Original nb-03171 (California Courier, The) [release], 1 row(s)
- jg-01514 (release Original nb-03621, Targeted News Service, verdict yes): jg-NEW-0403: Original ws-01199 (Patch), 1 row(s); jg-01514: Original nb-03621 (Targeted News Service) [release], 1 row(s)
- jg-01827 (release Original ws-01338, Encino Enterprise, verdict borderline): jg-01827: Original ws-01338 (Encino Enterprise) [release], 3 row(s)
- jg-03045 (release Original ws-02714, Encino Enterprise, verdict borderline): jg-03045: Original ws-02714 (Encino Enterprise) [release], 2 row(s)

## jg-00334 (Excelsior) and jg-01584 (Sac Bee)
jg-00334:
  - jg-00334: Original nb-00792 (Excelsior: Orange County Register weekly, 2025-06-22), 14 rows
    - nb-00792 Excelsior: Orange County Register weekly (-) — unchanged (Original)
    - nb-00793 Daily Breeze (Print) — unchanged (Reprint)
    - nb-00794 Inland Valley Daily Bulletin (Print) — unchanged (Reprint)
    - nb-00795 Long Beach Press-Telegram (Print) — unchanged (Reprint)
    - nb-00796 Los Angeles Daily News (Print) — unchanged (Reprint)
    - nb-00798 Pasadena Star-News (Web + Print) — unchanged (Reprint)
    - nb-00799 Redlands Daily Facts (Print) — unchanged (Reprint)
    - nb-00800 San Gabriel Valley Tribune (Print) — unchanged (Reprint)
    - nb-00801 Monterey County Herald, The (Print) — unchanged (Reprint)
    - nb-00803 Orange County Register, The (Web + Print) — unchanged (Reprint)
    - nb-00804 Press-Enterprise, The (Print) — unchanged (Reprint)
    - nb-00805 Sun, The (Print) — unchanged (Reprint)
    - nb-00806 Whittier Daily News (Print) — unchanged (Reprint)
    - ws-00429 Canyon Crest Guide (Web) — unchanged (Reprint)
  - Note: Original kept by the order rule (tie); queued as a question (Register as source?). Board names for the author split follow whatever Original is approved.
jg-01584:
  - jg-01584: Original nb-03806 (Orange County Register, The, 2019-04-12), 10 rows
    - nb-03806 Orange County Register, The (Web + Print) — unchanged (Original)
    - nb-03800 Daily Breeze (Print) — unchanged (Reprint)
    - nb-03801 Inland Valley Daily Bulletin (Print) — unchanged (Reprint)
    - nb-03802 Long Beach Press-Telegram (Print) — unchanged (Reprint)
    - nb-03803 Los Angeles Daily News (Print) — unchanged (Reprint)
    - nb-03804 Pasadena Star-News (Web) — unchanged (Reprint)
    - nb-03805 Redlands Daily Facts (Print) — unchanged (Reprint)
    - nb-03807 Press-Enterprise, The (Print) — unchanged (Reprint)
    - nb-03808 Sun, The (Print) — unchanged (Reprint)
    - nb-03809 Sacramento Bee, The (Print) — unchanged (Reprint)
  - jg-NEW-0420: Original nb-03810 (Daily Democrat, The, 2019-04-17), 1 rows
    - nb-03810 Daily Democrat, The (Print) — Original: split: vs old Original nb-03806 runs>=25 cover 80.2% / 93.8% (<90%) (80.2/93.8%)
  - The Sacramento Bee print row (nb-03809) passes against the Register editorial — a true reprint; board name stays "The Orange County Register Editorial Board". The Daily Democrat row is a >10% trim and becomes its own story.

## Method notes
- Texts: cleaned saved copies (work/html_clean, header lines "Saved …", page title/h1, "Text of the ProQuest PDF", "Print edition" dropped), NewsBank texts (work/texts/nb), print-article PDFs of Web + Print rows (work/nb_split, NewsBank header/copyright/citation removed). A row with several versions uses the best-matching pair. Error-copy files (final/error_copies.csv) are not used as text; deletion rows are skipped.
- Normalization: NFKC, accents folded, lowercase, hyphenated words joined (incl. "D- Encino"), in-word apostrophes/periods/commas removed, CJK one token per character.
- NewsBank clutter: only the allowed patterns were flagged (log: work/tmp_agent-regroup2/strips_log.csv, every strip). Flagged text counts when the other text has it and is ignored only when unmatched. Pairs that pass only this way → low confidence with the text quoted.
- Saved web copies: leftover leading/trailing lines (dek, photo credit, byline/date lines, tag lists, "read next") that the HTML cleaning kept can push a true reprint under 90%. Unmatched leading/trailing spans of a saved web copy (each <=120 words, CJK <=400 chars, together <=30% of the text) were set aside the same way → always low confidence and queued (Reprint info: report such cases rather than guess).
- Same-outlet web vs print rows (separate rows, dates within 3 days) that fail the rule but share >=50% are kept together as editions → low confidence.
- Originals order tiers: 1 wire list; 2 person byline; 3 no byline; 4 byline credits another outlet, or outlet with >=80% Reprint rows (n>=5) in the current sheet; 5 aggregators/syndicators. Then earlier date (Korean outlets −1 day), NewsBank over tracker, web over print, current Original. Releases, error-copy rows and reprint-list rows are picked last. Tier 2/3/4 calls are heuristics → those Original changes are medium confidence.
- Story IDs: a story keeps the old Story ID of the old Original it contains (the new Original's own old ID first); stories with no old Original get temp IDs jg-NEW-NNNN in sheet order.

## Self-check (second implementation, difflib matching blocks)
40 random changes that have text on both sides (seed 20261027; 18 passing, 22 failing pairs; proposed statuses {'Reprint': 18, 'Original': 22}) re-measured with difflib.SequenceMatcher matching blocks (autojunk off, blocks >= 25 words / 40 CJK chars, one-to-one alignment) on the same best version pair. Pass/fail agreement 40/40. Coverage numbers agree within 2 points on 37/40; the 3 larger gaps (pq-00021 vs nb-01148, ws-02009 vs pq-00105, nb-02235 vs nb-02234; up to 11.6 points) are reordered paragraphs that difflib's one-to-one alignment does not count — all three fail under both methods. Details: work/tmp_agent-regroup2/selfcheck.csv. Limitation: both methods share the normalization and text extraction; the queue items are where human review is needed.
