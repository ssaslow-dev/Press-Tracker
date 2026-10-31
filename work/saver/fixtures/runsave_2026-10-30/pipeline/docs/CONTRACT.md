# Data contract — new tracker (v1 2026-10-26; wording updated 2026-10-28)

L = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib

## Inputs
- Workbook: the Coverage tab of the master `~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx` (README rule 7); the sheet task and the Update button's rebuild read the master. Historical snapshots (read only): L/work/coverage_snapshot_1793053407608.xlsx (2026-10-26) and L/work/coverage_prepped.xlsx (adds the **Role** column after "Mentions \"Gabriel\" in text", filled Topic/Bills/Reach, and the 101 added rows).
- IDs (DECISIONS 2026-10-27 new ID scheme + amendment): Article ID and Print Article ID = plain 5-digit numbers (`00034`), no prefix, no o/r suffix; old IDs (nb-/ws-/pq-NNNNN) kept in "Old Article ID" / "Old Print Article ID". Story ID = `sNNNNN` (was jg-NNNNN, same number). The 6-hex old-tracker codes (jg-xxxxxx) in "Tracker story code" stay as they are. Library file names: `<nb|pq|ws><NNNNN><o|r>-s<NNNNN>.<ext>` (o/r only here); rows with no Story ID `<format><NNNNN>.<ext>`.
- Old tracker: L/work/index_original.html (embedded data + JS), L/work/tracker_original.js (the JS from the main <script>, char offset 4086065 of the html).

## Embedded blocks in the new index.html (built by L/code/build_data.py)

### `<script id="data" type="application/json">`: array, one record per Original row
Same field names and value formats as the old records, so the rendering code keeps working, with these changes:

| field | meaning / source |
|---|---|
| id | **Story ID** (sNNNNN; was jg-NNNNN before the ID migration) — the entry key everywhere (db docs, URLs, DOM ids) |
| code | old tracker code (jg-xxxxxx, 6 hex) or "" — use ONLY to find saved copies (articles/manifest.json, img, pdf) and to migrate old db docs |
| aid | Article ID of the Original row (5-digit; was nb-/pq-/ws-) |
| date, prec, year | Date (YYYY-MM-DD); prec "day"/"month"/"year" as before |
| outlet, pub, author, hl, hl_en, text_en, lang | Outlet, Publisher, Author / byline, Headline, Translated Headline, Story in English, Language ("" for English) |
| topic, issue | Topic (issue = topic, as before) |
| bills | list of strings, from Bills ("; "-separated in the sheet) |
| reach, media, county | Reach, Medium, Outlet county |
| tone, twhy, tauto | Tone ("Not rated" if blank), Tone note, tauto = Tone rated by starts with "Claude" |
| role | Role column |
| src, added | carried from the old record when code exists; else src from Data Source ("NewsBank", "ProQuest, full text", "Web, verified"), added = "" (new rows: "Tracker update YYYY-MM-DD") |
| link, plink, lstat, pq | Publisher link (or NewsBank article link if none), NewsBank article link, Link status, ProQuest link |
| rep | the sheet's "# of reprints" (distinct outlets other than the original's) |
| reps | **NEW**: array of reprint objects for every Reprint row with the same Story ID, sorted by date then outlet: `{aid, outlet, date, county, state, link, hl, src}` (missing values = "") |
| also | generated from reps for backward compatibility: distinct outlet names joined "; " in reps order (same style as old `also`) |
| rc | distinct non-empty counties of the reps |
| conf | **removed** (Confirmed is dropped) |

### `<script id="rows" type="application/json">`: dedupe index over ALL Coverage rows
- HIDEUNVERIFIED-v1 (2026-10-28): the only block that still carries "Reprint (unverified)" rows (kind ""), so the Update button never re-adds them; every other block, view, count, copy and CSV is built from `reprint_rule.hide_unverified(Coverage)`.
`{"cols": ["aid","sid","kind","outlet","date","hl","links"], "rows": [[...], ...]}`
- kind: "O" original, "R" reprint, "" unclassified
- hl: normalized headline (lowercase, punctuation stripped, whitespace collapsed)
- links: list of normalized URLs (scheme and www. stripped, trailing slash and query stripped) from Publisher link, NewsBank article link, ProQuest link
- `"next": {"aid": <max Article ID + 1>, "s": <max Story ID number + 1>, "pr": <next free Release ID number>}` — the next free numbers at build time (one sequence over Article ID and Print Article ID; the sheet task assigns the real ones). Before the ID migration this was `{"ws": …, "jg": …}`.

### `<script id="idmap" type="application/json">`
`{"<old code>": "<Story ID>", ...}` for every old code found in Tracker story code (Original rows first, then any row). Used to migrate db docs and old links.

### `<script id="covcols" type="application/json">`
The Coverage column names in sheet order (incl. Role). The Update button's TSV and proposed rows use exactly this order.

## Proposed rows from the Update button (db collection "runs", field `rows`)
Each find → one object keyed by Coverage column names, plus:
- "Article ID": placeholder `NEW-<run>-<n>`; "Story ID": an existing sNNNNN for a reprint, or `sNEW-<run>-<n>` for a new story (pages from before the migration may still send `ws-NEW-…` / `jg-NEW-…`; the sheet task accepts both)
- "Original or reprint": "Original" | "Reprint"; "Data Source": "Web search (TinyFish)"
The sheet task replaces placeholders with real numbers and writes the mapping back into the run entry as `ids: {placeholder: real}`.
- BUTTONOPT-v1 (agent-buttonopt2, 2026-10-28): run rows may carry `_page` (the reprint candidate's saved page, pages doc `rp-<hash6>`) and `_origin` (`{service, how, cands:[{url, title, date, outlet, page: og-<hash6>}]}`); neither is a sheet column. The edits doc gains field `reported`. Result keys added: `pages_drop`, `reprint_failed`, `reprint_untested`, `origin_added`, `origin_unverified`, `held`, `outlet_unresolved`, `removed`, `removal_failed`, `edits_reported`, `red_rows`, `av_show_to_channel`, `av_date_review`, `copies_changed`. sheet_task.py flags: `--db-dir`, `--copies-needed`, `--copies-out`, `--img-cache`.

**Worked example (COLDSTART-v1).** `build/tests/sheet_task/fixtures/example_db.json` is a complete, runnable input (the db export format `{collection: {doc_id: doc}}`; with `--db-dir` the same docs are read from `<collection>/<doc id>.json` files). One run `run-example1` with three rows (an Original with a saved page, a Reprint of it in another outlet, a Reprint of the existing story s00037), a tone for the new story and the page doc keyed by the Article ID placeholder:
```json
{"runs": {"run-example1": {"at": "2026-10-27T10:00:00Z", "mode": "find", "rows": [
   {"Article ID": "NEW-run-example1-1", "Story ID": "sNEW-run-example1-1", "Original or reprint": "Original", "Data Source": "Web search (TinyFish)",
    "Date": "2026-10-25", "Outlet": "Test Gazette", "Headline": "Gabriel bill test story one",
    "Publisher link": "https://www.testgazette.com/news/gabriel-one/", "Link status": "Publisher URL"},
   {"Article ID": "NEW-run-example1-2", "Story ID": "sNEW-run-example1-1", "Original or reprint": "Reprint", "Outlet": "Echo Times", "Publisher link": "https://echotimes.com/gabriel-one"},
   {"Article ID": "NEW-run-example1-3", "Story ID": "s00037", "Original or reprint": "Reprint", "Outlet": "Reprint Weekly", "Publisher link": "https://reprintweekly.com/x"}]}},
 "tones": {"sNEW-run-example1-1": {"tone": "Neutral", "why": "tone for new story", "rated": "2026-10-27", "by": "Claude"}},
 "pages": {"NEW-run-example1-1": {"url": "https://www.testgazette.com/news/gabriel-one/", "title": "Gabriel bill test story one", "scoped": "<html>…the saved page, ≥ a few paragraphs naming him…</html>"}},
 "edits": {}, "authors": {}, "translations": {}, "reprints": {}}
```
Run (fixture workbook; real runs use the staged master and the flags in HANDOFF 5.2): `python3 -I code/sheet_task.py --db build/tests/sheet_task/fixtures/example_db.json --xlsx build/tests/sheet_task/fixtures/work/tmp_agent-ids/migrated_current.xlsx --out out.xlsx --result result.json --pages-dir pages --idmap build/tests/sheet_task/fixtures/work/tmp_agent-ids/blocks_post/idmap.json --today 2026-10-27`. Verified 2026-10-30: exit 0, `verify.ok` true, `runs["run-example1"].ids` = `{"NEW-run-example1-1": "09762", "NEW-run-example1-2": "09763", "NEW-run-example1-3": "09764", "sNEW-run-example1-1": "s04297"}`, counts 3 rows added / 8 cells filled / next_aid 09765 / next_s s04298 (the fixture workbook is a 2026-10-27 snapshot, so these numbers are the fixture's, not the master's). Exit codes: 0 ok, 2 verification failed (do not commit), 3 with `--check-only` = nothing queued. The saved page lands in `pages/<year>/ws<aid>o-<sid>.html`.

## Rules every component follows
- Workbook: fill blanks only; never change an existing value. New fills in the default black font (DECISIONS 102; coordinator 2026-10-28; sheet_task.py since OUTLETRULES-v1). Red whole-row font = not in the tracker.
- Story ID is the key everywhere; old codes only for saved-copy lookup and migration.

## Coverage row conventions (from the retired "Reprint info" tab, OUTLETRULES-v1 gap-fill, 2026-10-28)
- **Web + Print row:** one outlet's own web and print editions of the same article are ONE row, never reprints and never tested by the 90% rule (Sammy, 2026-10-26). The web version is the main row; the print edition sits in Print Article ID (its own 5-digit number), Print date, Print headline, Print section, Print word count, Page, the NewsBank print columns and File name 2. A new find that is another edition of a row already in the story fills that row's blank print/web cells instead of adding a row (sheet_task same-outlet rule; DECISIONS 172).
- **Location:** Outlet city / county / state are the outlet's home, not the story's subject (CalMatters = CA).
- **Outlet names:** NewsBank style ("Sacramento Bee, The"); outlet variants are one outlet per code/outlet_rules.json (sheet_task.norm_outlet(name, Outlet city): "Today's Edition" / ": Blogs" variants, feeds, aliases, generic names by city, keep_separate pairs).
- **# of reprints** counts an outlet once across its web and print editions, repeat runs, regional editions and feed variants (outlet_rules.json). FINALCHECK-v1 B1 (2026-10-30): the original's own house is not a reprint either (tab-common house_map: "Today's Edition", "Name: … Edition/English/Spanish/Portuguese/Blogs", "(Substack)/(Medium)", FoodNavigator-USA, outlet_rules aliases such as CNN Wire Service = CNN; chain sister papers and city-qualified names are NOT one house). The page counts this way (repNames/reprintCount); the sheet cell is written on touched stories only (12 disagreements listed in work/out/repcount_not_written_2026-10-30.csv).

## Official press releases (RELEASES-v2 + RELCHECK-v1, 2026-10-27)

### Workbook tab "Press releases" (one row per official release; built by agent-releasecheck, kept up to date by the sheet task; current layout: RELTAB-v1/v2 below)
(Old 16-column layout, superseded 2026-10-28 by "Press releases tab layout (RELTAB-v1)" below.) Columns, in order: Date (YYYY-MM-DD, as posted) · Title · Subtitle/dek · Source ("Gabriel's office (gabriel.asmdc.org)", "California Legislative Jewish Caucus", or both joined by "; ") · URL (hyperlink; unique) · Release type · Bills mentioned ("; ") · Issue (tracker labels) · Gabriel quoted (Yes/No/blank) · Co-issuers / other members named · Contact · Word count · In tracker (Yes/No) · Tracker release ID ("sNNNNN" or "sNNNNN; sNNNNN": the Press-release stories that carry it) · Coverage stories linked (runs) · Note.
Scope: every release on gabriel.asmdc.org; Jewish Caucus "Press Release" items only from his chair tenure (Date >= 2020-11-18; Sammy 2026-10-27 "2 no" — pre-tenure rows stay on the tab with Note "OUT OF SCOPE …" and are not counted).
The Update button's release check (RELCHECK-v1) queues new releases in its run doc as `releases_new: [{src: office|caucus, source, url, title, date, dek, text (page markdown, ≤12,000 chars), err?}]` (at most 5 a run); sheet_task.py appends them (blanks where the page doesn't say) and marks Coverage rows by the release text rule (RELRULE-v1 below; it replaced the original headline match), listing them in the run's review as releases_flagged (default black font).

### Block `<script id="ins-release_pickup" type="application/json">` (v2; built by build_data.py via build/insights/release_pickup_data.py)
`{"v":2, "cols":["key","date","iss","title","bills","topic","auto","sids","rows","url","official"], "rowcols":["aid","outlet","date","kind"], "rel":[...], "src":"sheet:Press releases", "n_tab":<tab rows>, "n_scope":<in-scope releases>, "tenure":"2020-11-18", "known":[out-of-scope tab URLs]}`
- one entry per release: key (a Story ID, or "offNNN" for an official release no outlet ran), date (official date when linked, else earliest run), iss (o = his office, b = as Budget chair, c = Jewish Caucus), title (official when linked), bills, topic, auto (1 = added by rule, not by the review; the headline auto-rule is retired by RELRULE-v1, so new builds carry 0), sids (Press-release Story IDs), rows ([aid, outlet, date, kind] runs; [] = "No pickup found"), url (official URL or ""), official (1/0).
- n_tab / n_scope are build-time counts (244 / 236 at the 2026-10-27 build).
- Readers: the Press releases tab (v19, TABS-v1; before that the Press desk "Releases" view, before that Insights "Press releases"); the tracker's release wiring (story panel line "From press release", Clips badge, search text, CSV columns "Press release" / "Press release link") for stories in `data` whose id is in a release's sids; the Update button's release check (known URLs + newest date per site).

### Tracker tabs and links (REORG-v1, 2026-10-27; superseded by TABS-v1 below from v19)
Tabs: Home (#), Clips (#clips), Data (#data; #report and #trends still open it), Press desk (tab id `tab-in`, #press-desk/<view>?<params>).
Press desk views (view ids unchanged, so blocks and story-panel links keep working): Pitch = `reporters` (#press-desk/pitch; params win=24, issue, author), Releases = `release_pickup` (#press-desk/releases), Bills = `bill_timeline` (#press-desk/bills), Story travel = `story_travel` (#press-desk/story-travel). Old #insights/<id> links open the same view. `tone_topic` is drawn in Data › Tone (not in the Press desk sub-nav); #insights/tone_topic and #press-desk/tone-by-issue open Data.

### Release text rule (RELRULE-v1 + RELCHECK-v2, agent-relrule 2026-10-27)
- A Coverage row carries an official release only when its saved text passes `reprint_rule.text_verdict` against the release text (`code/release_rule.py`; release versions headline+dek+body and body; rows dated 1 day before .. 30 days after). No saved text = untestable: listed, never marked.
- `release_texts.json` (code/ + pipeline/): `{"v":1, "rel": {url: {date, title, dek, body, src: office|caucus}}}`, one entry per "Press releases" tab row; the sheet task appends new releases (result `release_texts_changed`; step 7 republishes `pipeline/release_texts.json`); apply_all merges, never shrinks.
- sheet_task.py: `--release-texts FILE`, `--library DIR` (staged `<year>/<file>`), `--release-candidates` (prints the `<year>/<file>` list to stage, exits). Result keys: `releases_flagged[]` now carry `mode`, `conf`, `pct`; new `releases_untestable[] {aid, outlet, release, url, why}`.
- Block `ins-release_pickup` v2 (built by release_pickup_data.py v3): stories join an official release only through the tab's Tracker release ID; REL lists only the 5 releases with no official posting.
- `sid_map.json` (pipeline, SIDMAP-v1): passed to build_data.py by the button's rebuild (step 6).

### Press releases tab layout (RELTAB-v1 + RELCHECK-v3, agent-reltab 2026-10-28)
(RELTAB-v2 since 2026-10-28: + Release ID, Saved Copy?, File name — see "Press-release copies" below; 46 columns.)
One value per cell; 43 columns in this order (code/reltab.py `COLS`, the single definition; pipeline file `reltab.py`):
- Identity: Date (real date, yyyy-mm-dd) · Title · Subtitle/dek · Source (ONE site: "Gabriel's office (gabriel.asmdc.org)" or "California Legislative Jewish Caucus") · URL (hyperlink, unique) · Also on caucus site (date) · Also on caucus site (URL) (hyperlink; the 3 releases posted on both sites) · Release type · In scope (Yes/No; No = caucus release before 2020-11-18)
- Content: Issue (tracker Topic labels) · Gabriel quoted (Yes/No) · Caucus release names Gabriel (Yes/No, caucus rows only) · Word count
- People: Legislator 1..6 · Legislators (more) · Other official 1..4 · Other officials (more) · Contact name · Contact title · Contact phone · Contact email (lower case). Legislators = Assemblymember / Senator / Assembly Speaker / Senate President pro Tempore; everyone else = Other official. Names canonical (reltab.CANON).
- Bills: Bill 1..6 · Bills (more) — "AB 1234" form
- Tracker: In tracker (Yes/No) · Tracker release ID 1 · Tracker release ID 2 (one sNNNNN each) · Coverage stories linked (count of runs) · Tracker date (earliest pickup) (real date; only where it differed from the official date) · Before text rule (In tracker / ID / runs) (state before RELRULE-v1, 2026-10-27)
- Note (what remains free text)
"(more)" columns hold the overflow "; "-joined in the original order (caps = max needed, capped: legislators 16 → 6, others 6 → 4, bills 14 → 6). Header bold, frozen at C2, filter on all columns, black font.
Readers: release_pickup_data.py (v3.1) and build/tabs/releases_data.py read either layout through a local `_tab_rows()` that rebuilds the old column names (Source with "; Jewish Caucus", Bills mentioned, Tracker release ID, Co-issuers / other members named); the ins-release_pickup block is byte-identical to the one built from the old layout; tab-releases `r[url][4]` (co-issuers) = the split names re-joined, legislators first. Code that needs the old view of a row: `reltab.legacy(get, cols)` / `reltab.legacy_df(df)`.
Writers: sheet_task.py RELCHECK-v3 (code/_history/patches/patch_reltab.py, retired apply_all step 4m) appends new releases with `reltab.row_values()` (names from the release text via `reltab.officials()` + CANON, bills, contact split, In scope) and `_rel_mark` adds a story to the next Tracker release ID column; with an old-layout sheet it still writes the old 16 columns. Nothing may pack several values into one cell.


### Press-release copies (RELCOPIES-v1 + RELTAB-v2 + RELCHECK-v4, agent-relcopies2/3 2026-10-28; sheet written 2026-10-28, master 1fae6a32…)
- **Release ID**: `prNNNNN`, permanent, one per "Press releases" tab row (in or out of scope), assigned pr00001… by Date, then Title (case-folded), then URL (244 on 2026-10-28: pr00001 2018-06-10 … pr00244 2026-10-24); new releases take the next number (max on the tab or in release_texts.json + 1). The 5 releases with no official posting (release_pickup_data REL) are not tab rows and have no Release ID.
- **Tab columns (RELTAB-v2 = RELTAB-v1 + 3)**: "Release ID" is column A; "Saved Copy?" (Yes/No) and "File name" (`<prid>.html`) follow "Also on caucus site (URL)"; frozen at D2. `reltab.COLS` is the single definition; `reltab.RELCOPY_COLS` = the three; the sheet task treats them as optional (an old tab without them is appended as before).
- **Library**: cleaned copy `Tracker library/Press releases/<year>/<prid>.html`, raw page `Tracker library/_original_html/Press releases/<year>/<prid>.html` (<year> = release date). Page = `<title>` + header div (Source · date / URL / "Saved <date>"; lines equal to the tab are removed by the cleaner, "Saved" kept) + `<h1>` official title + the release (dek, date + contact block, body, photos with absolute src + alt text). Cleaned by clean_html.py in library mode with the sites `gabriel.asmdc.org` (+ a46.asmdc.org) and `jewishcaucus.legislature.ca.gov` in clean_rules.json. The cleaned body text equals release_texts.json's `body` (244/244 on 2026-10-28).
- **release_texts.json**: each entry `{date, title, dek, body, src, prid}`; merged, never shrunk (apply_all also fills fields a pipeline entry lacks).
- **Viewer copies**: `make_copies.py --releases work/html_clean/press_releases` -> `articles/releases.json` (`releases-2.json`… above the shard size) `{prid: html}`, manifest key = Release ID. Not stories: never in `data`, counts, Clips search or exports.
- **Blocks**: `ins-release_pickup` cols += `"prid"` (12th; "" for the no-posting releases); `tab-releases` `r[url]` += `[6]` Release ID, `[7]` file name when Saved Copy? = Yes; `rows.next.pr` = next free Release ID number.
- **Press releases tab (tracker)**: release page `#press-releases/<prid>` (old date-title slugs and `legacy` links redirect there). The page keeps the official link (copy icon left) and, when the release has a saved copy, a "Saved copy of this release" row whose title opens it with `ctx.openSaved(prid, …)` = the story panel's article viewer (side panel, full-page toggle, Gabriel highlighting; the official link is listed in the panel). No saved copy: the link only. List search text includes the Release ID; CSV gains "Release ID" and "Saved copy".
- **Update button (RELCHECK-v4, sheet_task.py)**: a new release gets the next Release ID; its page (the run's `html` when given, else built from the release text) is cleaned and saved to `--pages-dir` as `Press releases/<year>/<prid>.html` + `_original_html/Press releases/<year>/<prid>.html`; Release ID / Saved Copy? / File name filled (No + blank when there is no text); release_texts.json entry gets `prid`. Result keys `release_copies[] {prid, url, file, original, status, flags}` (or `why`), `releases_new[].prid`. The prompt commits them to the library (add-only) and adds each to articles/releases.json + the manifest.

### Related stories on release pages (RELRELATED-v1, agent-relrelated 2026-10-28; Sammy kept the 90-day text window)
- A release's related stories are evidence only (code/relmatch.py; spec work/tmp_agent-relrelated/spec.md): `text` = shared runs of ≥ 25 words (runs found in 3+ releases are boilerplate), story dated −1 … +90 days; `quote` = ≥ 12-word runs totalling ≥ 20 words, −1 … +30; `bill` = shared bill and the story is on the release's subject (tf-idf text cosine ≥ 0.14 or headline ≥ 0.10), −1 … +7; `topic` = English text cosine ≥ 0.25, −1 … +7; `possible` = shared bill in the bill window but the subject cannot be checked (not English / no saved text). The release's own copies (rows passing the release text rule) are not stories and never listed.
- State file `release_related.json` (code/ + pipeline/): `{"v":1, "version":"RELRELATED-v1", "rel": {Release ID (prNNNNN; the 5 no-posting releases: their Story-ID key): [[Story ID, type, days after the release], ...]}}`. The Update button updates the pipeline copy incrementally (`relmatch.py --update`); apply_all merges code/ into pipeline/ by key and Story ID, never shrinks it.
- RELRELATED-v3 (rp-match 2026-10-28): same file shape, version "RELRELATED-v3", one row per Story ID per release. New types: `nearcopy`, `anchor` (tier 1), `later`, `laterquote` (tier 3 "Later coverage", NOT related stories). Tiers and labels = `relmatch.TIER` / `relmatch.LABEL`; full table build/relplan_contract.md "rp-match". apply_all's merge must let a newer version's row type replace an older one (work/tmp_rp-match/handoff.md).
- Block `tab-releases` gets `"rel"` = the state filtered to stories in the build (build/tabs/releases_data.py; file looked up next to the pipeline folder, then <lib>/code, or env RELRELATED_JSON).
- Release page: "Related stories · N" (chart + list; hidden when N = 0) with the evidence breakdown, collapsed "Possibly related · N", "Bill coverage" before/after counts (context only). Header (HEADER-v2): kicker Press release · date · source, dek = the summary, clusters Who / What / Coverage / Links (Official release, or "Not posted on Gabriel’s or the Jewish Caucus’s site."). CSV: Related stories / Possibly related stories / Same-bill stories before / after.

### Press-release copies v2 + tab columns (RELCOPIES-v2 + RELTAB-v3, rp-copies 2026-10-28; sheet write prepared, not yet committed)
- **Renamed tab columns** (copies are not tracker stories): "In tracker" → **Has copies**; "Tracker release ID 1/2" → **Copy story ID 1/2**; "Coverage stories linked" → **Copies (rows)**; "Tracker date (earliest pickup)" → **First copy date (if different)** (earliest copy row date when it differs from Date; recomputed). `reltab.RENAMED` maps old → new; `reltab.col(H, name)`, `is_new_layout`, `ids`, `legacy` accept both, so the RELTAB-v1/v2 descriptions above read with the new names. "Before text rule (In tracker / ID / runs)" keeps its name (history).
- **New derived columns** after First copy date: **Related count** (int) and **Related story IDs** ("; "-joined Story IDs; the one sanctioned multi-value cell on the tab): `reltab.related_values(release_related.json rows, exclude = copy stories, known = tracker stories)`, tiers `reltab.RELATED_TYPES` ("possible" excluded). Recomputed on every build / Update; never edited by hand. 48 columns.
- **Issue** label "District / community" for district honors, local grants/checks and district events.
- **More copies** (code/relcopy.py, same Press release = Yes + Copy story ID mechanism): `near_copy` (≥ 50% of a ≥ 250-word release in ≥ 25-word runs, −1…+30 d; story share ≥ 0.85 → copy, else review) and `wire_title_copy` (PublicNow row with no text whose headline is the release title cut at "…", ≥ 5 words, 0…+1 d → copy; overrides DECISIONS 133). A copy filed as a Reprint of another issuer's story gets its own Story ID (pr00182 / 01760 → s04749).
- `release_pickup_data.py` v3.2 reads either column name; block shape unchanged. rp-final: `known` also lists the tab's "Also on caucus site (URL)" values.
- rp-final (2026-10-28): tab-releases `bc` excludes bills named only as background (thr x.bg); the page shows "N stories on <bill> that week". pipeline/release_related.json is merged with newer rows replacing older ones (apply_all merge_rel_related); pipeline ships relthread.py and relcopy.py. Tab blocks: soft cap 200 KB.

## Audio & video details tab (AVTAB-v1, agent-avtab 2026-10-28)

### Workbook tab "Audio & video details" (one row per Coverage row with Medium Podcast / Radio / TV / Video; key Article ID)
Layout in `code/avtab.py` (COLS; pipeline file): Article ID · Story ID · Medium · Item type (Episode | Broadcast segment | Video clip | Web story) · **Channel** (AVSHOW-v1, 2026-10-28: the channel/station/network/publisher that carried the item, e.g. "KTLA", "CNN", "KFI AM 640", "Jewish California" (YouTube); every row type; blank only when no channel is stated, e.g. independent podcasts) · Show/program (real program names only: never a channel, station, publication or host-site name) · Station (call sign) · Network · Episode/segment title · Episode number · Air/publish date (real date; archive.org clips: local Pacific date of the clip ID's UTC time) · Air time ("18:30 PT", "1-2a ET") · Duration · His role (guest | interviewed | soundbite | discussed | brief mention) · Guest 1..4 + Guests (more) · Mention 1..5 + Mentions (more) (timestamps; Mention 1 = first) · Timestamp basis · Transcript kind (full | excerpts | none) · Transcript file (library file name) · Show page link · Apple Podcasts link · Spotify link · YouTube link · Archive.org link · Details from (provenance) · Notes.
Hosts are NOT on the tab: they are Coverage Author 1..N. Web story rows (text stories on a station's site) carry only Item type, Station, Network. Blank = not established; never guessed. The item itself stays a normal Coverage row (Outlet = show, Headline = episode/segment title, Author N = hosts).
Writers: the backfill (883 rows on 2026-10-28: 869 existing + 14 podcast imports; 899 after the same day's follow-ups); sheet_task.py `Task.apply_av` appends a row for every Podcast/Radio/TV/Video row the Update button adds (from the find's saved page / transcript; a run doc may carry `av: {placeholder: {column: value}}`, blanks only). Existing tab rows are never changed by code. Result keys `av_rows[] {aid, type, role, transcript}`, `av_skipped[]`.
- AVTAB-v2 (code/_history/patches/patch_avtab.py): for new archive.org TV finds `Task.apply_av` also sets the Coverage Date (and Year) of the row it added to the Pacific air date; result key `av_date_fixes`.

### build_data.py (AVTAB-v1 via code/_history/patches/patch_avtab.py, retired apply_all step 4n)
- `OUT/av.json` = `{"v":1, "cols": avtab.KEYS, "rows": {aid: [values in KEYS order, trailing blanks trimmed]}}` (not embedded by assemble.py; for the integrator).
- AVSHOW-v1 (v20 code, 2026-10-28): avtab.COLS/KEYS carry "Channel"/`channel` after Item type/`type` (readers read by header). `avtab.channel_of()` fills Channel on every item type (Outlet [network] bracket, URL domain, page metadata, saved copy); `show_of()` returns real program names only (station clips: only from the main clip's own description). Tracker: `avChannel(r)` / `avShow(r)` (01_authors.js; Show only for non-Web-story items); the AV panel shows separate Channel and Show rows (Show omitted when blank; Notes / Details from not shown); Clips facets `channel` and `show`; Clips CSV columns Channel and Show after Format.
- every `data` record whose Original Article ID is on the tab gets `av` = {key: value} (non-blank only; keys sid/medium/from dropped); every reprint object in `reps` likewise. KEYS: type, show, station, network, title, epno, air, airtime, dur, role, g1..g4, gmore, m1..m5, mmore, tbasis, tkind, tfile, lshow, lapple, lspotify, lyoutube, larchive, notes. (+~75 KB on the data block.)


## Tracker tabs (TABS-v1, v19, 2026-10-28; agent-tabs + agent-v19finish)

### Menu, routes, old links
Home (#) · Clips (#clips) · Data (#data) · Reporters (#reporters[/<slug>]) · Outlets (#outlets[/<slug>]) · Press releases (#press-releases[/<slug>]) · Bills (#bills[/<bill-session slug>], e.g. ab-418-2023-24, abx1-4-2025-26-1st-ex-sess) · Story travel (#story-travel[/<Story ID>-<words>]). A tab's filters live in its URL (`?q=&<facet>=a|b&sort=-n&open=`; a removed default is `<facet>=~`); entity pages also carry the chart (`ci cb co cm cs cf ca ct cq`) and list state (`when pg per sort` + Clips facet keys). Old #insights[/<id>], #press-desk[/<slug>], #release_pickup, #bill_timeline, #story_travel, #pitch links and data-ins-go entry points redirect (win= dropped). Back / Forward header buttons walk an in-page history of these places + the open story panel (NAVHIST-v1).

### Code and pipeline
code/tracker/53_tabs.js (framework: menu, routing, search-tab and entity-page components, shared helpers, maps, NAVHIST, DATATRIM) and code/tracker/52_us_map.js are sections of the tracker JS (code/tracker/ concatenated into build/js_merged.js by apply_all; TABS-v1 was apply_all step 4l, retired 2026-10-28). Tab modules build/tabs/<id>.js (reporters, outlets, releases, bills, travel; contract build/tabs_contract.md) and their data builders build/tabs/<id>_data.py + _common_data.py ride in pipeline/tabs/; assemble.py adds the modules (tabs_assemble.py) and build_data.py the blocks (tabs_data.py): `tab-common` (canonical outlet names, Publisher spans, out-of-state outlets), `tab-outlets`, `tab-releases`, `tab-travel`, read by `ctx.block(name)`.

### Link rules (LINKRULES-v2 + LINKSCOPE-v1)
- Entities open their page: bill → Bills page of the session the story/release date falls in (`ctx.billLink(bill, {date})`, bills module `billSlug`); author → Reporters page (`ctx.authorLink(name)`); outlet → Outlets page (`ctx.pageLink('outlets', …)` / `tbOutletSub`); release → its page.
- Attributes open Clips filtered: `ctx.issueLink(topic)`, `ctx.facetLink(field, value)` with field ∈ Clips FACETS keys (topic, reach, media, lang, county, state, channel, show …), rendered as `<button data-tbclip='{"<field>":[v], <scope>}'>`. On an entity page the link carries `page.scope(entity, ctx)` = `{sel: {pub|author|bills: [...]}, when: [from, to, label]?, ranin?, label}` (outlet: its originals' Clips outlet names, else "ran in"; reporter: author; bill: bill + session dates when the number is reused). A state is filterable too: Clips has a State facet (`state`, GEOMAP-v1, 2026-10-28; `statesOf(r)` = the state of an out-of-state regional/local outlet; California, national and wire outlets have none), so a state opens Clips filtered like any attribute.
- Inside Clips (its list and the story panel opened there) clicks filter Clips; the panel adds `button.tb-pgo[data-tb-go][data-tb-sub]` "page ›" icons after bills, authors and the outlet (PAGEICON-v1). The panel shows "How it spread ›" (Story travel page) when another outlet ran the story (HOWSPREAD-v1). Story headlines always open the panel.

### Entity page spec additions
`page.spec()` may return `chart:false`, `list:false`, `after(el, ctx)`, `cards` (html after the header), `rowAs(r)` (this entity's copy of a story: outlet/date/pub/prec), and `embeds: [{tab, title, cap, unit(u) | item(it), cols:[column keys], limit}]` = the named tab's own list rows filtered to this page (EMBEDROWS-v1, `ctx.miniList(host, tab, o)`; item-level defaults of that tab apply, date defaults do not).

### Published files
index.html, data/sheet.json, **data/release_texts.json** (= pipeline/release_texts.json; the Press releases tab fetches it lazily for full-text search, RELTEXTS-v1), articles/<year>.json + **articles/releases.json** (release copies keyed by Release ID, RELCOPIES-v1; `make_copies.py --releases`) + articles/manifest.json (viewer copies + search text; make_copies.py NAMING-v2 reads current library names `<nb|pq|ws><NNNNN><o|r>-s<NNNNN>.<ext>`, files named for a Story ID, OCR texts work/texts/nb/<Old Article ID>.json or by the clip's library name, the undated folder), img/<n>.json, pdf/, pipeline/ (incl. tabs/, tabs_assemble.py, tabs_data.py, make_copies.py, avtab.py, reltab.py, relpage.py).


## Inclusion, wave 1 (INCL-v1, incl-apply 2026-10-28; PROPOSED for the v22 write, nothing written yet)
Decisions: DECISIONS 2026-10-28 inclusion line. Data plan: work/tmp_incl_apply/plan.csv; code: work/tmp_incl_apply/patches/01..05 (apply after reprint-code).

### Coverage column "Mention depth" (new)
- **Position:** immediately after **Role**, before "Press release" (Coverage; Originals gets it in the same relative place because rebuild_originals copies every Coverage column; the Removed tab and the new "Unmatched print pages" tab carry Coverage's columns in Coverage order, so they get it too). Readers read by header; `covcols` picks it up; add it after 'Role' in COV_FALLBACK (code/tracker/40_update_outlets.js).
- **Values:** `Featured` (op-ed by him, his name in the headline, ≥ 3 sentences naming him with the first in the opening quarter, or ≥ 2 quoted sentences) · `Quoted` (≥ 1 sentence quoting him) · `Named` (named in prose) · `List-only` (STRICT: every sentence naming him is a roster/list: caucus or co-author lists, attendee/endorser/signer lists, results lines; ≥ 5 names, ≥ 4 commas, nothing predicated of him) · blank = no text on file, or the text never names him. Derived from the row's saved text (own copy, else the story's copy) by `mention_depth()` (patch 04, = work/tmp_incl_apply/depth.py).
- **Writers:** the v22 write fills every row from plan.csv (`set_depth`; a derived column, so the write may replace a value); afterwards sheet_task `fill_counts()` fills it for every row it saves a page for (blanks only). Role stays as it is (Featured ⊇ Named in headline + Op-ed).

### Coverage column "Format" (FORMAT-v1, v23 write 2026-10-29)
- **Position:** immediately after **Medium** on Coverage, Originals (mirror), Removed and Unlinked print pages. Readers read by header; `Format` follows 'Medium' in COV_FALLBACK (code/tracker/40_update_outlets.js).
- **Values:** `Article` · `Print` · `Broadcast segment` · `Video clip` · `Audio segment` · `Podcast episode` · `Unknown` (the row's own form, separate from the outlet's Medium; "Unknown" = the v23 backfill's low-confidence rows: unverified reprints with no link or AV item). Every Coverage row is filled.
- **Writers:** the v23 write backfilled every row (work/tmp_v23_outlets/changes.csv: AV tab Item type, Edition, print fields; high + medium as proposed, low -> Unknown); sheet_task `format_of()` sets it on new rows (Update button: link host / Medium), `apply_av` refines a new row from its extracted Item type. build_data: `fmt` on data records and reps; blank falls back to the AV item type, else Article (fmtOf).

### Tracker (note for the UI integrator)
- build_data: `data` records get `depth` (the Original row's value, "" when blank); every `reps` object gets `depth` too. Clips CSV: column "Mention depth" after Role.
- **List-only is kept and shown, badged, and out of headline counts:** a small "List only" chip on the story's list row and in the story panel (next to Role); a Clips facet `depth` (Featured / Quoted / Named / List-only / Not rated); every headline count (Home totals and charts, Data tab, Outlets / Reporters / Bills / Press releases counts, Story travel) leaves out stories whose depth is List-only by default, with one toggle "Include list-only mentions" (stored in the URL like other filters). Blank depth counts as coverage (no text ≠ list-only).
- Tone: List-only rows stay rated as they are; the designer's suggestion to exclude them from tone rating by default is not decided.

### Workbook tab "Unmatched print pages" (new)
- The 1,443 NewsBank print-page rows of Coverage that have no Story ID (Original or reprint blank, no text; page-image pointers awaiting clipping/linking) move here with all their columns, in Coverage column order, sorted as in Coverage. Key Article ID (numbers stay reserved in the one Article ID / Print Article ID sequence). Not coverage: not counted, not in the tracker. When a page is clipped and linked, its row moves back to Coverage (or its data goes into the matched row's print columns) and leaves this tab. 09720 (AOL web row with a blank Story ID) does not move; it needs a Story ID.
- Readers to update: sheet_task.Sheet (max_num and the link / old-ID indexes must also read this tab), build_data (`rows` dedupe index and `next` must include it), make_copies, extract_nb, the clip pipeline targets (work/clip), apply_fills / prep_workbook / author_columns / billstatus/parse / make_id_map / migrate_ids / patch_ids (Coverage loops), insights_data / tabs_data (counts).

### Removed tab (categories used by INCL-v1)
`3 not coverage` (calendar / meeting listings), `3 database/results page` (results tables), `3 database/listing page` (index/archive/tag/sitemap pages, profile/scorecard/donor/bill-tracker/topic pages, slate-only voter guides), `3 only outside article` (Times of Israel sidebar rows), `4 not about Gabriel` (another Jesse Gabriel; stubs whose full live page never names him). From tab = Coverage, Removed on = the write date; the Originals tab drops the same rows on its rebuild.


### Coverage column "Quoted" (QUOTED-v1, 2026-10-29)
- **Position:** immediately after **Mention depth** on Coverage, Originals (mirror), Removed and Unlinked print pages. Readers read by header; 'Quoted' follows 'Mention depth' in COV_FALLBACK.
- **Values:** `Yes` (Gabriel's own words are quoted in the story's text) or blank (no quote of him, an op-ed by him, or no text). Derived from the row's saved text by sheet_task.quoted_him(); a row with no text takes its story Original's value. DEPTHQ-v1 (2026-10-29): Quoted and Mention depth agree: Quoted=Yes on a row whose depth would be Named gives depth Quoted; depth is never Quoted when quoted_him is False and the text is on file (it becomes Named); Featured, List-only and blank are unchanged (sheet_task.depthq(), called from fill_counts). quoted_him also counts a speech-verb subject plus a quote of 2+ words in the same sentence.
- **Writers:** the 2026-10-29 write backfilled every row; sheet_task fill_counts() sets it on rows it saves a page for; a no-copy originator copies it from its crediting reprint.
- **Tracker:** build_data `quoted` ('Yes' or '') on data records and reps; a "Quoted" tag and Clips facet; Clips CSV column "Quoted" after Mention depth.

### Shared viewer copy (VIEWER-v1, 2026-10-29)
- A second, shareable artifact (https://claude.ai/artifact/6vhKKcNXarhSKwnCMk3Bks, capabilities {}) is built from the tracker's built index.html by `code/make_viewer.py`: data/rows move to data/data.json + data/rows.json, a VIEWER-LOAD loader fetches them, and the Update/download controls are hidden. It exists because the sharing review refuses a ~10 MB page. It must be refreshed after every tracker publish (HANDOFF 4.4). Share-safe media rules: MEDIAGATE-v1/v2 (static copies only; no svg/vtt/video/audio markup).
- Role has no blanks on Originals (FINALCHECK-v1 D1: blank non-release Originals written as Mentioned in story / Named in headline); build_data has no Role fallback. Undated rows (06976, 06977) show "Undated" and are out of period counts.
