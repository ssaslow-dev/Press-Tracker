# Final proposal: Report + Press desk (agent-org-synth)
Checked against the v15 render (1400 and 390 px), the code and the data. Assumes v16 (244 releases) is live.

## 1. Recommendation
Data becomes **Report**, the record for a chosen period, and Insights becomes **Press desk**: task views that each end in copy, CSV or Clips. Each question gets one home, and the other tab gets a one-line link. Phase 1 is renames, cuts and a 12-month Pitch, with no data or contract changes.

## 2. Structure
**Home · Clips · Report · Press desk.** Clips and Manage are unchanged.
- **Home:** tiles · Needs attention (the only negative list; rows link to Story travel) · Tone as one line plus the bar.
- **Report:** period picker plus the Clips filter chips. Each section collapses to its headline sentence.
  1. Summary: brief · quarter · Compare
  2. Issues & bills
  3. Outlets & reach
  4. Languages
  5. Tone
  6. Gaps
  7. More charts (collapsed)
- **Press desk:** Pitch · Releases · Bills · Story travel, plus Respond in phase 3. One shared Issue + Period bar (default 12 months); each view opens with a one-sentence answer.
- **Phone (phase 2):** bottom tabs. The admin buttons go under "⋯" (the header is 226 px, 27% of the screen). The sub-nav becomes one scrolling row, and lists show 25 rows then "Show more".

## 3. Mapping
| Now | → |
|---|---|
| Home tiles, Needs attention | Keep; add a Story travel link |
| Home Tone card's negative list | **Cut** |
| Home "New since your last visit" (CSS-hidden) | Stays hidden |
| Brief, Volume, Coverage by quarter, Compare | Report › Summary |
| Issues, Biggest news moments | Report › Issues & bills |
| Bills in the news | Same section; top 10 + link |
| Reach + Format | **Merge** (toggle) → Outlets & reach |
| Top outlets, County map | Outlets & reach |
| Most reprinted + Which issues travel | **Merge** (toggle); rows open Story travel |
| By language + Top outlets in other languages | **Merge** (toggle) → Languages |
| Share over time | Languages |
| Latest clips in other languages | **Cut** → Clips link |
| Outlets gone quiet, District & Valley, Outlet relationships | **Move** → Pitch › Outlets |
| Counties / Issues gone quiet | Report › Gaps |
| How it read + its negative list | Keep the mix; list → "N negative → Clips" |
| Reporters (Data) | **Cut** → "Top reporters: … · Pitch ›" |
| Issues by year, Busiest months | More charts |
| Bills over time | **Cut** (Bills covers it per bill) |
| Insights Reporters | **Rename** → Pitch › People |
| Press releases, Bills | Keep → Releases, Bills |
| Story travel | Keep; "Where it ran" → **"Map of pickups"** |
| Tone by issue | **Move** → Report › Tone |

## 4. New and reworked views
- **Pitch: "Who do I pitch on X?"**
  - People: name, outlet, stories on the issue in the window, last story. Anyone not active in 12 months is greyed.
  - Outlets: reliable, gone quiet, District & Valley.
  - Actions: Copy names, CSV. There are no contact details, so the list holds names and outlets only.
- **Releases: "How do releases like this do?"** A by-issue table (counts only when n < 20). A "similar releases" strip showing coverage before vs after.
- **Bills: "What happened to this bill, and who covered it?"** Defaults to bills covered in the last 90 days. Adds the bill's reporters, outlets and releases.
- **Respond: "How bad is this negative story?"** Spread so far, the reporter's and outlet's history, and recent positive stories on the same issue. Copy response brief.

## 5. Fixes found (verified)
- **Release tile overstates impact.** "Led to original coverage 80% (56 of 70)" has no baseline. Of v15's 72 releases, 45 are tagged with a bill, and 25 of those already had same-bill coverage in the prior 7 days. Show before vs after on v16's 244. "Outlets per release 1.4" is mostly reposts (PublicNow, US Fed News).
- **Bills: 69 in Report vs 70 in Insights.** The data's single "AB 787" tag (12 stories) covers two bills, one from 2021–22 (3 stories) and one from 2023–24 (9). Insights splits them; Report merges them.
- **The two Reporters lists use different rules.** Report counts wires and staff (Associated Press 22); Insights counts people only.
- **The negative list appears three times:** Home Needs attention (5), Home Tone (the same 3 newest), and Report How it read. Proposals 1 and 3 miscounted this.
- **Outlet names.** Proposal 2 has it backwards: Report already shows "CalMatters". The raw names ("CALmatters", "The Associated Press News Service") are in Insights Reporters. Report instead *splits* outlets: Daily News 80 / Los Angeles Daily News 27, and Jewish Journal 80 / The Jewish Journal of Greater Los Angeles 28. Apply Story travel's name cleaner everywhere.
- **Pitch is stale.** The top name, Lara Korte, last wrote about him on Oct 11, 2024. Avg tone reads "Neutral" for nearly everyone; replace it with a negative-story count.
- **Name clashes.** The Data heading says "Report"; "Where it ran" is used twice; Insights ignores the period.
- **Phone length:** Report 15,066 px, Reporters 22,844 px, Releases 13,640 px (before v16 more than triples the releases).

## 6. Rejected
- Issue scorecard (P4): repeats Issues + Which issues travel, and most issues have n < 20.
- Audience mix (P4): one Reach line covers it (District & Valley: 32 of 1,376 stories, 2.3%, in 2025–26).
- Priorities list saved in db (P4): new storage nobody asked for.
- Report builder (P4): Copy brief plus presets covers it.
- "Since last check" filter / restoring "New since" (P1): this is the dropped digest.
- Gone-quiet lists under Respond (P3): they are pitch material.
- Story travel as a drill-down only (P4): people look for it directly.
- "Today" tab name (P3): Home already works.
- Release type, weekday and word-count stats (P4): confounded or thin.
- Cutting Busiest months (P2): harmless once collapsed.

## 7. Phases
- **Phase 1, S (one build):**
  - renames;
  - Report sections;
  - the §3 cuts and merges, except the moves into Pitch;
  - Tone by issue → Report;
  - Home dedupe;
  - Pitch: 12 months, issue filter, 25-row phone cap, Copy names, negative count;
  - release tile before/after;
  - AB 787 split.
- **Phase 2, M:**
  - shared Issue/Period bar (a contract addition; `ctx` has no filter today);
  - Pitch › Outlets;
  - Bills panels;
  - Releases table and similar releases;
  - canonical outlet names;
  - copyable answer sentences;
  - phone header and tabs;
  - "Last month" and "This session" presets (today: All, 30d, 90d, 12m, years, custom).
- **Phase 3, M:** Respond.

## 8. Sammy decides
1. Override DECISIONS 2026-10-26 "Look unchanged" for layout and names (styles kept)? Yes/no.
2. A Home line such as "This week: 11 stories, down from 15"? It is close to the dropped digest. Yes/no.
3. Phone bottom tabs, with the admin buttons under "⋯"? Yes/no.
4. Pitch window: 12 or 24 months?
5. Build Respond, or keep Home's link to Story travel?
