// Press releases tab test (agent-tab-releases). Counts recomputed here from srv/blocks/ins_release_pickup.json, data.json,
// tab_common.json, tab_releases.json and code/release_texts.json (never read from the page).
// data/release_texts.json is served through a route: 'real' = code/release_texts.json, 'mock' = a small {t:{url:text}}
// file, 'missing' = 404 (fallback to title + dek). Screenshots: work/tests_out/tabs/shots/releases/.
const fs = require('fs'), path = require('path');
module.exports = async (pg, ok, h) => {
  const L = path.resolve(__dirname, '../../..'), SHOTS = path.join(L, 'work', 'tests_out', 'tabs', 'shots', 'releases'); fs.mkdirSync(SHOTS, { recursive: true });
  const B = h.block('ins_release_pickup'), C = h.block('tab_common'), T = h.tabBlock(), D = h.data(), F = h.fold;
  // RELRELATED-v1: the evidence rows the page was built with (srv/blocks/tab_releases.json from build_testpage.sh); the harness's
  // own regenerated block may lack "rel" when release_related.json is not found next to it
  const REL = (() => { try { return JSON.parse(fs.readFileSync(path.join(h.blocksDir, 'tab_releases.json'), 'utf8')).rel; } catch(e){ return null; } })() || T.rel || {};
  const TX = JSON.parse(fs.readFileSync(path.join(L, 'code', 'release_texts.json'), 'utf8')).rel;
  const W = h.phone ? 390 : 1400, sleep = h.sleep;
  let mode = 'real', mockUrl = '', fetches = 0;
  await pg.route('**/data/release_texts.json', async r => { fetches++;
    if (mode === 'missing') return r.fulfill({ status: 404, body: 'nope' });
    if (mode === 'mock') return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ v: 1, t: { [mockUrl]: 'Opening words of the mock text. The zzqxmock parade of words continues here for the snippet test and then ends.' } }) });
    return r.fulfill({ status: 200, contentType: 'application/json', body: fs.readFileSync(path.join(L, 'code', 'release_texts.json')) }); });

  /* ---- independent model ---- */
  const ci = n => B.cols.indexOf(n);
  const RU = T.rules || {}, BCW = RU.bc || [-7, -2, -1, 7], TIER = t => (RU.t && RU.t[t] ? RU.t[t][0] : t === 'possible' ? 2 : /^later/.test(t) ? 3 : 1);
  const RANKL = ['nearcopy', 'text', 'quote', 'anchor', 'pre', 'bill', 'topic', 'laterquote', 'later', 'possible'], RNK = t => { const i = RANKL.indexOf(t); return i < 0 ? RANKL.length : i; };
  const canon = (name, aid) => (C.a && C.a[aid]) || (C.n && C.n[name]) || name;
  const addD = (iso, n) => { const d = new Date(iso + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
  const byDate = {}; D.forEach(r => { if (r.prec === 'day' && r.date) (byDate[r.date] = byDate[r.date] || []).push(r); });
  const R = B.rel.map(t => { const url = t[9] || '', x = T.r[url] || [], o = { key: t[0], date: t[1], title: t[3], bills: t[4], topic: t[5], sids: t[7], rows: t[8], url, official: !!t[10] };
    const sc = o.official ? x[3] : ''; o.src = { o: 'Gabriel’s office', c: 'Jewish Caucus', oc: 'Both sites', '': 'Not posted officially' }[sc == null ? (t[2] === 'c' ? 'c' : 'o') : sc];
    o.type = x[0] || ''; o.quoted = x[1] || ''; o.dek = x[2] || ''; o.n = o.rows.length; o.outlets = [...new Set(o.rows.map(q => canon(q[1], q[0])))];
    /* RELRELATED-v1 (2026-10-28): bill coverage +-7 days is context only and has no issue basis; related stories = the tab
       block's evidence rows (rel[<Release ID or key>] = [[Story ID, type, lag]], type 'possible' apart) */
    /* RELUI-v1 (rp-final): bill coverage windows = rules.bc [before from, before to, after from, after to]; tiers = rules.t[type][0]
       (1 related, 2 possibly, 3 later coverage); one row per story (the strongest) */
    o.prid = x[6] || ''; const obg = (((T.thr || {}).x || {})[o.prid || o.key] || {}).bg || []; o.ab = o.bills.filter(b => !obg.includes(b));   /* background bills don't count (rp-final) */
    o.basis = o.ab.length ? 'bill' : ''; o.pre = 0; o.post = 0;
    if (o.date && o.basis) for (let i = BCW[0]; i <= BCW[3]; i++) (byDate[addD(o.date, i)] || []).forEach(r => { if ((r.bills || []).some(b => o.ab.includes(b))) { if (i <= BCW[1]) o.pre++; else if (i >= BCW[2]) o.post++; } });
    o.prid = x[6] || ''; const ids = new Set(D.map(r => r.id)), rr = (REL[o.prid || o.key] || []).filter(q => ids.has(q[0]));
    const best = new Map(); rr.forEach(q => { const b = best.get(q[0]); if (!b || RNK(q[1]) < RNK(b)) best.set(q[0], q[1]); });
    const ofTier = n => [...best].filter(([, t]) => TIER(t) === n).map(([sid]) => sid);
    o.related = ofTier(1); o.possible = ofTier(2); o.later = ofTier(3);
    o.body = (TX[url] || {}).body || ''; return o; });
  const cnt = f => R.filter(f).length;
  const textHit = (o, q, withBody) => { const t = F(o.title + ' ' + o.dek + (withBody ? ' ' + o.body : '')); return F(q).split(' ').filter(Boolean).every(w => t.includes(w)); };
  const answer = () => pg.evaluate(() => { const a = document.querySelector('#tbBody .tb-view[data-tb="releases"]:not([hidden]) .tt-ans'); return a ? a.textContent : ''; });
  const cap = () => pg.evaluate(() => { const a = document.querySelector('#tbBody .tb-view[data-tb="releases"]:not([hidden]) .tt-head'); return a ? [...a.querySelectorAll('.cap')].map(x => x.textContent).join(' ') : '';   /* LISTHEAD-v1: the caption's rest is under "About this list" */ });
  const waitText = async () => { for (let i = 0; i < 40 && /Searching full text/.test(await answer()); i++) await sleep(150); await sleep(200); };

  /* ---- list ---- */
  await h.markNav();
  ok('renders the list', !!(await h.view()) && (await h.total()) === R.length && R.length > 0, `total ${await h.total()}`);
  ok('total = independent (every release in the pickup block)', (await h.total()) === R.length && (await h.count()) === R.length);
  const np = cnt(o => o.n), nc = R.reduce((s, o) => s + o.n, 0);
  // the pickup counts come from the fixture blocks the page was built from (they change with every master): computed here, and cross-checked
  // against the block's other column (sids = the stories each release was picked up in): same releases, copies never fewer than stories
  const nSid = B.rel.filter(t => (t[7] || []).length).length, nStories = B.rel.reduce((s, t) => s + (t[7] || []).length, 0);
  ok('independent counts: releases / picked up / copies agree with the block (rows vs sids)', R.length === B.rel.length && new Set(R.map(o => o.key)).size === R.length && np > 0 && np === nSid && nc >= nStories, `${R.length}/${np}/${nc} sids ${nSid}/${nStories}`);
  const a0 = await answer();
  /* RELUI-v1 (rp-ui, Sammy-approved RELPLAN; test updated by rp-final): "N releases · N run by outlets (N copies) · N with related stories" */
  ok('answer line: run by outlets + copies (RELUI-v1)', a0.includes(`${R.length} releases`) && a0.includes(`${np} run by outlets (${nc} copies)`), a0);
  ok('answer line: releases with related stories (tier 1) = independent (RELUI-v1)', a0.includes(`${cnt(o => o.related.length)} with related stories`), a0 + ` vs ${cnt(o => o.related.length)}`);
  ok('caption: tenure date + not-posted count, no rule paragraphs; no text fetch before a search (RELUI-v1)', /Jewish Caucus releases count from/.test(await cap()) && (await cap()).includes(`Also lists ${cnt(o => !o.official)} releases`) && !/cosine|25-word|≥/.test(await cap()) && fetches === 0, `${await cap()} fetches=${fetches}`);
  const rk = await h.rowKeys(), want = R.slice().sort((a, b) => b.date.localeCompare(a.date))[0];
  ok('default sort: newest first', rk[0] && R.find(o => o.key === rk[0]).date === want.date, rk[0]);
  { const th = await pg.evaluate(() => [...document.querySelectorAll('#tbBody .tt-tab thead th')].map(t => t.textContent.trim()).join('|'));
    ok('columns: release, date, source, ran it, related (RELUI-v1)', th === 'Release|Date|Source|Ran it|Related', th); }
  if (h.phone) ok('phone: 25 rows then Show more', (await h.rowKeys()).length === 25);
  ok('no horizontal overflow (list)', !(await h.overflowX()));

  /* each facet vs independent */
  const fcase = async (key, val, f, label) => { await h.open(); await h.facet(key, val); const n = await h.count(); ok(`facet ${key}=${label || val}: ${n} = independent`, n === cnt(f), `${n} vs ${cnt(f)}`); };
  await fcase('pick', 'yes', o => o.n > 0); await fcase('pick', 'no', o => !o.n);
  await fcase('src', 'Jewish Caucus', o => o.src === 'Jewish Caucus'); await fcase('src', 'Both sites', o => o.src === 'Both sites'); await fcase('src', 'Not posted officially', o => o.src === 'Not posted officially');
  await fcase('type', 'Statement', o => o.type === 'Statement');
  await fcase('iss', 'Guns', o => o.topic === 'Guns');
  const bill = 'AB 1626'; await fcase('bill', bill, o => o.bills.includes(bill));
  await fcase('quoted', 'No', o => o.quoted === 'No');
  await fcase('pick', '4', o => o.n >= 4, '4+'); await fcase('pick', '1', o => o.n === 1); await fcase('pick', '2', o => o.n >= 2 && o.n <= 3, '2–3');   /* RELUI-v1: the "Ran it" facet carries the counts */
  await fcase('rel', 'yes', o => o.related.length > 0, 'Some related'); await fcase('rel', 'no', o => !o.related.length, 'No related');
  await fcase('outlet', 'San Diego Jewish World', o => o.outlets.includes('San Diego Jewish World'));
  await h.open(); await h.customDate('date', '2024-01-01', '2024-12-31');
  ok('facet date custom 2024 = independent', (await h.count()) === cnt(o => o.date >= '2024-01-01' && o.date <= '2024-12-31'), `${await h.count()}`);
  const TODAY = await h.TODAY(), c12 = (() => { const d = new Date(TODAY + 'T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() - 12); return d.toISOString().slice(0, 10); })();
  await h.open({ date: '12m' });
  ok('facet date preset 12m = independent', (await h.count()) === cnt(o => o.date > c12), `${await h.count()} vs ${cnt(o => o.date > c12)}`);
  /* combined + facet counts + chips */
  await h.open(); await h.facet('src', 'Jewish Caucus'); await h.facet('pick', 'yes');
  const comb = cnt(o => o.src === 'Jewish Caucus' && o.n > 0);
  ok('combined src + picked up = independent', (await h.count()) === comb, `${await h.count()} vs ${comb}`);
  await h.openRail(); const fcN = await h.facetCount('src', 'Gabriel’s office'); await h.closeRail();
  ok('facet count (office, with picked up kept) = independent', fcN === cnt(o => o.src === 'Gabriel’s office' && o.n > 0), `${fcN}`);
  ok('two chips', (await h.chips()).length === 2, (await h.chips()).join('|'));
  await h.removeChip(0);
  ok('chip removal: back to picked up only', (await h.count()) === np, `${await h.count()}`);
  await h.clearAll(); ok('clear all', (await h.count()) === R.length);

  /* search: case + accent, full text loads lazily */
  await h.open(); await h.search('ANTISÉMITISM'); await waitText();
  const nAnti = cnt(o => textHit(o, 'antisemitism', true));
  ok('search case + accent insensitive, full text = independent', (await h.count()) === nAnti, `${await h.count()} vs ${nAnti}`);
  ok('full text fetched once', fetches === 1, `fetches=${fetches}`);
  ok('caption after loading says full text', /full text of each release/.test(await cap()), await cap());
  // a word only in one release body (not in any title or dek)
  const tf = new Map(); R.forEach(o => new Set(F(o.body).split(/[^a-z0-9]+/).filter(w => w.length >= 9 && /^[a-z]+$/.test(w))).forEach(w => tf.set(w, (tf.get(w) || []).concat(o))));
  const allTD = F(R.map(o => o.title + ' ' + o.dek).join(' '));
  const [bw, [bo]] = [...tf].filter(([w, os]) => os.length === 1 && !allTD.includes(w)).sort((a, b) => a[0].localeCompare(b[0]))[0];
  await h.search(bw);
  ok(`body-only term "${bw}" finds its release`, (await h.rowKeys()).join() === bo.key, (await h.rowKeys()).join());
  const sn = await pg.evaluate(k => { const r = document.querySelector(`#tbBody [data-ttk="${k}"] .ft-hit`); return r ? { t: r.textContent, m: [...r.querySelectorAll('mark')].map(x => x.textContent) } : null; }, bo.key);
  const words = sn ? sn.t.replace(/^In the release text: “|”$/g, '').replace(/…/g, ' ').split(/\s+/).filter(Boolean) : [];
  ok('snippet shown with the match marked', !!sn && sn.m.some(m => F(m).includes(bw)), JSON.stringify(sn));
  ok('snippet is at most 20 words', words.length > 0 && words.length <= 20, words.length + ': ' + (sn && sn.t));
  await h.search(want.title.split(/\s+/).slice(0, 3).join(' '));
  ok('no snippet on the row whose title matches', !(await pg.evaluate(k => !!document.querySelector(`#tbBody [data-ttk="${k}"] .ft-hit`), want.key)) && (await h.rowKeys()).includes(want.key));

  /* sort + export */
  await h.open(); await h.sort('n');
  const top = await h.rowKeys(), mx = Math.max(...R.map(o => o.n));
  ok('sort by pickups (desc)', R.find(o => o.key === top[0]).n === mx, `${top[0]} max ${mx}`);
  await h.open(); await h.facet('pick', 'yes');
  const csv = await h.exportCsv(), recs = (() => { let n = 0, q = false; const s = csv.text.replace(/^﻿/, ''); for (let i = 0; i < s.length; i++){ const ch = s[i]; if (ch === '"') q = !q; else if (ch === '\n' && !q) n++; } return n + (s.endsWith('\n') ? 0 : 1); })();
  ok('CSV rows = count + header', recs === np + 1, `${recs} vs ${np + 1}`);
  ok('CSV has official link + bill coverage columns', /Official link/.test(csv.text.split('\n')[0]) && /Bill stories the week before/.test(csv.text.split('\n')[0]), csv.text.split('\n')[0]);
  const cp = await h.exportCopy(0);
  ok('Copy titles and links: one line per release', cp && cp.split('\n').length === np, cp && cp.split('\n').length);

  /* URL round-trip */
  await h.open(); await h.facet('src', 'Jewish Caucus'); await h.search('Newsom');
  const hs = await h.hash(), n1 = await h.count(), ch1 = await h.chips();
  await h.reload(hs); await waitText();
  ok('URL round-trip restores list', (await h.count()) === n1 && JSON.stringify(await h.chips()) === JSON.stringify(ch1), `${hs} ${n1} vs ${await h.count()}`);

  /* release page (s00018: AB 1626/1665, 2 copies) */
  const S = R.find(o => o.key === 's00018');
  await h.open(); await h.search(S.title.slice(0, 40)); await waitText();
  ok('nothing navigated to #clips (list: facets, search, sort, export, reload)', (await h.leftTab()) === '', await h.leftTab());
  await h.markNav(); await h.openRow('s00018');
  const ph = await h.hash();
  ok('release page URL #press-releases/<Release ID> (RELCOPIES-v1; the old date-title slug redirects)', S.prid ? ph.split('?')[0] === '#press-releases/' + S.prid : /^#press-releases\/2026-10-02-amid-youth-mental-health-crisis/.test(ph), ph);
  ok('page title', (await h.pageTitle()) === S.title);
  const facts = await h.pageFacts();
  const kick = await pg.evaluate(() => (document.querySelector('#tbBody .tb-view:not([hidden]) .tbe-head') || {}).textContent || '');
  /* RELUI-v1: type + source in the kicker; facts grouped Who / What / Coverage; "Ran it" = copies */
  ok('type + source in the kicker; facts: quoted, ran it (RELUI-v1)', kick.includes(S.src) && kick.includes(S.type || 'Press release') && facts['Gabriel quoted'] === S.quoted && (facts['Ran it'] || '').startsWith(S.n ? `${S.n} cop` : '0'), JSON.stringify(facts));
  ok('facts: related stories = independent (RELRELATED-v3 tier 1)', (facts['Related stories'] || '').startsWith(String(S.related.length)), facts['Related stories'] + ` vs ${S.related.length}`);
  /* rp-final (coordinator review): plain words "N stories on <bill> that week" (after window); before / not linked in the ⓘ */
  { const bcb = S.ab.length === 1 ? S.ab[0] : 'these bills', want = (S.post ? `${S.post} ${S.post === 1 ? 'story' : 'stories'}` : 'No stories') + ` on ${bcb} that week`;
    const ip = await pg.evaluate(() => { const d = [...document.querySelectorAll('#tbBody .tbe-facts > div')].find(x => x.querySelector('dt').textContent.trim() === 'Bill coverage'); const b = d && d.querySelector('.tb-i'); return b ? b.dataset.tbi : ''; });
    ok('facts: bill coverage in plain words = independent, before count in the ⓘ', (facts['Bill coverage'] || '').startsWith(want) && ip.startsWith(`${S.pre} ${S.pre === 1 ? 'story' : 'stories'} the week before`), (facts['Bill coverage'] || '') + ` vs ${want} | ${ip}`); }
  const hdr = await pg.evaluate(u => { const a = document.querySelector(`#tbBody .tbe-head a[href="${u}"]`); if (!a) return null; const w = a.closest('.lkw'); return { cpFirst: !!(w && w.firstElementChild && w.firstElementChild.classList.contains('cpb')), txt: a.textContent }; }, S.url);
  ok('official link with copy icon on its left', hdr && hdr.cpFirst, JSON.stringify(hdr));
  const secs = await pg.evaluate(() => [...document.querySelectorAll('#tbBody .tb-view:not([hidden]) .tbe .tb-us')].map(s => ({ h: (s.querySelector('h3') || {}).textContent || '', n: s.querySelectorAll('.clip').length, cp: s.querySelectorAll('.clip .cpb').length })));
  const cs = secs.find(s => /^Ran the release/.test(s.h));
  ok('"Ran the release" section lists each copy with links (RELUI-v1)', cs && cs.n === S.n && cs.cp >= S.n, JSON.stringify(secs));
  ok('no bill-coverage story section (counts only, RELRELATED-v1)', !secs.some(s => /before vs after/.test(s.h)), JSON.stringify(secs));
  const rsh = await pg.evaluate(() => (document.querySelector('#tbBody .tb-view:not([hidden]) .tbe .rl-relh h3') || {}).textContent || '');
  ok('"Related stories · N" heading = independent', /^Related stories/.test(rsh) && rsh.includes(String(S.related.length)), rsh);
  const relBadge = await pg.evaluate(() => document.querySelectorAll('#tbBody .tb-view:not([hidden]) .tbe-body .badge.rel').length);
  ok('release-page story rows carry the evidence tag, not the Clips press-release badge (rp-final)', relBadge === 0, relBadge);
  const sess = D.filter(r => S.related.includes(r.id));
  if (sess.length) ok('page list = its related stories (independent)', (await h.pageTotal()) === sess.length, `${await h.pageTotal()} vs ${sess.length}`);
  const yrs = {}; sess.forEach(r => yrs[r.date.slice(0, 4)] = (yrs[r.date.slice(0, 4)] || 0) + 1);
  ok('no chart on a release page (RELUI-v1)', !(await pg.evaluate(() => !!document.querySelector('#tbBody .tb-view:not([hidden]) .tbe-cchart svg'))));
  if (false){   /* RELUI-v1: the release page has no chart (chart: false); the v19 per-year chart checks are retired */
    await h.open({ ci: 'year' }, ph.slice('#press-releases/'.length).split('?')[0]);
    const tbl = await pg.evaluate(() => [...document.querySelectorAll('#tbBody .tb-view:not([hidden]) .tbe-ctable tbody tr')].map(tr => [tr.children[0].textContent, +tr.lastElementChild.textContent]));
    const want2 = Object.entries(yrs).sort();
    if (want2.length > 1) ok('page chart: stories per year = independent', JSON.stringify(tbl) === JSON.stringify(want2), JSON.stringify(tbl) + ' vs ' + JSON.stringify(want2));
    else {   /* CHARTRULE-v1 (v19): every story in one year -> one sentence instead of a one-bar chart */
      const note = await pg.evaluate(() => { const n = document.querySelector('#tbBody .tb-view:not([hidden]) .tbe-cnote'); return n && !n.hidden ? n.textContent : ''; });
      ok('page chart by year: one year only -> a sentence, no one-bar chart (CHARTRULE-v1)', new RegExp('All ' + want2[0][1] + ' stor(y|ies) here ran in ' + want2[0][0]).test(note) && !tbl.length, note + ' | ' + JSON.stringify(tbl)); }
    await h.markNav();
  }
  if (sess.length){ const w = F(sess[0].hl).split(' ').filter(x => x.length > 4)[0] || F(sess[0].hl).split(' ')[0]; await h.pageSearch(w);
    const exp = sess.filter(r => F(r.hl + ' ' + (r._s || '')).includes(w)).length;
    const pc2 = await h.pageCount(); ok('in-page search narrows the list', pc2 >= 1 && pc2 <= sess.length, `${w}: ${pc2} (headline-only ${exp})`); await h.pageSearch(''); }
  const POS = '#tbBody .tb-view:not([hidden]) details.rl-det';   /* RELUI-v1: "Possibly related" = a collapsed details card */
  if (S.possible.length){ await pg.evaluate(P => { const d = [...document.querySelectorAll(P)].find(x => /^Possibly related/.test(x.querySelector('summary').textContent)); if (d) { d.open = true; d.dataset.pos = '1'; } }, POS); await pg.click(POS + '[data-pos] tbody.tbe-xbody tr[data-id] td.h .hl');   /* RELLATER-v1: same rows as Related stories */ await sleep(500);
    ok('possibly related story opens the story panel', await pg.evaluate(() => { const s = document.querySelector('#sheet'); return !!s && !s.hidden; }));
    await pg.evaluate(() => { const b = document.querySelector('#sheet [data-close]'); if (b) b.click(); }); await sleep(250); }
  const bl = await pg.evaluate(() => [...document.querySelectorAll('#tbBody .tbe-facts [data-bill]')].map(a => [a.dataset.bill, a.dataset.date]));
  { const tx = ((T.thr || {}).x || {})[S.prid || S.key] || {}, bg = tx.bg || [], wantB = S.bills.filter(b => !bg.includes(b)).concat(tx.m ? [tx.m[0]] : []).map(b => [b, S.date]);   /* RELTHREAD: background bills are text; the milestone carries its bill chip */
    ok('bill numbers render as bill links (data-bill + release date for the Bills helper)', JSON.stringify(bl.slice().sort()) === JSON.stringify(wantB.slice().sort()), JSON.stringify(bl) + ' vs ' + JSON.stringify(wantB)); }
  const fl = await pg.evaluate(P => { const d = [...document.querySelectorAll(P)].find(x => /^Possibly related/.test(x.querySelector('summary').textContent)); return d ? [d.querySelectorAll('.tbe-xbody tr[data-id]').length, d.querySelectorAll('.tbe-xbody tr[data-id] .ol [data-pub]').length, d.querySelectorAll('.tbe-xbody a[href]').length] : [0, 0, 0]; }, POS);
  ok('possibly related stories: one row per story (Related stories row format), outlet buttons, no links', fl[0] === S.possible.length && fl[1] === fl[0] && fl[2] === 0, JSON.stringify(fl));
  { const lc = await pg.evaluate(() => { const c = [...document.querySelectorAll('#tbBody .tb-view:not([hidden]) .rl-sec')].find(x => /^Later coverage/.test((x.querySelector('h3') || {}).textContent || '')); return c ? [c.querySelectorAll('.tbe-xbody tr[data-id]').length, c.querySelectorAll('a[href]').length, c.querySelectorAll('.tbe-xbody .rl-tag').length] : null; });
    ok('later coverage: Related stories rows with the evidence tag, no links (RELLATER-v1)', !S.later.length || (lc && lc[0] === S.later.length && lc[1] === 0 && lc[2] === lc[0]), JSON.stringify([lc, S.later.length])); }
  ok('no horizontal overflow (page)', !(await h.overflowX()));
  await shots('page');
  ok('nothing navigated to #clips (release page)', (await h.leftTab()) === '', await h.leftTab());
  await h.reload(ph);
  ok('deep link reload restores the page', (await h.pageTitle()) === S.title, await h.pageTitle());
  await h.back();
  ok('back link returns to the list', /^#press-releases(\?|$)/.test(await h.hash()) && !!(await pg.$('#tbBody .tt')), await h.hash());
  // a release with no pickup and no official posting
  const none = R.find(o => !o.n && o.official);
  await h.hashGo('#press-releases'); await h.search(none.title); await waitText(); await h.openRow(none.key);
  { const f0 = await h.pageFacts(), rr0 = await pg.evaluate(() => [...document.querySelectorAll('#tbBody .tb-view:not([hidden]) .tbe h3')].some(x => /^Ran the release/.test(x.textContent)));
    ok('no-pickup release page: "Ran it" 0 and no "Ran the release" section (RELUI-v1)', f0['Ran it'] === '0' && !rr0, JSON.stringify(f0)); }
  const np2 = R.find(o => !o.official);
  await h.hashGo('#press-releases'); await h.facet('src', 'Not posted officially'); await h.openRow(np2.key);
  ok('not-posted release page says so in the kicker (RELUI-v1)', await pg.evaluate(() => /Not posted officially/.test(document.querySelector('#tbBody .tbe-head').textContent)));

  /* every copy row: a working article link (copy icon left), the outlet linked to its outlet page, the date */
  const picked = R.filter(o => o.n), sample = h.phone ? picked.slice(0, 6) : picked; let copyBad = [], copyN = 0;
  for (const o of sample){
    await h.hashGo('#press-releases/' + await pageSlug(o));
    const cs2 = await pg.evaluate(() => [...document.querySelectorAll('#tbBody .tb-view:not([hidden]) .tbe [data-relcopy]')].map(c => ({ aid: c.dataset.relcopy,
      links: [...c.querySelectorAll('.lkw')].map(w => ({ cp: !!(w.firstElementChild && w.firstElementChild.classList.contains('cpb')), href: (w.querySelector('a[href]') || {}).href || '' })),
      saved: !!c.querySelector('[data-relsaved]'), outlet: (c.querySelector('[data-tb-go="outlets"]') || {}).dataset ? { tab: c.querySelector('[data-tb-go="outlets"]').dataset.tbGo, sub: c.querySelector('[data-tb-go="outlets"]').dataset.tbSub, name: c.querySelector('[data-tb-go="outlets"]').textContent } : null,
      cm: (c.querySelector('.cm') || {}).textContent || '' })));
    copyN += cs2.length;
    if (cs2.length !== o.n) copyBad.push(o.key + ' count ' + cs2.length + '/' + o.n);
    cs2.forEach(c => { const row = o.rows.find(q => q[0] === c.aid), name = row && canon(row[1], row[0]);
      const good = c.saved || c.links.some(l => /^https?:\/\/[^\s]+\.[a-z]{2,}/i.test(l.href) && l.cp);
      if (!good) copyBad.push(c.aid + ' no link');
      if (c.links.some(l => /docref=image/i.test(l.href))) copyBad.push(c.aid + ' print-page link');
      if (c.links.some(l => /infoweb\.newsbank\.com/i.test(l.href))) copyBad.push(c.aid + ' NewsBank not via CSL');
      if (!c.outlet || c.outlet.name !== name || c.outlet.sub !== h.fold(name).replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')) copyBad.push(c.aid + ' outlet ' + JSON.stringify(c.outlet));
      if (row && row[2] && !/20\d\d/.test(c.cm)) copyBad.push(c.aid + ' no date'); });
  }
  ok(`every copy row has a working article link, outlet page link and date (${copyN} copies of ${sample.length} releases)`, !copyBad.length && copyN === sample.reduce((a, o) => a + o.n, 0), copyBad.slice(0, 8).join('; '));

  /* legacy links */
  await h.hashGo('#insights/release_pickup?id=s00018');
  ok('legacy #insights/release_pickup?id=<story> opens the release page', (await h.hash()).startsWith(ph.split('?')[0]), await h.hash());
  const off = R.find(o => /^off/.test(o.key)); await h.hashGo('#press-desk/releases?id=' + off.key);
  ok('legacy id=offNNN opens that release', (await h.pageTitle()) === off.title, await h.pageTitle());
  await h.hashGo('#press-desk/releases?year=2024');
  ok('legacy year=2024 -> date filter', (await h.count()) === cnt(o => o.date.startsWith('2024')), `${await h.count()}`);
  await h.hashGo('#release_pickup?pick=no&topic=Guns');
  ok('legacy pick=no&topic=Guns', (await h.count()) === cnt(o => !o.n && o.topic === 'Guns'), `${await h.count()}`);

  /* list screenshots (light + dark), then the fallbacks */
  await h.open(); await shots('list');

  mode = 'missing'; await h.reload('#press-releases'); fetches = 0;
  await h.search(bw); await waitText();
  ok('missing text file: body-only term finds nothing', (await h.count()) === 0 && fetches === 1, `${await h.count()} fetches=${fetches}`);
  ok('missing text file: answer says so', /could not be loaded|Nothing|No releases/.test((await answer()) + (await pg.evaluate(() => document.querySelector('#tbBody .tt-list').textContent))));
  await h.search(S.title.split(/\s+/).slice(0, 4).join(' '));
  ok('missing text file: title search still works', (await h.count()) === cnt(o => textHit(o, S.title.split(/\s+/).slice(0, 4).join(' '), false)), `${await h.count()}`);
  ok('missing text file: answer says titles and deks only (RELUI-v1: the caption is static)', /could not be loaded; searched titles and deks/.test(await answer()), await answer());

  mode = 'mock'; mockUrl = S.url; await h.reload('#press-releases'); fetches = 0;
  await h.search('ZZQXMOCK'); await waitText();
  ok('mocked {t:{url:text}} file: body-only term matches', (await h.rowKeys()).join() === S.key, (await h.rowKeys()).join());
  const ms = await pg.evaluate(() => { const r = document.querySelector('#tbBody .ft-hit'); return r ? r.innerHTML : ''; });
  ok('mocked file: snippet with <mark>', /<mark>zzqxmock<\/mark>/.test(ms) && ms.replace(/<[^>]+>/g, '').replace(/^In the release text: “|”$/g, '').split(/\s+/).filter(Boolean).length <= 20, ms);
  ok('nothing navigated to #clips (page chart, legacy links, fallbacks)', (await h.leftTab()) === '', await h.leftTab());

  async function pageSlug(o){ // the slug the list opens (independent of the page): via the legacy id link
    await h.hashGo('#insights/release_pickup?id=' + o.key); const x = await h.hash(); return x.slice('#press-releases/'.length).split('?')[0]; }
  async function shots(name){
    for (const sc of ['light', 'dark']){ await pg.emulateMedia({ colorScheme: sc }); await pg.evaluate(() => scrollTo(0, 0)); await sleep(250);
      await pg.screenshot({ path: path.join(SHOTS, `releases_${name}_${sc}_${W}.png`), fullPage: false }); }
    await pg.emulateMedia({ colorScheme: 'light' });
  }
};
