"""LIBFILES-v1 end to end: everything an update brings lands in the keeper's PC library under the schema name (NAMING-v2, CONTRACT.md) in the right year folder,
the workbook's File name / File name 2 / Saved Copy? / File type cells match the files, nothing existing is touched, renames are listed in the panel result,
and a keeper -> reader refresh delivers the same files to the same paths.

    AJG_TEST_BUILD="<scratchpad>/app_build_v64/linux/AJG Tracker" python3 -I -m unittest discover -s work/localapp/app/tests -p test_libfiles.py -v

Needs the Linux test build (assemble_app.py --target linux --role keeper, from the v64 workbook copy) and the station outputs libfiles_zip.py names (looked for in
LIBFILES_SRC or the scratchpad). About 10 minutes (two previews, two saves, a refresh). Works on hard-linked copies of the build; the build is never written."""
import json
import os
import re
import shutil
import sys
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import support as T  # noqa: E402
import libfiles_zip as LZ  # noqa: E402

SRCROOT = Path(os.environ.get('LIBFILES_SRC') or T.SCRATCH)
SRC = {'nb': SRCROOT / 'nb64' / 'out' / 'nb_update.zip', 'pq': SRCROOT / 'pq64' / 'out' / 'pq_update.zip', 'yt': SRCROOT / 'yt64' / 'yt_update.zip'}
FU = SRCROOT / 'fu64' / 'for_update.json'
BASE = T.SCRATCH / 'app_build' / 'test_libfiles'
K = R = None
S = {}

SCHEMA = re.compile(r'^(ws|nb|pq)(\d{5})([or])-(s\d{5})\.(html|pdf)$')


def setUpModule():
    if not T.BUILD.is_dir():
        raise unittest.SkipTest('no test build')
    for p in list(SRC.values()) + [FU]:
        if not p.is_file():
            raise unittest.SkipTest('station outputs missing: ' + str(p))
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    global K, R
    K = T.Server(T.make_work(BASE, 'keeper', 'keeper')).start()
    R = T.Server(T.make_work(BASE, 'reader', 'reader')).start()


def tearDownModule():
    for s in (K, R):
        if s:
            s.stop()


def wbfile(srv):
    return next((srv.root / 'data' / 'workbook').glob('*.xlsx'))


def lib_snapshot(root: Path) -> dict:
    """every library file -> (inode, size, mtime_ns): existing files must come out of a save exactly as they went in"""
    snap = {}
    for dp, _, fns in os.walk(root / 'data' / 'library'):
        for fn in fns:
            p = Path(dp) / fn
            st = p.stat()
            snap[p.relative_to(root / 'data' / 'library').as_posix()] = (st.st_ino, st.st_size, st.st_mtime_ns)
    return snap


def coverage(srv):
    import openpyxl
    wb = openpyxl.load_workbook(wbfile(srv), read_only=True)
    rows = list(wb['Coverage'].iter_rows(values_only=True))
    ix = {c: i for i, c in enumerate(rows[0])}
    out = [{c: r[i] for c, i in ix.items()} for r in rows[1:]]
    rel = [dict(zip([c.value for c in next(wb['Press releases'].iter_rows(max_row=1))], r)) for r in wb['Press releases'].iter_rows(min_row=2, values_only=True)]
    av = [dict(zip([c.value for c in next(wb['Audio & video details'].iter_rows(max_row=1))], r)) for r in wb['Audio & video details'].iter_rows(min_row=2, values_only=True)]
    return out, rel, av


def sha(p):
    return T.sha(p)


class LibFiles(unittest.TestCase):
    maxDiff = None

    def test_01_one_update_with_everything(self):
        fu = json.loads(FU.read_text(encoding='utf-8'))
        wsha = sha(wbfile(K))
        self.assertTrue(wsha.startswith(fu['fingerprint']['workbook_sha256'][:8]), 'the for-Update file was made from this workbook')
        cov0, rel0, av0 = coverage(K)
        tv = next(r for r in cov0 if r['Medium'] == 'TV' and r['Format'] == 'Article' and r['Publisher link'] and r['Original or reprint'] == 'Original')
        S['attach_row'] = tv
        today = '2026-11-03'
        S['A'] = A = LZ.build(BASE / 'updA.zip', for_update=fu, src=SRC, today=today, workbook_sha=wsha, attach_row_link=tv['Publisher link'], tag='A')
        S['B'] = B = LZ.build(BASE / 'updB.zip', for_update=fu, src=SRC, today=today, workbook_sha=wsha, attach_row_link=tv['Publisher link'], tag='B')
        S['before'] = lib_snapshot(K.root)
        S['cov0'] = cov0
        st, j = K.upload(A['zip'])
        self.assertEqual(st, 200, j)
        ins = K.job('inspect', {'file': j['file']})
        self.assertTrue(ins.get('ok') and ins.get('can_save'), ins)
        S['insA'] = ins
        panel = '\n'.join(ins['lines'])
        self.assertIn('as the station named them', panel, 'the preview says the file names were checked')
        S['previewA_panel'] = panel
        self.assertFalse([x for x in ins.get('needs_person', []) if 'wanted' in x or 'first publisher' in x or 'review-queue' in x], ins['needs_person'])
        res = K.job('save', {'update_id': ins['update_id'], 'token': ins['token']}, timeout=1800)
        self.assertTrue(res.get('ok') and res.get('written'), res)
        S['saveA'] = res
        self.assertIn('as the station named them', '\n'.join(res['lines']))
        self.assertFalse(res.get('warnings'), res.get('warnings'))
        # the save's checks of the station's names: every rename is listed in the panel (with its reason), and the update folder kept in done/ now carries the SAVE's names
        done = K.root / 'data' / 'updates' / 'done' / ins['update_id']
        nr = json.loads((done / 'names_result.json').read_text(encoding='utf-8'))
        S['namesA'] = nr
        lines = '\n'.join(res['lines'])
        for r in nr['renamed']:
            stem_from, stem_to = r['from'].rsplit('/', 1)[-1].rsplit('.', 1)[0], r['to'].rsplit('/', 1)[-1].rsplit('.', 1)[0]
            self.assertIn(f'{stem_from} -> {stem_to}', lines, 'every rename is listed in the panel result')
            self.assertIn(f'{stem_from} -> {stem_to}', S['previewA_panel'], 'and was already listed in the preview')
            self.assertTrue((done / Path(*r['to'].split('/'))).is_file(), r)
            if r['from'] not in {x['to'] for x in nr['renamed']}:      # a number that moved on may be taken by the next file in the chain
                self.assertFalse((done / Path(*r['from'].split('/'))).exists(), r)
        self.assertEqual(nr['unnamed'], [], 'every file the save wrote had been named by the station')
        lib = K.root / 'data' / 'library'
        for f in nr and [p for p in (done / 'library').rglob('*') if p.is_file()]:
            rel = f.relative_to(done / 'library').as_posix()
            if (lib / rel).is_file():
                self.assertEqual(sha(lib / rel), sha(f), ('the update folder copy and the library file differ', rel))
            else:
                self.assertIn('library/' + rel, {x['file'] for x in nr['not_saved']} | {x for x in nr['raw_not_kept']}, ('a file in the kept update folder is not in the library and not listed as unsaved', rel))

    def test_02_files_at_schema_names_and_folders(self):
        A = S['A']
        cov, rel, av = coverage(K)
        old_ids = {r['Article ID'] for r in S['cov0']}
        new = [r for r in cov if r['Article ID'] not in old_ids]
        self.assertEqual(len(new), 10, [r['Headline'] for r in new])      # 2 NB + 2 PQ + reprint + 2 web + 3 yt rows
        lib = K.root / 'data' / 'library'
        by_hl = {r['Headline']: r for r in new}
        today_year = '2026'
        seen_files = set()
        for key, row in A['rows'].items():
            r = by_hl.get(row['Headline'])
            self.assertIsNotNone(r, ('row missing from the workbook', key))
            aid, sid = r['Article ID'], r['Story ID']
            kind = 'r' if r['Original or reprint'] == 'Reprint' else 'o'
            year = (str(r['Date'])[:4] if r['Date'] else today_year)
            fmt = {'nb_a': 'nb', 'nb_b': 'nb', 'nb_c': 'nb', 'pq_a': 'pq', 'pq_b': 'pq', 'pq_reprint': 'pq'}.get(key, 'ws')
            if key == 'yt_nocopy' or key == 'yt_clip':
                self.assertEqual(r['Saved Copy?'], 'No' if key == 'yt_nocopy' else r['Saved Copy?'])
            if key == 'yt_nocopy':
                self.assertFalse(r['File name'] and re.search(r'\.(html|pdf)$', str(r['File name'])), r['File name'])
                continue
            fn = r['File name']
            m = SCHEMA.match(str(fn or ''))
            if key == 'yt_clip':
                if not m:
                    continue
            self.assertIsNotNone(m, (key, 'File name is not a schema name', fn))
            self.assertEqual((m.group(1), m.group(2), m.group(3)), (fmt, aid, kind), (key, fn))
            self.assertEqual(m.group(4), sid, (key, fn))
            ext = 'pdf' if fmt == 'nb' else 'html'
            self.assertEqual(m.group(5), ext, (key, fn))
            self.assertEqual(r['Saved Copy?'], 'Yes', key)
            want_type = {'nb': 'Newsbank pdf', 'pq': 'ProQuest pdf', 'ws': None}[fmt]
            if want_type:
                self.assertEqual(r['File type'], want_type, (key, r['File type']))
            f = lib / year / fn
            self.assertTrue(f.is_file(), ('saved copy not at <year>/<File name>', key, str(f)))
            seen_files.add(f'{year}/{fn}')
            if fmt == 'ws':
                self.assertTrue((lib / '_original_html' / year / fn).is_file(), ('raw page missing', key, fn))
                seen_files.add(f'_original_html/{year}/{fn}')
                for q in (lib / '_original_html' / year / fn, f):
                    self.assertIn(row['Headline'], q.read_text(encoding='utf-8'), 'the page text is in both the saved copy and the raw page')
            if fmt == 'pq':
                self.assertTrue((lib / '_original_pdf' / year / (fn[:-5] + '.pdf')).is_file(), ('original PDF missing', key, fn))
                seen_files.add(f'_original_pdf/{year}/{fn[:-5]}.pdf')
                self.assertTrue(f.read_bytes().startswith(b'<') or b'<html' in f.read_bytes()[:400].lower(), 'ProQuest copy is html text')
            if fmt == 'nb':
                self.assertTrue(f.read_bytes().startswith(b'%PDF'), 'NewsBank copy is the story PDF')
            if key in ('pq_a', 'nb_a'):
                self.assertEqual(f.parent.name, '2026')
        self.assertEqual(by_hl[S['A']['rows']['nb_b']['Headline']]['File name'][:2], 'nb')
        self.assertTrue((lib / '2025').is_dir() and (lib / '_original_pdf' / '2024').is_dir())
        # the undated web find goes to the year of the day of the save, and the workbook says so in the same cells
        und = by_hl[A['rows']['undated']['Headline']]
        self.assertTrue((lib / '2026' / und['File name']).is_file(), und)
        # the reprint is a pq...r-s00003 copy
        rp = by_hl[A['rows']['pq_reprint']['Headline']]
        self.assertRegex(rp['File name'], r'^pq\d{5}r-s00003\.html$')
        # press release
        newrel = [x for x in rel if 'libfiles-test-release' in str(x.get('URL'))]
        self.assertEqual(len(newrel), 1, 'the release is on the Press releases tab')
        pr = newrel[0]
        prid = pr['Release ID']
        self.assertRegex(str(prid), r'^pr\d{5}$')
        self.assertEqual((pr['File name'], pr['Saved Copy?']), (f'{prid}.html', 'Yes'))
        self.assertTrue((lib / 'Press releases' / '2026' / f'{prid}.html').is_file())
        self.assertTrue((lib / '_original_html' / 'Press releases' / '2026' / f'{prid}.html').is_file())
        seen_files |= {f'Press releases/2026/{prid}.html', f'_original_html/Press releases/2026/{prid}.html'}
        # everything the update's names block promised is there under exactly that name
        for path in A['library']:
            self.assertTrue((lib / path[len('library/'):]).is_file(), ('named file missing from the library', path))
        S['new_files'] = seen_files
        # YouTube attach: the tracked story became a broadcast story, its saved copy untouched
        tv = S['attach_row']
        got = next(r for r in cov if r['Article ID'] == tv['Article ID'])
        self.assertEqual(got['Format'], 'Broadcast segment')
        self.assertEqual(got['File name'], tv['File name'])
        self.assertTrue(any(a.get('Article ID') == tv['Article ID'] and 'youtube.com/watch?v=AAAAAAAAAAA' in str(a.get('YouTube link')) for a in av), 'YouTube link on the A/V row')

    def test_03_nothing_existing_touched(self):
        before = S['before']
        after = lib_snapshot(K.root)
        gone = [p for p in before if p not in after]
        changed = [p for p in before if p in after and before[p] != after[p]]
        self.assertEqual(gone, [], gone[:5])
        self.assertEqual(changed, [], changed[:5])
        added = sorted(set(after) - set(before))
        self.assertEqual(set(added), S['new_files'] | {a for a in added if a.startswith('_original_html/') and a[len('_original_html/'):] in {p[len('_original_html/'):] for p in S['new_files']}}, (added, sorted(S['new_files'])))
        self.assertFalse((K.root / 'data' / 'library' / '_to_delete').exists())

    def test_04_second_update_numbers_taken_renames_listed(self):
        B = S['B']
        st, j = K.upload(B['zip'])
        ins = K.job('inspect', {'file': j['file']})
        self.assertEqual(ins.get('stage'), 'needs_confirm', 'made from the same for-Update file, but the workbook has moved on since (update A)')
        ins = K.job('preview', {'update_id': ins['update_id'], 'accept_mismatch': True})      # "Use it anyway"
        self.assertTrue(ins.get('ok') and ins.get('can_save'), ins)
        panel = '\n'.join(ins['lines'])
        self.assertRegex(panel, r'\d+ file\(s\) renamed to the names the save gave', panel)
        self.assertIn('->', panel)
        before = lib_snapshot(K.root)
        res = K.job('save', {'update_id': ins['update_id'], 'token': ins['token'], 'accept_mismatch': True}, timeout=1800)
        self.assertTrue(res.get('ok') and res.get('written'), res)
        self.assertRegex('\n'.join(res['lines']), r'file\(s\) renamed to the names the save gave')
        after = lib_snapshot(K.root)
        self.assertEqual([p for p in before if p not in after or before[p] != after[p]], [], 'existing files untouched')
        cov, _, _ = coverage(K)
        by_hl = {r['Headline']: r for r in cov}
        for key in ('nb_c', 'web'):
            r = by_hl[B['rows'][key]['Headline']]
            fn = r['File name']
            self.assertRegex(fn, SCHEMA.pattern)
            self.assertTrue((K.root / 'data' / 'library' / str(r['Date'])[:4] / fn).is_file(), (key, fn))
            planned = [p for p in B['library'] if p.endswith('/' + fn)]
            self.assertEqual(planned, [], 'the station had named it with the numbers that were taken, so the final name differs')
        self.assertTrue(int(by_hl[B['rows']['web']['Headline']]['Article ID']) > 10679)
        S['wb_final'] = sha(wbfile(K))
        S['b_files'] = sorted(set(after) - set(before))

    def test_05_keeper_to_reader_refresh_same_files(self):
        mk = K.job('refresh_make', {}, timeout=1800)
        self.assertTrue(mk.get('ok'), mk)
        z = sorted((K.root / 'data' / 'refresh_out').glob('refresh_*.zip'))[-1]
        rz = BASE / z.name
        shutil.copy2(z, rz)
        with zipfile.ZipFile(rz) as zf:
            names = set(zf.namelist())
        S['refresh_names'] = names
        reader_before = lib_snapshot(R.root)
        st, j = R.upload(rz, 'refresh')
        got = R.job('refresh_take', {'file': j['file']}, timeout=1800)
        self.assertTrue(got.get('ok'), got)
        self.assertEqual(sha(wbfile(R)), S['wb_final'], 'identical workbook')
        kl, rl = lib_snapshot(K.root), lib_snapshot(R.root)
        new_in_keeper = sorted(set(kl) - set(S['before']))
        self.assertTrue(new_in_keeper)
        missing = [p for p in new_in_keeper if p not in rl]
        self.assertEqual(missing, [], ('files the keeper added that the reader did not get', missing))
        for p in new_in_keeper:
            self.assertEqual(sha(R.root / 'data' / 'library' / p), sha(K.root / 'data' / 'library' / p), p)
        self.assertEqual([p for p in reader_before if p not in rl or reader_before[p][1:2] != rl[p][1:2]], [], 'reader files untouched')
        self.assertEqual(sorted(set(rl) - set(reader_before)), new_in_keeper, 'exactly the new files')
        # the reader's workbook names match the files it now holds
        cov, rel, _ = coverage(R)
        old_ids = {r['Article ID'] for r in S['cov0']}
        for r in cov:
            if r['Article ID'] in old_ids or not r['File name'] or not SCHEMA.match(str(r['File name'])):
                continue
            year = str(r['Date'])[:4] if r['Date'] else '2026'
            self.assertTrue((R.root / 'data' / 'library' / year / r['File name']).is_file(), r['File name'])


if __name__ == '__main__':
    unittest.main()
