# agent-queuerefresh — 2026-10-27 (complete)

Task (Sammy, "the artifact is outdated"): refresh review queue https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB so it only holds what still needs him. Wrote db `items` only; `decisions` (396) untouched. No Exa, no Mac, no workbook.

Read: README, DECISIONS (all), BOARD, work/final/* (corrections, deletions, error_copies, fills, regroup_exclude, sammy_list.md, sammy_detail.csv), out/author_split_review.json, status/agent-queueprune.md, agent-retry, coordinator.

## Removed (archive: work/out/queue_archive_20261027T094013Z.json)
- lang-003 nb-03075 and lang-007 nb-03485 (Language; Claude has authority per DECISIONS). Neither is in corrections.csv. Both are Sacramento Bee print election-results tables in English; "German" was a language-detector artifact.
  - nb-03075: sheet English → leave as is.
  - nb-03485 (jg-01438): sheet says **Spanish → should be English**. FINAL PASS MUST ADD this correction (not in corrections.csv).
- Doc 4-language was empty afterwards → deleted.

## Kept (not clearly settled)
- 0 items had decision docs. Nogabriel 25: none in deletions/corrections (wrong-Gabriel deletions ws-01876/02294/03814 were never queue items). Reach 57 / relabel 72: no outlet already decided (checked against previous archive + DECISIONS; Guardian relabel-021 kept: 1 of 5 stories may be the London edition). Press releases 71, regroup 209, role 2, headline 2, copy 1, process 2 (Exa vs TinyFish unsettled): kept. No regroup/press-release item touches deleted or error-copy rows.

## Added
- 15-authors: 48 items from author_split_review.json (cat set to "authors"; none only on deleted rows).
- 16-checks: 21 items (cat "checks") from sammy_list.md groups A–S. B and D split into two items each (B1/B2, D1/D2) because each holds two different questions. A reduced to the 2 rows still open (ws-03208, ws-03503); the other A rows were settled by the wrong-Gabriel deletion. T and U are FYI-only (no decision) → not added. Options: keep / fix / skip (decide later), proposed = the consolidator's default.

## Page
- build/review/index.html: CATS `checks: {label:'Data checks'}` added; republished (v10, capabilities db kept).

## Self-check
| Tab | Before | After |
|---|---|---|
| Reach | 57 | 57 |
| Role | 2 | 2 |
| Not about Gabriel? | 25 | 25 |
| Language | 2 | 0 |
| Headlines | 2 | 2 |
| Saved copies | 1 | 1 |
| Reach relabels | 72 | 72 |
| Process choices | 2 | 2 |
| Press releases | 71 | 71 |
| Reprint regroup | 209 | 209 |
| Authors | 0 | 48 |
| Data checks | 0 | 21 |
| Total | 443 | 510 |

Read back: the 2 new docs match what was written; the 9 untouched docs are byte-identical; decisions are identical (396).
Note: the existing 14-regroup doc is 214,577 bytes (over 200 KB; written by agent-queuewrite). Not changed here.
Helpers: work/tmp_agent-queuerefresh/ (build.py, r1 = before, r2 = after, new/).
