# agent-queue-add (2026-10-28): translations accepted; tags + outlet items queued; labels prepared

Queue https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB. Owns: decisions rv2translation-* (52 listed below), items/24-tags, items/24-tags-2, items/24-outlet; work/tmp_queue_add/. Sheet, code/, Mac: not touched. Create-only throughout (no if_version, so no existing doc could be overwritten); batches ≤ 50.

Read before (work/tmp_queue_add/before/): 32 items docs (1,711 items, ids unique), 1,633 decisions (= 1,440 + queue-tidy's 193).

## 1. Translations (done)
- Rule: cat translation, conf high, no decision → choice = proposed ("Apply"), note "Auto-accepted: high confidence (Sammy 2026-10-28)", by "Claude (Sammy's instruction)", at 2026-10-28T21:41:12Z. Files dec/<id>.json.
- 52 creates (batches 50 + 2), all version 1: rv2translation-001…016, 018…044, 046, 047, 049…055. Translation now has 3 undecided (the medium ones).
- Read back: 52 docs by "Claude (Sammy's instruction)", each equal to its file; decisions total 1,685.

## 2. Tags (items/24-tags, 24-tags-2; cat "tags"; ids tags-000…302)
Source work/tmp_tags_apply/review.csv (335 rows). Builder work/tmp_queue_add/build.py → new/*.json.
- **Sammy decision applied, not queued: ABX1-1 / ABX1-2 = LEAVE UNTAGGED.** 21 rows dropped (18 sole-authorship rows proposing "ABX1-1; ABX1-2" + 3 bill-match rows proposing one of them; 19 Originals: 01677, 01698, 01699, 01712, 01753, 07991, 08020, 08028, 08032, 08034, 08035, 08036, 08038, 08039, 08041, 08043, 08044, 08046, 08058). Rule: the row only adds bills ⊆ {ABX1-1, ABX1-2}. List in dropped.json. Nothing to write to the sheet (Bills stays as it is on those rows).
- **Inclusion-wave listings (10): 6 dropped, 4 queued.** Dropped because tmp_incl_apply/plan.csv removes the row to the Removed tab: 04694, 05208, 09287, 09485, 09648 ("3 not coverage"), 09199 ("3 database/results page"). Kept: 04774, 04880, 09735, 09737 (plan only sets Mention depth; the row stays, so the tone call stays): options "Keep Tone Neutral" / "Clear Tone", proposed Keep.
- 308 rows left → **303 items** (5 exact-duplicate cells merged: same article, column, current, proposed; evidence lines joined).
- Item: {cat, conf, id, key "story:article:column", title, detail (story · article · outlet · date · headline · now → proposed · rule · evidence · proposal + reason), options [change, leave], proposed}. Options come from the row: Bills "Add X" / "Leave Bills as is (…)" (or Remove/Keep, Set), Tone "Clear Tone" / "Keep Tone …", Topic/Role "Set … to" / "Keep …", Date "Set Date to 2024-09-03" or "write the right date in the note" / "Keep Date …", Tone note Replace / Keep.
- Proposed answer (the change is always the first option): leave for low bill matches Sammy's rules already rule out (Budget Act number, number credited to another member, earlier-session list number, named before introduction, coauthor with only a weak cue) and for sole-authorship / before-introduction rows; change for ABX1-4 (policy bill, names it), role / note fixes, low reads, reviewer cross-checks, no-Gabriel tone clears, date fixes, and the 2 AB 1807 anachronisms (the AB 1836 one: keep the tag, fix the date).

| rule | items | conf | proposed change / leave |
|---|---|---|---|
| bill match, low confidence | 198 | low | 13 / 185 |
| reviewer cross-check | 29 | low | 29 / 0 |
| no Gabriel mention per note (verify) | 22 | medium | 22 / 0 |
| no Gabriel mention | 15 | **high** | 15 / 0 |
| sole authorship | 13 | low | 0 / 13 |
| role fix | 7 | medium | 7 / 0 |
| before introduction | 6 | low | 0 / 6 |
| inclusion-wave listing | 4 | **high** | 0 / 4 |
| anachronism | 3 | low | 2 / 1 |
| read text, low | 3 | low | 3 / 0 |
| date check | 2 | medium | 2 / 0 |
| note fix | 1 | **high** | 1 / 0 |
| total | 303 | 252 low / 31 medium / 20 high | 94 / 209 |

**Flag:** review.csv is not all medium/low: 26 rows are "high" (15 no-Gabriel, 10 inclusion, 1 note fix); 20 survive as items and keep conf high, so the Content tags tab shows the "Accept all high-confidence" button for them. Downgrade them if no tags call should be bulk-acceptable.

## 3. Outlets (items/24-outlet; cat "outlet"; 143 items)
Source work/tmp_outlet_design/ (design.md §5, changes.csv, outlets_proposed.csv).
- changes.csv corrections 550 = 84 Sammy-backed (not queued, applied at v22 per coordinator) + **466 queued**. Fills (3,501) and variant-keep (685) not queued.
- **13 question items outlet-q01…q12, q14** (§5 wording, options, the designer's recommendation pre-selected). Q13 (bare-majority outlets) has no item of its own: it is answered by the 15 per-outlet items it covers (conf low, detail says "§5 Q13"). Cells folded into a question item instead of an outlet item: Q1 row-level language tags (16), Q5 Politico (23), Q8 FoodNavigator-USA (12), Q12 Substack/Medium names (35 rows, 28 *.substack.com / *.medium.com keys; design.md's "33" counted a wider set, and the rest such as podbean hosts stay as per-outlet items), Q14 mis-folds (24, "do not apply").
- **130 per-outlet items outlet-000…129**, one per outlet key with its remaining corrections (356 cells): detail = record (rows, type, Reach + source, Format) and each change "field: old → new ×n [basis] (rows …)". Options "Apply all", "Apply <field> only" per field when more than one, "Skip"; proposed Apply all.
- Conf: medium, or low where a cell rests on a bare sheet majority (16 items). None high on purpose: every correction overrides CONTRACT blanks-only and needs Sammy's sign-off, so none should be bulk-accepted.
- Q2 (SF Chronicle) and Q11 (Denver Gazette) concern Sammy-backed corrections the coordinator applies at v22; each item says so and the second option reverses it. If Sammy picks the reversal, drop those cells from the v22 write.

## Read back (after/)
35 items docs: the 32 earlier docs are equal to before/; 24-tags (223), 24-tags-2 (80), 24-outlet (143) are equal to new/. 2,157 items, ids unique. 1,720 db docs = 35 items + 1,685 decisions.

## 4. Page labels (prepared, NOT published)
- Live re-read: version 1793223348-eb68 (as expected). Saved: work/tmp_queue_add/live/index.html = review_page.html.
- work/tmp_queue_add/page_edit.json: one edit (anchor = the addorig line + "};", occurs once) adding
  - tags: label "Content tags", note "Lower-confidence tone, issue and bill calls from the content-tags review."
  - outlet: label "Outlet corrections", note "Outlet-level corrections (Reach, Format, location, publisher, name) that change an existing value." ("Outlets" alone would sit next to the existing "New outlets" tab.)
- Result review_page_edited.html: the edit reproduces it; the script passes node --check; CATS parses (31 keys). Apply with Artifact publish url + edits; leave out capabilities (db stays).
