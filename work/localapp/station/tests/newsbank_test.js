/* Playwright test of the "Add NewsBank PDFs" card (NEWSBANKPDF-v1). Run:
     node tests/newsbank_test.js --page dist/index.html --file FOR_UPDATE.json --pdfs PDFDIR --out OUTDIR
   PDFDIR comes from tests/nb/make_nb_pdfs.py. Everything is local: the page is served on 127.0.0.1 inside the skeleton the Artifact tool adds, with a
   deliberately strict Content-Security-Policy (inline scripts only; no eval, no worker, no blob: script, no connections), window.claude is a stub
   (db in memory, TinyFish search / fetch canned, sample canned) and the downloaded zip is written to OUTDIR (checked afterwards by tests/nb/verify_nb_zip.py). */
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page'), FILE = arg('file'), PDFS = arg('pdfs'), OUT = arg('out');
fs.mkdirSync(OUT, { recursive: true });
let failed = 0; const check = (name, ok, extra) => { if (!ok) failed++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (!ok && extra !== undefined ? '  -> ' + extra : '')); };
const exp = JSON.parse(fs.readFileSync(path.join(PDFS, 'expected.json'), 'utf8'));
const fu = JSON.parse(fs.readFileSync(FILE, 'utf8'));
const laDay = (d = new Date()) => d.toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' });
const TODAY = laDay();
const HL = k => (exp.stories[k].same_as ? exp.stories[exp.stories[k].same_as] : exp.stories[k]).hl;

const shellHead = (() => { const vd = path.join(__dirname, '..', '..', 'vendor'); return fs.readFileSync(path.join(vd, fs.readdirSync(vd).filter(d => d.startsWith('live_')).sort().pop(), 'pipeline', 'shell.html'), 'utf8').split('<body>')[0] + '<body>'; })();
const wrapped = shellHead + fs.readFileSync(PAGE, 'utf8') + '</body></html>';
const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; worker-src 'none'; connect-src 'none'";
const server = http.createServer((req, res) => {
  if (req.url.split('?')[0] === '/index.html' || req.url === '/') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Security-Policy': CSP }); res.end(wrapped); }
  else { res.writeHead(404); res.end('no'); }
});

const INIT = ({ today, hl }) => {
  const st = window.setTimeout.bind(window);
  window.setTimeout = (f, d, ...a) => st(f, d >= 300 ? Math.max(1, d / 100) : d, ...a);
  const realNow = Date.now.bind(Date), t0 = realNow(); Date.now = () => t0 + (realNow() - t0) * 100;
  window.__calls = []; window.__dl = []; window.__workers = 0; window.__texts = {};
  const RW = window.Worker; window.Worker = function () { window.__workers++; throw new Error('workers are not allowed here'); };
  const load = () => { try { return JSON.parse(localStorage.getItem('__fakedb')) || {}; } catch (e) { return {}; } }, save = o => localStorage.setItem('__fakedb', JSON.stringify(o));
  Object.defineProperty(window, '__realdb', { get: () => load() });
  const fakeDb = { collection: n => ({ doc: id => ({ set: async d => { const o = load(); (o[n] = o[n] || {})[id] = JSON.parse(JSON.stringify(d)); save(o); }, delete: async () => {}, get: async () => { const d = (load()[n] || {})[id]; return { exists: !!d, data: () => d }; } }),
    get: async () => ({ docs: Object.entries(load()[n] || {}).map(([id, d]) => ({ id, data: () => d })) }), onSnapshot: cb => { cb({ docs: Object.entries(load()[n] || {}).map(([id, d]) => ({ id, data: () => d })) }); return () => {}; } }) };
  const PUB = 'https://www.valleycourier-test.com/news/gabriel-clean-air-permits', ELSE = 'https://elsewhere-test.example/a';
  const mcp = { callTool: async (server, tool, input) => {
    window.__calls.push({ tool, q: input.query || (input.urls || []).join(' ') });
    if (tool === 'search') { const q = String(input.query || '').replace(/^"|"$/g, '');
      if (q === hl.new1) return { payload: { results: [{ url: PUB, title: hl.new1 + ' - Valley Courier Test', date: '2026-10-29', publisher: 'Valley Courier Test' }, { url: 'https://infoweb.newsbank.com/x', title: hl.new1, date: '2026-10-29' }] } };
      if (q === hl.f12) return { payload: { results: [{ url: ELSE, title: hl.f12, date: '2026-10-22', publisher: 'Elsewhere' }] } };
      return { payload: { results: [] } }; }
    if (tool === 'fetch_content') return { payload: { results: (input.urls || []).map(u => u === PUB ? { url: u, final_url: u, title: hl.new1, text: '<html><body><article><h1>' + hl.new1 + '</h1><p>' + (window.__texts.new1 || '') + '</p></article></body></html>', published_date: '' }
      : { url: u, final_url: u, title: 'Other', text: '<html><body><article><p>Entirely different words about a different subject that share nothing with the story text at all, honestly.</p></article></body></html>', published_date: '' }) } };
    return { payload: {} };
  } };
  const sample = async () => ({ text: '', truncated: false });
  sample.json = async prompt => {
    window.__calls.push({ tool: 'sample', q: String(prompt).slice(0, 50) });
    if (/^These items come from NewsBank/.test(prompt)) {
      return [...prompt.matchAll(/=== ITEM (\d+)\nURL: (\S+)\nPage title: (.*)\n/g)].map(m => {
        const t = m[3], r = { n: +m[1], keep: true, why: 'NewsBank story naming him.', date: '', outlet: '', pub: '', hl: t, topic: 'State budget', media: 'Newspaper', role: 'Mentioned in story', tone: 'Neutral', twhy: 'Straight news.', author: '', lang: '', hl_en: '', text_en: '' };
        if (/^Filler story 15/.test(t)) return Object.assign(r, { press_release: 'yes', pr_why: 'the city’s own release posted in full' });   // PRJUDGE-v1
        if (/^Filler story 20/.test(t)) return Object.assign(r, { keep: false, why: 'A community calendar item, not press.' });
        if (/加布里埃尔/.test(t)) return Object.assign(r, { lang: 'Chinese', hl_en: 'Assemblymember Gabriel pushes California budget bill', text_en: 'He said the budget committee will review housing and wildfire spending.' });
        if (/^Gabriel presenta/.test(t)) return Object.assign(r, { lang: 'Spanish', hl_en: '' });
        return r; });
    }
    if (/^Translate each news headline/.test(prompt)) return [...prompt.matchAll(/id=(\S+) \((\w+),/g)].map(m => ({ id: m[1], hl: 'Gabriel presents a bill to speed up housing construction' }));
    return [];
  };
  window.claude = { use: async name => name === 'db' ? fakeDb : name === 'mcp' ? mcp : name === 'sample' ? sample : name === 'downloads' ? { save: async ({ filename, data }) => { const buf = new Uint8Array(await data.arrayBuffer()); window.__dl.push({ filename, size: buf.length }); window.__lastDl = buf; } } : null };
};

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1300, height: 1100 }, acceptDownloads: true });
  await ctx.addInitScript(INIT, { today: TODAY, hl: { new1: HL('new1'), f12: HL('f12') } });
  await ctx.addInitScript(() => { try { localStorage.setItem('ajg_station_auto', '0'); } catch (e) {} });   // AUTOSTATION-v1: these tests click each step themselves (the automatic mode has its own test)
  const outside = []; await ctx.route(u => !/^(http:\/\/127\.0\.0\.1[:/]|data:|blob:|about:)/.test(u.href), r => { outside.push(r.request().url()); r.abort(); });
  const page = await ctx.newPage();
  const errors = []; page.on('pageerror', e => errors.push('pageerror: ' + e.message)); page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  const cspViol = []; page.on('console', m => { if (/Content Security Policy/i.test(m.text())) cspViol.push(m.text()); });

  await page.goto(base + '/index.html'); await page.waitForSelector('#nbDrop');
  check('the NewsBank card is on the page, locked until a file is loaded', await page.locator('#st-nb.st-lock').count() === 1);
  await page.setInputFiles('#nbFile', path.join(PDFS, 'batch_A.pdf'));
  await page.waitForSelector('#nbMsg:not([hidden])');
  check('PDFs dropped before the for-Update file are refused with a plain message', /Load the for Update file first/.test(await page.textContent('#nbMsg')), await page.textContent('#nbMsg'));

  await page.setInputFiles('#stFile', FILE); await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 90000 });
  await page.waitForFunction(() => window.__nb && window.__nb.version === 1, null, { timeout: 30000 });
  check('after loading the file the card is unlocked and the NewsBank code is in the tracker scope', await page.locator('#st-nb.st-lock').count() === 0 && await page.evaluate(() => window.__nb.docrefs() > 3000));

  /* a, identical copy of A, and a 19-story batch, in one drop */
  await page.setInputFiles('#nbFile', ['batch_A.pdf', 'batch_A_copy.pdf', 'batch_19.pdf'].map(f => path.join(PDFS, f)));
  await page.waitForFunction(() => window.__station.state.nb.files.length === 3 && window.__station.state.nb.files.every(f => f.status !== 'reading') && !window.__station.state.nb.reading, null, { timeout: 120000 });
  const files = await page.evaluate(() => window.__station.state.nb.files.map(f => ({ name: f.name, status: f.status, note: f.note, warn: f.warn, stories: f.stories, pages: f.pages })));
  console.log('   files', JSON.stringify(files));
  check('batch_A: 20 stories found in ' + exp.batch_A.pages + ' pages', files[0].status === 'ok' && files[0].stories === 20 && files[0].pages === exp.batch_A.pages, JSON.stringify(files[0]));
  check('batch_A: mid-page starts are noticed', /mid-page/.test(files[0].note), files[0].note);
  check('the byte-identical copy is skipped and says so', files[1].status === 'same' && /identical to “batch_A.pdf”/.test(files[1].note), JSON.stringify(files[1]));
  check('batch_19: 19 stories found, no warning about the count (any number per PDF is fine)', files[2].stories === 19 && !(files[2].warn || []).some(w => /stories \(a batch/.test(w)), JSON.stringify(files[2]));
  check('a full batch gets no count warning', !(files[0].warn || []).length, JSON.stringify(files[0].warn));

  const items = await page.evaluate(() => window.__station.state.nb.items.map(it => ({ key: it.key, st: it.screen.status, of: it.screen.of, why: it.screen.why, hl: it.p.headline, date: it.p.date, outlet: it.p.outlet_clean, docref: it.p.docref, file: it.batch.name, idx: it.batch.index, pdf: it.pdf && it.pdf.bytes, pdfid: it.fileId, kind: it.p.kind, shared: !!(it.batch.sharedFirst || it.batch.sharedLast), pages: it.batch.firstPage + '-' + it.batch.lastPage })));
  const A = items.filter(i => i.file === 'batch_A.pdf'), by = k => A.find(i => i.idx === exp.batch_A.items.findIndex(x => x.key === k) + 1);
  const cnt = o => o.reduce((c, i) => (c[i.st] = (c[i.st] || 0) + 1, c), {});
  check('batch_A statuses: 15 new, 1 reprint, 2 already in the tracker, 1 repeated in the batch, 1 print page', JSON.stringify(cnt(A)) === JSON.stringify({ new: 15, known: 2, reprint: 1, dup_batch: 1, print_page: 1 }) || (() => { const c = cnt(A); return c.new === 15 && c.known === 2 && c.reprint === 1 && c.dup_batch === 1 && c.print_page === 1; })(), JSON.stringify(cnt(A)));
  check('already in the tracker by NewsBank id (s00001’s docref)', by('dup_docref5').st === 'known' && /same NewsBank link/.test(by('dup_docref5').why), JSON.stringify(by('dup_docref5')));
  check('already in the tracker by headline, outlet and date (another NewsBank id)', by('dup_hl6').st === 'known' && /same outlet and headline/.test(by('dup_hl6').why), JSON.stringify(by('dup_hl6')));
  check('another outlet with the same headline: a reprint of s00002', by('rep7').st === 'reprint' && by('rep7').of === 's00002', JSON.stringify(by('rep7')));
  check('the same story twice in one batch: the second is dropped as a repeat', A.find(i => i.idx === 8).st === 'dup_batch', JSON.stringify(A.find(i => i.idx === 8)));
  check('a print page is not a story', by('printpage10').st === 'print_page' && by('printpage10').kind === 'print_page');
  check('the Chinese headline is read', /加布里埃尔议员推动加州预算法案/.test(by('zh3').hl), by('zh3').hl);
  check('a story with a Page line is a print record', by('print9') && by('print9').st === 'new');
  const n19 = items.filter(i => i.file === 'batch_19.pdf');
  check('batch_19: 19 new stories, each with its own PDF', n19.length === 19 && n19.every(i => i.st === 'new' && i.pdf > 1000), JSON.stringify(cnt(n19)));
  check('every new story has a PDF of its own', A.filter(i => i.st === 'new').every(i => i.pdf > 1000));
  check('the story that starts mid-page is flagged as sharing a page', by('long2').shared === true && by('rep7').shared === true, JSON.stringify([by('long2').shared, by('rep7').shared]));
  const L2 = exp.batch_A.items.find(x => x.key === 'long2');
  check('batch_A: the long story starting mid-page got its page range ' + L2.start_page + '-' + L2.end_page, by('long2').pages === L2.start_page + '-' + L2.end_page && L2.end_page > L2.start_page, by('long2').pages);

  /* the table */
  const tbl = await page.textContent('#nbBody');
  check('the list shows statuses a person can read', /Already in the tracker/.test(tbl) && /Reprint/.test(tbl) && /Twice in these PDFs/.test(tbl) && /Print page/.test(tbl) && /New/.test(tbl));
  check('the summary line adds up', /3 stories|39 stories/.test(await page.textContent('#nbSummary')) || /\b39 stories\b/.test(await page.textContent('#nbSummary')), await page.textContent('#nbSummary'));
  await page.evaluate(() => { const it = window.__station.state.nb.items.find(i => /^Gabriel unveils plan/.test(i.p.headline)); window.__texts.new1 = it.p.text; });
  await page.screenshot({ path: path.join(OUT, 'nb_1_list.png'), fullPage: true });

  /* untick one new story: it must stay out */
  const f13 = A.find(i => /Filler story 13/.test(i.hl));
  await page.uncheck(`input[data-nbk="${f13.key}"]`);
  const nBefore = await page.evaluate(() => window.__calls.length);

  /* add */
  const addLabel = await page.textContent('#nbAdd');
  check('the button says how many stories it adds (36: 15 + 19 new, minus 1 unticked, plus 1 reprint, plus 1 print page and 1 known story whose PDF is kept as an extra copy)', /Add 36 stories/.test(addLabel), addLabel);
  await page.click('#nbAdd');
  await page.waitForFunction(() => /Added:|Stopped/.test(document.querySelector('#nbProg').textContent), null, { timeout: 180000 });
  const prog = await page.textContent('#nbProg'); console.log('   ', prog);
  check('the run finished without stopping', /^Added:/.test(prog), prog);
  const S = await page.evaluate(() => { const o = {}; for (const [c, m] of Object.entries(window.__station.sess)) o[c] = [...m].map(([id, v]) => [id, v.data]); return o; });
  fs.writeFileSync(path.join(OUT, 'session_docs.json'), JSON.stringify(S, null, 1));
  const run = S.runs.map(x => x[1]).find(r => r.mode === 'newsbank');
  check('one run doc of mode newsbank, status done, newsbank = today, searched_to stays blank', !!run && run.status === 'done' && run.newsbank === TODAY && run.searched_to === '' && S.runs.length === 1, JSON.stringify(run && { mode: run.mode, s: run.status, n: run.newsbank, st: run.searched_to }));
  const rows = run.rows, orig = rows.filter(r => r['Original or reprint'] === 'Original'), rep = rows.filter(r => r['Original or reprint'] === 'Reprint');
  check('rows: 32 Originals (14 + 19 - the unticked one - the skipped one) and 1 Reprint', orig.length === 32 && rep.length === 1, orig.length + '/' + rep.length);
  const cols = fu.covcols, idx = k => cols.indexOf(k);
  check('every row key is a Coverage column (or an underscore key) and in covcols order', rows.every(r => { const ks = Object.keys(r).filter(k => !k.startsWith('_')); return ks.every(k => idx(k) >= 0) && ks.every((k, i) => i === 0 || idx(ks[i - 1]) < idx(k)); }), JSON.stringify(rows.map(r => Object.keys(r).filter(k => !k.startsWith('_') && idx(k) < 0))[0]));
  const r1 = orig.find(r => r.Headline === HL('new1'));
  check('Data Source is Newsbank, article link in the sheet’s form, citation kept', r1['Data Source'] === 'Newsbank' && /^https:\/\/infoweb\.newsbank\.com\/apps\/news\/document-view\?p=WORLDNEWS&docref=news\/[0-9A-F]{16}$/.test(r1['NewsBank article link']) && /^Whitfield, D\. \(2026, October 29\)/.test(r1['Newsbank APA citation (article)']) && /docref=news\//.test(r1['Newsbank APA citation (article)']), JSON.stringify(r1));
  check('date, outlet, author, section, words come from NewsBank’s header', r1.Date === '2026-10-29' && r1.Year === 2026 && r1.Outlet === 'Valley Courier Test' && r1['Author / byline'] === 'Dana Whitfield' && r1.Section === 'NEWS' && r1['Word count'] === 190 && r1['Date source'] === 'NewsBank', JSON.stringify(r1));
  check('the publisher’s own page was found for the story that has one, and is a Publisher URL', r1['Publisher link'] === 'https://www.valleycourier-test.com/news/gabriel-clean-air-permits' && r1['Link status'] === 'Publisher URL', r1['Publisher link']);
  const r12 = orig.find(r => /^Filler story 12/.test(r.Headline));
  check('a page with the same headline but other words is NOT taken as the publisher link', r12['Publisher link'] === undefined && /publisher link not found/.test(r12['Team note'] || ''), JSON.stringify([r12['Publisher link'], r12['Team note']]));
  check('a story with no search hit has no publisher link and no Link status', orig.filter(r => !r['Publisher link']).length >= 30 && orig.every(r => !r['Link status'] || r['Publisher link']));
  check('File name, File type and Saved Copy? are left for the PC save', rows.every(r => r['File name'] === undefined && r['File type'] === undefined && r['Saved Copy?'] === undefined));
  check('tone, topic and role come from Claude', r1.Tone === 'Neutral' && r1['Tone rated by'] && r1.Topic === 'State budget', JSON.stringify([r1.Tone, r1.Topic]));
  check('placeholders: Article IDs NEW-<run>-n, Story IDs sNEW-<run>-n', orig.every(r => /^NEW-run-[0-9a-z]+-\d+$/.test(r['Article ID']) && /^sNEW-run-[0-9a-z]+-\d+$/.test(r['Story ID'])), JSON.stringify(orig[0]));
  check('every Original carries its temporary code (how the PC save finds its pages doc)', orig.every(r => /^jg-[0-9a-f]{6}$/.test(r['Tracker story code']) && S.pages.some(p => p[0] === r['Tracker story code'])));
  const zh = orig.find(r => /加布里埃尔/.test(r.Headline));
  check('Chinese story: language, English headline and summary', zh.Language === 'Chinese' && zh['Translated Headline'] === 'Assemblymember Gabriel pushes California budget bill' && /budget committee/.test(zh['Story in English']), JSON.stringify([zh.Language, zh['Translated Headline']]));
  const es = orig.find(r => /^Gabriel presenta/.test(r.Headline));
  const trs = S.translations.map(x => x[1]);
  check('Spanish story: the tracker’s own translation pass filled the English headline (translations doc)', es.Language === 'Spanish' && S.translations.some(([id, d]) => id === es['Tracker story code'] && /Gabriel presents/.test(d.hl)), JSON.stringify([es.Language, trs.length]));
  const pr9 = orig.find(r => /^Council backs Gabriel bill/.test(r.Headline));
  check('a record with a Page is a print edition', pr9.Edition === 'Print' && pr9.Page === 'A5' && pr9['Date source'] === 'print edition' && pr9.Format === 'Print', JSON.stringify([pr9.Edition, pr9.Page, pr9['Date source'], pr9.Format]));
  const rp = rep[0];
  check('the reprint: Reprint of s00002, Data Source Newsbank, its own pages doc and NewsBank link, text test left to the PC', rp['Story ID'] === 's00002' && rp['Data Source'] === 'Newsbank' && /^rp-[0-9a-z]+$/.test(rp._page) && /docref=news\//.test(rp['NewsBank article link']) && S.pages.some(p => p[0] === rp._page && p[1].nb.file) && S.reprints.some(([id, d]) => id === rp._page && d.story === 's00002'), JSON.stringify(rp));
  check('skipped by Claude (not press) is listed, not added', !rows.some(r => /^Filler story 20/.test(r.Headline)) && run.left.some(x => /Filler story 20/.test(x.hl)), JSON.stringify(run.left));
  check('the unticked story is not in the run', !rows.some(r => /^Filler story 13/.test(r.Headline)));
  check('the print page is listed for clipping and is not a row', run.print_pages.length === 1 && /Valley Courier Test: Page 4/.test(run.print_pages[0].hl) && !rows.some(r => /Page 4/.test(r.Headline)), JSON.stringify(run.print_pages));
  const pdocs = S.pages.map(x => x[1]).filter(d => d.nb);
  check('a pages doc per story, reprint and print page, each naming its PDF with sha256 and size', pdocs.length === 34 && pdocs.every(d => /^files\/nb-[0-9a-f]{16}\.pdf$/.test(d.nb.file) && /^[0-9a-f]{64}$/.test(d.nb.pdf_sha256) && d.nb.pdf_bytes > 1000 && d.nb.docref), pdocs.length);
  check('the pages doc holds the story text in the library’s NewsBank-text form, with no neighbouring story in it', pdocs.every(d => /<article class="jg-pdf-text">/.test(d.clean)) && !pdocs.some(d => /long night of testimony/.test(d.clean) && /Valley Courier Test \(CA\)|加布里埃尔议员/.test(d.clean)));
  const long2 = pdocs.find(d => /wildfire recovery money/.test(d.title));
  check('a multi-page story starting mid-page: its page range and a band recorded', long2.nb.batch.pages.join('-') === L2.start_page + '-' + L2.end_page && long2.nb.batch.bands.length >= 1 && long2.nb.batch.shared_first === true, JSON.stringify(long2.nb.batch));
  check('the book-keeping travels: batch name and sha256 and story number', pdocs.every(d => d.nb.batch.name && /^[0-9a-f]{64}$/.test(d.nb.batch.sha256) && d.nb.batch.index >= 1));

  /* NewsBank text never copied to the artifact db */
  await page.waitForFunction(() => !window.__station.mirrorBusy(), null, { timeout: 30000 });
  const rec = await page.evaluate(() => Object.values(window.__realdb.recover || {}));
  check('no NewsBank run, page, reprint or translation was copied to the artifact db', !rec.some(d => /newsbank|nb\.|jg-|rp-|files\/nb-/.test(JSON.stringify(d)) && !d.deleted) && !rec.some(d => d.coll === 'pages' || d.coll === 'reprints'), JSON.stringify(rec.map(d => d.coll + '.' + d.id)).slice(0, 200));
  const calls = await page.evaluate(() => window.__calls);
  const searches = calls.filter(c => c.tool === 'search').length, fetches = calls.filter(c => c.tool === 'fetch_content').length;
  check('TinyFish: one search per story or reprint for the publisher link, a few page opens, no 700-search plan', searches >= 33 && searches < 80 && fetches >= 1 && fetches < 12, searches + ' searches ' + fetches + ' fetches');
  check('Claude: classify in batches of 20, plus the translation pass', calls.filter(c => c.tool === 'sample').length >= 3, JSON.stringify(calls.filter(c => c.tool === 'sample').map(c => c.q)));
  check('after adding, the table marks them added and the button is off', /added to the update/.test(await page.textContent('#nbSummary')) && await page.$eval('#nbAdd', b => b.disabled));
  await page.screenshot({ path: path.join(OUT, 'nb_2_added.png'), fullPage: true });

  /* the same batch dropped again after adding */
  await page.setInputFiles('#nbFile', path.join(PDFS, 'batch_B.pdf'));
  await page.waitForFunction(() => window.__station.state.nb.files.length === 4 && window.__station.state.nb.files[3].status !== 'reading', null, { timeout: 120000 });
  const B = await page.evaluate(() => window.__station.state.nb.items.filter(i => i.batch.name === 'batch_B.pdf').map(i => i.screen.status));
  check('the same stories in another file (page-aligned layout) dropped later: nothing new', B.length === 20 && !B.includes('new') && !B.includes('reprint'), JSON.stringify(B));

  /* step 3: pack */
  await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 20000 });
  check('step 3 says how many NewsBank PDFs the update holds', /34 NewsBank story PDFs/.test(await page.textContent('#stPackStatus')), await page.textContent('#stPackStatus'));
  await page.click('#stPack');
  await page.waitForFunction(() => window.__dl.length > 0, null, { timeout: 60000 });
  const dl = await page.evaluate(() => ({ name: window.__dl[0].filename, size: window.__dl[0].size, b64: btoa(String.fromCharCode.apply(null, window.__lastDl.subarray(0, 0))) }));
  const zipBytes = await page.evaluate(async () => { const b = window.__lastDl; let s = ''; const CH = 0x8000; for (let i = 0; i < b.length; i += CH) s += String.fromCharCode.apply(null, b.subarray(i, i + CH)); return btoa(s); });
  fs.writeFileSync(path.join(OUT, 'nb_update.zip'), Buffer.from(zipBytes, 'base64'));
  console.log('   zip', dl.name, dl.size);
  check('the update folder downloaded', new RegExp("^ajg_update_\\d{8}-\\d{4}_" + fu.fingerprint.workbook_sha256.slice(0, 8) + "\\.zip$").test(dl.name) && dl.size > 100000, dl.name + ' ' + dl.size);
  check('no worker was started, no outside request, no CSP violation, no page error', (await page.evaluate(() => window.__workers)) === 0 && outside.length === 0 && cspViol.length === 0 && errors.length === 0, JSON.stringify({ outside, cspViol: cspViol.slice(0, 2), errors: errors.slice(0, 3) }));
  console.log(failed ? failed + ' FAILED' : 'all passed');
  await browser.close(); server.close(); process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
