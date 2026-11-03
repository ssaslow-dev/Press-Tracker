"""LIBFILES-v1 test helper: builds ONE update zip the way the Update station's packer does (db docs + files named by the station's names.js + a manifest `names` block),
carrying every kind of item the library has to receive:

    a web find with a raw page (kept under _original_html), a NewsBank story PDF, a ProQuest story (html copy + original PDF, one of them an older year),
    a press release, a reprint of an existing story (ProQuest copy), an undated web find, three YouTube-run rows (a blocked find, a podcast, a station-clip
    video) and one YouTube attach to a story already in the tracker.

The pieces come from real station outputs (the NewsBank, ProQuest and YouTube zips the station's own tests made: nb_update.zip, pq_update.zip, yt_update.zip, all
made from the v64 for-Update file); the run documents are merged here and the names block is computed by the station's own names.js under node, so the zip is
what the station would have packed for this run. The sources are looked for in SRC (default: the scratchpad folders those tests wrote); the test skips when absent.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'updatefolder'))
import formats as F  # noqa: E402

NAMES_JS = REPO / 'work' / 'localapp' / 'station' / 'src' / 'names.js'

PLAN_JS = r"""
const N = require(process.argv[1]);
const inp = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const byCode = new Map(inp.stories.map(s => [s.code.toLowerCase(), s.id]));
const pl = N.plan({ next: inp.next, today: inp.today, pages: inp.pages, runs: inp.runs, existingStories: new Set(inp.stories.map(s => s.id)), storyOfCode: c => byCode.get(c) || '' });
process.stdout.write(JSON.stringify({ plan: pl, block: N.manifestBlock(pl, inp.today) }));
"""


def read_zip(path):
    z = zipfile.ZipFile(path)
    docs = {}
    for n in z.namelist():
        if n.startswith('db/') and n.endswith('.json'):
            _, coll, fn = n.split('/')
            docs.setdefault(coll, {})[fn[:-5]] = json.loads(z.read(n))
    return z, json.loads(z.read('manifest.json')), docs


def names_plan(for_update: dict, runs, pages, today):
    inp = {'next': for_update['rows']['next'], 'today': today, 'pages': pages, 'runs': runs,
           'stories': [{'id': s['id'], 'code': s.get('code') or ''} for s in for_update['stories'] if s.get('code')]}
    p = subprocess.run(['node', '-e', PLAN_JS, str(NAMES_JS)], input=json.dumps(inp), capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError('names.js failed: ' + p.stderr[-800:])
    return json.loads(p.stdout)


def pdf_bytes_for(sources, doc):
    """the PDF of a pages doc: the sources' zips hold it under its library name (the station moved it out of files/)"""
    for z, man, _ in sources:
        for it in man.get('names', {}).get('items', []):
            if it.get('pdf_for') and it['pdf_for'] == (doc.get('nb') or doc.get('pq') or {}).get('file'):
                return z.read(it['pdf'] or it['copy'])
    raise KeyError(doc.get('url'))


def build(out_zip: Path, *, for_update: dict, src: dict, today: str, workbook_sha: str, attach_row_link: str, tag='A', web_only_extra=False) -> dict:
    """returns {'zip': path, 'rows': {key: row}, 'names': block}. tag A = the full set; tag B = a smaller second update from the SAME for-Update file (its numbers will be taken)"""
    nb = read_zip(src['nb']); pq = read_zip(src['pq']); yt = read_zip(src['yt'])
    nbrun = next(iter(nb[2]['runs'].values())); pqrun = next(iter(pq[2]['runs'].values())); ytrun = next(iter(yt[2]['runs'].values()))
    pages, reprints, rows, keys = {}, {}, [], {}

    def take(run, i, key, **over):
        r = copy.deepcopy(run['rows'][i])
        r.update(over)
        rows.append(r)
        keys[key] = r
        return r

    def page(zdocs, code):
        pages[code] = copy.deepcopy(zdocs['pages'][code])
        return pages[code]

    web_html = ('<html><head><title>LibFiles web find</title></head><body><nav>Home | Sports | Weather | Subscribe now</nav><article><h1>{h}</h1>'
                '<p>Assemblymember Jesse Gabriel (D-Encino) said the {x} measure would move to the Assembly floor next week, according to his office. '
                'The Encino Democrat chairs the Budget Committee. Lawmakers said the budget would be debated next week in Sacramento. ' * 1 +
                '</p><p>Local officials welcomed the plan and said {x} residents had asked for it for years. Gabriel added that he would continue to push the bill.</p></article>'
                '<footer>Copyright {x}. All rights reserved. Related stories | Trending | Contact us</footer></body></html>')
    tpl = ytrun['rows'][1]       # the podcast row: a complete web row

    def web_row(key, n, date, outlet, hl, link):
        r = copy.deepcopy(tpl)
        r.update({'Date': date, 'Year': date[:4] if date else '', 'Outlet': outlet, 'Format': 'Article', 'Headline': hl, 'Publisher link': link, 'Medium': 'Online news',
                  'Tracker story code': f'jg-1f{n:04x}', 'Date source': 'page metadata' if date else '', '_date_src': 'page' if date else '', 'Article ID': f'NEW-lf-{n}', 'Story ID': f'sNEW-lf-{n}'})
        if not date:
            r.pop('Date source', None); r.pop('_date_src', None)
        rows.append(r)
        keys[key] = r
        host = re.match(r'https?://([^/]+)/', link).group(1)
        raw = web_html.format(h=hl, x=outlet)
        scoped = '<html><head><title>%s</title></head><body><article>%s</article></body></html>' % (hl, raw.split('<article>')[1].split('</article>')[0])
        pages[r['Tracker story code']] = {'url': link, 'title': hl, 'clean': raw, 'scoped': scoped, 'publine': '', 'at': '2026-11-03T02:00:00.000Z'}
        assert host
        return r

    if tag == 'A':
        take(nbrun, 0, 'nb_a'); page(nb[2], nbrun['rows'][0]['Tracker story code'])
        take(nbrun, 1, 'nb_b', Date='2025-12-30', Year='2025'); page(nb[2], nbrun['rows'][1]['Tracker story code'])
        take(pqrun, 0, 'pq_a'); page(pq[2], pqrun['rows'][0]['Tracker story code'])
        take(pqrun, 1, 'pq_b', Date='2024-05-05', Year='2024'); page(pq[2], pqrun['rows'][1]['Tracker story code'])
        take(pqrun, 6, 'pq_reprint'); page(pq[2], 'rp-4665d06e9c62'); reprints['rp-4665d06e9c62'] = pq[2]['reprints']['rp-4665d06e9c62']
        web_row('web', 1, '2026-10-28', 'LibFiles Gazette Test', 'Gabriel bill on library hours advances in Sacramento', 'https://www.libfiles-gazette.test/news/gabriel-library-hours')
        web_row('undated', 2, '', 'LibFiles Undated Test', 'Gabriel meets Encino neighbors about the new park', 'https://www.libfiles-undated.test/news/gabriel-park')
        for i, k in enumerate(('yt_nocopy', 'yt_podcast', 'yt_clip')):
            take(ytrun, i, k); page(yt[2], ytrun['rows'][i]['Tracker story code']) if ytrun['rows'][i]['Tracker story code'] in yt[2]['pages'] else None
        # the podcast page of the yt zip carries a real host: fine as it is
    else:
        take(nbrun, 2, 'nb_c'); page(nb[2], nbrun['rows'][2]['Tracker story code'])
        web_row('web', 3, '2026-10-29', 'LibFiles Second Gazette Test', 'Gabriel announces a second library hours hearing', 'https://www.libfiles-second.test/news/gabriel-hearing')
    for i, r in enumerate(rows, 1):
        r['Article ID'] = f'NEW-lf{tag}-{i}'
        if r['Original or reprint'] == 'Original':
            r['Story ID'] = f'sNEW-lf{tag}-{i}'
    run = {'at': '2026-11-03T02:10:00.000Z', 'mode': 'find', 'status': 'done', 'stories': sorted({r['Tracker story code'] for r in rows if r.get('Tracker story code')}),
           'reprints': [pq[2]['reprints']['rp-4665d06e9c62']] if tag == 'A' else [], 'rows': rows, 'print_pages': [], 'found_by': {'mixed': len(rows)}, 'searched_to': '', 'since': '',
           'since_manual': False, 'left': [], 'tones': [], 'authors': [], 'translations': [], 'bills_new': [], 'lookups': [], 'unconfirmed': []}
    if tag == 'A':
        run['attach'] = [dict(ytrun['attach'][0], row_link=attach_row_link, story='')]
        run['releases_new'] = [{'url': 'https://gabriel.asmdc.org/press-releases/libfiles-test-release', 'date': '2026-10-29', 'title': 'Gabriel statement on library hours', 
                                'text': 'SACRAMENTO - Assemblymember Jesse Gabriel (D-Encino) today announced a hearing on library hours.\n\nThe hearing is set for next week.'}]
        run['nb'] = nbrun.get('nb'); run['pq'] = pqrun.get('pq')
    rid = f'run-lf{tag.lower()}0001'
    plan = names_plan(for_update, [{'id': rid, 'at': run['at'], 'rows': rows, 'releases_new': run.get('releases_new', [])}], pages, today)
    lib = {}
    for f in plan['plan']['files']:
        if f['kind'] == 'html':
            lib[f['path']] = f['text'].encode('utf-8')
        else:
            doc = pages[f['doc']]
            lib[f['path']] = pdf_bytes_for([nb, pq], doc)
    for z, _, _ in (nb, pq, yt):
        pass
    db = out_zip.with_suffix('.db')
    import shutil
    shutil.rmtree(db, ignore_errors=True)
    for coll, docs in {'runs': {rid: run}, 'pages': pages, 'reprints': reprints}.items():
        for k, v in docs.items():
            p = db / coll / f'{k}.json'
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(v), encoding='utf-8')
    F.pack_update_zip(out_zip, db, workbook_sha, library=lib, extra_manifest={'names': plan['block'], 'station_version': 'station-1', 'for_update_created_at': for_update.get('created_at', ''), 'for_update_name': 'for_update.json'})
    return {'zip': out_zip, 'rows': keys, 'names': plan['block'], 'library': sorted(lib), 'run_id': rid}
