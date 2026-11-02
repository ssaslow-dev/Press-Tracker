#!/usr/bin/env python3
"""Fetch the exact font files Google Fonts serves to the OLD tracker and write work/localapp/fonts/google/ (SAMELOOK-v2).

    python3 -I work/localapp/fonts/fetch_google_fonts.py [--out DIR]      fetch (needs the internet once), write, print sha256s
    python3 -I work/localapp/fonts/fetch_google_fonts.py --check [--out DIR]   no network: the files on disk against FONTS_GOOGLE.json

Why: the old tracker asks fonts.googleapis.com for two stylesheets, and Google answers with VARIABLE woff2 files (one file per script subset, every
weight in it). The first PC build used the static fontsource files instead (fonts/fetch_fonts.py): the same design, but other font versions,
so text measured 0.02 px differently and anti-aliased differently (0.7 percent of the pixels on the Home page). Same files, same pixels: this
folder holds the very files Google serves, under their own unicode-range rules, for exactly the two requests the old tracker makes.

    page.css    what the tracker page asks for     Roboto Slab 500-800, Public Sans 400-700, normal style only (the page never asks for italic;
                                                   a browser draws its own slanted italic, and that is the old look)
    viewer.css  what the saved-copy frame asks for Roboto Slab 600 and 700, Public Sans 400 and 600, Public Sans 400 italic (and nothing else:
                                                   a bold word in a saved copy uses the 600 face, as in the old tracker)

The CSS is Google's own text with each gstatic address replaced by the local file name. Files are named <family>-<subset>-<style>-<v>.woff2.
Licences (Public Sans: SIL OFL 1.1; Roboto Slab: Apache 2.0) are copied from fonts/files. The user agent below is Chromium's (Edge sends the
same engine string with "Edg/"); Google's answer depends on it only for the file format.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
SHEETS = {
    'page.css': 'https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&display=swap',
    'viewer.css': 'https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@600;700&family=Public+Sans:ital,wght@0,400;0,600;1,400&display=swap',
}
GSTATIC = re.compile(r'https://fonts\.gstatic\.com/s/[^)\s]+\.woff2')
BLOCK = re.compile(r'/\* ([a-z-]+) \*/\s*@font-face \{([^}]*)\}')


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if binary else r.read().decode('utf-8')


def local_name(family, subset, style, url):
    v = re.search(r'/(v\d+)/', url)
    return f"{family.lower().replace(' ', '-')}-{subset}-{style}-{v.group(1) if v else 'v0'}-{url.rsplit('/', 1)[1][:-6][-8:]}"


def build(out):
    os.makedirs(out, exist_ok=True)
    files, sheets = {}, {}
    for name, url in SHEETS.items():
        css = get(url)
        sheets[name] = {'url': url, 'google_css_sha256': sha256(css.encode('utf-8'))}

        def face(m):
            subset, body = m.group(1), m.group(2)
            fam = re.search(r"font-family: '([^']+)'", body).group(1)
            sty = re.search(r'font-style: (\w+)', body).group(1)
            u = GSTATIC.search(body).group(0)
            fn = local_name(fam, subset, sty, u)
            if fn not in files:
                data = get(u, True)
                files[fn] = {'url': u, 'sha256': sha256(data), 'bytes': len(data)}
                with open(os.path.join(out, fn + '.woff2'), 'wb') as f:
                    f.write(data)
            return m.group(0).replace(u, './' + fn + '.woff2')
        local = BLOCK.sub(face, css)
        assert 'gstatic' not in local, 'an address was not rewritten'
        with open(os.path.join(out, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'/* SAMELOOK-v2: Google Fonts css2 answer for\n   {url}\n   addresses replaced by the local files (fonts/fetch_google_fonts.py) */\n' + local)
        sheets[name]['sha256'] = sha256(open(os.path.join(out, name), 'rb').read())
    for lic in ('LICENSE-roboto-slab', 'LICENSE-public-sans'):
        shutil.copy2(os.path.join(HERE, 'files', lic), os.path.join(out, lic))
    meta = {'note': 'written by fetch_google_fonts.py', 'user_agent': UA, 'sheets': sheets, 'files': {k + '.woff2': v for k, v in sorted(files.items())},
            'licenses': {lic: sha256(open(os.path.join(out, lic), 'rb').read()) for lic in ('LICENSE-roboto-slab', 'LICENSE-public-sans')}}
    with open(os.path.join(out, 'FONTS_GOOGLE.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(meta, f, indent=1)
        f.write('\n')
    return meta


def check(out):
    meta = json.load(open(os.path.join(out, 'FONTS_GOOGLE.json'), encoding='utf-8'))
    bad = []
    for fn, m in meta['files'].items():
        p = os.path.join(out, fn)
        if not os.path.isfile(p) or sha256(open(p, 'rb').read()) != m['sha256']:
            bad.append(fn)
    for name, m in meta['sheets'].items():
        p = os.path.join(out, name)
        if not os.path.isfile(p) or sha256(open(p, 'rb').read()) != m['sha256']:
            bad.append(name)
        else:
            for ref in re.findall(r'url\(\./([^)]+)\)', open(p, encoding='utf-8').read()):
                if ref not in meta['files']:
                    bad.append(name + ' -> ' + ref)
    for lic, h in meta['licenses'].items():
        p = os.path.join(out, lic)
        if not os.path.isfile(p) or sha256(open(p, 'rb').read()) != h:
            bad.append(lic)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'google'))
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    if a.check:
        bad = check(a.out)
        print('OK' if not bad else 'MISMATCH: ' + ', '.join(bad))
        return 1 if bad else 0
    meta = build(a.out)
    print(f"{len(meta['files'])} font files, {sum(m['bytes'] for m in meta['files'].values())} bytes, 2 stylesheets -> {a.out}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
