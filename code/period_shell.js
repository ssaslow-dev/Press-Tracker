/* ---------- PERIOD-v1 (agent-relrule, 2026-10-27; Sammy: "Make the press desk have variable time periods") ----------
   One period bar at the top of Press desk, shared by Pitch, Releases, Bills and Story travel. Kept in the URL
   (#press-desk/<view>?per=90d, or per=custom&from=YYYY-MM-DD&to=YYYY-MM-DD) and remembered per viewer (localStorage, in
   try/catch). Default 24 months. Views read ctx.period {key, from, to, label, phrase} (from/to inclusive ISO dates, ''
   = open) and ctx.inPeriod(date); a change fires document event "ajg:period" (detail = the period) and redraws the view.
   Home (30-day rule) and the Data tab's own period are not affected. code/period_shell.js, installed by
   code/patch_period.py (apply_all step 4l) between these markers. */
const PD_KEY = 'ajg.pressdesk.period';
const PD_PRESETS = ['30d', '90d', '12m', '24m', 'this', 'last', 'all', 'custom'];
function pdSession(back){   // CA session: Dec 1 of the year before the odd first year .. Nov 30 of the even second year
  let y1 = +TODAY.slice(0, 4); if (y1 % 2 === 0) y1 -= 1; if (TODAY < `${y1 - 1}-12-01`) y1 -= 2; y1 -= 2 * (back || 0);
  return { from: `${y1 - 1}-12-01`, to: `${y1 + 1}-11-30`, name: `${y1}–${String(y1 + 1).slice(2)}` };
}
function pdMonthsBack(n){ const d = new Date(TODAY + 'T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() - n); return addDays(iso(d), 1); }
const pdDay = s => { const m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(s || ''); return m ? `${MONTHS_L[+m[2] - 1].slice(0, 3)} ${+m[3]}, ${m[1]}` : ''; };
function pdMake(key, from, to){
  const ok = s => /^\d{4}-\d\d-\d\d$/.test(s || '');
  if (!PD_PRESETS.includes(key)) key = '24m';
  if (key === 'custom'){ from = ok(from) ? from : ''; to = ok(to) ? to : ''; if (from && to && from > to) [from, to] = [to, from];
    if (!from && !to) key = 'all'; }
  const P = { '30d': [addDays(TODAY, -29), '', 'Last 30 days', 'in the last 30 days'], '90d': [addDays(TODAY, -89), '', 'Last 90 days', 'in the last 90 days'],
    '12m': [pdMonthsBack(12), '', 'Last 12 months', 'in the last 12 months'], '24m': [pdMonthsBack(24), '', 'Last 24 months', 'in the last 24 months'],
    'all': ['', '', 'All time', 'across all dates'] };
  if (P[key]) return { key, from: P[key][0], to: P[key][1], label: P[key][2], phrase: P[key][3] };
  if (key === 'this' || key === 'last'){ const s = pdSession(key === 'last' ? 1 : 0);
    return { key, from: s.from, to: key === 'this' ? '' : s.to, label: `${key === 'this' ? 'This' : 'Last'} session (${s.name})`, phrase: `in the ${s.name} session` }; }
  const lab = from && to ? `${pdDay(from)} – ${pdDay(to)}` : from ? `Since ${pdDay(from)}` : `Through ${pdDay(to)}`;
  return { key: 'custom', from, to, label: lab, phrase: from && to ? `from ${pdDay(from)} to ${pdDay(to)}` : from ? `since ${pdDay(from)}` : `through ${pdDay(to)}` };
}
const PD = { per: null };
(function pdInit(){ let s = null; try { s = JSON.parse(localStorage.getItem(PD_KEY) || 'null'); } catch(e){ s = null; }
  PD.per = s && s.key ? pdMake(s.key, s.from, s.to) : pdMake('24m'); })();
const pdIn = (d, per) => { per = per || PD.per; d = String(d || ''); if (!d) return !per.from && !per.to;
  return (!per.from || d >= per.from || (d.length < 10 && d >= per.from.slice(0, d.length))) && (!per.to || d.slice(0, 10) <= per.to); };
function pdParams(){ const p = { per: PD.per.key }; if (PD.per.key === 'custom'){ if (PD.per.from) p.from = PD.per.from; if (PD.per.to) p.to = PD.per.to; } return p; }
/* the URL carries the period; links and old hashes without one keep the viewer's period */
const pdHash0 = insHash;
insHash = function(){ const h = pdHash0(), q = new URLSearchParams(pdParams()).toString(); return h + (h.includes('?') ? '&' : '?') + q; };
const pdParse0 = insParse;
insParse = function(h){ const r = pdParse0(h); if (!r) return r; const p = r.params || {};
  if (p.per){ PD.per = pdMake(p.per, p.from, p.to); pdSave(); }
  delete p.per; delete p.from; delete p.to; delete p.win;   // old Pitch links (win=12/24) open the shared period
  return r; };
const pdCtx0 = insCtx;
insCtx = function(id){ const c = pdCtx0(id); c.period = Object.assign({}, PD.per); c.inPeriod = d => pdIn(d); return c; };
function pdSave(){ try { localStorage.setItem(PD_KEY, JSON.stringify({ key: PD.per.key, from: PD.per.from, to: PD.per.to })); } catch(e){} }
function pdBar(){
  const v = $('#view-in'); if (!v) return; let b = $('#pdPer');
  if (!b){ v.querySelector('.in-bar').insertAdjacentHTML('afterend', `<div class="card pad pd-per" id="pdPer" role="group" aria-label="Period">
    <label class="pd-l">Period<select class="sel" id="pdSel">${PD_PRESETS.map(k => `<option value="${k}">${k === 'custom' ? 'Custom…' : pdMake(k).label}</option>`).join('')}</select></label>
    <span class="pd-c" id="pdCustom"><label>From<input type="date" id="pdFrom"></label><label>To<input type="date" id="pdTo"></label><button type="button" class="btn" id="pdApply">Apply</button></span>
    <span class="pd-r" id="pdRange"></span></div>`);
    b = $('#pdPer');
    $('#pdSel').addEventListener('change', e => { const k = e.target.value;
      if (k === 'custom'){ $('#pdCustom').hidden = false; $('#pdFrom').value = PD.per.from || ''; $('#pdTo').value = PD.per.to || TODAY; $('#pdFrom').focus(); return; }
      pdSet(pdMake(k)); });
    $('#pdApply').addEventListener('click', () => pdSet(pdMake('custom', $('#pdFrom').value, $('#pdTo').value)));
    b.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('#pdFrom, #pdTo')) pdSet(pdMake('custom', $('#pdFrom').value, $('#pdTo').value)); });
  }
  $('#pdSel').value = PD.per.key; $('#pdCustom').hidden = PD.per.key !== 'custom';
  if (PD.per.key === 'custom'){ $('#pdFrom').value = PD.per.from || ''; $('#pdTo').value = PD.per.to || ''; }
  $('#pdRange').textContent = PD.per.from || PD.per.to ? `${PD.per.from ? pdDay(PD.per.from) : 'First story'} – ${PD.per.to ? pdDay(PD.per.to) : 'today'}` : 'Every date in the tracker';
}
function pdSet(per){
  PD.per = per; pdSave(); pdBar(); INS.drawn.clear();
  try { document.dispatchEvent(new CustomEvent('ajg:period', { detail: Object.assign({}, per) })); } catch(e){}
  if (S.tab === 'in' && INS.cur) insShow(INS.cur, INS.params, true);
}
document.head.insertAdjacentHTML('beforeend', `<style id="pd-css">
.pd-per{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;margin-top:12px;padding:10px 16px}
.pd-per .pd-l{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)}
.pd-per .pd-l select{text-transform:none;letter-spacing:0;font-weight:600;color:var(--ink)}
.pd-per .pd-c{display:flex;flex-wrap:wrap;align-items:center;gap:8px}.pd-per .pd-c[hidden]{display:none}
.pd-per .pd-c label{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--ink-2)}
.pd-per input[type=date]{padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--panel-2);color:inherit;font:inherit;font-size:13px}
.pd-per .pd-r{font-size:12.5px;color:var(--ink-3);margin-left:auto}
.pd-sum{font-size:13.5px;color:var(--ink);margin:2px 0 8px}
@media (max-width:640px){.pd-per .pd-l{width:100%}.pd-per .pd-l select{flex:1}.pd-per .pd-r{margin-left:0;width:100%}}
</style>`);
pdBar();
const pdShow0 = insShow;
insShow = function(id, params, force){ pdBar(); return pdShow0(id, params, force); };
/* ---------- /PERIOD-v1 ---------- */
