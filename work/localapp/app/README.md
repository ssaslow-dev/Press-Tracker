# The PC tracker: one app folder ("AJG Tracker")

Assembled by `assemble_app.py` from the finished pieces (page build, server, update folder, saver, winpack). Decisions behind it: LOCALAPP-v1, UPDATEFOLDER-v1, UPDATESTATION-v1, SWITCHOVER-v1, GOVIT-v1, and **MULTIPC-v2** (each person keeps a LOCAL copy of the folder; one keeper takes in updates and passes a refresh file to the others; MULTIPC-v1, the shared network folder, is replaced).

## Folder layout

    AJG Tracker\
      Start Tracker.cmd         double-click to start (pushd, python -B -X utf8 -I, Edge app mode at http://127.0.0.1:8765/)
      READ ME FIRST.txt         one page of instructions for the person using it
      layout.json               {"pipeline": "app/pipeline", "saver": "app/saver/saver.py"}  (updatefolder/layout.py overrides)
      python\                   NuGet CPython 3.13.16 (see winpack/README.md) + python313._pth (and python._pth): Lib, DLLs, ..\app\site-packages
      app\
        site-packages\          the 10 pinned wheels (winpack/requirements-win.txt), tests folders left out, precompiled
        server\                 server.py, claude_shim.js            (unchanged copies)
        updatefolder\           formats, layout, make_for_update, take_update   (unchanged copies)
        saver\                  saver.py, saver_diff.py (unchanged), saver_steps.py (winpack patch 03 applied to the copy), pipeline_sha.py
        pipeline\               code\ + vendor files from the page build, winpack patches 01 and 02 and app patches 04 to 06 (PHOTOLINK-v1) applied, pdftext_pypdf.py, photolink.py, PIPELINE.sha256 regenerated
        station\                the layer written for this folder: launcher.py, station_server.py, station_cli.py, refresh.py, post_save.py,
                                plain.py, common.py, web\panel.js, selfcheck.py
        docs\                   FORMAT.md, IT_NOTE_APP.md, winpack README, this file
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

## What each button does (the "Tracker files" panel, opened by the masthead button directly left of Manage; TIDY-v1)

The page is the tracker as built, plus one style block that hides the Update buttons and the tone, author and translation buttons (the list of code/make_viewer.py:25 without the download entries), plus the panel script. Downloads stay visible. Every call needs the per-launch token.

| Button | Who | What it does |
|---|---|---|
| Make "for Update" file | keeper (any copy can) | runs updatefolder/make_for_update.py, then downloads the JSON (about 7 MB, no article text) |
| Bring in update | keeper | the zip goes to data\updates\incoming; `take_update` checks it (allow-list, caps, hashes) and the saver runs a **preview**; the panel says in words what would change and which items need a person. A fingerprint warning needs "Use it anyway". **Save** runs the saver (backup first, checked swap, pages add-only, ledger, newest 3 backups kept), then the tracker's own sync (page, article shards, the pipeline's state files) and reloads the page |
| Save my edits (N) | keeper | PCEDITS-v1. Stories removed or edited in the page wait in `data\db\edits`; N counts those not yet saved. The button (enabled when N > 0) previews in plain words (stories removed, stories edited, rows that move to the Removed tab, blank cells filled, edits the workbook's filled cells would not take) and then **Save** runs the same save (backup, checked swap, Excel/lock/workbook-changed refusals) with no update zip. Used-up edits docs are moved to `data\db\_applied\edits` (never deleted); edits that disagree with a filled cell are not applied and are marked reported; a refused save changes nothing. Bring in update's preview and save include the same pending edits and list them. Readers: no button (a one-line note says their edits stay in their copy), refused by the server and the job |
| Accept the workbook as it is now (under **Repairs**) | keeper | explicit confirm; refuses while Excel has the file open; `saver init` with the sha it just showed (refused if the file changed again meanwhile) |
| Set up from the Mac library | keeper, while there is no workbook (SWITCHOVER-v1) | see "Switch-over day" below |
| Switch-over changes (one screen, shown once) | keeper, after the setup, until Finished | DROPUNVERIFIED-v1, PRJUDGE-v2 existing rows, PRCOLOR-v1 recolour, OTHERFILES-v1 column and approved data-check fixes: previewed together, one backup, confirm all or step by step; see "Switch-over day" below |
| Make refresh file | keeper | one button, one zip for the other copies (below). It makes the short one (what changed since the last) when that can be complete, and a **full** one by itself when it cannot: the first refresh file ever made, no record of what the last one carried, a save since the last one whose added pages are not in its save log, or an added page no longer in the library (`refresh._needs_full`; the panel says why) |
| Make a FULL refresh file (under **Repairs**) | keeper | always the full one, for a copy that has never had a refresh |
| Bring in refresh file | reader | takes a refresh zip (below) |
| Rebuild the page (under **Repairs**) | everyone | build_data + assemble from the workbook as it is now (the pipeline-only build of build.sh, no bash) |

**Where it sits (TIDY-v1).** The button is a masthead button of the page's own class (`upd-btn`, same size, font and radius as Spreadsheet and Manage), directly left of Manage, for keeper and reader copies; an amber dot on it (like Manage's count) replaces the old amber button when Excel has the workbook open, a save is running or the workbook is not the one last saved. There is no floating button. The panel opens pinned under the masthead at the right (`top: var(--hdr) + 4px`) so it never covers the masthead buttons; opening it closes the Manage panel and the other way round. Sections for the keeper: 1 Make "for Update" file, 2 Bring in update, 3 Save my edits, 4 Make refresh file, then a closed **Repairs** fold (Accept the workbook as it is now, Make a FULL refresh file, Rebuild the tracker page; it opens by itself when the workbook needs accepting). Reader: 1 Make "for Update" file, 2 Bring in refresh file, Repairs (Rebuild the tracker page).

The panel shows plainly: another save is running (on which PC, how long), Excel has the workbook open, the workbook is not the one the tracker last saved. One job runs at a time per PC; the station lock `data\state\app.lock` and the saver's lock stop two people saving at once on one folder.

### Refresh files (MULTIPC-v2)

`manifest.json` has format, format_version, created_at, kind (full or incremental), seq (the keeper's ledger line count), base_seq (the previous refresh), the workbook sha, and the sha256 and size of every file. Contents: `workbook/`, `library/` (incremental: the pages the saves since the previous refresh added, found in the saver's own save logs; full: the whole library), `site/` (index.html and data\*; a full refresh also img\), `copies/articles/` (shards that changed; full: all). Never notes, views, edits or anything from `db\`.
A reader checks names (allow-listed folders and file types, no scripts), caps (300,000 files, 4 GB, 512 MB a file, 200x expansion) and every hash **before anything is written**; refuses a refresh that is not newer than the one it applied last; refuses an incremental one that skips a refresh it never got (asks for a full one); backs up its workbook; swaps in the new one atomically and checks the sha; adds library files that are missing (existing names are skipped); replaces the page files (old ones kept in `site_replaced\`); records the new workbook with `saver init`; reloads. Notes and saved views are not touched.

## Added in the consolidation round (2026-11-03)

- **Last updated (LASTUPDATED-v1).** `station.js` adds `<br><span id="ajg-lastupd">Last updated Nov. 2, 2026</span>` as the third line of the masthead subtitle (same element, so same font, size, colour and letter spacing). The date is the Pacific
  date of the newest ledger entry whose verb is a save or a switch-over change (`common.UPDATE_VERBS`, `last_updated`); a refresh file carries it (`manifest.last_updated`) and a reader copy shows the keeper's date.
- **View original (VIEWORIG-v1, PRINTORIG-v1 option B).** Patch 26 makes `build_data` list print originals found by name (`<Article ID or Print Article ID>_p<pages>.pdf` in `library\_original_pdf\<year>`, also in the save's staged pages) as `rec.po`; patch 27 shows
  "View original" in the story sheet for each (opens `/library/_original_pdf/<year>/<name>` in a new tab; the server serves only that name pattern). No file, no button.
- **PRCOLOR-v1 / PRJUDGE-v2 on the save.** Patch 22 (the station's per-item verdict), 28 (rows with Press release = Yes are coloured #7030A0, other hidden rows stay red), 23 (air date Pacific), 24 (print-page rows, Unlinked print pages writer, known-story copies), 25/26 (Other files).
- **A refresh job that stops moving is reported (CHAINCHECK-v1).** Making or taking in a refresh file touches `data\state\job_heartbeat`; the server tells the page "nothing has moved for N s" after 45 s and stops the job after 240 s (its half file and lock put away, "Nothing was changed").

## Switch-over day (SWITCHOVER-v1, DROPUNVERIFIED-v1)

**The empty tracker.** `assemble_app.py --data-mode empty` ships `data\` without a workbook, ledger or library. `data\site\index.html` is a one-screen page
(`src/launcher/no_workbook.html`) that says "No workbook yet: use Set up from the Mac library"; a reader copy is told to bring in the keeper's refresh file instead.
The snapshot's page and `sheet.json` are not shipped. What stays is the shipped page data: article data (`copies\articles`), photo shards (`site\img`), fonts, release texts and the pipeline.
A copy is a keeper copy only when `data\role.json` says so (the shipped one is a reader copy: edit it by hand once).

**Set up from the Mac library** (`station/setup_mac.py`, verbs `setup_check` and `setup_run`). Input: the copied "Tracker library" folder (its path is typed or pasted: a browser cannot hand a program a
folder's path) and the fingerprint list the Mac made (`shasum -a 256` format as `data/library_manifest.sha256`: `<sha256>  <path>`, paths relative to the folder, the workbook as `AJG Coverage - NewsBank.xlsx`;
chosen as a file, typed as a path, or found inside the folder). *Check* (read only) hashes every listed file in the workbook slot and the year folders, `_original_html`, `_original_pdf` and `Press releases`:
it reports by count and first 20 names what is missing, different, a cloud placeholder (0 bytes, or Windows "online only" attributes) or of a name or type a refresh file cannot carry (`refresh.check_name`),
and lists files the list does not name as extra (ignored; the list file itself, `.DS_Store`, `Thumbs.db`, `desktop.ini`, `._*` are not reported; Backups, Work archive and other folders are never read). A missing list line for the workbook is refused.
*Set up* repeats the check, copies into `data\tmp\setup_<stamp>` (hashing the source while copying, then the copy again), and only when every file checked out moves the files into `data\library` and the workbook into
`data\workbook`; any refusal leaves `workbook\`, `library\` and the ledger as they were. The source is never written. Then: the saver ledger is seeded (`init` with the workbook's sha), the page is built from the workbook
(`rebuild_page`: build_data + assemble from the pipeline copy, plus `sheet.json`), `data\state\logs\setup-<stamp>.json` is written and the summary shows stories, rows, library files, the fingerprint and how many stories
have a saved copy that the shipped article data does not hold. It refuses if a workbook is already there, unless it is run from Repairs ("Set up again", an explicit warning and tick box): then the old workbook is backed up first and
library files that differ from the list refuse the step. Reader copies refuse it (server and job).

**Switch-over changes** (`station/switchover.py`; verbs `switch_preview`, `switch_apply`, `switch_finish`, `switch_remove_file`; the panel's top section after the setup, hidden by *Finished*). Steps, in this order:
`drop_unverified` (below), `prjudge` (PRJUDGE-v2: the candidate rows in `station/data/prjudge_v2.json` are re-checked on the real workbook, a row that no longer matches by Article ID, Story ID, outlet, headline start or whose Press release cell is not
Yes is skipped and listed; own-release copies (Story ID is a Copy story ID on the Press releases tab) never change; the 118 other-issuer reposts become `No`, font back to automatic, Role filled from the headline on Originals that lack one, on Coverage and the Originals
mirror; 3 missed wire releases become Yes; 05166 (s01614) is left alone because its Original stays Yes; the 13 organisation-site posts are listed for Sammy), `prcolor` (every cell of a row with Press release = Yes gets font #7030A0, computed as the
workbook will be after `prjudge`), `other_files` (`other_files_column.py`), `datafix` (an approved proposals CSV from `work/localapp/datafix/*/`, uploaded in the screen to `data\switchover\datafix`; plain cell fixes on Coverage only, blanks only unless the line has
an `overwrite` column saying yes, confidence low left out unless ticked, link columns also get their hyperlink; the Originals mirror gets the same fill). One backup (`... BACKUP before switch-over changes <stamp>.xlsx`, made at the first confirmed step, reused by the rest).
Each step stages its own workbook, checks it cell by cell against the master (values, looks, font colours, hyperlinks, header, tabs; `switchover.check_cells`), swaps it in, writes its own ledger entry (`press_release_judge`, `recolor_press_releases`,
`apply_datafix`, `add_other_files_column`, `drop_unverified`) and re-seeds the baseline; a plan that changed since the preview (digest) is refused. The page is rebuilt once at the end. State in `data\state\switchover.json`.

**Remove unverified reprints** (`station/drop_unverified.py`, verbs `drop_preview`, `drop_apply`). Preview lists every Coverage row whose "Original or reprint" is "Reprint (unverified)" (Article ID, Story ID, outlet, headline), the
Audio & video rows with the same Article IDs, and the saved files (File name / File name 2, and any file named after the row's Article ID: `<nb|pq|ws><ID>...`, `<ID>_p<n>.pdf`, `.ocr.txt`) found under `library\<year>`,
`_original_html\<year>`, `_original_pdf\<year>`; a file another row of any tab still names is kept and listed as kept. Apply (after the tick box): backup (`... BACKUP before drop_unverified <stamp>.xlsx`, sha checked) ->
staged workbook with a unique name in `data\tmp` (rows removed in one pass, hyperlinks and row heights moving with their rows: `delete_rows_batch`, the effect of `sheet_task.delete_rows_keep_links`) ->
**the save program's own independent diff** (`saver_diff.compare`): the only differences allowed are exactly the planned rows missing on Coverage and Audio & video; any other cell, hyperlink, header or tab change refuses
before anything is replaced -> reserved ids written -> Excel and checksum re-check -> `os.replace` -> sha verified -> ledger line `drop_unverified` (before and after sha, backup, Article and Story IDs, files planned) followed by
the ledger's usual `init` -> the files deleted (each with its sha256 first written to `data\state\logs\drop-unverified-<stamp>.json`, then the log is completed) -> the page rebuilt. Not a normal save: a save refuses lost rows.
Refused when Excel has the workbook open, a save is running, the workbook is not the one last saved or accepted, or the token (workbook fingerprint + the list) is not the previewed one. The Originals and Removed tabs are not touched.

**Reserved ids.** sheet_task takes the next Article ID as the highest number on Coverage, Removed and Unlinked print pages plus one (build_data computes the same `next` for the Update station). Deleted rows would lower that
highest number, so their numbers are recorded in `data\state\reserved_ids.json` (floors: `article_floor`, `story_floor`; the lists `article_ids`, `story_ids`), written before the workbook is swapped. Two patches read it through the
environment variable `AJG_RESERVED_IDS` (set by `station_cli` for every child): `19_sheet_task_reserved_ids.patch` raises `max_num` and `max_s` in `Sheet.__init__` and makes `verify` refuse a new row that reuses a reserved Article ID;
`20_build_data_reserved_ids.patch` raises `NEXT['aid']` and `NEXT['s']`. A missing file changes nothing.

**Refresh files carry the deletions.** `refresh.make` lists every library file deleted since the previous refresh (a full one: all of them) in the manifest's `deleted` (`"library/<path>": sha256`, format_version 2; a refresh
without deletions is still version 1, and an older reader refuses version 2 rather than ignoring it). A reader checks the names (library only) before anything is written, and after its own library step deletes each file only
when its sha256 is the one the keeper deleted; a file that differs is kept and listed (`library_delete_kept`); `data\state\logs\refresh-deleted-<stamp>.json` records it.

## Changes to other pieces, all made outside them (wrapper, copy or patch at assembly)

1. `saver_steps.py` copy gets winpack patch 03; `release_rule.py` and `img_embed.py` copies get patches 01 and 02; `pdftext_pypdf.py` added; `PIPELINE.sha256` regenerated (assemble_app.py has its own small unified-diff applier and refuses a patch that does not match exactly once). PHOTOLINK-v1 adds app patches 04 (`img_embed.py`), 05 (`sheet_task.py`) and 06 (`tracker.js`, and the same text applied to `data\site\index.html`) and the new module `photolink.py`, all from `app/patches/` (item 6).
2. `take_update.py` and `make_for_update.py` start children with `python -I` only. `station_cli.py` swaps their `subprocess` for a shim that adds `-B -X utf8` and `AJG_NO_NETWORK=1`; it also points temp files at `data\tmp`. They are also told `--legacy app\pipeline\legacy_index.html` (make_for_update's CLI does not look for it by itself, so the "for Update" file would lack the fields only the old page carries).
3. `server.py`: not edited. `station_server.py` subclasses its handler, adds the script/style to the served page (monkey-patching `inject_shim`), the `/articles/` route, the `/_local/station/*` endpoints and a streaming upload (the base server holds bodies in memory, capped at 64 MB).
4. `take_update.save` is called with `rebuild=True` (the saver's rebuild into its working folder). The saver "never writes" the page, the shards or the pipeline folder, so `post_save.py` copies them in afterwards (page, changed shards into `data\copies\articles`, and `lookup_cache.json`, `outlets.json`, bills, release texts and release related into `app\pipeline`, then writes PIPELINE.sha256 again; old versions are kept aside). This is the "adapter" job of SAVER_SPEC section 8 and fixes the nested-shard bug of the manual 2026-10-30 save. If the saver's rebuild fails, the page is rebuilt the plain way.
5. (Lesson of the old workspace, 2026-11-03: build copies against the current published shards, never a cached set.) The save is given `data\copies` itself (`take_update --copies`), so it merges new entries into the folder's own current shards, and `post_save` writes back only the shards it changed; `tests/test_libfiles.py` checks that no existing entry is lost or altered except those of stories the update touched. The article shards live once, in `data\copies\articles`; the server serves `/articles/<file>.json` from there instead of keeping a second copy in `data\site`.
6. **Photos kept as links (PHOTOLINK-v1, 2026-11-02; replaces the offline photo step, HANDOFF_PC_APP point 6).** New saved copies keep their photos as remote `<img>` links to the news site's own image addresses; Edge loads them when a copy is opened. Copies already in the library keep the photos embedded in them; nothing is changed there. See "Photos" below.
7. B10 (same handoff, point 8): `station_cli` refuses a second take-in of a run id that the saver's ledger, the local db (`sheet.written`) or a finished update already holds (`ALREADY_SAVED`), at inspect and again at save.
8. **Local fonts (LOCALFONTS-v1, 2026-11-02; SAMELOOK-v2 the same day).** The page head and the saved-copy viewer no longer ask Google Fonts. `fonts/fetch_google_fonts.py` fetches, once, the very files Google serves for the old tracker's two requests (variable woff2, one file per script subset, sha256 pinned in `fonts/google/FONTS_GOOGLE.json`; a first version used the static fontsource files, which measured 0.02 px differently and anti-aliased differently on every page). `fonts/google/page.css` is Google's answer for the page (Roboto Slab 500-800, Public Sans 400-700, normal style only: the page never asked for italic, so a browser draws its own slanted italic, as in the old tracker) and `viewer.css` Google's answer for the saved-copy frame (Roboto Slab 600 and 700, Public Sans 400 and 600, Public Sans 400 italic; a bold word in a saved copy uses the 600 face, as before). Assembly copies them to `data\site\fonts\` (served at `/fonts/`), applies patch 08 (`shell.html` and the built `index.html`: the three Google links become `<link rel="stylesheet" href="/fonts/page.css">`) and patch 07 (`tracker.js` and `index.html`: the viewer's `@import` points at `/fonts/viewer.css`, and the frame's policy becomes `style-src 'unsafe-inline' 'self'; font-src 'self'`). Tests: `tests/test_localfonts.py`. The look check (`work/localapp/lookcheck/`) proves the result against the live tracker's own files.
9. **Library files (LIBFILES-v1, 2026-11-03).** The NewsBank and ProQuest save patches and the date-source rules are wired into the pipeline copy at assembly, each by the same exactly-once rule, in this order after the PHOTOLINK ones: 09 `sheet_task.py` (NewsBank story PDFs: `<year>/nb<Article ID><o|r>-<Story ID>.pdf`), 10 `date_rules.py` (Date source "NewsBank"), 11 `pdftext_pypdf.py` (a story cut from a shared page is read inside its band only), 12 `sheet_task.py` (ProQuest: text copy `<year>/pq....html` and the original PDF in `_original_pdf/<year>/`), 13 `date_rules.py` (Date source "ProQuest"), 14 `sheet_task.py` (ProQuest outlet names as aliases; data file `station/data/proquest_outlets.json` copied beside `sheet_task.py`). The sources are in `newsbank_pc/patches/`; the copies here carry the assembler's numbers. `PIPELINE.sha256` is generated after all of them. The panel result lists what the save checked about the station's file names (`plain.names_lines`: renamed files with the reason, files not saved). When the save gave a file another name than the station did and the station's old name is still held by a story the save did not write, that unsaved file is set aside in the kept update folder under `not_saved\` (never a made-up `-2` name). Test: `tests/test_libfiles.py` (one update with a web find and raw page, a NewsBank story PDF, a ProQuest story with its original PDF, a press release, a reprint, an undated story and a YouTube attach; every library file at its NAMING-v2 name and year folder, the workbook's File name / File name 2 / Saved Copy? / File type cells match, nothing existing touched or overwritten, renames listed in the panel result, the article shards kept as they were and only added to, a second update whose numbers were taken, and a keeper to reader refresh that delivers the same files to the same paths; about 12 minutes; needs a test build from the v64 workbook copy and skips on any other).
10. **No review queue (NOQUEUE-v1, 2026-11-03).** `take_update` never gives the saver `--queue`; the layout has no `queue/` folder; the panel does not list the saver's `origin_wanted` (stories where the first publisher should be found) or `queue_conflicts` as things for a person to do (`plain.NOQUEUE_KEYS`). The saver still computes them; they are simply not shown or acted on.
10b. **Reserved ids (DROPUNVERIFIED-v1).** Patches 19 (`sheet_task.py`) and 20 (`build_data.py`), applied after patch 14 / in the same exactly-once way; see "Switch-over day".
11. **Layout fixes and wording (TIDY-v1, 2026-11-03; approved exceptions to SAMELOOK-v2).** Four patches, applied like 06 to 08: to the pipeline copies (`tracker.js`, `tabs/reporters.js`, `tabs/outlets.js`, so every page rebuild has them) and, with the same exactly-once rule, to a page already built. `15_tracker_js_tidy_css.patch` adds one style block (`#tidy-css`, selectors all start with `:root` so they beat the page's own rules however late those were added): the navy table header meets the card border (a 1 px navy extension behind each header cell, `overflow:clip` with `overflow-clip-margin:1px` on `.card>.tablewrap`; rounded at rest, square while pinned), a list tab never grows wider than the window (Outlets drops Publisher, Originals and Top reporters below 1300 px, and Reprints and Last story below 860 px; Reporters drops Last story below 1000 px), headings line up with their tables, Back and Forward as tall as the other masthead buttons, text 1 px lower in tab buttons, Filters, the per-page select and badges, Home tile labels in one row, and Manage's "Find & refresh" tab hidden. `16_tabs_reporters_tidy.patch` and `17_tabs_outlets_tidy.patch` make the Top issues cells a list of non-breaking items (no commas, the count on the issue's line). `18_wording_tidy.subs.json` is a list of exact text swaps (each old text must occur exactly `count` times in the pipeline's page files and in the built page, or assembly stops): Manage opens on the Update log, and the Update-era sentences (Update database, Refresh from files, ask Claude in chat, Rated by Claude, Mac paths, notes "shared with everyone") say what is true on the PC. Tests: `tests/test_tidy.py`. Not changed: `code/` and `build/` (the Update station reuses them byte for byte).
8b. The pipeline folder is therefore written by the tracker after a save (the keeper copy only). FORMAT.md said "never written".

## Photos (PHOTOLINK-v1)

**What the save does.** `station_cli` no longer gives the saver an `--img-cache`; it sets `AJG_LINK_PHOTOS=1` for every child process (and `AJG_NO_NETWORK=1` stays). Patch 05 makes `sheet_task` run its photo step on each new page and release copy when that switch is on; patch 04 hands the page to `photolink.link_page` instead of fetching and caching. For each `<img>` it:
- keeps one absolute `https` address (the largest `srcset` entry up to 1,000 px wide, as PHOTOS-v2; lazy-load attributes and `<picture>` sources are used only to find that address and are then removed). An `http` address is kept only when the image has no `https` one, and is listed in the save log (`photos.http_only`);
- sets `referrerpolicy="no-referrer"` and `loading="lazy"`, and removes event handlers;
- drops what `img_embed` already classifies as ads, tracking pixels, logos and avatars, 1-pixel images and images declared smaller than 60 x 40 px; the wrapper they leave empty goes with them, a caption stays;
- leaves embedded photos (`data:`, `jgimg:`) and published local paths (`pdf/...`) alone.

It also removes every `<script>`, and `media_gate.clean_html` still removes `<svg>`, `<video>`, `<audio>`, `<iframe>`, `<object>`, `<embed>`, `<canvas>`, `<picture>`, `<track>` and any `<img>` whose address is svg, avif, bmp and the like. Nothing is fetched, cached or looked up: the step imports no network code.

**What the page does.** Patch 06 changes the viewer (`safeImgs`): an `<img>` with an absolute `http(s)` address now stays (before, every remote image was removed); it gets no `srcset`, `no-referrer` and lazy loading. A photo that fails to load is removed after the error, caption kept (the existing `hideBroken`). The saved copy's frame is still sandboxed without scripts, and now carries its own Content-Security-Policy: images (`https:`, `http:`, `data:`, `blob:`, local) and the fonts the tracker already asks for, nothing else (no script, stylesheet, connection, media, frame or form). The server sends `Referrer-Policy: no-referrer` on every response and no policy of its own; the page as a whole is not opened to anything new.

**Make copies.** The PC never runs `make_copies.py`. Run without `--img-cache` it keeps linked photos and exits 0; run with `--img-cache` it would drop remote photos as it always did.

**Where this differs from the old tracker.** This is the one place where the PC's browser (not the program) goes to news sites: when a copy is opened. Photos vanish when a site removes them, and a CSS `background-image` in a saved page loads like any image. The old tracker (claude.ai) embeds photos and never shows a remote one.

## Look and function check (SAMELOOK-v2)

`python3 -I work/localapp/lookcheck/run_lookcheck.py` serves the live tracker's own published files next to this page and compares screenshots, computed styles, font files and behaviour. See `work/localapp/lookcheck/README.md`.

## Tests

    python3 -I -m unittest discover -s work/localapp/app/tests -p test_station.py -v       (about 15 minutes: real previews and saves on the real workbook; 13 tests)
    python3 -I -m unittest discover -s work/localapp/app/tests -p test_photolink.py -v     (PHOTOLINK-v1: LinkPage and Viewer in seconds, Save a few minutes)
    python3 -I -m unittest discover -s work/localapp/app/tests -p test_localfonts.py -v    (LOCALFONTS-v1: zero outside requests from the page and the viewer frame; both fonts load; 15 seconds)
    cd work/localapp/app && python3 -I -m unittest discover -s tests -t tests              (the whole suite)
    AJG_TEST_BUILD_EMPTY=<empty build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_switchover.py -v   (SWITCHOVER-v1, DROPUNVERIFIED-v1: needs a build made with --data-mode empty and $SCRATCH/wb_0bccc1fc.xlsx; about 17 minutes)

Every host in test_photolink.py is on the reserved `.test` domain, Playwright answers the requests itself, and every python process of the app runs under a net guard (a `.pth` in the work copy's site-packages) that logs and refuses any non-loopback connection or name lookup.

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

**Everyone.** Your notes and saved views stay in your own copy; nobody else sees them, and a refresh never touches them. The **Tracker files** button (top right, next to Manage) shows an amber dot when Excel has the workbook open and whether a save is running.

**Keeper (Sammy).** Each time you want new stories:
1. Tracker files, **Make "for Update" file**. It downloads a file; keep it.
2. In the Update station, load that file and press Update, then download the update zip.
3. Tracker files, **Bring in update**: drop the zip in. Read what it says it will change and the list of items that need a person. If it warns that the update was made from an older workbook, the clean fix is to start again at step 1; "Use it anyway" is there if you know what you are doing. Press **Save**. The tracker backs up the workbook first, saves, rebuilds the page and reloads it.
4. Tracker files, **Make refresh file**. Pass the file it downloaded to the others (shared drive, email or Teams). The first one it makes is a full one (bigger: it carries the whole library); for a person who joins later, open **Repairs** and use **Make a FULL refresh file**.
If you edit the workbook in Excel yourself: close Excel, open **Repairs** in Tracker files and press **Accept the workbook as it is now** once.

**Readers.** When the keeper sends a refresh file, open the tracker, press Tracker files, and drop the zip into **Bring in refresh file**. Your workbook, article pages and page data are brought up to date, your old workbook is backed up first, and the page reloads. If it says the refresh is older than what you have, you already have it. If it says it skips a refresh you never got, ask the keeper for a FULL refresh. Readers cannot save updates; that is by design.

**Setting up a keeper copy (once).** Put `{"role": "keeper"}` in `data\role.json` (a copy without that file is a reader). Put the current workbook and library in `data\`, open **Repairs** in Tracker files, press **Accept the workbook as it is now**, then **Rebuild the page**.

## Version 2 additions (2026-11-04)
- **Article data from the library (ARTICLEDATA-v1).** `station/article_copies.py` adds the copy of every story that has a saved copy in the keeper's library but no entry in `data\copies\articles` (setup, after every save, and Repairs "Rebuild saved copies"). Existing entries are never changed.
- **Windows file locks (WINLOCK-v1).** `fs_retry.py` (copies in `app\saver`, `app\updatefolder`; `common.retry_busy` in the station code) waits about 10 s on PermissionError for every replace, rename and move. App code ships without .pyc.
- **Install a new version (PROGRAMUPDATE-v1).** `Install update.cmd` / `.command` and `station/install_update.py`; see READ ME FIRST.
