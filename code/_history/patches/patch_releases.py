#!/usr/bin/env python3
"""RELEASES-v2 + RELCHECK-v1 (agent-insights, 2026-10-27; Sammy: official press releases plugged in everywhere, and the
Update button looks for new ones). Idempotent (marker per target).
  python3 -I patch_releases.py [--js build/js_merged.js] [--sheet-task code/sheet_task.py] [--prompt code/sheet_task_prompt.md]
Tracker JS (RELEASES-v2): the release data of the "ins-release_pickup" block (built by release_pickup_data.py from the
  workbook's "Press releases" tab + Press release = Yes rows) is read once: a story that carries a release gets a
  "From press release" badge (Clips list, Home lists), a "From press release: <title>" line with the official link + copy
  icon in the story panel, the release title in its search text, and "Press release" / "Press release link" columns in the
  CSV download.
Tracker JS (RELCHECK-v1): the Update button (find mode) reads the first listing page of gabriel.asmdc.org/press-releases
  and of the Jewish Caucus news page (Press Release items only) through TinyFish (live, ttl 0), newest first, stopping at the
  first URL already on the tab or at a date older than the tab's newest for that site; a second page only when the whole
  first page is new. Each new release page is fetched once (body text, at most 5 a run) and saved in the run doc as
  releases_new. Jewish Caucus releases count only from his chair tenure (2020-11-18; Sammy 2026-10-27 "2 no").
sheet_task.py (RELCHECK-v1): releases_new rows are appended to the "Press releases" tab (same 16 columns, filled from the
  release page, blanks where the page doesn't say), matched to Coverage by headline (same rule as the audit: normalized
  headline equal, or one containing the other above 40 characters, run dated within 30 days); a matched Coverage row with a
  blank "Press release" gets "Yes" (blanks-only fill, green, listed for review); the tab row gets In tracker / Tracker
  release ID / Coverage stories linked."""
import argparse, os, sys
MARK_JS, MARK_ST, MARK_PR = '/* RELEASES-v2 tracker */', '# RELCHECK-v1 sheet_task', 'RELCHECK-v1'

REL_JS = r'''/* RELEASES-v2 tracker */
/* official press releases (block "ins-release_pickup", read once): Story ID -> {title, url, date, key} for stories that carry one */
var REL_BY_SID = null;
function relOf(id){
  if (!REL_BY_SID){ REL_BY_SID = new Map();
    try { const el = document.getElementById('ins-release_pickup'), b = el ? JSON.parse(el.textContent) : null;
      ((b && b.rel) || []).forEach(t => (t[7] || []).forEach(s => { if (!REL_BY_SID.has(s)) REL_BY_SID.set(s, { key: t[0], date: t[1], title: t[3], url: t[9] || '' }); })); } catch(e){} }
  return REL_BY_SID.get(id) || null;
}
function relLine(r){ const x = relOf(r.id); if (!x) return '';
  return `<div class="relline"><b>From press release:</b> ${x.url ? `<span class="lkw">${typeof cpBtn === 'function' ? cpBtn(x.url) : ''}<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.title)} ↗</a></span>` : esc(x.title) + ' <span class="note">(not posted officially)</span>'}${x.date ? ` <span class="note">· ${esc(x.date)}</span>` : ''}</div>`; }
try { document.head.insertAdjacentHTML('beforeend', '<style>.relline{font-size:12.5px;color:var(--ink-2)}.relline b{font-weight:600;color:var(--ink)}.badge.rel{border-color:transparent;background:var(--panel-2);color:var(--ink-2)}</style>'); } catch(e){}
/* /RELEASES-v2 tracker */
'''

RELCHECK_JS = r'''
/* RELCHECK-v1 (Sammy 2026-10-27): look for new official press releases on each Update. Listing pages through TinyFish
   (live), newest first; stop at the first URL already on the "Press releases" tab or at a date older than the tab's newest
   for that site; page 2 only when page 1 is all new; each new release page fetched once (at most 5 a run). Jewish Caucus
   releases count only from his chair tenure (2020-11-18). The sheet task writes them to the tab and matches them to Coverage. */
const REL_TENURE = '2020-11-18';
const REL_SITES = [
  { src: 'office', label: "Gabriel's office (gabriel.asmdc.org)", base: 'https://gabriel.asmdc.org', list: n => 'https://gabriel.asmdc.org/press-releases' + (n ? '?page=' + n : ''), sel: '.view-press-releases .view-content' },
  { src: 'caucus', label: 'California Legislative Jewish Caucus', base: 'https://jewishcaucus.legislature.ca.gov', list: n => 'https://jewishcaucus.legislature.ca.gov/news' + (n ? '?page=' + n : ''), sel: '.view-newsroom .view-content' }];
function relKnown(){ const urls = new Set(), newest = { office: '', caucus: '' };
  try { const b = JSON.parse((document.getElementById('ins-release_pickup') || {}).textContent || 'null');
    ((b && b.rel) || []).forEach(t => { if (!t[9]) return; urls.add(String(t[9]).replace(/\/+$/, '').toLowerCase()); const s = /jewishcaucus/.test(t[9]) ? 'caucus' : 'office'; if (t[1] > newest[s]) newest[s] = t[1]; });
    ((b && b.known) || []).forEach(u => urls.add(String(u).replace(/\/+$/, '').toLowerCase())); } catch(e){}
  return { urls, newest, ok: urls.size > 0 }; }
function relDate(t){ const d = Date.parse(String(t || '').replace(/^[A-Za-z]+,\s*/, '')); return isNaN(d) ? '' : new Date(d - new Date(d).getTimezoneOffset() * 6e4).toISOString().slice(0, 10); }
function relParseList(html, site){
  const doc = new DOMParser().parseFromString(String(html || ''), 'text/html'), out = [];
  (site.src === 'office' ? doc.querySelectorAll('article') : doc.querySelectorAll('.views-row')).forEach(n => {
    if (site.src === 'caucus'){ const cat = n.querySelector('.views-field-field-news-category'); if (!cat || !/press release/i.test(cat.textContent)) return; }
    const a = n.querySelector(site.src === 'office' ? 'h2 a[href]' : 'h3 a[href]'), tm = n.querySelector('time');
    if (!a || !tm) return;
    const href = a.getAttribute('href'), url = /^https?:/.test(href) ? href : site.base + href;
    const sub = n.querySelector('.field--name-field-subtitle');
    out.push({ url, title: a.textContent.replace(/\s+/g, ' ').trim(), date: relDate(tm.textContent) || String(tm.getAttribute('datetime') || '').slice(0, 10), dek: sub ? sub.textContent.replace(/\s+/g, ' ').trim() : '' });
  });
  return out;
}
async function relFetch(mcp, url, sel, fmt){
  const p = tfPayload(await tfCall(mcp, 'fetch_content', { urls: [url], format: fmt || 'html', links: false, include_selectors: [sel], ttl: 0, per_url_timeout_ms: 90000, image_links: false, iframe_links: false, page_metadata: false }));
  const r = ((p && p.results) || [])[0]; if (r && r.text) return String(r.text);
  throw new Error(((p && p.errors) || []).map(e => String((e && (e.error || e.code || e.message)) || '')).join(' ') || 'no page');
}
async function releaseCheck(mcp){
  U.newrels = []; U.relcheck = '';
  const K = relKnown(); if (!K.ok){ U.relcheck = 'release check skipped (no release list in this build)'; return; }
  const found = [], notes = [];
  try {
    for (const site of REL_SITES){
      let stop = false;
      for (let pg = 0; pg < 2 && !stop && !U.ctl.signal.aborted; pg++){
        const items = relParseList(await relFetch(mcp, site.list(pg), site.sel), site);
        if (!items.length){ notes.push(site.src + ': listing not read'); break; }
        for (const it of items){
          if (K.urls.has(it.url.replace(/\/+$/, '').toLowerCase()) || (it.date && K.newest[site.src] && it.date < K.newest[site.src])){ stop = true; break; }
          if (site.src === 'caucus' && it.date && it.date < REL_TENURE) continue;   // before his chair tenure: out of scope
          if (!found.some(x => x.url === it.url)) found.push(Object.assign({ src: site.src, source: site.label }, it));
        }
      }
    }
    for (const r of found.slice(0, 5)){   // the release page itself: body text for the sheet task
      try { r.text = (await relFetch(mcp, r.url, 'main', 'markdown')).slice(0, 12000); } catch(e){ r.text = ''; r.err = VS(String(e && e.message || e), 200); }
    }
    U.newrels = found.slice(0, 5);
    U.relcheck = `releases: ${found.length ? pl(found.length, 'new official release') + (found.length > 5 ? ' (5 saved this run)' : '') : 'none new'}` + (notes.length ? ' (' + notes.join('; ') + ')' : '');
  } catch(e){ U.relcheck = 'release check skipped'; try { console.warn('release check skipped', e); } catch(_){} }
}
/* /RELCHECK-v1 */
'''

JS_R = [
 ("const searchStr = r => fold([r.hl, r.hl_en, r.outlet,", REL_JS + "const searchStr = r => fold([(relOf(r.id) || {}).title, r.hl, r.hl_en, r.outlet,"),
 ("  if (rated(r)) b += B('tone', 'tone', r.tone, `<i style=\"background:${colorFor('tone',r.tone)}\"></i>${esc(r.tone)}`, 'Tone toward Gabriel');\n",
  "  if (rated(r)) b += B('tone', 'tone', r.tone, `<i style=\"background:${colorFor('tone',r.tone)}\"></i>${esc(r.tone)}`, 'Tone toward Gabriel');\n"
  "  if (relOf(r.id)) b += `<span class=\"badge rel\" title=\"${esc('Carries an official press release: ' + relOf(r.id).title)}\">From press release</span>`;   /* RELEASES-v2 */\n"),
 ("      ${insEntry(r)}\n", "      ${insEntry(r)}\n      ${relLine(r)}\n"),
 ("['Link',r=>r.plink||r.link],['ProQuest link','pq']];",
  "['Link',r=>r.plink||r.link],['ProQuest link','pq'],['Press release',r=>(relOf(r.id)||{}).title||''],['Press release link',r=>(relOf(r.id)||{}).url||'']];   /* RELEASES-v2 */"),
 ("/* TOKENS-v1 tracker (agent-code, 2026-10-27, Sammy's token cuts)", RELCHECK_JS + "/* TOKENS-v1 tracker (agent-code, 2026-10-27, Sammy's token cuts)"),
 ("    if (!U.ctl.signal.aborted){ U.step = 'Checking leginfo for new bills of his'; drawProg(); await leginfoCheck(mcp); }   /* AUTO-v1 */\n",
  "    if (!U.ctl.signal.aborted){ U.step = 'Checking leginfo for new bills of his'; drawProg(); await leginfoCheck(mcp); }   /* AUTO-v1 */\n"
  "    if (!U.ctl.signal.aborted){ U.step = 'Checking his and the Jewish Caucus’s sites for new press releases'; drawProg(); await releaseCheck(mcp); }   /* RELCHECK-v1 */\n"),
 ("      bills_new: mode === 'find' ? (U.newbills || []).slice(0, 50) : [], leginfo: mode === 'find' ? VS(U.leginfo || '', 300) : '',   /* AUTO-v1 */\n",
  "      bills_new: mode === 'find' ? (U.newbills || []).slice(0, 50) : [], leginfo: mode === 'find' ? VS(U.leginfo || '', 300) : '',   /* AUTO-v1 */\n"
  "      releases_new: mode === 'find' ? (U.newrels || []).slice(0, 5) : [], relcheck: mode === 'find' ? VS(U.relcheck || '', 300) : '',   /* RELCHECK-v1 */\n"),
 ("    if (mode === 'find' && !RA.added.length && !RA.reprints && !(U.newbills || []).length){",
  "    if (mode === 'find' && !RA.added.length && !RA.reprints && !(U.newbills || []).length && !(U.newrels || []).length){   /* RELCHECK-v1 */"),
]

ST_METHOD = r'''
    # RELCHECK-v1 sheet_task: official releases the Update button found (run docs' releases_new) -> "Press releases" tab
    def apply_releases(self):
        new, seen = [], set()
        for rid, run in sorted((self.db.get('runs') or {}).items()):
            if ((run or {}).get('sheet') or {}).get('at'):
                continue
            for x in (run or {}).get('releases_new') or []:
                if isinstance(x, dict) and str(x.get('url', '')).startswith('http') and x['url'] not in seen:
                    seen.add(x['url']); new.append(x)
        if not new:
            return
        wb = self.s.wb
        if 'Press releases' not in wb.sheetnames:
            self.res['releases_skipped'].append({'why': 'no "Press releases" tab', 'n': len(new)}); return
        ws = wb['Press releases']; H = {c.value: c.column for c in ws[1] if c.value}
        need = ['Date', 'Title', 'Subtitle/dek', 'Source', 'URL', 'Release type', 'Bills mentioned', 'Issue', 'Gabriel quoted',
                'Co-issuers / other members named', 'Contact', 'Word count', 'In tracker', 'Tracker release ID',
                'Coverage stories linked', 'Note']
        if any(c not in H for c in need):
            self.res['releases_skipped'].append({'why': 'tab columns differ', 'n': len(new)}); return
        have = {str(ws.cell(r, H['URL']).value or '').strip().rstrip('/').lower() for r in range(2, ws.max_row + 1)}
        nh = lambda t: ' '.join(re.findall(r'[a-z0-9]+', str(t or '').lower().replace('’', "'")))
        cov = []
        for r in range(2, self.s.last_row + 1):
            h = nh(self.s.get(r, 'Headline'))
            if h:
                cov.append((r, h, str(self.s.get(r, 'Date') or '')[:10]))
        for x in sorted(new, key=lambda x: (str(x.get('date', '')), x['url'])):
            url, d, title = x['url'].strip(), str(x.get('date', ''))[:10], str(x.get('title', '')).strip()
            if url.rstrip('/').lower() in have:
                continue
            caucus = x.get('src') == 'caucus' or 'jewishcaucus' in url
            if caucus and d and d < '2020-11-18':
                self.res['releases_skipped'].append({'url': url, 'why': 'Jewish Caucus release before his chair tenure'}); continue
            body = self._rel_body(str(x.get('text') or ''), title)
            nt = nh(title); hits = []
            for r, h, rd in cov:
                if h == nt or (len(h) > 40 and (h in nt or nt in h)):
                    try:
                        ok = bool(re.match(r'\d{4}-\d\d-\d\d$', rd)) and d and abs((datetime.date.fromisoformat(rd) - datetime.date.fromisoformat(d)).days) <= 30
                    except ValueError:
                        ok = False
                    if ok:
                        hits.append(r)
            sids = []
            for r in hits:
                sid = str(self.s.get(r, 'Story ID') or '').strip()
                if sid and sid not in sids:
                    sids.append(sid)
                if self.fill(r, 'Press release', 'Yes', 'release check', url) == 'written':
                    self.res['releases_flagged'].append({'aid': self.s.get(r, 'Article ID'), 'story': sid, 'release': title[:200], 'url': url})
            bills = []
            for m in re.finditer(r'\b(AB|SB|ACA|SCA|ACR|SCR|AJR|SJR|HR|SR)\s*-?\s*(\d{1,4})\b', body):
                b = f'{m.group(1)} {int(m.group(2))}'
                if b not in bills:
                    bills.append(b)
            quoted = 'Yes' if re.search(r'(said|says|stated)\s+(Assembly(member| Budget Chair)?|Assemblymember|Budget Chair|Asm\.?)?\s*(Jesse\s+)?Gabriel|Gabriel\s+(said|says|stated)', body) else ''
            cm = re.search(r'Contact:?\s*([^\n]{3,160})', body)
            vals = {'Date': d, 'Title': title, 'Subtitle/dek': str(x.get('dek', '')).strip(), 'Source': x.get('source') or ('California Legislative Jewish Caucus' if caucus else "Gabriel's office (gabriel.asmdc.org)"),
                    'URL': url, 'Release type': '', 'Bills mentioned': '; '.join(bills), 'Issue': '', 'Gabriel quoted': quoted,
                    'Co-issuers / other members named': '', 'Contact': cm.group(1).strip() if cm else '', 'Word count': len(body.split()) if body else '',
                    'In tracker': 'Yes' if sids else 'No', 'Tracker release ID': '; '.join(sids), 'Coverage stories linked': len(hits) if hits else '',
                    'Note': f"Added by the Update button's release check ({self.today})" + ('' if body else '; release page not read')}
            r = ws.max_row + 1
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c)._style = copy.copy(ws.cell(r - 1, c)._style)
            for k, v in vals.items():
                ws.cell(r, H[k]).value = v if v != '' else None
            ws.cell(r, H['URL']).hyperlink = url
            have.add(url.rstrip('/').lower())
            self.res['releases_new'].append({'date': d, 'title': title[:200], 'url': url, 'in_tracker': bool(sids), 'stories': sids})
        if ws.auto_filter.ref:
            from openpyxl.utils import get_column_letter
            ws.auto_filter.ref = f'A1:{get_column_letter(ws.max_column)}{ws.max_row}'

    @staticmethod
    def _rel_body(text, title):
        """the release text from the page's markdown: from the title on, without the site's sidebar"""
        t = text
        i = t.find(title[:40]) if title else -1
        if i >= 0:
            t = t[i + len(title):]
        for stop in ('\n## Search', '\n## Connect', '\n## Offices', '\n#### Pagination', '\nShare this'):
            j = t.find(stop)
            if j > 0:
                t = t[:j]
        return re.sub(r'[#*_>\[\]]+', ' ', t).strip()

'''

ST_R = [
 ("    # ---------- derived ----------\n", ST_METHOD + "    # ---------- derived ----------\n"),
 ("        self.apply_bills()   # AUTO-v1\n", "        self.apply_bills()   # AUTO-v1\n        self.apply_releases()   # RELCHECK-v1\n"),
 ("                    'date_fixes': [], 'date_review': []}   # F7-v1\n",
  "                    'date_fixes': [], 'date_review': []}   # F7-v1\n"
  "        self.res.update({'releases_new': [], 'releases_flagged': [], 'releases_skipped': []})   # RELCHECK-v1\n"),
 ("           'bills': sum(1 for r in runs if (r or {}).get('bills_new') and not ((r or {}).get('sheet') or {}).get('at')),\n",
  "           'bills': sum(1 for r in runs if (r or {}).get('bills_new') and not ((r or {}).get('sheet') or {}).get('at')),\n"
  "           'releases': sum(1 for r in runs if (r or {}).get('releases_new') and not ((r or {}).get('sheet') or {}).get('at')),   # RELCHECK-v1\n"),
 ("          + (f\", {len(res['bills_new'])} new bills from leginfo\" if res['bills_new'] else ''))\n",
  "          + (f\", {len(res['bills_new'])} new bills from leginfo\" if res['bills_new'] else '')\n"
  "          + (f\", {len(res['releases_new'])} new official press releases on the Press releases tab\" if res['releases_new'] else '')   # RELCHECK-v1\n"
  "          + (f\" ({len(res['releases_flagged'])} Coverage rows marked Press release = Yes, see review)\" if res['releases_flagged'] else ''))\n"),
]

PR_R = [
 ("- Pipeline files (Artifact `read` with `path`, all into one folder): `pipeline/sheet_task.py`, `build_data.py`, `assemble.py`, `tracker.js`, `legacy_index.html`, `clean_html.py`, `clean_rules.json`, `authorsplit.py`, `author_canon.csv`, `reprint_rule.py`, `gabriel_bills_leginfo.json`.",
  "- Pipeline files (Artifact `read` with `path`, all into one folder): `pipeline/sheet_task.py`, `build_data.py`, `assemble.py`, `tracker.js`, `legacy_index.html`, `clean_html.py`, `clean_rules.json`, `authorsplit.py`, `author_canon.csv`, `reprint_rule.py`, `gabriel_bills_leginfo.json`, `insights_assemble.py`, `insights_data.py`, and every file in `pipeline/insights/` (into `insights/` next to them).\n"
  "- Official press releases (RELCHECK-v1): the Update button finds new releases on gabriel.asmdc.org and the Jewish Caucus site and queues them in its run doc (`releases_new`); sheet_task.py appends them to the workbook's \"Press releases\" tab and marks matching Coverage rows Press release = Yes (blanks only). Jewish Caucus releases count only from his chair tenure (2020-11-18)."),
 ("   - Run doc `review` (first 50 each): conflicts, removals_requested, duplicates, unknown_story, skipped, pages_error, pages_flagged, reprint_check, reach, gabriel_unclear, date_fixes, date_review.",
  "   - Run doc `review` (first 50 each): conflicts, removals_requested, duplicates, unknown_story, skipped, pages_error, pages_flagged, reprint_check, reach, gabriel_unclear, date_fixes, date_review, releases_new, releases_flagged, releases_skipped."),
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
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--js'); ap.add_argument('--sheet-task'); ap.add_argument('--prompt')
    a = ap.parse_args()
    if a.js: print('js:', _apply(a.js, JS_R, MARK_JS))
    if a.sheet_task: print('sheet_task:', _apply(a.sheet_task, ST_R, MARK_ST))
    if a.prompt: print('prompt:', _apply(a.prompt, PR_R, MARK_PR))
