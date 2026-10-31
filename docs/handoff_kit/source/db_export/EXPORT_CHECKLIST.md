# Database export checklist (HANDOFF 0.5)

Artifact databases are NOT in the published files. Before the old account closes, a Claude session on the OLD
account exports every collection below with ArtifactData `list` (every page; `get` for single docs) and saves
each doc as `L/work/db_export/<artifact>/<collection>/<doc_id>.json` (artifact = `tracker` or `review`;
a saved list page `[{doc_id|id, data}, ...]` per file also works). Then re-run `build/build.sh --kit`: the kit
copies them to `source/db_export/`, `code/db_reseed.py` writes `source/db_export/_batches/<artifact>/batch_NNN.json`
(<=50 writes each, doc ids unchanged), and KIT_README.md gets the counts.

On the NEW account: after the first publish of the new tracker / review queue and BEFORE anyone presses Update,
send each batch file, in order, as ArtifactData action `batch` to the new artifact url.

| done | artifact | collection | holds | docs exported |
|---|---|---|---|---|
|   | tracker | `runs` | Update-button run log: proposed rows, releases_new, ids, sheet lines, review lists | not exported |
|   | tracker | `edits` | queued sheet edits / removal requests (field reported) | not exported |
|   | tracker | `tones` | team tone ratings/edits per story | not exported |
|   | tracker | `authors` | author fills from saved pages | not exported |
|   | tracker | `translations` | English headlines/texts done in the page | not exported |
|   | tracker | `pages` | saved pages waiting for the sheet task (rp-/og- docs) | not exported |
|   | tracker | `reprints` | reprint docs written by runs | not exported |
|   | tracker | `notes` | team notes | not exported |
|   | tracker | `clips` | clip store | not exported |
|   | tracker | `views` | saved views | not exported |
|   | review | `items` | review-queue item docs (14-regroup…, 17-newoutlet, 18-origins-3 …) | not exported |
|   | review | `decisions` | {choice, note, at} per item: Sammy's and Claude's answers | not exported |

Old artifacts: tracker https://claude.ai/code/artifact/27f923dc-2407-40a0-b8a9-ec3dfed87ad9 (= claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv); review queue claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB.
Per-viewer browser storage (localStorage jg-tones / jg-authors / jg2-notes, IndexedDB jg-archive) cannot move.
