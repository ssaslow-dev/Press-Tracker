/* Playwright test for the Update station page (work/localapp/station). Run:
     node tests/station_test.js --page DIST/index.html --file FOR_UPDATE.json --out OUTDIR
   Everything is local: the page is served on 127.0.0.1 inside the same wrapper the Artifact tool adds, window.claude is a stub
   (db in memory, TinyFish search/fetch canned from three fake articles, sample canned), and the downloaded zip is written to OUTDIR. */
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page'), FILE = arg('file'), OUT = arg('out'), DBMODE = arg('db-mode') || 'empty';   // empty | stale (junk left by an earlier use) | none (no db capability)
fs.mkdirSync(OUT, { recursive: true });
const eq2 = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const results = []; let failed = 0;
const check = (name, ok, extra) => { results.push({ name, ok: !!ok, extra: extra === undefined ? '' : String(extra) }); if (!ok) failed++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra !== undefined && !ok ? '  -> ' + extra : '')); };

const laDay = (d = new Date()) => d.toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' });
const TODAY = laDay(), dayAgo = n => laDay(new Date(Date.now() - n * 864e5));
const fu = JSON.parse(fs.readFileSync(FILE, 'utf8'));
const exist1 = fu.stories.find(s => s.id === 's04930'), exist2 = fu.stories.find(s => s.id === 's04931');

const ARTICLES = {
  new1: { url: 'https://www.valleygazette-test.com/2026/11/gabriel-clean-air-permits', title: 'Gabriel unveils bill to speed clean air permits', date: dayAgo(2), author: 'Dana Whitfield',
    body: 'Assemblymember Jesse Gabriel (D-Encino) introduced a bill in Sacramento on Friday that would speed up clean air permits across California. "Californians should not wait years for clean air," Gabriel said in a statement to reporters at the Capitol. The measure would set a deadline for regional air districts and has the backing of several environmental groups, lawmakers said. ' + 'The bill is expected to go before the Assembly Natural Resources Committee early next year. '.repeat(8) },
  new2: { url: 'https://www.diariotest.example/2026/11/gabriel-ley-vivienda', title: 'Gabriel presenta ley de vivienda', date: dayAgo(1), author: '',
    body: 'El asambleísta Jesse Gabriel (D-Encino) presentó una ley de vivienda en Sacramento, California, que busca acelerar la construcción de viviendas asequibles en el Valle de San Fernando. ' + 'La propuesta pasará al comité de la Asamblea el próximo mes. '.repeat(10) },
  rep: { url: 'https://www.anotherpaper-test.com/news/sports-prison-walls', title: exist2.hl, date: dayAgo(1), author: 'Wire Desk',
    body: 'Assemblymember Jesse Gabriel (D-Encino) and other California lawmakers visited a prison sports program. ' + 'Organized sports can reduce recidivism, advocates said at the Sacramento hearing. '.repeat(10) },
};
const html = a => `<html><head><title>${a.title}</title></head><body><article><h1>${a.title}</h1><p>${a.body}</p></article></body></html>`;
const SEARCH_HITS = [
  { url: ARTICLES.new1.url, title: ARTICLES.new1.title, date: ARTICLES.new1.date, snippet: 'Assemblymember Jesse Gabriel (D-Encino) introduced a bill to speed clean air permits in California.', site_name: 'Valley Gazette' },
  { url: ARTICLES.new2.url, title: ARTICLES.new2.title, date: ARTICLES.new2.date, snippet: 'El asambleísta Jesse Gabriel (D-Encino) presentó una ley de vivienda en California.', site_name: 'Diario Test' },
  { url: exist1.link, title: exist1.hl, date: exist1.date, snippet: 'Jesse Gabriel delivers $2.5 million, California Assembly Budget Chair.', site_name: exist1.outlet },   // same link as a story in the file: must not come back as new
  { url: ARTICLES.rep.url, title: ARTICLES.rep.title, date: ARTICLES.rep.date, snippet: 'Assemblymember Jesse Gabriel (D-Encino) California prison sports.', site_name: 'Another Paper' },
];
const CLASSIFY = {
  [ARTICLES.new1.url]: { keep: true, why: 'News story on his bill.', date: ARTICLES.new1.date, outlet: 'Valley Gazette', pub: 'Valley Gazette', hl: ARTICLES.new1.title, topic: 'Energy / environment', media: 'Online news', role: 'Named in headline', tone: 'Positive', twhy: 'Quotes Gabriel on his own bill.', author: '', lang: '', hl_en: '', text_en: '' },
  [ARTICLES.new2.url]: { keep: true, why: 'Spanish-language story on his housing bill.', date: ARTICLES.new2.date, outlet: 'Diario Test', pub: 'Diario Test', hl: ARTICLES.new2.title, topic: 'Housing / homelessness', media: 'Online news', role: 'Named in headline', tone: 'Neutral', twhy: 'Straight news.', author: 'María López; Juan Pérez', lang: 'Spanish', hl_en: 'Gabriel introduces housing bill', text_en: 'Assemblymember Jesse Gabriel introduced a housing bill in Sacramento.' },
  [ARTICLES.rep.url]: { keep: true, why: 'Same story as one in the log.', date: ARTICLES.rep.date, outlet: 'Another Paper', pub: 'Another Paper', hl: ARTICLES.rep.title, topic: 'Other / roundup', media: 'Online news', role: 'Mentioned in story', tone: 'Neutral', twhy: '', author: '', lang: '', hl_en: '', text_en: '' },
};
const CALLS = [];

/* ---- local server: the page inside the skeleton the Artifact tool adds; the for-Update file; nothing else ---- */
const shellHead = (() => { const s = fs.readFileSync(path.join(__dirname, '..', '..', 'vendor', fs.readdirSync(path.join(__dirname, '..', '..', 'vendor')).filter(d => d.startsWith('live_')).sort().pop(), 'pipeline', 'shell.html'), 'utf8'); return s.slice(0, s.indexOf('<body>') + 6).replace(/<link rel="(?:preconnect|stylesheet)"[^>]*fonts\.g[^>]*>\s*/g, ''); })();   // the Artifact tool's skeleton has no font links; the vendor head's Google links are not part of the page under test
const wrapped = shellHead + fs.readFileSync(PAGE, 'utf8') + '</body></html>';
const server = http.createServer((req, res) => {
  if (req.url.split('?')[0] === '/index.html' || req.url === '/') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); res.end(wrapped); }
  else if (req.url === '/for_update.json') { res.writeHead(200, { 'Content-Type': 'application/json' }); fs.createReadStream(FILE).pipe(res); }
  else { res.writeHead(404); res.end('no'); }
});

const INIT = ({ hits, pages, classify, today, dbMode }) => {
  const st = window.setTimeout.bind(window);
  window.setTimeout = (f, d, ...a) => st(f, d >= 300 ? Math.max(1, d / 100) : d, ...a);   // the TinyFish 2.1 s throttle, compressed
  const realNow = Date.now.bind(Date), t0 = realNow(); Date.now = () => t0 + (realNow() - t0) * 100;   // the clock runs 100x so the 2.1 s TinyFish throttle does not pile up
  window.__calls = []; window.__dl = [];
  // the artifact's own db is scratch: 'stale' leaves what an earlier use could have left (a future searched_to, a waiting clip, an edit); the station must ignore it
  const stale = dbMode === 'stale' ? { runs: { 'run-stale0001': { at: '2030-01-01T00:00:00Z', mode: 'find', searched_to: '2030-01-01', status: 'done', stories: [], reprints: [] } },
    clips: { 'jg-stale1': { date: '2026-10-30', outlet: 'Stale Gazette', pub: 'Stale Gazette', hl: 'Stale story from an earlier use', link: 'https://stale.example/x', plink: 'https://stale.example/x', added: '2026-10-30' } },
    edits: { s04931: { removed: true, at: '2026-10-30' } }, packed: { 'run-old': { run: 'run-old' } } } : {};
  // the artifact db stub persists across reloads of the page (localStorage) like the real one would
  const load = () => { try { return JSON.parse(localStorage.getItem('__fakedb')) || null; } catch (e) { return null; } };
  if (!load()) localStorage.setItem('__fakedb', JSON.stringify(stale));
  const save = o => localStorage.setItem('__fakedb', JSON.stringify(o));
  Object.defineProperty(window, '__realdb', { get: () => load() || {} });
  const fakeDb = { collection: n => ({
    doc: id => ({ set: async d => { const o = load() || {}; (o[n] = o[n] || {})[id] = JSON.parse(JSON.stringify(d)); save(o); }, delete: async () => {},
      get: async () => { const d = ((load() || {})[n] || {})[id]; return { exists: !!d, data: () => d }; } }),
    get: async () => ({ docs: Object.entries((load() || {})[n] || {}).map(([id, d]) => ({ id, data: () => d })) }),
    onSnapshot: cb => { cb({ docs: Object.entries((load() || {})[n] || {}).map(([id, d]) => ({ id, data: () => d })) }); return () => {}; } }) };
  const mcp = { callTool: async (server, tool, input) => {
    window.__calls.push({ tool, q: input.query || (input.urls || []).join(' ') });
    if (tool === 'search') { const q = String(input.query || ''); return { payload: { results: /^"Jesse Gabriel"$/.test(q) ? hits : [] } }; }
    if (tool === 'fetch_content') return { payload: { results: (input.urls || []).filter(u => pages[u]).map(u => ({ url: u, final_url: u, title: pages[u].title, text: pages[u].html, author: pages[u].author, published_date: '' })), errors: [] } };
    return { payload: {} };
  } };
  const sample = async () => ({ text: '', truncated: false });
  sample.json = async (prompt) => {
    window.__calls.push({ tool: 'sample', q: String(prompt).slice(0, 40) });
    if (/^You screen web search results/.test(prompt)) { const n = (prompt.match(/^=== \d+$/gm) || []).length; return Array.from({ length: n }, (_, i) => ({ n: i + 1, keep: true, why: 'names him' })); }
    if (/^You are screening web search results/.test(prompt)) {
      const items = [...prompt.matchAll(/=== ITEM (\d+)\nURL: (\S+)/g)];
      return items.map(m => Object.assign({ n: +m[1] }, classify[m[2]] || { keep: false, why: 'unknown in test' }));
    }
    return [];
  };
  window.claude = { use: async name => name === 'db' ? (dbMode === 'none' ? null : fakeDb) : name === 'mcp' ? mcp : name === 'sample' ? sample
    : name === 'downloads' ? { save: async ({ filename, data }) => { const buf = new Uint8Array(await data.arrayBuffer()); window.__dl.push({ filename, size: buf.length }); window.__lastDl = buf; } } : null };
};

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1200, height: 1000 }, acceptDownloads: true });
  const pages = {}; Object.values(ARTICLES).forEach(a => { pages[a.url] = { title: a.title, html: html(a), author: a.author }; });
  await ctx.addInitScript(INIT, { hits: SEARCH_HITS, pages, classify: CLASSIFY, today: TODAY, dbMode: DBMODE });
  const outside = []; await ctx.route(u => !/^(http:\/\/127\.0\.0\.1[:/]|data:|blob:|about:)/.test(u.href), r => { outside.push(r.request().url()); r.abort(); });   // LOCALFONTS-v1: record and refuse any request that leaves the machine
  const page = await ctx.newPage();
  const errors = []; page.on('pageerror', e => errors.push('pageerror: ' + e.message)); page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

  /* 1. before a file is loaded */
  await page.goto(base + '/index.html');
  await page.waitForSelector('#stDrop');
  check('step 1 shows a drop zone and file picker', await page.locator('#stDrop').isVisible() && (await page.locator('#stFile').count()) === 1);
  check('Update button is disabled before a file is loaded', await page.$eval('#runFind', b => b.disabled));
  await page.evaluate(() => document.querySelector('#runFind').click());
  check('clicking it does nothing: tracker code not started, no confirm dialog', (await page.locator('#rcScrim').count()) === 0 && !(await page.evaluate(() => window.__station.state.loaded)));
  check('step 3 button is disabled', await page.$eval('#stPack', b => b.disabled));
  /* gate: the NewsBank and ProQuest boxes are shut until a valid for-Update file is loaded (all three actions need it) */
  for (const k of ['nb', 'pq']) {
    check('gate ' + k + ': box is locked, input disabled, plain message shown', await page.locator('#st-' + k + '.st-lock').count() === 1 && await page.$eval('#' + k + 'File', i => i.disabled) && await page.locator('#' + k + 'Gate').isVisible() && /^Load the for Update file first/.test(await page.textContent('#' + k + 'Gate')), await page.textContent('#' + k + 'Gate'));
    await page.evaluate(k => { const dt = new DataTransfer(); dt.items.add(new File([new Uint8Array([37, 80, 68, 70, 45])], 'x.pdf', { type: 'application/pdf' })); document.getElementById(k + 'Drop').dispatchEvent(new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true })); }, k);
    check('gate ' + k + ': a PDF dropped anyway is refused ("Load the for Update file first") and nothing is read', /Load the for Update file first/.test(await page.textContent('#' + k + 'Msg')) && await page.evaluate(k => window.__station.state[k] ? window.__station.state[k].files.length === 0 : true, k), await page.textContent('#' + k + 'Msg'));
  }
  check('gate: Update button, step 3 and both PDF boxes all wait for the file', await page.$eval('#runFind', b => b.disabled) && await page.$eval('#stPack', b => b.disabled));
  check('other tabs are hidden', !(await page.locator('nav.tabs').isVisible()) && !(await page.locator('#view-ov').isVisible()));
  await page.screenshot({ path: path.join(OUT, 'shot_1_before.png') });

  /* 1b. fonts (LOCALFONTS-v1): the real Roboto Slab and Public Sans, from the page itself, no outside request */
  const fnt = await page.evaluate(async () => {
    const want = [['700 16px "Roboto Slab"', 'Abc'], ['800 16px "Roboto Slab"', 'Abc'], ['500 16px "Roboto Slab"', 'Abc'], ['600 16px "Roboto Slab"', 'Łódź'], ['400 16px "Public Sans"', 'Abc'], ['700 16px "Public Sans"', 'Abc'], ['500 16px "Public Sans"', 'Łódź'], ['600 16px "Public Sans"', 'Abc']];
    const got = {}; for (const [spec, txt] of want) { const l = await document.fonts.load(spec, txt); got[spec + '|' + txt] = l.length && l.every(f => f.status === 'loaded'); }
    await document.fonts.ready;
    const slab = [...document.querySelectorAll('h1,h2,h3,b,.sec,.tile b')].filter(e => e.offsetParent && /^"?Roboto Slab/.test(getComputedStyle(e).fontFamily)).length;
    const faces = [...document.fonts].map(f => f.family.replace(/"/g, '') + '|' + f.weight + '|' + f.status);
    return { got, slab, faces, body: getComputedStyle(document.body).fontFamily, src: [...document.querySelectorAll('style')].map(x => x.textContent).join('').includes('data:font/woff2;base64,') };
  });
  check('Roboto Slab (500-800) and Public Sans (400-700) faces load, latin and latin-ext', Object.values(fnt.got).every(Boolean), JSON.stringify(fnt.got));
  check('18 inlined faces, none in error', fnt.faces.filter(f => /^(Roboto Slab|Public Sans)\|/.test(f)).length === 18 && !fnt.faces.some(f => f.endsWith('|error')), JSON.stringify(fnt.faces));
  check('headings use Roboto Slab, body uses Public Sans', fnt.slab > 0 && /^"?Public Sans/.test(fnt.body), fnt.slab + ' ' + fnt.body);
  check('the fonts are inline data: URIs (no file, no outside link)', fnt.src);
  check('no request left the machine (Google Fonts or anything else)', outside.length === 0, outside.join(' '));
  await page.screenshot({ path: path.join(OUT, 'shot_fonts.png') });

  /* 2. a wrong file is refused */
  fs.writeFileSync(path.join(OUT, 'bad.json'), JSON.stringify({ hello: 1 }));
  await page.setInputFiles('#stFile', path.join(OUT, 'bad.json'));
  await page.waitForSelector('#stErr:not([hidden])');
  check('a file that is not a for-Update file is refused with a message', /not a “for Update” file/.test(await page.textContent('#stErr')), await page.textContent('#stErr'));
  fs.writeFileSync(path.join(OUT, 'bad2.json'), '{not json');
  await page.setInputFiles('#stFile', path.join(OUT, 'bad2.json'));
  await page.waitForFunction(() => /Could not read/.test(document.querySelector('#stErr').textContent));
  check('a broken file is refused', !(await page.evaluate(() => window.__station.state.loaded)));
  const noFp = JSON.parse(JSON.stringify({ format: 'ajg-for-update', format_version: 1, stories: [{ id: 'x' }], rows: { rows: [[1]] }, fingerprint: {} }));
  fs.writeFileSync(path.join(OUT, 'bad3.json'), JSON.stringify(noFp));
  await page.setInputFiles('#stFile', path.join(OUT, 'bad3.json'));
  await page.waitForFunction(() => /fingerprint/.test(document.querySelector('#stErr').textContent));
  check('a file without a workbook fingerprint is refused', !(await page.evaluate(() => window.__station.state.loaded)));
  check('gate stays shut after refused files', await page.$eval('#nbFile', i => i.disabled) && await page.$eval('#pqFile', i => i.disabled) && await page.locator('#nbGate').isVisible() && await page.locator('#pqGate').isVisible());

  /* 3. load the real file (picker) */
  await page.setInputFiles('#stFile', FILE);
  await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 60000 });
  const facts = await page.textContent('#stFacts');
  check('file facts shown: workbook short form', facts.includes(fu.fingerprint.workbook_sha256.slice(0, 8)), facts);
  check('file facts shown: story count', facts.includes(fu.stories.length.toLocaleString('en-US')), facts);
  check('Update button enabled after load', !(await page.$eval('#runFind', b => b.disabled)));
  check('gate opens after load: both PDF boxes enabled, no gate message', !(await page.$eval('#nbFile', i => i.disabled)) && !(await page.$eval('#pqFile', i => i.disabled)) && !(await page.locator('#nbGate').isVisible()) && !(await page.locator('#pqGate').isVisible()));
  { const ageTxt = await page.textContent('#stAge'), ageDays = Math.floor((Date.now() - Date.parse(fu.created_at)) / 864e5), isOld = ageDays > 7;
    check('file date and age in days shown', await page.locator('#stAge').isVisible() && (ageDays === 0 ? /today/.test(ageTxt) : new RegExp(ageDays + ' days? old').test(ageTxt)), ageTxt);
    check('age warning only when older than 7 days', isOld === /make a fresh one from the PC tracker so stories saved since are not found again/.test(ageTxt), ageTxt); }
  await page.waitForFunction(() => document.querySelector('#updGo'), null, { timeout: 30000 });
  check('step 2 shows the Update panel with Since control and the tracker’s Update button', await page.locator('#updSince').isVisible() && await page.locator('#updGo').isVisible());
  check('Refresh from files / Spreadsheet / Manage buttons are hidden', !(await page.locator('#runRefresh').isVisible()) && !(await page.locator('#updRefresh').isVisible()) && !(await page.locator('#updBtn').isVisible()));
  const sinceDef = await page.inputValue('#updSince');
  check('Since default comes from the data in the file (newest clip, no earlier run), whatever the db holds', sinceDef === fu.stories.filter(r => r.prec === 'day' && r.date <= TODAY).map(r => r.date).sort().pop(), sinceDef);
  await page.screenshot({ path: path.join(OUT, 'shot_2_loaded.png'), fullPage: true });

  /* 4. Update */
  await page.click('#runFind');
  await page.waitForSelector('#rcScrim:not([hidden])');
  check('header Update button asks “Are you sure?” with the Since field', await page.locator('#rcSince').isVisible());
  await page.click('#rcYes');
  await page.waitForFunction(() => { const f = document.querySelector('#updBody'); return f && (document.querySelector('#updAdd') || /Added|Nothing new|Stopped|nothing/i.test(f.textContent)) && !document.querySelector('#updStop'); }, null, { timeout: 180000 });
  const searches = await page.evaluate(() => window.__calls.filter(c => c.tool === 'search').length), fetches = await page.evaluate(() => window.__calls.filter(c => c.tool === 'fetch_content').length);
  console.log('   searches', searches, 'fetches', fetches);
  check('the run searched (many TinyFish searches issued)', searches > 50, searches);
  let body = await page.textContent('#updBody');
  await page.screenshot({ path: path.join(OUT, 'shot_3_review.png'), fullPage: true });
  check('new story from the canned search is found (English)', body.includes(ARTICLES.new1.title) || (await page.evaluate(() => JSON.stringify(window.__station.sess.runs.size))) !== '0');
  const hlList = await page.$$eval('#updBody .upd-item .h a', as => as.map(a => a.textContent));
  console.log('   review list:', JSON.stringify(hlList));
  if (await page.locator('#updAdd').count() && !(await page.$eval('#updAdd', b => b.disabled))) { await page.click('#updAdd'); await page.waitForFunction(() => /Added/.test(document.querySelector('#updBody').textContent) || !document.querySelector('#updAdd'), null, { timeout: 60000 }); }
  // a reprint candidate left unticked waits in review: add it too
  for (let k = 0; k < 3; k++) { if (await page.locator('#updAdd').count() && !(await page.$eval('#updAdd', b => b.disabled))) { await page.click('#updAdd'); await page.waitForTimeout(1500); } }
  await page.waitForFunction(() => window.__station.sess.runs.size > 0, null, { timeout: 30000 });
  await page.waitForTimeout(1500);
  body = await page.textContent('#updBody');
  const S = await page.evaluate(() => { const o = {}; for (const [c, m] of Object.entries(window.__station.sess)) o[c] = [...m].map(([id, v]) => [id, v.data]); return o; });
  fs.writeFileSync(path.join(OUT, 'session_docs.json'), JSON.stringify(S, null, 1));
  if (DBMODE !== 'none') {
    await page.waitForFunction(() => !window.__station.mirrorBusy(), null, { timeout: 30000 });
    const nSess = S.runs.length + S.pages.length + S.reprints.length + S.authors.length + S.translations.length + S.tones.length + S.edits.length;
    const mirrored = await page.evaluate(() => Object.values(window.__realdb.recover || {}).filter(d => !d.deleted).length);
    check('documents written after loading are mirrored to the db for recovery (sessions docs + clips)', mirrored >= nSess, mirrored + ' vs ' + nSess);
    await page.reload(); await page.waitForSelector('#stDrop');
    check('after a reload the station starts empty (nothing carried over by itself)', await page.evaluate(() => !window.__station.state.loaded && window.__station.sess.runs.size === 0));
    await page.setInputFiles('#stFile', FILE); await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 60000 });
    await page.waitForSelector('#stRecover:not([hidden])', { timeout: 20000 });
    check('same file loaded again: the unfinished run is offered for recovery', /1 run/.test(await page.textContent('#stRecoverTxt')), await page.textContent('#stRecoverTxt'));
    check('nothing is packable before the user recovers', await page.$eval('#stPack', b => b.disabled));
    await page.click('#stRecoverBtn');
    await page.waitForFunction(() => window.__station.sess.runs.size === 1 && window.__station.sess.pages.size >= 3, null, { timeout: 20000 });
    const S2 = await page.evaluate(() => { const o = {}; for (const [c, m] of Object.entries(window.__station.sess)) o[c] = [...m].map(([id, v]) => [id, v.data]); return o; });
    check('recovered documents equal the originals', JSON.stringify(S2) === JSON.stringify(S), '');
    await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 10000 });
    check('a recovered run can be packed', true);
  }
  const run = S.runs[0] && S.runs[0][1];
  check('a run doc was saved in the station session', !!run, JSON.stringify(Object.keys(S.runs)));
  check('run doc is final (status done) with searched_to = today or not set by an unclean run', run && run.status === 'done', run && run.status);
  check('run doc carries searched_to for the next Update (today)', run && run.searched_to === TODAY, run && run.searched_to);
  const storyIds = (run && run.stories) || [];
  check('two new stories added (English + Spanish)', storyIds.length === 2, JSON.stringify(storyIds));
  check('the find that duplicates an existing story (same link) was not added', !JSON.stringify(S).includes('"hl":"' + exist1.hl.replace(/"/g, '\\"') + '"') && !(run.rows || []).some(r => r['Publisher link'] === exist1.link), '');
  const rowsLinks = (run.rows || []).map(r => r['Publisher link']);
  check('proposed rows: one Original per new story and one Reprint', (run.rows || []).filter(r => r['Original or reprint'] === 'Original').length === 2 && (run.rows || []).filter(r => r['Original or reprint'] === 'Reprint').length >= 1, JSON.stringify((run.rows || []).map(r => [r['Original or reprint'], r['Outlet']])));
  const rp = S.reprints[0] && S.reprints[0][1];
  check('reprint candidate recorded against the existing story', rp && rp.story === 's04931' && rp.link === ARTICLES.rep.url, JSON.stringify(S.reprints));
  check('reprint candidate is marked as added today', rp && rp.added === TODAY, rp && rp.added);
  check('pages docs saved for the new stories and the reprint candidate', S.pages.length >= 3 && S.pages.some(([id]) => /^rp-/.test(id)), JSON.stringify(S.pages.map(p => p[0])));
  check('translation doc for the Spanish find (headline + summary)', S.translations.length === 1 && S.translations[0][1].hl === 'Gabriel introduces housing bill' && S.translations[0][1].lang === 'Spanish', JSON.stringify(S.translations));
  check('author doc for the find whose page had no byline (Claude split “A; B”)', S.authors.length === 1 && /María López; Juan Pérez/.test(S.authors[0][1].author), JSON.stringify(S.authors));
  const toneRows = (run.rows || []).filter(r => r['Original or reprint'] === 'Original').map(r => r['Tone']);
  check('tone rated for new finds (in the proposed rows)', toneRows.includes('Positive') && toneRows.includes('Neutral'), JSON.stringify(toneRows));
  await page.waitForFunction(() => !document.querySelector('#st').textContent.includes('save the last run to the sheet'), null, { timeout: 5000 }).catch(() => {});
  const stText = await page.textContent('#st'); const at = stText.indexOf('save the last run to the sheet');
  check('station text replaced the “ask Claude in chat” sentence', at < 0, at < 0 ? '' : stText.slice(Math.max(0, at - 120), at + 60));

  /* 5. step 3 */
  await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 10000 });
  const status = await page.textContent('#stPackStatus');
  check('step 3 says what is ready', /1 run: 2 new stories/.test(status), status);
  await page.click('#stPack');
  await page.waitForFunction(() => window.__dl.length > 0, null, { timeout: 30000 });
  const dl = await page.evaluate(() => ({ name: window.__dl[0].filename, bytes: Array.from(window.__lastDl) }));
  const zipPath = path.join(OUT, dl.name); fs.writeFileSync(zipPath, Buffer.from(dl.bytes));
  check('zip downloaded with a name carrying the workbook short sha', new RegExp("^ajg_update_\\d{8}-\\d{4}_" + fu.fingerprint.workbook_sha256.slice(0, 8) + "\\.zip$").test(dl.name), dl.name);
  { /* STATIONNAMES: every file in the folder carries its library name, numbers from the file's rows.next, and the PC's own checker accepts the block */
    const cp = require('child_process'), nx = fu.rows.next;
    const man = JSON.parse(cp.execFileSync('python3', ['-I', '-c', "import zipfile,sys;print(zipfile.ZipFile(sys.argv[1]).read('manifest.json').decode())", zipPath]).toString());
    const lst = cp.execFileSync('python3', ['-I', '-c', "import zipfile,sys;print('\\n'.join(zipfile.ZipFile(sys.argv[1]).namelist()))", zipPath]).toString().split('\n').filter(Boolean);
    const nm = man.names || {}, pad = (n, w) => String(n).padStart(w, '0');
    check('names block: starts at the for-Update file’s rows.next', nm.version === 1 && nm.from_next && nm.from_next.aid === nx.aid && nm.from_next.s === nx.s && nm.from_next.pr === nx.pr, JSON.stringify(nm.from_next));
    check('names: Article IDs run on from rows.next in the order the run proposes rows (Originals, then the Reprint)', (nm.items || []).map(i => i.aid).join() === [0, 1, 2].map(i => pad(nx.aid + i, 5)).join(), JSON.stringify((nm.items || []).map(i => i.aid)));
    const o1 = (nm.items || [])[0] || {}, rp = (nm.items || [])[2] || {};
    check('names: a web find is ws<aid>o-s<sid>.html in library/<year>/, a reprint candidate is ws<aid>r-s<existing sid>.html', /^library\/\d{4}\/ws\d{5}o-s\d{5}\.html$/.test(o1.copy) && o1.kind === 'o' && /^library\/\d{4}\/ws\d{5}r-s04931\.html$/.test(rp.copy) && rp.kind === 'r', JSON.stringify([o1.copy, rp.copy]));
    check('names: the files are in the zip under exactly those names, nothing else under library/', eq2(lst.filter(x => x.startsWith('library/')).sort(), (nm.items || []).flatMap(i => [i.copy, i.raw, i.pdf]).concat((nm.releases || []).flatMap(r => [r.copy, r.raw])).filter(Boolean).sort()), lst.join(' '));
  }
  await page.waitForTimeout(500);
  const recorded = await page.evaluate(id => !!(window.__realdb.packed || {})[id], S.runs[0][0]);
  check(DBMODE === 'none' ? 'no db capability: packing still works, nothing recorded' : 'station db records the run as packed (write only)', recorded === (DBMODE !== 'none'), JSON.stringify(await page.evaluate(() => window.__realdb)).slice(0, 300));
  check('the station db is never read for the run history: no stale run/clip/edit from it reached the session', !JSON.stringify(S).includes('stale') && !(await page.evaluate(() => document.body.textContent.includes('Stale story'))), '');
  check('after packing, nothing is left to pack and the button is off', await page.$eval('#stPack', b => b.disabled) && /Nothing new/.test(await page.textContent('#stPackStatus')), await page.textContent('#stPackStatus'));
  check('“download the last one again” is offered', await page.locator('#stPackAgain').isVisible());
  await page.screenshot({ path: path.join(OUT, 'shot_4_packed.png'), fullPage: true });
  fs.writeFileSync(path.join(OUT, 'pageerrors.txt'), errors.join('\n'));
  check('no page errors in the console', errors.length === 0, errors.slice(0, 5).join(' | '));

  /* 6. drag and drop in a fresh page */
  const p2 = await ctx.newPage();
  const errors2 = []; p2.on('pageerror', e => errors2.push(e.message));
  await p2.goto(base + '/index.html'); await p2.waitForSelector('#stDrop');
  await p2.evaluate(async () => { const b = await (await fetch('/for_update.json')).blob(); const f = new File([b], 'for_update_test.json', { type: 'application/json' }); const dt = new DataTransfer(); dt.items.add(f);
    document.querySelector('#stDrop').dispatchEvent(new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true })); });
  await p2.waitForSelector('#stLoaded:not([hidden])', { timeout: 60000 });
  await p2.waitForTimeout(1500);
  check('after the update folder was downloaded the same file offers no recovery', await p2.locator('#stRecover').isHidden());
  check('drag-and-drop loads the file too', (await p2.textContent('#stFacts')).includes('for_update_test.json') && errors2.length === 0, errors2.join('|'));

  /* 7. memory is seeded from the file: a file with an earlier run + waiting clip + removed story */
  const mem = JSON.parse(JSON.stringify(fu));
  const lastDay = dayAgo(10);
  mem.memory.searched_to = lastDay; mem.memory.searched_run = 'run-seedrun1';
  mem.memory.runs = { 'run-seedrun1': { at: lastDay + 'T12:00:00.000Z', mode: 'find', searched_to: lastDay, since: dayAgo(20), status: 'done', failed: '0 of 10', stories: ['jg-aa11bb'], reprints: [], sheet: {} } };
  mem.memory.clips = { 'jg-aa11bb': { date: dayAgo(11), outlet: 'Seed Gazette', pub: 'Seed Gazette', hl: 'Seeded story waiting for a save', link: 'https://www.seedgazette-test.com/seeded', plink: 'https://www.seedgazette-test.com/seeded', also: '', rep: 0, added: dayAgo(10) } };
  mem.memory.edits_removed = ['s04931'];
  const memPath = path.join(OUT, 'for_update_seeded.json'); fs.writeFileSync(memPath, JSON.stringify(mem));
  const p3 = await ctx.newPage(); const errors3 = []; p3.on('pageerror', e => errors3.push(e.message));
  await p3.goto(base + '/index.html'); await p3.waitForSelector('#stDrop'); await p3.setInputFiles('#stFile', memPath);
  await p3.waitForSelector('#stLoaded:not([hidden])', { timeout: 60000 });
  await p3.waitForFunction(() => document.querySelector('#updSince'), null, { timeout: 30000 });
  await p3.waitForTimeout(800);
  await p3.waitForFunction(d => document.querySelector('#updBody').textContent.includes('last full update searched up to ' + d), lastDay, { timeout: 15000 }).catch(() => {});
  const since3 = await p3.inputValue('#updSince');
  const expectSince = new Date(Date.parse(lastDay) - 7 * 864e5).toISOString().slice(0, 10);
  check('seeded memory: Since default = last searched_to minus 7 days', since3 === expectSince, since3 + ' vs ' + expectSince);
  check('seeded memory: the “last full update searched up to” line shows the run', (await p3.textContent('#updBody')).includes('last full update searched up to ' + lastDay), (await p3.textContent('#updBody')).slice(0, 600));
  await p3.click('#mgTabs [data-mg="log"]'); await p3.waitForTimeout(300);
  check('seeded memory: run log lists the earlier run', /Update database/.test(await p3.textContent('#mgOther')) && /Seeded story waiting for a save/.test(await p3.textContent('#mgOther')), (await p3.textContent('#mgOther')).slice(0, 300));
  check('seeded run is not packed (only runs made after loading)', await p3.evaluate(() => window.__station.pending().runs.length === 0));
  check('no page errors (seeded page)', errors3.length === 0, errors3.join('|'));
  await p3.screenshot({ path: path.join(OUT, 'shot_5_log.png'), fullPage: true });

  fs.writeFileSync(path.join(OUT, 'results_' + DBMODE + '.json'), JSON.stringify({ today: TODAY, zip: dl.name, results }, null, 1));
  check('still no request left the machine, whole run', outside.length === 0, outside.join(' '));
  /* age warning: a file 8 days old warns in plain words, 7 days does not, a file with no date warns; the gate opens either way */
  for (const [days, warn] of [[8, true], [7, false], [null, true]]) {
    const old = JSON.parse(JSON.stringify(Object.assign({}, fu, { memory: fu.memory }))); if (days === null) delete old.created_at; else old.created_at = new Date(Date.now() - days * 864e5 - 3600e3).toISOString();
    const f = path.join(OUT, 'aged_' + days + '.json'); fs.writeFileSync(f, JSON.stringify(old));
    const pa = await ctx.newPage(); await pa.goto(base + '/index.html'); await pa.waitForSelector('#stDrop'); await pa.setInputFiles('#stFile', f); await pa.waitForSelector('#stLoaded:not([hidden])', { timeout: 60000 });
    const t = await pa.textContent('#stAge'), has = /make a fresh one from the PC tracker so stories saved since are not found again/.test(t);
    check('age line for a file ' + (days === null ? 'with no date' : days + ' days old') + (warn ? ' warns' : ' does not warn'), has === warn && (days === null || new RegExp(days + ' days old').test(t)) && (await pa.locator('#stAge.err').count() === (warn ? 1 : 0)), t);
    check('the gate opens for that file too', !(await pa.$eval('#nbFile', i => i.disabled)));
    await pa.close();
  }
  await browser.close(); server.close();
  console.log(`\n${results.length - failed} of ${results.length} checks passed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('TEST CRASH', e); process.exit(2); });
