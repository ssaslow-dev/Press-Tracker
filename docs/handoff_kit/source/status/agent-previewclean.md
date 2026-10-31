# agent-previewclean — AV preview cleanup (Sammy comment de9c2baa)
## Rules: draft only — no edits to code/ or build/ (agent-backendclean2 is folding code), no publish, no workbook/Mac writes, add-only. Helpers + outputs in work/tmp_agent-previewclean/.
## Log
- 2026-10-28 started; read README, DECISIONS (newest), phaseB_inbox, status/agent-backendclean2. Brief: audit all preview types.
- SCOPE CHANGE (Sammy via coordinator): AUDIO & VIDEO previews only; article / press-release / NewsBank / other web-save previews dropped, no findings on them in the spec. Inbox item retitled "AV PREVIEW CLEANUP".
- Read the live tracker's copies (artifact 27f923dc…, version 1793153876-e0f4) via Artifact read into work/tmp_agent-previewclean/live/ (25 shards + manifest).
- AV set (avset.py): AV tab Item type Episode / Broadcast segment / Video clip on the story's Original = 86 stories, 80 with a copy (6 have none: s01777 s01795 s01796 s04667 s04676 s04687). Web-story AV rows (375 Originals) are article saves -> out of scope.
- Rendered all 80 the way 06_story_sheet does (srcdoc, <a>/<area> stripped) with Playwright (render.py / test_av_clean.py) -> before/*.txt.
- Leaks found in 75/80 copies (table in spec.md §2): capture header 41 copies; Exa analyst fields 13 copies/91 lines; raw ms/ISO time codes 14 copies/400 hits; caption time markers + cue junk 8 copies/179; NewsBank/ProQuest file captions + citation 6/16; vendor boilerplate 5/7; player/app/nav UI 12/25; shortcodes/tags 2; IA internal label 1; layout debris 12/33. Sources: saved files (all but one); make_copies.nb_page (PDF captions/citation); renderer adds nothing.
- The commented preview = s04692 (John Kobylt Show): "1 of 3" = 2 hits in our own field lines + 1 real; after cleanup 1 of 1.
- Wrote av_display_clean.py + av_rules.json (standalone display-copy cleaner), test_av_clean.py (all 80 AV copies; word balance + Gabriel accounting + long-block check), samples.py -> before_after_samples.md, spec.md.
## Self-check
- test_av_clean.py: 80 copies, 75 changed, 0 fails, 0 safety flags. Words 99,737 -> 94,949 (4,880 removed by rules; balance holds per copy within 2%). Gabriel mentions 162 -> 126; all 36 removed were in back-end fragments (13 Gabriel role, 13 Excerpt rule, 5 Note, 1 IA title label, 1 "Tweets by AsmGabriel") or exact duplicate lines (3). No transcript/story mention lost.
- Idempotent (second pass changes nothing on all 80); jgimg image refs preserved (35 before = 35 after).
## Not fixable by the cleaner (for coordinator)
- Listing/wrong-page copies -> RETRY queue candidates: s01819 (FOX40 teaser list), s03489 (VBS gala sponsors), s03780 (VBS archive list), s04178 (podbean listing).
- s01426 / s01548: empty NewsBank AirTalk copies; likely duplicates of s03947 / s04061 (same episodes) -> regroup/duplicate queue.
- s01619: ProQuest transcript with fused words (missing spaces at line joins) -> re-extract.
- AV box Notes row (53_tabs.js tbAvBox) shows "Exa podcast library: https://…; finder note: …" verbatim — panel, not preview; follow-up.
## Handoff
- Queued in build/phaseB_inbox.md: "AV PREVIEW CLEANUP (Sammy comment de9c2baa)" -> work/tmp_agent-previewclean/spec.md. Integration = make_copies av_clean hook (fix A), sheet_task display copy + prompt step 6 (B/B2); publish av_display_clean.py + av_rules.json in pipeline/. Waits for agent-backendclean2's fold.
