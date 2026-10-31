# agent-decide-reach — 2026-10-27

Tabs: 1-reach (57 open items) and 9-relabel (72 open items). Queue https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB.
Wrote 116 create-only decision docs ({choice list, note "Auto: …", at, by "Claude (auto)"}) in 3 atomic batches (50+50+16). No existing doc touched; items docs not edited. Readback OK (relabel-130).
Files: lib/work/out/decided_1-reach.csv (46), lib/work/out/decided_9-relabel.csv (70). Script and payloads: lib/work/tmp_agent-decide-reach/ (decide.py, w/*.json, batch*.json, outlet_rows.txt).

## Counts
| Tab | Open | Decided now | Already Sammy's | Left |
|---|---|---|---|---|
| 1-reach | 57 | 46 | 3 (reach-015, -024, -025) | 8 |
| 9-relabel | 72 | 70 | 0 | 2 |

## Left for Sammy
- reach-041 Denver Gazette: Colorado daily (Out-of-state local by type), but the old tracker labels it National 5 to 2.
- reach-044 / reach-072 / reach-232 CE Noticias Financieras Portuguese/Spanish and LATAM: ContentEngine LLC is in Miami (LinkedIn), but the content is syndicated Latin American press. US base points to Spanish-language (and Ethnic for Portuguese); content origin points to International. Sammy's reach-013 (CE English) predates International.
- reach-056 Tribune Content Agency Special Sections: the old tracker maps TCA as Statewide California, but TCA is a Chicago national syndicate.
- reach-065 Food Navigator: William Reed (UK) brand, but the bylines are FoodNavigator-USA staff (Elizabeth Crawford, Deniz Ataman). The US edition would be Trade only; the UK brand would be Trade + International.
- reach-066 The Story Is with Elex Michaelson (CNN): a national CNN airing vs a California-focused LA show; the 2 rows are national topics.
- reach-092 Compton Bulletin: could not confirm it is ethnic (Black) press. The alternative is California regional & local only.
- relabel-088 GitHub: a mirror of an Epoch Times Chinese article, not an outlet. Sammy might want it re-attributed to Epoch Times (Ethnic + National) or dropped.
- relabel-141 VOA Vietnamese: a US government broadcaster aimed at audiences abroad. It is US-based, but "Ethnic" (diaspora press) fits poorly; National is also plausible.

## Decisions that differ from the proposal
- reach-009 MailOnline → National (proposed International). All 18 stories are DailyMail.com US-desk pieces ("For Dailymail.com", "U.S. Senior Health Reporter"), so the Guardian US rule applies. relabel-076 (dailymail.com) is National to match.
- relabel-008 Hebrew News → Jewish press + Ethnic (proposed + International). The site describes itself as "the leading news site for Israelis in America".
- relabel-019 Unecne → Ethnic + CA regional (proposed International). It is a Southern California Chinese site with LA datelines.
- relabel-030 El Mundo → Spanish-language (proposed International). The ProQuest stories are California pieces by US ethnic-media reporters, so this is not Spain's El Mundo.
- relabel-044 52hrtt → International (proposed Ethnic). The operator is Fujian Kebi IT in Fuzhou, China.
- relabel-059 TVNext → Ethnic + Trade (proposed International). It is a California Korean-American Christian advocacy group.
- relabel-133 Shaded Community → Ethnic (proposed International). Its address is 3435 Wilshire Blvd, LA.
- relabel-142 Vechyorka → Ethnic + CA regional (proposed International). It is a Russian-language Sacramento news site.
- relabel-054 Korea Daily Times → + CA regional (Silicon Valley). relabel-114 Metro Korean → + Out-of-state local (Philadelphia). Both match the Korean Journal and Bao Cali Today pattern.
- relabel-075 Contify and relabel-111 Looted Art → Trade + International, to match the other foreign aggregators and advocacy sites.
- relabel-104 KFN Spanish row → Statewide California + Spanish-language (the outlet's English row is Statewide).

## Paired items (kept consistent)
- reach-015 (Sammy: SFV Sun = District & Valley) ↔ relabel-130 SFV Sun Spanish row = District & Valley; Spanish-language.
- reach-114 SB Independent = California regional & local ↔ relabel-131 Spanish row = California regional & local; Spanish-language.
- reach-224 Associated Press (its one story is the Spanish AP piece jg-00045) = National; Spanish-language ↔ relabel-068 = National; Spanish-language (AP = National per Sammy's reach-025).
Rule used: on a row-level Spanish story in an English outlet, the primary tag is the outlet's Reach and Spanish-language is the 2nd tag.

## relabel-021 Guardian (story-by-story)
All 5 originals are Guardian US:
- jg-00261, jg-00700 and jg-03400 are theguardian.com/us-news.
- jg-01066 is in the NewsBank "US news" section, "Matthew Cantor in Los Angeles".
- jg-00285 is /environment/ by Cecilia Nowell: a US-reported piece with US sources. TinyFish fetch showed no UK framing.

Result: National.

## Web sources
- hebrewnews.com
- unecne.com
- oragark.com
- himalayanvoice.com/contact-us (Norwalk, CA)
- koreadailytimes.com
- metrokorean.com
- tvnext.org/about
- twig24.com
- shadedcommunity.com
- 52hrtt.com
- nowruzmedia.com
- ve4erka.com
- vsluh.net
- hongparkblog.com
- eurasiareview.com/about
- donorbox.org/aboluowang
- forumdaily.com
- kfn.one
- cafecoado.substack.com/about
- linkedin.com/company/contentengine-llc
- the Guardian article

No Exa used. WebFetch was blocked on theguardian.com, so TinyFish was used there.

Self-check: 46 + 3 + 8 = 57; 70 + 2 = 72. Every choice is validated against the item's options.
