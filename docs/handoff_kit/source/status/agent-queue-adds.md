# agent-queue-adds (2026-10-27)

Review queue artifact https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB, db collection "items" (did not touch "decisions" or other docs).

- items/10-tone (new, v1, cat tone): 10 items tone-000..009 — jg-03120, 03206, 03288, 03501, 03538, 03575, 03724, 04102, 04125, 04180 (all records with tone_agrees_with_current == false in fetch_rated_1/2). Current tone from coverage_current.xlsx Tone column. key = Article ID (ws-). jg-04180 title uses full headline "Six-Day War: Voices after victory" (sheet has truncated "Six"); detail notes Role may be Op-ed.
- items/3-nogabriel (v2 -> v3, if_version pinned): kept nogab-000..027, appended nogab-028..034: jg-03782, 02792 (propose Keep), 03137, 03879, 04120, 04168 (propose Keep), 01796.
- items/11-links (new, v1, cat links): links-000..003 — jg-01821, 01822, 03682, 03684.
- build/review/index.html: added CATS tone + links entries only; republished via Artifact edits (version 6), capabilities carried forward.
- Read-back: all three docs match local JSON; ids unique; proposed in options.
- Note: existing nogab-023 (jg-01710, nb-04028, Jewish Journal "Six-Day War: Voices after victory", "no Jesse Gabriel mention") conflicts with tone-009 (jg-04180, same story, fetch says Gabriel wrote one of the pieces).
