"""Build "AJG Tracker test.zip". Standard library + a pip subprocess.
Run: python3 -I build_probe.py
"""
import hashlib, os, shutil, struct, subprocess, sys, urllib.request, zipfile, glob

SRC = os.path.dirname(os.path.abspath(__file__))
BUILD = "/tmp/claude-0/-home-user-Press-Tracker/ec7aac73-d461-552b-aaac-9f8ebc5e7581/scratchpad/probe_build"
PYVER = "3.13.16"
URL = "https://api.nuget.org/v3-flatcontainer/python/%s/python.%s.nupkg" % (PYVER, PYVER)
NAME = "AJG Tracker test"
DROP_DIRS = {"__pycache__", "test", "tests", "idlelib", "tkinter", "ensurepip", "turtledemo", "lib2to3", "site-packages"}
DROP_TOP = {"include", "libs"}  # tools/include, tools/libs (compile-time only)
DROP_FILES = {"turtle.py"}
DROP_DLL = {"_tkinter.pyd", "tcl86t.dll", "tk86t.dll"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def has_authenticode(data):
    """True if the PE has a non-empty certificate table (data directory 4)."""
    if data[:2] != b"MZ":
        return None
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        return None
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    off, size = struct.unpack_from("<II", data, dd + 4 * 8)
    return (off, size) if size else False


def main():
    shutil.rmtree(BUILD, ignore_errors=True)
    dl = os.path.join(BUILD, "download")
    os.makedirs(dl)
    nupkg = os.path.join(dl, "python.%s.nupkg" % PYVER)
    print("Downloading", URL)
    urllib.request.urlretrieve(URL, nupkg)
    nsha = sha256(nupkg)
    print("nupkg sha256:", nsha, "size", os.path.getsize(nupkg))

    root = os.path.join(BUILD, "bundle", NAME)
    pydir = os.path.join(root, "python")
    os.makedirs(pydir)
    with zipfile.ZipFile(nupkg) as z:
        if ".signature.p7s" in z.namelist():
            print("nupkg carries NuGet package signature (.signature.p7s)")
        for info in z.infolist():
            n = info.filename
            if not n.startswith("tools/") or n.endswith("/"):
                continue
            rel = n[len("tools/"):]
            parts = rel.split("/")
            if parts[0] in DROP_TOP or any(p in DROP_DIRS for p in parts[:-1]) or parts[-1] in DROP_FILES or parts[-1] in DROP_DLL:
                continue
            if parts[-1].endswith(".pyc"):
                continue
            dest = os.path.join(pydir, *parts)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with z.open(info) as s, open(dest, "wb") as d:
                shutil.copyfileobj(s, d)
    # signature check
    for exe in ("python.exe", "pythonw.exe", "python313.dll"):
        with open(os.path.join(pydir, exe), "rb") as f:
            print("Authenticode table in %s:" % exe, has_authenticode(f.read()))
    print("python.cat present:", os.path.exists(os.path.join(pydir, "DLLs", "python.cat")))

    # app
    app = os.path.join(root, "app")
    sp = os.path.join(app, "site-packages")
    os.makedirs(sp)
    shutil.copy(os.path.join(SRC, "probe.py"), app)
    whl = os.path.join(BUILD, "wheels")
    subprocess.check_call([sys.executable, "-m", "pip", "download", "--only-binary=:all:", "--platform", "win_amd64",
                           "--python-version", "3.13", "--no-deps", "-d", whl, "openpyxl==3.1.5", "et_xmlfile==2.0.0",
                           "pandas==3.0.5", "numpy==2.5.4", "python_dateutil==4.0.0", "tzdata==2026.6"])
    for w in sorted(glob.glob(os.path.join(whl, "*.whl"))):
        print("wheel", os.path.basename(w), "sha256", sha256(w))
        with zipfile.ZipFile(w) as z:
            for m in z.namelist():
                parts = m.split("/")
                if "tests" in parts[:-1] or ".." in parts or m.startswith("/"):
                    continue   # the packages' own test suites are not needed (fewer files on a network share)
                z.extract(m, sp)
    # text files with CRLF
    for name in ("Start test.cmd", "READ ME FIRST.txt"):
        with open(os.path.join(SRC, name), "rb") as f:
            b = f.read().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        with open(os.path.join(root, name), "wb") as f:
            f.write(b)

    out = os.path.join(BUILD, NAME + ".zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for d, dirs, files in os.walk(root):
            dirs.sort()
            for fn in sorted(files):
                p = os.path.join(d, fn)
                z.write(p, os.path.relpath(p, os.path.dirname(root)))
    print("Wrote", out, os.path.getsize(out), "bytes; sha256", sha256(out))


if __name__ == "__main__":
    main()
