"""Shared rules for the two files that travel between the PC tracker and the Update station (see FORMAT.md).

Data only (GOVIT-v1): nothing here runs code from a zip, opens saved HTML, or touches the network. Python 3.11+, standard library only.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

FORMAT_FOR_UPDATE = 'ajg-for-update'
FORMAT_UPDATE = 'ajg-update-folder'
FORMAT_VERSION = 1

# collections the PC save reads (sheet_task.load_db); anything else is refused
COLLECTIONS = ('runs', 'pages', 'reprints', 'authors', 'translations', 'tones', 'edits')
ID_PART = r'[A-Za-z0-9][A-Za-z0-9._-]{0,119}'
ENTRY_RE = re.compile(r'^db/(' + '|'.join(COLLECTIONS) + r')/(' + ID_PART + r')\.json$')
# NEWSBANKPDF-v1 / PROQUESTPDF-v1: a NewsBank story's own PDF (or a ProQuest article's) travels as files/<id>.pdf (binary), named by the pages doc that carries it (pages/<doc>.json nb.file / pq.file)
PDF_ENTRY_RE = re.compile(r'^files/(' + ID_PART + r')\.pdf$')
WINDOWS_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}

# zip-bomb and size caps (GOVIT-v1)
MAX_FILES = 20000
MAX_TOTAL_BYTES = 512 * 1024 * 1024        # all entries together, uncompressed
MAX_FILE_BYTES = 64 * 1024 * 1024          # one entry, uncompressed
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_PDF_BYTES = 32 * 1024 * 1024           # one story PDF (NEWSBANKPDF-v1)
MAX_ZIP_BYTES = 256 * 1024 * 1024          # the zip file itself
MAX_RATIO = 200                            # uncompressed / compressed, checked on entries over RATIO_FROM bytes
RATIO_FROM = 256 * 1024


class UpdateRefused(Exception):
    """The update zip is refused. `code` is stable text for callers and tests."""

    def __init__(self, code: str, msg: str, detail=None):
        super().__init__(msg)
        self.code, self.msg, self.detail = code, msg, detail or {}


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def dumps_compact(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def dumps_pretty(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=1) + '\n').encode('utf-8')


def is_pdf_entry(name: str) -> bool:
    return bool(PDF_ENTRY_RE.match(name or ''))


def entry_cap(name: str) -> int:
    return MAX_MANIFEST_BYTES if name == 'manifest.json' else MAX_PDF_BYTES if is_pdf_entry(name) else MAX_FILE_BYTES


# ---- story PDFs: data only. A PDF can carry JavaScript, launch actions, embedded files and form code; none of that is allowed (GOVIT-v1) ----
DANGEROUS_NAMES = ('JS', 'JavaScript', 'Launch', 'EmbeddedFile', 'EmbeddedFiles', 'OpenAction', 'AA', 'RichMedia', 'XFA', 'SubmitForm', 'ImportData',
                   'GoToR', 'GoToE', 'Encrypt', 'Rendition', 'Movie', 'Sound', 'FileAttachment')
_NAME_END = rb'(?![^\s/<>\[\]()%{}])'
_DANGER_RX = re.compile(rb'/(' + b'|'.join(n.encode() for n in DANGEROUS_NAMES) + rb')' + _NAME_END)
_NAME_RX = re.compile(rb'/[^\s/<>\[\]()%{}]*')
_STREAM_RX = re.compile(rb'(?<![A-Za-z])stream\r?\n.*?\r?\nendstream', re.S)


def _unhex_names(b: bytes) -> bytes:
    """/J#53 is /JS: names may hide characters as #xx"""
    return _NAME_RX.sub(lambda m: re.sub(rb'#([0-9A-Fa-f]{2})', lambda h: bytes([int(h.group(1), 16)]), m.group(0)), b)


def pdf_problems(b: bytes) -> list[str]:
    """Why this PDF must not be taken in ([] = fine). Two independent looks: (1) the file's own text outside stream data, with names un-escaped,
    and the decoded object streams; (2) when pypdf is present (it is on the PC), every object of the file, searched for the same names. A file
    pypdf cannot read is refused too."""
    out = []
    if not b.startswith(b'%PDF-') and b'%PDF-' not in b[:1024]:
        return ['not a PDF (no %PDF- header)']
    if b'%%EOF' not in b[-2048:]:
        out.append('no %%EOF at the end (cut off)')
    lex = _unhex_names(_STREAM_RX.sub(b'', b))
    for m in sorted({x.group(1).decode() for x in _DANGER_RX.finditer(lex)}):
        out.append('/' + m)
    # object streams hold dictionaries too: decode them
    import zlib
    for m in re.finditer(rb'<<([^>]|>(?!>))*?/ObjStm.*?>>\s*stream\r?\n', _unhex_names(b), re.S):
        start = m.end(); end = b.find(b'endstream', start)
        if end < 0: continue
        data = b[start:end].rstrip(b'\r\n')
        try:
            d = zlib.decompressobj().decompress(data, 64 * 1024 * 1024)
        except zlib.error:
            out.append('an object stream that cannot be read'); continue
        for x in sorted({y.group(1).decode() for y in _DANGER_RX.finditer(_unhex_names(d))}):
            out.append('/' + x + ' (in an object stream)')
    try:
        import io, pypdf
    except ImportError:
        pypdf = None
    if pypdf is not None:
        try:
            r = pypdf.PdfReader(io.BytesIO(b), strict=False)
            if r.is_encrypted:
                out.append('/Encrypt')
            else:
                seen, budget = set(), [200000]

                def walk(o, depth=0):
                    if depth > 40 or budget[0] <= 0: return
                    budget[0] -= 1
                    try: o = o.get_object()
                    except Exception: return
                    if id(o) in seen: return
                    seen.add(id(o))
                    if isinstance(o, dict):
                        for k, v in o.items():
                            ks = str(k).lstrip('/')
                            if ks in DANGEROUS_NAMES: out.append('/' + ks + ' (object walk)')
                            walk(v, depth + 1)
                    elif isinstance(o, (list, tuple)):
                        for v in o: walk(v, depth + 1)
                seen_nums = set()
                for gen, nums in list(r.xref.items()):
                    for num in list(nums):
                        if (num, gen) in seen_nums: continue
                        seen_nums.add((num, gen))
                        walk(pypdf.generic.IndirectObject(num, gen, r))
                for num in list(getattr(r, 'xref_objStm', {}) or {}):
                    walk(pypdf.generic.IndirectObject(num, 0, r))
                walk(r.trailer)
        except Exception as e:
            out.append('the PDF cannot be read (' + type(e).__name__ + ')')
    return sorted(set(out))


def entry_ok(name: str) -> tuple[bool, str]:
    """Is this zip entry name on the allow-list? Only manifest.json and db/<collection>/<id>.json."""
    if name == 'manifest.json':
        return True, ''
    if not name or name != name.strip() or '\\' in name or '\x00' in name or any(ord(c) < 32 for c in name):
        return False, 'odd characters in the name'
    if name.startswith('/') or re.match(r'^[A-Za-z]:', name) or name.startswith('//'):
        return False, 'absolute path'
    parts = PurePosixPath(name).parts
    if any(p in ('..', '.', '') for p in parts):
        return False, "'..' in the path"
    m = ENTRY_RE.match(name) or PDF_ENTRY_RE.match(name)
    if not m:
        return False, 'not an allowed file (only manifest.json, db/<collection>/<id>.json and files/<id>.pdf)'
    if m.groups()[-1].split('.')[0].upper() in WINDOWS_RESERVED:
        return False, 'reserved Windows file name'
    return True, ''


def pack_update_zip(out_zip, db_dir, source_workbook_sha256: str, *, created_at=None, extra_manifest=None) -> Path:
    """Reference writer of the update folder (the Update station does the same in the browser). `db_dir` holds <collection>/<id>.json.
    Returns the zip path. Never overwrites."""
    out_zip = Path(out_zip)
    if out_zip.exists():
        raise FileExistsError(str(out_zip))
    db_dir = Path(db_dir)
    files, blobs = {}, {}
    for coll in COLLECTIONS:
        d = db_dir / coll
        for f in sorted(d.glob('*.json')) if d.is_dir() else []:
            name = f'db/{coll}/{f.name}'
            ok, why = entry_ok(name)
            if not ok:
                raise ValueError(f'{name}: {why}')
            b = f.read_bytes()
            json.loads(b.decode('utf-8'))       # must be JSON
            blobs[name] = b
            files[name] = {'sha256': sha256_bytes(b), 'bytes': len(b)}
    fdir = db_dir / 'files'
    for f in sorted(fdir.glob('*.pdf')) if fdir.is_dir() else []:     # NEWSBANKPDF-v1
        name = f'files/{f.name}'
        ok, why = entry_ok(name)
        if not ok:
            raise ValueError(f'{name}: {why}')
        b = f.read_bytes()
        blobs[name] = b
        files[name] = {'sha256': sha256_bytes(b), 'bytes': len(b), 'kind': 'pdf'}
    runs = sorted(Path(n).stem for n in blobs if n.startswith('db/runs/'))
    manifest = {'format': FORMAT_UPDATE, 'format_version': FORMAT_VERSION, 'created_at': created_at or utc_now_iso(),
                'source': {'workbook_sha256': source_workbook_sha256}, 'runs': runs, 'files': files}
    manifest.update(extra_manifest or {})
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', dumps_pretty(manifest))
        for name, b in blobs.items():
            z.writestr(name, b)
    return out_zip


def scan_zip(z: zipfile.ZipFile, zip_size: int) -> list:
    """Pre-scan the central directory: names, flags, sizes. Raises UpdateRefused. Reads no entry data."""
    if zip_size > MAX_ZIP_BYTES:
        raise UpdateRefused('TOO_BIG', f'the zip is {zip_size // 2**20} MB; the limit is {MAX_ZIP_BYTES // 2**20} MB')
    infos = z.infolist()
    if len(infos) > MAX_FILES:
        raise UpdateRefused('TOO_MANY_FILES', f'{len(infos)} entries; the limit is {MAX_FILES}')
    seen, total, out = set(), 0, []
    for i in infos:
        name = i.filename
        if name.endswith('/'):
            if i.file_size:
                raise UpdateRefused('BAD_ENTRY', f'{name!r}: a folder entry with content')
            continue                       # plain folder entries are ignored (nothing is created from them)
        ok, why = entry_ok(name)
        if not ok:
            raise UpdateRefused('BAD_ENTRY', f'{name!r} is not allowed: {why}', {'entry': name})
        if name.lower() in seen:
            raise UpdateRefused('BAD_ENTRY', f'{name!r} appears twice', {'entry': name})
        seen.add(name.lower())
        if i.flag_bits & 0x1:
            raise UpdateRefused('BAD_ENTRY', f'{name!r} is encrypted', {'entry': name})
        mode = (i.external_attr >> 16) & 0xFFFF
        ftype = stat.S_IFMT(mode)           # zip writers often leave the type bits 0; only an explicit non-file type is refused
        if ftype == stat.S_IFLNK:
            raise UpdateRefused('BAD_ENTRY', f'{name!r} is a link', {'entry': name})
        if ftype and ftype != stat.S_IFREG:
            raise UpdateRefused('BAD_ENTRY', f'{name!r} is not a plain file', {'entry': name})
        if i.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise UpdateRefused('BAD_ENTRY', f'{name!r}: unsupported compression', {'entry': name})
        cap = entry_cap(name)
        if i.file_size > cap:
            raise UpdateRefused('TOO_BIG', f'{name!r} is {i.file_size // 2**20} MB uncompressed; the limit is {cap // 2**20} MB', {'entry': name})
        if i.file_size > RATIO_FROM and i.compress_size and i.file_size / i.compress_size > MAX_RATIO:
            raise UpdateRefused('ZIP_BOMB', f'{name!r} expands {i.file_size // i.compress_size}x; the limit is {MAX_RATIO}x', {'entry': name})
        total += i.file_size
        if total > MAX_TOTAL_BYTES:
            raise UpdateRefused('TOO_BIG', f'the entries add up to more than {MAX_TOTAL_BYTES // 2**20} MB uncompressed')
        out.append(i)
    if 'manifest.json' not in {i.filename for i in out}:
        raise UpdateRefused('BAD_MANIFEST', 'manifest.json is missing')
    return out


def read_entry(z: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    """Read one entry with a hard cap; the bytes read must equal the declared size (a lying header is a bomb)."""
    cap = entry_cap(info.filename)
    with z.open(info) as f:
        b = f.read(cap + 1)
    if len(b) > cap or len(b) != info.file_size:
        raise UpdateRefused('ZIP_BOMB', f'{info.filename!r}: the size in the zip header does not match the data', {'entry': info.filename})
    return b


def check_manifest(m, entries: dict) -> None:
    """m: parsed manifest; entries: {name: bytes} of every non-manifest entry. Raises UpdateRefused."""
    if not isinstance(m, dict) or m.get('format') != FORMAT_UPDATE:
        raise UpdateRefused('BAD_MANIFEST', f'not an update folder (format is {m.get("format") if isinstance(m, dict) else None!r})')
    v = m.get('format_version')
    if not isinstance(v, int) or isinstance(v, bool) or v < 1:
        raise UpdateRefused('BAD_MANIFEST', f'format_version {v!r} is not understood')
    if v > FORMAT_VERSION:
        raise UpdateRefused('NEWER_FORMAT', f'this update is format version {v}; this tracker reads up to {FORMAT_VERSION}. Update the tracker first.')
    src = m.get('source')
    sha = src.get('workbook_sha256') if isinstance(src, dict) else None
    if not (isinstance(sha, str) and re.fullmatch(r'[0-9a-f]{64}', sha)):
        raise UpdateRefused('BAD_MANIFEST', 'the manifest has no source workbook fingerprint')
    if not isinstance(m.get('created_at'), str):
        raise UpdateRefused('BAD_MANIFEST', 'the manifest has no created_at')
    files = m.get('files')
    if not isinstance(files, dict):
        raise UpdateRefused('BAD_MANIFEST', 'the manifest lists no files')
    for name in files:
        ok, why = entry_ok(name)
        if not ok or name == 'manifest.json':
            raise UpdateRefused('BAD_ENTRY', f'the manifest lists {name!r}: {why or "not allowed"}')
    extra = sorted(set(entries) - set(files))
    if extra:
        raise UpdateRefused('UNLISTED_FILE', f'the zip holds files the manifest does not list: {extra[:5]}', {'files': extra})
    missing = sorted(set(files) - set(entries))
    if missing:
        raise UpdateRefused('MISSING_FILE', f'the manifest lists files the zip does not hold: {missing[:5]}', {'files': missing})
    bad = []
    for name, meta in files.items():
        b = entries[name]
        if not isinstance(meta, dict) or meta.get('sha256') != sha256_bytes(b) or meta.get('bytes') != len(b):
            bad.append(name)
    if bad:
        raise UpdateRefused('HASH_MISMATCH', f'{len(bad)} file(s) do not match their checksum (damaged or edited): {bad[:5]}', {'files': bad})
    docs = {}
    for name, b in entries.items():
        if is_pdf_entry(name):
            continue
        try:
            doc = json.loads(b.decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            raise UpdateRefused('BAD_JSON', f'{name!r} is not valid JSON', {'entry': name})
        if not isinstance(doc, dict):
            raise UpdateRefused('BAD_JSON', f'{name!r} is not a JSON object', {'entry': name})
        docs[name] = doc
    if not any(n.startswith('db/runs/') for n in entries):
        raise UpdateRefused('BAD_MANIFEST', 'the update holds no run document')
    check_pdfs(entries, docs)


def check_pdfs(entries: dict, docs: dict) -> None:
    """NEWSBANKPDF-v1, PROQUESTPDF-v1: every files/<id>.pdf is a safe PDF, is named by exactly the pages doc(s) that carry it (nb.file or pq.file, with its sha256), and every
    pages doc that names a PDF finds it. Raises UpdateRefused (BAD_PDF, MISSING_FILE, UNLISTED_FILE, HASH_MISMATCH)."""
    refs = {}
    for name, doc in docs.items():
        if not name.startswith('db/pages/'):
            continue
        nb = doc.get('nb') if isinstance(doc.get('nb'), dict) else doc.get('pq')    # PROQUESTPDF-v1: a ProQuest story's PDF is named by the pages doc's `pq` the same way
        f = nb.get('file') if isinstance(nb, dict) else ''
        if not f:
            continue
        if not isinstance(f, str) or not is_pdf_entry(f):
            raise UpdateRefused('BAD_PDF', f'{name!r} names a PDF {f!r} that is not allowed (only files/<id>.pdf)', {'entry': name})
        refs.setdefault(f, []).append((name, nb.get('pdf_sha256')))
    for f, who in refs.items():
        if f not in entries:
            raise UpdateRefused('MISSING_FILE', f'{who[0][0]!r} names {f!r}, which the zip does not hold', {'files': [f]})
        for n, sha in who:
            if sha != sha256_bytes(entries[f]):
                raise UpdateRefused('HASH_MISMATCH', f'{n!r} gives another checksum for {f!r} than the file has', {'files': [f]})
    for name, b in entries.items():
        if not is_pdf_entry(name):
            continue
        if name not in refs:
            raise UpdateRefused('UNLISTED_FILE', f'{name!r} is not named by any pages document (a PDF nothing refers to is not taken in)', {'files': [name]})
        bad = pdf_problems(b)
        if bad:
            raise UpdateRefused('BAD_PDF', f'{name!r} is refused: it contains {", ".join(bad)}. A story PDF must hold pages only: no JavaScript, launch or open actions, embedded files or forms.', {'entry': name, 'problems': bad})
