"""ins-bill_timeline block: leginfo milestones per bill, for the Bills insight view.

Sources, first found wins:
  1. sheet tab "Bills" (if the coordinator adds one): columns Bill, Session, Date, Milestone (= step), Detail,
     optional Final status
  2. <lib>/work/out/bill_milestones.json (agent-billstatus)
No source -> None (the view shows "Milestones not loaded yet").

Block: {"src": "...", "b": [[bill, session, history_url, [[iso_date, kind, label], ...], final_status_short], ...]}
kind "other" = suspense file, enrolled, passed both houses, etc. (listed in the milestone table, not drawn).
kind in: introduced, committee, floor, signed, vetoed, chaptered, died, other.
"""
import json, os, re

KINDS = ('introduced', 'committee', 'floor', 'signed', 'vetoed', 'chaptered', 'died', 'other')
LABEL = {'introduced': 'Introduced', 'committee': 'Committee vote', 'floor': 'Floor vote',
         'signed': 'Signed by Governor', 'vetoed': 'Vetoed by Governor', 'chaptered': 'Chaptered',
         'died': 'Died', 'other': 'Action'}


def _date(v):
    s = str(v or '').strip()
    m = re.match(r'^(\d{4})-(\d\d)-(\d\d)', s)
    if m:
        return s[:10]
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', s)
    if m:
        mo, d, y = m.groups()
        y = ('20' + y) if len(y) == 2 else y
        return f'{y}-{int(mo):02d}-{int(d):02d}'
    return ''


def _kind(k, label=''):
    t = (str(k or '') + ' ' + str(label or '')).lower()
    if not t.strip():
        return 'other'
    first = str(k or '').strip().lower()
    if first in KINDS:
        return first
    for key, words in (('vetoed', ('veto',)), ('signed', ('signed', 'approved by the governor', 'governor approved')),
                       ('chaptered', ('chaptered',)), ('introduced', ('introduc',)),
                       ('floor', ('floor', 'third reading', 'third time', 'concurr')),
                       ('committee', ('committee', 'com.')), ('died', ('died', 'dead'))):
        if any(w in t for w in words):
            return key
    return 'other'


def _bill(v):
    s = re.sub(r'[\s\-]+', ' ', str(v or '').strip().upper())
    m = re.match(r'^([A-Z]+)\s*(\d+)$', s)
    return f'{m.group(1)} {int(m.group(2))}' if m else s


def _session(v):
    s = str(v or '').strip()
    m = re.match(r'^(\d{4})\s*[-/]\s*(\d{2,4})$', s)
    if m:
        a, b = m.groups()
        return f'{a}-{a[:2] + b if len(b) == 2 else b}'
    m = re.match(r'^(\d{4})(\d{4})', s)  # leginfo bill_id prefix 20232024...
    return f'{m.group(1)}-{m.group(2)}' if m else s


def _events(r):
    for key in ('milestones', 'events', 'actions', 'history', 'm'):
        if isinstance(r.get(key), list):
            return r[key]
    return []


STEP = {'introduced': 'introduced', 'committee vote': 'committee', 'floor vote': 'floor', 'concurrence vote': 'floor',
        'signed': 'signed', 'vetoed': 'vetoed', 'chaptered': 'chaptered', 'died': 'died'}
HOUSE = {'Assembly': 'Asm.', 'Senate': 'Sen.'}


def _label(e, k):
    det = re.sub(r'\(Ayes (\d+), Noes (\d+)\)', r'(\1-\2)', str(e.get('detail') or '').strip()).rstrip('.')
    h, com, step = str(e.get('house') or ''), str(e.get('committee') or '').strip().rstrip('.'), str(e.get('step') or '')
    if step == 'committee vote' or (step and 'committee' in step):
        return f"{HOUSE.get(h, h)} {com} committee: {det}".replace('  ', ' ').strip()
    if step == 'floor vote':
        return f"{h} floor: {det}".strip()
    if step == 'concurrence vote':
        return f"{h or 'Assembly'} concurrence: {det}".strip()
    if k in ('signed', 'vetoed'):
        return LABEL[k]
    if k == 'introduced':
        return 'Introduced'
    if step and k == 'other':       # short: suspense file, enrolled, passed both houses, chaptered ...
        return (step.capitalize() + (f' ({HOUSE.get(h, h)} {com})' if com else '')).strip()
    return det or step.capitalize() or LABEL[k]


def final_short(s):
    s = str(s or '').strip()
    if not s:
        return ''
    if s.startswith('Chaptered'):
        return 'Adopted' if 'Res. Chapter' in s else 'Signed into law'   # V23-BILLS: ACR/AJR/ACA are resolutions, not signed
    if s.startswith('Vetoed'):
        return 'Vetoed'
    if s.startswith('Pending'):
        return 'Pending'
    m = re.match(r'^Died - (.*?)(?:\s*\(([^()]*)\))?$', s)
    if m:
        why, par = m.group(1), m.group(2) or ''
        if 'Art. IV' in why:
            return 'Died (missed deadline)'
        if why.lower().startswith('held in committee'):
            com = par.split(',')[0].strip() if ',' in par else ''
            return f'Died in committee ({com})' if com else 'Died in committee'
        return re.sub(r'\b(senate|assembly)\b', lambda m: m.group(1).capitalize(), 'Died ' + re.sub(r'^Died\s+', '', why).lower())
    return re.sub(r'\s*\([^()]*\)$', '', s)


def _rows_from_json(obj):
    if isinstance(obj, dict):
        rows = obj.get('rows') or obj.get('bills')
        if rows is None:  # keyed by bill
            rows = [dict(v, bill=v.get('bill', k)) if isinstance(v, dict) else {'bill': k, 'milestones': v}
                    for k, v in obj.items() if isinstance(v, (dict, list))]
    else:
        rows = obj
    out = {}
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        bill = _bill(r.get('bill') or r.get('measure') or r.get('leginfo_measure'))
        ses = _session(r.get('session') or r.get('bill_id') or '')
        if not bill:
            continue
        ev, steps = [], {str(e.get('step') or '') for e in _events(r) if isinstance(e, dict)}
        for e in _events(r):
            if isinstance(e, (list, tuple)):
                e = dict(zip(('date', 'kind', 'label'), e))
            d = _date(e.get('date'))
            if not d:
                continue
            if e.get('step') is not None:   # agent-billstatus format
                k = STEP.get(str(e['step']), 'other')
                if k == 'chaptered' and 'signed' in steps:
                    k = 'other'             # same day as the signature: one marker is enough
                lab = _label(e, k)
            else:
                lab = str(e.get('label') or e.get('action') or e.get('text') or e.get('desc') or e.get('detail') or '').strip()
                k = _kind(e.get('kind') or e.get('type') or e.get('milestone') or e.get('event'), lab)
            ev.append([d, k, lab or LABEL[k]])
        url = str(r.get('history_url') or r.get('url') or '')
        if 'billHistoryClient.xhtml?bill_id=' in url:
            url = ''                       # rebuilt in the view from bill + session (block size)
        out[(bill, ses)] = {'url': url, 'ev': ev,
                            'fin': final_short(r.get('final_status'))}
    return out


def _rows_from_sheet(df):
    """The "Bills" tab (agent-billstab): Milestone = "Step (House[, Committee])", Detail = leginfo action text.
    Parsed back into the agent-billstatus fields so labels match the JSON route (integrator, LINKUI-v1 build)."""
    cols = {c.strip().lower(): c for c in df.columns}
    need = ('bill', 'session', 'date', 'milestone')
    if not all(n in cols for n in need):
        return {}
    raw = {}
    for _, r in df.iterrows():
        bill, ses, d = _bill(r[cols['bill']]), _session(r[cols['session']]), _date(r[cols['date']])
        if not bill or not d:
            continue
        ms = str(r[cols['milestone']]).strip()
        m = re.match(r'^(.*?)\s*\(([^,()]+)(?:,\s*(.*))?\)$', ms)
        step, house, com = (m.group(1), m.group(2), m.group(3) or '') if m else (ms, '', '')
        e = {'date': d, 'step': step.strip().lower(), 'house': house.strip(), 'committee': com.strip(),
             'detail': str(r[cols['detail']]).strip() if 'detail' in cols else ''}
        o = raw.setdefault((bill, ses), {'ev': [], 'fin': r[cols['final status']] if 'final status' in cols else ''})
        o['ev'].append(e)
    out = {}
    for key, o in raw.items():
        steps = {e['step'] for e in o['ev']}
        ev = []
        for e in o['ev']:
            k = STEP.get(e['step'], 'other')   # same rule as the agent-billstatus JSON route
            if k == 'chaptered' and 'signed' in steps:
                k = 'other'
            ev.append([e['date'], k, _label(e, k)])
        out[key] = {'url': '', 'ev': ev, 'fin': final_short(o['fin'])}
    return out


def build(cov, data, ctx):
    rows, src = {}, ''
    rs = ctx.get('read_sheet')
    df = rs('Bills') if rs else None
    if df is not None and len(df):
        rows, src = _rows_from_sheet(df), 'sheet:Bills'
    if not rows:
        # the lib copy (agent-billstatus) first; in the sheet task's pipeline the copy next to this file (apply_all puts it there)
        p = next((q for q in (os.path.join(ctx.get('lib') or '', 'work', 'out', 'bill_milestones.json'),
                              os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bill_milestones.json')) if os.path.exists(q)), '')
        if p:
            with open(p) as f:
                rows, src = _rows_from_json(json.load(f)), 'leginfo'
    if not rows:
        return None
    b = []
    for (bill, ses), v in sorted(rows.items()):
        ev = sorted({tuple(e) for e in v['ev']})
        if ev:
            b.append([bill, ses, v['url'], [list(e) for e in ev], v.get('fin', '')])
    return {'src': src, 'b': b} if b else None


if __name__ == '__main__':  # test helper: python3 bill_timeline_data.py IN.json OUT.json
    import sys
    with open(sys.argv[1]) as f:
        rows = _rows_from_json(json.load(f))
    b = [[k[0], k[1], v['url'], sorted(v['ev']), v.get('fin', '')] for k, v in sorted(rows.items()) if v['ev']]
    with open(sys.argv[2], 'w') as f:
        json.dump({'src': 'fixture', 'b': b}, f, separators=(',', ':'), sort_keys=True)
    print(sys.argv[2], len(b))
