# AJG Press Tracker: instructions for Claude

Press-coverage database for CA Assemblymember Jesse Gabriel (AD-46), kept by Sammy (ssaslow@berkeley.edu). It catches every real story about Gabriel the Assemblymember and nothing else: print, online, TV, radio, podcasts and non-English outlets. Reprints are grouped under the story that ran first. Sammy prefers lean, precise prose and plain words; he is not a programmer (basic level: high-school AP Computer Science). Explain technical ideas in everyday terms and define any jargon.

## Where things live

**In this repository:**
- `docs/`: START_HERE, HANDOFF (operations), DECISIONS (the decision log; tags like `NOSCHED-v1`; newest at the end), CONTRACT (run-doc schema), AGENT_BRIEF, BOARD, TONE_GUIDE. Search DECISIONS by tag; don't read it whole.
- `code/`: tracker page sources (`code/tracker/NN_*.js`), the save pipeline (`sheet_task.py` plus rule modules), reference data (`outlets.json`, `reporters.json`, `reporter_employment.csv`, `outlet_rules.json`, `lookup_cache.json`), `make_viewer.py` (shared copy), and `sheet_task_prompt.md` (today's manual save procedure).
- `build/`: build scripts (`apply_all_patches.py`, `build.sh`), tab sources (`build/tabs/`) and tests (`build/tests/run_all.sh`, about 5 min; TABS harness in `build/tests/tabs/`).
- `work/saver/`: the save program in progress (see Current work).
- `work/desktop_plan/`: Fable's Windows plan (PLAN.md, BUILD_NOTES.md). The closest existing plan for LOCALAPP-v1 (portable zip, embeddable Python, local page in the browser). Its Claude Desktop connector for saves does not fit LOCALAPP-v1.
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
  - Fable's review (`work/saver/REVIEW_1.md`) findings are fixed; all 25 tests in `work/saver/tests/review/` pass.
  - Part 2 is built (2026-10-31): `save` (backup, checked swap, pages add-only, removals moved to `_to_delete/`, ledger, keep 3 saver backups, rebuild). 95 saver tests pass. See `work/saver/README.md`.
  - Not yet run: a replay against a real past save (the fixture is not in this repo), and the rebuild against the real published pipeline (only stubs so far; use `--no-rebuild` until it has run once).
  - Hold lifted (Sammy, 2026-11-02): the saver is the save engine of the local app (LOCALAPP-v1); work on everything is go.
- **Next steps:**
  1. Replay more past saves.
  2. Fable reviews the whole program.
  3. First supervised live save.
- **Known bug from the 2026-10-30 manual save:** article shards were copied into `copies/articles/articles/`, nested one level too deep, so relmatch read stale shards. Two `release_related.json` entries are `bill` where they should be `text`. The next save fixes them.

## Build decisions (Sammy, 2026-10-31, NEWPROJECT-v1)

1. **This repository is an entirely new project.** It must not change anything about the artifact-based tracker: the live tracker, the shared copy, their databases, the Mac master or the library. The old tracker keeps running exactly as now, and its saves keep going to the Mac master until Sammy decides to switch over.
   - The workbook and library move into this repository as a **snapshot copy** for building and testing.
   - At switch-over, the snapshot is replaced with the then-current Mac master and library, with every file's checksum verified. Until then the copy here is not a master and is never written back anywhere.
2. **Hand edits:** Sammy downloads the workbook, edits it in Excel and uploads it back; the save program accepts it as the new baseline (SAVE_RULES answer 2).
3. **No Update button in the new app yet.** During the build, new stories still come only from the old tracker. The new project's save program is built and tested on the snapshot; there are no live saves in the new project until switch-over.
4. **Autonomy** (Sammy: "do what you think is best"):
   - Commit and push code freely.
   - Build and test only on copies.
   - Never publish or modify the old tracker's artifacts or databases.
   - A new artifact for the new tracker may be created, private, for testing.
   - Never write the Mac master or library.
   - The first real save and the switch-over need Sammy present.
   - Fable: the three checkpoints plus at most one more, for an unexplained replay mismatch.
5. **The 256 MB artifact cap** (Sammy: "do what you think is best"): keep the current tracker's design for now, with saved copies in per-year files. Revisit only if the new tracker gets near the cap. A browser page can't read a private GitHub repo without credentials, so the copies can't simply be loaded from here.
6. **Look and feel** (SAMELOOK-v1): the new tracker looks and feels the same as the current one, minus the Update button functionality. Leaving out the Update button is temporary; it comes back later.
7. **Local software** (LOCALAPP-v1): the new project turns the existing tracker into self-contained software that runs locally. Its only outside connections, later, are Claude and TinyFish, and only for the Update button. Target: the office Windows PC, with nothing installed (portable folder only).
8. **Update folder** (UPDATEFOLDER-v1): Claude does the searching and saving work and hands Sammy an update folder; he drags it into the local program, which integrates it into the tracker. The program itself does not go online. The PC program writes the workbook (all saver checks, workbook never leaves the PC); a program button makes a "for Update" list of stories already in the tracker (no article text) that Sammy loads into the Update station.
9. **Update station** (UPDATESTATION-v1): a new, separate claude.ai artifact holds only the Update button, working exactly as today, and produces the update folder for the PC tracker. Each use starts by uploading the "for Update" file from the PC; duplicate checks and the reprint logic work from that file, which carries story details only, no article text (the text-based reprint test runs at save time on the PC); read in the browser, not stored in the artifact. Tone rating, author splitting and translation also happen in the Update station.
10. **Switch-over** (SWITCHOVER-v1): when ready and tested (end-to-end test, Fable review, one supervised real save). The PC tracker starts fresh (no old notes, views or edit history). The review queue moves into the PC tracker. Plan: `work/localapp/PLAN.md`.
11. **Government computer** (GOVIT-v1): strict IT. On the PC: no installs, admin, registry, services or network connections; 127.0.0.1 only; files only in the app folder; signed official Python and hash-pinned packages; readable source. Get IT's OK first (`work/localapp/IT_NOTE.md`).
12. **Several PCs** (MULTIPC-v1): one tracker folder on a shared network drive; several PCs and several people save. The lock and ledger keep saves one at a time; notes and views live in the shared folder.

## Open decisions for Sammy (don't assume answers)

- **An online read-only copy for colleagues** after switch-over (SWITCHOVER-v1: decide later).
- **How new stories reach the new project after switch-over,** until it has its own Update button.
- The office PC runs the unzipped test folder (2026-11-02: it works).
- **From earlier work:**
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
