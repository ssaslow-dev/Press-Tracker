#!/usr/bin/env python3
"""T23: old -> new ID map for the Coverage workbook (DECISIONS 2026-10-27 "new ID scheme").

Usage: python3 -I make_id_map.py COVERAGE.xlsx OUT_DIR [--dup DUP_ID_MAP.json]
Writes OUT_DIR/id_map.csv, sid_map.json, aid_map.json and id_map_report.json.

Rules
- One 5-digit sequence 00001... over every Article ID AND Print Article ID, in Coverage sheet order.
  A Web + Print row's Print Article ID takes the number right after its own Article ID.
- New IDs are plain 5-digit numbers (no suffix; DECISIONS amendment 2026-10-27). The row's o/r goes only into
  library file names: column file_suffix = 'o' (Original) / 'r' (Reprint) / '' (blank status), for agent-librename.
- A Print Article ID that is also an Article ID on another row reuses that row's number (reported as a collision).
- Story ID jg-NNNNN -> sNNNNN (same digits). Tracker story code (6-hex legacy codes) is not touched.
- --dup: ids removed as duplicates (work/dup_id_map.json {"aid": {removed: kept}, "sid": {...}}) are mapped
  through to their surviving row's new id in aid_map.json / sid_map.json.
"""
import csv, json, os, re, sys, argparse
import openpyxl

SUFFIX = {'Original': 'o', 'Reprint': 'r', 'Reprint (unverified)': 'r'}   # F1: regroup status 'Reprint (unverified)' (DECISIONS) -> r
OLD_AID = re.compile(r'^(nb|ws|pq)-\d{5}$')
OLD_SID = re.compile(r'^jg-(\d{5})$')
COLS = ['row', 'old_article_id', 'new_article_id', 'old_print_article_id', 'new_print_article_id',
        'old_story_id', 'new_story_id', 'status', 'file_suffix']


def s(v):
    return '' if v is None else str(v).strip()


def new_sid(old):
    m = OLD_SID.match(old)
    if not m:
        raise ValueError(f'unexpected Story ID {old!r}')
    return 's' + m.group(1)


def build(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb['Coverage']
    it = ws.iter_rows(values_only=True)
    hdr = list(next(it))
    ix = {h: i for i, h in enumerate(hdr)}
    raw = []
    for n, row in enumerate(it, start=2):
        aid = s(row[ix['Article ID']])
        if not aid:
            continue
        raw.append((n, aid, s(row[ix['Print Article ID']]), s(row[ix['Story ID']]), s(row[ix['Original or reprint']])))
    wb.close()
    article_ids = {r[1] for r in raw}
    rep = {'rows': len(raw), 'collisions': [], 'blank_status': [], 'bad_ids': [], 'print_ids': 0}
    num = {}            # old id -> number
    nxt = 0
    out = []
    for n, aid, pid, sid, st in raw:
        if not OLD_AID.match(aid):
            rep['bad_ids'].append({'row': n, 'id': aid})
        if aid in num:
            raise SystemExit(f'duplicate Article ID {aid} on row {n}')
        if aid not in num:
            nxt += 1
            num[aid] = nxt
        if pid:
            rep['print_ids'] += 1
            if pid in article_ids and pid != aid:
                rep['collisions'].append({'row': n, 'print_id': pid})   # numbered on its own Article ID row
            elif pid in num:
                raise SystemExit(f'Print Article ID {pid} on row {n} repeats an earlier print id')
            else:
                nxt += 1
                num[pid] = nxt
        out.append((n, aid, pid, sid, st))
    # a collided print id may come before its Article ID row in sheet order: number it at its Article ID row
    rows = []
    for n, aid, pid, sid, st in out:
        suf = SUFFIX.get(st, '')
        if st and st not in SUFFIX:
            raise SystemExit(f'unknown status {st!r} on row {n}')
        if not st:
            rep['blank_status'].append(aid)
        rows.append({'row': n, 'old_article_id': aid, 'new_article_id': f'{num[aid]:05d}',
                     'old_print_article_id': pid, 'new_print_article_id': f'{num[pid]:05d}' if pid else '',
                     'old_story_id': sid, 'new_story_id': new_sid(sid) if sid else '', 'status': st,
                     'file_suffix': suf})
    rep['last_number'] = nxt
    return rows, rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('xlsx'); ap.add_argument('out'); ap.add_argument('--dup')
    a = ap.parse_args()
    rows, rep = build(a.xlsx)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'id_map.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
    aid_map, sid_map = {}, {}
    for r in rows:
        aid_map[r['old_article_id']] = r['new_article_id']
        if r['old_print_article_id']:
            aid_map[r['old_print_article_id']] = r['new_print_article_id']
        if r['old_story_id']:
            sid_map[r['old_story_id']] = r['new_story_id']
    rep['dup_mapped'] = {'aid': 0, 'sid': 0, 'aid_unresolved': [], 'sid_unresolved': []}
    if a.dup:
        dup = json.load(open(a.dup, encoding='utf-8'))
        for kind, m, tgt in (('aid', dup.get('aid', {}), aid_map), ('sid', dup.get('sid', {}), sid_map)):
            for old, keep in m.items():
                seen = set()
                while keep in m and keep not in tgt and keep not in seen:   # chains removed -> removed -> kept
                    seen.add(keep); keep = m[keep]
                if old in tgt:
                    raise SystemExit(f'dup id {old} still a live row')
                if keep in tgt:
                    tgt[old] = tgt[keep]; rep['dup_mapped'][kind] += 1
                else:
                    rep['dup_mapped'][kind + '_unresolved'].append(old)
    json.dump(aid_map, open(os.path.join(a.out, 'aid_map.json'), 'w'), indent=0)
    json.dump(sid_map, open(os.path.join(a.out, 'sid_map.json'), 'w'), indent=0)
    rep['aid_map'] = len(aid_map); rep['sid_map'] = len(sid_map)
    rep['blank_status_count'] = len(rep['blank_status'])
    json.dump(rep, open(os.path.join(a.out, 'id_map_report.json'), 'w'), indent=1)
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in rep.items()}, default=str))


if __name__ == '__main__':
    main()
