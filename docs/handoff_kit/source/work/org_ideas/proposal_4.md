# Proposal 4: comms strategy, "what works" (agent-org-4)

Rule: **Data = the record** (what ran, where, when; descriptive). **Insights = decisions**: what to pitch, release and push, and proof it worked. Every Insights view shows its n, ends in an action (copy, export, open in Clips), and greys out (not hides) cells with too few rows.

Counts: v15 data (4,121 Originals) and the master's Press releases tab (244).

## 1. Structure

**Data** (one period picker drives every card)
- Summary: period + Volume, Coverage by quarter, Compare two periods
- Issues & bills: Issues, Biggest news moments, Bills in the news, Issues by year, Bills over time
- Outlets & audiences: Reach, Top outlets, Format, Local coverage by county, Languages (4 cards → 1 card with a toggle), Most reprinted
- Tone: How it read + Latest negative

**Insights** (sub-nav grouped into 4 sections)
- **What works**: Issue scorecard (new) · Release ROI (rework of Press releases) · Bills
- **Audiences**: Audience mix (new) · Gaps vs priorities (new)
- **Outreach**: Reporters
- **Report**: Report builder (new)
- Drill-downs only, not in the sub-nav: Story travel (from the story panel and scorecard), Tone by issue (from the scorecard)

## 2. Mapping of existing cards and views

| Now | Action | Effort |
|---|---|---|
| Data: Report header, Volume, Coverage by quarter, Compare two periods, Issues, Biggest news moments, Bills in the news, Reach, Top outlets, Format, County map, Most reprinted, How it read + Latest negative | Keep | – |
| Data: The brief / Copy brief | Move to the Report builder; Data keeps a one-line summary | S |
| Data: Explore more (Issues by year, Bills over time, Busiest months) | Keep, folded into Issues & bills (Busiest months under Summary) | S |
| Data: Which issues travel | Merge into the Issue scorecard (a reprints/story column) | S |
| Data: 4 language cards | Merge into one card | S |
| Data: Coverage gaps (outlets, District & Valley outlets, counties, issues gone quiet) | Move to Insights › Gaps vs priorities | S |
| Data: Reporters bar list | Cut (duplicates Insights Reporters); leave a link | S |
| Data: Outlet relationships | Merge into Reporters as an "Outlets" toggle | M |
| Insights: Press releases | Rework into Release ROI (below) | M |
| Insights: Bills | Keep; add a "coverage per milestone" strip | S |
| Insights: Story travel | Demote to a drill-down | S |
| Insights: Reporters | Keep; default to active in the last 24 months, with an issue filter | S |
| Insights: Tone by issue | Demote to the scorecard's drill-down; add a yearly-bin option | S |
| Home: Needs attention, Tone last 90 days | Keep; add a link to Gaps | S |

## 3. New decision views and the data each needs

**Issue scorecard (M, ctx.D only).** One row per issue for the current session vs the prior one, or the last 12 months vs the 12 before. Columns: stories, % in national/statewide outlets, reprints/story, District & Valley stories, in-language stories, positive/negative counts, headline/op-ed. Click a row to open its tone and bill drill-downs.
- *Supported:* 2025-26 session = 1,376 stories. Last 12 months: Food safety 154, State budget 120, Antisemitism 82, Other 74, Elections 51.
- *Thin:* Guns 33, Immigration 38. Housing, Wildfire, Health, Public safety, Education, Energy, Leadership and Restaurants each have 2–16 → greyed.
- Rates and percentages hidden when n < 20; counts only.

**Release ROI (M; new block from the Press releases tab, ~20 KB).** The denominator should be the **244 official releases**, not the 72 tracker reposts. 162 releases never appear in the tracker, and the unanswered ones are the finding. Metric: original stories on the same bill or issue in the 7 days after, compared with the 7 days before (lift), plus major-outlet stories after.
- 223 releases can be checked (they have a bill or issue). 149 were followed by coverage, but 68 already had coverage in the week before. Mean stories: 5.0 after vs 0.7 before.
- By issue, which is usable:

  | Issue | Releases | Stories per release | Releases followed by coverage |
  |---|---|---|---|
  | Food safety | 24 | 20 | 96% |
  | State budget | 17 | 7.5 | 88% |
  | Guns | 21 | 6.4 | 71% |
  | Antisemitism | 54 | 3.3 | 78% |
  | Housing | 24 | 0.8 | 42% |
  | Public safety | 12 | 1.8 | 42% |
  | Education | 10 | 1.0 | 40% |

- Release type: Statement 33 releases (85%) vs Press release 186 (64%). Show it, flagged: statements react to news that is already running.
- **Fix now:** the current "Led to original coverage 80%" tile ignores the baseline. 34 of the 72 tracker releases had same-bill coverage the week before.
- **Cut** day-of-week (weekend n = 5–6; signing days confound it), word count (weak), and "outlets per release" (1.4, almost all verbatim wires: US Fed News, PublicNow, SD Jewish World) as headline numbers.

**Audience mix (S–M, ctx.D).** Reach share per session, stacked, with in-language as an overlay.
- 2025-26: CA regional 413, Statewide 292, Trade 215, National 184, Ethnic 94, International 80, Jewish 77, Spanish 34, **District & Valley 32 (2.3%)**, in-language 148.
- District coverage is the clear gap: 19 district outlets ever, 14–28 stories a year, led by Elections and Other.
- Only 146 stories have a blank Reach, so per-session shares hold. Per-month shares by tier would be noise.

**Gaps vs priorities (M; needs a priorities list).** District priorities are not in the data. The press sec ticks up to 8 priority issues, saved with the `db` capability. For each priority: stories in the last 90 days and 12 months, district-outlet stories, in-language stories, and active reporters on that beat (97 reporters had ≥3 stories in 24 months; by top issue: Budget 28, Food 23, Antisemitism 12, Guns 12, Housing 1). The 4 "gone quiet" lists sit underneath. With no list saved, the view falls back to Issues gone quiet.

## 4. Report outputs

**Report builder (L).** Presets: Month, Quarter, Legislative session (Dec 1 start), Custom.
- One page: headline numbers vs the prior period, top 5 stories (tier, reprints), wins (headline/op-ed, major outlets), audience mix, releases issued in the period with lift, bills with milestones in the period and their coverage, and negative stories with notes.
- Outputs: Copy as email (the current brief text, extended), Print/PDF, clip-list CSV (reuses the Clips export), Reporters CSV (exists).
- Honest limits: monthly volume runs 18–156 stories (Dec 2025: 18), and there are ~1–5 negatives a month. Monthly tone and issue splits show counts, with % only when n ≥ 20. The session report is the one that carries percentages.

## 5. Noise: don't build

- Per-reporter average tone (most of 1,285 reporters have fewer than 5 stories, and the means sit near 0).
- Monthly tone % by issue.
- County trends outside LA and Sacramento (1,957 stories have a blank county).
- Per-language trends beyond Spanish (235) and Chinese (106).
- Per-milestone comparisons for any bill with fewer than ~20 stories (about 15 bills qualify).

## 6. Effort and phasing

**Phase 1** (one build, ctx.D only, no new data blocks):
- Grouped sub-nav and card moves/merges/cuts (S)
- Issue scorecard (M)
- Release tile baseline fix (S)
- Reporters active/issue filter (S)
- Audience mix (S–M)

**Phase 2:**
- Release ROI on the 244-release block (M)
- Gaps vs priorities with the db capability (M)
- Report builder with session presets and print (L)
