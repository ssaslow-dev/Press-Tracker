/* PROQUESTPDF-v1: hostile PDFs that look like ProQuest articles (JavaScript on open, a launch action, an embedded program) dropped in the station.
   The station's copy (pdf-lib, pages only) carries none of it; the PC check then accepts the zip (checked by tests/pq/verify_pq_zip.py --evil).
     node tests/proquest_evil_test.js --page dist/index.html --file FOR_UPDATE.json --pdfs PDFDIR --out ZIPDIR */
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page'), FILE = arg('file'), PDFS = arg('pdfs'), OUT = arg('out');
fs.mkdirSync(OUT, { recursive: true });
let failed = 0; const check = (name, ok, extra) => { if (!ok) failed++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (!ok && extra !== undefined ? '  -> ' + extra : '')); };
const shellHead = (() => { const vd = path.join(__dirname, '..', '..', 'vendor'); return fs.readFileSync(path.join(vd, fs.readdirSync(vd).filter(d => d.startsWith('live_')).sort().pop(), 'pipeline', 'shell.html'), 'utf8').split('<body>')[0] + '<body>'; })();
const wrapped = shellHead + fs.readFileSync(PAGE, 'utf8') + '</body></html>';
const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; worker-src 'none'; connect-src 'none'";
const server = http.createServer((req, res) => { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Security-Policy': CSP }); res.end(wrapped); });
const INIT = () => {
  const st = window.setTimeout.bind(window); window.setTimeout = (f, d, ...a) => st(f, d >= 300 ? Math.max(1, d / 100) : d, ...a);
  window.__dl = [];
  const mem = {}; const fakeDb = { collection: n => ({ doc: id => ({ set: async d => { (mem[n] = mem[n] || {})[id] = JSON.parse(JSON.stringify(d)); }, delete: async () => {}, get: async () => ({ exists: false, data: () => null }) }),
    get: async () => ({ docs: Object.entries(mem[n] || {}).map(([id, d]) => ({ id, data: () => d })) }), onSnapshot: cb => { cb({ docs: [] }); return () => {}; } }) };
  window.claude = { use: async name => name === 'db' ? fakeDb : name === 'downloads' ? { save: async ({ filename, data }) => { window.__lastDl = new Uint8Array(await data.arrayBuffer()); window.__dl.push({ filename }); } } : null };
};
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port, browser = await chromium.launch();
  for (const kind of ['openaction', 'embedded', 'launch']) {
    const ctx = await browser.newContext({ viewport: { width: 1300, height: 1100 } });
    await ctx.addInitScript(INIT);
    await ctx.addInitScript(() => { try { localStorage.setItem('ajg_station_auto', '0'); } catch (e) {} });   // AUTOSTATION-v1: these tests click each step themselves (the automatic mode has its own test)
    const page = await ctx.newPage(); const errs = []; page.on('pageerror', e => errs.push(e.message));
    await page.goto(base + '/'); await page.setInputFiles('#stFile', FILE); await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 90000 });
    await page.waitForFunction(() => window.__pq && window.__pq.version === 1, null, { timeout: 30000 });
    await page.setInputFiles('#pqFile', path.join(PDFS, `evil_${kind}.pdf`));
    await page.waitForFunction(() => window.__station.state.pq.files.length === 1 && window.__station.state.pq.files[0].status !== 'reading', null, { timeout: 60000 });
    const it = await page.evaluate(() => { const i = window.__station.state.pq.items[0]; return { st: i && i.screen.status, pdf: i && i.pdf && i.pdf.bytes }; });
    check(`evil_${kind}: read as a new story (the station reads text only) with a rebuilt PDF`, it.st === 'new' && it.pdf > 1000, JSON.stringify(it));
    await page.uncheck('#pqLinks').catch(() => {});
    await page.click('#pqAdd'); await page.waitForFunction(() => /Added:|Stopped/.test(document.querySelector('#pqProg').textContent), null, { timeout: 60000 });
    await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 20000 });
    await page.click('#stPack'); await page.waitForFunction(() => window.__dl.length > 0, null, { timeout: 60000 });
    const b64 = await page.evaluate(() => { const b = window.__lastDl; let s = ''; for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000)); return btoa(s); });
    fs.writeFileSync(path.join(OUT, `evil_${kind}.zip`), Buffer.from(b64, 'base64'));
    check(`evil_${kind}: no page error`, errs.length === 0, errs.join('; '));
    await ctx.close();
  }
  console.log(failed ? failed + ' FAILED' : 'all passed'); await browser.close(); server.close(); process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
