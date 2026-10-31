# REQ-4 openpyxl round-trip fidelity of the master (informational)

Ran: `cd results/REQ-4 && python3 -I roundtrip.py L/work/coverage_current.xlsx` (log `REQ-4/roundtrip.log`): `openpyxl.load_workbook` -> `save` to a temp file -> reload both; plus `REQ-4/parts.log` (zip part and per-sheet XML tag comparison). Nothing written outside results/.
Time: load 8.9 s, save 5.2 s (whole script 35 s including reloading both and the per-cell hyperlink scans).

| sheet | max_row x col | freeze | filter | hyperlinks | DV | CF | merged | images | charts | widths |
|---|---|---|---|---|---|---|---|---|---|---|
| Coverage | 8178 x 71 | C2 | A1:BS8178 | 23 | 0 | 0 | 0 | 0 | 0 | same |
| Originals | 4089 x 70 | C2 | A1:BR4089 | 0 | 0 | 0 | 0 | 0 | 0 | same |
| Bills | 1896 x 6 | A2 | A1:F1896 | 0 | 0 | 0 | 0 | 0 | 0 | same |
| Press releases | 245 x 48 | D2 | A1:AV245 | 247 | 0 | 0 | 0 | 0 | 0 | same |
| Audio & video details | 1026 x 35 | B2 | A1:AI1026 | 88 | 0 | 0 | 0 | 0 | 0 | same |
| Removed | 329 x 76 | A2 | A1:BX329 | 2 | 0 | 0 | 0 | 0 | 0 | same |
| Unlinked print pages | 1444 x 73 | C2 | A1:BU1444 | 0 | 0 | 0 | 0 | 0 | 0 | same |

Every column was identical before and after (the script prints `before>after` on any difference; none appeared). Sheet names and order identical, sheet state visible everywhere, hidden columns identical, defined names 0 before / 0 after. Verdict: PASS, no sheet, hyperlink, image or chart lost.
Zip level: the same set of parts before and after, per-sheet counts of `<hyperlink>`, `<col>`, `<sheetPr>` equal, no conditionalFormatting / dataValidation / drawing / legacyDrawing / extLst / mergeCell elements exist in the master at all (so nothing for openpyxl to drop). The master has no sharedStrings part (it was itself last written by openpyxl, inline strings), so the round trip is idempotent; a master edited by hand in Excel would first gain a sharedStrings part and Excel-only features (comments, drawings, slicers, extLst) would be at risk on the next sheet-task run - none are present now.
Not tested: cell styles/fonts/fills cell by cell (styles.xml compared only by existence), and formulas (the master has none that I looked for; `data_only=False` load keeps any).
