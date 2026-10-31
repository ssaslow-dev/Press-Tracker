# agent-v21-post (2026-10-28, after v21 publish 1793220623-9df2, page 884d7efc…)

## 1. Comment threads (40 threads read; 5 were open)
Checked against work/build_last/lib (sha 884d7efc = live), work/tmp_rp-final/shots, work/tmp_v21review/review.md, source.
- 83b36e23 confirm popups: RUNCONFIRM-v1 live (review §4, confirm_test 56/56). Replied "live", RESOLVED.
- e10d15f0 time axis: TIMEAXIS-v1 live (year tier on AB 418, axis_probe 0 overlaps, caps 8/5). Replied, RESOLVED.
- d38d2b91 release-list bill chips: build/tabs/releases.js list cell uses chips(); shot list_1400_light_top.png shows chips. Replied, RESOLVED.
- 9eb75f10 corner (Press releases list): CORNER-v4 live, Chromium DSF2 56/56 = Clips; WebKit never checked (not installed). Replied, LEFT OPEN pending Sammy's confirmation on his browser.
- de9c2baa "· ·": NOT fixed. code/tracker/06_story_sheet.js factline always emits `<span>${reachTags(r)…}</span>` (and the topic span); CSS `.factline>span:not(:last-child)::after{content:"·"}` gives empty spans a separator; no :empty rule in the page. Replied "not fixed in v21, queued", LEFT OPEN. Fix: skip empty spans (or add `.factline>span:empty{display:none}`).
- ab7c842d corners, 56b789c7 tick-all: were already resolved with "ships next update" replies; added "live in v21" replies (acknowledge_duplicate), no re-resolve.
- Release box separations (bae35bbf) and related stories (eb3d0330) already resolved with "live" replies in v20; nothing added. All other threads already resolved.
- acknowledge_duplicate used on every reply above (each thread had a standing Claude reply); each adds the v21 "live"/"not fixed" fact.

## 2. Handoff kit
- build/handoff/live_listing.txt = Artifact list scope "files" verbatim (139 files, version 1793220623-9df2).
- record with --map work/tmp_rp-final/publish.json: exit 2, 35 unresolved — its format (batches[].files / final_batch / page) is not read by make_handoff_kit.read_map (expects files / publishes[] / file_path). Converted to work/tmp_v21-post/publish_map.json (publishes = batches + final_batch with page_sha256); rerun exit 0, nothing to fetch. Ledger: 139 files, 249,437,528 bytes, page 884d7efcfba5; verified sha 53 / size 34 / live-read 52. Suggest make_handoff_kit read `batches`/`final_batch` (or make_publish.py emit `publishes`), and per-file shas in the map.
- bash build/build.sh --kit: exit 0; rebuild test page_ok (lib = pipe = live 884d7efc), 15 blocks 0 differ, copies 28 same, pipeline 0 differ / 0 missing, apply_all --check OK. 6 parts 368 MiB; SHA256SUMS OK; verify on an unzipped copy 0 bad (139 publish + 10,522 source). Rebuilt once more after the doc edits below (see end).
- HANDOFF §0.3 kit facts + §8.2 open threads + Changelog line updated.

## 3. Mac _docs
- Old 6 copies mv'd to Tracker library/_archive/_docs_pre_v21_2026-10-28/; 7 new (README, CONTRACT, DECISIONS, BOARD, HANDOFF [new], TONE_GUIDE, clean_playbook) committed from /mnt/user-data/outputs/v21docs (SHA256SUMS.txt); Mac shasum 7/7 equal. _docs/archive/ untouched.
- Note: L/DECISIONS.md is ahead of build/pub/pipeline/docs/DECISIONS.md (and the live pipeline copy, 122,786 bytes): lines appended after the v21 build. Mac _docs has the newer L copy; the pipeline copy catches up at the next apply_all + publish.

## 4. Project docs
- /home/claude/projdocs/{README,CONTRACT,DECISIONS,BOARD,HANDOFF}.md + SHA256SUMS.txt (no Projects tool here; coordinator syncs).

## Kit rebuild after the doc edits (20:57Z): EXIT 3
- Another agent's REPRINT-v2 edits landed at 20:56:35Z (code/make_copies.py, reprint_rule.py, outlet_rules.json, sheet_task.py, + reporters.py etc.; pre-edit copies in code/_history/*_pre_reprintv2_2056*). Rebuild test: page sha still = live 884d7efc, blocks 15/0, apply_all --check OK, but copies 26/28 (articles/2024.json, articles/manifest.json differ) and pipeline differ_from_live: docs/DECISIONS.md, make_copies.py, outlet_rules.json, reprint_rule.py, sheet_task.py. These are unpublished source changes, not a v21 defect. The 20:54Z kit passed every check but was overwritten by this build.
- Kit on disk: verify 0 bad (139 publish + 10,534 source); SHA256SUMS OK; HANDOFF inside the kit = current. Regenerate after the REPRINT-v2 publish (record + build.sh --kit).
- HANDOFF §0.3 / Changelog amended; Mac _docs/HANDOFF.md and /home/claude/projdocs/HANDOFF.md re-copied after the amendment (sha below).
- Mac _docs final shas (7/7 = L): BOARD 2c0f66ad, CONTRACT da251888, DECISIONS a6865688, HANDOFF c212f7bb, README ef0b6d4f, TONE_GUIDE 85f08259, clean_playbook fe3c0159.
- Bridge pitfall: re-committing the SAME stagedPath after changing its content wrote the OLD bytes (mtime updated, sha old). Staging under a new path (/mnt/user-data/outputs/v21docs_b/) fixed it. Always sha-verify after a re-commit.
- The kit's own source/HANDOFF.md predates the §0.3 amendment (amendment only notes the exit 3); not rebuilt again since a rebuild would fail the same way until REPRINT-v2 is published.
