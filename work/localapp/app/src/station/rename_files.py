"""rename_files.py: RENAME-v1. Bring library file names (and the File name / File name 2 / Other files cells that name them) up to NAMING-v2.

NAMING-v2: a saved copy is `<nb|pq|ws><Article ID><o|r>-s<Story ID>[-suffix].<html|pdf>` (o = the row is an Original, r = a Reprint). A file belongs to the row whose
Article ID (or, for a print file, Print Article ID) is in its name. After merges and swaps a row's Story ID or role changes and the old name goes stale.

This module only PLANS (read only) and moves files; the workbook is changed by switchover.run_cell_step (backup, staged copy, cell-by-cell check, swap, ledger).

  plan(lay, only_aids=None)  -> {renames: [...], changes: [cell changes], collisions, shared, missing, unnamed, counts, digest, lines}
  move_files(lay, plan)      -> the files (and their _original_html raw page and .ocr.txt partner) moved together; a journal makes it undoable
  undo(journal)              -> puts every moved file back
  write_list(lay, plan, stamp) -> the old -> new list, a new file in <library>/_renamed/

Rules: nothing is deleted. A name that is already right, text that is not a file name (BLOCKED, RETRY), a cell that names another row's file (a shared copy: it is left
alone, but follows the file if the owning row's file is renamed), a file that is not in the library, or a file whose new name already exists (collision) is not renamed and is
listed. Standard library plus openpyxl.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

COVERAGE, ORIGINALS = 'Coverage', 'Originals'
FILE_COLS = ('File name', 'File name 2', 'Other files')
NAME_RX = re.compile(r'^(?P<fmt>nb|pq|ws)(?P<aid>\d{5})(?P<oor>[or])?(?:-(?P<sid>s\d{5}))?(?P<suf>(?:-[A-Za-z0-9]+)*)\.(?P<ext>html|pdf)$')
YEAR_RX = re.compile(r'^(\d{4}|undated)$')
LIST_DIR = '_renamed'


def _s(v) -> str:
    return '' if v is None else str(v).strip()


def read_rows(wb_path: Path, tabs=(COVERAGE, ORIGINALS)) -> dict:
    import openpyxl
    wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)
    try:
        out = {}
        for t in tabs:
            if t not in wb.sheetnames:
                continue
            it = wb[t].iter_rows(values_only=True)
            hdr = [_s(c) for c in next(it, [])]
            out[t] = (hdr, [(i, dict(zip(hdr, r))) for i, r in enumerate(it, start=2) if r and _s(r[0])])
        return out
    finally:
        wb.close()


def story_roles(wb_path: Path) -> dict:
    """{Article ID: (Story ID, Original or reprint)} of the Coverage tab: what the save compares before and after to find rows whose story or role changed"""
    t = read_rows(wb_path, (COVERAGE,)).get(COVERAGE)
    return {_s(d['Article ID']): (_s(d.get('Story ID')), _s(d.get('Original or reprint'))) for _, d in (t[1] if t else [])}


def library_index(lib: Path) -> dict:
    """{file name: [year folder, ...]} of the schema-named files directly inside the year folders (not _original_html and the like)"""
    idx = {}
    if not lib.is_dir():
        return idx
    for y in sorted(lib.iterdir()):
        if not (y.is_dir() and YEAR_RX.match(y.name)):
            continue
        with os.scandir(y) as it:
            for e in it:
                if e.is_file() and not e.name.startswith('.'):       # MAC-JUNK: .DS_Store and ._ files
                    idx.setdefault(unicodedata.normalize('NFC', e.name), []).append(y.name)       # MAC-NFC
    return idx


def entries(cell) -> list:
    return [x.strip() for x in _s(cell).split(';') if x.strip()]


def correct_name(name: str, row: dict):
    """(status, new name). status: ok | stale | foreign (names another row's file) | other (not a schema name) | unsure"""
    m = NAME_RX.match(name)
    if not m:
        return 'other', name
    aid = m.group('aid')
    if aid not in (_s(row.get('Article ID')), _s(row.get('Print Article ID'))):
        return 'foreign', name
    sid, orr = _s(row.get('Story ID')), _s(row.get('Original or reprint'))
    if not re.fullmatch(r's\d{5}', sid):
        return ('ok', name) if not m.group('sid') else ('unsure', name)
    if orr not in ('Original', 'Reprint'):
        return 'unsure', name
    new = f"{m.group('fmt')}{aid}{'o' if orr == 'Original' else 'r'}-{sid}{m.group('suf')}.{m.group('ext')}"
    return ('ok' if new == name else 'stale'), new


def plan(lay, only_aids=None) -> dict:
    """only_aids: plan only for rows with these Article IDs (the save: rows whose story or role just changed). None = every row (switch-over)."""
    recover_pending(lay)
    tabs = read_rows(lay.workbook)
    cov = tabs.get(COVERAGE)
    if not cov:
        return _empty()
    idx = library_index(lay.library)
    counts = {'ok': 0, 'stale': 0, 'shared': 0, 'other': 0, 'missing': 0, 'unsure': 0, 'ambiguous': 0, 'cells': 0}
    cand = {}                                   # old -> {new, aids}
    shared, missing, unsure, ambiguous = [], [], [], []
    named = set()
    for _, d in cov[1]:
        aid = _s(d.get('Article ID'))
        for col in FILE_COLS:
            for nm in entries(d.get(col)):
                named.add(nm)
                st, new = correct_name(nm, d)
                if only_aids is not None and aid not in only_aids and st != 'foreign':
                    continue
                if st == 'other':
                    counts['other'] += 1
                elif st == 'foreign':
                    counts['shared'] += 1
                    if len(shared) < 400:
                        shared.append({'aid': aid, 'col': col, 'name': nm})
                elif st == 'unsure':
                    counts['unsure'] += 1
                    unsure.append({'aid': aid, 'col': col, 'name': nm})
                elif st == 'ok':
                    counts['ok'] += 1
                else:
                    c = cand.setdefault(nm, {'new': set(), 'aids': set()})
                    c['new'].add(new)
                    c['aids'].add(aid)
    for tab in (ORIGINALS,):
        if tab in tabs:
            for _, d in tabs[tab][1]:
                for col in FILE_COLS:
                    named.update(entries(d.get(col)))
    renames, collisions = [], []
    taken = {}                                  # new name -> old name that wants it
    for old in sorted(cand):
        c = cand[old]
        if len(c['new']) > 1:
            collisions.append({'old': old, 'new': sorted(c['new']), 'why': 'two rows disagree about the right name', 'aids': sorted(c['aids'])})
            continue
        new = next(iter(c['new']))
        yrs = idx.get(old, [])
        if not yrs:
            counts['missing'] += 1
            missing.append({'old': old, 'new': new, 'aids': sorted(c['aids'])})
            continue
        if len(yrs) > 1:
            counts['ambiguous'] += 1
            ambiguous.append({'old': old, 'folders': yrs})
            continue
        taken.setdefault(new, []).append(old)
        renames.append({'old': old, 'new': new, 'year': yrs[0], 'aids': sorted(c['aids'])})
    final = renames
    while True:                                 # dropping a file can free or block another one (A -> B while B -> C): repeat until nothing changes
        olds = {r['old'] for r in final}
        srcs = {str(src) for r in final for src, _ in _groups(lay, r)}
        want = {}
        for r in final:
            want.setdefault(r['new'], []).append(r['old'])
        keep = []
        for r in final:
            why = ''
            if len(want[r['new']]) > 1:
                why = 'another file wants the same new name'
            elif r['new'] in idx and r['new'] not in olds:
                why = 'a file with the new name already exists in the library'
            elif any(dst.exists() and str(dst) not in srcs for _, dst in _groups(lay, r)):
                why = 'a partner file (raw page or OCR text) with the new name already exists'
            if why:
                collisions.append({'old': r['old'], 'new': [r['new']], 'why': why, 'aids': r['aids']})
            else:
                keep.append(r)
        if len(keep) == len(final):
            break
        final = keep
    mapping = {r['old']: r['new'] for r in final}
    changes = []
    for tab in (COVERAGE, ORIGINALS):
        if tab not in tabs:
            continue
        hdr = tabs[tab][0]
        for ri, d in tabs[tab][1]:
            sets, expect = {}, {}
            for col in FILE_COLS:
                if col not in hdr:
                    continue
                es = entries(d.get(col))
                if any(e in mapping for e in es):
                    new_es = [mapping.get(e, e) for e in es]
                    sets[col] = '; '.join(new_es)
                    expect[col] = _s(d.get(col))
            if sets:
                changes.append(dict(tab=tab, row=ri, aid=_s(d.get('Article ID')), set=sets, expect=expect))
                counts['cells'] += len(sets)
    unnamed = sorted(n for n in idx if NAME_RX.match(n) and n not in named and n not in mapping.values())
    counts.update(stale=len(final), collisions=len(collisions), unnamed=len(unnamed))
    lines = []
    if final:
        lines.append(f'{len(final)} saved files get the right name (their raw page and OCR text move with them): {counts["cells"]} cells on Coverage and Originals change to match.')
        ex = final[:3]
        lines.append('For example: ' + '; '.join(f'{r["old"]} -> {r["new"]}' for r in ex) + '.')
    else:
        lines.append('Every saved file already has the right name.')
    lines.append(f'{counts["ok"]} names are already right; {counts["shared"]} cells name another row\'s file (a shared copy: left as it is, and it follows the file if that file is renamed).')
    if collisions:
        lines.append(f'{len(collisions)} files are NOT renamed because the new name is taken or the rows disagree (listed in the rename list): ' +
                     '; '.join(f'{c["old"]} ({c["why"]})' for c in collisions[:3]) + (' ...' if len(collisions) > 3 else '') + '.')
    if missing:
        lines.append(f'{len(missing)} files named in the workbook are not in the library: left as they are.')
    if ambiguous:
        lines.append(f'{len(ambiguous)} names exist in more than one year folder: left as they are.')
    if unnamed:
        lines.append(f'{len(unnamed)} schema-named library files are named by no row: listed, not touched.')
    lines.append('Nothing is deleted. The old and new names are written to a list in the library.')
    digest = hashlib.sha256(json.dumps([[r['old'], r['new'], r['year']] for r in final], sort_keys=True).encode()).hexdigest()[:16]
    return {'renames': final, 'changes': changes, 'collisions': collisions, 'shared': shared, 'missing': missing, 'ambiguous': ambiguous, 'unsure': unsure, 'unnamed': unnamed,
            'counts': counts, 'lines': lines, 'digest': digest, 'n': len(final)}


def _empty():
    return {'renames': [], 'changes': [], 'collisions': [], 'shared': [], 'missing': [], 'ambiguous': [], 'unsure': [], 'unnamed': [], 'counts': {}, 'lines': ['No Coverage tab.'],
            'digest': '', 'n': 0}


# ---------------------------------------------------------------- moving files

def _groups(lay, r) -> list:
    """[(src, dst)] for one rename: the saved copy, its raw page in _original_html, its OCR text. Missing partners are simply not moved."""
    lib, y, old, new = Path(lay.library), r['year'], r['old'], r['new']
    out = [(lib / y / old, lib / y / new)]
    raw = lib / '_original_html' / y / old
    if raw.is_file():
        out.append((raw, lib / '_original_html' / y / new))
    ocr = lib / y / (Path(old).stem + '.ocr.txt')
    if ocr.is_file():
        out.append((ocr, lib / y / (Path(new).stem + '.ocr.txt')))
    return out


def move_files(lay, pl: dict, journal_path: Path) -> list:
    """Two phases (old -> temporary -> new) so a swap (A -> B while B -> C) cannot collide. The journal is written first; on any error everything done is undone."""
    moves = [m for r in pl['renames'] for m in _groups(lay, r)]
    for src, dst in moves:
        if not src.is_file():
            raise OSError(f'{src} is not there')
    journal = [{'src': str(s), 'tmp': str(s.with_name(s.name + f'.rn{i}')), 'dst': str(d), 'state': 'planned'} for i, (s, d) in enumerate(moves)]
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    _save(journal_path, journal)
    every = 1 if len(journal) <= 400 else 20      # REVIEW_3 finding 4: the journal is saved as the moves happen (every move for a normal list); recover() also reads the disk itself
    try:
        k = 0
        for ph, nxt in (('src', 'tmp'), ('tmp', 'dst')):
            for j in journal:
                if Path(j[nxt]).exists():
                    raise OSError(f'{j[nxt]} exists')
                os.rename(j[ph], j[nxt])
                j['state'] = 'tmp' if nxt == 'tmp' else 'done'
                k += 1
                if k % every == 0:
                    _save(journal_path, journal)
        _save(journal_path, journal)
    except Exception:
        undo(journal)
        _save(journal_path, journal)
        raise
    return journal


def recover(journal_path: Path) -> int:
    """after a crash in move_files (some files under temporary .rnN names): put every file of that journal back under its old name, judging by what is on the disk (the saved
    journal may be a few moves behind). Does nothing when no temporary file is left. Returns the number of files put back."""
    try:
        journal = json.loads(Path(journal_path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return 0
    if not any(Path(j['tmp']).exists() for j in journal):
        return 0       # finished (the workbook step comes after the last move) or never started
    n = 0
    for j in reversed(journal):
        src, tmp, dst = Path(j['src']), Path(j['tmp']), Path(j['dst'])
        if src.exists():
            continue
        if tmp.exists():
            os.rename(tmp, src)
        elif dst.exists():
            os.rename(dst, src)
        else:
            continue
        j['state'] = 'undone'
        n += 1
    _save(Path(journal_path), journal)
    return n


def recover_pending(lay) -> int:
    n = 0
    for jp in sorted(Path(lay.state).glob('rename_journal_*.json')):
        n += recover(jp)
    return n


def undo(journal: list) -> None:
    for j in reversed(journal):
        if j['state'] == 'done' and Path(j['dst']).exists() and not Path(j['src']).exists():
            os.rename(j['dst'], j['src'])
            j['state'] = 'undone'
        elif j['state'] == 'tmp' and Path(j['tmp']).exists() and not Path(j['src']).exists():
            os.rename(j['tmp'], j['src'])
            j['state'] = 'undone'


def _save(p: Path, obj) -> None:
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(json.dumps(obj, indent=1), encoding='utf-8')
    os.replace(tmp, p)


def write_list(lay, pl: dict, stamp: str, why: str) -> Path:
    """the old -> new list, a new file in <library>/_renamed/ (never replaces anything); collisions and unnamed files are listed after the renames"""
    d = Path(lay.library) / LIST_DIR
    d.mkdir(parents=True, exist_ok=True)
    p = d / f'renamed {stamp}.csv'
    n = 1
    while p.exists():
        n += 1
        p = d / f'renamed {stamp} ({n}).csv'
    with open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['result', 'folder', 'old name', 'new name', 'article ids / note'])
        for r in pl['renames']:
            w.writerow(['renamed', r['year'], r['old'], r['new'], ' '.join(r['aids'])])
        for c in pl['collisions']:
            w.writerow(['NOT renamed', '', c['old'], ' | '.join(c['new']), c['why']])
        for m in pl['missing']:
            w.writerow(['not in library', '', m['old'], m['new'], ' '.join(m['aids'])])
        for a in pl['ambiguous']:
            w.writerow(['in several folders', ' '.join(a['folders']), a['old'], '', ''])
        for u in pl['unnamed']:
            w.writerow(['named by no row', '', u, '', ''])
        w.writerow(['why', why, '', '', ''])
    return p
