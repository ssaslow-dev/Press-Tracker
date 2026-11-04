# Decision archive (superseded entries)

Entries moved out of docs/DECISIONS.md by CLEANUP-v1 (2026-11-04) because a later decision replaced them. Kept word for word for history; the current rule is in DECISIONS.md under the tag named in each heading. Search by tag.

## SAMELOOK-v1 (superseded by SAMELOOK-v2)

## SAMELOOK-v1 (Sammy, 2026-10-31)
The new project's tracker looks and feels the same as the current artifact tracker (code/tracker/NN_*.js), minus the Update button functionality (40_update_outlets.js, 41_update_search.js, 42_update_buttons.js, 43_update_log.js and what they drive). Still open: how new stories reach the new project after switch-over.

## SAMELOOK-v1 amended and SAVERHOLD-v1 (hold lifted; leaving the Update button out stays temporary, see CLAUDE.md)

## SAMELOOK-v1 amended, SAVERHOLD-v1, NOWATCH-v1 (Sammy, 2026-10-31)
- SAMELOOK-v1: leaving the Update button out of the new tracker is temporary; it is to come back later.
- SAVERHOLD-v1: the save program (work/saver/) is on hold after part 2 (save path built, 95 tests pass). No replays, Fable review or live save until Sammy lifts the hold.

## MULTIPC-v1 (replaced by MULTIPC-v2)

## MULTIPC-v1 (Sammy, 2026-11-02)
The tracker folder lives on one shared office network drive; several PCs open it, and several people save. Consequences: the save's lock file (exclusive create) and checksum ledger enforce one save at a time across PCs; notes, views and edits live in the shared folder's db (not per-PC browser storage) so everyone sees them; the launcher works from mapped drives and UNC paths (pushd); each PC runs its own 127.0.0.1 server pointed at the shared folder. Accepting a hand edit as the new baseline needs an explicit confirm, since another person may have made it. To check first: the test zip run from the network drive (portable Python from a network path, exclusive locking over the share).

## UPDATESTATION-v1 follow-up 7 (photos in the station: replaced by PHOTOLINK-v1; wanted originals: dropped by NOQUEUE-v1)

UPDATESTATION-v1 (Sammy, 2026-11-02, follow-up 7): (1) Photos: Sammy wants the Update station to download each new find's HTML with its photos included, so saved copies keep photos without the PC going online. Feasibility inside a claude.ai artifact (browser security rules, the artifact sandbox, TinyFish returning text only) is being checked before building; report back if it is impossible. (2) Wanted originals (CHAINORIG-v1 `origin_wanted`): the PC puts the list in the for-Update file and the next Update in the station searches for them along with everything else; they arrive in the next update folder.

## PRJUDGE-v1 follow-up (replaced by PRJUDGE-v2)

PRJUDGE-v1 (Sammy, 2026-11-03, follow-up): only wires and official sites count as press releases; a community outlet running a release, even word for word, is coverage and stays shown. Applying the check (work/localapp/PRESS_RELEASE_CHECK.md), Sammy said "do what you think is best": Claude's call, consistent with that rule: at switch-over mark only the 4 missed wire releases (01759 US Fed News; 01190 and 01364 PR Newswire on Yahoo; 00290 GlobeNewswire on Yahoo; checked again on the real workbook first); the ~82 community-outlet posts stay coverage. Not changed: the ~261 existing Yes rows on non-wire outlets (some contradict the rule; listed for Sammy, never unmarked without his say).
