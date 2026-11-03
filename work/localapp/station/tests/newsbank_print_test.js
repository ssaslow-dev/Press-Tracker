/* PRINTPAGES-v1 on the REAL multi3 batch (stories 8 and 9: the East Bay Times and Mercury News print pages that carry the LA Times story of tracker story s01903):
   each page is cut into a PDF of its own, shown as a picture, and the intern may name the tracker story; a confirmed page is proposed as a print reprint of it, an unconfirmed one as an
   "Unlinked print pages" row. Licensed text: AJG_REAL_NB2 names the folder with multi3.pdf and for_update_0bccc1fc.json; skipped without it.   AJG_REAL_NB2=DIR node tests/newsbank_print_test.js */
const fs = require('fs'), path = require('path');
const H = require('./nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB2, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json');
if (!DIR || !fs.existsSync(path.join(DIR, 'multi3.pdf')) || !fs.existsSync(FU)) { console.log('SKIP newsbank_print_test (AJG_REAL_NB2 not set or files absent)'); process.exit(0); }
const PAGE = path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;
// STUBBED Claude: every item is answered with canned fields (these are not results of a real Claude call)
const stub = prompt => /^These items come from NewsBank/.test(prompt) ? [...prompt.matchAll(/=== ITEM (\d+)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'x', press_release: 'no', pr_why: 'a reporter’s story', date: '', outlet: '', pub: '', hl: '', topic: 'Food safety', media: 'Online news', role: 'Mentioned in story', tone: 'Neutral', twhy: '', author: '', lang: '', hl_en: '', text_en: '' })) : [];
(async () => {
  const X = await H.start(PAGE, stub), page = X.page;
  await H.loadFile(page, FU); await H.dropPdf(page, path.join(DIR, 'multi3.pdf'));
  const pp = await page.evaluate(() => window.__station.state.nb.items.filter(x => x.screen.status === 'print_page').map(x => ({ key: x.key, outlet: x.p.outlet_clean, date: x.p.date, page: x.p.page, pdf: !!x.pdf, thumb: (x.thumb || '').slice(0, 22), cands: window.__nb.candidates(x.p.date, x.p.outlet_clean).map(c => c.id) })));
  check('two print pages, each with a PDF of its own and a picture', pp.length === 2 && pp.every(x => x.pdf && /^data:image\/jpeg/.test(x.thumb)), JSON.stringify(pp.map(x => [x.outlet, x.pdf, x.thumb])));
  check('the candidate list (stories nearest before the page date) includes s01903 for both pages; the intern still decides from the picture', pp.every(x => x.cands.includes('s01903')), JSON.stringify(pp.map(x => x.cands.length)));
  const box = await page.evaluate(() => document.querySelectorAll('#nbBody img[alt]').length + ' ' + document.querySelectorAll('#nbBody input[data-nbp]').length);
  check('the box shows the pictures and one question per page', box === '2 2', box);
  // confirm the first page (East Bay Times) as s01903, leave the Mercury News page unconfirmed
  const inputs = await page.$$('#nbBody input[data-nbp]'); await inputs[0].fill('s01903 · Los Angeles Times'); await inputs[0].dispatchEvent('change');
  const conf = await page.evaluate(() => window.__station.state.nb.items.filter(x => x.screen.status === 'print_page').map(x => x.confirm));
  check('the first page is confirmed as s01903, the second is not', conf.filter(Boolean).join() === 's01903' && conf.length === 2, JSON.stringify(conf));
  await page.uncheck('#nbLinks').catch(() => {});
  await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 90000 });
  const run = await page.evaluate(() => { const r = window.__station.state.nb.lastRun; return { rows: r.rows, doc: r.doc, pp: r.print_pages }; });
  const rep = run.rows.find(r => r['Outlet'] === 'East Bay Times');
  check('the confirmed page is a Reprint row of s01903: Original or reprint, Story ID, Edition Print, Format Print, Page 18, Date source print edition, 2026-11-01', !!rep && rep['Original or reprint'] === 'Reprint' && rep['Story ID'] === 's01903' && rep['Edition'] === 'Print' && rep['Format'] === 'Print' && rep['Page'] === '18' && rep['Date source'] === 'print edition' && rep['Date'] === '2026-11-01', rep && JSON.stringify([rep['Original or reprint'], rep['Story ID'], rep['Edition'], rep['Format'], rep['Page'], rep['Date']]));
  check('that row: the story’s headline, the page link in the print-page column (not the article column), the citation in the print-page citation column, no Press release', !!rep && rep['Headline'] === 'California just changed the way you shop for food. Here\u0027s how' && /docref=image\/v2%3A/.test(rep['NewsBank print-page link']) && !rep['NewsBank article link'] && /East Bay Times/.test(rep['Newsbank APA citation (print page)']) && !rep['Newsbank APA citation (article)'] && rep['Press release'] !== 'Yes', rep && JSON.stringify([rep['Headline'], rep['NewsBank print-page link'], rep['Newsbank APA citation (print page)']]).slice(0, 300));
  check('the unconfirmed page (Mercury News) is an Unlinked print pages row', run.doc.print_rows.length === 1 && run.doc.print_rows[0]['Outlet'] === 'Mercury News, The' && run.doc.print_rows[0]['Page'] === '11' && !run.rows.some(r => r['Outlet'] === 'Mercury News, The'), JSON.stringify(run.doc.print_rows.map(x => x['Outlet'])));
  const docs = await page.evaluate(() => { const o = []; const st = window.__station.sess; if (!st || !st.pages) return null; for (const [id, v] of st.pages) if (v.data && v.data.nb && v.data.nb.kind === 'print_page') o.push({ id, as: v.data.nb.as, file: v.data.nb.file, sha: !!v.data.nb.pdf_sha256 }); return o; });
  if (docs) check('both print pages have a pages document with its PDF (as: reprint / unlinked)', docs.length === 2 && docs.some(d => d.as === 'reprint') && docs.some(d => d.as === 'unlinked') && docs.every(d => /^files\/nb-/.test(d.file) && d.sha), JSON.stringify(docs));
  else console.log('NOTE the page documents are not reachable from window.__station.sess; checked through the run document only');
  check('no outside request, no page error', X.outside.length === 0 && X.errors.length === 0, JSON.stringify([X.outside, X.errors.slice(0, 3)]));
  await X.close(); console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
