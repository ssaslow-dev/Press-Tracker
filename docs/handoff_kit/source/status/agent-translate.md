# agent-translate (T13 part 1) — 2026-10-27
Output: lib/work/out/translate_tracker.jsonl (23 lines); per-story English text in lib/work/out/tr/<sid>.txt.
- hl_en written for all 16 stories that needed one.
- text_en (full translation, not summary) for 13 stories: jg-00045, 01831, 01865, 01887, 01966, 02192, 02260, 02543, 02729, 03107, 03174, 03683, 04133.
- text_en_missing for 10: no saved text at all (jg-01872, 02673, 03034, 03666, 03824) or source already English (jg-02183, 03211, 03983, 04015, 04177 — flagged source_already_english).
- Tone: none of these 23 sids are in tone_tracker_*.jsonl with text (only jg-04043 and jg-02347 there), so no tone ratings from this task.
Self-check (re-read against source): jg-01831, jg-02729, jg-03174 — faithful; quotes rendered as translations of the outlet's own (already translated) quotes, not original English wording.
Caveats for Sammy:
- Language label looks wrong on 5 stories whose saved text is English (jg-02183 "Chinese", jg-03211 "Portuguese", jg-03983 "Korean", jg-04015/04177 "Hebrew"), and jg-02260 is labeled Portuguese but the page is Vietnamese.
- jg-04177 saved text does not mention Gabriel (possible wrong match); jg-03983 and jg-04015 have no Gabriel mention in the first 15,000 characters of the saved text.
- jg-02260: names were machine-mangled in the Vietnamese page; restored to real names (George Whitesides, Mark Takano, Ted Lieu, Norma Torres, Chris Duncan, etc.).
- jg-02192: one source item title is garbled ("uma leitura shiológica"); rendered as "a reading".
- Listing/sitemap/video pages (jg-01887, 03683, 04133, 03107) are not single articles; translated what's there and noted it.
