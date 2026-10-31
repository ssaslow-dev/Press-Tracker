# agent-imgfetch — download + normalize broken saved-copy photos for v20 embedding
Download/cache only. No edits to code/, workbook, library or published files. No Exa.
## Log
- 04:2xZ start. Worklist built from published v19 pages (tmp_agent-v19finish/pub/articles, same img index as agent-photos' scan) merged with same-index attrs from work/html_clean/<stem>.html; release copies from tmp_agent-relcopies3/tb/copies/articles/releases.json. Not from img_todo.csv.
  - 585 story imgs (593 broken content photos minus 8 pruned PDF pages) + 38 release imgs = 623. Candidates: srcset/data-srcset/data-lazy-srcset/picture>source, src + data-src/lazy-src/original/gl-src etc.; relative URLs resolved against article URL (page header line, else workbook Publisher link via id_map old->new aid). Pick largest <=1000w, else src; up to 4 fallbacks.
  - Referer = article URL (31 items with no URL anywhere: image origin).
- Fetch: requests via agent proxy, Chrome UA, <=4/host, 32 workers, 20s timeout, 2 retries. Pillow 12.3: cap 1000w, JPEG q75 progressive, alpha -> white. 99s.
- gabriel.asmdc.org / a46.asmdc.org: server sends wrong intermediate (TLS verify fail). Fixed properly by adding the missing intermediate "Entrust DV TLS Issuing RSA CA 2" (from crt.sh, verified chain to Sectigo R46) to a side bundle scratchpad/imgfetch_ca/bundle_plus.pem; no verification disabled. 35 recovered.
- Cloudflare challenges recorded as failed (status=cloudflare), not worked around. 402/403 not worked around.
- Restored 8 pruned PDF page jpgs -> work/img_cache/pdf_restore/{jg-f0d87d/p1, jg-0d9131/p1,p6, jg-8095c6/p1,p9,p11, jg-8aec80/p1,p6}.jpg (1584x2160, unchanged bytes, 4.2 MB).
## Result
- Story imgs: 343 ok / 2 skipped (3lift ad buttons s02227) / 240 failed. Releases: 37 ok / 1 skipped (logo pr00026) / 0 failed.
- Leads: 57/186 ok (31%). Lead failures: jweekly CF 33, politico CF 18, lanacion 10, infobae 8, no-url 5, ktla 5, gvwire CF 5.
- Failures by cause: cloudflare 98, 403 62, 404 48, no-url 10, 402 7, not-image 7, conn 5, timeout 2, 405 1.
- Saved-copy URL defects (not fetchable from any source we may use): 47 Arc resizer URLs (lanacion 39, infobae 8) saved without ?auth= token -> 403; 13 KTLA/Mother Jones srcs mangled to "<article URL>/<width>"; 10 src="" (s01513 s04745 s04710 s04715 s04717).
- Cache: 308 unique JPEGs, 15.5 MB (from 62.9 MB originals) + pdf_restore 4.2 MB.
- Manifest: work/img_cache/manifest.csv (+ manifest.json, worklist.json). Scripts: scratchpad/imgfetch_scripts/{build,fetch,retry}.py.
- DONE.
