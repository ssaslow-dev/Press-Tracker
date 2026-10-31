# agent-buttonopt2 handoff (2026-10-28) — items outside my files

1. DECISIONS / CONTRACT (coordinator): "BUTTONOPT-v1 (Update button Phase 2): the page no longer decides reprints by text — every
   proposed reprint (page reprint candidates with their page, pages doc rp-<hash6>), every new find and every originator copy
   (row `_origin` {service, how, cands[{url,title,date,outlet,page: og-<hash6>}]}) is judged by sheet_task.py with reprint_rule.py;
   an originator whose text passes is added as the Original and the find becomes its Reprint; removal requests move the story's
   rows to the Removed tab (Category '5 removed in the tracker'); appended rows the tracker won't show get the red font;
   searches start 7 days before searched_to, which advances only when <=2% of searches failed; no issue-word / D-Encino site
   searches; native-script site searches only script-only queries on hosts with a story in 24 months; 1 backfill search per new
   outlet; classify prompt without bill/reach lists, 20 per call, bills tagged in the page." CONTRACT: run row keys `_page`,
   `_origin` (not sheet columns); edits doc field `reported`; result keys pages_drop, reprint_failed, reprint_untested,
   origin_added, origin_unverified, held, outlet_unresolved, removed, removal_failed, edits_reported, red_rows, av_no_channel,
   av_date_review, copies_changed; sheet_task.py flags --db-dir, --copies-needed, --copies-out, --img-cache.
2. Final build / apply_all owner (plan T4b, not done): ship `pipeline/shell.html` (published page with data blocks stripped) so
   step 6 assembles from it instead of reading the ~10 MB published index.html. The prompt still reads the published page.
3. tabs owner (build/tabs/releases_data.py): the TABS harness regenerates tab_releases.json without "rel" (release_related.json
   not found from the harness's tmp folder: `tabs_data.py --only releases` passes no lib ctx). releases.test.js now reads the
   evidence rows from the page's srv/blocks/tab_releases.json, so it passes either way.
4. Final build: full copies rebuild drops the copies of removed stories (copies_out only adds); no action needed beyond the usual
   make_copies run with `--img-cache work/img_cache --pdf-restore work/img_cache/pdf_restore --img-strict`.
