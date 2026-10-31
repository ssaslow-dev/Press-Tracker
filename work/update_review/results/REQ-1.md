# REQ-1 Reprint headline searches lose the late-pickup window

Patch: `patches/REQ-1_late_window.patch` (one line, `code/tracker/41_update_search.js` line 649: `after_date: it.minDate && it.minDate < U.since ? it.minDate : U.since`; the rest of the line is unchanged, `/* LATEWINDOW-v1 */` marker added).
Test: `patches/tests/test_late_window_js.js` (source-line test; honours `L_ROOT` env var, default the tree it sits in).

Ran (patched copy and unpatched copy in /tmp/pd1, each with code/tracker/41_update_search.js and build/tests/update_js/ test):
- `node /tmp/pd1/b/build/tests/update_js/test_late_window_js.js` (patched) -> ALL 8 CHECKS PASSED (`REQ-1/test_patched.log`).
- same test on unpatched 41 -> FAIL at the first check "minDate before since -> after_date = minDate" (`REQ-1/test_unpatched.log`), so the test discriminates.
Checks: minDate 2026-10-01 with since 2026-10-20 -> 2026-10-01; no minDate -> since; minDate 2026-10-25 -> since; an explicit item `after_date` (release pickups) still overrides; location/purpose unchanged; reprint plan line still `Object.assign({ minDate: r.date }, RC_LONGTAIL...)`; `delete inp.minDate` still strips it before the call.
Patch applies cleanly with `patch -p1` from a copy of L; REQ-2's patch also edits the adjacent line `let next = 0, done = 0;` (line 646) of the same file, but a different line, so both apply (apply REQ-1 first or use patch's fuzz; hunks are separated by 2 lines of context).
Side effect to know: the downstream filter `c.published < (it.minDate || U.since)` already used minDate, so after this fix results in the window now actually arrive; expect more reprint candidates (up to RC_LATE_DAYS = 21 days before since) per run, all passing through the same known-link / reprint dedupe.
