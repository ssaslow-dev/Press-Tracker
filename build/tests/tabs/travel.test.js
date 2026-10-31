// Story travel tab test (agent-tab-travel, TABS-v1). Every count is recomputed here from srv/blocks/*.json (data, tab_common,
// ins_story_travel) and the harness-built tab_travel block, never read back from the page.
const fs = require('fs'), path = require('path');
module.exports = async (pg, ok, h) => {
  const W = h.viewport.width, SHOTS = path.resolve(__dirname, '../../../work/tests_out/tabs/shots/travel'); fs.mkdirSync(SHOTS, { recursive: true });
  const shot = async (name, full) => { for (const cs of ['light', 'dark']){ await pg.emulateMedia({ colorScheme: cs }); await h.sleep(150);
    await pg.screenshot({ path: path.join(SHOTS, `${name}_${cs}_${W}.png`), fullPage: !!full }); } await pg.emulateMedia({ colorScheme: 'light' }); };
  const D = h.data(), C = h.block('tab_common'), INS = h.block('ins_story_travel'), TB = h.tabBlock() || { v: [''], r: {} };
  const fold = h.fold, ISO = /^\d{4}-\d{2}-\d{2}$/;
  const canon = (n, aid) => (aid && C.a[String(aid)]) || C.n[String(n || '').trim()] || String(n || '').trim();
  const langOf = r => r.lang || 'English';
  const days = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 864e5);
  /* outlet language fallback: most common language of that outlet's originals */
  const ol = new Map(); D.forEach(r => { const o = canon(r.outlet, r.aid), m = ol.get(o) || ol.set(o, new Map()).get(o); m.set(langOf(r), (m.get(langOf(r)) || 0) + 1); });
  const top = m => m && m.size ? [...m].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0][0] : '';
  const repLang = p => { const t = TB.r[p.aid]; return (t && TB.v[t[1]]) || (t ? 'English' : (top(ol.get(canon(p.outlet, p.aid))) || 'English')); };
  function entry(r){
    const own = canon(r.outlet, r.aid), ownH = ((C.h || {})[own] || own), g = new Map(); let ownN = 0;   /* REPCOUNT-v1: own house */
    (r.reps || []).forEach(p => { if (!p.outlet) return; const n = canon(p.outlet, p.aid); if (n === own || ((C.h || {})[n] || n) === ownH){ ownN++; return; } (g.get(n) || g.set(n, []).get(n)).push(p); });
    const ps = [...g].map(([name, cs]) => { const ds = cs.map(c => ISO.test(c.date) ? c.date : '').filter(Boolean).sort(); const f = ds[0] || '';
      return { name, n: cs.length, date: f, d: f && ISO.test(r.date) ? days(r.date, f) : null, langs: cs.map(repLang), first: cs.slice().sort((a, b) => ((ISO.test(a.date) ? a.date : '9999').localeCompare(ISO.test(b.date) ? b.date : '9999')) || String(a.aid).localeCompare(String(b.aid)))[0] }; });
    ps.sort((a, b) => (a.d == null) - (b.d == null) || (a.d - b.d) || a.name.localeCompare(b.name));
    const dd = ps.filter(p => p.d != null).map(p => p.d);
    return { r, id: r.id, out: own, ps, n: ps.length, copies: ps.reduce((a, p) => a + p.n, 0), ownN, span: dd.length ? Math.max(0, ...dd) : null,
      lng: [...new Set([langOf(r)].concat(ps.map(p => repLang(p.first))))] };
  }
  const ALL = D.filter(r => String(r.hl || '').trim()).map(entry);
  const L = ALL.filter(e => e.n > 0 && !/^dup:/.test((INS.x || {})[e.id] || ''));
  const byId = new Map(ALL.map(e => [e.id, e]));
  const nb = (e, id) => id === '1' ? e.n === 1 : id === '2' ? e.n >= 2 && e.n <= 4 : id === '5' ? e.n >= 5 && e.n <= 9 : e.n >= 10;
  const slugOf = e => e.id + '-' + fold(e.r.hl).replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').split('-').slice(0, 6).join('-');
  const V = `#tbBody .tb-view[data-tb="travel"]:not([hidden])`;

  /* ---- list ---- */
  await h.open();
  ok('list renders: total = independent', (await h.total()) === L.length, `${await h.total()} vs ${L.length}`);
  ok('count = total with no filters', (await h.count()) === L.length);
  const k0 = await h.rowKeys(), want0 = L.slice().sort((a, b) => b.n - a.n)[0];
  ok('default sort: most outlets first', byId.get(k0[0]).n === want0.n, `${k0[0]} ${byId.get(k0[0]) && byId.get(k0[0]).n} vs ${want0.n}`);
  ok('row in Clips form with outlet count', await pg.evaluate(v => { const c = document.querySelector(v + ' tr[data-ttk] .clip'); return !!c && /\d+ outlets?/.test(c.textContent) && !c.hasAttribute('data-id'); }, V));
  ok('no horizontal overflow (list)', !(await h.overflowX()));
  await shot('list');

  // search: case + accent
  const qn = L.filter(e => fold([e.r.hl, e.r.hl_en, e.out, e.r.outlet, (e.r.authors || []).join(' ')].join(' ')).includes('glock')).length;
  await h.search('GLOCK'); ok('search (case-insensitive) = independent', (await h.count()) === qn && qn > 0, `${await h.count()} vs ${qn}`);
  await h.search('glöck'); ok('search (accent-insensitive) = independent', (await h.count()) === qn, `${await h.count()} vs ${qn}`);
  const au = L.find(e => (e.r.authors || []).length && e.n >= 3).r.authors[0];
  const an = L.filter(e => fold([e.r.hl, e.r.hl_en, e.out, e.r.outlet, (e.r.authors || []).join(' ')].join(' ')).includes(fold(au))).length;
  await h.search(au); ok('search by author = independent', (await h.count()) === an, `${au}: ${await h.count()} vs ${an}`);
  await h.search('');

  // each facet
  const cnt = m => { const c = new Map(); L.forEach(e => [].concat(m(e)).forEach(v => c.set(v, (c.get(v) || 0) + 1))); return [...c].sort((a, b) => b[1] - a[1])[0]; };
  const [o1, o1n] = cnt(e => e.out);
  ok('facet count shown: original outlet', (await h.facetCount('outlet', o1)) === o1n, `${o1}: ${await h.facetCount('outlet', o1)} vs ${o1n}`);
  await h.facet('outlet', o1); ok('facet original outlet = independent', (await h.count()) === o1n, `${await h.count()} vs ${o1n}`); await h.clearAll();
  const gn = L.filter(e => (String(e.r.topic || '').trim() || 'Unassigned') === 'Guns').length;
  await h.facet('iss', 'Guns'); ok('facet issue = independent', (await h.count()) === gn, `${await h.count()} vs ${gn}`); await h.clearAll();
  const n10 = L.filter(e => nb(e, '10')).length;
  await h.facet('n', '10'); ok('facet reprint count (10+) = independent', (await h.count()) === n10, `${await h.count()} vs ${n10}`); await h.clearAll();
  const [rc, rcn] = cnt(e => e.ps.map(p => p.name));
  await h.facet('reached', rc); ok('facet outlets it reached = independent', (await h.count()) === rcn, `${rc}: ${await h.count()} vs ${rcn}`); await h.clearAll();
  const spn = L.filter(e => e.lng.includes('Spanish')).length;
  await h.facet('lng', 'Spanish'); ok('facet language = independent', (await h.count()) === spn && spn > 0, `${await h.count()} vs ${spn}`); await h.clearAll();
  const dn = L.filter(e => e.r.date >= '2024-01-01' && e.r.date.slice(0, 10) <= '2024-12-31').length;
  await h.customDate('date', '2024-01-01', '2024-12-31'); ok('facet original date (custom range) = independent', (await h.count()) === dn, `${await h.count()} vs ${dn}`);
  // combined
  const cb = L.filter(e => e.r.date >= '2024-01-01' && e.r.date.slice(0, 10) <= '2024-12-31' && nb(e, '2')).length;
  ok('combined facet count shown = independent', (await h.facetCount('n', '2')) === cb, `${await h.facetCount('n', '2')} vs ${cb}`);
  await h.facet('n', '2'); ok('combined filters = independent', (await h.count()) === cb, `${await h.count()} vs ${cb}`);
  // URL round-trip
  const p1 = await h.params();
  ok('filters in URL', p1.n === '2' && /^c:2024-01-01\.\.2024-12-31$/.test(p1.date || ''), JSON.stringify(p1));
  await h.reload('#story-travel?' + new URLSearchParams(p1).toString());
  ok('URL round-trip restores the list', (await h.count()) === cb && (await h.chips()).length === 2, `${await h.count()} ${(await h.chips()).join(' | ')}`);
  // sort
  await h.sort('date'); const ks = await h.rowKeys(); const ds = ks.slice(0, 10).map(k => byId.get(k).r.date);
  ok('sort by original date (newest first)', ds.every((d, i) => !i || ds[i - 1] >= d), ds.join(','));
  // export
  const csv = await h.exportCsv(), lines = (csv && csv.text || '').replace(/^﻿/, '').split(/\r\n/).filter(Boolean);
  ok('CSV rows = count + header', lines.length === cb + 1 && /Story ID/.test(lines[0]) && /Outlets reached/.test(lines[0]), `${lines.length} vs ${cb + 1}`);
  const cp = await h.exportCopy(0); ok('copy pickup summary: one line per story', (cp || '').split('\n').length === cb, `${(cp || '').split('\n').length}`);
  const tsv = await h.exportCopy(); ok('copy list (TSV) = count + header', (tsv || '').split('\n').length === cb + 1);
  // chip removal
  await h.removeChip((await h.chips()).findIndex(c => /Reprint count/.test(c)));
  ok('removing a chip widens the list', (await h.count()) === dn, `${await h.count()} vs ${dn}`);
  await h.clearAll(); ok('clear all', (await h.count()) === L.length);

  /* ---- story page: the widest story + one with a real curve ---- */
  const big = byId.get('s00228');
  await h.markNav();
  await h.search('glock'); await h.openRow('s00228');
  ok('click opens the story page', (await h.hash()).startsWith('#story-travel/' + slugOf(big)), await h.hash());
  const f = await h.pageFacts();
  ok('page facts = independent', f['Outlets reached'] === String(big.n) && f['Copies'].startsWith(String(big.copies)) && f['Days to last pickup'] === String(big.span) && f['Original'] === big.out, JSON.stringify(f) + ` vs n=${big.n} copies=${big.copies} span=${big.span}`);
  const sub = await pg.evaluate(v => document.querySelector(v + ' .tbe-sub').textContent, V);
  ok('summary line', sub.startsWith(`Picked up by ${big.n} outlets in ${big.span} day`) && /furthest: /.test(sub), sub);
  ok('Where it ran sits above the Pickup ladder (bcb6ffb1)', await pg.evaluate(v => { const w = document.querySelector(v + ' .tv-where'), l = document.querySelector(v + ' .tv-ladder'); return !!w && !!l && !!(w.compareDocumentPosition(l) & Node.DOCUMENT_POSITION_FOLLOWING); }, V));
  const lad = await pg.evaluate(v => [...document.querySelectorAll(v + ' .tv-ladder [data-step]')].map(x => [+x.dataset.step, x.dataset.out]), V);
  ok('ladder: original + one row per outlet, in the order it ran', lad.length === big.n + 1 && lad[0][1] === big.out && lad.slice(1).every(([i, o], j) => i === j + 1 && o === big.ps[j].name), JSON.stringify(lad.slice(0, 4)));
  const hid = await pg.evaluate(v => document.querySelectorAll(v + ' .tv-ladder [data-step][hidden]').length, V);
  ok('ladder shows 20 then "Show all"', hid === big.n - 20, `${hid}`);
  await pg.click(V + ' [data-tv="all"]'); await h.sleep(150);
  ok('"Show all" reveals every outlet', (await pg.evaluate(v => document.querySelectorAll(v + ' .tv-ladder [data-step][hidden]').length, V)) === 0);
  const grouped = big.ps.find(p => p.n > 1);
  if (grouped) ok('same-outlet copies grouped', await pg.evaluate(([v, o, n]) => { const x = [...document.querySelectorAll(v + ' .tv-ladder [data-step]')].find(e => e.dataset.out === o); return !!x && x.textContent.includes(n + ' copies'); }, [V, grouped.name, grouped.n]), grouped.name);
  ok('every ladder link has its copy icon on the left', await pg.evaluate(v => [...document.querySelectorAll(v + ' .tv-ladder a[href]')].every(a => { const p = a.previousElementSibling; return p && p.classList.contains('cpb'); }), V));
  ok('outlet names link to outlet pages', await pg.evaluate(v => [...document.querySelectorAll(v + ' .tv-ladder [data-step] .ct [data-tb-go="outlets"]')].length, V) === big.n + 1);
  // US map rule (USMAP-v1 threshold, independent)
  const abbr = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split(' ');   // code/us_map.js
  const qual = e => [...new Set([e.out].concat(e.ps.map(p => p.name)))].filter(n => { const g = C.o[n]; if (!g) return false; const [st, rch, med] = g;
    return !(st === 'USA' || /(^|;\s*)(National|International|Trade, advocacy & blogs)(;|$)/.test(rch || '') || med === 'Wire') && abbr.includes(st); }).length;
  const show = await pg.evaluate(v => (document.querySelector(v + ' .tv-us') || {}).dataset.show, V);
  ok('US map shown when > 5 out-of-state sources qualify', (qual(big) > 5) === (show === '1') && show === '1', `${qual(big)} ${show}`);
  ok('no horizontal overflow (page)', !(await h.overflowX()));
  ok('bill numbers render as bill links (addendum)', await pg.evaluate(([v, bs]) => { const l = [...document.querySelectorAll(v + ' .tbe-facts [data-bill]')].map(x => x.dataset.bill); return JSON.stringify(l) === JSON.stringify(bs); }, [V, big.r.bills || []]));
  await pg.click(V + ' .tbe-facts [data-tbstory]'); await h.sleep(400);
  ok('"Open the story" opens the story panel', await pg.evaluate(() => !document.querySelector('#sheet').hidden));
  await pg.evaluate(() => { const b = document.querySelector('#sheet [data-close]'); if (b) b.click(); }); await h.sleep(200);
  ok('no Data chart and no one-row list on a story page (page spec chart:false / list:false)', await pg.evaluate(v => !document.querySelector(v + ' .tbe-chart') && document.querySelector(v + ' .tbe > .grid-clips').hidden, V));
  await shot('page');
  // ladder export
  await pg.click(V + ' .tv-ladder summary'); await pg.click(V + ' [data-tv="csv"]'); await h.sleep(300);
  const lc = (await h.downloads()).slice(-1)[0]; const ll = (lc && lc.text || '').replace(/^﻿/, '').split(/\r\n/).filter(Boolean);
  ok('ladder CSV = original + outlets + header', ll.length === big.n + 2, `${ll.length}`);
  ok('never left the tab (no #clips)', (await h.leftTab()) === '', await h.leftTab());
  await h.back(); ok('back link returns to the list with its search', (await h.count()) === qn && (await h.params()).q === 'glock', `${await h.count()}`);
  await h.search('');

  // a story with a multi-day curve: cumulative counts per day + milestones vs independent
  const cv = L.filter(e => e.span >= 4 && e.span <= 60 && e.n >= 6 && e.ps.every(p => p.d == null || p.d >= 0)).sort((a, b) => b.n - a.n)[0];
  await h.open({}, slugOf(cv)); await h.sleep(300);
  const num = await pg.evaluate(v => [...document.querySelectorAll(v + ' .tv-num tr[data-day]')].map(t => [+t.dataset.day, +t.children[2].textContent, +t.children[3].textContent]), V);
  const dd = [...new Set(cv.ps.filter(p => p.d != null).map(p => p.d))].sort((a, b) => a - b); let acc = 0;
  const exp = dd.map(d => { const k = cv.ps.filter(p => p.d === d).length; acc += k; return [d, k, acc]; });
  ok('spread curve: outlets per day and cumulative = independent', JSON.stringify(num) === JSON.stringify(exp), `${cv.id} ${JSON.stringify(num)} vs ${JSON.stringify(exp)}`);
  const ms = await pg.evaluate(v => [...document.querySelectorAll(v + ' .tv-chart text[data-ms]')].map(t => t.dataset.ms.split('|').map(Number)), V);
  ok('milestones sit on the curve', ms.length >= 1 && ms.every(([k, d]) => exp.some(e => e[0] === d && e[2] === k)) && ms.some(([k]) => k === acc), JSON.stringify(ms));
  const yTop = await h.chartTop(V + ' .tv-chart');
  ok('curve axis auto-scaled (AXIS-v1)', yTop >= acc && yTop <= Math.max(2 * acc, acc + 5), `${yTop} vs ${acc}`);
  // the US map threshold on a story with 1-5 qualifying sources: a line, not a map
  const few = L.find(e => { const q = qual(e); return q >= 1 && q <= 5; });
  if (few){ await h.open({}, slugOf(few)); await h.sleep(300);
    const st = await pg.evaluate(v => { const u = document.querySelector(v + ' .tv-us'); return [u.dataset.show, !!u.querySelector('svg'), u.textContent]; }, V);
    ok('US map rule: <= 5 qualifying sources -> one line, no map', st[0] === '0' && !st[1] && /Out of state/.test(st[2]), `${few.id} ${qual(few)} ${JSON.stringify(st)}`); }
  // CA county map when most counties are known
  const caOne = L.find(e => e.id !== 's00228' && e.n >= 6 && e.r.county && e.ps.filter(p => p.first.state === 'CA' && p.first.county).length >= e.n * 0.8 && new Set(e.ps.map(p => p.first.county)).size >= 3);
  if (caOne){ await h.open({}, slugOf(caOne)); await h.sleep(300);
    ok('CA county map drawn when most counties are known', await pg.evaluate(v => document.querySelectorAll(v + ' .tv-cmap path.on').length >= 2, V), caOne.id);
    await shot('page_ca', true); }
  // URL round-trip of a page
  await h.reload('#story-travel/' + slugOf(cv));
  ok('page URL round-trip', (await h.pageTitle()) === cv.r.hl.trim() || (await h.pageTitle()) === cv.r.hl, await h.pageTitle());
  // legacy links
  for (const [hash, id] of [['#insights/story_travel?id=s00228', 's00228'], ['#story_travel?id=' + cv.id, cv.id], ['#press-desk/story-travel?id=' + cv.id, cv.id]]){
    await h.hashGo(hash); ok('legacy ' + hash.split('?')[0] + ' opens the story page', (await h.hash()).startsWith('#story-travel/' + id), await h.hash()); }
  await h.hashGo('#insights/story_travel?id=s99999'); ok('legacy unknown id -> list searched for it', (await h.hash()).startsWith('#story-travel?') && (await h.params()).q === 's99999', await h.hash());
  ok('never left the tab overall (no #clips)', !(await pg.evaluate(() => (window.__nav || []).some(x => /^#clips/.test(x)))));
};
