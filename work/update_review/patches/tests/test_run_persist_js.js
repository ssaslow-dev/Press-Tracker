// RUNPERSIST-v1 (REQ-2): the Update run writes a progress doc before searching, shows a failed save, never fires the sheet task without a run doc,
// and ends with a saved doc (status done / error) even when something throws.
// Usage: NODE_PATH=/opt/npm-tools/node_modules node build/tests/update_js/test_run_persist_js.js [page.html]   (default work/build_last/lib/index.html)
// Exit 0 = pass or skipped, 1 = fail.
const fs = require('fs'), path = require('path'); const L = path.resolve(__dirname, '../../..');
const page = path.resolve(process.argv[2] || path.join(L, 'work', 'build_last', 'lib', 'index.html'));
let chromium; try { chromium = require('playwright').chromium; } catch (e) { console.log('SKIPPED: playwright not installed'); process.exit(0); }
if (!fs.existsSync(page)) { console.log('SKIPPED: no built page at ' + page); process.exit(0); }
let fails = 0; const ok = (c, m, i) => { console.log((c ? 'PASS ' : 'FAIL ') + m + (c ? '' : '  -- ' + i)); if (!c) fails++; };
const today = new Date().toISOString().slice(0, 10);
async function scenario(br, name, cfg) {
  const pg = await (await br.newContext({ viewport: { width: 1400, height: 1000 } })).newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.addInitScript(cfg => {
    window.__sets = []; window.__calls = []; window.__dbFail = !!cfg.dbFail; window.__cfg = cfg; window.__n = { search: 0, fetch: 0 };
    const st = window.setTimeout; window.setTimeout = (f, d, ...a) => st(f, (d || 0) > 100 ? 1 : d, ...a);   // the 2.1 s TinyFish gate and retry waits would take half an hour
    const col = name => ({ onSnapshot(cb) { st(() => cb({ docs: [] }), 30); return () => {}; },
      doc(id) { return { set: async d => { if (window.__dbFail) throw { code: 'tool_error' }; window.__sets.push([name, id, JSON.parse(JSON.stringify(d)), window.__calls.length]); }, delete: async () => {} }; } });
    const hit = { payload: { results: [{ url: 'https://example-news.test/a', title: 'Jesse Gabriel bill advances', snippet: 'Assemblymember Jesse Gabriel, D-Encino, said …', date: cfg.today }] } };
    window.claude = { use: async n => {
      if (n === 'db') return { collection: col };
      if (n === 'mcp') return { callTool: async (server, tool, input) => {
        window.__calls.push([server, tool, input]);
        if (tool === 'fire_trigger') return {};
        if (cfg.mcp === 'hit') {
          if (tool === 'search') { return window.__n.search++ === 0 ? hit : { payload: { results: [] } }; }
          if (tool === 'fetch_content') { window.__n.fetch++; if (cfg.fetchThrows) throw new Error('boom'); return { payload: { results: [] } }; }
          return { payload: { results: [] } };
        }
        throw { code: 'server_not_connected' }; } };
      return null; } };
  }, Object.assign({ today }, cfg));
  await pg.goto('file://' + page); await pg.waitForFunction(() => !!document.querySelector('#runFind'), null, { timeout: 30000 }); await pg.waitForTimeout(800);
  await pg.evaluate(() => document.querySelector('#runFind').click()); await pg.waitForSelector('#rcYes', { state: 'visible', timeout: 5000 }); await pg.evaluate(() => document.querySelector('#rcYes').click());
  // wait for the run to finish: no step in the "run" state and the button no longer busy
  await pg.waitForFunction(() => !document.querySelector('#runFind').classList.contains('busy') && window.__sets.some(s => s[0] === 'runs'), null, { timeout: 120000 }).catch(() => {});
  await pg.waitForTimeout(500);
  const r = await pg.evaluate(() => ({ sets: window.__sets, calls: window.__calls.map(c => [c[0], c[1]]), body: (document.querySelector('#updBody') || document.body).innerText, ls: (() => { try { return localStorage.getItem('jg-runs-pending'); } catch (e) { return null; } })(), busy: document.querySelector('#runFind').classList.contains('busy'),
    steps: [...document.querySelectorAll('.ra-step, [data-ra-step], #raSteps li')].map(e => e.innerText) }));
  r.errs = errs; await pg.context().close(); return r;
}
(async () => {
  const br = await chromium.launch();
  // A: empty search world
  let A = await scenario(br, 'A', { mcp: 'down' });
  const runsA = A.sets.filter(s => s[0] === 'runs'), firstTf = A.calls.findIndex(c => c[0] === 'TinyFish');
  ok(runsA.length >= 2 && runsA[0][2].status === 'running' && (firstTf < 0 || runsA[0][3] <= firstTf), 'A: first runs doc is status running, written before any TinyFish call', JSON.stringify({ n: runsA.length, first: runsA[0] && runsA[0][2], at: runsA[0] && runsA[0][3], firstTf }));
  const fin = runsA[runsA.length - 1] && runsA[runsA.length - 1][2];
  ok(fin && fin.status === 'done' && 'failed' in fin && Array.isArray(fin.unconfirmed), 'A: final runs doc has status done, failed, unconfirmed[]', JSON.stringify(fin).slice(0, 300));
  ok(!A.calls.some(c => c[1] === 'fire_trigger'), 'A: nothing found -> no fire_trigger', JSON.stringify(A.calls.slice(-3)));
  ok(!A.errs.length, 'A: no page errors', A.errs.join(' | '));
  // B: shared store down
  const B = await scenario(br, 'B', { mcp: 'down', dbFail: true });
  ok(/Run log unavailable/.test(B.body), 'B: find step says "Run log unavailable"', B.body.slice(0, 400));
  ok(!B.calls.some(c => c[1] === 'fire_trigger'), 'B: no fire_trigger without a saved run doc', JSON.stringify(B.calls.slice(-3)));
  ok(/spreadsheet update was not started/.test(B.body), 'B: sheet step is a warning that the update was not started', B.body.slice(0, 600));
  let ent = []; try { ent = JSON.parse(B.ls || '[]'); } catch (e) {}
  ok(ent.length === 1 && /^run-/.test(ent[0].id), 'B: localStorage jg-runs-pending holds one entry with the run id', B.ls);
  ok(!B.errs.length, 'B: no page errors', B.errs.join(' | '));
  // C: one hit, page fetch throws a plain Error
  const C = await scenario(br, 'C', { mcp: 'hit', fetchThrows: true });
  const runsC = C.sets.filter(s => s[0] === 'runs'), finC = runsC.length ? runsC[runsC.length - 1][2] : null;
  ok(finC && finC.status === 'done', 'C: run ends with a status done doc', JSON.stringify(finC).slice(0, 300));
  const mention = finC && JSON.stringify([finC.rows, finC.unconfirmed, finC.left]).includes('example-news.test');
  ok(mention, 'C: the find is in rows, unconfirmed or left, not silently gone', JSON.stringify(finC && { rows: (finC.rows || []).length, unconfirmed: finC.unconfirmed, left: finC.left }));
  ok(!C.busy, 'C: button not left busy', '');
  ok(!C.errs.length, 'C: no page errors', C.errs.join(' | '));
  await br.close(); console.log('FAILS ' + fails); process.exit(fails ? 1 : 0);
})().catch(e => { console.log('FAIL exception ' + e); process.exit(1); });
