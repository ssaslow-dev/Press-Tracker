# Press releases tab: backend review (reviewer-backend)

**Inputs.** I read `work/coverage_current.xlsx` (Press releases tab with 244 rows and 46 columns; Coverage with 9,787 rows) and the v20 pub2 build. The block sizes are `ins-release_pickup` 81 KB, `tab-releases` 126 KB and `data` 6.75 MB. I also read `code/release_related.json` (RELRELATED-v2, 1,216 pairs) and the code listed in the brief.

**Scripts.** My scripts are in this folder (`load.py`, `a1.py`, `a2.py`).

**Reproducibility check.** A fresh full relmatch run takes 33 s and reproduces the state file exactly: 1,216 = 1,216 pairs, with 0 differences. Reviewer 4's "1,217 vs 1,212" drift is therefore resolved in `code/`.

**Where the earlier reviews stand:**

| Claim | Reviewer | Status |
|---|---|---|
| 388 Press release = Yes rows that are not copies | 3, 4 | Confirmed (500 − 112) |
| 8 PublicNow stories, none with a saved copy | 2, 3, 4 | Confirmed |
| 153 releases show Pickups 0 | 3 | Confirmed |
| 112 releases show 0 pickups but have related stories | 4 | Now 113 with v2 |
| Match bills by session | 2, 4 | Fine for threads, wrong for Related (see #9) |
| The "From press release" line fires for 1 story | 2 | True, and that one link is wrong (see #4) |

---

## Ranked findings

### 1. The release check permanently loses releases when more than 5 come out between Updates (bug; XS)
**Evidence.**
- `41_update_search.js releaseCheck` collects the listing newest first. It stops at the first known URL, or at a date older than the tab's newest date for that site.
- It then keeps `found.slice(0, 5)`, which are the **5 newest**. The tab's newest date then becomes the newest of those 5.
- The next run stops at the top of the listing, so the older ones are never found.
- Real burst: the office posted **8 releases between 2026-09-25 and 2026-10-02**: 10 in the 14 days from 09-25, 3 on 09-29 alone. On a weekly cadence, 3 of those would have been dropped silently.

**Fix.** Sort `found` by date ascending before `slice(0, 5)`, which keeps the oldest 5. The next run then still walks down to the first known URL. Also write "N more waiting" into `relcheck`.

**Risk.** None. **Effort.** XS (one line plus the note).

### 2. `relmatch.py --update` writes duplicate related rows in the normal case (bug, reproduced; XS)
**Evidence.**
- `main()` runs `match_all` for `--releases`, then **also** `match_story` for each `--stories` ID. Both results are appended to `res[k]`.
- `to_state` then replaces the release's rows with the doubled list.
- This happens whenever a new Original falls inside a new release's window, which is the usual Update run: a release and its coverage arrive together.
- Reproduced in `rr_out.json`, from `--releases pr00243 --stories s01869,s00019`. pr00243 went from `[[s00019,bill,0],[s01869,text,3]]` to **4 rows** (each twice), and the total went from 1,216 to 1,218.
- releases.js would list those stories twice and count them twice ("Related stories · 4").

**Fix.**
- In `main()`, skip `match_story` for keys in `only_r`, or dedupe each `res[k]` by Story ID.
- Make `to_state` dedupe by (sid) on write as a belt-and-braces step.

**Risk.** None. **Effort.** XS.

### 3. The missing step: search for coverage and republications of each release (known gap; M)
**Evidence that nothing does it:**
- The Update plan (`tfPlan`) searches his name, his bills, outlet sites and wire headlines. It never searches a release's own title or text.
- `releaseCheck` runs **last** (line 606, after the search, screening and review), so a release found in a run cannot shape that run's searches.
- Of the 112 copies, **0** came from the Update button's web search. Their Data Source is Tracker scrape 62, NewsBank 48, Tracker reprint list 2.
- A title search would work:
  - **51 of 112 copies (46%)** use the official title as their headline (45 exact, 6 prefix).
  - **104 of 112 (93%)** ran within 4 days of the release, and all within 9.
- Caucus releases that don't name him get a share of the search for free: they are in scope (3 rows), but a "Jesse Gabriel" search can never find their copies.

**The step.** `releasePickups(mcp)` in `41_update_search.js`:
1. **Move** `await releaseCheck(mcp)` to before the search loop. It only reads the two listing pages, so it costs the same.
2. **Open releases** = this run's `U.newrels` plus the block's releases dated within the last 30 days. Thirty days is the RELRULE copy window (−1..+30). Cap it at 8 releases, newest first.
3. **Per open release, add up to 2 queries to the plan**, kind `'release'`, label `Copies of release prNNNNN`:
   - (a) `"<official title, ≤110 chars, quotes stripped>"`. This is the same form as the existing `'reprint'` headline queries.
   - (b) `"<first 12 words of the release's longest 14–45-word sentence that names him, else its first body sentence>"`. This is the `wireByText` sentence picker. With no `site:` it catches outlets that post the release verbatim.
   - Source text for (b): `U.newrels[].html/text` for new releases, and `data/release_texts.json` (already fetched by the tab) for open ones.
4. **Results go into the normal find flow.** Dedupe against `D` links and Coverage links, fetch the page (the existing `toFetch` batch), and save the page.
   - Each find carries `_release: {prid, url}` and Data Source `"Release pickup search (TinyFish)"`.
   - **The screen** must not drop a `_release` find for not naming Gabriel. That is what makes caucus copies findable. The sheet task's text rule is the gate.
5. **Sheet task (no new code path).**
   - `apply_release_finds` already tests every new row against all in-scope releases in its window. A pass sets Press release = Yes, links the row on the tab, and bumps the count.
   - A `_release` find that fails the text rule and does not name Gabriel is dropped and listed in `releases_skipped`, with why `"release search hit, not a copy and not naming him"`.
   - A find that fails but names him is ordinary coverage. It becomes a story, and step 6's `relmatch --stories` links it as `text`/`quote`/`bill`.

**Cost.** At most 16 TinyFish searches a run. The plan already runs several hundred outlet-site searches.

**Risk.** Low. Precision comes from the text rule, not from the search. Pages with no saved text stay untestable (see #5).

### 4. pr00182's copy is filed as a reprint of the Speaker's release, which mislinks a tracker story (data bug and rule hole; S)
**Evidence.**
- `s00485` = 01759, the Original: US Fed News, "SPEAKER ROBERT RIVAS URGES FISCAL RESTRAINT…". Sammy said to unmark it and return it to the tracker as a story (DECISIONS 141).
- Its **Reprint** row 01760 is Gabriel's "Budget Chair Gabriel Responds…" (Press release = Yes).
- The tab's Tracker release ID for pr00182 is `s00485`. As a result:
  - (a) the only tracker story with the "From press release" badge and line (`relOf`) is the Speaker's release, badged with Gabriel's title;
  - (b) relmatch skips s00485 for pr00182 (`story['id'] in sids`).
- **Cause.** `_rel_mark` and `apply_releases` link the passing row's **Story ID** even when that row is a Reprint of a different story.

**Fix.**
- Data: give 01760 its own Story ID (Original, Press release = Yes) and point pr00182's Tracker release ID at it.
- Code: when the passing row is a Reprint whose Original does not also pass, queue it in review as "copy filed under another story" instead of linking that story.

**Risk.** Low. One sheet write needs Sammy's OK (rule 7). **Effort.** S.

### 5. New wire rows with no saved text disappear from both the tracker and the release page (S)
**Evidence.**
- `is_press_release` (PR_HOSTS includes publicnow.com, targetednews.com and others) sets Press release = Yes on every new wire find **before** any text test.
- If the row has no saved text, `apply_release_finds` only lists it as untestable. It stays Yes and unlinked, so `build_data` hides it and no release lists it.
- For the existing rows Sammy decided the opposite: "untestable → unmark" (DECISIONS 133/136; this is how the 8 PublicNow rows went back into the tracker).
- So the same row type is treated two ways depending on when it arrived.

**Fix.** Pick one rule.
- Recommended: adopt reviewers 2/3/4's wire headline-prefix rule here. A release-wire host plus a headline that is a ≥5-word prefix of an in-scope title, lag −1..+3, counts as a copy, linked with `mode:'title'` and listed in review. This also handles the 8 existing PublicNow rows.
- Otherwise: unmark untestable wire rows, as the precedent does.

**Risk.** Very low, given 8 of 8 in the earlier hand checks. **Effort.** S.

### 6. A release posted on both sites in the same run will become two tab rows (S)
**Evidence.**
- 3 historical releases are on both sites (pr00021, pr00038, pr00063). They are one row, with the caucus URL in "Also on caucus site (URL)".
- That URL is **not** in `ins-release_pickup.known` (`official.known` = the tab's URL column only). Both listings return new URLs, and `apply_releases` dedupes by URL only.
- A new dual posting would therefore get two Release IDs, two library copies, two text-rule passes over the same Coverage rows, and split counts.

**Fix.**
- Add the "Also on caucus site (URL)" values to `known`.
- In `apply_releases`, merge an office item and a caucus item with the same normalized title within ±3 days into one row: Source = office, caucus URL in "Also on…".

**Risk.** None. **Effort.** S.

### 7. Release copies carry 5.8 MB of inline photos, and opening any one downloads 7.3 MB (performance; S)
**Evidence.**
- `articles/releases.json` is 7.33 MB, the largest copies file; the 2024 shard is 6.77 MB. Of that, **5.81 MB (80%) is `data:image` URIs** in 25 releases.
- pr00045 alone is 2.08 MB (four JPEGs of 22 KB, 442 KB, 732 KB and 878 KB base64). The median release is 6 KB.
- Story copies use `jgimg:` refs into `img/1xx.json` shards; release copies have **0** refs.
- Opening any saved release fetches the whole file. At the current rate, new photo releases reach the 12 MB `--shard-mb` split within about 20 photo-heavy releases.

**Fix.**
- Run `make_copies.py --releases` through the same image externalization as story copies (refs into `img/` shards).
- Downscale to the viewer width (≤1200 px, JPEG q≈75). `img_embed.embed_page(kind='release')` in the sheet task should emit refs too.
- Also exclude `releases-N.json` (not just `releases.json`) in `relmatch.load_texts`. Today a second shard would be parsed as story texts.

**Risk.** Low (viewer path already exists). **Effort.** S.

### 8. Architecture: one concept, many code paths and names (M; consolidation, no behavior change)
**"Pickups" / "copies"** are computed in 2 places and shown under 6 names:
- Computed by:
  - `sheet_task` (`_rel_mark` +1 increments "Coverage stories linked"; `apply_releases` uses `len(hits)`);
  - `release_pickup_data.build`, which recomputes from **every** Press release = Yes row of the linked stories.
- Counts agree today: 0 of 236 releases disagree, and sheet 107 + 5 no-posting = block 112.
- But the block counts any Press release = Yes row of a linked story, including one set later by the wire auto-mark (#5) that never passed the text rule. The sheet counter is never recomputed. The two can drift silently.
- Names: list "Pickups", page "Copies of this release", facet "Picked up", answer "copies", sheet "Coverage stories linked" (it counts rows, which are neither stories nor coverage), CONTRACT "runs", Bills tab "N outlets ran it" (it counts rows; pr00143 shows 3 rows from 2 outlets).
- Fix:
  - One term in the UI, **Copies**, used on the list column, page, facet and Bills tab, with "outlets" only where it really counts outlets.
  - Rename the sheet columns: "In tracker" → "Has copies", "Tracker release ID 1/2" → "Copy story ID 1/2", "Coverage stories linked" → "Copies (rows)". Copies are not tracker stories, so the current names are stale.
  - Add a build check: block row count = sheet count per release.

**Dead or duplicated logic:**
- `build/insights/release_pickup.js` (16.8 KB) **still ships** in pub2: all 95 long lines are present, and it is registered as AJGInsights `release_pickup`. It contains the "same bill, else same **issue**, 0–7 days" follow-up logic that RELRELATED-v1 retired. `relHits` still links to it via `data-ins-go`. Remove it from `insights_assemble.ORDER` and point `relHits` at `#press-releases`.
- Tab-layout adapter in 3 copies: `release_pickup_data._tab_rows`, `releases_data._tab_rows`, `reltab.legacy`. The old 16-column layout is retired (BUTTONOPT-v1), so keep `reltab` only.
- No-posting list in 2 copies: `REL` and `NO_POSTING` ("keep in step").
- Tenure date in 6 places: `release_pickup_data.TENURE`, `reltab.TENURE`, sheet_task twice, `REL_TENURE` in JS, the releases.js caption, plus the old module. The block even carries `tenure`, and no reader uses it. Readers should use the tab's **In scope** column (0 mismatches today) and keep TENURE in `reltab` only.
- Two `officials()` (relpage, reltab; `apply_releases` calls reltab's even when relpage parsed the page) and two bill extractors (relpage.bills and a regex in `apply_releases`).
- Stale block fields:
  - `auto` (always 0; 0 of 241 nonzero);
  - `official` (= `url != ''`);
  - `tab-releases.c` repeats outlet and date already in `rows`;
  - "Phase B" (merge `tab-releases.r` into `ins-release_pickup`) was never done, and `prid` is carried in both.

**Fix.** One builder, `releases_data.py`, emits one `tab-releases` block. `ins-release_pickup` shrinks to what `relOf`, `relList`, bills.js and `relKnown` read (key, date, title, bills, sids, url, prid, n). Saves about 30 KB, and more importantly 3 adapters.

**Risk.** Low. Touches 5 readers. **Effort.** M.

### 9. "Bill coverage" before/after mostly re-counts the Related stories and is off by a day (S)
**Evidence.**
- It is computed in the browser from `D` (`releases.js prep`, ±7 days on any shared bill), separately from relmatch.
- Of the **877** "after" stories across the 174 bill releases, **729 (83%) are already Related**.
- **14 stories are counted "before" and also listed as Related** (lag −1, because relmatch's windows start at −1; e.g. pr00224/s02088, pr00221/s02130). The page then says the same story preceded and followed the release.
- Session filtering is **not** the fix. 53 releases name an older-session bill, but the 17 bill/possible links made only through such bills are correct, e.g. pr00135 (AB 587, the X lawsuit) has 6 English and 8 non-English stories. This refutes session matching for Related; it remains fine for release threads (reviewers 2 and 4).

**Fix.**
- Compute it in `releases_data.py` with relmatch's windows (before = −7..−2, after = −1..+7).
- Report "N other stories on the bill, not linked" (after minus related). This turns a context number into a useful "unlinked coverage" pointer that feeds reviewer 1's #3 later-coverage tier.

**Risk.** None. **Effort.** S.

### 10. Rule text hard-coded in the UI (S)
**Evidence.** No UI string is generated from a backend rule; every threshold is retyped in JS:
- releases.js list cap: "Pickups are sheet rows that carry the release's own text";
- Copies cap: "runs of 25 or more identical words covering 90% of both; distribution-service excerpts count";
- Related cap: 25 words / 90 days / 30 days / 7 days / 14 days;
- Possibly related cap; Bill coverage cap; the date facet hint;
- `relHits`: "same text, by the reprint rule";
- tenure "Nov 18, 2020" in the list cap.

Labels already differ between the two sources. relmatch `LABEL` (used in its CSV) says "Same bill, same week, same topic" and "topic not checked". releases.js `EV` says "same bill, same week" and "subject not checked". "Same week" is really a −1..+7 window. The pub2 build's EV had no `pre` while the code's state had it, which is a drift caught only by a handoff note.

**Fix.**
- Add `RULES = {type: {label, short, window}}` to relmatch.py and `COPY_RULE` to release_rule.py. `releases_data.py` writes them into the block as `rules`.
- releases.js renders the labels and the windows from it.
- Captions shrink to one plain line each ("Stories that reuse, quote or report the same announcement").
- The full explanation lives in CONTRACT "Related stories on release pages", reachable from one "How links are made ›" line.

**Risk.** None. **Effort.** S.

### 11. Data quality on the tab (S; mostly decisions for Sammy)
Of 236 in-scope rows:
- Dek is blank on 140 (a property of the source).
- Issue is blank on 27, 2 of them with copies.
- Contact is blank on 77: all 37 caucus rows and 40 office rows.
- 3 caucus rows don't name him; they are in scope under the tenure rule (pr00067, pr00150, pr00195).
- 1 duplicate title, which is legitimate (pr00182 and pr00211 are the annual budget statement).
- **"Tracker date (earliest pickup)" disagrees with the current copies on 28 rows.** E.g. pr00116 shows 2023-03-20 but has no copies now, and pr00056's earliest copy is 2021-06-07 but the cell is blank. It is a pre-RELRULE history column. Label it "(before text rule)", next to the other history column, or recompute it.
- **The 5 no-posting releases** (s02061, s02140, s02158, s02549, s03045) are not tab rows. They have no Release ID and no entry in release_texts.json. relmatch therefore indexes their **title only** (`has_body` False): text, quote and topic evidence are impossible, and 4 of 5 have no related stories at all. Their copies do have saved text. Proposal: make them tab rows (Source "Not posted officially", text from the copy's saved page, next Release IDs). That retires `REL`/`NO_POSTING` and the Story-ID keys in release_related.json. Needs Sammy (CONTRACT says they are not tab rows).
- 2 NewsBreak "Reprint (unverified)" rows (07197 under s02017, 07098 under s04641) have no date or headline and are untested. Run the text rule or remove them.
- "Caucus release names Gabriel" is left over from the overruled "or names him" rule (DECISIONS 123). It is harmless as information, but no code reads it.

### 12. Smaller Update-flow gaps (XS each)
- `copies_needed` stages −1..+90 days around a new release. RELRELATED-v2 `pre` needs −14, so a release in early January has no prior-year texts and cannot get `pre`/`text` evidence from December stories. Use `span(d, -14, 90)`.
- The live pipeline (pub2) ships relmatch **v1** and v1 state, while `code/` is v2. An Update between now and the v2 publish runs v1 `--update`. That is safe for new rows, but it writes `version: RELRELATED-v1`. Ship relmatch.py, release_related.json and releases.js together.
- The "merged, never shrunk" policy keeps stale links when a story's bill tag or text changes. A full run is 33 s and reproduces the state exactly, so run one at each full build and let it replace the state. Keep `--update` for the button.
- Stories that gain a saved copy later (Chrome saves) are never re-matched. Add their Story IDs to `--stories` when the run fills Saved Copy?.
- `releases_data._related` silently returns `{}` when it cannot find the state file, and the page then shows no related stories. Make `build_data` fail or warn.

---

## Quick wins vs bigger changes
- **Ship now (XS–S, bugs):** #1, #2, #6, #12 (first two items). Then #4 (sheet write) and #5 (pick the rule with Sammy).
- **This week (S):** #7 image externalization, #9 bill coverage in Python, #10 rules in one place.
- **Bigger (M):** #3, the pickup search step: JS plan, screen exception, sheet-task skip reason. #8, consolidation, ideally done together with reviewers' reverse links so the readers are touched once.
