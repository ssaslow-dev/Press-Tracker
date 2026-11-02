# NEWSBANKPDF-v1: what the PC app needs (patch proposals; NOT wired in)

The Update station now sends NewsBank stories with their own PDFs (`files/nb-<hex>.pdf`, FORMAT.md 2b). `updatefolder/formats.py` and `take_update.py` already take them in (done, tested). The save needs three changes in the pipeline copy, made at assembly like the PHOTOLINK patches:

| File | Applies to | What |
|---|---|---|
| `patches/01_sheet_task_nbpdf.patch` | `code/sheet_task.py` | NewsBank pages docs (`nb` key): `check_page` skips the web cleaning and web copy checks (they refuse NewsBank text: "page host is not the Publisher link host"); `apply_pages` saves the PDF as `<year>/nb<Article ID><o\|r>-<Story ID>.pdf`, fills Saved Copy? / File type "Newsbank pdf" / File name and the text-derived cells; `wrong_gabriel` keeps NewsBank text that lacks his name (only "another Gabriel" drops it); a citation-page-only story gets Saved Copy? No; `main` sets `task.db_dir` so the PDFs are read from `<db-dir>/files/` |
| `patches/02_date_rules_newsbank.patch` | `code/date_rules.py` | `_date_src: "newsbank"` means Date source "NewsBank" ("print edition" for Edition Print) |
| `patches/03_pdftext_pypdf_band.patch` (= `pdftext_pypdf.py` here) | `winpack/patches/pdftext_pypdf.py` | a story PDF cut from a shared page carries `/AJGBands`; its text is read inside the band only, so a neighbour's lines never reach the reprint test or Clips search. Same result as before for every other PDF |

## How to wire it into `assemble_app.py` (not done: another builder is editing it)
Add to the list of app patches applied to the pipeline copy, after the PHOTOLINK ones, with the existing `patched_copy(src, dst, patch_file)`:
`('sheet_task.py', '01_sheet_task_nbpdf.patch')`, `('date_rules.py', '02_date_rules_newsbank.patch')`, and for `pdftext_pypdf.py` apply `03_pdftext_pypdf_band.patch` to the winpack copy (or copy `pdftext_pypdf.py` from this folder over it). Copy the three patch files to `app/patches/`. Then regenerate `PIPELINE.sha256` (assembly already does). The patches apply by the assembler's own exact-once rule; `tests/e2e_sheet_task.py` shows the sequence.
Also: the saver's `--db` copy already carries `files/` (it copies the whole staged db folder), and `pages_in` commits any file under the pages folder, so no saver change is needed. The tracker page's viewer opens `nb*.pdf` library files the way it opens today's.

## Tests
`cd work/localapp/newsbank_pc && python3 -I -m unittest discover -s tests -t . -v` (band reader), `python3 -I tests/e2e_sheet_task.py ZIP WORKBOOK SCRATCH` (about 1 minute: patched sheet_task on a copy of the snapshot workbook with the station's real zip: 33 rows, 33 PDFs, no conflicts), and `updatefolder/tests/test_nbpdf.py` (refusals).
