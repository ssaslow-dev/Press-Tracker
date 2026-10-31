# RELRELATED-v1 handoff (agent-relrelated, 2026-10-28). Sammy approved; 90-day text window kept.

## Done (my files)
- code/relmatch.py: the matcher (copy of work/tmp_agent-relrelated/relmatch.py; imports reprint_rule from code/).
- code/release_related.json and build/pub/pipeline/release_related.json: the state file (241 releases, 1,059 related + 153 possibly
  related), keyed by Release ID (prNNNNN; the 5 no-posting releases by their Story-ID key).
- build/tabs/releases_data.py: block tab-releases gets "rel" = the state, filtered to stories in the build. It looks for the file
  next to the pipeline folder (dirname of tabs/), then <lib>/code, or env RELRELATED_JSON. With the field the block is 126 KB,
  under the 150 KB cap. I put the column here instead of in ins-release_pickup, because release_pickup_data.py is not mine.
- build/tabs/releases.js:
  - related() returns only evidence rows, with no bill, session or issue fallback.
  - New "Related stories · N" heading with an evidence breakdown.
  - New collapsed "Possibly related · N" section.
  - Chart and list are hidden when N = 0.
  - Facts: "Related stories" (+ possibly related), and "Bill coverage" (was "Original coverage"; counts only, bill basis only).
  - The after-list and the issue basis are removed, as is the planned 'uses' section.
  - New list facet "Related stories".
  - CSV columns: Related stories / Possibly related stories / Same-bill stories before / after.
  - node --check passes. Originals are in work/tmp_agent-relrelated/orig/.
- Unit tests: work/tmp_agent-relrelated/test_relmatch.py (14 pass). Copy to build/tests if wanted.
- Test page: work/tmp_agent-relrelated/tb/srv. Screenshots in shots/ (pr00171, pr00243, pr00063, pr00172 at 1400 light and
  390 dark), no page errors.
  - pr00171: 16 related + 4 possibly related (was 494)
  - pr00243: 2 related (was 5)
  - pr00063: 7 related
  - pr00172: 0 related + 2 possibly related, chart and list hidden (was 304)

## For the final build (apply_all, not mine)
- PIPELINE map: add 'relmatch.py': 'code/relmatch.py' and 'release_related.json': 'code/release_related.json'.
  - Treat release_related.json like release_texts.json: never shrink it with an older code/ copy, because the button updates the
    pipeline copy. Merge by key, taking the pipeline's rows for keys it has.
- Also add relmatch.py to the helper list, and both files to the sheet-task prompt's pipeline file list (docs / buttonopt).
- build/tabs/releases.js and releases_data.py are refreshed into pipeline/tabs/ by step 4l as usual.
- At the v20 build, re-run the full match on the v20 data and all article years, then copy the result to
  build/pub/pipeline/release_related.json:

  `python3 -I code/relmatch.py --index <v20 index.html> --release-texts code/release_texts.json --articles <v20 srv>/articles --json code/release_related.json --csv work/out/related_v20.csv`
- DECISIONS line (coordinator): "RELRELATED-v1: a release's related stories = evidence only (text runs −1..+90 d, quotes
  −1..+30, same bill same week on subject, same week strong subject match); 'Possibly related' = same bill same week, subject
  uncheckable; Sammy kept the 90-day text window." CONTRACT: the tab-releases "rel" field.

## For agent-buttonopt (Update button step 6, sheet_task_prompt.md; not mine)
After build_data has written blocks/ and the new saved pages have been added to copies/articles/<year>.json:
1. `python3 -I relmatch.py --data blocks/data.json --pickup blocks/ins_release_pickup.json --release-texts release_texts.json --articles copies/articles --update release_related.json --json release_related.json --releases <Release IDs of new releases (result.release_copies[].prid)> --stories <Story IDs of new Originals>`
2. Re-run `tabs_data.py <xlsx> blocks tabs --only releases`, or build_data again, then assemble.py.
3. Step 3 must also read articles/<year>.json for the years covering each new release's window, from release date −1 to +90 days.
4. Step 7: publish release_related.json as pipeline/release_related.json when it changed.

The incremental update was verified byte-equal to a full run.
