# Coordinator context for the handoff (written by main, 2026-10-28)
Facts only the coordinator session holds. Treat as authoritative; the repo docs (README, CONTRACT, DECISIONS, BOARD, phaseB_inbox, status/) hold the rest.

## Why a handoff
Sammy is moving jobs and will recreate everything on a NEW Claude account by copying. claude.ai has no artifact-ownership transfer, so the new account will republish its own copy from the handoff kit (new URL). This cloud scratchpad (L) is ephemeral and is NOT reachable from another account. Everything needed must be in the kit.

## Accounts and places (old account)
- Owner: Sammy, ssaslow@berkeley.edu. The work is press coverage of CA Assemblymember Jesse Gabriel (AD46; Assembly Budget Chair; Jewish Caucus chair since 2020-11-18).
- Live tracker artifact: https://claude.ai/code/artifact/27f923dc-2407-40a0-b8a9-ec3dfed87ad9 = https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv, title "AJG Press Coverage Tracker".
  - Current version 1793174282-172b ("v20.1": UI + RELRELATED-v2). Page sha c252e5a1…
  - v20 page 1793170541-a64f; v19 1793153876-e0f4.
  - 138 published files, about 250 MB of the 256 MB per-version cap (storage is nearly full).
  - Declared capabilities: db {}, downloads {}, sample {}, mcp {servers:[{server:"TinyFish",tools:["search","fetch_content"]},{server:"Claude Code Remote",tools:["fire_trigger"]}]}. Runtime contract 0.2.91.
  - Because of the mcp connectors it cannot get an "anyone with the link" share. A public copy was considered and ABANDONED by Sammy. Email invites are possible.
- Review-queue artifact: 8yp4a5q8A8PcrQFdYcXPuB. Item docs such as items/18-origins, 18-origins-3; categories include "origins" and "newoutlet".
- Older artifacts, superseded: "AJG Press Coverage Tracker (Copy)" dc44cdfe-0365-403e-925f-ee998e6700ef / UCat3jW8cViL37pHTTt6JA.
- Scheduled task (claude.ai scheduled task, the Update button's sheet step) trig_01WRLX437wg7VRViGUTKei8R: DISABLED. Its replacement prompt waits for Sammy's approval in work/tmp_agent-buttonopt2/scheduled_prompt.md. The Update button fires it via Claude Code Remote fire_trigger. An older task, trig_01Wg3NS6hNteZq4hwQTRcDay, belonged to the old tracker copy.
- claude.ai Project "AJG Mentions Database" (id 01a1413e-6231-75bd-9079-fa4237b5738f). Docs: library/README.md, CONTRACT.md, DECISIONS.md, BOARD.md, plus the old claude/AJG Project - Handoff Memory.md, which is being replaced by the new handoff.
- Project memory files (copy their content into the handoff, since the new account won't have them):
  - areas/ajg-coverage-workbook.md: "the main sheet" = AJG Coverage - NewsBank.xlsx; since 2026-10-27 the working master is in ~/Desktop/Tracker library/ and the Documents copy is no longer updated.
  - areas/newsbank-print-clipping.md: the NewsBank clipping workflow. Since 2026-10-27, clips go into the Tracker library via CA State Library NewsBank links; save the entire page plus spill-over pages; OCR on. Proxy host infoweb-newsbank-com.castatelib.idm.oclc.org; Sammy logs in himself.
- Sammy's Mac, reached through the Claude desktop app's linked-computer tools (mcp__remote-devices__*: device_bash, device_stage_files, device_commit_files, device_list_dir, request_delete_permission). These tools come and go; the computer must be online with the app open. Deletes need permission, so use mv to _to_delete/ and _archive/.
  - ~/Desktop/Tracker library/: master workbook "AJG Coverage - NewsBank.xlsx", Backups/, the library (year folders, Press releases/<year>/prNNNNN.html + _original_html, _original_pdf, _docs/, _archive/, _to_delete/).
  - ~/Documents/Gabriel press PDFs/: 329 NewsBank batch PDFs, the Companion xlsx (print pages AJG-P####), the old AJG Combined Coverage.xlsx (superseded).
- Master workbook sha now: 4d7fb37cbd111b7f4df018633af3e7d6d42fa0ef5640a1b6d73279c009ebf24a (L/work/coverage_current.xlsx = the same file).
- Connectors used: TinyFish (search, fetch_content, browser automation; costs money per step; deep research $2/run, avoid it). Exa is FORBIDDEN except for the two one-time exceptions already used (podcast + people lookups). Claude in Chrome / built-in browser for logged-in saves (Sammy logs in; never enter credentials).

## Network
Sammy opened the account network allowlist to all domains (2026-10-28), so container image downloads work. The new account needs the same setting for photo fetching.

## How Sammy works (standing rules he stated)
- Lean, direct, precise; dry humor fine; pushes back on overstatement. State limits plainly.
- Leaves many artifact comments: reply in the thread and resolve when shipped; leave open if partial.
- Coordinator mode: delegate to background agents, run them in parallel whenever possible ("always use multiple agents"), keep the chat clear.
- Every change goes to all three: the code base, the Update button (pipeline + sheet task), and the master sheet.
- No checks/tests before all changes are made; run the full suite once at the end. For pure UI changes, no rechecks: build + a quick screenshot.
- Never delete: _to_delete/archive with an undo log; the library is add-only; fill blanks only unless DECISIONS overrides; Excel closed before writes; one workbook writer at a time (token L/work/WORKBOOK_WRITER.txt); README rule 7 for every write.
- Don't work around blocks or paywalls; don't log in for him.
- Publish only to the live tracker; no preview unless he asks.
- Instruction tabs: "fill gaps only, never rewrite an existing process with them".
- Ordering: optimizations (buttonopt) go LAST so later changes don't undo them.
- Fix whole classes ("throughout") rather than the one instance commented on.

## Decisions made late on 2026-10-28 (also in DECISIONS.md)
- AV: Channel vs Show split (AVSHOW-v1). A blank Channel stays blank (no review flag). A channel/station/network name is never recorded as Show (NOSHOWCHAN-v1). The public-fact networks TODAY→NBC, GMA→ABC, As It Happens→CBC Radio are kept.
- Release related stories RELRELATED-v1, then v2: the 90-day text window is kept; stories up to 14 days BEFORE a release count when they cover the same announcement (anchor name + figure/partner/bill).
- Brentwood thepress.net rows = "Press, The" (Brentwood, Contra Costa). 09772 date 2025-10-08. 07430 = Reprint of s02212.
- Reprint Author titles: generic staff titles on other-outlet reprints are blanked (10 rows). 07066 "Staff (ABC10)" kept.
- UI v20.1:
  - "Copy link to this page" removed everywhere.
  - Group subtitles (Who/What/Coverage) removed on Reporters AND Bills. Bills was removed by coordinator mistake; Sammy hasn't answered whether to keep that or revert it.
  - Tone number muted; masthead reorganized; release lower card dividers.

## Open with Sammy at handoff time
1. Press-release mapping recommendations (4 reviewer proposals, work/tmp_relaudit_1..4/proposal.md, synthesized in chat). None approved yet:
   - quick wins: reverse links from stories, bill, reporter and outlet pages; use English translations; sibling releases + milestone labels; PublicNow reposts as copies (overrides DECISIONS 133, needs OK); a Related count column
   - medium: tracker stories that reprint releases count as pickups; bill named in text but not tagged; "later coverage of the bill" section; later quotes
   - needs a decision: other organizations' releases; a District/community Issue label
2. Bills group subtitles: keep removed or revert? And Outlets/Press releases?
3. Table-corner thread 9eb75f10 still open: couldn't reproduce in Chromium; asked Sammy for his browser and width.
4. Comment thread de9c2baa (stray "· ·" separator) and d38d2b91 (bill chips in the release list rows) are open, queued v21.
5. Scheduled task stays disabled until he approves the replacement prompt.
6. The Sepulveda coverage search (pr00244 had no coverage in the sheet) was stopped by Sammy and not resumed. Root issue: the Update button never searches for coverage/reprints of a specific new release. A proposed button step: a per-release coverage + republication search.
7. v21 queue: L/build/phaseB_inbox.md, the "## v21 queue" section and later lines.
8. Storage: about 250/256 MB. Repack/trim the old img shards before the next big update.
