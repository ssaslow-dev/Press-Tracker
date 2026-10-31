"""shownet.py - SHOWNET-v1 (Sammy 2026-10-29, comment on 00198 "See how it's a show on a network? Also fix the name of the show").

NewsBank writes a broadcast record's SOURCE as the show, inverted, with the network in brackets: "Story Is with Elex Michaelson, The [CNN]",
"Morning Edition [NPR]", "Mornings with Maria [Fox Business]", and puts access labels in brackets on print sources ("Valley News [30 Day Embargo]").
The Coverage Outlet is the network / station / publisher; the show goes in the Audio & video details tab ("Show/program"), un-inverted.

  split_outlet(raw, medium='', channel='') -> dict(outlet, show, network, label, kind)
      kind: 'network' (Show [NET]) | 'label' (access label stripped) | 'inverted' (show/podcast name un-inverted) | 'station' (talk-radio show -> its station) | ''
  uninvert("Story Is with Elex Michaelson, The") -> "The Story Is with Elex Michaelson"
  is_rundown(headline)  -> True for an episode rundown ("A; B; C; D") or a very long multi-topic string
  segment_headline(show, text, hit_re) -> "<Show>: <topic>" from the lead-in before his first mention ('' when nothing usable)

No file access; mirrored in the tracker JS (covOutletName / covShowSplit in 40_update_outlets.js).
"""
import re

# network brackets NewsBank uses, canonical spelling
NETWORKS = ['Fox Business', 'Fox News', 'CNN', 'MSNBC', 'CNBC', 'NPR', 'PBS', 'ABC', 'CBS', 'NBC', 'FOX', 'Bloomberg', 'C-SPAN', 'BBC', 'CBC',
            'Al Jazeera', 'NewsNation', 'Newsmax', 'Telemundo', 'Univision', 'Spectrum News', 'MyNetworkTV', 'CW', 'Reuters TV']
_CANON = {n.lower(): n for n in NETWORKS}
# access / status labels NewsBank appends in brackets to a source name; never part of the outlet
LABEL = re.compile(r'(?i)^\s*(?:\d+\s*-?\s*days?\s*embargo(?:ed)?|embargo(?:ed)?(?:\s+\d+\s*days?)?|subscription(?:\s+required)?|paid(?:\s+archive)?|archive|premium|'
                   r'registration(?:\s+required)?|pay\s*wall(?:ed)?|restricted|limited\s+access)\s*$')
_ART = r'(The|A|An|La|El|Los|Las|Le|Les|Il|Die|Der)'
_TRAIL_BRACKET = re.compile(r'\s*\[([^\[\]]+)\]\s*$')
# talk-radio hosts' station strings: call letters, "790 KABC", "News 93.1 KFBK", "KFI AM 640"
_STATION = re.compile(r'(?<![A-Za-z])[KW][A-Z]{2,3}(?:-(?:AM|FM|TV))?(?![A-Za-z])')


def _s(v):
    return '' if v is None else re.sub(r'\s+', ' ', str(v)).strip()


def canon_network(n):
    return _CANON.get(_s(n).lower(), _s(n))


def uninvert(name):
    """'Story Is with Elex Michaelson, The' -> 'The Story Is with Elex Michaelson' (a name without a trailing article is returned as is)"""
    n = _s(name)
    m = re.match(r'^(.*\S),\s*' + _ART + r'$', n)
    return f'{m.group(2)} {m.group(1)}' if m else n


def is_station(v):
    """a call-letter station string (KFI AM 640, 790 KABC, News 93.1 KFBK, KTRH)"""
    return bool(_STATION.search(_s(v)))


def split_outlet(raw, medium='', channel=''):
    """-> dict(outlet, show, network, label, kind). `channel` = the AV tab Channel/Station of the row (talk-radio shows resolve to it)."""
    o = _s(raw)
    out = {'outlet': o, 'show': '', 'network': '', 'label': '', 'kind': ''}
    if not o:
        return out
    m = _TRAIL_BRACKET.search(o)
    if m:
        inner, base = m.group(1).strip(), o[:m.start()].strip()
        if LABEL.match(inner):                      # "Valley News [30 Day Embargo]" -> "Valley News"
            out.update(outlet=base, label=inner, kind='label')
            return out
        net = canon_network(inner)
        if net.lower() in _CANON:                   # "Morning Edition [NPR]" -> outlet NPR, show "Morning Edition"
            out.update(outlet=net, show=uninvert(base), network=net, kind='network')
            return out
    # a show / podcast written inverted ("John Kobylt Show, The"): un-inverted; a talk-radio show whose channel is a station -> that station.
    # Only broadcast / podcast rows: a newspaper's "Sacramento Bee, The" keeps the NewsBank form (the display layer re-orders it).
    inv = re.match(r'^(.*\S),\s*' + _ART + r'$', o)
    if inv and (re.search(r'(?i)\b(show|podcast)\b', inv.group(1)) or _s(medium) in ('Podcast', 'TV', 'Radio')):
        show = uninvert(o)
        ch = _s(channel)
        if ch and is_station(ch) and (_s(medium) in ('Podcast', 'Radio') or re.search(r'(?i)\bshow\b', show)):
            out.update(outlet=ch, show=show, kind='station')
        else:
            out.update(outlet=show, show=show, kind='inverted')
        return out
    ch = _s(channel)   # a host-named talk show ("John McGinness" on News 93.1 KFBK): the station is the outlet
    if ch and _s(medium) in ('Podcast', 'Radio') and is_station(ch) and not is_station(o) and ch.lower() not in o.lower():
        out.update(outlet=ch, show=o, kind='station')
    return out


# ---------------- broadcast headlines ----------------
def is_rundown(h):
    """an episode rundown: several segment titles joined with ';' (NewsBank puts the whole show's headline list in the title), or one string
    far longer than any segment title"""
    h = _s(h)
    parts = [p for p in re.split(r'\s*;\s+', h) if p]
    return len(parts) >= 3 or (len(parts) >= 2 and len(h) > 160) or len(h) > 260


def _first_sentence(t, n=150):
    t = _s(t)
    m = re.match(r'^(.{20,%d}?[.!?])(?:\s|$)' % n, t)
    s = m.group(1) if m else t[:n].rsplit(' ', 1)[0]
    return s.rstrip('.!? ')


def segment_headline(show, text, hit_re=r'(?i)gabriel'):
    """'<Show>: <topic>' from the transcript: the host's lead-in (the paragraph before the one that first names him, else that paragraph's
    first sentence). Best effort; the caller flags the result for a human look. '' when there is no text or no mention."""
    t = text or ''
    m = re.search(hit_re, t)
    if not m or not show:
        return ''
    paras = [p.strip() for p in re.split(r'\n\s*\n', t) if p.strip()]
    pos = 0
    hit = None
    for i, p in enumerate(paras):
        j = t.find(p, pos)
        pos = j + len(p) if j >= 0 else pos
        if j >= 0 and j + len(p) > m.start():
            hit = i
            break
    if hit is None:
        return ''
    cand = []
    for i in (hit - 1, hit):
        if i >= 0:
            p = re.sub(r'^\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s*', '', paras[i])
            p = re.sub(r'^[A-Z][A-Z .\'-]{2,40}(?:,[^:]{0,60})?:\s*', '', p)   # speaker label
            if not re.match(r'^\((?:BEGIN|END|COMMERCIAL)', p):
                cand.append(p)
    for p in cand:
        s = _first_sentence(p)
        if len(s) >= 25:
            return f'{show}: {s}'
    return ''
