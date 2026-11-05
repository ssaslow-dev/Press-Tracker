/* N7 (one story found by two sources in a session is offered once) and N14 ("Add print pages": any newspaper page, a picture or an e-edition PDF) in the built station page.
   Claude is a FAKE (canned masthead and article readings); nothing is read from a real page. Needs the for-Update file only:
     AJG_REAL_NB2=DIR (with for_update_0bccc1fc.json) node tests/crosssource_pageany_test.js          (skipped without it) */
const fs = require('fs'), path = require('path'), os = require('os'), { execFileSync } = require('child_process');
const H = require('./nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB2, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json');
if (!DIR || !fs.existsSync(FU)) { console.log('SKIP crosssource_pageany_test (AJG_REAL_NB2 not set or the for-Update file is absent)'); process.exit(0); }
const PAGE = path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;
const stub = (prompt, o) => {
  if (/^These items (come from NewsBank|are articles read by Claude)/.test(prompt)) return [...prompt.matchAll(/=== ITEM (\d+)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'x', press_release: 'no', pr_why: 'a reporter’s story', date: '', outlet: '', pub: '', hl: '', topic: 'Energy / environment', media: 'Newspaper', role: 'Named in headline', tone: 'Neutral', twhy: '', author: '', lang: '', hl_en: '', text_en: '' }));
  if (!/^You are reading a scanned page/.test(prompt)) return [];
  const next = (window.__readQ || []).shift(); if (!next) return { readable: true, masthead: {}, articles: [] };
  if (next.error) { const e = new Error('x'); e.code = next.error; throw e; }
  return next;
};
const BODY = 'Assemblymember Jesse Gabriel (D-Encino) introduced a bill in Sacramento on Friday that would speed up clean air permits across California, saying that Californians should not wait years for clean air and that regional air districts need a firm deadline to act on every application.';
const read = (paper, date, page, conf, arts) => ({ readable: true, masthead: { paper, date, page, confidence: conf }, articles: arts });
const art = (hl, extra) => Object.assign({ headline: hl, byline: 'By Dana Whitfield', section: 'Metro', page: 'A5', text: BODY + '\n\n' + BODY, continues: '', continued_from: '', names_gabriel: true, confidence: 'high', box: { x: 0.05, y: 0.3, w: 0.5, h: 0.4 }, name_sentences: [BODY] }, extra || {});
const HL = 'Gabriel bill would speed clean air permits';
async function png(page, label) { return page.evaluate(l => { const c = document.createElement('canvas'); c.width = 900; c.height = 1300; const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, 900, 1300); x.fillStyle = '#000'; x.font = '40px serif'; x.fillText('THE VALLEY GAZETTE TEST ' + l, 30, 80); for (let i = 0; i < 40; i++) x.fillRect(30, 140 + i * 26, 300 + (i * 37 + l.length * 11) % 500, 4); return c.toDataURL('image/png').split(',')[1]; }, label); }
const waitRead = page => page.waitForFunction(() => window.__station.state.nb.files.every(f => f.status !== 'reading') && !window.__station.state.nb.reading, null, { timeout: 120000 });
async function dropImg(page, label) { const b = Buffer.from(await png(page, label), 'base64'); await page.setInputFiles('#nbFile', { name: label + '.png', mimeType: 'image/png', buffer: b }); await page.waitForTimeout(300); await waitRead(page); }
async function fresh(opts) { const X = await H.start(PAGE, stub, Object.assign({ images: 8 }, opts || {})); await H.loadFile(X.page, FU); await X.page.uncheck('#nbLinks').catch(() => {}); return X; }
const q = (page, reads) => page.evaluate(r => { window.__readQ = r; }, reads);
const lastRun = async page => { await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 120000 }); return page.evaluate(() => { const r = window.__station.state.nb.lastRun; return { rows: r.rows, doc: r.doc, items: r.items, counts: r.counts }; }); };
const sessDocs = (page, c) => page.evaluate(c => [...window.__station.sess[c]].map(([id, v]) => [id, v.data]), c);
const W = (id, at, rows, extra) => Object.assign({ at, mode: 'find', status: 'done', stories: rows.filter(r => r['Original or reprint'] === 'Original').map(r => r['Tracker story code']).filter(Boolean), reprints: [], rows, left: [], searched_to: '' }, extra || {});
const R = (n, o) => Object.assign({ 'Article ID': 'NEW-run-' + n, 'Story ID': 'sNEW-run-' + n, 'Original or reprint': 'Original', 'Data Source': 'Web search (TinyFish)', Date: '2026-11-03', Outlet: 'Valley Gazette Test', Headline: HL, 'Publisher link': 'https://www.valleygazette-test.com/2026/11/clean-air', 'Tracker story code': 'jg-' + String(n).padStart(6, 'a') }, o || {});
const putRun = (page, id, doc) => page.evaluate(([i, d]) => window.__station.mem.collection('runs').doc(i).set(d), [id, doc]);
const putDoc = (page, c, id, doc) => page.evaluate(([c, i, d]) => window.__station.mem.collection(c).doc(i).set(d), [c, id, doc]);
const settle = async page => { await page.waitForTimeout(400); await page.evaluate(() => window.__station.xdReconcile()); await page.waitForTimeout(200); };

(async () => {
  /* ---------- N14 ---------- */
  let X = await fresh(), page = X.page;
  const OTHER = 'ZZZ another story on the same page about the harbor budget that the save must never see';
  await q(page, [read('Valley Gazette Test', '2026-11-03', 'A5', 'high', [art(HL), art('Harbor budget', { names_gabriel: false, text: OTHER + ' ' + OTHER + ' ' + OTHER })])]);
  await dropImg(page, 'one');
  let it = await page.evaluate(() => window.__station.state.nb.items.map(i => ({ st: i.screen.status, src: i.p.src, thumb: !!i.thumb, pdf: !!i.pdf, file: i.fileId })));
  check('a picture of a page is taken as one newspaper page with a PDF and a thumbnail', it.length === 1 && it[0].st === 'print_page' && it[0].src === 'page' && it[0].thumb && it[0].pdf && /^pg-/.test(it[0].file), JSON.stringify(it));
  check('the table calls it a newspaper page to be read', /Newspaper page \(to be read\)/.test(await page.textContent('#nbBody')));
  let run = await lastRun(page);
  const prompts = await page.evaluate(() => window.__prompts.filter(p => /^You are reading a scanned page/.test(p)));
  check('Claude is asked for the masthead too (paper, date, page) and sent the page as tiles', prompts.length === 1 && /Nothing is known about it yet/.test(prompts[0]) && /"masthead"/.test(prompts[0]) && (await page.evaluate(() => window.__calls.filter(c => c.images >= 6).length)) === 1);
  const row = run.rows[0];
  check('NEW story from the page: Original, outlet/date/page from the masthead, Print edition, Data Source “Print page”, no link, no NewsBank cells', run.rows.length === 1 && row['Original or reprint'] === 'Original' && row['Outlet'] === 'Valley Gazette Test' && row['Date'] === '2026-11-03' && row['Page'] === 'A5' && row['Edition'] === 'Print' && row['Data Source'] === 'Print page' && row['Date source'] === 'print edition' && !row['Publisher link'] && !row['NewsBank print-page link'] && !row['Newsbank APA citation (print page)'] && /masthead/.test(row['Team note'] || ''), JSON.stringify(row));
  check('run doc: mode hand, printpage mark, no NewsBank mark, no print_rows', run.doc.mode === 'hand' && run.doc.printpage && !run.doc.newsbank && run.doc.print_rows.length === 0 && run.doc.nb && run.doc.nb.pdfs === 1 && /newspaper page/.test(run.doc.nb.source), JSON.stringify(run.doc).slice(0, 300));
  const pg = (await sessDocs(page, 'pages')).map(x => x[1]).filter(d => d.nb);
  check('its pages doc names the one-page PDF (pg- id), source page, reading kept', pg.length === 1 && pg[0].nb.source === 'page' && /^files\/pg-/.test(pg[0].nb.file) && pg[0].nb.pdf_sha256 && pg[0].nb.read && pg[0].nb.read.outcome === 'new', JSON.stringify(pg[0] && pg[0].nb).slice(0, 300));
  { const txt = h => String(h || '').replace(/<(script|style)[\s\S]*?<\/\1>/g, ' ').replace(/<[^>]+>/g, '\n').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
    const docs = (await sessDocs(page, 'pages')).map(x => x[1]), body = BODY + '\n\n' + BODY;
    check('TEXT RULE: the pages doc text is ONLY that article’s text as Claude read it (= nb.read.text); nothing of the page’s other articles, no caption, no OCR', docs.every(d => !/ZZZ/.test(JSON.stringify(d))) && txt(docs[0].clean).replace(/\s+/g, ' ').includes(body.replace(/\s+/g, ' ')) && docs[0].nb.read.text === body && docs[0].scoped === '', docs[0] && txt(docs[0].clean).slice(0, 300)); }
  check('no reprints document (it would be written to the sheet as a second row)', (await sessDocs(page, 'reprints')).length === 0);
  await page.click('#stPack'); await page.waitForFunction(() => window.__dl.length > 0, null, { timeout: 30000 });
  const zp = path.join(os.tmpdir(), 'pageany_' + process.pid + '.zip'); fs.writeFileSync(zp, Buffer.from(await page.evaluate(() => Array.from(window.__lastDl))));
  let out = ''; try { out = execFileSync('python3', ['-I', path.join(__dirname, 'pageany_verify_zip.py'), zp], { encoding: 'utf8' }); } catch (e) { out = 'FAIL ' + (e.stderr || e.message); }
  check('the PC’s own checker accepts the update folder; a page PDF is not claimed as an NB text copy (it travels as files/pg-….pdf)', /^PASS/m.test(out) && /files\/pg-/.test(out) && !/library\/\d{4}\/nb/.test(out), out.slice(0, 400));
  check('SAVED COPY of a print-only story: named like a text copy (ws<ID>o-s<ID>.html in library/<year>/), its HTML is the read article with the “read by Claude” line; the page scan travels as files/pg-….pdf', /\["ws", "o", "library\/2026\/ws\d{5}o-s\d{5}\.html"\]/.test(out), out.slice(0, 500));
  check('no outside request, no page error', X.outside.length === 0 && X.errors.length === 0, JSON.stringify([X.outside, X.errors.slice(0, 3)]));
  await X.close();

  /* masthead not clear / no article / Claude fails: listed, nothing added, no run, never a row */
  X = await fresh(); page = X.page;
  await q(page, [read('', '2026-11-03', 'A5', 'low', [art(HL)]), read('Valley Gazette Test', '2026-11-03', 'A5', 'high', []), read('Valley Gazette Test', '2026-13-45', 'A5', 'high', [art(HL)]), { error: 'rate_limited' }]);
  for (const l of ['a', 'b', 'c', 'd']) await dropImg(page, l);
  await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.items.every(i => window.__station.state.nb.added.has(i.key)), null, { timeout: 120000 });
  const st = await page.evaluate(() => window.__station.state.nb.items.map(i => [i.screen.status, i.screen.why]));
  check('unclear paper -> look; no article -> nohim; impossible date -> look; Claude busy -> look (retry); none became a row or an Unlinked print pages row', st.map(x => x[0]).join() === 'look,nohim,look,look' && (await sessDocs(page, 'runs')).length === 0, JSON.stringify(st));
  check('the reasons are plain', /paper|clearly/.test(st[0][1]) && /no article/.test(st[1][1]) && /date/.test(st[2][1]) && /busy|usage|could not read|try once more/i.test(st[3][1]), JSON.stringify(st.map(x => x[1])));
  await X.close();

  /* a page of a story the tracker has: print edition (the same flow as a NewsBank page); and an e-edition PDF: pages without his name are skipped */
  X = await fresh(); page = X.page;
  const fu = JSON.parse(fs.readFileSync(FU, 'utf8')), s1903 = fu.stories.find(s => s.id === 's01903');
  await q(page, [read('East Bay Times', '2026-11-01', 'B6', 'high', [art(s1903.hl)])]);
  await dropImg(page, 'ebt'); run = await lastRun(page);
  check('a page whose article is a story in the tracker (another outlet) is filed as its print edition: Reprint of s01903, no new Original', run.rows.length === 1 && run.rows[0]['Original or reprint'] === 'Reprint' && run.rows[0]['Story ID'] === 's01903' && run.rows[0]['Outlet'] === 'East Bay Times' && run.rows[0]['Print headline'] === s1903.hl && (await sessDocs(page, 'reprints')).length === 0 && (await sessDocs(page, 'pages')).every(([, d]) => !d.scoped && d.nb.read.text === BODY + '\n\n' + BODY && String(d.clean).includes(BODY.slice(0, 60)) && d.title === s1903.hl.slice(0, 300)), JSON.stringify(run.rows[0]));
  await X.close();
  const pdfPath = path.join(os.tmpdir(), 'eedition_' + process.pid + '.pdf');
  execFileSync('python3', ['-I', '-c', 'import sys\nfrom reportlab.pdfgen import canvas\nc=canvas.Canvas(sys.argv[1])\nfor t in ["City council meeting notes about the harbor budget " * 12, "Valley schools: Assemblymember Jesse Gabriel visited the school " * 8, "Sports scores and standings " * 15, "Photo page"]:\n    c.drawString(40, 700, t[:90]); y=680\n    for i in range(0, len(t), 90):\n        c.drawString(40, y, t[i:i+90]); y-=14\n    c.showPage()\nc.save()', pdfPath]);
  X = await fresh(); page = X.page;
  await q(page, [read('Valley Gazette Test', '2026-11-03', 'A3', 'high', [art('Valley schools welcome Gabriel visit')]), read('Valley Gazette Test', '2026-11-03', 'A4', 'high', [])]);
  await page.setInputFiles('#nbFile', pdfPath); await page.waitForTimeout(300); await waitRead(page);
  const f = await page.evaluate(() => window.__station.state.nb.files[0]);
  check('an e-edition PDF: the 2 pages with a text layer that never says Gabriel are skipped; the page that does and the photo page are to be read', f.status === 'ok' && f.stories === 2 && /2 to be read/.test(f.note) && /2 with text/.test(f.note), JSON.stringify(f));
  run = await lastRun(page);
  check('one new story from the page that names him; the photo page (nothing found) is listed only', run.rows.length === 1 && run.rows[0]['Headline'] === 'Valley schools welcome Gabriel visit' && run.items.some(i => i.status === 'nohim'), JSON.stringify(run.items.map(i => i.status)));
  await X.close();

  /* ---------- N7 ---------- */
  X = await fresh(); page = X.page;
  const NB = { 'NewsBank article link': 'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=news/AAAA1111BBBB2222', 'Newsbank APA citation (article)': 'Whitfield, D. (2026, November 3). Clean air. Valley Gazette Test.', Section: 'Metro', Page: 'A5' };
  await putRun(page, 'run-web', W('run-web', '2026-11-03T10:00:00Z', [R('w1')]));
  const nbRow = R('n1', { 'Data Source': 'Newsbank', 'Story ID': 'sNEW-run-n1', 'Tracker story code': 'jg-nb0001', 'Publisher link': '' }); Object.assign(nbRow, NB);
  const kid = { 'Article ID': 'NEW-run-n2', 'Story ID': 'sNEW-run-n1', 'Original or reprint': 'Reprint', 'Data Source': 'Newsbank', Outlet: 'Other Daily', Date: '2026-11-04', Headline: HL };
  await putDoc(page, 'pages', 'jg-nb0001', { url: NB['NewsBank article link'], title: HL, clean: '<p>x</p>', nb: { docref: 'news/aaaa1111bbbb2222', file: '', kind: 'article' } });
  await putDoc(page, 'tones', 'jg-nb0001', { tone: 'Neutral' }); await putDoc(page, 'authors', 'jg-nb0001', { author: 'Dana Whitfield' });
  await putRun(page, 'run-nb', W('run-nb', '2026-11-03T11:00:00Z', [nbRow, kid], { mode: 'newsbank' }));
  await settle(page);
  let runs = Object.fromEntries(await sessDocs(page, 'runs')); const wrow = runs['run-web'].rows[0];
  check('web first, NewsBank second: the NewsBank copy is folded into the web row (link, citation, section, page in its blank cells; a note) and leaves the NewsBank run', runs['run-nb'].rows.length === 1 && wrow['NewsBank article link'] === NB['NewsBank article link'] && wrow['Newsbank APA citation (article)'] === NB['Newsbank APA citation (article)'] && wrow['Section'] === 'Metro' && wrow['Page'] === 'A5' && wrow['Publisher link'] === 'https://www.valleygazette-test.com/2026/11/clean-air' && /also found by NewsBank/.test(wrow['Team note']), JSON.stringify(wrow));
  check('its reprint row now belongs to the web story; its saved page, tone and author documents are gone; the run lists why it was left out', runs['run-nb'].rows[0]['Story ID'] === wrow['Story ID'] && runs['run-nb'].rows[0]['Original or reprint'] === 'Reprint' && (await sessDocs(page, 'pages')).length === 0 && (await sessDocs(page, 'tones')).length === 0 && (await sessDocs(page, 'authors')).length === 0 && runs['run-nb'].left.length === 1 && !runs['run-nb'].stories.includes('jg-nb0001') && runs['run-web'].reprints.some(x => x.outlet === 'Other Daily'), JSON.stringify([runs['run-nb'].rows, runs['run-nb'].left]));
  await page.evaluate(() => window.__station.xdReconcile()); runs = Object.fromEntries(await sessDocs(page, 'runs'));
  check('a second check changes nothing', runs['run-nb'].rows.length === 1 && runs['run-nb'].left.length === 1);
  await putRun(page, 'run-web', W('run-web', '2026-11-03T10:00:00Z', [R('w1')])); await settle(page);
  runs = Object.fromEntries(await sessDocs(page, 'runs'));
  check('the web run saved again without them: the folded cells come back (blanks only)', runs['run-web'].rows[0]['NewsBank article link'] === NB['NewsBank article link']);
  await X.close();

  X = await fresh(); page = X.page;   // PDF source first (earlier), web run after: the web row still wins; the PDF run's reprint row moves to the web run (it comes later)
  const nb2 = Object.assign(R('n1', { 'Data Source': 'Newsbank', 'Tracker story code': 'jg-nb0001', 'Publisher link': '' }), NB), kid2 = Object.assign({}, kid);
  await putRun(page, 'run-nb', W('run-nb', '2026-11-03T09:00:00Z', [nb2, kid2], { mode: 'newsbank'}));
  await putRun(page, 'run-web', W('run-web', '2026-11-03T10:00:00Z', [R('w1')])); await settle(page);
  runs = Object.fromEntries(await sessDocs(page, 'runs'));
  check('PDF first, web second: same result, the reprint row is moved to the later web run so its story is placed first', runs['run-nb'].rows.length === 0 && runs['run-web'].rows.length === 2 && runs['run-web'].rows[1]['Story ID'] === runs['run-web'].rows[0]['Story ID'] && runs['run-web'].rows[0]['NewsBank article link'] === NB['NewsBank article link'], JSON.stringify(runs['run-web'].rows.map(r => [r['Original or reprint'], r['Story ID']])));
  await X.close();

  X = await fresh(); page = X.page;   // another outlet's copy = a reprint of the story that ran first; unrelated and same-source rows and a run still going are left alone
  const pq = R('p1', { 'Data Source': 'ProQuest', Outlet: 'Other Daily', Date: '2026-11-04', 'Publisher link': '', 'ProQuest link': 'https://www.proquest.com/docview/12345678', 'Tracker story code': 'jg-pq0001', Topic: 'x', Tone: 'Neutral' });
  const other = R('o1', { 'Data Source': 'ProQuest', Outlet: 'Third Daily', Date: '2026-09-01', Headline: 'A completely different story about school lunches', 'Publisher link': '', 'Tracker story code': 'jg-pq0002' });
  await putDoc(page, 'pages', 'jg-pq0001', { url: 'https://www.proquest.com/docview/12345678', title: HL, clean: '<p>x</p>', pq: { docid: '12345678', file: '', header: {} } });
  await putRun(page, 'run-web', W('run-web', '2026-11-03T10:00:00Z', [R('w1')]));
  await putRun(page, 'run-pq', W('run-pq', '2026-11-04T10:00:00Z', [pq, other], { mode: 'hand' }));
  await putRun(page, 'run-live', Object.assign(W('run-live', '2026-11-04T11:00:00Z', [R('l1', { 'Tracker story code': 'jg-live01' })]), { status: 'running' }));
  await settle(page); runs = Object.fromEntries(await sessDocs(page, 'runs'));
  const rp = runs['run-pq'].rows.find(r => r['Article ID'] === 'NEW-run-p1');
  check('another outlet’s copy becomes a Reprint row of the story that ran first (web, 11-03): its story, its page document kept, its tone/topic cleared', rp && rp['Original or reprint'] === 'Reprint' && rp['Story ID'] === 'sNEW-run-w1' && rp._page === 'jg-pq0001' && !rp.Tone && !rp.Topic && (await sessDocs(page, 'pages')).length === 1 && runs['run-web'].reprints.some(x => x.outlet === 'Other Daily'), JSON.stringify(rp));
  check('unrelated rows stay; a run still going is not touched', runs['run-pq'].rows.some(r => r['Article ID'] === 'NEW-run-o1' && r['Original or reprint'] === 'Original') && runs['run-live'].rows.length === 1 && runs['run-live'].rows[0]['Original or reprint'] === 'Original');
  await X.close();

  /* N7 end to end with a page: the web run first, then a picture of the same story -> shown once; and the other order, with automatic mode on */
  X = await fresh(); page = X.page;
  await putRun(page, 'run-web', W('run-web', '2026-11-03T10:00:00Z', [R('w1')]));
  await q(page, [read('Valley Gazette Test', '2026-11-03', 'A5', 'high', [art(HL)])]);
  await dropImg(page, 'x1'); await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 120000 }); await page.waitForTimeout(600);
  runs = Object.fromEntries(await sessDocs(page, 'runs')); const ppRun = Object.values(runs).find(r => r.mode === 'hand');
  check('web run, then a picture of the same story: the page’s row is folded into the web row, one Original in the session', ppRun.rows.length === 0 && runs['run-web'].rows.length === 1 && /also found by a newspaper page/.test(runs['run-web'].rows[0]['Team note']) && /Same story/.test(await page.textContent('#nbBody')), JSON.stringify(Object.values(runs).map(r => r.rows.length)));
  await X.close();
  X = await fresh({ auto: true }); page = X.page;
  await q(page, [read('Valley Gazette Test', '2026-11-03', 'A5', 'high', [art(HL)])]);
  await page.setInputFiles('#nbFile', { name: 'auto.png', mimeType: 'image/png', buffer: Buffer.from(await png(page, 'auto'), 'base64') });
  await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 120000 });
  await putRun(page, 'run-web', W('run-web', '2026-11-03T10:00:00Z', [R('w1')]));
  await page.waitForTimeout(8000);
  const dl0 = await page.evaluate(() => window.__dl.length);
  await page.waitForFunction(() => !document.querySelector('#stPack').disabled, null, { timeout: 60000 });
  await page.click('#stPack');
  await page.waitForFunction(() => window.__dl && window.__dl.length > 0, null, { timeout: 120000 });
  check('automatic mode: nothing downloaded by itself; the button gives exactly one folder', dl0 === 0 && (await page.evaluate(() => window.__dl.length)) === 1, dl0);
  const zr = await page.evaluate(async () => { const runs = [...window.__station.sess.runs].map(([id, v]) => v.data.rows.length + ':' + (v.data.rows[0] ? v.data.rows[0]['Data Source'] : '')); return runs; });
  check('picture first, web run second, automatic mode on: a single Original is in the update folder', zr.filter(x => /^1:/.test(x)).length === 1 && zr.some(x => /^1:Web/.test(x)) && zr.filter(x => /^[1-9]/.test(x)).length === 1, JSON.stringify(zr));
  await X.close();
  console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
