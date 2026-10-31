# agent-update — T4 (Update button reports in Coverage format)

Status: **done**. Output: L/build/js_update.js (the full file, still wrapped in `<script>…</script>` like tracker_original.js). Tests: L/build/test_update/.

## What changed (all in the Update path; everything else is byte-identical to tracker_original.js)
- **New section `/* COV-BEGIN … COV-END */`**, inserted right after `reprintFor`. It holds:
  - the block loader `covLoad()` (reads `rows`, `covcols` and `idmap` from the page lazily; `COV_FALLBACK` = Coverage columns with Role last, used if no covcols block)
  - `covNormU` (the CONTRACT normalization), `covOutlet` (outlet key that ignores "The", ", The" and a bracketed credit)
  - `covHit` (link, or outlet + headline within 3 days = already a row; the same long headline from another outlet = a reprint of that row's story)
  - `covRepKnown`, `covOutletName` (NewsBank style "X, The"), `covRole` (the DECISIONS rule), `covCounty` (the county from D when every story from that outlet agrees)
  - `covRow`, `proposeRows`, `covCompact`, `covTsv`, `covResolve`
- **runUpdate:**
  - Search candidates whose link is any Coverage row are skipped.
  - A headline match against any Coverage row is either dropped (same outlet) or offered as a reprint of that row's story.
  - TV captions are skipped when their link is a row.
  - The final dedupe of finds checks `covHit` before the old `dupOf(D)`.
  - Same-run copies of a new story are kept as `r._reps`, and still also added to `also` as before.
  - Reprints the sheet already has (`covRepKnown`) are filtered out before the text check.
  - The old tests (knownIndex, dupOf, TF_WIRE, TF_GAP, rate limits, error codes) are unchanged.
- **saveFound:**
  - It now has a run id: the button run, or a new hand-run id.
  - It builds proposed rows: an Original per story that went in, Reprint rows for its `_reps`, Reprint rows for finds that `addClips` folded into an existing story, and the added reprints.
  - The rows are stored in `RA.rows`, or for hand runs saved directly in the run entry's `rows`.
  - The fireSheet text says how many rows to write.
- **runAll:** resets `RA.rows`; the run entry now saves `rows: covCompact(RA.rows)`, i.e. non-empty cells only; the fire_trigger text names the row count. `SHEET_TASK` is still one constant.
- **copyFound:**
  - TSV in `covcols` order: a header row, then every column, with blanks where unknown.
  - It covers both stories and reprints, with placeholders `ws-NEW-copy-YYYYMMDD-n` when no run is under way.
- **drawUpd:** the only visible change in the update panel. "Copy for spreadsheet" now also shows when there are only reprints, and is enabled when any story or reprint is ticked.
- **cleanRun:**
  - Keeps `rows`: up to 500 objects, string or number values.
  - Keeps `ids`: placeholder → real, with keys matching `^(ws|jg)-NEW-…` and values matching `^(ws|pq|nb|jg)-\d{5}$`.
- **Run log:**
  - A new "Spreadsheet rows" section in `runCard`. Each row is listed by `logRow` with its Article ID, Original/Reprint, Story ID, date and outlet. Placeholders show until `ids` arrive; after that the real IDs show.
  - `logItem` resolves old or temporary codes through idmap (`covResolve`).

## Decisions I made (flag if wrong)
- **Temporary codes for new stories.** In the page, a story added from a find keeps a temporary jg- + 6-hex code, made by `toRow` as before. Its row carries that code in **Tracker story code**, and its Story ID is `jg-NEW-<run>-<n>`. Pages, tones, authors and translations saved under the temporary code follow it to the real Story ID through idmap after the rebuild, because Tracker story code feeds idmap.
- **Reprints of stories not yet rebuilt.** A reprint of a story added by an earlier update but not yet rebuilt gets Story ID = its temporary code, also written in Tracker story code. **The sheet task must resolve it** by finding the Original row whose Tracker story code equals it.
- **Outlet** is NewsBank style ("Fresno Bee, The"), with no bracketed wire credit.
- **Publisher, Outlet city/state, Saved Copy?, File type/name, In Tracker?** are left blank. The sheet task fills the file columns when it saves the page; In Tracker? is left empty per the standing rule.
- **Tone rated by** = "Claude, from article excerpt (YYYY-MM-DD)", the existing style, set only when the screen rated tone.
- **Edition** = "Web".
- **Language:** English rows say "English".
- **Mentions "Gabriel" in text** = "Yes" for confirmed finds.
- **# of reprints** on a new Original = the distinct outlets among its same-run copies.
- **Role** = the DECISIONS rule (byline → headline). The classifier's role still drives the panel's dropdown.

## Notes for the coordinator / merge
- **Link-normalization problem in CONTRACT:** dropping the query collapses all NewsBank `document-view?...` links (3,780 rows) and Google search links into one key each. I exclude these from link matching (`COV_SHARED`). Any other component that matches on `rows` links should do the same, or the build should keep the query for those hosts.
- **Names I added at the IIFE top level:** COV_FALLBACK, COV_DS, COV, COV_SHARED, covBlock, covNormU, covOutlet, covLoad, covDays, covLink, covHit, covRepKnown, covOutletName, covRole, covCounty, covRow, proposeRows, covCompact, covTsv, covResolve, logRow. The display JS must not declare these.
- **I call display-owned functions unchanged:** ranIn, reprintFor, addClips, applyReprints, cleanClip, alsoNames. The display agent's `cleanClip` / `cleanReprint` validators must keep accepting jg- + 6-hex temporary codes, since new finds are stored under them until the rebuild.
- **Hunks vs the original:** about 20, all in runUpdate, saveFound, copyFound, drawUpd's footer line, runAll's saveRun and fire text, cleanRun, logItem, logSection, runCard, plus the inserted COV section after `reprintFor` (old line 1785).
- **Fresh db:** there are no old runs, so `covResolve` only matters for runs made before the next rebuild.

## Self-check
- `node --check` on the script body: OK.
- `node lib/build/test_update/test.js`: **ALL 32 CHECKS PASSED**, against the real blocks (9,686 rows, 55 covcols, idmap). It covers:
  - block loading, with Role last
  - JS/Python link normalization agreeing on every link
  - NewsBank and Google links never matching
  - a link hit, ignoring scheme, www, query and fragment
  - same outlet + headline within 3 days → already a row
  - another outlet with the same long headline → reprint of that sid
  - 9 days apart → not the same row
  - short headlines not counted as reprints
  - covRepKnown
  - outlet naming, the Role rule
  - proposeRows: column set and order, placeholder sequence, original fields, # of reprints (distinct outlets), in-run reprints, reprint of an existing Story ID, reprint of a temporary code
  - compact rows, TSV shape
  - cleanRun keeping rows and validating ids
  - covResolve
- **Not tested:** a full in-browser run (needs TinyFish and sampling in the artifact). That belongs to T6/T7.
