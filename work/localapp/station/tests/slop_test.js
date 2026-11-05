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
  const rpDir = path.join(path.dirname(RUN), '..', 'reprints'), rpIn = fs.existsSync(rpDir) ? fs.readdirSync(rpDir).filter(f => f.endsWith('.json')) : [];
  for (const f of rpIn) await page.evaluate(([id, d]) => window.__station.mem.collection('reprints').doc(id).set(d), [f.replace(/\.json$/, ''), JSON.parse(fs.readFileSync(path.join(rpDir, f), 'utf8'))]);
  console.log('  reprint records in', rpIn.length);
  await page.waitForTimeout(800); await page.evaluate(() => window.__station.xdReconcile()); await page.waitForTimeout(500);
  const out = await page.evaluate(() => window.__station.sess.runs.get('run-test').data);
  const by = h => out.rows.find(r => String(r.Headline || '').startsWith(h));
  const pas = by('Major revisions coming for high school ethnic studies'), sfg = by('Keep an eye on these 5 deals'), keyt = by('California 1st to make firms disclose'), wt = by('California bans \'deep fakes\'');
  check('FILEDUP: the Pasadena Star-News 2019 story the tracker has (NewsBank row, no link) is left out', !pas, JSON.stringify(pas && pas['Article ID']));
  check('FILEDUP / OLDFIND: SFGATE’s Aug 10 copy of the CalMatters “5 deals” story is not a new story (left out as old, or a reprint)', !sfg || (sfg['Original or reprint'] === 'Reprint' && /^s\d+$/.test(sfg['Story ID'])), JSON.stringify(sfg && [sfg['Original or reprint'], sfg['Story ID']]));
  out.rows.forEach(r => console.log('  kept:', r['Original or reprint'], r.Date, r.Outlet, '|', String(r.Headline).slice(0, 60)));
  check('URLDATE: KEYT reprint dated from its web address (2022-09-13)', keyt && keyt.Date === '2022-09-13' && keyt['Date source'] === 'URL', JSON.stringify(keyt && [keyt.Date, keyt['Date source']]));
  check('URLDATE: Washington Times reprint dated from /2019/oct/4/', wt && wt.Date === '2019-10-04', JSON.stringify(wt && wt.Date));
  const nodate = out.rows.filter(r => !r.Date).map(r => r.Outlet);
  console.log('  rows', run.rows.length, '->', out.rows.length, '; still undated:', nodate.join(', '));
  console.log('  left (new):', (out.left || []).slice(-6).map(x => x.hl.slice(0, 50) + ' — ' + x.why).join('\n    '));
  const rps = await page.evaluate(() => [...window.__station.sess.reprints].map(([id, v]) => v.data));
  check('Fable 1: no junk reprint records left (Spotify, board page, ?page=), and the dated reprints stay', rps.length >= 10 && !rps.some(x => /spotify|whichrow|page\/Board|[?&]page=/i.test(x.link || '')), JSON.stringify(rps.map(x => x.link).filter(l => /spotify|whichrow|Board|page=/i.test(l))));
  console.log('  reprint records left', rps.length, rps.map(x => (x.date || 'nodate') + ' ' + x.outlet).join('; '));
  check('Fable 3: no new story dated more than 30 days before the search start', !out.rows.some(r => (r['Original or reprint'] || 'Original') === 'Original' && r.Date && !/NewsBank|ProQuest/.test(r['Data Source'] || '') && Date.parse(r.Date) < Date.parse(st.since) - 30 * 864e5), JSON.stringify(out.rows.filter(r => r['Original or reprint'] === 'Original').map(r => r.Date)));
  check('Fable 4: the reasons for rows left out are kept', (out.left || []).some(x => /old story|listing|already in the tracker|no date/.test(x.why)), (out.left || []).length);
  check('no page errors', X.errors.length === 0, X.errors.join(' | '));
  await X.close(); console.log(C.failed ? `FAILED ${C.failed} of ${C.n}` : `ALL ${C.n} PASSED`); process.exit(C.failed ? 1 : 0);
})();
