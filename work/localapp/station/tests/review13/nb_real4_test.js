/* NEWSBANK_AUDIT_13: failing tests for the top findings on the real multi4.pdf batch (85 pages: 13 text stories, 14 "Full Page" print pages).
   Claude is a FAKE (canned answers that say what is really printed on the pages, read by the auditor); the page is the built station dist/index.html.
   Licensed text: AJG_REAL_NB4 names a folder with multi4.pdf and for_update_0bccc1fc.json; without it this test is SKIPPED.
     AJG_REAL_NB4=DIR node tests/review13/nb_real4_test.js
   Expected to FAIL until the station is fixed (the checks say what should happen). */
const fs = require('fs'), path = require('path');
const H = require('../nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB4, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json');
if (!DIR || !fs.existsSync(path.join(DIR, 'multi4.pdf')) || !fs.existsSync(FU)) { console.log('SKIP review13/nb_real4_test (AJG_REAL_NB4 not set or files absent)'); process.exit(0); }
const PAGE = path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;

/* Claude's answers, from what the pages really show. The article texts are taken from the batch's own NewsBank text records of the same stories (set on window.__truth
   after the drop), so no licensed text sits in this file. window.__scn 1 = headlines as printed; 3 = the Oct 25 headline with NewsBank's kicker "2026 elections - ". */
const stub = (prompt, o) => {
  const T = window.__truth || {}, scn = window.__scn || 1;
  if (/^These items come from NewsBank/.test(prompt)) return [...prompt.matchAll(/=== ITEM (\d+)\nURL: (.*)\nPage title: (.*)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'x', press_release: /MAYOR BASS HIGHLIGHTS/.test(m[3]) ? 'yes' : 'no', pr_why: 'x', date: '', outlet: '', pub: '', hl: '', topic: 'District / community', media: 'Newspaper', role: 'Mentioned in story', tone: 'Neutral', twhy: '', author: '', lang: /recibe 22 millones/.test(m[3]) ? 'Spanish' : '', hl_en: /recibe 22 millones/.test(m[3]) ? 'Sepulveda Basin receives $22 million' : '', text_en: '' }));
  if (!/^You are reading a scanned page/.test(prompt)) return [];
  const m = /Outlet: (.*?)\. Date: (\d{4}-\d{2}-\d{2})\. Page: (.*?)\.\n/.exec(prompt); if (!m) return { readable: false, articles: [] };
  const outlet = m[1], date = m[2], page = m[3];
  const art = (hl, byline, section, pg, text, extra) => Object.assign({ headline: hl, byline, section, page: pg, text, continues: '', continued_from: '', names_gabriel: /Gabriel/.test(text), confidence: 'high', box: { x: 0.04, y: 0.03, w: 0.92, h: 0.55 }, name_sentences: (text.match(/[^.!?]*Gabriel[^.!?]*[.!?]/g) || []).map(x => x.trim()) }, extra || {});
  if (date === '2026-10-25') return { readable: true, articles: [art(scn === 3 ? '2026 elections - Term limits shake up runs for Senate, Assembly' : 'Term limits shake up runs for Senate, Assembly', 'By Linh Tat', '2026 ELECTIONS', '14', T.termlimits)] };
  if (date === '2026-10-27' && page === '3') return { readable: true, articles: [art('Sepulveda Basin gets $22M in funding', 'By Teresa Liu', 'SAN FERNANDO VALLEY', '3', T.basin_p3 + '\n\nAssemblymember Jesse Gabriel speaks as Los Angeles Mayor Karen Bass and Councilmember Imelda Padilla look on during the event.', { continues: 'See BASIN on Page A4' })] };
  if (date === '2026-10-27' && page === '4') return { readable: true, articles: [art('BASIN', '', '', '4', T.basin_p4 + '\n\nLos Angeles leaders Jesse Gabriel, Mayor Karen Bass, Imelda Padilla and Celeste Rodriguez sign a ceremonial check for $22 million in state funding.', { continued_from: 'From Page 3' })] };
  const upf = 'California is now on track to be the first state to create a front-of-package label to help consumers identify foods in the grocery store aisles that are not ultraprocessed. Gov. Gavin Newsom signed Assembly Bill 2244 into law on Monday. "Parents shouldn\'t need a Ph.D. in chemistry to understand what they\'re feeding their kids," said Assemblymember Jesse Gabriel (D-Encino), author of Assembly Bill 2244. Last year, researchers with USC\'s Keck School of Medicine published a study that found that an increase in ultraprocessed food intake was associated with a higher risk of prediabetes.';
  if (/East Bay Times|Mercury News/.test(outlet)) return { readable: true, articles: [art("California will add 'Non-Ultraprocessed Certified' seal to foods. What that means", 'By Karen Garcia, Los Angeles Times', '', /East/.test(outlet) ? 'B6' : 'B3', upf)] };
  if (/Santa Cruz/.test(outlet)) return { readable: true, articles: [art("Calif. creates 'Non-Ultraprocessed Certified' food label and standard", 'By Karen Garcia, Los Angeles Times', '', 'B2', upf)] };
  if (/Oroville|Enterprise-Record/.test(outlet)) return { readable: true, articles: [art("California will add 'Non-Ultraprocessed Certified' seal to foods", 'By Karen Garcia, Los Angeles Times', '', 'B2', upf)] };
  if (date === '2026-11-04' && page === '9') return { readable: true, articles: [art('Early mail-in ballots tend to favor incumbents', 'By Teresa Liu', '2026 ELECTIONS', '9', T.ballots)] };
  return { readable: true, articles: [] };
};
async function fresh(scn) {
  const X = await H.start(PAGE, stub, { images: 3 }), page = X.page;
  await H.loadFile(page, FU); await H.dropPdf(page, path.join(DIR, 'multi4.pdf'));
  await page.evaluate(s => {   // the true article texts, from the batch's own text records (NewsBank's text of the same printed stories)
    const its = window.__station.state.nb.items, byDoc = d => (its.find(x => x.p.docref === 'news/' + d) || { p: {} }).p.text || '';
    const basin = byDoc('1AB81C250BB884D0'), cut = basin.indexOf('Assemblymember Jesse Gabriel said');
    window.__truth = { termlimits: byDoc('1AB771535547D488'), ballots: byDoc('1ABAC3F6E33BA358'), basin_p3: basin.slice(0, cut), basin_p4: basin.slice(cut) }; window.__scn = s;
  }, scn);
  await page.uncheck('#nbLinks').catch(() => {});
  await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 300000 });
  const run = await page.evaluate(() => { const r = window.__station.state.nb.lastRun; return { rows: r.rows, doc: r.doc, items: r.items, counts: r.counts }; });
  return { X, page, run };
}
const SIX = ['Whittier Daily News', 'San Gabriel Valley Tribune', 'Pasadena Star-News', 'Long Beach Press-Telegram', 'Los Angeles Daily News', 'Daily News of Los Angeles', 'Daily Breeze'];
(async () => {
  const items0 = await (async () => { const X = await H.start(PAGE, stub, { images: 3 }); await H.loadFile(X.page, FU); await H.dropPdf(X.page, path.join(DIR, 'multi4.pdf')); const it = await H.items(X.page); await X.close(); return it; })();
  check('the batch is read: 27 records = 13 text stories + 14 print pages; 2 text stories already in the tracker (00001, 00003)', items0.length === 27 && items0.filter(i => i.kind === 'print_page').length === 14 && items0.filter(i => i.st === 'known').length === 2, JSON.stringify(items0.map(i => i.st)));
  /* FINDING 1: the six Oct 25 p.14 pages carry "Term limits shake up runs for Senate, Assembly", the print story the tracker already holds as s00001 with a row for
     EVERY one of these six outlets (00001 Original Pasadena Star-News web; 00003-00007 Reprints, NewsBank print records, p. 14). Nothing new may be proposed: the pages
     are the print originals of those rows (ORIGCOPIES-v1 / PRINTORIG-v1: _original_pdf/<year>/<aid>_p14.pdf), filled in as extra copies, not rows. */
  for (const scn of [1, 3]) {
    const { X, run } = await fresh(scn), tag = scn === 1 ? '[headline as printed] ' : '[headline with NewsBank’s kicker] ';
    const oct25 = run.rows.filter(r => r['Date'] === '2026-10-25' && /Term limits/.test(r['Headline'] + ' ' + (r['NewsBank print-page link'] || '')));
    const pageRows = run.rows.filter(r => /image\/v2/.test(r['NewsBank print-page link'] || '') && r['Date'] === '2026-10-25');
    check(tag + 'the six Oct 25 pages add NO rows (s00001 already has a row for each of these outlets): 0 rows, not ' + pageRows.length, pageRows.length === 0, JSON.stringify(pageRows.map(r => [r['Original or reprint'], r['Story ID'], r['Outlet']])));
    check(tag + 'no new Original story is made from these pages', !run.rows.some(r => r['Date'] === '2026-10-25' && r['Original or reprint'] === 'Original' && /image\/v2/.test(r['NewsBank print-page link'] || '')), JSON.stringify(oct25.map(r => [r['Original or reprint'], r['Outlet']])));
    check(tag + 'the six pages are carried as extra copies / print originals of rows 00001, 00003-00007 (extra_copies names them)', SIX.filter(o => o !== 'Daily News of Los Angeles').every(o => (run.doc.extra_copies || []).some(x => x.outlet === o || ['00001', '00003', '00004', '00005', '00006', '00007'].includes(x.aid) && x.kind === 'print_page')), JSON.stringify((run.doc.extra_copies || []).map(x => x.aid)));
    /* FINDING 2: NewsBank names the same paper two ways: "Los Angeles Daily News (CA)" (text records) and "Daily News of Los Angeles (CA)" (e-edition pages); the sheet spells it
       "Los Angeles Daily News" (172 rows). The Nov 4 p. 9 and Oct 27 p. 3 pages are the printed pages of text records IN THIS BATCH (same outlet, date and page number) and must not become second Original rows. */
    const dn = run.rows.filter(r => /Daily News of Los Angeles/.test(r['Outlet']));
    check(tag + 'no row is filed under the outlet name "Daily News of Los Angeles" (the tracker spells it "Los Angeles Daily News")', dn.length === 0, dn.map(r => r['Date'] + ' ' + r['Headline'].slice(0, 40)).join(' / '));
    const ballots = run.rows.filter(r => /mail-in ballots/i.test(r['Headline']) && r['Original or reprint'] === 'Original'), basin = run.rows.filter(r => /Sepulveda Basin gets \$22M in funding/i.test(r['Headline']) && r['Original or reprint'] === 'Original');
    check(tag + 'Nov 4 p. 9 (Daily News) is the printed page of the batch’s own text record (Los Angeles Daily News 2026-11-04 p. 9): ONE Original, not ' + ballots.length, ballots.length === 1, JSON.stringify(ballots.map(r => r['Outlet'])));
    check(tag + 'Oct 27 p. 3 (Daily News) is the printed page of the batch’s own text record (Los Angeles Daily News 2026-10-27 p. 3): ONE Original, not ' + basin.length, basin.length === 1, JSON.stringify(basin.map(r => r['Outlet'])));
    /* FINDING 3: Oct 27 p. 4 is the JUMP page of that story ("BASIN / From Page 3", with his quote and a captioned photo of him). It belongs with p. 3 as a print original (_p3-4),
       never an Unlinked print pages row, and never "too little text" (the page has a 100+ word continuation; only the slug "BASIN" is short). */
    const pr4 = (run.doc.print_rows || []).filter(r => r['Date'] === '2026-10-27' && r['Page'] === '4');
    check(tag + 'the Oct 27 p. 4 jump page ("From Page 3") is not an Unlinked print pages row', pr4.length === 0, pr4.map(r => r['Team note']).join(' / '));
    check(tag + 'the jump page is kept with the p. 3 story (print_pages entry with a story or a batch item, not "unlinked")', (run.doc.print_pages || []).some(p => p.date === '2026-10-27' && /Daily News/.test(p.outlet) && p.as !== 'unlinked' && (p.story || p.item)), JSON.stringify((run.doc.print_pages || []).filter(p => p.date === '2026-10-27')));
    check(tag + 'no outside request, no page error', X.outside.length === 0 && X.errors.length === 0, JSON.stringify([X.outside, X.errors.slice(0, 3)]));
    await X.close();
  }
  console.log(C.failed ? C.failed + ' FAILED (expected until the audit’s findings are fixed)' : 'all passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
