# agent-rate-1
Started 2026-10-27T13:55:10Z. Jobs: final_pass/F1/rate_jobs_1.jsonl (156; 8 press releases). Output: final_pass/F1/rate_out_1.jsonl
Done 2026-10-27. 156 lines written: 8 press-release skips, 99 rated (35 tone ratings: 30 Neutral, 4 Positive, 1 Negative; topic on all 99; bills on 30), 45 flag "no text", 4 flag "no Gabriel mention" (jg-04312, jg-01311, jg-01513, jg-01731).
- All 13 NewsBank PDF splits (work/nb_split) are citation pages only (no page image, OCR-confirmed) -> flagged no text with note.
- Bills: session-matched against gabriel_bills_leginfo.json (author + coauthor roles, Dec of even year = next session). Coauthor bills named in roundups included (SB 2, SB 4, AB 421, AB 715, SB 1524, SBX1-3). other_bills empty everywhere.
- no_text jobs rated only when headline makes role clear (1: jg-01823). Topic-only no_text flags carry topic_suggestion (jg-04468, jg-04515, jg-04535 = Food safety). jg-03457 is an SF Chronicle bill-tracker page (removal class per DECISIONS).
- Self-check: 10 random rated lines re-checked against text; no changes.
Scratch: scratchpad/rate1/ (all.txt, compact.txt, r1.tsv, write.py).
