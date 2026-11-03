"""YTSTATION-v1 / YTBROADCAST-v1 / YTLINK-v1 through the saver (mirrors build/tests/sheet_task/test_ytstation.py).

What the old tracker's sheet_task.py does for a station's own YouTube video, and that the saver must accept and show:
  * a find with `_av` marked as a station channel becomes a new story: Medium TV, Format "Broadcast segment", an Audio & video details row;
    a YouTube link without the mark is still dropped (NOBLOGS-v1); two videos differ by their ?v= id (YTLINK-v1: both are added);
  * a run doc's `attach` list turns an EXISTING story into a broadcast story: Format -> "Broadcast segment" (an explicit override of fill-blanks-only,
    YTBROADCAST-v1, this case only), Medium "Video" -> TV / Radio, the Audio & video details row's Item type -> "Broadcast segment", blank
    Channel / Station / Network / YouTube link filled, a missing AV row added; the saved copy and every other cell stay.
The saver's own comparison (saver_diff) allows exactly those changes, and only for the cells sheet_task reports in result.yt_attached.

End to end through `saver.py preview` (real sheet_task.py from code/, stub build_data / relmatch as in test_saver_save.py), plus direct tests of the
allow-list in saver_diff.compare.

    python3 -I -m unittest discover -s tests -t tests"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAVER_DIR = HERE.parent
SRC = SAVER_DIR / 'src'
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))
import saver_diff as D       # noqa: E402
from wbhelp import make_wb, pipeline_source, REPO   # noqa: E402

SAVER = SRC / 'saver.py'
TMP = tempfile.TemporaryDirectory()
ROOT = Path(TMP.name)
PIPE = ROOT / 'pipeline'
MASTER = 'AJG Coverage - NewsBank.xlsx'
MINI = REPO / 'build' / 'tests' / 'sheet_task' / 'audit' / 'mini.py'
STUB_BUILD = ("import sys, os\nos.makedirs(sys.argv[3], exist_ok=True)\n"
              "for n in ('data', 'rows', 'idmap', 'covcols'):\n    open(os.path.join(sys.argv[3], n + '.json'), 'w').write('{}')\n")
URL = 'https://www.youtube.com/watch?v=P6zsjIepWaQ'
URL2 = 'https://www.youtube.com/watch?v=Q7ztkJfxXbR'
AV_FOX = {'Item type': 'Broadcast segment', 'Channel': 'FOX 11 Los Angeles', 'Station': 'KTTV', 'Network': 'FOX',
          'Episode/segment title': 'Special Report: Assemblyman Jesse Gabriel', 'Air/publish date': '2022-03-17', 'YouTube link': URL, 'Details from': 'YouTube page'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def setUpModule():
    global MINIMOD, AVCOLS
    shutil.copytree(pipeline_source(), PIPE, ignore=shutil.ignore_patterns('docs', '__pycache__', '*.pyc', '_history', 'tracker', 'fetch2',
                                                                          'billstatus', 'fetch_rated1'))
    (PIPE / 'build_data.py').write_text(STUB_BUILD, encoding='utf-8')
    (PIPE / 'relmatch.py').write_text('import sys\n', encoding='utf-8')
    subprocess.run([sys.executable, '-I', str(SAVER_DIR / 'tools' / 'pipeline_sha.py'), str(PIPE)], check=True, capture_output=True)
    os.environ.setdefault('AUDIT_OUT', str(ROOT / 'aud'))
    spec = importlib.util.spec_from_file_location('mini_wb', MINI)
    MINIMOD = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(MINIMOD)
    sys.path.insert(0, str(PIPE))
    import avtab
    AVCOLS = list(avtab.COLS)


def cli(*args):
    p = subprocess.run([sys.executable, '-I', str(SAVER), *map(str, args)], capture_output=True, text=True, encoding='utf-8')
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {'raw': p.stdout, 'err': p.stderr}
    return p.returncode, res


def mini_with_av(path, rows, av_rows):
    """the audit mini workbook (Coverage, Originals, Removed) plus an Audio & video details tab"""
    import openpyxl
    MINIMOD.make(str(path), [MINIMOD.row(**r) for r in rows])
    wb = openpyxl.load_workbook(path)
    ws = wb.create_sheet('Audio & video details')
    ws.append(AVCOLS)
    for r in av_rows:
        ws.append([r.get(c) for c in AVCOLS])
    wb.save(path)
    return path


BASE = {'Data Source': 'Web search (TinyFish)', 'Edition': 'Web', 'Language': 'English', 'Link status': 'Publisher URL', 'Original or reprint': 'Original',
        'Medium': 'TV', 'Format': 'Article', '# of reprints': 0, 'Year': '2026', 'Date': '2026-10-20'}


def tracked():
    return [dict(BASE, **{'Article ID': '00100', 'Story ID': 's00100', 'Outlet': 'FOX 11 Los Angeles', 'Headline': 'Gas rebate debated',
                          'Publisher link': 'https://www.foxla.com/news/gas', 'File name': 'saved.html', 'Saved Copy?': 'Yes'}),
            dict(BASE, **{'Article ID': '00101', 'Story ID': 's00101', 'Outlet': 'KTLA', 'Medium': 'Video', 'Format': 'Video clip', 'Headline': 'Budget vote',
                          'Publisher link': 'https://ktla.com/news/budget'}),
            dict(BASE, **{'Article ID': '00102', 'Story ID': 's00102', 'Outlet': 'ABC7 Los Angeles', 'Headline': 'Fire bill', 'Publisher link': 'https://abc7.com/fire',
                          'Team note': 'checked'})]


def av_rows():
    return [{'Article ID': '00100', 'Story ID': 's00100', 'Medium': 'TV', 'Item type': 'Video clip'},
            {'Article ID': '00102', 'Story ID': 's00102', 'Medium': 'TV', 'Item type': 'Web story', 'Channel': 'ABC7 Los Angeles'}]


def attach_item(vid, row_link, ch, st, net, med='TV'):
    return {'row_link': row_link, 'link': 'https://www.youtube.com/watch?v=' + vid, 'title': 'x', 'channel': ch, 'station': st, 'network': net,
            'medium': med, 'date': '2026-10-20', 'story': 's'}


def station_find(n, url, title, av_title=None):
    f = {'Article ID': f'NEW-r-{n}', 'Story ID': f'sNEW-r-{n}', 'Original or reprint': 'Original', 'Data Source': 'Web search (TinyFish, YouTube station channel)',
         'Date': '2026-10-19', 'Outlet': 'FOX 11 Los Angeles', 'Headline': title, 'Edition': 'Web', 'Language': 'English',
         'Medium': 'TV', 'Format': 'Broadcast segment', 'Publisher link': url, 'Link status': 'Publisher URL',
         '_av': dict(AV_FOX, **{'YouTube link': url, 'Episode/segment title': av_title or title})}
    return f


class Env:
    n = 0

    def __init__(self, rows, avs, runs):
        Env.n += 1
        self.d = ROOT / f'yt{Env.n}'
        self.d.mkdir()
        self.master = mini_with_av(self.d / MASTER, rows, avs)
        self.db = self.d / 'db'
        (self.db / 'runs').mkdir(parents=True)
        for rid, doc in runs.items():
            (self.db / 'runs' / f'{rid}.json').write_text(json.dumps(doc), encoding='utf-8')
        (self.d / 'library').mkdir()
        (self.d / 'copies' / 'articles').mkdir(parents=True)
        (self.d / 'copies' / 'articles' / 'manifest.json').write_text('{"articles":{}}')
        (self.d / 'backups').mkdir()
        self.state = self.d / 'state'
        cli('init', '--workbook', self.master, '--state', self.state, '--sha', sha(self.master))

    def preview(self):
        return cli('preview', '--workbook', self.master, '--db', self.db, '--pipeline', PIPE, '--copies', self.d / 'copies', '--library', self.d / 'library',
                   '--backups', self.d / 'backups', '--out', self.d / 'out', '--state', self.state, '--today', '2026-10-30')

    def changes(self, res):
        lines = Path(res['diff']['tsv']).read_text(encoding='utf-8').splitlines()[1:]
        return [dict(zip(('sheet', 'row', 'key', 'column', 'kind', 'old', 'new', 'allowed_by'), ln.split('\t'))) for ln in lines]


class AttachThroughPreview(unittest.TestCase):
    """an `attach` list: existing stories become broadcast stories; nothing else changes"""

    @classmethod
    def setUpClass(cls):
        att = [attach_item('P6zsjIepWaQ', 'https://www.foxla.com/news/gas', 'FOX 11 Los Angeles', 'KTTV', 'FOX'),
               attach_item('AAAAAAAAAAA', 'https://ktla.com/news/budget', 'KTLA 5', 'KTLA', 'CW'),
               attach_item('BBBBBBBBBBB', 'https://abc7.com/fire', 'ABC7', 'KABC', 'ABC'),
               attach_item('CCCCCCCCCCC', 'https://nowhere.example/none', 'KTLA 5', 'KTLA', 'CW')]
        # the run also carries one new station find: a run with only `attach` is not "work" for sheet_task.has_work (see AttachOnly below)
        cls.e = Env(tracked(), av_rows(), {'r2': {'at': '2026-10-30T10:00:00Z', 'rows': [station_find(9, URL2, 'Another report')], 'attach': att}})
        cls.code, cls.res = cls.e.preview()
        cls.ch = cls.e.changes(cls.res) if cls.code == 0 else []

    def cell(self, sheet, key, col):
        m = [c for c in self.ch if c['sheet'] == sheet and c['key'].startswith(key) and c['column'] == col]
        return m[0] if m else None

    def test_accepted_without_refusal(self):
        self.assertEqual((self.code, self.res.get('refusal')), (0, None), self.res)
        self.assertEqual(self.res['diff']['disallowed'], 0)

    def test_format_override_on_coverage_and_originals(self):
        for sheet in ('Coverage', 'Originals'):
            for key, old in (('00100', 'Article'), ('00101', 'Video clip'), ('00102', 'Article')):
                c = self.cell(sheet, key, 'Format')
                self.assertIsNotNone(c, (sheet, key))
                self.assertEqual((c['kind'], c['old'], c['new'], c['allowed_by']), ('changed', old, 'Broadcast segment', 'yt_attach'))

    def test_medium_video_becomes_tv_and_tv_stays(self):
        c = self.cell('Coverage', '00101', 'Medium')
        self.assertEqual((c['old'], c['new'], c['allowed_by']), ('Video', 'TV', 'yt_attach'))
        self.assertIsNone(self.cell('Coverage', '00100', 'Medium'))

    def test_av_item_type_override_and_blank_fills(self):
        c = self.cell('Audio & video details', '00100', 'Item type')
        self.assertEqual((c['old'], c['new'], c['allowed_by']), ('Video clip', 'Broadcast segment', 'yt_attach'))
        c = self.cell('Audio & video details', '00102', 'Item type')
        self.assertEqual((c['old'], c['new'], c['allowed_by']), ('Web story', 'Broadcast segment', 'yt_attach'))
        for col, new in (('Channel', 'FOX 11 Los Angeles'), ('Station', 'KTTV'), ('Network', 'FOX'), ('YouTube link', 'https://www.youtube.com/watch?v=P6zsjIepWaQ')):
            c = self.cell('Audio & video details', '00100', col)
            self.assertEqual((c['kind'], c['new'], c['allowed_by']), ('filled', new, 'blank_fill'), col)
        self.assertIsNone(self.cell('Audio & video details', '00102', 'Channel'), 'a filled Channel is kept (blanks only)')

    def test_story_without_av_row_gets_one(self):
        rows = [c for c in self.ch if c['sheet'] == 'Audio & video details' and c['key'].startswith('00101')]
        self.assertTrue(rows)
        self.assertTrue(rows and all(c['kind'] == 'added' and c['allowed_by'] == 'new_row' for c in rows))
        d = {c['column']: c['new'] for c in rows}
        self.assertEqual((d['Item type'], d['Channel'], d['Station'], d['Network'], d['Details from'], d['Episode/segment title']),
                         ('Broadcast segment', 'KTLA 5', 'KTLA', 'CW', 'YouTube page', 'Budget vote'))

    def test_nothing_else_changes_and_no_new_story(self):
        allowed = {(c['sheet'], c['column']) for c in self.ch if c['kind'] == 'changed'}
        self.assertEqual(allowed, {('Coverage', 'Format'), ('Coverage', 'Medium'), ('Originals', 'Format'), ('Originals', 'Medium'), ('Audio & video details', 'Item type')})
        self.assertEqual(self.res['diff']['rows_added'], {'Coverage': 1, 'Audio & video details': 2, 'Originals': 1}, 'one new story (the find), not one per attach item')
        self.assertEqual(len({c['key'] for c in self.ch if c['sheet'] == 'Coverage' and c['kind'] == 'added'}), 1)
        self.assertFalse([c for c in self.ch if c['kind'] == 'changed' and c['column'] in ('File name', 'Saved Copy?', 'Headline', 'Team note')])

    def test_unplaced_item_is_for_a_person(self):
        self.assertEqual(len(self.res['judgment']['yt_attach_unplaced']), 1)
        self.assertEqual(self.res['judgment_counts']['yt_attach_unplaced'], 1)
        self.assertEqual(len(self.res['review']['yt_attached']), 3)


class AttachOnly(unittest.TestCase):
    def test_a_run_with_only_attach_items_is_not_queued(self):
        """Documents the old sheet_task.has_work(): it counts runs with `rows`, bills, releases, edits, reprints and pages, not `attach`. A run
        doc holding only attach items therefore reads "Nothing new to write." and its attach list is not applied until a save with other work.
        If sheet_task changes this, this test should be updated, not worked around."""
        e = Env(tracked(), av_rows(), {'r2': {'at': '2026-10-30T10:00:00Z', 'attach': [attach_item('P6zsjIepWaQ', 'https://www.foxla.com/news/gas', 'FOX 11 Los Angeles', 'KTTV', 'FOX')]}})
        code, res = e.preview()
        self.assertEqual((code, res.get('nothing_queued')), (3, True))


class StationFindThroughPreview(unittest.TestCase):
    """new stories from a station's YouTube channel: broadcast stories with an AV row; a plain YouTube link is refused; two videos are two links"""

    @classmethod
    def setUpClass(cls):
        find = station_find(1, URL, 'Special Report: Assemblyman Jesse Gabriel')
        find2 = station_find(3, URL2, 'Special Report, part two')
        other = dict(find, **{'Article ID': 'NEW-r-2', 'Story ID': 'sNEW-r-2', 'Outlet': 'Forbes Breaking News', 'Medium': 'Online news', 'Format': 'Video clip',
                              'Publisher link': 'https://www.youtube.com/watch?v=nIKyZqVQaFo', 'Headline': 'Lawmaker calls out GOP'})
        other.pop('_av')
        cls.e = Env(tracked(), av_rows(), {'r1': {'at': '2026-10-30T10:00:00Z', 'rows': [find, find2, other]}})
        cls.code, cls.res = cls.e.preview()
        cls.ch = cls.e.changes(cls.res) if cls.code == 0 else []

    def test_accepted_and_shaped(self):
        self.assertEqual((self.code, self.res.get('refusal')), (0, None), self.res)
        self.assertEqual(self.res['diff']['rows_added'].get('Coverage'), 2)
        self.assertEqual(self.res['diff']['rows_added'].get('Audio & video details'), 2)
        self.assertEqual(self.res['diff']['disallowed'], 0)
        new = {}
        for c in self.ch:
            if c['sheet'] == 'Coverage' and c['kind'] == 'added':
                new.setdefault(c['key'], {})[c['column']] = c['new']
        self.assertEqual(len(new), 2)
        for v in new.values():
            self.assertEqual((v['Medium'], v['Format'], v['Outlet'], v['Data Source']),
                             ('TV', 'Broadcast segment', 'FOX 11 Los Angeles', 'Web search (TinyFish, YouTube station channel)'))
        self.assertEqual({v['Publisher link'] for v in new.values()}, {URL, URL2}, 'YTLINK-v1: two ?v= links are two links')
        av = {}
        for c in self.ch:
            if c['sheet'] == 'Audio & video details' and c['kind'] == 'added':
                av.setdefault(c['key'], {})[c['column']] = c['new']
        self.assertEqual({(v['Item type'], v['Channel'], v['Station'], v['Network']) for v in av.values()}, {('Broadcast segment', 'FOX 11 Los Angeles', 'KTTV', 'FOX')})
        self.assertEqual({v['YouTube link'] for v in av.values()}, {URL, URL2})

    def test_plain_youtube_link_is_still_refused(self):
        self.assertNotIn('nIKyZqVQaFo', json.dumps(self.ch))
        sk = (self.res.get('review') or {}).get('skipped') or []
        self.assertTrue(any('nIKyZqVQaFo' in json.dumps(x) for x in sk), sk)


class AllowListIsNarrow(unittest.TestCase):
    """saver_diff.compare: the YTBROADCAST-v1 override is allowed only for the cells and values sheet_task reported"""

    def sheets(self, med='Video', fmt='Video clip', item='Video clip'):
        cov_h = ['Article ID', 'Original or reprint', 'Story ID', 'Medium', 'Format', 'Headline']
        cov = [['10001', 'Original', 's00001', med, fmt, 'H1'], ['10002', 'Original', 's00002', 'Online news', 'Article', 'H2']]
        return {'Coverage': [cov_h, cov], 'Originals': [list(cov_h), [list(r) for r in cov]], 'Audio & video details': [['Article ID', 'Story ID', 'Item type', 'Channel'], [['10001', 's00001', item, None]]]}

    def compare(self, after_over, yt):
        b = make_wb(ROOT / 'b.xlsx', self.sheets(), {})
        sh = self.sheets()
        after_over(sh)
        a = make_wb(ROOT / 'a.xlsx', sh, {})
        res = {'yt_attached': yt} if yt is not None else {}
        return D.compare(b, a, res, None, derived_rel=set(), new_ok={'Audio & video details'})

    def full(self, sh):
        for t in ('Coverage', 'Originals'):
            sh[t][1][0][3], sh[t][1][0][4] = 'TV', 'Broadcast segment'
        sh['Audio & video details'][1][0][2] = 'Broadcast segment'

    ENTRY = {'aid': '10001', 'cells': ['Medium', 'Format'], 'changed': ['Medium Video -> TV', 'Format Video clip -> Broadcast segment', 'AV Item type Video clip -> Broadcast segment']}

    def test_reported_override_is_allowed(self):
        rep = self.compare(self.full, [self.ENTRY])
        self.assertEqual(rep.problems, [])
        self.assertEqual({c.allowed_by for c in rep.changes}, {'yt_attach'})
        self.assertEqual(len(rep.changes), 5)

    def test_same_edit_without_the_result_entry_is_refused(self):
        rep = self.compare(self.full, None)
        self.assertEqual({p.kind for p in rep.problems}, {'cell_changed'})
        self.assertEqual(len(rep.problems), 5)

    def test_entry_for_another_story_does_not_cover_it(self):
        rep = self.compare(self.full, [dict(self.ENTRY, aid='10002')])
        self.assertEqual(len(rep.problems), 5)

    def test_only_the_reported_cells(self):
        rep = self.compare(self.full, [dict(self.ENTRY, cells=['Format'], changed=['Format Video clip -> Broadcast segment'])])
        self.assertEqual(sorted(p.text.split(' / ')[-1].split(':')[0] for p in rep.problems), ['Item type', 'Medium', 'Medium'][0:0] + sorted(['Medium', 'Medium', 'Item type']))

    def test_other_values_are_refused(self):
        def odd(sh):
            for t in ('Coverage', 'Originals'):
                sh[t][1][0][3], sh[t][1][0][4] = 'Newspaper', 'Podcast episode'
            sh['Audio & video details'][1][0][2] = 'Episode'
        rep = self.compare(odd, [self.ENTRY])
        self.assertEqual(len(rep.problems), 5)

    def test_medium_other_than_video_is_not_overridden(self):
        b = make_wb(ROOT / 'b2.xlsx', self.sheets(med='Online news'), {})
        sh = self.sheets(med='Online news')
        self.full(sh)
        a = make_wb(ROOT / 'a2.xlsx', sh, {})
        rep = D.compare(b, a, {'yt_attached': [self.ENTRY]}, None, derived_rel=set(), new_ok=set())
        self.assertEqual(sorted(p.text.split(' / ')[2].split(':')[0] for p in rep.problems), ['Medium', 'Medium'])


if __name__ == '__main__':
    unittest.main()
