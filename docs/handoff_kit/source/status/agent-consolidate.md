# agent-consolidate (B1) — DONE 2026-10-27

Read-only pass over all 10 cleaning buckets. No workbook, Mac, artifact, queue or web/Exa use. Helpers: work/tmp_agent-consolidate/ (txt.py text extraction, g.py/gcls.py Gabriel check, build.py, sammy.py). Outputs in work/final/, all keyed by OLD Article ID.

## Outputs
| File | Rows | What |
|---|---|---|
| fills.csv | 1517 (1375 aids) | blank-cell fills: Word count 1188, Mentions 189 (all Yes), Language 107, Author/byline 28, Headline 4, Outlet city 1 |
| corrections.csv | 164 (149 aids) | Mentions "Gabriel" No→Yes 124, Language 40 |
| error_copies.csv | 107 (57 files, 56 aids) | File name / File name 2 → `RETRY – TinyFish` (52 File name + 2 File name 2), Saved Copy? → No (50; ws-00947/ws-00620 already No), 3 library-only files; library, _original_html backup, _to_delete and viewer key per file |
| deletions.csv | 29 rows | 13 California Files, 14 California Globe comment-only, SDJW ws-03686, Knock LA ws-01877; no reprint rows (none exist for these stories) |
| regroup_exclude.txt | 84 aids | rows in error_copies + deletions |
| sammy_list.md | 25 items / 21 groups | the one combined list for Sammy |
| sammy_detail.csv | 831 | check rows behind the list groups (bylines, dates, outlets, URLs, headlines, word counts) |

## Method
- Every Gabriel claim re-checked on the cleaned texts (work/html_clean): Jesse Gabriel in Latin script with context, or transliterations; other Gabriels (Ugarte, Petek, Dillard, Lerner) and "San Gabriel" excluded.
- Fills: deduped; skipped on deleted/error-copy rows; bucket conflicts (6 word counts) dropped and listed; ws-00200 print-note fills held; 3 CMS-user bylines skipped; 1 byline e-mail stripped. Bucket "No" Mentions proposals: 3 actually name him (→ Yes), 5 don't (→ list).
- Word count: Chinese/Japanese = Han/kana characters + spaced non-CJK tokens; Korean = spaced words; others = bucket count. 3 CJK fills recomputed.
- Language corrections only where the copy is the same article (headline matches the sheet); different-article copies went to error_copies with Language unchanged. "Arabic/Persian" vs "Persian" left alone.
- nb- rows with a bad web copy (nb-00327, nb-02019): only File name 2 → RETRY; NewsBank PDF and Saved Copy? = Yes kept.

## Findings that differ from the brief / buckets
- **LA Wave ×7 are not truncated**: each copy is 560–1,000 words and names Jesse Gabriel (checked in Chromium). Bucket 4's parser dropped unclosed <p> text. Not error copies. Same for NPR ws-00543, pq-00300, ws-03471 (they name him) and GovTech ws-03271 (full article).
- FoodBev ws-01765: only the h1/byline are template placeholders; the body is the real article → kept.
- Defender ×4 digests: the sheet row is the digest itself, so a retry would return the same page → listed for Sammy instead of RETRY.
- Only rows other agents had already flagged were handled (no sweep). Copies saved from a different outlet with the same syndicated text (15) were listed for Sammy. Only the cases the buckets called wrong (Today.com, KSBY, the English-source copies, SMDP, One Armed Man) went to error_copies.

## Self-check
- All 1,103 html_checks rows routed to exactly one destination (corrections 170, error_copies 86, deletions 16, Sammy 831; 0 unrouted). Every "For Sammy" status item traced to one file (bucket by bucket).
- Overlaps: deletions∩fills, deletions∩corrections, error∩fills, error∩corrections, deletions∩error all empty.
- regroup_exclude = (error ∪ deletion aids) minus the file-only jg-a6dd2b: 84.
- Bucket-8 comment-only list matches the 14 IDs in DECISIONS/brief exactly.
