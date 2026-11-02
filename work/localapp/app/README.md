# The PC tracker: one app folder ("AJG Tracker")

Assembled by `assemble_app.py` from the finished pieces (page build, server, update folder, saver, winpack). Decisions behind it: LOCALAPP-v1, UPDATEFOLDER-v1, UPDATESTATION-v1, SWITCHOVER-v1, GOVIT-v1, and **MULTIPC-v2** (each person keeps a LOCAL copy of the folder; one keeper takes in updates and passes a refresh file to the others; MULTIPC-v1, the shared network folder, is replaced).

## Folder layout

    AJG Tracker\
      Start Tracker.cmd         double-click to start (pushd, python -B -X utf8 -I, Edge app mode at http://127.0.0.1:8765/)
      READ ME FIRST.txt         one page of instructions for the person using it
      layout.json               {"pipeline": "app/pipeline", "saver": "app/saver/saver.py"}  (updatefolder/layout.py overrides)
      python\                   NuGet CPython 3.13.16 (as probe/build_probe.py) + python313._pth (and python._pth): Lib, DLLs, ..\app\site-packages
      app\
        site-packages\          the 10 pinned wheels (winpack/requirements-win.txt), tests folders left out, precompiled
        server\                 server.py, claude_shim.js            (unchanged copies)
        updatefolder\           formats, layout, make_for_update, take_update   (unchanged copies)
        saver\                  saver.py, saver_diff.py (unchanged), saver_steps.py (winpack patch 03 applied to the copy), pipeline_sha.py
        pipeline\               code\ + vendor files from the page build, winpack patches 01 and 02 applied, pdftext_pypdf.py, PIPELINE.sha256 regenerated
        station\                the layer written for this folder: launcher.py, station_server.py, station_cli.py, refresh.py, post_save.py,
                                plain.py, common.py, web\panel.js, selfcheck.py
        docs\                   FORMAT.md, IT_NOTE.md, winpack README, this file
        APP_FILES.sha256        sha256 of every app\ file except site-packages;  BUILD_INFO.json  versions, nupkg and wheel hashes, source commit
      data\                     everything that changes (nothing outside this folder is ever written)
        role.json               {"role": "keeper"} or {"role": "reader"} (default reader)
        workbook\  library\  backups\  state\ (ledger.jsonl, logs\, app.lock, refresh_*.json)
        copies\articles\        article shards (the page reads them through the server's /articles/ route; the save reads them too)
        db\                     notes, views, edits, runs ... (personal to this copy)
        site\                   index.html, data\sheet.json, data\release_texts.json, img\   (what the browser loads)
        for_update\  refresh_out\  updates\{incoming,staging,work,done,rejected,refresh_incoming}   tmp\   site_replaced\ (old page files, kept)

## How to assemble

    python3 -I work/localapp/app/assemble_app.py --target windows --library-mode hardlink --zip     # the product (needs internet: NuGet, PyPI)
    python3 -I work/localapp/app/assemble_app.py --target linux --role keeper                          # the test build

It builds the page first (work/localapp/build/build_tracker.py; needs `--legacy` and `--live-site`, defaults point at the scratchpad copies), then python\, site-packages (winpack/fetch_wheels.py, hash-checked), the code, and `data\` from COPIES of the snapshot workbook and library (data\ in the repository is only read). `--code-only` refreshes the code in an existing build. `--data-mode empty` leaves data\ empty. The zip leaves out data\library unless `--zip-library`.
The Linux target uses a venv in place of python\ (a `.pth` file does what `python313._pth` does on Windows).

## What each button does (the "Tracker files" panel, bottom right of the page)

The page is the tracker as built, plus one style block that hides the Update buttons and the tone, author and translation buttons (the list of code/make_viewer.py:25 without the download entries), plus the panel script. Downloads stay visible. Every call needs the per-launch token.

| Button | Who | What it does |
|---|---|---|
| Make "for Update" file | keeper (any copy can) | runs updatefolder/make_for_update.py, then downloads the JSON (about 7 MB, no article text) |
| Bring in update | keeper | the zip goes to data\updates\incoming; `take_update` checks it (allow-list, caps, hashes) and the saver runs a **preview**; the panel says in words what would change and which items need a person. A fingerprint warning needs "Use it anyway". **Save** runs the saver (backup first, checked swap, pages add-only, ledger, newest 3 backups kept), then the tracker's own sync (page, article shards, the pipeline's state files) and reloads the page |
| Accept the workbook as it is now | keeper | explicit confirm; refuses while Excel has the file open; `saver init` with the sha it just showed (refused if the file changed again meanwhile) |
| Make refresh file / Make FULL refresh | keeper | one zip for the other copies (below) |
| Bring in refresh file | reader | takes a refresh zip (below) |
| Rebuild the page | everyone | build_data + assemble from the workbook as it is now (the pipeline-only build of build.sh, no bash) |

The panel shows plainly: another save is running (on which PC, how long), Excel has the workbook open, the workbook is not the one the tracker last saved. One job runs at a time per PC; the station lock `data\state\app.lock` and the saver's lock stop two people saving at once on one folder.

### Refresh files (MULTIPC-v2)

`manifest.json` has format, format_version, created_at, kind (full or incremental), seq (the keeper's ledger line count), base_seq (the previous refresh), the workbook sha, and the sha256 and size of every file. Contents: `workbook/`, `library/` (incremental: the pages the saves since the previous refresh added, found in the saver's own save logs; full: the whole library), `site/` (index.html and data\*; a full refresh also img\), `copies/articles/` (shards that changed; full: all). Never notes, views, edits or anything from `db\`.
A reader checks names (allow-listed folders and file types, no scripts), caps (300,000 files, 4 GB, 512 MB a file, 200x expansion) and every hash **before anything is written**; refuses a refresh that is not newer than the one it applied last; refuses an incremental one that skips a refresh it never got (asks for a full one); backs up its workbook; swaps in the new one atomically and checks the sha; adds library files that are missing (existing names are skipped); replaces the page files (old ones kept in `site_replaced\`); records the new workbook with `saver init`; reloads. Notes and saved views are not touched.

## Changes to other pieces, all made outside them (wrapper, copy or patch at assembly)

1. `saver_steps.py` copy gets winpack patch 03; `release_rule.py` and `img_embed.py` copies get patches 01 and 02; `pdftext_pypdf.py` added; `PIPELINE.sha256` regenerated (assemble_app.py has its own small unified-diff applier and refuses a patch that does not match exactly once).
2. `take_update.py` and `make_for_update.py` start children with `python -I` only. `station_cli.py` swaps their `subprocess` for a shim that adds `-B -X utf8` and `AJG_NO_NETWORK=1`; it also points temp files at `data\tmp`. They are also told `--legacy app\pipeline\legacy_index.html` (make_for_update's CLI does not look for it by itself, so the "for Update" file would lack the fields only the old page carries).
3. `server.py`: not edited. `station_server.py` subclasses its handler, adds the script/style to the served page (monkey-patching `inject_shim`), the `/articles/` route, the `/_local/station/*` endpoints and a streaming upload (the base server holds bodies in memory, capped at 64 MB).
4. `take_update.save` is called with `rebuild=True` (the saver's rebuild into its working folder). The saver "never writes" the page, the shards or the pipeline folder, so `post_save.py` copies them in afterwards (page, changed shards into `data\copies\articles`, and `lookup_cache.json`, `outlets.json`, bills, release texts and release related into `app\pipeline`, then writes PIPELINE.sha256 again; old versions are kept aside). This is the "adapter" job of SAVER_SPEC section 8 and fixes the nested-shard bug of the manual 2026-10-30 save. If the saver's rebuild fails, the page is rebuilt the plain way.
5. The article shards live once, in `data\copies\articles`; the server serves `/articles/<file>.json` from there instead of keeping a second copy in `data\site`.
6. Offline photos (HANDOFF_PC_APP point 6): take_update does not give the saver an `--img-cache`, and without one the saver skips its photo step and leaves remote `<img>` tags in the cleaned copy. The subprocess shim adds `--img-cache data\img_cache` (an empty folder), so the step runs, every fetch fails at once (patch 02) and the images go with their wrappers. Tested: a saved page that carried a remote photo has none in the library copy or the shard (`_original_html` keeps the raw page).
7. B10 (same handoff, point 8): `station_cli` refuses a second take-in of a run id that the saver's ledger, the local db (`sheet.written`) or a finished update already holds (`ALREADY_SAVED`), at inspect and again at save.
8. The pipeline folder is therefore written by the tracker after a save (the keeper copy only). FORMAT.md said "never written".

## Tests

    python3 -I -m unittest discover -s work/localapp/app/tests -p test_station.py -v       (about 15 minutes: real previews and saves on the real workbook; 13 tests)

Needs the Linux test build, node and Playwright at /opt/node-tools. Results are in the report that came with this folder; screenshots in the scratchpad `app_build/test_shots`.

## Still needs a Windows round

- `python313._pth` (and `python._pth`): whether Windows honours the file, and that `-I` pipeline scripts find `app\site-packages` (run `python\python.exe -X utf8 -I app\station\selfcheck.py`).
- pandas and numpy `.pyd`/`.dll` loading from a user folder on the office PC (AppLocker); a pandas-free fallback is described in winpack/README.md.
- Edge app mode (`--app=`) opening at the fixed address; what happens if Edge is not at the usual path (the default browser opens instead).
- Speed: the preview and the save run build_data five or more times on the real workbook (about 80 s per preview here on Linux).
- Excel detection on Windows (opening the file for writing is refused when Excel holds it).
- `os.replace` of the workbook while a virus scanner holds it; very long library paths (the folder should stay near the drive root).

## How to use (plain words)

**Starting.** Double-click **Start Tracker.cmd** in your copy of the folder. A black window opens (leave it open) and the tracker opens in an Edge window. Closing the black window stops the tracker. If it is already running, double-clicking just opens it again.

**Everyone.** Your notes and saved views stay in your own copy; nobody else sees them, and a refresh never touches them. The **Tracker files** button (bottom right) shows whether Excel has the workbook open and whether a save is running.

**Keeper (Sammy).** Each time you want new stories:
1. Tracker files, **Make "for Update" file**. It downloads a file; keep it.
2. In the Update station, load that file and press Update, then download the update zip.
3. Tracker files, **Bring in update**: drop the zip in. Read what it says it will change and the list of items that need a person. If it warns that the update was made from an older workbook, the clean fix is to start again at step 1; "Use it anyway" is there if you know what you are doing. Press **Save**. The tracker backs up the workbook first, saves, rebuilds the page and reloads it.
4. Tracker files, **Make refresh file**. Pass the file it downloaded to the others (shared drive, email or Teams). For a new person, make a **FULL refresh** instead (bigger: it carries the whole library).
If you edit the workbook in Excel yourself: close Excel, then press **Accept the workbook as it is now** once.

**Readers.** When the keeper sends a refresh file, open the tracker, press Tracker files, and drop the zip into **Bring in refresh file**. Your workbook, article pages and page data are brought up to date, your old workbook is backed up first, and the page reloads. If it says the refresh is older than what you have, you already have it. If it says it skips a refresh you never got, ask the keeper for a FULL refresh. Readers cannot save updates; that is by design.

**Setting up a keeper copy (once).** Put `{"role": "keeper"}` in `data\role.json` (a copy without that file is a reader). Put the current workbook and library in `data\`, press **Accept the workbook as it is now**, then **Rebuild the page**.
