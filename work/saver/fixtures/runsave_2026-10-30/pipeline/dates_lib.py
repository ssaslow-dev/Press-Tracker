"""DATES-v1 helpers shared by the dates-apply scripts (and mirrored in patches/): outlet zone, local-day conversion,
displayed-date parsing. Pure functions, no I/O."""
import re, datetime as dt
from zoneinfo import ZoneInfo

US_ZONE = {
    'CA': 'America/Los_Angeles', 'WA': 'America/Los_Angeles', 'OR': 'America/Los_Angeles', 'NV': 'America/Los_Angeles',
    'AZ': 'America/Phoenix', 'ID': 'America/Boise', 'MT': 'America/Denver', 'WY': 'America/Denver', 'UT': 'America/Denver',
    'CO': 'America/Denver', 'NM': 'America/Denver',
    'TX': 'America/Chicago', 'OK': 'America/Chicago', 'KS': 'America/Chicago', 'NE': 'America/Chicago', 'SD': 'America/Chicago',
    'ND': 'America/Chicago', 'MN': 'America/Chicago', 'IA': 'America/Chicago', 'MO': 'America/Chicago', 'AR': 'America/Chicago',
    'LA': 'America/Chicago', 'MS': 'America/Chicago', 'AL': 'America/Chicago', 'TN': 'America/Chicago', 'WI': 'America/Chicago',
    'IL': 'America/Chicago',
    'NY': 'America/New_York', 'GA': 'America/New_York', 'FL': 'America/New_York', 'NC': 'America/New_York', 'OH': 'America/New_York',
    'SC': 'America/New_York', 'PA': 'America/New_York', 'VA': 'America/New_York', 'DC': 'America/New_York', 'MI': 'America/New_York',
    'MA': 'America/New_York', 'KY': 'America/New_York', 'CT': 'America/New_York', 'IN': 'America/New_York', 'NJ': 'America/New_York',
    'MD': 'America/New_York', 'RI': 'America/New_York', 'NH': 'America/New_York', 'WV': 'America/New_York', 'VT': 'America/New_York',
    'ME': 'America/New_York', 'DE': 'America/New_York',
    'AK': 'America/Anchorage', 'HI': 'Pacific/Honolulu', 'Puerto Rico': 'America/Puerto_Rico',
}
FOREIGN_ZONE = {
    'England': 'Europe/London', 'UK': 'Europe/London', 'Israel': 'Asia/Jerusalem', 'India': 'Asia/Kolkata',
    'New Zealand': 'Pacific/Auckland', 'Mexico': 'America/Mexico_City', 'Argentina': 'America/Argentina/Buenos_Aires',
    'Jordan': 'Asia/Amman', 'Armenia': 'Asia/Yerevan', 'South Africa': 'Africa/Johannesburg', 'Spain': 'Europe/Madrid',
    'Peru': 'America/Lima', 'Nigeria': 'Africa/Lagos', 'Brunei Darussalam': 'Asia/Brunei', 'Australia': 'Australia/Sydney',
    'China': 'Asia/Shanghai', 'Canada': 'America/Toronto', 'Philippines': 'Asia/Manila', 'Africa': 'Africa/Johannesburg',
    'Asia': 'Asia/Shanghai',
}
PACIFIC = 'America/Los_Angeles'


def zone_for(state):
    """Outlet state -> IANA zone. CA / USA -> Pacific (DATES-v1: US outlets their local time, Pacific default).
    v22 zone guard: a BLANK state returns None (zone unknown): local_day then never assumes Pacific for what may be an
    Eastern outlet (see local_day)."""
    s = str(state or '').strip() if state == state else ''
    if not s:
        return None
    return US_ZONE.get(s) or FOREIGN_ZONE.get(s) or PACIFIC


def _in_zone(base_utc, zone):
    """v22 zone guard: zone None (outlet state unknown) -> the Pacific day when Pacific and Eastern agree, else the Eastern
    day (a UTC evening stamp is never back-shifted to the previous day on a guess)"""
    if zone:
        return base_utc.astimezone(ZoneInfo(zone)).date().isoformat()
    pt, et = (base_utc.astimezone(ZoneInfo(z)).date().isoformat() for z in (PACIFIC, 'America/New_York'))
    return pt if pt == et else et


# hosts whose CMS writes a zone-less ISO stamp that is really UTC (auditor: LA Times, NPR member stations, Politico,
# Courthouse News) -- an hour before 08:00 with no zone is treated as UTC
UTC_NAKED_HOSTS = re.compile(r'(^|\.)(latimes\.com|politico\.com|politicopro\.com|courthousenews\.com|kvpr\.org|mynspr\.org|capradio\.org|kqed\.org|kcrw\.com|kpbs\.org|kcbx\.org|kazu\.org|kclu\.org|ijpr\.org|npr\.org|laist\.com|scpr\.org)$', re.I)

ISO = re.compile(r'^(\d{4})-(\d\d)-(\d\d)(?:[T ](\d\d):(\d\d)(?::(\d\d(?:\.\d+)?))?\s*(Z|UTC|GMT|[+-]\d\d:?\d\d)?)?$', re.I)


def local_day(stamp, zone=PACIFIC, host='', naked_utc_before=8):
    """ISO timestamp -> calendar date in `zone`.
    - 'Z'/'+00:00': UTC -> convert to `zone` (a 00:00 UTC stamp keeps its own date: site clock, never back-shifted).
    - any other offset: the stamp is already the publisher's local time -> its own date.
    - no time part: the date as given.
    - no zone: the stamp is taken as already local, except on UTC_NAKED_HOSTS (or when naked_utc_before covers it: hour
      < naked_utc_before on those hosts) where it is UTC.
    Returns '' when the stamp cannot be read."""
    s = str(stamp or '').strip()
    m = ISO.match(s)
    if not m:
        return ''
    y, mo, d, hh, mi, ss, tz = m.groups()
    if hh is None:
        return f'{y}-{mo}-{d}'
    try:
        base = dt.datetime(int(y), int(mo), int(d), int(hh), int(mi), int(float(ss or 0)))
    except ValueError:
        return ''
    if tz:
        if tz.upper() in ('Z', 'UTC', 'GMT') or re.fullmatch(r'[+-]00:?00', tz):
            # a UTC stamp at exactly midnight is a site clock (weeklies, CMS issue dates): keep its own date (DATES-v1)
            if base.hour == 0 and base.minute == 0:
                return base.date().isoformat()
            return _in_zone(base.replace(tzinfo=dt.timezone.utc), zone)
        # a stamp with its own non-UTC offset is already written in the publisher's local time: its date stands
        return base.date().isoformat()
    # zone-less
    if host and UTC_NAKED_HOSTS.search(host) and base.hour < naked_utc_before:
        return _in_zone(base.replace(tzinfo=dt.timezone.utc), zone)
    return base.date().isoformat()


MON = {m: i + 1 for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}
MONRE = r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
D_LONG = re.compile(r'\b' + MONRE + r'\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b', re.I)
D_DMY = re.compile(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+' + MONRE + r'\.?,?\s+(\d{4})\b', re.I)
D_ISO = re.compile(r'\b((?:19|20)\d\d)-(\d\d)-(\d\d)\b')
D_US = re.compile(r'\b(\d{1,2})/(\d{1,2})/((?:19|20)\d\d)\b')
TZ_WORD = re.compile(r'\b([AP]\.?M\.?)\s*,?\s*(P[SD]?T|E[SD]?T|C[SD]?T|M[SD]?T|UTC|GMT)\b', re.I)
LABEL = re.compile(r'(Published(?: on)?|Posted(?: on)?|Updated|Last updated|Modified|Date)\s*:?\s*', re.I)


def ymd(y, m, d):
    try:
        return dt.date(int(y), int(m), int(d)).isoformat()
    except Exception:
        return ''


def text_dates(text, limit=None):
    """All calendar dates written in `text` (long form, d-m-y, ISO, m/d/y) in order: [(pos, 'YYYY-MM-DD', context)]."""
    t = text if limit is None else text[:limit]
    out = []
    for m in D_LONG.finditer(t):
        out.append((m.start(), ymd(m.group(3), MON[m.group(1)[:3].lower()], m.group(2)), m))
    for m in D_DMY.finditer(t):
        out.append((m.start(), ymd(m.group(3), MON[m.group(2)[:3].lower()], m.group(1)), m))
    for m in D_ISO.finditer(t):
        out.append((m.start(), ymd(*m.groups()), m))
    for m in D_US.finditer(t):
        out.append((m.start(), ymd(m.group(3), m.group(1), m.group(2)), m))
    res = []
    for pos, v, m in sorted(out, key=lambda x: x[0]):
        if not v:
            continue
        ctx = t[max(0, pos - 70):m.end() + 40].replace('\n', ' ')
        res.append((pos, v, ctx))
    return res


_BY_START = re.compile(r"(?:^|[\n\r|·•]|[-–—,(]\s|\b(?:story|written|reported|report|posted|published|text|words|article|compiled)\s)\s*by\s+", re.I)
_BY_CAP = re.compile(r"\b(?:By|BY):?\s+")
_BY_WORDS = {'to', 'on', 'admin', 'author', 'staff-author', 'and', 'de', 'la', 'van', 'von', 'der', 'del', 'di', 'da', 'el', 'al', 'bin', 'of', 'the', 'for', 'in',
             'at', 'pm', 'am', 'pt', 'pst', 'pdt', 'et', 'est', 'edt', 'ct', 'updated', 'published', 'posted', 'section', 'edition', 'by', 'with', 'from', 'staff',
             'writer', 'editor', 'reporter', 'min', 'read', 'jr', 'sr', 'ii', 'iii', 'news', 'service', 'times', 'press', 'associated'}
_MONTH_START = re.compile(r"^(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d", re.I)


def byline_before(before):
    """REQ-10 (mirror of the page's BYLINE_BEFORE): 'by <name>' that starts a line or follows a separator or a Written/Story/Posted word
    (or a capitalised 'By'), with at most an outlet, section or time between it and the date. Not 'signed by Governor ... on October 10',
    'Photo by X (Aug. 15)' or 'by June 1, 2029'."""
    last = None
    for rx in (_BY_START, _BY_CAP):
        for m in rx.finditer(before):
            if last is None or m.end() > last.end():
                last = m
    if last is None:
        return False
    tail = before[last.end():]
    rest = re.sub(r"\d{1,2}:\d\d\s*(?:[ap]\.?m\.?)?(?:\s+[A-Z]{2,4})?", ' ', tail, flags=re.I)
    rest = re.sub(r"[^\W\d_]+\d+", ' ', rest)
    low = [w for w in re.findall(r"(?:^|[\s(])([a-z][a-z'’.-]*)(?=$|[\s,;)])", rest) if w.lower().rstrip('.,') not in _BY_WORDS]
    if len(low) > 1:
        return False
    return (len(rest) <= 100 and re.search(r"[^\W\d_]{2}", rest) is not None and not re.search(r"\d", rest)
            and not _MONTH_START.match(tail) and not re.search(r"[.!?]\s+[a-z]", rest))


def stamp_ok(v, today=None):
    """No page stamp after tomorrow (Pacific; outlets east of LA run a day ahead) or before 1990."""
    t = (today or dt.datetime.now(ZoneInfo(PACIFIC)).date()) + dt.timedelta(days=1)
    return bool(re.match(r"^\d{4}-\d\d-\d\d$", v or '')) and '1990-01-01' <= v <= t.isoformat()


def displayed_stamp(text, limit=2500):
    """The page's own publish line, read from the (markdown) text near the top:
    returns (date, kind, context) with kind 'label' (Published/Posted ...), 'tzline' (date with h:mm pm TZ),
    'lead' (first date before the body), or ('', '', '') when none. 'Updated' lines are never taken as the date."""
    t = text or ''
    head = t[:limit]
    best = None
    for pos, v, ctx in text_dates(head):
        if not stamp_ok(v):
            continue
        before = head[max(0, pos - 40):pos]
        after = head[pos:pos + 80]
        lab = LABEL.search(before)
        if lab and re.search(r'updat|modif', lab.group(1), re.I) and lab.end() >= len(before) - 3:
            continue
        if lab and lab.end() >= len(before) - 3:
            return v, 'label', ctx
        if TZ_WORD.search(after) and best is None:
            best = (v, 'tzline', ctx)
        elif best is None and byline_before(head[max(0, pos - 140):pos]):
            best = (v, 'byname', ctx)
    return best or ('', '', '')


def updated_stamp(text, limit=2500):
    head = (text or '')[:limit]
    for pos, v, ctx in text_dates(head):
        before = head[max(0, pos - 40):pos]
        lab = LABEL.search(before)
        if lab and re.search(r'updat|modif', lab.group(1), re.I) and lab.end() >= len(before) - 3:
            return v
    return ''


def days_between(a, b):
    try:
        return (dt.date.fromisoformat(a[:10]) - dt.date.fromisoformat(b[:10])).days
    except Exception:
        return None
