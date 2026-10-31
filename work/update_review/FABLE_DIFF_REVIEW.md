# Diff review of the Update-button change (UPDFIX-v1 / NOSCHED-v1 / NOBLOGS-v1 / SINCE-v1)

Reviewer: Fable, 2026-10-30. Scope: `L/code/` and `L/build/tabs/` vs `L/handoff_kit/source/...` (98_stickycorner.js ignored; `build/tabs/` differs only by `__pycache__`). Read: the diffs of `tracker/00,10,40,41,42,43`, `sheet_task.py`, `sheet_task_prompt.md`, `build_data.py`, `outlet_rules.json`, `clean_rules.json`, `lookup_cache.json/.py`, the new tests, plus two measurements against the real master (`work/coverage_current.xlsx`, 7,736 Coverage rows).

Verdict in one line: no blocker; the fire_trigger / scheduled-task path is gone completely; five should-fixes, of which two can lose or hide real coverage (headline-segment dedupe on recurring titles; Sing Tao e-paper pages diverted to a list the page never shows).

Measured facts used below (script runs in this review, not in the suite):
- Master headlines whose first " - " / " | " / " — " segment is ≥ 25 chars and shared by ≥ 2 different Story IDs: 11 of 259 segments. Nine are recurring TV program titles (`KRON 4 News at 530pm (MyNetworkTV - San Francisco (KRON))` ×3 stories, `… at 12Noon` ×3, `KTVU FOX 2 News at Noon` ×2, …), two are wire-story families with a shared dek.
- Master rows whose Publisher link matches the new `print_page_urls`: 24, all `epaper.singtaousa.com/flippingbook/...` (Sing Tao Daily, 2022-2026). Rows on never-coverage hosts: tistory 3, blogspot 2, blog.naver 1, youtube 3, medium.com 5 (all `<name>.medium.com` subdomains, which the rule correctly leaves alone).

---

## Blockers

None.

---

## Should-fix

### S1. Headline-segment index merges or drops recurring-title finds (REQ-14 §2)
Files: `code/tracker/40_update_outlets.js:100` (`covHlSeg`), `:116` (covLoad indexes the segment), `:37` (`knownIndex` adds the segment to `hls`/`hlId`), `:133-140` (`covHit` tests the find's segment and, in the cross-outlet branch at `:140`, returns a story with **no date test** when the segment is ≥ 25 chars); consumer `41_update_search.js:719` (`known.hls` hit → reprint or `continue`) and `:866-873` (`covHit` hit → `_dup`, and when `ranIn` says the outlet already has that story, no reprint either: the find vanishes).

Failure scenario: a TV-captions find titled `KRON 4 News at 530pm (MyNetworkTV - San Francisco (KRON))` (41:383 builds exactly that shape) dated 2026-10-28 → `covHit`: list for segment `kron 4 news at 530pm mynetworktv` holds s03206/s03372/s03456 (2023); `same` fails (not within 3 days), the `h.length >= REPRINT_MIN` branch returns the 2023 story with `same:false`; at 41:866 `st` is set, `ranIn(st, 'KRON 4', …)` is true → `_dup`, no reprint, no skipped entry. The full-title rule already collided for these TV titles before the change (the full normalized title is also identical), so the change widens an existing hole rather than opening a new one; but the segment rule reaches any recurring column/show/newsletter name ≥ 25 chars whose outlet writes "Name - subtitle" or "Name | date" (e.g. `Capitol Weekly Podcast - Episode …`, `KCRW Press Play with Madeleine Brand - …`), and 41:719 now drops such a find from the same outlet before Claude ever sees it.

Minimal fix (two lines, page only; mirror in `knownIndex().hls` if desired):
1. In `covLoad`, after the loop, delete every segment key of `COV.hl` that maps to ≥ 2 distinct `sid`s (a recurring title is not a headline): e.g. keep a `Map seg→Set(sid)` while indexing and `COV.hl.delete(seg)` when `size > 1`; same for `knownIndex` (skip `sg` when `hlId` already holds it for another id).
2. In `covHit`, for a hit that came from a segment (`h !== h0`), require `covDays(c.date, o.date) <= 7` before returning the `same:false` reprint (the full-headline branch can keep its old behaviour).
Add to `test_updfix_js.js`: a find titled like the KRON row dated today is NOT `_dup` of s03206; the KIIS/Patriot case still passes.

### S2. E-paper finds are routed to a list the page never shows (REQ-11)
Files: `41_update_search.js:712`, `:769` (pushed to `U.printPages`, `continue`/`return`), `42_update_buttons.js:84` (`print_pages` in the run doc). No consumer in `drawUpd` (41:1064-1101) or `logRun` (43): `grep printPages code/tracker` finds only the three writers.

Failure scenario: the master already carries 24 Sing Tao Daily rows from exactly these flipbook URLs (its US editions are print-only; the Jul 2 2026 page names 蓋博 and AB 1127). After the change every Sing Tao find lands in `U.printPages`, the review panel lists it nowhere, the step summary counts it nowhere, and it reaches a human only if Sammy later runs the chat sheet step and reads `review.print_pages`. A real, recurring Chinese-language source becomes silently invisible at the point where he reviews finds. The REPORT's own verdict on row 6 was "fix by hand or review", not "hide".

Minimal fix: in `drawUpd`'s review/done branches render `U.printPages` as a short "Print pages to clip (N)" list (hl, outlet, date, link) with a "Copy list" button, and in `43` `logRun` show `x.print_pages.length` in the summary (add `print_pages` to `cleanRun`, ≤ 100 of {url, outlet, date, hl}). Also note in DECISIONS that Sing Tao Daily moves from story rows to the print-page path, since that is a change in what the tracker records for an outlet with 24 rows.

### S3. A manual Since date advances `searched_to` after a weaker search (SINCE-v1)
File: `42_update_buttons.js:78`: `searched_to: … && (!U.sinceManual || U.since <= U.sinceDefault0) ? TODAY : ''`. The manual plan is deliberately thinner: `after_date` on every `site:` search (41:701-702; the code's own comment at 41:698-699: "with site: it keeps few (2 of 10 LA Times 2026 results)"), no deep paging of outlet sweeps (41:737), only hosts active in the last 24 months (41:120), no new-outlet all-time sweep (41:746).

Failure scenario: Sammy enters 2026-09-01 (earlier than the default start) → the run ends with `searched_to = TODAY`; the next weekly run starts 7 days before TODAY. The window Sept 1 → Oct 23 was searched only with the date-filtered site queries and is never covered by the full sweep. Per-outlet recall for that window is lost for good, not deferred.

Minimal fix: `searched_to` only when `!U.sinceManual` (one token). This departs from the letter of SINCE-v1 ("advances only when the manual date is not later than the usual start"), so it is a coordinator decision; the alternative that keeps the decision is to run the manual date with the full plan (drop the `!U.sinceManual` guards at 41:701 and 41:737), at the cost of a longer run.

### S4. The blocked-find originator search never fires in a live run (REQ-14 page side)
File: `41_update_search.js:304`: `if (r._blocked && !r._text && …)`. `_text` is `String(c.text || '').slice(0, 6000)` (41:855) and `c.text` is the search **snippet** (41:707), present for essentially every blocked find. The branch is reached only when TinyFish returned an empty snippet. `test_updfix_js.js:83-85` passes because its fixture rows have no `_text`.

Failure scenario: Marin IJ / Santa Cruz Sentinel (blocked, snippet present) → no exact-headline search, no `_origin` candidate; the sheet-side `headline_story` (sheet_task.py:1784) still catches the case when the story is already in the master, so this is a missed feature, not a bad row.

Minimal fix: condition on the page, not the snippet: `if (r._blocked && !r._page && …)` (`_blocked` already means `!c.page`), and give the test fixture a `_text` snippet so it exercises the live shape.

### S5. Heartbeat docs reuse the first run's `at` for the whole page session (RUNPERSIST)
File: `43_update_log.js:88`: `at: (LOG.hbAt0 = LOG.hbAt0 || new Date().toISOString())` is never reset. A second Update in the same tab writes `status:'running'` docs stamped with the first run's start time; if that tab is closed mid-run the log card says "Running since <hours ago>" / "No progress since …; the tab was probably closed" for a run that just started, and `LOG.runs` sorts it under the older run. The final `saveRun` corrects `at` only when the run completes.

Minimal fix: reset `LOG.hbAt0 = ''` next to `RA.hbOff = false` in `runAll` (42:22), or key it by run id (`LOG.hbAt0 = LOG.hbAt0For === id ? LOG.hbAt0 : …`).

---

## Nits

- N1 `40_update_outlets.js:463` `BYLINE_BEFORE` is case-sensitive on `By` and needs every name token capitalised: "by Jane Doe", "BY JANE DOE" (fine: `JANE` is `[A-Z][\w…]`), "By Ana de la Cruz" lose the byline date and fall back to the TinyFish/Claude date (no story lost; one more `date check`). Fix: `\b[Bb][Yy]\s+` and `(?:\s+(?:and\s+|de\s+|la\s+|van\s+)?[A-Z][\w'.-]+){0,4}`.
- N2 `40:504` (`toRow`) and `sheet_task.py:1011` (`date_check`) blank any date `> TODAY` with no tolerance, while `stampOk` (40:464) allows +1 day. Israel/Korea/Taiwan outlets (Jewish Caucus and second-language coverage) date a morning story one calendar day ahead of Los Angeles until 9-11 am PT; a late-evening run blanks a correct date and sends it to `date_review`. Fix: compare against TODAY+1 in both places (the sheet step may keep its stricter rule since it runs later).
- N3 `outlet_rules.json` `houses` block: consumed by nothing (`grep houses code/` → only the apply_all_patches comment); the house test passes through the `types` table. Its `hosts` list contains `knx.iheart.com` while `houses_note` says KNX is Audacy, not iHeart. Either delete the block or wire it (REQ-14 §3 "editions of one row" is not implemented: same-house copies still land as Reprint rows, which is acceptable but should be said in DECISIONS).
- N4 `41:685`: `U.sinceUser` (set when the panel's date field is edited, 41:1108) is never cleared, so once Sammy touches that field every later Update in the tab runs in manual mode with that date. Clear `U.sinceUser` at the end of `runUpdate`, or treat only the dialog's value as manual.
- N5 `clean_rules.json print_page_urls`: `/digital-?edition(/|$|?)` also matches magazine article paths under a `digital-edition` section (not a flipbook). Low risk; a path-depth guard (`/digital-?edition/?$`) would narrow it.
- N6 `sheet_task.py verify_tabs` (4310-4325): the Bills tab is keyed on its first four columns with duplicates numbered in order; a future tab that gets rows inserted mid-table with duplicate keys will report false cell changes. Not reachable today (`apply_bills` writes JSON, not the tab).
- N7 `41:779-782` pass-2 step label uses `toFetch.length` and `i+10` for batches of 5: cosmetic.
- N8 `drawUpd` (41:1066) calls `searchPlan(since)` without the manual flag, so the "runs about N searches" count for a manual date is the default plan's N.

---

## Checked and found sound

- No `fire_trigger`, `SHEET_TASK`, `CCR` or scheduled-task path remains in `code/` or `build/tabs/`; `saveSheet`, `runAll` and the hand-add path only write run docs and toast `SHEET_MSG`; `sheet_task_prompt.md` rule 9 forbids triggers and CCR and every `sheet:` shape carries `written:`.
- Never-coverage rules: host suffix match with path prefix (`medium.com/@` only); `<name>.medium.com`, Substack, custom domains and the 5 existing Medium rows are untouched; an `outlets.json` host rescues (`NEVER_KEEP` / `never_coverage_reason`). YouTube and mrcolionnoir.com come from `lookup_cache.json never_coverage_hosts` as NOBLOGS-v1 says. Real outlets that merely host blogs or video are not rejected by any rule (only the platform hosts are).
- Mirror canonicalisation (`canonMirror` / `canon_mirror` / build_data): strips one leading label from the fixed list, only when a dot remains, and unwraps `*.cdn.ampproject.org/[cv]/s/`; `m.com/a` survives (tested). Three copies are byte-equivalent in logic.
- Late window (REQ-1): one-line change; with a manual date `after_date` is clamped to the manual date (41:702), as SINCE-v1 says.
- `sinceKeep` / `sinceFloor`: identical to the old filter without a manual date; with one, `max(minDate, since)`; undated results pass to the page-date stage. `late`/`siteHosts`/new-outlet guards all read `U.sinceManual`, which `searchPlan` saves and restores around `tfPlan`.
- Fetch retry (REQ-6): per-candidate `_fetchfail`, cleared on any successful batch (also when the page is a blocked error), pass 2 in fives, `U.failed` counted per page after pass 2, honest skip reason; `STOP_CODES` still propagate.
- RUNPERSIST: provisional doc before any TinyFish call; `hbTick` is gated (20 s, `RA.busy`, `RA.noStore`, `RA.hbOff`) and serialised on one promise; `hbFlush` before both the provisional doc in `saveFound` and the final doc; `!saved` blocks the "Nothing new" path too; error path marks the running step, saves `status:'error'`, `finally` still clears `RA.busy`. `keepPending` strips `_text`, caps 5.
- `sheet_applied` / `run_done`: `written:true` closes, `written:false` never, legacy `{at, line}` closes unless the line starts "Not written"; all five callers updated.
- `has_work` orphans: refs from undone runs' rows (`Article ID`, `Story ID`, `Tracker story code` jg-codes, `_page`, `_ph_sid`, `_origin.cands[*].page`) and unwritten reprint docs (`rp-<id>`, `<id>`, `rp:<id>`, `_pageKey`); step 5 deletes processed pages docs, so a leftover is an orphan by construction.
- `verify_tabs`: header identity, key-row presence (A/V rows moved to Removed excepted), fill-blanks-only with the Press-releases derived set exempt, new rows only on the three tabs the run writes, hyperlink count from the sheet XML, order check with new owned tabs removed; REQ-8's rehearsal passed it on the real master.
- Future-date rule in `pageStamp`: `stampOk` filters candidates before the label/tz/byname rules, +1 day tolerance, ≥ 1990; `updated` detection runs on the filtered list.
- Backfill label: `isBackfill` keys on `_found_by` prefix `outlets:` and `date < since − 180 d`; Data Source, Team note, `_backfill`, `found_by.backfill`, sheet `review.backfill_finds` all wired and tested.
- `headline_story` (sheet side): only when the find has no text and no copy test matched; Jaccard ≥ 0.8 on content words (crude plural stem) within 7 days; a headline match never swaps the Original.
