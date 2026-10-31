"""Strip the data blocks from a tracker page -> page shell for assemble.py (BUTTONOPT T4b, agent-v20-final)."""
import sys, re
src, out = sys.argv[1:3]
h = open(src, encoding='utf-8').read()
# 1. data payload -> []
d = h.find('<script id="data"'); ds = h.find('>', d) + 1; de = h.find('</script>', ds)
h = h[:ds] + '[]' + h[de:]
# 2. blocks assemble/insights/tabs re-add: drop whole
for n in ('rows', 'idmap', 'covcols', 'billsinfo', 'cleanrules', 'fetchrules'):
    tag = f'<script id="{n}" type="application/json">'
    while tag in h:
        i = h.find(tag); j = h.find('</script>', i) + len('</script>')
        if h[i-1:i] == '\n': i -= 1
        h = h[:i] + h[j:]
# 3. ins-*/tab-* json payloads -> {}
h = re.sub(r'(<script id="(?:ins|tab)-[a-z_]+" type="application/json">).*?(</script>)', r'\1{}\2', h, flags=re.S)
# 4. main script body emptied (assemble replaces from the last <script> to the end)
m = h.rfind('<script>')
h = h[:m] + '<script>\n</script>\n</body>\n</html>\n'
open(out, 'w', encoding='utf-8').write(h)
print(out, len(h))
