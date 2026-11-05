# AJG Press Tracker: instructions for Claude

Press-coverage database for CA Assemblymember Jesse Gabriel (AD-46), kept by Sammy (ssaslow@berkeley.edu). It catches every real story about Gabriel the Assemblymember and nothing else: print, online, TV, radio, podcasts and non-English outlets. Reprints are grouped under the story that ran first. Sammy prefers lean, precise prose and plain words; he is not a programmer (basic level: high-school AP Computer Science). Explain technical ideas in everyday terms and define any jargon.

## Where things live

**In this repository:**
- `docs/`: START_HERE, HANDOFF (operations), HANDOFF_PC_APP (2026-11-02 handoff from the Claude that ran the old tracker: rules, quirks and lessons for the PC app and Update station; read sections 1, 6 and 10 before working on them), DECISIONS (the decision log; tags like `NOSCHED-v1`; newest at the end; superseded entries are in DECISIONS_ARCHIVE, with a pointer left behind), CONTRACT (run-doc schema), AGENT_BRIEF, BOARD, TONE_GUIDE. Search DECISIONS by tag; don't read it whole.
- `code/`: tracker page sources (`code/tracker/NN_*.js`), the save pipeline (`sheet_task.py` plus rule modules), reference data (`outlets.json`, `reporters.json`, `reporter_employment.csv`, `outlet_rules.json`, `lookup_cache.json`), `make_viewer.py` (shared copy), and `sheet_task_prompt.md` (today's manual save procedure).
- `build/`: build scripts (`apply_all_patches.py`, `build.sh`), tab sources (`build/tabs/`) and tests (`build/tests/run_all.sh`, about 5 min; TABS harness in `build/tests/tabs/`).
- `work/saver/`: the save program (see Current work).
- `work/update_review/`: the Update-button review (REPORT.md, FABLE_DIFF_REVIEW.md, REPLAY.md); the patches it made were applied to `code/` long ago.

Docs written before the move refer to the old workspace root `L = /tmp/.../scratchpad/lib`. In this repository, that root is the repo itself (`L/code` = `code/`, `L/DECISIONS.md` = `docs/DECISIONS.md`).

**Not in this repository:**
- Master workbook: `~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx` on Sammy's Mac. It is the single source of truth. Current sha256 starts `0bccc1fc` (2026-11-03, after LANGADD: docs/CHANGES_2026-11-03.md; before that `62786489`, docs/CHANGES_2026-11-02.md). The repo snapshot in `data/` is still `bc21c9fb` (2026-10-30), 6 writes behind; it is replaced at switch-over.
- Article library: `~/Desktop/Tracker library/<year>/`, `_original_html/<year>/`, `Press releases/<year>/`, and `Backups/`, all on the Mac. It is add-only.
- Live tracker (claude.ai artifact): https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv, also at https://claude.ai/code/artifact/27f923dc-2407-40a0-b8a9-ec3dfed87ad9. Its database holds runs, pages, edits and similar. Capabilities: db, downloads, sample, and mcp TinyFish (search, fetch_content).
- Shared read-only copy: https://claude.ai/artifact/6vhKKcNXarhSKwnCMk3Bks. Rebuild it with `code/make_viewer.py` after every tracker publish.
- Review queue artifact: https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB.
- claude.ai Project "AJG Mentions Database" holds copies of the docs under `library/`.
- **New project's Update station** (private, UPDATESTATION-v1): https://claude.ai/artifact/5uGsM8yQMphjAQbKhvc5SL. Source and build: `work/localapp/station/`.
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

## Current work: the new tracker (status 2026-11-04)

Plan: `work/localapp/PLAN.md`. Everything left, with owner and status: `work/localapp/FINISH_LIST.md` (FINISH-v1; keep it current after every step). Three parts, all built and tested on copies (no real saves yet):
- **PC tracker** (`work/localapp/app/`, assembled by `assemble_app.py`): portable Windows folder (NuGet CPython 3.13.16 + 10 hash-pinned wheels, `work/localapp/winpack/`), local server on 127.0.0.1:8765 (`work/localapp/server/`), the tracker page with the Update/tone/author/translation buttons hidden, a "Tracker files" panel (Make "for Update" file, Bring in update, Accept the workbook, refresh files for readers), keeper/reader roles. Pipeline patches 01-14 applied to a copy at assembly (winpack, photolink, local fonts, NewsBank/ProQuest saving). Look check (`work/localapp/lookcheck/`) clean against live v65 on the routes the latest code touched; last full clean run against v63-era files. Parity test (`work/localapp/paritytest/`, PARITYTEST-v1): the live v65 files against the PC build on the same workbook, 19 interactions plus the PC's own additions (one save so "Last updated" shows, one print original so "View original" shows, one opened linked-photo copy), light and dark keeper copies and a reader copy; a guard fails the run if the page patches change the reference page beyond a reviewed set (`ref_patch_diff.json`); independent audit in `ALLOWED_AUDIT.md`; 0 differences (2026-11-04). Switch-over screen (SWITCHOVER-v1) also carries RENAME-v1 (library names brought up to NAMING-v2) and DATAFIX-v1 (approved data-check fixes, row-changing fixes, 01920 and 03486 listed "for you to decide"); all built and tested on copies, none applied.
- **Update station** (`work/localapp/station/`): private artifact (URL above), published version 1793907302-9424 (2026-11-05 evening: searches from the day before the newest story with no date to pick, tracker-duplicate / junk / old-find clean-up, full English translations, plain page, Fable-reviewed: work/localapp/station/REVIEW_STREAMLINE.md; before that 1793889653-19e6: captions stay with their story, clean print bylines; earlier: print-read fixes, clean interface, full-size page pieces, no recovery, download only on the button): the live tracker's own Update code (v65), "Add NewsBank PDFs" and "Add ProQuest PDFs" boxes, names files by NAMING-v2, needs the for-Update file first. Never tested with a real TinyFish run yet (needs Sammy). Move to the office account: work/localapp/station/MOVE_TO_OFFICE.md.
- **Save engine** (`work/saver/`): `saver.py preview|save` with all refusal checks; rules in `SAVE_RULES.md` (SAVER-RULES-v1); learns YTSTATION/YTBROADCAST/YTLINK. Formats between the parts: `work/localapp/updatefolder/FORMAT.md`.

Next steps:
1. Sammy tests the PC tracker zip and one real Update run (station -> folder -> PC preview).
2. Fable checkpoint 3 done (work/saver/REVIEW_2.md); findings fixed. PCEDITS-v1 built (Manage edits saved with updates or via "Save my edits").
3. Station final checks after Sammy's additions; publish it on the office claude.ai account.
4. Switch-over with Sammy (SWITCHOVER-v1): replace the snapshot with the current Mac master and library, then the Switch-over changes screen (file renames, PRJUDGE-v2, data-check fixes), first real save, full refresh files for readers.
5. PC tracker version 4.1 (2026-11-05: version 4 plus the installer fixes, ORIGLINKS-v1 and OWNCREDIT-v1; zip fingerprints in FINISH_LIST) is the current build. The office PC runs it from `Desktop\AJG_v4\AJG Tracker` (installed by hand; the old folder is a backup).

Importing the old workspace's change bundles: docs/CHANGES_*.md. Copy code/ and build/ files as they come, keep the repo-only changes listed in docs/REPO_LOCAL_CHANGES.md, place new DECISIONS entries before the marker line, never commit bundle workbooks (SWITCHOVER-v1 follow-up), then rebuild js_merged.js, re-apply PC patches, rebuild and republish the station.

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
6. **Look and feel** (SAMELOOK-v1, tightened by SAMELOOK-v2): the new tracker keeps the old one's functionality, look and feel exactly, down to font sizes, minus the recorded exceptions (hidden Update/tone/author/translation buttons, the Tracker files panel, linked photos). Checked by an automated side-by-side comparison with the live tracker's files. Leaving out the Update button is temporary; it comes back later.
7. **Local software** (LOCALAPP-v1): the new project turns the existing tracker into self-contained software that runs locally. Its only outside connections, later, are Claude and TinyFish, and only for the Update button. Target: the office Windows PC, with nothing installed (portable folder only).
8. **Update folder** (UPDATEFOLDER-v1): Claude does the searching and saving work and hands Sammy an update folder; he drags it into the local program, which integrates it into the tracker. The program itself does not go online. The PC program writes the workbook (all saver checks, workbook never leaves the PC); a program button makes a "for Update" list of stories already in the tracker (no article text) that Sammy loads into the Update station.
9. **Update station** (UPDATESTATION-v1): a new, separate claude.ai artifact holds only the Update button, working exactly as today, and produces the update folder for the PC tracker. Each use starts by uploading the "for Update" file from the PC; duplicate checks and the reprint logic work from that file, which carries story details only, no article text (the text-based reprint test runs at save time on the PC); read in the browser, not stored in the artifact. Tone rating, author splitting and translation also happen in the Update station.
10. **Switch-over** (SWITCHOVER-v1): when ready and tested (end-to-end test, Fable review, one supervised real save). The PC tracker starts fresh (no old notes, views or edit history). No review queue and no wanted-originals lookups (NOQUEUE-v1). Plan: `work/localapp/PLAN.md`.
11. **Government computer** (GOVIT-v1): strict IT. On the PC: no installs, admin, registry, services or network connections; 127.0.0.1 only; files only in the app folder; signed official Python and hash-pinned packages; readable source. Get IT's OK first (`work/localapp/IT_NOTE.md`).
12. **Several PCs** (MULTIPC-v2, replaces v1): each person keeps a local copy (running from the shared drive failed). One keeper saves; the keeper's tracker makes a "refresh file" the others drag in to match. Notes and views stay personal. Reader copies hide the save buttons.
13. **Photos** (PHOTOLINK-v1): new saved copies link to the news sites' photos (Edge loads them when a copy is opened); existing copies keep embedded photos. The one exception to "the PC never goes online"; IT's note says so.
14. **Library files** (LIBFILES-v1): everything brought in lands in the keeper's PC library in the existing layout (`<year>/` by story date; `_original_html/<year>/`, `_original_pdf/<year>/`, `Press releases/<year>/`), add-only; readers get them via refresh files.

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
