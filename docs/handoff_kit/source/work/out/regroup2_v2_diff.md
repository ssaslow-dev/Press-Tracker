# regroup2 v2 vs v1 (one new deterministic run; proposals only)

## What changed in the method (coordinator items 1–6)
1. **Stability:** after the seeding pass, a row that passes against its own old Original, which is still an Original, goes back to it. This reverts the 7 strict-pass splits: ws-00360 and nb-03281/03288/03290 by reassignment; ws-00579, ws-00060 and ws-02989 by item 3.
2. **Edge set-aside:** now applies to every text (NewsBank too), not only saved web copies. In the verifier's list of 51 edge near-miss splits, any row that still splits is marked low confidence and queued. Rows that now pass with edges set aside are kept as low-confidence Reprints and queued.
3. **Photo captions:** `<figcaption>` text in saved web copies is flagged like NewsBank clutter (counts when matched, ignored when not). A pass that needs only that is medium confidence. This fixes the ABC News, Washington Times and Korea Times/Yonhap splits.
4. **NewsBank first per row:** a copy mapped only through a tracker story code (html_clean/<year>/jg-xxxxxx.html) is used for a row with a NewsBank text only if it is the same text; a row's own aid-named copy is always kept. 5 copies were dropped this way: nb-01048 (html:2025/jg-d48cd8.html), nb-01175 (html:2024/jg-7355fd.html), nb-02319 (html:2023/jg-9bb4b4.html), nb-00137 (html:2026/jg-a3f86a.html), nb-04014 (html:2017/jg-4d7eb5.html). That fixes jg-00908: the long AP version (Westerly nb-02294, CBS, KCRA, NBC LA, Fox) now sits with the long AP text nb-02320. The merged story keeps jg-00896, and the short State Wire nb-02319 keeps jg-00908.
5. **Same-outlet editions:** web/print (incl. ProQuest) rows are no longer kept together automatically when the text fails. They are queued as "merge as Web + Print or own story". nb-01765 stays in jg-00730 with Daily Breeze nb-01762. pq-00115 is forced "not the same" as ws-02277 per the verifier and stays Original of jg-02638. Note: this run measures 87.6/95.3 on html_clean/2025/pq-00115.html, against the verifier's 31.6/36.7, so the two read different texts; the existing v1 queue item for pq-00115 should be decided as "Own story".
6. **Originals:**
   - A byline naming the row's own outlet (sheet byline or NewsBank author field) is tier 2 even for "mostly reprints" outlets, so Fresno Bee nb-03194 stays Original of jg-01285.
   - Aggregators now rank after press releases, so PR Newswire nb-01008 stays Original of jg-00418.
   - ws-00665 vs nb-01647 is queued for Sammy.
7. **CalMatters web chrome:** "Lea esta historia en español", "Read this story in English", the "Become a CalMatters member" box, the sign-up/subscribe boxes and "Learn more about legislators" are now flagged in NewsBank texts. Every strip is logged in work/tmp_agent-regroup2/strips_log_v2.csv.

## Counts
- Rows changed: v1 1681 (high 1490 / medium 132 / low 59) → v2 1623 (high 1420 / medium 115 / low 88).
- v2 by kind: 6417 unchanged, 115 demoted, 114 original_changed, 649 unverified, 442 split, 253 regrouped, 50 merge. Stories after: 4563.
- Real differences v1 → v2 (temp-ID renumbering ignored): 185 rows — 87 v1 change dropped (row stays as in the sheet); 50 different proposal; 29 new change in v2; 19 confidence only. Full list: out/regroup2_v2_vs_v1.csv.
- Kept only with set-aside: v1 149 → v2 156 rows (out/regroup2_v2_kept_lowconf.csv).
- v1 queue items whose row now has a different proposal: 30. These are listed in out/regroup2_v2_vs_v1.csv; agent-decide-regroup should use the v2 proposal for them: nb-00541, nb-00568, nb-00569, nb-01004, nb-01008, ws-00487, nb-01035, nb-01036, nb-01038, nb-01039, nb-01042, nb-01043, nb-01044, ws-00489, nb-01050, nb-01090, nb-01550, nb-01765, nb-01773, nb-01795, nb-01863, ws-00840, ws-00853, ws-00858, ws-00859, nb-02567, nb-02694, nb-02955, ws-01124, pq-00115.
- New queue items (rows not already in 14-regroup/14-regroup-2): 134 in out/regroup2_v2_new_items.json (138 KB), ids regroup2-0210…regroup2-0343.
- Verifier flags already resolved by v2 (no queue item needed): 1 — ws-00853 now Reprint of jg-00896 (Original nb-02320).

## Self-check (v2)
I re-measured 40 random v2 changes that have text on both sides (21 passing, 19 failing) with a second method, difflib matching blocks (only blocks of 25 or more words count). Pass/fail agrees on 39 of 40. The one disagreement is ws-00858 (KCRA) vs nb-02320: 92.2% by the main method, 85.4% by difflib, because of repeated or reordered text. That row is already low confidence and in the new queue items. Details: work/tmp_agent-regroup2/selfcheck_v2.csv. Rerunning v2 gives byte-identical outputs.
