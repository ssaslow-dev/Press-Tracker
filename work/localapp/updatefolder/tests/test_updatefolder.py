"""Tests for the two travelling files and the PC-side code. Everything runs in temp folders on copies; data/ is never touched.

    cd work/localapp/updatefolder && python3 -I -m unittest discover -s tests -t . -v
"""
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
UF = HERE.parent
REPO = UF.parent.parent.parent
sys.path.insert(0, str(UF))
import formats as F                 # noqa: E402
import make_for_update as MFU       # noqa: E402
import take_update as TU            # noqa: E402
from layout import PCLayout, OutsideAppFolder   # noqa: E402

SAVER = REPO / 'work' / 'saver' / 'src' / 'saver.py'
PIPE_SHA_TOOL = REPO / 'work' / 'saver' / 'tools' / 'pipeline_sha.py'
EXAMPLE_DB = REPO / 'build' / 'tests' / 'sheet_task' / 'fixtures' / 'example_db.json'
MINI = REPO / 'build' / 'tests' / 'sheet_task' / 'audit' / 'mini.py'
MASTER = 'AJG Coverage - NewsBank.xlsx'

TMP = tempfile.TemporaryDirectory()
ROOT = Path(TMP.name)
PIPE_REAL = ROOT / 'pipe_real'      # code/ top-level files: build_data.py runs for real
PIPE_STUB = ROOT / 'pipe_stub'      # the saver's pipeline with build_data/relmatch stubbed (as in the saver's own e2e tests)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def setUpModule():
    PIPE_REAL.mkdir()
    for f in (REPO / 'code').iterdir():
        if f.is_file() and f.suffix in ('.py', '.json', '.csv'):
            shutil.copy2(f, PIPE_REAL / f.name)
    shutil.copytree(REPO / 'code', PIPE_STUB, ignore=shutil.ignore_patterns('docs', '__pycache__', '*.pyc', '_history', 'tracker', 'fetch2',
                                                                            'billstatus', 'fetch_rated1'))
    (PIPE_STUB / 'build_data.py').write_text("import sys, os\nos.makedirs(sys.argv[3], exist_ok=True)\n"
                                             "for n in ('data', 'rows', 'idmap', 'covcols'):\n"
                                             "    open(os.path.join(sys.argv[3], n + '.json'), 'w').write('{}')\n", encoding='utf-8')
    (PIPE_STUB / 'relmatch.py').write_text('import sys\n', encoding='utf-8')
    subprocess.run([sys.executable, '-I', str(PIPE_SHA_TOOL), str(PIPE_STUB)], check=True, capture_output=True)


def load_mini():
    os.environ.setdefault('AUDIT_OUT', str(ROOT / 'aud'))
    spec = importlib.util.spec_from_file_location('mini_wb', MINI)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- a small workbook with the columns build_data.py reads


def make_big_wb(path):
    import openpyxl
    mini = load_mini()
    cols = list(mini.COLS) + ['Translated Headline', 'Story in English', 'Print Article ID']
    cols = list(dict.fromkeys(cols))

    def row(**kw):
        return [kw.get(c) for c in cols]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Coverage'
    ws.append(cols)
    ws.append(row(**{'Article ID': '00001', 'Story ID': 's00001', 'Original or reprint': 'Original', 'Date': '2026-10-01', 'Year': '2026',
                     'Outlet': 'Old Gazette', 'Headline': 'Gabriel bill passes, again', 'Publisher link': 'https://old.example.com/a?x=1',
                     'Medium': 'Online news', 'Reach': 'California regional & local', 'Topic': 'Housing', 'Role': 'Mentioned in story',
                     'Tone': 'Neutral', 'Tone note': 'a long tone note that stays home', 'Story in English': 'TRANSLATED ARTICLE TEXT',
                     'Bills': 'AB 1'}))
    ws.append(row(**{'Article ID': '00002', 'Story ID': 's00001', 'Original or reprint': 'Reprint', 'Date': '2026-10-02', 'Year': '2026',
                     'Outlet': 'Echo Times', 'Headline': 'Gabriel bill passes, again', 'Publisher link': 'https://echo.example.com/b'}))
    ws.append(row(**{'Article ID': '00003', 'Story ID': 's00003', 'Original or reprint': 'Original', 'Date': '2026-10-05', 'Year': '2026',
                     'Outlet': 'Other Times', 'Headline': 'Second story', 'Publisher link': 'https://other.example.com/c',
                     'Role': 'Named in headline'}))
    o = wb.create_sheet('Originals')
    o.append(cols)
    rm = wb.create_sheet('Removed')
    rm_cols = list(mini.RM_COLS) + ['Translated Headline', 'Story in English']
    rm_cols = list(dict.fromkeys(rm_cols))
    rm.append(rm_cols)
    rm.append([{'Article ID': '00009', 'Story ID': 's00009', 'Original or reprint': 'Original', 'Outlet': 'Gone News', 'Date': '2026-09-01',
                'Headline': 'A removed story', 'Publisher link': 'https://gone.example.com/z'}.get(c) for c in rm_cols])
    wb.save(path)
    return Path(path)


def jwrite(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding='utf-8')


class MakeForUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = ROOT / 'mfu'
        cls.d.mkdir()
        cls.wb = make_big_wb(cls.d / MASTER)
        cls.sha = sha(cls.wb)
        cls.db = cls.d / 'db'
        jwrite(cls.db / 'runs' / 'run-aaaa1.json', {'at': '2026-10-20T10:00:00Z', 'mode': 'find', 'searched_to': '2026-10-19', 'status': 'done',
                                                    'rows': [{'x': 1}], 'sheet': {'written': True, 'at': 'x', 'line': 'ok'}, 'secret_big': 'x' * 10})
        jwrite(cls.db / 'runs' / 'run-bbbb2.json', {'at': '2026-10-25T10:00:00Z', 'mode': 'find', 'searched_to': '2026-10-24',
                                                    'rows': [{'x': 1}, {'x': 2}]})
        jwrite(cls.db / 'runs' / 'run-cccc3.json', {'at': '2026-10-26T10:00:00Z', 'mode': 'edits'})
        jwrite(cls.db / 'clips' / 's00077.json', {'date': '2026-10-24', 'outlet': 'Clip Daily', 'hl': 'A clip', 'link': 'https://c.example.com/1', 'junk': 1})
        jwrite(cls.db / 'reprints' / 'rp-abc123.json', {'story': 's00001', 'outlet': 'Rep Weekly', 'link': 'https://r.example.com/1'})
        jwrite(cls.db / 'edits' / 's00003.json', {'removed': True})
        jwrite(cls.db / 'edits' / 's00001.json', {'topic': 'Other'})
        jwrite(cls.db / 'notes' / 's00001.json', {'text': 'team note stays on the PC'})
        cls.out = cls.d / 'out' / 'for_update.json'
        cls.res = MFU.make(cls.wb, cls.db, PIPE_REAL, cls.out)
        cls.fu = json.loads(Path(cls.res['path']).read_text(encoding='utf-8'))

    def test_header_and_fingerprint(self):
        fu = self.fu
        self.assertEqual((fu['format'], fu['format_version']), (F.FORMAT_FOR_UPDATE, 1))
        self.assertRegex(fu['created_at'], r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$')
        self.assertEqual(fu['fingerprint']['workbook_sha256'], self.sha)
        self.assertEqual(sha(self.wb), self.sha)      # workbook untouched

    def test_stories_have_no_article_text(self):
        s = {r['id']: r for r in self.fu['stories']}
        self.assertEqual(set(s), {'s00001', 's00003'})
        self.assertNotIn('text_en', s['s00001'])
        self.assertNotIn('twhy', s['s00001'])
        blob = json.dumps(self.fu)
        self.assertNotIn('TRANSLATED ARTICLE TEXT', blob)
        self.assertNotIn('a long tone note', blob)
        r = s['s00001']
        for k in ('id', 'date', 'outlet', 'pub', 'hl', 'link', 'plink', 'also', 'reps', 'media', 'county', 'reach', 'lang', 'topic', 'bills'):
            self.assertIn(k, r)
        self.assertEqual(r['also'], 'Echo Times')
        self.assertEqual([x['outlet'] for x in r['reps']], ['Echo Times'])
        self.assertEqual(set(r['reps'][0]), set(MFU.REP_KEEP))

    def test_rows_index_has_every_row_kind(self):
        rows = self.fu['rows']
        self.assertEqual(rows['cols'], ['aid', 'sid', 'kind', 'outlet', 'date', 'hl', 'links', 'files'])
        kinds = {r[0]: r[2] for r in rows['rows']}
        self.assertEqual(kinds['00001'], 'O')
        self.assertEqual(kinds['00002'], 'R')
        self.assertEqual(kinds['00009'], 'X')         # the Removed tab
        self.assertIn('aid', rows['next'])
        self.assertGreaterEqual(int(rows['next']['aid']), 10)
        self.assertIn('Headline', self.fu['covcols'])

    def test_button_memory(self):
        m = self.fu['memory']
        self.assertEqual((m['searched_to'], m['searched_run']), ('2026-10-24', 'run-bbbb2'))     # newest find run with a searched_to
        self.assertNotIn('rows', m['runs']['run-aaaa1'])
        self.assertNotIn('secret_big', m['runs']['run-aaaa1'])
        self.assertEqual(m['runs']['run-bbbb2']['unsaved_rows'], 2)
        self.assertNotIn('unsaved_rows', m['runs']['run-aaaa1'])
        self.assertEqual(set(m['clips']['s00077']), {'date', 'outlet', 'hl', 'link'})
        self.assertEqual(m['reprints']['rp-abc123']['story'], 's00001')
        self.assertEqual(m['edits_removed'], ['s00003'])
        self.assertNotIn('notes', m)

    def test_reference_blocks_and_never_overwrite(self):
        for k in ('idmap', 'billsinfo', 'fetchrules', 'release_texts'):
            self.assertIn(k, self.fu)
        self.assertIn('skip_urls', self.fu['fetchrules'])
        r2 = MFU.make(self.wb, self.db, PIPE_REAL, self.out)
        self.assertNotEqual(r2['path'], self.res['path'])
        self.assertTrue(Path(self.res['path']).is_file())

    def test_refuses_missing_workbook(self):
        with self.assertRaises(MFU.Refused):
            MFU.make(self.d / 'nope.xlsx', self.db, PIPE_REAL, self.d / 'o2' / 'x.json')

    def test_cli_in_app_root_layout(self):
        app = ROOT / 'mfu_app'
        lay = PCLayout(app)
        lay.workbook.parent.mkdir(parents=True)
        shutil.copy2(self.wb, lay.workbook)
        shutil.copytree(PIPE_REAL, lay.pipeline)
        p = subprocess.run([sys.executable, '-I', str(UF / 'make_for_update.py'), '--app-root', str(app), '--no-release-texts'],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        r = json.loads(p.stdout.strip().splitlines()[-1])
        self.assertTrue(Path(r['path']).is_file())
        self.assertEqual(Path(r['path']).parent, lay.for_update)
        self.assertNotIn('release_texts', json.loads(Path(r['path']).read_text(encoding='utf-8')))


# ---------------------------------------------------------------- the update zip


def synthetic_db(d: Path, sha_unused=None):
    ex = json.loads(EXAMPLE_DB.read_text(encoding='utf-8'))
    for coll, docs in ex.items():
        if isinstance(docs, dict):
            for k, v in docs.items():
                jwrite(d / coll / f'{k}.json', v)
    return d


class ZipRules(unittest.TestCase):
    n = 0

    def setUp(self):
        ZipRules.n += 1
        self.d = ROOT / f'zip{ZipRules.n}'
        self.d.mkdir()
        self.app = self.d / 'app'
        self.lay = PCLayout(self.app)
        self.lay.workbook.parent.mkdir(parents=True)
        self.lay.workbook.write_bytes(b'workbook bytes v1')
        self.sha = sha(self.lay.workbook)
        self.db = synthetic_db(self.d / 'db')
        self.zip = F.pack_update_zip(self.d / 'update.zip', self.db, self.sha)

    def rezip(self, name, mutate):
        """copy self.zip to <name> with mutate(entries dict, manifest dict) applied; manifest kept as the (possibly changed) dict"""
        with zipfile.ZipFile(self.zip) as z:
            entries = {i.filename: z.read(i) for i in z.infolist()}
        man = json.loads(entries.pop('manifest.json'))
        mutate(entries, man)
        extra = {}
        out = self.d / name
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('manifest.json', json.dumps(man))
            for k, v in entries.items():
                if isinstance(v, zipfile.ZipInfo):
                    continue
                z.writestr(k, v)
            for info, data in extra.get('infos', []):
                z.writestr(info, data)
        return out

    def refused(self, path, code):
        with self.assertRaises(F.UpdateRefused) as cm:
            TU.inspect_update(path, self.lay)
        self.assertEqual(cm.exception.code, code, cm.exception.msg)
        self.assertEqual(list((self.lay.updates / 'staging').glob('*')) if (self.lay.updates / 'staging').exists() else [], [])   # nothing left behind

    def test_round_trip(self):
        r = TU.inspect_update(self.zip, self.lay)
        self.assertTrue(r['proceed'])
        self.assertEqual(r['fingerprint']['status'], 'match')
        self.assertEqual(r['runs'], ['run-example1'])
        stage = Path(r['stage'])
        self.assertTrue((stage / 'db' / 'runs' / 'run-example1.json').is_file())
        self.assertEqual(json.loads((stage / 'db' / 'pages' / 'NEW-run-example1-1.json').read_text()),
                         json.loads((self.db / 'pages' / 'NEW-run-example1-1.json').read_text()))
        m = json.loads((stage / 'manifest.json').read_text())
        self.assertEqual((m['format'], m['format_version'], m['source']['workbook_sha256']), (F.FORMAT_UPDATE, 1, self.sha))
        self.assertEqual(set(m['files']), {f'db/{c}/{p.name}' for c in F.COLLECTIONS for p in (self.db / c).glob('*.json')})

    def test_tampered_file_refused(self):
        def mut(e, m):
            e['db/pages/NEW-run-example1-1.json'] = e['db/pages/NEW-run-example1-1.json'].replace(b'Gabriel', b'Gabrie1')
        self.refused(self.rezip('t.zip', mut), 'HASH_MISMATCH')

    def test_tampered_manifest_hash_refused(self):
        def mut(e, m):
            m['files']['db/runs/run-example1.json']['sha256'] = '0' * 64
        self.refused(self.rezip('t.zip', mut), 'HASH_MISMATCH')

    def test_unlisted_and_missing_files_refused(self):
        self.refused(self.rezip('a.zip', lambda e, m: e.update({'db/pages/extra.json': b'{}'})), 'UNLISTED_FILE')
        self.refused(self.rezip('b.zip', lambda e, m: e.pop('db/tones/sNEW-run-example1-1.json')), 'MISSING_FILE')

    def test_not_json_refused(self):
        def mut(e, m):
            e['db/pages/NEW-run-example1-1.json'] = b'not json'
            m['files']['db/pages/NEW-run-example1-1.json'] = {'sha256': F.sha256_bytes(b'not json'), 'bytes': 8}
        self.refused(self.rezip('j.zip', mut), 'BAD_JSON')

    def test_allow_list(self):
        bad = ['evil.py', 'run.exe', 'db/runs/x.py', 'db/runs/x.html', 'db/other/x.json', 'db/runs/sub/x.json', 'script.js', 'db/runs/.json',
               '../evil.json', 'db/../../evil.json', '/etc/passwd', 'C:/Windows/x.json', 'db\\runs\\x.json', 'db/runs/CON.json',
               'db/runs/a b.json', 'db/runs/x.json.exe', '//server/share/x.json']
        for name in bad:
            ok, why = F.entry_ok(name)
            self.assertFalse(ok, name)
        for name in ('manifest.json', 'db/runs/run-abc12.json', 'db/pages/NEW-run-1-1.json', 'db/pages/rp-ab12cd.json', 'db/tones/sNEW-run-1-1.json'):
            self.assertTrue(F.entry_ok(name)[0], name)

    def test_bad_entries_in_zip_refused_before_anything_is_read(self):
        for name in ('evil.py', 'tool.exe', '../escape.json', '/abs.json', 'db/pages/x.html'):
            out = self.d / 'bad.zip'
            if out.exists():
                out.unlink()
            with zipfile.ZipFile(self.zip) as src, zipfile.ZipFile(out, 'w') as z:
                for i in src.infolist():
                    z.writestr(i.filename, src.read(i))
                z.writestr(zipfile.ZipInfo(name), b'{}')
            self.refused(out, 'BAD_ENTRY')

    def test_symlink_entry_refused(self):
        out = self.d / 'link.zip'
        with zipfile.ZipFile(self.zip) as src, zipfile.ZipFile(out, 'w') as z:
            for i in src.infolist():
                z.writestr(i.filename, src.read(i))
            zi = zipfile.ZipInfo('db/pages/link.json')
            zi.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(zi, 'db/runs/run-example1.json')
        self.refused(out, 'BAD_ENTRY')

    def test_zip_bomb_ratio_refused(self):
        def mut(e, m):
            big = b'{"a":"' + b'0' * (8 * 1024 * 1024) + b'"}'
            e['db/pages/bomb.json'] = big
            m['files']['db/pages/bomb.json'] = {'sha256': F.sha256_bytes(big), 'bytes': len(big)}
        self.refused(self.rezip('bomb.zip', mut), 'ZIP_BOMB')

    def test_size_and_count_caps(self):
        old = (F.MAX_FILES, F.MAX_TOTAL_BYTES, F.MAX_FILE_BYTES)
        self.addCleanup(lambda: (setattr(F, 'MAX_FILES', old[0]), setattr(F, 'MAX_TOTAL_BYTES', old[1]), setattr(F, 'MAX_FILE_BYTES', old[2])))
        F.MAX_FILES = 3
        self.refused(self.zip, 'TOO_MANY_FILES')
        F.MAX_FILES = old[0]
        F.MAX_TOTAL_BYTES = 500
        self.refused(self.zip, 'TOO_BIG')
        F.MAX_TOTAL_BYTES = old[1]
        F.MAX_FILE_BYTES = 100
        self.refused(self.zip, 'TOO_BIG')

    def test_header_that_lies_about_size_refused(self):
        out = self.d / 'lie.zip'
        shutil.copy2(self.zip, out)
        # raise the declared uncompressed size of one entry in both headers: the data read will not match it
        raw = bytearray(out.read_bytes())
        name = b'db/runs/run-example1.json'
        with zipfile.ZipFile(out) as z:
            real = z.getinfo('db/runs/run-example1.json').file_size
        import struct
        for sig, off in ((b'PK\x03\x04', 22), (b'PK\x01\x02', 24)):
            pos = 0
            while True:
                pos = raw.find(sig, pos)
                if pos < 0:
                    break
                nlen = struct.unpack_from('<H', raw, pos + (26 if sig == b'PK\x03\x04' else 28))[0]
                nstart = pos + (30 if sig == b'PK\x03\x04' else 46)
                if bytes(raw[nstart:nstart + nlen]) == name:
                    struct.pack_into('<I', raw, pos + off, real + 5)
                pos += 4
        out.write_bytes(bytes(raw))
        with self.assertRaises(F.UpdateRefused):
            TU.inspect_update(out, self.lay)

    def test_newer_format_and_missing_fingerprint(self):
        def newer(e, m):
            m['format_version'] = 2
        self.refused(self.rezip('n.zip', newer), 'NEWER_FORMAT')

        def nofp(e, m):
            m['source'] = {}
        self.refused(self.rezip('f.zip', nofp), 'BAD_MANIFEST')

        def wrongfmt(e, m):
            m['format'] = 'something-else'
        self.refused(self.rezip('w.zip', wrongfmt), 'BAD_MANIFEST')

    def test_not_a_zip(self):
        p = self.d / 'x.zip'
        p.write_bytes(b'hello')
        self.refused(p, 'BAD_ZIP')

    def test_fingerprint_mismatch_is_reported_and_not_silent(self):
        self.lay.workbook.write_bytes(b'workbook edited in Excel')
        r = TU.inspect_update(self.zip, self.lay)
        self.assertFalse(r['proceed'])
        self.assertEqual(r['fingerprint']['status'], 'mismatch')
        self.assertIn('different version of the workbook', r['fingerprint']['message'])
        with self.assertRaises(TU.FingerprintMismatch) as cm:
            TU.preview(self.lay, r['update_id'])
        self.assertIn(self.sha[:8], cm.exception.msg)
        self.assertFalse((self.lay.updates / 'work').exists())            # nothing was started
        with self.assertRaises(TU.FingerprintMismatch):
            TU.save(self.lay, r['update_id'], 'tok')

    def test_cli_exit_codes(self):
        py = [sys.executable, '-I', str(UF / 'take_update.py')]
        p = subprocess.run(py + ['inspect', '--app-root', str(self.app), '--zip', str(self.zip)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        bad = self.rezip('b.zip', lambda e, m: e.update({'evil.py': b'print(1)'}))
        p = subprocess.run(py + ['inspect', '--app-root', str(self.app), '--zip', str(bad)], capture_output=True, text=True)
        self.assertEqual(p.returncode, TU.EXIT_ZIP_REFUSED)
        self.assertEqual(json.loads(p.stdout)['refused'], 'BAD_ENTRY')
        self.lay.workbook.write_bytes(b'changed')
        p = subprocess.run(py + ['inspect', '--app-root', str(self.app), '--zip', str(self.zip)], capture_output=True, text=True)
        self.assertEqual(p.returncode, TU.EXIT_MISMATCH)

    def test_layout_cannot_leave_the_app_folder(self):
        lay = PCLayout(self.app, overrides={'db': '../elsewhere'})
        with self.assertRaises(OutsideAppFolder):
            lay.db
        with self.assertRaises(OutsideAppFolder):
            self.lay.inside(self.d / 'db')


# ---------------------------------------------------------------- through the real saver


class ThroughSaver(unittest.TestCase):
    n = 0

    def setUp(self):
        ThroughSaver.n += 1
        self.d = ROOT / f'sv{ThroughSaver.n}'
        self.app = self.d / 'app'
        self.lay = PCLayout(self.app)
        mini = load_mini()
        row = {'Article ID': '10001', 'Story ID': 's00001', 'Original or reprint': 'Original', 'Date': '2026-10-01', 'Year': '2026',
               'Outlet': 'Old Gazette', 'Headline': 'Old story', 'Publisher link': 'https://old.example.com/a'}
        self.lay.workbook.parent.mkdir(parents=True)
        mini.make(str(self.lay.workbook), [mini.row(**row)])
        shutil.copytree(PIPE_STUB, self.lay.pipeline)
        (self.lay.copies / 'articles').mkdir(parents=True)
        (self.lay.copies / 'articles' / 'manifest.json').write_text('{"articles":{}}')
        self.lay.library.mkdir(parents=True)
        self.sha = sha(self.lay.workbook)
        r = TU.init_baseline(self.lay, saver=SAVER)
        self.assertEqual(r['exit_code'], 0, r)
        db = synthetic_db(self.d / 'srcdb')
        self.zip = F.pack_update_zip(self.d / 'update.zip', db, self.sha)
        # the tracker's own store already holds an older run and a pending hand edit
        jwrite(self.lay.db / 'runs' / 'run-older1.json', {'at': '2026-10-01T00:00:00Z', 'mode': 'find', 'searched_to': '2026-09-30'})
        jwrite(self.lay.db / 'edits' / 's00001.json', {'topic': 'Housing'})

    def test_preview_then_save_then_merge(self):
        r = TU.inspect_update(self.zip, self.lay)
        self.assertTrue(r['proceed'])
        uid = r['update_id']
        pv = TU.preview(self.lay, uid, saver=SAVER, today='2026-10-30')
        self.assertEqual((pv['exit_code'], pv.get('refusal')), (0, None), pv)
        self.assertEqual(pv['run'], 'run-example1')
        self.assertEqual(pv['diff']['rows_added']['Coverage'], 2)
        self.assertEqual(sha(self.lay.workbook), self.sha)                       # preview writes nothing
        self.assertEqual(list(self.lay.backups.glob('*')) if self.lay.backups.exists() else [], [])
        sv = TU.save(self.lay, uid, pv['diff']['token'], saver=SAVER, today='2026-10-30')
        self.assertEqual((sv['exit_code'], sv.get('refusal')), (0, None), sv)
        self.assertTrue(sv['written'] and sv['confirmed'])
        self.assertIn('reused_preview', sv)                                        # the save took the preview's finished passes
        self.assertEqual(sv['out_dir'], pv['out_dir'])
        self.assertEqual(sorted(p.name for p in (self.lay.updates / 'work' / uid).iterdir() if p.is_dir() and not p.name.startswith('db_composed')), [Path(pv['out_dir']).name])   # no second pipeline folder (PCEDITS-v1: the preview and the save each compose their own db folder)
        self.assertNotEqual(sha(self.lay.workbook), self.sha)
        self.assertEqual(sha(next(self.lay.backups.glob('*.xlsx'))), self.sha)     # backup of the old workbook
        # the run doc is now in the tracker's store, marked written, with the real ids
        doc = json.loads((self.lay.db / 'runs' / 'run-example1.json').read_text())
        self.assertTrue(doc['sheet']['written'])
        self.assertEqual(doc['ids']['NEW-run-example1-1'], '10002')
        self.assertTrue((self.lay.db / 'runs' / 'run-older1.json').is_file())       # untouched
        # staging moved to done, nothing deleted
        self.assertFalse((self.lay.updates / 'staging' / uid).exists())
        self.assertTrue((Path(sv['done_dir']) / 'manifest.json').is_file())
        self.assertTrue((self.lay.library / '2026' / 'ws10002o-s04297.html').is_file())
        # the next for-Update memory sees the run as saved
        mem = MFU.button_memory(self.lay.db)
        self.assertNotIn('unsaved_rows', mem['runs']['run-example1'])

    def test_save_without_reuse_runs_everything_again(self):
        r = TU.inspect_update(self.zip, self.lay)
        uid = r['update_id']
        pv = TU.preview(self.lay, uid, saver=SAVER, today='2026-10-30')
        sv = TU.save(self.lay, uid, pv['diff']['token'], saver=SAVER, today='2026-10-30', reuse_preview=False)
        self.assertEqual((sv['exit_code'], sv.get('refusal')), (0, None), sv)
        self.assertNotIn('reused_preview', sv)
        self.assertNotEqual(sv['out_dir'], pv['out_dir'])
        self.assertTrue(sv['written'])

    def test_save_after_the_workbook_changed_does_not_reuse(self):
        r = TU.inspect_update(self.zip, self.lay)
        uid = r['update_id']
        pv = TU.preview(self.lay, uid, saver=SAVER, today='2026-10-30')
        mini = load_mini()
        mini.make(str(self.lay.workbook), [mini.row(**{'Article ID': '10001', 'Story ID': 's00001', 'Original or reprint': 'Original',
                                                      'Date': '2026-10-01', 'Year': '2026', 'Outlet': 'Old Gazette', 'Headline': 'Edited by hand'})])
        TU.init_baseline(self.lay, saver=SAVER)                                    # the hand edit is accepted as the new baseline
        sv = TU.save(self.lay, uid, pv['diff']['token'], saver=SAVER, today='2026-10-30', accept_mismatch=True)
        self.assertNotIn('reused_preview', sv)
        self.assertEqual(sv['refusal']['code'], 'TOKEN_STALE')                     # a fresh full diff is against another workbook
        self.assertIn('workbook', sv['full_run_reason'])
        self.assertTrue((self.lay.updates / 'staging' / uid).is_dir())

    def test_save_with_wrong_token_changes_nothing(self):
        r = TU.inspect_update(self.zip, self.lay)
        sv = TU.save(self.lay, r['update_id'], 'deadbeefdeadbeef', saver=SAVER, today='2026-10-30')
        self.assertEqual((sv['exit_code'], sv['refusal']['code']), (2, 'TOKEN_STALE'))
        self.assertEqual(sha(self.lay.workbook), self.sha)
        self.assertTrue((self.lay.updates / 'staging' / r['update_id']).is_dir())    # still waiting
        self.assertFalse((self.lay.db / 'runs' / 'run-example1.json').exists())

    def test_accepting_a_mismatch_still_goes_through_the_saver_checks(self):
        # the workbook changed after "for Update" was made; the ledger knows the old checksum, so the saver refuses even if the user accepts
        mini = load_mini()
        mini.make(str(self.lay.workbook), [mini.row(**{'Article ID': '10001', 'Story ID': 's00001', 'Original or reprint': 'Original',
                                                      'Date': '2026-10-01', 'Year': '2026', 'Outlet': 'Old Gazette', 'Headline': 'Edited by hand'})])
        r = TU.inspect_update(self.zip, self.lay)
        self.assertEqual(r['fingerprint']['status'], 'mismatch')
        pv = TU.preview(self.lay, r['update_id'], saver=SAVER, today='2026-10-30', accept_mismatch=True)
        self.assertEqual(pv['exit_code'], 2)
        self.assertEqual(pv['refusal']['code'], 'SHA_MISMATCH')
        self.assertEqual(pv['fingerprint']['status'], 'mismatch')

    def test_local_edits_option_composes_a_db(self):
        r = TU.inspect_update(self.zip, self.lay)
        stage = self.lay.updates / 'staging' / r['update_id']
        work = self.d / 'w'
        work.mkdir()
        self.assertEqual(TU._db_for_saver(self.lay, stage, work, False), (stage / 'db', {}))
        comp, sent = TU._db_for_saver(self.lay, stage, work, True)
        self.assertTrue((comp / 'edits' / 's00001.json').is_file())
        self.assertEqual(set(sent), {'s00001'})
        self.assertTrue((comp / 'runs' / 'run-example1.json').is_file())
        self.assertFalse((stage / 'db' / 'edits' / 's00001.json').exists())
        # PCEDITS-v1: every call makes its own folder (a second call used to copy into the first one's and fail)
        comp2, _ = TU._db_for_saver(self.lay, stage, work, True)
        comp3, _ = TU._db_for_saver(self.lay, None, work, True)       # an edits-only save: nothing but the edits
        self.assertEqual(len({comp, comp2, comp3}), 3)
        self.assertEqual(sorted(p.name for p in comp3.iterdir()), ['edits'])
        # an edit the update carries itself wins; an edit already reported is not pending
        jwrite(stage / 'db' / 'edits' / 's00001.json', {'topic': 'Carried'})
        comp4, sent4 = TU._db_for_saver(self.lay, stage, work, True)
        self.assertEqual((json.loads((comp4 / 'edits' / 's00001.json').read_text())['topic'], sent4), ('Carried', {}))
        jwrite(self.lay.db / 'edits' / 's00001.json', {'topic': 'Housing', 'at': '2026-10-02T00:00:00Z', 'reported': '2026-10-02T00:00:00Z'})
        self.assertEqual(TU.edits_summary(self.lay), {'n': 0, 'removed': [], 'edited': {}})
        jwrite(self.lay.db / 'edits' / 's00002.json', {'removed': True, 'at': '2026-10-02T00:00:00Z'})
        jwrite(self.lay.db / 'edits' / 's00003.json', {'outlet': 'X', 'bills': ['AB 1'], 'at': '2026-10-02T00:00:00Z'})
        self.assertEqual(TU.edits_summary(self.lay), {'n': 2, 'removed': ['s00002'], 'edited': {'s00003': ['bills', 'outlet']}})

    def test_edits_writeback_moves_never_deletes_and_leaves_changed_docs(self):
        out = self.d / 'saverout'
        out.mkdir()
        jwrite(out / 'writeback.json', {'edits_delete_or_archive': ['s00001', 's00004', 's00009'], 'edits_reported': {'s00005': '2026-10-02T00:00:00Z', 's00006': '2026-10-02T00:00:00Z'}})
        for sid in ('s00004', 's00005', 's00006'):
            jwrite(self.lay.db / 'edits' / f'{sid}.json', {'topic': 'T', 'at': '2026-10-02T00:00:00Z'})
        sent = {sid: TU._file_sha(self.lay.db / 'edits' / f'{sid}.json') for sid in ('s00001', 's00004', 's00005', 's00006')}
        jwrite(self.lay.db / 'edits' / 's00004.json', {'topic': 'changed again', 'at': '2026-10-03T00:00:00Z'})       # edited again while the save ran
        res = TU.apply_edits_writeback(self.lay, out, sent)
        self.assertEqual(len(res['edits_applied']), 1)                                  # s00001 moved
        self.assertTrue(res['edits_applied'][0].replace('\\', '/').count('_applied/edits/s00001.'))
        self.assertEqual(res['edits_changed_meanwhile'], ['s00004'])
        self.assertTrue((self.lay.db / 'edits' / 's00004.json').is_file())               # still pending
        self.assertEqual(res['edits_reported'], ['s00005', 's00006'])
        self.assertEqual(json.loads((self.lay.db / 'edits' / 's00005.json').read_text())['reported'], '2026-10-02T00:00:00Z')
        self.assertFalse((self.lay.db / 'edits' / 's00001.json').exists())
        self.assertEqual(len(list((self.lay.db / '_applied' / 'edits').glob('*.json'))), 1)

    def test_edits_only_preview_and_save_remove_a_story(self):
        """PCEDITS-v1 through the real save program: no update zip; the story moves to Removed, the doc is set aside; a refused save moves nothing"""
        jwrite(self.lay.db / 'edits' / 's00001.json', {'removed': True, 'at': '2026-10-05T10:00:00Z'})
        uid = TU.new_edits_id(self.lay)
        pv = TU.preview(self.lay, uid, saver=SAVER, today='2026-10-30', edits_only=True)
        self.assertEqual((pv['exit_code'], pv.get('refusal')), (0, None), pv)
        self.assertTrue(pv['edits_only'])
        self.assertEqual(pv['diff']['rows_added'].get('Removed'), 1)
        self.assertEqual(sha(self.lay.workbook), self.sha)
        bad = TU.save(self.lay, uid, '0' * 16, saver=SAVER, today='2026-10-30', edits_only=True)       # wrong token: refused
        self.assertFalse(bad['written'], bad)
        self.assertTrue((self.lay.db / 'edits' / 's00001.json').is_file(), 'a refused save leaves the edit pending')
        sv = TU.save(self.lay, uid, pv['diff']['token'], saver=SAVER, today='2026-10-30', edits_only=True)
        self.assertEqual((sv['exit_code'], sv.get('refusal')), (0, None), sv)
        self.assertTrue(sv['written'])
        self.assertEqual(sv['local_db']['edits_applied'] and len(sv['local_db']['edits_applied']), 1)
        self.assertFalse((self.lay.db / 'edits' / 's00001.json').exists())
        self.assertEqual(len(list((self.lay.db / '_applied' / 'edits').glob('s00001.*.json'))), 1)
        self.assertEqual(sha(next(self.lay.backups.glob('*.xlsx'))), self.sha)


if __name__ == '__main__':
    unittest.main()
