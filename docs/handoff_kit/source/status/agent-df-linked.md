# agent-df-linked (DATEFILL Group B), 2026-10-28

Scope: Coverage rows "Reprint" + blank Date at master 4d7fb37c = 94 (89 with a Publisher link, 5 without; the brief's 94 includes the 5).
Tools: TinyFish fetch_content + search only (no browser automation, no Exa, no deep research).

Outputs (L/work/tmp_datefill/):
- B.csv: 477 high-confidence changes (blank cells only): Date 91, Year 91, Word count 86, Mentions "Gabriel" 84, Language 42, Reach 34, Publisher link 4, Link status 4, Translated Headline 1, Story in English 1, Author / byline 1, Author 1 1.
- B_review.csv: 6 medium (09245 Date/Year: visible "March 17, 2022 at 2:11 AM PDT" vs metadata 02:11+00:00; 09234/09245 Word count from ProQuest text, not the reprint page; 08145 Reach "Out-of-state local" from one HealthDay row).
- B_reprint.csv: text-rule results per row. B_corrections.csv: proposed corrections (not written).
- pages/: empty. Every found page already has a library copy except 03183 (dead) and 08959 (dek-only teaser, no article), so nothing new to save.
Scripts: work/tmp_df-linked/ (load.py, rtest.py, build_csv.py, notes1.tsv = per-row date evidence).

Date convention used: the page's own byline date; UTC timestamps (Yahoo/AOL, metadata-only pages) converted to the US-local date (ET and PT agree in every case). 10 rows land a day before their UTC date: 01063, 02101, 02630, 04119, 04183, 05035, 07619, 07675, 08599, 08783 (and 00695, 00990, 05157, 07646, 08233 where visible date = PT date).
Not found: 03183 (AOL 404, no other copy), 04865 (American Israelite, no copy online). Their "Search lookup (Oct 26)" cells are already filled, so not touched.

Self-check: 92 of 94 dated; every Date has a quoted date line in notes1.tsv; text rule: 87 pass, 5 fail, 2 no text.
