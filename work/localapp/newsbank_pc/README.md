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

---

# PROQUESTPDF-v1: ProQuest article PDFs (two more patches, same status: proposals, NOT wired in)

The Update station's "Add ProQuest PDFs" box sends each ProQuest article with its text (`pages/<id>.json` key `pq`) and, when it could be copied, its PDF (`files/pq-<hex>.pdf`). `updatefolder/formats.py` and `take_update.py` already take them in (the same PDF safety checks as the NewsBank ones; tested). The save needs two more small changes in the pipeline copy. **They apply after 01 and 02** (they patch the lines those two added), so keep the order:

| File | Applies to | What |
|---|---|---|
| `patches/04_sheet_task_pqpdf.patch` | `code/sheet_task.py` (after 01) | a pages doc with a `pq` key: `check_page` skips the web cleaning and the web copy checks (a ProQuest text is not the publisher's page: copy check R1 would refuse it); `apply_pages` calls `apply_pq_pdf`, which saves the text as `<year>/pq<Article ID><o\|r>-<Story ID>.html` (the library's ProQuest-copy name and form), File type `ProQuest pdf`, Saved Copy? Yes, File name, Word count and Mentions "Gabriel" from the text; and keeps the PDF as `_original_pdf/<year>/pq<Article ID><o\|r>-<Story ID>.pdf` (checksum checked; a missing or wrong PDF is flagged `pdf_missing` and does not stop the text copy). Other Gabriels and a full text that lacks him are skipped as for a web page (ProQuest text is the whole article, unlike NewsBank's) |
| `patches/05_date_rules_proquest.patch` | `code/date_rules.py` (after 02) | `_date_src: "proquest"` means Date source "ProQuest" ("print edition" for Edition Print) |

No change to `pdftext_pypdf.py` (a ProQuest PDF has no bands) and none to the saver: `commit_library` already copies every file under the pages folder, so `_original_pdf/<year>/...` is committed add-only like `_original_html/`.

To wire in (not done: another builder is editing `assemble_app.py`): add, in the same place and the same way as the NewsBank ones and after them, `('sheet_task.py', '04_sheet_task_pqpdf.patch')` and `('date_rules.py', '05_date_rules_proquest.patch')`; copy the two patch files to `app/patches/`; regenerate `PIPELINE.sha256` (the assembler does).

Tests: `python3 -I tests/e2e_pq_sheet_task.py ZIP WORKBOOK SCRATCH` (about 1.5 minutes: patches 01-05 on a copy of the pipeline, the station's real zip, a copy of the snapshot workbook: 6 rows, 6 `pq...html` copies, 6 `_original_pdf` PDFs, no conflicts, and a second pass adds nothing), `updatefolder/tests/test_pqpdf.py` (refusals, including hostile ProQuest PDFs), and the station's `tests/pq/verify_pq_zip.py`.
