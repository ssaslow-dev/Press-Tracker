#!/usr/bin/env python3
"""PROQUESTPDF-v1 answer 2: build data/proquest_outlets.json, the ProQuest-name -> tracker-outlet-name map of the Update station's ProQuest box.

    python3 -I work/localapp/station/tools/build_pq_aliases.py --workbook COPY.xlsx [--library data/library] [--out data/proquest_outlets.json] [--check]

Sources, in order (the order is also the order of trust):
  (a) evidence in the data: the workbook's ProQuest rows (which Outlet names ProQuest items are filed under) and the library's ProQuest html copies
      (any ProQuest publication title they carry);
  (b) ProQuest's naming pattern: the rules in data/proquest_outlets_curated.json (clean_rules, key_steps, key_post) and its hand-kept pairs;
  (c) code/outlet_rules.json: the tracker's own folding (feeds, aliases, generic names), copied in whole.
Read only: the workbook and library are opened for reading (pass a COPY of the workbook), code/ is read, nothing but --out is written.
--check: rebuild in memory and fail if --out differs (the page and the tests use the file as built).
Python and the page apply the same rules; tests/pq/alias_test.mjs checks that the keys written here are the keys the page computes.
"""
import argparse, glob, hashlib, html, json, os, re, sys, unicodedata, collections, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(ST, '..', '..', '..'))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def expand(to, m):
    return re.sub(r'\$(\d)', lambda x: m.group(int(x.group(1))) or '', to)


def clean_name(raw, T):
    """a ProQuest publication title -> the name (what pqparse.outletOf does)"""
    t = re.sub(r'\s+', ' ', str(raw or '')).strip()
    t = re.split(r'\s*;\s*', t)[0]
    for r in T['clean_rules']:
        t = re.sub(r['rx'], r['to'], t, count=1, flags=re.I if 'i' in r.get('flags', '') else 0)
    return re.sub(r'\s+', ' ', t).strip()


def base_key(name, T):
    """code/sheet_task._outlet_base, as data steps"""
    s = str(name or '').replace('\u2019', "'").replace('\u2018', "'")
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().strip()
    for r in T['key_steps']:
        if r['id'] == 'punct':
            s = re.sub(r['rx'], r['to'], s).strip()
        else:
            s = re.sub(r['rx'], lambda m, r=r: expand(r['to'], m), s, count=1)
            s = s.strip()
    return s


def keys(name, T):
    """(exact, fold): exact = the plain key; fold = after the PC's feeds and aliases and the leading foreign article"""
    b = base_key(name, T)
    if not b:
        return '', ''
    k = b
    for pre, key in T['feeds'].items():
        if b == pre or b.startswith(pre + ' '):
            k = key
            break
    else:
        k = T['aliases'].get(b, b)
    post = lambda x: re.sub(T['key_post'][0]['rx'], '', x)
    return post(b), post(k)


INFO = ('inputs', 'seen_in_proquest_rows', 'evidence', 'stats', 'fold_key_collisions', 'about')


def functional(d):
    """the part of the file the page and the PC use; per-pair tracker_rows (a workbook count) and the informational blocks left out"""
    o = {k: v for k, v in d.items() if k not in INFO}
    o['pairs'] = [{k: v for k, v in p.items() if k != 'tracker_rows'} for p in d.get('pairs', [])]
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workbook', required=True)
    ap.add_argument('--library', default=os.path.join(REPO, 'data', 'library'))
    ap.add_argument('--rules', default=os.path.join(REPO, 'code', 'outlet_rules.json'))
    ap.add_argument('--curated', default=os.path.join(ST, 'data', 'proquest_outlets_curated.json'))
    ap.add_argument('--out', default=os.path.join(ST, 'data', 'proquest_outlets.json'))
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    import openpyxl
    cur = json.load(open(a.curated, encoding='utf-8'))
    OR = json.load(open(a.rules, encoding='utf-8'))
    T = {k: cur[k] for k in ('clean_rules', 'key_steps', 'key_post')}
    T['feeds'] = OR.get('feeds') or {}
    T['aliases'] = OR.get('aliases') or {}
    generic = OR.get('generic_needs_city') or []
    # --- (a) the workbook
    wb = openpyxl.load_workbook(a.workbook, read_only=True)
    rows = wb['Coverage'].iter_rows(values_only=True)
    hdr = next(rows)
    H = {n: i for i, n in enumerate(hdr)}
    allr = list(rows)
    out_all = collections.Counter(r[H['Outlet']] for r in allr if r[H['Outlet']])
    pq_rows = [r for r in allr if r[H['Data Source']] == 'ProQuest']
    seen = collections.Counter(r[H['Outlet']] for r in pq_rows)
    byfile = {}
    for r in allr:
        for c in ('File name', 'File name 2'):
            if r[H[c]]:
                byfile[r[H[c]]] = r
    pub_lines = collections.Counter()
    nfiles = 0
    for f in sorted(glob.glob(os.path.join(a.library, '*', 'pq*.html'))):
        nfiles += 1
        t = open(f, encoding='utf-8').read()
        m = re.search(r'<p>Publication: ([^<]*)</p>', t)
        if m:
            r = byfile.get(os.path.basename(f))
            pub_lines[(html.unescape(m.group(1)).split(',')[0].strip(), r[H['Outlet']] if r else None)] += 1
    # --- (b) the curated pairs, checked against the workbook
    exact_idx = collections.defaultdict(collections.Counter)
    fold_idx = collections.defaultdict(collections.Counter)
    for name, n in out_all.items():
        e, f = keys(name, T)
        if e:
            exact_idx[e][name] += n
            fold_idx[f][name] += n
    pairs = []
    for p in cur['pairs']:
        e, f = keys(p['pq'], T)
        if p['tracker'] not in out_all:
            sys.exit('pair %r: tracker outlet %r is not an Outlet in the workbook' % (p['pq'], p['tracker']))
        if e in exact_idx and p['tracker'] in exact_idx[e] and not p.get('place'):
            sys.exit('pair %r is redundant: the plain rules already match %r' % (p['pq'], p['tracker']))
        g = base_key(p['pq'], T) in generic
        if g and not p.get('place'):
            sys.exit('pair %r is a generic name and needs a place' % p['pq'])
        pairs.append(dict(pq=p['pq'], place=p.get('place', ''), key=f, tracker=p['tracker'], tracker_rows=out_all[p['tracker']], kind=p['kind'], source=p['source']))
    # --- (c) what the tracker's folding does to the sheet's own outlet names
    collide = {k: dict(v) for k, v in fold_idx.items() if len(v) > 1}
    aliases_live = sum(1 for k, v in T['aliases'].items() if keys(v, T)[1] in fold_idx)
    out = collections.OrderedDict()
    out['id'] = 'PROQUESTPDF-v1 outlet names'
    out['version'] = 1
    out['about'] = ("Built by tools/build_pq_aliases.py from data/proquest_outlets_curated.json (rules and hand-kept pairs), code/outlet_rules.json (the tracker's own folding) and the workbook's ProQuest rows. "
                    "How a ProQuest PDF's outlet is named: (1) clean_rules turn the Publication title into a name (text before ';', edition and '(Online)' suffixes off); (2) the name gets a key: key_steps then the PC's feeds and aliases then key_post "
                    "(exact = before the PC aliases, fold = after); (3) a pair (below) wins; a generic name (generic_needs_city) with no pair for its place is never matched; else the tracker's own spelling for the same exact key, then the same fold key; "
                    "else the cleaned name is kept and the row's Team note says 'outlet name from ProQuest; check'. Nothing is guessed.")
    out['inputs'] = dict(outlet_rules_sha256=sha(open(a.rules, 'rb').read()), curated_sha256=sha(open(a.curated, 'rb').read()),
                         workbook_rows=len(allr), proquest_rows=len(pq_rows), proquest_html_copies=nfiles)
    out['clean_rules'] = cur['clean_rules']
    out['key_steps'] = cur['key_steps']
    out['key_post'] = cur['key_post']
    out['feeds'] = T['feeds']
    out['aliases'] = T['aliases']
    out['generic_needs_city'] = generic
    out['pairs'] = pairs
    out['seen_in_proquest_rows'] = [dict(outlet=k, rows=v) for k, v in sorted(seen.items(), key=lambda x: (-x[1], str(x[0])))]
    out['evidence'] = dict(
        library_publication_lines=[dict(publication_line=k[0], filed_under=k[1], copies=v) for k, v in sorted(pub_lines.items(), key=lambda x: str(x))],
        library_note=("The library's ProQuest html copies are text made from the PDFs and carry no ProQuest publication title. The only 'Publication:' lines are inside University Wire items, naming the student paper; "
                      "every ProQuest row among them is filed under 'University Wire', the wire's own name (the one exception is a NewsBank row, Daily Bruin, whose second source is such a copy), so they give no alias. The workbook's 64 ProQuest Outlet names (seen_in_proquest_rows) show only the tracker's side."),
    )
    out['stats'] = dict(pairs=len(pairs), clean_rules=len(cur['clean_rules']), key_steps=len(cur['key_steps']) + len(cur['key_post']), outlet_rules_aliases=len(T['aliases']),
                        outlet_rules_aliases_with_a_tracker_outlet=aliases_live, outlet_rules_feeds=len(T['feeds']), generic_names=len(generic),
                        tracker_outlets=len(out_all), proquest_outlet_names_seen=len(seen), fold_key_collisions=len(collide))
    out['fold_key_collisions'] = collide
    s = json.dumps(out, indent=1, ensure_ascii=False, sort_keys=False) + '\n'
    if a.check:
        # the check compares what the page uses: the rules, keys, feeds, aliases, generic names and pairs. The fingerprints
        # and counts taken from the workbook and library (inputs, seen_in_proquest_rows, evidence, stats, fold_key_collisions,
        # each pair's tracker_rows) are informational: they change whenever the workbook does and do not fail the check.
        if not os.path.exists(a.out):
            sys.exit('proquest_outlets.json is missing: run build_pq_aliases.py')
        have = json.load(open(a.out, encoding='utf-8'))
        want = json.loads(s)
        if functional(have) != functional(want):
            diff = [k for k in sorted(set(have) | set(want)) if k not in INFO and have.get(k) != want.get(k)]
            if functional(have).get('pairs') != functional(want).get('pairs') and 'pairs' not in diff:
                diff.append('pairs')
            sys.exit('proquest_outlets.json differs from the build in: %s. Rerun build_pq_aliases.py' % ', '.join(diff))
        same = open(a.out, encoding='utf-8').read() == s
        print('ok: matches the build' if same else 'ok: aliases match the build (informational fields differ: workbook fingerprints and counts; rerun to refresh)')
        return
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write(s)
    print(json.dumps(out['stats'], indent=1))
    print('collisions:', json.dumps(collide, ensure_ascii=False)[:1500])


if __name__ == '__main__':
    main()
