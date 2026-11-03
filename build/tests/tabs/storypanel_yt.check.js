// YTBROADCAST-v1 check: the story panel lists the AV tab's YouTube link as "YouTube (station clip)" (09246 FOX 11, 10315 ABC7 SF),
// and a broadcast story with a saved copy labels the copy as the station's web story. Standalone (not a tab module):
//   NODE_PATH=/opt/npm-tools/node_modules node build/tests/tabs/storypanel_yt.check.js   (needs work/build_last/lib from build/build.sh)
// Screenshots go to work/yt_ui/ (SHOTS=0 to skip).
const { chromium } = require('playwright'); const http = require('http'); const fs = require('fs'); const path = require('path');
const L = path.resolve(__dirname, '../../..'), ROOT = path.join(L, 'work', 'build_last', 'lib'), OUT = path.join(L, 'work', 'yt_ui');
const SIDS = {}, DATA = JSON.parse(fs.readFileSync(path.join(ROOT, 'blocks', 'data.json'), 'utf8'));
for (const r of DATA) if (r.aid === '09246' || r.aid === '10315') SIDS[r.aid] = r.id;
// a stub saved copy for the two rows (the real library is not served here): manifest + one shard
const srv = http.createServer((q, s) => { const u0 = q.url.split('?')[0];
  if (u0 === '/articles/manifest.json'){ s.writeHead(200, { 'content-type': 'application/json' }); return s.end(JSON.stringify({ articles: Object.fromEntries(Object.values(SIDS).map(id => [id, 'articles/stub.json'])) })); }
  if (u0 === '/articles/stub.json'){ s.writeHead(200, { 'content-type': 'application/json' }); return s.end(JSON.stringify(Object.fromEntries(Object.values(SIDS).map(id => [id, '<html><body><h1>Saved station web story</h1><p>Assemblymember Jesse Gabriel spoke on the segment.</p></body></html>'])))); }
  const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]) === '/' ? 'index.html' : decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, b) => { if (e){ s.writeHead(404); s.end(); return; } s.writeHead(200, { 'content-type': f.endsWith('.html') ? 'text/html' : 'application/json' }); s.end(b); }); });
let pass = 0, fail = 0; const ok = (n, c, i) => { c ? pass++ : fail++; console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -- ' + i)); };
const CASES = [['09246', 'https://www.youtube.com/watch?v=P6zsjIepWaQ', 'FOX 11'], ['10315', 'https://www.youtube.com/watch?v=H4nhBSNZkxs', 'ABC7']];
(async () => {
  await new Promise(r => srv.listen(0, r)); const port = srv.address().port; const browser = await chromium.launch();
  for (const vp of [{ width: 1400, height: 1000 }, { width: 390, height: 844 }]) {
    const pg = await (await browser.newContext({ viewport: vp })).newPage(); const errs = [];
    pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error' && !/404|Failed to load/.test(m.text())) errs.push(m.text()); });
    await pg.addInitScript(() => { const col = () => ({ onSnapshot(cb){ setTimeout(() => cb({ docs: [] }), 30); return () => {}; }, doc(){ return { set: async () => {}, delete: async () => {} }; } });
      window.claude = { use: async n => { if (n === 'db') return { collection: col }; throw new Error('no'); } }; });
    await pg.goto(`http://localhost:${port}/`); await pg.waitForSelector('#tab-db', { timeout: 30000 }); await pg.waitForTimeout(1500);
    await pg.click('#tab-db'); await pg.waitForTimeout(400);
    for (const [aid, url, name] of CASES) {
      const tag = `[${vp.width}] ${aid} ${name}: `, sid = SIDS[aid];
      ok(tag + 'row exists', !!sid, sid);
      await pg.evaluate(() => { const c = document.querySelector('#sheet [data-close]'); if (c && !document.querySelector('#sheet').hidden) c.click(); });
      await pg.fill('#q', aid === '09246' ? 'Special Report' : 'ABC7'); await pg.waitForTimeout(700);
      const row = await pg.$(`#tbody tr[data-id="${sid}"]`); ok(tag + 'row listed in Clips', !!row, 'not listed'); if (!row) continue;
      await (await row.$('td.h .hl')).click(); await pg.waitForSelector('#sheet:not([hidden]) .sheet-meta h2', { timeout: 10000 }); await pg.waitForTimeout(500);
      const links = await pg.evaluate(() => [...document.querySelectorAll('#sheet .sheet-meta .dlinks a[data-lk]')].map(a => ({ k: a.dataset.lk, href: a.href, label: a.querySelector('b').textContent.trim(), sub: a.querySelector('span').textContent.trim() })));
      const yt = links.filter(x => x.k === 'yt');
      ok(tag + 'one YouTube link, label "YouTube (station clip) ↗", href = AV tab link', yt.length === 1 && yt[0].label === 'YouTube (station clip) ↗' && yt[0].href === url, JSON.stringify(links));
      ok(tag + 'drawn like the archive.org link (label, host line, copy button)', yt.length === 1 && yt[0].sub === 'youtube.com' && await pg.evaluate(u => !!document.querySelector(`#sheet .dlinks .lkw .cpb[data-cp="${u}"]`), url), JSON.stringify(yt));
      ok(tag + 'no "Publisher site" link pointing at YouTube', !links.some(x => x.k === 'pub' && /youtube\.com/.test(x.href)), JSON.stringify(links));
      const info = await pg.evaluate(() => ({ badges: [...document.querySelectorAll('#sheet .sh-badges .badge')].map(b => b.textContent.trim()), avType: (document.querySelector('#sheet .tb-av h4 .note') || {}).textContent }));
      ok(tag + 'Format badge and AV Item type read Broadcast segment', info.badges.includes('Broadcast segment') && info.avType === 'Broadcast segment', JSON.stringify(info));
      ok(tag + 'saved-copy badge reads "Saved copy (station’s web story)"', info.badges.includes('Saved copy (station’s web story)') && !info.badges.includes('Saved copy'), JSON.stringify(info.badges));
      if (process.env.SHOTS !== '0') await (await pg.$('#sheet')).screenshot({ path: path.join(OUT, `story_${aid}_${vp.width}.png`) });
    }
    // an ordinary article keeps the plain label: find one with a saved copy in the manifest-less page is not possible, so check the source rule instead
    ok(`[${vp.width}] source: plain "Saved copy" label kept for other formats`, /fmtOf\(r\) === 'Broadcast segment' \? 'Saved copy \(station’s web story\)' : 'Saved copy'/.test(fs.readFileSync(path.join(L, 'code', 'tracker', '02_state.js'), 'utf8')), 'rule not found');
    ok(`[${vp.width}] no page errors`, errs.length === 0, errs.slice(0, 3).join(' | '));
  }
  await browser.close(); srv.close(); console.log(`\n${pass}/${pass + fail} passed`); process.exit(fail ? 1 : 0);
})();
