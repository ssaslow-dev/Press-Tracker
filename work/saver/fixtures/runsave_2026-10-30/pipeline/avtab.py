"""avtab.py - the workbook's "Audio & video details" tab (AVTAB-v1, agent-avtab 2026-10-28; Sammy approved the tab).
AVTAB-v3 (v20, agent-v20-origin-av): station video pages never date a row (page_date reads Posted:/JSON-LD/
article:published_time, single unambiguous date only; nothing within 3 days of the save day). AVSHOW-v1: Channel column
(channel_of) on every item type; Show/program = real program names only (show_of / station_show).

One row per Coverage row whose Medium is Podcast, Radio, TV or Video, keyed by Article ID; format-specific fields only
(the item itself stays a Coverage row: Outlet = show, Headline = title, Author 1..N = hosts). Blank = not established.
Used by: the backfill (work/tmp_agent-avtab/backfill.py), sheet_task.py (Task.apply_av: rows the Update button adds),
build_data.py (block `av`), the podcast import (work/tmp_agent-avtab/import_podcasts.py).
"""
import datetime, html as _html, re

TAB = 'Audio & video details'
MEDIA = ('Podcast', 'Radio', 'TV', 'Video')
N_GUEST, N_MENTION = 4, 5
COLS = (['Article ID', 'Story ID', 'Medium', 'Item type', 'Channel', 'Show/program', 'Station', 'Network',   # AVSHOW-v1: Channel (col E)
         'Episode/segment title', 'Episode number', 'Air/publish date', 'Air time', 'Duration', 'His role']
        + [f'Guest {i}' for i in range(1, N_GUEST + 1)] + ['Guests (more)']
        + [f'Mention {i}' for i in range(1, N_MENTION + 1)] + ['Mentions (more)', 'Timestamp basis',
        'Transcript kind', 'Transcript file', 'Show page link', 'Apple Podcasts link', 'Spotify link', 'YouTube link',
        'Archive.org link', 'Details from', 'Notes'])
# short keys for the tracker block (build_data `av`), same order as COLS minus Article ID
KEYS = ['sid', 'medium', 'type', 'channel', 'show', 'station', 'network', 'title', 'epno', 'air', 'airtime', 'dur', 'role'] + \
       ['g%d' % i for i in range(1, N_GUEST + 1)] + ['gmore'] + ['m%d' % i for i in range(1, N_MENTION + 1)] + \
       ['mmore', 'tbasis', 'tkind', 'tfile', 'lshow', 'lapple', 'lspotify', 'lyoutube', 'larchive', 'from', 'notes']
ITEM_TYPES = ('Episode', 'Broadcast segment', 'Video clip', 'Web story')
ROLES = ('guest', 'interviewed', 'soundbite', 'discussed', 'brief mention', 'moderator')   # REVIEW4 F3: moderator = he hosted/chaired the segment
WIDTHS = {'Article ID': 10, 'Story ID': 9, 'Medium': 9, 'Item type': 16, 'Channel': 22, 'Show/program': 30, 'Station': 9, 'Network': 10,
          'Episode/segment title': 44, 'Episode number': 9, 'Air/publish date': 12, 'Air time': 11, 'Duration': 9,
          'His role': 13, 'Timestamp basis': 34, 'Transcript kind': 10, 'Transcript file': 26, 'Details from': 30, 'Notes': 60}

# ---------------- small helpers ----------------
def s(v):
    if v is None:
        return ''
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.strftime('%Y-%m-%d')
    return re.sub(r'\s+', ' ', str(v)).strip()


def hms(sec):
    sec = int(round(float(sec)))
    h, m, x = sec // 3600, sec % 3600 // 60, sec % 60
    return f'{h}:{m:02d}:{x:02d}' if h else f'{m}:{x:02d}'


def fill_numbered(out, stem, n, more, vals):
    vals = [v for i, v in enumerate(vals) if v and v not in vals[:i]]
    for i in range(1, n + 1):
        out[f'{stem} {i}'] = vals[i - 1] if len(vals) >= i else ''
    out[more] = '; '.join(vals[n:])


def strip_html(h):
    h = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', h or '')
    h = re.sub(r'(?i)<br\s*/?>|</p>|</div>|</h\d>|</li>|</tr>', '\n', h)
    t = _html.unescape(re.sub(r'<[^>]+>', ' ', h))
    return re.sub(r'[ \t]+', ' ', re.sub(r'\n\s*\n+', '\n', t)).strip()


# ---------------- archive.org TV News Archive clip ids ----------------
ARCHIVE_TV = re.compile(r'archive\.org/(?:details|embed)/(?P<id>(?P<call>[A-Z0-9]+)_(?P<d>\d{8})_(?P<t>\d{6})_(?P<show>[A-Za-z0-9_]+))'
                        r'(?:[^#\s]*#start/(?P<st>\d+(?:\.\d+)?)/end/(?P<en>\d+(?:\.\d+)?))?')


def _pacific(utc):
    """UTC datetime -> (local datetime, 'PT') with US DST rules (2nd Sun Mar 2:00 .. 1st Sun Nov 2:00 local)."""
    try:
        from zoneinfo import ZoneInfo
        return utc.replace(tzinfo=datetime.timezone.utc).astimezone(ZoneInfo('America/Los_Angeles')).replace(tzinfo=None)
    except Exception:
        y = utc.year
        m2 = datetime.datetime(y, 3, 8 + (6 - datetime.date(y, 3, 8).weekday()) % 7, 10)   # 2:00 PST = 10:00 UTC
        n1 = datetime.datetime(y, 11, 1 + (6 - datetime.date(y, 11, 1).weekday()) % 7, 9)   # 2:00 PDT = 09:00 UTC
        return utc + datetime.timedelta(hours=-7 if m2 <= utc < n1 else -8)


def archive_clip(url):
    """archive.org TV clip URL -> dict(id, call, utc, local, show, start, end) or None. The id's date/time are UTC."""
    m = ARCHIVE_TV.search(s(url))
    if not m:
        return None
    utc = datetime.datetime.strptime(m.group('d') + m.group('t'), '%Y%m%d%H%M%S')
    loc = _pacific(utc)
    return {'id': m.group('id'), 'call': m.group('call'), 'utc': utc, 'local': loc, 'show': m.group('show').replace('_', ' '),
            'start': float(m.group('st')) if m.group('st') else None, 'end': float(m.group('en')) if m.group('en') else None,
            'url': 'https://archive.org/details/' + m.group('id') + (f"#start/{m.group('st')}/end/{m.group('en')}" if m.group('st') else '')}


# ---------------- station / network / show from the sheet's own strings ----------------
NETWORKS = ['Telemundo', 'Univision', 'Spectrum News', 'Fox News', 'CNN', 'MSNBC', 'NPR', 'PBS', 'ABC', 'CBS', 'NBC', 'FOX',
            'MyNetworkTV', 'KCAL', 'CW', 'Bloomberg', 'C-SPAN', 'BBC', 'CBC', 'Al Jazeera', 'NewsNation', 'Newsmax']
_NETRX = re.compile(r'\b(' + '|'.join(re.escape(n) for n in sorted(NETWORKS, key=len, reverse=True)) + r')', re.I)
_CALL = re.compile(r'(?<![A-Za-z])([KW][A-Z]{2,3})(?:-(?:TV|FM|AM|DT|CD|LD))?(?![A-Za-z])')
_NOT_CALL = {'WITH', 'WEST', 'WEEK', 'WHAT', 'WHEN', 'WIDE', 'WAR', 'WAY', 'WHO S', 'KIDS', 'KEY', 'KING', 'WALL', 'WORLD', 'WIRE', 'WEB'}


def _canon_net(n):
    n = n.strip()
    for x in NETWORKS:
        if x.lower() == n.lower():
            return x
    return n


def station_network(outlet, headline=''):
    """('KTVU', 'FOX') from 'KTVU FOX 2' / 'CBS - 7 WHIO' / 'Story Is ..., The [CNN]' / '... (FOX - San Francisco (KTVU))'"""
    o, h = s(outlet), s(headline)
    st = net = ''
    m = re.search(r'\(([^()]+?) - [^()]+\(([A-Z0-9]{3,6})\)\)\s*$', h)          # archive.org program title
    if m:
        net, st = _canon_net(m.group(1)), m.group(2)
    m = re.search(r'\[([^\]]+)\]\s*$', o)                                     # NewsBank "Show [Network]"
    if m and not net:
        net = _canon_net(m.group(1))
    m = re.match(r'^([A-Za-z]+) - \d+ ([KW][A-Z]{2,3})\b', o)                 # NewsBank "CBS - 7 WHIO"
    if m:
        net = net or _canon_net(m.group(1)); st = st or m.group(2)
    if not st:
        for c in _CALL.findall(o):
            if c not in _NOT_CALL:
                st = c; break
    if not net:
        m = _NETRX.search(re.sub(r'\[.*?\]', '', o))
        if m and (m.start() == 0 or o[:m.start()].strip().upper() == st):
            net = _canon_net(m.group(1))
    return st, net


# ---------------- AVSHOW-v1: Channel (who carried it) vs Show/program (real program names only) ----------------
# outlet that names a program, not a channel -> the program's network (Sammy 2026-10-28, comments 69e1f457 + b8050b09)
PROGRAM_NET = {'today': 'NBC', 'goodmorningamerica.com': 'ABC', 'good morning america': 'ABC', 'as it happens': 'CBC Radio',
               'noticias telemundo': 'Telemundo', 'cbs evening news': 'CBS', 'cbs mornings': 'CBS', 'nbc nightly news': 'NBC',
               'abc world news tonight': 'ABC', 'pbs newshour': 'PBS'}
DOMAIN_NET = {'today.com': 'NBC', 'goodmorningamerica.com': 'ABC', 'telemundo.com': 'Telemundo', 'noticias.telemundo.com': 'Telemundo'}
# known "channel + show" outlet strings -> (channel, show)
SPLITS = {'kqed political breakdown': ('KQED', 'Political Breakdown'), 'greater la (kcrw)': ('KCRW', 'Greater LA'),
          'laist - 89.3 fm airtalk: audio': ('LAist', 'AirTalk')}
PLATFORM = re.compile(r'(?i)\b(podbean|apple podcasts?|itunes|spotify|soundcloud|buzzsprout|anchor|simplecast|libsyn|megaphone|'
                      r'omny(?: studio)?|captivate|transistor|spreaker|youtube|vimeo|substack|iheart(?:radio)?|audioboom|podcastrex)\b')
SHOWY = re.compile(r"(?i)\b(show|podcast|hour|chat|talk|breakdown|happens|daily|edition|hour|minutes|live|tonight|today|weekly|radio hour|"
                   r"conversations?|interview|happy hour|watch|tox)\b")


def _is_domain(o):
    return bool(re.search(r'\.(com|org|net|tv|fm|us|edu|news)$', s(o).lower()))


def _meta(h, prop):
    m = re.search(r'<meta[^>]+(?:property|name)="%s"[^>]+content="([^"]*)"' % re.escape(prop), h or '', re.I) or \
        re.search(r'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="%s"' % re.escape(prop), h or '', re.I)
    return _html.unescape(m.group(1)).strip() if m else ''


def _split(o):
    """outlet -> (channel, show) when the outlet string carries both, else ('', '')"""
    o = s(o)
    if o.lower() in SPLITS:
        return SPLITS[o.lower()]
    m = re.match(r'^(.+?)\s*\(([KW][A-Z]{2,3})(?:-(?:TV|FM|AM))?\)$', o)          # "<Show> (<CALL>)"
    if m:
        return m.group(2), m.group(1).strip()
    m = re.match(r'^([KW][A-Z]{2,3})\s+([A-Z][A-Za-z\'&]+(?:\s+[A-Z][A-Za-z\'&]+)*)$', o)   # "<CALL> <Show>" (words only)
    if m and m.group(1) not in _NOT_CALL and not _NETRX.fullmatch(m.group(2)) and SHOWY.search(m.group(2)) \
       and not re.search(r'(?i)^(news|tv|radio|channel)\b', m.group(2)):
        return m.group(1), m.group(2)
    return '', ''


def _page_channel(html):
    """channel named by the saved page itself (Omny Author, Apple artistName naming a station, YouTube channel, og:site_name)"""
    h = html or ''
    for p in (r'"Author"\s*:\s*"([^"]{2,80})"', r'"ownerChannelName"\s*:\s*"([^"]{2,80})"', r'"author"\s*:\s*\{[^{}]*"name"\s*:\s*"([^"]{2,80})"'):
        m = re.search(p, h)
        if m and not PLATFORM.search(m.group(1)):
            v = _html.unescape(m.group(1)).strip()
            if p.startswith('"Author"'):
                v = re.sub(r'\s*\([A-Z]{3,5}-(?:AM|FM|TV)\)\s*$', '', v)
            if p.startswith('"author"') and not re.search(r'\b[KW][A-Z]{2,3}\b', v):   # JSON-LD author is often the host: stations only
                continue
            return v
    m = re.search(r'"artistName"\s*:\s*"([^"]{2,80})"', h)
    if m and re.search(r'\b[KW][A-Z]{2,3}\b', m.group(1)):
        return m.group(1)
    v = _meta(h, 'og:site_name')
    if v and not PLATFORM.search(v) and not _is_domain(v):
        return v
    return ''


# REVIEW4-LEFTOVERS C4: one name per broadcaster. Network-level labels fold to the news division the rows already use most;
# NewsBank "NET - n CALL" station labels become "CALL (NET n)" (E3, optional: CHANNEL_NEXSTAR = False keeps them).
CHANNEL_CANON = {'CBS': 'CBS News', 'NBC': 'NBC News', 'ABC': 'ABC News', 'Valley Beth Shalom Hazak': 'Valley Beth Shalom', 'KABC 790 AM': '790 KABC'}
try:   # LEARN-v1: the canonical channel names are reference data (outlet_rules.json channel_canon); the literal above is the fallback
    import json as _j, os as _o
    CHANNEL_CANON = dict(_j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), 'outlet_rules.json'), encoding='utf-8')).get('channel_canon') or CHANNEL_CANON)
except Exception:
    pass
CHANNEL_NEXSTAR = True
_NEX = re.compile(r'^(ABC|CBS|NBC|FOX|Independent) - (\d+) ([KW][A-Z]{2,3})$')


def canon_channel(ch):
    c = s(ch)
    if c in CHANNEL_CANON:
        return CHANNEL_CANON[c]
    m = _NEX.match(c)
    return f'{m.group(3)} ({m.group(1)} {m.group(2)})' if m and CHANNEL_NEXSTAR else c


def channel_of(outlet, medium='', network='', url='', html='', text='', show=''):
    return canon_channel(_channel_of(outlet, medium, network, url, html, text, show))


def _channel_of(outlet, medium='', network='', url='', html='', text='', show=''):
    """AVSHOW-v1: the channel/station/network/publisher that carried the item ('' when not stated). First match wins:
    NewsBank "[NET]" bracket; program-named outlet -> its network (table / Network / URL domain); known channel+show
    outlet split; page evidence; else the Coverage Outlet when it is not the show itself and not a bare domain.
    A host platform (podbean, Apple, Spotify, SoundCloud ...) is never a channel."""
    o = s(outlet)
    m = re.search(r'\[([^\]]+)\]\s*$', o)
    if m:
        return _canon_net(m.group(1))
    if o.lower() in PROGRAM_NET:
        return s(network) or PROGRAM_NET[o.lower()]
    h = host_of(url)
    if (not o or _is_domain(o)) and h in DOMAIN_NET:
        return DOMAIN_NET[h]
    ch, _ = _split(o)
    if ch:
        return ch
    pc = _page_channel(html) if medium in ('Podcast', 'Radio', 'Video') or EPISODE_HOST.search(h) or 'youtu' in h else ''
    if pc and (not o or _is_domain(o) or s(show).lower() == o.lower() or PLATFORM.search(o) or medium == 'Podcast'):
        return pc
    if o and not _is_domain(o) and not PLATFORM.search(o) and o.lower() != s(show).lower():
        return o
    return ''


def _show_from_page(html, url):
    h, u = html or '', s(url)
    m = re.search(r'tvmaze\.com/episodes/\d+/([a-z0-9-]+?)-\d+x\d+', u)
    if m:
        return m.group(1).replace('-', ' ').title()
    hh = host_of(u)
    if re.search(r'podbean\.com|omny\.fm|buzzsprout|libsyn|spreaker|captivate|transistor', hh):
        m = re.search(r'"Program"\s*:\s*\{[^{}]*?"Name"\s*:\s*"([^"]{2,100})"', h)
        if m:
            return _html.unescape(m.group(1)).strip()
        t = _meta(h, 'og:title') or (re.search(r'(?is)<title[^>]*>(.*?)</title>', h).group(1) if re.search(r'(?is)<title[^>]*>(.*?)</title>', h) else '')
        t = _html.unescape(re.sub(r'\s+', ' ', t)).strip()
        m = re.match(r'^.+\s(?:\||-|–)\s([^|–]+?)\s*$', t)
        v = re.sub(r'[™®]', '', m.group(1)).strip() if m else ''
        if v and not PLATFORM.search(v) and re.search(r'[A-Za-z]{3}', v) and not re.match(r'^[\d\s/.,:-]+$|^\d{4}-\d{2}', v):
            return v
    m = re.search(r'(?i)About the ([A-Z][\w\'&. ]{1,60}? Podcast)\b', h)
    if m:
        return m.group(1).strip()
    m = re.search(r'(?is)class="[^"]*\bseries[^"]*"[^>]*>\s*(?:<[^>]+>\s*)*(?:Series\s*)?([^<]{2,60})<', h)
    if m and m.group(1).strip().lower() not in ('series', ''):
        return _html.unescape(m.group(1)).strip()
    return ''


def station_show(html):
    """station video page: the show only from the MAIN clip's own description ("This segment aired on the <Show> on <date>");
    sidebar / related videos are never read (DECISIONS 188 rule)"""
    d = _meta(html, 'og:description') or _meta(html, 'description')
    m = re.search(r'(?i)\baired on (?:the )?(.+?)\s+on\s+(?:[A-Z][a-z]+day,?\s+)?[A-Z][a-z]+\.? \d{1,2}', d)
    return m.group(1).strip() if m else ''


# NOSHOWCHAN-v1 (Sammy 2026-10-28): a channel/station/network name never sits in Show/program
_STATION_NAME = re.compile(r'(?i)^(?:[KW][A-Z]{2,3}(?:-(?:TV|FM|AM|DT|CD|LD))?(?:\s+(?:\d{1,4}(?:\.\d)?|FOX|NBC|ABC|CBS|CW|TV|FM|AM))*'
                           r'|(?:ABC|NBC|CBS|FOX|CW|KCAL|Telemundo|Univision)\s?\d{1,2}(?:\.\d)?)$')   # v20-channel: AM dials (KNX 1070)
# v20-channel: words that make a station-prefixed name a program ("KTLA 5 Morning News"), so an Outlet that equals it keeps its Show
_PROGRAM_WORDS = re.compile(r'(?i)\b(morning|evening|nightly|midday|noon|night|weekend|sunday|saturday|newshour|report|update|'
                            r'news at|this week|in focus|press|forum|roundtable)\b')


def _nk(v):
    return re.sub(r'[^a-z0-9]+', ' ', s(v).lower()).strip()


def _outlet_is_program(outlet, medium='', channel=''):
    """the Outlet names the program itself (podcast outlets, "CBS Evening News", "The John Kobylt Show" with Channel KFI)"""
    o = s(outlet)
    return (o.lower() in PROGRAM_NET or bool(SHOWY.search(o)) or bool(_PROGRAM_WORDS.search(o)) or medium == 'Podcast'
            or bool(s(channel) and _nk(channel) != _nk(o)))


def is_channel_name(v, outlet='', channels=(), medium='', channel=''):
    """True when v names a channel/station/network: any known Channel value, a network, a station pattern (K/W call letters
    with optional -TV/number/network; 'ABC7', 'FOX 11'), or the row's Outlet when that Outlet is a channel and not the
    program itself (podcast / program-named outlets, or a row whose Channel is another name, keep their Show)"""
    k = _nk(v)
    if not k:
        return False
    if k in {_nk(c) for c in channels if c} or k in {_nk(n) for n in NETWORKS}:
        return True
    if k == _nk(outlet) and not _outlet_is_program(outlet, medium, channel):
        return True
    t = s(v)
    m = _STATION_NAME.match(t)
    return bool(m) and t.split()[0].upper() not in _NOT_CALL


def guard_show(row, outlet='', channels=()):
    """NOSHOWCHAN-v1: if row['Show/program'] is a channel name it moves to Channel (when Channel is blank) and Show is blanked.
    Returns the moved value ('' when nothing moved)."""
    v = s(row.get('Show/program'))
    ch = s(row.get('Channel'))
    if not v or not is_channel_name(v, outlet, tuple(channels) + (ch,),
                                    s(row.get('Medium')), ch):
        return ''
    if not ch:
        row['Channel'] = v
    row['Show/program'] = ''
    return v


def show_of(outlet, medium, headline='', url='', html='', channel=''):
    """AVSHOW-v1: real program names only; never the channel."""
    o = s(outlet)
    m = re.match(r'^(.*?),\s*(The|La|El)\s*\[[^\]]+\]$', o)                   # "Story Is with Elex Michaelson, The [CNN]"
    if m:
        return f'{m.group(2)} {m.group(1)}'
    m = re.match(r'^(.*?)\s*\[[^\]]+\]$', o)                                  # "Morning Edition [NPR]"
    if m:
        return m.group(1)
    _, sh = _split(o)
    if sh:
        return sh
    m = re.search(r'\bFM\s+(.+?):\s*Audio$', o)                               # "LAist - 89.3 FM AirTalk: Audio"
    if m:
        return m.group(1)
    m = re.search(r'laist\.com/shows/([a-z0-9-]+)/', s(url))
    if m:
        return {'airtalk': 'AirTalk'}.get(m.group(1), m.group(1).replace('-', ' ').title())
    if o.lower() in PROGRAM_NET and o.lower() not in DOMAIN_NET:              # "CBS Evening News", "TODAY": the outlet is the program
        return o
    p = _show_from_page(html, url)
    if p and p.lower() != s(channel).lower() and not is_channel_name(p, o, (channel,), medium, channel):   # NOSHOWCHAN-v1
        return p
    if medium == 'Podcast' and o and not _is_domain(o) and not re.search(r'\b(AM|FM)\s*\d', o) and not _CALL.search(o) \
       and SHOWY.search(o) and o.lower() != s(channel).lower():
        m = re.match(r'^(.*?),\s*(The|La|El)$', o)
        return f'{m.group(2)} {m.group(1)}' if m else o
    return ''


# ---------------- item type ----------------
EPISODE_HOST = re.compile(r'(^|\.)(podbean\.com|buzzsprout\.com|soundcloud\.com|podcasts\.apple\.com|open\.spotify\.com|'
                          r'anchor\.fm|simplecast\.com|libsyn\.com|megaphone\.fm|omny\.fm|podcastrex\.com|captivate\.fm|'
                          r'transistor\.fm|spreaker\.com|iheart\.com/podcast)$', re.I)


def host_of(u):
    return re.sub(r'^www\.', '', re.sub(r'^[a-z]+://', '', s(u).lower()).split('/')[0].split(':')[0])


def is_transcript(text):
    """broadcast/podcast transcript: speaker labels or time markers"""
    t = text or ''
    up = len(re.findall(r'(?m)^\s*[A-Z][A-Z .\'\-]{2,40}(?:,\s*[A-Z0-9 .,\'()&/\-]{2,80})?:\s', t))
    mixed = len(re.findall(r'(?m)^\s*[A-Z][a-z]+(?: [A-Z][a-z\'\-]+){1,2}:\s', t))
    marks = len(re.findall(r'\[\d{1,2}:\d{2}:\d{2}\]', t))
    return up >= 6 or marks >= 2 or (mixed >= 10 and re.search(r'(?i)transcript', t[:3000]) is not None)


def item_type(row, text):
    med, url, o = s(row.get('Medium')), s(row.get('Publisher link')), s(row.get('Outlet'))
    h = host_of(url)
    if archive_clip(url):
        return 'Broadcast segment'
    if is_transcript(text) and med in ('TV', 'Radio'):
        return 'Broadcast segment'
    if med == 'Podcast' and not h.endswith('iheart.com'):
        return 'Episode'
    if EPISODE_HOST.search(h) or re.search(r'laist\.com/shows/|/podcasts?/', url) or re.search(r'AirTalk|Political Breakdown', o):
        return 'Episode'
    if (re.search(r'\[[A-Z]+\]$', o) or s(row.get('_show'))) and med in ('TV', 'Radio') and not url:   # NewsBank program record ("Morning Edition [NPR]")
        return 'Broadcast segment'
    if med == 'Video' or re.search(r'/video/|youtube\.com/watch|youtu\.be/', url):
        return 'Video clip'
    if url or text:
        return 'Web story'
    return ''


# ---------------- page metadata ----------------
def duration_of(html, text):
    h, t = html or '', text or ''
    m = re.search(r'"duration"\s*:\s*"P?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?"', h)
    if m and any(m.groups()):
        return hms(int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + float(m.group(3) or 0))
    m = re.search(r'(?:property|name)="(?:og:video:duration|video:duration|itunes:duration)"\s+content="(\d+)"', h)
    if m:
        return hms(int(m.group(1)))
    m = re.search(r'(?i)\bDuration:?\s*(\d{1,2}:\d{2}(?::\d{2})?)(?:\.\d+)?\b', t)
    if m and m.group(1).strip('0:'):   # a video player's unloaded "Duration 0:00" is not a duration
        return m.group(1)
    m = re.search(r'\b[A-Z][a-z]{2} \d{1,2}, \d{4} \((\d{1,2}:\d{2}(?::\d{2})?)\)', t)      # CBS video page "Jan 25, 2025 (06:11)"
    if m:
        return re.sub(r'^0(\d:)', r'\1', m.group(1))
    m = re.findall(r'(?m)^\s*Listen\s*\n+\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*$', t)        # LAist segment page "Listen 29:16" (one segment only)
    if len(m) == 1:
        return m[0]
    m = re.findall(r'(?m)^\s*(\d{1,3}) min\s*$', t)                                     # podcast host episode list "32 min"
    if len(set(m)) == 1:
        return m[0] + ' min'
    return ''


_MON = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


def _ymd(mon, d, y):
    k = mon[:3].lower()
    return f'{int(y):04d}-{_MON.index(k) + 1:02d}-{int(d):02d}' if k in _MON else ''


def page_date(text, html=''):
    """AVTAB-v3: the page's own date for the item -> 'YYYY-MM-DD' ('' if absent or ambiguous). Sources: CBS video page
    'Jul 12, 2023 (03:57)'; Nexstar 'Posted: May 22, 2023 / 02:54 PM PDT'; JSON-LD uploadDate / datePublished;
    meta article:published_time. Station pages list sidebar videos with their own dates, so each source counts only
    when it gives ONE distinct date, and sources must agree; otherwise ''."""
    t, h = text or '', html or ''
    groups = []
    g = {_ymd(*m.groups()) for m in re.finditer(r'\b([A-Z][a-z]{2}) (\d{1,2}), (\d{4}) \(\d{1,2}:\d{2}', t)}
    groups.append(g)
    g = {_ymd(*m.groups()) for m in re.finditer(r'(?i)\bPosted:?\s*([A-Z][a-z]{2,8})\.? (\d{1,2}), (\d{4})', t)}
    groups.append(g)
    g = {m.group(1) for m in re.finditer(r'"(?:uploadDate|datePublished)"\s*:\s*"(\d{4}-\d{2}-\d{2})', h)}
    groups.append(g)
    v = _meta(h, 'article:published_time')
    groups.append({v[:10]} if re.match(r'\d{4}-\d{2}-\d{2}', v) else set())
    found = set()
    for g in groups:
        g.discard('')
        if len(g) > 1:
            return ''          # several dates in one source: sidebar/related items -> not the main clip's date
        found |= g
    return found.pop() if len(found) == 1 else ''


def _days(a, b):
    try:
        return abs((datetime.date.fromisoformat(a[:10]) - datetime.date.fromisoformat(b[:10])).days)
    except Exception:
        return None


def station_video(row, typ=''):
    """a TV station's own video page (KTLA/FOX40/NBC/FOX 11/CBS ...): Video clip on the station's site, not YouTube/archive.org"""
    url, med = s(row.get('Publisher link')), s(row.get('Medium'))
    h = host_of(url)
    if not url or archive_clip(url) or re.search(r'youtube\.com|youtu\.be|vimeo\.com|facebook\.com|tiktok\.com|instagram\.com', h):
        return False
    return (typ == 'Video clip' or '/video/' in url) and med in ('TV', 'Video')


def save_day(src='', today=''):
    """the save/fetch day this extract runs for: `today`, or the date in src ('Update button 2026-10-20', 'page fetch (…)')"""
    m = re.search(r'\d{4}-\d{2}-\d{2}', s(today)) or re.search(r'\d{4}-\d{2}-\d{2}', s(src))
    return m.group(0) if m else ''


def episode_number(*vals):
    for v in vals:
        m = re.search(r'(?i)\b(?:EP|Ep\.?|Episode|ep)\s*#?\s*(\d{1,4})\b', s(v)) or re.search(r'(?i)podcast-ep(\d{1,5})\b', s(v))
        if m:
            return m.group(1)
    return ''


def platform_links(*blobs, youtube=True):
    out = {'Apple Podcasts link': '', 'Spotify link': '', 'YouTube link': '', 'Archive.org link': ''}
    pats = {'Apple Podcasts link': r'https?://podcasts\.apple\.com/[^\s"\'<>|]+',
            'Spotify link': r'https?://open\.spotify\.com/(?:episode|show)/[^\s"\'<>|?]+',
            'YouTube link': r'https?://(?:www\.)?(?:youtube\.com/watch\?v=[\w-]+|youtu\.be/[\w-]+)',
            'Archive.org link': r'https?://(?:www\.)?archive\.org/details/[A-Z0-9]+_\d{8}_\d{6}_[^\s"\'<>|]+'}
    if not youtube:   # a page's outbound-link list carries related videos: no YouTube link from it
        pats.pop('YouTube link')
    for k, p in pats.items():   # only when the page carries exactly one candidate (related-video lists are skipped)
        found = []
        for b in blobs:
            for m in re.finditer(p, b or ''):
                u = _html.unescape(m.group(0)).rstrip('.,);')
                u = re.sub(r'[?&]si=[^&]*$', '', u) if 'spotify' in u else u
                if u not in found:
                    found.append(u)
        if len(found) == 1:
            out[k] = found[0]
    return out


# ---------------- transcripts: role, guests, mention timestamps ----------------
STAFF = re.compile(r'(?i)\b(anchor|host|co-host|correspondent|reporter|contributor|analyst|meteorologist|producer|'
                   r'commentator|moderator|announcer|chief|editor|bureau)\b')
_UPLABEL = re.compile(r'(?m)^\s*([A-Z][A-Z .\'\-]{2,40})(?:,\s*([A-Z0-9 .,\'()&/\-]{2,90}))?:\s')
_MIXLABEL = re.compile(r'(?m)^\s*([A-Z][a-z]+(?: [A-Z][a-z\'\-]+){1,2}):\s')
_TIMEMARK = re.compile(r'\[(\d{1,2}:\d{2}:\d{2})\]')
_GAB = re.compile(r'\bGabriel\b', re.I)


def _title(n):
    return ' '.join(w.capitalize() if w.isupper() else w for w in n.split()).replace("'S", "'s")


def transcript_details(text):
    """-> dict(role, guests[], mentions[], basis) from a speaker-labelled transcript"""
    t = text or ''
    labels = list(_UPLABEL.finditer(t)) or list(_MIXLABEL.finditer(t))
    his = [m for m in labels if re.search(r'\bGABRIEL\b', m.group(1), re.I)]
    mentions = [m.start() for m in _GAB.finditer(t)]
    # mentions that are not his own speaker label
    named = [p for p in mentions if not any(m.start() <= p < m.end() for m in his)]
    role = ''
    if his:
        first = his[0].start()
        intro = t[max(0, first - 600):first]
        if re.search(r'(?i)joining (me|us)|joins (me|us)|with (me|us) now|welcome|good to have you|thank(s| you) for (being|joining|coming)', intro):
            role = 'guest'
        elif len(his) >= 3:
            role = 'interviewed'
        else:
            role = 'soundbite'
    elif len(named) >= 2:
        role = 'discussed'
    elif len(named) == 1:
        role = 'brief mention'
    # segment that names him: between commercial breaks
    p0 = (his[0].start() if his else (named[0] if named else 0))
    cuts = [m.end() for m in re.finditer(r'\((?:COMMERCIAL BREAK|BEGIN VIDEOTAPE|END VIDEOTAPE)\)|\(COMMERCIAL BREAK\)', t) if 'COMMERCIAL' in m.group(0)]
    a = max([c for c in cuts if c <= p0] or [0])
    b = min([c for c in cuts if c > p0] or [len(t)])
    guests = []
    for m in labels:
        if a <= m.start() < b and len(m.groups()) > 1 and m.group(2) and not STAFF.search(m.group(2) or '') and m.group(1).strip() not in ('UNIDENTIFIED MALE', 'UNIDENTIFIED FEMALE'):
            n = _title(m.group(1))
            if n not in guests:
                guests.append(n)
    marks = [(m.start(), m.group(1)) for m in _TIMEMARK.finditer(t)]
    ts = []
    for p in ([m.start() for m in his] + named):
        prev = [v for q, v in marks if q <= p]
        if prev and prev[-1] not in ts:
            ts.append(prev[-1])
    ts.sort()
    return {'role': role, 'guests': guests, 'mentions': ts, 'basis': 'transcript time marker before the mention' if ts else ''}


def caption_mentions(text):
    return len(_GAB.findall(text or ''))


# ---------------- one tab row ----------------
def blank_row():
    return {c: '' for c in COLS}


def extract(row, html='', text='', src='', today=''):
    """row: Coverage cells (dict col -> value) of a Podcast/Radio/TV/Video row; html/text: its saved copy (may be '').
    -> dict COLS -> value (blanks where not established)"""
    r = {k: s(v) for k, v in row.items()}
    text = text or (strip_html(html) if html else '')
    out = blank_row()
    out.update({'Article ID': r.get('Article ID', ''), 'Story ID': r.get('Story ID', ''), 'Medium': r.get('Medium', '')})
    url, hl, o, med = r.get('Publisher link', ''), r.get('Headline', ''), r.get('Outlet', ''), r.get('Medium', '')
    frm, notes = ['sheet'], []
    typ = item_type(r, text)
    out['Item type'] = typ
    st, net = station_network(o, hl)
    clip = archive_clip(url)
    if clip:
        st = st or clip['call']
    out['Station'], out['Network'] = st, net
    # AVSHOW-v1: Channel on every item type (Web story included; facets use it); Show = program names only
    if station_video(r, typ):   # main clip's own description only; a program-named outlet (TODAY) is itself the show
        show = station_show(html) or (show_of(o, med, hl, url) if o.lower() in PROGRAM_NET else '')
    else:
        show = show_of(o, med, hl, url, html)
    if r.get('_show'):   # SHOWNET-v1: the show split off a NewsBank "Show [Network]" Outlet by the importer
        show = r['_show']
    out['Channel'] = channel_of(o, med, net, url, html, text, show)
    out['Show/program'] = show if show.lower() != out['Channel'].lower() else ''
    guard_show(out, o)   # NOSHOWCHAN-v1
    if typ == 'Web story' or not typ:   # Web stories: Station/Network/Channel only (Channel feeds the facets)
        out['Show/program'] = ''
        out['Details from'] = 'sheet'
        return out
    t_hl = hl
    m = re.match(r'^(.*\S)\s*\|\s*([^|]+)$', hl)
    if m and o and (m.group(2).strip().lower() in o.lower() or o.lower() in m.group(2).lower()):   # "... | KFI AM 640"
        t_hl = m.group(1)
    t_hl =re.sub(r'\.?\s*Aired\s+[\d:\-–apmAPM ]+(?:ET|PT|CT)\.?\s*$', '', t_hl).strip()
    if clip:
        frm.append('archive.org clip ID')
        m = re.match(r'^(.*?)\s*\([^()]*\([A-Z0-9]+\)\)\s*$', hl)
        out['Show/program'] = (m.group(1) if m else clip['show']).strip()
        loc = clip['local']
        out['Air/publish date'] = loc.strftime('%Y-%m-%d')
        out['Air time'] = loc.strftime('%H:%M') + ' PT'
        out['Archive.org link'] = clip['url']
        if clip['start'] is not None:
            out['Mention 1'] = hms(clip['start'])
            out['Timestamp basis'] = 'offset into the program (TV News Archive clip start)'
        if r.get('Date', '')[:10] and r.get('Date', '')[:10] != out['Air/publish date']:
            notes.append(f"Coverage Date {r['Date'][:10]} is the clip ID's UTC date ({clip['utc']:%Y-%m-%d %H:%M} UTC), aired {out['Air/publish date']} {out['Air time']}")
        if text:
            out['Transcript kind'] = 'excerpts'
            out['Transcript file'] = r.get('File name', '')
            notes.append('saved copy = TV captions around the clip (lower case, speakers not named)')
            frm.append('saved copy')
    else:
        out['Episode/segment title'] = t_hl
        cov = r.get('Date', '')[:10] if re.match(r'^\d{4}-\d{2}-\d{2}$', r.get('Date', '')[:10]) else ''
        if station_video(r, typ):
            # AVTAB-v3 (DECISIONS 188): station video pages carry no date for the main clip; never take a date that
            # sits within 3 days of the save/fetch day (sidebar videos / the save day itself)
            sd = save_day(src, today)
            pd_ = page_date(text, html)
            if pd_ and sd and (_days(pd_, sd) or 0) <= 3:
                pd_ = ''
            if pd_:
                out['Air/publish date'] = pd_
                frm.append('page date')
            elif cov and not (sd and (_days(cov, sd) or 0) <= 3):
                out['Air/publish date'] = cov
            elif cov:
                notes.append(f'air date not established: station video page has no date for the clip; Coverage Date {cov} '
                             f'is within 3 days of the save day {sd}')
        elif cov:
            out['Air/publish date'] = cov
        m = re.search(r'Aired\s+([\d:\-–apmAPM ]+(?:ET|PT|CT))', hl)
        if m:
            out['Air time'] = m.group(1).strip()
    out['Episode number'] = episode_number(hl, url, text[:600])
    out['Duration'] = duration_of(html, text)
    pdte = page_date(text, html) if not station_video(r, typ) else ''
    if pdte and r.get('Date', '') and not pdte.startswith(r['Date'][:10]):
        notes.append(f"page dates it {pdte}; Coverage Date is {r['Date']}")
    if text and not clip:
        frm.append('saved copy')
        if is_transcript(text):
            d = transcript_details(text)
            out['His role'] = d['role']
            fill_numbered(out, 'Guest', N_GUEST, 'Guests (more)', d['guests'])
            fill_numbered(out, 'Mention', N_MENTION, 'Mentions (more)', d['mentions'])
            out['Timestamp basis'] = d['basis']
            out['Transcript kind'] = 'full'
            out['Transcript file'] = r.get('File name', '')
        else:
            out['Transcript kind'] = 'none'
            low = text[:4000]
            if re.search(r'(?i)(joined by|joins|sits down with|talks with|speaks with|interview(s|ed)? with|our guest[s]?|featuring|guests?:)[^.\n]{0,120}\bJesse Gabriel\b', low) \
               or re.search(r'(?i)\bwith\b[^|]{0,60}\bJesse Gabriel\b', hl) or re.search(r'(?i)^(Asm\.|Assemblymember|Assemblyman)?\s*Jesse Gabriel (on|talks|discusses|joins)\b', hl):
                out['His role'] = 'guest'
    pl = platform_links(html, text, url, youtube=not src.startswith('page fetch'))
    for k, v in pl.items():
        if v and not out.get(k):
            out[k] = v
    if url and not archive_clip(url) and not re.search(r'podcasts\.apple\.com|open\.spotify\.com|youtube\.com|youtu\.be|exa\.ai/', url) \
       and typ in ('Episode', 'Video clip', 'Broadcast segment'):
        out['Show page link'] = url
    for k, p in (('Apple Podcasts link', 'podcasts.apple.com'), ('Spotify link', 'open.spotify.com'), ('YouTube link', 'youtu')):
        if p in url and not out[k]:
            out[k] = url
    guard_show(out, o)   # NOSHOWCHAN-v1 (archive.org / page show names too)
    if src:
        frm.append(src)
    out['Details from'] = '; '.join(dict.fromkeys(frm))
    out['Notes'] = '; '.join(notes)
    return out



# ---------------- REVIEW4-v1 rules (F1 / F3 / F4 / F5 / F6) ----------------
_TZ = {'PT': 'America/Los_Angeles', 'PST': 'America/Los_Angeles', 'PDT': 'America/Los_Angeles', 'ET': 'America/New_York', 'EST': 'America/New_York',
       'EDT': 'America/New_York', 'CT': 'America/Chicago', 'CST': 'America/Chicago', 'CDT': 'America/Chicago', 'MT': 'America/Denver',
       'MST': 'America/Denver', 'MDT': 'America/Denver', 'UTC': 'UTC', 'GMT': 'UTC'}


def to_pacific(date, time, tz='PT'):
    """F1: a broadcast/audio air date + time in `tz` (ET, CT, UTC ...) -> (Pacific 'YYYY-MM-DD', 'H:MM am/pm PT', source note).
    A source time of 9:00 pm ET on 2026-09-08 is 6:00 pm PT the same day; 11:00 pm PT on the 8th is the 9th in ET, so the
    Coverage Date stays the PACIFIC date. ('', '', '') when the date or time cannot be read."""
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', s(date))
    t = re.match(r'(\d{1,2}):(\d{2})\s*([ap]m)?', s(time).lower())
    z = _TZ.get(s(tz).upper().replace('.', ''))
    if not (m and t and z):
        return '', '', ''
    hh, mm = int(t.group(1)), int(t.group(2))
    if t.group(3) == 'pm' and hh < 12:
        hh += 12
    if t.group(3) == 'am' and hh == 12:
        hh = 0
    from zoneinfo import ZoneInfo
    src = datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), hh, mm, tzinfo=ZoneInfo(z))
    pt = src.astimezone(ZoneInfo('America/Los_Angeles'))
    h12 = pt.hour % 12 or 12
    return (pt.strftime('%Y-%m-%d'), '%d:%02d %s PT' % (h12, pt.minute, 'am' if pt.hour < 12 else 'pm'),
            'source time %s %s %s' % (s(date)[:10], s(time), s(tz).upper()))


def role_depth(role, depth=''):
    """F3: a guest (or a moderator) of the segment/episode is Featured; other roles keep the depth the text rule gave."""
    return 'Featured' if s(role).lower() in ('guest', 'moderator') else depth


def spoken_quoted(role, text=''):
    """F4: transcribed on-air speech is a quote. True when he is a guest/interviewed/soundbite/moderator AND a transcript turn
    is labelled with his name (GABRIEL: ...), or the role is guest/interviewed on a transcript."""
    r = s(role).lower()
    if r in ('discussed', 'brief mention', ''):
        return False
    return bool(re.search(r'(?im)^\s*(?:ASM(?:BLY)?\.?\s+|ASSEMBLY(?:MAN|MEMBER)\s+)?(?:JESSE\s+)?GABRIEL(?:,[^:\n]{0,60})?:\s', text or '')) \
        or (r in ('guest', 'interviewed', 'moderator') and bool(re.search(r'(?i)\bGABRIEL\b', text or '')) and is_transcript(text or ''))


def _ep_key(v):
    return re.sub(r'[^a-z0-9]+', ' ', s(v).lower()).strip()


def same_episode(a, b):
    """F5: two AV rows are ONE story (platform editions) when the show matches and the episode number or title matches and the
    dates are within 2 days, whatever the platform (Apple, Spotify, YouTube, show page)."""
    sa, sb = _ep_key(a.get('Show/program') or a.get('Channel')), _ep_key(b.get('Show/program') or b.get('Channel'))
    if not sa or sa != sb:
        return False
    ea, eb = s(a.get('Episode number')), s(b.get('Episode number'))
    ta, tb = _ep_key(a.get('Episode/segment title')), _ep_key(b.get('Episode/segment title'))
    if not ((ea and ea == eb) or (ta and ta == tb)):
        return False
    da, db_ = s(a.get('Air/publish date'))[:10], s(b.get('Air/publish date'))[:10]
    try:
        return abs((datetime.date.fromisoformat(da) - datetime.date.fromisoformat(db_)).days) <= 2
    except Exception:
        return not da or not db_


def medium_rule(is_station_program, is_video=False):
    """F6: a station's program is Radio, a station's video is TV, an independent show is Podcast."""
    if is_station_program:
        return 'TV' if is_video else 'Radio'
    return 'Podcast'

# ---------------- workbook ----------------
def write_tab(wb, rows, after='Press releases'):
    """create the tab (if missing) and append rows (dicts COLS -> value); returns the worksheet. Header bold, frozen,
    filtered; widths from WIDTHS. Existing rows (by Article ID) are never changed."""
    from openpyxl.styles import Font, Alignment
    from openpyxl.utils import get_column_letter
    if TAB in wb.sheetnames:
        ws = wb[TAB]
    else:
        idx = wb.sheetnames.index(after) + 1 if after in wb.sheetnames else len(wb.sheetnames)
        ws = wb.create_sheet(TAB, idx)
        for i, c in enumerate(COLS, 1):
            x = ws.cell(1, i, c)
            x.font = Font(bold=True)
            x.alignment = Alignment(vertical='top', wrap_text=True)
            ws.column_dimensions[get_column_letter(i)].width = WIDTHS.get(c, 22 if 'link' in c else 14)
        ws.freeze_panes = 'B2'
    H = {ws.cell(1, i).value: i for i in range(1, ws.max_column + 1)}
    have = {s(ws.cell(r, H['Article ID']).value) for r in range(2, ws.max_row + 1)}
    n = 0
    for row in rows:
        if s(row.get('Article ID')) in have:
            continue
        r = ws.max_row + 1
        for c in COLS:
            v = row.get(c, '')
            if v in ('', None) or c not in H:
                continue
            cell = ws.cell(r, H[c], v)
            if c == 'Air/publish date' and re.match(r'^\d{4}-\d{2}-\d{2}$', str(v)):
                cell.value = datetime.datetime.strptime(v, '%Y-%m-%d')
                cell.number_format = 'yyyy-mm-dd'
            if c.endswith('link') and str(v).startswith('http'):
                cell.hyperlink = v
        have.add(s(row.get('Article ID')))
        n += 1
    ws.auto_filter.ref = f'A1:{get_column_letter(len(COLS))}{max(ws.max_row, 1)}'
    return ws


def read_tab(path_or_wb):
    """-> {Article ID: {col: value}} ({} when the tab is missing)"""
    import openpyxl
    wb = path_or_wb if hasattr(path_or_wb, 'sheetnames') else openpyxl.load_workbook(path_or_wb, read_only=True, data_only=True)
    if TAB not in wb.sheetnames:
        return {}
    rows = wb[TAB].iter_rows(values_only=True)
    hdr = [s(h) for h in next(rows, [])]
    out = {}
    for v in rows:
        d = {h: s(x) for h, x in zip(hdr, v) if h}
        if d.get('Article ID'):
            out[d['Article ID']] = d
    return out


def block(path_or_wb):
    """tracker block `av`: {"v":1, "cols": KEYS, "rows": {aid: [values in KEYS order]}} (trailing blanks trimmed)"""
    rows = {}
    for aid, d in read_tab(path_or_wb).items():
        vals = [d.get(c, '') for c in COLS[1:]]
        while vals and vals[-1] == '':
            vals.pop()
        rows[aid] = vals
    return {'v': 1, 'cols': KEYS, 'rows': rows}
