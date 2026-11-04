/* Station side of the for-Update print tab (applied in the station and PC build; PRINTPAGES-v1): with kind-P rows (and a `files` column) in the for-Update file, a print page already listed on the Unlinked print pages tab
   is "already in the tracker as a print page", and a known story whose row already holds a NewsBank PDF gets no extra copy. Licensed text: AJG_REAL_NB2 (multi3.pdf, for_update_0bccc1fc.json).
   AJG_REAL_NB2=DIR node tests/print_known_test.js */
const fs = require('fs'), path = require('path'), os = require('os');
const H = require('./nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB2, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json');
if (!DIR || !fs.existsSync(path.join(DIR, 'multi3.pdf')) || !fs.existsSync(FU)) { console.log('SKIP print_known_test (AJG_REAL_NB2 not set or files absent)'); process.exit(0); }
const C = H.makeChecker(), check = C.check;
(async () => {
  const fu = JSON.parse(fs.readFileSync(FU, 'utf8')), cols = fu.rows.cols;
  fu.rows.cols = cols.concat(['files']); fu.rows.rows = fu.rows.rows.map(r => r.concat([/^(00038|00049)$/.test(r[0]) ? 'nb' + r[0] + 'r-sx.pdf' : '']));   // two rows already hold a NewsBank PDF
  const eb = 'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=image/v2%3A1704477003BED8D8%40AWNB-1AB9BE40AB87C16A%402461346-1AB9BE65EDB41DE5%4017-1AB9BE65EDB41DE5%40';
  const row = []; cols.forEach((c, i) => { row[i] = ''; }); row[cols.indexOf('aid')] = '05999'; row[cols.indexOf('kind')] = 'P'; row[cols.indexOf('outlet')] = 'East Bay Times'; row[cols.indexOf('date')] = '2026-11-01'; row[cols.indexOf('links')] = [eb]; row.push('');
  fu.rows.rows.push(row);
  const tmp = path.join(os.tmpdir(), 'fu_p_' + process.pid + '.json'); fs.writeFileSync(tmp, JSON.stringify(fu));
  const X = await H.start(path.join(H.ST, 'dist', 'index.html'), () => []);
  await H.loadFile(X.page, tmp); await H.dropPdf(X.page, path.join(DIR, 'multi3.pdf'));
  const it = await X.page.evaluate(() => window.__station.state.nb.items.map(x => ({ n: x.batch.index, st: x.screen.status, why: x.screen.why, pdf: !!x.pdf, inc: x.include })));
  check('the East Bay page is "already in the tracker as a print page (05999)", not offered again', it[7].st === 'known' && /print page \(05999\)/.test(it[7].why) && !it[7].pdf, JSON.stringify(it[7]));
  check('the Mercury News page (not on the tab) is still a print page to confirm', it[8].st === 'print_page' && it[8].pdf, JSON.stringify(it[8]));
  check('rows 00038 and 00049 already hold a NewsBank PDF: no extra copy (no PDF cut, not ticked)', !it[0].pdf && !it[0].inc && !it[1].pdf && !it[1].inc, JSON.stringify([it[0], it[1]]));
  check('the other known stories (their rows hold no NewsBank PDF in this file) keep their PDF as an extra copy', [2, 3, 4, 5, 6, 10, 11].every(i => it[i].st === 'known' && it[i].pdf && it[i].inc), JSON.stringify([2, 3, 4, 5, 6, 10, 11].map(i => [it[i].n, it[i].pdf])));
  await X.close(); fs.unlinkSync(tmp); console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
