# agent-blankfill — blank Medium / domain Outlet fills (Sammy: Clips "Format" filter shows a blank option, 22 stories)
Rules: no Exa, no publishing; one rule-7 write (token); helpers in work/tmp_agent-blankfill/.
## Log
- Read README r7, DECISIONS (fill-blanks-only, NewsBank outlet names, OUTLETRULES-v1, writer token), CONTRACT, outlet_rules.json.
- Audit: today's rows = coverage_current vs archive/2026-10-28/work/coverage_pre_reltab.xlsx (start of 2026-10-28): 365 new rows (47 TinyFish Originals, 303 TinyFish Reprints, 14 podcast, 1 people search) + 779 changed rows. 29 Originals with blank Medium (23 TinyFish, 6 Tracker reprint list); 144 new Reprints with blank Medium too.
- plan.py -> plan.json (293 cell changes over 454 scoped rows).
- Token taken (read "none").
- Staged master sha b90fc791… = expected. Backup Backups/"AJG Coverage - NewsBank BACKUP before blank-field fills 2026-10-28.xlsx" (sha b90fc791…, on the Mac).
- write_wb.py: 293/293 expected cells changed, 0 unexpected (diff over 715,122 cells). Originals rebuilt (4,493 rows, 30 rows updated). The 14 mirror mismatches are pre-existing podcast Publisher-link hyperlinks (same 14 in the input).
- First commit attempt: "fetch or write failed" (Mac unchanged, b90fc791). Retry with the same expectedMtimeMs 1793161224676 succeeded. Mac sha 5b073e81a02119a229aba4b124db2f25f4749b55b294017b78f88f01a4d20690 = local. coverage_current.xlsx updated (pre copy coverage_pre_blankfill_b90fc791.xlsx). Token released ("none"). DECISIONS line appended (pre-edit copy tmp_agent-blankfill/DECISIONS.pre.md). rootfix.md written.
## Self-check
- Originals with a blank Medium: 29 → 0. 160 blank Medium remain, all old "Tracker reprint list" Reprint / Reprint (unverified) rows of outlets outside today's scope.
## Open for coordinator / Sammy
- 03875 "Brentwood News" (old reprint-list row, no link): Medium left blank. The 5 TinyFish "Brentwood News" rows (09750, 09925, 09927, 10074, 10078) are thepress.net = The Press, Brentwood (Contra Costa County), but they carry Outlet "Brentwood News" + county "Los Angeles", copied from 03875. Existing values left as they are; this needs Sammy's call.
- 09772 Daily Sundial: Date 2026-11-18 (in the future); the page says October 8, 2025. Not overwritten (not blank).
- 07430 One Commune (Apple Podcasts) is the same episode as 07429 One Commune (s02212): same title and date. It should be a Reprint of s02212 or removed.
- 05222 "csun.edu" (Reprint unverified, no link): can't tell CSUN Today from Daily Sundial, left as is.
- Reach blank on 51 scoped Originals: brand-new outlets with no consensus (Daily Kos, SD Voice & Viewpoint, Brentwood News, KESQ, KCCI, UCLA Newsroom, CSUN Today, the 14 podcasts…), plus LA Times 01973/03117 (mixed). Location/Publisher of brand-new outlets also left blank (no rows to copy).
- Year blank on 3 (09773 Lake County News and 09774 Produce Market Guide are undated; 02356 KSBY has no Date). Topic blank on 02356 KSBY and 02207 Consumer Reports (need a rating). Edition blank on the 14 podcasts and the 6 old reprint-list Originals (that source's convention).
- Georgia Public Broadcasting got "Online news" (precedent: Houston Public Media, Northern California Public Media). Weeklies (Pleasanton Weekly, Chico N&R, SD Voice & Viewpoint, Turlock Journal) got "Newspaper".
## Write 2 (Sammy's 3 decisions, via coordinator)
- Waited for agent-avshow to release the token, then took it. Master sha b395595a… (avshow's commit) = staged copy. Backup "…BACKUP before Brentwood-Sundial-OneCommune fixes 2026-10-28.xlsx" (b395595a…).
- write2.py: 23/23 expected cells, 0 unexpected over 716,019 cells. Same 14 pre-existing podcast hyperlink mismatches in the mirror. Originals 4493 → 4492 (07430 left the tab). # of reprints recomputed on s00051, s00099, s02212, s04716, s04738, s04746, s04748: all unchanged. The AV tab has no row for 07430 (only 07429, s02212). 07430 had a blank Medium until write 1 set Podcast, so the avtab backfill skipped it. An AV row for it is still open for agent-avtab/avshow.
- Committed (expectedMtimeMs 1793162185813). Mac sha d00118c583fe4c9807bf514a57408e504d7296e7808af81061a8ee457fad9972 = local. coverage_current updated (pre copy coverage_pre_blankfill2_b395595a.xlsx). Library 2026/ws09772o-s04738.html → 2025/ (+ _original_html, work/html_clean). Token released. DECISIONS line added. keep_separate patch: work/tmp_agent-blankfill/outlet_rules.keep_separate.patch (+ outlet_rules.proposed.json).
- Note: 09772's saved-copy header line still reads "csun.edu · 2026-11-18". The next copy regeneration or clean pass should fix it.
