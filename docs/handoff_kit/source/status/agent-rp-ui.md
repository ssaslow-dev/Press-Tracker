# agent-rp-ui — release page/list UI (RELPLAN phase 2)
## Own: build/tabs/releases.js, releases_data.py, 00_head.js (CSS), 53_tabs.js (ⓘ + release viewer), 01_authors.js (rel labels, relHits), relpage.py + make_copies release part. Pre-edit copies work/tmp_rp-ui/pre/.
## Log
- started
- backend #7 DONE in code/make_copies.py (RELIMG-v1; patch script work/tmp_rp-ui/patch_mc.py): release pages built before the image shards, data: photos -> img/1NN.json jgimg refs (after all story images), >1200 px wide downscaled (JPEG q75) when smaller. Old vs new run (work/tmp_rp-ui/mc_old|mc_new, same inputs as v20-final): every story shard byte-identical; releases.json 7.33 MB -> 1.52 MB (pr00045 2.08 MB -> 8 KB; largest release 23 KB); release text byte-identical except img src (244/244); 40 refs, 0 unresolved, 0 data: left; 3 photos downscaled (5.81 -> 4.61 MB); img/101.json gains release images (old keys unchanged), new img/102.json (1.55 MB). Publish must ship articles/releases.json + img/101.json + img/102.json together.
- releases_data.py: `rules` table (from relmatch/release_rule/relcopy/reprint_rule constants), `bc` bill coverage with relmatch windows + not-linked count (backend #9), _tab_rows reads Copy story ID 1/2 (and old names), r[url][4] emptied when thr.pp exists. tab-releases 149,657 B (< 150 KB cap).
- releases.js rewritten (RELUI-v1): UI items 1-6, 8-11 (7 was rp-reverse's); tiers from rules (later/laterquote -> Later coverage; nearcopy/anchor labelled); thr threads/pairs/milestone/Joint with/Others named; no rule paragraphs.
- 53_tabs.js: tbInfo ⓘ component + CSS (relui-css), tbOpenSaved list + tbCopySheet viewer cleanup, entity-page hooks rowTag/rank/how/below.
- 01_authors.js: anchor + laterquote in REL_RANK/REL_EV/REL_FROM, labels from rules.t; relHits patch from rp-clips (relfrom) + links to Press releases tab (backend #8).
- 00_head.js not touched (tab CSS lives in 53_tabs.js).
- Scratch build work/tmp_rp-ui/build.sh -> b/srv (articles/img from mc_new); shots work/tmp_rp-ui/shots/ (pr00171, pr00244, pr00187, pr00139, list, preview pr00154 + ⓘ popover; 1400/390 x light/dark), probe.json; 0 page errors. No harness run.
- Not done: Export as icon in filter row; Who cluster one-line on phones (hlist "+N more" used instead). Copies of pr00154 have no saved copies (press-release stories get none), so its viewer shows "1 of 1".
- Handoffs: work/tmp_rp-ui/handoff.md. DONE.
