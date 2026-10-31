/* ---------- charts ---------- */
const tip = $('#tip');
function showTip(e, html){ tip.innerHTML = html; tip.hidden = false; const w = tip.offsetWidth, h = tip.offsetHeight; let x = e.clientX + 14, y = e.clientY + 14; if (x + w > innerWidth - 8) x = e.clientX - w - 14; if (y + h > innerHeight - 8) y = e.clientY - h - 14; tip.style.left = Math.max(8,x)+'px'; tip.style.top = Math.max(8,y)+'px'; }
const hideTip = () => { tip.hidden = true; };
/* AXIS-v1: one nice-scale helper for every chart. kind 'count' (integer ticks), 'pct' (capped at 100, zooms in when low),
   'tone' (symmetric around 0; returns the half-span). max = data max + ~6% headroom rounded up to 1/2/2.5/5 x 10^n, 2-5 steps. */
function niceScale(v, kind){ kind = kind || 'count'; if (!(v > 0)) return { max: 0, step: 0, n: 0, empty: true };
  if (kind === 'tone') v = Math.max(v, 0.45);
  const t = v * 1.06, e0 = Math.floor(Math.log10(t)) - 1;
  for (let e = e0; e <= e0 + 3; e++) for (const m of [1, 2, 2.5, 5]){ const step = m * Math.pow(10, e);
    if (kind === 'count' && (step < 1 || !Number.isInteger(step))) continue; if (kind === 'tone' && step < 0.1) continue;
    const n = Math.max(kind === 'tone' ? 1 : 2, Math.ceil(t / step - 1e-9)); if (n > (kind === 'tone' ? 3 : 5)) continue;
    let max = +(n * step).toFixed(6);
    if (kind === 'pct' && max > 100) return { max: 100, step: 20, n: 5 };
    if (kind === 'tone' && max > 2) return { max: 2, step: 1, n: 2 };
    return { max, step, n }; }
  return { max: t, step: t / 4, n: 4 }; }
function niceMax(v, kind){ const s = niceScale(v, kind); return s.max || (kind === 'pct' ? 100 : 1); }
/* AXIS-v1: tick count for a max from niceScale (integer steps whenever the max allows it) */
function axisTicks(ymax){ const nice = st => { const p = Math.pow(10, Math.floor(Math.log10(st) + 1e-9)), m = st / p; return [1, 2, 2.5, 5, 10].some(x => Math.abs(m - x) < 1e-6); };
  const intOnly = Number.isInteger(ymax) && ymax >= 2;
  for (const n of [5, 4, 3, 2, 6]){ const st = ymax / n; if (nice(st) && (!intOnly || Number.isInteger(+st.toFixed(9)))) return n; }
  return 4; }
const axisLab = v => Number.isInteger(+v.toFixed(6)) ? fmt(Math.round(v)) : (+v.toFixed(2)).toString();
function barPath(x, y0, y1, bw, top){
  const hgt = Math.max(0.5, y0 - y1); const r = top ? Math.min(3, bw/2, hgt) : 0;
  return r>0 ? `M${x},${y0} V${y1+r} Q${x},${y1} ${x+r},${y1} H${x+bw-r} Q${x+bw},${y1} ${x+bw},${y1+r} V${y0} Z` : `M${x},${y0} V${y1} H${x+bw} V${y0} Z`;
}
function axis(svg, W, H, m, ymax, suf){
  const ih = H-m.t-m.b; let s = '<g class="grid">';
  const nt = axisTicks(ymax); for (let i=0;i<=nt;i++){ const v = ymax*i/nt, yy = m.t + ih - (v/ymax)*ih; s += `<line x1="${m.l}" x2="${W-m.r}" y1="${yy}" y2="${yy}"></line><text x="${m.l-6}" y="${yy+4}" text-anchor="end">${axisLab(v)}${suf||''}</text>`; }  /* AXIS-v1 */
  return svg + s + '</g>';
}
function simpleBars(el, items, onClick, tickMode){
  const W = Math.max(300, el.clientWidth || 1000), H = W < 600 ? 180 : 220, m = {l:34, r:6, t:8, b:24}, iw = W-m.l-m.r, ih = H-m.t-m.b;
  if (!items.some(i => i.v)){ el.innerHTML = '<div class="empty">Nothing to chart.</div>'; el.onclick = el.onmousemove = null; return; }  /* AXIS-v1 */
  const ymax = niceMax(Math.max(...items.map(i=>i.v))), band = iw/items.length, bw = band*.72;
  const y = v => m.t + ih - (v/ymax)*ih;
  let svg = axis(`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Stories per month">`, W, H, m, ymax);
  items.forEach((it,i) => { const x = m.l + i*band + (band-bw)/2; if (it.v) svg += `<path d="${barPath(x, y(0), y(it.v), bw, true)}" fill="var(--bar)"></path>`; if (it.tick) svg += tickMode==='centered' ? `<text x="${m.l+i*band+band/2}" y="${H-6}" text-anchor="middle">${it.tick}</text>` : `<text x="${m.l+i*band}" y="${H-6}">${it.tick}</text>`; });
  svg += `<line class="base" x1="${m.l}" x2="${W-m.r}" y1="${y(0)}" y2="${y(0)}"></line>`;
  items.forEach((it,i) => svg += `<rect class="hit${onClick?'':' nc'}" data-i="${i}" x="${m.l+i*band}" y="${m.t}" width="${band}" height="${ih}"></rect>`);
  el.innerHTML = svg + '</svg>';
  el.onmousemove = e => { const t = e.target.closest('.hit'); if (!t){ hideTip(); return; } const it = items[+t.dataset.i]; showTip(e, `<div class="th">${it.label}</div><div class="row"><span class="l">Stories</span><b>${fmt(it.v)}</b></div>${onClick?'<div class="foot">Click to see these clips</div>':''}`); };
  el.onmouseleave = hideTip;
  el.onclick = e => { const t = e.target.closest('.hit'); if (t && onClick){ hideTip(); onClick(items[+t.dataset.i].k); } };
}

function bucketKey(r, iv){
  const y = r.date.slice(0,4);
  if (iv==='year') return y;
  if (r.prec==='year') return null;
  const m = +r.date.slice(5,7);
  return iv==='month' ? `${y}-${String(m).padStart(2,'0')}` : `${y}-Q${Math.ceil(m/3)}`;
}
function allBuckets(iv, y0, y1){
  const out = [];
  for (let y=y0; y<=y1; y++){
    if (iv==='year') out.push(String(y));
    else if (iv==='quarter') for (let q=1;q<=4;q++) out.push(`${y}-Q${q}`);
    else for (let m=1;m<=12;m++) out.push(`${y}-${String(m).padStart(2,'0')}`);
  }
  return out;
}
const bucketLabel = (k, iv) => iv==='year' ? k : iv==='quarter' ? k.replace('-',' ') : monthName(k);

// the "Show only" list: every value of the Color by field in the clips shown, busiest first; keeps the pick while it is still there
function fillOnly(bk, rows, sel){
  sel = sel || $('#anOnly'); const cur = sel.value, c = new Map();  /* TABS-v1: the entity-page chart passes its own select */
  rows.forEach(r => (bk==='reach' ? reachTags(r) : [bkVal(r, bk)]).forEach(v => { if (v) c.set(v, (c.get(v)||0)+1); }));
  const order = (bk==='reach' || bk==='tone' || bk==='role') ? (RANK[bk]||[]).filter(v=>c.has(v)) : [...c.entries()].sort((a,b)=>b[1]-a[1]).map(e=>e[0]);
  const key = bk + '|' + order.join('|');
  if (sel.dataset.key !== key){ sel.innerHTML = '<option value="">All of them</option>' + order.map(v => `<option value="${esc(v)}">${esc(v)} (${fmt(c.get(v))})</option>`).join(''); sel.dataset.key = key; }
  sel.value = c.has(cur) ? cur : '';
  return sel.value;
}
/* TABS-v1: Data's "Coverage over time" chart is drawn by timeChart(rows, o), shared with the reporter and outlet pages.
   o = the controls' values, the elements to draw into, and what a click on a bar does; Data passes its own controls and
   its old click (open Clips on that period), so the Data tab behaves exactly as before. */
function renderTimeChart(rows){ return timeChart(rows, { iv: $('#anInterval').value, bk: $('#anBreak').value, meas: $('#anMeasure').value, from: +$('#anFrom').value,
  pct: $('#anShow').value==='pct', avgOn: $('#anAvg').checked, avgEl: $('#anAvg'), onlyEl: $('#anOnly'), title: $('#tsTitle'), cap: $('#tsCap'), legend: $('#tsLegend'),
  chart: $('#tsChart'), table: $('#tsTable'), quick: true, pick: (b, iv) => {
    if (iv==='month') setMonth(b);
    else if (iv==='year') applyWhen('y'+b);
    else { const yr = b.slice(0,4), q = +b.slice(-1); S.when='custom'; S.d0 = `${yr}-${String(q*3-2).padStart(2,'0')}`; S.d1 = `${yr}-${String(q*3).padStart(2,'0')}-99`; S.whenLabel = `${b.replace('-',' ')}`; }
    go('db'); } }); }
/* TIMEAXIS-v1 (rp-final 2026-10-28, Sammy comment e10d15f0 "super clunky" + "even if you need to remove months"): the ONE x axis for
   every time chart (Data / reporter / outlet "Coverage by …" via timeChart, the bill "Milestones and coverage" chart via ctx.timeAxis).
   Replaces MONTHAXIS-v1's two loops. lo / hi = 'YYYY-MM'; xOf('YYYY-MM') = the x of that month's tick; o = {W, y0 (baseline),
   yText, minor (default true)}. Tiers by span: > 24 months = years ("2023"), small unlabeled quarter ticks; 7-24 = quarters
   ("Jan 2025", "Apr", "Jul", "Oct"; the year on January, or on the first label when no January shows); <= 6 = months. At most 8 labels
   (5 under 600 px wide), each centred under its tick with a gap; a quarter tier that would overlap or pass the cap falls back to years,
   and years thin to every 2 / 5 / 10. Text uses the chart axis style (.chart text: 11px mono, var(--ink-3)); ticks var(--line). */
const TA_MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function timeAxisPlan(lo, hi, xOf, o){
  const W = o.W, cap = W < 600 ? 5 : 8, CW = 6.7, GAP = 10, ms = [];
  for (let y = +lo.slice(0, 4), mo = +lo.slice(5, 7); y * 12 + mo <= +hi.slice(0, 4) * 12 + +hi.slice(5, 7); mo === 12 ? (y++, mo = 1) : mo++) ms.push([y, mo]);
  const n = ms.length, ym = (y, mo) => y + '-' + String(mo).padStart(2, '0');
  const fits = labs => { if (!labs.length || labs.length > cap) return false; let end = -1e9;
    for (const l of labs){ const w = l.t.length * CW, x = Math.min(Math.max(l.x, w / 2 + 1), W - w / 2 - 1); if (x - w / 2 < end + GAP) return false; end = x + w / 2; } return true; };
  const mk = (sel, txt) => { const a = ms.filter(sel), out = a.map(([y, mo], i) => ({ x: xOf(ym(y, mo)), t: txt(y, mo, i, a) })); return out; };
  const years = () => { for (const k of [1, 2, 5, 10, 20]){ const labs = mk(([y, mo]) => mo === 1 && y % k === 0, y => String(y)); if (labs.length && fits(labs)) return labs;
      if (!labs.length) break; } return n ? [{ x: xOf(ym(ms[0][0], ms[0][1])), t: String(ms[0][0]) }] : []; };
  let tier, labs;
  if (n <= 6){ tier = 'month';
    for (const k of [1, 2, 3]){ labs = mk(([y, mo], i) => i % k === 0, (y, mo, i) => mo === 1 || i === 0 ? TA_MON[mo - 1] + ' ' + y : TA_MON[mo - 1]); if (fits(labs)) break; labs = null; }
    if (!labs){ tier = 'year'; labs = years(); } }
  else if (n <= 24){ tier = 'quarter';
    labs = mk(([y, mo]) => (mo - 1) % 3 === 0, (y, mo, i, a) => mo === 1 || (i === 0 && !a.some(q => q[1] === 1)) ? TA_MON[mo - 1] + ' ' + y : TA_MON[mo - 1]);
    if (!fits(labs)){ tier = 'year'; labs = years(); } }
  else { tier = 'year'; labs = years(); }
  const minor = tier === 'year' && o.minor !== false ? ms.filter(([y, mo]) => (mo - 1) % 3 === 0).map(([y, mo]) => xOf(ym(y, mo))) : [];
  return { tier, labs: labs.map(l => ({ x: l.x, tx: Math.min(Math.max(l.x, l.t.length * CW / 2 + 1), W - l.t.length * CW / 2 - 1), t: l.t })), minor, cap };
}
function timeAxis(lo, hi, xOf, o){
  const p = timeAxisPlan(lo, hi, xOf, o), y0 = o.y0, yt = o.yText, lx = new Set(p.labs.map(l => l.x.toFixed(1)));
  let s = '<g class="taxis">';
  p.minor.forEach(x => { if (!lx.has(x.toFixed(1))) s += `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${y0}" y2="${y0 + 2.5}" stroke="var(--line)"></line>`; });
  p.labs.forEach(l => { s += `<line x1="${l.x.toFixed(1)}" x2="${l.x.toFixed(1)}" y1="${y0}" y2="${y0 + 4}" stroke="var(--line)"></line><text x="${l.tx.toFixed(1)}" y="${yt}" text-anchor="middle">${l.t}</text>`; });
  return s + '</g>';
}
function timeChart(rows, o){
  const iv = o.iv, bk = o.bk, meas = o.meas, from = o.from, pct = o.pct, showAvg = o.avgOn && !pct;
  o.avgEl.disabled = pct; o.avgEl.parentElement.style.opacity = pct ? .5 : '';
  const w = r => meas==='all' ? 1 + r.pick : 1;
  // "Show only": one issue, outlet, format and so on by itself over time; a share is then of all coverage in that period
  const only = bk==='none' ? '' : fillOnly(bk, rows, o.onlyEl);
  o.onlyEl.disabled = bk==='none'; o.onlyEl.parentElement.style.opacity = bk==='none' ? .5 : '';
  const inRange = rows.filter(r => r.year >= from);
  const lastYear = inRange.length ? Math.max(...inRange.map(r=>r.year)) : yMax;
  let buckets = allBuckets(iv, from, lastYear);
  const idx = new Map(buckets.map((b,i)=>[b,i])), grid = new Map(); let skipped = 0;
  for (const r of inRange){
    const k = bucketKey(r, iv); if (k==null){ skipped++; continue; }
    // a story counts under each of its Reach tags
    const ss = bk==='none' ? ['All stories'] : bk==='reach' ? (only ? [hasReach(r, only) ? only : '\u0000rest'] : (reachTags(r).length ? reachTags(r) : [r.reach])) : [only ? (bkVal(r, bk)===only ? only : '\u0000rest') : seriesOf(bk, bkVal(r, bk))];
    for (const s of ss){
      if (!grid.has(s)) grid.set(s, new Array(buckets.length).fill(0));
      const i = idx.get(k); if (i!=null) grid.get(s)[i] += w(r);
    }
  }
  let lastIdx = -1; grid.forEach(arr => arr.forEach((v,i)=>{ if (v && i>lastIdx) lastIdx=i; }));
  if (lastIdx >= 0){ buckets = buckets.slice(0, lastIdx+1); grid.forEach((arr,k)=>grid.set(k, arr.slice(0,lastIdx+1))); }
  const series = bk==='none' ? ['All stories'] : only ? [only] : (bk==='reach' ? REACH_ORDER : RANK[bk].slice(0,7).concat(['Other'])).filter(s => grid.has(s));
  const totals = buckets.map((_,i) => series.reduce((a,s)=>a+(grid.get(s)?.[i]||0),0));
  const denom = only ? buckets.map((_,i) => [...grid.values()].reduce((a,arr)=>a+(arr[i]||0),0)) : totals;
  const val = (s, i) => { const v = grid.get(s)?.[i]||0; return pct ? (denom[i] ? v/denom[i]*100 : 0) : v; };
  const color = s => bk==='none' ? 'var(--bar)' : s==='Other' ? 'var(--sother)' : only && colorFor(bk, s)==='var(--sother)' ? 'var(--bar)' : colorFor(bk, s);
  const earlier = rows.filter(r=>r.year>0 && r.year<from).length;
  const unit = meas==='all' ? 'stories and reprints' : 'stories';
  const win = iv==='month' ? 3 : iv==='quarter' ? 4 : 3, winLabel = iv==='month' ? '3-month average' : iv==='quarter' ? '4-quarter average' : '3-year average';
  const avg = totals.map((_,i) => i < win-1 ? null : totals.slice(i-win+1, i+1).reduce((a,b)=>a+b,0)/win);
  o.title.textContent = (pct ? `Share of coverage by ${iv}` : `Coverage by ${iv}`) + (only ? `: ${only}` : '');
  o.cap.textContent = `${fmt(totals.reduce((a,b)=>a+b,0))} ${unit} since ${from}.` + (earlier?` ${pl(earlier,'earlier story','earlier stories')} not shown.`:'') + (skipped?` ${pl(skipped,'story','stories')} dated only by year left out.`:'') + (pct ? ' Each bar adds up to 100%.' : '') + (o.capEnd || ' Click a bar to see those clips.');
  const sLab = s => s === 'Other' ? (bk === 'topic' ? 'All other issues' : 'All other') : s;   /* REVIEW4-PAGE-v1 E5: the collapsed bucket is not the real issue 'Other / roundup' */
  const lastB = buckets[buckets.length - 1], partial = !!lastB && (iv === 'year' ? lastB === TODAY.slice(0, 4) : iv === 'quarter' ? lastB === `${TODAY.slice(0, 4)}-Q${Math.ceil(+TODAY.slice(5, 7) / 3)}` : lastB === TODAY.slice(0, 7));   /* the current period is not finished */
  o.legend.innerHTML = (series.length>1 ? series.map(s=>`<span class="it"><span class="sw" style="background:${color(s)}"></span>${esc(sLab(s))}</span>`).join('') : '') + (showAvg ? `<span class="it"><span class="line"></span>${winLabel}${partial ? ' (to the last full ' + iv + ')' : ''}</span>` : '') + (partial ? `<span class="it"><span class="sw" style="background:var(--bar);opacity:.5"></span>${bucketLabel(lastB, iv)} not finished (to ${dateLabel({date: TODAY, prec: 'day', year: +TODAY.slice(0, 4)}, true)})</span>` : '') + (o.legendExtra || '');

  if (!totals.some(Boolean)){ o.chart.innerHTML = '<div class="empty">Nothing to chart for these settings.</div>'; o.chart.onclick = o.chart.onmousemove = null; o.table.innerHTML = ''; return { buckets, totals, series, grid, empty: true }; }  /* AXIS-v1 */
  const W = Math.max(300, o.chart.clientWidth || 1000), H = W < 600 ? 220 : 300, m = {l:40, r:8, t:16, b:26}, iw = W-m.l-m.r, ih = H-m.t-m.b;
  const ymax = pct ? (only ? niceMax(Math.max(...buckets.map((_,i)=>val(only,i))), 'pct') : 100) : niceMax(Math.max(...totals));  /* AXIS-v1: scaled to the data shown (a stacked share is always 100) */
  const n = buckets.length, band = iw / Math.max(1,n), bw = Math.max(1, band * (n>120 ? .9 : .72));
  const y = v => m.t + ih - (v/ymax)*ih;
  let svg = axis(`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Stories per ${iv}">`, W, H, m, ymax, pct ? '%' : '');
  { /* TIMEAXIS-v1: one helper for every interval; a bucket's months map to ticks inside its band */
    const mon = b => iv === 'month' ? [b.slice(0, 7), b.slice(0, 7)] : iv === 'quarter' ? (q => [b.slice(0, 4) + '-' + String(q * 3 - 2).padStart(2, '0'), b.slice(0, 4) + '-' + String(q * 3).padStart(2, '0')])(+b.slice(-1)) : [b.slice(0, 4) + '-01', b.slice(0, 4) + '-12'];
    const bi = new Map(buckets.map((b, i) => [iv === 'month' ? b.slice(0, 7) : iv === 'quarter' ? b : b.slice(0, 4), i]));
    const xOf = k => { const yy = k.slice(0, 4), mo = +k.slice(5, 7);
      if (iv === 'month'){ const i = bi.get(k); return m.l + (i == null ? 0 : i) * band + band / 2; }
      if (iv === 'quarter'){ const i = bi.get(yy + '-Q' + Math.ceil(mo / 3)); return m.l + (i == null ? 0 : i) * band + band * (((mo - 1) % 3) + 0.5) / 3; }
      const i = bi.get(yy); return m.l + (i == null ? 0 : i) * band + band / 2; };
    if (buckets.length) svg += timeAxis(mon(buckets[0])[0], mon(buckets[buckets.length - 1])[1], xOf, { W, y0: m.t + ih, yText: H - 8, minor: iv !== 'year' }); }
  buckets.forEach((b,i) => {
    let acc = 0; const x = m.l + i*band + (band-bw)/2;
    const segs = series.map(s => ({s, v: val(s,i)})).filter(o=>o.v>0);
    segs.forEach((o, j) => { const top = j===segs.length-1; const y0 = y(acc), y1 = y(acc+o.v); acc += o.v; svg += `<path d="${barPath(x, y0, Math.min(y1, y0-0.5), bw, top)}" fill="${color(o.s)}"${partial && i === n-1 ? ' fill-opacity=".5" stroke="var(--ink-3)" stroke-dasharray="3 2" stroke-width=".8"' : ''}></path>`; });
  });
  svg += `<line class="base" x1="${m.l}" x2="${W-m.r}" y1="${m.t+ih}" y2="${m.t+ih}"></line>`;
  if (showAvg){ let d = ''; avg.forEach((v,i) => { if (v==null || (partial && i === n-1)) return; d += `${d?'L':'M'}${(m.l + i*band + band/2).toFixed(1)},${y(v).toFixed(1)}`; }); if (d) svg += `<path class="avg" d="${d}"></path>`; }
  if (!pct && totals.some(Boolean)){ const pi = totals.indexOf(Math.max(...totals)); const px = m.l + pi*band + band/2; svg += `<text class="peak" x="${px}" y="${y(totals[pi])-5}" text-anchor="${pi > n*.85 ? 'end' : pi < n*.15 ? 'start' : 'middle'}">Peak: ${fmt(totals[pi])}</text>`; }
  if (o.extra) svg += o.extra({ buckets, iv, rows: inRange, m, W, H, ih, band, key: r => bucketKey(r, iv) });
  buckets.forEach((b,i) => { svg += `<rect class="hit" data-i="${i}" x="${m.l+i*band}" y="${m.t}" width="${band}" height="${ih}"></rect>`; });
  const el = o.chart; el.innerHTML = svg + '</svg>';
  const fv = v => pct ? Math.round(v)+'%' : fmt(v);
  el.onmousemove = e => { const t = e.target.closest('.hit'); if (!t){ hideTip(); return; } const i = +t.dataset.i;
    el.querySelectorAll('.hit.on').forEach(h=>h.classList.remove('on')); t.classList.add('on');
    const rowsH = series.map(s=>({s,v:val(s,i)})).filter(o=>o.v).sort((a,b)=>b.v-a.v);
    showTip(e, `<div class="th">${bucketLabel(buckets[i], iv)}</div>` + (series.length>1 ? rowsH.map(o=>`<div class="row"><span class="l"><span class="sw" style="background:${color(o.s)}"></span><span>${esc(sLab(o.s))}</span></span><b>${fv(o.v)}</b></div>`).join('') : '') + `<div class="row ${series.length>1?'tot':''}"><span class="l">Total</span><b>${fmt(totals[i])}</b></div>` + (showAvg && avg[i]!=null ? `<div class="row"><span class="l">${winLabel}</span><b>${avg[i].toFixed(1)}</b></div>` : '') + `<div class="foot">${o.foot || 'Click to see these clips'}</div>`); };
  el.onmouseleave = () => { hideTip(); el.querySelectorAll('.hit.on').forEach(h=>h.classList.remove('on')); };
  el.onclick = e => { const t = e.target.closest('.hit'); if (!t) return; hideTip(); const b = buckets[+t.dataset.i]; o.pick(b, iv); };
  o.table.innerHTML = `<table><thead><tr><th>${iv[0].toUpperCase()+iv.slice(1)}</th>${series.length>1?series.map(s=>`<th>${esc(s)}</th>`).join(''):''}<th>Total</th></tr></thead><tbody>${buckets.map((b,i)=> totals[i] ? `<tr><td>${bucketLabel(b,iv)}</td>${series.length>1?series.map(s=>`<td>${grid.get(s)?.[i]||''}</td>`).join(''):''}<td>${totals[i]}</td></tr>` : '').join('')}</tbody></table>`;
  if (o.quick) document.querySelectorAll('.quick [data-qv]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.qv === S.qv)));
  return { buckets, totals, series, grid };
}
const QV = {
  volume:{anBreak:'none', anMeasure:'stories', anShow:'n'}, issues:{anBreak:'topic', anMeasure:'stories', anShow:'n'},
  reach:{anBreak:'reach', anShow:'pct', anInterval:'year'}, formats:{anBreak:'fmt', anShow:'pct', anInterval:'year'},
  role:{anBreak:'role', anShow:'n'}, tone:{anBreak:'tone', anShow:'n'}, reprints:{anBreak:'none', anMeasure:'all', anShow:'n'}
};
const HB_NOUN = {pub:'more outlet', topic:'more issue', media:'more medium', fmt:'more format', reach:'more reach group', role:'more kind', author:'more reporter'};
function hbars(el, key, rows, limit, colored, order){
  const c = new Map(); rows.forEach(r => (key==='reach' ? reachTags(r) : [r[key]]).forEach(v => c.set(v, (c.get(v)||0)+1)));
  let items = order ? order.filter(k=>c.has(k)).map(k=>[k,c.get(k)]) : [...c.entries()].sort((a,b)=>b[1]-a[1]);
  const rest = items.slice(limit); items = items.slice(0, limit);
  const tot = rows.length || 1;
  barList(el, key, items.map(([k,v]) => ({k, v, label:`${fmt(v)} · ${Math.round(v/tot*100)}%`})),
    rest.length ? `Plus ${pl(rest.length, HB_NOUN[key] || 'more')} with ${pl(rest.reduce((a,b)=>a+b[1],0),'story','stories')}` : '');
}
/* FORMAT-v1: Medium x Format. One bar per Medium (its click filters Medium), with its Formats indented underneath when it has more than one (a click filters both) */
function hbarsMF(el, rows){
  const m = new Map(); rows.forEach(r => { const a = r.media || 'Not recorded', f = fmtOf(r); const e = m.get(a) || m.set(a, {n: 0, f: new Map()}).get(a); e.n++; e.f.set(f, (e.f.get(f) || 0) + 1); });
  const tot = rows.length || 1, items = [];
  [...m.entries()].sort((a, b) => b[1].n - a[1].n).slice(0, 12).forEach(([a, e]) => {
    items.push({k: a, v: e.n, label: `${fmt(e.n)} · ${Math.round(e.n / tot * 100)}%`});
    if (e.f.size > 1) [...e.f.entries()].sort((x, y) => y[1] - x[1]).forEach(([f, n]) => items.push({k: f, v: n, label: fmt(n), m: a, key: 'fmt', sub: true}));
  });
  barList(el, 'media', items, '');
}
function barList(el, key, items, foot){
  const max = Math.max(1e-9, ...items.map(i=>i.v));
  el.innerHTML = items.length ? items.map(it => `<button class="hb${it.sub ? ' hb-sub' : ''}" ${it.sub ? 'style="margin-left:18px" data-m="' + esc(it.m) + '" ' : ''}data-k="${it.key || key}" data-v="${esc(it.k)}" title="See clips: ${esc(it.k)}${it.tip?' · '+esc(it.tip):''}"><span class="hb-l">${esc(it.k)}</span><span class="hb-track"><span class="hb-fill" style="width:${it.v/max*100}%;background:var(--q${3+Math.round(it.v/max*3)})"></span></span><span class="hb-v">${it.label}</span></button>`).join('')
    + (foot ? `<div class="result-line" style="margin-top:4px">${foot}</div>` : '')
    : '<div class="empty">No stories</div>';
}
/* compare two periods */
function periods(){
  const ly = +LAST.slice(0,4), cut = LAST.slice(5), [cm, cd] = cut.split('-').map(Number), when = `${MONTHS[cm-1]} ${cd}`;
  const P = [
    {id:'ytd', label:`${ly} so far`, f: r => r.year===ly && (r.prec==='year' || r.date.slice(5) <= cut), pair:'pytd'},
    {id:'pytd', label:`${ly-1} through ${when}`, f: r => r.year===ly-1 && r.prec!=='year' && r.date.slice(5) <= cut, pair:'ytd'},
    {id:'l90', label:'Last 90 days', f: r => r.prec==='day' && r.date > addDays(TODAY,-90), pair:'p90'},
    {id:'p90', label:'The 90 days before', f: r => r.prec==='day' && r.date > addDays(TODAY,-180) && r.date <= addDays(TODAY,-90), pair:'l90'},
    {id:'l12', label:'Last 12 months', f: r => r.prec==='day' && r.date > addDays(TODAY,-365), pair:'p12'},
    {id:'p12', label:'The 12 months before', f: r => r.prec==='day' && r.date > addDays(TODAY,-730) && r.date <= addDays(TODAY,-365), pair:'l12'},
    ...YEARS.slice().reverse().filter(y=>y>=2017).map(y => ({id:'y'+y, label: y===ly ? `All of ${y} so far` : `All of ${y}`, f: r => r.year===y, pair:'y'+(y-1)}))
  ];
  return P;
}
/* REVIEW4-PAGE-v1 A2: the compare box is independent of the page Period (its own two periods decide the rows); other filters still apply */
function cmpRows(){ const k = [S.d0, S.d1]; S.d0 = S.d1 = null; let r; try { r = D.filter(x => match(x) && countable(x)); } finally { S.d0 = k[0]; S.d1 = k[1]; } return r; }
function renderCompare(){
  const rows = cmpRows();
  const P = periods(), byP = new Map(P.map(p=>[p.id,p]));
  const sa = $('#cmpA'), sb = $('#cmpB');
  if (!sa.options.length){ const o = P.map(p=>`<option value="${p.id}">${esc(p.label)}</option>`).join(''); sa.innerHTML = o; sb.innerHTML = o; sa.value = 'ytd'; sb.value = 'pytd'; }
  const A = byP.get(sa.value), B = byP.get(sb.value);
  const ra = rows.filter(A.f), rb = rows.filter(B.f);
  const stat = rs => { const rt = rs.filter(rated); return {
    n: rs.length, pick: rs.reduce((a,r)=>a+r.pick,0), named: rs.filter(r=>r.role!=='Mentioned in story').length,
    major: rs.length ? rs.filter(r=>hasReach(r,'National')||hasReach(r,'Statewide California')).length/rs.length*100 : null,
    dist: rs.filter(r=>hasReach(r,'District & Valley')).length,
    pos: rt.length ? rt.filter(r=>/positive/i.test(r.tone)).length/rt.length*100 : null, rt: rt.length }; };
  const a = stat(ra), b = stat(rb);
  const chg = (x, y, isPct) => { if (x==null || y==null) return 'Not enough rated stories'; if (isPct){ const d = Math.round(x-y); return d===0 ? 'No change' : `<span class="${d>0?'up':'down'}">${d>0?'▲':'▼'} ${Math.abs(d)} pts</span> vs. ${Math.round(y)}%`; }
    if (!y) return x ? `vs. none` : 'No change'; if (y < 5 && x !== y) return `<span class="${x>y?'up':'down'}">${x>y?'▲ +':'▼ −'}${Math.abs(x-y)}</span> vs. ${fmt(y)}`; const d = Math.round((x-y)/y*100); return d===0 ? `Same as ${fmt(y)}` : `<span class="${d>0?'up':'down'}">${d>0?'▲':'▼'} ${Math.abs(d)}%</span> vs. ${fmt(y)}`; };
  $('#cmpCap').textContent = `${A.label} (${pl(a.n,'story','stories')}) compared with ${B.label.charAt(0).toLowerCase()+B.label.slice(1)} (${pl(b.n,'story','stories')}).` + (a.n || b.n ? '' : ' Neither period has any stories.') + (S.d0 || S.d1 ? ' The Period chosen above does not change this box.' : '') + (anyFilter() && (S.q || S.flag || S.ranin || FACETS.some(f=>S.sel[f.key].size)) ? ' Filters on the Clips tab apply.' : '');
  $('#cmpKpis').innerHTML = [
    ['Stories', fmt(a.n), chg(a.n, b.n)],
    ['Reprints', fmt(a.pick), chg(a.pick, b.pick)],
    ['Named in headline or op-ed', fmt(a.named), chg(a.named, b.named)],
    ['National or statewide', a.major==null?'–':Math.round(a.major)+'%', chg(a.major, b.major, true)],
    ['District & Valley stories', fmt(a.dist), chg(a.dist, b.dist)],
    ['Average reprints per story', a.n ? (a.pick/a.n).toFixed(1) : '–', b.n ? `vs. ${(b.pick/b.n).toFixed(1)}` : ''],
    ['Positive tone', a.pos==null?'–':Math.round(a.pos)+'%', a.pos==null||b.pos==null ? `${pl(a.rt,'rated story','rated stories')}` : chg(a.pos, b.pos, true)],
    ['Outlets', fmt(new Set(ra.map(r=>r.pub)).size), chg(new Set(ra.map(r=>r.pub)).size, new Set(rb.map(r=>r.pub)).size)],
  ].map(([l,v,s]) => `<div class="k"><span class="eyebrow">${l}</span><b>${v}</b><small>${s}</small></div>`).join('');
  const ca = new Map(), cb = new Map(); ra.forEach(r=>ca.set(r.topic,(ca.get(r.topic)||0)+1)); rb.forEach(r=>cb.set(r.topic,(cb.get(r.topic)||0)+1));
  const mv = [...new Set([...ca.keys(), ...cb.keys()])].map(t => ({t, d:(ca.get(t)||0)-(cb.get(t)||0), a:ca.get(t)||0, b:cb.get(t)||0})).filter(o=>o.d).sort((x,y)=>Math.abs(y.d)-Math.abs(x.d)).slice(0,8);
  const mx = Math.max(1, ...mv.map(o=>Math.abs(o.d)));
  if ($('#cmpMovers')) $('#cmpMovers').innerHTML = mv.length ? mv.map(o => `<button class="mv hb-like" data-k="topic" data-v="${esc(o.t)}" title="${esc(o.t)}: ${o.a} vs. ${o.b}"><span class="ml">${esc(o.t)}</span><span class="neg">${o.d<0?`<i style="width:${-o.d/mx*100}%"></i>`:''}</span><span class="pos">${o.d>0?`<i style="width:${o.d/mx*100}%"></i>`:''}</span><span class="mval">${o.d>0?'+':'−'}${Math.abs(o.d)}</span></button>`).join('') + `<div class="mv-axis"><span></span><span>Fewer stories</span><span>More stories</span><span></span></div>` : '<div class="note">No change by issue between these periods.</div>';
}
function renderTravel(rows){
  const g = new Map(); rows.forEach(r => { const o = g.get(r.topic) || g.set(r.topic, {n:0,p:0}).get(r.topic); o.n++; o.p += r.pick; });
  const items = [...g.entries()].filter(([,o])=>o.n>=5).map(([k,o]) => ({k, v:o.p/o.n, label:`${(o.p/o.n).toFixed(1)} · ${pl(o.n,'story','stories')}`})).sort((a,b)=>b.v-a.v).slice(0,10);
  barList($('#travelBars'), 'topic', items);
}
function renderRel(rows){
  const mode = S.rel || 'loyal'; document.querySelectorAll('#relSeg button').forEach(b=>b.setAttribute('aria-pressed', String(b.dataset.rel===mode)));
  const g = new Map(); rows.forEach(r => { const o = g.get(r.pub) || g.set(r.pub, {n:0, ys:new Set(), first:'9'}).get(r.pub); o.n++; if (r.year) o.ys.add(r.year); if (r.date && r.date < o.first) o.first = r.date; });
  let items;
  if (mode==='loyal'){
    items = [...g.entries()].map(([k,o]) => ({k, v:o.ys.size, n:o.n, label:`${pl(o.ys.size,'year')} · ${fmt(o.n)}`})).sort((a,b)=>b.v-a.v || b.n-a.n).slice(0,10);
    $('#relCap').textContent = 'Outlets that covered Gabriel in the most different years. The second number is total stories.';
  } else {
    const cut = addDays(TODAY,-365);
    items = [...g.entries()].filter(([,o]) => o.first > cut).map(([k,o]) => ({k, v:o.n, label:`${pl(o.n,'story','stories')} · since ${MONTHS[+o.first.slice(5,7)-1]||''} ${o.first.slice(0,4)}`})).sort((a,b)=>b.v-a.v).slice(0,10);
    $('#relCap').textContent = items.length ? 'Outlets whose first story about Gabriel ran in the last 12 months.' : 'No outlets covered Gabriel for the first time in the last 12 months.';
  }
  barList($('#relBars'), 'pub', items);
}
function renderBills(rows){
  const bills = new Map(); rows.forEach(r => { if (r.prec!=='year') r.bills.forEach(b => (bills.get(b) || bills.set(b, []).get(b)).push(r)); });
  const list = [...bills.entries()].sort((a,b)=>b[1].length-a[1].length);
  if (!list.length){ $('#btls').innerHTML = '<div class="empty">No bill coverage in this view</div>'; $('#btlCap').textContent = ''; return; }
  const first = list.reduce((a,[,rs]) => rs.reduce((x,r)=> r.date < x ? r.date : x, a), '9').slice(0,7);
  const months = []; let [y, mo] = first.split('-').map(Number); const end = LAST.slice(0,7);
  while (`${y}-${String(mo).padStart(2,'0')}` <= end){ months.push(`${y}-${String(mo).padStart(2,'0')}`); mo++; if (mo>12){ mo=1; y++; } }
  const gmax = Math.max(1, ...list.map(([,rs]) => { const c = new Map(); rs.forEach(r=>{ const k=r.date.slice(0,7); c.set(k,(c.get(k)||0)+1); }); return Math.max(...c.values()); }));
  $('#btlCap').textContent = `Stories per month for each bill, on the same scale, from ${monthName(first)} to ${monthName(end)}. Click a bill to see its clips.`;
  const W = 600, H = 34;
  $('#btls').innerHTML = list.map(([b, rs]) => {
    const c = new Map(); rs.forEach(r=>{ const k=r.date.slice(0,7); c.set(k,(c.get(k)||0)+1); });
    const peak = [...c.entries()].sort((x,z)=>z[1]-x[1])[0], bw = W/months.length;
    const bars = months.map((k,i) => { const v = c.get(k); if (!v) return ''; const h = Math.max(1.5, v/gmax*(H-2)); return `<rect x="${(i*bw).toFixed(2)}" y="${(H-h).toFixed(2)}" width="${Math.max(1, bw*.8).toFixed(2)}" height="${h.toFixed(2)}" rx="1" fill="var(--bar)"><title>${monthName(k)}: ${pl(v,'story','stories')}</title></rect>`; }).join('');
    return `<button class="btl" data-k="bills" data-v="${esc(b)}"><span class="bn"><b>${b}</b>${esc(billName(b))}<span class="bs">Peak ${MONTHS[+peak[0].slice(5)-1]} ${peak[0].slice(0,4)} · ${pl(peak[1],'story','stories')}</span></span><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true"><line x1="0" x2="${W}" y1="${H-.5}" y2="${H-.5}" stroke="var(--line)"></line>${bars}</svg><span class="bv"><b>${fmt(rs.length)}</b>stories</span></button>`;
  }).join('') + `<div class="btl-axis"><span></span><span><span>${first.slice(0,4)}</span><span>${end.slice(0,4)}</span></span><span></span></div>`;
}
const DOW = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
function renderCalendar(rows){
  const dated = rows.filter(r => r.prec!=='year'), days = rows.filter(r => r.prec==='day');
  const mc = new Array(12).fill(0); dated.forEach(r => mc[+r.date.slice(5,7)-1]++);
  const dc = new Array(7).fill(0); days.forEach(r => dc[new Date(r.date+'T12:00:00Z').getUTCDay()]++);
  const top = (arr, names) => { const t = arr.reduce((a,b)=>a+b,0); const i = arr.indexOf(Math.max(...arr)); return t ? `Busiest: ${names[i]}, with ${Math.round(arr[i]/t*100)}% of stories.` : 'No dated stories.'; };
  $('#moyCap').textContent = `All years combined. ${top(mc, MONTHS_L)} Click a month to see that month in the latest year.`;
  simpleBars($('#moyChart'), mc.map((v,i) => ({k:i, v, label: MONTHS_L[i], tick: MONTHS[i]})), i => { clearAll(); const yr = [...YEARS].reverse().find(y => D.some(r=>r.year===y && +r.date.slice(5,7)===i+1)); setMonth(`${yr}-${String(i+1).padStart(2,'0')}`); go('db'); }, 'centered');
}
function renderHeat(rows){
  const from = +$('#anFrom').value, rk = $('#hmRows').value, ck = $('#hmCols').value;
  const RL = {bills:'Bills', topic:'Issues', pub:'Outlets', author:'Reporters', reach:'Reach', media:'Mediums', role:'How Gabriel appears', tone:'Tone'};
  $('#heatTitle').textContent = `${RL[rk]} by ${ck==='year' ? 'year' : 'month of the year'}`;
  const use = rows.filter(r => r.year>=from && (ck==='year' || r.prec!=='year') && (rk!=='tone' || rated(r)) && (rk!=='author' || r.authors.length) && (rk!=='bills' || r.bills.length));
  const cnt = new Map(); use.forEach(r => vals(r, rk).forEach(v => cnt.set(v, (cnt.get(v)||0)+1)));
  let keys = (rk==='reach' ? REACH_ORDER : rk==='tone' ? TONE_ORDER.slice(0,5) : rk==='author' || rk==='bills' ? [...cnt.keys()] : RANK[rk]).filter(k => cnt.has(k));
  if (rk==='pub' || rk==='author' || rk==='bills') keys = keys.sort((a,b)=>cnt.get(b)-cnt.get(a)).slice(0,20);
  const cols = ck==='year' ? YEARS.filter(y=>y>=from && use.some(r=>r.year===y)) : MONTHS.map((_,i)=>i+1);
  const colOf = r => ck==='year' ? r.year : +r.date.slice(5,7);
  const c = new Map(); let max = 1;
  use.forEach(r => vals(r, rk).forEach(x => { const k = x+'|'+colOf(r); const v = (c.get(k)||0)+1; c.set(k, v); if (v>max) max=v; }));
  const step = v => { const t = v/max; return t>.8?6: t>.6?5: t>.4?4: t>.22?3: t>.1?2:1; };
  const cl = v => ck==='year' ? v : MONTHS[v-1];
  $('#heat').innerHTML = keys.length && cols.length ? `<table><thead><tr><th></th>${cols.map(v=>`<th>${cl(v)}</th>`).join('')}</tr></thead><tbody>${keys.map(t=>`<tr><th class="rowh" title="${esc(t)}">${esc(t)}</th>${cols.map(v=>{ const n = c.get(t+'|'+v)||0; if (!n) return '<td class="z">·</td>'; const s = step(n); return `<td class="q${s} click" style="background:var(--q${s})" data-hk="${rk}" data-hv="${esc(t)}" ${ck==='year'?`data-hy="${v}"`:''} title="${esc(t)}, ${ck==='year'?v:MONTHS_L[v-1]}: ${pl(n,'story','stories')}">${n}</td>`; }).join('')}</tr>`).join('')}</tbody></table>` : '<div class="empty">No stories</div>';
}
function renderTrends(rows){
  rows = rows.filter(countable);   /* INCL-v1 / DATABASIS-v1: the Data tab follows "Include list-only mentions" on first load and after every control change */
  renderReport(rows);
  $('#anScope').innerHTML = anyFilter() ? `Showing ${fmt(rows.length)} filtered stories. <button class="linkbtn" data-clear>Show all</button>` : '';
  renderTimeChart(rows);
  renderCompare();
  hbars($('#pubBars'), 'pub', rows, 12, false);
  hbars($('#reachBars'), 'reach', rows, 11, true, REACH_ORDER);
  /* REORG-v1: the Reporters chart is cut (one line + Press desk > Pitch) */
  authorStatus();
  hbars($('#topicBars'), 'topic', rows, 21, true);
  hbarsMF($('#fmtBars'), rows);
  renderTravel(rows); renderRel(rows); renderCalendar(rows);  /* REORG-v1: Bills over time cut */
  renderHeat(rows);
}

