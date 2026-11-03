// TIDY-v1 page checks in the real page (Chromium) of a running PC tracker. node tidy_page.js BASE OUTDIR  -> one JSON line
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/opt/node-tools/node_modules/playwright');
const fs = require('fs');
const [BASE, OUT] = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ROUTES = { clips: '#clips', reporters: '#reporters', outlets: '#outlets', releases: '#press-releases', bills: '#bills', travel: '#story-travel', rel_page: '#press-releases/pr00208', outlet_page: '#outlets/politico' };
const RECTS = () => [...document.querySelectorAll('.card table.db')].filter(t => t.tHead && t.offsetParent).map(t => {
  const c = t.closest('.card'), th = [...t.tHead.rows[0].cells].filter(x => x.offsetParent), f = th[0].getBoundingClientRect(), l = th[th.length - 1].getBoundingClientRect(), cr = c.getBoundingClientRect();
  return { cls: t.className, card: [cr.left, cr.top, cr.right, cr.bottom], th: [f.left, f.top, l.right, f.bottom], stuck: t.classList.contains('hdr-stuck') };
});
async function page(ctx, hash) {
  const p = await ctx.newPage(); await p.goto(BASE + '/' + (hash || '')); await p.waitForFunction(() => window.__ajgFiles === true, null, { timeout: 90000 }); await sleep(2500);
  if (hash) { await p.evaluate(h => { location.hash = h; }, hash); await sleep(1800); }
  await p.waitForFunction(() => document.querySelector('#view-tb .card table.db tbody tr, #view-db .card table.db tbody tr') || !document.querySelector('nav.tabs'), null, { timeout: 60000 }).catch(() => {});
  await sleep(500);
  return p;
}
(async () => {
  const b = await chromium.launch(); const res = { edges: {}, outlets: {}, issues: {}, align: {}, tiles: null, wording: {} };
  // 1. table header edges: shots + rectangles (the test samples pixels with Pillow)
  for (const [vw, scheme] of [[1440, 'light'], [960, 'dark']]) {
    const ctx = await b.newContext({ viewport: { width: vw, height: 900 }, colorScheme: scheme, reducedMotion: 'reduce' });
    await Promise.all(Object.entries(ROUTES).map(async ([rn, h]) => {
      const p = await page(ctx, h);
      for (const st of ['rest', 'pinned']) {
        if (st === 'pinned') { await p.evaluate(() => { const t = [...document.querySelectorAll('.card table.db')].find(t => t.tHead && t.offsetParent && t.getBoundingClientRect().height > 500) || [...document.querySelectorAll('.card table.db')].find(t => t.tHead && t.offsetParent); window.scrollTo(0, t.getBoundingClientRect().top + scrollY - 128 + 200); }); await sleep(900); }
        const k = `${rn}_${vw}_${scheme}_${st}`; await p.screenshot({ path: `${OUT}/${k}.png` }); res.edges[k] = await p.evaluate(RECTS);
      }
      await p.close();
    }));
    await ctx.close();
  }
  // 2. Outlets and Reporters at 960 and 1440: no sideways scroll, heading/search/Export inside the window
  for (const vw of [960, 1440, 1100]) {
    const ctx = await b.newContext({ viewport: { width: vw, height: 900 }, reducedMotion: 'reduce' });
    for (const h of ['#outlets', '#reporters']) {
      const p = await page(ctx, h);
      res.outlets[`${h}_${vw}`] = await p.evaluate(() => { const de = document.documentElement, t = document.querySelector('#view-tb table.db'), card = t.closest('.card').getBoundingClientRect();
        const R = s => { const e = document.querySelector(s); return e ? e.getBoundingClientRect().right : null; };
        return { sw: de.scrollWidth, cw: de.clientWidth, table: t.getBoundingClientRect().width, cardInner: card.width - 2, head: R('#view-tb .tt-head'), h1: R('#view-tb .tt-h1'), search: R('#view-tb .tt-bar .search'), exp: R('#view-tb .tt-exp') }; });
      if (vw === 1440 || vw === 960) {   // 3. Top issues cells
        res.issues[`${h}_${vw}`] = await p.evaluate(() => { const out = { n: 0, comma: 0, wrapped: 0, split: 0, countAlone: 0, sample: [] };
          for (const it of document.querySelectorAll('#view-tb table.db td .tiss')) { out.n++;
            let lo = 1e9, hi = -1e9; const rg = document.createRange(); rg.selectNodeContents(it); for (const r of rg.getClientRects()) { if (!r.width) continue; const c = (r.top + r.bottom) / 2; lo = Math.min(lo, c); hi = Math.max(hi, c); }
            if (hi - lo > 6) out.wrapped++; if (/^\s*,/.test(it.textContent)) out.comma++;
            const sub = it.querySelector('.sub'); if (sub && sub.getBoundingClientRect().top > it.getBoundingClientRect().top + it.getBoundingClientRect().height - sub.getBoundingClientRect().height + 3) out.countAlone++;
            if (out.sample.length < 3) out.sample.push(it.textContent.trim()); }
          out.rowsWithComma = [...document.querySelectorAll('#view-tb table.db td')].filter(td => /(^|\n)\s*,/.test(td.innerText)).length; return out; });
      }
      await p.close();
    }
    await ctx.close();
  }
  // 4. alignment
  { const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
    let p = await page(ctx, '#reporters');
    res.align.headLeft = await p.evaluate(() => { const L = e => e.getBoundingClientRect().left, h = document.querySelector('#view-tb .tt-head'); return { head: L(h), h1: L(h.querySelector('h2')), cap: L(h.querySelector('.tt-about > summary')), card: L(document.querySelector('#view-tb .card')), filters: L(document.querySelector('#view-tb .tt-ft')) }; });
    res.align.masthead = await p.evaluate(() => { const H = s => document.querySelector(s).getBoundingClientRect().height; return { back: H('#navBack'), fwd: H('#navFwd'), sheet: H('header .hdr-acts [data-dl="sheet"]'), manage: H('#updBtn'), tf: H('#ajgf-btn') }; });
    res.align.tabPad = await p.evaluate(() => { const c = getComputedStyle(document.querySelector('#tab-ov')); return [c.paddingTop, c.paddingBottom]; });
    await p.close();
    p = await page(ctx, '');
    res.tiles = await p.evaluate(() => [...document.querySelectorAll('button.tile')].map(t => +(t.querySelector('.eyebrow').getBoundingClientRect().top - t.getBoundingClientRect().top).toFixed(1)));
    // 6. wording: every Manage tab, the Data checks, a story sheet
    await p.click('#updBtn'); await sleep(1200);
    res.wording.manageTabs = await p.evaluate(() => [...document.querySelectorAll('#mgTabs [data-mg]')].map(b => [b.dataset.mg, b.offsetParent !== null, b.getAttribute('aria-pressed')]));
    const texts = {};
    for (const k of ['log', 'saved', 'quality', 'defs']) { await p.click(`#mgTabs [data-mg="${k}"]`); await sleep(700); texts[k] = await p.evaluate(() => (document.querySelector('#mgOther') || {}).innerText || ''); }
    res.wording.texts = texts;
    res.wording.firstOpen = null;
    await p.close();
    p = await page(ctx, '#clips');
    await p.locator('#tbody tr[data-id]').first().locator('td').nth(1).click(); await sleep(2500);
    res.wording.sheet = await p.evaluate(() => document.querySelector('#sheet').innerText);
    await p.close(); await ctx.close();
    // first open of Manage: which tab is shown
    const ctx2 = await b.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' }); p = await page(ctx2, '#clips');
    await p.click('#updBtn'); await sleep(1200);
    res.wording.firstOpen = await p.evaluate(() => [document.querySelector('#mgTabs [aria-pressed="true"]').dataset.mg, document.querySelector('#upd').innerText.slice(0, 400)]);
    await ctx2.close(); }
  console.log(JSON.stringify(res)); await b.close();
})().catch(e => { console.error(e); process.exit(1); });
