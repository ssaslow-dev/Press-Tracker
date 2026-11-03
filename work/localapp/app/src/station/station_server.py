"""station_server.py: the PC tracker server with the "Tracker files" panel (wrapper around server/server.py; that file is not edited).

What this adds to server.py (APP-WRAP):
  - the page gets one more script (/_local/station.js: the panel) and one style block that hides the Update, tone, author and
    translation buttons (the CSS list of code/make_viewer.py:25 without the download entries, plus data-trate / data-afind / data-trstory);
  - /articles/<file>.json is served from data/copies/articles (the one copy of the article shards, which the save also reads);
  - /_local/station/* endpoints (token as everywhere else) that run station_cli.py jobs one at a time: make the "for Update" file,
    take in an update zip, preview, save, set aside, accept the workbook, rebuild the page; and a status call.
Listens on 127.0.0.1 only. Children run with the bundled python -B -X utf8 -I, cwd = the tracker folder, no shell, no network.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import common as C
import refresh as R
import server as S

HERE = Path(__file__).resolve().parent
WEB = HERE / 'web'
UPLOAD_MAX = 256 * 1024 * 1024          # an update zip (formats.py caps it at 256 MB too)
REFRESH_MAX = R.CAP_TOTAL               # a FULL refresh carries the whole library
APP_ID = 'ajg-tracker'
HIDE_CSS = ('#runFind,#runRefresh,#raStrip,[data-runfind],#updGo,#updRefresh,#updSave,#updAdd,#updCopy,#updAgain,'
            '[data-trate],[data-afind],[data-trstory],[data-tstop],[data-astop]{display:none!important}')
ID_OK = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._ ()-]{0,100}$')
SHA_OK = re.compile(r'^[0-9a-f]{64}$')
TOKEN_OK = re.compile(r'^[0-9a-f]{8,64}$')
RF_OK = re.compile(r'^refresh_(full|incr)_[0-9]{4}_[0-9TZ]+_[0-9a-f]{8}( \([0-9]+\))?\.zip$')
FU_OK = re.compile(r'^for_update_[0-9]{12}_[0-9a-f]{8}( \([0-9]+\))?\.json$')
SHARD_OK = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*\.json$')


def root_id(root: Path) -> str:
    return hashlib.sha256(str(root).encode('utf-8')).hexdigest()[:12]


# ---------------------------------------------------------------- jobs (one at a time on this PC)


class Jobs:
    def __init__(self, root: Path):
        self.root = root
        self.lock = threading.Lock()
        self.current = None
        self.done = {}

    def summary(self, j):
        return None if j is None else {k: j[k] for k in ('id', 'verb', 'state', 'started', 'seconds') if k in j}

    def start(self, verb: str, args: list):
        with self.lock:
            if self.current and self.current['state'] == 'running':
                return None
            j = {'id': uuid.uuid4().hex[:12], 'verb': verb, 'state': 'running', 'started': time.time(), 'result': None}
            self.current = j
            self.done[j['id']] = j
            for old in list(self.done)[:-20]:
                self.done.pop(old, None)
        threading.Thread(target=self._run, args=(j, verb, args), daemon=True).start()
        return j

    def _run(self, j, verb, args):
        cmd = [sys.executable, '-B', '-X', 'utf8', '-I', str(HERE / 'station_cli.py'), verb, '--root', str(self.root)] + args
        env = dict(os.environ, AJG_NO_NETWORK='1', AJG_LINK_PHOTOS='1', PYTHONDONTWRITEBYTECODE='1')
        try:
            tmp = Path(self.root) / 'data' / 'tmp'       # GOVIT-v1: temporary files only inside the app folder
            tmp.mkdir(parents=True, exist_ok=True)
            env.update(TMP=str(tmp), TEMP=str(tmp), TMPDIR=str(tmp))
        except OSError:
            pass
        try:
            p = subprocess.run(cmd, cwd=str(self.root), capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, timeout=7200)
            try:
                res = json.loads(p.stdout.strip().splitlines()[-1])
            except (ValueError, IndexError):
                res = {'ok': False, 'line': 'The job gave no answer. ' + (p.stderr or '')[-300:]}
            res['exit_code'] = p.returncode
        except subprocess.TimeoutExpired:
            res = {'ok': False, 'line': 'The job took too long and was stopped. The save program may still be finishing: check the workbook status in a few minutes before trying again.'}
        except OSError as e:
            res = {'ok': False, 'line': f'The job could not start: {e}'[:300]}
        j['result'] = res
        j['seconds'] = round(time.time() - j['started'], 1)
        j['state'] = 'done'

    def get(self, jid):
        j = self.done.get(jid)
        if not j:
            return None
        d = self.summary(j)
        d['seconds'] = round(time.time() - j['started'], 1) if j['state'] == 'running' else j.get('seconds')
        d['result'] = j['result']
        return d


# ---------------------------------------------------------------- handler


class StationHandler(S.Handler):
    server_version = 'AJGStation/1.0'

    # -- plumbing
    def end_headers(self):
        # PHOTOLINK-v1: no response of this server tells a news site where the reader came from (the page, the shards, everything)
        self.send_header('Referrer-Policy', 'no-referrer')
        super().end_headers()

    def _token_ok(self):
        return hmac.compare_digest(self.headers.get('X-Local-Token') or '', self.server.token)

    def _dispatch(self, method):
        if method == 'POST' and urlsplit(self.path).path == '/_local/station/upload':
            return self._upload()
        return super()._dispatch(method)

    def _static(self, path, head):
        if path.startswith('/articles/'):
            return self._articles(path, head)
        return super()._static(path, head)

    def _articles(self, path, head):
        name = path[len('/articles/'):]
        if not SHARD_OK.match(name):
            return self._err(404, 'not found', head)
        f = self.server.lay.copies / 'articles' / name
        try:
            body = f.read_bytes()
        except OSError:
            return self._err(404, 'not found', head)
        return self._send(200, body, S.TYPES['.json'], {'Cache-Control': 'no-cache'}, head)

    def _upload(self):
        self.close_connection = True
        if not self._host_ok():
            return self._err(403, 'wrong host or origin')
        if not self._token_ok():
            return self._err(403, 'missing or wrong token (reload the tracker page)')
        q = parse_qs(urlsplit(self.path).query)
        kind = (parse_qs(urlsplit(self.path).query).get('kind') or ['update'])[0]
        want = 'reader' if kind == 'refresh' else 'keeper'
        if R.role(self.server.lay) != want:
            return self._err(403, 'This copy of the tracker %s.' % ('is the keeper copy and does not take refresh files' if want == 'reader' else 'is a reader copy and does not take in updates'))
        name = re.sub(r'[^A-Za-z0-9._ -]', '_', os.path.basename((q.get('name') or ['update.zip'])[0]))[:80]
        if not name.lower().endswith('.zip'):
            return self._err(400, 'An update must be a .zip file.')
        n = int(self.headers.get('Content-Length') or 0)
        if n <= 0:
            return self._err(411, 'empty upload')
        if n > (REFRESH_MAX if kind == 'refresh' else UPLOAD_MAX):
            return self._err(413, 'That file is larger than this kind of file may be.')
        inc = self.server.lay.updates / ('refresh_incoming' if kind == 'refresh' else 'incoming')
        inc.mkdir(parents=True, exist_ok=True)
        dest = inc / f'{C.stamp()}-{name}'
        part = dest.with_name(dest.name + '.part')
        h = hashlib.sha256()
        left = n
        try:
            with open(part, 'wb') as f:
                while left > 0:
                    b = self.rfile.read(min(1 << 20, left))
                    if not b:
                        break
                    f.write(b)
                    h.update(b)
                    left -= len(b)
            if left:
                os.replace(part, dest.with_name(dest.name + '.incomplete'))
                return self._err(400, 'The upload was cut off. Try again.')
            os.replace(part, dest)
        except OSError as e:
            return self._err(500, f'could not store the upload: {e}')
        return self._json({'ok': True, 'file': dest.name, 'bytes': n, 'sha256': h.hexdigest()})

    # -- /_local/
    def _local(self, method, path, query, head):
        if path == '/_local/station.js':
            return self._send(200, (WEB / 'panel.js').read_bytes(), S.TYPES['.js'], {'Cache-Control': 'no-cache'}, head)
        if path == '/_local/station/ping':
            S_ = self.server
            return self._json({'app': APP_ID, 'root': str(S_.root), 'root_id': root_id(S_.root), 'started': S_.started}, head=head)
        if path.startswith('/_local/station/refresh_out/') and method in ('GET', 'HEAD'):
            tok = (parse_qs(query).get('t') or [''])[0]        # a plain link must be able to download a big file: the token rides in the URL (loopback only)
            if not hmac.compare_digest(tok, self.server.token) or R.role(self.server.lay) != 'keeper':
                return self._err(403, 'missing or wrong token (reload the tracker page)', head)
            name = unquote(path[len('/_local/station/refresh_out/'):])
            f = self.server.lay.data / 'refresh_out' / name
            if not RF_OK.match(name) or not f.is_file():
                return self._err(404, 'not found', head)
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Length', str(f.stat().st_size))
            self.send_header('Content-Disposition', 'attachment; filename="%s"' % name)
            self.end_headers()
            if not head:
                with open(f, 'rb') as fh:
                    shutil.copyfileobj(fh, self.wfile, 1 << 20)
            return
        if path.startswith('/_local/station/'):
            if not self._token_ok():
                return self._err(403, 'missing or wrong token (reload the tracker page)', head)
            return self._station(method, path[len('/_local/station/'):], head)
        return super()._local(method, path, query, head)

    def _body_json(self):
        try:
            d = json.loads(self._body.decode('utf-8') or '{}')
        except ValueError:
            raise S.StoreError(400, 'body is not JSON')
        if not isinstance(d, dict):
            raise S.StoreError(400, 'body must be an object')
        return d

    def _station(self, method, rest, head):
        srv = self.server
        lay, jobs = srv.lay, srv.jobs
        if rest == 'status' and method in ('GET', 'HEAD'):
            return self._json(srv.status(), head=head)
        if rest.startswith('job/') and method in ('GET', 'HEAD'):
            j = jobs.get(rest[4:])
            return self._json(j, head=head) if j else self._err(404, 'no such job', head)
        if rest.startswith('for_update/') and method in ('GET', 'HEAD'):
            name = unquote(rest[len('for_update/'):])
            f = lay.for_update / name
            if not FU_OK.match(name) or not f.is_file():
                return self._err(404, 'not found', head)
            return self._send(200, f.read_bytes(), S.TYPES['.json'], {'Content-Disposition': 'attachment; filename="%s"' % name,
                                                                      'Cache-Control': 'no-store'}, head)
        if method != 'POST':
            return self._err(405, 'method not allowed', head)
        d = self._body_json()
        r_ = R.role(lay)
        if rest in ('inspect', 'preview', 'save', 'reject', 'init', 'refresh_make') and r_ != 'keeper':
            return self._json({'ok': False, 'line': 'This copy of the tracker is a reader copy. Only the keeper copy takes in updates, accepts the workbook or makes refresh files.'}, 403)
        if rest == 'refresh_take' and r_ == 'keeper':
            return self._json({'ok': False, 'line': 'This is the keeper copy. It makes refresh files; it does not take them in.'}, 403)
        verb, args = None, []
        if rest == 'make':
            verb = 'make'
        elif rest == 'rebuild':
            verb = 'rebuild'
        elif rest == 'refresh_make':
            verb, args = 'refresh_make', (['--full'] if d.get('full') is True else [])
        elif rest == 'refresh_take':
            f = str(d.get('file') or '')
            if not re.match(r'^[A-Za-z0-9._ ()-]{1,120}$', f) or '..' in f or not (lay.updates / 'refresh_incoming' / f).is_file():
                return self._err(400, 'That upload is not there. Choose the file again.')
            verb, args = 'refresh_take', ['--zip', str(lay.updates / 'refresh_incoming' / f)]
        elif rest == 'inspect':
            f = str(d.get('file') or '')
            if not re.match(r'^[A-Za-z0-9._ ()-]{1,120}$', f) or '..' in f or not (lay.updates / 'incoming' / f).is_file():
                return self._err(400, 'That upload is not there. Choose the file again.')
            verb, args = 'inspect', ['--zip', str(lay.updates / 'incoming' / f)]
        elif rest in ('preview', 'save', 'reject'):
            uid = str(d.get('update_id') or '')
            if not ID_OK.match(uid) or '..' in uid or not (lay.updates / 'staging' / uid).is_dir():
                return self._err(400, 'That update is no longer waiting. Bring it in again.')
            verb, args = rest, ['--update', uid]
            if rest in ('preview', 'save') and d.get('accept_mismatch') is True:
                args.append('--accept-mismatch')
            if rest == 'save':
                tok = str(d.get('token') or '')
                if not TOKEN_OK.match(tok):
                    return self._err(400, 'The preview must be made first.')
                args += ['--token', tok]
        elif rest == 'init':
            sha = str(d.get('sha') or '')
            if not SHA_OK.match(sha):
                return self._err(400, 'bad fingerprint')
            verb, args = 'init', ['--sha', sha]
        else:
            return self._err(404, 'not found')
        j = jobs.start(verb, args)
        if j is None:
            return self._json({'ok': False, 'busy': True, 'line': 'The tracker is still busy with the last step on this PC. Wait for it to finish.'}, 409)
        return self._json({'ok': True, 'job': j['id']})


def station_inject(raw, token=''):
    out = _orig_inject(raw, token)
    txt = out.decode('utf-8', 'replace')
    extra = '<style id="ajg-station-hide">%s</style><script src="/_local/station.js" defer></script>' % HIDE_CSS
    if 'ajg-station-hide' in txt:
        return out
    i = txt.find('<script src="%s"></script>' % S.SHIM_URL)
    if i < 0:
        return out
    i += len('<script src="%s"></script>' % S.SHIM_URL)
    return (txt[:i] + extra + txt[i:]).encode('utf-8')


_orig_inject = S.inject_shim
S.inject_shim = station_inject


class StationServer(S.TrackerServer):
    def __init__(self, root: Path, port=S.DEFAULT_PORT, verbose=False):
        self.root = Path(root).resolve()
        self.lay = C.layout(self.root)
        S.Handler, orig = StationHandler, S.Handler
        try:
            super().__init__(str(self.lay.data / 'site'), str(self.lay.data), port, verbose)
        finally:
            S.Handler = orig
        self.jobs = Jobs(self.root)

    def status(self):
        lay = self.lay
        fu = sorted(lay.for_update.glob('for_update_*.json'), key=lambda p: p.stat().st_mtime) if lay.for_update.is_dir() else []
        return {'app': APP_ID, 'root': str(self.root), 'role': R.role(lay), 'ledger_seq': R.seq_of(lay), 'refresh_applied': R._read_json(lay.state / 'refresh_applied.json', None),
                'refresh_made': R._read_json(lay.state / 'refresh_state.json', None), 'workbook': C.workbook_state(lay), 'lock': C.lock_status(lay.state),
                'job': self.jobs.summary(self.jobs.current), 'page_built': (lay.data / 'site' / 'index.html').is_file(),
                'pipeline_ok': (lay.pipeline / 'PIPELINE.sha256').is_file(),
                'last_for_update': fu[-1].name if fu else None, 'time': time.time()}
