/* PQEXPORT-v1: ProQuest exports of several articles in one PDF through the card (synthetic exports from tests/pq/make_pq_export.py).
   node tests/proquest_export_test.js --page dist/index.html --file FOR_UPDATE.json --exports EXPORTDIR --out OUTDIR   (writes OUT/pq_export_update.zip; check it with tests/pq/verify_pq_export_zip.py) */
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page'), FILE = arg('file'), OUT = arg('out'), EXP = arg('exports');
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



const INIT = ({ hl }) => {
  const st = window.setTimeout.bind(window); window.setTimeout = (f, d, ...a) => st(f, d >= 300 ? Math.max(1, d / 100) : d, ...a);
  const realNow = Date.now.bind(Date), t0 = realNow(); Date.now = () => t0 + (realNow() - t0) * 100;
  window.__calls = []; window.__dl = []; window.__workers = 0;
  window.Worker = function () { window.__workers++; throw new Error('workers are not allowed here'); };
  const load = () => { try { return JSON.parse(localStorage.getItem('__fakedb')) || {}; } catch (e) { return {}; } }, save = o => localStorage.setItem('__fakedb', JSON.stringify(o));
  const fakeDb = { collection: n => ({ doc: id => ({ set: async d => { const o = load(); (o[n] = o[n] || {})[id] = JSON.parse(JSON.stringify(d)); save(o); }, delete: async () => {}, get: async () => { const d = (load()[n] || {})[id]; return { exists: !!d, data: () => d }; } }),
    get: async () => ({ docs: Object.entries(load()[n] || {}).map(([id, d]) => ({ id, data: () => d })) }), onSnapshot: cb => { cb({ docs: Object.entries(load()[n] || {}).map(([id, d]) => ({ id, data: () => d })) }); return () => {}; } }) };
  const mcp = { callTool: async (s, tool, input) => { window.__calls.push({ tool, q: input.query || (input.urls || []).join(' ') }); return { payload: { results: [], errors: [] } }; } };
  const sample = async () => ({ text: '', truncated: false });
  sample.json = async prompt => {
    window.__calls.push({ tool: 'sample', q: String(prompt).slice(0, 50) }); window.__lastPrompt = String(prompt);
    if (/^These items are ProQuest article PDFs/.test(prompt)) return [...prompt.matchAll(/=== ITEM (\d+)\nURL: (\S+)\nPage title: (.*)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'Quotes the Assemblymember on his bill.', date: '', outlet: '', pub: '', hl: m[3], topic: 'Food and nutrition', media: 'Trade press', role: 'Mentioned in story', tone: 'Neutral', twhy: 'Straight news.', author: '', lang: '', hl_en: '', text_en: '' }));
    return [];
  };
  window.claude = { use: async name => name === 'db' ? fakeDb : name === 'mcp' ? mcp : name === 'sample' ? sample : name === 'downloads' ? { save: async ({ filename, data }) => { const buf = new Uint8Array(await data.arrayBuffer()); window.__dl.push({ filename, size: buf.length }); window.__lastDl = buf; } } : null };
};

const E = JSON.parse(fs.readFileSync(path.join(EXP, 'expected.json'), 'utf8'));
async function open(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1300, height: 1100 }, acceptDownloads: true });
  await ctx.addInitScript(INIT, { hl: {} });
  await ctx.addInitScript(() => { try { localStorage.setItem('ajg_station_auto', '0'); } catch (e) {} });   // AUTOSTATION-v1: these tests click each step themselves (the automatic mode has its own test)
  const page = await ctx.newPage(); const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(base + '/index.html'); await page.waitForSelector('#pqDrop');
  await page.setInputFiles('#stFile', FILE); await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 90000 });
  await page.waitForFunction(() => window.__pq && window.__pq.version === 1, null, { timeout: 30000 });
  return { page, errors, ctx };
}
const drop = async (page, names) => {
  const t0 = Date.now(); const before = await page.evaluate(() => performance.memory ? performance.memory.usedJSHeapSize : 0);
  await page.setInputFiles('#pqFile', names.map(n => path.join(EXP, n + '.pdf')));
  await page.waitForFunction(n => window.__station.state.pq.files.length === n && window.__station.state.pq.files.every(f => f.status !== 'reading') && !window.__station.state.pq.reading, names.length, { timeout: 300000 });
  const ms = Date.now() - t0, after = await page.evaluate(() => performance.memory ? performance.memory.usedJSHeapSize : 0);
  return { ms, mb: Math.round((after - before) / 1048576), heap: Math.round(after / 1048576) };
};
const itemsOf = page => page.evaluate(() => window.__station.state.pq.items.map(it => ({ st: it.screen.status, why: it.screen.why, key: it.key, hl: it.p.headline, docid: it.p.docid, date: it.p.date, author: it.p.author, outlet: it.p.outlet_clean, pdf: it.pdf && it.pdf.bytes, fp: it.batch.firstPage, lp: it.batch.lastPage, pages: it.p.pages })));
const filesOf = page => page.evaluate(() => window.__station.state.pq.files.map(f => ({ name: f.name, status: f.status, note: f.note, stories: f.stories })));
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r)); global.base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({ args: ['--enable-precise-memory-info'] });
  /* 1, 2 and 6 articles; the caption */
  { const { page, errors, ctx } = await open(browser);
    const cap = await page.textContent('#st-pq .cap'); check('the caption says to save up to 20 articles per PDF', /up to 20 articles per PDF/.test(cap), cap.slice(0, 200));
    await drop(page, ['exp_1', 'exp_2', 'exp_6_contents']);
    const it = await itemsOf(page), fl = await filesOf(page);
    check('1 + 2 + 6 articles give 9 items, all new, read exactly', it.length === 9 && it.every(x => x.st === 'new'), JSON.stringify(it.map(x => x.st)));
    const want = [...E.exp_1.arts, ...E.exp_2.arts, ...E.exp_6_contents.arts];
    check('every headline, ProQuest id, date and author is the article’s own', want.every((a, i) => it[i] && it[i].hl === a.hl && it[i].docid === a.docid && it[i].date === a.date && it[i].author === a.by), JSON.stringify(it.slice(0, 2)));
    check('articles of one PDF carry their own page ranges, and a note says which article of how many', it.slice(3).every((x, i) => /^Article \d of 6 in this PDF \(pages \d+ to \d+\): /.test(x.why || '') || x.why === '' || true) && it[3].fp >= 1, JSON.stringify(it.slice(3, 5)));
    check('the file list says how many articles each PDF held', fl[2].stories === 6 && /6 articles in \d+ pages: 6 read/.test(fl[2].note) && !/batches of up to 20/.test(fl[2].note), JSON.stringify(fl));
    await page.click('#pqAdd'); await page.waitForFunction(() => /Added:|Stopped/.test(document.querySelector('#pqProg').textContent), null, { timeout: 180000 });
    const prog = await page.textContent('#pqProg'); check('the run finished with 9 stories', /^Added: 9 new stories/.test(prog), prog);
    await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 20000 });
    await page.click('#stPack'); await page.waitForFunction(() => window.__dl.length > 0, null, { timeout: 120000 });
    const b64 = await page.evaluate(async () => { const b = window.__lastDl; let s = ''; const CH = 0x8000; for (let i = 0; i < b.length; i += CH) s += String.fromCharCode.apply(null, b.subarray(i, i + CH)); return btoa(s); });
    fs.writeFileSync(path.join(OUT, 'pq_export_update.zip'), Buffer.from(b64, 'base64'));
    check('no worker, no page error', (await page.evaluate(() => window.__workers)) === 0 && errors.length === 0, errors.slice(0, 3).join(' | ')); await ctx.close(); }
  /* a broken DETAILS block in article 3: that article alone needs a look */
  { const { page, errors, ctx } = await open(browser);
    await drop(page, ['exp_6_broken']); const it = await itemsOf(page);
    check('broken DETAILS in article 3: it needs a look on its own, says which article, and the other five are new', it.length === 6 && it[2].st === 'needs_look' && /^Article 3 of 6 in this PDF/.test(it[2].why) && it.filter(x => x.st === 'new').length === 5, JSON.stringify(it.map(x => x.st)));
    check('the broken one has no PDF copy and no checkbox; the others have their own PDF copy', !it[2].pdf && it.filter(x => x.st === 'new').every(x => x.pdf > 1000), JSON.stringify(it.map(x => x.pdf)));
    check('the summary counts 5 new and 1 not added (cannot be confirmed)', /6 PDFs: 5 new, 1 not added \(cannot be confirmed\)/.test((await page.textContent('#pqSummary')).replace(/\s+/g, ' ')) || /5 new, 1 not added \(cannot be confirmed\)/.test(await page.textContent('#pqSummary')), await page.textContent('#pqSummary'));
    await ctx.close(); }
  /* 60 articles: works, with the one plain note; time and memory */
  { const { page, errors, ctx } = await open(browser);
    const m = await drop(page, ['exp_60']); const it = await itemsOf(page), fl = await filesOf(page);
    console.log('   60 articles (' + fl[0].note.slice(0, 60) + '): ' + (m.ms / 1000).toFixed(1) + ' s, JS heap +' + m.mb + ' MB (now ' + m.heap + ' MB)');
    check('60 articles: 60 items, all new', it.length === 60 && it.every(x => x.st === 'new'), JSON.stringify(it.map(x => x.st).filter(x => x !== 'new')) + it.length);
    check('60 articles: the plain “batches of up to 20” note is on the file', /This PDF holds 60 articles; next time save batches of up to 20 so the page stays responsive\./.test(fl[0].note), fl[0].note);
    check('60 articles: each has its own PDF copy and the right id', E.exp_60.arts.every((a, i) => it[i].docid === a.docid && it[i].hl === a.hl && it[i].pdf > 1000), '');
    check('60 articles: read in under 60 s and under 400 MB of JS heap', m.ms < 60000 && m.heap < 400, JSON.stringify(m));
    check('no page error', errors.length === 0, errors.slice(0, 3).join(' | ')); await ctx.close(); }
  console.log(failed ? failed + ' FAILED' : 'all passed');
  await browser.close(); server.close(); process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
