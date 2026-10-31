"""TABS-v1: build the tab data blocks. Runs TABS_DIR/_common_data.py (framework: cleaned outlet names + publishers ->
tab_common.json) and every TABS_DIR/<id>_data.py: build(cov, data, ctx) -> obj|None, written to BLOCKS_DIR/tab_<id>.json
(compact JSON, sorted keys). Same build() signature and ctx as the Insights data builders (build/insights_contract.md §6).
Usage: python3 -I tabs_data.py XLSX BLOCKS_DIR TABS_DIR [--only ID]
Also importable: run(xlsx, blocks_dir, tabs_dir, lib=None, cov=None, data=None, only=None) -> {id: bytes}."""
import sys, os, json, importlib.util, datetime
CAP = 200_000   # soft warning; raised from 150 KB by rp-final 2026-10-28 (tab-releases 154 KB: RELRELATED-v3 rel + RELTHREAD thr)
def run(xlsx, blocks_dir, tabs_dir, lib=None, cov=None, data=None, only=None):
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
    for f in sorted(os.listdir(tabs_dir) if os.path.isdir(tabs_dir) else []):
        if not f.endswith('_data.py'): continue
        vid = f[:-len('_data.py')]
        if vid.startswith('_') and vid != '_common': continue
        name = 'common' if vid == '_common' else vid
        if only and name not in (only, 'common'): continue
        spec = importlib.util.spec_from_file_location(f'tab_{name}_data', os.path.join(tabs_dir, f)); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        obj = mod.build(cov, data, ctx)
        p = os.path.join(blocks_dir, f'tab_{name}.json')
        if obj is None:
            if os.path.exists(p): os.remove(p)
            continue
        t = json.dumps(obj, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
        if len(t.encode()) > CAP: print(f'WARNING tab_{name}.json is {len(t.encode())} bytes (> {CAP})', file=sys.stderr)
        open(p, 'w', encoding='utf-8').write(t); out[name] = len(t.encode())
    return out
if __name__ == '__main__':
    a = sys.argv[1:]; only = None
    if '--only' in a: i = a.index('--only'); only = a[i + 1]; del a[i:i + 2]
    X, B, T = a[:3]; print(run(X, B, T, a[3] if len(a) > 3 else None, only=only))
