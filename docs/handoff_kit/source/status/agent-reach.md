# agent-reach (T15) — done
Output: lib/work/out/reach_proposals.csv (241 outlets, 862 stories): outlet_display, outlet_sheet, stories, reach, confidence, reason.
Method: existing tracker outlet→reach mapping (data.json) learned per category; outlets already mapped elsewhere use the majority (17 outlets, splits noted as medium/low); remaining by sheet city/state/medium/language + general knowledge. No web research; nothing written outside lib/work/out and this file.
Confidence: high 160 outlets (465 stories), medium 57 (312), low 24 (85).
Notes for Sammy: existing mapping itself is inconsistent for some outlets (OC Register, FOX40, SF Chronicle, AP feeds, Denver Gazette) — proposals follow the majority. College student papers have no precedent (set CA regional & local, medium). Foreign general outlets set National (UK precedent), low/medium.
