"""Step 1: read every NewsBank PDF copy (File name / File name 2 = nb*.pdf) and store its text (cache in the scratchpad)."""
import sys, os, pickle, multiprocessing as mp
sys.path.insert(0, '/home/user/Press-Tracker/work/localapp/datafix')
from common import *
CACHE = S + '/nb_fills2_texts.pkl'
def rd(p):
    import pypdf, logging; logging.disable(logging.CRITICAL)
    try:
        r = pypdf.PdfReader(p); return p, [(pg.extract_text() or '') for pg in r.pages]
    except Exception as e:
        return p, None
def main():
    h, rows = load_coverage()
    paths = set()
    for r in rows:
        for c in ('File name', 'File name 2'):
            f = s(r[c])
            if f.startswith('nb') and f.endswith('.pdf'):
                p = lib_path(f, r['Date'])
                if p: paths.add(p)
    with mp.Pool(4) as pool: res = dict(pool.map(rd, sorted(paths), chunksize=20))
    pickle.dump(res, open(CACHE, 'wb')); print(len(res), sum(v is None for v in res.values()))
if __name__ == '__main__': main()
