/* Drives the Update station page with a stubbed window.claude through one whole use, for the chain check:
     node station_drive.js --page FILE --file FOR_UPDATE.json --inputs DIR(nb.pdf, pq.pdf) --out DIR [--wrap auto|yes|no]
   Writes OUT/station_results.json ({checks:[{step,name,ok,extra}], zip, facts}) and the downloaded update zip (OUT/<name>.zip).
   Everything is local: the page is served from 127.0.0.1 inside the skeleton the Artifact tool adds (unless the file is already a whole page, as a
   copy of the PUBLISHED page is), TinyFish and Claude are canned. Nothing leaves the machine (every other host is refused and recorded). */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/opt/node-tools/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const MANUAL = arg('mode') === 'manual';   // default: automatic mode on, as a person finds it (AUTOSTATION-v1)
const PAGE = arg('page'), FILE = arg('file'), IN = arg('inputs'), OUT = arg('out'), WRAP = arg('wrap') || 'auto';
fs.mkdirSync(OUT, { recursive: true });
const checks = []; let curStep = '';
const check = (name, ok, extra) => { checks.push({ step: curStep, name, ok: !!ok, extra: ok ? '' : (extra === undefined ? '' : String(extra).slice(0, 700)) }); console.log((ok ? 'PASS ' : 'FAIL ') + curStep + ': ' + name + (!ok && extra !== undefined ? '  -> ' + String(extra).slice(0, 300) : '')); };
const laDay = (d = new Date()) => d.toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' });
const dayAgo = n => laDay(new Date(Date.now() - n * 864e5));
const fu = JSON.parse(fs.readFileSync(FILE, 'utf8'));
const plan = JSON.parse(fs.readFileSync(path.join(IN, 'plan.json'), 'utf8'));

/* what the tracker already has: one story whose link a search hit repeats (must not come back), one whose headline a wire copy repeats (reprint candidate) */
const good = s => s.rep === 0 && s.link && /^https?:/.test(s.link) && s.hl && s.hl.length >= 40 && s.hl.length <= 130 && !/["“”]/.test(s.hl) && s.date >= '2026-09-01' && s.media !== 'TV' && !/newsbank/i.test(s.link);
const pool = fu.stories.filter(good).sort((a, b) => a.date < b.date ? 1 : -1);
const exist2 = fu.stories.find(s => s.id === plan.rep.id), exist1 = pool.find(s => s.id !== exist2.id && s.outlet !== exist2.outlet);
const W = [
  { k: 'web1', url: 'https://www.valleygazette-test.com/2026/11/gabriel-quokka-permits-ccmarkweb1', title: 'Gabriel unveils bill to speed quokka habitat permits chaincheck', date: dayAgo(2), author: 'Dana Whitfield', outlet: 'Valley Gazette', topic: 'Energy / environment', tone: 'Positive', mark: 'ccmarkweb1' },
  { k: 'web2', url: 'https://www.diariotest.example/2026/11/gabriel-ley-vivienda-ccmarkweb2', title: 'Gabriel presenta ley de vivienda para el Valle chaincheck', date: dayAgo(1), author: '', outlet: 'Diario Test', topic: 'Housing / homelessness', tone: 'Neutral', mark: 'ccmarkweb2', es: true },
];
const REP = { url: 'https://www.reprintweekly-test.com/2026/11/chaincheck-repeat-ccmarkrep1', title: exist2.hl, date: dayAgo(1), mark: 'ccmarkrep1' };
const YT = { id: 'CCCCCCCCCCC', title: 'Jesse Gabriel on wildfire insurance chaincheck', date: dayAgo(1), channel: ['KTLA 5', 'https://www.youtube.com/@KTLA'] };
YT.url = 'https://www.youtube.com/watch?v=' + YT.id;
const SENT = ['The measure goes to committee next month, lawmakers said.', 'Regional air districts would have to publish their schedules online.', 'Environmental groups praised the proposal at a hearing on Tuesday.', 'Business leaders asked for more time to review the costs involved.', 'Staff estimate the program would cost about two million dollars a year.', 'Residents of the San Fernando Valley have waited years for answers.', 'A similar bill stalled in the Senate last session after a close vote.', 'The author said he expects amendments before the final floor vote.', 'Opponents argued the deadlines were too tight for smaller districts.', 'The committee chair promised a full hearing early in the new year.', 'County officials said they were still reading the language of the bill.', 'The governor has not said whether he would sign such a measure.'];
const SENT_ES = ['La propuesta pasará al comité de la Asamblea el próximo mes, dijeron los legisladores.', 'Los distritos regionales tendrían que publicar sus calendarios en línea.', 'Grupos ambientalistas elogiaron la propuesta en una audiencia el martes.', 'Líderes empresariales pidieron más tiempo para revisar los costos.', 'Residentes del Valle de San Fernando han esperado años por respuestas.', 'Un proyecto similar se estancó en el Senado la sesión pasada tras una votación reñida.', 'El autor dijo que espera enmiendas antes de la votación final.', 'Los opositores dijeron que los plazos eran demasiado cortos para los distritos pequeños.', 'El presidente del comité prometió una audiencia completa a principios del año.', 'Funcionarios del condado dijeron que aún leían el texto del proyecto.'];
const body = a => `Assemblymember Jesse Gabriel (D-Encino) ${a.es ? 'presentó una ley de vivienda en Sacramento, California, para el Valle de San Fernando. ' : 'introduced a bill in Sacramento that would speed permits across California. '}${a.mark} ` + (a.es ? SENT_ES : SENT).join(' ');
const PAGES = {};
W.forEach(a => { PAGES[a.url] = { title: a.title, html: `<html><head><title>${a.title}</title></head><body><article><h1>${a.title}</h1><p>${body(a)}</p></article></body></html>`, author: a.author }; });
PAGES[REP.url] = { title: REP.title, html: `<html><body><article><h1>${REP.title}</h1><p>${plan.rep.text} ${REP.mark}</p></article></body></html>`, author: 'Wire Desk' };
const ytDate = new Date(Date.parse(YT.date + 'T12:00:00Z')).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
PAGES[YT.url] = { title: YT.title, html: `<html><body><h1>${YT.title}</h1><p>Date</p><p>${ytDate}</p><yt-attributed-string>Assemblymember Jesse Gabriel (D-Encino) talks California wildfire insurance in this segment. ${SENT.join(' ')} ${SENT_ES.join(' ')}</yt-attributed-string></body></html>` };
const HITS = [
  ...W.map(a => ({ url: a.url, title: a.title, date: a.date, snippet: 'Assemblymember Jesse Gabriel (D-Encino) California bill.', site_name: a.outlet })),
  { url: exist1.link, title: exist1.hl, date: exist1.date, snippet: 'Jesse Gabriel California.', site_name: exist1.outlet },
  { url: REP.url, title: REP.title, date: REP.date, snippet: 'Assemblymember Jesse Gabriel (D-Encino) California.', site_name: 'Reprint Weekly' },
];
const YT_HITS = [{ url: YT.url, title: YT.title, date: YT.date, snippet: 'Assemblymember Jesse Gabriel (D-Encino) California.', site_name: 'YouTube' }];
const base = o => Object.assign({ keep: true, why: 'Names him.', topic: 'Budget / finance', media: 'Online news', role: 'Named in headline', tone: 'Neutral', twhy: 'Straight news.', author: '', lang: '', hl_en: '', text_en: '', press_release: 'no', pr_why: 'a reporter’s own story' }, o);
const CLASSIFY = {};
W.forEach(a => { CLASSIFY[a.url] = base({ date: a.date, outlet: a.outlet, pub: a.outlet, hl: a.title, topic: a.topic, tone: a.tone, author: a.es ? 'María López; Juan Pérez' : '', lang: a.es ? 'Spanish' : '', hl_en: a.es ? 'Gabriel presents housing bill for the Valley' : '', text_en: a.es ? 'Assemblymember Jesse Gabriel presented a housing bill in Sacramento.' : '' }); });
CLASSIFY[REP.url] = base({ date: REP.date, outlet: 'Reprint Weekly', pub: 'Reprint Weekly', hl: REP.title, topic: 'Other / roundup', role: 'Mentioned in story' });
CLASSIFY[YT.url] = base({ date: YT.date, outlet: 'KTLA', pub: 'KTLA', hl: YT.title, topic: 'Insurance' });

/* ---- local server ---- */
let html = fs.readFileSync(PAGE, 'utf8');
const whole = /^\s*<!doctype html|^\s*<html/i.test(html);
const wrap = WRAP === 'yes' || (WRAP === 'auto' && !whole);
if (wrap) {
  const vd = path.join(__dirname, '..', 'vendor'), live = fs.readdirSync(vd).filter(d => d.startsWith('live_')).sort().pop();
  const head = fs.readFileSync(path.join(vd, live, 'pipeline', 'shell.html'), 'utf8'); html = head.slice(0, head.indexOf('<body>') + 6).replace(/<link rel="(?:preconnect|stylesheet)"[^>]*fonts\.g[^>]*>\s*/g, '') + html + '</body></html>';
}
const server = http.createServer((req, res) => { if (req.url.split('?')[0] === '/index.html' || req.url === '/') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); res.end(html); } else { res.writeHead(404); res.end('no'); } });

const INIT = ({ hits, yt, pages, classify, ch }) => {
  const st = window.setTimeout.bind(window);
  window.setTimeout = (f, d, ...a) => st(f, d >= 300 ? Math.max(1, d / 100) : d, ...a);   // the 2.1 s TinyFish throttle, compressed
  const realNow = Date.now.bind(Date), t0 = realNow(); Date.now = () => t0 + (realNow() - t0) * 100;
  window.__calls = []; window.__dl = [];
  const load = () => { try { return JSON.parse(localStorage.getItem('__fakedb')) || {}; } catch (e) { return {}; } }, save = o => localStorage.setItem('__fakedb', JSON.stringify(o));
  Object.defineProperty(window, '__realdb', { get: () => load() });
  const fakeDb = { collection: n => ({ doc: id => ({ set: async d => { const o = load(); (o[n] = o[n] || {})[id] = JSON.parse(JSON.stringify(d)); save(o); }, delete: async () => {}, get: async () => { const d = (load()[n] || {})[id]; return { exists: !!d, data: () => d }; } }),
    get: async () => ({ docs: Object.entries(load()[n] || {}).map(([id, d]) => ({ id, data: () => d })) }), onSnapshot: cb => { cb({ docs: Object.entries(load()[n] || {}).map(([id, d]) => ({ id, data: () => d })) }); return () => {}; } }) };
  const mcp = { callTool: async (server, tool, input) => {
    window.__calls.push({ tool, q: input.query || '', inc: String(input.include_domains || ''), urls: input.urls || [] });
    if (tool === 'search') { const q = String(input.query || '');
      if (/youtube/.test(String(input.include_domains || ''))) return { payload: { results: /^"Jesse Gabriel"$/.test(q) ? yt : [] } };
      return { payload: { results: /^"Jesse Gabriel"$/.test(q) ? hits : [] } }; }
    if (tool === 'fetch_content') {
      const results = []; for (const u of (input.urls || [])) {
        if (/youtube\.com\/oembed/.test(u)) { const id = new URL(u).searchParams.get('url').split('v=')[1]; const c = ch[id]; if (c) results.push({ url: u, final_url: u, title: '', text: JSON.stringify({ title: 'x', author_name: c[0], author_url: c[1], type: 'video' }) }); }
        else if (pages[u]) results.push({ url: u, final_url: u, title: pages[u].title, text: pages[u].html, author: pages[u].author || '', published_date: '' });
      }
      return { payload: { results, errors: [] } }; }
    return { payload: {} };
  } };
  const sample = async () => ({ text: '', truncated: false });
  sample.json = async prompt => {
    prompt = String(prompt); window.__calls.push({ tool: 'sample', q: prompt.slice(0, 40) });
    if (/^You screen web search results/.test(prompt)) { const n = (prompt.match(/^=== \d+$/gm) || []).length; return Array.from({ length: n }, (_, i) => ({ n: i + 1, keep: true, why: 'names him' })); }
    if (/^You are screening web search results/.test(prompt)) { const items = [...prompt.matchAll(/=== ITEM (\d+)\nURL: (\S+)/g)]; return items.map(m => Object.assign({ n: +m[1] }, classify[m[2]] || { keep: false, why: 'unknown in test' })); }
    const generic = (n, t) => ({ n, keep: true, why: 'Names the Assemblymember.', date: '', outlet: '', pub: '', hl: t, topic: 'Budget / finance', media: 'Newspaper', role: 'Mentioned in story', tone: 'Neutral', twhy: 'Straight news.', author: '', lang: '', hl_en: '', text_en: '', press_release: 'no', pr_why: 'a reporter’s own story' });
    if (/^These items come from NewsBank/.test(prompt) || /^These items are ProQuest article PDFs/.test(prompt)) return [...prompt.matchAll(/=== ITEM (\d+)\nURL: (\S+)\nPage title: (.*)\n/g)].map(m => generic(+m[1], m[3]));
    if (/^Translate each news headline/.test(prompt)) return [...prompt.matchAll(/id=(\S+) \((\w+),/g)].map(m => ({ id: m[1], hl: 'Gabriel presents a bill (translated)' }));
    return [];
  };
  window.claude = { use: async name => name === 'db' ? fakeDb : name === 'mcp' ? mcp : name === 'sample' ? sample
    : name === 'downloads' ? { save: async ({ filename, data }) => { const buf = new Uint8Array(await data.arrayBuffer()); window.__dl.push({ filename, size: buf.length }); window.__lastDl = buf; } } : null };
};

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1300, height: 1100 }, acceptDownloads: true });
  if (MANUAL) await ctx.addInitScript(() => { try { localStorage.setItem('ajg_station_auto', '0'); } catch (e) {} });
  await ctx.addInitScript(INIT, { hits: HITS, yt: YT_HITS, pages: PAGES, classify: CLASSIFY, ch: { [YT.id]: YT.channel } });
  const outside = []; await ctx.route(u => !/^(http:\/\/127\.0\.0\.1[:/]|data:|blob:|about:)/.test(u.href), r => { outside.push(r.request().url()); r.abort(); });
  const page = await ctx.newPage(); const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message)); page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  const res = { checks, zip: null, facts: {}, stories: { exist1: exist1.id, exist2: exist2.id }, wrapped: wrap };
  const finish = async (code) => { res.errors = errors; res.outside = outside; fs.writeFileSync(path.join(OUT, 'station_results.json'), JSON.stringify(res, null, 1)); await browser.close(); server.close(); process.exit(code); };
  try {
    /* ---- step 2: the station takes the PC's file ---- */
    curStep = '2 station loads the file';
    await page.goto(base + '/index.html'); await page.waitForSelector('#stDrop', { timeout: 60000 });
    check('station page starts, Update button off before a file', await page.$eval('#runFind', b => b.disabled));
    await page.setInputFiles('#stFile', FILE);
    await page.waitForSelector('#stLoaded:not([hidden])', { timeout: 120000 }).catch(() => {});
    const err = (await page.locator('#stErr:not([hidden])').count()) ? await page.textContent('#stErr') : '';
    check('format version accepted (no refusal message)', !err && await page.locator('#stLoaded:not([hidden])').count() === 1, err);
    const facts = await page.textContent('#stFacts').catch(() => ''); res.facts.facts = facts;
    check('workbook fingerprint shown (first 8)', facts.includes(fu.fingerprint.workbook_sha256.slice(0, 8)), facts);
    check('story count shown', facts.includes(fu.stories.length.toLocaleString('en-US')), facts);
    const ageTxt = await page.textContent('#stAge').catch(() => ''); res.facts.age = ageTxt;
    check('a fresh file: made today, no age warning', /today|0 days/.test(ageTxt) && !/more than 7 days old|no date/i.test(ageTxt), ageTxt);
    check('Update button and both PDF boxes open after loading', !(await page.$eval('#runFind', b => b.disabled)) && !(await page.$eval('#nbFile', i => i.disabled)) && !(await page.$eval('#pqFile', i => i.disabled)));
    await page.waitForFunction(() => document.querySelector('#updGo'), null, { timeout: 30000 });

    /* ---- step 3a: the stubbed Update ---- */
    curStep = '3 stubbed Update';
    await page.click('#runFind'); await page.waitForSelector('#rcScrim:not([hidden])'); await page.click('#rcYes');
    await page.waitForFunction(() => { const f = document.querySelector('#updBody'); return f && (document.querySelector('#updAdd') || /Added|Nothing new|Stopped|nothing/i.test(f.textContent)) && !document.querySelector('#updStop'); }, null, { timeout: 300000 });
    const nSearch = await page.evaluate(() => window.__calls.filter(c => c.tool === 'search').length);
    check('the run searched (many TinyFish searches, YouTube station search included)', nSearch > 50 && await page.evaluate(() => window.__calls.some(c => c.tool === 'search' && /youtube/.test(c.inc))), nSearch);
    for (let k = 0; k < 4; k++) { if (await page.locator('#updAdd').count() && !(await page.$eval('#updAdd', b => b.disabled))) { await page.click('#updAdd'); await page.waitForTimeout(1500); } }
    await page.waitForFunction(() => window.__station.sess.runs.size > 0, null, { timeout: 30000 });
    await page.waitForTimeout(1500);
    const S = await page.evaluate(() => { const o = {}; for (const [c, m] of Object.entries(window.__station.sess)) o[c] = [...m].map(([id, v]) => [id, v.data]); return o; });
    fs.writeFileSync(path.join(OUT, 'session_docs.json'), JSON.stringify(S, null, 1));
    const run = S.runs[0] && S.runs[0][1], rows = (run && run.rows) || [];
    check('a finished run doc was made', run && run.status === 'done', run && run.status);
    const byLink = u => rows.filter(r => r['Publisher link'] === u || r['YouTube link'] === u);
    check('2 new web stories (English + Spanish) proposed as Originals', W.every(a => byLink(a.url).some(r => r['Original or reprint'] === 'Original')), JSON.stringify(rows.map(r => [r['Original or reprint'], r['Outlet']])));
    check('the hit whose link the tracker already has was not added', !rows.some(r => r['Publisher link'] === exist1.link) && !JSON.stringify(S.pages || []).includes(exist1.link), exist1.link);
    const rp = (S.reprints[0] || [])[1];
    check('one reprint candidate, recorded against the story the tracker already has', S.reprints.length === 1 && rp && rp.story === exist2.id && rp.link === REP.url, JSON.stringify(S.reprints).slice(0, 300) + ' want ' + exist2.id);
    const yrow = byLink(YT.url)[0];
    check('the YouTube station clip is a new Broadcast segment story (KTLA)', !!yrow && yrow['Format'] === 'Broadcast segment' && yrow['Outlet'] === 'KTLA', JSON.stringify(yrow));
    check('Spanish find: translation and author docs made', S.translations.length >= 1 && S.authors.length >= 1, JSON.stringify([S.translations.length, S.authors.length]));
    const tones = rows.filter(r => r['Original or reprint'] === 'Original').map(r => r['Tone']);
    check('tone rated for the new finds', tones.length >= 3 && tones.every(Boolean), JSON.stringify(tones));

    /* ---- automatic mode: the folder downloads by itself once the web run is quiet; PDFs added AFTER that must still end in ONE complete folder ---- */
    if (!MANUAL) {
      curStep = '3 automatic download';
      await page.waitForFunction(() => window.__dl.length >= 1, null, { timeout: 60000 });
      const first = await page.evaluate(() => ({ name: window.__dl[0].filename, bytes: Array.from(window.__lastDl) }));
      fs.writeFileSync(path.join(OUT, first.name), Buffer.from(first.bytes)); res.zip_first = path.join(OUT, first.name);
      check('automatic mode: the update folder downloaded by itself after the web run (no button pressed)', /^ajg_update_/.test(first.name), first.name);
    }

    /* ---- step 3b: a NewsBank PDF, a ProQuest export ---- */
    curStep = '3 NewsBank PDF';
    await page.setInputFiles('#nbFile', path.join(IN, 'nb.pdf'));
    await page.waitForFunction(() => window.__station.state.nb.files.length === 1 && window.__station.state.nb.files[0].status !== 'reading' && !window.__station.state.nb.reading, null, { timeout: 180000 });
    const nbf = await page.evaluate(() => window.__station.state.nb.files.map(f => ({ status: f.status, note: f.note, stories: f.stories, warn: f.warn })));
    const nbi = await page.evaluate(() => window.__station.state.nb.items.map(it => ({ st: it.screen.status, why: it.screen.why, hl: it.p.headline, docref: it.p.docref, outlet: it.p.outlet_clean, date: it.p.date, pdf: it.pdf && it.pdf.bytes })));
    check('the real-layout PDF is read: 2 stories, no warnings', nbf[0].status === 'ok' && nbf[0].stories === 2 && !(nbf[0].warn || []).length, JSON.stringify(nbf));
    const inew = nbi.find(i => i.hl === plan.nb.new.hl), iknown = nbi.find(i => (i.docref || '').toUpperCase().endsWith(plan.nb.known.docref));
    check('the new NewsBank story is new, with its own cut PDF', inew && inew.st === 'new' && inew.pdf > 1000 && inew.date === plan.nb.new.date, JSON.stringify(inew));
    check('the story the tracker already has (same docref) is recognised and not added', iknown && iknown.st === 'known', JSON.stringify(iknown));
    if (MANUAL) await page.click('#nbAdd');   // automatic mode adds them by itself
    await page.waitForFunction(() => /Added:|Stopped/.test(document.querySelector('#nbProg').textContent), null, { timeout: 240000 });
    const nbp = await page.textContent('#nbProg'); res.facts.nb_prog = nbp;
    check('added to the update (1 story)', /Added:/.test(nbp) && !/Stopped/.test(nbp), nbp);

    curStep = '3 ProQuest export';
    await page.setInputFiles('#pqFile', path.join(IN, 'pq.pdf'));
    await page.waitForFunction(() => window.__station.state.pq.files.length === 1 && window.__station.state.pq.files[0].status !== 'reading' && !window.__station.state.pq.reading, null, { timeout: 180000 });
    const pqi = await page.evaluate(() => window.__station.state.pq.items.map(it => ({ st: it.screen.status, why: it.screen.why, hl: it.p.headline, docid: it.p.docid, date: it.p.date, pdf: it.pdf && it.pdf.bytes })));
    check('the export is read: 1 new article with its own PDF', pqi.length === 1 && pqi[0].st === 'new' && pqi[0].docid === plan.pq.docid && pqi[0].pdf > 1000, JSON.stringify(pqi));
    if (MANUAL) await page.click('#pqAdd');
    await page.waitForFunction(() => /Added:|Stopped/.test(document.querySelector('#pqProg').textContent), null, { timeout: 240000 });
    const pqp = await page.textContent('#pqProg'); res.facts.pq_prog = pqp;
    check('added to the update (1 story)', /Added:/.test(pqp) && !/Stopped/.test(pqp), pqp);

    /* ---- step 3c: the update folder ---- */
    curStep = '3 update folder (zip)';
    let status;
    if (MANUAL) {
      await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 20000 });
      status = await page.textContent('#stPackStatus'); res.facts.pack_status = status;
      await page.click('#stPack');
      await page.waitForFunction(() => window.__dl.length > 0, null, { timeout: 60000 });
    } else {
      await page.waitForFunction(() => window.__dl.length >= 2, null, { timeout: 90000 });   // the second, complete folder comes by itself
      await page.waitForTimeout(8000);   // and nothing more after it
      status = await page.textContent('#stPackStatus'); res.facts.pack_status = status + ' | ' + await page.textContent('#stPackNote');
      const nd = await page.evaluate(() => window.__dl.length);
      check('automatic mode: exactly two downloads (the early one, then one complete folder), the PDFs did not make a third', nd === 2, nd);
    }
    const dl = await page.evaluate(() => { const i = window.__dl.length - 1; return { name: window.__dl[i].filename, bytes: Array.from(window.__lastDl) }; });
    const zipPath = path.join(OUT, dl.name); fs.writeFileSync(zipPath, Buffer.from(dl.bytes)); res.zip = zipPath;
    check('the zip downloads, named with the workbook short sha', new RegExp('^ajg_update_\\d{8}-\\d{4}_' + fu.fingerprint.workbook_sha256.slice(0, 8) + '(_v\\d+)?\\.zip$').test(dl.name), dl.name);
    check('step 3 says what it holds (a run, a NewsBank PDF, a ProQuest PDF)', MANUAL ? (/NewsBank/.test(status) && /ProQuest/.test(status)) : /replaces ajg_update_/.test(res.facts.pack_status), status);
    check('no page error, nothing asked of any outside host', errors.length === 0 && outside.length === 0, errors.concat(outside).slice(0, 4).join(' | '));
    res.expect = { web: W.map(a => ({ hl: a.title, url: a.url, mark: a.mark })), rep: { url: REP.url, story: exist2.id, mark: REP.mark }, yt: { url: YT.url, hl: YT.title }, exist1: exist1.id };
    await finish(0);
  } catch (e) {
    check('driver ran to the end', false, String(e).slice(0, 500));
    res.crash_panel = await page.evaluate(() => document.body.innerText.slice(0, 1500)).catch(() => '');
    await finish(1);
  }
})().catch(e => { console.error(e); process.exit(2); });
