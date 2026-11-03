#!/usr/bin/env python3 -I
"""NewsBank-header fills (read-only check; nothing is applied).

For every Coverage row whose File name / File name 2 is a NewsBank PDF (nb*.pdf), read the NewsBank header block inside the
saved copy and propose values for cells that are BLANK on the row:  Section, Author / byline, Author 1-9, Author title, Edition,
Page, Outlet city, and (only on rows that are one web+print row) Print date, Print section, Print word count.
Filled cells are never changed; where the header disagrees with a filled cell the disagreement is listed in conflicts.csv.

  step 1 (once, parallel):  python3 -I extract_texts.py     -> reads all NewsBank PDFs with 4 processes, caches the text in the scratchpad
  step 2:                   python3 -I build_proposals.py   -> proposals.csv, conflicts.csv, stats.json, calibration.json
Inputs (never written): the workbook copy wb_0bccc1fc.xlsx and data/library.   Output: this folder only.
"""
import sys, os, re, csv, json, pickle, collections, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/home/user/Press-Tracker/work/localapp/datafix')
from common import *                       # ROOT, S, WB, LIB, load_coverage, s, aid, lib_path (read-only helpers)
from nbhead import read_header, read_printpage
import authorsplit as A

T = pickle.load(open(S + '/nb_fills2_texts.pkl', 'rb'))
h, rows = load_coverage()
OUT = HERE

def fold(x): return re.sub(r'[^a-z0-9]+', '', A.fold(x).lower())
def outlet_key(o):
    o = re.sub(r'\s*\([^()]*\)\s*', ' ', s(o)); o = re.sub(r':.*$', '', o)          # drop "(City, ST)" and ": Web Edition Articles"
    o = re.sub(r',\s*(The|La|El|Los|Las)\s*$', '', o.strip(), flags=re.I); o = re.sub(r'^(The)\s+', '', o, flags=re.I)
    return fold(o)

# ---- what each row's NewsBank copies say ----
def copies(r):
    out = []
    for col in ('File name', 'File name 2'):
        f = s(r[col])
        if f.startswith('nb') and f.endswith('.pdf'):
            p = lib_path(f, r['Date'])
            if p in T:
                hd = read_header(T[p]); pp = None
                if not hd: pp = read_printpage(T[p])
                if hd:
                    cls = 'web' if 'web edition' in hd['source'].lower() else ('print' if hd['page'] else 'plain')
                elif pp: cls = 'pp'
                else: cls = 'nohdr'
                out.append(dict(col=col, file=f, hd=hd, pp=pp, cls=cls))
    return out

KNOWN_OUTLETS = {outlet_key(r['Outlet']) for r in rows if s(r['Outlet'])}
# consensus city per outlet from rows that already have one
city_by_outlet = collections.defaultdict(collections.Counter)
for r in rows:
    if s(r['Outlet city']) and s(r['Outlet']): city_by_outlet[s(r['Outlet'])][s(r['Outlet city'])] += 1

def city_from(c):
    if c['hd']:
        m = re.search(r'\(([^()]+?),\s*([A-Z]{2})\)\s*$', c['hd']['source'])
        if m: return m.group(1).strip(), c['hd']['source']
    if c['pp'] and c['pp']['city']:
        m = re.match(r'^(.+), ([A-Z][A-Za-z ]+)$', c['pp']['city'])
        if m: return m.group(1).strip(), c['pp']['line'] + ' / ' + c['pp']['city']
    return '', ''

def print_headline(pages, source):
    """Headline of a saved print copy: the PDF starts with the headline; the APA citation at the end repeats it with punctuation dropped
    ("(2026, October 25). <headline>. <Outlet label>"). Take the top lines whose letters and digits, joined, equal the citation's headline exactly.
    Returns (headline, first lines) or ('', '') when the two do not match exactly (then nothing is proposed)."""
    L = [l.strip() for l in '\n'.join(pages).split('\n')]
    try: ci = next(i for i, l in enumerate(L) if l.lower().startswith('citation (apa'))
    except StopIteration: return '', ''
    cit = ' '.join(x for x in L[ci + 1:] if x)
    m = re.search(r'\(\d{4}, [A-Za-z]+ \d{1,2}\)\.\s*(.*)$', cit)
    if not m or not source: return '', ''
    rest = fold(m.group(1)); src = fold(source)
    acc = ''; used = []
    for l in L[:8]:
        if not l: continue
        acc += fold(l); used.append(l)
        if rest.startswith(acc) and rest[len(acc):].startswith(src) and len(acc) >= 8:
            return re.sub(r'\s+', ' ', ' '.join(used)).strip(), ' / '.join(used)
        if not rest.startswith(acc): return '', ''
    return '', ''

def author_conf(raw, outlet, main_src=''):
    """-> (parse dict, confidence, why). high = plain person name(s), nothing trimmed; medium = trimmed credit / group byline; low = org alone, e-mail, digits, glued text."""
    p = A.parse_byline(raw, outlet)
    names = p['authors']
    if not names: return p, 'none', 'no author'
    clean = re.sub(r'^\s*By\s+', '', raw, flags=re.I).strip()
    kinds = [A.author_kind(n) for n in names]
    # an outlet's own name, a one-word handle or a log-in name is not a byline
    ok_ = outlet_key(outlet)
    if re.search(r'(?i)\b(publisher|mil-osi|insider|donate|admin|webmaster|newsroom)\b', raw): return p, 'low', 'organisation or CMS label'
    srcname = outlet_key((main_src or ''))
    if any(outlet_key(n) in KNOWN_OUTLETS or (srcname and outlet_key(n) == srcname) for n in names if len(outlet_key(n)) > 4 and not re.search(r'(?i)\b(staff|editorial|board|reports?)\b', n)):
        return p, 'low', "the name of an outlet, not a person"
    if any(outlet_key(n) and (outlet_key(n) == ok_ or (len(outlet_key(n)) > 5 and outlet_key(n) in ok_) or (len(ok_) > 5 and ok_ in outlet_key(n))) for n in names if not re.search(r'(?i)\b(staff|editorial|board|reports?)\b', n)) \
            or any(len(n.split()) == 1 and not re.search(r'(?i)(staff|redacci)', n) or n == n.lower() for n in names):
        return p, 'low', "the outlet's own name, a one-word handle or a log-in name"
    allp = all(k == 'person' for k in kinds)
    shape = all(2 <= len(n.split()) <= 4 and not re.search(r'[\d@]', n) for n in names)
    joined = A.fold(' '.join(names)).lower().replace(' and ', ' ').replace(',', ' ')
    same = re.sub(r'[\s,.]+', ' ', joined).strip() == re.sub(r'[\s,.]+', ' ', re.sub(r'\band\b', ' ', A.fold(clean).lower())).strip()
    if p['confidence'] == 'high' and allp and shape and same and not p['title']: return p, 'high', 'plain name(s)'
    if p['confidence'] == 'high' and allp and shape and (same or p['title']) and not re.search(r'[@\d]', raw): return p, 'high' if same else 'medium', 'name(s) + title' if p['title'] else 'name(s)'
    if p['confidence'] in ('high', 'medium') and all(k in ('person', 'board', 'staff', 'wire') for k in kinds) and shape and not re.search(r'[@\d]', raw): return p, 'medium', 'trimmed credit or group byline'
    if re.search(r'[@\d]', raw) or p['confidence'] == 'low': return p, 'low', 'e-mail, digits or glued text in header'
    return p, 'low', 'organisation or unclear'

props = []; conflicts = []; blocked = {}
def prop(r, col, new, conf, ev, extra=''):
    props.append(dict(tab='Coverage', article_id=aid(r), column=col, current='', new=new, confidence=conf, evidence=ev, kind=s(r['Original or reprint']), note=extra))
def confl(r, typ, col, cur, hdrv, ev, effect):
    conflicts.append(dict(article_id=aid(r), type=typ, column=col, current=cur, header=hdrv, evidence=ev, effect=effect, outlet=s(r['Outlet']), file=ev.split(':')[0]))
def q(x): return '"' + x + '"'

rowstat = collections.Counter(); calib = collections.defaultdict(collections.Counter)
for r in rows:
    C = copies(r)
    if not C: continue
    rowstat['rows with NewsBank PDF'] += 1
    ed = s(r['Edition']); wp = ed == 'Web + Print'
    web = [c for c in C if c['cls'] == 'web']; prt = [c for c in C if c['cls'] in ('print', 'pp')]
    if wp:   main = (web or [c for c in C if c['cls'] != 'pp'] or C)[0]; printc = prt[0] if prt else None
    else:    main = C[0]; printc = None
    # a Web + Print row whose only NewsBank copy is the print one: that copy is the print side
    if wp and not web and prt and len(C) == 1: main = prt[0]; printc = prt[0]
    hd = main['hd']; pp = main['pp']
    dstr = s(r['Date'])[:10]
    # ---- identity check: header date vs Date (DATES-v1 makes 1-3 day gaps normal for reprints / print issue dates; more is a different article) ----
    hdate = (hd or pp or {}).get('date', '')
    block = False
    if hdate and dstr and not (wp and main['cls'] == 'print'):
        gap = abs((dt.date.fromisoformat(hdate) - dt.date.fromisoformat(dstr)).days)
        if gap > 3: block = True; confl(r, 'date (blocks all fills on this row)', 'Date', dstr, hdate, main['file'] + ': ' + q(hd['lines'][0] if hd else pp['line']), 'no fills proposed for this row')
        elif gap: confl(r, 'date (1-3 days, normal; fills still proposed)', 'Date', dstr, hdate, main['file'] + ': ' + q(hd['lines'][0] if hd else pp['line']), 'none')
    if block: rowstat['rows blocked by date gap > 3 days'] += 1; continue
    # ---- outlet check (city only) ----
    src = (hd or pp or {}).get('source', '')
    outlet_ok = (not src) or outlet_key(src) == outlet_key(r['Outlet']) or outlet_key(src) in outlet_key(r['Outlet']) or outlet_key(r['Outlet']) in outlet_key(src)

    # ---- Section ----
    if hd and hd['section']:
        cur = s(r['Section'])
        if not cur and not (wp and main['cls'] == 'print' and web): prop(r, 'Section', hd['section'], 'high', main['file'] + ': ' + q('Section: ' + hd['section']))
        elif cur and cur.lower() != hd['section'].lower() and not (wp and main['cls'] == 'print'):
            confl(r, 'section differs', 'Section', cur, hd['section'], main['file'] + ': ' + q('Section: ' + hd['section']), 'filled cell kept')
    # ---- Edition / Page (single-copy rows and rows whose other copy is also a NewsBank PDF) ----
    other_nonnb = bool(s(r['File name 2'])) and len(C) == 1 or (not C[0]['file'] == s(r['File name']) and bool(s(r['File name'])) and len(C) == 1)
    page_val = ''
    pg_src = None
    for c in (printc, main) if printc else (main,):
        if c and c['cls'] in ('print', 'pp'):
            pg_src = c; page_val = (c['hd']['page'] if c['hd'] else c['pp']['page']); break
    # Edition
    if not ed:
        e_new = ''; ev = ''
        if len(C) == 2 and web and prt and abs((dt.date.fromisoformat((web[0]['hd'] or {}).get('date', '2000-01-01')) - dt.date.fromisoformat((prt[0]['hd'] or prt[0]['pp'] or {}).get('date', '2000-01-01'))).days) <= 7 and outlet_key((web[0]['hd'] or {}).get('source', '')) == outlet_key(((prt[0]['hd'] or prt[0]['pp']) or {}).get('source', '')):
            e_new, conf = 'Web + Print', 'medium'; ev = web[0]['file'] + ': ' + q((web[0]['hd'] or {})['source']) + ' and ' + prt[0]['file'] + ': ' + q(((prt[0]['hd'] or {}).get('page') and 'Page: ' + prt[0]['hd']['page']) or prt[0]['pp']['line'])
        elif other_nonnb: rowstat['blank Edition left alone: another non-NewsBank copy on the row'] += 1
        elif len(C) == 1 and main['cls'] == 'web': e_new, conf = 'Web', 'high'; ev = main['file'] + ': ' + q(hd['source'])
        elif len(C) == 1 and main['cls'] in ('print', 'pp'):
            e_new, conf = 'Print', 'high'; ev = main['file'] + ': ' + q('Page: ' + hd['page'] if hd else pp['line'])
        if e_new:
            prop(r, 'Edition', e_new, conf, ev)
            if e_new == 'Web + Print': wp = True; printc = prt[0]; main = web[0]; hd = main['hd']; pp = None
    elif not wp and ed in ('Web', 'Print') and main['cls'] in ('web', 'print', 'pp'):
        inf = 'Web' if main['cls'] == 'web' else 'Print'
        calib['edition'][inf == ed] += 1
        if inf != ed: confl(r, 'edition differs', 'Edition', ed, inf, main['file'] + ': ' + q(hd['source'] if hd else pp['line']), 'filled cell kept')
    # Page (blank only; belongs to the print side)
    if page_val and not s(r['Page']) and (s(r['Edition']) in ('Print', 'Web + Print', '') or any(p['column'] == 'Edition' and p['article_id'] == aid(r) for p in props)):
        pv = re.sub(r'^([A-Za-z]{1,2}) (\d+)$', r'\1\2', page_val.strip())          # "A 4" -> "A4"
        new = int(pv) if pv.isdigit() else pv
        prop(r, 'Page', new, 'high' if pv == page_val.strip() else 'medium', pg_src['file'] + ': ' + q(('Page: ' + page_val) if pg_src['hd'] else pg_src['pp']['line']))
    elif page_val and s(r['Page']) and s(r['Page']).lower() != page_val.lower().replace(' ', ''):
        confl(r, 'page differs', 'Page', s(r['Page']), page_val, pg_src['file'] + ': ' + q('Page: ' + page_val), 'filled cell kept')
    # ---- Print fields: only on one-row web+print rows (the print copy is the NewsBank print PDF) ----
    if wp and printc:
        ph = printc['hd']; ppp = printc['pp']; pdate = (ph or ppp or {}).get('date', '')
        if pdate and not s(r['Print date']): prop(r, 'Print date', pdate, 'high', printc['file'] + ': ' + q(ph['lines'][0] if ph else ppp['line']), 'print side of a Web + Print row')
        elif pdate and s(r['Print date'])[:10] != pdate: confl(r, 'print date differs', 'Print date', s(r['Print date'])[:10], pdate, printc['file'] + ': ' + q(ph['lines'][0] if ph else ppp['line']), 'filled cell kept')
        if ph and not s(r['Print headline']):
            ps = ph['source']
            hl, first = print_headline(T[[p for p in T if p.endswith('/' + printc['file'])][0]], ps)
            if hl: prop(r, 'Print headline', hl, 'high', printc['file'] + ': first lines ' + q(first) + ' = the headline in its citation', 'print side of a Web + Print row')
            else: rowstat['Print headline blank, could not be read from the print copy'] += 1
        if ph and ph['section'] and not s(r['Print section']): prop(r, 'Print section', ph['section'], 'high', printc['file'] + ': ' + q('Section: ' + ph['section']), 'print side of a Web + Print row')
        if ph and ph['words'] and not s(r['Print word count']): prop(r, 'Print word count', int(ph['words']), 'high', printc['file'] + ': ' + q(ph['words'] + ' Words'), 'print side of a Web + Print row')
    # ---- City ----
    if not s(r['Outlet city']):
        cc, ev = city_from(main)
        if not cc and printc: cc, ev = city_from(printc); ev = (printc['file'] + ': ' + ev) if ev else ''
        else: ev = (main['file'] + ': ' + q(ev)) if ev else ''
        if cc:
            cons = city_by_outlet.get(s(r['Outlet']))
            if not outlet_ok: confl(r, 'outlet differs (city not proposed)', 'Outlet', s(r['Outlet']), src, ev, 'no city proposed')
            elif cons and cc not in cons: confl(r, 'city differs from other rows of this outlet (city not proposed)', 'Outlet city', '/'.join(cons), cc, ev, 'no city proposed')
            else: prop(r, 'Outlet city', cc, 'high' if cons else ('low' if '-' in cc else 'medium'), ev, '' if cons else 'no other row of this outlet states a city' + ('; header names a region, not a city' if '-' in cc else ''))
    # ---- Authors ----
    ah = (hd or {}).get('author', '') or ((printc or {}).get('hd') or {}).get('author', '') if not (hd and hd['author']) else hd['author']
    asrc = main if (hd and hd['author']) else (printc if printc and printc['hd'] and printc['hd']['author'] else None)
    if ah and asrc:
        pa, conf, why = author_conf(ah, s(r['Outlet']), (asrc['hd'] or {}).get('source', ''))
        a1 = s(r['Author 1'])
        if not a1 and not s(r['Author / byline']) and pa['authors'] and conf != 'none':
            ev = asrc['file'] + ': ' + q('Author: ' + ah)
            cleaned = re.sub(r'\s+', ' ', re.sub(r'^\s*By\s+', '', ah, flags=re.I)).strip()
            if conf in ('high', 'medium'): cleaned_b = '; '.join([', '.join(pa['authors'][:-1]) + (' and ' if len(pa['authors']) > 1 else '') + pa['authors'][-1]] + ([pa['title']] if pa['title'] else []))
            else: cleaned_b = cleaned
            prop(r, 'Author / byline', cleaned_b, conf, ev, why)
            for i, n in enumerate(pa['authors'][:9], 1):
                if not s(r['Author %d' % i]): prop(r, 'Author %d' % i, n, conf, ev, why)
            if pa['title'] and not s(r['Author title']): prop(r, 'Author title', pa['title'], conf, ev, why)
        elif a1:
            # calibration: does the header's first cleaned author match the filled one?
            ok = bool(pa['authors']) and A.author_key(pa['authors'][0]) == A.author_key(a1)
            calib['author1_vs_filled_' + conf][ok] += 1
            if ok and pa['title'] and not s(r['Author title']) and conf in ('high', 'medium'):
                prop(r, 'Author title', pa['title'], conf, asrc['file'] + ': ' + q('Author: ' + ah), 'Author 1 on the row matches the header')
            elif (not ok) and conf in ('high',): confl(r, 'author differs (info only)', 'Author 1', a1, ah, asrc['file'] + ': ' + q('Author: ' + ah), 'filled cell kept')
    rowstat['rows checked'] += 1

# ---- write ----
cols = ['tab', 'article_id', 'column', 'current', 'new', 'confidence', 'evidence']
hdr = ['tab', 'Article ID', 'column', 'current value (blank)', 'new value', 'confidence', 'evidence']
with open(OUT + '/proposals.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(hdr)
    for p in props: w.writerow([p[c] for c in cols])
ccols = ['article_id', 'type', 'column', 'current', 'header', 'outlet', 'evidence', 'effect']
with open(OUT + '/conflicts.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['Article ID', 'type', 'column', 'current (filled)', 'header says', 'outlet', 'evidence', 'effect']);
    for c in conflicts: w.writerow([c[k] for k in ccols])
by = collections.Counter((p['column'], p['confidence']) for p in props)
cnt = collections.Counter(p['column'] for p in props)
rowsets = collections.defaultdict(set)
for p in props: rowsets[p['column']].add(p['article_id'])
allrows = {p['article_id'] for p in props}
orig = {p['article_id'] for p in props if p['kind'] == 'Original'}
ct = collections.Counter(c['type'] for c in conflicts)
json.dump(dict(rowstat=rowstat, by_column=cnt, by_column_conf={f'{a}|{b}': v for (a, b), v in by.items()}, rows_touched=len(allrows), original_rows_touched=len(orig),
               conflicts=ct, calibration={k: dict(v) for k, v in calib.items()}), open(OUT + '/stats.json', 'w'), indent=1, default=dict)
print(json.dumps(json.load(open(OUT + '/stats.json')), indent=1))
