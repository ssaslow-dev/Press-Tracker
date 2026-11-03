/* STATIONNAMES (LIBFILES-v1 follow-up 2): the station names every file in the update folder by the library's schema (CONTRACT.md NAMING-v2).
   Pure functions, no DOM; inlined into the station page and run by node in tests/names_test.js.

   Saved copies   <ws|nb|pq><Article ID><o|r>[-s<Story ID>].<html|pdf>     in  <year>/
   Raw pages      the same name                                            in  _original_html/<year>/
   ProQuest PDFs  pq<Article ID><o|r>-s<Story ID>.pdf                      in  _original_pdf/<year>/
   NewsBank PDFs  nb<Article ID><o|r>-s<Story ID>.pdf  (the saved copy)    in  <year>/
   Releases       pr<Release ID>.html in  Press releases/<year>/   and the raw page in  _original_html/Press releases/<year>/

   The numbers are the next free ones from the for-Update file (rows.next: aid, s, pr), handed out the way the PC save hands them out
   (sheet_task.apply_runs / add_row): runs in the order of their `at`, inside a run the Originals first, then the Reprints, in row order; a new Original
   takes the next Story ID unless its Story ID is already a real one; one Article ID per row (Article IDs include the Print Article IDs: one sequence).
   Releases take the next Release IDs in (date, url) order. This is the station's best guess: the PC save checks every name and renames what it
   assigns differently (a number taken meanwhile, a find the duplicate check drops, an Original the text test makes a Reprint). */
(function (root) {
'use strict';
const pad = (n, w) => String(n).padStart(w, '0');
const REAL_SID = /^s\d{5,}$/;
const ymd = d => (/^\d{4}-\d{2}-\d{2}/.test(String(d || '')) ? String(d).slice(0, 10) : '');

/* the library year folder of a row: the date's year, else the Year column, else the year of the day the save runs (sheet_task.apply_pages) */
function yearOf(row, today) {
  const d = String(row.Date || '');
  if (/^\d{4}/.test(d)) return d.slice(0, 4);
  const y = String(row.Year == null ? '' : row.Year).slice(0, 4);
  return /^\d{4}$/.test(y) ? y : String(today || '').slice(0, 4);
}
function stem(fmt, aid, kind, sid) { return fmt + aid + (kind === 'Reprint' ? 'r' : kind === 'Original' ? 'o' : '') + (sid ? '-' + sid : ''); }
const NAME_RX = /^(ws|nb|pq)(\d{5,})([or]?)(?:-(s\d{5,}))?$/;
function parseStem(s) { const m = NAME_RX.exec(s || ''); return m ? { fmt: m[1], aid: m[2], kind: m[3], sid: m[4] || '' } : null; }

/* the pages document of a proposed row (sheet_task.page_doc_id) */
function pageDocId(obj, pages) {
  const has = k => k && Object.prototype.hasOwnProperty.call(pages, k);
  const keys = [String(obj._page || '')];
  const own = (obj['Original or reprint'] || 'Original') === 'Original' || obj._auto_reprint;
  if (own) (String(obj['Tracker story code'] || '').toLowerCase().match(/jg-[0-9a-f]{6}/g) || []).forEach(k => keys.push(k));
  keys.push(obj['Article ID'] || '', own ? (obj._ph_sid || obj['Story ID'] || '') : '');
  return keys.find(k => has(k)) || '';
}
const libName = (sub, year, name) => 'library/' + (sub ? sub + '/' : '') + year + '/' + name;

/* opts: { next:{aid,s,pr}, runs:[{id, at, rows:[...], releases_new:[...]}], pages:{id: doc}, today:'YYYY-MM-DD', storyOfCode:(code)=>sid|'', existingStories:Set }
   returns { items:[...], releases:[...], used:{aid,s,pr} (the first free numbers after this update), files:[{path, kind:'html'|'pdf', text?, pdfFor?, doc}] } */
function plan(opts) {
  const next = opts.next || {}, pages = opts.pages || {}, today = opts.today || '';
  let aid = Number(next.aid) || 1, sNo = Number(next.s) || 1, pr = Number(next.pr) || 1;
  const items = [], files = [], ids = {}, existing = opts.existingStories || new Set(), taken = new Set();
  const sidOf = ph => { ph = String(ph || '').trim(); if (ids[ph]) return ids[ph]; if (REAL_SID.test(ph)) return ph; if (opts.storyOfCode && /^jg-[0-9a-f]{6}$/i.test(ph)) return opts.storyOfCode(ph.toLowerCase()) || ''; return ''; };
  const runs = (opts.runs || []).slice().sort((a, b) => String(a.at || '').localeCompare(String(b.at || '')));
  for (const run of runs) {
    const rows = run.rows || [];
    for (const kind of ['Original', 'Reprint']) rows.forEach((obj, ri) => {
      if ((obj['Original or reprint'] || 'Original') !== kind) return;
      let sid;
      if (kind === 'Original') {
        const ph = String(obj['Story ID'] || '').trim();
        sid = ids[ph];
        if (!sid) {
          sid = REAL_SID.test(ph) && !existing.has(ph) && !taken.has(ph) ? ph : 's' + pad(sNo++, 5);
          if (ph && !REAL_SID.test(ph)) ids[ph] = sid;
        }
        taken.add(sid);
      } else {
        sid = sidOf(obj['Story ID']);
        if (!sid) { items.push({ run: run.id, row: ri, doc: '', aid: pad(aid++, 5), sid: '', kind: 'r', fmt: '', year: '', skipped: 'a reprint of a story the station cannot place' }); return; }
      }
      const a = pad(aid++, 5);
      const doc = pageDocId(obj, pages), d = doc ? pages[doc] : null;
      const fmt = d && d.nb ? 'nb' : d && d.pq ? 'pq' : 'ws', year = yearOf(obj, today);
      const it = { run: run.id, row: ri, doc, aid: a, sid, kind: kind === 'Reprint' ? 'r' : 'o', fmt, year, copy: '', raw: '', pdf: '', pdf_for: '' };
      if (d) {
        const st = stem(fmt, a, kind, sid);
        if (fmt === 'nb') {
          if (d.nb.file) { it.copy = libName('', year, st + '.pdf'); it.pdf_for = String(d.nb.file); files.push({ path: it.copy, kind: 'pdf', pdfFor: it.pdf_for, doc }); }
        } else if (fmt === 'pq') {
          const t = String(d.clean || ''); if (t.trim()) { it.copy = libName('', year, st + '.html'); files.push({ path: it.copy, kind: 'html', text: t, doc }); }
          if (d.pq.file) { it.pdf = libName('_original_pdf', year, st + '.pdf'); it.pdf_for = String(d.pq.file); files.push({ path: it.pdf, kind: 'pdf', pdfFor: it.pdf_for, doc }); }
        } else {
          const sc = String(d.scoped || ''), cl = String(d.clean || ''), t = sc.trim() ? sc : cl;
          if (t.trim()) {
            it.copy = libName('', year, st + '.html'); files.push({ path: it.copy, kind: 'html', text: t, doc });
            // the save keeps the page as fetched under _original_html whenever cleaning changed it, which is nearly always: the station names it too (the fullest page it holds)
            it.raw = libName('_original_html', year, st + '.html'); files.push({ path: it.raw, kind: 'html', text: cl.trim() ? cl : sc, doc });
          }
        }
      }
      items.push(it);
    });
  }
  // releases: the save takes them in (date, url) order, once per url, and gives each the next Release ID (a release with no text still takes its number)
  const rels = [], seen = new Set();
  for (const run of runs) for (const x of run.releases_new || []) if (x && typeof x === 'object' && /^https?:/.test(String(x.url || '')) && !seen.has(x.url)) { seen.add(x.url); rels.push(Object.assign({ _run: run.id }, x)); }
  rels.sort((a, b) => (ymd(a.date) + '|' + a.url < ymd(b.date) + '|' + b.url ? -1 : 1));
  const releases = [];
  for (const x of rels) {
    const d = ymd(x.date), caucus = x.src === 'caucus' || /jewishcaucus/.test(x.url);
    if (caucus && d && d < '2020-11-18') continue;     // the save skips these before it numbers them
    const id = 'pr' + pad(pr++, 5), year = d ? d.slice(0, 4) : String(today).slice(0, 4), body = String(x.html || x.text || '').trim();
    const it = { run: x._run, url: x.url, prid: id, year, copy: '', raw: '' };
    if (body) {
      const page = releasePage(x, d);
      it.copy = 'library/Press releases/' + year + '/' + id + '.html'; it.raw = 'library/_original_html/Press releases/' + year + '/' + id + '.html';
      files.push({ path: it.copy, kind: 'html', text: page, rel: id }, { path: it.raw, kind: 'html', text: page, rel: id });
    }
    releases.push(it);
  }
  return { items, releases, files, used: { aid, s: sNo, pr }, from_next: { aid: Number(next.aid) || 1, s: Number(next.s) || 1, pr: Number(next.pr) || 1 } };
}
const escH = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
function releasePage(x, d) {
  const body = String(x.html || '').trim() ? String(x.html) : String(x.text || '').split(/\n\s*\n/).map(p => p.trim()).filter(Boolean).map(p => '<p>' + escH(p) + '</p>').join('\n');
  return '<!doctype html><html><head><meta charset="utf-8"><title>' + escH(x.title) + '</title></head><body><div>' + escH(d) + '<br>' + escH(x.url) + '</div><h1>' + escH(x.title) + '</h1>\n<article>' + body + '</article>\n</body></html>';
}
/* the manifest's `names` block */
function manifestBlock(pl, today) {
  return { version: 1, today: today || '', from_next: pl.from_next,
    items: pl.items.filter(i => !i.skipped).map(i => ({ run: i.run, row: i.row, doc: i.doc, aid: i.aid, sid: i.sid, kind: i.kind, fmt: i.fmt, year: i.year, copy: i.copy, raw: i.raw, pdf: i.pdf, pdf_for: i.pdf_for })),
    releases: pl.releases.map(r => ({ run: r.run, url: r.url, prid: r.prid, year: r.year, copy: r.copy, raw: r.raw })) };
}
const api = { plan, manifestBlock, stem, parseStem, pageDocId, yearOf, releasePage };
if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.AJGNames = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
