/* PRINTNEW-v1 (station part) on the REAL multi3 batch: Claude (a FAKE sample that returns canned readings; not a real Claude call) reads the East Bay Times (Nov 1 p. 18) and Mercury News
   (Nov 3 p. 11) pages. Scenarios: 1 EBT = the tracker story s01903 -> its print edition, Mercury = a new story; 2 no Gabriel article -> Unlinked print pages; 3 low confidence / bad text -> Unlinked;
   4 no `images` in sample.limits -> today's behaviour, with a note; 5 rate_limited -> fallback, run completes; 6 the person's own pick is not overridden.
   Licensed text: AJG_REAL_NB2 names the folder with multi3.pdf and for_update_0bccc1fc.json; skipped without it. */
const fs = require('fs'), path = require('path');
const H = require('./nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB2, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json');
if (!DIR || !fs.existsSync(path.join(DIR, 'multi3.pdf')) || !fs.existsSync(FU)) { console.log('SKIP newsbank_printread_test (AJG_REAL_NB2 not set or files absent)'); process.exit(0); }
const PAGE = path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;
const stub = (prompt, o) => {
  if (/^These items come from NewsBank/.test(prompt)) return [...prompt.matchAll(/=== ITEM (\d+)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'x', press_release: 'no', pr_why: 'a reporter’s story', date: '', outlet: '', pub: '', hl: '', topic: 'Food safety', media: 'Newspaper', role: 'Named in headline', tone: 'Neutral', twhy: '', author: '', lang: '', hl_en: '', text_en: '' }));
  if (!/^You are reading a scanned page/.test(prompt)) return [];
  const scn = window.__scn || 1, ebt = /East Bay Times/.test(prompt);
  if (scn === 5) { const e = new Error('slow down'); e.code = 'rate_limited'; throw e; }
  const body = 'Assemblymember Jesse Gabriel, D-Northridge, said the new law will change how Californians shop for food and what is printed on the labels of packaged products sold in grocery stores across the state this year, adding that families deserve to know what is in their food.';
  const art = (hl, conf, extra) => Object.assign({ headline: hl, byline: 'By A. Reporter', section: 'Business', page: ebt ? '18' : '11', text: body + '\n\n' + body, continues: '', continued_from: '', names_gabriel: true, confidence: conf, box: ebt ? { x: 0.05, y: 0.30, w: 0.55, h: 0.40 } : { x: 0.9, y: 0.2, w: 0.5, h: 0.3 }, name_sentences: ['Assemblymember Jesse Gabriel, D-Northridge, said the new law will change how Californians shop for food and what is printed on the labels of packaged products sold in grocery stores across the state this year, adding that families deserve to know what is in their food.', 'Gabriel invented this sentence that is not in the text.'] }, extra || {});
  if (scn === 2) return { readable: true, articles: [] };
  if (scn === 3) return { readable: true, articles: [art('Low confidence piece about food', 'low'), art('Short bit', 'high', { text: 'Gabriel said so.' }), art('Wrong text piece about shopping', 'high', { text: 'The governor signed a bill about food labels in the state and the grocery industry said it would comply with the new rules by next year, with many stores already changing their shelf signs and packaging to meet the standard set out in the law. '.repeat(2) })] };
  return { readable: true, articles: ebt ? [art("California just changed the way you shop for food. Here's how", 'high')] : [art('Bay Area lawmaker pushes new rule on school lunch menus', 'medium')] };
};
async function fresh(opts, scn) {
  const X = await H.start(PAGE, stub, opts), page = X.page;
  await page.evaluate(s => { window.__scn = s; }, scn);
  await H.loadFile(page, FU); await H.dropPdf(page, path.join(DIR, 'multi3.pdf'));
  await page.uncheck('#nbLinks').catch(() => {});
  return X;
}
const lastRun = async page => { await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 120000 }); return page.evaluate(() => { const r = window.__station.state.nb.lastRun; return { rows: r.rows, doc: r.doc, items: r.items, pp: r.print_pages, warn: [...document.querySelectorAll('#nbWarn li')].map(x => x.textContent) }; }); };
const pageDocs = page => page.evaluate(() => { const o = {}; for (const [id, v] of window.__station.sess.pages) if (v.data && v.data.nb && v.data.nb.kind === 'print_page') o[id] = v.data; return o; });
(async () => {
  /* 1. both pages read */
  let X = await fresh({ images: 3 }, 1), page = X.page;
  let run = await lastRun(page);
  const calls = await page.evaluate(() => window.__calls.filter(c => c.tool === 'sample' && c.images));
  check('Claude was asked once per print page, with 3 pictures each (whole page + upper + lower), each a non-trivial JPEG under the limit', calls.length === 2 && calls.every(c => c.images === 3 && c.sizes.every(z => z > 2000 && z < 5e6)), JSON.stringify(calls));
  const ebt = run.rows.find(r => r['Outlet'] === 'East Bay Times'), mn = run.rows.find(r => /Mercury News/.test(r['Outlet']));
  check('East Bay Times: read as the tracker story s01903 -> a print Reprint row of it, no confirmation asked', !!ebt && ebt['Original or reprint'] === 'Reprint' && ebt['Story ID'] === 's01903' && ebt['Edition'] === 'Print' && ebt['Format'] === 'Print' && ebt['Page'] === '18' && ebt['Date'] === '2026-11-01' && /image\/v2/.test(ebt['NewsBank print-page link'] || ''), ebt && JSON.stringify([ebt['Original or reprint'], ebt['Story ID'], ebt['Edition'], ebt['Page']]));
  check('Mercury News: no match -> a NEW story row: Original, Edition Print, Format Print, Page 11, Date 2026-11-03, Claude’s headline/byline/section, print-page link, Date source print edition', !!mn && mn['Original or reprint'] === 'Original' && mn['Headline'] === 'Bay Area lawmaker pushes new rule on school lunch menus' && mn['Edition'] === 'Print' && mn['Format'] === 'Print' && mn['Page'] === '11' && mn['Date'] === '2026-11-03' && mn['Author / byline'] === 'By A. Reporter' && mn['Section'] === 'Business' && /image\/v2/.test(mn['NewsBank print-page link'] || '') && !mn['NewsBank article link'] && mn['Date source'] === 'print edition' && mn['Data Source'] === 'Newsbank', mn && JSON.stringify([mn['Original or reprint'], mn['Headline'], mn['Page'], mn['Date'], mn['Author / byline'], mn['Date source'], mn['NewsBank print-page link']]).slice(0, 400));
  check('the new story has tone/topic from the normal classify path and a team note that says to check the reading', !!mn && mn['Topic'] === 'Food safety' && /read from the page picture by Claude/.test(mn['Team note'] || ''), mn && JSON.stringify([mn['Topic'], mn['Team note']]).slice(0, 300));
  check('no print_rows (nothing went to Unlinked print pages) and the print_pages list names only the matched page', run.doc.print_rows.length === 0 && run.doc.print_pages.length === 1 && run.doc.print_pages[0].story === 's01903', JSON.stringify([run.doc.print_rows.length, run.doc.print_pages.map(x => x.story)]));
  const docs = await pageDocs(page), vals = Object.values(docs);
  check('both pages docs keep the read text beside the item: nb.read {by claude, outcome reprint / new, text, headline, matched}', vals.length === 2 && vals.every(d => d.nb.read && d.nb.read.by === 'claude' && d.nb.read.text.length > 200 && d.nb.read.headline) && vals.some(d => d.nb.read.outcome === 'reprint' && d.nb.read.matched === 's01903') && vals.some(d => d.nb.read.outcome === 'new' && d.nb.as === 'new'), JSON.stringify(vals.map(d => [d.nb.as, d.nb.read && d.nb.read.outcome])));
  check('the new story’s pages doc text is the reading (words read from the page), and both docs still name their own PDF', vals.every(d => /^files\/nb-/.test(d.nb.file) && d.nb.pdf_sha256) && vals.some(d => /read from the newspaper page by Claude/.test(d.clean || '') && /school lunch/.test(d.clean || '')), JSON.stringify(vals.map(d => (d.clean || '').length)));
  check('list shows what was done for each page (status, no question left open)', (pi => pi.length === 2 && pi.every(i => /Claude/.test(i.why)))(run.items.filter(i => /by Claude|read the page/.test(i.why))), JSON.stringify(run.items.filter(i => /by Claude|read the page/.test(i.why)).map(i => [i.status, i.why.slice(0, 50)])));
  check('no outside request, no page error', X.outside.length === 0 && X.errors.length === 0, JSON.stringify([X.outside, X.errors.slice(0, 3)]));
  await X.close();
  /* 2. no Gabriel article -> Unlinked print pages, with the reason in the team note */
  X = await fresh({ images: 3 }, 2); page = X.page; run = await lastRun(page);
  check('no article names him -> both pages are Unlinked print pages rows with the reason, no story rows, nothing guessed', run.doc.print_rows.length === 2 && !run.rows.some(r => /East Bay|Mercury/.test(r['Outlet'])) && run.doc.print_rows.every(r => /no article that names Jesse Gabriel/.test(r['Team note'])), JSON.stringify([run.rows.length, run.doc.print_rows.length]));
  const d2 = Object.values(await pageDocs(page)); check('their pages docs say outcome none and carry no text', d2.length === 2 && d2.every(d => d.nb.read && d.nb.read.outcome === 'none' && !d.nb.read.text && d.nb.as === 'unlinked'), JSON.stringify(d2.map(d => d.nb.read)));
  await X.close();
  /* 3. low confidence / too short / no Gabriel in the text */
  X = await fresh({ images: 3 }, 3); page = X.page; run = await lastRun(page);
  check('low confidence, too little text, or no name in the text -> Unlinked, never guessed', run.doc.print_rows.length === 2 && !run.rows.some(r => /East Bay|Mercury/.test(r['Outlet'])) && run.doc.print_rows.every(r => /not clearly/.test(r['Team note'])), JSON.stringify([run.rows.length, run.doc.print_rows.length]));
  await X.close();
  /* 4. the page declares no images (limits has none) -> today's behaviour + a note */
  X = await fresh({}, 1); page = X.page; run = await lastRun(page);
  check('without the images permission: no picture is sent, the pages are Unlinked print pages as before, and the warning says why', run.doc.print_rows.length === 2 && (await page.evaluate(() => window.__calls.filter(c => c.images).length)) === 0 && run.warn.some(w => /images/.test(w)), JSON.stringify(run.warn));
  await X.close();
  /* 5. rate limited -> the run still completes */
  X = await fresh({ images: 3 }, 5); page = X.page; run = await lastRun(page);
  const n5 = await page.evaluate(() => window.__calls.filter(c => c.images).length);
  check('rate limited on the first page: the second is not tried, both are Unlinked print pages, the run completes with a note', n5 === 1 && run.doc.print_rows.length === 2 && run.warn.some(w => /busy|usage limit/.test(w)), JSON.stringify([n5, run.warn]));
  await X.close();
  /* 6. a manual pick is an override: that page is not read */
  X = await fresh({ images: 3 }, 1); page = X.page;
  const inputs = await page.$$('#nbBody input[data-nbp]'); await inputs[0].fill('s01903 · Los Angeles Times'); await inputs[0].dispatchEvent('change');
  run = await lastRun(page);
  check('the person’s own pick is kept: only the other page is read (1 picture call)', (await page.evaluate(() => window.__calls.filter(c => c.images).length)) === 1 && run.rows.some(r => r['Story ID'] === 's01903'), '');
  await X.close();
  /* 7. AUTOSTATION-v1: automatic mode: the PDF is dropped and nothing else is clicked: pages are read, added, and the update folder downloads by itself (one file) */
  X = await H.start(PAGE, stub, { images: 3, auto: true }); page = X.page; await page.evaluate(() => { window.__scn = 1; });
  await H.loadFile(page, FU); await page.uncheck('#nbLinks').catch(() => {});
  await page.setInputFiles('#nbFile', path.join(DIR, 'multi3.pdf'));
  await page.waitForFunction(() => window.__dl && window.__dl.length > 0, null, { timeout: 240000 });
  const au = await page.evaluate(() => ({ dl: window.__dl, run: !!window.__station.state.nb.lastRun, added: window.__station.state.nb.added.size, left: window.__station.state.nb.items.filter(x => !window.__station.state.nb.added.has(x.key) && x.include).length }));
  check('automatic mode: dropped PDF -> read -> added -> one update folder downloaded, with no click', au.run && au.dl.length === 1 && /^ajg_update_.*\.zip$/.test(au.dl[0].filename) && au.dl[0].size > 10000 && au.left === 0, JSON.stringify(au));
  if (process.env.AJG_DUMP_ZIP) { const b = await page.evaluate(() => Array.from(window.__lastDl)); require('fs').writeFileSync(process.env.AJG_DUMP_ZIP, Buffer.from(b)); }   // for verify_nb_zip.py (the PC's own checks)
  await page.waitForTimeout(4000); check('and it is not downloaded a second time', (await page.evaluate(() => window.__dl.length)) === 1);
  await X.close();
  console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
