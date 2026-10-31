#!/usr/bin/env python3
"""patch_auto.py - AUTO-v1 (agent-code, 2026-10-27): the manual steps of 2026-10-27 made automatic for new finds.

  python3 -I patch_auto.py --js build/js_merged.js --sheet-task code/sheet_task.py --prompt build/sheet_task_prompt_final.md \
      --assemble code/assemble.py --build-data code/build_data.py

DECISIONS 2026-10-27 ("automate in the Update button + sheet task"):
  1 reprint check   sheet_task.py: a new find whose text passes the regroup's string-of-text rule (code/reprint_rule.py) against
                    an Original within +-7 days with overlapping headline words becomes a Reprint of that story; edge/clutter
                    passes are reported as low confidence; no text -> headline + author rule; a find that would rank before
                    the existing Original (originals order) is reported, never swapped (blank cells only)
  2 BLOCKED/RETRY   paywall / login / bot-wall pages -> File name 'BLOCKED – TinyFish' (sheet task and Update button),
                    other bad pages keep 'RETRY – TinyFish'
  3 wrong Gabriel   Jesse Gabriel only: pages naming only another Gabriel (Ugarte, Petek, Dillard, Lerner, San Gabriel …) or
                    no Gabriel in any script are skipped and reported (sheet task + Update button)
  4 authors         Author 1..N + Author title on new rows (authorsplit.parse_byline; author_canon applies at build)
  5 counts          Word count (CJK by character) and Mentions "Gabriel" in text (non-Latin forms too) from the saved page
  6 reach           a new row's Reach = the same outlet's Reach in the sheet when all its rows agree (tag sets), else blank
  7 listing pages   database / results / listing pages (clean_rules.json skip_urls) are never added
  + bills           the tracker's hard-coded BILL_INFO is replaced by <script id="billsinfo"> (gabriel_bills_leginfo.json);
                    authored bills are his, coauthored ones are named and marked "(coauthored)"; the Update button checks
                    leginfo's author search for the current session (TinyFish) and passes new bills to the sheet task
                    (run doc "bills_new"), which appends them to gabriel_bills_leginfo.json in the pipeline.
Each file is skipped when its AUTO-v1 marker is already there; nothing is written unless every anchor is found once.
"""
import argparse, os, re, sys

MARK = {'js': '/* AUTO-v1 tracker */', 'st': '# AUTO-v1 sheet_task', 'pr': '<!-- AUTO-v1 -->', 'asm': 'AUTO-v1 assemble',
        'bd': '# AUTO-v1 build_data'}


class Patch:
    def __init__(self, path, marker):
        self.path, self.marker = path, marker
        self.t = self.orig = open(path, encoding='utf-8').read()
        self.bad, self.done = [], []
        self.skip = marker in self.t

    def rep(self, name, old, new):
        if self.skip:
            return
        n = self.t.count(old)
        if n != 1:
            self.bad.append(f'{os.path.basename(self.path)}: anchor {name!r} found {n}x')
            return
        self.t = self.t.replace(old, new)
        self.done.append(name)

    def ready(self):
        """every anchor found and the marker in place (checked for all files before any is written)"""
        if not self.skip and not self.bad and self.marker not in self.t:
            self.bad.append(f'{os.path.basename(self.path)}: marker missing after patch')
        return self.skip or not self.bad

    def save(self):
        if self.skip:
            self.done.append('already applied')
        elif self.t != self.orig:
            open(self.path, 'w', encoding='utf-8').write(self.t)


# ===================================================================================== sheet_task.py
ST_IMPORTS = r'''RETRY = 'RETRY – TinyFish'
# AUTO-v1 sheet_task (agent-code, 2026-10-27): the manual steps of 2026-10-27 for new finds (see Task.reprint_check etc.)
BLOCKED = 'BLOCKED – TinyFish'   # DECISIONS 2026-10-27: blocked / paywall / login pages; other bad pages keep RETRY
try:
    import reprint_rule as RR        # the regroup's string-of-text reprint rule (reprint_rule.py next to this script)
except Exception as _e:
    RR = None
try:
    from authorsplit import parse_byline as _parse_byline   # Author 1..N + Author title (author_canon applies at build)
except Exception:
    _parse_byline = None
'''

ST_METHODS = r'''
    # ---------- AUTO-v1: reprint check, Jesse Gabriel only, reach, authors, counts, bills (DECISIONS 2026-10-27) ----------
    def rules(self):
        if self._rules is None:
            self._rules = CH.load_rules() if CH is not None else {}
        return self._rules

    def page_text(self, html):
        from bs4 import BeautifulSoup
        return CH.norm(' '.join(b.text for b in CH.extract_blocks(CH.body_of(BeautifulSoup(html or '', 'html.parser')))))

    def wrong_gabriel(self, chk, obj, run_id):
        """Jesse Gabriel only: a page naming only another Gabriel, or no Gabriel in any script, is skipped (reason);
        a bare "Gabriel" with nothing to tell which one is kept and reported (gabriel_unclear)."""
        t = str(obj.get('Headline') or '') + '\n' + self.page_text(chk['html'])
        v = CH.jesse_check(t, self.rules())
        if v == 'other':
            m = CH.rx(self.rules()['other_gabriel']).search(t)
            return f"another Gabriel, not Jesse Gabriel ({m.group(0) if m else 'other Gabriel'})"
        if v == 'none':
            return 'no Jesse Gabriel on the page in any script'
        if v == 'unclear':
            self.res['gabriel_unclear'].append({'run': run_id, 'placeholder': obj.get('Article ID', ''), 'outlet': obj.get('Outlet', ''),
                                                'link': obj.get('Publisher link', ''), 'why': 'a bare "Gabriel" with no sign which one: kept, check it'})
        return None

    def originals(self):
        if self._origs is None:
            cols = ('Article ID', 'Story ID', 'Date', 'Headline', 'Outlet', 'Author / byline', 'Press release', 'Data Source', 'Edition')
            self._origs = [dict({c: norm_val(self.s.get(r, c)) for c in cols}, _row=r) for r in range(2, self.s.last_row + 1)
                           if self.s.get(r, 'Original or reprint') == 'Original' and not blank(self.s.get(r, 'Story ID'))]
        return self._origs

    def copy_html(self, sid):
        """the tracker's saved copy of a story (articles/manifest.json + articles/<year>.json from the published tracker)"""
        import os
        if not self.copies_dir:
            return None
        if self._manifest is None:
            try:
                self._manifest = json.load(open(os.path.join(self.copies_dir, 'articles', 'manifest.json'), encoding='utf-8')).get('articles', {})
            except Exception:
                self._manifest = {}
        f = self._manifest.get(sid)
        if not f:
            return None
        if f not in self._shards:
            try:
                self._shards[f] = json.load(open(os.path.join(self.copies_dir, f), encoding='utf-8'))
            except Exception:
                self._shards[f] = {}
        return self._shards[f].get(sid)

    def compare(self, find, ftext, orig, otext):
        """the regroup's rule: text when both sides have it, else headline + author; None = cannot tell (stays Original)"""
        if ftext and otext:
            v = RR.text_verdict([RR.version(*ftext)], [RR.version(*otext)])
            if v is not None:
                return v
        ha = RR.headline_author(find, orig)
        if ha['verifiable']:
            return {'ok': ha['ok'], 'conf': 'medium', 'mode': 'headline+author', 'm': None}
        return None

    def reprint_check(self, rows, run_id):
        """A new find (Original row of this run) whose cleaned page passes the string-of-text rule against an Original in the
        sheet (or an earlier-ranked new find of this run) dated within +-7 days with overlapping headline words becomes a
        Reprint of that story; its own reprint rows follow it. Low-confidence passes (clutter / edge lines set aside) are
        converted and reported. A find that ranks before the existing Original in the originals order is reported only:
        the sheet's existing cells are never changed."""
        finds = [o for o in rows if (o.get('Original or reprint') or 'Original') == 'Original']
        if not finds:
            return rows
        if RR is None or CH is None:
            self.res['reprint_check'].append({'run': run_id, 'note': 'reprint_rule.py or clean_html.py not loaded: finds not checked'})
            return rows
        texts = {}
        for o in finds:
            pid = self.page_doc_id(o)
            chk = self.check_page(pid, o) if pid else None
            texts[id(o)] = RR.html_text(chk['html']) if chk and chk['verdict'] == 'ok' else None
        kept = []
        for o in sorted(finds, key=lambda x: RR.rank(x)):
            ft = texts[id(o)]
            best = None
            for c in RR.candidates(o, self.originals()) + RR.candidates(o, kept):
                if '_text' in c:
                    ot = c['_text']
                else:
                    h = self.copy_html(c['Story ID'])
                    ot = RR.html_text(h) if h else None
                v = self.compare(o, ft, c, ot)
                if v and v['ok']:
                    key = (v['conf'] == 'high', v['mode'] != 'headline+author', min(v['m']['raw']) if v.get('m') else 0)
                    if best is None or key > best[0]:
                        best = (key, c, v, ot is not None)
            if best is None:
                kept.append(dict(o, _text=ft))
                continue
            _, c, v, had = best
            ph, target = o.get('Story ID') or '', c['Story ID']
            for r2 in rows:
                if r2 is not o and ph and r2.get('Story ID') == ph:
                    r2['Story ID'] = target
            # the same story from an outlet the story already has (another link to the same article): not added
            same = {norm_outlet(self.s.get(x, 'Outlet')) for x in self.s.story_rows.get(target, [])} | {norm_outlet(c.get('Outlet'))}
            if norm_outlet(o.get('Outlet')) in same - {''}:
                o['_dup'] = True
                if ph and not self.real_sid(ph):
                    self.ids[ph] = target
                self.res['skipped'].append({'run': run_id, 'placeholder': o.get('Article ID', ''), 'story': ph, 'code': str(o.get('Tracker story code') or ''),
                                            'outlet': o.get('Outlet', ''), 'link': o.get('Publisher link', ''),
                                            'why': f"same story and outlet as {c.get('Article ID', '')} ({v['mode']}): another link to an article already in the sheet"})
                continue
            o.update({'Original or reprint': 'Reprint', 'Story ID': target, '_auto_reprint': True, '_ph_sid': ph})
            o.pop('# of reprints', None)
            e = {'run': run_id, 'placeholder': o.get('Article ID', ''), 'code': str(o.get('Tracker story code') or ''),
                 'outlet': o.get('Outlet', ''), 'link': o.get('Publisher link', ''), 'headline': o.get('Headline', ''),
                 'story': target, 'original': c.get('Article ID', ''), 'original_outlet': c.get('Outlet', ''),
                 'mode': v['mode'], 'conf': v['conf'],
                 'coverage': round(min(v['m'][{'text': 'raw', 'text-clutter': 'clut', 'text-edge': 'edge'}[v['mode']]]), 3) if v.get('m') else None}
            if v['conf'] == 'low':
                e['note'] = 'low confidence: passes only with clutter or edge lines set aside; check it'
            if RR.rank(o) < RR.rank(c):
                e['order'] = (f"under the originals order this find ({RR.tier(o)[1]}) would be the Original, not {c.get('Outlet', '')} "
                              f"({RR.tier(c)[1]}); the existing Original was kept (cells are never changed): Sammy to decide")
            self.res['reprint_check'].append(e)
        return [r for r in rows if not r.get('_dup')]

    def reach_for(self, outlet):
        """(consensus Reach of the outlet's rows in the sheet, [distinct values]); consensus = one tag set (order ignored)"""
        if self._reach is None:
            self._reach = {}
            for r in range(2, self.s.last_row + 1):
                v = norm_val(self.s.get(r, 'Reach'))
                if v:
                    d = self._reach.setdefault(norm_outlet(self.s.get(r, 'Outlet')), {})
                    k = frozenset(x.strip() for x in v.split(';') if x.strip())
                    d.setdefault(k, {}).setdefault(v, 0)
                    d[k][v] += 1
        d = self._reach.get(norm_outlet(outlet), {})
        if len(d) == 1:
            forms = next(iter(d.values()))
            return max(forms, key=lambda f: forms[f]), list(forms)
        return '', sorted(f for forms in d.values() for f in forms)

    def auto_fill_row(self, vals, obj, kind, sid, run_id, ph_aid):
        """new row: Reach from the outlet's consensus (else blank); Author 1..N + Author title from the byline"""
        if 'Reach' in self.s.col:
            cons, seen = self.reach_for(vals.get('Outlet'))
            prop = norm_val(vals.get('Reach'))
            vals['Reach'] = cons
            tags = lambda s: {x.strip() for x in str(s or '').split(';') if x.strip()}
            if prop and tags(prop) != tags(cons):
                self.res['reach'].append({'run': run_id, 'placeholder': ph_aid, 'outlet': vals.get('Outlet', ''), 'tracker': prop,
                                          'written': cons, 'why': 'the outlet’s Reach in the sheet' if cons else
                                          ('the outlet’s rows disagree: ' + ' | '.join(seen) if seen else 'outlet has no Reach in the sheet: left blank')})
        if 'Author 1' in self.s.col and _parse_byline and not blank(vals.get('Author / byline')):
            self.split_into(vals, kind, sid, vals.get('Outlet'), run_id, ph_aid)

    def split_into(self, vals, kind, sid, outlet, run_id, key):
        o = self.s.original_row(sid) if kind == 'Reprint' else None
        board = norm_val(self.s.get(o, 'Outlet')) if o else norm_val(outlet)   # editorial boards: the Original's outlet
        p = _parse_byline(str(vals.get('Author / byline')), board)
        n = sum(1 for c in self.s.col if re.fullmatch(r'Author \d+', str(c)))
        e = {'run': run_id, 'key': key, 'byline': norm_val(vals.get('Author / byline'))[:200], 'authors': p['authors'], 'title': p['title'],
             'confidence': p['confidence']}
        if len(p['authors']) > n:
            e['why'] = f'needs {len(p["authors"])} Author columns, the sheet has {n}: not written'
        else:
            for i, a in enumerate(p['authors'], 1):
                vals[f'Author {i}'] = a
            if p['title'] and 'Author title' in self.s.col:
                vals['Author title'] = p['title']
        self.res['authors_split'].append(e)

    def split_authors(self, r):
        """a byline written by the authors collection on an existing row: split it too (blank Author cells only)"""
        if 'Author 1' not in self.s.col or not _parse_byline:
            return
        vals = {'Author / byline': self.s.get(r, 'Author / byline')}
        self.split_into(vals, self.s.get(r, 'Original or reprint'), self.s.get(r, 'Story ID'), self.s.get(r, 'Outlet'), 'authors',
                        self.s.get(r, 'Article ID'))
        for c, v in vals.items():
            if c != 'Author / byline':
                self.fill(r, c, v, 'authors', self.s.get(r, 'Article ID'))

    def fill_counts(self, r, chk, pid):
        """Word count (CJK by character) and Mentions "Gabriel" in text (non-Latin forms too) of the saved, cleaned page"""
        if RR is not None:
            t = RR.html_text(chk['html'])[0].replace('\x01', ' ').replace('\x02', ' ')
        else:
            t = self.page_text(chk['html'])
        self.fill(r, 'Word count', CH.nwords(t), 'pages', pid)
        self.fill(r, 'Mentions "Gabriel" in text', 'Yes' if CH.gab_re(self.rules()).search(t) else 'No', 'pages', pid)

    def apply_bills(self):
        """bills the Update button's leginfo check found (run docs' bills_new) are appended to gabriel_bills_leginfo.json
        (--bills, the pipeline copy), once each (bill + session)"""
        new = [b for run in (self.db.get('runs') or {}).values() for b in ((run or {}).get('bills_new') or []) if isinstance(b, dict) and b.get('bill')]
        if not new:
            return
        if not self.bills_path:
            self.res['bills_note'] = f'{len(new)} new bills in run docs but no --bills file: not saved'
            return
        try:
            data = json.load(open(self.bills_path, encoding='utf-8'))
        except Exception as e:
            self.res['bills_note'] = f'could not read {self.bills_path}: {e!r}'
            return
        have = {(str(b.get('bill')), str(b.get('session', ''))[:9]) for b in data.get('rows', [])}
        for b in new:
            k = (str(b['bill']).strip(), str(b.get('session', ''))[:9])
            if k in have or not re.fullmatch(r'\d{4}-\d{4}', k[1]):
                continue
            have.add(k)
            row = {f: str(b.get(f, ''))[:400] for f in ('bill', 'leginfo_measure', 'session', 'title', 'role', 'status', 'url', 'source')}
            row['confirmed_leginfo'] = True
            row['source'] = row['source'] or f'leginfo (Update button, {self.today})'
            data.setdefault('rows', []).append(row)
            self.res['bills_new'].append(row)
        if self.res['bills_new']:
            json.dump(data, open(self.bills_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------- derived ----------'''



def patch_sheet_task(path):
    p = Patch(path, MARK['st'])
    p.rep('imports', "RETRY = 'RETRY – TinyFish'\n", ST_IMPORTS)
    p.rep('res keys', "'skipped': [], 'pages_error': [], 'pages_skipped': [], 'pages_flagged': [], 'press_releases': []}",
          "'skipped': [], 'pages_error': [], 'pages_skipped': [], 'pages_flagged': [], 'press_releases': [],\n"
          "                    # AUTO-v1: finds turned into reprints, reach and author fills, unclear Gabriels, bills from leginfo\n"
          "                    'reprint_check': [], 'reach': [], 'authors_split': [], 'gabriel_unclear': [], 'bills_new': []}")
    p.rep('state', "        self.page_checks = {}     # CLEAN-v1: page doc id -> clean/check result (cached)\n",
          "        self.page_checks = {}     # CLEAN-v1: page doc id -> clean/check result (cached)\n"
          "        # AUTO-v1: page doc -> the reprint row a find became; tracker copies (--copies); bills file (--bills); caches\n"
          "        self.page_target, self.copies_dir, self.bills_path = {}, None, None\n"
          "        self._rules = self._origs = self._reach = self._manifest = None\n"
          "        self._shards = {}\n")
    p.rep('drop_skipped', """            elif (obj.get('Original or reprint') or 'Original') == 'Original' and CH is not None:
                pid = self.page_doc_id(obj)
                chk = self.check_page(pid, obj) if pid else None
                if chk and chk['verdict'] == 'skip':
                    why = chk['reason']
""", """            elif CH is not None and hasattr(CH, 'skip_url') and CH.skip_url(obj.get('Publisher link'), self.rules()):   # AUTO-v1
                why = 'database, results or listing page: never added (DECISIONS 2026-10-27)'
            elif (obj.get('Original or reprint') or 'Original') == 'Original' and CH is not None:
                pid = self.page_doc_id(obj)
                chk = self.check_page(pid, obj) if pid else None
                if chk and chk['verdict'] == 'skip':
                    why = chk['reason']
                elif chk and hasattr(CH, 'jesse_check') and (chk['verdict'] == 'ok' or chk['reason'].startswith('no Gabriel')):
                    why = self.wrong_gabriel(chk, obj, run_id)   # AUTO-v1: Jesse Gabriel only
""")
    p.rep('apply_runs', "            rows = self.drop_skipped(rows, run_id)   # CLEAN-v1: californiafiles.org; Gabriel only outside the article\n",
          "            rows = self.drop_skipped(rows, run_id)   # CLEAN-v1: californiafiles.org; Gabriel only outside the article\n"
          "            rows = self.reprint_check(rows, run_id)   # AUTO-v1: new finds that are reprints of a story by text\n")
    p.rep('add_row fills', "        if 'Press release' in self.s.col and is_press_release(vals):   # CLEAN-v1\n",
          "        self.auto_fill_row(vals, obj, kind, sid, run_id, ph_aid)   # AUTO-v1: Reach (outlet consensus), Author 1..N + title\n"
          "        if 'Press release' in self.s.col and is_press_release(vals):   # CLEAN-v1\n")
    p.rep('add_row page target', "        self.touched_stories.add(sid)\n        return aid\n",
          "        self.touched_stories.add(sid)\n"
          "        if obj.get('_auto_reprint'):   # AUTO-v1: the find's saved page belongs to this reprint row, not the story's Original\n"
          "            for k in re.findall(r'jg-[0-9a-f]{6}', str(obj.get('Tracker story code') or '').lower()) + [ph_aid, obj.get('_ph_sid') or '']:\n"
          "                if k:\n"
          "                    self.page_target[k] = aid\n"
          "        return aid\n")
    p.rep('apply_authors', "                self.fill(r, 'Author / byline', (a or {}).get('author', ''), 'authors', sid)\n",
          "                if self.fill(r, 'Author / byline', (a or {}).get('author', ''), 'authors', sid) == 'written':\n"
          "                    self.split_authors(r)   # AUTO-v1\n")
    p.rep('pages target', "            target = self.norm_id(self.ids.get(pid, pid))\n",
          "            target = self.norm_id(self.page_target.get(pid) or self.ids.get(pid, pid))   # AUTO-v1: finds that became reprints\n")
    p.rep('pages blocked', "                self.fill(r, 'File name', RETRY, 'pages', pid)\n",
          "                self.fill(r, 'File name', BLOCKED if chk['reason'] in getattr(CH, 'BLOCKED_REASONS', ()) else RETRY, 'pages', pid)   # AUTO-v1\n")
    p.rep('pages counts', "            self.fill(r, 'File name', fname, 'pages', pid)\n",
          "            self.fill(r, 'File name', fname, 'pages', pid)\n"
          "            self.fill_counts(r, chk, pid)   # AUTO-v1: Word count (CJK by character), Mentions \"Gabriel\" (any script)\n")
    p.rep('methods', "\n    # ---------- derived ----------", ST_METHODS)
    p.rep('run', "        self.apply_pages(pages_dir)\n        self.recount()\n",
          "        self.apply_pages(pages_dir)\n        self.apply_bills()   # AUTO-v1\n        self.recount()\n")
    p.rep('argparse', "    ap.add_argument('--idmap', help='idmap.json from build_data.py (old code -> Story ID), optional fallback')\n",
          "    ap.add_argument('--idmap', help='idmap.json from build_data.py (old code -> Story ID), optional fallback')\n"
          "    ap.add_argument('--copies', help='folder holding the tracker\\'s articles/manifest.json + articles/<year>.json (AUTO-v1 reprint check)')\n"
          "    ap.add_argument('--bills', help='gabriel_bills_leginfo.json to append new bills to (AUTO-v1; the pipeline copy)')\n")
    p.rep('task args', "    if a.idmap:\n",
          "    task.copies_dir, task.bills_path = a.copies, a.bills   # AUTO-v1\n    if a.idmap:\n")
    p.rep('counts', "                          'press_releases': len(res['press_releases'])})\n",
          "                          'press_releases': len(res['press_releases'])})\n"
          "    res['counts'].update({'reprint_check': sum(1 for x in res['reprint_check'] if x.get('mode')),   # AUTO-v1\n"
          "                          'reprint_check_low': sum(1 for x in res['reprint_check'] if x.get('conf') == 'low'),\n"
          "                          'reprint_check_order': sum(1 for x in res['reprint_check'] if x.get('order')),\n"
          "                          'gabriel_unclear': len(res['gabriel_unclear']), 'reach_changed': len(res['reach']),\n"
          "                          'authors_split': len(res['authors_split']), 'bills_new': len(res['bills_new'])})\n")
    p.rep('sheet line', "    res['sheet_stories'] = stories\n",
          "    # AUTO-v1: the line names the new kinds of skips and placeholders, reprints found by text and new bills\n"
          "    res['sheet_line'] = (res['sheet_line'].replace('(California Files or Gabriel only outside the article)',\n"
          "                                                   '(California Files, listing pages, other Gabriels or Gabriel only outside the article)')\n"
          "                         .replace('(RETRY – TinyFish)', '(RETRY or BLOCKED – TinyFish)'))\n"
          "    _x = ((f\", {res['counts']['reprint_check']} finds written as reprints (same text as another story)\" if res['counts']['reprint_check'] else '')\n"
          "          + (f\" ({res['counts']['reprint_check_low']} low confidence, see review)\" if res['counts']['reprint_check_low'] else '')\n"
          "          + (f\", {len(res['bills_new'])} new bills from leginfo\" if res['bills_new'] else ''))\n"
          "    if _x:\n"
          "        res['sheet_line'] = res['sheet_line'][:-1] + _x + '.'\n"
          "    res['sheet_stories'] = stories\n")
    return p


# ===================================================================================== tracker JS
JS_BILLS = r'''/* AUTO-v1 tracker (agent-code, 2026-10-27): Gabriel's bills from leginfo (gabriel_bills_leginfo.json, embedded by build_data.py /
   assemble.py as <script id="billsinfo">, plus bills the Update button's leginfo check adds). Bills he authored (author, co-lead)
   are "his": BILL_INFO, the bill searches and the screening prompt use only those. Coauthored bills keep their name, marked
   "(coauthored)". The hand list below is only the fallback when the block is missing. */
const BILL_FALLBACK = __FALLBACK__;
const BILL_ROWS = (() => { try { const e = typeof document !== 'undefined' && document.getElementById('billsinfo'); const j = e ? JSON.parse(e.textContent) : null;
  if (j && Array.isArray(j.rows) && j.rows.length) return j.rows.filter(b => b && b.bill); } catch(e){} return BILL_FALLBACK.map(b => ({ bill: b.bill, session: b.session, title: b.name, role: 'author' })); })();
const billSess = s => { const m = String(s || '').match(/^(\d{4})-(\d{2})?(\d{2})/); return m ? `${m[1]}-${m[3]}` : String(s || ''); };
const billAuthored = b => /^author/i.test(String(b.role || ''));
const billTitle = b => String(b.title || b.name || '').trim().replace(/\.$/, '');
let BILL_INFO = [], BILL_NAMES = {}, BILL_ROLE = {};
function setBills(){
  BILL_INFO = BILL_ROWS.filter(billAuthored).map(b => ({ bill: b.bill, session: billSess(b.session), name: billTitle(b) }));
  // bill numbers restart each session: the authored bill wins, then the latest session
  const best = new Map();
  BILL_ROWS.slice().sort((a, b) => (billAuthored(a) - billAuthored(b)) || String(a.session).localeCompare(String(b.session))).forEach(b => best.set(b.bill, b));
  BILL_NAMES = {}; BILL_ROLE = {};
  best.forEach((b, k) => { BILL_NAMES[k] = billTitle(b) + (billAuthored(b) ? '' : ' (coauthored)'); BILL_ROLE[k] = billAuthored(b) ? 'author' : 'coauthor'; });
}
setBills();
// his bills for the screening prompt: the current and previous sessions, plus any bill the log already tags
function billList(){
  const yr = +String(TODAY).slice(0, 4), s0 = yr - (yr % 2 ? 0 : 1) - 2, tagged = new Set(); D.forEach(r => (r.bills || []).forEach(b => tagged.add(b)));
  return BILL_INFO.filter(b => +b.session.slice(0, 4) >= s0 || tagged.has(b.bill)).map(b => `${b.bill} (${b.session}, ${b.name})`).join('; ');
}
const billName = b => BILL_NAMES[b] || '';
'''

JS_REACH = r'''/* AUTO-v1 tracker: a new row's Reach = the outlet's Reach in the log when all its stories agree (tags in any order), else blank.
   Stories added by updates since the last rebuild don't count (their reach is Claude's guess). */
const REACH_BASE = new Set(D.map(r => r.id));
function covReach(name){
  const k = nrmName(String(name || '').replace(/\s*\([^)]*\)\s*$/, '')); if (!k) return '';
  const seen = new Map();
  D.forEach(r => { if (!REACH_BASE.has(r.id)) return; const t = Array.isArray(r.reach) ? r.reach.filter(Boolean) : String(r.reach || '').split(/;\s*/).filter(Boolean); if (!t.length) return;
    if (nrmName(r.pub) === k || nrmName(String(r.outlet || '').replace(/\s*\([^)]*\)\s*$/, '')) === k){ const key = t.slice().sort().join('|'); if (!seen.has(key)) seen.set(key, t.join('; ')); } });
  return seen.size === 1 ? [...seen.values()][0] : '';
}
function covRow(base){'''

JS_LEGINFO = r'''/* AUTO-v1 tracker: leginfo check (approach from work/out/leginfo_tinyfish_probe.md). One TinyFish fetch_content per Update run
   of leginfo's author search for the current session (the "Authored Bills" link on his Assembly page): live (ttl 0), the
   #bill_results table only, one retry when TinyFish reports the page bot-blocked, and 0 rows counts as a failure. The search
   lists only bills where he is the first-listed lead author (regular and extraordinary sessions); co-lead and coauthored
   bills can't be discovered this way and come only from the embedded list. Bills not in the list are added to the tracker's
   bill list and saved in the run log ("bills_new"); the sheet task appends them to pipeline/gabriel_bills_leginfo.json so they
   persist across rebuilds. Any failure: "leginfo check skipped". */
const LEGINFO_SEARCH = key => `https://leginfo.legislature.ca.gov/faces/billSearchClient.xhtml?session_year=${key}&house=Both&author=Gabriel&lawCode=All`;
function leginfoSession(today){ const y = +String(today).slice(0, 4), a = y % 2 ? y : y - 1; return { key: `${a}${a + 1}`, label: `${a}-${a + 1}` }; }
const legBill = m => /^[A-Z]+X\d+-\d+$/.test(m) ? m : m.replace(/^([A-Z]+)-(\d+)$/, '$1 $2');
const legOrd = n => n + (['th', 'st', 'nd', 'rd'][(n % 100 > 10 && n % 100 < 14) ? 0 : n % 10] || 'th');
function leginfoParse(md, s){
  const out = [];
  String(md || '').split('\n').forEach(l => {
    const c = l.split('|').map(x => x.replace(/\[([^\]]*)\]\([^)]*\)/g, '$1').trim()); if (c.length < 5 || !/^[A-Z]+(X\d+)?-\d+$/.test(c[1]) || !/gabriel/i.test(c[3])) return;
    const m = c[1].match(/^([A-Z]+?)(?:X(\d+))?-(\d+)$/);
    out.push({ bill: legBill(c[1]), leginfo_measure: c[1], session: s.label + (m[2] ? ` (${legOrd(+m[2])} Ex. Sess.)` : ''), title: c[2], role: 'author', status: c[4],
      url: `https://leginfo.legislature.ca.gov/faces/billStatusClient.xhtml?bill_id=${s.key}${m[2] || '0'}${m[1]}${m[3]}` });
  });
  return out;
}
function leginfoNew(found){
  const key = b => String(b.bill) + '|' + String(b.session || '').slice(0, 9), have = new Set(BILL_ROWS.map(key)), seen = new Set();
  return found.filter(b => { const k = key(b); if (have.has(k) || seen.has(k)) return false; seen.add(k); return true; });
}
async function leginfoFetch(mcp, url){
  const inp = { urls: [url], format: 'markdown', links: false, include_selectors: ['#bill_results'], ttl: 0, per_url_timeout_ms: 90000, image_links: false, iframe_links: false, page_metadata: false };
  for (let k = 0; k < 2; k++){
    const p = tfPayload(await tfCall(mcp, 'fetch_content', inp));
    const r = ((p && p.results) || [])[0];
    if (r && r.text) return String(r.text);
    const er = ((p && p.errors) || []).map(e => String((e && (e.error || e.code || e.message)) || '')).join(' ');
    if (!/bot|block/i.test(er) || k) throw new Error(er || 'no page');
    await new Promise(r2 => setTimeout(r2, 3000));   // bot_blocked: one retry
  }
}
async function leginfoCheck(mcp){
  U.newbills = []; U.leginfo = '';
  const s = leginfoSession(TODAY);
  try {
    await new Promise(r => setTimeout(r, 1500));   // politely: one request per run, after the searches
    const found = leginfoParse(await leginfoFetch(mcp, LEGINFO_SEARCH(s.key)), s);
    if (!found.length) throw new Error('0 rows');   // an empty table is a failure, never "no bills"
    const add = leginfoNew(found).map(b => Object.assign(b, { source: `leginfo author search (Update button, ${TODAY})`, confirmed_leginfo: true }));
    add.forEach(b => BILL_ROWS.push(b)); if (add.length) setBills();
    U.newbills = add;
    U.leginfo = `leginfo: ${pl(found.length, 'bill')} of his in ${s.label}, ${add.length ? pl(add.length, 'new bill') + ' added (' + add.map(b => b.bill).join(', ') + ')' : 'none new'}`;
  } catch(e){
    U.leginfo = 'leginfo check skipped';
    try { console.warn('leginfo check skipped', e); } catch(_){}
  }
}
async function runUpdate(){'''


def skip_urls_js():
    """the cheap URL-based skips (clean_rules.json skip_urls: database, results and listing pages) as a JS list"""
    import json
    rules = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clean_rules.json'), encoding='utf-8'))
    out = []
    for pat in rules.get('skip_urls', []):
        fl = 'i' if pat.startswith('(?i)') else ''
        src = pat[4:] if fl else pat
        out.append('new RegExp(' + json.dumps(src) + (', ' + json.dumps(fl) if fl else '') + ')')
    return ('/* AUTO-v1 tracker: listing pages never searched (bill trackers, election results, donor / Form 700 pages; from\n'
            '   code/clean_rules.json skip_urls, the same list the sheet task applies) */\n'
            'const TF_SKIP_URLS = [' + ', '.join(out) + '];\n')


def patch_js(path):
    p = Patch(path, MARK['js'])
    t = p.t
    a = t.find('const BILL_INFO = [')
    z = t.find("const billName = b => BILL_NAMES[b] || '';")
    if not p.skip:
        if a < 0 or z < 0 or z < a:
            p.bad.append('tracker: BILL_INFO block not found')
        else:
            line = t[a:t.index('\n', a)]
            fallback = line[len('const BILL_INFO = '):].rstrip(';')
            old = t[a:z + len("const billName = b => BILL_NAMES[b] || '';")]
            p.rep('bills block', old, JS_BILLS.replace('__FALLBACK__', fallback).rstrip('\n'))
    p.rep('bill list prompt', 'His bills, with the session each was introduced in: ${BILL_LIST}.',
          'His bills, with the session each was introduced in: ${billList()}.')
    p.rep('reach fn', 'function covRow(base){', JS_REACH)
    p.rep('reach original', "'Medium': r.media || '', 'Reach': r.reach || '',", "'Medium': r.media || '', 'Reach': covReach(r.pub || r.outlet),")
    p.rep('reach reprint', "'Outlet': covOutletName(p.outlet), 'Outlet county': covCounty(p.outlet),",
          "'Outlet': covOutletName(p.outlet), 'Outlet county': covCounty(p.outlet), 'Reach': covReach(p.outlet),")
    p.rep('blocked row', "'Publisher link': r.link || '', 'Link status': 'Publisher URL', 'Tracker story code': r.id }));",
          "'Publisher link': r.link || '', 'Link status': 'Publisher URL', 'Tracker story code': r.id,\n"
          "      'File name': r._blocked ? 'BLOCKED – TinyFish' : '', 'Saved Copy?': r._blocked ? 'No' : '' }));   /* AUTO-v1: paywall/login/bot wall */")
    p.rep('skip urls', "if (SKIP_HOSTS.test(hostOf(c.url)) || TF_NOT_NEWS.test(c.url) ||",
          "if (SKIP_HOSTS.test(hostOf(c.url)) || TF_SKIP_URLS.some(x => x.test(c.url)) /* AUTO-v1: listing pages */ || TF_NOT_NEWS.test(c.url) ||")
    p.rep('blocked flag', "          if (stub) U.paywalled++;\n", "          if (stub){ U.paywalled++; c.blocked = true; }   /* AUTO-v1 */\n")
    p.rep('fetch errors', "        const pages = tfResults(tfPayload(await tfCall(mcp, 'fetch_content', tfFetchInput(batch.map(c => c.url)))));\n"
          "        batch.forEach(c => { const r = pages.get(normU(c.url)); if (!r) return; U.opened++;\n",
          "        const pl0 = tfPayload(await tfCall(mcp, 'fetch_content', tfFetchInput(batch.map(c => c.url)))), pages = tfResults(pl0), errs = tfErrors(pl0);   /* AUTO-v1 */\n"
          "        batch.forEach(c => { const r = pages.get(normU(c.url));\n"
          "          if (!r){ const er = errs.get(normU(c.url)); if (er && TF_BLOCKED_ERR.test(er)){ c.blocked = true; U.paywalled++; } return; }   /* AUTO-v1: login_required, bot wall */\n"
          "          U.opened++;\n")
    p.rep('stub phrases', "const TF_STUB = /subscribe to (continue|read)|already a subscriber|sign in to (continue|read)|create a free account to|verify you are human|access denied|just a moment|enable javascript and cookies/i;",
          "const TF_STUB = /subscribe to (continue|read)|already a subscriber|sign in to (continue|read)|create a free account to|verify you are human|access denied|just a moment|enable javascript and cookies|subscriber\\? click here to log ?in|log ?in\\/register your account/i;\n"
          "/* AUTO-v1 tracker: TinyFish fetch errors that mean the site blocked us or wants a login (BLOCKED – TinyFish), from errors[] */\n"
          "const TF_BLOCKED_ERR = /login|paywall|subscri|bot|blocked|captcha|forbidden|access denied|\\b40[13]\\b/i;\n"
          + skip_urls_js() +
          "function tfErrors(p){ const m = new Map(); ((p && p.errors) || []).forEach(e => { if (e && e.url) m.set(normU(e.url), String(e.error || e.message || e.code || '')); }); return m; }")
    p.rep('blocked carry', "r._page = c.page || null;", "r._page = c.page || null; r._blocked = !!c.blocked && !c.page; /* AUTO-v1 */")
    p.rep('leginfo fn', 'async function runUpdate(){', JS_LEGINFO)
    p.rep('leginfo call', "    await verifyReprints(mcp);\n",
          "    await verifyReprints(mcp);\n"
          "    if (!U.ctl.signal.aborted){ U.step = 'Checking leginfo for new bills of his'; drawProg(); await leginfoCheck(mcp); }   /* AUTO-v1 */\n")
    p.rep('run doc', "rows: covCompact(RA.rows || []),\n      left: mode === 'find'",
          "rows: covCompact(RA.rows || []),\n"
          "      bills_new: mode === 'find' ? (U.newbills || []).slice(0, 50) : [], leginfo: mode === 'find' ? VS(U.leginfo || '', 300) : '',   /* AUTO-v1 */\n"
          "      left: mode === 'find'")
    p.rep('fire on bills', "if (mode === 'find' && !RA.added.length && !RA.reprints){",
          "if (mode === 'find' && !RA.added.length && !RA.reprints && !(U.newbills || []).length){   /* AUTO-v1: new bills go to the sheet task too */")
    p.rep('find note', "`${pl(nf,'new story','new stories')} found` + (nrp ? `, and ${pl(nrp,'reprint')} of stories already in the log` : ''));",
          "`${pl(nf,'new story','new stories')} found` + (nrp ? `, and ${pl(nrp,'reprint')} of stories already in the log` : '') + (U.leginfo ? `. ${U.leginfo}` : ''));")
    p.rep('about', 'Then the spreadsheet and this tracker are updated.</p>',
          'It also reads leginfo’s list of his bills for the current session and adds any the tracker doesn’t list yet. Then the spreadsheet and this tracker are updated.</p>')
    p.rep('marker', "/* CLEAN-v1 loader end */", "/* CLEAN-v1 loader end */\n" + MARK['js'])
    return p


# ===================================================================================== prompt, assemble, build_data
def patch_prompt(path):
    p = Patch(path, MARK['pr'])
    p.rep('files', "  - `pipeline/author_canon.csv` (same-person author names Sammy merged; build_data.py reads it from its own folder)  <!-- AUTHOR-CANON -->\n",
          "  - `pipeline/author_canon.csv` (same-person author names Sammy merged; build_data.py reads it from its own folder)  <!-- AUTHOR-CANON -->\n"
          "  - `pipeline/reprint_rule.py` (the regroup's string-of-text reprint rule; sheet_task.py imports it)  <!-- AUTO-v1 -->\n"
          "  - `pipeline/gabriel_bills_leginfo.json` (Gabriel's bills from leginfo; build_data.py embeds it, sheet_task.py appends new bills to it)\n")
    p.rep('command', "--pages-dir pages --today <YYYY-MM-DD>", "--pages-dir pages --copies copies --bills gabriel_bills_leginfo.json --today <YYYY-MM-DD>")
    p.rep('copies', "It is only a fallback: old codes are matched against the sheet's Tracker story code first.\n",
          "It is only a fallback: old codes are matched against the sheet's Tracker story code first.\n\n"
          "   `--copies copies`: before running, read the tracker's `articles/manifest.json` (Artifact read with `path`) into `copies/articles/`, "
          "and the `articles/<year>.json` files for the years of each new find's date (±7 days; usually one or two files). sheet_task.py compares "
          "each new find's cleaned page with the saved copies of Originals dated within 7 days whose headlines share words, by the regroup's rule "
          "(runs of 25+ identical words covering 90% of both texts). A find that passes becomes a Reprint row of that story; with no copy on "
          "either side the headline + author rule decides, else the find stays an Original. `--bills` is the pipeline copy of "
          "`gabriel_bills_leginfo.json`: bills the Update button's leginfo check found (run docs' `bills_new`) are appended to it.\n")
    p.rep('check', "Report both counts in `sheet.line` (sheet_task.py's line already does).\n",
          "Report both counts in `sheet.line` (sheet_task.py's line already does).\n"
          "   - AUTO-v1 (DECISIONS 2026-10-27): `result.skipped` also lists database/results/listing pages (bill trackers, election results, "
          "donor and Form 700 pages) and pages that name only another Gabriel (Ugarte, Petek, San Gabriel …) or no Gabriel in any script. "
          "Pages behind a paywall, a login or a bot wall get File name `BLOCKED – TinyFish` instead of `RETRY – TinyFish`. "
          "`result.reprint_check` lists finds written as Reprints of an existing story (`conf: low` = passed only with clutter or edge lines set "
          "aside; `order` = the find would rank before the existing Original, which was kept). `result.reach` lists new rows whose Reach "
          "differs from the tracker's guess (the outlet's Reach in the sheet when all its rows agree, else blank); `result.authors_split` the "
          "Author 1..N / Author title fills; `result.gabriel_unclear` finds kept with a bare \"Gabriel\". Saved pages also fill Word count "
          "(Chinese/Japanese/Korean counted by character) and Mentions \"Gabriel\" in text (other scripts count).\n")
    p.rep('newbills', "`line` = `result.sheet_line`.",
          "`line` = `result.sheet_line`. `newbills` = the `bill` of each row in `result.bills_new`.")
    p.rep('review', "   - Add `result.skipped`, `result.pages_error` and `result.pages_flagged` to the run doc's `review`",
          "   - Add `result.skipped`, `result.pages_error`, `result.pages_flagged`, `result.reprint_check`, `result.reach` and `result.gabriel_unclear` to the run doc's `review`")
    p.rep('publish', "Keep the existing files.",
          "Keep the existing files. When `result.bills_new` is not empty, also publish the updated `gabriel_bills_leginfo.json` as "
          "`pipeline/gabriel_bills_leginfo.json`, so the new bills survive the next rebuild.")
    return p


def patch_assemble(path):
    # CLEAN-v1's own markers (patch_clean.py) stay intact so both patches keep re-running cleanly
    p = Patch(path, MARK['asm'])
    p.rep('drop', "for n in ('rows', 'idmap', 'covcols', 'cleanrules'):   # CLEAN-v1",
          "for n in ('billsinfo', 'rows', 'idmap', 'covcols', 'cleanrules'):   # CLEAN-v1")
    p.rep('load', "if os.path.exists(f'{BLK}/cleanrules.json'): blocks['cleanrules'] = open(f'{BLK}/cleanrules.json', encoding='utf-8').read()\n",
          "if os.path.exists(f'{BLK}/cleanrules.json'): blocks['cleanrules'] = open(f'{BLK}/cleanrules.json', encoding='utf-8').read()\n"
          "if os.path.exists(f'{BLK}/billsinfo.json'): blocks['billsinfo'] = open(f'{BLK}/billsinfo.json', encoding='utf-8').read()   # AUTO-v1: his bills (leginfo)\n"
          "blocks.pop('cleanrules', None)   # CLEAN-v2: the tracker no longer cleans pages, so it doesn't carry the rules\n")
    p.rep('emit', "for n in ('rows', 'idmap', 'covcols', 'cleanrules') if n in blocks)\n",
          "for n in ('rows', 'idmap', 'covcols', 'cleanrules') if n in blocks)\n"
          "extra += ''.join(f'\\n<script id=\"{n}\" type=\"application/json\">{esc(blocks[n])}</script>' for n in ('billsinfo',) if n in blocks)   # AUTO-v1 assemble\n")
    return p


def patch_build_data(path):
    p = Patch(path, MARK['bd'])
    p.rep('bills', "report.update({'rows': len(rows), 'idmap'",
          "# AUTO-v1 build_data: Gabriel's bills (gabriel_bills_leginfo.json next to this script, with the bills the sheet task appended\n"
          "# from the Update button's leginfo check) go into the page as <script id=\"billsinfo\">\n"
          "_bl = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gabriel_bills_leginfo.json')\n"
          "if os.path.exists(_bl):\n"
          "    dump('billsinfo', {'rows': [{k: b.get(k, '') for k in ('bill', 'session', 'title', 'role', 'status')}\n"
          "                            for b in json.load(open(_bl, encoding='utf-8')).get('rows', []) if b.get('bill')]})\n"
          "report.update({'rows': len(rows), 'idmap'")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description='AUTO-v1 patches')
    ap.add_argument('--js'); ap.add_argument('--sheet-task'); ap.add_argument('--prompt')
    ap.add_argument('--assemble'); ap.add_argument('--build-data')
    a = ap.parse_args(argv)
    ps = []
    if a.js: ps.append(patch_js(a.js))
    if a.sheet_task: ps.append(patch_sheet_task(a.sheet_task))
    if a.prompt: ps.append(patch_prompt(a.prompt))
    if a.assemble: ps.append(patch_assemble(a.assemble))
    if a.build_data: ps.append(patch_build_data(a.build_data))
    if not all([p.ready() for p in ps]):
        print('NOT applied (nothing written):', *[b for p in ps for b in p.bad], sep='\n  ')
        return 1
    for p in ps:
        p.save()
    for p in ps:
        print(os.path.basename(p.path) + ':', 'AUTO-v1', ', '.join(p.done))
    return 0


if __name__ == '__main__':
    sys.exit(main())
