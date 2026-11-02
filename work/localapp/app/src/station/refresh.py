"""refresh.py: the keeper's "refresh file" and the readers' "Bring in refresh file" (MULTIPC-v2).

One zip, data only. Carries the workbook, the library files added since the previous refresh (or all of them in a FULL refresh), and the
data the page loads (data/site, data/copies/articles). NEVER notes, views, edits or any other db document.

    manifest.json   {format: "ajg-refresh", format_version: 1, created_at, kind: "full"|"incremental", seq, base_seq,
                     workbook_name, workbook_sha256, files: {<zip name>: {sha256, bytes}}}
    workbook/<workbook name>        library/<path under data/library>        site/<path under data/site>        copies/articles/<shard>.json

seq = the keeper's ledger sequence number (the number of lines in data/state/ledger.jsonl). A reader refuses a refresh whose seq is not
higher than the one it applied last, and an incremental one whose base_seq is higher than what it has (a gap: ask for a full refresh).
Reading rules follow updatefolder/formats.py: allow-listed names and extensions, size/count/ratio caps, hashes checked before anything is
written, any failure refuses the whole file. Everything is moved aside or kept, nothing is deleted.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

import common as C

FORMAT = 'ajg-refresh'
VERSION = 1
KINDS = ('workbook', 'library', 'site', 'copies')
MEDIA = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.mp3', '.wav', '.mp4', '.webm'}
EXT = {'workbook': {'.xlsx'}, 'library': {'.html', '.htm', '.pdf', '.json', '.txt', '.csv'} | MEDIA,
       'site': {'.html', '.json'} | MEDIA, 'copies': {'.json'}}
CAP_ENTRIES, CAP_TOTAL, CAP_ENTRY, RATIO = 300_000, 4 * 2**30, 512 * 2**20, 200
BAD_CH = re.compile(r'[\x00-\x1f"<>|?*:\\]')
RESERVED = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)), *(f'lpt{i}' for i in range(1, 10))}
SKIP_LIB = ('_to_delete', '_docs', 'Backups')


class RefreshRefused(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code, self.msg = code, msg


def role(lay) -> str:
    try:
        r = json.loads((lay.data / 'role.json').read_text(encoding='utf-8')).get('role')
    except (OSError, ValueError):
        r = None
    return 'keeper' if r == 'keeper' else 'reader'


def seq_of(lay) -> int:
    return len(C.read_ledger(lay.state))


def _state_file(lay, name):
    return lay.state / name


def _read_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


# ---------------------------------------------------------------- names

def check_name(name: str):
    if name == 'manifest.json':
        return 'manifest', ''
    if len(name) > 240 or name.startswith('/') or BAD_CH.search(name) or '//' in name:
        raise RefreshRefused('BAD_ENTRY', f'a file name in the refresh is not allowed: {name[:60]!r}')
    parts = name.split('/')
    if parts[0] not in KINDS or len(parts) < 2:
        raise RefreshRefused('BAD_ENTRY', f'a file in the refresh is outside what a refresh may carry: {name[:60]!r}')
    for p in parts:
        if not p or p in ('.', '..') or p.endswith(('.', ' ')) or len(p) > 200 or p.split('.')[0].lower() in RESERVED:
            raise RefreshRefused('BAD_ENTRY', f'a file name in the refresh is not allowed: {name[:60]!r}')
    kind, ext = parts[0], os.path.splitext(parts[-1])[1].lower()
    if ext not in EXT[kind]:
        raise RefreshRefused('BAD_ENTRY', f'a {ext or "no-extension"} file is not allowed in a refresh: {name[:60]!r}')
    if kind == 'workbook' and len(parts) != 2:
        raise RefreshRefused('BAD_ENTRY', 'the workbook must sit at the top of the refresh')
    if kind == 'site' and ext == '.html' and parts[1:] != ['index.html']:
        raise RefreshRefused('BAD_ENTRY', f'only the tracker page itself may be an .html file in site: {name[:60]!r}')
    if kind == 'copies' and (len(parts) != 3 or parts[1] != 'articles'):
        raise RefreshRefused('BAD_ENTRY', f'bad article shard name: {name[:60]!r}')
    return kind, '/'.join(parts[1:])


# ---------------------------------------------------------------- make (keeper)

def _sha(p):
    return C.sha256_file(p)


def _tree(root: Path, skip=()):
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root)
        if p.is_file() and not any(x in rel.parts for x in skip) and not any(s.startswith('.') for s in rel.parts) \
                and p.suffix != '.part' and '.part' not in p.name:
            yield rel.as_posix(), p


def make(lay, full=False) -> dict:
    if role(lay) != 'keeper':
        raise RefreshRefused('NOT_KEEPER', 'Only the keeper copy of the tracker makes refresh files.')
    wb = lay.workbook
    if not wb.is_file():
        raise RefreshRefused('NO_WORKBOOK', 'The workbook is not in the data folder.')
    ws = C.workbook_state(lay)
    if ws.get('baseline') != 'ok':
        raise RefreshRefused('BASELINE', 'The workbook is not the one the tracker last saved or accepted. Use "Accept the workbook as it is now" first, '
                             'so the refresh matches the tracker\'s record.')
    if ws.get('excel_open'):
        raise RefreshRefused('EXCEL_OPEN', 'Excel has the workbook open. Close it first.')
    st = _read_json(_state_file(lay, 'refresh_state.json'), {})
    prev_seq, prev_at = (0, '') if full else (int(st.get('last_seq') or 0), st.get('last_at') or '')
    files = {}     # zip name -> source path
    files['workbook/' + wb.name] = wb
    # library: added by saves since the previous refresh (the saver's own save logs), or all of it
    if full:
        for rel, p in _tree(lay.library, SKIP_LIB):
            files['library/' + rel] = p
    else:
        for lg in sorted((lay.state / 'logs').glob('save-*.log')) if (lay.state / 'logs').is_dir() else []:
            d = _read_json(lg, {})
            if str(d.get('at') or '') > prev_at:
                for rel in (d.get('library') or {}).get('pages_added') or []:
                    p = lay.library / Path(*rel.split('/'))
                    if p.is_file():
                        files['library/' + rel] = p
    # what the page loads
    site = lay.data / 'site'
    old_map = {} if full else (st.get('shards') or {})
    new_map = {}
    for rel, p in _tree(site):
        if rel == 'index.html' or rel.startswith('data/') or (full and rel.startswith('img/')):
            files['site/' + rel] = p
    if (lay.copies / 'articles').is_dir():
        for rel, p in _tree(lay.copies / 'articles'):
            if rel.endswith('.json') and '/' not in rel:
                h = _sha(p)
                new_map[rel] = h
                if full or old_map.get(rel) != h:
                    files['copies/articles/' + rel] = p
    for n in files:
        check_name(n)
    sha_wb = _sha(wb)
    seq = seq_of(lay)
    created = C.utc_now().strftime('%Y-%m-%dT%H:%M:%SZ')
    manifest_files = {n: {'sha256': _sha(p), 'bytes': p.stat().st_size} for n, p in files.items()}
    if manifest_files['workbook/' + wb.name]['sha256'] != sha_wb or _sha(wb) != sha_wb:
        raise RefreshRefused('CHANGED', 'The workbook changed while the refresh file was being made. Try again.')
    manifest = {'format': FORMAT, 'format_version': VERSION, 'created_at': created, 'kind': 'full' if full else 'incremental', 'seq': seq,
                'base_seq': prev_seq, 'workbook_name': wb.name, 'workbook_sha256': sha_wb, 'files': manifest_files}
    out = lay.data / 'refresh_out'
    out.mkdir(parents=True, exist_ok=True)
    name = f'refresh_{"full" if full else "incr"}_{seq:04d}_{created.replace(":", "").replace("-", "")}_{sha_wb[:8]}.zip'
    dest = out / name
    part = dest.with_name(name + '.part')
    with zipfile.ZipFile(part, 'w', allowZip64=True) as z:
        z.writestr('manifest.json', json.dumps(manifest, indent=1), compress_type=zipfile.ZIP_DEFLATED)
        for n, p in files.items():
            ct = zipfile.ZIP_STORED if os.path.splitext(n)[1].lower() in MEDIA | {'.pdf'} else zipfile.ZIP_DEFLATED
            z.write(p, n, compress_type=ct)
    os.replace(part, dest)
    C.atomic_write(_state_file(lay, 'refresh_state.json'), json.dumps({'last_seq': seq, 'last_at': created, 'shards': new_map or st.get('shards') or {},
                                                                    'last_file': name}, indent=1).encode())
    return {'name': name, 'path': str(dest), 'bytes': dest.stat().st_size, 'kind': manifest['kind'], 'seq': seq, 'files': len(files),
            'library_files': sum(1 for n in files if n.startswith('library/')), 'workbook_sha256': sha_wb}


# ---------------------------------------------------------------- verify (reader)

def _read_checked(z: zipfile.ZipFile, info: zipfile.ZipInfo, sink=None):
    """stream an entry: returns (sha256, bytes); the bytes actually read must equal the header size; sink(chunk) gets the data"""
    h, n = hashlib.sha256(), 0
    with z.open(info) as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            n += len(b)
            if n > info.file_size or n > CAP_ENTRY:
                raise RefreshRefused('TOO_BIG', f'{info.filename[:60]} is larger than its header says')
            h.update(b)
            if sink:
                sink(b)
    if n != info.file_size:
        raise RefreshRefused('BAD_ZIP', f'{info.filename[:60]} is shorter than its header says')
    return h.hexdigest(), n


def verify(zip_path) -> dict:
    zp = Path(zip_path)
    try:
        z = zipfile.ZipFile(zp)
    except (zipfile.BadZipFile, OSError) as e:
        raise RefreshRefused('BAD_ZIP', f'not a readable zip file: {e}')
    with z:
        infos = [i for i in z.infolist() if not i.filename.endswith('/')]
        if len(infos) > CAP_ENTRIES:
            raise RefreshRefused('TOO_MANY_FILES', 'the refresh holds more files than a refresh may have')
        seen, total = set(), 0
        for i in infos:
            check_name(i.filename)
            low = i.filename.lower()
            if low in seen:
                raise RefreshRefused('BAD_ENTRY', f'the same file name appears twice: {i.filename[:60]!r}')
            seen.add(low)
            if i.flag_bits & 1:
                raise RefreshRefused('BAD_ENTRY', 'the zip is encrypted')
            if (i.external_attr >> 28) == 0xA:
                raise RefreshRefused('BAD_ENTRY', f'a link inside the zip is not allowed: {i.filename[:60]!r}')
            if i.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise RefreshRefused('BAD_ENTRY', 'the zip uses a compression this tracker does not read')
            if i.file_size > CAP_ENTRY:
                raise RefreshRefused('TOO_BIG', f'{i.filename[:60]} is bigger than a refresh file may be')
            if i.file_size > 256 * 1024 and i.compress_size and i.file_size / i.compress_size > RATIO:
                raise RefreshRefused('ZIP_BOMB', f'{i.filename[:60]} expands far more than it should')
            total += i.file_size
        if total > CAP_TOTAL:
            raise RefreshRefused('TOO_BIG', 'the refresh would expand to more than a refresh may')
        by = {i.filename: i for i in infos}
        if 'manifest.json' not in by:
            raise RefreshRefused('BAD_MANIFEST', 'manifest.json is missing')
        if by['manifest.json'].file_size > 64 * 1024 * 1024:
            raise RefreshRefused('TOO_BIG', 'manifest.json is too big')
        try:
            man = json.loads(z.read(by['manifest.json']).decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            raise RefreshRefused('BAD_MANIFEST', 'manifest.json is not valid JSON')
        if not isinstance(man, dict) or man.get('format') != FORMAT:
            raise RefreshRefused('BAD_MANIFEST', 'this is not a tracker refresh file')
        if not isinstance(man.get('format_version'), int) or man['format_version'] > VERSION:
            raise RefreshRefused('NEWER_FORMAT', 'this refresh file was made by a newer version of the tracker')
        if not isinstance(man.get('seq'), int) or not isinstance(man.get('base_seq'), int) or man.get('kind') not in ('full', 'incremental'):
            raise RefreshRefused('BAD_MANIFEST', 'the manifest lacks its sequence number or kind')
        if not re.fullmatch(r'[0-9a-f]{64}', str(man.get('workbook_sha256'))):
            raise RefreshRefused('BAD_MANIFEST', 'the manifest lacks the workbook fingerprint')
        files = man.get('files')
        if not isinstance(files, dict) or set(files) != set(by) - {'manifest.json'}:
            raise RefreshRefused('BAD_MANIFEST', 'the manifest does not list exactly the files in the zip')
        wbs = [n for n in files if n.startswith('workbook/')]
        if len(wbs) != 1 or files[wbs[0]].get('sha256') != man['workbook_sha256']:
            raise RefreshRefused('BAD_MANIFEST', 'the refresh must carry exactly one workbook, matching the fingerprint')
        for n, meta in files.items():
            sha, nbytes = _read_checked(z, by[n])
            if sha != meta.get('sha256') or nbytes != meta.get('bytes'):
                raise RefreshRefused('HASH_MISMATCH', f'{n[:60]} does not match its checksum: the file was changed or damaged after it was made')
    return man


# ---------------------------------------------------------------- take (reader)

def take(lay, zip_path, init_fn) -> dict:
    """verify, then apply. init_fn(note) re-seeds the saver ledger with the new workbook (returns the exit code)."""
    if role(lay) == 'keeper':
        raise RefreshRefused('IS_KEEPER', 'This is the keeper copy. It makes refresh files; it does not take them in.')
    man = verify(zip_path)
    applied = _read_json(_state_file(lay, 'refresh_applied.json'), {})
    have = int(applied.get('seq') or 0)
    if man['seq'] <= have:
        raise RefreshRefused('OLDER', f'This copy already has refresh {have}; this file is refresh {man["seq"]}. A refresh that is not newer is refused.')
    if man['kind'] == 'incremental' and man['base_seq'] > have:
        raise RefreshRefused('GAP', f'This refresh only carries changes since refresh {man["base_seq"]}, but this copy is at refresh {have}. '
                             'Ask the keeper for a full refresh.')
    wb = lay.workbook
    if wb.is_file() and C.excel_open(wb):
        raise RefreshRefused('EXCEL_OPEN', 'Excel has the workbook open. Close it, then try again.')
    wb_name = [n for n in man['files'] if n.startswith('workbook/')][0]
    stamp = C.stamp()
    res = {'seq': man['seq'], 'kind': man['kind'], 'library_added': 0, 'library_skipped': 0, 'site_files': 0, 'backup': None}
    with zipfile.ZipFile(zip_path) as z:
        by = {i.filename: i for i in z.infolist()}
        # 1. backup (rule 7), then the workbook: unique staged file, verified, swapped in atomically
        wb.parent.mkdir(parents=True, exist_ok=True)
        if wb.is_file():
            lay.backups.mkdir(parents=True, exist_ok=True)
            bk = lay.backups / f'{wb.stem} BACKUP before refresh {man["seq"]} {stamp}.xlsx'
            n = 2
            while bk.exists():
                bk = bk.with_name(f'{bk.stem} ({n}){bk.suffix}')
                n += 1
            shutil.copy2(wb, bk)
            if C.sha256_file(bk) != C.sha256_file(wb):
                raise RefreshRefused('BACKUP_FAILED', 'The backup of the current workbook could not be made, so nothing was changed.')
            res['backup'] = bk.name
        staged = wb.with_name(f'{wb.stem} REFRESH {stamp}.xlsx.part')
        _extract(z, by[wb_name], staged, man['files'][wb_name]['sha256'])
        if C.excel_open(wb):
            staged.unlink()
            raise RefreshRefused('EXCEL_OPEN', 'Excel opened the workbook meanwhile. Nothing was changed.')
        os.replace(staged, wb)
        if C.sha256_file(wb) != man['workbook_sha256']:
            raise RefreshRefused('COMMIT_FAILED', 'The new workbook did not check out after it was written. Tell Claude; do not save.')
        # 2. library (add-only), site and shards (replaced; the old file is kept aside)
        keep_site, keep_copies = lay.data / 'site_replaced' / stamp, lay.copies / '_replaced' / stamp
        for n, meta in man['files'].items():
            kind, rel = check_name(n)
            if kind == 'workbook':
                continue
            if kind == 'library':
                dst = lay.library / Path(*rel.split('/'))
                if dst.exists():
                    res['library_skipped'] += 1
                    continue
                _extract(z, by[n], dst, meta['sha256'])
                res['library_added'] += 1
            else:
                dst = (lay.data / 'site' / Path(*rel.split('/'))) if kind == 'site' else (lay.copies / Path(*rel.split('/')))
                C.keep_old(dst, keep_site if kind == 'site' else keep_copies)
                _extract(z, by[n], dst, meta['sha256'])
                res['site_files'] += 1
    # 3. the saver's ledger starts from the new workbook (SAVE_RULES answer 2); notes and views are not touched
    code = init_fn(f'refresh {man["seq"]} ({man["kind"]}) from the keeper, made {man["created_at"]}')
    if code != 0:
        raise RefreshRefused('LEDGER', 'The workbook was replaced, but the tracker could not record it as its starting point. Use "Accept the workbook as it is now".')
    C.atomic_write(_state_file(lay, 'refresh_applied.json'), json.dumps({'seq': man['seq'], 'kind': man['kind'], 'created_at': man['created_at'],
                                                                     'applied_at': C.utc_now().isoformat(timespec='seconds'),
                                                                     'workbook_sha256': man['workbook_sha256']}, indent=1).encode())
    res['workbook_sha256'] = man['workbook_sha256']
    return res


def _extract(z, info, dst: Path, want_sha: str):
    dst.parent.mkdir(parents=True, exist_ok=True)
    part = dst.with_name(dst.name + ('' if dst.name.endswith('.part') else '.part'))
    try:
        with open(part, 'wb') as f:
            sha, _ = _read_checked(z, info, f.write)
            f.flush()
            os.fsync(f.fileno())
        if sha != want_sha:
            raise RefreshRefused('HASH_MISMATCH', f'{info.filename[:60]} changed while it was being read')
        if part != dst:
            os.replace(part, dst)
    except BaseException:
        try:
            if part.exists() and part != dst:
                part.unlink()
        except OSError:
            pass
        raise
