// Bills tab test (agent-tab-bills). Run: cd build/tests/tabs && NODE_PATH=/opt/npm-tools/node_modules MOD=bills node harness.js
// Counts are recomputed here from srv/blocks/*.json (data, billsinfo, ins_bill_timeline, ins_release_pickup), never read from the page.
const path = require('path'), fs = require('fs');
const SHOTS = path.resolve(__dirname, '../../../work/tests_out/tabs/shots/bills');
module.exports = async (pg, ok, h) => {
  const V = '#tbBody .tb-view[data-tb="bills"]:not([hidden])', W = h.viewport.width;
  /* ---------- independent model ---------- */
  const RX = /^((AB|SB|ACA|ACR|AJR|HR) \d{1,4}|(AB|SB)X\d{1,2}-\d{1,4})$/;   // the tracker's bill parser (SPLITBILLS-v2: + extraordinary-session numbers; final-int: + HR, the 20 Assembly resolutions with leginfo titles)
  const D = h.data(), info = h.block('billsinfo').rows, TL = h.block('ins_bill_timeline').b, REL = h.block('ins_release_pickup').rel;
  const bk = b => String(b).toUpperCase().replace(/[^A-Z0-9]/g, '');
  const sesL = s => { const m = String(s).match(/^(\d{4})-\d{2}(\d{2})(.*)$/); return m ? m[1] + '–' + m[2] + (m[3].trim() ? ' ' + m[3].trim() : '') : s; };
  const slug = s => h.fold(s).replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  const start = s => (+String(s).slice(0, 4) - 1) + '-12-01';
  const sesBy = new Map(); info.forEach(b => { const a = sesBy.get(bk(b.bill)) || sesBy.set(bk(b.bill), []).get(bk(b.bill)); if (!a.includes(b.session)) a.push(b.session); }); sesBy.forEach(a => a.sort());
  const pick = (k, d) => { const ss = sesBy.get(k) || []; const dd = d.length < 10 ? d.slice(0, 7) + '-15' : d; return ss.filter(s => start(s) <= dd).pop() || ss[0]; };
  const ms = new Map(TL.map(x => [bk(x[0]) + '|' + x[1], x]));
  const items = new Map();
  /* COAUTH-v1 (integration): author-led bills, plus coauthored bill-sessions that stories are tagged with */
  info.forEach(b => { const k = bk(b.bill) + '|' + b.session; if (!items.has(k)) items.set(k, { k, bill: b.bill, ses: b.session, title: b.title.replace(/\.$/, ''), rs: [], rels: [], m: ms.get(k), co: !/^author/i.test(b.role), status: b.status, budget: !!(b.budget_act || b.budgetAct) }); });
  D.forEach(r => { if (!r.date) return; [...new Set((r.bills || []).filter(b => RX.test(b)))].forEach(b => { const it = items.get(bk(b) + '|' + pick(bk(b), r.date)); if (it) it.rs.push(r); }); });
  /* RELSES-v1 (rp-clips): a bill page lists only releases from the bill's own session: in rp-threads' thread for the bill +
     session (tab_releases thr.th, any row form), or naming the bill and dated in that session (Dec of an even year = next) */
  const THR = (h.block('tab_releases') || {}).thr, thIn = new Set(), iPid = (h.block('ins_release_pickup').cols || []).indexOf('prid');
  if (THR) THR.th.forEach(t => t[2].forEach(row => t[0].forEach(b => thIn.add(bk(b) + '|' + t[1] + '|' + (Array.isArray(row) ? row[0] : row)))));
  const TN = (t, k) => { const m = /^([A-Z]+)(\d+)$/.exec(k); if (!m) return false; const W = { AB: 'Assembly Bill', SB: 'Senate Bill', ACR: 'Assembly Concurrent Resolution', ACA: 'Assembly Constitutional Amendment', AJR: 'Assembly Joint Resolution' }[m[1]];
    return new RegExp('(^|[^A-Za-z0-9])(' + m[1].split('').join('\\.?\\s?') + '\\.?' + (W ? '|' + W : '') + ')\\s*(No\\.?\\s*)?' + m[2] + '(?![0-9])', 'i').test(String(t || '')); };
  const dSes = d => { let y = +d.slice(0, 4); if (d.slice(5, 7) === '12' && y % 2 === 0) y++; const a = y % 2 ? y : y - 1; return a + '-' + (a + 1); };
  REL.forEach(x => { if (!x[1]) return; const id = (iPid >= 0 && x[iPid]) || x[0], named = new Set((x[4] || []).map(bk));
    const hit = new Set();
    items.forEach(it => { const k = bk(it.bill), s9 = String(it.ses).slice(0, 9); if (thIn.has(k + '|' + s9 + '|' + id) || (named.has(k) && dSes(x[1]) === s9)) { it.rels.push(x); hit.add(k); } });
    /* RELSES-v2 (rp-final, coordinator correction 2026-10-28): a later-session release whose TITLE names the bill goes on the bill's latest earlier session, marked later */
    named.forEach(k => { if (hit.has(k) || !TN(x[3], k)) return; const prev = [...items.values()].filter(it => bk(it.bill) === k && String(it.ses).slice(0, 9) < dSes(x[1])).map(it => it.ses).sort().pop();
      if (prev) { const it = items.get(k + '|' + prev); it.rels.push(x); (it.later = it.later || []).push(x); } }); });
  [...items].forEach(([k, it]) => { if (it.co && !it.rs.length) items.delete(k); });
  const IT = [...items.values()];
  IT.forEach(it => { it.slug = slug(it.bill + ' ' + sesL(it.ses)); it.kinds = new Set((it.m ? it.m[3] : []).map(e => e[1]).filter(k => k !== 'other'));
    it.issues = new Set(it.rs.map(r => r.topic).filter(Boolean).concat(it.rels.map(x => x[5]).filter(Boolean)));
    it.dates = (it.m ? it.m[3].map(e => e[0]) : []).concat(it.rs.map(r => r.date)); });
  const withCov = IT.filter(it => it.rs.length);
  const allTagged = new Set(); D.forEach(r => (r.bills || []).filter(b => RX.test(b)).forEach(b => allTagged.add(bk(b) + '|' + pick(bk(b), r.date))));
  const cnt = f => IT.filter(f).length;
  const niceScale = (v, kind) => { kind = kind || 'count'; if (!(v > 0)) return { max: 0 }; const t = v * 1.06, e0 = Math.floor(Math.log10(t)) - 1;
    for (let e = e0; e <= e0 + 3; e++) for (const m of [1, 2, 2.5, 5]){ const st = m * Math.pow(10, e); if (kind === 'count' && (st < 1 || !Number.isInteger(st))) continue;
      const n = Math.max(2, Math.ceil(t / st - 1e-9)); if (n > 5) continue; return { max: +(n * st).toFixed(6) }; } return { max: t }; };
  const weekOf = iso => { const d = new Date(iso.slice(0, 10) + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() - (d.getUTCDay() + 6) % 7); return d.toISOString().slice(0, 10); };
  const ab418 = items.get('AB418|2023-2024'), a787a = items.get('AB787|2021-2022'), a787b = items.get('AB787|2023-2024');
  if (W === 1400) console.log(`  [info] author-led bill+session items ${IT.length}; with coverage ${withCov.length}; all tagged bill+sessions in D (incl. coauthored) ${allTagged.size}; ` +
    `coauthored with coverage: ${[...allTagged].filter(k => !items.has(k)).join(', ')}; X-session tags dropped by the parser: ${[...new Set(D.flatMap(r => (r.bills || []).filter(b => !RX.test(b))))].join(', ')}`);

  /* ---------- billSlug (BILL-SLUG-v1, for ctx.billLink): the module run in Node against the blocks ---------- */
  if (W === 1400){
    const vm = require('vm'); let mod = null;
    const sb = { AJGTabs: { register: m => { mod = m; } }, document: { addEventListener(){}, querySelectorAll: () => [] }, setTimeout, console };
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../tabs/bills.js'), 'utf8'), sb);
    const cx = { D: D.map(r => Object.assign({}, r, { bills: (r.bills || []).filter(b => RX.test(b)) })), bills: () => info, version: 1, TODAY: '2026-10-27', slug,
      block: n => n === 'bill_timeline' ? h.block('ins_bill_timeline') : n === 'release_pickup' ? h.block('ins_release_pickup') : n === 'releases' ? h.block('tab_releases') : null };
    { const M = mod.page.find('ab-418-2023-24', cx);   /* RELSES-v1: the module's own-session releases = the independent model */
      ok('RELSES-v1: module release lists = independent (every bill + session)', IT.every(it => { const m = mod.page.find(it.slug, cx); return m && m.rels.length === it.rels.length; }), IT.filter(it => { const m = mod.page.find(it.slug, cx); return !m || m.rels.length !== it.rels.length; }).map(it => it.k).slice(0, 8).join());
      ok('RELSES-v2: AB 418 2023-24 lists a release dated after its session only when its title names AB 418, labelled "Later release" (2025-26 passing mentions dropped)', M && M.rels.length > 0 && M.rels.every(r => r.date <= '2024-11-30' ? !r.later : (r.later && TN(r.title, 'AB418'))), M && M.rels.filter(r => r.date > '2024-11-30').map(r => r.key + ':' + !!r.later).join()); }
    const bs = (b, d) => mod.billSlug(b, d ? { date: d } : {}, cx);
    ok('billSlug: AB 787 by date -> its session page', bs('AB 787', '2022-05-01') === 'ab-787-2021-22' && bs('AB 787', '2024-03') === 'ab-787-2023-24' && bs('AB 787', '2022-12-15') === 'ab-787-2023-24', [bs('AB 787', '2022-05-01'), bs('AB 787', '2024-03'), bs('AB 787', '2022-12-15')].join(' '));
    ok('billSlug: no date -> most covered session; AB418 spelling', bs('AB 787') === 'ab-787-2023-24' && bs('AB418') === 'ab-418-2023-24' && bs('ab-418', '2026-10-01') === 'ab-418-2023-24', bs('AB 787'));
    ok('billSlug: unknown -> empty; a coauthored bill tagged in stories has a page', bs('AB 9999') === '' && IT.filter(it => it.co).every(it => bs(it.bill, it.rs[0].date) === it.slug) && IT.some(it => it.co), IT.filter(it => it.co).map(it => it.k).join());
    ok('billSlug: extraordinary session', bs('ABX1-4', '2025-06-01') === 'abx1-4-2025-26-1st-ex-sess', bs('ABX1-4', '2025-06-01'));
    ok('billSlug = list slugs for every item', IT.every(it => mod.page.find(it.slug, cx) && mod.page.find(it.slug, cx).key === it.k));
  }

  /* ---------- list ---------- */
  await h.open();
  ok('renders the Bills list', !!(await h.view()) && (await pg.$(V + ' .tt-tab, ' + V + ' .tt-empty')) !== null);
  ok('total = author-led bill+session items + tagged coauthored ones (independent)', (await h.total()) === IT.length, `${await h.total()} vs ${IT.length}`);
  /* v23 (Sammy, V23Q): Budget Act bills are hidden by default behind "Show Budget Act bills"; the checks below open the full list */
  ok('default list = every non-Budget-Act bill (v23 BUDGET default)', (await h.count()) === IT.filter(it => !it.budget).length, `${await h.count()} vs ${IT.filter(it => !it.budget).length}`);
  ok('one default chip: Budget Act bills left out', JSON.stringify(await h.chips()).includes('Left out')   /* REVIEW4-PAGE-v1 E9: the chip label was reworded ("Hide Budget Act bills" read as two labels) */ && (await h.chips()).length === 1, JSON.stringify(await h.chips()));
  await h.open({ bud: '~' }); ok('Show Budget Act bills = every bill (independent)', (await h.count()) === IT.length, `${await h.count()} vs ${IT.length}`);
  /* the checks below were written for the full list of covered bills: they open it with bud=~ (Budget Act bills shown) and cov=Yes, as an old link that carried the former default still does; the default (Budget Act hidden) view gets its own check next */
  await h.open({ cov: 'Yes' }); ok('default Budget Act filter + cov=Yes = covered non-Budget-Act bills (independent)', (await h.count()) === withCov.filter(it => !it.budget).length, `${await h.count()} vs ${withCov.filter(it => !it.budget).length}`);
  /* (former note:) the checks below were written for the list of covered bills: they open it explicitly (cov=Yes), as an old link that carried the former default still does */
  await h.open({ bud: '~', cov: 'Yes' }); ok('cov=Yes (old default, explicit) = bills with coverage', (await h.count()) === withCov.length && (await h.chips()).some(c => /Has coverage\s*Yes/.test(c)), `${await h.count()} vs ${withCov.length}`);
  await h.open({ bud: '~', cov: 'Yes', q: '787' }); ok('AB 787 is two rows (two sessions)', JSON.stringify((await h.rowKeys()).filter(k => k.startsWith('AB787|')).sort()) === '["AB787|2021-2022","AB787|2023-2024"]', JSON.stringify(await h.rowKeys())); await h.open({ bud: '~', cov: 'Yes' });
  const n787 = new Set(D.filter(r => r.date && (r.bills || []).some(b => bk(b) === 'AB787')).map(r => r.id)).size;   // every countable story tagged AB 787, any session
  ok('AB 787 stories per session = independent (computed from the data; the two sessions together = all countable AB 787 stories)', a787a && a787b && a787a.rs.length > 0 && a787b.rs.length > 0 && a787a.rs.length + a787b.rs.length === n787, a787a && a787b && `${a787a.rs.length}/${a787b.rs.length} vs ${n787}`);
  { const keys = await h.rowKeys(), nCo = IT.filter(it => it.co && it.rs.length).length;   // the desk list shows 100 rows: compare the marks on the rows shown, then the role facet for the whole list
    ok('coauthored bills listed only with stories, marked', !keys.some(k => !items.has(k)) && await pg.evaluate(() => [...document.querySelectorAll('#tbBody .tb-view:not([hidden]) tr[data-ttk]')].filter(tr => /Coauthored/.test(tr.children[0].textContent)).length) === keys.filter(k => items.get(k).co).length || h.phone);
    await h.open({ bud: '~', cov: 'Yes', role: 'Coauthored' }); ok('role facet Coauthored (with stories) = independent', (await h.count()) === nCo && nCo > 0, `${await h.count()} vs ${nCo}`); await h.open({ bud: '~', cov: 'Yes' }); }
  const firstRow = await pg.evaluate(v => { const tr = document.querySelector(v + ' tr[data-ttk]'); return tr ? [...tr.children].map(td => td.textContent.trim()) : null; }, V);
  const top = withCov.slice().sort((a, b) => b.rs.length - a.rs.length)[0];
  ok('top row = most covered bill, columns bill/title/session/status/stories/last', firstRow && firstRow[0] === top.bill && firstRow[2] === sesL(top.ses) && +firstRow[4].replace(/,/g, '') === top.rs.length && firstRow.length === 6, JSON.stringify(firstRow));
  if (!h.phone) ok('column heads', JSON.stringify(await pg.evaluate(v => [...document.querySelectorAll(v + ' .tt-tab thead th')].map(t => t.textContent.trim()), V)) === JSON.stringify(['Bill', 'Title', 'Session', 'Final status', 'Stories', 'Last activity']));
  ok('no horizontal overflow (list)', !(await h.overflowX()));
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, `list_light_${W}.png`) });

  /* search: number, title, case + accent */
  await h.search('ab 787'); ok('search "ab 787" -> both sessions', (await h.count()) === 2, await h.count());
  await h.search('AB787'); ok('search "AB787" (no space) -> 2', (await h.count()) === 2, await h.count());
  const word = 'food';
  const nWord = withCov.filter(it => h.fold(it.title).includes(word) || h.fold(it.bill).includes(word)).length;
  await h.search('FOOD'); const c1 = await h.count(); await h.search('Fóöd'); const c2 = await h.count();
  ok('search title, case- and accent-insensitive (= independent)', c1 === nWord && c2 === nWord && nWord > 0, `${c1} ${c2} vs ${nWord}`);
  await h.search('');

  /* each facet vs independent */
  const sel = async (key, val, want, label) => { await h.open(key === 'cov' ? { bud: '~', [key]: val } : { bud: '~', cov: 'Yes', [key]: val }); ok(`facet ${label} = independent`, (await h.count()) === want, `${await h.count()} vs ${want}`); };
  await sel('ses', '2023–24', cnt(it => it.rs.length && it.ses === '2023-2024'), 'session 2023–24');
  await sel('fin', 'Vetoed', cnt(it => it.rs.length && it.m && /^Vetoed/.test(it.m[4])), 'final status Vetoed');
  await sel('fin', 'Signed into law', cnt(it => it.rs.length && (it.m ? /^Signed into law/.test(it.m[4]) : /^chaptered$/i.test(it.status || ''))), 'final status Signed into law');
  await sel('iss', 'Guns', cnt(it => it.rs.length && it.issues.has('Guns')), 'issue Guns');
  await sel('mst', 'Vetoed', cnt(it => it.rs.length && it.kinds.has('vetoed')), 'milestone Vetoed');
  await sel('mst', 'Committee vote', cnt(it => it.rs.length && it.kinds.has('committee')), 'milestone Committee vote');
  await sel('rel', 'Yes', cnt(it => it.rs.length && it.rels.length), 'has release');
  await sel('cov', 'No', cnt(it => !it.rs.length), 'has coverage = No');
  await sel('cov', '~', IT.length, 'has coverage removed (all)');
  await h.open({ bud: '~', cov: '~' }); await h.customDate('date', '2024-01-01', '2024-12-31');
  ok('facet activity custom 2024 = independent', (await h.count()) === cnt(it => it.dates.some(d => d >= '2024-01-01' && d.slice(0, 10) <= '2024-12-31')), `${await h.count()} vs ${cnt(it => it.dates.some(d => d >= '2024-01-01' && d.slice(0, 10) <= '2024-12-31'))}`);
  /* through the rail UI: pick a value, facet count shown = result */
  await h.open({ bud: '~', cov: 'Yes' });
  const fcV = await h.facetCount('fin', 'Vetoed'); await h.facet('fin', 'Vetoed');
  ok('facet count shown = results after click (Vetoed)', fcV === (await h.count()) && fcV === cnt(it => it.rs.length && it.m && /^Vetoed/.test(it.m[4])), `${fcV} ${await h.count()}`);
  /* combined */
  await h.open({ bud: '~', cov: 'Yes', ses: '2023–24', fin: 'Signed into law', rel: 'Yes' });
  const wantC = cnt(it => it.rs.length && it.ses === '2023-2024' && (it.m ? /^Signed into law/.test(it.m[4]) : /^chaptered$/i.test(it.status || '')) && it.rels.length);   // same status rule as the facet above
  ok('combined session + status + release = independent', (await h.count()) === wantC, `${await h.count()} vs ${wantC}`);
  const nChips = (await h.chips()).length; await h.removeChip(nChips - 1);
  ok('chip removal widens the list', (await h.count()) >= wantC && (await h.chips()).length === nChips - 1);
  /* URL round trip */
  await h.open({ bud: '~', cov: 'Yes', ses: '2021–22', q: 'gun', sort: '-ses' }); const hh = await h.hash(), n0 = await h.count(), k0 = await h.rowKeys();
  await h.reload('#' + hh.slice(1)); ok('URL round trip restores the list', (await h.count()) === n0 && JSON.stringify(await h.rowKeys()) === JSON.stringify(k0), `${hh} ${n0}`);
  /* sort */
  await h.open({ bud: '~', cov: 'Yes' }); await h.sort('bill'); const ks = await h.rowKeys();
  const byNum = withCov.slice().sort((a, b) => { const f = it => { const m = it.bill.match(/^([A-Z]+)\D*?(\d+)$/); return m ? m[1] + ' ' + m[2].padStart(5, '0') + ' ' + it.ses : it.bill + ' ' + it.ses; };   /* same key as the module (ABX1-4 has none) */ return f(a) < f(b) ? -1 : 1; }).map(it => it.k);
  ok('sort by bill number', JSON.stringify(ks.slice(0, 6)) === JSON.stringify(byNum.slice(0, 6)), JSON.stringify(ks.slice(0, 6)));
  await h.open({ bud: '~', cov: 'Yes', sort: '-last' }); const lastK = (await h.rowKeys())[0];
  const mx = it => it.dates.slice().sort().pop(); ok("sort by last activity", !!lastK && mx(items.get(lastK)) === withCov.map(mx).sort().pop(), lastK + " " + mx(items.get(lastK)) + " vs " + withCov.map(mx).sort().pop());
  /* show more (phone step 25) */
  await h.open({ bud: '~', cov: '~' });
  if (h.phone){ const a = (await h.rowKeys()).length; await h.more(); ok('phone: 25 rows then Show more', a === 25 && (await h.rowKeys()).length === 50, `${a}`); }
  else ok('desk: 100 rows then Show all', (await h.rowKeys()).length === 100);
  /* export */
  await h.open();
  const csv = await h.exportCsv(), lines = csv ? csv.text.replace(/^\uFEFF/, '').trim().split(/\r\n/) : [];
  ok('CSV = count + header, with LegInfo history column', lines.length === (await h.count()) + 1 && /LegInfo history/.test(lines[0]) && /^AJG bills /.test(csv.filename), `${lines.length} ${csv && csv.filename}`);
  const tsv = await h.exportCopy(); ok('Copy list (TSV) = count + header', tsv && tsv.trim().split('\n').length === (await h.count()) + 1);
  const cl = await h.exportCopy(0); ok('Copy bill list = one line per bill', cl && cl.trim().split('\n').length === (await h.count()) && /^AB 418 \(2023–24\): /.test(cl), cl && cl.split('\n')[0]);

  /* ---------- bill page ---------- */
  await h.open(); await h.markNav();
  await h.openRow('AB418|2023-2024');
  ok('row click opens #bills/ab-418-2023-24', (await h.hash()).startsWith('#bills/ab-418-2023-24'), await h.hash());
  ok('page title', /^AB 418: /.test(await h.pageTitle() || ''), await h.pageTitle());
  const facts = await h.pageFacts();
  ok('facts: stories / session / final status / releases = independent', +String(facts.Stories).replace(/,/g, '') === ab418.rs.length && facts.Session === '2023–24' && facts['Final status'] === ab418.m[4] && parseInt(facts['Press releases'], 10) === ab418.rels.length - (ab418.later || []).length, JSON.stringify(facts));   // RELSES-v2: the link counts own-session releases   // RELLIST-v1: the count is a "N ›" link
  { const rl = await pg.evaluate(v => { const b = document.querySelector(v + ' .tbe-facts [data-tb-go="releases"][data-tb-p]'); try { return b ? JSON.parse(b.dataset.tbP) : null; } catch(e){ return null; } }, V);
    ok('RELLIST-v1 + RELSES-v1: "Press releases N ›" opens the releases list for this bill and its session dates', rl && rl.bill === 'AB 418' && rl.date === 'c:2022-12-01..2024-11-30', JSON.stringify(rl)); }
  const intro = ab418.m[3].find(e => e[1] === 'introduced');
  ok('facts: introduced date', intro && facts.Introduced.endsWith(intro[0].slice(0, 4)), facts.Introduced);
  const leg = await pg.evaluate(v => { const a = [...document.querySelectorAll(v + ' .tbe-head a')].find(x => /LegInfo/.test(x.textContent)); if (!a) return null; const w = a.closest('.lkw'); return { t: a.textContent.trim(), href: a.href, first: w && w.firstElementChild && w.firstElementChild.className }; }, V);
  ok('"LegInfo history" link, copy icon on its left, AB 418 2023-24 bill_id', leg && /^LegInfo history/.test(leg.t) && leg.first === 'cpb' && /bill_id=202320240AB418$/.test(leg.href), JSON.stringify(leg));
  ok('page list = bill stories (independent)', (await h.pageTotal()) === ab418.rs.length && (await h.pageCount()) === ab418.rs.length, `${await h.pageTotal()} vs ${ab418.rs.length}`);
  const msRows = await pg.evaluate(v => document.querySelectorAll(v + ' details.dt tbody tr').length, V);
  ok('milestone table = block milestones', msRows >= ab418.m[3].length, `${msRows} vs ${ab418.m[3].length}`);
  const relN = await pg.evaluate(v => document.querySelectorAll(v + ' .tbe-head .clip').length, V);
  ok('related releases = independent', relN === ab418.rels.length, `${relN} vs ${ab418.rels.length}`);
  /* RELREVERSE-v1: each release title opens its release page; the official link (copy icon on its left) is on the right */
  const relLinks = await pg.evaluate(v => [...document.querySelectorAll(v + ' .tbe-head .clip')].map(c => ({ pg: !!c.querySelector('[data-tb-go="releases"][data-tb-sub]:not([data-tb-sub=""])'),
    off: [...c.querySelectorAll('a[target="_blank"]')].every(a => a.previousElementSibling && a.previousElementSibling.classList.contains('cpb')) })), V);
  ok('release titles open the release page; official links have the copy icon on the left', relLinks.length && relLinks.every(x => x.pg && x.off), JSON.stringify(relLinks.filter(x => !x.pg || !x.off).slice(0, 3)));
  /* milestone timeline: auto-scaled axis */
  await h.sleep(150);
  const plot = ab418.rs.filter(r => r.prec === 'day' && r.date.length === 10 && r.date >= '2022-12-01'), wk = new Map(); plot.forEach(r => wk.set(weekOf(r.date), (wk.get(weekOf(r.date)) || 0) + 1));
  const wmax = Math.max(...wk.values()), tlTop = await h.chartTop(V + ' .chart[data-blc]');
  ok('timeline y axis = nice max of the busiest week (not fixed)', tlTop === niceScale(wmax).max, `${tlTop} vs ${niceScale(wmax).max} (max ${wmax})`);
  const ruleN = await pg.evaluate(v => document.querySelectorAll(v + ' .chart[data-blc] line[stroke-dasharray]').length + document.querySelectorAll(v + ' .chart[data-blc] circle:not(.rel-dot)').length, V);
  ok('timeline draws the milestones', ruleN === ab418.m[3].filter(e => e[1] !== 'other').length, `${ruleN}`);
  /* framework coverage chart by year vs independent, axis auto-scaled */
  await h.open({ ci: 'year' }, 'ab-418-2023-24');
  const yr = new Map(); ab418.rs.forEach(r => yr.set(r.date.slice(0, 4), (yr.get(r.date.slice(0, 4)) || 0) + 1));
  const tbl = await pg.evaluate(v => [...document.querySelectorAll(v + ' .tbe-ctable tbody tr')].map(tr => [tr.children[0].textContent.trim(), +tr.lastElementChild.textContent.replace(/,/g, '')]).filter(x => x[1]), V);
  ok('coverage chart: stories per year = independent', JSON.stringify(tbl) === JSON.stringify([...yr].sort()), JSON.stringify(tbl) + ' vs ' + JSON.stringify([...yr].sort()));
  const cTop = await h.chartTop(V + ' .tbe-cchart'), yMax = Math.max(...yr.values());
  ok('coverage chart axis scales to the data (not 0–100)', cTop === niceScale(yMax).max && cTop !== 100, `${cTop} vs ${niceScale(yMax).max}`);
  await h.open({ ci: 'year' }, 'ab-787-2021-22'); const small = await h.pageTotal();
  const hid = () => pg.evaluate(v => document.querySelector(v + ' .tbe-cchart').hidden, V);
  ok('AB 787 2021–22 page: story count = independent; no chart exactly when 3 stories or fewer, or all in one year (CHARTRULE-v1)', small === a787a.rs.length && (await hid()) === (small <= 3 || new Set(a787a.rs.map(r => r.date.slice(0, 4))).size <= 1), small);
  const few = withCov.find(it => it.rs.length >= 1 && it.rs.length <= 3);   // a covered bill with 3 stories or fewer: plain line instead of a chart (computed, not named)
  if (few){ await h.open({ ci: 'year' }, few.slug); ok(`${few.bill} ${sesL(few.ses)} page (${few.rs.length} stories): plain line instead of a chart`, (await h.pageTotal()) === few.rs.length && await hid(), few.k); }
  await h.open({}, 'ab-787-2023-24'); ok('AB 787 2023–24 page: story count = independent', (await h.pageTotal()) === a787b.rs.length, await h.pageTotal());
  /* in-page search */
  await h.open({}, 'ab-418-2023-24'); await h.pageSearch('newsom');
  const nNew = await h.pageCount(); ok('in-page search narrows the list', nNew > 0 && nNew < ab418.rs.length, nNew);
  await h.pageSearch('');
  /* week click on the timeline filters the page list to that week */
  const busiest = [...wk].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1))[0];
  const idx = await pg.evaluate(v => document.querySelectorAll(v + ' .chart[data-blc] rect.hit[data-blw]').length, V);
  const weeks0 = weekOf(ab418.rs.filter(r => r.prec === 'day' && r.date >= '2022-12-01').map(r => r.date).concat(ab418.m[3].filter(e => e[1] !== 'other').map(e => e[0])).sort()[0]);
  const wi = Math.round((Date.parse(busiest[0]) - Date.parse(weeks0)) / 6048e5);
  await pg.evaluate(([v, i]) => { const r = document.querySelector(`${v} .chart[data-blc] rect.hit[data-blw="${i}"]`); r.dispatchEvent(new MouseEvent('click', { bubbles: true })); }, [V, wi]); await h.sleep(500);
  ok('timeline week click filters the list to that week (= independent)', (await h.pageCount()) === busiest[1] && /when=c:/.test(await h.hash()), `${await h.pageCount()} vs ${busiest[1]} (${idx} weeks)`);
  ok('still on the bill page after the week click', (await h.hash()).startsWith('#bills/ab-418-2023-24'));
  /* story panel opens from the page list */
  const rid = (await h.pageRowIds())[0]; await pg.click(`${V} .tbe-body tr[data-id="${rid}"] .hl`); await h.sleep(400);
  ok('page row opens the story panel', await pg.evaluate(() => { const s = document.querySelector('#sheet'); return !!s && !s.hidden; }));
  await pg.evaluate(() => { const b = document.querySelector('#sheet [data-close]'); if (b) b.click(); }); await h.sleep(200);
  /* no Clips jumps */
  const txt = await pg.evaluate(v => document.querySelector(v).textContent, V);
  ok('no "See all in Clips" / "Open in Clips" on the bill page', !/in Clips/i.test(txt) && !(await pg.$(V + ' [data-clips]')));
  ok('LegInfo capitalised, no "leginfo history"', /LegInfo history/.test(txt) && !/leginfo history/.test(txt));
  /* URL round trip of the page */
  await h.open({ q: 'ban', ci: 'year' }, 'ab-418-2023-24'); const ph = await h.hash(), pc = await h.pageCount();
  await h.reload('#' + ph.slice(1)); ok('URL round trip restores the bill page', (await h.pageTitle() || '').startsWith('AB 418') && (await h.pageCount()) === pc, `${ph} ${pc} ${await h.pageCount()}`);
  ok('no horizontal overflow (page)', !(await h.overflowX()));
  await h.open({}, 'ab-418-2023-24'); await h.sleep(200);
  await pg.screenshot({ path: path.join(SHOTS, `page_light_${W}.png`) });
  /* back link returns to the list with its filters */
  await h.open({ ses: '2023–24' }); const nb = await h.count(); await h.openRow('AB418|2023-2024'); await h.back();
  ok('back link returns to the filtered list', (await h.hash()).startsWith('#bills') && !(await h.hash()).startsWith('#bills/') && (await h.count()) === nb, await h.hash());
  ok('never left the Bills tab (no #clips)', (await h.leftTab()) === '', await h.leftTab());
  /* a bill with no coverage, deep link on its own */
  const none = IT.find(it => !it.rs.length && it.m); await h.open({}, none.slug);
  ok('bill without coverage: page opens, empty timeline, milestones listed', (await h.pageTitle() || '').startsWith(none.bill) && await h.chartEmpty(V + ' .chart[data-blc]') && (await pg.evaluate(v => document.querySelectorAll(v + ' details.dt tbody tr').length, V)) === none.m[3].length, none.slug);
  await h.open({}, 'nothing-here'); ok('unknown slug -> not-found card', await pg.evaluate(v => /Nothing in Bills/.test(document.querySelector(v).textContent), V));
  /* legacy links */
  await h.hashGo('#bill_timeline?bill=AB%20787&s=2021-2022'); ok('legacy #bill_timeline?bill=AB 787&s=2021-2022 -> its page', (await h.hash()).startsWith('#bills/ab-787-2021-22'), await h.hash());
  await h.hashGo('#insights/bill_timeline?bill=AB418'); ok('legacy #insights/bill_timeline?bill=AB418 -> AB 418 page', (await h.hash()).startsWith('#bills/ab-418-2023-24'), await h.hash());
  await h.hashGo('#press-desk/bills?bill=AB%20787'); ok('legacy bill without session -> most covered session', (await h.hash()).startsWith('#bills/ab-787-2023-24'), await h.hash());
  await h.hashGo('#press-desk/bills?bill=AB%209999&range=session'); ok('legacy unknown bill -> list searched for it', /^#bills\?/.test(await h.hash()) && (await h.params()).q === 'AB 9999', await h.hash());
  await h.hashGo('#press-desk/bills'); ok('legacy #press-desk/bills -> list', (await h.hash()).replace(/\?.*/, '') === '#bills', await h.hash());
  await h.open({}, 'ab-418'); ok('bare bill slug resolves to its covered session', (await h.pageTitle() || '').startsWith('AB 418'));
  /* dark mode screenshots */
  await pg.emulateMedia({ colorScheme: 'dark' });
  await h.open(); await h.sleep(200); await pg.screenshot({ path: path.join(SHOTS, `list_dark_${W}.png`) });
  await h.open({}, 'ab-418-2023-24'); await h.sleep(250); await pg.screenshot({ path: path.join(SHOTS, `page_dark_${W}.png`) });
  await pg.evaluate(v => { const c = document.querySelector(v + ' .chart[data-blc]'); if (c) c.scrollIntoView({ block: 'center' }); }, V); await h.sleep(150);
  await pg.screenshot({ path: path.join(SHOTS, `page_timeline_dark_${W}.png`) });
  await pg.emulateMedia({ colorScheme: 'light' });
  await h.open({}, 'ab-418-2023-24'); await h.sleep(250);
  await pg.evaluate(v => { const c = document.querySelector(v + ' .chart[data-blc]'); if (c) c.scrollIntoView({ block: 'center' }); }, V); await h.sleep(150);
  await pg.screenshot({ path: path.join(SHOTS, `page_timeline_light_${W}.png`) });
  const inl = await pg.evaluate(v => [...document.querySelectorAll(v + ' .tbe-head [style]')].filter(x => !x.closest('.lkw')).length, V);
  ok('no inline style attributes in the module markup', inl === 0, inl);
};
