/* ---------- INSIGHTS-v1: Insights tab shell (agent-insights; contract build/insights_contract.md) ----------
   One top-level tab with a sub-nav. Feature views live in their own script blocks (id ins-js-ID) after this
   script and call AJGInsights.register({id, label, render(el, ctx)}). */
const INS_ORDER = ['release_pickup','bill_timeline','story_travel','reporters','tone_topic'];
const INS = { views: new Map(), cur: null, params: {}, drawn: new Map(), version: '0', pending: null, pendingParams: null };
(function insMount(){
  const nav = document.querySelector('nav.tabs');
  if (nav && !$('#tab-in')) nav.insertAdjacentHTML('beforeend', '<button role="tab" id="tab-in" data-tab="in" aria-selected="false" hidden>Insights</button>');
  if (!$('#view-in')) $('main.wrap').insertAdjacentHTML('beforeend', `<section id="view-in" hidden>
    <div class="card pad in-bar"><div style="min-width:0"><h2 class="sec">Insights</h2><div class="cap" id="inCap" style="margin-bottom:0">Who picks up his releases, how bills and stories travel, and who covers him. Uses every story in the tracker.</div></div>
    <div class="seg in-nav" id="inNav" role="group" aria-label="Insights views"></div></div>
    <div id="inBody"></div></section>`);
  document.head.insertAdjacentHTML('beforeend', `<style id="ins-css">
.in-bar{display:flex;justify-content:space-between;align-items:flex-end;gap:12px 18px;flex-wrap:wrap}
.seg.in-nav{display:inline-flex;flex-wrap:wrap;max-width:100%} .seg.in-nav button{flex:none;padding:6px 12px;font-size:12.5px}
#inBody{margin-top:12px} .in-view{display:grid;gap:12px} .in-view[hidden]{display:none}
.in-sec{display:grid;gap:12px}
.in-entry{margin-top:8px;font-size:12.5px;color:var(--ink-3);display:flex;gap:4px 14px;flex-wrap:wrap;align-items:baseline}
.in-cmap{width:100%;height:auto;max-height:560px;overflow:visible}
.in-cmap path{stroke:var(--map-edge);stroke-width:.7;stroke-linejoin:round}
.in-cmap path.on{cursor:pointer} .in-cmap path.on:hover{stroke:var(--map-edge-on);stroke-width:1.4}
.in-hl{outline:2px solid var(--focus);outline-offset:-2px;background:var(--sel)}
@media (max-width:640px){.in-bar{align-items:stretch}.seg.in-nav{display:flex}.seg.in-nav button{flex:1 1 auto}}
</style>`);
})();
const insCsv = (rows, cols) => { const q = v => { const t = String(v ?? ''); return /[",\n\r]/.test(t) ? '"' + t.replace(/"/g,'""') + '"' : t; };
  return '﻿' + [cols.map(c => q(c[0])).join(',')].concat(rows.map(r => cols.map(([,k]) => q(typeof k === 'function' ? k(r) : r[k])).join(','))).join('\r\n'); };
const insBlock = (() => { const c = new Map(); return name => { if (c.has(name)) return c.get(name); let v = null;
  try { const el = document.getElementById('ins-' + name); if (el) v = JSON.parse(el.textContent); } catch(e){ v = null; } c.set(name, v); return v; }; })();
const insRows = (() => { let c = null; return () => { if (c) return c; let j = null; try { j = JSON.parse(document.getElementById('rows').textContent); } catch(e){}
  const cols = (j && j.cols) || []; c = ((j && j.rows) || []).map(a => { const o = {}; cols.forEach((k, i) => o[k] = a[i]); return o; }); return c; }; })();
const insBills = () => { try { const j = JSON.parse(document.getElementById('billsinfo').textContent); return (j && j.rows) || []; } catch(e){ return []; } };
function insDrawCountyMap(svg, counts, opts){
  opts = opts || {}; const max = Math.max(0, ...counts.values());
  const steps = 6, cut = n => !n ? 0 : Math.min(steps, 1 + Math.floor(Math.log(n) / Math.log(Math.max(2, max) + 1e-9) * (steps - 1) + 1e-9));
  svg.setAttribute('viewBox', `0 0 ${CA_MAP.w} ${CA_MAP.h}`); svg.classList.add('in-cmap');
  svg.innerHTML = CA_MAP.counties.map(c => { const n = counts.get(c.name) || 0;
    return `<path d="${c.d}" data-county="${esc(c.name)}" class="${n ? 'on' : ''}" style="fill:${n ? `var(--q${cut(n)})` : 'var(--panel-2)'}"><title>${esc(c.name)} County: ${n}</title></path>`; }).join('');
  svg.onmousemove = e => { const p = e.target.closest('path.on'); if (!p || !opts.tip){ hideTip(); return; } showTip(e, opts.tip(p.dataset.county)); };
  svg.onmouseleave = hideTip;
  svg.onclick = e => { const p = e.target.closest('path.on'); if (p && opts.onClick){ hideTip(); opts.onClick(p.dataset.county); } };
  return { max };
}
function insHash(){ const p = new URLSearchParams(); Object.entries(INS.params || {}).forEach(([k, v]) => { if (v != null && v !== '') p.set(k, v); });
  const q = p.toString(); return '#insights' + (INS.cur ? '/' + INS.cur : '') + (q ? '?' + q : ''); }
function insParse(h){ const m = /^insights(?:\/([a-z_]+))?(?:\?(.*))?$/.exec(h || ''); if (!m) return null;
  const params = {}; if (m[2]) new URLSearchParams(m[2]).forEach((v, k) => params[k] = v); return { id: m[1] || null, params }; }
function insCtx(id){
  return {
    D, byId: k => byId.get(k), rows: insRows, bills: insBills, block: insBlock, version: INS.version, TODAY, LAST,
    TONE_ORDER, RANK, REACH_ORDER, rated, reachTags, billName, countiesOf, authorKey, canonAuthors,
    authorKind: a => AKIND.get(authorKey(a)) || 'person',
    esc, fmt, pl, iso, addDays, monthName, dateLabel, daysBetween: (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 864e5),
    colorFor, niceMax, barPath, axis, barList, reporterBars, showTip, hideTip, drawCountyMap: insDrawCountyMap,
    cpBtn: u => (typeof cpBtn === 'function' ? cpBtn(u) : ''),   // LINKUI-v1: copy-link icon to put left of a link
    /* TRAVEL-v3: a story drawn exactly as the Clips list draws it (.clip markup + CSS), for pickers inside a view.
       opts.pub replaces the outlet name; author names are plain text (no Clips author filter); role="option". */
    clipItem: (r, extra, opts) => { opts = opts || {}; let h = clipItem(opts.pub ? Object.assign({}, r, { pub: opts.pub }) : r, extra);
      h = h.replace(/<button type="button" class="tlink" data-author="[^"]*" title="[^"]*">([^<]*)<\/button>/g, '<span class="by-n">$1</span>');
      h = h.split('</span>, <span class="by-n">').join(', ');
      return h.replace(/ tabindex="0" role="button" aria-label="Story details: [^"]*"/, ` tabindex="-1" role="option"${opts.optId ? ` id="${opts.optId}"` : ''}`); },
    fold: s => String(s || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[‘’]/g, "'").replace(/\s+/g, ' ').trim(),
    openStory: (sid, order) => openViewer(sid, order || [sid]),
    clips: f => { clearAll(); Object.entries(f || {}).forEach(([k, v]) => { if (S.sel[k]) [].concat(v).forEach(x => S.sel[k].add(x)); }); go('db'); },
    get params(){ return Object.assign({}, INS.params); }, set params(v){ INS.params = Object.assign({}, v || {}); try { if (S.tab === 'in') history.replaceState(null, '', insHash()); } catch(e){} }, setParams: p => { INS.params = Object.assign({}, p); try { history.replaceState(null, '', insHash()); } catch(e){} },
    go: (v, p) => insShow(v, p || {}), saveFile, csv: insCsv, copy, toast, refresh: () => insShow(id, INS.params, true)
  };
}
function insNav(){
  const ids = INS_ORDER.filter(k => INS.views.has(k)).concat([...INS.views.keys()].filter(k => !INS_ORDER.includes(k)));
  $('#inNav').innerHTML = ids.map(k => `<button type="button" data-in="${k}" aria-pressed="${k === INS.cur}">${esc(INS.views.get(k).label)}</button>`).join('');
  $('#inNav').hidden = !ids.length; $('#tab-in').hidden = !ids.length; return ids;
}
function insShow(id, params, force){
  const ids = insNav(); const body = $('#inBody');
  if (!ids.length){ if (!body.querySelector('.in-none')) body.innerHTML = '<div class="card pad in-none"><div class="empty">No insight views are installed in this build.</div></div>'; return; }
  body.querySelectorAll('.in-none').forEach(x => x.remove());
  // a view picked by the user, a link or a deep link sticks; otherwise ("auto") the first view in sub-nav order is shown
  const keep = id && INS.views.has(id) && !(INS.auto && id === INS.cur);
  if (INS.pending && INS.views.has(INS.pending)){ id = INS.pending; params = INS.pendingParams || {}; INS.pending = null; INS.pendingParams = null; INS.auto = false; }
  else if (keep) INS.auto = false;
  else { INS.auto = true; id = ids[0]; }
  const changed = id !== INS.cur; INS.cur = id; if (params) INS.params = Object.assign({}, params); else if (changed) INS.params = {};
  insNav(); let el = body.querySelector(`.in-view[data-in="${id}"]`);
  if (!el){ el = document.createElement('div'); el.className = 'in-view'; el.dataset.in = id; body.appendChild(el); }
  body.querySelectorAll('.in-view').forEach(v => v.hidden = v !== el);
  if (S.tab !== 'in') return;
  try { history.replaceState(null, '', insHash()); } catch(e){}
  const key = INS.version + '|' + JSON.stringify(INS.params);
  if (!force && INS.drawn.get(id) === key) return;
  INS.drawn.set(id, key); const v = INS.views.get(id);
  if (v.destroy && el.childNodes.length){ try { v.destroy(); } catch(e){} }
  // every render gets a fresh element, so listeners a view added to el on an earlier render can't stack
  const fresh = el.cloneNode(false); el.replaceWith(fresh); el = fresh;
  const fail = e => { console.error(e); el.innerHTML = `<div class="card pad"><div class="empty">This view could not be drawn: ${esc(e && e.message || e)}</div></div>`; };
  try { const p = v.render(el, insCtx(id)); if (p && p.catch) p.catch(fail); } catch(e){ fail(e); }
}
/* a cheap signature of the data: re-render the open view when Update/refresh, tones or authors change it */
function insSig(){ let a = D.length, t = 0, n = 0; for (const r of D){ if (rated(r)) t++; n += (r.authors||[]).length + (r.pick||0); } return a + '.' + t + '.' + n; }
$('#inNav').addEventListener('click', e => { const b = e.target.closest('button[data-in]'); if (b && b.dataset.in !== INS.cur) insShow(b.dataset.in, {}); });
window.AJGInsights = Object.freeze({ register(v){
  if (!v || typeof v.id !== 'string' || typeof v.render !== 'function' || INS.views.has(v.id)) return false;
  INS.views.set(v.id, { id: v.id, label: String(v.label || v.id), render: v.render, destroy: v.destroy });
  if (S.tab === 'in') insShow(INS.cur, INS.cur ? INS.params : null); else insNav();
  return true; } });
/* entry points from the story panel (the only Insights links outside the tab) */
function insEntry(r){
  const out = [];
  if (INS.views.has('story_travel') && (r.reps || []).length) out.push(`<button class="linkbtn" data-ins-go="story_travel" data-ins-k="id" data-ins-v="${esc(r.id)}" title="See where this story ran, on a timeline">Trace this story</button>`);
  const ppl = (r.authors || []).filter(a => (AKIND.get(authorKey(a)) || 'person') === 'person');
  if (INS.views.has('reporters') && ppl.length) out.push(...ppl.slice(0, 3).map(a => `<button class="linkbtn" data-ins-go="reporters" data-ins-k="author" data-ins-v="${esc(a)}" title="${esc(a)} in the reporter outreach list">${ppl.length > 1 ? esc(a) + ' in outreach list' : 'Reporter in outreach list'}</button>`));
  return out.length ? `<div class="in-entry">${out.join('')}</div>` : '';
}
document.addEventListener('click', e => { const b = e.target.closest('[data-ins-go]'); if (!b) return; e.preventDefault(); closeAuthorSheet();
  const p = {}; p[b.dataset.insK] = b.dataset.insV; S.page = 0; setTab('in'); insShow(b.dataset.insGo, p, true); scrollTo(0, 0); });
/* ---------- /INSIGHTS-v1 shell ---------- */
