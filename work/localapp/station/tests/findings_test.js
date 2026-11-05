/* FINDINGS 1-5 of Sammy's second real folder (2026-11-05), on synthetic runs in the built station page (no Claude, no TinyFish):
   1 rows with the same link never appear twice; 2 reprints of a folded story are repointed to the kept story (also in another run); 3 the tracker's spelling of an outlet;
   4 an outlet name or "| junk" is not an author; 5 a "Calmatters:" headline prefix or a CalMatters byline credit files the row as a reprint of the CalMatters story (else a note).
     AJG_REAL_NB2=DIR (with for_update_0bccc1fc.json) node tests/findings_test.js */
const fs = require('fs'), path = require('path');
const H = require('./nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB2, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json');
if (!DIR || !fs.existsSync(FU)) { console.log('SKIP findings_test (AJG_REAL_NB2 not set)'); process.exit(0); }
const PAGE = path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;
const stub = () => [];
const W = (id, at, rows, extra) => Object.assign({ at, mode: 'find', status: 'done', stories: rows.filter(r => r['Original or reprint'] === 'Original').map(r => r['Tracker story code']).filter(Boolean), reprints: [], rows, left: [], searched_to: '' }, extra || {});
let N = 0;
const R = (n, o) => Object.assign({ 'Article ID': 'NEW-' + n, 'Story ID': 'sNEW-' + n, 'Original or reprint': 'Original', 'Data Source': 'Web search (TinyFish)', Date: '2026-11-03', Outlet: 'Valley Gazette Test', Headline: 'Headline number ' + n, 'Publisher link': 'https://www.valleygazette-test.com/2026/11/' + n, 'Author / byline': 'Dana Whitfield', 'Tracker story code': 'jg-' + String(n).padEnd(6, 'a').slice(0, 6) }, o || {});
const RP = (n, story, sid, o) => R(n, Object.assign({ 'Original or reprint': 'Reprint', 'Story ID': sid, 'Tracker story code': '', Outlet: 'Other Daily ' + n, 'Publisher link': 'https://other-' + n + '.test/story' }, o || {}));
const put = (page, id, doc) => page.evaluate(([i, d]) => window.__station.mem.collection('runs').doc(i).set(d), [id, doc]);
const runs = async page => { await page.waitForTimeout(1800); return Object.fromEntries(await page.evaluate(() => [...window.__station.sess.runs].map(([id, v]) => [id, v.data]))); };
(async () => {
  const X = await H.start(PAGE, stub, { images: 8 }), page = X.page; await H.loadFile(page, FU);
  /* 1. the same 3 reprint rows in two runs (an old run and a newer one) and the same Original twice: one copy of each link */
  const a1 = R('a1'), rp1 = RP('p1', 'jg-a1aaaa', a1['Story ID']), rp2 = RP('p2', 'jg-a1aaaa', a1['Story ID']);
  await put(page, 'run-old', W('run-old', '2026-11-04T10:00:00Z', [a1, rp1, rp2], { reprints: [{ story: 'jg-a1aaaa', outlet: rp1.Outlet }, { story: 'jg-a1aaaa', outlet: rp2.Outlet }] }));
  const a1b = R('a1b', { 'Publisher link': a1['Publisher link'] }), rp1b = RP('p1b', 'jg-a1baaa', a1b['Story ID'], { 'Publisher link': rp1['Publisher link'] }), rp2b = RP('p2b', 'jg-a1baaa', a1b['Story ID'], { 'Publisher link': rp2['Publisher link'] });
  await put(page, 'run-new', W('run-new', '2026-11-05T10:00:00Z', [a1b, rp1b, rp2b], { reprints: [{ story: 'jg-a1baaa', outlet: rp1b.Outlet }, { story: 'jg-a1baaa', outlet: rp2b.Outlet }] }));
  let rs = await runs(page); const all = Object.values(rs).flatMap(r => r.rows), links = all.map(r => r['Publisher link']);
  check('1. rows with the same link are in the folder once (3 rows, not 6)', all.length === 3 && new Set(links).size === 3, JSON.stringify(all.map(r => r['Article ID'])));
  check('1. the kept rows are the earliest run’s, the reprints still point at their Original', rs['run-old'].rows.length === 3 && rs['run-new'].rows.length === 0 && rs['run-old'].rows.filter(r => r['Original or reprint'] === 'Reprint').every(r => r['Story ID'] === a1['Story ID']));
  /* 2. a folded story's reprints in ANOTHER run are repointed */
  const web = R('w2', { 'Publisher link': 'https://calm.test/prop2', Outlet: 'CalMatters', Headline: 'Californians vote to grow the state savings' });
  const lk = RP('l1', 'jg-w2aaaa', web['Story ID']), kp = RP('l2', 'jg-w2aaaa', web['Story ID']);
  await put(page, 'run-web', W('run-web', '2026-11-04T09:00:00Z', [web], { reprints: [] }));
  await put(page, 'run-reps', W('run-reps', '2026-11-04T09:30:00Z', [lk, kp], { reprints: [{ story: web['Tracker story code'], outlet: lk.Outlet }, { story: web['Tracker story code'], outlet: kp.Outlet }] }));
  const nbRow = R('n2', { 'Data Source': 'NewsBank', Outlet: 'CALmatters', Headline: 'Californians vote to grow the state savings', 'Publisher link': 'https://calm.test/prop2', 'NewsBank article link': 'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=news/ZZ1' });
  await put(page, 'run-nb', W('run-nb', '2026-11-05T11:00:00Z', [nbRow], {}));
  rs = await runs(page);
  const kept = Object.values(rs).flatMap(r => r.rows).filter(r => /^(NEW-w2|NEW-n2)$/.test(r['Article ID']));
  const reps = Object.values(rs).flatMap(r => r.rows).filter(r => /^NEW-l[12]$/.test(r['Article ID']));
  check('2. the two sources found the same story: shown once', kept.length === 1, JSON.stringify(kept.map(r => r['Article ID'])));
  check('2. every reprint of the folded story now points at the kept row’s story (also the ones in another run)', reps.length === 2 && reps.every(r => r['Story ID'] === kept[0]['Story ID']), JSON.stringify(reps.map(r => r['Story ID'])) + ' vs ' + kept[0]['Story ID']);
  check('2. the run documents list the reprints under the kept story code', Object.values(rs).flatMap(r => r.reprints || []).filter(x => x.story === kept[0]['Tracker story code']).length >= 2 && !Object.values(rs).flatMap(r => r.reprints || []).some(x => x.story === (kept[0]['Article ID'] === 'NEW-w2' ? 'jg-n2aaaa' : 'jg-w2aaaa')), JSON.stringify(Object.values(rs).flatMap(r => r.reprints || [])));
  /* 3. + 4. spelling and author */
  const t1 = R('t1', { Outlet: 'Sfgate', 'Author / byline': 'Bakersfield Californian, The' }), t2 = R('t2', { Outlet: 'Epoch Times', 'Author / byline': 'James Salazar | Examiner Staff Writer' });
  await put(page, 'run-tidy', W('run-tidy', '2026-11-05T12:00:00Z', [t1, t2]));
  rs = await runs(page); const tr = Object.fromEntries(rs['run-tidy'].rows.map(r => [r['Article ID'], r]));
  check('3. outlets use the tracker’s spelling (Sfgate -> SFGATE, Epoch Times -> Epoch Times, The)', tr['NEW-t1'].Outlet === 'SFGATE' && tr['NEW-t2'].Outlet === 'Epoch Times, The', JSON.stringify([tr['NEW-t1'].Outlet, tr['NEW-t2'].Outlet]));
  check('3. every spelling of CalMatters becomes the one the tracker uses most (here CALmatters)', (await page.evaluate(() => ['Calmatters', 'CalMatters', 'CALMATTERS'].map(x => window.__nb.respell(x)))).every(x => x === 'CALmatters'), '');
  check('4. an outlet name as author is cleared; "| junk" after a byline is cut', tr['NEW-t1']['Author / byline'] === '' && tr['NEW-t2']['Author / byline'] === 'James Salazar', JSON.stringify([tr['NEW-t1']['Author / byline'], tr['NEW-t2']['Author / byline']]));
  /* 5. syndication */
  const cm = R('c1', { Outlet: 'CalMatters', Headline: 'Prop 2 passes: voters boost the state rainy day fund', 'Author / byline': 'Yue Stella Yu', 'Publisher link': 'https://calmatters.test/prop2' });
  const s1 = R('c2', { Outlet: 'LAist', Headline: 'Rainy day fund passes', 'Author / byline': 'Yue Stella Yu', 'Publisher link': 'https://laist.test/rainy' });
  const s2 = R('c3', { Outlet: 'San Mateo Daily Journal', Headline: 'Save for California’s Future Act', 'Author / byline': 'Yue Stella Yu CalMatters', 'Publisher link': 'https://smdj.test/prop2' });
  const s3 = R('c4', { Outlet: 'SFGATE', Headline: 'Calmatters: Keep an eye on these 5 deals', 'Author / byline': '', Date: '2026-10-20', 'Publisher link': 'https://sfgate.test/5deals' });
  await put(page, 'run-syn', W('run-syn', '2026-11-05T13:00:00Z', [cm, s1, s2, s3]));
  rs = await runs(page); const sy = Object.fromEntries(rs['run-syn'].rows.map(r => [r['Article ID'], r]));
  check('5. a CalMatters credit in the byline files the row as a Reprint of the CalMatters story in the folder', sy['NEW-c3'] && sy['NEW-c3']['Original or reprint'] === 'Reprint' && sy['NEW-c3']['Story ID'] === cm['Story ID'], JSON.stringify(sy['NEW-c3'] && [sy['NEW-c3']['Original or reprint'], sy['NEW-c3']['Story ID']]));
  check('5. a "Calmatters:" headline prefix with no CalMatters story near it stays an Original with a note saying where it comes from', sy['NEW-c4'] && sy['NEW-c4']['Original or reprint'] === 'Original' && /syndicated from CalMatters/.test(sy['NEW-c4']['Team note'] || ''), JSON.stringify(sy['NEW-c4'] && sy['NEW-c4']['Team note']));
  check('5. the CalMatters story itself stays an Original; an ordinary row of the same author with no credit and no prefix is left alone', sy['NEW-c1']['Original or reprint'] === 'Original' && sy['NEW-c2']['Original or reprint'] === 'Original');
  check('a second check changes nothing (the notes are not added twice)', await (async () => { const before = JSON.stringify(rs); await page.evaluate(() => window.__station.xdReconcile()); const after = JSON.stringify(await runs(page)); return before === after; })());
  check('no page error, nothing outside', X.errors.length === 0 && X.outside.length === 0, JSON.stringify([X.errors, X.outside]));
  await X.close();
  console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
