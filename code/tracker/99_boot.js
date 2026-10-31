/* ---------- boot ---------- */
D.forEach(r => { r.pick = reprintCount(r); });
const setHdr = () => document.documentElement.style.setProperty('--hdr', document.querySelector('header.mast').offsetHeight+'px');
setHdr(); let rT; addEventListener('resize', () => { setHdr(); clearTimeout(rT); rT = setTimeout(() => { if (S.tab==='ov' || S.tab==='an') render(); if (S.tab==='in' && INS.cur) insShow(INS.cur, INS.params, true); }, 200); });
$('#anFrom').innerHTML = YEARS.map(y=>`<option value="${y}" ${y===2017?'selected':''}>${y}</option>`).join('');
const h = location.hash.slice(1);
try { if (localStorage.getItem('jg2-density')==='compact'){ $('#table').classList.add('compact'); $('#density').setAttribute('aria-pressed','true'); } } catch(e){}
const insH = insParse(h); if (insH){ INS.pending = insH.id; INS.pendingParams = insH.params; }  // INSIGHTS-v1
setTab(insH ? 'in' : ({clips:'db', trends:'an', report:'an', data:'an'}[h] || (RG.toTone ? 'an' : 'ov')));  /* REORG-v1 */ renderWhen(); render();
if (h==='about') openUpd('defs');
(async () => {
  await loadManifest();
  if (await IDB.open()){ (await IDB.all()).forEach(([k,v]) => { const s = sidOf(k); if (byId.has(s) && (s === k || !local.has(s))) local.set(s, cleanLocal(s, v)); /* CLEAN-v1 */ }); }
  if (local.size || Object.keys(remote).length) render();
  indexSaved();
  initTone();
  initClips();
})();
})();
</script>


</body></html>