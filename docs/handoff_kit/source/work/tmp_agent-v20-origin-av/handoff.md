# Handoffs from agent-v20-origin-av (2026-10-28)

The code side is done in code/avtab.py (AVTAB-v3 + AVSHOW-v1) and code/reprint_rule.py (ORIGINCREDIT-v1). Both are synced to build/pub/pipeline by apply_all. The items below sit in files I don't own.

## 1. v20-tabsui: code/tracker/53_tabs.js (`tbAvBox`) and 04_facets.js
Spec: work/tmp_agent-avshow/codespec.md sections 3 and 4.
- The `av` block cols now contain `channel` after `type` (avtab.KEYS). It is filled on 890 of the 1,030 tab rows. The 134 backfilled rows also have it.
- Panel: replace the single `row('Show', j(a.show, a.station, a.network))` with two rows:
  - `Channel` = `a.channel || a.station`, plus the network when it isn't already part of the channel.
  - `Show` = `a.show`, omitted when blank.
- Show Channel on every non-Web-story panel type. Keep the Web story early return. CNN check: 00198, 00742 and 05177 must show Show = program and Channel = CNN.
- **Remove Notes from the panel entirely** (Sammy, via coordinator). `a.notes` (Exa URLs, finder and provenance notes) is back-end text. Don't render `a.notes`, and don't render `a.from` ("Details from") either. Both stay in the sheet and the data.
- Clips facets: add `channel` (`av.channel`, falling back to `av.station`) and `show` (`av.show`). Label blanks "Not recorded" and sort them last. Add both to the FACETS keys so `ctx.facetLink('channel'|'show', v)` works. Search text should include channel + show. CSV export gets separate Channel and Show columns.

## 2. agent-buttonopt: code/sheet_task.py (+ sheet_task_prompt.md)
- **AVTAB-v3 (AVDATE item 3):**
  - Widen the F7 date_check to ±3 days for TV/Video/Radio/Podcast.
  - Never take a row's Date from a station video page or from the save/fetch day. `avtab.extract` now leaves Air/publish date blank and adds a note when the Coverage Date is within 3 days of the save day. It reads the save day from `src='Update button YYYY-MM-DD'`, which `apply_av` already passes, or from the new `today=` argument.
  - When `out['Air/publish date']` is blank on a station video row (`avtab.station_video(row, type)`), the row's Coverage Date must also not be the save day. Leave it for review and add it to a result list.
  - Make sure every path that adds Podcast/Radio/TV/Video rows calls `apply_av`. The v20 backfill found 134 AV-medium rows with no tab row: rows added by the new-outlet/reprint-fetch writes, and Medium fills by blankfill.
- **AVSHOW-v1 (codespec section 5):**
  - `apply_av` needs no code change to fill Channel and Show: `avtab.extract` now returns `Channel` and the evidence-only `Show/program`.
  - Add `channel` and `show` to the `av_rows[]` entries, and add `av_no_channel[] {aid, why}` for blank Channel rows.
  - Prompt verify step: fail when a new Broadcast segment, Video clip or Episode row has a blank Channel while the outlet or URL names a station or network.
- **ORIGINCREDIT-v1 (rootfix.md A, C, E):**
  - In `reprint_check`, compute `cred, ev = RR.origin_credits(story_rows + [find], texts)` and use `RR.rank(x, credited=cred)` / `RR.tier(x, credited=cred)`. A credited originating service ranks first (tier 0).
  - Pass `credited=True` to `RR.candidates(...)` when `RR.credit_of(find, text)` is non-empty, or when the row just gained text. This drops the headline prefilter (90-day window, text rule only).
  - Any write that gives a row text it didn't have should re-run reprint_check for that row against all Originals.
  - `originCredit` (Update JS 40–43, also yours) should send `origin: {url, service}` instead of rewriting the find's outlet/link. Rootfix B (fetch and add a missing originator page as a new Original) is button work.

## 3. v20-photos: code/clean_rules.json, make_copies.py
- **CalMatters cleaner rules** (rootfix B). The full-page clean of calmatters.org leaves:
  - the promo / newsletter boxes;
  - the "READ NEXT" block;
  - the author bio at the end.
  agent-calmatters removed them by hand for 2026/ws00009o-s00002.html: compare `_original_html/2026/ws00009o-s00002.html` with the cleaned copy. Add a calmatters.org rule: kill "READ NEXT" and what follows it, the "We want to hear from you"/membership promo, and the trailing author bio block.
- make_copies order (rootfix D) is already in your make_copies item.
- **Renamed library files:** 29 rows' File name changed in the master (o/r and -s<sid> now follow the sheet). The list is in work/tmp_agent-v20-origin-av/renames.txt, and the Mac undo log is `Tracker library/_archive/_renames_origin_2026-10-28.tsv`. In work/html_clean I added copies under the new names (11, see html_clean_adds.tsv). The old names are kept. make_copies must find the rest by Old Article ID, as it does today.
