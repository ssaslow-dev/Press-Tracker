/* NBTV-v1 on the REAL multi3 batch: story 11 (the CNN transcript "Story Is with Elex Michaelson, The [CNN]", already in the tracker as 00198 dated 2026-09-09 while NewsBank says
   2026-09-10) is handled as the Update button handles a TV find. Licensed text: set AJG_REAL_NB2 to the folder with multi3.pdf and for_update_0bccc1fc.json; else skipped.
   Two parts: (1) the transcript read by NBTV.detect, and the Pacific-date rule against the tracker's own row 00198; (2) the story run as NEW (its NewsBank link removed from a
   scratch copy of the for-Update file) through the page: its proposed row.   AJG_REAL_NB2=DIR node tests/newsbank_tv_real_test.js [--page dist/index.html] */
const fs = require('fs'), path = require('path'), os = require('os');
const H = require('./nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB2, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json');
if (!DIR || !fs.existsSync(path.join(DIR, 'multi3.pdf')) || !fs.existsSync(FU)) { console.log('SKIP newsbank_tv_real_test (AJG_REAL_NB2 not set or files absent)'); process.exit(0); }
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page') || path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;
const stub = prompt => /^These items come from NewsBank/.test(prompt) ? [...prompt.matchAll(/=== ITEM (\d+)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'x', press_release: 'no', pr_why: 'a reporter’s story', date: '', outlet: '', pub: '', hl: '', topic: 'Food & nutrition', media: 'Online news', role: 'Mentioned in story', tone: 'Neutral', twhy: '', author: '', lang: '', hl_en: '', text_en: '' })) : [];
(async () => {
  // a scratch copy of the for-Update file in which the CNN story is not yet in the tracker
  const raw = fs.readFileSync(FU, 'utf8'), fu = JSON.parse(raw);
  const row = fu.rows.rows.find(r => String(r[0]) === '00198'), dcol = fu.rows.cols.indexOf('date');
  const scratch = path.join(os.tmpdir(), 'tv_fu_' + process.pid + '.json');
  fs.writeFileSync(scratch, raw.replace(/1AA8F62D6C707318/gi, 'ZZZZZZZZZZZZZZZZ'));
  const X = await H.start(PAGE, stub), page = X.page;
  await H.loadFile(page, scratch); await H.dropPdf(page, path.join(DIR, 'multi3.pdf'));
  const info = await page.evaluate(() => { const it = window.__station.state.nb.items.find(x => /Michaelson/.test(x.p.outlet)); return { st: it.screen.status, why: it.screen.why, tv: NBTV.detect(it.p), date: it.p.date, outlet: it.p.outlet }; });
  const tv = info.tv;
  check('the CNN transcript is read as broadcast: TV, network CNN, show un-inverted', tv && tv.medium === 'TV' && tv.network === 'CNN' && tv.show === 'The Story Is with Elex Michaelson', JSON.stringify(tv && [tv.medium, tv.network, tv.show]));
  check('NewsBank says 2026-09-10 and "Aired 1-2a ET"; the Pacific air date is 2026-09-09 at 22:00 PT (REVIEW4-v1 F1)', info.date === '2026-09-10' && tv.air_text === '1-2a ET' && tv.date_pt === '2026-09-09' && tv.air_clock === '22:00 PT', JSON.stringify([info.date, tv.air_text, tv.date_pt, tv.air_clock]));
  check('that is the date the tracker already has for 00198 (' + (row && row[dcol]) + ')', !!row && String(row[dcol]).slice(0, 10) === tv.date_pt, row && row[dcol]);
  check('his role from the transcript: guest -> Featured, his speech -> Quoted; markers 01:23:28 and 01:25:23 (as 00198 has)', tv.role === 'guest' && tv.depth === 'Featured' && tv.quoted === true && tv.marks.includes('01:23:28') && tv.marks.includes('01:25:23'), JSON.stringify([tv.role, tv.depth, tv.quoted, tv.marks]));
  check('the story is new once its link is not in the tracker (so the run below adds it)', info.st === 'new', info.st + ' ' + info.why);
  await page.uncheck('#nbLinks').catch(() => {});
  await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 90000 });
  const run = await page.evaluate(() => { const r = window.__station.state.nb.lastRun; return { rows: r.rows, counts: r.counts }; });
  const cnn = run.rows.find(r => r['Medium'] === 'TV' || /Michaelson|CNN/.test(r['Outlet'] || ''));
  check('its row exists', !!cnn, run.rows.map(r => r['Outlet']));
  if (cnn) {
    check('row: Medium TV although Claude said Online news; Format Broadcast segment', cnn['Medium'] === 'TV' && cnn['Format'] === 'Broadcast segment', JSON.stringify([cnn['Medium'], cnn['Format']]));
    check('row: Date is the Pacific air date 2026-09-09, Year 2026, Date source "air date (Pacific)"', cnn['Date'] === '2026-09-09' && cnn['Year'] === 2026 && cnn['Date source'] === 'air date (Pacific)' && cnn._date_src === 'airdate_pt', JSON.stringify([cnn['Date'], cnn['Year'], cnn['Date source'], cnn._date_src]));
    check('row: Mention depth Featured, Quoted Yes (REVIEW4-v1 F3, F4)', cnn['Mention depth'] === 'Featured' && cnn['Quoted'] === 'Yes', JSON.stringify([cnn['Mention depth'], cnn['Quoted']]));
    check('row: an Audio & video row (_av): Broadcast segment, CNN, show, guest, 22:00 PT, transcript full', cnn._av && cnn._av['Item type'] === 'Broadcast segment' && cnn._av.Network === 'CNN' && cnn._av.Channel === 'CNN' && cnn._av['Show/program'] === 'The Story Is with Elex Michaelson' && cnn._av['His role'] === 'guest' && cnn._av['Air time'] === '22:00 PT' && cnn._av['Air/publish date'] === '2026-09-09' && cnn._av['Transcript kind'] === 'full', JSON.stringify(cnn._av));
    check('row: the Team note carries the source time, the Pacific date and the headline warning; the NewsBank source line check stays', /source time 2026-09-10 1-2a ET; Pacific date 2026-09-09/.test(cnn['Team note']) && /episode rundown/.test(cnn['Team note']) && /SHOWNET-v1/.test(cnn['Team note']), cnn['Team note']);
    check('row: still a NewsBank row (Data Source, link, Press release not Yes)', cnn['Data Source'] === 'Newsbank' && /docref=news\/1AA8F62D6C707318/i.test(cnn['NewsBank article link']) && cnn['Press release'] !== 'Yes' && cnn._pr && cnn._pr.v === 'no', JSON.stringify([cnn['Data Source'], cnn['NewsBank article link'], cnn._pr]));
  }
  const bk = run.rows.find(r => /Bakersfield/.test(r['Outlet'] || ''));
  check('the newspaper story in the same batch is untouched by the TV handling (Medium from Claude, Format Article, NewsBank date)', bk && bk['Medium'] === 'Online news' && bk['Format'] === 'Article' && bk['Date'] === '2026-10-28' && !bk._av, bk && JSON.stringify([bk['Medium'], bk['Format'], bk['Date'], bk._av]));
  check('no outside request, no page error', X.outside.length === 0 && X.errors.length === 0, JSON.stringify([X.outside, X.errors.slice(0, 3)]));
  await X.close(); fs.unlinkSync(scratch);
  console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
