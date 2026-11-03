#!/usr/bin/env bash
# PROQUESTPDF-v1: every ProQuest test, in order. Needs node + playwright (chromium), python3 with pypdf, reportlab, openpyxl.
#   bash work/localapp/station/tests/pq/run_all.sh FOR_UPDATE.json [SCRATCH]
set -euo pipefail
FU="$1"; S="${2:-$(mktemp -d)}"; R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; ST="$R/work/localapp/station"
python3 -I "$ST/build_station.py" >/dev/null
python3 -I "$ST/tests/pq/make_pq_pdfs.py" "$S/pdfs" "$FU" >/dev/null
python3 -I "$ST/tools/build_pq_aliases.py" --workbook "$R/data/AJG Coverage - NewsBank.xlsx" --check
node "$ST/tests/pq/alias_test.mjs" 2>&1 | grep -E "^(FAIL|all|[0-9]+ FAILED)"
node "$ST/tests/pq/parse_test.mjs" "$S/pdfs" 2>&1 | grep -E "^(FAIL|all|[0-9]+ FAILED)"
node "$ST/tests/proquest_test.js" --page "$ST/dist/index.html" --file "$FU" --pdfs "$S/pdfs" --out "$S/out" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
python3 -I "$ST/tests/pq/verify_pq_zip.py" "$S/out/pq_update.zip" "$S/scratch" "$FU" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
node "$ST/tests/proquest_real_test.js" --page "$ST/dist/index.html" --file "$FU" --out "$S/real" | grep -E "^(FAIL|SKIPPED|all|[0-9]+ FAILED)"   # skipped unless AJG_REAL_PQ names the real PDF (licensed text: never in the repository)
node "$ST/tests/proquest_evil_test.js" --page "$ST/dist/index.html" --file "$FU" --pdfs "$S/pdfs" --out "$S/evil" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
python3 -I "$ST/tests/pq/verify_pq_zip.py" --evil "$S/pdfs" "$S/evil" "$S/scratch2" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
(cd "$R/work/localapp/updatefolder" && python3 -I -m unittest discover -s tests -t . -p "test_pqpdf.py" 2>&1 | tail -3)
python3 -I "$R/work/localapp/newsbank_pc/tests/e2e_pq_sheet_task.py" "$S/out/pq_update.zip" "$R/data/AJG Coverage - NewsBank.xlsx" "$S/e2e" | grep -E "^(FAIL|all|[0-9]+ FAILED)"
