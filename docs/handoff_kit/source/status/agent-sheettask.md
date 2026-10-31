# agent-sheettask — T5 status (2026-10-26)

**Status: done.** Deliverables:
- lib/code/sheet_task.py
- lib/build/sheet_task_prompt.md
- test files in lib/build/t5test/

## Old task
trig_01Wg3NS6hNteZq4hwQTRcDay is not in this account's scheduled-task list (paged list_triggers, including completed ones). Its duties were inferred from tracker_original.js:
- write clips, reprints, tones, authors, translations and edits into the sheet;
- delete removed stories' rows;
- save waiting `pages` (tfpages.py / merge.py / embed.py);
- write `runs/<id>.sheet = {at, line, stories, translations, bills, newbills}`, which the Refresh progress bar waits for;
- republish the tracker.

## sheet_task.py
Pure and offline: db export JSON plus workbook copy in; new workbook plus result.json out.
- **Columns:** looked up by header name, so the Role column works.
- **New rows:** from `runs[*].rows` and unwritten `reprints` docs. Originals are added first. Real IDs are the next free ws-/jg- numbers. Dedupe is by normalized Publisher, NewsBank or ProQuest link; a duplicate maps its placeholder to the existing ID.
- **Blank-only fills:** tones, authors, translations and edits fill blank cells only. A different existing value goes to `conflicts`, never written. `also` and `conf` edits are reported as unsupported.
- **Removals:** reported, not executed.
- **Pages:** written as `Saved pages (TinyFish)/<Article ID>.html`. Saved Copy?, File type and File name are filled.
- **# of reprints:** delta-updated (old count + new distinct outlets), so counts built under the Reprint info rules aren't recomputed.
- **Originals tab:** rebuilt in Coverage order, without "Search lookup (Oct 26)", with styles, widths, freeze panes and filter.
- **Colors:** every write is green 000B8A3E. New rows copy the previous row's style.
- **verify():** with pandas, every previously non-blank Coverage cell is unchanged. The only allowed exception is "# of reprints" on touched stories. It also checks that the Originals tab mirrors Coverage and that Article IDs are unique. Exit code 2 on failure.

## Test (synthetic db: 2 originals, 1 reprint of existing jg-00037, 1 reprint of a new story, 1 duplicate, tone on a blank story, tone on a new story, edit with a conflicting headline and a blank author, 1 page)
- **Snapshot:**
  - 4 rows added: ws-03866/67 (jg-04196/97) and reprints ws-03868 (jg-00037) and ws-03869 (jg-04196).
  - The duplicate was caught (it maps to nb-00111 / jg-00055).
  - 10 cells filled.
  - 1 conflict (jg-00015 Headline). Its author was filled and the edit was kept as pending.
  - # of reprints: jg-00037 went 9→10 and jg-04196 went 0→1.
  - The page was saved as ws-03866.html.
  - verify ok, 9,544→9,548 rows, Originals 4,197. All new cells are green.
- **Rerun on its own output:** 0 rows added, 5 duplicates, 0 cells, verify ok. Idempotent.
- **coverage_prepped.xlsx:** 9,686→9,690 rows, verify ok, Originals 4,298, Role present in both tabs. Next free before the test was ws-03987 and jg-04297, which matches the coordinator.
- **Runtime:** about 14 s.

## Patch 2026-10-26 (coordinator follow-ups from T4)
1. **Link normalization:** `norm_url` is now an exact copy of build_data.py's. It keeps the query string for hosts matching newsbank|oclc|google.|proquest and strips it elsewhere. Google search links are excluded from link identity for dedupe: any google.*/search URL, plus Publisher links whose Link status is "Search link only".
2. **Temporary Story IDs on reprints:**
   - `jg-NEW-*` resolves to the real jg assigned earlier in the same execution, or to one recorded in an earlier run doc's `ids` (preloaded).
   - `jg-` + 6 hex resolves to the Story ID of the row whose Tracker story code matches. Original rows win, and there is an optional `--idmap idmap.json` fallback.
   - An unresolved code is reported in `unknown_story` and not written.
   - A new Original never gets a temporary code as its Story ID; it always gets a fresh jg-NNNNN.

Tests on coverage_prepped.xlsx (lib/build/t5test/db2.json, db3.json): all pass, verify ok.

| Case | Result |
|---|---|
| New NewsBank doc-view link (new docref) | added, not collapsed |
| Existing NewsBank link | duplicate of nb-00002 |
| Google "Search link only" link that exists in the sheet | added; no false duplicate |
| Reprint keyed by code jg-7e66d6 | ws-03990 under jg-00021 (12→13) |
| Reprint keyed by jg-NEW-b-1 from an earlier run in the same execution | attached to jg-04297 |
| Reprint listed before its same-run original jg-NEW-c-9 | attached to jg-04299 |
| Unknown code jg-abcdef | reported, not written |
| Later execution, jg-NEW-b-1 from run-b's saved `ids` | attached to jg-04297 (1→2) |
| Regression (original synthetic test) | unchanged: 4 added, 1 conflict, 1 duplicate |

The prompt's step 3 should pass `--idmap blocks/idmap.json` when available. The rebuild comes after the write, so the idmap from the previous build is the one available; that's fine, because the sheet's Tracker story code is checked first.

## For the coordinator
1. **Pipeline files in the artifact.** The scheduled session runs in a fresh container without this library. Publish these as artifact files: `pipeline/sheet_task.py`, `pipeline/build_data.py`, `pipeline/assemble.py`, `pipeline/tracker.js` (the merged JS) and `pipeline/legacy_index.html` (index_original.html). The prompt fetches them with Artifact read.
2. **Saved copies keyed by Story ID.** The prompt adds new stories' saved pages to `articles/<year>.json` keyed by Story ID, with manifest entries. CONTRACT says saved copies are looked up by `code`, so T3's lookup must also accept a Story-ID key, or the pages won't show. Please confirm with agent-display.
3. **Contract fields the JS should write:**
   - **runs:** T4's runs must carry `rows` (Coverage-shaped, placeholders) for the task to pick up.
   - **pages:** `pages` docs must be keyed by Story ID, the placeholder, or the Article ID placeholder.
   - **tones, authors, translations, edits:** keyed by Story ID, or the jg-NEW placeholder for brand-new stories.
4. **"Tone rated by" format** for tracker tones is "Claude, from tracker (YYYY-MM-DD)", or "<name> (date)" for team ratings. Change it in apply_tones if Sammy prefers a different format.

## Creating the scheduled task (T8)
Use create_trigger:
- name: "AJG tracker sheet task"
- no cron (fire-only; the tracker calls fire_trigger)
- `requires_local_device: true` (it stages and commits on Sammy's Mac); folders need no setting, since `Documents/Gabriel press PDFs` is already connected
- prompt = lib/build/sheet_task_prompt.md with `{{TRACKER_URL}}` replaced by the new tracker's URL
- initiation: human_request

Then set `SHEET_TASK` in the merged JS to the new trigger id and republish. The task's session also needs the Artifact and ArtifactData tools and the remote-devices tools. Check its permission mode on the result; a run that needs approval will stall unattended.

## Open questions for Sammy
- Edits that conflict with the sheet are never written, so they stay "edited, not yet in the spreadsheet" in the tracker until he resolves them. Should a tracker edit be allowed to overwrite? The old task did overwrite.
- Removal requests are only reported. The old task deleted the row.
