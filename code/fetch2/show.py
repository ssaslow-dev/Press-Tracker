import json,hashlib,sys,re
C='/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib/work/fetch_cache'
for u in sys.argv[1:]:
    try: r=json.load(open(f"{C}/{hashlib.sha1(u.encode()).hexdigest()[:16]}.json"))
    except FileNotFoundError: print('### MISSING',u); continue
    t=r['text']; paras=[p for p in re.split(r'\n\s*\n',t) if p.strip()]
    g=[i for i,p in enumerate(paras) if re.search('gabriel',p,re.I)]
    print('#####',u,'|',r.get('title'),'| len',len(t),'| paras',len(paras),'| gabriel paras',g, '| author',r.get('author'))
    print('FIRST:',' // '.join(p[:160] for p in paras[:4]))
    print('LAST:',' // '.join(p[:120] for p in paras[-4:]))
    for i in g: print(f'  G[{i}]:',paras[i][:900])
