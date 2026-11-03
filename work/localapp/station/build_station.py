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


def vendor_pdf_libs():
    """NEWSBANKPDF-v1: pdf.js (Apache-2.0) and pdf-lib (MIT), pinned in vendor/PINS.json (npm tarball sha512, file sha256). Every file is checked
    here. pdf.js ships as ES modules; the page runs it as plain scripts, so the module syntax is removed exactly as below and each build asserts the
    result: `import.meta.url` (used only in a Node branch) becomes a constant, and the final `export{...}` becomes an assignment to a global."""
    vd = os.path.join(HERE, 'vendor')
    pins = json.load(open(os.path.join(vd, 'PINS.json')))
    raw = {}
    for pk in pins['packages'].values():
        for fn, meta in pk['files'].items():
            b = open(os.path.join(vd, fn), 'rb').read()
            assert sha(b) == meta['sha256'], f'vendor/{fn} does not match PINS.json (rerun vendor/fetch_pdflibs.py)'
            raw[fn] = b.decode('utf-8')

    def classic(src, glob):
        m = re.search(r'export\s*\{([^}]*)\}\s*;?\s*$', src)
        assert m, 'no final export statement'
        pairs = []
        for part in m.group(1).split(','):
            a = part.strip().split(' as ')
            pairs.append((a[-1].strip(), a[0].strip()))
        body = src[:m.start()]
        assert body.count('import.meta') == body.count('import.meta.url'), 'import.meta used other than .url'
        body = body.replace('import.meta.url', '"about:blank"')
        assert not re.search(r'(^|[;}])\s*import\s*[{(*\w"\']', body.replace('import(', '')), 'a static import is left'
        return '"use strict";(function(){' + body + '\n;globalThis.' + glob + '={' + ','.join(f'{k}:{v}' for k, v in pairs) + '};})();'
    js = classic(raw['pdf.min.mjs'], 'pdfjsLib')
    worker = classic(raw['pdf.worker.min.mjs'], 'pdfjsWorker')
    return {'pdfjs': js, 'pdfjs_worker': worker, 'pdflib': raw['pdf-lib.min.js'],
            'info': {k: {'version': v['version'], 'license': v['license'], 'integrity': v['integrity'], 'files': {f: m['sha256'] for f, m in v['files'].items()}} for k, v in pins['packages'].items()}}


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
    nb_ui = open(os.path.join(HERE, 'src', 'newsbank_ui.js'), encoding='utf-8').read()
    nb_parse = open(os.path.join(HERE, 'src', 'nbparse.js'), encoding='utf-8').read()
    nb_scope = open(os.path.join(HERE, 'src', 'newsbank.js'), encoding='utf-8').read()
    pq_parse = open(os.path.join(HERE, 'src', 'pqparse.js'), encoding='utf-8').read()   # PROQUESTPDF-v1
    # PROQUESTPDF-v1 answer 2: the ProQuest -> tracker outlet-name map (data/proquest_outlets.json, built by tools/build_pq_aliases.py), inlined as data
    pq_outlets_raw = open(os.path.join(HERE, 'data', 'proquest_outlets.json'), 'rb').read()
    pq_outlets = json.loads(pq_outlets_raw.decode('utf-8'))
    assert pq_outlets.get('version') == 1 and pq_outlets['clean_rules'] and pq_outlets['key_steps'] and pq_outlets['pairs'], 'proquest_outlets.json is incomplete (rerun tools/build_pq_aliases.py)'
    pq_parse = pq_parse + '\nPQParse.setTable(' + json.dumps(pq_outlets, separators=(',', ':')).replace('</', '<\\/') + ');\n'
    pq_scope = open(os.path.join(HERE, 'src', 'proquest.js'), encoding='utf-8').read()
    pq_ui = open(os.path.join(HERE, 'src', 'proquest_ui.js'), encoding='utf-8').read()
    nb_scope = nb_scope + '\n' + pq_scope          # one text run inside the tracker's scope: NewsBank first, then the ProQuest source object
    st_js = once(st_js, '/*NB_UI*/', nb_ui)
    st_js = once(st_js, '/*PQ_UI*/', pq_ui)
    for t in (st_js, nb_parse, nb_scope, pq_parse):
        assert '</script' not in t
    # UPDATESTATION-v1 follow-up 9: the v64 button's extra passes (RECALLFIX-v1, PODSITE-v1, YTSTATION-v1) read fetchrules.recall. A new for-Update file carries it
    # (make_for_update runs the PC's build_data); this default is the same block built from the repository's reference files, used only for a file that lacks it.
    rs = json.load(open(os.path.join(REPO, 'code', 'recall_sources.json'), encoding='utf-8'))
    em = json.load(open(os.path.join(REPO, 'code', 'ems_ca_outlets.json'), encoding='utf-8'))
    recall_default = dict(rs, ethnic=dict(rs.get('ethnic') or {}, outlets=[[o.get('host'), o.get('language'), o.get('region'), o.get('city'), o.get('name')] for o in (em.get('outlets') or [])]))
    assert recall_default.get('priority') and recall_default.get('youtube', {}).get('channels') and recall_default.get('podcasts'), 'recall_sources.json is incomplete'
    recall_json = json.dumps(recall_default, separators=(',', ':')).replace('</', '<\\/')
    lib = vendor_pdf_libs()
    page = once(page, '<main class="wrap">', '<main class="wrap">\n' + st_html)
    fonts_css, nfonts = inline_fonts_css()
    doc = ('<title>AJG Update Station</title>\n' + page + '\n<style id="station-fonts">\n' + fonts_css + '</style>\n<style id="station-css">\n' + st_css + '</style>\n'
           '<script type="text/plain" id="tracker-src">' + body_esc + '</script>\n<script type="text/plain" id="nb-scope-src">' + nb_scope + '</script>\n'
           '<script type="application/json" id="recall-default">' + recall_json + '</script>\n'
           '<script id="nbparse-js">\n' + nb_parse + '</script>\n'
           '<script id="pqparse-js">\n' + pq_parse + '</script>\n'
           '<script type="text/plain" id="vendor-pdfjs-worker">' + lib['pdfjs_worker'].replace('</script', '<\\/script') + '</script>\n'
           '<script type="text/plain" id="vendor-pdfjs">' + lib['pdfjs'].replace('</script', '<\\/script') + '</script>\n'
           '<script type="text/plain" id="vendor-pdflib">' + lib['pdflib'].replace('</script', '<\\/script') + '</script>\n'
           '<script id="station-js">\n' + st_js + '</script>\n')
    # outside references: none in the shell or the station layer; the tracker JS keeps two it never reaches in the station (listed in README)
    outer = doc.replace(body_esc, '')
    for k in ('pdfjs_worker', 'pdfjs', 'pdflib'):
        outer = outer.replace(lib[k].replace('</script', '<\\/script'), '')   # the vendored libraries keep some URLs in strings and comments; none is fetched (listed below)
    for bad in ('fonts.googleapis', 'fonts.gstatic', 'claude.ai/', 'cdnjs.cloudflare', 'jsdelivr', 'unpkg.com'):
        assert bad not in outer, f'outside reference left in the page: {bad}'
    residual = sorted({m.group(0) for m in re.finditer(r'https://(?:fonts\.googleapis\.com|cdnjs\.cloudflare\.com)[^\s\'"`)]*', body)})
    print('tracker JS keeps (not reachable in the station):', residual)
    vend_urls = sorted({m.group(0) for k in ('pdfjs_worker', 'pdfjs', 'pdflib') for m in re.finditer(r'https?://[^\s\'"`)<>\\]+', lib[k])})
    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, 'index.html')
    open(p, 'w', encoding='utf-8').write(doc)
    info = {'index_html_bytes': len(doc.encode()), 'index_html_sha256': sha(doc.encode()), 'tracker_js_sha256': sha(js), 'tracker_js_parts_bytes': len(js),
            'shell_sha256': sha(shell.encode()), 'vendor': os.path.basename(vendor),
            'pdf_libs': lib['info'], 'vendor_urls_in_strings': vend_urls, 'nb_scope_sha256': sha(nb_scope.encode()), 'nbparse_sha256': sha(nb_parse.encode()), 'pqparse_sha256': sha(pq_parse.encode()), 'proquest_outlets_sha256': sha(pq_outlets_raw), 'proquest_outlets_pairs': len(pq_outlets['pairs']), 'recall_default_sha256': sha(recall_json.encode()), 'recall_default_priority_sites': sum(len(g['sites']) for g in recall_default['priority']['groups']), 'recall_default_youtube_channels': len(recall_default['youtube']['channels']), 'pq_ui_sha256': sha(pq_ui.encode()), 'pq_scope_sha256': sha(pq_scope.encode()), 'nb_ui_sha256': sha(nb_ui.encode()),
            'fonts_woff2_inlined': nfonts, 'fonts_css_sha256': sha(fonts_css.encode()), 'station_css_sha256': sha(st_css.encode()), 'station_html_sha256': sha(st_html.encode()), 'station_js_sha256': sha(st_js.encode())}
    json.dump(info, open(os.path.join(a.out, 'build_info.json'), 'w'), indent=1)
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    main()
