"""Read the NewsBank header block out of a saved-copy PDF's text (older "Month D, YYYY | source" layout, which is
what every saved copy in the library has: the block sits in the page flow, ending at the line "OpenURL Link").
Block, top to bottom:   <Month D, YYYY>  /  |  /  <source (outlet label)>  /  Author: ...  /  Section: ...  /  N Words  /  Page: ...  /  OpenURL Link
(any of Author / Section / Words / Page may be missing).  Also reads the labelled form (Date:/Source:/Section:/Word Count:/Author:/Edition:/Page:)."""
import re
MONTHS = 'January|February|March|April|May|June|July|August|September|October|November|December'
ES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
EN_IDX = {m: i + 1 for i, m in enumerate(MONTHS.split('|'))}
DATE_EN = re.compile(rf'^({MONTHS}) (\d{{1,2}}), (\d{{4}})\s*\|?\s*(.*)$')
DATE_ES = re.compile(r'^(\d{1,2}) de ([a-záéíóú]+) (?:del? )?(\d{4})\s*\|?\s*(.*)$', re.I)
LAB = re.compile(r'^(Date|Source|Section|Word Count|Words|Author|Byline|Edition|Page|Length|Publication Location)\s*:\s*(.*)$', re.I)
WORDS = re.compile(r'^(\d[\d,]*) Words$')

def iso_date(l):
    m = DATE_EN.match(l)
    if m: return '%04d-%02d-%02d' % (int(m.group(3)), EN_IDX[m.group(1)], int(m.group(2))), m.group(4)
    m = DATE_ES.match(l)
    if m and m.group(2).lower() in ES: return '%04d-%02d-%02d' % (int(m.group(3)), ES.index(m.group(2).lower()) + 1, int(m.group(1))), m.group(4)
    return None, None

def read_header(pages):
    """-> dict(date, source, author, section, words, page, edition_label, lines=[the header lines], cit_page, cit_source) or None"""
    L = [l.rstrip() for l in '\n'.join(pages).split('\n')]
    out = dict(date='', source='', author='', section='', words='', page='', edition_label='', lines=[], cit_page='', cit_outlet='')
    # citation: "... , p. 14. Available from NewsBank"  (print) -- page printed in the citation
    txt = ' '.join(x.strip() for x in L)
    cm = re.search(r',\s*p\.\s*([A-Za-z]?\d+[A-Za-z]?|[A-Z]{1,3}\d*)\.\s*Available from NewsBank', txt)
    if cm: out['cit_page'] = cm.group(1)
    oi = [i for i, l in enumerate(L) if l.strip() == 'OpenURL Link']
    if not oi: return None
    o = oi[0]
    # walk back to the date line (at most 14 lines)
    di = None
    for i in range(o - 1, max(o - 16, -1), -1):
        d, rest = iso_date(L[i].strip())
        if d: di = i; break
    if di is not None:
        blk = [x.strip() for x in L[di:o]]
        d, rest = iso_date(blk[0]); out['date'] = d
        rest = rest.strip()
        body = [x for x in blk[1:] if x and x != '|']
        if rest: body.insert(0, rest)
        out['lines'] = [blk[0]] + [x for x in body if x != rest] if False else [x for x in blk if x]
        # split into source (lines before the first label/Words) and labelled lines
        src = []; cur = None
        for x in body:
            m = LAB.match(x); w = WORDS.match(x)
            if m:
                cur = m.group(1).lower(); v = m.group(2).strip()
                key = {'words': 'words', 'word count': 'words', 'author': 'author', 'byline': 'author', 'section': 'section', 'page': 'page', 'edition': 'edition_label', 'source': 'source'}.get(cur)
                if key == 'words': mm = re.search(r'\d[\d,]*', v); out['words'] = mm.group(0).replace(',', '') if mm else ''
                elif key: out[key] = (out[key] + ' ' + v).strip()
            elif w: out['words'] = w.group(1).replace(',', ''); cur = 'words'
            elif cur in ('author', 'section', 'source', 'edition_label') and cur: key = {'author': 'author', 'section': 'section', 'source': 'source', 'edition_label': 'edition_label'}[cur]; out[key] = (out[key] + ' ' + x).strip()
            elif cur is None: src.append(x)
        if src and not out['source']: out['source'] = ' '.join(src)
        out['source'] = re.sub(r'\s+', ' ', out['source']).strip()
        mm = re.match(r'^(.*?)\s+(\d[\d,]*) Words$', out['section'])
        if mm: out['section'] = mm.group(1); out['words'] = out['words'] or mm.group(2).replace(',', '')
        return out
    # labelled form, no date line before OpenURL: scan the 20 lines above
    blk = [x.strip() for x in L[max(0, o - 20):o]]
    found = False
    for x in blk:
        m = LAB.match(x)
        if m:
            found = True; k = m.group(1).lower(); v = m.group(2).strip()
            if k == 'date': out['date'] = iso_date(v)[0] or ''
            elif k in ('word count', 'words'): out['words'] = re.sub(r'\D', '', v)
            else: out[{'source': 'source', 'section': 'section', 'author': 'author', 'byline': 'author', 'page': 'page', 'edition': 'edition_label'}.get(k, 'x')] = v
    return out if found else None


PP_TOP = re.compile(r'^(.*) - (' + MONTHS + r') (\d{1,2}), (\d{4}) - page (\S+)\s*$')
def read_printpage(pages):
    """Print-page image copy (OCR text): first line "<Outlet label> - Month D, YYYY - page N", then date / | / outlet / | / "City, State" / | / "Page N".
    -> dict(date, source, city, page, line) or None"""
    L = [l.strip() for l in '\n'.join(pages).split('\n')[:12]]
    if not L: return None
    m = PP_TOP.match(L[0])
    if not m: return None
    city = ''
    for x in L[1:10]:
        if x and x != '|' and re.match(r'^[A-Z][A-Za-z.\' -]+, [A-Z][A-Za-z ]+$', x) and x != m.group(1): city = x; break
    return dict(date='%04d-%02d-%02d' % (int(m.group(4)), EN_IDX[m.group(2)], int(m.group(3))), source=m.group(1), city=city, page=m.group(5), line=L[0])
