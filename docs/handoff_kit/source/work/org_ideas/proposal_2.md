# Proposal 2: information architecture and de-duplication (agent-org-2)

**Rule:** *Data* is the period record. It follows the Clips filters and period and answers "how much, where, when". *Insights* becomes **Press desk**. It is built around one person, release, bill or story and answers "who or what next". Each question gets one home, and the other tab gets a one-line link instead of a second copy.

## 1. Inventory (about 35 cards and views; rows with no overlap left out; Manage is out of scope)

| Card (tab) | Question | Overlap |
|---|---|---|
| 4 tiles (Home) | How are we doing now? | Compare two periods (same metrics) |
| Needs attention (Home) | What needs action today? | Its negative list repeats the Tone card below it |
| Tone, last 90 days + latest negative (Home) | How is it reading? | **3rd copy** of the negative list (also Data "How it read") |
| The brief (Data) | One-paragraph summary | Each section lede repeats its bullet word for word |
| Compare two periods | Up or down vs. before? | Home tiles |
| Issues | Which issues drive coverage? | Heatmap "Issues by year" |
| Bills in the news (69) | Which bills got coverage? | **Insights Bills at a glance (70)**: same list, counts differ |
| Reach / Top outlets / Format | What kind of outlets, which ones? | Top outlets in other languages; Format is rarely acted on |
| Most reprinted / Which issues travel | What travels? | **Story travel** (picker sorted by reprints; Top sources) |
| County map + Top counties | Where locally? | Story travel "Where it ran" (same title, different question) |
| By language / Top outlets in other languages / Share over time / Latest clips | Non-English coverage | 4 cards; "Latest" duplicates a Clips filter |
| Outlets gone quiet / District & Valley | Who stopped covering him? | Press-desk questions held in Data |
| How it read | Tone in period | Home Tone card, same lede repeated as the caption |
| Reporters (Data) | Who wrote most? | **Insights Reporters**. Data's version counts wires (AP) and the Insights one doesn't |
| Outlet relationships | Long-time vs. new outlets | Relationship data, but not in Insights |
| Heatmap / Bills over time / Busiest months | Explore | Bills over time duplicates Insights Bills; Busiest months is dead weight |
| Story travel: timeline / Where it ran / Top sources | How far did one story go? | Data Most reprinted / Which issues travel |
| Reporter outreach list | Who do I pitch? | Data Reporters; no issue or date filter; 1,285 rows, about 22,800px tall on a phone |

**Naming problems:** "Where it ran" is used twice. "Reporters" is used twice with different rules. Bills goes by four names (in the news / over time / at a glance / a bill's life). The Data tab's heading says "Report", not "Data". Outlet names differ between Data (old names, e.g. "CALmatters") and Story travel (current sheet names).

**Filters today:** Clips and Data share the period and facets, but Data shows only the text "Filtered to …", not the filter chips. Each Insights view has its own controls, which don't match. Only Releases can filter by issue, and none can filter by period.

## 2. Proposed structure

- **Home**: tiles (each opens Report › Compare with that pair) · Needs attention (keeps its negative list) · Tone tile, without its own list
- **Clips**: unchanged
- **Report** (renamed from Data), in collapsible sections, with a filter chip bar at the top:
  1. Summary: Brief · Coverage over time · Compare
  2. Issues & bills: Issues · Biggest moments · Bills this period (top 10 → "Open in Press desk › Bills")
  3. Outlets & reach: Reach (Format as a toggle) · Top outlets · County map
  4. Languages: one card with a Language/Outlet toggle and Share over time; "Latest" becomes a Clips link
  5. Tone: How it read
  6. Gaps: Counties gone quiet · Issues gone quiet
  7. Explore: Heatmap
- **Press desk** (renamed from Insights), with one shared bar: Issue · Since · Originals/Incl. reprints
  1. **Who to pitch**, with People/Outlets toggle. People = outreach list + Data Reporters. Outlets = Outlet relationships + Outlets gone quiet + District & Valley.
  2. **Releases**: unchanged
  3. **Bills**: Bill's life + At a glance (absorbs Bills over time)
  4. **Story pickup**: renamed Story travel; absorbs Most reprinted and Which issues travel (as a "by issue" tab in Top sources)
  5. **Tone watch**: Tone by issue + latest negative stories (the one full list)
- **Manage**: unchanged

## 3. Mapping

| Item | Action | Effort |
|---|---|---|
| Insights → Press desk; Data → Report; Story travel → Story pickup | rename | S |
| Story travel "Where it ran" → "Map of pickups" | rename | S |
| Section ledes that repeat the brief; How it read caption | cut | S |
| Home Tone "Latest negative coverage" | cut (link to Tone watch) | S |
| Data Reporters | cut → one line "Top reporters: A, B, C · Who to pitch ›" | S |
| Most reprinted, Which issues travel | move → Story pickup | M |
| Bills over time | merge → Bills | M |
| Bills in the news | top 10 + link; fix 69/70 | S |
| Outlet relationships, Outlets gone quiet, District & Valley | move → Who to pitch › Outlets | M |
| Busiest months | cut | S |
| By language + Top outlets in other languages | merge (toggle) | S |
| Latest clips in other languages | cut → Clips link | S |
| Format card | merge as Reach toggle | S |
| Old outlet names in Report | rename via Story travel's name cleaner | M |

## 4. Filters and navigation

- **Report:** show the same filter chips as Clips (reuse `renderChips`) so filters carried over from Clips are visible. They already apply there. (S)
- **Press desk:** one bar shared by all five views, kept in the hash (`#desk/bills?issue=Guns&since=365`) and passed as `ctx.filter`. Releases' own Year/Issue controls move into it. (L in total; M per view)
- **Cross-links instead of duplicates:**
  - Report entity rows link to Clips, plus "Press desk ›" where a Press-desk view exists.
  - The story panel already links to Trace and Outreach; add "Bill brief".
- **Phone:** Press desk sub-nav as a single-row scrollable segment. Who to pitch shows 25 rows with "Show more".

## 5. Recommended first phase

All S items: the renames, the dead-weight cuts, the repeated ledes, Home's third negative list, Data Reporters → link, the Report chip bar, the 69/70 fix, and the Reporters 25-row cap. This removes about 9 cards and both naming collisions without changing any module's logic.

Phase 2 (M): Who to pitch (People/Outlets) with the Issue + Since filter. This is the most useful change for a press secretary.

Phase 3: the remaining moves and the full shared bar.

**Flag for Sammy:** this overrides "Look unchanged" (2026-10-26) for Data. His new ask implies it, but he should confirm.
