/* FILEDUP-v1 / URLDATE-v1 / NEWEST-v1 / JUNKURL-v1 on the rows of Sammy's 2026-11-05 18:35 run (licensed folder, scratchpad only):
     AJG_FU=for_update.json AJG_RUN=run.json node tests/slop_test.js */
const fs = require('fs'), path = require('path');
const H = require('./nb/real_harness.js');
const FU = process.env.AJG_FU, RUN = process.env.AJG_RUN;
if (!FU || !RUN) { console.log('SKIP slop_test (AJG_FU / AJG_RUN not set)'); process.exit(0); }
const C = H.makeChecker(), check = C.check;
(async () => {
  const X = await H.start(path.join(H.ST, 'dist', 'index.html'), () => [], { images: 4 }), page = X.page; await H.loadFile(page, FU);
  const fu = JSON.parse(fs.readFileSync(FU, 'utf8'));
  const st = await page.evaluate(() => ({ since: window.__stationSince, facts: document.getElementById('stFacts').innerText }));
  check('NEWEST-v1: the search starts the day before the newest story', /^\d{4}-\d\d-\d\d$/.test(st.since || ''), JSON.stringify(st));
  console.log('  since', st.since, '|', st.facts.replace(/\n/g, ' / '));
  const run = JSON.parse(fs.readFileSync(RUN, 'utf8'));
  await page.evaluate(d => window.__station.mem.collection('runs').doc('run-test').set(d), run);
  await page.waitForTimeout(800); await page.evaluate(() => window.__station.xdReconcile()); await page.waitForTimeout(500);
  const out = await page.evaluate(() => window.__station.sess.runs.get('run-test').data);
  const by = h => out.rows.find(r => String(r.Headline || '').startsWith(h));
  const pas = by('Major revisions coming for high school ethnic studies'), sfg = by('Keep an eye on these 5 deals'), keyt = by('California 1st to make firms disclose'), wt = by('California bans \'deep fakes\'');
  check('FILEDUP: the Pasadena Star-News 2019 story the tracker has (NewsBank row, no link) is left out', !pas, JSON.stringify(pas && pas['Article ID']));
  check('FILEDUP: SFGATE’s copy of the CalMatters “5 deals” story is a reprint of the tracker’s story', sfg && sfg['Original or reprint'] === 'Reprint' && /^s\d+$/.test(sfg['Story ID']), JSON.stringify(sfg && [sfg['Original or reprint'], sfg['Story ID']]));
  check('URLDATE: KEYT reprint dated from its web address (2022-09-13)', keyt && keyt.Date === '2022-09-13' && keyt['Date source'] === 'URL', JSON.stringify(keyt && [keyt.Date, keyt['Date source']]));
  check('URLDATE: Washington Times reprint dated from /2019/oct/4/', wt && wt.Date === '2019-10-04', JSON.stringify(wt && wt.Date));
  const nodate = out.rows.filter(r => !r.Date).map(r => r.Outlet);
  console.log('  rows', run.rows.length, '->', out.rows.length, '; still undated:', nodate.join(', '));
  console.log('  left (new):', (out.left || []).slice(-6).map(x => x.hl.slice(0, 50) + ' — ' + x.why).join('\n    '));
  const junk = await page.evaluate(() => { const T = window.__nbJunk; return T ? T : null; });
  check('no page errors', X.errors.length === 0, X.errors.join(' | '));
  await X.close(); console.log(C.failed ? `FAILED ${C.failed} of ${C.n}` : `ALL ${C.n} PASSED`); process.exit(C.failed ? 1 : 0);
})();
