# Final build — the exact commands the final pass runs (agent-code, B2, 2026-10-27)

L = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib (run every command from L).
Everything below was rehearsed on copies (work/tmp_agent-code/integ + suite); nothing shared was edited by B2 except new
files in code/ (listed at the end) and the new files in build/pub/pipeline.

Run this AFTER the final workbook write, the ID migration and the library rename (so the workbook has the new IDs and
"Old Article ID" columns). The tracker build reads that migrated workbook: call it `FINAL.xlsx`.

## 0. Code: one idempotent step
```
python3 -I code/apply_all_patches.py --check      # dry run on a scratch copy; must end "CHECK OK"
python3 -I code/apply_all_patches.py              # applies; must end "OK"; a 2nd run reports "unchanged" for every file
```
It applies, in order: links (code/patch_links.py, LINKS-v1 + LINKS-v2 archive.org TV clips) → authors (T30:
patch_authors_build_data.py, patch_authors_apply_fills.py, patch_authors_js.py) → make_copies.py T40 version
(code/make_copies_clean.py; only over the known T14a version) → cleaner wiring (code/patch_clean.py, CLEAN-v1: tracker JS,
sheet_task.py, sheet task prompt, assemble.py, build_data.py) → refreshes build/pub/pipeline/. Targets are backed up to
work/pre_apply_all_<time>/ first; Python is compiled and the tracker JS is `node --check`ed; on any failure everything is
restored and it exits 1.

Note for the final write (apply_fills.py): the author-column block is now in apply_fills.py (T30 patch), so the final
write adds Author 1..8 + Author title. Run work/tmp_agent-authorsplit/run_split.py first if the regroup changed Originals
(T30b).

## 1. Tracker data blocks
```
python3 -I code/build_data.py FINAL.xlsx work/index_original.html build/blocks_final work/sid_map.json
```
Writes data/rows/idmap/covcols + **cleanrules.json** (copied from code/clean_rules.json) + report.json +
links_not_listed.csv. Expect `links no_listed_link_originals` ≈ 30 (63 before the TV-clip amendment).

## 2. Viewer copies + search index (from the cleaned library only)
```
python3 -I code/make_copies.py work/tmp_agent-write1/copies FINAL.xlsx build/copies_final \
   --clean work/html_clean --nb work/texts/nb --img-map build/clean/img_map.json \
   --errors work/final/error_copies.csv --deletions work/final/deletions.csv \
   --sidmap work/sid_map.json --report build/copies_final/report.json
```
- First argument = the published copies (read only, for the "what changed" report).
- work/html_clean must hold every cleaned library HTML under its OLD name `<year>/<old Article ID>.html`. If the
  reprint fetch (T44) or the retry agent added pages to the Desktop library after B2, copy their cleaned versions in
  under the old Article ID first (make_copies maps old → new IDs through "Old Article ID").
- Rehearsal on the migrated test workbook: 3,887 copies (2,979 cleaned HTML + 908 NewsBank PDF texts), 36.7 MB;
  images: 2,744 reuse the published img/0–15.json shards (matched byte for byte), 93 new in img/100.json (3.4 MB);
  dropped: 32 deleted stories, 48 error-copy files, press-release stories (no tracker entry).
  On coverage_current (pre-migration): 3,607 copies; vs the published v7 copies, the only stories losing a copy are
  the 45 error copies, the 32 deletions and 343 press-release stories.

## 3. Assemble the page
```
python3 -I code/assemble.py <current page shell> build/blocks_final build/js_merged.js build/index_final.html
```
Shell = the page the last publish used (work/tmp_agent-write1/index_base_T14a.html, or the live index.html read back).
The page gets `<script id="cleanrules">` next to rows/idmap/covcols.

## 4. Tests (all must pass; ~10 min; NODE_PATH=/opt/npm-tools/node_modules)
Point SRV at a folder holding index_final.html as index.html (+ articles/ for the search test).
| Suite | Command | Result on the B2 rehearsal |
|---|---|---|
| cleaner, library regression | `cd work/tmp_agent-code && python3 regress.py ../../code/clean_rules.json ../../code/clean_overrides.json` | 3,471/3,497 identical (99.26%), 99.91% ignoring spacing |
| cleaner, TinyFish pages | `cd work/tmp_agent-code && python3 regress_retry.py ../../code/clean_rules.json ../../code/clean_overrides.json` | 28/29 |
| skip/error scan | `cd work/tmp_agent-code && python3 findscan.py` | 16 skips = the 16 comment/teaser-only rows, 0 false |
| Python vs JS | `cd build/test_clean && python3 mkcases.py && node test_clean.js && CASES=cases_find.json node test_clean.js` | 30/30, 45/45 |
| display | `cd build/test_display && SRV=<rel. dir with fixture articles> CASES=../../work/tmp_agent-write1/cases_T14a.json node test.js` | 18/18 |
| reach | `work/tmp_agent-code/suite/test_reach.js` (srvtest -> page dir) | 8/8 |
| links (v2) | `cd work/tmp_agent-code/suite/test_links_v2 && python3 -I mkcases.py <blocks>/data.json c.json && SRV=<dir> CASES=c.json node test_links.js` | 25/25 |
| authors | `cd work/tmp_agent-authorsplit && PYTHONPATH=../../code python3 mkcases.py <blocks>/data.json c.json; SRV=<dir> CASES=c.json node test_authors.js` | 23/23 |
| update | body.js = script of build/js_merged.js; `BLOCKS=<migrated blocks> node test.js` (work/tmp_agent-code/suite/test_update) | 39/39 |
| sheet task | `ST=code/sheet_task.py python3 -I work/tmp_agent-code/suite/test_sheet_task.py` | 34/34 |
| search + Update path | `cd work/tmp_agent-code/suite && SRV=<dir with index + articles> node test_search_skip.js` | 15/15 |
(The old build/test_links suite's "archive link not listed" case is superseded by the v2 suite. The display suite needs
the fixture copies of work/tmp_agent-write1/srvtest/articles for its old-code checks.)

## 5. Publish (ONE publish, same artifact https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv)
- `index.html` ← build/index_final.html
- `articles/*.json` + `articles/manifest.json` ← build/copies_final/articles/ (all of them; they replace the old ones)
- `img/100.json` (and 101… if made) ← build/copies_final/img/ ; KEEP img/0–15.json (reused)
- `data/sheet.json` ← the final workbook (as before)
- `pipeline/`: sheet_task.py, build_data.py, assemble.py, tracker.js, authorsplit.py, clean_html.py, clean_rules.json,
  clean_playbook.md (all in build/pub/pipeline after step 0), legacy_index.html (unchanged)
- Old year shards with no successor (none expected) can be removed with `null`.
Then the sheet task's scheduled prompt = build/sheet_task_prompt_final.md (patched in step 0).

## Files added to code/ by B2
apply_all_patches.py, patch_clean.py, clean_html.py, clean_html.js, clean_rules.json, clean_overrides.json,
make_copies_clean.py, authorsplit.py, author_columns.py, patch_authors_build_data.py, patch_authors_apply_fills.py,
patch_authors_js.py; patch_links.py amended (LINKS-v2). build/clean/: img_map.json, regression outputs.
