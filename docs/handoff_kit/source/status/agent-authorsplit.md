# agent-authorsplit (T30) — status log

## Done (2026-10-27)
- Parser `work/tmp_agent-authorsplit/authorsplit.py` (pure functions, reusable): `parse_byline(byline, outlet)`, `split_fill_row(T24 row, outlet, sheet_byline)`, `author_key(name)`.
- Runner `run_split.py L` → `work/out/author_split.csv` (5,989 rows: 5,459 sheet bylines, 520 sheet bylines written from T24 (T24's structured split used, keeps titles), 10 T24 rows not yet in the sheet), `work/out/author_split_review.json` (49 items, cat "15-authors"), `work/out/author_variants.csv`.
- T24 merge: out/author_fills.csv (530 rows). ws-02922 → Joyann Jeffrey / "Trending News Reporter" (title recovered from the glued evidence text). Rerun run_split.py after T24's TinyFish resume.
- Patch `build/author_columns_patch.md` + anchor scripts (patch_apply_fills.py, patch_build_data.py, patch_authors_js.py) + author_columns.py. Tested on copies only; nothing shared edited.

## Self-check
- n_authors: 0 → 51 (role-only bylines: Contributor 22, Contributing Editor 10, Staff 9, Staff Writer 4, Special to … 4, Editor 2), 1 → 5,255, 2 → 554, 3 → 89, 4 → 21, 5 → 12, 6 → 2, 7 → 1, 8 → 4. Max 8 → columns Author 1..8 + Author title.
- Confidence: high 5,882, medium 41, low 66 (→ 39 grouped low items + 10 "same person?" items in the queue).
- Editorial boards: 56 rows, 23 names (Daily Breeze, Inland Valley Daily Bulletin, Long Beach Press-Telegram, LA Daily News, Pasadena Star-News, Redlands Daily Facts, The Orange County Register, The Press-Enterprise, The Sun ×4 each; San Gabriel Valley Tribune, Whittier Daily News ×3; The Sacramento Bee, Yahoo News ×2; CALO NEWS, California Local News, East Bay Times, Excelsior, Inyo Register, Los Angeles Times, San Francisco Chronicle, Santa Cruz Sentinel, The Mercury News, The Monterey County Herald ×1).
- 30 random parses checked by eye: all correct. Spec patterns unit-checked (t.py).
- Workbook insert test, apply_fills dry run, migrate_ids on the result, build_data, browser 16/16 + existing display 18/18: see build/author_columns_patch.md §4.

## Update — Sammy's answer applied (reprint boards → ORIGINAL outlet)
- authorsplit.py: `originals_by_story()` + `board_outlet()`; run_split.py and author_columns.py name a reprint's editorial board after the Original row of the same Story ID (tracker-style name). No reprint lacked an Original outlet (fallback list empty).
- Regenerated from coverage_current.xlsx (05:09:36, the T14a file): 46 rows changed, all editorial-board reprints, nothing else. author_variants.csv unchanged; review items 50.
  - jg-00334 (12 SCNG reprints) → "Excelsior: Orange County Register weekly Editorial Board": its Original is the Spanish Excelsior weekly. Likely a grouping problem for T28, not an author one.
  - jg-01584 (10 reprints incl. The Sacramento Bee nb-03809) → The Orange County Register Editorial Board. A Bee reprint of an OCR editorial is worth a look.
  - jg-00615 (12) → The Orange County Register; jg-00938 (11) → Daily Breeze; jg-00959 Mercury News → East Bay Times; jg-00116 California Local News → CALO NEWS; ws-00052 Yahoo → The Sacramento Bee; ws-02598 Yahoo → Los Angeles Times.
- Re-tested against current build_data.py / js_merged.js (05:10:51) / apply_fills.py: all 3 patch scripts apply cleanly; parser cases same; apply_fills dry run 0 unexpected changes; migrate_ids 0 problems; build_data identical apart from the 2 new fields; browser 16/16; display suite 18/18. Copies only, no writes, no publish.

## Questions for Sammy
1. (answered 2026-10-27: original outlet's board)
2. One title shared by several authors ("A and B; Staff Writer") is written once ("Staff Writer"), not repeated per author. OK?
3. "X / Associated Press": X is the author, "Associated Press" goes in Author title (affiliation). No such byline in the sheet today.
4. Honorifics moved to the title: "Rabbi Lynn Gottlieb" → Lynn Gottlieb / Rabbi (2 rows).
5. Same-person variants: 18 differ only by case/accents/periods/middle initial → tracker shows one entry (most common form), sheet keeps each byline as written; 10 spelling variants (Haven Daly/Daley, Antionio/Antonio Ray Harvey, Alexei Kosoff/Koseff, Beau Yarbough/Yarbrough, Claudia Boyd Barrett/Boyd-Barrett, Kate Rodgers/Rogers, Nic/Nick Robertson, Tara Nguyen/Trân Nguyễn, The Triplicat/Triplicate, California Playbook/… PM) are NOT merged — in the queue.

## Update — group bylines vs article labels (Sammy, DECISIONS 2026-10-27)
- Rule: a byline naming a GROUP OF PEOPLE is an author. With no outlet in it, it's named "<Outlet> <Group, Title Case>", using the board outlet rule (the Original's outlet on reprints): Staff, News Staff, Editorial Staff/Team, Editors, Newsroom, Staff and wire reports, Staff report(s), Redacción. "<Org> Staff" bylines are kept, with the group words in Title Case. A KIND OF ARTICLE (Editorial, Opinion, Our View, Commentary, Letters to the Editor) gives blank Author columns and a blank title. A singular role (Staff Writer, Editor, Contributor, Special to …) stays title-only.
- Re-checked the 56 board rows and every byline with editorial/opinion/editor/board: all 56 credit "Editorial Board", so they stay boards. No sheet byline is a pure article label (0 become blank).
- Regenerated author_split.csv: 19 rows changed. 9 rows "Staff" become 0→1 author (Los Angeles Business Journal Staff ×6, Pasadena Independent Staff ×2, Lassen County Times Staff ×1; the last 3 are HeySoCal reprints named after their Original). 6 rows "Staff report/Report" become "Daily News Staff Report" ×5 and "NBC Los Angeles Staff Report" ×1. 4 rows are case-only changes ("EdSource staff" → "EdSource Staff", etc.).
- Group authors by type: Editorial Board 56, Staff 70, Editorial Team 7, Staff Report 6, News Staff 3, Newsroom 1 (143 rows; 68 on reprints).
- Still ambiguous, kept as given and listed: "Knock LA Editorial" (ws-03671, ws-03712). Is that an article label or a group credit?
- n_authors 0 is now 42 (Contributor 22, Contributing Editor 10, Staff Writer 4, Special to … 4, Editor 2). Review items: 49.
- Tests on copies: parser cases OK; workbook insert 0 changed, 0 disagreements; apply_fills dry run 0 unexpected; migrate_ids 0 problems; build_data identical apart from the new fields; browser 16/16; display 18/18. Patch scripts apply cleanly to the current files.

## Update — author kinds + folded "Staff bylines" filter group (Sammy, 2026-10-27)
- authorsplit.author_kind(): person | board | staff | wire | org. author_split.csv now has an `author_kinds` column. build_data patch emits `akinds`. JS patch: staff kinds go in one collapsed "Staff bylines" group at the end of the Reporter filter; they stay normal links on stories.
- Also fixed: "Alston & Bird" (law firm, T24) is kept whole (a T24 org byline that matches the sheet text keeps T24's split; "X & Y" with single words isn't split). 20 rows differ from before the group rule (the 19 already reported + this one).
- Current counts: n_authors 0:42, 1:5,265, 2:553, 3:89, 4:21, 5:12, 6:2, 7:1, 8:4. Confidence high 5,890 / medium 41 / low 58. Review items 48. Author values by kind: person 6,490, org 119, staff 85, wire 76, board 63.
- Tests (copies): parser same; workbook insert 0 changed / 0 disagree; apply_fills 0 unexpected; migrate_ids 0 problems; build_data columns vs fallback identical, other fields identical; authors 23/23 (authors-only and links+authors pages); links 23/23 on the composed page; display 18/18 on the old blocks, 17/18 on current blocks (stale "empty reach" case, fails identically with links-only); patches compose with patch_links.py in either order.
