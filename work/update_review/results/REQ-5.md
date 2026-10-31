# REQ-5 Search plan of one Update run (measurement, no patch)

Ran: built page `L/work/build_last/pipe_index.html` already existed (not rebuilt). All tracker code lives inside one IIFE, so the harness
needs a scratch copy with `window.__E=function(c){return eval(c)}` inserted after `initClips();\n})();` (copy at `REQ-5/page_exposed.html`;
nothing in L/code or L/build touched). Harness `REQ-5/run.js` (fake `window.claude`: use('db') returns empty collections, others throw):
`cd results/REQ-5 && NODE_PATH=/opt/npm-tools/node_modules node run.js $PWD/page_exposed.html` -> `REQ-5/out.json`. No page errors.
Caveat: with the empty fake db `LOG.runs` is empty, so `sinceDefault()` falls back to `LAST` = 2026-10-27; in Sammy's real browser it is (last `searched_to` - 7 days).

## Results (expression exactly as specified)
default (since 2026-10-27): {"since":"2026-10-27","total":702,"dropped":0,"by":{"core":14,"outlets":3,"outlets deep":614,"bill":6,"reprint":5,"fresh":51,"youtube":5,"sister":4},"hosts":593,"active24m":421,"TF_GAP":2100,"D":3667}
7 days ago (2026-10-23): total 703, dropped 0, by {core 14, outlets 3, outlets deep 614, bill 6, reprint 6, fresh 51, youtube 5, sister 4}
60 days ago (2026-08-31): total 731, dropped 0, by {core 14, outlets 3, outlets deep 614, bill 6, reprint 33, reprint deep 1, fresh 51, youtube 5, sister 4}
(hosts 593, active24m 421, D 3667 in all three.)

## Versus expected
Total 702-731: at the bottom of the 700-900 range. Outlets deep 614 (expected ~650), fresh 51 (~40), reprint 5-33 (<=60). Only the reprint count moves with `since`
(RC_LATE_DAYS look-back of headlines); everything else is fixed by the outlet list.

## Minimum run time
total x TF_GAP / 1000 / 60: 702 x 2.1 s = 24.6 min (default); 703 -> 24.6 min; 731 -> 25.6 min.
Agree it is serialised: `tfCall` (41 lines 9-19) reserves its slot synchronously (`wait = tfLast + TF_GAP - now; tfLast = max(now, tfLast + TF_GAP)`) before any await, so two
workers (`Promise.all([worker(), worker()])`, lines 689/699) still start TinyFish calls >= 2.1 s apart; the second worker only overlaps latency, not the rate. The retry path
(line 16-17) takes a second slot. Page fetches (line 726 etc.) share the same gate, so they add to the time on top: each batch of 10 candidate pages costs one 2.1 s slot.
So 25 min is a floor for the search phase only; plus retries/fetch batches.

## Deep paging
614 items are `deep` (all outlets-deep; +1 reprint deep at 60 days). A deep item pages on while a page returns >= 10 results and page < 9 (lines 683-685), i.e. up to 9 extra pages each:
worst case 614 x 9 = 5,526 extra searches = 193 min more (total ~6,240 calls, ~3.6 h). Realistic: only outlets where he has >= 10 results continue (big outlets); the rest stop after page 1.
Non-deep items page to at most 4 extra pages while >= 8 results and >= 50% new (the 51 fresh + others, bound 5 x ~88 = 440 more calls worst case).
Hard upper bound if every item paged to the limit is therefore far above the page's "about N" figure; the true count is unknowable without a trace of per-outlet result counts.
