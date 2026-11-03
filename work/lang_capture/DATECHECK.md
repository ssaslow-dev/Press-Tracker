# Date-limit check on TinyFish search (2026-11-03)

29 searches, each with and without `after_date` (and `before_date` once), query shapes copied from the Update button (code/tracker/41_update_search.js). Known stories taken from work/coverage_current.xlsx.

## Result
The date filter does not suppress results in general. It drops results the index has no date for, and that is what returned 0 in the one shape that failed.

| Shape (as the button sends it) | With date | Without date | Verdict |
|---|---|---|---|
| LA TV `"Jesse Gabriel" (site:ktla.com OR site:abc7.com OR site:nbclosangeles.com OR site:cbsnews.com/losangeles)`, after 2026-09-20 | 1 (KTLA 2026-09-28, tracked) | 10, six of them 2018-2025 | works; date is what narrows to the window |
| same, after 2025-10-01 | 7, all in window (KTLA, ABC7 x3, NBC LA x2) | 10, mostly older | works |
| Valley `(site:valleynewsgroup.com OR site:vannuysnewspress.com OR site:sanfernandosun.com OR site:dailynews.com)`, after 2026-09-01 | 10, all in window incl. sanfernandosun 2026-09-09 and dailynews 2026-09-29 | 10, five older than 2025 | works |
| `include_domains` ktla,foxla,abc7,nbclosangeles + date, after 2026-05-01 | 5 incl. foxla 2026-05-08 (tracked) | not run | works (include_domains + date is fine here) |
| YouTube `"Jesse Gabriel"`, include_domains youtube.com, after 2025-06-01 | 10 relevant videos incl. 5iNsMhTGynA (tracked 2025-06-25) | 7, mixed with channel pages and off-topic | date better |
| YouTube, window 2025-03-01..04-01 | 6, incl. the 2025-03-19 videos LhQjXv0BZ4M and H4nhBSNZkxs | not run | works |
| YouTube, window 2025-06-20..06-30 (after + before) | 2, incl. 5iNsMhTGynA | not run | works |
| YouTube `"Assemblymember Gabriel" OR "Assemblyman Gabriel"`, after 2025-06-01 | 7, all Gabriel Rodriguez (other states) | 10, includes Jesse Gabriel videos | no better with date: this query is weak either way |
| YouTube `"Jesse Gabriel" 天下衛視`, after 2024-08-01 | 1 (qcn_agBF074) | 3 (adds two undated Sky Link videos) | date drops undated videos: slight loss |
| **Podcast pages** `(site:podcasts.apple.com OR site:open.spotify.com/episode OR site:iheart.com/podcast)`, after 2026-01-01 / 2026-04-01, page 0 and 1 | **0** | 10 (Commune with Jeff Krasno, iHeart shows) | **suppressed** |
| `include_domains podcasts.apple.com` + after 2026-04-01 | **0** | not run | **suppressed** (Apple Podcasts pages have no date in the index; the tracked 2026-04-29 episode never comes back) |
| `include_domains podcasts.apple.com,iheart.com`, after 2025-01-01 | 3, all iHeart station pages (dated), no Apple | not run | Apple missing |
| Chinese `"Jesse Gabriel" OR 加布里埃爾 OR 加布里埃尔 (site:worldjournal.com OR site:singtaousa.com)`, after 2026-09-01 | 3: Sing Tao 2026-09-14, World Journal 2026-10-01, Sing Tao 2026-10-25 | 4, all Sing Tao e-paper PDFs/pages; missed the World Journal and 10-25 stories | date better |
| Chinese `Jesse Gabriel 加州眾議員` include_domains worldjournal,singtaousa, after 2026-09-01 | 2 (WJ 10-01, Sing Tao 10-25) | not run | works |
| Korean `제시 가브리엘 (site:koreadaily.com OR site:koreatimes.com)`, after 2026-06-01 | 4, three off-topic (a football player, a church hall) | 10, many tracked-style stories 2022-2025 | works; unquoted name is noisy. Quoted `"제시 가브리엘"` returns 1 clean hit |
| Korean include_domains koreadaily,koreatimes + date | same 4 | not run | works |
| Hebrew `ג'סי גבריאל` include_domains hebrewnews.com + after 2026-09-01 and the `site:` form | 1 each: hebrewnews.com/article/76966 ("8 days ago", about 2026-10-26, not yet tracked) | not run | works |
| Armenian-American `"Jesse Gabriel" (site:asbarez.com OR site:massispost.com OR site:mirrorspectator.com)`, after 2025-01-01 | 5 Asbarez pages (2025-03 to 2026-10) | not run | works |

Result dates come back as "Sep 28, 2026", "8 days ago" or missing; `tfDate` already reads the first two.

## What the filter does
- It keeps only results that have a date in TinyFish's index. Pages with none are dropped. Apple Podcasts episode pages have none, so the whole podcast group returned nothing, in both `site:` and `include_domains` forms.
- On every shape with dated pages (TV, news, Chinese, Korean, Hebrew, Armenian) it helps: it pushes the window's stories into the top 10 instead of leaving them behind years of older ones.
- YouTube results rarely show a date but are filtered anyway; the date still narrows to the window (known 2025 videos came back in their windows). One undated Sky Link segment is lost with a date; accepted.

## Change made (DATEFILTER-v1)
- The podcast-page search is sent with no `after_date` (group flag `nodate` in code/recall_sources.json, plan item `noDate`, handled in the new `tfInput`). Results older than the run's since date are dropped afterwards by the result's own date (existing `sinceKeep`); a result with no date is kept and goes through the normal candidate checks.
- Nothing else changed: TV, Valley, YouTube, ethnic and the new language-press searches keep the date.
- Tests: build/tests/recallfix/test_recallfix.js (`tfInput` sends no after_date for the podcast search, manual Since or not; keeps it for LA TV, Chinese and YouTube).

## Not tested
Spotify episode pages and iHeart `/podcast` pages through the OR form with no date (the undated query returned iHeart episodes, so they are indexed). Real run yield of the undated podcast search is unknown: expect old results, which the since filter drops.
