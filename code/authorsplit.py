"""T30 (agent-authorsplit): split an "Author / byline" string into ordered author names + an "Author title".

parse_byline(byline, outlet) -> dict(authors=[...], title='...', rule='...', confidence='high|medium|low', note='...')
  - authors: names in byline order; editorial boards -> "<Outlet as displayed> Editorial Board"; wires/staff kept as given
  - title: job/role text. One title per author joined "; " in author order; a single title shared by every
    author is written once (e.g. "A and B; Staff Writer" -> title "Staff Writer").
author_key(name) -> normalized key used to match the same person (case, accents, periods, extra spaces, middle initials).
Pure functions, no I/O: reusable by apply_fills.py / build_data.py / the final-write agent.
"""
import re, unicodedata

def s(v): return '' if v is None else str(v).strip()

def disp(o):  # same as build_data.py disp(): "Sacramento Bee, The" -> "The Sacramento Bee"
    o = s(o); m = re.match(r'^(.*), (The|La|El|Los|Las|Le|Les|Die|Der|Il)$', o)
    return f'{m.group(2)} {m.group(1)}' if m else o

# ---------- vocab ----------
TITLE_WORDS = r'(?:staff|writer|writers|reporter|reporters|columnist|columnista|contributor|contributing|correspondent|corresponsal|' \
              r'editor|editora?|editors|special to|especial para|bureau|chief|producer|anchor|intern|freelance|guest|' \
              r'commentator|critic|analyst|photographer|deputy|senior|associate|news staff|general assignment|redactora?|periodista|' \
              r'opinion columnist|political columnist|host|president|ceo|founder|director|assemblymember|assemblyman|senator|' \
              r'member|professor|attorney|executive)'
TITLE_RX = re.compile(r'\b' + TITLE_WORDS + r'\b', re.I)
TITLE_START_RX = re.compile(r'^(?:special to|especial para|for the|for |staff|contributing|contributor|correspondent|columnist|'
                            r'senior|deputy|associate|reporter|writer|editor|news staff|u\.?s\.? |us |health|politics|live news|'
                            r'weekend|global|chief|bureau|opinion|guest|freelance|intern|times staff|columnista|corresponsal|redact)', re.I)
WIRES = {  # normalized -> name as given style
    'associated press': 'Associated Press', 'the associated press': 'The Associated Press', 'ap': 'Associated Press',
    'ap news': 'Associated Press', 'via ap news': 'Associated Press', 'reuters': 'Reuters', 'bloomberg': 'Bloomberg',
    'bloomberg news': 'Bloomberg News', 'city news service': 'City News Service', 'cns': 'City News Service',
    'tribune news service': 'Tribune News Service', 'tns': 'Tribune News Service', '(tns)': 'Tribune News Service',
    'bay city news': 'Bay City News', 'bay city news service': 'Bay City News Service', 'afp': 'AFP',
    'agence france-presse': 'Agence France-Presse', 'efe': 'EFE', 'jta': 'JTA', 'cnn wire': 'CNN Wire',
}
WIRE_EXPAND = {'ap', 'via ap news', 'ap news', 'tns', '(tns)', 'cns'}   # abbreviations expanded -> medium confidence
HONORIFIC_RX = re.compile(r'^(Rabbi|Rev\.?|Reverend|Dr\.?|Assemblymember|Assemblywoman|Assemblyman|Sen\.?|Senator|'
                          r'Rep\.?|Mayor|Councilmember|Supervisor|Judge|Father|Pastor|Professor|Prof\.?)\s+(.+)$')
EDITORIAL_RX = re.compile(r'\b(editorial board|editorial staff|editorial team|editorial writers|board of editors|'
                          r'consejo editorial|junta editorial|the editors|our view|editorial)\b', re.I)
ORG_RX = re.compile(r'\b(staff|news|press|times|post|journal|media|service|services|reports?|wire|desk|office|association|'
                    r'foundation|group|llp|inc|calmatters|edsource|tribune|herald|register|daily|weekly|magazine|network|'
                    r'agencia|agencias|redacci[oó]n|newsroom|department|district attorney|committee|council|coalition|'
                    r'institute|center|centre|org|\.com|online|bureau|radio|tv|abc|nbc|cbs|fox|kqed|laist)\b', re.I)
EMAIL_RX = re.compile(r'\s*[\(<\[]?\b[\w.+-]+@[\w-]+\.[\w.-]+\b[\)>\]]?')
SUFFIX = {'jr', 'jr.', 'sr', 'sr.', 'ii', 'iii', 'iv'}

# v23-REPCREDIT: a credit next to a person ("Name • Outlet", "Name / JTA", "Name, JTA", "NAME AND NAME Service", "Name Capradio")
CREDIT_WORDS = r'(?:calmatters|jta|jns|associated press/report for america|associated press|ap|reuters|bloomberg|capradio|capitol weekly|cnn|edsource|kqed|laist|city news service|cns|bay city news|'\
               r'politico|npr|kff health news|the center square|center square|report for america|los angeles times|sacramento bee|san francisco chronicle)'
CREDIT_TAIL_RX = re.compile(r'^(.*?\S)\s*(?:•|/|\|)\s*(' + CREDIT_WORDS + r')\s*$', re.I)
CREDIT_COMMA_RX = re.compile(r'^([A-Z][\w.\'’-]+(?: [A-Z][\w.\'’-]+){1,3}),\s*(' + CREDIT_WORDS + r')\s*$', re.I)
CREDIT_SPACE_RX = re.compile(r'^([A-Z][\w.\'’-]+ [A-Z][\w.\'’-]+)\s+(' + CREDIT_WORDS + r')\s*$', re.I)
CREDIT_CAPS_RX = re.compile(r'^([A-Z][A-Z\'’.-]+(?: [A-Z][A-Z\'’.-]+)+(?: AND [A-Z][A-Z\'’.-]+(?: [A-Z][A-Z\'’.-]+)+)?)\s+(' + CREDIT_WORDS + r')\s*$', re.I)
CREDIT_CANON = {'jta': 'JTA', 'jns': 'JNS', 'ap': 'Associated Press', 'cns': 'City News Service', 'capradio': 'CapRadio', 'calmatters': 'CalMatters',
                'cnn': 'CNN', 'kqed': 'KQED', 'laist': 'LAist', 'npr': 'NPR', 'edsource': 'EdSource', 'politico': 'Politico'}
WIRE_RX_V23 = re.compile(r'^(the )?(associated press|reuters|bloomberg|cnn|afp|efe|jta|jns|city news service|bay city news)\b', re.I)
def split_credit(t):
    """(names part, credit title or '')"""
    for rx in (CREDIT_CAPS_RX, CREDIT_TAIL_RX, CREDIT_COMMA_RX, CREDIT_SPACE_RX):
        m = rx.match(t)
        if m and m.group(1).lower() not in WIRES and not re.search(r'\b(staff|editorial)\b', m.group(1), re.I) and not re.search(r'\b(and|y|&)\s*$', m.group(1), re.I) and not WIRE_RX_V23.match(m.group(1)):
            c = m.group(2); return m.group(1).strip(' ,'), CREDIT_CANON.get(c.lower(), c)
    return t, ''

def fold(t):
    t = unicodedata.normalize('NFKD', s(t)); t = ''.join(c for c in t if not unicodedata.combining(c))
    return t.replace('’', "'").replace('‘', "'")

def author_key(name):
    """same-person key: accents/case/periods/extra spaces ignored, single-letter middle initials dropped."""
    t = fold(name).lower().replace('.', ' ').replace(',', ' ')
    t = re.sub(r'(?<=\S)\s*\([^()]{1,30}\)\s*(?=[^\s()])', ' ', t)   # REVIEW4-LEFTOVERS A10: "Robert (Bob) Smith" / "Elise N. (Paeffgen) Bowen" = same person; a trailing "(ABC10)" credit is untouched
    t = re.sub(r'\s+', ' ', t).strip(); w = t.split(' ')
    if len(w) > 2: w = [w[0]] + [x for x in w[1:-1] if len(x) > 1] + [w[-1]]
    return ' '.join(w)

GROUP_RX = (r"(the |la |el )?(editorial board|board of editors|editorial staff|editorial team|editorial writers|editorial department|"
            r"editors|staff|staffs|news staff|newsroom|news desk|news team|staff writers|staff reports?|"
            r"staff and (wire|news service|news services|agency|agencies|wire service) (reports?|services?)|staff and agencies|"
            r"staff and wire|redacci[oó]n|consejo editorial)")
_SMALL = {'and', 'of', 'the', 'de', 'la', 'el', 'y'}
def group_case(t):
    """group words in Title Case ("staff and wire reports" -> "Staff and Wire Reports"); acronyms kept."""
    w = re.sub(r'\s+', ' ', s(t)).split(' ')
    allcaps = not any(c.islower() for c in s(t))
    out = []
    for i, x in enumerate(w):
        if i and x.lower() in _SMALL: out.append(x.lower())
        elif x.isupper() and len(x) > 1 and not allcaps: out.append(x)
        else: out.append(x[:1].upper() + x[1:].lower())
    return ' '.join(out)

def fix_case(name):
    """Title Case only when the whole name is in capitals."""
    letters = [c for c in name if c.isalpha()]
    if not letters or any(c.islower() for c in letters): return name, False
    if len(name.split()) == 1 and len(letters) <= 5: return name, False      # acronym: AOL, MMR, CNN
    def cap(w):
        lw = w.lower()
        if lw in ('ii', 'iii', 'iv'): return lw.upper()
        if re.fullmatch(r"(?:[a-z]\.){1,3}", lw): return lw.upper()          # initials J.D.
        parts = re.split(r"([-'’])", lw)
        out = ''.join(p[:1].upper() + p[1:] if p not in "-'’" else p for p in parts)
        out = re.sub(r'^Mc([a-z])', lambda m: 'Mc' + m.group(1).upper(), out)
        out = re.sub(r"^O'([a-z])", lambda m: "O'" + m.group(1).upper(), out)
        return out
    return ' '.join(cap(w) for w in name.split(' ')), True

def norm_title(t):
    t = s(t).strip(' ,;-|/')
    if not t: return ''
    t, _ = fix_case(t)
    low = t.lower()
    if low in ('staff writer', 'staff writers'): return 'Staff Writer'
    if low in ('staff', 'news staff'): return t[:1].upper() + t[1:]
    # sentence-case common titles -> Title Case ("Staff writer" -> "Staff Writer"); leave "Special to the Times" alone
    if not low.startswith(('special to', 'especial para', 'for the', 'for ')):
        t = ' '.join(w[:1].upper() + w[1:] if w.lower() not in ('and', 'of', 'the', 'for', 'to', 'de', 'para', 'la', 'el') or i == 0 else w
                     for i, w in enumerate(t.split(' ')))
    return t

def is_title(seg):
    seg = s(seg)
    if not seg: return False
    if seg.lower() in WIRES: return False
    return bool(TITLE_START_RX.match(seg)) or (bool(TITLE_RX.search(seg)) and len(seg.split()) <= 6 and not re.search(r'\band\b', seg))

def split_names(t):
    if not re.fullmatch(r'\S+\s*&\s*\S+', t.strip()):   # "Alston & Bird" (firm name) stays whole
        t = re.sub(r'\s*&\s*', ' and ', t)
    t = re.sub(r',\s*(Jr\.?|Sr\.?|II|III|IV)\b', r' \1', t)                 # "Joe Bowers, Jr." -> keep with name
    parts = re.split(r'\s*,\s*(?:and\s+)?|\s+and\s+|\s+y\s+(?=[A-ZÁÉÍÓÚÑ])', t)
    return [p.strip() for p in parts if p and p.strip()]

def parse_byline(byline, outlet=''):
    raw = s(byline); note = []; rule = []; conf = 'high'
    out = dict(authors=[], title='', rule='', confidence='high', note='')
    if not raw:
        out.update(rule='blank', confidence='high'); return out
    t = raw.strip().strip('"').strip()
    t = EMAIL_RX.sub('', t).strip()
    if t != raw.strip().strip('"').strip(): rule.append('email-stripped')
    t = re.sub(r'\s*[-–—|/]\s*$', '', t).strip()                          # "Erika Sorocco -"
    if re.match(r'^(opinion|commentary|op-ed|guest commentary|column|analysis)\s*[:|]\s*', t, re.I):
        t = re.sub(r'^[^:|]+[:|]\s*', '', t); rule.append('opinion-prefix')
    t = re.sub(r'^(by|por|posted by|written by)\s+', '', t, flags=re.I).strip()
    t = re.sub(r'\s+', ' ', t)
    # v23-REPCREDIT: "Name • Outlet" / "Name, JTA" / "NAME AND NAME Service" / "A - B" -> names + credit title
    t, _credit = split_credit(t)
    if _credit: rule.append('credit-to-title')
    if ';' not in t and '|' not in t and re.fullmatch(r'[A-Z][\w.\'’-]+ [A-Z][\w.\'’-]+ - [A-Z][\w.\'’-]+ [A-Z][\w.\'’-]+', t):
        t = t.replace(' - ', ' and '); rule.append('dash-authors')
    if _credit and re.fullmatch(r'[A-Z ,.\'’-]+', t) and ' AND ' in t:
        t = t.replace(' AND ', ' and ')
    # "Joyann JeffreyTrending News Reporter": title glued to the name (page scrape)
    if ';' not in t and '|' not in t:
        for m in re.finditer(r'(?<=[a-z\u00e0-\u00ff])(?=[A-Z])', t):
            rest = t[m.start():]
            if re.fullmatch(r'(?:[A-Z][a-z.&-]*\s){0,4}(?:Reporter|Writer|Editor|Columnist|Correspondent|Contributor|Producer)s?', rest) and ' ' in t[:m.start()]:
                t = f'{t[:m.start()]}; {rest}'; rule.append('glued-title'); break

    low = fold(t).lower()
    # ---- a label for the piece, not an author (DECISIONS 2026-10-27): Author columns and title stay blank
    if re.fullmatch(r"(the )?(editorials?|opinion|opinions|our view|our opinion|op-?ed|commentary|editorial(es)?|opinion editorial|"
                    r"editorial opinion|editorial page|columna|editorial: our view|letters? to the editors?)", low.strip(' .:')):
        out.update(authors=[], title='', rule='+'.join(rule + ['label-not-author']), confidence='high',
                   note='byline labels the piece (editorial/opinion), not an author'); return out
    # ---- a GROUP OF PEOPLE with no outlet named (DECISIONS 2026-10-27): "<Outlet> <group, Title Case>";
    #      outlet = the row's outlet, or the Original row's outlet on reprints (caller passes it)
    g = re.sub(r'^(from|by|compiled by)\s+', '', low.strip(' .:'))
    if re.fullmatch(GROUP_RX, g) and not re.search(r'editorial board|consejo editorial|junta editorial|board of editors|comite editorial', g):
        grp = group_case(re.sub(r'^(from|by|compiled by)\s+', '', t.strip(' .:'), flags=re.I))
        grp = re.sub(r'^(The|La|El)\s+', '', grp)
        o = disp(outlet)
        if o and grp.split(' ')[0].lower() == o.split(' ')[-1].lower(): grp = ' '.join(grp.split(' ')[1:])   # "Daily News" + "News Staff"
        name = f'{o} {grp}'.strip() if o else grp
        out.update(authors=[name], title='', rule='+'.join(rule + ['group-author']), confidence='high' if s(outlet) else 'low',
                   note='' if s(outlet) else 'group byline, no outlet on row'); return out
    # ---- "<Org> Staff" / "<Org> Editorial Team": the group already names its outlet -> kept, group words Title Case
    m = re.fullmatch(r'(.+?)\s+(' + GROUP_RX + r')', t.strip(), flags=re.I)
    if m and not re.search(r'[;|]', t) and not re.search(r'\band\b', m.group(1), re.I) and len(m.group(1).split()) <= 5 and \
            not re.search(r'editorial board|consejo editorial|junta editorial|board of editors|comite editorial', low):
        out.update(authors=[f'{fix_case(m.group(1))[0]} {group_case(m.group(2))}'], title='', rule='+'.join(rule + ['group-named']),
                   confidence='high'); return out
    # ---- "<X> Editorial": outlet + kind of article -> still ambiguous, kept as given, listed for Sammy
    if re.search(r'\beditorial$', low) and not re.search(r'consejo editorial|junta editorial|comite editorial', low):
        out.update(authors=[t], title='', rule='+'.join(rule + ['editorial-ambiguous']), confidence='low',
                   note='"<outlet> Editorial": article label or group credit? kept as given, listed for Sammy'); return out
    # ---- the board itself is credited -> "<Outlet> Editorial Board"
    if EDITORIAL_RX.search(low) and not re.search(r'letters? to the editor', low) and \
            re.search(r'editorial board|consejo editorial|junta editorial|board of editors|comite editorial', low):
        name = (disp(outlet) + ' Editorial Board').strip() if s(outlet) else 'Editorial Board'
        rule.append('editorial-board')
        named = re.sub(r'\b(the\s+)?(editorial board|consejo editorial|junta editorial|editorial staff|editorial team|editorial writers)\b', '', t, flags=re.I).strip(' ,;-')
        if named and fold(named).lower() not in fold(disp(outlet)).lower() and fold(named).lower().replace('the ', '') not in fold(outlet).lower():
            conf = 'medium'; note.append(f'byline names "{raw}" but row outlet is "{disp(outlet)}"')
        if re.search(r'consejo|junta', low): note.append('Spanish editorial board')
        if not s(outlet): conf = 'low'; note.append('no outlet on row')
        out.update(authors=[name], title='', rule='+'.join(rule), confidence=conf, note='; '.join(note)); return out

    # ---- title part: "Names; Title", "Name | Title", "Name, Special to ...", "Name / Associated Press"
    titles = []
    if ';' in t:
        a, b = t.split(';', 1); names_part = a.strip(); tpart = b.strip()
        segs = [x.strip() for x in tpart.split(';') if x.strip()]
        # dedupe "X; X"
        if all(fold(x).lower() == fold(names_part).lower() for x in segs):
            tpart = ''; rule.append('duplicate-removed')
        elif not any(is_title(x) for x in segs) and not re.fullmatch(r'(news )?staff', tpart, re.I):
            # "A; B" = two authors (tracker/Claude style)
            names_part = t.replace(';', ' and '); tpart = ''; rule.append('semicolon-authors')
        if tpart:
            rule.append('semicolon-title')
            # several titles for several authors: "Deputy Health Editor, Health Reporter"
            titles = [x.strip() for x in re.split(r'\s*;\s*', tpart) if x.strip()]
    else:
        names_part = t; tpart = ''
    m = re.match(r'^(.+?)\s*\|\s*(.+)$', names_part)
    if m and not tpart:
        names_part, tpart = m.group(1), m.group(2); titles = [tpart]; rule.append('pipe-title')
    m = re.match(r'^(.+?)\s+/\s+(.+)$', names_part)
    if m and not tpart:
        right = m.group(2).strip()
        if right.lower() in WIRES:   # "X / Associated Press": wire is the affiliation
            names_part = m.group(1); titles = [WIRES[right.lower()]]; rule.append('slash-wire-affiliation'); conf = 'medium'
        else:
            names_part = m.group(1); titles = [right]; rule.append('slash-title')
    # trailing ", Title" segments (", Special to the Times", ", Staff Writer")
    if not titles:
        segs = [x.strip() for x in names_part.split(',')]
        tail = []
        while len(segs) > 1 and is_title(segs[-1]) and not re.match(r'^(jr|sr|ii|iii|iv)\.?$', segs[-1], re.I):
            tail.insert(0, segs.pop())
        if tail:
            names_part = ', '.join(segs); titles = [', '.join(tail)]; rule.append('comma-title')
        else:  # "Name Special to the Times" without comma
            m = re.match(r'^(.+?)\s+((?:Special to|Especial para|For the)\b.*)$', names_part)
            if m: names_part, titles = m.group(1), [m.group(2)]; rule.append('inline-title')

    # ---- whole byline is a role only ("Staff Writer", "Special to the Enterprise")
    if re.match(r'^(special to|especial para|for the)\b', names_part, re.I) and not titles:
        out.update(authors=[], title=norm_title(names_part), rule='+'.join(rule + ['title-only']), confidence='low',
                   note='byline is a role only, no name'); return out
    if is_title(names_part) and not ORG_RX.search(re.sub(r'(?i)\bstaff\b|\bnews staff\b', '', names_part)) and \
            not re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', re.sub(TITLE_RX, '', names_part).strip()):
        if TITLE_START_RX.match(names_part) and not re.search(r'\band\b', names_part, re.I) and not names_part.lower().startswith(('staff and', 'staff report', 'from staff')):
            out.update(authors=[], title=norm_title(names_part), rule='+'.join(rule + ['title-only']), confidence='low',
                       note='byline is a role only, no name'); return out

    # "LA Downtown; News Staff" -> org staff byline kept whole
    if titles and len(titles) == 1 and re.fullmatch(r'(news )?staff', titles[0], re.I) and ORG_RX.search(names_part + ' news') and \
            not re.search(r'\band\b', names_part):
        if not re.fullmatch(r'[A-Z][a-z]+ [A-Z][a-z]+', names_part) or re.search(r'Acorn|Downtown|Briefing', names_part):
            out.update(authors=[f'{names_part} {titles[0]}'], title='', rule='+'.join(rule + ['org-staff-rejoined']),
                       confidence='medium', note='organization staff byline kept as one name'); return out

    # ---- staff / wire combos kept as given ("Staff and wire reports", "From staff and wire services")
    if re.search(r'\b(staff|wire|reports?|services?)\b', names_part, re.I) and re.search(r'\band\b', names_part, re.I) and \
            not re.search(r'[A-Z][a-z]+ [A-Z][a-z]+ and', names_part):
        out.update(authors=[names_part], title=norm_title(titles[0]) if titles else '', rule='+'.join(rule + ['staff-wire-as-given']),
                   confidence='high'); return out

    if re.fullmatch(r'[A-Z][A-Z\'’.-]+(?: [A-Z][A-Z\'’.-]+)+ AND [A-Z][A-Z\'’.-]+(?: [A-Z][A-Z\'’.-]+)+', names_part): names_part = names_part.replace(' AND ', ' and ')   # v23-REPCREDIT
    names = split_names(names_part)
    # wires
    fixed = []
    for n in names:
        k = n.lower().strip()
        if k in WIRES:
            fixed.append(WIRES[k]); rule.append('wire')
            if k in WIRE_EXPAND: conf = min_conf(conf, 'medium'); note.append(f'"{n}" read as {WIRES[k]}')
        else:
            fixed.append(n)
    names = fixed
    # v23-REPCREDIT-UNION (auditor): a wire / service credit beside a person ("Alyssa Guzman and Ap", "Associated Press, Don Thompson",
    # "Justine McDaniel and (tns)") is a credit -> Author title; a wire is an author only when the byline has no person
    _wn = [n for n in names if n in WIRES.values() or n.lower() in CREDIT_CANON or n in CREDIT_CANON.values()]
    _pn = [n for n in names if n not in _wn]
    if _wn and _pn and all(not ORG_RX.search(n) and len(n.split()) >= 2 for n in _pn) and (not titles or len(titles) == 1):
        names = _pn
        _credit = '; '.join([x for x in [_credit] if x] + [WIRES.get(n.lower(), CREDIT_CANON.get(n.lower(), n)) for n in _wn])
        rule.append('credit-to-title')
    # honorifics -> title
    hon = []
    for i, n in enumerate(names):
        m = HONORIFIC_RX.match(n)
        if m and len(m.group(2).split()) >= 2:
            names[i] = m.group(2); hon.append((i, m.group(1).rstrip('.') if m.group(1) not in ('Dr.', 'Rev.', 'Sen.', 'Rep.', 'Prof.') else m.group(1)))
    if hon:
        rule.append('honorific-to-title')
        if not titles: titles = [''] * len(names)
        if len(titles) == len(names):
            for i, h in hon: titles[i] = h if not titles[i] else f'{h}, {titles[i]}'
        conf = min_conf(conf, 'medium')
    # all-caps fix
    cased = []
    for n in names:
        c, ch = fix_case(n)
        if ch and n.upper() not in WIRES.values() and n not in ('AP', 'AFP', 'EFE', 'JTA', 'CNN'):
            rule.append('caps-fixed') if 'caps-fixed' not in rule else None
        else:
            c = n
        cased.append(c)
    names = cased
    # Gabriel
    names = ['Jesse Gabriel' if re.fullmatch(r'(assemblymember |assemblyman |asm\.? )?jesse gabriel', n, re.I) else n for n in names]
    # dedupe
    seen = set(); dd = []
    for n in names:
        k = author_key(n)
        if k in seen: rule.append('duplicate-removed'); continue
        seen.add(k); dd.append(n)
    names = dd

    # per-author titles "Deputy Health Editor, Health Reporter"
    if titles and len(titles) == 1 and len(names) > 1:
        parts = [x.strip() for x in titles[0].split(',') if x.strip()]
        if len(parts) == len(names) and all(is_title(p) for p in parts): titles = parts
    titles = [norm_title(x) for x in titles]
    if len(titles) > 1 and len(set(x for x in titles if x)) == 1 and all(titles) and len(titles) == len(names):
        titles = [titles[0]]                                   # same title for everyone -> once
    if len(titles) > 1 and len(titles) != len(names):
        conf = min_conf(conf, 'low'); note.append('title count does not match author count')
    title = '; '.join(x for x in titles) if any(titles) else ''
    if _credit: title = (title + '; ' if title else '') + _credit   # v23-REPCREDIT
    if len(titles) > 1 and len(titles) == len(names) and not all(titles):
        title = '; '.join(titles)   # keep positions (honorific on one author)

    # ---- confidence checks on names
    for i, n in enumerate(names):
        w = n.split()
        is_wire = n in WIRES.values()
        if is_wire: continue
        if ORG_RX.search(n) and not re.search(r'Editorial Board$', n):
            conf = min_conf(conf, 'medium'); note.append(f'"{n}" looks like an organization, kept as given')
        elif len(w) == 1 and not re.search(r'[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]', n):
            conf = min_conf(conf, 'low'); note.append(f'"{n}" is a single name')
        elif re.fullmatch(r'[A-Z]\.?', w[-1]):
            conf = min_conf(conf, 'low'); note.append(f'"{n}" ends with an initial (truncated?)')
        elif any(len(x) > 25 for x in w) or len(w) > 5:
            conf = min_conf(conf, 'low'); note.append(f'"{n}" does not look like a name')
    if len(names) >= 6:
        note.append(f'{len(names)} authors')
    if len(names) >= 8 or re.search(r'\band (Sarah A\.|Thomas|Keyshawn)$', names_part):
        conf = min_conf(conf, 'low'); note.append('author list may be truncated by NewsBank')
    if len(names) == 2 and len(names[0].split()) == 1 and len(names[1].split()) == 1:
        conf = 'low'; note.append('two single words: maybe one name split (e.g. "Gewertz and Catherine")')
    if not rule: rule.append('names-only' if len(names) == 1 else 'and-comma-list')
    elif not any(r_ in rule for r_ in ('semicolon-authors',)) and len(names) > 1: rule.append('and-comma-list')
    out.update(authors=names, title=title, rule='+'.join(dict.fromkeys(rule)), confidence=conf, note='; '.join(dict.fromkeys(note)))
    return out

def from_fill(authors, titles, outlet, kind=''):
    """agent-authors format: names / titles joined by ' | ' -> same shape as parse_byline.
    kind (T24 column): organization / staff / wire names are kept whole (no splitting on "and"/"&", no single-name flag)."""
    names = [x.strip() for x in str(authors or '').split(' | ') if x.strip()]
    tl = [x.strip() for x in str(titles or '').split(' | ')]
    res = dict(authors=[], title='', rule='author_fills', confidence='high', note='')
    notes, conf = [], 'high'
    for n in names:   # each name normalized by the same parser (case, editorial board, wires)
        p = parse_byline(n, outlet)
        if kind in ('organization', 'staff', 'wire') and p['authors'] and not re.search(r'editorial-board|editorial-ambiguous|group-', p['rule']) and \
                not (kind == 'wire' and len(p['authors']) > 1):
            p = dict(p, authors=[fix_case(n)[0] if len(n.split()) > 1 else n], confidence='high', note='')
        res['authors'] += [a for a in p['authors'] if author_key(a) not in {author_key(x) for x in res['authors']}]
        if p['confidence'] != 'high': conf = 'low' if p['confidence'] == 'low' or conf == 'low' else 'medium'
        if p['note']: notes.append(p['note'])
        if re.search(r'editorial-board|editorial-ambiguous|label-not-author|group-', p['rule']): res['rule'] += '+' + p['rule']
        if p['title'] and not any(tl): tl = [p['title']]
    tl = [t for t in tl if t] if not (len(tl) == len(names) and any(tl)) else tl
    if len(tl) > 1 and len(set(tl)) == 1: tl = tl[:1]
    res.update(title='; '.join(tl) if any(tl) else '', confidence=conf, note='; '.join(notes))
    return res


WIRE_RX = re.compile(r"^(the )?(associated press|reuters|bloomberg( news)?|afp|agence france-presse|efe|cnn wire|jta|"
                     r"city news services?|bay city news( service| foundation)?|tribune news service|tribune content agency|"
                     r"california news wire services|sentinel news service|u-t news services|cnn com wire service|agencia [\w ]+|agencias|"
                     r"news agencies.*|cns|scng services?|servicios de scng|[\w ]+ newswire)$", re.I)
STAFF_RX = re.compile(r"\b(staff|staffs|news staff|newsroom|news desk|news team|desk|staff reports?|staff and [\w ]+|"
                      r"redacci[oó]n)$", re.I)
EDIT_RX = re.compile(r"\b(editorial board|editorial staff|editorial team|editorial writers|editorial department|editors|board of editors)$", re.I)
KIND_OVERRIDE = {   # v23-REPKIND (v23 reporters audit): non-person strings the general rules type as people / the wrong kind
    'redaccion clarin': 'staff', 'redaccion/adelante valle': 'staff', 'redaccion adelante valle': 'staff', '华人头条-卡罗莱纳': 'org',
    'environmental working group': 'org', 'the algemeiner': 'org', 'newtalk': 'org', 'the vanguard at berkeley': 'org',
    'vanguard court watch interns': 'org', 'california alcohol policy alliance': 'org', 'telemundo': 'staff', 'marin independent journal': 'staff',
    'la nacion': 'org', 'cnn newsource': 'wire', 'associated press spanish': 'wire'}


def author_kind(name):
    """Kind of one Author N value, for the tracker filter: person | board | staff | wire | org.
    board = editorial board / editorial staff / team / editors (normal filter entries);
    staff = generic staff groups ("<Outlet> Staff", News Staff, Newsroom, Staff and Wire Reports, Staff Report) -> folded group."""
    n = s(name)
    if not n: return ''
    _o = KIND_OVERRIDE.get(fold(n).lower().strip()) or KIND_OVERRIDE.get(n.lower().strip())   # v23-REPKIND
    if _o: return _o
    if EDIT_RX.search(n): return 'board'
    if WIRE_RX.match(n): return 'wire'
    if STAFF_RX.search(n) or re.search(r'\bstaff (reports?|and |writers?$)', n, re.I): return 'staff'
    w = n.split()
    if re.match(r'(Editor|Admin|Webmaster)\s', n): return 'org'
    if len(w) == 1 and not re.search(r'[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]', n) and not re.fullmatch(r'[A-Z][a-z]+', n): return 'org'
    if re.search(r"\b(foundation|association|llp|inc|media|magazine|news|times|journal|post|office|department|network|agency|"
                 r"institute|coalition|committee|council|center|radio|tv|daily|weekly|herald|tribune|report|online|wire|playbook|"
                 r"caucus|politics|chat|district attorney|telemundo|univision|cbs|nbc|abc|fox|kqed|laist)\b|\.(com|us|org|gov|net)\b|&", n, re.I) \
            and not re.fullmatch(r"[A-Z][a-z]+ (Post|Fox|Times)", n):
        return 'org'
    return 'person'

def originals_by_story(rows):
    """{Story ID: Outlet of its Original row} from Coverage rows (dicts with 'Story ID', 'Original or reprint', 'Outlet')."""
    out = {}
    for r in rows:
        if s(r.get('Original or reprint')) == 'Original' and s(r.get('Outlet')) and s(r.get('Story ID')):
            out.setdefault(s(r['Story ID']), s(r['Outlet']))
    return out

def board_outlet(kind, outlet, sid, orig_by_sid):
    """Outlet an editorial board is named after (DECISIONS 2026-10-27): reprints use the ORIGINAL row of the same
    Story ID; a reprint with no Original outlet keeps its own outlet. Returns (outlet, fell_back)."""
    if s(kind) == 'Reprint':
        o = orig_by_sid.get(s(sid), '')
        if o: return o, False
        return s(outlet), True
    return s(outlet), False

def split_fill_row(x, outlet, sheet_byline=''):
    """One row of out/author_fills.csv (T24: authors / titles joined by ' | ', kind, evidence) -> parse dict.
    If the sheet already has a byline that names different people, the sheet wins (returns parse_byline(sheet))."""
    p = from_fill(x.get('authors', ''), x.get('titles', ''), outlet, x.get('kind', ''))
    if sheet_byline:
        q = parse_byline(sheet_byline, outlet)
        same_text = fold(sheet_byline).lower().strip() in (fold(x.get('author', '')).lower().strip(), fold(x.get('authors', '')).lower().strip())
        if not same_text and {author_key(n) for n in q['authors']} != {author_key(n) for n in p['authors']}:
            return q
        if not p['title'] and q['title']: p['title'] = q['title']
    # title glued to the name in the scraped evidence ("Joyann JeffreyTrending News Reporter", ws-02922)
    if not p['title'] and len(p['authors']) == 1:
        ev = re.search(r'"' + re.escape(p['authors'][0]) + r'([A-Z][^"]*)"', x.get('evidence', '') or '')
        if ev and len(ev.group(1).split()) <= 5 and re.search(r'(Reporter|Writer|Editor|Columnist|Correspondent|Contributor|Producer)s?$', ev.group(1)):
            p['title'] = ev.group(1).strip(); p['rule'] += '+glued-title-from-evidence'
    return p

_RANK = {'high': 2, 'medium': 1, 'low': 0}
def min_conf(a, b): return a if _RANK[a] <= _RANK[b] else b

if __name__ == '__main__':
    import sys
    for line in sys.stdin:
        if '\t' in line: b, o = line.rstrip('\n').split('\t', 1)
        else: b, o = line.rstrip('\n'), ''
        print(b, '=>', parse_byline(b, o))
