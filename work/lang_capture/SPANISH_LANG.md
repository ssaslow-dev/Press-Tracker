# Non-English capture test: Spanish outlets direct (A) and language-filtered search (B)

Run 2026-11-03. About 55 TinyFish searches (limit 60) and 6 URL fetches (limit 25; one fetch blocked as bot_blocked and not bypassed). No workbook or code edits. Data: `spanish_lang_finds.csv` (116 rows, despite the name it also holds zh/ko/vi/pt).

## Two findings about the tools that change the plan
1. **Date windows (`after_date`/`before_date`) are unreliable in web mode.** With `include_domains`, windowed queries often returned 0 results for outlets that have dozens of hits (sanfernandosun.com returned 0 for every window, yet 10 hits undated, including a 2026-09-09 story). They work in `domain_type=news`. So I searched undated and used page 0 and page 1, and judged the year from the returned date.
2. **`language=` alone does not filter.** "Jesse Gabriel" with language es or vi returned English results (his own site, Wikipedia, CalMatters). It only gives non-English results when the query itself contains native words ("asambleísta", "dân biểu", "加州眾議員", "주하원의원"). And `domain_type=news` with `include_domains` ignores the domain list. Domain-restricted web searches with native-language words were the most productive form.

## Method A: Spanish outlets searched directly (about 24 searches)
- La Opinión (4 undated plus windows), San Fernando Valley Sun / El Sol (4), Adelante Valle on ivpressonline.com (2), Telemundo 52 plus telemundo.com (2), Univision (1), El Diario NY (1, combined with EFE and LA Times), CalMatters en español (3).
- EFE and efe.com returned nothing. LA Times en Español surfaced only through the Method B news search.
- **Hits: 68 distinct URLs naming or about Gabriel. Already tracked: 67. Maybe: 1 (Univision AB 587, 2022 signing; same story as a tracked Univision item under a different URL and headline). New: 0.**
- Per year of the hits: 2021: 4, 2022: 14, 2023: 15, 2024: 22, 2025: 6, 2026: 4.
- The tracker is already complete for these outlets. Matching was by URL, then headline similarity at 0.85 or higher, so dates differ by a day in places but the story is the same.

## Method B: language-filtered and native-word searches (about 31 searches)
- es (news mode, three windows plus extra topic queries): 13 distinct hits. 9 tracked, 3 untracked and unconfirmed (AB 1264 stories on El HuffPost España, El Latino, Diario Constitucional, snippets empty and not fetched), 1 Spanish-language Governor's budget release (Gabriel named only in the list of bills signed; list-only).
- zh (news mode, plus worldjournal.com and singtaousa.com direct): 17 hits, 9 tracked, 8 new.
- ko (Korea Daily and Korea Times direct, plus news mode): 11 hits, 9 tracked, 2 new (one is a same-day sibling URL of a tracked story).
- vi (nguoi-viet.com direct): 6 hits, all tracked. The news-mode vi query found nothing useful.
- pt: 1 hit, a personal blog repost. Excluded under NOBLOGS-v1.
- **New or untracked, by confidence:**
  - Verified by fetch or by snippet naming Gabriel (7): World Journal 2025-09-01 (AB 1264), World Journal 2025-10-10 (AB 1264), World Journal 2026-06-19 (ethnic-media letter addressed to Gabriel), World Journal 2026-10-01 (AB 2244), Sing Tao 2026-10-25 (Prop 2, Gabriel quoted), NTD Taiwan 2023-04-15 (AB 418, Gabriel on camera), Chosun Daily US 2023 (AB 418; page bot-blocked, snippet names him).
  - Unconfirmed (5): 商傳媒 2026-09-24, Sing Tao 2026-01-08 (AG race, snippet names him), the three Spanish AB 1264 pieces (counted above under es).
  - Borderline: the Governor's Spanish budget release (list-only, a government release rather than a news story) and Korea Times 1541507 (same story as tracked 1541427).
- **New per year (zh/ko/vi/pt):** 2023: 2; 2025: 2; 2026: 5. Spanish: 2025: 3 unconfirmed; 2026: 1 (the govt release).

## Is the 2025-26 Spanish drop real?
Mostly yes. Direct-outlet Spanish hits fall from 22 in 2024 to 6 in 2025 and 4 in 2026, and every one of them was already in the tracker. The drop is in what these outlets publish and what the search index holds, not in a gap in the tracker. Of the 4 outlets that still carry Gabriel in 2025-26 (Telemundo 52, Noticias Telemundo, San Fernando Valley Sun, La Opinión), all hits were tracked. Caveat: the index is thin for late 2025 and 2026, so a few unindexed stories could still exist. Neither method found any Adelante Valle story after 2024 (the tracker has three from 2025).

## What to add to every Update run
Spanish direct outlets add nothing the tracker lacks; keep the NewsBank route and skip them. The gain is in the Asian-language outlets, where the new items sit.
1. **Chinese:** one search per run, query `Jesse Gabriel 加州眾議員` with `include_domains=worldjournal.com,singtaousa.com` (pages 0 and 1: 2 searches). This found 5 of the 8 new items. Add epochtimes.com in a second query only if needed.
2. **Korean:** one search, `제시 가브리엘 주하원의원`, `include_domains=koreadaily.com,koreatimes.com` (1-2 searches). Found 9 hits, 1 near-new.
3. **Vietnamese:** one search at `nguoi-viet.com` (1 search). All 6 hits were already tracked, so run it monthly rather than weekly.
4. **Spanish:** one native-word news search (`asambleísta Jesse Gabriel`, `domain_type=news`, dated to the update window), 1 search, as a safety net for Spanish outlets not in the list. It surfaced Excelsior, Abasto and LA Times en Español, all tracked.
5. Do not rely on `language=` alone, and do not rely on date windows with `include_domains`. Use `after_date` only with `domain_type=news`.
- Cost per run: about 5-7 searches. Fetch only to confirm that Gabriel is named when the snippet is empty (Sing Tao and World Journal snippets are often empty in news mode).
