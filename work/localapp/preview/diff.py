import sys, glob, os
import numpy as np
from PIL import Image
d = sys.argv[1]
for f in sorted(glob.glob(d + '/pv_*.png')):
    n = os.path.basename(f)[3:]
    a = np.asarray(Image.open(f).convert('RGB')).astype(int); b = np.asarray(Image.open(d + '/pc_' + n).convert('RGB')).astype(int)
    if a.shape != b.shape: print(n, 'shape', a.shape, b.shape); continue
    df = np.abs(a - b).sum(2) > 0; df[:75, 600:] = False   # masthead right side: the PC has extra buttons there, the preview its line
    ys, xs = np.nonzero(df); print(n, 'diff px', int(df.sum()), (int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())) if len(ys) else '')
