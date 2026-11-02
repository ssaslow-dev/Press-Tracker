"""AJG Tracker "does it run here?" probe. Standard library only (except the openpyxl test)."""
import sys, os, platform, socket, threading, time, json, html, shutil, traceback, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site-packages")
MAX_SECONDS = 15 * 60


def check(name, fn, required=False):
    try:
        ok, detail = fn()
    except Exception as e:  # never let one check kill the run
        ok, detail = False, "%s: %s" % (type(e).__name__, e)
    return {"name": name, "ok": ok, "detail": detail, "required": required}


def c_write():
    p = os.path.join(HERE, "_write_test.tmp")
    with open(p, "w") as f:
        f.write("ok")
    with open(p) as f:
        assert f.read() == "ok"
    os.remove(p)
    return True, "wrote and removed a file in " + HERE


def c_openpyxl():
    if SITE not in sys.path:
        sys.path.insert(0, SITE)
    import openpyxl
    return True, "openpyxl %s from %s" % (openpyxl.__version__, os.path.dirname(openpyxl.__file__))


def c_xlsx():
    import openpyxl
    tmp = os.path.join(HERE, "_tmp_xlsx")
    out = os.path.join(HERE, "_test_output")
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    p = os.path.join(tmp, "probe_test.xlsx")
    wb = openpyxl.Workbook()
    wb.active["A1"] = "hello"
    wb.active["B2"] = 42
    wb.save(p)
    wb2 = openpyxl.load_workbook(p)
    ws = wb2.active
    assert ws["A1"].value == "hello" and ws["B2"].value == 42, "values did not round-trip"
    wb2.close()
    dest = os.path.join(out, "probe_test.xlsx")
    if os.path.exists(dest):
        dest = os.path.join(out, "probe_test_%d.xlsx" % int(time.time()))
    shutil.move(p, dest)
    try:
        os.rmdir(tmp)
    except OSError:
        pass
    return True, "created, saved, re-read and moved to " + dest


def c_bind():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return True, "bound 127.0.0.1 on port %d" % port


def c_internet():
    import urllib.request
    try:
        with urllib.request.urlopen("https://www.example.com", timeout=5) as r:
            return True, "HTTPS GET www.example.com -> HTTP %s" % r.status
    except Exception as e:
        return False, "no internet or blocked (%s: %s)" % (type(e).__name__, e)


def find_edge():
    cands = []
    for var in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            cands.append(os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"))
    cands += [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def c_edge():
    e = find_edge()
    return (e is not None), (e or "msedge.exe not found at the usual paths (will use the default browser)")


def run_checks():
    results = [
        check("Write a file in this folder", c_write, True),
        check("Load openpyxl from app\\site-packages", c_openpyxl, True),
        check("Create and read an .xlsx", c_xlsx, True),
        check("Open a local port (127.0.0.1)", c_bind, True),
        check("Outbound internet (info only)", c_internet),
        check("Microsoft Edge found (info only)", c_edge),
    ]
    return results


def build_report(results):
    lines = ["AJG Tracker test report",
             "Time: " + datetime.datetime.now().isoformat(timespec="seconds"),
             "Python: " + sys.version.replace("\n", " "),
             "Executable: " + sys.executable,
             "Windows/OS: " + platform.platform(),
             "Machine: " + platform.machine(),
             "Folder: " + HERE,
             ""]
    for r in results:
        lines.append("[%s] %s%s - %s" % ("OK" if r["ok"] else "FAIL", r["name"],
                                          " (required)" if r["required"] else "", r["detail"]))
    return "\n".join(lines)


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>AJG Tracker test</title>
<style>body{font-family:Segoe UI,Arial,sans-serif;max-width:900px;margin:30px auto;padding:0 16px}
h1{font-size:56px;margin:0 0 8px}.good{color:#176b2c}.bad{color:#a33a00}
pre{background:#f4f4f4;border:1px solid #ccc;padding:12px;white-space:pre-wrap;word-break:break-word}
button{font-size:18px;padding:8px 18px}</style></head><body>
<h1 class="%(cls)s">%(head)s</h1><p>%(sub)s</p>%(failed)s
<p><button id="b" onclick="c()">Copy report</button> <span id="m"></span></p>
<pre id="r">%(report)s</pre>
<script>function c(){var t=document.getElementById('r').innerText,m=document.getElementById('m');
function ok(){m.textContent='Copied.'}
function fb(){var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();
try{document.execCommand('copy');ok()}catch(e){m.textContent='Select the text below and press Ctrl+C.'}document.body.removeChild(a)}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(ok,fb)}else{fb()}}</script>
</body></html>"""


def render(results, report):
    bad = [r for r in results if r["required"] and not r["ok"]]
    if not bad:
        head, cls, sub, failed = "It works", "good", "Everything required passed on this PC.", ""
    else:
        head, cls, sub = "Partly works", "bad", "These required checks failed:"
        failed = "<ul>" + "".join("<li><b>%s</b>: %s</li>" % (html.escape(r["name"]), html.escape(r["detail"])) for r in bad) + "</ul>"
    return (PAGE % dict(cls=cls, head=head, sub=sub, failed=failed, report=html.escape(report))).encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    results = run_checks()
    report = build_report(results)
    body = render(results, report)

    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] not in ("/", "/index.html"):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *x):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    url = "http://127.0.0.1:%d/" % port
    report += "\nServer: started at %s" % url
    body = render(results, report)  # H reads the closure variable at request time

    try:
        with open(os.path.join(HERE, "probe_report.txt"), "w", encoding="utf-8") as f:
            f.write(report + "\n")
    except Exception as e:
        print("Could not write probe_report.txt: %s" % e)

    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    print(report)
    print("\nPage address: " + url)

    if a.selftest:
        import urllib.request
        with urllib.request.urlopen(url, timeout=5) as r:
            page = r.read().decode("utf-8")
        print("SELFTEST fetched %d bytes; heading ok=%s" % (len(page), ("It works" in page) or ("Partly works" in page)))
        srv.shutdown()
        return 0

    if not a.no_browser:
        opened = False
        edge = find_edge()
        if edge:
            try:
                import subprocess
                subprocess.Popen([edge, "--app=" + url])
                opened = True
            except Exception as e:
                print("Could not start Edge: %s" % e)
        if not opened:
            try:
                import webbrowser
                opened = webbrowser.open(url)
            except Exception as e:
                print("Could not open a browser: %s" % e)
        if not opened:
            print("Could not open a browser automatically. Type the page address above into a browser.")

    print("\nClose this window to stop.")
    try:
        end = time.time() + MAX_SECONDS
        while time.time() < end:
            time.sleep(1)
        print("15 minutes passed; stopping.")
    except KeyboardInterrupt:
        pass
    srv.shutdown()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:
        traceback.print_exc()
        sys.exit(1)
