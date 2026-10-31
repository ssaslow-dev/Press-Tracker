# Press releases: build_data.py and apply_fills.py changes (agent-pressrelease, 2026-10-27)

Spec: DECISIONS.md 2026-10-27, "pure press releases are excluded". Input: `work/out/press_releases.csv` (keyed by OLD Article IDs; verdicts yes / no / borderline). Borderline rows are in the review queue (`items/13-pressrelease`, 71 items); a row becomes 'Yes' only after Sammy's decision is saved, or when the agent decided it.

These are change specs only. I edited neither file (agent-ids owns build_data.py).

## 1. apply_fills.py: new column 'Press release'

Two things in the current script affect this:
- `put()` writes only into columns that already exist (`colname not in col` returns early), so the column has to be created first.
- The final check asserts `x.shape == y.shape` and identical column lists. Adding a column breaks that, so the check has to compare the old columns only and then check the new column on its own.

Add this block before `wb.save(a.out)`. The column goes at the end of both tabs, after Role.

```python
# --- Press release column (agent-pressrelease; DECISIONS 2026-10-27 "pure press releases are excluded") ---
# Source: work/out/press_releases.csv (old_aid, sid, outlet, headline, verdict, confidence, reason).
# verdict 'yes' -> 'Press release' = 'Yes' (green). 'borderline' -> 'Yes' only if Sammy chose the release option
# in the review queue (decisions/pr-NNN, item key = old_aid); otherwise left blank. 'no' -> blank.
PR_COL = 'Press release'
PR_YES_CHOICE = 'Press release: leave out of tracker (Press release = Yes)'
for sheet, cols in ((ws, col), (wo, ocol)):
    if PR_COL not in cols:
        c = sheet.max_column + 1
        sheet.cell(1, c).value = PR_COL
        h = sheet.cell(1, c - 1)                      # copy the header style of the previous header cell
        sheet.cell(1, c).font = copy.copy(h.font); sheet.cell(1, c).fill = copy.copy(h.fill)
        sheet.cell(1, c).alignment = copy.copy(h.alignment); sheet.cell(1, c).border = copy.copy(h.border)
        cols[PR_COL] = c
prf = os.path.join(W, 'out', 'press_releases.csv')
pq = os.path.join(W, 'out', 'pressrelease_queue_decisions.json')   # optional: export of decisions for pr-* items
qdec = {}                                                          # {old_aid: chosen option}
if os.path.exists(pq):
    qdec = json.load(open(pq))
rp = rep['press_release'] = {'yes_auto': 0, 'yes_queue': 0, 'borderline_undecided': 0, 'unknown_aid': 0}
if os.path.exists(prf):
    for x in pd.read_csv(prf, dtype=str).fillna('').to_dict('records'):
        x = fix_ids({'aid': x['old_aid'], 'sid': x['sid'], 'verdict': x['verdict']})
        if x['aid'] not in row_of: rp['unknown_aid'] += 1; continue
        if x['verdict'] == 'yes':
            put(x['aid'], PR_COL, 'Yes'); rp['yes_auto'] += 1
        elif x['verdict'] == 'borderline':
            if qdec.get(x['aid']) == PR_YES_CHOICE: put(x['aid'], PR_COL, 'Yes'); rp['yes_queue'] += 1
            else: rp['borderline_undecided'] += 1
# --- end Press release ---
```

`put()` already mirrors into Originals (Original rows only) and writes green (`GREEN = '000B8A3E'`).

Change the verify section so the new column doesn't trip the shape check:

```python
for s in ('Coverage', 'Originals'):
    x, y = A[s], B[s]
    new = [c for c in y.columns if c not in x.columns]
    assert new in ([], ['Press release']), (s, new)
    y_old = y[list(x.columns)]
    assert x.shape == y_old.shape and list(x.columns) == list(y_old.columns), s
    ch = int(((x.notna()) & (x.fillna('') != y_old.fillna(''))).sum().sum())
    rep[f'{s}_existing_changed'] = ch
    assert ch == 0, f'{s}: {ch} existing values changed'
    if new: rep[f'{s}_press_release_yes'] = int((y['Press release'].fillna('') == 'Yes').sum())
```

Queue export: the decisions live in the review page's `decisions` collection, one doc per item id (`pr-000` to `pr-070`). Each item's `key` is the old Article ID (in `items/13-pressrelease`). Whoever runs T14 writes `work/out/pressrelease_queue_decisions.json` as `{old_aid: choice}`. Without that file, borderline rows are simply left blank.

Expected result with no queue answers: 497 'Yes' on Coverage (348 Original rows, 149 Reprint rows), and 348 'Yes' on Originals.

Order: this runs in the T14 write while IDs are still old (fills are keyed by old IDs, per DECISIONS). The ID migration then carries the column along. `migrate_ids.py` needs no change, because it doesn't touch this column, but it should keep the column when it copies or reorders.

## 2. build_data.py: leave 'Press release' = 'Yes' rows out of entries and reprint lists

Add one helper next to `s()`. It works on any workbook with or without the column, and old or new IDs:

```python
PR = 'Press release'
def is_pr(r): return PR in C.columns and s(r[PR]).lower() == 'yes'
```

**a) Reprint lists.** In the `reps` loop (currently line 48), skip release rows:

```python
for _, r in C[C['Original or reprint'] == 'Reprint'].iterrows():
    if is_pr(r): report['pr_reprints_dropped'] += 1; continue
    reps[r['Story ID']].append({...})            # unchanged
```

`report` is created after this loop in the current file (line 58). Move `data = []; report = collections.Counter()` above the `reps` loop, or use a separate counter.

**b) Entries.** In the Originals loop (currently line 59), skip release originals:

```python
for _, r in C[C['Original or reprint'] == 'Original'].iterrows():
    if is_pr(r): report['pr_originals_dropped'] += 1; continue
    ...
```

**c) '# of reprints' (`rep`).** It currently trusts the sheet's "# of reprints" cell, which still counts release outlets. When any reprint was dropped, use the recount instead:

```python
dropped_here = pr_reps_by_sid.get(r['Story ID'], 0)      # count per sid collected in (a)
'rep': len(outs) if dropped_here else (int(float(r['# of reprints'])) if s(r['# of reprints']) else len(outs)),
```

In (a), collect `pr_reps_by_sid = collections.Counter()` and do `pr_reps_by_sid[r['Story ID']] += 1` where the row is skipped. `also` and `rc` are already derived from `rs`, so they follow automatically.

**d) Leave the `rows` dedupe index (line 112) and `idmap` unchanged.** Release rows must stay in `rows`, so the Update button's dedupe still recognizes them and doesn't propose them again as new finds. Optionally add a kind code `"P"` for release rows (`kind = 'P' if is_pr(r) else {...}`). That would need a CONTRACT change (kind is "O"/"R"/"" today) and a check in js_update.js. The safer default is no change.

**e) Report.** Add `pr_originals_dropped` and `pr_reprints_dropped` to the printed report. The self-check is: stories before minus `pr_originals_dropped` equals stories after.

**f) Update button / sheet task (for the coordinator).** New finds from release wires should arrive with 'Press release' = 'Yes'. The simplest version: the sheet task sets it when Outlet is on the wire list (Targeted News Service, US Fed News, PR Newswire, Hispanic PR Newswire, Business Wire, GlobeNewswire, U.S. Newswire, ENP Newswire, M2 Presswire, PR.com, PublicNow, TendersInfo, *Monitor Worldwide, Contify, MIL-OSI/ForeignAffairs) or when the URL contains /press-release(s)/ or /press_release/. Anything else goes to the queue. This also needs a CONTRACT entry: covcols gains 'Press release'.

## 3. Stories whose Original is a release but which have non-release rows

Dropping a release Original also hides that story's non-release reprints, because reps hang off the Original. Ten stories have this (5 'yes' originals, 5 borderline). Full list: `work/out/press_release_originals.csv`. Suggested new original = the earliest non-release row (wire services first, then a staff byline):

| Story | Release original (old ID) | Suggested new original |
|---|---|---|
| jg-00248 | nb-00614 TNS (governor's signing list) | ws-00358 KRCR, 2025-10-10 |
| jg-00672 | nb-01647 California Courier (Caucus Foundation) | ws-00665 Armenian Mirror-Spectator, 2024-04-18 |
| jg-00690 | nb-01681 US Fed News (Gabriel/Kounalakis release) | ws-00686 Beverly Press (Edwin Folven), 2024-04-04 |
| jg-00873 | nb-02203 TNS (legislative update) | ws-00844 FOX 11 list, 2023-10-08 |
| jg-01514 | nb-03621 TNS (legislative update) | ws-01199 Patch, 2019-10-06 |
| jg-01030 | nb-02697 CE Think Tank Newswire (borderline) | ws-00944 Pacific Research Institute, 2023-04-21 |
| jg-01037 | nb-02706 Chemicals Monitor (borderline) | ws-00946 Baking Business, 2023-04-17 |
| jg-01266 | nb-03171 California Courier (borderline) | ws-01094 Armenian Weekly, 2022-02-10 |
| jg-01827 | ws-01338 Encino Enterprise (borderline) | ws-01340 Valley News Group, 2026-10-15 |
| jg-03045 | ws-02714 Encino Enterprise (borderline) | ws-02715 Imperial Valley Press, 2024-04-16 |

In almost every case these non-release rows are rewrites that share release text, not true reprints. Under the 90% reprint rule they would be their own stories, so this overlaps with T28 (agent-regroup). The re-pick needs Sammy's approval, like other grouping changes, and belongs in the regroup's approved changes, not in this column.

Of the 348 'yes' originals: 335 stories consist only of 'yes' rows and disappear from the tracker entirely; 5 are in the table above; 8 more stories also contain borderline rows, and how those end up depends on the queue.
