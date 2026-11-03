// SINCE-v1 + NOSCHED-v1 (UPDFIX-v1, 2026-10-30): the Update dialog's optional "Since" date, the run doc's since / searched_to, and the end of the scheduled task
// (no fire_trigger anywhere; the page says to ask Claude in chat). Playwright against the built page, fake mcp (every search returns nothing).
// Usage: NODE_PATH=/opt/npm-tools/node_modules node build/tests/update_js/test_since_js.js [page.html]   Exit 0 = pass or skipped.
const fs = require('fs'), path = require('path'); const L = path.resolve(__dirname, '../../..');
const page = path.resolve(process.argv[2] || path.join(L, 'work', 'build_last', 'lib', 'index.html'));
let chromium; try { chromium = require('playwright').chromium; } catch (e) { console.log('SKIPPED: playwright not installed'); process.exit(0); }
if (!fs.existsSync(page)) { console.log('SKIPPED: no built page at ' + page); process.exit(0); }
let fails = 0; const ok = (c, m, i) => { console.log((c ? 'PASS ' : 'FAIL ') + m + (c ? '' : '  -- ' + i)); if (!c) fails++; };
const dayMinus = (d, n) => new Date(Date.parse(d) - n * 864e5).toISOString().slice(0, 10);
async function open(br, cfg) {
  const pg = await (await br.newContext({ viewport: { width: 1400, height: 1000 } })).newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.addInitScript(cfg => {
    window.__sets = []; window.__calls = [];
    const st = window.setTimeout; window.setTimeout = (f, d, ...a) => st(f, (d || 0) > 100 ? 1 : d, ...a);
    const col = name => ({ onSnapshot(cb) { st(() => cb({ docs: [] }), 30); return () => {}; }, doc(id) { return { set: async d => { window.__sets.push([name, id, JSON.parse(JSON.stringify(d))]); }, delete: async () => {} }; } });
    window.claude = { use: async n => { if (n === 'db') return { collection: col };
      if (n === 'mcp') return { callTool: async (server, tool, input) => { window.__calls.push([server, tool, JSON.parse(JSON.stringify(input || {}))]); if (cfg && cfg.epaper && tool === 'search' && !window.__epDone) { window.__epDone = true; return { payload: { results: [{ url: 'https://epaper.singtaousa.com/flippingbook/epaper_la/2026/20261020/3/', title: 'Sing Tao page 3', date: new Date().toISOString().slice(0, 10), snippet: '蓋博 AB 1127', publisher: 'Sing Tao Daily' }] } }; } return { payload: { results: [] } }; } };
      return null; } };
  }, cfg || {});
  await pg.goto('file://' + page); await pg.waitForFunction(() => !!document.querySelector('#runFind'), null, { timeout: 30000 }); await pg.waitForTimeout(800);
  pg.errs = errs; return pg;
}
const openDialog = async (pg, sel) => { await pg.evaluate(s => document.querySelector(s).click(), sel || '#runFind'); await pg.waitForSelector('#rcYes', { state: 'visible', timeout: 5000 }); };
async function runWith(br, since, cfg) {
  const pg = await open(br, cfg); await openDialog(pg);
  if (since !== undefined) await pg.fill('#rcSince', since);
  await pg.evaluate(() => document.querySelector('#rcYes').click());
  await pg.waitForFunction(() => !document.querySelector('#runFind').classList.contains('busy') && window.__sets.some(s => s[0] === 'runs' && s[2].status === 'done'), null, { timeout: 170000 }).catch(() => {});
  await pg.waitForTimeout(300);
  const r = await pg.evaluate(() => { const runs = window.__sets.filter(s => s[0] === 'runs'); return { doc: runs.length ? runs[runs.length - 1][2] : null, calls: window.__calls, body: (document.querySelector('#updBody') || document.body).innerText, LAST: typeof LAST !== 'undefined' ? LAST : '', def: typeof sinceDefault === 'function' ? sinceDefault() : '' }; });
  r.errs = pg.errs; await pg.context().close(); return r;
}
(async () => {
  const br = await chromium.launch(); const today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' });
  // 1. the dialog
  let pg = await open(br); await openDialog(pg);
  const d1 = await pg.evaluate(() => { const i = document.querySelector('#rcSince'), w = document.querySelector('#rcSinceWrap'); return { type: i && i.type, val: i && i.value, vis: !!w && !w.hidden, max: i && i.max, min: i && i.min, cs: i && getComputedStyle(i).borderRadius }; });
  ok(d1.type === 'date' && d1.val === '' && d1.vis && d1.min === '1990-01-01' && d1.max === today, 'dialog: optional native date input, blank, min 1990-01-01, max today', JSON.stringify(d1));
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(100);
  await openDialog(pg, '#runRefresh'); ok(await pg.evaluate(() => document.querySelector('#rcSinceWrap').hidden), 'dialog: no Since field on "Refresh from files"');
  await pg.keyboard.press('Escape'); await openDialog(pg);
  // 2. validation
  for (const [v, re, label] of [[dayMinus(today, -2), /future/, 'a future date'], ['1989-12-31', /1990/, 'a date before 1990']]) {
    await pg.fill('#rcSince', v); await pg.evaluate(() => document.querySelector('#rcYes').click()); await pg.waitForTimeout(150);
    const e = await pg.evaluate(() => ({ err: document.querySelector('#rcErr').hidden ? '' : document.querySelector('#rcErr').innerText, open: !document.querySelector('#rcScrim').hidden, calls: window.__calls.length, sets: window.__sets.length }));
    ok(re.test(e.err) && e.open && e.calls === 0 && e.sets === 0, `validation: ${label} is refused with a message and nothing starts`, JSON.stringify(e)); }
  await pg.context().close();
  // 3. blank = the current behaviour (also gives the usual start for the checks below)
  const B = await runWith(br, '');
  const sB = B.calls.filter(c => c[1] === 'search'); const def = B.doc && B.doc.since;
  ok(B.doc && B.doc.since_manual === false && /^\d{4}-\d\d-\d\d$/.test(def) && B.doc.searched_to === today, 'blank: since is the usual start, not manual, searched_to advances', JSON.stringify(B.doc && { s: B.doc.since, m: B.doc.since_manual, to: B.doc.searched_to }));
  ok(sB.some(c => !c[2].after_date) && sB.some(c => c[2].after_date), 'blank: site searches still go without after_date, fresh passes with it (unchanged)', '');
  ok(!B.errs.length, 'no page errors (default run)', B.errs.join(' | '));
  // 4. a run with the date 30 days back
  const d30 = dayMinus(today, 30);
  const A = await runWith(br, d30);
  ok(A.doc && A.doc.since === d30 && A.doc.since_manual === true, 'run doc: since = the chosen date, since_manual true', JSON.stringify(A.doc && { s: A.doc.since, m: A.doc.since_manual, st: A.doc.status }));
  const sA = A.calls.filter(c => c[1] === 'search');
  /* DATEFILTER-v1 (2026-11-03): the podcast-page group goes without a date (TinyFish returns nothing for that shape with one) and is filtered by date afterwards */
  const noDateOk = c => /site:open\.spotify\.com\/episode/.test(String(c[2].query || ''));
  ok(sA.length > 20 && sA.every(c => noDateOk(c) ? !c[2].after_date : (c[2].after_date && c[2].after_date >= d30)), `search: every one of ${sA.length} searches (site searches too) carries after_date >= the chosen date, except the undated podcast-page group`, JSON.stringify(sA.filter(c => !(noDateOk(c) ? !c[2].after_date : (c[2].after_date && c[2].after_date >= d30))).slice(0, 2).map(c => [c[2].after_date, c[2].query])));
  ok(sA.every(c => !c[2].page), 'search: no older pages of an outlet sweep are read', '');
  ok(A.doc && A.doc.searched_to === '', `searched_to (S3): blank after a manual date ${d30} (the usual start is ${def}); a thinner plan never claims the window as searched`, JSON.stringify(A.doc && A.doc.searched_to));
  ok(!A.calls.some(c => c[1] === 'fire_trigger') && !A.calls.some(c => c[0] === 'Claude Code Remote') && /ask Claude in chat/.test(A.body) && /save the last run to the sheet/.test(A.body), 'NOSCHED: no Claude Code Remote call; the panel says to ask Claude in chat to "save the last run to the sheet"', A.body.slice(0, 300));
  ok(!A.errs.length, 'no page errors (manual run)', A.errs.join(' | '));
  const nB = +(String(B.doc.failed).split(' of ')[1]), nA = +(String(A.doc.failed).split(' of ')[1]);
  const nums = {}; for (const n of [7, 90]) { const R = await runWith(br, dayMinus(today, n)); nums[n] = +(String(R.doc.failed).split(' of ')[1]); }
  console.log(`PLAN SIZE (searches run, with paging and pickups): default (since ${def}) ${nB} vs since 7 days ${nums[7]}, 30 days ${nA}, 90 days ${nums[90]}`);
  ok(nA > 0 && nB > 0 && nA < nB && nums[7] < nB && nums[90] < nB && nums[7] <= nA && nA <= nums[90], 'plan: a recent date plans fewer searches than the default (only outlets active in 24 months get a site search; no deep paging), more for a longer window', JSON.stringify({ nB, d7: nums[7], d30: nA, d90: nums[90] }));
  // 5. a manual date later than the usual start never advances searched_to
  const late = await runWith(br, today);
  ok(late.doc && late.doc.since === today && late.doc.searched_to === '', 'searched_to: a manual date of today (later than the usual start) leaves searched_to blank so no gap is claimed', JSON.stringify(late.doc && { s: late.doc.since, to: late.doc.searched_to, def }));
  // S2: an e-paper find is shown in the panel and listed in the run doc, not dropped silently
  const EP = await runWith(br, '', { epaper: true });
  ok(EP.doc && Array.isArray(EP.doc.print_pages) && EP.doc.print_pages.length === 1 && /singtaousa/.test(EP.doc.print_pages[0].url) && /print page/i.test(EP.body), 'S2: the e-paper find is in the run doc (print_pages) and the panel says "1 print page to clip"', JSON.stringify(EP.doc && EP.doc.print_pages) + ' | ' + EP.body.slice(0, 200));
  await br.close(); console.log('FAILS ' + fails); process.exit(fails ? 1 : 0);
})().catch(e => { console.log('FAIL exception ' + e); process.exit(1); });
