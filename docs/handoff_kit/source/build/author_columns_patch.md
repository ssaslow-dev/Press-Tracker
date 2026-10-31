# T30 — Author 1..N + Author title: patch for the coordinator

Owner: agent-authorsplit. Spec: DECISIONS 2026-10-27 "authors split into columns" + Sammy's addendum (each co-author its own link; filter by person; same-person variants listed, not merged silently).
Nothing here edits a shared file. The coordinator applies it after agent-ids (T23) is done with build_data.py / js_merged.js.

T = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib/work/tmp_agent-authorsplit

## 0. Files to copy into L/code/
| from | to | what |
|---|---|---|
| T/authorsplit.py | code/authorsplit.py | the parser: `parse_byline(byline, outlet)`, `split_fill_row(T24 row, outlet, sheet_byline)`, `from_fill`, `author_key`, `disp` (same as build_data's) |
| T/author_columns.py | code/author_columns.py | `add_author_columns(wb, fills, overrides)`: inserts/fills the columns on Coverage + Originals |

Every patch below is an anchor script (each anchor must match exactly once, else it exits 1 and changes nothing):
```
python3 -I T/patch_apply_fills.py code/apply_fills.py code/apply_fills.py
python3 -I T/patch_build_data.py  code/build_data.py  code/build_data.py
python3 -I T/patch_authors_js.py  build/js_merged.js  build/js_merged.js
```

## 1. Workbook — apply_fills.py
The block goes right before `wb.save(a.out)`, after every `put()` (insertion shifts column indexes; bylines written in the same run get split too):
```python
# --- T30 author columns (agent-authorsplit; DECISIONS 2026-10-27 "authors split into columns") ---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from author_columns import add_author_columns
_af = os.path.join(W, 'out', 'author_fills.csv')
_fills = {}
if os.path.exists(_af):
    for _x in pd.read_csv(_af, dtype=str).fillna('').to_dict('records'):
        if _x.get('authors'): _x = fix_ids(_x); _fills[_x['aid']] = _x
_ovf = os.path.join(W, 'out', 'author_overrides.csv')          # Sammy's 15-authors answers: aid, authors (" | "), title
_over = {}
if os.path.exists(_ovf):
    for _x in pd.read_csv(_ovf, dtype=str).fillna('').to_dict('records'):
        _x = fix_ids(_x); _over[_x['aid']] = (_x['authors'], _x.get('title', ''))
rep['author_columns'] = add_author_columns(wb, fills=_fills, overrides=_over)
# --- end author columns ---
wb.save(a.out)
```
Verification change, in the `for s in ('Coverage', 'Originals')` loop:
```python
    AUTH = rep['author_columns'][s]['columns'] if rep['author_columns'][s]['inserted'] else []
    if AUTH:   # Author 1..N + Author title sit right after Author / byline
        _i = list(y.columns).index('Author / byline'); assert list(y.columns)[_i + 1:_i + 1 + len(AUTH)] == AUTH, (s, 'author cols')
    new = [c for c in y.columns if c not in x.columns and c not in AUTH]
    assert new in ([], ['Press release']), (s, new)
```
What it does:
- First run: inserts `Author 1` … `Author 8` + `Author title` (8 = longest split today) right after "Author / byline" on Coverage AND Originals (cols Y–AG); headers copy the byline header style; widths and the autofilter range are shifted; every old cell moves right unchanged.
- Group bylines (Staff, News Staff, Editorial Staff/Team, Editors, Newsroom, Staff and wire reports, Staff report) are authors: "<Outlet> <Group>". Article labels (Editorial, Opinion, Our View, Commentary, Letters) give blank Author columns. Editorial boards: "<Outlet> Editorial Board". On Reprint rows the outlet is the Original row's outlet for the same Story ID (Sammy, 2026-10-27); if there's no Original outlet, the row's own outlet is used.
- Fills every row with a byline; new cells green `000B8A3E`. Source per row: Sammy's override if any → T24's structured split (`out/author_fills.csv`, keeps its titles) when it names the same people as the sheet byline → else `parse_byline(sheet byline, Outlet)`.
- Later runs (columns exist, e.g. after T24's TinyFish resume adds ~846 bylines): fills only rows whose Author cells are all blank; never changes a filled cell; a row needing more than 8 author columns is skipped and listed in `report['author_columns']['needs_more_columns']`.
- `--hold` rows are split like the rest (the columns only restate the existing byline).
- Overrides file (to be made from the queue answers): `work/out/author_overrides.csv` with `aid, authors, title` (authors joined " | "). Grouped queue items carry several aids in `key` (comma-separated): one override line per aid.

## 2. Tracker data — build_data.py
```python
import sys, re, json, collections, os
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I drops the script dir; authorsplit.py lives here
from authorsplit import parse_byline
...
covcols = list(C.columns)
ACOLS = sorted([c for c in C.columns if re.fullmatch(r'Author \d+', c)], key=lambda c: int(c.split()[1]))
def authors_of(r, o):
    a = [str(r[c]).strip() for c in ACOLS if str(r[c]).strip()]
    if a: return a, str(r.get('Author title', '')).strip()
    b = str(r['Author / byline']).strip()
    if b: p = parse_byline(b, r['Outlet']); return p['authors'], p['title']   # rows the sheet task added unsplit
    old = o.get('author', '')
    return [x.strip() for x in old.split(';') if x.strip()], ''
...
        'author': s(r['Author / byline']) or o.get('author', ''),
        'authors': authors_of(r, o)[0], 'atitle': authors_of(r, o)[1],
```
**CONTRACT proposal** (data block): add `authors` = list of names from Author 1..N (editorial boards as "<Outlet> Editorial Board"), `atitle` = Author title. `author` stays the raw "Author / byline". `covcols` gains the 9 columns automatically.

## 3. Tracker page — js_merged.js (15 anchored replacements)
New helpers after `splitAuthors`:
```js
const authorKey = a => { let w = String(a||'').normalize('NFKD').replace(/[̀-ͯ]/g,'').replace(/[‘’]/g,"'").toLowerCase().replace(/[.,]/g,' ').replace(/\s+/g,' ').trim().split(' ');
  if (w.length > 2) w = [w[0], ...w.slice(1,-1).filter(x => x.length > 1), w[w.length-1]]; return w.join(' '); };
const ACANON = new Map();   // key -> display form used most often (ties: longer form)
function buildAuthorCanon(rows){ … }
const canonAuthors = list => { … dedupe by key, map to ACANON display … };
```
`authorKey` is identical to Python `author_key` (case, accents, periods, commas, extra spaces, single-letter middle initials ignored).

| # | where | change |
|---|---|---|
| 1 | after `splitAuthors` | authorKey / ACANON / buildAuthorCanon / canonAuthors |
| 2 | `searchStr` | also searches every author and `atitle` |
| 3 | `setAuthor` | runtime-found authors go through `canonAuthors` |
| 4 | record init (`D.forEach … r.authors = splitAuthors`) | use `r.authors` from data (Author 1..N), fallback `splitAuthors(author)`; build ACANON; canonicalize |
| 5 | Update-added stories (`r.authors = splitAuthors(r.author)` in the add loop) | same as 4 |
| 6 | `[data-author]` click handler | filters on the canonical person, so the link shows solo AND co-written stories |
| 7 | `clipItem` (overview cards) | each author is its own `data-author` link (was plain text) |
| 8 | main click handler | a click on `.clip [data-author]` filters instead of opening the story |
| 9 | table row `.by` | shown when `r.authors.length` (each already a link) |
| 10 | story detail factline | shown when `r.authors.length`; adds ` (Author title)` |
| 11 | CSV export columns | `Author / byline`, `Author 1..N`, `Author title` (was one `Author`) |
| 12–13 | Copy-for-sheet TSV | header `Authors`, value = authors joined "; " |
| 14 | Reporter facet hint | "Co-authors are listed one by one, and a co-written story counts for each of them." |
| 15 | About → Author definition | one name per author; editorial boards as "<Outlet> Editorial Board"; titles shown with the story |

Unchanged on purpose: `vals('author')`, `authorRank`, `reporterBars`, facet counts all read `r.authors`, so the Reporter filter list, the Trends bars and the report "most stories" line become per-person with no further edits.

## 3b. Author kinds + folded "Staff bylines" group (Sammy, 2026-10-27)
- Data: build_data adds `akinds` (list parallel to `authors`): person | board | staff | wire | org, from `authorsplit.author_kind()`. The JS reads it and does not guess from the text. The sheet is unchanged; author_split.csv has a matching `author_kinds` column.
  - board = Editorial Board / Editorial Staff / Editorial Team / Editors → normal filter entries.
  - staff = generic staff groups ("<Outlet> Staff", News Staff, Newsroom, Desk, Staff and Wire Reports, Staff Report) → folded.
  - Today's split: 6,490 person, 119 org, 85 staff, 76 wire, 63 board author values.
- JS (4 more anchored edits, now 19 in total): `AKIND` map + `isStaffAuthor()` + `staffGroup()`. In the Reporter facet, staff entries leave the main list (and the "Show all N" count) and go into one nested `<details data-facet="author-staff">` "Staff bylines" at the end. It is collapsed by default (opens while a facet search matches, or once the user opens it; it uses the existing openFacets toggle handler), and each entry is a normal checkbox with its count. On cards, rows and the detail panel, staff bylines stay normal links. A one-rule style tag is injected for the nested group.
- Composes with code/patch_links.py in either order: byte-identical JS and build_data.

## 4. Tests run (all on copies)
- Group/kind tests added to T/test_authors.js (now 23): the Staff bylines group exists, is collapsed and comes last; it holds every staff byline with its count; no staff byline is in the main list; boards stay in the main list; a staff entry inside the group can be selected and filters (summary "1 on"); a staff byline is a normal link on the row and in the detail. 23/23 on the authors-only page and 23/23 on the links+authors page.
- links+authors page: links suite 23/23; display suite 17/18. The one failure ("empty reach") also fails with the links patch alone on the same blocks: the case's story now has a Reach value in the current workbook, so it is a stale test case, not code. On the old blocks the display suite is 18/18.

- Parser cases (spec list): "By X and Y", "X, Y and Z", "X | Staff Writer", "X, Special to the Times", "X / Associated Press", "Staff and wire reports", "Editorial Board", "The Times Editorial Board", "Opinion: …", ALL-CAPS names, duplicated names, trailing emails, "Consejo editorial", "Redacción/…", glued "NameTitle" (ws-02922 → Joyann Jeffrey / Trending News Reporter): T/t.py, all as intended.
- Workbook (T/test_cols.py + patched apply_fills on coverage_current.xlsx): 0 existing cells changed on either tab, other tabs identical, columns at Y–AG on both tabs, autofilter A1:BK…, Originals mirror Coverage, 5,979 Coverage rows / 2,682 Originals rows written, 0 rows disagree with out/author_split.csv. Second pass: only the newly-bylined blank row written; a 9-author row reported in needs_more_columns. migrate_ids.py on the result: 0 problems (9,761 ids paired).
- build_data: workbook with Author columns vs the same workbook parsed by the fallback: identical `authors`/`atitle` on all 3,899 stories; every other field identical to the unpatched build.
- Browser (T/test_authors.js, playwright, real data): **16/16** — co-written story jg-02083 shows "Brett Stover", "Eytan Wallace" as two links; Brett Stover's link → his 4 stories (3 solo + jg-02083), Eytan Wallace's → his 4 (3 solo + jg-02083); facet lists each once with full count; "Jeremy B. White"/"Jeremy B White" = one option (33); "Los Angeles Times Editorial Board" is a normal option; 1,374 options, none combined "X and Y", no two share a key; card link filters without opening the viewer; detail shows "(Staff Writer)"; no page errors. Existing display suite on the patched page: **18/18**.

## 5. Follow-ups for other owners
- sheet task (sheet_task.py, agent-ids): rows it appends get only "Author / byline"; the tracker still splits them (build_data fallback), and the next apply_fills run fills their Author columns. Optionally call `authorsplit.parse_byline` when appending.
- Update button proposed rows carry the new covcols; Author N / Author title stay blank there (filled by the next apply_fills pass).
- When T24 resumes (TinyFish, up to 846 rows): re-run `python3 -I T/run_split.py L` to refresh out/author_split.csv + review items; apply_fills fills the new rows' columns.
