"""T30: build_data.py change — carry Author 1..N + Author title into each tracker record as `authors` (list) and `atitle`.
Usage: python3 -I patch_build_data.py IN.py OUT.py   (anchors must match exactly once)
Needs code/authorsplit.py next to build_data.py (fallback parser for rows the sheet hasn't split yet).
"""
import sys
src, dst = sys.argv[1:3]
t = open(src, encoding='utf-8').read()
R = [
("import sys, re, json, collections\nimport pandas as pd\n",
 "import sys, re, json, collections, os\nimport pandas as pd\n"
 "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I drops the script dir; authorsplit.py lives here\n"
 "from authorsplit import parse_byline, author_kind\n"),
("covcols = list(C.columns)\n",
 "covcols = list(C.columns)\n"
 "# T30: Author 1..N + Author title (split of Author / byline). Rows not split yet (sheet task adds) are parsed here.\n"
 "ACOLS = sorted([c for c in C.columns if re.fullmatch(r'Author \\d+', c)], key=lambda c: int(c.split()[1]))\n"
 "def authors_of(r, o):\n"
 "    a = [str(r[c]).strip() for c in ACOLS if str(r[c]).strip()]\n"
 "    if a: return a, str(r.get('Author title', '')).strip()\n"
 "    b = str(r['Author / byline']).strip()\n"
 "    if b: p = parse_byline(b, r['Outlet']); return p['authors'], p['title']\n"
 "    old = o.get('author', '')                      # old tracker records keep \"A; B\"\n"
 "    return [x.strip() for x in old.split(';') if x.strip()], ''\n"),
("        'author': s(r['Author / byline']) or o.get('author', ''),\n",
 "        'author': s(r['Author / byline']) or o.get('author', ''),\n"
 "        'authors': authors_of(r, o)[0], 'atitle': authors_of(r, o)[1],\n"
 "        'akinds': [author_kind(x) for x in authors_of(r, o)[0]],   # person|board|staff|wire|org (tracker filter grouping)\n"),
]
for old, new in R:
    n = t.count(old)
    if n != 1: sys.exit(f'anchor found {n}x: {old[:80]!r}')
    t = t.replace(old, new)
open(dst, 'w', encoding='utf-8').write(t)
print('ok', dst)
