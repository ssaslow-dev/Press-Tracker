#!/bin/bash
# TABS-v1 test page (agent-tabs; moved from build/tabs/test to build/tests/tabs by agent-backendclean2, 2026-10-28): the page shell
# (build/shell/index.html) re-assembled with the current tracker JS (concatenated from code/tracker/), the Insights views, every
# production tab module in build/tabs/ and the tab blocks built from the workbook.
# Output: build/tests/tabs/srv/index.html (+ srv/blocks/*.json for independent checks, srv/articles/manifest.json stub).
# Rerun after changing code/tracker/*.js, a module in build/tabs/ or a *_data.py.  Env: XLSX, BASE (page shell), BLOCKS (fixture blocks).
set -e
L=$(cd "$(dirname "$0")/../../.." && pwd)
T=$L/build/tests/tabs; W=$L/work/tests_out/tabs/testpage; mkdir -p $W/blocks $T/srv/blocks $T/srv/articles $T/blocks
BASE=${BASE:-$L/build/shell/index.html}; BLOCKS=${BLOCKS:-$L/build/shell/blocks}; XLSX=${XLSX:-$L/work/coverage_current.xlsx}
python3 -I $L/code/apply_all_patches.py --tracker-js $W/tracker.js >/dev/null
rm -f $W/blocks/*; cp $BLOCKS/*.json $W/blocks/
export RELRELATED_JSON=${RELRELATED_JSON:-$L/code/release_related.json}   # v20-final: tab-releases "rel" (RELRELATED-v1)
python3 -I $L/code/tabs_data.py "$XLSX" $W/blocks $L/build/tabs
cp $W/blocks/tab_*.json $T/blocks/ 2>/dev/null || true
INS_DIR=$L/build/insights python3 -I $L/code/assemble.py $BASE $W/blocks $W/tracker.js $W/page.html >/dev/null
python3 -I $L/code/tabs_assemble.py $W/page.html $L/build/tabs $W/blocks $T/srv/index.html
for f in data rows billsinfo covcols ins_release_pickup ins_bill_timeline ins_story_travel; do cp $W/blocks/$f.json $T/srv/blocks/; done
cp $W/blocks/tab_*.json $T/srv/blocks/
cp $BASE $T/srv/v18.html
# the framework page: the same build with only the stub module (build/tests/tabs/stub.js) assembled in
rm -rf $W/stubdir; mkdir -p $W/stubdir; cp $T/stub.js $W/stubdir/stub.js
python3 -I $L/code/tabs_assemble.py $W/page.html $W/stubdir $W/blocks $T/srv/stub.html >/dev/null
[ -f $T/srv/articles/manifest.json ] || echo '{"articles":{}}' > $T/srv/articles/manifest.json
echo "test page: $T/srv/index.html"
