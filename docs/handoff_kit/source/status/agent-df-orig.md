# agent-df-orig (DATEFILL Group A), 2026-10-28
- 32 rows (Original YYYY-MM / YYYY / blank + Reprint 06925). TinyFish search + fetch_content only; no browser automation.
- Output: work/tmp_datefill/groupA.csv (27 change rows: 19 high-conf dates, 5 med dates, 3 author/mention fills (2 high, 1 med); 8 not-found rows).
- Proposed corrections: 06915 month 02->03 (2026-03-25), 06933 month 09->10 (2024-10-02), 06952 maybe 10-04 (med); 06925 is CALmatters web copy of Original 01537 (CALmatters NB, same day; text rule passes text-edge/low on fetched text) -> same-outlet edition, should fold into 01537 (Removed "2 duplicate", Publisher link to 01537 which is blank).
- No pages saved to tmp_datefill/pages: every found row already has a library copy; fetch_content does not return raw HTML for clean_html.py.
