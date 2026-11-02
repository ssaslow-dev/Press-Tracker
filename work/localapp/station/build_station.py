#!/usr/bin/env python3
"""Build the Update station page (LOCALAPP step 7): ONE html file, ready for the Artifact tool.

    python3 -I work/localapp/station/build_station.py [--out DIR] [--vendor DIR]

Inputs (all read only; nothing under code/, build/, data/ is written):
  code/tracker/NN_*.js      the tracker's own JS, concatenated by `code/apply_all_patches.py --tracker-js` (same bytes as the tracker build)
  vendor/live_*/pipeline/shell.html   the tracker page shell (HTML + CSS), copied from the live tracker (work/localapp/vendor)
  station/src/station.css, station.html, station.js   the station-only layer (the only new code)
Output: OUT/index.html (default station/dist/), plus OUT/build_info.json with the input checksums.
The page holds no stories and no workbook data: step 1 of the page loads the "for Update" file in the browser.
"""
import argparse, base64, hashlib, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VENDOR = os.path.join(REPO, 'work', 'localapp', 'vendor')
FONTS = os.path.join(REPO, 'work', 'localapp', 'fonts', 'files')


def inline_fonts_css():
    """LOCALFONTS-v1: fonts/files/fonts.css with every woff2 as a data: URI, so the published page needs no outside request and no file beside it.
    Every file is checked against FONTS.json (written by fonts/fetch_fonts.py) first."""
    meta = json.load(open(os.path.join(FONTS, 'FONTS.json'), encoding='utf-8'))['files']
    css = open(os.path.join(FONTS, 'fonts.css'), encoding='utf-8').read()
    assert sha(css.encode('utf-8')) == meta['fonts.css']['sha256'], 'fonts.css does not match FONTS.json (rerun fonts/fetch_fonts.py)'

    def uri(m):
        n = m.group(1)
        b = open(os.path.join(FONTS, n), 'rb').read()
        assert sha(b) == meta[n]['sha256'], f'{n} does not match FONTS.json'
        return 'url(data:font/woff2;base64,' + base64.b64encode(b).decode() + ')'
    out, n = re.subn(r'url\(\./([A-Za-z0-9._-]+\.woff2)\)', uri, css)
    assert n == sum(1 for k in meta if k.endswith('.woff2')), (n, 'woff2 files in fonts.css')
    return out, n


def sha(b):
    return hashlib.sha256(b).hexdigest()


def once(s, old, new):
    if s.count(old) != 1:
        raise SystemExit(f'build: expected exactly one {old[:60]!r}, found {s.count(old)}')
    return s.replace(old, new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'dist'))
    ap.add_argument('--vendor', default=None)
    a = ap.parse_args()
    vendor = a.vendor or os.path.join(VENDOR, sorted(d for d in os.listdir(VENDOR) if d.startswith('live_'))[-1])
    # 1. the tracker JS, exactly as the tracker build concatenates it
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, 'tracker.js')
        r = subprocess.run([sys.executable, '-I', os.path.join(REPO, 'code', 'apply_all_patches.py'), '--root', REPO, '--tracker-js', out],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit('apply_all_patches --tracker-js failed:\n' + r.stdout + r.stderr)
        js = open(out, 'rb').read()
    js_s = js.decode('utf-8')
    assert js_s.startswith('<script>') and js_s.rstrip().endswith('</html>'), 'unexpected tracker JS shape'
    body = js_s[len('<script>'):js_s.rindex('</script>')]
    for need in ('initClips();', 'runAll', 'function drawUpd'):
        assert need in body, need
    body_esc = body.replace('</script', '<\\/script')
    # 2. the shell: body content only (the Artifact tool adds the document skeleton)
    shell = open(os.path.join(vendor, 'pipeline', 'shell.html'), encoding='utf-8').read()
    i, j = shell.index('<body>') + len('<body>'), shell.rindex('</body>')
    page = shell[i:j]
    page = re.sub(r'<title>[^<]*</title>', '', page, count=1).strip()
    # ACCOUNT-NEUTRAL-v1 (UPDATESTATION-v1 follow-up 6): no outside code or fonts. The shell's Google Fonts links go; the two fonts the links
    # asked for (Roboto Slab, Public Sans) come back as data: URIs in a style block (LOCALFONTS-v1), so the look is the tracker's own.
    page, n = re.subn(r'<link rel="(?:preconnect|stylesheet)"[^>]*fonts\.g[^>]*>\s*', '', page)
    assert n == 3, f'expected 3 font links, removed {n}'
    page = once(page, '<script id="data" type="application/json">[]</script>', '<script id="data" type="application/json">[]</script>')
    tail = '<script>\n</script>'
    assert page.rstrip().endswith(tail), 'shell does not end with the empty main <script>'
    page = page.rstrip()[:-len(tail)].rstrip()
    page = once(page, 'Press coverage<br>tracker', 'Update<br>station')
    st_html = open(os.path.join(HERE, 'src', 'station.html'), encoding='utf-8').read()
    st_css = open(os.path.join(HERE, 'src', 'station.css'), encoding='utf-8').read()
    st_js = open(os.path.join(HERE, 'src', 'station.js'), encoding='utf-8').read()
    assert '</script' not in st_js
    page = once(page, '<main class="wrap">', '<main class="wrap">\n' + st_html)
    fonts_css, nfonts = inline_fonts_css()
    doc = ('<title>AJG Update Station</title>\n' + page + '\n<style id="station-fonts">\n' + fonts_css + '</style>\n<style id="station-css">\n' + st_css + '</style>\n'
           '<script type="text/plain" id="tracker-src">' + body_esc + '</script>\n<script id="station-js">\n' + st_js + '</script>\n')
    # outside references: none in the shell or the station layer; the tracker JS keeps two it never reaches in the station (listed in README)
    outer = doc.replace(body_esc, '')
    for bad in ('fonts.googleapis', 'fonts.gstatic', 'claude.ai/', 'cdnjs.cloudflare', 'jsdelivr', 'unpkg.com'):
        assert bad not in outer, f'outside reference left in the page: {bad}'
    residual = sorted({m.group(0) for m in re.finditer(r'https://(?:fonts\.googleapis\.com|cdnjs\.cloudflare\.com)[^\s\'"`)]*', body)})
    print('tracker JS keeps (not reachable in the station):', residual)
    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, 'index.html')
    open(p, 'w', encoding='utf-8').write(doc)
    info = {'index_html_bytes': len(doc.encode()), 'index_html_sha256': sha(doc.encode()), 'tracker_js_sha256': sha(js), 'tracker_js_parts_bytes': len(js),
            'shell_sha256': sha(shell.encode()), 'vendor': os.path.basename(vendor),
            'fonts_woff2_inlined': nfonts, 'fonts_css_sha256': sha(fonts_css.encode()), 'station_css_sha256': sha(st_css.encode()), 'station_html_sha256': sha(st_html.encode()), 'station_js_sha256': sha(st_js.encode())}
    json.dump(info, open(os.path.join(a.out, 'build_info.json'), 'w'), indent=1)
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    main()
