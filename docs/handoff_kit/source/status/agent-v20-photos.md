# agent-v20-photos — v20 code pass: photos, PDF pages, copy order, AV preview cleanup (2026-10-28)
Owned files: code/tracker/06_story_sheet.js, code/make_copies.py, code/clean_html.py, code/clean_rules.json (unchanged), new code/img_embed.py,
code/av_display_clean.py + code/av_rules.json (copied from tmp_agent-previewclean, identical). Pre-change copies: work/tmp_agent-v20-photos/pre/.
No workbook writes, no publishing, no Exa, no full harness runs.
## Changes
- code/img_embed.py (new, PHOTOS-v2): candidate choice (srcset <= 1000w, lazy attrs, <picture>), cache index over work/img_cache
  (manifest.json + worklist.json), fetch/normalize (same format as agent-imgfetch), resolve_page (embed or drop + prune emptied
  wrappers, captions kept), embed_page (save-time, appends to manifest), unresolved() build gate.
- make_copies.py: --img-cache/--pdf-restore/--img-strict (photos embedded from cache -> img/1NN.json shards; unfetchable dropped;
  8 PDF page images restored + 4 PDF links dropped); ORIGIN ROOT FIX D copy order; AVPREVIEW-v1 fix A (av_clean on Episode /
  Broadcast segment / Video clip Originals; nb_page(av=True) without PDF caption / word count / citation); unchanged copies are byte-identical.
- clean_html.py: fix_imgs() in find mode (F1). CLIFIX + davisvanguard/jweekly/gvwire rules were already in (v19finish) - verified
  (find mode single-file runs; DV rule matches).
- 06_story_sheet.js: safeImgs() before srcdoc + hideBroken() on load + CSS for empty src (self-contained, no other file touched).
- work/img_cache: fill pass added 10 records (1 ok: s00002's CalMatters lead photo). Backups of manifest/worklist in pre/.
- build/pub/pipeline/: img_embed.py, av_display_clean.py, av_rules.json copied (PIPELINE list addition = handoff).
## Self-check (old = pre make_copies, new = this one; same inputs, master copy d00118c5…)
- 3,873 copies both. 3,544 byte-identical; 260 photo-only (235 stories + 25 releases; text identical after stripping tags);
  240 source changed (reprint page -> Original's NewsBank text); 73 AV-cleaned (74 incl. one also source-changed).
- Photos: 310 embedded from cache, 8 PDF pages restored, 340 dropped (cloudflare 86, 403 53, 404 49, http402 12, not fetched 106 =
  ads/pixels/logos never in the worklist, src="" 8, other 26). Gate: 0 unresolved; 33 local pdf/ refs kept.
- Sizes: img/100.json 11.9 MB, img/101.json 8.9 MB, releases.json 7.3 MB, largest year shard 6.8 MB (all < 16 MB); copies total 64.0 MB (was 43.4).
- AV: test_av_clean.py (copy in work/tmp_agent-v20-photos/avtest, code/ version) 80 copies, 75 changed, 0 fails, 0 flags. In the build 74 change:
  s00486 now uses its Original's NewsBank text, which has nothing to clean.
- Screenshots (work/tmp_agent-v20-photos/shots/, harness srv/viewer.html with the page CSP): s00002 lead photo, s04710 12 photos (were src=""),
  s02009/s03273 failed photos hidden with captions kept, s02782/s02409 PDF pages + no PDF link, pr00005 release photos, s04692 AV clean;
  shots_old/: old unprocessed copies through the new viewer backstop show no broken icons.
## Left
- handoff.md: buttonopt (sheet_task save-step embed_page), apply_all PIPELINE list, final-build make_copies flags.
- CalMatters cleaner rules (rootfix B) not done (not in my items).
## Follow-ups (coordinator, from v20-origin-av handoff)
- clean_rules.json calmatters.org (only that entry changed; pre copy in work/tmp_agent-v20-photos/pre/): cut READ NEXT..Read more from CalMatters,
  section "read next" (older inline teaser label), ltail read more from calmatters / nonpartisan, independent california news for all / about the author,
  lkill share bar, election-newsletter promo, voter-guide promo, "Just the right amount of news" signup box, "We want to hear from you", About CalMatters, Most popular.
  Test: live calmatters.org page of ws00009o-s00002 (find mode): 2,139 -> 1,069 words, matches agent-calmatters' hand clean except the byline line and none lost;
  (a "Republish" tail was tried and dropped: it matched the share bar above the article). Library mode on 47 CalMatters-URL copies: 15 change, all removals are
  About the Author/bio/About CalMatters/"Most Popular"/"read next" label; ws00009o-s00002 unchanged.
- make_copies RENAME-v1: when html_clean holds old+new names of a renamed file, the name whose -s<Story ID> matches the row's current Story ID wins, and a stale
  -s<old sid> name is not indexed under that old story. Rerun on master 8002aa59: 4,117 manifest keys = last run, 0 lost / 0 gained, 0 source changes, page bytes
  identical; only s01819/s01820 moved year shard (their dates changed). The 22 renamed HTML files are reprint pages: none is a story copy (Originals have own copies).
