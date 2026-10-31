"""TABS-v1: put the tab modules and their data blocks into an assembled tracker page (idempotent).
Usage: python3 -I tabs_assemble.py PAGE.html TABS_DIR [BLOCKS_DIR] [OUT.html]
- removes any earlier <script id="tab-..."> / <script id="tab-js-..."> blocks
- adds BLOCKS_DIR/tab_<id>.json (incl. tab_common.json) as <script id="tab-<id>" type="application/json"> after the
  other data blocks
- adds TABS_DIR/<id>.js (every *.js not starting with '_' and not a test) as <script id="tab-js-<id>"> right after the
  last Insights view script (or the main script), in menu order.
Also importable: apply(html, tabs_dir, blocks_dir) -> html."""
import sys, os, re, json
ORDER = ['reporters', 'outlets', 'releases', 'bills', 'travel']
ID = re.compile(r'^[a-z][a-z0-9_]*$')
def _esc(s): return s.replace('</', '<\\/')
def apply(h, tabs_dir, blocks_dir=None):
    # only blocks this script wrote (each starts a line), never text inside another script
    h = re.sub(r'\n<script id="tab-[a-z0-9_-]+"( type="application/json")?>.*?</script>', '', h, flags=re.S)
    mods = sorted([f[:-3] for f in (os.listdir(tabs_dir) if tabs_dir and os.path.isdir(tabs_dir) else [])
                   if f.endswith('.js') and not f.startswith('_') and not f.endswith('.test.js') and ID.match(f[:-3])],
                  key=lambda k: (ORDER.index(k) if k in ORDER else 99, k))
    blocks = []
    if blocks_dir and os.path.isdir(blocks_dir):
        for f in sorted(os.listdir(blocks_dir)):
            m = re.match(r'^tab_([a-z][a-z0-9_]*)\.json$', f)
            if m:
                t = open(os.path.join(blocks_dir, f), encoding='utf-8').read(); json.loads(t)
                blocks.append(f'\n<script id="tab-{m.group(1)}" type="application/json">{_esc(t)}</script>')
    if blocks:
        d = h.find('<script id="data"'); k = h.find('</script>', d) + len('</script>')
        while True:   # after the last data block that follows "data" (rows/idmap/covcols/billsinfo/ins-*)
            m2 = re.match(r'\s*<script id="[a-z_-]+" type="application/json">', h[k:])
            if not m2: break
            k = h.find('</script>', k + m2.end()) + len('</script>')
        h = h[:k] + ''.join(blocks) + h[k:]
    ins = [m.end() for m in re.finditer(r'<script id="ins-js-[a-z_]+">.*?</script>', h, flags=re.S)]
    if ins: e = ins[-1]
    else: m = h.rfind('<script>'); e = h.find('</script>', m) + len('</script>')
    js = ''.join(f'\n<script id="tab-js-{k}">\n{open(os.path.join(tabs_dir, k + ".js"), encoding="utf-8").read()}\n</script>' for k in mods)
    assert js.lower().count('</script') == len(mods), 'a tab module contains </script>'
    return h[:e] + js + h[e:]
if __name__ == '__main__':
    PAGE, TD = sys.argv[1:3]; BLK = sys.argv[3] if len(sys.argv) > 3 else None; OUT = sys.argv[4] if len(sys.argv) > 4 else PAGE
    h = apply(open(PAGE, encoding='utf-8').read(), TD, BLK)
    open(OUT, 'w', encoding='utf-8').write(h); print(OUT, len(h))
