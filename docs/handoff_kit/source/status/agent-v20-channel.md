# agent-v20-channel (2026-10-28)
- NOSHOWCHAN-v1 code was already in code/avtab.py, code/sheet_task.py, code/tracker/53_tabs.js (av_no_channel review list retired; panel omits blank Channel; guard_show in show_of/extract/apply_av). Verified.
- avtab.py refinements: _STATION_NAME accepts AM dials up to 4 digits ("KNX 1070"); _PROGRAM_WORDS (morning/evening/nightly/noon/report/...) so an Outlet equal to a station-prefixed program ("KTLA 5 Morning News") keeps its Show. Backup work/tmp_agent-v20-channel/avtab.py.bak.
- Tests: 15 new checks in build/tests/sheet_task/test_sheet_task.py (7 channel->Channel moves, 7 programs kept, show_of, sheet_task source). test_sheet_task 50/50, test_auto 35/35.
- Recheck (work/tmp_agent-v20-channel/recheck.py) on master 4d7fb37c…ebf24a (Mac sha verified = work/coverage_current.xlsx): 1,030 AV rows, 70 Show values, 0 to move -> no sheet write, no DECISIONS line.
- apply_all run (pipeline avtab.py refreshed). work/CHANNEL_DONE written.
