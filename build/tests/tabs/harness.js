// TABS-v1 harness (agent-tabs). Run one tab alone:
//   cd build/tests/tabs && NODE_PATH=/opt/npm-tools/node_modules MOD=<id> node harness.js
// MOD = a tab id (reporters|outlets|releases|bills|travel|...), _framework (menu, redirects, search-tab and entity-page
// components through the stub module), or all (_framework + every <id>.test.js here).
// Serves srv/ (build_testpage.sh; SRV=dir to override), stubs window.claude (db, downloads), loads the page. When the page
// does not already carry the module (<script id="tab-js-<id>">) it injects blocks/tab_<id>.json and build/tabs/<id>.js (the
// harness runs `tabs_data.py --only <id>` first when build/tabs/<id>_data.py exists). Then it runs ./<id>.test.js(page, ok, h) at
// 1400x1000 and 390x844 and prints PASS/FAIL lines; exit 1 on any FAIL.
const { chromium } = require('playwright'); const http = require('http'); const fs = require('fs'); const path = require('path'); const cp = require('child_process');
const L = path.resolve(__dirname, '../../..'), ROOT = path.resolve(__dirname, process.env.SRV || 'srv'), PORT0 = +(process.env.PORT || 0); let PORT;
const SLUG = { reporters: 'reporters', outlets: 'outlets', releases: 'press-releases', bills: 'bills', travel: 'story-travel', stub: 'stub' };
const MOD = process.env.MOD || '_framework';
const mods = MOD === 'all' ? ['_framework'].concat(fs.readdirSync(__dirname).filter(f => f.endsWith('.test.js') && !f.startsWith('_')).map(f => f.slice(0, -8)).sort()) : [MOD];
const VPS = process.env.VP === 'desk' ? [{ width: 1400, height: 1000 }] : process.env.VP === 'phone' ? [{ width: 390, height: 844 }] : [{ width: 1400, height: 1000 }, { width: 390, height: 844 }];
const srv = http.createServer((q, s) => { const u = decodeURIComponent(q.url.split('?')[0]); const f = path.join(ROOT, u === '/' ? 'index.html' : u);
  fs.readFile(f, (e, b) => { if (e){ s.writeHead(404); s.end(); return; } s.writeHead(200, { 'content-type': f.endsWith('.html') ? 'text/html' : 'application/json' }); s.end(b); }); });
// REPO-LOCAL (fixed clock): the tabs' date presets (3 / 12 months, "Active within" ...) count back from the page's own today (code/tracker/00_head.js TODAY,
// which reads new Date() in America/Los_Angeles) and the tests' independent models count back from h.TODAY(). Both used the real clock, so the counts moved with
// the calendar (and with UTC vs Los Angeles near midnight). Every page now runs with the clock fixed at the day the fixture blocks were taken from (the
// 2026-10-30 workbook snapshot, 20:00 UTC = 13:00 in Los Angeles: same date in both zones). TABS_NOW=real uses the real clock; TABS_NOW=<ISO instant> another instant.
const NOW = process.env.TABS_NOW === 'real' ? null : (process.env.TABS_NOW || '2026-10-30T20:00:00Z');
const results = []; let cur = '';
const PAGE = () => MOD === '_framework' || process.env.PAGE === 'stub' ? 'stub.html' : '';
const skip = (name, why) => { results.push(['SKIP', cur + name, why]); console.log('SKIP ' + cur + name + '  -- ' + why); };
const ok = (name, cond, info) => { results.push([cond ? 'PASS' : 'FAIL', cur + name, info || '']); console.log((cond ? 'PASS ' : 'FAIL ') + cur + name + (info && !cond ? '  -- ' + String(info).slice(0, 300) : '')); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await new Promise(r => srv.listen(PORT0, r)); PORT = srv.address().port;
  const browser = await chromium.launch();
  for (const mod of mods) {
    const isFw = mod === '_framework', id = isFw ? 'stub' : mod, slug = SLUG[id] || id;
    const dataPy = path.join(L, 'build', 'tabs', id + '_data.py'), blk = path.join(__dirname, 'blocks', `tab_${id}.json`);
    if (!isFw && fs.existsSync(dataPy) && !process.env.NO_DATA) {
      fs.mkdirSync(path.join(__dirname, 'blocks'), { recursive: true });
      const tmp = path.join(L, 'work', 'tests_out', 'tabs', 'hblocks_' + id); fs.mkdirSync(tmp, { recursive: true });
      fs.copyFileSync(path.join(ROOT, 'blocks', 'data.json'), path.join(tmp, 'data.json'));
      cp.execFileSync('python3', ['-I', path.join(L, 'code', 'tabs_data.py'), process.env.XLSX || path.join(L, 'work', 'coverage_current.xlsx'), tmp, path.join(L, 'build', 'tabs'), '--only', id], { stdio: 'inherit',
        env: Object.assign({}, process.env, { RELRELATED_JSON: process.env.RELRELATED_JSON || path.join(L, 'code', 'release_related.json') }) });   // v20-final: releases block keeps its related rows
      if (fs.existsSync(path.join(tmp, `tab_${id}.json`))) fs.copyFileSync(path.join(tmp, `tab_${id}.json`), blk);
    }
    for (const vp of VPS) {
      cur = `[${mod} ${vp.width}] `;
      const bctx = await browser.newContext({ viewport: vp, permissions: ['clipboard-read', 'clipboard-write'] }); if (NOW) await bctx.clock.setFixedTime(new Date(NOW)); const pg = await bctx.newPage();
      const errors = []; pg.on('pageerror', e => errors.push(String(e))); pg.on('console', m => { if (m.type() === 'error' && !/404|Failed to load/.test(m.text())) errors.push(m.text()); });
      await pg.addInitScript(([fw]) => {
        window.__dl = []; window.__clip = null; if (fw) window.__STUB_IDS = fw;
        window.__nav = []; const lg = () => window.__nav.push(location.hash); addEventListener('hashchange', lg);   // every hash the page shows (to prove a tab never jumps to #clips)
        for (const k of ['replaceState', 'pushState']){ const f = history[k].bind(history); history[k] = (a, b, u) => { const r = f(a, b, u); lg(); return r; }; }
        const col = () => ({ onSnapshot(cb){ setTimeout(() => cb({ docs: [] }), 30); return () => {}; }, doc(){ return { set: async () => {}, delete: async () => {} }; } });
        const blobText = async d => typeof d === 'string' ? d : (d && d.text ? await d.text() : String(d));
        window.claude = { use: async n => { if (n === 'db') return { collection: col }; if (n === 'downloads') return { save: async ({ filename, data }) => { window.__dl.push({ filename, text: await blobText(data) }); } }; throw new Error('no ' + n); } };
        try { const w = navigator.clipboard.writeText.bind(navigator.clipboard); navigator.clipboard.writeText = t => { window.__clip = t; return w(t).catch(() => {}); }; } catch(e){}
      }, [isFw ? (process.env.STUB_IDS || 'reporters,outlets,releases,bills,travel,stub').split(',') : null]);
      await pg.goto(`http://localhost:${PORT}/` + (isFw ? 'stub.html' : '') + (process.env.START_HASH || '')); await pg.waitForFunction(() => !!window.AJGTabs, null, { timeout: 30000 });
      const has = await pg.evaluate(m => !!document.getElementById('tab-js-' + m), id);
      if (!has) {
        if (fs.existsSync(blk)) await pg.evaluate(([m, t]) => { const s = document.createElement('script'); s.id = 'tab-' + m; s.type = 'application/json'; s.textContent = t; document.body.appendChild(s); }, [id, fs.readFileSync(blk, 'utf8')]);
        await pg.addScriptTag({ path: isFw ? path.join(__dirname, 'stub.js') : path.join(L, 'build', 'tabs', id + '.js') });
      }
      const V = () => `#tbBody .tb-view[data-tb="${id}"]:not([hidden])`;
      const h = {
        skip, page: pg, errors, viewport: vp,
        /* v18Full: the v18 baseline page (page shell with its own data) is there; the repository has only the stripped shell.html */
        v18Full: fs.existsSync(path.join(L, 'build', 'shell', 'index.html')), phone: vp.width <= 640, id, slug, sleep,
        blocksDir: path.join(ROOT, 'blocks'),
        // INCL-v1 (final-codedesign 2026-10-29): the page's ctx.D = dCount() leaves List-only stories out unless "Include list-only
        // mentions" is on, so the tests' independent models see the same set; dataAll() = every record (the Clips list, badges)
        data: () => JSON.parse(fs.readFileSync(path.join(ROOT, 'blocks', 'data.json'), 'utf8')).filter(r => r && r.depth !== 'List-only'),
        dataAll: () => JSON.parse(fs.readFileSync(path.join(ROOT, 'blocks', 'data.json'), 'utf8')),
        block: name => JSON.parse(fs.readFileSync(path.join(ROOT, 'blocks', name + '.json'), 'utf8')),   // e.g. 'tab_common', 'ins_release_pickup', 'rows'
        tabBlock: () => fs.existsSync(blk) ? JSON.parse(fs.readFileSync(blk, 'utf8')) : null,
        /* navigate: open(params, sub, tab) -> '#<slug>[/<sub>]?<params>' through the hash router */
        async open(params, sub, tab){ const s = tab ? (SLUG[tab] || tab) : slug, q = params && Object.keys(params).length ? '?' + new URLSearchParams(params).toString() : '';
          await pg.evaluate(() => { const b = document.querySelector('#sheet [data-close]'); if (b && !document.querySelector('#sheet').hidden) b.click(); });
          await pg.evaluate(() => { location.hash = '#x-reset'; }); await sleep(30);
          await pg.evaluate(hh => { location.hash = hh; }, '#' + s + (sub ? '/' + encodeURIComponent(sub) : '') + q); await sleep(450); },
        async hashGo(hash){ await pg.evaluate(() => { location.hash = '#x-reset'; }); await sleep(30); await pg.evaluate(hh => { location.hash = hh; }, hash); await sleep(450); },
        async reload(hash){ await pg.goto(`http://localhost:${PORT}/` + (isFw ? 'stub.html' : '') + (hash || '')); await pg.reload(); await pg.waitForFunction(() => !!window.AJGTabs, null, { timeout: 30000 });
          const has2 = await pg.evaluate(m => !!document.getElementById('tab-js-' + m), id);
          if (!has2){ if (fs.existsSync(blk)) await pg.evaluate(([m, t]) => { const s = document.createElement('script'); s.id = 'tab-' + m; s.type = 'application/json'; s.textContent = t; document.body.appendChild(s); }, [id, fs.readFileSync(blk, 'utf8')]);
            await pg.addScriptTag({ path: isFw ? path.join(__dirname, 'stub.js') : path.join(L, 'build', 'tabs', id + '.js') }); }
          await sleep(500); },
        view: () => pg.$(V()),
        hash: () => pg.evaluate(() => decodeURIComponent(location.hash)),
        params: () => pg.evaluate(() => { const h = location.hash, i = h.indexOf('?'), o = {}; if (i >= 0) new URLSearchParams(h.slice(i + 1)).forEach((v, k) => o[k] = v); return o; }),
        /* search tab */
        count: () => pg.evaluate(v => { const b = document.querySelector(v + ' .tt-chips .result-line b'); return b ? +b.textContent.replace(/,/g, '') : null; }, V()),
        total: () => pg.evaluate(v => { const t = document.querySelector(v + ' .tt-chips .result-line'); const m = t && /of ([\d,]+)/.exec(t.textContent); return m ? +m[1].replace(/,/g, '') : null; }, V()),
        rowKeys: () => pg.evaluate(v => [...document.querySelectorAll(v + ' [data-ttk]')].map(x => x.dataset.ttk), V()),
        async search(text){ await pg.fill(V() + ' .tt-q', text); await sleep(350); },
        /* the filter rail is a drawer (as in Clips): opened from the Filters button when it is off screen */
        async openRail(){ const off = await pg.evaluate(v => { const r = document.querySelector(v + ' .tt-rail'); return !r.classList.contains('open') && r.getBoundingClientRect().right <= 0; }, V()); if (off){ await pg.click(V() + ' .tt-ft'); await sleep(300); } },
        async closeRail(){ const d = await pg.$(V() + ' .tt-rail.open [data-tt="done"]'); if (d){ await d.click(); await sleep(250); } },
        async facet(key, value){ await h.openRail();
          await pg.evaluate(([v, k]) => { const d = document.querySelector(`${v} details[data-ttfacet="${k}"]`); if (d && !d.open) d.open = true; }, [V(), key]); await sleep(60);
          const sel = `${V()} input[data-ttf="${key}"][value="${String(value).replace(/"/g, '\\"')}"]`;
          if (!(await pg.$(sel))){ const fs_ = await pg.$(`${V()} input[data-ttq="${key}"]`); if (fs_){ await fs_.fill(String(value)); await sleep(150); } else { const m = await pg.$(`${V()} [data-ttmore="${key}"]`); if (m){ await m.click(); await sleep(150); } } }
          await pg.click(sel); await sleep(300); await h.closeRail(); },
        facetCount: async (key, value) => { await pg.evaluate(([v, k]) => { const d = document.querySelector(`${v} details[data-ttfacet="${k}"]`); if (d && !d.open) d.open = true; }, [V(), key]); await sleep(120); return pg.evaluate(([v, k, val]) => { const i = [...document.querySelectorAll(`${v} input[data-ttf="${k}"]`)].find(x => x.value === val); if (!i) return null; const n = i.closest('label').querySelector('.n'); return n ? +n.textContent.replace(/,/g, '') : null; }, [V(), key, String(value)]); },
        async customDate(key, from, to){ await h.openRail(); await pg.evaluate(([v, k]) => { const d = document.querySelector(`${v} details[data-ttfacet="${k}"]`); if (d) d.open = true; }, [V(), key]);
          await pg.fill(`${V()} [data-ttc0="${key}"]`, from || ''); await pg.fill(`${V()} [data-ttc1="${key}"]`, to || ''); await pg.click(`${V()} [data-tt="cust"][data-k="${key}"]`); await sleep(300); await h.closeRail(); },
        chips: () => pg.evaluate(v => [...document.querySelectorAll(v + ' .tt-chips .chip')].map(c => c.textContent.trim()), V()),
        async removeChip(i){ const b = await pg.$$(V() + ' .tt-chips .chip button'); await b[i].click(); await sleep(300); },
        async clearAll(){ await pg.click(V() + ' .tt-chips [data-tt="clear"]'); await sleep(300); },
        async sort(key){ if (h.phone){ await pg.selectOption(V() + ' .tt-sort', key); } else await pg.click(`${V()} th button[data-ttsort="${key}"]`); await sleep(300); },
        async exportCsv(){ await pg.click(V() + ' .tt-exp summary'); await pg.click(V() + ' [data-tt="csv"]'); await sleep(400); const d = await pg.evaluate(() => window.__dl); return d[d.length - 1]; },
        async exportCopy(i){ await pg.click(V() + ' .tt-exp summary'); await pg.click(V() + (i == null ? ' [data-tt="copy"]' : ` [data-tt="copyx"][data-i="${i}"]`)); await sleep(300); return pg.evaluate(() => window.__clip); },
        async more(){ await pg.click(V() + ' [data-tt="more"]'); await sleep(250); },
        async openRow(key){ await pg.click(`${V()} [data-ttk="${key}"] ${await pg.$(`${V()} [data-ttk="${key}"] .tt-open`) ? '.tt-open' : ''}`.trim()); await sleep(450); },
        /* entity page */
        pageCount: () => pg.evaluate(v => { const b = document.querySelector(v + ' .tbe-chips .result-line b'); return b ? +b.textContent.replace(/,/g, '') : null; }, V()),
        pageTotal: () => pg.evaluate(v => { const t = document.querySelector(v + ' .tbe-chips .result-line'); const m = t && /of ([\d,]+)/.exec(t.textContent); return m ? +m[1].replace(/,/g, '') : null; }, V()),
        pageFacts: () => pg.evaluate(v => Object.fromEntries([...document.querySelectorAll(v + ' .tbe-facts > div')].map(d => [d.querySelector('dt').textContent.trim(), d.querySelector('dd').textContent.trim()])), V()),
        pageTitle: () => pg.evaluate(v => { const t = document.querySelector(v + ' .tbe-head h2'); return t ? t.textContent.trim() : null; }, V()),
        async pageSearch(text){ await pg.fill(V() + ' .tbe-q', text); await sleep(350); },
        pageRowIds: () => pg.evaluate(v => [...document.querySelectorAll(v + ' .tbe-body tr[data-id]')].map(x => x.dataset.id), V()),
        async back(){ await pg.click(V() + ' [data-tbe="back"]'); await sleep(450); },
        /* call markNav() before a sequence of actions, then leftTab() -> the first hash outside this tab (e.g. '#clips') or '' */
        markNav: () => pg.evaluate(() => { window.__nav = []; }),
        leftTab: () => pg.evaluate(sl => (window.__nav || []).find(x => x && !x.startsWith('#' + sl) && x !== '#x-reset') || '', slug),
        /* chart helpers: top y-axis label of a chart host, its largest bar total (from the numbers table), empty state */
        chartTop: sel => pg.evaluate(s => { const t = [...document.querySelectorAll(s + ' svg g.grid text')].map(x => +x.textContent.replace(/[,%]/g, '')).filter(x => !isNaN(x)); return t.length ? Math.max(...t) : null; }, sel),
        chartEmpty: sel => pg.evaluate(s => !!document.querySelector(s + ' .empty'), sel),
        downloads: () => pg.evaluate(() => window.__dl), clipboard: () => pg.evaluate(() => window.__clip),
        overflowX: () => pg.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1),
        fold: s => String(s == null ? '' : s).normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/\s+/g, ' ').trim(),
        TODAY: () => pg.evaluate(() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }),
        async shot(name){ const dir = path.join(L, 'work', 'tests_out', 'tabs', 'shots', process.env.SHOTS || mod); /* per module (Phase B) */ fs.mkdirSync(dir, { recursive: true }); const f = path.join(dir, `${name}_${vp.width}.png`); await pg.screenshot({ path: f, fullPage: false }); return f; }
      };
      try {
        await h.open();
        await require(path.join(__dirname, mod + '.test.js'))(pg, ok, h);
      } catch (e) { ok('test threw', false, String(e && e.stack || e).slice(0, 1500)); }
      ok('no page errors', errors.length === 0, errors.slice(0, 3).join(' | '));
      await bctx.close();
    }
  }
  await browser.close(); srv.close();
  const f = results.filter(r => r[0] === 'FAIL').length, sk = results.filter(r => r[0] === 'SKIP').length; console.log(`\n${results.length - f - sk}/${results.length - sk} passed` + (sk ? `, ${sk} skipped` : '')); process.exit(f ? 1 : 0);
})();
