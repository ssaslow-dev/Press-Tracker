"""Download the pinned Windows wheels into a cache folder and verify every hash. Run on the BUILD machine (any OS with pip and internet).
  python3 -I fetch_wheels.py [--cache DIR] [--extract SITE_PACKAGES_DIR]
Steps: (1) pip download --require-hashes for win_amd64 / cp313 (pip itself refuses a wrong hash); (2) re-hash each file here against
requirements-win.txt and refuse extra or missing files; (3) report every native file (.pyd/.dll/.exe) inside each wheel and refuse any
wheel outside the allowlist (numpy, pandas); (4) with --extract, unzip into site-packages (path-checked), which is what the portable
folder ships (same see winpack/README.md). Standard library + pip only."""
import argparse, hashlib, os, re, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REQ = os.path.join(HERE, 'requirements-win.txt')
NATIVE_OK = {'numpy', 'pandas'}   # the only wheels allowed to contain compiled code; GOVIT-v1 README lists them for IT
NATIVE_EXT = ('.pyd', '.dll', '.exe', '.so', '.dylib')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read_req():
    pins = {}
    for line in open(REQ, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^([A-Za-z0-9_.-]+)==(\S+)\s+--hash=sha256:([0-9a-f]{64})$', line)
        if not m:
            sys.exit('bad line in requirements-win.txt: ' + line)
        pins[re.sub(r'[-_.]+', '_', m.group(1)).lower()] = (m.group(2), m.group(3))
    return pins


def wheel_key(fn):
    return re.sub(r'[-_.]+', '_', fn.split('-')[0]).lower(), fn.split('-')[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache', default=os.path.join(HERE, 'wheel_cache'))
    ap.add_argument('--extract', help='unzip all wheels here (site-packages of the portable folder)')
    ap.add_argument('--keep-tests', action='store_true', help='keep the packages\' own tests/ folders (default: leave them out, ~1600 files)')
    ap.add_argument('--no-precompile', action='store_true', help='skip the .pyc step')
    a = ap.parse_args()
    pins = read_req()
    os.makedirs(a.cache, exist_ok=True)
    subprocess.check_call([sys.executable, '-m', 'pip', 'download', '--require-hashes', '--only-binary=:all:', '--no-deps',
                           '--platform', 'win_amd64', '--python-version', '3.13', '--implementation', 'cp', '--abi', 'cp313',
                           '--abi', 'none', '--abi', 'abi3',
                           '-r', REQ, '-d', a.cache])
    seen = {}
    for fn in sorted(os.listdir(a.cache)):
        if not fn.endswith('.whl'):
            continue
        name, ver = wheel_key(fn)
        if name not in pins:
            sys.exit('unexpected wheel in cache (not pinned): ' + fn)
        want_ver, want_sha = pins[name]
        got = sha256(os.path.join(a.cache, fn))
        if ver != want_ver or got != want_sha:
            sys.exit('HASH/VERSION MISMATCH %s: got %s %s, pinned %s %s' % (fn, ver, got, want_ver, want_sha))
        seen[name] = fn
        with zipfile.ZipFile(os.path.join(a.cache, fn)) as z:
            nat = [i.filename for i in z.infolist() if i.filename.lower().endswith(NATIVE_EXT)]
        flag = '' if not nat else ('  NATIVE x%d' % len(nat))
        print('ok  %-48s %s%s' % (fn, got[:16], flag))
        if nat and name not in NATIVE_OK:
            sys.exit('wheel %s holds native files outside the allowlist: %s' % (fn, nat[:5]))
    missing = sorted(set(pins) - set(seen))
    if missing:
        sys.exit('pinned but not downloaded: %s' % missing)
    print('all %d wheels verified' % len(seen))
    if a.extract:
        root = os.path.realpath(a.extract)
        shutil.rmtree(root, ignore_errors=True)
        os.makedirs(root)
        for fn in seen.values():
            with zipfile.ZipFile(os.path.join(a.cache, fn)) as z:
                for info in z.infolist():
                    dest = os.path.realpath(os.path.join(root, info.filename))
                    if not (dest == root or dest.startswith(root + os.sep)):
                        sys.exit('unsafe path in %s: %s' % (fn, info.filename))
                for info in z.infolist():
                    if not a.keep_tests and re.search(r'(^|/)tests/', info.filename):
                        continue   # MULTIPC-v1: fewer small files on a network share
                    z.extract(info, root)
        n = sum(len(f) for _, _, f in os.walk(root))
        print('extracted to', root, '-', n, 'files')
        if not a.no_precompile:
            # MULTIPC-v1: the shared folder is read-mostly; run with -B and ship the .pyc made here. unchecked-hash = never
            # re-validated against the source (no stat per import over SMB). Needs the same Python minor version as the PC (3.13).
            if sys.version_info[:2] != (3, 13):
                print('WARNING: build Python is %d.%d, not 3.13: .pyc step skipped (run this on 3.13)' % sys.version_info[:2])
            else:
                subprocess.check_call([sys.executable, '-m', 'compileall', '-q', '-j', '0', '--invalidation-mode', 'unchecked-hash', root])
                print('precompiled (unchecked-hash); start Python with -B')


if __name__ == '__main__':
    main()
