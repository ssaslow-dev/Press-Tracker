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

**Section and Page** are never written for a ProQuest row (answer 1): the pages doc's `pq.header` still carries them as a record, and neither patch copies them.

To wire in (not done: another builder is editing `assemble_app.py`): add, in the same place and the same way as the NewsBank ones and after them, `('sheet_task.py', '04_sheet_task_pqpdf.patch')` and `('date_rules.py', '05_date_rules_proquest.patch')`; copy the two patch files to `app/patches/`; regenerate `PIPELINE.sha256` (the assembler does).

Tests: `python3 -I tests/e2e_pq_sheet_task.py ZIP WORKBOOK SCRATCH` (about 1.5 minutes: patches 01-05 on a copy of the pipeline, the station's real zip, a copy of the snapshot workbook: 6 rows, 6 `pq...html` copies, 6 `_original_pdf` PDFs, no conflicts, and a second pass adds nothing), `updatefolder/tests/test_pqpdf.py` (refusals, including hostile ProQuest PDFs), and the station's `tests/pq/verify_pq_zip.py`.

## PROQUESTPDF-v1 answer 2: ProQuest outlet names (one more patch proposal, NOT wired in)

`patches/06_sheet_task_pq_outlet_aliases.patch` (applies after 01 and 04; independent of them): `code/sheet_task.py` reads `proquest_outlets.json` (the Update station's `data/proquest_outlets.json`, copied beside `sheet_task.py` and `outlet_rules.json`) and adds each ProQuest-name -> tracker-name pair as an alias in `OUTLET_RULES['aliases']` (an alias already in `outlet_rules.json` wins; a place-specific pair is skipped because generic names are already told apart by city). Effect: `norm_outlet('The Center Square') == norm_outlet('Center Square California, The')`, and `Center Square Texas, The` stays separate (`keep_separate`). **Needed only if a ProQuest-named outlet can reach the save**: the station already writes the row's `Outlet` in the tracker's spelling, so the same-outlet and reprint checks see one outlet without it. No data file next to `sheet_task.py` = behaviour unchanged. To wire in: copy the data file and the patch to `app/patches/` and add `('sheet_task.py', '06_sheet_task_pq_outlet_aliases.patch')` after the 04 entry; regenerate `PIPELINE.sha256`. Test: `python3 -I -m unittest discover -s tests -t . -p test_pq_outlet_alias.py` (applies 01, 04, 06 to a copy; needs the `patch` program).

---

# PRJUDGE-v2 and NBTV-v1: two more patches (proposals, NOT wired in)

| File | Applies to | What |
|---|---|---|
| `patches/07_sheet_task_prjudge2.patch` | `code/sheet_task.py` (any point after 01; independent of 04 and 06) | `add_row`: a row whose `_pr.v` is `no` (the Update station judged it from its own text: another issuer's repost on a news outlet, or a wire / official-site item whose text is not a release) is NOT marked Press release = Yes by the outlet-name rule (`is_press_release`: PR_OUTLETS / PR_HOSTS); it is listed in `result.json` under `press_release_station_no`. A row without `_pr` (an old update, the web Update button) behaves exactly as before. Copies of HIS releases are untouched: `release_rows` / `_rel_mark` / the near-copy and title rules still mark them Yes, and `unmark_untestable_wire` is unchanged. |
| `patches/08_date_rules_airdate.patch` | `code/date_rules.py` (after 02) | `_date_src: "airdate_pt"` means Date source "air date (Pacific)" (a NewsBank broadcast transcript whose Date the station converted to the Pacific air date, REVIEW4-v1 F1). Needed only for the label; without it such a row would read "unknown". |

**How the app assembler should include them** (not done: another builder owns `assemble_app.py`): in the same list and the same way as 01-06, in this order after the existing entries: `('sheet_task.py', '07_sheet_task_prjudge2.patch')` and `('date_rules.py', '08_date_rules_airdate.patch')`; copy both patch files to `app/patches/`; regenerate `PIPELINE.sha256` (the assembler does). They use one line of context, so they apply with the assembler's exact-once rule after 01-06 (checked: 01,02,04,05,06,07,08 and 01,02,07,08 both apply cleanly).

Tests: `python3 -I tests/e2e_sheet_task.py ZIP WORKBOOK SCRATCH` now applies 07 and 08 and has a second pass in which the station's verdict for the wire-named row is No (the save leaves Press release blank and reports it; the control pass marks it Yes).

| `patches/09_sheet_task_printpages.patch` | `code/sheet_task.py` (after 01; checked with and without 04, 06, 07) | PRINTPAGES-v1 / ORIGCOPIES-v1: `apply_print_pages` (called after `apply_pages`): a pages doc with `nb.kind: print_page` is kept as `_original_pdf/<year>/<Article ID>_p<page>.pdf` and, when `nb.as` is `unlinked`, the run's `print_rows` entry becomes a row of the "Unlinked print pages" tab (the tab had no writer; next Article ID from the one sequence; an existing print-page link is never added twice); `extra_copies` entries (the update folder's contract) are kept as `_original_pdf/<year>/nb<Article ID><o\|r>-<Story ID>.pdf`, listed in Other files when that column exists, skipped when the row already holds an nb PDF, blank cells filled only. `VT_NEW_OK` gains the Unlinked tab (the verify step refused new rows there). Assemble after 01 (and 04, 06, 07). `e2e_sheet_task.py` covers it. |
