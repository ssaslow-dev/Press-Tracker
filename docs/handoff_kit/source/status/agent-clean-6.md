# agent-clean-6 — T32 bucket 6 (350 files, 65 outlets)

Status: DONE (2026-10-27)

## What was done
- Bucket 6 = 350 files (largest: Epoch Times 65, SFV Sun 36, Food Safety Magazine 27, Sing Tao 24, KTVU 20, San José Inside 15, University Wire 13, The Hill 11, La Nación 10, Korea Times 9 …).
- Read 2–3 files per template (every template of the one-file outlets), wrote one rule-based cleaner: `work/tmp_agent-clean-6/clean6.py` (outlet rule tables + global rules; drop single blocks by exact full-text match, or cut from a reviewed end-marker to the end; 3 ad images by exact image hash, 3 promo images by alt text).
- Safety per file, automatic: never touch a block containing Gabriel (Latin or CJK/Korean/Hebrew/Cyrillic transliterations), never the headline, ≥40-word removed block only where the rule was reviewed, >35% removal → review.
- Run ON THE MAC (`~/clean6/run3/mac_run.py apply`, one python run for the whole bucket): each original copied to `Tracker library/_original_html/<file_stem>.html` (254 new backups, sha256-verified = original), then cleaned file written in place (sha256 of written file = expected, 254/254).
- Same code run in the container first: Mac dry-run output was byte-identical to the container output (sha list md5 88f751de…), and the Mac originals were identical to the staged ones.
- `work/html_clean/<file_stem>.html`: all 350 files (254 cleaned = byte-identical to what is now on the Mac; 96 unchanged = original copies, so the regroup has every text of the bucket).
- `work/library_new`: only `pq-00312.html` belongs to this bucket; the cleaner finds nothing to remove in it (print-page text layer) → left as is.

## Results
- cleaned 254 · unchanged 96 · review-kept 0 · error 0.
- Safety stops: 31 files went over the 35% limit. I read every one and applied the clean (listed as approved in jobs.json): 13 Epoch Times traditional-Chinese pages (~800 words of rankings/related/comment boxes after "分享本頁"), 6 Food Safety Magazine empty-body pages (only the matching header lines), FSM ws-02567/ws-02446 (product/event lists), Korea Times ×5 (comment policy, reader comments, login box, footer), ECJ ws-03536/ws-03504 (archive list of ~150 months), Imperial Valley Press nb-01648 (tags/comments/footer), Forum Daily ws-02928 (related/tags/offers/footer), FBN ws-00947. The "headline hit" stops were false positives (Korea Times ×8: login-box h1 "x 로그인 회원가입"; SFV Sun ×2: comment heading "One reply on '<headline>'"; KTVU ×1: tag "California"); the check now only fires on the real headline.
- Top clutter removed (blocks): related/rankings/comment boxes (Epoch, 1,444), blog archives/recent posts (ECJ, 328), comment policy + reader comments + login (Korea Times, 236), popularity counters (143), The Hill "More … News/Hill.TV/Top Stories" tails (129), related-news lists (75), share widgets (52), tag lists (48+), Forum Daily related/offers/footer (48), stray UI words ("html", "article", "close", 43), Telegram/"support us"/video lists (Epoch Spanish, 39), promos (32), breadcrumbs (28), FlippingBook viewer junk (Sing Tao, 26), ads (23 text + 21 ad images), newsletter prompts.
- Metadata header ("Outlet · date / URL / Saved …"): 149 lines removed in 83 files (outlet+date or URL equal to the sheet; "The X" = "X, The" and accents ignored). "Saved YYYY-MM-DD" lines kept (no column). Lines kept where the date differs (8 SFV Sun files: header date = URL date, sheet = one day later), or the outlet carries extra detail in parentheses (9 files, e.g. "The National Desk (Sinclair)"), or the URL differs (2).
- Fills proposed (blanks only): `work/out/html_meta_fills_6.csv` — 37 rows: Mentions "Gabriel" 20, Language 9, Author / byline 7 ("SFVS Staff"), Headline 1 (ws-02247). Header lines with a blank sheet cell: none (all header outlet/date/URL cells were already filled).
- Discrepancies: `work/out/html_checks_6.csv` — 122 rows: copy problems 29 (listing/feed pages, empty or truncated captures, digests), placeholder image 20, Gabriel 18, language 10, headline 9, word count 9 (non-CJK only; >25% and >25 words), outlet 9, date 8, byline 8, url 2.
- Log: `work/out/html_clean_log_6.csv` (words = CJK-aware word count of visible text: 2 CJK characters ≈ 1 word).

## Spot check (step 9)
Rendered 10 random cleaned files with Playwright (seed 6): 2025/ws-02238, 2024/ws-02615, 2025/ws-02283, 2021/ws-03586, 2024/ws-02459, 2025/ws-02205, 2023/ws-02959, 2021/pq-00068, 2018/ws-03831, 2023/nb-02062. All open, headline + body + Gabriel mention present, tails end with the article / author bio, no share bars, related lists or footers. The nb-02062 screenshot exposed an image-only "No on Prop 44" banner ad → added image-ad removal (exact image hashes) before the Mac run.

## Left alone on purpose (when in doubt, keep)
- Single-block captures (NewsBank text, Sing Tao FlippingBook pages, Epoch English one-paragraph pages, Korea Daily ws-03257/ws-01657): clutter sits inside the one prose block; not cut.
- Multi-story pages (Defender digests, Sound of Hope news roundups, Eater "Intel" roundup items) and listing pages: the other stories were not removed.
- "Copyright 2024 Capital & Main." line, ProQuest "PDF GENERATED BY PROQUEST.COM / Page x of y" lines, "Text of the ProQuest PDF" notes, editor credits (责任编辑), author bios.

## For Sammy / coordinator
1. Stray files I could not delete (deleting is off): `Desktop/Tracker library/_tmp_clean6/` holds b6.tgz (11 MB archive of the 350 originals), bundle6.tgz, bundle6b.tgz (cleaner code). Safe to delete the whole `_tmp_clean6` folder.
2. 20 SFV Sun copies show the same unrelated lead photo ("We Are the Constitution" protest) under the article's own caption: capture artifact, left in place.
3. 29 saved copies are not the article (FSM/NewsBreak listing pages, MoJo nb-00053 (jg-a87925) = a 25-story list, empty FSM/FBN bodies, truncated FSM captures, Defender digests). See `copy` rows in the checks file; these may need re-capture.
4. Gabriel = "No" in the sheet while the text names him only in transliteration (가브리엘, Габриэл, גבריאל…) in 18 files: should transliterations count as a mention?
5. Language: Sing Tao ×5 marked Korean but are Chinese; Epoch ws-03783/03784 marked Japanese but are Chinese; Korea Times ws-00554 and Chinese in LA ws-01422 copies are the English source articles (CalMatters/LA Times), not the outlet's version; Forum Daily ws-02928 marked English, copy is the Kyrgyz page.
6. Byline conflicts: San José Inside ws-00621/ws-00777 (sheet Barry Holtzclaw vs copy Alexei Koseff/Ben Christopher), MoJo nb-00073 (Jane Black vs Stephanie Mencimer), California Black Media ws-00199 (Antonio Ray Harvey vs Kenneth Miller).
