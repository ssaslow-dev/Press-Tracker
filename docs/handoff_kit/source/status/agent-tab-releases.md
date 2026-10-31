# agent-tab-releases: Press releases tab (TABS-v1 module), 2026-10-27/28

No publish, no Exa, no workbook writes. Files written: build/tabs/releases.js (24 KB), build/tabs/releases_data.py
(block tab-releases, 91 KB), build/tabs/test/releases.test.js. Scratch: work/tmp_agent-tab-releases/ (mkpage.sh, srv/, blk/, shots/).
build/tabs/releases.md was NOT written: the coordinator limited this agent to the three files above (contract §1 asks for it; the integrator can lift this log).

## Log
- Read tabs_contract (incl. bill-link addendum), agent-tabs, tabs_tracker.js, stub.js, harness, release_pickup.js + _data.py v3,
  release_rule.py header, agent-relrule, DECISIONS (scope, text rule, EXCERPT-v1).
- Coordinator change 1 (full-text search): data/release_texts.json fetched lazily (first search or first release page).
- Coordinator change 2 (bill links): bill numbers via ctx.billLink(bill, {date}) when present, else <a class="linkbtn" data-bill data-date>.
- Coordinator change 3 (Sammy's comment "why isnt this a link to the article?"): every copy and every uses-text story links to the
  article (listed link with copy icon left; saved copy via ctx.openSaved when the framework has it), outlet -> #outlets/<slug>, date.
- The shared srv/index.html was rebuilt by agent-tabs at 23:52 with an older releases.js embedded, so tests run on a private
  page: work/tmp_agent-tab-releases/mkpage.sh (shared page with only the current releases module + blocks), SRV=that dir.

## What the tab shows
List: 241 releases (ins-release_pickup), search title + dek + full release text, facets date / source (Gabriel's office,
Jewish Caucus, Both sites, Not posted officially) / type / issue / bills / Gabriel quoted / picked up / number of pickups /
outlet that ran it (ctx.outlet). Columns Release (type, issue, bill links, text snippet) / Date / Source / Pickups. Answer line:
releases, picked up, copies, before/after shares. Export: titles + links copy, TSV, CSV (+ type, issue, bills, quoted, dek,
official link, outlets, before/after counts, key).
Page #press-releases/<date + first 8 title words slug>: header with dek and official link (copy icon left), facts (date, source,
type, quoted, issue, bill links, pickups, before → after, others named); "Copies of this release" (sheet rows, not tracker
stories); "Stories that use its text" (only when ins-release_pickup has col 'uses'); "Original coverage, before vs after" (7-day
windows, follow-up stories listed); then the framework chart + list over related tracker stories: same bill in the release's
two-year session, else the same issue 30 days either side, plus uses-text stories. Legacy: id (story or offNNN) -> page, year ->
date range, topic -> issue, pick -> picked up.

## Tests (MOD=releases, 1400 + 390, private page): 149/149 PASS
Independent: 241 / 85 / 109; each facet + combined + facet count; 12m preset; custom 2024; before/after shares 30% / 67% of 221
(v17 note said 31%/69%: data has moved since; the stat is recomputed, not copied); case+accent search incl. full text; body-only
term ("abandoning") + snippet <= 20 words with <mark>; CSV rows = count + 1; URL round-trip; page facts/before-after/follow-ups/
session list/chart per year; deep-link reload; back; no-pickup and not-posted pages; legacy links; every copy row has a working
article link + outlet page link + date (109 copies of 85 releases at 1400; 6 releases at 390); no #clips anywhere; no overflow;
missing text file -> fallback caption + title search; mocked {t:{}} file -> body match + snippet; no page errors.
Shots: work/tmp_agent-tab-releases/shots/releases_{list,page}_{light,dark}_{1400,390}.png
