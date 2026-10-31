# Build saved copies + fetch_rated_1 output lines from cached fetches and per-story decisions.
# decisions line: {sid, url, flag?, save?, start?, end?, drop?, start_para?, end_para?, h1?, byline?,
#   tone, why, topic?, bills?, other_bills?, other_bills_note?, author?, mentions?(override), verified?}
import json, hashlib, os, re, html, sys
L='/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib'
C=f'{L}/work/fetch_cache'; DEC=f'{L}/work/fetch_rated1_decisions.jsonl'
jobs={json.loads(l)['sid']:json.loads(l) for l in open(f'{L}/work/jobs/fetch_rated_1.jsonl')}
OUT=f'{L}/work/out/fetch_rated_1.out.jsonl'
done={json.loads(l)['sid'] for l in open(OUT)} if os.path.exists(OUT) else set()
e=html.escape
for line in open(DEC):
    if not line.strip(): continue
    d=json.loads(line); sid=d['sid']; j=jobs[sid]
    if sid in done: continue
    rec={'sid':sid,'aid':j['aid'],'url_used':d.get('url','')}
    year=j.get('year') or (j['date'] or '')[:4] or 'undated'
    if not d.get('save'):
        rec.update({'verified':d.get('verified',False),'mentions_gabriel':d.get('mentions'),'flag':d['flag']})
        for k in ('note','fulltext_tone','fulltext_why'):
            if d.get(k): rec[k]=d[k]
    else:
        p1=f"{L}/work/texts/tracker/{sid}.html"
        if d.get('use_existing'):
            text=re.sub(r'<[^>]+>',' ',html.unescape(open(p1).read()))
        else:
            r=json.load(open(f"{C}/{hashlib.sha1(d['url'].encode()).hexdigest()[:16]}.json"))
            t=r['text']
            if 'start_para' in d or 'end_para' in d:
                P=[x for x in re.split(r'\n\s*\n',t) if x.strip()]
                t='\n\n'.join(P[d.get('start_para',0):d.get('end_para',len(P))])
            if d.get('start'): i=t.find(d['start']); assert i>=0,(sid,'start'); t=t[i:]
            if d.get('end'): i=t.find(d['end']); assert i>=0,(sid,'end'); t=t[:i]
            paras=[]; kept=[]
            for p in re.split(r'\n\s*\n',t):
                p=p.strip()
                if not p or any(x in p for x in d.get('drop',[])): continue
                if p.startswith('# '): continue
                p=re.sub(r'!\[[^\]]*\]\([^)]*\)','',p); p=re.sub(r'\[([^\]]*)\]\([^)]*\)',r'\1',p).strip()
                if not p: continue
                kept.append(p)
                if re.fullmatch(r'#+ .*',p): paras.append(f'<p><b>{e(p.lstrip("# "))}</b></p>'); continue
                p=re.sub(r'^\* ','• ',p,flags=re.M)
                paras.append('<p>'+e(p).replace('\n','<br>')+'</p>')
            text='\n\n'.join(kept)
            url=r.get('final_url') or d['url']; au=d.get('byline') or ''
            page=(f'<!doctype html><html><head><meta charset="utf-8"><title>{e(d.get("h1") or j["hl"])}</title><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'
                  f'<div>{e(j["outlet"])} · {e(j["date"])}<br>{e(url)}<br>Saved 2026-10-27</div><h1>{e(d.get("h1") or j["hl"])}</h1>'
                  +(f'<div>{e(au)}</div>' if au else '')+'<div>'+''.join(paras)+'</div></body></html>')
            if not os.path.exists(p1): open(p1,'w').write(page)
        page=open(p1).read()
        os.makedirs(f'/mnt/user-data/outputs/tlib_rated1/{year}',exist_ok=True)
        open(f"/mnt/user-data/outputs/tlib_rated1/{year}/{j['aid']}.html",'w').write(page)
        words=len(re.findall(r"\w[\w'’-]*",text))
        mg=d.get('mentions', bool(re.search(r'gabriel',text,re.I)))
        rec.update({'verified':True,'mentions_gabriel':mg})
        if mg or d.get('tone'):
            rec.update({'fulltext_tone':d['tone'],'fulltext_why':d['why'],'tone_agrees_with_current':d['tone']==j['current_tone']})
        if j.get('need_topic') and d.get('topic'): rec['topic']=d['topic']
        if j.get('need_bills'): rec['bills']=d.get('bills','')
        for k in ('other_bills','other_bills_note','flag','note'):
            if d.get(k): rec[k]=d[k]
        if not j.get('author') and d.get('author'): rec['author']=d['author']
        rec['words']=words
        rec['sha256']=hashlib.sha256(page.encode()).hexdigest()
    open(OUT,'a').write(json.dumps(rec,ensure_ascii=False)+'\n'); done.add(sid)
    print(sid, rec.get('fulltext_tone') or rec.get('flag'), rec.get('words',''), rec.get('mentions_gabriel',''), rec.get('tone_agrees_with_current',''))
