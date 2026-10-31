"""relpage.py - RELCOPIES-v1 (agent-relcopies2, 2026-10-28; Sammy: "Add press release clean up to button training").
One official release page -> the facts the "Press releases" tab holds, extracted EXACTLY the way the existing 244 rows were
(agent-releasecheck's extract.py + build_table.py, 2026-10-27; copied verbatim below), so the Update button's new rows come
out like the cleaned existing rows once reltab.row_values() splits and canonicalizes them.

  parse(page, title, src)  page = the release's article HTML (TinyFish html, include_selectors ["article"]) or, as a
                           fallback, its markdown; src 'office' | 'caucus'.  ->
      {dek, body, contact, words, bills, quoted (bool), named (bool), officials, type, issue, html (bool)}
  ISSUE_FIX                the manual issue corrections of build_table.py (URL fragment -> label)
Standard library only; no network."""
import re, html
from html.parser import HTMLParser


class Grab(HTMLParser):
    """Collect text of: body field, subtitle h3, press-status names, time."""
    def __init__(self):
        super().__init__()
        self.stack = []
        self.body, self.sub, self.names, self.times = [], [], [], []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get('class', '') or ''
        mode = None
        if 'field--name-body' in cls:
            mode = 'body'
        elif tag == 'h3' and 'subtitle' in cls:
            mode = 'sub'
        elif 'press-status__names' in cls:
            mode = 'names'
        elif tag == 'time':
            self.times.append(a.get('datetime', ''))
        if tag in ('script', 'style', 'img'):
            self.skip += 1 if tag != 'img' else 0
        if tag in ('p', 'br', 'li', 'div', 'h1', 'h2', 'h3', 'h4'):
            self._emit('\n')
        self.stack.append((tag, mode))

    def handle_endtag(self, tag):
        # pop to matching tag
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
        if tag in ('p', 'li', 'div'):
            self._emit('\n')

    def _modes(self):
        return {m for _, m in self.stack if m}

    def _emit(self, s):
        ms = self._modes()
        if 'body' in ms: self.body.append(s)
        if 'sub' in ms: self.sub.append(s)
        if 'names' in ms: self.names.append(s)

    def handle_data(self, d):
        if self.skip:
            return
        self._emit(d)


def clean(s):
    s = html.unescape(s).replace('\xa0', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\s*\n\s*', '\n', s)
    return s.strip()


BILL_RE = re.compile(
    r'\b(?:(Assembly|Senate)\s+(Bill|Constitutional Amendment|Joint Resolution|Concurrent Resolution)\s*(?:\((?:AB|SB|ACA|SCA|AJR|SJR|ACR|SCR)\)\s*)?(?:No\.\s*)?(\d{1,4})'
    r'|(AB|SB|ACA|SCA|AJR|SJR|ACR|SCR|HR)\s?-?\s?(\d{1,4})\b)')
ABBR = {('Assembly', 'Bill'): 'AB', ('Senate', 'Bill'): 'SB', ('Assembly', 'Constitutional Amendment'): 'ACA',
        ('Senate', 'Constitutional Amendment'): 'SCA', ('Assembly', 'Joint Resolution'): 'AJR',
        ('Senate', 'Joint Resolution'): 'SJR', ('Assembly', 'Concurrent Resolution'): 'ACR',
        ('Senate', 'Concurrent Resolution'): 'SCR'}


def bills(t):
    out = []
    for m in BILL_RE.finditer(t):
        if m.group(1):
            b = f"{ABBR[(m.group(1), m.group(2))]} {int(m.group(3))}"
        else:
            b = f"{m.group(4)} {int(m.group(5))}"
        if b not in out:
            out.append(b)
    return out


GAB = r'(?:Jesse\s+Gabriel|Gabriel)(?!le)'
NAMES_GAB = re.compile(r'(?<!San )\b' + GAB + r'\b')
# quote attribution patterns
Q1 = re.compile(r'(?:said|says|stated|added|noted)\s*,?\s*(?:[A-Z][\w.\'’\-,() ]{0,130}?\s)?' + GAB + r'\b')
Q5 = re.compile(GAB + r'\s+(?:Says|Said|made the following remarks|issued the following statement)')
Q6 = re.compile(GAB + r'[^“\n]{0,80}\)\s*:\s*[“"]')
Q2 = re.compile(GAB + r'\b[^“”"\n]{0,160}?\b(?:said|says|stated|added)\b')
Q3 = re.compile(GAB + r'\b[^\n]{0,220}?\b(?:released|issued)\s+the\s+following\s+(?:joint\s+)?statement')
Q4 = re.compile(r'[“"][^”"]{20,}[”"]\s*[—–-]+\s*(?:[A-Z][\w.\'’ ]{0,60}?)?' + GAB)

TITLE_RE = re.compile(
    r"\b(Assemblymember|Assemblywoman|Assemblyman|Assembly Majority Leader|Assembly Speaker|Speaker pro Tem(?:pore)?|Speaker|"
    r"State Senator|Senator|Sen\.|Senate President pro Tempore|Senate Pro Tem|President pro Tempore|Lieutenant Governor|Lt\. Governor|Governor|Gov\.|"
    r"Attorney General|Mayor|Councilmember|Council Member|Supervisor|Congresswoman|Congressman|Representative|Rep\.|"
    r"Superintendent(?: of Public Instruction)?|Treasurer|Controller|Secretary of State|Insurance Commissioner|District Attorney)"
    r"\s+((?:[A-Z][a-zA-Z.\'’\-]+)(?:\s+(?:[A-Z][a-zA-Z.\'’\-]+|de|del|la)){0,3})")
STOP_AFTER = re.compile(r"\s+(?:D|R|and|of|the|for|said|who|has|is|was)$")


NAME = r"[A-Z][^\W\d_]*(?:[.\'’\-][^\W\d_]+)*\.?"
TITLE_RE2 = re.compile(TITLE_RE.pattern.replace(r"((?:[A-Z][a-zA-Z.\'’\-]+)(?:\s+(?:[A-Z][a-zA-Z.\'’\-]+|de|del|la)){0,3})", "(" + NAME + r"(?:\s+(?:" + NAME + r"|de|del|la)){0,3})"))
PLURAL = re.compile(r"\b(Assemblymembers|Senators|Assemblywomen|Assemblymen)\s+([^.;:“\"]{0,400})")
BAD_TOK = {'Signing','Signs','AB','SB','Bill','Budget','Committee','Office','Chair','Pro','District','Says','Said','Announces','Issues','Comments','Responds'}
TNORM = {'Gov.': 'Governor', 'Sen.': 'Senator', 'Assemblywoman': 'Assemblymember', 'Assemblyman': 'Assemblymember',
         'State Senator': 'Senator', 'Lt. Governor': 'Lieutenant Governor', 'Council Member': 'Councilmember', 'Rep.': 'Representative',
         'Assemblymembers': 'Assemblymember', 'Assemblywomen': 'Assemblymember', 'Assemblymen': 'Assemblymember', 'Senators': 'Senator'}


def _clean_name(name):
    name = re.split(r"[’']s\b", name.strip())[0]
    name = re.split(r"\s+(?:and|of|the|for|to|in|on|at|D|R)\b", name)[0].strip(' .,')
    toks = name.split()
    while toks and toks[-1] in BAD_TOK:
        toks.pop()
    return ' '.join(toks)


def officials(t):
    found = []
    for m in TITLE_RE2.finditer(t):
        found.append((TNORM.get(m.group(1), m.group(1)), _clean_name(m.group(2))))
    for m in PLURAL.finditer(t):
        title = TNORM[m.group(1)]
        for nm in re.findall("(" + NAME + r"(?:\s+" + NAME + r"){1,3})\s*\(", m.group(2)):
            found.append((title, _clean_name(nm)))
    out = []
    for title, name in found:
        if not name or len(name) < 3 or re.search(r'\bGabriel\b', name) or name.split()[0] in BAD_TOK | {'Assembly', 'Senate', 'State', 'California', 'The'}:
            continue
        key = f"{title} {name}"
        if key not in out:
            out.append(key)
    # drop short forms (e.g. 'Governor Newsom', 'Attorney General Bonta') when a longer form with the same surname exists
    keep = []
    for o in out:
        last = o.split()[-1]
        if any(f != o and f.endswith(' ' + last) and len(f) > len(o) for f in out):
            continue
        keep.append(o)
    return keep


def rtype(title, sub, body):
    t = title.lower()
    b = body[:1500].lower()
    if 'media advisory' in t or 'media advisory' in b[:200]:
        return 'Media advisory'
    if "what they're saying" in t.replace('’', "'"):
        return 'Statement roundup'
    if 'town hall' in t:
        return 'Event notice'
    if 'covid-19 update' in t:
        return 'Constituent update'
    if 'letter' in t and 'sends letter' in t:
        return 'Letter'
    if re.search(r'\bstatements?\b|\bcomments? on\b|\bresponds?\b|\bcomments\b', t) or re.search(r'(released|issued) the following (joint )?statement', b):
        return 'Statement'
    return 'Press release'


ISSUE_KW = [
    ('Food safety', r'food additive|ultra-?processed|harmful chemicals in school|school food|dangerous chemicals in food|red dye|food safety|processed foods|ultraprocessed'),
    ('Guns', r'\bgun|firearm|machine gun|microstamping|ghost gun|handgun'),
    ('Antisemitism / Jewish community', r'antisemit|holocaust|jewish|hate crime|hate-motivated|nonprofit security|breed street|religious and cultural holidays|pride parades'),
    ('State budget', r'budget|revenue forecast|rainy day|may revis|special session'),
    ('Housing / homelessness', r'homeless|affordable housing|eviction|housing'),
    ('Social media / tech', r'social media|online hate|ab 587|twitter|elon musk|caller id|spam calls|privacy and consumer'),
    ('Restaurants / outdoor dining', r'outdoor dining|restaurant'),
    ('Wildfire / looting', r'looting|wildfire'),
    ('Immigration / DACA', r'immigra|ice raids|daca|asylum|refugee'),
    ('Energy / environment', r'climate|carbon offset|electric vehicle|water conservation|forever chemicals|pfas'),
    ('Public safety', r'street racing|sideshow|violence intervention|domestic violence|restraining order|corporate malfeasance|private judges|second chance sports|correctional'),
    ('Education / students', r'student|college|school'),
    ('Health / labor', r'mental health|wage theft|covid|health'),
    ('Leadership / committee posts', r'appointed|majority whip|leadership|chair of the|takes oath|named chair'),
]


def issue(title, sub):
    s = (title + ' ' + (sub or '')).lower()
    for lab, rx in ISSUE_KW:
        if re.search(rx, s):
            return lab
    return ''




ISSUE_FIX = {  # build_table.py: manual corrections of the keyword guess (blank = no tracker label clearly fits)
 'senator-ben-allen-named-chair': 'Leadership / committee posts', 'announces-leadership-2023-2024': 'Leadership / committee posts',
 'announces-leadership-2025-2026': 'Leadership / committee posts', 'appointed-chair-assembly-committee-privacy': 'Leadership / committee posts',
 'lisa-kodimer': '', 'onegeneration-selected-2021': '', 'child-development-institute': '',
 '500000-check-alliance': '', '35-million-state-funding-west-valley': '', 'organization-social-media-safety-selected': '',
 '2-million-new-economics-women': '', 'house-leadership-take-action-protect-democracy': '', 'stand-solidarity-ukraine': '',
 'hold-corporations-accountable-fund-essential': 'Public safety',
 '20260527-california-advances-legislation-protect-state-resources': 'Immigration / DACA',
 'jewish-caucus-statement-ice-raids': 'Immigration / DACA', 'visit-ice-detention-center': 'Immigration / DACA',
}


def _from_markdown(md, title):
    """fallback when only the page markdown is available (the button's older release check): dek = a leading '### ' line,
    contact = the lines between the 'For immediate release' date line and the dateline paragraph, body = the rest without
    the site's sidebar; markdown marks dropped."""
    t = md or ''
    i = t.find(title[:40]) if title else -1
    if i >= 0 and i < 400:
        t = t[i + len(title):]
    for stop in ('\n## Search', '\n## Connect', '\n## Offices', '\n#### Pagination', '\nShare this'):
        j = t.find(stop)
        if j > 0:
            t = t[:j]
    lines = [re.sub(r'[*_>\[\]]+|^#+\s*|\(https?://[^)]*\)', '', x).replace('\xa0', ' ').strip() for x in t.split('\n')]
    dek, contact, body, k = '', [], [], 0
    lines = [x for x in lines if x]
    if lines and re.match(r'^#{1,4}\s', (t.lstrip().split('\n') or [''])[0]):
        dek, k = lines[0], 1
    if k < len(lines) and re.match(r'(?i)^for immediate release', lines[k]):
        k += 1
        if k < len(lines) and re.match(r'^[A-Z][a-z]+day, ', lines[k]):
            k += 1
        while k < len(lines) and len(lines[k]) < 80 and not re.search(r'\s[—–-]\s|—', lines[k]):
            contact.append(lines[k]); k += 1
    body = lines[k:]
    return dek, '\n'.join(body), ', '.join(contact)


def parse(page, title, src):
    page = page or ''
    if '<' in page[:200] and re.search(r'field--name-body|<article|<p[ >]', page):
        g = Grab()
        g.feed(page)
        body = clean(''.join(g.body))
        sub = clean(''.join(g.sub))
        names = clean(''.join(g.names)).replace('\n', ', ')
        is_html = True
    else:
        sub, body, names = _from_markdown(page, title)
        body, sub = clean(body), clean(sub)
        is_html = False
    if src == 'caucus' and not sub:
        first = body.split('\n')[0] if body else ''
        if first and len(first) < 250 and not re.match(r'(SACRAMENTO|LOS ANGELES)', first) and first.strip() != (title or '').strip():
            sub = first
    words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-\.]*", body))
    quoted = bool(Q1.search(body) or Q2.search(body) or Q3.search(body) or Q4.search(body) or Q5.search(body) or Q6.search(body))
    named = bool(NAMES_GAB.search((title or '') + '\n' + body))
    return {'dek': sub, 'body': body, 'contact': names, 'words': words, 'bills': bills((title or '') + '\n' + sub + '\n' + body),
            'quoted': quoted, 'named': named, 'officials': officials(body), 'type': rtype(title or '', sub, body),
            'issue': issue(title or '', sub), 'html': is_html}


def issue_for(url, guess):
    for frag, lab in ISSUE_FIX.items():
        if frag in (url or ''):
            return lab
    return guess
