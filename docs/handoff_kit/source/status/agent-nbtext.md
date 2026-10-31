# agent-nbtext (T10) — DONE 2026-10-27 (relaunch, agent-nbtext2)
- Staged all 329 NewsBank batch PDFs + Companion fresh (read-only on Mac). Extracted with pdftotext here.
- Script: lib/code/extract_nb.py (rerunnable). 6,559 items parsed (1 unparsed); 2,149 print-page items (no text); 419 items = exactly the Companion "Removed" tab (wrong Jesse Gabriel) — none unmatched otherwise.
- Output: lib/work/texts/nb/<Article ID>.json for 3,987 rows (Web + Print rows keep the web text); index lib/work/texts/nb_index.csv.
  Fields: aid, sid, link_col, pdf, pos, headline, source, date_line, author, section, page, edition, words, date, language_detected, mentions_gabriel, mentions_jesse_gabriel, gabriel_sentences, bills_mentioned (from gabriel_bills.json, with sessions), text (body only, paragraphs kept, untruncated), citation, docref.
- Coverage: all 3,780 NewsBank rows with an article link have text; NewsBank Originals 1,750 of 1,751 (the other is print-only, no article link).
- Gabriel: 3,753 texts mention "Gabriel" (3,743 "Jesse Gabriel"); 27 don't at all (21 of them Originals) → lib/work/texts/nb_no_gabriel.csv. Note: La Opinión bylines "Gabriel Lerner" — author field, not counted.
- Fill candidates (not written): author where sheet blank 418 (only 31 are people → lib/work/texts/nb_author_fills.csv, proposed column); word count 30; section 28; page 233.
- Language mismatches vs sheet (texts >300 chars): 14 → lib/work/texts/nb_language_mismatch.csv (mostly sheet "Spanish" on English text).
- 1,319 texts name a Gabriel bill.
