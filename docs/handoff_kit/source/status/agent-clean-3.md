# agent-clean-3 (T32 bucket 3) — DONE 2026-10-27

Bucket 3 = 350 files across 61 outlets (120 LA Times, 26 La Opinión, 22 Beverly Press, 16 Food Safety News, ...).

## What was done
- Staged all 350 originals into the container (tmp_agent-clean-3/orig/), built per-outlet rules (tmp_agent-clean-3/clean.py, overrides.py, final.py) and cleaned in the container. Wrote back to the Mac with device_commit_files using expectedMtimeMs (0 rejections).
- Backups: all 196 changed files were copied to `Tracker library/_original_html/<year>/<file>.html` BEFORE writing (sha256-checked against the staged original; 196 made, 0 pre-existing). After the write: 196/196 library files match the cleaned sha256, 196/196 backups present.
- Scratch on the Mac only in `$HOME/mnt/outputs/c3/` (and c3_mtimes.json); nothing extra in the library folder. No deletes.
- Results: **196 changed** (124 had clutter removed, 72 only had matching header lines removed), **154 unchanged** (118 tracker jg-pdf ProQuest/print-page copies, plus clean pages), **0 review-kept**.
- Words removed: 9,279 total.
- Header metadata: 194 lines removed (86 files outlet·date + URL, 21 URL only, 1 outlet·date only). "Saved <date>" lines kept (no column).
- Outputs: work/out/html_clean_log_3.csv (350 rows), html_checks_3.csv (106), html_meta_fills_3.csv (264), work/html_clean/<stem>.html (all 350).
- library_new: 29 of my aids have image-embedded replacements there; all are jg-pdf copies left unchanged by cleaning → no change needed.

## Clutter removed (top)
Trailing more-stories/related/comments/footer blocks (64 files: Beverly Press Prev/Next/You might also like/comments/footer; SJV Sun Related Posts; FSN "More in…/More from…/Support FSN"; EdSource More News Briefs; Business Journal Related Coverage/poll/blogs; Precinct Reporter prev/next; CBS "In:" tags+video teaser; La Opinión "Sigue leyendo"/"En esta nota"; Headtopics, Hanbit, Aura Scan "In this series", LA Issue stats widget, podbean comments, CJN ratings/e-news); newsletter/subscribe prompts (FSN 22); share widgets (Governing, Electronic Times, Substack player); ads/promos (LA Times "Advertisement" ×17, Politico promo/ad blocks, Aura Scan app promos, ABC10 "Watch, Download, Read"); nav/login chrome (Precinct Reporter, Daily Bruin breadcrumbs); form inputs; KRCR embed junk/"Report a correction".
Kept on purpose: author bios (FSN author box, SJV "Author…", TNS/KFF boilerplate), "This story originally appeared…", copyright lines, captions, "Got tips?", in-article "Read more on …", Monterey Squid-style column blocks.

## Manual review (safety check tripped, read and approved)
>35% words or a ≥40-word block removed, all verified as non-article: Beverly Press ws-03416, ws-02202, ws-03719 (short story + big related/comments footer); FSN nb-02338, ws-01413 (related teasers); SJV ws-02552 (related-post teaser); EdSource ws-02245 (news-brief list); Headtopics ws-01639 (other stories' summaries); Hanbit ws-01726 (portal news lists); Food Business ME ws-03231 (exact second copy of the article after "No related posts."); Governing ws-03359 ("More Quotes Who Said That" — other people's quotes; only the Gabriel quote remains).

## Spot check (Playwright, 10 random cleaned files)
nb-02624, ws-00770, ws-03017, ws-03087, ws-02052, ws-03032, ws-00248, ws-02801, ws-02475, ws-00385: all render; headline, byline, body and end of article intact; clutter gone. Minor leftover: SJV Sun single-word section label ("California") above the headline kept.

## For Sammy / coordinator
- Gabriel mention: 29 rows where sheet says "No" but the saved copy names him (mostly La Opinión nb- rows, plus Korean/Persian/Ukrainian ws-02384, ws-03020, ws-03032); 4 where sheet says "Yes" but the copy has no Gabriel (pq-00300, ws-01876, ws-03471, ws-03621 — ws-03621's saved copy contains no article text at all, only the sidebar).
- ws-03032 (NV Tekhno): sheet Language English, text is Ukrainian/Russian.
- Business Journal ws-00490/00644/00732/00175: sheet author "Ben Hensley", saved copies are AP stories (Sophie Austin / Adam Beam).
- Date conflicts with header (nb-01256, nb-02199, ws-02497) and several 1-day lags; header lines kept where they differ.
- 22 "outlet" rows are name variants (ABC10 Sacramento, CBS Sacramento, Beverly Press & Park Labrea News, syndication notes like "VINnews (JNS)") — header line kept per the rule.
- 5 link conflicts (header URL vs sheet Publisher link; e.g. nb-00721 LAist vs EdSource, JNS syndications).
