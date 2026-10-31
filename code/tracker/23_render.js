/* ---------- render + tabs ---------- */
function render(){
  const rows = filtered();
  if (S.tab==='ov') renderToday();
  if (S.tab==='db'){ renderViews(); renderFacets(); renderChips(rows); renderTable(rows); $('#when').value = S.when==='custom' ? 'custom' : S.when; }
  if (S.tab==='an'){ $('#rpWhen').value = S.when==='custom' ? 'custom' : S.when; renderTrends(rows.filter(countable)); }   /* INCL-v1 */
  if (S.tab==='in'){ INS.version = insSig(); insShow(INS.cur, INS.cur ? INS.params : null); }  // INSIGHTS-v1
  if (!$('#upd').hidden && S.mg!=='upd') renderAbout();
  drawBulk(); toneStatus(); authorStatus(); drawBadge();
}
function renderWhen(){
  const o = WHEN.map(([v,l])=>`<option value="${v}">${l}</option>`).join('') + (S.when==='custom' ? `<option value="custom">${esc(S.whenLabel)}</option>` : '') + '<option value="pick">Custom range…</option>';
  $('#when').innerHTML = o; $('#rpWhen').innerHTML = o;
  $('#when').value = S.when; $('#rpWhen').value = S.when;
}
function setTab(t){
  S.tab = t;
  
  document.querySelectorAll('nav.tabs button').forEach(b => b.setAttribute('aria-selected', b.dataset.tab===t));
  ['ov','db','an','in'].forEach(k => $('#view-'+k).hidden = k!==t);  // INSIGHTS-v1
  try { history.replaceState(null, '', t==='ov' ? location.pathname : t==='in' ? insHash() : '#'+({db:'clips',an:'data'}[t])); } catch(e){}
}
function go(t){ S.page = 0; setTab(t); renderWhen(); render(); scrollTo(0,0); }

