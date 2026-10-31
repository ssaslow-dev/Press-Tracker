#!/usr/bin/env python3
"""AVTAB-v1 (agent-avtab, 2026-10-28; Sammy approved the "Audio & video details" tab). Idempotent (marker per target);
apply_all step 4n, after 4m (reltab).
  python3 -I patch_avtab.py [--build-data code/build_data.py] [--sheet-task code/sheet_task.py] [--prompt code/sheet_task_prompt.md]
build_data.py: reads the tab (avtab.block) -> OUT/av.json {"v":1,"cols":KEYS,"rows":{aid:[...]}}; every record whose Original
  Article ID has a tab row gets rec["av"] = {key: value} (non-blank, without sid/medium/from); every reprint object likewise.
sheet_task.py: Task.apply_av (after the pages are saved): each Podcast/Radio/TV/Video row this run added gets a tab row, filled by
  avtab.extract from the find's saved page (the cleaned page = its transcript when the page is one) plus any `av` values the run
  doc carries for its placeholder ({placeholder: {column: value}}, blanks only). Result: av_rows[], av_skipped[].
prompt: one line (Fixed facts) + avtab.py in the pipeline file list."""
import argparse, os

MARK_BD, MARK_ST, MARK_PR = '# AVTAB-v1 build_data', '# AVTAB-v1 sheet_task', 'AVTAB-v1'

BD_R = [
 ("data.sort(key=lambda x: (x['date'] or '', x['id']), reverse=True)\n",
  """data.sort(key=lambda x: (x['date'] or '', x['id']), reverse=True)
# AVTAB-v1 build_data: "Audio & video details" tab (avtab.py next to this script) -> rec['av'] / reps[i]['av'] + block av.json
AVB = {'v': 1, 'cols': [], 'rows': {}}
try:
    import avtab as _AV
    AVB = _AV.block(COV)
except Exception as _e:
    report['av_error'] = repr(_e)[:200]
_AV_SKIP = {'sid', 'medium', 'from'}
def _av_of(aid):
    v = AVB['rows'].get(aid)
    return {k: x for k, x in zip(AVB['cols'], v) if x and k not in _AV_SKIP} if v else None
for _x in data:
    _a = _av_of(_x['aid'])
    if _a: _x['av'] = _a; report['av_stories'] += 1
    for _rp in _x['reps']:
        _a = _av_of(_rp['aid'])
        if _a: _rp['av'] = _a; report['av_reprints'] += 1
report['av_tab_rows'] = len(AVB['rows'])
"""),
 ("dump('idmap', idmap); dump('covcols', covcols)\n",
  "dump('idmap', idmap); dump('covcols', covcols)\ndump('av', AVB)   # AVTAB-v1 build_data\n"),
]

ST_R = [
 ("""try:
    import reltab as RT
except Exception as _e:
    RT = None
""",
  """try:
    import reltab as RT
except Exception as _e:
    RT = None
# AVTAB-v1 sheet_task: "Audio & video details" tab (avtab.py next to this script)
try:
    import avtab as AV
except Exception as _e:
    AV = None
"""),
 ("""        self.apply_release_finds()   # RELCHECK-v2
""",
  """        self.apply_release_finds()   # RELCHECK-v2
        self.apply_av()   # AVTAB-v1
"""),
 ("""    # ---------- derived ----------
""",
  """    # AVTAB-v1 sheet_task: every Podcast/Radio/TV/Video row this run added gets an "Audio & video details" row
    def apply_av(self):
        self.res.setdefault('av_rows', []); self.res.setdefault('av_skipped', [])
        added = [a for k, v in self.res['runs'].items() for a in (v or {}).get('added', [])]
        if not added:
            return
        if AV is None:
            self.res['av_skipped'].append({'why': 'avtab.py not loaded', 'n': len(added)}); return
        ph = {}      # real Article ID -> placeholder, and the run doc's av values
        extra = {}
        for rid, run in (self.db.get('runs') or {}).items():
            for p, real in ((self.res['runs'].get(rid) or {}).get('ids') or {}).items():
                ph[real] = p
            for p, vals in ((run or {}).get('av') or {}).items():
                extra[p] = vals or {}
        page_of = {x['aid']: x['page'] for x in self.res.get('pages', [])}
        rows = []
        for aid in added:
            r = self.s.rows.get(aid)
            if not r or str(self.s.get(r, 'Medium') or '').strip() not in AV.MEDIA:
                continue
            cells = {c: self.s.get(r, c) for c in self.s.col}
            pid = page_of.get(aid) or ph.get(aid)
            chk = self.page_checks.get(pid) if pid else None
            html = (chk or {}).get('html', '') if (chk or {}).get('verdict') == 'ok' else ''
            out = AV.extract(cells, html, '', src='Update button ' + self.today)
            for c, v in (extra.get(ph.get(aid, ''), {}) or {}).items():
                if c in AV.COLS and v not in ('', None) and not out.get(c) and c not in ('Article ID', 'Story ID', 'Medium'):
                    out[c] = v
            rows.append(out)
            self.res['av_rows'].append({'aid': aid, 'type': out['Item type'], 'role': out['His role'],
                                        'transcript': out['Transcript kind']})
        if rows:
            AV.write_tab(self.s.wb, rows)

    # ---------- derived ----------
"""),
 ("""    res['sheet_stories'] = stories
    json.dump(res, open(a.result,""",
  """    res['sheet_stories'] = stories
    if res.get('av_rows'):   # AVTAB-v1 sheet_task (after sheet_stories: patch_f7 keeps its block contiguous with that line)
        res['sheet_line'] = res['sheet_line'][:-1] + f", {len(res['av_rows'])} rows on the Audio & video details tab."
        res['counts']['av_rows'] = len(res['av_rows'])
    json.dump(res, open(a.result,"""),
]

PR_R = [
 ("never pack several values into one cell.",
  "never pack several values into one cell.\n- Audio & video (AVTAB-v1, `avtab.py`): every Podcast / Radio / TV / Video row sheet_task.py adds also gets a row on the "
  "workbook's \"Audio & video details\" tab (keyed by Article ID; item type, show, station/network, air date/time, duration, his role, "
  "guests, mention timestamps, transcript kind/file, platform links), filled from the find's saved page (its transcript when the page "
  "is one); a run doc may carry `av: {placeholder: {column: value}}` for values the page doesn't show. Blank = not established; "
  "never guess. Hosts stay in Coverage Author 1..N."),
 ("`reltab.py` (RELTAB-v1b), ", "`reltab.py` (RELTAB-v1b), `avtab.py` (AVTAB-v1), "),
]


# AVTAB-v2 (Sammy 2026-10-28, "Yes, use air date"): a new archive.org TV find's Coverage Date (and Year) is the Pacific air date of
# the clip, not the clip ID's UTC date; the sheet task sets it on the row it just added (its own new row) and lists it in
# res['av_date_fixes'].
MARK_ST2 = '# AVTAB-v2 sheet_task'
ST2_R = [
 ("""            rows.append(out)
            self.res['av_rows'].append(""",
  """            clip = AV.archive_clip(cells.get('Publisher link'))   # AVTAB-v2 sheet_task: Coverage Date = Pacific air date
            if clip and out.get('Air/publish date'):
                cur = AV.s(cells.get('Date'))[:10]
                air = out['Air/publish date']
                if cur != air:
                    self.s.put(r, 'Date', air)
                    if 'Year' in self.s.col:
                        self.s.put(r, 'Year', int(air[:4]))
                    out['Notes'] = '; '.join(x for x in [n for n in out['Notes'].split('; ') if "clip ID's UTC date" not in n]
                                             + [f'Coverage Date set to the air date (clip ID UTC date {cur})'] if x)
                    self.res.setdefault('av_date_fixes', []).append({'aid': aid, 'old': cur, 'new': air})
            rows.append(out)
            self.res['av_rows'].append("""),
]


def _apply(path, R, mark):
    if not path or not os.path.exists(path):
        return 'skipped (no file)'
    s = open(path, encoding='utf-8').read()
    if mark in s:
        return 'unchanged'
    for a, b in R:
        n = s.count(a)
        if n != 1:
            raise SystemExit(f'{path}: anchor found {n}x: {a[:80]!r}')
        s = s.replace(a, b)
    if mark not in s:
        s = s + ('' if s.endswith('\n') else '\n') + ('<!-- ' + mark + ' -->\n' if path.endswith('.md') else mark + '\n')
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--build-data'); ap.add_argument('--sheet-task'); ap.add_argument('--prompt')
    a = ap.parse_args()
    if a.build_data: print('build_data:', _apply(a.build_data, BD_R, MARK_BD))
    if a.sheet_task: print('sheet_task:', _apply(a.sheet_task, ST_R, MARK_ST))
    if a.sheet_task: print('sheet_task v2:', _apply(a.sheet_task, ST2_R, MARK_ST2))
    if a.prompt: print('prompt:', _apply(a.prompt, PR_R, MARK_PR))
