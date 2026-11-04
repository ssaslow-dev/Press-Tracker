// node check_preview.js <preview.html> <pc base url> <outdir>   (needs Playwright; compares routes of the file:// preview with the PC tracker)
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs'), path = require('path');
const [, , FILE, PC, OUT] = process.argv;
fs.mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ROUTES = ['', '#clips', '#data', '#reporters', '#outlets', '#press-releases', '#bills', '#story-travel', '#press-releases/pr00244', '#bills/AB 418'];
async function run(url, tag, browser) {
  const out = { errs: [], routes: {} };
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce', locale: 'en-US' });
  const p = await ctx.newPage(); p.setDefaultTimeout(6000);
  p.on('console', m => { if (m.type() === 'error') out.errs.push(m.text().slice(0, 200)); });
  p.on('pageerror', e => out.errs.push('PAGEERROR ' + e.message.slice(0, 200)));
  p.on('requestfailed', r => { if (!/^(data|blob):/.test(r.url())) out.errs.push('REQFAILED ' + r.url().slice(0, 120)); });
  await p.goto(url); await sleep(3500);
  for (const r of ROUTES) {
    await p.evaluate(h => { location.hash = h; }, r); await sleep(1800);
    const t = await p.evaluate(() => { const v = document.querySelector('main') || document.body; return v.innerText; });
    out.routes[r || 'home'] = { len: t.length, text: t };
    await p.screenshot({ path: path.join(OUT, tag + '_' + (r || 'home').replace(/[^a-z0-9]+/gi, '_') + '.png') });
  }
  // interactions on Clips
  await p.evaluate(() => { location.hash = '#clips'; }); await p.reload(); await sleep(3500);
  out.clipsCount = await p.evaluate(() => document.querySelectorAll('#tbody tr[data-id]').length);
  out.countText = await p.evaluate(() => { const e = document.querySelector('#count, #resCount, .count'); return e ? e.innerText : ''; });
  await p.fill('#q', 'housing'); await sleep(1500);
  out.search = await p.evaluate(() => ({ rows: document.querySelectorAll('#tbody tr[data-id]').length, txt: (document.querySelector('#count, #resCount, .count') || {}).innerText }));
  await p.fill('#q', ''); await sleep(800);
  await p.click('[data-sort="hl"]'); await sleep(800);
  out.sorted = await p.evaluate(() => [...document.querySelectorAll('#tbody tr[data-id] td:nth-child(2)')].slice(0, 3).map(e => e.innerText.slice(0, 40)));
  await p.locator('#tbody tr[data-id]').nth(2).locator('td').nth(1).click(); await sleep(2500);
  out.sheet = await p.evaluate(() => { const s = document.getElementById('sheet'); return { open: !s.hidden, h2: (s.querySelector('h2') || {}).innerText, len: s.innerText.length, vis: [...s.querySelectorAll('button,a,textarea,select')].filter(e => e.offsetParent).map(e => (e.className || e.tagName) + ':' + (e.innerText || '').trim().slice(0, 20)).join('|') }; });
  await p.screenshot({ path: path.join(OUT, tag + '_sheet.png') });
  await p.keyboard.press('Escape'); await sleep(500);
  // Manage panel
  await p.click('#updBtn'); await sleep(1200);
  out.manage = await p.evaluate(() => ({ tabs: [...document.querySelectorAll('#mgTabs button')].filter(e => e.offsetParent).map(e => e.innerText), vis: [...document.querySelectorAll('#upd button,#upd input')].filter(e => e.offsetParent).map(e => (e.innerText || e.id).trim().slice(0, 24)).join('|') }));
  for (const k of ['quality', 'defs']) { const b = p.locator('[data-mg="' + k + '"]'); if (await b.isVisible()) { await b.click(); await sleep(900); out['mg_' + k] = (await p.evaluate(() => document.querySelector('#upd').innerText)).length; } }
  await p.screenshot({ path: path.join(OUT, tag + '_manage.png') });
  out.visibleButtons = await p.evaluate(() => [...document.querySelectorAll('header button')].filter(e => e.offsetParent).map(e => e.innerText.trim()).join('|'));
  await ctx.close(); return out;
}
(async () => {
  const b = await chromium.launch();
  const pv = await run('file://' + FILE, 'pv', b), pc = PC !== '-' ? await run(PC, 'pc', b) : null;
  const rep = { preview: { errs: pv.errs, clipsCount: pv.clipsCount, search: pv.search, sorted: pv.sorted, sheet: pv.sheet, manage: pv.manage, mg_quality: pv.mg_quality, mg_defs: pv.mg_defs, buttons: pv.visibleButtons, routes: Object.fromEntries(Object.entries(pv.routes).map(([k, v]) => [k, v.len])) } };
  if (pc) { rep.pc = { errs: pc.errs, clipsCount: pc.clipsCount, search: pc.search, sorted: pc.sorted, sheet: pc.sheet, manage: pc.manage, buttons: pc.visibleButtons, routes: Object.fromEntries(Object.entries(pc.routes).map(([k, v]) => [k, v.len])) };
    rep.textDiff = {}; for (const k of Object.keys(pv.routes)) { const A = pv.routes[k].text.split('\n'), B = pc.routes[k].text.split('\n'); const sa = new Set(A), sb = new Set(B);
      rep.textDiff[k] = { onlyPreview: A.filter(x => !sb.has(x)).slice(0, 8), onlyPC: B.filter(x => !sa.has(x)).slice(0, 8) }; } }
  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(rep, null, 1)); console.log(JSON.stringify(rep, null, 1).slice(0, 6000));
  await b.close();
})();
