// TABS-v1 framework test (agent-tabs): menu, redirects, Home/Clips untouched, the search-tab and entity-page components
// (through the stub module registered under every menu id + 'stub'). Counts are recomputed here from srv/blocks/data.json.
module.exports = async (pg, ok, h) => {
  const D = h.data(), TODAY = await h.TODAY();
  const cut = m => { const d = new Date(TODAY + 'T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() - m); return d.toISOString().slice(0, 10); };
  const topicsOf = rs => new Set(rs.map(r => String(r.topic || '').trim() || 'Unassigned'));
  const dated = D.filter(r => r.date), c24 = cut(24), w24 = dated.filter(r => r.date > c24);
  const tab = () => pg.evaluate(() => { const b = document.querySelector('nav.tabs button[aria-selected="true"]'); return b ? (b.dataset.tb || b.dataset.tab) : null; });
  const vis = sel => pg.evaluate(s => { const e = document.querySelector(s); if (!e) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }, sel);

  /* ---- menu ---- */
  const labels = await pg.evaluate(() => [...document.querySelectorAll('nav.tabs button')].filter(b => !b.hidden && getComputedStyle(b).display !== 'none').map(b => b.textContent.trim()));
  ok('menu order', JSON.stringify(labels.slice(0, 8)) === JSON.stringify(['Home', 'Clips', 'Data', 'Reporters', 'Outlets', 'Press releases', 'Bills', 'Story travel']), labels.join(' · '));
  ok('Press desk tab gone', !(await vis('#tab-in')) && !labels.includes('Press desk') && !labels.includes('Insights'));
  const nav = await pg.evaluate(() => { const n = document.querySelector('nav.tabs'), bs = [...n.querySelectorAll('button')].filter(b => !b.hidden);
    return { tops: [...new Set(bs.map(b => Math.round(b.getBoundingClientRect().top)))].length, sw: n.scrollWidth, cw: n.clientWidth, ox: getComputedStyle(n).overflowX }; });
  ok('tab row is one line', nav.tops === 1, JSON.stringify(nav));
  if (h.phone) ok('tab row scrolls sideways on a phone', nav.sw > nav.cw && /auto|scroll/.test(nav.ox), JSON.stringify(nav));
  ok('no horizontal page overflow (Stub list)', !(await h.overflowX()));

  /* ---- Home and Clips: same layout as v18 ---- */
  const geo = async () => pg.evaluate(async () => {
    const q = s => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; };
    const out = { hdr: document.querySelector('header.mast').offsetHeight };
    document.querySelector('#tab-ov').click(); await new Promise(r => setTimeout(r, 400));
    out.home = ['#view-ov .today-head', '#homeLine', '#tiles', '#attn', '#toneMix'].map(q);
    document.querySelector('#tab-db').click(); await new Promise(r => setTimeout(r, 500));
    out.clips = ['#rail', '#view-db .toolbar', '#chips', '#table', '#pager'].map(q); out.clipsN = (document.querySelector('#chips .result-line') || {}).textContent;
    /* RELCLIPS-v1 (DECISIONS 2026-10-28): the Clips table gains "From / Related press release" badges (taller rows on phones); the
       v18 layout is compared with them hidden (rp-final) */
    const rb = [...document.querySelectorAll('#table .badge.rel')]; rb.forEach(x => { x.style.display = 'none'; });
    out.clipsNoRel = ['#rail', '#view-db .toolbar', '#chips', '#table', '#pager'].map(q); rb.forEach(x => { x.style.display = ''; });
    return out; });
  const g1 = await geo();
  const p2 = await pg.context().newPage(); await p2.setViewportSize(h.viewport);
  await p2.addInitScript(() => { window.claude = { use: async n => { if (n === 'db') return { collection: () => ({ onSnapshot(cb){ setTimeout(() => cb({ docs: [] }), 30); return () => {}; }, doc(){ return { set: async () => {}, delete: async () => {} }; } }) }; throw new Error('no'); } }; });
  await p2.goto(new URL(pg.url()).origin + '/v18.html'); await p2.waitForTimeout(1200);
  const g0 = await p2.evaluate(async () => {
    const q = s => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; };
    const out = { hdr: document.querySelector('header.mast').offsetHeight };
    document.querySelector('#tab-ov').click(); await new Promise(r => setTimeout(r, 400));
    out.home = ['#view-ov .today-head', '#homeLine', '#tiles', '#attn', '#toneMix'].map(q);
    document.querySelector('#tab-db').click(); await new Promise(r => setTimeout(r, 500));
    out.clips = ['#rail', '#view-db .toolbar', '#chips', '#table', '#pager'].map(q); out.clipsN = (document.querySelector('#chips .result-line') || {}).textContent;
    return out; });
  await p2.close();
  const rel = (g, k) => JSON.stringify(g[k].map(b => b && [b[0], Math.round((b[1] - (b[0] < 0 ? 0 : g.hdr)) / 2) * 2, b[2], b[3]]));   // 1 px sub-pixel rounding tolerated
  /* MASTHEAD-v2 (Sammy 2026-10-28, "reorganize this header so that it displays buttons for tabs cleanly"; agent-v20b-subtitle): the
     phone header is two button rows + the scrolling tab row, no taller than v18's (rp-final: was "= v18") */
  if (h.phone) ok('header height <= v18 (phone: MASTHEAD-v2, tab row scrolls)', g1.hdr <= g0.hdr && g1.hdr >= 120, `${g1.hdr} vs v18 ${g0.hdr}`);
  else ok('header height (desktop: 8 tabs need a second header row; v18 had one at <= 1280 px too)', g1.hdr >= g0.hdr && g1.hdr <= g0.hdr + 60, `${g1.hdr} vs v18 ${g0.hdr}`);
  /* v19 changes Home on purpose: no 30-day line (HOMELINE-off), upkeep items moved to Manage (HOMEUPKEEP-v1). The heading and the
     tiles keep their size; everything else keeps its width and column */
  const hm1 = JSON.parse(rel(g1, 'home')), hm0 = JSON.parse(rel(g0, 'home'));
  ok('Home: heading = v18, no 30-day line, tiles/attention/tone keep their size and column', JSON.stringify(hm1[0]) === JSON.stringify(hm0[0]) && hm1[1] === null   /* the baseline page (build/shell/index.html, the same file the build starts from) has carried HOMELINE-off since 2026-10-30, so v18's 30-day line is no longer there to compare: only 'none now' is checked */
    && [2, 3, 4].every(i => hm1[i][0] === hm0[i][0] && hm1[i][2] === hm0[i][2]) && hm1[2][3] === hm0[2][3], JSON.stringify(hm1) + ' vs ' + JSON.stringify(hm0));
  /* the v18 page carries its own (older) data, so row heights and the story count differ with the data; the layout is compared on what does not:
     rail, toolbar and chips exactly; table and pager by left edge and width, the table starting where v18's does and the pager below it */
  { const a = JSON.parse(rel(g1, 'clipsNoRel')), b = JSON.parse(rel(g0, 'clips'));
    ok('Clips layout = v18 (below the header; release badges hidden, RELCLIPS-v1; table/pager heights follow the data)', JSON.stringify(a.slice(0, 3)) === JSON.stringify(b.slice(0, 3)) && [3, 4].every(i => a[i] && b[i] && a[i][0] === b[i][0] && a[i][2] === b[i][2]) && a[3][1] === b[3][1] && a[4][1] >= a[3][1] + a[3][3] - 2, JSON.stringify(a) + ' vs ' + JSON.stringify(b)); }
  /* the count is the fixture's own story count (Clips shows every story, List-only included), computed from data.json, not v18's */
  { const n = h.dataAll().length; ok('Clips count = every story in the fixture data', g1.clipsN.includes(n.toLocaleString('en-US') + ' of ' + n.toLocaleString('en-US')), g1.clipsN + ' vs ' + n); }

  /* ---- search tab (stub: issues over stories) ---- */
  await h.open();
  ok('Stub tab selected', (await tab()) === 'stub');
  ok('default 24-month window: count = independent', (await h.count()) === topicsOf(w24).size, `${await h.count()} vs ${topicsOf(w24).size}`);
  ok('total = every issue', (await h.total()) === topicsOf(dated).size);
  ok('default filter shows as a chip', (await h.chips()).some(c => /Date range/.test(c) && /24 months/.test(c)), (await h.chips()).join(' | '));
  await h.search('GUNS');
  const kq = await h.rowKeys();
  ok('search is case-insensitive', kq.length === 1 && kq[0] === 'guns', kq.join(','));
  await h.search('ímmigration');
  ok('search is accent-insensitive', (await h.rowKeys()).join() === 'immigration-daca', (await h.rowKeys()).join());
  ok('search in URL', (await h.params()).q === 'ímmigration');
  await h.search('');
  const spN = topicsOf(w24.filter(r => r.lang === 'Spanish')).size;
  ok('facet count shown = independent (Spanish)', (await h.facetCount('lang', 'Spanish')) === spN, `${await h.facetCount('lang', 'Spanish')} vs ${spN}`);
  await h.facet('lang', 'Spanish');
  ok('language filter = independent', (await h.count()) === spN, `${await h.count()} vs ${spN}`);
  const byT = new Map(); w24.filter(r => r.lang === 'Spanish').forEach(r => { const t = String(r.topic || '').trim() || 'Unassigned'; byT.set(t, (byT.get(t) || 0) + 1); });
  const midN = [...byT.values()].filter(n => n >= 10 && n < 100).length;
  ok('item facet count (10 to 99, given Spanish) = independent', (await h.facetCount('size', 'mid')) === midN, `${await h.facetCount('size', 'mid')} vs ${midN}`);
  await h.facet('size', 'mid');
  ok('combined filters = independent', (await h.count()) === midN, `${await h.count()} vs ${midN}`);
  const p1 = await h.params();
  ok('filters in URL', p1.lang === 'Spanish' && p1.size === 'mid' && !('date' in p1), JSON.stringify(p1));
  await h.reload('#stub?' + new URLSearchParams(p1).toString());
  ok('URL round-trip restores the list', (await h.count()) === midN && (await h.chips()).length === 3, `${await h.count()} ${(await h.chips()).join(' | ')}`);
  await h.removeChip((await h.chips()).findIndex(c => /Story count/.test(c)));
  ok('removing a chip widens the list', (await h.count()) === spN);
  await h.removeChip((await h.chips()).findIndex(c => /Date range/.test(c)));
  const allSp = topicsOf(dated.filter(r => r.lang === 'Spanish')).size;
  ok('removing the default date chip: all dates, kept in URL as ~', (await h.count()) === allSp && (await h.params()).date === '~', `${await h.count()} vs ${allSp} ${JSON.stringify(await h.params())}`);
  await h.reload('#stub?' + new URLSearchParams(await h.params()).toString());
  ok('cleared default survives a reload', (await h.count()) === allSp);
  await h.clearAll();
  ok('clear all = every issue', (await h.count()) === topicsOf(dated).size);
  await h.customDate('date', '2020-01-01', '2020-12-31');
  const y20 = topicsOf(dated.filter(r => r.date >= '2020-01-01' && r.date.slice(0, 10) <= '2020-12-31')).size;
  ok('custom date range = independent', (await h.count()) === y20 && (await h.params()).date === 'c:2020-01-01..2020-12-31', `${await h.count()} vs ${y20}`);
  await h.clearAll();
  await h.sort('stories');   // default is stories desc -> now asc on desktop (header click toggles); on phone the select keeps desc
  const keys = await h.rowKeys(), cnt = new Map(); dated.forEach(r => { const t = String(r.topic || '').trim() || 'Unassigned'; cnt.set(t, (cnt.get(t) || 0) + 1); });
  const sorted = [...cnt.entries()].sort((a, b) => h.phone ? b[1] - a[1] : a[1] - b[1]);
  const slug = s => h.fold(s).replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  ok('sort by stories', keys[0] === slug(sorted[0][0]), keys[0] + ' vs ' + sorted[0][0]);
  ok('show-more cap (stub: 10 desktop / 5 phone)', keys.length === (h.phone ? 5 : 10));
  await h.more();
  ok('show more', (await h.rowKeys()).length === (h.phone ? 10 : cnt.size));
  const csv = await h.exportCsv();
  ok('CSV = every listed issue + header', csv && csv.text.replace(/^﻿/, '').trim().split(/\r\n/).length === cnt.size + 1 && /^﻿?Issue,Stories,Negative,Tone avg,Last story/.test(csv.text), csv && csv.text.slice(0, 80));
  const names = await h.exportCopy(0);
  ok('extra copy (names)', names && names.split('\n').length === cnt.size);
  const tsv = await h.exportCopy();
  ok('copy list (TSV)', tsv && tsv.split('\n')[0] === 'Issue\tStories\tNegative\tTone avg\tLast story');
  // tone average helper: Guns, all dates, rated only
  const P = { 'Very positive': 2, 'Positive': 1, 'Neutral': 0, 'Negative': -1, 'Very negative': -2 }, gr = dated.filter(r => r.topic === 'Guns' && r.tone in P);
  // TONELABEL-v1 (DECISIONS 2026-10-28): "<Label> <signed value>", banded at the midpoints of the one-decimal value; n in the tooltip
  const avg = gr.reduce((s, r) => s + P[r.tone], 0) / gr.length, r1 = Math.round(avg * 10) / 10, ab = Math.abs(r1);
  const band = ['Very negative', 'Negative', 'Neutral', 'Positive', 'Very positive'][2 + (ab < 0.5 ? 0 : ab < 1.5 ? 1 : 2) * (r1 < 0 ? -1 : 1)];
  const want = band + ' ' + (r1 > 0 ? '+' : r1 < 0 ? '−' : '') + ab.toFixed(1), wantN = new RegExp(`\\b${gr.length} rated`);
  const toneCell = await pg.evaluate(() => { const tr = document.querySelector('#tbBody .tb-view:not([hidden]) tr[data-ttk="guns"]'); if (!tr) return null; const c = tr.children[3]; return { t: c.textContent.trim(), title: c.getAttribute('title') || (c.querySelector('[title]') || {}).title || '' }; });
  ok('tone average label + value (n in tooltip where shown) = independent (Guns)', toneCell && toneCell.t === want && (!toneCell.title || wantN.test(toneCell.title)), `${JSON.stringify(toneCell)} vs ${want} (n=${gr.length})`);
  ok('no horizontal overflow (list)', !(await h.overflowX()));
  { await h.openRail(); ok('filter drawer opens', await pg.evaluate(() => !!document.querySelector('#tbBody .tb-view:not([hidden]) .tt-rail.open'))); await h.closeRail(); }
  await h.shot('framework_stub_list');

  /* ---- entity page ---- */
  await h.open({ date: '~', q: 'guns' });
  const listHash = await h.hash();
  await h.openRow('guns');
  ok('row opens the page #stub/guns', /^#stub\/guns/.test(await h.hash()), await h.hash());
  const gAll = dated.filter(r => r.topic === 'Guns');
  ok('page header', (await h.pageTitle()) === 'Guns' && (await h.pageFacts())['Stories'] === gAll.length.toLocaleString('en-US'), JSON.stringify(await h.pageFacts()));
  ok('page lists every story of the entity', (await h.pageCount()) === gAll.length && (await h.pageTotal()) === gAll.length, `${await h.pageCount()} vs ${gAll.length}`);
  const fts = gAll.filter(r => h.fold(r.hl + ' ' + r.outlet).includes('newsom'));
  await h.pageSearch('NEWSOM');
  const pc = await h.pageCount();
  ok('in-page search narrows to this entity (case/accent-insensitive; headline/outlet hits at least)', pc >= fts.length && pc < gAll.length, `${pc} (>= ${fts.length})`);
  ok('in-page search in URL', /[?&]q=NEWSOM/.test(await h.hash()));
  await h.pageSearch('');
  await pg.evaluate(() => { const v = document.querySelector('#tbBody .tb-view:not([hidden])'); const d = v.querySelector('details[data-tbefacet="tone"]'); if (d) d.open = true; });
  await pg.click('#tbBody .tb-view:not([hidden]) .tbe-ft'); await h.sleep(300);
  await pg.click('#tbBody .tb-view:not([hidden]) input[data-tbef="tone"][value="Negative"]'); await h.sleep(300);
  await pg.click('#tbBody .tb-view:not([hidden]) .tt-rail.open [data-tbe="done"]'); await h.sleep(300);
  const gNeg = gAll.filter(r => r.tone === 'Negative').length;
  ok('page filter (Clips facets) = independent', (await h.pageCount()) === gNeg, `${await h.pageCount()} vs ${gNeg}`);
  const ph = await h.hash();
  await h.reload(ph);
  ok('page URL round-trip', (await h.pageCount()) === gNeg && /^#stub\/guns\?/.test(await h.hash()), await h.hash());
  const ids = await h.pageRowIds();
  if (ids.length){ await pg.click(`#tbBody .tb-view:not([hidden]) .tbe-body tr[data-id="${ids[0]}"] .hl`); await h.sleep(500);
    ok('story panel opens from the page', await pg.evaluate(() => !document.querySelector('#sheet').hidden));
    await pg.evaluate(() => { const b = document.querySelector('#sheet [data-close]'); if (b) b.click(); }); await h.sleep(200); }
  await pg.click('#tbBody .tb-view:not([hidden]) .tbe-head + .grid-clips .dlmenu summary, #tbBody .tb-view:not([hidden]) .tbe .dlmenu summary'); await pg.click('#tbBody .tb-view:not([hidden]) [data-tbe="csv"]'); await h.sleep(400);
  const dl = (await h.downloads()).pop();
  ok('page CSV = the listed stories (Clips exporter)', dl && dl.text.replace(/^﻿/, '').trim().split(/\r\n/).length === gNeg + 1, dl && dl.filename);
  ok('no horizontal overflow (page)', !(await h.overflowX()));
  await h.shot('framework_stub_page');
  await h.back();
  ok('back link returns to the list with its filters', (await h.hash()) === listHash || (await h.hash()).startsWith('#stub?q=guns'), `${await h.hash()} vs ${listHash}`);
  await pg.click('#tab-db'); await h.sleep(400);
  ok('Clips untouched by the page (no filter carried; every story in the fixture data)', await pg.evaluate(n => document.querySelector('#chips .result-line').textContent.includes(n.toLocaleString('en-US') + ' of ' + n.toLocaleString('en-US')) && !document.querySelector('#chips .chip'), h.dataAll().length), await pg.evaluate(() => document.querySelector('#chips').textContent.slice(0, 80)));

  /* ---- entity-page chart = Data's chart over the entity's stories ---- */
  await h.open({ ci: 'year' }, 'guns');
  const yrs = new Map(); gAll.forEach(r => { const y = r.date.slice(0, 4); yrs.set(y, (yrs.get(y) || 0) + 1); });
  const y0 = Math.min(...gAll.map(r => +r.date.slice(0, 4)));
  const tbl = await pg.evaluate(() => [...document.querySelectorAll('#tbBody .tb-view:not([hidden]) .tbe-ctable tbody tr')].map(tr => [tr.children[0].textContent, +tr.lastElementChild.textContent]));
  const want2 = [...yrs.entries()].filter(([y]) => +y >= y0).sort();
  ok('page chart: stories per year = independent', JSON.stringify(tbl) === JSON.stringify(want2), JSON.stringify(tbl).slice(0, 200) + ' vs ' + JSON.stringify(want2).slice(0, 200));
  ok('page chart starts at the entity\'s first year', (await pg.evaluate(() => document.querySelector('#tbBody .tb-view:not([hidden]) .tbe-chart [data-tbc="from"]').value)) === String(y0));
  await pg.evaluate(() => { const d = document.querySelector('#tbBody .tb-view:not([hidden]) .tbe-copts'); d.open = true; }); await h.sleep(100);
  await pg.click('#tbBody .tb-view:not([hidden]) [data-tbqv="tone"]'); await h.sleep(400);
  const ty = '2024', tr24 = gAll.filter(r => r.date.startsWith(ty) && r.tone in P), tv = tr24.reduce((a, r) => a + P[r.tone], 0) / tr24.length;
  const dot = await pg.evaluate(y => { const c = document.querySelector(`#tbBody .tb-view:not([hidden]) .tbe-chart circle.tb-tone[data-b="${y}"]`); return c ? [+c.dataset.tv, +c.dataset.tn] : null; }, ty);
  ok('page chart: tone average line (2024) = independent', dot && Math.abs(dot[0] - tv) < 0.006 && dot[1] === tr24.length, JSON.stringify(dot) + ' vs ' + tv.toFixed(2) + ' n=' + tr24.length);
  ok('page chart: tone mix series', await pg.evaluate(() => /Negative/.test(document.querySelector('#tbBody .tb-view:not([hidden]) .tbe-cleg').textContent)));
  ok('chart state in URL', /[?&]cq=tone/.test(await h.hash()) && /[?&]ct=1/.test(await h.hash()), await h.hash());
  await pg.evaluate(y => { const rs = [...document.querySelectorAll('#tbBody .tb-view:not([hidden]) .tbe-cchart rect.hit')]; const from = +document.querySelector('#tbBody .tb-view:not([hidden]) .tbe-chart [data-tbc="from"]').value; rs[+y - from].dispatchEvent(new MouseEvent('click', { bubbles: true })); }, ty);
  await h.sleep(400);
  ok('click a bar: the page list shows that year', (await h.pageCount()) === (yrs.get(ty) || 0) && /when=y2024/.test(await h.hash()), `${await h.pageCount()} vs ${yrs.get(ty)} ${await h.hash()}`);
  await pg.evaluate(() => scrollTo(0, 0)); await h.shot('framework_stub_page_chart_guns');
  await h.open({}, 'tiny');
  ok('small entity: a plain line, no chart', await pg.evaluate(() => { const v = document.querySelector('#tbBody .tb-view:not([hidden])'); return v.querySelector('.tbe-cchart').hidden && /Only 2 stories/.test(v.querySelector('.tbe-cnote').textContent); }));
  await h.shot('framework_stub_page_chart');

  /* ---- AXIS-v1: every chart scales its y axis to the data shown ---- */
  const nice = v => { const p = Math.pow(10, Math.floor(Math.log10(v) + 1e-9)), m = v / p; return [1, 2, 2.5, 5, 10].some(x => Math.abs(m - x) < 1e-6) || [1.5, 3, 4, 6, 8].some(x => Math.abs(m - x) < 1e-6); };
  const PC = '#tbBody .tb-view:not([hidden]) .tbe-cchart';
  /* a clean axis: gridline labels 0, s, 2s, ... with s = 1, 2, 2.5 or 5 x 10^n */
  const clean = async sel => { const l = await pg.evaluate(s => [...document.querySelectorAll(s + ' svg g.grid text')].map(x => +x.textContent.replace(/[,%]/g, '')).filter(x => !isNaN(x)).sort((a, b) => a - b), sel);
    if (l.length < 3 || l[0] !== 0) return false; const st = l[1] - l[0]; return l.every((v, i) => Math.abs(v - i * st) < 1e-6) && nice(st); };
  const tmax = () => pg.evaluate(() => Math.max(0, ...[...document.querySelectorAll('#tbBody .tb-view:not([hidden]) .tbe-ctable tbody tr')].map(tr => +tr.lastElementChild.textContent)));
  await h.open({ ci: 'year' }, 'guns'); const big = [await h.chartTop(PC), await tmax()];
  await h.open({ ci: 'year', q: 'newsom', tone: 'Negative' }, 'guns'); const small = [await h.chartTop(PC), await tmax()];
  ok('entity chart: big and small sets get different clean maxima, no clipping', big[0] !== small[0] && big[0] >= big[1] && small[0] >= small[1] && big[0] <= big[1] * 2.6 && small[0] <= Math.max(2, small[1] * 2.6), JSON.stringify({ big, small }));
  ok('entity chart: clean ticks on the small set', await clean(PC));
  const tops = await pg.evaluate(s => { const svg = document.querySelector(s + ' svg'); if (!svg) return null; const g = [...svg.querySelectorAll('g.grid line')].map(l => +l.getAttribute('y1')); const top = Math.min(...g);
    const ys = [...svg.querySelectorAll('path')].filter(p => !p.classList.contains('avg')).map(p => Math.min(...(p.getAttribute('d').match(/[-\d.]+/g) || []).map(Number).filter((_, i) => i % 2 === 1))); return [top, Math.min(...ys)]; }, PC);
  ok('entity chart: tallest bar below the top gridline', tops && tops[1] >= tops[0] - 0.01, JSON.stringify(tops));
  await h.open({ ci: 'year', cq: 'tone', cb: 'tone', ct: '1' }, 'guns');
  const ts = await pg.evaluate(() => { const g = document.querySelector('#tbBody .tb-view:not([hidden]) .tb-tscale'); const v = [...document.querySelectorAll('#tbBody .tb-view:not([hidden]) circle.tb-tone')].map(c => Math.abs(+c.dataset.tv)); return [g ? +g.dataset.t : null, Math.max(...v)]; });
  ok('tone axis: symmetric, zoomed to the data (not fixed at +-2)', ts[0] && ts[0] >= ts[1] && ts[0] <= Math.max(0.5, ts[1] * 2.2) && ts[0] <= 2, JSON.stringify(ts));
  await h.open({ q: 'zzqqxx-nothing' }, 'guns');
  ok('all-zero chart: an empty state, not a broken axis', await h.chartEmpty(PC));
  // Data's chart: a 30-day period vs all dates
  await pg.click('#tab-an'); await h.sleep(600);
  const dataTop = async w => { await pg.selectOption('#rpWhen', w); await h.sleep(500); return [await h.chartTop('#tsChart'), await pg.evaluate(() => Math.max(0, ...[...document.querySelectorAll('#tsTable tbody tr')].map(tr => +tr.lastElementChild.textContent)))]; };
  const dAll = await dataTop('all'), cAll = await clean('#tsChart'), d30 = await dataTop('30'), c30 = await clean('#tsChart');
  ok('Data chart: all dates vs last 30 days get different clean maxima, no clipping', dAll[0] !== d30[0] && dAll[0] >= dAll[1] && d30[0] >= d30[1] && cAll && c30 && d30[0] <= Math.max(2, d30[1] * 2.6), JSON.stringify({ dAll, d30, cAll, c30 }));
  const ints = await pg.evaluate(() => [...document.querySelectorAll('#tsChart svg g.grid text')].map(t => t.textContent));
  ok('Data chart: small counts get integer ticks', ints.every(t => /^[\d,]+$/.test(t)), ints.join(' '));
  await pg.selectOption('#rpWhen', 'all'); await h.sleep(400);
  await pg.evaluate(() => { const r = document.querySelectorAll('#tsChart rect.hit'); r[r.length - 1].dispatchEvent(new MouseEvent('click', { bubbles: true })); }); await h.sleep(500);
  ok('Data chart click still opens Clips on that period', (await tab()) === 'db' && await pg.evaluate(() => !!document.querySelector('#chips .chip')));
  /* the tabs never send the user to Clips (entity page actions, list actions) */
  await h.open({}, 'guns'); await h.markNav();
  for (const sel of ['.tbe-body tr[data-id] .tag[data-fk="topic"]', '.tbe-body tr[data-id] .tlink[data-pub]']){ const e = await pg.$('#tbBody .tb-view:not([hidden]) ' + sel); if (e && await e.isVisible()){ await e.click(); await h.sleep(250); } }
  await pg.evaluate(() => { const r = document.querySelectorAll('#tbBody .tb-view:not([hidden]) .tbe-cchart rect.hit'); if (r.length) r[r.length - 1].dispatchEvent(new MouseEvent('click', { bubbles: true })); }); await h.sleep(300);
  ok('entity page never navigates to Clips', (await h.leftTab()) === '' && (await tab()) === 'stub', await h.leftTab());

  /* ---- USMAP-v1: the state map shows only with MORE than 5 qualifying out-of-state sources ---- */
  const CM = h.block('tab_common'), US = new Set(['AL','AK','AZ','AR','CO','CT','DE','DC','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']);
  const natRx = /(^|;\s*)(National|International|Trade, advocacy & blogs)(;|$)/;
  const qual = Object.entries(CM.o).filter(([, g]) => US.has(g[0]) && !natRx.test(g[1]) && g[2] !== 'Wire' && g[0] !== 'USA').map(([n]) => n);
  const natO = Object.entries(CM.o).filter(([, g]) => g[0] === 'USA' || natRx.test(g[1]) || g[2] === 'Wire').map(([n]) => n);
  await h.open();
  const um = async outs => pg.evaluate(o => { const c = window.__tbctx, host = document.createElement('div'); host.id = 'usTest'; document.querySelector('#tbBody .tb-view:not([hidden])').appendChild(host);
    const M = c.usMap(host, o, {}); const r = { show: host.dataset.show, q: M.qualifying, states: [...host.querySelectorAll('path.on')].map(p => [p.dataset.st, +/: (\d+)/.exec(p.getAttribute('aria-label'))[1]]).sort(), line: (host.querySelector('.tb-us-line') || {}).textContent || '' }; return r; }, outs);
  const five = qual.slice(0, 5), six = qual.slice(0, 6);
  const r5 = await um(five.concat(natO.slice(0, 3)));
  await pg.evaluate(() => document.querySelector('#usTest').remove());
  const r6 = await um(six.concat(natO.slice(0, 3)));
  const by6 = new Map(); six.forEach(n => { const s = CM.o[n][0]; by6.set(s, (by6.get(s) || 0) + 1); });
  ok('state map hidden at 5 qualifying sources (one "Out of state" line; nationals not counted)', r5.show === '0' && r5.q === 5 && /^Out of state: /.test(r5.line) && /National outlets: 3\./.test(r5.line), JSON.stringify(r5));
  ok('state map shown at 6, per-state counts = independent', r6.show === '1' && r6.q === 6 && JSON.stringify(r6.states) === JSON.stringify([...by6].sort()), JSON.stringify(r6) + ' vs ' + JSON.stringify([...by6].sort()));
  const st0 = r6.states[0][0];
  await pg.click(`#usTest path[data-st="${st0}"]`); await h.sleep(200);
  // GEOMAP-v1 (DECISIONS 2026-10-28): a click pins the state's preview; its expand button opens Clips filtered by that State
  const pinU = await pg.evaluate(() => { const t = document.querySelector('#usTest .cmap-tip'), b = t && t.querySelector('.tacts [data-tbclip]');
    return t ? { pinned: t.classList.contains('pinned') && !t.hidden, head: (t.querySelector('h4 .tt') || {}).textContent || '', items: t.querySelectorAll('li').length, sel: b ? JSON.parse(b.dataset.tbclip) : null } : null; });
  const st0n = await pg.evaluate(st => (/^(.+?): /.exec((document.querySelector(`#usTest path[data-st="${st}"]`) || { getAttribute: () => '' }).getAttribute('aria-label') || '') || [])[1] || st, st0);
  ok('click a state pins its preview; expand = Clips filtered by that State (GEOMAP-v1)', pinU && pinU.pinned && pinU.head.startsWith(st0n + ' · ') && pinU.items > 0 && pinU.sel && JSON.stringify(pinU.sel.state) === JSON.stringify([st0n]), JSON.stringify(pinU));
  await pg.evaluate(() => document.querySelector('#usTest').remove());
  // Data › Outlets & reach: the state map on all dates, counted independently
  await pg.click('#tab-an'); await h.sleep(500); await pg.selectOption('#rpWhen', 'all'); await h.sleep(500);
  await pg.evaluate(() => { document.querySelectorAll('#view-an .rp-sec.rg-shut .rg-sh').forEach(b => b.click()); });
  // GEOMAP-v1 (DECISIONS 2026-10-28): Data's state map (#gmUs, its own card under the county map) counts CLIPS: per story, each
  // out-of-state regional/local outlet (Original + reprints) once per state; national/Reach-national/wire/USA/CA outlets not counted
  const canon = (n, aid) => (CM.a[aid]) || CM.n[n] || n;
  const place = (n, aid, st0) => { const o = CM.o[n] || CM.o[canon(n, aid)] || null; const st = o ? o[0] : (st0 || '');
    if (!st || st === 'USA' || (o && (natRx.test(o[1] || '') || o[2] === 'Wire')) || st === 'CA') return ''; return US.has(st) ? st : ''; };
  const dBy = new Map(); D.forEach(r => { const seen = new Set(), add = (o, aid, st0) => { const st = place(o, aid, st0); if (!st || seen.has(o + '|' + st)) return; seen.add(o + '|' + st); dBy.set(st, (dBy.get(st) || 0) + 1); };
    add(String(r.outlet || '').replace(/\s*\(\+.*$/, ''), r.aid); (r.reps || []).forEach(p => p && p.outlet && add(String(p.outlet).trim(), p.aid, p.state)); });
  const dm = await pg.evaluate(() => { const h = document.querySelector('#gmUs'); return h ? { states: [...h.querySelectorAll('svg path.on')].map(p => [p.dataset.st, +/: ([\d,]+)/.exec(p.getAttribute('aria-label'))[1].replace(/,/g, '')]).sort() } : null; });
  ok('Data: state map card under the county map, per-state clip counts = independent (GEOMAP-v1)', dm && dm.states.length > 0 && JSON.stringify(dm.states) === JSON.stringify([...dBy].sort()), JSON.stringify(dm).slice(0, 300) + ' vs ' + JSON.stringify([...dBy].sort()).slice(0, 300));
  await pg.evaluate(() => { const m = document.querySelector('#gmUsCard'); if (m) m.scrollIntoView({ block: 'center' }); }); await h.shot('framework_data_usmap');

  /* ---- redirects of old links ---- */
  const R = [['#insights', 'reporters', /^#reporters/], ['#insights/reporters?author=Jane%20Doe&win=12', 'reporters', /^#reporters\?q=Jane/],
    ['#press-desk', 'reporters', /^#reporters/], ['#press-desk/pitch?win=24', 'reporters', /^#reporters$|^#reporters\?(?!.*win)/],
    ['#press-desk/releases', 'releases', /^#press-releases/], ['#insights/release_pickup?id=s00018', 'releases', /^#press-releases\?q=s00018/],
    ['#press-desk/bills', 'bills', /^#bills/], ['#insights/bill_timeline', 'bills', /^#bills/],
    ['#press-desk/story-travel?id=s00001', 'travel', /^#story-travel\?q=s00001/], ['#insights/story_travel?id=s00001', 'travel', /^#story-travel/],
    ['#story_travel', 'travel', /^#story-travel/], ['#release_pickup', 'releases', /^#press-releases/], ['#bill_timeline', 'bills', /^#bills/], ['#pitch', 'reporters', /^#reporters/]];
  for (const [from, want, rx] of R){ await h.hashGo(from); const t = await tab(), hh = await pg.evaluate(() => location.hash);
    ok(`redirect ${from}`, t === want && rx.test(decodeURIComponent(hh)), `${t} ${hh}`); }
  for (const [from, want] of [['#insights/story_travel?id=s00001', 'travel'], ['#press-desk/pitch?win=12', 'reporters']]){
    await h.reload(from); ok(`redirect on page load ${from}`, (await tab()) === want && !/win=/.test(await h.hash()), `${await tab()} ${await h.hash()}`); }
  await h.reload('#press-desk/tone-by-issue'); ok('Tone by issue link still opens Data', (await tab()) === 'an');
  await h.reload('#data'); ok('#data opens Data', (await tab()) === 'an');
  await h.reload('#clips'); ok('#clips opens Clips', (await tab()) === 'db');
  await h.reload('#outlets/guns'); ok('deep link to an entity page on page load', (await tab()) === 'outlets' && (await pg.evaluate(() => (document.querySelector('#tbBody .tb-view:not([hidden]) .tbe-head h2') || {}).textContent)) === 'Guns');
  /* entry points that used to open Press desk views */
  await h.reload('');
  await pg.evaluate(() => { const b = document.createElement('button'); b.dataset.insGo = 'story_travel'; b.dataset.insK = 'id'; b.dataset.insV = 's00001'; document.body.appendChild(b); b.click(); b.remove(); }); await h.sleep(400);
  ok('data-ins-go story_travel -> Story travel tab', (await tab()) === 'travel' && /^#story-travel\?q=s00001/.test(await h.hash()), await h.hash());
  await pg.click('#tab-an'); await h.sleep(600);
  const dl2 = await pg.evaluate(() => [...document.querySelectorAll('#view-an [data-ins-go]')].map(b => b.textContent.trim()));
  ok('Data links name the new tabs', dl2.includes('Bills tab ›') && dl2.includes('Reporters tab ›') && !dl2.some(t => /Press desk/.test(t)), dl2.join(' | '));
  await pg.evaluate(() => { const v = document.querySelector('#view-an'); v.querySelectorAll('.rp-sec.rg-shut .rg-sh').forEach(b => b.click()); [...v.querySelectorAll('[data-ins-go]')].find(b => /Bills tab/.test(b.textContent)).click(); }); await h.sleep(400);
  ok('Data "Bills tab ›" opens Bills', (await tab()) === 'bills');
  await pg.click('#tab-an'); await h.sleep(400);
  await pg.evaluate(() => [...document.querySelectorAll('#view-an [data-ins-go]')].find(b => /Reporters tab/.test(b.textContent)).click()); await h.sleep(400);
  ok('Data "Reporters tab ›" opens Reporters (win dropped)', (await tab()) === 'reporters' && !/win=/.test(await h.hash()), await h.hash());
  ok('nav click on another tab', await (async () => { await pg.click('#tab-tb-outlets'); await h.sleep(300); return (await tab()) === 'outlets' && /^#outlets/.test(await h.hash()); })());
  if (h.phone){ await pg.click('#tab-tb-travel'); await h.sleep(300);
    ok('phone: the active tab is scrolled into view', await pg.evaluate(() => { const b = document.querySelector('#tab-tb-travel'), n = b.parentElement, r = b.getBoundingClientRect(), q = n.getBoundingClientRect(); return r.left >= q.left - 1 && r.right <= q.right + 1; }));
    await h.shot('framework_nav_travel'); }
};
