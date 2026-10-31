# Parse cached leginfo history pages -> bill_milestones.json / .csv (+ coverage sanity counts).
import json, re, os, csv, collections, datetime
L = '/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib'
C = L + '/work/billstatus_cache'
OUT = L + '/work/out'
MONTHS = {m: i for i, m in enumerate(['January','February','March','April','May','June','July','August',
                                      'September','October','November','December'], 1)}

rows = json.load(open(L + '/work/gabriel_bills_leginfo.json'))['rows']
sel = [r for r in rows if r['role'] == 'author' or r['role'].startswith('author (co-lead')]

def actions(text):
    acts = re.findall(r'^\|\s*(\d\d/\d\d/\d\d)\s*\|\s*(.*?)\s*\|\s*$', text, re.M)
    if not acts:
        acts = re.findall(r'^(\d\d/\d\d/\d\d)\n(.+)$', text, re.M)
    out = []
    for d, a in acts:
        m, dd, yy = d.split('/')
        out.append((f'20{yy}-{m}-{dd}', a.strip()))
    return list(reversed(out))  # page lists newest first (incl. within a day)


TERM = re.compile(r'\s+(?:pursuant|with recommendation|for assignment|Read second time|Amended\.?$)|\s*\(|\.?\s*$')
def com_list(after):
    m = TERM.search(after)
    return after[:m.start()].strip().rstrip('.').strip() if m else after.strip().rstrip('.')
def com_names(a):
    # all 'Com. on X' / 'Coms. on X' captures in an action line
    return [com_list(m.group(1)) for m in re.finditer(r'Coms?\. on (.+)$', a)]

# known single committee names, for splitting "Coms. on A, B and C"
known = set()
cache = {}
for r in sel:
    bid = re.search(r'bill_id=(\w+)', r['url']).group(1)
    d = json.load(open(f'{C}/{bid}.json'))
    cache[bid] = d
    for _, a in actions(d['text']):
        for m in re.finditer(r'(?:Referred|re-referred|Re-referred|re-refer) to Com\. on (.+)$', a):
            known.add(com_list(m.group(1)))
known = sorted(known, key=len, reverse=True)

def split_coms(s):
    s = s.strip().rstrip('.')
    if s in known: return [s]
    out = []
    while s:
        s = re.sub(r'^(,\s*|and\s+)', '', s).strip()
        if not s: break
        for k in known:
            if s.startswith(k):
                out.append(k); s = s[len(k):].lstrip('.').strip(); break
        else:
            parts = re.split(r'\s+and\s+|,\s+', s, maxsplit=1)
            out.append(parts[0].rstrip('.')); s = parts[1] if len(parts) > 1 else ''
    return out

def hearing_date(act_date, txt):
    m = re.search(r'\)\s*\((January|February|March|April|May|June|July|August|September|October|November|December) (\d+)\)', txt)
    if not m: return act_date
    y = int(act_date[:4]); mo = MONTHS[m.group(1)]
    if mo > int(act_date[5:7]): y -= 1
    return f'{y}-{mo:02d}-{int(m.group(2)):02d}'

def votes(txt):
    m = re.search(r'Ayes (\d+)\.\s*Noes (\d+)', txt)
    return f' (Ayes {m.group(1)}, Noes {m.group(2)})' if m else ''

OTHER = {'Assembly': 'Senate', 'Senate': 'Assembly'}

def parse(bill, session, acts):
    origin = 'Senate' if bill.startswith('S') else 'Assembly'
    house = origin; cur = []; ms = []; floor_houses = set()
    def add(date, step, h, detail, committee=''):
        ms.append({'date': date, 'step': step, 'house': h, 'committee': committee, 'detail': detail})
    for i, (d, a) in enumerate(acts):
        al = a.lower()
        if a.startswith('(pending'): continue
        if i == 0 or a.startswith('Introduced') or (a.startswith('Read first time. To print') and not any(x['step'] == 'introduced' for x in ms)):
            if not any(x['step'] == 'introduced' for x in ms):
                add(d, 'introduced', origin, a)
        if re.match(r'In (Senate|Assembly)\b', a):
            house = re.match(r'In (Senate|Assembly)', a).group(1)
        m = re.search(r'^Referred to Coms?\. on (.+)$', a) or re.search(r'Introduced\..*Referred to Coms?\. on (.+)$', a)
        if m and 'rescinded' not in al:
            cur = split_coms(com_list(m.group(1)))
        m = re.search(r'[Rr]e-refer(?:red)? to Coms?\. on (.+)$', a)
        if a.startswith('From committee:') and 'Ayes' in a:
            com = cur[0] if cur else ''
            res = re.sub(r'\s*\(Ayes.*$', '', a[len('From committee:'):]).strip().rstrip('.')
            res = re.sub(r' and re-refer to Com\..*$', ' and re-refer', res)
            add(hearing_date(d, a), 'committee vote', house, res + votes(a), com)
            if cur: cur = cur[1:]
        elif a.startswith('From committee: Be ordered to second reading') or a.startswith('From committee: Ordered to third reading'):
            add(d, 'committee action', house, a[len('From committee: '):].rstrip('.'), cur[0] if cur else '')
        elif a.startswith('From committee: That the measure be returned'):
            add(hearing_date(d, a), 'committee vote', house, 'Returned to floor' + votes(a), cur[0] if cur else '')
        if m:
            nxt = split_coms(com_list(m.group(1)))
            cur = nxt + [c for c in cur if c not in nxt]
        if 'referred to appr. suspense file' in al or 'referred to suspense file' in al or 'referred to appr suspense file' in al:
            add(d, 'suspense file', house, a, 'APPR')
            cur = ['APPR'] + [c for c in cur if c != 'APPR']
        if 'held under submission' in al:
            add(d, 'held in committee', house, a, cur[0] if cur else '')
        # floor votes
        fm = re.search(r'Read third time\.(?: Urgency clause adopted\.)? Passed\.', a) or \
             re.match(r'(Adopted and to (Senate|Assembly))', a) or re.match(r'Read\. Adopted', a)
        if fm and 'Reconsideration' not in a:
            add(d, 'floor vote', house, ('Passed' if 'Passed' in a else 'Adopted') + votes(a))
            floor_houses.add(house)
            if re.search(r'Ordered to the (Senate|Assembly)|to (Senate|Assembly)', a) and 'to Assembly' not in a.split('Adopted and')[0][:0]:
                pass
        if re.search(r'(Senate|Assembly) amendments concurred in', a):
            add(d, 'concurrence vote', house, 'Concurred' + votes(a))
        if re.search(r'[Oo]rdered to [Ee]ngrossing and [Ee]nrolling|To Engrossing and Enrolling', a):
            if not any(x['step'] == 'passed both houses' for x in ms):
                add(d, 'passed both houses', '', a)
        if a.startswith('Enrolled and presented to the Governor'):
            add(d, 'enrolled', '', a)
        if a.startswith('Approved by the Governor'):
            add(d, 'signed', '', 'Approved by the Governor')
        cm = re.search(r'Chaptered by Secretary of State[.\s-]+(Res\. )?Chapter (\d+), Statutes of (\d+)', a)
        if cm:
            add(d, 'chaptered', '', f"{'Res. ' if cm.group(1) else ''}Chapter {cm.group(2)}, Statutes of {cm.group(3)}")
        if a.startswith('Vetoed by Governor'):
            add(d, 'vetoed', '', a)
        if a.startswith('Ordered to inactive file'):
            add(d, 'inactive file', house, a)
        if re.match(r'Died|From (Senate )?committee without further action|From committee: Filed with the Chief Clerk|Filed with the Chief Clerk', a):
            if not any(x['step'] == 'died' for x in ms):
                add(d, 'died', house, a)
    return ms

SESSION_END = {'2017-2018': '2018-11-30', '2019-2020': '2020-11-30', '2021-2022': '2022-11-30',
               '2023-2024': '2024-11-30', '2025-2026': '2026-11-30', '2025-2026 (1st Ex. Sess.)': '2026-11-30'}
TODAY = '2026-10-27'

def final_status(bill, session, ms, acts):
    steps = {m['step']: m for m in ms}
    if 'chaptered' in steps: return f"Chaptered ({steps['chaptered']['detail']}, {steps['chaptered']['date']})"
    if 'vetoed' in steps: return f"Vetoed ({steps['vetoed']['date']})"
    if bill.startswith('HR') and any(m['step'] == 'floor vote' for m in ms):
        return f"Adopted ({[m for m in ms if m['step']=='floor vote'][-1]['date']})"
    last = acts[-1][1]
    if 'died' in steps:
        held = [m for m in ms if m['step'] == 'held in committee']
        if held: return f"Died - held in committee ({held[-1]['committee'] or 'APPR'}, {held[-1]['date']})"
        return f"Died - {steps['died']['detail'].rstrip('.')} ({steps['died']['date']})"
    held = [m for m in ms if m['step'] == 'held in committee']
    if held and acts[-1][1].lower().startswith('in committee: held'):
        return f"Held in committee ({held[-1]['committee'] or 'APPR'}, {held[-1]['date']})"
    if 'inactive file' in steps and acts[-1][1].startswith('Ordered to inactive'):
        return f"On inactive file ({steps['inactive file']['date']})"
    if SESSION_END[session] < TODAY:
        return f"Died - session ended (last action {acts[-1][0]}: {last.rstrip('.')})"
    return f"Pending (last action {acts[-1][0]}: {last.rstrip('.')})"

def comkey(c): return re.sub(r'[\s,.]', '', c).upper()
bills = []
for r in sel:
    bid = re.search(r'bill_id=(\w+)', r['url']).group(1)
    d = cache[bid]; acts = actions(d['text'])
    if not acts: raise SystemExit('no actions ' + bid)
    ms = parse(r['bill'], r['session'], acts)
    title = r['title'] or re.sub(r'^Bill History - \S+\s*', '', d.get('title', ''))
    bills.append({'bill': r['bill'], 'session': r['session'], 'title': title, 'role': r['role'],
                  'bill_id': bid, 'status_url': r['url'],
                  'history_url': f'https://leginfo.legislature.ca.gov/faces/billHistoryClient.xhtml?bill_id={bid}',
                  'milestones': ms, 'final_status': final_status(r['bill'], r['session'], ms, acts),
                  'leginfo_status_in_list': r['status'], 'n_history_actions': len(acts)})

# normalise committee spellings: most common display form per key, with closing period
forms = collections.defaultdict(collections.Counter)
for b in bills:
    for m in b['milestones']:
        if m['committee']: forms[comkey(m['committee'])][m['committee']] += 1
canon = {k: v.most_common(1)[0][0].rstrip('.') + '.' for k, v in forms.items()}
for b in bills:
    for m in b['milestones']:
        if m['committee']: m['committee'] = canon[comkey(m['committee'])]

# ---- coverage counts (Bills column; session disambiguated by story date)
import openpyxl
wb = openpyxl.load_workbook(L + '/work/coverage_current.xlsx', read_only=True)
ws = wb['Coverage']; h = list(next(ws.iter_rows(max_row=1, values_only=True)))
bi, di, si, oi = h.index('Bills'), h.index('Date'), h.index('Story ID'), h.index('Original or reprint')
by_num = collections.defaultdict(list)
for b in bills: by_num[b['bill']].append(b)
SESS_START = {'2017-2018': '2017-01-01', '2019-2020': '2018-12-01', '2021-2022': '2020-12-01',
              '2023-2024': '2022-12-01', '2025-2026': '2024-12-01', '2025-2026 (1st Ex. Sess.)': '2024-12-01'}
art = collections.Counter(); stories = collections.defaultdict(set); unmatched = collections.Counter()
def norm(x): return re.sub(r'\s+', ' ', x.strip().upper().replace('-', ' ')).replace('ABX1 ', 'ABX1-').replace('SBX1 ', 'SBX1-')
for row in ws.iter_rows(min_row=2, values_only=True):
    if not row[bi]: continue
    dt = row[di]; ds = dt.strftime('%Y-%m-%d') if isinstance(dt, (datetime.date, datetime.datetime)) else str(dt or '')[:10]
    for num in re.split(r'[;,]', str(row[bi])):
        num = norm(num)
        if not num: continue
        cands = by_num.get(num)
        if not cands: unmatched[num] += 1; continue
        # pick the latest session that started on/before the story date (stories after a session can still discuss its bills)
        pick = [c for c in cands if not ds or SESS_START[c['session']] <= ds]
        b = (sorted(pick, key=lambda c: SESS_START[c['session']])[-1] if pick else sorted(cands, key=lambda c: SESS_START[c['session']])[0])
        k = (b['bill'], b['session']); art[k] += 1; stories[k].add(row[si])
for b in bills:
    k = (b['bill'], b['session'])
    b['tracker_articles'] = art[k]; b['tracker_stories'] = len(stories[k])

json.dump({'generated': TODAY, 'source': 'leginfo billHistoryClient pages via TinyFish fetch_content (ttl 0)',
           'scope': 'role author or author (co-lead) in work/gabriel_bills_leginfo.json; coauthor/principal coauthor skipped',
           'steps': ['introduced','committee vote','committee action','suspense file','held in committee','floor vote',
                     'concurrence vote','passed both houses','enrolled','signed','vetoed','chaptered','inactive file','died'],
           'notes': ['committee name is inferred from the referral sequence (history lines say only "From committee:"); best-effort',
                     'committee-vote date is the hearing date in the parenthetical; floor/other dates are the action date',
                     'tracker_articles / tracker_stories count rows of the Coverage tab whose Bills cell names the bill; same bill numbers in different sessions are split by story date'],
           'bills': bills, 'unmatched_tracker_bill_numbers': dict(unmatched)},
          open(OUT + '/bill_milestones.json', 'w'), indent=1, ensure_ascii=False)
with open(OUT + '/bill_milestones.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['bill', 'session', 'title', 'role', 'date', 'step', 'house', 'committee', 'detail', 'final_status', 'history_url'])
    for b in bills:
        for m in b['milestones']:
            w.writerow([b['bill'], b['session'], b['title'], b['role'], m['date'], m['step'], m['house'], m['committee'], m['detail'], b['final_status'], b['history_url']])
print(len(bills), 'bills', sum(len(b['milestones']) for b in bills), 'milestones')
print(collections.Counter(b['final_status'].split(' (')[0].split(' - ')[0] for b in bills))
print('unmatched', unmatched.most_common(20))
