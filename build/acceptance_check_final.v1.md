# Final acceptance check (slimmed, Sammy 2026-10-27) — run ONCE, by an agent that hasn't seen the work

Already verified upstream, NOT repeated here: cell-level "no existing value changed" (apply_fills/migrate_ids verify), sha256 of committed files, old→new ID 1:1 mapping, test suites (run before publish), NewsBank split headlines (all 3,982 checked), per-file cleaning safety checks, regroup independent sample (done inside the regroup task).

Only cross-system checks no single step can see:
1. Sheet ↔ live tracker: story count = Original rows minus press releases; 30 random stories — headline, outlet, date, tone, Reach, authors, links match the sheet row.
2. Sheet ↔ library: every File name cell points to a file that exists in Desktop/Tracker library under the new name; every library file maps to a sheet row (orphans listed).
3. Tracker ↔ library: 30 random "Saved copy" buttons open the right article (headline match), including NewsBank-led stories (the suspected empty-button case).
4. Live page smoke test: filters (Reach multi-tag, per-author links, topic), Update button dry run, viewer, old jg- links still resolve.
5. Rename undo log is complete (every renamed file has an old→new line).
Report: pass/fail per item, with examples of any failure.
6. Article files load in the live tracker (Sammy, 2026-10-27): for EVERY story with a "Saved copy" button, the file it points to (articles/*.json entry, pdf/*, NewsBank text) is present in the published artifact, loads without error, and renders non-empty article text in the viewer. Automated over all stories (fetch each referenced file from the published artifact and parse it), plus a browser pass in Playwright that opens the viewer for 50 random stories across every copy type (web HTML, NewsBank text, ProQuest, print PDF) and checks for console/network errors. Report any story whose button opens nothing, errors, or shows the wrong article.

Sammy (2026-10-27): SKIP placeholder rows everywhere in this check — any row whose File name is `BLOCKED – TinyFish` or `RETRY – TinyFish` is not tested (not a missing file, not a missing copy, not counted as a failure). Just report how many rows carry each placeholder.
