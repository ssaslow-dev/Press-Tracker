# agent-chrome-b — J. (jweekly) Chrome saves (2026-10-28)
- started; read brief (incl. UPDATE: J. only), README, DECISIONS, playbook. No rows done for other outlets (told main).
- browsing in own tab 995517847; per-row browse log work/tmp_agent-chrome-b/browse.jsonl
- browsing done: 32/32 pages downloaded (no paywall/login, all h1 match), tab closed. Next: stage, clean, save.
- Targets: 32 J. Coverage rows (Saved Copy? No + Publisher link), all with File name "BLOCKED – TinyFish" -> work/chromesave2/targets_B.csv. (1 more J. row has no Publisher link; 30 already Yes.)
- Browser: 32/32 opened in own tab, all article pages (h1 matches sheet headline, small variants), dates match, no paywall/login/CAPTCHA. Full outerHTML downloaded per brief, then moved to Documents/Gabriel press PDFs/_clip_downloads/ (mv, 32).
- Cleaning: clean_html.py find mode on the full page left cookie-consent tables + site nav (~2,400 words vs ~800 article), so I built library-format pages (header div "Outlet · date / URL / Saved 2026-10-28 (Chrome)", h1, byline, lead photo+caption, .entry-content minus newsletter aside, ad zones, scripts, Jetpack Related, donation box, cookie video placeholders) and ran clean_html.py find mode on that: all 32 status cleaned, verdict ok, no flags, words within a few % of the browser's article count. Jesse Gabriel named in article text on every row (checked contexts on 09443/09444/09278 where Gabriel Greschler is byline/photo credit).
- Library adds (add-only, preflight: none existed): 32 cleaned -> Desktop/Tracker library/<year>/ws<aid><o|r>-s<story>.html; 32 full raw pages -> _original_html/<year>/ same name. Mac sha256 = local for all 64. Cleaned copies in work/html_clean/<year>/. 32 lines appended to work/library_adds.csv.
- Results: work/chromesave2/results_B.csv — 32 saved, 0 paywalled, 0 wrong-page, 0 no-gabriel, 0 error.
- NOTE for the sheet write (agent-chrome-a): these rows' File name cells hold "BLOCKED – TinyFish", not blank; per DECISIONS 2026-10-27 (good retries replace the placeholder) they should become the library name + Saved Copy? = Yes + File type "scraped html".
- Self-check: 32 targets = 32 results rows = 32 library files = 32 _original_html files = 32 html_clean files; checksums verified on Mac.
FINAL
