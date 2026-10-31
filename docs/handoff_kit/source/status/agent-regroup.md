# agent-regroup (T28): DONE 2026-10-27

Reprint regroup proposals under the stricter 90% rule (Audit plan Part 2), from saved texts only. Not written: the workbook, the Mac, any publish, Exa, or the web.

## Outputs
- work/out/regroup_changes.csv: 2,038 changed rows (old IDs). Columns: old_article_id, current_story_id, current_status, proposed_story_id, proposed_status, similarity, reason, confidence.
- work/out/regroup_summary.md: counts, causes, borderline sample, interpretations, self-check.
- work/out/regroup_queue_items.json: 373 low-confidence items, not published.
  - Item shape: {id: regroup-NNN, cat: "regroup", title, detail, proposed, options, conf, key: old aid}.
  - They go in db doc **"14-regroup"** as {list: [...]}, matching 1-reach … 7-copy.
  - review/index.html's CATS has no `regroup` label yet. Coordinator: add `regroup:{label:'Reprint regroup', note:'…'}` when publishing.
- Helpers in work/tmp_agent-regroup/: load_texts.py, regroup.py, write_outputs.py, selfcheck.py (+ selfcheck.json), part3_sample.csv (50 reprint links + 50 splits for an independent Part 3 agent).

## Option run
Part 2 + 3: Part 2 run fully from saved texts; Part 3 prepared but not run, since it needs a separate agent. FULL and LIGHT both need workbook writes (Part 5 rebuild, Part 4 Change log tab), and Part 1 is a field audit outside this task.

## Counts
| | Count |
|---|---|
| Stories | 4,195 → 4,609 |
| Counted reprints | 2,494 → 2,149 |
| Groups split | 356 |
| Merged | 102 |
| Originals changed | 100 |
| Rows unchanged | 6,034 / 8,072 |
| Rows checked by headline + author for lack of text | 404 (275 with no author) |
| Tracker reprint-list rows → "Reprint (unverified)" | 1,076 |
| Blank-status rows (out of scope) | 1,472 |

## Press releases (coordinator input)
- No release (verdict yes) row is proposed as an Original.
- The 10 release-original stories are marked "release original" (22 rows). jg-01827 and jg-03045 promote the suggested reprint-list row (low confidence).
- 6 release rows fail the rule but are kept as Reprint, because a release can't be an Original. Flagged for Sammy.

## Self-check
- 20 random changes re-measured with an independent method (difflib alignment on re-read texts): 16 exact, 19/20 on the same side of 90%. The differences are explained by chrome flags, and the one flip is already in the queue.
- With the proposals applied, every story has exactly one Original.

## Questions for Sammy
The 8 interpretations listed in regroup_summary.md, chiefly:
- Web + Print originals match either edition.
- Unmerged same-outlet editions are kept together.
- Release rows that fail the rule stay attached as Reprint.
- Trims of more than 10% split under the agreed rule: 104 NewsBank-only cases, 77 of them high confidence.
