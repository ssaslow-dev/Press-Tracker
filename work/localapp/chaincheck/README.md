# Chain check (CHAINCHECK-v1)

One command that proves the PC tracker and the Update station still work together. Run it before switch-over and before every final zip or station republish. Any failure blocks the zip or republish (docs/DECISIONS.md, CHAINCHECK-v1).

    python3 -I work/localapp/chaincheck/run_chaincheck.py [--pc-build DIR] [--station-html FILE] [--workbook FILE] [--published] [--scratch DIR]

Exit code: 0 all checks passed, 1 a check failed, 2 the check could not run. It prints a PASS/FAIL line per step (with the failed checks under it) and writes the full report to `SCRATCH/chaincheck/last_report.md` (and a copy at `SCRATCH/last_report.md`).

It takes about 5 minutes with `--pc-build` (reusing a build) and 6 with a fresh assembly (1 minute) on this machine; the PC's preview and save take about 3 minutes of that.

## What it does

| Step | What happens | What is checked |
|---|---|---|
| 1 PC makes the for-Update file | A working copy of the PC test build (keeper) starts; in the page, "Make for Update file" is clicked and the downloaded JSON is kept | file name, `ajg-for-update` format version 1, fingerprint = the workbook's sha256, more than 3,000 stories, no article text, copy kept in `data/for_update` |
| 2 Update station loads the file | The station page (stubbed `window.claude`) takes that file | format accepted, story count and fingerprint (first 8) shown, "made today" with no age warning, the Update button and both PDF boxes open |
| 3 stubbed Update, NewsBank PDF, ProQuest export, zip | The station runs its whole plan against canned TinyFish and Claude answers: two new web stories (one Spanish, with author and translation), one YouTube station clip (KTLA), one reprint candidate (a wire copy repeating the text of a story the tracker has), one search hit whose link the tracker already has (must not return). Then a synthetic NewsBank PDF in the real layout (one new story, one the tracker already has by NewsBank link) and a synthetic ProQuest export (one article) are added; the update zip is downloaded | the run, the proposals, the duplicate dropped, the reprint recorded against the right story, tone, the NewsBank known story recognised and not added, the PDFs cut, the zip: manifest, fingerprint, names block (ws / nb / pq, numbers from the file's `rows.next`), every library file listed is in the zip |
| 4 PC brings in the update and saves | In the PC page the zip is dropped; the preview is read; Save is pressed; the page reloads | accepted (fingerprint matches), preview text, Save says "Saved." with the backup named, workbook changed, backup = old bytes, ledger entry, Coverage tab grew by the expected rows, the known NewsBank story not added again, the new stories in the page, the reprint attached to its story, Clips search finds them (headline word and a word from inside a saved copy), library files at their NAMING-v2 paths, run docs in the PC db, the same zip refused a second time |
| 5 refresh file to a reader copy | The keeper makes a refresh file; a second copy (reader) brings it in | the reader shows the same new stories, the same workbook bytes, the same library files at the same paths, the same page |
| 6 nothing real was touched | | the workbook copy given is unchanged |

Every outside host is refused and recorded (nothing may leave 127.0.0.1); page errors count as failures.

## Files

| File | What |
|---|---|
| `run_chaincheck.py` | the command; steps 1, 4, 5, 6 and the report |
| `pc.py` | PC helpers: hard-linked working copy of the test build, local server, node step driver |
| `ui_pc.js` | the Playwright step interpreter for the PC page (a copy of `work/localapp/app/tests/ui.js`) |
| `make_inputs.py` | synthetic NewsBank PDF (`station/tests/nb/make_nb_pdfs.py`, real layout) and ProQuest export (`station/tests/pq/make_pq_export.py`) from the for-Update file, and the oracle `plan.json` |
| `station_drive.js` | drives the station page: steps 2 and 3, writes `station_results.json` and the update zip |

Nothing outside this folder is changed. The check reads the app and station sources (the assembler and `station/dist/index.html`; `build_station.py` runs only if `dist` is missing).

## Needs

Python 3.11+ with `openpyxl`, `pandas`, `reportlab`, `pypdf` (the same as the app and station tests), node with Playwright and Chromium at `/opt/node-tools` (`PLAYWRIGHT_MODULE` overrides), the workbook copy and the live-page files the assembler needs (`--workbook`, `--live-site`, `--legacy`; the defaults are the scratchpad copies `wb_0bccc1fc.xlsx` and `live_v65`).

## Options

- `--pc-build DIR`: reuse an assembled Linux test build (`AJG Tracker` folder, or the `--out` folder holding `linux/AJG Tracker`). Default: assemble a fresh one from `--workbook` (a copy of the workbook is made; the original is never written; its sha256 is re-checked at the end).
- `--station-html FILE`: the station page to test. Default `work/localapp/station/dist/index.html`. A file that is a whole page (starts with `<!doctype` or `<html`) is served as it is; the build output is a fragment and is wrapped in the skeleton the Artifact tool adds.
- `--published`: marks the run as against a copy of the PUBLISHED page (see below); the file is served unwrapped.
- `--station-manual`: drive the station with automatic mode off (buttons pressed by hand). Default: automatic mode on, as a person finds it: the folder downloads by itself after the web run, the PDFs are added by themselves, and a second, complete folder replaces the first (checked, and the PC refuses the early one once the complete one is saved).
- `--scratch DIR`: working folder (default the session scratchpad, or `$CHAINCHECK_SCRATCH`).

## Testing the published page

The published station is https://claude.ai/artifact/5uGsM8yQMphjAQbKhvc5SL. The check needs a saved copy of what is published, not a rebuild:

1. In a Claude session with the Artifact tool, read it: `Artifact` with `action: "read"` and `url: https://claude.ai/artifact/5uGsM8yQMphjAQbKhvc5SL`. For an artifact the person owns this returns the raw HTML, and the result names the file it saved. (If the result is only a summary, the page is not owned by this account; use the owner's session.)
2. Run `python3 -I work/localapp/chaincheck/run_chaincheck.py --published --station-html THAT_FILE`.

The stub is installed before the page's scripts run and replaces `window.claude`, so the published page is exercised exactly as a viewer's browser would, but with canned TinyFish and Claude. What cannot be tested this way: the real capability prompts (consent for TinyFish and Claude), the real `downloads` dialog and the real artifact database. Those are covered by the first real update on switch-over day (checklist step 7).

## What the check does not prove

- Real TinyFish and Claude answers (they are canned); real NewsBank and ProQuest PDFs (synthetic in the real layout; the real ones are tested by `station/tests/*real*`).
- A real Windows machine (this uses the Linux test build; the Windows folder differs in the Python and launcher only).
- Anything about the old live tracker (never touched).

## Notes on how the inputs are chosen

- The reprint candidate repeats the real text of a story the tracker already has. The story is picked from the build's `data/copies` article shards (the copies the save reads), so the PC's text test can confirm the reprint. The test build's shards come from the scratchpad copy of the live page and can lag behind the workbook; a story with no entry there would give "no text to compare" at save time, so such stories are skipped.
- The YouTube clip's page carries a description of over 60 words: the PC does not save a page with less than 60 words of body ("not saved to the library"), and the station still names a library file for it. That gap is listed by the PC in plain words; the check treats any unsaved named file as a failure, so a clip with a short real description will show it.
- Station names are checked strictly: if the save gives a file another name than the station did (the PC says so in the preview and the saved panel), the check fails on purpose, and later checks follow the PC's own name so the rest of the chain is still tested.
- A refresh file made right after the first save is a FULL one (about 840 MB, 20 to 30 seconds here). If the "Make refresh file" step hangs, look for a `.zip.part` in the keeper copy's `data/refresh_out` (SCRATCH/work/keeper). One run stalled once at 67 MB and could not be reproduced (the same job run by hand took 22 seconds); another builder's process activity on the machine at that time is the likely cause.
