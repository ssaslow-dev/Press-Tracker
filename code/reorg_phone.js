/* ---------- PHONE-v1 (agent-reorg, 2026-10-27): phone layout, at 640px and narrower only ----------
   The main tabs move to a bar at the bottom of the screen; Update / Refresh / Spreadsheet / Manage go under a "⋯" menu;
   the header slims to one title line. Desktop is unchanged. To remove: delete this block (code/reorg_phone.js; patch_reorg.py
   installs it between these markers). */
document.head.insertAdjacentHTML('beforeend', `<style id="phone-css">
#moreBtn{display:none}
@media (max-width:640px){
  .mast .mast-row{flex-wrap:nowrap;gap:10px;padding-block:8px;position:relative}
  .mast .brand{min-width:0;flex:1 1 auto;display:flex;align-items:center}
  .mast .brand h1{margin:0;line-height:0} .mast .brand h1 img{height:34px;width:auto}
  .mast .brand .sub{display:none}
  #moreBtn{display:inline-grid;place-items:center;flex:none;width:44px;height:40px;border-radius:8px;border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.08);color:#fff;font:700 20px/1 var(--f-body);letter-spacing:1px;position:relative;cursor:pointer}
  #moreBtn[aria-expanded="true"]{background:#fff;color:#132a4a}
  #moreBtn[data-badge]::after{content:"";position:absolute;top:6px;right:6px;width:8px;height:8px;border-radius:50%;background:#e8a33d;box-shadow:0 0 0 2px #132a4a}
  .mast .hdr-acts{display:none!important}
  .mast.ph-open .hdr-acts{display:grid!important;grid-template-columns:minmax(0,1fr);gap:8px;position:absolute;top:calc(100% + 6px);right:0;left:auto;width:min(280px,calc(100vw - 32px));
    background:#132a4a;border:1px solid rgba(255,255,255,.18);border-radius:12px;padding:10px;box-shadow:0 12px 30px rgba(0,0,0,.35);z-index:25;order:0;margin:0}
  .mast.ph-open .hdr-acts .upd-btn{justify-content:flex-start;padding:11px 12px;width:100%}
  header.mast nav.tabs{position:fixed;left:0;right:0;bottom:0;z-index:21;margin:0;width:auto;order:0;border-radius:0;border:0;border-top:1px solid rgba(255,255,255,.16);
    background:#132a4a!important;padding:6px 8px calc(6px + env(safe-area-inset-bottom,0px));gap:4px;box-shadow:0 -4px 14px rgba(0,0,0,.18)}
  header.mast nav.tabs button{flex:1 1 0;padding:10px 4px;font-size:12.5px;min-height:44px}
  body{padding-bottom:calc(64px + env(safe-area-inset-bottom,0px))}
  .toast{bottom:calc(76px + env(safe-area-inset-bottom,0px))} .bulk{bottom:calc(72px + env(safe-area-inset-bottom,0px))}
}
</style>`);
(function phoneMenu(){
  const row = document.querySelector('header.mast .mast-row'), acts = row && row.querySelector('.hdr-acts'), mast = document.querySelector('header.mast');
  if (!row || !acts || $('#moreBtn')) return;
  acts.id = acts.id || 'hdrActs';
  acts.insertAdjacentHTML('beforebegin', `<button type="button" id="moreBtn" aria-label="More: update, refresh, spreadsheet, manage" aria-haspopup="true" aria-expanded="false" aria-controls="${acts.id}" title="More">⋯</button>`);
  const btn = $('#moreBtn'), set = open => { mast.classList.toggle('ph-open', open); btn.setAttribute('aria-expanded', String(open)); };
  btn.addEventListener('click', e => { e.stopPropagation(); set(!mast.classList.contains('ph-open')); if (mast.classList.contains('ph-open')){ const f = acts.querySelector('button'); if (f) f.focus(); } });
  acts.addEventListener('click', () => setTimeout(() => set(false), 0));
  document.addEventListener('click', e => { if (mast.classList.contains('ph-open') && !e.target.closest('.hdr-acts') && e.target !== btn) set(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && mast.classList.contains('ph-open')){ set(false); btn.focus(); } });
  addEventListener('resize', () => { if (innerWidth > 640) set(false); });
  const badge = $('#mgBadge'), sync = () => { if (badge && !badge.hidden) btn.dataset.badge = '1'; else delete btn.dataset.badge; };
  if (badge){ new MutationObserver(sync).observe(badge, { attributes: true, attributeFilter: ['hidden'] }); sync(); }
})();
/* ---------- /PHONE-v1 ---------- */
