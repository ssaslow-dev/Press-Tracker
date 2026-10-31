/* ---------- saved views ---------- */
const PRESETS = [
  { id:'p30', name:'Last 30 days', st:{ when:'30' } },
  { id:'phd', name:'Headlines and op-eds', st:{ sel:{ role:['Named in headline','Op-ed by Gabriel'] } } },
  { id:'pmj', name:'National and statewide', st:{ sel:{ reach:['National','Statewide California'] } } },
  { id:'png', name:'Negative tone', st:{ sel:{ tone:['Negative','Very negative'] } } },
  { id:'psv', name:'With a saved copy', st:{ saved:'yes' } },
];
let VIEWS = [], viewsCol = null; const V_LS = 'jg2-views';
function lsViews(){ try { return JSON.parse(localStorage.getItem(V_LS)||'[]') || []; } catch(e){ return []; } }
function curState(){
  const st = {}, sel = {};
  if (S.q) st.q = S.q;
  if (S.when!=='all'){ st.when = S.when; if (S.when==='custom'){ st.d0 = S.d0; st.d1 = S.d1; st.label = S.whenLabel; } }
  FACETS.forEach(f => { if (S.sel[f.key].size) sel[f.key] = [...S.sel[f.key]]; }); if (Object.keys(sel).length) st.sel = sel;
  if (S.saved!=='all') st.saved = S.saved; if (S.flag) st.flag = S.flag; if (S.ranin) st.ranin = S.ranin;
  if (S.lo) st.lo = 1;   /* INCL-v1 */
  return st;
}
const stKey = st => JSON.stringify([st.q||'', st.when||'all', st.d0||'', st.d1||'', FACETS.map(f => ((st.sel||{})[f.key]||[]).slice().sort()), st.saved||'all', st.flag||'', st.ranin||'', st.lo ? 1 : 0]);
function applyState(st){
  S.q = foldQ(String(st.q||'')).trim(); $('#q').value = S.q; FACETS.forEach(f => { S.sel[f.key].clear(); ((st.sel||{})[f.key]||[]).forEach(v => S.sel[f.key].add(String(v))); });
  applyWhen('all'); if (st.when==='custom'){ S.when = 'custom'; S.d0 = st.d0||null; S.d1 = st.d1||null; S.whenLabel = String(st.label||'Custom dates'); } else if (st.when && WHEN.some(w=>w[0]===st.when)) applyWhen(st.when);
  S.saved = ['yes','no'].includes(st.saved) ? st.saved : 'all'; S.flag = FLAGS[st.flag] ? st.flag : ''; S.ranin = st.ranin ? String(st.ranin) : ''; S.lo = !!st.lo; S.page = 0; renderWhen(); render();
}
function renderViews(){
  const k = stKey(curState()), any = anyFilter();
  const b = v => `<span class="view-b${stKey(v.st)===k?' on':''}"><button data-view="${esc(v.id)}" aria-pressed="${stKey(v.st)===k}">${esc(v.name)}</button>${v.team ? `<button class="vx" data-vdel="${esc(v.id)}" aria-label="Delete the view ${esc(v.name)}" title="Delete this view">${IC.xs}</button>` : ''}</span>`;
  $('#views').innerHTML = `<span class="eyebrow">Views</span>` + PRESETS.map(b).join('') + VIEWS.map(v => b(Object.assign({team:true}, v))).join('')
    + (S._naming ? `<form class="vsave" id="vform"><input id="vname" maxlength="40" placeholder="Name this view" aria-label="View name" required><button class="btn primary" type="submit">Save</button><button class="linkbtn" type="button" data-vcancel>Cancel</button></form>`
       : any && ![...PRESETS, ...VIEWS].some(v => stKey(v.st)===k) ? `<button class="linkbtn" data-vnew>+ Save this view</button>` : '');
  if (S._naming) setTimeout(() => { const i = $('#vname'); if (i && document.activeElement!==i) i.focus(); }, 0);
}
async function saveView(name){
  const v = { id: 'v' + Date.now().toString(36), name: name.slice(0,40), st: curState() };
  S._naming = false;
  if (viewsCol){ try { await viewsCol.doc(v.id).set({ name: v.name, st: JSON.stringify(v.st) }); toast(`Saved the view “${v.name}” for the team`); return; } catch(e){} }
  v.id = 'l' + v.id.slice(1); const l = lsViews(); l.push(v); try { localStorage.setItem(V_LS, JSON.stringify(l)); } catch(e){} VIEWS = l; renderViews(); toast(`Saved the view “${v.name}” on this computer`);
}
async function delView(id){
  if (viewsCol && !id.startsWith('l')){ try { await viewsCol.doc(id).delete(); } catch(e){ toast('That view could not be deleted.'); } }
  const l = lsViews().filter(v => v.id!==id); try { localStorage.setItem(V_LS, JSON.stringify(l)); } catch(e){}
  VIEWS = VIEWS.filter(v => v.id!==id); renderViews();
}
function initViews(db){
  VIEWS = lsViews();
  if (!db) return;
  viewsCol = db.collection('views');
  viewsCol.onSnapshot(snap => {
    const team = []; snap.docs.forEach(d => { const x = d.data(); let st = null; try { st = JSON.parse(x.st); } catch(e){} if (st && typeof st==='object' && x.name) team.push({ id: d.id, name: String(x.name).slice(0,40), st }); });
    VIEWS = team.concat(lsViews().filter(v => !team.some(t => t.id===v.id))); if (S.tab==='db') renderViews();
  }, () => {});
}

