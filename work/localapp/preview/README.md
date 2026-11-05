# Preview (PREVIEW-v1)

One read-only HTML file of the new tracker, with the workbook's data inside it. Double-click it; it opens offline in Edge, Chrome, Safari or Firefox. No server, no install, nothing goes online.

## Final preview in one command (about 40 seconds)

    AJG_SCRATCH=<scratch folder> sh work/localapp/preview/make_final.sh WORKBOOK.xlsx [OUT.html] [--no-internal]

Builds the page from the workbook (`build/build_tracker.py`), applies the PC page patches (`prep_page.py`: photo viewer, local fonts, TIDY-v1 layout fixes; no full assembly), then `make_preview.py`. Needs in `$AJG_SCRATCH`: `live_pipeline/pipeline/legacy_index.html` and `live_site/` (the inputs of the PC build). Default output `$AJG_SCRATCH/AJG_Tracker_preview_final.html`; `KEEP=1` keeps `prev_work/`. Checked 2026-11-05 against PC version 4 (layout fixes N8-N11, no switch-over screen, Repairs): no console errors, every tab renders, same text as the PC page on all routes. The "saved copy" badges come from `live_site/articles/manifest.json`; refresh `live_site` if saved copies were added since.

## Make it by hand

    python3 -I work/localapp/preview/make_preview.py --page "<PC build>/data/site/index.html" \
        --workbook "<AJG Coverage - NewsBank.xlsx>" --out AJG_Tracker_preview.html [--no-internal]

- `--page`: the PC tracker's page (its fonts folder and the article manifest (`articles/manifest.json`, or `../copies/articles/manifest.json` in a PC build) are read from next to it; the manifest only says which stories have a saved copy, so the "Saved copy" badges and counts match the PC tracker).
- "Data as of" comes from the workbook's last-saved date (`--as-of YYYY-MM-DD` overrides).
- `--no-internal` (off by default) also drops Tone, Tone note and "tone rated by" from every story and hides the tone badges. Charts and tables built before the page loads from tone totals still show tone numbers.
- The output holds workbook data: keep it out of the repository.

## What is in it

The PC page as it is (same look, fonts inside the file): every story, reporters, outlets, press release headlines and details, bills, charts, maps, story travel; search, filters, sort, the story panel, Data checks and Definitions. Saved views live in the browser's own storage when it allows it.

## What is left out

- Update, Refresh, Spreadsheet download, Tracker files (the PC server adds that panel; it is not in the page file), Repairs, Manage's Update log and Saved copies, tone/note/detail editing, adding files.
- Saved article copies, photos, print originals ("View original"), full press release texts (a story's panel says "Not in this preview"; the links to the source stay).
- English translations longer than 600 characters are cut (no full article text in a shareable file).

## Files

`make_preview.py` (builder), `shim.js` (stand-in for the runtime the page expects; goes inside the file), `check_preview.js` and `shots.js` (Playwright checks against the PC build), `diff.py` (pixel comparison), `prep_page.py`, `make_final.sh`.
