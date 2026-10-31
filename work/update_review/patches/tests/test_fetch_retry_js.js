// FETCHRETRY-v1 (REQ-6): a thrown fetch_content for a batch of candidate pages is retried once (batches of 5); a page that still cannot be read is skipped
// with its own reason (not "Gabriel isn't named"), counted in U.failed, and a page that was read and does not name him keeps the old reason.
// Usage: NODE_PATH=/opt/npm-tools/node_modules node build/tests/update_js/test_fetch_retry_js.js [page.html]   (default work/build_last/lib/index.html)
const fs = require('fs'), path = require('path'); const L = path.resolve(__dirname, '../../..');
const page = path.resolve(process.argv[2] || path.join(L, 'work', 'build_last', 'lib', 'index.html'));
let chromium; try { chromium = require('playwright').chromium; } catch (e) { console.log('SKIPPED: playwright not installed'); process.exit(0); }
if (!fs.existsSync(page)) { console.log('SKIPPED: no built page at ' + page); process.exit(0); }
let fails = 0; const ok = (c, m, i) => { console.log((c ? 'PASS ' : 'FAIL ') + m + (c ? '' : '  -- ' + i)); if (!c) fails++; };
const today = new Date().toISOString().slice(0, 10), URL = 'https://example-news.test/a';
const NEW_REASON = 'Its page could not be fetched (TinyFish error), so it was not judged. Try again later.';
async function scenario(br, cfg) {
  const pg = await (await br.newContext({ viewport: { width: 1400, height: 1000 } })).newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.addInitScript(cfg => {
    window.__sets = []; window.__calls = []; window.__att = 0;
    const st = window.setTimeout; window.setTimeout = (f, d, ...a) => st(f, (d || 0) > 100 ? 1 : d, ...a);
    const col = name => ({ onSnapshot(cb) { st(() => cb({ docs: [] }), 30); return () => {}; }, doc(id) { return { set: async d => { window.__sets.push([name, id, JSON.parse(JSON.stringify(d))]); }, delete: async () => {} }; } });
    // the snippet says only "Gabriel said ..." (passes the any-script filter, but not the full-name test); the page names him in full
    const hit = { payload: { results: [{ url: cfg.url, title: 'Housing bill advances in Sacramento', snippet: 'Gabriel said the measure would move to the Senate floor next week.', date: cfg.today }] } };
    const page = { payload: { results: [{ url: cfg.url, final_url: cfg.url, title: 'Housing bill advances in Sacramento', published_date: cfg.today + 'T12:00:00Z',
      text: cfg.pageText, html: '<article><p>' + cfg.pageText + '</p></article>' }] } };
    let nSearch = 0;
    window.claude = { use: async n => {
      if (n === 'db') return { collection: col };
      if (n === 'mcp') return { callTool: async (server, tool, input) => {
        window.__calls.push([server, tool, input]);
        if (tool === 'fire_trigger') return {};
        if (tool === 'search') return nSearch++ === 0 ? hit : { payload: { results: [] } };
        if (tool === 'fetch_content' && (input.urls || []).includes(cfg.url)) {
          window.__att++;
          if (cfg.failFirst === 'always' || window.__att <= cfg.failFirst) throw { code: 'tool_error', message: 'TinyFish 500' };   // not retryable: tfCall does not retry it itself
          return page;
        }
        return { payload: { results: [] } }; } };
      return null; } };
  }, Object.assign({ today, url: URL }, cfg));
  await pg.goto('file://' + page); await pg.waitForFunction(() => !!document.querySelector('#runFind'), null, { timeout: 30000 }); await pg.waitForTimeout(800);
  await pg.evaluate(() => document.querySelector('#runFind').click()); await pg.waitForSelector('#rcYes', { state: 'visible', timeout: 5000 }); await pg.evaluate(() => document.querySelector('#rcYes').click());
  await pg.waitForFunction(() => !document.querySelector('#runFind').classList.contains('busy') && window.__sets.some(s => s[0] === 'runs'), null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(600);
  const r = await pg.evaluate(() => ({ sets: window.__sets, att: window.__att, body: (document.querySelector('#updBody') || document.body).textContent,   // textContent: the left-out list sits in a closed <details>
     busy: document.querySelector('#runFind').classList.contains('busy') }));
  r.errs = errs; await pg.context().close(); return r;
}
const lastRun = r => { const a = r.sets.filter(s => s[0] === 'runs'); return a.length ? a[a.length - 1][2] : null; };
const kept = (r, d) => !!d && JSON.stringify([d.rows, d.unconfirmed, d.stories]).includes('example-news.test') || /Housing bill advances/.test(r.body) && !/could not be fetched/.test(r.body);
(async () => {
  const br = await chromium.launch();
  const full = 'Assemblymember Jesse Gabriel, D-Encino, said the housing bill would move to the Senate floor next week, according to the California Assembly. ' + 'More text about the bill. '.repeat(40);
  // 1: first attempt throws, the retry reads the page naming him
  const A = await scenario(br, { failFirst: 1, pageText: full }), dA = lastRun(A);
  ok(A.att >= 2, '1: the page is fetched again after the thrown error', 'attempts ' + A.att);
  ok(dA && dA.status === 'done' && kept(A, dA), '1: the find is kept (rows / unconfirmed), not dropped as "not naming Gabriel"', JSON.stringify(dA && { rows: (dA.rows || []).length, unconf: dA.unconfirmed, left: dA.left }));
  ok(dA && !(dA.left || []).some(x => /example-news|Housing bill/.test(x.hl + x.outlet)), '1: it is not in the left-out list', JSON.stringify(dA && dA.left));
  const nf = d => +String(d && d.failed).split(' of ')[0];   // failures from the fake search world are the baseline (1 and 2 below are compared to it)
  const C0 = await scenario(br, { failFirst: 0, pageText: full }), base = nf(lastRun(C0));
  ok(nf(dA) === base, '1: the retry cleared the failure (failed ' + (dA && dA.failed) + ' = clean-fetch run ' + (lastRun(C0) && lastRun(C0).failed) + ')', dA && dA.failed);
  // 2: both attempts throw
  const B = await scenario(br, { failFirst: 'always', pageText: full }), dB = lastRun(B);
  const lx = dB && (dB.left || []).find(x => /example-news|Housing bill/.test(x.hl + x.outlet));
  ok(B.att === 2, '2: exactly one retry (2 attempts)', 'attempts ' + B.att);
  ok(lx && lx.why === NEW_REASON, '2: the final run doc `left` carries the new reason', JSON.stringify(dB && dB.left));
  ok(!(dB.rows || []).length && !(dB.unconfirmed || []).length, '2: nothing was added or proposed', JSON.stringify({ rows: dB.rows, unconf: dB.unconfirmed }));
  ok(nf(dB) === base + 1, '2: the unread page is counted in failed, once per page (' + dB.failed + ' vs ' + base + ' clean)', dB.failed);
  ok(B.body.includes(NEW_REASON) || /could not be fetched/.test(B.body), '2: the panel (#updBody) shows the new reason', B.body.slice(0, 500));
  ok(!/isn.t named in the page text/.test(JSON.stringify(dB.left)), '2: the old misleading reason is not used for it', '');
  // 3: the page WAS read and does not name him -> the old reason stays
  const C = await scenario(br, { failFirst: 0, pageText: 'The city council met on Tuesday to talk about parking meters and street sweeping. ' + 'Nothing else happened. '.repeat(40) }), dC = lastRun(C);
  const lc = dC && (dC.left || []).find(x => /example-news|Housing bill/.test(x.hl + x.outlet));
  ok(lc && /isn.t named/.test(lc.why), '3: a fetched page that does not name him keeps the old reason', JSON.stringify(dC && dC.left));
  ok(!A.errs.length && !B.errs.length && !C.errs.length, 'no page errors', [A.errs, B.errs, C.errs].flat().join(' | '));
  await br.close(); console.log('FAILS ' + fails); process.exit(fails ? 1 : 0);
})().catch(e => { console.log('FAIL exception ' + e); process.exit(1); });
