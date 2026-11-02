#!/usr/bin/env bash
# NEWSBANKPDF-v1: every NewsBank test, in order. Needs node + playwright (chromium), python3 with pypdf, reportlab, pypdfium2-free.
#   bash work/localapp/station/tests/nb/run_all.sh FOR_UPDATE.json [SCRATCH]
set -euo pipefail
FU="$1"; S="${2:-$(mktemp -d)}"; R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; ST="$R/work/localapp/station"
python3 -I "$ST/build_station.py" >/dev/null
python3 -I "$ST/tests/nb/make_nb_pdfs.py" "$S/pdfs"
node "$ST/tests/nb/parse_test.mjs" "$S/pdfs" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
node "$ST/tests/newsbank_test.js" --page "$ST/dist/index.html" --file "$FU" --pdfs "$S/pdfs" --out "$S/out" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
python3 -I "$ST/tests/nb/verify_nb_zip.py" "$S/out/nb_update.zip" "$S/scratch" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
(cd "$R/work/localapp/updatefolder" && python3 -I -m unittest discover -s tests -t . -p "test_nbpdf.py" 2>&1 | tail -3)
(cd "$R/work/localapp/newsbank_pc" && python3 -I -m unittest discover -s tests -t . 2>&1 | tail -3)
python3 -I "$R/work/localapp/newsbank_pc/tests/e2e_sheet_task.py" "$S/out/nb_update.zip" "$R/data/AJG Coverage - NewsBank.xlsx" "$S/e2e" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
