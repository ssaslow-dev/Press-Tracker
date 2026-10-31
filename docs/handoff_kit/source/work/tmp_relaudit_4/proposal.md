# Press releases tab: mapping audit (reviewer 4)

Data: the master sheet, the v20 build (4,103 stories, 241 releases) and `release_related.json` (1,212 pairs). Scripts are in this folder.

**Baseline.** 174 of 241 releases have related stories, 88 have copies, and 41 have neither. A loose hand check of all 41 (cosine ≥ 0.15, −14..+30 days) found 3 real misses: pr00244 (fix in progress), pr00232 → s01944 and pr00219 → s02146. The other 38 have no coverage. The bigger gaps are where links are shown and how releases link to each other.

## Ranked improvements

### 1. Reverse links: show related releases on story, bill, reporter and outlet pages (S–M)
- **Problem:** A story panel only shows "From press release" when the story *is* the release (Tracker release ID). The 1,212 evidence links, covering **942 tracker stories**, appear only on release pages. On a bill page the release title is a plain `<span>` (bills.js:275): 322 bill–release rows, none of them linked. outlets.js and reporters.js never mention releases, though related stories come from 518 bylines and 333 outlets (e.g. Sacramento Bee 32, LA Times 30), and 21 outlets ran 112 copies.
- **Rule:** Invert `tab-releases.rel` (story → [prid, type, lag]). Add a "Related press releases" line to the story panel, link bill-page release titles to `#press-releases/<prid>`, and show "Releases covered / copies run" counts on reporter and outlet pages.
- **Gain:** 942 stories, 322 bill rows, and 851 reporter and outlet pages gain links.
- **Risk:** None new, since these are the same evidence links shown in reverse.

### 2. Release threads: "Other releases on this bill" plus bill stage (S–M)
- **Problem:** The pr00232 page ("Legislature passes Second Chance Sports Act") doesn't link to pr00215 (announced), pr00222 (Assembly passed) or pr00241 (enacted). 63 bills have two or more releases. 133 release pairs (130 releases) share a bill within 120 days with cosine ≥ 0.15, or have cosine ≥ 0.35 without a shared bill (7 pairs, e.g. pr00127/pr00132 for New Economics for Women).
- **Rule:**
  - Match on bill **plus session**. Count December of even years as the next session. 49 release–bill pairs are background mentions of an older session's bill (AB 418 is named in 24 releases), so keep those out of threads.
  - Label each release with its Bills-tab milestone within ±3 days. 143 of 296 pairs match (Chaptered 46, Passed both houses 26, Assembly floor 22).
- **Gain:** 130 release pages gain a thread, plus a stage label in list rows.
- **Risk:** Low with session matching. Show the no-bill cosine links as "Similar releases".

### 3. Use the English translations for non-English stories (S)
- **Problem:** The "Possibly related" tier (152 pairs) exists because the cosine test only reads English. But 133 of those stories have `text_en`.
- **Rule:** Run the topic test on `text_en`/`hl_en`. Pairs that pass become Related, type `bill`. Also run the `topic` test (cosine ≥ 0.25) on `text_en`.
- **Gain:** **86 pairs** move up from Possibly related to Related, plus **20 new** topic links (Telemundo, Univision and La Opinion on pr00187's looting bill; SFV Sun on pr00158).
- **Risk:** Low. One questionable case in 20 (a CALmatters piece on the shutdown).

### 4. Bill follow-on tier: coverage until the next release (M)
- **Problem:** The same-bill rule stops at 7 days. Widening it naively to 30 days adds 290 pairs, but most of them attach stories to the wrong stage. For example, "Newsom signs" stories got pinned to the pr00203 "Legislature passes" release.
- **Rule:** Same bill and session, 8–30 days after the release, *before the next release on that bill*, and text cosine ≥ 0.14. Show this as a separate tier, "Later coverage of this bill", not as Related.
- **Gain:** **112 stories on 42 releases**, e.g. pr00232 → s01944 (CBS Sacramento, +24 days, cosine 0.43). In a hand check, 12 of 15 were right.
- **Risk:** Medium (about 20% false). Misses so far are local spin-offs and profiles (s00799 San Clemente council, s01954 Consumed profile). That's why it belongs in its own tier.

### 5. List rows: add a Related column (S)
- **Problem:** The list has only a "Pickups" column, so **112 releases show 0** even though they have related stories. Related appears only as a facet.
- **Rule:** Add a "Related" count column. Optionally make the Issue label clickable, as Bills already are.
- **Gain:** 112 misleading zeros fixed. **Risk:** none.

### 6. Untested wire copies sitting in the tracker as stories (S)
- **Problem:** 8 PublicNow tracker stories have no saved text, so the text rule couldn't test them. Their headlines are Gabriel's own release titles cut off with "…", dated the same day or the next. Examples: s02146 = pr00219, s01874 = pr00243. PublicNow is on Sammy's pure-release wire list.
- **Rule:** For release-wire outlets only, a truncated headline that is a prefix of the release title (similarity ≥ 0.64), dated 0–1 days after, makes the row a copy. Queue it for Press release = Yes.
- **Gain:** 8 releases gain a copy, and 8 non-stories leave the tracker. **Risk:** Very low.

### 7. Other organizations' releases on the same action (M, needs Sammy's OK)
- **Problem:** 388 Press release = Yes rows are third-party releases (Governor, EWG, Giffords, AG). They are excluded from the tracker, so no release page shows them. 61 of these stories share a bill with a Gabriel release within ±3 days (58 releases). Example: pr00238 matches TNS "Newsom Signs Bills to Push Back on Trump's … Immigration".
- **Rule:** A collapsed section, "Other releases on this", with the sheet rows only, never counted as coverage.
- **Gain:** 58 releases. **Risk:** Governor "Legislative Update" roundups match several releases (s00020 matches 4), so require a bill in the headline or a release text cosine ≥ 0.2. DECISIONS line 35 excluded these rows, so ask first.

### 8. Sheet: related-story columns (S, needs Sammy's OK)
"Coverage stories linked" counts copies only. Add "Related stories (count)" and "Related story IDs" to the Press releases tab. The tab is a static snapshot, so this needs Sammy's say-so.

## Checked, low value
- **Bills inside releases:** none missing. A regex over every release text found no bill number absent from the Bill columns.
- **AV:** fine. 168 of 466 AV stories are already related. The 15 unlinked same-bill-week items are law roundups, correctly left out.
- **Issue fill:** 17 of 28 blank Issues could be inferred, mostly as "Other / roundup".
- **People named / contacts:** there is no person page to link to. At most, make names run a Clips search.
- **State drift:** a fresh relmatch run gives 1,217 pairs vs 1,212 in the state file (5 new). Re-run it at the next build.

## Quick wins vs bigger changes
- **Quick (S):** 1 (bill-page links and story-panel line), 3, 5, 6, plus a relmatch re-run.
- **Medium:** 2 and 4, which both need a bill+session thread index. Build it once and both use it.
- **Needs Sammy:** 7 and 8.
