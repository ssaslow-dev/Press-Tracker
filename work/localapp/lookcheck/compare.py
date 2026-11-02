"""Compare two lookcheck captures (pixels, computed styles, resolved faces).
    python3 -I compare.py --a DIR/1440x900/ref --b DIR/1440x900/pc --out DIR/1440x900/diff [--only a,b] [--json results.json]
Pixels: both screenshots get the recorded-exception rectangles painted black (hidden buttons in the reference, the Tracker files button on the PC),
then every pixel that differs in any channel counts (no tolerance). Styles: every visible element matched by DOM path; every property compared as text
(boxes to 0.02 px). Faces: Chromium's own answer to "which font file drew this text" per text-bearing element."""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

BOX = ('x', 'y', 'w', 'h')
SKIP = {'k', 'tag', 't', '__text'}
# The masthead row is a grid (logo | spacer | buttons). The recorded exception hides two of the buttons, so the spacer grows and the button group shrinks by the
# same amount; the buttons that remain (Spreadsheet, Manage) keep their exact place (right-aligned), which this check proves by finding no other difference.
REFLOW = re.compile(r'^html:0>body:1>header:0>div:1>div:0>div:\d+$')
REFLOW_PROPS = {'x', 'w', 'width'}


def load_meta(d, n):
    p = Path(d) / (n + '.meta.json')
    return json.loads(p.read_text()) if p.is_file() else None


def pixel_diff(a_png, b_png, masks, out_png):
    A, B = Image.open(a_png).convert('RGB'), Image.open(b_png).convert('RGB')
    res = {'a_size': A.size, 'b_size': B.size}
    W, H = max(A.width, B.width), max(A.height, B.height)
    ca, cb = Image.new('RGB', (W, H), (255, 0, 255)), Image.new('RGB', (W, H), (255, 0, 255))
    ca.paste(A, (0, 0)); cb.paste(B, (0, 0))
    a, b = np.array(ca), np.array(cb)
    for m in masks:
        pad = 40 if m.get('fixed') else 1       # the Tracker files button casts a shadow around itself
        x0, y0 = max(0, int(m['x']) - pad), max(0, int(m['y']) - pad)
        x1, y1 = min(W, int(m['x'] + m['w']) + pad + 1), min(H, int(m['y'] + m['h']) + pad + 1)
        a[y0:y1, x0:x1] = 0
        b[y0:y1, x0:x1] = 0
    d = (a != b).any(axis=2)
    n = int(d.sum())
    res['diff_px'], res['total_px'], res['pct'] = n, W * H, (100.0 * n / (W * H))
    res['maxdelta'] = int(np.abs(a.astype(np.int16) - b.astype(np.int16)).max()) if n else 0
    res['n_over_24'] = int((np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2) > 24).sum()) if n else 0
    res['size_equal'] = A.size == B.size
    if n:
        ys, xs = np.nonzero(d)
        res['bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        rows = np.nonzero(d.any(axis=1))[0]
        bands, s = [], rows[0]
        for i in range(1, len(rows)):
            if rows[i] - rows[i - 1] > 12:
                bands.append((int(s), int(rows[i - 1])))
                s = rows[i]
        bands.append((int(s), int(rows[-1])))
        res['bands'] = [(y0, y1, int(np.nonzero(d[y0:y1 + 1].any(axis=0))[0].min()), int(np.nonzero(d[y0:y1 + 1].any(axis=0))[0].max()), int(d[y0:y1 + 1].sum())) for y0, y1 in bands[:12]]
        res['nbands'] = len(bands)
        dim = (a.astype(np.float32) * 0.35 + 255 * 0.65).astype(np.uint8)
        dim[d] = (255, 0, 0)
        Image.fromarray(dim).save(out_png)
        # side by side crop of the first band, for the eye
        y0, y1 = max(0, bands[0][0] - 40), min(H, bands[0][1] + 40)   # the first band, both sides
        sb = Image.new('RGB', (W * 2 + 10, y1 - y0), (0, 0, 0))
        sb.paste(Image.fromarray(a[y0:y1]), (0, 0)); sb.paste(Image.fromarray(b[y0:y1]), (W + 10, 0))
        sb.save(str(out_png).replace('.diff.png', '.side.png'))
    return res


def style_diff(a_json, b_json):
    A = {r['k']: r for r in json.loads(Path(a_json).read_text())}
    B = {r['k']: r for r in json.loads(Path(b_json).read_text())}
    res = {'n_a': len(A), 'n_b': len(B), 'only_a': [], 'only_b': [], 'props': Counter(), 'examples': defaultdict(list), 'elements_diff': 0, 'reflow': []}
    for k in A:
        if k not in B:
            res['only_a'].append((k, A[k]['t']))
    for k in B:
        if k not in A:
            res['only_b'].append((k, B[k]['t']))
    for k, ra in A.items():
        rb = B.get(k)
        if not rb:
            continue
        bad = False
        for p in ra:
            if p in SKIP:
                continue
            va, vb = ra[p], rb.get(p)
            if p in BOX:
                same = abs(va - vb) <= 0.02 if isinstance(vb, (int, float)) else False
            else:
                same = va == vb
            if not same and REFLOW.match(k) and p in REFLOW_PROPS:
                res['reflow'].append((k[-24:], p, va, vb))
                continue
            if not same:
                bad = True
                res['props'][p] += 1
                if len(res['examples'][p]) < 4:
                    res['examples'][p].append((k[-90:], ra['t'], va, vb))
        res['elements_diff'] += bad
    return res


def face_diff(a_meta, b_meta):
    fa, fb = a_meta.get('faces', []), b_meta.get('faces', [])
    res = {'n_a': len(fa), 'n_b': len(fb), 'diff': 0, 'examples': [], 'kinds_a': Counter(), 'kinds_b': Counter()}
    for x in fa:
        res['kinds_a'][x['face'].split(';')[0].rsplit('|', 1)[0] if x['face'] else '-'] += 1
    for x in fb:
        res['kinds_b'][x['face'].split(';')[0].rsplit('|', 1)[0] if x['face'] else '-'] += 1
    for x, y in zip(fa, fb):
        if (x['pre'], x['tag'], x['t']) != (y['pre'], y['tag'], y['t']):
            res['diff'] += 1
            if len(res['examples']) < 5:
                res['examples'].append(('misaligned', x['t'], y['t']))
            continue
        if x['face'] != y['face']:
            res['diff'] += 1
            if len(res['examples']) < 5:
                res['examples'].append((x['t'], x['face'], y['face']))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True)
    ap.add_argument('--b', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--only', default='')
    ap.add_argument('--json', default='')
    ap.add_argument('--nomask', action='store_true', help='noise-floor mode (reference against itself): no masks')
    o = ap.parse_args()
    A, B, OUT = Path(o.a), Path(o.b), Path(o.out)
    OUT.mkdir(parents=True, exist_ok=True)
    names = sorted({p.name[:-10] for p in A.glob('*.meta.json')} & {p.name[:-10] for p in B.glob('*.meta.json')})
    if o.only:
        names = [n for n in names if n in o.only.split(',')]
    allres = {}
    for n in names:
        ma, mb = load_meta(A, n), load_meta(B, n)
        r = {'errors': [x.get('error') for x in (ma, mb) if x.get('error')]}
        if r['errors'] or not (A / (n + '.png')).is_file() or not (B / (n + '.png')).is_file():
            allres[n] = r
            print(f'{n}: ERROR {r["errors"]}')
            continue
        masks = [] if o.nomask else (ma.get('masks', []) + mb.get('masks', []))
        # a viewport screenshot of a scrolled page: the masthead is pinned, so its rectangles are in viewport coordinates, not page coordinates
        im_h = Image.open(A / (n + '.png')).height
        if im_h < ma.get('docH', 0) - 2:
            masks = [dict(m, y=m['y'] - ((ma if m in ma.get('masks', []) else mb).get('scroll') or [0, 0])[1]) if not m.get('fixed') else m for m in masks]
        r['masks'] = [(round(m['x']), round(m['y']), round(m['w']), round(m['h']), m['why']) for m in masks]
        r['pixels'] = pixel_diff(A / (n + '.png'), B / (n + '.png'), masks, OUT / (n + '.diff.png'))
        r['styles'] = style_diff(A / (n + '.styles.json'), B / (n + '.styles.json'))
        r['faces'] = face_diff(ma, mb)
        r['state_equal'] = ma['state'] == mb['state']
        r['state'] = (ma['state'], mb['state']) if not r['state_equal'] else None
        r['hash'] = (ma['hash'], mb['hash'])
        allres[n] = r
        p, s, f = r['pixels'], r['styles'], r['faces']
        print(f"{n}: px {p['pct']:.4f}% ({p['diff_px']}) size {p['a_size']}/{p['b_size']}  styles: {s['elements_diff']} el differ of {s['n_a']}/{s['n_b']} (only ref {len(s['only_a'])}, only pc {len(s['only_b'])}) {dict(s['props'])}  faces: {f['diff']}/{f['n_a']}  state={'same' if r['state_equal'] else 'DIFF'}")
    if o.json:
        def enc(x):
            if isinstance(x, Counter):
                return dict(x)
            if isinstance(x, defaultdict):
                return dict(x)
            raise TypeError(type(x))
        Path(o.json).write_text(json.dumps(allres, default=enc, indent=1))


if __name__ == '__main__':
    main()
