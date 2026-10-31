# rp-button handoffs (files I don't own)
1. code/apply_all_patches.py (coordinator / rp-final): PIPELINE += 'relcopy.py': 'code/relcopy.py' (sheet_task.py imports it; the prompt's pipeline list names it). py_compile list too.
2. build/insights/release_pickup_data.py (rp-copies' file, done): `official.known` should also carry the tab's "Also on caucus site (URL)" values (backend review #6). 41_update_search.js relKnown() reads `known` and also a block key `also` if you prefer a separate list. Without it a dual-posted caucus URL is re-found each run (harmless: the sheet task merges/skips it, the page skips fetching it via dup_of).
3. Final build: run build/tests/sheet_task/test_relbutton.py with the other sheet_task suites.
