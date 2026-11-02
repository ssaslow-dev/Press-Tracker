# Building the tracker page for the local app

`build_tracker.py` builds the tracker page from a workbook, the way the live tracker is built, without writing into `code/`, `build/` or `data/`.

## Rebuild

    python3 -I work/localapp/build/build_tracker.py --out OUTDIR --legacy PATH/legacy_index.html [--live-site DIR]

Needs Python 3.11+, pandas, openpyxl, beautifulsoup4, and `bash` (it runs `build/build.sh`). About 40 seconds.

- `--xlsx FILE`: workbook to build from. Default `data/AJG Coverage - NewsBank.xlsx` (the snapshot). It is copied, never written.
- `--legacy FILE`: the live tracker's `pipeline/legacy_index.html`. Required: it holds translated story text, so it is not in the repository (see `vendor/live_*/README.md`). build_data uses it for fallback fields where a workbook cell is blank.
- `--live-site DIR`: a folder holding `articles/`, `img/`, `copies/` fetched from the live tracker. Copied into the site as is.
- `--vendor DIR`: default is the newest `work/localapp/vendor/live_*`.

## What it does

1. Copies `code/`, `build/tabs/`, `build/clean_playbook.md`, `build/build.sh` and the docs into `OUTDIR/stage/`, laid out like the old workspace (`docs/*.md` at the root, `work/sid_map.json`, `build/shell/shell.html`, `work/index_original.html`).
2. Adds the pieces the repository lacks from `vendor/`: page shell, `sid_map.json`, the Outlets tab, the Insights views and `bill_milestones.json`.
3. Runs, inside the stage: `code/apply_all_patches.py --root` (tracker JS from `code/tracker/`, pipeline folder, checks) then `build/build.sh` (page built twice, from `code/` and from the pipeline folder; both must match, and they do).
4. Writes `OUTDIR/site/`: `index.html`, `data/sheet.json` (workbook as `{filename, b64}`, byte-identical to the live file), `data/release_texts.json`, plus `articles/`, `img/`, `copies/` with `--live-site`.

Logs: `OUTDIR/apply_all.log`, `OUTDIR/build_sh.log`, `OUTDIR/stage/work/build_last/` (both builds and block comparison).

## Serve and look

    cd OUTDIR/site && python3 -m http.server 8765 --bind 127.0.0.1    # then open http://127.0.0.1:8765/index.html

Use one fixed address and port: the page's browser-side storage (notes, saved views) is tied to it.

## What is stubbed or cannot be rebuilt

- `articles/*.json`, `img/*.json`, `copies/articles/*`: not rebuilt. `code/make_copies.py` needs `work/html_clean`, `work/texts/nb`, the image cache, `error_copies.csv`, `deletions.csv` and more, none of them here; the handoff kit says its output is a check, not a source. They are used as fetched from the live tracker.
- `pdf/<code>/pN.jpg` (50 page images, about 45 MB, referenced by saved copies): not fetched; those copies show without the page image.
- `legacy_index.html`: supplied by `--legacy` (see above).
- Update, tone, author and translation buttons: still in the page. Without `window.claude` they do nothing useful (below). Nothing is hidden yet. To hide them, inject CSS the way `code/make_viewer.py:25` does: `#runFind,#runRefresh,#raStrip,[data-runfind],#updGo,#updRefresh,#updSave,#updAdd,#updCopy,#updAgain,[data-dl],#bkCsv{display:none!important}` (the `[data-dl]` and `#bkCsv` entries hide downloads too; drop them to keep those).
