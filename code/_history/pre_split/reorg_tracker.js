/* ---------- REORG-v1 (agent-reorg, 2026-10-27): Phase 1 of work/org_ideas/proposal_final.md with Sammy's answers ----------
   Home: one 30-day line (copy icon), one negative list (Needs attention; rows link to Story travel), Tone = one line + bar,
   no "new since your last visit" / weekly items. Data keeps its name; sections Summary · Issues & bills · Outlets & reach ·
   Languages · Tone · Gaps · More charts, each collapsible to its headline sentence; the cuts and merges with one-line links;
   Tone by issue drawn inside Data › Tone. Insights → "Press desk" (Pitch · Releases · Bills · Story travel); old #insights
   links and tab ids still work. Bill numbers reused across sessions are split by session (AB 787). Installed by
   code/patch_reorg.py (apply_all step 4j) before the boot section; the phone layout is a separate block (PHONE-v1). */
const RG = { shut: new Set(), dt: { p: {}, key: '' }, toTone: false };
try { JSON.parse(localStorage.getItem('jg2-rg-shut') || '[]').forEach(k => RG.shut.add(k)); } catch(e){}
document.head.insertAdjacentHTML('beforeend', `<style id="reorg-css">
.rg-line{display:flex;align-items:center;gap:6px;margin:-4px 0 12px;font-size:15px;color:var(--ink);font-weight:600;line-height:1.4}
.rg-line .cpb{flex:none}
.rg-trace{margin:-2px 0 8px;font-size:12.5px}
.rg-tg{display:inline-flex;margin:2px 0 8px;max-width:100%}.rg-tg button{flex:none;padding:5px 12px;white-space:nowrap}
#view-ov .ov>.col{align-self:start}
.rg-hd{display:flex;justify-content:space-between;align-items:baseline;gap:8px 14px;flex-wrap:wrap}
.rg-link{font-size:13px;color:var(--ink-2);margin-top:8px}
.rg-who{font-size:14px;color:var(--ink-2);max-width:90ch}
.rp-h h2 .rg-sh{all:unset;cursor:pointer;display:flex;align-items:baseline;gap:8px;width:100%}
.rp-h h2 .rg-sh::before{content:"–";color:var(--accent);font-weight:700;width:.8em;flex:none}
.rp-sec.rg-shut .rp-h h2 .rg-sh::before{content:"+"}
.rp-h h2 .rg-sh:focus-visible{outline:2px solid var(--focus);outline-offset:3px;border-radius:3px}
.rp-sec.rg-shut>:not(.rp-h){display:none!important}
#rgToneIssue{margin-top:4px}
</style>`);

/* ---- bills: a number reused across sessions is one bill per session (same rule as Press desk › Bills) ---- */
const rgSesStart = s => { const y = +String(s).slice(0,4); return y ? `${y-1}-12-01` : '0000'; };
const rgSesShort = s => { const m = String(s).match(/^(\d{4})-(\d{2})?(\d{2})$/); return m ? `${m[1]}–${m[3]}` : String(s); };
const RG_SES = (() => { const m = new Map(); BILL_ROWS.forEach(b => { if (b.session) (m.get(b.bill) || m.set(b.bill, new Set()).get(b.bill)).add(String(b.session)); });
  return new Map([...m].map(([k, s]) => [k, [...s].sort()])); })();
function rgPickSes(bill, date){ const ss = RG_SES.get(bill) || []; if (!ss.length || !date) return ''; const d = date.length < 10 ? date.slice(0,7) + '-15' : date;
  return ss.filter(s => rgSesStart(s) <= d).pop() || ss[0]; }
/* bills that the whole log covers in more than one session get a "bill|session" key everywhere in Data */
const RG_SPLIT = (() => { const g = new Map(); D.forEach(r => (r.bills || []).forEach(b => { if (!r.date || (RG_SES.get(b) || []).length < 2) return;
  (g.get(b) || g.set(b, new Set()).get(b)).add(rgPickSes(b, r.date)); })); return new Set([...g].filter(([, s]) => s.size > 1).map(([b]) => b)); })();
function billGroups(rows){ const m = new Map(); rows.forEach(r => (r.bills || []).forEach(b => { const k = RG_SPLIT.has(b) ? b + '|' + rgPickSes(b, r.date) : b;
  (m.get(k) || m.set(k, []).get(k)).push(r); })); return m; }
function billSesName(b, s){ const row = BILL_ROWS.find(x => x.bill === b && String(x.session) === s); return row ? billTitle(row) + (billAuthored(row) ? '' : ' (coauthored)') : billName(b); }
function billLabel(k){ const [b, s] = k.split('|'); const n = s ? billSesName(b, s) : billName(b); return `${b}${s ? ` (${rgSesShort(s)})` : ''}${n ? ', ' + n : ''}`; }
/* a split bill opens Clips on that bill within its session's dates */
document.addEventListener('click', e => { const b = e.target.closest('[data-bses]'); if (!b) return; e.preventDefault(); e.stopPropagation();
  const bill = b.dataset.bill, s = b.dataset.bses, ss = RG_SES.get(bill) || [], i = ss.indexOf(s);
  clearAll(); S.sel.bills.add(bill); S.when = 'custom'; S.d0 = i > 0 ? rgSesStart(s) : null; S.d1 = i >= 0 && i < ss.length - 1 ? addDays(rgSesStart(ss[i+1]), -1) : null;
  S.whenLabel = `${rgSesShort(s)} session`; go('db'); toast(`Showing stories on ${bill}, ${rgSesShort(s)} session`); }, true);

/* ---- Home ---- */
function reorgHomeLine(n30, p30){
  const el = $('#homeLine'); if (!el) return;
  const tc = new Map(); D.forEach(r => { if (r.prec==='day' && r.date > addDays(TODAY,-30) && r.topic && !/^(Unassigned|Other \/ roundup)$/.test(r.topic)) tc.set(r.topic, (tc.get(r.topic)||0)+1); });
  const top = [...tc.entries()].sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0]))[0];
  const dir = n30 > p30 ? 'up from' : n30 < p30 ? 'down from' : 'level with';
  const t = `${pl(n30,'story','stories')} in the last 30 days, ${dir} ${fmt(p30)} the 30 days before${top ? `; led by ${top[0]}` : ''}.`;
  el.innerHTML = `<button type="button" class="cpb" data-cpt="${esc(t)}" title="Copy this line" aria-label="Copy this line">${CP_ICON}</button><span>${esc(t)}</span>`;
}
document.addEventListener('click', e => { const b = e.target.closest('button[data-cpt]'); if (!b) return; e.preventDefault(); e.stopPropagation();
  copy(b.dataset.cpt, 'Copied the line'); b.innerHTML = CP_OK; b.classList.add('ok'); clearTimeout(b._cpT);
  b._cpT = setTimeout(() => { b.innerHTML = CP_ICON; b.classList.remove('ok'); }, 1500); }, true);
/* a story in Home's negative list, with a link to where it ran (Press desk › Story travel) when it ran elsewhere */
function reorgAttnItem(r){
  const other = (r.reps || []).some(p => (p.pub || p.outlet) && (p.pub || p.outlet) !== (r.pub || r.outlet));
  return clipItem(r) + (other ? `<div class="rg-trace"><button class="linkbtn" data-ins-go="story_travel" data-ins-k="id" data-ins-v="${esc(r.id)}" title="See where this story ran">Story travel ›</button></div>` : '');
}

/* ---- Data ---- */
function rgSec(id){ const p = $(id); return p ? p.closest('.rp-sec') : null; }
function rgToggle(card, title, items){   // one card, a segmented switch between existing bodies [{label, cap, el}]
  const hd = document.createElement('div'); hd.className = 'rg-hd';
  hd.innerHTML = `<h2 class="sec">${esc(title)}</h2><div class="seg rg-tg" role="group" aria-label="${esc(title)}">${items.map((it, i) => `<button type="button" data-rgi="${i}" aria-pressed="${!i}">${esc(it.label)}</button>`).join('')}</div>`;
  const cap = document.createElement('div'); cap.className = 'cap'; cap.textContent = items[0].cap;
  card.innerHTML = ''; card.append(hd, cap); items.forEach((it, i) => { it.el.hidden = !!i; card.appendChild(it.el); });
  hd.querySelector('.rg-tg').addEventListener('click', e => { const b = e.target.closest('[data-rgi]'); if (!b) return; const i = +b.dataset.rgi;
    hd.querySelectorAll('[data-rgi]').forEach(x => x.setAttribute('aria-pressed', String(x === b))); items.forEach((it, j) => it.el.hidden = j !== i); cap.textContent = items[i].cap; });
  return card;
}
(function reorgLayout(){
  /* Home: the 30-day line; the "new since your last visit" card goes; Needs attention left, Tone right */
  /* HOMELINE-off (Sammy 2026-10-27 "remove this"): the 30-day summary line and its copy icon are no longer on Home */
  const nw = document.querySelector('#view-ov .ov-new'), cols = document.querySelectorAll('#view-ov .ov > .col');
  if (nw && cols.length === 2){ const at = document.querySelector('#view-ov .ov-attn'), tn = document.querySelector('#view-ov .ov-tone'); nw.remove(); cols[0].appendChild(at); cols[1].appendChild(tn); }
  const v = $('#view-an'); if (!v || v.dataset.rg) return; v.dataset.rg = '1';
  const sVol = rgSec('#hVol'), sDrove = rgSec('#hDrove'), sWhere = rgSec('#hWhere'), sMap = rgSec('#hMap'), sEth = rgSec('#hEth'), sGap = rgSec('#hGap'), sTone = rgSec('#hTone'), sWho = rgSec('#hWho');
  const name = (s, t, k) => { const h = s.querySelector('.rp-h h2'); h.innerHTML = `<button type="button" class="rg-sh" aria-expanded="true">${esc(t)}</button>`; s.dataset.rgk = k; };
  const card = id => $(id).closest('.card');
  /* 1 Summary: the brief, coverage over time, compare */
  name(sVol, 'Summary', 'sum'); sVol.querySelector('.rp-h').after($('#brief'));
  /* 2 Issues & bills (+ link to Press desk › Bills) */
  name(sDrove, 'Issues & bills', 'iss');
  card('#bills').insertAdjacentHTML('beforeend', '<div class="rg-link">Timelines with LegInfo milestones for each bill: <button class="linkbtn" data-ins-go="bill_timeline" data-ins-k="range" data-ins-v="all">Bills tab ›</button></div>');
  /* 3 Outlets & reach: Reach|Format, Top outlets, Most reprinted|Which issues travel (rows open Story travel), the county map, outlet relationships, top reporters */
  name(sWhere, 'Outlets & reach', 'out');
  const fmtCard = card('#fmtBars'), rcCard = card('#reachBars');
  rgToggle(rcCard, 'Reach and format', [{ label: 'Reach', cap: 'The kind of outlet that ran each story. Click one to see its clips.', el: $('#reachBars') },
    { label: 'Format', cap: 'Print, broadcast, online and other formats. Click one to see its clips.', el: $('#fmtBars') }]);
  fmtCard.remove();
  const rpCard = card('#reprint'), trCard = card('#travelBars'), rpEl = $('#reprint'), trEl = $('#travelBars');
  rgToggle(rpCard, 'Stories that travel', [{ label: 'Most reprinted', cap: 'Stories that ran in the most other outlets. Click one to see where it ran (Story travel tab).', el: rpEl },
    { label: 'Which issues travel', cap: 'Average number of other outlets that picked up each story. Issues with at least 5 stories.', el: trEl }]);
  rpCard.classList.remove('chartcard'); rpCard.classList.add('pad'); trCard.remove();
  const twoA = rcCard.parentElement, twoB = rpCard.parentElement; if (twoB !== twoA) twoB.className = '';
  rpEl.addEventListener('click', e => { if (e.target.closest('[data-author]')) return; const c = e.target.closest('.clip[data-id]'); if (!c) return; e.stopPropagation();
    S.page = 0; setTab('in'); insShow('story_travel', { id: c.dataset.id }, true); scrollTo(0, 0); }, true);
  const mapCard = sMap.querySelector('.cmap-card'), hMap = $('#hMap');
  mapCard.insertAdjacentHTML('afterbegin', '<h2 class="sec">Local coverage by county</h2>'); hMap.className = 'cap'; hMap.style.margin = '0 0 4px'; mapCard.querySelector('h2').after(hMap);
  sWhere.appendChild(mapCard); sMap.remove();
  const relCard = card('#relBars'); sWhere.appendChild(relCard);
  sWho.querySelector('.rp-h').remove(); const who = document.createElement('div'); who.className = 'rg-who';
  who.innerHTML = '<span id="hWho"></span> <button class="linkbtn" data-ins-go="reporters" data-ins-k="win" data-ins-v="24">Reporters tab ›</button>';
  sWhere.appendChild(who); sWho.remove();
  /* 4 Languages: By language|Top outlets, share over time; latest clips → Clips link */
  name(sEth, 'Languages', 'lang');
  const lgCard = card('#ethBars'), lpCard = card('#ethPubs');
  rgToggle(lgCard, 'Other languages', [{ label: 'By language', cap: 'Stories that ran in a language other than English. Click one to see its clips.', el: $('#ethBars') },
    { label: 'Top outlets', cap: 'Outlets that ran stories in other languages. Click an outlet to see its clips.', el: $('#ethPubs') }]);
  lpCard.remove(); const ltCard = card('#ethLatest'), trend = card('#ethTrend'), lgTwo = lgCard.parentElement, trTwo = trend.parentElement; ltCard.remove();
  lgTwo.className = 'two'; lgTwo.appendChild(trend); if (trTwo !== lgTwo && !trTwo.children.length) trTwo.remove();
  trend.insertAdjacentHTML('beforeend', '<div class="rg-link"><button class="linkbtn" data-rglang>See clips in other languages, newest first, in Clips ›</button></div>');
  document.querySelectorAll('#view-an .two').forEach(t => { if (t.children.length < 2) t.className = ''; });
  /* 5 Tone: the mix (no list; one link to the negative stories) + Tone by issue */
  name(sTone, 'Tone', 'tone');
  $('#rpTone').insertAdjacentHTML('afterend', '<div class="rg-link" id="rgNeg"></div>');
  sTone.insertAdjacentHTML('beforeend', '<div class="in-view" data-in="tone_topic" id="rgToneIssue"></div>');
  /* 6 Gaps */
  name(sGap, 'Gaps', 'gap');
  sGap.before(sTone);
  /* 7 More charts: issues by year, busiest months (bills over time is cut: Press desk › Bills covers each bill) */
  const ex = $('#explore'); const btl = $('#btls') && $('#btls').closest('.card'); if (btl) btl.remove();
  const sm = ex.querySelector('summary'); if (sm) sm.innerHTML = 'More charts<small>Issues by year (heatmap) and the busiest months of the year</small>';
  /* collapsible sections, remembered per viewer */
  v.querySelectorAll('.rp-sec[data-rgk]').forEach(s => { if (RG.shut.has(s.dataset.rgk)){ s.classList.add('rg-shut'); s.querySelector('.rg-sh').setAttribute('aria-expanded', 'false'); } });
  v.addEventListener('click', e => { const b = e.target.closest('.rg-sh'); if (!b) return; const s = b.closest('.rp-sec'), shut = !s.classList.contains('rg-shut');
    s.classList.toggle('rg-shut', shut); b.setAttribute('aria-expanded', String(!shut)); shut ? RG.shut.add(s.dataset.rgk) : RG.shut.delete(s.dataset.rgk);
    try { localStorage.setItem('jg2-rg-shut', JSON.stringify([...RG.shut])); } catch(x){}
    if (!shut && s.dataset.rgk === 'tone') rgDrawTone(true); });
  v.addEventListener('click', e => {
    if (e.target.closest('[data-rgneg]')){ TONE_ORDER.slice(3,5).forEach(t => S.sel.tone.add(t)); go('db'); toast('Showing the negative stories'); return; }
    if (e.target.closest('[data-rglang]')){ const keep = S.when, d0 = S.d0, d1 = S.d1, wl = S.whenLabel; clearAll(); langRank().filter(l => l !== 'English').forEach(l => S.sel.lang.add(l));
      S.when = keep; S.d0 = d0; S.d1 = d1; S.whenLabel = wl; S.sort = { key: 'date', dir: -1 }; go('db'); toast('Showing clips in other languages'); } });
})();
/* called at the end of renderReport */
function reorgReport(rows){
  const neg = rows.filter(r => rated(r) && NEG(r)).length, el = $('#rgNeg');
  if (el) el.innerHTML = neg ? `${pl(neg, 'negative story', 'negative stories')} in this period. <button class="linkbtn" data-rgneg>See them in Clips ›</button>` : 'No negative stories among the rated stories in this period.';
  rgDrawTone();
}
/* Data › Tone: the Tone by issue view (build/insights/tone_topic.js), drawn here instead of on the Press desk */
function rgDrawTone(force){
  const el = $('#rgToneIssue'), v = INS.views.get('tone_topic');
  if (!el || !v || S.tab !== 'an' || el.closest('.rg-shut')) return;
  const key = insSig() + '|' + JSON.stringify(RG.dt.p) + '|' + Math.round(el.clientWidth / 40);
  if (!force && RG.dt.key === key) return; RG.dt.key = key;
  const c = insCtx('tone_topic');
  Object.defineProperty(c, 'params', { get: () => Object.assign({}, RG.dt.p), set: x => { RG.dt.p = Object.assign({}, x || {}); }, configurable: true });
  c.setParams = p => { RG.dt.p = Object.assign({}, p || {}); }; c.refresh = () => rgDrawTone(true);
  try { const p = v.render(el, c); if (p && p.catch) p.catch(e => console.error(e)); } catch(e){ console.error(e); el.innerHTML = `<div class="card pad"><div class="empty">Tone by issue could not be drawn: ${esc(e && e.message || e)}</div></div>`; }
}

/* ---- Press desk (was Insights): name, order, hidden views, links ---- */
const RG_PD = { order: ['reporters', 'release_pickup', 'bill_timeline', 'story_travel'], hide: new Set(['tone_topic']),
  label: { reporters: 'Pitch', release_pickup: 'Releases', bill_timeline: 'Bills', story_travel: 'Story travel' },
  slug: { reporters: 'pitch', release_pickup: 'releases', bill_timeline: 'bills', story_travel: 'story-travel', tone_topic: 'tone-by-issue' } };
const RG_UNSLUG = Object.fromEntries(Object.entries(RG_PD.slug).map(([k, v]) => [v, k]));
(function(){ const t = $('#tab-in'); if (t) t.textContent = 'Press desk';
  const h = document.querySelector('#view-in .in-bar h2'); if (h) h.textContent = 'Press desk';
  const c = $('#inCap'); if (c) c.textContent = 'Who to pitch, how releases and bills played, and where stories traveled. Each view uses every story in the tracker.';
  const n = $('#inNav'); if (n) n.setAttribute('aria-label', 'Press desk views'); })();
insNav = function(){
  const ids = RG_PD.order.filter(k => INS.views.has(k)).concat([...INS.views.keys()].filter(k => !RG_PD.order.includes(k) && !RG_PD.hide.has(k)));
  $('#inNav').innerHTML = ids.map(k => `<button type="button" data-in="${k}" aria-pressed="${k === INS.cur}">${esc(RG_PD.label[k] || INS.views.get(k).label)}</button>`).join('');
  $('#inNav').hidden = !ids.length; $('#tab-in').hidden = !ids.length;
  if (INS.views.has('tone_topic') && S.tab === 'an') rgDrawTone();
  return ids;
};
insHash = function(){ const p = new URLSearchParams(); Object.entries(INS.params || {}).forEach(([k, v]) => { if (v != null && v !== '') p.set(k, v); });
  const q = p.toString(); return '#press-desk' + (INS.cur ? '/' + (RG_PD.slug[INS.cur] || INS.cur) : '') + (q ? '?' + q : ''); };
/* #press-desk/<view>, and the old #insights/<id> links; Tone by issue links open Data › Tone */
insParse = function(h){ const m = /^(?:insights|press-desk)(?:\/([a-z_-]+))?(?:\?(.*))?$/.exec(h || ''); if (!m) return null;
  const params = {}; if (m[2]) new URLSearchParams(m[2]).forEach((v, k) => params[k] = v);
  const id = m[1] ? (RG_UNSLUG[m[1]] || m[1]) : null;
  if (id === 'tone_topic'){ RG.toTone = true; RG.dt.p = params; return null; }
  return { id, params }; };
const rgInsShow = insShow;
insShow = function(id, params, force){
  if (id === 'tone_topic'){ RG.dt.p = Object.fromEntries(Object.entries(params || {}).filter(([, x]) => x != null && x !== ''));
    const s = $('#rgToneIssue') && $('#rgToneIssue').closest('.rp-sec'); if (s && s.classList.contains('rg-shut')) s.querySelector('.rg-sh').click();
    if (S.tab !== 'an') go('an'); rgDrawTone(true); setTimeout(() => { const t = $('#rgToneIssue'); if (t) t.scrollIntoView({ block: 'start' }); }, 0); return; }
  return rgInsShow(id, params, force);
};
insEntry = function(r){
  const out = [];
  if (INS.views.has('story_travel') && (r.reps || []).length) out.push(`<button class="linkbtn" data-ins-go="story_travel" data-ins-k="id" data-ins-v="${esc(r.id)}" title="See where this story ran, on a timeline">Trace this story</button>`);
  const ppl = (r.authors || []).filter(a => (AKIND.get(authorKey(a)) || 'person') === 'person');
  if (INS.views.has('reporters') && ppl.length) out.push(...ppl.slice(0, 3).map(a => `<button class="linkbtn" data-ins-go="reporters" data-ins-k="author" data-ins-v="${esc(a)}" title="${esc(a)} on the Press desk Pitch list">${ppl.length > 1 ? esc(a) + ' in Pitch' : 'Reporter in Pitch'}</button>`));
  return out.length ? `<div class="in-entry">${out.join('')}</div>` : '';
};
/* ---------- /REORG-v1 ---------- */
