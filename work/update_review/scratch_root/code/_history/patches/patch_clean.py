"""agent-code (B2, 2026-10-27): merged cleaner wired into the tracker, the sheet task and the build.

Anchored, idempotent edits (marker CLEAN-v1). Each anchor must match exactly once; an edit already applied is skipped
(its marker is present); if any anchor is missing nothing is written and the script exits 1.

  python3 -I patch_clean.py --js build/js_merged.js --sheet-task code/sheet_task.py --prompt build/sheet_task_prompt_final.md \
      --assemble code/assemble.py --build-data code/build_data.py           (each in place; any subset)

What it does
  js_merged.js   CleanHTML (code/clean_html.js, re-inserted on every run so rule-engine fixes propagate) + loader of the
                 embedded rules block; the Update button cleans every fetched page with the same rules before keeping
                 it, skips finds whose only Gabriel mention is outside the article, never searches californiafiles.org;
                 saved copies dropped into the page are cleaned too, so the full-text search never indexes clutter.
  sheet_task.py  skips californiafiles.org finds and finds whose page names Gabriel only outside the article; cleans
                 every page before saving it to Tracker library/<year>/ (original to _original_html/<year>/); error
                 pages are not saved (File name 'RETRY – TinyFish', Saved Copy? = No); wire/PR finds get
                 'Press release' = Yes; counts.tracker_stories = Original rows minus press releases.
  prompt         saved pages -> Desktop/Tracker library; pipeline files clean_html.py + clean_rules.json; step 8 count
                 excludes press releases; nothing is deleted (files to remove go to Tracker library/_to_delete/).
  assemble.py    embeds blocks/cleanrules.json as <script id="cleanrules" type="application/json">.
  build_data.py  copies clean_rules.json (next to it) into the blocks folder as cleanrules.json.
"""
import argparse, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = 'CLEAN-v1'


class Patch:
    def __init__(self, path):
        self.path = path
        self.t = open(path, encoding='utf-8').read()
        self.orig = self.t
        self.bad = []
        self.done = []

    def rep(self, name, old, new, marker):
        """replace old (must occur once) with new, unless marker is already in the file"""
        if marker in self.t:
            self.done.append(name + ' (already)')
            return
        n = self.t.count(old)
        if n != 1:
            self.bad.append(f'{os.path.basename(self.path)}: anchor {name!r} found {n}x')
            return
        self.t = self.t.replace(old, new)
        self.done.append(name)

    def save(self):
        if self.bad:
            return False
        if self.t != self.orig:
            open(self.path, 'w', encoding='utf-8').write(self.t)
        return True


# ===================================================================================== tracker JS
JS_LOADER = r"""
/* CLEAN-v2 (agent-code, Sammy 2026-10-27): the tracker no longer cleans pages in the browser. The Update button stores what
   TinyFish returns; the sheet task cleans every page with code/clean_html.py when it saves it (and applies the skip rules:
   californiafiles.org, listing pages, other Gabriels, Gabriel only outside the article). tfClean() and cleanLocal() keep
   their call sites and pass pages through unchanged. */
const CLEAN_RULES = null;
function tfClean(html, url, outlet){ html = String(html || ''); return { html, text: tfStrip(html), outside: false, flags: [] }; }
function cleanLocal(id, html){ return html; }
/* CLEAN-v1 loader end */
"""


def js_block():
    src = open(os.path.join(HERE, 'clean_html.js'), encoding='utf-8').read().strip()
    assert src.startswith('/* CLEAN_HTML_JS') and src.endswith('/* CLEAN_HTML_JS end */'), 'unexpected clean_html.js shape'
    return src


def patch_js(path):
    p = Patch(path)
    # 1. CLEAN-v2: no browser cleaner. Any embedded CleanHTML block and the old loader are removed; the pass-through loader is
    #    inserted (once) before the Update section
    loader = JS_LOADER.strip()
    if '/* CLEAN_HTML_JS' in p.t:
        a = p.t.index('/* CLEAN_HTML_JS')
        z = p.t.index('/* CLEAN_HTML_JS end */') + len('/* CLEAN_HTML_JS end */')
        p.t = p.t[:a].rstrip('\n') + '\n' + p.t[z:].lstrip('\n')
        p.done.append('CleanHTML removed')
    if 'CLEAN-v2 (agent-code' in p.t:
        p.done.append('pass-through loader (already)')
    elif '/* CLEAN-v1 (agent-code): the cleaning rules' in p.t:
        a = p.t.index('/* CLEAN-v1 (agent-code): the cleaning rules')
        z = p.t.index('/* CLEAN-v1 loader end */') + len('/* CLEAN-v1 loader end */')
        p.t = p.t[:a] + loader + p.t[z:]
        p.done.append('loader -> pass-through')
    else:
        anchor = '/* ---------- update: TinyFish search and page fetch, Claude screening, run from the page ----------'
        n = p.t.count(anchor)
        if n != 1:
            p.bad.append(f'js: anchor loader found {n}x')
        else:
            p.t = p.t.replace(anchor, loader + '\n' + anchor)
            p.done.append('pass-through loader')
    # 2. never search californiafiles.org (DECISIONS 2026-10-27)
    p.rep('skip californiafiles', "const SKIP_HOSTS = /(^|\\.)(linkedin\\.com|",
          "const SKIP_HOSTS = /(^|\\.)(californiafiles\\.org|linkedin\\.com|", 'californiafiles\\.org|linkedin')
    # 3. step 2: every opened page is cleaned before it is read or kept
    p.rep('open pages', "          const html = String(r.text || ''), t = tfStrip(html);\n",
          "          const cl = tfClean(String(r.text || ''), r.final_url || c.url, c.site), html = cl.html, t = cl.text; /* CLEAN-v1 */\n"
          "          if (cl.outside) c.outside = true;\n", 'html = cl.html, t = cl.text; /* CLEAN-v1 */')
    # 4. skip finds whose only mention is outside the article
    p.rep('skip outside', "    list = list.filter(c => !c.published || c.published >= U.since || c.alltime);\n",
          "    // CLEAN-v1: Gabriel named only in reader comments, teasers or tags (on the cleaned page): skipped (DECISIONS 2026-10-27)\n"
          "    list.filter(c => c.outside).forEach(c => U.skipped.push({ c, why: 'Gabriel is named only outside the article (reader comments, teasers or tags).' }));\n"
          "    list = list.filter(c => !c.outside);\n"
          "    list = list.filter(c => !c.published || c.published >= U.since || c.alltime);\n", '// CLEAN-v1: Gabriel named only in reader comments')
    # 5. reprint check: the reprint's page, cleaned
    p.rep('reprint page', "const pg = pages.get(normU(p.link)), rt = pg ? tfStrip(String(pg.text || '')) : '';",
          "const pg = pages.get(normU(p.link)), pgc = pg ? tfClean(String(pg.text || ''), pg.final_url || p.link, p.outlet) : null, rt = pgc ? pgc.text : ''; /* CLEAN-v1 */",
          'pgc = pg ? tfClean(')
    p.rep('reprint page kept', "if (rt && pg) nr._page = { url: pg.final_url || p.link, title: String(pg.title || p.hl), clean: String(pg.text || '').slice(0, 400000) };",
          "if (rt && pg) nr._page = { url: pg.final_url || p.link, title: String(pg.title || p.hl), clean: pgc.html.slice(0, 400000) };",
          'clean: pgc.html.slice(0, 400000)')
    # 6. origin credit: the original's page, cleaned
    p.rep('origin page check', "const t0 = pg0 ? tfStrip(String(pg0.text || '')) : '';",
          "const t0 = pg0 ? tfClean(String(pg0.text || ''), pg0.final_url || o.url, '').text : ''; /* CLEAN-v1 */",
          "tfClean(String(pg0.text || ''), pg0.final_url || o.url, '').text")
    p.rep('origin page kept', "const html = pg && String(pg.text || ''), t = html ? tfStrip(html) : '';",
          "const pgc = pg ? tfClean(String(pg.text || ''), pg.final_url || o.url, name) : null, html = pgc ? pgc.html : '', t = html ? pgc.text : ''; /* CLEAN-v1 */",
          "tfClean(String(pg.text || ''), pg.final_url || o.url, name)")
    # 7. the article-scoped copy (photos) that goes to the sheet task is cleaned too
    p.rep('scoped copy', "scoped: (scoped.get(normU(r._page.url)) || '').slice(0, 400000)",
          "scoped: (scoped.get(normU(r._page.url)) ? tfClean(scoped.get(normU(r._page.url)), r._page.url, r.pub || r.outlet).html : '').slice(0, 400000)",
          "tfClean(scoped.get(normU(r._page.url))")
    # 8. copies dropped into the page and copies kept in this browser: cleaned before they are shown or searched
    p.rep('ingest', "local.set(id, txt); IDB.put(id, txt); indexHtml(id, txt);",
          "if (!isPdf) txt = cleanLocal(id, txt); /* CLEAN-v1 */\n    local.set(id, txt); IDB.put(id, txt); indexHtml(id, txt);",
          'if (!isPdf) txt = cleanLocal(id, txt);')
    p.rep('local copies', "if (byId.has(s) && (s === k || !local.has(s))) local.set(s, v);",
          "if (byId.has(s) && (s === k || !local.has(s))) local.set(s, cleanLocal(s, v)); /* CLEAN-v1 */",
          'local.set(s, cleanLocal(s, v))')
    return p


# ===================================================================================== sheet_task.py
ST_HEAD_OLD = "from openpyxl.styles import Font\n"
ST_HEAD_NEW = r'''from openpyxl.styles import Font

# CLEAN-v1 (agent-code, 2026-10-27): saved pages are cleaned with the library's rules before they are saved
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))   # -I drops the script dir
try:
    import clean_html as CH          # clean_html.py + clean_rules.json are published next to this script
    CH_ERR = ''
except Exception as _e:              # pages then wait in the shared store for the next run
    CH, CH_ERR = None, repr(_e)
RETRY = 'RETRY – TinyFish'
# DECISIONS 2026-10-27: California Files (californiafiles.org) is never added
SKIP_HOSTS = re.compile(r'(^|\.)californiafiles\.org$', re.I)
# DECISIONS 2026-10-27 "pure press releases": release wires and press-release pages -> 'Press release' = Yes
PR_HOSTS = re.compile(r'(^|\.)(prnewswire\.com|businesswire\.com|globenewswire\.com|einpresswire\.com|einnews\.com|prweb\.com|'
                      r'accesswire\.com|newswire\.com|publicnow\.com|targetednews\.com|contify\.com|m2\.com|asmdc\.org|'
                      r'assembly\.ca\.gov|cision\.com|prlog\.org|openpr\.com)$', re.I)
PR_OUTLETS = re.compile(r'^(the\s+)?(pr newswire|business wire|globe ?newswire|targeted news service|u\.?s\.? fed news|publicnow|'
                        r'enp newswire|m2 ?presswire|contify|ein presswire|accesswire|prweb|newswire\.com|cision)\b', re.I)


def host_of(u):
    return re.sub(r'^www\.', '', re.sub(r'^[a-z]+://', '', str(u or '').strip().lower()).split('/')[0].split(':')[0])


def is_press_release(vals):
    return bool(PR_HOSTS.search(host_of(vals.get('Publisher link'))) or PR_OUTLETS.match(str(vals.get('Outlet') or '').strip()))
'''

ST_INIT_OLD = "                    'edits_keep': [], 'reprint_counts': {}, 'pages': [], 'counts': {}}\n"
ST_INIT_NEW = ("                    'edits_keep': [], 'reprint_counts': {}, 'pages': [], 'counts': {},\n"
               "                    # CLEAN-v1: finds not added, pages not saved, pages kept as they were, press releases marked\n"
               "                    'skipped': [], 'pages_error': [], 'pages_skipped': [], 'pages_flagged': [], 'press_releases': []}\n"
               "        self.page_checks = {}     # CLEAN-v1: page doc id -> clean/check result (cached)\n")

ST_RUNS_OLD = """            before = dict(self.ids)
            added = []
            for kind in ('Original', 'Reprint'):"""
ST_RUNS_NEW = """            before = dict(self.ids)
            added = []
            rows = self.drop_skipped(rows, run_id)   # CLEAN-v1: californiafiles.org; Gabriel only outside the article
            for kind in ('Original', 'Reprint'):"""

ST_ADD_OLD = """        if kind == 'Original':
            vals['# of reprints'] = 0
"""
ST_ADD_NEW = """        if kind == 'Original':
            vals['# of reprints'] = 0
        if 'Press release' in self.s.col and is_press_release(vals):   # CLEAN-v1
            vals['Press release'] = 'Yes'
            self.res['press_releases'].append({'run': run_id, 'placeholder': ph_aid, 'aid': aid, 'outlet': vals.get('Outlet', ''),
                                               'link': vals.get('Publisher link', '')})
"""

ST_PAGES_NEW = r'''    # ---------- pages (CLEAN-v1) ----------
    def page_doc_id(self, obj):
        """the pages doc of a proposed row: keyed by the find's temporary code (Tracker story code) or a placeholder"""
        pages = self.db.get('pages') or {}
        keys = re.findall(r'jg-[0-9a-f]{6}', str(obj.get('Tracker story code') or '').lower())
        keys += [obj.get('Article ID') or '', obj.get('Story ID') or '']
        return next((k for k in keys if k and k in pages), None)

    def check_page(self, pid, row):
        """clean the page doc's copies (article-scoped first, then the full clean copy) and judge them:
        ok -> save the cleaned page; skip -> Gabriel only outside the article; error -> not saved (RETRY)"""
        if pid in self.page_checks:
            return self.page_checks[pid]
        p = (self.db.get('pages') or {}).get(pid) or {}
        best = None
        for key in ('scoped', 'clean'):
            body = p.get(key) or ''
            if not body.strip():
                continue
            page = self.page_html(p, body, row)
            res = CH.clean_page(page, p.get('url', '') or row.get('Publisher link', ''), row.get('Outlet', ''), row, mode='find')
            verdict, reason = CH.page_check(res, page)
            cand = {'verdict': verdict, 'reason': reason, 'source': key, 'page': page, 'html': res['html'],
                    'status': res['status'], 'flags': res['flags'], 'removed': len(res['removed']),
                    'words': [res.get('words_before'), res.get('words_after')], 'header': res['header']}
            rank = {'ok': 0, 'skip': 1, 'error': 2}[verdict]
            if best is None or rank < {'ok': 0, 'skip': 1, 'error': 2}[best['verdict']]:
                best = cand
            if verdict == 'ok':
                break
        self.page_checks[pid] = best
        return best

    def page_html(self, p, body, row):
        """the page as the library keeps it: title, a metadata header (Outlet · Date, URL, Saved date) and the body.
        The cleaner removes the header lines that match the sheet and keeps (and reports) the ones that don't."""
        import html as _h
        url = p.get('url', '') or row.get('Publisher link', '')
        hdr = [x for x in (f"{row.get('Outlet', '')} · {norm_val(row.get('Date', ''))[:10]}" if row.get('Outlet') and row.get('Date') else '',
                           url, f'Saved {self.today}') if x]
        div = '<div>' + '<br>'.join(_h.escape(x) for x in hdr) + '</div>'
        m = re.search(r'<body[^>]*>', body, re.I)
        if m:
            return body[:m.end()] + div + body[m.end():]
        return (f'<!doctype html><html><head><meta charset="utf-8"><title>{_h.escape(p.get("title", "") or row.get("Headline", "") or "")}</title></head>'
                f'<body>{div}{body}</body></html>')

    def drop_skipped(self, rows, run_id):
        """CLEAN-v1: rows not added. californiafiles.org finds; finds whose saved page names Gabriel only outside the
        article (reader comments, teasers, tags), checked on the cleaned page; and the reprint rows of such a story."""
        out, gone = [], set()
        for obj in rows:
            why = None
            if SKIP_HOSTS.search(host_of(obj.get('Publisher link'))) or norm_val(obj.get('Outlet')).lower() == 'california files':
                why = 'californiafiles.org: never added (DECISIONS 2026-10-27)'
            elif (obj.get('Original or reprint') or 'Original') == 'Original' and CH is not None:
                pid = self.page_doc_id(obj)
                chk = self.check_page(pid, obj) if pid else None
                if chk and chk['verdict'] == 'skip':
                    why = chk['reason']
            if why:
                self.res['skipped'].append({'run': run_id, 'placeholder': obj.get('Article ID', ''), 'story': obj.get('Story ID', ''),
                                            'code': str(obj.get('Tracker story code') or ''),
                                            'outlet': obj.get('Outlet', ''), 'link': obj.get('Publisher link', ''), 'why': why})
                if (obj.get('Original or reprint') or 'Original') == 'Original' and obj.get('Story ID'):
                    gone.add(obj['Story ID'])
                continue
            out.append(obj)
        keep = []
        for obj in out:
            if obj.get('Original or reprint') == 'Reprint' and obj.get('Story ID') in gone:
                self.res['skipped'].append({'run': run_id, 'placeholder': obj.get('Article ID', ''), 'story': obj.get('Story ID', ''),
                                            'outlet': obj.get('Outlet', ''), 'link': obj.get('Publisher link', ''),
                                            'why': 'reprint of a skipped story'})
                continue
            keep.append(obj)
        return keep

    def apply_pages(self, pages_dir):
        """Each waiting page: cleaned with the library's rules (clean_html.py), saved as <year>/<file> (the library
        folder Desktop/Tracker library/<year>/) with the original as _original_html/<year>/<file>. Error pages (not the
        article, no body, no Gabriel, paywall/login/404) are not saved: File name 'RETRY – TinyFish', Saved Copy? = No.
        A page naming Gabriel only outside the article is not saved (its row was skipped when the find came in)."""
        import os
        if not (self.db.get('pages') or {}):
            return
        if CH is None:
            self.res['pages_note'] = f'clean_html.py could not be loaded ({CH_ERR}); pages left waiting'
            return
        for pid, p in (self.db.get('pages') or {}).items():
            p = p or {}
            target = self.norm_id(self.ids.get(pid, pid))
            aid = None
            if target in self.s.rows:
                aid = target
            else:
                r = self.s.original_row(self.resolve_sid(target))
                if r:
                    aid = self.s.get(r, 'Article ID')
            if not aid:
                if not any(pid in (x.get('story'), x.get('placeholder')) or pid in x.get('code', '') for x in self.res['skipped']):
                    self.res['unknown_story'].append({'collection': 'pages', 'id': pid})
                continue
            if not ((p.get('scoped') or '').strip() or (p.get('clean') or '').strip()):
                continue
            r = self.s.rows[aid]
            row = {c: norm_val(self.s.get(r, c)) for c in ('Outlet', 'Date', 'Headline', 'Publisher link', 'NewsBank article link', 'ProQuest link')}
            chk = self.check_page(pid, row)
            if self.s.new_scheme:   # library naming: ws<Article ID><o|r>-s<Story ID>.html (DECISIONS 2026-10-27)
                suf = {'Original': 'o', 'Reprint': 'r'}.get(self.s.get(r, 'Original or reprint'), '')
                st = str(self.s.get(r, 'Story ID') or '').strip()
                fname = f'ws{aid}{suf}' + (f'-{st}' if st else '') + '.html'
            else:
                fname = f'{aid}.html'
            d = norm_val(self.s.get(r, 'Date'))
            year = d[:4] if re.match(r'^\d{4}', d) else str(self.s.get(r, 'Year') or '')[:4] or self.today[:4]
            info = {'page': pid, 'aid': aid, 'file': f'{year}/{fname}', 'url': p.get('url', ''), 'source': chk['source'],
                    'status': chk['status'], 'flags': chk['flags'], 'removed': chk['removed'], 'words': chk['words'],
                    'header_conflicts': chk['header']['conflicts']}
            if chk['verdict'] == 'skip':
                self.res['pages_skipped'].append(dict(info, why=chk['reason']))
                continue
            if chk['verdict'] == 'error':
                self.fill(r, 'File name', RETRY, 'pages', pid)
                self.fill(r, 'Saved Copy?', 'No', 'pages', pid)
                self.res['pages_error'].append(dict(info, why=chk['reason']))
                continue
            if pages_dir:
                os.makedirs(os.path.join(pages_dir, year), exist_ok=True)
                with open(os.path.join(pages_dir, year, fname), 'w', encoding='utf-8') as f:
                    f.write(chk['html'])
                if chk['html'] != chk['page']:   # the original, as the library keeps it (Tracker library/_original_html/)
                    os.makedirs(os.path.join(pages_dir, '_original_html', year), exist_ok=True)
                    with open(os.path.join(pages_dir, '_original_html', year, fname), 'w', encoding='utf-8') as f:
                        f.write(chk['page'])
                    info['original'] = f'_original_html/{year}/{fname}'
            if 'big_removal' in chk['flags'] or 'long_block' in chk['flags']:
                self.res['pages_flagged'].append(info)
            self.fill(r, 'Saved Copy?', 'Yes', 'pages', pid)
            self.fill(r, 'File type', 'HTML', 'pages', pid)
            self.fill(r, 'File name', fname, 'pages', pid)
            self.res['pages'].append(info)

    # ---------- derived ----------
'''

ST_MAIN_OLD = "    res['verify'] = verify(a.xlsx, a.out, res)\n"
ST_MAIN_NEW = ("    # CLEAN-v1: the tracker leaves press releases out (build_data.py), so step 8 compares with this count\n"
               "    res['counts']['tracker_stories'] = sum(1 for r in range(2, sheet.last_row + 1)\n"
               "                                           if sheet.get(r, 'Original or reprint') == 'Original'\n"
               "                                           and str(sheet.get(r, 'Press release') or '').strip().lower() != 'yes')\n"
               "    res['counts'].update({'skipped': len(res['skipped']), 'pages_error': len(res['pages_error']),\n"
               "                          'pages_skipped': len(res['pages_skipped']), 'pages_flagged': len(res['pages_flagged']),\n"
               "                          'press_releases': len(res['press_releases'])})\n"
               "    res['verify'] = verify(a.xlsx, a.out, res)\n")

ST_LINE_OLD = """                         + (f", {len(res['removals_requested'])} removal requests left for Sammy" if res['removals_requested'] else '')"""
ST_LINE_NEW = """                         + (f", {len(res['removals_requested'])} removal requests left for Sammy" if res['removals_requested'] else '')
                         + (f", {len(res['skipped'])} finds skipped (California Files or Gabriel only outside the article)" if res['skipped'] else '')
                         + (f", {len(res['pages_error'])} pages not saved (RETRY – TinyFish)" if res['pages_error'] else '')"""


def patch_sheet_task(path):
    p = Patch(path)
    p.rep('imports', ST_HEAD_OLD, ST_HEAD_NEW, 'CLEAN-v1 (agent-code, 2026-10-27): saved pages')
    p.rep('init', ST_INIT_OLD, ST_INIT_NEW, 'self.page_checks = {}')
    p.rep('runs', ST_RUNS_OLD, ST_RUNS_NEW, 'rows = self.drop_skipped(rows, run_id)')
    p.rep('press release', ST_ADD_OLD, ST_ADD_NEW, "is_press_release(vals):   # CLEAN-v1")
    # pages of new stories are keyed by the find's temporary code (Tracker story code): resolvable in the same run
    p.rep('codes', "        self.s.rows[aid] = r\n        self.s.story_rows.setdefault(sid, []).append(r)\n",
          "        self.s.rows[aid] = r\n        self.s.story_rows.setdefault(sid, []).append(r)\n"
          "        for code in re.findall(r'jg-[0-9a-f]{6}', str(obj.get('Tracker story code') or '').lower()):   # CLEAN-v1\n"
          "            self.s.codes.setdefault(code, sid)\n", "self.s.codes.setdefault(code, sid)")
    # replace the whole old apply_pages method
    if '# ---------- pages (CLEAN-v1) ----------' in p.t:
        p.done.append('pages (already)')
    else:
        a = p.t.find('    # ---------- pages ----------\n')
        z = p.t.find('    # ---------- derived ----------\n')
        if a < 0 or z < 0 or p.t.count('    # ---------- pages ----------\n') != 1:
            p.bad.append('sheet_task: pages section anchors missing')
        else:
            p.t = p.t[:a] + ST_PAGES_NEW + p.t[z + len('    # ---------- derived ----------\n'):]
            p.done.append('pages')
    p.rep('counts', ST_MAIN_OLD, ST_MAIN_NEW, "res['counts']['tracker_stories']")
    p.rep('sheet line', ST_LINE_OLD, ST_LINE_NEW, 'finds skipped (California Files or Gabriel only outside the article)')
    return p


# ===================================================================================== prompt
PROMPT_EDITS = [
    ('saved folder',
     "- Saved page folder (on the Mac): `~/Documents/Gabriel press PDFs/Saved pages (TinyFish)/`\n",
     "- Saved page folder (on the Mac): the library, `~/Desktop/Tracker library/<year>/`. Every page is cleaned before it is saved (clean_html.py, the same rules as the rest of the library); the page as fetched goes to `~/Desktop/Tracker library/_original_html/<year>/` under the same name. Add-only: never overwrite or delete a file there.\n"
     "- Files that must go (an error copy, a deleted story, a California Files page) are never deleted: move them to `~/Desktop/Tracker library/_to_delete/` under the same subfolder (e.g. `_to_delete/2026/…`).\n",
     'Tracker library/<year>/`. Every page is cleaned'),
    ('pipeline files',
     "  - `pipeline/legacy_index.html` (the old tracker, used for carried-over fields)\n",
     "  - `pipeline/legacy_index.html` (the old tracker, used for carried-over fields)\n"
     "  - `pipeline/clean_html.py` and `pipeline/clean_rules.json` (the page cleaner and its rules; keep them in the same folder as sheet_task.py and build_data.py)\n"
     "  - `pipeline/authorsplit.py` (build_data.py imports it)\n"
     "  - `pipeline/clean_playbook.md` (how the cleaning rules work, for anyone adding a rule)\n",
     'pipeline/clean_rules.json'),
    ('ids file names',
     "Saved pages are named like the library: `ws<Article ID><o|r>-s<Story ID>.html` (e.g. `ws09762o-s04297.html`).",
     "Saved pages are named like the library: `ws<Article ID><o|r>-s<Story ID>.html` (e.g. `ws09762o-s04297.html`) and saved in `Tracker library/<year>/` (year of the story's date).",
     'saved in `Tracker library/<year>/` (year'),
    ('step 4 checks',
     "   - `Originals` = the number of Original rows.\n",
     "   - `Originals` = the number of Original rows.\n"
     "   - `result.skipped` lists finds that were not added: californiafiles.org pages (never added) and finds whose page names Gabriel only outside the article (reader comments, teasers, tags), with their reprint rows. `result.pages_error` lists pages that were not saved because they are not the article (no body, no Gabriel, paywall, login or error page); their row's File name is `RETRY – TinyFish` and Saved Copy? is No. Report both counts in `sheet.line` (sheet_task.py's line already does).\n",
     'result.skipped` lists finds that were not added'),
    ('step 5 pages',
     "   - Commit each file in `pages/Saved pages (TinyFish)/` (named `ws<Article ID><o|r>-s<Story ID>.html`, as listed in `result.pages[].file`) to the saved page folder.\n",
     "   - Commit each cleaned page `pages/<year>/<file>` (listed in `result.pages[].file`) to `~/Desktop/Tracker library/<year>/<file>`, and its original `pages/_original_html/<year>/<file>` (`result.pages[].original`, when present) to `~/Desktop/Tracker library/_original_html/<year>/<file>`. Add-only: if a file of that name is already there, don't overwrite it; list it in the run's review instead. Pages in `result.pages_error` and `result.pages_skipped` are not saved anywhere.\n",
     'pages/_original_html/<year>/<file>'),
    ('step 6 skipped',
     "   - Delete each pages doc listed in `result.pages` whose file was committed.\n",
     "   - Delete each pages doc listed in `result.pages` whose file was committed, and each pages doc in `result.pages_error` and `result.pages_skipped` (they are reported, not retried from the old copy).\n"
     "   - Add `result.skipped`, `result.pages_error` and `result.pages_flagged` to the run doc's `review` (first 50 of each) so Sammy sees what was left out and why.\n",
     'result.pages_skipped` (they are reported'),
    ('step 7 articles',
     "   - `articles/<year>.json` keyed by Story ID (`sNNNNN`), with `articles/manifest.json` mapping Story ID → year file;\n",
     "   - `articles/<year>.json` keyed by Story ID (`sNNNNN`), with `articles/manifest.json` mapping Story ID → year file; the copy is the CLEANED page that was saved to the library (never the raw TinyFish copy), so the full-text search only sees article text;\n",
     'the copy is the CLEANED page that was saved'),
    ('step 8 count',
     "Then read it back and check that the `data` block's story count equals the Original row count.",
     "Then read it back and check that the `data` block's story count equals `result.counts.tracker_stories` (Original rows minus rows with Press release = Yes: the tracker leaves press releases out).",
     'result.counts.tracker_stories'),
    ('rules',
     "3. **Never delete rows.** Removal requests are reported for Sammy, not executed.\n",
     "3. **Never delete rows or files.** Removal requests are reported for Sammy, not executed. A file that must go is moved to `~/Desktop/Tracker library/_to_delete/` (same subfolder), never deleted.\n",
     'Never delete rows or files.'),
]


def patch_prompt(path):
    p = Patch(path)
    for name, old, new, marker in PROMPT_EDITS:
        p.rep(name, old, new, marker)
    return p


# ===================================================================================== assemble / build_data
def patch_assemble(path):
    p = Patch(path)
    p.rep('drop old blocks', "for n in ('rows', 'idmap', 'covcols'):\n    while True:",
          "for n in ('rows', 'idmap', 'covcols', 'cleanrules'):   # CLEAN-v1\n    while True:", "'covcols', 'cleanrules'):   # CLEAN-v1")
    p.rep('blocks', "for n, v in blocks.items(): json.loads(v)\n",
          "import os   # CLEAN-v1: the page-cleaning rules (blocks/cleanrules.json, from build_data.py) ride along\n"
          "if os.path.exists(f'{BLK}/cleanrules.json'): blocks['cleanrules'] = open(f'{BLK}/cleanrules.json', encoding='utf-8').read()\n"
          "for n, v in blocks.items(): json.loads(v)\n", "blocks['cleanrules'] = open(")
    p.rep('extra', "extra = ''.join(f'\\n<script id=\"{n}\" type=\"application/json\">{esc(blocks[n])}</script>' for n in ('rows', 'idmap', 'covcols'))",
          "extra = ''.join(f'\\n<script id=\"{n}\" type=\"application/json\">{esc(blocks[n])}</script>' for n in ('rows', 'idmap', 'covcols', 'cleanrules') if n in blocks)",
          "for n in ('rows', 'idmap', 'covcols', 'cleanrules') if n in blocks)")
    return p


def patch_build_data(path):
    p = Patch(path)
    p.rep('cleanrules', "dump('idmap', idmap); dump('covcols', covcols)\n",
          "dump('idmap', idmap); dump('covcols', covcols)\n"
          "# CLEAN-v1: the page-cleaning rules (clean_rules.json next to this script) go into the page as a block\n"
          "_cr = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clean_rules.json')\n"
          "if os.path.exists(_cr):\n"
          "    json.dump(json.load(open(_cr, encoding='utf-8')), open(f'{OUT}/cleanrules.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))\n",
          "_cr = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clean_rules.json')")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description='CLEAN-v1 patches')
    ap.add_argument('--js'); ap.add_argument('--sheet-task'); ap.add_argument('--prompt')
    ap.add_argument('--assemble'); ap.add_argument('--build-data')
    a = ap.parse_args(argv)
    ps = []
    if a.js: ps.append(patch_js(a.js))
    if a.sheet_task: ps.append(patch_sheet_task(a.sheet_task))
    if a.prompt: ps.append(patch_prompt(a.prompt))
    if a.assemble: ps.append(patch_assemble(a.assemble))
    if a.build_data: ps.append(patch_build_data(a.build_data))
    bad = [b for p in ps for b in p.bad]
    if bad:
        print('NOT applied (nothing written):', *bad, sep='\n  ')
        return 1
    for p in ps:
        p.save()
        print(os.path.basename(p.path) + ':', ', '.join(p.done))
    return 0


if __name__ == '__main__':
    sys.exit(main())
