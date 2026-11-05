/* PRINTFIX (PRINTREAD_REVIEW fixes 1, 3, 5, 6, 7) on the real multi4.pdf batch. Fake Claude as in review13/nb_real4_test.js, with scenarios.
   Claude is a FAKE (canned answers that say what is really printed on the pages, read by the auditor); the page is the built station dist/index.html.
   Licensed text: AJG_REAL_NB4 names a folder with multi4.pdf and for_update_0bccc1fc.json; without it this test is SKIPPED.
     AJG_REAL_NB4=DIR node tests/review13/nb_real4_test.js
   Expected to FAIL until the station is fixed (the checks say what should happen). */
const fs = require('fs'), path = require('path');
const H = require('./nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB4, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json');
if (!DIR || !fs.existsSync(path.join(DIR, 'multi4.pdf')) || !fs.existsSync(FU)) { console.log('SKIP review13/nb_real4_test (AJG_REAL_NB4 not set or files absent)'); process.exit(0); }
const PAGE = path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;

/* Claude's answers, from what the pages really show. The article texts are taken from the batch's own NewsBank text records of the same stories (set on window.__truth
   after the drop), so no licensed text sits in this file. window.__scn 1 = headlines as printed; 3 = the Oct 25 headline with NewsBank's kicker "2026 elections - ". */
const stub = (prompt, o) => {
  const T = window.__truth || {}, scn = window.__scn || 1;
  if (/^These items come from NewsBank/.test(prompt)) return [...prompt.matchAll(/=== ITEM (\d+)\nURL: (.*)\nPage title: (.*)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'x', press_release: /MAYOR BASS HIGHLIGHTS/.test(m[3]) ? 'yes' : 'no', pr_why: 'x', date: '', outlet: '', pub: '', hl: '', topic: 'District / community', media: 'Newspaper', role: 'Mentioned in story', tone: 'Neutral', twhy: '', author: '', lang: /recibe 22 millones/.test(m[3]) ? 'Spanish' : '', hl_en: /recibe 22 millones/.test(m[3]) ? 'Sepulveda Basin receives $22 million' : '', text_en: '' }));
  if (!/^You are reading a scanned page/.test(prompt)) return [];
  window.__pcalls = (window.__pcalls || 0) + 1;
  const m = /Outlet: (.*?)\. Date: (\d{4}-\d{2}-\d{2})\. Page: (.*?)\.\n/.exec(prompt); if (!m) return { readable: false, articles: [] };
  const outlet = m[1], date = m[2], page = m[3];
  const art = (hl, byline, section, pg, text, extra) => Object.assign({ headline: hl, byline, section, page: pg, text, continues: '', continued_from: '', names_gabriel: /Gabriel/.test(text), confidence: 'high', box: { x: 0.04, y: 0.03, w: 0.92, h: 0.55 }, name_sentences: (text.match(/[^.!?]*Gabriel[^.!?]*[.!?]/g) || []).map(x => x.trim()) }, extra || {});
  if (scn === 10 && ((date === '2026-10-25' && /Breeze/.test(outlet)) || (date === '2026-10-27' && page === '3') || (date === '2026-11-04' && page === '9'))) return { readable: true, articles: [] };
  if (scn === 11 && date === '2026-11-04' && page === '9') return { readable: true, articles: [art('Congressional races in the San Gabriel Valley', 'By A', '', '9', 'The San Gabriel Valley district race and the San Gabriel Mountains foothills voters in the San Gabriel Valley will decide the seat. '.repeat(4))] };
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
  const X = await H.start(PAGE, stub, { images: 8 }), page = X.page;
  await H.loadFile(page, FU); await H.dropPdf(page, path.join(DIR, 'multi4.pdf'));
  await page.evaluate(s => {   // the true article texts, from the batch's own text records (NewsBank's text of the same printed stories)
    const its = window.__station.state.nb.items, byDoc = d => (its.find(x => x.p.docref === 'news/' + d) || { p: {} }).p.text || '';
    const basin = byDoc('1AB81C250BB884D0'), cut = basin.indexOf('Assemblymember Jesse Gabriel said');
    window.__truth = { termlimits: byDoc('1AB771535547D488'), ballots: byDoc('1ABAC3F6E33BA358'), basin_p3: basin.slice(0, cut), basin_p4: basin.slice(cut) }; window.__scn = s;
  }, scn);
  await page.uncheck('#nbLinks').catch(() => {});
  await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 300000 });
  const pcalls = await page.evaluate(() => window.__pcalls || 0);
  const run = await page.evaluate(() => { const r = window.__station.state.nb.lastRun; return { rows: r.rows, doc: r.doc, items: r.items, counts: r.counts }; });
  run.pcalls = pcalls;
  return { X, page, run };
}
(async () => {
  let r = await fresh(1), run = r.run;
  const rl = run.doc.nb && run.doc.nb.read_limits;
  check('fix 5: the run doc records the runtime image limits (maxCount 8) and the count used', !!rl && rl.images && rl.images.maxCount === 8 && rl.max_count_used >= 6 && rl.max_count_used <= 8, JSON.stringify(rl));
  check('fix 7: pages showing a byte-identical picture are read once (fewer Claude calls than the 14 pages)', run.pcalls < 14, 'calls ' + run.pcalls);
  const sc = run.rows.find(x => /Santa Cruz/.test(x['Outlet']));
  check('fix 3: the Santa Cruz Sentinel copy (36 days after s01903, same author credited to the LA Times) is proposed as a print Reprint of s01903', !!sc && sc['Original or reprint'] === 'Reprint' && sc['Story ID'] === 's01903', JSON.stringify(sc && [sc['Original or reprint'], sc['Story ID']]));
  check('byline: no leading "By", no credit in the author ("Karen Garcia")', !!sc && !/^by\b/i.test(sc['Author'] || sc['Authors'] || 'x') && !/Times/.test(sc['Author'] || ''), JSON.stringify(sc && [sc['Author'], Object.keys(sc).filter(k => /uthor/.test(k))]));
  const unl1 = (run.doc.print_rows || []).length;
  await r.X.close();
  r = await fresh(10); run = r.run;
  const unl = (run.doc.print_rows || []).map(x => JSON.stringify(x).slice(0, 200));
  check('fix 1: pages Claude answers "none" for are still placed by the batch\'s own text record: none of Daily Breeze p.14, Oct 27 p.3, Nov 4 p.9 goes to Unlinked print pages', !unl.some(x => /Breeze|2026-10-27|2026-11-04/.test(x) && /(Breeze|p\.? ?14|"3"|"9"|Page 3|Page 9)/.test(x)), JSON.stringify(unl) + ' | before ' + unl1);
  const sts = run.items.filter(x => /(Page|p\.) ?(14|3|9)|Daily Breeze/.test(x.why || '') || /^The page|Claude found no article/.test(x.why || '')).map(x => x.status + ': ' + String(x.why).slice(0, 70));
  check('fix 1: those pages are known or attached (reason names the batch\'s text record)', run.items.filter(x => /Claude found no article naming him on the page, but/.test(x.why || '')).length >= 3, JSON.stringify(sts));
  await r.X.close();
  r = await fresh(11); run = r.run;
  check('fix 6: "San Gabriel Valley" text does not count as naming him (page not used as an article)', !run.rows.some(x => /San Gabriel Valley/.test(x['Headline'] || '') && /Congressional races/.test(x['Headline'] || '')), JSON.stringify(run.rows.map(x => x['Headline']).filter(h => /Congressional/.test(h))));
  await r.X.close();
  console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.log('FAIL exception', e); process.exit(1); });
