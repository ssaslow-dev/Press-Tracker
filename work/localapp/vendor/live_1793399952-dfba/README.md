# Copy of page-build inputs from the live tracker (read-only)

- Source: claude.ai artifact 5wHur4aRkSbAu6FscDpTjv (https://claude.ai/code/artifact/27f923dc-2407-40a0-b8a9-ec3dfed87ad9), version id 1793399952-dfba, contract 0.2.91.
- Fetched: 2026-11-02 with the Artifact tool (action read). Nothing was published to, edited in or written to that artifact or its database (NEWPROJECT-v1).
- Paths mirror the published paths. Why each file is here (the repo has none of them):
  - `pipeline/shell.html`: the page skeleton and CSS (build input BASE; `code/make_shell.py` makes it from a full page).
  - `pipeline/sid_map.json`: legacy jg- codes for build_data's idmap (`work/sid_map.json` in the old workspace).
  - `pipeline/tabs/outlets.js`, `pipeline/tabs/outlets_data.py`: the Outlets tab; `build/tabs/` in the repo lacks them.
  - `pipeline/insights/*`: Insights views and data builders (`build/insights/` in the old workspace) plus `bill_milestones.json`.
- Not copied here, on purpose:
  - `pipeline/tracker.js`: byte-identical to `build/js_merged.js` (sha256 92e2b785c2f11311c85ffd255d7a1fe79601987ed89c7656c4d6abf48902315c), which `code/apply_all_patches.py` regenerates from `code/tracker/`.
  - `pipeline/legacy_index.html` (4.4 MB, sha256 fe08f27631f631748d279959ac671d7a219548c80b17afbe049830016ac001b5): its data block carries translated story text (`text_en`, 453 stories), so it stays out of the repository. `work/localapp/build/build_tracker.py` takes it with `--legacy`.
  - Article, image and `data/` files (full article text, the workbook).
- Everything else under live `pipeline/` equals `code/`, `build/tabs/` or `docs/` in the repo, except `outlets.json` (the repo's is newer: 9 more records) and `docs/DECISIONS.md` (the repo's is newer).
