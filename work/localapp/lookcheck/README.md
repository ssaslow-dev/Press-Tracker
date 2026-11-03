# Look and function check (SAMELOOK-v2)

Proves that the PC tracker looks and works exactly like the live tracker, and finds every difference that is not a recorded exception.
Reference = the live tracker's own published files (`index.html`, `articles/`, `img/`, `copies/`, `data/`), served read-only by a plain static server on 127.0.0.1.
Candidate = the PC build's page, served by its own launcher on a hard-linked working copy (the build is never written). Same data (workbook sha `bc21c9fb`).

## Rerun

    python3 -I work/localapp/lookcheck/run_lookcheck.py                 # both viewports, capture + compare + function parity (about 60 minutes)
    python3 -I work/localapp/lookcheck/run_lookcheck.py --viewports 1440x900 --only home,clips --no-parity
    python3 -I work/localapp/lookcheck/report.py --out OUTDIR > RESULTS.md

Needs the Linux test build (`app_build/linux/AJG Tracker`, or `--build`), the live tracker's files (`--live-site`), node and Playwright at `/opt/node-tools`, Pillow and numpy.
Viewports: 1440x900 (a full desktop window) and 960x1040 (a window snapped beside Excel on a 1920x1080 screen). Sammy dropped the phone size (the PC tracker only runs on office PCs).
Output folder: `<vp>/{ref,refhide,pc}/<route>.png|.styles.json|.meta.json`, `<vp>/diff_*/` (diff images: differing pixels red), `results_<vp>_*.json`, `parity/`.

Files: `lookcheck.js` capture, `compare.py` pixels/styles/fonts, `parity.js` behaviour, `report.py` tables, `run_lookcheck.py` orchestration.

## What is compared, and how

Same Chromium (what Edge is built on), same viewport, deviceScaleFactor 1, a fixed start time (Monday 2026-11-02 19:30 Los Angeles, so "Good evening", "last 30 days" and the date windows match; time still runs), locale en-US, reduced motion, a fresh browser context per route and target (empty storage). Every page is loaded twice (the second load finds the fonts cached, so both pages paint alike), then after the interaction the viewport is resized by one pixel and back, the story sheet is hidden and shown, and scroll panels are nudged: that makes Chromium paint everything again from the final page. Without it a few rounded-corner pixels (about 30 of 1.3 million, at most 12 levels out of 255) depended on how many times a region had been repainted on the way, and the PC page (which has `window.claude`) repaints more than the reference (which has none). The same steps run on every target.

Per route: a full-page screenshot (or the viewport, for scrolled and hover states), the computed style of **every visible element** matched by DOM path (font-family string, size, weight, style, line height, letter spacing, colour, background, border radius, padding, margin, width, height, plus box position and 15 more properties; the saved-copy frame is walked too), and for every piece of text the **font file Chromium actually used** (CDP `getPlatformFontsForNode`).

Routes and states (each at both viewports): Home; Clips (default, 3 filter combinations, a search, sort plus compact density, scrolled with the sticky header pinned); Data (list-only mentions off and on, scrolled, hover on a chart element); Reporters, Outlets, Press releases, Bills, Story travel (each plus scrolled where the table header pins); a press release page; a bill page with the milestones chart, and a hover on one of its dots; a story sheet (side panel and full page); saved copies: a 2015 story with 5 embedded photos (`s04743`) and a 2025 story with `data:` photos (`s02546`), at the top, middle and end, and full page; the Manage panel.

Fonts: the reference asks Google Fonts exactly as the live tracker does, through Playwright; the first answers are kept in `_fontcache` so every later run gets the same bytes (if Google cannot be reached and nothing is cached, the reference gets `fonts/google`, and the run says so). The PC page asks nothing outside 127.0.0.1 (any outside request is recorded as an error).

### Three targets, two comparisons

- `ref`: the reference untouched. `pc`: the PC page.
- `refhide`: the reference with the recorded exception applied (the same `display:none` rule the PC's server adds for the hidden Update, Refresh, tone, author and translation buttons).
- **Exception applied = `refhide` against `pc`, nothing masked except the Tracker files button (and its shadow).** This is the proof: the target is 0 differing pixels, 0 style differences, 0 font-file differences, in every route.
- **Raw = `ref` against `pc`**, with only the rectangles of the hidden buttons and the Tracker files button masked (painted black in both). Whatever else differs is what hiding causes. Result: nothing outside those rectangles, except the reflow below.

### What the recorded exceptions do to the layout

The masthead row is a three-column grid (logo | spacer | buttons). With the Update and Refresh buttons hidden, the spacer column grows by 323.6 px (743.9 to 1067.5 at 1440 wide) and the button group shrinks by the same amount (560.1 to 236.5). Spreadsheet and Manage are right-aligned in that group and stay at exactly the same x position (1187.48 and 1321.06), so nothing else moves, shifts or wraps; `compare.py` lists the two moved boxes as "reflow" and finds no other difference. At 960 wide the same two buttons stay right-aligned. Other tabs lose only the hidden buttons themselves (they sit in rectangles that are masked in the raw comparison and empty in the PC page).
In the raw comparison, a handful of pixels at the right-hand corners of the Manage button (at most 1 level out of 255) differ: Chromium draws a rounded corner a hair differently when the siblings next to it are gone; `refhide` against `pc` has none, which shows this is the exception and nothing else.

## TIDY-v1 (2026-11-03): the recorded exceptions now include Sammy's approved layout fixes

TIDY-v1 changes the PC page on purpose (docs/DECISIONS.md, TIDY-v1; the changes are patches 15 to 18 in `work/localapp/app/patches/` and the Tracker files button in `app/src/station/web/panel.js`). The look check therefore no longer compares the PC page with the untouched live page for those spots. What changed in the check:

- **`refhide` is now the reference with ALL recorded exceptions applied.** `run_lookcheck.py` makes a copy of the live site's `index.html`, applies the very same patch files the PC build applies (`assemble_app.patch_index_tidy`: patches 15 to 17 and the wording list 18) and serves it as `_refx`; `lookcheck.js --refx` captures `refhide` from it, with the old hide rule for the Update, tone, author and translation buttons, and with a copy of the Tracker files masthead button (`TF_BUTTON`, the same markup `panel.js` builds) placed left of Manage, so the masthead lays out the same. Everything else in the PC page (fonts, photo links, the pipeline, the data) is still compared with the live tracker's own page: **exception applied = `refhide` against `pc` must still be 0 pixels, 0 style differences, 0 font-file differences, 0 function differences.**
- **`ref` against `pc` ("raw") is informational now.** It used to be 0 outside the hidden-button rectangles. It now shows where TIDY-v1 changed the page (table header edges and Top issues cells, Outlets columns at 960, tab and badge text 1 px lower, heading padding, Back/Forward height, Home tile labels, Manage's first tab, reworded sentences, the Tracker files button); `RESULTS.md` lists the routes where raw differs and says which TIDY-v1 item causes it.
- **Masks:** the Tracker files button (`#ajgf-btn`) is masked in the masthead (it is not fixed any more, and is pinned in scrolled screenshots, so its rectangle is in viewport coordinates), the panel `#ajgf` as before. Nothing else is masked.
- **Function parity** (`parity.js`) runs the reference side on the patched copy (`--ref` is `_refx`): the Top issues cells are different markup (a list of items, no commas), so their text differs from the untouched page by design; CSV and "Copy for spreadsheet" use the data columns, not the cell markup, and come from the unchanged `val`/`csv` functions of the columns (patches 16 and 17 touch only the `cell` markup), so they are not affected.
- The TIDY-v1 changes themselves are proven separately, in the real engine, by `app/tests/test_tidy.py` (pixel sampling of every header edge at rest and pinned, light and dark, 1440 and 960; no sideways scroll; Top issues lines; alignment numbers; the masthead button and panel; the wording).

## What was found and fixed (all through `work/localapp/app/` and `work/localapp/fonts/`)

| # | Difference | Cause | Fix |
|---|---|---|---|
| 1 | Every page: text anti-aliased differently (0.7 to 1.6 percent of pixels), text 0.02 px wider or narrower, 851 of 1362 text pieces drawn from another font file | The PC served the static **fontsource** versions of Roboto Slab and Public Sans; Google serves other (variable) files | `fonts/fetch_google_fonts.py` fetches the very files Google serves for the old tracker's two requests (sha256 pinned in `fonts/google/FONTS_GOOGLE.json`); assembly copies them; the font files are now byte-identical to what the old page loads |
| 2 | Italic: the PC page defined a Public Sans italic face; the old page never loaded one (the browser slants the regular face) | The single `fonts.css` carried the saved-copy viewer's italic face | `fonts/google/page.css` has no italic; `viewer.css` (what the saved-copy frame asked Google for) has it and is used only inside the frame (patches 07, 08) |
| 3 | Bold text in a saved copy used the 700 face; the old frame only had 400 and 600 (and Roboto Slab 600 and 700) | Same single stylesheet carried every weight | `viewer.css` holds exactly the old frame's faces |
| 4 | Clips: the newest story lacked its "Related press release" badge; 3 releases showed one related story fewer; the press release tab's counts differed | `code/release_related.json` in the repository is older than the page the live tracker last published (the 2026-10-30 save added relations for the 3 newest stories, and the published page lists them in its `tab-releases` block) | `build/build_tracker.py` merges the published relations into the staged state file (merged, never shrunk, published order and types); the `tab-releases` data block is now byte-identical to the live page's |
| 5 | (test only) The look check itself: the test page asked for `fonts/fonts.css` | | `tests/test_localfonts.py` updated: page defines 28 Roboto Slab and 12 Public Sans faces and no italic; frame exactly the five faces it asked for |

## Results (final run, against the fixed build; full tables in RESULTS.md and below)

Before the fixes (first pass, Home and Clips only, 1440x900): Home 0.68 percent of pixels differing (8,841), Clips 1.61 percent (92,099), 343 elements with different widths or positions, 1,002 of 1,364 text pieces drawn from a different font file, the newest Clips row missing its release badge.
After: **exception applied (reference with the recorded exception against the PC page): 0 differing pixels, 0 style differences, 0 font-file differences, 0 function differences, in 31 routes and states at each of the two sizes**, with two noted exceptions of noise:

- `data_on` at 1440x900 in the full run: 38 pixels (0.0005 percent), each at most 1 level of 255 apart, at rounded corners on the right edge. The same route rerun on its own twice gives 0. The reference compared with itself gives 0 (noise floor measured), so this is not input noise, but raster noise that depends on machine load and paint history; no style, box or text differs.
- Raw comparison (reference untouched, only the exception rectangles masked): 0 differing pixels except `home` 1440x900 (10 pixels, at most 1 level, the corners of the Manage button) and `manage` (732 pixels: the Manage panel loses its hidden Update-related buttons, so what follows them moves up; `refhide` against `pc` is 0). The masthead reflow is two boxes (spacer and button group); Spreadsheet and Manage do not move.

The Tracker files button is masked (it sits in the masthead since TIDY-v1; before that a floating button of about 110 x 36 px at the bottom right) in every pixel comparison, and its elements are left out of the style comparison.

## Remaining differences

See RESULTS below. Everything not listed there is identical.

- **PHOTOLINK-v1 (recorded exception).** New saved copies keep remote photo links; the old viewer removes them. The viewer code in `index.html` therefore differs (patch 06). The routes above use copies with embedded photos, which are identical; a copy with a remote photo is the only place the PC page shows something the old page would not (and needs the internet).
- **Update-only data in the page** (`fetchrules` block: skip lists in a different order, a few more learned fetch results). Used only by the Update button, which is hidden; no visible effect.
- **Tracker files** button and panel (recorded exception, masked).
- Fonts load from the PC's own folder instead of fonts.gstatic.com (same bytes).
- The reference here has no `window.claude`, the PC page has the local one. This has no visible effect (verified above); function parity gives the reference an in-memory stand-in with the same db and downloads calls so notes, views and downloads follow the same path.
- Not checked here: Edge itself and Windows font rendering (Chromium on Linux is the stand-in; Windows applies its own text smoothing to both old and new pages alike).

## Function parity (`parity.js`)

The same clicks and typing on both, outcomes compared (lists of story ids, counts, pager text, chips, URLs, text hashes, downloaded bytes): Clips search (8 terms incl. a miss), every date range, one filter from each facet then Clear all, list-only on/off, every sort twice, compact density, page sizes, the five preset views and saving, applying and deleting a view, the story sheet (first, next, next, previous, full page, Escape), saved copies (text hash, images loaded with their sizes, mention finder "n of m", sandbox), team notes (add, edit, reopen, clear: message text and badges), Back/Forward header buttons and Alt+Left over a 10-step walk, 19 hash routes (plain, with filters, invalid) opened directly, downloads (CSV, Source spreadsheet byte for byte against the workbook sha `bc21c9fb`, Copy clips list, Copy for spreadsheet, ticked-story CSV, the four tab CSVs), and every tab's table (each sort, entity page) and the Data tab's controls.

## Result tables

### 1440x900

| route / state | page size | differing pixels (exception applied) | % | style differences | font-file differences | differing pixels (raw, exception rectangles masked) |
|---|---|---|---|---|---|---|
| bill_hover | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 3,175 | 0 of 1,821 | 0 (masthead spacer and button group resize, see README) |
| bill_page | 1440x8471 | 0 of 12,198,240 | 0.0000 | 0 of 3,175 | 0 of 1,821 | 0 (masthead spacer and button group resize, see README) |
| bills | 1440x4913 | 0 of 7,074,720 | 0.0000 | 0 of 1,129 | 0 of 960 | 0 (masthead spacer and button group resize, see README) |
| bills_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,129 | 0 of 960 | 0 (masthead spacer and button group resize, see README) |
| clips | 1440x3974 | 0 of 5,722,560 | 0.0000 | 0 of 2,220 | 0 of 1,362 | 0 (masthead spacer and button group resize, see README) |
| clips_f1 | 1440x4219 | 0 of 6,075,360 | 0.0000 | 0 of 2,194 | 0 of 1,322 | 0 (masthead spacer and button group resize, see README) |
| clips_f2 | 1440x3631 | 0 of 5,228,640 | 0.0000 | 0 of 2,004 | 0 of 1,268 | 0 (masthead spacer and button group resize, see README) |
| clips_f3 | 1440x4090 | 0 of 5,889,600 | 0.0000 | 0 of 2,341 | 0 of 1,514 | 0 (masthead spacer and button group resize, see README) |
| clips_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 2,220 | 0 of 1,362 | 0 (masthead spacer and button group resize, see README) |
| clips_search | 1440x7452 | 0 of 10,730,880 | 0.0000 | 0 of 2,294 | 0 of 1,435 | 0 (masthead spacer and button group resize, see README) |
| clips_sort_dense | 1440x3220 | 0 of 4,636,800 | 0.0000 | 0 of 1,933 | 0 of 1,304 | 0 (masthead spacer and button group resize, see README) |
| data_hover | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 4,353 | 0 of 2,478 | 0 (masthead spacer and button group resize, see README) |
| data_off | 1440x5791 | 0 of 8,339,040 | 0.0000 | 0 of 4,353 | 0 of 2,478 | 0 (masthead spacer and button group resize, see README) |
| data_on | 1440x5819 | 38 of 8,379,360 | 0.0005 | 0 of 4,386 | 0 of 3,647 | 0 (masthead spacer and button group resize, see README) |
| data_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 4,353 | 0 of 2,478 | 0 (masthead spacer and button group resize, see README) |
| home | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 120 | 0 of 259 | 10 (masthead spacer and button group resize, see README) |
| manage | 1440x3974 | 0 of 5,722,560 | 0.0000 | 0 of 2,964 | 0 of 2,083 | 732 (masthead spacer and button group resize, see README) |
| outlets | 1440x14336 | 0 of 20,643,840 | 0.0000 | 0 of 3,570 | 0 of 2,532 | 0 (masthead spacer and button group resize, see README) |
| outlets_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 3,570 | 0 of 2,532 | 0 (masthead spacer and button group resize, see README) |
| release_page | 1440x1005 | 0 of 1,447,200 | 0.0000 | 0 of 330 | 0 of 382 | 0 (masthead spacer and button group resize, see README) |
| releases | 1440x6846 | 0 of 9,858,240 | 0.0000 | 0 of 1,662 | 0 of 1,277 | 0 (masthead spacer and button group resize, see README) |
| releases_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,662 | 0 of 1,277 | 0 (masthead spacer and button group resize, see README) |
| reporters | 1440x5535 | 0 of 7,970,400 | 0.0000 | 0 of 2,114 | 0 of 1,511 | 0 (masthead spacer and button group resize, see README) |
| reporters_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 2,114 | 0 of 1,511 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_data | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,573 | 0 of 1,011 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_data_end | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,573 | 0 of 1,011 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_old | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,195 | 0 of 751 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_old_end | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,195 | 0 of 751 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_old_mid | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,195 | 0 of 751 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_old_wide | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,195 | 0 of 751 | 0 (masthead spacer and button group resize, see README) |
| story_sheet | 1440x3974 | 0 of 5,722,560 | 0.0000 | 0 of 2,293 | 0 of 1,393 | 0 (masthead spacer and button group resize, see README) |
| story_sheet_wide | 1440x3974 | 0 of 5,722,560 | 0.0000 | 0 of 2,293 | 0 of 1,393 | 0 (masthead spacer and button group resize, see README) |
| travel | 1440x8686 | 0 of 12,507,840 | 0.0000 | 0 of 1,849 | 0 of 1,355 | 0 (masthead spacer and button group resize, see README) |
| travel_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,849 | 0 of 1,355 | 0 (masthead spacer and button group resize, see README) |
| **total** | | **38** | | **0** | **0** | **742** |

Function parity at 1440x900:

| interaction | steps compared | differences |
|---|---|---|
| clips_search | 11 | 0 |
| clips_dates | 18 | 0 |
| clips_facets | 22 | 0 |
| clips_sort | 17 | 0 |
| saved_views | 10 | 0 |
| story_sheet | 8 | 0 |
| saved_copy | 5 | 0 |
| team_notes | 6 | 0 |
| history | 14 | 0 |
| hash_routes | 11 | 0 |
| downloads | 11 | 0 |
| tab_tables | 69 | 0 |

### 960x1040

| route / state | page size | differing pixels (exception applied) | % | style differences | font-file differences | differing pixels (raw, exception rectangles masked) |
|---|---|---|---|---|---|---|
| bill_hover | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 3,173 | 0 of 1,821 | 0 (masthead spacer and button group resize, see README) |
| bill_page | 960x10413 | 0 of 9,996,480 | 0.0000 | 0 of 3,173 | 0 of 1,821 | 0 (masthead spacer and button group resize, see README) |
| bills | 960x5706 | 0 of 5,477,760 | 0.0000 | 0 of 1,127 | 0 of 960 | 0 (masthead spacer and button group resize, see README) |
| bills_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,127 | 0 of 960 | 0 (masthead spacer and button group resize, see README) |
| clips | 960x6113 | 0 of 5,868,480 | 0.0000 | 0 of 2,218 | 0 of 1,362 | 0 (masthead spacer and button group resize, see README) |
| clips_f1 | 960x5987 | 0 of 5,747,520 | 0.0000 | 0 of 2,192 | 0 of 1,322 | 0 (masthead spacer and button group resize, see README) |
| clips_f2 | 960x5301 | 0 of 5,088,960 | 0.0000 | 0 of 2,002 | 0 of 1,268 | 0 (masthead spacer and button group resize, see README) |
| clips_f3 | 960x6100 | 0 of 5,856,000 | 0.0000 | 0 of 2,339 | 0 of 1,514 | 0 (masthead spacer and button group resize, see README) |
| clips_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 2,218 | 0 of 1,362 | 0 (masthead spacer and button group resize, see README) |
| clips_search | 960x10136 | 0 of 9,730,560 | 0.0000 | 0 of 2,292 | 0 of 1,435 | 0 (masthead spacer and button group resize, see README) |
| clips_sort_dense | 960x3832 | 0 of 3,678,720 | 0.0000 | 0 of 1,931 | 0 of 1,304 | 0 (masthead spacer and button group resize, see README) |
| data_hover | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 4,390 | 0 of 2,496 | 18 (masthead spacer and button group resize, see README) |
| data_off | 960x6800 | 0 of 6,528,000 | 0.0000 | 0 of 4,351 | 0 of 2,478 | 0 (masthead spacer and button group resize, see README) |
| data_on | 960x6828 | 0 of 6,554,880 | 0.0000 | 0 of 4,384 | 0 of 3,647 | 0 (masthead spacer and button group resize, see README) |
| data_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 4,351 | 0 of 2,478 | 0 (masthead spacer and button group resize, see README) |
| home | 960x1055 | 0 of 1,012,800 | 0.0000 | 0 of 118 | 0 of 219 | 0 (masthead spacer and button group resize, see README) |
| manage | 960x6113 | 0 of 5,868,480 | 0.0000 | 0 of 2,962 | 0 of 2,083 | 732 (masthead spacer and button group resize, see README) |
| outlets | 960x16000 | 0 of 15,360,000 | 0.0000 | 0 of 3,568 | 0 of 2,532 | 0 (masthead spacer and button group resize, see README) |
| outlets_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 3,568 | 0 of 2,532 | 0 (masthead spacer and button group resize, see README) |
| release_page | 960x1132 | 0 of 1,086,720 | 0.0000 | 0 of 325 | 0 of 382 | 0 (masthead spacer and button group resize, see README) |
| releases | 960x8168 | 0 of 7,841,280 | 0.0000 | 0 of 1,660 | 0 of 1,277 | 0 (masthead spacer and button group resize, see README) |
| releases_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,660 | 0 of 1,277 | 0 (masthead spacer and button group resize, see README) |
| reporters | 960x8623 | 0 of 8,278,080 | 0.0000 | 0 of 2,112 | 0 of 1,511 | 0 (masthead spacer and button group resize, see README) |
| reporters_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 2,112 | 0 of 1,511 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_data | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,568 | 0 of 1,011 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_data_end | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,568 | 0 of 1,011 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_old | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,190 | 0 of 751 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_old_end | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,190 | 0 of 751 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_old_mid | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,190 | 0 of 751 | 0 (masthead spacer and button group resize, see README) |
| saved_copy_old_wide | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,190 | 0 of 751 | 0 (masthead spacer and button group resize, see README) |
| story_sheet | 960x6113 | 0 of 5,868,480 | 0.0000 | 0 of 2,288 | 0 of 1,393 | 0 (masthead spacer and button group resize, see README) |
| story_sheet_wide | 960x6113 | 0 of 5,868,480 | 0.0000 | 0 of 2,288 | 0 of 1,393 | 0 (masthead spacer and button group resize, see README) |
| travel | 960x9891 | 0 of 9,495,360 | 0.0000 | 0 of 1,847 | 0 of 1,355 | 0 (masthead spacer and button group resize, see README) |
| travel_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,847 | 0 of 1,355 | 0 (masthead spacer and button group resize, see README) |
| **total** | | **0** | | **0** | **0** | **750** |

Function parity at 960x1040:

| interaction | steps compared | differences |
|---|---|---|
| clips_search | 11 | 0 |
| clips_dates | 18 | 0 |
| clips_facets | 22 | 0 |
| clips_sort | 17 | 0 |
| saved_views | 10 | 0 |
| story_sheet | 8 | 0 |
| saved_copy | 5 | 0 |
| team_notes | 6 | 0 |
| history | 14 | 0 |
| hash_routes | 11 | 0 |
| downloads | 11 | 0 |
| tab_tables | 69 | 0 |

