#!/usr/bin/env python3
"""RELCOPIES-v1 (agent-relcopies2, 2026-10-28; Sammy: "download press releases and add them to the press release tab pages as
if they were articles", "create unique file name codes and press release codes in the press release tab in the sheet as
well" (prefix "pr"), "for press releases keep the link to the website and add the file as a preview as if its an article").
Idempotent (one marker per target); apply_all step 4o, after 4l (tabs).

  python3 -I patch_relcopies.py --root L

Targets (each skipped when its marker is already there):
  code/make_copies.py + code/make_copies_clean.py  --releases DIR: cleaned release copies <year>/prNNNNN.html (work/html_clean/
        press_releases) -> articles/releases.json (split releases-2.json… above the shard size), manifest key = Release ID.
        Both files get the same edit, so apply_all step 3 (make_copies_clean.py == make_copies.py) still sees them equal.
  code/build_data.py        rows.next.pr = next free Release ID number (max prNNNNN on the "Press releases" tab + 1).
  build/insights/release_pickup_data.py  ins-release_pickup gets a 12th column "prid" (the tab's Release ID; "" for the 5
        releases with no official posting).
  build/tabs/releases_data.py  tab-releases r[url] gets [6] Release ID, [7] File name when Saved Copy? = Yes.
  build/tabs/releases.js    release pages at #press-releases/<prid> (old date-title slugs redirect to it); the page keeps the
        official link (copy icon left) and, when the release has a saved copy, a "Saved copy" row that opens it in the story
        panel's article viewer (ctx.openSaved: side panel, full-page toggle, Gabriel highlighting) - no copy: link only;
        Release ID searchable and in the CSV.
  code/reltab.py            RELTAB-v2 COLS: "Release ID" first; "Saved Copy?" + "File name" after "Also on caucus site (URL)";
        RELCOPY_COLS.
  code/sheet_task.py        RELCHECK-v4 (Sammy: "Add press release clean up to button training"): a new release's page
        (`html`, else `text`) is parsed by relpage.py exactly as the existing 244 rows were (dek, body, contact block, bills,
        Gabriel quoted, names Gabriel, Release type, Issue; officials by reltab.officials) and written through
        reltab.row_values (numbered columns, canonical names incl. the D-Ontario Rodriguez rule, real dates, "AB 1234" bills,
        contact split, In scope); Issue = the linked story's Topic, else the keyword label (+ build_table's fixes); the copy check
        and In tracker linking stay RELCHECK-v2/v3 (release text rule). Then the next prNNNNN, and its page cleaned with clean_html.py (library mode, the release site rules) and saved
        as pages/Press releases/<year>/<prid>.html (+ pages/_original_html/Press releases/<year>/<prid>.html); Release ID /
        Saved Copy? / File name filled; release_texts.json entry gets "prid". Result: release_copies[], releases_new[].prid.
        Old-layout tabs (no Release ID column) are written as before.
  code/sheet_task_prompt.md commit + rebuild lines for the release copies.
  code/clean_rules.json     site rules gabriel.asmdc.org (+ a46.asmdc.org) and jewishcaucus.legislature.ca.gov.
  code/release_texts.json   "prid" on every entry (from work/release_prids.json; never removes anything).
  build/js_merged.js        the Update button's release check fetches each new release's article as HTML (`html`, <= 40,000
        chars; markdown `text` only when that fails) - the form the existing releases were read from.
(apply_all_patches.py itself carries the step-4o call, relpage.py in PIPELINE + helper copies, and merge_rel_texts filling
fields a pipeline entry lacks, e.g. prid: edited directly, so a second apply_all run changes nothing.)
"""
import argparse, json, os, re

MARK = 'RELCOPIES-v1'


def _apply(path, R, mark=MARK, end_mark=True):
    if not path or not os.path.exists(path):
        return 'skipped (no file)'
    s = open(path, encoding='utf-8').read()
    if mark in s:
        return 'unchanged'
    for a, b in R:
        n = s.count(a)
        if n != 1:
            raise SystemExit(f'{path}: anchor found {n}x: {a[:90]!r}')
        s = s.replace(a, b)
    if mark not in s and end_mark:
        s = s + ('' if s.endswith('\n') else '\n') + ('<!-- ' + mark + ' -->\n' if path.endswith('.md') else
                                                      ('/* ' + mark + ' */\n' if path.endswith('.js') else '# ' + mark + '\n'))
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'


# ---------------------------------------------------------------- make_copies.py / make_copies_clean.py
MC_R = [
 ("ap.add_argument('--shard-mb', type=float, default=12.0)\n",
  "ap.add_argument('--shard-mb', type=float, default=12.0)\n"
  "ap.add_argument('--releases', help='RELCOPIES-v1: cleaned press-release copies <year>/prNNNNN.html (work/html_clean/press_releases) '\n"
  "                '-> articles/releases.json keyed by Release ID')\n"),
 ("rep['copies'] = len(man['articles'])\nwrite_out(arts, man)\n",
  """rep['copies'] = len(man['articles'])
# RELCOPIES-v1 make_copies: official press-release copies (Tracker library/Press releases/<year>/<prid>.html, cleaned like an
# article) keyed by Release ID in articles/releases.json; the Press releases tab opens them in the story panel's viewer
rep['release_copies'] = 0
if a.releases and os.path.isdir(a.releases):
    _rp, _size, _k = {}, 0, 1
    for _f in sorted(glob.glob(os.path.join(a.releases, '*', 'pr[0-9][0-9][0-9][0-9][0-9].html'))):
        _pid = os.path.basename(_f)[:-5]
        _page = drop_blobs(open(_f, encoding='utf-8', errors='replace').read(), _pid)
        _b = len(_page.encode('utf-8'))
        if _rp and _size + _b > a.shard_mb * 1e6:
            arts['releases.json' if _k == 1 else f'releases-{_k}.json'] = _rp; _k += 1; _rp, _size = {}, 0
        _rp[_pid] = _page; _size += _b; rep['release_copies'] += 1
    if _rp:
        arts['releases.json' if _k == 1 else f'releases-{_k}.json'] = _rp
    for _yf in [x for x in arts if x.startswith('releases')]:
        for _pid in arts[_yf]:
            man['articles'][_pid] = f'articles/{_yf}'
write_out(arts, man)
"""),
 ("for k in ('copies', 'stories', 'from_clean', 'from_newsbank_text', 'images', 'total_mb')",
  "for k in ('copies', 'stories', 'from_clean', 'from_newsbank_text', 'release_copies', 'images', 'total_mb')"),
]

# ---------------------------------------------------------------- build_data.py
BD_R = [
 ("dump('rows', {'cols': ['aid', 'sid', 'kind', 'outlet', 'date', 'hl', 'links'], 'rows': rows,\n",
  """# RELCOPIES-v1 build_data: next free Release ID number (prNNNNN on the "Press releases" tab) for the Update button / sheet task
try:
    _pr = pd.read_excel(COV, sheet_name='Press releases', dtype=str).fillna('')
    _prn = [int(m.group(1)) for m in (re.match(r'^pr(\\d{5})$', s(v)) for v in (_pr['Release ID'] if 'Release ID' in _pr.columns else [])) if m]
    NEXT['pr'] = max(_prn) + 1 if _prn else 1
except Exception as _e:
    report['prid_error'] = repr(_e)[:200]
dump('rows', {'cols': ['aid', 'sid', 'kind', 'outlet', 'date', 'hl', 'links'], 'rows': rows,
"""),
]

# ---------------------------------------------------------------- release_pickup_data.py
RP_R = [
 ('"bills": _bills(str(r.get("Bills mentioned", ""))), "topic": str(r.get("Issue", "")).strip(), "sids": sids})',
  '"bills": _bills(str(r.get("Bills mentioned", ""))), "topic": str(r.get("Issue", "")).strip(), "sids": sids,\n'
  '                    "prid": str(r.get("Release ID", "") or "").strip()})   # RELCOPIES-v1: the tab\'s Release ID'),
 ('o["url"] if o else "", 1 if o else 0])',
  'o["url"] if o else "", 1 if o else 0, o.get("prid", "") if o else ""])'),
 ('o["topic"], 0, [], [], o["url"], 1])',
  'o["topic"], 0, [], [], o["url"], 1, o.get("prid", "")])'),
 ('"cols": ["key", "date", "iss", "title", "bills", "topic", "auto", "sids", "rows", "url", "official"],',
  '"cols": ["key", "date", "iss", "title", "bills", "topic", "auto", "sids", "rows", "url", "official", "prid"],'),
]

# ---------------------------------------------------------------- releases_data.py
RD_R = [
 ('_s(x.get("Co-issuers / other members named", "")), _s(x.get("Word count", ""))]',
  '_s(x.get("Co-issuers / other members named", "")), _s(x.get("Word count", "")),\n'
  '                      # RELCOPIES-v1: [6] Release ID, [7] the saved copy\'s file name (Saved Copy? = Yes)\n'
  '                      _s(x.get("Release ID", "")), _s(x.get("File name", "")) if _s(x.get("Saved Copy?", "")).lower() == "yes" else ""]'),
]

# ---------------------------------------------------------------- releases.js
RJ_R = [
 ("it.src = SRC[sc]; it.co = x[4] || ''; it.wc = x[5] || '';",
  "it.src = SRC[sc]; it.co = x[4] || ''; it.wc = x[5] || '';\n"
  "      /* RELCOPIES-v1: Release ID (prNNNNN) and the saved release copy (articles/releases.json, keyed by Release ID) */\n"
  "      var iP = ci('prid'); it.prid = (iP >= 0 ? t[iP] : '') || x[6] || ''; it.saved = !!x[7];"),
 ("it.slug = s; bySlug.set(s, it); });",
  "it.old = s; it.slug = it.prid || s; bySlug.set(s, it); if (it.prid) bySlug.set(it.prid, it); });   /* RELCOPIES-v1: #press-releases/<prid>; the old date-title slug still finds it */"),
 ("find: function(sub, ctx){ prep(ctx); cur.ctx = ctx; loadTexts(); return M.bySlug.get(sub) || null; },",
  "find: function(sub, ctx){ prep(ctx); cur.ctx = ctx; loadTexts(); var it = M.bySlug.get(sub) || null;\n"
  "      /* RELCOPIES-v1: an old date-title link redirects to #press-releases/<prid> */\n"
  "      if (it && it.prid && sub !== it.prid && ctx.openPage) setTimeout(function(){ ctx.openPage(it.prid); }, 0);\n"
  "      return it; },"),
 ("if (it) return { params: {}, sub: it.slug }; }",
  "if (it) return { params: {}, sub: it.prid || it.slug }; }"),
 ("text: function(it){ return it.title + ' ' + it.dek + ' ' + body(it); },",
  "text: function(it){ return it.title + ' ' + it.dek + ' ' + (it.prid || '') + ' ' + body(it); },"),
 ("      h += '<div class=\"tb-us\"><h3 class=\"tb-us-h\">Copies of this release · '",
  "      h += savedRow(it, ctx);   /* RELCOPIES-v1 */\n"
  "      h += '<div class=\"tb-us\"><h3 class=\"tb-us-h\">Copies of this release · '"),
 ("['Release key', function(it){ return it.key; }]]",
  "['Release key', function(it){ return it.key; }], ['Release ID', function(it){ return it.prid; }], ['Saved copy', function(it){ return hasCopy(it, cur.ctx) ? 'Yes' : 'No'; }]]"),
 ("  document.addEventListener('click', function(ev){\n    var b = ev.target.closest && ev.target.closest('[data-relsaved]'), c = cur.ctx;",
  """  /* RELCOPIES-v1: the release's own saved copy (Tracker library/Press releases/<year>/<prid>.html, cleaned like an article),
     opened like a story's saved copy: the story panel's article viewer (side panel, full-page toggle, Gabriel highlighting),
     with the official link listed in the panel too. No saved copy: the page shows the official link only. */
  function hasCopy(it, ctx){ return !!(it && it.prid && (it.saved || (ctx && ctx.hasSaved && ctx.hasSaved(it.prid)))); }
  function savedRow(it, ctx){
    if (!hasCopy(it, ctx) || !ctx.openSaved) return '';
    var e = ctx.esc, t = '<button type="button" class="linkbtn" data-relprev="' + e(it.prid) + '" title="Open the saved copy in the article viewer">' + e(it.title) + '</button>';
    var meta = [e(it.src), e(dl(ctx, it.date)), it.wc ? e(ctx.fmt(+it.wc || 0) + ' words') : '', e(it.prid)];
    var right = it.url ? ctx.link(it.url, 'Official release', (function(){ try { return new URL(it.url).hostname.replace(/^www\\./, ''); } catch(x){ return ''; } })()) : '';
    return '<div class="tb-us"><h3 class="tb-us-h">Saved copy of this release</h3><div class="cap">The release as posted, saved and cleaned like an article. Click the title to read it in the article viewer.</div>'
      + '<div class="clip-list">' + (ctx.row ? ctx.row({ attrs: ' data-relprevrow="' + e(it.prid) + '"', title: t, meta: meta, right: right })
        : '<div class="clip"><span class="ct">' + t + '</span><span class="cm">' + meta.filter(Boolean).join(' · ') + '</span>' + right + '</div>') + '</div></div>';
  }
  document.addEventListener('click', function(ev){
    var b = ev.target.closest && ev.target.closest('[data-relprev]'), c = cur.ctx;
    if (!b || !c || !c.openSaved) return; ev.preventDefault(); ev.stopPropagation();
    var it = M.bySlug && M.bySlug.get(b.dataset.relprev);
    if (it) c.openSaved(it.prid, { aid: '', hl: it.title, outlet: it.src, date: it.date, plink: it.url, link: '', pq: '' });
  });
  document.addEventListener('click', function(ev){
    var b = ev.target.closest && ev.target.closest('[data-relsaved]'), c = cur.ctx;"""),
]

# ---------------------------------------------------------------- reltab.py
RT_R = [
 ('COLS = (["Date", "Title", "Subtitle/dek", "Source", "URL", "Also on caucus site (date)", "Also on caucus site (URL)",\n         "Release type",',
  '# RELCOPIES-v1 (RELTAB-v2): "Release ID" (prNNNNN, permanent, first column) and the release\'s saved copy (Tracker library/\n'
  '# Press releases/<year>/<prid>.html): "Saved Copy?" + "File name" after the official links\n'
  'RELCOPY_COLS = ("Release ID", "Saved Copy?", "File name")\n'
  'COLS = (["Release ID", "Date", "Title", "Subtitle/dek", "Source", "URL", "Also on caucus site (date)", "Also on caucus site (URL)",\n'
  '         "Saved Copy?", "File name", "Release type",'),
 ('WIDTHS = {"Date": 11,', 'WIDTHS = {"Release ID": 10, "Saved Copy?": 9, "File name": 16, "Date": 11,'),
]

# ---------------------------------------------------------------- sheet_task.py
ST_R = [
 ("    import reltab as RT\n",
  "    import reltab as RT\n"
  "    try:\n"
  "        import relpage as RPG   # RELCOPIES-v1 sheet_task: a release page -> the tab's facts, exactly as the existing rows were made\n"
  "    except Exception:\n"
  "        RPG = None\n"),
 ("            body = self._rel_body(str(x.get('text') or ''), title)",
  "            # RELCOPIES-v1 sheet_task: the page (run doc `html` = the article, else its markdown `text`) parsed like the existing rows\n"
  "            _pg = RPG.parse(str(x.get('html') or x.get('text') or ''), title, 'caucus' if caucus else 'office') \\\n"
  "                if (RPG is not None and (x.get('html') or x.get('text'))) else None\n"
  "            body = _pg['body'] if (_pg and _pg['body']) else self._rel_body(str(x.get('text') or ''), title)"),
 ("            rel = {'url': url, 'date': d, 'title': title, 'dek': str(x.get('dek', '')).strip(), 'body': body,",
  "            rel = {'url': url, 'date': d, 'title': title, 'dek': ((_pg or {}).get('dek') or str(x.get('dek', ''))).strip(), 'body': body,"),
 ("            need = list(RT.COLS)",
  "            need = [c for c in RT.COLS if c not in getattr(RT, 'RELCOPY_COLS', ())]   # RELCOPIES-v1: the copy columns are optional"),
 ("            r = ws.max_row + 1\n            for c in range(1, ws.max_column + 1):",
  """            if new_layout and _pg:   # RELCOPIES-v1 sheet_task: the whole RELTAB cleanup, the way the existing rows were made
                vals = RT.row_values(d, title, rel['dek'], caucus, url, _pg['bills'], 'Yes' if _pg['quoted'] else 'No', RT.officials(body),
                                     _pg['contact'], _pg['words'], sids, len(hits) if hits else '', vals['Note'])
                vals['Release type'] = _pg['type']
                vals['Issue'] = self._rel_topic(sids) or RPG.issue_for(url, _pg['issue'])
                if caucus:
                    vals['Caucus release names Gabriel'] = 'Yes' if _pg['named'] else 'No'
            if 'Release ID' in H:   # RELCOPIES-v1 sheet_task: Release ID + the release's library copy (cleaned like an article)
                prid = self.next_prid(ws, H, texts)
                vals['Release ID'] = prid
                fn = self.save_release_copy(prid, d, title, str(x.get('dek', '')).strip(), x, caucus, url, body)
                if 'Saved Copy?' in H:
                    vals['Saved Copy?'] = 'Yes' if fn else 'No'
                if 'File name' in H:
                    vals['File name'] = fn
                if url in texts:
                    texts[url]['prid'] = prid
            r = ws.max_row + 1
            for c in range(1, ws.max_column + 1):"""),
 ("self.res['releases_new'].append({'date': d, 'title': title[:200], 'url': url, 'in_tracker': bool(sids), 'stories': sids})",
  "self.res['releases_new'].append({'date': d, 'title': title[:200], 'url': url, 'in_tracker': bool(sids), 'stories': sids,\n"
  "                                             'prid': vals.get('Release ID', '')})   # RELCOPIES-v1"),
 ("    # RELCHECK-v2 sheet_task: the release text rule (Sammy 2026-10-27) - a row carries an official release only when its saved",
  """    # RELCOPIES-v1 sheet_task: Release IDs (prNNNNN: max on the tab or in release_texts.json + 1; never reused) and release copies
    def _rel_topic(self, sids):
        \"\"\"a release linked to tracker stories takes the Topic of the first one's Original (build_table.py rule)\"\"\"
        for sid in sids or []:
            r = self.s.original_row(sid)
            t = str(self.s.get(r, 'Topic') or '').strip() if r else ''
            if t:
                return t
        return ''

    def next_prid(self, ws, H, texts):
        if getattr(self, '_prid_next', None) is None:
            n = 0
            for rr in range(2, ws.max_row + 1):
                m = re.match(r'^pr(\\d{5})$', str(ws.cell(rr, H['Release ID']).value or '').strip())
                if m:
                    n = max(n, int(m.group(1)))
            for t in (texts or {}).values():
                m = re.match(r'^pr(\\d{5})$', str((t or {}).get('prid', '')))
                if m:
                    n = max(n, int(m.group(1)))
            self._prid_next = n + 1
        p = f'pr{self._prid_next:05d}'
        self._prid_next += 1
        return p

    def save_release_copy(self, prid, d, title, dek, x, caucus, url, body):
        \"\"\"the release page as the library keeps it (title, header div, <h1>, the release), cleaned with clean_html.py in library
        mode (clean_rules.json site rules for gabriel.asmdc.org / jewishcaucus), photos' src made absolute; saved to
        <pages-dir>/Press releases/<year>/<prid>.html, the uncleaned page to <pages-dir>/_original_html/Press releases/<year>/.
        Returns the file name, or '' (no release text, no --pages-dir, cleaner not loaded).\"\"\"
        import os, html as _h
        self.res.setdefault('release_copies', [])
        pages_dir = getattr(self, 'pages_dir', None)
        if not body or not pages_dir or CH is None:
            self.res['release_copies'].append({'prid': prid, 'url': url, 'file': '', 'why': 'no release text' if not body else
                                               ('no --pages-dir' if not pages_dir else 'clean_html.py not loaded')})
            return ''
        year = d[:4] if re.match(r'^\\d{4}', d or '') else self.today[:4]
        src = 'California Legislative Jewish Caucus' if caucus else "Gabriel's office (gabriel.asmdc.org)"
        e = _h.escape
        art = str(x.get('html') or '').strip()   # the article HTML as fetched (the library's raw page keeps it as is)
        if not art:
            paras = [p.strip() for p in re.split(r'\\n\\s*\\n', body) if p.strip()]
            if len(paras) < 2:
                paras = [p.strip() for p in body.split('\\n') if p.strip()]
            art = (f'<h3 class="subtitle">{e(dek)}</h3>' if dek else '') + ''.join(f'<p>{e(p)}</p>' for p in paras)
        page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{e(title)}</title></head><body>'
                f'<div>{e(src)} · {d}<br>{e(url)}<br>Saved {self.today}</div><h1>{e(title)}</h1>\\n' + (art if art.lstrip().startswith('<article') else f'<article>{art}</article>') + '\\n</body></html>')
        res = CH.clean_page(page, url, src, {'Outlet': src, 'Date': d, 'Publisher link': url, 'Headline': title}, self.rules(), mode='library')
        base = (re.match(r'^(https?://[^/]+)', url) or [None, ''])[1] if url else ''
        out = re.sub(r'(<img\\b[^>]*?\\bsrc=")(/[^"]*)"', lambda m: m.group(1) + base + m.group(2) + '"', res['html']) if base else res['html']
        fname = f'{prid}.html'
        os.makedirs(os.path.join(pages_dir, 'Press releases', year), exist_ok=True)
        with open(os.path.join(pages_dir, 'Press releases', year, fname), 'w', encoding='utf-8') as f:
            f.write(out)
        os.makedirs(os.path.join(pages_dir, '_original_html', 'Press releases', year), exist_ok=True)
        with open(os.path.join(pages_dir, '_original_html', 'Press releases', year, fname), 'w', encoding='utf-8') as f:
            f.write(page)
        self.res['release_copies'].append({'prid': prid, 'url': url, 'file': f'Press releases/{year}/{fname}',
                                           'original': f'_original_html/Press releases/{year}/{fname}', 'status': res['status'], 'flags': res['flags']})
        return fname

    # RELCHECK-v2 sheet_task: the release text rule (Sammy 2026-10-27) - a row carries an official release only when its saved"""),
]

# ---------------------------------------------------------------- tracker JS (the Update button's release check)
JS_R = [
 ("try { r.text = (await relFetch(mcp, r.url, 'main', 'markdown')).slice(0, 12000); } catch(e){ r.text = ''; r.err = VS(String(e && e.message || e), 200); }",
  "/* RELCOPIES-v1: the article as HTML (what the library copy and the tab's facts are made from, like the existing releases); markdown only as a fallback */\n"
  "      try { r.html = (await relFetch(mcp, r.url, 'article', 'html')).slice(0, 40000); r.text = ''; }\n"
  "      catch(e0){ r.html = ''; try { r.text = (await relFetch(mcp, r.url, 'main', 'markdown')).slice(0, 12000); } catch(e){ r.text = ''; r.err = VS(String(e && e.message || e), 200); } }"),
]

# ---------------------------------------------------------------- lean sheet-task prompt
PR_R = [
 ("and add `--library library` (RELCHECK-v2).",
  "and add `--library library` (RELCHECK-v2). New releases (RELCOPIES-v1): a `releases_new` item with neither `html` nor `text`: fetch the page first (TinyFish `fetch_content`, format html, include_selectors [\"article\"]) into its `html`. sheet_task.py then does the whole release cleanup itself: tab row split and named like the existing rows, copy check + In tracker by the text rule, next Release ID, cleaned + raw library copy in `pages/`, Saved Copy? / File name, release_texts.json entry."),
 ("Commit each `pages/<year>/<file>` to `Tracker library/<year>/`",
  "Commit each `pages/Press releases/<year>/<prid>.html` to `Tracker library/Press releases/<year>/` and each `pages/_original_html/Press releases/<year>/<prid>.html` to `Tracker library/_original_html/Press releases/<year>/` (RELCOPIES-v1, add-only). Commit each `pages/<year>/<file>` to `Tracker library/<year>/`"),
 ("Add each saved (cleaned) page to `articles/<year>.json` keyed by Story ID and to `articles/manifest.json`.",
  "Add each saved (cleaned) page to `articles/<year>.json` keyed by Story ID and to `articles/manifest.json`. Add each saved release copy (`result.release_copies[].file`) to `articles/releases.json` keyed by its Release ID and to the manifest (RELCOPIES-v1; read the published `articles/releases.json` first, keep its entries)."),
]

SITES = {
    "gabriel.asmdc.org": {"hosts": ["gabriel.asmdc.org", "a46.asmdc.org"], "outlets": ["Gabriel's office (gabriel.asmdc.org)"], "kill": ["Image"],
                          "note": "RELCOPIES-v1 (agent-relcopies2 2026-10-28): official release pages (Drupal press-releases node). Keep headline, dek (h3.subtitle), date + contact block (press-status), body, photos + alt text; only the bare 'Image' field label goes."},
    "jewishcaucus.legislature.ca.gov": {"hosts": ["jewishcaucus.legislature.ca.gov"], "outlets": ["California Legislative Jewish Caucus"], "kill": ["Image"],
                                        "note": "RELCOPIES-v1: Jewish Caucus news pages (Drupal news node). Keep headline, 'Publish Date' + date, body; only a bare 'Image' field label goes."},
}


def rules_json(path):
    if not os.path.exists(path):
        return 'skipped (no file)'
    r = json.load(open(path, encoding='utf-8'))
    if all(k in r.get('sites', {}) for k in SITES):
        return 'unchanged'
    for k, v in SITES.items():
        r['sites'].setdefault(k, v)
    json.dump(r, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return 'patched'


def texts_json(path, prids):
    if not os.path.exists(path) or not os.path.exists(prids):
        return 'skipped (no file)'
    t, m = json.load(open(path, encoding='utf-8')), json.load(open(prids, encoding='utf-8'))
    n = 0
    for u, x in t.get('rel', {}).items():
        if isinstance(x, dict) and not x.get('prid') and m.get(u):
            x['prid'] = m[u]; n += 1
    if not n:
        return 'unchanged'
    json.dump({'v': t.get('v', 1), 'rel': t['rel']}, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    return f'patched ({n} prids)'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    a = ap.parse_args()
    P = lambda *x: os.path.join(a.root, *x)
    here = os.path.dirname(os.path.abspath(__file__))
    for f in ('code/make_copies.py', 'code/make_copies_clean.py'):
        print(f + ':', _apply(P(f), MC_R))
    print('build_data:', _apply(P('code/build_data.py'), BD_R))
    print('release_pickup_data:', _apply(P('build/insights/release_pickup_data.py'), RP_R))
    print('releases_data:', _apply(P('build/tabs/releases_data.py'), RD_R))
    print('releases.js:', _apply(P('build/tabs/releases.js'), RJ_R))
    print('reltab:', _apply(P('code/reltab.py'), RT_R))
    print('sheet_task:', _apply(P('code/sheet_task.py'), ST_R))
    print('prompt:', _apply(P('code/sheet_task_prompt.md'), PR_R))
    print('tracker JS:', _apply(P('build/js_merged.js'), JS_R, mark='RELCOPIES-v1: the article as HTML', end_mark=False))
    print('clean_rules.json:', rules_json(P('code/clean_rules.json')))
    print('release_texts.json:', texts_json(P('code/release_texts.json'), P('work/release_prids.json')))
