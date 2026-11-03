/* NEWSBANKPDF-v1: the NewsBank part of the Update station that needs the tracker's own functions. This text is run INSIDE the tracker's
   function scope (the station appends it to the tracker code, which it runs in one function), so it uses covHit, dupOf, toRow, classifyPrompt,
   proposeRows, originCredit, tfCall and the rest exactly as the Update button does, and the tracker code itself stays byte for byte as it is.
   Input comes from the page layer (newsbank_ui.js): stories already read from batch PDFs (NBParse.parseStory) with their own PDF built.
   Output: the same documents an Update run leaves for the PC save (a run doc with proposed rows, pages docs, reprints, authors, translations),
   plus the per-story PDF names the update zip carries.

   PROQUESTPDF-v1: the same run serves ProQuest article PDFs. Everything source-specific (the record's link, how a story is found already in the
   tracker, the prompt preface, the row's source columns, the pages doc and the run doc's names) sits in a source object, NBSRC.nb here and NBSRC.pq in
   proquest.js, passed as opts.src / the last argument; with none given the NewsBank one is used, so the NewsBank behaviour is unchanged.

   What is NOT done here, on purpose: a reprint is never decided by text (the PC save does it by the string-of-text rule, as for a web find);
   NewsBank text that lacks his name is not grounds to drop a story (HANDOFF 3: NewsBank drops captions and guest lists). */
const NBX = { seen: new Map(), docrefs: null, items: [], marked: new Set() };
const NB_DS = 'Newsbank';                 // the sheet's own spelling (3,874 rows)
const NB_BLOCK_HOSTS = /(^|\.)(newsbank\.com|oclc\.org|google\.[a-z.]+|proquest\.com|bing\.com|archive\.org|webcache\.googleusercontent\.com)$/i;

/* every NewsBank record the tracker already has: docref of any link in the Coverage rows, the stories and their reprints */
function nbDocrefs(){
  if (!NBX.docrefs){
    /* a Map: docref key -> the row that holds it ({aid, sid, kind, files}); `files` is the row's saved-copy names when the for-Update file carries them (rows.cols "files"), else null */
    const s = NBX.docrefs = new Map(), add = (u, row) => { const m = /docref=([^&\s#]+)/i.exec(String(u || '')); if (m){ const k = NBParse.docrefKey(m[1]); if (!s.has(k) || (row && !s.get(k).aid)) s.set(k, row || {}); } };
    const b = covBlock('rows'), ix = {}; ((b && b.cols) || []).forEach((k, i) => { ix[k] = i; });
    ((b && b.rows) || []).forEach(a => { if (!Array.isArray(a)) return; const row = { aid: String(a[ix.aid] || ''), sid: String(a[ix.sid] || ''), kind: String(a[ix.kind] || ''), files: ix.files !== undefined && a[ix.files] != null ? String(a[ix.files]) : null }; (Array.isArray(a[ix.links]) ? a[ix.links] : []).forEach(u => add(u, row)); });
    D.forEach(r => { add(r.link); add(r.plink); (r.reps || []).forEach(x => add(x && x.link)); });
  }
  return NBX.docrefs;
}
/* the outlet as the tracker already spells it: the most used spelling among the sheet's Outlet names with the same key (covOutlet: case, "The", punctuation and a state in parentheses ignored) */
let NBX_SPELL = null;
function nbSpell(p){
  if (p._ol) return p; p._ol = true;
  if (!NBX_SPELL){
    const cnt = new Map(), add = n => { n = String(n || '').trim(); if (n) cnt.set(n, (cnt.get(n) || 0) + 1); };
    covLoad().rows.forEach(o => add(o.outlet)); D.forEach(r => add(String(r.outlet || '').replace(/\s*\([^)]*\)\s*$/, '')));
    const best = new Map(); cnt.forEach((c, n) => { const k = covOutlet(n); const o = best.get(k); if (k && (!o || c > o.c || (c === o.c && n < o.n))) best.set(k, { n, c }); });
    NBX_SPELL = best;
  }
  const hit = NBX_SPELL.get(covOutlet(p.outlet_clean));
  if (hit && hit.n !== p.outlet_clean){ p.outlet_note = 'outlet “' + p.outlet + '” (NewsBank) filed as “' + hit.n + '” (the tracker’s spelling)'; p.outlet_clean = hit.n; }
  return p;
}
const nbLink = p => NBParse.canonLink(p.docref);
const nbCand = p => ({ link: nbLink(p), hl: p.headline, date: ((window.NBTV && NBTV.detect(p)) || {}).date_pt || p.date, outlet: p.outlet_clean, pub: p.outlet_clean, plink: nbLink(p) });

/* Is this story new? (the checks the Update button makes for a find, plus NewsBank's own id)
   -> { status: 'new' | 'reprint' | 'known' | 'dup_batch' | 'print_page' | 'thin', why, of? (story id for a reprint, first copy for dup_batch) } */
function nbScreen(p, SRC){
  SRC = SRC || NBSRC.nb;
  const key = p.docref_key, isNb = SRC.id === 'nb';
  if (isNb) nbSpell(p);
  if (p.kind === 'print_page' && key && SRC.known().has(key)){ const kr = SRC.known().get(key) || {}; return { status: 'known', why: 'already in the tracker as ' + (kr.kind === 'P' ? 'a print page (' + kr.aid + ')' : 'row ' + (kr.aid || '?')) + ' (same ' + SRC.idName + ')', row: kr.aid || '', sid: kr.sid || '' }; }   // PRINTPAGES-v1 (the for-Update file lists the Unlinked print pages tab's links)
  if (p.kind === 'print_page') return key && NBX.seen.has(key) ? { status: 'dup_batch', why: 'the same print page appears twice in the PDFs added', of: NBX.seen.get(key) } : { status: 'print_page', why: 'a newspaper page image, not a story: listed as a print page to clip' };
  if (key && SRC.known().has(key)){ const kr = SRC.known().get ? SRC.known().get(key) || {} : {}; return { status: 'known', why: 'already in the tracker' + (kr.aid ? ' as ' + kr.aid : '') + ' (same ' + SRC.idName + ')', row: kr.aid || '', sid: kr.sid || '', files: kr.files == null ? null : kr.files }; }
  if (key && NBX.seen.has(key)) return { status: 'dup_batch', why: 'the same story appears twice in the PDFs added (same ' + SRC.idName + ')', of: NBX.seen.get(key) };
  // SAFETY: a story with no link and no readable header is never "new": it needs a look. A story with no link but a header is checked by headline, date and outlet,
  // and if that finds nothing it still is not offered (no link = no way to tell it apart from a story already in the tracker): "needs a look".
  if (isNb && !key && (p.how === 'citation' || !p.headline)) return { status: 'look', why: 'no NewsBank link and no readable header in the PDF: not added, check this story by hand', needs_check: true };
  if (!p.headline) return { status: 'new', why: 'no headline could be read: check it', needs_check: true };
  const c = SRC.cand(p), ch = covHit(c);
  const noLink = isNb && !key, nl = r => noLink && (r.status === 'new' || r.status === 'reprint') ? { status: 'look', why: 'no NewsBank link was read for this story, and the headline check found it not in the tracker: not added, check it by hand (' + r.why + ')', needs_check: true } : r;
  if (ch && ch.same) return { status: 'known', why: 'already in the tracker (same outlet and headline as ' + ch.o.aid + ', within 3 days)' };
  const old = dupOf(Object.assign({}, c, { link: '', plink: '' }), D);   // no link: two NewsBank records share one host, which dupOf would read as one outlet
  if (old && old.same) return { status: 'known', why: 'already in the tracker (same story and outlet as ' + old.r.id + ')' };
  const st = ch && !ch.same ? byId.get(ch.o.sid) || byId.get(IDMAP_SID(ch.o.sid)) : old && !old.same ? old.r : null;
  const sid = ch && !ch.same ? ch.o.sid : old && !old.same ? old.r.id : '';
  if (st && !ranIn(st, p.outlet_clean, '')) return nl({ status: 'reprint', of: st.id, of_hl: st.hl, why: 'another outlet’s copy of “' + String(st.hl).slice(0, 60) + '” (' + st.id + '): proposed as a reprint; the PC save tests the text' });
  if (st) return { status: 'known', why: 'this outlet already has the story (' + st.id + ')' };
  if (sid) return nl({ status: 'reprint', of: sid, of_hl: '', why: 'another outlet’s copy of a story already in the tracker (' + sid + '): proposed as a reprint; the PC save tests the text' });
  return nl({ status: 'new', why: 'new story' });
}
function nbRemember(p, key){ if (p.docref_key) NBX.seen.set(p.docref_key, key); }

/* ---------- the publisher's own link: a search for the headline, then a look at the page ---------- */
let NB_OUT_HOSTS = null;
function nbOutletHosts(name){
  if (!NB_OUT_HOSTS){
    NB_OUT_HOSTS = new Map();
    D.forEach(r => [r.link, r.plink].forEach(u => { const h = hostOf(u); if (!h || NB_BLOCK_HOSTS.test(h)) return; [r.pub, String(r.outlet || '').replace(/\s*\([^)]*\)\s*$/, '')].map(nrmName).filter(Boolean).forEach(k => (NB_OUT_HOSTS.get(k) || NB_OUT_HOSTS.set(k, new Set()).get(k)).add(h)); }));
  }
  return NB_OUT_HOSTS.get(nrmName(String(name || '').replace(/\s*\([^)]*\)\s*$/, ''))) || new Set();
}
function nbShingles(text, n){ const w = normH(text).split(' ').filter(Boolean), out = new Set(); for (let i = 0; i + n <= w.length && i < 4000; i++) out.add(w.slice(i, i + n).join(' ')); return out; }
async function nbFindLinks(mcp, items, say, SRC){
  SRC = SRC || NBSRC.nb;
  const cands = [];
  let i = 0;
  for (const it of items){
    if (U.ctl.signal.aborted) break;
    i++; say(`Looking for the publisher’s own page (${i} of ${items.length})`, i / items.length * 0.5);
    const p = it.p, hl = String(p.headline || '').replace(/["“”]/g, '').slice(0, 110);
    if (!hl || (hl.split(/\s+/).length < 4 && !/[㐀-鿿가-힯]/.test(hl))) continue;
    if (/^(TV|Radio|Podcast)$/.test(it.media || '')) continue;
    let res = null;
    try { res = tfPayload(await tfCall(mcp, 'search', { query: `"${hl}"`, location: 'US' })); }
    catch(e){ if (STOP_CODES.has(e && e.code)) throw e; it.linkNote = 'the web search failed'; continue; }
    const words = new Set(normH(hl).split(' ').filter(x => x.length > 1)), hosts = nbOutletHosts(p.outlet_clean), oname = nrmName(p.outlet_clean);
    const hits = ((res && res.results) || []).map(x => {
      const h = hostOf(x.url); if (!h || NB_BLOCK_HOSTS.test(h) || TF_AGG_HOSTS.test(h) || SKIP_HOSTS.test(h) || neverCoverage(x.url, x.publisher || x.site_name) || isPrintPage(x.url) || isOwned({ url: x.url })) return null;
      if (normH(x.title).split(' ').filter(t => words.has(t)).length < 0.8 * Math.max(1, words.size)) return null;
      const d = tfDate(x.date); if (d && p.date && Math.abs(Date.parse(d) - Date.parse(p.date)) > 4 * 864e5) return null;
      const strong = [...hosts].some(k => h === k || h.endsWith('.' + k)), sld = nrmName((h.split('.').slice(-2, -1)[0]) || ''), named = !!oname && sld.length > 3 && (oname.startsWith(sld) || sld.startsWith(oname.slice(0, 8)));
      return { x, url: x.url, host: h, strong, named, rank: strong ? 0 : named ? 1 : 2 };
    }).filter(Boolean).sort((a, b) => a.rank - b.rank);
    if (hosts.size && !hits.some(h => h.strong || h.named)) { it.linkNote = 'a page with this headline was found only on other sites'; continue; }
    if (hits.length) cands.push({ it, c: hits[0] });
  }
  // open each candidate page once: does its text share runs of words with the NewsBank text?
  for (let k = 0; k < cands.length && !U.ctl.signal.aborted; k += 10){
    const b = cands.slice(k, k + 10); say(`Checking ${b.length} candidate pages`, 0.5 + k / Math.max(1, cands.length) * 0.5);
    let pg = new Map(), errs = new Map();
    try { const pl0 = tfPayload(await tfCall(mcp, 'fetch_content', tfFetchInput(b.map(x => x.c.url)))); pg = tfResults(pl0); errs = tfErrors(pl0); }
    catch(e){ if (STOP_CODES.has(e && e.code)) throw e; }
    b.forEach(({ it, c }) => {
      const r = pg.get(normU(c.url)), blocked = !r && (TF_BLOCKED_HOSTS.test(c.host) || lkBlockedHost(c.url) || TF_BLOCKED_ERR.test(String(errs.get(normU(c.url)) || '')));
      if (r){
        const t = tfStrip(String(r.text || '')), ns = nbShingles(it.p.text, 6), ps = nbShingles(t, 6); let share = 0; ns.forEach(s => { if (ps.has(s)) share++; });
        const ok = share >= 2 || (!ns.size && (c.strong || c.named)) || ((c.strong || c.named) && NAMES_HIM.test(t));
        if (ok){ it.pub = { url: r.final_url || c.url, status: 'Publisher URL', how: share >= 2 ? 'same wording as the ' + SRC.name + ' text' : 'same headline on the outlet’s own site' }; return; }
        it.linkNote = 'a page with this headline was found but its text does not match the NewsBank text'; return;
      }
      if (blocked && (c.strong || c.named)){ it.pub = { url: c.url, status: 'Search link only', how: 'same headline on the outlet’s site; the page is blocked, so its text could not be compared' }; return; }
      it.linkNote = 'the candidate page could not be opened';
    });
  }
}

/* ---------- Claude's reading of each new story (the tracker's own classify prompt, with the NewsBank facts first) ---------- */
const NB_PREFACE = `These items come from NewsBank's own search for "Jesse Gabriel", read from its PDFs. The url is NewsBank's record, the text is NewsBank's text. Three things differ from web results: (1) NewsBank drops photo captions and guest lists, so a story whose text does not show his name is still kept (keep false only for another person named Jesse Gabriel, or a page that is not press: an advocacy group's or an official's own release, a database or listing); (2) the date and the outlet are NewsBank's and are right: copy them; (3) the headline is NewsBank's own: copy it.\n\n`;
async function nbClassify(items, sample, say, preface){
  const out = new Map(); if (!items.length) return out;
  const CB = 20;
  for (let i = 0; i < items.length && !U.ctl.signal.aborted; i += CB){
    const b = items.slice(i, i + CB); say(`Claude is reading the stories (${Math.min(i + CB, items.length)} of ${items.length})`, (i + CB) / items.length);
    const cs = b.map(it => it.c); let res = null;
    if (sample){ try { res = await sample.json((preface || NB_PREFACE) + classifyPrompt(cs), { signal: U.ctl.signal, modelTier: 'default' }); } catch(e){ if (e && e.code === 'cancelled') break; res = null; } }
    b.forEach((it, j) => { const k = (Array.isArray(res) && (res.find(o => o && +o.n === j + 1) || res[j])) || null; out.set(it, { k: k || nbGuess(it), claude: !!k }); });
  }
  return out;
}
function nbGuess(it){ return { keep: true, why: 'Not read by Claude: check the fields.', date: it.p.date, outlet: it.p.outlet_clean, pub: it.p.outlet_clean, hl: it.p.headline, topic: 'Other / roundup', media: 'Newspaper', role: /Gabriel/.test(it.p.headline) ? 'Named in headline' : 'Mentioned in story' }; }

/* ---------- the whole run ----------
   items: [{ key, p, screen, fileId, pdf: {sha256, bytes} | null, batch: {name, sha256, index, firstPage, lastPage, span}, include }] (status new or reprint only)
   opts: { say(msg, 0..1), links: bool, sample, mcp, mark(coll, id) }  ->  { run, rows, ids, counts, left, print_pages, ... } */
/* PRINTPAGES-v1: the tracker stories a print page may carry, nearest before the page's date (a print page has no text to match on: the intern decides from the picture) */
function nbPrintCands(date, outlet){
  const d = Date.parse(date); if (!d) return [];
  const out = []; D.forEach(r => { if (!r || !r.id || !r.date) return; const g = (d - Date.parse(r.date)) / 864e5; if (g < -1 || g > 75) return; out.push({ g, id: r.id, label: r.id + ' · ' + String(r.pub || r.outlet || '') + ' · ' + r.date + ' · ' + String(r.hl || '').slice(0, 70) }); });
  return out.sort((a, b) => a.g - b.g).slice(0, 250);
}
const nbHasStory = id => byId.has(id);
async function nbRun(items, opts){
  const SRC = opts.src || NBSRC.nb, say = opts.say || (() => {}), mark = opts.mark || (() => {});
  const wasCtl = U.ctl; U.ctl = new AbortController(); U.busy = true; U.failed = 0; U.originPages = U.originPages || new Map();
  const run = newRunId(), at = new Date().toISOString();
  const res = { run, at, rows: [], stories: [], reprints: [], left: [], unconfirmed: [], counts: {}, links: { found: 0, searched: 0 }, errors: [] };
  try {
    // PRINTPAGES-v1: a print page the intern matched to a tracker story is proposed as a print reprint of it; one not matched becomes an "Unlinked print pages" row
    items.forEach(it => { if (it.screen.status === 'print_page' && it.include !== false && it.confirm && byId.has(it.confirm)){ const st = byId.get(it.confirm); it.printAs = 'reprint'; it.screen = Object.assign({}, it.screen, { status: 'reprint', of: it.confirm, of_hl: st.hl, why: 'print page confirmed by the intern as a print copy of “' + String(st.hl).slice(0, 60) + '” (' + it.confirm + ')' }); } });
    const unl = items.filter(it => it.screen.status === 'print_page' && it.include !== false); unl.forEach(it => { it.printAs = 'unlinked'; });
    const news = items.filter(it => it.screen.status === 'new' && it.include !== false), reps0 = items.filter(it => it.screen.status === 'reprint' && it.include !== false);
    news.forEach(it => { it.c = { url: SRC.link(it.p), title: it.p.headline, published: it.p.date, dateSrc: 'tinyfish', author: it.p.author, text: (SRC.hint ? SRC.hint(it.p) : '') + String(it.p.text || '').slice(0, 20000), site: it.p.outlet_clean, found_by: SRC.foundBy };
      it.c.gab = NAMES_HIM.test(it.c.title + ' ' + it.c.text) && TF_CONTEXT.test(gabrielContext(it.c.title + '\n' + it.c.text)); it.c.ctx = (it.c.title + '\n' + (it.c.gab ? gabrielContext(it.c.text) + '\n' : '') + it.c.text).slice(0, 1800); });
    // 1. Claude: topic, media, role, tone, language (and the English headline and summary of a non-English story)
    const cls = await nbClassify(news, opts.sample, say, SRC.preface);
    const kept = [], usedIds = new Set();
    const prJudge = (it, kk, claude) => { const pj = PRJudge.judge({ text: it.p.text, title: it.p.headline, outlet: it.p.outlet, url: '', date: it.p.date, claude: claude ? kk : null, rel: window.__prRel ? window.__prRel() : null }); it.pr = pj; return pj; };
    news.forEach(it => {
      let { k, claude } = cls.get(it) || { k: nbGuess(it), claude: false };
      // PRJUDGE-v1: is it a pure press release? Decided from its own text and Claude's answer; a pure release is not "left out as not press": it stays, marked Press release = Yes
      it.tv = NBTV.detect(it.p);   // NBTV-v1: a broadcast transcript is TV / Radio, a Broadcast segment, dated by the Pacific air date
      const pj = prJudge(it, k, claude);
      if (k.keep === false && pj.v === 'yes') k = Object.assign({}, k, { keep: true, why: 'press release (kept in the sheet, Press release = Yes): ' + pj.why });
      if (k.keep === false){ res.left.push({ hl: VS(it.p.headline, 200), outlet: VS(it.p.outlet_clean, 120), date: it.p.date, why: VS(k.why, 200) || 'Not press coverage about him.' }); it.skipped = VS(k.why, 200) || 'Claude: not press coverage about him'; return; }
      const kk = Object.assign({}, k, { date: it.p.date, outlet: it.p.outlet_clean, hl: it.p.headline, pub: VS(k.pub, 100) || it.p.outlet_clean });
      const r = toRow(it.c, kk); r._on = true; r._claude = claude; r._text = String(it.p.text || '').slice(0, 6000); r._nb = it; r._found_by = SRC.foundBy + ': ' + it.batch.name;
      r.src = SRC.srcName; r.plink = SRC.plink(it.p); r.pq = SRC.pq ? SRC.pq(it.p) : ''; r.lstat = ''; r._pageKey = ''; r._dateSrc = SRC.dateSrc;   // sheet_task.dates_v1 (patch 03) reads 'newsbank' as Date source "NewsBank" ("print edition" for a print record)
      if (SRC.print(it.p)) r.fmt = 'Print';
      if (!SRC.link(it.p) || usedIds.has(r.id)) { let id = 'jg-' + hash6(it.key || String(kept.length)); while (usedIds.has(id) || byId.has(id) || (covLoad().idmap || {})[id]) id = 'jg-' + hash6(id + 'x'); r.id = id; }   // never the id of "no link" ('' hashes alike for every story)
      usedIds.add(r.id);
      if (it.tv){ r.media = it.tv.medium; r.fmt = 'Broadcast segment'; r._av = Object.assign({}, it.tv.av); if (it.tv.date_pt !== r.date){ r.date = it.tv.date_pt; r.year = +r.date.slice(0, 4); } }   // NBTV-v1 (REVIEW4-v1 F1)
      it.r = r; it.media = r.media; kept.push(it);
    });
    reps0.forEach(it => { it.tv = NBTV.detect(it.p); prJudge(it, null, false); });
    // 2. the publisher's own link (a search for the headline, then a look at the page): stories and reprints alike
    const lookup = kept.concat(reps0.map(it => { it.media = ''; return it; })), nlook = lookup.length;
    if (opts.links && opts.mcp && lookup.length){ say('Looking for the publisher’s own pages', 0); res.links.searched = nlook; await nbFindLinks(opts.mcp, lookup, say, SRC); res.links.found = lookup.filter(x => x.pub).length; }
    kept.forEach(it => { if (it.pub){ it.r.link = it.pub.url; it.r.lstat = it.pub.status; } else it.r.link = SRC.link(it.p); });
    // 3. the same new story twice in the PDFs: keep the earliest, the other becomes its reprint (the Update button's rule)
    const keep2 = [];
    const cmp = it => Object.assign({}, it.r, { link: it.pub ? it.pub.url : '', plink: '' });   // publisher link or none, never the shared NewsBank host
    kept.slice().sort((a, b) => a.r.date.localeCompare(b.r.date)).forEach(it => {
      const f = dupOf(cmp(it), keep2.map(cmp));
      if (!f){ keep2.push(it); return; }
      const first = keep2.find(x => x.r.id === f.r.id) || keep2[keep2.length - 1];
      if (f.same){ it.skipped = 'the same story and outlet as another story in these PDFs'; res.left.push({ hl: VS(it.p.headline, 200), outlet: VS(it.p.outlet_clean, 120), date: it.p.date, why: it.skipped }); return; }
      if (!ranIn(first.r, it.p.outlet_clean, '')){ (first.r._reps || (first.r._reps = [])).push({ outlet: it.p.outlet_clean, link: SRC.link(it.p), date: it.r.date, hl: it.p.headline, _nb: it }); first.r.also = (first.r.also ? first.r.also + '; ' : '') + it.p.outlet_clean; it.asRep = true; }
      else { it.skipped = 'this outlet already has the story in these PDFs'; res.left.push({ hl: VS(it.p.headline, 200), outlet: VS(it.p.outlet_clean, 120), date: it.p.date, why: it.skipped }); }
    });
    const orig = keep2;
    // 4. the outlet that first ran each new story (a wire's or a credited paper's own copy), as the Update button does
    if (opts.mcp && orig.length){ say('Looking for the outlet that first ran each story', 0); try { await originCredit(opts.mcp, orig.map(it => it.r)); } catch(e){ if (STOP_CODES.has(e && e.code)) throw e; res.errors.push('origin search: ' + VS(String(e && e.message || e), 120)); } }
    // 5. the proposed rows, in the Coverage columns with placeholders (the tracker's own proposeRows), then what is NewsBank's
    const reps = reps0.map(it => ({ story: it.screen.of, outlet: it.p.outlet_clean, link: SRC.link(it.p), date: it.tv ? it.tv.date_pt : it.p.date, hl: it.p.headline, _on: true, _named: true, _nb: it, _pageKey: 'rp-' + hash12(normU(SRC.link(it.p))), _page: { url: SRC.link(it.p), title: it.p.headline, clean: '' } }));
    orig.forEach(it => (it.r._reps || []).forEach(x => { x._pageKey = 'rp-' + hash12(normU(x.link)); }));
    const stories = orig.map(it => it.r);
    const prop = proposeRows(run, stories, reps);
    const order = []; stories.forEach(r => { order.push(r._nb); (r._reps || []).forEach(x => order.push(x._nb)); }); reps.forEach(p => order.push(p._nb));
    if (order.length !== prop.rows.length) throw new Error('NewsBank rows do not line up with the proposed rows (' + order.length + ' vs ' + prop.rows.length + ')');
    prop.rows.forEach((row, i) => SRC.rowFill(row, order[i]));
    // 6. documents: pages (the story's text as the library's NewsBank text copy, plus where its PDF is), reprints, authors, translations
    const pdb = window.claude && window.claude.use ? await window.claude.use('db').catch(() => null) : null;
    const col = n => pdb ? pdb.collection(n) : null, setDoc = async (n, id, data) => { const c = col(n); if (!c) return; mark(n, id); await c.doc(id).set(data); };
    const pageDoc = (it, key) => { const p = it.p, row = { outlet: p.outlet_clean, date: p.date, headline: p.headline };
      return { url: SRC.link(p), title: VS(p.headline, 300), clean: SRC.html(p, row), scoped: '', publine: '', at, [SRC.metaKey]: SRC.meta(it) }; };
    for (const it of orig){ await setDoc('pages', it.r.id, pageDoc(it)); res.stories.push(it.r.id);
      (it.r._reps || []).forEach(x => { x._doc = pageDoc(x._nb); }); }
    for (const it of orig) for (const x of (it.r._reps || [])) await setDoc('pages', x._pageKey, x._doc);
    for (const p of reps){ await setDoc('pages', p._pageKey, pageDoc(p._nb));
      const id = p._pageKey, doc = { story: p.story, outlet: p.outlet, link: p.link, date: p.date, added: TODAY }; await setDoc('reprints', id, doc); res.reprints.push({ story: p.story, outlet: p.outlet });
      if (!RPS.has(id)) RPS.set(id, cleanReprint(id, doc)); }
    // PRINTPAGES-v1: unconfirmed print pages: a pages document (the page's PDF, the print original) and a row for the "Unlinked print pages" tab
    const printRows = [];
    for (const it of unl){ const key = 'pp-' + hash12(normU(nbLink(it.p) || it.key)), p = it.p;
      await setDoc('pages', key, pageDoc(it)); it.ppKey = key;
      printRows.push({ _page: key, 'Data Source': NB_DS, 'Saved Copy?': 'No', 'Date': p.date, 'Year': p.date ? +p.date.slice(0, 4) : '', 'Date source': 'print edition', 'Outlet': p.outlet_clean, 'Medium': 'Newspaper', 'Format': 'Print', 'Language': 'English', 'Edition': 'Print', 'Page': p.page || '',
        'NewsBank print-page link': nbLink(p), 'Newsbank APA citation (print page)': VS(p.citation, 1500).replace(/\.\s*$/, '') + '.', 'Likely counterpart': '', 'Team note': 'NewsBank print page from ' + it.batch.name + ' #' + it.batch.index + ' (' + TODAY + '): not matched to a tracker story; the page PDF is kept as the print original' }); }
    // ORIGCOPIES-v1: a story already in the tracker keeps its PDF as an extra original copy of the row it matched (the PC adds it only when that row does not hold this NewsBank record's PDF already, and fills only blank cells)
    const copies = [];
    for (const it of items.filter(x => x.screen.status === 'known' && x.include !== false && x.pdf && x.screen.row)){ const p = it.p;   // the run document names the PDF itself (updatefolder FORMAT: run.extra_copies {aid, fmt, file, pdf_sha256})
      copies.push({ aid: it.screen.row, fmt: 'nb', file: 'files/' + it.fileId + '.pdf', pdf_sha256: it.pdf.sha256, docref: p.docref, story: it.screen.sid || '', cells: { 'Section': VS(p.section, 120), 'Author / byline': p.author || '', 'Word count': p.words_nb || '', 'Newsbank APA citation (article)': VS(p.citation, 1500).replace(/\.\s*$/, '') + '.', 'NewsBank article link': nbLink(p) } }); it.copyKey = it.fileId; }
    orig.forEach(it => ((it.r._origin || {}).cands || []).forEach(c => { const pg = U.originPages && U.originPages.get(c.page); if (pg) it.ogPages = (it.ogPages || []).concat([[c.page, pg]]); }));
    for (const it of orig) for (const [k, pg] of (it.ogPages || [])) await setDoc('pages', k, { url: pg.url, title: VS(pg.title, 300), clean: pg.clean, scoped: '', at });
    const strip = r => { const o = {}; Object.keys(r).forEach(k => { if (!/^_|^why$/.test(k)) o[k] = r[k]; }); return o; };
    const added = addClips(stories.map(strip).map(o => cleanClip(o.id, o)).filter(Boolean));
    applyReprints();
    for (const r of stories){ if (r._authorBy && r.author) await setDoc('authors', r.id, { author: r.author.slice(0, 300), found: TODAY, by: 'Claude' });
      if (r.lang && r.hl_en) await setDoc('translations', r.id, { hl: r.hl_en, text: r.text_en || '', lang: r.lang, at: TODAY, by: 'Claude' }); }
    // headlines Claude did not translate in the same call (the tracker's own pass, scoped to these stories)
    const ptr = pendingTr().filter(id => stories.some(r => r.id === id));
    ptr.forEach(id => mark('translations', id));   // headline translations stay in this tab too
    if (ptr.length && sampler){ say('Translating headlines', 0.9); try { await translateHeadlines(ptr); } catch(e){ res.errors.push('translation: ' + VS(String(e && e.message || e), 120)); } }
    // 7. the run doc: the same shape an Update run leaves; mode "newsbank" also marks the NewsBank refresh as done today (the reminder in the Update panel)
    orig.forEach(it => nbRemember(it.p, it.key)); reps0.forEach(it => nbRemember(it.p, it.key));
    items.filter(it => it.printAs).forEach(it => (res.print_pages = res.print_pages || []).push({ as: it.printAs, story: it.confirm || '', file: it.pdf ? 'files/' + it.fileId + '.pdf' : '', url: nbLink(it.p) || '', outlet: VS(it.p.outlet_clean, 120), date: it.p.date || '', hl: VS(it.p.headline, 200), snippet: 'NewsBank print page from ' + it.batch.name }));
    res.print_pages = res.print_pages || [];
    const batches = [...new Map(items.map(it => [it.batch.sha256, { name: it.batch.name, sha256: it.batch.sha256 }])).values()];
    const doc = { at, mode: SRC.runMode, [SRC.runMark]: TODAY, status: 'done', stories: stories.map(r => r.id).filter(id => byId.has(id)), reprints: res.reprints.concat(orig.flatMap(it => (it.r._reps || []).map(x => ({ story: it.r.id, outlet: x.outlet })))),
      rows: covCompact(prop.rows), print_pages: res.print_pages.slice(0, 100), print_rows: printRows, extra_copies: copies, found_by: { [SRC.runMark]: prop.rows.length }, searched_to: '', since: '', since_manual: false,
      left: res.left.slice(0, 150), [SRC.metaKey]: { source: SRC.runSource, batches, pdfs: prop.rows.map((r, i) => order[i].fileId).filter(Boolean).length, links_found: res.links.found, links_searched: res.links.searched } };
    mark('runs', run);
    const saved = await saveRun(run, doc);
    res.rows = prop.rows; res.added = added; res.doc = doc; res.saved = saved;
    res.counts = { stories: stories.length, reprint_rows: reps.length + orig.reduce((a, it) => a + (it.r._reps || []).length, 0), rows: prop.rows.length, print_pages: res.print_pages.length, left: res.left.length };
    res.items = items.map(it => ({ key: it.key, status: it.skipped ? 'skipped' : it.asRep ? 'reprint_in_batch' : it.screen.status, why: it.skipped || it.screen.why, link: it.pub ? it.pub.url : '', link_status: it.pub ? it.pub.status : '', link_note: it.linkNote || '' }));
    return res;
  } finally { U.ctl = wasCtl; U.busy = false; }
}
function nbMeta(it){
  const p = it.p, b = it.batch;
  return { docref: p.docref, url: nbLink(p), file: it.pdf ? 'files/' + it.fileId + '.pdf' : '', pdf_sha256: it.pdf ? it.pdf.sha256 : '', pdf_bytes: it.pdf ? it.pdf.bytes : 0, thin: !!p.thin,
    kind: p.kind, as: it.printAs || (it.copyKey ? 'known' : ''), batch: { name: b.name, sha256: b.sha256, index: b.index, pages: [b.firstPage, b.lastPage], shared_first: !!b.sharedFirst, shared_last: !!b.sharedLast, bands: b.bands || [] },
    header: { headline: p.headline, date: p.date, source: p.outlet, author: p.author, section: p.section, page: p.page, words: p.words_nb }, citation: p.citation, flags: p.flags || [], how: p.how };
}
/* what NewsBank, not the web, gives a row (the sheet's own NewsBank conventions: Data Source "Newsbank", Date source "NewsBank" / "print edition",
   the article link in its normal form, the APA citation in its column); File name and Saved Copy? stay blank: the PC save names the PDF nb<ID>(o|r)-<story>.pdf */
function nbRowFill(row, it){
  const p = it.p, isRep = row['Original or reprint'] === 'Reprint';
  row['Data Source'] = NB_DS; row['Date source'] = p.page ? 'print edition' : 'NewsBank';
  row._date_src = 'newsbank';   // every NewsBank row (reprints too): the PC's date check names the source NewsBank / print edition
  row['NewsBank article link'] = nbLink(p); row['Newsbank APA citation (article)'] = VS(p.citation, 1500).replace(/\.\s*$/, '') + '.';
  row['Publisher link'] = it.pub ? it.pub.url : ''; row['Link status'] = it.pub ? it.pub.status : '';
  row['Section'] = VS(p.section, 120); row['Page'] = p.page || ''; if (p.words_nb) row['Word count'] = p.words_nb;
  row['Edition'] = p.page ? 'Print' : /web edition|online/i.test(p.outlet || '') ? 'Web' : '';
  row['Format'] = p.page ? 'Print' : (row['Format'] === 'Article' || !row['Format'] ? 'Article' : row['Format']);
  row['Headline'] = p.headline; row['Date'] = p.date; row['Year'] = p.date ? +p.date.slice(0, 4) : '';
  if (isRep){ row['Author / byline'] = p.author || ''; row['Tracker story code'] = ''; }
  if (p.kind === 'print_page'){   // PRINTPAGES-v1: a confirmed print page is a print reprint of the story: the story's headline, the page's own link and citation in the print-page columns
    row['Headline'] = it.screen.of_hl || row['Headline']; row['NewsBank print-page link'] = row['NewsBank article link']; row['NewsBank article link'] = '';
    row['Newsbank APA citation (print page)'] = row['Newsbank APA citation (article)']; row['Newsbank APA citation (article)'] = ''; row['Edition'] = 'Print'; row['Format'] = 'Print'; row['Date source'] = 'print edition'; row['Page'] = p.page || '';
  }
  if (it.tv){   // NBTV-v1: a broadcast transcript is handled as the Update button's TV finds are (Medium, Format, Pacific date, his role, an Audio & video row)
    const tv = it.tv; row['Medium'] = tv.medium; row['Format'] = 'Broadcast segment'; row['Date'] = tv.date_pt; row['Year'] = tv.date_pt ? +tv.date_pt.slice(0, 4) : '';
    if (tv.air_clock){ row['Date source'] = 'air date (Pacific)'; row._date_src = 'airdate_pt'; }
    if (tv.depth && !row['Mention depth']) row['Mention depth'] = tv.depth;
    if (tv.quoted && !row['Quoted']) row['Quoted'] = 'Yes';
    row._av = Object.assign({}, tv.av); row._tv = { medium: tv.medium, role: tv.role, note: tv.note };
  }
  if (it.pr){ row._pr = window.__prRecord(it.pr); if (it.pr.v === 'yes') row['Press release'] = 'Yes'; }   // PRJUDGE-v1: the decision and its reason travel with the row; the PC save fills Press release (fill-blanks)
  row['Team note'] = [it.pr && it.pr.v === 'yes' ? 'press release: ' + VS(it.pr.why, 220) : '', 'NewsBank PDF ' + it.batch.name + ' #' + it.batch.index + ' (' + TODAY + ')', it.tv ? 'broadcast transcript (' + it.tv.medium + (it.tv.network ? ', ' + it.tv.network : '') + (it.tv.role ? ', his role: ' + it.tv.role : '') + '): ' + it.tv.note + '; the headline is NewsBank’s episode rundown: shorten it to the segment he is in (SHOWNET-v1)' : '', p.thin ? 'citation page only, no text: no saved copy' : '', (p.flags || []).join('; '), p.outlet_note || '', it.linkNote ? 'publisher link not found: ' + it.linkNote : '', /\[[^\]]+\]/.test(p.outlet || '') && !/embargo|subscription|archive/i.test(p.outlet) ? 'NewsBank source “' + VS(p.outlet, 80) + '”: check show and network (SHOWNET-v1)' : ''].filter(Boolean).join('; ');
  if (!isRep && !it.pdf) { row['Saved Copy?'] = 'No'; }
  return row;   // an Original finds its pages doc by its temporary code (Tracker story code), a reprint by _page (set by proposeRows)
}
/* NewsBank's source object (ProQuest's is in proquest.js) */
const NBSRC = { nb: { id: 'nb', name: 'NewsBank', idName: 'NewsBank link', foundBy: 'newsbank-pdf', srcName: 'NewsBank', preface: NB_PREFACE, dateSrc: 'newsbank', print: p => !!p.page, runMode: 'newsbank', runMark: 'newsbank', metaKey: 'nb', runSource: 'NewsBank batch PDFs',
  known: () => nbDocrefs(), cand: nbCand, link: nbLink, plink: nbLink, html: (p, row) => NBParse.storyHtml(p, row), meta: nbMeta, rowFill: nbRowFill } };
window.__nb = { candidates: nbPrintCands, hasStory: nbHasStory, screen: nbScreen, remember: nbRemember, run: nbRun, docrefs: () => nbDocrefs().size, version: 1 };
