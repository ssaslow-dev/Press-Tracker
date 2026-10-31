# Pull TinyFish fetch_content results for leginfo history pages out of this agent's transcript (no retyping).
import json, re, os, sys
T='/root/.claude/projects/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/subagents/agent-a7276149b9f1b0882.jsonl'
C='/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib/work/billstatus_cache'
def walk(o):
    if isinstance(o,dict):
        if 'results' in o and isinstance(o['results'],list): yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
    elif isinstance(o,str) and o.lstrip().startswith('{') and '"results"' in o:
        try: yield from walk(json.loads(o))
        except Exception: pass
n=e=0
for line in open(T):
    try: d=json.loads(line)
    except Exception: continue
    for res in walk(d):
        for r in res['results']:
            if not isinstance(r,dict) or 'billHistoryClient' not in r.get('url',''): continue
            bid=re.search(r'bill_id=(\w+)',r['url']).group(1)
            json.dump(r,open(f'{C}/{bid}.json','w')); n+=1
            if os.path.exists(f'{C}/{bid}.err.json'): os.remove(f'{C}/{bid}.err.json')
        for er in res.get('errors',[]) or []:
            u=er.get('url','') if isinstance(er,dict) else ''
            m=re.search(r'bill_id=(\w+)',u)
            if m and 'billHistoryClient' in u and not os.path.exists(f'{C}/{m.group(1)}.json'):
                json.dump(er,open(f'{C}/{m.group(1)}.err.json','w')); e+=1
print('ok',len([f for f in os.listdir(C) if not f.endswith('.err.json')]),'err',len([f for f in os.listdir(C) if f.endswith('.err.json')]))
