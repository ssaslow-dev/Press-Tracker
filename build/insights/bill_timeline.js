(function(){ "use strict";
/* Bills: stories per week for one bill, with leginfo milestones (block ins-bill_timeline), plus a table of every
   bill with coverage. Stories = Originals (ctx.D). A story is matched to the session of its bill number whose window
   (Dec 1 before the first year .. Nov 30 of the second) holds its date; else the latest session that started
   before it; else the earliest. Stories dated before the session start and month/year-only dates are counted in
   the table but not plotted (said under the chart). */
const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const KEY_KINDS = {introduced:1, floor:1, signed:1, vetoed:1, chaptered:1, died:1};
const FINAL = {signed:'Signed by Governor', vetoed:'Vetoed', chaptered:'Chaptered', died:'Died'};
let memo = null, state = null;
const TOP = 12;

const isAuthor = role => /^author/i.test(String(role||''));
const sesStart = s => { const y = +String(s).slice(0,4); return y ? `${y-1}-12-01` : '0000'; };
const sesEnd = s => { const y = +String(s).slice(5,9) || (+String(s).slice(0,4)+1); return `${y}-11-30`; };
const sesShort = s => String(s).replace(/^(\d{4})-\d\d(\d\d)$/, '$1–$2');
const dayLabel = iso => `${MON[+iso.slice(5,7)-1]} ${+iso.slice(8,10)}, ${iso.slice(0,4)}`;
function weekOf(iso){ const d = new Date(iso.slice(0,10)+'T00:00:00Z'); d.setUTCDate(d.getUTCDate() - (d.getUTCDay()+6)%7); return d.toISOString().slice(0,10); }
function addW(iso, n){ const d = new Date(iso+'T00:00:00Z'); d.setUTCDate(d.getUTCDate()+7*n); return d.toISOString().slice(0,10); }
function statusText(s){
  s = String(s||'').trim(); if (!s) return '';
  if (/^chaptered$/i.test(s)) return 'Signed into law';
  if (/^vetoed$/i.test(s)) return 'Vetoed';
  let m = s.match(/^(Assembly|Senate)\s*-\s*Died\s*-\s*(.+)$/); if (m) return `Died in ${m[1]} ${m[2]}`;
  m = s.match(/^(Assembly|Senate)\s*-\s*(.+)$/); if (m) return `Last in ${m[1]} ${m[2]}`;
  return s;
}

function build(ctx){
  if (memo && memo.v === ctx.version) return memo;
  const info = new Map();                          // bill -> [{session, title, role, status}]
  (ctx.bills() || []).forEach(b => { if (!b || !b.bill) return; (info.get(b.bill) || info.set(b.bill, []).get(b.bill)).push(b); });
  const blk = ctx.block('bill_timeline'), ms = new Map();
  if (blk && Array.isArray(blk.b)) blk.b.forEach(([bill, ses, url, ev, fin]) => ms.set(bill+'|'+ses, {url: url || `https://leginfo.legislature.ca.gov/faces/billHistoryClient.xhtml?bill_id=${String(ses).replace('-','')}0${String(bill).replace(/\s+/g,'')}`, fin: fin || '', ev: (ev||[]).map(([date, kind, label]) => ({date, kind, label}))}));
  const pickSes = (bill, date) => {
    const ss = (info.get(bill) || []).map(b => b.session).filter(Boolean).sort();
    if (!ss.length) return '';
    const d = date.length < 10 ? date.slice(0,7) + '-15' : date;
    return ss.filter(s => sesStart(s) <= d).pop() || ss[0];   // latest session started by the story's date (= agent-billstatus)
  };
  const groups = new Map();
  ctx.D.forEach(r => (r.bills || []).forEach(bill => {
    if (!r.date) return;
    const ses = pickSes(bill, r.date), k = bill+'|'+ses;
    (groups.get(k) || groups.set(k, {bill, ses, rs: []}).get(k)).rs.push(r);
  }));
  const list = [...groups.values()].map(g => {
    const inf = (info.get(g.bill) || []).find(b => b.session === g.ses) || {};
    const start = g.ses ? sesStart(g.ses) : '0000';
    const plot = [], early = [], vague = [];
    g.rs.forEach(r => r.prec !== 'day' || r.date.length < 10 ? vague.push(r) : r.date < start ? early.push(r) : plot.push(r));
    const wk = new Map(); plot.forEach(r => { const w = weekOf(r.date); (wk.get(w) || wk.set(w, []).get(w)).push(r); });
    let peak = null; [...wk.entries()].sort((a,b) => a[0] < b[0] ? -1 : 1).forEach(([w, rs]) => { if (!peak || rs.length > peak.n) peak = {w, n: rs.length}; });
    const m = ms.get(g.bill+'|'+g.ses) || null;
    const fin = m && m.ev.filter(e => FINAL[e.kind]).pop();
    return { key: g.bill+'|'+g.ses, bill: g.bill, ses: g.ses, title: String(inf.title||'').replace(/\.$/,''), role: inf.role || '',
      author: isAuthor(inf.role), status: (m && m.fin) || (fin ? FINAL[fin.kind] : statusText(inf.status)), n: g.rs.length,
      plot, early, vague, wk, peak, ms: m };
  }).sort((a,b) => b.n - a.n || (a.bill < b.bill ? -1 : 1));
  memo = {v: ctx.version, list, hasBlock: !!blk};
  return memo;
}

function chart(ctx, host, b, range){
  const W = Math.max(300, host.clientWidth || 700), small = W < 600, H = small ? 220 : 270;
  const m = {l: 36, r: 8, t: 40, b: 24}, iw = W-m.l-m.r, ih = H-m.t-m.b;
  const ev = b.ms ? b.ms.ev.filter(e => e.kind !== 'other') : [];
  let lo = null, hi = null; const ext = d => { if (!d) return; const w = weekOf(d); if (!lo || w < lo) lo = w; if (!hi || w > hi) hi = w; };
  b.plot.forEach(r => ext(r.date)); ev.forEach(e => ext(e.date));
  if (range === 'session' && b.ses){ const s = weekOf(sesStart(b.ses)), e = weekOf(sesEnd(b.ses)); if (lo < s) lo = s; if (hi > e) hi = e; }
  if (!lo){ host.innerHTML = '<div class="empty">No day-dated stories to plot for this bill.</div>'; return {weeks: []}; }
  const weeks = []; for (let w = lo; w <= hi; w = addW(w, 1)) weeks.push(w);
  const counts = weeks.map(w => (b.wk.get(w) || []).length);
  const ymax = ctx.niceMax(Math.max(1, ...counts)), band = iw / weeks.length;
  const bw = Math.min(24, Math.max(1, band - (band > 5 ? 2 : band > 2.5 ? 1 : 0.3)));
  const y = v => m.t + ih - (v/ymax)*ih, xw = w => m.l + ((Date.parse(w) - Date.parse(lo)) / 6048e5) * band;
  const xd = d => xw(weekOf(d)) + band * (((new Date(d+'T00:00:00Z').getUTCDay()+6)%7 + 0.5) / 7);
  let svg = ctx.axis(`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${ctx.esc(b.bill)} stories per week">`, W, H, m, ymax);
  counts.forEach((v, i) => { if (v) svg += `<path d="${ctx.barPath(m.l + i*band + (band-bw)/2, y(0), y(v), bw, true)}" fill="var(--bar)"></path>`; });
  svg += `<line class="base" x1="${m.l}" x2="${W-m.r}" y1="${y(0)}" y2="${y(0)}"></line>`;
  // time labels: months for short spans, else years
  const months = weeks.length <= 70, step = months ? Math.max(1, Math.ceil(weeks.length / 4.3 / Math.max(2, iw/70))) : 1;
  let lastLab = -1e9;
  for (let d = lo.slice(0,7)+'-01'; d <= hi; ){
    const yy = +d.slice(0,4), mo = +d.slice(5,7);
    if (d >= lo && (months ? (mo-1) % step === 0 : mo === 1)){
      const x = xd(d), t = months ? (mo === 1 || lastLab < 0 ? `${MON[mo-1]} ${yy}` : MON[mo-1]) : String(yy);
      if (x - lastLab > (months ? 44 : 30) && x < W - m.r - 10){ svg += `<text x="${x}" y="${H-6}">${t}</text><line x1="${x}" x2="${x}" y1="${y(0)}" y2="${y(0)+4}" stroke="var(--line)"></line>`; lastLab = x; }
    }
    d = mo === 12 ? `${yy+1}-01-01` : `${yy}-${String(mo+1).padStart(2,'0')}-01`;
  }
  if (!months && lastLab < 0) svg += `<text x="${m.l}" y="${H-6}">${lo.slice(0,4)}</text>`;
  // milestones: dashed rules for key kinds, dots for committee votes; labels for introduced, last floor vote, final action
  const shown = ev.filter(e => weekOf(e.date) >= lo && weekOf(e.date) <= hi);
  const lastFloor = shown.filter(e => e.kind === 'floor').pop(), rows = [-1e9, -1e9];
  shown.forEach((e, i) => {
    const x = xd(e.date).toFixed(1);
    if (KEY_KINDS[e.kind]) svg += `<line x1="${x}" x2="${x}" y1="${m.t-14}" y2="${y(0)}" stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"></line>`;
    else svg += `<circle cx="${x}" cy="${m.t-8}" r="3.5" fill="var(--ink-3)" stroke="var(--panel)" stroke-width="2"></circle>`;
    const lab = e.kind === 'introduced' ? 'Introduced' : FINAL[e.kind] ? FINAL[e.kind] : e === lastFloor ? 'Final floor vote' : '';
    if (lab){
      const tw = lab.length * 6.3 + 6, right = +x + tw > W - m.r, lx = right ? +x - tw : +x;
      const row = rows.findIndex(end => lx > end + 4);
      if (row >= 0){ rows[row] = lx + tw; svg += `<text class="ms" x="${right ? +x-3 : +x+3}" y="${row ? 26 : 12}" text-anchor="${right?'end':'start'}" fill="var(--ink-2)" style="font-size:var(--fs-xs)">${lab}</text>`; }
    }
  });
  weeks.forEach((w, i) => svg += `<rect class="hit" data-w="${i}" x="${m.l+i*band}" y="${m.t}" width="${band}" height="${ih}"></rect>`);
  shown.forEach((e, i) => { const x = xd(e.date); svg += `<rect class="hit ms-hit" data-m="${i}" x="${x-6}" y="0" width="12" height="${m.t}"></rect>`; });
  host.innerHTML = svg + '</svg>';
  return {weeks, shown};
}

function weekList(ctx, b, w){
  const rs = (b.wk.get(w) || []).slice().sort((a,c) => a.date < c.date ? -1 : a.date > c.date ? 1 : String(a.outlet).localeCompare(c.outlet));
  if (!rs.length) return `<div class="cap">No stories the week of ${dayLabel(w)}.</div>`;
  return `<h3 class="bt-wh">Week of ${dayLabel(w)} · ${ctx.pl(rs.length,'story','stories')}</h3><ul class="bt-wl">${rs.map(r =>
    `<li><button class="linkbtn" data-open="${ctx.esc(r.id)}">${ctx.esc(r.hl || r.hl_en || '(no headline)')}</button><span class="bt-m">${ctx.esc(r.outlet)} · ${ctx.esc(ctx.dateLabel(r))}</span></li>`).join('')}</ul>`;
}

function render(el, ctx){
  const M = build(ctx), list = M.list;
  if (!list.length){ el.innerHTML = '<div class="in-sec"><div class="card pad"><div class="empty">No stories are tagged with a bill yet.</div></div></div>'; return; }
  const p = ctx.params || {};
  const want = p.bill ? String(p.bill).toUpperCase().replace(/^([A-Z]+)\s*-?\s*/, '$1 ') : '';
  let b = want ? list.find(x => x.bill === want && (!p.s || x.ses === p.s)) : (list.find(x => x.author) || list[0]);
  state = {range: p.range === 'session' ? 'session' : 'all', week: null};
  const opts = list.map(x => `<option value="${ctx.esc(x.key)}"${b && x.key === b.key ? ' selected' : ''}>${ctx.esc(x.bill)}${list.some(o => o !== x && o.bill === x.bill) ? ` (${sesShort(x.ses)})` : ''} · ${ctx.esc(x.title || '')}${x.author ? '' : ' (coauthored)'} · ${ctx.fmt(x.n)}</option>`).join('');
  const peakTxt = x => x.peak ? `${dayLabel(x.peak.w)} (${x.peak.n})` : '—';
  el.innerHTML = `<div class="in-sec">
  <div class="card chartcard">
    <h2 class="sec">Coverage over a bill's life</h2>
    <div class="cap">Stories per week mentioning the bill, with its LegInfo milestones. Hover a week for counts; click it to list that week's stories.</div>
    <div class="an-controls"><label>Bill<select class="sel bt-pick">${want && !b ? '<option value="" selected>—</option>' : ''}${opts}</select></label>
      <div class="seg bt-range" role="group" aria-label="Date range"><button data-r="all" aria-pressed="${state.range==='all'}">All dates</button><button data-r="session" aria-pressed="${state.range==='session'}">Session only</button></div></div>
    <div class="bt-head"></div><div class="bt-chart chart"></div><div class="bt-foot"></div>
    <div class="bt-week"></div>
  </div>
  <div class="card pad">
    <h2 class="sec">Bills at a glance</h2>
    <div class="cap">Bills with coverage, most covered first. Final status from LegInfo. Click a row to chart it.</div>
    <div class="tablewrap bt-tw"><table class="db bt-tab"><thead><tr><th>Bill</th><th class="t">Title</th><th>Final status</th><th class="num">Stories</th><th>Peak week</th></tr></thead><tbody>${list.map((x, i) =>
      `<tr class="click${i >= TOP ? ' bt-more' : ''}" data-k="${ctx.esc(x.key)}" tabindex="0"${b && x.key === b.key ? ' aria-current="true"' : ''}><td class="nw"><b>${ctx.esc(x.bill)}</b><div class="bt-m">${ctx.esc(sesShort(x.ses))}${x.author ? '' : ' · coauthored'}</div></td><td class="t">${ctx.esc(x.title)}</td><td>${ctx.esc(x.status || '—')}</td><td class="num">${ctx.fmt(x.n)}</td><td class="nw">${peakTxt(x)}</td></tr>`).join('')}</tbody></table></div>${list.length > TOP ? `<button class="linkbtn bt-all" aria-expanded="false">Show all ${list.length} bills</button>` : ''}
  </div></div>
  <style>.in-view[data-in="bill_timeline"] .bt-chart svg{display:block;width:100%;height:auto}
  .in-view[data-in="bill_timeline"] .bt-head{display:flex;flex-wrap:wrap;gap:4px 16px;margin:6px 0 4px;color:var(--ink-2);font-size:var(--fs-md)}
  .in-view[data-in="bill_timeline"] .bt-head b{color:var(--ink)}
  .in-view[data-in="bill_timeline"] .bt-foot{color:var(--ink-3);font-size:var(--fs-sm);margin-top:6px;display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center}
  .in-view[data-in="bill_timeline"] .bt-m{color:var(--ink-3);font-size:var(--fs-sm)}
  .in-view[data-in="bill_timeline"] .bt-wh{font-size:var(--fs-md);margin:14px 0 6px;color:var(--ink)}
  .in-view[data-in="bill_timeline"] .bt-wl{list-style:none;margin:0;padding:0;max-height:320px;overflow:auto}
  .in-view[data-in="bill_timeline"] .bt-wl li{padding:5px 0;border-top:1px solid var(--line-2);display:flex;flex-direction:column;gap:1px}
  .in-view[data-in="bill_timeline"] .bt-wl .linkbtn{text-align:left}
  .in-view[data-in="bill_timeline"] .bt-tab tr[aria-current] td{background:var(--panel-2)}
  .in-view[data-in="bill_timeline"] .bt-tab thead th{position:static;padding:8px 10px}
  .in-view[data-in="bill_timeline"] .bt-tab td{padding:7px 10px;border-bottom:1px solid var(--line-2);vertical-align:top}
  .in-view[data-in="bill_timeline"] .bt-tab:not(.all) tr.bt-more:not([aria-current]){display:none}
  .in-view[data-in="bill_timeline"] .bt-all{margin-top:8px}
  .in-view[data-in="bill_timeline"] .bt-tab td.nw{white-space:nowrap}
  .in-view[data-in="bill_timeline"] .bt-tab .num{text-align:right}
  .in-view[data-in="bill_timeline"] .bt-pick{width:100%;max-width:560px;min-width:0;text-overflow:ellipsis}
  .in-view[data-in="bill_timeline"] .an-controls{flex-wrap:wrap}
  .in-view[data-in="bill_timeline"] .an-controls label{flex:1 1 260px;max-width:100%;min-width:0;display:flex;align-items:center;gap:6px}
  .in-view[data-in="bill_timeline"] .bt-range button{white-space:nowrap}
  .in-view[data-in="bill_timeline"] .bt-tw{overflow-x:auto;max-width:100%}
  @media (max-width:600px){.in-view[data-in="bill_timeline"] .bt-tab .t{display:none}}
  .in-view[data-in="bill_timeline"] details.dt{margin-top:8px}</style>`;
  const host = el.querySelector('.bt-chart');
  let geo = {weeks: [], shown: []};
  const draw = () => {
    const head = el.querySelector('.bt-head'), foot = el.querySelector('.bt-foot'), wk = el.querySelector('.bt-week');
    wk.innerHTML = ''; state.week = null;
    if (!b){ head.innerHTML = ''; foot.innerHTML = ''; host.innerHTML = `<div class="empty">No stories are tagged ${ctx.esc(want)}.</div>`; return; }
    const url = b.ms && b.ms.url;
    head.innerHTML = `<span><b>${ctx.esc(b.bill)}</b> ${ctx.esc(b.title)} · ${ctx.esc(sesShort(b.ses))} session</span><span>${ctx.esc(b.status || 'Status unknown')}</span><span><b>${ctx.fmt(b.n)}</b> ${b.n === 1 ? 'story' : 'stories'}${b.peak ? ` · peak week ${dayLabel(b.peak.w)} (${b.peak.n})` : ''}</span>`;
    geo = chart(ctx, host, b, state.range);
    const notes = [];
    if (!M.hasBlock) notes.push('Milestones not loaded yet.');
    else if (!b.ms) notes.push('No LegInfo milestones for this bill yet.');
    else notes.push(`<span class="legend"><span class="it"><svg width="14" height="12" aria-hidden="true"><line x1="7" x2="7" y1="0" y2="12" stroke="var(--ink-3)" stroke-dasharray="3 3"></line></svg>Introduced, floor vote, final action</span><span class="it"><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="3.5" fill="var(--ink-3)"></circle></svg>Committee vote</span></span>`);
    if (b.early.length) notes.push(`<span>Not plotted: <button class="linkbtn" data-list="early">${ctx.pl(b.early.length,'story','stories')} dated before this session</button></span>`);
    if (b.vague.length) notes.push(`<span>Not plotted: <button class="linkbtn" data-list="vague">${ctx.pl(b.vague.length,'story','stories')} dated only to the month or year</button></span>`);
    notes.push(`<button class="linkbtn" data-clips>See all in Clips</button>`);
    if (url) notes.push(`<span class="lkw">${ctx.cpBtn ? ctx.cpBtn(url) : ''}<a class="linkbtn" href="${ctx.esc(url)}" target="_blank" rel="noopener">LegInfo history</a></span>`);  // LINKUI-v1
    foot.innerHTML = notes.join(' ');
    const old = el.querySelector('details.bt-ms'); if (old) old.remove();
    if (b.ms && b.ms.ev.length){
      const evs = b.ms.ev;
      foot.insertAdjacentHTML('afterend', `<details class="dt bt-ms"><summary>Show the milestones (${evs.length})</summary><table><tbody>${evs.map(e => `<tr><td class="nw">${dayLabel(e.date)}</td><td>${ctx.esc(e.label)}</td><td class="num">${ctx.fmt((b.wk.get(weekOf(e.date)) || []).length)} that week</td></tr>`).join('')}</tbody></table></details>`);
    }
  };
  draw();
  const select = key => { const nb = list.find(x => x.key === key); if (!nb) return; b = nb;
    el.querySelector('.bt-pick').value = key; el.querySelectorAll('.bt-tab tr[data-k]').forEach(tr => tr.toggleAttribute('aria-current', tr.dataset.k === key));
    ctx.setParams(Object.assign({bill: b.bill}, list.some(o => o !== b && o.bill === b.bill) ? {s: b.ses} : {}, state.range === 'session' ? {range: 'session'} : {}));
    draw(); };
  el.querySelector('.bt-pick').addEventListener('change', e => select(e.target.value));
  el.onclick = e => {
    const t = e.target;
    const r = t.closest('.bt-range button'); if (r){ state.range = r.dataset.r; el.querySelectorAll('.bt-range button').forEach(x => x.setAttribute('aria-pressed', x === r)); if (b) select(b.key); return; }
    const o = t.closest('[data-open]'); if (o){ ctx.openStory(o.dataset.open); return; }
    if (t.closest('[data-clips]')){ ctx.clips({bills: b.bill}); return; }
    const l = t.closest('[data-list]'); if (l){ const rs = b[l.dataset.list]; el.querySelector('.bt-week').innerHTML = `<h3 class="bt-wh">${ctx.esc(l.textContent)}</h3><ul class="bt-wl">${rs.map(r => `<li><button class="linkbtn" data-open="${ctx.esc(r.id)}">${ctx.esc(r.hl || r.hl_en || '(no headline)')}</button><span class="bt-m">${ctx.esc(r.outlet)} · ${ctx.esc(ctx.dateLabel(r))}</span></li>`).join('')}</ul>`; return; }
    const h = t.closest('.hit[data-w]'); if (h && b){ const w = geo.weeks[+h.dataset.w]; if ((b.wk.get(w)||[]).length){ el.querySelector('.bt-week').innerHTML = weekList(ctx, b, w); } return; }
    const ab = t.closest('.bt-all'); if (ab){ const tb = el.querySelector('.bt-tab'), on = tb.classList.toggle('all'); ab.setAttribute('aria-expanded', on); ab.textContent = on ? `Show top ${TOP}` : `Show all ${list.length} bills`; return; }
    const tr = t.closest('.bt-tab tr[data-k]'); if (tr){ select(tr.dataset.k); el.querySelector('.bt-chart').scrollIntoView({block: 'nearest'}); }
  };
  el.onkeydown = e => { if (e.key === 'Enter'){ const tr = e.target.closest && e.target.closest('.bt-tab tr[data-k]'); if (tr) select(tr.dataset.k); } };
  el.onmousemove = e => {
    const t = e.target.closest && e.target.closest('.hit'); if (!t || !b){ ctx.hideTip(); return; }
    if (t.dataset.m != null){ const ev = geo.shown[+t.dataset.m]; ctx.showTip(e, `<div class="th">${ctx.esc(ev.label)}</div><div class="row"><span class="l">Date</span><b>${dayLabel(ev.date)}</b></div>`); return; }
    const w = geo.weeks[+t.dataset.w], n = (b.wk.get(w) || []).length;
    const msw = geo.shown.filter(ev => weekOf(ev.date) === w).map(ev => `<div class="row"><span class="l">${dayLabel(ev.date).replace(/, \d{4}$/,'')}</span><b>${ctx.esc(ev.label)}</b></div>`).join('');
    ctx.showTip(e, `<div class="th">Week of ${dayLabel(w)}</div><div class="row"><span class="l">Stories</span><b>${ctx.fmt(n)}</b></div>${msw}${n ? '<div class="foot">Click to list these stories</div>' : ''}`);
  };
  el.onmouseleave = () => ctx.hideTip();
}

AJGInsights.register({ id: 'bill_timeline', label: 'Bills', render, destroy(){ memo = null; } });
})();
