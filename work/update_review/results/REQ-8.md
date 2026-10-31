# REQ-8 End-to-end rehearsal of the sheet task's local steps

Script: `L/work/update_review/rehearse.sh` (reads only; writes into its work folder). Run: `bash rehearse.sh` -> work folder `results/REQ-8/run_20261030T201022Z` (103 MB: pipeline copy, out1.xlsx, final workbook, blocks, index.html, per-step .out/.err), log `results/REQ-8/steps.log`, console `results/rehearse_run1.out`.
Inputs: `L/build/pub/pipeline/` copied to `pipeline/` (the published pipeline, not L/code: it predates the REQ-3 patch, so `verify` has no `tabs_checked` here); `example_db.json` expanded to `db/<collection>/<doc id>.json`; `L/work/coverage_current.xlsx` copied to `in.xlsx` (sha256 0159ea384edc..., 8,177 Coverage rows; note the working copy was rewritten during my session: mtime 20:06 UTC, earlier reads showed 8,170 / 8,178 rows); copies = `L/work/handoff_stage/articles` (newest manifest, 19:11 UTC; `work/review_serve/articles` has an older manifest with 10 story keys different, same 3,758 entries); `--queue queue` = empty items/decisions/applied folders; `--today` = 2026-10-30 (TZ=America/Los_Angeles).
Commands: exactly the prompt's step 1 (`--db-dir db --db db.json --check-only`), step 3 (`--copies-needed`; the main run with every flag in the prompt except the optional `--idmap`; `build_data.py out1.xlsx ...`; copies_out over copies/articles; `relmatch.py ... --stories s04929` because `result.relmatch.releases` was empty and stories had one entry; `--after-relmatch`) and step 6 (`tabs_data.py ... --only releases`, `assemble.py pipeline/shell.html blocks/ pipeline/tracker.js index.html`, `data/sheet.json` from the committed workbook copy).

| step | exit | seconds |
|---|---|---|
| s1 check-only | 0 (work: 1 run, 1 page) | 0.3 |
| s3a copies-needed | 0 | 8.6 |
| s3b main pass | 0 | 26.6 |
| s3c build_data (out1.xlsx) | 0 | 10.1 |
| s3d relmatch --update (stories s04929) | 0 | 6.4 |
| s3e --after-relmatch | 0 | 23.2 |
| s6a tabs_data --only releases | 0 | 4.8 |
| s6b assemble | 0 | 0.4 |
| s6c data/sheet.json | 0 | 0.1 |
| total (wall, incl. copying inputs) | | 86 |

Checks: `result.json` verify.ok true (rows 8,177 -> 8,180, 3 rows added, 9 cells filled, 0 conflicts), `result2.json` verify.ok true; empty stderr on every step. `index.html` (10.59 MB) embedded rows block `next` = {aid: 10653, s: 4930, pr: 245}: the master's highest Article ID is 10649 (Coverage; the sheet task also counts the print tab), +3 rows added +1 = 10653, equals `result.counts.next_aid` ("10653", next_s s04930). Matches the expected relation.
Prompt vs script flags: none mismatched. Every flag the prompt uses was accepted (argparse would have exited 2). Observations (not bugs): (1) `--idmap` is optional in the prompt and the rehearsal ran without it; (2) the prompt step 3 passes `--release-related pipeline/release_related.json` to the main pass and the file is only updated by relmatch afterwards; the script keeps that order and `--after-relmatch` re-reads it; (3) the local steps only take ~1.5 minutes on this machine, so the long part of a real run is the Mac staging/commit and the Artifact publish, not these scripts; (4) this uses the fixture db (3 rows), not Sammy's live run, so release pickups, `--library`, `--lookup-cache` and the removal path were not exercised.
