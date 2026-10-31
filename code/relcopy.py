"""relcopy.py - RELCOPIES-v2 (rp-copies, 2026-10-28; Sammy approved the RELPLAN recommendations, incl. overriding DECISIONS
133 for PublicNow reposts). Two more ways a Coverage row is a copy of one of Gabriel's official releases, on top of the
RELRULE-v1 text rule (release_rule.match: >= 25-word runs covering >= 90% of BOTH texts):

1. near_copy(): the story IS the release, condensed or with a photo caption / dateline / byline added. Same run measure as
   the text rule (reprint_rule.measure, 25-word runs, release versions headline+dek+body and body), window -1..+30 days:
     rel_share  = share of the release (>= MIN_REL_WORDS words) inside runs shared with the story  >= NEAR_REL (0.50)
     story_share = share of the story inside those runs
   verdict 'copy'   when story_share >= NEAR_STORY_AUTO (0.85): no hand-check reject at or above it (2026-10-28 audit,
                    10 of 10 copies);
           'review' when 0.50 <= rel_share and story_share < 0.85: the story may add its own reporting (briefs columns,
                    editor's notes, signing stories built around the earlier release) -> review queue, never auto-marked.
2. wire_title_copy(): a row with no saved text from a release wire whose headline is the release title cut short
   ("..." / "…" stripped, >= 5 words, word-for-word prefix of the title), dated 0..+1 days after the release.
   (PublicNow posts only the truncated title; 8 of 8 matched exactly one release in the 2026-10-28 hand checks.)
   Untestable wire rows that match no release are NOT copies of his releases; whether they stay Press release = Yes
   (another issuer's release, DECISIONS 35) is unchanged by this rule.

Standard library + reprint_rule / release_rule (same folder)."""
import re
import reprint_rule as RR
import release_rule as REL

MIN_REL_WORDS = 250
NEAR_REL = 0.50
NEAR_STORY_AUTO = 0.85
WIRE_LAG = (0, 1)
WIRE_MIN_WORDS = 5
WIRE_HOSTS = ("publicnow.com",)          # release-wire outlets whose rows carry only a truncated title
WIRE_OUTLETS = ("PublicNow",)


def near_copy(row_versions, rel):
    """row_versions: reprint_rule versions of the row/story text; rel: an entry of release_rule.releases().
    -> None or {'verdict': 'copy'|'review', 'rel_share', 'story_share', 'label'}"""
    vs = [v for v in row_versions if len(v['raw']) >= RR.MINW and v.get('label') != 'excerpt']
    if not vs or len(rel['vers'][1]['raw']) < MIN_REL_WORDS:
        return None
    if not REL.shares_run(vs, rel):
        return None
    best = None
    for sv in vs:
        for rv in rel['vers']:
            m = RR.measure(sv, rv)
            if m and (best is None or m['raw'][1] > best[0][1]):
                best = (m['raw'], rv['label'])
    if not best or best[0][1] < NEAR_REL:
        return None
    story, relsh = best[0]
    return {'verdict': 'copy' if story >= NEAR_STORY_AUTO else 'review', 'rel_share': round(relsh, 3),
            'story_share': round(story, 3), 'label': best[1]}


def _words(s):
    s = str(s or '').lower().replace('’', "'").replace("'", '')
    return re.sub(r'[^a-z0-9 ]+', ' ', s).split()


def is_wire(outlet, link=''):
    return str(outlet or '').strip() in WIRE_OUTLETS or any(h in str(link or '').lower() for h in WIRE_HOSTS)


def wire_title_copy(headline, row_date, releases):
    """releases: [{'prid'|'url', 'title', 'date'}]; -> the one release whose title starts with the truncated headline, dated
    WIRE_LAG days before the row, or None (also None when two releases qualify)."""
    h = re.sub(r'(\.\.\.|…)\s*$', '', str(headline or '')).strip()
    hw = _words(h)
    if len(hw) < WIRE_MIN_WORDS:
        return None
    d = RR.todate(row_date)
    hits = []
    for r in releases:
        rd = RR.todate(r.get('date'))
        if not d or not rd or not (WIRE_LAG[0] <= (d - rd).days <= WIRE_LAG[1]):
            continue
        if _words(r.get('title'))[:len(hw)] == hw:
            hits.append(r)
    return hits[0] if len(hits) == 1 else None
