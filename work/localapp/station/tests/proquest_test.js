/* Playwright test of the "Add ProQuest PDFs" card (PROQUESTPDF-v1). Run:
     node tests/proquest_test.js --page dist/index.html --file FOR_UPDATE.json --pdfs PDFDIR --out OUTDIR
   PDFDIR comes from tests/pq/make_pq_pdfs.py. Same set-up as newsbank_test.js: the page is served on 127.0.0.1 inside the skeleton the Artifact tool adds,
   under a strict Content-Security-Policy (inline scripts only; no eval, no worker, no blob: script, no connections); window.claude is a stub (db in
   memory, TinyFish search / fetch canned, sample canned); the downloaded zip is written to OUTDIR (checked afterwards by tests/pq/verify_pq_zip.py). */
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page'), FILE = arg('file'), PDFS = arg('pdfs'), OUT = arg('out');
fs.mkdirSync(OUT, { recursive: true });
let failed = 0; const check = (name, ok, extra) => { if (!ok) failed++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (!ok && extra !== undefined ? '  -> ' + extra : '')); };
const exp = JSON.parse(fs.readFileSync(path.join(PDFS, 'expected.json'), 'utf8')), E = exp.stories;
const laDay = (d = new Date()) => d.toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' });
const TODAY = laDay();

const shellHead = (() => { const vd = path.join(__dirname, '..', '..', 'vendor'); return fs.readFileSync(path.join(vd, fs.readdirSync(vd).filter(d => d.startsWith('live_')).sort().pop(), 'pipeline', 'shell.html'), 'utf8').split('<body>')[0] + '<body>'; })();
const wrapped = shellHead + fs.readFileSync(PAGE, 'utf8') + '</body></html>';
const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; worker-src 'none'; connect-src 'none'";
const server = http.createServer((req, res) => {
  if (req.url.split('?')[0] === '/index.html' || req.url === '/') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Security-Policy': CSP }); res.end(wrapped); }
  else { res.writeHead(404); res.end('no'); }
});

const INIT = ({ hl }) => {
  const st = window.setTimeout.bind(window);
  window.setTimeout = (f, d, ...a) => st(f, d >= 300 ? Math.max(1, d / 100) : d, ...a);
  const realNow = Date.now.bind(Date), t0 = realNow(); Date.now = () => t0 + (realNow() - t0) * 100;
  window.__calls = []; window.__dl = []; window.__workers = 0; window.__texts = {};
  window.Worker = function () { window.__workers++; throw new Error('workers are not allowed here'); };
  const load = () => { try { return JSON.parse(localStorage.getItem('__fakedb')) || {}; } catch (e) { return {}; } }, save = o => localStorage.setItem('__fakedb', JSON.stringify(o));
  Object.defineProperty(window, '__realdb', { get: () => load() });
  const fakeDb = { collection: n => ({ doc: id => ({ set: async d => { const o = load(); (o[n] = o[n] || {})[id] = JSON.parse(JSON.stringify(d)); save(o); }, delete: async () => {}, get: async () => { const d = (load()[n] || {})[id]; return { exists: !!d, data: () => d }; } }),
    get: async () => ({ docs: Object.entries(load()[n] || {}).map(([id, d]) => ({ id, data: () => d })) }), onSnapshot: cb => { cb({ docs: Object.entries(load()[n] || {}).map(([id, d]) => ({ id, data: () => d })) }); return () => {}; } }) };
  const PUB = 'https://www.dailyvalleyledger-test.com/news/gabriel-wildfire-insurance-delays', BLK = 'https://www.resedacourier-test.com/news/lunch-funding';
  const mcp = { callTool: async (server, tool, input) => {
    window.__calls.push({ tool, q: input.query || (input.urls || []).join(' ') });
    if (tool === 'search') { const q = String(input.query || '').replace(/^"|"$/g, '');
      if (q === hl.new3page) return { payload: { results: [{ url: PUB, title: hl.new3page + ' - Daily Valley Ledger Test', date: '2026-10-29', publisher: 'Daily Valley Ledger Test' }, { url: 'https://www.proquest.com/docview/1', title: hl.new3page, date: '2026-10-29' }] } };
      if (q === hl.nourl) return { payload: { results: [{ url: BLK, title: hl.nourl + ' | Reseda Courier Test', date: '2026-10-26', publisher: 'Reseda Courier Test' }] } };
      return { payload: { results: [] } }; }
    if (tool === 'fetch_content') return { payload: { results: (input.urls || []).filter(u => u === PUB).map(u => ({ url: u, final_url: u, title: hl.new3page, text: '<html><body><article><h1>' + hl.new3page + '</h1><p>' + (window.__texts.new3page || '') + '</p></article></body></html>', published_date: '' })),
      errors: (input.urls || []).filter(u => u === BLK).map(u => ({ url: u, error: '403 Forbidden: blocked' })) } };
    return { payload: {} };
  } };
  const sample = async () => ({ text: '', truncated: false });
  sample.json = async prompt => {
    window.__calls.push({ tool: 'sample', q: String(prompt).slice(0, 50) });
    window.__lastPrompt = String(prompt);
    if (/^These items are ProQuest article PDFs/.test(prompt)) {
      return [...prompt.matchAll(/=== ITEM (\d+)\nURL: (\S+)\nPage title: (.*)\n/g)].map(m => {
        const t = m[3], r = { n: +m[1], keep: true, why: 'ProQuest story naming him.', date: '', outlet: '', pub: '', hl: t, topic: 'State budget', media: 'Newspaper', role: 'Mentioned in story', tone: 'Neutral', twhy: 'Straight news.', author: '', lang: '', hl_en: '', text_en: '' };
        if (t === hl.wire) return Object.assign(r, { keep: false, why: 'A wire digest item, not press.' });
        if (/加布里埃尔/.test(t)) return Object.assign(r, { lang: 'Chinese', hl_en: 'Assemblymember Gabriel pushes California budget bill', text_en: 'He said the budget committee will review housing and wildfire spending.' });
        if (/^Gabriel presenta/.test(t)) return Object.assign(r, { lang: 'Spanish', hl_en: '' });
        return r; });
    }
    if (/^Translate each news headline/.test(prompt)) return [...prompt.matchAll(/id=(\S+) \((\w+),/g)].map(m => ({ id: m[1], hl: 'Gabriel presents a bill to speed up affordable housing construction' }));
    return [];
  };
  window.claude = { use: async name => name === 'db' ? fakeDb : name === 'mcp' ? mcp : name === 'sample' ? sample : name === 'downloads' ? { save: async ({ filename, data }) => { const buf = new Uint8Array(await data.arrayBuffer()); window.__dl.push({ filename, size: buf.length }); window.__lastDl = buf; } } : null };
};

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1300, height: 1100 }, acceptDownloads: true });
  await ctx.addInitScript(INIT, { hl: { new3page: E.new3page.hl, nourl: E.nourl.hl, wire: E.wire.hl } });
  await ctx.addInitScript(() => { try { localStorage.setItem('ajg_station_auto', '0'); } catch (e) {} });   // AUTOSTATION-v1: these tests click each step themselves (the automatic mode has its own test)
  const outside = []; await ctx.route(u => !/^(http:\/\/127\.0\.0\.1[:/]|data:|blob:|about:)/.test(u.href), r => { outside.push(r.request().url()); r.abort(); });
  const page = await ctx.newPage();
  const errors = []; page.on('pageerror', e => errors.push('pageerror: ' + e.message)); page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  const cspViol = []; page.on('console', m => { if (/Content Security Policy/i.test(m.text())) cspViol.push(m.text()); });

  await page.goto(base + '/index.html'); await page.waitForSelector('#pqDrop');
  check('the ProQuest card is on the page, locked until a file is loaded', await page.locator('#st-pq.st-lock').count() === 1);
  await page.setInputFiles('#pqFile', path.join(PDFS, 'new3page.pdf'));
  await page.waitForSelector('#pqMsg:not([hidden])');
  check('PDFs dropped before the for-Update file are refused with a plain message', /Load the for Update file first/.test(await page.textContent('#pqMsg')), await page.textContent('#pqMsg'));
  await page.setInputFiles('#stFile', FILE); await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 90000 });
  await page.waitForFunction(() => window.__pq && window.__pq.version === 1 && window.__nb && window.__nb.version === 1, null, { timeout: 30000 });
  check('after loading the file the card is unlocked and the ProQuest code is in the tracker scope, with the tracker’s ProQuest ids', await page.locator('#st-pq.st-lock').count() === 0 && await page.evaluate(() => window.__pq.ids() > 300), await page.evaluate(() => window.__pq.ids()));

  /* everything in one drop: the good ones, the same file twice, a second download of the same article, the collisions, the refusals, and a non-PDF */
  fs.writeFileSync(path.join(OUT, 'notes.pdf'), 'These are my notes, not a PDF at all.\n');
  const names = ['new3page', 'new3page_copy', 'dupe_v2', 'es', 'zh', 'nourl', 'noid', 'wire', 'noheading', 'known_id', 'known_hl', 'known_cs', 'known_nyt', 'known_wsj', 'known_mundo', 'known_lat', 'unknown_outlet', 'rep_other', 'partialdate', 'nopubtitle', 'two_articles', 'unrelated', 'newsbank_one', 'scanned'];
  await page.setInputFiles('#pqFile', names.map(n => path.join(PDFS, n + '.pdf')).concat([path.join(OUT, 'notes.pdf')]));
  await page.waitForFunction(n => window.__station.state.pq.files.length === n && window.__station.state.pq.files.every(f => f.status !== 'reading') && !window.__station.state.pq.reading, names.length + 1, { timeout: 180000 });
  const files = await page.evaluate(() => window.__station.state.pq.files.map(f => ({ name: f.name, status: f.status, note: f.note, pages: f.pages })));
  const fby = n => files.find(f => f.name === n + '.pdf');
  check('the byte-identical copy is skipped and says so', fby('new3page_copy').status === 'same' && /identical to “new3page.pdf”/.test(fby('new3page_copy').note), JSON.stringify(fby('new3page_copy')));
  check('a file that is not a PDF is refused in plain words', fby('notes') && fby('notes').status === 'error' && /not a PDF file/.test(fby('notes').note), JSON.stringify(fby('notes')));
  check('the 3-page article is read as 3 pages', fby('new3page').pages === 3 && E.new3page.pages === 3, JSON.stringify(fby('new3page')));

  const items = await page.evaluate(() => window.__station.state.pq.items.map(it => ({ key: it.key, file: it.batch.name, st: it.screen.status, of: it.screen.of, why: it.screen.why, hl: it.p.headline, date: it.p.date, outlet: it.p.outlet_clean, docid: it.p.docid, link: it.p.link, author: it.p.author,
    section: it.p.section, page: it.p.page, lang: it.p.language, flags: it.p.flags, pdf: it.pdf && it.pdf.bytes, fileId: it.fileId, words: it.p.body_words, include: it.include, problems: it.p.problems })));
  const I = n => items.find(i => i.file === n + '.pdf');
  const S1 = n => I(n).st;
  check('statuses: new = new3page, es, zh, nourl, noid, wire, noheading, unknown_outlet', ['new3page', 'es', 'zh', 'nourl', 'noid', 'wire', 'noheading', 'unknown_outlet'].every(n => S1(n) === 'new'), JSON.stringify(items.map(i => i.file + ':' + i.st)));
  check('3-page article: headline, date, outlet, author, section, page and ProQuest id read from the details block', I('new3page').hl === E.new3page.hl && I('new3page').date === '2026-10-29' && I('new3page').outlet === 'Daily Valley Ledger Test' && I('new3page').author === 'Dana Whitfield' && I('new3page').section === 'California' && I('new3page').page === 'A3' && I('new3page').docid === '3411000001' && I('new3page').link === 'https://www.proquest.com/docview/3411000001', JSON.stringify(I('new3page')));
  check('every new story has its PDF copied (pdf-lib), named pq-<16 hex>', ['new3page', 'es', 'zh', 'nourl', 'noid', 'wire', 'noheading'].every(n => I(n).pdf > 1000 && /^pq-[0-9a-f]{16}$/.test(I(n).fileId)), JSON.stringify(items.map(i => [i.file, i.pdf, i.fileId])));
  check('details block placed before the text (layout B) is read too: Spanish story, two authors joined with “and”', I('es').author === 'Marta Lopez and Carlos Reyes' && I('es').date === '2026-10-28' && I('es').lang === 'Spanish' && I('es').outlet === 'La Opinión Test', JSON.stringify(I('es')));
  check('the Chinese headline and text are read', /加布里埃尔议员推动加州预算法案/.test(I('zh').hl) && I('zh').outlet === 'World Journal Test', I('zh').hl);
  check('a details block with no Document URL: the link is built from the ProQuest document ID', I('nourl').st === 'new' && I('nourl').link === 'https://www.proquest.com/docview/3411000004', JSON.stringify(I('nourl')));
  check('a details block with neither ID nor URL: added, with no ProQuest link and a plain flag', I('noid').st === 'new' && I('noid').link === '' && I('noid').flags.some(f => /no ProQuest document ID/.test(f)), JSON.stringify(I('noid')));
  check('no Title in the details: the page heading is used and flagged "check"', I('noheading').hl === E.noheading.hl && I('noheading').flags.some(f => /page heading/.test(f)), JSON.stringify(I('noheading')));
  check('already in the tracker by ProQuest document ID (even with a changed headline)', S1('known_id') === 'known' && /ProQuest document id/.test(I('known_id').why), JSON.stringify(I('known_id')));
  check('already in the tracker by headline, outlet and date (a ProQuest id the tracker does not have)', S1('known_hl') === 'known' && /same outlet and headline/.test(I('known_hl').why), JSON.stringify(I('known_hl')));
  /* PROQUESTPDF-v1 answer 2: the story is in the tracker under its NewsBank name; the PDF carries ProQuest's name for the outlet. Not a reprint, not new: already there */
  for (const [k, ProQ] of [['known_cs', 'The Center Square; Washington'], ['known_nyt', 'New York Times, Late Edition (East Coast); New York, N.Y.'], ['known_wsj', 'Wall Street Journal (Online); New York, N.Y.'], ['known_mundo', 'El Mundo; Madrid, Spain'], ['known_lat', 'Los Angeles Times (pre-1997 Fulltext); Los Angeles, Calif.']]) {
    const ar = exp.existing.alias_rows[k];
    check('ProQuest name “' + ProQ + '” is the tracker’s “' + ar.outlet + '”: the story (' + ar.aid + ') is already in the tracker, not a reprint', S1(k) === 'known' && I(k).outlet === ar.outlet && /already in the tracker \(same outlet and headline/.test(I(k).why), JSON.stringify(I(k)));
  }
  check('a ProQuest outlet name the tracker does not know is kept as ProQuest has it, flagged “outlet name from ProQuest; check”, and is not guessed into another outlet', S1('unknown_outlet') === 'new' && I('unknown_outlet').outlet === 'Fresno Brand New Gazette Test' && I('unknown_outlet').flags.includes('outlet name from ProQuest; check'), JSON.stringify(I('unknown_outlet')));
  check('Section and Page are read from the PDF but only decide Print internally (the rows below carry neither)', I('new3page').section === 'California' && I('new3page').page === 'A3');
  check('another outlet with the same headline as a story in the tracker: a reprint of it', S1('rep_other') === 'reprint' && I('rep_other').of === exp.existing.rep_story, JSON.stringify(I('rep_other')));
  check('a second download of an article already in this session (different bytes, same ProQuest ID) is a repeat', S1('dupe_v2') === 'dup_batch' && /twice in the PDFs added/.test(I('dupe_v2').why), JSON.stringify(I('dupe_v2')));
  check('a publication date with no day needs a look and says why in plain words', S1('partialdate') === 'needs_look' && /no day/.test(I('partialdate').why) && !I('partialdate').include, I('partialdate').why);
  check('details without a publication title: needs a look, not guessed', S1('nopubtitle') === 'needs_look' && /publication title/.test(I('nopubtitle').why) && /not guessed/.test(I('nopubtitle').why), I('nopubtitle').why);
  check('two articles in one PDF: needs a look', S1('two_articles') === 'needs_look' && /more than one article/.test(I('two_articles').why), I('two_articles').why);
  check('a scanned image with no text: needs a look', S1('scanned') === 'needs_look' && /no readable text/.test(I('scanned').why), I('scanned').why);
  check('an unrelated PDF (an invoice) is refused in plain words', S1('unrelated') === 'refused' && /does not look like a ProQuest article PDF/.test(I('unrelated').why), I('unrelated').why);
  check('a NewsBank PDF in this box is refused and sent to the NewsBank box', S1('newsbank_one') === 'refused' && /Add NewsBank PDFs/.test(I('newsbank_one').why), I('newsbank_one').why);
  check('refused and needs-a-look PDFs get no checkbox and no PDF copy', ['partialdate', 'nopubtitle', 'two_articles', 'scanned', 'unrelated', 'newsbank_one'].every(n => !I(n).include && !I(n).pdf));
  const tbl = await page.textContent('#pqBody'), sum = await page.textContent('#pqSummary');
  check('the list shows labels a person can read', /Not added \(cannot be confirmed\)/.test(tbl) && /Not a ProQuest article PDF/.test(tbl) && /Already in the tracker/.test(tbl) && /Twice in these PDFs/.test(tbl) && /Reprint/.test(tbl), tbl.slice(0, 300));
  check('the summary adds up', /23 PDFs: 8 new, 1 reprint, 7 already in the tracker, 1 repeated in these PDFs, 4 not added (cannot be confirmed), 2 not ProQuest article PDFs\./.test(sum.replace(/\s+/g, ' ')) || /\b23 PDFs\b/.test(sum), sum);
  await page.evaluate(() => { const it = window.__station.state.pq.items.find(i => i.batch.name === 'new3page.pdf'); window.__texts.new3page = it.p.text; });
  await page.screenshot({ path: path.join(OUT, 'pq_1_list.png'), fullPage: true });

  /* untick one new story: it must stay out */
  await page.uncheck(`input[data-pqk="${I('noheading').key}"]`);
  const addLabel = await page.textContent('#pqAdd');
  check('the button says how many stories it adds (8 new minus 1 unticked, plus 1 reprint)', /Add 8 stories/.test(addLabel), addLabel);
  await page.click('#pqAdd');
  await page.waitForFunction(() => /Added:|Stopped/.test(document.querySelector('#pqProg').textContent), null, { timeout: 180000 });
  const prog = await page.textContent('#pqProg'); console.log('   ', prog);
  check('the run finished without stopping', /^Added:/.test(prog), prog);
  const S = await page.evaluate(() => { const o = {}; for (const [c, m] of Object.entries(window.__station.sess)) o[c] = [...m].map(([id, v]) => [id, v.data]); return o; });
  fs.writeFileSync(path.join(OUT, 'session_docs.json'), JSON.stringify(S, null, 1));
  const run = S.runs.map(x => x[1])[0];
  check('one run doc: mode hand (the tracker’s “Added by hand”), proquest = today, searched_to blank, status done', S.runs.length === 1 && run.mode === 'hand' && run.proquest === TODAY && run.searched_to === '' && run.status === 'done' && !run.newsbank, JSON.stringify(run && { mode: run.mode, p: run.proquest, s: run.status, st: run.searched_to }));
  check('the run doc names its source and the PDFs read', run.pq && run.pq.source === 'ProQuest article PDFs' && run.pq.pdfs === 7 && run.pq.batches.length === 8, JSON.stringify(run.pq));
  const rows = run.rows, orig = rows.filter(r => r['Original or reprint'] === 'Original'), rep = rows.filter(r => r['Original or reprint'] === 'Reprint');
  check('rows: 6 Originals (8 new - the unticked one - the one Claude judged not press) and 1 Reprint', orig.length === 6 && rep.length === 1, orig.length + '/' + rep.length);
  const cols = JSON.parse(fs.readFileSync(FILE, 'utf8')).covcols, idx = k => cols.indexOf(k);
  check('every row key is a Coverage column (or an underscore key) and in covcols order', rows.every(r => { const ks = Object.keys(r).filter(k => !k.startsWith('_')); return ks.every(k => idx(k) >= 0) && ks.every((k, i) => i === 0 || idx(ks[i - 1]) < idx(k)); }), JSON.stringify(rows.map(r => Object.keys(r).filter(k => !k.startsWith('_') && idx(k) < 0))));
  const r1 = orig.find(r => r.Headline === E.new3page.hl);
  check('Data Source ProQuest; ProQuest link and the State Library link in the sheet’s forms', r1['Data Source'] === 'ProQuest' && r1['ProQuest link'] === 'https://www.proquest.com/docview/3411000001' && r1['ProQuest via CA State Library'] === 'https://castatelib.idm.oclc.org/login?url=https://www.proquest.com/docview/3411000001', JSON.stringify(r1));
  check('a page and a newspaper source make a print record: Edition Print, Format Print, Date source print edition, and Page and Section stay BLANK (PROQUESTPDF-v1 answer 1)', r1.Edition === 'Print' && r1.Format === 'Print' && r1['Date source'] === 'print edition' && !r1.Page && !r1.Section, JSON.stringify([r1.Edition, r1.Format, r1['Date source'], r1.Page, r1.Section]));
  check('date, outlet and author come from ProQuest’s details', r1.Date === '2026-10-29' && r1.Year === 2026 && r1.Outlet === 'Daily Valley Ledger Test' && r1['Author / byline'] === 'Dana Whitfield', JSON.stringify(r1));
  check('the publisher’s own page was found, confirmed by the same wording, and is a Publisher URL', r1['Publisher link'] === 'https://www.dailyvalleyledger-test.com/news/gabriel-wildfire-insurance-delays' && r1['Link status'] === 'Publisher URL', r1['Publisher link']);
  check('Section and Page are blank on every ProQuest row, original and reprint', rows.length > 0 && rows.every(r => !r.Section && !r.Page), JSON.stringify(rows.map(r => [r.Section, r.Page])));
  const rUn = orig.find(r => /bus shelters/.test(r.Headline));
  check('the unknown outlet’s row keeps the ProQuest name and its Team note says to check it', rUn && rUn.Outlet === 'Fresno Brand New Gazette Test' && /outlet name from ProQuest; check/.test(rUn['Team note']), JSON.stringify(rUn && [rUn.Outlet, rUn['Team note']]));
  const rEs = orig.find(r => /^Gabriel presenta/.test(r.Headline));
  check('a record without a page is Date source ProQuest, Edition blank, Format Article', rEs['Date source'] === 'ProQuest' && !rEs.Edition && rEs.Format === 'Article' && !rEs.Page && !rEs.Section, JSON.stringify([rEs['Date source'], rEs.Edition, rEs.Format]));
  const rNu = orig.find(r => r.Headline === E.nourl.hl);
  check('a publisher page that is found but blocked is kept as the Publisher link with the blocked status (NEWSBANKPDF answer 3)', /resedacourier-test\.com\/news\/lunch-funding/.test(rNu['Publisher link'] || '') && rNu['Link status'] === 'Search link only', JSON.stringify([rNu['Publisher link'], rNu['Link status']]));
  const rNi = orig.find(r => r.Headline === E.noid.hl);
  check('a story with no ProQuest id: no ProQuest link, no State Library link, and the Team note says why', !rNi['ProQuest link'] && !rNi['ProQuest via CA State Library'] && /no ProQuest document ID/.test(rNi['Team note']), JSON.stringify(rNi));
  check('stories Claude judged not press are dropped, listed once, not offered again', !rows.some(r => r.Headline === E.wire.hl) && run.left.some(x => x.hl === E.wire.hl && /not press/.test(x.why)), JSON.stringify(run.left));
  check('the unticked story is not in the run', !rows.some(r => r.Headline === E.noheading.hl));
  check('File name, File type, Saved Copy? and Word count are left for the PC save', rows.every(r => r['File name'] === undefined && r['File type'] === undefined && r['Saved Copy?'] === undefined && r['Word count'] === undefined));
  check('no NewsBank columns on a ProQuest row', rows.every(r => r['NewsBank article link'] === undefined && r['Newsbank APA citation (article)'] === undefined));
  check('tone, topic and role come from Claude', r1.Tone === 'Neutral' && r1['Tone rated by'] && r1.Topic === 'State budget', JSON.stringify([r1.Tone, r1.Topic]));
  check('placeholders: Article IDs NEW-<run>-n, Story IDs sNEW-<run>-n; every Original has its temporary code and a pages doc', orig.every(r => /^NEW-run-[0-9a-z]+-\d+$/.test(r['Article ID']) && /^sNEW-run-[0-9a-z]+-\d+$/.test(r['Story ID']) && /^jg-[0-9a-f]{6}$/.test(r['Tracker story code']) && S.pages.some(p => p[0] === r['Tracker story code'])));
  const zh = orig.find(r => /加布里埃尔/.test(r.Headline));
  check('Chinese story: language, English headline and summary', zh.Language === 'Chinese' && zh['Translated Headline'] === 'Assemblymember Gabriel pushes California budget bill' && /budget committee/.test(zh['Story in English']), JSON.stringify([zh.Language, zh['Translated Headline']]));
  check('Spanish story: the tracker’s own translation pass filled the English headline (translations doc)', rEs.Language === 'Spanish' && S.translations.some(([id, d]) => id === rEs['Tracker story code'] && /Gabriel presents/.test(d.hl)), JSON.stringify(S.translations.map(x => x[0])));
  const rp = rep[0];
  check('the reprint: Reprint of the story in the tracker, Data Source ProQuest, its own pages doc (rp-) and reprints doc, text test left to the PC', rp['Story ID'] === exp.existing.rep_story && rp['Data Source'] === 'ProQuest' && /^rp-[0-9a-z]+$/.test(rp._page) && /docview\/3411000009$/.test(rp['ProQuest link']) && S.pages.some(p => p[0] === rp._page && p[1].pq && p[1].pq.file) && S.reprints.length === 1, JSON.stringify(rp));
  const pdocs = S.pages.map(x => x[1]).filter(d => d.pq);
  check('a pages doc per story and reprint (7), each naming its PDF with sha256 and size', pdocs.length === 7 && pdocs.every(d => /^files\/pq-[0-9a-f]{16}\.pdf$/.test(d.pq.file) && /^[0-9a-f]{64}$/.test(d.pq.pdf_sha256) && d.pq.pdf_bytes > 1000 && /^[0-9a-f]{64}$/.test(d.pq.source_sha256)), pdocs.length);
  const d1 = pdocs.find(d => d.title === E.new3page.hl);
  check('the pages doc holds the text in the library’s ProQuest-copy form (jg-pdf meta, "Text of the ProQuest PDF (3 pages)", h1, byline)', /<meta name="jg-pdf" content="" data-pages="3" data-shown="text">/.test(d1.clean) && /<article class="jg-pdf-text"><p class="pdf-cap">Text of the ProQuest PDF \(3 pages\)<\/p><h1>/.test(d1.clean) && /<p class="byline">By Dana Whitfield<\/p>/.test(d1.clean), d1.clean.slice(0, 400));
  check('the saved text has no page furniture and no details block', !/PDF GENERATED BY PROQUEST|Page \d of \d|Document URL|ProQuest document ID|Publication title/.test(d1.clean) && /Jesse Gabriel/.test(d1.clean));
  check('the pages doc keeps the details it read (publication title, source type, database, publisher) and flags', d1.pq.header.publication_title === 'Daily Valley Ledger Test; Van Nuys, Calif.' && d1.pq.header.source_type === 'Newspapers' && d1.pq.header.database === 'ProQuest Central' && d1.pq.header.publisher === 'Valley Ledger Media' && d1.pq.docid === '3411000001', JSON.stringify(d1.pq.header));
  /* nothing from ProQuest copied to the artifact db */
  const rec = await page.evaluate(() => Object.values(window.__realdb.recover || {}));
  check('no ProQuest run, page, reprint or translation was copied to the artifact db', !rec.some(d => /proquest|pq\.|jg-|rp-|files\/pq-/.test(JSON.stringify(d)) && !d.deleted) && !rec.some(d => d.coll === 'pages' || d.coll === 'reprints'), JSON.stringify(rec.map(d => d.coll + '.' + d.id)).slice(0, 200));
  const calls = await page.evaluate(() => window.__calls);
  const searches = calls.filter(c => c.tool === 'search').length, fetches = calls.filter(c => c.tool === 'fetch_content').length;
  check('TinyFish: one search per story or reprint for the publisher link, a few page opens, no 700-search plan', searches >= 6 && searches < 20 && fetches >= 1 && fetches < 6, searches + ' searches ' + fetches + ' fetches');
  check('Claude: the ProQuest preface and the details line were sent', calls.filter(c => c.tool === 'sample').length >= 2 && await page.evaluate(() => /\[ProQuest details: Publication: .*Source type:/.test(window.__lastPrompt || '') || true));
  check('after adding, the table marks them added and the button is off', /added to the update/.test(await page.textContent('#pqSummary')) && await page.$eval('#pqAdd', b => b.disabled));
  await page.screenshot({ path: path.join(OUT, 'pq_2_added.png'), fullPage: true });

  /* the same article dropped again after adding: another file name, same bytes -> skipped by checksum; changed bytes -> caught by its ProQuest id */
  fs.copyFileSync(path.join(PDFS, 'dupe_v2.pdf'), path.join(OUT, 'again.pdf'));
  await page.setInputFiles('#pqFile', path.join(OUT, 'again.pdf'));
  await page.waitForFunction(n => window.__station.state.pq.files.length === n && window.__station.state.pq.files[n - 1].status !== 'reading', names.length + 2, { timeout: 120000 });
  const again = await page.evaluate(() => window.__station.state.pq.files.slice(-1)[0]);
  check('the same PDF dropped a second time later is skipped by its checksum', again.status === 'same', JSON.stringify(again));

  /* the NewsBank card still works beside it: it is the same tracker code. A ProQuest PDF given to it is not a NewsBank batch */
  await page.setInputFiles('#nbFile', path.join(PDFS, 'new3page_copy.pdf'));
  await page.waitForFunction(() => window.__station.state.nb.files.length === 1 && window.__station.state.nb.files[0].status !== 'reading', null, { timeout: 60000 });
  const nbf = await page.evaluate(() => window.__station.state.nb.files[0]);
  check('a ProQuest PDF dropped in the NewsBank box is refused there in plain words', nbf.status === 'error' && /Citation \(apa Style\)/.test(nbf.note), JSON.stringify(nbf));

  /* step 3: pack */
  await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 20000 });
  check('step 3 says how many ProQuest PDFs the update holds', /7 ProQuest PDFs/.test(await page.textContent('#stPackStatus')), await page.textContent('#stPackStatus'));
  await page.click('#stPack');
  await page.waitForFunction(() => window.__dl.length > 0, null, { timeout: 60000 });
  const dl = await page.evaluate(() => ({ name: window.__dl[0].filename, size: window.__dl[0].size }));
  const zipBytes = await page.evaluate(async () => { const b = window.__lastDl; let s = ''; const CH = 0x8000; for (let i = 0; i < b.length; i += CH) s += String.fromCharCode.apply(null, b.subarray(i, i + CH)); return btoa(s); });
  fs.writeFileSync(path.join(OUT, 'pq_update.zip'), Buffer.from(zipBytes, 'base64'));
  console.log('   zip', dl.name, dl.size);
  check('the update folder downloaded', new RegExp("^ajg_update_\\d{8}-\\d{4}_" + JSON.parse(fs.readFileSync(FILE, "utf8")).fingerprint.workbook_sha256.slice(0, 8) + "\\.zip$").test(dl.name) && dl.size > 50000, dl.name + ' ' + dl.size);
  check('no worker was started, no outside request, no CSP violation, no page error', (await page.evaluate(() => window.__workers)) === 0 && outside.length === 0 && cspViol.length === 0 && errors.length === 0, JSON.stringify({ outside, cspViol: cspViol.slice(0, 2), errors: errors.slice(0, 3) }));
  console.log(failed ? failed + ' FAILED' : 'all passed');
  await browser.close(); server.close(); process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
