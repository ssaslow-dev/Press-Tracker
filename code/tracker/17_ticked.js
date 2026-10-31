/* ---------- ticked stories ---------- */
const exportRows = () => S.pick.size ? sortRows(D.filter(r => S.pick.has(r.id))) : sortRows(filtered());
function drawBulk(){ const n = S.pick.size; $('#bulk').hidden = !n || S.tab!=='db'; $('#bulkN').textContent = `${pl(n,'story','stories')} ticked`;
  const pa = $('#pickAll'), ids = S._pageIds || []; if (pa){ const on = ids.filter(id => S.pick.has(id)).length; pa.checked = !!ids.length && on===ids.length; pa.indeterminate = on>0 && on<ids.length; } }

/* PICKALL-v1 (rp-final 2026-10-28, Sammy comment 56b789c7): the header "Tick every story on this page" box sits on the text baseline,
   ~3 px above the navy header's centre. As a block in a middle-aligned cell it centres exactly, keeps the row boxes' x and size (16 px),
   and the Date header does not move. */
document.head.insertAdjacentHTML('beforeend', '<style id="pickall-css">table.db th.c-x{vertical-align:middle!important;line-height:0;padding-top:0!important;padding-bottom:0!important}table.db th.c-x input{display:block;width:16px;height:16px;margin:0}</style>');
