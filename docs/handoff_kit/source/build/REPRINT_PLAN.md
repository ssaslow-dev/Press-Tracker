# REPRINT PLAN: synthesis of 3 independent reviews (coordinator, 2026-10-28)
Sources:
- work/tmp_reprintlogic/scheme.md: scheme, matrix, back-test, top-down review
- work/tmp_reprintaudit/findings.md: independent audit
- work/tmp_queuerec/recs_2.csv + process_2.md: 184 origins items

## Agreed by all three (safe to implement)
1. **Membership:** "is it the same text" stays the text rule. Error about 0.3% (audit); 3,043 of 3,166 pass (scheme).
2. **AV:** a segment, episode or clip is never a reprint of text, and text is never a reprint of AV. Second platform, re-air or re-upload = an edition of one item. Known wrong: 00199, 01734, 01762, 07430, s00486.
3. **Aggregators and PR/release services are never the Original.**
4. **Wires never reprint other wires.** AP feeds and state wires are duplicate rows of one item.
5. **Originals order v2:**
   1. eligibility
   2. credit line in the text (add RSS forms such as "appeared first on JNS.org", "Original Location", "Copyright NPR", "(KTLA)")
   3. the reporter's employer on the story date (rank inside a grouping only; freelancers excluded)
   4. originator type (wire, nonprofit, national, network)
   5. byline
   6. earliest date (no same-house date-only swaps)

   Service tier adds JNS, JTA, KFF, HealthDay, VERIFY, Center Square and California Black Media. TCA, TNS and UWire are distributors.
6. **Same paper, web + print (+ "Today's Edition") = one row** (Web + Print convention). Scheme: 172 rows; audit: 10 stories.
7. **Split stories:** the same text under the same author in two stories → merge. Audit: 83 pairs plus a hand-verified list; origins: 120 merges.
8. **Missing originators:** the real originator has no row (scheme: 340 stories; origins: 21) → the originator fetch-add pass (rootfix B).
9. **Wrong saved copies poison matching:** 07052, 08080, 07500 (date), and the 02347/02348 stubs. Fix the data; add a guard in make_copies/fetch.
10. **Merge the four hand lists** (WIRE, AGG, CREDIT, SERVICES) into one outlet type table in outlet_rules.json. Retire mostly_reprint and CREDIT tier 4.

## Needs Sammy (asked 2026-10-28)
- Containment class: trimmed/excerpted copies that credit the service count as Reprints? (33 trimmed credited items; 74 rule failures the scheme would keep)
- Blocked-site originators (LAT, Bee, Chronicle) added as Original rows without a saved copy?
- Translations: reprints (with credit, ≤2 days) or their own stories?
- Hub stories (Scripps/Nexstar): Original = the reporter's home station or the hub brand?

## Execution after answers
1. Code (one agent): type table, order v2, credit forms, reporters module, containment, edition collapse, never-cells, prefilter by type pair, translation rule. Add to the Update button too, with tests.
2. Regroup plan (one agent): apply to the sheet copy. Output every change: swaps, merges, splits, edition folds and originator adds. Show Sammy the merges before writing (standing request).
3. One rule-7 write, rebuild, publish.

## Sammy answers (2026-10-28): containment YES; no-copy blocked originators YES; translations reprint if credited ≤2d; hubs → reporter's home station. All agreed items approved.
