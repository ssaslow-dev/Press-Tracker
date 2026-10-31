# agent-clean-1 — T32 bucket 1 (350 files, 60 outlets; Politico 167)

Status: DONE (2026-10-27)

## What was done
- Staged all 350 originals to the container (tmp_agent-clean-1/orig). Built `clean_lib.py` (rule-based, per outlet; pure function) + `run_container.py` (header decisions from coverage_current.xlsx, safety checks, final data checks, logs).
- Mac execution: shipping the code to the Mac was impractical (no stageable scratch path, ~19 KB base64 bundle), so I used the prompt's fallback: one device_bash run backed up the 243 files to change into `Tracker library/_original_html/<year>/` (243 made, 0 already there, each byte-verified) and printed sha256 + mtime. All 243 Mac originals matched the staged copies. Cleaned files then written with device_commit_files (5 batches, expectedMtimeMs on each, 0 rejected).
- Verified after writing: the combined sha256 of the 243 live files equals the container output (0c4f0618…), and the combined sha256 of the 243 backups equals the originals (a3081255…).
- Mac scratch: only ~/tmp_agent-clean-1 (outside mnt) plus one unused tar in ~/mnt/outputs. Nothing was written to the Desktop library except the cleaned files and the backups.
- work/html_clean/<stem>.html: all 350 (243 cleaned, byte-identical to the Mac; 107 unchanged originals). No work/library_new files in this bucket.

## Results
- 243 cleaned, 107 unchanged, 0 kept for review. One file went to manual review: Korean Journal ws-02336 would have lost 41% of its words. I read it: the removed text was only site nav, weather, a search widget, tags and the footer, and 가브리엘 is kept. Applied.
- Safety: no removed text contains Gabriel in any script, h1 unchanged everywhere, no block of 40+ words removed except vetted boilerplate: POLITICO ads ("Want to make an impact?", "CALIFORNIA POLICY IS ALWAYS CHANGING", "POLITICO Pro/Advertising Solutions") and the AV Press comment rules ("Keep it Clean…").
- Main clutter removed (block counts): POLITICO partner ads 75, POLITICO California Pro ads 72 (incl. trims of the ad text where ProQuest PDF text runs it into the end/start of a paragraph), generic ad/widget residue 56 (Advertisement, Share, Trinity audio, ProQuest page footers), comments plus "more stories" 45, newsletter sign-up prompts 29, related posts 26, AV Press comment and newsletter widgets 25, Newsweek "…" placeholders 23, tag/share/footer blocks, site nav, the Newsweek search promo, ABC7 "MORE:" links, NBC LA promo boxes, KNX social and podcast promos, a STAT+ paywall, and others. About 14.6k words removed in total.
- Kept on purpose (when unsure, I kept it): Politico "Got a tip", "WANT A SHOUT-OUT FEATURED?", "Available free through…", "POLITICO Pro subscribers can read more here — <author>", "IT'S OUR PARTY…fireside chat"; AV Press tag lists (they include "Jesse Gabriel"); author contact and bio lines; "Read the original article" and source lines; Newsweek Bulletin FEATURED CONTENT; Twig24 ⓒ line; CalMatters and Common Sense boilerplate.
- Metadata header: 137 lines removed from 78 files (outlet·date and URL lines that match the sheet). "Saved YYYY-MM-DD" lines kept (no column). Lines that differ from the sheet were kept and listed.
- Outputs: work/out/html_clean_log_1.csv, html_checks_1.csv (90 rows: word count 31, header outlet 19, headline 16, Gabriel mention 10, language 6, byline 4, header date 2, header URL 2), html_meta_fills_1.csv (209 rows: Word count 189, Mentions Gabriel 15, Author/byline 3, Language 1). Word count is checked with a 10% tolerance and skipped for Chinese; excerpt copies get no Word count fill.
- Spot check: 10 random cleaned files rendered with Playwright (ws-03367, nb-00750, ws-01439, nb-00332, ws-02336, pq-00306, pq-00251, pq-00270, pq-00194, ws-02335). Headline, byline and body are intact and none of the clutter patterns remain. Screenshots are in tmp_agent-clean-1/shots. Small leftover: FoodBev ws-01439 ends with the tag text "IngredientsFood".

## For Sammy / coordinator
- Gabriel mention, sheet "No" but the saved text names him in another script (Yes under the new rule): ws-02255 (both copies, Armenian), ws-03212 and ws-01407 (Russian), ws-03213 (Nur.kz), ws-01763 (Kapital.kz), ws-02336, ws-02469 and ws-02451 (Korean), ws-02759 (Hebrew).
- Sheet Language says English but the text is in another language: ws-02255 (Armenian, both copies), ws-03212, ws-01407, ws-03213 and ws-01763 (Russian).
- FoodBev ws-01765: the saved page's h1 and byline are template placeholders ("Post Headline" / "Post Writer").
- ws-02160 (sheet: Gun Owners of California): the saved page is a One Armed Man repost by Greg Raven, not the GOC original.
- Sentinel nb-01006 and nb-02516: the sheet byline Cora Jackson-Fossett differs from the article bylines (Lila Brown, Antonio Ray Harvey).
- Date conflicts: nb-02960 (sheet 2022-10-25, header 2022-10-24); ws-02241 (sheet 2025-03-19, plain copy's header 2025-03-20).
