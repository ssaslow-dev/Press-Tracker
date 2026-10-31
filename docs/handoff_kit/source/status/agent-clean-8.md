# agent-clean-8 — T32 bucket 8 (349 files, 64 outlets) — DONE

## Result
- 349 files: 268 changed on the Mac (210 clutter removed, 58 header lines only), 81 unchanged. 0 errors, 0 left in review (23 safety-flagged files were read and decided; see below).
- Backups: 268 originals in Desktop/Tracker library/_original_html/<year>/ (none pre-existed, none overwritten). Verified: combined sha256 of backups == originals staged at start; combined sha256 of the 349 library files on disk == container outputs (disk digest bd8f863b98e817ac).
- Mac runs: one dry run (digest match), one apply, then a small second pass (6 files: headless WordPress comment lists, applied from the backups; dry digest matched first). Scratch/code only in $HOME/mnt/outputs/clean8.
- Final copies: L/work/html_clean/<file_stem>.html (all 349, cleaned or unchanged). library_new: 6 bucket-8 aids (ws-02024, ws-02714, ws-00041, ws-01338, ws-02126, ws-02432) are page-image PDF renditions (jg-pdf) -> nothing to clean, left as is.
- Outputs: L/work/out/html_clean_log_8.csv, html_checks_8.csv (74 rows), html_meta_fills_8.csv (159 rows).
- Code: L/work/tmp_agent-clean-8/clean8.py (rules), core8.py (guards + header lines), run8.py, checks8.py, overrides.json (manual review decisions), mac8.py/mac8b.py.

## Removed (counts of blocks)
related/more-stories 280, reader comments 136, share widgets 123, ads/ad slots 115, site UI/nav/login/footer links 114, newsletter boxes 80, form/select/login inputs 72, promos 47, CA Globe author tabs 41, site copyright footers 23, skip/back-to-top 21, follow-us 19, support/donate appeals 13, paywall 4. Header lines removed: 195 (outlet·date and URL lines matching the sheet; "Saved …" lines kept).
Skipped by design: jg-pdf page-image files (Encino Enterprise, Valley Vantage) and tracker jg-pdf-text renditions (Center Square/Daily News/JPost/Desert Sun ProQuest/NewsBank text).

## Safety-flag decisions (manual)
- Approved (only reader comments / support appeals / comment-policy text exceeded the 40-word or 35% limits; Gabriel count unchanged): 2019/ws-03763, 2021/ws-01142, 2021/ws-03612 (one reader comment also named Gabriel; article keeps its 2 mentions), 2023/ws-00930, 2023/ws-01003, 2023/ws-02971, 2023/ws-03197, 2024/ws-02382, 2024/ws-02440, 2024/ws-02809, 2025/ws-01884, 2025/ws-01967, 2025/ws-02315, 2025/ws-02362, 2026/ws-01437, 2026/ws-01622, 2026/ws-01653, 2026/ws-01865.
- Reader comments KEPT because they hold the only Gabriel mention (article body never names him): 2024/ws-02708, ws-02813, ws-02840, 2025/ws-01900, ws-01913, ws-02190, ws-02196, ws-02219, ws-02222, 2026/ws-01709, ws-01762, ws-01804, ws-01806, ws-01807 (all California Globe). Listed in html_checks_8 (field "Gabriel mention", note) — Sammy may want to revisit "Mentions Gabriel = Yes" / whether these belong in the tracker.

## Checks (html_checks_8.csv)
word count 26 (mostly sheet counts that included comments/clutter), Gabriel mention 23 (14 comment-only notes above; 8 sheet "No" where the text has Gabriel incl. 가브리엘/Габриэль forms -> to correct to Yes; nb-00327 sheet Yes but saved copy is only the National Law Review legal disclaimer), outlet 7, headline 6, url 5, language 4 (ws-03038 Habr and ws-03229 Vechyorka are Russian, sheet says English; ws-02257 Vsluh is Russian, sheet says Portuguese; ws-00566 text English vs sheet Korean), date 2, byline 1.

## Fills proposed (html_meta_fills_8.csv)
Word count 124 (cleaned body words excl. header lines/headline; median ratio vs existing sheet counts 0.98), Mentions "Gabriel" 29, Author 4, Outlet city 1 (ws-01766 Patch (Los Angeles)), Language 1. Header lines are kept in files whose fill is pending only if they map to a fill (none here: outlet/date never blank).

## Spot check (Playwright, 20 renders)
Articles intact; clutter gone. Known small leftovers kept (scalpel): CA Globe "One thought on …" heading in 2025/ws-01884; ECT comment author/date stubs (e.g. 2021/ws-01142); Armenian Mirror "Forgot your password? Get help"; Seoul Shinmun (jg-c55b98) font-size UI + more-stories list; Univision ViX promo h3s; Vsluh/Vechyorka trailing related lists.
