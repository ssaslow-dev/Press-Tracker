# agent-buttonopt — Update button audit + optimization (Sammy: "debug and eliminate redundancy and optimize")
## Rules: Phase 1 read-only (no shared-file edits, no Exa, no workbook writes, no publishing); work in work/tmp_agent-buttonopt/.
## Log
- 01:57Z read README, DECISIONS (all), CONTRACT, apply_all, sheet_task.py + prompt, status of code/relrule/reltab/avtab/tabs/v19finish/relcopies2.
  Snapshot of shared files -> work/tmp_agent-buttonopt/snap/ (sha16 in SHAS.txt; = build/pub/pipeline at 01:57Z).
- ~02:05Z coordinator asked for a sub-agent split; no Agent tool here -> sent main the A-D split (JS map / sheet task / dry run / yield); continuing all myself.
- 02:10Z plan measured on the v19 preview (page copy with an eval hook, srv/): 780 TinyFish searches before paging for a since=LAST run (517 outlet-site, 120 issue-word, 40 D-Encino, 83 native-script outlet, 20 other); 521 hosts, 22 of them in TF_BLOCKED_HOSTS; tfDedupe drops 0. -> js/plan_out.json (for agent-buttonopt-yield). Coordinator: A (js) and D (yield) launched as agents; I do B + C + merge.
- 02:05Z (C) dry run: dry/mkfix.py fixture (13 rows, 9 pages, 3 releases, tones/authors, removal edit, hand reprint) on a copy of coverage_current with the pipeline copy: exit 0, verify ok, 33 s; 12 brief cases behave, except: Reprint rows keep Tone/Topic (S2), spurious Tone-rated-by conflict (S3), untestable listed 3x (S5), CONTACT regex (S6), JS reprints never text-checked (A-B1). After the prompt's write-back --check-only still exits 0 (S1). Live db (read-only list, out_dir): 2 removal edits pending since 10-27, so the no-op stop never fires today. Report: dry_report.md.
- 02:12Z (B) sheet-task map + token estimates -> map.md. Merged A (js_map.md) + D (yield.md) -> plan.md (ranked; A-B5 rejected per DECISIONS 98). 5 questions for Sammy in plan.md §E.
- Self-check: dry fixture cases 13/13 classified (9 OK, 4 with listed defects); plan numbers: searches 780 measured (2 independent measurements agree), prompt sizes measured on the preview page; sheet-task token figures are estimates (marked est.).
- WAITING for coordinator go-ahead (after v19 publish + step 4o). No shared file edited.
