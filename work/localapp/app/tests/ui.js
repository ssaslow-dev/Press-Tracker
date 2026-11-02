// usage: node ui.js <base url> <steps.json>   -> prints one JSON line {results, errors}
// A tiny step interpreter so the Python tests can drive the real page in Chromium.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/opt/node-tools/node_modules/playwright');
const fs = require('fs');
(async () => {
  const base = process.argv[2], steps = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
  const b = await chromium.launch(); const ctx = await b.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 900 } });
  const p = await ctx.newPage(); const errors = [], results = {}, external = [], pending = [];
  // every request that is not for this PC's own server (PHOTOLINK-v1 tests: what would the browser fetch, and with which headers)
  p.on('request', r => { if (!r.url().startsWith(base) && !/^(data|blob):/.test(r.url())) pending.push(r.allHeaders().then(h => external.push({ url: r.url(), type: r.resourceType(), referer: h['referer'] || null, headers: h }), () => external.push({ url: r.url(), type: r.resourceType(), referer: null }))); });
  p.on('pageerror', e => errors.push('pageerror: ' + String(e).slice(0, 300)));
  p.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text().slice(0, 300)); });
  const failures = {};
  p.on('requestfailed', r => { failures[r.url()] = (r.failure() || {}).errorText || 'failed'; errors.push('requestfailed: ' + r.url().slice(0, 120)); });
  p.on('response', r => { if (r.status() >= 400) errors.push('http ' + r.status() + ' ' + r.url().slice(0, 120)); });
  const panel = () => p.evaluate(() => (document.querySelector('#ajgf') || {}).innerText || '');
  try {
    for (const s of steps) {
      const name = s.name || s.op;
      if (s.op === 'goto') { await p.goto(base + '/', { waitUntil: 'load' }); await p.waitForFunction(() => window.__ajgFiles === true, null, { timeout: 60000 }); await p.waitForTimeout(s.wait || 1500); }
      else if (s.op === 'open_panel') { const open = await p.evaluate(() => document.querySelector('#ajgf').classList.contains('open')); if (!open) await p.click('#ajgf-btn'); await p.waitForTimeout(800); }
      else if (s.op === 'click') { await p.locator('#ajgf button', { hasText: s.text }).first().click(); }
      else if (s.op === 'file') { await p.setInputFiles('#ajgf input[type=file]', s.path); }
      else if (s.op === 'drop') {
        const b64 = fs.readFileSync(s.path).toString('base64');
        await p.evaluate(({ b64, name }) => { const bin = atob(b64), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
          const dt = new DataTransfer(); dt.items.add(new File([u], name, { type: 'application/zip' })); const d = document.querySelector('#ajgf .ajgf-drop');
          d.dispatchEvent(new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true })); }, { b64, name: s.fname || 'update.zip' });
      }
      else if (s.op === 'wait_text') {
        await p.waitForFunction(ts => { const t = (document.querySelector('#ajgf') || {}).innerText || ''; return ts.some(x => t.includes(x)); }, s.text, { timeout: s.timeout || 600000, polling: 500 });
        const t = await panel(); results[name] = s.text.find(x => t.includes(x)); results[name + '_panel'] = t;
      }
      else if (s.op === 'download') {
        const dl = p.waitForEvent('download', { timeout: s.timeout || 300000 });
        await p.locator('#ajgf button', { hasText: s.text }).first().click(); const d = await dl;
        await d.saveAs(s.save); results[name] = d.suggestedFilename();
      }
      else if (s.op === 'intercept') {   // answer requests to other hosts from here (nothing leaves the machine): rules [{match, status, type, b64|body}], default empty 200
        await ctx.route(u => !u.href.startsWith(base) && !/^(data|blob):/.test(u.href), route => {
          const u = route.request().url(), rule = (s.rules || []).find(x => u.includes(x.match));
          if (!rule) return route.fulfill({ status: 200, contentType: 'text/plain', body: '' });
          route.fulfill({ status: rule.status || 200, contentType: rule.type || 'text/plain', body: rule.b64 ? Buffer.from(rule.b64, 'base64') : (rule.body || '') });
        });
      }
      else if (s.op === 'eval') { results[name] = await p.evaluate(s.expr); }
      else if (s.op === 'mark') { await p.evaluate(() => { window.__mark = 1; }); }
      else if (s.op === 'wait_reload') { await p.waitForFunction(() => !window.__mark, null, { timeout: 60000 }); await p.waitForFunction(() => window.__ajgFiles === true, null, { timeout: 60000 }); await p.waitForTimeout(2000); }
      else if (s.op === 'panel') { results[name] = await panel(); }
      else if (s.op === 'wait') { await p.waitForTimeout(s.ms); }
      else if (s.op === 'screenshot') { await p.screenshot({ path: s.path }); }
      else throw new Error('unknown op ' + s.op);
    }
  } catch (e) { results.crash = String(e).slice(0, 600); try { results.crash_panel = await panel(); } catch (x) { } }
  await Promise.all(pending);
  external.forEach(e => { e.failure = failures[e.url] || null; });
  console.log(JSON.stringify({ results, errors, external }));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
