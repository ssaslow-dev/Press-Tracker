/* ---------- report: one period, a written brief, then the sections ---------- */
function periodLabel(){ if (S.when==='custom') return S.whenLabel; if (S.when==='all') return `all coverage since ${YEARS[0]}`; const w = WHEN.find(x=>x[0]===S.when); return w ? w[1].replace(/^Last/,'the last') : ''; }
const joinL = a => a.length < 2 ? (a[0]||'') : a.slice(0,-1).join(', ') + ' and ' + a[a.length-1];
function priorRows(){
  let p0 = null, p1 = null, label = '';
  if (/^\d+$/.test(S.when)){ const n = +S.when; p0 = addDays(TODAY, -(2*n - 1)); p1 = addDays(TODAY, -n); label = n===365 ? 'the 12 months before' : `the ${n} days before`; }
  else if (S.when[0]==='y'){ const y = +S.when.slice(1); p0 = String(y-1); if (y===yMax){ p1 = `${y-1}-${LAST.slice(5)}`; label = `${y-1} through ${MONTHS[+LAST.slice(5,7)-1]} ${+LAST.slice(8)}`; } else { p1 = `${y-1}-99`; label = String(y-1); } }
  else if (S.when==='custom' && /^\d{4}-\d{2}-\d{2}$/.test(S.d0||'') && /^\d{4}-\d{2}-\d{2}$/.test(S.d1||'')){ const n = Math.round((new Date(S.d1) - new Date(S.d0)) / 864e5) + 1; p0 = addDays(S.d0, -n); p1 = addDays(S.d0, -1); label = `the ${pl(n,'day')} before`; }
  else if (S.when==='custom' && S.d0 && /^\d{4}-\d{2}$/.test(S.d0)){ let y = +S.d0.slice(0,4), m = +S.d0.slice(5) - 1; if (!m){ m = 12; y--; } const k = `${y}-${String(m).padStart(2,'0')}`; p0 = k; p1 = k+'-99'; label = monthName(k); }
  else return null;
  const keep = [S.d0, S.d1]; S.d0 = p0; S.d1 = p1; const rows = D.filter(r => match(r)); [S.d0, S.d1] = keep;
  return { rows, label };
}
function filterDesc(){
  const out = []; if (S.q) out.push(`search “${S.q}”`);
  FACETS.forEach(f => { if (S.sel[f.key].size) out.push(`${f.label}: ${[...S.sel[f.key]].join(', ')}`); });
  if (S.saved!=='all') out.push(S.saved==='yes' ? 'with a saved copy' : 'without a saved copy');
  if (S.flag) out.push(FLAGS[S.flag].label);
  if (S.ranin) out.push(`ran in ${S.ranin}`);
  return out.join('; ');
}
function briefOf(rows){
  const n = rows.length, picks = rows.reduce((a,r)=>a+r.pick,0), L = {};
  const pr = priorRows();
  let vol = `${pl(n,'story','stories')} mentioned Gabriel${picks ? `, plus ${pl(picks,'reprint')} in other outlets` : ''}.`;
  if (pr && pr.rows.length){ const d = Math.round((n-pr.rows.length)/pr.rows.length*100); vol += ` That is ${d===0 ? 'level with' : Math.abs(d)+'% '+(d>0?'more than':'fewer than')} ${pr.label} (${fmt(pr.rows.length)}).`; }
  L.vol = vol;
  const cnt = key => { const c = new Map(); rows.forEach(r => c.set(r[key], (c.get(r[key])||0)+1)); return [...c.entries()].sort((a,b)=>b[1]-a[1]); };
  const tp = cnt('topic').slice(0,3);
  L.issues = tp.length ? `Coverage was led by ${joinL(tp.map(([k,c]) => `${k} (${c})`))}.` : '';
  const bc = new Map([...billGroups(rows)].map(([k, rs]) => [k, rs.length]));  /* REORG-v1: split by session */
  const tb = [...bc.entries()].sort((a,b)=>b[1]-a[1]).slice(0,3);
  L.bills = tb.length ? `The bills most in the news were ${joinL(tb.map(([b,c]) => `${billLabel(b)} (${c})`))}.` : '';
  const hd = rows.filter(r=>r.role==='Named in headline').length, op = rows.filter(r=>r.role==='Op-ed by Gabriel').length;
  L.heads = n ? `${pl(hd,'story','stories')} named him in the headline${op ? ` and ${pl(op,'op-ed')} ran under his name` : ''}.` : '';
  const maj = rows.filter(r => hasReach(r,'National') || hasReach(r,'Statewide California')).length, po = cnt('pub').slice(0,3);
  L.reach = n ? `${Math.round(maj/n*100)}% ran in national or statewide outlets. The most frequent outlets were ${joinL(po.map(([k,c]) => `${k} (${c})`))}.` : '';
  const tr = rows.filter(rated);
  if (tr.length){ const pos = tr.filter(r=>/positive/i.test(r.tone)).length, neg = tr.filter(NEG); const ln = neg.sort((a,b)=>b.date.localeCompare(a.date))[0];
    L.tone = `${Math.round(pos/tr.length*100)}% positive and ${Math.round(neg.length/tr.length*100)}% negative across ${pl(tr.length,'rated story','rated stories')}.${ln ? ` The latest negative story was “${ln.hl}” (${ln.pub}, ${dateLabel(ln)}).` : ''}`; }
  else L.tone = n ? 'No stories in this period have a tone rating yet.' : '';
  const ar = authorRank(rows).filter(a => (AKIND.get(authorKey(a)) || 'person') === 'person').slice(0,3)  /* REORG-v1: people only */.map(a => [a, rows.filter(r => (r.authors||[]).includes(a)).length]);
  L.who = ar.length && ar[0][1] < 2 ? 'No reporter has more than one story in this period.' : ar.length ? `Reporters with the most stories: ${joinL(ar.map(([a,c]) => `${a} (${c})`))}. Authors are known only for stories with a saved copy.` : (n ? 'No authors recorded for these stories yet. Authors come from saved copies.' : '');
  const big = rows.slice().sort((a,b)=>b.pick-a.pick || b.date.localeCompare(a.date))[0];
  L.big = big && big.pick ? `Most reprinted: “${big.hl}” (${big.pub}, ${dateLabel(big)}), which was reprinted in ${pl(big.pick,'other outlet')}.` : '';
  return L;
}
const BRIEF_ORDER = [['vol','Volume'],['issues','Issues'],['bills','Bills'],['heads','Headlines'],['reach','Reach'],['big','Biggest story'],['tone','Tone'],['who','Reporters']];
function briefText(){
  const rows = filtered().filter(countable), L = briefOf(rows), fd = filterDesc();
  return `Jesse Gabriel press coverage: ${periodLabel()}\n` + (fd ? `Filtered to ${fd}\n` : '') + '\n'
    + BRIEF_ORDER.filter(([k]) => L[k]).map(([k,l]) => `• ${l}: ${L[k]}`).join('\n') + `\n\nFrom the AJG Press Coverage Tracker, ${new Date().toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'})}.`;
}
function renderReport(rows){
  const L = briefOf(rows), fd = filterDesc(), per = periodLabel();
  $('#rpTitle').textContent = `Data: ${per.charAt(0).toUpperCase()+per.slice(1)}`;  /* REORG-v1: the tab keeps the name Data */
  $('#rpScope').innerHTML = `${pl(rows.length,'story','stories')}${fd ? ` · Filtered to ${esc(fd)} <button class="linkbtn" data-clearf>Clear filters</button>` : ''}`;
  $('#brief').innerHTML = `<div class="hdl"><h3>The brief</h3><span class="note">Written from the stories below. Copy it into an email or memo.</span></div><ul>${BRIEF_ORDER.filter(([k]) => L[k]).map(([k,l]) => `<li><b>${l}.</b> ${esc(L[k])}</li>`).join('')}</ul>`;
  $('#hVol').textContent = L.vol; $('#hDrove').textContent = [L.issues, L.heads].join(' '); $('#hWhere').textContent = L.reach; $('#hTone').textContent = L.tone; $('#hWho').innerHTML = tbWhoHtml(L.who);  /* LINKRULES-v1 */
  renderMoments(rows); renderBillList(rows); renderReprint(rows); renderCountyMap(rows); renderEthnic(rows); renderGaps();
  toneMix($('#rpTone'), $('#rpToneCap'), rows, ' in this period', { watch: false }); reorgReport(rows);  /* REORG-v1 */
}
