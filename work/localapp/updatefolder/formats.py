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
# STATIONNAMES (LIBFILES-v1 follow-up 2): the files the station names by the library's schema (NAMING-v2) travel under library/ in the library's own layout:
#   library/<year>/<ws|nb|pq><Article ID><o|r>[-s<Story ID>].<html|pdf>     saved copies (a NewsBank saved copy is the story PDF; ws and pq are HTML)
#   library/_original_html/<year>/<same name>.html                          raw pages;  library/_original_pdf/<year>/pq<...>.pdf  ProQuest originals
#   library/Press releases/<year>/pr<Release ID>.html  and  library/_original_html/Press releases/<year>/pr<Release ID>.html
# The manifest's `names` block says which row/pages document/release each file belongs to (section 2d of FORMAT.md). Data only: HTML is never opened here.
LIB_STEM = r'(?:(?:ws|nb|pq)\d{5,}[or]?(?:-s\d{5,})?(?:-v\d{1,3})?|pr\d{5,})'
LIB_ENTRY_RE = re.compile(r'^library/(?P<dir>(?:_original_html/|_original_pdf/)?(?:Press releases/)?)(?P<year>\d{4}|undated)/(?P<stem>' + LIB_STEM + r')\.(?P<ext>html|pdf)$')
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


def lib_entry(name: str):
    """The match for a library/ entry that obeys the layout rules, else None: releases (pr...) only in Press releases folders and only html; ws/nb/pq
    names never in a Press releases folder; a PDF only as a NewsBank saved copy (library/<year>/nb...) or a ProQuest original (library/_original_pdf/<year>/pq...);
    html never under _original_pdf."""
    m = LIB_ENTRY_RE.match(name or '')
    if not m:
        return None
    d, stem, ext = m.group('dir'), m.group('stem'), m.group('ext')
    rel = stem.startswith('pr')
    if rel != d.endswith('Press releases/') or (rel and ext != 'html'):
        return None
    if d.startswith('_original_pdf/'):
        return m if (ext == 'pdf' and stem.startswith('pq') and d == '_original_pdf/') else None
    if ext == 'pdf':
        return m if (d == '' and stem.startswith('nb')) else None
    return m


def is_lib_entry(name: str) -> bool:
    return lib_entry(name) is not None


def is_pdf_entry(name: str) -> bool:
    m = PDF_ENTRY_RE.match(name or '')
    if m:
        return True
    m = lib_entry(name)
    return bool(m and m.group('ext') == 'pdf')


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
    if name.startswith('library/'):
        return (True, '') if lib_entry(name) else (False, 'not a library file name of the schema (library/<year>/<ws|nb|pq><Article ID><o|r>-s<Story ID>.html|pdf, _original_html/, _original_pdf/, Press releases/)')
    m = ENTRY_RE.match(name) or PDF_ENTRY_RE.match(name)
    if not m:
        return False, 'not an allowed file (only manifest.json, db/<collection>/<id>.json, files/<id>.pdf and library/... files named by the schema)'
    if m.groups()[-1].split('.')[0].upper() in WINDOWS_RESERVED:
        return False, 'reserved Windows file name'
    return True, ''


def pack_update_zip(out_zip, db_dir, source_workbook_sha256: str, *, created_at=None, extra_manifest=None, library=None) -> Path:
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
    for name, b in (library or {}).items():           # STATIONNAMES: {'library/2026/ws10670o-s04942.html': bytes}
        ok, why = entry_ok(name)
        if not ok or not name.startswith('library/'):
            raise ValueError(f'{name}: {why or "not a library name"}')
        blobs[name] = b
        files[name] = {'sha256': sha256_bytes(b), 'bytes': len(b), 'kind': 'pdf' if name.endswith('.pdf') else 'html'}
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
        if is_lib_entry(name):                                  # STATIONNAMES: saved HTML. Data only; it must be text (UTF-8) and is never opened here.
            try:
                b.decode('utf-8')
            except UnicodeDecodeError:
                raise UpdateRefused('BAD_HTML', f'{name!r} is not UTF-8 text', {'entry': name})
            if b'\x00' in b:
                raise UpdateRefused('BAD_HTML', f'{name!r} holds a NUL character', {'entry': name})
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
    names = check_names(m.get('names'), entries, docs)
    check_pdfs(entries, docs, names)


def _bad_names(msg, **d):
    return UpdateRefused('BAD_NAMES', 'the manifest\'s names block is not right: ' + msg, d)


def check_names(names, entries: dict, docs: dict) -> dict:
    """STATIONNAMES: the manifest's `names` block (FORMAT.md 2d) says what every library/ file is. Every library file must be claimed exactly once, each
    path must be exactly the name the schema gives for the fields next to it, and a PDF must be the one its pages document names (same checksum).
    Returns {logical PDF path (files/<id>.pdf, as a pages doc names it): the library/ entry that holds it}. No `names` block: no library/ files allowed."""
    libs = sorted(n for n in entries if is_lib_entry(n))
    if names is None:
        if libs:
            raise UpdateRefused('UNLISTED_FILE', f'the zip holds library files but the manifest has no names block: {libs[:5]}', {'files': libs})
        return {}
    if not isinstance(names, dict) or names.get('version') != 1 or not isinstance(names.get('items'), list) or not isinstance(names.get('releases', []), list):
        raise _bad_names('expected {version: 1, items: [...], releases: [...]}')
    claimed, pdf_map, aids = {}, {}, set()

    def claim(path, who, want):
        if not isinstance(path, str):
            raise _bad_names(f'{who}: a path is not text')
        if path != want:
            raise _bad_names(f'{who}: {path!r} is not the name the schema gives ({want!r})', entry=path)
        if path not in entries:
            raise UpdateRefused('MISSING_FILE', f'{who}: the names block lists {path!r}, which the zip does not hold', {'files': [path]})
        if path in claimed:
            raise _bad_names(f'{path!r} is claimed twice ({claimed[path]} and {who})', entry=path)
        claimed[path] = who

    for n, it in enumerate(names['items']):
        who = f'item {n}'
        if not isinstance(it, dict):
            raise _bad_names(f'{who} is not an object')
        aid, sid, kind, fmt, year = (it.get(k) for k in ('aid', 'sid', 'kind', 'fmt', 'year'))
        if not (isinstance(aid, str) and re.fullmatch(r'\d{5,}', aid) and isinstance(sid, str) and re.fullmatch(r'(s\d{5,})?', sid) and kind in ('o', 'r')
                and fmt in ('ws', 'nb', 'pq') and isinstance(year, str) and re.fullmatch(r'\d{4}|undated', year)):
            raise _bad_names(f'{who}: aid, sid, kind, fmt or year is malformed')
        if aid in aids:
            raise _bad_names(f'{who}: Article ID {aid} appears twice')
        aids.add(aid)
        doc = it.get('doc') or ''
        pdoc = docs.get(f'db/pages/{doc}.json') if doc else None
        if doc and pdoc is None:
            raise _bad_names(f'{who}: pages document {doc!r} is not in the update')
        stem = f'{fmt}{aid}{kind}' + (f'-{sid}' if sid else '')
        paths = {'copy': f'library/{year}/{stem}.' + ('pdf' if fmt == 'nb' else 'html'), 'raw': f'library/_original_html/{year}/{stem}.html',
                 'pdf': f'library/_original_pdf/{year}/{stem}.pdf'}
        for k in ('copy', 'raw', 'pdf'):
            if it.get(k):
                if not doc:
                    raise _bad_names(f'{who}: a file is named but no pages document')
                if k == 'raw' and fmt != 'ws' or k == 'pdf' and fmt != 'pq':
                    raise _bad_names(f'{who}: a {fmt} story has no {k} file')
                claim(it[k], f'{who} ({k})', paths[k])
        pf = it.get('pdf_for') or ''
        pdf_path = it.get('pdf') or (it.get('copy') if fmt == 'nb' else '')
        if pdf_path:
            src = (pdoc or {}).get('nb' if fmt == 'nb' else 'pq')
            f = src.get('file') if isinstance(src, dict) else ''
            if not (pf and pf == f and PDF_ENTRY_RE.match(pf)):
                raise _bad_names(f'{who}: pdf_for {pf!r} is not the PDF its pages document names ({f!r})')
            if src.get('pdf_sha256') != sha256_bytes(entries[pdf_path]):
                raise UpdateRefused('HASH_MISMATCH', f'{who}: the pages document gives another checksum than {pdf_path!r} has', {'files': [pdf_path]})
            if pf in pdf_map:
                raise _bad_names(f'{who}: {pf!r} is named by two files')
            pdf_map[pf] = pdf_path
        elif pf:
            raise _bad_names(f'{who}: pdf_for without a PDF file')
    for n, r in enumerate(names.get('releases') or []):
        who = f'release {n}'
        if not (isinstance(r, dict) and isinstance(r.get('prid'), str) and re.fullmatch(r'pr\d{5,}', r['prid']) and isinstance(r.get('year'), str) and re.fullmatch(r'\d{4}|undated', r['year'])):
            raise _bad_names(f'{who} is malformed')
        for k, d in (('copy', 'Press releases'), ('raw', '_original_html/Press releases')):
            if r.get(k):
                claim(r[k], f'{who} ({k})', f'library/{d}/{r["year"]}/{r["prid"]}.html')
    left = sorted(set(libs) - set(claimed))
    if left:
        raise UpdateRefused('UNLISTED_FILE', f'library files the names block does not claim: {left[:5]}', {'files': left})
    return pdf_map


def check_pdfs(entries: dict, docs: dict, names_map=None) -> None:
    """NEWSBANKPDF-v1, PROQUESTPDF-v1: every files/<id>.pdf is a safe PDF, is named by exactly the pages doc(s) that carry it (nb.file or pq.file, with its sha256), and every
    pages doc that names a PDF finds it. Raises UpdateRefused (BAD_PDF, MISSING_FILE, UNLISTED_FILE, HASH_MISMATCH)."""
    refs = {}
    for name, doc in docs.items():
        if name.startswith('db/runs/'):       # OTHERFILES-v1 / ORIGCOPIES-v1: a run's extra_copies name PDFs (another original copy of a story already in the tracker) the same way
            for x in doc.get('extra_copies') or []:
                f = x.get('file') if isinstance(x, dict) else None
                if not isinstance(f, str) or not PDF_ENTRY_RE.match(f):
                    raise UpdateRefused('BAD_PDF', f'{name!r} has an extra copy with a PDF {f!r} that is not allowed (only files/<id>.pdf)', {'entry': name})
                refs.setdefault(f, []).append((name, x.get('pdf_sha256')))
            continue
        if not name.startswith('db/pages/'):
            continue
        nb = doc.get('nb') if isinstance(doc.get('nb'), dict) else doc.get('pq')    # PROQUESTPDF-v1: a ProQuest story's PDF is named by the pages doc's `pq` the same way
        f = nb.get('file') if isinstance(nb, dict) else ''
        if not f:
            continue
        if not isinstance(f, str) or not PDF_ENTRY_RE.match(f):
            raise UpdateRefused('BAD_PDF', f'{name!r} names a PDF {f!r} that is not allowed (only files/<id>.pdf)', {'entry': name})
        refs.setdefault(f, []).append((name, nb.get('pdf_sha256')))
    names_map = names_map or {}
    for f, who in refs.items():
        loc = names_map.get(f, f)               # STATIONNAMES: the PDF may travel under its library name
        if loc not in entries:
            raise UpdateRefused('MISSING_FILE', f'{who[0][0]!r} names {f!r}, which the zip does not hold', {'files': [f]})
        for n, sha in who:
            if sha != sha256_bytes(entries[loc]):
                raise UpdateRefused('HASH_MISMATCH', f'{n!r} gives another checksum for {f!r} than the file has', {'files': [f]})
    held = {names_map.get(f, f) for f in refs}
    for name, b in entries.items():
        if not is_pdf_entry(name):
            continue
        if name not in held:
            raise UpdateRefused('UNLISTED_FILE', f'{name!r} is not named by any pages document (a PDF nothing refers to is not taken in)', {'files': [name]})
        bad = pdf_problems(b)
        if bad:
            raise UpdateRefused('BAD_PDF', f'{name!r} is refused: it contains {", ".join(bad)}. A story PDF must hold pages only: no JavaScript, launch or open actions, embedded files or forms.', {'entry': name, 'problems': bad})
