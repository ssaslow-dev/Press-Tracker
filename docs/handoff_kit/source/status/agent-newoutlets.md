# agent-newoutlets — site-search outlets not covered by the Oct 21, 2026 TinyFish all-time run

## Step 1 (done)
- Oct 21 plan/results (tinyfish/hybrid-alltime/) are NOT in the scratchpad (only referenced in tracker JS comments).
- Proxy used instead: the old tracker data (work/index_original.html, newest story 2026-10-21 = state right after the Oct 21 run).
  Its outlet hosts (outletGroups logic: link/plink host, not proquest/oclc/google, minus SKIP_HOSTS/youtube/google/msn/yahoo/aol/archive)
  = 635 hosts + yahoo/aol/msn = "site-searched Oct 21" (work/tmp_agent-newoutlets/oct21_hosts.json).
- Current sheet (coverage_current.xlsx, Coverage): 1,440 outlets; 798 have no own-site host (build_data own_link logic) in that set;
  32 matched by name to a searched host -> 766 candidates. Own domains assigned (Publisher link host, else known site: domains.py).
  57 map to a domain already searched Oct 21; 52 no web presence (wires/NewsBank feeds/unknown); 1 skip host (pbs.org);
  656 outlets -> 599 unique domains to search. Files: outlet_status.json, search_domains.json.
## Step 2 — searches (done)
- 1,251 TinyFish searches on 599 domains (plus pbs.org, added after it was wrongly skipped in step 2; ctvnews.ca searched last).
  647 "Jesse Gabriel" site:, 601 "Gabriel" "D-Encino" site: (both queries on every domain, so nothing was skipped), 3 native-script
  (Armenian on panarmenian/armenpress, Chinese on ecns.cn: 0 results); 50 of the searches were extra result pages.
  asreport.americanbanker.com is covered by the americanbanker.com search. Paced at 10 calls, then 18 s, after one 30/min rate-limit hit.
- 1,824 results, 1,668 unique URLs (hits_sofar.json, searches_sofar.json).

## Step 3 — free filters (no fetch), screen.py -> screen_log.json
1,659 unique normalized URLs (amp/query/#/www/m stripped). Removed before fetching: 929
- 10 off-domain (site: ignored), 30 already in sheet by link (any link column), 371 skip URLs (election-results pages, obits/obits.*,
  data.* / health.usnews.com directories, californiafiles, public-records), 94 listing/tag/author/section/PDF/calcities docs/csun clips lists,
  68 wrong person by keyword, 65 SCNG/sidebar teasers, 291 outlet+headline already in sheet within +-3 days (web copies of rows the sheet
  already has: listed in out/newoutlet_linkfills.csv as link fills). TF_BLOCKED_HOSTS: none of the new domains were on it.
- Wrong-person keywords (title+snippet, unless the snippet has Assembl/lawmaker/legislat/Democrat/Encino/D-): drummer, Seratones,
  volleyball, Righetti, wrestl*, obituar*/obit, passed away, survived by, grandchild, great-grand, funeral, memorial service, Wheat Kings,
  hockey, WHL, CHL, The Narrative, Suzie Zeldin, tattoo, DDS, practitioner, M.D., nurse, graduates, class of N, dean's list, honor roll,
  Autrand, Gabriel Ortiz/Lee/Stripling, soccer, football, baseball, softball, basketball, touchdown, scored, goal and, assists, arrested,
  sheriff's log, police log, booked, "Jesse, Gabriel", "(Jesse) Gabriel", "Jesse (Gabriel)", Jesse Gabriel Lee/Ortiz/Autrand/Stripling/Sabatis.
- SCNG/sidebar teaser snippets: "signs two immigration bills co-authored by Encino", "Jesse Gabriel is seen in a 2025 photo",
  "Jesse Gabriel speaks as Los Angeles Mayor Karen Bass", "More in News", Chico N&R "From left, Assemblymember Jesse Gabriel and state Sen.
  John Laird" (unless the title is that story itself).

## Step 4 — one fetch per page (730 pages), process.py / group.py / finalize.py
- TinyFish fetch_content, html, TF_SCOPE selectors (article/main + TF_SCOPE excludes), 10 URLs per call. 44 pages that returned
  selector_not_matched with an ordinary page structure were fetched once more without include_selectors (not blocks).
- Cleaned with code/clean_html.py (mode find) + page_check; saved to work/tmp_agent-newoutlets/pages/NNN.html (no Mac library writes).
- Results: 357 finds; 236 BLOCKED (403 / bot wall / login / Hearst #loading-error; mostly Nexstar TV sites and Hearst papers — not
  worked around); 73 no article (no Gabriel on the page: csun.edu clip stubs, paywall teasers, empty JS pages); 18 not Jesse Gabriel or
  only outside article prose (tags, wrong person); 10 RETRY (404/unreachable/timeout); 36 IN-SHEET (story already has a row for that
  outlet with no link: link fills).
- Reprint check (code/reprint_rule.py text rule vs the story texts in work/html_clean + work/texts/nb; then among the finds; then a
  text-only check vs stories within +-3 days; then same headline (>=0.85) within +-7 days as a low-confidence fallback):
  295 reprints of sheet stories, 53 new stories (Original), 9 reprints of those new stories. Release check (release_rule.py vs
  release_texts.json): 0 copies of Gabriel releases. 2 press-release pages flagged (PR Newswire, Musical America).
- Tone/Topic/Bills for the 53 new stories rated from the Gabriel passages (Tone rated by "Claude, from article excerpt (2026-10-28)");
  reprints carry the sheet story's Tone/Topic/Bills.

## Outputs (work/out/)
- newoutlet_finds.csv (357), newoutlet_rejects.csv (373 non-finds with reason), newoutlet_linkfills.csv (327 web links for rows the
  sheet already has), newoutlet_outlet_summary.csv (766 outlets + pbs.org: status, searches, results, finds, blocked).

## Self-check
- No workbook writes, no Exa, no publishing, nothing written to the Mac library or other agents' files.
- Every find was fetched and has Jesse Gabriel in article text (snippet in gabriel_in_text); listing pages, californiafiles,
  teasers/tags-only and wrong Gabriels excluded. Blocks/paywalls recorded, not worked around.
- Caveats: the Oct 21 outlet list is a proxy (old tracker hosts). 143 finds are low confidence (rule's own low-confidence passes,
  headline+date matches without text, short pages); 17 carry "same outlet has a row within 2 days" (likely the web version of a print
  row) and 9 "possible reprint of sNNNNN" warnings. Sundial (sundial.csun.edu) and CSUN Today pages are both under csun.edu.

## Phase 2 (2026-10-28) — DONE
- Rule-7 write committed and verified on the Mac: sha a5d5bc002217b5f26797f26933398052bfec2db1bf71fb66c6b2b328cd7b44f8 (was 02c82bc5…fe10; backup in Backups/). diffcheck: 0 unexpected differences. work/coverage_current.xlsx updated (pre-copy work/coverage_pre_newoutlets.xlsx). WORKBOOK_WRITER.txt set back to "none".
- 366 library pages added and sha-verified (tar extracted with -k from _to_delete/newoutlet_pages_2026-10-28.tar; the tar and its .sha256.txt can be deleted). library_adds.csv appended.
- Self-check: all 185 pages verdict ok with Gabriel in text; IDs did not collide with agent-avtab (09721–09734 / s04687–s04700); next_sid = 4741.
