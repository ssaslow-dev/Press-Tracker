# agent-rp-threads (2026-10-28)
Row: build/RELPLAN.md rp-threads. Scope change from coordinator mid-task: other organizations' releases dropped entirely (not built).
Files: NEW code/relthread.py; build/tabs/releases_data.py (+ _threads(), `thr` key; backup work/tmp_rp-threads/releases_data.py.before);
build/relplan_contract.md (created; section "rp-threads"); DECISIONS.md (1 line); HANDOFF.md (3.3 RELTHREAD, 4.1, changelog).
Tests: work/tmp_rp-threads/test_relthread.py: 26 checks pass (synthetic + current data: AB 2204 thread, AB 469→AB 468, pr00091
inherits ACR 51, AB 418 background in 2024/25, milestone labels pr00139/pr00122, suspense file excluded, pr00187 joint,
pr00080/81 follow-up, food/guns run-only pair dropped, 41 people ≥ 3). Deterministic; pipeline layout gives identical thr.
Hand checks: all 47 threads read (work/tmp_rp-threads/threads.txt), all 38 pairs, 16 random milestone labels, all 19 Joint with.
Calibration changes after hand check: run-only pairs need cosine ≥ 0.20 or ≥ 40 words (dropped caucus-intro boilerplate pairs);
clerical milestones excluded; identical-member threads merged; Joint with uses the lead subject (caught comma lists, dropped
"Newsom vetoed … Gabriel"). Known misses: caucus leadership releases ("caucus elected Wiener and Gabriel") get no Joint with.
Size: thr 25,290 B; tab-releases 151,667 B (was 126,377 B). No sheet write. No build.sh, no harness.
Handoff to main: work/tmp_rp-threads/handoff.md (apply_all PIPELINE entry; CAP note).
