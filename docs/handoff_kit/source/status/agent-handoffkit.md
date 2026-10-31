# agent-handoffkit (2026-10-28)
Scope (coordinator, revised twice): regenerable handoff-kit INFRASTRUCTURE, run once; no delivery to outputs/Mac yet; DB export step prepared, not run.

## Done
- New code/make_handoff_kit.py (record / build / verify) + `build/build.sh --kit` hook (exec's `make_handoff_kit.py build`; normal build.sh unchanged otherwise).
  - record: ledger build/handoff/ledger.json from the verbatim Artifact list (build/handoff/live_listing.txt) + publish maps; blobs in content store work/live_store/<sha256>; unresolved -> build/handoff/need_fetch.json, exit 2.
  - build: handoff_kit/publish (+ MANIFEST.tsv, capabilities.json, BATCHES.json: 5 file batches <=60 MB/250 files with republish/placeholder.html, page last), handoff_kit/source, clean-dir rebuild test, REBUILD_TEST.json, KIT_README.md, parts/*.zip <=90 MB (deterministic), SHA256SUMS.txt.
  - verify: checks an unzipped kit against MANIFEST.tsv + source/FILES.sha256.
- New code/db_reseed.py: work/db_export/<artifact>/<collection>/<doc_id>.json -> ArtifactData batch payloads (<=50 writes, same doc ids, format of build/review/seed). Self-tested on a synthetic export (120 + 2 docs). build writes source/db_export/EXPORT_CHECKLIST.md (12 collections, HANDOFF 0.5) and puts counts in KIT_README once exported.
- build/handoff/project_memory.md: the two old-account Project memory files, verbatim.
- README.md: new section "5. Handoff kit" (how/when: after every publish; record then build).
- Ledger bootstrap: maps work/tmp_agent-v20-final/publish2.json + work/tmp_agent-v20b-subtitle/publish.json (86 files sha-matched to the maps), the 52 files kept from older versions (img/0..15, 36 pdf jpgs) read back from the live artifact (work/handoff_fetch, 2 reads) = all 52 equal to the local copies. Second record run used no roots (incremental mode works).

## Self-check
- Live 1793174282-172b: 138 files, 250,491,170 bytes; page c252e5a1…5587; verified 86 sha + 52 live-read.
- Rebuild test (clean folder, source/ only): build.sh LIB = PIPELINE = c252e5a1… (15/15 blocks); make_copies 28/28 files identical to live (articles/*, img/100, img/101); build/pub/pipeline = live pipeline/ (0 differ, 0 missing); data/release_texts.json = pipeline copy; data/sheet.json decodes to coverage_current.xlsx (4d7fb37c…); apply_all --check OK.
- Zips: sha256sum -c OK, unzipped into a fresh folder, verify 0 bad, build.sh from the unzipped tree = c252e5a1…. Two runs gave identical data/publish zip shas.
- Parts: kit-1-docs-code-01 38.2 MB, kit-2-data-01 89.3 MB, kit-2-data-02 85.7 MB, kit-3-publish-01 85.9 MB, kit-3-publish-02 81.2 MB (363 MB).

## Notes / for the coordinator
- README.md edit reaches pipeline/docs/README.md at the next apply_all + publish (not run here).
- HANDOFF.md 0.3 marks the kit "[unverified]"; it can now point at handoff_kit/parts/KIT_README.md (owner agent-handoffdoc).
- Account-specific ids (trigger id in 42_update_buttons.js, tracker URL in sheet_task_prompt.md) are still the old ones in the kit by design (byte-identical); KIT_README says to change them per HANDOFF 0.4.
- Some side tools (code/fetch*, code/billstatus, build/insights/_shell) hardcode the old L path; not part of the build.
- Not delivered: nothing copied to /mnt/user-data/outputs or the Mac (per scope change).
