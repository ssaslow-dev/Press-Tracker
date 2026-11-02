# The two travelling files (LOCALAPP step 6)

Decisions behind this: UPDATEFOLDER-v1, UPDATESTATION-v1 (follow-ups 3, 4, 5), SWITCHOVER-v1, GOVIT-v1. Facts: `work/localapp/SURVEY.md` section 7. Code: `formats.py` (shared rules), `layout.py`, `make_for_update.py`, `take_update.py`; tests in `tests/`.

Both files are **data only**. No scripts, no programs, no network. Saved article HTML that travels inside the update is untrusted data: the PC never opens or runs it here, and the PC tracker page must show it only the way it shows saved copies today (in the sandboxed viewer, never as part of the page).

## 1. The "for Update" file (PC tracker -> Update station)

**One plain `.json` file**, not a zip. Why: the Update station reads it in the browser with a file picker and `JSON.parse`, with no unzip code to ship or trust; it is about 7.4 MB on the snapshot (1.5 MB gzipped), which a browser reads in well under a second; and it is not an upload to anywhere (UPDATESTATION-v1: read in the browser from disk, never stored online). Name: `for_update_<YYYYMMDDhhmm>_<sha8>.json`; an existing file is never overwritten (`name (2).json`).

**No article text.** Not `text_en` (translated story), not tone notes (`twhy`), no saved HTML, no OCR, no `av` details. Press-release text (`release_texts`) is the one block of sentences; it is official release text, not coverage, and can be left out with `--no-release-texts` (the release-pickup search then has no sentences).

Top level (all keys always present unless noted):

| Key | Contents | Source | Read by (SURVEY) |
|---|---|---|---|
| `format` | `"ajg-for-update"` | | |
| `format_version` | `1` (integer; a reader refuses a higher one) | | |
| `created_at` | UTC `YYYY-MM-DDThh:mm:ssZ` | | |
| `fingerprint` | `{workbook_sha256, workbook_name, workbook_bytes}`. `workbook_sha256` is the sha256 of the workbook file the file was built from | `sha256` of the workbook, taken from the same copy that was read | the update folder copies it into its manifest (section 2) |
| `notes` | list of plain sentences about anything missing (no legacy page, no sid_map ...) | | station may show them |
| `stories` | one object per tracker story (the page's `D`, 3,681 on the snapshot), fields below | `build_data.py` `data.json`, projected | 7b `D`, 7e |
| `rows` | `{cols:["aid","sid","kind","outlet","date","hl","links"], rows:[[...]], next:{aid,s,pr}}`: **every** Coverage row including Reprints, "Reprint (unverified)" (kind `""`), Removed-tab rows (kind `X`) and the Unlinked-print-pages rows. `hl` is normalized, `links` are normalized URLs. 9,964 rows on the snapshot | `build_data.py` `rows.json`, as is | `covLoad`, `covHit`, `covLink`, `covRepKnown`, `COV.next` |
| `idmap` | `{old code: Story ID}` | `idmap.json` | `00_head.js:7`, `40:256` |
| `covcols` | Coverage column names in sheet order | `covcols.json` | `40:107` (order of proposed rows) |
| `billsinfo` | `{rows:[{bill,session,title,role,status,introduced,titles,program,budget_act,topic}], programs}` | `billsinfo.json` | `00_head.js:56`, `41:406-420` |
| `fetchrules` | `{skip_urls, print_page_urls, never_coverage, never_keep, never_keep_outlets, blocked_hosts, lookups, lookup_hosts, lookup_archive}`. This is also the **lookup cache** in the form the page reads (verdicts `dead`/`not_found`/`blocked`, blocked hosts, archive links) | `fetchrules.json` (made from `clean_rules.json`, `outlet_rules.json`, `outlets.json`, `lookup_cache.json`) | `41:53-65,598-603` |
| `ins_release_pickup` | the `ins-release_pickup` block (v2: `rel`, `known`, `also`, ...) | `release_pickup_data.py` through `build_data.py` | `relKnown` `41:468-475` |
| `release_texts` | `{v, rel:{url:{date,title,dek,body,src,prid}}}` (optional) | `pipeline/release_texts.json` | `relTexts` `41:555` |
| `memory` | the button's memory, below | the tracker's own db folder | 7b `runs`, `edits`, `clips`, `reprints` |

### `stories[]` fields

Kept (SURVEY 7e): `id, code, aid, date, prec, year, outlet, pub, hl, hl_en, link, plink, lstat, pq, also, rep, media, county, reach, lang, fmt, topic, issue, bills, author, authors, atitle, role, tone, tauto, src, added`, and `reps` (list of `{aid, outlet, date, county, state, link, hl, src}`; `state` lives only here). Left out: `text_en`, `twhy`, `lk`, `akinds`, `rc`, `av`, `depth`, `quoted`, and the per-reprint `lk/depth/quoted/fmt/av`. (Page logic reads none of them; `text_en` is only diffed before/after, and an absent value counts as `''` on both sides.)

### `memory`

```
searched_to   "YYYY-MM-DD" or ""   newest find-run's searched_to (the page's lastSearched()); the Update's default start is this minus 7 days
searched_run  run id it came from
runs          {run id: {at, mode, newsbank, searched_to, since, since_manual, status, failed, stories, reprints, sheet:{at,written,line,stories,bills,newbills}, unsaved_rows?}}
              rows, pages, tones, lookups and the rest of a run doc are not carried. unsaved_rows = number of proposed rows of a run that the
              workbook does not have yet (sheet.written is not true)
clips         {Story ID: {date,outlet,pub,hl,link,plink,also,rep,added}}      finds from earlier runs not yet in the workbook
reprints      {rp-id: {story,outlet,link,date,added}}                         same, for reprints
edits_removed [Story ID, ...]                                                  stories the team removed and the sheet has not yet applied (do not count as known)
```
Team notes, saved views and other edits stay on the PC (not in the file). On the PC the run docs get there by `take_update.py` after a save (section 3), so `searched_to` advances only for updates that were really saved.

### Size on the snapshot (`data/AJG Coverage - NewsBank.xlsx`, sha256 `bc21c9fb...`)

7,379,156 bytes (7.0 MB); 1,473,056 bytes gzipped. By block: stories 4.29 MB, rows 2.11 MB, release_texts 1.01 MB, billsinfo 0.11 MB, idmap 0.09 MB, release pickup 0.09 MB, fetchrules 0.03 MB. Built in about 12 s. Grows roughly with the number of stories; the update zip is separate and small.

### How it is made

`make_for_update.py --app-root APP` (or `--workbook --db --pipeline --out`). It copies the workbook (checksum compared after the copy), copies the pipeline's top-level `.py/.json/.csv` files into a temp folder and runs `build_data.py` there as a subprocess (the original is never edited), with only the `release_pickup` insight view enabled. Without `legacy_index.html` it uses an empty stand-in, so fields that only the old page carried come from the workbook alone (`--legacy FILE` supplies it). Needs `pandas` and `openpyxl`, as the pipeline does.

## 2. The update folder (Update station -> PC tracker)

**One `.zip`**, deflate or store, containing only:

```
manifest.json
db/runs/<run id>.json            the final run doc: rows, lookups, bills_new, releases_new, print_pages, searched_to ... (CONTRACT "Proposed rows")
db/pages/<id>.json               {url,title,clean|scoped,...}: saved HTML of each find, reprint candidate (rp-<hash>) and originator copy (og-<hash>)
db/reprints/<rp-id>.json
db/authors/<id>.json             {author, found, by}
db/translations/<id>.json        {hl, text, lang, at, by}
db/tones/<Story ID or placeholder>.json   {tone, why, rated, by, topic?, bills?}
db/edits/<id>.json               only if the station carries any (it normally does not)
files/<id>.pdf                   NEWSBANKPDF-v1: one NewsBank story's own PDF (binary), only when a pages doc names it (below)
```
`db/` is exactly the layout `saver.py --db` reads (a folder per collection, one `<doc id>.json` per document; `sheet_task.load_db` reads `runs, edits, tones, authors, translations, pages, reprints`). The PC unpacks it to a staging folder and passes `staging/<id>/db` as `--db` unchanged. Collections the save does not read (`clips`, `notes`, `views`) are not allowed in the zip.

`manifest.json`:

```json
{"format": "ajg-update-folder", "format_version": 1, "created_at": "2026-11-02T18:00:00Z",
 "source": {"workbook_sha256": "<the for-Update file's fingerprint.workbook_sha256>"},
 "runs": ["run-abc123"],
 "files": {"db/runs/run-abc123.json": {"sha256": "<hex>", "bytes": 12345}, "db/pages/NEW-run-abc123-1.json": {"sha256": "...", "bytes": 678}}}
```
Extra keys (for example `station_version`, `for_update_created_at`) are allowed and ignored. `files` lists every file except `manifest.json`, with sha256 and byte count. Reference writer: `formats.pack_update_zip`.

### Allow-list and limits (GOVIT-v1) checked by `take_update.py` before anything is written

- Entry names: exactly `manifest.json`, `db/<collection>/<id>.json` with `<collection>` one of the seven above, or `files/<id>.pdf` (NEWSBANKPDF-v1), `<id>` matching `[A-Za-z0-9][A-Za-z0-9._-]{0,119}`. So no `.py .js .html .exe .cmd` and no other extension; no absolute path, drive letter, `..`, backslash, control character or Windows-reserved name; no duplicate names (case-insensitive); no encrypted, link or non-file entry; folder entries are ignored.
- Caps: 20,000 entries; 512 MB all entries together uncompressed; 64 MB per entry (8 MB for the manifest, 32 MB for a story PDF); 256 MB for the zip file; no entry over 256 KB may expand more than 200x; the bytes actually read must equal the size in the zip header.
- Every file must be valid UTF-8 JSON holding an object; the manifest must list exactly the files present and every sha256 and size must match; `format` must be `ajg-update-folder`; `format_version` above 1 is refused with a clear message; there must be at least one run doc; a source fingerprint is required.
- Story PDFs (`files/<id>.pdf`, section 2b): every one must be named by a pages doc, match the sha256 that doc gives and the manifest, start with `%PDF-`, and hold no JavaScript, launch or open action, embedded file, form code, rich media or encryption (checked two ways: the file's own text with `#xx` names un-escaped and its object streams decoded, and, when pypdf is present, every object of the file).
- Any failure refuses the whole zip (`UpdateRefused`, codes `BAD_ZIP BAD_MANIFEST BAD_ENTRY BAD_JSON BAD_PDF HASH_MISMATCH UNLISTED_FILE MISSING_FILE TOO_BIG TOO_MANY_FILES ZIP_BOMB NEWER_FORMAT`), leaves nothing in staging, and the CLI exits 7.
- The station (browser) should write the zip with the same names and put the sha256 of each file in the manifest; the PC does not trust anything it has not checked.

### 2b. NewsBank story PDFs (NEWSBANKPDF-v1)

The Update station's "Add NewsBank PDFs" card splits NewsBank "Multiple Articles" batch PDFs into one PDF per story and puts each in the update folder as `files/nb-<16 hex>.pdf` (the hex is a hash of the story's NewsBank id, so the same story always gets the same name). Format version stays 1: an older PC refuses the zip at the first `files/` entry (`BAD_ENTRY`), which is the right outcome.

- **A run doc of its own**: `mode: "newsbank"`, `newsbank: <date>` (this also resets the Update panel's NewsBank reminder), `status: "done"`, `rows` (Coverage rows in `covcols` order with placeholders, see CONTRACT "Proposed rows" and below), `print_pages`, `left`, `searched_to: ""` (so the Update's search window never moves), `nb: {batches: [{name, sha256}], pdfs, links_found, links_searched}`.
- **Proposed rows** are the same shape as a web find's: `Data Source` `Newsbank` (the sheet's own spelling), `Date source` `NewsBank` (`print edition` when the record has a page), `NewsBank article link` = `https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=<docref>` (the form the sheet holds; the proxy host in a downloaded citation is normalized away), `Newsbank APA citation (article)`, `Section`, `Page`, `Word count` (NewsBank's), `Edition` (`Print` / `Web` / blank), `Headline`/`Date`/`Outlet`/`Author / byline` from NewsBank's header, `Publisher link` + `Link status` (`Publisher URL`; `Search link only` when the page was blocked) only when the publisher's own page was found, else both blank. `File name`, `File type` and `Saved Copy?` stay blank: the PC save names the PDF. An Original is found by its pages doc through `Tracker story code` (`jg-<6 hex>`); a reprint of a story already in the sheet carries `_page` = its pages doc `rp-<12 hex>` and a `reprints` doc (the string-of-text test is the PC's, never the station's).
- **The pages doc** of a story (`pages/<jg- or rp- id>.json`): `{url (the NewsBank link), title, clean (the story's text as HTML in the library's NewsBank-text form: <article class="jg-pdf-text">), scoped: "", at, nb}` with `nb` =
  `{docref, url, file: "files/nb-<hex>.pdf" ("" when the record is a citation page only: no saved copy, Sammy 2026-10-27), pdf_sha256, pdf_bytes, thin, batch: {name, sha256, index, pages: [first, last], shared_first, shared_last, bands: [{page, top, bottom}]}, header: {...}, citation, flags: [...], how}`.
  The PC save puts the PDF in the library as `<year>/nb<Article ID><o|r>-<Story ID>.pdf` (patches in `work/localapp/newsbank_pc/`).
- **Which pages a story's PDF holds.** Exact page ranges: from the page its header starts on to the page its citation ends on. The library's single-story NewsBank PDFs suggest NewsBank starts each story on a new page (of 300 sampled, 299 hold exactly one citation; the 6 measured all start at the same top margin and end mid-page), but no real batch PDF has been seen, so the station does not rely on it: when a story shares a page with its neighbour, the page is cropped to the story's band (`CropBox`), and the band is written into the PDF's info dictionary as `/AJGBands` (JSON `[{i, top, bottom}]`, `i` = page index inside the story PDF, PDF user-space y). A text reader on the PC keeps only text inside the band (`newsbank_pc/nb_band.py`), so a neighbour's text on a shared page never reaches the reprint test. The same numbers are in `nb.batch.bands`.
- **What the station does not put in a story PDF**: annotations (including the "OpenURL Link"), actions, page metadata, anything document-level. The PC checks again and refuses any file that has them.
- **Size**: one update holds at most about 180 MB of PDFs (the station stops adding before that; the PC's zip cap is 256 MB).

### Fingerprint

`source.workbook_sha256` is compared with the sha256 of the workbook now at `data/workbook/`. Different: `inspect` returns `proceed: false`, `fingerprint.status: "mismatch"` and a plain-language message the page can show; `preview` and `save` raise `FingerprintMismatch` (CLI exit 8) unless called with `accept_mismatch` / `--accept-mismatch`. Even when accepted, the saver's own check applies: its ledger must hold the workbook's checksum, otherwise it refuses `SHA_MISMATCH` (an edit made in Excel is first accepted with `take_update.py init`, SAVE_RULES answer 2). The message says the workbook changed since "for Update" was made and that the clean fix is to make a new "for Update" file and run the station again.

An update that is made but never taken in leaves `searched_to` where it was (nothing is merged before a successful save), so the next Update re-finds those stories; the save fills blanks only and the duplicate checks drop what the workbook already has.

## 3. The PC folder layout and the take-in flow

One app folder; the program reads and writes only inside it (the update zip the user picks is read where it is, and copied into `updates/done/`).

```
<app>/
  pipeline/            published pipeline files + PIPELINE.sha256 (+ insights/release_pickup_data.py, sid_map.json); never written
  saver/saver.py ...   the save program (work/saver/src); never written
  layout.json          optional overrides (relative paths; refused if they leave <app>)
  data/
    workbook/AJG Coverage - NewsBank.xlsx
    library/<year>/...  _original_html/  Press releases/     article library, add-only
    backups/            the saver's backups (newest 3 kept; older ones moved to _to_delete/)
    state/              ledger.jsonl, logs/, saver.lock
    copies/articles/    manifest.json + year shards (read by the save)
    db/<collection>/<id>.json   the tracker's own store: runs, edits, notes, views, ...
    queue/              review queue (items/ decisions/ applied/), optional
    for_update/         files made by make_for_update.py
    updates/staging/<id>/   unpacked update: manifest.json + db/ (+ zip_sha256.txt)
    updates/work/<id>/      saver outputs: preview-1/, save-1/ and their result json
    updates/done/<id>/      finished updates (staging moved here, nothing deleted)
    updates/rejected/<id>/  updates the user turned down
    db/_replaced/runs/  run docs replaced by a newer copy;  db/_archived/edits/  edits the save consumed
```
`PCLayout` (`layout.py`) is the single definition. `<id>` = `UTC timestamp-zipsha8`.

Flow (`take_update.py`, or the same functions called by the server):

1. `inspect --zip UPDATE.zip`: allow-list, caps, manifest and hashes, JSON check; unpack to `updates/staging/<id>/`; fingerprint comparison. Result has `update_id`, `fingerprint {status: match|mismatch|unknown, message}`, `proceed`.
2. `preview --update <id>`: runs `saver.py preview --workbook <workbook> --db staging/<id>/db --pipeline <pipeline> --copies <copies> --library <library> --backups <backups> --out updates/work/<id>/preview-1 --state <state> [--queue <queue>] [--today D]`. Writes nothing to the workbook, library or backups. The result carries the saver's `diff` (rows added, cells filled, items needing Sammy) and `diff.token`.
3. `save --update <id> --token <token>`: the same arguments plus `--token T --master-is-local --no-rebuild` (`--rebuild` is opt-in until the rebuild has run once against the real pipeline). The saver does the backup, checked swap, pages add-only, ledger, retention. If the workbook was written (exit 0, 5 or 6): the update's run docs are merged into `db/runs/` with the saver's `writeback.json` applied (`ids`, `sheet.written: true`, `review`); a different existing doc with the same id is first moved to `db/_replaced/`; edits the save consumed are moved to `db/_archived/edits/`; the staging folder is moved to `updates/done/<id>/`. Any other outcome leaves the update in staging and the local db unchanged.
4. `init`: `saver.py init` with the workbook's current checksum (first run, or accepting Sammy's own Excel edit).

Local edits: `--include-local-edits` makes a composed `--db` that adds the tracker's own pending `db/edits/*.json` (hand edits, removals) that the update does not carry. Off by default so the saver sees exactly the update. Tones, authors and translations in the update go to the saver and end up in the workbook; they are not copied into the local db (the page is rebuilt from the workbook).

Exit codes: the saver's (0 ok, 2 refused, 3 nothing queued, 4 bad arguments, 5 and 6 written with a follow-up problem), plus 7 update zip refused and 8 fingerprint mismatch not accepted.

## 4. Where SURVEY or the saver did not match

- SURVEY 7e lists `state` among per-story fields; the page's story records (`D`) have no `state`. It exists only on reprint objects (`reps[].state`), which are carried.
- `build_data.py` cannot run from `code/` alone: it needs `legacy_index.html` (only for fallback fields; an empty stand-in works) and `sid_map.json` (vendor copy). `ins-release_pickup` needs `release_pickup_data.py`, which is in `work/localapp/vendor/*/pipeline/insights/`, not in `code/` or `build/`. The PC pipeline folder must ship `insights/release_pickup_data.py` and `sid_map.json`.
- The saver's `diff.rows_added` is a per-tab dict (`{"Coverage": 2, "Originals": 1}`), not a number.
- The saver needs `init` (ledger) before any preview; the PC must run it once at switch-over and after each hand edit.
- Proposal for the saver (not edited): none required. One convenience: a `--db` that may be a read-only folder is already supported (it copies it). A `--json` result path outside `--out` works, as used here.
