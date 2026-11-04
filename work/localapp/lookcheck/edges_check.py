"""N10: do the list tables line up exactly with the controls above them? Run edges.js against a running PC tracker (default http://127.0.0.1:8791/), then measure the
screenshots: the navy header bar and the body's side borders must start at the controls' left edge (16 px) and end at the right edge (width - 16 px), in every list tab,
at 1440x900, 1366x768, 1536x864 at 125 % and 1280x720.
    node work/localapp/lookcheck/edges.js OUTDIR 1440x900@1 1366x768@1 1536x864@1.25 1280x720@1 ; python3 -I work/localapp/lookcheck/edges_check.py OUTDIR"""
import glob
import json
import sys

from PIL import Image

bad = 0
for f in sorted(glob.glob(sys.argv[1] + '/*.json')):
    g = json.load(open(f))
    im = Image.open(f.replace('.json', '.png')).convert('RGB')
    d = g['dpr']
    y = int((g['th'][2] + g['th'][3]) / 2 * d)
    navy = [x for x in range(im.width) if (lambda p: p[0] < 40 and p[1] < 60 and p[2] < 100)(im.getpixel((x, y)))]
    yb = int((g['th'][3] + 30) * d)
    bg = im.getpixel((2, yb))
    body = [x for x in range(im.width) if im.getpixel((x, yb)) != bg]
    want = (g['ctl'][0], g['card'][1])
    got = (navy[0] / d, (navy[-1] + 1) / d, body[0] / d, (body[-1] + 1) / d)
    ok = abs(got[0] - want[0]) < 0.5 and abs(got[2] - want[0]) < 0.5 and abs(got[1] - want[1]) < 0.5 and abs(got[3] - want[1]) < 0.5
    bad += not ok
    print(('ok  ' if ok else 'BAD ') + f.split('/')[-1][:-5], got, want)
print('EDGES:', 'PASS' if not bad else f'{bad} differ')
sys.exit(1 if bad else 0)
