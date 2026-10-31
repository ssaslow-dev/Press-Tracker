# agent-uv-triage: "Reprint (unverified)" triage (Sammy 2026-10-28 A/B/C; DECISIONS line 230)
Source: work/coverage_current.xlsx = master 4d7fb37c…, 585 unverified rows. No sheet, library or queue writes. Output for df-write: work/tmp_uv/.

## Outputs
- work/tmp_uv/changes.csv: 1,131 lines (Article ID, action, column, old, new, evidence). Actions: verify 30 (15 rows × Original or reprint + Search lookup), fill 42, set 11 (Saved Copy? = Yes), replace_placeholder 1 (00061 BLOCKED → library name), recount 14 (# of reprints, mirror to Originals), remove 117 (Removed tab; category + reason in `new`), tag 449 (Search lookup), hide 453 (tracker display, for rp-final), review 4, library_move 1, proposed_correction 4 (NOT to apply), unresolved 5 (Medium blank: brand-new outlets).
- work/tmp_uv/pages/<year>/ws<aid>r-<sid>.html + pages/_original_html/<year>/… : 11 new library copies (MANIFEST.csv with sha256). The other 4 passes already have library copies (00094, 02755, 06919, 07064); not replaced.
- work/tmp_uv/review_items.json: {list:[…]} 5 items, cat "uvreprint", ids uvreprint-001…005 (shape as status/agent-rp-queue.md).
- Working files: a_results.json (tier A fetch + rule), b_results.json (NewsBank check per row), outcomes.json (one outcome per Article ID, 585), fetched_clean/ fetched_raw/ (all fetched pages), orig_for_test/ (Daily News Originals 00090, 02754 fetched only to test 00094/02755; not proposed as copies).

## Tier A (26 = 26 with a link/headline; all 14 "Found online" are among them)
TinyFish fetch_content (free), no workarounds. Page built as reprintfetch did (header div + fragment), cleaned with clean_html.clean_page(mode='find') + page_check, then reprint_rule.text_verdict vs the Original's own text (html_clean copy or texts/nb). Per-page pre-trim (raw copy keeps it): Yahoo "Return to Homepage" + AI key-points list; Al Jazeera "Recommended Stories" box.
- Pass 15 → Reprint: 00061 00094 00095 00221 00242 00243(low, edge) 00282 01297 01313 01736 02755(low, clutter) 03007(low, edge) 03775 06919 07064. 00094 and 02755: the Original (Daily News) had no copy and the viewer copy was the row's own page (circular), so the Daily News Original pages were fetched and used.
- Fail 4 → review: 04660 Al Jazeera (edited AP, 79/86%), 07066 Yahoo (99/84%, Original has a later White House statement), 07444 Yahoo = CBS8 copy (99/77%, Original copy carries dek + sponsored ad), 08340 Epoch Times (Original CityMatters is a 110-word excerpt of it). 08349 CALmatters also failed (Original = Observer 57-word teaser) but is a NewsBank duplicate of 02138, handled under B.
- Unreachable 6 → tier C: 07771 08073 08826 (Daily Breeze login_required), 08827 (Pasadena Star-News login_required), 07995 (E&E paywall preview), 04556 (alcoholjustice headline-only page).
- Dates: every pass row already had a full date. Three filled dates look off by the UTC→PT shift (00095 09-30→09-29, 06919 10-09→10-08, 00282 08-05→08-04, last medium) and 00061's byline lists 3 authors: listed as proposed_correction, not applied.
- AV: 00095 (KESQ) and 03775 (PBS NewsHour) are TV; both already have Audio & video rows (Web story). No new AV rows.
- Fills: same-outlet consensus only (all rows agree), otherwise blank. Most tier-A outlets are brand-new (no other rows): Publisher/place/Reach left blank; Medium blank for 5 (00242 00243 01297 01313 01736) — listed `unresolved`.

## Tier B (NewsBank absence)
Pool: sheet Newsbank rows (any status, texts work/texts/nb) + Companion All PDF Items (staged copy = Mac file, 1,703,302 bytes, mtime 2026-10-27): unmatched text items and print pages (Print Editions "Matched headline"). Outlet = sheet_task.norm_outlet; Companion names folded (": Web Edition Articles", "(ST)") and mapped to sheet keys via nb_index.csv. Window −3..+7 d of the Original's date; match = headline sim ≥ 0.8, or overlap + sim ≥ 0.5, or text rule pass.
- Indexed for the period = the outlet has NewsBank items and the Original's date lies inside its NewsBank date span (±30 d) with ≥1 item within a year. 17 rows at indexed outlets fail this (e.g. Modesto Bee 2019, Daily Breeze 2017, Philadelphia Tribune 2019) → C, not removed.
- Absent 111 → Removed, "unconfirmed reprint claim" / "Not in NewsBank results for an indexed outlet". By outlet: SLO Tribune 23, Modesto Bee 21, Merced Sun-Star 21, Fresno Bee 15, Press Democrat 9, SD Union-Tribune 4, San Mateo Daily Journal 2, Santa Monica Daily Press 2, Mercury News 2, Daily Breeze 2, others 1 each. (Daily Breeze 07771, 08073 were also absent but are tier-A unreachable with a found URL: kept as C, flagged in their tag.)
- Present 6 → removed as duplicates ("2 duplicate"): 00114–00117 (Fresno/Modesto/SLO/Merced; the same story s00037 already has their NewsBank Today's Edition rows 05447/05449/05451/05448 as verified Reprints, text rule high); 08345 Santa Ynez and 08349 CALmatters (= s00611 rows 02141, 02138). No "present but unlinked" case needed a new link: every NewsBank match is already a row of a story.
- Not removable 86: an unidentified NewsBank print page (no matched headline) exists at the outlet in the window (codes in the tag) → C.

## Tier C 449 = 339 outlet not indexed + 86 print page in window + 17 outside NewsBank's span + 6 tier-A unreachable + 1 Original undated (06942, Associated Press)
Search lookup tag: "<old>; old tracker reprint list, no further search (Oct 28)" (+ reason suffix). Uncounted; hide action for rp-final. The 4 tier-A fails are also hidden until their review items are decided.

## # of reprints / Originals mirror
- Removals change no count (unverified rows were never counted; the 6 duplicates' verified twins stay).
- 14 Originals gain: 00053 6→7, 00091 9→10, 00217 3→4, 00237 5→7, 00268 13→14, 01290 8→9, 01299 14→15, 01714 7→8, 02999 5→6, 03742 32→33, 06918 1→2, 07063 0→1, 00090 0→1, 02754 0→1 (+15). Recomputed from Reprint rows by norm_outlet, Original's outlet excluded.
- Originals tab: no Original rows are removed or added; only these 14 "# of reprints" cells change in the mirror. Rebuild per rule 7 as usual.
- Removed tab: 117 rows; no AV-tab rows among them; one library file (ws08349r-s02995.html, + _original_html if present) → _to_delete.
- Red font: the 15 verified rows become tracker rows (drop red); everything else unverified stays red/hidden.

## Questions for Sammy (in review queue or here)
1. uvreprint-005: s02995 (Observer teaser) duplicates s00611 (CalMatters); proposed merge.
2. 07066 / 07444 fail only through Original-copy clutter and an update: proposed "Count as Reprint".
3. 08340: Epoch Times looks like the originator of s02992 (CityMatters excerpt).
4. Daily Breeze 07771 / 08073: URL exists (login wall) but not in NewsBank: kept as C rather than removed.

## Suggested cleaner rules (clean_playbook, for agent-code)
- yahoo.com: drop "Return to Homepage" and the AI key-points <ul> before the first article <p>.
- aljazeera.com: drop the "Recommended Stories / list of N items" box.
- abc10.com/Tegna: "Sponsored By" ad blocks inside the article body (seen in ws07443o-s02227).
- worldisraelnews.com and pbs.org pages come through as one text block (share widgets inline); kept as is (keep when in doubt).

## Self-check
- 585 rows, one outcome each (outcomes.json). 15+4+6 (A) + 117 removed + 443 other C = 585.
- All 11 new copies name Gabriel (1–7 mentions); MANIFEST sha256 listed. Random absent rows checked: no NewsBank item at the outlet in the window, or only an unrelated headline (e.g. 04264 Modesto Bee, sim 0.41, text 20%).
- No sheet, library, queue or Mac writes made.
