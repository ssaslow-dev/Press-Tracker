#!/bin/bash
# Canonical tracker build (from work/tmp_agent-v19finish/build.sh, agent-backendclean2 2026-10-28).
#   build/build.sh --kit [--no-test|--no-zip|--part-mb N] -> handoff kit into handoff_kit/ (after every publish)
#   build/build.sh                 -> LIB build + PIPELINE-ONLY build into $OUT, prints the two index.html sha256s and
#                                     a per-block comparison (every blocks/*.json of the lib build vs the pipeline build)
# LIB      = code/build_data.py + code/assemble.py with build/js_merged.js (written by code/apply_all_patches.py from code/tracker/)
# PIPELINE = build/pub/pipeline copied to a scratch folder and run exactly as sheet-task step 6
# Env: XLSX (default work/coverage_current.xlsx), BASE (page shell, default build/shell/index.html), OUT (default work/build_last)
set -e
L=$(cd "$(dirname "$0")/.." && pwd)
# --kit: regenerate the handoff kit (code/make_handoff_kit.py build; README "Handoff kit"); extra args pass through
if [ "$1" = "--kit" ]; then shift; exec python3 -I "$L/code/make_handoff_kit.py" build "$@"; fi
# REPO-LOCAL defaults (this repository has no work/coverage_current.xlsx, build/shell/index.html or work/index_original.html):
#   XLSX falls back to the data/ snapshot, BASE to build/shell/shell.html, LEGACY (the old page, OLD_INDEX for build_data) to
#   work/index_original.html or build/pub/pipeline/legacy_index.html. The old page holds translated story text, so it is not in
#   the repository: copy the live tracker's pipeline/legacy_index.html to build/pub/pipeline/ (git-ignored) or set LEGACY=FILE.
XLSX=${XLSX:-$L/work/coverage_current.xlsx}; [ -f "$XLSX" ] || XLSX="$L/data/AJG Coverage - NewsBank.xlsx"
BASE=${BASE:-$L/build/shell/index.html}; [ -f "$BASE" ] || BASE=$L/build/shell/shell.html
OUT=${OUT:-$L/work/build_last}
LEGACY=${LEGACY:-$L/work/index_original.html}; [ -f "$LEGACY" ] || LEGACY=$L/build/pub/pipeline/legacy_index.html
SIDMAP=$L/work/sid_map.json; [ -f "$SIDMAP" ] || SIDMAP=$L/code/sid_map.json
[ -f "$LEGACY" ] || { echo "build.sh: old page not found (set LEGACY=FILE or put the live tracker's pipeline/legacy_index.html at build/pub/pipeline/legacy_index.html)" >&2; exit 2; }
rm -rf "$OUT"; mkdir -p "$OUT/lib/blocks" "$OUT/pipe" "$OUT/pipeblocks"
# LIB
(cd "$L" && python3 -I code/build_data.py "$XLSX" "$LEGACY" "$OUT/lib/blocks" "$SIDMAP" > "$OUT/lib/build_data.log" 2>&1)
(cd "$L" && python3 -I code/assemble.py "$BASE" "$OUT/lib/blocks" build/js_merged.js "$OUT/lib/index.html" > "$OUT/lib/assemble.log" 2>&1)
# PIPELINE ONLY
cp -r "$L/build/pub/pipeline/." "$OUT/pipe/"; find "$OUT/pipe" -name __pycache__ -prune -exec rm -rf {} +
cp "$XLSX" "$OUT/committed.xlsx"; cp "$BASE" "$OUT/index_current.html"; cp "$LEGACY" "$OUT/pipe/legacy_index.html"
(cd "$OUT/pipe" && python3 -I build_data.py ../committed.xlsx legacy_index.html ../pipeblocks sid_map.json > ../pipe_build_data.log 2>&1)
# step 6 assembles from pipeline/shell.html (BUTTONOPT T4b); PIPE_BASE overrides (e.g. ../index_current.html)
(cd "$OUT/pipe" && python3 -I assemble.py "${PIPE_BASE:-shell.html}" ../pipeblocks tracker.js ../pipe_index.html > ../pipe_assemble.log 2>&1)
sha256sum "$OUT/lib/index.html" "$OUT/pipe_index.html"
n=0; d=0; for f in "$OUT"/lib/blocks/*.json; do n=$((n+1)); cmp -s "$f" "$OUT/pipeblocks/$(basename "$f")" || { d=$((d+1)); echo "block differs: $(basename "$f")"; }; done
echo "blocks: $n, differing lib vs pipeline: $d"
