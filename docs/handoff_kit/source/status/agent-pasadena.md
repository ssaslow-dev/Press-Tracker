# agent-pasadena
- started: listing Pasadena Now rows
- saved copies (html_clean + clean-10 orig + authors tf) carry no date metadata/byline; going to live pages. Header date on live page = view date (Oct 27 2026 today).
- live pages checked (18 links) via WebFetch "Published on" dateline; TinyFish fetch confirmed header date "Oct 21, 2026" = date of visit (cache) and its published_date field = 2026-10-21 (that header) — the source of the error.
- text checks run with code/reprint_rule.py vs candidate Originals on true dates (script work/out/pas_textcheck.py).
- output: work/out/pasadena_dates.csv. 17 wrong (all Originals ws-01313..01329 -> 06955..06971, sheet 2026-10-21). DONE.
