# Check 1: translated Reprints

Nothing was changed. Checked the 0bccc1fc workbook (Coverage tab) against the translation rule: a translation is a Reprint only if it is credited, or has the same byline, within 2 days, with a matching translated headline (the rule in `code/reprint_rule.py`, `pair_class`).

## Counts
- 133 rows sit in a different language than their Original (128 Reprints, 5 "Reprint (unverified)"). Another 143 Reprint rows have a blank Language cell and no foreign-looking headline; they were not counted.
- 79 meet the rule. Nothing to do.
- 5 are "Reprint (unverified)" (hidden in the tracker); left alone.
- 3 are really Language-cell errors, not translations (KNX News 00169 and AOL 00170 say English but carry the Spanish AP headline; the Original 10618, City News Service, says English but its headline is Spanish).
- 9 cannot be tested: same byline, same day, but no Translated Headline on file (e.g. Telemundo 33 Sacramento 07256, 08050, 08243; El Sol del Valle 02334, 04254; Independent en Espanol 01315; Excelsior 01547; Epoch Times 03787; CE Noticias 01508).
- 4 have the same byline and date but a weak headline match (CNN en Espanol 08245 is the same outlet and byline as English CNN 08224; Telemundo 52 09597; Kyunghyang Shinmun 08658; Israel Info 00514). Almost surely true translations; the headline test is too strict.
- 8 are too late (same byline, 3 to 8 days after): Vida en el Valle 04685 (8 days), Shuang Ma Chemical 01920, La Prensa Sonoma 02117, Press Democrat 02118, and four English copies of CALmatters s00985.
- 25 fail outright (no credit, no shared byline). 9 are CE Noticias Financieras machine translations (plainly the same story, but the feed credits nothing), 2 Sohu, 3 AP-story Spanish rewrites (CALmatters 01317, El Mundo 07806, Telemundo 52 07807), Presse Canadienne 08040 (a wire against a wire is never a reprint), and 10 English copies hanging under a Spanish Original.

## Top finding
Stories s00512 (HealthDay) and s00985 (CALmatters) have a Spanish Original with English reprints under it (9 chain newspapers; Napa Valley Register, Noozhawk, etc.). The Spanish row is the translation of an English story that is not in the tracker. The rule fix (new story for the English copies) is low confidence; the cleaner fix is a no-copy English Original, which is Sammy's call.

## What applying would change
Per the rule, 33 rows would leave their story and form 16 new stories (the earliest of each language group becomes its Original; reprint counts of the old Originals drop). Plus 9 Translated Headline cells to fill and 3 Language cells to correct. Tracker effect: roughly 16 more stories shown, a few fewer reprint counts.

## How it would be applied on switch-over day
Re-run `check_translations.py` on the real workbook, read `proposals.csv`, Sammy picks which groups to apply (high/medium first), preview in the "Switch-over changes" screen, back up the workbook, apply in one step. New Story IDs are assigned by the save program, never by hand. Translated Headlines come from the Update station.

Files: `proposals.csv` (61 lines), `all_checked.csv` (every row with its verdict and reason), `check_translations.py`.
Not checked: same-language rows whose text is a translation (no field marks them).
