# agent-queue-tidy (2026-10-28): auto-accept high confidence + page shows only open items

Sammy: "go through the coverage review queue and auto accept all high confidence proposals, then rebuild it to show nothing that's already been dealt with".
Queue https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB. Owns: decisions docs listed in work/tmp_queue_tidy/accept_ids.json; work/tmp_queue_tidy/. Items collection, sheet, Mac: not touched.

## 1. Auto-accept (done)
- Read before: 32 items docs (1,711 items, ids unique), 1,440 decisions (work/tmp_queue_tidy/before/).
- Coordinator hold (mid-task): **translation not auto-accepted**. It arrived before any write, so no translation decision was written.
- Rule: conf == "high", no decision doc, cat != translation → choice = proposed (list for multi; 5 multi billtags), note "Auto-accepted: high confidence (Sammy 2026-10-28)", by "Claude (auto-accept, Sammy's instruction)", at 2026-10-28T21:27:52Z.
- 193 creates in 4 atomic batches (50/50/50/43) using per-doc files work/tmp_queue_tidy/dec/<id>.json. No if_version, so writing over an existing doc was not possible. All came back as version 1.
- Read back (after/): 1,633 decisions = 1,440 + 193. The new set equals the plan, each matches its file, and all 1,440 earlier docs are byte-identical.

| cat | accepted | undecided left |
|---|---|---|
| billtags | 54 | 58 |
| merge | 42 | 156 |
| swap | 34 | 28 |
| verify | 31 | 2 |
| edition | 16 | 14 |
| addorig | 11 | 39 |
| split | 3 | 21 |
| uvreprint | 2 | 3 |
| translation | 0 (held; 52 high) | 55 |
| origins | 0 | 73 |
| nearcopy | 0 | 10 |
| dates | 0 | 9 |
| regroup | 0 | 6 |
| total | 193 | 474 |

Flags for main:
- 22 accepted merges are in linked groups (the item says "Linked groups should be applied together"). Some siblings may still be medium/low and undecided, so check the group before applying.
- 3 accepted swaps carry a NOTE (the story is also moved by a merge).
- uvreprint-005 is a compound call (merge s02995 into s00611, plus row moves).

## 2. Page edit (prepared, NOT published)
- Live re-read: version 1793222739-1350 (as expected). Source (<title>..</script>) = work/tmp_queue_tidy/review_page.html; full served file = live/index.html.
- work/tmp_queue_tidy/page_edit.json: 16 old_str/new_str edits, each unique in the source, applied in order → review_page_edited.html. Apply with Artifact publish url + edits; omit capabilities (db carried).
  - Decided items are not rendered. Tabs show only categories with undecided items. A tab's count is the undecided number only (no "/total").
  - The tab you are on stays visible after you clear it (items stay on screen, marked Saved). It disappears when you switch tabs.
  - When nothing is left: tabs hidden; the list reads "Nothing left to review."
  - "Show decided" / "Hide decided" link below the list: off by default, a plain variable, not stored. It shows all categories and decided items with the existing Claude tag and Update flow.
  - The "Show only items that need me" checkbox, its change handler, its CSS and the localStorage key reviewOnlyNeedsMe were removed. The page now uses no localStorage.
  - The bulk button shows only when the tab has undecided high-confidence items.
  - Fixed a phone-width overflow that was already on the live page. Long option text in a select widened the grid to 527–800px on the regroup, origins and dates tabs. The fix sets grid-template-columns:minmax(0,1fr) on .wrap, .list and .item, plus select{max-width:100%}.
- Test: Playwright Chromium, page served through a routed URL. The db is a stub loaded with the real items and post-write decisions (work/tmp_queue_tidy/t/test.js, data.json): **23/23 PASS**. Checks: tabs and counts, 474 undecided rendered and 0 decided rendered, toggle on/off, toggle not kept across a reload, no localStorage, save keeps the item and the current tab, the emptied tab is hidden after switching, bulk, the all-decided empty state, 375px with no horizontal scroll (every tab checked by wide.js), no page errors. JS passes node --check.
