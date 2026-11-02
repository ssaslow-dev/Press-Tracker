# Update station (LOCALAPP step 7)

A new, private claude.ai artifact, **AJG Update Station**, that holds only today's Update button. Decisions: UPDATESTATION-v1 (all follow-ups, 5 and 6), NEWPROJECT-v1, GOVIT-v1.

- **Artifact URL:** https://claude.ai/artifact/5uGsM8yQMphjAQbKhvc5SL (private, titled "AJG Update Station", icon search; capabilities db, downloads, sample, mcp TinyFish search + fetch_content). Republish to the same URL for later changes: `Artifact` with `file_path` = `dist/index.html` and the same capabilities.
- It does not touch the old tracker, its artifacts or its databases. Nothing was published except this one page.

## What it does (three steps on one page)

1. **Load the "for Update" file.** Picker or drag and drop. The file is read in the browser (`FileReader` + `JSON.parse`); it is never uploaded or stored. The page shows its date, the workbook fingerprint (first 8 characters) and the story count, refuses anything that is not a version-1 `ajg-for-update` file with a fingerprint, and keeps the Update button off until a file is in.
2. **Update.** The tracker's own Update code runs, unmodified, on the file's data: the same plan (about 700 TinyFish searches), dedupe against the file's stories and spreadsheet rows, reprint candidates, Claude screening, tone, author and translation for each new find, the Since control, the run steps and the run log. Only the masthead, the Update panel and the run log are shown; the other tabs, Refresh from files, Spreadsheet download and the Manage extras are hidden.
3. **Download the update folder.** One zip, written in the page (small store-only zip writer, sha256 per file with `crypto.subtle`), exactly per `work/localapp/updatefolder/FORMAT.md`: `manifest.json` (source fingerprint = the loaded file's workbook sha) and `db/<collection>/<id>.json` for the runs made since the file was loaded plus their pages, reprints, authors, translations, tones and edits. Saved through the artifact `downloads` capability (a normal download if that is absent). The packed runs are recorded in the station db (`packed/<run id>`); nothing is deleted.

## Layout

| File | What |
|---|---|
| `build_station.py` | one-command build: `python3 -I work/localapp/station/build_station.py` writes `dist/index.html` (about 0.84 MB) and `dist/build_info.json` |
| `src/station.html`, `src/station.css`, `src/station.js` | the station-only layer (the only new code) |
| `tests/station_test.js` | Playwright test (below); `tests/verify_zip.py` checks a zip with the PC side's own code |
| `dist/` | build output (git-ignored) |

## Build inputs

- `code/tracker/NN_*.js`, concatenated by `code/apply_all_patches.py --tracker-js` (the same bytes as the tracker build; sha256 `92e2b785...` equals the live tracker's `pipeline/tracker.js`).
- `work/localapp/vendor/live_*/pipeline/shell.html`: the live page's HTML and CSS (SAMELOOK-v1). Its Google Fonts links are removed at build time (see "Moving to another account").
- `src/station.*`.

Needs only Python 3.11+. No pandas, no network, no node.

## What is reused unmodified

`code/tracker/00_head.js` ... `99_boot.js`, all 34 parts, byte for byte, including 40 to 43 (the Update code) and every helper they need (SURVEY 7a). The tracker starts only after the file is loaded.

The station layer adapts around it, without editing it:

- **Data blocks.** The file's `stories` go into `<script id="data">`; `rows`, `idmap`, `covcols`, `billsinfo`, `fetchrules` and `ins-release_pickup` become the `<script type="application/json">` blocks the code reads. `release_texts` is served to the code's `fetch('data/release_texts.json')` by a wrapper around `window.fetch`; the other relative fetches the tracker makes at start (`articles/manifest.json`) get a 404 (the station holds no saved copies).
- **The button's memory.** `window.claude.use('db')` as the tracker code sees it is an in-memory db seeded from the file's `memory` (`runs`, `clips`, `reprints`, `edits_removed` as `edits/<id> {removed:true}`). The code gets this by running inside a function whose `window` parameter is a Proxy of the real window with `claude` replaced, so nothing depends on `window.claude` being writable. `mcp`, `sample` and `downloads` pass through to the real runtime.
- **Opening the Update panel.** The tracker draws it only when Manage is opened, so the station clicks the (hidden) Manage button once the run history has arrived and shows the panel in the page flow with CSS.
- **Text.** Three sentences that send the user to a chat to "save the last run to the sheet" are rewritten to point at step 3.

### Where unmodified reuse is not possible or not complete

- **Refresh from files** (tone, author, translation of older saved pages) is hidden: it works on saved page text, which the station does not have (the for-Update file carries no article text). Tone, authors and translation for **new finds** are done inside the Update run (classify step and the translate step), as in the tracker. Re-rating older stories (follow-up 5) therefore cannot happen in the station as the file is defined; say if it should.
- **Fonts.** The shell's Google Fonts links are dropped, so headings use the shell's own fallbacks (Rockwell, Georgia) and body text system-ui. The look differs slightly from the live tracker.
- **Pieces of the tracker code never reached here:** a PDF.js `cdnjs` URL (loads only when a PDF is dropped on the tracker's Manage panel) and a Google Fonts `@import` inside the saved-copy viewer's CSS. The station offers neither a drop zone nor a story sheet. `build_station.py` asserts that the shell and the station layer hold no outside reference.
- Edits made in the Log pane (Edit/Remove) are packed as `db/edits` docs if made after loading. Hide them if that is not wanted.


## Persistence, recovery and "packed" (HANDOFF_PC_APP sections 6, 7, 10)

- **Heartbeat (REQ-2).** The tracker code writes its progress run doc at the start and every 25 searches, unmodified. Here those writes go to the in-memory db, and each one is also copied (best effort, one write at a time) to the artifact db, collection `recover`, one document per tracker document, keyed to the loaded file (workbook sha + file date). The documents hold the JSON as a string.
- **Closed tab.** Load the same file again: the page finds the unfinished session in `recover` and offers **Recover**. Recover puts the documents back through the same in-memory db (so the tracker code sees the run, the finds and the reprints again and does not propose them twice) and they can be packed like any run. A session that was already downloaded is not offered again (`recoverstate/<key>` holds the packed point). Tested: reload, load, Recover, pack; the recovered documents equal the originals. Without a db capability there is nothing to recover from (the old localStorage fallback `jg-runs-pending` only triggers when the tracker's store write fails, which the in-memory store never does).
- **Packed runs.** The zip carries each run doc as the tracker wrote it, without `ids` or `sheet.written`, because the PC's save sets those (the saver's write-back). The station does not need them: nothing is reused between uses (the next file brings the memory), and inside one use the packed point (`S.lastPacked`) stops a run being packed twice. A packed but never saved run is re-found by the next Update, which is intended (FORMAT.md, "Fingerprint").
- **`_text`** (up to 6,000 characters per proposed row) stays in the run doc in the zip. **`searched_to`** advances only when at most 2% of the calls failed: that rule is the tracker's own code (`runAll`), unchanged.
- **Without `sample`** (not offered or not allowed) a red note appears above the Update panel; the tracker's own message ("Claude couldn't review these ...") follows a run.
- **Hidden:** Refresh from files (header and panel), Save to sheet, Spreadsheet download, Manage. Only Update (confirm dialog with the Since field), the run log, and the new Download step remain.
- **Connector name.** The mcp capability declares the server as exactly `TinyFish`, the value of `TF` in `41_update_search.js`. A page that declares mcp cannot be shared "anyone with the link"; it stays private.

## Photos (UPDATESTATION-v1 follow-up 7A): feasibility

See the report in the build hand-back; summary here. TinyFish `fetch_content` cannot supply image bytes: on a direct image URL it returned only metadata (title with the pixel size, `text: null`, `image_links` listing the same URL), the tool has no bytes or base64 option, and a Wikimedia thumbnail gave `target_http_error 400`. The artifact sandbox blocks other hosts for fetch/XHR and images (artifact contract text), so the page cannot fetch them itself either. A test page ("AJG photo test", `photo_test/photo_test.html`) records what an open page really gets; its result is in db collection `photo_test`, document `latest`, once someone opens it.

## Wanted originals (follow-up 7B)

`origin_wanted` comes from `sheet_task.py` (`central_wanted`, aggregator finds) and is worked by Claude in chat today (`code/sheet_task_prompt.md` line 16). The Update JS has no pass for it. Proposal in the build hand-back; not built because the for-Update `origin_wanted` entries and the update-folder return shape are not defined in FORMAT.md yet.

## Moving to another account

The station depends on nothing but its own files, the for-Update file, Claude and the TinyFish connector.

1. Check out the repository and run `python3 -I work/localapp/station/build_station.py` (one command; no network).
2. On the new account, connect **TinyFish** in claude.ai Settings, Connectors. It is the only outside dependency besides Claude itself.
3. Publish `dist/index.html` as a new private artifact titled **AJG Update Station** (icon `search`), declaring these capabilities (nothing else):
   ```
   db: {}
   downloads: true
   sample: {}
   mcp: {servers: [{server: "TinyFish", tools: ["search", "fetch_content"]}]}
   ```
   No `{artifact, path}` copies and no links to other artifacts are used or needed.
4. Open it, load a for-Update file, press Update (Claude and TinyFish each ask for consent on first use).

Account-neutrality checks:

- The page reads nothing that differs per account or per artifact: no artifact id, no user id (the tracker code uses `window.claude.use` for `db`, `sample`, `mcp`, `downloads` only; the only URL state it reads is `location.hash`, `#about`, which the station never sets).
- The artifact db is scratch. The station never reads it: the run history, waiting finds and removals come from the for-Update file every time. The only write is the `packed/<run id>` note. A fresh, empty db, a db full of leftovers and no db at all give the same result (tests below).
- No CDN script, no JSZip, no web font. The zip writer is in `src/station.js`.

## Tests (Playwright, chromium, local 127.0.0.1 server)

`node tests/station_test.js --page dist/index.html --file FOR_UPDATE.json --out OUTDIR [--db-mode empty|stale|none]`. The page is served inside the skeleton the Artifact tool adds; `window.claude` is a stub: db in memory, TinyFish `search` and `fetch_content` answered from three fake articles (one English, one Spanish with no byline, one reprint of a story in the file) plus a search hit whose link is a story already in the file, `sample` answering the screen and classify prompts. The 2.1 s TinyFish throttle is compressed 100 times. The for-Update file is real: `make_for_update.py` on a copy of the snapshot workbook (3,681 stories, workbook sha `bc21c9fb`).

Results on 2026-11-02 (50 checks in empty and stale db modes, 44 in none, all passed):

- before a file: drop zone and picker present; Update button disabled; clicking it does nothing (tracker code not started, no confirm dialog); step 3 disabled; other tabs hidden; wrong files refused (not a for-Update file, broken JSON, no fingerprint);
- loading (picker, and drag and drop in a fresh page): workbook short form `bc21c9fb`, 3,681 stories shown; Update enabled; Update panel with the Since control; Refresh, Spreadsheet and Manage hidden;
- seeding: a file with an earlier run, a waiting find and a removed story gives Since = searched_to minus 7 days, the "last full update searched up to" line, the run in the log, and nothing from it in the next zip;
- a run (708 searches, 9 page fetches): 2 new stories (English; Spanish with no byline), the hit whose link is already a story in the file is not added, the same-headline hit becomes a reprint candidate on s04931 with `added` = today, 3 pages docs (2 stories, 1 reprint candidate), a translation doc, an authors doc (Claude split "A; B"), tone in the proposed rows, `searched_to` = today;
- recovery: reload, same file, Recover, recovered docs equal the originals, then pack;
- step 3: the zip downloads with the right name; the run is recorded in `packed`; nothing left to pack afterwards; the same file offers no recovery;
- db modes: empty db, a db holding stale leftovers (a future `searched_to`, a waiting find, a removal, an old pack note) and no db capability give the same run, the same zip contents and no stale item anywhere;
- no page errors.

PC-side checks of the zip (`tests/verify_zip.py`): `formats.scan_zip` and `check_manifest` pass (7 files: manifest, 1 run, 3 pages, 1 reprint, 1 author, 1 translation), and `take_update.py inspect` on a copy of the snapshot workbook: `proceed: true`, fingerprint `match`. `tests/preview_zip.py` then runs the saver preview on a copy: the saver's first pass accepts the update: it assigns Article and Story IDs (10666 to 10668, s04938, s04939), applies the pages docs (saved copy, word count, mention depth, quoted) and adds the Originals and the Reprint of s04931. Its second pass (`after_relmatch`) did not finish in my scratch folder: with build_data stubbed it failed in `reltab`, and with the real `build_data` and `relmatch` it stopped on a missing `pipeline/release_related.json`, a gap in the scratch pipeline folder (the PC app builder's step 5 and 6 own that layout), not a fault in the zip. So "preview against a copy" is only half proven; rerun `PIPE_REAL=<folder> python3 -I tests/preview_zip.py ZIP WORKBOOK SCRATCH TODAY` once the PC pipeline folder exists.

## Still needs a real run

A live TinyFish search can only be judged when Sammy presses Update in the published page. Also unproven here: the real artifact runtime's consent prompts for TinyFish, Claude and the download; that the real `downloads` capability accepts the zip (allow-listed extension `zip`); how long 700 live searches take (about 25 minutes at the code's own throttle); and that Edge shows the page the same way as chromium.
