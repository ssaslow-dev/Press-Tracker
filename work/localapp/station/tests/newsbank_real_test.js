/* The first REAL NewsBank batch (Sammy 2026-11-03, multi.pdf: 3 stories, 7 pages, page-aligned) through the station page. The file is licensed text: set AJG_REAL_NB to a
   folder holding multi.pdf and for_update.json (the for-Update file of the snapshot workbook); without it this test is skipped.
     AJG_REAL_NB=DIR node tests/newsbank_real_test.js [--page dist/index.html] */
const fs = require('fs'), path = require('path');
const H = require('./nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB;
if (!DIR || !fs.existsSync(path.join(DIR, 'multi.pdf')) || !fs.existsSync(path.join(DIR, 'for_update.json'))) { console.log('SKIP newsbank_real_test (AJG_REAL_NB not set or files absent)'); process.exit(0); }
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page') || path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;
const TRUTH = [
  { span: '1-2', hl: "CALIFORNIA LEGISLATIVE CENTRAL COAST CAUCUS ISSUES STATEMENT ON PRESIDENT TRUMP'S DANGEROUS REMARKS AGAINST LOS ANGELES AND SAN DIEGO", date: '2026-10-06', source: 'US Fed News (USA)', section: '', words: 345, docref: 'news/1AB23E965A346B78', aid: '00038', pr: 'yes' },
  { span: '3-5', hl: 'Two new lawsuits reignite the debate over Nazi-looted art in the U.S.', date: '2026-10-06', source: 'CE Noticias Financieras: English', section: 'News', words: 1339, docref: 'news/1AB14299E2B1ED70', aid: '00049', pr: 'no' },
  { span: '6-7', hl: 'STATE APPROVES $2.5 MILLION FOR GCC & LIBRARY', date: '2026-10-09', source: 'US Fed News (USA)', section: '', words: 608, docref: 'news/1AB28653D2FFFBB0', aid: '00031', pr: 'yes' },
];
(async () => {
  // Claude's stub says press_release "no" for everything: the text signals alone must find the two US Fed News releases
  const T = await H.start(PAGE, prompt => /^These items come from NewsBank/.test(prompt) ? [...prompt.matchAll(/=== ITEM (\d+)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'x', press_release: 'no', pr_why: 'stub', date: '', outlet: '', pub: '', hl: '', topic: 'Other / roundup', media: 'Newspaper', role: 'Mentioned in story', tone: 'Neutral', twhy: '', author: '', lang: '', hl_en: '', text_en: '' })) : []);
  const { page } = T;
  await H.loadFile(page, path.join(DIR, 'for_update.json'));
  await H.dropPdf(page, path.join(DIR, 'multi.pdf'));
  const files = await page.evaluate(() => window.__station.state.nb.files.map(f => ({ status: f.status, note: f.note, warn: f.warn, stories: f.stories, pages: f.pages })));
  check('7 pages, 3 stories', files[0].status === 'ok' && files[0].stories === 3 && files[0].pages === 7, JSON.stringify(files[0]));
  check('no "starts mid-page" note, no warning about headers or leftovers', !/mid-page/.test(files[0].note) && !(files[0].warn || []).length, JSON.stringify(files[0]));
  const items = await H.items(page), { known } = H.knownDocrefs(path.join(DIR, 'for_update.json'));
  check('3 stories read', items.length === 3, items.length);
  items.forEach((it, i) => {
    const t = TRUTH[i], c = 'story ' + (i + 1) + ': ';
    check(c + 'pages ' + t.span, it.pages === t.span, it.pages);
    check(c + 'headline', it.hl === t.hl, JSON.stringify(it.hl));
    check(c + 'date, source, section, word count', it.date === t.date && it.outlet === t.source && it.section === t.section && it.words === t.words, JSON.stringify([it.date, it.outlet, it.section, it.words]));
    check(c + 'docref from the openurl link, and the sheet-form article link', it.docref === t.docref && it.link === 'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=' + t.docref, it.docref + ' ' + it.link);
    const k = known.get(t.docref.toLowerCase());
    check(c + 'the for-Update file has this link as row ' + t.aid, !!k && k.aid === t.aid, JSON.stringify(k));
    check(c + 'already in the tracker (same NewsBank link)', it.st === 'known' && /same NewsBank link/.test(it.why), it.st + ' ' + it.why);
    check(c + 'no parse flags, no bands', !it.flags.length && !it.bands.length, JSON.stringify([it.flags, it.bands]));
  });
  check('unique story keys and no shared story file name', new Set(items.map(i => i.key)).size === 3 && new Set(items.map(i => i.docref)).size === 3);
  check('nothing to add: no row in the table is offered, the button says so', await page.evaluate(() => !document.querySelector('#nbBody input[type=checkbox]')) && await page.$eval('#nbAdd', b => b.disabled), '');
  check('summary says 3 already in the tracker', /3 stories: 3 already in the tracker/.test(await page.textContent('#nbSummary')), await page.textContent('#nbSummary'));
  check('no junk rows: every headline is a headline, every outlet an outlet', items.every(i => i.hl.length > 20 && i.hl.length < 200 && !/Available from|Date:|openurl/.test(i.hl + i.outlet)));
  // PRJUDGE-v1 on the real text: the two US Fed News items are releases (found in their text), the CE Noticias article is not
  const pr = await page.evaluate(() => window.__station.state.nb.items.map(it => PRJudge.judge({ text: it.p.text, title: it.p.headline, outlet: it.p.outlet, claude: { press_release: 'no', pr_why: 'stub' } })));
  pr.forEach((j, i) => check('story ' + (i + 1) + ': press release = ' + TRUTH[i].pr + ' with a reason', j.v === TRUTH[i].pr && (j.v === 'no' || (j.why && j.by === 'text')), JSON.stringify(j)));
  console.log('   reasons: ' + pr.map(j => j.v + ' (' + j.by + '): ' + j.why).join(' | '));
  check('no worker, no outside request, no page error', T.outside.length === 0 && T.errors.length === 0, JSON.stringify([T.outside, T.errors.slice(0, 3)]));
  console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); await T.close(); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
