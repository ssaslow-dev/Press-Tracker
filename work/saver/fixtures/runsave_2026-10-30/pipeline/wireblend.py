"""wireblend.py - WIREBLEND-v1 (Sammy 2026-10-29): "staff and wire reports" / blended stories.

A paper's own story that wraps local reporting around wire paragraphs stays its OWN story (the paper's Original, never a Reprint),
carries a "uses wire copy" note + a link to the wire story, and counts toward the wire story's pickups. Detection = a wire credit
signal on the paper's row/text AND partial containment of a wire Original's text in the paper's text, BELOW the reprint threshold
(reprint_rule.THR = 0.90 of both texts), so the reprint rule keeps deciding everything at or above it.

detect(row, text, wire_pool, texts) -> dict | None
  signals (any): a wire service in the byline / Author title (credit_of), a credit line or "(AP) -" dateline (credit_of), or a
  blend phrase ("staff and wire reports", "wire services", "The Associated Press contributed", "with wire reports").
  evidence: the wire Original within +-WIN_DAYS (same service as the credit when the credit names one; any wire Original when the
  signal is the generic phrase) whose text has >= LO of its words inside runs of >= 25 identical words found in the paper's text
  AND >= MIN_WORDS matched words, while pair_class says it is not a Reprint (so wire_cov < THR, or the credit-less containment).
Never: a wire/prservice/aggregator row as the blend, an AV item, a row in the same house as the wire, a Reprint row, a press release.
"""
import re
import reprint_rule as RR

WIN_DAYS = 7
NOT_BLEND_TYPES = RR.BLEND_NOT


def wire_pool(originals):
    """Original rows (dicts) that are wire-type text stories: the pool a blend is matched against"""
    return [o for o in originals if RR.row_type(o) == 'wire' and not RR.is_av_item(o) and str(o.get('Press release') or '').lower() != 'yes']


def signals(row, text):
    """(set of wire services credited, blend phrase or '', [evidence])"""
    cr = RR.credit_of(row, text)
    svc = {s for s in cr if not s.startswith('STATION:')}
    ev = [f'{s}: {e}' for s, es in cr.items() for e in es[:1] if s in svc]
    ph = RR.blend_phrase(row, text)
    if ph:
        ev.append('phrase: "' + ph + '"')
    return svc, ph, ev


def detect(row, text, pool, texts, days=WIN_DAYS):
    """the blend verdict for one non-wire Original row, or None: the best wire Original (+-days) whose pair_class cell is 'blend'.
    pool: wire_pool(); texts: {Article ID: text}"""
    if str(row.get('Original or reprint') or 'Original') != 'Original' or RR.row_type(row) in NOT_BLEND_TYPES or RR.is_av_item(row):
        return None
    if len((text or '').split()) < 100:
        return None
    d = RR.todate(row.get('Date'))
    svc, ph, ev = signals(row, text)
    if not d or not (svc or ph):
        return None
    va = RR.version(text)
    best = None
    for w in pool:
        wd = RR.todate(w.get('Date'))
        if not wd or abs((d - wd).days) > days or w.get('Article ID') == row.get('Article ID') or RR.same_house(row, w):
            continue
        wt = texts.get(w.get('Article ID')) or ''
        if len(wt.split()) < 60:
            continue
        v = RR.text_verdict([va], [RR.version(wt)])
        if not v:
            continue
        credits = any(RR.service_matches_outlet(c, w.get('Outlet'), RR.row_key(w)) for c in svc)
        cell = RR.blend_cell(w, row, v, credits, text)
        if not cell:
            continue
        sc = (cell['wire_cov'], cell['matched'])
        if best is None or sc > best['sc']:
            best = dict(cell, sc=sc, wire_aid=w['Article ID'], wire_sid=w.get('Story ID'), wire_outlet=w.get('Outlet'), wire_date=str(w.get('Date'))[:10],
                        wire_link=w.get('Publisher link') or w.get('NewsBank article link') or '', signals=ev, service_credit=credits,
                        full_wire_inside=cell['wire_cov'] >= RR.THR)
    if best:
        best.pop('sc')
    return best


NOTE_PREFIX = 'Uses wire copy'
def note_for(b):
    """the Team-note text: parseable (Story ID after 'of'), human readable"""
    return f"{NOTE_PREFIX} of {b['wire_sid']} ({b['wire_outlet']}, {b['wire_date']}, {round(b['wire_cov'] * 100)}% of the wire text){' ' + b['wire_link'] if b.get('wire_link') else ''}"
NOTE_RX = re.compile(r'Uses wire copy of (s\d{5})')
def wire_story_of(row):
    """the wire story's Story ID a row declares (column 'Uses wire copy of' when the sheet has it, else the Team note), or ''"""
    v = str(row.get('Uses wire copy of') or '').strip()
    if re.match(r'^s\d{5}$', v):
        return v
    m = NOTE_RX.search(str(row.get('Team note') or ''))
    return m.group(1) if m else ''


def add_pickups(data, cov):
    """build_data hook (after `data` is built, before sorting): every blended Original counts toward its wire story's pickups.
    cov: the Coverage DataFrame (or list of row dicts). Adds {'blend': True, ...} to the wire story's reps, +1 to its `rep` and
    `also` when the blended paper's outlet is not already counted for that story, and the county to `rc`. The blended story keeps its
    own record (its outlet counts once, as an Original: tabs that sum reps per outlet skip p.blend). Returns the number added."""
    rows = cov.to_dict('records') if hasattr(cov, 'to_dict') else list(cov)
    by = {str(r.get('id')): r for r in data}
    n = 0
    for r in rows:
        if str(r.get('Original or reprint') or '') != 'Original':
            continue
        w = wire_story_of(r)
        rec = by.get(w)
        mine = by.get(str(r.get('Story ID') or ''))
        if not rec or not mine or w == str(r.get('Story ID')):
            continue
        outlet = mine.get('outlet') or str(r.get('Outlet') or '')
        if any(p.get('aid') == r.get('Article ID') for p in rec['reps']):
            continue
        rec['reps'].append({'aid': str(r.get('Article ID') or ''), 'outlet': outlet, 'date': str(r.get('Date') or '')[:10], 'county': mine.get('county', ''),
                            'state': str(r.get('Outlet state') or ''), 'link': mine.get('link', ''), 'hl': mine.get('hl', ''), 'src': mine.get('src', ''),
                            'lk': mine.get('lk', []), 'blend': True, 'story': mine['id']})
        rec['reps'].sort(key=lambda x: (x.get('date') or '9999', (x.get('outlet') or '').lower()))
        seen = [x for x in str(rec.get('also') or '').split('; ') if x]   # v23-int: a list (order kept; a set made builds differ run to run)
        if outlet and outlet != rec.get('outlet') and outlet not in seen:
            rec['rep'] = int(rec.get('rep') or 0) + 1
            rec['also'] = '; '.join(seen + [outlet]) if seen else outlet
        if mine.get('county') and mine['county'] not in rec.get('rc', []):
            rec['rc'] = sorted(set(rec.get('rc', [])) | {mine['county']})
        n += 1
    return n
