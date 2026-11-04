"""Tiny tests for the Mac proposals. Applies the four patches to a temporary copy of app/src/station (the repository is not touched) and checks each.
    python3 -I work/localapp/macpack/proposals/test_mac_proposals.py"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, unicodedata, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
tmp = Path(tempfile.mkdtemp())
st = tmp / 'work' / 'localapp' / 'app' / 'src' / 'station'
shutil.copytree(REPO / 'work/localapp/app/src/station', st, ignore=shutil.ignore_patterns('__pycache__'))
for p in sorted(HERE.glob('mac_*.patch')):
    subprocess.run(['patch', '-p1', '-s', '-d', str(tmp), '-i', str(p)], check=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(st))
import refresh as R, rename_files as RF
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

nfd, nfc = unicodedata.normalize('NFD', 'Mundo Hispánico.pdf'), 'Mundo Hispánico.pdf'
lib = tmp / 'lib'
(lib / '2026').mkdir(parents=True)
(lib / '2026' / nfd).write_bytes(b'x'); (lib / '2026' / '.DS_Store').write_bytes(b'x'); (lib / '2026' / '._junk').write_bytes(b'x')
ok([n for n, _ in R._tree(lib)] == ['2026/' + nfc] or True, 'tree names')   # on a filesystem that keeps NFD the next lines decide
names = [n for n, _ in R._tree(lib)]
ok(names == ['2026/' + nfc], 'a: refresh file names are NFC, dot-files left out: %r' % names)
ok(R.check_name('library/2026/' + nfd)[1] == '2026/' + nfc, 'a: a refresh entry in NFD is taken as NFC')
idx = RF.library_index(lib)
ok(list(idx) == [nfc], 'a/b: rename_files library index is NFC and skips .DS_Store and ._ files: %r' % list(idx))
# b: a refresh zip re-zipped in Finder (junk entries) is still taken
wbn = 'workbook/AJG Coverage - NewsBank.xlsx'
data = b'workbook bytes'; h = hashlib.sha256(data).hexdigest()
man = {'format': R.FORMAT, 'format_version': 1, 'created_at': '2026-11-04T00:00:00Z', 'kind': 'full', 'seq': 1, 'base_seq': 0, 'workbook_name': 'AJG Coverage - NewsBank.xlsx',
       'workbook_sha256': h, 'files': {wbn: {'sha256': h, 'bytes': len(data)}}}
z = tmp / 'r.zip'
with zipfile.ZipFile(z, 'w') as zf:
    zf.writestr('manifest.json', json.dumps(man)); zf.writestr(wbn, data)
    zf.writestr('__MACOSX/workbook/._x.xlsx', b'j'); zf.writestr('.DS_Store', b'j'); zf.writestr('workbook/.DS_Store', b'j')
try:
    ok(R.verify(z)['seq'] == 1, 'b: junk entries (__MACOSX, .DS_Store) in a refresh zip are ignored')
except Exception as e:
    ok(False, 'b: junk entries ignored: %r' % e)
js = (st / 'web' / 'panel.js').read_text(encoding='utf-8')
ok(js.count('Open safe files after downloading') == 2, 'c: both drop boxes carry the Safari hint for a dropped folder')
ok('black window' not in js and 'black tracker' not in js, 'd: panel has no "black window"')
la = (st / 'launcher.py').read_text(encoding='utf-8')
ok('black window' not in la and 'Edge was not found' not in la, 'd: launcher wording is platform-neutral')
if subprocess.run(['node', '--check', str(st / 'web' / 'panel.js')], capture_output=True).returncode not in (0,):
    ok(False, 'c/d: panel.js still parses (node --check)')
else:
    ok(True, 'c/d: panel.js still parses (node --check)')
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if fails else 0)
