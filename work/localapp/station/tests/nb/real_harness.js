/* Shared by the two REAL-batch tests (newsbank_real_test.js, newsbank_real2_test.js): the station page served on 127.0.0.1 inside the Artifact skeleton with a strict
   Content-Security-Policy, window.claude a stub (db in memory, TinyFish canned, Claude's classify canned by a function the test gives), and helpers. The batch PDFs are
   licensed text: they stay in the scratchpad and are read only when the test's environment variable names their folder. */
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ST = path.join(__dirname, '..', '..');
exports.ST = ST;
exports.makeChecker = () => { const c = { failed: 0, n: 0 }; c.check = (name, ok, extra) => { c.n++; if (!ok) c.failed++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (!ok && extra !== undefined ? '  -> ' + extra : '')); }; return c; };
exports.start = async function (pageFile, claudeStub, opts) {
  opts = opts || {};
  const vd = path.join(ST, '..', 'vendor'), shellHead = fs.readFileSync(path.join(vd, fs.readdirSync(vd).filter(d => d.startsWith('live_')).sort().pop(), 'pipeline', 'shell.html'), 'utf8').split('<body>')[0] + '<body>';
  const wrapped = shellHead + fs.readFileSync(pageFile, 'utf8') + '</body></html>';
  const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; worker-src 'none'; connect-src 'none'";
  const server = http.createServer((req, res) => { if (req.url.split('?')[0] === '/index.html' || req.url === '/') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Security-Policy': CSP }); res.end(wrapped); } else { res.writeHead(404); res.end('no'); } });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port, browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1300, height: 1100 }, acceptDownloads: true });
  const INIT = (arg) => {
    const stubSrc = arg.stubSrc, OPT = arg.opts || {};
    const st = window.setTimeout.bind(window); window.setTimeout = (f, d, ...a) => st(f, d >= 300 ? Math.max(1, d / 100) : d, ...a);
    const realNow = Date.now.bind(Date), t0 = realNow(); Date.now = () => t0 + (realNow() - t0) * 100;
    window.__calls = []; window.__dl = []; window.__prompts = [];
    window.Worker = function () { throw new Error('workers are not allowed here'); };
    const store = {};
    const fakeDb = { collection: n => ({ doc: id => ({ set: async d => { (store[n] = store[n] || {})[id] = JSON.parse(JSON.stringify(d)); }, delete: async () => {}, get: async () => { const d = (store[n] || {})[id]; return { exists: !!d, data: () => d }; } }),
      get: async () => ({ docs: Object.entries(store[n] || {}).map(([id, d]) => ({ id, data: () => d })) }), onSnapshot: cb => { cb({ docs: Object.entries(store[n] || {}).map(([id, d]) => ({ id, data: () => d })) }); return () => {}; } }) };
    const mcp = { callTool: async (server, tool, input) => { window.__calls.push({ tool }); return { payload: { results: [] } }; } };
    const stub = new Function('return ' + stubSrc)();
    const sample = async () => ({ text: '', truncated: false });
    sample.json = async (prompt, o) => { window.__prompts.push(String(prompt)); window.__calls.push({ tool: 'sample', images: o && o.images ? (Array.isArray(o.images) ? o.images.length : 1) : 0, sizes: o && Array.isArray(o.images) ? o.images.map(b => b.size) : [] }); return stub(String(prompt), o); };
    if (OPT.images) sample.limits = async () => ({ maxPromptBytes: 262144, images: { maxCount: OPT.images, maxInputBytes: 5e6, mediaTypes: ['image/jpeg', 'image/png'] } });   // the runtime reports `images` only when the page declares sample.images
    Object.freeze(sample);
    window.claude = { use: async name => name === 'db' ? fakeDb : name === 'mcp' ? mcp : name === 'sample' ? sample : name === 'downloads' ? { save: async ({ filename, data }) => { const buf = new Uint8Array(await data.arrayBuffer()); window.__dl.push({ filename, size: buf.length }); window.__lastDl = buf; } } : null };
  };
  await ctx.addInitScript(INIT, { stubSrc: claudeStub.toString(), opts });
  const outside = []; await ctx.route(u => !/^(http:\/\/127\.0\.0\.1[:/]|data:|blob:|about:)/.test(u.href), r => { outside.push(r.request().url()); r.abort(); });
  const page = await ctx.newPage(); const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message)); page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto(base + '/index.html'); await page.waitForSelector('#nbDrop');
  return { page, browser, server, outside, errors, close: async () => { await browser.close(); server.close(); } };
};
exports.loadFile = async (page, fuFile) => {
  await page.setInputFiles('#stFile', fuFile); await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 90000 });
  await page.waitForFunction(() => window.__nb && window.__nb.version === 1, null, { timeout: 30000 });
};
exports.dropPdf = async (page, pdf, n = 1) => {
  const have = await page.evaluate(() => window.__station.state.nb.files.length);
  await page.setInputFiles('#nbFile', pdf);
  await page.waitForFunction(k => window.__station.state.nb.files.length === k && window.__station.state.nb.files.every(f => f.status !== 'reading') && !window.__station.state.nb.reading, have + n, { timeout: 180000 });
};
exports.items = page => page.evaluate(() => window.__station.state.nb.items.map(it => ({ key: it.key, st: it.screen.status, why: it.screen.why, of: it.screen.of, hl: it.p.headline, date: it.p.date, outlet: it.p.outlet, outlet_clean: it.p.outlet_clean, section: it.p.section, words: it.p.words_nb, docref: it.p.docref,
  kind: it.p.kind, thin: it.p.thin, flags: it.p.flags, link: it.p.docref ? 'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=' + it.p.docref : '', pages: it.batch.firstPage + '-' + it.batch.lastPage, idx: it.batch.index, bands: it.batch.bands, shared: !!it.batch.sharedFirst, pdfid: it.fileId, pdf: it.pdf && it.pdf.bytes, include: it.include, author: it.p.author, body_words: it.p.body_words })));
/* the for-Update file's NewsBank links: docref (lower case) -> [aid, kind, outlet, date] */
exports.knownDocrefs = fuFile => { const fu = JSON.parse(fs.readFileSync(fuFile, 'utf8')), m = new Map(); fu.rows.rows.forEach(r => (r[6] || []).forEach(l => { const x = /docref=([^&\s#]+)/i.exec(l); if (x) m.set(decodeURIComponent(x[1]).toLowerCase(), { aid: r[0], sid: r[1], kind: r[2], outlet: r[3], date: r[4] }); })); return { fu, known: m }; };
