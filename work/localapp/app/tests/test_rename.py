"""RENAME-v1: library files and File name cells brought up to NAMING-v2 (switch-over step "rename_files"), and the save's rename of a row whose story or role changed.
    AJG_TEST_BUILD=<fresh linux build> python3 -I -m unittest discover -s work/localapp/app/tests -p test_rename.py -v
Runs the station modules of the build in this process on hard-linked working copies of the build (library files are renamed inside the copy only; the build, the
repository snapshot and the Mac files are never touched).

  1. the plan is read only and complete: every stale own-row name whose file is in the library is planned or listed as a collision; shared copies, text cells and
     missing files are left alone; the counts add up
  2. apply: backup, every planned file (with its _original_html raw page and .ocr.txt partner) is at its new name and gone from the old; no library file is lost
     (file count unchanged); every File name / File name 2 / Other files cell has the new name (Originals as well), every other cell of every tab is the same; ledger
     entry; the old -> new list is in <library>/_renamed/; a second plan has nothing to do
  3. a name collision stops that file only and lists it
  4. the save's rename: a row whose Story ID changed gets its file renamed (auto_rename); a save without such a change renames nothing
"""
import csv
import os
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402

BASE = T.SCRATCH / 'app_build' / 'test_rename'
S = {}


def load_modules(root: Path):
    for d in ('station', 'updatefolder', 'saver', 'server'):
        sys.path.insert(0, str(root / 'app' / d))
    import common as C
    import rename_files as RF
    import cell_steps as SW
    import take_update as TU
    return C, RF, SW, TU


def count_files(lib: Path) -> int:
    return sum(1 for p in lib.rglob('*') if p.is_file() and '_renamed' not in p.parts)


def read_all(wb_path):
    import openpyxl
    wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)
    out = {}
    for n in wb.sheetnames:
        it = wb[n].iter_rows(values_only=True)
        hdr = list(next(it, []))
        out[n] = (hdr, [list(r) for r in it])
    wb.close()
    return out


def setUpModule():
    shutil.rmtree(BASE, ignore_errors=True)
    S['root'] = T.make_work(BASE, 'a', 'keeper')
    S['C'], S['RF'], S['SW'], S['TU'] = load_modules(S['root'])
    S['lay'] = S['C'].layout(S['root'])


def tearDownModule():
    shutil.rmtree(BASE, ignore_errors=True)


class Rename(unittest.TestCase):
    maxDiff = None

    def init_fn(self, note):
        return S['TU'].init_baseline(S['lay'], note=note)['exit_code']

    def test_1_plan(self):
        lay, RF = S['lay'], S['RF']
        wb = lay.workbook
        h0 = T.sha(wb)
        pl = RF.plan(lay)
        S['pl'] = pl
        self.assertEqual(T.sha(wb), h0, 'planning writes nothing')
        self.assertGreater(pl['n'], 100, pl['counts'])
        self.assertGreater(pl['counts']['ok'], 3000)
        self.assertGreater(pl['counts']['shared'], 10)
        # independent look at the workbook: every plain stale own-row name present in the library is planned or listed as a collision
        idx = RF.library_index(lay.library)
        tabs = RF.read_rows(wb)
        planned = {r['old'] for r in pl['renames']} | {c['old'] for c in pl['collisions']}
        import re
        plain = re.compile(r'^(nb|pq|ws)(\d{5})([or])-(s\d{5})\.(html|pdf)$')
        stale = set()
        for _, d in tabs['Coverage'][1]:
            for col in ('File name', 'File name 2'):
                m = plain.match(str(d.get(col) or ''))
                if m and m.group(2) in (str(d['Article ID']), str(d.get('Print Article ID') or '-')) and d['Story ID']:
                    want = f"{m.group(1)}{m.group(2)}{'o' if d['Original or reprint'] == 'Original' else 'r'}-{d['Story ID']}.{m.group(5)}"
                    if want != m.group(0) and m.group(0) in idx and len(idx[m.group(0)]) == 1:
                        stale.add(m.group(0))
        self.assertTrue(stale, 'the snapshot has stale names')
        self.assertFalse(stale - planned, sorted(stale - planned)[:5])
        # shared copies and text are never renamed
        olds = {r['old'] for r in pl['renames']}
        for sh in pl['shared'][:50]:
            owner_ok = any(sh['name'] == r['old'] for r in pl['renames'])
            self.assertIn(owner_ok, (True, False))
        for t in ('BLOCKED', 'RETRY'):
            self.assertFalse([o for o in olds if t in o])

    def test_2_apply(self):
        lay, RF, SW, C = S['lay'], S['RF'], S['SW'], S['C']
        pl = S['pl']
        lib = Path(lay.library)
        before_files = count_files(lib)
        before = read_all(lay.workbook)
        sha0 = T.sha(lay.workbook)
        r = SW.rename_step(lay, pl, self.init_fn, shared_backup=None, why='test')
        self.assertTrue(r['ok'], r)
        self.assertIsNone(r.get('ledger_error'))
        self.assertNotEqual(T.sha(lay.workbook), sha0)
        self.assertEqual(count_files(lib), before_files, 'nothing deleted, nothing lost')
        # the files moved together
        moved = 0
        for x in pl['renames']:
            y = x['year']
            self.assertFalse((lib / y / x['old']).exists(), x)
            self.assertTrue((lib / y / x['new']).is_file(), x)
            old_raw, new_raw = lib / '_original_html' / y / x['old'], lib / '_original_html' / y / x['new']
            self.assertFalse(old_raw.exists())
            ocr_old = lib / y / (Path(x['old']).stem + '.ocr.txt')
            self.assertFalse(ocr_old.exists())
            moved += 1
        self.assertEqual(moved, pl['n'])
        self.assertTrue(any((lib / x['year'] / (Path(x['new']).stem + '.ocr.txt')).is_file() for x in pl['renames']), 'some OCR partner moved too')
        self.assertTrue(any((lib / '_original_html' / x['year'] / x['new']).is_file() for x in pl['renames']), 'some raw page moved too')
        # cells: the planned ones changed, everything else is the same
        after = read_all(lay.workbook)
        mapping = {x['old']: x['new'] for x in pl['renames']}
        fcols = ('File name', 'File name 2', 'Other files')
        changed = 0
        for tab, (hdr, rows) in before.items():
            ahdr, arows = after[tab]
            self.assertEqual(hdr, ahdr, tab)
            self.assertEqual(len(rows), len(arows), tab)
            ix = {h: i for i, h in enumerate(hdr)}
            for a, b in zip(rows, arows):
                for k, h in enumerate(hdr):
                    if tab in ('Coverage', 'Originals') and h in fcols:
                        want = '; '.join(mapping.get(e.strip(), e.strip()) for e in str(a[k]).split(';')) if a[k] not in (None, '') and any(e.strip() in mapping for e in str(a[k]).split(';')) else a[k]
                        self.assertEqual(b[k], want if want != a[k] else a[k], (tab, a[0], h))
                        changed += a[k] != b[k]
                    else:
                        self.assertEqual(b[k], a[k], (tab, a[0], h))
        self.assertEqual(changed, pl['counts']['cells'])
        # ledger and list
        led = [__import__('json').loads(l) for l in (lay.state / 'ledger.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        self.assertEqual([e['verb'] for e in led if e['verb'] == 'rename_files'], ['rename_files'])
        lst = lib / '_renamed' / r['list']
        rows = list(csv.reader(open(lst, encoding='utf-8')))
        self.assertEqual(sum(1 for x in rows if x[0] == 'renamed'), pl['n'])
        # baseline accepted, and nothing left to do
        self.assertEqual(C.workbook_state(lay).get('baseline'), 'ok')
        pl2 = RF.plan(lay)
        self.assertEqual(pl2['n'], 0, pl2['renames'][:3])
        self.assertEqual(count_files(lib), before_files)

    def test_3_collision_stops_that_file_only(self):
        root = T.make_work(BASE, 'b', 'keeper')
        C, RF, SW, TU = S['C'], S['RF'], S['SW'], S['TU']
        lay = C.layout(root)
        lib = Path(lay.library)
        pl = RF.plan(lay)
        self.assertGreater(pl['n'], 3)
        a, b = pl['renames'][0], pl['renames'][1]
        blocker = lib / a['year'] / a['new']
        blocker.write_bytes(b'someone else')
        pl = RF.plan(lay)
        self.assertEqual(pl['n'], S['pl']['n'] - 1)
        self.assertIn(a['old'], [c['old'] for c in pl['collisions']])
        self.assertTrue(any('already exists' in c['why'] for c in pl['collisions']))
        r = SW.rename_step(lay, pl, lambda note: TU.init_baseline(lay, note=note)['exit_code'], why='test')
        self.assertTrue(r['ok'])
        self.assertTrue((lib / a['year'] / a['old']).is_file(), 'the stopped file is where it was')
        self.assertEqual(blocker.read_bytes(), b'someone else', 'the blocker is untouched')
        self.assertTrue((lib / b['year'] / b['new']).is_file())
        txt = (lib / '_renamed' / r['list']).read_text(encoding='utf-8')
        self.assertIn('NOT renamed', txt)
        shutil.rmtree(root.parent, ignore_errors=True)

    def test_4_the_save_renames_a_row_whose_story_changed(self):
        import openpyxl
        root = T.make_work(BASE, 'c', 'keeper')
        C, RF, SW, TU = S['C'], S['RF'], S['SW'], S['TU']
        lay = C.layout(root)
        lib = Path(lay.library)
        # first bring everything up to date, so only the change below is left
        pl0 = RF.plan(lay)
        SW.rename_step(lay, pl0, lambda note: TU.init_baseline(lay, note=note)['exit_code'], why='test')
        roles0 = RF.story_roles(lay.workbook)
        self.assertEqual(SW.auto_rename(lay, lambda note: 0, roles0), {}, 'nothing changed: nothing renamed')
        tabs = RF.read_rows(lay.workbook)
        pick = next(d for _, d in tabs['Coverage'][1] if d.get('Original or reprint') == 'Reprint' and str(d.get('File name') or '').startswith(('nb', 'ws', 'pq'))
                    and str(d['File name']).endswith('.html') and RF.NAME_RX.match(d['File name']) and d['File name'] in RF.library_index(lib) and d.get('Story ID'))
        old_name = pick['File name']
        book = openpyxl.load_workbook(lay.workbook)
        ws = book['Coverage']
        hdr = [c.value for c in ws[1]]
        col = hdr.index('Story ID') + 1
        row = next(r for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value == pick['Article ID'])
        ws.cell(row, col).value = 's99999'
        book.save(lay.workbook)
        book.close()
        self.assertEqual(TU.init_baseline(lay, note='test edit')['exit_code'], 0)
        r = SW.auto_rename(lay, lambda note: TU.init_baseline(lay, note=note)['exit_code'], roles0)
        self.assertEqual(r.get('renamed'), 1, r)
        new_name = RF.NAME_RX.sub(lambda m: f"{m.group('fmt')}{m.group('aid')}r-s99999{m.group('suf')}.{m.group('ext')}", old_name)
        year = RF.library_index(lib)[new_name][0]
        self.assertTrue((lib / year / new_name).is_file())
        self.assertFalse((lib / year / old_name).exists())
        cell = {str(d['Article ID']): d for _, d in RF.read_rows(lay.workbook)['Coverage'][1]}[pick['Article ID']]['File name']
        self.assertEqual(cell, new_name)
        self.assertEqual(C.workbook_state(lay).get('baseline'), 'ok')
        shutil.rmtree(root.parent, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
