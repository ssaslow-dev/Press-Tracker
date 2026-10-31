# agent-clean-10 — T32 bucket 10 (349 files, incl. 23 jg-xxxxxx "(unknown)")

## Done (2026-10-27)
- Staged all 349 originals once (container copies: work/tmp_agent-clean-10/orig/). Cleaner built/tested in container:
  work/tmp_agent-clean-10/clean10.py (generic: widget tags, share/ad/newsletter chrome, tail markers, inline "Link copied")
  + rules10.py (per-outlet + per-jg-file rules) + pipeline.py (header, safety, checks) + mac10.py (Mac runner).
- Mac: one dry run (251/251 outputs sha-identical to container), then one apply: 251 originals backed up to
  Tracker library/_original_html/<year>/ (all new backups, sha verified), cleaned files written, written sha == expected (0 mismatches).
  Mac scratch only in $HOME/mnt/outputs/c10/.
- Status: cleaned 251, unchanged 96 (incl. 13 PDF-text copies left as is), review-kept 2.
- Outputs: work/out/html_clean_log_10.csv, html_checks_10.csv (89 rows), html_meta_fills_10.csv (197 fills);
  work/html_clean/<stem>.html for all 349 (cleaned or original).
- library_new: only pq-00091 and pq-00235 are mine; both are PDF-text pages -> no cleaning applies (left unchanged).

## Safety
- Auto checks: >35% words removed, removed block with >=40-word prose, every Gabriel sentence (incl. 가브리엘/Габри/גבריאל/加布里埃/加布尔) and the h1 must survive.
- Hand-reviewed and allowed: SB Independent ws-00364 (36%: only the "Premier Events" calendar), and long removed blocks that are
  CNS newsletter promo, TownNews comment rules, TTAG "In Other NEWS", J. donation box, BHS other stories, QA "Latest" list, VBS nav.
- review-kept (not cleaned, read by hand): 2025/ws-02163 (New Times "Cover Story" index page, not the article),
  2020/ws-03665 (Acorn issue front page with teasers, not the article) — both listed in checks as "saved copy".

## jg- files (23)
Mapped via Tracker story code (rename_ambiguous). All 23 cleaned like the rest; checks compare with the best headline match among
the code's rows and list all candidate rows (field "mapping"); no fills proposed for them (the page is not itself any row).

## Spot check
10 random cleaned files rendered with Playwright (Chromium): article text intact start to end, clutter gone. Minor leftovers seen
and accepted: GV Wire "more from Edward Smith" link label; CNS "Categories / …" lines kept on purpose (taxonomy, not clutter).

## For Sammy
- Language: Bao Cali Today ws-01982 and VOA ws-02410 are Vietnamese (sheet: Portuguese); ws-01377 Vietnamese (sheet: English).
- Gabriel mention: sheet "No" but text has 가브리엘 — ws-02108, ws-02412 (Shaded Community), ws-02454 (Kormedi).
- Saved copy is not the article: ws-02163, ws-03665 (need a new capture); GovTech ws-03271 is paywall-only (headline + teaser).
