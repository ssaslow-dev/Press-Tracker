"""agent-fetch helper. Usage: python3 -I save_fetch.py SPEC.json BATCH_TAG
SPEC: list of {sid, aid, year, outlet, date, url, hl, byline?, paras:[...] (omit when flagged), tone..., flag?}
Writes lib/work/texts/tracker/<sid>.html (skip if exists), stages a copy for the Mac at
/mnt/user-data/outputs/tlib_<tag>/<year>/<aid>.html, appends rating lines to out/tone_batch_<tag>.out.jsonl."""
import sys, os, json, html, hashlib
L = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
spec = json.load(open(sys.argv[1])); tag = sys.argv[2]
out = open(os.path.join(L, 'work', 'out', f'tone_batch_{tag}.out.jsonl'), 'a', encoding='utf-8')
for s in spec:
    rec = {k: s[k] for k in ('sid', 'aid', 'tone', 'why', 'rated_by', 'topic', 'bills', 'author', 'words', 'mentions_gabriel', 'hl_en', 'text_en', 'url_used', 'flag') if k in s}
    if not s.get('flag') and s.get('paras'):
        e = html.escape
        page = ('<!doctype html><html><head><meta charset="utf-8"><title>' + e(s['hl']) + '</title><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'
                f'<div>{e(s["outlet"])} · {e(s["date"])}<br>{e(s["url"])}<br>Saved 2026-10-27</div><h1>{e(s["hl"])}</h1>'
                + (f'<div>{e(s["byline"])}</div>' if s.get('byline') else '') + '<div>' + ''.join(f'<p>{e(p)}</p>' for p in s['paras']) + '</div></body></html>')
        p = os.path.join(L, 'work', 'texts', 'tracker', s['sid'] + '.html')
        if not os.path.exists(p): open(p, 'w', encoding='utf-8').write(page)
        page = open(p, encoding='utf-8').read()
        d = f'/mnt/user-data/outputs/tlib_{tag}/{s["year"]}'; os.makedirs(d, exist_ok=True)
        open(f'{d}/{s["aid"]}.html', 'w', encoding='utf-8').write(page)
        rec['words'] = rec.get('words') or sum(len(x.split()) for x in s['paras'])
        rec['sha256'] = hashlib.sha256(page.encode()).hexdigest()
    out.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(s['sid'], s['aid'], 'FLAG ' + s['flag'] if s.get('flag') else s.get('tone'))
