REQ-5 done: plan total 702 (default) / 703 (7d) / 731 (60d); outlets deep 614, fresh 51, reprint 5; floor 24.6 min serialised (agree); deep paging worst case +5,526 searches
REQ-1 done: 1-line patch + source test; test fails unpatched, 8/8 patched
REQ-2 done: patch + 3-scenario playwright test pass (fails 7/14 on unpatched); full run_all fail=0 (2 skips = inputs not copied); heartbeat race with provisional doc guarded (RA.hbOff)
REQ-3 done: verify_tabs patch + test 8/8; master self-check 1.9 s no false positives; Bills keyed on first four columns (deviation)
REQ-4 done: round trip PASS, nothing lost (load 8.9 s, save 5.2 s); no CF/DV/images/charts/merges exist in master
REQ-6 done: retry+own reason patch; 12/12 patched, 8 fail unpatched (bug reproduced); note retryable errors never reach this path
REQ-8 done: rehearse.sh runs prompt steps 1/3/6 in 86 s, all exit 0, verify.ok true, next.aid 10653 = highest 10649 + 3 + 1; no prompt/flag mismatch
REQ-7 done: has_work counts only referenced pages docs, pages_orphan reported; 10/10 patched, unpatched fails; suites still pass
