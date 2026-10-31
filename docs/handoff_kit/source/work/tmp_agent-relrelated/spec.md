# RELRELATED-v1: related stories on release pages (Sammy comment eb3d0330)

agent-relrelated, 2026-10-28. Nothing in code/ or build/ was changed. Everything is in work/tmp_agent-relrelated/:
- relmatch.py: the matcher
- test_relmatch.py: 14 tests, all passing
- out/related_v20.csv: release → story, with the evidence for each pair
- out/release_related.json: the state file to seed
- labels_round1/2.txt: the hand labels

## 1. Root cause

`build/tabs/releases.js` (identical in `build/pub/pipeline/tabs/releases.js`), `related(it, ctx)` (L137–145), feeds the release page's chart, its list (the "Related stories" table) and the "Search N related stories" box. It matches stories on tags and dates, never on content:
- **A release with bills:** every tracker story tagged with any of the release's bills, anywhere in the release's two-year session. That is up to 24 months on either side. A bill intro release lists the signing coverage, and a "seven bills advance" release lists every story on any of the seven.
- **A release with no bills:** every story with the same Issue tag, 30 days either side of the release.
- **The `uses` list** (stories that use the release text) was meant as the evidence-based part, but it is never filled. Phase B item 2 was deferred (DECISIONS 170), so `it.uses` is null.

There is a second, smaller version of the same problem in `prep()` (L49–57). The "Original coverage, before vs after" section lists every same-bill or same-Issue story within ±7 days as coverage after the release.

**Measured over all 241 releases on the page** (244 tab rows, 3 posted on both sites):
- 188 releases have a list, holding 12,959 story rows.
- 92.0% of those rows (11,928) show no evidence of a link under the rule below. The median release has 91% of its list unlinked, 95 releases have at least 90% unlinked, and 52 releases have no linked story at all.
- 48% of listed rows predate the release, and 36% are more than 30 days after it.
- Worst cases:
  - pr00171 (rally before the AB 2316 vote): 494 listed
  - pr00116 (AB 418 intro): 364 listed
  - pr00172 ("Seven bills advance"): 304 listed, none related
  - pr00054 ("Appointed chair of the Privacy committee"): 48 stories on AB 587 social-media regulation

## 2. Rule (RELRELATED-v1, relmatch.py)

A story is related to a release only with evidence. The release's own copies (sheet rows that pass the release text rule) are not stories and are never listed here.

| type | evidence | window (story date − release date) |
|---|---|---|
| `text` | Shares ≥ 25-word runs with the release, ≥ 25 words in total. Uses the reprint_rule tokenizer and run length. A run found in 3 or more releases is boilerplate (bio, standing quote) and does not count. The story must also share a bill, or have text cosine ≥ 0.10, or headline cosine ≥ 0.10. That last condition drops multi-bill roundups carrying one paragraph of the release. | −1 … +90 days (the reprint text window). A story dated only to the month counts if its month overlaps the window. |
| `quote` | ≥ 12-word runs of the release totalling ≥ 20 words (same boilerplate filter), plus a shared bill or text cosine ≥ 0.14 | −1 … +30 |
| `bill` | Shared bill, and the story is on the release's topic: tf-idf cosine of the story text vs the release text ≥ 0.14, or of the headline vs the release text ≥ 0.10 | −1 … +7 |
| `topic` | No bill needed: English text with cosine ≥ 0.25 against the release text | −1 … +7 |
| `possible` (tier 2) | Shared bill and the `bill` window, but the topic can't be checked: the story is not in English, or has no saved text and its headline is below 0.10 | −1 … +7 |

- The same-issue ±30-day rule is dropped entirely.
- Idf weights are computed from release_texts.json only. A run needs nothing beyond that file, the build data and the story copies.

**Results (v19 data plus Release IDs, the relcopies3 build):**
- 1,059 related pairs: text 593, bill 347, quote 77, topic 42
- 153 possibly related pairs
- 174 of the 241 releases have at least one related story; the median is 3 and the maximum 58
- Of the 12,959 old rows, 864 survive as related. The 195 other related pairs are stories the old rule never listed, mostly text reuse without a matching tag, plus untagged stories on the same announcement.

**Keep the "Possibly related" tier, shown separately and collapsed.** Labelled precision was 19 of 21 decided, about 90%, mostly Spanish, Chinese and Russian coverage of the bill in the same week. That is useful, and it is clearly labelled as unchecked.

## 3. Validation (hand checks, labels_round1/2.txt)

Hand-checked releases:
- **30-release sample:** 22 releases with bills and 8 with an Issue only; sample_keys.json, chosen at random
- **14-release holdout:** fresh random releases (holdout_keys.json), checked after the thresholds were fixed

What was labelled:
- every new-rule pair
- every v19 pair inside ±7 days or with any quote overlap
- up to 8 random other v19 pairs per release, used to estimate the rest of the list

Related means the story reports the release's own news (same announcement, action or event) or quotes or reuses its text.

| | v19 precision | new "Related" precision | new "Possibly" |
|---|---|---|---|
| sample (30) | 8.2% pooled (29.9% mean per release) | 168 / 170 decided = 98.8% (6 unsure) | 9 / 11 |
| holdout (14) | 14.1% pooled (19.0% mean per release) | 64 / 64 = 100% | 10 / 10 (2 unsure) |

**Recall:** labelled related stories the new rule misses are 21 in the sample (about 89% recall) and 4 in the holdout (about 94%). Almost all are same-week stories with cosine 0.07–0.13, typically roundups or very short items: the Center Square and Techdirt pieces on X's lawsuit, the Politico DOJ Glock piece, and the JTA piece on AB 1836.

**A "Possibly" tier for cosine 0.08–0.14 was tested and rejected:** its precision was about 60%.

**Judgment call:** 73 `text` pairs fall 31–90 days after the release. They are later-milestone stories quoting this release, e.g. Glock signing coverage quoting the "advances to Senate Appropriations" release. They count under the rule as written ("quotes or reuses the release text"). If Sammy wants them gone, set TEXT_WIN = (−1, 30).

**Examples: dropped**
- pr00243 / s00018 (NBA champion coaches, AB 1626 signing): "City Hall Pass: AD46 race 2026" and the passage stories (English and Spanish) dated 22 days before.
- pr00171 (rally before the AB 2316 vote): Newsweek "Foods With Red Dye 40 Banned" (591 days before), LAist "Legislature is back to decide 1,300 bills", FoodService Director "Pennsylvania to continue universal free school breakfast".
- pr00054 (appointed Privacy chair): 47 AB 587 social-media stories, including the 2022 signing coverage and Korean, Spanish and Fox News pieces.
- pr00217 (budget road map): 9 Politico, WaPo and SF Standard pieces on unrelated races.
- pr00114 (Holocaust Remembrance Day statement): 5 pieces on the January shootings and caucus leadership.
- pr00172 ("seven bills advance"): 304 rows, now 0 related and 2 possibly related.

**Examples: kept or added**
- pr00208 (Glock law signed): CBS, Desert Sun, FOX40, LA Times "NRA sues…", USA Today and others, all same week and same bill on topic. 21 related.
- pr00046 (ethnic studies statement): San Diego Jewish World, Jewish Journal, Israel National News, all quoting the statement.
- pr00215 (Second Chance Sports Act): NYT "San Quentin Uses Sports as Rehabilitation", Hoodline, a Substack piece (`bill`).
- pr00063 (Breed Street Shul $15M): KNX, the Forward, the Algemeiner, RNS (`topic`; the stories carry no bill tag).
- pr00135 (statement on X's lawsuit against AB 587): 19 related same-day stories (SF Chronicle, AP, the Guardian, the Hill…) plus 8 non-English stories as possibly related.

## 4. Where it goes

The matching needs every story's text, and a pipeline-only rebuild by the Update button does not have that. Matching therefore runs in Python and is kept in a persisted pipeline file. The page only renders that file.

### 4a. Code (agent-backendclean2's layout, wherever code/ lands)
- `code/relmatch.py`, and in the pipeline `pipeline/relmatch.py`: copy work/tmp_agent-relrelated/relmatch.py. It imports reprint_rule from the same folder; set RELMATCH_RR_DIR if not.
- `build/tests/test_relmatch.py`, from test_relmatch.py. The label regression test is skipped without data.pkl.
- **State file** `code/release_related.json`, and in the pipeline `pipeline/release_related.json`:
  - Format: `{"v":1,"version":"RELRELATED-v1","rel":{"prNNNNN" | "<Story ID key for the 5 no-posting releases>": [[Story ID, type, days], …]}}`.
  - Keys are Release IDs because ins-release_pickup's `offNNN` keys are positional and shift when a release is added.
  - Seed from out/release_related.json, or re-run the full mode on the v20 build (command in 4e).
- Add both files to apply_all's PIPELINE list and helper list, and to the sheet-task prompt's pipeline file list.

### 4b. Build data: `insights/release_pickup_data.py` (code/ and pipeline/insights/)
- Read `release_related.json` from the folder above `insights/`, the same place build_data finds gabriel_bills_leginfo.json (`os.path.dirname(_here)`).
- Append the column `related` to `cols`. Each release row gets `rel_state.get(prid or key, [])`, filtered to Story IDs present in data.json, because deleted or merged stories drop out.
- Size is about +27 KB, with ins-release_pickup going from about 79 KB to about 105 KB, under the 150 KB cap.
- Update CONTRACT ("ins-release_pickup" columns).
- Phase B item 2's `uses` column becomes unnecessary: `text` rows are the stories that use the release's text. If the "≥25% share" figure is still wanted, add the share as a 4th element in relmatch.block_rows (words in runs ÷ story words).

### 4c. Renderer: `build/tabs/releases.js`, the tracker side of the release page
- **`prep()`:** read `iR = ci('related')`. Set `it.related` to the tier-1 rows and `it.possible` to the tier-2 rows, as `{r: ctx.byId(sid), type, lag}` with missing stories filtered out.
- **`related(it, ctx)`:** replace the body with `return (it.related || []).map(x => x.r)`. If the column is absent (an old build), return `[]`. Never fall back to bill, session or issue matching.
- **Page chart and list:** `rows` = related stories only. The caption becomes "Stories linked to this release by evidence: they quote or reuse its text, or cover its bill in the same week on the same topic." Add a small evidence label on each row: Uses the release text / Quotes the release / Same bill, same week / Same week, same subject, plus the lag.
- **New collapsed section "Possibly related · N":** "Same bill in the same week; not in English or no saved text, so the subject was not checked."
- **Placeholder** "Search N related stories": N = the related count. Show nothing when N is 0, with the note "No story in the tracker is linked to this release by its text, its bill or its subject."
- **Facts:** add `['Related stories', N (+ M possibly)]`.
- **"Original coverage, before vs after":**
  - Keep the counts only for releases with bills, labelled "stories on <bills>, ±7 days (context, not related stories)".
  - Remove its after-list (`it.post` rows), because the Related list replaces it.
  - Drop the issue basis (`WEAK`/`issue`) from pre/post, the list `answer()` sentence and the CSV columns. The issue basis is the same loose match.
- **CSV:** add "Related stories" and "Possibly related stories" (counts).
- Optional: a list facet "Related coverage: Has related stories / None".
- **Stale text:** remove the header comment's "related tracker stories (same bill in the release's two-year session, else the same issue 30 days either side…)".
- Pipeline copy: `pipeline/tabs/releases.js`.

### 4d. Update button (sheet task; RELCHECK-v4 release cleanup → RELRELATED)
- Prompt step 6, between "Add each saved page to articles/<year>.json" and the final assemble:
  1. `python3 -I build_data.py …` (as now; this writes blocks/data.json and blocks/ins_release_pickup.json)
  2. Add the saved pages to `copies/articles/<year>.json` (as now; move this before step 3 if it currently comes after)
  3. `python3 -I relmatch.py --data blocks/data.json --pickup blocks/ins_release_pickup.json --release-texts release_texts.json --articles copies/articles --update release_related.json --json release_related.json --releases <Release IDs of result.release_copies/new tab rows> --stories <Story IDs of the new Originals>`
  4. Re-run `python3 -I build_data.py …` (seconds) so ins-release_pickup carries the new rows, then `assemble.py`.
- **Articles to read in step 3:** besides the find years, also the years covering each new release's window, from release date −1 to +90 days. New releases are recent, so this is normally the current year. Stories added later inside a release's 90-day window are caught by `--stories`. Each new story is matched against every release, which needs only release_texts.json.
- Step 7: publish `release_related.json` as `pipeline/release_related.json` whenever relmatch reports a change. Add `result.release_related_changed`, or compare the file.
- sheet_task.py itself needs no change unless you prefer to call `relmatch.match_story` and `to_state` from `apply_release_finds()`. The CLI path keeps it out of the sheet write.
- The incremental mode was checked: removing one release (pr00140) and one story (s01488) from the state, then running `--update --releases pr00140 --stories s01488`, gives a file byte-identical to the full run.

### 4e. v20 build checklist
1. Full run on the v20 data and all article years:

   `python3 -I code/relmatch.py --index <v20 index.html> --release-texts code/release_texts.json --articles <v20 srv>/articles --json code/release_related.json --csv work/out/related_v20.csv`

   Expect about 1,059 related and 153 possibly related, changing only with data changes since v19.
2. `python3 -m unittest test_relmatch` passes.
3. Page check at 1400 and 390 widths, light and dark:
   - pr00243 shows 2 related (OC Register signings roundup, LA County Politics).
   - pr00172 shows 0 related plus 2 possibly related, and the empty note.
   - pr00208 shows 21 related.
   - No release page lists a story dated before the release −1 day.
4. DECISIONS line for RELRELATED-v1, and a CONTRACT column note.
