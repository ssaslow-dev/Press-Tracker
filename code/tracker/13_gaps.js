/* ---------- coverage gaps: who and what covered him before this period but not during it ---------- */
function renderGaps(){
  const norm = d => d.length === 4 ? d + '-01-01' : d.length === 7 ? d + '-01' : d;
  const all = !S.d0, start = all ? addDays(TODAY, -90) : norm(S.d0), end = S.d1 && S.d1 < TODAY ? S.d1 : TODAY, before = addDays(start, -730);
  const [d0, d1] = [S.d0, S.d1]; S.d0 = S.d1 = null; const base = D.filter(r => match(r)); S.d0 = d0; S.d1 = d1;
  const cur = base.filter(r => r.date >= start && r.date <= end), prev = base.filter(r => r.date >= before && r.date < start && r.prec !== 'year');
  $('#gapCap').textContent = `Compares ${all ? 'the last 90 days' : 'this period'} with the two years before it${anyFilter() && (S.q || FACETS.some(f => S.sel[f.key].size)) ? ', within your filters' : ''}.`;
  const last = l => l.reduce((a, r) => r.date > a.date ? r : a);
  const group = (rows, keys) => { const m = new Map(); rows.forEach(r => keys(r).forEach(k => k && (m.get(k) || m.set(k, []).get(k)).push(r))); return m; };
  const bar = (k, v, l, max, label) => `<button type="button" class="hb" data-gk="${k}" data-gv="${esc(v)}" title="See all clips: ${esc(v)}"><span class="hb-l">${esc(v)}</span><span class="hb-track"><span class="hb-fill" style="width:${l/max*100}%;background:var(--q3)"></span></span><span class="hb-v gap-v">${label}</span></button>`;
  const quiet = (keys, min) => { const p = group(prev, keys), c = group(cur, keys); return [...p.entries()].filter(([k, l]) => l.length >= min && !c.has(k)).sort((a,b) => b[1].length - a[1].length || last(b[1]).date.localeCompare(last(a[1]).date)); };
  const lastLbl = l => `${fmt(l.length)} before · last ${dateLabel(last(l))}`;
  const pubs = quiet(r => [r.media !== 'Wire' ? r.pub : ''], 3).slice(0, 10);
  $('#gapPubs').innerHTML = pubs.length ? pubs.map(([o, l]) => bar('pub', o, l.length, pubs[0][1].length, lastLbl(l))).join('') : '<div class="note">Every outlet with 3 or more earlier stories also covered him in this period.</div>';
  const home = group(base.filter(r => hasReach(r, 'District & Valley')), r => [r.pub]), cg = group(cur, r => [r.pub]);
  const hl = [...home.entries()].map(([o, l]) => [o, l, (cg.get(o) || []).length]).sort((a,b) => (a[2] > 0) - (b[2] > 0) || b[1].length - a[1].length).slice(0, 12), hm = Math.max(1, ...hl.map(x => x[1].length));
  $('#gapHome').innerHTML = hl.length ? hl.map(([o, l, n]) => bar('pub', o, l.length, hm, n ? `${fmt(n)} this period` : `<b>none this period</b> · last ${dateLabel(last(l))}`)).join('') : '<div class="note">No district-area outlets in the log.</div>';
  const cq = quiet(r => countiesOf(r), 1).slice(0, 10);
  $('#gapCounties').innerHTML = cq.length ? cq.map(([c, l]) => bar('county', c, l.length, cq[0][1].length, lastLbl(l))).join('') : '<div class="note">Every county with earlier local coverage also had some in this period.</div>';
  const iq = quiet(r => [r.topic], 3).slice(0, 10);
  $('#gapIssues').innerHTML = iq.length ? iq.map(([t, l]) => bar('topic', t, l.length, iq[0][1].length, lastLbl(l))).join('') : '<div class="note">Every issue with 3 or more earlier stories also drew coverage in this period.</div>';
  const nq = pubs.length + hl.filter(x => !x[2]).length;
  $('#hGap').textContent = `${pl(pubs.length,'regular outlet')} and ${pl(hl.filter(x => !x[2]).length,'district-area outlet')} haven’t covered him ${all ? 'in the last 90 days' : 'in this period'}${cq.length ? `, and ${pl(cq.length,'county','counties')} with earlier local coverage went quiet` : ''}.`;
  if (!nq && !cq.length && !iq.length) $('#hGap').textContent = 'No gaps: every regular outlet, county and issue drew coverage in this period.';
}
/* gap bars open Clips on every date, since the point is the earlier coverage */
['#gapPubs','#gapHome','#gapCounties','#gapIssues'].forEach(id => $(id).addEventListener('click', e => { const b = e.target.closest('[data-gk]'); if (!b) return;
  FACETS.forEach(f => S.sel[f.key].clear()); S.q = ''; $('#q').value = ''; S.flag = ''; S.ranin = ''; applyWhen('all');
  S.sel[b.dataset.gk].add(b.dataset.gv); S.openFacets.add(b.dataset.gk); S.sort = { key: 'date', dir: -1 }; go('db'); toast(`Showing all ${b.dataset.gv} clips`); }));
