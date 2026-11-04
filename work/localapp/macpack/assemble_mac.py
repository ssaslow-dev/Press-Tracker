#!/usr/bin/env python3
"""assemble_mac.py: the Mac folder "AJG Tracker" (and a zip), made by running ../app/assemble_app.py (unchanged, imported) with
three Windows-specific steps swapped: the Python (python-build-standalone, both chips), the wheels (macOS) and the start files.
    python3 -I work/localapp/macpack/assemble_mac.py [--out DIR] [--arch both|arm64|x86_64] [--zip] [any other assemble_app.py option]
Layout:  AJG Tracker/  Start Tracker.command  READ ME FIRST.txt  layout.json
           python-arm64/ python-x86_64/   (each: bin/python3.13, lib/python3.13; its site-packages holds ajg.pth)
           app/site-packages (pure Python, shared)  app/native-arm64  app/native-x86_64 (numpy, pandas)  app/... (as on Windows)  data/ (as on Windows)
Run on Python 3.13 (the .pyc files). Internet needed for the Python tarball and the wheels (hash-pinned) unless caches exist."""
import importlib.util, json, os, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('assemble_app', HERE.parent / 'app' / 'assemble_app.py')
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
sys.dont_write_bytecode = True
ARCHS = ['arm64', 'x86_64']


def load(name):
    s = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def chosen(a):
    return ARCHS if a.arch == 'both' else [a.arch]


def build_python(root, a, info):
    P = load('fetch_python_mac')
    info['pythons'] = {}
    for arch in chosen(a):
        tgz, h = P.fetch(arch, str(a.out / '_cache'))
        P.unpack(tgz, root / f'python-{arch}')
        sp = root / f'python-{arch}' / 'lib' / 'python3.13' / 'site-packages'
        (sp / 'ajg.pth').write_text('../../../../app/site-packages\n../../../../app/native-%s\n' % arch, encoding='utf-8')
        info['pythons'][arch] = {'version': P.PYV, 'release': P.TAG, 'tarball_sha256': h, 'source': P.url(arch)}


def build_wheels(root, a, info):
    W = load('fetch_wheels_mac')
    sp = root / 'app' / 'site-packages'
    info['wheels'] = {}
    for n, arch in enumerate(chosen(a)):
        cache = a.out / '_cache' / f'wheels-{arch}'
        A.run([sys.executable, '-I', HERE / 'fetch_wheels_mac.py', '--arch', arch, '--cache', cache, '--native-out', root / 'app' / f'native-{arch}']
              + (['--pure-out', sp] if n == 0 else []))
        info['wheels'][arch] = {p.name: A.sha256(p) for p in sorted(cache.glob('*.whl'))}
    for d in [sp] + [root / 'app' / f'native-{x}' for x in chosen(a)]:
        A.run([sys.executable, '-m', 'compileall', '-q', '-j', '0', '--invalidation-mode', 'unchecked-hash', d])


def top_files(root, a, _orig=A.top_files):
    _orig(root, a)
    for f in ('Start Tracker.cmd', 'start_tracker.sh', 'READ ME FIRST.txt', 'Install update.cmd'):
        (root / f).unlink(missing_ok=True)
    shutil.copy2(HERE / 'Start Tracker.command', root / 'Start Tracker.command')
    shutil.copy2(HERE / 'READ ME FIRST.txt', root / 'READ ME FIRST.txt')
    shutil.copy2(HERE / 'Install update.command', root / 'Install update.command')
    os.chmod(root / 'Start Tracker.command', 0o755)
    os.chmod(root / 'Install update.command', 0o755)
    shutil.copy2(HERE.parent / 'winpack' / 'selfcheck.py', root / 'app' / 'station' / 'selfcheck.py') if (root / 'app' / 'station').is_dir() else None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    a_arch = 'both'
    if '--arch' in argv:
        i = argv.index('--arch'); a_arch = argv[i + 1]; del argv[i:i + 2]
    argv = ['--target', 'linux'] + argv
    # the stand-ins for the Linux test build's venv and wheels are replaced by the Mac ones; nothing in assemble_app.py is edited
    A.build_python_linux = lambda root, a, info: build_python(root, setattr(a, 'arch', a_arch) or a, info)
    A.build_site_packages = lambda root, a, info: build_wheels(root, a, info)
    A.top_files = top_files
    rc = A.main(argv)
    return rc


if __name__ == '__main__':
    sys.exit(main())
