# agent-regroup-final — 2026-10-27

This is the final regroup plan for the final pass. It is not applied yet: Sammy must approve it first. No workbook, Mac or publish writes were made, and Exa was not used.

Helpers are in work/tmp_agent-regroup-final/:
- load.py, m.py: the v2 measure functions, reused without re-clustering.
- build.py, check.py, write.py: the build, the checks and the output files.
- corrections_map.json, overrides.json, extra_notes.json: the hand-settled cases.
- q/: a snapshot of the queue taken before my writes.

## Inputs
- Base: work/tmp_agent-regroup2/snap.xlsx (= coverage_current.xlsx, sha e1c70819…).
- out/regroup2_v2_changes.csv, regroup2_v2_kept_lowconf.csv and run_state_v2.pkl (the v2 cluster membership).
- Queue items 14-regroup, 14-regroup-2 and 14-regroup-3: 343 items. Decisions: 324, all by "Claude (auto)". Sammy has made no regroup decisions.
- Rows in final/deletions.csv and the 3 wrong-Gabriel rows are left out.

## Outputs
- work/final/regroup_final.csv: 1,855 rows. Columns: old_aid, current_sid, current_status, final_sid, final_status, basis, note.
  - 1,609 rows actually change. The rest are queue or override rows that keep their current values; they are listed for traceability.
- work/final/regroup_open.csv: the 19 undecided items. They keep their current grouping. The file gives the v2 proposal and a recommendation for each.
- work/final/corrections.csv: added ws-00485, Press release = Yes.
- Temp story IDs jg-NEW-0001…0424 are numbered in sheet order of each story's first row. The v2 temp ID is kept in the note wherever it differs.

## Conflicts settled (read texts; v2 measure)
**pq-00115.** Both agents read the same file, html_clean/2025/pq-00115.html. It is a ProQuest PDF layout where line-break hyphens are followed by blank lines ("Cali-\n\n\nfornia"). The verifier's tokenizer joins only "-\n", so the words split and the 25-word runs broke. That is where its 31.6/36.7 comes from.
- With the hyphens joined, the verifier's own code gives 87.4/95.3 raw and 99.2/99.0 with edges. v2 gets 87.6/95.3.
- The text is the LA Times print edition of ws-02277.
- **Override of v2:** pq-00115 becomes a Reprint in jg-02639 (decision 0048 stands). It is a Web + Print merge candidate.

Auto-decisions that were wrong, corrected in the queue (choice and note updated, note says "Corrected after v2/reconcile"):
- **0007, 0008 (Glock):** stay in jg-00238 under USA TODAY nb-00571 (97/97 with edges). Desert Sun ws-00353 fails against nb-00571, so following it would be chaining.
- **0030 ws-00840:** stays in jg-00872. It is the same AP roundup as ws-00838 with an updated top. The earlier choice named a v1 story that no longer exists. v2's split is overridden. (The decision agent's own status note also proposed this.)
- **0032, 0122, 0123:** go with the long AP text nb-02320 in jg-00896, as v2 has them (92–99 against it, about 61 against nb-02319).
- **0045 ws-01196:** goes with Times of Israel ws-01195, as in v2. The decided partner nb-03611 sits under nb-03610, which ws-01196 fails, so that choice was chaining.
- **0098 nb-01050:** own story, as in v2. NewsBank texts compare at 62.8/75.0. The 99.6/90 figure came from html/2025/nb-01048.html, which is Spectrum News' later AP version. That file is the wrong copy for nb-01048.

Auto-decisions kept over v2:
- **0014 nb-01036 (CALO):** stays a Reprint in jg-00427. Borderline: 94.9/91.4 against ws-01285 with edges. Against nb-01037 it is 87.0, and about 90 once the unflagged WeeklyMatters box is set aside.
- **0095, 0106, 0119:** same-outlet print editions. Under the edition rule they are not subject to the 90% rule, so they stay together. Each is a Web + Print merge candidate.

Story-ID label only (0013, 0015–0020 → jg-00427; 0041 → jg-01353): grouping unchanged. A note was added to each decision.

## Originals (task 2), all verified in the saved texts
- **jg-03533:** Nur.kz ws-03213 becomes the Original. Crispy News ends with "Источник: nur.kz". Decision 0202 updated.
- **jg-03672:** The Hill ws-03353 becomes the Original. KTLA's byline reads "The Hill via Nexstar Media Wire", and The Hill posted first. Decision 0204 updated.
- **jg-03890:** LA Times pq-00289 becomes the Original. Governing credits "Los Angeles Times (TNS)". Governing and Yahoo both pass against pq-00289. Decision 0206 updated.
- **jg-00423:** Asbarez ws-00487 (01-23) becomes the Original. Every row is a release, including the Mirror-Spectator (pr-006), so date decides. This overrides v2's Mirror-Spectator pick. Decision 0012 updated; note added to 0219.
- **jg-01125:** Lassen County Times nb-02924 stays the Original. It is dated 12-06; the Contra Costa News copy is 12-08, and both are releases. This overrides v2's medium-confidence change.
- **Extra, found by the check:** in jg-01093, Desert Review ws-01003 (not a release, pr-026) replaces the Lassen County Times release nb-02872 (pr-025) as the Original. Decision 0153 updated.

## Checks
- Every story has exactly one Original (4,545 stories).
- 8,040 rows; none is in two stories.
- No deleted row is an Original.
- No error-copy row (not retried successfully) is an Original where another row could be.
- No release row is an Original of a story that has a non-release row.
- 4 two-row stories have a tracker reprint-list row as Original: jg-NEW for ws-00016, ws-00390, ws-00494 and ws-00987. Each was split by headline + author, which is legitimate under v2 at high confidence. These are noted only.

Counts:
- Stories: 4,163 before, 4,545 after.
- Rows changed: 1,609 in all.
  - v2-high: 1,416
  - v2-medium: 108
  - Queue, Claude (auto): 72
  - Queue, corrected: 4
  - Override: 9
- By status: 649 Reprint → Reprint (unverified); 543 → Original; 161 Original → Reprint; 256 Reprint moved.

## T44: re-check of fetched reprint-list rows, and Sammy's approvals baked in (2026-10-27)
- Copies of the previous outputs:
  - final/regroup_final.v1_20261027T1012.csv
  - final/regroup_open.v1_20261027T1012.csv
  - tmp_agent-regroup-final/fills.before_T44.csv
- The 19 open items now follow my recommendations. Their basis reads "queue:<id> by Sammy (approved agent recommendation)". regroup_open.csv is now empty, with headers only.
- Delta run: delta.py (inside write.py) and deltaq.py.
  - All 419 rows with result=saved were re-checked by text.
  - Each row's own cleaned copy is read from html_clean/<year>/<aid>.html. Its leading "Saved YYYY-MM-DD (TinyFish reprint fetch)" header is set aside (an allowed tracker header); this was stripped in 410 files.
  - The error-copy web file html/2025/nb-01048.html is dropped from the texts.
  - Each row is tested against its story's Original first, then against the Originals of the stories holding its sheet siblings. The test is v2's own test(), with the same edge-line and clutter rules.
  - The run repeats until nothing changes (3 passes), so chained joins are re-checked.
- Rows I sent to the queue instead of applying, even when the rule's confidence was medium or high, to avoid false splits:
  - the fetched copy contains the whole Original (Original side covered at least 98%);
  - the Original's saved copy is a stub (under 150 words).
- In stories created by the delta run, the Original is re-picked by the originals order: ws-00675 replaces ws-00674.

Transitions from the pre-delta plan (419 rows):

| Before | After | Rows |
|---|---|---|
| Reprint | Reprint, same story (verified) | 275 |
| Reprint (unverified) | Reprint, same story | 30 |
| Original of a split story | Reprint, back in another story | 37 |
| Original | stays Original | 35 |
| Reprint | Reprint, moved to another story | 6 |
| Reprint | Original of a new story | 15 |
| Reprint | Reprint in a new story | 2 |
| Reprint (unverified) | Original of a new story | 5 |
| Reprint (unverified) | unchanged | 14 |

Of the 14 unchanged unverified rows, 10 have an Original with no text; the rest are in the queue.

- Queue: 103 low-confidence items, regroup2-0344…0446. Written to out/regroup_delta_queue_items.json and to the items doc "14-regroup-4" (read back, identical).

| Kind | Items |
|---|---|
| pass-low | 52 |
| join-low | 23 |
| fail, Original contained | 19 |
| fail, Original stub | 5 |
| Original with followers passes another story | 4 |

- Plan totals: stories 4,163 → 4,530. regroup_final.csv has 2,091 rows.
- Checks: every story has exactly one Original; no row is in two stories. The only flags are 6 stories whose Original is a reprint-list row that now has text, which is fine.
- fills.csv: 32 Author / byline fills added for blank cells (source "reprint-fetch"). Now 1,549 rows.
