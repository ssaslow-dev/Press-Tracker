// Reporters tab test (agent-tab-reporters, TABS-v1). Every expected number is recomputed here from srv/blocks/data.json and
// tab_common.json (never read from the page): same author key / canon / kind rules as the tracker, same outlet names as tab-common.
const fs = require('fs'), path = require('path');
module.exports = async (pg, ok, h) => {
  const V = '#tbBody .tb-view[data-tb="reporters"]:not([hidden])';
  const SHOTS = path.resolve(__dirname, '../../../work/tests_out/tabs/shots/reporters'); fs.mkdirSync(SHOTS, { recursive: true });
  const shot = async name => { await pg.evaluate(() => scrollTo(0, 0));
    for (const th of ['light', 'dark']){ await pg.evaluate(t => { document.documentElement.dataset.theme = t; }, th); await h.sleep(120);
      await pg.screenshot({ path: path.join(SHOTS, `${name}_${h.viewport.width}_${th}.png`) }); }
    await pg.evaluate(() => { delete document.documentElement.dataset.theme; }); };
  const D = h.data(), CM = h.block('tab_common'), TODAY = await h.TODAY();
  const cut = m => { const d = new Date(TODAY + 'T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() - m); return d.toISOString().slice(0, 10); };
  const P = { 'Very positive': 2, 'Positive': 1, 'Neutral': 0, 'Negative': -1, 'Very negative': -2 };
  const NEG = r => r.tone === 'Negative' || r.tone === 'Very negative';
  /* ---- independent model ---- */
  const akey = a => { let w = String(a || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/[‘’]/g, "'").toLowerCase().replace(/[.,]/g, ' ').replace(/\s+/g, ' ').trim().split(' ');
    if (w.length > 2) w = [w[0], ...w.slice(1, -1).filter(x => x.length > 1), w[w.length - 1]]; return w.join(' '); };
  const kind = new Map(), forms = new Map();
  D.forEach(r => (r.authors || []).forEach((a, i) => { const k = (r.akinds || [])[i]; if (k) kind.set(akey(a), k); a = String(a || '').trim(); if (!a) return; const m = forms.get(akey(a)) || forms.set(akey(a), new Map()).get(akey(a)); m.set(a, (m.get(a) || 0) + 1); }));
  const canon = new Map(); forms.forEach((m, k) => canon.set(k, [...m.entries()].sort((x, y) => y[1] - x[1] || y[0].length - x[0].length)[0][0]));
  const outletOf = r => CM.a[r.aid] || CM.n[String(r.outlet || '').trim()] || String(r.outlet || '').trim();
  const reach = r => r.reach ? String(r.reach).split(/;\s*/).filter(Boolean) : [];
  /* AFFIL-v1 (v20): a person's outlet on a story = the story's outlet, except an outlet's edited re-run of their story: (a) same
     person, fewer stories at that outlet, 0-7 days after (or 1 day before) a similar-headline story at an outlet with more of
     their stories; (b) a smaller non-wire outlet inside their wire/originating-service tenure (+-14 days) */
  const WIRE = /calmatters|associated press|^ap$|center square|\bupi\b|religion news service|edsource|kff health news|kaiser health news|cronkite news|jewish telegraphic agency|\bjta\b|city news service|bay city news|yonhap|newsis|china news service|armenpress|mynewsla|jewish news syndicate|^jns\b|capital (?:&|and) main|states newsroom|stateline|^cnn wire|cnn newsource/i;
  const STOP = new Set(['the', 'and', 'for', 'with', 'from', 'that', 'this', 'what', 'will', 'into', 'over', 'after', 'about', 'their', 'here', 'have', 'says', 'said', 'more', 'than', 'they', 'are', 'how', 'why', 'new']);
  const hw = t => new Set(h.fold(t).replace(/[^a-z0-9 ]+/g, ' ').split(' ').filter(w => w.length >= 3 && !STOP.has(w)));
  const AFF = new Map(); { const byP = new Map();
    D.forEach(r => { if (!r.date) return; const o = outletOf(r); if (!o) return; const seen = new Set();
      (r.authors || []).forEach(a => { const k = akey(a); if (!k || seen.has(k)) return; seen.add(k); (byP.get(k) || byP.set(k, []).get(k)).push({ r, o, d: Date.parse(String(r.date).slice(0, 10) + 'T12:00:00Z') || 0 }); }); });
    byP.forEach((es, k) => { const n = new Map(); es.forEach(e => n.set(e.o, (n.get(e.o) || 0) + 1)); if (n.size < 2) return;
      es.forEach(e => { let best = null; es.forEach(f => { if (f.o === e.o) return; const g = (e.d - f.d) / 864e5; if (g < -1 || g > 7) return; const nf = n.get(f.o), ne = n.get(e.o);
        if (!(nf > ne || (nf === ne && f.d < e.d))) return; const a = hw(e.r.hl), b = hw(f.r.hl); let x = 0; a.forEach(w => { if (b.has(w)) x++; });
        if (x < 2 || x / Math.max(1, Math.min(a.size, b.size)) < 0.4) return; if (!best || nf > n.get(best.o) || (nf === n.get(best.o) && f.d < best.d)) best = f; });
        if (best) AFF.set(k + '|' + e.r.id, best.o); });
      const ws = [...n.keys()].filter(o => WIRE.test(o)).sort((a, b) => n.get(b) - n.get(a));
      if (ws.length){ const w = ws[0], ds = es.filter(e => e.o === w).map(e => e.d), d0 = Math.min(...ds) - 14 * 864e5, d1 = Math.max(...ds) + 14 * 864e5;
        es.forEach(e => { if (WIRE.test(e.o) || n.get(e.o) >= n.get(w) || e.d < d0 || e.d > d1) return; if (!AFF.has(k + '|' + e.r.id)) AFF.set(k + '|' + e.r.id, w); }); } }); }
  /* v23 REPAFF-v1: the page reads the build's tab-reporters block (one affiliation engine); the rules above stay the fallback */
  const RB = h.block('tab_reporters'); if (RB && RB.aff){ const ids = new Set(String(RB.ids || '').split(',').map(x => 's' + x));
    const aidOf = new Map(D.map(r => [String(r.id), String(r.aid || '')])), judged = sid => ids.has(sid + ':' + aidOf.get(sid));
    [...AFF.keys()].forEach(x => { if (judged(x.split('|')[1])) AFF.delete(x); });   /* stories the build judged: the block's answer only */
    Object.entries(RB.aff).forEach(([sid, m]) => { if (judged(sid)) Object.entries(m).forEach(([k, o]) => AFF.set(k + '|' + sid, o)); }); }
  const RP = (RB && RB.p) || {};
  const affOf = (r, k) => AFF.get(k + '|' + r.id) || outletOf(r);
  const U = [];
  D.forEach(r => { if (!r.date || r.role === 'Op-ed by Gabriel' || r.depth === 'List-only') return;   /* v23: list-only never on this tab */
    const titles = new Set(String(r.atitle || '').split(';').map(akey).filter(Boolean)), seen = new Set(), ppl = [];
    (r.authors || []).forEach(a => { a = String(a || '').trim(); if (!a) return; const k = akey(a); if (!k || k === 'jesse gabriel' || titles.has(k) || seen.has(k)) return; seen.add(k); ppl.push(k); });
    if (ppl.length) U.push({ r, ppl, outlet: outletOf(r), affs: [...new Set(ppl.map(k => affOf(r, k)))], topic: String(r.topic || '').trim() || 'Unassigned', bills: r.bills || [], lang: r.lang || 'English', reach: reach(r), media: r.media || '' }); });
  const KL = { person: 'People', contributor: 'Contributors', staff: 'Staff bylines', board: 'Editorial boards', wire: 'Wires', org: 'Organizations' };
  const group = us => { const m = new Map(); us.forEach(u => u.ppl.forEach(k => { const o = m.get(k) || m.set(k, { key: k, name: canon.get(k), kind: KL[(kind.get(k) || 'person') === 'person' && (RP[k] || {}).c ? 'contributor' : (kind.get(k) || 'person')], rs: [], out: new Map() }).get(k); o.rs.push(u.r); const ao = affOf(u.r, k); o.out.set(ao, (o.out.get(ao) || 0) + 1); }));
    return [...m.values()].map(o => { o.also = []; if (o.kind !== 'Contributors') ((RP[o.key] || {}).also || []).forEach(x => { if (o.out.has(x) && o.out.size > 1){ o.out.delete(x); o.also.push(x); } });   /* v23: Also wrote for */
      const rated = o.rs.filter(r => r.tone in P); o.n = o.rs.length; o.neg = o.rs.filter(NEG).length; o.last = o.rs.reduce((a, r) => r.date > a ? r.date : a, '');
      o.tn = rated.length; o.avg = rated.length ? rated.reduce((a, r) => a + P[r.tone], 0) / rated.length : null;
      o.top = [...o.out.entries()].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1))[0][0]; return o; }); };
  /* TONELABEL-v1: "<Label> <signed value>", label = band of the one-decimal value (|v| < 0.5 Neutral, < 1.5 Positive/Negative) */
  const toneText = o => { if (!o.tn) return ''; const r1 = Math.round(o.avg * 10) / 10, a = Math.abs(r1);
    const lab = ['Very negative', 'Negative', 'Neutral', 'Positive', 'Very positive'][2 + (a < 0.5 ? 0 : a < 1.5 ? 1 : 2) * (r1 < 0 ? -1 : 1)];
    return lab + ' ' + (r1 > 0 ? '+' : r1 < 0 ? '−' : '') + a.toFixed(1); };
  const c24 = cut(24), inDate = (u, c) => u.r.date > c;
  const people = it => it.kind === 'People';
  /* DEFCLEAR-v1: the tab opens with no filters (no 24-month window, every byline type) */
  const calc = (uf, itf) => group(U.filter(u => (!uf || uf(u)))).filter(it => (!itf || itf(it)));
  const ALL = group(U), def = calc();
  const slugify = s => h.fold(s).replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'x';
  const cnt = (arr, f) => { const m = new Map(); arr.forEach(x => [].concat(f(x)).forEach(v => m.set(v, (m.get(v) || 0) + 1))); return [...m.entries()].sort((a, b) => b[1] - a[1]); };
  const tab = () => pg.evaluate(() => { const b = document.querySelector('nav.tabs button[aria-selected="true"]'); return b ? (b.dataset.tb || b.dataset.tab) : null; });

  /* ---- list: default state ---- */
  await h.open();
  ok('renders', !!(await h.view()) && (await tab()) === 'reporters');
  ok('default (no filters): count = independent', (await h.count()) === def.length, `${await h.count()} vs ${def.length}`);
  ok('total = every byline entry, all dates', (await h.total()) === ALL.length, `${await h.total()} vs ${ALL.length}`);
  const ch0 = await h.chips();
  ok('opens with no filters (no chips, no params)', ch0.length === 0 && !Object.keys(await h.params()).length, ch0.join(' | '));
  const top = def.slice().sort((a, b) => b.n - a.n || (b.last < a.last ? -1 : b.last > a.last ? 1 : 0) || a.name.localeCompare(b.name))[0];
  ok('first row = most stories', (await h.rowKeys())[0] === top.key, `${(await h.rowKeys())[0]} vs ${top.key}`);
  const cells = k => pg.evaluate(([v, k]) => { const tr = document.querySelector(`${v} tr[data-ttk="${k}"]`); return tr ? [...tr.children].map(td => td.textContent.trim()) : null; }, [V, k]);
  const c1 = await cells(top.key);
  ok('row: stories, tone average label + value, negative = independent', c1 && c1[2] === String(top.n) && c1[5] === (toneText(top) || '—') && c1[6] === String(top.neg) && c1[1].startsWith(top.top), JSON.stringify(c1) + ` vs ${top.n} ${toneText(top)} ${top.neg} ${top.top}`);
  // two more hand-checked reporters: one with a negative story, one with several outlets
  const negR = def.filter(o => o.neg > 0).sort((a, b) => b.n - a.n)[0], multi = def.filter(o => o.out.size > 2).sort((a, b) => b.n - a.n)[0];
  for (const o of [negR, multi].filter(Boolean)){ const c = await cells(o.key);
    ok(`row ${o.name}: stories / tone / negative / outlets`, c && c[2] === String(o.n) && c[5] === (toneText(o) || '—') && c[6] === String(o.neg) && (o.out.size <= 2 || new RegExp(`\\+${o.out.size - 2} more`).test(c[1])), JSON.stringify(c) + ` vs ${o.n} ${toneText(o)} ${o.neg} outlets ${o.out.size}`); }
  ok('tone average reads "<Label> <signed value>" (minus sign; count in the tooltip)', /^(Very negative|Negative|Neutral|Positive|Very positive) [−+]?\d\.\d$|^—$/.test(c1[5]), c1[5]);
  ok('one-sentence answer', /reporters?( \(plus [^)]*\))? wrote about him\. Most stories: /   /* REVIEW4-PAGE-v1 A10: the count is people; staff bylines / wires / organizations are named separately */.test(await pg.evaluate(v => document.querySelector(v + ' .tt-ans').textContent, V)));
  ok('no inline style attributes in the list rows', await pg.evaluate(v => !document.querySelector(v + ' .tt-list [style]'), V));
  ok('no horizontal overflow (list)', !(await h.overflowX()));
  const step = h.phone ? 25 : 100, shownN = async () => pg.evaluate(v => document.querySelectorAll(v + ' tr[data-ttk]').length, V);
  ok(`row cap ${step} with Show more`, (await shownN()) === Math.min(step, def.length), String(await shownN()));
  if (def.length > step){ await h.more(); ok('Show more', (await shownN()) === (h.phone ? Math.min(2 * step, def.length) : def.length), String(await shownN())); }
  await shot('reporters_list');

  /* ---- search (name + outlet; case and accent) ---- */
  const acc = def.find(o => /[^\x00-\x7f]/.test(o.name) && h.fold(o.name) !== o.name.toLowerCase());
  if (acc){ const plain = h.fold(acc.name).toUpperCase(); await h.search(plain);
    const want = def.filter(o => h.fold(o.name + ' | ' + [...o.out.keys(), ...(o.also || [])].join(' | ')).includes(h.fold(plain))).length;
    ok(`search case + accent ("${plain}" finds ${acc.name})`, (await h.rowKeys()).includes(acc.key) && (await h.count()) === want, `${await h.count()} vs ${want}`); }
  const w2 = top.name.split(' ').slice(-1)[0], ol = top.top.split(' ').filter(x => x.length > 3)[0] || top.top;
  await h.search(`${w2.toLowerCase()} ${ol.toUpperCase()}`);
  const want2 = def.filter(o => { const t = h.fold(o.name + ' | ' + [...o.out.keys(), ...(o.also || [])].join(' | ')); return h.fold(`${w2} ${ol}`).split(' ').every(x => t.includes(x)); }).length;
  ok('search multi-word AND over name + outlet', (await h.count()) === want2 && want2 >= 1, `${await h.count()} vs ${want2}`);
  await h.search(ol); const want3 = def.filter(o => h.fold(o.name + ' | ' + [...o.out.keys(), ...(o.also || [])].join(' | ')).includes(h.fold(ol))).length;
  ok('search by outlet', (await h.count()) === want3, `${await h.count()} vs ${want3}`);
  ok('search in URL', (await h.params()).q === ol);
  await h.search('');

  /* ---- each facet: count shown on the option and the result = independent ---- */
  const U24 = U.filter(u => inDate(u, c24));
  const topOf = f => cnt(U24.filter(u => u.ppl.some(k => (kind.get(k) || 'person') === 'person')), f)[0][0];
  const cases = [
    ['iss', topOf(u => u.topic), u => u.topic],
    ['bill', topOf(u => u.bills), u => u.bills],
    ['outlet', topOf(u => u.affs), u => u.affs],
    ['aud', 'Statewide California', u => u.reach],
    ['med', 'Newspaper', u => u.media],
    ['lng', 'Spanish', u => u.lang]];
  for (const [k, v, f] of cases){
    await h.open(); const want = calc(u => [].concat(f(u)).includes(v)).length;
    const fc = await h.facetCount(k, v);
    await h.facet(k, v);
    ok(`facet ${k}=${v}: option count and result = independent`, fc === want && (await h.count()) === want, `option ${fc}, list ${await h.count()} vs ${want}`);
  }
  // Issue facet changes the row numbers (unit facets filter stories before grouping)
  { await h.open({ iss: cases[0][1] }); const g = calc(u => u.topic === cases[0][1]).sort((a, b) => b.n - a.n)[0]; const c = await cells(g.key);
    ok('issue filter: row counts are over that issue\'s stories', c && c[2] === String(g.n) && c[5] === (toneText(g) || '—'), JSON.stringify(c) + ` vs ${g.n} ${toneText(g)}`); }
  // byline type (item facet, no default): Staff bylines only
  await h.open();
  const staff = group(U).filter(it => it.kind === 'Staff bylines').length;
  ok('byline type: Staff bylines option count = independent', (await h.facetCount('byline', 'Staff bylines')) === staff, `${await h.facetCount('byline', 'Staff bylines')} vs ${staff}`);
  await h.facet('byline', 'Staff bylines');
  ok('byline type: Staff bylines', (await h.count()) === staff, `${await h.count()} vs ${staff}`);
  { const sf = group(U).filter(it => it.kind === 'Staff bylines').sort((a, b) => b.n - a.n)[0]; await h.search(sf.name);
    ok(`staff entries are marked (${sf.name})`, await pg.evaluate(([v, k]) => /Staff byline/.test((document.querySelector(`${v} tr[data-ttk="${k}"] td.tt-name .sub`) || {}).textContent || ''), [V, sf.key])); await h.search(''); }
  // story count, tone, active within (type one / date, item level)
  const one = [['n', '10', o => o.n >= 10], ['n', '2', o => o.n >= 2 && o.n < 5], ['tmix', 'neg', o => o.neg > 0], ['tmix', 'below', o => o.tn && o.avg < 0], ['tmix', 'unrated', o => !o.tn], ['active', '3m', o => o.last > cut(3)]];
  for (const [k, v, f] of one){ await h.open(); const want = calc(null, f).length; const fc = await h.facetCount(k, v); await h.facet(k, v);
    ok(`facet ${k}=${v} = independent`, fc === want && (await h.count()) === want, `option ${fc}, list ${await h.count()} vs ${want}`); }
  // date range: 12 months preset and a custom range
  await h.open(); await h.facet('date', '12m');
  ok('date range 12 months = independent', (await h.count()) === group(U.filter(u => u.r.date > cut(12))).length);
  await h.open(); await h.customDate('date', '2020-01-01', '2020-12-31');
  const cust = group(U.filter(u => u.r.date >= '2020-01-01' && u.r.date.slice(0, 10) <= '2020-12-31'));
  ok('custom date range = independent', (await h.count()) === cust.length, `${await h.count()} vs ${cust.length}`);
  ok('custom range in URL', (await h.params()).date === 'c:2020-01-01..2020-12-31', JSON.stringify(await h.params()));

  /* ---- combined, chips, clear, URL round-trip ---- */
  await h.open(); await h.facet('iss', cases[0][1]); await h.facet('tmix', 'noneg'); await h.search(top.top.split(' ')[0]);
  const comb = calc(u => u.topic === cases[0][1], o => o.neg === 0).filter(o => h.fold(o.name + ' | ' + [...o.out.keys(), ...(o.also || [])].join(' | ')).includes(h.fold(top.top.split(' ')[0])));
  ok('combined (issue + tone + search) = independent', (await h.count()) === comb.length, `${await h.count()} vs ${comb.length}`);
  const hh = await pg.evaluate(() => location.hash);
  await h.reload(hh);
  ok('URL round-trip restores the list', (await h.count()) === comb.length && (await h.chips()).length === ch0.length + 3, `${await h.count()} ${(await h.chips()).join(' | ')}`);
  const chs = await h.chips(), ii = chs.findIndex(c => /^Issue/.test(c));
  await h.removeChip(ii);
  const comb2 = calc(null, o => o.neg === 0).filter(o => h.fold(o.name + ' | ' + [...o.out.keys(), ...(o.also || [])].join(' | ')).includes(h.fold(top.top.split(' ')[0])));
  ok('chip removal', (await h.count()) === comb2.length, `${await h.count()} vs ${comb2.length}`);
  ok('an old link with the former defaults still applies them', await (async () => { await h.open({ date: '24m', byline: 'People' }); const n = group(U.filter(u => inDate(u, c24))).filter(people).length; return (await h.count()) === n && (await h.chips()).length === 2; })());
  await h.clearAll();
  ok('Clear all = every entry, all dates, all kinds', (await h.count()) === ALL.length && (await h.chips()).length === 0, String(await h.count()));

  /* ---- sort ---- */
  await h.open(); await h.more().catch(() => {});
  await h.sort('tone');
  const tv = await pg.evaluate(v => [...document.querySelectorAll(v + ' tr[data-ttk]')].map(tr => tr.children[5].textContent.trim()), V);
  const nums = tv.filter(t => t !== '—').map(t => +t.replace('−', '-').split(' ').pop());
  ok('sort by tone average (most negative first, unrated last)', nums.length > 10 && nums.every((x, i) => !i || nums[i - 1] <= x + 1e-9) && (tv.indexOf('—') === -1 || tv.slice(tv.indexOf('—')).every(t => t === '—')), tv.slice(0, 6).join(','));
  ok('sort in URL', (await h.params()).sort === 'tone');
  await h.sort('name');
  const nm = await pg.evaluate(v => [...document.querySelectorAll(v + ' tr[data-ttk] td.tt-name .linkbtn')].slice(0, 30).map(x => x.textContent.trim().toLowerCase()), V);
  ok('sort by name', nm.every((x, i) => !i || nm[i - 1] <= x), nm.slice(0, 4).join(','));
  await h.sort('last');
  const ks = await h.rowKeys(), lastW = def.slice().sort((a, b) => (b.last > a.last ? 1 : b.last < a.last ? -1 : 0))[0].last;
  ok('sort by last story (newest first)', def.find(o => o.key === ks[0]).last === lastW);

  /* ---- export ---- */
  await h.open();
  const csv = await h.exportCsv(), lines = csv ? csv.text.replace(/^﻿/, '').trim().split(/\r\n/) : [];
  ok('CSV = every listed row + header', lines.length === def.length + 1 && /Reporter/.test(lines[0]) && /Tone average/.test(lines[0]), `${lines.length} vs ${def.length + 1} ${csv && csv.filename}`);
  const names = await h.exportCopy(0), nl = (names || '').split('\n');
  ok('Copy names: "Name (Outlet)" per line, every listed row', nl.length === def.length && nl[0] === `${top.name} (${top.top})`, nl[0] + ' / ' + nl.length);
  const tsv = await h.exportCopy();
  ok('Copy list (TSV) = rows + header', (tsv || '').split('\n').length === def.length + 1);

  /* ---- reporter page ---- */
  await h.open(); await h.markNav();
  await h.openRow(top.key);
  const T = ALL.find(o => o.key === top.key), slug = slugify(T.name);
  ok('click opens #reporters/<slug>', (await h.hash()).startsWith('#reporters/' + slug), await h.hash());
  ok('page title', (await h.pageTitle()) === T.name);
  /* RELREVERSE-v1 independent model (rp-clips): Story ID -> release keys, from ins_release_pickup t[7] (copies) + tab_releases
     "rel" (any type but 'possible'; keyed by release key or Release ID) */
  const RPB = h.block('ins_release_pickup'), TRB = h.block('tab_releases') || {}, iPr = (RPB.cols || []).indexOf('prid'), relKey = new Map(), relBySid = new Map();
  RPB.rel.forEach(t => { relKey.set(t[0], t[0]); const pr = (iPr >= 0 && t[iPr]) || ((TRB.r || {})[t[9] || ''] || [])[6]; if (pr) relKey.set(pr, t[0]); });   // Release ID: the block's prid, else tab_releases r[url][6] (as relIndex; rp-final)
  const addR = (s, k) => { if (s && k) (relBySid.get(s) || relBySid.set(s, new Set()).get(s)).add(k); };
  RPB.rel.forEach(t => (t[7] || []).forEach(s => addR(s, t[0])));
  Object.entries(TRB.rel || {}).forEach(([k, v]) => (v || []).forEach(x => { if (x[1] !== 'possible') addR(x[0], relKey.get(k)); }));
  const relsFor = (rs, ran) => { const s = new Set(); rs.forEach(r => (relBySid.get(r.id) || []).forEach(k => s.add(k))); if (ran) RPB.rel.forEach(t => { if ((t[8] || []).some(q => ran(q))) s.add(t[0]); }); return s.size; };
  const relFactDom = () => pg.evaluate(v => { const d = [...document.querySelectorAll(v + ' .tbe-facts > div')].find(x => x.querySelector('dt').textContent.trim() === 'Press releases');
    return d ? { n: d.querySelectorAll('.tbh-i').length, go: [...d.querySelectorAll('a[data-tb-go="releases"]')].every(a => a.dataset.tbSub && a.getAttribute('href') === '#press-releases/' + encodeURIComponent(a.dataset.tbSub)) } : null; }, V);
  const facts = await h.pageFacts();
  ok('page facts = independent (all of their stories)', facts.Stories === String(T.n) && facts['Negative stories'] === String(T.neg) && facts['Tone average'].startsWith(toneText(T) || 'No rated'), JSON.stringify(facts).slice(0, 300) + ` vs ${T.n} ${T.neg} ${toneText(T)}`);
  { const want = relsFor(T.rs), got = await relFactDom();
    ok('RELREVERSE-v1: "Press releases" fact = releases their stories come from or relate to (independent); each opens its release page', want ? !!got && got.n === want && got.go : !got, JSON.stringify(got) + ' vs ' + want); }
  ok('page list = all their stories', (await h.pageTotal()) === T.n && (await h.pageCount()) === T.n, `${await h.pageTotal()} vs ${T.n}`);
  /* EMBEDROWS-v1 (v19): the Outlets tab's own rows for this reporter's outlets replace the text list */
  const emb = await pg.evaluate(v => { const m = document.querySelector(v + ' .tbe-emb [data-tb-mini="outlets"]'); return m ? { n: +(m.querySelector('.tb-mini-n') || {}).textContent, rows: m.querySelectorAll('tr[data-tbmk]').length } : null; }, V);
  ok('outlets: the Outlets tab rows for their outlets are embedded (count = independent)', emb && emb.n === T.out.size && emb.rows === Math.min(10, T.out.size), JSON.stringify(emb) + ' vs ' + T.out.size);
  const tdt = await pg.evaluate(v => [...document.querySelectorAll(v + ' .tbe-facts dt')].map(x => x.textContent.trim()), V);
  ok('header facts (HEADER-v2): outlets (their own outlets only), stories, last story, top issues, bills, tone, negative', ['Outlets', 'Stories', 'Last story', 'Top issues', 'Bills', 'Tone average', 'Negative stories'].every(x => tdt.includes(x)), tdt.join(','));
  { const ol = await pg.evaluate(v => { const d = [...document.querySelectorAll(v + ' .tbe-facts > div')].find(x => x.querySelector('dt').textContent.trim() === 'Outlets'); return d ? [...d.querySelectorAll('[data-tb-go="outlets"]')].map(b => b.textContent.trim()) : []; }, V);
    ok('header outlets = the reporter\'s own outlets (AFFIL-v1)', ol.length === T.out.size && ol.every(x => T.out.has(x)), ol.join('; ') + ' vs ' + [...T.out.keys()].join('; ')); }
  /* AFFIL-v1 hand check (Sammy): a CalMatters reporter lists CalMatters only; an outlet that only re-ran her story does not list her */
  { const yu = ALL.find(o => o.name === 'Yue Stella Yu'); if (yu) ok('Yue Stella Yu: outlets = CalMatters only', yu.out.size === 1 && [...yu.out.keys()][0] === 'CalMatters', [...yu.out.keys()].join('; ')); }
  { const bd = {}; T.rs.forEach(r => (r.bills || []).forEach(b => { if (!bd[b] || r.date > bd[b]) bd[b] = r.date; }));
    const bl = await pg.evaluate(v => [...document.querySelectorAll(v + ' .tbe-facts [data-bill]')].map(a => [a.dataset.bill, a.dataset.date || '', a.textContent.trim()]), V);
    ok('every bill in the header is a bill link (data-bill + latest story date)', bl.length === Object.keys(bd).length && bl.every(([b, d, t]) => t === b && (d === '' || d === bd[b].slice(0, 10))), JSON.stringify(bl.slice(0, 3)) + ' vs ' + JSON.stringify(bd)); }
  ok('no inline style attributes in the header', await pg.evaluate(v => !document.querySelector(v + ' .tbe-head [style]'), V));
  // titles from the sheet when it has them
  const withT = ALL.filter(o => o.rs.some(r => r.atitle && (r.authors || []).length === 1)).sort((a, b) => b.n - a.n)[0];
  if (withT){ await h.open({}, slugify(withT.name)); const f2 = await h.pageFacts(); const want = [...new Set(withT.rs.filter(r => r.atitle && r.authors.length === 1).map(r => r.atitle.trim()))];
    ok(`title from the sheet (${withT.name})`, !!f2.Title && want.every(t => f2.Title.includes(t)), (f2.Title || 'none') + ' vs ' + want.join('; ')); await h.open({}, slug); }
  // in-page search
  const word = (T.rs.map(r => r.hl).join(' ').match(/[A-Za-z]{6,}/g) || ['Gabriel']).find(w => { const n = T.rs.filter(r => h.fold(r.hl).includes(h.fold(w))).length; return n > 0 && n < T.n; }) || 'Gabriel';
  const hit = T.rs.filter(r => h.fold(r.hl + ' ' + r.outlet).includes(h.fold(word))).length;
  await h.pageSearch(word.toUpperCase());
  ok(`in-page search ("${word}")`, (await h.pageCount()) >= hit && (await h.pageCount()) <= T.n, `${await h.pageCount()} vs >= ${hit}`);
  await h.pageSearch('');
  // the chart: stories per year
  await h.open({ ci: 'year' }, slug);
  const yrs = new Map(); T.rs.forEach(r => yrs.set(r.date.slice(0, 4), (yrs.get(r.date.slice(0, 4)) || 0) + 1));
  const tbl = await pg.evaluate(v => [...document.querySelectorAll(v + ' .tbe-ctable tbody tr')].map(tr => [tr.children[0].textContent, +tr.lastElementChild.textContent]), V);
  ok('page chart: stories per year = independent', T.n <= 3 || JSON.stringify(tbl) === JSON.stringify([...yrs.entries()].sort()), JSON.stringify(tbl) + ' vs ' + JSON.stringify([...yrs.entries()].sort()));
  await shot('reporters_page');
  // a story in the page list opens the story panel; list links filter the page; nothing jumps to Clips
  const ids = await h.pageRowIds();
  if (ids.length){ await pg.click(`${V} .tbe-body tr[data-id="${ids[0]}"] .hl`); await h.sleep(400);
    ok('story panel opens from the page', await pg.evaluate(() => !document.querySelector('#sheet').hidden));
    await pg.evaluate(() => { const b = document.querySelector('#sheet [data-close]'); if (b) b.click(); }); await h.sleep(200); }
  /* LINKRULES-v2 + LINKSCOPE-v1 (v19): in the page list an issue / reach tag opens Clips on that value AND this reporter; the outlet opens its page */
  const tag = await pg.evaluate(v => { const e = document.querySelector(v + ' .tbe-body tr[data-id] .tag[data-tbclip]'); try { return e ? JSON.parse(e.dataset.tbclip) : null; } catch(x){ return null; } }, V);
  ok('list issue tag -> Clips on the issue within this reporter', tag && tag.topic && tag.author && tag.author[0] === T.name, JSON.stringify(tag));
  const olk = await pg.$(V + " .tbe-body tr[data-id] .tlink[data-pub]");
  if (olk && await olk.isVisible()){ await olk.click(); await h.sleep(400); ok('list outlet link opens its Outlets page', (await h.hash()).startsWith('#outlets/'), await h.hash()); await h.open({}, slug); await h.markNav(); }
  await pg.evaluate(v => { const r = document.querySelectorAll(v + ' .tbe-cchart rect.hit'); if (r.length) r[r.length - 1].dispatchEvent(new MouseEvent('click', { bubbles: true })); }, V); await h.sleep(300);
  await pg.click(V + ' .tbe-facts [data-tbstory]'); await h.sleep(300);
  await pg.evaluate(() => { const b = document.querySelector('#sheet [data-close]'); if (b) b.click(); }); await h.sleep(200);
  ok('reporter page never navigates to Clips', (await h.leftTab()) === '' && (await tab()) === 'reporters', await h.leftTab());
  const ph = await pg.evaluate(() => location.hash); await h.reload(ph);
  ok('page URL round-trip', (await h.pageTitle()) === T.name && (await h.hash()).startsWith('#reporters/' + slug), await h.hash());
  ok('no horizontal overflow (page)', !(await h.overflowX()));
  // back link returns to the list with its filters
  await h.open({ iss: cases[0][1] }); const lh = await h.hash(); const k0 = (await h.rowKeys())[0]; await h.openRow(k0); await h.back();
  ok('back link returns to the filtered list', (await h.hash()) === lh, `${await h.hash()} vs ${lh}`);
  ok('unknown reporter page: empty state', await (async () => { await h.open({}, 'no-such-reporter-zz'); return pg.evaluate(v => /Nothing in Reporters/.test(document.querySelector(v).textContent), V); })());

  /* ---- legacy links (old Pitch / Insights) ---- */
  await h.hashGo('#pitch?author=' + encodeURIComponent(top.name.toUpperCase()));
  ok('#pitch?author=<name> opens the reporter page', (await tab()) === 'reporters' && (await h.hash()).startsWith('#reporters/' + slug), await h.hash());
  await h.hashGo('#press-desk/pitch?issue=' + encodeURIComponent(cases[0][1]) + '&win=12');
  ok('#press-desk/pitch?issue=&win=12 -> issue filter, no date default', (await h.params()).iss === cases[0][1] && !(await h.params()).win && (await h.count()) === calc(u => u.topic === cases[0][1]).length, await h.hash());
  await h.hashGo('#insights/reporters?author=Nobody%20Zzq');
  ok('unknown author -> name search', (await h.params()).q === 'Nobody Zzq' && (await h.count()) === 0, await h.hash());
  await h.hashGo('#insights/reporters?author=' + encodeURIComponent(top.name) + '&issue=' + encodeURIComponent(cases[0][1]));
  ok('author + issue -> page filtered to the issue', (await h.hash()).startsWith('#reporters/' + slug) && (await h.pageCount()) === T.rs.filter(r => (String(r.topic || '').trim() || 'Unassigned') === cases[0][1]).length, await h.hash());
  await pg.evaluate(n => { const b = document.createElement('button'); b.dataset.insGo = 'reporters'; b.dataset.insK = 'author'; b.dataset.insV = n; document.body.appendChild(b); b.click(); b.remove(); }, top.name); await h.sleep(450);
  ok('story-panel "Reporter page" entry point -> reporter page', (await h.hash()).startsWith('#reporters/' + slug), await h.hash());
};
