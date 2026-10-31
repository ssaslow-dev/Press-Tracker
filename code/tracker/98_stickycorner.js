/* STUCKCORNER-v1 (Sammy thread a9b77912, 2026-10-30: "make sure this corner is fixed"). The list tables' navy header row
   keeps its 9 px rounded top corners while it is pinned under the masthead (position: sticky), so rows scrolling beneath
   show through the two corner notches in every engine (WebKit/Safari most visibly). Rule: rounded at rest, square while
   pinned. One passive scroll/resize listener marks each table.db whose header is pinned with .hdr-stuck. */
(function(){
  try { document.head.insertAdjacentHTML('beforeend', '<style id="stuckcorner-css">table.db.hdr-stuck thead th{border-top-left-radius:0!important;border-top-right-radius:0!important}</style>'); } catch(e){}
  let queued = false;
  function mark(){
    queued = false;
    document.querySelectorAll('table.db').forEach(t => {
      const th = t.tHead && t.tHead.rows[0] && t.tHead.rows[0].cells[0];
      if (!th || !t.offsetParent){ t.classList.remove('hdr-stuck'); return; }
      const pin = parseFloat(getComputedStyle(th).top);
      const stuck = isFinite(pin) && t.getBoundingClientRect().top < pin - 0.5;
      t.classList.toggle('hdr-stuck', stuck);
    });
  }
  function q(){ if (!queued){ queued = true; requestAnimationFrame(mark); } }
  addEventListener('scroll', q, { passive: true, capture: true });
  addEventListener('resize', q, { passive: true });
  try { new MutationObserver(q).observe(document.body, { childList: true, subtree: true }); } catch(e){}
  q();
})();
