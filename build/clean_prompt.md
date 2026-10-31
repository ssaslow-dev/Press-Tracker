# T32 — Clean saved HTMLs (one bucket per agent)

You are agent-clean-<N> on Sammy's AJG press-coverage project. L = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib
Read first: L/README.md, L/DECISIONS.md (the "clean every saved HTML" entry is your spec), L/CONTRACT.md, L/BOARD.md.
Log in L/status/agent-clean-<N>.md. Helpers ONLY in L/work/tmp_agent-clean-<N>/. No Exa. No web fetching. Never write the workbook. Never delete anything.

## Your files
Rows of L/work/html_clean_partition.csv with bucket = <N> (columns: bucket, outlet, file_stem = "<year>/<name without .html>"). The files live on Sammy's Mac in the Desktop library: via device_bash at `$HOME/mnt/Tracker library/<file_stem>.html` (some names contain spaces/parentheses — quote paths). Your bucket holds whole outlets, so you can work outlet by outlet (same site = same template).

## Method (scalpel — when in doubt, keep)
1. Per outlet/template: look at 2–3 files, identify the article container and the clearly-errant blocks: more/related/recommended/trending stories, ads and ad slots, newsletter/subscribe/paywall/"support us" prompts, cookie/consent banners, nav menus, breadcrumbs, share/social widgets, comment sections, site headers/footers, promo boxes (e.g. CalMatters "Learn more about legislators"), "Read more"/"Most popular" lists, scripts/tracking pixels.
   KEEP: headline, dek/subhead, byline + author title/tagline, dateline/date, the body, in-article photos with captions, pull quotes, embedded tweets/videos that are part of the story, corrections/editor's notes, the author bio line at the end, the tracker's page CSS, and any "Copy saved from the tracker" provenance note.
2. Write a per-template cleaner (python, BeautifulSoup or lxml) and run it ON THE MAC with device_bash (install bs4 there with pip --user if missing; if impossible, stage files into the container with device_stage_files, clean there, and write back with device_commit_files using expectedMtimeMs).
3. Before changing ANY file: copy the original to `$HOME/mnt/Tracker library/_original_html/<file_stem>.html` (create dirs; if a backup already exists, don't overwrite it). Then write the cleaned file in place.
4. Safety checks per file, automatic: every paragraph containing "Gabriel" and the headline must survive; if the cleaner would remove >35% of the visible text words, or touch a block containing ≥40 words of continuous prose, DON'T apply — restore and list the file in your review list for a manual look (then decide by reading it; keep if unsure).
5. Metadata header at the top of a file (lines like Outlet / Date / Author / URL / Headline / Section / Page, usually added when the page was saved): compare each value with the sheet row (L/work/coverage_current.xlsx, Coverage tab — read-only; map the file to its row by Article ID = the file name's ID, or Print Article ID; for jg-xxxxxx names use "Tracker story code").
   - Same value already in the sheet → remove that header line.
   - Sheet cell blank and an existing column fits → record the fill in L/work/out/html_meta_fills_<N>.csv (aid, column, value, evidence) and KEEP the line for now (it is removed after the write).
   - No column for it → keep the line. Conflicts with the sheet → keep the line, record in the checks file.
6. Final data checks in the same read (don't read anything twice): headline, date, outlet, byline, "Gabriel" mention, language, word count (article body, after cleaning) vs the sheet. Record every discrepancy in L/work/out/html_checks_<N>.csv (aid, file, field, sheet_value, file_value, note). Blank sheet cells that the file clearly answers go to html_meta_fills_<N>.csv. Never overwrite a filled sheet value.
7. Log every file in L/work/out/html_clean_log_<N>.csv: file_stem, aid, bytes_before, bytes_after, words_before, words_after, blocks_removed (short labels), header_lines_removed, status (cleaned | unchanged | review-kept | error).
8. At the end, stage your cleaned files into the container and copy them to L/work/html_clean/<file_stem>.html (the regroup reads these). Also, if L/work/library_new/<same aid>.html exists (image-embedded replacement), apply the same cleaning to that container copy.
9. Spot check 10 random cleaned files by rendering them (Playwright in the container is fine) — article intact, clutter gone — and note it in your status file.

Final report (short): files cleaned / unchanged / kept for review, top clutter types removed, metadata lines removed, fills proposed, discrepancies found by field, anything Sammy must decide.
