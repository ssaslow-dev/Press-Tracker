# agent-autodecide — 2026-10-27

Queue: https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB. Created decision docs only for items with no decision (create-only `set`, no if_version, so any doc that already existed was refused, never overwritten). Each auto doc: {choice, note "Auto: …", at, by "Claude (auto)"}. 299 written in 6 batches.

| Tab | Items | Auto-decided | Already decided (Sammy) | Left for Sammy |
|---|---|---|---|---|
| 1-reach | 241 | 168 | 16 | 57 (38 medium, 18 low, + reach-015) |
| 2-role | 20 | 3 (role-015, -016 own press releases; role-019 Boutrous+Gabriel co-byline, same as Sammy's role-003) | 15 | 2 (role-017, role-018 "Sacramento Archives") |
| 3-nogabriel | 35 | 8 (take out: 006 land auction, 021 NY musician, 022 Witvoet infant obit, 030 Giffords, 031 other Jesse Gabriel arrest, 032 Petek; keep: 029 data table, 033 sidebar) | 2 | 25 |
| 4-language | 20 | 18 | 0 | 2 (lang-003, lang-007: "German" detection on US election/news pages looks doubtful) |
| 5-headline | 11 | 9 (5 section labels → Fix by hand; 4 already-English → Leave as is) | 0 | 2 (hl-001 'Regalos' "likely" label; hl-002 '– The Orion' suffix) |
| 6-duplicate | 5 | 5 | 0 | 0 |
| 7-copy | 6 | 5 (match < 0.5) | 0 | 1 (copy-005, match 0.9) |
| 8-bills | 64 | 0 (skipped) | 64 | 0 |
| 9-relabel | 151 | 79 | 0 | 72 (32 medium, 37 low, + 3 high held back) |
| 10-tone | 10 | 0 — see below | 0 | 10 |
| 11-links | 4 | 4 | 0 | 0 |
| 12-process | 2 | 0 (Sammy's) | 0 | 2 |

Held back despite "high": relabel-068 (AP Spanish feed), relabel-130 (SFV Sun), relabel-131 (Santa Barbara Independent) — row-level Spanish-language relabels that conflict with the outlet-level Reach item for the same outlet (reach-224 low, reach-015 high, reach-114 medium); reach-015 held with its pair.
Race: role-014 was decided by Sammy mid-run; that batch was refused atomically and resent without it.

10-tone: the coordinator relayed Sammy's new rule (DECISIONS.md: full-text tone overrides snippet tone) and asked to auto-decide all 10 as "Use the full-text rating (…)". The batch write was DENIED by the permission classifier (agent instruction is not user consent). Not retried. Files ready at scratchpad/autodecide/w/d/tone-000..009.json if Sammy approves.

Page (build/review/index.html, published v8; backup index.pre-autodecide.html): "Show only items that need me" toggle (default on, localStorage key reviewOnlyNeedsMe in try/catch) hides decided items; tab counts are now remaining/total; Claude-decided items carry a "Decided by Claude" tag with the note, a dashed accent border, and stay editable (Update re-saves as Sammy's, dropping `by`).
