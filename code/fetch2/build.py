# Build saved copies + output lines from cached fetches and my per-story decisions (decisions file holds only markers + ratings).
import json, hashlib, os, re, html, sys
L='/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib'
C=f'{L}/work/fetch_cache'; DEC=sys.argv[1]
jobs={json.loads(l)['sid']:json.loads(l) for l in open(f'{L}/work/jobs/fetch_2.jsonl')}
OUT=f'{L}/work/out/tone_batch_fetch2.out.jsonl'
done={json.loads(l)['sid'] for l in open(OUT)} if os.path.exists(OUT) else set()
e=html.escape
for line in open(DEC):
    if not line.strip(): continue
    d=json.loads(line); sid=d['sid']; j=jobs[sid]
    if sid in done: continue
    if d.get('real_sid'): j=dict(j,aid=d['real_aid']); sid=d['real_sid']
    rec={'sid':sid,'aid':j['aid']}
    year=(j['date'] or '')[:4] or 'undated'
    if d.get('flag') and not d.get('save'):
        rec.update({'flag':d['flag'],'url_used':d.get('url','')})
    else:
        if d.get('use_existing'):
            body_html=None; text=re.sub(r'<[^>]+>',' ',open(f"{L}/work/texts/tracker/{sid}.html").read())
        else:
            r=json.load(open(f"{C}/{hashlib.sha1(d['url'].encode()).hexdigest()[:16]}.json"))
            t=r['text']
            if 'start_para' in d or 'end_para' in d:
                P=[x for x in re.split(r'\n\s*\n',t) if x.strip()]
                t='\n\n'.join(P[d.get('start_para',0):d.get('end_para',len(P))])
            if d.get('start'): i=t.find(d['start']); assert i>=0,(sid,'start'); t=t[i:]
            if d.get('end'): i=t.find(d['end']); assert i>=0,(sid,'end'); t=t[:i]
            paras=[]
            for p in re.split(r'\n\s*\n',t):
                p=p.strip()
                if not p or any(x in p for x in d.get('drop',[])): continue
                if p.startswith('# '): continue
                if re.fullmatch(r'#+ .*',p): paras.append(f'<p><b>{e(p.lstrip("# "))}</b></p>'); continue
                p=re.sub(r'^\* ','• ',p,flags=re.M)
                paras.append('<p>'+e(p).replace('\n','<br>')+'</p>')
            text=t
            url=r.get('final_url') or d['url']; au=d.get('byline') or r.get('author') or ''
            body_html=(f'<!doctype html><html><head><meta charset="utf-8"><title>{e(j["hl"])}</title><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'
                       f'<div>{e(j["outlet"])} · {e(j["date"])}<br>{e(url)}<br>Saved 2026-10-27</div><h1>{e(d.get("h1") or j["hl"])}</h1>'
                       +(f'<div>{e(au)}</div>' if au else '')+'<div>'+''.join(paras)+'</div></body></html>')
            p1=f"{L}/work/texts/tracker/{sid}.html"
            if not os.path.exists(p1): open(p1,'w').write(body_html)
            os.makedirs(f'/mnt/user-data/outputs/tlib_fetch2/{year}',exist_ok=True)
            open(f"/mnt/user-data/outputs/tlib_fetch2/{year}/{j['aid']}.html",'w').write(body_html)
        words=len(re.findall(r"\w[\w'’-]*",text))
        rec.update({'tone':d['tone'],'why':d['why'],'rated_by':d.get('rated_by','Claude, from saved copy (2026-10-27)'),'topic':d['topic'],'bills':d.get('bills',[]),
                    'words':words,'mentions_gabriel':bool(re.search(r'gabriel',text,re.I)),'url_used':d.get('url','')})
        for k in ('author','hl_en','text_en','flag','note'):
            if d.get(k): rec[k]=d[k]
    open(OUT,'a').write(json.dumps(rec,ensure_ascii=False)+'\n'); done.add(sid)
    print(sid, rec.get('tone') or rec.get('flag'), rec.get('words',''), rec.get('mentions_gabriel',''))
