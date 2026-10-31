# AGENT BRIEF (read this instead of HANDOFF.md; open other docs only for the section you need)
Project: press-coverage database of CA Assemblymember Jesse Gabriel. Coordinator = main session; you are a background agent. L = this folder.

## Where things are
- Master workbook (Mac): ~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx. Working copy: L/work/coverage_current.xlsx (check its sha against BOARD.md's current master).
- SHARED DATA (load this, don't re-parse the xlsx): `python3 -c "import sys; sys.path.insert(0,'L/code'); from shared_data import load; d=load()"` → d.coverage, d.originals, d.removed, d.av, d.unlinked_print (DataFrames), d.text(article_id) (saved-copy text), d.copy_path(article_id). Rebuilt by L/code/shared_data.py --rebuild after each master write. Also d.press_releases, d.bills, d.copy_paths(aid) (all candidates). Caveat: copy↔row matching isn't hand-verified (some IDs resolve via old IDs or a story-level pub2 copy); when a decision hinges on the text, confirm the copy's headline/outlet matches the row.
- Mac library ("Tracker library"): saved copies <year>/, raw pages _original_html/<year>/, Backups/, Work archive/. Reach via mcp__remote-devices__ tools.
- Code: L/code/ (sheet_task.py, reprint_rule.py, tracker/NN_*.js); build: L/build/build.sh; tests: L/build/tests/.
- Plans: L/build/V22_ORDER.md (order of work), RULES_REVIEW_PLAN.md. Board: L/BOARD.md. Rules: L/DECISIONS.md (grep the tag you need: REPRINT-v2, INCL-v1, TONE, OUTLET, COPIES-v1, DATES-v1, NOCOPY-v2, OWNED-v1, PRINTTAB-v1, AVTAB-v3, RELRELATED-v3). Tone rubric: L/TONE_GUIDE.new.md. Naming/layout: L/CONTRACT.md.

## Hard rules
- Write only in your assigned folder unless told otherwise. Never write the master (rule 7, one writer: L/work/WORKBOOK_WRITER.txt) or publish unless your brief says so.
- Library is ADD-ONLY: never delete or overwrite; new names only. Deletes → move to _to_delete/ with a log.
- Before building any new row: dedupe against the master (URL, and outlet+headline+date ±2d). An originator already in another story = a merge, not a new row.
- Web: TinyFish (search/fetch_content, ≤4 in flight) and WebSearch/WebFetch. NO Exa. Never work around paywalls/blocks, never log in, never enter credentials.
- Report permission denials to the coordinator; never work around them.
- Fill blanks only unless DECISIONS overrides. Same text → same tone/tags.
- Gabriel's own channels are never coverage (OWNED-v1). Release services/aggregators are never the Original.
- Dates: outlet's local calendar date; displayed date line > metadata > URL > NewsBank/ProQuest; never save/lastmod/updated (DATES-v1).

## Standing rule: reference data first (LEARN-v1, Sammy 2026-10-30)
Before any web fetch or search: (1) check the reference data (`code/outlets.json` location/owner/reach/periods, `code/reporters.json` + `code/reporter_employment.csv` dated tenures, `code/outlet_rules.json` aliases/channel names/blocked hosts) and `code/lookup_cache.json` (URL -> what it settled, verdict, date checked, source; blocked hosts; dead link -> archive copy; searches that found nothing) with `lookup_cache.Cache.load().needs_fetch(url)`; (2) go to the web only for something genuinely new; (3) save every confirmed answer back (record + cache entry, mirrored to `build/pub/pipeline/`). Medium/low finds go in the cache as `unconfirmed` and never stop a later fetch. The sheet task does the same: `--lookup-cache` / `--lookup-cache-out`, `result.fetch_plan`, run-doc `lookups`.

## Reporting
Final report ≤ the line count in your brief: counts, outputs (paths), decisions needed, errors. Hand-check a sample of your own output and give the rate.
- Models: Haiku for fetch/save loops and rote steps; Sonnet for light-judgment mechanical work; Fable for judgment only (MODELS-v1).
