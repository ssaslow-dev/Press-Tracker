# agent-chrome-calmatters (2026-10-28)
Task: save copies of CalMatters Coverage rows with Saved Copy? != Yes and a Publisher link.

## Finding: 0 targets
- CalMatters/CALmatters rows without a copy: 14 (13 "CalMatters" + 1 "CALmatters", aid 09013). Every other CalMatters row (134) already has Saved Copy? = Yes.
- All 14 are "Reprint (unverified)", Data Source "Tracker reprint list", Search lookup (Oct 26) = "Not found online".
- None has ANY link (Publisher link, ProQuest, NewsBank all blank), and none has a Headline or Date. So none meets the brief's target rule; nothing to fetch.
- Why no copy: they are AP (Adam Beam, Don Thompson, etc.) and NPR (Joe Hernandez, Ayana Archie) wire stories whose Originals are AP / KRCR / FOX40 / LAist / CapRadio rows (12 of 14 Originals have publisher links). The old tracker's free-text "also" list named CalMatters as a pickup; the Oct 26 search found no CalMatters copy. CalMatters does not normally run AP/NPR wire copy, so these CalMatters "reprints" are likely spurious.
- Note on the premise: DECISIONS.md does not say reprints never get copies (line 85: 466 reprint rows with links WERE fetched). These rows lack copies because they lack links, not because they are reprints.
- Question for Sammy (not decided here): keep these 14 unverified CalMatters reprint rows, or drop them as unconfirmed? Listed in work/chromesave2/results_calmatters.csv (result = not-attempted).

## Self-check
- results_calmatters.csv: 14 rows, 0 saved. targets_calmatters.csv: header only (0 targets).
- No fetches, no library writes, no workbook writes, no Exa.

FINAL
