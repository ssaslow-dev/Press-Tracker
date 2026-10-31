"""INSIGHTS-v1: put the Insights views and their data blocks into an assembled tracker page (idempotent).
Usage: python3 -I insights_assemble.py PAGE.html INS_DIR [BLOCKS_DIR] [OUT.html]
- removes any earlier <script id="ins-..."> / <script id="ins-js-..."> blocks
- adds BLOCKS_DIR/ins_<id>.json as <script id="ins-<id>" type="application/json"> after the other data blocks
- adds INS_DIR/<id>.js (every *.js not starting with '_' and not a test) as <script id="ins-js-<id>"> right after the
  main script, in the sub-nav order.
Also importable: apply(html, ins_dir, blocks_dir) -> html."""
import sys, os, re, json
ORDER = ['bill_timeline', 'story_travel', 'reporters', 'tone_topic']
# rp-final 2026-10-28 (backend #8): the legacy release_pickup VIEW is retired (the Press releases tab replaced it); its data block
# ins_release_pickup.json still ships (relIndex, bills.js, relList, 41 relKnown read it). build/insights/release_pickup.js stays on disk.
RETIRED = {'release_pickup'}
ID = re.compile(r'^[a-z][a-z_]*$')
def _esc(s): return s.replace('</', '<\\/')
def apply(h, ins_dir, blocks_dir=None):
    h = re.sub(r'\n?<script id="ins-[a-z_-]+"( type="application/json")?>.*?</script>', '', h, flags=re.S)
    mods = sorted([f[:-3] for f in (os.listdir(ins_dir) if ins_dir and os.path.isdir(ins_dir) else [])
                   if f.endswith('.js') and not f.startswith('_') and not f.endswith('.test.js') and ID.match(f[:-3]) and f[:-3] not in RETIRED],
                  key=lambda k: (ORDER.index(k) if k in ORDER else 99, k))
    blocks = []
    if blocks_dir and os.path.isdir(blocks_dir):
        for f in sorted(os.listdir(blocks_dir)):
            m = re.match(r'^ins_([a-z][a-z_]*)\.json$', f)
            if m:
                t = open(os.path.join(blocks_dir, f), encoding='utf-8').read(); json.loads(t)
                blocks.append(f'\n<script id="ins-{m.group(1)}" type="application/json">{_esc(t)}</script>')
    if blocks:
        d = h.find('<script id="data"'); de = h.find('</script>', d) + len('</script>')
        # after the last data block that follows "data" (rows/idmap/covcols/billsinfo)
        k = de
        while True:
            m2 = re.match(r'\s*<script id="[a-z]+" type="application/json">', h[k:])
            if not m2: break
            k = h.find('</script>', k + m2.end()) + len('</script>')
        h = h[:k] + ''.join(blocks) + h[k:]
    m = h.rfind('<script>'); e = h.find('</script>', m) + len('</script>')
    js = ''.join(f'\n<script id="ins-js-{k}">\n{open(os.path.join(ins_dir, k + ".js"), encoding="utf-8").read()}\n</script>' for k in mods)
    assert js.lower().count('</script') == len(mods), 'a view file contains </script>'
    h = h[:e] + js + h[e:]
    return h
if __name__ == '__main__':
    PAGE, INS = sys.argv[1:3]; BLK = sys.argv[3] if len(sys.argv) > 3 else None; OUT = sys.argv[4] if len(sys.argv) > 4 else PAGE
    h = apply(open(PAGE, encoding='utf-8').read(), INS, BLK)
    open(OUT, 'w', encoding='utf-8').write(h); print(OUT, len(h))
