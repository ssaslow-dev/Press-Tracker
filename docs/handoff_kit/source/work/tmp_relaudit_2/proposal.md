# Press releases tab: mapping audit (reviewer 2)

**Baseline.** 241 releases in scope. 88 have copies and 174 have related stories (1,060 tier-1 links plus 152 "possible"). 67 have no related story. Of those 67, 51 have no candidate under any relaxed rule, so they really have no coverage: honors, caucus statements, 2018–20 items. Bill extraction is complete: no bill in a release's text is missing from the tab.

## Ranked improvements

**1. Reverse links (S–M, no false-link risk).** The story panel's "From press release" line and the Clips badge read only the release's own Story IDs. Release stories are now left out of the tracker, so the line fires for **1 story**. The **942 stories** that relmatch links to a release show nothing about it. Those stories span 518 reporters and 333 outlets. On the Bills page, release rows link to the official URL, not to `#press-releases/<prid>`, and Reporter and Outlet pages list no releases.
*Rule:* invert release_related.json and add "Related press releases" (with the evidence label) to the story panel, Clips and the CSV. Point bill-page release rows at the release page. Add "Releases they covered" to reporter pages and "Releases they ran or covered" to outlet pages.

**2. PublicNow copies counted as stories (S, low risk; needs Sammy because it overrides DECISIONS 133).** Eight PublicNow rows are tracker stories. Each headline is the official title cut short at "…", dated 0–1 days after the release: s01874→pr00243, s01893→pr00239, s01923→pr00237, s01933→pr00236, s01935→pr00235, s02082→pr00224, s02091→pr00223, s02146→pr00219. They have no saved text, so the text rule "unmarked" them, and they went back into the tracker as Originals. DECISIONS 35 names PublicNow as a release wire. Example: pr00239 shows "Pickups 0" and lists its own PublicNow copy nowhere.
*Rule:* a release-wire outlet + a headline that is a prefix of the release title (≥5 words, −1..+2 days) = a copy. Alternatively, fetch the PublicNow text and test it. *Gain:* +8 copies, −8 non-stories. pr00219 and pr00237 go from nothing to a pickup.

**3. Use the English translations (S, low–medium risk).** 137 of the 152 "possibly related" links are stories not in English. All 137 carry `hl_en`/`text_en`, but the topic check is English-only, so they are never checked. Scored against the translation, **91 reach the 0.14 cutoff** (examples: s01233→pr00088 at 0.90, s00962→pr00130 at 0.87). Same-week topic matching on the translations also finds **20 new links**; 14 of the top 15 are plausible (s00968 protective-order law, s01220 Sally Ride highway, s02649 looting bill). `text_en` can be a summary, so links scoring under 0.14 stay "Possible" rather than being dropped.

**4. Bill named in the story text, not only in the Bills column (S, low risk).** In the −1..+7 day window there are 83 story–release pairs where the story's text names the release's bill but its Bills cell lacks it. **21 are on topic** and would become "same bill" links. About 19 are right on a hand check (s03389, X sues over AB 587; s03381, AB 28 gun tax).

**5. Shared rare words between headline and release title (S–M, ~85% precise).** Some pairs share ≥2 uncommon words between the story headline and the release title, including dollar figures and place names (e.g. "$22", "Sepulveda", "Basin"). Limits: ±14 days, and text similarity ≥0.10 or no saved text. This yields **16 pairs**, about 13–14 correct: pr00005/s01602, pr00086/s03778, pr00140/s03251 (+8 d), pr00141/s03245 (+9 d), pr00189/s02633 (no text), s03045/s00673. **Caveat for the in-progress pre-release fix:** s01827 scores only **0.142** against pr00244, and the topic rule needs 0.25. Widening the date window alone will not link it; this rule or a lower bar is also needed.

**6. Release ↔ release and release ↔ milestone (M, low risk).**
- **Other releases on this bill.** Count only Gabriel bills from the release's own session (bills cited as background are excluded). That gives 54 chains covering **144 releases**, e.g. AB 28: pr00112→pr00169.
- **Follow-ups and duplicates.** 12 release pairs ≤14 days apart have text similarity ≥0.35: pr00133↔pr00134, pr00223↔pr00224, pr00099↔pr00103, pr00080↔pr00081↔pr00082.
- **Milestone marked.** 121 of 174 releases with a bill fall 0–3 days after a LegInfo milestone of their bill (45 floor votes, 19 committee votes, 10 introductions, 46 other). Show "Marks: Assembly floor passed (53-17)". The milestone data is already in ins-bill_timeline.

**7. Other organizations' releases (M, medium risk).** 302 sheet stories are releases from other issuers (Governor, AG, EWG and others) and are left out of the tracker. **62 of them share a bill with 54 Gabriel releases** in the same week, e.g. Bonta's AB 1002 release next to pr00209. Show them as a collapsed "Other releases on this" section.

**8. Near-copies shown as ordinary related stories (S, low risk).** For **25 "uses the release text" stories, ≥60% of the story text is the release; for 12 it is ≥80%.** Examples: s00833 Del Norte Triplicate 100%, s01384 Record Bee 99%, s01172 97%. They fail the text rule's 90%-of-both test because they are condensed. Label them "Runs the release (edited)", count them in a "pickups incl. edited runs" figure, and send them to the review queue. Their copy/story status is not changed.

**9. Coverage of the same bill 8–14 days later (M, medium risk).** 43 pairs on 28 releases have text similarity ≥0.20, and 33 of those stories have no release link at all (e.g. pr00231/s01986 "California Establishes … Seal", +10 d). Attach each story only to the nearest earlier release on the same bill. Past 14 days the matches are bill-level coverage, not release coverage.

**10. Fields and list (S).**
- Issue is blank on 27 in-scope releases, mostly district honors, grants and Days of Service. Only 7 can be filled from their related stories, so Sammy should decide on a district/community label instead.
- 103 people are named, 42 of them in ≥3 releases; add a "Joint with / others named" list facet.
- Add a "Related" count column to the list (today it is only a filter).

## Quick wins vs bigger changes
- **Quick (S):** 1 (story panel and bill-row links), 2, 3, 4, 8, 10. These add about **+130 related links**, 8 copies and 942 reverse links.
- **Bigger (M):** 5, 6, 7, 9 and the reporter/outlet pages from item 1. They add release-to-release navigation and about 100 more links, but need precision checks before they ship.
