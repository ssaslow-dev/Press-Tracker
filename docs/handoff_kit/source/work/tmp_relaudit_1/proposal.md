# Press releases tab: mapping audit (reviewer 1)

Baseline (pub2 build plus release_related.json): 241 releases. 88 have copies (112 sheet rows), 174 have tracker related stories, 67 have none, and 40 have neither copies nor related stories. Evidence types: text 593, bill 348, quote 77, topic 42, possible 152. 942 tracker stories are related to some release. The pre-release window issue (pr00244/s01827) is left out because it is already being fixed.

## Ranked improvements

### 1. Count tracker stories that reprint the release as pickups (S/M)
**Problem.** Copies come only from Coverage rows flagged Press release = Yes. Some tracker stories reprint a release almost word for word, but the flag was never set on them, so they appear only as "uses the release text". Example: pr00139 (AB 418 signed) shows **Pickups 0**, yet SFV Sun s00837 reuses 53% of it and Lake County Record-Bee s00859 reuses 71%. 24 stories reuse at least 50% of a release that is 250 words or longer. They cover 21 releases, **15 of which now show 0 pickups**.
**Rule.** Run `reprint_rule.text_verdict` (the RELRULE test) on every text-evidence story, not just flagged rows. If it passes, flag it Press release = Yes and count it as a copy.
**Gain.** About 24 copies. 15 releases move from "No pickup found" to "Picked up".
**Risk.** Low. My hand check found 22 of 24 to be reprints. Two need review: s02336 and s02437 match pr00200 at 92%, but their headline is about a later signing, and s02437's date (2025-08-26) looks wrong.

### 2. Give the matcher data it already has but ignores (S)
**a. English translations.** "Possible" exists because the topic cosine runs only on English text. But 137 of the 152 possible pairs are non-English stories that carry `text_en`/`hl_en`. Scoring the translation (cos ≥ 0.14 or headline ≥ 0.10) promotes **103 of 152** to related across 39 releases. The other 49 stay possible; don't drop them, because some are short summaries such as s01865 and s01934. The translations also add **20 new topic links** (cos ≥ 0.25 within the week).
**b. Bill numbers named in the story text.** 172 stories name a release's bill in their text without carrying the bill tag. 78 of them are linked to no release. Treating "the text names the bill" as a shared bill, with the existing on-topic check, adds **22 stories to 16 releases**. My sample: 11 of 12 related. Examples: SF Chronicle s00893 "Newsom signs new gun tax" (pr00137, same day) and LA Times s00560 (pr00174). The same rule could backfill the stories' Bills tags, which also helps the Bills tab. List: `bill_in_text.csv`.

### 3. "Later coverage of the bill" after each release (M)
**Problem.** Bill evidence stops at +7 days. 366 tracker stories sit 0–30 days after a release on their bill and are linked to no release at all. 111 of them are on topic (cos ≥ 0.14). Example: The Hill s03332 "Newsom signs gun tax", 19 days after pr00134. Hand check: 12 of 12 were about the bill.
**Rule.** Assign each such story to the latest earlier release on that bill, up to the next release on it. Show them in their own section, not under "Related": *Later coverage of AB X (until the next release)*.
**Risk.** Medium if these were mixed into Related, because they are coverage of the bill rather than responses to this release. Keeping them in their own labelled section brings it down to low. List: `thread_followon.csv`.

### 4. Release threads and milestones on the page (S/M)
**Problem.** A release page never shows the other releases on the same subject. 63 bills have two or more releases (AB 418 has 24, AB 2316 has 19). 165 of 241 releases have a sibling, either through a shared bill or text cosine ≥ 0.4. Some threads cross bill numbers:
- pr00187 (AB 469) → pr00193 and pr00210 (AB 468), cosine 0.70;
- pr00091 has no bill but matches pr00066 (ACR 51) at 0.83, so it should inherit ACR 51.

Separately, 124 of the 174 releases with a bill fall within 3 days before or 1 day after a Bills-tab milestone for that bill: floor vote 46, chaptered 45, signed 44.
**Rule.** Add an "Other releases on this subject" list: shared bill, or cosine ≥ 0.45, or 50+ shared run words, in date order. Add a "Milestone" fact taken from `ins-bill_timeline`.
**Risk.** Low for shared bills. For pairs linked only by cosine, show the score.

### 5. Reverse links (M)
- **Story panel.** "From press release" covers only the 88 Tracker-release-ID stories, and it links off-site. The **942** related stories show no release at all. Add "Related to release: <title>", linking to `#press-releases/prNNNNN`.
- **Bills tab.** Release titles there are plain `<span>`s with only the official link (bills.js:275). Link them to the release pages; that covers 174 releases.
- **Reporters and Outlets tabs.** Neither mentions releases at all. 81 reporters have 3 or more related stories (Evan Symon 16, Iman Palm 13, Alan Riquelmy 13). 21 outlets ran copies and 333 carry related stories. Add "Releases covered" and "Releases run".

### 6. List rows (S, quick wins)
- Add a sortable **Related** column next to Pickups.
- Show the related count in the row sub-line.
- Add a "Has possibly related" facet option.
- Once #1 lands, count tracker copies in Pickups.

### 7. AV (S, low)
- 12 AV stories that are linked to nothing share a bill with a release within −1 to +7 days.
- 46 rows have transcript excerpts that could be run through the quote rule.
- Same-issue, same-day AV matching is too noisy to use: about 9 of 16 in my sample were relevant.

## Quick wins vs bigger changes
- **Quick wins:** #2a, #2b, #6, #7, and the milestone fact from #4. These are matcher inputs or front-end only.
- **Bigger changes:** #1 needs a sheet write and Sammy's sign-off under the RELRULE precedent. #3 needs a new section. #4's thread list and #5 touch the bills, reporters, outlets and tracker modules.

## Checked, low value
Issue inference (only 6 of the 25 blank Issues); third-party release rows (only 8 of 302 stories are in the tracker); undated stories (2); relaxing the boilerplate filter (+10 unlinked stories); caucus duplicates (already handled); bill numbers in release text (all tagged except HR 1); linking "Others named" (no person pages).
