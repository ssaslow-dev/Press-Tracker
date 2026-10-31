#!/bin/bash
# build/tests/run_all.sh (final-codedesign 2026-10-29; installed + extended by final-int): every unit suite in build/tests against code/, one line each.
# Usage: bash build/tests/run_all.sh   (the TABS harness is separate: build/tests/tabs/build_testpage.sh, then MOD=all node harness.js)
# Mirrors work/tmp_chainorig-fix/run_suites.sh, which lived in scratch; two suites need their own invocation (copies takes the code
# dir as argv[1]; paywall imports its harness from its own folder, so -I cannot be used there).
L=$(cd "$(dirname "$0")/../.." && pwd); T=$L/build/tests; cd "$L" || exit 1; fail=0
# r NAME CMD...: run a suite, one line (rc, seconds, last result lines). s NAME WHY: skip with a notice (not a failure).
# COLDSTART-v1: three suites need inputs that are NOT in the handoff kit (final_pass/ is left out of source/); they are skipped with
# a notice instead of failing. Whole run: about 5 min 15 s on 2026-10-30 (sheet_task 101 s, auto 120 s, coldstart_f1 36 s, the rest under 10 s each; per-suite seconds are printed).
skipped=0
r(){ n=$1; shift; t0=$(date +%s); out=$("$@" 2>&1); rc=$?; [ $rc -ne 0 ] && fail=1
     echo "== $n rc=$rc ($(( $(date +%s) - t0 ))s) :: $(echo "$out" | grep -E 'passed|PASSED|failed|FAIL|OK|Ran |checks|ALL|ok$|^PASS$' | tail -3 | tr '\n' ' ')"; }
s(){ skipped=$((skipped+1)); echo "== $1 SKIPPED :: $2"; }
r sheet_task     python3 -I $T/sheet_task/test_sheet_task.py
r verify_tabs    python3 -I $T/sheet_task/test_verify_tabs.py
r has_work_pages python3 -I $T/sheet_task/test_has_work_pages.py
r updfix         python3 -I $T/sheet_task/test_updfix.py
r nosched        python3 -I $T/sheet_task/test_nosched.py
if [ -f $L/final_pass/F1/final.xlsx ] && [ -d $L/final_pass/F4/build/copies_final ]; then r auto python3 -I $T/sheet_task/test_auto.py
else s auto "needs final_pass/F1/final.xlsx and final_pass/F4/build/copies_final (final_pass/ is not in the kit)"; fi
r removal_links  python3 -I $T/sheet_task/test_removal_links.py
r print_tab      python3 -I $T/sheet_task/test_print_tab.py
r nocopy_owned   python3 -I $T/sheet_task/test_nocopy_owned.py
r relbutton      python3 -I $T/sheet_task/test_relbutton.py
r av_date_rows   python3 -I $T/sheet_task/test_av_date_existing.py
r unverified_hit python3 -I $T/sheet_task/test_unverified_hit.py
r final_int      python3 -I $T/sheet_task/test_final_int.py
r quoted        python3 -I $T/sheet_task/test_quoted.py
r review4_rules python3 -I $T/sheet_task/test_review4_rules.py
r coldstart_f1  python3 -I $T/sheet_task/test_coldstart_f1.py
r leftovers_rules python3 -I $T/sheet_task/test_leftovers_rules.py
r lookup_cache  python3 -I $T/lookup_cache/test_lookup_cache.py
r data_basis_js node $T/update_js/test_data_basis_js.js
r final_int_js   node $T/update_js/test_final_int_js.js
r opeds_js       node $T/update_js/test_opeds_js.js
r reachguard_js node $T/update_js/test_reachguard_js.js
r late_window_js node $T/update_js/test_late_window_js.js
r run_persist_js node $T/update_js/test_run_persist_js.js
r fetch_retry_js node $T/update_js/test_fetch_retry_js.js
r updfix_js      node $T/update_js/test_updfix_js.js
r since_js       node $T/update_js/test_since_js.js
r audit_removed  python3 -I $T/sheet_task/audit/test_removed_tab_ids.py
r audit_dupph    python3 -I $T/sheet_task/audit/test_dup_placeholders.py
r audit_swap     python3 -I $T/sheet_task/audit/test_swap_then_held.py
r audit_retry    python3 -I $T/sheet_task/audit/test_retry_dead_end.py
r audit_avdate   python3 -I $T/sheet_task/audit/test_av_date_verify.py
r reprint        python3 -I $T/reprint/test_reprint_v2.py
r outlets        python3 -I $T/outlets/test_outlets.py
r recall         node $T/recall/test_recall.js
r handoff        python3 -I $T/handoff/test_read_map.py
r dates          python3 -I $T/dates/test_dates.py
r dates_js       node $T/dates/test_dates_js.js
r nb             python3 -I $T/nb/test_extract_nb.py
r copies         python3 -I $T/copies/test_copy_check.py $L/code
# shared_data needs the snapshot work/shared/ (meta.json, tables.pkl, texts.db); the kit does not carry it. Create it from the master copy.
if [ ! -f $L/work/shared/meta.json ] && [ -f $L/work/coverage_current.xlsx ]; then
  echo "== shared_data: no snapshot, building it (python3 -I code/shared_data.py --rebuild)"; python3 -I $L/code/shared_data.py --rebuild >/dev/null 2>&1; fi
if [ -f $L/work/shared/meta.json ]; then r shared_data bash -c "python3 -I $T/shared_data/test_shared_data.py 2>&1 | grep -c ^PASS"
else s shared_data "no work/shared snapshot and it could not be rebuilt (python3 -I code/shared_data.py --rebuild)"; fi
r relmatch       bash -c "cd $T/relmatch && python3 -m unittest test_relmatch test_relmatch_v4 test_relmatch_v23"
if [ -f $L/work/tmp_v23-int/pre/code/authorsplit.py ]; then r reporters python3 -I $T/reporters/test_reporters_v23.py $L
else s reporters "needs work/tmp_v23-int/pre/code/authorsplit.py (the pre-v23 authorsplit, not in the kit)"; fi
r blend          python3 -I $T/rules/test_blend.py
r paywall        bash -c "cd $T/rules && PYTHONPATH=. python3 test_paywall.py"
r chainorig      python3 -I $T/reporters/test_chainorig.py $L
r agg_origin     python3 -I $T/agg_origin/test_agg_origin.py
r agg_origin_js  node $T/agg_origin/test_agg_origin_js.js
r shownet        python3 -I $T/shownet/test_shownet.py
r shownet_js     node $T/shownet/test_shownet_js.js
r media_gate     python3 -I $T/media_gate/test_media_gate.py $L ${MEDIA_SCAN_DIRS_ARGS:-}
echo "== done: fail=$fail skipped=$skipped"
exit $fail
