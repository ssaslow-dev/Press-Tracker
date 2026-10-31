# agent-tab-bills — Bills tab module (TABS-v1)
- Read contract (+ bill-link addendum), agent-tabs Phase A, tabs_tracker.js, old bill_timeline.js/_data.py, blocks, DECISIONS.
- Wrote build/tabs/bills.js (26.6 KB), build/tabs/test/bills.test.js, build/tabs/bills.md. No _data.py, no framework/code edits.
- Tests: MOD=bills 140/140 at 1400 and 390. Shots in work/tmp_agent-tab-bills/shots/.
- Count: 63 author-led bill+sessions with coverage (69 incl. 6 coauthored); the coordinator's "70 at v18" does not reproduce from the blocks (69 = Data's billGroups on the same D).
- Addendum: billSlug(bill, {date}, ctx) exposed on the registered module for ctx.billLink.
