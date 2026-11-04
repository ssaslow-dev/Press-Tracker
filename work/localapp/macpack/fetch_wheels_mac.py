"""fetch_wheels_mac.py: the pinned macOS wheels, hash-checked (same method as ../winpack/fetch_wheels.py, which it reuses). Build machine only.
  python3 -I fetch_wheels_mac.py --arch arm64|x86_64 --cache DIR [--pure-out DIR] [--native-out DIR]
pip refuses a wrong hash; every file is hashed again here; a wheel with compiled code other than numpy and pandas is refused.
--pure-out gets the 8 pure-Python wheels (identical files for both chips and for Windows); --native-out gets numpy and pandas for this chip."""
import argparse, importlib.util, os, re, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('fw', os.path.join(HERE, '..', 'winpack', 'fetch_wheels.py'))
fw = importlib.util.module_from_spec(spec); spec.loader.exec_module(fw)
TAGS = {'arm64': 'macosx_11_0_arm64', 'x86_64': 'macosx_10_13_x86_64'}   # oldest builds: macOS 11 (Apple silicon) / 10.13 (Intel)


def read_req(path):
    fw.REQ = path
    return fw.read_req()


def extract(whl, root):
    with zipfile.ZipFile(whl) as z:
        for i in z.infolist():
            dest = os.path.realpath(os.path.join(root, i.filename))
            if not dest.startswith(os.path.realpath(root) + os.sep):
                sys.exit('unsafe path in ' + whl)
            if re.search(r'(^|/)tests/', i.filename):
                continue
            z.extract(i, root)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arch', choices=sorted(TAGS), required=True)
    ap.add_argument('--cache', required=True)
    ap.add_argument('--pure-out'); ap.add_argument('--native-out')
    a = ap.parse_args()
    req = os.path.join(HERE, f'requirements-mac-{a.arch}.txt')
    pins = read_req(req)
    os.makedirs(a.cache, exist_ok=True)
    subprocess.check_call([sys.executable, '-m', 'pip', 'download', '--require-hashes', '--only-binary=:all:', '--no-deps', '--platform', TAGS[a.arch],
                           '--python-version', '3.13', '--implementation', 'cp', '--abi', 'cp313', '--abi', 'none', '--abi', 'abi3', '-r', req, '-d', a.cache])
    seen = {}
    for fn in sorted(os.listdir(a.cache)):
        if not fn.endswith('.whl'):
            continue
        name, ver = fw.wheel_key(fn)
        if name not in pins:
            sys.exit('unexpected wheel (not pinned): ' + fn)
        got = fw.sha256(os.path.join(a.cache, fn))
        if (ver, got) != pins[name]:
            sys.exit(f'HASH/VERSION MISMATCH {fn}: {ver} {got}')
        with zipfile.ZipFile(os.path.join(a.cache, fn)) as z:
            nat = [i.filename for i in z.infolist() if i.filename.lower().endswith(fw.NATIVE_EXT)]
        if nat and name not in fw.NATIVE_OK:
            sys.exit(f'{fn} holds compiled files outside numpy/pandas: {nat[:3]}')
        if name in fw.NATIVE_OK and TAGS[a.arch] not in fn:
            sys.exit(f'{fn} is not a {TAGS[a.arch]} wheel')
        print('ok  %-52s %s%s' % (fn, got[:12], '  COMPILED' if nat else ''))
        seen[name] = fn
    miss = sorted(set(pins) - set(seen))
    if miss:
        sys.exit('pinned but missing: %s' % miss)
    for out, want in ((a.pure_out, False), (a.native_out, True)):
        if out:
            shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
            for n, fn in seen.items():
                if (n in fw.NATIVE_OK) == want:
                    extract(os.path.join(a.cache, fn), out)
    print('all %d wheels verified (%s)' % (len(seen), a.arch))


if __name__ == '__main__':
    main()
