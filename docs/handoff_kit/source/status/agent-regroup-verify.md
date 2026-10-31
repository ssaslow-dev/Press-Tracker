# agent-regroup-verify (T31) — status

## Part 3 independent check — DONE
Inputs read: README, DECISIONS, BOARD; workbook "Reprint info" + "Audit plan" tabs (snapshot of work/coverage_current.xlsx copied to tmp_agent-regroup-verify/coverage_snapshot.xlsx at start); sample work/tmp_agent-regroup/part3_sample.csv (only file read from that folder). Did NOT read agent-regroup's scripts, status, summary or regroup_changes.csv.

Method (own, helpers in work/tmp_agent-regroup-verify/):
- Texts: NewsBank work/texts/nb/<aid>.json body; tracker copies from work/artifact_files/articles/<year>.json by the row's Tracker story code (header line, "Text of the ProQuest PDF", "Print edition" removed; page <h1> dropped as NB headlines are not in NB body either); print pages from work/nb_split/<aid>.pdf (both sample print pages are image-only, so no text).
- Tokens: lowercase words, hyphenated words joined (NewsBank drops hyphens: "ultraprocessed", "knowhow"), accents folded.
- Rule: runs of >=25 identical consecutive words must cover >=90% of BOTH texts. NB copyright line flagged as clutter. Site-chrome test (same domain, other unrelated saved pages, >=30-day span) built over all 3,317 tracker copies — it fires almost never (few pages per outlet).
- No text on a side: exact headline (case/punct/quotes ignored) + same people in byline.
- Every pair below 90% with one side high was read by hand; "Report" = true reprint in substance pushed under 90% only by clutter (Reprint info says report such cases to Sammy instead of guessing).

Results (work/out/regroup_part3_check.csv):
- Reprint links (50): 46 agree; 3 Report (nb-02501, nb-00579, nb-00580: NewsBank texts with Sac Bee photo captions / CalMatters promo boxes, strict 87-89.5%); 1 disagree: nb-03902 (Daily Breeze) vs nb-03900 (OC Register) — Register has a 207-word district list the Breeze lacks, 84.5% → own story.
- Splits (50): 34 agree; 3 disagree (should be Reprint): nb-03099/nb-03100 (same Lara release on two PR wires, 93.4/91.1%), nb-00566/nb-00560 (Bakersfield NB text has raw <a href> markup; stripped 97.8/93.1%), nb-01020/nb-01013 (image-only print pages, exact headline + same author; the sample's reprint row nb-04024/nb-04019 is the same case and kept as Reprint); 13 Report (clutter-limited true reprints): 8 already in the low-confidence queue (ws-01245, ws-00628, ws-03163, ws-01027, ws-00316, ws-02396, ws-01259, pq-00008), 5 NOT queued (ws-00363, nb-00119, nb-03600, nb-00760, ws-03006).
- Strict agreement 80/100. Outcome-changing errors not caught by the queue: 1 reprint link + 3 hard splits + 5 unqueued clutter splits = 9/100.

Other findings for coordinator:
- Temp story IDs in part3_sample.csv do not match regroup_queue_items.json (21 of 22 shared rows differ, e.g. ws-01245 jg-NEW-rg-0504 vs 0421; ws-03397's queue id is jg-NEW-rg-0504). ws-00488: sample says split into its own story; queue says "Make ws-00488 the original of jg-00423". The sample appears to come from a different run than the queue — confirm which run is final.
- NewsBank texts DO carry clutter (CalMatters promos, photo captions with .JPG names, "Related Articles" boxes, raw HTML anchors, "Share this" buttons), contrary to the Reprint info assumption. Question for Sammy: allow these specific patterns to be set aside?

## Part 2 queue publish — BLOCKED (needs coordinator/Sammy)
- 14-regroup as one doc is impossible: {"list":[373 items]} = 365 KB; the db limit is 256 KB per document.
- The page loads every doc in `items` (flatMap of .list), so I prepared two docs: work/tmp_agent-regroup-verify/14-regroup.json (items 0-185, 179 KB) and 14-regroup-2.json (186-372, 192 KB). The batch write of these two docs was DENIED by the permission classifier ("Modify Shared Resources"), so NOTHING was written to the db. Existing 9 docs untouched (pre-state saved in tmp_agent-regroup-verify/db_before/).
- To finish: approve the two-doc split (or trim the "detail" field to fit one doc) and run the batch set of both files to collection items of https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB.
- Review page: CATS labels added for regroup ("Reprint regroup"), pressrelease ("Press releases"), authors ("Authors") in build/review/index.html; republished as version 9 (capabilities db carried forward). JS syntax OK; offline load simulation with current docs + the two planned docs renders 10 tabs incl. Press releases 71 and Reprint regroup 373.
