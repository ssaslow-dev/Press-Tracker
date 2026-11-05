/* STFIX: Sammy's first real Update run (2026-11-05), findings 1-4 on the REAL batch multi4.pdf (85 pages: 13 text stories, 14 "Full Page" print pages) and finding 5 (a web run that ends early).
   Claude is a FAKE: its classify answers repeat the wrong guesses the real one made (the publisher group as the outlet, a headline as the outlet, "Associated Press" for a local paper's print copy), and every
   request to read a page picture is counted (PRINTREAD-v2: all 14 are sent, as tiles; here Claude cannot make them out, so the pages are placed by outlet, date and page number). Licensed text: AJG_REAL_NB4 names a folder with multi4.pdf and for_update_0bccc1fc.json (skipped without it).
     AJG_REAL_NB4=DIR node tests/stfix/stfix_test.js
   Part B (finding 5) and part C (picture size) need no licensed file. */
const fs = require('fs'), path = require('path'), os = require('os'), { execFileSync } = require('child_process');
const H = require('../nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB4, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json'), HAVE = DIR && fs.existsSync(path.join(DIR, 'multi4.pdf')) && fs.existsSync(FU);
const FU_ANY = HAVE ? FU : (process.env.AJG_REAL_NB2 && path.join(process.env.AJG_REAL_NB2, 'for_update_0bccc1fc.json'));
const PAGE = path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;
const stub = (prompt, o) => {
  if (/^These items come from NewsBank/.test(prompt)) return [...prompt.matchAll(/=== ITEM (\d+)\nURL: (.*)\nPage title: (.*)\n/g)].map(m => {
    const t = m[3], pub = /Mayor Bass Announces \$22 Million/.test(t) ? t : /New Laws Trigger/.test(t) ? 'Associated Press' : /mail-in ballots|Sepulveda Basin|recibe 22 millones/.test(t) ? 'Southern California News Group' : '';
    return { n: +m[1], keep: true, why: 'x', press_release: /MAYOR BASS HIGHLIGHTS/.test(t) ? 'yes' : 'no', pr_why: 'x', date: '', outlet: '', pub, hl: '', topic: 'District / community', media: 'Newspaper', role: 'Mentioned in story', tone: 'Neutral', twhy: '', author: '', lang: /recibe 22 millones/.test(t) ? 'Spanish' : '', hl_en: /recibe 22 millones/.test(t) ? 'Sepulveda Basin receives $22 million' : '', text_en: '' };
  });
  if (/^You are reading a scanned page/.test(prompt)) { window.__pageAsks = (window.__pageAsks || 0) + 1; return { readable: false, articles: [] }; }   // PRINTREAD-v2: every page IS sent (as tiles); this Claude cannot make them out, so the fallback placement is what is tested
  return [];
};
const WEB_STUB = (tool, input, calls) => {   // a TinyFish that answers 25 searches and then loses its connection (a STOP code, as when a connector lapses)
  if (tool === 'search') { window.__nsearch = (window.__nsearch || 0) + 1; if (window.__failAfter && window.__nsearch > window.__failAfter) { const e = new Error('lapsed'); e.code = 'needs_reauth'; throw e; } return { payload: { results: [] } }; }
  return { payload: { results: [], errors: [] } };
};
async function runWeb(page) {
  await page.click('#runFind'); await page.waitForSelector('#rcScrim:not([hidden])'); await page.click('#rcYes');
  await page.waitForFunction(() => { const f = document.querySelector('#updBody'); return f && /Added|Nothing new|Stopped|nothing|Stopped by|found/i.test(f.textContent) && !document.querySelector('#updStop') && !document.querySelector('#runFind.busy'); }, null, { timeout: 240000 });
  await page.waitForTimeout(700);
}
const finalRuns = page => page.evaluate(() => [...window.__station.sess.runs].map(([id, v]) => ({ id, mode: v.data.mode, status: v.data.status, searched_to: v.data.searched_to, ended_early: v.data.ended_early || null })));
(async () => {
  if (HAVE) {
    const X = await H.start(PAGE, stub, { images: 8 }), page = X.page;
    await H.loadFile(page, FU); await H.dropPdf(page, path.join(DIR, 'multi4.pdf'));
    await page.uncheck('#nbLinks').catch(() => {});
    const items0 = await H.items(page);
    check('the batch is read: 27 records = 13 text stories + 14 print pages', items0.length === 27 && items0.filter(i => i.kind === 'print_page').length === 14, items0.length);
    await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 300000 });
    const run = await page.evaluate(() => { const r = window.__station.state.nb.lastRun; const its = window.__station.state.nb.items; return { rows: r.rows, doc: r.doc, items: r.items, pages: its.filter(i => i.p.kind === 'print_page').map(i => ({ key: i.key, outlet: i.p.outlet_clean, date: i.p.date, page: i.p.page, st: i.screen.status, why: i.screen.why, read: i.reading && i.reading.state, pic: i.reading && i.reading.pic, note: i.reading && i.reading.note, readNote: i.readNote, attachTo: i.attachTo, printAs: i.printAs })) }; });
    const asks = await page.evaluate(() => window.__pageAsks || 0);
    /* FINDING 1 */
    check('1. Claude is asked to read every one of the 14 NewsBank page pictures (PRINTREAD-v2: no size gate)', asks === 14, asks);
    check('1. every page is marked unread (Claude could not make it out), none "too small"', run.pages.length === 14 && run.pages.every(p => p.read === 'unclear'), JSON.stringify(run.pages.map(p => p.read)));
    const blob = JSON.stringify([run.doc, run.items, run.pages]);
    check('1. nothing says "no article that names Jesse Gabriel" (the page was not read)', !/no article that names Jesse Gabriel/i.test(blob), (blob.match(/.{60}no article that names.{20}/i) || [''])[0]);
    check('1. the note says why: Claude could not read the page', run.pages.every(p => /could not read the page/.test(p.note || '')), run.pages[0] && run.pages[0].note);
    const byPage = (d, pg) => run.pages.filter(p => p.date === d && String(p.page) === String(pg));
    const nov4 = byPage('2026-11-04', '9').filter(p => /Los Angeles Daily News/.test(p.outlet)), oct3 = byPage('2026-10-27', '3').filter(p => /Los Angeles Daily News/.test(p.outlet)), oct4 = byPage('2026-10-27', '4');
    check('1a. Daily News Nov 4 p.9 is linked to the batch\'s own text record (same outlet, date, page): kept with it, no row of its own', nov4.length === 1 && nov4[0].st === 'attached' && !!nov4[0].attachTo, JSON.stringify(nov4));
    check('1a. Daily News Oct 27 p.3 is linked to the text record "Sepulveda Basin gets $22M": kept with it', oct3.length === 1 && oct3[0].st === 'attached' && !!oct3[0].attachTo, JSON.stringify(oct3));
    const ballots = run.rows.filter(r => /mail-in ballots/i.test(r['Headline']) && r['Original or reprint'] === 'Original'), basin = run.rows.filter(r => /Sepulveda Basin gets \$22M/i.test(r['Headline']) && r['Original or reprint'] === 'Original');
    check('1a. one Original each for those two stories (the pages add no second row)', ballots.length === 1 && basin.length === 1, [ballots.length, basin.length]);
    check('1a. the page PDFs are carried as print originals of those records (print_pages entries "attached")', ['2026-11-04', '2026-10-27'].every(d => (run.doc.print_pages || []).some(x => x.as === 'attached' && x.date === d && x.item)), JSON.stringify((run.doc.print_pages || []).map(x => [x.as, x.date, x.outlet])));
    const att = (run.doc.print_pages || []).filter(x => x.as === 'attached');
    check('1a. every attached page names its item key (batch sha8#index) and the run row + story it belongs to', att.length >= 2 && att.every(x => /^[0-9a-f]{8}#\d+$/.test(x.item) && x.aid && x.story) && att.some(x => ballots.length && x.aid === ballots[0]['Article ID'] && x.story === ballots[0]['Story ID']) && att.some(x => basin.length && x.aid === basin[0]['Article ID'] && x.story === basin[0]['Story ID']), JSON.stringify(att.map(x => [x.item, x.aid, x.story])));
    check('1b. Oct 27 p.4 (no text record of its own) goes to Unlinked print pages with the true reason', oct4.length === 1 && oct4[0].st === 'print_page' && (run.doc.print_rows || []).some(r => r['Date'] === '2026-10-27' && r['Page'] === '4' && /could not read the page/.test(r['Team note'])), JSON.stringify(oct4));
    check('1b. the Oct 25 p.14 page of the Daily Breeze is the print original of the text record already in the tracker (00003)', (run.doc.extra_copies || []).some(x => x.aid === '00003' && x.kind === 'print'), JSON.stringify((run.doc.extra_copies || []).map(x => [x.aid, x.kind])));
    check('1. no row comes from a page picture', !run.rows.some(r => /image\/v2/.test(r['NewsBank print-page link'] || '')), '');
    /* FINDING 2 */
    const dn = run.rows.filter(r => /Daily News/.test(r['Outlet']));
    check('2. the two Daily News text records are filed under "Los Angeles Daily News", not the publisher group', ballots.length === 1 && basin.length === 1 && ballots[0]['Outlet'] === 'Los Angeles Daily News' && basin[0]['Outlet'] === 'Los Angeles Daily News', JSON.stringify([ballots.map(r => r['Outlet']), basin.map(r => r['Outlet'])]));
    const es = run.rows.filter(r => /recibe 22 millones/i.test(r['Headline']));
    check('2. the Spanish Sepulveda story is filed under its own source (Excelsior), not the publisher group', es.length === 1 && /^Excelsior/.test(es[0]['Outlet']), JSON.stringify(es.map(r => r['Outlet'])));
    check('2. no row has Southern California News Group as its Outlet', !run.rows.some(r => /Southern California News Group/.test(r['Outlet'])), '');
    check('2. nothing is filed as "Daily News of Los Angeles"', !run.rows.some(r => /Daily News of Los Angeles/.test(r['Outlet'])), dn.length);
    /* FINDING 3 */
    const sent = run.rows.filter(r => /Sepulveda Basin/.test(r['Headline']) && /Mayor Bass Announces/.test(r['Headline']));
    check('3. the mayor\'s-office story is filed under its source, Los Angeles Sentinel, not its headline', sent.length === 1 && sent[0]['Outlet'] === 'Los Angeles Sentinel', JSON.stringify(sent.map(r => r['Outlet'])));
    check('3. "nathan" is neither the author nor in the citation', sent.length === 1 && !/nathan/i.test(sent[0]['Author / byline'] || '') && !/nathan/i.test(sent[0]['Newsbank APA citation (article)'] || '') && /^Mayor Bass Announces \$22 Million Investment in Sepulveda Basin\. \(2026, October 26\)\. Los Angeles Sentinel/.test(sent[0]['Newsbank APA citation (article)'] || ''), sent[0] && sent[0]['Newsbank APA citation (article)'].slice(0, 160));
    check('3. no spurious "headline differs" flag from the user name', sent.length === 1 && !/differs/.test(sent[0]['Team note'] || ''), sent[0] && sent[0]['Team note']);
    /* FINDING 4 */
    const art = run.rows.filter(r => /Nazi-Looted Art/.test(r['Headline']));
    check('4. the Nazi-looted-art story is filed under the paper that printed it (Newtown Bee, The, Connecticut), not "Associated Press"', art.length === 1 && art[0]['Outlet'] === 'Newtown Bee, The' && art[0]['Edition'] === 'Print' && art[0]['Page'] === '25D', JSON.stringify(art.map(r => [r['Outlet'], r['Edition'], r['Page']])));
    check('4. its AP credit is kept (Author / byline "Associated Press", from the "(AP)" dateline)', art.length === 1 && art[0]['Author / byline'] === 'Associated Press', art[0] && art[0]['Author / byline']);
    check('no outside request, no page error', X.outside.length === 0 && X.errors.length === 0, JSON.stringify([X.outside, X.errors.slice(0, 3)]));
    await X.close();
  } else console.log('SKIP parts A (AJG_REAL_NB4 not set or files absent)');

  /* C. no size gate (PRINTREAD-v2): a 900 px and a 2400 px picture made here are both sent, as tiles at their own size */
  if (FU_ANY) {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'stfixc-'));
    const mk = (n, w, h) => { const f = path.join(tmp, n); execFileSync('python3', ['-I', '-c', 'import sys\nfrom PIL import Image, ImageDraw\nw,h=int(sys.argv[2]),int(sys.argv[3])\nim=Image.new("RGB",(w,h),"white")\nd=ImageDraw.Draw(im)\nfor y in range(0,h,max(8,h//90)): d.rectangle([w//10,y,w*9//10,y+max(2,h//300)],fill=(20,20,20))\nim.save(sys.argv[1])', f, String(w), String(h)]); return f; };
    const small = mk('small.png', 900, 1300), big = mk('big.png', 2400, 3400);
    const stubC = (prompt) => {
      if (/^You are reading a scanned page/.test(prompt)) { window.__pageAsks = (window.__pageAsks || 0) + 1; return { readable: true, masthead: { paper: 'Valley Courier Test', date: '2026-11-02', page: 'A3', confidence: 'high' }, articles: [{ headline: 'Valley schools: Assemblymember Jesse Gabriel visits a classroom', byline: 'By A. Reporter', section: 'Local', page: 'A3', text: 'Assemblymember Jesse Gabriel, D-Northridge, visited a Valley classroom on Monday to talk about school lunch menus and what parents want their children to eat each day, and he said the state would keep funding the program. ' .repeat(2), continues: '', continued_from: '', names_gabriel: true, confidence: 'high' }] }; }
      return [];
    };
    const X = await H.start(PAGE, stubC, { images: 8 }), page = X.page;
    await H.loadFile(page, FU_ANY);
    const have = await page.evaluate(() => window.__station.state.nb.files.length);
    await page.setInputFiles('#nbFile', [small, big]);
    await page.waitForFunction(k => window.__station.state.nb.files.length === k && window.__station.state.nb.files.every(f => f.status !== 'reading') && !window.__station.state.nb.reading, have + 2, { timeout: 120000 });
    await page.uncheck('#nbLinks').catch(() => {});
    await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun || window.__station.state.nb.items.every(i => i.screen.status !== 'print_page' || i.reading), null, { timeout: 120000 }).catch(() => {});
    await page.waitForTimeout(1500);
    const rd = await page.evaluate(() => window.__station.state.nb.items.map(i => ({ st: i.screen.status, read: i.reading && i.reading.state, pic: i.reading && i.reading.pic, why: i.screen.why })));
    const asks = await page.evaluate(() => window.__pageAsks || 0);
    const tl = await page.evaluate(() => window.__calls.filter(c => c.images).map(c => c.images));
    check('C. both pictures are sent to Claude, each as several tiles in one call (no size gate)', rd.length === 2 && rd.every(r => r.read !== 'toosmall') && asks === 2 && tl.length === 2 && tl.every(n => n >= 6), JSON.stringify([rd, asks, tl]));
    await X.close();
  }

  /* B. finding 5: a web run that loses TinyFish part way must say so; a clean run must not */
  if (FU_ANY) {
    for (const scn of ['lapse', 'clean']) {
      const X = await H.start(PAGE, stub, { images: 8, mcpStub: WEB_STUB.toString() }), page = X.page;
      await H.loadFile(page, FU_ANY);
      await page.evaluate(s => { window.__failAfter = s === 'lapse' ? 25 : 0; }, scn);
      await runWeb(page);
      const runs = await finalRuns(page), fin = runs.find(r => r.mode === 'find' && r.status === 'done');
      const noteVisible = await page.evaluate(() => { const e = document.getElementById('stEndNote'); return !!e && !e.hidden && e.textContent; });
      if (scn === 'lapse') {
        check('5. a web run that loses TinyFish part way is written with ended_early (the reason) and an empty searched_to', !!fin && !!fin.ended_early && !fin.searched_to && /TinyFish connection has lapsed/.test(fin.ended_early.why), JSON.stringify(fin));
        check('5. the page shows a red note "did NOT finish ... not the same as nothing new"', /did NOT finish/.test(noteVisible || '') && /nothing new/.test(noteVisible || ''), noteVisible);
        const z = await page.evaluate(async () => { const z = await window.__station.pack(); return z ? z.manifest.runs : null; });
        const warn = await page.evaluate(() => document.getElementById('stPackWarn').textContent);
        check('5. the update folder\'s warnings repeat it', /did not finish/.test(warn), warn);
        const st = await page.evaluate(() => window.__station.sess.runs.size && [...window.__station.sess.runs].map(([, v]) => !!v.data.ended_early));
        check('5. the run document inside the folder carries ended_early', st.some(Boolean), JSON.stringify(st));
        // a second, clean run clears the note
        await page.evaluate(() => { window.__failAfter = 0; window.__nsearch = 0; });
        await runWeb(page);
        const after = await page.evaluate(() => { const e = document.getElementById('stEndNote'); return !e || e.hidden; });
        check('5. a later clean web run clears the note', after, '');
      } else {
        check('5. a clean web run (nothing found, searched_to moved) has no ended_early and no red note', !!fin && !fin.ended_early && !!fin.searched_to && !noteVisible, JSON.stringify([fin, noteVisible]));
      }
      check('5. no page error', X.errors.length === 0, JSON.stringify(X.errors.slice(0, 3)));
      await X.close();
    }
    /* the web run and a PDF add never run at the same time: the Update button during an add says so */
    const X = await H.start(PAGE, stub, { images: 8 }), page = X.page;
    await H.loadFile(page, FU_ANY);
    await page.evaluate(() => { window.__station.state.nb.busy = true; });
    await page.click('#runFind').catch(() => {});
    await page.waitForTimeout(400);
    const scrim = await page.evaluate(() => { const s = document.getElementById('rcScrim'); return s && !s.hidden; }), toast = await page.evaluate(() => (document.getElementById('toast') || {}).textContent || '');
    check('5. pressing Update while PDFs are being added does not start a run (and says why)', !scrim && /PDFs are being added/.test(toast), JSON.stringify([scrim, toast]));
    await page.evaluate(() => { window.__station.state.nb.busy = false; });
    const err = await page.evaluate(async () => { try { window.__nb.screen; } catch (e) {} return 0; });
    await X.close();
  }
  console.log(C.failed ? C.failed + ' FAILED' : 'all passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
