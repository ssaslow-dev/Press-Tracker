# Organisation-site posts: audit of the 13 rows left for Sammy (PRJUDGE-v2)

Fable, 2026-11-04. Read-only audit; nothing in the workbook was changed. The approved changes are in `work/localapp/datafix/org_posts/approved_org_posts.csv`.

## Question

PRJUDGE-v2 says another organisation's press release counts as a press release (hidden, Press release = Yes) only on a wire or on the organisation's own official site. These 13 rows are posts on an organisation's own site that the review (`PRESS_RELEASE_YES_REVIEW.csv`) said are not releases. They were left for Sammy with a possible NOBLOGS-v1 question (are they advocacy blogs, i.e. not coverage at all?). Sammy asked for an independent verdict and said to apply it.

## Verdict in one line

All 13 become **Press release = No** (coverage, shown in the tracker). None is a release; none is a YouTube or advocacy blog under NOBLOGS-v1 as the tracker applies it.

## How I checked

- Read the saved copy of every row (`data/library/<year>/ws<id>o-<story>.html`). No web fetch was needed.
- Looked for release signals: "FOR IMMEDIATE RELEASE", a CONTACT line, a dateline opening ("SACRAMENTO, CA --"), a release category tag, "issued the following statement". None of the 13 has any.
- Checked the reference data: `code/outlets.json` and `code/lookup_cache.json` already carry all three outlets as confirmed publishers of their own content (CAA: type institution, medium Trade press; Common Sense Media: medium Newsletter or blog; Jewish World Watch: medium Online news). The NOBLOGS-v1 never-coverage list (`outlet_rules.json`, `lookup_cache.json`) holds YouTube, platform blogs (blogspot, wordpress.com, medium.com/@...) and one personal advocacy blog. An organisation's newsroom on its own domain is not on it.

## The rows

| Article ID | Story | Date | Outlet | Headline (short) | Decision | Reason |
|---|---|---|---|---|---|---|
| 09618 | s04096 | 2019-03-20 | California Apartment Association | Bill would authorize tenants to shelter families facing homelessness | No | CAA newsroom post on AB 1188 by Gabriel; news style, no release markers. |
| 09527 | s04027 | 2020-02-18 | California Apartment Association | Bill would create tax credit aimed at keeping housing affordable | No | Same: news post on AB 2058 by Gabriel. |
| 09407 | s03913 | 2021-04-13 | California Apartment Association | CAA objects to eviction-defense fund in new legislation | No | CAA's own reporting of its opposition to AB 1487; not a release. |
| 09400 | s03907 | 2021-04-28 | California Apartment Association | CAA-sponsored housing bills move unanimously out of committees | No | Committee-vote report on AB 989 by Gabriel, quotes CAA's Tony Bui; news post. |
| 09387 | s03894 | 2021-06-02 | California Apartment Association | CAA-cosponsored housing bill wins approval in Assembly | No | Floor-vote report on AB 989; news post. |
| 09370 | s03878 | 2021-07-09 | California Apartment Association | CAA-cosponsored housing appeal bill advances in Senate | No | Senate committee report on AB 989; news post. |
| 09367 | s03876 | 2021-07-15 | California Apartment Association | Eviction-defense bill on Senate floor, vote expected after summer recess | No | Member-news post on AB 1487, quotes CAA/CAR letter to Gabriel; not a release. |
| 09353 | s03862 | 2021-08-18 | California Apartment Association | CAA members urge lawmakers to reject eviction-delay legislation | No | Bylined (Mike Nemeth) report on CAA's campaign against AB 1487; news post. |
| 09316 | s03828 | 2021-10-09 | California Apartment Association | Gov. Newsom vetoes eviction-delay legislation | No | Bylined report of the AB 1487 veto; news post. |
| 08624 | s03236 | 2023-10-26 | California Apartment Association | Package of CAA-supported housing bills signed by Gov. Newsom | No | Bylined bill-by-bill roundup naming Gabriel's bill; news post. |
| 09115 | s03643 | 2022-10-06 | Common Sense Media | California Continues Its Leadership with Online Protections for Kids and Families | No | Kids Action article on AB 587 by Gabriel; first-person advocacy write-up, not a release (the site keeps a separate press-releases section). |
| 08621 | s03233 | 2023-10-30 | Common Sense Media | Five Major Legislative Wins for Kids in California | No | Kids Action legislative recap naming AB 787 by Gabriel; same kind of post. |
| 09096 | s03624 | 2022-12-02 | Jewish World Watch | JWW's Serena Oberstein named Activist of the Year by Asm. Jesse Gabriel | No | Bylined (Jeff Hensiek) write-up of Gabriel's award ceremony, quotes him; news post on the organisation's site. |

## Why coverage and not "advocacy blog"

- These are organisations with their own domains and newsrooms, writing news-style items (bylines, votes, dates, quotes) about Gabriel's bills. That is stakeholder coverage: how the apartment industry, a children's media group and a Jewish human-rights group reported his work. The CAA items are the only record of the apartment industry's reporting on AB 1487 and AB 989 and carry real Tone (Negative on AB 1487, Positive on AB 989), already rated.
- NOBLOGS-v1 was written for YouTube and personal or platform blogs (the never-coverage list), judged by outlet. The tracker's own outlet records already give these three a place ("Trade, advocacy & blogs" and "Jewish press" reach buckets), so the tracker's taxonomy treats them as outlets.
- PRJUDGE-v2 decides release vs not by the item's own text. None of the 13 reads as a release, so under the rule they are No even on the issuer's own site. The rows that stay Yes at the same kind of organisation (ANCA-WR, Steinberg Institute, Consumer Reports, Liberty Counsel, Jewish California) do read as releases; that difference is the rule working as written.
- The two Common Sense Media posts are the closest to "advocacy blog" (first person, "we sponsored"). I still class them as coverage: it is a national organisation's own site, not a platform or personal blog, and the posts report on signed laws by bill and author. If Sammy ever decides organisation advocacy blogs are out, these two are the ones to revisit.

## What the change does

- 13 rows: Press release Yes -> No on Coverage (and the Originals mirror, same value). Font back to black (PRCOLOR-v1: only Yes rows are purple). All 13 are Originals with Role and Tone already filled, so nothing else needs filling. 13 more stories become visible (none has reprints).
- Nothing else changes: no rows removed, no library files touched.

## Note for whoever runs the switch-over screen

`switchover.py` `plan_datafix` skips the column "Press release" ("a column the fixes never touch"), so the CSV will be left out if it is dropped into the datafix step as the code stands. The clean route is to move these 13 from `org_posts_listed` to `unmark` in `app/src/station/data/prjudge_v2.json`, so the PRJUDGE-v2 step applies them with the ~119 others (same re-check on the real sheet, font back to black, one ledger entry). The CSV is the record of the approved values either way.

## Side observation (no change made)

Row 09095 (Jewish World Watch, headline "December 2, 2022", link `jww.org/site/2022/12/02/`) is the site's date-archive page for the same day as 09096 and looks like a stray row rather than a story. Worth a look in a data check; not part of this audit.
