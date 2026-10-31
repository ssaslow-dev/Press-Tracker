# AJG — what only Sammy can decide (B1 consolidate, 2026-10-27)

Sources: all 10 cleaning buckets (html_checks/meta_fills/clean logs, html_review_7, "For Sammy" sections), checked against the cleaned texts in work/html_clean. Read-only pass: nothing written to the workbook, Mac, artifact or queue.

## Already settled by DECISIONS.md (queued for the final write, no answer needed)

- **fills.csv** — 1517 blank-cell fills: Word count 1188, Mentions "Gabriel" in text 189, Language 107, Author / byline 28, Headline 4, Outlet city 1.
- **corrections.csv** — 164 overrides: Mentions "Gabriel" No→Yes 124 (no Yes→No), Language 40.
- **error_copies.csv** — 57 library files are not the article → `RETRY – TinyFish` + Saved Copy? No on 54 rows (3 extra files have no sheet cell and only move to _to_delete).
- **deletions.csv** — 29 rows deleted everywhere: 13 California Files, 14 California Globe (comment-only), SDJW ws-03686, Knock LA ws-01877. No reprint rows qualify (these stories have none).
- **regroup_exclude.txt** — 84 Article IDs (rows in error_copies + deletions).

## Needs Sammy — 25 items in 21 groups (detail rows: sammy_detail.csv, 831 rows)

### A. "Gabriel" may not be Jesse Gabriel
- ws-02294 Vistazo and ws-01876 Ecuavisa: both are about **Gabriel Ugarte** (Ecuadorian Assembly candidate); sheet says Mentions = Yes. Delete both rows? (DECISIONS has no rule for "wrong Gabriel".)
- ws-03814 LA Times (2019, LAO pick): only **Gabriel Petek**; Mentions blank. Delete row, or fill "No"?
- ws-03208 La Opinión: only "dijo Gabriel, legislador de California" about the food-additive bill — almost certainly him. ws-03503 Homeless Strategy: only "AB 977 …, Gabriel." — AB 977 (2021) is his bill. Both left as Yes unless you say otherwise.

### B. Article text never names Gabriel
- ws-02441 CalMatters (absences), ws-02625 Sac Bee (excise-tax suit), ws-02833 Sac Bee (Everytown, Spanish), ws-03851 Times of Israel (Corey Feldman): full copies, no Gabriel, Mentions blank. Fill "No" and keep, or delete rows?
- nb-03972 and nb-03965 KPCC (2018 AD-45 special election): LAist-archive web copies are full articles without Gabriel; sheet says Yes (NewsBank PDF is the File name). Leave as is, or check the PDFs?

### C. Byline conflicts (sheet vs copy)
- 68 rows in sammy_detail.csv. Notable: Business Journal ws-00490/00644/00732/00175 sheet "Ben Hensley" but copies are AP (Sophie Austin/Adam Beam); Sentinel nb-01006/nb-02516 sheet Cora Jackson-Fossett vs Lila Brown/Antonio Ray Harvey; San José Inside ws-00621/ws-00777 Barry Holtzclaw vs Alexei Koseff/Ben Christopher; MoJo nb-00073 Jane Black vs Stephanie Mencimer; California Black Media ws-00199 Antonio Ray Harvey vs Kenneth Miller. Change the sheet?

### D. Outlet names
- 121 header lines name a sub-brand/variant (Politico Playbook, ABC7 (KGO), Spectrum "Inside the Issues", FOX40 shows…); header lines kept. Keep as is (no column for sub-brands)?
- 15 saved copies come from a different outlet carrying the same text (e.g. CalMatters rows saved from ABC10/LAist/Desert Review, AP rows from ABC7/Spectrum/KTLA, JNS from VINnews/Jewish Website, Israel Info from The Jewish News). Not treated as error copies. Keep them, or RETRY for the row's own outlet? IDs: nb-00138, nb-00209, nb-00629, nb-00721, nb-00737, nb-00739, nb-01048, nb-02201, ws-00199, ws-00231, ws-00292, ws-00402, ws-00515, ws-00783, ws-02427

### E. Date conflicts
- 49 rows: header/page date ≠ sheet Date (often 1 day; 8 SFV Sun files where the sheet is one day after the URL date). Biggest: nb-02960, nb-01256, nb-02199, ws-02497, ws-02241, nb-02935. Change any?

### F. Header URL mismatches
- 50 rows. KCRA ws-02681/02462/02679/01802: header URL is an unrelated WWII-grenade story (copy itself is right) — drop those header lines? Engadget ws-03053 header URL is a car-keys how-to (copy right). The rest are long/short forms or syndication URLs.

### G. Defender digests
- ws-02016, ws-02487, ws-02599, ws-02774 (The Defender): the saved page is a multi-story digest, but the sheet row IS that digest (its headline is the digest title) and the Gabriel item is in it, so a retry would fetch the same page. Kept as copies; DECISIONS lists digest pages as errors — mark them RETRY anyway?

### H. ws-00200 print note
- ws-00200 (2026): the page ends with a publisher print note: Print headline "California Legislature Approves $356 Billion Budget — Rejecting Some of Gov. Newsom’s Proposed Cuts", Section "UL", Page "3". Fill those three cells?

### I. CalMatters WhatMatters link lists
- 36 saved WhatMatters newsletters keep their "Other things worth your time" / "Other Stories You Should Know" link roundups (kept as the newsletter's own content). Keep or strip?

### J. Daily Journal copyright notice
- ws-02814, ws-02767, ws-02460, ws-03172: a 60+ word Daily Journal Corporation copyright/subscriber notice sits at the top of the text. Strip it (it would also leave the search index)?

### K. SFV Sun lead photo
- 19 SFV Sun copies show the same unrelated "We Are the Constitution" protest photo under the article caption (capture artifact). Remove the image, or leave it?

### L. Sheet headline looks wrong
- nb-04053 Jewish Journal: sheet Headline "More from JewishJournal.com"; the article is "Immigration reform: no longer so controversial, but not inevitable either". ws-02646: sheet Headline "Flam"; page headline "Republicans Excluded From Governor’s And Legislators’ State Budget Negotiations". Overwrite? (blanks-only rule)

### M. Word counts
- 267 existing sheet counts differ >20% from the cleaned text (mostly counts that included comments/clutter; KQED script dumps). Existing Chinese/Japanese counts were made by spaces (e.g. ws-01499 = 34 for a ~2,000-character article). New fills count Chinese/Japanese by character and Korean by spaced word. Allow overwriting the existing counts with the same method?

### N. Headlines differ
- 195 rows where the page headline differs from the sheet (web vs print/updated headlines). Recorded only; no action unless you want the page headline somewhere.

### O. Byline fills skipped
- Byline line on the page is a CMS user or placeholder: ws-01673 "healthadmin", ws-01675 "Source Author", nb-02382 "swilliams". Left blank.

### P. Word-count fill conflicts
- Two buckets proposed different counts for the same row (row has two library copies); left blank: pq-00096 Word count: 989; 925; pq-00211 Word count: 1446; 1333; ws-01932 Word count: 598; 572; ws-02862 Word count: 571; 591; ws-02871 Word count: 437; 629; ws-02904 Word count: 660; 694

### Q. Language label
- ws-01959 Nowruz Media: sheet "Arabic/Persian", text is Persian (Dari); the sheet uses both "Arabic/Persian" (7 rows) and "Persian" (1). Merge the labels? Also new value "Kyrgyz" (ws-02928 Forum Daily) and "Armenian", "German", "Hindi", "Italian" (Vinetur) enter the Language list via corrections.

### R. Housekeeping
- Desktop/Tracker library/_tmp_clean6/ (b6.tgz 11 MB, bundle6.tgz, bundle6b.tgz) is cleaning scratch left by bucket 6; safe to delete (or move to _to_delete).

### S. Rows whose sheet data may itself be wrong
- The 12 Times of Israel rows sent to RETRY (ws-03185, 03854, 03858, 03594, 03483, 03700, 03653, 03711, 03699, 03688, 03702, 03853) have sheet headlines that match the unrelated saved pages (Sudan clashes, lockdowns…). A retry may find the same page; the rows may need re-checking or deleting. Same for ws-02163 (New Times "Summer Guide 2025"), ws-03665 (Acorn issue 2020-10-22) and ws-03364 (Excelsior "Sitemap").

### T. Bucket flags I could not confirm (no action, FYI)
- LA Wave ws-02009/00294/00484/02699/01707/03517/00715 are complete (~560–1,000 words) and name Jesse Gabriel — bucket 4's "truncated" flag came from its parser (unclosed <p> tags); confirmed in Chromium. Also name him: NPR ws-00543, pq-00300 (Moderate Voice), ws-03471 (Environmental Voters), GovTech ws-03271 (full 970-word article, not paywall-only). FoodBev ws-01765: only the h1/byline are template placeholders ("Post Headline"/"Post Writer"); body is the real article. Korea Daily ws-03257/ws-01657: article plus menus in one block (not cut). Adelante Valle: the 5 removed tag-list items named Gabriel, but every Adelante copy still names him in the text (no tag-only rows).

### U. jg- files (FYI)
- 22 old-tracker files named jg-xxxxxx map to several rows each (rename_ambiguous); compared with the best headline match, no fills taken. jg-a6dd2b (LAist page, no Gabriel) is in error_copies.

## Method notes

- Word count fills: Chinese/Japanese text = number of Han/kana characters + space-separated non-CJK tokens; Korean = space-separated words; all other languages = the bucket's whitespace count of the cleaned body (header lines, headline excluded). 3 CJK fills recomputed this way.
- Gabriel checks were re-run on the cleaned copies (Jesse Gabriel in Latin script with context, or a transliteration: 가브리엘, Габриэл, גבריאל, 加布里埃尔 …); other Gabriels (Ugarte, Petek, Dillard, Lerner) excluded. 3 blank cells the buckets proposed as "No" actually name him (CBS ws-03184, ws-03192 transcripts; CNN ws-03817) → filled "Yes".
- Language corrections skip rows whose copy is a different article (those are in error_copies; Language untouched).
- Error copies on nb- rows (nb-00327, nb-02019) replace only File name 2 (the web copy); the NewsBank PDF in File name stays and Saved Copy? stays Yes.
