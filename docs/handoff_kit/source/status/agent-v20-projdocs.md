# agent-v20-projdocs (2026-10-28)
- Handoff check (work/tmp_agent-buttonopt2/handoff.md item 1): DECISIONS L216 BUTTONOPT-v1 and CONTRACT L53 (run fields `_page`/`_origin`, edits `reported`, result keys, sheet_task flags) already present. `av_no_channel` intentionally absent: retired by NOSHOWCHAN-v1 (DECISIONS L218), CONTRACT carries `av_show_to_channel` instead. Nothing added.
- Mac _docs refresh method (README §4; status agent-insights/reorg/v19finish): stage README/DECISIONS/CONTRACT/TONE_GUIDE/clean_playbook to /mnt/user-data/outputs/vNNdocs, commit to ~/Desktop/Tracker library/_docs/, sha-verify on the Mac. This round adds BOARD.md and mv-archives the old copies to Tracker library/_archive/.
- Preliminary staging: /mnt/user-data/outputs/v20docs/ (re-copied after BUILD_DONE + 10 min).
- 06:45Z BUILD_DONE seen; waited to 06:55Z: no late appends (DECISIONS 218 lines, last write 06:13Z). README/DECISIONS/CONTRACT/TONE_GUIDE/clean_playbook = build/pub/pipeline/docs (byte-equal).
- BOARD.md: appended one v20 line (build done, not yet published; docs pushed). Nothing else edited.
- Mac: old _docs copies (5; no BOARD there before) mv'd to Tracker library/_archive/_docs_pre_v20_2026-10-28/; 6 new copies committed to Tracker library/_docs/ (staged /mnt/user-data/outputs/v20docs, SHA256SUMS.txt); Mac sha256 6/6 equal. _docs/archive/ untouched.
- Project doc texts: work/tmp_agent-v20-final/projdocs/{README,CONTRACT,DECISIONS,BOARD}.md + SHA256SUMS.txt (for project_write by main; I have no Projects tool).
