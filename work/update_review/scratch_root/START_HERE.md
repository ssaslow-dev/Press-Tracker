# START HERE: AJG Press Coverage Tracker (one page)

Read this, then HANDOFF.md section 0.3 (the runbook). Where any doc disagrees with DECISIONS.md, DECISIONS.md wins.

## What it is
A press-coverage database and web tracker for California Assemblymember Jesse Gabriel (AD46). Owner: Sammy (ssaslow@berkeley.edu). Three parts that must always agree: the **master workbook**, the **tracker page** built from it, and the **Update button** that finds new coverage and writes it back through a scheduled "sheet task".

## Where things are
- **Master workbook (source of truth):** Sammy's Mac, `~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx`. Working copy in the kit: `source/work/coverage_current.xlsx` (its sha is in the facts block below; compare with the Mac before any write). Saved pages, raw pages and backups: `~/Desktop/Tracker library/` (`<year>/`, `_original_html/`, `Backups/`).
- **Live tracker (old account):** https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv ("AJG Press Coverage Tracker"). Artifacts cannot move between accounts: a new account publishes its own copy from this kit (new URL).
- **Shared viewer copy (read-only, no Update button):** https://claude.ai/artifact/6vhKKcNXarhSKwnCMk3Bks ("AJG Press Coverage Tracker (Shared)"). Built by `code/make_viewer.py`; how to rebuild it, and the server-side copy step for a new account: HANDOFF 4.4a.
- **Review queue artifact:** https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB (collections items, decisions, applied).
- **Code and docs:** `source/` = the library L. Rules: DECISIONS.md. Formats: CONTRACT.md. Protocol: README.md. Detail: HANDOFF.md. Build: `bash build/build.sh`. Tests: `bash build/tests/run_all.sh`.

## How Update works (and what is switched off)
1. Sammy presses **Update database** in the tracker. The page searches the web with TinyFish, checks for new press releases, and saves the finds as a run document in the artifact database.
2. The page then fires the scheduled **sheet task** (`fire_trigger`, Claude Code Remote). The task reads `pipeline/sheet_task_prompt.md` from the tracker, runs `sheet_task.py` (reprint rule, IDs, fills, verification), writes the workbook on Sammy's Mac, saves pages to the library, rebuilds and republishes the tracker.
3. **The scheduled task is DISABLED.** It stays off until Sammy approves its prompt (`source/work/tmp_agent-buttonopt2/scheduled_prompt.md`, final instructions in `pipeline/sheet_task_prompt.md`) and one supervised run passes (HANDOFF 8.1 D3). Until then, pressing Update finds and queues rows, but nothing reaches the workbook and release pickups never run live. A successor must create the task disabled and ask Sammy before enabling it.
4. Rehearsal without the Mac: `build/tests/sheet_task/fixtures/example_db.json` is a worked input (CONTRACT "Proposed rows").

## Never do
- Go to the web first. Reference data first (LEARN-v1): check `outlets.json`, `reporters.json` / `reporter_employment.csv`, `outlet_rules.json` and `lookup_cache.json` before any fetch or search; web only for something genuinely new; save confirmed answers back.
- Write the master workbook without the writer token (`work/WORKBOOK_WRITER.txt` must read "none"), Excel closed, a backup committed first, a new unique file name (never the master's own name), fill-blanks-only, sha verified on the Mac (README rule 7, HANDOFF 6.1).
- Publish except through the coordinator or the agent it dispatched (README rule 1), publish anywhere but the live tracker, or publish a preview he did not ask for. Publishes go page last.
- Delete anything: the library and L are add-only. Move to `_to_delete/` or `archive/<date>/` with a log.
- Use Exa (forbidden). Web fetch/search is TinyFish only; never use deep research ($2 a run).
- Work around paywalls or blocks, log in for Sammy, or enter credentials. Mark the row `BLOCKED – TinyFish` and move on.
- Count Gabriel's own channels or release services/aggregators as coverage or as the Original (OWNED-v1).
- Change an existing cell value unless DECISIONS says so; decide for Sammy anything not in DECISIONS (ask in short labels).
- Fix a symptom only: fix the whole class, and apply every change to all three: code (apply_all), the Update button/pipeline, the master sheet.
- Edit `build/js_merged.js` by hand (edit `code/tracker/NN_*.js`, run `python3 code/apply_all_patches.py`).
- Assign IDs by hand (sheet_task.py does), reuse a Removed or Print Article ID, or date a story by save/updated time (DATES-v1).
- Overstate: say what was checked and what was not.

## Open items
- Sammy to approve the sheet-task prompt and a supervised run (D3, above).
- Storage: the img repack is live (shards img/0-13; 203.1 MB of 256 MB). After any make_copies run, repack again with `python3 -I code/repack_img.py` (HANDOFF 4.4a) before publishing.
- After the new account publishes: swap the trigger id and tracker URL (HANDOFF 0.4), re-seed the databases (0.5), recreate the review queue.
- Decisions waiting on Sammy: HANDOFF 8.1 (D1-D12), e.g. wire-blend pickups A5; 09721, 01734, 06948, 06949; 8 medium date fixes (work/out/web_dates_2026-10-30.csv); 04889; Korea Daily Times home city; 19 blank reaches; stray empty file 'Tracker library/.probe_w'; TinyFish needs re-authorizing.

## Where to go next
1. HANDOFF.md **0.3** (runbook: publish once, create the task disabled, swap ids, apply_all + build, republish page and pipeline), then 0.4 (ids that change) and 0.5 (database carry-over).
2. KIT_README.md (next to the zips): unzip, verify, republish batches. Publish `publish/articles/*` as shipped; do not substitute rebuilt copies.
3. HANDOFF 1 (working with Sammy), 3 (data rules), 4 (code and build), 5 (Update end to end), 8 (open items).

## Facts (generated; do not edit)
<!-- FACTS:BEGIN (generated by code/make_handoff_kit.py facts --write; do not edit by hand) -->
Generated 2026-10-30T19:20:22Z. Re-run `python3 -I code/make_handoff_kit.py facts --write` (or `build`) instead of editing these numbers.

- Live tracker version 1793387365-be18 (runtime contract 0.2.91), page sha256 `5c9a096b24031149a40b8f48578d51781b2d1d66d0991d776cb633c1f9f215f8`; 153 published files, 203.1 MB of the 256 MB per-version cap (52.9 MB free; the 511-file cap leaves 358 files). Recorded 2026-10-30T19:12:11Z; anything published since is not in this kit.
- Master workbook copy work/coverage_current.xlsx: sha256 `bd2d84ea36ea1600ca12a756f9eacdccf99e36390888b536b563df9a7d9ab04e` (must equal the Mac master; compare before any write). Rows: Coverage 8,169, Originals 4,082, Bills 1,895, Press releases 244, Audio & video details 1,022, Removed 328, Unlinked print pages 1,443.
- Highest IDs in the workbook: Article ID 10641, Story ID s04922, Release ID pr00244. Next free is one above, but never assign by hand: sheet_task.py assigns IDs (it also skips reserved blocks and every ID in Removed / Print Article ID).
- Workbook writer token (work/WORKBOOK_WRITER.txt): "none".
- Unit suites: 42 in build/tests/run_all.sh (3 of them skip with a notice when their inputs are not in the kit). The TABS harness is separate.
<!-- FACTS:END -->
