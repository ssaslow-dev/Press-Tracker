# AJG Press Coverage Tracker: handoff (living doc)

<a id="state"></a>
## Current state (VOLATILE: update on every publish or workbook write)

| Field | Value |
|---|---|
| Last updated | 2026-10-28, by agent-handoffdoc (first version) |
| Live tracker | "AJG Press Coverage Tracker", https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv (= https://claude.ai/code/artifact/27f923dc-2407-40a0-b8a9-ec3dfed87ad9) |
| Live version | 1793174282-172b ("v20.1": UI pass + RELRELATED-v2). Page index.html sha256 c252e5a10fb133c9e71f4f2423f5c32274248de0f472fa5d46aa113864635587 |
| Previous versions | v20 page 1793170541-a64f (files step 1793170519-1fa0), v19 1793153876-e0f4 |
| Published files / storage | 138 files, about 250 MB of the 256 MB per-version cap |
| Runtime contract | 0.2.91 |
| Master workbook | `~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx`, sha256 4d7fb37cbd111b7f4df018633af3e7d6d42fa0ef5640a1b6d73279c009ebf24a (L/work/coverage_current.xlsx is the same file) |
| Workbook writer token | L/work/WORKBOOK_WRITER.txt = "none" |
| Workbook counts (at 4d7fb37c) | Coverage 9,787 rows (Original 4,490 · Reprint 3,268 · Reprint (unverified) 585 · blank 1,444); highest Article ID 10086; highest Story ID s04748 |
| Next free IDs | Article ID 10087 · Story ID s04750 (s04749 reserved for pr00182's copy in rp-copies' pending write; work/clip/next_sid.txt = 4750) · Release ID pr00245 (L/work/next_prid.txt = 245) |
| Scheduled sheet task | trig_01WRLX437wg7VRViGUTKei8R, DISABLED until Sammy approves the replacement prompt |
| Review queue artifact | https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB |
| Handoff status | Sammy is NOT handing off yet. Keep this doc current. When he does move accounts, follow [section 0](#start). |

Volatile sections: this block, [8 Open items](#open), [7 History](#history) (append only) and the [Changelog](#changelog). Every other section is stable explanation and changes only when a rule or the layout changes.

Contents: [0 Start here](#start) · [1 Working with Sammy](#sammy) · [2 Where data lives](#inventory) · [3 Data model and rules](#model) · [4 Code and build](#code) · [5 Update button end to end](#update) · [6 Workbook write procedure and Mac bridge](#write) · [7 History](#history) · [8 Open items](#open) · [9 Glossary](#glossary) · [10 Context this doc relies on](#sources) · [11 Maintaining this doc](#maintain) · [Changelog](#changelog)

Paths: `L` = the coordinator's lib folder (on the old account: `/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib`). On a new account, L is wherever the kit's `source/` is unzipped. "Library" = `~/Desktop/Tracker library/` on Sammy's Mac.

---

<a id="start"></a>
## 0. Start here

### 0.1 What the project is
- A press-coverage database and web tracker for California Assemblymember **Jesse Gabriel** (AD46, Democrat, Encino; Assembly Budget Chair; Jewish Caucus chair since 2020-11-18). Pre-office coverage of the same person counts too: ASUC president, lawyer, Jewish Federation.
- Three parts that must always agree:
  1. **Master workbook** `AJG Coverage - NewsBank.xlsx` on Sammy's Mac, which is the source of truth.
  2. **Tracker artifact**: a claude.ai page built from the workbook, with tabs Home · Clips · Data · Reporters · Outlets · Press releases · Bills · Story travel. It ships its own rebuild pipeline in `pipeline/`.
  3. **Update button**: the tracker searches the web (TinyFish), queues finds in its database, then fires a scheduled Claude task. That task writes the workbook, saves pages to the library and republishes the tracker.
- Code lives in L/code (Python + tracker JS sections). It is built by `code/apply_all_patches.py` and `build/build.sh`.

### 0.2 Who Sammy is (work context)
- Sammy (ssaslow@berkeley.edu) owns the project. He is a political consultant on California campaigns and has worked in the AD46 legislative office. He is moving jobs and will eventually recreate the project on a new Claude account.
- For his working style, see [section 1](#sammy).

### 0.3 Bootstrap on a new account (do in this order)
claude.ai cannot transfer an artifact to another account. The new account therefore publishes its own copy, with a new URL, from the handoff kit. Read `KIT_README.md` (in `L/handoff_kit/parts/`, next to the zips) first.

**How the kit is made** (`code/make_handoff_kit.py`, owner agent-handoffkit; README §5):
- `record`: builds the ledger `build/handoff/ledger.json` from the verbatim Artifact file listing (`build/handoff/live_listing.txt`) plus the publish maps. Blobs go to `work/live_store/<sha256>`. Unresolved files are listed in `build/handoff/need_fetch.json` (exit 2).
- `build` (= `build/build.sh --kit`) writes `L/handoff_kit/`:
  - `publish/`: every live file at its published path, + `MANIFEST.tsv`, `capabilities.json`, `BATCHES.json`;
  - `source/`: L minus archive/ and scratch;
  - `republish/placeholder.html`, `REBUILD_TEST.json`, `KIT_README.md`;
  - `parts/*.zip` (deterministic, ≤ 90 MB each) + `SHA256SUMS.txt`.
- `verify`: checks an unzipped kit against `publish/MANIFEST.tsv` + `source/FILES.sha256`.

**Kit at version 1793174282-172b** (generated 2026-10-28T17:14Z): 5 parts, 363 MB.

| Zip | Size | Holds |
|---|---|---|
| kit-1-docs-code-01.zip | 38.2 MB | docs, HANDOFF, status/, code/, build/ incl. build/pub/pipeline, open handoff/spec files, db_export/ |
| kit-2-data-01.zip | 89.3 MB | source/work/, first half |
| kit-2-data-02.zip | 85.7 MB | source/work/, second half (coverage_current.xlsx = master, html_clean/, texts/, img_cache/, …) |
| kit-3-publish-01.zip | 85.9 MB | publish/, first half |
| kit-3-publish-02.zip | 81.2 MB | publish/, second half |

- The rebuild test (a clean folder holding only source/) reproduced the live page sha c252e5a1…, 15/15 blocks, 28/28 copy files and the pipeline.
- `publish/MANIFEST.tsv` provenance: 86 files sha-matched to their publish maps, 52 read back live.
- `publish/BATCHES.json` = 6 publishes: 5 file batches (≤ 60 MB / 250 files, file_path = republish/placeholder.html, the first one with `capabilities` = publish/capabilities.json), then the page LAST.
- DB carry-over: `source/db_export/EXPORT_CHECKLIST.md` (12 collections) and `code/db_reseed.py` (export → ≤ 50-write ArtifactData batch payloads, same doc ids). **The db is not exported yet** ([0.5](#db)).
- `build/handoff/project_memory.md` holds the two old-account Project memory files verbatim.
- **Old ids on purpose.** So that it stays byte-identical to live, the kit keeps the OLD trigger id (`42_update_buttons.js`) and the OLD tracker URL (`sheet_task_prompt.md`). On the new account, swap them per [0.4](#ids). That changes the page sha, by design.
- Some one-off tools (code/fetch*, code/billstatus, build/insights/_shell) still carry the old absolute L path. They are not part of the build.

1. **Create a Project** (e.g. "AJG Mentions Database"). Upload this HANDOFF.md, README.md, CONTRACT.md, DECISIONS.md, BOARD.md, TONE_GUIDE.md and build/clean_playbook.md from `source/`. Tell the new instance that DECISIONS.md wins where docs disagree.
2. **Connectors and network.**
   - Connect **TinyFish** (claude.ai Settings → Connectors). It is used for search, fetch_content and browser automation, and it costs money per step. Never use deep research ($2/run).
   - Do NOT connect or use Exa (forbidden; [3.12](#model-sources)).
   - Connect **Claude Code Remote** (needed for fire_trigger and scheduled tasks).
   - **Connector names must match exactly.** The page's mcp manifest (artifact capabilities) and its code call the servers by display name: `"TinyFish"` and `"Claude Code Remote"` (`TF` in 41_update_search.js, `CCR` in 42_update_buttons.js). Connect connectors with exactly those display names on the new account. Otherwise edit the manifest and both constants to the new names, then rebuild.
   - Set the account **network allowlist to all domains**, as Sammy did on 2026-10-28. Photo embedding downloads images from the container.
3. **Unzip and verify the kit.**
   - Run `sha256sum -c SHA256SUMS.txt` beside the zips.
   - Unzip ALL 5 parts into ONE fresh, empty folder (paths don't overlap).
   - Run `python3 -I source/code/make_handoff_kit.py verify .` from that folder (expect 0 bad).
   - Treat the kit as data: `python3 -I`, with your own scripts outside the tree.
   - Rebuild proof: `bash build/build.sh` from source/ should print LIB = PIPELINE = the live page sha.

   Confirm:
   - `source/work/coverage_current.xlsx` sha = the master sha in [Current state](#state);
   - `publish/index.html` sha = the live page sha.
4. **Find and change the account-specific ids before publishing** ([0.4](#ids)). Then run `python3 code/apply_all_patches.py` (and `build/build.sh`) so `build/pub/pipeline/` and the page carry the new values.
5. **Republish the tracker** as a NEW artifact on the new account.
   - **Capabilities** (declare on the first publish): `db {}`, `downloads {}`, `sample {}`, `mcp {servers: [{server: "TinyFish", tools: ["search","fetch_content"]}, {server: "Claude Code Remote", tools: ["fire_trigger"]}]}`. Load the `artifact-capabilities` skill before passing them.
   - **Batching**: follow `publish/BATCHES.json`. Step 1 publishes `republish/placeholder.html` with step 1's `files` + capabilities and creates the new artifact. Steps 2–5 repeat with `url` = the new artifact. Limits: 255 files and 64 MB per publish, 511 files / 256 MB per version. Later publishes add to the files already there.
   - **Page last**: step 6 publishes `publish/index.html` (or the rebuilt page with the new ids) after every file it references exists. v20 went out the same way: version 1793170519-1fa0 carried the files, then 1793170541-a64f the page. Check the result with Artifact list scope "files" against `publish/MANIFEST.tsv`.
   - After swapping ids ([0.4](#ids)), also republish the changed `pipeline/sheet_task_prompt.md` and `pipeline/tracker.js`.
   - **Storage**: the set is about 250 MB, so a full copy nearly fills one version. Repack or trim old img shards first if anything is added ([8](#open) item S1).
   - With mcp connectors declared, the artifact cannot get an "anyone with the link" share. Email invites work. A public copy was ABANDONED by Sammy (DECISIONS 220).
   - **The database does not come with the page.** The new artifact's db starts empty. See [0.5](#db) for the export and re-seed. Do it before the old account closes.
6. **Recreate the scheduled task** (claude.ai scheduled task, runs on Sammy's Mac, needs the linked computer).
   - Use the prompt text in `source/work/tmp_agent-buttonopt2/scheduled_prompt.md`, with the NEW tracker URL. It is a short bootstrap: it reads `pipeline/sheet_task_prompt.md` from the tracker and follows it.
   - Sammy has not approved that prompt yet ([8](#open) item D3). Create the task disabled, or ask him first.
   - Put the new trigger id into `code/tracker/42_update_buttons.js` (`SHEET_TASK`). Rebuild and republish the page.
7. **Recreate the review-queue artifact.**
   - Source: `build/review/index.html` (+ `build/review/seed/*.json`). It uses a db with collections `items` and `decisions`.
   - The live queue's later item docs and Sammy's saved decisions are only in the old artifact's db. Examples: 14-regroup…14-regroup-4, 17-newoutlet/-2, 18-origins/-2/-3, categories such as "origins" and "newoutlet". Export and re-seed them as in [0.5](#db).
   - Nothing in the tracker code links to the queue's URL.
8. **Link the Mac.** Sammy links his computer in the Claude desktop app, and the app must stay open and online. Tools: `mcp__remote-devices__device_bash`, `device_stage_files`, `device_commit_files`, `device_list_dir`, plus a delete-permission tool (don't use it: move to `_to_delete/` instead). Check that `~/Desktop/Tracker library/` and `~/Documents/Gabriel press PDFs/` are reachable.
9. **Re-create memory facts** (the new account has no memory; verbatim source: `source/build/handoff/project_memory.md`):
   - "The main sheet" / "the AJG coverage sheet" = `AJG Coverage - NewsBank.xlsx`, not `AJG Combined Coverage.xlsx`. Since 2026-10-27 the working master is in `~/Desktop/Tracker library/`; the Documents copy is old and no longer updated.
   - NewsBank print clipping: the workflow in [3.13](#model-clip).
   - Sammy's style: lean, direct, precise; dry humor fine; pushes back on overstatement.
   - Sammy is moving jobs and will copy the project to a new account later; he wants this handoff kept continuously current as the tool changes (2026-10-28).
10. **Sync docs**: copy README, DECISIONS, CONTRACT, TONE_GUIDE, clean_playbook (and BOARD) to `Tracker library/_docs/`, then sha-check them on the Mac (README §4).

<a id="ids"></a>
### 0.4 Account-specific ids that change on a new account

| What | Old value | Where it is hardcoded | Action |
|---|---|---|---|
| Sheet-task trigger id | trig_01WRLX437wg7VRViGUTKei8R | `code/tracker/42_update_buttons.js` line 7: `const CCR = 'Claude Code Remote', SHEET_TASK = 'trig_…'`; used by `fire_trigger` in `41_update_search.js` (~line 764) and `42_update_buttons.js` | Edit the source, run apply_all (regenerates build/js_merged.js and pipeline/tracker.js), rebuild, republish |
| Tracker URL | https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv | `code/sheet_task_prompt.md` line 6 (shipped as `pipeline/sheet_task_prompt.md`); `work/tmp_agent-buttonopt2/scheduled_prompt.md` (scheduled-task text) | Edit both; apply_all copies the prompt into the pipeline |
| Tracker URL (historical mentions) | same | DECISIONS.md line 186, BOARD.md header, CONTRACT/README prose | Leave history as is; add a new DECISIONS line with the new URL |
| MCP server names | "TinyFish", "Claude Code Remote" | `41_update_search.js` (`TF = 'TinyFish'`), `42_update_buttons.js` (`CCR`), artifact capabilities | Change only if the new account's connector names differ |
| Review queue URL | 8yp4a5q8A8PcrQFdYcXPuB | not in code; only in docs | Record the new one in [Current state](#state) |
| Old tracker copy trigger | trig_01Wg3NS6hNteZq4hwQTRcDay | inside `pipeline/legacy_index.html` (the old tracker page, used only as build_data's OLDHTML input; its script is replaced at assembly) | No action |
| Project id / memory paths | 01a1413e-6231-75bd-9079-fa4237b5738f | memory and Project only | New Project gets its own |

The handoff kit deliberately ships the OLD trigger id and tracker URL (byte-identical to live). This swap is the first change on the new account.

`build/shell/index.html` also contains the trigger id, but assemble.py replaces the page's main script with tracker.js, so the source edit above is enough. Before publishing, check: `grep -rn "trig_\|5wHur4" code/ build/pub/pipeline/` should show only the new values (plus legacy_index.html).

<a id="db"></a>
### 0.5 Database carry-over (export before migrating, re-seed after)
Artifact databases are per artifact and are not in the published files or the kit's publish/ folder. Tools: `source/db_export/EXPORT_CHECKLIST.md` (steps; export target `work/db_export/<artifact>/<collection>/<doc_id>.json`) and `code/db_reseed.py` (turns the export into ≤ 50-write ArtifactData batch payloads with the same doc ids; KIT_README shows the counts once exported). Before exporting, press "Save to sheet" on the old tracker so `pages` and `edits` are empty. On the OLD account:
1. Export every collection below with ArtifactData `list` (all pages; `get` for single docs) to JSON files.
2. Carry the files over.
3. On the new artifact, re-seed them with ArtifactData `batch` (up to 50 writes per call, doc ids unchanged).
4. Re-seed after the first publish of the new page and before anyone presses Update.

| Artifact | Collection | Holds | Carry over? |
|---|---|---|---|
| Tracker | `runs` | Update-button run log: proposed rows, `releases_new`, `ids`, `sheet` lines, `review` lists | Yes: history, and the run the sheet task needs if one is unwritten |
| Tracker | `edits` | Queued sheet edits / removal requests (field `reported`) | Yes: anything not yet written to the sheet |
| Tracker | `tones` | Team tone ratings/edits per story | Yes |
| Tracker | `authors` | Author fills from saved pages | Yes |
| Tracker | `translations` | English headlines/texts done in the page | Yes |
| Tracker | `pages` | Saved pages waiting for the sheet task (`rp-`/`og-` docs) | Yes if not empty; otherwise press Save to sheet on the old account first |
| Tracker | `reprints` | Reprint docs written by runs (`aid` filled back) | Yes |
| Tracker | `notes` | Team notes | Yes |
| Tracker | `clips` | Clip store (was empty at the F7 prune) | Yes if not empty |
| Tracker | `views` | Saved views | Yes |
| Review queue | `items` | Item docs (e.g. 14-regroup…, 17-newoutlet, 18-origins-3) | Yes (or re-seed from build/review/seed + later docs) |
| Review queue | `decisions` | `{choice, note, at}` per item: Sammy's and Claude's answers | Yes, since this is decision history |

Per-viewer browser storage (localStorage `jg-tones`, `jg-authors`, `jg2-notes`, the review page's `reviewOnlyNeedsMe`, IndexedDB `jg-archive`) is tied to the old artifact's origin and cannot be moved. It holds conveniences only.

Collections were found by grep of `collection('…')` in code/tracker/*.js, build/tabs/*.js and build/review/index.html. The doc counts in the live dbs were not checked.

---

<a id="sammy"></a>
## 1. Working with Sammy

### 1.1 Style
- Lean, direct, precise. Dry humor is fine. He pushes back on overstatement, so state limits plainly and don't claim more than was checked.
- Ground everything in what he asked. Don't widen the scope or decide for him: anything not in DECISIONS.md is a question for him (README rule 4).
- He answers by short labels ("1 yes", "2 no", "3 hold off"). Record his answers verbatim in DECISIONS.md.

- Older rules of his, from the 2026-10-26 handoff and still in force:
  - "Do only the ones you are 99% sure on."
  - Ask before expensive or ambiguous work. He often asks "how long would it take" first, so give an estimate.
  - Use a scalpel.
  - If something is obviously a mistake you may break a rule to fix it, but say so.
  - His latest instruction wins.
  - No internet research to fill gaps unless he asks.

### 1.2 Standing rules (all from DECISIONS / coordinator context)
| Rule | Source |
|---|---|
| Every change goes to all three: the code base (L/code via apply_all), the Update button (pipeline + sheet task) and the master sheet | DECISIONS 134 |
| Fix whole classes ("throughout"), not only the instance commented on | coordinator context; e.g. DECISIONS 206, 210 |
| No checks or tests until all changes are made; run the full suite once at the end. Pure UI change: build + a quick screenshot, no rechecks | coordinator context; DECISIONS 106, 170 |
| Never delete: move to `_to_delete/` or `_archive/` with an undo log. The library is add-only. Nothing in L is deleted either (moves go to L/archive/<date>/, MOVES.tsv) | DECISIONS 75, 182 |
| Fill blanks only; never change an existing value unless DECISIONS overrides it | README rule 7 |
| Excel closed before writes; one workbook writer at a time (token) | README rule 7; DECISIONS 165 |
| Don't work around blocks or paywalls; don't log in for him (he logs in himself; never enter credentials) | DECISIONS 78; context |
| No Exa (two one-time exceptions are used up) | DECISIONS 32, 159, 162 |
| Publish only to the live tracker; no preview unless he asks | DECISIONS 186 |
| Instruction tabs only fill gaps; they never rewrite an existing process | DECISIONS 183 |
| Optimizations (buttonopt) go LAST so later changes don't undo them | context; BOARD "POST-V19 ORDER" |
| Reuse every pass for every feature: one read of a text feeds everything it can (copy, tone, topic, bills, author, word count, language, translation) | DECISIONS 22 |
| Always split work across parallel agents where possible | DECISIONS 198 |
| Docs ship with the tool (pipeline/docs + Tracker library/_docs) | DECISIONS 111 |

### 1.3 Coordinator / multi-agent workflow
- The **coordinator** chat (linked to the Mac) only plans, dispatches, records and reports. Every piece of work goes to a background agent, including Mac writes, builds and publishes (DECISIONS 27). Keep the chat clear for Sammy.
- Agents run in parallel on disjoint files. Each file has one owner (BOARD.md; per-pass ownership tables such as build/V20_BRIEF.md). A change needed in a file you don't own goes to `work/tmp_<you>/handoff.md` for its owner.
- Each agent:
  - logs in `status/<agent>.md` (its own file only);
  - keeps scratch in `work/tmp_<agent>/`;
  - ends with a self-check (counts, samples, tests);
  - appends a DECISIONS line for any rule or data change.
- Only the coordinator or an agent it dispatched writes to the Mac or publishes (README rule 1). Exception: fetch agents may ADD new files to the library and log them in `work/library_adds.csv`.
- Integration: one integrator per shared artifact. The final build agent runs apply_all, build.sh and the suites once, and writes `work/BUILD_DONE` (page sha).

### 1.4 Comment-thread etiquette
- Sammy leaves many comments on the artifact (ArtifactComments tool). Reply in the thread.
- **Resolve** the thread when the fix ships live. **Leave it open** if the fix is partial or waiting on him.
- Comment ids are recorded in DECISIONS / phaseB_inbox (e.g. 69e1f457, fd56a06d). Threads open at handoff: [8](#open) items C1–C3.

---

<a id="inventory"></a>
## 2. Inventory: every place data lives

| Place | What | Notes |
|---|---|---|
| `~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx` | **Master workbook** | Tabs in [2.1](#tabs). Sha in [Current state](#state) |
| `~/Desktop/Tracker library/Backups/` | One backup per write, named "AJG Coverage - NewsBank BACKUP before <what> <date>.xlsx" or "… <mtime>.xlsx" (sheet task) | Never pruned |
| `~/Desktop/Tracker library/<year>/` | Cleaned saved copies: `<nb|pq|ws><NNNNN><o|r>-s<NNNNN>.<html|pdf>` | Add-only. NewsBank PDFs (one per article, split from the batch PDFs) and print clips with OCR layer |
| `~/Desktop/Tracker library/_original_html/<year>/` | Raw page as fetched, before cleaning | Same name as the cleaned copy |
| `~/Desktop/Tracker library/Press releases/<year>/prNNNNN.html` | Cleaned release copies (244) | Raw in `_original_html/Press releases/<year>/` |
| `~/Desktop/Tracker library/_original_pdf/<year>/` | Raw single-page downloads of print jump pages (`<aid>_p<page>.pdf`) | Clipping |
| `~/Desktop/Tracker library/_docs/` | Copies of README, DECISIONS, CONTRACT, TONE_GUIDE, clean_playbook, BOARD; `_docs/archive/` = retired "Reprint info" / "Audit plan" tab content | Refreshed + sha-checked on each publish |
| `~/Desktop/Tracker library/_to_delete/`, `_archive/` | Moved-out files, same subfolder layout; undo logs (e.g. `_to_delete/_cleanrows_moved_2026-10-28.txt`, `_archive/_renames_origin_2026-10-28.tsv`, `_archive/_docs_pre_v20_2026-10-28/`) | Never emptied by Claude |
| `~/Documents/Gabriel press PDFs/` | 329 NewsBank batch PDFs (unnumbered, (1)–(100), then 228 "NewsBank Multiple Articles - <timestamp>.pdf" ordered by time; (92) duplicates (90)) ("NewsBank Multiple Articles (N).pdf" / "… - <timestamp>.pdf"); "Gabriel Print Editions - Companion.xlsx" (tabs Print Editions, All PDF Items, Removed, About; print pages AJG-P0001–P2137, 2,133 remain); old `AJG Combined Coverage.xlsx` (superseded); old Documents copy of the master (no longer updated) | Never write the workbooks here. Never touch `Jesse_Gabriel_Mentions.xlsx` (retired source) |
| `$HOME/mnt/outputs` (Mac) | Scratch on the Mac | Never scratch inside the library |
| Tracker artifact (published files) | `index.html`; `data/sheet.json` (b64 of the master); `data/release_texts.json`; `articles/<year>.json` (+ `-N` shards), `articles/releases.json`, `articles/manifest.json` (viewer copies + search text); `img/<n>.json` (embedded images; img/0..15, 100, 101); `pdf/`; `pipeline/**` (rebuild code + docs) | Full list: CONTRACT "Published files" |
| Tracker artifact db (ArtifactData) | Collections runs, edits, tones, authors, translations, pages, reprints, notes, clips | Queue state for the sheet task; team data. Not in the published files |
| Review-queue artifact 8yp4a5q8A8PcrQFdYcXPuB | db `items` (docs such as 14-regroup…, 17-newoutlet, 18-origins-3) and `decisions` (Sammy's or Claude's answers, `{choice, note, at}`) | Source page build/review/index.html |
| Old artifacts | "AJG Press Coverage Tracker (Copy)" UCat3jW8cViL37pHTTt6JA / dc44cdfe-0365-403e-925f-ee998e6700ef, kept as fallback; preview 2bMQrhKHRzpK9A9qMbzAk6 DELETED | Don't publish to them |
| claude.ai Project "AJG Mentions Database" (01a1413e-6231-75bd-9079-fa4237b5738f) | library/README.md, CONTRACT.md, DECISIONS.md, BOARD.md, the old `claude/AJG Project - Handoff Memory.md` (superseded by this doc) | Synced by main after each publish |
| Memory (Project-scoped) | areas/ajg-coverage-workbook.md, areas/newsbank-print-clipping.md | Content copied in [0.3](#start) step 9 and [3.13](#model-clip) |
| Scheduled task trig_01WRLX437wg7VRViGUTKei8R | Sheet task, runs on the Mac, auto approval, DISABLED | Older trig_01Wg3NS6hNteZq4hwQTRcDay belongs to the old Copy |
| Connectors | TinyFish (search, fetch_content, browser automation; paid per step; the leginfo + release checks use it); Claude Code Remote (fire_trigger, scheduled tasks); Claude in Chrome / built-in browser (logged-in saves with Sammy's own login: LA Times, Sac Bee); linked Mac (remote-devices) | Exa forbidden |
| L (coordinator scratchpad) | code/, build/, docs, status/, work/ (snapshots, state files: next_prid.txt, WORKBOOK_WRITER.txt, sid_map.json, id_map.csv, library_adds.csv, img_cache/, html_clean/, texts/), archive/ | Ephemeral and not reachable from another account; the kit carries it |

<a id="tabs"></a>
### 2.1 Workbook tabs (at master 4d7fb37c)
| Tab | Rows | Cols | Key columns / notes |
|---|---|---|---|
| Coverage | 9,787 | 67 | Article ID · Story ID · Original or reprint · Data Source · Saved Copy? · File type · File name · File type 2 · File name 2 · In Tracker? · Date · Year · Outlet · Publisher · Outlet city/county/state · Medium · Reach · Language · Headline · Translated Headline · Story in English · Author / byline · Author 1–9 · Author title · Edition · Section · Page · Print Article ID · Print date/headline/section/word count · Word count · Mentions "Gabriel" in text · # of reprints · Topic · Bills · Tone · Tone note · Tone rated by · Team note · Publisher link · Link status · ProQuest link(s) · NewsBank links (article, print article, print page, via CA State Library) · APA citations · Tracker story code · Search lookup (Oct 26) · Role · Press release · Old Article ID · Old Print Article ID. Column order authority: `covcols` block |
| Originals | 4,490 | 66 | Mirror of Coverage's Original rows (no "Search lookup"). **Rebuild after any Coverage change** |
| Bills | 1,895 | 6 | Bill · Session · Date · Milestone · Detail · Final status. Static leginfo snapshot (273 bills); the sheet task does not refresh it (DECISIONS 117) |
| Press releases | 244 | 46 | RELTAB-v2: Release ID (col A) · Date · Title · … · Saved Copy? · File name · … Legislator 1–6 · Other official 1–4 · Contact · Bill 1–6 · In tracker · Tracker release ID 1–2 · … Note. `code/reltab.py COLS` is the definition. Frozen at D2. Pending RELTAB-v3 write (48 cols): In tracker → Has copies, Tracker release ID → Copy story ID, Coverage stories linked → Copies (rows), Tracker date → First copy date (if different), + Related count, Related story IDs |
| Audio & video details | 1,030 | 35 | One row per Podcast/Radio/TV/Video Coverage row, keyed by Article ID; Channel (col E) then Show/program. `code/avtab.py COLS` |
| Removed | 85 (incl. AV-tab lines) | 72 | From tab · Reason removed · Removed on · Category · every Coverage column · Other tab row. Navy header |

Colours: **every font is default black**, except that a **red whole-row font (00C00000) = row not shown in the tracker** (DECISIONS 102, 185). The old provenance colours (blue/green/orange/red, from the 2026-10-26 handoff) are history; don't apply them. The "Reprint info" and "Audit plan" tabs were retired 2026-10-28 (content archived).

Styling:
- Header row navy 132A4A, white bold. Removed tab: navy header too.
- Freeze panes at C2 (Press releases: D2). Autofilter on. Column widths kept.
- Edit cells in place with openpyxl so formatting survives; never rebuild a tab from scratch.
- Always rebuild the Originals tab from Coverage after a change.

Rows with a blank "Original or reprint" (1,444 at 4d7fb37c; 1,471 on 2026-10-26) are mostly NewsBank print pages with no text and no Story ID. They are not in the tracker (DECISIONS 7). The 2026-10-26 options were a "Likely article" column or reading the pages through Chrome. The current route is print clipping ([3.13](#model-clip)), which is paused at 28 rows; no "Likely article" column was built.

---

<a id="model"></a>
## 3. Data model and rules
DECISIONS.md is authoritative; line numbers below are its line numbers at 4d7fb37c.

### 3.1 IDs
| ID | Form | Rules |
|---|---|---|
| Article ID | 5-digit, `00034`; no prefix, no o/r suffix | One per Coverage row; Web + Print rows also have a Print Article ID (its own number). Old nb-/ws-/pq- IDs in "Old Article ID" (DECISIONS 36, 42). One sequence over Article ID + Print Article ID |
| Story ID | `sNNNNN` (was jg-NNNNN, same number) | The key everywhere (db docs, URLs, DOM). Old 6-hex tracker codes `jg-xxxxxx` stay in "Tracker story code" (saved-copy lookup + migration only; `idmap` block, sid_map.json) |
| Release ID | `prNNNNN` | Permanent, one per Press releases tab row, pr00001… by date → title → URL; never reused. Next = 1 + max (tab, release_texts.json) |
| Placeholders | `NEW-<run>-<n>`, `sNEW-<run>-<n>` | Update-button rows; sheet_task.py assigns real IDs and writes the mapping back into the run doc (`ids`) |
| Library file names | `<nb|pq|ws><NNNNN><o|r>-s<NNNNN>.<ext>` (nb = NewsBank, pq = ProQuest, ws = web-saved); rows with no Story ID `<fmt><NNNNN>.<ext>` | o/r appears only in file names. Some swapped/merged rows keep their old o/r suffix until a library rename pass |
| Print pages (Companion) | AJG-P#### | Old clipping codes; retired codes are not reused |

### 3.2 Originals and the reprint rule
- Only **Original** rows become tracker entries. Reprints are listed under their Original by Story ID, by outlet and date only, with no links to reprints (DECISIONS 104). Rows with a blank "Original or reprint" (unidentified print pages) and "Reprint (unverified)" rows are kept in the sheet but not shown (DECISIONS 7, 90).
- **String-of-text rule** (`code/reprint_rule.py text_verdict`): runs of ≥ 25 identical consecutive words cover ≥ 90% of both texts. Edge lines (≤ 120 words each end) may be set aside. Not a % similarity (DECISIONS 53, 72).
  - Window: 90 days for text matches. ±7 days for the headline-only / headline+people fallback and the OCR near-miss link (DECISIONS 158).
  - OCR-tolerant option for print clips only (DECISIONS 153, 180).
- **Originals order** (tier/rank in reprint_rule.py) decides which row of a story is the Original. Releases and aggregators rank low.
  - ORIGINCREDIT-v1: a credit line, dateline, NewsBank author, section or person+service byline on any row ranks that service first (AP, MyNewsLA/CNS, JNS, Capital & Main, States Newsroom, CNN Wire …) (DECISIONS 206).
- Same outlet's web + print editions = ONE row, never reprints (CONTRACT "Coverage row conventions").
- Korean outlets can be dated a day after U.S. outlets for the same moment. A one-day gap is not an order.
- "# of reprints" is a derived count: distinct outlets other than the Original's, unverified rows excluded, counting each outlet once across editions and feeds. It is recomputed on every write that touches a story's Reprint rows (DECISIONS 177, 204).
- Topic/Bills/Reach carry to a new Original blank-only, and Tone too when it is the same text (DECISIONS 90).

### 3.3 Press releases
- **Pure press releases are excluded from the tracker**: the release text republished as-is with no reporting (PR wires, US Fed News, PublicNow, the office's own page, verbatim posts). The sheet keeps them with "Press release" = Yes (DECISIONS 35).
- **Release text rule** (RELRULE-v1, `code/release_rule.py`): a row carries an official release only when its saved text passes text_verdict against the release (headline+dek+body, or body), dated −1 … +30 days.
  - No saved text = untestable: listed, never marked.
  - EXCERPT-v1: distribution-service abstracts ≥ 25 words that lie ≥ 90% in the release count as copies (DECISIONS 142).
- Scope: everything on gabriel.asmdc.org (a46 redirects there). Jewish Caucus "Press Release" items count only from 2020-11-18 (his chair tenure; DECISIONS 123). Five releases have no official posting; they are not tab rows and have no Release ID.
- Copies: cleaned like articles, `Press releases/<year>/<prid>.html`, served from articles/releases.json. They are not stories (DECISIONS 187).
- **RELCOPIES-v2** (rp-copies, `code/relcopy.py`; contract build/relplan_contract.md "rp-copies"): besides the 90%-of-both text rule, a story is a copy when it holds ≥ 50% of a ≥ 250-word release (story share ≥ 0.85 automatic, else hand check / review), and a PublicNow row with no text is a copy when its headline is the release title cut at "…" (0–1 day; overrides DECISIONS 133). A copy filed as a Reprint of another issuer's story gets its own Story ID (pr00182 → s04749).
  - Tab columns renamed to what they hold: Has copies · Copy story ID 1–2 · Copies (rows) · First copy date (if different); new derived Related count · Related story IDs (from release_related.json, recomputed each build). `reltab.RENAMED` / `reltab.col()` read old and new names.
  - Issue label "District / community" for district honors, local grants and district events.
  - Sheet write prepared, not committed yet (see 8.1 D10).
- **RELRELATED** (release page "Related stories"; `code/relmatch.py`, state `release_related.json` keyed by Release ID, merged and never shrunk):
  - v1 evidence types: `text` (≥ 25-word runs, −1 … +90 days), `quote` (≥ 12-word runs totalling ≥ 20 words, −1 … +30), `bill` (shared bill + on subject, −1 … +7), `topic` (cosine ≥ 0.25, −1 … +7). "Possibly related" = shared bill, subject not checkable.
  - v2 adds `pre`: up to 14 days BEFORE the release when it is clearly the same announcement (release-rare anchor name + dollar figure / second partner / bill in the same passage) (DECISIONS 212, 219).
  - v3 (rp-match, RELPLAN; contract build/relplan_contract.md "rp-match"): non-English stories scored on their English `text_en`/`hl_en`; a release bill NAMED in the story text counts as a shared bill (text cosine ≥ 0.15 when untagged); `nearcopy` (≥ 60% of the story is release text, one release per story); `anchor` (0 … +7 days, release-rare names + figure/partner/bill, or rare title words in the headline); AV transcripts with a ≥ 20-word quotation count as `quote` without the topic floor, short same-bill AV summaries are "possibly".
  - v3 tier 3 "Later coverage" (not counted as related; only for stories with no other link): `later` (same bill + session, +8 … +30 days, before the next release on the bill, on topic and leading with the bill or Gabriel) and `laterquote` (> 7 days, ≥ 20-word quotation, not a bio formula, cosine ≥ 0.125). Tier is `relmatch.TIER`; "Related" = tier 1.
  - Totals (v3): 1,223 related on 180 releases + 62 possibly related + 121 later coverage. Hand-check precision per new tier ≥ 96% (status/agent-rp-match.md). Sammy kept the 90-day text window (DECISIONS 205).
  - `--update` (Update button) recomputes every story from 14 days before the earliest re-matched release against all releases, so it equals a full run; one row per story per release.
- **RELTHREAD** (release ↔ release, `code/relthread.py`, called by build/tabs/releases_data.py → tab-releases `thr`; contract build/relplan_contract.md "rp-threads"):
  - Threads: same bill + session (December of an even year = next session). Background mentions (older session's bill, or finished > 45 days before) make no thread.
  - Text links (cosine ≥ 0.60, boilerplate sentences dropped): a no-bill release inherits the bill (pr00091 → ACR 51); renumbered bills join (AB 469 → AB 468).
  - Pairs outside threads: follow-up (≤ 14 d, cosine ≥ 0.35), similar (cosine ≥ 0.45 or shared runs).
  - Milestone label: Bills-tab milestone −3 … +1 days of the release; clerical steps never label.
  - People: Others named table (41 people in ≥ 3 releases) and Joint with (named with Gabriel in title / lead subject).
  - Other organizations' releases are not shown (Sammy, 2026-10-28).
- **RELUI-v1** (release tab UI, rp-ui; build/tabs/releases.js + releases_data.py, ⓘ + viewer hooks in 53_tabs.js):
  - No rule paragraphs: short labels + ⓘ tooltips (53_tabs.js `tbInfo`, ctx.info). Every rule text comes from tab-releases `rules` (releases_data.py builds it from relmatch TIER/LABEL/windows, release_rule, relcopy, reprint_rule constants); releases.js types no thresholds.
  - Release page order: header (kicker type · date · source; title and [Read release] open the release in the viewer; official link; word count; ~80-word lead ≥ 1100 px; Who/What/Coverage incl. milestone and "AB xxx coverage" before · after · not linked) → Ran the release → Related stories (per-row evidence tag, "How it's related" chips, strongest link first, no chart) → Later coverage (tier 3) → Other releases on this bill (thr threads + pairs) → Possibly related (collapsed).
  - Viewer: a release / release copy opens without story controls (tbCopySheet), "1 of N" over the release and its saved copies.
  - List: columns Release · Date · Source · Ran it · Related ("–" for 0), one "Ran it" facet, Related / Possibly related Some·None, Joint with and Others named facets (thr people), bill chips, no "Press release ·" prefix.
  - Bill coverage counts (tab-releases `bc`) are computed at build with relmatch's windows (before −7…−2, after −1…+7) and report stories not linked to the release (backend #9).

### 3.4 Outlets
- Names are NewsBank style ("Sacramento Bee, The"). Variants fold to one outlet through `code/outlet_rules.json` + `sheet_task.norm_outlet(name, Outlet city)` (OUTLETRULES-v1). That covers "Today's Edition" / ": Blogs" variants, feeds, aliases, generic names by city, and keep_separate pairs (e.g. Brentwood News vs "Press, The" @ Brentwood).
- Location = the outlet's home, not the story's (CalMatters = CA). Raw domains are never outlet names (DECISIONS 199).
- Publisher = owner at the row's date (e.g. Santa Maria Times etc. → "Santa Maria News Media" after Lee's 2020 sale) (DECISIONS 100–101).
- Skip lists: californiafiles.org, database/results/listing pages (bill trackers, election results, donor/Form 700, tag listings, sitemaps) (DECISIONS 73, 81, 93; `clean_rules.json skip_urls`).
- Sister sites (sfgate.com, eastbaytimes.com) are not the publisher's own site (DECISIONS 60).

### 3.5 Audio & video: Channel vs Show (AVSHOW-v1, NOSHOWCHAN-v1)
- **Channel** = the channel/station/network/publisher that carried the item. It is filled where evidence states it: Outlet [network] bracket, URL domain, page metadata, saved copy. **Blank when none is stated, with no review flag; the panel omits the row** (DECISIONS 217–218).
- **Show/program = real program names only.** A channel/station/network name never sits in Show; `avtab.guard_show` moves it to Channel. Public-fact networks are kept: TODAY→NBC, GMA→ABC, As It Happens→CBC Radio (DECISIONS 205).
- Hosts go in Author 1..N, not on the AV tab. Item type ∈ Episode | Broadcast segment | Video clip | Web story.
- Dates:
  - archive.org TV clips: the Pacific air date (also sets the Coverage Date).
  - Station video pages never date a row: no sidebar dates, and nothing within 3 days of the save day (DECISIONS 164, 168, 188; AVTAB-v3).

### 3.6 Tone, Topic, Bills (TONE_GUIDE.md)
- Five-point tone toward Gabriel (Very negative … Very positive). One-sentence note under 30 words, not starting "The article". "Tone rated by" = `Claude, from saved copy (YYYY-MM-DD)` or `… from article excerpt (…)`.
- Full-text ratings overwrite excerpt ratings (DECISIONS 34).
- No text: rate only when the headline names Gabriel, in any script (DECISIONS 91).
- Tone is rated on Originals only (DECISIONS 110).
- Topic: exactly one from the 16-label list. Bills: only from `gabriel_bills_leginfo.json` (443 measures; leginfo is the source of truth, DECISIONS 26, 94–95).
  - Authored bills always count.
  - Coauthored bills count only when the article ties them to him.
  - Budget trailer bills (Committee on Budget) do NOT count (DECISIONS 98 reverses 97; TONE_GUIDE still describes a "budget chair" role; DECISIONS wins).
- Gabriel in other scripts counts as a mention (가브리엘, Габриэл, גבריאל, 加布里埃尔/爾) (DECISIONS 63). Wrong Gabriels (Ugarte, Petek, San Gabriel) are skipped or removed (DECISIONS 77, 93).
- Tracker averages display as "<Label> <signed value>" (TONELABEL-v1).

### 3.7 Reach
- Labels in the master (4d7fb37c): Statewide California · California regional & local · District & Valley · National · Out-of-state local · Trade, advocacy & blogs · Jewish press · **Spanish-language** (US-based) · **Ethnic** (US-based, neither English nor Spanish) · **International** (foreign-based, non-Jewish press). The retired "Spanish-language & ethnic" label is never output.
- An outlet may carry several tags, "; "-joined, first = primary. A story counts under every tag (DECISIONS 28–30).
- New rows take Reach only from the same outlet's consensus. Brand-new outlets are left blank (DECISIONS 93, 199).

### 3.8 Reporter affiliation (AFFIL-v1)
- A reporter's outlets are only those of their **Original** stories. Reprint outlets never appear as an employer (DECISIONS 193, 208).
- Sheet side: generic staff titles on reprints at another outlet are blanked or replaced by the Original's title (10 cells, DECISIONS 210, 215; "Staff (ABC10)" on 07066 kept). The button copies Author title from the Original.
- Bylines:
  - A group of people is an author: "<Outlet> Editorial Board", "<Outlet> Staff", using the Original's outlet on reprints.
  - A kind of article is not ("Editorial", "Opinion") (DECISIONS 44, 54, 58–59).
  - CMS account labels are not bylines (DECISIONS 171).

### 3.9 Fill rules
- Blanks only, in black font (README rule 7; DECISIONS 185).
- Explicit overrides (only these):

| Override | DECISIONS |
|---|---|
| Reach relabel | 28 |
| Full-text tone over excerpt | 34 |
| ID / file-name migration | 36 |
| Language from the text | 64 |
| Gabriel-mention No→Yes | 63 |
| Error copies → `RETRY – TinyFish` / `BLOCKED – TinyFish` placeholders | 65, 80, 82 |
| Placeholder replaced when a copy is later saved | 171 |
| "# of reprints" (always recomputed) | 177 |
| Word count from the saved text | 173 |
| Show/program cleanup | 202 |
| Press releases tab cleanup | 160 |
| Publisher corrections | 101 |

- Links shown in the tracker: CA State Library NewsBank/ProQuest links, the publisher's own link, and archive.org TV clips. No NewsBank print-page links. A copy-link icon sits LEFT of every link. Links appear on Originals only (DECISIONS 49, 61, 83, 104, 118).

### 3.10 Removals
- Rows move to the **Removed** tab (never deleted) with a reason and category. Their library files `mv` to `_to_delete/`.
- Category values in use at 4d7fb37c (85 rows):

| Category | Rows |
|---|---|
| 1 mis-credited reprint | 14 |
| 2 duplicate | 20 |
| 3 database/listing page | 20 |
| 3 database/results page | 15 |
| 3 only outside article | 2 |
| 3 not coverage | 2 |
| 4 not about Gabriel (review queue) | 11 |
| 4 this-session duplicate | 1 |

  The button writes "5 removed in the tracker" for removal requests, which now execute (DECISIONS 180, 216).
- Delete everywhere when Gabriel appears only outside the article: comments, teasers, tags (DECISIONS 68–70, 74).
- NewsBank text missing a mention is NOT grounds by itself: captions get dropped. Full text that lacks him IS grounds (DECISIONS 81, 173).

### 3.11 Saved copies and photos
- Every HTML is cleaned with `code/clean_html.py` + `clean_rules.json` (scalpel; keep when in doubt; > 35% removal → keep the page as is and flag). The raw page goes to `_original_html` (DECISIONS 52, 66).
- **Clutter rule for text comparisons** (reprint rule, regroup): set aside only known clutter. That means the NewsBank header/citation block, the tracker's "Saved YYYY-MM-DD" header, "Text of the ProQuest PDF…" and "Print edition: pages…". No broad phrase triggers: they delete real syndicated text (clean_playbook, 2026-10-26 trial).
- Viewer copy = the Original's own HTML > the Original's NewsBank/ProQuest text > another row's HTML (DECISIONS 213).
- PHOTOS-v2: real photos are embedded (largest srcset ≤ 1000 px, JPEG q≈0.75). Images that fail are dropped with captions kept, and the build gate allows no unresolved images (DECISIONS 196, 213).
- RELIMG-v1: release copies' photos also go to img/1NN.json shards (jgimg refs, after all story images; > 1200 px downscaled); articles/releases.json 7.33 MB → 1.52 MB, text byte-identical.

<a id="model-sources"></a>
### 3.12 Sources and tools
- TinyFish only for web fetch/search. Exa is forbidden; the two one-time exceptions (podcasts, people lookup) are used up.
- **TinyFish costs** (Sammy's plan, per the 2026-10-26 handoff): search and fetch_content are free; browser automation costs about $0.016 per step; deep research costs $2 per run, so avoid it.
- **Sites that block Claude**: LA Times, Politico, NYT, Washington Post, Sacramento Bee, The Center Square, Daily News, SF Chronicle, OC Register. Don't work around them; mark the row `BLOCKED – TinyFish`. Only LA Times and Sac Bee were ever saved, through Sammy's logged-in Chrome (DECISIONS 115–116).
- No curl through the proxy for site pages.
- Chrome saves use Sammy's logged-in browser, read-only (no subscribe/login/consent clicks) (DECISIONS 115–116).
- McClatchy rows with no Publisher link are not Chrome targets.

<a id="model-clip"></a>
### 3.13 NewsBank print clipping (paused)
- Access: CA State Library NewsBank via the proxy host `infoweb-newsbank-com.castatelib.idm.oclc.org`. Sammy logs in himself.
- Since 2026-10-27, clips go into the Tracker library under the row's library name, not AJG-P codes:
  - Save the ENTIRE page ("Download Full Page" PDF, APA citation, no selection box) plus every page the article jumps to/from, merged into one PDF in reading order.
  - Raw jump pages go to `_original_pdf/<year>/<aid>_p<page>.pdf`; record "cont. p. N" in Team note.
  - OCR on (ocrmypdf layer). Only his article's text goes to `work/texts/nb/<Old Article ID>.json`.
  - OCR near misses are decided automatically ([3.2](#model)) (DECISIONS 150–154, 157).
- Paused at 28 rows by Sammy; resume from `work/clip/targets.csv` per status/agent-clip.md.
- Browser mechanics (old AJG-P flow, still useful):
  - Search Page needs real keystrokes for "Gabriel".
  - Fit to Screen needs a real click.
  - Don't hook iframe src or other request hooks: that blocked the download.
- The Companion workbook rules are in memory file newsbank-print-clipping.md: codes in PDF order, Removed tab, existing codes never change. Its content is copied in [0.3](#start) step 9.

<a id="model-nb"></a>
### 3.14 NewsBank text and docref notes
- NewsBank article text begins "Author: … Section: … N Words / OpenURL Link" and ends with a copyright line plus "Citation (apa Style)". In the batch PDFs, a text is keyed by "PDF name#position" (code/extract_nb.py; Companion "All PDF Items" maps NewsBank link → Source PDF + Position).
- Extracted texts: `work/texts/nb/<Old Article ID>.json`.
- pdftotext drops the hyphen after the 7-digit julian date in NewsBank docrefs; reinsert it (`%40\d{7}-HEX16`).
- Print pages in the PDFs are titled "Paper: Page N" and carry only a citation + a `docref=image/v2…` link, with no text. Open them through the CA State Library proxy host.
- NewsBank extraction drops photo captions and guest lists, so a missing mention in NewsBank text alone is not grounds to remove a row (DECISIONS 81).

---

<a id="code"></a>
## 4. Code and build

### 4.1 Layout (L)
| Path | Contents |
|---|---|
| `code/tracker/NN_*.js` | Tracker JS, one file per section. 00_head (CSS, tonePrompt) · 01_authors · 02_state · 03_overview · 04_facets · 05_table · 06_story_sheet · 07_charts · 10–21 Manage panes, report, languages, gaps, county map, checks, saved views, team notes/tone, translation · 22_helpers · 23_render · 24_events · **40–43 Update flow** (40_update_outlets, 41_update_search, 42_update_buttons, 43_update_log) · 50_insights_shell · 51_reorg · 52_us_map · 53_tabs (tab framework, routing, maps, NAVHIST) · 99_boot |
| `code/*.py` | build_data.py (sheet → data blocks), assemble.py, sheet_task.py (the Update button's writer), reprint_rule.py, release_rule.py, relmatch.py, relthread.py (release threads / milestones / people for tab-releases), reltab.py, relpage.py, avtab.py, av_display_clean.py, clean_html.py, make_copies.py, img_embed.py, authorsplit.py, tabs_data.py / tabs_assemble.py, insights_data.py / insights_assemble.py, make_shell.py, migrate_ids.py / make_id_map.py (ID migration), apply_fills.py, extract_nb.py (Companion), prep_workbook.py |
| `code/*.json`, `*.csv` | clean_rules.json, clean_overrides.json (library-only), outlet_rules.json, av_rules.json, release_texts.json, release_related.json, gabriel_bills_leginfo.json, author_canon.csv |
| `code/sheet_task_prompt.md` | The sheet task's full instructions (shipped as pipeline/sheet_task_prompt.md) |
| `code/_history/` | Retired patch scripts (`patches/`, with README mapping step → marker → where the edit lives now), `pre_split/` |
| `code/make_handoff_kit.py` | Builds L/handoff_kit/ (owner agent-handoffkit) |
| `build/js_merged.js` | = code/tracker/ concatenated. **Never edit by hand** (guard stamp js_merged.js.sha256) |
| `build/tabs/<id>.js` + `<id>_data.py`, `_common_data.py` | Tab modules (reporters, outlets, releases, bills, travel); contract build/tabs_contract.md |
| `build/insights/` | Insight blocks (release_pickup_data.py, story_travel …) |
| `build/shell/index.html`, `shell.html` | Page shell the builds assemble into; shell.html = stripped (95 KB) |
| `build/pub/pipeline/` | What ships as `pipeline/` (code + docs/ + tabs/ + insights/) |
| `build/build.sh` | Canonical build |
| `build/tests/` | `tabs/` (harness), `sheet_task/` (test_sheet_task.py, test_auto.py, fixtures) |
| `build/review/` | Review-queue page source + seed |

### 4.2 apply_all
`python3 code/apply_all_patches.py`:
1. concatenates code/tracker/ → build/js_merged.js (stops if js_merged was hand-edited);
2. refreshes code/gabriel_bills_leginfo.json from work/;
3. refreshes build/pub/pipeline/ (docs, insights, tabs; merges release_texts.json and release_related.json, never shrinking them);
4. verifies (py_compile on every shipped .py, node --check).

A second run changes nothing. Flags: `--check` (scratch copy), `--no-pipeline`, `--tracker-js OUT`. There are no anchor patches since 2026-10-28.

### 4.3 build.sh and tests
- `build/build.sh` (env XLSX default work/coverage_current.xlsx, BASE, OUT default work/build_last) runs two builds:
  - the **LIB build**: code/build_data.py + assemble.py with js_merged.js;
  - the **PIPELINE-ONLY build**: build/pub/pipeline copied to scratch and run exactly as sheet-task step 6, assembling from shell.html.
- It prints both index sha256s and a per-block comparison. The proof standard is "LIB index = pipeline index, 0 block diffs" (v20.1: c252e5a1…, 15/15 blocks).
- Tests (run once, at the end):

| Suite | Command | v20 result |
|---|---|---|
| Tabs harness | `bash build/tests/tabs/build_testpage.sh`, then `cd build/tests/tabs && MOD=all node harness.js` | 869/869 |
| Sheet task | `python3 -I build/tests/sheet_task/test_sheet_task.py` | 50/50 |
| Auto | `python3 -I build/tests/sheet_task/test_auto.py` | 35/35 |
| REORG | — | 62/62 |
| Copies | — | 16/16 |
| AV clean | — | 80 copies / 75 changed / 0 fails |

  Other page suites live in work/tmp_agent-code/suite and partly point at archived folders.
- Copies: `make_copies.py --img-cache work/img_cache --pdf-restore work/img_cache/pdf_restore --img-strict` (+ `--releases work/html_clean/press_releases`) → articles/*.json, img/100–101.json, manifest.

### 4.4 How a publish works
1. All changes made (code, pipeline, sheet) → apply_all → build.sh → suites once → `work/BUILD_DONE` = page sha.
2. Build a publish map: published path → source, diffed against the live listing (`Artifact list scope:"files"`). Files left out stay as published; `null` removes one. Examples: work/tmp_agent-v20-final/make_publish2.py, work/tmp_agent-v20b-subtitle/publish.json.
3. Publish to the live artifact URL (read it first if this conversation didn't publish it). Omit `capabilities` to keep them. Batch within 255 files / 64 MB per call, **page last**.
4. Refresh `Tracker library/_docs/` (stage → commit → sha-check). Main syncs the Project docs.
5. Reply and resolve the comment threads the publish fixed.

**Storage cap**: 256 MB per version and 511 files. About 250 MB is used now, so the next big update needs a repack or trim of the old img shards (img/0..15) first. The prune plan in status/agent-prune.md shows how: repack img/3, drop unreferenced images; the copies-only repack frees about 80 MB.

---

<a id="update"></a>
## 5. The Update button end to end

### 5.1 Page side (code/tracker/40–43)
- Header buttons: **Update database** (find mode), **Refresh from files** (refresh mode), and **Save to sheet** (queued edits only). Nothing runs on its own (DECISIONS 107).
- Find mode steps: search the web → add new stories → translate new non-English ones → sheet step.
  - **Search**: TinyFish keyword and site searches. These cover his name in English and in other scripts, recent bills, dormant outlets every run, and 1 backfill search per new outlet. There are no issue-word or D-Encino searches.
  - Searches start 7 days before `searched_to`, which advances only when ≤ 2% of searches failed. Rate limit about 30 calls/min (TF_GAP 2.1 s).
  - Free pre-filters (links already in the sheet, known-blocked hosts, skip URLs, no Gabriel / no bill number) run before Claude screening (20 per call, lightest model tier).
  - TinyFish fetches every candidate. Blocked/paywalled pages become `BLOCKED – TinyFish`.
- **Leginfo check**: one TinyFish fetch_content per run for new Gabriel bills (adds to gabriel_bills_leginfo.json).
- **Release check** (RELCHECK; RELBUTTON-v1 runs it FIRST, before the searches): gabriel.asmdc.org/press-releases + the Jewish Caucus news page (Press Release items), up to 2 listing pages, stopping at a known URL or an older date. The OLDEST 5 new releases are fetched and go to `releases_new` (the rest wait for the next run; `relcheck` says how many). A caucus posting of an office release (same normalized title ±3 days) rides on the office item (`also_caucus`) or, when the office copy is already on the tab, goes unfetched with `dup_of`.
- **Release pickups** (RELBUTTON-v1, backend review #3): for each open release (this run's new ones + the build's releases of the last 30 days, newest first, ≤ 8) up to 3 searches, kind `release`: the title in quotes, the first 12 words of its longest 14–45-word sentence naming him, its first bill. Results dated from the day before the release; the release's own sites dropped. Finds carry `_release {prid, url}`, Data Source "Release pickup search (TinyFish)", and skip the no-Gabriel filters and the quick screen (the sheet task decides).
- **TV**: archive.org TV News via the GDELT TV API through TinyFish, one clip per station per day.
- The page never decides reprints by text (BUTTONOPT-v1). It proposes rows in Coverage-column order (`covcols`) with placeholders, plus `_page` (pages doc `rp-<hash6>`) and `_origin` (originator candidates `og-<hash6>`). Everything goes into db collection `runs` (CONTRACT "Proposed rows").
- Refresh mode: rate tone, read authors and translate whatever is missing, then the sheet step.
- Sheet step: `fire_trigger(SHEET_TASK, text "… Log entry: run-<id>")` through Claude Code Remote.

### 5.2 Scheduled task → sheet task
- The scheduled task's text (replacement pending, work/tmp_agent-buttonopt2/scheduled_prompt.md) reads `pipeline/sheet_task_prompt.md` from the tracker and follows it. It never uses Exa or search, never changes scheduled tasks, never deletes.
- `sheet_task_prompt.md` steps:
  1. Read the db collections to files; `sheet_task.py --check-only`. Exit 3 = nothing queued → stop, unless the run is a Refresh.
  2. Stage the workbook. Stop if the Excel lock file `~$AJG Coverage - NewsBank.xlsx` exists. Back up to Backups/.
  3. Read all pipeline files in one call. `--copies-needed`; fetch release pages if needed; `--release-candidates`; then run sheet_task.py (`--out out1.xlsx --result --pages-dir --copies --copies-out --img-cache --bills --release-texts --release-related --today`). Exit 2 = verification failed → don't commit. Then (RELBUTTON-v1) build_data.py on out1.xlsx, copies_out over copies, relmatch `--update` with `result.relmatch` (releases + new / newly saved stories, v3 tiers), and `sheet_task.py --after-relmatch pipeline/release_related.json` → the workbook to commit (only the Press releases tab's derived columns change; review-queue docs in `result2.queue_docs`).
  4. Commit the workbook (expectedMtimeMs, then shasum). Add pages add-only. `mv` removals to `_to_delete/`.
  5. Write back to the db: ids, `sheet` line, clear edits, delete pages docs, `review` lists (+ releases_review / releases_unmarked / releases_dual). Review queue (artifact 8yp4a5q8A8PcrQFdYcXPuB, `items`): `result2.queue_docs` (`<tag>-nearcopy`, `<tag>-billtags`, rp-queue shapes) in one batch.
  6. Rebuild: blocks / copies / relmatch are already done in step 3 → tabs_data `--only releases` on the committed copy → assemble from pipeline/shell.html → data/sheet.json.
  7. Republish index.html + changed copies + data/sheet.json (+ the bill list / release_texts / release_related when changed). Keep the existing files and capabilities.
- `sheet_task.py` makes all judgments: the reprint rule on every find, reprint and originator; originals order + origin credits; skips; fills; Author title from the Original; outlet/Medium/place; date checks; Press releases tab (RELTAB with the old or the RELCOPIES-v2 column names via reltab.col, Release IDs, release copies, release_texts, dual posts merged, Has copies / Copies (rows) / First copy date / Related count / Related story IDs recomputed every run); Press release marks (text rule, relcopy near copy ≥ 0.85 story share → mode nearcopy, below → review + queue; PublicNow title prefix → mode title; untestable wire rows this run marked on arrival that start no release title → unmarked; a passing Reprint of a story whose Original does not carry the release → marked, not linked, `releases_review`); release-pickup finds (kept when a copy, or when they name him; else `releases_skipped`); AV tab (Channel/Show, guard_show, AV dates); photo embedding; red rows; removals; "# of reprints"; Originals tab; verification.

### 5.3 Known gaps
| # | Gap |
|---|---|
| G1 | ~~No per-release coverage search~~ → RELBUTTON-v1 release pickups (5.1), not yet run live (scheduled task disabled, G2). pr00244 (2026-10-24) falls in the 30-day window of the first live run |
| G2 | Scheduled task DISABLED: the button's sheet step does nothing until the replacement prompt is approved and a supervised run passes |
| G3 | Previews right after Update may show clutter until the rebuild (no in-browser cleaner; DECISIONS 99) |
| G4 | Merges of stories split by the old ±7-day window are not done automatically; queued for the next full regroup with a list to Sammy (DECISIONS 158; BOARD NEXT-REGROUP; e.g. AP "Nazi-looted art" s00044/s04300/s04685/s04686) |
| G5 | The Bills tab (sheet) is a static snapshot, not refreshed by the button |
| G6 | TV syndication (e.g. KTLA reporter on "NBC - 8 WFLA") is not handled by AFFIL-v1 (v21 queue) |
| G7 | Origin root fix "fetch the missing originator page and add it": implemented through `_origin` candidates; credits alone would reorder 4 stories already in review 18-origins [unverified: whether any live run has exercised it] |

---

<a id="write"></a>
## 6. Workbook write procedure (README rule 7) and Mac bridge pitfalls

### 6.1 Rule-7 write, step by step
1. Sammy closes Excel. Check that there is no `~$AJG Coverage - NewsBank.xlsx` lock file in `Tracker library/`.
2. Take the token: write your agent name to `L/work/WORKBOOK_WRITER.txt` only if it reads "none".
3. Re-stage the master (`device_stage_files`), note its mtimeMs, and confirm its sha = the current master sha (DECISIONS' last line / [Current state](#state)).
4. Commit a backup first: `Backups/AJG Coverage - NewsBank BACKUP before <what> <date>.xlsx`.
5. Write to a NEW, uniquely named file. Fill blanks only (except DECISIONS overrides), in default black font. Red row font for rows not in the tracker. Rebuild the Originals tab after any Coverage change. Recompute "# of reprints" on touched stories.
6. Diff the old and new workbooks cell by cell (expected changes only; other tabs unchanged) and write a change list in work/out/.
7. Commit to the master path with `expectedMtimeMs` (if refused, re-stage and redo once). Verify `shasum -a 256` on the Mac.
8. Update `work/coverage_current.xlsx`. Set the token back to "none". Append a DECISIONS line (what, counts, old sha → new sha, backup name). Update [Current state](#state) + the Changelog.

### 6.2 Mac bridge pitfalls
- The file-transfer bridge can return a **cached old copy**. After staging, confirm it is current (sha256 + size + mtime against a device listing) before using it.
- The device tools come and go. The Mac must be online with the Claude app open. If it is offline, stage the adds and list them in `work/library_adds_pending.csv` (with sha256) for a later commit.
- `device_commit_files` needs a `fileUuid` from a SendUserFile of a file staged under `/mnt/user-data/outputs/`. Agents without SendUserFile cannot commit. Commits went in batches of ≤ 25 files; `device_stage_files` takes ≤ 50 paths per call.
- `device_bash` times out at 45 s. Long jobs: write a runner to `$HOME/mnt/outputs/`, run it in steps, keep a progress file.
- Shipping code to the Mac by base64 is impractical above about 20 KB. Prefer: clean in the container → commit the outputs → verify sha.
- Deletes need permission. Don't ask: `mv` to `_to_delete/` (same subfolder layout) or `_archive/`, with an undo log.
- Add-only commits: re-check that the target doesn't exist just before committing. Use `tar -k` for bulk adds.
- Undated pages: the Mac library has no undated folder (09773, 09774 live only in work/html_clean/undated).
- Never scratch inside the Tracker library; use `$HOME/mnt/outputs`.

---

<a id="history"></a>
## 7. History (append only)
| When | Version / event |
|---|---|
| 2026-10-16…23 | Earlier chats. "Jesse Gabriel news mentions" built Jesse_Gabriel_Mentions.xlsx (742 stories) from web search, ProQuest exports and deep dives. "Chrome mentions" grew it to 1,265+ and saved about 840 reader-view HTMLs ("Gabriel press archive", named "Date - Publication - Headline", under ~/Desktop/Tracker library/) plus 488 ProQuest PDFs. Those files were later renamed to Article IDs (T18) and the library naming |
| 2026-10-24…26 | NewsBank download: 6,539 results for "Jesse Gabriel" in 329 batch PDFs of 20 with APA citations; Companion workbook; print clipping with AJG-P codes (paused after AJG-P0002 on 10-25). AJG Combined Coverage.xlsx and "NewsBank vs Tracker - Crosswalk.xlsx" are superseded: a TinyFish chat once wrote lookups into Combined by mistake, so don't build on it |
| 2026-10-26 | Master-sheet build phases C–F: Article ID per row and Story ID per story; NewsBank outlet style; Medium in the tracker's categories; bylines people only; NewsBank data wins and the tracker fills blanks; 217 Web+Print merges (exempt from the reprint rule); ID prefixes nb-/pq-/ws- (ts- → ws-), later replaced by the 5-digit scheme. The old handoff "AJG Project - Handoff Memory.md" was written then |
| 2026-10-26 | Tracker rebuilt on the Coverage tab (Jesse_Gabriel_Mentions.xlsx retired); Story ID keys; Confirmed dropped; Role column; new artifact ("Copy" kept as fallback). v6 published |
| 2026-10-27 | Phase 2/3: NewsBank text extraction, one-read tone pass (1,148), leginfo bill list (443), Reach categories, press-release exclusion, new ID scheme (5-digit / sNNNNN), author columns, cleaning of 3,497 HTMLs (10 buckets) → merged cleaner, regroup2 by text streaks (approved; first regroup abandoned), final pass (one write + library rename). **v8** 1793119028-42ac (4,130 stories) |
| 2026-10-27 | F6/F7: publisher fills, colours flattened + red rows, no reprint links, LINKUI (no print-page links, copy icons). Master moved to Desktop/Tracker library. Token cuts. **v11** 1793123501-bc1f; Insights (5 views) **v12** 1793128073-069f; Bills + Press releases sheet tabs; RELEASES-v2/RELCHECK; REORG (Press desk) **v17**; RELRULE text rule; clipping resumed then paused at 28 rows |
| 2026-10-28 | Press releases tab one value per cell (RELTAB-v1); AV tab (AVTAB-v1) + 14 podcasts; 185 new-outlet finds; cleanrows (Removed tab); review queue decided by web check; **v19** 1793153876-e0f4 (TABS-v1: Reporters, Outlets, Press releases, Bills, Story travel tabs; link rules) |
| 2026-10-28 | Release IDs + copies (RELCOPIES-v1); instruction tabs retired (OUTLETRULES-v1); code folded into sections (backendclean2); origin fixes (CalMatters); blank-field fills; AV Channel/Show split; photos embedded (PHOTOS-v2); GEOMAP, AFFIL, TONELABEL, DEFCLEAR; RELRELATED-v1; BUTTONOPT-v1 (Update button Phase 2). **v20** 1793170541-a64f |
| 2026-10-28 | **v20.1** 1793174282-172b: "Copy link to this page" removed; group subtitles removed on Reporters and Bills; tone number muted; masthead reorganized; release card dividers; RELRELATED-v2 (pre-release coverage). Master 4d7fb37c (reprint author titles) |
| 2026-10-28 | Public copy abandoned. Handoff planned; Sammy: not yet, keep this doc living |

The old Project doc "AJG Project - Handoff Memory.md" (2026-10-26) is superseded by this doc; its still-true content is merged above. Superseded parts, kept as history only:
- the old tracker copy dc44cdfe… / UCat3jW8… and its trigger trig_01Wg3NS6hNteZq4hwQTRcDay;
- "the reprint rule is not yet applied" (it was applied: regroup2 and the final pass, then the 90-day text window);
- the tracker rebuild plan (done: v6 → v20.1);
- the provenance font colours (now all black + red rows);
- the AJG-P clip naming (clips now use library names).

---

<a id="open"></a>
## 8. Open items and decisions pending with Sammy (VOLATILE)

### 8.1 Decisions pending
| # | Item | Where |
|---|---|---|
| D1 | **Press-release mapping recommendations**: 4 reviewer proposals, none approved. Quick wins: reverse links from story/bill/reporter/outlet pages to releases; use English translations; sibling releases + milestone labels; PublicNow reposts as copies (overrides DECISIONS 133, needs OK); a Related count column. Medium: tracker stories that reprint releases count as pickups; bill named in text but not tagged; "later coverage of the bill" section; later quotes. Needs a decision: other organizations' releases; a District/community Issue label | work/tmp_relaudit_1..4/proposal.md (synthesis in coordinator chat) |
| D2 | **Bills group subtitles** were removed by coordinator mistake in v20.1: keep removed or revert? Also: should Outlets / Press releases lose theirs? | v20.1 (agent-v20b-subtitle) |
| D3 | **Scheduled-task replacement prompt**: approve the text, then a supervised run, then enable | work/tmp_agent-buttonopt2/scheduled_prompt.md |
| D4 | **Per-release coverage search** for the button (gap G1); resume the pr00244 Sepulveda coverage search? | status/agent-pr244.md |
| D5 | 13 new origin pairs (review items 18-origins-3, origin-172..184, proposed "Keep as separate stories"), plus 93 medium + 79 low origin items (18-origins, 18-origins-2) | review queue |
| D6 | Old-window story merges (G4): show the merge list before any Story ID change | BOARD NEXT-REGROUP |
| D7 | "Uses release text" tag + extra release columns: deferred | DECISIONS 170, 176 |
| D8 | McClatchy no-copy rows (~380, no Publisher link): how to get copies | DECISIONS 171 |
| D10 | **rp-copies sheet write (RELCOPIES-v2) prepared, not committed**: Mac bridge was offline. Commit only after sheet_task.py (`_rel_mark`) and build/tabs/releases_data.py read the renamed columns, ideally with the publish that ships them; re-stage the master, re-run work/tmp_rp-copies/write_wb.py + diff_wb.py on it (and on the latest release_related.json) | status/agent-rp-copies.md |
| D9 | DB carry-over on migration: export + re-seed (team notes, queued edits, review decisions); kit export step proposed to agent-handoffkit | [0.5](#db) |

### 8.2 Comment threads open
| # | Thread | State |
|---|---|---|
| C1 | 9eb75f10 table corner | Couldn't reproduce in Chromium; asked Sammy for his browser and width |
| C2 | de9c2baa stray "· ·" separator (06_story_sheet detail line: an empty reach span still gets separators, e.g. "ABX1-4 page › · · Podcast") | Queued v21 |
| C3 | d38d2b91 bill chips in the Press releases list rows (bill numbers are plain text) | Queued v21 |

### 8.3 v21 queue (build/phaseB_inbox.md "## v21 queue" and after)
- Strip provenance lines from copies (e.g. s00002 "Saved 2026-10-28 (CalMatters original page, agent-calmatters)"), all types.
- Fix the separator in the detail line (C2).
- s01819 FOX40 copy is the wrong page (listing) → RETRY; also s03489, s03780, s04178 (listing/wrong AV pages).
- **S1 Storage**: about 250/256 MB → repack/trim old img shards before the next big update.
- s04422 KQED may be an ungrouped reprint of s00639 → review queue.
- Bill chips in the release list (C3).
- AFFIL station-syndication rule (G6).
- Carried-over follow-ups from the inbox:
  - s01426/s01548 empty NewsBank copies (dupes of s03947/s04061?);
  - s01619 ProQuest fused words;
  - 08938 VBS gala page not a video;
  - 08984 GMA3 typed Web story;
  - suspicious copies 08480 (42 words), 08984 (40), 09203 (34,512);
  - language check of the 185 new-outlet rows (all labelled English);
  - 09772 Mac library file still has the old header date;
  - 09600 points at its reprint's file;
  - about 12 file names shared by more than one cell;
  - 10 jg- orphan files;
  - 09773/09774 undated (no Mac file);
  - 14 podcast Publisher-link hyperlink mismatches;
  - library rename for rows that kept old o/r / -s suffixes;
  - s04710 KRON4 banner logo;
  - FIXED: apply_all `--check` failing on a scratch copy (code/apply_fills.py missing). agent-v20-integrate made `--check` copy the PY_CHECK files, and it passes.
- CalMatters cleaner rules are present in code/clean_rules.json, and releases.js has `EV.pre` (v20.1). Nothing to do; listed so nobody redoes them.

---

<a id="glossary"></a>
## 9. Glossary
| Term | Meaning |
|---|---|
| L | The coordinator's lib folder (repo root) |
| Master / the main sheet | `~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx` |
| Library | `~/Desktop/Tracker library/` (saved copies) |
| Original / Reprint | A story's first-ranked row / a row whose text passes the reprint rule against it |
| Reprint (unverified) | Listed by the old tracker's "also" text, never text-checked; not shown |
| Story ID / Article ID / Release ID | sNNNNN / 5-digit / prNNNNN ([3.1](#model)) |
| Text rule / string-of-text rule | ≥ 25-word runs covering ≥ 90% of both texts |
| Originals order | Ranking that picks the Original (reprint_rule tiers + ORIGINCREDIT) |
| Rule 7 | README's workbook-write procedure ([6.1](#write)) |
| Writer token | work/WORKBOOK_WRITER.txt |
| Sheet task | The scheduled Claude task that writes the workbook and republishes (sheet_task.py + sheet_task_prompt.md) |
| Pipeline | The tracker's published `pipeline/` folder that rebuilds the page |
| apply_all | code/apply_all_patches.py |
| BLOCKED – TinyFish / RETRY – TinyFish | File name placeholders: blocked/paywalled vs other bad fetch |
| Red row | Row not shown in the tracker |
| CSL | California State Library (NewsBank/ProQuest access) |
| Release copy | A cleaned saved copy of an official release |
| Related / Possibly related / Later coverage / pre | RELRELATED tiers 1 / 2 / 3 and evidence types on release pages |
| Channel / Show | AV carrier vs program name |
| AFFIL | Reporter-affiliation rule (Originals only) |
| Markers (XXX-vN) | Change tags in code and DECISIONS (e.g. BUTTONOPT-v1, RELTAB-v2) |
| Review queue | Artifact 8yp4a5q8A8PcrQFdYcXPuB where Sammy decides items |
| Coordinator | The chat that dispatches agents; "main" |

---

<a id="sources"></a>
## 10. Context this doc relies on
| Source | Path |
|---|---|
| Coordinator context (authoritative for accounts, URLs, preferences, open items) | L/handoff_ctx_main.md |
| Protocol | L/README.md |
| Data contract | L/CONTRACT.md |
| Decisions (later lines win) | L/DECISIONS.md (221 lines at this version) |
| Task board | L/BOARD.md |
| Tone rubric | L/TONE_GUIDE.md |
| Cleaning playbook | L/build/clean_playbook.md |
| Phase B inbox + v21 queue | L/build/phaseB_inbox.md |
| v20 brief (ownership, docs rule) | L/build/V20_BRIEF.md |
| Sheet-task prompt | L/code/sheet_task_prompt.md |
| Scheduled-task replacement | L/work/tmp_agent-buttonopt2/scheduled_prompt.md, handoff.md |
| Status logs used | L/status/coordinator.md, agent-v20-final.md, agent-v20b-subtitle.md, agent-v20-channel.md, agent-v20-projdocs.md, agent-relpre.md, agent-pr244.md, agent-buttonopt2.md, agent-prune.md (+ grep across status/ for Mac pitfalls) |
| Code read | L/code/tracker/41_update_search.js, 42_update_buttons.js, code/assemble.py, code/apply_all_patches.py, build/build.sh, work/tmp_agent-v20-final/make_publish2.py + publish2.json |
| Workbook facts | L/work/coverage_current.xlsx (sha 4d7fb37c…, read-only header/count scan); L/work/next_prid.txt; L/work/WORKBOOK_WRITER.txt |
| Memory (Project) | /projects/01a1413e-…/areas/ajg-coverage-workbook.md, areas/newsbank-print-clipping.md |
| Old handoff | Project doc `claude/AJG Project - Handoff Memory.md` (2026-10-26), via main's extract L/handoff_old_extract.md |
| DB collections | grep of `collection('…')` in code/tracker/*.js, build/tabs/*.js, build/review/index.html |
| Handoff kit | L/handoff_kit/ (publish/, source/, KIT_README.md), built by L/code/make_handoff_kit.py |

---

<a id="maintain"></a>
## 11. Maintaining this doc
This is a living doc (Sammy, 2026-10-28). Keep the anchors (`<a id="…">`) and section numbers stable. Add subsections rather than renumbering.

| On this change | Who | Update |
|---|---|---|
| Any rule, data or behaviour change | The agent making it | Append a DECISIONS.md line; HANDOFF [Changelog](#changelog) line + the affected stable section(s) |
| Data shape change (columns, blocks, run/result keys, file names) | That agent | CONTRACT.md + HANDOFF [2.1](#tabs) / [3](#model) / [5](#update) as affected |
| Workbook write | The writer agent | DECISIONS line with old → new sha + backup; HANDOFF [Current state](#state) (sha, counts, next IDs); Changelog |
| Publish | The publishing agent | [Current state](#state) (version, page sha, file count, storage); [7 History](#history) row for a named version; Changelog |
| Task started/finished | Coordinator | BOARD.md |
| New open question / answer from Sammy | Coordinator | [8 Open items](#open) (add or strike), DECISIONS for the answer |
| New account-specific id (artifact, trigger, connector) | Coordinator | [0.4](#ids) + [Current state](#state) |
| After each publish | Coordinator (main) | Sync HANDOFF.md + README/CONTRACT/DECISIONS/BOARD to the Project; copy docs to Tracker library/_docs/ |
| After EVERY publish: regenerate the kit | Coordinator (main) or the publishing agent | 1. Save the verbatim Artifact list scope "files" output to `build/handoff/live_listing.txt`. 2. `python3 -I code/make_handoff_kit.py record --listing build/handoff/live_listing.txt --map <this publish's map.json>`. Exit 2 means some files did not resolve: read the paths in `build/handoff/need_fetch.json` with Artifact `read` `paths` (out_dir work/handoff_fetch), then rerun with `--fetched work/handoff_fetch`. 3. `bash build/build.sh --kit`. 4. `python3 -I code/make_handoff_kit.py verify` on an unzipped copy. 5. Update the kit facts in [0.3](#start) (version, part sizes) and add a Changelog line |
| DB export (only when migrating) | Coordinator | Run `source/db_export/EXPORT_CHECKLIST.md`, then rebuild the kit so KIT_README carries the counts |

Rules for editing: facts with ids, paths and numbers; no secrets or credentials; no article text; mark anything not checked as [unverified]; where this doc and DECISIONS disagree, DECISIONS wins, so fix this doc.

---

<a id="changelog"></a>
## Changelog
- 2026-10-28 · rp-button · RELBUTTON-v1: release check first + oldest-5 + dual-post merge, release pickup searches (`_release` finds), sheet_task renamed-column reads (reltab.col), relcopy near-copy / PublicNow title rules + untestable-wire unmark + reprint guard (backend #4) for new rows, dual posts one row (#6), derived tab columns recomputed every run (`--release-related`, `--after-relmatch` pass), review-queue feed (nearcopy / billtags), copies_needed −14..+90, reltab.RELATED_TYPES = relmatch tier 1. Prompt: out1.xlsx → build_data → relmatch → --after-relmatch → commit; relcopy.py in the pipeline list. Tests: build/tests/sheet_task/test_relbutton.py 44/44 (+ test_sheet_task 50/50, test_auto 35/35). Section 5 updated.
- 2026-10-28 · rp-ui · RELUI-v1 + RELIMG-v1: Press releases tab rebuilt to the UI review (Read release button + plain viewer, section order, ⓘ tooltips from a rules table in tab-releases, per-row evidence tags, Later coverage / Other releases on this bill / milestone / Joint with / Others named, list columns and merged filters); releases_data.py adds `rules` + `bc`, reads Copy story ID 1/2, empties r[url][4] (block 149.7 KB); make_copies moves release photos to img shards; 01_authors.js anchor/laterquote labels + relHits → Press releases tab. 3.3, 3.11 updated.
- 2026-10-28 · rp-clips · RELCLIPS-v1 + RELSES-v1: Clips badge, "Press release" filter (Ran release text / Related to a release / No release) and CSV columns (From / Related press release + link + how) cover every release relation via relsOf (02_state.js, 15_checks.js, 21_manage_badge.js); Bills page lists only own-session releases from rp-threads thr (build/tabs/bills.js; AB 418 2023–24 24 → 13); bills/reporters/outlets tab tests updated (not run). Facet buttons / relHits / panel badge row need the handoff patch in 04_facets, 01_authors, 06_story_sheet (work/tmp_rp-clips/handoff.md).
- 2026-10-28 · rp-match · RELRELATED-v3: code/relmatch.py (translations, bills named in text, nearcopy, anchor, tier-3 later / laterquote, AV transcript quote, --update dedupe + per-story recompute = full run); code/release_related.json regenerated (1,223 related / 62 possibly / 121 later; was 1,064 / 152 / 0); 50 tests (work/tmp_agent-relrelated/test_relmatch.py); contract build/relplan_contract.md "rp-match"; 3.3 updated.
- 2026-10-28 · rp-copies · RELCOPIES-v2 + RELTAB-v3: code/relcopy.py (near copies ≥ 50% of a ≥ 250-word release; PublicNow title-prefix reposts), reltab.py renamed copy columns + Related count / Related story IDs + col()/related_values()/first_copy_date(), release_pickup_data v3.2; 22 new copy stories (14 near copies, 8 PublicNow), pr00182 copy → s04749, 18 "District / community" Issues, First copy date recomputed. Sheet write prepared from 4d7fb37c, not committed (8.1 D10). Sections 2.1, 3.3, 8.1.
- 2026-10-28 · rp-reverse · RELREVERSE-v1 + BILLSLUG-v1: story panel "From press release / Related press release: <title> ›" for every story related to or a copy of a release (01_authors.js relIndex/relsOf/relLine; ctx.rels in 53_tabs.js); Bills page release titles → release page, "Press releases N ›" → list filtered by bill (+ session dates); Reporter/Outlet pages "Press releases" fact; bill numbers link on first view (53_tabs.js register redraws a page drawn before bills.js registered). Contract: build/relplan_contract.md "rp-reverse".
- 2026-10-28 · rp-threads · RELTHREAD-v1: new code/relthread.py; build/tabs/releases_data.py emits tab-releases `thr` (threads on bill + session incl. inherited / renumbered, follow-up and similar pairs, milestone label, Others named people table, Joint with). Data only; UI is rp-ui. Other organizations' releases dropped per Sammy. 3.3 and 4.1 updated. apply_all needs PIPELINE 'relthread.py' (handoff to main: work/tmp_rp-threads/handoff.md).
- 2026-10-28 · agent-handoffdoc · 0.3 now describes the real kit (record → build.sh --kit → verify; 5 parts, 363 MB; BATCHES.json 6 publishes with the page last; db_reseed.py + EXPORT_CHECKLIST; build/handoff/project_memory.md); notes that the kit keeps the old trigger id and URL by design (swap per 0.4); section 11 gains the regenerate-after-every-publish step; [unverified] on the kit removed.
- 2026-10-28 · agent-handoffdoc · Merged the old handoff (handoff_old_extract.md): background history rows, Sammy's older rules, blocked sites, TinyFish costs, styling, clutter rule, NewsBank text/docref notes (3.14), stale-copy bridge pitfall, superseded items. Added 0.5 DB carry-over (collections + export/re-seed) and the connector display-name rule; apply_all --check marked fixed.
- 2026-10-28 · agent-handoffdoc · First version, written from handoff_ctx_main.md, README, CONTRACT, DECISIONS (L1–221), BOARD, TONE_GUIDE, clean_playbook, phaseB_inbox, V20_BRIEF, status logs and code. State: live v20.1 1793174282-172b, master 4d7fb37c.
- 2026-10-28 · agent-rp-queue · Review queue db: new items/19-billtags (112 items billtag-000..111, cat "billtags": 105 stories text/quote/topic-related to a Gabriel bill release with no bill tag + 7 untagged stories at cosine ≥0.25 to a bill release 0–30 d earlier; "Add" proposed for 54 where the story names an authored bill of the same session, else "Leave untagged"; 34 multi-bill items are multi-select; 13 candidates dropped because the release's bills aren't his bills that session) and items/20-nearcopy (23 items nearcopy-000..022, cat "nearcopy": stories ≥60% release text, 12 ≥80%; proposed "Keep as a story"). Page CATS labels for billtags/nearcopy/origins prepared in work/tmp_rp-queue/page_edit.json, NOT published. Basis: work/tmp_relaudit_3 pairs + master coverage_current.xlsx Bills; script work/tmp_rp-queue/build.py.
