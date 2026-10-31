/* ---------- events ---------- */
document.querySelector('nav.tabs').onclick = e => { const b = e.target.closest('button[data-tab]'); if (b) go(b.dataset.tab); };
let qT; $('#q').oninput = e => { clearTimeout(qT); qT = setTimeout(()=>{ S.q = foldQ(e.target.value).trim(); S.page = 0; render(); }, 120); };
$('#when').onchange = e => { if (e.target.value==='pick'){ openRange(e.target); return; } if (e.target.value!=='custom'){ applyWhen(e.target.value); renderWhen(); } S.page = 0; render(); };
document.addEventListener('change', e => { const t = e.target; if (t && t.matches && t.matches('[data-lo]')){ S.lo = t.checked; S.page = 0; render(); if (typeof TB !== 'undefined' && TB.cur) tbShow(true); } });   /* INCL-v1 */
$('#facets').addEventListener('change', e => { const t = e.target; if (t.dataset.f){ const s = S.sel[t.dataset.f]; t.checked ? s.add(t.value) : s.delete(t.value); S.page = 0; render(); } });
$('#facets').addEventListener('toggle', e => { const d = e.target.closest('details[data-facet]'); if (d) d.open ? S.openFacets.add(d.dataset.facet) : S.openFacets.delete(d.dataset.facet); }, true);
$('#facets').addEventListener('input', e => { const k = e.target.dataset.fq; if (k){ S.fq[k] = e.target.value; const pos = e.target.selectionStart; renderFacets(); const i = document.querySelector(`[data-fq="${k}"]`); i.focus(); i.setSelectionRange(pos,pos); } });
$('#facets').addEventListener('click', e => {
  if (e.target.dataset.fmore){ const k = e.target.dataset.fmore; S.fall[k] = !S.fall[k]; renderFacets(); }
  const a = e.target.closest('[data-saved]'); if (a){ S.saved = a.dataset.saved; S.page=0; render(); }
});
function clearAll(){ S.q=''; $('#q').value=''; FACETS.forEach(f=>S.sel[f.key].clear()); applyWhen('all'); S.saved='all'; S.flag=''; S.ranin=''; S.fq={}; S.page=0; renderWhen(); render(); }
$('#clearAll').onclick = clearAll;
$('#chips').onclick = e => { const b = e.target.closest('button[data-rm]'); if (!b) return; const k = b.dataset.rm;
  if (k==='q'){ S.q=''; $('#q').value=''; } else if (k==='when'){ applyWhen('all'); renderWhen(); } else if (k==='saved'){ S.saved='all'; } else if (k==='flag'){ S.flag=''; } else if (k==='ranin'){ S.ranin=''; } else if (b.dataset.v==='__rated'){ TONE_ORDER.slice(0,5).forEach(t=>S.sel.tone.delete(t)); } else S.sel[k].delete(b.dataset.v);
  S.page=0; render(); };
document.querySelector('#table thead').onclick = e => { const b = e.target.closest('button[data-sort]'); if (!b) return; const k = b.dataset.sort;
  S.sort = S.sort.key===k ? {key:k, dir:-S.sort.dir} : {key:k, dir: (k==='date'||k==='rep') ? -1 : 1}; S.page=0; renderTable(filtered()); };
$('#tbody').onclick = e => { if (e.target.closest('a[href],td.x,[data-fk],[data-tb-go],[data-bill],[data-pub],[data-author]')) return; if (e.target.closest('[data-clear]')){ clearAll(); return; } const tr = e.target.closest('tr[data-id]'); if (tr) openViewer(tr.dataset.id, S._order); };
$('#tbody').onkeydown = e => { if (e.key==='Enter' && !e.target.closest('td.x')){ const tr = e.target.closest('tr[data-id]'); if (tr) openViewer(tr.dataset.id, S._order); } };
$('#pager').onclick = e => { const b = e.target.closest('[data-pg]'); if (b){ S.page += +b.dataset.pg; renderTable(filtered()); document.querySelector('.tablewrap').scrollIntoView({block:'start'}); } };
$('#pager').onchange = e => { if (e.target.id==='per'){ S.per = +e.target.value; S.page = 0; renderTable(filtered()); } };
$('#sheet').onclick = e => {
  if (e.target.closest('[data-close]')) closeViewer();
  const w = e.target.closest('[data-wide]');
  if (w){ const on = $('#sheet').classList.toggle('wide');
    w.setAttribute('aria-pressed', String(on)); w.innerHTML = on ? IC.shrink : IC.exp; w.title = on ? 'Back to the side panel' : 'Full-page view: details on the left, the article on the right'; }
  const n = e.target.closest('[data-nav]'); if (n && !n.disabled) navViewer(+n.dataset.nav);
};
$('#scrim').onclick = () => { closeViewer(); $('#rail').classList.remove('open'); $('#scrim').hidden = true; };
document.addEventListener('keydown', e => {
  if (e.key==='Escape'){ $('#rail').classList.remove('open'); closeViewer(); $('#scrim').hidden = $('#sheet').hidden; }
  if (!$('#sheet').hidden && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)){ if (e.key==='ArrowRight') navViewer(1); if (e.key==='ArrowLeft') navViewer(-1); if (e.key==='Enter' && !e.target.closest('#tbody,.clip,button,a') && (S._hits||[]).length){ e.preventDefault(); stepHit(e.shiftKey?-1:1); } }
});
$('#clearTop').onclick = () => clearAll();
$('#openRail').onclick = () => { $('#rail').classList.add('open'); $('#scrim').hidden = false; };
$('#closeRail').onclick = () => { $('#rail').classList.remove('open'); $('#scrim').hidden = $('#sheet').hidden; };
$('#rpWhen').onchange = e => { if (e.target.value==='pick'){ openRange(e.target, true); return; } if (e.target.value!=='custom'){ applyWhen(e.target.value); renderWhen(); } tuneChart(); S.qv = null; render(); };
$('#briefCopy').onclick = e => copy(briefText(), 'Copied the brief. Paste it into an email or memo.', e.currentTarget);
$('#explore').addEventListener('toggle', () => { if ($('#explore').open) renderTrends(filtered()); });
$('#views').addEventListener('click', e => {
  const v = e.target.closest('[data-view]'); if (v){ const x = [...PRESETS, ...VIEWS].find(y => y.id===v.dataset.view); if (x){ if (v.getAttribute('aria-pressed')==='true') clearAll(); else applyState(x.st); } return; }
  const d = e.target.closest('[data-vdel]'); if (d){ delView(d.dataset.vdel); return; }
  if (e.target.closest('[data-vnew]')){ S._naming = true; renderViews(); return; }
  if (e.target.closest('[data-vcancel]')){ S._naming = false; renderViews(); }
});
$('#views').addEventListener('submit', e => { e.preventDefault(); const n = $('#vname').value.trim(); if (n) saveView(n); });
$('#density').onclick = () => { const on = !$('#table').classList.contains('compact'); $('#table').classList.toggle('compact', on); $('#density').setAttribute('aria-pressed', on); try { localStorage.setItem('jg2-density', on ? 'compact' : ''); } catch(e){} };
$('#tbody').addEventListener('change', e => { const id = e.target.dataset.pick; if (!id) return; e.target.checked ? S.pick.add(id) : S.pick.delete(id); drawBulk(); });
$('#pickAll').onchange = e => { (S._pageIds||[]).forEach(id => e.target.checked ? S.pick.add(id) : S.pick.delete(id)); renderTable(filtered()); };
$('#bkList').onclick = () => $('#copyClips').onclick();
$('#bkSheet').onclick = () => $('#copySheet').onclick();
$('#bkCsv').onclick = () => download('csv');
$('#bkClear').onclick = () => { S.pick.clear(); renderTable(filtered()); };
document.addEventListener('click', e => {
  if (e.target.closest('[data-runfind]')){ runAll('find'); return; }
  const m = e.target.closest('[data-mgopen]'); if (m){ openUpd(m.dataset.mgopen); return; }
  const g = e.target.closest('#mgTabs [data-mg]'); if (g){ S.mg = g.dataset.mg; drawMg(); return; }
  const f = e.target.closest('[data-flag]'); if (f){ closeUpd(); clearAll(); S.flag = f.dataset.flag; go('db'); return; }
  if (e.target.closest('.dlmenu .menu button')) document.querySelectorAll('.dlmenu[open]').forEach(d => d.open = false);
});
$('#sheet').addEventListener('click', e => {
  const r = byId.get(S.openId); if (!r) return;
  if (e.target.closest('[data-clink]')) copy(storyUrl(r), 'Copied the link');
  // Edit details opens the edit form right here in the story panel, under the links
  if (e.target.closest('[data-editstory]')){ const open = $('#sheet .log-form'); if (open){ open.remove(); return; }
    e.target.closest('.dlinks,.note').insertAdjacentHTML('afterend', editForm(r.id));
    const f = $('#sheet .log-form'); f.scrollIntoView({block:'nearest', behavior:'smooth'}); f.querySelector('[data-ef]')?.focus({preventScroll:true}); return; }
  const lf = e.target.closest('.log-form'); if (lf){
    if (e.target.closest('[data-logclose]')){ lf.remove(); return; }
    if (e.target.closest('[data-logsave]')){ saveEdit(r.id, lf).then(() => { if (S.openId===r.id) openViewer(r.id); }); return; }
    if (e.target.closest('[data-logremove]')){ removeStory(r.id); return; }
  }
});
$('#sheet').addEventListener('change', e => { if (e.target.matches('[data-tset]') && e.target.value && S.openId) setTeamTone(S.openId, e.target.value); });
$('#sheet').addEventListener('input', e => { if (e.target.id==='tnote' && S.openId){ $('#tnoteMeta').textContent = 'Saving…'; saveNote(S.openId, e.target.value); } });
document.addEventListener('keydown', e => {
  if (/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName) || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key==='/'){ e.preventDefault(); if (S.tab!=='db') go('db'); $('#q').focus(); }
  if (!$('#sheet').hidden && (e.key==='j' || e.key==='k')) navViewer(e.key==='j' ? 1 : -1);
});
$('#anBreak').addEventListener('change', () => { $('#anOnly').value = ''; });
['anInterval','anBreak','anOnly','anMeasure','anFrom','anShow','anAvg'].forEach(id => $('#'+id).onchange = () => { S.qv = null; renderTrends(filtered()); });
['hmRows','hmCols','cmpB'].forEach(id => $('#'+id).onchange = () => renderTrends(filtered()));
$('#cmpA').onchange = () => { const p = periods().find(x=>x.id===$('#cmpA').value); if (p && p.pair && [...$('#cmpB').options].some(o=>o.value===p.pair)) $('#cmpB').value = p.pair; renderTrends(filtered()); };
document.querySelector('.quick').onclick = e => { const b = e.target.closest('[data-qv]'); if (!b) return; const q = QV[b.dataset.qv];
  for (const [k,v] of Object.entries(Object.assign({anInterval:'quarter', anMeasure:'stories', anShow:'n'}, q))) $('#'+k).value = v;
  $('#anOnly').value = '';
  S.qv = b.dataset.qv; renderTrends(filtered()); };
$('#relSeg').onclick = e => { const b = e.target.closest('[data-rel]'); if (b){ S.rel = b.dataset.rel; renderRel(filtered().filter(countable)); } };
$('#heat').onclick = e => { const c = e.target.closest('td[data-hk]'); if (!c) return; clearAll(); S.sel[c.dataset.hk].add(c.dataset.hv); if (c.dataset.hy) applyWhen('y'+c.dataset.hy); go('db'); toast(`Showing ${c.dataset.hv}${c.dataset.hy?', '+c.dataset.hy:''}`); };
document.addEventListener('click', e => { const b = e.target.closest('[data-copytable]'); if (!b) return; const t = document.getElementById(b.dataset.copytable); if (t) copy([...t.querySelectorAll('tr')].map(tr => [...tr.children].map(c => tsvCell(c.textContent)).join('\t')).join('\n'), 'Copied the table. Paste it into Excel or Google Sheets.'); });
// overview + trends shortcuts into the clip list
document.querySelector('main').addEventListener('keydown', e => { const c = e.target.closest && e.target.closest('.clip[data-id]'); if (c && e.target===c && e.key==='Enter') c.click(); });
document.querySelector('main').addEventListener('click', e => {
  if (e.target.closest('a[href]')) return;
  if (e.target.closest('[data-clearf]')){ clearFilters(); return; }
  if (e.target.closest('[data-clear]') && S.tab==='an'){ clearAll(); return; }
  const tl = e.target.closest('[data-tile]'); if (tl){ const k = tl.dataset.tile, ly = LAST.slice(0,4); clearAll();
    if (k==='30') applyWhen('30'); else if (k==='ytd') applyWhen('y'+ly);
    else if (k==='named'){ applyWhen('y'+ly); S.sel.role.add('Named in headline'); S.sel.role.add('Op-ed by Gabriel'); }
    else if (k==='major'){ applyWhen('365'); S.sel.reach.add('National'); S.sel.reach.add('Statewide California'); }
    else if (k==='neg30'){ applyWhen('30'); S.sel.tone.add('Negative'); S.sel.tone.add('Very negative'); }
    else if (k.startsWith('tone30:')){ applyWhen('30'); S.sel.tone.add(k.slice(7)); }
    else if (k==='notes') S.flag = 'notes';
    go('db'); return; }
  if (e.target.closest('#newAll')){ clearAll(); S.when = 'custom'; S.d0 = S._since; S.d1 = null; S.whenLabel = `Since ${dateLabel({date:S._since, prec:'day'})}`; go('db'); return; }
  const g = e.target.closest('[data-goto]'); if (g){ if (g.dataset.goto==='tone'){ clearAll(); TONE_ORDER.slice(0,5).forEach(t=>S.sel.tone.add(t)); go('db'); return; } go(g.dataset.goto); return; }
  if (e.target.closest('.clip [data-author]')) return; // author link inside a card: the document handler filters
  const c = e.target.closest('.clip[data-id]'); if (c){ const list = [...c.parentElement.querySelectorAll('.clip[data-id]')].map(x=>x.dataset.id); openViewer(c.dataset.id, list); return; }
  const mo = e.target.closest('[data-month]'); if (mo){ clearAll(); setMonth(mo.dataset.month); go('db'); return; }
  const hb = e.target.closest('.hb,.btl,.mv'); if (hb && hb.dataset.k && (S.tab==='an' || S.tab==='ov')){ if (S.tab==='ov') clearAll(); if (hb.dataset.m && S.sel.media) S.sel.media.add(hb.dataset.m); S.sel[hb.dataset.k].add(hb.dataset.v); go('db'); toast(`Showing ${hb.dataset.v}`); }
});
$('#copyClips').onclick = () => { const rows = exportRows(); copy(rows.map(r => `${dateLabel(r)} · ${r.pub}: ${r.hl}${r.pick?`\n${alsoShort(r,99)}`:''}${r.lstat==='Search link only'?'':exportLinkText(r)}`).join('\n\n'), `Copied ${pl(rows.length,'clip')}`); };
$('#copySheet').onclick = () => { const rows = exportRows(); copy(['Date\tOutlet\tAuthors\tHeadline\tIssue\tBills\tReach\tMedium\tFormat\tHow Gabriel appears\tReprints\tReprinted in\tTone\tTone note\tQuoted\tMention depth\tLanguage\tAired (Pacific)\tLink'].concat(rows.map(r=>[r.date,r.outlet,(r.authors||[]).join('; ') || r.author,r.hl,r.topic,r.bills.join('; '),r.reach,r.media,fmtOf(r),r.role,r.pick,r.also,rated(r)?r.tone:'',r.twhy||'',r.quoted||'',r.depth||'',r.lang||'',avtLine(r),exportLinkBest(r)].map(tsvCell).join('\t'))).join('\n'), `Copied ${pl(rows.length,'row')}. Paste into Excel or Google Sheets.`); };
$('#fileIn').onchange = e => { ingest([...e.target.files]); e.target.value=''; };
$('#dirIn').onchange = e => { ingest([...e.target.files]); e.target.value=''; };

