// usage: node browser_check.js <base url> <ext-writer cmd base url>   (prints JSON result)
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const base = process.argv[2], token = process.argv[3];
  const b = await chromium.launch(); const ctx = await b.newContext({ acceptDownloads: true }); const p = await ctx.newPage();
  const errors = []; p.on('pageerror', e => errors.push(String(e)));
  await p.goto(base + '/');
  // outside writer: another process adds a doc through the API while the page waits
  await p.waitForFunction(() => window.EXT_READY, null, { timeout: 15000 });
  const r = await fetch(base + '/_local/api/tones/ext-1', { method: 'PUT', headers: { 'X-Local-Token': token }, body: '{"tone":"Neutral"}' });
  const dlp = p.waitForEvent('download', { timeout: 30000 });
  await p.waitForFunction(() => window.RESULT, null, { timeout: 60000 });
  const res = await p.evaluate(() => window.RESULT);
  let dl = null; try { const d = await dlp; dl = { name: d.suggestedFilename(), text: require('fs').readFileSync(await d.path(), 'utf8') }; } catch (e) { dl = { error: String(e) }; }
  console.log(JSON.stringify({ res, dl, errors, extStatus: r.status }));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
