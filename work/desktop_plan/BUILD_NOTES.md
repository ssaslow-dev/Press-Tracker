# BUILD_NOTES: technical appendix for the builder agents

Companion to PLAN.md (2026-10-30). Read START_HERE.md, HANDOFF.md 0.3, 4, 5, 6 and `code/sheet_task_prompt.md` first. DECISIONS.md wins over this file. Nothing here changes a data rule.

Conventions: `L` = the library folder (source). `APP` = the installed folder on the PC (`AJG Tracker\`). All agent code runs with `python -I`. Model split per MODELS-v1: Haiku for fetch/copy/bundle loops, Sonnet for building, Fable for the save rules and the final review.

## 1. File layout

### 1.1 Source tree (new, under `L/app/`; nothing under `L/code` or `L/build` is edited)

```
L/app/
  ajg/                      package
    __init__.py
    config.py               paths, settings (see 1.3), version
    store.py                runs / inbox / pages JSON store (section 3)
    saver.py                the save (section 4)
    site.py                 build site/ from the workbook (section 5)
    server.py               local HTTP app (section 6)
    mcp_server.py           connector (section 2)
    refdata.py              lookup_reference / record_lookup over L reference files
    winlaunch.py            find Edge, open --app window, single-instance port file
  main.py                   entry: `main.py serve | mcp | build | save --run ID | doctor`
  pipeline/                 COPY of build/pub/pipeline/ as shipped (code + tabs + insights + json), never edited by hand; refreshed by `tools/sync_pipeline.py` from the L build
  tools/
    sync_pipeline.py        copies build/pub/pipeline -> app/pipeline, writes PIPELINE.sha256
    make_bundle.py          builds the Windows zip on Linux (section 7)
    mcpb/manifest.json      MCPB manifest (section 2.4)
  tests/                    pytest; reuses build/tests fixtures (section 8)
  requirements.txt          pinned: openpyxl, pandas, beautifulsoup4, lxml, langdetect, mcp, keyring (button phase), pillow (only if img_embed needs it: check)
  README_APP.md             one page for Sammy / successor: unzip, run, install .mcpb, where files live
```

### 1.2 Installed folder on the PC

```
AJG Tracker\
  AJG Tracker.cmd           launcher: start "" py\pythonw.exe -I app\main.py serve
  AJG Tracker (Claude).mcpb the connector bundle (also installable from Claude Desktop settings)
  py\                       python.org embeddable 3.13 x64 + python313._pth edited to add ..\lib
  lib\                      vendored site-packages (win_amd64 + pure wheels, unpacked)
  app\                      = L/app
  library\                  THE library, moved from the Mac (same layout: <year>\, _original_html\, Press releases\, Backups\, _to_delete\, _docs\)
    AJG Coverage - NewsBank.xlsx   the master, unchanged name
  data\
    runs\<run-id>.json      run docs (CONTRACT "Proposed rows"), one file per run
    inbox\                  imported web-tracker runs and downloaded run exports, before import
    pages\<rp|og>-<hash6>.json  saved page docs waiting for a save
    edits\, reprints\, tones\, authors\, translations\, notes\, views\   mirrors of the artifact collections, one JSON per doc
    state.json              master sha, last save, searched_to, next ids as last computed (informational; sheet_task.py recomputes)
    lookup_cache.json       LIVE copy (pipeline/lookup_cache.json is the shipped seed)
  site\                     built page + copies: index.html, data\, articles\, img\, pdf\
  logs\                     one file per save and per Update run (rotating, never pruned by code)
  SHA256SUMS.txt            of py\, lib\, app\ as shipped
```

Decision 2 in PLAN: `library\` is on the local disk. If Sammy picks OneDrive for `Backups\`, `config.py` takes `backups_dir` separately; the saver copies the backup there and verifies its sha after the copy.

### 1.3 Settings (`APP\settings.json`, created by `main.py doctor` on first run)

```json
{"library_dir": "C:\\Users\\<u>\\AJG Tracker\\library",
 "workbook": "AJG Coverage - NewsBank.xlsx",
 "backups_dir": null,
 "port": 8747,
 "edge_app_mode": true,
 "tz": "America/Los_Angeles"}
```

No key or secret ever goes in this file. The TinyFish key (button phase) is stored with `keyring` under service `ajg-tracker`, user `tinyfish`.

## 2. Connector tool contracts

Transport: stdio, Python `mcp` SDK (`FastMCP`). All tools return JSON text. Every tool is read-only except `import_run`, `record_lookup`, `add_find`, `save_run`, `rebuild_site`; those are annotated `destructiveHint`/`readOnlyHint` accordingly. Errors are returned as `{"ok": false, "error": "...", "hint": "..."}`, never raised across the wire. No tool opens a network connection in phases 1 to 4.

| Tool | Input | Output | Notes |
|---|---|---|---|
| `tracker_status()` | none | `{master: {path, sha256, mtime, size, excel_open, lock_file}, runs: {pending: [ids], last_saved: {id, at, line}}, site: {built_at, stories, copies}, app: {version, pipeline_sha}}` | First call Claude makes. `excel_open` = `~$` file present OR open-for-append fails |
| `list_runs(status="pending"\|"all", limit=20)` | | `[{id, at, since, finds, rows, releases_new, sheet: {written, line}}]` | Reads `data\runs\` |
| `get_run(run_id, part="summary"\|"rows"\|"review"\|"full")` | | the run doc or the named part | `rows` are the proposed rows in `covcols` order; `review` = the lists in sheet_task_prompt step 5 |
| `import_run(source, payload=null, path=null)` | `source` = `"artifact-db"` or `"file"`; `payload` = `{runs: [...], pages: [...], edits: [...], reprints: [...]}` as read from the web tracker's ArtifactData; or `path` = a downloaded export in `data\inbox\` | `{imported: {runs: n, pages: n, edits: n, reprints: n}, run_ids, skipped_existing}` | Doc ids unchanged. A run that already exists locally with `sheet.written: true` is skipped, never overwritten. Validates each run against CONTRACT "Proposed rows" (`store.validate_run`) and rejects a payload with a row that would overwrite a non-blank cell by construction (no such field exists; defence in depth) |
| `search_tracker(query, fields=["headline","outlet","author"], limit=25)` | | `[{story_id, article_id, date, outlet, headline, original_or_reprint}]` | Over `site\data\rows.json` (the built page's rows block); no workbook read |
| `get_story(story_id\|article_id)` | | the story's rows + copy file names + release links | From the built blocks, same data the page shows |
| `lookup_reference(kind, key)` | `kind` ∈ `url`, `outlet`, `reporter`, `host` | `{found: bool, source: "outlets.json"\|"reporters.json"\|"reporter_employment.csv"\|"outlet_rules.json"\|"lookup_cache.json", record, needs_fetch: bool}` | LEARN-v1 as a tool. `needs_fetch` comes from `lookup_cache.Cache.load().needs_fetch(url)`. Claude's instructions (in the tool description): call this before any web lookup |
| `record_lookup(kind, key, answer, evidence_url, confidence)` | | `{written: true, file}` | Appends to the live `data\lookup_cache.json` (never the shipped seed) in the format `lookup_cache.py` reads; outlets/reporters records are NOT edited by this tool (those changes stay a human-reviewed DECISIONS step) |
| `add_find(url, text, meta)` | `meta` = `{headline, outlet, date, author, source: "claude-chat", note}` | `{run_id, find_id}` | Creates a one-find run in `data\runs\` in the Update-button shape, with `_page` saved under `data\pages\`. Goes through `sheet_task.py` like any button find. This replaces the draft's `propose_rows`: Claude supplies a find, never a row |
| `preview_save(run_id=null)` | null = newest pending run | `{run_id, ok, exit_code, verification, changes: {rows_added, cells_filled, removed, originals_rebuilt, releases}, diff_path, problems: [...], confirm_token}` | Runs section 4 steps 1 to 6 into a scratch copy; nothing under `library\` changes. `confirm_token` = sha256 of (run_id + master sha + diff file sha), valid 30 minutes |
| `save_run(run_id, confirm_token)` | | `{written: bool, line, new_sha, backup, pages_added, removed_moved, site_rebuilt, log}` | Refuses without a matching token (master unchanged since preview). Section 4 |
| `rebuild_site(reason)` | | `{built_at, index_sha, stories, copies}` | For after a manual Excel edit. Reads the master, writes `site\`. No workbook write |

Tool descriptions carry the standing rules in one line each: reference data first; never log in or bypass paywalls; YouTube and advocacy blogs are not coverage; free sources only; nothing scheduled.

What is NOT a tool: publishing to claude.ai (Claude does that itself if a viewer refresh is wanted, from `site\`), deleting anything, editing the workbook outside `save_run`, reading `settings.json` secrets.

### 2.4 MCPB manifest (essentials)

```json
{"manifest_version": "0.3", "name": "ajg-tracker", "display_name": "AJG Tracker",
 "version": "0.1.0", "description": "Read the AJG press tracker, review finds, save runs to the workbook.",
 "server": {"type": "binary", "entry_point": "py/python.exe",
   "mcp_config": {"command": "${__dirname}/py/python.exe",
                  "args": ["-I", "${__dirname}/app/main.py", "mcp"],
                  "env": {"AJG_HOME": "${user_config.app_dir}"}}},
 "user_config": {"app_dir": {"type": "directory", "title": "AJG Tracker folder",
                 "description": "The unzipped AJG Tracker folder", "required": true,
                 "default": "${HOME}/AJG Tracker"}},
 "compatibility": {"platforms": ["win32", "darwin"]}}
```

Two packaging choices, pick at phase 3 after the PC test: (a) the `.mcpb` contains `py\`, `lib\` and `app\` itself (about 100 MB; self-contained; `${__dirname}` works); (b) a 50 KB `.mcpb` whose command points at the already-unzipped folder through `user_config.app_dir` (`"command": "${user_config.app_dir}/py/python.exe"`). (b) keeps one copy of the code; (a) survives the folder being moved. Default: (b). Fallback with no extension support: one entry in `%APPDATA%\Claude\claude_desktop_config.json` with the same command and args.

Note: the `uv` server type (host-managed Python) exists in the manifest spec but Claude Desktop support was not verified; do not depend on it.

## 3. Store (runs and friends)

- One JSON file per doc, `data\<collection>\<doc_id>.json`, UTF-8, 2-space indent, keys sorted (diff-friendly). Writes are atomic: write `<name>.tmp`, `os.replace`.
- Collections and doc shapes are exactly the artifact's (HANDOFF 0.5 table; CONTRACT "Proposed rows"). `sheet_task.py --db-dir data --db db.json` therefore works unchanged, because sheet_task_prompt step 1 already describes `db/<collection>/` on disk.
- `store.py` API: `list(collection, where=None)`, `get`, `put` (refuses to overwrite a run whose `sheet.written` is true unless `allow_closed=True`, used only by `save_run` to write the `sheet` line), `pending_runs()`, `validate_run(doc)`.
- Nothing is deleted. The prompt's "delete pages docs" becomes a move to `data\_applied\pages\<run-id>\`. Edits in `result.edits_clear` move to `data\_applied\edits\<run-id>\`.
- Web-tracker import (interim, decision 3): the chat session (claude.ai or Claude Desktop) reads the artifact's ArtifactData collections as today and passes them to `import_run(source="artifact-db", payload=...)` in batches of at most 50 docs per call. After `save_run` succeeds, the same chat writes `sheet: {at, written: true, line}` back to the artifact run doc (REQ-9) so the web tracker closes the run. If the chat has no ArtifactData tool, the fallback is the page's export file: a small patch to `43_update_log.js` adds "Export run" (the `downloads` capability is already declared) writing `run-<id>.json` with the run plus its pages/edits/reprints docs; Sammy saves it into `data\inbox\` and Claude calls `import_run(source="file", path=...)`.

## 4. Save safety rules (`saver.py`)

Transcribed from README rule 7, HANDOFF 6.1 and sheet_task_prompt rules 1 to 9. Fable reviews this module line by line in phase 3. Order is fixed; any failed step returns `written: false` with a line starting "Not written: " and leaves the run queued.

1. **Preconditions.** `settings.library_dir` exists and contains the master. No `~$AJG Coverage - NewsBank.xlsx`. Open the master with `open(path, "r+b")` and close it at once: a `PermissionError` means Excel (or OneDrive) holds it: stop. No `library\.sheet_task.lock` younger than 30 minutes; otherwise write it (`<run id> <UTC time>`). On exit, whatever happens, move the lock to `library\_to_delete\.sheet_task.lock.<run id>` (never delete).
2. **Identity.** sha256 the master; it must equal `data\state.json.master_sha` (the sha recorded after the last save, or the DECISIONS sha at migration). Mismatch = someone edited the workbook in Excel or OneDrive replaced it: stop with the two shas in the line, and tell Claude to call `rebuild_site` after Sammy confirms the file (which records the new sha). Size and mtime logged.
3. **Backup first.** Copy the master to `Backups\AJG Coverage - NewsBank BACKUP before run <run id> <YYYY-MM-DD HHMM>.xlsx` (unique name, never the master's own name: incident 2026-10-29). sha the copy; it must equal the master's. If `backups_dir` is set, copy there too and verify.
4. **Stage.** Work in `APP\work\<run id>\`: `in.xlsx` (copy of the master), `db.json` assembled by `sheet_task.py --db-dir data --db db.json --check-only` (exit 3 = nothing queued: write `sheet: {written: true, line: "Nothing new to write."}` and stop; a Refresh continues).
5. **Apply** = sheet_task_prompt step 3, verbatim, against `pipeline\` in `APP\app\pipeline\` and copies in `site\articles\`: `--copies-needed`, release candidates from `library\`, the main run with `--today` in `America/Los_Angeles`, `--lookup-cache data\lookup_cache.json --lookup-cache-out <work>\lookup_cache.out.json`, then `build_data.py`, `relmatch.py` when needed, then `--after-relmatch`. Exit 2 anywhere = verification failed: stop, first problems in the line. `release_new` items without html/text: in phases 1 to 4 the saver has no network; the run is held with line "Not written: N release pages need fetching; ask Claude to fetch and attach them" and Claude fetches them itself (claude.ai fetch) and calls `import_run` with the html added. (Button phase: the app fetches via TinyFish.)
6. **Preview** (this is where `preview_save` stops): cell-by-cell diff of `in.xlsx` vs the `--after-relmatch` output (reuse the diff logic of `build/tests/sheet_task` / `copy_check.py` where it exists; otherwise openpyxl values only). Allowed differences: new rows at the bottom of Coverage / Originals / Press releases / Audio & video / Removed; blanks filled; the enumerated exceptions in rule 2 of the prompt ("# of reprints", Removed moves, Original swap, RETRY/BLOCKED copy, decided queue merge, archive.org air date on added rows). Any other changed non-blank cell = stop with `problems` listing the first 20 cells. Writes `diff.tsv` and `confirm_token`.
7. **Commit** (only `save_run`, with a token whose master sha still matches): write the output to `library\AJG Coverage - NewsBank.xlsx.new-<run id>` beside the master, sha it, then `os.replace` onto the master path (atomic on NTFS; fails if Excel reopened the file). Re-read and sha the master: must equal the staged file's sha. Then `pages\<year>\...` etc. are copied add-only into `library\` (an existing name is listed in the run's review, never overwritten); removals `shutil.move` to `library\_to_delete\<same path>` with a line in `library\_to_delete\_moves_<date>.tsv`.
8. **Write back.** `sheet: {at, written: true, line, stories, ...}` on each run in `result.runs`; ids; reprint `aid`s; edits and pages moved to `_applied\`; `data\lookup_cache.json` replaced by the `--lookup-cache-out` file (after a JSON parse check); `state.json.master_sha` = new sha; `logs\save-<run id>.log` with every sha, path and exit code. Review-queue items (`result2.queue_docs`, `result.queue_applied`) are written to `data\queue\items\` and `data\queue\applied\` locally; the claude.ai review-queue artifact is not updated by the app (Claude may mirror them in chat if Sammy still uses that page).
9. **Rebuild** `site\` (section 5). A rebuild failure after a successful commit is reported as `written: true, site_rebuilt: false`; the workbook is right, the page is stale, `rebuild_site` fixes it.
10. **Never:** delete; write the master's name as a staging name; write when the sha check fails; write without a backup whose sha was verified; run two saves at once (a process-level lock `APP\work\.saver.lock` with the pid, in addition to the library lock); touch `~/Documents` copies, `AJG Combined Coverage.xlsx` or `Jesse_Gabriel_Mentions.xlsx`; call the network in phases 1 to 4.

Tests (phase 1): fixture = `build/tests/sheet_task/fixtures/example_db.json` + a copy of `work/coverage_current.xlsx`; cases: happy path (sha chain, backup exists, diff allowed), Excel-open simulation (hold the file open from the test), sha mismatch, exit 2, exit 3, stale token, two saves at once, a page name collision, a removal move.

## 5. Site build (`site.py`)

Same recipe as sheet_task_prompt step 6 and HANDOFF 4.3, local paths:
- `build_data.py <master> pipeline/legacy_index.html blocks/ pipeline/sid_map.json` → `tabs_data.py` (all tabs on a full build; `--only releases` after a save, as the prompt does) → `assemble.py pipeline/shell.html blocks/ pipeline/tracker.js site/index.html`.
- Copies: `make_copies.py` with `--img-cache data\img_cache` writes `site\articles\*.json`, `site\img\*.json`, manifest; `repack_img.py` is unnecessary locally (no 256 MB cap) but harmless.
- `data\sheet.json` is not needed locally (the page's download button can serve the master file directly: `server.py` route `/download/workbook` streams the current master). `data\release_texts.json` is copied as is.
- The page is served from `http://127.0.0.1:<port>/`, so its relative fetches of `articles/`, `img/`, `pdf/` work unchanged. Check `make_viewer.py`'s data-split (VIEWER-LOAD) is NOT applied: the local page keeps inline blocks; there is no 10 MB share limit on localhost.
- The Update / Refresh / Save-to-sheet buttons: hidden in phases 1 to 4 by the same selector list `make_viewer.py` uses (import its `HIDE` constant; do not fork the page). The button phase re-enables Update and points it at `server.py` routes instead of `window.claude`.

## 6. Local server (`server.py`, `winlaunch.py`)

- Stdlib `http.server` + `ThreadingHTTPServer`, bound to `127.0.0.1` only, port from settings (fallback: next free; port written to `APP\work\port`). No framework dependency in phases 1 to 4.
- Routes: `/` and static files under `site\`; `/api/status` (same JSON as `tracker_status`); `/api/runs`, `/api/runs/<id>` (read-only); `/download/workbook`; `/api/export/site.zip` (for the monthly viewer refresh, decision 4). No write routes until the button phase.
- Launcher: `main.py serve` starts the server, then opens Edge: look up `msedge.exe` in `HKCU\Software\Microsoft\Windows\CurrentVersion\App Paths` then `HKLM`, then Program Files; run `msedge --app=http://127.0.0.1:<port>/ --user-data-dir=%LOCALAPPDATA%\AJG Tracker\edge-profile` (separate profile so office Edge policies on the default profile don't collide; drop the flag if IT disallows it). If Edge is missing, `webbrowser.open`. Single instance: if the port file names a live server, just open the window.
- Mac (decision 9): same code; `ajg.command` runs `python3 -I app/main.py serve`; opener is `open -a "Google Chrome" --args --app=...` or `webbrowser`.

## 7. Windows bundle built on Linux (`tools/make_bundle.py`, Haiku)

1. Download `python-3.13.x-embed-amd64.zip` from python.org and verify its published sha256/signature. Unzip to `py\`. Edit `python313._pth`: add `..\lib` and `..\app`, keep `import site` commented out (isolation).
2. `pip download -r app/requirements.txt --platform win_amd64 --python-version 3.13 --implementation cp --abi cp313 --only-binary=:all: -d wheels/`; pure-Python wheels fall back automatically. Unpack each wheel into `lib\` (`python -m zipfile -e`, or `pip install --target lib --platform ... --only-binary=:all:` which does the same in one step). Reject any sdist.
3. Copy `L/app` to `app\`, run `tools/sync_pipeline.py` first so `app\pipeline` equals `build/pub/pipeline` (sha file written).
4. Write `AJG Tracker.cmd`, `README_APP.md`, `SHA256SUMS.txt`; zip as `AJG-Tracker-<version>-win64.zip` (expected 90 to 130 MB; pandas and lxml dominate. If size matters, check which 4 modules import pandas and whether openpyxl alone suffices: that is a Sonnet task with tests, not a bundle-time shortcut).
5. Smoke test on Linux is limited to `python3 -I -c "import ajg"` with the pure parts; the real test is Sammy's PC round (section 9). Use `mcpb pack` (Node, runs on Linux) for the `.mcpb`.
6. Never include: `settings.json`, any key, `work\`, the master workbook, saved copies.

`.mcpb` and zip both carry Mark-of-the-Web when downloaded; the `.cmd` launcher may show a one-time SmartScreen or "open file" prompt. `python.exe` itself is PSF-signed. If IT policy blocks `.cmd`, ship a `.lnk` shortcut to `py\pythonw.exe` with arguments instead (make it on the PC in the first test round; `.lnk` files cannot be made reliably from Linux).

## 8. Reuse of existing code (what is new vs kept)

| Existing | Used as | Changes |
|---|---|---|
| `code/sheet_task.py` + rule modules (reprint_rule, release_rule, relmatch, reltab, avtab, authorsplit, dates, lookup_cache, media_gate, ...) | The writer. Called as a subprocess exactly as the prompt does | None |
| `code/sheet_task_prompt.md` | Spec for `saver.py` (steps 1 to 7 → sections 4.4 to 4.9) | The prompt itself is rewritten in phase 3 to "call the connector": read runs with `list_runs`, `preview_save`, confirm, `save_run`, then write `sheet` back to the artifact run (interim). Save the new version as `code/sheet_task_prompt.md` v2 via apply_all, by its owner, not by the app agents |
| `code/build_data.py`, `assemble.py`, `tabs_data.py`, `tabs_assemble.py`, `insights_*`, `make_copies.py`, `img_embed.py` | `site.py` | None |
| `code/make_viewer.py` | `site.py` imports its `HIDE` constant (the `VIEWER-HIDE` style block) and inserts it before `</head>`; it does NOT apply the data split (`LOADER`) | None; the local page keeps `[data-dl]` visible by stripping that selector from the imported string, since the download route exists locally |
| `code/tracker/40–43_update_*.js` | Spec for the button phase; the search plan, pre-filters, `TF_GAP`, `searched_to` rules are ported to `ajg/update/*.py` | JS stays for the web tracker; `test_nosched.py` and the update_js suites keep guarding it |
| `code/lookup_cache.py`, `outlets.json`, `reporters.json`, `reporter_employment.csv`, `outlet_rules.json` | `refdata.py` reads them | None; `record_lookup` appends only to the live cache copy |
| `build/tests/*` (42 suites, `run_all.sh`) | Run unchanged in CI of the app repo, plus `app/tests` | None |
| `build/build.sh` | Stays the proof that LIB = PIPELINE; `sync_pipeline.py` copies the result | None |
| `code/make_handoff_kit.py` | Phase 4 uses its `verify` to check the library copy | None |
| Artifact publish steps (HANDOFF 4.4) | Only for the optional monthly viewer refresh from `site.zip` | No app code |

## 9. PC test rounds (what Sammy reports back each time)

Round 1 (phase 2): unzip to `%USERPROFILE%\AJG Tracker`, double-click the launcher. Report: did a window open; the first line of `logs\serve.log`; any SmartScreen / IT dialog text verbatim; output of `main.py doctor` (Python version, Edge found, library path, write test in `library\_to_delete\`).
Round 2 (phase 3): install Claude Desktop (if absent), double-click the `.mcpb`, open a chat, ask "what is the tracker status". Report the tools Claude lists and the status JSON.
Round 3 (phase 3): with a copy of the workbook named differently in a scratch library, "preview the latest run" then "save it". Report the diff line counts and the log file.
Round 4 (phase 4): the real library in place; first supervised save, Fable watching in chat; DECISIONS line with old → new sha and the backup name.

IT questions to ask before round 1 (one email): (1) may an unzipped `python.exe` run from the user profile; (2) is Claude Desktop installable or already deployed, and are desktop extensions allowed; (3) may Edge be started with `--app` and a separate `--user-data-dir`; (4) is `%USERPROFILE%` redirected to OneDrive.

## 10. Button phase (later; design only)

- `ajg/update/plan.py` (port of 40/41: outlets, keyword and site searches, dormant outlets, release check, pickups, GDELT TV via TinyFish fetch, since date, `searched_to` advance ≤ 2% failures), `ajg/update/tinyfish.py` (REST: `GET https://api.search.tinyfish.ai?query=`, `POST https://api.fetch.tinyfish.ai`, `X-API-Key` from `keyring`; 30/min and 150/min limits → keep `TF_GAP` 2.1 s), `ajg/update/prefilter.py` (free pre-filters from 41: links already in the sheet, never-coverage hosts, skip URLs, no Gabriel / no bill number).
- No classification in the app (no Claude API). The run is queued with `needs_review: true`; the connector gains `review_queue(run_id)` returning finds in classify-prompt batches and `set_decisions(run_id, decisions)` storing Claude's choices in the run doc in the same shape the page's `sample.json(classifyPrompt)` produced, so `sheet_task.py` sees no difference.
- Server routes `/api/update/start`, `/api/update/progress`, `/api/update/cancel`; the page's existing progress UI (`drawProg`) is re-pointed at them. Nothing scheduled: a run starts only from the button or `main.py update`.
- Rules carried over unchanged: FREEONLY, NOBLOGS, LEARN (pre-filter asks `refdata` first), never log in, BLOCKED – TinyFish on paywalls.
