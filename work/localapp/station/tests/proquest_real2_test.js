/* SECOND REAL ProQuest PDF (2026-11-03): Food Processing, 2026-03-26, ProQuest document 3374372406: a trade journal, no Pages field, a wrapped headline ("...Non-" / "UPF Foods"), a wrapped Document URL,
   "Publication history :" labels, the details block cut by the page-1 footer. The story is already in the tracker (07406 / s02194, from the publisher's site, no ProQuest link), so phase 1 expects "known" by headline;
   phase 2 takes that story out of a copy of the for-Update file and expects a NEW find, runs the card with canned Claude/TinyFish and packs the update folder (OUT/pq2_update.zip).
   AJG_REAL_PQ2=/path/real2.pdf node tests/proquest_real_test.js --page dist/index.html --file FOR_UPDATE.json --out OUTDIR
   Skips (exit 0) when AJG_REAL_PQ2 is not set: the PDF is licensed text and is never in the repository.
   (not used) Same set-up as newsbank_test.js: the page is served on 127.0.0.1 inside the skeleton the Artifact tool adds,
   under a strict Content-Security-Policy (inline scripts only; no eval, no worker, no blob: script, no connections); window.claude is a stub (db in
   memory, TinyFish search / fetch canned, sample canned); the downloaded zip is written to OUTDIR (checked afterwards by tests/pq/verify_pq_zip.py). */
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page'), FILE = arg('file'), OUT = arg('out'), REAL = process.env.AJG_REAL_PQ2;
if (!REAL || !fs.existsSync(REAL)) { console.log('SKIPPED: set AJG_REAL_PQ2 to the real ProQuest PDF (licensed text: keep it out of the repository)'); process.exit(0); }
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



const mk = require('child_process');
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
const HL = 'California May Create a Certification and Seal for Non-UPF Foods';
async function open(browser, fuFile) {
  const ctx = await browser.newContext({ viewport: { width: 1300, height: 1100 }, acceptDownloads: true });
  await ctx.addInitScript(INIT, { hl: {} });
  await ctx.addInitScript(() => { try { localStorage.setItem('ajg_station_auto', '0'); } catch (e) {} });   // AUTOSTATION-v1: these tests click each step themselves (the automatic mode has its own test)
  const page = await ctx.newPage(); const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(base + '/index.html'); await page.waitForSelector('#pqDrop');
  await page.setInputFiles('#stFile', fuFile); await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 90000 });
  await page.waitForFunction(() => window.__pq && window.__pq.version === 1, null, { timeout: 30000 });
  await page.setInputFiles('#pqFile', REAL);
  await page.waitForFunction(() => window.__station.state.pq.files.length === 1 && window.__station.state.pq.files[0].status !== 'reading' && !window.__station.state.pq.reading, null, { timeout: 120000 });
  return { page, errors };
}
const items = page => page.evaluate(() => window.__station.state.pq.items.map(it => ({ st: it.screen.status, why: it.screen.why, of: it.screen.of, hl: it.p.headline, date: it.p.date, outlet: it.p.outlet_clean, resolved: it.outlet, author: it.p.author, docid: it.p.docid, link: it.p.link, source: it.p.source_type, flags: it.p.flags, problems: it.p.problems, words: it.p.body_words, text: it.p.text, pages: it.p.pages, page: it.p.page, lang: it.p.language, url_in_pdf: it.p.url_in_pdf, issn: it.p.issn, pdf: it.pdf && it.pdf.bytes })));
function readingChecks(x, f) {
  check('the PDF opens in the browser: 3 pages', f.status !== 'error' && f.pages === 3, JSON.stringify(f));
  check('headline: the two wrapped lines joined without a space, hyphen kept', x.hl === HL, x.hl);
  check('date 2026-03-26', x.date === '2026-03-26', x.date);
  check('author in the sheet’s form from “Fusaro, Dave . Fusaro, Dave.”', x.author === 'Dave Fusaro', x.author);
  check('outlet: “Food Processing; Chicago” -> Food Processing', x.outlet === 'Food Processing' && (x.resolved || x.outlet) === 'Food Processing', JSON.stringify([x.outlet, x.resolved]));
  check('ProQuest document ID 3374372406 and the plain docview link', x.docid === '3374372406' && x.link === 'https://www.proquest.com/docview/3374372406', x.docid + ' ' + x.link);
  check('the Document URL wrapped over 3 lines is read whole (CSL proxy form)', x.url_in_pdf === 'https://castatelib.idm.oclc.org/login?url=https://www.proquest.com/trade-journals/california-may-create-certification-seal-non-upf/docview/3374372406/se-2?accountid=26958', x.url_in_pdf);
  check('source type “Trade Journal”, no page: not a print record', x.source === 'Trade Journal' && !x.page, JSON.stringify([x.source, x.page]));
  check('language English, ISSN 00156523', x.lang === 'English' && x.issn === '00156523', JSON.stringify([x.lang, x.issn]));
  check('no “needs a look”: no problems, no flags', (x.problems || []).length === 0 && (x.flags || []).length === 0, JSON.stringify([x.problems, x.flags]));
  const t = x.text || '';
  check('the text is the article only, from “A trailblazing California bill” to “according to his website.” (no DETAILS, Publication history, footer, links)', /^A trailblazing California bill aims/.test(t) && /according to his website\.$/.test(t) && !/DETAILS|Subject:|Publication history|Online publication date|First posting date|PDF GENERATED|Terms and Conditions|Check for Full Text|Database copyright|ProQuest document link|Document URL|Publication title|Fusaro|FULL TEXT|Page \d of \d/.test(t) && x.words > 380 && x.words < 480, t.slice(0, 60) + ' … ' + t.slice(-60) + ' ' + x.words);
}
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r)); global.base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();
  /* phase 1: the real for-Update file. The tracker holds this story (07406, Food Processing, same day, from the publisher's site) */
  { const { page, errors } = await open(browser, FILE);
    const f = await page.evaluate(() => window.__station.state.pq.files[0]), it = await items(page), x = it[0] || {};
    check('phase 1: one story read', it.length === 1, it.length);
    readingChecks(x, f);
    check('phase 1: already in the tracker, by outlet + headline + date (row 07406, the publisher’s copy), not new and not a reprint', x.st === 'known' && /same outlet and headline as 07406/.test(x.why || ''), JSON.stringify([x.st, x.why, x.of]));
    check('phase 1: no page errors', errors.length === 0, errors.slice(0, 3).join(' | ')); await page.context().close(); }
  /* phase 2: the same file without that story: a NEW find; run it and pack the folder */
  const fu = JSON.parse(fs.readFileSync(FILE, 'utf8'));
  fu.stories = fu.stories.filter(s => s.id !== 's02194'); fu.rows.rows = fu.rows.rows.filter(r => r[0] !== '07406'); for (const k of Object.keys(fu.idmap)) if (fu.idmap[k] === 's02194') delete fu.idmap[k];
  const fu2 = path.join(OUT, 'for_update_without_07406.json'); fs.writeFileSync(fu2, JSON.stringify(fu));
  const outside = [];
  { const { page, errors } = await open(browser, fu2);
    const it = await items(page), x = it[0] || {};
    check('phase 2: a NEW find (not known, not needs-a-look)', x.st === 'new' && !x.of, JSON.stringify([x.st, x.why, x.of]));
    check('phase 2: its PDF copy was made', x.pdf > 1000, x.pdf);
    await page.click('#pqAdd'); await page.waitForFunction(() => /Added:|Stopped/.test(document.querySelector('#pqProg').textContent), null, { timeout: 180000 });
    const prog = await page.textContent('#pqProg'); check('phase 2: the run finished', /^Added:/.test(prog), prog);
    const S = await page.evaluate(() => { const o = {}; for (const [c, m] of Object.entries(window.__station.sess)) o[c] = [...m].map(([id, v]) => [id, v.data]); return o; });
    const run = S.runs.map(r => r[1])[0], rows = run.rows, r = rows[0] || {};
    check('phase 2: one row, an Original, Data Source ProQuest, links in the sheet’s forms', rows.length === 1 && r['Original or reprint'] === 'Original' && r['Data Source'] === 'ProQuest' && r['ProQuest link'] === 'https://www.proquest.com/docview/3374372406' && r['ProQuest via CA State Library'] === 'https://castatelib.idm.oclc.org/login?url=https://www.proquest.com/docview/3374372406', JSON.stringify(r));
    check('phase 2: Outlet Food Processing, Date 2026-03-26, Author Dave Fusaro, Language English, not print (Edition blank, Format Article, Date source ProQuest), Page and Section blank', r.Outlet === 'Food Processing' && r.Date === '2026-03-26' && r['Author / byline'] === 'Dave Fusaro' && r.Language === 'English' && !r.Edition && r.Format === 'Article' && r['Date source'] === 'ProQuest' && !r.Page && !r.Section, JSON.stringify([r.Outlet, r.Date, r['Author / byline'], r.Language, r.Edition, r.Format, r['Date source'], r.Page, r.Section]));
    check('phase 2: no reprint rows', !rows.some(q => q['Original or reprint'] === 'Reprint'), rows.length);
    const pd = S.pages.map(q => q[1]).filter(d => d.pq)[0];
    check('phase 2: the pages doc holds the library’s ProQuest text form: 3 pages, h1 headline, byline, paragraphs', pd && /data-pages="3" data-shown="text"/.test(pd.clean) && pd.clean.includes('<h1>' + HL + '</h1>') && /<p class="byline">By Dave Fusaro<\/p>/.test(pd.clean) && /according to his website\.<\/p><\/article>/.test(pd.clean), pd && pd.clean.slice(0, 400));
    await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 20000 });
    await page.click('#stPack'); await page.waitForFunction(() => window.__dl.length > 0, null, { timeout: 60000 });
    const b64 = await page.evaluate(async () => { const b = window.__lastDl; let s = ''; const CH = 0x8000; for (let i = 0; i < b.length; i += CH) s += String.fromCharCode.apply(null, b.subarray(i, i + CH)); return btoa(s); });
    fs.writeFileSync(path.join(OUT, 'pq2_update.zip'), Buffer.from(b64, 'base64'));
    check('phase 2: no worker started, no page error', (await page.evaluate(() => window.__workers)) === 0 && errors.length === 0, errors.slice(0, 3).join(' | '));
    await page.context().close(); }
  console.log(failed ? failed + ' FAILED' : 'all passed');
  await browser.close(); server.close(); process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
