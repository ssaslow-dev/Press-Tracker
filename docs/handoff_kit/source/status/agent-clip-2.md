# agent-clip-2 log
- 23:13Z start; tab 995517842; rows i%3==2 from i=5 (489 rows)
- Pipeline (per coordinator note): page OCR = work/tmp_agent-clip/ocr_page.py (flock-serialized), text = extract.article_text, match = matcher.decide (read-only; jump/kicker lines stripped first). Scripts: scratchpad/c2/{prep,isolate,match,add_result}.py.
- Jump-page nav: page dropdown at (924,247), items Page A001.. at y=280+29.4*(n-1) (real clicks; JS click on div.page doesn't navigate).
- done 05434 (A1+A9, Reprint of s00019), 05441 (A1+A7, Reprint of s00029)
- done 05444 (A7, Reprint s00037), 05447 (57+58, Reprint s00037). 23:37Z PAUSED: 05451 NewsBank error 1500 'Unable to retrieve document'; messaged main, waiting. Next row k=4 (05451).

## FINAL (2026-10-27 ~23:45Z) — stopped per Sammy's shutdown via coordinator
- Rows done (6, all status=done, each with shard_2/<aid>.pdf merged + text layer, <aid>.ocr.json, raw/<aid>_p<N>.pdf, results.csv line):
  05434 (OC Register A1+A9, Reprint of s00019), 05441 (Whittier Daily News A1+A7, Reprint of s00029), 05444 (Sac Bee A7, Reprint of s00037),
  05447 (Fresno Bee TE 57+58, Reprint of s00037), 05451 (Tribune TE 34+35, Reprint of s00037; first load error 1500, retry OK), 05454 (Modesto Bee TE 56, Reprint of s00038).
- Abandoned: 05458 (Daily Camera 2026-09-20 p7) — download submitted (citation modal OK, 4 highlights) but 05458_p7.pdf never appeared in Documents/Gabriel press PDFs; no result line, no files in shard_2. Next unstarted row after it: k=7 (05461).
- Downloads in Documents/Gabriel press PDFs without a finished result: none (all my files there — 05434_p1/p9, 05441_p1/p7, 05444_p7, 05447_p57/p58, 05451_p34/p35, 05454_p56 — have finished results). If 05458_p7.pdf shows up late, it has no result.
- Chrome tab 995517842: the tab group was already gone when I tried to close it (closed elsewhere), so no tab of mine is left open. That may also be why 05458_p7.pdf never landed.
