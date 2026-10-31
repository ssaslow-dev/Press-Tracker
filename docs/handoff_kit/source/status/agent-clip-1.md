# agent-clip-1 — clipping helper (rows i%3==1 from row 4)

## Run 1 — 2026-10-27 ~23:13–23:42Z — STOPPED by Sammy (process shut down)
- Own Chrome tab (now closed). No logins, CAPTCHAs, or blocks were seen.
- Done (9 rows, every one with merged PDF, OCR JSON and results line in work/clip/shard_1/):
  05431 (row 4), 05438 (7), 05443 (10), 05446 (13), 05449 (16, cont. p36), 05453 (19), 05457 (22), 05460 (25), 05463 (28).
- Proposed matches (evidence only; agent-clip decides):
  05431→s00011 (text 100%, would rank first);
  05438→s00029 (97%);
  05443 and 05453→s00038 (100%);
  05446 and 05449→s00037 (100%);
  05457, 05460 and 05463→s04300 (auto OCR near miss: headline + same author).
- Abandoned: none. 05466 (row 31), the next row, was never started.
- Downloads in Documents/Gabriel press PDFs: 05431_p19, 05438_p5, 05443_p44, 05446_p205, 05449_p35, 05449_p36, 05453_p38, 05457_p13, 05460_p16, 05463_p5 (.pdf). All have finished results. None are orphaned. Nothing was moved or deleted there.
- Pipeline: ocr_page.py (agent-clip) → extract.article_text → finalize.body_of → matcher.decide. Scripts are in scratchpad/clip1_scripts/ (prep2.py, finish2.py, blocks.py).
  ocr.json is in the row-JSON shape that finalize.write takes (old_aid, text=body, words, citation, docref, pages, flags), with no sid or file yet.
- Notes:
  - 05446: NewsBank page search found 0 highlights, but OCR finds Gabriel.
  - 05449: e-edition story continues on p36 with no jump line.
  - 05463: the last few OCR lines are slightly out of order.
