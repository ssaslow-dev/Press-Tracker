# AJG Press Tracker: instructions for Claude

Press-coverage database for CA Assemblymember Jesse Gabriel (AD-46), kept by Sammy (ssaslow@berkeley.edu). It catches every real story about Gabriel the Assemblymember and nothing else: print, online, TV, radio, podcasts and non-English outlets. Reprints are grouped under the story that ran first. Sammy prefers lean, precise prose and plain words; he is not a programmer.

## Where things live

**In this repository:**
- `docs/`: START_HERE, HANDOFF (operations), DECISIONS (the decision log; tags like `NOSCHED-v1`; newest at the end), CONTRACT (run-doc schema), AGENT_BRIEF, BOARD, TONE_GUIDE. Search DECISIONS by tag; don't read it whole.
- `code/`: tracker page sources (`code/tracker/NN_*.js`), the save pipeline (`sheet_task.py` plus rule modules), reference data (`outlets.json`, `reporters.json`, `reporter_employment.csv`, `outlet_rules.json`, `lookup_cache.json`), `make_viewer.py` (shared copy), and `sheet_task_prompt.md` (today's manual save procedure).
- `build/`: build scripts (`apply_all_patches.py`, `build.sh`), tab sources (`build/tabs/`) and tests (`build/tests/run_all.sh`, about 5 min; TABS harness in `build/tests/tabs/`).
- `work/saver/`: the save program in progress (see Current work).
- `work/desktop_plan/`: Fable's Windows plan (PLAN.md, BUILD_NOTES.md). It's on hold because IT probably won't allow local installs.
- `work/update_review/`: the Update-button review (REPORT.md) and its patches.

Docs written before the move refer to the old workspace root `L = /tmp/.../scratchpad/lib`. In this repository, that root is the repo itself (`L/code` = `code/`, `L/DECISIONS.md` = `docs/DECISIONS.md`).

**Not in this repository:**
- Master workbook: `~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx` on Sammy's Mac. It is the single source of truth. Current sha256 starts `bc21c9fb` (2026-10-30 save).
- Article library: `~/Desktop/Tracker library/<year>/`, `_original_html/<year>/`, `Press releases/<year>/`, and `Backups/`, all on the Mac. It is add-only.
- Live tracker (claude.ai artifact): https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv, also at https://claude.ai/code/artifact/27f923dc-2407-40a0-b8a9-ec3dfed87ad9. Its database holds runs, pages, edits and similar. Capabilities: db, downloads, sample, and mcp TinyFish (search, fetch_content).
- Shared read-only copy: https://claude.ai/artifact/6vhKKcNXarhSKwnCMk3Bks. Rebuild it with `code/make_viewer.py` after every tracker publish.
- Review queue artifact: https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB.
- claude.ai Project "AJG Mentions Database" holds copies of the docs under `library/`.
- Plan docs (Claude Docs): first draft https://claude.ai/artifact/1DoeTcpiPqYeXemdCk6Jfy; Fable's Windows plan https://claude.ai/artifact/TRc8DoNxDpByjKA5zNevvN.

## Hard rules (never break these; ask Sammy if one seems wrong)

- **Nothing scheduled.** No scheduled tasks, cron jobs or background runs for the Update button or saves (NOSCHED-v1). Saves happen only when Sammy asks.
- **Free sources only** (FREEONLY-v1). TinyFish search and fetch are free with a key and already in use. Never log in, create accounts, enter keys or credentials, or bypass paywalls or bot blocks.
- **No YouTube or advocacy blogs** (NOBLOGS-v1). Judge by outlet; TV stations' own clips stay.
- **Reference data first** (LEARN-v1). Check `lookup_cache.json` and the reference files before any web lookup, and save confirmed answers back.
- **Fill blanks only**, unless a recorded decision says otherwise.
- **The library is add-only.** Files that must go are moved to `_to_delete/`, never deleted, unless Sammy asks.
- **One writer at a time.** Every master write follows rule 7: back up first, write a uniquely named staged file, commit, verify the sha256 where the master lives. Excel must be closed.
- **No Exa.** Never put full saved article text behind a public link. Don't commit the workbook or library text to this repository unless Sammy decides it should live here.
- **Report permission denials plainly.** Never route around them.
- **Tab work** (TABKEEP-v1) only tweaks existing behavior.

## Model policy (MODELS-v1; Sammy asked to optimize tokens)

- **Haiku:** search and fetch loops, bulk checks.
- **Sonnet:** building and mechanical fixes.
- **Fable:** only for judgment. Use it at three checkpoints on the save program:
  1. the change-checking code;
  2. replay mismatches nobody can explain;
  3. a line-by-line review before the first live save.

  A Fable reviewer sees code, rules and test results only, never the builder's notes.

## Current work: the save program (`work/saver/`)

- **Goal:** replace the ~30 manual steps in `code/sheet_task_prompt.md` with one program, `saver.py preview|save`. It works on local paths only; getting the workbook in and out is a separate adapter. It runs on Windows and Linux, Python 3.11+.
- **Rules:** `work/saver/SAVE_RULES.md`. Sammy approved them on 2026-10-31 (SAVER-RULES-v1); his answers are at the end of that file and override SAVER_SPEC.md.
- **Spec:** `work/saver/SAVER_SPEC.md`, about 20 Sonnet hours in total.
- **Status:**
  - Part 1 is built: `saver_diff.py` and the preview path. The replay of the 2026-10-30 save matches cell for cell. The replay fixture (in.xlsx, the staged result, db/) is not in this repo because it contains the workbook.
  - Fable's review (`work/saver/REVIEW_1.md`, failing tests in `work/saver/tests/review/`) said fix first. Five gaps were found: hyperlink targets, identity checks on new rows of the A&V and Removed tabs, removed_move on pre-existing rows, links on moved and header rows, and a lock-takeover race. A Sonnet fix was in progress at handoff; check the latest commit.
- **Next steps:**
  1. Finish the fixes so all review tests pass.
  2. Build `save`, the write path.
  3. Replay more past saves.
  4. Fable reviews the whole program.
  5. First supervised live save.
- **Known bug from the 2026-10-30 manual save:** article shards were copied into `copies/articles/articles/`, nested one level too deep, so relmatch read stale shards. Two `release_related.json` entries are `bill` where they should be `text`. The next save fixes them.

## Open decisions for Sammy (don't assume answers)

- **Where the master workbook and library should live.** GitHub is recommended. Google Drive can't carry the workbook: its connector passes files through the conversation as base64 and can't replace a file's contents. A private artifact is the fallback. The office PC can open claude.ai, and IT probably won't allow local installs, so the plan is browser-only.
- **From earlier work:**
  - weekly watch plus a monthly sweep;
  - A5 wire-blend pickups;
  - 4 unsettled F7 rows (09721, 01734, 06948, 06949);
  - 8 medium-confidence date fixes;
  - whether to add full versions of 4 thin saved copies;
  - Patch rows 00740 and 04889;
  - Korea Daily Times;
  - the 7 existing NOBLOGS rows, to be listed before any removal;
  - the Independent story's date (blank; GDELT saw it 2026-09-30);
  - blank Tone/Topic on Newsroom America and Organiser.

## Working conventions

- Run Python with `-I`. Tests: `bash build/tests/run_all.sh`; saver tests: `cd work/saver && python3 -I -m pytest tests -q`.
- Building the tracker:
  1. `python3 -I code/apply_all_patches.py`;
  2. `bash build/build.sh`;
  3. publish `index.html` plus changed files. Pipeline `.py`/`.js`/`.html` files are published with contentType text/plain.

  The published tracker is near its 256 MB per-version cap; publish batches stay under 64 MB.
- Commit messages end with the attribution lines the session provides.
