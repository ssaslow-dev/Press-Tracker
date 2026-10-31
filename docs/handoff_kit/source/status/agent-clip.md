# agent-clip — NewsBank print-page clipping (Sammy: "start using claude in chrome to do the press clippings ... use the ca library newsbank links")

## Run 1 — 2026-10-27 ~22:55Z — STOPPED: CSL NewsBank logged out
- Read README, DECISIONS, CONTRACT, TONE_GUIDE, make_copies.py, reprint_rule.py, relrule loader. Master sha check: work/coverage_current.xlsx = 35f97ebbaf5892cc47707e112b64d5cc7cae66886522cdb5a1f1d4f246fb221e (matches expected).
- Target list built: work/clip/targets.csv (script work/tmp_agent-clip/targets.py). 1,471 blank "Original or reprint" print pages with a CSL print-page link (the 1 other blank row is a TinyFish web row, no link; no California Files among them).
  Priority 1 = 1,054 (no other classified row of the same outlet within +-1 day, outlet names normalized incl. "Today's Edition"; no row sharing the docref). Priority 2 = 417. Ordered newest first within priority.
- Mac bridge up (connected: Documents/Gabriel press PDFs, Desktop/Tracker library). Earlier clips AJG-P0001/P0002 landed in Documents/Gabriel press PDFs, so Chrome's download folder is probably that folder (verify on first clip).
- Chrome reachable (new tab group), but the first CSL link (05427, Record Stockton 2026-10-18 p.20) redirected to login.castatelib.idm.oclc.org "California State Library - Login page". Per instructions: no login attempted; stopped. 0 clips, 0 downloads, 0 sheet writes.

## Resume
1. Sammy logs in to the CA State Library proxy in Chrome (barcode/email + password, his own action).
2. Re-run from targets.csv row 1 (05427). Plan for metadata/indexing: OCR text -> work/texts/nb/<Old Article ID>.json in the existing texts/nb format (make_copies.py nb_texts/nb_page reads it, keyed via Old Article ID -> Article ID), reprint check via reprint_rule.text_verdict against texts_v2.pkl + cleaned HTML (relrule.py loader pattern).

## RESUME NOTE (coordinator, 2026-10-27): Sammy said "skip the ocr step". Do not OCR clips. Read metadata off the clip image (screenshot) or from a matched full-text article (same paper, date, page); story matching via available text or the headline + people fallback; no work/texts/nb OCR JSON. Still blocked until Sammy logs in to the CSL proxy in Chrome.

## Run 2 — 2026-10-27 ~23:00Z (Sammy logged in)
- Dry-run clips 05427/05428/05429 made as BOXED clips, files placed in library (nb05427o-s04685, nb05428o-s04686, nb05429r-s00011). Then three workflow changes from Sammy (DECISIONS lines added at end):
  1. whole page + jump pages, merged, no selection box (boxed clips redone; old ones -> _to_delete/2026/);
  2. OCR back ON (article text only, to texts/nb/<old aid>.json);
  3. OCR near misses decided automatically (OCR-tolerant option in code/reprint_rule.py).
- Downloads land in ~/Documents/Gabriel press PDFs (Chrome's folder); after placing, raw downloads are moved to Documents/Gabriel press PDFs/_clip_downloads/.
- Whole-page download: actions-bar__button--download_ha -> "Download Full Page" -> "Download Full Page PDF" -> citation modal (APA) -> submit; JS helper __fullDl(name). Selection-box handles respond 1:1 to synthetic pointer events (no longer needed).
- Tools: work/tmp_agent-clip/ocr_page.py (one tesseract pass -> TSV + invisible text layer grafted onto the original NewsBank page, ~10 s/page; ocrmypdf --redo-ocr took 45 s/page because it rasterizes the 2092x4300 pt page), prep.py (preview with grid + Gabriel boxes for picking the article rectangle), extract.py (article text = TSV words inside the rectangle(s), tesseract reading order; JUMP regex), matcher.py (cached index of all classified rows' texts, crc32 25-gram candidate lookup + headline overlap, reprint_rule.decide_ocr), finalize.py (texts/nb JSON), write_batch.py + diff_check.py (rule-7 batch).
- code/reprint_rule.py: OCRTOL-v1 appended (opt-in: ocr_fold, ocr_tolerant_pair, text_verdict_ocr, headline_sim, ocr_near_miss_link, decide_ocr); default rule unchanged. Pre-edit copy work/tmp_agent-clip/reprint_rule.pre_ocr.py. Test work/tmp_agent-clip/test_ocrtol.py: 4/4 PASS.
- DRY RUN DONE (batch b001, 3 rows): 05427 -> Reprint s00007 (text 99% OCR vs CalMatters 00021); 05428 -> new Original s04685 (AP Bharath trimmed print version; near miss 88% vs AP 00133, headline 0.40/date out of window -> new per rule); 05429 -> Reprint s00011 (text 99% vs South Marion Citizen 00036). Library: 3 whole-page OCR PDFs in Tracker library/2026 (boxed versions moved to _to_delete/2026). Sheet: backup "…BACKUP before clip batch 001 2026-10-27.xlsx" (35f97ebb…221e), master now 1e41d71cfda6a91717c15d2bfeb288eabb134139d495710121d1a0c36e8cafab (Mac-verified), 49 value cells + red->default font on 3 rows + 1 Originals row inserted; diff check 0 unexpected. coverage_current.xlsx updated (pre copy coverage_pre_clip001.xlsx).
- Local make_copies build (work/tmp_agent-clip/copies_test): s04685 gets its viewer/search copy from texts/nb/nb-04096.json (OCR text). Reprints get no copy (same as all reprints).
- Pending correction (next batch): 05428 Word count 1065 -> 1049 (my own b001 value counted header lines) — work/clip/corrections.json.

## STOPPED by Sammy — 2026-10-27 ~23:55Z ("save what you have … then stop the process its taking too long")
### Saved (all three shards, 28 rows; progress.csv has every row with target_row, shard, decision evidence)
- Shard 0 (me): 05427 05428 05429 05430 05437 05442 05445 05448 05452 05456 05459 05462 05465 (05428/05429 were rows 1/2, done in the dry run).
- Shard 1 (agent-clip-1): 05431 05438 05443 05446 05449 05453 05457 05460 05463. Shard 2 (agent-clip-2): 05434 05441 05444 05447 05451 05454.
- Decisions (agent-clip only, matcher.decide with OCRTOL-v1b): 2 new Originals — s04685 (05428 Daily Times 10-11, trimmed AP Bharath, 21 days after s04300/s00044 -> outside +-7 days) and s04686 (05462 Denver Post 09-20 "Laws trigger fresh legal fight": near miss 86% but headline 0.69 < 0.8 -> new by rule); 26 Reprints: s00007 x1, s00011 x3 (05431 does NOT rank first: its byline credits LA Times/TNS -> tier 4 vs the South Marion Citizen Original's tier 2), s00019, s00029 x2 (05441 passes only after jump/label stripping: tolerant 91%), s00037 x8, s00038 x6, s00044 x3 (05457 auto near miss: headline 0.83 + same author vs 05465), s01903 (05437, tolerant 93%), s04300 x2 (05460/05463 text 91%).
  AP "Nazi-looted art" consistency note: the rule was applied exactly; versions split by their text (full AP -> s00044; Seattle-style trim -> s04300; Denver trim -> new s04686; Oct 11 Maryville trim -> new s04685 because every candidate is > 7 days away). The helpers' proposals 05457 -> s04300 became s00044 (rule result).
  Tone/Topic/Bills only on the 2 Originals (Reprints carry Role, byline, authors, section, word count, mentions).
- Library: 28 whole-page PDFs with OCR text layers in Tracker library/2026 (b001 3 + b002 25; Mac shas verified); raw jump pages for 6 multi-page rows in Tracker library/_original_pdf/2026/ (12 files); boxed dry-run clips in _to_delete/2026/ (3). Raw downloads moved to Documents/Gabriel press PDFs/_clip_downloads/ (incl. duplicates "05449_p35 (1).pdf", "05456_p55 (1).pdf").
- texts/nb: 28 new OCR JSONs (nb-04095…), indexed by make_copies (checked: s04685 copy built from texts/nb). Reprints get no viewer copy (as all reprints).
- Sheet: b002 = backup "Backups/…BACKUP before clip batch 002 2026-10-27.xlsx" (1e41d71c…), 25 rows filled (blank cells; Saved Copy? No->Yes), red font removed on the 25 rows, 1 Originals row inserted (05462), 05428 Word count 1065->1049, '# of reprints' recomputed on 8 Originals (00021 00036 00086 00110 00120 00133 00147 07051) + 05462 = 0, mirrored on Originals; diff check 0 unexpected. MASTER NOW e08906723649b3b1cba14859506fff609cf267df0c33f512a9e3765e5e90ef8b (Mac-verified) = work/coverage_current.xlsx (pre: coverage_pre_clip002.xlsx).
### Not done / left
- 05458 (target row 23, shard 2): abandoned; its late download 05458_p7.pdf is in Documents/Gabriel press PDFs, UNPROCESSED; sheet row untouched.
- No no-gabriel / error rows.
### To resume (targets.csv order unchanged; 1,443 rows left)
- Next rows: shard 0 -> row 33 (05468); shard 1 -> row 31 (05466); shard 2 -> row 23 (05458, file already downloaded) then row 26 (05461).
- Per row: browser (store helper JS once: localStorage.__fdl = work/tmp_agent-clip/fulldl.js + __openSearch/__go; wait >= 15 s after submit before navigating; <= 2 rows per browser_batch), stage download, work/tmp_agent-clip/step1.sh KEY (OCR graft + preview), view preview, mkrow.py decide/commit SPEC (rects in page fractions), then batch: stage files to /mnt/user-data/outputs/clip/<year>/ + device_commit_files, write_batch.py (env CLIP_REP_SIDS / CLIP_CORR) + diff_check.py, rule-7 commit. next_sid.txt = 4687.
