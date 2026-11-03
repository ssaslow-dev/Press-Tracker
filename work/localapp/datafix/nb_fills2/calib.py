import sys,pickle,collections,re
sys.path.insert(0,'/home/user/Press-Tracker/work/localapp/datafix'); sys.path.insert(0,'/home/user/Press-Tracker/work/localapp/datafix/nb_fills2')
from common import *
from nbhead import *
import authorsplit as A
T=pickle.load(open(S+'/nb_fills2_texts.pkl','rb'))
h,rows=load_coverage()
def pdfs(r):
    out=[]
    for c in ('File name','File name 2'):
        f=s(r[c])
        if f.startswith('nb') and f.endswith('.pdf'):
            p=lib_path(f,r['Date'])
            if p in T: out.append((c,f,p))
    return out
agree=collections.defaultdict(collections.Counter); dis=collections.defaultdict(list)
for r in rows:
    P=pdfs(r)
    if len(P)!=1: continue
    hd=read_header(T[P[0][2]])
    if not hd: continue
    wp = s(r['Edition'])=='Web + Print'
    chk={'Section':hd['section'],'Page':hd['page'],'Date':hd['date']}
    for col,val in chk.items():
        cur=s(r[col])
        if cur and val: 
            ok = cur.lower()==val.lower() or cur[:10]==val
            agree[col][ok]+=1
            if not ok and len(dis[col])<12: dis[col].append((aid(r),cur,val))
    # outlet city from source
    m=re.search(r'\(([^()]*?),\s*([A-Z]{2})\)\s*$',hd['source'])
    if m and s(r['Outlet city']):
        ok=s(r['Outlet city']).lower()==m.group(1).lower(); agree['city'][ok]+=1
        if not ok and len(dis['city'])<15: dis['city'].append((aid(r),s(r['Outlet city']),hd['source']))
    if s(r['Author 1']) and hd['author']:
        pa=A.parse_byline(hd['author'],s(r['Outlet']))
        ok = bool(pa['authors']) and A.author_key(pa['authors'][0])==A.author_key(s(r['Author 1']))
        agree['author1'][ok]+=1
        if not ok and len(dis['author1'])<25: dis['author1'].append((aid(r),s(r['Author 1']),hd['author'],pa['authors']))
        ok2 = s(r['Author / byline']).lower()==hd['author'].lower(); agree['byline_raw'][ok2]+=1
        if not ok2 and len(dis['byline_raw'])<10: dis['byline_raw'].append((aid(r),s(r['Author / byline']),hd['author']))
    # edition
    web='web edition' in hd['source'].lower()
    inf = 'Web' if web else ('Print' if hd['page'] else '')
    cur=s(r['Edition'])
    if cur and inf and not wp:
        ok=cur==inf; agree['edition'][ok]+=1
        if not ok and len(dis['edition'])<12: dis['edition'].append((aid(r),cur,hd['source'],hd['page']))
for k,v in agree.items(): print(k,dict(v))
for k,v in dis.items():
    print('---',k)
    for x in v: print(x)
