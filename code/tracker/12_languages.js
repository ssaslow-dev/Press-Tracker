/* ---------- coverage in other languages ---------- */
function renderEthnic(rows){
  const own = new Map(), pubs = new Map();
  rows.forEach(r => { if (!r.lang) return; own.set(r.lang, (own.get(r.lang)||0)+1); const o = r.pub || r.outlet; pubs.set(o, (pubs.get(o)||0)+1); });
  const langs = [...own.entries()].sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0])), n = langs.reduce((a, x) => a + x[1], 0);
  const pct = x => rows.length ? Math.round(x / rows.length * 100) : 0;
  $('#hEth').textContent = n ? `${pl(n,'story','stories')} (${pct(n)}% of the period) ran in ${pl(langs.length,'language')} other than English${langs.length > 1 ? `, most in ${langs[0][0]} and ${langs[1][0]}` : `, all in ${langs[0][0]}`}.` : 'No stories in other languages in this period.';
  const max = langs.length ? langs[0][1] : 1;
  $('#ethBars').innerHTML = langs.map(([k, c]) => `<button type="button" class="hb" data-k="lang" data-v="${esc(k)}" title="See ${esc(k)} clips"><span class="hb-l">${esc(k)}</span><span class="hb-track"><span class="hb-fill" style="width:${c/max*100}%;background:var(--bar)"></span></span><span class="hb-v">${fmt(c)}</span></button>`).join('') || '<div class="note">None in this period.</div>';
  const tp = [...pubs.entries()].sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0])).slice(0, 8), pm = tp.length ? tp[0][1] : 1;
  $('#ethPubs').innerHTML = tp.map(([o, c]) => `<button type="button" class="hb" data-k="pub" data-v="${esc(o)}" title="See clips from ${esc(o)}"><span class="hb-l">${esc(o)}</span><span class="hb-track"><span class="hb-fill" style="width:${c/pm*100}%;background:var(--bar)"></span></span><span class="hb-v">${fmt(c)}</span></button>`).join('') || '<div class="note">None in this period.</div>';
  // share by quarter over the last three years, from every story, so a short period still has context
  const qk = d => `${d.slice(0,4)}-Q${Math.ceil(+d.slice(5,7)/3)}`, nowQ = qk(TODAY), qs = [];
  for (let y = +TODAY.slice(0,4) - 2; y <= +TODAY.slice(0,4); y++) for (let q = 1; q <= 4; q++){ const k = `${y}-Q${q}`; if (k <= nowQ) qs.push(k); }
  const tot = new Map(), oth = new Map();
  D.forEach(r => { if (r.prec === 'year' || r.date < qs[0].slice(0,4)) return; const k = qk(r.date); tot.set(k, (tot.get(k)||0)+1); if (r.lang) oth.set(k, (oth.get(k)||0)+1); });
  const sh = qs.map(k => [k, tot.get(k) ? (oth.get(k)||0) / tot.get(k) : 0, oth.get(k)||0, tot.get(k)||0]), sm = Math.max(.01, ...sh.map(x => x[1]));
  $('#ethTrendCap').textContent = 'Share of all stories that ran in a language other than English, by quarter over the last three years. Uses every story, not just this period. The last bar is a quarter still in progress.';
  $('#ethTrend').innerHTML = sh.map(([k, f, e, t]) => `<div class="eth-col${k === nowQ ? ' now' : ''}" title="${k.replace('-',' ')}: ${fmt(e)} of ${pl(t,'story','stories')}${k === nowQ ? ' (quarter not finished; to ' + TODAY + ')' : ''}"><span class="v">${t ? (f > 0 && f < .005 ? '<1' : Math.round(f*100))+'%' : '–'}</span><span class="bar" style="height:${Math.max(2, Math.round(f/sm*64))}px;flex:none"></span><span class="k">${k.slice(2).replace('-',' ')}</span></div>`).join('');
  const latest = rows.filter(r => r.lang).sort((a,b) => b.date.localeCompare(a.date)).slice(0, 6);
  if ($('#ethLatest')) $('#ethLatest').innerHTML = latest.length ? latest.map(r => clipItem(r)).join('') : '<div class="note">None in this period.</div>';
}
