# agent-photos — saved-copy photos not loading (Sammy comment on v19, s00002 "California has more revenue than expected thanks to AI…")
Read-only toward code/ and the workbook; no Exa, no publishing. Work in work/tmp_agent-photos/.
## Log
- 03:59Z start. Live v19 1793153876-e0f4 listed (127 files). Local mirror of live img shards in work/tmp_agent-photos/img (F7/live 0-15 except 3; F7/repack 3; v19 pub 100) — sizes equal live listing.
- s00002 copy = work/html_clean/2026/ws09919r-s00002.html (Piedmont Exedra, TinyFish new-outlet save 2026-10-28); lead photo is <img src="https://piedmontexedra.com/...jpeg" srcset=remote>, never embedded. Viewer srcdoc iframe inherits artifact CSP (img-src: self/data/blob only) -> blocked.
- Scan (scratchpad/photos_scripts/scan.py, classify.py, tables.py) over v19's 3,889 copies, 3,633 <img>: 2,909 load, 724 don't (131 ads/pixels/logos). 593 content photos in 225 stories (190 leads) don't load; 404 photos / 109 stories are today's saves. Causes: remote src/srcset blocked by CSP 569; src="" 10; lazy-only 3; relative 3; pruned PDF page jpgs 8 (s02782 s02409 s02503 s01827, prune + NAMING-v2). 0 jgimg misses (prune, NAMING-v2 and the img/100 union are fine). v20 release copies: 25/244 with 38 remote imgs.
- Fetch paths: container and Mac VM egress 403; TinyFish fetch_content on an image = empty_content -> only Claude-in-Chrome can get the bytes.
- Outputs: work/tmp_agent-photos/{scan_imgs.csv,scan_imgs.json,img_todo.csv,tables.md,live_pdf_paths.txt}. report.md not written (the harness blocks report files for subagents); the full report went to main in the handback.
- DONE. Nothing in code/, the workbook, the library or the artifact changed.
