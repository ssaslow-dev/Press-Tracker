#!/usr/bin/env python3
"""RELRULE-v1 + RELCHECK-v2 (agent-relrule, 2026-10-27). Sammy: "Use the same standard for determine if something is a
release as you do for a reprint." Idempotent (marker per target); runs after patch_releases.py (step 4i) as apply_all 4k.
  python3 -I patch_relrule.py [--js build/js_merged.js] [--sheet-task code/sheet_task.py] [--prompt code/sheet_task_prompt.md]
                              [--views build/insights]
sheet_task.py (RELCHECK-v2): new official releases are matched to Coverage rows by the reprint string-of-text rule
  (release_rule.py over reprint_rule.py) against the release text, rows dated 1 day before to 30 days after, instead of the
  headline match; new finds of the run are tested the same way against every in-scope release on the tab; rows with no saved
  text are listed as releases_untestable and never marked. Release texts: release_texts.json (pipeline file, appended).
  Row text: the run's saved page / a staged library file (--library, list from --release-candidates) / the tracker copy for
  Originals. Marks are blanks-only; the tab's In tracker / Tracker release ID / Coverage stories linked follow.
Tracker JS (RELRULE-v1): Clips gets a "Press release" filter (rail section, "Release copies") and a box above the results that
  lists official releases whose title matches the search (or, with the filter on, the releases that have copies), each opening
  its entry in the Press releases view - release copies are not tracker stories, so searching a release title used to find 0.
Press releases view: the method note says copies are matched by the text rule."""
import argparse, os
MARK_JS, MARK_ST, MARK_PR, MARK_VIEW = '/* RELRULE-v1 tracker */', '# RELCHECK-v2 sheet_task', 'RELCHECK-v2', 'RELRULE-v1'

JS_FN = r'''/* RELRULE-v1 tracker */
/* official releases from the "ins-release_pickup" block, for the Clips search / filter box (release copies are not stories) */
var REL_LIST = null;
function relList(){ if (!REL_LIST){ REL_LIST = [];
  try { const el = document.getElementById('ins-release_pickup'), b = el ? JSON.parse(el.textContent) : null;
    ((b && b.rel) || []).forEach(t => REL_LIST.push({ key: t[0], date: t[1] || '', title: t[3] || '', runs: (t[8] || []).length, f: fold(String(t[3] || '')) })); } catch(e){} }
  return REL_LIST; }
function relHits(){
  if (!(S.flag === 'relcopy' || S.q)) return '';
  const canGo = typeof INS !== 'undefined' && INS.views && INS.views.has('release_pickup');
  let L = relList().filter(x => (!S.d0 || x.date >= S.d0) && (!S.d1 || x.date <= S.d1));
  L = S.q ? L.filter(x => x.f.includes(S.q) && (S.flag !== 'relcopy' || x.runs)) : L.filter(x => x.runs);
  if (!L.length) return '';
  const top = L.slice(0, 8), runs = L.reduce((a, x) => a + x.runs, 0);
  const head = S.q ? `${pl(L.length, 'official press release')} match “${esc(S.q)}”` : `${pl(runs, 'press-release copy', 'press-release copies')} of ${pl(L.length, 'release')}`;
  const go = (k, v, t) => canGo ? `<button type="button" class="linkbtn" data-ins-go="release_pickup" data-ins-k="${k}" data-ins-v="${esc(v)}">${t}</button>` : t;
  return `<div class="relhits" role="note"><b>${head}</b> <span class="note">Copies of his releases (same text, by the reprint rule) aren’t counted as stories; each release is in Press releases.</span><ul>`
    + top.map(x => `<li>${go('id', x.key, esc(x.title))} <span class="note">· ${esc(x.date || 'no date')} · ${x.runs ? pl(x.runs, 'copy', 'copies') : 'no pickup found'}</span></li>`).join('')
    + `</ul>${L.length > top.length ? `<div class="note">and ${fmt(L.length - top.length)} more ${go('pick', S.q ? '' : 'yes', 'in Press releases')}</div>` : ''}</div>`;
}
document.addEventListener('click', e => { const b = e.target.closest('[data-relf]'); if (!b) return; S.flag = b.dataset.relf; S.page = 0; render(); });
try { document.head.insertAdjacentHTML('beforeend', '<style>.relhits{flex-basis:100%;width:100%;margin:6px 0 2px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--panel-2);font-size:12.5px;color:var(--ink-2)}.relhits b{color:var(--ink);font-weight:600}.relhits ul{margin:4px 0 0;padding-left:18px}.relhits li{margin:2px 0}</style>'); } catch(e){}
/* /RELRULE-v1 tracker */
'''

JS_R = [
 ("const searchStr = r => fold([", JS_FN + "const searchStr = r => fold(["),
 ("  nopick: { chip:'Reprints', label:'No reprints', f: r => !r.pick },\n",
  "  nopick: { chip:'Reprints', label:'No reprints', f: r => !r.pick },\n"
  "  relcopy: { chip:'Press release', label:'Press release copies', f: r => !!relOf(r.id) },   /* RELRULE-v1 */\n"),
 ("['no','Not yet']].map(([k,l])=>`<button data-saved=\"${k}\" aria-pressed=\"${S.saved===k}\">${l}</button>`).join('')}</div></div></details>`;\n",
  "['no','Not yet']].map(([k,l])=>`<button data-saved=\"${k}\" aria-pressed=\"${S.saved===k}\">${l}</button>`).join('')}</div></div></details>`;\n"
  "  html += `<details class=\"facet\" data-facet=\"relf\" ${S.openFacets.has('relf')?'open':''}><summary>Press release<small>${S.flag==='relcopy'?'1 on':''}</small></summary><div class=\"body\"><div class=\"hint\">Copies of his official releases, matched by the same text rule as reprints. Most are kept out of the story list; the releases themselves are listed above the results.</div><div class=\"seg\" role=\"group\" aria-label=\"Press release\">${[['','Any'],['relcopy','Release copies']].map(([k,l])=>`<button data-relf=\"${k}\" aria-pressed=\"${(S.flag==='relcopy'?'relcopy':'')===k}\">${l}</button>`).join('')}</div></div></details>`;   /* RELRULE-v1 */\n"),
 ("data-rm=\"${esc(k)}\" data-v=\"${esc(v)}\">${IC.xs}</button></span>`).join('');\n}\n",
  "data-rm=\"${esc(k)}\" data-v=\"${esc(v)}\">${IC.xs}</button></span>`).join('') + relHits();   /* RELRULE-v1 */\n}\n"),
]

ST_IMPORT = '''try:
    import release_rule as REL       # RELCHECK-v2: the release text rule (release_rule.py next to this script)
except Exception as _e:
    REL = None
'''

ST_METHODS = r'''
    # RELCHECK-v2 sheet_task: the release text rule (Sammy 2026-10-27) - a row carries an official release only when its saved
    # text passes the reprint string-of-text rule against the release text; no text = untestable (listed, never marked)
    def row_versions(self, r):
        import os
        vs = []
        year = str(self.s.get(r, 'Date') or '')[:4]
        for col in ('File name', 'File name 2'):
            fn = str(self.s.get(r, col) or '').strip()
            if not fn or '–' in fn or fn.startswith('articles/') or not re.search(r'\.(html?|pdf)$', fn, re.I):
                continue
            for base in (getattr(self, 'pages_dir', None), getattr(self, 'library_dir', None)):
                p = os.path.join(base, year, fn) if base else ''
                if p and os.path.exists(p):
                    vs += REL.file_versions(p)
                    break
        if not REL.usable([v for v in vs if v.get('label') != 'excerpt']) and self.s.get(r, 'Original or reprint') == 'Original':
            h = self.copy_html(str(self.s.get(r, 'Story ID') or '').strip())
            if h:
                vs += REL.page_versions(h)
        return vs   # EXCERPT-v1: REL.match filters short normal versions itself and keeps excerpt versions

    def release_rows(self, rel):
        """Coverage rows (1 day before .. 30 days after the release) whose text passes against this release ->
        [(row, verdict)]; prefilter: headline words overlap, or an Original with a tracker copy"""
        rr = REL.releases({rel['url']: rel})
        hits = []
        for r in range(2, self.s.last_row + 1):
            if not REL.in_window(self.s.get(r, 'Date'), rel['date']):
                continue
            hl = str(self.s.get(r, 'Headline') or '')
            over = REL.title_near(hl, rel['title'])
            if not (over or (self.s.get(r, 'Original or reprint') == 'Original' and self.copies_dir) or r > self.first_new_row):
                continue
            m = REL.match(self.row_versions(r), rr)
            if m == 'untestable':
                if over:
                    self.res['releases_untestable'].append({'aid': self.s.get(r, 'Article ID'), 'outlet': self.s.get(r, 'Outlet'),
                                                            'release': rel['title'][:200], 'url': rel['url'], 'why': 'no saved text'})
                continue
            if m:
                hits.append((r, m['verdict']))
        return hits

    def _rel_tab(self):
        wb = self.s.wb
        if 'Press releases' not in wb.sheetnames:
            return None, None
        ws = wb['Press releases']
        return ws, {c.value: c.column for c in ws[1] if c.value}

    def _rel_mark(self, r, url, title, v, ws, H, tr):
        sid = str(self.s.get(r, 'Story ID') or '').strip()
        if self.fill(r, 'Press release', 'Yes', 'release text rule', url) != 'written':
            return
        self.res['releases_flagged'].append({'aid': self.s.get(r, 'Article ID'), 'story': sid, 'release': title[:200], 'url': url,
                                             'mode': v['mode'], 'conf': v['conf'], 'pct': REL.pct(v)})
        if ws is None or tr is None:
            return
        ids = [x.strip() for x in str(ws.cell(tr, H['Tracker release ID']).value or '').split(';') if x.strip()]
        if sid and sid not in ids:
            ids.append(sid)
        ws.cell(tr, H['In tracker']).value = 'Yes'
        ws.cell(tr, H['Tracker release ID']).value = '; '.join(ids) or None
        n = ws.cell(tr, H['Coverage stories linked']).value
        ws.cell(tr, H['Coverage stories linked']).value = (int(n) if str(n or '').strip().isdigit() else 0) + 1

    def apply_release_finds(self):
        """new rows of this run whose saved page passes the release text rule against an in-scope official release (tab,
        dated 1 day after .. 30 days before the row) -> Press release = Yes (blanks only) + the tab's link columns"""
        if REL is None or RR is None or not getattr(self, 'release_texts', None) or self.s.last_row <= self.first_new_row:
            return
        texts = REL.load_texts(self.release_texts)
        ws, H = self._rel_tab()
        if ws is None or not texts:
            return
        scope = {}
        for tr in range(2, ws.max_row + 1):
            u = str(ws.cell(tr, H['URL']).value or '').strip()
            src, d = str(ws.cell(tr, H['Source']).value or '').lower(), str(ws.cell(tr, H['Date']).value or '')[:10]
            if 'caucus' in src and 'office' not in src and d < '2020-11-18':
                continue
            if u in texts:
                scope[u] = tr
        rels = REL.releases(texts, set(scope))
        for r in range(self.first_new_row + 1, self.s.last_row + 1):
            cand = [x for x in rels if REL.in_window(self.s.get(r, 'Date'), x['date'])]
            if not cand:
                continue
            m = REL.match(self.row_versions(r), cand)
            if m == 'untestable':
                hl = str(self.s.get(r, 'Headline') or '')
                x = next((x for x in cand if REL.title_near(hl, x['title'])), None)
                if x:
                    self.res['releases_untestable'].append({'aid': self.s.get(r, 'Article ID'), 'outlet': self.s.get(r, 'Outlet'),
                                                            'release': x['title'][:200], 'url': x['url'], 'why': 'no saved text'})
                continue
            if m:
                x = m['release']
                self._rel_mark(r, x['url'], x['title'], m['verdict'], ws, H, scope.get(x['url']))

'''

ST_R = [
 ("try:\n    from authorsplit import parse_byline as _parse_byline", ST_IMPORT + "try:\n    from authorsplit import parse_byline as _parse_byline"),
 # apply_releases: the headline match -> the text rule
 ("        nh = lambda t: ' '.join(re.findall(r'[a-z0-9]+', str(t or '').lower().replace('’', \"'\")))\n"
  "        cov = []\n"
  "        for r in range(2, self.s.last_row + 1):\n"
  "            h = nh(self.s.get(r, 'Headline'))\n"
  "            if h:\n"
  "                cov.append((r, h, str(self.s.get(r, 'Date') or '')[:10]))\n",
  "        # RELCHECK-v2 sheet_task: rows are matched by the release text rule (release_rule.py), not by headline\n"
  "        texts = REL.load_texts(self.release_texts) if (REL is not None and getattr(self, 'release_texts', None)) else {}\n"
  "        n_texts = len(texts)\n"),
 ("            nt = nh(title); hits = []\n"
  "            for r, h, rd in cov:\n"
  "                if h == nt or (len(h) > 40 and (h in nt or nt in h)):\n"
  "                    try:\n"
  "                        ok = bool(re.match(r'\\d{4}-\\d\\d-\\d\\d$', rd)) and d and abs((datetime.date.fromisoformat(rd) - datetime.date.fromisoformat(d)).days) <= 30\n"
  "                    except ValueError:\n"
  "                        ok = False\n"
  "                    if ok:\n"
  "                        hits.append(r)\n"
  "            sids = []\n"
  "            for r in hits:\n"
  "                sid = str(self.s.get(r, 'Story ID') or '').strip()\n"
  "                if sid and sid not in sids:\n"
  "                    sids.append(sid)\n"
  "                if self.fill(r, 'Press release', 'Yes', 'release check', url) == 'written':\n"
  "                    self.res['releases_flagged'].append({'aid': self.s.get(r, 'Article ID'), 'story': sid, 'release': title[:200], 'url': url})\n",
  "            rel = {'url': url, 'date': d, 'title': title, 'dek': str(x.get('dek', '')).strip(), 'body': body,\n"
  "                   'src': 'caucus' if caucus else 'office'}\n"
  "            if body:\n"
  "                texts[url] = rel\n"
  "            if REL is None or RR is None or not body:\n"
  "                hv = []\n"
  "                self.res['releases_skipped'].append({'url': url, 'why': 'release text rule not run (' + ('no release text' if not body else 'release_rule.py not loaded') + '): no Coverage rows matched'})\n"
  "            else:\n"
  "                hv = self.release_rows(rel)\n"
  "            hits = [r for r, _ in hv]\n"
  "            sids = []\n"
  "            for r, v in hv:\n"
  "                sid = str(self.s.get(r, 'Story ID') or '').strip()\n"
  "                if sid and sid not in sids:\n"
  "                    sids.append(sid)\n"
  "                if self.fill(r, 'Press release', 'Yes', 'release text rule', url) == 'written':\n"
  "                    self.res['releases_flagged'].append({'aid': self.s.get(r, 'Article ID'), 'story': sid, 'release': title[:200], 'url': url,\n"
  "                                                         'mode': v['mode'], 'conf': v['conf'], 'pct': REL.pct(v)})\n"),
 ("        if ws.auto_filter.ref:\n            from openpyxl.utils import get_column_letter\n            ws.auto_filter.ref = f'A1:{get_column_letter(ws.max_column)}{ws.max_row}'\n\n    @staticmethod\n    def _rel_body",
  "        if ws.auto_filter.ref:\n            from openpyxl.utils import get_column_letter\n            ws.auto_filter.ref = f'A1:{get_column_letter(ws.max_column)}{ws.max_row}'\n"
  "        if REL is not None and getattr(self, 'release_texts', None) and len(texts) > n_texts:   # RELCHECK-v2: new release texts\n"
  "            REL.save_texts(self.release_texts, texts)\n"
  "            self.res['release_texts_changed'] = len(texts) - n_texts\n"
  + ST_METHODS + "    @staticmethod\n    def _rel_body"),
 ("    def run(self, pages_dir=None):\n        self.norm_preloaded()\n",
  "    def run(self, pages_dir=None):\n        self.pages_dir = pages_dir   # RELCHECK-v2\n        self.norm_preloaded()\n"),
 ("        self.apply_releases()   # RELCHECK-v1\n",
  "        self.apply_releases()   # RELCHECK-v1\n        self.apply_release_finds()   # RELCHECK-v2\n"),
 ("        self.res.update({'releases_new': [], 'releases_flagged': [], 'releases_skipped': []})   # RELCHECK-v1\n",
  "        self.res.update({'releases_new': [], 'releases_flagged': [], 'releases_skipped': []})   # RELCHECK-v1\n"
  "        self.res.update({'releases_untestable': []})   # RELCHECK-v2\n"
  "        self.release_texts = self.library_dir = self.pages_dir = None   # RELCHECK-v2\n"),
 ("    ap.add_argument('--bills', help='gabriel_bills_leginfo.json to append new bills to (AUTO-v1; the pipeline copy)')\n",
  "    ap.add_argument('--bills', help='gabriel_bills_leginfo.json to append new bills to (AUTO-v1; the pipeline copy)')\n"
  "    ap.add_argument('--release-texts', help='release_texts.json (RELCHECK-v2; the pipeline copy, new releases appended)')\n"
  "    ap.add_argument('--library', help='folder with staged library files <year>/<file> for the release text rule (RELCHECK-v2)')\n"
  "    ap.add_argument('--release-candidates', action='store_true', help='print the library files (<year>/<file>) to stage for --library and exit (RELCHECK-v2)')\n"),
 ("    if not (a.xlsx and a.out and a.result):\n",
  "    if a.release_candidates:   # RELCHECK-v2: rows near a queued release whose saved copy the text rule needs\n"
  "        if not a.xlsx:\n"
  "            sys.exit('--release-candidates needs --xlsx')\n"
  "        print(json.dumps(release_candidates(db, Sheet(a.xlsx))))\n"
  "        return 0\n"
  "    if not (a.xlsx and a.out and a.result):\n"),
 ("    task.copies_dir, task.bills_path = a.copies, a.bills   # AUTO-v1\n",
  "    task.copies_dir, task.bills_path = a.copies, a.bills   # AUTO-v1\n"
  "    task.release_texts, task.library_dir = a.release_texts, a.library   # RELCHECK-v2\n"),
 ("          + (f\" ({len(res['releases_flagged'])} Coverage rows marked Press release = Yes, see review)\" if res['releases_flagged'] else ''))\n",
  "          + (f\" ({len(res['releases_flagged'])} Coverage rows marked Press release = Yes, see review)\" if res['releases_flagged'] else '')\n"
  "          + (f\", {len(res['releases_untestable'])} rows near a release with no saved text to test (see review)\" if res.get('releases_untestable') else ''))   # RELCHECK-v2\n"),
 ("\n\ndef main(argv=None):\n",
  "\n\ndef release_candidates(db, sheet):   # RELCHECK-v2\n"
  "    \"\"\"library files (<year>/<file>) of Coverage rows dated 1 day before .. 30 days after a queued new release whose headline\n"
  "    overlaps it: stage these into --library so the text rule can read them\"\"\"\n"
  "    if REL is None or RR is None:\n"
  "        return []\n"
  "    rels = []\n"
  "    for rid, run in sorted((db.get('runs') or {}).items()):\n"
  "        if ((run or {}).get('sheet') or {}).get('at'):\n"
  "            continue\n"
  "        rels += [x for x in (run or {}).get('releases_new') or [] if isinstance(x, dict)]\n"
  "    out = []\n"
  "    for r in range(2, sheet.last_row + 1):\n"
  "        hl, d = str(sheet.get(r, 'Headline') or ''), sheet.get(r, 'Date')\n"
  "        if not any(REL.in_window(d, str(x.get('date', ''))[:10]) and REL.title_near(hl, str(x.get('title', ''))) for x in rels):\n"
  "            continue\n"
  "        for col in ('File name', 'File name 2'):\n"
  "            fn = str(sheet.get(r, col) or '').strip()\n"
  "            if fn and re.search(r'\\.(html?|pdf)$', fn, re.I):\n"
  "                p = str(d or '')[:4] + '/' + fn\n"
  "                if p not in out:\n"
  "                    out.append(p)\n"
  "    return out\n"
  "\n\ndef main(argv=None):\n"),
]
ST_R = [(a, b.replace("# RELCHECK-v2 sheet_task: rows are matched", MARK_ST + ": rows are matched")) for a, b in ST_R]

PR_R = [
 ("`reprint_rule.py`, `gabriel_bills_leginfo.json`, `insights_assemble.py`",
  "`reprint_rule.py`, `release_rule.py`, `release_texts.json`, `gabriel_bills_leginfo.json`, `insights_assemble.py`"),
 ("sheet_task.py appends them to the workbook's \"Press releases\" tab and marks matching Coverage rows Press release = Yes (blanks only). Jewish Caucus releases count only from his chair tenure (2020-11-18).",
  "sheet_task.py appends them to the workbook's \"Press releases\" tab and marks Coverage rows Press release = Yes (blanks only) only when their saved text passes the reprint string-of-text rule against the release text (RELCHECK-v2, release_rule.py; rows dated 1 day before to 30 days after; new finds are tested against every in-scope release too). Rows with no saved text are listed as releases_untestable, never marked. Jewish Caucus releases count only from his chair tenure (2020-11-18)."),
 ("   (add `--idmap idmap.json` from the page's `<script id=\"idmap\">` if you have it).",
  "   Add `--release-texts release_texts.json` always. If a run has `releases_new`, first run `python3 -I sheet_task.py --db db.json --xlsx in.xlsx --release-candidates`, stage each listed `<year>/<file>` from `Tracker library/` into `library/<year>/<file>`, and add `--library library` (RELCHECK-v2).\n"
  "   (add `--idmap idmap.json` from the page's `<script id=\"idmap\">` if you have it)."),
 ("releases_new, releases_flagged, releases_skipped.", "releases_new, releases_flagged, releases_skipped, releases_untestable."),
 ("If `result.bills_new` is not empty, also publish `gabriel_bills_leginfo.json` as `pipeline/gabriel_bills_leginfo.json`.",
  "If `result.bills_new` is not empty, also publish `gabriel_bills_leginfo.json` as `pipeline/gabriel_bills_leginfo.json`. If `result.release_texts_changed`, also publish `release_texts.json` as `pipeline/release_texts.json` (RELCHECK-v2)."),
]

# RELRULE-v1b: release titles in the Clips box stay left-aligned on phones (phone CSS centers buttons)
MARK_JS_B = 'RELRULE-v1b'
JS_B = [(".relhits li{margin:2px 0}</style>", ".relhits li{margin:2px 0}.relhits .linkbtn{display:inline;text-align:left;padding:0;font-size:inherit}/* RELRULE-v1b */</style>")]
MARK_JS_D = 'RELRULE-v1d'   # buttons are always inline-block: no list bullets, a rule on the left instead
JS_D = [("/* RELRULE-v1c */</style>", "/* RELRULE-v1c */.relhits ul{list-style:none;padding-left:0}.relhits li{padding-left:9px;border-left:2px solid var(--line);margin:5px 0}.relhits li .linkbtn{vertical-align:top}/* RELRULE-v1d */</style>")]
MARK_JS_C = 'RELRULE-v1c'
JS_C = [("/* RELRULE-v1b */</style>", "/* RELRULE-v1b */.relhits li .linkbtn{display:inline!important;text-align:left!important;justify-content:flex-start!important;white-space:normal}/* RELRULE-v1c */</style>")]

# SIDMAP-v1 (agent-relrule for agent-reorg's finding, 2026-10-27): the button's rebuild passes sid_map.json to build_data.py,
# so the 101 legacy jg- codes of removed duplicates stay in idmap and old deep links keep working after a button run
MARK_SID = 'SIDMAP-v1'
SID_R = [
 ("`release_rule.py`, `release_texts.json`, `gabriel_bills_leginfo.json`",
  "`release_rule.py`, `release_texts.json`, `sid_map.json`, `gabriel_bills_leginfo.json`"),
 ("6. **Rebuild.** `python3 -I build_data.py \"<committed workbook copy>\" legacy_index.html blocks/`;",
  "6. **Rebuild.** `python3 -I build_data.py \"<committed workbook copy>\" legacy_index.html blocks/ sid_map.json` (SIDMAP-v1: always pass sid_map.json, or 101 legacy deep links drop out of idmap);"),
]

VIEW_R = [
 ("Which outlets ran a release comes from sheet rows marked Press release = Yes. ",
  "Which outlets ran a release comes from sheet rows marked Press release = Yes whose saved text passes the same test as reprints against the release’s own text: runs of 25 or more identical words covering 90% of both (RELRULE-v1). "),
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
            raise SystemExit(f'{path}: anchor found {n}x: {a[:80]}')
        s = s.replace(a, b)
    if mark not in s:
        s = s + ('' if s.endswith('\n') else '\n') + ('<!-- ' + mark + ' -->\n' if path.endswith('.md') else '')
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'


def _apply_view(views):
    p = os.path.join(views or '', 'release_pickup.js')
    if not views or not os.path.exists(p):
        return 'skipped (no file)'
    s = open(p, encoding='utf-8').read()
    if 'RELRULE-v1' in s:
        return 'unchanged'
    for a, b in VIEW_R:
        if s.count(a) != 1:
            raise SystemExit(f'{p}: anchor found {s.count(a)}x: {a[:80]}')
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)
    return 'patched'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--js'); ap.add_argument('--sheet-task'); ap.add_argument('--prompt'); ap.add_argument('--views')
    a = ap.parse_args()
    if a.js: print('js:', _apply(a.js, JS_R, MARK_JS))
    if a.js: print('js b:', _apply(a.js, JS_B, MARK_JS_B))
    if a.js: print('js c:', _apply(a.js, JS_C, MARK_JS_C))
    if a.js: print('js d:', _apply(a.js, JS_D, MARK_JS_D))
    if a.sheet_task: print('sheet_task:', _apply(a.sheet_task, ST_R, MARK_ST))
    if a.prompt: print('prompt:', _apply(a.prompt, PR_R, MARK_PR))
    if a.prompt: print('prompt sid_map:', _apply(a.prompt, SID_R, MARK_SID))
    if a.views: print('view:', _apply_view(a.views))
