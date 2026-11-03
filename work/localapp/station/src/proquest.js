/* PROQUESTPDF-v1: the ProQuest part of the Update station that needs the tracker's own functions. Like newsbank.js, this text is run INSIDE the
   tracker's function scope (build_station.py appends it to newsbank.js), so it uses covHit, dupOf, covLoad, D, VS, hash12 ... exactly as the Update
   button does. It adds only the ProQuest source object (NBSRC.pq): how a ProQuest story is recognised as already in the tracker, what its record
   link is, the preface for Claude, and how its row, its pages doc and its run doc are filled. The run itself (classify, publisher-link lookup,
   originator lookup, proposed rows, reprints, authors, translations, the run doc) is newsbank.js's nbRun, unchanged for NewsBank.

   Run doc: mode "hand" (the tracker's own label "Added by hand"; the run log would otherwise turn an unknown mode into "find"), plus proquest: <date> and
   pq: {...}. searched_to stays blank, so the Update's search window never moves. */

/* every ProQuest document the tracker already has: the id of any ProQuest link of any Coverage row, story or reprint ("pq:<id>", the key the parser gives) */
let PQX_IDS = null;
function pqIds(){
  if (!PQX_IDS){
    const s = PQX_IDS = new Set(), add = u => { const m = /proquest\.com\/docview\/(\d{5,})/i.exec(String(u || '')); if (m) s.add('pq:' + m[1]); };
    covLoad().rows.forEach(o => (o.links || []).forEach(add));
    D.forEach(r => { add(r.pq); add(r.link); add(r.plink); (r.reps || []).forEach(x => add(x && x.link)); });
  }
  return PQX_IDS;
}
/* PROQUESTPDF-v1 answer 2: the outlet's name. ProQuest names a paper its own way ("The Center Square; Washington"); the sheet holds the NewsBank form ("Center Square California, The").
   Before the dedupe (and for the row's Outlet) the PDF's outlet is turned into the tracker's own name by PQParse.resolveOutlet: a pair in data/proquest_outlets.json, else the
   tracker's own spelling of the same name (every Outlet of the sheet's rows and stories, most used spelling). A name nothing matches keeps ProQuest's name and the Team note says so. */
let PQX_OUT = null;
function pqOutIdx(){
  if (!PQX_OUT){
    const ex = new Map(), fo = new Map(), cnt = new Map();
    const add = n => { n = String(n || '').trim(); if (n) cnt.set(n, (cnt.get(n) || 0) + 1); };
    covLoad().rows.forEach(o => add(o.outlet));
    D.forEach(r => add(String(r.outlet || '').replace(/\s*\([^)]*\)\s*$/, '')));   /* the sheet's Outlet names only (r.pub is a display name) */
    const best = (m, k, n) => { const c = cnt.get(n); const o = m.get(k); if (!o || c > o.c || (c === o.c && n < o.n)) m.set(k, { n, c }); };
    cnt.forEach((c, n) => { const k = PQParse.outletKeys(n); if (k.exact) { best(ex, k.exact, n); best(fo, k.fold, n); } });
    const flat = m => { const o = new Map(); m.forEach((v, k) => o.set(k, v.n)); return o; };
    PQX_OUT = { exact: flat(ex), fold: flat(fo) };
  }
  return PQX_OUT;
}
function pqResolve(p){
  if (p._ol) return p; p._ol = true;
  p.outlet_pq = p.outlet_clean;
  const r = PQParse.resolveOutlet(p.outlet_clean, [String(p.pubtitle || '').split(';').slice(1).join(' '), p.place].join(' '), pqOutIdx());
  p.outlet_how = r.how;
  if ((r.how === 'pair' || r.how === 'tracker') && r.name !== p.outlet_clean){ p.outlet_note = 'outlet “' + p.outlet_clean + '” (ProQuest) filed as “' + r.name + '” (' + r.src + ')'; p.outlet_clean = r.name; }
  else if (r.how === 'unknown') (p.flags || (p.flags = [])).push('outlet name from ProQuest; check');
  else if (r.how === 'generic') (p.flags || (p.flags = [])).push('outlet name from ProQuest; check (“' + p.outlet_clean + '” is a generic name: the tracker keeps one outlet per city, and none matched)');
  return p;
}

/* the record's link. A PDF with no readable document id has none; the tab then uses a stand-in so the tracker's own code (which keys finds by link)
   still works. The stand-in is never written to the sheet (pqRowFill leaves the ProQuest link blank for it). */
const pqReal = p => p.link || '';
const pqLink = p => p.link || ('https://www.proquest.com/docview/0?pdf=' + hash12(normH(p.headline) + '|' + (p.date || '') + '|' + normH(p.outlet_clean)));
const pqCand = p => ({ link: pqLink(p), hl: p.headline, date: p.date, outlet: p.outlet_clean, pub: p.outlet_clean, plink: '' });
/* a print record: ProQuest gives a page for a newspaper or magazine (the sheet's "print edition" ProQuest rows) */
const pqPrint = p => !!p.page && /newspaper|magazine|periodical|journal|trade/i.test(p.source_type || '');

const PQ_PREFACE = `These items are ProQuest article PDFs from the State Library's ProQuest, read in the browser. The url is ProQuest's record (or a stand-in when the PDF gave no document id), the text is the article's full text from the PDF, and the first line of the text lists ProQuest's own details (publication, source type, language of publication, publisher). Three things differ from web results: (1) the text is the complete article, so a story whose text does not name Jesse Gabriel the Assemblymember is not his coverage: keep false for that, for another person named Jesse Gabriel, and for anything that is not press (an advocacy group's or an official's own release, a database or listing); (2) the date and the outlet are ProQuest's and are right: copy them; (3) the headline is ProQuest's own: copy it. Use the details line for medium (a "Wire Feed" source is Wire) and language.\n\n`;

function pqMeta(it){
  const p = it.p, b = it.batch;
  return { docid: p.docid, url: pqReal(p), file: it.pdf ? 'files/' + it.fileId + '.pdf' : '', pdf_sha256: it.pdf ? it.pdf.sha256 : '', pdf_bytes: it.pdf ? it.pdf.bytes : 0,
    source_name: b.name, source_sha256: b.sha256, pages: p.pages,
    header: { headline: p.headline, date: p.date, publication_title: p.pubtitle, outlet: p.outlet, outlet_filed_as: p.outlet_clean, outlet_how: p.outlet_how || '', author: p.author, section: p.section, pages: p.page, publisher: p.publisher, place: p.place,
      source_type: p.source_type, document_type: p.doc_type, language: p.language, issn: p.issn, copyright: p.copyright, database: p.database, publication_date_text: p.pubdate_raw },
    flags: p.flags || [], how: p.how };
}
/* what ProQuest, not the web, gives a row: Data Source "ProQuest", Date source "ProQuest" ("print edition" for a print record), the ProQuest links in their
   two columns (the second through the State Library's login, as the sheet holds it). File name, File type, Saved Copy? and Word count are the PC save's. */
function pqRowFill(row, it){
  const p = it.p, isRep = row['Original or reprint'] === 'Reprint', printed = pqPrint(p), real = pqReal(p);
  row['Data Source'] = 'ProQuest'; row['Date source'] = printed ? 'print edition' : 'ProQuest';
  row._date_src = 'proquest';
  row['ProQuest link'] = real; row['ProQuest via CA State Library'] = real ? PQParse.viaLink(p.docid) : '';
  row['Publisher link'] = it.pub ? it.pub.url : ''; row['Link status'] = it.pub ? it.pub.status : '';
  row['Section'] = ''; row['Page'] = '';   /* PROQUESTPDF-v1 answer 1: Section and Page stay blank on ProQuest rows, always (the page only decides Print below) */
  row['Edition'] = printed ? 'Print' : ''; row['Format'] = printed ? 'Print' : (row['Format'] === 'Article' || !row['Format'] ? 'Article' : row['Format']);
  row['Headline'] = p.headline; row['Date'] = p.date; row['Year'] = p.date ? +p.date.slice(0, 4) : '';
  if (isRep){ row['Author / byline'] = p.author || ''; row['Tracker story code'] = ''; }
  if (it.pr){ row._pr = window.__prRecord(it.pr); if (it.pr.v === 'yes') row['Press release'] = 'Yes'; }   // PRJUDGE-v1
  row['Team note'] = [it.pr && it.pr.v === 'yes' ? 'press release: ' + VS(it.pr.why, 220) : '', 'ProQuest PDF ' + it.batch.name + ' (' + TODAY + ')', (p.flags || []).join('; '), p.outlet_note || '', it.linkNote ? 'publisher link not found: ' + it.linkNote : ''].filter(Boolean).join('; ');
  return row;
}
NBSRC.pq = { id: 'pq', name: 'ProQuest', idName: 'ProQuest document id', foundBy: 'proquest-pdf', srcName: 'ProQuest, full text', preface: PQ_PREFACE, dateSrc: 'proquest', print: pqPrint,
  runMode: 'hand', runMark: 'proquest', metaKey: 'pq', runSource: 'ProQuest article PDFs',
  hint: p => '[ProQuest details: ' + [p.pubtitle && 'Publication: ' + p.pubtitle, p.source_type && 'Source type: ' + p.source_type, p.language && 'Language of publication: ' + p.language, p.publisher && 'Publisher: ' + p.publisher, p.section && 'Section: ' + p.section].filter(Boolean).join('; ') + ']\n',
  known: () => pqIds(), cand: pqCand, link: pqLink, plink: () => '', pq: pqReal, html: (p, row) => PQParse.storyHtml(p, row), meta: pqMeta, rowFill: pqRowFill };
window.__pq = { screen: p => nbScreen(pqResolve(p), NBSRC.pq), resolve: pqResolve, remember: nbRemember, run: (items, opts) => nbRun(items, Object.assign({}, opts, { src: NBSRC.pq })), ids: () => pqIds().size, version: 1 };
