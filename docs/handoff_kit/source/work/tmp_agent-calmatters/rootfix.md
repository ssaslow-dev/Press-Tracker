# Root fix proposal: originating service as the root (agent-calmatters, 2026-10-28)

For the queued button/cleanup work. Nothing here is applied yet.

## What happened on s00002
The grouping was already right: CALmatters 00009 (NewsBank) is the Original and there are 5 Reprints. 00009 had no web copy, though. `make_copies.py` takes the story's copy from the Original's cleaned HTML first, then from **any other row's HTML**, and only after that from the Original's NewsBank text. So the viewer showed reprint 09919's Piedmont Exedra page (header "Piedmont Exedra · 2026-10-23", byline "Yue Stella Yu | CalMatters") as the story. The same copy is also what `sheet_task.copy_html(sid)` compares new finds against.

## Same pattern across the sheet (work/out/origin_fixes.csv)
22 high (applied), 93 medium, 79 low (review queue items 18-origins / 18-origins-2).

## Which step let it through
1. **Regroup (±7-day window, headline prefilter).** 4 of the 16 applied merges were NewsBank rows that already had text at regroup time but missed the target, through the headline-overlap prefilter (`reprint_rule.candidates`: 01854 Korean headline, 05405 rewritten headline) or the window. In addition, 20 medium splits are dated more than 7 days from the service Original (e.g. Lake County Record Bee 02107, 36 days after CalMatters 02240). 21 same-service splits (mostly AP) are the known 90-day re-match.
2. **Originals order (`reprint_rule.tier/rank`).** `tier()` reads only the row's own Outlet and byline:
   - It ignores credit lines in the text ("This article was produced by Capital & Main", "originally appeared in Los Angeles Times").
   - It ignores credits on the story's other rows (2UrbanGirls/Daily News bylines "City News Service").
   - `WIRE` lacks MyNewsLA (CNS's own site), JNS, Capital & Main and States Newsroom.

   That is why 5 stories kept a republisher as Original: OC Register over MyNewsLA/CNS, CALO NEWS over Capital & Main, North Bay Business Journal / Marin IJ / "Looted Art" over the LA Times.
3. **Update button `originCredit`.** It searches for the credited original but uses the result only for wire/credit/aggregator/translation finds, and plain local finds' searches are discarded (buttonopt B7/F1). When it does move a find to the wire, nothing re-checks it against the real text rule (`sheet_task.reprint_check` tests only Original finds). It also never adds the originator as a new Original row: it rewrites the find's outlet/link in the browser.
4. **New-outlet / review / chrome-save writes.** 12 of the 16 applied merges are old "Tracker scrape" rows (ABC10, GV Wire, Times of Israel, J., Korea Times) whose saved copies were added on 2026-10-28 00:59–01:03 by the chrome-save rounds. That is after the regroup, and those writes never re-ran the reprint test on rows that newly gained text. The new-outlet write added 09919 correctly as a Reprint, but no step adds the originator's own page when the Original has only a NewsBank PDF/text.

The main hole is (4) together with (2). (1) is already queued. (3) explains why the button doesn't catch it going forward.

## Proposed code fix (for the queued button/cleanup work)
A. **Credit forces the originator (reprint_rule + sheet_task).** Add `reprint_rule.credit_of(row, text, story_rows)`. It returns the originating service named by:
   - a credit line in the text (`originally (published|appeared) (by|in|on)`, `republished from`, `(story|article) was (produced|published) by`, `is part of States Newsroom`);
   - a byline/author title "X, CalMatters" / "X | CalMatters" / "(CalMatters)";
   - the NewsBank APA author ("Stella Yu CalMatters, Y.");
   - a CalMatters section;
   - an "(AP) —" / "(CNN) —" dateline.

   `tier()` uses it from any row of the story: a row whose outlet is the credited service ranks tier 0, ahead of everything. Extend `WIRE` with MyNewsLA→City News Service, Jewish News Syndicate, Capital & Main, States Newsroom outlets and CNN Wire.

B. **Missing originator page is fetched and added.** If the credited service has no row in the story, sheet_task fetches its page (TinyFish: site search by headline, then the credit's link if present). The page is cleaned with clean_html (library mode; CalMatters' promo/"READ NEXT"/bio blocks need site rules: they survived cleaning here), and the text rule (25-word runs, ≥90% of both, 90-day window, no headline prefilter for credited pages) is run against the story's Original.
   - On a pass, it is added as a new Original row (full metadata, `ws<aid>o-s<sid>.html` + `_original_html`), and the old Original becomes a Reprint (Topic/Bills/Tone carried per DECISIONS 90; Reach by outlet consensus).
   - When the existing Original is the service's own NewsBank row, only its web copy is filled (Publisher link, File type 2/File name 2), as done for 00009.
   - A trimmed credited copy (≥90% contained one way only) goes to review, not auto (see queue item kind credit+trimmed).

C. **Re-test on new text.** Any write that gives a row text it didn't have (chrome saves, new-outlet fills, reprint fetch) runs `reprint_check` for that row against all Originals: 90-day window, and **no headline-overlap prefilter when a credit names a service**. Otherwise use a 25-gram index prefilter instead of headlines (the scan here ran over all 9,789 rows in 14 s).

D. **make_copies.py.** The story copy order becomes: Original's own HTML, then **Original's NewsBank/ProQuest text**, then other rows' HTML. A reprint's page should never stand in for the story while the Original has text. Its header should name the reprint's outlet when it is used.

E. **Update JS `originCredit`.** Drop the unused search for plain local finds (F1). When a credit/wire original is found, send it to the sheet task as `origin: {url, service}` on the find instead of rewriting outlet/link in the browser, so B adds it with the real rule. Also run `reprint_check` on the moved find (buttonopt js_map note).

Tests: the 22 applied cases + the 34 credit+trimmed must come out the same. The 4 CalMatters→AP State Wire pairs (AP author "X/CalMatters") must keep CalMatters as Original.
