"""billmatch.py - the "names a bill" rule shared by code/sheet_task.py (queue_after / rubric checks), code/build_data.py
(billsinfo extras) and the acceptance checks. Ported from work/tmp_tags_apply/rules.py (2026-10-28 tags pass).
Data: gabriel_bills_leginfo.json (bills, sessions, roles, titles) + bills_extra.json (introduction dates, popular names,
grant-program flag, budget-act flag, issue) next to this file. Nothing here touches the sheet."""
import re, json, os, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
def _load(name, alt=''):
    for p in (os.path.join(HERE, name), alt):
        if p and os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    return {'rows': []}
BL = _load('gabriel_bills_leginfo.json')['rows']
_EX = _load('bills_extra.json')
_EXTRA = {(r['bill'], r['session']): r for r in _EX.get('rows', [])}

def sess_key(s):  # '2025-2026 (1st Ex. Sess.)' -> '2025-2026x'
    return s[:9] + ('x' if 'Ex' in s else '')
def sess_start(s):
    return s[:4] + '-12-01' if 'Ex' not in s else s[:4] + '-12-02'

INFO = {}   # bill -> list of dicts, one per session
for r in BL:
    ex = _EXTRA.get((r['bill'], r['session']), {})
    INFO.setdefault(r['bill'], []).append({'bill': r['bill'], 'session': r['session'], 'sk': sess_key(r['session']), 'role': r['role'], 'title': r['title'],
                                           'authored': r['role'].startswith('author'), 'intro': ex.get('introduced') or sess_start(r['session']),
                                           'intro_exact': bool(ex.get('introduced_exact')), 'program': ex.get('program', ''), 'topic': ex.get('topic')})

BUDGET_ACTS = {b['bill'] for b in BL if re.match(r'Budget Acts? of', b['title']) and b['role'].startswith('author')} - {'ABX1-4'}   # ABX1-4 = the $2.5B wildfire relief package, tagged like a policy bill (4 sheet rows)

def story_sess(d):
    """session key whose dates contain the story date (regular session: Dec 1 of even year .. Nov 30 of next even year)"""
    y, m = int(d[:4]), int(d[5:7])
    s = y if y % 2 else y - 1
    if y % 2 == 0 and m == 12: s = y + 1
    return f'{s}-{s + 1}'

def resolve(bill, date, ex=False):
    """the (bill, session) row a number names on a story of this date: the session containing the date, else the latest earlier one.
    Returns (info, same_session) or (None, False). Extraordinary-session numbers (ABX1-4) resolve to their own rows."""
    cands = INFO.get(bill, [])
    if not cands: return None, False
    ss = story_sess(date)
    same = [c for c in cands if c['sk'].rstrip('x') == ss and (c['sk'].endswith('x') == ex)]
    if same: return same[0], True
    earlier = [c for c in cands if c['sk'][:4] < ss[:4]]
    if earlier: return max(earlier, key=lambda c: c['sk']), False
    return None, False

# ---------- number forms ----------
PFX = {'AB': r'(?:A\.?\s?B\.?|Assembly\s+Bill|Asm\.?\s+Bill)', 'SB': r'(?:S\.?\s?B\.?|Senate\s+Bill)',
       'ACR': r'(?:ACR|Assembly\s+Concurrent\s+Resolution)', 'ACA': r'(?:ACA|Assembly\s+Constitutional\s+Amendment)',
       'AJR': r'(?:AJR|Assembly\s+Joint\s+Resolution)', 'SCR': r'(?:SCR|Senate\s+Concurrent\s+Resolution)', 'SJR': r'SJR', 'HR': r'HR'}
NUM_RX = re.compile(r'(?<![A-Za-z0-9])(ABX\s?\d|SBX\s?\d|' + '|'.join(PFX.values()) + r')\s*(?:\(\s*(?:AB|SB)\s*\)\s*)?(?:No\.?\s*)?[-–]?\s*(\d{1,2}\.\d{1,2}|\d{1,4})(?!\d)', re.I)
# Spanish / CJK / Korean forms
ES_RX = re.compile(r'Proyecto\s+de\s+Ley(?:\s+de\s+la\s+Asamblea)?\s*(?:\(?\s*(AB|SB)\s*\)?\s*)?(\d{1,4})(?!\d)|Ley\s*\(?\s*(AB|SB)\s*\)?\s*(\d{1,4})(?!\d)|Ley\s+(\d{1,4})\s+de\s+la\s+(Asamblea|Senado)', re.I)
CJK_RX = re.compile(r'(?:第\s*(\d{1,4})\s*[号號]\s*(眾議院|众议院|州眾議院|州众议院|参议院|參議院)?\s*法案|(眾議院|众议院|州眾議院|州众议院)\s*(?:第)?\s*(\d{1,4})\s*[号號]?\s*法案)')
KO_RX = re.compile(r'(?:(AB|SB)\s*)?(\d{1,4})\s*호\s*(?:법안|주\s*하원\s*법안)')
GAB_RX = re.compile(r'Gabriel|גבריאל|加布里埃尔|加布里爾|가브리엘|Габриэл', re.I)

def _pfx(p):
    p = re.sub(r'[\s.]', '', p).upper()
    if p.startswith('ASSEMBLYBILL') or p.startswith('ASMBILL'): return 'AB'
    if p.startswith('SENATEBILL'): return 'SB'
    if p.startswith('ASSEMBLYCONCURRENT'): return 'ACR'
    if p.startswith('ASSEMBLYCONSTITUTIONAL'): return 'ACA'
    if p.startswith('ASSEMBLYJOINT'): return 'AJR'
    if p.startswith('SENATECONCURRENT'): return 'SCR'
    return p

def numbers(txt):
    """-> list of (bill, span) for every bill number written in the text, any form"""
    out = []
    for m in NUM_RX.finditer(txt):
        p, n = _pfx(m.group(1)), m.group(2).replace('.', '')
        if p.startswith('ABX') or p.startswith('SBX'):
            out.append((f'{p[:3]}{p[3:]}-{int(n)}', m.span()))
        else:
            out.append((f'{p} {int(n)}', m.span()))
    for m in ES_RX.finditer(txt):
        if m.group(2): out.append((f"{(m.group(1) or 'AB').upper()} {int(m.group(2))}", m.span()))
        elif m.group(4): out.append((f"{m.group(3).upper()} {int(m.group(4))}", m.span()))
        else: out.append((('SB' if m.group(6).lower() == 'senado' else 'AB') + f' {int(m.group(5))}', m.span()))
    for m in CJK_RX.finditer(txt):
        n = m.group(1) or m.group(4); h = m.group(2) or m.group(3) or ''
        out.append((('SB' if '参' in h or '參' in h else 'AB') + f' {int(n)}', m.span()))
    for m in KO_RX.finditer(txt):
        out.append((f"{(m.group(1) or 'AB').upper()} {int(m.group(2))}", m.span()))
    return out

# ---------- titles / popular names (incl. translations) ----------
TITLES = {}
for _r in _EX.get('rows', []):
    if _r.get('titles'): TITLES[_r['bill']] = _r['titles']
TITLE_RX = {b: re.compile('|'.join(ps), re.I) for b, ps in TITLES.items()}

# ---------- programs: a grant program named -> the Gabriel bill behind it (Sammy 2026-10-28: NSGP -> its funding bill) ----------
# NSGP: the most recent of his NSGP bills introduced on or before the story date (AB 1548 created it; 1664 / 1185 / 1836 extended or funded it)
PROGRAMS = {k: {'rx': re.compile(v['regex'], re.I), 'bills': v['bills']} for k, v in _EX.get('programs', {}).items()}
PROGRAM_BILLS = {b for p in PROGRAMS.values() for b in p['bills']} | {'AB 2378', 'AB 166', 'AB 1929'}   # program flag: release matching must not spawn tags

def program_bill(code, date):
    best = None
    for b in PROGRAMS[code]['bills']:
        for c in INFO[b]:
            if c['intro'] <= date and (best is None or c['intro'] > best['intro']): best = c
    return best

# coauthor tie cue within the window around the mention
TIE_RX = re.compile(r'co-?author|co-?sponsor|co-?written|co-?wrote|principal|jointly?\s+author|author|sponsor|introduc|carried|carry|present|unveil', re.I)
KEYWORDS = {  # cross-session safety: the bill's subject must be in the text when the number comes from an earlier session
    'AB 418': r'dye|additive|food|brominated|skittles|titanium', 'AB 2316': r'dye|school|food', 'AB 1264': r'ultra-?processed|school|food',
    'AB 587': r'social media|content moderation|platform', 'AB 28': r'firearm|gun|ammunition|excise', 'AB 1548': r'security grant|nonprofit',
    'AB 1664': r'security grant|nonprofit', 'AB 1185': r'security grant|nonprofit', 'AB 2867': r'art|holocaust|nazi|looted',
    'AB 61': r'outdoor|dining|alcohol|parklet|restaurant', 'AB 1217': r'outdoor|dining|parklet|restaurant', 'AB 2000': r'sideshow|street racing|speed',
    'AB 1127': r'glock|pistol|firearm|gun', 'AB 2432': r'victim', 'AB 57': r'hate crime', 'AB 977': r'homeless', 'AB 1487': r'eviction|homeless|legal',
    'AB 468': r'loot', 'AB 1305': r'carbon|offset', 'AB 165': r'restraining|firearm|gun', 'AB 2236': r'hate crime', 'AB 876': r'microstamp|firearm|gun',
    'AB 624': r'student|hotline|id card', 'AB 309': r'mental health|student', 'AB 1474': r'sentenc|incarcerat', 'ACR 51': r'sally ride|highway'}

def names_bills(txt, date):
    """Apply the 'names a bill' rule to one text. -> dict bill -> {'how','ev','conf'} (conf high/medium/low)"""
    found = {}; veto = {}
    def put(b, how, ev, conf):
        if how == 'number, text credits another author': veto[b] = ev
        if b not in found or ('high', 'medium', 'low').index(conf) < ('high', 'medium', 'low').index(found[b]['conf']):
            found[b] = {'how': how, 'ev': ev[:160], 'conf': conf}
    for bill, (a, z) in numbers(txt):
        ex = '-' in bill
        info, same = resolve(bill, date, ex)
        if not info: continue
        win = txt[max(0, a - 300): z + 300]
        if bill in BUDGET_ACTS:
            put(bill, 'number (Budget Act)', txt[max(0, a - 60): z + 60], 'low'); continue
        if info['intro'] > date:
            put(bill, 'number BEFORE introduction', txt[max(0, a - 60): z + 60], 'low'); continue
        if info['authored']:
            after = txt[z: z + 110]
            other = re.search(r"^([^.;]{0,24}?)\b(?:by|from|de\s+(?:la|el)\s+asamble[íi]sta)\s+(?:(?:Assembly\s*(?:members?|woman|man)|Asm\.?|Sen\.?|Senators?|State\s+Sen\.?|Rep\.?|Assemblyman|Assemblywoman)\s+)?([A-Z][\w.'-]+(?:\s+[A-Z][\w.'-]+){0,3})", after)
            if other and not re.search(r'signed|vetoed|approved|announced|administered|funded|passed|adopted', other.group(1), re.I) \
               and not GAB_RX.search(after[: other.end() + 60]) and 'co-lead' not in info['role']:
                put(bill, 'number, text credits another author', txt[max(0, a - 60): z + 110], 'low'); continue
            # legislative-tracker form: "AB 1546  Vehicles: driving under the influence. Schultz (D-Burbank)" -> another member's bill of that number
            other2 = re.search(r"^[\s\S]{0,160}?\b([A-Z][A-Za-z'’-]+)\s*\((?:D|R)\s*[-–]", txt[z: z + 200])
            if other2 and not GAB_RX.search(other2.group(1)) and not GAB_RX.search(txt[max(0, a - 200): z + 200]) and 'co-lead' not in info['role']:
                put(bill, 'number, text credits another author', txt[max(0, a - 60): z + 110], 'low'); continue
            dense = len({bb for bb, _ in numbers(txt)}) >= 8 and not GAB_RX.search(txt[max(0, a - 300): z + 300])
            if same:
                put(bill, 'number', txt[max(0, a - 60): z + 60], 'medium' if 'one of' in info['role'] else 'high')
            else:
                kw = KEYWORDS.get(bill)
                near = GAB_RX.search(txt[max(0, a - 150): z + 150]); cue = TIE_RX.search(win) or re.search(r"Gabriel['’]s|\bhis\b", win)
                ev = txt[max(0, a - 60): z + 60]
                if dense or 'one of' in info['role']:
                    put(bill, 'number (earlier session, list or minor co-lead)', ev, 'low')
                elif near and cue:
                    put(bill, 'number (earlier session)', ev, 'high')
                elif near or (kw and re.search(kw, txt, re.I)):
                    put(bill, 'number (earlier session)', ev, 'medium')
                else:
                    put(bill, 'number (earlier session, no tie)', ev, 'low')
        else:  # coauthor: needs his name tied to the bill in the same passage with a coauthor cue
            w2 = txt[max(0, a - 200): z + 200]
            strong = re.search(r'co-?author|co-?sponsor|co-?written|co-?wrote|principal|jointly|joint\s+author', w2, re.I)
            if GAB_RX.search(w2) and (strong or (info['role'] == 'principal coauthor' and TIE_RX.search(w2))):
                put(bill, 'coauthor tie', w2.strip(), 'medium')
            elif GAB_RX.search(win) and TIE_RX.search(win):
                put(bill, 'coauthor, name near, weak cue', win.strip(), 'low')
    for b, rx in TITLE_RX.items():
        m = rx.search(txt)
        if not m: continue
        info, same = resolve(b, date)
        if not info or info['intro'] > date: continue
        if b == 'AB 1127' and not same: continue
        put(b, 'title', txt[max(0, m.start() - 60): m.end() + 60], 'high')
    for b, ev in veto.items():   # one occurrence credited to another member vetoes the number for this text
        found[b] = {'how': 'number, text credits another author', 'ev': ev[:160], 'conf': 'low'}
    for code, p in PROGRAMS.items():
        m = p['rx'].search(txt)
        if m:
            if any(b in found and found[b]['how'] != 'program' for b in p['bills']): continue   # an NSGP bill is already named -> no program tag
            info = program_bill(code, date)
            if info: put(info['bill'], 'program', txt[max(0, m.start() - 60): m.end() + 60], 'medium')
    return found

def pad_date(d):
    """'2023-09' -> '2023-09-28', '2023' -> '2023-12-31' (late in the period: conservative for 'before introduction')."""
    d = (d or '').strip()
    if re.fullmatch(r'\d{4}-\d\d-\d\d', d): return d
    if re.fullmatch(r'\d{4}-\d\d', d): return d + '-28'
    if re.fullmatch(r'\d{4}', d): return d + '-12-31'
    return None

# ---------- topic precedence ----------
TOPICS = ['Food safety', 'Antisemitism / Jewish community', 'State budget', 'Guns', 'Elections / campaigns', 'Housing / homelessness',
          'Social media / tech', 'Education / students', 'Immigration / DACA', 'Restaurants / outdoor dining', 'Energy / environment',
          'Wildfire / looting', 'Leadership / committee posts', 'Health / labor', 'Public safety', 'District / community', 'Other / roundup']
BILL_TOPIC = {}
# ... with session-split numbers (the same number names different bills of his in two sessions)
BILL_TOPIC_SESS = {}

def bill_topic(bill, date):
    info, _ = resolve(bill, date, '-' in bill)
    return info.get('topic') if info else None

FOOD = {r['bill'] for r in _EX.get('rows', []) if r.get('topic') == 'Food safety'}
GUNS = {r['bill'] for r in _EX.get('rows', []) if r.get('topic') == 'Guns'}
NSGP = {b for p in PROGRAMS.values() for b in p['bills']}

def topic_override(topic, bills, date, txt=''):
    """Deterministic precedence after the model's / sheet's label. -> (new_topic, rule) or (None, None)"""
    bills = [b for b in bills if b]
    tps = {bill_topic(b, date) for b in bills}
    if topic in (None, '', 'Other / roundup') and bills and len(tps) == 1 and None not in tps and 'Other / roundup' not in tps:
        return tps.pop(), 'single-issue bills -> bill issue'
    if topic == 'Public safety' and bills and set(bills) <= NSGP: return 'Antisemitism / Jewish community', 'NSGP precedence'
    if topic == 'Public safety' and bills and set(bills) <= GUNS: return 'Guns', 'Guns beats Public safety'
    if topic in ('Health / labor', 'Energy / environment', 'Education / students') and bills and set(bills) <= FOOD: return 'Food safety', 'Food safety precedence'
    if topic == 'Education / students' and ('AB 715' in bills or (re.search(r'antisemit', txt, re.I) and re.search(r'ethnic studies', txt, re.I))):
        return 'Antisemitism / Jewish community', 'Antisemitism beats Education (AB 715 / ethnic studies)'
    return None, None
