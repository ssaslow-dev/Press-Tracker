"""T10: NewsBank batch PDFs -> per-article JSON (lib/work/texts/nb/<Article ID>.json).
Usage: python3 extract_nb.py PDF_DIR COMPANION.xlsx COVERAGE.xlsx BILLS.json OUT_DIR
"""
import sys, os, re, json, subprocess, collections, unicodedata
import pandas as pd
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
except NameError:
    pass
try:
    import shownet as SN   # SHOWNET-v1
except Exception:
    SN = None
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
PDF_DIR, COMP, COV, BILLS, OUT = sys.argv[1:6]
os.makedirs(OUT, exist_ok=True)

MONTHS = 'January|February|March|April|May|June|July|August|September|October|November|December'
DATE_RE = re.compile(rf'^(?:(?:{MONTHS}) \d{{1,2}}, \d{{4}}|\d{{1,2}} de [a-záéíóú]+ (?:del? )?\d{{4}}|[^|]{{3,40}}\d{{4}}) \| ', re.I)
STRICT_DATE_RE = re.compile(rf'^(?:(?:{MONTHS}) \d{{1,2}}, \d{{4}}|\d{{1,2}} de [a-záéíóú]+ (?:del? )?\d{{4}}) \| ', re.I)   # v22 route G
AUTH_RE = re.compile(r'^Author:\s*(.*?)\s*(?:Section:\s*(.*?)\s*)?(?:(\d[\d,]*) Words)?\s*$')
SECT_RE = re.compile(r'^Section:\s*(.*?)\s*(?:(\d[\d,]*) Words)?\s*$')
WORDS_RE = re.compile(r'^(\d[\d,]*) Words$')
PAGE_RE = re.compile(r'^Page:\s*(.+)$')

def norm(s): return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFKC', str(s)).lower())).strip()

def docref(url):
    m = re.search(r'docref=([^&\s]+)', url or '')
    if not m: return ''
    d = m.group(1).rstrip('.')
    d = re.sub(r'(%40\d{7})(?!-)([0-9A-F]{16})', r'\1-\2', d)  # pdftotext drops this hyphen
    return d.lower()

def split_items(txt):
    lines = [l.rstrip() for l in txt.replace('\f', '\n').split('\n')]
    segs, cur = [], []
    for l in lines:
        if l.strip() == 'Citation (apa Style)':
            segs.append(cur); cur = []
        else: cur.append(l)
    segs.append(cur)
    items = []
    # segs[0] = item1 body; segs[j] = citation(j) + item(j+1); last = citation only
    pending = segs[0]
    for j in range(1, len(segs)):
        s = segs[j]; cit = []; k = 0
        while k < len(s):
            cit.append(s[k]); k += 1
            joined = ' '.join(x.strip() for x in cit)
            if 'docref=' in joined and joined.rstrip().endswith('.'): break
        items.append((pending, ' '.join(x.strip() for x in cit if x.strip())))
        pending = s[k:]
    return items

def paragraphs(body):
    body = [l for l in body]
    out, cur = [], []
    lens = [len(l) for l in body if l.strip()]
    mx = max(lens) if lens else 100
    for l in body:
        if not l.strip():
            if cur: out.append(' '.join(cur)); cur = []
            continue
        cur.append(l.strip())
        if len(l.rstrip()) < 0.8 * mx and re.search(r'[.!?:"”’)\]]$', l.rstrip()):
            out.append(' '.join(cur)); cur = []
    if cur: out.append(' '.join(cur))
    return [p for p in out if p]

def parse(pending, cit):
    L = [l for l in pending]
    while L and not L[0].strip(): L.pop(0)
    di = next((i for i, l in enumerate(L) if DATE_RE.match(l.strip())), None)
    if di is None: return None
    # v22 route G: a "Kicker | Headline" first line ("Bills of 2023 | 'Skittles bill' amended ...", "VC ELECTION 2020 | ...")
    # matches DATE_RE's loose "<text> <year> |" form; when a real "<Month d, yyyy> | <source>" line follows within 3 lines,
    # that one is the date line and the kicker line is the headline (kicker kept as `kicker`)
    kicker = ''
    if not STRICT_DATE_RE.match(L[di].strip()):
        ds = next((i for i in range(di + 1, min(len(L), di + 4)) if STRICT_DATE_RE.match(L[i].strip())), None)
        if ds is not None:
            k_line = ' '.join(l.strip() for l in L[di:ds] if l.strip())
            pre = ' '.join(l.strip() for l in L[:di] if l.strip())
            kicker, _, hl = k_line.partition(' | ')
            L = L[:di] + [(pre + ' ' if pre else '') + (hl or k_line)] + L[ds:]
            di += 1
    title = ' '.join(l.strip() for l in L[:di] if l.strip())
    date_line = L[di].strip(); src = date_line.split(' | ', 1)[1] if ' | ' in date_line else ''
    i = di + 1; author = section = words = page = ''
    hdr = []
    while i < len(L) and L[i].strip() != 'OpenURL Link' and i < di + 8:
        hdr.append(L[i].strip()); i += 1
    if i >= len(L) or L[i].strip() != 'OpenURL Link':  # no OpenURL line: treat no header
        i = di + 1; hdr = []
    else: i += 1
    h = ' '.join(hdr)
    m = re.search(r'Author:\s*(.*?)(?=\s+Section:|\s+\d[\d,]* Words|\s+Page:|$)', h)
    if m: author = m.group(1).strip()
    m = re.search(r'Section:\s*(.*?)(?=\s+\d[\d,]* Words|\s+Page:|$)', h)
    if m: section = m.group(1).strip()
    m = re.search(r'(\d[\d,]*) Words', h)
    if m: words = m.group(1).replace(',', '')
    m = re.search(r'Page:\s*(\S+)', h)
    if m: page = m.group(1)
    body = L[i:]
    while body and not body[-1].strip(): body.pop()
    # strip the end copyright block (last lines starting with © / Copyright / (c))
    for k in range(len(body) - 1, max(-1, len(body) - 5), -1):
        if re.match(r'^(©|Copyright|\(c\)|COPYRIGHT)', body[k].strip()):
            body = body[:k]; break
    out = {'headline': title, 'date_line': date_line, 'source': src, 'author': author, 'section': section,
           'words': words, 'page': page, 'paras': paragraphs(body), 'citation': cit}
    if kicker:
        out['kicker'] = kicker   # v22 route G
    if SN is not None and src:
        # SHOWNET-v1: NewsBank's source for a broadcast record is the SHOW, inverted, with the network in brackets ("Morning Edition [NPR]");
        # print sources carry access labels ("Valley News [30 Day Embargo]"). outlet = network / publisher; show un-inverted; label dropped.
        sp = SN.split_outlet(src.split(' | ')[0].split('  ')[0])
        out.update(outlet=sp['outlet'], show=sp['show'], network=sp['network'], label=sp['label'])
        if sp['show'] and SN.is_rundown(title):   # the title is the whole episode rundown: suggest "<Show>: <lead-in of his segment>"
            out['rundown'] = True
            out['segment_headline'] = SN.segment_headline(sp['show'], '\n\n'.join(out['paras']))
    return out

bills = json.load(open(BILLS))
bill_nums = collections.defaultdict(list)
for b in bills: bill_nums[b['bill'].replace(' ', '').upper()].append(b['session'])

comp = pd.read_excel(COMP, sheet_name='All PDF Items', dtype=str).fillna('')
comp_key = {(r['Source PDF'], int(r['Position in PDF'])): r for _, r in comp.iterrows()}
C = pd.read_excel(COV, sheet_name='Coverage', dtype=str).fillna('')
try:   # PRINTTAB-v1: print-page pointers moved to "Unlinked print pages" still match their NewsBank docrefs
    _P = pd.read_excel(COV, sheet_name='Unlinked print pages', dtype=str).fillna('')
    C = pd.concat([C, _P[[c for c in _P.columns if c in C.columns]]], ignore_index=True).fillna('')
except Exception:
    pass
by_ref = collections.defaultdict(list)
for _, r in C.iterrows():
    for col in ('NewsBank article link', 'NewsBank print article link'):
        d = docref(r[col])
        if d: by_ref[d].append((r['Article ID'], col))

stats = collections.Counter(); index = []; unmatched = []; per_pdf = {}
pdfs = sorted(f for f in os.listdir(PDF_DIR) if f.startswith('NewsBank Multiple Articles') and f.endswith('.pdf'))
for f in pdfs:
    txt = subprocess.run(['pdftotext', os.path.join(PDF_DIR, f), '-'], capture_output=True, text=True).stdout
    items = split_items(txt); per_pdf[f] = len(items); stats['pdfs'] += 1
    for pos, (pending, cit) in enumerate(items, 1):
        stats['items'] += 1
        it = parse(pending, cit)
        c = comp_key.get((f, pos))
        if it is None: stats['unparsed'] += 1; continue
        ref = docref(cit)
        if c is not None:
            if norm(c['Headline / page title'])[:40] != norm(it['headline'])[:40]: stats['companion_headline_mismatch'] += 1
            if c['NewsBank link'] and docref(c['NewsBank link']) != ref: stats['companion_link_mismatch'] += 1
        else: stats['not_in_companion'] += 1
        if ref.startswith('image/'): stats['print_page_items'] += 1; continue
        rows = by_ref.get(ref, [])
        text = '\n\n'.join(it['paras'])
        if not rows:
            unmatched.append({'pdf': f, 'pos': pos, 'headline': it['headline'], 'source': it['source'], 'docref': ref, 'has_text': bool(text)})
            stats['article_unmatched'] += 1; continue
        try: lang = detect(text[:3000]) if len(text) > 80 else ''
        except Exception: lang = ''
        sents = re.split(r'(?<=[.!?])\s+(?=[A-Z“"\'(])', text)
        gs = [s.strip() for s in sents if re.search(r'gabriel', s, re.I)]
        found = sorted({re.sub(r'\s+', '', m.upper()) for m in re.findall(r'\b(?:AB|SB|A\.B\.|Assembly Bill)\s*\d+\b', text, re.I)})
        found = [re.sub(r'ASSEMBLYBILL', 'AB', x).replace('A.B.', 'AB') for x in found]
        bm = [{'bill': b[:2] + ' ' + b[2:], 'sessions': bill_nums[b]} for b in found if b in bill_nums]
        for aid, col in rows:
            sid = C.loc[C['Article ID'] == aid, 'Story ID'].iloc[0]
            rec = {'aid': aid, 'sid': sid, 'link_col': col, 'pdf': f, 'pos': pos, 'headline': it['headline'], 'source': it['source'],
                   'date_line': it['date_line'], 'author': it['author'], 'section': it['section'], 'page': it['page'],
                   'edition': 'Print' if col == 'NewsBank print article link' or it['page'] else 'Web',
                   'words': it['words'], 'date': it['date_line'].split(' | ')[0], 'language_detected': lang,
                   'mentions_gabriel': bool(gs), 'mentions_jesse_gabriel': bool(re.search(r'Jesse\s+Gabriel', text)), 'gabriel_sentences': gs, 'bills_mentioned': bm,
                   'text': text, 'citation': it['citation'], 'docref': ref}
            p = os.path.join(OUT, f'{aid}.json')
            if os.path.exists(p) and col == 'NewsBank print article link':
                continue  # keep the web article's text when a Web + Print row has both
            json.dump(rec, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
            index.append({k: rec[k] for k in ('aid', 'sid', 'link_col', 'pdf', 'pos', 'headline', 'source', 'date', 'author', 'section', 'page', 'words', 'language_detected', 'mentions_gabriel', 'mentions_jesse_gabriel')} | {'chars': len(text), 'bills': '; '.join(b['bill'] for b in bm)})
            stats['article_rows_written'] += 1

pd.DataFrame(index).to_csv(os.path.join(os.path.dirname(OUT.rstrip('/')), 'nb_index.csv'), index=False)
pd.DataFrame(unmatched).to_csv(os.path.join(os.path.dirname(OUT.rstrip('/')), 'nb_unmatched.csv'), index=False)
json.dump({'stats': stats, 'items_per_pdf': per_pdf}, open(os.path.join(os.path.dirname(OUT.rstrip('/')), 'nb_extract_stats.json'), 'w'), indent=1)
print(dict(stats))
