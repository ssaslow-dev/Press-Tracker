# T43 — fetch reprint-list links (half <H>)

You are agent-reprintfetch-<H> on Sammy's AJG press-coverage project. L = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib.
Read README.md, DECISIONS.md (newest entries — esp. the T43 entry, TinyFish/Desktop library rules, BLOCKED/RETRY placeholders, Gabriel incl. non-Latin forms, "San Gabriel" not a mention, skip californiafiles.org, skip pages where Gabriel is only outside the article), build/clean_playbook.md, status/agent-code.md (how to call code/clean_html.py). Log in L/status/agent-reprintfetch-<H>.md; helpers in L/work/tmp_agent-reprintfetch-<H>/. Never write the workbook; never overwrite or delete library files; no Exa; don't work around blocks/paywalls.

Targets: rows of L/work/final/reprint_fetch_targets.csv with half = <H> (~233). Another agent does the other half at the same time — TinyFish is shared: keep to ≤12 fetches/min.

For each row:
1. Skip hosts documented as blocked (see status/agent-fetch-rated-1b.md, agent-authors.md, work/final/blocked_marks.csv) → result blocked-known (no fetch).
2. Fetch the Publisher link with mcp__TinyFish__fetch_content (load via ToolSearch). Blocked/403/paywall/login → blocked.
3. Accept only if it is this outlet's copy of the story: headline matches the row's Headline (allow small variants), Gabriel is named in the article text (any script), the body is complete. Yahoo/AOL/MSN syndication pages count when they carry the story itself.
4. Clean with code/clean_html.py (find mode, sheet row passed in) — same safety checks. Then save add-only on the Mac (device_bash or device_commit_files): cleaned page to `$HOME/mnt/Tracker library/<year>/<old aid>.html`, the raw fetched page to `$HOME/mnt/Tracker library/_original_html/<year>/<old aid>.html`; skip if a file already exists; Mac scratch only in $HOME/mnt/outputs. Append to L/work/library_adds.csv. Also copy the cleaned page to L/work/html_clean/<year>/<old aid>.html (the regroup reads it).
5. Record in L/work/final/reprint_fetch_results_<H>.csv: aid, sid, url, result (saved | blocked | blocked-known | wrong-page | no-gabriel | incomplete | error), placeholder (blank for saved; `BLOCKED – TinyFish` for blocked/blocked-known; `RETRY – TinyFish` otherwise), library_file, words, byline_found (byline from the page, if any — reuse for the author columns), note.

Self-check: render 5 saved pages in Playwright; sha-check 10 Mac files against the container copies. Short final report: counts by result and by host.
