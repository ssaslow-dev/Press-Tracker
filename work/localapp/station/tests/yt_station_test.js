/* Playwright test for the Update station page (work/localapp/station). Run:
     node tests/station_test.js --page DIST/index.html --file FOR_UPDATE.json --out OUTDIR
   Everything is local: the page is served on 127.0.0.1 inside the same wrapper the Artifact tool adds, window.claude is a stub
   (db in memory, TinyFish search/fetch canned from three fake articles, sample canned), and the downloaded zip is written to OUTDIR. */
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page'), FILE0 = arg('file'), OUT = arg('out'), DBMODE = arg('db-mode') || 'empty';   // empty | stale (junk left by an earlier use) | none (no db capability)
fs.mkdirSync(OUT, { recursive: true });
const results = []; let failed = 0;
const check = (name, ok, extra) => { results.push({ name, ok: !!ok, extra: extra === undefined ? '' : String(extra) }); if (!ok) failed++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra !== undefined && !ok ? '  -> ' + extra : '')); };

const STRIP = process.argv.includes('--strip-recall');   // a file made before RECALLFIX-v1: the station's own default lists must stand in
const itunes = fs.readFileSync(path.join(__dirname, '..', '..', '..', '..', 'build', 'tests', 'recallfix', 'itunes_fixture.json'), 'utf8');
const laDay = (d = new Date()) => d.toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' });
const TODAY = laDay(), dayAgo = n => laDay(new Date(Date.now() - n * 864e5));
const fu = JSON.parse(fs.readFileSync(FILE0, 'utf8'));
// a tracked ABC10 story two days ago: the same-segment target for the YouTube clip
const ABC = { id: 's99001', code: 'jg-seg001', aid: '99001', date: dayAgo(2), prec: 'day', year: +dayAgo(2).slice(0, 4), outlet: 'ABC10', pub: 'ABC10', hl: 'Gabriel on the budget: ABC10 interview', link: 'https://www.abc10.com/article/news/politics/gabriel-budget-interview/test-seg', plink: 'https://www.abc10.com/article/news/politics/gabriel-budget-interview/test-seg', lstat: 'Publisher URL', media: 'TV', fmt: 'Web story', rep: 0, reps: [], also: '', lk: [], tone: 'Neutral', topic: 'Budget / finance' };
fu.stories.unshift(ABC);
if (STRIP) delete fu.fetchrules.recall;
const FILE = path.join(OUT, 'for_update_yt.json'); fs.writeFileSync(FILE, JSON.stringify(fu));
const V = { A: 'AAAAAAAAAAA', B: 'BBBBBBBBBBB', C: 'CCCCCCCCCCC', D: 'DDDDDDDDDDD' };
const yurl = id => 'https://www.youtube.com/watch?v=' + id;
const CH = { [V.A]: ['ABC10', 'https://www.youtube.com/@ABC10'], [V.B]: ['KTLA 5', 'https://www.youtube.com/@KTLA'], [V.C]: ['Random Political Blog', 'https://www.youtube.com/@randomblog'], [V.D]: ['KBS News', 'https://www.youtube.com/@newskbs'] };
const KTLA = { url: 'https://ktla.com/news/california/gabriel-test-priority-find/', title: 'Gabriel proposes new fire insurance rules', date: dayAgo(1) };
const POD = { url: 'https://podcasts.apple.com/us/podcast/the-capitol-test/id1234567890?i=1000700000001', title: 'Budget Chair Jesse Gabriel on the California budget', date: dayAgo(1) };
const body = (t, extra) => 'Assemblymember Jesse Gabriel (D-Encino) spoke about ' + t + ' in Sacramento on Friday. ' + (extra || 'Lawmakers said the budget would be debated next week in California. ').repeat(8);
const HITS = [
  { re: /site:ktla\.com/, hits: [{ url: KTLA.url, title: KTLA.title, date: KTLA.date, snippet: 'Assemblymember Jesse Gabriel (D-Encino) proposes fire insurance rules.', site_name: 'KTLA' }] },
  { re: /site:podcasts\.apple\.com/, hits: [{ url: POD.url, title: POD.title, date: POD.date, snippet: 'Budget Chair Jesse Gabriel joins the show.', site_name: 'The Capitol Test' }] },
];
const YT_HITS = [V.A, V.B, V.C, V.D].map((id, i) => ({ url: yurl(id), title: ['Assemblymember Jesse Gabriel on the budget (ABC10)', 'Jesse Gabriel on wildfire insurance', 'Jesse Gabriel is wrong about everything', 'Jesse Gabriel on the California budget (KBS News)'][i], date: dayAgo(i === 0 ? 2 : 1), snippet: 'Assemblymember Jesse Gabriel (D-Encino) California.', site_name: 'YouTube' }));
const CLASSIFY = {};
const base = (o) => Object.assign({ keep: true, why: 'Names him.', topic: 'Budget / finance', media: 'Online news', role: 'Named in headline', tone: 'Neutral', twhy: 'Straight news.', author: '', lang: '', hl_en: '', text_en: '' }, o);
CLASSIFY[KTLA.url] = base({ date: KTLA.date, outlet: 'KTLA', pub: 'KTLA', hl: KTLA.title, topic: 'Insurance' });
CLASSIFY[POD.url] = base({ date: POD.date, outlet: 'The Capitol Test', pub: 'The Capitol Test', hl: POD.title });
CLASSIFY[yurl(V.A)] = base({ date: dayAgo(2), outlet: 'ABC10', pub: 'ABC10', hl: YT_HITS[0].title });
CLASSIFY[yurl(V.B)] = base({ date: dayAgo(1), outlet: 'KTLA', pub: 'KTLA', hl: YT_HITS[1].title, topic: 'Insurance' });
CLASSIFY[yurl(V.D)] = base({ date: dayAgo(1), outlet: 'KBS News', pub: 'KBS News', hl: YT_HITS[3].title });
CLASSIFY[yurl(V.C)] = base({ date: dayAgo(1), outlet: 'Random Political Blog', pub: 'Random Political Blog', hl: YT_HITS[2].title });
const ytPage = (id) => '<html><body><h1>' + YT_HITS.find(h => h.url.endsWith(id)).title + '</h1><p>Date</p><p>' + new Date(Date.parse(YT_HITS.find(h => h.url.endsWith(id)).date + 'T12:00:00Z')).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }) + '</p><yt-attributed-string>Assemblymember Jesse Gabriel (D-Encino) talks California budget.</yt-attributed-string></body></html>';
const PAGES = {};
[KTLA, POD].forEach(a => { PAGES[a.url] = { title: a.title, html: '<html><head><title>' + a.title + '</title></head><body><article><h1>' + a.title + '</h1><p>' + body(a.title) + '</p></article></body></html>' }; });
[V.A, V.B, V.C, V.D].forEach(id => { PAGES[yurl(id)] = { title: YT_HITS.find(h => h.url.endsWith(id)).title, html: ytPage(id) }; });
/* ---- local server: the page inside the skeleton the Artifact tool adds; the for-Update file; nothing else ---- */
const shellHead = (() => { const s = fs.readFileSync(path.join(__dirname, '..', '..', 'vendor', fs.readdirSync(path.join(__dirname, '..', '..', 'vendor')).filter(d => d.startsWith('live_')).sort().pop(), 'pipeline', 'shell.html'), 'utf8'); return s.slice(0, s.indexOf('<body>') + 6).replace(/<link rel="(?:preconnect|stylesheet)"[^>]*fonts\.g[^>]*>\s*/g, ''); })();   // the Artifact tool's skeleton has no font links; the vendor head's Google links are not part of the page under test
const wrapped = shellHead + fs.readFileSync(PAGE, 'utf8') + '</body></html>';
const server = http.createServer((req, res) => {
  if (req.url.split('?')[0] === '/index.html' || req.url === '/') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); res.end(wrapped); }
  else if (req.url === '/for_update.json') { res.writeHead(200, { 'Content-Type': 'application/json' }); fs.createReadStream(FILE).pipe(res); }
  else { res.writeHead(404); res.end('no'); }
});

const INIT = ({ hits, yt, pages, classify, itunes, ch }) => {
  const st = window.setTimeout.bind(window);
  window.setTimeout = (f, d, ...a) => st(f, d >= 300 ? Math.max(1, d / 100) : d, ...a);
  const realNow = Date.now.bind(Date), t0 = realNow(); Date.now = () => t0 + (realNow() - t0) * 100;
  window.__calls = []; window.__dl = [];
  const store = {};
  const fakeDb = { collection: n => ({ doc: id => ({ set: async d => { (store[n] = store[n] || {})[id] = JSON.parse(JSON.stringify(d)); }, delete: async () => {}, get: async () => ({ exists: false, data: () => null }) }),
    get: async () => ({ docs: [] }), onSnapshot: cb => { cb({ docs: [] }); return () => {}; } }) };
  const mcp = { callTool: async (server, tool, input) => {
    window.__calls.push({ tool, q: input.query || '', inc: input.include_domains || '', urls: input.urls || [], after: input.after_date || '' });
    if (tool === 'search') { const q = String(input.query || ''); let res = [];
      if (/youtube/.test(String(input.include_domains || ''))) res = /^"Jesse Gabriel"$/.test(q) ? yt : [];
      else for (const h of hits) if (new RegExp(h.re.source).test(q)) res = res.concat(h.hits);
      return { payload: { results: res } }; }
    if (tool === 'fetch_content') {
      const results = []; for (const u of (input.urls || [])) {
        if (/youtube\.com\/oembed/.test(u)) { const id = new URL(u).searchParams.get('url').split('v=')[1]; const c = ch[id]; if (c) results.push({ url: u, final_url: u, title: '', text: JSON.stringify({ title: 'x', author_name: c[0], author_url: c[1], type: 'video' }) }); }
        else if (/itunes\.apple\.com\/search/.test(u)) results.push({ url: u, final_url: u, title: '', text: itunes });
        else if (pages[u]) results.push({ url: u, final_url: u, title: pages[u].title, text: pages[u].html, author: '', published_date: '' });
      }
      return { payload: { results, errors: [] } }; }
    return { payload: {} };
  } };
  const sample = async () => ({ text: '', truncated: false });
  sample.json = async (prompt) => {
    if (/^You screen web search results/.test(prompt)) { const n = (prompt.match(/^=== \d+$/gm) || []).length; return Array.from({ length: n }, (_, i) => ({ n: i + 1, keep: true, why: 'names him' })); }
    if (/^You are screening web search results/.test(prompt)) { const items = [...prompt.matchAll(/=== ITEM (\d+)\nURL: (\S+)/g)]; return items.map(m => Object.assign({ n: +m[1] }, classify[m[2]] || { keep: false, why: 'unknown in test' })); }
    return [];
  };
  window.claude = { use: async name => name === 'db' ? fakeDb : name === 'mcp' ? mcp : name === 'sample' ? sample
    : name === 'downloads' ? { save: async ({ filename, data }) => { const buf = new Uint8Array(await data.arrayBuffer()); window.__dl.push({ filename, size: buf.length }); window.__lastDl = buf; } } : null };
};

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1200, height: 1000 }, acceptDownloads: true });
  await ctx.addInitScript(INIT, { hits: HITS.map(h => ({ re: { source: h.re.source }, hits: h.hits })), yt: YT_HITS, pages: PAGES, classify: CLASSIFY, itunes, ch: CH });
  const page = await ctx.newPage(); const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message)); page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto(base + '/index.html'); await page.waitForSelector('#stDrop');
  await page.setInputFiles('#stFile', FILE); await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 60000 });
  await page.waitForFunction(() => document.querySelector('#updGo'), null, { timeout: 30000 });
  const rc = await page.evaluate(() => { try { const b = JSON.parse(document.getElementById('fetchrules').textContent); return { has: !!b.recall, pri: ((b.recall.priority || {}).groups || []).length, yt: Object.keys(((b.recall.youtube || {}).channels) || {}).length, ems: (((b.recall.ethnic || {}).outlets) || []).length }; } catch (e) { return { err: String(e) }; } });
  check(STRIP ? 'file without a recall block: the station supplies its default lists (priority groups, YouTube channels, ethnic outlets)' : 'the recall block in the file reaches the tracker code', rc.has && rc.pri === 7 && rc.yt >= 30 && rc.ems > 100, JSON.stringify(rc));
  check('station states when it used its own default lists', STRIP === await page.evaluate(() => !!window.__station.state.recallDefault || !!(window.__station.recallDefault)), '');
  await page.click('#runFind'); await page.waitForSelector('#rcScrim:not([hidden])'); await page.click('#rcYes');
  await page.waitForFunction(() => { const f = document.querySelector('#updBody'); return f && (document.querySelector('#updAdd') || /Added|Nothing new|Stopped|nothing/i.test(f.textContent)) && !document.querySelector('#updStop'); }, null, { timeout: 240000 });
  const calls = await page.evaluate(() => window.__calls);
  const S_ = calls.filter(c => c.tool === 'search');
  check('priority-outlet searches ran (LA TV and radio, Valley weeklies, podcast sites) with a date filter (the podcast-page group without one: DATEFILTER-v1)', ['site:ktla.com', 'site:valleynewsgroup.com'].every(s => S_.some(c => c.q.includes(s) && c.after)) && S_.some(c => c.q.includes('site:open.spotify.com/episode') && !c.after), JSON.stringify(S_.filter(c => /podcasts\.apple|valleynews/.test(c.q)).map(c => c.q)));
  const has = (re, pred) => S_.some(c => re.test(c.q) && (!pred || pred(c)));
  check('LANGCAP-v1: Chinese-language press search sent with the native-script query and a date', has(/加布里埃爾/, c => /site:worldjournal\.com/.test(c.q) && /singtaousa\.com/.test(c.q) && c.after) && has(/加布里埃尔/), JSON.stringify(S_.filter(c => /加布/.test(c.q)).map(c => [c.q, c.after])));
  check('LANGCAP-v1: Korean search "제시 가브리엘" sent with a date', has(/"제시 가브리엘"/, c => /koreadaily|koreatimes/.test(c.q) && c.after), JSON.stringify(S_.filter(c => /가브리엘/.test(c.q)).map(c => [c.q, c.after])));
  check("LANGCAP-v1: Hebrew search \"ג'סי גבריאל\" sent with a date", has(/ג'סי גבריאל/, c => /hebrewnews/.test(c.q) && c.after), JSON.stringify(S_.filter(c => /גבריאל/.test(c.q)).map(c => [c.q, c.after])));
  check('LANGCAP-v1: Armenian-press search ("Jesse Gabriel", Asbarez, Massis Post, Mirror-Spectator) sent with a date', has(/"Jesse Gabriel"/, c => /asbarez/.test(c.q) && /massispost/.test(c.q) && /mirrorspectator/.test(c.q) && c.after), JSON.stringify(S_.filter(c => /asbarez/.test(c.q)).map(c => [c.q, c.after])));
  check('DATEFILTER-v1: the podcast-page group is sent without after_date', S_.filter(c => /site:open\.spotify\.com\/episode/.test(c.q)).length === 1 && S_.filter(c => /site:open\.spotify\.com\/episode/.test(c.q)).every(c => !c.after), JSON.stringify(S_.filter(c => /spotify/.test(c.q)).map(c => [c.q, c.after])));
  const Y = S_.filter(c => /youtube/.test(c.inc));
  check('exactly two station YouTube searches, include_domains youtube.com, with the date filter', Y.length === 2 && Y.every(c => c.after), JSON.stringify(Y));
  const oe = calls.filter(c => c.tool === 'fetch_content' && c.urls.some(u => /youtube\.com\/oembed/.test(u)));
  check('channels read through oEmbed (fetch_content, batched)', oe.length >= 1 && oe[0].urls.length === 4, JSON.stringify(oe.map(c => c.urls.length)));
  check('the iTunes podcast pass ran through fetch_content', calls.some(c => c.tool === 'fetch_content' && c.urls.some(u => /itunes\.apple\.com\/search/.test(u))));
  const ytOpened = calls.filter(c => c.tool === 'fetch_content' && c.urls.some(u => /youtube\.com\/watch/.test(u))).flatMap(c => c.urls);
  check('the other uploader\'s video (not a station channel) was never opened', !ytOpened.includes(yurl(V.C)), JSON.stringify(ytOpened));
  for (let k = 0; k < 3; k++) { if (await page.locator('#updAdd').count() && !(await page.$eval('#updAdd', b => b.disabled))) { await page.click('#updAdd'); await page.waitForTimeout(1500); } }
  await page.waitForFunction(() => window.__station.sess.runs.size > 0, null, { timeout: 30000 });
  await page.waitForTimeout(1500);
  const S = await page.evaluate(() => { const o = {}; for (const [c, m] of Object.entries(window.__station.sess)) o[c] = [...m].map(([id, v]) => [id, v.data]); return o; });
  fs.writeFileSync(path.join(OUT, 'session_docs.json'), JSON.stringify(S, null, 1));
  const run = S.runs[0][1];
  const rows = run.rows || [];
  const byLink = u => rows.filter(r => r['Publisher link'] === u || r['YouTube link'] === u);
  check('run doc has an attach list with the clip for the tracked ABC10 story', Array.isArray(run.attach) && run.attach.length === 1 && run.attach[0].link === yurl(V.A) && run.attach[0].row_link === ABC.link && run.attach[0].channel === 'ABC10' && run.attach[0].station === 'KXTV', JSON.stringify(run.attach));
  check('the blog video produced no story and no attach', !JSON.stringify(S).includes(V.C), '');
  check('the attached clip is not also a new story', byLink(yurl(V.A)).length === 0);
  const ytRowB = byLink(yurl(V.B))[0];
  check('KTLA clip is a new Broadcast segment story (Medium TV, outlet KTLA, source YouTube station channel)', !!ytRowB && ytRowB['Format'] === 'Broadcast segment' && ytRowB['Medium'] === 'TV' && ytRowB['Outlet'] === 'KTLA' && /YouTube station channel/.test(ytRowB['Data Source'] || ''), JSON.stringify(ytRowB));
  const ytRowD = byLink(yurl(V.D))[0];
  check('KBS News YouTube clip is kept as a station clip (Broadcast segment, Medium TV, outlet KBS News, source YouTube station channel)', !!ytRowD && ytRowD['Format'] === 'Broadcast segment' && ytRowD['Medium'] === 'TV' && ytRowD['Outlet'] === 'KBS News' && /YouTube station channel/.test(ytRowD['Data Source'] || ''), JSON.stringify(ytRowD));
  const av = rows.filter(r => r._av || r.av);
  check('the zip row for the new clip carries its Audio & video details (_av: Channel KTLA 5, Station KTLA)', !!(ytRowB && ytRowB._av && ytRowB._av.Channel === 'KTLA 5' && ytRowB._av.Station === 'KTLA' && ytRowB._av['YouTube link'] === yurl(V.B)), JSON.stringify(ytRowB && ytRowB._av));
  check('priority-search find (KTLA site) was added as a story', rows.some(r => r['Publisher link'] === KTLA.url), '');
  check('podcast-site find was added with the show (not the platform) as outlet', rows.some(r => r['Publisher link'] === POD.url && /Capitol Test/.test(r['Outlet'])), JSON.stringify(rows.filter(r => r['Publisher link'] === POD.url)));
  await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 10000 });
  await page.click('#stPack'); await page.waitForFunction(() => window.__dl.length > 0, null, { timeout: 30000 });
  const dl = await page.evaluate(() => ({ name: window.__dl[0].filename, bytes: Array.from(window.__lastDl) }));
  fs.writeFileSync(path.join(OUT, 'yt_update.zip'), Buffer.from(dl.bytes));
  check('zip downloaded', /^ajg_update_\d{8}-\d{4}_[0-9a-f]{8}\.zip$/.test(dl.name), dl.name);
  check('no page errors', errors.length === 0, errors.slice(0, 5).join(' | '));
  console.log(failed ? failed + ' FAILED' : 'all passed'); console.log(results.filter(r => r.ok).length + ' of ' + results.length + ' checks passed');
  await browser.close(); server.close(); process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
