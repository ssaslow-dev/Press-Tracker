"""travel_data.py — block "tab-travel" for the Story travel tab (TABS-v1, agent-tab-travel; contract §6: build(cov, data, ctx)).

Why: reprint records (story.reps) carry outlet, date, county, state, headline and links but no Medium or Language, and the
story page shows a type chip (Reach / Medium / Language) per pickup and counts pickups in other languages. Both columns are
on the reprint's own Coverage row (Medium on ~99%, Language on ~94% of reprint rows), so they are read from there by
Article ID. Reach per reprint stays with the existing ins-story_travel block (story_travel_data.py) and tab-common.
Nothing is written to the sheet.

Block: {"v": [value, ...], "r": {Article ID: [medium index, language index]}}
  index 0 = blank. Language "English" is stored as blank (the default), so only other languages take space.
  Only reprint rows that some story in data.json lists are included. Deterministic (sorted).
"""


def build(cov, data, ctx):
    need = sorted({str(p.get('aid') or '').strip() for r in data for p in (r.get('reps') or []) if p.get('aid')})
    if not need or 'Article ID' not in cov.columns:
        return None
    col = lambda k: cov[k] if k in cov.columns else [''] * len(cov)
    by = {}
    for aid, med, lang in zip(cov['Article ID'], col('Medium'), col('Language')):
        a = str(aid).strip()
        if not a:
            continue
        a = a.zfill(5)
        lang = str(lang).strip()
        by[a] = (str(med).strip(), '' if lang.lower() == 'english' else lang)
    vals = sorted({v for a in need for v in by.get(a, ('', '')) if v})
    idx = {v: i + 1 for i, v in enumerate(vals)}
    r = {}
    for a in need:
        m, l = by.get(a, ('', ''))
        if m or l:
            r[a] = [idx.get(m, 0), idx.get(l, 0)]
    return {'v': [''] + vals, 'r': r}


if __name__ == '__main__':  # standalone: python3 -I travel_data.py XLSX DATA_JSON OUT_JSON
    import json, sys
    import pandas as pd
    cov = pd.read_excel(sys.argv[1], sheet_name='Coverage', dtype=str).fillna('')
    res = build(cov, json.load(open(sys.argv[2])), {})
    txt = json.dumps(res, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    open(sys.argv[3], 'w').write(txt)
    print(len(res['r']), 'rows,', len(res['v']), 'values,', len(txt.encode()), 'bytes')
