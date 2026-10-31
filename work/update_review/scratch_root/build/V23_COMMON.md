# v23 common brief (all v23 review/design agents)
- Read L/AGENT_BRIEF.md first (rules, paths, shared data). Base = master 49baead0 (v22, live version 1793236038-04e6). Load data via code/shared_data.py load() — already built for 49baead0.
- The built tracker page (v22): L/work/tmp_v22-int/srv22/ — NOT build/pub, which is stale (Oct 27) (serve locally, e.g. `python3 -m http.server` in build/pub, Playwright is installed). Tab sources: code/tracker/*.js and the tab modules (build/pub/pipeline/tabs/*.js are BUILD COPIES — find the source, don't edit either).
- READ-ONLY: write only in your own folder L/work/tmp_v23_<yourname>/. No master writes, no code/ edits, no publishing. Deliverables = findings.md + data plan CSVs (Article ID, column, old, new, evidence, confidence) + code patches (patch files with tests, dry-run against code/).
- TABKEEP-v1: keep each tab working as it does; fix wrong data/counts/logic within the current design. Label every proposal FIX / TWEAK / NEEDS APPROVAL (removals, redesigns, new features). Past UI decisions in DECISIONS stand.
- Don't re-verify v22's counts or redo finished reviews (reprint, tags, inclusion, outlets record, dates, copies) — use their results.
- MODELS-v1: if you need a big fetch loop, say so in your report rather than burning tokens; keep TinyFish ≤4 in flight; no Exa.
- Hand-check a sample of your own findings and give the rate. Report ≤10 lines.
