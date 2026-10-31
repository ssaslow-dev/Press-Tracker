# Proposal 3: at a glance, on a phone (agent-org-3)

What I measured on v15 at 390×844:
- The sticky header is 226 px, 27% of the screen. The four admin buttons sit above the tabs, and the tabs are out of thumb reach.
- Home shows the same 5 negative stories twice.
- Data is 18 screens with 35 headings. Bills start at screen 5, "gone quiet" at 13, Reporters at 16.
- Insights: Releases is 16 screens and Reporters 26. Reporters sorts all-time, so the top name (Lara Korte) last wrote about him in Oct 2024.

How long the four questions take:
- **What changed this week?** Nowhere on the page; Clips + filters, 3+ taps.
- **What needs a response?** 1 scroll on Home (good).
- **Who to call on food safety?** 4 taps, typing and a sort.
- **A quotable bill count?** 2 taps and 5 screens of scrolling.

## 1. Structure

- **Phone:** a bottom tab bar (Today · Press desk · Clips · Data) and a 56 px top bar. Update, Refresh, Spreadsheet and Manage move into a "⋯" menu.
- **Desktop:** the same tabs in the header, with the same "⋯" menu.

| Tab | Job | Sections |
|---|---|---|
| Today (Home) | 30-second read | What changed · Needs a response · Numbers to quote · Tone (one line) |
| Press desk (Insights) | act | Respond · Pitch · Releases · Bills · Story travel |
| Clips | find a story | unchanged |
| Data | the record | Report · Volume · Issues & bills · Where it ran · Languages · How it read · More charts. Each section collapses to its headline sentence. |

Every view follows the same pattern:
1. One answer sentence, with a copy icon.
2. At most 5 one-line rows.
3. "Show all" or the chart.

The Issue and Period chips are shared across Press desk.

## 2. Mapping

| Now | Change |
|---|---|
| Home KPI tiles | Keep → Today › Numbers to quote, as copyable sentences |
| Home Needs attention + Latest negative | Merge → Today › Needs a response (top 3) |
| Home Tone 90 days | Shrink to a sentence plus one bar |
| What changed | Add (new) at the top of Today |
| Data Report/brief, Volume, Quarter, Compare | Keep (Data) |
| What drove coverage, Issues, News moments, Bills in the news | Keep → Data › Issues & bills |
| Reach, Top outlets, Format, County map/list | Keep → Data › Where it ran |
| Languages (5 cards) | Keep, collapsed |
| Most reprinted, Which issues travel | Move → Press desk › Story travel |
| Outlets / District & Valley / Counties / Issues gone quiet | Move → Press desk › Respond |
| Data Latest negative | Cut (it lives in Respond) |
| Insights Tone by issue | Move → Data › How it read (it's a trend, not an action) |
| Data Who covered it + Reporters | Cut → a one-line link to Pitch |
| Outlet relationships | Move → Pitch, "Outlets" toggle |
| Issues by year, Bills over time, Busiest months | Keep, under Data › More charts |
| Insights Releases | Keep, with one-line rows |
| Insights Bills | Keep; default to bills covered in the last 90 days |
| Insights Story travel | Keep; default to the top story of the last 90 days |
| Insights Reporters | Keep → Pitch; default to active in the last 12 months |

## 3. Answer-first headlines (real v15 data, newest story Oct 24)

- **What changed:** "11 stories Oct 18–24, down from 15. Led by elections (4) and ACA 20 (2). Most picked up: CalMatters, Oct 23, 4 reprints. No negatives." Tapping it opens Clips.
- **Needs a response:** "5 negative stories in 30 days. Newest: Knock LA voter guide, Oct 11." Each row carries its tone note and copy/open buttons.
- **Respond › Gone quiet:** "LA Times: nothing since Nov 25, 2025 (28 before). East Bay Times and KQED quiet since July."
- **Pitch (Food safety, 12 months):** "154 stories. Most active: Linh Tat (Inland Valley Daily Bulletin, Oct 10), Karen Garcia, Dustin Gardiner (Politico), Rachel Bluth." Rows read name · outlet · n · last date.
- **Releases:** "Latest: Oct 2, AB 1626. 3 outlets ran it and 2 original stories followed. Across releases, 80% led to original coverage within 7 days (56 of 70)."
- **Bills:** "AB 2244: 103 stories, peak Sep 2026, latest Oct 11."
- **Story travel:** keep its current sentence ("Reprinted by 47 other outlets… 20 states or countries outside California").
- **Numbers to quote:** "604 stories in 2026 so far (as of Oct 24)" · "33% of the last 12 months' coverage ran in national or statewide outlets (210 of 646)."

## 4. Copy and share

All of these reuse `ctx.copy` and the copy-link icon:
1. **Copy sentence** on every headline. The text includes "as of <date>".
2. **Copy list** in Pitch: name, outlet, last headline and link per line. CSV stays.
3. **Share** (`navigator.share` on phone, falling back to copy) for a story or a view, using the existing `#insights/...` deep links.
4. **Copy brief** (exists). Also offer a 7-day version on Today.

Caveats:
- The data has no reporter phone or email. "Text a reporter list" means pasting names and outlets. Contact columns would be a CONTRACT change and Sammy's call.
- Sammy dropped the digest (feature 6). "What changed" is one sentence plus a Clips link, not a clip email. Ask him before giving it a copy button.

## 5. Effort and phasing

| Change | Effort |
|---|---|
| Slim header, "⋯" menu, bottom tabs on phone | M |
| Today: What changed, merged negatives, copyable numbers | S–M |
| Pitch re-default plus one-line rows plus Copy list | S |
| Releases one-line rows plus headline | S |
| Copy icon on every headline; Share | S |
| Moves between Data and Press desk; cut duplicates | M |
| Shared Issue/Period chips; collapsible Data sections | M |
| Canonical outlet names in Data. Top outlets splits "Daily News"/"Los Angeles Daily News" and "Jewish Journal"/"The Jewish Journal of Greater LA", so quoted counts undercount. Reuse Story travel's TRAVEL-v2 cleaner. | M |

**Phase 1 (no data or contract changes):**
1. Header and "⋯" menu.
2. Today.
3. Pitch re-default and Copy list.
4. Releases rows.
5. Copy icons.

Phase 1 puts all four questions within one tap of opening the page.

**Phase 2:** the moves and the rename, after Sammy approves the tab names. DECISIONS 2026-10-26 ("look unchanged") still applies to style: keep the tokens, cards and fonts.
