# agent-regroup2-verify — independent check of regroup2 (2026-10-27)

## Scope and independence
I read only README, DECISIONS, the workbook's "Reprint info" and "Audit plan" tabs, and the regroup2_changes.csv columns old_aid, current_sid, current_status, proposed_sid, proposed_status and confidence. I did not open regroup2's scripts, logs, status or summary, or abandoned_regroup. Read-only, no web.

The checker in work/tmp_agent-regroup2-verify/vlib.py was written from scratch:
- Tokens: NFKC, lowercase, apostrophes dropped, hyphenated words joined (ultra-processed = ultraprocessed), PDF line-break hyphens joined, then \w+ words.
- Text that is more than 30% CJK/Hangul is tokenized by character, with a 40-character minimum run.
- Runs: 25-gram (or 40-gram) shingle matching marks covered positions on both sides. Pass means at least 90% of both texts are covered. pass_edge means the pass needs uncovered leading and trailing blocks set aside (≤120 words each, ≤300 CJK characters).
- Text sources, in order: texts/nb json; html_clean (h1, byline, pdf-cap, "Saved" header, script and style dropped); nb_split pdftotext (NewsBank header and citation block stripped).
- Web + Print originals: a row also passes if it passes against the original's print-edition text (Print Article ID).
- No text: exact headline match (case, punctuation and quotes ignored) plus the same set of people in the byline.
- Rows in regroup_exclude.txt are skipped.

## Sample (seed 20261027; unchanged pool shuffled with seed+1; H+A sample seed+2)
- 35 high-confidence splits (pool 685)
- 15 high-confidence merges into existing stories (pool 36)
- 15 high-confidence Original changes within a story (pool 113)
- 15 unchanged reprints with text on both sides
- 10 medium, 10 low
Plus 10 Reprint (unverified) rows and 10 headline+author rows.

Output: work/out/regroup2_verify.csv. Population-wide flags: work/out/regroup2_verify_population.csv.

## Agreement (after reading every disagreement by eye)
| stratum | agree |
|---|---|
| high split | 35/35 (ws-00838 is an edge near-miss and should be low confidence) |
| merge | 14/15 (nb-02294 wrong) |
| original changed | 14/15 (ws-00665: original choice, soft) |
| unchanged reprint | 15/15 |
| medium | 9/10 (nb-03196: original wrong) |
| low | 7/10 (nb-01008 original wrong; pq-00115, nb-01765 wrong) |
Total: 94/100. Each case is explained in the CSV.

## Population scan (all rows, my checker)
- **7 high splits pass the rule strictly against the story they left.** These are errors:
  - ws-00579 ABC News = CBS-7 WHIO nb-01354, 99.6/100.
  - ws-00060 Washington Times = AP nb-00078, 93.1/97.4 (includes a podcast widget).
  - ws-00360 Sierra Sun Times = TNS nb-00616, 95.6/92.3.
  - ws-02989 Korea Times = Yonhap ws-02991, 94.3/90.8 CJK. This also contradicts the Yonhap-over-Korea-Times decision.
  - Borderline copy-edited case: nb-03281, nb-03288 and nb-03290 vs nb-03278, 91.4/91.3.
- **51 high splits pass only once edge lines are set aside.** DECISIONS says such near-misses are reprints once Sammy confirms them in the queue, so they should be low confidence and queued, not auto-split. Check whether they are among the 209 queue items.
- **32 unchanged different-outlet reprints fail the strict rule** (about 1.7% of keeps with text). Main clusters:
  - jg-00908: the long AP version (CBS, KCRA, NBC LA, plus Fox and Westerly) sits under the short AP State Wire version.
  - Several CalMatters stories (nb-01415, nb-01663, nb-00436, nb-00465, nb-00573, nb-03843). Republishers drop sidebars and boxes.
  - pq-00004 TCA vs Press Democrat: 605 extra words.
  - Sac Bee to Georgia and McClatchy trims of more than 10%.
- **14 same-outlet rows labeled Reprint whose text fails.** Examples: Sac Bee print vs web, Pasadena print vs web, LA Times pq vs ws. Either they are Web + Print edition merges or they are separate stories. Sammy should decide; Reprint is the wrong label either way.
- **13 no-text NewsBank print-page rows kept as reprints although the headline differs.** Examples: "SPECIAL SESSION TO SHORE UP PRIORITIES…" ×10, and "California - Summertime blues…" (section prefix). By the rule each would be its own story; by eye they are plainly the same pieces.
- Reprint (unverified): 10/10 reasonable. Every row is a tracker reprint-list row with no text, attached to the story that holds its tracker code.
- Headline+author: 10/10 sampled correct (435 H+A keeps are clean; the 13 failures are listed above).

## Systematic issues
1. **Edge lines:** high-confidence splits include about 51 edge near-misses.
2. **NewsBank clutter:** the CalMatters NewsBank texts DO contain web chrome ("Lea esta historia en español", "Become a CalMatters member", sign-up boxes, "Learn more about legislators mentioned in this story"). The Reprint info tab says NewsBank texts have no web clutter, which is wrong for CalMatters. This pushes CalMatters originals under 90%.
3. **Print vs web:** reprints of a Web + Print original often match only its print text. With a web-only check, 43 more keeps fail. The proposal seems to handle this.
4. **CJK:** one wrong high split (Korea Times/Yonhap). One CJK keep (ws-02412) fails because of a 302-character ad block at the end (edge).
5. **Long and short versions of one wire story** (jg-00908): no-chaining is not being enforced against the original in at least this story.
6. **Original order:** three misses in the sample (byline-names-outlet tier, Yahoo aggregator tier, and a soft NewsBank-over-tracker tie). The tier logic for bylines that credit another outlet works elsewhere (ws-00146, nb-00973, ws-03147).

## Recommendation
Approve the high tier only after fixing the following. Medium and low are already queue items and are fine to queue.
- Revert the 7 strict-pass high splits.
- Move the 51 edge near-miss high splits to the queue.
- Fix jg-00908.
- Fix the 3 original picks (nb-03196, nb-01008, ws-00665 for Sammy).
- Add the 32 failing keeps and the 13 headline-mismatch print pages to the queue.
