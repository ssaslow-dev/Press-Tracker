# Pull every TinyFish fetch_content result out of agent-fetch-2's own transcript into a cache (no retyping of page text).
import json, hashlib, os, sys
T='/root/.claude/projects/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/subagents/agent-aced6994a1d3d3171.jsonl'
C='/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib/work/fetch_cache'
os.makedirs(C,exist_ok=True); n=0
def walk(o):
    if isinstance(o,dict):
        if 'results' in o and isinstance(o['results'],list) and o['results'] and isinstance(o['results'][0],dict) and 'text' in o['results'][0]:
            yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
    elif isinstance(o,str) and o.startswith('{') and '"results"' in o:
        try: yield from walk(json.loads(o))
        except Exception: pass
import glob
for f in glob.glob('/root/.claude/projects/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/tool-results/*.json')+glob.glob('/root/.claude/projects/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/tool-results/mcp-TinyFish-fetch_content-*.txt'):
    try: d=json.load(open(f))
    except Exception: continue
    for res in walk(d):
        for r in res['results']:
            json.dump(r,open(f"{C}/{hashlib.sha1(r['url'].encode()).hexdigest()[:16]}.json",'w')); n+=1
for line in open(T):
    try: d=json.loads(line)
    except Exception: continue
    for res in walk(d):
        for r in res['results']:
            k=hashlib.sha1(r['url'].encode()).hexdigest()[:16]
            json.dump(r,open(f'{C}/{k}.json','w')); n+=1
        for e in res.get('errors',[]) or []:
            u=e.get('url') if isinstance(e,dict) else None
            if u: json.dump({'url':u,'error':e},open(f"{C}/{hashlib.sha1(u.encode()).hexdigest()[:16]}.err.json",'w'))
print('cached',n,'files',len(os.listdir(C)))
