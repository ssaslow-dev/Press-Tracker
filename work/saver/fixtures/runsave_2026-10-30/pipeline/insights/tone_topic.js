/* Insights view (5): tone by issue over time — small multiples of diverging quarterly columns (agent-ins-tone_topic). */
(function(){ "use strict";
  const MIN_N = 5;             // a quarter needs at least this many rated stories to get a bar
  const START_N = 50;          // first charted year needs this many rated stories
  const MAIN = 6;              // issues shown before "All issues"
  const POS = ['Positive','Very positive'], NEG = ['Negative','Very negative']; // inner → outer
  const SKIP = new Set(['', 'Other / roundup', 'Unassigned']);
  const TV = ['Very positive','Positive','Neutral','Negative','Very negative'];
  const memo = {v:-1, r:{}};

  const qOf = d => { if (!d || d.length < 7) return null; const y = +d.slice(0,4), m = +d.slice(5,7); return (y && m >= 1 && m <= 12) ? y*4 + Math.floor((m-1)/3) : null; };
  const qLab = k => `Q${k%4+1} ${Math.floor(k/4)}`;
  const pct = (a, n) => n ? Math.round(a/n*100) : 0;
  const net = c => c.n ? Math.round((c['Very positive']+c.Positive-c.Negative-c['Very negative'])/c.n*100) : 0;
  const signed = v => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v);

  // cells: topic -> Map(quarter -> {n, per-tone counts, ids: Map(storyId -> count)})
  function compute(ctx, withRep){
    const key = withRep ? 'r' : 'o';
    if (memo.v !== ctx.version) { memo.v = ctx.version; memo.r = {}; }
    if (memo.r[key]) return memo.r[key];
    const cells = new Map(), totO = new Map(); let undated = 0, rated = 0;
    const add = (t, k, r) => { let m = cells.get(t); if (!m) cells.set(t, m = new Map()); let c = m.get(k);
      if (!c) m.set(k, c = {n:0, 'Very positive':0, Positive:0, Neutral:0, Negative:0, 'Very negative':0, ids:new Map()});
      c.n++; c[r.tone]++; c.ids.set(r.id, (c.ids.get(r.id)||0) + 1); };
    for (const r of ctx.D){
      if (!ctx.rated(r) || SKIP.has(r.topic || '') || !TV.includes(r.tone)) continue;
      rated++; totO.set(r.topic, (totO.get(r.topic)||0) + 1);
      const k = qOf(r.date); if (k == null) undated++; else add(r.topic, k, r);
      if (withRep) for (const p of (r.reps || [])){ const kp = qOf(p.date) ?? k; if (kp == null) undated++; else add(r.topic, kp, r); }
    }
    // issue order: by rated Originals (stable across the reprint toggle)
    const topics = [...totO.keys()].sort((a, b) => totO.get(b) - totO.get(a) || a.localeCompare(b));
    // chart starts in the first year with at least START_N rated stories (earlier years are a handful of scattered clips)
    const yr = new Map(); let k1 = -Infinity, early = 0, pMax = 0, nMax = 0;
    for (const m of cells.values()) for (const [k, c] of m){ yr.set(Math.floor(k/4), (yr.get(Math.floor(k/4))||0) + c.n); k1 = Math.max(k1, k); }
    const ys = [...yr.keys()].sort((a, b) => a - b), y0 = ys.find(y => yr.get(y) >= START_N) ?? ys[0];
    const k0 = y0 == null ? 0 : y0*4;
    for (const m of cells.values()) for (const [k, c] of m){ if (k < k0){ early += c.n; continue; }
      if (c.n >= MIN_N){ pMax = Math.max(pMax, (c.Positive+c['Very positive'])/c.n); nMax = Math.max(nMax, (c.Negative+c['Very negative'])/c.n); } }
    const out = {cells, topics, totO, k0, k1, early, undated, rated,
      pMax: Math.max(.25, Math.ceil(pMax*4)/4), nMax: Math.max(.25, Math.ceil(nMax*4)/4)};
    return memo.r[key] = out;
  }

  // vertical segment: from y0 to y1 (either direction), rounded on the far end only when `end`
  function seg(x, y0, y1, bw, end){
    const up = y1 < y0, h = Math.abs(y1 - y0); if (h < .5) return '';
    const r = end ? Math.min(3, bw/2, h) : 0, s = up ? 1 : -1;
    return r > 0 ? `<path d="M${x},${y0} V${y1+s*r} Q${x},${y1} ${x+r},${y1} H${x+bw-r} Q${x+bw},${y1} ${x+bw},${y1+s*r} V${y0} Z"` : `<path d="M${x},${y0} V${y1} H${x+bw} V${y0} Z"`;
  }

  function panel(ctx, A, t, W){
    const m = {l:34, r:6, t:6, b:20}, ph = 120, sh = 16, H = m.t + ph + 6 + sh + m.b;
    const iw = W - m.l - m.r, nq = A.k1 - A.k0 + 1, band = iw / nq, bw = Math.max(1.5, Math.min(24, band - 2)), gap = band >= 5 ? 1 : 0;
    const span = A.pMax + A.nMax, y0 = m.t + ph * A.pMax / span, ppx = ph / span; // px per share unit
    const cm = A.cells.get(t) || new Map();
    let nPk = 1; for (const [k, c] of cm) if (k >= A.k0) nPk = Math.max(nPk, c.n);
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${ctx.esc(t)}: share of positive and negative stories by quarter"><g class="grid">`;
    const st = span > 1 ? .5 : .25;
    for (let v = -Math.floor(A.nMax/st)*st; v <= A.pMax + 1e-9; v += st){ if (Math.abs(v) < 1e-9) continue; const yy = y0 - v*ppx;
      s += `<line x1="${m.l}" x2="${W-m.r}" y1="${yy}" y2="${yy}"></line><text x="${m.l-6}" y="${yy+4}" text-anchor="end">${signed(Math.round(v*100))}%</text>`; }
    s += `<text x="${m.l-6}" y="${y0+4}" text-anchor="end">0</text>`;
    s += `</g><line class="base" x1="${m.l}" x2="${W-m.r}" y1="${y0}" y2="${y0}"></line>`;
    const sy = m.t + ph + 6 + sh; // count strip baseline
    s += `<line class="base" x1="${m.l}" x2="${W-m.r}" y1="${sy}" y2="${sy}"></line><text x="${m.l-6}" y="${sy-3}" text-anchor="end">n</text>`;
    let hits = '';
    for (let k = A.k0; k <= A.k1; k++){
      const c = cm.get(k), x = m.l + (k - A.k0) * band + (band - bw) / 2;
      if (c){
        const sh2 = Math.max(1, c.n / nPk * sh);
        s += `<path d="M${x},${sy} V${sy-sh2} H${x+bw} V${sy} Z" fill="var(${c.n >= MIN_N ? '--q3' : '--muted-dot'})"></path>`;
        if (c.n >= MIN_N){
          for (const [side, list] of [[1, POS], [-1, NEG]]){
            let y = y0; const last = list.reduce((a, tn, i) => c[tn] ? i : a, -1);
            list.forEach((tn, i) => { if (!c[tn]) return; const h = c[tn] / c.n * ppx, ys = y + (y === y0 ? 0 : -side*gap), ye = y - side*h;
              s += seg(x, ys, ye, bw, i === last) + ` fill="${ctx.colorFor('tone', tn)}"></path>`; y = ye; });
          }
        } else s += `<circle cx="${x+bw/2}" cy="${y0}" r="${Math.min(2.5, Math.max(1.5, bw/2))}" fill="none" stroke="var(--ink-3)" stroke-width="1"></circle>`;
      }
      hits += `<rect class="hit${c ? '' : ' nc'}" data-k="${k}" x="${m.l + (k - A.k0)*band}" y="${m.t}" width="${band}" height="${H - m.t - m.b}"></rect>`;
    }
    // year labels: every year if room, else every other / every fourth
    const yrs = Math.floor(A.k1/4) - Math.ceil(A.k0/4) + 1, step = band*4 >= 34 ? 1 : band*8 >= 34 ? 2 : 4;
    for (let y = Math.ceil(A.k0/4); y*4 <= A.k1; y++){ if ((y - Math.ceil(A.k0/4)) % step) continue;
      const x = m.l + (y*4 - A.k0) * band; s += `<line x1="${x}" x2="${x}" y1="${sy}" y2="${sy+3}" stroke="var(--line)"></line><text x="${x}" y="${H-5}">${step > 1 || yrs > 6 ? '’' + String(y).slice(2) : y}</text>`; }
    return s + `<g data-t="${ctx.esc(t)}">${hits}</g></svg>`;
  }

  function tipHtml(ctx, t, k, c){
    const row = (l, sw, v) => `<div class="row"><span class="l">${sw ? `<span class="sw" style="background:${sw}"></span>` : ''}<span>${l}</span></span><b>${v}</b></div>`;
    let h = `<div class="th">${ctx.esc(t)} · ${qLab(k)}</div>`;
    if (!c) return h + `<div class="foot">No rated stories this quarter.</div>`;
    for (const tn of TV) h += row(tn, ctx.colorFor('tone', tn), `${c[tn]} · ${pct(c[tn], c.n)}%`);
    h += `<div class="tot">${row('Rated stories', '', c.n)}${c.n >= MIN_N ? row('Net tone', '', signed(net(c)) + ' pts') : ''}</div>`;
    return h + `<div class="foot">${c.n < MIN_N ? `Fewer than ${MIN_N} rated stories: no bar. ` : ''}Click to list these stories.</div>`;
  }

  function detail(ctx, A, t, k, withRep){
    const c = A.cells.get(t)?.get(k);
    if (!c) return '';
    const ord = r => TV.indexOf(r.tone);
    const recs = [...c.ids.keys()].map(id => ctx.byId(id)).filter(Boolean).sort((a, b) => ord(a) - ord(b) || (a.date < b.date ? -1 : 1));
    const li = r => { const x = c.ids.get(r.id); return `<li><button class="linkbtn tt-open" data-id="${ctx.esc(r.id)}" style="text-align:left;font-weight:500">${ctx.esc(r.hl || '(no headline)')}</button> <span style="color:var(--ink-3)">— ${ctx.esc(r.outlet)}, ${ctx.esc(ctx.dateLabel(r))}${withRep && x > 1 ? `, counted ${x}× with reprints` : ''}</span></li>`; };
    const nonN = recs.filter(r => r.tone !== 'Neutral'), neu = recs.filter(r => r.tone === 'Neutral');
    let h = `<h2 class="sec">${ctx.esc(t)} · ${qLab(k)}</h2><div class="cap">${ctx.pl(c.n, 'rated story', 'rated stories')}${withRep ? ` incl. reprints (${ctx.pl(recs.length, 'Original', 'Originals')} below)` : ''}${c.n >= MIN_N ? `, net tone ${signed(net(c))} pts` : ` — too few for a bar`}. Click a headline to open the story.</div>`;
    for (const tn of TV){ const g = recs.filter(r => r.tone === tn); if (!g.length || tn === 'Neutral') continue;
      h += `<div style="margin-top:10px;font-weight:600;display:flex;gap:6px;align-items:center"><span class="sw" style="background:${ctx.colorFor('tone', tn)}"></span>${tn} (${g.length})</div><ul class="tt-list">${g.map(li).join('')}</ul>`; }
    if (neu.length) h += `<details style="margin-top:10px"><summary style="cursor:pointer;font-weight:600"><span class="sw" style="background:${ctx.colorFor('tone','Neutral')};margin-right:6px"></span>Neutral (${neu.length})</summary><ul class="tt-list">${neu.map(li).join('')}</ul></details>`;
    if (!nonN.length && !neu.length) h += '<div class="empty">No stories.</div>';
    return h;
  }

  function table(ctx, A, list){
    let rows = '';
    for (const t of list){ const cm = A.cells.get(t); if (!cm) continue;
      for (const k of [...cm.keys()].sort((a, b) => a - b)){ const c = cm.get(k);
        rows += `<tr><td>${ctx.esc(t)}</td><td>${qLab(k)}</td><td>${c.n}</td>${TV.map(tn => `<td>${c[tn] || ''}</td>`).join('')}<td>${c.n >= MIN_N ? signed(net(c)) : '–'}</td></tr>`; } }
    return `<table><thead><tr><th>Issue</th><th>Quarter</th><th>Rated</th>${TV.map(tn => `<th>${tn}</th>`).join('')}<th>Net (pts)</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  const V = {
    id: 'tone_topic',
    label: 'Tone by issue',
    render(el, ctx){
      const P = Object.assign({}, ctx.params || {}), withRep = P.r === '1', all = P.all === '1';
      const A = compute(ctx, withRep), Ao = compute(ctx, false);
      if (!Ao.rated || !A.topics.length){ el.innerHTML = '<div class="in-sec"><div class="card pad"><h2 class="sec">Tone by issue</h2><div class="empty">No rated stories yet.</div></div></div>'; return; }
      if (P.issue && !Ao.topics.includes(P.issue)){ el.innerHTML = `<div class="in-sec"><div class="card pad"><h2 class="sec">Tone by issue</h2><div class="empty">No rated stories for “${ctx.esc(P.issue)}”. <button class="linkbtn" data-set="issue" data-v="">Show all issues</button></div></div></div>`;
        el.onclick = e => { if (e.target.closest('[data-set="issue"]')){ const np = Object.assign({}, P); delete np.issue; ctx.setParams(np); V.render(el, Object.assign(Object.create(ctx), {params: np})); } }; return; }
      const list = P.issue ? [P.issue] : all ? Ao.topics : Ao.topics.slice(0, MAIN);
      const segBtn = (k, v, lab) => `<button data-set="${k}" data-v="${v}" aria-pressed="${(P[k] === '1') === (v === '1')}">${lab}</button>`;
      const lg = (tn) => `<span class="it"><span class="sw" style="background:${ctx.colorFor('tone', tn)}"></span>${tn}</span>`;
      const notes = [];
      if (A.early) notes.push(`${ctx.pl(A.early, 'story', 'stories')} before ${qLab(A.k0)} (too few to chart) are left out`);
      if (A.undated) notes.push(`${ctx.pl(A.undated, 'story has', 'stories have')} only a year`);
      el.innerHTML = `<div class="in-sec">
        <div class="card chartcard">
          <h2 class="sec">Tone by issue, quarter by quarter</h2>
          <div class="cap">Each column is one quarter: share of rated stories that were positive (up) or negative (down); neutral is the rest. The small bars underneath count the rated stories. Quarters with fewer than ${MIN_N} get a ring, not a bar. Click a quarter to list its stories.</div>
          <div class="an-controls" style="margin:10px 0 12px">
            <div class="seg tt-seg" role="group" aria-label="Count">${segBtn('r', '0', 'Originals only')}${segBtn('r', '1', 'Incl. reprints')}</div>
            <div class="seg tt-seg" role="group" aria-label="Issues">${segBtn('all', '0', `Main ${MAIN} issues`)}${segBtn('all', '1', `All ${Ao.topics.length} issues`)}</div>
          </div>
          <div class="legend">${lg('Very positive')}${lg('Positive')}${lg('Negative')}${lg('Very negative')}<span class="it"><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="3" fill="none" stroke="var(--ink-3)"></circle></svg>Under ${MIN_N} rated</span></div>
          <div class="tt-grid">${list.map(t => { const n = [...(A.cells.get(t)?.values() || [])].reduce((s, c) => s + c.n, 0);
            return `<div class="tt-p" data-t="${ctx.esc(t)}"><div class="tt-h"><button class="linkbtn tt-clips" data-t="${ctx.esc(t)}" title="See these stories in Clips">${ctx.esc(t)}</button><span>${ctx.fmt(n)} rated</span></div><div class="chart"></div></div>`; }).join('')}</div>
          <div class="cap" style="margin-top:10px">${withRep ? 'Reprints count in the quarter they ran and carry their Original’s tone (only Originals are rated). ' : ''}${notes.length ? notes.join('; ') + '.' : ''}</div>
          <details class="dt"><summary>Show the numbers</summary><div class="dt-act"><button class="linkbtn tt-copy">Copy table</button></div><div class="tt-table" style="overflow:auto;max-height:440px">${table(ctx, A, list)}</div></details>
        </div>
        <div class="card pad tt-detail"${P.q ? '' : ' hidden'}></div>
      </div>
      <style>.tt-seg button{white-space:nowrap;padding:5px 10px}.tt-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,400px),1fr));gap:14px 22px}
      .tt-h{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:2px}.tt-h span{font-size:var(--fs-sm);color:var(--ink-3);white-space:nowrap}
      .tt-h .linkbtn{color:var(--ink);font-size:var(--fs-md);text-align:left}
      .tt-list{margin:4px 0 0;padding-left:18px;font-size:var(--fs-md)}.tt-list li{margin:3px 0}
      .tt-p .chart rect.hit:hover,.tt-p .chart rect.hit.on{fill:var(--ink);fill-opacity:.06}</style>`;
      el.querySelectorAll('.tt-p').forEach(p => { const t = p.dataset.t, c = p.querySelector('.chart'); c.innerHTML = panel(ctx, A, t, Math.max(300, Math.round(c.clientWidth || 340))); });
      const det = el.querySelector('.tt-detail');
      const showDetail = (t, k) => { det.innerHTML = detail(ctx, A, t, k, withRep); det.hidden = !det.innerHTML; };
      if (P.q){ const i = P.q.lastIndexOf('|'), t = P.q.slice(0, i), k = +P.q.slice(i+1); if (A.cells.get(t)?.get(k)) showDetail(t, k); else det.hidden = true; }
      const cellAt = e => { const h = e.target.closest('rect.hit'); if (!h) return null; const t = h.parentNode.dataset.t, k = +h.dataset.k; return {h, t, k, c: A.cells.get(t)?.get(k)}; };
      el.onpointermove = e => { const o = cellAt(e); if (o) ctx.showTip(e, tipHtml(ctx, o.t, o.k, o.c)); else ctx.hideTip(); };
      el.onpointerleave = () => ctx.hideTip();
      el.onclick = e => {
        const b = e.target.closest('[data-set]'); if (b){ const np = Object.assign({}, P, {[b.dataset.set]: b.dataset.v === '1' ? '1' : undefined}); if (b.dataset.set === 'r') delete np.q; if (b.dataset.set === 'all') delete np.issue; Object.keys(np).forEach(k => np[k] === undefined && delete np[k]); ctx.setParams(np); V.render(el, Object.assign(Object.create(ctx), {params: np})); return; }
        const o2 = e.target.closest('.tt-open'); if (o2){ ctx.openStory(o2.dataset.id); return; }
        const cl = e.target.closest('.tt-clips'); if (cl){ ctx.clips({topic: cl.dataset.t}); return; }
        if (e.target.closest('.tt-copy')){ const tb = el.querySelector('.tt-table table'); ctx.copy([...tb.rows].map(r => [...r.cells].map(c => c.textContent).join('\t')).join('\n'), 'Copied the table.', e.target); return; }
        const o = cellAt(e); if (o && o.c){ el.querySelectorAll('rect.hit.on').forEach(x => x.classList.remove('on')); o.h.classList.add('on');
          const np = Object.assign({}, P, {q: o.t + '|' + o.k}); ctx.setParams(np); P.q = np.q; showDetail(o.t, o.k); det.scrollIntoView({block:'nearest', behavior:'smooth'}); }
      };
    }
  };
  AJGInsights.register(V);
})();
