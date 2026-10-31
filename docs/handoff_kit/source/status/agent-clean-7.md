# agent-clean-7 (T32, bucket 7) — DONE 2026-10-27

Files: 350 (64 outlets; SDJW 62, CBS 37, Asbarez 28, KQED 24, CapRadio 20, ...). Helpers: work/tmp_agent-clean-7/ (clean7.py = per-outlet rules + header + checks; force.json = manual approvals).

## Result
- cleaned 237, unchanged 112, review-kept 1 (2020/ws-03686 SDJW: Gabriel appears only inside a reader comment that reprints a Jewish Caucus release; file left untouched).
- 50 files tripped a safety check and were applied only after I read the removed text (reasons in work/out/html_review_7.csv): reader comments (SDJW, Asbarez), CapRadio donate appeal, Daily Republic comment rules, KQED page-state script dump (window.__INITIAL_STATE__, 8–13k words printed as text), LA County Politics verbatim duplicate of the article after the comment form, SMDJ paywall/login prompt, Dealmoon nav + comments, Alamy licensing text, NCSL "MORE CHATS" archive, Univision "Mira también" related story, Lewiston paywall/cookie lines.
- Metadata header lines removed: 155 (outlet·date and URL lines that match the sheet). Kept: "Saved …" lines, 17 outlet lines with qualifiers/different labels (e.g. "CBS News (CBS LA/AP)", "CalMatters" vs "News From The States"), 6 URL lines that differ from Publisher link.

## Mac
- Originals backed up first: Tracker library/_original_html/<year>/<file> (237 new, all byte-identical to the pre-clean files).
- Cleaned files written with device_commit_files (expectedMtimeMs guard; 237 written, 0 rejected). Shipping the 34 KB cleaner by base64 was impractical, so the playbook's "run on Mac" step became commit + verify.
- Verify: sha256 of the 237 files on the Mac = the container's (list hash 4177996e…3aa6).
- Mac scratch only in $HOME/mnt/outputs/c7 (cleaned_files.txt, an unused tgz of originals).

## Outputs
- work/out/html_clean_log_7.csv, html_checks_7.csv (73 rows), html_meta_fills_7.csv (151 rows), html_review_7.csv
- work/html_clean/<stem>.html — all 350 (cleaned version where cleaned, else the original). No library_new overlap for this bucket.

## Self-check
- Spot check (Playwright, 10 random cleaned files: ws-00743, ws-00061, ws-02794, ws-01458, ws-01829, ws-01096, ws-02992, ws-00812, ws-03816, ws-01231): article intact, headline/byline/body present, tails end at the last article paragraph; clutter gone.
- Every removed block was checked: no paragraph with Gabriel (incl. non-Latin forms) lost; headline kept.

## For Sammy
- Gabriel mention "No" in sheet but the text has it: ws-02525, ws-02947 (Dealmoon, 加布里埃尔), ws-02322 (Astroclub, Persian), ws-02610 (Shavua Israeli, Hebrew), ws-03498 (Lechaim, Russian; sheet Language says English → Russian).
- ws-03343 Mo Nam Cali: sheet Language Portuguese, text is Vietnamese.
- ws-02673 Lewiston: saved copy is paywalled (headline + byline only).
- ws-03817 CNN transcript segment: saved copy text does not contain "Gabriel" (sheet Mentions blank → fill "No" proposed).
- Word count: 37 differences, mostly where the sheet counted page clutter (KQED script dumps, comments) — see checks.
