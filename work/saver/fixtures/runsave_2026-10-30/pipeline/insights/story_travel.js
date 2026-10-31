/* Insights: Story travel (agent-ins-story_travel). How far one story traveled: the original and every reprint on a
   days-after-the-original timeline coloured by Reach, where it ran (county map when the shell offers it), and the
   sources whose originals get reprinted most. Reprint Reach comes from the "ins-story_travel" block
   (story_travel_data.py: the reprint row's own Reach, else same-outlet / same-publisher consensus, else inferred
   from the outlet's state); reprints the block doesn't know (live finds) fall back to the outlet's Reach on originals. */
(function(){ "use strict";
  const GROUPS = {
    'Southern California News Group': ['The Orange County Register','Orange County Register','The Press-Enterprise','Press-Enterprise','Los Angeles Daily News','Daily News','Daily Breeze','Long Beach Press-Telegram','Press-Telegram','Pasadena Star-News','San Gabriel Valley Tribune','Whittier Daily News','Inland Valley Daily Bulletin','The Sun','Redlands Daily Facts'],
    'Bay Area News Group': ['East Bay Times','The Mercury News','San Jose Mercury News','Marin Independent Journal','Santa Cruz Sentinel','Monterey Herald','Vallejo Times-Herald','The Reporter']
  };
  const GROUP_OF = new Map(); Object.entries(GROUPS).forEach(([g, l]) => l.forEach(o => GROUP_OF.set(o.toLowerCase(), g)));
  const NC = 'Not classified';
  let memo = null, st = { id: '', pid: '', src: '', grp: 'outlet', all: false };
  const setId = ctx => { st.pid = st.id; ctx.setParams({ id: st.id }); };

  // TRAVEL-v2: the outlet behind an original, named from the CURRENT sheet (block "n": AP wire feeds -> Associated Press,
  // case / leading-"The" variants -> one spelling). Never r.pub: that is carried over from the old tracker's records.
  let NAMES = {};
  function srcName(r){ const o = String(r.outlet || '').trim(); if (NAMES[o]) return NAMES[o];
    if (/^(the )?associated press\b/i.test(o) || /^ap\b/i.test(o)) return 'Associated Press';
    const m = /^(.*), The\/(.*)$/.exec(o); return m ? 'The ' + m[1].trim() : o; }
  // reprints that count as travel: other outlets only, one per outlet (its earliest dated copy)
  function travelReps(r){ const by = new Map(), own = String(r.outlet || '');
    (r.reps || []).forEach(rp => { if (!rp.outlet || rp.outlet === own) return; const cur = by.get(rp.outlet);
      const dk = rp => /^\d{4}-\d{2}-\d{2}$/.test(rp.date || '') ? rp.date : '9999';
      if (!cur) by.set(rp.outlet, Object.assign({ n: 1 }, rp)); else { cur.n++; if (dk(rp) < dk(cur)) Object.assign(cur, rp, { n: cur.n }); } });
    return [...by.values()]; }
  const keyOf = (name, grp) => grp === 'group' ? (GROUP_OF.get(name.toLowerCase()) || name) : name;

  function build(ctx){
    if (memo && memo.v === ctx.version) return memo;
    const blk = ctx.block('story_travel') || {}, bo = blk.o || {}, ba = blk.a || {}, inf = new Set(blk.inf || []), X = blk.x || {};
    NAMES = blk.n || {};
    const oReach = new Map();  // outlet -> primary Reach from originals (fallback for reprints the block doesn't cover)
    ctx.D.forEach(r => { const t = ctx.reachTags(r)[0]; if (!t) return; [r.outlet].forEach(o => { if (!o) return;
      const m = oReach.get(o) || oReach.set(o, new Map()).get(o); m.set(t, (m.get(t) || 0) + 1); }); });
    const topOf = m => m ? [...m].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0][0] : '';
    const repReach = rp => { const v = ba[rp.aid] || bo[rp.outlet] || topOf(oReach.get(rp.outlet));
      return { reach: String(v || '').split(/;\s*/)[0] || NC, inf: !ba[rp.aid] && inf.has(rp.outlet) }; };
    // display spelling for a merged source: the most common raw spelling
    const spell = new Map();
    // TRAVEL-v2: only stories that travelled (a reprint in another outlet), no picker duplicates (block "x"), one entry each
    const tr = new Map(); ctx.D.forEach(r => { if ((r.reps || []).length) tr.set(r.id, travelReps(r)); });
    const stories = ctx.D.filter(r => (tr.get(r.id) || []).length && String(r.hl || '').trim() && !X[r.id])
      .sort((a, b) => tr.get(b.id).length - tr.get(a.id).length || String(b.date).localeCompare(String(a.date)) || a.id.localeCompare(b.id));
    stories.forEach(r => { const n = srcName(r), k = n.toLowerCase(), m = spell.get(k) || spell.set(k, new Map()).get(k); m.set(n, (m.get(n) || 0) + 1); });
    const nameOf = n => topOf(spell.get(n.toLowerCase())) || n;
    memo = { v: ctx.version, stories, repReach, nameOf, src: {}, tr: id => tr.get(id) || [] };
    return memo;
  }
  function sources(M, grp){
    if (M.src[grp]) return M.src[grp];
    const m = new Map();
    M.stories.forEach(r => { const k = keyOf(M.nameOf(srcName(r)), grp), e = m.get(k) || m.set(k, { k, stories: 0, reps: 0, outs: new Set(), ids: [] }).get(k);
      const t = M.tr(r.id); e.stories++; e.reps += t.length; e.ids.push(r.id); t.forEach(rp => e.outs.add(rp.outlet)); });
    return (M.src[grp] = [...m.values()].sort((a, b) => b.reps - a.reps || b.outs.size - a.outs.size || a.k.localeCompare(b.k)));
  }
  const OTHER = '__other';   // sources with a single travelled story share one "Other sources" entry in the Source picker
  const inSource = (M, r) => { if (!st.src) return true; const k = keyOf(M.nameOf(srcName(r)), st.grp);
    if (st.src === OTHER){ const e = sources(M, st.grp).find(x => x.k === k); return !!e && e.stories < 2; } return k === st.src; };

  function travel(ctx, M, r){
    const pts = [], undated = [];
    travelReps(r).forEach((rp, i) => { const d = /^\d{4}-\d{2}-\d{2}$/.test(rp.date || '') && /^\d{4}-\d{2}-\d{2}$/.test(r.date || '') ? ctx.daysBetween(r.date, rp.date) : null;
      const rr = M.repReach(rp), p = { i, rp, d, reach: rr.reach, inf: rr.inf };
      (d === null || isNaN(d) ? undated : pts).push(p); });
    pts.sort((a, b) => a.d - b.d || ctx.REACH_ORDER.indexOf(a.reach) - ctx.REACH_ORDER.indexOf(b.reach) || a.rp.outlet.localeCompare(b.rp.outlet));
    const own = (r.reps || []).filter(rp => rp.outlet === r.outlet).length;
    return { pts, undated, outlets: pts.length + undated.length, own };
  }
  const reachColor = (ctx, v) => v === NC ? 'var(--sother)' : ctx.colorFor('reach', v);
  const place = rp => [rp.county ? rp.county + ' County' : '', rp.state || ''].filter(Boolean).join(', ');

  function timeline(ctx, r, T, W){
    const m = { l: 30, r: 18, t: 12, b: 30 }, iw = W - m.l - m.r;
    const lo = Math.min(0, ...T.pts.map(p => p.d)), hiRaw = Math.max(1, ...T.pts.map(p => p.d)), hi = hiRaw <= 7 ? 7 : ctx.niceMax(hiRaw);
    const x = d => m.l + (d - lo) / (hi - lo) * iw;
    // stack the dots of one day into a column (original at the bottom of day 0)
    const col = new Map(); col.set(0, 1);
    const R = 5, sp = R * 2 + 2; let maxStack = 1;
    const dots = [{ orig: true, d: 0, k: 0 }].concat(T.pts.map(p => { const k = col.get(p.d) || 0; col.set(p.d, k + 1); maxStack = Math.max(maxStack, k + 1); return Object.assign({ k }, p); }));
    const step = Math.min(sp, (300 - m.t - m.b - R * 2) / Math.max(1, maxStack - 1));
    const H = Math.max(150, Math.min(300, m.t + m.b + R * 2 + (maxStack - 1) * step + 6)), base = H - m.b - R - 2;
    // ticks: whole days, at most ~8
    const span = hi - lo, every = [1, 2, 5, 7, 10, 14, 30, 60, 90, 180, 365].find(s => span / s <= Math.max(3, Math.floor(iw / 70))) || 365;
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Original and ${ctx.pl(T.pts.length, 'reprint')} by days after the original"><g class="grid">`;
    for (let d = Math.ceil(lo / every) * every; d <= hi; d += every) s += `<line x1="${x(d)}" x2="${x(d)}" y1="${m.t - 6}" y2="${H - m.b}"></line><text x="${x(d)}" y="${H - 8}" text-anchor="middle">${d === 0 ? 'Original' : (d > 0 ? '+' : '') + d}</text>`;
    s += `</g><line class="base" x1="${m.l}" x2="${W - m.r}" y1="${H - m.b}" y2="${H - m.b}"></line>`;
    dots.forEach((p, j) => { const cx = x(p.d), cy = base - p.k * step, c = p.orig ? reachColor(ctx, ctx.reachTags(r)[0] || NC) : reachColor(ctx, p.reach);
      s += p.orig ? `<circle cx="${cx}" cy="${cy}" r="${R + 2}" fill="${c}" stroke="var(--ink)" stroke-width="2"></circle>`
        : p.inf ? `<circle cx="${cx}" cy="${cy}" r="${R - 1}" fill="var(--panel)" stroke="${c}" stroke-width="2"></circle>`
        : `<circle cx="${cx}" cy="${cy}" r="${R}" fill="${c}" stroke="var(--panel)" stroke-width="1.5"></circle>`;
      s += `<circle class="hit st-hit" data-j="${j}" cx="${cx}" cy="${cy}" r="${Math.max(R + 3, step / 2 + 1)}" fill="transparent"></circle>`; });
    return { svg: s + '</svg>', dots };
  }

  function legend(ctx, r, T){
    const c = new Map(); [ctx.reachTags(r)[0] || NC].concat(T.pts.concat(T.undated).map(p => p.reach)).forEach(v => c.set(v, (c.get(v) || 0) + 1));
    const ord = ctx.REACH_ORDER.concat([NC]).filter(v => c.has(v));
    const anyInf = T.pts.some(p => p.inf);
    return `<div class="legend">${ord.map(v => `<span class="it"><span class="sw" style="background:${reachColor(ctx, v)}"></span>${ctx.esc(v)} (${ctx.fmt(c.get(v))})</span>`).join('')}<span class="it"><span class="sw" style="background:var(--panel);box-shadow:inset 0 0 0 2px var(--ink)"></span>Ringed: the original</span>${anyInf ? '<span class="it"><span class="sw" style="background:var(--panel);box-shadow:inset 0 0 0 2px var(--ink-3)"></span>Hollow: Reach inferred from the outlet’s state</span>' : ''}</div>`;
  }

  function where(ctx, r, T){
    const all = [{ rp: { outlet: srcName(r), county: r.county, state: '' }, orig: true }].concat(T.pts, T.undated);
    const ca = new Map(), out = new Map(), byC = new Map();
    all.forEach(p => { const rp = p.rp, stt = String(rp.state || '').trim();
      if (rp.county && (!stt || stt === 'CA')){ ca.set(rp.county, (ca.get(rp.county) || 0) + 1); const l = byC.get(rp.county) || byC.set(rp.county, []).get(rp.county); if (!l.includes(rp.outlet)) l.push(rp.outlet); }
      else if (stt && stt !== 'CA') out.set(stt, (out.get(stt) || 0) + 1); });
    return { ca, out, byC };
  }


  /* TRAVEL-v3 (Sammy: "a pop out menu and a search function and list them as they would appear in clips"): one pop-out
     picker for both Story and Source. Desktop: a popover anchored under its button; phone (≤640px): a full-width sheet.
     Search box on top (focused on open; headline, outlet, author, date; accent- and case-insensitive; 120 ms debounce)
     with a result count; entries drawn in chunks of 60 as the list scrolls; arrows / Enter / Esc; Esc or a click outside
     closes. Clicks inside never reach the tracker's own Clips handlers (no author filter, no story panel). */
  let POP = null;
  function closePop(focusBtn){ if (!POP) return; const p = POP; POP = null;
    document.removeEventListener('mousedown', p.outside, true); window.removeEventListener('resize', p.place);
    p.node.remove(); if (p.scrim) p.scrim.remove(); p.btn.setAttribute('aria-expanded', 'false'); if (focusBtn) p.btn.focus(); }
  function openPop(btn, o){
    closePop(); const ctx = o.ctx, CH = o.chunk || 60, phone = matchMedia('(max-width: 640px)').matches;
    const node = document.createElement('div'); node.className = 'st-pop' + (phone ? ' sheetmode' : ''); node.setAttribute('role', 'dialog'); node.setAttribute('aria-label', o.title);
    node.innerHTML = `<div class="st-pop-h"><div class="st-pop-t"><b>${ctx.esc(o.title)}</b><span class="st-pop-n" aria-live="polite"></span><button type="button" class="iconbtn st-pop-x" aria-label="Close" title="Close (Esc)"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button></div>
      <input type="search" class="st-pop-q" placeholder="${ctx.esc(o.placeholder)}" aria-label="${ctx.esc(o.placeholder)}" autocomplete="off" role="combobox" aria-expanded="true" aria-controls="stPopList"></div>
      <div class="st-pop-list${o.clips ? ' clip-list' : ''}" id="stPopList" role="listbox"></div>`;
    let scrim = null; if (phone){ scrim = document.createElement('div'); scrim.className = 'st-pop-scrim'; document.body.appendChild(scrim); }
    document.body.appendChild(node);
    const list = node.querySelector('.st-pop-list'), q = node.querySelector('.st-pop-q'), cnt = node.querySelector('.st-pop-n');
    const keys = o.items.map(it => ctx.fold(o.text(it)));
    let hits = o.items.map((_, i) => i), drawn = 0, act = -1, tq;
    const more = () => { if (drawn >= hits.length) return; const end = Math.min(hits.length, drawn + CH);
      list.insertAdjacentHTML('beforeend', hits.slice(drawn, end).map((i, j) => o.render(o.items[i], 'stpo-' + (drawn + j), o.items[i] === o.current)).join('')); drawn = end; };
    const setAct = k => { const els = list.children; if (!hits.length){ act = -1; return; }
      k = Math.max(0, Math.min(hits.length - 1, k)); while (k >= drawn && drawn < hits.length) more();
      if (els[act]) els[act].classList.remove('act'); act = k; const a = els[act]; a.classList.add('act'); q.setAttribute('aria-activedescendant', a.id || '');
      a.scrollIntoView({ block: 'nearest' }); };
    const run = () => { const t = ctx.fold(q.value).split(' ').filter(Boolean);
      hits = []; keys.forEach((k, i) => { if (t.every(w => k.includes(w))) hits.push(i); });
      list.innerHTML = hits.length ? '' : `<div class="empty">No match for “${ctx.esc(q.value)}”.</div>`; drawn = 0; act = -1; more();
      cnt.textContent = (q.value.trim() ? `${ctx.fmt(hits.length)} of ${ctx.fmt(o.items.length)}` : ctx.fmt(o.items.length)) + ' ' + o.noun(hits.length); };
    const pick = i => { const it = o.items[i]; closePop(false); o.onPick(it); };
    list.addEventListener('scroll', () => { if (list.scrollTop + list.clientHeight > list.scrollHeight - 240) more(); });
    node.addEventListener('click', e => { e.stopPropagation();
      if (e.target.closest('.st-pop-x')){ closePop(true); return; }
      const c = e.target.closest('[data-pi]'); if (c) pick(+c.dataset.pi); });
    node.addEventListener('keydown', e => { e.stopPropagation();
      if (e.key === 'Escape'){ e.preventDefault(); closePop(true); }
      else if (e.key === 'ArrowDown'){ e.preventDefault(); setAct(act + 1); }
      else if (e.key === 'ArrowUp'){ e.preventDefault(); setAct(act - 1); }
      else if (e.key === 'Enter'){ e.preventDefault(); const i = act >= 0 ? hits[act] : hits[0]; if (i != null) pick(i); } });
    q.addEventListener('input', () => { clearTimeout(tq); tq = setTimeout(run, 120); });
    const place = () => { if (phone) return; const r = btn.getBoundingClientRect(), w = Math.min(Math.max(r.width, 520), innerWidth - 32);
      node.style.width = w + 'px'; node.style.left = Math.max(16, Math.min(r.left, innerWidth - w - 16)) + 'px';
      const below = innerHeight - r.bottom - 16, above = r.top - 16, up = below < 320 && above > below;
      node.style.maxHeight = Math.max(240, Math.min(560, up ? above : below)) + 'px';
      if (up){ node.style.top = ''; node.style.bottom = (innerHeight - r.top + 6) + 'px'; } else { node.style.bottom = ''; node.style.top = (r.bottom + 6) + 'px'; } };
    const outside = e => { if (!node.contains(e.target) && !btn.contains(e.target)) closePop(false); };
    POP = { node, scrim, btn, outside, place };
    document.addEventListener('mousedown', outside, true); window.addEventListener('resize', place);
    btn.setAttribute('aria-expanded', 'true'); place(); run();
    const cur = hits.findIndex(i => o.items[i] === o.current); if (cur > 0 && cur < 600) setAct(cur);
    q.focus();
  }

  function render(el, ctx){
    const M = build(ctx), p = ctx.params || {};
    if ((p.id || '') !== st.pid){ st.pid = p.id || ''; if (p.id){ st.id = p.id; st.src = ''; } }  // only a NEW param id wins (ctx.params can be stale after setParams)
    if (!ctx.D.length || !M.stories.length){ el.innerHTML = '<div class="in-sec"><div class="card pad"><div class="empty">No reprints in the data yet.</div></div></div>'; return; }
    const pool = M.stories.filter(r => inSource(M, r));
    let r = st.id ? ctx.byId(st.id) : null;
    if (!r && st.id){ el.innerHTML = `<div class="in-sec"><div class="card pad"><h2 class="sec">How far a story traveled</h2><div class="empty">No story with the ID ${ctx.esc(st.id)}. <button type="button" class="linkbtn" data-act="reset">Show the most reprinted story</button></div></div></div>`;
      el.onclick = e => { if (e.target.closest('[data-act="reset"]')){ st.id = ''; ctx.setParams({}); render(el, ctx); } }; return; }
    if (!r || (st.src && !inSource(M, r))) r = pool[0] || M.stories[0];
    st.id = r.id;
    const W = Math.max(300, (el.clientWidth || 1000) - 34), T = travel(ctx, M, r), TL = timeline(ctx, r, T, W), w = where(ctx, r, T);
    const last = T.pts.length ? Math.max(...T.pts.map(q => q.d)) : 0, places = w.ca.size + w.out.size;
    const opts = pool.some(x => x.id === r.id) ? pool : [r].concat(pool);
    const srcList = sources(M, st.grp), srcMany = srcList.filter(e => e.stories > 1), srcOne = srcList.filter(e => e.stories < 2);
    const nOut = x => M.tr(x.id).length, cut = (t, n) => t.length > n ? t.slice(0, n - 1).trimEnd() + '…' : t;
    const summary = T.pts.length || T.undated.length
      ? `Reprinted by ${ctx.pl(T.outlets, 'other outlet')}${T.pts.length ? `, the last ${last === 0 ? 'the same day' : ctx.pl(last, 'day') + ' after the original'}` : ''}${places ? ', in ' + [w.ca.size ? ctx.pl(w.ca.size, 'California county', 'California counties') : '', w.out.size ? ctx.pl(w.out.size, w.ca.size ? 'other state or country' : 'state or country outside California', w.ca.size ? 'other states or countries' : 'states or countries outside California') : ''].filter(Boolean).join(' and ') : ''}.`
      : (T.own ? 'Reprinted only in its own outlet.' : 'No reprints found for this story.');
    const canMap = typeof ctx.drawCountyMap === 'function' && w.ca.size > 0;
    const outList = [...w.out].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    const rowsT = [{ orig: true, d: 0, rp: { outlet: r.outlet, date: r.date, county: r.county, state: '' }, reach: ctx.reachTags(r)[0] || NC }].concat(T.pts, T.undated.map(q => Object.assign({ d: null }, q)));
    const shown = st.all ? srcList : srcList.slice(0, 12), maxReps = srcList.length ? srcList[0].reps : 1;

    el.innerHTML = `<div class="in-sec">
<div class="card chartcard st-card" data-sid="${r.id}">
  <h2 class="sec">How far a story traveled</h2>
  <div class="cap">The original and every reprint, by days after the original ran, coloured by the reprinting outlet’s Reach. Hover a dot for the outlet; click it to open the story.</div>
  <div class="an-controls st-controls">
    <div class="st-pf"><span class="eyebrow">Source</span><button type="button" class="st-pbtn" data-pop="src" aria-haspopup="dialog" aria-expanded="false"><span>${ctx.esc(st.src === OTHER ? 'Other sources, one story each' : st.src || 'All sources')}</span><i aria-hidden="true"></i></button></div>
    <div class="st-pf st-pick"><span class="eyebrow">Story</span><button type="button" class="st-pbtn" data-pop="story" aria-haspopup="dialog" aria-expanded="false"><span>${ctx.esc(cut(String(r.hl || '').trim(), 90))}</span><small>${ctx.fmt(opts.length)} ${opts.length === 1 ? 'story' : 'stories'}</small><i aria-hidden="true"></i></button></div>
  </div>
  <div class="st-head"><button type="button" class="linkbtn st-hl" data-act="open">${ctx.esc(r.hl || '(no headline)')}</button><div class="st-sub">${ctx.esc(srcName(r))} · ${ctx.esc(ctx.dateLabel(r))}${r.prec && r.prec !== 'day' ? ' (date not exact, so days after are approximate)' : ''}</div><div class="st-sum">${summary}</div></div>
  <div class="st-chart">${TL.svg}</div>
  ${legend(ctx, r, T)}
  ${T.own ? `<div class="note">Not counted: ${ctx.pl(T.own, 'copy', 'copies')} in ${ctx.esc(srcName(r))} itself.</div>` : ''}
  ${T.undated.length ? `<div class="note">${ctx.pl(T.undated.length, 'reprint has', 'reprints have')} no date and ${T.undated.length === 1 ? 'is' : 'are'} not on the timeline.</div>` : ''}
  ${T.pts.some(q => q.d < 0) ? '<div class="note">Points left of day 0 are reprints dated before the original (usually a print edition dated earlier than the web original).</div>' : ''}
  <details class="dt"><summary>Show the numbers</summary><div class="tablewrap"><table class="db"><thead><tr><th>Outlet</th><th>Date</th><th>Days after</th><th>Reach</th><th>Where</th></tr></thead><tbody>${rowsT.map(q => `<tr><td>${ctx.esc(q.orig ? srcName(r) : q.rp.outlet)}${q.orig ? ' <b>(original)</b>' : ''}${q.rp.n > 1 ? ` <span class="note">(${q.rp.n} copies)</span>` : ''}</td><td>${ctx.esc(q.orig ? ctx.dateLabel(r) : (q.rp.date || 'no date'))}</td><td>${q.d === null ? '' : q.d}</td><td>${ctx.esc(q.reach)}${q.inf ? ' (inferred)' : ''}</td><td>${ctx.esc(place(q.rp))}</td></tr>`).join('')}</tbody></table></div></details>
</div>
${places ? `<div class="card pad st-where"><h2 class="sec">Map of pickups</h2><div class="cap">${canMap ? 'California outlets by home county (darker = more clips); outside California by state or country. Hover a county for its outlets.' : 'Outlets by home county in California, and by state or country outside it.'}</div>
  <div class="${canMap ? 'two' : ''}">${canMap ? '<div><svg class="st-map"></svg></div>' : ''}<div>${w.ca.size ? `<div class="st-pl"><b>California</b>${[...w.ca].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).map(([c, n]) => `<span>${ctx.esc(c)} County <i>${n}</i></span>`).join('')}</div>` : ''}${outList.length ? `<div class="st-pl"><b>Outside California</b>${outList.map(([c, n]) => `<span>${ctx.esc(c)} <i>${n}</i></span>`).join('')}</div>` : ''}</div></div></div>` : ''}
<div class="card pad st-src">
  <h2 class="sec">Top sources</h2>
  <div class="cap">Outlets whose original stories others reprinted most: reprints, distinct reprinting outlets, and how many of its stories were reprinted. Click a source to trace its stories above.</div>
  <div class="an-controls"><div class="seg" role="group" aria-label="Group sources"><button type="button" data-grp="outlet" aria-pressed="${st.grp === 'outlet'}">By outlet</button><button type="button" data-grp="group" aria-pressed="${st.grp === 'group'}">By newsroom group</button></div></div>
  <div class="tablewrap"><table class="db st-tbl"><thead><tr><th>Source</th><th class="n">Reprints</th><th class="n" title="Distinct outlets that reprinted them">Outlets</th><th class="n" title="Original stories that were reprinted">Stories</th></tr></thead><tbody>${shown.map(e => `<tr data-src="${ctx.esc(e.k)}"${e.k === st.src ? ' class="on"' : ''}><td><button type="button" class="linkbtn">${ctx.esc(e.k)}</button></td><td class="n"><span class="st-bar"><span style="width:${(e.reps / maxReps * 100).toFixed(1)}%"></span></span>${ctx.fmt(e.reps)}</td><td class="n">${ctx.fmt(e.outs.size)}</td><td class="n">${ctx.fmt(e.stories)}</td></tr>`).join('')}</tbody></table></div>
  ${srcList.length > 12 ? `<button type="button" class="linkbtn" data-act="more">${st.all ? 'Show the top 12' : `Show all ${ctx.fmt(srcList.length)} sources`}</button>` : ''}
  ${st.grp === 'group' ? `<div class="note">Combined: ${Object.keys(GROUPS).map(ctx.esc).join('; ')}. Reprints between sister papers count.</div>` : ''}
</div></div>
<style>
.st-controls{display:flex;flex-wrap:wrap;gap:8px 14px}
.st-pf{display:grid;gap:4px;min-width:0}.st-pf .eyebrow{font-size:var(--fs-xs)}
.st-pbtn{display:flex;align-items:center;gap:10px;width:100%;min-width:0;text-align:left;border:1px solid var(--line);border-radius:8px;background:var(--panel);padding:8px 12px;font-size:var(--fs-md);font-weight:600;color:var(--ink)}
.st-pbtn:hover,.st-pbtn[aria-expanded="true"]{border-color:var(--accent)} .st-pbtn>span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.st-pbtn small{color:var(--ink-3);font-weight:500;white-space:nowrap} .st-pbtn i{width:12px;height:8px;flex:none;background:var(--chev) center/12px 8px no-repeat}
.st-pop{position:fixed;z-index:62;background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);display:flex;flex-direction:column;overflow:hidden}
.st-pop.sheetmode{left:0;right:0;bottom:0;top:auto;max-height:86dvh;height:86dvh;border-radius:14px 14px 0 0;padding-bottom:env(safe-area-inset-bottom,0px)}
.st-pop-scrim{position:fixed;inset:0;z-index:61;background:rgba(8,12,16,.35)}
.st-pop-h{padding:10px 12px;border-bottom:1px solid var(--line-2);display:grid;gap:8px;background:var(--panel)}
.st-pop-t{display:flex;align-items:center;gap:10px} .st-pop-t b{font:700 var(--fs-h3) var(--f-display);color:var(--ink)} .st-pop-n{margin-left:auto;font-size:var(--fs-sm);color:var(--ink-3)}
.st-pop-q{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--panel-2);font-size:var(--fs-lg);color:var(--ink)} .st-pop-q:focus{outline:2px solid var(--focus);outline-offset:0;border-color:transparent}
.st-pop-list{overflow:auto;overscroll-behavior:contain;padding:2px 12px 10px;flex:1;min-height:0}
.st-pop-list .clip{padding:10px 8px;margin:0 -8px;border-radius:6px} .st-pop-list .clip:first-child{padding-top:10px}
.st-pop-list .clip.act,.st-pop-list .st-srcopt.act{background:var(--sel)} .st-pop-list .clip.cur .ct{color:var(--accent)}
.st-pop-list .by-n{color:var(--ink-2)} .st-nrep{font-weight:600;color:var(--ink-2)}
.st-srcopt{display:flex;gap:10px;align-items:baseline;justify-content:space-between;padding:9px 8px;margin:0 -8px;border-radius:6px;cursor:pointer;font-size:var(--fs-md);border-top:1px solid var(--line-2)}
.st-srcopt:first-child{border-top:0} .st-srcopt:hover{background:var(--panel-2)} .st-srcopt.cur span{color:var(--accent);font-weight:600} .st-srcopt small{color:var(--ink-3);white-space:nowrap}.st-controls label{min-width:0;max-width:100%}.st-pick{flex:1 1 320px}.st-pick .sel,.st-controls .sel{max-width:100%;min-width:0}
.st-pick .sel{width:100%}.st-head{margin:12px 0 4px}.st-hl{font-family:var(--f-display);font-weight:600;font-size:var(--fs-h3);text-align:left;color:var(--ink);overflow-wrap:anywhere}
.st-sub,.st-sum{color:var(--ink-2);font-size:var(--fs-lg)}.st-sum{color:var(--ink);margin-top:4px}.st-chart svg{display:block;width:100%;height:auto}
.st-hit{cursor:pointer}.st-chart .grid line{stroke:var(--line);stroke-width:1}.st-chart .grid text{fill:var(--ink-3);font-size:var(--fs-xs)}.st-chart .base{stroke:var(--line-2)}.st-pl{display:flex;flex-wrap:wrap;gap:4px 14px;margin:6px 0 10px;font-size:var(--fs-lg)}.st-pl b{flex-basis:100%;font-weight:600}
.st-pl i{font-style:normal;color:var(--ink-3)}.st-map{width:100%;height:auto;max-height:340px}
.st-tbl td,.st-tbl th{text-align:left}.st-tbl td.n,.st-tbl th.n{text-align:right;white-space:nowrap;padding-left:12px}.st-tbl .linkbtn{text-align:left}.st-tbl tr.on td{background:var(--panel-2)}
.st-bar{display:inline-block;width:70px;height:8px;margin-right:8px;background:var(--panel-2);border-radius:4px;vertical-align:middle;overflow:hidden}
.st-bar span{display:block;height:100%;background:var(--bar);border-radius:0 4px 4px 0}
@media (max-width:600px){.st-bar{display:none}.st-tbl{font-size:var(--fs-md)}}
</style>`;

    if (canMap && places){ try { ctx.drawCountyMap(el.querySelector('.st-map'), w.ca, { tip: c => `<div class="th">${ctx.esc(c)} County · ${ctx.pl(w.ca.get(c) || 0, 'clip')}</div>${(w.byC.get(c) || []).slice(0, 8).map(o => `<div class="row"><span class="l">${ctx.esc(o)}</span></div>`).join('')}` }); } catch(e){ /* map is optional */ } }

    const chart = el.querySelector('.st-chart');
    chart.onmousemove = e => { const t = e.target.closest('.st-hit'); if (!t){ ctx.hideTip(); return; } const q = TL.dots[+t.dataset.j];
      if (q.orig) ctx.showTip(e, `<div class="th">${ctx.esc(srcName(r))}</div><div class="row"><span class="l">Original</span><b>${ctx.esc(ctx.dateLabel(r))}</b></div><div class="row"><span class="l">Reach</span><b>${ctx.esc(ctx.reachTags(r).join('; ') || NC)}</b></div><div class="foot">Click to open the story</div>`);
      else ctx.showTip(e, `<div class="th">${ctx.esc(q.rp.outlet)}</div><div class="row"><span class="l">Ran</span><b>${ctx.esc(q.rp.date)} (${q.d === 0 ? 'same day' : (q.d > 0 ? '+' : '') + ctx.pl(q.d, 'day')})</b></div><div class="row"><span class="l">Reach</span><b>${ctx.esc(q.reach)}${q.inf ? ' (inferred)' : ''}</b></div>${place(q.rp) ? `<div class="row"><span class="l">Where</span><b>${ctx.esc(place(q.rp))}</b></div>` : ''}<div class="foot">Click to open the story</div>`); };
    chart.onmouseleave = () => ctx.hideTip();
    el.onclick = e => {
      const h = e.target.closest('.st-hit'); if (h){ ctx.hideTip(); const q = TL.dots[+h.dataset.j]; ctx.openStory(r.id); return; }
      const a = e.target.closest('[data-act]');
      if (a && a.dataset.act === 'open'){ ctx.openStory(r.id); return; }
      if (a && a.dataset.act === 'more'){ st.all = !st.all; render(el, ctx); return; }
      const g = e.target.closest('[data-grp]'); if (g && g.dataset.grp !== st.grp){ st.grp = g.dataset.grp; st.src = ''; st.all = false; render(el, ctx); return; }
      const tr = e.target.closest('tr[data-src]'); if (tr){ st.src = tr.dataset.src === st.src ? '' : tr.dataset.src; st.id = ''; render(el, ctx); setId(ctx); const c = el.querySelector('.st-card'); if (c && c.scrollIntoView) c.scrollIntoView({ block: 'start', behavior: 'smooth' }); }
    };
    const pb = el.querySelectorAll('[data-pop]');
    pb.forEach(b => b.addEventListener('click', e => { e.stopPropagation(); if (POP && POP.btn === b){ closePop(true); return; }
      if (b.dataset.pop === 'story') openPop(b, { ctx, title: 'Choose a story', placeholder: 'Search headline, outlet, author or date', clips: true,
        items: opts, current: r, noun: n => n === 1 ? 'story' : 'stories',
        text: x => [x.hl, x.hl_en, srcName(x), x.outlet, (x.authors || []).join(' '), ctx.dateLabel(x), x.date].join(' '),
        render: (x, id, on) => ctx.clipItem(x, `<b class="st-nrep">${ctx.pl(nOut(x), 'reprint')}</b>`, { pub: srcName(x), optId: id })
          .replace('<div class="clip"', `<div class="clip${on ? ' cur' : ''}" data-pi="${opts.indexOf(x)}" aria-selected="${on}"`),
        onPick: x => { st.id = x.id; render(el, ctx); setId(ctx); const nb = el.querySelector('[data-pop="story"]'); if (nb) nb.focus(); } });
      else { const items = [{ k: '', label: 'All sources', n: M.stories.length }].concat(srcMany.map(e => ({ k: e.k, label: e.k, n: e.stories })),
          srcOne.length ? [{ k: OTHER, label: 'Other sources, one story each', n: srcOne.reduce((a, e) => a + e.stories, 0), sub: srcOne.map(e => e.k) }] : []);
        openPop(b, { ctx, title: 'Choose a source', placeholder: 'Search outlets', items, chunk: 400, current: items.find(x => x.k === st.src) || items[0],
          noun: n => n === 1 ? 'source' : 'sources', text: x => x.label + ' ' + (x.sub || []).join(' '),
          render: (x, id, on) => `<div class="st-srcopt${on ? ' cur' : ''}" role="option" id="${id}" data-pi="${items.indexOf(x)}" aria-selected="${on}"><span>${ctx.esc(x.label)}</span><small>${ctx.fmt(x.n)} ${x.n === 1 ? 'story' : 'stories'}</small></div>`,
          onPick: x => { st.src = x.k; st.id = ''; render(el, ctx); setId(ctx); const nb = el.querySelector('[data-pop="src"]'); if (nb) nb.focus(); } }); } }));
    el.onchange = e => { const s = e.target.closest('[data-ctl]'); if (!s) return;
      if (s.dataset.ctl === 'src'){ st.src = s.value; st.id = ''; } else st.id = s.value;
      render(el, ctx); setId(ctx); };
  }

  AJGInsights.register({ id: 'story_travel', label: 'Story travel', render, destroy(){ memo = null; closePop(false); } });
})();
