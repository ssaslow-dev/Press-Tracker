# Audit: the 33 translated Reprints that fail the code's rule

Independent judgment audit (Fable, 2026-11-04) of the 33 rows in `proposals.csv` that sit in a different language from their Original and fail `pair_class` (no credit and no shared byline: 25; same byline but 3 to 8 days apart: 8). Read-only: the workbook copy 0bccc1fc and the saved copies in `data/library`. Nothing changed. The proposals were treated as claims to test, not conclusions.

## Verdict

**Keep 32 of the 33 as reprints of their current story. Split 1** (01920, Shuang Ma Chemical, Korean): its saved page is a different article, not a translation of the USA Today story.

The script's rule is right for new finds (where nobody has read the text), but on these rows the text itself answers the question, and in 32 cases the text is the Original's text in another language. The 25 "no credit, no shared byline" rows failed the rule for mechanical reasons, not because they are different stories:

- **9 CE Noticias Financieras rows** (English / Portuguese feed copies of Spanish papers: El Tiempo, El País, El Imparcial, Metro Puerto Rico, Expansión; Portuguese copies of the AP fire-money story). Each is a sentence-for-sentence machine translation published the same day (one day for the AP story). The feed credits only "ContentEngine", so the code sees no credit. CE Noticias is typed `aggregator` in `outlet_rules.json`, which may never be an Original (REPRINT-v2); splitting would make it one. Same reasoning for the 2 **Sohu** rows: the Chinese texts carry the AP story's facts and quotes (Farkas, Sawicki, Greenberg, the Norton Simon "nearly 50 years" statement), one a full translation, one a condensed rewrite; Sohu is an aggregator.
- **3 AP Spanish rows** (CalMatters 01317, El Mundo 07806, Telemundo 52 07807): AP's own Spanish translations, bylined "Trân Nguyen / Trán Nguyén, The Associated Press", 0-1 days later; 01317 ends "traducida del inglés por un editor de AP". The byline failed to match only because the code's name comparison keeps accents (Nguyễn vs Nguyen). Consistent with 07815 (Vietnamese, byline AP), already filed under s00353 (WEBLOOKUPS-v1).
- **La Presse Canadienne 08040** (French): same-day translation of the AP special-session story under the AP reporter's byline, ending "Les journalistes de l'Associated Press ... ont contribué". The Canadian Press is AP's distributor in Canada, so the wire-against-wire bar ("own distributor only") does not apply.
- **East Bay Express 03486**: not a different story. Its text is the CalMatters housing story word for word (same as Napa Valley Register 03482), signed "-CalMatters" at the end. The byline cell "D. Scot Miller" is wrong (an East Bay Express name, not the author); listed for Sammy, not changed here.
- **The 9 English rows of s00512** stay in the story under Sammy's decision 7 (English becomes the Original).

The 8 "too late" rows are translations by the same reporter or the same house, published on the Spanish-language outlet's own schedule 3 to 8 days later: CalMatters' own Spanish version in La Prensa Sonoma and the Press Democrat ("Read this story in English", byline "Levi Sumagaysay | CalMatters"), the Sacramento Bee story in McClatchy's Vida en el Valle (co-byline adds the translator, Juan Esparza Loera), and the four English copies of s00985 that Sammy has already kept. Sammy's s00985 decision shows the 2-day limit is a search-time guard, not a definition of "same story".

**The one split, 01920 (Shuang Ma Chemical, Korean, 2024-09-05):** the saved page (ko.shuangmachemical.com) is a Korean explainer "Titanium dioxide in food: should you be concerned?" on a chemical company's site. It mentions Gabriel's bill in one sentence and is not the USA Today article in any language; the "Eduardo Cuevas" byline was copied from a cited source. It becomes its own story (Original = 01920, the only row of its group). Flag for Sammy: a chemical supplier's resource page may not be press coverage at all (NOBLOGS-v1 judges by outlet); if he drops it, no split is needed.

## Per-row decisions

| Article ID | Story | Row | Decision | Why |
|---|---|---|---|---|
| 07129 | s00044 | Sohu (Chinese) 09-20 | keep | full Chinese translation of the AP story; aggregator, never an Original |
| 07119 | s00044 | Sohu (Chinese) 09-21 | keep | condensed Chinese rewrite of the same AP story, same facts and quotes; aggregator |
| 00986 | s00252 | CE Noticias English | keep | machine translation of El Tiempo, same day |
| 00991 | s00252 | CE Noticias Portuguese | keep | same text as 00986 in Portuguese, same day |
| 01317 | s00353 | CALmatters (Spanish) | keep | AP's own Spanish translation, AP byline, same day; byline match lost to accents |
| 07806 | s00353 | El Mundo (Spanish) | keep | "Por Trán Nguyén, The Associated Press", next day |
| 07807 | s00353 | Telemundo 52 (Spanish) | keep | same AP Spanish text and byline, same day |
| 01531 | s00430 | CE Noticias Portuguese | keep | Portuguese translation of the AP fire-money story, next day |
| 01532 | s00430 | CE Noticias Portuguese | keep | second Portuguese translation of the same AP text (Sacramento dateline) |
| 08040 | s00479 | La Presse Canadienne (French) | keep | AP's Canadian distributor, same byline and day, AP credit in the text |
| 01829-01837 | s00512 | 9 English chain copies | keep | Sammy's decision 7: English becomes the Original; 01829 marked as the Original (same-day tie, lowest Article ID; the save program's originals order settles the tie) |
| 01846 | s00519 | CE Noticias English | keep | machine translation of El País, same day |
| 01926 | s00546 | CE Noticias English | keep | machine translation of El Imparcial, same day |
| 02885 | s00827 | CE Noticias English | keep | machine translation of Metro Puerto Rico, same day |
| 02914 | s00853 | CE Noticias English | keep | machine translation of Expansión, same day |
| 02960 | s00853 | CE Noticias Portuguese | keep | same, Portuguese |
| 03482-03485 | s00985 | 4 English copies | keep | Sammy's decision 7; 03482 marked as the Original (06-16 tie with Noozhawk 03483, lowest Article ID) |
| 03486 | s00985 | East Bay Express | keep | the CalMatters text word for word, "-CalMatters" sign-off; byline cell wrong |
| 01920 | s00552 | Shuang Ma Chemical (Korean) | **split** | a different article (titanium dioxide explainer); not a translation of USA Today; may not be coverage |
| 02117 | s00610 | La Prensa Sonoma (Spanish) | keep | CalMatters' own Spanish version, same byline, 3 days |
| 02118 | s00610 | Press Democrat (Spanish) | keep | same text and byline as 02117 |
| 04685 | s01422 | Vida en el Valle (Spanish) | keep | Sacramento Bee story translated in the same house, co-byline, 8 days |

## Side findings (not changed, for Sammy)

- 03486 East Bay Express: Author / byline "D. Scot Miller" should be Marisa Kendall (CalMatters).
- 01920 Shuang Ma Chemical: decide whether a chemical supplier's resource page counts as coverage.
- Sohu 07119 / 07129 are self-media accounts hosted on Sohu (marked "原创"); kept because the outlet is already in the table as an aggregator.
- For the code: `people()` compares names with accents kept, so "Nguyễn" and "Nguyen" never match. Folding accents (as `norm_tokens` does) would have let the 3 AP Spanish rows pass the rule on their own.

## Counts

33 rows: keep 32, split 1 (new story: 1, Original = 01920). Of the 32 kept, 14 are under stories Sammy already settled (s00512, s00985) and 18 are this audit's call.
