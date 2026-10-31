# agent-decide-pr — 2026-10-27

Scope: queue tabs 13-pressrelease, 3-nogabriel, 2-role, 5-headline, 7-copy (not 12-process). Queue: https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB
Wrote 85 decision docs (2 atomic batches, create-only, by "Claude (auto)", at 2026-10-27T09:55:00Z). Nothing overwritten, items untouched.
CSVs: work/out/decided_{pressrelease,nogabriel,role,headline,copy}.csv. Helpers: work/tmp_agent-decide-pr/ (txt.py text lookup, cmp.py release-overlap, make.py docs).

| Tab | Open items | Decided | Left |
|---|---|---|---|
| 13-pressrelease | 71 | 66 (52 release, 14 keep) | 5 |
| 3-nogabriel | 25 | 14 (11 keep, 3 take out) | 11 |
| 2-role | 2 | 2 | 0 |
| 5-headline | 2 | 2 | 0 |
| 7-copy | 1 | 1 | 0 |

## Press-release rule used
Release = posted with no reporting: wires, the org's own page (CAA, Common Sense, JWW, JPAC, ICLC, CR), unbylined "Contributor" or announcement posts, or ≥~85% of sentences taken from a release, adding only boilerplate, attribution or captions. Bylined rewrites with ~20%+ of their own wording or framing stayed "keep" (KRCR, McMillen, Westside Today, Food Safety News News Desk/Flynn). Commentary on Contify and the UC Berkeley profile: keep.
Proposals overturned: pr-000 (Noozhawk byline is the Goleta PIO), pr-006, pr-008 (stitched Senate + governor releases), pr-009, pr-010, pr-011, pr-012 (CR's own release page), pr-035, pr-036, pr-039, pr-049, pr-054 → release; pr-044 → keep.

## Left for Sammy
- pr-028..032 (Jim Wood caucus, SCNG page 5, 2022-06-09): these are NewsBank print-page rows with no text. Their headline was borrowed from the California Courier item on the same page number (nb-03076). Five SCNG papers sharing page 5 most likely carried a different (SCNG) story, so the headline and Story ID grouping may be wrong. Check the clips.
- nogab-000 (Strickland op-ed), 001 (Mammoth men's service), 007 (Daily Post gas blowers), 014 (SDUT foreclosure), 016/017/018 (2018 PG&E reprieve; the Fox Business and KTVU copies show no Gabriel even in captions): none of these texts mentions him. The web copies I could check are inconclusive. NewsBank text drops captions; see the finding below.
- nogab-015 (St. Paul Pioneer Press 2018 "Young political voice", 36 words), 019 (2013 SF Book Festival), 020 (2004 Sac Bee El Dorado Hills kids): no tie to him, and could be a different Jesse Gabriel in a caption.
- nogab-025 (Sac Bee red-dye Halloween): the site is blocked. The earlier fetch names AB 418 but not him.

## Finding
NewsBank text extraction omits photo captions and AirTalk guest lists. Every no-mention NB row I could check on the web (nogab-008, 009, 010, 013) had Gabriel in a caption or guest list. The NB "no Gabriel" flag is unreliable, so don't auto-delete on it.
Also: role-018 / ws-03709 saved copy + headline "Sacramento Archives" is a J. Weekly listing page, not the op-ed ("Driven by values, Jewish legislators get it done in Sacramento"). pr-012 saved copy is FSN not CR. copy-005: Madisony row is Original while CBS is its Reprint (looks inverted).
