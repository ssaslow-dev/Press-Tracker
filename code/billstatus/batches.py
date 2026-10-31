import json,re,os
L='/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib'
rows=json.load(open(L+'/work/gabriel_bills_leginfo.json'))['rows']
sel=[r for r in rows if r['role']=='author' or r['role'].startswith('author (co-lead')]
C=L+'/work/billstatus_cache'
todo=[]
for r in sel:
    bid=re.search(r'bill_id=(\w+)',r['url']).group(1)
    if not os.path.exists(f'{C}/{bid}.json'): todo.append(bid)
print(len(sel),'selected;',len(todo),'todo')
for i in range(0,len(todo),10):
    print(json.dumps(['https://leginfo.legislature.ca.gov/faces/billHistoryClient.xhtml?bill_id='+b for b in todo[i:i+10]]))
