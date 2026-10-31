"""Assemble the new tracker index.html.
Usage: python3 -I assemble.py OLD_INDEX.html BLOCKS_DIR JS_FILE OUT.html
Replaces the <script id="data"> payload with BLOCKS_DIR/data.json, adds <script id="rows|idmap|covcols"> blocks
right after it, and replaces the main inline <script> (the last one) with JS_FILE.
"""
import sys, json
OLD, BLK, JS, OUT = sys.argv[1:5]
h = open(OLD, encoding='utf-8').read()

def esc(s):  # keep JSON safe inside <script>
    return s.replace('</', '<\\/')

# drop blocks from an earlier assembly so re-assembling a published page doesn't duplicate them
for n in ('billsinfo', 'rows', 'idmap', 'covcols', 'cleanrules', 'fetchrules'):   # CLEAN-v1; fetchrules: DRIFT-2/3
    while True:
        i = h.find(f'\n<script id="{n}" type="application/json">')
        if i < 0: i = h.find(f'<script id="{n}" type="application/json">')
        if i < 0: break
        j = h.find('</script>', i) + len('</script>')
        h = h[:i] + h[j:]
d = h.find('<script id="data"'); ds = h.find('>', d) + 1; de = h.find('</script>', ds)
blocks = {n: open(f'{BLK}/{n}.json', encoding='utf-8').read() for n in ('data', 'rows', 'idmap', 'covcols')}
import os   # CLEAN-v1: the page-cleaning rules (blocks/cleanrules.json, from build_data.py) ride along
if os.path.exists(f'{BLK}/cleanrules.json'): blocks['cleanrules'] = open(f'{BLK}/cleanrules.json', encoding='utf-8').read()
if os.path.exists(f'{BLK}/fetchrules.json'): blocks['fetchrules'] = open(f'{BLK}/fetchrules.json', encoding='utf-8').read()   # DRIFT-2/3 (final-int)
if os.path.exists(f'{BLK}/billsinfo.json'): blocks['billsinfo'] = open(f'{BLK}/billsinfo.json', encoding='utf-8').read()   # AUTO-v1: his bills (leginfo)
blocks.pop('cleanrules', None)   # CLEAN-v2: the tracker no longer cleans pages, so it doesn't carry the rules
for n, v in blocks.items(): json.loads(v)
extra = ''.join(f'\n<script id="{n}" type="application/json">{esc(blocks[n])}</script>' for n in ('rows', 'idmap', 'covcols', 'cleanrules', 'fetchrules') if n in blocks)
extra += ''.join(f'\n<script id="{n}" type="application/json">{esc(blocks[n])}</script>' for n in ('billsinfo',) if n in blocks)   # AUTO-v1 assemble
h = h[:ds] + esc(blocks['data']) + '</script>' + extra + h[de + len('</script>'):]

h = h.replace('<title>AJG Press Coverage Tracker (Copy)</title>', '<title>AJG Press Coverage Tracker</title>')  # F7-v1
m = h.rfind('<script>')
js = open(JS, encoding='utf-8').read()
# JS files in lib/build are the tail of the page from the main <script> to </html> (as extracted)
assert js.startswith('<script>') and js.lower().count('</script') == 1, 'unexpected JS file shape'
h = h[:m] + js
open(OUT, 'w', encoding='utf-8').write(h)
print(OUT, len(h))

# INSIGHTS-v1: the Insights views (<INS_DIR>/<id>.js) and their data blocks (BLOCKS_DIR/ins_<id>.json)
_ins_dir = os.environ.get('INS_DIR') or os.path.join(os.path.dirname(os.path.abspath(JS)), 'insights')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import insights_assemble
h = insights_assemble.apply(open(OUT, encoding='utf-8').read(), _ins_dir, BLK)
open(OUT, 'w', encoding='utf-8').write(h)
print('insights:', _ins_dir, len(h))
# TABS-v1: the tab modules (<TABS_DIR>/<id>.js) and their data blocks (BLOCKS_DIR/tab_<id>.json)
_tabs_dir = os.environ.get('TABS_DIR') or os.path.join(os.path.dirname(os.path.abspath(JS)), 'tabs')
import tabs_assemble
h = tabs_assemble.apply(open(OUT, encoding='utf-8').read(), _tabs_dir, BLK)
open(OUT, 'w', encoding='utf-8').write(h)
print('tabs:', _tabs_dir, len(h))
