"""fetch_python_mac.py: download the pinned macOS CPython (python-build-standalone) and unpack a trimmed copy. Build machine only.
  python3 -I fetch_python_mac.py --arch arm64|x86_64 --out DIR [--cache DIR]
The tarball's sha256 must equal the pin below (taken from the release's own SHA256SUMS file); otherwise nothing is unpacked.
Unpacked: bin/python3.13 (a single program, links only Apple system libraries), lib/python3.13 (standard library without tests, GUI parts, pip),
LICENSE. Dropped: Tcl/Tk, pip, headers, man pages, idle, symbolic links (a zip then needs none)."""
import argparse, hashlib, os, shutil, sys, tarfile, urllib.request

TAG, PYV = '20261026', '3.13.18'
PINS = {'arm64': ('aarch64', '8392b6ea51d94391befb2c31ebe75463f045d0b69dfcf5e1bb3234e1f5fa3405'),
        'x86_64': ('x86_64', '7412c19d896c99431b74a18a5643e110449a7f9590fbab179c3e5ab27b9aa9e3')}
DROP_DIRS = {'__pycache__', 'test', 'tests', 'idlelib', 'tkinter', 'ensurepip', 'turtledemo', 'lib2to3', 'config-3.13-darwin', 'site-packages'}
DROP_FILES = {'turtle.py', '_tkinter.cpython-313-darwin.so'}


def url(arch):
    return f'https://github.com/astral-sh/python-build-standalone/releases/download/{TAG}/cpython-{PYV}%2B{TAG}-{PINS[arch][0]}-apple-darwin-install_only_stripped.tar.gz'


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def fetch(arch, cache):
    os.makedirs(cache, exist_ok=True)
    dst = os.path.join(cache, f'pbs-{PYV}-{TAG}-{arch}.tar.gz')
    if not os.path.isfile(dst):
        urllib.request.urlretrieve(url(arch), dst)
    got = sha256(dst)
    if got != PINS[arch][1]:
        os.remove(dst)
        sys.exit(f'HASH MISMATCH for {arch} Python: got {got}, pinned {PINS[arch][1]}')
    return dst, got


def unpack(tgz, out):
    out = os.path.realpath(out)
    shutil.rmtree(out, ignore_errors=True)
    n = 0
    with tarfile.open(tgz) as t:
        for m in t:
            if not m.isfile():
                continue
            parts = m.name.split('/')[1:]          # drop the leading "python/"
            if not parts or parts[0] not in ('bin', 'lib') and parts != ['LICENSE.txt']:
                continue
            if parts[0] == 'bin' and parts[-1] != 'python3.13':
                continue
            if parts[0] == 'lib' and (len(parts) < 2 or parts[1] != 'python3.13'):
                continue                            # libpython dylib, Tcl/Tk, pkgconfig: not used (the program has Python built in)
            if any(p in DROP_DIRS for p in parts[:-1]) or parts[-1] in DROP_FILES or parts[-1].endswith('.pyc'):
                continue
            dest = os.path.realpath(os.path.join(out, *parts))
            if not dest.startswith(out + os.sep):
                sys.exit('unsafe path in tarball: ' + m.name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with t.extractfile(m) as s, open(dest, 'wb') as d:
                shutil.copyfileobj(s, d)
            os.chmod(dest, 0o755 if parts[0] == 'bin' or dest.endswith('.so') else 0o644)
            n += 1
    os.makedirs(os.path.join(out, 'lib', 'python3.13', 'site-packages'), exist_ok=True)
    return n


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--arch', choices=sorted(PINS), required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cache', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '_cache'))
    a = ap.parse_args()
    f, h = fetch(a.arch, a.cache)
    print('ok', os.path.basename(f), h[:16], unpack(f, a.out), 'files ->', a.out)
