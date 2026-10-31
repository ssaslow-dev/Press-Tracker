"""lookup_cache.py - LEARN-v1 (Sammy 2026-10-30: "learn from the results so you don't have to use the internet in the future").

Reference-data-first rule for every web lookup (agents, sheet_task.py, the Update page):
  1. check the reference data (outlets.json, reporters.json, reporter_employment.csv, outlet_rules.json) and THIS cache;
  2. go to the web only for something genuinely new;
  3. save every confirmed answer back (add() / sheet_task --lookup-cache-out / the run doc's `lookups`).

code/lookup_cache.json shape (all keys optional except version):
  urls          {normalized url: {settled, verdict, checked, source, fields?}}   what a URL settled
  blocked_hosts {host: {why, checked, source}}                                   hosts that block bots / want a login (never worked around)
  archive       {dead url: {archive_url, status, checked, source}}               dead link -> archive replacement
  never_coverage_hosts {host: {why, checked, source}}                            NOBLOGS-v1: YouTube, advocacy blogs: never coverage (page pre-filter + sheet drop_skipped)
  searches      {key: {settled, verdict, checked, source}}                       a search that found nothing (e.g. "origin:10634 publisher link") so it is not repeated
verdict: confirmed | dead | blocked | not_found | unconfirmed.  Only confirmed / dead / blocked / not_found stop a fetch;
unconfirmed (medium/low confidence finds) is kept for the record and never counts as settled.
"""
import json, os, re, datetime
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(HERE, 'lookup_cache.json')
SETTLED = {'confirmed', 'dead', 'blocked', 'not_found'}
VERDICTS = SETTLED | {'unconfirmed'}
MAX_AGE_DAYS = {'confirmed': 3650, 'dead': 3650, 'blocked': 365, 'not_found': 180}   # a not-found answer is rechecked after ~6 months


def norm_url(u):
    """Cache key: lower-case host without www, no scheme, no fragment, no trailing slash, utm_* stripped."""
    u = str(u or '').strip()
    if not u:
        return ''
    if '://' not in u:
        u = 'https://' + u
    p = urlsplit(u)
    host = re.sub(r'^www\.', '', p.netloc.lower())
    q = '&'.join(x for x in p.query.split('&') if x and not x.lower().startswith(('utm_', 'fbclid', 'gclid')))
    return host + (p.path.rstrip('/') or '') + (('?' + q) if q else '')


def host_of(u):
    s = norm_url(u)
    return s.split('/')[0].split('?')[0] if s else ''


def _days(a, b):
    try:
        return (datetime.date.fromisoformat(b[:10]) - datetime.date.fromisoformat(a[:10])).days
    except Exception:
        return 0


class Cache:
    def __init__(self, data=None):
        d = data or {}
        self.version = d.get('version', 1)
        self.note = d.get('note', '')
        self.urls = dict(d.get('urls') or {})
        self.blocked_hosts = dict(d.get('blocked_hosts') or {})
        self.archive = dict(d.get('archive') or {})
        self.searches = dict(d.get('searches') or {})
        self.never_coverage_hosts = dict(d.get('never_coverage_hosts') or {})   # NOBLOGS-v1
        self.added = []   # entries added in this process (the run reports them)

    @classmethod
    def load(cls, path=None):
        path = path or DEFAULT_PATH
        try:
            return cls(json.load(open(path, encoding='utf-8')))
        except (OSError, ValueError):
            return cls()

    def to_dict(self):
        return {'version': self.version, 'note': self.note, 'urls': dict(sorted(self.urls.items())),
                'blocked_hosts': dict(sorted(self.blocked_hosts.items())), 'archive': dict(sorted(self.archive.items())), 'searches': dict(sorted(self.searches.items())),
                'never_coverage_hosts': dict(sorted(self.never_coverage_hosts.items()))}

    def save(self, path=None):
        path = path or DEFAULT_PATH
        tmp = path + '.tmp'
        json.dump(self.to_dict(), open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=False)
        os.replace(tmp, path)
        return path

    # ---------- reads ----------
    def get(self, url):
        return self.urls.get(norm_url(url))

    def blocked_host(self, url):
        h = host_of(url)
        while h:
            if h in self.blocked_hosts:
                return self.blocked_hosts[h]
            h = h.split('.', 1)[1] if '.' in h else ''
        return None

    def never_coverage(self, url):
        """NOBLOGS-v1: the entry when the URL's host (or a parent host) is on the never-coverage list, else None"""
        h = host_of(url)
        while h:
            if h in self.never_coverage_hosts:
                return self.never_coverage_hosts[h]
            h = h.split('.', 1)[1] if '.' in h else ''
        return None

    def add_never_coverage(self, host, why, source, checked=None):
        h = host_of(host) or str(host).lower()
        e = {'why': why, 'checked': checked or datetime.date.today().isoformat(), 'source': source}
        if self.never_coverage_hosts.get(h) != e:
            self.never_coverage_hosts[h] = e
            self.added.append(('never:' + h, e))

    def archive_for(self, url):
        a = self.archive.get(norm_url(url))
        return a['archive_url'] if a else ''

    def is_settled(self, url, today=None):
        """True when the cache already answers this URL (so no web fetch is needed)."""
        e = self.get(url)
        if not e or e.get('verdict') not in SETTLED:
            return False
        if today:
            return _days(e.get('checked', today), today) <= MAX_AGE_DAYS.get(e['verdict'], 365)
        return True

    def needs_fetch(self, url, today=None):
        """False when the URL is cached as settled, its host is a known blocked host, or it is dead with an archive copy."""
        if not norm_url(url):
            return False
        if self.blocked_host(url) or self.is_settled(url, today) or self.archive_for(url):
            return False
        return True

    def partition(self, urls, today=None):
        """-> (to_fetch, answered) ; answered = {url: reason}"""
        go, done = [], {}
        for u in urls:
            if self.blocked_host(u):
                done[u] = 'blocked host ' + host_of(u)
            elif self.archive_for(u):
                done[u] = 'dead; archive ' + self.archive_for(u)
            elif self.is_settled(u, today):
                done[u] = 'cached ' + self.get(u)['verdict']
            else:
                go.append(u)
        return go, done

    # ---------- writes ----------
    def add(self, url, settled, verdict, source, checked=None, **fields):
        if verdict not in VERDICTS:
            raise ValueError('verdict must be one of %s' % sorted(VERDICTS))
        k = norm_url(url)
        if not k:
            return None
        e = {'settled': settled, 'verdict': verdict, 'checked': checked or datetime.date.today().isoformat(), 'source': source}
        if fields:
            e['fields'] = fields
        old = self.urls.get(k)
        if old and old.get('verdict') in SETTLED and verdict == 'unconfirmed':
            return old   # never downgrade a settled answer to an unconfirmed one
        if old != e:
            self.urls[k] = e
            self.added.append((k, e))
        return e

    def add_blocked_host(self, host, why, source, checked=None):
        h = host_of(host) or str(host).lower()
        e = {'why': why, 'checked': checked or datetime.date.today().isoformat(), 'source': source}
        if self.blocked_hosts.get(h) != e:
            self.blocked_hosts[h] = e
            self.added.append(('host:' + h, e))

    def get_search(self, key):
        return self.searches.get(key)

    def add_search(self, key, settled, verdict, source, checked=None):
        if verdict not in VERDICTS:
            raise ValueError('verdict must be one of %s' % sorted(VERDICTS))
        e = {'settled': settled, 'verdict': verdict, 'checked': checked or datetime.date.today().isoformat(), 'source': source}
        if self.searches.get(key) != e:
            self.searches[key] = e
            self.added.append(('search:' + key, e))
        return e

    def add_archive(self, dead_url, archive_url, status, source, checked=None):
        k = norm_url(dead_url)
        e = {'archive_url': archive_url, 'status': status, 'checked': checked or datetime.date.today().isoformat(), 'source': source}
        if self.archive.get(k) != e:
            self.archive[k] = e
            self.added.append(('archive:' + k, e))

    def merge_lookups(self, items, today=None):
        """Run-doc / agent lookups: [{url, settled, verdict, source, checked?, kind?, archive_url?}] -> number added.
        A blocked verdict also records the host; a dead one with archive_url records the replacement."""
        n0 = len(self.added)
        for it in items or []:
            if not isinstance(it, dict) or not it.get('url') or it.get('verdict') not in VERDICTS:
                continue
            chk = str(it.get('checked') or today or datetime.date.today().isoformat())[:10]
            src = str(it.get('source') or 'run')[:300]
            self.add(it['url'], str(it.get('settled') or '')[:300], it['verdict'], src, chk)
            if it['verdict'] == 'blocked' and it.get('host_wide'):
                self.add_blocked_host(it['url'], str(it.get('settled') or '')[:200], src, chk)
            if it['verdict'] == 'dead' and it.get('archive_url'):
                self.add_archive(it['url'], str(it['archive_url']), str(it.get('settled') or '')[:120], src, chk)
        return len(self.added) - n0


_CACHE = None


def shared(path=None, reload=False):
    global _CACHE
    if _CACHE is None or reload:
        _CACHE = Cache.load(path)
    return _CACHE


def needs_fetch(url, today=None):
    """Module-level convenience: ask the shared cache before any web fetch."""
    return shared().needs_fetch(url, today)
