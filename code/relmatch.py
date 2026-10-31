"""relmatch.py - RELRELATED-v1 (agent-relrelated, 2026-10-28; Sammy comment eb3d0330: "most of these 'related stories' are not
related to this press release").

Decides which tracker stories are RELATED to an official press release, from evidence only. A story is related when one of:

  text      the story reuses the release text: it shares >= 25-word runs of identical words (reprint_rule tokens) with the
            release, >= 25 words in all, dated 1 day before to 90 days after the release (the reprint rule's run length and
            its 90-day text window, DECISIONS 72/158). Runs that occur in 3 or more releases (boilerplate: bios, standing
            quotes, program descriptions) do not count.
  quote     a shorter quotation: >= 12-word runs of the release totalling >= 20 words (same boilerplate filter), dated 1 day
            before to 30 days after, and the story carries one of the release's bills or its text matches the release's
            topic (see COS_MIN).
  bill      the story carries one of the release's bills AND is dated 1 day before to 7 days after the release AND its text
            is on the release's topic: tf-idf cosine of the story text vs the release text >= COS_MIN (0.14), or of the
            headline vs the release text >= HCOS_MIN (0.10).
  topic     no shared bill needed: dated 1 day before to 7 days after, English text with tf-idf cosine vs the release
            text >= TOPIC_COS (0.25) (catches untagged or mis-tagged stories on the same announcement: a grant, a
            highway naming, a caucus statement; 2026-10-28 probe: ~41 of 43 such pairs related).
Second tier, shown apart as "Possibly related":
  possible  same bill and same window as `bill`, but the topic cannot be checked: the story is not in English (the cosine
            is English-only) or has no saved text and its headline does not reach HCOS_MIN.
  pre       RELRELATED-v2 (Sammy, 2026-10-28, pr00244 / s01827): the story covered the SAME announcement before the release
            went out, dated 14 to 1 days before it (PRE_WIN) and not already related by the types above. One of:
              anchor  a specific subject of the release (a proper-name pair from its title that the release body also uses
                      as a name, e.g. "Sepulveda Basin"; release-rare) appears in the story's headline or text, and in the
                      same passage (the headline, or 80 words either side) the release's key dollar figure ("$22 million")
                      or a named partner of the release (another release-rare proper-name pair from its body, e.g.
                      "Karen Bass") or one of the release's bills;
              text    the story already carries >= 25-word runs of the release text (the release text was out before
                      the release was posted);
              subject a release with no bills: English story text with tf-idf cosine >= PRE_TOPIC_COS against the
                      release text, and the headline on the subject too (headline cosine >= HCOS_MIN).
            Anchors also need a minimal topic match (text cosine >= TEXT_COS_FLOOR or headline cosine >= HCOS_MIN).
            Generic same-bill coverage that precedes a release is excluded: when the story shares one of the release's
            bills, its headline must report the release's own milestone (signed / passed / took effect / introduced /
            vetoed, as the release title states it) and not anticipate it ("could", "would", "awaits", "?" ...), and no
            other release on that bill may fall between the story and this release; a story whose text is explained
            by an EARLIER release (as many 25-word-run words, or a 20-word quotation, of a release dated on or before
            the story) is that release's coverage, not this one's.
RELRELATED-v3 (rp-match, 2026-10-28, Sammy approved RELPLAN):
  - Non-English stories are scored on their English translation (data.json text_en / hl_en) wherever the topic check
    reads a cosine (bill on-topic test, topic, text/quote floors), so most "possible" pairs become `bill`.
  - A release bill NAMED in the story text (or headline, or translation) counts as a shared bill, like the Bills tag.
  - nearcopy  a `text` pair where >= NEAR_SHARE (60%) of the story's words lie in runs of the release: the story runs the
              release (edited/condensed). Tier 1, replaces `text` for that pair; a story is a nearcopy of one release
              only (the one it shares most text with).
  - anchor    0 to +7 days after (ANCHOR_WIN), no other evidence for the pair: the v2 anchor test (a release-rare name from
              the title + the key dollar figure / a named partner / a release bill in the same passage; text cosine >=
              ANCHOR_COS or headline cosine >= HCOS_MIN) or a headline test (ANCHOR_HL_MIN release-rare title words in the
              story headline, plus a minimal topic match or no saved text).
  Tier 3 "Later coverage" (shown apart; only for stories with NO tier-1/2 link to any release; one release per kind):
  - later       same bill AND session (a Gabriel bill of the release's session per gabriel_bills_leginfo.json), dated 8 to
                30 days after (LATER_WIN) and before the next release on that bill, on topic (cosine >= LATER_COS), and
                leading with it (a shared bill number or Gabriel's name in the headline or first LATER_LEAD words). The
                story goes to the latest such release.
  - laterquote  dated more than 7 days after the release (no upper limit), carries a quotation of it (>= 20 words of 12-word
                runs, or >= 25 words of 25-word runs) with at least one contiguous run >= LQ_LONG words that is not a bio or
                title formula, and text cosine >= LQ_COS. The story goes to the release it quotes most.
  AV: a transcript (av.tkind excerpts/full) with a contiguous >= LQ_LONG-word quotation of the release counts as `quote`
  (-1..+30) / `laterquote` without the topic floors (a broadcast covers many subjects); a same-bill same-week AV story
  whose saved text is a short station summary (<= AV_SHORT words) is `possible` (its cosine says nothing).
  The tier-3 choice is made per story against every release (resolve()), so the full run and the --update run agree.
RELRELATED-v4 (v23-rel-design, 2026-10-29):
  - bill       also when the story's headline reports the release's own milestone (the v2 `pre` headline test: signed / passed /
               introduced as the release title states it, nothing anticipatory) and text cosine >= MILE_COS (0.09), or no saved text: signing-day
               stories whose vocabulary differs from the release's ("Newsom signs California gun tax") were falling under COS_MIN.
  - superseded a tier-1 text / quote / bill row to release A is dropped when the story is ALSO tier-1 related to a later release B on
               a shared bill dated between A and the story, and the story reuses no more of A's text than of B's: the story reports
               B's milestone, and A's text reached it through B (releases on one bill repeat each other's bill description, which
               the <= MAX_DF boilerplate filter lets through when only two releases share it). nearcopy rows are kept.
  v23 integration (DECISIONS V23Q + v23 audit R2):
  - wave       `bill` (and `topic` for a release with bills) also +8..+30 days (WAVE_WIN) when no other release on the bill is dated
               between the release and the story and the bill is the release session's own (the `later` test, _later_ok; the
               lead test is NOT applied: on a 25-row read it dropped 7 right rows for 3 weak roundups): the
               introduction "coverage wave" weeks after the release is tier 1, not "Later coverage". The milestone path and
               `possible` stay same-week.
  - topic      the story must name Gabriel (INCL-v1), and must share a concrete anchor with the release (a shared bill, a
               release-rare proper name, or >= ANCHOR_HL_MIN release-rare title words in its headline: Sammy, "same subject links
               need a concrete anchor"); without one it is `subject` (tier 2, "possibly related").
  - roundup    a `text` row whose headline AND lead (headline + first LATER_LEAD words) are off the release's subject (cosine
               < ROUNDUP_HCOS, no shared bill or Gabriel in the lead) is tagged `roundup` ("Mentions it in a roundup"): a
               newsletter, briefing or column carrying a release paragraph. Still tier 1. (Headline cosine alone flagged 128 rows,
               ~40% right on a 20-row read; with the lead test 34, ~85%.)
Everything else (same bill months away, same issue +-30 days, roundups that only list the bill) is not related.

The release's own copies (sheet rows that pass the release text rule) are not stories and are never listed here; a tracker
story that IS the release (the release's Tracker release ID) is skipped.

Inputs are plain data so the same code serves the full build and the Update button:
  release_texts.json  {"v":1,"rel":{url:{date,title,dek,body,prid,...}}}  (pipeline file)
  releases            [{key, prid, date, url, title, bills:[...], sids:[...]}]  (ins-release_pickup rows)
  stories             [{id, date, prec, bills, lang, hl}]                 (data.json records)
  texts               {story id: (text, kind)}  kind 'html' | 'nb' as reprint_rule.html_text returns
Idf weights come from the release texts alone, so a run needs no corpus beyond release_texts.json.

Standard library + reprint_rule (tokeniser, html_text). No network, no writes except --out.
"""
import collections, datetime as dt, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.environ.get('RELMATCH_RR_DIR', ''), os.path.join(HERE, '..', '..', 'code'), HERE):
    if p and os.path.exists(os.path.join(p, 'reprint_rule.py')) and p not in sys.path:
        sys.path.insert(0, p)
        break
import reprint_rule as RR

VERSION = 'RELRELATED-v4'
RUN = 25                 # reprint_rule run length
QRUN, QMIN = 12, 20      # quote evidence: 12-word runs, >= 20 words in all
MAX_DF = 2               # a run counts only if it occurs in <= 2 releases
TEXT_WIN = (-1, 90)
QUOTE_WIN = (-1, 30)
BILL_WIN = (-1, 7)
COS_MIN = 0.14
HCOS_MIN = 0.10
TOPIC_COS = 0.25        # `topic` evidence: same week, no shared bill needed, strong text match
TEXT_COS_FLOOR = 0.10   # text/quote evidence also needs a shared bill or a minimal topic match (drops multi-bill roundups
                        # that carry one paragraph of the release, e.g. a Glock-signing roundup vs the AB 1264 release)
PRE_WIN = (-14, -1)     # RELRELATED-v2 `pre`: coverage of the same announcement before the release (Sammy: "up to about 14 days")
PRE_TOPIC_COS = 0.30    # `pre` subject path (releases with no bills)
ANCHOR_DF = 6           # a proper-name pair counts as an anchor when it is in <= 6 releases ...
ANCHOR_WDF = 12         # ... and one of its two words is in <= 12 releases' proper names
ANCHOR_SPAN = 80        # a passage = the headline, or 80 words either side of an anchor in the story text
NEAR_SHARE = 0.60      # v3 `nearcopy`: share of the story's words inside 25-word runs of the release
ANCHOR_WIN = (0, 7)     # v3 `anchor` after the release (hand check: +8..+14 was mostly later bill coverage)
ANCHOR_COS = 0.15       # v3 `anchor` name paths: text cosine >= 0.15 or headline cosine >= HCOS_MIN (drops news roundups)
ANCHOR_HL_MIN = 2       # v3 `anchor` headline path: rare release-title words in the story headline
BILLTEXT_COS = 0.15     # v3: on-topic bar when the shared bill is only named in the story text (no Bills tag)
LATER_WIN = (8, 30)     # v3 `later`
LATER_COS = 0.14
LATER_LEAD = 90         # ... and the story leads with it: a shared bill number or Gabriel's name in the headline or first 90 words
LQ_MIN_LAG = 8          # v3 `laterquote`: more than 7 days after
LQ_LONG = 20            # ... with one contiguous quoted run of >= 20 words
AV_MEDIA = {'TV', 'Radio', 'Podcast', 'Video'}
AV_SHORT = 400          # v3: an AV story with <= 400 words of saved text (a station's web summary) cannot be topic-checked
LQ_COS = 0.125          # ... and text cosine >= 0.125 (hand check: below it, quotes of another member's bill description)
WAVE_WIN = (8, 30)      # v23 (audit R2): the coverage wave after a release, when no newer release on the bill lies between
ROUNDUP_HCOS = 0.05     # v23 (audit R9, V23Q): a `text` row whose headline and lead cosines are below this is a roundup mention
MILE_COS = 0.09         # v4 `bill` milestone path: same tagged bill, same week, the story HEADLINE reports the release's own milestone
                        # (signed / passed / introduced ... as the release title states it, not anticipating it) and text cosine >= 0.09
                        # (v23 back-test: 11 of 11 pairs at or above it were the same announcement; below it, multi-bill roundups)
TIER = {'text': 1, 'nearcopy': 1, 'quote': 1, 'bill': 1, 'topic': 1, 'pre': 1, 'anchor': 1, 'roundup': 1, 'possible': 2,
        'subject': 2, 'later': 3, 'laterquote': 3}
LABEL = {'text': 'Uses the release text', 'nearcopy': 'Runs the release (edited)', 'quote': 'Quotes the release',
         'bill': 'Same bill, same topic, in the coverage wave', 'topic': 'Same subject and a shared name or bill',
         'roundup': 'Mentions it in a roundup', 'subject': 'Similar subject, no shared name or bill (not checked)',
         'pre': 'Covered the announcement before the release', 'anchor': 'Same announcement (names and figures match)',
         'possible': 'Same bill, same week (topic not checked)',
         'later': 'Later coverage of the bill', 'laterquote': 'Later coverage quoting the release'}

STOP = set(RR.STOP) | set('he she they his her their we our you i me my mr ms has have had but more than also which who what '
                          'when where how all one two said says year years percent million people would will just like time '
                          'there been other its your them these those first last most some such only'.split())


def _day(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def lag_days(story, rel_date):
    """story date - release date in days; None unless the story is dated to the day"""
    if (story.get('prec') or 'day') != 'day':
        return None
    a, b = _day(story.get('date')), _day(rel_date)
    return (a - b).days if a and b else None


def content_words(toks):
    return [t for t in toks if len(t) > 2 and t not in STOP and not t.isdigit()]


# ---------------- RELRELATED-v2 `pre` helpers ----------------
NAME_TITLES = set('assemblymember assemblymembers assemblywoman assemblyman senator senators mayor governor councilmember '
                  'councilwoman councilman supervisor chair chairman chairwoman speaker president secretary director chief '
                  'commissioner attorney general dr rabbi pro tem assistant majority leader representative congressman '
                  'congresswoman lieutenant ceo executive founder vice the a an and of for in on to at by with today '
                  'yesterday this that these our we'.split())
NAME_SKIP = {'jesse', 'gabriel', 'california', 'sacramento', 'assembly', 'state', 'senate', 'legislature', 'bill', 'act', 'ab',
             'sb', 'governor', 'newsom', 'gavin', 'los', 'angeles', 'san', 'fernando', 'valley'}
_SENT = re.compile(r'(?<=[.!?:;"\u201c\u201d])\s+|\n')
_WORD = re.compile(r"[A-Za-z][A-Za-z\u2019'\-]*")


def name_pairs(text, skip_first=True):
    """adjacent pairs of capitalised words (proper names: "Sepulveda Basin", "Karen Bass"), as reprint_rule token pairs.
    skip_first drops each sentence's first word (capitalised anyway); titles ("Mayor", "Senator") break a name."""
    out = set()
    for sent in _SENT.split(text or ''):
        words = _WORD.findall(sent)
        run = []
        for i, w in enumerate(words + ['x']):
            if w[0].isupper() and w.lower() not in NAME_TITLES and not (skip_first and i == 0):
                run.append(w)
                continue
            t = RR.norm_tokens(' '.join(run)) if len(run) >= 2 else []
            for j in range(len(t) - 1):
                if len(t[j]) > 2 and len(t[j + 1]) > 2 and not (t[j] in NAME_SKIP and t[j + 1] in NAME_SKIP):
                    out.add((t[j], t[j + 1]))
            run = []
    return out


_FIG = re.compile(r'\$\s?(\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand|[mbk]\b)?', re.I)


def dollar_figures(text):
    """{value in dollars: count} for every "$22 million" / "$22M" / "$1,500,000" in text"""
    out = collections.Counter()
    for m in _FIG.finditer(text or ''):
        u = {'m': 'million', 'b': 'billion', 'k': 'thousand'}.get((m.group(2) or '').lower(), (m.group(2) or '').lower())
        try:
            v = float(m.group(1).replace(',', '').rstrip('.'))
        except ValueError:
            continue
        out[v * {'million': 1e6, 'billion': 1e9, 'thousand': 1e3}.get(u, 1)] += 1
    return out


def figure_token_seqs(v):
    """token sequences a story may use for the dollar value v ("22 million", "22m", "22,000,000")"""
    out = set()
    for u, m in (('billion', 1e9), ('million', 1e6), ('thousand', 1e3)):
        if v >= m:
            n = '%g' % (v / m)
            out.add(tuple(RR.norm_tokens(n + ' ' + u)))
            out.add(tuple(RR.norm_tokens(n + u[0])))
            break
    if v >= 1000:
        out.add(tuple(RR.norm_tokens('{:,}'.format(int(v)))))
        out.add(tuple(RR.norm_tokens('%d' % v)))
    return {t for t in out if t}


MILESTONE = {'sign': {'signs', 'signed', 'signing', 'enacts', 'enacted'},
             'veto': {'veto', 'vetoes', 'vetoed'},
             'pass': {'passes', 'passed', 'approves', 'approved', 'clears', 'cleared', 'advances', 'advanced'},
             'effect': {'effect', 'effective'},
             'intro': {'introduces', 'introduced', 'unveils', 'unveiled', 'proposes'}}
ANTICIPATE = {'could', 'would', 'will', 'may', 'might', 'awaits', 'await', 'awaiting', 'decide', 'decision', 'wants', 'want',
              'urges', 'urge', 'proposal', 'proposed', 'proposes', 'should', 'soon', 'ahead', 'pending', 'seeks', 'plan',
              'plans', 'what', 'which', 'whether', 'about'}


def milestones(toks):
    s = set(toks)
    return {k for k, v in MILESTONE.items() if s & v}


def _has_seq(toks, seq):
    n = len(seq)
    if not n or not toks:
        return False
    f = seq[0]
    return any(toks[i] == f and tuple(toks[i:i + n]) == seq for i in range(len(toks) - n + 1))


def _bill_seqs(bills):
    return {tuple(RR.norm_tokens(b)) for b in bills}


# ---------------- RELRELATED-v3 helpers ----------------
BILL_PFX = {'ab': 'AB', 'sb': 'SB', 'aca': 'ACA', 'acr': 'ACR', 'ajr': 'AJR', 'sca': 'SCA', 'scr': 'SCR', 'sjr': 'SJR'}
_GLUED = re.compile(r'^(ab|sb|aca|acr|ajr|sca|scr|sjr)(\d{1,4})$')


def bills_in_tokens(toks):
    """bill numbers a text names ("AB 1264", "AB1264", "A.B. 1264", "Assembly Bill 1264", "Senate Bill No. 2"), as tab labels"""
    out = set()
    n = len(toks or [])
    num = lambda j: str(int(toks[j])) if j < n and toks[j].isdigit() and len(toks[j]) <= 4 and int(toks[j]) else None
    for i, t in enumerate(toks or []):
        p = j = None
        if t in BILL_PFX:
            p, j = BILL_PFX[t], i + 1
        elif t == 'a' and i + 1 < n and toks[i + 1] == 'b':
            p, j = 'AB', i + 2
        elif t in ('assembly', 'senate') and i + 1 < n and toks[i + 1] == 'bill':
            p, j = ('AB' if t == 'assembly' else 'SB'), i + 2
        else:
            m = _GLUED.match(t)
            if m and int(m.group(2)):
                out.add('%s %d' % (BILL_PFX[m.group(1)], int(m.group(2))))
            continue
        if j < n and toks[j] == 'no':
            j += 1
        v = num(j)
        if v:
            out.add('%s %s' % (p, v))
    return out


def session_of(d):
    """first year of the two-year California session a date falls in (December of an even year opens the next one)"""
    d = _day(d) if not isinstance(d, dt.date) else d
    if not d:
        return None
    if d.year % 2:
        return d.year
    return d.year + 1 if d.month == 12 else d.year - 1


def own_bill_sessions(leginfo):
    """gabriel_bills_leginfo.json -> {bill: {session start year}}"""
    out = collections.defaultdict(set)
    for g in (leginfo or {}).get('rows', []):
        try:
            out[g['bill']].add(int(str(g['session'])[:4]))
        except (KeyError, ValueError):
            pass
    return dict(out)


HL_STOP = STOP | NAME_TITLES | NAME_SKIP | set('announce announces announced passes passed signs signed new law laws bill bills '
                                                 'statement caucus jewish legislative california calif assemblymember gabriel '
                                                 'jesse million billion funding state'.split())


class Index:
    def __init__(self, release_texts, releases, own_bills=None):
        """own_bills: {bill: {session start year}} from gabriel_bills_leginfo.json (v3 `later`); None = every release bill
        counts as the release session's own bill"""
        self.own_bills = own_bills
        self.rel = {}
        df = collections.Counter()
        for r in releases:
            x = release_texts.get(r.get('url') or '') or {}
            full = '\n'.join(v for v in (x.get('title') or r.get('title') or '', x.get('dek') or '', x.get('body') or '') if v)
            toks = RR.version(full, 'html', 'rel')['raw']
            self.rel[r['key']] = {'r': r, 'toks': toks, 'cw': content_words(toks), 'has_body': bool(x.get('body'))}
            df.update(set(self.rel[r['key']]['cw']))
        self._pre_anchors(release_texts)
        self.all_rel = self.rel   # the incremental (--update) run narrows .rel; the `pre` earlier-release check uses all
        self.N = max(1, len(self.rel))
        self.idf = {t: math.log((self.N + 1) / (n + 0.5)) for t, n in df.items()}
        self.idf_unseen = math.log((self.N + 1) / 0.5)
        self.g25, self.g12 = collections.defaultdict(set), collections.defaultdict(set)
        for k, v in self.rel.items():
            t = v['toks']
            for i in range(len(t) - RUN + 1):
                self.g25[tuple(t[i:i + RUN])].add(k)
            for i in range(len(t) - QRUN + 1):
                self.g12[tuple(t[i:i + QRUN])].add(k)
            v['vec'] = self.vec(v['cw'])
        # v3: release dates, releases per bill (date order), rare title words for the `anchor` headline path
        self.rdate = {k: _day(v['r'].get('date')) for k, v in self.rel.items()}
        self.bybill = collections.defaultdict(list)
        for k, v in self.rel.items():
            for b in v['r'].get('bills') or []:
                if self.rdate[k]:
                    self.bybill[b].append((self.rdate[k], k))
        for b in self.bybill:
            self.bybill[b].sort()
        twdf = collections.Counter()
        tw = {}
        for k, v in self.rel.items():
            x = release_texts.get(v['r'].get('url') or '') or {}
            tw[k] = {t for t in RR.norm_tokens(x.get('title') or v['r'].get('title') or '')
                     if len(t) > 2 and t not in HL_STOP and not t.isdigit()}
            twdf.update(tw[k])
        for k in self.rel:
            self.rel[k]['tw'] = {t for t in tw[k] if twdf[t] <= 2}

    def _pre_anchors(self, release_texts):
        """RELRELATED-v2: per release, its subject pairs (title names the body also uses as names), its partners (other
        release-rare names in the body), its key dollar figures and the milestone its title states"""
        pdf, wdf, raw = collections.Counter(), collections.Counter(), {}
        for k, v in self.rel.items():
            r = v['r']
            x = release_texts.get(r.get('url') or '') or {}
            title = x.get('title') or r.get('title') or ''
            body = '\n'.join(t for t in (x.get('dek') or '', x.get('body') or '') if t)
            tp, bp = name_pairs(title, skip_first=False), name_pairs(body)
            raw[k] = (title, body, tp, bp)
            pdf.update(tp | bp)
            wdf.update({w for p in tp | bp for w in p})
        for k, (title, body, tp, bp) in raw.items():
            # a name: rare across releases, and never written in lower case in this release ("climate change" is not a name)
            rare = lambda p: pdf[p] <= ANCHOR_DF and min(wdf[w] for w in p) <= ANCHOR_WDF and \
                not re.search(r'\b%s\s+%s\b' % (re.escape(p[0]), re.escape(p[1])), title + '\n' + body)
            subj = {p for p in tp if rare(p) and (p in bp or not body)}
            part = {p for p in bp if rare(p)} - subj
            figs = dollar_figures(title)
            if not figs:
                figs = {f: n for f, n in dollar_figures(body).items() if n >= 2}
            fseq = set()
            for f in figs:
                if f >= 1000:
                    fseq |= figure_token_seqs(f)
            self.rel[k]['pre'] = {'subj': subj, 'part': part, 'fig': fseq, 'mile': milestones(RR.norm_tokens(title)),
                                  'bills': _bill_seqs(self.rel[k]['r'].get('bills') or [])}

    def vec(self, cw):
        c = collections.Counter(cw)
        v = {t: (1 + math.log(n)) * self.idf.get(t, self.idf_unseen) for t, n in c.items()}
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / nrm for t, x in v.items()}

    @staticmethod
    def cos(a, b):
        if len(a) > len(b):
            a, b = b, a
        return sum(x * b.get(t, 0.0) for t, x in a.items())

    def runs(self, toks, key, k, idx):
        """(words of the story inside k-word runs of release `key` that occur in <= MAX_DF releases, longest such run)"""
        n = len(toks)
        cov = bytearray(n)
        for i in range(n - k + 1):
            s = idx.get(tuple(toks[i:i + k]))
            if s and key in s and len(s) <= MAX_DF:
                cov[i:i + k] = b'\x01' * k
        best = cur = 0
        for c in cov:
            cur = cur + 1 if c else 0
            best = max(best, cur)
        return sum(cov), best

    def candidates(self, toks):
        """release keys sharing at least one 12-word run with the story"""
        out = set()
        for i in range(len(toks) - QRUN + 1):
            s = self.g12.get(tuple(toks[i:i + QRUN]))
            if s:
                out |= s
        return out


def story_tokens(text, kind='html'):
    return RR.version(text or '', kind, 'story')['strip'] if text else None


def story_ctx(ix, story, toks=None, story_vec=None, cands=None):
    """per-story inputs of evidence(), computed once per story: tokens, vector, run candidates, the English translation's
    vectors (v3) and the bills the text names (v3)"""
    c = {'toks': toks, 'sv': story_vec, 'cands': cands}
    if toks and story_vec is None:
        c['sv'] = ix.vec(content_words(toks))
    c['hv'] = ix.vec(content_words(RR.norm_tokens(story.get('hl') or '')))
    c['ev'] = c['hev'] = None
    if (story.get('lang') or '').strip():
        te, he = story.get('text_en') or '', story.get('hl_en') or ''
        if te.strip():
            c['ev'] = ix.vec(content_words(RR.norm_tokens(te)))
        if he.strip():
            c['hev'] = ix.vec(content_words(RR.norm_tokens(he)))
    named = bills_in_tokens(toks or [])
    for f in ('hl', 'hl_en', 'text_en'):
        if story.get(f):
            named |= bills_in_tokens(RR.norm_tokens(story[f]))
    c['named'] = named
    lead = RR.norm_tokens(story.get('text_en') or '') if (story.get('lang') or '').strip() and story.get('text_en') else (toks or [])
    c['lead'] = RR.norm_tokens(story.get('hl_en') or story.get('hl') or '') + RR.norm_tokens(story.get('hl') or '') + list(lead[:LATER_LEAD])
    return c


def evidence(ix, key, story, toks=None, story_vec=None, cands=None, ctx=None):
    """-> {'type', 'tier', 'lag', 'bills', 'bills_text', 'run_words', 'longest_run', 'quote_words', 'longest_quote', 'share',
    'cos', 'hcos', 'cos_en', 'hcos_en'} or None. Tier-3 types (later, laterquote) are CANDIDATES: resolve() keeps them only
    for stories with no tier-1/2 link."""
    R = ix.rel[key]
    r = R['r']
    if story['id'] in (r.get('sids') or []):
        return None
    if ctx is None:
        ctx = story_ctx(ix, story, toks, story_vec, cands)
    toks, cands = ctx['toks'], ctx['cands']
    lag = lag_days(story, r.get('date'))
    rb = set(r.get('bills') or [])
    tagged = rb & set(story.get('bills') or [])
    bills = sorted(tagged | (rb & ctx['named']))
    e = {'lag': lag, 'bills': bills, 'bills_text': sorted(set(bills) - tagged), 'run_words': 0, 'longest_run': 0,
         'quote_words': 0, 'longest_quote': 0, 'share': 0.0, 'cos': None, 'hcos': None, 'cos_en': None, 'hcos_en': None}
    if toks and (cands is None or key in cands):
        e['run_words'], e['longest_run'] = ix.runs(toks, key, RUN, ix.g25)
        e['quote_words'], e['longest_quote'] = ix.runs(toks, key, QRUN, ix.g12)
        e['share'] = round(e['run_words'] / len(toks), 3)
    if toks:
        e['cos'] = round(ix.cos(R['vec'], ctx['sv']), 3)
    e['hcos'] = round(ix.cos(R['vec'], ctx['hv']), 3)
    english = not (story.get('lang') or '').strip()
    if not english:   # v3: score the English translation
        if ctx['ev'] is not None:
            e['cos_en'] = round(ix.cos(R['vec'], ctx['ev']), 3)
        if ctx['hev'] is not None:
            e['hcos_en'] = round(ix.cos(R['vec'], ctx['hev']), 3)
    c1, h1 = (e['cos'], e['hcos']) if english else (e['cos_en'], e['hcos_en'])
    scorable = english or c1 is not None or h1 is not None
    inw = lambda w: lag is not None and w[0] <= lag <= w[1]
    av = story.get('media') in AV_MEDIA
    transcript = av and ((story.get('av') or {}).get('tkind') in ('excerpts', 'full'))
    on_topic = scorable and ((c1 or 0) >= COS_MIN or (h1 or 0) >= HCOS_MIN)
    if bills and not tagged:   # v3: a bill only NAMED in the text needs the text itself on the release's subject
        on_topic = (c1 or 0) >= BILLTEXT_COS
    t = None
    topical = bool(bills) or max(e['cos'] or 0, c1 or 0) >= TEXT_COS_FLOOR or max(e['hcos'], h1 or 0) >= HCOS_MIN
    if e['run_words'] >= RUN and topical and (inw(TEXT_WIN) or (lag is None and _month_in_window(story, r.get('date'), TEXT_WIN))):
        t = 'nearcopy' if e['share'] >= NEAR_SHARE else 'text'
    elif e['quote_words'] >= QMIN and inw(QUOTE_WIN) and (bills or max(e['cos'] or 0, c1 or 0) >= COS_MIN
                                                           or (transcript and e['longest_quote'] >= LQ_LONG)):
        t = 'quote'
    elif bills and (inw(BILL_WIN) or (inw(WAVE_WIN) and _later_ok(ix, key, story, bills))):   # v23 wave
        week = inw(BILL_WIN)
        if on_topic or (week and tagged and ((scorable and (c1 or 0) >= MILE_COS) or not toks) and _milestone_headline(ix, key, story)):   # v4
            t = 'bill'
        elif week and (not english or e['cos'] is None or (av and len(toks) <= AV_SHORT)):
            t = 'possible'
    if not t and (c1 or 0) >= TOPIC_COS and R['has_body'] and (inw(BILL_WIN) or (
            inw(WAVE_WIN) and r.get('bills') and _later_ok(ix, key, story, sorted(rb)))) and _names_gabriel(story, toks):   # v23
        t = 'topic' if _topic_anchor(ix, key, story, toks, e) else 'subject'
    if (not t or t == 'possible') and inw(PRE_WIN):
        p = pre_evidence(ix, key, story, toks, e, cands)
        if p:
            t = 'pre'
            e['pre'] = p
    if (not t or t == 'possible') and inw(ANCHOR_WIN):
        p = post_anchor(ix, key, story, toks, e, cands)
        if p:
            t = 'anchor'
            e['anchor'] = p
    if not t and inw(LATER_WIN) and bills and (c1 or 0) >= LATER_COS and _leads_with(ctx, bills) \
            and _later_ok(ix, key, story, bills):
        t = 'later'
    if not t and lag is not None and lag >= LQ_MIN_LAG and (e['quote_words'] >= QMIN or e['run_words'] >= RUN) \
            and e['longest_quote'] >= LQ_LONG and (transcript or max(e['cos'] or 0, e['cos_en'] or 0) >= LQ_COS) \
            and not _formula_only(ix, key, toks):
        t = 'laterquote'
    if not t:
        return None
    if t == 'text' and max(e['hcos'], e['hcos_en'] or 0) < ROUNDUP_HCOS and not _leads_with(ctx, bills):   # v23 roundup tag
        if ctx.get('lv') is None:
            ctx['lv'] = ix.vec(content_words(ctx['lead']))
        if ix.cos(R['vec'], ctx['lv']) < ROUNDUP_HCOS:
            t = 'roundup'
    e['type'], e['tier'] = t, TIER[t]
    return e


GAB_RE = re.compile(r'gabriel|개브리엘|가브리엘|加布里爾|加布里尔|ガブリエル|габриэл|габриел', re.I)


def _names_gabriel(story, toks):
    """v23 `topic`: the story names Gabriel (INCL-v1: case-insensitive, also in the English translation and his KO/ZH/JA/RU
    spellings); a story with no saved text and no translation is given the benefit (its sheet row was included on his name)"""
    if toks and 'gabriel' in toks:
        return True
    blob = ' '.join(str(story.get(f) or '') for f in ('hl', 'hl_en', 'text_en', 'text'))
    if GAB_RE.search(blob):
        return True
    return not toks and not (story.get('text_en') or '').strip()


def _topic_anchor(ix, key, story, toks, e):
    """v23 `topic` anchor test (V23Q): a shared bill, a release-rare proper name (subject or partner pair) in the story, or
    >= ANCHOR_HL_MIN release-rare title words in its headline"""
    if e['bills']:
        return True
    R = ix.rel[key]
    A = R['pre']
    htoks = RR.norm_tokens(story.get('hl_en') or story.get('hl') or '')
    if len(R['tw'] & set(htoks)) >= ANCHOR_HL_MIN:
        return True
    pool = list(htoks) + list(toks or []) + RR.norm_tokens(story.get('text_en') or '')
    names = A['subj'] | A['part']
    return bool(names and set(zip(pool, pool[1:])) & names)


def _milestone_headline(ix, key, story):
    """v4 `bill` milestone path: the headline proper (not its dek) states the release title's milestone and does not anticipate it
    (the RELRELATED-v2 `pre` headline test)"""
    A = ix.rel[key]['pre']
    main = re.split(r'\s+[-\u2013\u2014|]\s+', story.get('hl_en') or story.get('hl') or '')[0]
    mt = RR.norm_tokens(main)
    return bool(A['mile'] and milestones(mt) & A['mile']) and not (set(mt) & ANTICIPATE) and '?' not in main


def _superseded(ix, pairs):
    """v4: tier-1 text / quote / bill rows to a release A that a later tier-1 release B on a shared bill supersedes (B dated after A
    and on or before the story + 1 day; the story reuses no more 25-word-run text of A than of B). Returns the rows to drop."""
    prim = [p for p in pairs if p[1]['tier'] < 3]
    drop = []
    for pa in prim:
        ka, ea = pa
        if ea['type'] not in ('text', 'roundup', 'quote', 'bill') or ea['lag'] is None:
            continue
        da, ba = ix.rdate.get(ka), set(ix.rel[ka]['r'].get('bills') or [])
        if not da or not ba:
            continue
        for kb, eb in prim:
            if kb == ka or eb['lag'] is None or pa in drop:
                continue
            db = ix.rdate.get(kb)
            if not db or not (da < db) or eb['lag'] < -1 or not ba & set(ix.rel[kb]['r'].get('bills') or []):
                continue
            if ea['run_words'] <= eb['run_words'] and ea['quote_words'] <= max(eb['quote_words'], eb['run_words']):
                drop.append(pa)
                break
    return drop


def _leads_with(ctx, bills):
    """v3 `later`: the story is about the bill, not a roundup or spin-off that mentions it: one of the shared bills, or
    Gabriel's name, is in the headline or the first LATER_LEAD words (the English translation for a non-English story)"""
    lead = ctx['lead']
    return 'gabriel' in lead or bool(bills_in_tokens(lead) & set(bills))


def _later_ok(ix, key, story, bills):
    """v3 `later`: a shared bill is the release session's own bill, the story is in that session, and no other release on
    that bill is dated between the release and the story (+1 day)"""
    d0, d = ix.rdate[key], _day(story.get('date'))
    s0 = session_of(d0)
    if not d or s0 != session_of(d):
        return False
    for b in bills:
        if ix.own_bills is not None and s0 not in ix.own_bills.get(b, ()):
            continue
        if not any(k2 != key and d0 <= d2 <= d + dt.timedelta(days=1) and (d2, k2) > (d0, key)
                   for d2, k2 in ix.bybill.get(b, [])):
            return True
    return False


FORMULA = re.compile(r'\b(represents? the \w+ (assembly )?district|chairs? (of )?the (assembly )?\w+( \w+)? committee|'
                     r'chair of the|vice chair|member of the|serves? (as|on)|elected (to|in)|first elected|'
                     r'for more information|follow (him|us)|contact|previously served|served on the boards?|community activist|'
                     r'environmentalist|born and raised|graduate of)\b')


def _formula_only(ix, key, toks):
    """v3 `laterquote`: every contiguous quoted run (12-word runs of this release) of >= LQ_LONG words is a bio, title or
    contact formula ("represents the 46th Assembly District", "chair of the Assembly Budget Committee")"""
    if not toks:
        return True
    n = len(toks)
    cov = bytearray(n)
    for i in range(n - QRUN + 1):
        s = ix.g12.get(tuple(toks[i:i + QRUN]))
        if s and key in s and len(s) <= MAX_DF:
            cov[i:i + QRUN] = b'\x01' * QRUN
    i = 0
    while i < n:
        if not cov[i]:
            i += 1
            continue
        j = i
        while j < n and cov[j]:
            j += 1
        if j - i >= LQ_LONG and not FORMULA.search(' '.join(toks[i:j])):
            return False
        i = j
    return True


def post_anchor(ix, key, story, toks, e, cands=None):
    """v3 `anchor` (0..+7 days, no other evidence): 'name:<figure|partner|bill>' (the v2 passage test) or 'headline' (>=
    ANCHOR_HL_MIN release-rare title words in the story headline, plus a minimal topic match or no saved text). Excluded
    when another release on a shared bill falls between this release and the story, or the story's text is another
    release's (_explained_by_earlier)."""
    R = ix.rel[key]
    A = R['pre']
    d, d0 = _day(story.get('date')), ix.rdate[key]
    if e['bills'] and d and any(k2 != key and d0 < d2 <= d for b in e['bills'] for d2, k2 in ix.bybill.get(b, [])):
        return None
    if toks and _explained_by_earlier(ix, key, story, toks, cands):
        return None
    topical = (e['cos'] or 0) >= TEXT_COS_FLOOR or e['hcos'] >= HCOS_MIN or (e['cos_en'] or 0) >= TEXT_COS_FLOOR \
        or (e['hcos_en'] or 0) >= HCOS_MIN
    hl = story.get('hl_en') or story.get('hl') or ''
    htoks = RR.norm_tokens(hl)
    strong = max(e['cos'] or 0, e['cos_en'] or 0) >= ANCHOR_COS or max(e['hcos'], e['hcos_en'] or 0) >= HCOS_MIN
    if A['subj'] and strong:
        passages = [htoks]
        if toks:
            first = {p[0] for p in A['subj']}
            for i in range(len(toks) - 1):
                if toks[i] in first and (toks[i], toks[i + 1]) in A['subj']:
                    passages.append(toks[max(0, i - ANCHOR_SPAN):i + ANCHOR_SPAN + 2])
        for w in passages:
            subj = {p for p in A['subj'] if _has_seq(w, p)}
            if not subj:
                continue
            if any(_has_seq(w, f) for f in A['fig']):
                return 'name:figure'
            names = {q for q in A['subj'] | A['part'] if _has_seq(w, q)}
            if any(not (set(p) & set(q)) for p in subj for q in names):
                return 'name:partner'
            if e['bills'] and any(_has_seq(w, b) for b in A['bills']):
                return 'name:bill'
    shared = R['tw'] & set(htoks)
    if len(shared) >= ANCHOR_HL_MIN and (topical or not toks):
        return 'headline'
    return None


def resolve(pairs, ix=None):
    """per story: [(release key, evidence)] -> the rows kept. Tier 1/2 rows are all kept (v4: minus the rows a later release on the
    bill supersedes, _superseded, when ix is given); tier-3 candidates only when the story has no tier-1/2 row: `later` to the
    nearest release (smallest lag, then highest cosine), `laterquote` to the release it quotes most (then nearest); a `later`
    row on the same release as the `laterquote` row is dropped."""
    if ix is not None:
        gone = _superseded(ix, pairs)
        pairs = [p for p in pairs if p not in gone]
    prim = [p for p in pairs if p[1]['tier'] < 3]
    nc = [p for p in prim if p[1]['type'] == 'nearcopy']
    if len(nc) > 1:   # a story runs ONE release: the one it shares most text with; the others (quoted inside it) stay `text`
        best = min(nc, key=lambda p: (-p[1]['run_words'], p[1]['lag'] if p[1]['lag'] is not None else 999, p[0]))
        for p in nc:
            if p is not best:
                p[1]['type'] = 'text'
    if prim:
        return prim
    la = [p for p in pairs if p[1]['type'] == 'later']
    lq = [p for p in pairs if p[1]['type'] == 'laterquote']
    out = []
    if lq:
        out.append(min(lq, key=lambda p: (-p[1]['quote_words'], -p[1]['run_words'], p[1]['lag'], p[0])))
    if la:
        b = min(la, key=lambda p: (p[1]['lag'], -(p[1]['cos'] if p[1]['cos'] is not None else (p[1]['cos_en'] or 0)), p[0]))
        if not out or out[0][0] != b[0]:
            out.append(b)
    return out


def pre_evidence(ix, key, story, toks, e, cands=None):
    """RELRELATED-v2 `pre` (story dated PRE_WIN before the release): -> 'anchor:<what>' | 'text' | 'subject' | None"""
    R = ix.rel[key]
    A = R['pre']
    english = not (story.get('lang') or '').strip()
    htoks = RR.norm_tokens(story.get('hl') or '')
    if e['bills']:   # generic same-bill coverage: the headline must report the release's own milestone, not anticipate it
        main = re.split(r'\s+[-\u2013\u2014|]\s+', story.get('hl') or '')[0]   # the headline proper, not its dek
        mt = RR.norm_tokens(main)
        if not (A['mile'] and milestones(mt) & A['mile']) or set(mt) & ANTICIPATE or '?' in main:
            return None
    if e['bills'] and _nearer_bill_release(ix, key, story, e['bills']):
        return None
    if toks and _explained_by_earlier(ix, key, story, toks, cands):
        return None
    if e['run_words'] >= RUN:
        return 'text'
    if english and not (R['r'].get('bills') or []) and R['has_body'] and (e['cos'] or 0) >= PRE_TOPIC_COS \
            and e['hcos'] >= HCOS_MIN:
        return 'subject'
    if not A['subj'] or not ((e['cos'] or 0) >= TEXT_COS_FLOOR or e['hcos'] >= HCOS_MIN):   # anchors need a minimal topic match
        return None
    passages = [htoks]
    if toks:
        first = {p[0] for p in A['subj']}
        for i in range(len(toks) - 1):
            if toks[i] in first and (toks[i], toks[i + 1]) in A['subj']:
                passages.append(toks[max(0, i - ANCHOR_SPAN):i + ANCHOR_SPAN + 2])
    for w in passages:
        subj = {p for p in A['subj'] if _has_seq(w, p)}
        if not subj:
            continue
        if any(_has_seq(w, f) for f in A['fig']):
            return 'anchor:figure'
        names = {q for q in A['subj'] | A['part'] if _has_seq(w, q)}   # a second, separate name: a partner or co-subject
        if any(not (set(p) & set(q)) for p in subj for q in names):
            return 'anchor:partner'
        if e['bills'] and any(_has_seq(w, b) for b in A['bills']):
            return 'anchor:bill'
    return None


def _nearer_bill_release(ix, key, story, bills):
    """another release on one of these bills is dated between the story (-1 day) and this release: the story is that
    release's milestone, not this one's"""
    d, d0 = _day(story.get('date')), _day(ix.rel[key]['r'].get('date'))
    if not d or not d0:
        return False
    for k2, R2 in getattr(ix, 'all_rel', ix.rel).items():
        if k2 == key or not set(bills) & set(R2['r'].get('bills') or []):
            continue
        d2 = _day(R2['r'].get('date'))
        if d2 and d - dt.timedelta(days=1) <= d2 < d0:
            return True
    return False


def _explained_by_earlier(ix, key, story, toks, cands=None):
    """the story reuses text of ANOTHER release dated on or before the story at least as much as this one's (>= 25-word
    runs, or with no such runs of this release >= 20 words of 12-word runs): it is coverage of that earlier announcement"""
    d = _day(story.get('date'))
    if not d:
        return False
    rw0 = qw0 = None
    for k2 in (cands if cands is not None else ix.candidates(toks)):
        R2 = getattr(ix, 'all_rel', ix.rel).get(k2)
        if k2 == key or not R2:
            continue
        d2 = _day(R2['r'].get('date'))
        if not d2 or d2 > d:
            continue
        if rw0 is None:
            rw0, _ = ix.runs(toks, key, RUN, ix.g25)
            qw0, _ = ix.runs(toks, key, QRUN, ix.g12)
        rw, _ = ix.runs(toks, k2, RUN, ix.g25)
        if rw >= max(RUN, rw0):
            return True
        qw, _ = ix.runs(toks, k2, QRUN, ix.g12)
        if rw0 < RUN and qw >= max(QMIN, qw0):
            return True
    return False


def _month_in_window(story, rel_date, win):
    """a story dated only to the month (prec 'month'): its month overlaps [release + win[0], release + win[1]]"""
    d, r0 = str(story.get('date') or ''), _day(rel_date)
    if (story.get('prec') or 'day') != 'month' or len(d) < 7 or not r0:
        return False
    try:
        a = dt.date(int(d[:4]), int(d[5:7]), 1)
    except ValueError:
        return False
    z = (a.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
    return a <= r0 + dt.timedelta(days=win[1]) and z >= r0 + dt.timedelta(days=win[0])


POOL_WIN = (min(TEXT_WIN[0], PRE_WIN[0]), TEXT_WIN[1])   # releases a story is scored against (plus month windows, laterquote)


def _story_pairs(ix, story, tk):
    """every release with evidence for one story (before resolve), in ix.rel order"""
    ctx = story_ctx(ix, story, tk, None, ix.candidates(tk) if tk else set())
    d = _day(story.get('date'))
    month = (story.get('prec') or 'day') == 'month'
    out = []
    for key, R in ix.rel.items():
        d0 = ix.rdate[key]
        if not d0:
            continue
        if d:
            g = (d - d0).days
            if not (POOL_WIN[0] <= g <= POOL_WIN[1] or (g >= LQ_MIN_LAG and key in ctx['cands'])
                    or (month and _month_in_window(story, R['r'].get('date'), TEXT_WIN))):
                continue
        elif not (month and _month_in_window(story, R['r'].get('date'), TEXT_WIN)):
            continue
        e = evidence(ix, key, story, ctx=ctx)
        if e:
            out.append((key, e))
    return out


def match_all(ix, stories, texts):
    """every (release, story) row kept -> {release key: [(story id, evidence), ...]} (tier, lag order). Each story is scored
    against every release (ix.rel) and resolved on its own, so a run on a subset of stories gives exactly those stories'
    rows of the full run."""
    out = {key: [] for key in ix.rel}
    for s in stories:
        t = texts.get(s['id'])
        tk = story_tokens(*t) if t and t[0] else None
        for key, e in resolve(_story_pairs(ix, s, tk), ix):
            out[key].append((s['id'], e))
    for key in out:
        out[key].sort(key=lambda x: (x[1]['tier'], x[1]['lag'] if x[1]['lag'] is not None else 999, x[0]))
    return out


def match_story(ix, story, text=None, kind='html'):
    """Update button: a NEW story against every release -> [(release key, evidence)] (resolved)"""
    tk = story_tokens(text, kind) if text else None
    return resolve(_story_pairs(ix, story, tk), ix)


def block_rows(res):
    """compact per-release list for ins-release_pickup col 'related': [[story id, type, lag], ...]"""
    return [[sid, e['type'], e['lag']] for sid, e in res]


# ---------------- CLI: full run from a build ----------------
def load_build(index_html=None, data_json=None, pickup_json=None):
    if index_html:
        h = open(index_html, encoding='utf-8').read()
        B = {m.group(1): m.group(2) for m in re.finditer(r'<script id="([^"]+)" type="application/json">(.*?)</script>', h, re.S)}
        return json.loads(B['data']), json.loads(B['ins-release_pickup'])
    return json.load(open(data_json, encoding='utf-8')), json.load(open(pickup_json, encoding='utf-8'))


def pickup_releases(rp):
    cols = rp['cols']
    out = []
    for t in rp['rel']:
        x = dict(zip(cols, t))
        out.append({'key': x['key'], 'prid': x.get('prid') or '', 'date': x.get('date') or '', 'url': x.get('url') or '',
                    'title': x.get('title') or '', 'bills': x.get('bills') or [], 'sids': x.get('sids') or []})
    return out


def load_texts(articles_dir):
    texts = {}
    for f in sorted(os.listdir(articles_dir)):
        if not f.endswith('.json') or f in ('manifest.json', 'releases.json') or re.match(r'releases-\d+\.json$', f):   # RELIMG shards
            continue
        for sid, html in json.load(open(os.path.join(articles_dir, f), encoding='utf-8')).items():
            if isinstance(html, dict):
                html = html.get('html') or ''
            texts[sid] = RR.html_text(html)
    return texts


def state_key(r):
    """stable key for the persisted state: the permanent Release ID (prNNNNN); the 5 releases with no official posting keep
    their Story-ID key (ins-release_pickup's offNNN keys are positional and NOT stable)"""
    return r.get('prid') or r['key']


def to_state(rels, res, old=None, only_releases=None, only_stories=None):
    """persisted pipeline file release_related.json: {"v":1,"version":..,"rel":{state key: [[sid, type, lag], ...]}}.
    Full run: old=None. Incremental (Update button): rows of `only_releases` are replaced; rows of `only_stories` are
    dropped everywhere and re-added from `res`."""
    st = {'v': 1, 'version': VERSION, 'rel': dict((old or {}).get('rel', {}))}
    keymap = {r['key']: state_key(r) for r in rels}
    if old is None:
        st['rel'] = {}
    only_releases = {keymap.get(k, k) for k in (only_releases or ())}
    only_stories = set(only_stories or ())
    if old is not None:
        st['rel'] = {k: ([] if k in only_releases else [x for x in v if x[0] not in only_stories]) for k, v in st['rel'].items()}
    for k, v in res.items():
        sk = keymap[k]
        rows = block_rows(v)
        if old is None or sk in only_releases:
            st['rel'][sk] = rows
        elif only_stories:
            st['rel'][sk] = st['rel'].get(sk, []) + [x for x in rows if x[0] in only_stories]
    tier = lambda x: TIER[x[1]]
    clean = {}
    for k, v in sorted(st['rel'].items()):
        seen, rows = set(), []
        for x in sorted(v, key=lambda x: (tier(x), 999 if x[2] is None else x[2], x[0])):
            if x[0] not in seen:   # one row per story per release (backend review finding 2: --update duplicated rows)
                seen.add(x[0])
                rows.append(x)
        if rows:
            clean[k] = rows
    st['rel'] = clean
    return st


def update_stories(D, ix, old, only_r=(), only_s=()):
    """Story IDs whose rows an --update run recomputes: the given stories, every story dated from 14 days before the
    earliest re-matched release on (its pool, its laterquote range and every `later` / next-release interaction), stories
    not dated to the day, and stories holding old rows of the re-matched releases"""
    A = set(only_s)
    ds = [ix.rdate[k] for k in only_r if ix.rdate.get(k)]
    if only_r:
        lo = min(ds) - dt.timedelta(days=-POOL_WIN[0]) if ds else None
        keymap = {k: state_key(ix.rel[k]['r']) for k in only_r}
        for s in D:
            d = _day(s.get('date'))
            if (s.get('prec') or 'day') != 'day' or not d or (lo and d >= lo):
                A.add(s['id'])
        for k in only_r:
            A |= {x[0] for x in (old or {}).get('rel', {}).get(keymap[k], [])}
    return A


def main(argv=None):
    import argparse, csv
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', help='built index.html (data + ins-release_pickup blocks)')
    ap.add_argument('--data'); ap.add_argument('--pickup')
    ap.add_argument('--release-texts', required=True)
    ap.add_argument('--articles', required=True, help='folder of articles/<year>.json viewer copies (an Update run passes the years it read)')
    ap.add_argument('--csv'); ap.add_argument('--json', help='write the state file (release_related.json)')
    ap.add_argument('--update', help='existing release_related.json to update incrementally (Update button)')
    ap.add_argument('--releases', default='', help='comma list of Release IDs / keys to (re)match against all stories in their window')
    ap.add_argument('--stories', default='', help='comma list of Story IDs to (re)match against every release')
    ap.add_argument('--bills-leginfo', default=os.path.join(HERE, 'gabriel_bills_leginfo.json'),
                    help='gabriel_bills_leginfo.json (v3 `later`: own bill of the release session); default: next to relmatch.py')
    a = ap.parse_args(argv)
    D, rp = load_build(a.index, a.data, a.pickup)
    rels = pickup_releases(rp)
    own = own_bill_sessions(json.load(open(a.bills_leginfo, encoding='utf-8'))) if os.path.exists(a.bills_leginfo) else None
    if own is None:
        print('relmatch: %s not found; `later` treats every release bill as its own' % a.bills_leginfo, file=sys.stderr)
    ix = Index(json.load(open(a.release_texts, encoding='utf-8')).get('rel', {}), rels, own)
    texts = load_texts(a.articles)
    byId = {r['id']: r for r in D}
    only_r = {r['key'] for r in rels if a.releases and (r['key'] in a.releases.split(',') or (r['prid'] and r['prid'] in a.releases.split(',')))}
    only_s = set(x for x in a.stories.split(',') if x)
    if a.update:
        old = json.load(open(a.update, encoding='utf-8'))
        A = update_stories(D, ix, old, only_r, only_s)
        # a story whose year's articles file was not passed keeps its rows (its text is unknown to this run), unless named
        years = {f[:-5] for f in os.listdir(a.articles) if f.endswith('.json') and f[:-5].isdigit()}
        A = {sid for sid in A if sid in only_s or str((byId.get(sid) or {}).get('year') or (byId.get(sid) or {}).get('date', ''))[:4] in years}
        res = match_all(ix, [s for s in D if s['id'] in A], texts)
        st = to_state(rels, res, old, set(), A)
    else:
        res = match_all(ix, D, texts)
        st = to_state(rels, res)
    if a.json:
        json.dump(st, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    if a.csv:
        with open(a.csv, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['Release key', 'Release ID', 'Release date', 'Release title', 'Story ID', 'Story date', 'Outlet', 'Headline',
                        'Tier', 'Evidence', 'Evidence label', 'Days after release', 'Shared bills', 'Words in 25-word runs',
                        'Longest run', 'Words in 12-word runs', 'Text cosine', 'Headline cosine', 'Before-release evidence',
                        'Bills named in text only', 'Share of story in runs', 'Longest quoted run', 'Translation cosine',
                        'Translated headline cosine', 'Anchor evidence'])
            for r in rels:
                for sid, e in res.get(r['key'], []):
                    s = byId[sid]
                    w.writerow([r['key'], r['prid'], r['date'], r['title'], sid, s.get('date', ''), s.get('outlet', ''), s.get('hl', ''),
                                'Related' if e['tier'] == 1 else 'Possibly related', e['type'], LABEL[e['type']],
                                '' if e['lag'] is None else e['lag'], '; '.join(e['bills']), e['run_words'], e['longest_run'],
                                e['quote_words'], '' if e['cos'] is None else e['cos'], e['hcos'], e.get('pre', ''),
                                '; '.join(e['bills_text']), e['share'], e['longest_quote'], '' if e['cos_en'] is None else e['cos_en'],
                                '' if e['hcos_en'] is None else e['hcos_en'], e.get('anchor', '')])
    n1 = sum(1 for v in res.values() for _, e in v if e['tier'] == 1)
    n2 = sum(1 for v in res.values() for _, e in v if e['tier'] == 2)
    n3 = sum(1 for v in res.values() for _, e in v if e['tier'] == 3)
    print(json.dumps({'releases': len(rels), 'related': n1, 'possibly': n2, 'later': n3,
                      'by_type': collections.Counter(e['type'] for v in res.values() for _, e in v),
                      'releases_with_related': sum(1 for v in res.values() if any(e['tier'] == 1 for _, e in v))}))
    return res


if __name__ == '__main__':
    main()
