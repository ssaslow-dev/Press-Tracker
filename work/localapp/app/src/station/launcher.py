"""launcher.py: what "Start Tracker.cmd" runs.  python -B -X utf8 -I app\\station\\launcher.py

1. Port 8765 busy? If it is this tracker folder's own server, just open the page. If it is anything else, say so and stop
   (the tracker never picks another port: the browser keeps notes and settings under the exact address).
2. Otherwise start the server (127.0.0.1 only), open the page in Edge's app mode (or the default browser), and keep serving
   until the window is closed.
Plain messages only. No network except this PC's own port. AJG_NO_BROWSER=1 skips opening a browser (tests).
"""
from __future__ import annotations

import http.client
import json
import os
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

PORT = int(os.environ.get('AJG_TEST_PORT') or 8765)   # AJG_TEST_PORT is for the tests only; the tracker is always at port 8765
URL = f'http://127.0.0.1:{PORT}/'


def port_in_use(port=PORT) -> bool:
    s = socket.socket()
    s.settimeout(0.7)
    try:
        return s.connect_ex(('127.0.0.1', port)) == 0
    finally:
        s.close()


def who_is_there(port=PORT):
    try:
        c = http.client.HTTPConnection('127.0.0.1', port, timeout=3)
        c.request('GET', '/_local/station/ping', headers={'Host': f'127.0.0.1:{port}'})
        r = c.getresponse()
        if r.status == 200:
            return json.loads(r.read().decode('utf-8'))
    except (OSError, ValueError, http.client.HTTPException):
        pass
    return None


def edge_path():
    for env, rel in (('ProgramFiles(x86)', r'Microsoft\Edge\Application\msedge.exe'), ('ProgramFiles', r'Microsoft\Edge\Application\msedge.exe'),
                     ('LOCALAPPDATA', r'Microsoft\Edge\Application\msedge.exe')):
        base = os.environ.get(env)
        if base and os.path.isfile(os.path.join(base, rel)):
            return os.path.join(base, rel)
    return None


def open_page(url=URL):
    if os.environ.get('AJG_NO_BROWSER') == '1':
        return 'skipped'
    e = edge_path()
    if e:
        try:
            subprocess.Popen([e, f'--app={url}'], close_fds=True)
            return 'edge'
        except OSError:
            pass
    webbrowser.open(url)
    return 'default browser'


def main(argv=None) -> int:
    root = C.ROOT
    if '--check' in (argv or sys.argv[1:]):
        print('root:', root)
        return 0
    if port_in_use():
        who = who_is_there()
        if who and who.get('app') == 'ajg-tracker':
            if who.get('root_id') == __import__('station_server').root_id(root):
                print('The tracker is already running on this PC. Opening it.')
                open_page()
                return 0
            print('Another copy of the AJG Tracker is already running on this PC, from a different folder:\n  %s\n'
                  'Close that one first (close its black window), then start this one again.' % who.get('root'))
            return 3
        print('Port 8765 on this PC is used by another program, so the tracker cannot start.\n'
              'Close that program (or restart the PC) and start the tracker again.')
        return 3
    try:
        import station_server as SS
        srv = SS.StationServer(root, PORT)
    except FileNotFoundError as e:
        print('The tracker page is missing: %s\nThe folder may be incomplete. See READ ME FIRST.txt.' % e)
        return 2
    except OSError as e:
        print('The tracker could not start: %s' % e)
        return 3
    print('AJG Tracker is running at %s' % URL)
    print('Keep this window open while you use the tracker. Close it to stop the tracker.\n')
    how = open_page()
    if how == 'default browser':
        print('(Edge was not found, so the page opened in your usual browser.)')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
