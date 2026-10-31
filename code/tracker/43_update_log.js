/* ---------- Update log: what each update added, and edits to any story ----------
   Each button run (and each hand-add) saves an entry to the shared store, collection "runs": the stories, reprints, tones,
   authors and translations it added; the sheet task adds what it wrote to the spreadsheet. The log lists those entries,
   then older additions grouped by the spreadsheet's Added column. Any story can be edited there (or from the story panel);
   edits are saved to collection "edits" ({field: value} or {removed: true}), shown at once, and written into the
   spreadsheet by the sheet task, which then clears them. */
const LOG = { runs: [] }; let runsCol = null, editsCol = null; const EDITS = new Map();
const EDIT_FIELDS = [
  {k:'date', label:'Date', type:'date'}, {k:'outlet', label:'Outlet'}, {k:'hl', label:'Headline', wide:true}, {k:'link', label:'Link', wide:true},
  {k:'author', label:'Reporter', hint:'Several as "A; B"'}, {k:'topic', label:'Issue', opts:() => RANK.topic}, {k:'bills', label:'Bills', hint:'e.g. AB 418; AB 2316'},
  {k:'reach', label:'Reach', opts:() => [...new Set(REACH_ORDER.concat(D.map(r => r.reach).filter(v => typeof v === 'string' && v.includes(';'))))]}, {k:'media', label:'Format', opts:() => RANK.media}, {k:'role', label:'How Gabriel appears', opts:() => RANK.role},
  {k:'lang', label:'Language', opts:() => [...new Set(['English','Spanish','Chinese','French','Hebrew','Korean','Armenian','Russian','Vietnamese'].concat(D.map(r => r.lang).filter(Boolean)))]},
  {k:'also', label:'Reprinted in', wide:true, hint:'Other outlets that ran it, separated by ";"'}];
const EKEYS = new Set(EDIT_FIELDS.map(f => f.k));
const fieldVal = (r, k) => k==='bills' ? (r.bills||[]).join('; ') : k==='lang' ? (r.lang || 'English') : (r[k] || '');
function cleanEdit(d){
  if (!d) return null; const e = {};
  if (d.removed === true) return { removed: true, at: VS(d.at, 30) };
  EDIT_FIELDS.forEach(f => { if (f.k in d){ e[f.k] = f.k==='bills' ? splitBills(Array.isArray(d.bills) ? d.bills : VS(d.bills, 300)) : VS(d[f.k], 1500); } });
  if (e.date && !/^\d{4}-\d{2}-\d{2}$/.test(e.date)) delete e.date;
  e.at = VS(d.at, 30); return e;
}
function applyEdit(id, e){
  const r = byId.get(id); if (!r || !e) return false;
  if (e.removed){
    const i = D.indexOf(r); if (i >= 0) D.splice(i, 1); byId.delete(id); S.pick.delete(id);
    const l = byDate.get(r.date); if (l) l.splice(l.indexOf(r), 1); if (S.openId === id) closeViewer(); return true;
  }
  let ch = false;
  EDIT_FIELDS.forEach(({k}) => { if (!(k in e)) return; const v = e[k];
    if (k==='bills'){ if (v.join(';') !== (r.bills||[]).join(';')){ r.bills = v.slice(0, 12); ch = true; } return; }
    if (k==='lang'){ const l = /^english$/i.test(v) ? '' : v; if (l !== r.lang){ r.lang = l; ch = true; } return; }
    if (v === (r[k] || '')) return; ch = true;
    if (k==='date'){ const l = byDate.get(r.date); if (l) l.splice(l.indexOf(r), 1); r.date = v; r.year = +v.slice(0,4); r.prec = 'day'; (byDate.get(v) || byDate.set(v, []).get(v)).push(r); }
    else if (k==='outlet'){ r.outlet = v; r.pub = v.replace(/\s*\(.*$/, '').trim() || r.pub; }
    else if (k==='link'){ if (!r.plink || r.plink === r.link) r.plink = v; r.link = v; }
    else if (k==='author') setAuthor(r, v);
    else if (k==='topic'){ r.topic = v; r.issue = v; }
    else { r[k] = v; if (k==='also') r._alsoEdit = true; }
  });
  if (ch){ r._s = searchStr(r); r.pick = reprintCount(r); }
  return ch;
}
function cleanRun(id, d){
  if (!/^run-[0-9a-z]{4,24}$/.test(id) || !d) return null;
  const ids = v => (Array.isArray(v) ? v : []).filter(x => SID_ANY(x)).slice(0, 1000);
  const sh = d.sheet && typeof d.sheet === 'object' ? { at: VS(d.sheet.at, 30), line: VS(d.sheet.line, 600), bills: ids(d.sheet.bills), stories: ids(d.sheet.stories), translations: ids(d.sheet.translations), newbills: (Array.isArray(d.sheet.newbills) ? d.sheet.newbills : []).filter(x => typeof x === 'string').slice(0, 20).map(x => VS(x, 160)) } : null;
  // rows: the spreadsheet rows the run proposed (Coverage column -> value); ids: placeholder -> real ID, written by the sheet task
  const rows = (Array.isArray(d.rows) ? d.rows : []).filter(o => o && typeof o === 'object' && !Array.isArray(o)).slice(0, 500).map(o => {
    const r = {}; Object.keys(o).slice(0, 80).forEach(k => { const v = o[k]; if (typeof v === 'string') r[VS(k, 80)] = VS(v, 3000); else if (typeof v === 'number' && isFinite(v)) r[VS(k, 80)] = v; }); return r; });
  const rid = {}; if (d.ids && typeof d.ids === 'object' && !Array.isArray(d.ids)) Object.keys(d.ids).slice(0, 2000).forEach(k => {
    const v = d.ids[k]; if (/^(s?NEW|ws-NEW|jg-NEW)-[0-9a-z-]{1,40}$/.test(k) && typeof v === 'string' && /^(\d{5}|s\d{5}|(ws|pq|nb|jg)-\d{5})$/.test(v)) rid[k] = v; });
  return { id, at: VS(d.at, 30), mode: pick1(VS(d.mode, 20), ['find','refresh','hand','edits','save','newsbank'], 'find'), newsbank: /^\d{4}-\d\d-\d\d$/.test(d.newsbank || '') ? d.newsbank : '' /* RECALL-v1 */, searched_to: /^\d{4}-\d\d-\d\d$/.test(d.searched_to || '') ? d.searched_to : '', since: /^\d{4}-\d\d-\d\d$/.test(d.since || '') ? d.since : '', since_manual: d.since_manual === true,   /* SINCE-v1 */ stories: ids(d.stories), tones: ids(d.tones), authors: ids(d.authors), translations: ids(d.translations), rows, ids: rid,
    reprints: (Array.isArray(d.reprints) ? d.reprints : []).filter(p => p && SID_ANY(p.story)).slice(0, 300).map(p => ({ story: VS(p.story, 30), outlet: VS(p.outlet, 120) })), sheet: sh,
    left: (Array.isArray(d.left) ? d.left : []).filter(x => x && typeof x === 'object').slice(0, 150).map(x => ({ hl: VS(x.hl, 200), outlet: VS(x.outlet, 120), date: VS(x.date, 10), why: VS(x.why, 200) })),
    /* RUNPERSIST-v1 */ status: VS(d.status, 20), step: VS(d.step, 120), error: VS(d.error, 300), heartbeat: VS(d.heartbeat, 30), failed: VS(String(d.failed == null ? '' : d.failed), 20),
    done: isFinite(d.done) ? +d.done : 0, plan: isFinite(d.plan) ? +d.plan : 0, cands: isFinite(d.cands) ? +d.cands : 0,
    print_pages: (Array.isArray(d.print_pages) ? d.print_pages : []).filter(x => x && typeof x === 'object').slice(0, 100).map(x => ({ url: VS(x.url, 500), outlet: VS(x.outlet, 120), date: VS(x.date, 10), hl: VS(x.hl, 200) })),
    unconfirmed: (Array.isArray(d.unconfirmed) ? d.unconfirmed : []).filter(x => x && typeof x === 'object').slice(0, 150).map(x => ({ hl: VS(x.hl, 200), outlet: VS(x.outlet, 120), date: VS(x.date, 10), link: VS(x.link, 500), why: VS(x.why, 200) })) };
}
async function initLog(db){
  if (!db) return;
  runsCol = db.collection('runs'); editsCol = db.collection('edits');
  runsCol.onSnapshot(snap => { LOG.runs = snap.docs.map(d => cleanRun(d.id, d.data())).filter(Boolean).sort((a,b) => b.at.localeCompare(a.at)); if (S.mg==='log' && !$('#upd').hidden) renderAbout(); }, () => {});
  editsCol.onSnapshot(snap => {
    let ch = false; EDITS.clear();
    oldFirst(snap.docs).forEach(d => { const e = cleanEdit(d.data()), id = sidOf(d.id); if (!e) return; EDITS.set(id, e); if (applyEdit(id, e)) ch = true; });
    if (ch){ refreshRanks(); rerender(); }
    if (S.mg==='log' && !$('#upd').hidden) renderAbout();
  }, () => {});
}
const newRunId = () => 'run-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
/* RUNPERSIST-v1: a run doc that cannot be stored stays in this browser (localStorage jg-runs-pending, 5 newest, row page texts stripped) and the
   reason is kept in LOG.lastSaveError, so runAll can say so instead of firing the sheet task for a doc that does not exist */
function keepPending(id, doc, e){
  LOG.lastSaveError = { code: String((e && e.code) || (runsCol ? 'save_failed' : 'no_store')), message: VS(String((e && (e.message || e)) || (runsCol ? 'save failed' : 'shared store not reachable')), 200) };
  try {
    const strip = o => { const c = Object.assign({}, o); if (Array.isArray(c.rows)) c.rows = c.rows.map(r => { const q = Object.assign({}, r); delete q._text; return q; }); return c; };
    let a = []; try { a = JSON.parse(localStorage.getItem('jg-runs-pending') || '[]'); } catch(e2){}
    a = (Array.isArray(a) ? a : []).filter(x => x && x.id !== id).concat([{ id, doc: strip(doc), at: new Date().toISOString() }]).slice(-5);
    localStorage.setItem('jg-runs-pending', JSON.stringify(a));
  } catch(e3){}
}
async function saveRun(id, doc){ LOG.runs = [cleanRun(id, doc)].concat(LOG.runs.filter(x => x.id !== id));
  if (runsCol){ try { await runsCol.doc(id).set(doc); return true; } catch(e){ keepPending(id, doc, e); return false; } }
  keepPending(id, doc, null); return false; }
/* progress doc written while the search runs (fire-and-forget from the search; replaced by the provisional / final doc) */
async function runHeartbeat(id, patch){
  const doc = Object.assign({ at: (LOG.hbAt0 = LOG.hbAt0 || new Date().toISOString()), mode: 'find', status: 'running', provisional: true }, patch || {}, { heartbeat: new Date().toISOString() });
  LOG.runs = [cleanRun(id, doc)].concat(LOG.runs.filter(x => x.id !== id)).filter(Boolean);
  if (!runsCol){ keepPending(id, doc, null); return false; }
  try { await runsCol.doc(id).set(doc); return true; } catch(e){ keepPending(id, doc, e); return false; }
}
function snapStories(){ return { f: new Map(D.map(r => [r.id, [r.tone, r.author, r.hl_en||'', r.text_en||'']])), rp: new Set(RP_DONE) }; }
function diffStories(s){
  const out = { tones:[], authors:[], translations:[], reprints:[] };
  D.forEach(r => { const b = s.f.get(r.id); if (!b) return; if (b[0] !== r.tone) out.tones.push(r.id); if (b[1] !== r.author) out.authors.push(r.id); if (b[2] !== (r.hl_en||'') || b[3] !== (r.text_en||'')) out.translations.push(r.id); });
  RP_DONE.forEach(id => { if (!s.rp.has(id)){ const p = RPS.get(id); if (p) out.reprints.push({ story: p.story, outlet: p.outlet }); } });
  return out;
}
const MODE_LBL = { find:'Update database', refresh:'Refresh from files', hand:'Added by hand', edits:'Edits' };
function whenLbl(s){ const d = new Date(s); return isNaN(d) ? esc(s) : d.toLocaleString(undefined, { month:'short', day:'numeric', hour:'numeric', minute:'2-digit' }); }
function logItem(id, extra){
  id = covResolve(id); const r = byId.get(id);
  if (!r) return `<div class="log-i gone"><div><b>Story removed</b><small>${esc(id)}</small></div><span></span></div>`;
  return `<div class="log-i${S.logEdit===id?' on':''}"><div><button class="linkbtn log-h" data-logopen="${esc(id)}">${esc(r.hl)}</button><small>${esc(dateLabel(r))} · ${esc(r.outlet)}${extra ? ' · ' + extra : ''}${EDITS.has(id) ? ' · <span class="log-pend">edited, not yet in the spreadsheet</span>' : ''}</small></div><button class="btn" data-logedit="${esc(id)}">Edit</button></div>`;
}
function logSection(title, rows){ return rows.length ? `<div class="log-sec"><div class="up-k">${title} (${fmt(rows.length)})</div>${rows.join('')}</div>` : ''; }
// one proposed spreadsheet row: its Article ID and Story ID (placeholders until the sheet task writes the real ones), kind, outlet, headline
function logRow(o, ids){
  const real = k => ids[o[k]] || o[k] || '', pend = !ids[o['Article ID']];
  const sid = real('Story ID'), r = byId.get(sid) || byId.get(covResolve(o['Tracker story code'] || ''));
  const what = o['Original or reprint'] === 'Reprint' ? `Reprint of ${esc(sid)}` : `Original, ${esc(sid)}`;
  const hl = o['Headline'] || (r ? r.hl : '');
  return `<div class="log-i"><div>${r ? `<button class="linkbtn log-h" data-logopen="${esc(r.id)}">${esc(hl || r.hl)}</button>` : `<b>${esc(hl || o['Publisher link'] || '')}</b>`}<small>${esc(real('Article ID'))} · ${what} · ${esc(o['Date'] || 'No date')} · ${esc(o['Outlet'] || '')}${pend ? ' · <span class="log-pend">placeholder IDs, not yet in the spreadsheet</span>' : ''}</small></div><span></span></div>`;
}
function runCard(x, open){
  const sh = x.sheet || {};
  const parts = [[x.stories.length,'new story','new stories'],[x.reprints.length,'reprint'],[x.tones.length,'tone'],[x.authors.length,'reporter'],[x.translations.length,'translation'],[(sh.bills||[]).length,'bill tag']].filter(p => p[0]).map(p => pl(p[0], p[1], p[2]));
  const body = logSection('New stories', x.stories.map(id => logItem(id)))
    + logSection('Reprints added', x.reprints.map(p => logItem(p.story, 'reprinted in ' + esc(p.outlet))))
    + logSection('Tones rated', x.tones.map(id => logItem(id, esc((byId.get(id)||{}).tone || ''))))
    + logSection('Reporters found', x.authors.map(id => logItem(id, esc((byId.get(id)||{}).author || 'no byline'))))
    + logSection('Translated', x.translations.map(id => logItem(id)))
    + logSection('Bills tagged in the spreadsheet', (sh.bills||[]).map(id => logItem(id, esc(((byId.get(id)||{}).bills||[]).join(', ')))))
    + logSection('Spreadsheet rows', (x.rows||[]).map(o => logRow(o, x.ids||{})))
    + (sh.line ? `<p class="log-sheet"><b>Spreadsheet:</b> ${esc(sh.line)}</p>` : `<p class="log-sheet">${x.mode==='hand' || x.stories.length || x.reprints.length || x.tones.length || x.authors.length || x.translations.length ? 'Saved in the tracker, not in the sheet yet. Ask Claude in chat to “save the last run to the sheet”.' : ''}</p>`)
    + ((sh.newbills||[]).length ? `<p class="log-sheet"><b>New bills on the list:</b> ${sh.newbills.map(esc).join('; ')}</p>` : '')
    + '';
  /* RUNPERSIST-v1: a run still searching, or one that stopped with an error */
  const hbAge = x.heartbeat ? Date.now() - Date.parse(x.heartbeat) : 0, stale = x.status === 'running' && hbAge > 30*60e3;
  const state = x.status === 'error' ? `Stopped: ${esc(x.error || 'an error')}` : x.status === 'running' ? (stale ? `No progress since ${whenLbl(x.heartbeat)} (${fmt(x.done)} of ${fmt(x.plan)} searches); the tab was probably closed` : `Running since ${whenLbl(x.at)}, ${fmt(x.done)} of ${fmt(x.plan)} searches`) : '';
  const unc = (x.unconfirmed || []).length ? logSection('Not confirmed (not in the spreadsheet)', x.unconfirmed.map(u => `<div class="log-i"><div><b>${esc(u.hl || u.link)}</b><small>${esc(u.date || 'No date')} · ${esc(u.outlet || '')}${u.why ? ' · ' + esc(u.why) : ''}</small></div><span></span></div>`)) : '';
  const ppg = (x.print_pages || []).length ? logSection('Print pages to clip (e-paper, not stories)', x.print_pages.map(u => `<div class="log-i"><div><b>${esc(u.hl || u.url)}</b><small>${esc(u.date || 'No date')} · ${esc(u.outlet || '')} · <a href="${esc(u.url)}" target="_blank" rel="noopener">page</a></small></div><span></span></div>`)) : '';
  return `<details class="log-run"${open?' open':''}><summary><b>${MODE_LBL[x.mode]}</b><span class="log-when">${whenLbl(x.at)}</span><span class="log-sum">${state || parts.join(' · ') || 'Nothing new'}${(x.print_pages || []).length ? ' · ' + pl(x.print_pages.length, 'print page') + ' to clip' : ''}${x.mode === 'find' && x.since_manual && x.since ? ' · since ' + esc(x.since) : ''}</span></summary>${(state ? `<p class="log-sheet">${state}</p>` : '') + body + unc + ppg || '<p class="log-sheet">Nothing was added.</p>'}</details>`;
}
function addedLabel(a){ return /^\d{4}-\d{2}-\d{2}$/.test(a) ? 'Tracker update ' + a : a; }
function addedKey(a){ let m = a.match(/(\d{4})-(\d{2})-(\d{2})/); if (m) return m[0]; m = a.match(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2})\b/); return m ? `${TODAY.slice(0,4)}-${String(MONTHS.findIndex(x => x.startsWith(m[1]))+1).padStart(2,'0')}-${m[2].padStart(2,'0')}` : '0000'; }
function editForm(id){
  const r = byId.get(id); if (!r) return '';
  const inp = f => { const v = fieldVal(r, f.k);
    if (f.opts){ const o = f.opts(); return `<select data-ef="${f.k}" aria-label="${esc(f.label)}">${(o.includes(v) ? o : [v].concat(o)).map(x => `<option${x===v?' selected':''}>${esc(x)}</option>`).join('')}</select>`; }
    return `<input data-ef="${f.k}" type="${f.type||'text'}" value="${esc(v)}" ${f.hint ? `placeholder="${esc(f.hint)}"` : ''} aria-label="${esc(f.label)}">`; };
  return `<div class="log-form" data-formid="${esc(id)}"><div class="log-form-h"><b>Edit story</b><button class="linkbtn" data-logclose>Close</button></div>
    <div class="log-grid">${EDIT_FIELDS.map(f => `<label class="${f.wide?'wide':''}"><span>${esc(f.label)}</span>${inp(f)}</label>`).join('')}
    <label><span>Tone</span><select data-ef="tone" aria-label="Tone"><option value="">${rated(r) ? esc(r.tone) + ' (unchanged)' : 'Not rated'}</option>${TONE_ORDER.slice(0,5).map(t => `<option value="${t}">${t}</option>`).join('')}</select></label>
    <label class="wide"><span>Team note</span><textarea data-ef="note" rows="2" placeholder="Anything the team should know.">${esc((NOTES.get(id)||{}).text||'')}</textarea></label></div>
    <div class="log-acts"><button class="btn primary" data-logsave>Save changes</button><button class="btn" data-logclose>Cancel</button><button class="btn danger" data-logremove>Remove story</button></div>
    <p class="upd-step">Changes show in the tracker at once and go into the spreadsheet when you ask Claude in chat to “save the last run to the sheet”. Removing a story takes it out of the tracker at once; when that is saved its rows move to the spreadsheet’s Removed tab.</p></div>`;
}
function renderLog(){
  const inRuns = new Set(LOG.runs.flatMap(x => x.stories));
  const groups = new Map(); D.forEach(r => { if (!r.added || inRuns.has(r.id)) return; const k = addedLabel(r.added); (groups.get(k) || groups.set(k, []).get(k)).push(r); });
  const g = [...groups].sort((a,b) => addedKey(b[0]).localeCompare(addedKey(a[0])));
  const pend = EDITS.size;
  let h = `<p>Every update and what it added, newest first. Press <b>Edit</b> on any story to change its details, or use <b>Edit details</b> in a story's panel.</p>`;
  if (pend) h += `<div class="upd-msg">${pl(pend,'edited story','edited stories')} not yet in the spreadsheet. They go in with the next update. <button class="linkbtn" data-logpush>Write them in now</button></div>`;
  if (S.logEdit) h += editForm(S.logEdit);
  h += LOG.runs.map((x, i) => runCard(x, i === 0)).join('');
  if (!LOG.runs.length) h += `<p class="upd-step">Updates run from now on are listed here with everything they added.</p>`;
  if (g.length) h += `<div class="up-k log-earlier">Earlier additions</div>` + g.map(([k, rs]) => { rs.sort((a,b) => b.date.localeCompare(a.date)); const all = S.logMore === k, show = all ? rs : rs.slice(0, 25);
    return `<details class="log-run"><summary><b>${esc(k)}</b><span class="log-sum">${pl(rs.length,'story','stories')}</span></summary><div class="log-sec">${show.map(r => logItem(r.id)).join('')}${rs.length > show.length ? `<button class="linkbtn" data-logmore="${esc(k)}">Show all ${fmt(rs.length)}</button>` : ''}</div></details>`; }).join('');
  return h;
}
async function saveEdit(id, form){
  const r = byId.get(id); if (!r) return;
  const e = Object.assign({}, EDITS.get(id) || {}); delete e.removed; let n = 0;
  form.querySelectorAll('[data-ef]').forEach(el => { const k = el.dataset.ef; if (!EKEYS.has(k)) return;
    let v = el.value.trim(); if (k==='bills') v = splitBills(v);
    const cur = fieldVal(r, k);
    if ((k==='bills' ? v.join('; ') : v) === cur) return;
    if (k==='date' && !/^\d{4}-\d{2}-\d{2}$/.test(v)) return;
    e[k] = v; n++; });
  if (e.bills){ const off = (r.bills||[]).filter(b => !e.bills.includes(b)); e.bills_off = off; }
  const tone = form.querySelector('[data-ef=tone]').value, note = form.querySelector('[data-ef=note]').value;
  if (tone && tone !== r.tone) await setTeamTone(id, tone);
  if (note !== ((NOTES.get(id)||{}).text||'')) saveNote(id, note);
  if (n){
    e.at = new Date().toISOString(); const doc = Object.assign({}, e); if (doc.bills) doc.bills = doc.bills.concat((doc.bills_off||[]).map(b => '-' + b)); delete doc.bills_off; delete e.bills_off;
    applyEdit(id, e); EDITS.set(id, e); refreshRanks();
    // an outlet taken out of "Reprinted in" stays out: drop its saved reprint
    if ('also' in e) RPS.forEach((p, rid) => { if (p.story === id && !ranIn(r, p.outlet, hostOf(p.link)) && reprintsCol) reprintsCol.doc(rid).delete().catch(() => {}); });
    let ok = false; if (editsCol){ try { await editsCol.doc(id).set(doc); ok = true; } catch(err){} }
    toast(ok ? 'Saved. It goes into the spreadsheet with the next update.' : 'Saved on this page only. Sign in to Claude with edit access to save it for everyone.');
  } else if (!tone && note === ((NOTES.get(id)||{}).text||'')) toast('Nothing changed');
  S.logEdit = null; render(); renderAbout();
}
async function removeStory(id){
  const r = byId.get(id); if (!r) return;
  // no confirm(): the artifact frame blocks dialogs, so it always returned false and nothing was removed
  const e = { removed: true, at: new Date().toISOString() };
  const form = [...document.querySelectorAll('.log-form')].find(f => f.dataset.formid === id), btn = form?.querySelector('[data-logremove]');
  if (btn){ btn.classList.add('busy'); btn.textContent = 'Removing…'; }
  let ok = false; if (editsCol){ try { await editsCol.doc(id).set(e); ok = true; } catch(err){} }
  if (clipsCol) clipsCol.doc(id).delete().catch(() => {});
  if (form && form.isConnected){ form.classList.add('removing'); await new Promise(res => setTimeout(res, 560)); }
  // removed from a story's panel: the whole panel flashes red and slides off before it closes
  const sh = form && form.closest('#sheet'); if (sh){ sh.classList.add('removing'); await new Promise(res => setTimeout(res, 420)); closeViewer(); sh.classList.remove('removing'); }
  EDITS.set(id, e); applyEdit(id, e); refreshRanks(); S.logEdit = null; render(); renderAbout();
  if (!ok){ toast('Removed on this page only. Sign in to Claude with edit access to remove it for everyone.'); return; }
  // delete its spreadsheet row now instead of waiting for the next update
  toast('Removed. Its rows move to the spreadsheet’s Removed tab when you ask Claude in chat to “save the last run to the sheet”.');   /* TOKENS-v1; BUTTONOPT-v1: removals execute */
}
$('#mgOther').addEventListener('click', e => {
  const t = e.target;
  const ed = t.closest('[data-logedit]'); if (ed){ S.logEdit = ed.dataset.logedit; renderAbout(); $('#mgOther').scrollTop = 0; return; }
  if (t.closest('[data-logclose]')){ S.logEdit = null; renderAbout(); return; }
  if (t.closest('[data-logsave]')){ const f = t.closest('.log-form'); saveEdit(f.dataset.formid, f); return; }
  if (t.closest('[data-logremove]')){ removeStory(t.closest('.log-form').dataset.formid); return; }
  const mo = t.closest('[data-logmore]'); if (mo){ S.logMore = mo.dataset.logmore; renderAbout(); return; }
  const op = t.closest('[data-logopen]'); if (op){ closeUpd(); openViewer(op.dataset.logopen); return; }
  if (t.closest('[data-logpush]')) saveSheet();   /* TOKENS-v1 */
});

