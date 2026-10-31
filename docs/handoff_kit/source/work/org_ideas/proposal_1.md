# Proposal 1 — organise around a press secretary's week (agent-org-1)


## Findings
- Data: 28 cards in 9 sections under one period picker plus "Copy brief". It works as a monthly report, but it is 8,800 px tall on desktop and 15,000 px on a phone.
- Insights: 5 all-time views, organised by dataset rather than by task. Reporters, bills and reprints each appear in both tabs.
- Home shows the same 3 negative stories twice. The "New since your last visit" card is in the code but hidden.
- Press releases shows 72 releases, only those with a run in Coverage. The "Press releases" tab holds all 244, so releases with no pickup never appear.

## Proposed structure
Top tabs: **Home · Clips · Report** (renamed from Data) **· Press desk** (renamed from Insights). Manage stays a header button.

- **Home = morning clip check:** tiles; Needs attention (negatives get a "Respond" link); new since last check; 90-day tone mix bar.
- **Clips** unchanged, plus a "Since last check" quick filter; with "Copy clips list" that is the morning clips email.
- **Report = monthly report to the boss:** "Last month" period preset; collapsible sections in report order: Summary (brief + Compare) · Volume · Issues & bills · Reach & outlets · Tone · Local & languages · Gaps · Seasonality.
- **Press desk = what to do next.** One view per workflow. Each view opens on a question and ends in an action (copy, CSV, or open in Clips):
  1. **Pitch**: "Who should I pitch on X?"
  2. **Releases**: "How do releases like this one do?"
  3. **Bill push**: "What happened to this bill and who covered it?"
  4. **Respond**: "How bad is this negative story?"
  5. **Trace**: story travel

## Mapping (every existing card/view)
| Now | Goes to | Action | Effort |
|---|---|---|---|
| Home tiles, Needs attention | Home | Keep; add "Respond" link on negatives | S |
| Home "New since your last visit" (hidden) | Home | Restore it or don't; Sammy's call (see note) | S |
| Home Tone 90d + "Latest negative coverage" | Home | Keep the mix bar; **cut** the repeated list | S |
| Report header, The brief, Compare two periods | Report › Summary | Keep; add "Last month" and "month vs prior month" presets | S |
| Coverage by quarter | Report › Volume | Keep | — |
| Issues, Biggest news moments, Issues by year | Report › Issues & bills | Keep | — |
| Bills in the news | Report › Issues & bills | Keep; rows open Press desk › Bill push | S |
| Bills over time | — | **Cut** (Bill push does it better, per bill) | S |
| Reach, Top outlets, Format | Report › Reach & outlets | Keep (Format collapsed) | — |
| Most reprinted, Which issues travel | Report › Reach & outlets | Keep; Most reprinted rows open Trace | S |
| Top counties (map) | Report › Local & languages | Keep | — |
| By language + Top outlets in other languages | Report › Local & languages | **Merge** (click a language to see its outlets) | S |
| Share over time, Latest clips in other languages | Report › Local & languages | Keep | — |
| Counties gone quiet, Issues gone quiet | Report › Gaps | Keep | — |
| Outlets gone quiet, District & Valley outlets | Press desk › Pitch | **Move** (a re-engagement list is pitch work) | M |
| How it read (tone mix + latest negatives) | Report › Tone | Keep the mix; the list becomes "N negative this period → Clips" | S |
| Tone by issue (Insights) | Report › Tone | **Move** (quarterly trend is report material); keep `issue=` deep link | S |
| Reporters bar card (Data) | — | **Cut**; replace with a link to Pitch | S |
| Outlet relationships | Press desk › Pitch | **Move** as "Reliable outlets" | S |
| Busiest months of the year | Report › Seasonality | Keep, collapsed | — |
| Reporter outreach list (Insights) | Press desk › Pitch | **Merge**: becomes Pitch's table, with "All reporters" kept as a toggle | M |
| Press releases (Insights) | Press desk › Releases | Keep; extend to all 244 | M |
| Bills: timeline + at a glance (Insights) | Press desk › Bill push | Keep; add panels below | M |
| Story travel (Insights) | Press desk › Trace | Keep; also embedded in Respond | S |

## What's new, and why a press sec would use it
- **Pitch** (M). Filters: issue or bill, plus a window (default 12 months). The list ranks reporters active in that window, showing stories on that issue, last story, average tone and outlet, and flags "last story > 12 months ago" so stale names drop down. Alongside it: reliable outlets, outlets gone quiet in the last 90 days, and the outlets that ran his past releases on this issue.
  - Actions: Copy names, CSV.
  - Data limits: only people bylines count, and authors are known for just 2,930 of 4,121 stories. **No contact details exist**, so it can't produce an email list.
- **Releases** (M).
  - Feed the view from the 244-row "Press releases" tab via `ctx.read_sheet`, so releases with zero pickup appear and pickup rates are honest. Today's 80% follow-up rate is computed over picked-up releases only.
  - Add a "Similar releases" strip: same issue or bill, median outlets, follow-up rate, same-day share. That is what you check before sending.
  - Caveat: follow-up means coverage came after the release, not that the release caused it. The tab is a static snapshot unless the sheet task maintains it.
- **Bill push** (M). For the chosen bill, under the existing timeline:
  - reporters and outlets who covered it;
  - its releases and their pickup;
  - "Last signing on this issue": stories in the 14 days after the prior bill's signature.
  - Caveat: the Bills tab is a 2026-10-27 snapshot, and the sheet task doesn't refresh it. Milestones for a live signing push will be stale until someone refreshes it.
- **Respond** (M–L). For one negative story (default: latest): tone note; spread so far (Trace embedded); reporter's history with him (stories, avg tone, last positive); outlet's history; the issue's tone trend; positive same-issue stories from the last 90 days to point to. Action: "Copy response brief".
  - Caveats: reprints appear only after Update database runs; no social or TV-audience data. Not a live monitor.

## Clutter to drop
The duplicate negative list on Home, the Data Reporters card, Bills over time, and the split language outlet card. All 28 Report cards start collapsed below Summary, except Volume and Issues. Press desk's "uses every story" all-time default becomes a 12-month default with an "All dates" option.

## Note for Sammy
He dropped feature (6), the "since last week" digest. Restoring the hidden "New since last visit" card, or adding the "Since last check" Clips filter, comes close to it, so ask before building either.

## Phasing
- **Phase 1 (one build, mostly S):**
  - rename and reorder the tabs;
  - Report sections and collapsing;
  - the "Last month" preset;
  - the cuts and merges in the table;
  - move Tone by issue to Report;
  - turn Reporters into Pitch (issue/bill/window filters, reliable outlets, gone-quiet outlets);
  - "Respond" links from Home, routed to Trace for now.
- **Phase 2:** Releases on the 244-release tab with similar releases, then Bill push panels.
- **Phase 3:** the full Respond view.
