# agent-review-multi — 2026-10-27

Task: review queue page supports multi-answer items. File: lib/build/review/index.html. Published as Version 4 of https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB (db capability carried forward). No db data, Mac or workbook touched.

## Changes
- `"multi": true` items render a wrap-row of checkbox chips (`fieldset.chips`, ids `c-<id>-<n>`, `label for`, focus ring via `:has(:focus-visible)`). Pre-checked from saved choice (string → one-element list) or `proposed` list.
- Save for multi stores `{choice: [checked, in option order], note, at}`; zero checked → inline "Pick at least one." (red, no write).
- Single items unchanged (select). Lookups switched from querySelector('#s-'+id) to getElementById (safe for any id chars).
- Bulk "Accept all high-confidence proposals": shown on any tab where an item has `conf`; acts on the current tab; saves the proposed list for multi items.
- "Proposed:" joins lists with " + ".
- Tabs: CATS order first, then any item category missing from CATS, labelled with its key. If the current tab has no items, the first tab is selected.
- CATS block not edited (no "relabel" entry existed at edit time or at publish; re-checked both times).

## Tests
- `new Function(script)`: syntax OK.
- jsdom 24.1.0 harness (scratchpad/jt/test.js), stub db, 3 reach multi + 1 role single + 1 unknown "relabel" multi: 16/16 PASS.
- Post-publish: ArtifactData list on "decisions" answered (5 docs read, nothing written).

## Note
- Saved decision reach-001 has choice "Spanish-language & ethnic" (with Sammy's note asking for the Ethnic split). If the reach items are re-seeded with the new labels, that legacy value matches no option, so no chip is pre-checked; the item still shows as Saved.
