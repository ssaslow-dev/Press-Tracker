# agent-pressrelease: pure press releases (DECISIONS 2026-10-27)

Status: DONE (fresh run; the earlier attempt's work/tmp_press_releases/ was not used)

## Outputs
- work/out/press_releases.csv: every Coverage row (9,544, old IDs): old_aid, sid, outlet, headline, verdict, confidence, reason
- work/out/pressrelease_queue_items.json: 71 borderline items, same shape as the other categories (cat "pressrelease", key = old aid, ids pr-000 to pr-070, options "Press release: leave out of tracker (Press release = Yes)" / "Not a pure release: keep in tracker"; 42 propose release, 29 propose keep)
- Live queue: items/13-pressrelease set (version 1, read back, 71 items). No other docs touched. The page shows unknown categories under their key ("pressrelease"), so it was not republished. Optional cosmetic: add `pressrelease:{label:'Press releases',note:'...'}` to CATS at the next republish.
- work/out/press_release_build.md: build_data.py change spec, apply_fills.py block (including the fix to apply_fills' verify, which asserts unchanged sheet shape and would fail on a new column), and the originals note
- work/out/press_release_originals.csv: 10 stories whose Original is a release (or borderline) but which have non-release rows, with a suggested new original
- Helpers: work/tmp_agent-pressrelease/ (load, feats, sim, pairs, classify, outputs)

## Counts
yes 497 (348 Original, 149 Reprint; 428 high, 69 medium) · borderline 71 · no 8,976.
Yes by source: release wires 274 (TNS 166, US Fed News 41, PR/Hispanic PR Newswire 19, PublicNow 16, TendersInfo 13, etc.); outlet labels 106 (SDJW "(Press Release)"/"Preceding provided by", CC News/ECT "Press Release by", Sierra Sun Times "Source: <office>", Asian Journal "(… Office Release)", Gabriel release boilerplate on Van Nuys News Press); text ≥85% contained in a release copy with no reporter byline: 33; manual (org release pages, Armenian Caucus/ANCA-WR announcements, etc.): 83; URL: 1.
335 stories consist entirely of 'yes' rows and drop out of the tracker.

## Method
Outlet + URL + headline + saved texts (texts/nb, texts/tracker, artifact_files/articles, fetch_cache; no web). Seven-gram containment against the wire release texts, plus an all-pairs near-duplicate pass. Release markers read by hand for ~550 candidate rows.

Not counted as releases: CE Noticias Financieras (news syndication), TCA, AP, Center Square, JTA/JNS, City News Service, Bay City News, Food Safety News staff reporting, org blogs/op-eds (CRPA, NSSF, CJAC, think tanks), voter guides, scorecards. Contra Costa News and East County Today write-ups without the "Press Release" label were checked one by one.

## Self-check
- 9,544 rows in = 9,544 CSV rows, unique old_aid. Verdicts limited to yes/no/borderline.
- Queue doc read back: 71 items, each key in the CSV as borderline.
- Spot fixes made during review: the SDJW rule wrongly caught "Preceding provided by JNS.org" (news, now no), plus its JNS/Algemeiner copies. ws-00629 is a CR press_release URL but its saved copy is a Food Safety News article (now borderline). nb-01553 Dan Flynn is now no.
- Rows with no saved text: only outlet/URL/headline evidence. Five SCNG rows share the headline of a Caucus Foundation announcement (nb-03077 to nb-03081): borderline, low.

## For Sammy / coordinator
- 10 stories have a release Original but non-release rows (table in press_release_build.md §3). Re-picking the original should go through the T28 regroup approval, because those rows are mostly rewrites that would split off under the 90% rule.
- Calls Sammy may want to check: California Courier and Asbarez Armenian Caucus Foundation / ANCA-WR announcements marked yes (medium); California Apartment Association own-site posts (10) and Common Sense Media posts (2) put in the queue rather than auto-decided.
