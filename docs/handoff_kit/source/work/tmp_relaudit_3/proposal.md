# Press releases tab: mapping audit (reviewer 3)

Basis: v20 build (241 releases, 4,103 stories), release_related.json (593 text, 348 bill, 77 quote, 42 topic, 152 possible), master sheet. I scored all 5,428 release/story pairs with any evidence (`scan.py` → `pairs.pkl`). The pre-release window is excluded (v2 `pre`).

Today 174/241 releases have related stories, 1 has only "possibly related", 66 have nothing, and 40 have neither copies nor related stories.

## Ranked improvements

### 1. Reverse links: story → release, outlet → release, reporter → release (quick win, S)
**Problem.** 942 tracker stories are tier-1 related to a release, and none of their story panels or Clips rows says so. `relOf()` reads only pickup sids (overlap 0). Outlets and Reporters pages have no release references.
**Rule.** Invert `tab-releases.rel`: story panel line "Related to press release: <title> (evidence)" → `#press-releases/prNNNNN`. Outlet page: "Ran N of his releases" from `rows` (21 outlets, 112 copies). Reporter page: "N stories used his releases" (153 reporters have 2 or more).
**Gain.** 942 story links, 21 outlet links, 153 reporter links. **False-link risk.** None new, since it reuses existing evidence.

### 2. Other issuers' releases on the same bill (M)
**Problem.** 388 Coverage rows have Press release = Yes but aren't copies of his releases: Governor signing releases, EWG, CSPI, Consumer Reports, the AG, Mayor McCarthy. They're saved but appear nowhere. 67 of these stories share a bill with one of his releases within −3…+10 days, which gives 59 releases and 78 pairs. E.g. s00251 ↔ pr00208, s00288 EWG ↔ pr00203.
**Rule.** Section "Other releases on this action": non-copy PR=Yes rows, shared bill, lag −3…+10, carried in `tab-releases.c` like copies.
**Hand check.** In a sample of 14, 12 were the same action and 2 were governor multi-bill roundups (s01168, s01334). **Risk.** Low. Label roundups by bill count of 3 or more.

### 3. Promote "possibly related" using the English translations already in data (S)
**Problem.** The 152 `possible` pairs are mostly non-English stories, which the cosine can't score. But 137 of them carry `hl_en`/`text_en`.
**Rule.** Run the same cosine on `hl_en + text_en`. If it's 0.14 or higher (with the shared bill and same week, as now), make the pair `bill`. Add `topic` (0.25 or higher, no bill) for non-English stories too.
**Gain.** 91 of 152 promoted, plus 19 new topic links. 4 Adelante Valle stories (s01233, s00962, s01013, s01386) are full translations at cosine 0.81–0.90; flag them "translated release". **Hand check.** 8 of 8 mid-range (0.14–0.30) pairs were on topic. **Risk.** Low. Many `text_en` are about 36-word summaries, so keep the bill requirement.

### 4. PublicNow reposts are release copies sitting in the tracker as stories (quick win, S)
**Problem.** All 8 PublicNow tracker stories (s01874…s02146) are truncated reposts of pr00219–pr00243, with lag 0–1 days and no saved text. None is linked. DECISIONS (line 35) lists PublicNow as a pure press release.
**Rule.** If a story from a release-wire outlet has a headline that is a prefix of a release title (after stripping "…") and lag is −1…+3, it's a copy. Mark Press release = Yes and link it.
**Gain.** 8 copies and 8 fewer false "stories". **Hand check.** 8 of 8 matched exactly one release. **Risk.** Very low.

### 5. Other releases on this bill and milestones (quick win, S)
**Problem.** 149 releases are on 63 bills that have 2 or more releases. The AB 1264 chain alone is 10 releases (pr00190 → pr00236). The page gives no sibling links, and list rows don't show the milestone.
**Rule.** Release siblings are releases with an exact shared bill, listed in date order. Each gets a milestone from the Bills tab: the latest milestone of a shared bill dated −3…+1 days from the release. 124 of 174 bill releases match one. Also link 69 release pairs that share 25-word runs without a shared bill (recycled statements).
**Risk.** None for bills. Text pairs need the existing boilerplate filter.

### 6. Later coverage that quotes the release (M)
**Problem.** Text/quote evidence stops at 90 or 30 days. 51 stories carry 25-word runs or 20-word quotations of a release, are dated more than 7 days after it, and are linked to no release. E.g. s00102 USA Today ↔ pr00208 (+259 d), s00228/s04325 Glock syndication ↔ pr00198 (+95).
**Rule.** A tier-2 "Later coverage quoting this release" for stories with no other release link. **Hand check.** 7 of 8 were real quotes. s03871 Spectrum only matched a standing title ("chair of the … committee"), so require at least one run of 20 or more words outside titles and bios. **Risk.** Moderate without the orphan restriction (series releases reuse text).

### 7. Bill-tag gaps on stories (M, sheet write via review queue)
**Problem.** 117 stories are related by text, quote or topic to a bill release but have no bill tag, and 87 untagged stories score cosine 0.25 or higher against a bill release within 30 days. Missing tags break the `bill` tier, the before/after counts and the Bills tab. AV is otherwise fine: 181 of 182 in-window AV pairs have text, and the 32 misses are mostly this tag gap.
**Rule.** Suggest the release's bill when the release has exactly one bill and the story is text/quote/topic related. Send it to the review queue rather than writing it automatically.

### 8. Smaller items
- **Same bill +8…+30 days at cosine 0.25 or higher.** 76 stories across 29 releases. 45 of them are already related to another release, so take only the rest, nearest release first. M, medium risk.
- **Names.** 102 named officials, 41 of them in 3 or more releases. Add an "Others named" facet and link each name to a Clips search. S.
- **Unfilled fields.** Issue is blank on 27 in-scope releases, and 8 can be filled from related stories' topics. The dek is blank on 140, but that's a property of the source. Bill columns are complete: a regex over the release texts found no missed AB/SB numbers.
- **Data flag.** s00673 (Imperial Valley Press) predates the no-posting release s03045 by 3 days, so that release's first-run date is wrong.
- **List rows.** Add a "Related" count column next to Pickups. Pickups is 0 for 153 releases, so the list reads as empty when it isn't.

## Quick wins vs bigger changes
- **Quick (S):** #1 reverse links, #3 translation promotion, #4 PublicNow copies, #5 siblings and milestones, list column. Together: about 1,060 story links (942 + 110 + 8) plus sibling links on 149 releases, with near-zero false-link risk.
- **Bigger (M):** #2 other-issuer releases (needs Coverage rows in a block), #6 later quotations (new tier and filter), #7 bill-tag backfill (sheet write, review), #8 extended window.
