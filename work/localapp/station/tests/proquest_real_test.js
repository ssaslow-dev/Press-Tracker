/* REAL ProQuest PDF through the station's "Add ProQuest PDFs" card (PROQUESTPDF-v1, real PDF 2026-11-03: Politico, 2023-06-28, ProQuest document 2830163640, already in the tracker as 08882 / s03441).
   AJG_REAL_PQ=/path/real1.pdf node tests/proquest_real_test.js --page dist/index.html --file FOR_UPDATE.json --out OUTDIR
   Skips (exit 0) when AJG_REAL_PQ is not set: the PDF is licensed text and is never in the repository.
   (not used) Same set-up as newsbank_test.js: the page is served on 127.0.0.1 inside the skeleton the Artifact tool adds,
   under a strict Content-Security-Policy (inline scripts only; no eval, no worker, no blob: script, no connections); window.claude is a stub (db in
   memory, TinyFish search / fetch canned, sample canned); the downloaded zip is written to OUTDIR (checked afterwards by tests/pq/verify_pq_zip.py). */
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page'), FILE = arg('file'), OUT = arg('out'), REAL = process.env.AJG_REAL_PQ;
if (!REAL || !fs.existsSync(REAL)) { console.log('SKIPPED: set AJG_REAL_PQ to the real ProQuest PDF (licensed text: keep it out of the repository)'); process.exit(0); }
fs.mkdirSync(OUT, { recursive: true });
let failed = 0; const check = (name, ok, extra) => { if (!ok) failed++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (!ok && extra !== undefined ? '  -> ' + extra : '')); };
const laDay = (d = new Date()) => d.toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' });
const TODAY = laDay();

const shellHead = (() => { const vd = path.join(__dirname, '..', '..', 'vendor'); return fs.readFileSync(path.join(vd, fs.readdirSync(vd).filter(d => d.startsWith('live_')).sort().pop(), 'pipeline', 'shell.html'), 'utf8').split('<body>')[0] + '<body>'; })();
const wrapped = shellHead + fs.readFileSync(PAGE, 'utf8') + '</body></html>';
const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; worker-src 'none'; connect-src 'none'";
const server = http.createServer((req, res) => {
  if (req.url.split('?')[0] === '/index.html' || req.url === '/') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Security-Policy': CSP }); res.end(wrapped); }
  else { res.writeHead(404); res.end('no'); }
});


const INIT = () => {
  const st = window.setTimeout.bind(window); window.setTimeout = (f, d, ...a) => st(f, d >= 300 ? Math.max(1, d / 100) : d, ...a);
  window.__calls = []; window.__dl = []; window.__workers = 0;
  window.Worker = function () { window.__workers++; throw new Error('workers are not allowed here'); };
  const fakeDb = { collection: n => ({ doc: id => ({ set: async () => {}, delete: async () => {}, get: async () => ({ exists: false, data: () => null }) }), get: async () => ({ docs: [] }), onSnapshot: cb => { cb({ docs: [] }); return () => {}; } }) };
  const mcp = { callTool: async (s, tool, input) => { window.__calls.push({ tool, q: input.query || (input.urls || []).join(' ') }); return { payload: { results: [], errors: [] } }; } };
  const sample = async () => ({ text: '', truncated: false }); sample.json = async () => [];
  window.claude = { use: async name => name === 'db' ? fakeDb : name === 'mcp' ? mcp : name === 'sample' ? sample : name === 'downloads' ? { save: async () => {} } : null };
};
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1300, height: 1100 } });
  await ctx.addInitScript(INIT);
  const page = await ctx.newPage(); const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(base + '/index.html'); await page.waitForSelector('#pqDrop');
  await page.setInputFiles('#stFile', FILE); await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 90000 });
  await page.waitForFunction(() => window.__pq && window.__pq.version === 1, null, { timeout: 30000 });
  await page.setInputFiles('#pqFile', REAL);
  await page.waitForFunction(() => window.__station.state.pq.files.length === 1 && window.__station.state.pq.files[0].status !== 'reading' && !window.__station.state.pq.reading, null, { timeout: 120000 });
  const f = await page.evaluate(() => window.__station.state.pq.files[0]);
  const it = await page.evaluate(() => window.__station.state.pq.items.map(it => ({ st: it.screen.status, why: it.screen.why, of: it.screen.of, hl: it.p.headline, date: it.p.date, outlet: it.p.outlet_clean, resolved: it.outlet, author: it.p.author, docid: it.p.docid, link: it.p.link, source: it.p.source_type, flags: it.p.flags, problems: it.p.problems, words: it.p.body_words, text: it.p.text, pages: it.p.pages })));
  check('the PDF opens in the browser (pdf.js, despite the “incorrect startxref pointer”): 5 pages', f.status !== 'error' && f.pages === 5, JSON.stringify(f));
  check('one story read', it.length === 1, it.length);
  const x = it[0] || {};
  check('already in the tracker, found by its ProQuest document ID', x.st === 'known' && /ProQuest document id/i.test(x.why || ''), JSON.stringify([x.st, x.why, x.of]));
  check('headline', x.hl === 'A new era of power in California’s Capitol', x.hl);
  check('date 2023-06-28', x.date === '2023-06-28', x.date);
  check('authors in the sheet’s form', x.author === 'Lara Korte, Jeremy B White and Sejal Govindarao', x.author);
  check('outlet resolves to Politico (curated pair)', x.outlet === 'Politico' || x.resolved === 'Politico' || (x.of && /Politico/.test(JSON.stringify(x.of))), JSON.stringify([x.outlet, x.resolved]));
  check('ProQuest document ID and link', x.docid === '2830163640' && x.link === 'https://www.proquest.com/docview/2830163640', x.docid + ' ' + x.link);
  check('not print: source type “Blog, Podcast, or Website”', x.source === 'Blog, Podcast, or Website', x.source);
  check('no “needs a look”: no problems, no flags', (x.problems || []).length === 0 && (x.flags || []).length === 0, JSON.stringify([x.problems, x.flags]));
  check('the text is the article only (no DETAILS, LINKS, footer, Document URL, Subject list)', !/DETAILS|Subject:|Lexile|PDF GENERATED|Terms and Conditions|Check for Full Text|Database copyright|ProQuest document link|Document URL|Publication title/.test(x.text || '') && /^THE BUZZ: Welcome to the new era/.test(x.text || '') && x.words > 1500, (x.text || '').slice(0, 80) + ' … ' + (x.text || '').slice(-120));
  check('no page errors', errors.length === 0, errors.slice(0, 3).join(' | '));
  console.log(failed ? failed + ' FAILED' : 'all passed');
  await browser.close(); server.close(); process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
