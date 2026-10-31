# agent-copycheck — PAUSED by Sammy 2026-10-27 (before any check ran)

Question: "Are there articles that say they have saved copies that don't?"

## State at pause
- work/out/copy_claims_check.csv: 10,580 claims listed, ALL marked `not checked` (6,438 sheet File name tokens, 825 File name 2 tokens, 3,317 tracker manifest entries). Library files (part 4) and tracker story-button rows are not listed yet; the script adds them.
- No content checks finished. No writes to the Mac, workbook or artifact.

## What's ready (work/tmp_agent-copycheck/)
- matcher.py: normalise, headline score, stub/error detection.
- analyze.py: full parts 1–3 (sheet tokens: NB batch PDF #item, AJG-P*.pdf, articles/YYYY.json (code), pdf/jg-*.pdf; tracker button simulation that copies getHtml/loadManifest from the published tracker.js; manifest integrity; wrong-article lookup). Written, NOT yet run or debugged. Writes claims_part1.jsonl.
- nbtxt/: pdftotext of all 329 NewsBank batch PDFs + AJG-P0001/2 (pages split by \f).
- mac_pdfs.tsv (staged list; matches the Mac list byte for byte by md5), mac_tracker_pdfs.tsv, pub_files.txt (published articles + pdf/ files).
- libscan.py: Desktop library scanner, already run ON THE MAC. Output is in the device VM at ~/mnt/outputs/cc_lib.jsonl (3,504 records). That folder can't be staged, so it may be gone next session. To resume, run the matching on the device (openpyxl 3.1.5 is there; read "AJG Coverage - NewsBank.xlsx" read-only) and print only the compact results.

## Facts already seen
- Sheet: Saved Copy? = Yes on 6,436 rows, all of which have a File name. Token types: 3,982 NewsBank batch "X.pdf #N", 3,273 articles/YYYY.json (jg-code), 6 pdf/jg-*.pdf, 2 AJG-P000N.pdf.
- All 329 named NewsBank batch PDFs plus AJG-P0001/2 exist in Documents/Gabriel press PDFs. The 6 pdf/jg-*.pdf exist in the published tracker and in Documents/Gabriel press PDFs/Tracker library/ (not in Desktop/Tracker library).
- Published tracker files = local work/artifact_files (sizes identical); build/pub/index.html = published index (7,764,506 bytes). It is the pre-FIX v1 data (4,296 stories).
- Something to test in the tracker: getHtml looks up shard[r.code || sid] in the year file of the FIRST manifest code that maps to the story. Stories with no code of their own (NewsBank-led) but a reprint's code in the manifest could show a "Saved copy" button that opens nothing. analyze.py records these as `missing`.

## To resume
1. python3 -I work/tmp_agent-copycheck/analyze.py and fix any errors.
2. Run the library matching on the device (part 4).
3. Merge into out/copy_claims_check.csv (replace the `not checked` rows) and write the summary.
