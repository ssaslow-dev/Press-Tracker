const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs');
const [,, outdir, ...specs] = process.argv;   // spec = WxH@dsf
(async () => {
  const b = await chromium.launch();
  for (const sp of specs) {
    const [vp, dsf] = sp.split('@'); const [w,h] = vp.split('x').map(Number);
    for (const r of ['outlets','reporters','press-releases','bills','story-travel']) {
      const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: Number(dsf||1) });
      const p = await ctx.newPage();
      await p.goto('http://127.0.0.1:8791/#' + r); await p.waitForTimeout(3000);
      const info = await p.evaluate(() => {
        const tt = [...document.querySelectorAll('.tt')].find(e => e.offsetParent);
        const th = tt.querySelector('table.db thead th'); const q = th.getBoundingClientRect();
        window.scrollTo(0, Math.max(0, tt.querySelector('.card').getBoundingClientRect().top + scrollY - 120));
        return null;
      });
      await p.waitForTimeout(400);
      const g = await p.evaluate(() => {
        const tt = [...document.querySelectorAll('.tt')].find(e => e.offsetParent);
        const R = e => { const q = e.getBoundingClientRect(); return [q.left, q.right, q.top, q.bottom]; };
        const th = tt.querySelector('table.db thead th');
        const ctl = tt.querySelector('.filters-toggle') || tt.querySelector('.tt-head');
        return { th: R(th), card: R(tt.querySelector('.card')), ctl: R(ctl), head: R(tt.querySelector('.tt-head')), dpr: devicePixelRatio, sy: scrollY };
      });
      const f = `${outdir}/${r}_${vp}_${dsf}.png`;
      await p.screenshot({ path: f });
      fs.writeFileSync(f.replace('.png', '.json'), JSON.stringify(g));
      await ctx.close();
    }
  }
  await b.close();
})();
