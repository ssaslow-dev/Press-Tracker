"""Test support: a working copy of the Linux test build, servers, the node/Chromium driver, synthetic update zips."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
APPSRC = HERE.parent
REPO = APPSRC.parents[2]
SCRATCH = Path('/tmp/claude-0/-home-user-Press-Tracker/ec7aac73-d461-552b-aaac-9f8ebc5e7581/scratchpad')
BUILD = Path(os.environ.get('AJG_TEST_BUILD') or SCRATCH / 'app_build' / 'linux' / 'AJG Tracker')
EXAMPLE_DB = REPO / 'build' / 'tests' / 'sheet_task' / 'fixtures' / 'example_db.json'
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'updatefolder'))
import formats as F  # noqa: E402

SHOTS = Path(os.environ.get('AJG_TEST_SHOTS') or SCRATCH / 'app_build' / 'test_shots')
SHOTS.mkdir(parents=True, exist_ok=True)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def make_work(base: Path, name: str, role: str) -> Path:
    """a hard-linked copy of the test build (the 900 MB library is shared, never written in place); workbook and state are real copies"""
    root = base / name / 'AJG Tracker'
    shutil.copytree(BUILD, root, symlinks=True, copy_function=os.link)
    data = root / 'data'
    wb = next((data / 'workbook').glob('*.xlsx'))
    tmp = wb.with_name('x.tmp')
    shutil.copy2(wb, tmp)
    wb.unlink()
    tmp.rename(wb)
    ledger = data / 'state' / 'ledger.jsonl'
    t = ledger.read_bytes()
    ledger.unlink()
    ledger.write_bytes(t)
    for d in ('tmp', 'db', 'backups', 'updates', 'for_update', 'refresh_out'):
        shutil.rmtree(data / d, ignore_errors=True)
    for d in ('tmp', 'db', 'backups', 'for_update', 'refresh_out', 'updates/incoming', 'updates/staging', 'updates/work', 'updates/done',
              'updates/rejected', 'updates/refresh_incoming'):
        (data / d).mkdir(parents=True, exist_ok=True)
    (data / 'role.json').unlink()
    (data / 'role.json').write_text(json.dumps({'role': role}))
    return root


class Server:
    def __init__(self, root: Path, port: int | None = None):
        self.root, self.port = root, port or free_port()
        self.proc = None
        self.log = root.parent / f'server-{self.port}.log'

    def start(self):
        env = dict(os.environ, AJG_NO_BROWSER='1', AJG_TEST_PORT=str(self.port))
        self.proc = subprocess.Popen([str(self.root / 'python' / 'bin' / 'python'), '-B', '-X', 'utf8', '-I', 'app/station/launcher.py'], cwd=self.root,
                                     env=env, stdout=open(self.log, 'w'), stderr=subprocess.STDOUT)
        for _ in range(100):
            try:
                self.get('/_local/station/ping')
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise RuntimeError('server did not start: ' + self.log.read_text())
        self.token = re.search(r'window\.__LOCAL_TOKEN="([^"]+)"', self.get('/').decode('utf-8', 'replace')).group(1)
        return self

    def stop(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    @property
    def base(self):
        return f'http://127.0.0.1:{self.port}'

    def get(self, path, headers=None):
        req = urllib.request.Request(self.base + path, headers=headers or {})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()

    def call(self, method, path, body=None, raw=None, headers=None):
        h = {'X-Local-Token': getattr(self, 'token', '')}
        h.update(headers or {})
        data = raw
        if body is not None:
            data = json.dumps(body).encode()
            h['Content-Type'] = 'application/json'
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, json.loads(r.read() or b'null')
        except urllib.error.HTTPError as e:
            t = e.read()
            try:
                return e.code, json.loads(t)
            except ValueError:
                return e.code, {'raw': t.decode('utf-8', 'replace')}

    def job(self, verb, body=None, timeout=900):
        st, j = self.call('POST', '/_local/station/' + verb, body or {})
        if st != 200 or not j.get('job'):
            return {'_http': st, **(j or {})}
        t0 = time.time()
        while time.time() - t0 < timeout:
            st, r = self.call('GET', '/_local/station/job/' + j['job'])
            if r['state'] == 'done':
                return r['result']
            time.sleep(1)
        raise TimeoutError(verb)

    def upload(self, path: Path, kind='update'):
        return self.call('POST', f'/_local/station/upload?kind={kind}&name={path.name}', raw=path.read_bytes())


def ui(server: Server, steps: list, name='ui', timeout=1800):
    sp = SHOTS.parent / f'{name}.steps.json'
    sp.write_text(json.dumps(steps))
    env = dict(os.environ, PLAYWRIGHT_MODULE='/opt/node-tools/node_modules/playwright')
    p = subprocess.run(['node', str(HERE / 'ui.js'), server.base, str(sp)], capture_output=True, text=True, env=env, timeout=timeout)
    if p.returncode:
        raise RuntimeError('node failed: ' + p.stderr[-800:])
    return json.loads(p.stdout.strip().splitlines()[-1])


def make_update_zip(root: Path, out: Path, suffix='example1', fake_sha=None) -> Path:
    """a synthetic update folder from the example db (renamed per suffix so every one is a new find), fingerprint = the workbook's sha"""
    txt = EXAMPLE_DB.read_text(encoding='utf-8')
    if suffix != 'example1':
        txt = (txt.replace('example1', suffix).replace('gabriel-one', f'gabriel-{suffix}').replace('Gabriel bill test story one', f'Gabriel bill test story {suffix}')
               .replace('echotimes.com/gabriel', f'echotimes.com/gabriel').replace('reprintweekly.com/x', f'reprintweekly.com/x-{suffix}'))
    ex = json.loads(txt)
    # every saved page also carries a remote photo (the PC is offline: it must be dropped, not trip the media gate) and one searchable word
    mark = f'<img src="https://images.example.com/photo-{suffix}.jpg" alt="photo"><p>Quokka{suffix} searchable marker words.</p>'
    for doc in ex.get('pages', {}).values():
        for k, v in list(doc.items()):
            if isinstance(v, str) and '</body>' in v:
                doc[k] = v.replace('</body>', mark + '</body>')
    d = out.with_suffix('.db')
    shutil.rmtree(d, ignore_errors=True)
    for coll, docs in ex.items():
        for k, v in docs.items():
            p = d / coll / f'{k}.json'
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(v))
    wb = next((root / 'data' / 'workbook').glob('*.xlsx'))
    return F.pack_update_zip(out, d, fake_sha or sha(wb))
