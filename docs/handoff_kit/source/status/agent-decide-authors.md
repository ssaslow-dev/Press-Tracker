# agent-decide-authors — 2026-10-27

Tabs: 15-authors (48), 16-checks (21). Queue: https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB.
Wrote 67 decision docs ({choice, note, at, by "Claude (auto)"}). Both batches were create-only (no if_version) and committed atomically; no decision docs existed before for these ids.
Outputs: work/out/decided_15-authors.csv, work/out/decided_16-checks.csv, work/out/decided_checks_rows.csv (51 per-row changes: aid, field, new_value, evidence). Helpers: work/tmp_agent-decide-authors/.

## 15-authors: 48 decided, 0 left
- Role-only bylines → proposed "(no name), title …": authors-000, 001, 004, 005, 010, 016, 020.
- Kept as the publisher credits them (no surname anywhere): Daniel (002; deltacollegian meta-author), Sharon (008), Randall (009; live AsAmNews page has no byline), Jay F. (013; the Substack credits "Jay F."), Mariam (017; Alphanews "Written by Mariam"), Kevin (019; the sidebar names a Kevin Deenihan, but that doesn't prove he wrote the post).
- Knock LA Editorial (018) kept as a group author: Knock LA has an author page knock-la.com/author/knock-la-editorial/.
- "Edit authors" (the new names are in each note):
  - 003 ws-00386 → Claudia Boyd-Barrett (copy says "By Claudia Boyd-Barrett"; "Lisa P" is not the author)
  - 006 → 8th author is Sarah A. Gaskell (NewsBank "Gaskellrn" had a line break glued on)
  - 007 → Thomas Peele
  - 011 → one author, Catherine Gewertz (NewsBank had it reversed)
  - 012 → Lori Porter
  - 014 → adds a 9th author, Brooke Curto
  - 015 → Keyshawn Davis
- Same-person pairs 021–037: all "One person".
- Merged: 038 Koseff, 039 Antonio Ray Harvey, 040 Yarbrough, 042 Boyd-Barrett, 043 Haven Daley, 044 Kate Rodgers (same CalMatters commentary), 047 The Triplicate.
- Kept apart as "Different people":
  - 041 California Playbook vs Playbook PM (two separate newsletters)
  - 045 Nic Robertson (CNN) vs Nick Robertson (The Hill)
  - 046 Tara Nguyen (LA Magazine) vs Trân Nguyễn

## 16-checks: 19 decided, 2 left
- A: keep both. B1: fill "No" and keep. B2: keep (the NewsBank texts nb-03972 and nb-03965 name Jesse Gabriel).
- C: "Fix: use the copy's byline", but ONLY for 8 rows: ws-00175 and ws-00490 → Sophie Austin; ws-00644 and ws-00732 → Adam Beam; ws-00621 → Alexei Koseff; ws-00777 → Ben Christopher; nb-02516 → Antonio Ray Harvey; pq-00300 → David Skale. The other 60 keep the sheet value.
- D1, D2: keep.
- E: "Fix: use the page date", but ONLY for ws-01532 → 2026-09-01 (live ToI page) and ws-01294 → 2024-03-18 (the sheet had only "2024-03"). The other 47 keep.
- F: drop the 5 wrong header lines (verified the KCRA grenade URL). G: keep.
- H: keep. The note is California Black Media's syndication slug to subscribing papers, not The Observer's print data.
- I: keep. J: strip the notice. K: remove the photo. L: use the page headlines.
- N: keep. O: keep blank.
- Q: merge to Persian. All 7 Arabic/Persian rows are Persian text.
- R: move to _to_delete. S: re-check the rows.

### Left for Sammy
- **checks-M (267 word counts):** overwriting existing values is a policy override. Many nb- counts are NewsBank's own count for the print/NewsBank version, which can rightly differ from a web copy. The clutter and CJK cases are clearer, but they can't be split out from a single group choice.
- **checks-P (two counts per row):** "larger" or "smaller" doesn't fit as one rule.
  - ws-02871: the plain copy 2023/ws-02871.html is a DIFFERENT item (The Homework newsletter 2023-11-22). Only the jg-e41972 copy matches the sheet headline, so its count (437 per the bucket) is the right one. **The plain copy should be treated as an error copy.**
  - For the others, the suggestion is the count of the copy that matches the row's version:
    - pq-00096 and pq-00211 (ProQuest rows): the ProQuest-text copy (925 and 1446).
    - ws-01932 (web row): the web copy jg-7f5959, 598.

## Open flags (not changed)
- ws-02737 HS Insider: the sheet says "Summer Park" but the copy's byline is "Tamar Koren-Pinto". The live page was blocked, so the sheet value is kept.
- nb-01006 Sentinel: the copy reads "By Lila Brown", but the live page credits Lila Brown only for the photo. NewsBank's "Cora Jackson-Fossett" is kept.
- ws-00200: the CBM print note at the end of the copy is not article text. It could be stripped under the scalpel rule; this agent did not act on it.
