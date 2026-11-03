"""PC side helpers for the chain check: a working copy of the Linux test build, the local server, the node/Chromium step driver.
Written for this folder (copied in spirit from work/localapp/app/tests/support.py so the check does not depend on that file)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import socket
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
NODE_MODULES = os.environ.get('PLAYWRIGHT_MODULE') or '/opt/node-tools/node_modules/playwright'


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def free_port() -> int:
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def make_work(build: Path, base: Path, name: str, role: str) -> Path:
    """a hard-linked copy of the test build (the library is shared and never written in place); workbook and ledger are real copies; state is reset"""
    root = base / name / 'AJG Tracker'
    shutil.rmtree(base / name, ignore_errors=True)
    shutil.copytree(build, root, symlinks=True, copy_function=os.link)
    data = root / 'data'
    wb = next((data / 'workbook').glob('*.xlsx'))
    tmp = wb.with_name('x.tmp')
    shutil.copy2(wb, tmp)
    wb.unlink()
    tmp.rename(wb)
    ledger = data / 'state' / 'ledger.jsonl'
    if ledger.exists():
        t = ledger.read_bytes()
        ledger.unlink()
        ledger.write_bytes(t)
    for d in ('tmp', 'db', 'backups', 'updates', 'for_update', 'refresh_out'):
        shutil.rmtree(data / d, ignore_errors=True)
    for d in ('tmp', 'db', 'backups', 'for_update', 'refresh_out', 'updates/incoming', 'updates/staging', 'updates/work', 'updates/done',
              'updates/rejected', 'updates/refresh_incoming'):
        (data / d).mkdir(parents=True, exist_ok=True)
    rj = data / 'role.json'
    if rj.exists():
        rj.unlink()
    rj.write_text(json.dumps({'role': role}))
    return root


class Server:
    def __init__(self, root: Path):
        self.root, self.port = root, free_port()
        self.proc = None
        self.log = root.parent / f'server-{self.port}.log'

    def start(self):
        env = dict(os.environ, AJG_NO_BROWSER='1', AJG_TEST_PORT=str(self.port))
        self.proc = subprocess.Popen([str(self.root / 'python' / 'bin' / 'python'), '-B', '-X', 'utf8', '-I', 'app/station/launcher.py'], cwd=self.root,
                                     env=env, stdout=open(self.log, 'w'), stderr=subprocess.STDOUT)
        for _ in range(150):
            try:
                self.get('/_local/station/ping')
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise RuntimeError('server did not start: ' + self.log.read_text()[-800:])
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


def ui(server: Server, steps: list, name: str, workdir: Path, timeout=2400):
    """run a list of steps (ui_pc.js) against the server's page in Chromium; returns {results, errors, external}"""
    sp = workdir / f'{name}.steps.json'
    sp.write_text(json.dumps(steps))
    env = dict(os.environ, PLAYWRIGHT_MODULE=NODE_MODULES)
    p = subprocess.run(['node', str(HERE / 'ui_pc.js'), server.base, str(sp)], capture_output=True, text=True, env=env, timeout=timeout)
    if p.returncode:
        raise RuntimeError('node failed: ' + p.stderr[-800:])
    return json.loads(p.stdout.strip().splitlines()[-1])


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
