#!/bin/sh
# PREVIEW-v1, one command: workbook in, finished preview file out. About 1.5 minutes.
#   AJG_SCRATCH=<scratch folder> sh work/localapp/preview/make_final.sh WORKBOOK.xlsx [OUT.html] [--no-internal]
# Needs, in $AJG_SCRATCH: live_pipeline/pipeline/legacy_index.html and live_site/ (the same inputs the PC build used).
# Work files go to $AJG_SCRATCH/prev_work (deleted at the end unless KEEP=1). The output holds workbook data: keep it out of the repository.
set -e
WB="$1"; [ -f "$WB" ] || { echo "usage: make_final.sh WORKBOOK.xlsx [OUT.html] [--no-internal]"; exit 2; }
S="${AJG_SCRATCH:?set AJG_SCRATCH}"
OUT="${2:-$S/AJG_Tracker_preview_final.html}"; EXTRA="$3"
H="$(cd "$(dirname "$0")" && pwd)"; LA="$H/.."
W="$S/prev_work"; rm -rf "$W"; mkdir -p "$W"
python3 -I "$LA/build/build_tracker.py" --out "$W/pb" --legacy "$S/live_pipeline/pipeline/legacy_index.html" --live-site "$S/live_site" --xlsx "$WB" > "$W/build.log" 2>&1 || { tail -20 "$W/build.log"; exit 1; }
python3 -I "$H/prep_page.py" "$W/pb" "$W/site"
python3 -I "$H/make_preview.py" --page "$W/site/index.html" --workbook "$WB" --out "$OUT" $EXTRA
[ -n "$KEEP" ] || rm -rf "$W"
echo "done: $OUT"
