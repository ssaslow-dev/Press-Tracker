// SAMELOOK-v2 function parity: drive the same interactions on the live tracker's own files (reference) and on the PC page, compare the outcomes.
//   node parity.js --ref http://127.0.0.1:8801/index.html --pc http://127.0.0.1:8803/ --out DIR [--vp 1440x900] [--only a,b]
// Outcomes are counts, id lists, texts, URLs, hashes of downloaded bytes. A step that differs is printed with both values; the exit code is the number of differences.
// The reference has no window.claude (it is plain static files here), so it gets a small in-memory stand-in with the same db and downloads calls as the PC's
// local runtime (server/claude_shim.js): without it the reference page would keep notes and views in localStorage and word its messages differently.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/opt/node-tools/node_modules/playwright');
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const REF = arg('ref'), PC = arg('pc'), OUT = arg('out'), VP = arg('vp', '1440x900'), ONLY = arg('only', '');
const [VW, VH] = VP.split('x').map(Number);
const EXTRA = arg('extra', ''), ALLOW = arg('allow', '');   // PARITYTEST-v1: more interactions (a module) and the list of allowed differences (JSON)
const sleep = ms => new Promise(r => setTimeout(r, ms));
const FIXED = new Date('2026-11-02T19:30:00-08:00');
const STORY_OLD = process.env.LC_STORY_OLD || 's04743';
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const FONTCACHE = path.join(OUT, '_fontcache');

const MOCK = () => {   // the reference's stand-in for window.claude: in-memory db + the same download call
  let cols = {}; const subs = {};
  try { cols = JSON.parse(sessionStorage.getItem('__mockdb') || '{}'); } catch (e) { }   // survives a reload, like the live database does
  const keep = () => { try { sessionStorage.setItem('__mockdb', JSON.stringify(cols)); } catch (e) { } };
  const snap = c => { const docs = Object.entries(cols[c] || {}).map(([id, data]) => ({ id, exists: true, data: () => data })); return { docs, size: docs.length, empty: !docs.length, forEach: f => docs.forEach(f) }; };
  const fire = c => (subs[c] || []).forEach(cb => { try { cb(snap(c)); } catch (e) { } });
  const col = c => ({ id: c, doc: id => ({ id: String(id), set: o => { (cols[c] = cols[c] || {})[String(id)] = JSON.parse(JSON.stringify(o)); keep(); setTimeout(() => fire(c), 0); return Promise.resolve(); },
    delete: () => { delete (cols[c] || {})[String(id)]; keep(); setTimeout(() => fire(c), 0); return Promise.resolve(); },
    get: () => Promise.resolve(cols[c] && cols[c][String(id)] ? { id: String(id), exists: true, data: () => cols[c][String(id)] } : { id: String(id), exists: false, data: () => undefined }) }),
    get: () => Promise.resolve(snap(c)), onSnapshot: (cb) => { (subs[c] = subs[c] || []).push(cb); setTimeout(() => cb(snap(c)), 0); return () => { } } });
  const downloads = { save: o => new Promise(resolve => { const data = o && o.data, name = (o && o.filename) || 'download'; const blob = data instanceof Blob ? data : new Blob([data == null ? '' : data]);
    const u = URL.createObjectURL(blob), a = document.createElement('a'); a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 10000); resolve({ saved: true, filename: name }); }) };
  window.claude = { __mock: true, use: n => n === 'db' ? Promise.resolve({ collection: col }) : n === 'downloads' ? Promise.resolve(downloads) : Promise.reject(new Error('not_declared')) };
};

async function newPage(browser, target, base, extra) {
  const ctx = await browser.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: 1, reducedMotion: 'reduce', locale: 'en-US', timezoneId: 'America/Los_Angeles', acceptDownloads: true });
  await ctx.clock.install({ time: FIXED });
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: new URL(base).origin }).catch(() => { });
  if (target === 'ref') {
    await ctx.addInitScript(MOCK);
    // the recorded exception: the PC page server hides the Update, Refresh, tone, author and translation buttons (station_server.HIDE_CSS); the reference gets the same rule
    await ctx.addInitScript(css => document.addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s); }),
      '#runFind,#runRefresh,#raStrip,[data-runfind],#updGo,#updRefresh,#updSave,#updAdd,#updCopy,#updAgain,[data-trate],[data-afind],[data-trstory],[data-tstop],[data-astop]{display:none!important}');
    await ctx.route(/fonts\.(googleapis|gstatic)\.com/, async route => {   // the same Google answers the look check used (cached there)
      const url = route.request().url(), key = path.join(FONTCACHE, crypto.createHash('sha1').update(url).digest('hex'));
      if (fs.existsSync(key)) return route.fulfill({ status: 200, contentType: fs.readFileSync(key + '.type', 'utf8'), body: fs.readFileSync(key), headers: { 'access-control-allow-origin': '*' } });
      return route.continue();
    });
  }
  const p = await ctx.newPage(); p.__base = base; p.__errors = [];
  p.on('pageerror', e => p.__errors.push(String(e).slice(0, 200)));
  await p.goto(base + ((extra && extra.hash) || ''), { waitUntil: 'load' });
  await p.waitForSelector('nav.tabs button[data-tab]', { timeout: 60000 });
  await p.waitForFunction(() => { const q = document.querySelector('#q'); return !q || !/index/i.test(q.placeholder); }, null, { timeout: 120000 }).catch(() => { });
  await sleep(1500);
  return { ctx, p };
}
const snapClips = p => p.evaluate(() => ({
  pager: (document.querySelector('#pager .mono') || {}).textContent || '', ids: [...document.querySelectorAll('#tbody tr[data-id]')].slice(0, 15).map(r => r.dataset.id),
  rows: document.querySelectorAll('#tbody tr[data-id]').length, chips: (document.querySelector('#chips') || {}).innerText || '', hash: location.hash,
  views: [...document.querySelectorAll('#views button')].map(b => b.textContent.trim()).join('|'), q: document.querySelector('#q').value, when: document.querySelector('#when').value }));
const openRail = async p => { const open = await p.evaluate(() => document.querySelector('#view-db #rail').getBoundingClientRect().right > 20); if (!open) { await p.click('#openRail'); await sleep(500); } };
const closeRail = async p => { const open = await p.evaluate(() => document.querySelector('#view-db #rail').getBoundingClientRect().right > 20); if (open) { await p.click('#closeRail'); await sleep(500); } };
const tabText = p => p.evaluate(() => { const v = [...document.querySelectorAll('main > section')].find(s => !s.hidden); return v ? v.id + ':' + v.innerText.length + ':' + (() => { let h = 0; const s = v.innerText; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return h; })() : ''; });
async function download(p, clickFn) { const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 30000 }), clickFn()]); const fp = await dl.path(); const b = fs.readFileSync(fp); return { name: dl.suggestedFilename(), bytes: b.length, sha: sha(b) }; }
const exportMenu = async p => { const open = await p.evaluate(() => document.querySelector('details.dlmenu').open); if (!open) { await p.click('details.dlmenu summary'); await sleep(300); } };

const T = {};   // name -> async (p, base) => outcome
T.clips_search = async (p, base, out) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200);
  out.start = await snapClips(p);
  for (const term of ['housing', 'Newsom signs', 'food safety', 'AB 2204', 'gabriel schiavo', 'ICE', 'zzzqqq', 'Wiener Palestine']) { await p.fill('#q', term); await sleep(1500); out[term] = await snapClips(p); }
  await p.fill('#q', ''); await sleep(1200); out.cleared = await snapClips(p); return out; };
T.clips_dates = async (p, base, out) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200);
  const vals = await p.evaluate(() => [...document.querySelectorAll('#when option')].map(o => o.value)); out.options = vals;
  for (const v of vals.filter(v => v !== 'custom')) { await p.selectOption('#when', v); await sleep(900); out['when=' + v] = await snapClips(p); } return out; };
T.clips_facets = async (p, base, out) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200); await openRail(p);
  const keys = await p.evaluate(() => [...new Set([...document.querySelectorAll('#view-db input[data-f]')].map(i => i.dataset.f))]); out.keys = keys;
  for (const k of keys) { const inp = p.locator(`#view-db input[data-f="${k}"]`).first(); if (!(await inp.isVisible())) { await inp.locator('xpath=ancestor::details[1]/summary').click(); await sleep(300); }
    await inp.locator('xpath=ancestor::label[1]').click(); await sleep(800); out['+' + k] = await snapClips(p); }
  await p.click('#clearAll'); await sleep(900); out.cleared = await snapClips(p);
  // list-only toggle
  const lo = p.locator('#view-db [data-lo]').first(); if (await lo.count()) { if (!(await lo.isVisible())) { await lo.locator('xpath=ancestor::details[1]/summary').click(); await sleep(300); } await lo.locator('xpath=ancestor::label[1]').click(); await sleep(900); out.listonly_on = await snapClips(p); await lo.locator('xpath=ancestor::label[1]').click(); await sleep(900); out.listonly_off = await snapClips(p); }
  await closeRail(p); return out; };
T.clips_sort = async (p, base, out) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200);
  for (const k of ['date', 'hl', 'topic', 'reach', 'rep']) for (const n of [1, 2]) { await p.click(`[data-sort="${k}"]`); await sleep(700); out[k + n] = await snapClips(p); }
  await p.click('#density'); await sleep(600); out.dense = await snapClips(p); await p.click('#density');
  const per = await p.evaluate(() => [...document.querySelectorAll('#per option')].map(o => o.value)); out.per = per;
  for (const v of per) { await p.selectOption('#per', v); await sleep(900); out['per' + v] = await snapClips(p); }
  return out; };
T.saved_views = async (p, base, out) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200);
  for (const id of ['p30', 'phd', 'pmj', 'png', 'psv']) { await p.click(`[data-view="${id}"]`); await sleep(900); out[id] = await snapClips(p); }
  await p.click('#clearAll').catch(() => { }); await sleep(500);
  await p.fill('#q', 'housing'); await sleep(1200); await p.click('[data-vnew]'); await sleep(500); await p.fill('#vname', 'Parity view'); await p.click('#vform button[type=submit]'); await sleep(1500);
  out.after_save = await snapClips(p); out.toast = await p.evaluate(() => (document.querySelector('#toast,.toast') || {}).textContent || '');
  await p.fill('#q', ''); await sleep(800); const vb = p.locator('[data-view^="v"],[data-view^="l"]').first(); if (await vb.count()) { await vb.click(); await sleep(900); out.reapplied = await snapClips(p); }
  const del = p.locator('[data-vdel]').first(); if (await del.count()) { await del.click(); await sleep(900); out.after_delete = await snapClips(p); } return out; };
T.story_sheet = async (p, base, out) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200);
  const sheet = () => p.evaluate(() => { const s = document.querySelector('#sheet'); return { open: !s.hidden, pos: (s.querySelector('.pos') || {}).textContent || '', kick: (s.querySelector('.kick') || {}).innerText || '', h2: (s.querySelector('h2') || {}).textContent || '',
    links: [...s.querySelectorAll('.dlinks a')].map(a => a.textContent.trim().slice(0, 40) + '>' + a.getAttribute('href')).join('|'), badges: (s.querySelector('.sh-badges') || {}).innerText || '', factline: (s.querySelector('.factline') || {}).innerText || '',
    tone: (s.querySelector('.tonebox') || {}).innerText || '', note: (document.querySelector('#tnote') || {}).value, hash: location.hash, wide: s.classList.contains('wide') }; });
  await p.locator('#tbody tr[data-id]').first().locator('td').nth(1).click(); await sleep(2500); out.first = await sheet();
  await p.click('[data-nav="1"]'); await sleep(2000); out.next = await sheet(); await p.click('[data-nav="1"]'); await sleep(1500); out.next2 = await sheet();
  await p.click('[data-nav="-1"]'); await sleep(1500); out.prev = await sheet(); { const w = p.locator('[data-wide]'); if (await w.isVisible()) await w.click(); } await sleep(1500); out.wide = await sheet();   // the full-page button is hidden in a half-width window
  await p.keyboard.press('Escape'); await sleep(900); out.closed = await sheet(); out.rows = await snapClips(p); return out; };
T.saved_copy = async (p, base, out) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200);
  for (const id of [STORY_OLD, 's02546']) {
    const hl = await p.evaluate(id => JSON.parse(document.getElementById('data').textContent).find(r => r.id === id).hl, id);
    await p.fill('#q', hl); await sleep(1500); await p.locator(`#tbody tr[data-id="${id}"]`).first().locator('td').nth(1).click(); await sleep(3500);
    out[id] = await p.evaluate(async () => { const f = document.querySelector('#doc iframe'); if (!f) return { frame: false }; const d = f.contentDocument; await Promise.all([...d.images].filter(i => !i.complete).map(i => new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 5000); })));
      const t = d.body.innerText; let h = 0; for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) | 0;
      return { frame: true, textLen: t.length, textHash: h, imgs: d.images.length, loaded: [...d.images].filter(i => i.complete && i.naturalWidth > 0).map(i => i.naturalWidth + 'x' + i.naturalHeight).join(','), links: d.querySelectorAll('a').length,
        finder: (document.querySelector('#fcount') || {}).textContent, sandbox: f.getAttribute('sandbox'), marks: d.querySelectorAll('mark.jg-hit').length,
        italic: [...d.querySelectorAll('i,em')].length, bold: [...d.querySelectorAll('b,strong')].length, h1: (d.querySelector('h1') || {}).textContent }; });
    const hit = p.locator('[data-hit="1"]').first(); if (await hit.count()) { await hit.click().catch(() => { }); await sleep(500); out[id + '_hit'] = await p.evaluate(() => (document.querySelector('#fcount') || {}).textContent); }
    await p.keyboard.press('Escape'); await sleep(600); }
  return out; };
T.team_notes = async (p, base, out) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200);
  await p.locator('#tbody tr[data-id]').nth(1).locator('td').nth(1).click(); await sleep(2000);
  const st = () => p.evaluate(() => ({ meta: (document.querySelector('#tnoteMeta') || {}).textContent, val: (document.querySelector('#tnote') || {}).value, badges: ((document.querySelector('#sheet .sh-badges') || {}).innerText || ''), rowBadge: !!document.querySelector('#tbody tr.on .badge.flag') }));
  out.before = await st(); await p.fill('#tnote', 'Parity note one'); await sleep(2200); out.added = await st();
  await p.fill('#tnote', 'Parity note edited'); await sleep(2200); out.edited = await st();
  await p.keyboard.press('Escape'); await sleep(800); await p.fill('#q', ''); await p.locator('#tbody tr[data-id]').nth(1).locator('td').nth(1).click(); await sleep(1800); out.reopened = await st();
  await p.fill('#tnote', ''); await sleep(2200); out.cleared = await st(); return out; };
T.history = async (p, base, out) => { const st = () => p.evaluate(() => ({ hash: location.hash, tab: (document.querySelector('nav.tabs [aria-selected=true]') || {}).textContent, sheet: !document.querySelector('#sheet').hidden, back: document.querySelector('#navBack').disabled, fwd: document.querySelector('#navFwd').disabled }));
  out.start = await st();
  for (const [n, sel] of [['clips', 'nav.tabs button[data-tab=db]'], ['data', 'nav.tabs button[data-tab=an]'], ['reporters', 'nav.tabs button[data-tb=reporters]'], ['bills', 'nav.tabs button[data-tb=bills]']]) { await p.click(sel); await sleep(1500); out['go_' + n] = await st(); }
  await p.click('nav.tabs button[data-tab=db]'); await sleep(1200); await p.locator('#tbody tr[data-id]').first().locator('td').nth(1).click(); await sleep(2000); out.story = await st();
  for (let i = 0; i < 4; i++) { await p.click('#navBack'); await sleep(1200); out['back' + i] = await st(); }
  for (let i = 0; i < 2; i++) { await p.click('#navFwd'); await sleep(1200); out['fwd' + i] = await st(); }
  await p.keyboard.press('Alt+ArrowLeft'); await sleep(1000); out.altleft = await st(); return out; };
T.hash_routes = async (p, base, out) => { const hashes = ['#clips', '#data', '#reporters', '#outlets', '#press-releases', '#bills', '#story-travel', '#reporters?win=90', '#bills/ab-418-2023-24', '#press-releases/off140', '#outlets?iss=Food%20safety', '#nonsense'];
  // discover the filter hashes the tabs make when a filter is ticked, then open them as URLs on a fresh page
  for (const t of ['reporters', 'outlets', 'releases', 'bills', 'travel']) { await p.click(`nav.tabs button[data-tb=${t}]`); await sleep(1800);
    const rail = p.locator('#view-tb [data-tt=rail]:visible'); if (await rail.count()) { await rail.first().click(); await sleep(600); }
    const inp = p.locator('#view-tb input[data-ttf]:visible');
    for (const n of [0, 3]) if (await inp.count() > n) { await inp.nth(n).locator('xpath=ancestor::label[1]').click().catch(() => { }); await sleep(900); const h = await p.evaluate(() => location.hash); out['made_' + t + n] = h; hashes.push(h); }
    const dn = p.locator('#view-tb [data-tt=done]:visible'); if (await dn.count()) { await dn.first().click(); await sleep(500); } }
  out.hashes = hashes; return out; };
T.downloads = async (p, base, out) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200);
  await p.fill('#q', 'housing'); await sleep(1500);
  await exportMenu(p); out.csv = await download(p, () => p.click('[data-dl="csv"]'));
  await exportMenu(p); out.sheet = await download(p, () => p.click('[data-dl="sheet"]'));
  await exportMenu(p); await p.click('#copyClips').catch(() => { }); await sleep(600); out.copyClips = await p.evaluate(() => navigator.clipboard.readText().then(t => ({ len: t.length, head: t.slice(0, 160) })).catch(e => 'noclip'));
  await exportMenu(p); await p.click('#copySheet').catch(() => { }); await sleep(600); out.copySheet = await p.evaluate(() => navigator.clipboard.readText().then(t => ({ len: t.length, head: t.slice(0, 160) })).catch(e => 'noclip'));
  // ticked stories: tick two rows, the bulk bar's CSV
  await p.fill('#q', ''); await sleep(1000); await p.locator('#tbody tr[data-id] input[type=checkbox]').nth(0).check().catch(() => { }); await p.locator('#tbody tr[data-id] input[type=checkbox]').nth(2).check().catch(() => { }); await sleep(500);
  out.bulk = await p.evaluate(() => (document.querySelector('#bulkN') || {}).textContent); if (await p.locator('#bkCsv').isVisible()) out.bulk_csv = await download(p, () => p.click('#bkCsv'));
  for (const t of ['reporters', 'outlets', 'releases', 'bills']) { await p.click(`nav.tabs button[data-tb=${t}]`); await sleep(1500); await p.evaluate(() => document.querySelectorAll('#view-tb details').forEach(d => { if (d.querySelector('[data-tt=csv]')) d.open = true; })); await sleep(300); const b = p.locator('#view-tb [data-tt=csv]:visible').first(); if (await b.count()) { out['csv_' + t] = await download(p, () => b.click()).catch(e => 'fail ' + String(e).slice(0, 60)); } }
  return out; };
T.tab_tables = async (p, base, out) => { for (const t of ['reporters', 'outlets', 'releases', 'bills', 'travel']) { await p.click(`nav.tabs button[data-tb=${t}]`); await sleep(2000); out[t] = await tabText(p);
  const so = await p.evaluate(() => [...document.querySelectorAll('#view-tb [data-ttsort]')].filter(b => b.offsetParent).map(b => b.dataset.ttsort)); for (const k of so.slice(0, 4)) { await p.locator(`#view-tb [data-ttsort="${k}"]:visible`).first().click(); await sleep(700); out[t + '_sort_' + k] = await tabText(p); }
  const open = p.locator('#view-tb .tt-open:visible').first(); if (await open.count()) { await open.click(); await sleep(2000); out[t + '_entity'] = { hash: await p.evaluate(() => location.hash), t: await tabText(p) }; } }
  await p.click('nav.tabs button[data-tab=an]'); await sleep(2000); out.data = await tabText(p);
  for (const sel of await p.evaluate(() => [...document.querySelectorAll('#view-an select')].filter(s => s.offsetParent && s.id).map(s => '#' + s.id))) { const vals = await p.evaluate(s => [...document.querySelector(s).options].map(o => o.value), sel); for (const v of vals.slice(0, 4)) { await p.evaluate(([s, v]) => { const e = document.querySelector(s); e.value = v; e.dispatchEvent(new Event('change', { bubbles: true })); }, [sel, v]); await sleep(900); out['data_' + sel + '=' + v] = await tabText(p); } }
  return out; };

if (EXTRA) require(path.resolve(EXTRA))(T, { sleep, snapClips, openRail, closeRail, tabText, download, exportMenu, STORY_OLD, sha, fs, path, newPage });
const ALLOWED = ALLOW ? JSON.parse(fs.readFileSync(ALLOW, 'utf8')) : [];
const allowedBy = (name, x) => ALLOWED.find(r => (!r.test || r.test === name) && new RegExp(r.path || '.').test(x.at) && (!r.ref || new RegExp(r.ref).test(JSON.stringify(x.ref))) && (!r.pc || new RegExp(r.pc).test(JSON.stringify(x.pc))));

async function run(browser, target, base, name) {
  const { ctx, p } = await newPage(browser, target, base);
  let res = {}; try { const r = await T[name](p, base, res); if (r && r !== res) Object.assign(res, r); } catch (e) { res.crash = String(e).slice(0, 300); }
  res.__errors = p.__errors; await ctx.close(); return res;
}
async function hashRoutes(browser, target, base, hashes) {
  const out = {};
  for (const h of hashes) { const { ctx, p } = await newPage(browser, target, base, { hash: h }); await sleep(1500);
    out[h] = await p.evaluate(() => ({ hash: location.hash, tab: (document.querySelector('nav.tabs [aria-selected=true]') || {}).textContent, txt: (() => { const v = [...document.querySelectorAll('main > section')].find(s => !s.hidden); const s = v ? v.innerText : ''; let x = 0; for (let i = 0; i < s.length; i++) x = (x * 31 + s.charCodeAt(i)) | 0; return v ? v.id + ':' + s.length + ':' + x : ''; })() }));
    await ctx.close(); }
  return out;
}
function diff(a, b, pth, acc) {
  if (JSON.stringify(a) === JSON.stringify(b)) return acc;
  if (a && b && typeof a === 'object' && typeof b === 'object') { for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) diff(a[k], b[k], pth + '.' + k, acc); }
  else acc.push({ at: pth, ref: a, pc: b });
  return acc;
}
(async () => {
  if (process.argv.includes('--list')) { console.log(Object.keys(T).join(',')); return; }
  fs.mkdirSync(path.join(OUT, 'parity'), { recursive: true });
  const names = (ONLY ? ONLY.split(',') : Object.keys(T)), browser = await chromium.launch(); let nd = 0; const summary = {};
  for (const name of names) {
    const t0 = Date.now();
    let a, b;   // the clipboard is shared by every page of one browser: tests that use it run one side after the other
    if (['downloads', 'exports_more'].includes(name)) { a = await run(browser, 'ref', REF, name); b = await run(browser, 'pc', PC, name); } else[a, b] = await Promise.all([run(browser, 'ref', REF, name), run(browser, 'pc', PC, name)]);
    let extra = null;
    if (name === 'hash_routes') { const hs = [...new Set([...(a.hashes || []), ...(b.hashes || [])])]; const [ra, rb] = await Promise.all([hashRoutes(browser, 'ref', REF, hs), hashRoutes(browser, 'pc', PC, hs)]); extra = diff(ra, rb, 'route', []);
      a.routes = ra; b.routes = rb; }
    fs.writeFileSync(path.join(OUT, 'parity', `${VP}_${name}.ref.json`), JSON.stringify(a, null, 1)); fs.writeFileSync(path.join(OUT, 'parity', `${VP}_${name}.pc.json`), JSON.stringify(b, null, 1));
    let d = diff(a, b, name, []); const ok = [];
    d = d.filter(x => { const r = allowedBy(name, x); if (r) { ok.push({ at: x.at, reason: r.reason }); return false; } return true; });
    summary[name] = { diffs: d.length, allowed: ok.length, allowed_list: ok, steps: Object.keys(a).length, crash: a.crash || b.crash || null, diff_list: d.map(x => ({ at: x.at, ref: x.ref, pc: x.pc })) };
    nd += d.length + ((a.crash || b.crash) ? 1 : 0); console.log(`${name}: ${d.length} differences (+${ok.length} allowed) in ${Object.keys(a).length} steps (${((Date.now() - t0) / 1000).toFixed(0)}s)${a.crash || b.crash ? ' CRASH ' + (a.crash || b.crash) : ''}`);
    d.slice(0, 8).forEach(x => console.log('   ', x.at, '\n      ref:', String(JSON.stringify(x.ref)).slice(0, 220), '\n      pc :', String(JSON.stringify(x.pc)).slice(0, 220)));
  }
  { const sp = path.join(OUT, 'parity', `${VP}_summary.json`); let old = {}; try { old = JSON.parse(fs.readFileSync(sp, 'utf8')); } catch (e) { } fs.writeFileSync(sp, JSON.stringify(Object.assign(old, summary), null, 1)); }
  await browser.close(); process.exit(nd ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
