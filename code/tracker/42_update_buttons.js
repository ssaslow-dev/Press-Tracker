/* ---------- the two header buttons ----------
   "Update database" searches the web, adds the confirmed finds and translates new non-English ones. "Refresh from files" rates tone,
   reads authors and translates whatever is missing. NOSCHED-v1 (Sammy 2026-10-30): nothing is scheduled and the page starts nothing outside
   itself (no scheduled task, no connector call). A run ends with its finds saved in the tracker (the run log); to put them in the
   spreadsheet, Sammy asks Claude in chat to "save the last run to the sheet" (code/sheet_task_prompt.md). */
const SHEET_MSG = 'Saved in the tracker. To put it in the sheet, ask Claude in chat to “save the last run to the sheet”.';
const RA = { busy:false, steps:[], added:[] };
function raSteps(){
  if (!RA.steps.length) return '';
  const ic = { wait:'○', run:'…', done:'✓', warn:'!' };
  return raProgHtml() + `<ul class="ra-steps">${RA.steps.map(s => `<li class="${s.st}"><i>${ic[s.st]}</i><div><b>${esc(s.label)}</b>${s.note ? `<small>${esc(s.note)}</small>` : ''}</div></li>`).join('')}</ul>`;
}
async function runAll(mode, since){
  mode = mode === 'refresh' ? 'refresh' : 'find';
  if (RA.busy || U.busy || TQ.busy || AQ.busy) { openUpd('upd'); return; }
  RA.busy = true; RA.mode = mode; RA.sinceManual = mode === 'find' && since && !sinceError(since) ? since : '';   /* SINCE-v1: the dialog's optional date */
  RA.steps = (mode === 'find'
    ? [['find','Search the web for new stories'],['add','Add new stories'],['tr','Translate new non-English stories'],['sheet','Save them in the tracker']]
    : [['tone','Rate tone on saved pages'],['auth','Read authors on saved pages'],['tr','Translate non-English stories'],['sheet','Save the changes in the tracker']]
  ).map(([k,label]) => ({k, label, st:'wait', note:''}));
  const set = (k, st, note) => { const s = RA.steps.find(x => x.k===k); s.st = st; s.note = note || ''; drawUpd(); raBtn(); };
  const btn = $(mode === 'find' ? '#runFind' : '#runRefresh');
  btn.classList.add('busy'); RA.nst = RA.ns = 0; if (!TRQ.busy) TRQ.done = TRQ.total = 0; if (mode === 'refresh') raTrack(true); raBtn(); openUpd('upd');
  try {
    RA.added = []; RA.reprints = 0; RA.rows = []; RA.run = newRunId(); RA.noStore = false; RA.hbOff = false; LOG.hbAt0 = ''; const snap0 = snapStories();
    try {   /* RUNPERSIST-v1 (c): an error after this point stops the run with a message and a saved doc, not a button stuck at "…" */
    if (mode === 'find'){
      set('find', 'run'); U.phase = 'idle';
      /* RUNPERSIST-v1 (a): a first progress doc before any search, so a closed tab or a rate limit leaves a trace and an unreachable store is known at once */
      const persisted = await runHeartbeat(RA.run, { step: 'start' }); RA.noStore = !persisted;
      const NOSTORE = 'Run log unavailable (shared store not reachable): results will stay in this browser and will NOT reach the spreadsheet. You can still copy them for the spreadsheet.';
      if (RA.noStore) set('find', 'run', NOSTORE);
      await runUpdate();
      const nf = U.found.length, nrp = U.reprints.length;
      set('find', U.err && !nf && !nrp ? 'warn' : 'done', (U.err && !nf && !nrp ? U.err : `${pl(nf,'new story','new stories')} found` + (nrp ? `, and ${pl(nrp,'reprint')} of stories already in the log` : '') + (U.leginfo ? `. ${U.leginfo}` : '')) + (RA.noStore ? ' ' + NOSTORE : ''));
      set('add', 'run');
      U.found.forEach(r => r._on = r.conf==='Confirmed' && r._claude);
      // reprints on sites the log already names go straight in; the rest wait below for a proper outlet name
      U.reprints.forEach(p => p._on = !!p._named);
      const rpNames = U.reprints.filter(p => p._on).map(p => p.outlet);
      const nOn = U.found.filter(r => r._on).length;
      const prevIds = new Set(D.map(r => r.id));
      let res = { n: 0, nr: 0 };
      if (nOn || rpNames.length) res = await saveFound() || res;
      U.reprints.forEach(p => p._on = true);
      RA.added = D.filter(r => !prevIds.has(r.id)).map(r => r.id); RA.reprints = res.nr;
      const left = U.found.length, rleft = U.reprints.length;
      RA.pages = res.np || 0;
      set('add', 'done', `${pl(nOn,'story','stories')} added` + (RA.pages ? ` (${pl(RA.pages,'page')} saved)` : '') + (res.nr ? `, and ${pl(res.nr,'reprint')} added (${rpNames.join(', ')})` : '')
        + (left ? `. ${pl(left,'story','stories')} Claude couldn’t confirm ${left===1?'is':'are'} below for you to check and add` : '')
        + (rleft ? `. ${pl(rleft,'reprint')} on ${rleft===1?'a site':'sites'} not yet in the log ${rleft===1?'is':'are'} below for you to name and add` : '') + '.');
    } else {
      const pt = pendingTone();
      if (!pt.length) set('tone', 'done', 'Every saved page has a tone.');
      else if (!sampler) set('tone', 'warn', 'Needs the tracker open in Claude.');
      else { set('tone', 'run', pl(pt.length,'page')); await rateTones(pt); set('tone', TQ.msg ? 'warn' : 'done', TQ.msg || `${pl(TQ.done,'page')} rated.`); }
      const pa = pendingAuthor();
      if (!pa.length) set('auth', 'done', 'Every saved page has been checked for an author.');
      else if (!sampler) set('auth', 'warn', 'Needs the tracker open in Claude.');
      else { set('auth', 'run', pl(pa.length,'page')); await findAuthors(pa); set('auth', AQ.msg ? 'warn' : 'done', AQ.msg || `${pl(AQ.done,'page')} read.`); }
    }
    const scope = mode === 'find' ? new Set(RA.added) : null;
    const ptr = pendingTr().filter(id => !scope || scope.has(id));
    const pst = [];   /* TOKENS-v1b */ /* whole-story translation is click-only: the story panel's Translate button (Sammy 2026-10-27) */
    if (!ptr.length && !pst.length) set('tr', 'done', mode === 'find' ? 'No new non-English stories.' : 'Every non-English story has an English headline.');
    else if (!sampler) set('tr', 'warn', 'Needs the tracker open in Claude.');
    else {
      TRQ.msg = '';
      set('tr', 'run', pl(ptr.length,'headline') + (pst.length ? ` and ${pl(pst.length,'story','stories')}` : ''));
      if (ptr.length) await translateHeadlines(ptr);
      const nh = ptr.length ? TRQ.done : 0; let ns = 0; RA.nst = pst.length; RA.ns = 0; for (const id of pst){ if (await translateStory(id)) ns++; RA.ns++; }
      set('tr', TRQ.msg || ns < pst.length ? 'warn' : 'done', TRQ.msg || `${pl(nh,'headline')} translated` + (pst.length ? `, and ${pl(ns,'whole story','whole stories')} of ${fmt(pst.length)}.` : '.'));
    }
    const dif = diffStories(snap0);
    // rows: what this run puts in the spreadsheet, in the Coverage columns with placeholder IDs (the sheet task writes them and adds "ids")
    RA.hbOff = true; await hbFlush();   /* RUNPERSIST-v1: no progress write may land after the final doc */
    const saved = await saveRun(RA.run, { at: new Date().toISOString(), mode, status: 'done', stories: RA.added, reprints: dif.reprints, tones: dif.tones, authors: dif.authors, translations: dif.translations, rows: covCompact(RA.rows || []),
      searched_to: mode === 'find' && !U.err && U.plan && U.failed <= U.plan * 0.02 && !U.sinceManual ? TODAY : '',   /* SINCE-v1: a manual date later than the usual start would leave a gap, so it never advances searched_to; an earlier one still ends today, never backwards */
      since: mode === 'find' ? (U.since || '') : '', since_manual: mode === 'find' && !!U.sinceManual,   /* SINCE-v1: the date this run searched from */   /* TOKENS-v1; BUTTONOPT-v1 (A-B4): only when at most 2% of searches failed */
      failed: mode === 'find' ? (U.failed || 0) + ' of ' + (U.plan || 0) : '',
      found_by: mode === 'find' ? (RA.rows || []).reduce((o, x) => { const k = String(x._found_by || '').split(':')[0]; if (k) o[k] = (o[k] || 0) + 1; if (x._backfill) o.backfill = (o.backfill || 0) + 1; return o; }, {})   /* REQ-13: backfill finds counted apart */ : {}, gnews: mode === 'find' ? (U.gnews || 0) : 0,   /* RECALL-v1 */
      bills_new: mode === 'find' ? (U.newbills || []).slice(0, 50) : [], leginfo: mode === 'find' ? VS(U.leginfo || '', 300) : '',   /* AUTO-v1 */
      releases_new: mode === 'find' ? (U.newrels || []).slice(0, 10) : [],   /* RELBUTTON-v1: 5 to fetch + dual-post caucus copies (dup_of, unfetched) */ relcheck: mode === 'find' ? VS(U.relcheck || '', 300) : '',   /* RELCHECK-v1 */
      print_pages: mode === 'find' ? (U.printPages || []).slice(0, 100) : [],   /* REQ-11: e-paper pages (needs clipping), not stories */
      lookups: mode === 'find' ? (U.lookups || []).slice(0, 100) : [],   /* LEARN-v1: new confirmed answers; the sheet task appends them to lookup_cache.json */
      left: mode === 'find' ? U.skipped.slice(0, 150).map(x => ({ hl: VS(x.c.title || x.c.url, 200), outlet: hostOf(x.c.url), date: VS(x.c.published, 10), why: VS(x.why, 200) })) : [],
      unconfirmed: mode === 'find' ? U.found.filter(r => !r._on).slice(0, 150).map(r => ({ hl: VS(r.hl, 200), outlet: VS(r.outlet, 120), date: VS(r.date, 10), link: VS(r.link, 500), why: VS(r.why, 200) })) : [] });
    if (!saved){ set('sheet', 'warn', 'The run log could not be saved, so nothing is queued for the sheet. Use “Copy for spreadsheet” to keep the rows, or run it again once you are signed in.'); return; }   /* RUNPERSIST-v1 (e) */
    if (mode === 'find' && !RA.added.length && !RA.reprints && !(U.newbills || []).length && !(U.newrels || []).length){   /* RELCHECK-v1 */   /* AUTO-v1: new bills go to the sheet task too */ set('sheet', 'done', 'Nothing new to write.'); return; }
    set('sheet', 'done', SHEET_MSG);   /* NOSCHED-v1: no trigger; the run doc is the hand-off */
    } catch(e){
      const msg = String(e && (e.message || e)), s = RA.steps.find(x => x.st === 'run') || RA.steps[0];
      RA.hbOff = true; await hbFlush().catch(() => {}); RA.steps.forEach(x => { if (x.st === 'run') x.st = 'warn'; });
      set(s.k, 'warn', 'Stopped by an error: ' + VS(msg, 200));
      await saveRun(RA.run, { at: new Date().toISOString(), mode, status: 'error', error: VS(msg, 300), rows: covCompact(RA.rows || []) });
      return;
    }
  } finally {
    RA.busy = false; btn.classList.remove('busy'); raTrack(false); raBtn(); drawUpd(); render();
  }
}
/* Refresh from files progress: the steps in this page fill the bar; the last one (saving in the tracker) completes it. */
let raTimer = null;
function raTrack(on){ clearInterval(raTimer); raTimer = on ? setInterval(drawRaProg, 1000) : null; }
function raPct(){
  if (RA.mode !== 'refresh' || !RA.steps.length) return null;
  const frac = { tone: () => TQ.total ? TQ.done / TQ.total : 0, auth: () => AQ.total ? AQ.done / AQ.total : 0,
    tr: () => { const t = (TRQ.total || 0) + (RA.nst || 0); return t ? ((TRQ.done || 0) + (RA.ns || 0)) / t : 0; } };
  let p = 0;
  for (const s of RA.steps){
    if (s.k === 'sheet'){
      if (s.st === 'warn') return { pct: Math.round(p), label: 'The run was not saved', cls: 'warn' };
      if (s.st === 'done') return { pct: 100, label: 'Done. Saved in the tracker.', cls: 'ok' };
      return { pct: Math.round(p), label: s.st === 'run' ? 'Saving in the tracker' : 'Working in this page' };
    }
    p += s.st === 'done' || s.st === 'warn' ? 20 : s.st === 'run' ? 20 * Math.min(1, (frac[s.k] || (() => 0))()) : 0;
  }
  return { pct: Math.round(p), label: '' };
}
function raCurLabel(){ const s = RA.steps.find(x => x.st === 'run'); return s ? s.label : 'Working'; }
function raProgHtml(){
  const r = raPct(); if (!r) return '';
  return `<div class="ra-prog ${r.cls || ''}" role="progressbar" aria-label="Refresh from files" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${r.pct}" id="raProg">`
    + `<div class="row"><span id="raProgLbl">${esc(r.label || raCurLabel())}</span><b id="raProgPct">${r.pct}%</b></div><div class="bar"><i id="raProgBar" style="width:${r.pct}%"></i></div></div>`;
}
function drawRaProg(){
  const r = raPct(), strip = $('#raStrip');
  const live = r && RA.busy;
  strip.classList.toggle('det', !!(r && RA.mode === 'refresh')); strip.hidden = !live; if (r) strip.style.setProperty('--ra-pct', r.pct + '%');
  const rb = $('#runRefresh');
  if (!r) return; const box = $('#raProg'); if (!box) return;
  box.className = 'ra-prog ' + (r.cls || ''); box.setAttribute('aria-valuenow', r.pct);
  $('#raProgBar').style.width = r.pct + '%'; $('#raProgPct').textContent = r.pct + '%'; $('#raProgLbl').textContent = r.label || raCurLabel();
  if (r.pct >= 100 || r.cls === 'warn'){ raTrack(false); if (rb) rb.querySelector('.lbl').textContent = RA_IDLE.refresh; }
}
// header buttons: while a run is going the pressed one spins and names its step, the other is disabled, and a strip moves under the header
const RA_LBL = { find:'Searching the web…', add:'Adding stories…', tr:'Translating…', tone:'Rating tone…', auth:'Reading authors…', sheet:'Saving in the tracker…' };
const RA_IDLE = { find:'Update database', refresh:'Refresh from files' };
let raDoneT;
function raBtn(){
  const fb = $('#runFind'), rb = $('#runRefresh'), strip = $('#raStrip');
  [[fb,'find'],[rb,'refresh']].forEach(([b, m]) => {
    const me = RA.busy && RA.mode === m, lbl = b.querySelector('.lbl');
    const cur = me && (RA.steps.find(s => s.st === 'run') || RA.steps.find(s => s.st === 'wait'));
    let t = cur ? RA_LBL[cur.k] : 'Working…';
    if (me && cur && cur.k === 'find' && U.busy){ const n = (U.step.match(/\((\d+) of (\d+)\)/) || []); t = /^Searching/.test(U.step) && n[1] ? `Searching ${n[1]} of ${n[2]}…` : /^Opening/.test(U.step) ? 'Checking pages…' : /^Claude/.test(U.step) ? 'Claude is reviewing…' : t; }
    lbl.textContent = me ? t : RA_IDLE[m];
    b.disabled = RA.busy && !me; b.setAttribute('aria-busy', me ? 'true' : 'false');
  });
  strip.hidden = !RA.busy; drawRaProg();
  if (!RA.busy && RA.steps.length){
    const b = RA.mode === 'refresh' ? rb : fb; b.classList.add('done'); b.querySelector('.lbl').textContent = 'Done';
    clearTimeout(raDoneT); raDoneT = setTimeout(() => { b.classList.remove('done'); b.querySelector('.lbl').textContent = RA_IDLE[RA.mode === 'refresh' ? 'refresh' : 'find']; }, 6000);
  }
}
$('#updScrim').onclick = closeUpd;
$('#upd').addEventListener('keydown', e => { if (e.key==='Escape'){ e.stopPropagation(); closeUpd(); } });
$('#upd').addEventListener('click', e => {
  if (e.target.closest('[data-uclose]')) closeUpd();
  if (e.target.closest('#updGo') || e.target.closest('#updAgain')) runAll('find');
  if (e.target.closest('#updSave')) saveSheet();   /* TOKENS-v1 */
  if (e.target.closest('#updRefresh')) runAll('refresh');
  if (e.target.closest('[data-nbdone]')){ saveRun(newRunId(), { at: new Date().toISOString(), mode: 'newsbank', newsbank: TODAY }).then(() => drawUpd()); }   /* RECALL-v1: NewsBank refresh logged */
  if (e.target.closest('#updStop') && U.ctl) U.ctl.abort();
  if (e.target.closest('#updAdd')) saveFound();
  if (e.target.closest('[data-goclips]')){ closeUpd(); go('db'); }
  if (e.target.closest('#updCopy')) copyFound();
  if (e.target.closest('#updCopyPrint')) copy((U.printPages || []).map(p => [p.date || '', p.outlet, p.hl || '', p.url].join('\t')).join('\n'), `Copied ${pl((U.printPages || []).length,'print page')}.`);
});
$('#upd').addEventListener('change', e => {
  const t = e.target;
  if (t.dataset.ri != null){ const p = U.reprints[+t.dataset.ri]; if (!p) return;
    if (t.type==='checkbox'){ p._on = t.checked; drawUpd(); } else if (t.dataset.rf==='outlet'){ p.outlet = t.value.replace(/[;\n]+/g,' ').trim().slice(0,120) || p.outlet; }
    return; }
  const i = t.dataset.ui; if (i == null) return; const r = U.found[+i]; if (!r) return;
  if (t.type==='checkbox'){ r._on = t.checked; drawUpd(); return; }
  if (t.dataset.uf==='date'){ if (/^\d{4}-\d{2}-\d{2}$/.test(t.value)){ r.date = t.value; r.year = +t.value.slice(0,4); r._nodate = false; r._datecheck = false; r._dateSrc = 'edited'; } return; }
  if (t.dataset.uf==='bills'){ r.bills = splitBills(t.value); return; }
  if (t.dataset.uf){ r[t.dataset.uf] = t.value; if (t.dataset.uf==='topic') r.issue = t.value; }
});


/* RUNCONFIRM-v1 (rp-final 2026-10-28, Sammy comment 83b36e23): "Are you sure?" before either header button starts a run. In-page
   modal (not window.confirm): title, one sentence, Cancel + primary confirm; Esc / click outside cancel; focus starts on Cancel and
   stays in the dialog. While a run is going the header buttons still just open the Update panel (runAll does that, no prompt). */
const RC_TXT = {
  find: { t: 'Update the database?', d: 'Searches the web for new coverage of Gabriel and saves what it finds in this tracker. To put it in the master spreadsheet, ask Claude in chat afterwards.', ok: 'Update' },
  refresh: { t: 'Refresh from files?', d: 'Rates tone, reads authors and translates what is missing, and saves the changes in this tracker.', ok: 'Refresh' } };
document.head.insertAdjacentHTML('beforeend', `<style id="runconfirm-css">
.rc-scrim{position:fixed;inset:0;background:rgba(8,12,16,.45);z-index:90;display:flex;align-items:center;justify-content:center;padding:16px}
.rc-scrim[hidden]{display:none}
.rc-box{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);width:100%;max-width:420px;padding:20px 20px 16px}
.rc-box h2{margin:0 0 8px;font:700 var(--fs-h2)/1.25 var(--f-display);color:var(--ink)}
.rc-box p{margin:0 0 18px;font-size:var(--fs-lg);line-height:1.5;color:var(--ink-2)}
.rc-since{display:flex;flex-direction:column;gap:6px;margin:-6px 0 16px;font-size:var(--fs-md);color:var(--ink-2)}
.rc-since[hidden]{display:none}
.rc-since input{border:1px solid var(--line);border-radius:8px;padding:6px 8px;background:var(--panel);color:var(--ink);font-size:var(--fs-md);max-width:200px}
.rc-since small{color:var(--ink-3,var(--ink-2));font-size:var(--fs-sm)}
.rc-err{margin:-8px 0 14px;color:var(--bad,#b3261e);font-size:var(--fs-md)}
.rc-err[hidden]{display:none}
.rc-acts{display:flex;justify-content:flex-end;gap:8px}
@media (max-width:420px){.rc-acts .btn{flex:1}}
</style>`);
document.body.insertAdjacentHTML('beforeend', '<div class="rc-scrim" id="rcScrim" hidden><div class="rc-box" role="alertdialog" aria-modal="true" aria-labelledby="rcT" aria-describedby="rcD"><h2 id="rcT"></h2><p id="rcD"></p><label class="rc-since" id="rcSinceWrap" hidden><span>Since (optional)</span><input type="date" id="rcSince" min="1990-01-01"><small>Blank searches from where the last update stopped. A date searches only for coverage on or after it.</small></label><div class="rc-err" id="rcErr" role="alert" hidden></div><div class="rc-acts"><button type="button" class="btn" id="rcNo">Cancel</button><button type="button" class="btn primary" id="rcYes"></button></div></div></div>');
let RC_MODE = '', RC_BACK = null;
function rcClose(){ $('#rcScrim').hidden = true; RC_MODE = ''; if (RC_BACK && RC_BACK.focus) RC_BACK.focus(); RC_BACK = null; }
function raConfirm(mode, from){
  if (RA.busy || U.busy || TQ.busy || AQ.busy) return runAll(mode);   /* a run is going: same as before (opens the panel) */
  const x = RC_TXT[mode === 'refresh' ? 'refresh' : 'find'];
  RC_MODE = mode === 'refresh' ? 'refresh' : 'find'; RC_BACK = from || null;
  $('#rcT').textContent = x.t; $('#rcD').textContent = x.d; $('#rcYes').textContent = x.ok;
  $('#rcSinceWrap').hidden = RC_MODE !== 'find'; $('#rcSince').value = ''; $('#rcSince').max = TODAY; $('#rcErr').hidden = true; $('#rcErr').textContent = '';   /* SINCE-v1: blank = the current behaviour */
  $('#rcScrim').hidden = false; $('#rcNo').focus();
}
$('#rcNo').onclick = rcClose;
$('#rcYes').onclick = () => { const m = RC_MODE, v = m === 'find' ? $('#rcSince').value.trim() : '', er = sinceError(v);
  if (er){ $('#rcErr').textContent = er; $('#rcErr').hidden = false; $('#rcSince').setAttribute('aria-invalid', 'true'); $('#rcSince').focus(); return; }   /* SINCE-v1: no future dates, nothing before 1990 */
  $('#rcSince').removeAttribute('aria-invalid'); RC_BACK = null; rcClose(); if (m) runAll(m, v); };
$('#rcSince').addEventListener('input', () => { $('#rcErr').hidden = true; $('#rcSince').removeAttribute('aria-invalid'); });
$('#rcScrim').addEventListener('click', e => { if (e.target.id === 'rcScrim') rcClose(); });
$('#rcScrim').addEventListener('keydown', e => {
  if (e.key === 'Escape'){ e.preventDefault(); e.stopPropagation(); rcClose(); return; }
  if (e.key === 'Tab'){ const f = [$('#rcSince'), $('#rcNo'), $('#rcYes')].filter(x => x && x.offsetParent !== null), a = f[0], b = f[f.length - 1]; if (e.shiftKey && document.activeElement === a){ e.preventDefault(); b.focus(); } else if (!e.shiftKey && document.activeElement === b){ e.preventDefault(); a.focus(); } } });
$('#runFind').onclick = e => raConfirm('find', e.currentTarget);   /* replaces 41's direct runAll wiring */
$('#runRefresh').onclick = e => raConfirm('refresh', e.currentTarget);
