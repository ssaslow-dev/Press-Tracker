# agent-regroup-queue (2026-10-28) — REPRINT-v2 regroup into the review queue

Owns: review-queue db (https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB) items/23-* and the reconcile decision docs listed below; work/tmp_regroup_queue/.
Source: work/tmp_reprint_code/regroup_plan.csv (master e97fef6c = work/coverage_current.xlsx, sha e97fef6c). Builder: work/tmp_regroup_queue/build.py → new/*.json. Nothing written to the sheet.

## Items written (one atomic batch, create-only; read-back equal)
Item shape as before: {cat, conf, id, key "story:aid", title, detail, options ["Apply","Skip"], proposed}. Every detail ends "Different call? Pick Skip and write the call in the note."

| Doc | cat | n | high | medium | low |
|---|---|---|---|---|---|
| 23-merge, 23-merge-2 | merge | 198 | 42 | 143 | 13 |
| 23-edition | edition | 30 | 16 | 13 | 1 |
| 23-translation | translation | 55 | 52 | 3 | 0 |
| 23-swap | swap (51 + date 6 + lateral 5) | 62 | 34 | 22 | 6 |
| 23-split | split (22 + AV 2) | 24 | 3 | 20 | 1 |
| 23-verify | verify | 33 | 31 | 2 | 0 |
| 23-addorig | addorig (no-copy blocked) | 50 | 11 | 9 | 30 |
| total | | 452 | 189 | 212 | 51 |

Ids rv2<cat>-NNN (unique across the db). Left out: edition-fold, feed-duplicate, kept-*, release-pair, language-check, fetch-type originator adds (248), originator-unknown (96).

Confidence rules
- merge / edition: high = text rule passes at high confidence (raw ≥ 90% both) + same reporter (plan high). medium = edge pass or containment, same reporter. low = containment only and > 7 days apart (or no date).
- translation: high = same byline, ≤ 2 d, translated headline ≥ 0.9 (all 52); else medium.
- swap: high = credited originating service, "byline credits another outlet", or reporter's employer; medium = type-only order ("originating-type outlet over own byline") or aggregator Original; lateral = medium; date-only = low.
- split: AV and wire-wire = high (rules); text fail = medium; s01573/09939 trimmed uncredited = low.
- verify: text pass = high; headline+author only (03183, 08959) = medium.
- addorig: high = the story credits the outlet; medium = reporter's employer only; low + proposed **Skip** where a row of that outlet already exists (30): in the merge group (e.g. s00011 → s01903 already has 07053 LAT), a near-twin story (same headline words, ≤ 3 d), or an open origins item (rv2addorig-023 ↔ origin-007). The plan computes adds before merges, so applying both would duplicate rows.
- Merges in linked groups (> 2 stories) say so and list the stories. 11 swap/split items in stories that a merge also moves carry a NOTE.

## Reconcile (decision docs, create-only, by "Claude (regroup-queue, 2026-10-28)")
- 111 origins items superseded by an rv2 item (same row as subject, or same story pair; Fetch-items also by a no-copy add): choice "Superseded by REPRINT-v2 item <ids>", note "Auto: … nothing from this older item is applied." (choice is deliberately not one of the old options.)
- 13 nearcopy items already applied in the committed sheet (Press release = Yes and listed as Copy story ID on that release): 001, 002, 004–014, choice "Count as a copy of prNNN".
- Not touched: origin-000 (Sammy chose "Reprint of s04375"; same call as rv2merge-010, which is still undecided); 73 origins and 10 nearcopy stay open. origin-007 and origin-052 left open on purpose (only an addorig overlapped).
- Files: work/tmp_regroup_queue/dec/*.json, rec_origins.json.

## Page (NOT published)
- Live page re-read: still version 1793151804-5d51 (CATS unchanged). Source kept at work/tmp_regroup_queue/review_page.html (= work/tmp_rp-queue/review_page.html).
- work/tmp_regroup_queue/page_edit.json: one edit (anchor = the regroup line + "};", occurs once) adding origins, billtags, nearcopy (labels from tmp_rp-queue), uvreprint "Unverified reprints", dates "Dates", merge "Merges", edition "Web + print", translation "Translations", swap "Original swaps", split "Splits", verify "Unverified → Reprint", addorig "No-copy originals". regroup already had a label and was left as is. Result checked: review_page_edited.html CATS parses (29 keys). Supersedes work/tmp_rp-queue/page_edit.json.
