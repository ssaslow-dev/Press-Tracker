"""INSIGHTS-v1: build the Insights data blocks. Runs every <id>_data.py in INS_DIR: build(cov, data, ctx) -> obj|None,
written to BLOCKS_DIR/ins_<id>.json (compact JSON). Usage: python3 -I insights_data.py XLSX BLOCKS_DIR INS_DIR [LIB]
Also importable: run(xlsx, blocks_dir, ins_dir, lib=None, cov=None, data=None) -> {id: bytes}."""
import sys, os, json, importlib.util, datetime
CAP = 150_000
def run(xlsx, blocks_dir, ins_dir, lib=None, cov=None, data=None):
    import pandas as pd
    if cov is None: cov = pd.read_excel(xlsx, sheet_name='Coverage', dtype=str).fillna('')
    if data is None: data = json.load(open(os.path.join(blocks_dir, 'data.json'), encoding='utf-8'))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from reprint_rule import hide_unverified   # HIDEUNVERIFIED-v1: the one predicate
    cov = hide_unverified(cov)
    def read_sheet(name):
        try: df = pd.read_excel(xlsx, sheet_name=name, dtype=str).fillna(''); return hide_unverified(df) if name == 'Coverage' else df
        except Exception: return None
    ctx = {'xlsx': xlsx, 'lib': lib or '', 'blocks_dir': blocks_dir, 'today': datetime.date.today().isoformat(), 'read_sheet': read_sheet}
    out = {}
    for f in sorted(os.listdir(ins_dir) if os.path.isdir(ins_dir) else []):
        if not f.endswith('_data.py') or f.startswith('_'): continue
        vid = f[:-len('_data.py')]
        spec = importlib.util.spec_from_file_location(f'ins_{vid}_data', os.path.join(ins_dir, f)); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        obj = mod.build(cov, data, ctx)
        p = os.path.join(blocks_dir, f'ins_{vid}.json')
        if obj is None:
            if os.path.exists(p): os.remove(p)
            continue
        t = json.dumps(obj, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
        if len(t.encode()) > CAP: print(f'WARNING ins_{vid}.json is {len(t.encode())} bytes (> {CAP})', file=sys.stderr)
        open(p, 'w', encoding='utf-8').write(t); out[vid] = len(t.encode())
    return out
if __name__ == '__main__':
    X, B, I = sys.argv[1:4]; print(run(X, B, I, sys.argv[4] if len(sys.argv) > 4 else None))
