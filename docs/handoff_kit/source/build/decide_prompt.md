# Auto-decide review-queue items (Sammy 2026-10-27: "go through these decisions and figure out what to do for most of them, use the internet if needed")

L = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib. Read README.md, DECISIONS.md (ALL), BOARD.md, status/agent-autodecide.md (how earlier auto-decisions were stored). Log in L/status/<your agent name>.md; helpers in L/work/tmp_<your agent name>/.
Queue: https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB (ArtifactData via ToolSearch "select:ArtifactData"). Collection `items` (docs per tab, {"list":[...]}), collection `decisions` (one doc per item id: {choice, note, at, by}). Sammy approved writing decisions for the items you decide.

Rules:
- Decide ONLY your assigned tabs. Write a decision doc per decided item: choice = one of the item's options (or a list when "multi": true), note = 1–2 sentences of evidence (with a source URL when you used the web), at = ISO time, by = "Claude (auto)". Never overwrite an existing decision doc. Never edit `items` docs.
- Decide when the evidence is clear; leave genuinely uncertain items undecided and list them (with why) in your status file. Aim to decide most.
- Web: WebSearch / WebFetch or TinyFish (search/fetch_content, ≤15/min) are allowed; NEVER Exa. Don't work around paywalls/blocks. Saved texts: L/work/html_clean/, L/work/texts/nb/, the sheet L/work/coverage_current.xlsx.
- Batch writes (ArtifactData batch). If a write is denied by a permission check, stop and report exactly what was denied.
- Also write L/work/out/decided_<tab>.csv (id, key, choice, note).
Final report: per tab — decided / left for Sammy (with the short reason for each left), and anything surprising.
