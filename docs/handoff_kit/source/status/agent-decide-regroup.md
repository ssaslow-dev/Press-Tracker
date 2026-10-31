# agent-decide-regroup — 2026-10-27

Tabs: 14-regroup + 14-regroup-2 (209 items, regroup2-0001…0209) and, per coordinator update, new tab 14-regroup-3 (134 items, regroup2-0210…0343).
Method: my own text loader + matcher (work/tmp_agent-decide-regroup/rg.py, run.py, run3.py). For each item I computed coverage by shared 25-word runs (order-free) between the row and the proposed partner and the current Original. Then I read every unmatched segment and judged it under the DECISIONS rule: edge lines of up to 120 words at each end may be set aside (Sammy's OK); NewsBank clutter patterns may also be set aside. run3 (used for tab -3) uses NewsBank text first: tracker jg-xxxxxx copies are dropped for rows that have NewsBank text.
Did not read agent-regroup2-verify files.

## Writes
- decisions: 202 (tabs 1–2) + 122 (tab 3) = 324 docs, all create-only (no existing regroup2 docs), by "Claude (auto)". 7 batches committed.
- items: created NEW doc "14-regroup-3" from out/regroup2_v2_new_items.json (138 KB source, 152 KB stored). Read back: identical, 134 items. No other items docs touched.
- CSVs: work/out/decided_14-regroup.csv, decided_14-regroup-2.csv, decided_14-regroup-3.csv.

## Counts
| Tab | Items | Decided | Left for Sammy |
|---|---|---|---|
| 14-regroup + -2 | 209 | 202 | 7 |
| 14-regroup-3 | 134 | 122 | 12 |
| Total | 343 | 324 | 19 |

## Left for Sammy
- 0022 nb-01218, 0111 nb-01773, 0117 nb-01795, 0130 nb-02567, 0155 nb-02955: no option fits. Each print page is 100/100 identical to its SCNG sister pages (Daily Breeze / LA Daily News etc.). v2 now proposes exactly that grouping (jg-NEW-0170/0172/0242/0280), but the v1 items don't offer it. Recommendation: follow v2.
- 0082 nb-00541: the web item is a multi-item newsletter; the print copy is its first item. Two rules collide here: the edition exemption and the rule that a newsletter containing the article fails. Recommendation: Own story. v2 agrees.
- 0100 nb-01090: the print piece is rewritten and expanded (39/66). v2 splits it.
- 0330–0341 (12 no-text print pages): headline is not an exact match, so the written rule gives Own story. The independent check judged them the same piece by eye.

## Conflicts with v2 (decisions written before v2 arrived; NOT overwritten)
- v2 is right; my decision is wrong:
  - 0098 nb-01050: I read the tracker html copy. The NewsBank text vs nb-01048 is 62.8/75, so this should be Own story.
  - 0032 ws-00853, 0122 ws-00858, 0123 ws-00859: these belong with the long AP version nb-02320 in jg-00896, not with nb-02319 in jg-00908. (Tab-3 items 0231/0232 decided per v2.)
  - 0030 ws-00840: ws-00838 stays in jg-00872. ws-00840 passes vs nb-02201 (92.8/100 with edges), so the right answer is Leave as now (Reprint, jg-00872), not v2's split.
- Story ID only (same rows end up together):
  - 0013, 0015–0020: v2 keeps the CalMatters group in jg-00427 and merges ws-01285 into it (I decided 0249 that way). My decisions name jg-01782.
  - 0041 ws-01124: v2 keeps jg-01353. It passes 100/100 with edges.
- Substantive, and I disagree with v2:
  - 0014 nb-01036 (CALO): passes 94.9/91.4 vs both nb-01037 and ws-01285 with edges and NB clutter set aside. v2 splits it.
  - 0048 pq-00115: the coordinator says Own story. My text check: 86.9/93.5 raw, 99.2/99.0 with edges vs ws-02277 (LA Times print vs web, same author). The verifier must have read different text. Sammy should look.
  - 0007/0008 Glock (nb-00568/569): they pass vs both nb-00571 (97/97 adj) and ws-00353 (98/95 adj). v2 keeps them in jg-00238 and splits ws-00353 out.
  - 0095 nb-01004, 0106 nb-01550, 0119 nb-01863: I kept them under the edition exemption. v2 queues them as "merge as Web + Print or own story". The v1 options had no merge choice.
- Agree with v2: 0011, 0012, 0025, 0035.

## Other notes
- jg-00334 (0209): decided nb-00803 (OC Register) as Original. Every SCNG copy, including ocregister.com and excelsiorcalifornia.com, is stamped "June 22, 2025 at 8:00 a.m." by The Editorial Board. The board is the Register's.
- Original picks the regroup didn't change but should be looked at:
  - 0202: Crispy News cites "Источник: nur.kz", so Nur.kz should be the Original.
  - 0204: KTLA credits "The Hill via Nexstar", so The Hill should be the Original.
  - 0206: Governing carries LA Times via TCA.
  - 0012: Asbarez (01-23) predates the Courier (01-24).
  - 0011: Yahoo ws-00485 is the same paid release and should be marked Press release = Yes.

## Batch 4: items doc 14-regroup-4 (103 items, regroup2-0344…0446)
Method: same matcher (run4.py), NewsBank text first. Each row's fetched copy is html_clean/<year>/<aid>.html.
Decided 98, left 5. All 98 decision docs were create-only, by "Claude (auto)". CSV: work/out/decided_14-regroup-4.csv.
- 0346, 0349, 0357, 0373, 0396, 0418, 0422, 0440 ("fail, Original contained"): the article part passes. The leftover text is page chrome (Forward donate boxes, JTA bios, Yahoo summary bullets and captions, LAist "more news" lists). Decided as reprints.
- 0345, 0359, 0366, 0388 (Original with followers passes another story): text is 100/100 vs the other Original. Chose "Reprint of … (its followers re-checked)", not the proposed "Leave as now".
- Other calls:
  - 0434 is Own story: the RetailWire stub has a different byline and shares no text.
  - 0425 keeps "Reprint (unverified)": the 124-word stub appears verbatim inside the Epoch Times text.
  - 0412 keeps: the saved Politico copy appears to start mid-article.
  - 0375 is a reprint: the Asian Journal extras are an ad supplement.
- Left for Sammy:
  - 0360: an extra 78-word article paragraph, 89.2/100.
  - 0410: the NewsBreak copy adds about 600 words of real Playbook items, not page chrome.
  - 0426, 0427, 0428: the Original is an 86-word Observer link card. The fetched copies are the CalMatters Koseff story, which matches nb-01494 in jg-00611: 0426 94.6/100, 0428 98.5/97.8, KQED 0427 91.6/83.4. Neither option fits; recommend moving them to jg-00611 (KQED possibly its own story).
