// node shots.js <preview.html> <pc base> <outdir>: one fresh load per route, same viewport and clock, a screenshot each
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const [, , FILE, PC, OUT] = process.argv; const sleep = ms => new Promise(r => setTimeout(r, ms));
const R = { home: '', clips: '#clips', data: '#data', reporters: '#reporters', releases: '#press-releases', relpage: '#press-releases/pr00244', bills: '#bills', billpage: '#bills/AB 418', outlets: '#outlets', travel: '#story-travel' };
(async () => { const b = await chromium.launch();
  for (const [tag, base] of [['pv', 'file://' + FILE], ['pc', PC]]) for (const [n, h] of Object.entries(R)) {
    const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce', locale: 'en-US' }); const p = await ctx.newPage();
    await p.goto(base + h); await sleep(4500);
    if (n === 'clips') { await p.locator('#tbody tr[data-id]').nth(2).locator('td').nth(1).click(); await sleep(2500); await p.screenshot({ path: `${OUT}/${tag}_sheet.png` }); await p.keyboard.press('Escape'); await sleep(600); }
    await p.screenshot({ path: `${OUT}/${tag}_${n}.png` }); await ctx.close(); }
  await b.close(); })();
