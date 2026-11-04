"""setup_mac.py: "Set up from the Mac library" (SWITCHOVER-v1 plan; keeper copy, switch-over day).

The keeper copy ships with an empty data folder. Sammy copies the Mac's "Tracker library" folder to the PC (downloaded fully, outside any
cloud-synced folder) together with the fingerprint list the Mac made, and this step brings it into the tracker:

    check(lay, folder, listfile)            read only: every listed file must be there with the same sha256; reports plainly
    run(lay, folder, listfile, init_fn, repairs=False)
                                            copies (never moves, never changes the source) the workbook to data/workbook/ and the library
                                            folders to data/library/, each copy checked by sha256; nothing is written into data/workbook or
                                            data/library unless every file checked out. The caller then seeds the ledger, builds the page.

The fingerprint list is `shasum -a 256` format, as data/library_manifest.sha256: "<sha256>  <path>", one line per file, paths relative to the
"Tracker library" folder, the workbook as the line "<sha256>  AJG Coverage - NewsBank.xlsx". Year folders, _original_html/, _original_pdf/
and Press releases/ are copied; Backups/, Work archive/ and any other folder are not. Files in those four folders that the list does not name
are reported and ignored (the list file itself and OS junk are not reported). Cloud placeholders (empty or unreadable files, Windows
"online only" files) are refused with a message to download them fully.
Standard library only. Everything is written inside the tracker folder (GOVIT-v1).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import unicodedata
from pathlib import Path

import common as C

WB_NAME = C.WORKBOOK_NAME
LIB_TOPS = ('_original_html', '_original_pdf', 'Press releases')
JUNK_NAMES = {'.ds_store', 'thumbs.db', 'desktop.ini', 'icon\r'}
EMPTY_SHA = hashlib.sha256(b'').hexdigest()
LINE = re.compile(r'^([0-9a-fA-F]{64}) [ *](.+)$')
SHOW = 20
# Windows: file is a cloud placeholder (OneDrive "files on demand"): offline, recall on open, recall on data access, pinned-off
WIN_PLACEHOLDER = 0x1000 | 0x40000 | 0x400000


class SetupRefused(Exception):
    def __init__(self, code, msg, detail=None):
        super().__init__(msg)
        self.code, self.msg, self.detail = code, msg, detail or {}


def _nfc(s: str) -> str:
    return unicodedata.normalize('NFC', s)


def in_scope(rel: str) -> bool:
    """a path (relative to the Tracker library folder, '/' separated) the setup copies"""
    parts = rel.split('/')
    if rel == WB_NAME:
        return True
    if len(parts) < 2:
        return False
    return bool(re.fullmatch(r'\d{4}', parts[0])) or parts[0] in LIB_TOPS


def is_junk(name: str) -> bool:
    return name.lower() in JUNK_NAMES or name.startswith('._') or name.lower().startswith('~$')


# ---------------------------------------------------------------- the list

def find_list(folder: Path, given: str | None) -> Path:
    if given and given.strip():
        p = Path(given.strip().strip('"'))
        if not p.is_file():
            raise SetupRefused('NO_LIST', f'The fingerprint list is not at {p}. Check the path, or leave it empty to use the one inside the library folder.')
        return p
    cands = sorted(f for f in folder.glob('*.sha256') if f.is_file())
    pref = [f for f in cands if 'manifest' in f.name.lower()]
    pick = pref or cands
    if len(pick) != 1:
        raise SetupRefused('NO_LIST', 'No fingerprint list was given' + (' and the library folder holds more than one .sha256 file.' if pick else ' and the library folder holds none.')
                           + ' Choose the list the Mac made ("Tracker library manifest.sha256").')
    return pick[0]


def read_list(p: Path) -> dict:
    """{normalized relative path (NFC, '/'): (sha256 lower, original text of the path)} for every well-formed line"""
    try:
        txt = p.read_bytes().decode('utf-8-sig')
    except (OSError, UnicodeDecodeError) as e:
        raise SetupRefused('BAD_LIST', f'The fingerprint list could not be read: {e}'[:200])
    out, bad = {}, 0
    for ln in txt.splitlines():
        if not ln.strip():
            continue
        m = LINE.match(ln.rstrip('\r'))
        if not m:
            bad += 1
            continue
        rel = m.group(2).strip().replace('\\', '/')
        while rel.startswith('./'):
            rel = rel[2:]
        out[_nfc(rel)] = (m.group(1).lower(), rel)
    if not out:
        raise SetupRefused('BAD_LIST', 'The fingerprint list has no usable lines. It must be in shasum -a 256 format: "<sha256>  <path>" on each line.')
    if bad:
        out['\0bad'] = (str(bad), '')
    return out


# ---------------------------------------------------------------- the folder

def is_placeholder(p: Path, st=None) -> bool:
    st = st or p.stat()
    attrs = getattr(st, 'st_file_attributes', 0) or 0
    return bool(attrs & WIN_PLACEHOLDER)


def scan(folder: Path) -> dict:
    """{normalized relative path: Path} of every file in the workbook slot and the four library folders (junk left out)"""
    out = {}
    wbp = folder / WB_NAME
    for f in folder.iterdir():
        if f.is_file() and _nfc(f.name) == _nfc(WB_NAME):
            out[_nfc(WB_NAME)] = f
    for top in folder.iterdir():
        if not top.is_dir():
            continue
        nm = _nfc(top.name)
        if not (re.fullmatch(r'\d{4}', nm) or nm in LIB_TOPS):
            continue
        for dp, dn, fn in os.walk(top):
            dn[:] = [d for d in dn if not is_junk(d)]
            for f in fn:
                if is_junk(f):
                    continue
                p = Path(dp) / f
                out[_nfc(p.relative_to(folder).as_posix())] = p
    return out


def sha_of(p: Path, sink=None) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
            if sink:
                sink(b)
    return h.hexdigest()


def check(lay, folder, listfile=None, hash_files=True, progress=None) -> dict:
    """read only. Returns the report; raises SetupRefused for a list/folder that cannot be used. `ok` is true only when nothing is missing,
    different or a placeholder (extra files do not matter)."""
    folder = Path(str(folder).strip().strip('"'))
    if not folder.is_dir():
        raise SetupRefused('NO_FOLDER', f'The library folder is not at {folder}. Check the path (it should be the copied "Tracker library" folder).')
    lst = find_list(folder, listfile)
    want = read_list(lst)
    bad_lines = int(want.pop('\0bad', ('0', ''))[0])
    if _nfc(WB_NAME) not in want:
        raise SetupRefused('NO_WB_LINE', 'The fingerprint list has no line for the workbook. The Mac list must include "<sha256>  AJG Coverage - NewsBank.xlsx".')
    out_of_scope = sorted(r for r in want if not in_scope(r))
    want = {r: v for r, v in want.items() if in_scope(r)}
    have = scan(folder)
    list_norm = _nfc(lst.name)
    import refresh as R
    missing, different, placeholders, extra, unsupported, ok_n = [], [], [], [], [], 0
    for rel, (sha, orig) in sorted(want.items()):
        if rel != _nfc(WB_NAME):
            try:           # a file a refresh file could not carry would break every later refresh: say so now
                R.check_name('library/' + rel)
            except R.RefreshRefused:
                unsupported.append(orig)
        p = have.get(rel)
        if p is None:
            missing.append(orig)
            continue
        try:
            st = p.stat()
            if is_placeholder(p, st) or (st.st_size == 0 and sha != EMPTY_SHA):
                placeholders.append(orig)
                continue
            if hash_files:
                got = sha_of(p)
                if got != sha:
                    different.append(orig)
                    continue
        except OSError:
            placeholders.append(orig)
            continue
        ok_n += 1
        if progress and ok_n % 500 == 0:
            progress(ok_n)
    for rel, p in sorted(have.items()):
        if rel not in want and _nfc(p.name) != list_norm:
            extra.append(rel)
    rep = {'folder': str(folder), 'list': str(lst), 'listed': len(want), 'ok_files': ok_n, 'missing': len(missing), 'missing_names': missing[:SHOW],
           'different': len(different), 'different_names': different[:SHOW], 'placeholders': len(placeholders), 'placeholders_names': placeholders[:SHOW],
           'unsupported': len(unsupported), 'unsupported_names': unsupported[:SHOW], 'extra': len(extra), 'extra_names': extra[:SHOW], 'list_lines_ignored': len(out_of_scope), 'list_lines_unreadable': bad_lines,
           'workbook_sha256': want[_nfc(WB_NAME)][0], 'hashed': hash_files}
    rep['ok'] = not (missing or different or placeholders or unsupported)
    rep['lines'] = lines_of(rep)
    rep['_want'] = {r: v[0] for r, v in want.items()}
    rep['_have'] = {r: str(have[r]) for r in want if r in have}
    return rep


def lines_of(rep) -> list:
    def names(k, n):
        return ('; first %d: ' % min(SHOW, n) + ', '.join(rep[k + '_names'])) if n else ''
    L = [f'The list names {rep["listed"]} files (the workbook, the year folders, _original_html, _original_pdf and Press releases).']
    L.append(f'{rep["ok_files"]} of them are here with the right fingerprint.')
    if rep['missing']:
        L.append(f'{rep["missing"]} files are MISSING{names("missing", rep["missing"])}.')
    if rep['different']:
        L.append(f'{rep["different"]} files are DIFFERENT from the list (changed or damaged in the copy){names("different", rep["different"])}.')
    if rep['placeholders']:
        L.append(f'{rep["placeholders"]} files are empty or only online (a cloud folder has not downloaded them){names("placeholders", rep["placeholders"])}. '
                 'Make the whole folder "Always keep on this device" (or copy it again with everything downloaded), then check again.')
    if rep['unsupported']:
        L.append(f'{rep["unsupported"]} listed files have a name or type this tracker cannot pass on in refresh files (only .html, .pdf, .txt and similar in plain names are allowed){names("unsupported", rep["unsupported"])}. '
                 'Take them out of the copy (and the list) or tell Claude; nothing was copied.')
    if rep['extra']:
        L.append(f'{rep["extra"]} files in the folder are not on the list; they are ignored and not copied{names("extra", rep["extra"])}.')
    if rep['list_lines_ignored']:
        L.append(f'{rep["list_lines_ignored"]} lines of the list name files outside what is copied (for example Backups); they are ignored.')
    if rep['list_lines_unreadable']:
        L.append(f'{rep["list_lines_unreadable"]} lines of the list could not be read and were skipped.')
    return L


def public(rep: dict) -> dict:
    return {k: v for k, v in rep.items() if not k.startswith('_')}


# ---------------------------------------------------------------- copy

def _library_conflicts(lay, rep) -> list:
    """Repairs path: library files already in data/library with a different content than the list says"""
    out = []
    for rel, sha in rep['_want'].items():
        if rel == _nfc(WB_NAME):
            continue
        dst = lay.library / Path(*rel.split('/'))
        if dst.is_file() and C.sha256_file(dst) != sha:
            out.append(rel)
    return out


def run(lay, folder, listfile=None, repairs=False, progress=None) -> dict:
    """Checks (stat + fingerprint), then copies into a staging folder inside data/tmp with the fingerprint checked again on the copy, then puts the
    files in place. Any refusal leaves data/workbook and data/library exactly as they were (the staging folder is this step's own temporary folder)."""
    wb_dst = lay.workbook
    have_wb = wb_dst.is_file()
    if have_wb and not repairs:
        raise SetupRefused('HAS_WORKBOOK', 'This tracker already has a workbook, so the setup is not run. (To replace it on purpose, use Repairs, "Set up again from the Mac library".)')
    rep = check(lay, folder, listfile, hash_files=True, progress=progress)
    if not rep['ok']:
        raise SetupRefused('CHECK_FAILED', 'The copied folder does not match the fingerprint list. ' + ' '.join(l for l in rep['lines'][1:] if 'MISSING' in l or 'DIFFERENT' in l or 'empty or only online' in l or 'cannot pass on' in l)
                           + ' Nothing was copied.', public(rep))
    if have_wb:
        if C.excel_open(wb_dst):
            raise SetupRefused('EXCEL_OPEN', 'Excel has the workbook open. Close it first. Nothing was changed.')
        conf = _library_conflicts(lay, rep)
        if conf:
            raise SetupRefused('LIB_CONFLICT', f'{len(conf)} files already in this tracker\'s library differ from the list (first: {", ".join(conf[:5])}). Nothing was changed.', public(rep))
    stamp = C.stamp()
    stage = lay.data / 'tmp' / f'setup_{stamp}'
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    copied, skipped, n = [], 0, 0
    try:
        for rel, src in sorted(rep['_have'].items()):
            sha = rep['_want'][rel]
            is_wb = rel == _nfc(WB_NAME)
            dst = lay.library / Path(*rel.split('/'))
            if not is_wb and dst.is_file() and C.sha256_file(dst) == sha:
                skipped += 1
                continue
            tmp = stage / ('workbook' if is_wb else Path(*rel.split('/')).as_posix())
            tmp.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp, 'wb') as f:
                got = sha_of(Path(src), f.write)
                f.flush()
                os.fsync(f.fileno())
            if got != sha:
                raise SetupRefused('SOURCE_CHANGED', f'{rel} changed while it was being copied. Nothing was changed.')
            if C.sha256_file(tmp) != sha:
                raise SetupRefused('COPY_BAD', f'The copy of {rel} did not check out (disk problem?). Nothing was changed.')
            copied.append((rel, tmp, dst, is_wb))
            n += 1
            if progress and n % 200 == 0:
                progress(n)
        # everything is staged and verified: put it in place
        bk = None
        if have_wb:
            lay.backups.mkdir(parents=True, exist_ok=True)
            bk = lay.backups / f'{wb_dst.stem} BACKUP before setup {stamp}.xlsx'
            shutil.copy2(wb_dst, bk)
            if C.sha256_file(bk) != C.sha256_file(wb_dst):
                raise SetupRefused('BACKUP_FAILED', 'The backup of the current workbook could not be made. Nothing was changed.')
        for rel, tmp, dst, is_wb in copied:
            if is_wb:
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            C.replace_file(tmp, dst)
        for rel, tmp, dst, is_wb in copied:
            if is_wb:
                wb_dst.parent.mkdir(parents=True, exist_ok=True)
                C.replace_file(tmp, wb_dst)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    sha_wb = rep['_want'][_nfc(WB_NAME)]
    if C.sha256_file(wb_dst) != sha_wb:
        raise SetupRefused('COMMIT_FAILED', 'The workbook in the data folder did not check out after it was put in place. Tell Claude.')
    return {'ok': True, 'workbook_sha256': sha_wb, 'files_copied': sum(1 for c in copied if not c[3]), 'files_skipped_same': skipped, 'backup': bk.name if bk else None,
            'listed': rep['listed'], 'extra': rep['extra'], 'extra_names': rep['extra_names'], 'check_lines': rep['lines']}


def summary(lay) -> dict:
    """what the summary shows after setup: stories, rows, library files, workbook fingerprint; and stories with a saved copy that the page's
    article data does not hold (the article data ships with the tracker; see README)"""
    import openpyxl
    wb = openpyxl.load_workbook(lay.workbook, read_only=True, data_only=True)
    try:
        ws = wb['Coverage']
        it = ws.iter_rows(values_only=True)
        h = [str(x or '').strip() for x in next(it)]
        ix = {k: i for i, k in enumerate(h)}
        sids, rows, copies = set(), 0, set()
        for r in it:
            if not any(r):
                continue
            rows += 1
            if str(r[ix['Original or reprint']] or '').strip().lower() == 'reprint (unverified)':
                continue
            sid = str(r[ix['Story ID']] or '').strip()
            if sid:
                sids.add(sid)
                if str(r[ix['Saved Copy?']] or '').strip().lower() == 'yes':
                    copies.add(sid)
    finally:
        wb.close()
    nfiles = sum(len(f) for _, _, f in os.walk(lay.library)) if lay.library.is_dir() else 0
    shard = set()
    try:
        shard = set((json.loads((lay.copies / 'articles' / 'manifest.json').read_text(encoding='utf-8')).get('articles') or {}))
    except (OSError, ValueError):
        pass
    return {'stories': len(sids), 'coverage_rows': rows, 'library_files': nfiles, 'saved_copy_stories': len(copies),
            'saved_copy_stories_without_page_copy': len(copies - shard) if shard else None, 'workbook_sha256': C.sha256_file(lay.workbook)}
