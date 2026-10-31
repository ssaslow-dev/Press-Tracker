# agent-peoplelookup (2026-10-28)
Scope: ONE-TIME Exa exception (DECISIONS 2026-10-28): a people-research lookup on Jesse Gabriel only. No workbook writes and nothing published.

1. **Skill:** loaded mcpmarket-me:people-research. It runs as a forked subagent. The first call, made with no target, returned a request for one. I re-ran it with the seed profile as its input. It ran 18 web_search_exa queries; web_search_advanced_exa is not available.
2. **Seed:** identity and roles from the brief; top bills from the Coverage Bills column (AB 418, 2316, 1264, 28, 2244, 1127, 587); top topics; the excluded wrong Gabriels.
3. **Dedupe set:** 13,115 links from all Coverage link columns, plus 7,786 outlet+headline pairs. Work files are in work/tmp_peoplelookup/ (dedupe.json, rows.json, results.tsv, all_results.csv, check.py).
4. **Results:** 59 linked results, plus about 15 mentions without URLs.
   - 9 profile and reference pages
   - 44 already in the sheet (by link, or by same outlet, date and headline)
   - 4 not in the sheet but rejected: The Verge 2022-09-14 does not name Gabriel in its text; 3 Digital Democracy hearing transcripts are database pages
   - 2 new: J. 2003-11-28 Hillel feature; gov.ca.gov 2022-09-13 AB 587 signing release
   - 1 link update: cnn.com URL for row 08224
   - The unlinked mentions all match sheet rows (Spectrum 08942, Ars 09140, AP 04141/04142, Politico 07848/07821, KCRA 07753, MyNewsLA 09688/09689/05220, Fresno Bee 01226, CJAC 07735, Cool Down 07107, Bakersfield 00023). The skill also says the op-ed ran in the Santa Maria Times and MSN; those rows (00024, 00025) are still "Reprint (unverified)" with no date or link, and the skill gave no URLs to confirm them.
5. **Exa fetches for screening:** the 4 candidate URLs (CNN, Verge, J., gov.ca.gov).
6. **Reprint check** (code/reprint_rule.py text_verdict): the gov release does not pass against TNS 04126 (0.88/0.82) or TendersInfo 04065 (0.74/0.98). The CNN fetch was truncated, so I used the headline+author fallback: same story as 08224. The J. piece has no candidate originals.
7. **Outputs:** work/out/gabriel_profile.md and work/out/peoplelookup_finds.csv.
8. **Exa cost:** the tool did not show it.
