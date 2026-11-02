// the same page in a plain chromium (no claude.ai CSP): shows the generic browser rules only
const { chromium } = require('/opt/node-tools/node_modules/playwright'); const http = require('http'), fs = require('fs');
const html = '<!doctype html><html><head><meta charset=utf8></head><body>' + fs.readFileSync(__dirname + '/photo_test.html', 'utf8') + '</body></html>';
const srv = http.createServer((q, r) => { r.writeHead(200, { 'Content-Type': 'text/html' }); r.end(html); });
srv.listen(0, '127.0.0.1', async () => { const b = await chromium.launch(); const p = await b.newPage(); await p.addInitScript(() => { window.claude = { use: async () => null }; });
  await p.goto('http://127.0.0.1:' + srv.address().port + '/'); await p.waitForFunction(() => window.__photoResult, null, { timeout: 60000 });
  console.log(JSON.stringify(await p.evaluate(() => window.__photoResult), null, 1)); await b.close(); srv.close(); });
