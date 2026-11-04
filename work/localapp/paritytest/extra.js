// PARITYTEST-v1: the interactions the look check's parity.js does not have. Loaded by parity.js with --extra.
// Each test gets (page, base, out) and fills `out` with outcomes (counts, texts, hashes); the same steps run on the live tracker's files and on the PC page.
module.exports = (T, H) => {
  const { sleep, snapClips, tabText, download, exportMenu, sha } = H;
  const hashStr = s => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return h; };
  // db contents through the page's own window.claude (the live side: in-memory stand-in; the PC side: its file store). Times are normalised.
  const dump = (p, cols) => p.evaluate(async cols => {
    const db = await window.claude.use('db'), out = {};
    const norm = v => Array.isArray(v) ? v.map(norm) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).sort().map(([k, x]) => [k, norm(x)])) :
      typeof v === 'number' && v > 1e11 ? 'TS' : typeof v === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d/.test(v) ? 'ISO' : v;
    for (const c of cols) { const s = await db.collection(c).get(); out[c] = s.docs.map(d => [d.id, norm(d.data())]).sort((a, b) => a[0] < b[0] ? -1 : 1); }
    return out; }, cols);
  const sheetFull = p => p.evaluate(() => { const s = document.querySelector('#sheet'); const t = s.innerText; let h = 0; for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) | 0;
    return { open: !s.hidden, len: t.length, hash: h, h2: (s.querySelector('h2') || {}).textContent, links: [...s.querySelectorAll('a[href]')].map(a => a.textContent.trim().slice(0, 40) + '>' + a.getAttribute('href')).join('|'),
      btns: [...s.querySelectorAll('button')].map(b => b.textContent.trim()).filter(Boolean).join('|'), imgs: s.querySelectorAll('img').length }; });
  const openStory = async (p, n) => { await p.click('nav.tabs button[data-tab=db]'); await sleep(1200); await p.fill('#q', ''); await sleep(900);
    await p.locator('#tbody tr[data-id]').nth(n).locator('td').nth(1).click(); await sleep(2200); };
  const openById = async (p, id) => { const hl = await p.evaluate(id => JSON.parse(document.getElementById('data').textContent).find(r => r.id === id).hl, id);
    await p.click('nav.tabs button[data-tab=db]'); await sleep(1000); await p.fill('#q', hl); await sleep(1500); await p.locator(`#tbody tr[data-id="${id}"]`).first().locator('td').nth(1).click(); await sleep(2500); };

  T.edits = async (p, base, out) => {
    await openStory(p, 1); out.before = await sheetFull(p);
    await p.click('[data-editstory]'); await sleep(700);
    out.labels = await p.evaluate(() => [...document.querySelectorAll('#sheet .log-form label > span, #sheet .log-form .upd-step, #sheet .log-form .log-form-h b')].map(e => e.textContent.trim()).join('|'));
    out.fields = await p.evaluate(() => [...document.querySelectorAll('#sheet .log-form [data-ef]')].map(e => e.dataset.ef + '=' + (e.value || '').slice(0, 30)).join('|'));
    await p.fill('#sheet .log-form [data-ef="hl"]', 'Parity edited headline');
    const topic = p.locator('#sheet .log-form select[data-ef="topic"]'); if (await topic.count()) await topic.selectOption({ index: 2 });
    await p.selectOption('#sheet .log-form [data-ef="tone"]', 'Positive'); await p.fill('#sheet .log-form [data-ef="note"]', 'Parity edit note');
    await p.click('[data-logsave]'); await sleep(2500);
    out.toast = await p.evaluate(() => (document.querySelector('#toast,.toast') || {}).textContent || '');
    out.afterSave = await sheetFull(p); out.row = await snapClips(p);
    await p.keyboard.press('Escape'); await sleep(900);
    out.rowText = await p.evaluate(() => (document.querySelector('#tbody tr[data-id]:nth-child(2)') || {}).innerText || '');
    out.db1 = await dump(p, ['edits', 'notes']);
    // Manage > Update log shows the pending edit
    await p.click('#updBtn'); await sleep(900); await p.click('[data-mg="log"]'); await sleep(900);
    out.log = await p.evaluate(() => { const t = document.querySelector('#upd').innerText; return { len: t.length, hash: (() => { let h = 0; for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) | 0; return h; })(), pend: ((t.match(/\d+ edited stor\w+ not yet/) || [''])[0]), push: !!document.querySelector('[data-logpush]') }; });
    await p.click('[data-uclose]').catch(() => { }); await sleep(600);
    // remove a different story
    await openStory(p, 3); const before = (await snapClips(p)).pager;
    await p.click('[data-editstory]'); await sleep(600); await p.click('[data-logremove]'); await sleep(2500);
    out.removed = await snapClips(p); out.pagerBefore = before;
    out.db2 = await dump(p, ['edits', 'clips']);
    // reload keeps the edits (storage swap): same page again
    await p.reload({ waitUntil: 'load' }); await p.waitForSelector('nav.tabs button[data-tab]'); await sleep(4000); await p.click('nav.tabs button[data-tab=db]'); await sleep(1500);
    out.reloaded = await snapClips(p); out.rowText2 = await p.evaluate(() => (document.querySelector('#tbody tr[data-id]:nth-child(2)') || {}).innerText || '');
    out.db3 = await dump(p, ['edits']); return out; };

  T.notes_views_storage = async (p, base, out) => {
    await openStory(p, 2); await p.fill('#tnote', 'Storage parity note'); await sleep(2500); await p.keyboard.press('Escape'); await sleep(700);
    await p.fill('#q', 'housing'); await sleep(1200); await p.click('[data-vnew]'); await sleep(500); await p.fill('#vname', 'Storage view'); await p.click('#vform button[type=submit]'); await sleep(1800);
    out.db = await dump(p, ['notes', 'views']);
    out.db.views = out.db.views.map(([id, v], i) => ['view' + i, v]);   // view ids are random
    await p.reload({ waitUntil: 'load' }); await p.waitForSelector('nav.tabs button[data-tab]'); await sleep(4000); await p.click('nav.tabs button[data-tab=db]'); await sleep(1500);
    out.viewsAfter = await p.evaluate(() => [...document.querySelectorAll('#views button')].map(b => b.textContent.trim()).join('|'));
    out.noteBadges = await p.evaluate(() => document.querySelectorAll('#tbody tr .badge.flag').length);
    await openStory(p, 2); out.noteAfter = await p.evaluate(() => (document.querySelector('#tnote') || {}).value); return out; };

  T.manage_panel = async (p, base, out) => {
    await p.click('#updBtn'); await sleep(1200); out.opened = await p.evaluate(() => !document.querySelector('#upd').hidden);
    for (const k of ['upd', 'log', 'saved', 'quality', 'defs']) { if (!(await p.evaluate(k => { const b = document.querySelector(`[data-mg="${k}"]`); return !!b && b.offsetParent !== null; }, k))) { out[k] = 'hidden'; continue; } await p.click(`[data-mg="${k}"]`); await sleep(1200);
      out[k] = await p.evaluate(() => { const b = document.querySelector('#upd'); const t = b.innerText; let h = 0; for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) | 0;
        return { len: t.length, hash: h, txt: t.slice(0, 1200), details: b.querySelectorAll('details').length, links: b.querySelectorAll('a[href]').length, rows: b.querySelectorAll('tr,li').length }; }); }
    out.badge = await p.evaluate(() => (document.querySelector('#mgBadge') || {}).textContent || '');
    await p.keyboard.press('Escape'); await sleep(500); return out; };

  T.every_tab = async (p, base, out) => {
    out.tabs = await p.evaluate(() => [...document.querySelectorAll('nav.tabs button[data-tab]')].filter(b => !b.hidden).map(b => b.id + ':' + b.textContent.trim()));
    out.masthead = await p.evaluate(() => (document.querySelector('header') || document.body).innerText.replace(/\s+/g, ' ').replace(/Update database |Refresh from files |Tracker files |Last updated [A-Z][a-z]+ \d+, \d{4} ?/g, '').slice(0, 400));   // recorded exceptions: hidden Update and Refresh buttons, the Tracker files button, LASTUPDATED-v1
    out.home = await tabText(p);
    out.homeFacts = await p.evaluate(() => [...document.querySelectorAll('#view-ov .tile, #view-ov .card, #view-ov .stat')].slice(0, 40).map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 80)).join('|'));
    for (const t of await p.evaluate(() => [...document.querySelectorAll('nav.tabs button[data-tab]')].filter(b => !b.hidden).map(b => b.id))) {
      await p.click('#' + t.replace(/\$/g, '\\$')); await sleep(2000);
      out[t] = { text: await tabText(p), svg: await p.evaluate(() => document.querySelectorAll('main > section:not([hidden]) svg').length), rows: await p.evaluate(() => document.querySelectorAll('main > section:not([hidden]) tr').length),
        links: await p.evaluate(() => document.querySelectorAll('main > section:not([hidden]) a[href]').length) }; }
    out.counts = await p.evaluate(() => ({ data: JSON.parse(document.getElementById('data').textContent).length })); return out; };

  T.links_photos = async (p, base, out) => {
    // the first rows of Clips: every outbound link, and per saved copy the photo links in the frame
    await p.click('nav.tabs button[data-tab=db]'); await sleep(1200); await p.fill('#q', ''); await sleep(900);
    out.rowLinks = await p.evaluate(() => [...document.querySelectorAll('#tbody tr[data-id]')].slice(0, 25).map(r => r.dataset.id + ':' + [...r.querySelectorAll('a[href]')].map(a => a.getAttribute('href')).join(',')).join('|'));
    const ids = await p.evaluate(() => { const d = JSON.parse(document.getElementById('data').textContent); const pick = f => d.filter(f).slice(0, 2).map(r => r.id);
      return [].concat(pick(r => r.date >= '2026-10-01'), pick(r => r.date >= '2025-01-01' && r.date < '2025-03-01'), pick(r => r.date < '2016-01-01' && r.date > '2015-01-01'), pick(r => r.media === 'TV'), pick(r => r.lang && r.lang !== 'English')); });
    out.ids = ids;
    for (const id of ids) { await openById(p, id);
      out[id] = Object.assign(await sheetFull(p), await p.evaluate(async () => { const f = document.querySelector('#doc iframe'); if (!f) return { frame: false };
        const d = f.contentDocument; await Promise.all([...d.images].filter(i => !i.complete).map(i => new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 4000); })));
        const src = i => { const s = i.getAttribute('src') || ''; return s.startsWith('data:') ? 'data:' + s.length : s.replace(/^https?:\/\/127\.0\.0\.1:\d+/, ''); };
        return { frame: true, imgs: [...d.images].slice(0, 12).map(i => src(i) + '@' + i.naturalWidth).join('|'), n: d.images.length, anchors: [...d.querySelectorAll('a[href]')].slice(0, 30).map(a => a.getAttribute('href')).join('|'), text: (() => { let h = 0; const t = d.body.innerText; for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) | 0; return h; })() }; }));
      await p.keyboard.press('Escape'); await sleep(500); }
    return out; };

  T.reprint_groups = async (p, base, out) => {
    const ids = await p.evaluate(() => { const d = JSON.parse(document.getElementById('data').textContent); const g = d.filter(r => r.reps && r.reps.length).slice(0, 4).map(r => r.id); const a = d.filter(r => r.also).slice(0, 2).map(r => r.id);
      return { ids: g.concat(a), groups: d.filter(r => r.reps && r.reps.length).length, reprintRows: d.reduce((n, r) => n + (r.rep ? 1 : 0), 0), alsoRows: d.filter(r => r.also).length, listed: d.filter(r => r.lstat === 'List only').length }; });
    out.stats = ids;
    for (const id of ids.ids) { await openById(p, id); out[id] = await sheetFull(p); out[id + '_text'] = await p.evaluate(() => { const t = document.querySelector('#sheet').innerText; return t.slice(0, 1500); }); await p.keyboard.press('Escape'); await sleep(400); }
    await p.click('nav.tabs button[data-tab=db]'); await sleep(1000); await p.fill('#q', ''); await openRailSafe(p);
    out.facet = await p.evaluate(() => [...document.querySelectorAll('#view-db input[data-f]')].filter(i => /reprint|repeat|also/i.test(i.dataset.f + ' ' + (i.closest('label') || {}).innerText)).map(i => i.dataset.f + ':' + i.value + ':' + (i.closest('label') || {}).innerText.replace(/\s+/g, ' ')).slice(0, 10));
    return out; };
  async function openRailSafe(p) { const open = await p.evaluate(() => document.querySelector('#view-db #rail').getBoundingClientRect().right > 20); if (!open) { await p.click('#openRail'); await sleep(500); } }

  T.exports_more = async (p, base, out) => {   // the whole-file download (workbook), per-tab exports at default state, and a filtered export
    await p.click('nav.tabs button[data-tab=db]'); await sleep(1200);
    await p.selectOption('#when', 'p30').catch(() => { }); await sleep(900);
    await exportMenu(p); out.csv30 = await download(p, () => p.click('[data-dl="csv"]'));
    await exportMenu(p); out.sheet30 = await download(p, () => p.click('[data-dl="sheet"]')); return out; };
};
