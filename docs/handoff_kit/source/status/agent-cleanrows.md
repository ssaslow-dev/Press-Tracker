# agent-cleanrows (2026-10-28)
Task: delete accidental additions to the sheet (Sammy), conservatively, using past-search evidence. Helpers: work/tmp_agent-cleanrows/ (cands.py = list + reasons, edit.py, diffcheck.py, edit_report.json).

## WRITE (rule 7) — DONE
- Token taken when "none" (after newoutlets + avtab follow-ups); Mac master = staged = 4ebf43f7…6b0, no ~$ lock.
- Backup Backups/"AJG Coverage - NewsBank BACKUP before accidental-row cleanup 2026-10-28.xlsx" (Mac sha 4ebf43f7…6b0).
- Master committed with expectedMtimeMs 1793149174158; Mac sha 42ac14f13d858fcabe6e8c6e2e6dbe91f005e705687f190faa28ac38d6349f6a = output. work/coverage_current.xlsx updated (previous = work/coverage_pre_cleanrows.xlsx). Token back to "none".
- diffcheck: 0 unexpected differences. Coverage 9,702 → 9,633 (69 gone); Originals 4,547 → 4,510 (38 gone, 02356 added), mirror = Coverage Originals in order; A/V tab 899 → 896 (07762, 08131, 09681); other tabs unchanged; new "Removed" tab, 72 rows.
- 58 library files moved (mv) to Tracker library/_to_delete/ (31 library + 27 _original_html); list in _to_delete/_cleanrows_moved_2026-10-28.txt. work/html_clean copies left as they are (local snapshot).

## Deleted (69), reason per row in the Removed tab
1. Mis-credited reprint (14): CalMatters/CALmatters Reprint (unverified) of AP/NPR stories: 02278 02592 02632 03005 03220 03321 03785 04122 04148 04187 04199 04671 05053 09013. No link/headline/date; Search lookup (Oct 26) Not found online; chrome-calmatters found nothing. No other unverified outlet showed the pattern clearly (see review list).
2. Duplicates (24 + 1 from this session): 07762 (=01255), 08977 (=03777), 02762 (=02760), 01112 (=01110), 08068 (=08066), 08045 (=08043), 08570 08169 08042 (Politico Playbook = Politico ProQuest original), 06982 (=06980 e-edition PDF), 01856 (unverified edhat; verified edhat 01817 in same story), 02357 (=02344), 08412 (=02338), 07201 (=07151), 07413 (=07419), 09681 (=09684), 08131 (=08143). Session error: 09868 (=09867, agent-newoutlets added the same Lookout Santa Cruz article twice via a "/story" URL variant).
3. Not coverage (30): results pages 07318 08091 08517 08090 09074 09197 09452 09456 09642 + their unverified reprints 09075 09076 09198 09453 09454 09455; Blue Voter Guide 06908 07481 07482 08092 08261 08329 08516 08526 08543 09101 09513; C-SPAN 07700; Track JPAC 06914; J. Weekly archive 09525 (op-ed has row 09524); Excelsior sitemap 09157; FSM tag listings 07754 07900 07025 07317 07374; Davis Vanguard 07791 (tags only); Times of Israel 09692 (sidebar only).
- Promoted: 02356 (KSBY) → Original of s04435 (# of reprints 0). Reprint counts: 02759 2→1, 01109 2→1, 08064 3→2, 08043 1→0 (02356 set 0).
- Session-write check: clip/reltab/avtab/avtab follow-ups/chromesave added or changed no unintended rows; newoutlets only the 09868 double.

## Review list (NOT deleted; for Sammy)
- Web vs NewsBank copies of one article (distinct copies; merge?): 00598/00550, 07941/01486, 08352/02137 (different stories), 03255/03257 (different stories), 09314/04414, 07918/01466.
- Same URL, different stories (grouping choice): 06924 FOX40 reprint in s01781 vs 07933 Original; 06938 TODAY reprint in s01788 vs 08657 Original; 04564 JNS vs 04562 Jewish News Syndicate (ProQuest); 08190/08191 52hrtt regional editions (same article id, two URLs).
- 08421 LA Sentinel (BLOCKED) vs 08420 Precinct Reporter whose Publisher link points to lasentinel.net.
- Listing/issue pages that point at a real article (re-point rather than delete): 07086 Golden Coast Journal people page; 08597 California Globe tag page; 09476 Acorn issue page; 09654 SFV Sun "Page 1365"; 07801 New Times "Summer Guide 2025".
- Results/voter-guide items that are newspaper or editorial content: Sac Bee results tables 02501 04202 04806; CalMatters voter guide 06951 09227; Progressive Voters Guide 06912 (saved page = wrong election, no Gabriel); LAist guides 00079 00530; alfredtwu bill-tracker post 07358.
- Times of Israel liveblog rows whose right entry has no Gabriel (retry_results): 09701 09706 09700 09501 09514 09286 08957 09515.
- Originals whose full re-fetch had no Gabriel (reprint fetch): 00364 Yahoo, 07625 and 09256 Press Democrat.
- Possible mis-credits (Reprint unverified, Not found online): Press Democrat of ABC7 LA/WABC stories 08492 08928 09330 09024; Al Jazeera of AP 04660; Daily Kos / LAist of KQED-AP 08730 08731.
- NewsBank items with no Gabriel in text (DECISIONS 81: not grounds): 05386 (Anita Telle book festival), 05390 (El Dorado Hills kids).
- Same-outlet NewsBank duplicate records (separate records/copies, kept): e.g. Arcadia/Monrovia/Pasadena Weekly print pairs, Hispanic PR Newswire 04551–04553, Watertown 03805–03807, Bryan Times etc. 02932/02933 (two stories).

FINAL
