#!/usr/bin/env python3
"""patch_f7.py - F7-v1 (agent-final-F4, 2026-10-27): the combined-republish fixes.

  python3 -I code/patch_f7.py --js build/js_merged.js --build-data code/build_data.py --assemble code/assemble.py \
      --sheet-task code/sheet_task.py --prompt build/sheet_task_prompt_final.md

Idempotent: an edit is skipped when its new text is already present; an edit that finds neither its old nor its new
text exactly once stops the script (exit 1, nothing written).

1. Acceptance fixes (DECISIONS, coordinator 2026-10-27):
   - build_data never outputs the retired Reach label 'Spanish-language & ethnic' (dropped from multi-tag cells; the
     fill-from-outlet consensus never sees it, so those stories show blank until Sammy decides);
   - Bills shown are limited to bills in the leginfo list (gabriel_bills_leginfo.json next to build_data.py);
   - page <title> 'AJG Press Coverage Tracker' (assemble drops '(Copy)').
2. No reprint links anywhere (Sammy, artifact comment): the story panel's "Reprint links (N)" list is gone; reprints are
   listed by outlet only ("Reprinted in"); links stay on the Original.
3. Dates of future finds (DECISIONS, Pasadena entry):
   - pasadenanow.com / altadenanow.com: the date is the "Published on <weekday>, <date>" line under the headline, never
     the site header date or TinyFish's published_date (tracker Update button and sheet_task.py);
   - generic guard: a find whose date equals the fetch date and comes only from TinyFish's published_date is reported
     for review (Update review list tag; sheet task result.date_review).
"""
import argparse, sys

MARK = 'F7-v1'

# ------------------------------------------------------------------ build_data.py
BD = [
    ('reach/bills helpers',
     "def s(v): return str(v).strip()\n",
     "def s(v): return str(v).strip()\n"
     "# ---- F7-v1: retired Reach label never output; Bills limited to Gabriel's leginfo list\n"
     "RETIRED_REACH = {'Spanish-language & ethnic'}\n"
     "def reach_ok(v):\n"
     "    return '; '.join(t.strip() for t in str(v or '').split(';') if t.strip() and t.strip() not in RETIRED_REACH)\n"
     "_BL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gabriel_bills_leginfo.json')\n"
     "def _bnorm(b): return re.sub(r'\\s+', ' ', str(b or '').upper().replace('.', '')).strip()\n"
     "HIS_BILLS = {_bnorm(b.get('bill')) for b in json.load(open(_BL, encoding='utf-8')).get('rows', []) if b.get('bill')} if os.path.exists(_BL) else None\n"
     "BILLS_DROPPED = collections.Counter()\n"
     "def bills_ok(lst):\n"
     "    if HIS_BILLS is None: return list(lst)\n"
     "    out = [b for b in lst if _bnorm(b) in HIS_BILLS]\n"
     "    for b in lst:\n"
     "        if _bnorm(b) not in HIS_BILLS: BILLS_DROPPED[b] += 1\n"
     "    return out\n"
     "# ---- /F7-v1\n"),
    ('reach on records',
     "        'reach': s(r['Reach']) or o.get('reach', ''),\n",
     "        'reach': reach_ok(s(r['Reach']) or o.get('reach', '')),  # F7-v1\n"),
    ('bills on records',
     "        'bills': [b.strip() for b in re.split(r'[;,]', s(r['Bills'])) if b.strip()] or o.get('bills', []),\n",
     "        'bills': bills_ok([b.strip() for b in re.split(r'[;,]', s(r['Bills'])) if b.strip()] or o.get('bills', [])),  # F7-v1\n"),
    ('report',
     "report.update({'rows': len(rows), 'idmap': len(idmap),",
     "report['bills_dropped_not_leginfo'] = dict(BILLS_DROPPED)  # F7-v1\n"
     "report['reach_retired_label_left'] = sum(1 for x in data if 'Spanish-language & ethnic' in x['reach'])  # F7-v1\n"
     "report.update({'rows': len(rows), 'idmap': len(idmap),"),
]

# ------------------------------------------------------------------ assemble.py
ASM = [
    ('title',
     "m = h.rfind('<script>')\n",
     "h = h.replace('<title>AJG Press Coverage Tracker (Copy)</title>', '<title>AJG Press Coverage Tracker</title>')  # F7-v1\n"
     "m = h.rfind('<script>')\n"),
]

# ------------------------------------------------------------------ tracker JS
JS = [
    ('no reprint links: function',
     "function repLinks(r){\n",
     "function repLinks(r){ return '';  /* F7-v1: no links to reprints anywhere (Sammy 2026-10-27); links stay on the Original. The call in the story panel stays (LINKS-v1 owns it) and renders nothing. */\n"),
    ('page date helper',
     "function toRow(c, k){\n",
     "/* F7-v1 (DECISIONS, Pasadena entry): Pasadena Now and Altadena Now show the site's header date (today) above the story;\n"
     "   the story's date is the \"Published on <weekday>, <date>\" line under the headline. Never TinyFish's published_date there. */\n"
     "const PAGE_DATE_HOSTS = /(^|\\.)(pasadenanow|altadenanow)\\.com$/i;\n"
     "const MONTHS_FULL = ['january','february','march','april','may','june','july','august','september','october','november','december'];\n"
     "function pageDate(text, url){\n"
     "  if (!PAGE_DATE_HOSTS.test(hostOf(url))) return '';\n"
     "  const m = String(text || '').match(/Published on\\s+(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\\s*,?\\s+([A-Za-z]+)\\.?\\s+(\\d{1,2}),?\\s+(\\d{4})/i);\n"
     "  if (!m) return '';\n"
     "  const mi = MONTHS_FULL.findIndex(x => x.startsWith(m[1].toLowerCase().slice(0, 3)));\n"
     "  return mi < 0 ? '' : `${m[3]}-${String(mi + 1).padStart(2, '0')}-${String(+m[2]).padStart(2, '0')}`;\n"
     "}\n"
     "function toRow(c, k){\n"),
    ('fetch: page date first',
     "          if (/^\\d{4}-\\d\\d-\\d\\d/.test(r.published_date || '')) c.published = r.published_date.slice(0,10);\n",
     "          { const pd = pageDate(t, r.final_url || c.url);   /* F7-v1: \"Published on\" line; TinyFish's date only elsewhere */\n"
     "            if (pd){ c.published = pd; c.dateSrc = 'page'; }\n"
     "            else if (PAGE_DATE_HOSTS.test(hostOf(r.final_url || c.url))){ c.published = ''; c.dateSrc = 'none'; }\n"
     "            else if (/^\\d{4}-\\d\\d-\\d\\d/.test(r.published_date || '')){ c.published = r.published_date.slice(0,10); c.dateSrc = 'tinyfish'; } }\n"),
    ('body date fetch',
     "    list.forEach(c => { c.gab = NAMES_HIM.test(c.title + ' ' + c.text)",
     "    // F7-v1: Pasadena/Altadena Now keep the \"Published on\" line outside the article TinyFish extracts (TinyFish's\n"
     "    // published_date there is the site header date = today): read the line from the rest of the page body.\n"
     "    { const need = toFetch.filter(c => c.dateSrc === 'none');\n"
     "      for (let i = 0; i < need.length && !U.ctl.signal.aborted; i += 10){ const b = need.slice(i, i+10);\n"
     "        try { const pgs = tfResults(tfPayload(await tfCall(mcp, 'fetch_content', tfFetchInput(b.map(c => c.url), { format: 'markdown', include_selectors: ['body'], exclude_selectors: ['header', 'nav', 'footer', 'aside', 'article', 'script', 'style'] }))));\n"
     "          b.forEach(c => { const r = pgs.get(normU(c.url)); if (!r) return; const tx = String(r.text || ''), pd = pageDate(tx, r.final_url || c.url);\n"
     "            if (pd){ c.published = pd; c.dateSrc = 'page'; if (c.page) c.page.pubLine = ((tx.match(/Published on[^\\n|]{0,60}/i) || [''])[0]).trim(); } });\n"
     "        } catch(e){ if (STOP_CODES.has(e && e.code)) throw e; } } }\n"
     "    list.forEach(c => { c.gab = NAMES_HIM.test(c.title + ' ' + c.text)"),
    ('page doc carries the Published-on line',
     "clean: r._page.clean, scoped: ",
     "clean: r._page.clean, publine: VS(r._page.pubLine || '', 120) /* F7-v1 */, scoped: "),
    ('toRow: date source',
     "  const date = /^\\d{4}-\\d{2}-\\d{2}$/.test(k.date) ? k.date : (c.published || TODAY);\n"
     "  const nodate = !/^\\d{4}-\\d{2}-\\d{2}$/.test(k.date) && !c.published;\n",
     "  const kd = /^\\d{4}-\\d{2}-\\d{2}$/.test(k.date) ? k.date : '';   /* F7-v1 */\n"
     "  const date = c.dateSrc === 'page' && c.published ? c.published : (kd || c.published || TODAY);\n"
     "  const nodate = !kd && !c.published;\n"
     "  const dateSrc = c.dateSrc === 'page' ? 'page' : (kd && kd !== c.published ? 'claude' : (c.published ? (c.dateSrc || 'tinyfish') : ''));\n"
     "  const datecheck = (date === TODAY && dateSrc === 'tinyfish') || (c.dateSrc === 'none' && !nodate);\n"),
    ('toRow: carry flags',
     "added: TODAY, why: VS(k.why,300), _nodate: nodate,\n",
     "added: TODAY, why: VS(k.why,300), _nodate: nodate, _dateSrc: dateSrc, _datecheck: datecheck,  /* F7-v1 */\n"),
    ('review tag',
     "${r._nodate?'<span>Date not found, check it</span>':''}",
     "${r._nodate?'<span>Date not found, check it</span>':''}${r._datecheck?'<span>Date may be the fetch date (no date on the page), check it</span>':''}"),
    ('date edit clears check',
     "r._nodate = false; } return; }",
     "r._nodate = false; r._datecheck = false; r._dateSrc = 'edited'; } return; }"),
    ('proposed row carries date source',
     "      'File name': r._blocked ? 'BLOCKED – TinyFish' : '', 'Saved Copy?': r._blocked ? 'No' : '' }));   /* AUTO-v1: paywall/login/bot wall */\n",
     "      'File name': r._blocked ? 'BLOCKED – TinyFish' : '', 'Saved Copy?': r._blocked ? 'No' : '' }));   /* AUTO-v1: paywall/login/bot wall */\n"
     "    if (r._dateSrc) out[out.length - 1]._date_src = r._dateSrc;   /* F7-v1: read by the sheet task's date guard (not a sheet column) */\n"
     "    if (r._datecheck) out[out.length - 1]._date_check = 'yes';\n"),
]

# ------------------------------------------------------------------ sheet_task.py
ST = [
    ('page date helpers',
     "def is_press_release(vals):\n",
     "# F7-v1 (DECISIONS, Pasadena entry): Pasadena Now / Altadena Now dates come from the 'Published on <weekday>, <date>'\n"
     "# line under the headline, never the site header date or TinyFish's published_date.\n"
     "PAGE_DATE_HOSTS = re.compile(r'(^|\\.)(pasadenanow|altadenanow)\\.com$', re.I)\n"
     "_PUB_ON = re.compile(r'Published on\\s+(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\\s*,?\\s+([A-Za-z]+)\\.?\\s+(\\d{1,2}),?\\s+(\\d{4})', re.I)\n"
     "_MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']\n"
     "\n"
     "\n"
     "def published_on(html):\n"
     "    \"\"\"'Published on Thursday, March 6, 2025' -> '2025-03-06' (tags stripped first); '' if absent\"\"\"\n"
     "    t = re.sub(r'\\s+', ' ', re.sub(r'<[^>]+>', ' ', str(html or '')).replace('&nbsp;', ' '))\n"
     "    m = _PUB_ON.search(t)\n"
     "    if not m or m.group(1)[:3].lower() not in _MONTHS:\n"
     "        return ''\n"
     "    return f\"{m.group(3)}-{_MONTHS.index(m.group(1)[:3].lower()) + 1:02d}-{int(m.group(2)):02d}\"\n"
     "\n"
     "\n"
     "def is_press_release(vals):\n"),
    ('result keys',
     "'reprint_check': [], 'reach': [], 'authors_split': [], 'gabriel_unclear': [], 'bills_new': []}",
     "'reprint_check': [], 'reach': [], 'authors_split': [], 'gabriel_unclear': [], 'bills_new': [],\n"
     "                    'date_fixes': [], 'date_review': []}   # F7-v1"),
    ('run day',
     "            rows = run.get('rows') or []\n            if not rows or run.get('ids'):\n",
     "            rows = run.get('rows') or []\n            self._run_day = str(run.get('at') or '')[:10]   # F7-v1: the fetch date of this run's finds\n"
     "            if not rows or run.get('ids'):\n"),
    ('date check in add_row',
     "        d = norm_val(vals.get('Date'))\n        if re.match(r'^\\d{4}-\\d{2}-\\d{2}$', d):\n            vals['Date'] = d\n",
     "        self.date_check(vals, obj, run_id, ph_aid, aid)   # F7-v1\n"
     "        d = norm_val(vals.get('Date'))\n        if re.match(r'^\\d{4}-\\d{2}-\\d{2}$', d):\n            vals['Date'] = d\n"),
    ('date_check method',
     "    def apply_runs(self):\n",
     "    def date_check(self, vals, obj, run_id, ph_aid, aid):\n"
     "        \"\"\"F7-v1: Pasadena/Altadena Now -> the page's 'Published on' date; a date equal to the fetch date that only\n"
     "        TinyFish's published_date gave is reported for review (never changed).\"\"\"\n"
     "        d = norm_val(vals.get('Date'))[:10]\n"
     "        e = {'run': run_id, 'placeholder': ph_aid, 'aid': aid, 'outlet': vals.get('Outlet', ''),\n"
     "             'link': vals.get('Publisher link', ''), 'date': d}\n"
     "        if PAGE_DATE_HOSTS.search(host_of(vals.get('Publisher link', ''))):\n"
     "            pid = self.page_doc_id(obj)\n"
     "            p = ((self.db.get('pages') or {}).get(pid) or {}) if pid else {}\n"
     "            pd = published_on(' '.join(str(p.get(k) or '') for k in ('publine', 'clean', 'scoped', 'html')))\n"
     "            if pd:\n"
     "                if pd != d:\n"
     "                    vals['Date'], vals['Year'] = pd, int(pd[:4])\n"
     "                    self.res['date_fixes'].append(dict(e, new=pd, why='Published on line'))\n"
     "                return\n"
     "            if str(obj.get('_date_src') or '') == 'page':\n"
     "                return   # the Update button read the line when it fetched the page\n"
     "            self.res['date_review'].append(dict(e, why='Pasadena/Altadena Now page without a \"Published on\" line: date not confirmed'))\n"
     "            return\n"
     "        if str(obj.get('_date_check') or '') == 'yes' or (str(obj.get('_date_src') or '') == 'tinyfish'\n"
     "                                                         and d and d in (self.today, getattr(self, '_run_day', ''))):\n"
     "            self.res['date_review'].append(dict(e, why=\"date equals the fetch date and comes only from TinyFish's published_date\"))\n"
     "\n"
     "    def apply_runs(self):\n"),
    ('counts + line',
     "    res['sheet_stories'] = stories\n",
     "    res['counts'].update({'date_fixes': len(res['date_fixes']), 'date_review': len(res['date_review'])})   # F7-v1\n"
     "    if res['date_review']:\n"
     "        res['sheet_line'] = res['sheet_line'][:-1] + f\", {len(res['date_review'])} dates to check (see review).\"\n"
     "    res['sheet_stories'] = stories\n"),
]

PR = [
    ('date review',
     "Add `result.skipped`, `result.pages_error`, `result.pages_flagged`, `result.reprint_check`, `result.reach` and `result.gabriel_unclear` to the run doc's `review`",
     "Add `result.skipped`, `result.pages_error`, `result.pages_flagged`, `result.reprint_check`, `result.reach`, `result.gabriel_unclear`, `result.date_fixes` and `result.date_review` (F7-v1: Pasadena/Altadena Now dates taken from the page's \"Published on\" line; dates that equal the fetch date and come only from TinyFish) to the run doc's `review`"),
]


def apply(path, edits, name, check):
    t = open(path, encoding='utf-8').read(); t0 = t
    for label, old, new in edits:
        if new in t:
            print(f'  [{name}] skip (already applied): {label}'); continue
        if t.count(old) != 1:
            sys.exit(f'[{name}] anchor for "{label}" found {t.count(old)} times; nothing written')
        t = t.replace(old, new); print(f'  [{name}] applied: {label}')
    return t, t != t0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    for k in ('js', 'build-data', 'assemble', 'sheet-task', 'prompt'): ap.add_argument('--' + k)
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    out = []
    for path, edits, name in ((a.js, JS, 'js'), (a.build_data, BD, 'build_data'), (a.assemble, ASM, 'assemble'),
                              (a.sheet_task, ST, 'sheet_task'), (a.prompt, PR, 'prompt')):
        if path: out.append((path, *apply(path, edits, name, a.check)))
    if not a.check:
        for path, t, changed in out:
            if changed: open(path, 'w', encoding='utf-8').write(t)
    print('ok')
