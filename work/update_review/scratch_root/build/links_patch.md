# Links patch (agent-links, 2026-10-27)

Scope: DECISIONS 2026-10-27, final links scope. The tracker lists only two kinds of link from the sheet: California State Library (CSL) links to NewsBank or ProQuest, and the publisher's own link. Every listed link uses the ProQuest link's element and style, on originals and on reprints, including the second ID on Web + Print rows. The saved-copy viewer is unchanged.

## How to apply
```
python3 -I code/patch_links.py build/js_merged.js build/js_merged.js code/build_data.py code/build_data.py
python3 -I code/build_data.py <workbook> work/index_original.html <blocks dir> [work/sid_map.json]
python3 -I code/assemble.py <current page shell, e.g. work/tmp_agent-write1/index_base_T14a.html> <blocks dir> build/js_merged.js <out.html>
```
(build_data.py's OLD_INDEX argument stays as before. For the shell, use whatever the current publish uses: v7's shell has the reach CSS.)
- The patch is anchored and idempotent. Each anchor has to match exactly once. An edit that is already applied is skipped. If any anchor fails, the script writes nothing and exits 1.
- It was tested on the current v7 files (js_merged.js 05:10, build_data.py 05:09; snapshots in work/tmp_agent-links/*.v7.*). It composes with agent-authorsplit's patches in either order.
- Per Sammy, it goes into the final publish. Nothing was published and no shared build file was edited.
- A rebuild is needed, because the data now carries `lk`. With old blocks, the JS falls back to link/plink/pq, so it still works.

## The model: the ProQuest link before this patch
In the story panel's `.dlinks` row, the ProQuest link was `<a href=… target="_blank" rel="noopener"><b>ProQuest via CA State Library ↗</b><span>library card login</span></a>`. Next to it was a direct `<b>ProQuest ↗</b><span>proquest.com</span>`. ProQuest links for reprints were never shown, because the reprint list showed outlet names only.

## Edits
**build_data.py** (4 edits, marker `LINKS-v1`)
1. Adds link helpers after `prec()`:
   - `csl_of()`, which builds the CSL URL.
   - `own_link()`, which checks whether a publisher link is the outlet's own site.
   - `links_of(row)`, which returns `[[kind, url], …]`.
   - Kinds and their order: `pub` (Publisher link, own site only), `nb` (NewsBank article link), `nbpa` (NewsBank print article link, the second ID), `nbpg` (NewsBank print-page link, using the sheet's CSL column), `pq` (using the sheet's "ProQuest via CA State Library" column).
   - Duplicate URLs are dropped.
2. Every reprint object gets `lk`.
3. Every original record gets `lk`. It uses sheet values only, with no fallback to the old tracker.
4. Adds `links …` counters to report.json and writes `<out>/links_not_listed.csv` (Article ID, Story ID, O/R, Outlet, Column, reason, URL).

**js_merged.js** (3 edits)
1. Adds `LINK_KIND` (labels), `linksOf(x)`, `linkA(p)` and `repLinks(r)`.
   - `linksOf(x)` returns `x.lk`. For records without `lk` (Update-button finds, reprints from the shared store), it builds the same kinds from link/plink/pq.
   - `storyUrl(r)` now returns the first listed link. "Copy link" uses it.
2. In the story panel, the old 5-line link builder ("Read at <pub>", "Original link", "ProQuest", "ProQuest via CA State Library") is replaced by `linksOf(r).map(linkA)`.
3. Under "Reprinted in:", `repLinks(r)` adds a `<details class="also replinks">` block titled "Reprint links (N)".
   - It has one `.dlinks` row per reprint that has a listed link, showing outlet · date followed by the links.
   - The block starts open for 5 or fewer rows and folded for more.
   - It uses only existing classes plus inline styles, so no CSS change is needed.

Labels, all in the ProQuest element (`<a><b>Label ↗</b><span>detail</span></a>`, new tab, `data-lk=<kind>`):

| kind | label | detail |
|---|---|---|
| pub | Publisher site ↗ | site host |
| nb | NewsBank via CA State Library ↗ | library card login |
| nbpa | NewsBank print edition via CA State Library ↗ | library card login |
| nbpg | NewsBank print page via CA State Library ↗ | library card login |
| pq | ProQuest via CA State Library ↗ | library card login (unchanged) |

Nothing else in the page changes. That includes the saved-copy viewer, the saved copy's "Full print edition (PDF)" / "ProQuest PDF" link (it comes from the saved copy, not the sheet), the table, the exports' Link columns, and dedupe.

## CSL URL pattern
- ProQuest: `https://castatelib.idm.oclc.org/login?url=<https://www.proquest.com/docview/N>`. This is the sheet column "ProQuest via CA State Library". 474 of the sheet's 474 pairs follow it exactly.
- NewsBank: `https://infoweb-newsbank-com.castatelib.idm.oclc.org/<same path and query as infoweb.newsbank.com>`. This is the sheet column "NewsBank print page article link via CA State Library". 2,133 of 2,133 pairs follow it exactly.

## Inventory: Coverage link columns (whole sheet, 9,544 rows, including press-release and blank-status rows)

| Column | URLs | Host | Via CSL? | Listed after patch |
|---|---|---|---|---|
| Publisher link | 4,543 (688 hosts) | publishers, plus aggregators, archive.org, google.com | n/a | own site only (219 of 4,543 sheet links are not; 215 of them on tracker rows) |
| ProQuest link | 474 (366 O / 108 R) | proquest.com | no | not listed directly; its CSL twin is listed |
| ProQuest via CA State Library | 474 | castatelib.idm.oclc.org | yes | listed (`pq`) |
| NewsBank article link | 3,780 (1,750 O / 2,030 R) | infoweb.newsbank.com | no, and the sheet has **no CSL column** for it | listed as the derived CSL link (`nb`) |
| NewsBank print article link (2nd ID, Web + Print) | 202 (153 O / 49 R) | infoweb.newsbank.com | no, and the sheet has **no CSL column** for it | listed as the derived CSL link (`nbpa`) |
| NewsBank print-page link | 2,133 (155 O / 507 R / 1,471 blank-status) | infoweb.newsbank.com | no | not listed directly; its CSL twin is listed |
| NewsBank print page article link via CA State Library | 2,133 | infoweb-newsbank-com.castatelib.idm.oclc.org | yes | listed (`nbpg`) for O/R rows. The 1,471 blank-status rows aren't in the tracker. |
| Newsbank APA citation (article / print page) | 3,780 / 2,133 | citation text | n/a | not links, not listed |

## Before / after (current sheet after T14a: 3,899 tracker stories, press releases excluded)

| Link kind | Before (originals) | Before (reprints) | After (originals) | After (reprints) |
|---|---|---|---|---|
| Publisher's own site | 2,268 shown as "Read at <pub>", 742 as "Original link", 5 as "Read the reprint" (mixed with other kinds) | not shown | 2,972 "Publisher site" | 1,183 |
| NewsBank article | 1,522 shown **as "Read at <pub>"** (wrong label), plus 11 as "Read the reprint", direct non-CSL URL | not shown | 1,543 "NewsBank via CA State Library" | 1,965 |
| NewsBank print edition (Web + Print 2nd ID) | not shown | not shown | 153 | 49 |
| NewsBank print page | not shown | not shown | 155 | 507 |
| ProQuest direct (proquest.com) | 365 "ProQuest" | not shown | not listed (decision) | not listed |
| ProQuest via CSL | 365 | not shown | 365 (same element) | 105 |
| Internet Archive | 33 shown as "Read at <pub>" | not shown | not listed | not listed |
| Google search | hidden already | not shown | not listed | not listed |
| Other non-own sites (wires' partner sites, aggregators, mirrors) | shown as publisher | not shown | not listed | not listed |

Publisher links that stop being listed: 215 on tracker rows. All are in build/test_links/links_not_listed.csv.

| Reason | Originals | Reprints |
|---|---|---|
| Google search link | 59 | 22 |
| Internet Archive (TV news clips) | 33 | 2 |
| Wire outlet, link on a partner site (TCA, University Wire, U.S. Newswire, Contify, The National Desk, California Black Media) | 13 | 32 |
| Another outlet's site (e.g. CALmatters on kpbs.org, Press Democrat on abc30, SF Chronicle on sfgate, NNPA copies) | 18 | 24 |
| Yahoo page for a non-Yahoo outlet (Insider, Guardian) | 3 | 0 |
| Azure blob (Assembly letters) | 4 | 0 |
| github.com, nalert.blogspot, nmreports.org, tvmaze.com | 5 | 0 |

**Originals left with no listed link: 63** (build/test_links/no_link_originals.csv):

| Why | Originals |
|---|---|
| Internet Archive TV clips | 33 |
| Wire partner-site links | 12 |
| Another outlet's site | 10 |
| Azure blob | 4 |
| GitHub | 2 |
| Blogspot | 1 |
| TVmaze | 1 |

These stories show the existing "No direct link on file" note. 611 reprints have no listed link and are left out of "Reprint links". They still appear in "Reprinted in".

If CSL links are **not** derived (`CSL_DERIVE = False`), the 3,508 NewsBank article links and 202 print-edition links on tracker rows drop out. That leaves **781 originals** and 2,015 reprints with no listed link.

## Questions for Sammy
1. **Derived CSL links.** The sheet has no "via CA State Library" column for "NewsBank article link" (3,780) or "NewsBank print article link" (202). The patch lists them through CSL using the same host rewrite as the sheet's own CSL column, which matches 2,133 of 2,133 pairs. Is that OK, or should only CSL URLs written in the sheet be listed? A one-line switch controls this: 63 vs 986 originals without a link.
2. **Judgement calls kept as the publisher's own site.** Please confirm:
   - audacy.com for KNX
   - goldrushcam.com for Sierra Sun Times
   - ivpressonline.com for Adelante Valle
   - law.com for The Recorder
   - mynewsla.com for City News Service
   - valleynewsgroup.com for Encino Enterprise
   - jweekly.com for Jewish Bulletin
   - substack / buzzsprout / soundcloud / youtube pages for newsletters and podcasts
   - news.subaoxw.com for Shandong Business Times
   - aggregator pages whose outlet is the aggregator itself (Yahoo News, AOL, NewsBreak)
3. **Judgement calls treated as not own.**
   - sfgate.com for San Francisco Chronicle (5)
   - eastbaytimes.com for Mercury News (2)
   - Assembly letters on ct3.blob.core.windows.net (4)
   - GitHub mirrors of Epoch Times (2)
4. 15 Print Article IDs (Web + Print rows) have no NewsBank print article link in the sheet, so their second ID has no link to list. Examples: nb-00158 → nb-04184, nb-01889 → nb-04987.

## Tests (all on copies, in work/tmp_agent-links/)
**Against the current files (v7: js_merged.js 05:10, build_data.py 05:09, workbook after T14a, shell work/tmp_agent-write1/index_base_T14a.html):**

Run on two pages: links patch alone (compose/srvL), and links + agent-authorsplit's patch (compose/srvA).

| Suite | Links only | Links + authors |
|---|---|---|
| New links suite (build/test_links/test_links.js, cases_links_v7.json) | 23/23 | 23/23 |
| Display test.js (cases_T14a.json) | 18/18 | 18/18 |
| Reach test_reach.js | 8/8 | 8/8 |
| Authors test_authors.js | n/a | 16/16 |
| Update test.js (agent-ids blocks_post and mine) | 39/39 | 39/39 |

- **Composition:** applying links→authors and authors→links to the v7 JS and build_data.py gives byte-identical files in both orders.
- The rows, idmap and covcols blocks are identical to the v7 build. data.json differs only by the added `lk` / `authors` / `atitle` fields.
- Running patch_links.py again on a patched file skips all edits.

**Earlier, against the 04:45 JS and pre-T14a sheet:**
- Links suite: 23/23 on the pre-migration page and 23/23 on the migrated page. The unpatched JS on the same data passes 4/23.
- Display: 18/18 and 22/22.
- Update: 39/39.

**What the new suite covers:**
- ProQuest CSL: label, detail, new tab, and no direct proquest.com link.
- Publisher and NewsBank links, including the CSL host.
- The Web + Print second-ID link and the print-page link.
- Internet Archive, Google and wire partner-site links are excluded, and the "no link" note shows.
- Copy link copies the first listed link.
- Reprint lists for every kind, including excluded links; the list folds above 5 rows.
- A reprint added from the shared store (fallback path).
- Bulk check on about 210 random stories: each lists exactly its sheet links, all in ProQuest style, and nothing else.
- No page errors.

Re-run steps:
1. Build blocks with the patched build_data.py.
2. Assemble.
3. Run `python3 -I build/test_links/mkcases.py <blocks>/data.json cases.json`.
4. Run `SRV=<page dir> CASES=cases.json node build/test_links/test_links.js`. This needs a test-only hook, which the test's server injects itself.

**Data size:** data.json grows by about 1.2 MB, so the page is about 9.0 MB with author fields.
