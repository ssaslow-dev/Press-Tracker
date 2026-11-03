"""saver_diff.py: independent cell-by-cell comparison of two workbooks against the save allow-list (SAVER_SPEC section 6).

It is IN ADDITION to sheet_task.verify / verify_tabs, never a replacement. It imports nothing from the pipeline: the two constants it
needs from sheet_task.py (the Press releases derived columns, the tabs a run may add rows to) are passed in by the caller, who reads
them from sheet_task.py's source (saver_steps.read_sheet_task_constants), so the list is never copied here.

Public API
    read_book(path)                      -> Book
    compare(before, after, result, result2, derived_rel=..., new_ok=...) -> DiffReport
    DiffReport.tsv_text(), .summary(), .refusal()
    preview_token(run_id, before_sha, tsv_text)

Kinds in the report: added (cell of a new row), filled (blank -> value), changed (a non-blank value differs, or is cleared),
missing (a row of `before` has no row in `after`), moved (a missing row that went to the Removed tab, allowed).
A change is allowed only when `allowed_by` is set; everything else is listed in report.problems and the caller refuses.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path

COVERAGE = 'Coverage'
ORIGINALS = 'Originals'
AV_TAB = 'Audio & video details'
REMOVED = 'Removed'
PRESS = 'Press releases'
REPRINT_COL = '# of reprints'

# result.json keys that can introduce a new Coverage Article ID (SPEC section 6 / section 11 open point). Confirmed against the
# runsave replay: every new Coverage ID is a value of runs[*].ids or a member of runs[*].added. The other keys are the spec's list
# and are collected for the same purpose; they are empty in that fixture, so they are NOT confirmed by any replay.
ID_LIST_KEYS = ('origin_added', 'origin_nocopy', 'nocopy_finds', 'agg_origin', 'releases_new', 'releases_flagged', 'releases_skipped',
                'releases_untestable', 'releases_review', 'releases_unmarked', 'releases_dual', 'release_copies')
ID_FIELDS = ('aid', 'new_original')
AID_RE = re.compile(r'^\d{5}$')

REFUSAL_PRIORITY = ('OVERWRITE', 'ROWCOUNT', 'FOREIGN_ROW')

# ---------------------------------------------------------------- reading


def blank(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == '')


def _canon(v):
    """a value for equality: integral floats are ints; strings are kept exactly (a whitespace edit is a change, on purpose)"""
    if isinstance(v, bool):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def same(a, b) -> bool:
    if blank(a) and blank(b):
        return True
    if blank(a) or blank(b):
        return False
    if isinstance(a, bool) != isinstance(b, bool):   # Python's True == 1; a TRUE cell rewritten as 1 is a change
        return False
    return _canon(a) == _canon(b)


def text(v) -> str:
    if v is None:
        return ''
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if hasattr(v, 'strftime'):
        try:
            return v.strftime('%Y-%m-%d') if getattr(v, 'hour', 0) == 0 and getattr(v, 'minute', 0) == 0 else v.isoformat(sep=' ')
        except ValueError:
            pass
    return re.sub(r'\s+', ' ', str(v)).strip()


@dataclass
class Sheet:
    name: str
    header: list
    rows: list          # [(excel row number, tuple of values)] non-blank rows only, header excluded
    links: dict = field(default_factory=dict)   # excel row number -> {0-based column index: link target}


@dataclass
class Book:
    path: str
    names: list
    sheets: 'OrderedDict[str, Sheet]'


_TAG = re.compile(rb'<hyperlink\b[^>]*>')
_ATTR = re.compile(rb'\b([\w:]+)="([^"]*)"')


def _col_index(letters: bytes) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ch - 64)
    return n - 1


def _hyperlinks(path) -> dict:
    """{sheet name: {row: {col index: target}}} from the sheet XML and its relationships (read-only openpyxl does not expose hyperlinks).
    target = the relationship Target (external URL) or '#' + location (internal link)."""
    out = {}
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        wbx = z.read('xl/workbook.xml').decode('utf-8', 'ignore')
        rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8', 'ignore')
        tgt = {}
        for m in re.finditer(r'<Relationship\b[^>]*>', rels):
            t = m.group(0)
            i, g = re.search(r'\bId="([^"]+)"', t), re.search(r'\bTarget="([^"]+)"', t)
            if i and g:
                tgt[i.group(1)] = g.group(1)
        for m in re.finditer(r'<sheet\b[^>]*>', wbx):
            t = m.group(0)
            n, r = re.search(r'\bname="([^"]*)"', t), re.search(r'\br:id="([^"]+)"', t)
            if not (n and r and r.group(1) in tgt):
                continue
            tp = tgt[r.group(1)]
            tp = tp.lstrip('/') if tp.startswith('/') else 'xl/' + tp
            relp = tp.rsplit('/', 1)[0] + '/_rels/' + tp.rsplit('/', 1)[1] + '.rels'
            srel = {}
            if relp in names:
                for rm in re.finditer(r'<Relationship\b[^>]*>', z.read(relp).decode('utf-8', 'ignore')):
                    rt = rm.group(0)
                    i, g = re.search(r'\bId="([^"]+)"', rt), re.search(r'\bTarget="([^"]*)"', rt)
                    if i and g:
                        srel[i.group(1)] = unescape(g.group(1))
            rows: dict = {}
            for h in _TAG.finditer(z.read(tp)):
                at = {k.decode(): unescape(v.decode('utf-8', 'ignore')) for k, v in _ATTR.findall(h.group(0))}
                cell = re.match(r'([A-Z]+)(\d+)', at.get('ref', ''))
                if not cell:
                    continue
                target = srel.get(at.get('r:id', ''), '') or (('#' + at['location']) if at.get('location') else '')
                rows.setdefault(int(cell.group(2)), {})[_col_index(cell.group(1).encode())] = target
            out[unescape(n.group(1))] = rows
    return out


def read_book(path) -> Book:
    import openpyxl
    path = str(path)
    links = _hyperlinks(path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=False)
    try:
        sheets: 'OrderedDict[str, Sheet]' = OrderedDict()
        for ws in wb.worksheets:
            it = ws.iter_rows(values_only=True)
            hdr = list(next(it, ()))
            while hdr and blank(hdr[-1]):
                hdr.pop()
            rows = []
            for i, r in enumerate(it, start=2):
                if all(blank(c) for c in r):
                    continue
                rows.append((i, tuple(r)))
            sheets[ws.title] = Sheet(ws.title, hdr, rows, links.get(ws.title, {}))
        return Book(path, list(wb.sheetnames), sheets)
    finally:
        wb.close()


# ---------------------------------------------------------------- allow-list from the run results


@dataclass
class Allow:
    reprint_new: dict          # story id -> recorded new count (or None)
    swap_cells: set            # (aid, column)
    swap_old_aids: set
    retry_cells: set
    queue_cells: set
    removed_aids: set
    assigned_ids: set          # Article IDs sheet_task assigned this run
    removed_rows_n: int
    yt_cells: set = field(default_factory=set)       # (aid, column): Format / Medium of a story that became a broadcast story (YTBROADCAST-v1)
    yt_item_aids: set = field(default_factory=set)   # aid whose Audio & video details Item type became "Broadcast segment" (YTBROADCAST-v1)
    other_files: dict = field(default_factory=dict)  # aid -> [file names sheet_task appended to "Other files" this run] (OTHERFILES-v1)

    @classmethod
    def from_results(cls, *results) -> 'Allow':
        rc, swap, swap_old, retry, queue, removed, assigned = {}, set(), set(), set(), set(), set(), set()
        yt_cells, yt_item = set(), set()
        other = {}
        n_removed = 0
        for res in results:
            res = res or {}
            for sid, v in (res.get('reprint_counts') or {}).items():
                rc[str(sid)] = (v or {}).get('new') if isinstance(v, dict) else None
            for e in res.get('origin_swaps') or []:
                for aid, col in e.get('cells') or []:
                    swap.add((str(aid), col))
                if e.get('old_original'):
                    swap_old.add(str(e['old_original']))
            for x in res.get('retry_cleared') or []:
                for col in ('File name', 'Saved Copy?'):
                    retry.add((str(x.get('aid')), col))
            for e in res.get('yt_attached') or []:   # YTSTATION-v1 / YTBROADCAST-v1: sheet_task.apply_yt_attach lists the cells it overrode
                for col in e.get('cells') or []:
                    yt_cells.add((str(e.get('aid')), col))
                if any(str(x).startswith('AV Item type') for x in e.get('changed') or []):
                    yt_item.add(str(e.get('aid')))
            for e in res.get('other_files') or []:   # OTHERFILES-v1: sheet_task.apply_extra_copies lists the names it appended
                lst = other.setdefault(str(e.get('aid')), [])
                lst.extend(str(n) for n in e.get('names') or [] if str(n) not in lst)   # pass 1 and pass 2 report the same append: counted once
            for e in res.get('queue_applied') or []:
                for aid, col in e.get('cells') or []:
                    queue.add((str(aid), col))
            for e in res.get('removed') or []:
                for x in e.get('rows') or []:
                    if x.get('aid'):
                        removed.add(str(x['aid']))
                        n_removed += 1
            for v in (res.get('runs') or {}).values():
                for k in ((v or {}).get('ids') or {}).values():
                    if AID_RE.match(str(k)):
                        assigned.add(str(k))
                assigned.update(str(a) for a in (v or {}).get('added') or [])
            for key in ID_LIST_KEYS:
                for x in res.get(key) or []:
                    if isinstance(x, dict):
                        for f in ID_FIELDS:
                            if x.get(f):
                                assigned.add(str(x[f]))
            for e in res.get('origin_swaps') or []:
                if e.get('new_original'):
                    assigned.add(str(e['new_original']))
        return cls(rc, swap, swap_old, retry, queue, removed, assigned, n_removed, yt_cells, yt_item, other)


# ---------------------------------------------------------------- report


@dataclass
class Change:
    sheet: str
    row: int
    key: str
    column: str
    kind: str
    old: object
    new: object
    allowed_by: str      # '' = not allowed

    def tsv(self):
        def c(v):
            return text(v)[:300].replace('\t', ' ')
        return '\t'.join([self.sheet, str(self.row), self.key.replace('\t', ' '), self.column.replace('\t', ' '), self.kind,
                          c(self.old), c(self.new), self.allowed_by or 'NOT_ALLOWED'])


@dataclass
class Problem:
    code: str            # OVERWRITE | ROWCOUNT | FOREIGN_ROW
    kind: str            # finer label
    text: str


@dataclass
class DiffReport:
    changes: list = field(default_factory=list)
    problems: list = field(default_factory=list)
    rows_before: dict = field(default_factory=dict)
    rows_after: dict = field(default_factory=dict)
    sheets_before: list = field(default_factory=list)
    sheets_after: list = field(default_factory=list)

    def add_problem(self, code, kind, text_):
        self.problems.append(Problem(code, kind, text_))

    def disallowed(self):
        return [c for c in self.changes if not c.allowed_by]

    def tsv_text(self) -> str:
        head = 'sheet\trow\tkey\tcolumn\tkind\told\tnew\tallowed_by'
        return head + '\n' + '\n'.join(c.tsv() for c in self.changes) + ('\n' if self.changes else '')

    def summary(self) -> dict:
        added, filled, changed = Counter(), Counter(), Counter()
        rows_added = Counter()
        seen_rows = set()
        touched = []
        for c in self.changes:
            if c.kind == 'added':
                if (c.sheet, c.key) not in seen_rows:
                    seen_rows.add((c.sheet, c.key))
                    rows_added[c.sheet] += 1
            elif c.kind == 'filled':
                filled[c.sheet] += 1
            elif c.kind in ('changed', 'moved', 'missing'):
                changed[c.allowed_by or 'NOT_ALLOWED'] += 1
            if c.sheet not in touched:
                touched.append(c.sheet)
        return {'rows_added': dict(rows_added), 'cells_filled': dict(filled), 'cells_changed': dict(changed),
                'tabs_touched': touched, 'lines': len(self.changes), 'disallowed': len(self.disallowed())}

    def refusal(self):
        """(code, text, detail) for the highest-priority problem, or None"""
        if not self.problems:
            return None
        by = {}
        for p in self.problems:
            by.setdefault(p.code, []).append(p)
        code = next(c for c in REFUSAL_PRIORITY if c in by)
        ps = by[code]
        shown = '; '.join(p.text for p in ps[:20])
        more = f' (+{len(ps) - 20} more, all in diff.tsv or the detail)' if len(ps) > 20 else ''
        return code, shown + more, {'problems': [{'code': p.code, 'kind': p.kind, 'text': p.text} for p in self.problems[:200]],
                                    'n_problems': len(self.problems)}


def preview_token(run_id: str, before_sha: str, tsv_text: str) -> str:
    return hashlib.sha256((run_id + before_sha + hashlib.sha256(tsv_text.encode('utf-8')).hexdigest()).encode('utf-8')).hexdigest()[:16]


# ---------------------------------------------------------------- the comparison


def _col_labels(header):
    seen = Counter()
    out = []
    for i, h in enumerate(header):
        lab = text(h) if not blank(h) else f'#{i + 1}'
        seen[lab] += 1
        out.append(lab if seen[lab] == 1 else f'{lab} #{seen[lab]}')
    return out


def _key_cols(name, header):
    hi = {}
    for i, h in enumerate(header):
        if not blank(h) and text(h) not in hi:
            hi[text(h)] = i
    if name == PRESS:
        return [hi['Release ID']] if 'Release ID' in hi else [], hi.get('URL')
    if 'Article ID' in hi:
        return [hi['Article ID']], None
    return list(range(min(4, len(header)))), None


def _keyed(sheet: Sheet):
    """{key tuple: (row number, values)} in sheet order. Duplicate keys are numbered in order (as sheet_task does); rows with no key
    are matched by their order among the keyless rows (a shift then shows as a change, which is the safe side)."""
    kc, url_col = _key_cols(sheet.name, sheet.header)
    seen = Counter()
    out = OrderedDict()
    for rn, vals in sheet.rows:
        k = tuple(text(vals[i]) if i < len(vals) else '' for i in kc)
        if (not any(k)) and url_col is not None:
            k = (text(vals[url_col]) if url_col < len(vals) else '',)
        if not any(k):
            k = ('<no key>',)
        seen[k] += 1
        out[k + (seen[k] - 1,)] = (rn, vals)
    return out


def _klabel(k) -> str:
    return '/'.join(x for x in k[:-1] if x) + (f'#{k[-1]}' if k[-1] else '')


def compare(before, after, result=None, result2=None, *, derived_rel, new_ok) -> DiffReport:
    """before / after: paths or Book objects. derived_rel / new_ok: sheet_task's VT_DERIVED_REL and VT_NEW_OK, supplied by the caller."""
    B = before if isinstance(before, Book) else read_book(before)
    A = after if isinstance(after, Book) else read_book(after)
    allow = Allow.from_results(result, result2)
    derived_rel, new_ok = set(derived_rel), set(new_ok)
    rep = DiffReport(sheets_before=list(B.names), sheets_after=list(A.names))

    # --- tabs
    for n in B.names:
        if n not in A.sheets:
            rep.add_problem('OVERWRITE', 'tab_missing', f'tab missing after: {n!r}')
    added_tabs = [n for n in A.names if n not in B.sheets]
    for n in added_tabs:
        if n not in new_ok:
            rep.add_problem('OVERWRITE', 'tab_added', f'tab added that a run may not create: {n!r}')
    ob = [n for n in B.names if n in A.sheets and n != ORIGINALS]
    oa = [n for n in A.names if n in B.sheets and n != ORIGINALS]
    if ob != oa:
        rep.add_problem('OVERWRITE', 'tab_order', f'tab order changed: {ob} -> {oa}')

    # Coverage facts the other tabs lean on
    cov_after_originals = []
    cov_after_aids = set()
    removed_on_tab = set()
    removed_before = Counter()      # Article ID / Print Article ID -> number of Removed rows before
    removed_after = Counter()
    removed_rows_after = {}         # aid -> [(values, link targets)] on the after Removed tab
    if COVERAGE in A.sheets:
        s = A.sheets[COVERAGE]
        hi = {text(h): i for i, h in enumerate(s.header) if not blank(h)}
        ai, oi = hi.get('Article ID'), hi.get('Original or reprint')
        for _, v in s.rows:
            if ai is not None and ai < len(v):
                cov_after_aids.add(text(v[ai]))
                if oi is not None and oi < len(v) and text(v[oi]) == 'Original':
                    cov_after_originals.append(text(v[ai]))
    if REMOVED in A.sheets:
        s = A.sheets[REMOVED]
        hi = {text(h): i for i, h in enumerate(s.header) if not blank(h)}
        for col in ('Article ID', 'Print Article ID'):
            if col in hi:
                removed_on_tab |= {text(v[hi[col]]) for _, v in s.rows if hi[col] < len(v) and not blank(v[hi[col]])}
        for rn, v in s.rows:
            for col in ('Article ID', 'Print Article ID'):
                if col in hi and hi[col] < len(v) and not blank(v[hi[col]]):
                    removed_after[text(v[hi[col]])] += 1
                    removed_rows_after.setdefault(text(v[hi[col]]), []).append((v, set(s.links.get(rn, {}).values())))
    if REMOVED in B.sheets:
        s = B.sheets[REMOVED]
        hi = {text(h): i for i, h in enumerate(s.header) if not blank(h)}
        for _, v in s.rows:
            for col in ('Article ID', 'Print Article ID'):
                if col in hi and hi[col] < len(v) and not blank(v[hi[col]]):
                    removed_before[text(v[hi[col]])] += 1
    cov_before_aids = set()
    if COVERAGE in B.sheets:
        s = B.sheets[COVERAGE]
        ai = {text(h): i for i, h in enumerate(s.header) if not blank(h)}.get('Article ID')
        cov_before_aids = {text(v[ai]) for _, v in s.rows if ai is not None and ai < len(v)}

    for name in B.names:
        if name not in A.sheets:
            continue
        sb, sa = B.sheets[name], A.sheets[name]
        rep.rows_before[name], rep.rows_after[name] = len(sb.rows), len(sa.rows)
        if sb.header != sa.header:
            rep.add_problem('OVERWRITE', 'header_changed', f'{name}: header row changed ({len(sb.header)} -> {len(sa.header)} columns)'
                            + ('' if sa.header else ', header row lost'))
            if not sa.header or len(sb.header) != len(sa.header):
                continue   # the columns no longer line up; cell comparison would be noise
        labels = _col_labels(sb.header)
        hi = {text(h): i for i, h in enumerate(sb.header) if not blank(h)}
        si = hi.get('Story ID')
        kb, ka = _keyed(sb), _keyed(sa)
        _link_problems(rep, name, 'header row', labels, sb.links.get(1, {}), sa.links.get(1, {}))
        common = set(kb) & set(ka)
        if [k for k in kb if k in common] != [k for k in ka if k in common]:
            rep.add_problem('OVERWRITE', 'row_order', f'{name}: rows present before and after are in a different order')
        is_cov = name in (COVERAGE, ORIGINALS)
        width_h = len(sb.header)

        for k, (rn, bvals) in kb.items():
            key = _klabel(k)
            aid = k[0]
            story = text(bvals[si]) if si is not None and si < len(bvals) else ''
            if k not in ka:
                tag = ''
                landed = aid in removed_on_tab and removed_after[aid] > removed_before[aid]   # a Removed row that was not there before
                if name in (COVERAGE, AV_TAB, ORIGINALS) and aid in allow.removed_aids and landed:
                    tag = 'removed_move'
                elif name == ORIGINALS and aid in cov_after_aids and aid not in cov_after_originals:
                    tag = 'originals_mirror'   # no longer an Original on Coverage; that change is classified on the Coverage tab
                kind = 'moved' if tag == 'removed_move' else 'missing'
                rep.changes.append(Change(name, rn, key, '(row)', kind, key, '', tag))
                if not tag:
                    rep.add_problem('OVERWRITE', 'row_missing', f'{name}: row missing after: {key}')
                elif tag == 'removed_move' and name == COVERAGE:
                    # SAVE_RULES: a hyperlink may not go missing. Its target must reach the Removed row, as a link or as the cell's text.
                    for col, target in sorted(sb.links.get(rn, {}).items()):
                        carried = any(target in links or any(text(x) == target for x in vals) for vals, links in removed_rows_after.get(aid, []))
                        if not carried:
                            rep.add_problem('OVERWRITE', 'hyperlink_lost', f'{name} / {key}: hyperlink in {labels[col] if col < len(labels) else col} '
                                            f'({target[:60]}) did not reach the Removed tab')
                continue
            ra, avals = ka[k]
            _link_problems(rep, name, key, labels, sb.links.get(rn, {}), sa.links.get(ra, {}))
            for c in range(max(width_h, len(bvals), len(avals))):
                bv = bvals[c] if c < len(bvals) else None
                av = avals[c] if c < len(avals) else None
                if same(bv, av):
                    continue
                col = labels[c] if c < len(labels) else f'#{c + 1}'
                if blank(bv):
                    rep.changes.append(Change(name, ra, key, col, 'filled', bv, av, 'blank_fill'))
                    continue
                tag = _allowed_change(name, aid, story, col, av, allow, derived_rel, bv)
                rep.changes.append(Change(name, ra, key, col, 'changed', bv, av, tag))
                if not tag:
                    rep.add_problem('OVERWRITE', 'cell_changed', f'{name} / {key} / {col}: {text(bv)[:50]!r} -> {text(av)[:50]!r}')

        for k, (ra, avals) in ka.items():
            if k in kb:
                continue
            key = _klabel(k)
            ok = name in new_ok or is_cov
            if name == ORIGINALS and k[0] not in cov_after_originals:
                ok = False
            tag = 'new_row' if ok else ''
            labels_a = _col_labels(sa.header)
            nonblank = [(c, v) for c, v in enumerate(avals) if not blank(v)]
            for c, v in nonblank:
                rep.changes.append(Change(name, ra, key, labels_a[c] if c < len(labels_a) else f'#{c + 1}', 'added', None, v, tag))
            if not nonblank:
                rep.changes.append(Change(name, ra, key, '(row)', 'added', None, '', tag))
            if not ok:
                rep.add_problem('OVERWRITE', 'row_added', f'{name}: new row not allowed on this tab: {key}')
            elif name == AV_TAB and k[0] not in allow.assigned_ids and k[0] not in cov_after_aids:
                rep.add_problem('FOREIGN_ROW', 'foreign_row', f'{name}: new row whose Article ID is neither assigned this run nor on Coverage: {key}')
            elif name == REMOVED and k[0] not in allow.removed_aids:
                rep.add_problem('FOREIGN_ROW', 'foreign_row', f'{name}: new row for an Article ID this run did not remove: {key}')

    # --- counts and mirrors (only where there is something to check against)
    _count_rules(rep, B, A, result, result2, allow, cov_after_originals, cov_after_aids)
    return rep


def _link_problems(rep, name, key, labels, bl, al):
    """every hyperlink of a before row must be on the after row, in the same column, with the same target"""
    for col, target in sorted(bl.items()):
        lab = labels[col] if col < len(labels) else f'#{col + 1}'
        if col not in al:
            rep.add_problem('OVERWRITE', 'hyperlink_lost', f'{name} / {key}: hyperlink lost in {lab}')
        elif al[col] != target:
            rep.add_problem('OVERWRITE', 'hyperlink_target', f'{name} / {key}: hyperlink in {lab} now points to {al[col][:60]!r} (was {target[:60]!r})')


def _allowed_change(sheet, aid, story, col, new, allow: Allow, derived_rel, old=None) -> str:
    if sheet in (COVERAGE, ORIGINALS):
        if col == REPRINT_COL and story in allow.reprint_new:
            rec = allow.reprint_new[story]
            if rec is not None and not blank(new) and str(rec) == text(new):
                return 'reprint_count'
            return ''   # the count in the file is not the one sheet_task recorded
        if (aid, col) in allow.swap_cells:
            return 'origin_swap'
        if (aid, col) in allow.retry_cells:
            return 'retry_cleared'
        if (aid, col) in allow.queue_cells:
            return 'queue_applied'
        # YTBROADCAST-v1 (the one recorded override of fill-blanks-only for station YouTube clips): only these two exact changes, and only
        # for a cell sheet_task.apply_yt_attach reports it changed. Format -> "Broadcast segment"; Medium "Video" -> TV or Radio.
        # OTHERFILES-v1 (the one recorded exception to "a filled cell never changes", SAVE_RULES): the "Other files" cell of a row may GROW. The names before stay
        # first, unchanged and in order; what follows is exactly the names sheet_task reports it appended (res['other_files']). Replacing, reordering or removing a
        # name, or adding one sheet_task did not report, is refused like any changed cell.
        if col == 'Other files' and aid in allow.other_files:
            old_n = [x.strip() for x in text(old).split(';') if x.strip()]
            new_n = [x.strip() for x in text(new).split(';') if x.strip()]
            if new_n[:len(old_n)] == old_n and new_n[len(old_n):] == allow.other_files[aid]:
                return 'other_files_append'
            return ''
        if (aid, col) in allow.yt_cells:
            if col == 'Format' and text(new) == 'Broadcast segment':
                return 'yt_attach'
            if col == 'Medium' and text(old) == 'Video' and text(new) in ('TV', 'Radio'):
                return 'yt_attach'
    if sheet == AV_TAB and col == 'Item type' and aid in allow.yt_item_aids and text(new) == 'Broadcast segment':
        return 'yt_attach'
    if sheet == PRESS and col in derived_rel:
        return 'rel_derived'
    return ''


def _count_rules(rep, B, A, result, result2, allow, cov_after_originals, cov_after_aids):
    cb, ca = B.sheets.get(COVERAGE), A.sheets.get(COVERAGE)
    if cb is None or ca is None:
        return
    n_b, n_a = len(cb.rows), len(ca.rows)
    own_added = len({c.row for c in rep.changes if c.sheet == COVERAGE and c.kind == 'added'})
    own_moved = sum(1 for c in rep.changes if c.sheet == COVERAGE and c.kind == 'moved')
    own_missing = sum(1 for c in rep.changes if c.sheet == COVERAGE and c.kind == 'missing')
    if n_a != n_b + own_added - own_moved - own_missing:
        rep.add_problem('ROWCOUNT', 'identity', f'Coverage rows: after {n_a} != before {n_b} + added {own_added} - moved {own_moved}'
                        f' - missing {own_missing}')
    res = result or {}
    v1, v2 = (res.get('verify') or {}), ((result2 or {}).get('verify') or {})
    if v1:
        if v1.get('rows_before') is not None and v1['rows_before'] != n_b:
            rep.add_problem('ROWCOUNT', 'verify_before', f"sheet_task counted {v1['rows_before']} Coverage rows before, the diff counts {n_b}")
        if v1.get('rows_after') is not None and v1['rows_after'] != n_a:
            rep.add_problem('ROWCOUNT', 'verify_after', f"sheet_task counted {v1['rows_after']} Coverage rows after, the diff counts {n_a}")
    if v1 and v2 and v1.get('rows_after') != v2.get('rows_after'):
        rep.add_problem('ROWCOUNT', 'pass2', f"pass 2 rows_after {v2.get('rows_after')} != pass 1 {v1.get('rows_after')}")
    counts = res.get('counts') or {}
    if 'rows_added' in counts and counts['rows_added'] != own_added:
        rep.add_problem('ROWCOUNT', 'rows_added', f"sheet_task says {counts['rows_added']} rows added, the diff finds {own_added}")
    if 'removed' in res and own_moved + own_missing != allow.removed_rows_n:
        rep.add_problem('ROWCOUNT', 'rows_removed', f'result lists {allow.removed_rows_n} rows moved to Removed, the diff finds {own_moved + own_missing} Coverage rows gone')
    ob, oa = B.sheets.get(ORIGINALS), A.sheets.get(ORIGINALS)
    if oa is not None:
        o_aids = []
        if oa.header:
            hi = {text(h): i for i, h in enumerate(oa.header) if not blank(h)}
            if 'Article ID' in hi:
                o_aids = [text(v[hi['Article ID']]) for _, v in oa.rows if hi['Article ID'] < len(v)]
        if o_aids != cov_after_originals:
            rep.add_problem('ROWCOUNT', 'originals_mirror', f'Originals tab ({len(o_aids)} rows) does not match the Original rows of Coverage ({len(cov_after_originals)})')
        if v1.get('originals') is not None and v1['originals'] != len(o_aids):
            rep.add_problem('ROWCOUNT', 'originals_count', f"sheet_task counted {v1['originals']} Originals, the file has {len(o_aids)}")
    # foreign rows
    new_aids = {c.key for c in rep.changes if c.sheet == COVERAGE and c.kind == 'added'}
    before_aids = {k[0] for k in _keyed(cb)}
    foreign = sorted(a for a in new_aids if a not in before_aids and a not in allow.assigned_ids)
    if foreign:
        rep.add_problem('FOREIGN_ROW', 'foreign_row', f'Coverage rows whose Article ID sheet_task did not assign in this run: {foreign[:20]}')
