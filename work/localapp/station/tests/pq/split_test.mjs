// PQEXPORT-v1: splitting a multi-article ProQuest export (synthetic exports from make_pq_export.py) into articles, each read like a one-article PDF.
//   node split_test.mjs EXPORTDIR
import fs from 'fs'; import path from 'path'; import { createRequire } from 'module'; import { fileURLToPath, pathToFileURL } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url)), station = path.join(here, '..', '..');
const req = createRequire(import.meta.url);
const NB = req(path.join(station, 'src', 'nbparse.js')), PQ = req(path.join(station, 'src', 'pqparse.js'));
const pdfjs = await import(pathToFileURL(path.join(station, 'vendor', 'pdf.min.mjs')).href);
pdfjs.GlobalWorkerOptions.workerSrc = pathToFileURL(path.join(station, 'vendor', 'pdf.worker.min.mjs')).href;
const dir = process.argv[2], exp = JSON.parse(fs.readFileSync(path.join(dir, 'expected.json'), 'utf8'));
let fail = 0; const ok = (n, c, x) => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + String(x).slice(0, 300))); if (!c) fail++; };
async function readPdf(file) {
  const doc = await pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(file)), isEvalSupported: false, useSystemFonts: false, verbosity: 0 }).promise;
  const pages = [];
  for (let p = 1; p <= doc.numPages; p++) { const pg = await doc.getPage(p), tc = await pg.getTextContent(), v = pg.getViewport({ scale: 1 }); pages.push({ page: p, height: v.height, lines: NB.linesFromItems(tc.items) }); }
  return pages;
}
for (const [name, e] of Object.entries(exp)) {
  const n = e.arts.length, pages = await readPdf(path.join(dir, name + '.pdf'));
  const t0 = Date.now(), sp = PQ.splitPdf(pages);
  if (n === 1) { ok(name + ': one article is not split (single path)', sp === null, sp && sp.total); const r = PQ.parsePdf(pages); ok(name + ': read as before', r.status === 'ok' && r.headline === e.arts[0].hl && r.docid === e.arts[0].docid, JSON.stringify(r.problems)); continue; }
  ok(name + ': split into ' + n + ' articles', sp && sp.total === n, sp && sp.total);
  if (!sp || sp.total !== n) continue;
  const broken = new Set(e.kw.broken || []);
  let good = 0, bad = [];
  sp.parts.forEach((pt, k) => {
    const a = e.arts[k], r = PQ.parsePdf(pt.pages);
    if (broken.has(k + 1)) { ok(name + ': article ' + (k + 1) + ' (broken DETAILS) needs a look on its own', r.status === 'needs_look' && r.problems.length > 0, JSON.stringify([r.status, r.problems])); return; }
    const hit = r.status === 'ok' && r.headline === a.hl && r.docid === a.docid && r.date === a.date && r.author === a.by && r.outlet === a.pub.split(';')[0] && r.source_type === 'Trade Journal' && !r.page
      && r.url_in_pdf.includes('/docview/' + a.docid + '/') && /^"We have to get this done/.test(r.text) && r.text.endsWith(a.body.split(' ').slice(-3).join(' ')) && !/DETAILS|LINKS|Database copyright|ProQuest document link|FULL TEXT|Document \d+ of|PDF GENERATED|Documents \(/.test(r.text)
      && r.body_words === a.body.split(" ").length;
    if (hit) good++; else bad.push(k + 1 + ':' + r.status + ':' + r.headline + '|' + r.docid + '|' + r.body_words + '/' + (a.body.split(' ').length));
  });
  const want = n - broken.size;
  ok(name + ': the other ' + want + ' read exactly (headline, id, date, author, outlet, type, URL, text only)', good === want, bad.slice(0, 3).join(' ; '));
  ok(name + ': every part has bands, one per page, and page ranges rise', sp.parts.every((pt, k) => pt.bands.length === pt.pages.length && (k === 0 || pt.firstPage >= sp.parts[k - 1].lastPage)), JSON.stringify(sp.parts.slice(0, 3).map(p => [p.firstPage, p.lastPage])));
  ok(name + ': page counts match the parts', sp.parts.every(pt => PQ.parsePdf(pt.pages).pages === pt.pages.length));
  if (name === 'exp_6_contents' || name === 'exp_5_contents_nomarks') ok(name + ': the contents list is left out of every part', sp.parts.every(pt => !pt.pages.some(pg => pg.lines.some(l => /^Documents \(/.test(l.text)))), '');
  if (n >= 60) { const dt = Date.now() - t0; ok(name + ': split + read of 60 articles takes under 5 s (' + dt + ' ms)', dt < 5000, dt); }
}
// hand-made: two copies of a one-article layout with only anchors, a stray running header, an article with no authors line
{ const L = (text, y, h = 10, x = 60) => ({ y, x, h, text });
  const art = (id, hl) => [L(hl, 700, 14), L('ProQuest document link', 680), L('FULL TEXT', 660), L('The Assemblymember said this about the matter at some length today in the chamber.', 640), L('DETAILS', 600), L('Publication title:  Test Paper; City', 580), L('Publication date: Mar 3, 2026', 565), L('Source type: Newspaper', 550), L('ProQuest document ID: ' + id, 535), L('Database copyright  2026 ProQuest LLC. All rights reserved.', 500)];
  const sp = PQ.splitPdf([{ page: 1, height: 792, lines: art('1111111111', 'First story') }, { page: 2, height: 792, lines: art('2222222222', 'Second story') }]);
  ok('hand-made: two articles with no authors line and no markers are found', sp && sp.total === 2 && PQ.parsePdf(sp.parts[1].pages).headline === 'Second story' && PQ.parsePdf(sp.parts[0].pages).docid === '1111111111', JSON.stringify(sp && sp.total));
  const none = PQ.splitPdf([{ page: 1, height: 792, lines: [L('Details', 700), L('Publication title: A', 680), L('Document 1 of 1', 600)] }]);
  ok('hand-made: nothing to split gives null', none === null); }
console.log(fail ? fail + ' FAILED' : 'all passed'); process.exit(fail ? 1 : 0);
