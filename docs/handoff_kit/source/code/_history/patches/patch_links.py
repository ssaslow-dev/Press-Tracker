"""agent-links: list story links the same way as the ProQuest link (DECISIONS 2026-10-27, final links scope).
LINKS-v2 (agent-code): + Internet Archive TV clips (archive.org/details/<CALLSIGN>_<date>_<time>...), label "Internet Archive (TV clip)".

Listed: California State Library (CSL) links to NewsBank / ProQuest, and the publisher's own link. Nothing else.
Applies anchored, idempotent edits to the tracker JS and build_data.py.

Usage: python3 -I patch_links.py JS_IN JS_OUT [BUILD_DATA_IN BUILD_DATA_OUT]
  (in == out is fine.) Each edit's anchor must match exactly once; an edit already applied (marker present) is skipped.
  Exit 1 if an anchor is missing or ambiguous; nothing is written in that case.
"""
import sys, re

MARK = 'LINKS-v1'

# ---------------------------------------------------------------- build_data.py
BD_BLOCK = r'''
# ---- LINKS-v1 (agent-links): links the tracker lists, as [kind, url] pairs (DECISIONS 2026-10-27, final links scope).
# Listed: NewsBank / ProQuest through the California State Library (CSL) and the publisher's own link. Nothing else.
# CSL pattern: ProQuest  https://castatelib.idm.oclc.org/login?url=<ProQuest URL>   (sheet: "ProQuest via CA State Library")
#              NewsBank  https://infoweb-newsbank-com.castatelib.idm.oclc.org/<path>  (sheet: "... via CA State Library";
#              the same URL as infoweb.newsbank.com with the host swapped to the CSL proxy host)
# CSL_DERIVE: the sheet has no CSL column for "NewsBank article link" / "NewsBank print article link" (and a few rows may
# lack the CSL twin of a ProQuest / print-page link); True derives the CSL link with the same rewrite (100% of the sheet's
# existing CSL pairs follow it). False lists only CSL links written in the sheet.
CSL_DERIVE = True
CSL_PQ = 'https://castatelib.idm.oclc.org/login?url='
CSL_NB_HOST = 'infoweb-newsbank-com.castatelib.idm.oclc.org'
def csl_of(u):
    u = s(u)
    if not re.match(r'^https?://', u): return ''
    if re.match(r'^https?://castatelib\.idm\.oclc\.org/login\?url=https?://(www\.)?proquest\.com/', u) or \
       re.match(r'^https?://' + re.escape(CSL_NB_HOST) + '/', u): return u
    if not CSL_DERIVE: return ''
    if re.match(r'^https?://(www\.)?proquest\.com/', u): return CSL_PQ + u
    if re.match(r'^https?://infoweb\.newsbank\.com/', u): return re.sub(r'^https?://infoweb\.newsbank\.com/', 'https://' + CSL_NB_HOST + '/', u)
    return ''
# publisher link -> listed only when it is the outlet's own site
NOT_OWN_HOST = re.compile(r'(^|\.)(archive\.org|google\.[a-z.]+|github\.com|blob\.core\.windows\.net|tvmaze\.com|nalert\.blogspot\.com|'
                          r'nmreports\.org|oag\.ca\.gov|oclc\.org|newsbank\.com|proquest\.com)$')
AGGREGATOR = {'yahoo.com': 'yahoo', 'aol.com': 'aol', 'msn.com': 'msn', 'newsbreak.com': 'newsbreak', 'pressreader.com': 'pressreader'}
WIRE_OUTLET = re.compile(r'^(TCA (News Service|Regional News)|University Wire|U\.S\. Newswire|Contify\b|National Desk, The|California Black Media)')
NOT_OWN_PAIR = [  # (host suffix, outlet pattern): another outlet's site carrying this outlet's story
    ('abc30.com', 'Press Democrat'), ('cbsnews.com', 'Press Democrat'), ('aboluowang.com', 'Epoch Times'),
    ('clevelandjewishnews.com', 'American Israelite'), ('crbcnews.com', 'Just Food'), ('dailynews.com', 'Red Bluff'),
    ('eurweb.com', 'Oakland Post'), ('nnpa.org', '.'), ('foxnews.com', 'Charleston Gazette'), ('kpbs.org', 'CALmatters'),
    ('laist.com', 'CALmatters'), ('smdp.com', 'CALmatters'), ('ksl.com', 'Philadelphia Tribune'), ('kvia.com', '^CNN'),
    ('abc12.com', '^CNN'), ('lasentinel.net', 'Precinct Reporter'), ('sfgate.com', 'San Francisco Chronicle'),
    ('thesunreporter.com', 'Los Angeles Sentinel'), ('calonews.com', 'Calaveras'), ('eastbaytimes.com', 'Mercury News'),
    ('centerforhealthjournalism.org', 'San Francisco Public Press')]
LINK_SKIP = collections.Counter(); LINK_SKIP_ROWS = []
def url_host(u):
    m = re.match(r'^https?://([^/?#]+)', s(u)); return re.sub(r'^(www\d?|m|amp|mobile)\.', '', m.group(1).lower()) if m else ''
def own_link(u, outlet):
    h = url_host(u)
    if not h: return 'not a URL'
    if NOT_OWN_HOST.search(h): return 'not publisher: ' + NOT_OWN_HOST.search(h).group(2)
    for dom, name in AGGREGATOR.items():
        if (h == dom or h.endswith('.' + dom)) and name not in outlet.lower(): return 'aggregator: ' + dom
    if WIRE_OUTLET.search(outlet): return 'wire outlet, partner site'
    for dom, pat in NOT_OWN_PAIR:
        if (h == dom or h.endswith('.' + dom)) and re.search(pat, outlet): return 'another outlet\'s site'
    return ''
def links_of(r):
    out, seen = [], set()
    def add(kind, u):
        if u and u not in seen: seen.add(u); out.append([kind, u])
    def skip(kind, u, why):
        LINK_SKIP[kind + ' | ' + why] += 1; LINK_SKIP_ROWS.append([r['Article ID'], r['Story ID'], r['Original or reprint'], s(r['Outlet']), kind, why, u])
    pu = s(r['Publisher link'])
    if pu:
        why = own_link(pu, s(r['Outlet']))
        if why: skip('Publisher link', pu, why)
        else: add('pub', pu)
    for kind, col, csl_col in (('nb', 'NewsBank article link', None), ('nbpa', 'NewsBank print article link', None),
                               ('nbpg', 'NewsBank print-page link', 'NewsBank print page article link via CA State Library'),
                               ('pq', 'ProQuest link', 'ProQuest via CA State Library')):
        raw = s(r[col]) if col in r else ''; sheet_csl = s(r[csl_col]) if csl_col and csl_col in r else ''
        u = csl_of(sheet_csl) or csl_of(raw)
        if u:
            add(kind, u)
            if not sheet_csl: LINK_SKIP[col + ' | listed as derived CSL link'] += 1
        elif raw: skip(col, raw, 'not via CA State Library')
        elif sheet_csl: skip(csl_col, sheet_csl, 'unrecognised CSL URL')
    return out
# ---- /LINKS-v1
'''

BD_EDITS = [
    ('insert link helpers after prec()',
     "    return 'day' if re.match(r'^\\d{4}-\\d{2}-\\d{2}$', d) else 'month' if re.match(r'^\\d{4}-\\d{2}$', d) else 'year' if d else 'day'\n",
     "    return 'day' if re.match(r'^\\d{4}-\\d{2}-\\d{2}$', d) else 'month' if re.match(r'^\\d{4}-\\d{2}$', d) else 'year' if d else 'day'\n" + BD_BLOCK),
    ('reprint objects carry lk',
     "        'hl': s(r['Headline']), 'src': s(r['Data Source'])})",
     "        'hl': s(r['Headline']), 'src': s(r['Data Source']), 'lk': links_of(r)})  # LINKS-v1"),
    ('original records carry lk',
     "        'pq': s(r['ProQuest link']) or o.get('pq', ''),\n",
     "        'pq': s(r['ProQuest link']) or o.get('pq', ''),\n        'lk': links_of(r),  # LINKS-v1\n"),
    ('link report',
     "json.dump(dict(report), open(f'{OUT}/report.json', 'w'), indent=1)",
     "report.update({'links ' + k: v for k, v in LINK_SKIP.items()})  # LINKS-v1\n"
     "report['links no_listed_link_originals'] = sum(1 for x in data if not x['lk'])\n"
     "import csv\n"
     "with open(f'{OUT}/links_not_listed.csv', 'w', newline='', encoding='utf-8') as f:\n"
     "    w = csv.writer(f); w.writerow(['Article ID', 'Story ID', 'Original or reprint', 'Outlet', 'Column', 'Why not listed', 'URL']); w.writerows(LINK_SKIP_ROWS)\n"
     "json.dump(dict(report), open(f'{OUT}/report.json', 'w'), indent=1)"),
]

# ---------------------------------------------------------------- tracker JS
JS_HELPERS = r'''/* LINKS-v1 (agent-links): every listed link is drawn like the ProQuest one: <a><b>Label ↗</b><span>detail</span></a>.
   Listed: NewsBank / ProQuest through the CA State Library, and the publisher's own link (build_data: r.lk / rep.lk as
   [kind, url]). Records without lk (finds from the Update button, live reprints) get the same kinds from link/plink/pq. */
const LINK_KIND = { pub: ['Publisher site', ''], nb: ['NewsBank via CA State Library', 'library card login'],
  nbpa: ['NewsBank print edition via CA State Library', 'library card login'], nbpg: ['NewsBank print page via CA State Library', 'library card login'],
  pq: ['ProQuest via CA State Library', 'library card login'] };
const CSL_PQ = 'https://castatelib.idm.oclc.org/login?url=', CSL_NB = 'https://infoweb-newsbank-com.castatelib.idm.oclc.org/';
function linksOf(x){
  if (!x) return [];
  if (Array.isArray(x.lk)) return x.lk.filter(p => Array.isArray(p) && LINK_KIND[p[0]] && /^https?:\/\//i.test(p[1] || ''));
  const out = [], seen = new Set(), add = (k, u) => { if (u && !seen.has(u)) { seen.add(u); out.push([k, u]); } };
  [x.plink, x.link, x.pq].forEach(u => { u = String(u || '').trim(); if (!/^https?:\/\//i.test(u)) return;
    if (/^https?:\/\/castatelib\.idm\.oclc\.org\/login\?url=https?:\/\/(www\.)?proquest\.com\//i.test(u)) add('pq', u);
    else if (/^https?:\/\/(www\.)?proquest\.com\//i.test(u)) add('pq', CSL_PQ + u);
    else if (/^https?:\/\/infoweb-newsbank-com\.castatelib\.idm\.oclc\.org\//i.test(u)) add('nb', u);
    else if (/^https?:\/\/infoweb\.newsbank\.com\//i.test(u)) add('nb', u.replace(/^https?:\/\/infoweb\.newsbank\.com\//i, CSL_NB));
    else if (!/^https?:\/\/([^\/]*\.)?(archive\.org|google\.[a-z.]+|oclc\.org|newsbank\.com)(\/|$)/i.test(u)) add('pub', u); });
  return out;
}
function linkA(p){ const [label, sub] = LINK_KIND[p[0]], h = (() => { try { return new URL(p[1]).hostname.replace(/^www\./,''); } catch(e){ return ''; } })();
  return `<a href="${esc(p[1])}" target="_blank" rel="noopener" data-lk="${p[0]}"><b>${label} ↗</b><span>${esc(sub || h)}</span></a>`; }
function repLinks(r){
  const rows = (Array.isArray(r.reps) ? r.reps : []).map(p => [p, linksOf(p)]).filter(x => x[1].length);
  if (!rows.length) return '';
  return `<details class="also replinks"${rows.length <= 5 ? ' open' : ''}><summary style="cursor:pointer"><b style="font-weight:600;color:var(--ink)">Reprint links</b> (${fmt(rows.length)})</summary>${rows.map(([p, ls]) => `<div class="dlinks" style="margin:6px 0 0"><span>${esc(p.outlet || '')}${p.date ? ' · ' + esc(p.date) : ''}</span>${ls.map(linkA).join('')}</div>`).join('')}</details>`;
}
/* /LINKS-v1 */
'''

JS_EDITS = [
    ('helpers + storyUrl = first listed link',
     "function storyUrl(r){ return r.lstat==='Search link only' ? (r.link || r.pq || '') : (r.plink || r.link); }",
     JS_HELPERS + "function storyUrl(r){ const l = linksOf(r)[0]; return l ? l[1] : ''; }  // LINKS-v1"),
    ('story panel: listed links',
     "  const links = [], seen = new Set(), add = (u, label) => { if (!u || seen.has(u) || /google\\.com\\/search/.test(u)) return; seen.add(u); links.push(`<a href=\"${esc(u)}\" target=\"_blank\" rel=\"noopener\"><b>${label}</b><span>${esc(host(u))}</span></a>`); };\n"
     "  if (r.lstat!=='Search link only') add(r.plink, r.lstat==='Syndicated copy' ? 'Read the reprint ↗' : `Read at ${esc(r.pub)} ↗`);\n"
     "  const pqG = r.pq || (/oclc/.test(r.link||'') ? (r.link.split('url=')[1]||'') : ''), pqL = pqG ? 'https://castatelib.idm.oclc.org/login?url=' + pqG : '';\n"
     "  if (!/proquest|oclc/.test(r.link||'')) add(r.link, 'Original link ↗');\n"
     "  if (pqG){ add(pqG, 'ProQuest ↗'); seen.add(pqL); links.push(`<a href=\"${esc(pqL)}\" target=\"_blank\" rel=\"noopener\"><b>ProQuest via CA State Library ↗</b><span>library card login</span></a>`); }\n",
     "  const links = linksOf(r).map(linkA);  // LINKS-v1\n"),
    ('story panel: reprint links under "Reprinted in"',
     "${alsoMissing(r)?`${alsoNames(r).length?'; ':''}${pl(alsoMissing(r),'other outlet')} not identified`:''}</div>`:''}\n",
     "${alsoMissing(r)?`${alsoNames(r).length?'; ':''}${pl(alsoMissing(r),'other outlet')} not identified`:''}</div>`:''}\n      ${repLinks(r)}\n"),
]

# ---------------------------------------------------------------- LINKS-v2 (agent-code, 2026-10-27; DECISIONS amends links
# scope): archive.org TV/video clips (Internet Archive TV News, archive.org/details/<CALLSIGN>_<YYYYMMDD>_<HHMMSS>_...) from
# the sheet are listed too, label "Internet Archive (TV clip)", same element. Other archive.org pages stay unlisted.
BD_EDITS_V2 = [
    ('archive TV pattern',
     "def links_of(r):\n",
     "ARCHIVE_TV = re.compile(r'^https?://(www\\.)?archive\\.org/(details|embed)/[A-Za-z0-9-]+_\\d{8}_\\d{6}', re.I)  # LINKS-v2\n"
     "def links_of(r):\n"),
    ('archive TV clips listed',
     "    pu = s(r['Publisher link'])\n    if pu:\n",
     "    pu = s(r['Publisher link'])\n    if pu and ARCHIVE_TV.match(pu): add('tv', pu)  # LINKS-v2: Internet Archive TV clip\n    elif pu:\n"),
]
JS_EDITS_V2 = [
    ('tv label',
     "  pq: ['ProQuest via CA State Library', 'library card login'] };\n",
     "  pq: ['ProQuest via CA State Library', 'library card login'], tv: ['Internet Archive (TV clip)', 'archive.org'] };  /* LINKS-v2 */\n"),
    ('tv from link fields',
     "    else if (!/^https?:\\/\\/([^\\/]*\\.)?(archive\\.org|google\\.[a-z.]+|oclc\\.org|newsbank\\.com)(\\/|$)/i.test(u)) add('pub', u); });\n",
     "    else if (/^https?:\\/\\/(www\\.)?archive\\.org\\/(details|embed)\\/[A-Za-z0-9-]+_\\d{8}_\\d{6}/i.test(u)) add('tv', u);  /* LINKS-v2 */\n"
     "    else if (!/^https?:\\/\\/([^\\/]*\\.)?(archive\\.org|google\\.[a-z.]+|oclc\\.org|newsbank\\.com)(\\/|$)/i.test(u)) add('pub', u); });\n"),
]


def amended(new, later):
    """F4: the text a v1 edit leaves once the later (v2) edits have amended it."""
    for _, o, n in later or ():
        if o in new and n not in new: new = new.replace(o, n)
    return new


def apply(text, edits, name, later=None):
    for label, old, new in edits:
        if new in text or (later and amended(new, later) in text):
            print(f'  [{name}] skip (already applied): {label}'); continue
        if label == 'insert link helpers after prec()' and '# ---- /LINKS-v1' in text:
            # F4: its own inserted block is there (whatever later edits changed inside it) -> never insert twice
            print(f'  [{name}] skip (already applied, block present): {label}'); continue
        n = text.count(old)
        if n == 0 and MARK in text and not name.endswith('v2'):
            # v1 already applied and a later edit (LINKS-v2) changed its text: nothing to do (idempotent re-run)
            print(f'  [{name}] skip (already applied, amended since): {label}'); continue
        if n != 1:
            raise SystemExit(f'[{name}] anchor for "{label}" found {n} times; not patching')
        text = text.replace(old, new); print(f'  [{name}] applied: {label}')
    return text


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) not in (2, 4): raise SystemExit(__doc__)
    js = apply(apply(open(a[0], encoding='utf-8').read(), JS_EDITS, 'js', JS_EDITS_V2), JS_EDITS_V2, 'js v2')
    bd = apply(apply(open(a[2], encoding='utf-8').read(), BD_EDITS, 'build_data', BD_EDITS_V2), BD_EDITS_V2, 'build_data v2') if len(a) == 4 else None
    open(a[1], 'w', encoding='utf-8').write(js)
    if bd is not None: open(a[3], 'w', encoding='utf-8').write(bd)
    print('ok')
