#!/usr/bin/env python3
"""AJG Tracker PC server: serves the built tracker and stands in for the claude.ai runtime storage.

Python 3.11+, standard library only. Binds 127.0.0.1 only. See README.md.

    python server.py --site <folder with index.html> --data <data folder> [--port 8765]
"""
import argparse, hmac, json, mimetypes, os, re, secrets, sys, threading, time, uuid
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

VERSION = '1.0'
DEFAULT_PORT = 8765
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BODY = 64 * 1024 * 1024
SHIM_URL = '/_local/claude_shim.js'
SHIM_TAG = '<script src="%s"></script>' % SHIM_URL
COLL_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$')
ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')
WIN_RESERVED = {'con', 'prn', 'aux', 'nul', *('com%d' % i for i in range(1, 10)), *('lpt%d' % i for i in range(1, 10))}

TYPES = {
    '.html': 'text/html; charset=utf-8', '.htm': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
    '.txt': 'text/plain; charset=utf-8', '.csv': 'text/csv; charset=utf-8', '.md': 'text/plain; charset=utf-8',
    '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.gif': 'image/gif', '.webp': 'image/webp', '.ico': 'image/x-icon', '.avif': 'image/avif',
    '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.otf': 'font/otf',
    '.wasm': 'application/wasm', '.pdf': 'application/pdf', '.zip': 'application/zip',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xml': 'application/xml; charset=utf-8', '.map': 'application/json; charset=utf-8',
}


def valid_collection(c):
    return isinstance(c, str) and bool(COLL_RE.match(c))


def valid_id(i):
    return isinstance(i, str) and bool(ID_RE.match(i)) and not i.endswith('.') and i.split('.')[0].lower() not in WIN_RESERVED


def _busy_retry(fn, *args):
    """Windows: a file just written is sometimes held for a moment (virus scanner), and replacing it fails with "Access is denied".
    Wait and try again for about 10 seconds, PermissionError only (A15; same rule as fs_retry.py)."""
    delay = 0.05
    for attempt in range(16):
        try:
            return fn(*args)
        except PermissionError:
            if attempt == 15:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 1.0)


class StoreError(Exception):
    def __init__(self, status, msg):
        super().__init__(msg)
        self.status, self.msg = status, msg


class Store:
    """Documents as files: <data>/db/<collection>/<id>.json (the layout sheet_task.load_db reads)."""

    def __init__(self, data_dir):
        self.data = os.path.abspath(data_dir)
        self.root = os.path.join(self.data, 'db')
        self.lock = threading.Lock()
        self.bump = {}  # per-collection in-process change counter, part of the version string
        os.makedirs(self.root, exist_ok=True)

    def _cdir(self, c):
        if not valid_collection(c):
            raise StoreError(400, 'bad collection name')
        return os.path.join(self.root, c)

    def _path(self, c, i):
        if not valid_id(i):
            raise StoreError(400, 'bad document id')
        return os.path.join(self._cdir(c), i + '.json')

    def collections(self):
        try:
            return sorted(n for n in os.listdir(self.root)
                          if valid_collection(n) and os.path.isdir(os.path.join(self.root, n)))
        except OSError:
            return []

    def _files(self, c):
        d = self._cdir(c)
        try:
            return [e for e in os.scandir(d) if e.is_file() and e.name.endswith('.json') and not e.name.startswith('.')]
        except OSError:
            return []

    def version(self, c):
        """changes whenever a file is added, removed or rewritten (also by programs writing the folder)"""
        n, m = 0, 0
        for e in self._files(c):
            n += 1
            try:
                m = max(m, e.stat().st_mtime_ns)
            except OSError:
                pass
        return '%d:%d:%d' % (n, m, self.bump.get(c, 0))

    def versions(self, names=None):
        return {c: self.version(c) for c in (names if names is not None else self.collections()) if valid_collection(c)}

    @staticmethod
    def _read(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list(self, c):
        out = []
        for e in sorted(self._files(c), key=lambda e: e.name):
            try:
                out.append({'id': e.name[:-5], 'data': self._read(e.path)})
            except (OSError, ValueError):
                continue  # half-written or hand-damaged file: skip, never crash
        return out

    def get(self, c, i):
        p = self._path(c, i)
        try:
            return self._read(p)
        except FileNotFoundError:
            return None
        except ValueError:
            raise StoreError(500, 'document file is not valid JSON')

    def set(self, c, i, doc):
        if not isinstance(doc, dict):
            raise StoreError(400, 'a document must be a JSON object')
        p = self._path(c, i)
        d = os.path.dirname(p)
        raw = json.dumps(doc, ensure_ascii=False).encode('utf-8')
        with self.lock:
            os.makedirs(d, exist_ok=True)
            tmp = os.path.join(d, '.tmp-%s-%s.part' % (os.getpid(), uuid.uuid4().hex[:8]))
            try:
                with open(tmp, 'wb') as f:
                    f.write(raw)
                    f.flush()
                    os.fsync(f.fileno())
                _busy_retry(os.replace, tmp, p)
            finally:
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
            self.bump[c] = self.bump.get(c, 0) + 1

    def delete(self, c, i):
        """never deletes: moves the file to db/_deleted/<collection>/<id>.<timestamp>.json"""
        p = self._path(c, i)
        with self.lock:
            if not os.path.exists(p):
                return False
            dd = os.path.join(self.root, '_deleted', c)
            os.makedirs(dd, exist_ok=True)
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            _busy_retry(os.replace, p, os.path.join(dd, '%s.%s.json' % (i, stamp)))
            self.bump[c] = self.bump.get(c, 0) + 1
            return True

    def counts(self):
        return {c: len(self._files(c)) for c in self.collections()}

    def deleted_count(self):
        n = 0
        for dp, _, fs in os.walk(os.path.join(self.root, '_deleted')):
            n += sum(1 for f in fs if f.endswith('.json'))
        return n


class Handler(BaseHTTPRequestHandler):
    server_version = 'AJGLocal/' + VERSION
    protocol_version = 'HTTP/1.1'

    # --- plumbing
    def log_message(self, fmt, *a):
        if self.server.verbose:
            sys.stderr.write('%s %s\n' % (self.address_string(), fmt % a))

    def _send(self, status, body=b'', ctype='text/plain; charset=utf-8', extra=None, head=False):
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if not head and body:
            self.wfile.write(body)

    def _json(self, obj, status=200, head=False):
        self._send(status, json.dumps(obj, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8',
                   {'Cache-Control': 'no-store'}, head)

    def _err(self, status, msg, head=False):
        self._json({'error': msg}, status, head)

    def _host_ok(self):
        h = (self.headers.get('Host') or '').lower()
        port = self.server.server_address[1]
        if h not in ('127.0.0.1:%d' % port, 'localhost:%d' % port):
            return False
        o = self.headers.get('Origin')
        if o and o not in ('http://127.0.0.1:%d' % port, 'http://localhost:%d' % port):
            return False
        return True

    def _dispatch(self, method):
        head = method == 'HEAD'
        self._body = b''
        try:
            n = int(self.headers.get('Content-Length') or 0)
            if n > MAX_BODY or n < 0:
                self.close_connection = True
                return self._err(413, 'request too large')
            if n:
                self._body = self.rfile.read(n)  # always consume the body, so a refused request cannot corrupt the connection
            if not self._host_ok():
                return self._err(403, 'wrong host or origin', head)
            parts = urlsplit(self.path)
            path = unquote(parts.path, errors='strict')
            if '\x00' in path:
                return self._err(400, 'bad path', head)
            if path.startswith('/_local/'):
                return self._local(method, path, parts.query, head)
            if method not in ('GET', 'HEAD'):
                return self._err(405, 'method not allowed', head)
            return self._static(path, head)
        except StoreError as e:
            return self._err(e.status, e.msg, head)
        except (ConnectionError, BrokenPipeError):
            pass
        except (UnicodeDecodeError, ValueError):
            return self._err(400, 'bad request', head)
        except Exception as e:  # keep the server alive
            try:
                return self._err(500, 'server error: %s' % e, head)
            except Exception:
                pass

    do_GET = lambda self: self._dispatch('GET')
    do_HEAD = lambda self: self._dispatch('HEAD')
    do_PUT = lambda self: self._dispatch('PUT')
    do_POST = lambda self: self._dispatch('POST')
    do_DELETE = lambda self: self._dispatch('DELETE')

    # --- /_local/
    def _local(self, method, path, query, head):
        S = self.server
        if path == SHIM_URL:
            if method not in ('GET', 'HEAD'):
                return self._err(405, 'method not allowed')
            with open(os.path.join(HERE, 'claude_shim.js'), 'rb') as f:
                return self._send(200, f.read(), TYPES['.js'], {'Cache-Control': 'no-cache'}, head)
        if not hmac.compare_digest(self.headers.get('X-Local-Token') or '', S.token):
            return self._err(403, 'missing or wrong token (reload the tracker page)', head)
        if path == '/_local/status':
            return self._json({
                'app': 'ajg-tracker-local-server', 'version': VERSION, 'port': S.server_address[1],
                'site': S.site, 'data_dir': S.store.data, 'db_dir': S.store.root,
                'collections': S.store.counts(), 'deleted_files': S.store.deleted_count(),
                'started': S.started, 'time': datetime.now().isoformat(timespec='seconds'),
            }, head=head)
        if not path.startswith('/_local/api/'):
            return self._err(404, 'not found', head)
        segs = path[len('/_local/api/'):].split('/')
        if segs == ['_versions']:
            if method not in ('GET', 'HEAD'):
                return self._err(405, 'method not allowed')
            names = [n for n in (dict(q.split('=', 1) for q in query.split('&') if '=' in q).get('c') or '').split(',') if n]
            return self._json({'versions': S.store.versions(names or None)}, head=head)
        if len(segs) == 1 and segs[0]:
            c = segs[0]
            if method not in ('GET', 'HEAD'):
                return self._err(405, 'method not allowed')
            S.store._cdir(c)
            return self._json({'collection': c, 'version': S.store.version(c), 'docs': S.store.list(c)}, head=head)
        if len(segs) == 2 and segs[0] and segs[1]:
            c, i = segs
            if method in ('GET', 'HEAD'):
                doc = S.store.get(c, i)
                if doc is None:
                    return self._err(404, 'no such document', head)
                return self._json({'id': i, 'data': doc}, head=head)
            if method == 'PUT':
                try:
                    doc = json.loads(self._body.decode('utf-8'))
                except ValueError:
                    return self._err(400, 'body is not JSON')
                S.store.set(c, i, doc)
                return self._json({'ok': True, 'version': S.store.version(c)})
            if method == 'DELETE':
                moved = S.store.delete(c, i)
                return self._json({'ok': True, 'deleted': moved, 'version': S.store.version(c)})
            return self._err(405, 'method not allowed')
        return self._err(404, 'not found', head)

    # --- static files
    def _static(self, path, head):
        S = self.server
        if '\\' in path or path.startswith('//'):
            return self._err(400, 'bad path', head)
        rel = path.lstrip('/')
        segs = [s for s in rel.split('/') if s != '']
        if any(s in ('.', '..') or s.startswith('.') or ':' in s for s in segs):
            return self._err(403, 'forbidden', head)
        full = os.path.join(S.site_real, *segs) if segs else S.site_real
        if os.path.isdir(full):
            if path and not path.endswith('/') and segs:
                return self._err(404, 'not found', head)  # no listing, no redirect
            full = os.path.join(full, 'index.html')
        real = os.path.realpath(full)
        if os.path.commonpath([real, S.site_real]) != S.site_real:
            return self._err(403, 'forbidden', head)
        if not os.path.isfile(real):
            return self._err(404, 'not found', head)
        ext = os.path.splitext(real)[1].lower()
        ctype = TYPES.get(ext) or mimetypes.guess_type(real)[0] or 'application/octet-stream'
        st = os.stat(real)
        if real == S.index_real:
            with open(real, 'rb') as f:
                body = inject_shim(f.read(), self.server.token)
            return self._send(200, body, TYPES['.html'], {'Cache-Control': 'no-cache'}, head)
        etag = '"%x-%x"' % (st.st_mtime_ns, st.st_size)
        hdr = {'ETag': etag, 'Cache-Control': 'no-cache'}
        if self.headers.get('If-None-Match') == etag:
            return self._send(304, b'', ctype, hdr, head)
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(st.st_size))
        self.send_header('X-Content-Type-Options', 'nosniff')
        for k, v in hdr.items():
            self.send_header(k, v)
        self.end_headers()
        if not head:
            with open(real, 'rb') as f:
                while True:
                    b = f.read(1 << 20)
                    if not b:
                        break
                    self.wfile.write(b)


def inject_shim(raw, token=''):
    """put the per-launch token and the shim tag before the page's first <script> (or after <head>, or first)"""
    txt = raw.decode('utf-8', 'replace')
    if SHIM_URL in txt:
        return raw
    tag = '<script>window.__LOCAL_TOKEN="%s";</script>%s' % (token, SHIM_TAG)
    m = re.search(r'<script\b', txt, re.I) or re.search(r'<head\b[^>]*>', txt, re.I)
    if m and m.group(0).lower().startswith('<script'):
        i = m.start()
    elif m:
        i = m.end()
    else:
        i = 0
    return (txt[:i] + tag + txt[i:]).encode('utf-8')


class TrackerServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False  # a taken port must fail, never share

    def __init__(self, site, data, port=DEFAULT_PORT, verbose=False):
        self.site = os.path.abspath(site)
        self.site_real = os.path.realpath(self.site)
        if not os.path.isfile(os.path.join(self.site_real, 'index.html')):
            raise FileNotFoundError('no index.html in ' + self.site)
        self.index_real = os.path.join(self.site_real, 'index.html')
        self.store = Store(data)
        self.verbose = verbose
        self.token = secrets.token_urlsafe(24)  # new every launch; only the served page receives it
        self.started = datetime.now().isoformat(timespec='seconds')
        super().__init__(('127.0.0.1', port), Handler)


def main(argv=None):
    ap = argparse.ArgumentParser(description='AJG Tracker local server')
    ap.add_argument('--site', required=True, help='folder holding the built tracker (index.html)')
    ap.add_argument('--data', help='data folder (default: "data_local" beside the site folder)')
    ap.add_argument('--port', type=int, default=DEFAULT_PORT, help='port (default %d; keep it fixed, browser storage is tied to it)' % DEFAULT_PORT)
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args(argv)
    data = a.data or os.path.join(os.path.dirname(os.path.abspath(a.site)), 'data_local')
    try:
        srv = TrackerServer(a.site, data, a.port, a.verbose)
    except FileNotFoundError as e:
        print('Cannot start: %s' % e, file=sys.stderr)
        return 2
    except OSError as e:
        print('Cannot start: port %d is already in use or not allowed (%s).\n'
              'The tracker keeps your browser settings under this exact address, so it will not pick another port.\n'
              'Close the other copy of the tracker (or whatever uses port %d) and start again.' % (a.port, e, a.port), file=sys.stderr)
        return 3
    print('AJG Tracker running at http://127.0.0.1:%d/  (data: %s)\nPress Ctrl+C to stop.' % (srv.server_address[1], srv.store.data))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
