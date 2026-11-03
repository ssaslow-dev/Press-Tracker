"""Check 1: Reprint rows in another language than their Original. Read-only. Run: python3 -I check_translations.py"""
import sys, os, csv, collections, re
sys.path.insert(0, '/home/user/Press-Tracker/work/localapp/datafix')
from common import *
import reprint_rule as rr

OUT = os.path.dirname(os.path.abspath(__file__))
h, R = load_coverage()

STOP = {
 'English': set('the of to in and for a is on with at by from as that this it are be will new how what who why not after over into about says say bill law state'.split()),
 'Spanish': set('el la los las de del que para por con una un en y es se su al lo como más nueva nuevo ley sobre firma tras'.split()),
 'Portuguese': set('o os as de do da dos das que para por com uma um em e é se não mais nova novo lei sobre assinou'.split()),
 'French': set('le la les de des du que pour par avec une un en et est se au aux sur nouvelle loi californie veulent'.split()),
}
def detect_text(t):
    t = s(t)
    if re.search(r'[\u4e00-\u9fff]', t): return 'Chinese'
    if re.search(r'[\uac00-\ud7af]', t): return 'Korean'
    if re.search(r'[\u0400-\u04ff]', t): return 'Russian'
    if re.search(r'[\u0590-\u05ff]', t): return 'Hebrew'
    if re.search(r'[\u0600-\u06ff]', t): return 'Persian'
    w = re.findall(r"[a-záéíóúñãõçàèêâîôûœ']+", t.lower())
    if len(w) < 3: return ''
    sc = {k: sum(1 for x in w if x in v) for k, v in STOP.items()}
    if re.search(r'[ãõç]', t.lower()): sc['Portuguese'] += 2
    if re.search(r'[ñ¿¡]', t.lower()): sc['Spanish'] += 2
    best = max(sc, key=sc.get)
    srt = sorted(sc.values(), reverse=True)
    return best if srt[0] >= 2 and srt[0] > srt[1] else ''
def detect(r): return detect_text(r.get('Headline'))

by = collections.defaultdict(list)
for r in R: by[r['Story ID']].append(r)
cands = []
for sid, rs in by.items():
    o = [r for r in rs if r['Original or reprint'] == 'Original']
    if len(o) != 1: continue
    o = o[0]
    for r in rs:
        if r['Original or reprint'] == 'Original': continue
        lo, lb = s(o['Language']) or 'English', s(r['Language'])
        guessed = ''
        if not lb:
            g = detect(r)
            if g and g != lo: lb, guessed = g, ' (language cell blank; guessed from headline)'
            else: continue
        if lo == lb: continue
        cands.append((o, r, lo, lb, guessed))

texts_cache = {}
def text_of(r):
    k = aid(r)
    if k not in texts_cache:
        texts_cache[k] = read_text(lib_path(r.get('File name'), r.get('Date')))
    return texts_cache[k]

rows = []
for o, r, lo, lb, guessed in cands:
    ow = dict(o); ow['Language'] = lo
    rw = dict(r); rw['Language'] = lb
    ot, rt = text_of(o), text_of(r)
    # credit evidence: the translated row naming the Original's service (byline/Author title/NB author/credit line in its text)
    cr = rr.credit_of(rw, rt)
    cr_o = rr.credit_of(ow, ot)
    credited = rr.origin_credits([ow, rw], {ow["Article ID"]: ot, rw["Article ID"]: rt})[0]
    try:
        res = rr.pair_class(ow, rw, verdict=None, credited=credited, texts={rw['Article ID']: rt, ow['Article ID']: ot})
    except Exception as e:
        res = {'kind': 'error', 'note': str(e), 'conf': ''}
    do, db = rr.todate(o['Date']), rr.todate(r['Date'])
    gap = abs((do - db).days) if do and db else None
    hs = rr.translated_headline_sim(ow, rw)
    same = bool(rr.people(o['Author / byline']) & rr.people(r['Author / byline']))
    rows.append(dict(story=s(o['Story ID']), orig=aid(o), orig_outlet=s(o['Outlet']), orig_date=s(o['Date'])[:10], orig_lang=lo,
                     orig_by=s(o['Author / byline']), orig_head=s(o['Headline']), rep=aid(r), rep_tab_status=s(r['Original or reprint']),
                     rep_outlet=s(r['Outlet']), rep_date=s(r['Date'])[:10], rep_lang=lb + guessed, rep_by=s(r['Author / byline']),
                     rep_head=s(r['Headline']), rep_th=s(r['Translated Headline']), gap=gap, hs=None if hs is None else round(hs, 2),
                     same_byline=same, credit='; '.join(f"{k}: {v[0]}" for k, v in cr.items()),
                     kind=res['kind'], note=res['note'], conf=res.get('conf', ''), text=bool(rt), r=r, o=o))

def classify(x):
    if x['rep_tab_status'] != 'Reprint': return 'unverified'
    if x['kind'] == 'translation': return 'meets'
    ol, rl = detect_text(x['orig_head']), detect_text(x['rep_head'])
    cl_o, cl_r = x['orig_lang'], x['rep_lang'].split(' ')[0]
    if rl and rl != cl_r and rl == cl_o: x['why'] = f'Language cell of the reprint says {cl_r} but its headline is {rl}'; return 'language-cell'
    if ol and ol != cl_o and ol == cl_r: x['why'] = f'Language cell of the Original says {cl_o} but its headline is {ol}'; return 'language-cell'
    close = x['gap'] is not None and x['gap'] <= 2
    linked = x['same_byline'] or bool(x['credit'])
    if close and linked and x['hs'] is None:
        x['why'] = 'same byline/credit and within 2 days, but no translated headline on file to compare'; return 'cannot-test'
    if close and linked and x['hs'] < 0.5:
        x['why'] = 'same byline/credit and within 2 days, but the translated headline matches weakly (%.2f)' % x['hs']; return 'weak-headline'
    if linked and not close:
        x['why'] = 'same byline/credit but %s days apart (limit 2)' % x['gap']; return 'too-late'
    if x['kind'] == 'never': x['why'] = 'wire against wire is never a reprint'; return 'own'
    x['why'] = 'no credit and no shared byline' + ('' if close else ', %s days apart' % x['gap']); return 'own'
for x in rows: x['cls'] = classify(x)
cnt = collections.Counter(x['cls'] for x in rows)
print(cnt)
props = []
fixable = [x for x in rows if x['cls'] in ('own', 'too-late')]
groups = collections.defaultdict(list)
for x in fixable: groups[(x['story'], x['rep_lang'].split(' ')[0])].append(x)
for (sid, lang), xs in sorted(groups.items()):
    xs.sort(key=lambda x: (x['rep_date'], x['rep']))
    new = f'(new, for {sid}/{lang})'
    for k, x in enumerate(xs):
        conf = 'medium' if x['cls'] == 'own' and not x['same_byline'] and len(xs) < 3 else 'low'
        ev = f"{x['rep_lang']} copy of {x['orig_outlet']} {x['orig_lang']} Original {x['orig']} ({x['orig_date']}): {x['why']}; headline match {x['hs']}"
        if k == 0: props.append(dict(tab='Coverage', article_id=x['rep'], column='Original or reprint', current='Reprint', new='Original', confidence=conf, evidence=ev))
        props.append(dict(tab='Coverage', article_id=x['rep'], column='Story ID', current=sid, new=new, confidence=conf, evidence=ev if k else 'earliest of its language group becomes the Original of a new story'))
for x in rows:
    if x['cls'] == 'cannot-test':
        props.append(dict(tab='Coverage', article_id=x['rep'], column='Translated Headline', current='', new='(translate at Update station, then re-test the rule)', confidence='low', evidence=x['why']))
    if x['cls'] == 'language-cell':
        cell = 'Language'
        aid_, cur = (x['rep'], x['rep_lang'].split(' ')[0]) if 'Language cell of the reprint' in x['why'] else (x['orig'], x['orig_lang'])
        props.append(dict(tab='Coverage', article_id=aid_, column=cell, current=cur, new='(set from text; recorded override "Language from text")', confidence='medium', evidence=x['why']))
with open(OUT + '/proposals.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['tab', 'article_id', 'column', 'current', 'new', 'confidence', 'evidence']); w.writeheader(); w.writerows(props)
with open(OUT + '/all_checked.csv', 'w', newline='') as f:
    cols = ['cls', 'why', 'story', 'orig', 'orig_outlet', 'orig_date', 'orig_lang', 'orig_by', 'orig_head', 'rep', 'rep_tab_status', 'rep_outlet', 'rep_date', 'rep_lang', 'rep_by', 'rep_head', 'rep_th', 'gap', 'hs', 'same_byline', 'credit', 'kind']
    w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(sorted(rows, key=lambda x: (x['cls'], x['story'])))
print(len(props), 'proposal lines;', len(groups), 'new-story groups')
