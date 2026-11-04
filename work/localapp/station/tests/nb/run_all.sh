#!/usr/bin/env bash
# NEWSBANKPDF-v1: every NewsBank test, in order. Needs node + playwright (chromium), python3 with pypdf, reportlab, pypdfium2-free.
#   bash work/localapp/station/tests/nb/run_all.sh FOR_UPDATE.json [SCRATCH]
set -euo pipefail
FU="$1"; S="${2:-$(mktemp -d)}"; R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; ST="$R/work/localapp/station"
python3 -I "$ST/build_station.py" >/dev/null
python3 -I "$ST/tests/nb/make_nb_pdfs.py" "$S/pdfs"
node "$ST/tests/prjudge_test.js" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
node "$ST/tests/nbtv_test.js" | grep -E "^(FAIL|all|[0-9]+ FAILED)"   # NBTV-v1
node "$ST/tests/nb/parse_test.mjs" "$S/pdfs" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
node "$ST/tests/newsbank_test.js" --page "$ST/dist/index.html" --file "$FU" --pdfs "$S/pdfs" --out "$S/out" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
python3 -I "$ST/tests/nb/verify_nb_zip.py" "$S/out/nb_update.zip" "$S/scratch" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
(cd "$R/work/localapp/updatefolder" && python3 -I -m unittest discover -s tests -t . -p "test_nbpdf.py" 2>&1 | tail -3)
(cd "$R/work/localapp/newsbank_pc" && python3 -I -m unittest discover -s tests -t . 2>&1 | tail -3)
python3 -I "$R/work/localapp/newsbank_pc/tests/e2e_sheet_task.py" "$S/out/nb_update.zip" "$R/data/AJG Coverage - NewsBank.xlsx" "$S/e2e" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
# the two REAL batches (licensed text, scratchpad only): skipped unless the folders are named
#   AJG_REAL_NB=DIR with multi.pdf + for_update.json;  AJG_REAL_NB2=DIR with multi3.pdf + for_update_snapshot.json + for_update_0bccc1fc.json
node "$ST/tests/newsbank_real_test.js" --page "$ST/dist/index.html" | grep -E "^(FAIL|SKIP|all|[0-9]+ FAILED)"
node "$ST/tests/newsbank_real2_test.js" --page "$ST/dist/index.html" | grep -E "^(FAIL|SKIP|all|[0-9]+ FAILED)"
node "$ST/tests/newsbank_tv_real_test.js" | grep -E "^(FAIL|SKIP|all|[0-9]+ FAILED)"   # NBTV-v1: the real CNN transcript (AJG_REAL_NB2)
node "$ST/tests/newsbank_print_test.js" | grep -E "^(FAIL|SKIP|all|[0-9]+ FAILED)"   # PRINTPAGES-v1: the two real print pages (AJG_REAL_NB2)
node "$ST/tests/print_known_test.js" | grep -E "^(FAIL|SKIP|all|[0-9]+ FAILED)"   # PRINTPAGES-v1: print-tab rows and files column in the for-Update file
