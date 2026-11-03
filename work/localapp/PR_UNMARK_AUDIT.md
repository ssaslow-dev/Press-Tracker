# Audit: un-marking the 228 "Press release = Yes" rows (PRJUDGE-v1 follow-up 3)

Independent, read-only audit for Sammy, 2026-11-03. Workbook copy 0bccc1fc (2026-11-03), saved text from the library snapshot of 2026-10-31 and the live tracker's article files, release texts from the live tracker. Every number below was computed from those files; nothing was changed. Scratch work: `$S/audit/` (texts.json, signals.csv, no228_cats.csv; S = the session scratchpad).

## Verdict (plain words)

**The verdicts in the review are sound, but un-marking all 228 rows now is not wise, and it is not a harmless change.** Three reasons:

1. **It reverses decisions you made on 27–29 October, some by name.** On 27 Oct you said "pure press release" includes "an outlet posting the release verbatim" (DECISIONS line 35). You answered "Keep marked, unlink" for HeySoCal 02913, Pasadena Independent 02912 and San Fernando Valley Sun 04377 (line 136); all three are on the "should be No" list. You approved hand-checked marks on four more stories (line 225: s01589, s01362, s01286, s00838), also on the list. The TONE_GUIDE (line 15) and the handoff rules (HANDOFF_PC_APP section 3) say the same thing in writing. The new rule ("a community outlet running a release, even word for word, is coverage") is a policy change, not a correction, and the review does not say so.
2. **96 of the 228 rows (85 stories) are the copies of your own office's and the Jewish Caucus's releases** that the Press releases tab links to. Un-marking them empties the tab's "Ran it" (copies at real outlets) on **77 of the 95 releases that have copies** and turns 13 releases from "Picked up" to "Not picked up" (188 → 175 of 244). That is the opposite of what RELRECS-v1 (2 Nov) meant by "Picked up = … plus copies at real outlets". The tab's own counts also go inconsistent ("Has copies = Yes, Copies (rows) = 0") until its code is changed.
3. **The save program would refuse it, and the tracker needs follow-up work to look right.** 228 filled cells changing is exactly what SAVE_RULES refuses ("A filled cell would change, outside the recorded exceptions"). Done properly it is a dedicated one-time step with backup, like the unverified-rows deletion. After it, 54 of the new stories have a blank Role (the Home "Headlines in 2026" tile and the story badges mis-handle a blank), 17 pairs of the new stories are the same release text twice (would show as two stories), 85 stories need re-matching to their releases, and 1 row would still be hidden.

**Recommendation:** do not un-mark anything until you decide, in writing, that community reposts are coverage *and* how copies of your own releases should then be counted. If you confirm the rule, un-mark in two steps: first the 132 rows that are not copies of your releases (other issuers' releases and reported items at news outlets; minus the 13 advocacy-organization posts, which need a NOBLOGS-v1 call), then the 96 own-release copies only after the Press releases tab is changed to count copies by Copy story ID rather than by the Press release flag. Details in section 5.

---

## 1. Are the verdicts right under the rule?

The rule applied: a row is a press release only if (a) its text is a release and (b) the outlet is a wire or an official site. I read the saved text of 106 of the 527 rows: 47 "should be No" across the big groups, the 13 "official"-site "should be No" rows, 27 "keep Yes" (TendersInfo, Real Estate Monitor Worldwide, both Business Wire rows incl. 04130, Yahoo ×3, AOL, Jewish Federation 09281, Consumer Reports, Steinberg, ANCA, Liberty Counsel, Jewish California, ForeignAffairs, TNS, US Fed News) and the 19 unsure (no text: workbook row only). I also ran a signal scan over all 527 texts (`$S/audit/signals.csv`).

**"Should be No" (228).** Under the rule as written the verdicts are right in 45 of the 47 I read; the texts are releases on news or community sites, often self-labelled:
- San Diego Jewish World: 31 of 36 carry SDJW's own "(Press Release)" tag ("SACRAMENTO, California (Press Release) — The California Legislative Jewish Caucus released the following statement…", 09348).
- Contra Costa News: "Press Release by CC News" (02389, 00629, 08902, 01032).
- Santa Barbara Independent 08785: "Press releases are posted on Independent.com as a free community service."
- Sierra Sun Times: 12 of 39 are ≥ 60 % word-for-word with his own releases; 12 are Governor's-office releases ("What you need to know:" format); 3 "issued the following statement".
- Lassen County Times (NewsBank, "Author: swilliams"), Del Norte Triplicate ("Author: The Triplicate"), East County Today ("Press Release by ECT"), Lake County News ("Author: GOVERNOR'S OFFICE", 04109): release text run as news.

Two debatable ones: **00287 Daily Record (Dunn, NC)** is the paper's automated GlobeNewswire feed ("Section: Press Releases … (GLOBE NEWSWIRE) --"); the review keeps the Yahoo and AOL copies of PR Newswire releases as Yes ("wire release syndicated") but sends this identical case to No because the host is typed "news". **04844 California Courier** (ANI exhibit at CSUN) is a reported feature, so No is right but for a different reason than given.

**The 13 "official" rows** (California Apartment Association 10, Common Sense Media 2, Jewish World Watch 1) are correctly "not a release": they are the organizations' own blog-style posts ("Mike Nemeth … The California Apartment Association has defeated legislation…", 09316). But they are advocacy-organization posts. NOBLOGS-v1 (DECISIONS 385: "advocacy blogs are NOT coverage … existing rows: list for Sammy before removing") means un-marking them does not settle whether they are coverage; it only moves them from one hidden bucket to visible. Your call.

**"Keep Yes" (280).** 27 of 27 read as release text on a wire or an official site. 09281 (Jewish Federation "Dear Community…" letter) is a statement rather than a release, but it is the organization's own channel, so it is hidden either way.

**"Unsure" (19).** Not really unsure: 16 are PublicNow rows with a release title and no text; DECISIONS 225 (2) already decided these are copies (wire title rule, 8 of 8 matched) and RELCOPIES-v2 (2) that untestable Yes rows of other issuers stay marked (the 3 official rows: 04556, 07180, 09129). All 19 are "keep Yes" by recorded decision.

**Estimated error rate against the rule:** about 2 % on the 228 (2 debatable of 47 read; the automated scan found no reported-byline row that reads as original reporting, and 45 "bylines" are staff labels like "CC News", "ECT", "Vanguard Administrator"). The problem is not the verdicts; it is what the rule does to earlier decisions and to the release pages.

## 2. What changes in the tracker if the 228 become No

Computed from the workbook with build_data's own exclusion logic (`code/build_data.py:181-200`: a story is dropped when its **Original** is Yes; Yes reprints are dropped individually).

| | Before | After | Change |
|---|---|---|---|
| Stories shown (Originals not Yes) | 3,707 | 3,908 | +201 |
| Reprint rows shown | 3,562 | 3,593 | +31 |
| Stories with ≥ 1 shown reprint | 936 | 961 | +25 |
| Releases "Picked up" (RELRECS-v1 R1) | 188 of 244 | 175 of 244 | −13 |
| Releases with ≥ 1 copy at a real outlet | 77 | 0 | −77 |
| Originals with blank Role | 4 | 58 | +54 |

**Per year (stories shown):** 2018 126→129 · 2019 185→197 · 2020 118→126 · 2021 253→288 · 2022 282→310 · 2023 749→791 · 2024 695→725 · 2025 630→644 · 2026 578→607. Every Data-tab total, chart and outlet/reporter page moves with these.

**Who becomes visible:**
- 201 rows are Originals → 201 new stories (Story IDs unchanged). 147 of them show 0 reprints, 40 show 1, 11 show 2, 3 show 3.
- 27 rows are Reprints: 22 are reprints of Originals also on the list (they travel with their story); 4 are reprints of already-visible Originals (00692, 01424, 07351 Oragark; 01528 Armenian Mirror-Spectator) → +4 reprints and a changed "# of reprints"; **1 (05166 East County Today, s01614) stays hidden** because its Original 05165 California Newswire keeps Yes and build_data drops the whole story.
- 5 more reprint rows that are not on the list become visible because their Original is (they are blank today, hidden only by their Original).
- No story becomes "a hidden Original with visible reprints": the page cannot show that case; build_data drops the whole story. The same quirk already hides 8 blank-flag reprints today (Yahoo 00290/01190/01364, Courier 01383, Massis Post 10693/10664, Ukiah Daily Journal 04160, News.am 10665) — worth a separate decision whatever you do here.

**Fields:** Tone is filled on all 201 (112 Positive, 80 Neutral, 6 Negative, 3 Very positive: the TONE_GUIDE rates a release copy Positive, so the tone mix shifts: Positive 542→654, Very positive 17→20, Neutral 2,851→2,931, Negative 159→165). Topic blank on 1 (shows as "Unassigned"), Reach blank on 0, Language blank on 4, Mention depth filled on all. **Role is blank on 54** (Sierra Sun Times 20, Contra Costa News 12, East County Today 4 …). The Home tile "Headlines in <year>" counts every story whose role is not "Mentioned in story" (`code/tracker/03_overview.js:28`), so blank roles inflate it, and the story badge code (`code/tracker/02_state.js:143`) renders an empty badge for a blank role. Nothing lands in Needs attention (it lists only negative tone in the last 30 days and team notes).

**Outlets pages:** Sierra Sun Times 1→35 stories, San Diego Jewish World 24→59, Contra Costa News 9→29, Lassen County Times 6→17, East County Today 2→12, California Apartment Association 0→10, Del Norte Triplicate 1→9, Lake County News 3→9. Reporters: 78 of the 201 have a byline, mostly staff labels (CC News 20, ECT 8, SFVS Staff 5) and Mike Nemeth (CAA, 10); `reporter_record.py:141` excludes Yes rows today, so he would appear as a reporter with 10 stories.

**Story travel / maps:** +31 reprint rows; `rc` (reprint counties) recomputed per story; no new counties of note.

**Duplicates:** 17 pairs among the 201 share ≥ 50 % of their 8-word phrases both ways within 30 days and sit in different stories today (34 stories), e.g. Del Norte Triplicate 02770 vs 02858 (same text 94 %/91 %, 16 days apart), Lassen County Times 04111 vs 04161, Madera Tribune 04076 vs East County Today 04078 (90 %/74 %), Contra Costa News 01878 vs Sierra Sun Times 01879 (72 %/93 %). Hidden, nobody noticed; shown, the reprint rule would normally have merged them (new finds are tested, existing rows are not).

**Viewer copies:** the 228 rows' library files total 26.4 MB; `make_copies.py:410` skips release stories today, so the 201 stories need copies built and distributed in a refresh file.

## 3. What breaks or shifts in the logic

**Original choice (REPRINT-v2, `code/reprint_rule.py:748-760`).** Press release = Yes lowers a row's eligibility (elig 2). Today 23 stories have a Yes community Original and a Yes wire Reprint; `choose_original` already says the wire row should be the Original ("current Original is a press-release copy"; both Yes, wire earlier). Nothing acts on it while they are hidden. After the flip those 23 settle (community row elig 0 wins). One story goes the other way: **s01614**, where 05165 California Newswire (keeps Yes, prservice) is the Original and 05166 East County Today is un-marked: the rule then says East County Today should be Original, but saves only swap for new finds (`sheet_task.py` origin_swaps), so the story stays hidden until someone swaps or splits it.

**Reprint pair rule (`reprint_rule.py:877-879`).** A press-release-service row and a newsroom row can be reprints of each other only when both are Yes. 46 such pairs in 44 stories (e.g. s00013 Sierra Sun Times 00039 + US Fed News 00038) become "never a reprint" after the flip. Existing groupings are not re-tested by a save (`pair_class` runs on new candidates, `sheet_task.py:1698, 1964`), so nothing moves by itself, but the sheet then holds 44 stories the rule says cannot exist; a later regroup run would flag them.

**Release pages and the Press releases tab.**
- Copies = the Yes rows of the tab's Copy story IDs (`build/insights/release_pickup_data.py:158-168`, `build/tabs/releases_data.py:101-108`, `sheet_task._rel_counts` 2836-2855). Every non-wire copy row on the tab is on the 228 list: all 77 releases with real-outlet copies go to 0 "Ran it"; 66 of them lose every copy row (the other 11 keep only wire copies, which never counted as pickups). `_rel_counts` then writes "Has copies = Yes, Copies (rows) = 0" (ids still present, no runs). Copy story ID 1/2 is a derived column (VT_DERIVED_REL, `sheet_task.py:4318`) but is not recomputed from the flag, so it keeps pointing at stories that are no longer copies.
- "Picked up" (`build/tabs/releases.js:76-88`): related stories that are not wire and not `nearcopy`, plus copies at non-wire outlets. The 85 own-release stories would need `relmatch --stories` (the save runs it only for the run's stories, `work/saver/src/saver_steps.py:194-206`); 84 of them are ≥ 60 % the release's words, so relmatch would type them `nearcopy`, which is excluded from Picked up. Net: 13 releases flip to "Not picked up", the other 64 affected releases drop by one or more. The "Ran the release" list on each release page empties. Whether that is "right" depends on the rule you choose: RELRECS-v1 counted a community repost as a pickup; the new rule counts it as a story but the page's definition then stops counting it.
- The story panel would show "From press release: … (Runs the release (edited))" for those 85 once re-matched; "Related count / Related story IDs" on the tab change on the next save (allowed derived columns).

**Update station and dedupe.** Unaffected: the for-Update file carries every Coverage row including hidden ones (`work/localapp/updatefolder/FORMAT.md` `rows`), and the station never matches on the flag. PRJUDGE in the station (`src/prjudge.js`) already applies the new rule to new finds; the PC save still auto-marks by outlet name (`sheet_task.py:150-151, 994`; NEWSBANK.md line 96 notes `_pr.v = "no"` is not yet honoured), so new wire finds keep getting Yes by name until that is fixed.

**Colours.** 481 of the 527 Yes rows are red font today (DECISIONS 102 "red = not in the tracker"); 46 Yes rows are black (already inconsistent; 3 of the 228, e.g. 02770, 04055, 04760). Un-marking must set the 228 rows to black, and the PRCOLOR-v1 purple pass at switch-over must skip them. `mark_red` (`sheet_task.py:3596-3610`) only colours rows a run appends, so it will not fight the change.

**The save program.** Un-marking is a filled-cell change on 228 Coverage cells and 201 Originals-tab cells (the mirror carries Press release = Yes on all 201), refused by SAVE_RULES unless it is a recorded exception. Two legitimate routes: (a) a dedicated one-time step with backup, sha check and a ledger entry, like the unverified-rows deletion (DECISIONS line 530); (b) your own Excel edit, accepted as the new baseline (SAVER-RULES answer 2). Route (a) is safer: it can also fix colours, the Originals mirror, re-run relmatch and list every cell. Refresh files for readers follow from the next rebuild.

**Other code keyed on the flag, checked:** `wireblend.py:25` (wire blends skip Yes rows; no effect), `reporter_record.py:141`, `make_copies.py:410`, `sheet_task._pr_rows` / `_rel_link_ok` (2802-2831: a Reprint links its Story ID only if the Original carries the release; after the flip these community rows no longer count as "carrying" one), `releases_data.py` `nw` list (outlet types; no change), `relcopy.py` (near_copy writes Yes on hits: the next time a community copy of a new release is found, the save would mark it Yes again under RELCOPIES-v2 unless that rule is changed too).

## 4. Consistency after the change

With the 228 un-marked and the 299 others kept, the remaining Yes rows would be: wires and release services (TNS 161, US Fed News 40, TendersInfo 13, PR Newswire 11, Hispanic PR 9, ForeignAffairs 7, PublicNow 16 …), aggregator copies of wire releases (Yahoo 4, AOL 1) and official sites (ANCA, Jewish California, Consumer Reports, Steinberg, Liberty Counsel …). That is one clear rule except for:
- **Yahoo/AOL vs Daily Record:** the same automated wire feed is Yes on an aggregator and No on a newspaper site (00287).
- **Advocacy organizations:** CAA, Common Sense Media and Jewish World Watch posts become No (visible) while ANCA-WR, Steinberg Institute, Consumer Reports, Liberty Counsel posts stay Yes (hidden) because their text reads as a release. Same kind of site, opposite outcome, decided by prose style.
- **Outlets split across both:** none among the 228 vs 280 (no outlet appears on both lists), but 44 stories mix a Yes wire row and a No community row.
- **01759 US Fed News:** on 27 Oct you said "Unmark … back in the tracker as a story" (DECISIONS 141); the PRJUDGE follow-up plans to re-mark it at switch-over. Contradiction to settle.
- **RELCOPIES-v2 still in the code:** `relcopy.near_copy` and the save's "Count as a copy" queue answer (`sheet_task.py:2778`) still mark community copies Yes, so the rule would drift back with each save unless those are changed.

## 5. Recommendation and a safe way to do it

**What to decide first (Sammy):**
1. Confirm, knowing the above, that a community outlet running a release verbatim is coverage. If yes, record it as superseding DECISIONS 35, 123, 136, 225 (1), 311 (release copies) and TONE_GUIDE line 15; update HANDOFF_PC_APP section 3, CONTRACT "Press-release copies v2" and RELRECS-v1 definition D.
2. Decide how copies of your own releases are counted afterwards. Two sensible options: (A) keep tracking copies by Copy story ID regardless of the flag (the tab keeps "Ran it", Picked up keeps counting them; needs a small change in `release_pickup_data.py`, `releases_data.py`, `_rel_counts`); (B) drop "copies" at real outlets and let relmatch's `nearcopy` tier carry it (then change Picked up to include nearcopy, or accept 13 releases turning "Not picked up").
3. The 13 advocacy-organization posts (CAA 10, Common Sense 2, JWW 1): coverage or NOBLOGS? List is in the review CSV under Outlet type "official".
4. 01759 US Fed News: keep your 27 Oct "Unmark", or re-mark.
5. The 8 blank-flag reprints silently hidden under Yes Originals (section 2): give them their own Story IDs, or leave.

**If you confirm, do it in this order (one dedicated step, not a normal save):**
1. Back up the master (unique name, sha recorded); Excel closed.
2. Un-mark subset A first: the 132 rows that are not copies of your releases (list = the 228 minus the 96 in `$S/audit/no228_cats.csv` joined to the tab's Copy story IDs; minus the 13 advocacy posts pending item 3). Set Press release blank, font black, on Coverage and the Originals mirror; fill Role on the 54 blanks by the headline rule; split or swap s01614 (05166) so it shows.
3. Un-mark subset B (the 96 own-release copies) only after item 2 is built and tested on a copy, then re-run `relmatch --stories` for the 85 stories and the tab's derived columns.
4. Merge or accept the 17 duplicate pairs (list in this audit's scratch; the reprint rule can test them).
5. Rebuild on a copy; check: stories 3,908 (or subset count), no "Has copies = Yes / Copies (rows) = 0" rows, Home "Headlines" tile unchanged except for real headline rows, no empty badges, Press releases tab "Picked up" equals the number you intended, every un-marked row black, 0 Yes rows left on non-wire/non-official outlets.
6. Verify sha where the master lives; ledger entry; DECISIONS entry naming the superseded lines; then the PRCOLOR purple pass over the remaining Yes rows.

**Subset sizes:** 228 = 96 own-release copies (85 stories, 77 releases) + 13 advocacy-organization posts + 119 other issuers' releases and reported items at news outlets.

## Evidence index

- Rule and reversals: `docs/DECISIONS.md` lines 35, 102, 123, 136, 141, 225, 311, 422, 534-543; `docs/TONE_GUIDE.md:15`; `docs/HANDOFF_PC_APP.md` section 3 ("Pure press releases … verbatim reposts"); `docs/CONTRACT.md:139`.
- Exclusion and counts: `code/build_data.py:179-200, 212`; `code/make_copies.py:410`; `code/reporter_record.py:141`.
- Original choice and pairs: `code/reprint_rule.py:748-760, 877-879, 1209`; `code/sheet_task.py:1698, 1964, 2802-2831, 2836-2855, 3095-3107, 3596-3610, 4318`.
- Release pages: `build/insights/release_pickup_data.py:153-168`; `build/tabs/releases_data.py:23-24, 101-108, 133`; `build/tabs/releases.js:76-88, 356-357`; `code/relmatch.py:124, 142-144`; `code/relcopy.py:1-30`.
- Page behaviour: `code/tracker/03_overview.js:28, 44-55`; `code/tracker/02_state.js:143`; `code/tracker/15_checks.js:12-18`.
- Save and station: `work/saver/SAVE_RULES.md` (refusal list, answers 1-2); `work/saver/src/saver_steps.py:194-206`; `work/localapp/updatefolder/FORMAT.md` (`rows`); `work/localapp/station/NEWSBANK.md:52-60, 96`.
- Row lists: `work/localapp/PRESS_RELEASE_YES_REVIEW.csv`; own-release copies and categories in `$S/audit/no228_cats.csv`; duplicate pairs and swap list printed by `$S/audit/origchoice.py`.
