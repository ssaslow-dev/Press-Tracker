# LOCALAPP survey (read-only, 2026-11-02)

Paths are relative to the repo. `T/` = `code/tracker/`. Line numbers are from the files as committed (HEAD 3582d42).
Scratch build output: `/tmp/claude-0/-home-user-Press-Tracker/ec7aac73-d461-552b-aaac-9f8ebc5e7581/scratchpad/survey_build/` (nothing was written into code/ or build/).

## 1. Artifact runtime used by the page

The page reaches the runtime only through `window.claude.use(name)` with names `db`, `sample`, `mcp`, `downloads`. Nothing else: no file uploads, no identity or who-is-viewing, no `ask`. Every use is wrapped so the page works when `window.claude` is absent (falls back to localStorage); `make_viewer.py` (the shared copy, capabilities `{}`) relies on that.

Declared capabilities (CLAUDE.md): db, downloads, sample, mcp (TinyFish: search, fetch_content).

### 1a. `db` (shared store). API the page needs: `db.collection(c).doc(id).set(obj)`, `.doc(id).delete()`, `.onSnapshot(cb, errcb)` where `cb(snap)` gets `snap.docs[]` with `d.id` and `d.data()`.

Opened at `T/00_head.js:211-212` (`initTone`), and again in `T/41_update_search.js:988-989` (`initClips`).

| Collection | Doc shape | R/W | Feature | Update button? |
|---|---|---|---|---|
| `tones` | id = Story ID (or temp code `jg-xxxxxx`); `{tone, why<=300, rated, by:'Claude'\|'Team', topic?, bills?}` | R snapshot `00_head.js:219`; W `:239`, `:294`, `19_team_tone.js:6` | tone rating, team tone correction | no (Claude rating needs `sample`) |
| `authors` | `{author:'A; B', found, by:'Claude'\|'Page metadata'}` | R `00_head.js:224`; W `01_authors.js:168,196,207`, `41:1016` | byline finding | no (but 41:1016 writes for new finds) |
| `translations` | `{hl, text, lang, at, by}` | R `20_translation.js:15-16`; W `:23`, `41:1017` | English headline / story | no (41:1017 for new finds) |
| `notes` | `{text<=2000, at}` | R `18_team_notes.js:7-8`; W `:20` | team note on a story | no |
| `views` | `{name, st:JSON string of filter state}`; delete too | R `16_saved_views.js:48-49`; W `:37`; delete `:41` | saved views | no |
| `clips` | the full find record minus `_*` keys and `why` (id, date, outlet, pub, hl, link, plink, topic, media, reach, role, conf, bills, author, tone, lang, hl_en, text_en ...; see `cleanClip` `41:933`) | R `41:991,994-995`; W `41:1008`; delete `43:195` | stories added by Update, shown in tables | yes |
| `reprints` | id `rp-<hash12>`; `{story, outlet, link, date, added}` | R `41:994-996`; W `41:1028`; delete `43:182` | reprints of existing stories | yes |
| `pages` | id = temp story code, `rp-<hash12>` or `og-<hash12>`; `{url, title, clean, scoped, publine, at}` (`scoped` up to 400 KB, `clean` full cleaned page HTML) | W `41:916,926` | saved copies waiting for the save | yes |
| `runs` | id `run-<base36>`; run doc (see 7c) | R `43:63-64`; W `43:85,92,98` | Update log pane, run history, `searched_to` | yes |
| `edits` | id = Story ID; `{field:value ..., at}` or `{removed:true, at}`, plus `reported` set by the save | R `43:63-70`; W `43:183,194` | hand edit or removal of any story (story panel + Log pane) | partly: UI is in 43 but is a general feature |

Also browser storage (per-viewer): localStorage `jg-tones`, `jg-authors`, `jg2-notes`, `jg2-views`, `jg2-visit`, `jg2-rg-shut`, `jg2-density`, `jg-runs-pending` (`43:79-81`); sessionStorage `jg2-tb-lists` (`53_tabs.js`); IndexedDB `jg-archive`/`html` for saved pages dropped into Manage (`00_head.js:189-194`, `99_boot.js:13`). These are keyed by origin: a local server needs one fixed host:port or they reset.

### 1b. `sample` (ask Claude), `sampler.json(prompt, {signal, modelTier})`
- Tone + topic + bills rating: `00_head.js:212,256-309` (`tonePrompt`, `rateTones`; button `[data-trate]` `:309`).
- Byline finding: `01_authors.js:187-215` (`authorPrompt`; `[data-afind]` `:233`).
- Translate headlines/stories: `20_translation.js:32-83` (`sampler.json`, `translateStory`, `translateNew`).
- Update screening and classification: `41:686` (`sample`), `:837` (`screenPrompt`, tier quick), `:852` (`classifyPrompt`, tier default).
- Of these only the last belongs to the Update button; the first three run from "Refresh from files" (`42:56-71`), the Manage drop zone (`21:49 translateNew`), and click handlers, i.e. they stay when Update is removed but need Claude.

### 1c. `mcp` (TinyFish), `mcp.callTool('TinyFish', 'search'|'fetch_content', input, {signal, cache:false})`
- Update only: `41:12,16` (`tfCall`, throttled 2.1 s), calls at `41:209,270,274,287,312,325,333,341,358,380,434,488,708,788,818,922`; `leginfo` check `41:406-420`; GDELT TV via fetch_content `41:372-377`; release listing pages `41:462-`.
- Not Update: `20_translation.js:67-68` (fetch story text for translation when no saved copy).
- Error codes handled: `40_update_outlets.js:351-352` (`server_not_connected`, `needs_reauth`).

### 1d. `downloads`, `dl.save({filename, data})`
- `T/21_manage_badge.js:55-56` (`saveFile`); fallback is an `<a download>` blob (`:57`). Used by CSV and spreadsheet downloads (`download(kind)` `:68`; `'sheet'` fetches `data/sheet.json` and decodes base64 `:71-75`). Not Update.

### 1e. Not used
No file-upload capability (Manage drop zone reads local `File` objects in the browser, `21:34-50`), no identity, no `ask`, no `assets`.

## 2. How the page loads data

Embedded in `index.html` (assembled by `code/assemble.py` + `tabs_assemble.py`, built by `code/build_data.py`):
- `<script id="data">` array of stories (6.4 MB from the snapshot), read `00_head.js:4`.
- `rows` (dedupe index over ALL Coverage rows: cols aid, sid, kind, outlet, date, hl, links; plus `next` ids) `build_data.py:347`, read `40_update_outlets.js:96-124`.
- `idmap` (`00_head.js:7`), `covcols`, `billsinfo` (`00_head.js:56`), `fetchrules` (`41:53-65,600-603`; from clean_rules/outlet_rules/lookup_cache), `tab-<id>` json + `tab-js-<id>` module code (build/tabs), `ins-*` blocks (Insights views; `ins-release_pickup` is read by Update at `41:468`). Map geometry is inline JS (`14_county_map.js`, `52_us_map.js`).
- Not embedded: the page shell (HTML, CSS, header markup). See 3.

Fetched by relative URL at runtime (a local server must serve all of these):
- `articles/manifest.json` (`00_head.js:187`, `cache:no-cache`): `{articles: {storyId: "articles/<year>[-N].json"}}`.
- `articles/<year>.json` shards (path from manifest; `00_head.js:176`): `{fileKey(id): "<cleaned page html>"}`. About 12 MB per shard (`make_copies.py --shard-mb`). Also `articles/releases.json` (release copies, keyed by Release ID).
- `img/<n>.json` (`00_head.js:183`): `{key: data-URI}`; pages reference `src="jgimg:<n>/<key>"`.
- `data/sheet.json` (`21:53,71`): `{filename, b64}`, the workbook for the download button.
- `data/release_texts.json` (`41:555`; `build/tabs/releases.js:19,96`; 1 MB; `{rel:{url:{...}}}`), fetched lazily.
- `pdf/`: no direct fetch. Saved copies carry `<meta name="jg-pdf" content=URL>` (`06_story_sheet.js:142`); URL is whatever the copy holds (external or relative `pdf/...`, `make_copies.py:329-333` embeds or drops those).
- `copies/`: not a page path. It is the saver/sheet_task working folder (`copies/articles/...`, `sheet_task.py:1608 copy_html`).
- Viewer copy only: `data/data.json`, `data/rows.json` via synchronous XHR (`make_viewer.py:22-25`).
- Snapshot in repo: `data/AJG Coverage - NewsBank.xlsx`, `data/library/` (12,637 files). Shards, `img/` and `data/sheet.json` are NOT in the repo; regenerate with `make_copies.py` (needs the library + `work/` inputs listed in `docs/handoff_kit/KIT_README.md`) and `build_data`/pipeline.

## 3. The build

`build/build.sh` (bash, `set -e`, `$L` = repo root) expects: `XLSX` (default `work/coverage_current.xlsx`), `BASE` page shell (default `build/shell/index.html`), `work/index_original.html`, `work/sid_map.json`, `build/pub/pipeline/`. LIB path: `build_data.py` then `assemble.py` with `build/js_merged.js`. PIPELINE path: copy `build/pub/pipeline`, run `build_data.py ../committed.xlsx legacy_index.html ../pipeblocks sid_map.json`, then `assemble.py shell.html ../pipeblocks tracker.js ../pipe_index.html`; compares block by block. None of those inputs except js_merged.js exist here.

`code/apply_all_patches.py`: step 1 concatenates `code/tracker/NN_*.js` (34 files) into `build/js_merged.js` (+ `.sha256` stamp); step 2 bills; step 3 builds `build/pub/pipeline/` from a `PIPELINE` map (lines 34-74: ~50 py/json files from `code/`, `shell.html` from `build/shell/shell.html`, `sid_map.json` from `work/sid_map.json`, docs from repo root `README.md`, `DECISIONS.md`, `CONTRACT.md`, `TONE_GUIDE.md`, plus `build/insights/*` and `build/tabs/*`); step 4 `py_compile` + `node --check`.

What I ran (all in the scratch dir, on a copy):
- `apply_all_patches.py --tracker-js OUT`: OK, 34 parts, 718,285 bytes; it equals the committed `build/js_merged.js` (sha256 92e2b785..., matches the stamp). `node --check` passes.
- `apply_all_patches.py --root <copy> --no-pipeline`: OK (38 py files compile, node check ok, nothing changed).
- `apply_all_patches.py --root <copy>` (with pipeline): FAILS at the first missing source, `work/sid_map.json` (FileNotFoundError at line 148). Missing sources: `work/sid_map.json`, `build/shell/shell.html`, and `DECISIONS.md`, `CONTRACT.md`, `TONE_GUIDE.md` at root (they live in `docs/` here; `README.md` exists at root). `build/insights/` does not exist (the PIPELINE step tolerates that).
- `build_data.py "<snapshot xlsx>" <stub legacy_index.html> OUT/blocks` with a stub legacy page `<script id="data">[]</script>`: OK in 14.5 s, no sid_map: 3,681 stories, 9,964 Coverage rows, idmap 3,915, 8 wire-blend pickups. Wrote data.json (6.4 MB), rows.json (2.1 MB), idmap, covcols, billsinfo, fetchrules, cleanrules, av.json, report.json, links_not_listed.csv and `tab_common/releases/reporters/travel.json`. No `ins_*.json` (build/insights absent).
- `assemble.py <stub shell> blocks js_merged.js out.html` with `TABS_DIR=build/tabs INS_DIR=<none>`: OK, 9.8 MB page with `data, rows, idmap, covcols, billsinfo, fetchrules, tab-* , tab-js-bills/releases/reporters/travel`. It is only as good as the shell.

Inputs NOT in the repo, and what they are:
- `pipeline/shell.html` (= `build/shell/shell.html`): the page skeleton, CSS and header/panel markup (ids the JS needs, e.g. `#q #table #sheet #toast #updBtn #upd #updBody #mgTabs #mgOther #runFind #runRefresh #raStrip #rcSince ...`), with data blocks stripped by `code/make_shell.py`. Nothing in the repo contains this HTML/CSS (grep for `header.mast`, `<style`, `#anFrom` finds only JS). It cannot be generated from `code/` + `build/`. Source: the live artifact's `index.html` (Artifact `read`), or `publish/index.html` in the handoff-kit zips (not here), then `python3 -I code/make_shell.py index.html shell.html`. Also needed for SAMELOOK-v1 and for the local app.
- `pipeline/legacy_index.html` (= `work/index_original.html`): an old published page; build_data reads only its `data` block for fallbacks used where the workbook cell is blank (`build_data.py:201-242`: pub, src, added, hl_en/text_en, county, tone note ...). A stub works for structure; real fallbacks are lost (check output vs live before trusting; `added` feeds the Log pane grouping).
- `pipeline/sid_map.json`: output of `make_id_map.py` (optional 4th arg of build_data; omitted = only legacy `jg-` codes missing from idmap). Not needed for a clean build.
- `pipeline/tabs/`: generated by apply_all from `build/tabs/` (present: bills, releases, reporters, travel; `_common_data.py`, `*_data.py`). OK. `ORDER` in `tabs_assemble.py:11` lists `outlets`, which has no module.
- `build/insights/<id>.js` + `<id>_data.py` (release_pickup, bill_timeline, story_travel): absent. They feed `ins-*` blocks and the Insights tab (`50_insights_shell.js`) and `ins-release_pickup` used by Update. Source is in the kit zips only. Without them those views have no data.
- The saver's rebuild step (`work/saver/src/saver.py:954-964`, `saver_steps.py:175`) needs `pipeline/{assemble.py, shell.html, tracker.js, tabs/, legacy_index.html, sid_map.json}`: tracker.js, tabs/ and the py files are producible here; shell.html is the blocker; legacy_index and sid_map can be stubs/omitted as above (risk: changed fallbacks).
- Also absent: `work/` inputs for `make_copies.py` (html_clean, texts/nb, img cache, deletions.csv, error_copies.csv ...) and `data/sheet.json`. The saver/rebuild path is meant to produce `site/` (`work/saver/README.md:63`).

`docs/handoff_kit/` here holds docs and the retired patch scripts only (no zips). `KIT_README.md` says a clean rebuild from `source/` gave a page identical to live (sha 5c9a096b...).

Tests: `build/tests/run_all.sh` (bash, ~5 min) and `build/tests/tabs/build_testpage.sh` need `build/shell/index.html`, `work/coverage_current.xlsx`; I did not run them.

## 4. Update-button code and how to switch it off

Files: `T/40_update_outlets.js` (outlet groups, dedupe `dupOf` 297, `knownIndex` 35, `covLoad/covHit` 105-152, `proposeRows` 220, `classifyPrompt` 360, `tfClean` 540, `cleanLocal` 541 (stub), run state `U` 15), `T/41_update_search.js` (TinyFish plan/search/fetch `99-` , release check 462-, `runUpdate` ~681, `savePages` 914, `cleanClip/addClips/applyReprints` 933-986, `initClips` 987, `saveFound` 997, `drawUpd` 1067, `openUpd/closeUpd` 1107-1109, `#updBtn` handler 1109), `T/42_update_buttons.js` (`runAll` 13, `raConfirm` 207, header buttons `#runFind/#runRefresh`, the Update dialog `#upd` handlers 156-170), `T/43_update_log.js` (`cleanRun` 44, `initLog` 62, `saveRun` 84, heartbeat 87, `snapStories/diffStories` 94-100, `renderLog` 151, `editForm/saveEdit/removeStory` 139-200, `applyEdit` 23).

No flag, no clean seam. The files are not an optional plug-in: other files call into them.
- 40 defines shared helpers: `U` (used `03_overview.js:48`, `10_manage_panes.js:28`, `21_manage_badge.js:4`, `53_tabs.js`), `hostOf, VS, hash12, normU, normH, pick1` (used by all of 41/43), `ranIn` (used by `build/tabs/reporters.js`), `cleanLocal` (`21:~40`, `99_boot.js:13`).
- 41: `initClips` (called `99_boot.js`), `openUpd/closeUpd/drawUpd` (`24_events.js:58,60`, `21_manage_badge.js:11-13`, `99_boot.js`: `if (h==='about') openUpd('defs')`), `TF/tfPayload/tfFetchInput` (`20_translation.js:67-68`), `metaByline` (`01_authors.js`).
- 42: `runAll` (`24_events.js:57`).
- 43: `renderLog` (`10_manage_panes.js:5`), `editForm/saveEdit/removeStory` (`24_events.js:68-73`), `applyEdit`, `EDITS` (story edits and removal for ANY story).
- The "Manage" panel (`#upd`, opened by `#updBtn`) is shared: tabs `upd` (Update), `log`, `defs` (About), `quality` (data checks), saved copies drop zone; `drawMg` `21:8-13`.

Cleanest ways, in order of risk:
1. Keep all files; run without `window.claude`. Then `runUpdate` stops with "Finding stories needs the tracker open in Claude with the TinyFish connector" (`41:685`), Refresh/translate degrade (`sampler` null: `00_head.js:276`, `20_translation.js:32`). Hide the buttons with CSS as `code/make_viewer.py:25-26` does (`#runFind,#runRefresh,#raStrip,[data-runfind],#updGo,#updRefresh,#updSave,#updAdd,#updCopy,#updAgain,[data-dl],#bkCsv{display:none!important}`). That is a tested precedent (the shared viewer copy) and breaks no tab.
2. A local `window.claude` shim implementing only `use('db')` (collection/doc/set/delete/onSnapshot over local JSON files via the server) and `use('downloads')`; leave `mcp` and `sample` undefined. This keeps notes, saved views, team tones, hand edits, translations, the Log pane working with SAMELOOK-v1.
3. Removing 40-43 from the concatenation breaks the page (see the callers above): needs stubs for ~15 names. Not recommended for now.
When the button comes back: shim `mcp.callTool` and `sample.json` to call TinyFish and Claude from the local Python.

## 5. Python packages and tools

Third-party, by script (pipeline + build):
- `pandas` + `openpyxl`: `build_data.py`, `tabs_data.py`, `insights_data.py`, `sheet_task.py`, `make_copies.py`, `reltab.py`, `shared_data.py`, `avtab.py`, `author_columns.py`, `work/saver/src/saver_diff.py`. Core to the build and the save. (Installed here: pandas 3.0.5, openpyxl 3.1.5, Python 3.13.)
- `beautifulsoup4` with parser `html.parser` only (no lxml): `clean_html.py`, `reprint_rule.py`, `av_display_clean.py`, `sheet_task.py`.
- `Pillow`: `img_embed.py`, `make_copies.py:492`, `media_gate.py:72`.
- `requests`: `img_embed.py:239-240` (downloads page photos at save time; the only network use in the pipeline).
- `cairosvg`: `media_gate.py:95` (SVG to PNG; needs the native Cairo library; Windows-unfriendly; check whether the call is in a try).
- `langdetect`: `extract_nb.py:14` only (one-off NewsBank extraction, not in the build/save).
- Stdlib that needs a package on Windows: `zoneinfo` (`dates_lib.py:4`, `avtab.py:71,701`, `sheet_task.py:4515`, `saver.py:96,242`; timezone America/Los_Angeles) needs the `tzdata` wheel on Windows.
- Test only: `pytest` (saver tests).

Non-Python tools:
- `node`: `apply_all_patches.py:262` (`node --check`, build verify only, skipped if absent: "node not found"); JS tests in `build/tests/` (not needed at runtime).
- `pdftotext` (poppler): `release_rule.py:160-162` (PDF library files, 60 s timeout) used by `sheet_task.py` release checks; `extract_nb.py:148` (one-off). Needed on the PC for any save that reads PDF copies.
- `bash`: `build/build.sh`, `build/tests/run_all.sh`, `build/tests/tabs/build_testpage.sh`. The saver (`work/saver/src`) is pure Python (subprocess only runs `sys.executable`, `saver.py:17`).

Windows-unfriendly:
- Hard-coded Mac paths in `sheet_task.py:155-157` (`MASTER_XLSX`, `MASTER_LOCK`, `BACKUPS_DIR` under `~/Desktop/Tracker library/`) and in the prompt; the saver already works on local paths.
- `multiprocessing.Pool` in `shared_data.py:214` (spawn on Windows; needs a `__main__` guard); one-off.
- `os.link` and `copytree(symlinks=True)` in `make_handoff_kit.py:256,387` (kit tool, not needed).
- Old absolute `L` paths in some one-off tools (`code/fetch*`, `code/billstatus`), per `KIT_README.md`. Python is run with `-I` everywhere (`-I` drops the script dir from sys.path; scripts add it themselves).
- Not verified: shell `cp -r`/`find` in build.sh only. No `os.fork` found.

## 6. Network use other than Update

- Page: Google Fonts `@import` inside the saved-copy iframe CSS (`06_story_sheet.js:48`, Roboto Slab, Public Sans); falls back to system fonts offline. The page shell probably also links Google Fonts (shell missing; `build/review/index.html` does, and it is a different page). Unverified for the tracker.
- Page: PDF.js from `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/` (`06_story_sheet.js:112-117`), loaded only when a PDF is dropped under Manage (`pdfFileToHtml`).
- Page: outbound links only (State Library login `03_overview.js:98`, story links); no auto-fetch. Clipboard use `22_helpers.js:5`.
- Fetch of `articles/`, `img/`, `data/`: same origin.
- Saved copies embed photos as data URIs (`img/` shards), no image downloads at view time (`make_copies.py` drops or embeds external images).
- Pipeline: `img_embed.py` (requests) downloads photos at save time (`sheet_task.py` embed_page); the saver runs subprocesses with proxies pointed at a dead port (`saver_steps.offline_env`), so image embedding is off in preview and unverified in save. Everything else in the pipeline is offline (lookup cache first).
- TinyFish, GDELT, leginfo, gabriel.asmdc.org, jewishcaucus.legislature.ca.gov are Update only (via the TinyFish connector).

## 7. For the separate Update-only artifact

### 7a. Code the Update button depends on

Own files: `T/40_update_outlets.js` (all), `T/41_update_search.js` (all), `T/42_update_buttons.js` (all), `T/43_update_log.js` (all).

Needed from other files (top-level names found by scanning 40-43; re-check with a real dependency tool before cutting, my scan is by name):
- `T/00_head.js`: `$` :92, `esc` :93, `fmt` :94, `pl` :105, `D` :4 (embedded `data`), `IDMAP/sidOf/SID_OK/SID_ANY/CODE_OF/AID_OF/legacyKey/fileKey` :7-19, `oldFirst` :21, `syncReps` :43, `BILL_ROWS/BILL_INFO/BILL_RX/setBills/billNorm/splitBills` :56-88, `MONTHS` :95, `byId` :97, `TODAY` :100, `LAST` :102 (reassigned `41:953`), `TONE_ORDER/TONE_OK` :110,:198, `rated` :112, `REACH_ORDER` :122, `RANK/refreshRanks` :130-132, `local` :138, `IC` :109, `tdb/sampler` :199-200, `pendingTone/rateTones/tonePrompt` :203-276, `articleText` (:~290). `IDB`, `PAGE/htmlOf/loadPages` only if the Manage drop zone stays.
- `T/01_authors.js`: `fold` :35, `canonAuthors` :18, `searchStr` :135, `detectLang` :141, `setAuthor` :151, `bylineAuthors` :154, `aChecked` :6, `pendingAuthor/findAuthors` :171-187.
- `T/02_state.js`: `S` :18, `YEARS/setYears` :20-22, `reprintCount` :68, `match` :96, `filtered` :110, `dateLabel` :120, `alsoNames` :127, `nrmName` :136.
- `T/03_overview.js`: `cpBtn` :123. `T/06_story_sheet.js`: `openViewer` :2, `closeViewer` :168. `T/10_manage_panes.js`: `renderAbout` :2. `T/18_team_notes.js`: `NOTES`, `saveNote`. `T/19_team_tone.js`: `setTeamTone`. `T/20_translation.js`: `translateHeadlines`, `translateStory`, `pendingTr`. `T/21_manage_badge.js`: `drawMg` :8, `byDate` :15, `download` :68. `T/22_helpers.js`: `tsvCell` :2, `copy` :3, `toast` :15. `T/23_render.js`: `render` :2, `renderWhen` :11, `go` :23. `T/24_events.js`: click wiring (`:57-73`).
- Helpers defined inside 40-43 and used by the others: `hostOf :27, VS :32, hash12 :30, normU :22, normH :26, pick1 :33, covDays :129, mcpText :335, localDay :436`.
- Page ids and CSS (live in the missing shell): `#updBtn #mgBadge #mgTabs #upd #updScrim #updBody #updFoot #mgOther #runFind #runRefresh #raStrip #raProg* #rcScrim #rcT #rcD #rcSince #rcSinceWrap #rcYes #rcNo #rcErr #updGo #updAgain #updRefresh #updSave #updAdd #updCopy #updCopyPrint #updSince #updStep #updProg #updStop #toast #anFrom`, classes `.upd-*`, `.up-k`, `.ra-*`, `.attn*`, `.log-*`, `.dlmenu`. The CSS cannot be recovered from this repo; take it from the live page (`runconfirm-css` style is injected by 42 itself).
- Embedded blocks it reads: see 7b.

### 7b. Tracker data the Update reads

| Data | Used for | Where read | Source |
|---|---|---|---|
| `D` (all stories) | dedupe, outlet list, reach/medium/county of known outlets, reprint targets, `LAST`, `BILL` tags, Log grouping by `added` | `40:35-46,297-330`, `outletGroups` `40:~4-14`, `covReach/covMedium/covCounty` `40:134-210`, `41:1004` | `data` block (build_data.py) |
| `rows` block `{cols, rows, next}` | dedupe against ALL Coverage rows incl. removed and unverified; next ids | `covLoad` `40:105-124`, `covHit` 134, `covRepKnown` 152 | `build_data.py:347` |
| `covcols` | column order of proposed rows | `40:107` | build_data |
| `idmap` | temp code to Story ID | `00_head.js:7`, `40:256` | build_data |
| `billsinfo` | his bills, intro dates, leginfo comparison | `00_head.js:56`, `41:406-420` | `gabriel_bills_leginfo.json` |
| `fetchrules` | skip URLs, print-page URLs, never-coverage hosts, blocked hosts, lookup cache (urls, hosts, archive) | `41:53-65,598-603` | clean_rules.json, outlet_rules.json, lookup_cache.json |
| `ins-release_pickup` `{rel:[tuples], known, also}` | which releases are already on the Press releases tab, newest per site | `41:468-475` (`relKnown`) | `build/insights/release_pickup_data.py` (missing here) |
| `data/release_texts.json` (1 MB) | release pickup search sentences | `41:555` (`relTexts`) | `pipeline/release_texts.json` |
| run history `runs` collection | `searched_to` (default start = that date - 7 days) | `lastSearched` `41:616`, `sinceDefault` `:633`; mode/`newsbank` `43:53` | db `runs` |
| `edits` collection | removed stories do not count as known | `41:992` (`EDITS`) | db |
| `clips`, `reprints` collections | stories/reprints added by earlier runs not yet in the workbook | `41:991-996` | db |
| `data/sheet.json` | not read by Update (download only) | | |
| reporters, `lookup_cache.json`, `outlets.json` as files | not read by the page (only through `fetchrules`, and by sheet_task in the save) | | |

### 7c. Runtime calls and what a finished run looks like

Calls: TinyFish `search` and `fetch_content` (see 1c), `sample.json` (`41:837,852`), db writes `clips, pages, reprints, authors, translations, runs`. No downloads.

Collections written by one `Update database` run (mode `find`), in order:
1. `runs/<run-id>` heartbeat: `{at, mode:'find', status:'running', provisional:true, heartbeat, since, step, done, plan, cands, failed}` (`43:88-93`, `42:23-32`), at most every 20 s.
2. `pages/<tempcode>` for each added story: `{url, title, clean, publine, scoped, at}` (`41:926`); `pages/rp-<hash12>` for each reprint candidate and `pages/og-<hash12>` for originator copies: `{url, title, clean, scoped:'', at}` (`41:916`).
3. `clips/<tempcode>`, `reprints/rp-<hash12>`, optional `authors/<tempcode>` and `translations/<tempcode>` (`41:1008-1028`). Finds already carry Tone/Tone note/Tone rated by in their sheet row, so no `tones` doc (`41:1013`).
4. `runs/<run-id>` provisional doc after the adds (`41:1042-1045`) with `stories, reprints, rows`.
5. Final `runs/<run-id>` (`42:75-93`): `{at, mode, status:'done'|'error', stories[], reprints[{story,outlet}], tones[], authors[], translations[], rows[], searched_to, since, since_manual, failed:'n of m', found_by{}, gnews, bills_new[], leginfo, releases_new[{...html|text...}], relcheck, print_pages[], lookups[], left[], unconfirmed[]}`. `rows` are Coverage-column objects (names from `covcols`) with placeholder IDs `NEW-<run>-<n>` / `sNEW-<run>-<n>`, plus non-column keys `_page, _origin{service,how,cands[{url,title,date,outlet,page}]}, _found_by, _release{prid,url}, _backfill, _date_check, _nocopy_find, _date_src` (`40:244-251`). The sheet task later writes `ids` and `sheet{at,written,line,...}` back.
- Contract text: `docs/CONTRACT.md` section "Proposed rows from the Update button (db collection "runs", field `rows`)" (line 49) with the worked example (line 56) and fixture `build/tests/sheet_task/fixtures/example_db.json`. Run doc fields are also normalized by `cleanRun` `43:44-60` (caps: 500 rows, 150 unconfirmed, 100 print pages, 100 lookups). Saved-copy rules: CONTRACT "Press-release copies" sections (118-142).

### 7d. After a run, until the save

Today: nothing runs by itself (NOSCHED-v1). `saveSheet` only toasts (`41:666-670`); the run doc is the hand-off. Sammy asks Claude in chat; the procedure is `code/sheet_task_prompt.md`:
- Step 1 reads, as files `db/<collection>/<doc id>.json` (`sheet_task.py:4549-4574 load_db`, which reads exactly `runs, edits, tones, authors, translations, pages, reprints`; `clips`, `notes`, `views` are NOT read). Plus the review queue artifact's `items/decisions/applied` into `queue/` (`--queue`). `--check-only` exit 3 = nothing queued.
- Which run: the newest run doc with rows (or `bills_new` / `releases_new`) and no `sheet.written:true` (`run_done`).
- So the update folder must carry: `runs/<id>.json` (final, with `rows`, `lookups`, `bills_new`, `releases_new`, `print_pages`, etc.), `pages/<id>.json` for every key named by a row's `_page` / Tracker story code / Article ID / Story ID placeholder (`sheet_task.py page_doc_id`, `check_page` reads `scoped` first, then `clean`; this is the saved article HTML, unavoidable), `reprints/*.json`, `authors/*.json` and `translations/*.json` for new finds (hl/text), and any `edits` and team `tones` the PC copy should honour. Releases in `releases_new` with no `html`/`text` get fetched first (prompt step 3).
- Other inputs the PC has locally: workbook, library, `copies/articles/manifest.json` + `articles/<year>.json` for the years `copies_needed` returns (`sheet_task.py:4576`: finds' dates +-90 days, reprints' story years, releases -14..+90 days; it also lists `articles/releases.json`), pipeline files, `lookup_cache.json`, `release_texts.json`, `release_related.json`, `gabriel_bills_leginfo.json`, `idmap.json` (optional `--idmap`).
- Commands (step 3): `sheet_task.py --db db.json --xlsx in.xlsx --out out1.xlsx --result result.json --pages-dir pages --copies copies --copies-out copies_out --img-cache img_cache --bills ... --release-texts ... --release-related ... --queue queue --today <LA date>`, then `build_data.py`, `relmatch.py`, `sheet_task.py --after-relmatch`. Step 5 writes `ids`, `sheet`, `review` back to the db docs; steps 5 to 6 delete consumed `edits`/`pages` docs. With a PC copy these write-backs become local file edits (the saver replaces them).

### 7e. Fields the duplicate and reprint logic read (so the exported file can be defined)

**In the page (Update JS). It never reads article text of existing stories** (`getHtml/htmlOf/FT/local` do not appear in 40-43; the page header says "this page never decides a reprint by text", `41:1-6`). Text of a find's own page is read in the page (headline/byline/date extraction, `tfClean` `40:540`) but existing stories contribute headlines, links and outlets only.

Per existing story `r` in `D`:
- `id`; `link`, `plink` (publisher URL and NewsBank/other link; `dupOf` `40:297-302`, `knownIndex` `40:35-37`, `dupSameOutlet` `40:285-290`, `reprintFor` `40:76-79`); library/search links are ignored (`DUP_OFFSITE` `40:277`).
- `hl` (normalized `normH`; exact-headline index `knownIndex` 35-40, `reprintOf` 72-75, `dupWords` Jaccard >= 0.7/0.9 `dupOf` 313-327, first-segment `covHlSeg` 51-52, `REPRINT_MIN` 25 chars `40:47`).
- `date` (within 14 days for Jaccard match, 1 day for short headlines, 7 days for segment matches: `40:309,324-326`, `knownHl` `:44`).
- `outlet`, `pub` (`ranIn` `40:66-70`, `dupSameOutlet`, `dupCredits` `40:292`, `outletFor` `:57-59`, `outletGroups`).
- `also` (string "A; B") and `reps` (array `{aid,outlet,date,county,state,link,hl,src}`): "Reprinted in" names via `alsoNames` (`02_state.js:127`), `ranIn`, `foldReprint` `40:~330`, `applyReprints` `41:971-984`, `syncReps` `00_head.js:43`.
- For outlet-derived fields of NEW rows: `media`, `county`, `state`, `reach`, `lang`, `fmt`, `pub`, `outlet` of all stories with the same outlet (`covMedium/covCounty/covReach/covReachBlank` `40:134-210`, `REACH_BASE` `:53`).
- Others used for display or tagging: `topic`, `bills`, `tone`, `author`/`authors`, `hl_en`/`text_en` (only to diff before/after, `43:94-97`), `prid`/`kind` for releases, `added` (Log grouping), `year`, `code`/`aid` (temp codes, `00_head.js:14-17`).
- The `rows` block (all Coverage rows, including Reprints, Removed and "Reprint (unverified)", which `D` omits: `reprint_rule.py:29-40`, `build_data.py:27-30`): columns `aid, sid, kind (O/R/X), outlet, date, hl, links[]` (`build_data.py:347`, `covLoad` `40:105-124`), used for exact link match (`covLink`), headline and first-segment match with date window (`covHit` 134-150), "story already has a row from that outlet" (`covRepKnown` 152, `sidOn`), plus `next` counters (`COV.next`, ids for placeholders).
- Collections: `clips` and `reprints` and `edits` (removed) so earlier-run finds are not re-added (`41:991-996`, `43:63-70`); `runs` for `searched_to`.
- `fetchrules`, `billsinfo`, `ins-release_pickup`, `data/release_texts.json`: reference data, not per-story (see 7b).

Hard dependencies on existing-story data, so the export file must contain at least: per story `id, date, outlet, pub, hl, link, plink, also/reps outlets, media, county, state, reach, lang, fmt, topic, bills`, per Coverage row `aid, sid, kind, outlet, date, hl, links`, `next`, `idmap`, `covcols`, plus the reference blocks. No article text is needed for the page logic.

**In the PC save (sheet_task.py, reprint_rule.py, wireblend.py, relcopy.py, copy_check.py). Article text IS needed here, from the PC's own library, not from the Update file.**
- Candidates: `Task.originals()` (`sheet_task.py:1537-1546`) reads, for every Original row with a Story ID: `Article ID, Story ID, Date, Headline, Outlet, Outlet city, Medium, Publisher, Language, Author / byline, Author title, Press release, Data Source, Edition, Original or reprint, Translated Headline`, plus the AV tab `Item type` (`av_items` `:1547`). `reprint_rule.candidates` (`reprint_rule.py:801-823`) uses `Date` (+-90 days, `TEXT_WINDOW_DAYS` :42), `Headline` overlap, outlet type from `Outlet/Outlet city/Medium/Publisher/Language` (`row_type` :534), `is_av_item`. `pair_class` :854 and `rank/choose_original` :748-763 use `Outlet, Author / byline, Data Source, Edition, Press release, Date`, credits (`credit_of` :614), reporter employment (`reporters.py`, `reporter_employment.csv`).
- Text of the existing Original: `copy_html(sid)` (`sheet_task.py:1608-1625`) reads `copies/articles/manifest.json` + `articles/<year>.json` shards (full cleaned article HTML of the candidate), compared with the find's page by `RR.text_verdict` (>= 25-word runs covering >= 90% of both, `reprint_rule.py:1-16,243`). Only candidates within +-90 days and passing the type prefilter are read, but that requires the years from `copies_needed` (`sheet_task.py:4576`). Release checks also read library files via `row_versions` (`sheet_task.py:2666-2680`: `File name`, `File name 2` under `library/<year>/`, via `REL.file_versions`).
- `wireblend.py` (`signals/detect` :28-76, `add_pickups` :90): `Article ID, Story ID, Date, Outlet, Original or reprint, Publisher link, NewsBank article link, Uses wire copy of, Press release, Team note, Outlet state` and the texts of the wire original and the candidate.
- `build_data.py:347` is rebuilt from the workbook after the save, so the page-side `rows` index is regenerated, never carried.
- Conclusion: the Update export file needs NO article text; the text-based reprint decision happens only on the PC at save time with the PC's workbook, library and `articles/` shards. The only article-like text in the Update output is the `pages` docs (clean / scoped HTML of new finds and of reprint/originator candidates), which must travel to the PC unavoidably. `data/release_texts.json` (release body text, 1 MB) is read by the Update page for pickup searches (`41:555`); it is press release text, not article text, but it is large.

## Biggest risks

1. The page shell (HTML, CSS, header and Manage panel markup, fonts) is not in the repo and cannot be generated; it exists only in the live artifact (or kit zips). Nothing local can render the real look until it is pulled and stripped with `make_shell.py`. Without it SAMELOOK-v1 is not testable.
2. The page expects a `window.claude` db with realtime `onSnapshot` semantics. Notes, views, team tones, translations, hand edits and the Log pane all need a faithful local shim, and localStorage/IndexedDB are per-origin, so the local server needs a fixed port.
3. Update code is entangled with Manage, Log, edit-any-story, translation (`TF*` helpers), `cleanLocal` and `U`; no off switch exists. Safest is "run without mcp/sample + CSS hide" (as the viewer copy does), not deleting files.
4. `legacy_index.html`, `sid_map.json`, `build/insights/*` and `make_copies.py` inputs are missing: the build works with stubs, but fallbacks for blank workbook cells, the Insights and release-pickup blocks (also read by Update), and the `articles/` and `img/` shards cannot be reproduced from this repo. Compare a rebuilt page with the live one before trusting it.
5. Windows: `tzdata`, `cairosvg` (native Cairo), `pdftotext` (poppler) must ship with the portable folder; Mac paths in `sheet_task.py:155-157`; `build.sh` and test scripts are bash.
6. The save pipeline needs the full `articles/<year>.json` shards at save time for the +-90 day window (`copies_needed`), and `apply_all_patches.py` fails outright on this repo layout (docs at `docs/`, no `work/sid_map.json`, no `build/shell`), so the PIPELINE copy step must be rewritten or fed the missing inputs.
7. The Update export must carry the `rows` index including removed and unverified rows; leaving them out would let a run re-add them.
