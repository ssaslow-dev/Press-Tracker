/* screenshots of the station page (for UI review): node tests/shot_ui.js FOR_UPDATE.json OUTDIR */
const H = require('./nb/real_harness.js'), path = require('path');
(async () => {
  const X = await H.start(path.join(H.ST, 'dist', 'index.html'), () => [], { images: 4 }), page = X.page;
  await page.screenshot({ path: process.argv[3] + '/0_start.png', fullPage: true });
  await H.loadFile(page, process.argv[2]); await page.waitForTimeout(1500);
  await page.screenshot({ path: process.argv[3] + '/1_loaded.png', fullPage: true });
  console.log(await page.evaluate(() => document.body.innerText.slice(0, 6000)));
  await X.close();
})();
