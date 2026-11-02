#!/usr/bin/env python3
"""Fetch the tracker's two fonts from the pinned @fontsource npm packages and write work/localapp/fonts/files/.

    python3 -I work/localapp/fonts/fetch_fonts.py [--out DIR] [--cache DIR] [--check]

Why: the tracker page and its saved-copy viewer asked fonts.googleapis.com / fonts.gstatic.com for "Roboto Slab" and "Public Sans".
The PC tracker (GOVIT-v1) must make no outside request, and the Update station needs the fonts inline. Both use these files.

What it does
  1. downloads the two pinned tarballs from registry.npmjs.org (the only network use; skipped when the file is already in --cache);
  2. checks each tarball's sha512 against the npm "dist.integrity" recorded below (a mismatch stops the run, nothing is written);
  3. reads exactly the wanted files out of the tarball by name (nothing is extracted to disk by path, no extractall): the latin and latin-ext
     woff2 files, each package's LICENSE, and the package's own CSS for each weight (for the @font-face unicode-range);
  4. writes OUT/fonts.css (same family names and unicode-range as fontsource; woff2 only), OUT/*.woff2, one LICENSE-<package> per package,
     and OUT/FONTS.json (versions, integrity, sha256 of every file).
Running it again with the same pins gives the same bytes. Italic: only Public Sans 400 italic, because the saved-copy viewer's old Google
URL asked for it (ital,wght@...;1,400). Everything else is normal style.

Licences (as shipped in the packages): Public Sans is SIL OFL 1.1; Roboto Slab is Apache 2.0 (the npm package says so, and so does Google Fonts).
Both texts ship next to the fonts.
"""
import argparse, base64, hashlib, io, json, os, re, sys, tarfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

PACKAGES = {
    'roboto-slab': {
        'version': '5.3.0',
        'integrity': 'sha512-nrl4sOt5OIoMV3VecGVOnNAADU/8vz6+CLtLr4cCAf106hVtSLCTObPN8Z2KdZ03U01UDvgIp3hsu2TX3jen6w==',
        'family': 'Roboto Slab',
        'faces': [(w, 'normal') for w in (500, 600, 700, 800)],
        'license': 'Apache-2.0',
    },
    'public-sans': {
        'version': '5.3.0',
        'integrity': 'sha512-kjODI0S3zdv0mBYCIQ8TbBayaiqszpc2UbhJiO3bjIqVVXzcWfHSt2o3WBCLOY3juaGaQoy4MoWCcgmfI5hCuA==',
        'family': 'Public Sans',
        'faces': [(w, 'normal') for w in (400, 500, 600, 700)] + [(400, 'italic')],
        'license': 'OFL-1.1',
    },
}
SUBSETS = ('latin', 'latin-ext')
TARBALL = 'https://registry.npmjs.org/@fontsource/{n}/-/{n}-{v}.tgz'


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def get_tarball(name, spec, cache):
    fn = f'{name}-{spec["version"]}.tgz'
    p = os.path.join(cache, fn) if cache else None
    if p and os.path.isfile(p):
        data = open(p, 'rb').read()
    else:
        url = TARBALL.format(n=name, v=spec['version'])
        print('download', url)
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
        if p:
            os.makedirs(cache, exist_ok=True)
            open(p, 'wb').write(data)
    got = 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode()
    if got != spec['integrity']:
        raise SystemExit(f'{fn}: integrity mismatch\n  expected {spec["integrity"]}\n  got      {got}')
    return data


def face_blocks(css):
    """[(comment_name, block_text)] of a fontsource css file"""
    return [(m.group(1), m.group(0)) for m in re.finditer(r'/\* ([^*]+?) \*/\s*@font-face\s*\{[^}]*\}', css)]


def build(cache, out):
    files, css_parts, info = {}, [], {'note': 'written by fetch_fonts.py', 'packages': {}}
    for name, spec in PACKAGES.items():
        tgz = get_tarball(name, spec, cache)
        tf = tarfile.open(fileobj=io.BytesIO(tgz), mode='r:gz')
        names = set(tf.getnames())

        def member(n):
            if n not in names:
                raise SystemExit(f'{name}: {n} not in the tarball')
            return tf.extractfile(n).read()
        files[f'LICENSE-{name}'] = member('package/LICENSE')
        css_parts.append(f'/* {spec["family"]}: @fontsource/{name} {spec["version"]} ({spec["license"]}; text in LICENSE-{name}) */')
        used = []
        for w, style in spec['faces']:
            src = member(f'package/{w}{"-italic" if style == "italic" else ""}.css').decode('utf-8')
            blocks = dict(face_blocks(src))
            for sub in SUBSETS:
                key = f'{name}-{sub}-{w}-{style}'
                if key not in blocks:
                    raise SystemExit(f'{name}: no @font-face {key} in the package css')
                b = blocks[key]
                fam = re.search(r"font-family: '([^']+)'", b).group(1)
                assert fam == spec['family'], (fam, key)
                assert f'font-weight: {w};' in b and f'font-style: {style};' in b, key
                rng = re.search(r'unicode-range: ([^;]+);', b).group(1)
                wf = f'{key}.woff2'
                files[wf] = member(f'package/files/{wf}')
                css_parts.append(f'/* {key} */\n@font-face {{\n  font-family: \'{fam}\';\n  font-style: {style};\n  font-display: swap;\n  font-weight: {w};\n'
                                 f'  src: url(./{wf}) format(\'woff2\');\n  unicode-range: {rng};\n}}')
                used.append(wf)
        info['packages'][name] = {'version': spec['version'], 'integrity': spec['integrity'], 'license': spec['license'], 'tarball_bytes': len(tgz), 'woff2': used}
    files['fonts.css'] = ('\n'.join(css_parts) + '\n').encode('utf-8')
    info['files'] = {n: {'bytes': len(b), 'sha256': sha256(b)} for n, b in sorted(files.items())}
    files['FONTS.json'] = (json.dumps(info, indent=1) + '\n').encode('utf-8')
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'files'))
    ap.add_argument('--cache', default=None, help='folder for the downloaded tarballs (default: none, downloaded each time)')
    ap.add_argument('--check', action='store_true', help='do not write; fail if OUT differs from what the pinned packages give')
    a = ap.parse_args()
    files = build(a.cache, a.out)
    if a.check:
        bad = [n for n, b in files.items() if not os.path.isfile(os.path.join(a.out, n)) or open(os.path.join(a.out, n), 'rb').read() != b]
        if bad:
            raise SystemExit('differs: ' + ', '.join(bad))
        print('ok:', len(files), 'files identical')
        return
    os.makedirs(a.out, exist_ok=True)
    for n, b in files.items():
        open(os.path.join(a.out, n), 'wb').write(b)
    tot = sum(len(b) for n, b in files.items() if n.endswith('.woff2'))
    print(f'{len(files)} files in {a.out}; woff2 total {tot} bytes')


if __name__ == '__main__':
    main()
