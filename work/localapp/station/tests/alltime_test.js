/* ALLTIME-v1: "Search all time" sends every search without a date limit, tags the run doc all_time, and turns itself off afterwards; the normal Update keeps its date.
     AJG_FU=for_update.json node tests/alltime_test.js */
const H = require('./nb/real_harness.js'), path = require('path');
const FU = process.env.AJG_FU; if (!FU) { console.log('SKIP alltime_test (AJG_FU not set)'); process.exit(0); }
const C = H.makeChecker(), check = C.check;
const mcpStub = function (tool, input) { (window.__inputs = window.__inputs || []).push({ tool, after: input && (input.after_date || (input.queries || [])[0] && input.queries[0].after_date) || '' , input: JSON.stringify(input).slice(0, 300) }); return { payload: { results: [] } }; };
async function run(page, allTime) {
  await page.evaluate(() => { window.__inputs = []; });
  if (allTime) { await page.click('#stAllTime'); await page.click('#stAllTime'); }
  else await page.evaluate(() => document.getElementById('updGo').click());
  await page.waitForFunction(() => [...window.__station.sess.runs.values()].some(v => v.data && v.data.status === 'done' && !v.seen) , null, { timeout: 600000 });
  await page.waitForTimeout(1500);
  const out = await page.evaluate(() => { const r = [...window.__station.sess.runs.values()].filter(v => !v.seen); r.forEach(v => { v.seen = true; }); return { runs: r.map(v => ({ all_time: !!v.data.all_time, since: v.data.since, status: v.data.status })), inputs: window.__inputs.filter(x => x.tool === 'search'), flag: !!window.__stationAllTime }; });
  return out;
}
(async () => {
  const X = await H.start(path.join(H.ST, 'dist', 'index.html'), () => [], { images: 4, mcpStub: mcpStub.toString() }), page = X.page; await H.loadFile(page, FU);
  await page.waitForTimeout(800);
  check('the Search all time button is there and enabled after the file loads', await page.locator('#stAllTime').isEnabled());
  const a = await run(page, true);
  const dated = a.inputs.filter(x => /after_date/.test(x.input) && !/"query":"\\"[^\\]+\\""/.test(x.input));   // release-copy searches (a quoted release sentence) keep the release date: a copy can't predate the release
  console.log('  all-time searches', a.inputs.length, 'with a date filter', dated.length, dated.slice(0, 2).map(x => x.input));
  check('all-time run: many searches, none with a date filter', a.inputs.length > 50 && dated.length === 0, dated.length);
  check('all-time run: the run doc is marked all_time', a.runs.length === 1 && a.runs[0].all_time, JSON.stringify(a.runs));
  check('all-time mode turns itself off after the run', !a.flag);
  const b = await run(page, false);
  const dated2 = b.inputs.filter(x => /after_date/.test(x.input));
  console.log('  normal searches', b.inputs.length, 'with a date filter', dated2.length);
  check('normal Update afterwards: searches keep their date filter and the run is not all_time', dated2.length > 10 && b.runs.length === 1 && !b.runs[0].all_time, JSON.stringify(b.runs) + ' ' + dated2.length);
  check('no page errors', X.errors.length === 0, X.errors.join(' | '));
  await X.close(); console.log(C.failed ? `FAILED ${C.failed} of ${C.n}` : `ALL ${C.n} PASSED`); process.exit(C.failed ? 1 : 0);
})();
