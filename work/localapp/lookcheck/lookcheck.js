// SAMELOOK-v2 side-by-side capture: the live tracker's own published files (reference) against the PC page, same engine, same viewport.
//   node lookcheck.js --ref http://127.0.0.1:8801/index.html --pc http://127.0.0.1:8802/ --out DIR [--vp 1440x900] [--only a,b] [--fonts auto|google|bundled]
//         [--fontdir work/localapp/fonts/files] [--runs 1]
// For each scenario and each target (a fresh browser context each: empty storage, fixed clock, reduced motion, deviceScaleFactor 1) it writes
//   DIR/<vp>/<target>/<scenario>.png        full-page screenshot (capped at MAXH px)
//   DIR/<vp>/<target>/<scenario>.styles.json  computed styles + boxes of every visible element, keyed by DOM path (the saved-copy frame included)
//   DIR/<vp>/<target>/<scenario>.meta.json  hash, counts, text, mask rectangles, downloads, errors
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/opt/node-tools/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const REF = arg('ref'), PC = arg('pc'), OUT = arg('out'), VP = arg('vp', '1440x900'), ONLY = arg('only', ''), FONTS = arg('fonts', 'auto');
const FONTDIR = arg('fontdir', path.resolve(__dirname, '..', 'fonts', 'google'));
const RUNTAG = arg('tag', '');
const [VW, VH] = VP.split('x').map(Number);
const PHONE = VW <= 640;
const MAXH = 16000;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const FIXED = new Date('2026-11-02T19:30:00-08:00');   // a Monday evening in Los Angeles: "Good evening", the 30 / 90 day windows
// Elements the PC build hides on purpose (station_server.HIDE_CSS), and what it adds: the recorded exceptions
const HIDE_SEL = '#runFind,#runRefresh,#raStrip,[data-runfind],#updGo,#updRefresh,#updSave,#updAdd,#updCopy,#updAgain,[data-trate],[data-afind],[data-trstory],[data-tstop],[data-astop]';
const ADDED_SEL = '#ajgf,#ajgf-btn,#ajgf *';
const STORY_OLD = process.env.LC_STORY_OLD || 's04743';        // 2015 story with 5 embedded photos (jgimg:)
const STORY_DATA = process.env.LC_STORY_DATA || 's02546';       // 2025 story with data: photos

// ---------------------------------------------------------------- fonts (the reference asks Google Fonts, exactly as the live tracker does)
// auto (default): the real answer from Google, kept in a cache folder after the first time so every later run (and both viewports) gets the very same bytes;
//   if Google cannot be reached and nothing is cached yet, the reference gets work/localapp/fonts/google (the files Google served when they were fetched) and
//   the report says so. google: always ask Google (no cache). bundled: only fonts/google.
const FONTCACHE = arg('fontcache', path.join(OUT, '_fontcache'));
const crypto = require('crypto');
const FONTSTAT = { google: 0, cache: 0, bundled: 0 };
function bundledAnswer(url) {
  const GD = FONTDIR;
  if (url.includes('fonts.googleapis.com')) {
    const css = fs.readFileSync(path.join(GD, new URL(url).searchParams.get('family') && /ital/.test(url) ? 'viewer.css' : 'page.css'), 'utf8')
      .replace(/url\(\.\/([^)]+)\)/g, 'url(https://fonts.gstatic.com/lc/$1)');
    return { contentType: 'text/css', body: css };
  }
  return { contentType: 'font/woff2', body: fs.readFileSync(path.join(GD, url.split('/lc/')[1])) };
}
async function fontRoutes(ctx, mode) {
  if (mode === 'google') return;
  fs.mkdirSync(FONTCACHE, { recursive: true });
  await ctx.route(/fonts\.(googleapis|gstatic)\.com/, async route => {
    const url = route.request().url(), H = { 'access-control-allow-origin': '*' };
    if (mode === 'bundled' || url.includes('/lc/')) { const r = bundledAnswer(url); FONTSTAT.bundled++; return route.fulfill({ status: 200, ...r, headers: H }); }
    const key = path.join(FONTCACHE, crypto.createHash('sha1').update(url).digest('hex'));
    if (fs.existsSync(key)) { FONTSTAT.cache++; return route.fulfill({ status: 200, contentType: fs.readFileSync(key + '.type', 'utf8'), body: fs.readFileSync(key), headers: H }); }
    for (let i = 0; i < 3; i++) {
      try {
        const r = await route.fetch({ timeout: 15000 }); const body = await r.body();
        if (r.status() !== 200) throw new Error('status ' + r.status());
        fs.writeFileSync(key, body); fs.writeFileSync(key + '.type', r.headers()['content-type'] || 'application/octet-stream'); FONTSTAT.google++;
        return route.fulfill({ status: 200, contentType: r.headers()['content-type'], body, headers: H });
      } catch (e) { await sleep(500); }
    }
    FONTSTAT.bundled++; const r = bundledAnswer(url); console.log('WARNING: Google Fonts unreachable and not cached, the reference gets fonts/google for', url.slice(0, 80));
    return route.fulfill({ status: 200, ...r, headers: H });
  });
}

// ---------------------------------------------------------------- page helpers
async function settle(p, ms = 500) {
  await p.waitForFunction(() => document.fonts && document.fonts.status === 'loaded', null, { timeout: 30000 }).catch(() => { });
  await p.evaluate(() => document.fonts.ready).catch(() => { });
  await p.evaluate(async () => {   // images (saved-copy frame included) finished
    const docs = [document, ...[...document.querySelectorAll('iframe')].map(f => { try { return f.contentDocument; } catch (e) { return null; } }).filter(Boolean)];
    for (const d of docs) { await Promise.all([...d.images].filter(i => !i.complete).map(i => new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 8000); }))); try { await d.fonts.ready; } catch (e) { } }
  }).catch(() => { });
  await p.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
  await sleep(ms);
}
async function boot(p, hash) {
  // Load twice. The first load fetches the fonts (Google answers in 50-300 ms, the PC's own server in 2 ms), so the two pages would paint their first frame at
  // different moments (fallback face, then the real one) and Skia anti-aliases rounded corners a little differently after a repaint than after a first paint.
  // The second load finds the fonts already in the browser's cache in both, so both paint the same way. Storage stays empty (nothing is written by a bare load).
  await p.goto(p.__base + (hash || ''), { waitUntil: 'load' });
  await settle(p, 1500);
  await p.reload({ waitUntil: 'load' });
  await p.waitForSelector('nav.tabs button[data-tab]', { timeout: 60000 });
  // the saved-page text index is built in the background; the Clips search says "Indexing saved pages…" until it is ready
  await p.waitForFunction(() => { const q = document.querySelector('#q'); return !q || !/index/i.test(q.placeholder); }, null, { timeout: 120000 }).catch(() => { });
  await settle(p, 800);
}
const setHash = async (p, h) => { await p.evaluate(h => { location.hash = h; }, h); await sleep(700); };
const clickTab = async (p, tab, tb) => { await p.click(`nav.tabs button[data-tab="${tab}"]${tb ? `[data-tb="${tb}"]` : ''}`); await sleep(1500); };
async function railOpen(p) { return p.evaluate(() => { const r = document.querySelector('#view-db #rail'); if (!r) return false; const b = r.getBoundingClientRect(); return b.right > 20 && b.width > 0; }); }
async function openRail(p) { if (!(await railOpen(p))) { await p.click('#openRail'); await sleep(700); } }   // the filter rail is a drawer at every width
async function closeRail(p) { if (await railOpen(p)) { await p.click('#closeRail'); await sleep(700); } }
async function openStory(p, id) {
  const hl = await p.evaluate(id => { const d = JSON.parse(document.getElementById('data').textContent).find(r => r.id === id); return d ? d.hl : null; }, id);
  if (!hl) throw new Error('no story ' + id);
  await clickTab(p, 'db'); await p.fill('#q', hl); await sleep(1200);
  await p.locator(`#tbody tr[data-id="${id}"]`).first().locator('td').nth(1).click(); await sleep(1500);
  await p.waitForSelector('#sheet:not([hidden])', { timeout: 10000 });
  await p.waitForSelector('#doc iframe', { timeout: 30000 }).catch(() => { });
  await sleep(1500);
}
async function checkNth(p, scope, f, n) {
  const inp = p.locator(`${scope} input[data-f="${f}"]`).nth(n);
  if (!(await inp.isVisible())) { await inp.locator('xpath=ancestor::details[1]/summary').click(); await sleep(400); }   // open the facet like a person does
  await inp.locator('xpath=ancestor::label[1]').click(); await sleep(700);
}

// ---------------------------------------------------------------- scenarios
// run(p): after the page is booted at `hash`. shot: 'full' (default) | 'view' (viewport only, for scrolled states). A scenario may set p.__hover etc.
const SC = [];
const sc = (name, hash, run, o) => SC.push(Object.assign({ name, hash: hash || '', run }, o || {}));
sc('home', '');
sc('clips', '#clips');
sc('clips_f1', '#clips', async p => { await openRail(p); await checkNth(p, '#view-db', 'topic', 1); await checkNth(p, '#view-db', 'media', 0); await closeRail(p); });
sc('clips_f2', '#clips', async p => { await openRail(p); await checkNth(p, '#view-db', 'reach', 1); await p.selectOption('#when', { index: 3 }); await sleep(600); await closeRail(p); });
sc('clips_f3', '#clips', async p => { await openRail(p); await checkNth(p, '#view-db', 'depth', 0); await checkNth(p, '#view-db', 'topic', 0); await checkNth(p, '#view-db', 'topic', 2); await closeRail(p); });
sc('clips_search', '#clips', async p => { await p.fill('#q', 'housing'); await sleep(1500); });
sc('clips_sort_dense', '#clips', async p => { await p.click('#density'); await p.click('[data-sort="hl"]'); await sleep(800); });
sc('clips_scrolled', '#clips', async p => { await p.evaluate(() => window.scrollTo(0, 1800)); await sleep(700); }, { shot: 'view' });
sc('data_off', '#data');
sc('data_on', '#clips', async p => {   // the switch is in the Clips filter rail (List-only mentions); the Data tab follows it
  await openRail(p); const lo = p.locator('#view-db [data-lo]').first();
  if (!(await lo.isVisible())) { await lo.locator('xpath=ancestor::details[1]/summary').click(); await sleep(400); }
  await lo.locator('xpath=ancestor::label[1]').click(); await sleep(700); await closeRail(p); await clickTab(p, 'an'); await sleep(1500);
});
sc('data_hover', '#data', async p => {
  const el = p.locator('#view-an svg rect, #view-an svg circle, #view-an svg path[class]').filter({ hasNot: p.locator('nothing') });
  const n = await el.count(); let done = false;
  for (let i = 0; i < Math.min(n, 400) && !done; i++) {
    const e = el.nth(i); const bb = await e.boundingBox().catch(() => null);
    if (bb && bb.width > 4 && bb.height > 4 && bb.y > 150 && bb.y < VH - 50) { await p.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2); await sleep(500); done = true; }
  }
}, { shot: 'view' });
sc('reporters', '#reporters');
sc('reporters_scrolled', '#reporters', async p => { await p.evaluate(() => window.scrollTo(0, 1200)); await sleep(700); }, { shot: 'view' });
sc('outlets', '#outlets');
sc('outlets_scrolled', '#outlets', async p => { await p.evaluate(() => window.scrollTo(0, 1200)); await sleep(700); }, { shot: 'view' });
sc('releases', '#press-releases');
sc('releases_scrolled', '#press-releases', async p => { await p.evaluate(() => window.scrollTo(0, 1500)); await sleep(700); }, { shot: 'view' });
sc('release_page', '#press-releases', async p => { await p.locator('.tt-open').first().click(); await sleep(2000); });
sc('bills', '#bills');
sc('bills_scrolled', '#bills', async p => { await p.evaluate(() => window.scrollTo(0, 1500)); await sleep(700); }, { shot: 'view' });
sc('bill_page', '#bills', async p => { await p.locator('#view-tb .tt-open').first().click(); await sleep(2500); });   // AB 418, with the milestones chart
sc('bill_hover', '#bills', async p => {
  await p.locator('#view-tb .tt-open').first().click(); await sleep(2500);
  const el = p.locator('#view-tb svg circle'); const n = await el.count();
  for (let i = 0; i < Math.min(n, 300); i++) { const bb = await el.nth(i).boundingBox().catch(() => null); if (bb && bb.width > 3 && bb.y > 150 && bb.y < VH - 60 && bb.x > 5 && bb.x < VW - 5) { await p.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2); await sleep(600); break; } }
}, { shot: 'view' });
sc('travel', '#story-travel');
sc('travel_scrolled', '#story-travel', async p => { await p.evaluate(() => window.scrollTo(0, 2500)); await sleep(700); }, { shot: 'view' });
sc('data_scrolled', '#data', async p => { await p.evaluate(() => window.scrollTo(0, 2500)); await sleep(700); }, { shot: 'view' });
sc('story_sheet', '#clips', async p => { await p.locator('#tbody tr[data-id]').first().locator('td').nth(1).click(); await sleep(2500); });
sc('story_sheet_wide', '#clips', async p => { await p.locator('#tbody tr[data-id]').first().locator('td').nth(1).click(); await sleep(1500); { const w = p.locator('[data-wide]'); if (await w.isVisible()) await w.click(); }   // the full-page view button is hidden in a half-width window
    await sleep(2500); });
sc('saved_copy_old', '#clips', async p => { await openStory(p, STORY_OLD); });
sc('saved_copy_data', '#clips', async p => { await openStory(p, STORY_DATA); });
sc('saved_copy_old_wide', '#clips', async p => { await openStory(p, STORY_OLD); { const w = p.locator('[data-wide]'); if (await w.isVisible()) await w.click(); }   // the full-page view button is hidden in a half-width window
    await sleep(2500); });
sc('saved_copy_old_mid', '#clips', async p => { await openStory(p, STORY_OLD); await p.evaluate(() => { const s = document.querySelector('#sheet'); s.scrollTop = 700; }); await sleep(700); }, { shot: 'view' });
sc('saved_copy_old_end', '#clips', async p => { await openStory(p, STORY_OLD); await p.evaluate(() => { const s = document.querySelector('#sheet'); s.scrollTop = s.scrollHeight; }); await sleep(700); }, { shot: 'view' });
sc('saved_copy_data_end', '#clips', async p => { await openStory(p, STORY_DATA); await p.evaluate(() => { const s = document.querySelector('#sheet'); s.scrollTop = s.scrollHeight; }); await sleep(700); }, { shot: 'view' });
// v64 additions (RELXLOOK-v1, YTBROADCAST-v1, RELRECS-v1)
const STORY_YT = process.env.LC_STORY_YT || 's04941';          // a station clip: Broadcast segment with an A/V YouTube link
async function openReleaseWith(p, needles) {                   // walks the release list until a page shows every needle (same walk on both targets)
  const n = await p.locator('.tt-open').count();
  for (let i = 0; i < Math.min(n, 120); i++) {
    await p.locator('.tt-open').nth(i).click(); await sleep(700);
    const txt = await p.evaluate(() => document.body.innerText);
    if (needles.every(x => txt.includes(x))) return i;
    await p.evaluate(() => history.back()); await sleep(500);
  }
  throw new Error('no release page with ' + needles.join(' + '));
}
sc('release_page_later', '#press-releases', async p => { await openReleaseWith(p, ['Later coverage', 'Possibly related']); await sleep(1200); });
sc('release_page_pick', '#press-releases', async p => { await openReleaseWith(p, ['Picked up']); await sleep(1200); });
sc('story_yt_clip', '#clips', async p => { await openStory(p, STORY_YT); const t = await p.evaluate(() => document.querySelector('#sheet').innerText); if (!/YouTube \(station clip\)/.test(t)) throw new Error('no "YouTube (station clip)" link in the story sheet'); });
const trOpen = async (p, lab) => { const s = p.locator('#view-tb details > summary').filter({ hasText: lab }).first(); if (await s.count()) { await s.scrollIntoViewIfNeeded(); await s.click(); await sleep(400); } };
sc('releases_facets', '#press-releases', async p => { await trOpen(p, /^\s*Outlet, related stories/); await trOpen(p, /^\s*Pickup/); await trOpen(p, /^\s*Reporter, related stories/); await sleep(500); });
sc('releases_quiet', '#press-releases', async p => {
  await trOpen(p, /^\s*Pickup/);
  const lab = p.locator('#view-tb label', { hasText: 'Nothing after 30 days' }).first(); if (!(await lab.count())) throw new Error('no Pickup choice'); await lab.click(); await sleep(1200);
});
sc('manage', '#clips', async p => { await p.click('#updBtn'); await sleep(1500); });

// ---------------------------------------------------------------- the dump
const DUMP = ({ HIDE_SEL, ADDED_SEL }) => {
  const PROPS = ['fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'lineHeight', 'letterSpacing', 'color', 'backgroundColor', 'borderRadius', 'padding', 'margin', 'width', 'height',
    'textTransform', 'textDecorationLine', 'boxShadow', 'opacity', 'display', 'position', 'borderTopColor', 'borderTopWidth', 'borderBottomWidth', 'borderTopStyle', 'cursor', 'overflow', 'textAlign', 'zIndex'];
  const out = [], masks = [], hidden = [];
  const doc = document;
  function walk(d, win, prefix, mx, my) {
    const sy = win.scrollY, sx = win.scrollX;
    const all = d.documentElement ? [d.documentElement, ...d.documentElement.querySelectorAll('*')] : [];
    for (const el of all) {
      const tag = el.tagName.toLowerCase();
      if (['script', 'style', 'link', 'meta', 'head', 'title', 'noscript', 'base'].includes(tag) || el.closest('head')) continue;
      let r; try { r = el.getBoundingClientRect(); } catch (e) { continue; }
      const cs = win.getComputedStyle(el);
      const isHidden = d === doc && (el.matches(HIDE_SEL));
      const isAdded = d === doc && el.matches(ADDED_SEL);
      if (isHidden && r.width > 0 && r.height > 0) masks.push({ x: r.x + sx + mx, y: r.y + sy + my, w: r.width, h: r.height, why: 'hidden:' + (el.id || el.className || tag) });
      if (isAdded && r.width > 0 && r.height > 0 && getComputedStyle(el).position === 'fixed') masks.push({ x: r.x + mx, y: r.y + my, w: r.width, h: r.height, why: 'added:' + el.id, fixed: true });
      if (isHidden || isAdded || el.closest(HIDE_SEL) || el.closest('#ajgf,#ajgf-btn')) { if (isHidden) hidden.push(prefix + el.tagName); continue; }
      if (r.width === 0 && r.height === 0) continue;
      if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      // DOM path
      const parts = []; for (let n = el; n && n.nodeType === 1; n = n.parentElement) { const p = n.parentElement; const i = p ? [...p.children].filter(c => !['SCRIPT', 'STYLE', 'LINK', 'META', 'TITLE', 'NOSCRIPT', 'BASE'].includes(c.tagName)).indexOf(n) : 0; parts.unshift(n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') + ':' + i); }
      const rec = { k: prefix + parts.join('>'), tag, t: ([...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim().replace(/\s+/g, ' ')).slice(0, 40),
        x: +(r.x + sx).toFixed(2), y: +(r.y + sy).toFixed(2), w: +r.width.toFixed(2), h: +r.height.toFixed(2) };
      for (const pr of PROPS) rec[pr] = cs[pr];
      if (rec.t) { rec.__text = 1; }
      out.push(rec);
    }
  }
  walk(doc, window, '', 0, 0);
  for (const f of doc.querySelectorAll('iframe')) {
    let d; try { d = f.contentDocument; } catch (e) { d = null; } if (!d || !f.contentWindow) continue;
    const r = f.getBoundingClientRect();
    walk(d, f.contentWindow, 'iframe/', r.x + window.scrollX, r.y + window.scrollY);
  }
  return { els: out, masks, hidden: hidden.length, scroll: [window.scrollX, window.scrollY], docH: doc.documentElement.scrollHeight, docW: doc.documentElement.scrollWidth };
};

async function platformFonts(p, cdp) {
  // the face Chromium really used for each text-bearing element (family names + glyph counts)
  const n = await p.evaluate((HS) => {
    let i = 0;
    const mark = (d) => { const w = d.createTreeWalker(d.documentElement, NodeFilter.SHOW_TEXT); let t; while ((t = w.nextNode())) { const el = t.parentElement; if (!el || !t.textContent.trim() || el.closest('head,script,style,#ajgf,#ajgf-btn') || el.closest(HS)) continue; if (!el.hasAttribute('data-lcn')) el.setAttribute('data-lcn', i++); } };
    mark(document); for (const f of document.querySelectorAll('iframe')) { try { mark(f.contentDocument); } catch (e) { } }
    return i;
  }, HIDE_SEL);
  return n;
}

async function capture(browser, target, base, sc_, dir, errors) {
  const ctx = await browser.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: 1, reducedMotion: 'reduce', locale: 'en-US', timezoneId: 'America/Los_Angeles', acceptDownloads: true });
  await ctx.clock.install({ time: FIXED });
  if (target !== 'pc') await fontRoutes(ctx, FONTS);
  else await ctx.route(/fonts\.(googleapis|gstatic)\.com/, r => { errors.push('pc: outside font request ' + r.request().url()); r.abort(); });
  const p = await ctx.newPage(); p.__base = base;
  p.on('pageerror', e => errors.push(`${target}: pageerror ${String(e).slice(0, 200)}`));
  p.on('console', m => { if (m.type() === 'error') errors.push(`${target}: console ${m.text().slice(0, 200)}`); });
  const meta = { target, scenario: sc_.name };
  try {
    await boot(p, sc_.hash);
    // refhide: the reference with the recorded exception applied (the same hiding rule the PC's page server adds), to prove that nothing but the exception differs
    if (target === 'refhide') { await p.addStyleTag({ content: HIDE_SEL + '{display:none!important}' }); await sleep(300); }
    if (sc_.run) await sc_.run(p);
    await settle(p, 400);
    // Flush the raster: a 1 px width change and back makes Chromium lay out and paint everything again from the final DOM. Without it the pixels of a few rounded
    // corners (about 30 of 1.3 million, at most 12 levels) depend on how many times a region was repainted on the way (the PC page, which has window.claude,
    // re-renders more than the reference, which has none). The same step runs on both targets.
    await p.setViewportSize({ width: VW + 1, height: VH }); await sleep(500); await p.setViewportSize({ width: VW, height: VH }); await sleep(900); await settle(p, 300);
    // the story sheet is a layer of its own: hide and show it so that it too is painted afresh (its frame keeps its document)
    if (await p.evaluate(() => { const s = document.querySelector('#sheet'); if (!s || s.hidden) return false; s.style.display = 'none'; s.offsetHeight; s.style.display = ''; return true; })) await sleep(900);
    // the same for scrolling panels (the story sheet): nudge each by one pixel and back, which repaints what is inside them from the final DOM
    const nudged = await p.evaluate(() => { const els = [...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 2 && /(auto|scroll)/.test(getComputedStyle(e).overflowY) && e.scrollTop + 1 < e.scrollHeight - e.clientHeight); els.forEach(e => { e.__st = e.scrollTop; e.scrollTop = e.__st + 1; }); return els.length; });
    if (nudged) { await sleep(300); await p.evaluate(() => { document.querySelectorAll('*').forEach(e => { if (e.__st !== undefined) { e.scrollTop = e.__st; delete e.__st; } }); }); await sleep(500); }
    await p.evaluate(() => { if (document.activeElement && document.activeElement !== document.body && !/^(input|textarea|select)$/i.test(document.activeElement.tagName)) document.activeElement.blur(); });
    const cdp = await ctx.newCDPSession(p);
    const dump = await p.evaluate(DUMP, { HIDE_SEL, ADDED_SEL });
    meta.masks = dump.masks; meta.scroll = dump.scroll; meta.docH = dump.docH; meta.docW = dump.docW; meta.hash = await p.evaluate(() => location.hash);
    meta.state = await p.evaluate(({ HIDE_SEL, ADDED_SEL }) => ({
      rows: document.querySelectorAll('#tbody tr').length, count: ((document.querySelector('#count,.count,#resCount') || {}).textContent || '').trim(),
      sheet: !document.querySelector('#sheet').hidden,
      text: (() => { const els = [...document.querySelectorAll(HIDE_SEL + ',' + ADDED_SEL)], old = els.map(e => e.style.display); els.forEach(e => { e.style.display = 'none'; });
        const s = document.body.innerText; els.forEach((e, i) => { e.style.display = old[i]; });
        let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return s.length + ':' + h; })(),
      tabs: [...document.querySelectorAll('nav.tabs button')].map(b => b.textContent.trim() + (b.getAttribute('aria-selected') === 'true' ? '*' : ''))
    }), { HIDE_SEL, ADDED_SEL });
    const shotOpts = sc_.shot === 'view' ? { path: path.join(dir, sc_.name + '.png') } : { path: path.join(dir, sc_.name + '.png'), fullPage: true };
    // fixed-position panels (the PC's Tracker files button) are painted over the page: capture, then the diff masks them
    if (shotOpts.fullPage && dump.docH > MAXH) { shotOpts.clip = { x: 0, y: 0, width: VW, height: MAXH }; }
    await p.screenshot(shotOpts);
    // resolved faces
    const n = await platformFonts(p, cdp);
    const faces = {};
    if (n) {
      await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
      const { root } = await cdp.send('DOM.getDocument', { depth: -1, pierce: true });
      const { nodeIds } = await cdp.send('DOM.querySelectorAll', { nodeId: root.nodeId, selector: '[data-lcn]' });
      for (const id of nodeIds) {
        try {
          const { attributes } = await cdp.send('DOM.getAttributes', { nodeId: id }); const i = attributes[attributes.indexOf('data-lcn') + 1];
          const { fonts } = await cdp.send('CSS.getPlatformFontsForNode', { nodeId: id });
          faces[i] = fonts.map(f => `${f.familyName}|${f.postScriptName}|${f.isCustomFont ? 'web' : 'sys'}|${f.glyphCount}`).join(';');
        } catch (e) { }
      }
    }
    // join faces onto the element records by the order of the walk (same order, same filter)
    const rec2 = await p.evaluate(() => {
      const res = []; const add = (d, prefix) => { for (const el of d.querySelectorAll('[data-lcn]')) res.push([prefix, el.getAttribute('data-lcn'), el.tagName.toLowerCase(), [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim().replace(/\s+/g, ' ').slice(0, 40)]); };
      add(document, ''); for (const f of document.querySelectorAll('iframe')) { try { add(f.contentDocument, 'iframe/'); } catch (e) { } }
      return res;
    });
    meta.faces = rec2.map(([pre, i, tag, t]) => ({ pre, tag, t, face: faces[i] || '' }));
    fs.writeFileSync(path.join(dir, sc_.name + '.styles.json'), JSON.stringify(dump.els));
  } catch (e) { meta.error = String(e).slice(0, 400); errors.push(`${target}/${sc_.name}: ${meta.error}`); try { await p.screenshot({ path: path.join(dir, sc_.name + '.error.png') }); } catch (x) { } }
  fs.writeFileSync(path.join(dir, sc_.name + '.meta.json'), JSON.stringify(meta));
  await ctx.close();
  return meta;
}

(async () => {
  const names = ONLY ? ONLY.split(',') : SC.map(s => s.name);
  const browser = await chromium.launch();
  const errors = [];
  for (const target of ['ref', 'pc', 'refhide']) fs.mkdirSync(path.join(OUT, VP + RUNTAG, target), { recursive: true });
  for (const s of SC.filter(s => names.includes(s.name))) {
    const t0 = Date.now();
    const [a, b, c] = await Promise.all([
      capture(browser, 'ref', REF, s, path.join(OUT, VP + RUNTAG, 'ref'), errors),
      capture(browser, 'pc', PC, s, path.join(OUT, VP + RUNTAG, 'pc'), errors),
      capture(browser, 'refhide', REF, s, path.join(OUT, VP + RUNTAG, 'refhide'), errors)]);
    console.log(`${s.name}: ${((Date.now() - t0) / 1000).toFixed(1)}s ${a.error || ''} ${b.error || ''} ${c.error || ''}`);
  }
  console.log('reference fonts: from Google', FONTSTAT.google, ' from the cache', FONTSTAT.cache, ' from fonts/google', FONTSTAT.bundled);
  fs.writeFileSync(path.join(OUT, VP + RUNTAG, 'errors.json'), JSON.stringify([...new Set(errors)], null, 1));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
