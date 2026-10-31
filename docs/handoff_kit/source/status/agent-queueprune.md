# agent-queueprune — 2026-10-27 (complete)

Task (Sammy): remove everything already dealt with from the review queue https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB. Only db collection `items` written; `decisions` (396 docs) untouched. No Exa, no Mac, no workbook, page not republished.

- Read README/DECISIONS/BOARD, status agent-autodecide, agent-queue-adds, agent-review-multi, agent-reach-ethnic, agent-leginfo, coordinator. No press-release agent status file; no `13-pressrelease` items doc exists in the db. Last decision write 01:14Z; no queue agent active.
- Rule: removed = has a decision doc (Sammy or Claude), or settled by DECISIONS.md. Only the latter case: all 10 `tone` items (full-text tone always wins; their autodecide batch had been denied, so no decision docs exist).
- Archive BEFORE writes: work/out/queue_archive_20261027T043821Z.json — 406 items, each with its decision doc or settled_reason.
- Page check (build/review/index.html): tabs come from items present (catKeys), so missing docs are handled. Deleted the 4 empty docs: 6-duplicate, 8-bills, 10-tone, 11-links.
- One atomic pinned batch (11 writes). Scripts/reads: work/tmp_queueprune/.

| Doc | Before | Removed | Remaining |
|---|---|---|---|
| 1-reach | 241 | 184 | 57 |
| 2-role | 20 | 18 | 2 |
| 3-nogabriel | 35 | 10 | 25 |
| 4-language | 20 | 18 | 2 |
| 5-headline | 11 | 9 | 2 |
| 6-duplicate | 5 | 5 | 0 (doc deleted) |
| 7-copy | 6 | 5 | 1 |
| 8-bills | 64 | 64 | 0 (doc deleted) |
| 9-relabel | 151 | 79 | 72 |
| 10-tone | 10 | 10 | 0 (doc deleted) |
| 11-links | 4 | 4 | 0 (doc deleted) |
| 12-process | 2 | 0 | 2 (paused Exa/TinyFish, untouched) |
| Total | 569 | 406 | 163 |

Self-check: re-read after write — 8 docs, each identical to what was written; 0 remaining items have a decision doc; decisions still 396.

Note for coordinator: tone-009 (jg-04180, "Six-Day War: Voices after victory") said Role may be Op-ed; that hint left the queue with the tone item. Same story is still open as nogab-023 (jg-01710), which conflicts with it.
