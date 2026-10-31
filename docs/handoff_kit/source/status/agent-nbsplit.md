# agent-nbsplit (T25) — DONE 2026-10-27

## What was done
- Read README/DECISIONS/CONTRACT/BOARD and status/agent-nbtext.md (nbtext2's log; there is no separate agent-nbtext2.md). nbtext2 recorded item positions (pdf, pos) but no page ranges, so ranges were derived here with the same "Citation (apa Style)" splitter on per-page pdftotext output (work/tmp_agent-nbsplit/pages.py -> items_pages.json).
- Source: the 329 batch PDFs already staged at /mnt/user-data/uploads/Gabriel press PDFs. Mac check: 329 files, none modified since 2026-10-27 00:00, so the staged copies are current. Nothing written to the Mac or the Desktop library.
- Split with qpdf in the container (work/tmp_agent-nbsplit/split.py). Note: every batch PDF has a junk "content-type missing in HTTP POST…" line before %PDF; qpdf writes clean output.
- Row -> item mapping: docref of NewsBank article link / print article link / print-page link, and where a docref sits in two PDFs (the duplicate pair (90)/(92), 20 docrefs) the item named in the sheet's File name column wins. File name never names an item outside the docref matches.

## Outputs
- work/nb_split/<old aid>.pdf: 5,574 files
  - article 3,780 (Article ID, NewsBank article link item)
  - print_article 202 (Print Article ID on Web + Print rows)
  - print_page 1,592 (1,471 blank "Original or reprint" rows + 121 Print rows that have only a print-page item)
- work/nb_split/print_pages/<old aid>.pdf: 541 print-page header items belonging to Print rows that ALSO have an article item (kept separate so the article PDF holds only the article; agent-librename/Sammy decide whether to keep them).
- work/nb_split_index.csv (6,115 rows): old_aid, sid, kind, source_pdf, pos, pages, npages, out_path (relative to lib), bytes, shared_page_flag, alt_items (other PDF copy of the same docref), sheet_headline, pdf_first_line.
- work/nb_split_missing.csv: 15 Print Article IDs on Web + Print rows with no print article link, so no item to split.
- Total 292 MB (fonts repeat in every file).

## Facts found
- No page is shared between two items: every item starts on a fresh page. shared_page_flag is therefore empty everywhere (also no item maps to two rows).
- 227 pages are blank browser filler pages between items (verified blank by rendering) and are left out.
- 444 items not split: 420 articles with no Coverage row (the Companion "Removed" wrong-Jesse-Gabriel items + 1 unparsed), 20 duplicate copies in (90)/(92), 4 print pages with no Coverage row.

## Self-check
- Pages: 14,142 total = 12,177 in splits + 1,738 in unsplit items + 227 blank; holds for each of the 329 PDFs. Every output's page count equals its recorded range (6,115/6,115).
- vs nbtext2 mapping: same items, except 8 aids in the (90)/(92) duplicate pair where nbtext2 took (92) and the split takes (90), the copy named in File name. Content is identical.
- Headlines: all 3,982 text splits match the sheet headline on page 1 (first line vs Headline / Print headline). Random 10 + 3 print pages opened with pdftotext: 13/13 OK; one rendered visually (nb-03926) and it looks right.
