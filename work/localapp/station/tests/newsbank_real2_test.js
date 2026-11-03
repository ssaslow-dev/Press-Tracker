/* The second REAL NewsBank batch (Sammy 2026-11-03, multi3.pdf: 12 stories, 54 pages) through the station page, against two for-Update files: the snapshot's (bc21c9fb)
   and the current master's (0bccc1fc). Licensed text: set AJG_REAL_NB2 to a folder holding multi3.pdf, for_update_snapshot.json and for_update_0bccc1fc.json; without it
   this test is skipped.   AJG_REAL_NB2=DIR node tests/newsbank_real2_test.js [--page dist/index.html] */
const fs = require('fs'), path = require('path');
const H = require('./nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB2;
const FILES = ['for_update_snapshot.json', 'for_update_0bccc1fc.json'];
if (!DIR || !fs.existsSync(path.join(DIR, 'multi3.pdf')) || FILES.some(f => !fs.existsSync(path.join(DIR, f)))) { console.log('SKIP newsbank_real2_test (AJG_REAL_NB2 not set or files absent)'); process.exit(0); }
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const PAGE = arg('page') || path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;
// truth, read from the PDF text: pages, date, source as NewsBank writes it, the outlet the tracker spells it as, section, words, docref; row = the for-Update row it already is; pr = PRJUDGE-v1 verdict
const T = [
  { n: 1, span: '1-2', date: '2026-10-06', src: 'US Fed News (USA)', outlet: 'US Fed News', sec: '', words: 345, d: 'news/1AB23E965A346B78', row: '00038', pr: 'yes', hl: /^CALIFORNIA LEGISLATIVE CENTRAL COAST CAUCUS ISSUES STATEMENT.*SAN DIEGO$/ },
  { n: 2, span: '3-5', date: '2026-10-06', src: 'CE Noticias Financieras: English', outlet: 'CE Noticias Financieras: English', sec: 'News', words: 1339, d: 'news/1AB14299E2B1ED70', row: '00049', pr: 'no', hl: /^Two new lawsuits reignite the debate over Nazi-looted art in the U\.S\.$/ },
  { n: 3, span: '6-7', date: '2026-10-09', src: 'US Fed News (USA)', outlet: 'US Fed News', sec: '', words: 608, d: 'news/1AB28653D2FFFBB0', row: '00031', pr: 'yes', hl: /^STATE APPROVES \$2\.5 MILLION FOR GCC & LIBRARY$/ },
  { n: 4, span: '8-10', date: '2026-09-17', src: 'PR Newswire (USA)', outlet: 'PR Newswire', sec: '', words: 831, d: 'news/1AAB02E35BC74848', row: '00173', pr: 'yes', hl: /^Anheuser-Busch Invests \$21 Million in Los Angeles, CA Facilities, Expands Local Manufacturing Skills Training$/ },
  { n: 5, span: '11-17', date: '2026-09-19', src: 'Targeted News Service (USA)', outlet: 'Targeted News Service', sec: 'States - Government', words: 1784, d: 'news/1AABA1255E992140', row: '00131', pr: 'yes', hl: /^Calif\. Gov\. Newsom Issues Legislative Update on Sept\. 18, 2026$/ },
  { n: 6, span: '18-21', date: '2026-09-19', src: 'LATAM', outlet: 'LATAM', sec: 'International', words: 1384, d: 'news/1AABBB562E2F41E8', row: '00165', pr: 'no', hl: /^Nuevas leyes desatan batalla legal en EEUU por arte saqueado por los nazis$/, au: 'Por DEEPA BHARATH, Associated Press' },
  { n: 7, span: '22-24', date: '2026-09-19', src: 'Associated Press News Service, The', outlet: 'Associated Press News Service, The', sec: 'Domestic', words: 1192, d: 'news/1AABA5B950C2B9C8', row: '00133', pr: 'no', hl: /^New laws trigger a fresh legal fight over Nazi-looted art in Los Angeles and Auschwitz museums$/, au: 'By DEEPA BHARATH, Associated Press' },
  { n: 8, span: '25-27', date: '2026-11-01', src: 'East Bay Times (CA)', outlet: 'East Bay Times', sec: '', words: 0, d: 'image/v2%3A1704477003BED8D8%40AWNB-1AB9BE40AB87C16A%402461346-1AB9BE65EDB41DE5%4017-1AB9BE65EDB41DE5%40', print: true, page: '18', hl: /^Full Page$/ },
  { n: 9, span: '28-30', date: '2026-11-03', src: 'Mercury News, The (San Jose, CA) (CA)', outlet: 'Mercury News, The', sec: '', words: 0, d: 'image/v2%3A17D87B75E9B4E140%40AWNB-1ABA6A41550EB714%402461348-1ABA6A462A3F2E12%4010-1ABA6A462A3F2E12%40', print: true, page: '11', hl: /^Full Page$/ },
  { n: 10, span: '31-37', date: '2026-10-28', src: 'Bakersfield Californian, The: Web Edition Articles (CA)', outlet: 'Bakersfield Californian, The', sec: 'News', words: 2881, d: 'news/1AB8D1C54431E9E0', row: null, pr: 'no', hl: /^Tributes abound for civil rights icon Dolores Huerta$/, au: 'The Bakersfield Californian' },
  { n: 11, span: '38-53', date: '2026-09-10', src: 'Story Is with Elex Michaelson, The [CNN] (USA)', outlet: 'Story Is with Elex Michaelson, The [CNN]', tvOutlet: 'CNN', tvDate: '2026-09-09', sec: 'News; Domestic', words: 6811, d: 'news/1AA8F62D6C707318', row: '00198', pr: 'no', hl: /^Apple Unveils First Foldable iPhone At Product Showcase;.*Aired 1-2a ET$/, au: 'Elex Michaelson, Nic Robertson' },
  { n: 12, span: '54-54', date: '2026-09-30', src: 'Mother Jones', outlet: 'Mother Jones', sec: 'Food', words: 236, d: 'news/1AAF5B6ACD110820', row: '00082', pr: 'no', hl: /^Rural Voters Like MAHA\. They Just Don't Think It's Working\.$/, au: 'Sophie Hurwitz' },
];
const stub = prompt => /^These items come from NewsBank/.test(prompt) ? [...prompt.matchAll(/=== ITEM (\d+)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'x', press_release: 'no', pr_why: 'a reporter’s story', date: '', outlet: '', pub: '', hl: '', topic: 'District / community', media: 'Online news', role: 'Mentioned in story', tone: 'Neutral', twhy: '', author: '', lang: '', hl_en: '', text_en: '' })) : [];
async function one(fuName) {
  console.log('--- for-Update file ' + fuName);
  const X = await H.start(PAGE, stub), page = X.page, tag = '[' + fuName.slice(11, 19) + '] ';
  await H.loadFile(page, path.join(DIR, fuName));
  await H.dropPdf(page, path.join(DIR, 'multi3.pdf'));
  const f = await page.evaluate(() => window.__station.state.nb.files.map(x => ({ status: x.status, note: x.note, warn: x.warn, stories: x.stories, pages: x.pages })));
  check(tag + '54 pages, 12 stories, no mid-page note, no warnings', f[0].status === 'ok' && f[0].stories === 12 && f[0].pages === 54 && !/mid-page/.test(f[0].note) && !(f[0].warn || []).length, JSON.stringify(f[0]));
  const items = await H.items(page), { known } = H.knownDocrefs(path.join(DIR, fuName));
  check(tag + '12 stories read', items.length === 12, items.length);
  const pr = await page.evaluate(() => window.__station.state.nb.items.map(it => PRJudge.judge({ text: it.p.text, title: it.p.headline, outlet: it.p.outlet, claude: { press_release: 'no', pr_why: 'a reporter’s story' } })));
  for (const [i, it] of items.entries()) {
    const t = T[i], c = tag + 'story ' + t.n + ' (' + t.src.slice(0, 22) + '): ';
    check(c + 'pages ' + t.span + ' and no band', it.pages === t.span && !it.bands.length, it.pages + ' ' + JSON.stringify(it.bands));
    check(c + 'headline', t.hl.test(it.hl), it.hl);
    check(c + 'date ' + t.date + ', source as NewsBank writes it, section, word count', it.date === t.date && it.outlet === t.src && it.section === t.sec && (t.print || it.words === t.words), JSON.stringify([it.date, it.outlet, it.section, it.words]));
    if (t.tvOutlet) { const tv = await page.evaluate(k => { const x = window.__station.state.nb.items.find(y => y.key === k); return x.tv && { network: x.tv.network, show: x.tv.show, date_pt: x.tv.date_pt }; }, it.key); check(c + 'NewsBank’s source line is not the tracker’s outlet: the list shows CNN (the show goes to the Audio & video row) and the Pacific date ' + t.tvDate, !!tv && tv.network === t.tvOutlet && tv.date_pt === t.tvDate && tv.show === 'The Story Is with Elex Michaelson', JSON.stringify(tv)); const shown = await page.evaluate(() => [...document.querySelectorAll('#nbBody tr')].map(r => r.textContent).find(x => /Michaelson/.test(x)) || ''); check(c + 'the list row reads CNN and 2026-09-09', /2026-09-09/.test(shown) && /CNN/.test(shown), shown.slice(0, 160)); }
    else check(c + 'outlet in the tracker’s spelling: ' + t.outlet, it.outlet_clean === t.outlet, it.outlet_clean);
    check(c + 'docref ' + t.d, it.docref === t.d, it.docref);
    if (t.au) check(c + 'author', it.author === t.au, it.author);
    check(c + 'no parse flags', !it.flags.length, JSON.stringify(it.flags));
    if (t.print) { check(c + 'a print page (a picture, no story text): kept as a print original, to be matched to its story or listed as an Unlinked print page', it.kind === 'print_page' && it.st === 'print_page' && it.body_words === 0 && it.pages.split('-')[1] - it.pages.split('-')[0] === 2, it.kind + ' ' + it.st + ' ' + it.pages); continue; }
    if (t.row) { const k = known.get(t.d.toLowerCase()); check(c + 'the for-Update file has it as row ' + t.row, !!k && k.aid === t.row, JSON.stringify(k)); check(c + 'already in the tracker (same NewsBank link)', it.st === 'known' && /same NewsBank link/.test(it.why), it.st + ' ' + it.why); }
    else check(c + 'not in the tracker: new', it.st === 'new' && !known.has(t.d.toLowerCase()) && it.pdf > 1000, it.st + ' ' + it.why);
    check(c + 'press release = ' + t.pr + ' with a reason (the “no” rests on a STUBBED Claude answer plus the absence of text signals; no real Claude call is made here)', pr[i].v === t.pr && !!pr[i].why && (t.pr === 'no' || pr[i].by === 'text'), JSON.stringify(pr[i]));
  }
  check(tag + 'no two stories share a key, a docref or a story file', new Set(items.map(i => i.key)).size === 12 && new Set(items.map(i => i.docref)).size === 12 && new Set(items.filter(i => i.pdfid).map(i => i.pdfid)).size === items.filter(i => i.pdfid).length);
  check(tag + 'every story has a PDF of its own: the new one, the 2 print pages (print originals) and the 9 known ones (extra original copies, ORIGCOPIES-v1)', items.filter(i => i.pdfid).length === 12 && items[9].pdfid, JSON.stringify(items.filter(i => i.pdfid).map(i => i.n)));
  const sm = await page.textContent('#nbSummary'); check(tag + 'summary: 1 new, 9 already in the tracker, 2 print pages', /12 stories: 1 new, 9 already in the tracker, 2 print pages/.test(sm), sm);
  // add the one new story: its row
  await page.uncheck('#nbLinks').catch(() => {});
  await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 90000 });
  const run = await page.evaluate(() => { const r = window.__station.state.nb.lastRun; return { rows: r.rows, counts: r.counts, print_pages: r.print_pages, left: r.left, items: r.items, doc: r.doc }; });
  check(tag + 'one story added, no reprint rows, none left out', run.counts.stories === 1 && run.counts.rows === 1 && run.left.length === 0, JSON.stringify(run.counts));
  const row = run.rows[0];
  check(tag + 'its row: outlet in the tracker’s spelling, NewsBank link in the sheet’s form, date, section, words', row['Outlet'] === 'Bakersfield Californian, The' && row['NewsBank article link'] === 'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=news/1AB8D1C54431E9E0' && row['Date'] === '2026-10-28' && row['Section'] === 'News' && row['Word count'] === 2881, JSON.stringify([row['Outlet'], row['NewsBank article link'], row['Date'], row['Section'], row['Word count']]));
  check(tag + 'its row: the citation keeps NewsBank’s own words (feed label and all); Press release is not Yes, and the decision is kept', /Bakersfield Californian, The: Web Edition Articles \(CA\)\. Available from NewsBank/.test(row['Newsbank APA citation (article)']) && row['Press release'] !== 'Yes' && row._pr && row._pr.v === 'no', JSON.stringify([row['Newsbank APA citation (article)'].slice(0,200), row._pr]));
  check(tag + 'the two print pages are carried (not just listed): each with its PDF file, as unconfirmed Unlinked print page rows (the intern confirms a story in the box)', run.print_pages.length === 2 && run.print_pages.every(p => /docref=image\/v2%3A/.test(p.url) && p.as === 'unlinked' && /^files\/nb-/.test(p.file)) && /East Bay/.test(run.print_pages[0].outlet) && run.doc.print_rows.length === 2, JSON.stringify(run.print_pages.map(p => [p.outlet, p.as, p.file])));
  check(tag + 'print rows: Date, Date source print edition, Page, the print-page link and the print-page citation (NewsBank’s own page numbers)', run.doc.print_rows.every(x => x['Date source'] === 'print edition' && /docref=image\/v2%3A/.test(x['NewsBank print-page link']) && /p\. ?\d+|Available from NewsBank/.test(x['Newsbank APA citation (print page)']) && x['Page']) && run.doc.print_rows[0]['Date'] === '2026-11-01' && run.doc.print_rows[0]['Page'] === '18' && run.doc.print_rows[1]['Page'] === '11', JSON.stringify(run.doc.print_rows.map(x => [x['Outlet'], x['Date'], x['Page']])));
  check(tag + 'ORIGCOPIES-v1: all 9 known stories carry their PDF as an extra original copy of the row they matched (the for-Update file here does not say which rows already hold a NewsBank PDF, so the PC decides)', run.doc.extra_copies.length === 9 && run.doc.extra_copies.every(x => /^\d{5}$/.test(x.row) && /^kn-/.test(x._page)) && run.doc.extra_copies.map(x => x.row).sort().join() === T.filter(t => t.row).map(t => t.row).sort().join(), JSON.stringify(run.doc.extra_copies.map(x => x.row)));
  const ids = run.rows.map(r => r['Tracker story code']).concat(run.rows.map(r => r['Article ID']));
  check(tag + 'row ids unique, not the id of "no link"', new Set(ids).size === ids.length && !ids.includes('jg-1c9dc5'), JSON.stringify(ids));
  check(tag + 'no outside request, no page error', X.outside.length === 0 && X.errors.length === 0, JSON.stringify([X.outside, X.errors.slice(0, 3)]));
  await X.close();
}
(async () => { for (const f of FILES) await one(f); console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); process.exit(C.failed ? 1 : 0); })().catch(e => { console.error(e); process.exit(2); });
