# agent-libinventory (T26) — DONE 2026-10-27

Scope: tracker-saved sources not in ~/Desktop/Tracker library -> copies in lib/work/library_new/. Read-only on the Mac (device_bash listing + staged _rename_*.csv / index csv). Workbook not touched. No Exa.

## Method
- Tracker sources: artifact_files/articles (3,317 codes = manifest = old_manifest), published pdf/* (6 PDFs + 53 JPGs for 37 codes, fetched with Artifact read), img/*.json (checked in JS: photos embedded in web pages via `jgimg:`, not article page images), texts/tracker (220).
- Library: 3,497 HTML, 3,434 distinct nb/pq/ws IDs + 23 jg-named; ID set copied to tmp_agent-libinventory/lib_ids.txt, sha256 of the sorted set matches the Mac (1b2aad062f8699dd).
- Helpers: lib/work/tmp_agent-libinventory/{cands.py, build.py, gap.py}; downloads in tmp_agent-libinventory/dl/.

## Findings
- All 3,317 tracker article pages are in the library (3,294 renamed + 23 jg-*.html). All 472 ProQuest/print-page copies present (435 text-only as pq-*.html).
- 37 library HTMLs (31 pq, 6 ws Valley News Group, incl. "nb-01307 (jg-d83455).html") are byte-identical to the tracker pages (sha256 checked on the Mac) but reference pdf/<code>/pN.jpg, which the library lacks -> page images missing.
- 6 real PDFs (Valley News Group full print editions, ws- rows) are not in the library (it holds no PDFs).
- texts/tracker: 217/220 stories have a library file for their Original. 3 (ws-00230, ws-01193, ws-03775) don't, but each copy is a reprint row's page that IS in the library (pq-00005, ws-01195, ws-03777). Not copied under the Original's ID.

## Outputs
- lib/work/library_new/: 43 files, 92.9 MB: 37 HTML (page images inlined as data URIs + tracker PDF-page CSS + one-line "Copy saved from the tracker" note; action=replace) and 6 PDFs (action=add).
- lib/work/library_new_index.csv: old_aid, sid, fmt, source, out_path, bytes + extra cols action, library_file, code.
- lib/work/library_gap_report.md + lib/work/library_gap_no_copy.csv.
- Story coverage (4,195 Originals): 3,962 own copy; 3 only via a reprint row; 230 none anywhere (229 Tracker scrape, 1 ProQuest).

## Notes for agent-librename / coordinator
- "replace" files should overwrite (or sit beside) the existing library HTML of the same Article ID.
- 6 ws HTMLs link their PDF as `<old aid>.pdf`; update the link when the PDF gets its new name.
- fmt for the 6 PDFs = ws (publisher-site PDFs), not pq as DECISIONS' wording suggests.
- jg-d83455: library name "nb-01307 (jg-d83455).html"; log says nb-01307/jg-00539, map says pq-00360/jg-04252 (removed duplicate). Needs an Article ID decision.

## Self-check
- 43 index rows = 43 files on disk, all byte sizes match, out_paths distinct.
- All 37 HTMLs: no remaining `src="pdf/` refs, note + <style> present; 2 rendered headless (pq-00325, ws-02714): images load (naturalWidth 1567/1584), page readable.
- 6 PDFs open with pypdf; page counts 12/12/12/16/16/12 match the tracker's data-pages.
- Library ID set checksum identical container vs Mac; 0 `jgimg:` refs in library files.
