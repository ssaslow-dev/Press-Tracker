# Preview (PREVIEW-v1)

One read-only HTML file of the new tracker, with the workbook's data inside it. Double-click it; it opens offline in Edge, Chrome, Safari or Firefox. No server, no install, nothing goes online.

## Make it

    python3 -I work/localapp/preview/make_preview.py --page "<PC build>/data/site/index.html" \
        --workbook "<AJG Coverage - NewsBank.xlsx>" --out AJG_Tracker_preview.html [--no-internal]

- `--page`: the PC tracker's page (its fonts folder and `articles/manifest.json` are read from next to it; the manifest only says which stories have a saved copy, so the "Saved copy" badges and counts match the PC tracker).
- "Data as of" comes from the workbook's last-saved date (`--as-of YYYY-MM-DD` overrides).
- `--no-internal` (off by default) also drops Tone, Tone note and "tone rated by" from every story and hides the tone badges. Charts and tables built before the page loads from tone totals still show tone numbers.
- The output holds workbook data: keep it out of the repository.

## What is in it

The PC page as it is (same look, fonts inside the file): every story, reporters, outlets, press release headlines and details, bills, charts, maps, story travel; search, filters, sort, the story panel, Data checks and Definitions. Saved views live in the browser's own storage when it allows it.

## What is left out

- Update, Refresh, Spreadsheet download, Tracker files, Manage's Update log and Saved copies, tone/note/detail editing, adding files.
- Saved article copies, photos, print originals ("View original"), full press release texts (a story's panel says "Not in this preview"; the links to the source stay).
- English translations longer than 600 characters are cut (no full article text in a shareable file).

## Files

`make_preview.py` (builder), `shim.js` (stand-in for the runtime the page expects; goes inside the file), `check_preview.js` and `shots.js` (Playwright checks against the PC build), `diff.py` (pixel comparison).
