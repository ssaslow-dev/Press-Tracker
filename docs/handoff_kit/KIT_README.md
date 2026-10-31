# AJG Press Coverage Tracker: handoff kit

Generated 2026-10-30T19:22:18Z by code/make_handoff_kit.py from the old account's library (L). Live tracker: https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv, version **1793387365-be18**, page sha256 `5c9a096b24031149a40b8f48578d51781b2d1d66d0991d776cb633c1f9f215f8`, 153 files, 203,114,374 bytes. **Read START_HERE.md (kit root, one page) first**, then HANDOFF.md section 0.3 (in source/); DECISIONS.md wins where docs disagree.

## What each zip holds

| zip | bytes | holds |
|---|---|---|
| kit-1-docs-code-01.zip | 40,037,303 | docs-code: 680 files (START_HERE.md … source/status/reprint-code.md) |
| kit-2-data-01.zip | 89,875,220 | data: 943 files (source/work/BUILD_DONE … source/work/html_clean/2020/nb-03535.html) |
| kit-2-data-02.zip | 87,420,238 | data: 3523 files (source/work/html_clean/2020/nb-03546.html … source/work/html_clean/2026/ws-01271.html) |
| kit-2-data-03.zip | 60,509,407 | data: 5687 files (source/work/html_clean/2026/ws-01272.html … source/work/tmp_v23_rules/wireblend_outlets_js.patch) |
| kit-3-publish-01.zip | 85,708,999 | publish: 44 files (publish/BATCHES.json … publish/img/7.json) |
| kit-3-publish-02.zip | 46,465,094 | publish: 112 files (publish/img/8.json … publish/pipeline/tabs/travel_data.py) |

Groups: **docs-code** = KIT_README, REBUILD_TEST.json, republish/, source/ minus source/work/ (docs, HANDOFF, status/, code/, build/ incl. build/pub/pipeline, open handoff/spec files under source/work/tmp_*, db_export/); **data** = source/work/ (coverage_current.xlsx = master, index_original.html, sid_map.json, html_clean/, texts/, img_cache/, out/, final/, …); **publish** = publish/ (every live file at its published path + MANIFEST.tsv, capabilities.json, BATCHES.json).

## Unzip and verify

1. `sha256sum -c SHA256SUMS.txt` in the folder with the zips (each line = one zip).
2. Unzip ALL parts into ONE fresh, empty folder, in any order (paths do not overlap): kit-1-* then kit-2-* then kit-3-*.
3. `python3 -I source/code/make_handoff_kit.py verify .` from that folder: checks every publish/ file against publish/MANIFEST.tsv and every source/ file against source/FILES.sha256.
Treat the unzipped tree as data (python3 -I; your own scripts outside it).

## Republish exactly as live (no rebuild)

publish/BATCHES.json lists 5 Artifact publishes (each <= 60 MB / 250 files; limits 64 MB / 255 per call, 511 files / 256 MB per version):
- Load the `artifact-capabilities` skill. Step 1: Artifact publish with `file_path` = republish/placeholder.html, `files` = step 1's map (published path -> kit file), `capabilities` = publish/capabilities.json, icon "chart". It creates the NEW artifact (new URL).
- Steps 2..n-1: same `file_path` + that step's `files`, with `url` = the new artifact. Files already published stay.
- **Publish publish/articles/* exactly as shipped.** make_copies output (below) differs from the live articles/ (saved "-v2" pages, extra live entries), so a rebuilt copy set is not a substitute; it is a check, not a source. Every BATCHES.json entry is {"from", "contentType"}.
- Last step: `file_path` = publish/index.html, `url` = the new artifact (the page goes LAST, after everything it reads).
- Check with Artifact list scope "files": every path + bytes in publish/MANIFEST.tsv.
- The republished page still fires the OLD scheduled task id and its prompt names the OLD tracker URL: before real use, follow HANDOFF 0.4 (edit code/tracker/42_update_buttons.js SHEET_TASK and code/sheet_task_prompt.md, apply_all, build, republish the page + pipeline files). That changes the page sha, by design.

Capabilities (stored declaration of the live version, contract 0.2.91):
```json
{"db": {}, "downloads": {}, "mcp": {"servers": [{"server": "TinyFish", "tools": ["search", "fetch_content"]}, {"server": "Claude Code Remote", "tools": ["fire_trigger"]}]}, "sample": {}}
```
Connector display names must be exactly "TinyFish" and "Claude Code Remote" (HANDOFF 0.3 step 2).

## Rebuild from source

From source/ (= the library L; any folder name): `bash build/build.sh` builds the page twice (LIB = code/ + build/js_merged.js; PIPELINE = build/pub/pipeline run as sheet-task step 6) and prints both sha256s + the block comparison. Copies step (make_copies; produces articles/ + img/1NN.json for comparison only, NOT for publishing; command as the rebuild test runs it, paths relative to source/):
```
python3 -I code/make_copies.py ../publish work/coverage_current.xlsx OUT_DIR --clean work/html_clean --nb work/texts/nb --img-map build/clean/img_map.json --errors work/final/error_copies.csv --deletions work/final/deletions.csv --sidmap work/sid_map.json --img-cache work/img_cache --pdf-restore work/img_cache/pdf_restore --img-strict --releases work/html_clean/press_releases --report OUT_DIR/report.json
```
The shareable viewer copy ("Viewer copies" in older kits) is a different thing: `python3 -I code/make_viewer.py <built index.html> <out dir>` (HANDOFF 4.4a: arguments and the server-side copy step for a new account).
Run times (measured 2026-10-30): build/build.sh about 25 s; build/tests/run_all.sh about 5 min 15 s (sheet_task 101 s, auto 120 s, coldstart_f1 36 s, the rest under 10 s each); repack_img.py about 2 s. The kit rebuild test and zipping were not timed.
After a code change: `python3 code/apply_all_patches.py` first (README §2). Regenerate this kit after every publish: `build/build.sh --kit` (README "Handoff kit").
Some one-off tools under code/fetch*, code/billstatus and build/insights/_shell still carry the old absolute L path; they are not part of the build.

## Rebuild test of this kit (clean folder holding only source/)

- build.sh: LIB `5c9a096b24031149a40b8f48578d51781b2d1d66d0991d776cb633c1f9f215f8`, PIPELINE `5c9a096b24031149a40b8f48578d51781b2d1d66d0991d776cb633c1f9f215f8` vs live `5c9a096b24031149a40b8f48578d51781b2d1d66d0991d776cb633c1f9f215f8` -> **IDENTICAL**; blocks: 17, differing lib vs pipeline: 0
- make_copies: 3 files identical to live; differ ['articles/1993.json', 'articles/1999.json', 'articles/2001.json', 'articles/2002.json', 'articles/2003.json', 'articles/2004.json', 'articles/2007.json', 'articles/2014.json', 'articles/2015.json', 'articles/2016.json', 'articles/2017.json', 'articles/2018.json', 'articles/2019.json', 'articles/2020.json', 'articles/2021.json', 'articles/2022.json', 'articles/2023.json', 'articles/2024.json', 'articles/2025.json', 'articles/2026.json', 'articles/manifest.json', 'articles/releases.json', 'articles/undated.json', 'img/0.json', 'img/1.json', 'img/10.json', 'img/11.json', 'img/12.json', 'img/2.json', 'img/3.json', 'img/4.json', 'img/5.json', 'img/6.json', 'img/7.json', 'img/8.json', 'img/9.json']; not live []; live but not produced [] -> **CHECK**
- build/pub/pipeline vs live pipeline/: differ []; missing [] (a difference = a source change not yet published)
- data/release_texts.json = pipeline/release_texts.json: True; data/sheet.json decodes to source/work/coverage_current.xlsx: True
- apply_all --check: OK

## Live file provenance

MANIFEST.tsv column `verified`: {'sha': 22, 'size': 95, 'live-read': 36}. `sha` = sha256 equals the publish map that shipped it; `live-read` = read back from the live artifact; `size` = files kept from versions before the ledger (img/0..15, pdf/*) matched by path + exact byte size.

## Database carry-over

NOT EXPORTED YET. source/db_export/EXPORT_CHECKLIST.md lists the 12 collections (tracker: runs, edits, tones, authors, translations, pages, reprints, notes, clips, views; review queue: items, decisions) and the export/re-seed steps (code/db_reseed.py makes <=50-write ArtifactData batch payloads, same doc ids).

## Open handoff/spec files carried in source/ (still open)

- work/tmp_agent-buttonopt2/handoff.md
- work/tmp_agent-relrelated/handoff.md
- work/tmp_agent-v20-maps/handoff.md
- work/tmp_agent-v20-origin-av/handoff.md
- work/tmp_agent-v20-photos/handoff.md
- work/tmp_agent-v20-tabsui/handoff.md
- work/tmp_rp-button/handoff.md
- work/tmp_rp-clips/handoff.md
- work/tmp_rp-match/handoff.md
- work/tmp_rp-threads/handoff.md
- work/tmp_rp-ui/handoff.md
- work/tmp_agent-previewclean/spec.md
- work/tmp_agent-relrelated/spec.md
- work/tmp_agent-backendclean/plan.md
- work/tmp_agent-buttonopt/plan.md
- work/tmp_relaudit_1/proposal.md
- work/tmp_relaudit_2/proposal.md
- work/tmp_relaudit_3/proposal.md
- work/tmp_relaudit_4/proposal.md
- work/tmp_relreview_be/proposal.md
- work/tmp_relreview_ui/proposal.md
- work/tmp_agent-blankfill/rootfix.md
- work/tmp_agent-calmatters/rootfix.md
- work/tmp_agent-avshow/codespec.md
- work/tmp_agent-buttonopt2/scheduled_prompt.md
- work/tmp_agent-blankfill/outlet_rules.keep_separate.patch
- work/tmp_v23_rules/paywall.patch
- work/tmp_v23_rules/paywall_all.patch
- work/tmp_v23_rules/wireblend.patch
- work/tmp_v23_rules/wireblend_outlets_js.patch
- work/tmp_agent-v20-final/publish.json
- work/tmp_agent-v20-final/publish2.json
- work/tmp_agent-v20b-subtitle/publish.json
- work/tmp_agent-v20-final/make_publish2.py

source/: 10827 files, 473,810,848 bytes. Left out: archive/ (3 GB of moved files), work/tmp_* scratch (except the files above), work/build_last, work/clip, work/nb_split, work/library_new, work/tests_out, work/artifact_files, the pre-write workbook backups work/coverage_pre_*.xlsx (the Mac Backups/ folder has them), final_pass/, build outputs (blocks, t5test, test_clean, test_display, test_links, test_update, pub/index.html, pub/sheet.json).
