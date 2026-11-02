// Unit test of src/pqparse.js: on the synthetic ProQuest PDFs (read with the vendored pdf.js, node) and on hand-made line lists for the layouts the PDFs do not cover.
//   node parse_test.mjs PDFDIR
import fs from 'fs'; import path from 'path'; import { createRequire } from 'module'; import { fileURLToPath, pathToFileURL } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url)), station = path.join(here, '..', '..');
const req = createRequire(import.meta.url);
const NB = req(path.join(station, 'src', 'nbparse.js')), PQ = req(path.join(station, 'src', 'pqparse.js'));
const pdfjs = await import(pathToFileURL(path.join(station, 'vendor', 'pdf.min.mjs')).href);
pdfjs.GlobalWorkerOptions.workerSrc = pathToFileURL(path.join(station, 'vendor', 'pdf.worker.min.mjs')).href;
const dir = process.argv[2], exp = JSON.parse(fs.readFileSync(path.join(dir, 'expected.json'), 'utf8')), E = exp.stories;
let fail = 0; const ok = (n, c, x) => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + x)); if (!c) fail++; };
async function readPdf(file) {
  const doc = await pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(file)), isEvalSupported: false, useSystemFonts: false, verbosity: 0 }).promise;
  const pages = [];
  for (let p = 1; p <= doc.numPages; p++) { const pg = await doc.getPage(p), tc = await pg.getTextContent(), v = pg.getViewport({ scale: 1 }); pages.push({ page: p, height: v.height, lines: NB.linesFromItems(tc.items) }); }
  return pages;
}
// --- the generated PDFs ---
for (const k of ['new3page', 'es', 'zh', 'nourl', 'noid', 'wire', 'noheading', 'known_id', 'known_hl', 'rep_other', 'dupe_v2']) {
  const e = E[k], r = PQ.parsePdf(await readPdf(path.join(dir, k + '.pdf')));
  ok(k + ': status ok', r.status === 'ok', JSON.stringify(r.problems));
  ok(k + ': headline', r.headline === e.hl, r.headline);
  ok(k + ': date', r.date === e.date, r.date);
  ok(k + ': outlet is the publication title before the “;”', r.outlet === e.pub.split(';')[0].trim(), r.outlet);
  ok(k + ': ' + e.pages + ' page(s) counted', r.pages === e.pages, r.pages);
  if (e.docid && !e.drop.includes('ProQuest document ID')) ok(k + ': ProQuest document ID and its link', r.docid === e.docid && r.link === 'https://www.proquest.com/docview/' + e.docid, r.docid + ' ' + r.link);
  else ok(k + ': no ProQuest document ID, no link, and it says so', r.docid === '' && r.link === '' && r.flags.some(f => /no ProQuest document ID/.test(f)), JSON.stringify(r.flags));
  ok(k + ': the text is the article only (no heading, details, footer)', !/PDF GENERATED|Page \d of \d|Document URL|ProQuest document ID|Publication title|^Details$/m.test(r.text) && !r.text.includes(e.hl.slice(0, 25)) && (r.body_words > 40 || r.text.length > 100), r.text.slice(0, 120));
  ok(k + ': Gabriel is in the text', /Gabriel|加布里埃尔/.test(r.text));
}
{ const r = PQ.parsePdf(await readPdf(path.join(dir, 'new3page.pdf')));
  ok('new3page: author “First Last” from “Last, First”; section; page; publisher; place; source type; database', r.author === 'Dana Whitfield' && r.section === 'California' && r.page === 'A3' && r.publisher === 'Valley Ledger Media' && r.place === 'Van Nuys, Calif.' && r.source_type === 'Newspapers' && r.database === 'ProQuest Central', JSON.stringify([r.author, r.section, r.page, r.publisher, r.place, r.source_type, r.database]));
  ok('new3page: the wrapped Document URL is joined and agrees with the ID', r.url_in_pdf.startsWith('https://www.proquest.com/docview/3411000001/') && /accountid=13802$/.test(r.url_in_pdf), r.url_in_pdf);
  ok('new3page: paragraphs keep their order and nothing is lost between pages', r.paras.length === 4 && r.body_words > 900, r.paras.length + ' ' + r.body_words); }
{ const r = PQ.parsePdf(await readPdf(path.join(dir, 'es.pdf'))); ok('es: two authors joined with “and”, language Spanish, details-first layout', r.author === 'Marta Lopez and Carlos Reyes' && r.language === 'Spanish', r.author + ' / ' + r.language); }
{ const r = PQ.parsePdf(await readPdf(path.join(dir, 'noheading.pdf'))); ok('noheading: no Title field -> the large heading is used and flagged', r.how === 'heading' && r.flags.some(f => /page heading/.test(f)) && r.headline === E.noheading.hl, JSON.stringify([r.how, r.flags])); }
const bad = { partialdate: /no day/, nopubtitle: /publication title/, two_articles: /more than one article/, scanned: /no readable text/, unrelated: /does not look like a ProQuest/, newsbank_one: /NewsBank PDF/ };
for (const [k, rx] of Object.entries(bad)) { const r = PQ.parsePdf(await readPdf(path.join(dir, k + '.pdf'))); ok(k + ': not “ok”, with the reason in plain words', r.status !== 'ok' && r.problems.some(p => rx.test(p)), r.status + ' ' + JSON.stringify(r.problems)); }
// --- hand-made lines: layouts the generator does not draw ---
const L = (text, y, h = 10, x = 60) => ({ y, x, h, text });
const pg = (lines, n = 1) => ({ page: n, height: 792, lines });
const seq = (arr, y0 = 700, step = 13) => arr.map((t, i) => Array.isArray(t) ? L(t[0], y0 - i * step, t[1]) : L(t, y0 - i * step));
const BODY0 = 'The county board voted on Tuesday to expand the clinic hours after Assemblymember Jesse Gabriel (D-Encino) urged the members to act before the winter season begins in earnest.';
const BODY = BODY0 + ' ' + BODY0.replace('Tuesday', 'Wednesday') + ' ' + BODY0.replace('clinic', 'library');
{ // a table layout: no colons on the distinctive labels, label and value on one line
  const r = PQ.parsePdf([pg(seq([['Clinic hours expand after vote', 16], 'Title: Clinic hours expand after vote', 'Publication title The Daily Test; Sacramento, Calif.', 'Publication date Oct 3, 2026', 'Source type Newspapers', 'Language of publication English', 'ProQuest document ID 3400000099', 'Document URL https://www.proquest.com/docview/3400000099',
    ['Full text', 11], BODY, BODY + ' More.']))]);
  ok('colon-less distinctive labels are read (table layout)', r.status === 'ok' && r.outlet === 'The Daily Test' && r.date === '2026-10-03' && r.docid === '3400000099', JSON.stringify([r.status, r.outlet, r.date, r.docid, r.problems]));
  ok('the text after “Full text” is the body, the heading above it is not', r.text.startsWith('The county board') && !r.text.includes('Clinic hours expand'), r.text.slice(0, 80)); }
{ // label on a line of its own, value on the next
  const r = PQ.parsePdf([pg(seq(['Title:', 'A very long headline about Gabriel and the hospital district budget', 'Publication title:', 'Test Gazette; Fresno, Calif.', 'Publication date:', '13 Sep 2024', 'ProQuest document ID:', '3399999999', 'Source type: Newspapers', ['FULL TEXT', 11], BODY]))]);
  ok('a label with its value on the next line is read', r.status === 'ok' && r.headline.startsWith('A very long headline') && r.outlet === 'Test Gazette' && r.date === '2024-09-13' && r.docid === '3399999999', JSON.stringify([r.status, r.headline, r.outlet, r.date, r.docid, r.problems])); }
{ // body text that merely contains label-like words must not become metadata
  const r = PQ.parsePdf([pg(seq(['Title: The real headline of the story', 'Publication title: Test Gazette; Fresno, Calif.', 'Publication date: Sep 13, 2024', 'ProQuest document ID: 3399999998', 'Document type: News', ['FULL TEXT', 11],
    'Section: this word list is part of the article text and is not metadata, said Jesse Gabriel.', 'The date: Sep 14, 2025 is mentioned later in the text by Assemblymember Jesse Gabriel as the deadline.', BODY]))]);
  ok('label-like words in the article text are not metadata', r.status === 'ok' && r.date === '2024-09-13' && r.section === '' && /Section: this word list/.test(r.text), JSON.stringify([r.date, r.section, r.text.slice(0, 80)])); }
{ // the details block spread over two pages, wrapped title, document URL wrapped
  const r = PQ.parsePdf([pg(seq(['A headline that is long enough that the details block wraps it', BODY, ['Details', 11], 'Title: A headline that is long enough that the details block', 'wraps it', 'Publication title: Test Gazette; Fresno, Calif.'])),
    pg(seq(['Publication date: Sep 13, 2024', 'Pages: A1, A10', 'ProQuest document ID: 3399999997', 'Document URL: https://www.proquest.com/docview/3399999997/ABCDEF/1?', 'accountid=13802', 'Source type: Newspapers', 'Database: ProQuest Central']), 2)]);
  ok('a wrapped Title and URL, and a details block that runs onto page 2, are joined', r.status === 'ok' && r.headline === 'A headline that is long enough that the details block wraps it' && r.docid === '3399999997' && /accountid=13802$/.test(r.url_in_pdf) && r.page === 'A1', JSON.stringify([r.status, r.headline, r.page, r.url_in_pdf, r.problems]));
  ok('…and none of it is left in the text', r.text.trim() === BODY.trim(), r.text.slice(0, 160)); }
{ // ID and URL that disagree
  const r = PQ.parsePdf([pg(seq(['Title: Headline', 'Publication title: T; X', 'Publication date: Sep 13, 2024', 'ProQuest document ID: 3399999997', 'Document URL: https://www.proquest.com/docview/3000000000/1', ['FULL TEXT', 11], BODY, BODY]))]);
  ok('a document ID and a URL that name different articles: needs a look', r.status === 'needs_look' && r.problems.some(p => /different articles/.test(p)), JSON.stringify(r.problems)); }
{ // only a URL: the id comes from it
  const r = PQ.parsePdf([pg(seq(['Title: Headline here for a test', 'Publication title: T; X', 'Publication date: Sep 13, 2024', 'Document URL: https://www.proquest.com/docview/3388888888/ABC/1?accountid=1', 'Source type: Newspapers', ['FULL TEXT', 11], BODY, BODY]))]);
  ok('a Document URL with no ID line gives the ID', r.status === 'ok' && r.docid === '3388888888' && r.link === 'https://www.proquest.com/docview/3388888888', JSON.stringify([r.status, r.docid, r.problems])); }
{ // labels the reader does not know (First page, Number of pages, Identifier / keyword ...) sit inside the block without splitting it
  const r = PQ.parsePdf([pg(seq([['A headline for the unknown labels test', 15], BODY, ['Details', 11], 'Subject: Legislation; Housing', 'Location: California', 'Publication title: Test Gazette; Fresno, Calif.', 'First page: A3', 'Publication year: 2024', 'Publication date: Sep 13, 2024',
    'Number of pages: 2', 'Identifier / keyword: housing; AB 1924', 'Source type: Newspapers', 'Document type: News', 'ProQuest document ID: 3377777777', 'Database: ProQuest Central']))]);
  ok('unknown “Label: value” lines do not split the details block; First page gives the page', r.status === 'ok' && r.outlet === 'Test Gazette' && r.date === '2024-09-13' && r.page === 'A3' && r.docid === '3377777777' && r.text.trim() === BODY.trim(), JSON.stringify([r.status, r.outlet, r.page, r.docid, r.text.slice(0, 60), r.problems])); }
for (const [s, iso] of [['Sep 13, 2024', '2024-09-13'], ['September 13, 2024', '2024-09-13'], ['13 Sep 2024', '2024-09-13'], ['13 September 2024', '2024-09-13'], ['2024-09-13', '2024-09-13'], ['Sep. 3, 2024', '2024-09-03'], ['Sept 3, 2024', '2024-09-03'], ['Feb 30, 2024', '']])
  ok('date “' + s + '”', PQ.parseDate(s).iso === iso, JSON.stringify(PQ.parseDate(s)));
ok('month and year only is partial, not a date', PQ.parseDate('Sep 2024').partial === true && PQ.parseDate('Sep 2024').iso === '' && PQ.parseDate('2024').partial === true);
ok('outlet names: edition suffixes and places go', PQ.outletOf('New York Times, Late Edition (East Coast); New York, N.Y.') === 'New York Times' && PQ.outletOf('Los Angeles Times; Los Angeles, Calif.') === 'Los Angeles Times' && PQ.outletOf('The Center Square ; Washington') === 'The Center Square');
ok('bylines', PQ.bylineOf('Shannon, Madeline') === 'Madeline Shannon' && PQ.bylineOf('Madeline Shannon') === 'Madeline Shannon' && PQ.bylineOf('Rogers, Paul; Stringer, Grant') === 'Paul Rogers and Grant Stringer' && PQ.bylineOf('A, B; C, D; E, F') === 'B A, D C and F E');
ok('docview id from every URL form', PQ.docviewId('https://www.proquest.com/docview/3396453901') === '3396453901' && PQ.docviewId('https://castatelib.idm.oclc.org/login?url=https://www.proquest.com/docview/3396453901') === '3396453901' && PQ.docviewId('https://search.proquest.com/docview/12345678/abstract/AB/1?accountid=1') === '12345678' && PQ.docviewId('https://example.com/docview/123456') === '');
console.log(fail ? fail + ' FAILED' : 'all passed'); process.exit(fail ? 1 : 0);
