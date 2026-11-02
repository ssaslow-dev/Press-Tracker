#!/usr/bin/env python3
"""Synthetic NewsBank "Multiple Articles" batch PDFs for the NEWSBANKPDF-v1 tests (no real sample exists yet).

The layout copies what the library's single-story NewsBank PDFs show (tests learned from data/library/<year>/nb*.pdf, read only):
A4, headline, "<Month D, YYYY> | <source>", "Author: .. Section: .. N Words", optional "Page: ..", "OpenURL Link", body, a copyright line,
then "Citation (apa Style)" and the APA citation wrapped over several lines with the URL broken after "document-view?".
Two flows: 'continuous' (the next story starts right under the last citation, so a story can start mid-page) and 'newpage' (each story starts a page).

    python3 -I make_nb_pdfs.py OUTDIR
Writes batch_A.pdf (20 items, continuous), batch_A_copy.pdf (byte-identical), batch_19.pdf (19 items, newpage), batch_B.pdf (the same 20 items as A in newpage flow),
expected.json (the oracle the tests compare with) and evil_openaction.pdf / evil_embedded.pdf (a story PDF with JavaScript / an embedded file, for the PC-side refusal)."""
import json, sys, os, hashlib
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

DJ = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
DJB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
WQY = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
pdfmetrics.registerFont(TTFont('DJ', DJ)); pdfmetrics.registerFont(TTFont('DJB', DJB))
try:
    pdfmetrics.registerFont(TTFont('WQY', WQY, subfontIndex=0))
except Exception:
    pdfmetrics.registerFont(TTFont('WQY', DJ))
W, H = A4
LM, RM, TOP, BOT = 56, 56, 81, 56
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


def hexid(seed):
    return hashlib.sha256(seed.encode()).hexdigest()[:16].upper()


VOCAB = ('committee council valley county hearing budget housing school transit wildfire insurance hospital library tenants farmers veterans airport harbor library '
         'sacramento northridge reseda topanga ventura sepulveda burbank glendale pasadena oxnard fresno bakersfield modesto stockton redding chico monterey salinas '
         'advocates critics officials residents leaders families teachers nurses drivers riders voters donors neighbors volunteers inspectors auditors engineers '
         'approved rejected delayed funded expanded reviewed questioned praised opposed restored announced estimated proposed required reported measured '
         'million thousand percent quarter january february august october december tuesday wednesday friday weekend morning evening decade summer winter '
         'permit grant rebate lawsuit ordinance amendment audit survey forecast shortage surplus deadline timeline contract inspection ballot referendum').split()


def lorem(n, mention=True, seed=0):
    """n words of text that differs from story to story (a seeded pick from a vocabulary), so the reprint rule never calls two synthetic stories the same text"""
    import random
    rnd = random.Random(1000 + seed); out = []
    while len(out) < n:
        k = rnd.randint(8, 16); sent = [rnd.choice(VOCAB) for _ in range(k)]
        sent[0] = sent[0].capitalize(); out.append(' '.join(sent) + '.')
    t = ' '.join(' '.join(out).split(' ')[:n])
    if mention:
        t = '"We have to get this done," said Assemblymember Jesse Gabriel (D-Encino), who chairs the committee. ' + t
    return t


TOPICS = ['wildfire insurance rates climb in Topanga canyon', 'school lunch program expands to Reseda campuses', 'transit riders ask for later Metro buses', 'library hours restored after budget deal', 'rent relief fund opens for Van Nuys tenants', 'hospital seismic upgrade gets state loan', 'farmers market vendors protest new permit fee', 'police oversight panel meets in Northridge', 'water recycling plant breaks ground at Tillman', 'veterans housing complex opens on Sepulveda', 'bike lanes planned for Ventura Boulevard', 'community college adds nursing seats', 'jail diversion pilot reports early results', 'broadband grant reaches rural Kern County', 'heat shelters open across the Valley', 'charter school audit raises questions', 'harbor dredging project nears approval', 'tenant protections debated at city hall', 'food bank donations fall short this fall', 'airport noise complaints reach a record', 'park restoration honors longtime volunteers', 'ballot measure on housing draws donors', 'trauma center funding wins bipartisan support', 'solar rebate program closes early', 'museum expansion clears planning panel']
STORIES = [
    # key, headline, date (Y,M,D), outlet, author, section, page, words, body words, font, extra
    dict(k='new1', hl='Gabriel unveils plan to speed clean air permits in the Valley', d=(2026, 10, 29), src='Valley Courier Test (CA)', au='Dana Whitfield', sec='NEWS', pg='', n=190),
    dict(k='long2', hl='Budget chair pushes wildfire recovery money through committee after a long night of testimony', d=(2026, 10, 29), src='Sacramento Test Ledger, The (CA)', au='Priya Raman Staff Writer', sec='State', pg='A3', n=520),
    dict(k='zh3', hl='加布里埃尔议员推动加州预算法案', d=(2026, 10, 28), src='World Journal Test (CA)', au='', sec='', pg='', n=60, zh=True),
    dict(k='es4', hl='Gabriel presenta ley para acelerar la construcción de viviendas', d=(2026, 10, 28), src='Diario Test (CA)', au='Marta Lopez', sec='Local', pg='', n=120),
    dict(k='dup_docref5', hl='2026 elections: What you need to know about LA County\'s state Senate, Assembly races', d=(2026, 10, 24), src='Pasadena Star-News (CA)', au='Linh Tat', sec='California Politics', pg='14', n=140, docref='news/1AB748C7AEBF1E08'),
    dict(k='dup_hl6', hl='California has more revenue than expected thanks to AI. Should the state save it?', d=(2026, 10, 23), src='CALmatters (CA)', au='Yue Stella Yu', sec='Elections', pg='', n=150),
    dict(k='rep7', hl='California has more revenue than expected thanks to AI. Should the state save it?', d=(2026, 10, 24), src='Valley Courier Test (CA)', au='Yue Stella Yu CalMatters', sec='', pg='', n=150),
    dict(k='batchdup8', same_as='new1'),
    dict(k='print9', hl='Council backs Gabriel bill on food dyes', d=(2026, 10, 27), src='Courier Print Test (CA)', au='', sec='Local', pg='A5', n=110),
    dict(k='printpage10', hl='Valley Courier Test: Page 4', d=(2026, 10, 26), src='Valley Courier Test (CA)', au='', sec='', pg='', n=0, image=True),
] + [dict(k=f'f{i}', hl=f'Filler story {i}: {TOPICS[i]}', d=(2026, 10, 10 + i), src=f'Filler Gazette {i} (CA)', au=f'Writer {i}', sec='Metro', pg='', n=70 + 10 * i) for i in range(11, 21)]
STORIES = STORIES[:20]


class Pen:
    def __init__(self, path, flow):
        self.c = canvas.Canvas(path, pagesize=A4, pageCompression=0); self.c.setTitle('NewsBank Multiple Articles'); self.flow = flow
        self.y = H - TOP; self.page = 1; self.pos = []   # pos: (key, page, y_top_of_story)

    def room(self, h):
        if self.y - h < BOT:
            self.c.showPage(); self.page += 1; self.y = H - TOP

    def wrap(self, text, font, size, width):
        lines, cur = [], ''
        words = []
        for w in text.split(' '):   # an unbreakable token wider than the line (a long docref) is broken by characters, as NewsBank does
            while pdfmetrics.stringWidth(w, font, size) > width:
                k = len(w)
                while pdfmetrics.stringWidth(w[:k], font, size) > width: k -= 1
                words.append(w[:k]); w = w[k:]
            words.append(w)
        for w in words:
            t = (cur + ' ' + w).strip()
            if pdfmetrics.stringWidth(t, font, size) <= width or not cur:
                cur = t
            else:
                lines.append(cur); cur = w
        if cur: lines.append(cur)
        return lines

    def line(self, text, font='DJ', size=10, lead=13):
        self.room(lead)
        self.c.setFont(font, size); self.c.drawString(LM, self.y - size, text); self.y -= lead

    def para(self, text, font='DJ', size=10, lead=13, width=None):
        for ln in self.wrap(text, font, size, width or (W - LM - RM)):
            self.line(ln, font, size, lead)

    def gap(self, h): self.y -= h

    def end(self):
        self.c.showPage(); self.c.save()


def make(path, stories, flow, record):
    p = Pen(path, flow); pages_for = {}
    for i, s in enumerate(stories, 1):
        if flow == 'newpage' and i > 1:
            p.c.showPage(); p.page += 1; p.y = H - TOP
        elif i > 1:
            p.gap(28)
        p.room(90)
        top, page0 = p.y, p.page
        f = 'WQY' if s.get('zh') else 'DJB'
        if s.get('image'):
            p.para(s['hl'], 'DJB', 14, 18)
            y, m, d = s['d']; p.line(f'{MONTHS[m-1]} {d}, {y} | {s["src"]}', 'DJ', 10, 14)
            p.gap(30)   # (the page image is not text)
        else:
            p.para(s['hl'], f, 14, 18)
            y, m, d = s['d']; p.line(f'{MONTHS[m-1]} {d}, {y} | {s["src"]}', 'DJ', 10, 14)
            hdr = ('Author: ' + s['au'] if s['au'] else '') + (' Section: ' + s['sec'] if s['sec'] else '') + f' {s["n"]} Words'
            p.line(hdr.strip() if s['au'] or s['sec'] else f'{s["n"]} Words')
            if s['pg']: p.line('Page: ' + s['pg'])
            p.line('OpenURL Link'); p.gap(8)
            import zlib
            body = lorem(s['n'], seed=zlib.crc32(s['k'].encode()))
            if s.get('zh'):
                body = '加州众议员杰西·加布里埃尔（Jesse Gabriel）周二在萨克拉门托表示，预算委员会将审议住房和野火恢复的开支。' * 3
            cut = body.find(' ', len(body) // 2) if not s.get('zh') else len(body) // 2
            for para in (body[:cut], body[cut:]):
                p.para(para.strip(), 'WQY' if s.get('zh') else 'DJ', 10, 13); p.gap(8)
            p.line(f'Copyright (c) {y}, {s["src"].split(" (")[0]}, All Rights Reserved', 'DJ', 9, 12); p.gap(10)
        p.line('Citation (apa Style)', 'DJB', 10, 14)
        yy, mm, dd = s['d']
        au = s['au'].split(' Staff')[0].split(' CalMatters')[0]
        ap = (au.split(' ')[-1] + ', ' + au[0] + '. ') if au else ''
        outlet = s['src']
        ref = s.get('docref') or ('image/v2%3A' + hexid(s['k']) + '%40AWNB-1AABE8E425C5268C%402461304-' + hexid(s['k'] + 'x') + '%404-' + hexid(s['k'] + 'y') + '%40' if s.get('image') else 'news/' + hexid(s['k']))
        url = f'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref={ref}.'
        cit = f'{ap}({yy}, {MONTHS[mm-1]} {dd}). {s["hl"]}.{outlet.replace(" (CA)", "")}: Web Edition Articles (CA). Available from NewsBank: Access World News – Historical and Current: {url}' if not au else \
              f'{ap}({yy}, {MONTHS[mm-1]} {dd}). {s["hl"]}. {outlet}. Available from NewsBank: Access World News – Historical and Current: {url}'
        # wrap the URL like NewsBank does: break after "document-view?"
        cit = cit.replace('document-view?p=', 'document-view?\np=')
        for seg in cit.split('\n'):
            cf = 'WQY' if s.get('zh') else 'DJ'
            for ln in p.wrap(seg, cf, 9, W - LM - RM - 20):
                p.line(ln, cf, 9, 12)
        s_end_page, s_end_y = p.page, p.y
        record.append(dict(key=s['k'], start_page=page0, start_y_from_top=H - top, end_page=s_end_page, end_y_from_top=H - s_end_y, docref=ref, flow=flow))
    p.end()
    return p.page


def main(out):
    os.makedirs(out, exist_ok=True)
    byk = {s['k']: s for s in STORIES}
    stories = [dict(byk[s['same_as']]) if 'same_as' in s else s for s in STORIES]
    exp = {}
    gen19 = [dict(k=f'g{i}', hl=f'Second search story {i}: {TOPICS[i + 4]}', d=(2026, 10, 1 + i), src=f'Second Gazette {i} (CA)', au=f'Reporter {i}', sec='Metro', pg='', n=60 + 7 * i) for i in range(1, 20)]
    for s_ in gen19: s_['dup19'] = True
    for name, sts, flow in (('batch_A', stories, 'continuous'), ('batch_B', stories, 'newpage'), ('batch_19', gen19, 'newpage')):
        rec = []
        n = make(os.path.join(out, name + '.pdf'), sts, flow, rec)
        exp[name] = dict(pages=n, items=rec, n=len(rec))
    import shutil
    shutil.copy(os.path.join(out, 'batch_A.pdf'), os.path.join(out, 'batch_A_copy.pdf'))
    exp['stories'] = {s['k']: {k: v for k, v in s.items()} for s in STORIES + gen19}
    json.dump(exp, open(os.path.join(out, 'expected.json'), 'w'), indent=1, ensure_ascii=False)
    # hostile PDFs (a story PDF with /OpenAction JavaScript; one with an embedded file): made with pypdf from a one-page file
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject, DictionaryObject, ArrayObject, TextStringObject, DecodedStreamObject
    base = PdfReader(os.path.join(out, 'batch_19.pdf'))
    w = PdfWriter(); w.add_page(base.pages[0])
    js = DictionaryObject({NameObject('/S'): NameObject('/JavaScript'), NameObject('/JS'): TextStringObject('app.alert("x")')})
    w._root_object[NameObject('/OpenAction')] = w._add_object(js)
    w.write(os.path.join(out, 'evil_openaction.pdf'))
    w = PdfWriter(); w.add_page(base.pages[0]); w.add_attachment('payload.exe', b'MZ not a program'); w.write(os.path.join(out, 'evil_embedded.pdf'))
    w = PdfWriter(); w.add_page(base.pages[0])
    pg = w.pages[0]
    la = DictionaryObject({NameObject('/S'): NameObject('/Launch'), NameObject('/F'): TextStringObject('cmd.exe')})
    pg[NameObject('/AA')] = DictionaryObject({NameObject('/O'): w._add_object(la)})
    w.write(os.path.join(out, 'evil_launch.pdf'))
    print(json.dumps({k: (v['pages'], v['n']) for k, v in exp.items() if k.startswith('batch')}))


if __name__ == '__main__':
    main(sys.argv[1])
