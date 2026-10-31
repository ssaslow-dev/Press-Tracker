/* Story travel tab (TABS-v1, agent-tab-travel, 2026-10-27). Replaces Press desk › Story travel (build/insights/story_travel.js).
   List: every story that ran in at least one OTHER outlet (canonical names via ctx.outlet; copies in the original's own
   outlet don't count; same-headline/same-day duplicates left out as before, block ins-story_travel "x" dup:), in Clips form
   with the number of outlets it reached. Search headline / outlet / author; facets original date, original outlet, issue,
   reprint count, outlets it reached, language.
   Story page (#story-travel/<Story ID>-<words>): summary line, spread curve (cumulative outlets by day since the original,
   shared AXIS-v1 scale), pickup ladder (one row per outlet in the order it ran, copies grouped), where it ran (CA county map
   when most counties are known + ctx.usMap). The old +1…+7 dot grid and the Top sources table are gone.
   Data: ctx.D reps; tab-travel block (travel_data.py: Medium + Language of each reprint row from the sheet); ins-story_travel
   (Reach per reprint outlet, inferred list, dup list); tab-common (canonical names, out-of-state outlets). */
(function(){ "use strict";
  const ISO = /^\d{4}-\d{2}-\d{2}$/;
  /* rough centroids, only to rank "furthest" (CA counties; US states as "Name:lat:lon") */
  const CA = {}; ('Alameda:37.65:-121.92|Alpine:38.6:-119.82|Amador:38.45:-120.65|Butte:39.67:-121.6|Calaveras:38.2:-120.55|Colusa:39.18:-122.24|Contra Costa:37.92:-121.95|Del Norte:41.74:-123.9|El Dorado:38.78:-120.52|Fresno:36.76:-119.65|Glenn:39.6:-122.39|Humboldt:40.7:-123.87|Imperial:33.04:-115.36|Inyo:36.51:-117.41|Kern:35.34:-118.73|Kings:36.07:-119.82|Lake:39.1:-122.75|Lassen:40.67:-120.59|Los Angeles:34.32:-118.22|Madera:37.22:-119.77|Marin:38.05:-122.75|Mariposa:37.58:-119.91|Mendocino:39.44:-123.39|Merced:37.19:-120.72|Modoc:41.59:-120.72|Mono:37.94:-118.89|Monterey:36.22:-121.31|Napa:38.51:-122.33|Nevada:39.3:-120.77|Orange:33.7:-117.76|Placer:39.06:-120.72|Plumas:40:-120.84|Riverside:33.74:-115.99|Sacramento:38.45:-121.34|San Benito:36.61:-121.08|San Bernardino:34.84:-116.18|San Diego:33.03:-116.74|San Francisco:37.76:-122.44|San Joaquin:37.93:-121.27|San Luis Obispo:35.38:-120.4|San Mateo:37.43:-122.33|Santa Barbara:34.67:-120.02|Santa Clara:37.23:-121.7|Santa Cruz:37.06:-122|Shasta:40.76:-122.04|Sierra:39.58:-120.52|Siskiyou:41.59:-122.54|Solano:38.27:-121.94|Sonoma:38.53:-122.92|Stanislaus:37.56:-121|Sutter:39.03:-121.7|Tehama:40.13:-122.23|Trinity:40.65:-123.11|Tulare:36.22:-118.8|Tuolumne:38.03:-119.95|Ventura:34.45:-119.08|Yolo:38.68:-121.9|Yuba:39.27:-121.35')
    .split('|').forEach(s => { const a = s.split(':'); CA[a[0]] = [+a[1], +a[2]]; });
  const ST = {}; ('AL:Alabama:32.8:-86.8|AK:Alaska:64:-152|AZ:Arizona:34.3:-111.7|AR:Arkansas:34.9:-92.4|CA:California:37.2:-119.5|CO:Colorado:39:-105.5|CT:Connecticut:41.6:-72.7|DE:Delaware:39:-75.5|DC:Washington, D.C.:38.9:-77|FL:Florida:28.6:-82.4|GA:Georgia:32.7:-83.4|HI:Hawaii:20.8:-156.3|ID:Idaho:44.4:-114.6|IL:Illinois:40:-89.2|IN:Indiana:39.9:-86.3|IA:Iowa:42.1:-93.5|KS:Kansas:38.5:-98.4|KY:Kentucky:37.5:-85.3|LA:Louisiana:31.1:-92|ME:Maine:45.4:-69.2|MD:Maryland:39:-76.8|MA:Massachusetts:42.3:-71.8|MI:Michigan:44.3:-85.4|MN:Minnesota:46.3:-94.3|MS:Mississippi:32.7:-89.7|MO:Missouri:38.4:-92.5|MT:Montana:47:-109.6|NE:Nebraska:41.5:-99.8|NV:Nevada:39.3:-116.6|NH:New Hampshire:43.7:-71.6|NJ:New Jersey:40.2:-74.7|NM:New Mexico:34.4:-106.1|NY:New York:42.9:-75.5|NC:North Carolina:35.6:-79.4|ND:North Dakota:47.5:-100.5|OH:Ohio:40.3:-82.8|OK:Oklahoma:35.6:-97.5|OR:Oregon:43.9:-120.6|PA:Pennsylvania:40.9:-77.8|RI:Rhode Island:41.7:-71.5|SC:South Carolina:33.9:-80.9|SD:South Dakota:44.4:-100.2|TN:Tennessee:35.9:-86.4|TX:Texas:31.5:-99.3|UT:Utah:39.3:-111.7|VT:Vermont:44.1:-72.7|VA:Virginia:37.5:-78.8|WA:Washington:47.4:-120.5|WV:West Virginia:38.6:-80.6|WI:Wisconsin:44.6:-89.9|WY:Wyoming:43:-107.5|PR:Puerto Rico:18.2:-66.5')
    .split('|').forEach(s => { const a = s.split(':'); ST[a[0]] = [a[1], +a[2], +a[3]]; });
  const SAC = [38.58, -121.49];
  const km = (a, b) => { const r = Math.PI / 180, x = Math.sin((b[0] - a[0]) * r / 2), y = Math.sin((b[1] - a[1]) * r / 2);
    return 12742 * Math.asin(Math.sqrt(x * x + Math.cos(a[0] * r) * Math.cos(b[0] * r) * y * y)); };
  let MEMO = null, CTX = null;

  /* ---- model: one entry per story with its pickups grouped by canonical outlet, in the order they ran ---- */
  function model(ctx){
    if (MEMO && MEMO.v === ctx.version) return MEMO;
    const tb = ctx.block('travel') || { v: [''], r: {} }, ins = ctx.block('story_travel') || {}, com = ctx.block('common') || {};
    const V = tb.v || [''], TR = tb.r || {}, IO = ins.o || {}, IA = ins.a || {}, INF = new Set(ins.inf || []), X = ins.x || {}, CO = com.o || {};
    const by = new Map();   // canonical outlet -> {reach, media, lang} counts over its originals (fallbacks)
    const bump = (m, k) => { if (k) m.set(k, (m.get(k) || 0) + 1); };
    const top = m => m && m.size ? [...m].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0][0] : '';
    ctx.D.forEach(r => { const o = ctx.outlet(r.outlet, r.aid), e = by.get(o) || by.set(o, { reach: new Map(), media: new Map(), lang: new Map() }).get(o);
      bump(e.reach, ctx.reachTags(r)[0]); bump(e.media, r.media); bump(e.lang, ctx.langOf(r)); });
    const fb = (o, k) => top((by.get(o) || {})[k]);
    function rep(p){
      const name = ctx.outlet(p.outlet, p.aid), t = TR[p.aid] || [0, 0], st = String(p.state || '').trim() || ((CO[name] || [])[0] || '');
      const reach = String(IA[p.aid] || IO[p.outlet] || (CO[name] || [])[1] || fb(name, 'reach') || '').split(/;\s*/)[0];
      return { p, name, date: ISO.test(p.date || '') ? p.date : '', media: V[t[0]] || fb(name, 'media'), lang: V[t[1]] || (TR[p.aid] ? 'English' : (fb(name, 'lang') || 'English')),
        reach, inf: !IA[p.aid] && INF.has(p.outlet), county: String(p.county || '').trim(), state: st }; }
    function entry(r){
      const own = ctx.outlet(r.outlet, r.aid), ownH = ctx.house ? ctx.house(r.outlet, r.aid) : own, g = new Map(), ownC = [];
      /* REPCOUNT-v1: copies in the original's own house (same paper, another edition) are not pickups */
      (r.reps || []).forEach(p => { if (!p || !p.outlet) return; const x = rep(p); if (x.name === own || (ctx.house ? ctx.house(p.outlet, p.aid) : x.name) === ownH){ ownC.push(x); return; }
        (g.get(x.name) || g.set(x.name, []).get(x.name)).push(x); });
      const d0 = ISO.test(r.date || '') ? r.date : '';
      const ps = [...g].map(([name, cs]) => { cs.sort((a, b) => (a.date || '9999').localeCompare(b.date || '9999') || String(a.p.aid).localeCompare(String(b.p.aid)));
        const f = cs[0]; return Object.assign({}, f, { name, copies: cs, d: d0 && f.date ? ctx.daysBetween(d0, f.date) : null }); });
      ps.sort((a, b) => (a.d == null) - (b.d == null) || (a.d - b.d) || a.name.localeCompare(b.name));
      const dd = ps.filter(p => p.d != null).map(p => p.d);
      const langs = new Map(); ps.forEach(p => { if (p.lang && p.lang !== 'English') langs.set(p.lang, (langs.get(p.lang) || 0) + 1); });
      const it = { key: r.id, r, out: own, ps, n: ps.length, copies: ps.reduce((a, p) => a + p.copies.length, 0), ownC,
        span: dd.length ? Math.max(...dd) : null, early: dd.filter(d => d < 0).length, langs, lang0: ctx.langOf(r) };
      it.far = furthest(it, CO);
      return it; }
    const all = ctx.D.filter(r => r && String(r.hl || '').trim()).map(entry);
    const ids = new Map(all.map(it => [it.key, it]));
    const list = all.filter(it => it.n > 0 && !/^dup:/.test(X[it.key] || ''));
    MEMO = { v: ctx.version, ids, list, entry }; return MEMO;
  }
  /* where an outlet is: CA county, US state, or a place outside the US */
  function loc(county, state){
    if (state === 'CA' || (!state && CA[county])) return CA[county] ? { pt: CA[county], place: county + ' County', ca: county } : { pt: null, place: 'California', ca: '' };
    if (ST[state]) return { pt: [ST[state][1], ST[state][2]], place: ST[state][0] };
    if (state && !/^(USA|US)$/.test(state)) return { pt: null, place: state, abroad: true };
    return { pt: null, place: '' };
  }
  function furthest(it, CO){
    const r = it.r, o = loc(String(r.county || '').trim(), (CO[it.out] || [])[0] || (r.county ? 'CA' : ''));
    const from = o.pt || SAC; let best = null, bd = -1;
    it.ps.forEach(p => { const l = loc(p.county, p.state); const d = l.abroad ? 1e6 : l.pt ? km(from, l.pt) : -1;
      if (d > bd + 1e-9){ bd = d; best = { p, l, d }; } });
    return best && bd >= 1 ? best : null;
  }
  /* bill numbers link to the Bills tab through the shared helper (addendum); until it exists, an <a data-bill> it upgrades */
  const billLink = (ctx, b, date) => typeof ctx.billLink === 'function' ? ctx.billLink(b, { date }) : `<a data-bill="${ctx.esc(b)}" data-date="${ctx.esc(date || '')}">${ctx.esc(b)}</a>`;
  const slugOf = (it, ctx) => it.key + '-' + ctx.slug(it.r.hl).split('-').slice(0, 6).join('-');
  const daysTxt = (ctx, d) => d == null ? 'no date' : d === 0 ? 'same day' : (d > 0 ? '+' : '−') + ctx.pl(Math.abs(d), 'day');
  const repDate = (ctx, x) => x.date ? ctx.dateLabel({ date: x.date, prec: 'day' }) : 'no date';
  function summary(ctx, it){
    const out = [];
    let s = `Picked up by ${ctx.pl(it.n, 'outlet')}`;
    /* TRAVEL-v23: "the same day" only when no pickup ran before the original; days before day 0 are said, not floored to 0 */
    const all = it.early > 0 && it.early === it.ps.filter(p => p.d != null).length;
    if (it.span == null) s += ' (no dates on file)';
    else if (all) s += ', all before the original';
    else if (it.span <= 0) s += it.early ? `: ${it.early} before the original, the rest the same day` : ' the same day';
    else { s += ` in ${ctx.pl(it.span, 'day')}`; if (it.early) s += ` (${it.early} before the original)`; }
    out.push(s);
    if (it.far) out.push(`furthest: ${it.far.p.name} (${it.far.l.place})`);
    const k = [...it.langs.values()].reduce((a, b) => a + b, 0);
    if (k) out.push(`in-language: ${k} (${[...it.langs].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).map(x => x[0]).join(', ')})`);
    return it.n ? out.join('; ') + '.' : 'No other outlet ran this story.';
  }
  const chips = (ctx, x) => [x.media, x.reach, x.lang && x.lang !== 'English' ? x.lang : ''].filter(Boolean)
    .map((v, i) => `<span class="badge"${i === 1 && x.inf ? ' title="Reach inferred from the outlet’s state"' : ''}>${ctx.esc(v)}</span>`).join(' ');

  /* ---- the list ---- */
  const N_OPTS = [['1', 'One outlet', n => n === 1], ['2', '2 to 4', n => n >= 2 && n <= 4], ['5', '5 to 9', n => n >= 5 && n <= 9], ['10', '10 or more', n => n >= 10]];
  const list = {
    noun: ['story', 'stories'], title: 'Story travel', placeholder: 'Search headline, outlet, author',
    cap: 'Stories that other outlets ran too, with how many outlets picked each one up (copies in the original’s own outlet or house don’t count). Click a headline to read the story, or “How it spread” for its pickups.',
    items: ctx => { CTX = ctx; return model(ctx).list; },
    key: it => it.key,
    text: it => [it.r.hl, it.r.hl_en, it.out, it.r.outlet, (it.r.authors || []).join(' ')].join(' '),
    facets: [
      { key: 'date', label: 'Original date', type: 'date', date: it => it.r.date, hint: 'When the original ran.' },
      { key: 'outlet', label: 'Original outlet', search: true, limit: 8, vals: it => it.out },
      { key: 'iss', label: 'Issue', vals: it => String(it.r.topic || '').trim() || 'Unassigned', sw: v => CTX ? CTX.colorFor('topic', v) : '' },
      { key: 'n', label: 'Reprint count', type: 'one', any: 'Any number', hint: 'Other outlets that ran it, each counted once.',
        options: N_OPTS.map(([id, label, t]) => ({ id, label, test: it => t(it.n) })) },
      { key: 'reached', label: 'Outlets it reached', search: true, limit: 8, vals: it => it.ps.map(p => p.name), hint: 'Stories this outlet picked up.' },
      { key: 'lng', label: 'Language', vals: it => [...new Set([it.lang0].concat(it.ps.map(p => p.lang || 'English')))], hint: 'The original’s language or a pickup’s.' }
    ],
    columns: [
      { key: 'hl', label: 'Story', csvLabel: 'Headline', val: it => it.r.hl, cell: (it, ctx) => {
        let h = ctx.clipItem(it.r, `<b>${ctx.pl(it.n, 'outlet')}</b>`, { pub: it.out });
        h = h.replace(' · <b>', ' <b>');   /* C2 (FINALCHECK-v1): on the phone card .cm is a flex row, so the "·" before the count dangled after the byline */
        h = h.replace(/ data-id="[^"]*"/, '').replace(/ tabindex="-1" role="option"/, '').replace('<span class="cm">' + ctx.dateLabel(it.r) + ' · ', '<span class="cm">');
        /* HLPANEL-v1 (Sammy 2026-10-28): the headline opens the story panel, as everywhere; "How it spread ›" opens this tab's page */
        h = h.replace(/<span class="ct">([\s\S]*?)<\/span>/, function(m0, t){ return '<span class="ct"><button type="button" class="linkbtn tv-hl" data-tbstory="' + ctx.esc(it.r.id) + '" title="Open the story">' + t + '</button></span>'; });
        /* SPREADTAG-v1 (Sammy 2026-10-29): the link sits at the end of the tags row */ const go = ' <button type="button" class="linkbtn tt-open tv-go">How it spread ›</button>'; return /<\/span><\/div>$/.test(h) ? h.replace(/<\/span><\/div>$/, go + '</span></div>') : h + go; } },
      { key: 'date', label: 'Original date', dir: -1, cls: 'nw', val: it => it.r.date, cell: (it, ctx) => ctx.esc(ctx.dateLabel(it.r)) },
      { key: 'n', label: 'Outlets', num: true, dir: -1, val: it => it.n, cell: (it, ctx) => ctx.fmt(it.n), csvLabel: 'Outlets reached' },
      { key: 'span', label: 'Days to last', num: true, dir: -1, val: it => it.span, cell: (it, ctx) => it.span == null ? '<span class="sub">—</span>' : (it.span < 0 ? '−' : '') + ctx.fmt(Math.abs(it.span)), csvLabel: 'Days to last pickup' }
    ],
    sort: { key: 'n', dir: -1 }, open: 'page', step: { desk: 100, phone: 25 },
    answer: (res, st, ctx) => { if (!res.length) return ''; const t = res.slice().sort((a, b) => b.n - a.n || String(b.r.date).localeCompare(String(a.r.date)))[0];
      return `${ctx.pl(res.length, 'story', 'stories')} ran in other outlets. Widest: “${t.r.hl}” (${t.out}), picked up by ${ctx.pl(t.n, 'outlet')}.`; },
    empty: () => 'No story matches these filters.',
    copies: [{ label: 'Copy pickup summary', sub: 'One line per story: headline, original outlet and date, outlets reached',
      text: (res, st, ctx) => res.map(it => `${it.r.hl} (${it.out}, ${ctx.dateLabel(it.r)}): picked up by ${ctx.pl(it.n, 'outlet')}`).join('\n'),
      ok: res => `Copied ${res.length} ${res.length === 1 ? 'story' : 'stories'}` }],
    csvName: (st, ctx) => `AJG story travel ${ctx.TODAY}.csv`,
    csvExtra: [['Story ID', it => it.r.id], ['Original outlet', it => it.out], ['Issue', it => it.r.topic || ''], ['Copies in other outlets', it => it.copies],
      ['Copies in its own outlet', it => it.ownC.length], ['Outlets reached, in order', it => it.ps.map(p => p.name).join('; ')]]
  };

  /* ---- the story page ---- */
  function curve(ctx, it, W){
    const pts = it.ps.filter(p => p.d != null);
    if (!pts.length) return { svg: '<div class="empty">No dated pickups to chart.</div>', days: [] };
    const days = [...new Set(pts.map(p => p.d))].sort((a, b) => a - b), N = pts.length;
    const cum = new Map(); let c = 0; days.forEach(d => { c += pts.filter(p => p.d === d).length; cum.set(d, c); });
    const H = W < 600 ? 210 : 240, m = { l: 34, r: 14, t: 26, b: 30 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
    const S = ctx.niceScale(N, 'count'), ymax = S.max || 1, lo = Math.min(0, days[0]), hi = Math.max(3, days[days.length - 1]);   // at least 3 days wide, so a same-day story still reads as a curve
    const x = d => m.l + (d - lo) / (hi - lo) * iw, y = v => m.t + ih - v / ymax * ih;
    let s = ctx.axis(`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Outlets that had run the story, by days after the original">`, W, H, m, ymax);
    const span = hi - lo, every = [1, 2, 5, 7, 10, 14, 30, 60, 90, 180, 365, 730].find(k => span / k <= Math.max(3, Math.floor(iw / 64))) || 730;
    for (let d = Math.ceil(lo / every) * every; d <= hi; d += every) s += `<text x="${x(d).toFixed(1)}" y="${H - 8}" text-anchor="middle">${d > 0 ? '+' + d : d < 0 ? '−' + -d : '0'}</text>`;
    s += `<line class="base" x1="${m.l}" x2="${W - m.r}" y1="${y(0)}" y2="${y(0)}"></line>`;
    s += `<line x1="${x(0).toFixed(1)}" x2="${x(0).toFixed(1)}" y1="${m.t - 8}" y2="${y(0)}" stroke="var(--ink-3)" stroke-dasharray="3 3"></line><text class="peak" x="${(x(0) + 4).toFixed(1)}" y="${m.t - 12}" text-anchor="${x(0) > W - 90 ? 'end' : 'start'}">Original (day 0)</text>`;
    let dpath = `M${x(lo).toFixed(1)},${y(0).toFixed(1)}`;
    days.forEach(d => { dpath += `H${x(d).toFixed(1)}V${y(cum.get(d)).toFixed(1)}`; });
    dpath += `H${x(hi).toFixed(1)}`;
    s += `<path d="${dpath}" fill="none" stroke="var(--bar)" stroke-width="2.5" stroke-linejoin="round"></path>`;
    /* milestones: about half, every outlet, and 5 / 10 / 20 on the way when they fall elsewhere; at most 3, 70 px apart */
    const want = [...new Set([5, 10, 20, Math.ceil(N / 2), N].filter(k => k >= 1 && k <= N))].sort((a, b) => b - a);
    const ms = []; want.forEach(k => { const d = days.find(dd => cum.get(dd) >= k), v = cum.get(d);
      if (ms.length < 3 && !ms.some(q => q.d === d || Math.abs(x(q.d) - x(d)) < 70)) ms.push({ k: v, d }); });
    ms.sort((a, b) => a.d - b.d).forEach(q => { const cx = x(q.d), cy = y(q.k), end = cx > W - 120;
      s += `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="4" fill="var(--bar)" stroke="var(--panel)" stroke-width="1.5"></circle><text class="peak" data-ms="${q.k}|${q.d}" x="${(cx + (end ? -7 : 7)).toFixed(1)}" y="${(cy - 7).toFixed(1)}" text-anchor="${end ? 'end' : 'start'}">${ctx.pl(q.k, 'outlet')} ${q.d === 0 ? 'the same day' : q.d < 0 ? 'before day 0' : 'by day ' + q.d}</text>`; });
    const bw = Math.max(10, Math.min(40, iw / Math.max(1, span) * 0.9));
    days.forEach((d, i) => { s += `<rect class="hit nc" data-d="${d}" x="${(x(d) - bw / 2).toFixed(1)}" y="${m.t}" width="${bw.toFixed(1)}" height="${ih}"></rect>`; });
    return { svg: s + '</svg>', days, cum, pts, ms };
  }
  /* ROWLIST-v1: the ladder in the Clips row style. Line 1 the outlet (its page) + type badges; line 2 muted: date, days
     after, place, copies, the headline when it differs; links on the right (copy icon left); a quiet rank column. */
  function ladder(ctx, it){
    const r = it.r, rowO = (o, i) => ctx.row(Object.assign({ attrs: ` data-step="${i}" data-out="${ctx.esc(o.name)}"`, hidden: i > LCUT }, o));
    const o0 = { media: r.media, reach: ctx.reachTags(r)[0] || '', lang: ctx.langOf(r) };
    let h = rowO({ name: it.out, rank: '', title: ctx.pageLink('outlets', ctx.slug(it.out), it.out, 'Open the outlet page'), badges: '<span class="badge">Original</span> ' + chips(ctx, o0),
      meta: [ctx.esc(ctx.dateLabel(r)), 'day 0', it.ownC.length ? `${ctx.pl(it.ownC.length, 'more copy', 'more copies')} in ${ctx.esc(it.out)} (not counted)` : ''],
      right: ctx.storyLinks(r) + `<button type="button" class="linkbtn" data-tbstory="${ctx.esc(r.id)}">Open the story</button>` }, 0);
    const fh = ctx.fold(r.hl), fe = ctx.fold(r.hl_en || '');
    it.ps.forEach((p, i) => {
      const hls = [...new Set(p.copies.map(c => String(c.p.hl || '').trim()).filter(t => t && ctx.fold(t) !== fh && ctx.fold(t) !== fe))];
      const links = p.copies.map((c, j) => { const l = ctx.storyLinks(c.p), lab = p.copies.length > 1 ? `<span class="note">Copy ${j + 1} · ${ctx.esc(repDate(ctx, c))}</span>` : '';
        return l ? l.replace('<div class="dlinks">', '<div class="dlinks">' + lab) : `<div class="dlinks">${lab}<span class="note">No link on file</span></div>`; }).join('');
      const place = loc(p.county, p.state).place;
      h += rowO({ name: p.name, rank: i + 1, title: ctx.pageLink('outlets', ctx.slug(p.name), p.name, 'Open the outlet page'), badges: chips(ctx, p),
        meta: [ctx.esc(repDate(ctx, p)), ctx.esc(daysTxt(ctx, p.d)), place ? ctx.esc(place) : '', p.copies.length > 1 ? ctx.pl(p.copies.length, 'copy', 'copies') : '',
          hls.length ? `<span class="hl-en">“${ctx.esc(hls[0])}”${hls.length > 1 ? ` +${hls.length - 1}` : ''}</span>` : ''],
        right: links }, i + 1);
    });
    return `<div class="clip-list">${h}</div>` + (it.n > LCUT ? `<div><button type="button" class="btn" data-tv="all">Show all ${ctx.pl(it.n, 'outlet')}</button></div>` : '');
  }
  /* SPREADRULE-v1 (DECISIONS 2026-10-28): the "How it spread" curve only when it says something. All of: at least 3 pickups
     with a day-precise date; those fall on at least 3 distinct days counting the original's day 0; the last is day 2 or
     later. The original's own date must be day-precise too. Otherwise one plain sentence goes in the summary line. */
  function spread(ctx, it){
    if (it._sp) return it._sp;
    const r = it.r, dated = it.ps.filter(p => p.d != null), days = [...new Set([0].concat(dated.map(p => p.d)))].sort((a, b) => a - b);
    const undated = it.ps.length - dated.length, approx0 = (r.prec && r.prec !== 'day') || !ISO.test(r.date || '');
    const show = !approx0 && dated.length >= 3 && days.length >= 3 && days[days.length - 1] >= 2;
    if (show) return (it._sp = { show, text: '' });
    const dn = d => d < 0 ? 'day −' + -d : 'day ' + d, list = a => a.length > 1 ? a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1] : a[0];
    const more = undated ? ` ${ctx.pl(undated, 'more has', 'more have')} no exact date.` : '';
    let t;
    if (approx0) t = r.date ? 'The original’s date is only known to the ' + (r.prec === 'year' ? 'year' : 'month') + ', so there is no spread curve.' : 'The original has no date on file, so there is no spread curve.';
    else if (!dated.length) t = it.ps.some(p => String(p.p.date || '').trim() && p.p.date !== 'nan') ? 'Pickup dates are only known to the month.' : 'No pickup dates are on file.';
    else if (dated.every(p => p.d === 0)) t = undated ? more.trim() : '';   /* the summary line already says "the same day" */
    else { const pd = [...new Set(dated.map(p => p.d))].sort((a, b) => a - b);
      t = `They ran on ${list(pd.map(dn))}.${more}`; }
    return (it._sp = { show, text: t });
  }
  const LCUT = 20;   // ladder rows shown before "Show all"
  const LCOLS = [['Order', x => x.i], ['Outlet', x => x.name], ['Date', x => x.date || ''], ['Days after the original', x => x.d == null ? '' : x.d], ['Medium', x => x.media || ''],
    ['Reach', x => x.reach || ''], ['Language', x => x.lang || ''], ['Place', x => loc(x.county, x.state).place], ['Copies', x => x.copies ? x.copies.length : 1],
    ['Headline', x => x.hl], ['Links', x => x.links]];
  function ladderRows(ctx, it){
    const r = it.r, lk = o => ctx.linksOf ? ctx.linksOf(o).map(p => p[1]).join(' ') : (o.lk || []).map(p => p[1]).concat(o.lk && o.lk.length ? [] : [o.plink || o.link || ''].filter(Boolean)).join(' ');   /* PRINTLINK-v1 */
    return [{ i: 0, name: it.out + ' (original)', date: r.date, d: 0, media: r.media, reach: ctx.reachTags(r).join('; '), lang: ctx.langOf(r), county: r.county || '', state: '', hl: r.hl, links: lk(r), copies: [0].concat(it.ownC) }]
      .concat(it.ps.map((p, i) => Object.assign({}, p, { i: i + 1, hl: p.p.hl || '', links: p.copies.map(c => lk(c.p)).filter(Boolean).join(' ') })));
  }
  /* the original + every pickup outlet by place. The county map shows when at least 2 counties are known and the known
     counties cover at least half of the outlets that are not placed outside California ("most counties known"). */
  function where(ctx, it){
    const r = it.r, CO = (ctx.block('common') || {}).o || {}, ca = new Map(), byC = new Map(); let out = 0, none = 0;
    [{ name: it.out, county: String(r.county || '').trim(), state: r.county ? 'CA' : ((CO[it.out] || [])[0] || '') }].concat(it.ps).forEach(p => {
      const l = loc(p.county, p.state);
      if (l.ca){ ca.set(l.ca, (ca.get(l.ca) || 0) + 1); (byC.get(l.ca) || byC.set(l.ca, []).get(l.ca)).push(p.name); }
      else if (!l.place) none++;
      else if (l.place !== 'California') out++; });
    const known = [...ca.values()].reduce((a, b) => a + b, 0);
    return { ca, byC, known, none, map: ca.size >= 2 && known >= (it.n + 1 - out) / 2 };
  }
  function drawPage(ctx, it){
    const host = document.querySelector(`#tbBody .tb-view[data-tb="travel"] .tbe[data-tbe-id="${CSS.escape(ctx.sub)}"]`);
    if (!host || host.dataset.tvDrawn) return; host.dataset.tvDrawn = '1';
    const head = host.querySelector('.tbe-head'), fc = host.querySelector('.tbe-chart'), gl = host.querySelector(':scope > .grid-clips');
    if (fc) fc.hidden = true; if (gl) gl.hidden = true;   // one story: Data's chart and the one-row list add nothing here
    const w = where(ctx, it), r = it.r, approx = r.prec && r.prec !== 'day';
    const undated = it.ps.filter(p => p.d == null).length, early = it.ps.filter(p => p.d != null && p.d < 0).length;
    head.insertAdjacentHTML('afterend', `
<div class="card chartcard tv-curve"><h2 class="sec">How it spread</h2><div class="cap">Outlets that had run the story, by days after the original (day 0). Each outlet counts once, on the day its first copy ran. Hover a step for the outlets.</div>
  <div class="chart tv-chart"></div>
  ${undated ? `<div class="note">${ctx.pl(undated, 'outlet has', 'outlets have')} no date on file and ${undated === 1 ? 'is' : 'are'} not on the curve.</div>` : ''}
  ${early ? `<div class="note">${ctx.pl(early, 'outlet is', 'outlets are')} dated before the original (usually a print edition dated earlier than the web original).</div>` : ''}
  ${approx ? '<div class="note">The original’s date is not exact, so days after it are approximate.</div>' : ''}
  <details class="dt"><summary>Show the numbers</summary><div class="tablewrap tv-num"></div></details></div>
<div class="card pad tv-where"><h2 class="sec">Where it ran</h2><div class="cap">${w.map ? 'California outlets by home county, outside California by state: the same maps as Data. Hover over a county or state to preview its clips; click it to keep the preview open and see them in Clips.' : 'Outlets by home county in California, and by state outside it.'}${w.none > 0 ? ` ${ctx.pl(w.none, 'outlet has', 'outlets have')} no place on file.` : ''}</div>
  ${w.map ? '<h3 class="tb-us-h">In California</h3><div class="tv-cmap"></div>' : (w.ca.size ? `<div class="cap">California: ${[...w.ca].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).map(([c, n]) => `${ctx.esc(c)} County (${n})`).join(', ')}.</div>` : '')}<div class="tb-us tv-us"></div></div>
<div class="card pad tv-ladder"><h2 class="sec">Pickup ladder</h2><div class="cap">One row per outlet in the order it ran, with its type, date and days after the original; copies in the same outlet are grouped. Click an outlet for its page.${it.early ? ` The original is listed first; ${ctx.pl(it.early, 'outlet')} ran it earlier (negative days).` : ''}</div>
  <div class="an-controls"><details class="dlmenu"><summary class="btn">Export</summary><div class="menu">
    <button data-tv="copy"><b>Copy pickup list</b><span>One line per outlet: date, days after, link</span></button>
    <button data-tv="csv"><b>Download CSV</b><span>Every outlet, with every column</span></button></div></details></div>
  ${ladder(ctx, it)}</div>`);
    /* curve: SPREADRULE-v1 drops the card when the curve would say nothing (the sentence is in the summary line) */
    if (!spread(ctx, it).show){ const cv = host.querySelector('.tv-curve'); if (cv) cv.remove(); }
    const ch = host.querySelector('.tv-chart'), W = Math.max(300, (ch && ch.clientWidth) || 900), C = curve(ctx, it, W);
    if (ch) ch.innerHTML = C.svg;
    if (ch && C.days.length){
      host.querySelector('.tv-num').innerHTML = `<table><thead><tr><th>Day</th><th>Date</th><th>New outlets</th><th>Total</th></tr></thead><tbody>${C.days.map(d => { const ps = C.pts.filter(p => p.d === d);
        return `<tr data-day="${d}"><td>${d > 0 ? '+' + d : d}</td><td>${ctx.esc(repDate(ctx, ps[0]))}</td><td>${ps.length}</td><td>${C.cum.get(d)}</td></tr>`; }).join('')}</tbody></table>`;
      ch.onmousemove = e => { const t = e.target.closest('.hit'); if (!t){ ctx.hideTip(); return; } const d = +t.dataset.d, ps = C.pts.filter(p => p.d === d);
        ctx.showTip(e, `<div class="th">${ctx.esc(daysTxt(ctx, d))} · ${ctx.esc(repDate(ctx, ps[0]))}</div>${ps.slice(0, 8).map(p => `<div class="row"><span class="l"><span>${ctx.esc(p.name)}</span></span></div>`).join('')}${ps.length > 8 ? `<div class="foot">and ${ps.length - 8} more</div>` : ''}<div class="row tot"><span class="l">Outlets so far</span><b>${C.cum.get(d)}</b></div>`); };
      ch.onmouseleave = () => ctx.hideTip();
    }
    /* maps */
    if (w.map){ try { ctx.geoMap(host.querySelector('.tv-cmap'), { geo: 'ca', rows: [r], aria: 'Where the story ran in California' }); } catch(e){ console.error(e); } }   /* GEOMAP-v1 */
    try { ctx.usMap(host.querySelector('.tv-us'), [it.out].concat(it.ps.map(p => p.name)), { rows: [r] }); } catch(e){ console.error(e); }
    /* ladder export */
    host.querySelector('.tv-ladder').addEventListener('click', e => { const b = e.target.closest('[data-tv]'); if (!b) return; e.stopPropagation();
      if (b.dataset.tv === 'all'){ host.querySelectorAll('.tv-ladder [data-step][hidden]').forEach(x => { x.hidden = false; }); b.parentElement.remove(); return; }
      b.closest('details').open = false;
      const rows = ladderRows(ctx, it);
      if (b.dataset.tv === 'csv') ctx.saveFile(`AJG story travel ${r.id} ${ctx.TODAY}.csv`, ctx.csv(rows, LCOLS));
      else ctx.copy([`${r.hl} (${it.out}, ${ctx.dateLabel(r)}): ${summary(ctx, it)}`].concat(rows.slice(1).map(x => `${x.i}. ${x.name}, ${x.date ? ctx.dateLabel({ date: x.date, prec: 'day' }) : 'no date'} (${daysTxt(ctx, x.d)})${x.links ? ' ' + x.links.split(' ')[0] : ''}`)).join('\n'), `Copied ${ctx.pl(rows.length - 1, 'outlet')}`, b); });
  }
  const page = {
    slug: (it, ctx) => slugOf(it, ctx),
    find: (sub, ctx) => { const id = String(sub || '').split('-')[0].toLowerCase(), M = model(ctx); return M.ids.get(id) || null; },
    spec: (it, ctx) => {
      const r = it.r, by = (r.authors || []).map(a => ctx.authorLink ? ctx.authorLink(a) : ctx.esc(a)).join(', ');
      return { kicker: ['Story travel', ctx.dateLabel(r), it.out], title: r.hl, noun: 'story', backLabel: 'All stories that travelled',
        sub: ctx.esc(summary(ctx, it)) + (spread(ctx, it).show || !spread(ctx, it).text ? '' : ` <span class="tv-nocurve">${ctx.esc(spread(ctx, it).text)}</span>`),
        facts: [['Original', ctx.pageLink('outlets', ctx.slug(it.out), it.out, 'Open the outlet page')], ['Date', ctx.esc(ctx.dateLabel(r))], ['By', by],
          ['Issue', ctx.issueLink ? ctx.issueLink(r.topic || '') : ctx.esc(r.topic || '')], ['Bills', (r.bills || []).map(x => billLink(ctx, x, r.date)).join(', ')], ['Outlets reached', ctx.fmt(it.n)], ['Copies', ctx.fmt(it.copies) + (it.ownC.length ? ` <span class="sub">+ ${ctx.fmt(it.ownC.length)} in its own outlet</span>` : '')],
          ['Days to last pickup', it.span == null ? '' : (it.span < 0 ? '−' : '') + ctx.fmt(Math.abs(it.span))], ['Furthest', it.far ? `${ctx.esc(it.far.p.name)} <span class="sub">${ctx.esc(it.far.l.place)}</span>` : ''],
          ['Story', `<button type="button" class="linkbtn" data-tbstory="${ctx.esc(r.id)}">Open the story</button>`], ['Links', ctx.storyLinks(r)]],   /* TVLINKS-v1 (Sammy 2026-10-29: "move this link into the box above"): links in the header's Links row, not a card under it */
        rows: [r],
        chart: false, list: false, after: () => drawPage(ctx, it) };   // framework hooks (Phase B): no Data chart, no one-row list
    }
  };
  AJGTabs.register({ id: 'travel', list, page,
    legacy: (p, ctx) => { const it = p.id ? model(ctx).ids.get(String(p.id).toLowerCase()) : null;
      return it ? { params: {}, sub: slugOf(it, ctx) } : { params: p.id ? { q: p.id } : {}, sub: '' }; } });
})();
