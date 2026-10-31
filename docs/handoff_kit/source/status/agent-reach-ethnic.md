# agent-reach-ethnic — done (2026-10-27)

Scope: Reach changes per DECISIONS 2026-10-27 (Spanish-language / Ethnic split; International; multi-tag Reach). No workbook or Mac writes. Only external writes: review-queue artifact (items/1-reach, new items/9-relabel, one CATS entry on the page).

## Outputs
- lib/work/out/reach_relabel.csv — 205 rows (outlet × old reach × new tag set), columns: outlet_sheet, outlet_display, old_reach, old_source (existing/proposed), new_reach (primary), new_reach_tags ("; "-joined, primary first), basis, confidence, stories (Original rows), group, note, in_coverage_sheet, story_ids.
- lib/work/out/reach_proposals.csv — updated in place (53 of 241 outlets changed; `reach` now holds "; "-joined tags; new column reach_before). Backup: reach_proposals.before_ethnic.csv.
- lib/work/out/reach_tracker_changes.md — REACH_ORDER, color-slot map, multi-tag edits for js_merged.js.
- Queue: items/1-reach v1→v2 (241 items, 10 options, multi:true, proposed as list; 0 left with old label). items/9-relabel v1 created (151 items). Page republished as Version 5 with only the `relabel` CATS entry added. Readback: both docs identical to what was written.
- Scripts: lib/work/tmp_reach_ethnic/ (rules.py = every outlet call; classify.py; build_queue.py).

## Method
Outlet = sheet Outlet of the Original row (joined via Story ID); old reach = tracker (data.json) reach, else sheet Reach, else proposal. Publisher-link domains used to place outlets (.kr, .ir, .ru, .co.il, singtaousa, koreadaily, etc.). Language column is unreliable: Vietnamese is tagged "Portuguese", Sing Tao Chinese tagged "Korean", Epoch Chinese tagged "Japanese" (flag for 4-language).
Row-level only: ABC7, AP, SFV Sun, SB Independent, KFN (only their Spanish "S&E" rows move); Epoch Times (Chinese rows → Ethnic + National; es.theepochtimes rows → International; English stays National).

## Counts (stories = Original rows; existing + proposed)
- Spanish-language: 29 outlets / 137 stories (all from old S&E)
- Ethnic: 50 outlets / 238 stories (21 outlets/104 stories from old S&E; rest from CRL/National by language)
- International (any tag): 123 outlets / 304 stories (incl. 15 Jewish press + International, 18 Trade + International)
- Outlets with 2+ tags: 84 (23 in 1-reach, 61 in 9-relabel)

## Saved decisions using old labels (not changed)
reach-001 California Courier ("Spanish-language & ethnic"; note asked for the split → treat as Ethnic), reach-013 CE Noticias Financieras: English (now proposed International, low), reach-022 Hispanic PR Newswire (now Spanish-language).

## Questions for Sammy
- Israeli general press (Ynet, Makor Rishon, Srugim, Arutz 7, 7 Kanal, Hebrew News) proposed Jewish press + International by the Times of Israel / JPost precedent.
- Foreign trade press and release aggregators (Mondaq, Monitor Worldwide, TendersInfo, M2, ENP, FoodBev, Just Food...) proposed Trade + International.
- Guardian (4/5 "US news") kept National; Daily Mail (dailymail.com) kept National; NewsBank MailOnline → International.
- Not changed, flag only: La Nación 9 National rows now International; Yahoo News has a few tw/hk/sg rows; Spanish stories in National outlets (HealthDay en Español, CNN) untouched; SFV Sun could carry Spanish-language as a second tag (17 Spanish rows); Lechaim/Jewish.ru moved to Jewish press + International.
