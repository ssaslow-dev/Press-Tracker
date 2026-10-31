# agent-rename (T18) — 2026-10-27
Folder: ~/Desktop/Tracker library (3,317 HTML in year folders). Undo log: _rename_log.csv (3,294 rows: old_path,new_path,code,article_id,story_id,method). Map: _rename_map.csv.
- Coordinator renamed 3,284; T18 renamed 10 more of the 33 ambiguous (page outlet + same date + headline ≥0.95, or the tracker row's own link; exactly one candidate):
  jg-80f634→nb-03004, jg-f1f92d→nb-03039, jg-29ce76→nb-00539, jg-8c4983→nb-02378, jg-b1248d→nb-04049, jg-1d6528→nb-00214, jg-f9bb1f→nb-00249, jg-9140fb→ws-00062, jg-98b6db→nb-03409, jg-120fda→nb-03958.
- 23 left as jg-xxxxxx.html: lib/work/rename_ambiguous.csv (reasons: several same-outlet/same-day rows with the same headline — AP feed copies or editions (13); only reprint rows carry the code, no row is the page itself (9); jg-a6dd2b page body headline ≠ its title (1)).
- Verify: 3,294 files named <Article ID>.html + 23 jg-; every renamed ID exists in the sheet; no duplicate IDs; no same-name clashes in any folder.
- Byte-identical pages: 8 pairs → lib/work/library_duplicates.csv.
  * 5 pairs = same Story ID, outlet-name variants (Spectrum News 1 / Spectrum Local News ×4; FoodNavigator / FoodNavigator-USA): one page, two rows — likely merge candidates (they inflate # of reprints).
  * 3 pairs = DIFFERENT Story IDs among the 101 added old-tracker stories (jg-04262/04263, jg-04264/04265, jg-04236/04237): duplicate originals created by the 2026-10-26 add — the old tracker itself had them as separate stories. Flag for Sammy; also relevant to the regroup.
- Nothing deleted; no sheet or tracker changes.
