# RELPLAN shared data contract
One section per agent (build/RELPLAN.md). Fields the UI agents (rp-ui, rp-reverse) consume.

## rp-threads (RELTHREAD-v1, 2026-10-28)
Block **tab-releases**, new key **`thr`** (absent when code/relthread.py or the sheet's "Press releases" tab is missing).
Built by build/tabs/releases_data.py `_threads()` → code/relthread.py `build()`. Inputs: the tab's in-scope rows (+ the 5
no-posting releases from their Coverage Original row: date, headline, Bills cell; no text, no names), the sheet's "Bills" tab
(parsed by build/insights/bill_timeline_data.py `_rows_from_sheet`, so labels match ins-bill_timeline; fallback
bill_milestones.json), release_texts.json bodies. Keys are Release IDs (`prNNNNN`) or, for no-posting releases, the Story ID
(same keys as `rel`). Indexes into `th` / `pp` are only valid within one build. Other organizations' releases: NOT carried
(Sammy dropped the item, 2026-10-28).

`thr = {"th": [...], "x": {...}, "pp": [...]}`

**`th`**: list of threads (releases on the same bill + session), sorted by first release date. Each:
`[bills, session, rows]`
- `bills`: list of bill numbers (more than one when threads with the same members merged, e.g. a package, or a renumbered bill).
- `session`: "YYYY-YYYY" (odd year start; December of an even year counts as the next session).
- `rows`: members in date order. A plain string = the release names the bill. A list = how it joined:
  `[prid, "i", from_prid, cosine]` inherited the bill by text (it names no active bill);
  `[prid, "r", partner_prid, cosine]` renumbered link (it names a different single bill, joined by text ≥ 0.60).
  Show "Other releases on this bill" = the thread minus the release itself; mark i / r rows ("matched by text").

**`x`**: per release (only releases with something to say). All keys optional:
- `t`: [thread index, ...]: the threads it's in (two or more when it names several active bills).
- `bg`: [bill, ...]: bills named only as background (an older session's bill, or one finished > 45 days before). Not threaded.
- `nb`: int, set when it names ≥ 4 active bills (roundup / package release; de-emphasise its thread links).
- `m`: milestone label `[bill, iso date, kind, label, offset]`. The Bills-tab milestone of an active (or inherited) bill
  dated release −3 … +1 days; offset = release date − milestone date (days; −1 = milestone the day after). kind is one of
  introduced, committee, floor, signed, vetoed, chaptered, died, other (ins-bill_timeline kinds); label is ins-bill_timeline's
  label. Clerical steps (suspense file, enrolled, inactive file, committee action) never label a release.
- `p`: release pairs not in a shared thread: `[other_prid, rel, cosine, days, run_words]`, with days = other − this.
  rel "f" = follow-up / near-duplicate (≤ 14 days apart, cosine ≥ 0.35); "s" = similar text (cosine ≥ 0.45, or a shared
  ≥ 25-word run with cosine ≥ 0.20, or a ≥ 40-word run). run_words = words of the release in shared 25-word runs.
  Cosine = TF-IDF on release bodies with sentences found in ≥ 3 releases (bios, caucus boilerplate) removed.
- `n`: [people index, ...]: Others named (the tab's Legislator / Other official cells, tab order, one entry per person).
- `j`: [people index, ...]: Joint with, a subset of `n`: people joined to Gabriel in the title ("Gabriel and X",
  "X, Gabriel Announce") or named with him in the lead sentence's subject (up to the first verb).

**`pp`**: people table, sorted by release count desc then name: `[title, name, kind, n_releases]`.
kind "l" legislator, "o" other official. Display = title + " " + name (latest title used). People are keyed by
name without title (Kevin McCarty as Assemblymember and as Mayor = one person). Facet "Others named": people with
n_releases ≥ 3 (41 today); facet "Joint with": people in any `j`.

Examples (current data, 2026-10-28):
- **pr00171** (2024-08-06 food-safety rally): `{"bg":["AB 418"],"n":[10,0],"t":[25]}`; th[25] =
  `[["AB 2316"],"2023-2024",["pr00153","pr00162","pr00164","pr00166","pr00171","pr00172","pr00175","pr00180"]]`;
  pp[10] = `["Superintendent of Public Instruction","Tony Thurmond","o",7]`, pp[0] = `["Governor","Gavin Newsom","o",116]`.
  No `m`: the only milestone in range is the Senate suspense file (clerical).
- **pr00232** (2026-08-31 "Legislature passes Second Chance Sports Act"):
  `{"m":["AB 2204","2026-08-31","floor","Senate floor: Passed (39-0)",0],"n":[20,21,0],"t":[40]}`;
  th[40] = `[["AB 2204"],"2025-2026",["pr00215","pr00222","pr00232","pr00241"]]`; pp[20] Isaac Bryan, pp[21] Juan Alanis.
- **pr00187** (2025-02-10 looting bill announced as AB 469): `{"j":[7,5],"n":[7,5,73,71,48,43,79,54],"t":[32]}`;
  th[32] = `[["AB 468","AB 469"],"2025-2026",[["pr00187","r","pr00193",0.63],["pr00193","r","pr00187",0.63],"pr00196","pr00204","pr00210"]]`;
  j = Jacqui Irwin, Blanca Pacheco (lead: "Gabriel …, Assemblymember Jacqui Irwin …, and Assemblymember Blanca Pacheco … announced").
  No `m`: AB 469 was introduced 2025-02-06 (4 days before).
- Also: pr00091 `{"t":[12]}` with th[12] rows `["pr00066",["pr00091","i","pr00066",0.87]]` (ACR 51 inherited);
  pr00080 `p` = `[["pr00081","f",0.45,5,0],["pr00082","f",0.39,7,74]]`.

Counts today: 47 threads covering 139 releases (3 inherited, 2 renumbered rows); 41 releases with background bills;
118 milestone labels (floor 44, signed 42, committee 19, introduced 10, vetoed/chaptered/other 1 each); 38 pairs
(3 f, 35 s; each stored on both releases);
180 releases with Others named (101 people, 41 in ≥ 3 releases); 19 with Joint with.
Size: `thr` = 25.3 KB; tab-releases total 151.7 KB (was 126.4 KB), just over tabs_data.py's 150 KB soft warning.
Saving for rp-ui: once releases.js reads people from `thr.x.n` / `pp`, the `r[url][4]` co-issuer string (11.8 KB) can be emptied.

## rp-reverse (RELREVERSE-v1, 2026-10-28)
No new data block. The index is built client-side from blocks already on the page: `ins-release_pickup` (`rel` rows; t[7]
Story IDs = type `copy`; t[8] copy rows) + `tab-releases` (`r` for the Release ID fallback, `rel` evidence).
- Tracker (01_authors.js): `relIndex()` → `{list, byKey, bySid, ev(type), from(type)}`; `relsOf(sid)` → `[{rel, type, lag}]`,
  best evidence first. release = `{key, prid, sub, title, date, url, sids, copies:[{aid, raw, date, kind}]}`; `sub` = the
  release page id (`#press-releases/<sub>`: Release ID, else releases.js's date-title slug, same tie order).
- Tab modules: `ctx.rels()` = the same index (53_tabs.js ctx key).
- Tiers are generic: every type except `possible` counts; rank copy > nearcopy > text > quote > later > pre > bill > topic >
  any unknown type. "From press release" for copy/nearcopy/text/quote (the story uses the release's words), else
  "Related press release". A new rp-match tier needs no code change (add it to REL_RANK / REL_FROM / REL_EV in 01_authors.js
  only to rank it, label it "From", or give it a tooltip phrase).
- Bills page "Press releases N ›" opens the Press releases LIST with URL params `bill=<bill number>` (existing facet `bill`)
  and, for a number reused across sessions, `date=c:<from>..<to>` (existing date facet; the session window). rp-ui: keep
  facet keys `bill` and `date` (or tell rp-reverse/the coordinator if they change).

## rp-copies (RELCOPIES-v2, 2026-10-28)
Sheet write PREPARED, NOT COMMITTED (Mac bridge offline): work/tmp_rp-copies/out_rpcopies.xlsx from master 4d7fb37c…ebf24a;
plan work/tmp_rp-copies/plan.json, diff check diff_wb.py (OK), cell list report.json. Story ID s04749 reserved (work/clip/next_sid.txt = 4750).
**Do not commit it before sheet_task.py reads the renamed columns** (see "Readers to update" below), or the Update button
skips new releases and stops linking copies.

### Copies (what a release's "copies" now include)
Unchanged mechanism: a copy = a Coverage row with Press release = Yes in a story listed in the release's copy-ID columns;
`ins-release_pickup` t[7] sids / t[8] rows carry them (shape unchanged). New copies in this write:
- **near copies** (code/relcopy.py `near_copy`): story text holds ≥ 50% of a ≥ 250-word release in ≥ 25-word runs (reprint_rule
  measure, −1…+30 d). story share ≥ 0.85 → copy; below → review (hand check). 14 stories / 13 releases marked (10 auto, 4
  hand-checked: s01589, s01362, s01286, s00838). 11 candidates NOT marked (own reporting, briefs columns, opinion): plan.json
  `not_changed` → rp-queue "nearcopy" items / rp-match `nearcopy` tier, not copies.
- **wire reposts** (`wire_title_copy`): PublicNow row, no saved text, headline = release title cut at "…" (≥ 5 words, word
  prefix), 0…+1 days → copy (overrides DECISIONS 133). 8 rows: s01874→pr00243, s01893→pr00239, s01923→pr00237, s01933→pr00236,
  s01935→pr00235, s02082→pr00224, s02091→pr00223, s02146→pr00219.
- pr00182: its copy 01760 was a Reprint inside the Speaker's s00485 → own Story ID **s04749** (Original); pr00182's copy ID
  s00485 → s04749. s00485 (01759, the Speaker's release, Press release blank) stays a tracker story and is no longer a copy.
Effect on `ins-release_pickup` (built from the staged file): releases with copies 88 → 99, copy rows 112 → 134. These 22
stories leave `data` (they are Press release = Yes) → rp-reverse / rp-ui show them as copies; release_related.json still lists
some of them as `text` until the next relmatch run (relmatch skips a release's own copy stories).

### Press releases tab (RELTAB-v3, 48 columns; `code/reltab.py` COLS is the definition)
Renamed (reltab.RENAMED; `reltab.col(H, name)` / `is_new_layout` / `ids` / `legacy` accept old and new names):
| old | new | meaning |
|---|---|---|
| In tracker | Has copies | Yes/No: the release has ≥ 1 copy story |
| Tracker release ID 1, 2 | Copy story ID 1, 2 | Story IDs of its copies (max 2, reltab.N_TID) |
| Coverage stories linked | Copies (rows) | Press release = Yes rows in those stories (int; blank when none) |
| Tracker date (earliest pickup) | First copy date (if different) | earliest copy row date, only when ≠ the release Date; recomputed for all rows (38 cells: 28 stale + 10 new) |
New, derived (after "First copy date"; recompute on every build / Update from release_related.json: `reltab.related_values(state[prid], exclude=copy stories, known=tracker stories)`):
- **Related count** (int, 0 when none) and **Related story IDs** ("; "-joined Story IDs, state order; blank when none). Tiers
  counted: reltab.RELATED_TYPES = text, quote, bill, topic, pre, later, nearcopy ("possible" not counted). Staged values: 1,044 links on 173 releases (state 1,064 minus the stories that are now copies or not on the sheet).
Issue: blank → **"District / community"** on 18 releases (district honors, Nonprofit/Woman/Small Business of the Year, budget
checks to local groups, Valley Day of Service, Sally Ride highway): pr00017 45 59 61 62 64 65 66 79 91 92 111 120 127 132 158 167 216.
10 blank Issues left (not district): pr00004 08 24 30 41 56 85 108 166 172.

### Readers to update (files rp-copies does not own)
- **code/sheet_task.py (rp-button)**: `_rel_mark` (≈ l.1491–1502) uses the literal names "Tracker release ID {i}", "In tracker",
  "Coverage stories linked" → use `RT.col(H, f"{RT.COPY_ID} {i}")`, `RT.col(H, RT.HAS_COPIES)`, `RT.col(H, RT.N_COPIES)`; the
  RELTAB check at l.1279 passes once the sheet has the 48 columns. Recompute Related count / Related story IDs after
  `relmatch --update`, and First copy date / Copies (rows) on every mark. New-row copy tests: call relcopy.near_copy (copy →
  mark like the text rule, mode "nearcopy"; review → review list) and relcopy.wire_title_copy for untestable wire rows (mode
  "title"); wire rows auto-marked by is_press_release with no text that match no release → unmark (backend review #5).
  Also: a passing row that is a Reprint of a story whose Original does not pass → own Story ID or review, never link the other story (backend #4).
- **code/apply_all_patches.py (coordinator / rp-final)**: PIPELINE += `'relcopy.py': 'code/relcopy.py'` when sheet_task imports it.
- **build/tabs/releases_data.py (rp-threads)** l.35–46: `_tab_rows` reads "Tracker release ID 1/2" literally → also accept
  "Copy story ID 1/2" (or use reltab.legacy). Without it the tab-releases block loses copy links on the new sheet.
- **build/tabs/releases.js (rp-ui)**: no sheet names; wording "Pickups" → "Copies" per backend #8 is rp-ui's.
- code/relmatch.py docstring mentions "Tracker release ID" (text only).

## rp-match (RELRELATED-v3, 2026-10-28)
State file **unchanged in shape**: `code/release_related.json` (pipeline: `pipeline/release_related.json`)
`{"v":1,"version":"RELRELATED-v3","rel":{<Release ID | Story-ID key of the 5 no-posting releases>: [[Story ID, type, days after release], ...]}}`.
Rows sorted tier, lag, Story ID; **one row per Story ID per release** (dedupe, backend review finding 2). `days` is null for
a month-dated story. Readers: build/tabs/releases_data.py `rel` (tab-releases), rp-reverse relIndex(), reltab.related_values.

### Types and tiers (`relmatch.TIER` / `relmatch.LABEL` are the definition; import them rather than copying lists)
| type | tier | label (relmatch.LABEL) | rows | new in v3 |
|---|---|---|---|---|
| text | 1 | Uses the release text | 570 | (568 kept + 2 demoted nearcopies) |
| nearcopy | 1 | Runs the release (edited) | 23 | yes: was `text`; ≥ 60% of the story is release text; one release per story |
| quote | 1 | Quotes the release | 78 | +1 (AV transcript) |
| bill | 1 | Same bill, same week, same topic | 492 | +103 translations, +30 bill named in text, +11 relabel from topic |
| topic | 1 | Same week, same subject | 40 | +9 via translations (11 became `bill`) |
| pre | 1 | Covered the announcement before the release | 4 | |
| anchor | 1 | Same announcement (names and figures match) | 16 | yes: 0…+7 d |
| possible | 2 | Same bill, same week (topic not checked) | 62 | was 152 |
| later | **3** | Later coverage of the bill | 84 | yes: +8…+30 d, same bill + session, before the next release on it |
| laterquote | **3** | Later coverage quoting the release | 37 | yes: > 7 d after, no upper limit |
- **"Related" = tier 1 only** (counts, Related count / Related story IDs sheet columns, list "Related" column, chart, reverse
  "From/Related press release"). Tier 2 = collapsed "Possibly related". **Tier 3 = the "Later coverage" section** (rp-ui): not
  counted as related, not in the chart; label each row with LABEL[type] + lag. A tier-3 story has no tier-1/2 row anywhere.
- rp-copies: reltab.RELATED_TYPES should be the tier-1 set {text, nearcopy, quote, bill, topic, pre, anchor} (it currently lists
  `later` and lacks `anchor`); `laterquote` / `later` are not related stories.
- rp-reverse: REL_RANK/REL_EV already know nearcopy/later; add `anchor` (tier 1, "Same announcement") and `laterquote`
  (tier 3, "Later coverage quoting the release"; REL_FROM: it uses the release's words). Unknown types rank last.
- rp-ui (releases.js): EV / evCount() need nearcopy, anchor; prep() must split x[1] in {later, laterquote} into it.later
  (today everything except `possible` goes into it.related). Near-copy label = type `nearcopy`.
- rp-queue: near-copies = rows of type `nearcopy` (23); work/tmp_rp-match/related_v3.csv has per-pair evidence
  (Share of story in runs, Bills named in text only, Translation cosine, Anchor evidence, Longest quoted run).
Totals (v20 build): tier 1 1,223 links on 180 releases (was 1,064 / 176), 1,103 stories; tier 2 62 on 35 releases;
tier 3 121 on 46 releases. File 31.6 KB (was 27.5 KB).
### CLI (Update button, unchanged flags + one optional)
`relmatch.py --data … --pickup … --release-texts … --articles … --update release_related.json --json release_related.json
--releases <prids> --stories <sids> [--bills-leginfo gabriel_bills_leginfo.json]` (default: next to relmatch.py, which the
pipeline has). --update recomputes every story dated from 14 days before the earliest re-matched release (plus the named
stories and month-dated ones) against ALL releases, so it is byte-identical to a full run; stories whose year's articles file
was not passed keep their rows.

## rp-clips (RELCLIPS-v1 + RELSES-v1, 2026-10-28)
No new data. Reads relsOf / relIndex (01_authors.js) and tab-releases `thr`.
- Clips flags (15_checks.js FLAGS): `relfrom` "Ran release text" (best relation is copy/nearcopy/text/quote), `relrel` "Related to a release" (any other tier), `relnone` "No release"; the three split the stories. `relcopy` kept (copies only) for saved views. `REL_FILTERS` = facet buttons, `REL_FLAG` = the release flag keys, `relKind(r)` → 'from' | 'rel' | ''.
- Badge (02_state.js badges): "From press release" (from tiers) else "Related press release" (only where badges link: panel, Clips table); click → Clips with that flag.
- CSV (21_manage_badge.js relCsvCols): From press release / … link / … how, Related press release / … link / … how; several releases joined " | ", best evidence first. Replaces "Press release" / "Press release link".
- Bills (build/tabs/bills.js RELSES-v1): item.rels = releases in thr.th for bill + session (row forms i/r → rel.how) or naming the bill with date in the session (Dec of even year = next); rel.bg = named only as background. "Press releases N ›" always carries date=c:<session start>..<session end>.

## rp-ui (RELUI-v1, 2026-10-28)
Block **tab-releases** gains (build/tabs/releases_data.py):
- **`rules`** (absent when relmatch.py can't be loaded): `{"t": {type: [tier, label, tag, how]}, "copy": how, "bc": [-7, -2, -1, 7], "bch": how, "tenure": "2020-11-18"}`.
  tier/label = relmatch.TIER/LABEL; tag = row tag (releases_data.TAG); `how` sentences are built from relmatch / release_rule / relcopy /
  reprint_rule constants. Readers: releases.js (all labels and ⓘ texts), 01_authors.js relIndex().ev (panel labels).
- **`bc`**: `{release key: [before, after, after_not_linked]}` tracker stories (day-dated) on the release's bills in rules.bc windows.
- `r[url][4]` (co-issuers string) is "" whenever `thr.pp` exists (people come from thr).
- `_tab_rows` reads "Copy story ID 1/2" (RELTAB-v3) or "Tracker release ID 1/2".
53_tabs.js: `tbInfo(text, about)` / ctx.info (shared ⓘ); `tbOpenSaved(id, meta, list)` (list = [[id, meta]] → viewer "1 of N"; meta.kind 'release');
entity-page hooks P.rowTag(r), P.rank(r) (sort key `ev`), P.how {label, opts, of} (URL `how`), P.below (HTML after the list).
List facet keys: date, src, type, iss, bill, quoted, pick (yes/no/1/2/4), rel, pos, joint, named, outlet (`bill`/`date` unchanged for rp-reverse).

## rp-button (RELBUTTON-v1, 2026-10-28)
No new page block. Shapes added to the Update flow:
- **Run doc `releases_new[]`** (≤ 10): the oldest 5 new releases with `html`/`text` as before, each optionally `also_caucus: {url, date}`
  (its caucus posting); plus caucus items with `dup_of: <office URL on the tab>` and no page (the sheet task fills that row's
  "Also on caucus site (URL)/(date)" blanks and adds no row). `relcheck` notes "N more waiting".
- **Proposed rows**: a find of the release pickup search carries `_release: {prid, url}` (prid '' for a release new in this run)
  and Data Source "Release pickup search (TinyFish)".
- **ins-release_pickup** (read by 41 relKnown): `known` (or a new key `also`) may carry "Also on caucus site (URL)" values
  (handoff to the release_pickup_data owner).
- **sheet_task result**: `releases_review` (near copies below the bar, copies filed under another story, office postings of a caucus
  row), `releases_unmarked`, `releases_dual`, `related_cols` {copies_cells, related_cells, releases, links, state, columns},
  `queue` {nearcopy, billtags}, `relmatch` {releases, stories}. `releases_flagged[].mode` adds `nearcopy` and `title`.
- **--after-relmatch result** (`result2.json`): `related_cols`, `queue_docs` {"<tag>-nearcopy" | "<tag>-billtags": {"list": [...]}}
  in rp-queue's item shape (cat, conf, id `nearcopy-<tag>-NNN` / `billtag-<tag>-NNN`, key `prid:sid` / `sid`, title, detail,
  options, proposed[, multi]); tag = the run's UTC timestamp digits.
- Sheet: Has copies / Copies (rows) / First copy date / Related count / Related story IDs are recomputed for every release each
  run (tier-1 = reltab.RELATED_TYPES from relmatch.TIER; exclude copy stories and Press-release-only stories; known = tracker
  stories), exactly as rp-copies' write_wb.py computed them.
