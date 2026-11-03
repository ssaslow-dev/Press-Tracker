# Check 2: outlet names sitting in the Author cells

Nothing was changed. Checked all 8,222 Coverage rows (workbook 0bccc1fc), Author 1 to 9.

## Counts (author cells that equal or are a form of an outlet or publisher name)
- **23 cells in 23 rows: the outlet's own name alone, not a person and not a group of people.** Proposal: clear them (14 high confidence, 9 medium). Examples: Telemundo and Telemundo 52, The Algemeiner, ABC News, Times of Israel, La Opinion, La Nacion (2 rows), Marin Independent Journal, Turlock Journal, Paradise Post, The Armenian Mirror-Spectator, Sacto Daily, AOL (07261); medium (blog or brand labels): Ground Game LA (3, Knock LA), Los Angeles County Politics (3), Palate Shift, Alston & Bird (a law firm's own page).
- **48 cells keep:** "<Outlet> Staff" and "<Outlet> Editorial Board" forms (Yo Venice Staff, Asbarez Staff, Los Angeles Times Editorial Board ...). These are groups of people, allowed by the rules.
- **29 cells keep:** the outlet is one person's blog (a "(Substack)" or "(Medium)" outlet, or a person-named outlet such as Marion Nestle), so the name is the real writer.
- **Ambiguous, 175 cells, listed in `ambiguous.csv`, left as they are:** wire and service names (Associated Press 86, The Associated Press 13, City News Service 27, PR Newswire 4, Tribune Content Agency, Bay City News Foundation), and credits to another organization on a reprint (CalMatters 21 (20 plus "Calmatters"), California Black Media 8, Los Angeles Times 3, CNN 3, Environmental Working Group 3, The Hill, AOL on the Independent row 07262, and a few more). Rules and existing practice keep wire credits as authors; Sammy decides whether org credits should go (a wire or an org is not a person, but the saved rules allow them).
- Not yet in the workbook: "The Bakersfield Californian" (the Nov 3 NewsBank batch). It would be a new row of this kind; the save program should treat it the same way (blank the author, or keep by decision).

## What the Reporters tab would lose
`reporters_impact.csv`. Clearing removes 18 name entries that currently show as "reporters": together 19 Original stories (Ground Game LA 3, LA County Politics 3, Algemeiner 2, the rest 1 each; 4 of the names have no Original story, so they cost nothing). None of the 18 is in `reporters.json`, so no employment record is lost. The Outlet pages' "Top reporters" lists lose the same entries. Where a later author exists, the others shift left (none of the 23 has one).
Side note: Los Angeles County Politics rows have Publisher Stephen Witt; a person author could be filled instead, but that is a guess and not proposed.

## What applying would change
23 blank cells (plus the mirrored Originals rows). Author / byline (raw text) stays as is, so nothing is lost, only the clean Author split is blanked.

## How to apply on switch-over day
This clears filled cells, so it is an exception to fill-blanks-only that Sammy must approve and record in DECISIONS. Then: re-run `check_outlet_authors.py` on the real workbook, review `proposals.csv` in the preview, make the backup, apply in one step from the "Switch-over changes" screen, rebuild the Originals mirror. Alternative: keep, and teach `authorsplit.py` to leave an outlet-name byline blank for new rows only.

Files: `proposals.csv` (23 lines), `ambiguous.csv`, `reporters_impact.csv`, `check_outlet_authors.py`.
