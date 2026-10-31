# Press releases tab: UX review and proposal (agent relreview-ui, 2026-10-28)

Build reviewed: live v20.1, work/tmp_agent-v20b-subtitle/pub/index.html (sha c252e5a1…, same as live). Served from
work/tmp_relreview_ui/srv (symlinks to tmp_agent-v20-final/pub2 data), harness shot.js (v20b copy, also writes <name>.json).
Shots: `S = L/work/tmp_relreview_ui/shots/` (68 PNGs: 1400 and 390, light and dark). Samples: pr00154 (4 pickups, 7 related,
bill), pr00139 (0 pickups, 53 related, 17 possibly related), pr00001 (nothing), s02140 (not posted officially).
Read-only review: no code, sheet or publish changes. Owners: build/tabs/releases.js (tab), code/tracker/53_tabs.js (shared
page shell, list shell, viewer stand-in), build/tabs/bills.js (bill links).

Effort: S = under 1 h, M = 1–3 h, L = half a day or more.

## What a reader sees today (measured)

- Release page at 1400: header card 178–472 px, then one "extra" card holding five stacked sections, each with a rule
  paragraph; chart at 1009; related-story list at 1128. pr00139 page is 4,912 px tall.
- At 390 (pr00139): saved copy at 944 px (below the first screen), Copies at 1075, Related caption at 1401, chart 1634,
  list 1752. Page is 7,916 px tall.
- The saved copy (the "preview") is a plain title row under the small-caps label "SAVED COPY OF THIS RELEASE". Nothing
  says "read" or looks like a button. One click opens it in the story viewer, after a scroll on phones.
- Every release has a saved copy (244/244), so the preview is never optional. It should be the page's main action.

## Ranked changes

### 1. Make the release text the first thing on the page (M)
Problem: the preview is a list row titled like a heading, below the header card, with a caption explaining it
("The release as posted, saved and cleaned like an article. Click the title to read it in the article viewer.").
On phones it is below the fold. Clips opens a story's text with one click on the headline; here the reader has to find a
second copy of the title. S/r_pr00154_rich4pickups_full_1400_light.png, S/r_pr00154_rich4pickups_top_390_dark.png,
S/r_pr00001_empty_full_1400_light.png.
Change:
- In the header, under the dek, a button row: **[Read release]** (primary `.btn`, opens the same viewer as today via
  `data-relprev`) and **Official release ↗** (the existing link with its copy icon). Add a short muted note after them:
  "667 words".
- Delete the "Saved copy of this release" section and its caption (savedRow) entirely. Its facts (source, date, words,
  prid) are already in the kicker or not needed by a staffer; prid can go in the CSV only.
- The title itself (h2) also opens the viewer (cursor pointer, title="Read the release"), the way a Clips headline does.
- Desktop ≥1100 px, optional second step (L): show the first ~80 words of the release under the button row in a quiet
  quote block with "Read the full release ›". release_texts.json is already fetched when the page opens (loadTexts in
  page.find), so no new data. Not a full side-by-side layout: the viewer already gives side-by-side reading at 1400
  (S/v01_release_viewer_pr00154_1400_light.png), so a second reading pane would duplicate it.

### 2. Clean up the viewer when it shows a release (M, 53_tabs.js tbOpenSaved + viewer)
Problem: the release opens through a stand-in story record, so the viewer shows story controls that mean nothing for a
release: an empty meta line "· · · No reprints", "Publisher site ↗ gabriel.asmdc.org", "Edit details", "Tone: not rated
yet. [Set tone]", "TEAM NOTE … Notes are shared with everyone who opens the tracker.", and "1 of 1".
S/v01_release_viewer_pr00154_1400_light.png, S/v01_release_viewer_pr00154_390_dark.png. Copies (data-relsaved) get the
same treatment: S/v02_copy_viewer_pr00154_1400_light.png.
Change: when the record is `_copy` (stand-in), the viewer shows only kicker (date · source), title, one link row and the
text with Gabriel highlighting. Link label "Official release" instead of "Publisher site". Hide reprint meta, Edit
details, tone, team note. Give "1 of N" navigation over the page's copies when opened from the Copies list (pass the
list's ids to openViewer the way story rows do), and over [release, its copies] when opened from Read release.

### 3. Replace the five rule paragraphs with one-line labels and ⓘ tooltips (S–M)
Problem: this is the core of Sammy's complaint. Quoted as shown, with the proposal for each:

| Where | Current text | Proposal |
|---|---|---|
| Saved copy cap | "The release as posted, saved and cleaned like an article. Click the title to read it in the article viewer." | Cut (section goes, item 1). |
| Copies cap | "Sheet rows whose saved text passes the reprint text test against this release (runs of 25 or more identical words covering 90% of both; distribution-service excerpts count). They are copies, not tracker stories." | Heading "Ran the release · 4" + ⓘ tooltip: "Outlets that printed the release itself, word for word or nearly so." |
| Copies empty | "No outlet in the spreadsheet ran this release." | "No outlet ran it word for word." (muted, one line) |
| Bill before/after section | "0 tracker stories on AB 2867 in the 7 days before the release; 8 on the release day or the 7 days after. These are counts of all coverage of the bill, for context; they are not the related stories." | Cut the section. The same numbers are already in the header ("Bill coverage 0 before → 8 after"). Keep that fact, relabel "AB 2867 coverage", value "0 week before · 8 week after", ⓘ "All stories on the bill, not only ones tied to this release." |
| Header fact suffix | "same bill, 7 days" (sub after the value) | Cut (moves into the ⓘ above). |
| Header fact, no bill | "Not counted (no bill)" | Omit the row (the header already drops empty facts). |
| Possibly related cap | "Tracker stories on the same bill in the same week whose subject could not be checked: they are not in English, or there is no saved text. Not in the chart or list below." | Summary "Possibly related · 17" + ⓘ "Same bill, same week; not confirmed (no English text to check)." |
| Related cap (with stories) | "Tracker stories linked to this release by evidence: 21 uses the release text, 5 quotes the release, 27 same bill, same week. “Uses the release text” = runs of 25 or more identical words, up to 90 days after; “quotes” = shorter quotations, up to 30 days after; “same bill, same week” and “same week, same subject” = within 7 days and on the release’s subject; “covered the announcement before the release” = up to 14 days before, on the same announcement. Shown in the chart and list below." | Heading "Related stories · 53" + one line "21 used its text · 5 quoted it · 27 same bill, same week" + ⓘ with the definitions, one per line, plain words ("Used its text: shares long passages, within 90 days." etc.). Also fixes the grammar ("21 uses"). |
| Related empty | "No tracker story is linked to this release by its text, its bill or its subject." | "No related stories." |
| Links fact, not posted | "Not posted on Gabriel’s or the Jewish Caucus’s site." | Kicker already says "Not posted officially". Drop the Links row for these releases. |
| List caption | "Every release from Gabriel’s office and, from Nov 18, 2020, the Jewish Caucus he leads (the spreadsheet’s Press releases tab), plus releases outlets ran that are not posted officially." | "Releases from Gabriel’s office and the Jewish Caucus." Rest into About. |
| About this list | "Pickups are sheet rows that carry the release’s own text. Search covers titles and deks, and the full release text once it loads (the first time you search). Click a release to open its page." | "Jewish Caucus releases from Nov 18, 2020, when he became chair. Also lists 5 releases outlets ran that were never posted. Pickups = outlets that ran the release word for word. Search covers the full release text." Drop "Click a release to open its page" and the loading mechanics. |
| Answer line | "241 releases, 88 picked up (112 copies). 176 have related tracker stories. Of the 174 with a bill, 27% had coverage of that bill in the 7 days before and 64% on the release day or the 7 days after." | "241 releases · 88 picked up (112 copies) · 176 with related stories." Cut the bill percentages (same before/after context stat; it is a 2-line sentence on every load). If Sammy wants it, put it in About. |
| Date facet hint | "Release date (official date, or the first run for a release not posted officially)." | Cut. |
| Search states | "Searching full text…"; "Full text could not be loaded; searched titles and deks." | Keep (short, only when relevant). |
| Empty list | "No releases match. Clear all filters" | Keep. |
| Chart notes | "All 53 stories here ran in Oct 2023, so there is no chart." / "Only 3 stories, so no chart: …" | Moot if item 6 drops the chart. |
| Export sub | "Date, title and official link, one release per line" | Keep. |

S/r_pr00154_extra_card_1400_light.png, S/r_pr00139_nopickups53rel_top_1400_dark.png, S/r_pr00001_empty_full_1400_light.png,
S/r_notposted_s02140_full_1400_light.png, S/l03_list_about_1400_light.png, S/l01_list_top_1400_light.png.
ⓘ: the tracker has no ⓘ component yet that I found; a `<button class="linkbtn tb-i" title="…" aria-label="About …">ⓘ</button>`
with a tap-to-toggle popover (title attributes do not show on phones) is the shared piece. Effort S for the copy, M for a
shared ⓘ in 53_tabs.js.

### 4. Say which evidence links each related story (M, needs a 53_tabs row hook)
Problem: the related list is the generic story table; no row says whether the story used the release text, quoted it or
only shares the bill. The cap lists counts, but the reader can't tell which 4 of the 7 used the text. pr00154: "Vince
Fong’s ballot battle isn’t over" sits in the list with nothing saying why. S/r_pr00154_rich4pickups_full_1400_light.png,
probe S/p04_links_probe.json (no evidence word in the row).
Change: a small tag in each row's meta, Clips tag style: "Used release text" / "Quoted it" / "Same bill" / "Same subject" /
"Before release", plus a filter chip set "How it's related". releases.js already has x.type and x.lag per story; the page
shell needs `P.rowAs` (exists) to carry a tag and the row renderer to print it. Default sort for this list: evidence
strength, then date.

### 5. One section order, no duplicates (S–M)
Problem: section order today is header → saved copy → copies → bill before/after → possibly related → related caption →
chart → filters + list. "Possibly related" (weaker) comes before "Related" (stronger) and uses a different row style
(copy rows with link stacks, S/r_pr00139_possible_open_1400_light.png) from the related table. The Related caption sits
in the extra card, detached from its own list, which starts after a chart. "Official release ↗ gabriel.asmdc.org"
appears twice (header Links row and saved-copy row). "PRESS RELEASE" kicker and "Type: Press release" fact repeat each
other (205 of 241 releases are type Press release).
Change, top to bottom:
1. Header: kicker = type · date · source (use the real type: "STATEMENT · OCT 1, 2026 · JEWISH CAUCUS"; drop the Type
   fact), title, dek, button row (item 1), then the facts grid.
2. Facts grid: Who (Others named, Gabriel quoted) · What (Issue, Bills) · Coverage (Ran it, Related stories, AB xxx
   coverage). No Links row (the link is in the button row).
3. "Ran the release · N" (copies), only when N > 0; with 0, the header's "Ran it 0" is enough.
4. "Related stories · N" heading + one-line breakdown directly above its search/filter bar and list.
5. "Possibly related · N" collapsed, below the list, in the same story-row style.
Section labels: "Copies of this release" → "Ran the release"; "Related stories" stays; "Possibly related" stays.

### 6. Drop the "Coverage over time" chart on release pages (S)
Problem: related stories fall within −14…+90 days, so a by-month chart has 1–4 bars or turns into a sentence
("All 53 stories here ran in Oct 2023, so there is no chart."). pr00154 shows "Coverage by month" with an empty Jan and
Feb 2024 (S/r_pr00154_rich4pickups_full_1400_light.png). It pushes the list down 120–1,000 px.
Change: `chart: false` in releases.js page.spec. If Sammy wants a timing view, a one-line day strip in the Coverage
cluster: "Same day 4 · Days 1–7 2 · Later 1". Effort S (drop) / M (strip).

### 7. Bill numbers are plain text until the Bills tab has been opened (S–M, bug; open thread C3 / d38d2b91)
Problem: in the list rows and the release header, bills render as plain text. Cause found: `tbBillLink` gets '' from
bills.js `billSlug` on a fresh load; after visiting #bills once in the session, the same header renders
`<button class="linkbtn tb-bill" data-bill="AB 418">`. Probes S/p04_links_probe.json (plain span) vs
S/p07_bill_after_billsvisit.json (link). So C3 is not only styling: links are missing for anyone who lands on Press
releases first. Likely in bills.js build()/CTX state on first call through tbCtx('bills'); owner of bills.js to confirm.
Change: fix the init so billSlug works on first call; then render list-row bills as the Clips bill chip (gray pill, as in
the related list's "AB 2867" chips), not inline in the gray meta text.

### 8. List row and columns (S–M)
Problem (S/l01_list_top_1400_light.png, S/l02_list_full_1400_light.png):
- Every row's sub line starts "Press release ·" (205/241). Noise.
- "Pickups" shows 0 on 153/241 releases (69 zeros in the first 100 rows), a column of zeros; and a release like pr00139
  shows 0 while 21 tracker stories used its text. To a staffer, both are "pickups".
- No column for related stories, the tab's most useful number (176 releases have some).
- Sort menu offers "Sort: release" (title A–Z), which nobody needs.
Change:
- Sub line: issue · bill chips; add a type tag only when type ≠ Press release ("Statement", "Letter").
- Columns: Release · Date · Source · **Ran it** · **Related**. Zero shown as a muted "–". (Alternative, one column
  "Coverage": "2 ran it · 7 stories".)
- Sort options: date, ran it, related stories. Drop "release" (title).
- Question for Sammy, not decided here: should "Ran it" also count tracker stories with type `text` (uses the release
  text)? That changes a count's meaning, so it is his call (README rule 4).

### 9. Filters (S)
Problem: "Picked up" (All / Picked up / No pickup found) and "Number of pickups" (None / 1 / 2 or 3 / 4 or more) overlap;
"None" = "No pickup found". S/l05_list_filters_open_390_dark.png, S/l06_list_rail_1400_light.png.
Change: one facet "Ran it": Any · None · 1 · 2–3 · 4+. Rename "Related stories" options "Has related stories / None" →
"Some / None". Rename "Outlet that ran it" → "Outlet". Keep Source and Picked-up open by default → keep Source open only.

### 10. Mobile (S–M)
Problem (S/l01_list_top_390_dark.png, S/r_pr00154_rich4pickups_full_390_light.png):
- List: before the first row, the reader scrolls past a 4-line caption, "About this list", a 4-line answer sentence,
  search, Filters + Sort, Export: first row at ~590 px of 844. Each row then spends three lines on "DATE: / SOURCE: /
  PICKUPS: 0" labels.
- Page: saved copy below the first screen; header facts stack to ~600 px; the related list starts at 1,752 px.
- Possibly-related disclosure triangle hangs outside the card's left padding (also at 1400:
  S/r_pr00139_nopickups53rel_top_1400_dark.png, x≈20).
Change: items 1 and 3 fix most of it. Row meta on phones: one line "Oct 24, 2026 · Gabriel’s office · Ran it 2"
(no field labels). Put Export inside the Filters/Sort row as an icon button. On phones collapse the Who cluster to one
line ("Others named: Bonta, Harris, Kounalakis +1 · Quoted: Yes"). Fix the summary marker (`list-style-position:
inside` or a custom chevron, as other details use).

### 11. Consistency with Reporters, Outlets, Bills (S)
- Reporters/Outlets lists show linked cells (dates, issues) and an answer line of one sentence
  (S/o_reporters_list_1400_light.png). Releases' answer line is two sentences with a statistic; trim (item 3).
- Bill page has "Press releases 24" as plain text (S/o_bills_page_1400_light.png). Make it a link to
  #press-releases filtered by that bill (facet `bill`), the cross-tab rule in LINKRULES-v1.
- Bill pages show a one-line dek summary ("Author of the bill. 422 stories …"). Release pages use the release's own
  subtitle as the dek; keep that (it is real content), don't add a generated summary.
- Story viewer opened from a related row is the normal panel with "1 of 7" navigation
  (S/v03_related_story_viewer_pr00154_1400_light.png): good, and the model for item 2.

## Mock: redesigned release page, top section (1400)

```
‹ All press releases
┌────────────────────────────────────────────────────────────────────────────┐
│ PRESS RELEASE · MAR 28, 2024 · GABRIEL'S OFFICE                            │
│ Assemblymember Jesse Gabriel, Lieutenant Governor Eleni Kounalakis         │
│ Announce Legislation to Help Holocaust Survivors Recover Stolen Art        │  ← title opens the viewer
│ AB 2867 Introduced Following Recent Court Decision Allowing Spanish ...    │
│                                                                            │
│ [ Read release ]   ⧉ Official release ↗ gabriel.asmdc.org   · 667 words    │
│ “<first ~80 words of the release text> …”  Read the full release ›        │  ← optional 80-word lead
├──────────────────────┬──────────────────────┬──────────────────────────────┤
│ Others named  Bonta, │ Issue  Antisemitism /│ Ran it            4          │
│   Harris, Kounalakis │        Jewish comm.  │ Related stories   7          │
│   +1 more            │ Bills  [AB 2867]     │ AB 2867 coverage  0 → 8 ⓘ    │
│ Gabriel quoted  Yes  │                      │                              │
└──────────────────────┴──────────────────────┴──────────────────────────────┘
RAN THE RELEASE · 4  ⓘ
  Legislation Aims to Help Holocaust Survivors…   Contra Costa News · Mar 28 · same day   Publisher site ↗
  … (3 more rows)
RELATED STORIES · 7  ⓘ      4 used its text · 1 quoted it · 2 same bill, same week
[Filters] [Search 7 related stories        ] [All dates] [Export]
  Apr 4, 2024  Law will help Holocaust survivors…  Beverly Press · [Used release text]   …
▸ Possibly related · 2  ⓘ
```
At 390 the same order; the button row wraps to [Read release] full width with the official link under it, so the release
text is one tap from the first screen.

## Not checked
- Full-text search hit display: "fentanyl" returned 0 releases (S/l04_list_search_1400_light.png); I did not confirm
  whether that is a true zero or the texts had not loaded within 3.5 s.
- Screen reader / keyboard order, and 390 shots of the other tabs.
