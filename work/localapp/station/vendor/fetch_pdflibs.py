#!/usr/bin/env python3
"""Fetch the two open-source PDF libraries the Update station bundles (NEWSBANKPDF-v1) from the npm registry, once, and pin them.

    python3 -I work/localapp/station/vendor/fetch_pdflibs.py [--check]

pdfjs-dist 4.10.38 (Apache-2.0, Mozilla; reads text and positions) and pdf-lib 1.17.1 (MIT; copies page ranges into new PDFs).
Each npm tarball is checked against the sha512 integrity string npm publishes (PINS.json, taken from registry.npmjs.org) before anything is
read from it; each file kept is then checked against its sha256 in PINS.json. build_station.py re-checks the kept files on every build.
--check only verifies the files already here (no network)."""
import base64, hashlib, io, json, os, sys, tarfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PINS = os.path.join(HERE, 'PINS.json')

PACKAGES = {
    'pdfjs-dist': {'version': '4.10.38', 'license': 'Apache-2.0',
                   'integrity': 'sha512-/Y3fcFrXEAsMjJXeL9J8+ZG9U01LbuWaYypvDW2ycW1jL269L3js3DVBjDJ0Up9Np1uqDXsDrRihHANhZOlwdQ==',
                   'files': {'package/legacy/build/pdf.min.mjs': 'pdf.min.mjs', 'package/legacy/build/pdf.worker.min.mjs': 'pdf.worker.min.mjs',
                             'package/LICENSE': 'LICENSE-pdfjs-dist.txt'}},
    'pdf-lib': {'version': '1.17.1', 'license': 'MIT',
                'integrity': 'sha512-V/mpyJAoTsN4cnP31vc0wfNA1+p20evqqnap0KLoRUN0Yk/p3wN52DOEsL4oBFcLdb76hlpKPtzJIgo67j/XLw==',
                'files': {'package/dist/pdf-lib.min.js': 'pdf-lib.min.js', 'package/LICENSE.md': 'LICENSE-pdf-lib.md'}},
}


def sha(b, alg='sha256'):
    return hashlib.new(alg, b).hexdigest()


def integrity(b):
    return 'sha512-' + base64.b64encode(hashlib.sha512(b).digest()).decode()


def check():
    pins = json.load(open(PINS))
    for name, p in pins['packages'].items():
        for fn, meta in p['files'].items():
            b = open(os.path.join(HERE, fn), 'rb').read()
            assert sha(b) == meta['sha256'], f'{fn} does not match PINS.json'
    print('vendor files match PINS.json')


def fetch():
    out = {'note': 'Pinned by sha512 (npm tarball) and sha256 (kept files). Fetched from registry.npmjs.org.', 'packages': {}}
    for name, spec in PACKAGES.items():
        url = f'https://registry.npmjs.org/{name}/-/{name}-{spec["version"]}.tgz'
        data = urllib.request.urlopen(url, timeout=120).read()
        assert integrity(data) == spec['integrity'], f'{name}: tarball integrity mismatch'
        tf = tarfile.open(fileobj=io.BytesIO(data), mode='r:gz')
        files = {}
        for member, dest in spec['files'].items():
            b = tf.extractfile(member).read()
            open(os.path.join(HERE, dest), 'wb').write(b)
            files[dest] = {'sha256': sha(b), 'bytes': len(b), 'from': member}
        out['packages'][name] = {'version': spec['version'], 'license': spec['license'], 'tarball': url, 'integrity': spec['integrity'], 'files': files}
    json.dump(out, open(PINS, 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    check() if '--check' in sys.argv else fetch()
