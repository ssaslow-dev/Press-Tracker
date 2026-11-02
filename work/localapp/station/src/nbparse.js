/* NewsBank batch PDF reading (NEWSBANKPDF-v1): pure functions, no DOM, no pdf.js. Input is the text lines pdf.js reads from a batch PDF
   (page, baseline y in PDF coordinates, x, height, text); output is the stories in it with their page spans, bands and parsed details.
   Used by the Update station page (inlined) and by the node unit tests (module.exports). The layout rules come from the library's own
   NewsBank PDFs (code/extract_nb.py parse() and split_items(), which read the same "Multiple Articles" files by pdftotext):

     <headline, one or more lines>
     <Month D, YYYY> | <source>                       (other languages: "28 de octubre de 2026 | ...")
     Author: <name> Section: <section> <N> Words      (any part may be missing; "Page: <p>" may follow)
     OpenURL Link
     <body ...>
     <copyright line>                                 (print-page items put it after the citation)
     Citation (apa Style)
     <APA citation: Author, I. (YYYY, Month D). Headline.Outlet. Available from NewsBank: ...: https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=news/<16 hex>.>

   A story ends with the last line of its citation (docref=... and a final full stop); the next story starts on the next line. */
(function (root) {
'use strict';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const ES_MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
const MONTH_RX = MONTHS.join('|');
const DATE_EN = new RegExp('^(' + MONTH_RX + ') (\\d{1,2}), (\\d{4}) \\| ?(.*)$', 'i');
const DATE_ES = /^(\d{1,2}) de ([a-záéíóú]+) (?:del? )?(\d{4}) \| ?(.*)$/i;
const DATE_LOOSE = /^([^|]{3,40}\d{4}) \| ?(.*)$/;          // "Bills of 2023 | headline" kicker lines, odd date forms
const CIT_HEAD = /^citation\s*\(\s*apa\s+style\s*\)/i;
const COPY_RX = /^(©|copyright|\(c\)\s)/i;
const AUTH_RX = /Author:\s*(.*?)(?=\s+Section:|\s+\d[\d,]* Words|\s+Page:|$)/;
const SECT_RX = /Section:\s*(.*?)(?=\s+\d[\d,]* Words|\s+Page:|$)/;
const WORDS_RX = /(\d[\d,]*) Words/;
const PAGE_RX = /Page:\s*(\S+)/;

const squash = s => String(s == null ? '' : s).replace(/\s+/g, ' ').trim();
const pad = n => String(n).padStart(2, '0');
const iso = (y, m, d) => { const t = new Date(Date.UTC(+y, +m - 1, +d)); return t.getUTCFullYear() === +y && t.getUTCMonth() === +m - 1 && t.getUTCDate() === +d ? y + '-' + pad(m) + '-' + pad(d) : ''; };

/* ---- lines from pdf.js text items ---- */
/* items: pdf.js getTextContent().items for one page ({str, transform:[a,b,c,d,e,f], width, height, hasEOL}); returns lines top to bottom, each {y, x, h, text}.
   y is the baseline in PDF user space (origin bottom left). Items whose baselines are within 40% of the font height are one line. */
function linesFromItems(items) {
  const rows = [];
  for (const it of items || []) {
    if (!it || typeof it.str !== 'string' || !it.transform) continue;
    const y = it.transform[5], x = it.transform[4], h = Math.abs(it.height || it.transform[3] || 10) || 10;
    if (!it.str.trim() && !it.hasEOL) continue;
    let r = null;
    for (let i = rows.length - 1; i >= 0 && i >= rows.length - 6; i--) if (Math.abs(rows[i].y - y) <= Math.max(1.5, 0.4 * Math.min(h, rows[i].h))) { r = rows[i]; break; }
    if (!r) { r = { y, h, parts: [] }; rows.push(r); }
    r.parts.push({ x, w: it.width || 0, s: it.str }); r.h = Math.max(r.h, h);
  }
  rows.sort((a, b) => b.y - a.y);
  return rows.map(r => {
    r.parts.sort((a, b) => a.x - b.x);
    let t = '', end = null;
    for (const p of r.parts) {
      if (end !== null && t && !/\s$/.test(t) && !/^\s/.test(p.s) && p.x - end > Math.max(0.8, 0.12 * r.h)) t += ' ';
      t += p.s; end = p.x + p.w;
    }
    return { y: r.y, x: r.parts[0].x, h: r.h, text: t.replace(/\s+$/, '') };
  }).filter(l => l.text.trim());
}

/* ---- page furniture: a short line repeated in the top or bottom margin of most pages (running head, page counter) is not story text ---- */
function furnitureKeys(pages) {
  if (pages.length < 3) return new Set();
  const seen = new Map();
  for (const pg of pages) for (const l of pg.lines) {
    const fromTop = pg.height - l.y, fromBot = l.y;
    if (!(fromTop < 56 || fromBot < 44) || l.text.length > 60) continue;
    const k = (fromTop < 56 ? 'T' : 'B') + '|' + l.text.replace(/\d+/g, '#').trim();
    (seen.get(k) || seen.set(k, new Set()).get(k)).add(pg.page);
  }
  const out = new Set();
  seen.forEach((set, k) => { if (set.size >= 3 && set.size >= 0.5 * pages.length) out.add(k); });
  return out;
}

/* ---- split a batch into stories ----
   pages: [{page (1-based), height, lines: [{y, x, h, text}]}] top to bottom. Returns {stories, tail, furniture}. Every story gets
   firstPage, lastPage, top (PDF y of the top of its first line), bottom (PDF y of the bottom of its last line), sharedFirst / sharedLast
   (another story's text is on its first / last page), bands (what to keep on each page when the pages are shared), and its lines. */
function splitBatch(pages) {
  const fk = furnitureKeys(pages), seq = [];
  for (const pg of pages) for (const l of pg.lines) {
    const fromTop = pg.height - l.y;
    if (fk.has((fromTop < 56 ? 'T' : 'B') + '|' + l.text.replace(/\d+/g, '#').trim()) && (fromTop < 56 || l.y < 44)) continue;
    seq.push({ p: pg.page, H: pg.height, y: l.y, x: l.x, h: l.h, text: l.text });
  }
  const stories = []; let cur = 0, i = 0;
  while (i < seq.length) {
    if (CIT_HEAD.test(seq[i].text.trim())) {
      let j = i + 1, joined = '';
      const cit = [seq[i]];
      const rest = seq[i].text.trim().replace(CIT_HEAD, '').trim(); if (rest) joined = rest;
      for (; j < seq.length && j < i + 12; j++) {
        cit.push(seq[j]); joined = (joined + ' ' + seq[j].text).trim();
        if (/docref=/i.test(joined) && /\.\s*$/.test(joined.replace(/\s+/g, ' '))) { j++; break; }
        if (DATE_EN.test(seq[j].text.trim()) && j > i + 1) { cit.pop(); break; }
      }
      let end = j - 1;
      if (j < seq.length && COPY_RX.test(seq[j].text.trim()) && seq[j].text.length < 200) end = j;   // print-page items: copyright after the citation
      const body = seq.slice(cur, i);
      stories.push({ index: stories.length + 1, all: seq.slice(cur, end + 1), body, citLines: cit.map(l => l.text), citation: squashCit(cit.map(l => l.text)), heading: seq[i] });
      cur = end + 1; i = end + 1;
    } else i++;
  }
  const tail = seq.slice(cur);
  const out = stories.map((s, k) => {
    const first = s.all[0], last = s.all[s.all.length - 1];
    const st = { index: s.index, firstPage: first.p, lastPage: last.p, top: first.y + first.h * 0.85, bottom: last.y - last.h * 0.3, H: first.H,
      lines: s.body.map(l => ({ p: l.p, y: l.y, h: l.h, text: l.text })), citation: s.citation, citLines: s.citLines, lastTexts: s.all.length };
    st.firstLine = first; st.lastLine = last;
    return st;
  });
  out.forEach((s, k) => {
    const prev = out[k - 1], next = out[k + 1];
    s.sharedFirst = !!prev && prev.lastPage === s.firstPage;
    s.sharedLast = !!next && next.firstPage === s.lastPage;
    // junk before the first story or between stories on the same page counts as "shared" too
    s.bands = [];
    for (let p = s.firstPage; p <= s.lastPage; p++) {
      const H = s.H;
      let top = H, bottom = 0;
      if (p === s.firstPage && s.sharedFirst) top = Math.min(H, (prev.bottom + s.top) / 2);
      if (p === s.lastPage && s.sharedLast) bottom = Math.max(0, (s.bottom + next.top) / 2);
      if (p === s.firstPage && !s.sharedFirst && p === s.lastPage && !s.sharedLast) { top = H; bottom = 0; }
      s.bands.push({ page: p, top: Math.round(top * 10) / 10, bottom: Math.round(bottom * 10) / 10, full: top >= H - 0.01 && bottom <= 0.01 });
    }
    s.pageCount = s.lastPage - s.firstPage + 1;
  });
  return { stories: out, tail: tail.map(l => l.text), furniture: [...fk] };
}

function squashCit(lines) {
  // wrapped lines: "Star-" + "News" joins without a space; everything else with one
  let t = '';
  for (const l of lines) { const s = l.trim(); if (!s) continue; t += (t && /[A-Za-z]-$/.test(t) && /^[A-Za-z]/.test(s) ? '' : t ? ' ' : '') + s; }
  return t.replace(CIT_HEAD, '').trim();
}

/* ---- the citation ---- */
function docrefFix(d) {
  return String(d || '').replace(/\s+/g, '').replace(/\.+$/, '').replace(/(%40\d{7})(?!-)([0-9A-Fa-f]{16})/, '$1-$2');   // the hyphen after the julian date is lost by some readers
}
function docrefKey(d) { let s = docrefFix(d); try { s = decodeURIComponent(s); } catch (e) {} return s.toLowerCase(); }
function parseCitation(text) {
  const t = squash(text), out = { text: t, text_clean: '', docref: '', docref_key: '', url: '', host: '', author: '', year: '', month: '', day: '', date: '', title_outlet: '' };
  const m0 = /Historical and Current:\s*(.*)$/.exec(t);
  const urlText = (m0 ? m0[1] : ((/(https?:\/\/.*)$/.exec(t) || [])[1] || '')).replace(/\s+/g, '');
  if (urlText) {
    const m = /docref=([^&\s]+)/i.exec(urlText);
    if (m) { out.docref = docrefFix(m[1]); out.docref_key = docrefKey(m[1]); }
    out.url = urlText.replace(/\.$/, ''); out.text_clean = t.replace(/(Historical and Current:\s*)(.*)$/, (m, a) => a + urlText); const h = /^https?:\/\/([^/]+)/i.exec(out.url); out.host = h ? h[1].toLowerCase() : '';
  }
  const dm = /\((\d{4}), ([A-Za-z]+) (\d{1,2})\)\./.exec(t);
  if (dm) {
    const mi = MONTHS.findIndex(m => m.toLowerCase() === dm[2].toLowerCase());
    out.year = dm[1]; out.month = mi + 1; out.day = +dm[3]; out.date = mi >= 0 ? iso(dm[1], mi + 1, dm[3]) : '';
    out.author = squash(t.slice(0, dm.index)).replace(/[.,]\s*$/, '');
    const after = t.slice(dm.index + dm[0].length), av = after.search(/\s*Available from NewsBank/i);
    out.title_outlet = squash(av >= 0 ? after.slice(0, av) : after);
  } else {
    const nd = /\((\d{4}), ([A-Za-z]+) (\d{1,2})\)/.exec(t); if (nd) { const mi = MONTHS.findIndex(m => m.toLowerCase() === nd[2].toLowerCase()); out.date = mi >= 0 ? iso(nd[1], mi + 1, nd[3]) : ''; }
  }
  return out;
}

/* ---- the story header ---- */
function isoFromHeadDate(m, kind) {
  if (kind === 'en') { const mi = MONTHS.findIndex(x => x.toLowerCase() === m[1].toLowerCase()); return mi < 0 ? '' : iso(m[3], mi + 1, m[2]); }
  const mi = ES_MONTHS.indexOf(String(m[2]).toLowerCase()); return mi < 0 ? '' : iso(m[3], mi + 1, m[1]);
}
function parseHeader(lines) {
  const L = lines.map(l => (typeof l === 'string' ? l : l.text));
  let di = -1, kind = '', m = null;
  for (let i = 0; i < Math.min(L.length, 14); i++) {
    const s = L[i].trim();
    if ((m = DATE_EN.exec(s))) { di = i; kind = 'en'; break; }
    if ((m = DATE_ES.exec(s))) { di = i; kind = 'es'; break; }
  }
  if (di < 0) for (let i = 0; i < Math.min(L.length, 8); i++) { if ((m = DATE_LOOSE.exec(L[i].trim()))) { di = i; kind = 'loose'; break; } }
  const out = { ok: false, headline: '', kicker: '', date: '', date_line: '', source: '', author: '', section: '', words: 0, page: '', bodyStart: 0, has_openurl: false };
  if (di < 0) return out;
  let title = L.slice(0, di).map(squash).filter(Boolean).join(' ');
  let src = '', dateLine = L[di].trim();
  if (kind === 'loose') {   // v22 route G: a "Kicker | Headline" line, the real date line follows within 3 lines
    const ds = (() => { for (let i = di + 1; i < Math.min(L.length, di + 4); i++) { const mm = DATE_EN.exec(L[i].trim()) || DATE_ES.exec(L[i].trim()); if (mm) return { i, mm, k: DATE_EN.test(L[i].trim()) ? 'en' : 'es' }; } return null; })();
    if (ds) { const kl = L.slice(di, ds.i).map(squash).join(' '), cut = kl.indexOf(' | '); out.kicker = kl.slice(0, cut); title = (title ? title + ' ' : '') + (kl.slice(cut + 3) || kl); di = ds.i; m = ds.mm; kind = ds.k; dateLine = L[di].trim(); }
    else { out.date_line = dateLine; out.source = squash(m[2]); out.headline = title; return out; }
  }
  out.date = isoFromHeadDate(m, kind); out.date_line = dateLine; src = squash(kind === 'en' ? m[4] : m[4]);
  out.source = src; out.headline = title;
  let i = di + 1; const hdr = [];
  while (i < L.length && L[i].trim() !== 'OpenURL Link' && i < di + 8) { hdr.push(L[i].trim()); i++; }
  if (i < L.length && L[i].trim() === 'OpenURL Link') { out.has_openurl = true; i++; } else { i = di + 1; hdr.length = 0; }
  const h = hdr.join(' ');
  let a;
  if ((a = AUTH_RX.exec(h))) out.author = squash(a[1]);
  if ((a = SECT_RX.exec(h))) out.section = squash(a[1]);
  if ((a = WORDS_RX.exec(h))) out.words = +a[1].replace(/,/g, '');
  if ((a = PAGE_RX.exec(h))) out.page = a[1];
  out.bodyStart = i; out.ok = true;
  return out;
}

/* ---- paragraphs of the body: a vertical gap bigger than a line and a half, or a short line ending a sentence ---- */
function paragraphs(lines) {
  const out = []; let cur = [], prev = null;
  const ys = []; for (let i = 1; i < lines.length; i++) if (lines[i].p === lines[i - 1].p) ys.push(lines[i - 1].y - lines[i].y);
  ys.sort((a, b) => a - b); const lead = ys.length ? ys[Math.floor(ys.length / 2)] : 13;
  const mx = Math.max(1, ...lines.map(l => l.text.length));
  for (const l of lines) {
    const gap = prev && prev.p === l.p ? prev.y - l.y : 0;
    if (prev && gap > lead * 1.45 && cur.length) { out.push(cur.join(' ')); cur = []; }
    cur.push(l.text.trim()); prev = l;
    if (l.text.length < 0.6 * mx && /[.!?:"”’)\]]$/.test(l.text.trim())) { out.push(cur.join(' ')); cur = []; }
  }
  if (cur.length) out.push(cur.join(' '));
  return out.map(p => p.replace(/(\w)- (?=[a-z])/g, '$1').trim()).filter(Boolean);
}

/* ---- one story: header, body, citation, and what to call it ---- */
function parseStory(s) {
  const hd = parseHeader(s.lines), cit = parseCitation(s.citation);
  let bodyLines = s.lines.slice(hd.ok ? hd.bodyStart : 0);
  for (let k = bodyLines.length - 1; k >= Math.max(0, bodyLines.length - 4); k--) if (COPY_RX.test(bodyLines[k].text.trim())) { bodyLines = bodyLines.slice(0, k); break; }
  const paras = paragraphs(bodyLines), text = paras.join('\n\n');
  const kind = /^image\//i.test(cit.docref) ? 'print_page' : 'article';
  const flags = [];
  let outlet = hd.source, headline = hd.headline, date = hd.date, how = 'header';
  if (!hd.ok) {
    how = 'citation'; flags.push('no header: details read from the citation only');
    // "Headline.Outlet": the title ends where the outlet name starts; with no header this is a guess
    const t = cit.title_outlet, cuts = [...t.matchAll(/[.?!]\s*(?=[A-ZÁÉÍÓÚÑ0-9"“(])/g)].map(m => m.index + 1);
    let cutAt = -1; for (const c of cuts) { const rest = t.slice(c).trim(); if (rest && !/[.?!]\s+[A-Z]/.test(rest.replace(/\b(Inc|Jr|Sr|St|Mt|Dr|Co|Corp|Ltd)\./g, '$1'))) { cutAt = c; break; } }
    if (cutAt > 0) { headline = t.slice(0, cutAt).replace(/\.$/, '').trim(); outlet = t.slice(cutAt).trim(); } else { headline = t.replace(/\.$/, ''); outlet = ''; flags.push('outlet not found'); }
    date = cit.date;
  } else {
    if (cit.date && hd.date && cit.date !== hd.date) flags.push('header date ' + hd.date + ' and citation date ' + cit.date + ' differ');
    if (!date) { date = cit.date; if (date) flags.push('date taken from the citation'); }
    if (cit.title_outlet && headline && !normCmp(cit.title_outlet).startsWith(normCmp(headline).slice(0, 25))) flags.push('headline differs between header and citation');
  }
  if (!date) flags.push('no date');
  if (!outlet) flags.push('no outlet');
  if (!cit.docref) flags.push('no NewsBank link (docref) in the citation');
  const words = text ? text.split(/\s+/).length : 0;
  const cjk = (text.match(/[㐀-鿿가-힯぀-ヿ]/g) || []).length;
  const thin = kind === 'article' && words < 15 && cjk < 30;
  // author: the header's "Author:" is the byline as NewsBank holds it; the citation's "Last, I." is only an initial
  const author = hd.author || '';
  return { kind, thin, flags, how, headline, date, outlet, outlet_clean: cleanOutlet(outlet), author, section: hd.section, page: hd.page, words_nb: hd.words, kicker: hd.kicker,
    docref: cit.docref, docref_key: cit.docref_key, citation: cit.text_clean || cit.text, citation_author: cit.author, cit_host: cit.host, text, paras, body_words: words };
}
const normCmp = s => String(s || '').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
/* the outlet as NewsBank writes it, minus the access label and the state in parentheses ("Sacramento Bee, The (CA)" -> "Sacramento Bee, The") */
function cleanOutlet(s) { return squash(s).replace(/\s*\[[^\]]*(embargo|subscription|archive)[^\]]*\]\s*/i, ' ').replace(/\s*\((?:[A-Za-z .,'-]{2,40})\)\s*$/, '').replace(/-\s+(?=[A-Z])/g, '-').trim(); }

/* ---- a stable name for a story PDF: nb-<sha prefix of the docref key> (the station adds the batch position when there is no docref) ---- */
function canonLink(docref) { return docref ? 'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=' + docrefFix(docref) : ''; }

/* the saved copy's text as an HTML page, in the form the library's NewsBank text copies have (code/make_copies.py nb_page) */
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function storyHtml(p, row) {
  const meta = [row.outlet, row.date, p.section && 'Section: ' + p.section, p.page && 'Page ' + p.page, p.words_nb && p.words_nb + ' words'].filter(Boolean).join(' · ');
  return '<html><head><title>' + esc(row.headline) + '</title></head><body><article class="jg-pdf-text"><p class="pdf-cap">Text of the NewsBank PDF</p><h1>' + esc(row.headline) + '</h1>'
    + (p.author ? '<p class="byline">By ' + esc(p.author) + '</p>' : '') + '<p class="pdf-cap">' + esc(meta) + '</p>' + p.paras.map(x => '<p>' + esc(x) + '</p>').join('')
    + (p.citation ? '<p class="pdf-cap">' + esc(p.citation) + '</p>' : '') + '</article></body></html>';
}

const api = { linesFromItems, furnitureKeys, splitBatch, parseStory, parseHeader, parseCitation, paragraphs, docrefFix, docrefKey, canonLink, cleanOutlet, storyHtml, squashCit, MONTHS };
if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.NBParse = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
