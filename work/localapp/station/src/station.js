/* AJG Update Station: the station-only layer around the tracker's own Update code (code/tracker/*.js, unmodified).
   Order of events: step 1 reads the "for Update" file in this browser -> its blocks are put where the tracker code reads them
   (<script type=application/json id=...>) -> the db collections the Update button remembers things in (runs, clips, reprints, edits)
   are seeded from the file's memory -> only then the tracker code is started -> step 3 packs what this session wrote into the
   update folder (a zip of data: manifest.json + db/<collection>/<id>.json, FORMAT.md section 2). */
(function () {
'use strict';
const STATION_VERSION = 'station-1';
const $ = s => document.querySelector(s);
const clone = o => JSON.parse(JSON.stringify(o === undefined ? null : o));
const nowIso = () => new Date().toISOString().replace(/\.\d+Z$/, 'Z');
const fmtN = n => Number(n).toLocaleString('en-US');
const SEEDED = ['runs', 'clips', 'reprints', 'edits'];
const PACK_COLLS = ['runs', 'pages', 'reprints', 'authors', 'translations', 'tones', 'edits'];   // = the saver's load_db, FORMAT.md
const ID_RX = /^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/;
const RESERVED = new Set(['CON', 'PRN', 'AUX', 'NUL'].concat([1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => 'COM' + i), [1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => 'LPT' + i)));

const S = { loaded: false, file: null, seq: 0, lastPacked: 0, lastZip: null, realDb: null, busyPack: false, noMirror: new Set() };   // noMirror: documents that hold NewsBank text are never copied to the artifact db (NEWSBANKPDF-v1)
const sess = {};            // collection -> Map(id -> {data, seq}) of documents the tracker code wrote after the file was loaded
PACK_COLLS.forEach(c => { sess[c] = new Map(); });

/* ---------- the db the tracker code sees: in memory, seeded from the file (nothing is read from or written to a shared store) ---------- */
function makeMemDb() {
  const cols = new Map();
  const col = n => cols.get(n) || cols.set(n, { docs: new Map(), subs: new Set() }).get(n);
  const snap = c => { const docs = [...c.docs].map(([id, d]) => ({ id, exists: true, data: () => clone(d) })); return { docs, size: docs.length, empty: !docs.length, forEach: f => docs.forEach(f) }; };
  const notify = c => { const sn = snap(c); c.subs.forEach(cb => queueMicrotask(() => { try { cb(sn); } catch (e) { console.error('snapshot callback', e); } })); };
  const track = (name, id, data) => {
    if (!S.loaded || !(sess[name] || name === 'clips')) return;
    const seq = ++S.seq;
    if (sess[name]) { if (data === null) sess[name].delete(id); else sess[name].set(id, { data: clone(data), seq }); }
    if (!S.recovering) mirror(name, id, data === null ? null : clone(data), seq);
    updatePackUi();
  };
  const api = {
    collection(name) {
      const c = col(name);
      return {
        id: name, path: name,
        doc(id) {
          id = String(id);
          return {
            id, path: name + '/' + id,
            async get() { const has = c.docs.has(id); return { id, exists: has, data: () => (has ? clone(c.docs.get(id)) : undefined) }; },
            async set(data) { const d = clone(data); if (name === 'runs' && d && d.mode === 'find' && d.status === 'done' && S.loaded) markEnd(d); if (name === 'runs' && d && Array.isArray(d.rows)) prAnnotateRows(d.rows, pg => col('pages').docs.get(pg)); c.docs.set(id, d); track(name, id, d); notify(c); if (name === 'runs' && d && d.status === 'done' && S.loaded) xdSoon(); },
            async update(data) { const d = Object.assign({}, c.docs.get(id) || {}, clone(data)); c.docs.set(id, d); track(name, id, d); notify(c); },
            async delete() { c.docs.delete(id); track(name, id, null); notify(c); },
            onSnapshot(cb) { const f = c.subs.add(cb) && (() => c.subs.delete(cb)); queueMicrotask(() => { try { cb({ id, exists: c.docs.has(id), data: () => clone(c.docs.get(id)) }); } catch (e) {} }); return f; },
          };
        },
        async get() { return snap(c); },
        onSnapshot(cb, err) {
          c.subs.add(cb); const sn = snap(c); queueMicrotask(() => { try { cb(sn); } catch (e) { console.error('snapshot callback', e); } });
          if (name === 'runs' && S.afterRunsSub) { const f = S.afterRunsSub; S.afterRunsSub = null; setTimeout(f, 40); }   // the run history has arrived: the Update panel can draw
          return () => c.subs.delete(cb);
        },
      };
    },
    seed(name, id, data) { col(name).docs.set(String(id), clone(data)); },
  };
  return api;
}
const mem = makeMemDb();
/* STFIX 5: a web run that did not finish its search cleanly must never look like "nothing new". The tracker's own code ends such a run with status "done", no stories and an empty "searched_to" and keeps the reason
   (U.err) only on the page; the run document says nothing. At the moment the final run document is written, the reason is read from the tracker's state and written into the document (ended_early) and the page shows
   a red note until a later web run finishes cleanly. A manual "since" date also leaves searched_to empty on purpose; that is not an early end. */
S.endedEarly = new Map();   // run id -> { why, ... }
function markEnd(d) {
  const e = window.__nb && window.__nb.webEnd ? window.__nb.webEnd() : null;
  if (d.searched_to) { S.endedLast = null; showEnd(); return; }   // a clean web run: the earlier warning no longer applies
  if (d.since_manual) return;
  const why = [];
  if (e && e.err && !/^Added /.test(e.err)) why.push(String(e.err));
  if (e && e.aborted) why.push('the search was stopped');
  const m = /^(\d+) of (\d+)$/.exec(String(d.failed || ''));
  if (m && +m[2] && +m[1] > +m[2] * 0.02) why.push(m[1] + ' of ' + m[2] + ' searches or page reads failed');
  if (!why.length) why.push('the tracker did not mark the search as finished (its “searched to” date was not moved)');
  d.ended_early = { why: why.join('; ').slice(0, 400), searches_planned: e ? e.plan : (m ? +m[2] : 0), searches_done: e ? e.done : 0, step: e ? String(e.step || '').slice(0, 120) : '', candidates: e ? e.cands : 0, found: d.stories ? d.stories.length : 0 };
  S.endedEarly.set(d.at || String(Date.now()), d.ended_early);
  S.endedLast = d.ended_early; showEnd();
}
function showEnd() {
  const el = document.getElementById('stEndNote'); if (!el) return;
  const e = S.endedLast;
  el.hidden = !e;
  if (e) el.textContent = 'The web search did NOT finish: ' + e.why + (e.searches_planned ? ' (' + e.searches_done + ' of ' + e.searches_planned + ' searches done, ' + e.found + ' stories found)' : '') + '. This is not the same as “nothing new”: stories may be missing, and the date the search reached was not moved. Press Update database again. What it did find is still in the update folder.';
}

/* ---------- the window the tracker code sees: the real one, except window.claude (its db is the in-memory one above) ---------- */
const realClaude = window.claude;
/* Claude's consent is asked at the first call, so a "no" only shows then: remember it and show the red note above the Update panel */
function plainErr(e) {
  const c = e && e.code, m = String(e && e.message || e || '');
  if (c === 'server_not_connected' || c === 'server_not_found' || c === 'selection_required') return 'Stopped. TinyFish is not connected on this account. In claude.ai open Settings, Connectors, connect TinyFish, then reload this page.';
  if (c === 'needs_reauth') return 'Stopped. The TinyFish connection has lapsed. Reconnect TinyFish in claude.ai (Settings, Connectors), then reload this page.';
  if (c === 'not_in_manifest' || c === 'approval_required' || c === 'consent_required' || c === 'not_granted' || c === 'capability_disabled' || c === 'capability_removed') return 'Stopped. TinyFish or Claude was not allowed for this page. Allow it from the page’s Permissions menu, then reload this page.';
  if (c === 'blocked_by_policy') return 'Stopped. Your organization’s policy blocks this for the page. Ask your administrator.';
  if (c === 'cancelled') return 'Stopped.';
  return 'Stopped: ' + m;
}
function sampleDenied(e) { S.sampleDeniedFlag = true; if (e && (e.code === 'not_granted' || e.code === 'unavailable')) { const n = document.getElementById('stSampleNote'); if (n) n.hidden = false; } }
/* PRJUDGE-v1: the classify call is asked, as well, whether each item is a pure press release (a station-layer wrapper around the prompt: the tracker's own prompt
   text is untouched). The answers, with each item's own text, are kept by link (S.pr) so the proposed rows can carry the decision and its reason. */
S.pr = new Map();
const prKey = u => String(u || '').toLowerCase().replace(/^https?:\/\/(www\.)?/, '').replace(/[#?].*$/, '').replace(/\/+$/, '');
window.__prRel = () => (S.file && S.file.release_texts && S.file.release_texts.rel) || {};
function prCall(v, t, a) {
  const prompt = typeof a[0] === 'string' ? a[0] : '', aug = PRJudge.augmentPrompt(prompt);
  const rest = a.slice(1);
  return Promise.resolve(v.apply(t, [aug].concat(rest))).then(res => {
    if (aug !== prompt) { try {
      const its = PRJudge.itemsOfPrompt(prompt);
      its.forEach((it, j) => { const k = Array.isArray(res) ? (res.find(o => o && +o.n === it.n) || res[j]) : null; S.pr.set(prKey(it.url), { text: it.text, title: it.title, claude: k && k.press_release !== undefined ? { press_release: k.press_release, pr_why: k.pr_why } : null }); });
    } catch (e) {} }
    return res;
  });
}
/* what a row carries of the decision (PRJUDGE-v2): the verdict, the reason, who judged, the outlet type, whose release (his / other) and, for a copy of his, the release id */
const prRecord = j => { const o = { v: j.v, why: j.why, by: j.by, type: j.type }; if (j.issuer) o.issuer = j.issuer; if (j.release) o.release = j.release; if (j.mode) o.mode = j.mode; return o; };
window.__prRecord = prRecord;
/* proposed rows of a web run: the decision for each find, from its text and Claude's answer; "Yes" fills Press release (the PC save fills blanks only) */
function prAnnotateRows(rows, pageDoc) {
  (rows || []).forEach(r => {
    if (!r || r._pr) return;
    let rec = S.pr.get(prKey(r['Publisher link']));
    if (!rec && r._page && pageDoc) { const pd = pageDoc(r._page); if (pd && pd.clean) rec = { text: String(pd.clean).replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 6000), title: pd.title || '', claude: null }; }   // a reprint candidate is not classified by Claude: its saved page text is judged by the text signals
    if (!rec) return;
    const j = PRJudge.judge({ text: rec.text, title: rec.title, outlet: r['Outlet'], url: r['Publisher link'], claude: rec.claude, date: r['Date'], rel: window.__prRel() });
    r._pr = prRecord(j);
    if (j.v === 'yes') { r['Press release'] = 'Yes'; r['Team note'] = ('press release: ' + j.why + (r['Team note'] ? '; ' + r['Team note'] : '')).slice(0, 600); }
  });
}
/* A plain wrapper, not a Proxy: the runtime freezes the sample namespace, and a Proxy may not hand back a different value for a frozen property
   (a JavaScript rule). The Proxy here made every Claude call fail on 2026-11-04, so the whole run's finds came back "Not reviewed by Claude". */
function sampleWatch(f) {
  const w = (...a) => Promise.resolve(f(...a)).catch(e => { sampleDenied(e); throw e; });
  w.json = (...a) => prCall(f.json, f, a).catch(e => { sampleDenied(e); throw e; });
  for (const k of Object.keys(f)) if (k !== 'json' && !(k in w)) { const v = f[k]; w[k] = typeof v === 'function' ? (...a) => v.apply(f, a) : v; }
  if (typeof f.limits === 'function' && !w.limits) w.limits = (...a) => f.limits(...a);
  return w;
}
const claudeForTracker = {
  use: async name => {
    if (name === 'db') return mem.collection ? mem : null;
    try {
      const r = realClaude && realClaude.use ? await realClaude.use(name) : null;
      if (name === 'sample' && typeof r === 'function') return sampleWatch(r);
      return r;
    } catch (e) { return null; }
  },
};
/* The proxy's target is a plain empty object, not window: the runtime now defines window.claude as read-only and non-configurable, and a proxy on
   window may not answer a different value for such a property (a JavaScript rule), which stopped the Update button. Every read and write still goes to window. */
const winProxy = new Proxy({}, {
  get(_, k) { if (k === 'claude') return claudeForTracker; const v = window[k]; return typeof v === 'function' && !/^[A-Z]/.test(String(k)) ? v.bind(window) : v; },
  set(_, k, v) { window[k] = v; return true; },
  has(_, k) { return k in window; },
});
window.__stationWin = winProxy;

/* The tracker code fetches data/release_texts.json (press-release sentences for the release-pickup searches) and, at start, articles/manifest.json
   (saved copies, which the station does not have). The first is answered from the file, the second with a plain 404. */
const origFetch = window.fetch ? window.fetch.bind(window) : null;
window.fetch = function (input, init) {
  const u = typeof input === 'string' ? input : (input && input.url) || '';
  if (/(^|\/)data\/release_texts\.json(\?|$)/.test(u)) return Promise.resolve(new Response(JSON.stringify(S.file && S.file.release_texts ? S.file.release_texts : { v: 1, rel: {} }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
  if (/^(\.\/)?(articles|img|data|pdf|copies)\//.test(u)) return Promise.resolve(new Response('', { status: 404 }));
  return origFetch ? origFetch(input, init) : Promise.reject(new Error('fetch unavailable'));
};

/* ---------- optional recovery (REQ-2): a closed tab must not lose a run ----------
   Everything the tracker code writes after the file is loaded is also copied, best effort, to the artifact db (collection "recover", one
   document per tracker document, keyed to this file). It is scratch: the station never reads it for the button's memory. It is read only
   to offer "Recover" when the same file is loaded again after a reload. Nothing is deleted; a packed point is kept in "recoverstate". */
const MIRROR = new Set(PACK_COLLS.concat(['clips']));
const mirrorQ = new Map(); let mirroring = false, mirrorFail = 0;
const fileKey = () => S.file.fingerprint.workbook_sha256.slice(0, 12) + '-' + String(S.file.created_at || '').replace(/[^0-9]/g, '');
function mirror(coll, id, data, seq) {
  if (!S.realDb || !MIRROR.has(coll) || S.noMirror.has(coll + '.' + id)) return;
  mirrorQ.set(coll + '.' + id, { coll, id, data, seq });
  if (!mirroring) drain();
}
async function drain() {
  mirroring = true;
  try {
    while (mirrorQ.size) {
      const [k, v] = mirrorQ.entries().next().value; mirrorQ.delete(k);
      const doc = S.realDb.collection('recover').doc(fileKey() + '~' + k);
      try { await doc.set(v.data === null ? { fk: fileKey(), coll: v.coll, id: v.id, seq: v.seq, deleted: true } : { fk: fileKey(), coll: v.coll, id: v.id, seq: v.seq, json: JSON.stringify(v.data) }); }
      catch (e) { mirrorFail++; }
    }
  } finally { mirroring = false; }
}
async function offerRecovery() {
  if (!S.realDb) return;
  try {
    const fk = fileKey(), st = await S.realDb.collection('recoverstate').doc(fk).get(), packedTo = st && st.exists && st.data() ? +st.data().lastPackedSeq || 0 : 0;
    const snap = await S.realDb.collection('recover').get(), got = [];
    snap.docs.forEach(d => { const x = d.data(); if (x && x.fk === fk && !x.deleted && x.json && x.seq > packedTo) { try { got.push({ coll: x.coll, id: x.id, seq: x.seq, data: JSON.parse(x.json) }); } catch (e) {} } });
    const dead = new Set(); snap.docs.forEach(d => { const x = d.data(); if (x && x.fk === fk && x.deleted) dead.add(x.coll + '.' + x.id); });
    const keep = got.filter(g => !dead.has(g.coll + '.' + g.id)).sort((a, b) => a.seq - b.seq);
    const runs = keep.filter(g => g.coll === 'runs');
    if (!runs.length) return;
    S.recoverable = keep;
    const el = $('#stRecover'); el.hidden = false;
    if (S.auto) { await recover(); el.hidden = false; $('#stRecoverBtn').hidden = true; $('#stRecoverTxt').textContent = 'Recovered ' + fmtN(runs.length) + (runs.length === 1 ? ' run' : ' runs') + ' that an earlier tab left undownloaded (' + fmtN(keep.length) + ' saved items); they go into the update folder below.'; return; }
    $('#stRecoverTxt').textContent = 'An earlier tab left ' + fmtN(runs.length) + (runs.length === 1 ? ' run' : ' runs') + ' from this file that was not downloaded (' + fmtN(keep.length) + ' saved items). Recover ' + (runs.length === 1 ? 'it' : 'them') + ' to pack them, or ignore this and press Update again.';
  } catch (e) { console.warn('recovery check failed', e); }
}
async function recover() {
  const items = S.recoverable || []; if (!items.length) return;
  S.recovering = true;
  try {
    S.seq = Math.max(S.seq, ...items.map(g => g.seq));
    for (const g of items) { const c = mem.collection(g.coll); if (!sess[g.coll] && g.coll !== 'clips') continue; await c.doc(g.id).set(g.data); }
  } finally { S.recovering = false; }
  S.recoverable = null; $('#stRecover').hidden = true; updatePackUi(); xdSoon();
}

/* ---------- step 1: read the file ---------- */
function showErr(msg) { const e = $('#stErr'); e.textContent = msg; e.hidden = !msg; }
function shortSha(s) { return s ? s.slice(0, 8) + '…' : ''; }
function setBlock(id, value, type) {
  let el = document.getElementById(id);
  if (!el) { el = document.createElement('script'); el.id = id; el.type = 'application/json'; document.body.appendChild(el); }
  el.textContent = JSON.stringify(value);
}
function validate(j) {
  if (!j || typeof j !== 'object' || Array.isArray(j)) return 'This is not a “for Update” file (it is not a JSON object).';
  if (j.format !== 'ajg-for-update') return 'This is not a “for Update” file made by the PC tracker (its format is ' + JSON.stringify(j.format) + ').';
  if (!Number.isInteger(j.format_version) || j.format_version < 1) return 'The file’s version is not understood.';
  if (j.format_version > 1) return 'This file is version ' + j.format_version + '; this station reads version 1. Open the newest station page.';
  const fp = j.fingerprint;
  if (!fp || typeof fp.workbook_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(fp.workbook_sha256)) return 'The file has no workbook fingerprint, so an update made from it could not be checked on the PC. Make a new file.';
  if (!Array.isArray(j.stories) || !j.stories.length) return 'The file lists no stories.';
  if (!j.rows || !Array.isArray(j.rows.rows) || !j.rows.rows.length) return 'The file lacks the list of spreadsheet rows (needed to avoid adding stories twice).';
  for (const k of ['idmap', 'covcols', 'billsinfo', 'fetchrules', 'ins_release_pickup', 'memory']) if (j[k] === undefined || j[k] === null) return 'The file lacks the “' + k + '” block. Make a new file.';
  return '';
}
function readFile(f) {
  return new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(String(r.result)); r.onerror = () => rej(r.error || new Error('could not read the file')); r.readAsText(f); });
}
async function loadFile(f) {
  if (S.loaded) return;
  showErr('');
  if (!f) return;
  let j;
  try { j = JSON.parse(await readFile(f)); } catch (e) { showErr('Could not read “' + f.name + '” as a “for Update” file: ' + (e && e.message ? e.message : e)); return; }
  const bad = validate(j);
  if (bad) { showErr(bad); return; }
  S.file = j; S.fileName = f.name; S.loadedAt = nowIso();
  // 1. the blocks, where the tracker code reads them
  $('#data').textContent = JSON.stringify(j.stories);
  setBlock('rows', j.rows); setBlock('idmap', j.idmap); setBlock('covcols', j.covcols); setBlock('billsinfo', j.billsinfo); if (!j.fetchrules.recall || typeof j.fetchrules.recall !== 'object') { try { j.fetchrules.recall = JSON.parse(document.getElementById('recall-default').textContent); S.recallDefault = true; } catch (e) { } }   // follow-up 9: a file made before RECALLFIX-v1 lacks the extra-search lists; the station's own copy of the same reference data stands in
  setBlock('fetchrules', j.fetchrules);
  setBlock('ins-release_pickup', j.ins_release_pickup);
  // 2. the button's memory
  const m = j.memory || {};
  Object.entries(m.runs || {}).forEach(([id, d]) => mem.seed('runs', id, d));
  Object.entries(m.clips || {}).forEach(([id, d]) => mem.seed('clips', id, d));
  Object.entries(m.reprints || {}).forEach(([id, d]) => mem.seed('reprints', id, d));
  (m.edits_removed || []).forEach(id => mem.seed('edits', id, { removed: true, at: '' }));
  // 3. now the tracker code
  try { S.realDb = realClaude && realClaude.use ? await realClaude.use('db') : null; } catch (e) { S.realDb = null; }
  S.loaded = true;
  // the tracker draws its Update panel only when it is opened; here it is always open, so open it once the run history has arrived
  const openPanel = () => { const b = $('#updBtn'); if (b) b.click(); };
  S.afterRunsSub = openPanel; setTimeout(() => { if (S.afterRunsSub) openPanel(); }, 6000);   // slow start: draw now, and once more when the history arrives
  const src = $('#tracker-src').textContent.replace(/<\\\/script/gi, '<' + '/script');
  const s = document.createElement('script');
  const nbScope = (document.getElementById('nb-scope-src') || {}).textContent || '';   // NEWSBANKPDF-v1: runs in the tracker's own scope
  // the tracker code is one function ((function(){ ... })();): the NewsBank code goes inside it, before its closing, so it sees covHit, dupOf, toRow ... as the Update code does
  const cut = src.lastIndexOf('})();');
  if (cut < 0) { S.loaded = false; showErr('The tracker code has an unexpected shape.'); return; }
  s.textContent = '(function(window){\n' + src.slice(0, cut) + '\n' + nbScope.replace(/<\\\/script/gi, '<' + '/script') + '\n' + src.slice(cut) + '\n})(window.__stationWin);';
  try { document.body.appendChild(s); } catch (e) { S.loaded = false; showErr('The tracker code did not start: ' + (e && e.message ? e.message : e)); return; }
  showLoaded();
  offerRecovery();
  try { const sm = realClaude && realClaude.use ? await realClaude.use('sample') : null; if (!sm) $('#stSampleNote').hidden = false; } catch (e) { $('#stSampleNote').hidden = false; }
}
function showLoaded() {
  const j = S.file, fp = j.fingerprint, m = j.memory || {};
  const facts = [
    ['File', esc(S.fileName)],
    ['Made', esc(j.created_at ? new Date(j.created_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : 'unknown')],
    ['Workbook', '<code>' + esc(shortSha(fp.workbook_sha256)) + '</code> ' + esc(fp.workbook_name || '')],
    ['Stories', esc(fmtN(j.stories.length) + ' in the tracker, ' + fmtN(j.rows.rows.length) + ' spreadsheet rows checked for duplicates')],
    ['Last full update searched to', esc(m.searched_to || 'no record')],
    ['Earlier finds waiting for a save', esc(fmtN(Object.keys(m.clips || {}).length) + ' stories, ' + fmtN(Object.keys(m.reprints || {}).length) + ' reprints')],
  ];
  if ((j.notes || []).length) console.info('for-Update file notes (not shown):', j.notes);
  $('#stFacts').innerHTML = facts.map(([k, v]) => '<dt>' + esc(k) + '</dt><dd>' + v + '</dd>').join('');
  $('#stDrop').hidden = true; $('#stLoaded').hidden = false;
  $('#st-step1').classList.add('st-done');
  ['#st-step2', '#st-step3', '#st-nb', '#st-pq'].forEach(s => { const el = $(s); if (el) el.classList.remove('st-lock'); });
  ['#nbFile', '#pqFile'].forEach(s => { const el = $(s); if (el) el.disabled = false; });
  showAge();
  $('#stStep2Cap').textContent = 'Press Update database. It searches the web for new stories about him (about 700 TinyFish searches, 25 minutes or more), checks them against the file, and fills in tone, authors and translations for each new one. Keep this tab open until it finishes.';
  const f = $('#runFind'); if (f) f.disabled = false;
  updatePackUi();
}
/* how old the for-Update file is: stories saved on the PC since then are not in it, so a Find could add them a second time */
function fileAgeDays(j, now) { const t = Date.parse(j && j.created_at); if (!isFinite(t)) return null; return Math.max(0, Math.floor(((now || Date.now()) - t) / 86400000)); }
function showAge() {
  const j = S.file, el = $('#stAge'), d = fileAgeDays(j, window.__stationNow ? window.__stationNow() : Date.now());
  const made = j.created_at ? new Date(j.created_at).toLocaleDateString(undefined, { dateStyle: 'medium' }) : '';
  let msg, old = false;
  if (d === null) { msg = 'This file does not say when it was made, so its age is unknown: make a fresh one from the PC tracker so stories saved since are not found again.'; old = true; }
  else { msg = 'File made ' + made + ' (' + (d === 0 ? 'today' : d === 1 ? '1 day old' : d + ' days old') + ').'; if (d > 7) { msg += ' This file is more than 7 days old: make a fresh one from the PC tracker so stories saved since are not found again.'; old = true; } }
  el.textContent = msg; el.classList.toggle('err', old); el.classList.toggle('st-age-old', old); el.hidden = false;
}
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function wireStep1() {
  const inp = $('#stFile'), drop = $('#stDrop');
  inp.addEventListener('change', () => { const f = inp.files && inp.files[0]; if (f) loadFile(f); });
  ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', e => { const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]; if (f) loadFile(f); });
  drop.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inp.click(); } });
  // a file dropped anywhere else on the page must not make the browser open it
  ['dragover', 'drop'].forEach(ev => window.addEventListener(ev, e => { if (!e.target.closest || !e.target.closest('#stDrop')) e.preventDefault(); }));
  let armed = false;
  $('#stAnother').addEventListener('click', () => {
    if (!armed) { armed = true; $('#stAnotherNote').hidden = false; return; }
    location.reload();
  });
}

/* ---------- step 3: pack ---------- */
const CRC_T = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(b) { let c = 0xFFFFFFFF; for (let i = 0; i < b.length; i++) c = CRC_T[(c ^ b[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
/* store-only zip writer: entries = [{name (ASCII), bytes}] -> Uint8Array */
function zipStore(entries) {
  const enc = new TextEncoder(), d = new Date();
  const dosTime = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1), dosDate = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
  const parts = [], central = []; let off = 0;
  const u16 = (v, a) => { a.push(v & 0xFF, (v >>> 8) & 0xFF); }, u32 = (v, a) => { a.push(v & 0xFF, (v >>> 8) & 0xFF, (v >>> 16) & 0xFF, (v >>> 24) & 0xFF); };
  for (const e of entries) {
    const name = enc.encode(e.name), crc = crc32(e.bytes), h = [];
    u32(0x04034b50, h); u16(20, h); u16(0x0800, h); u16(0, h); u16(dosTime, h); u16(dosDate, h); u32(crc, h); u32(e.bytes.length, h); u32(e.bytes.length, h); u16(name.length, h); u16(0, h);
    parts.push(new Uint8Array(h), name, e.bytes);
    const c = [];
    u32(0x02014b50, c); u16(20, c); u16(20, c); u16(0x0800, c); u16(0, c); u16(dosTime, c); u16(dosDate, c); u32(crc, c); u32(e.bytes.length, c); u32(e.bytes.length, c);
    u16(name.length, c); u16(0, c); u16(0, c); u16(0, c); u16(0, c); u32(0, c); u32(off, c);
    central.push(new Uint8Array(c), name);
    off += h.length + name.length + e.bytes.length;
  }
  const cdSize = central.reduce((a, p) => a + p.length, 0), end = [];
  u32(0x06054b50, end); u16(0, end); u16(0, end); u16(entries.length, end); u16(entries.length, end); u32(cdSize, end); u32(off, end); u16(0, end);
  const all = parts.concat(central, [new Uint8Array(end)]), out = new Uint8Array(all.reduce((a, p) => a + p.length, 0));
  let o = 0; all.forEach(p => { out.set(p, o); o += p.length; });
  return out;
}
async function sha256Hex(bytes) { const h = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)); return [...h].map(b => b.toString(16).padStart(2, '0')).join(''); }

/* which run docs go into the update: every run this session saved that finished or carries rows, bills, releases, print pages or lookups */
function runPackable(d) {
  const has = k => Array.isArray(d[k]) && d[k].length;
  const content = has('rows') || has('bills_new') || has('releases_new') || has('print_pages') || has('print_rows') || has('extra_copies') || has('lookups');
  if (d.status === 'running' || d.status === 'error') return content;
  return true;
}
function pending() {
  /* AUTOSTATION-v1 follow-up (CHAINFIX): a folder always holds EVERYTHING this session found, not only what came after the last download. A person who adds a PDF after the automatic download gets a new complete folder (it says it replaces the earlier one), never a partial one. `fresh` = runs saved since the last download. */
  const runs = [...sess.runs].filter(([id, v]) => runPackable(v.data)), fresh = runs.filter(([, v]) => v.seq > S.lastPacked).length;
  const stories = runs.reduce((a, [, v]) => a + ((v.data.stories || []).length), 0), reprints = runs.reduce((a, [, v]) => a + ((v.data.reprints || []).length), 0);
  const rows = runs.reduce((a, [, v]) => a + ((v.data.rows || []).length), 0);
  const running = runs.filter(([, v]) => v.data.status === 'running').length;
  return { runs, stories, reprints, rows, running, fresh };
}
/* STFIX 5: the tracker's Update button does nothing while a PDF add is running (its own busy flag is shared): say so, instead of a silent no-op. */
document.addEventListener('click', ev => {
  const b = ev.target && ev.target.closest ? ev.target.closest('#runFind, #rcYes') : null; if (!b || !S.loaded) return;
  const adding = (S.nb && (S.nb.busy || S.nb.reading)) || (S.pq && (S.pq.busy || S.pq.reading));
  if (adding) { ev.stopImmediatePropagation(); ev.preventDefault(); toastMsg('PDFs are being added or read. Press Update database again when that is done (the station adds PDFs and the web search one after the other).'); }
}, true);
function trackerBusy() { const f = $('#runFind'); return !!(f && (f.getAttribute('aria-busy') === 'true' || f.classList.contains('busy'))) || !!$('#updStop'); }
/* AUTOSTATION-v1: the station does the next step itself. Nothing here runs on a schedule: it reacts to what the person did (dropped PDFs, pressed Update) while this page is open.
   1. PDFs read and waiting -> added to the update (after any run that is going finishes); 2. everything finished and quiet for 6 s -> the update folder downloads; 3. an earlier tab's unsaved runs are recovered on load.
   A step that fails is not retried by itself (the same list of items, the same runs: the signature below); the buttons stay as the manual way. */
S.auto = (() => { try { return localStorage.getItem('ajg_station_auto') !== '0'; } catch (e) { return true; } })();
const autoSig = { nb: '', pq: '', pack: '', packAt: 0, packed: '' };
function autoTick() {
  if (!S.auto || !S.loaded || S.recovering) return;
  const nb = S.nb, pq = S.pq;
  if (!nb || !pq || nb.busy || nb.reading || pq.busy || pq.reading || S.busyPack || trackerBusy()) { autoSig.packAt = 0; return; }
  const np = nbPickable(), pp = pqPickable();
  if (np.length) { const sg = np.map(x => x.key).join('|'); if (sg !== autoSig.nb) { autoSig.nb = sg; nbAdd(); } return; }
  if (pp.length) { const sg = pp.map(x => x.key).join('|'); if (sg !== autoSig.pq) { autoSig.pq = sg; pqAdd(); } return; }
  const p = pending();
  if (!p.fresh || p.running) { autoSig.pack = ''; return; }
  const sg = p.runs.map(([id, v]) => id + ':' + v.seq).join('|');
  if (sg !== autoSig.pack) { autoSig.pack = sg; autoSig.packAt = Date.now(); return; }
  if (Date.now() - autoSig.packAt >= 6000 && sg !== autoSig.packed) { autoSig.packed = sg; pack(); }
}
function updatePackUi() {
  if (!S.loaded) return;
  const p = pending(), busy = trackerBusy();
  const parts = [];
  const nbN = S.nb ? [...sess.pages].filter(([, v]) => v.data && v.data.nb && v.data.nb.file).length : 0;
  const pqN = S.pq ? [...sess.pages].filter(([, v]) => v.data && v.data.pq && v.data.pq.header).length : 0;   // PROQUESTPDF-v1: story text copies from ProQuest PDFs
  if (p.runs.length) parts.push(fmtN(p.runs.length) + (p.runs.length === 1 ? ' run' : ' runs') + (nbN ? ' (' + fmtN(nbN) + ' NewsBank story PDFs)' : '') + (pqN ? ' (' + fmtN(pqN) + ' ProQuest PDFs)' : '') + ': ' + fmtN(p.stories) + ' new ' + (p.stories === 1 ? 'story' : 'stories') + ', ' + fmtN(p.reprints) + (p.reprints === 1 ? ' reprint' : ' reprints') + ' (' + fmtN(p.rows) + ' spreadsheet rows)');
  let msg = p.fresh ? 'Ready: ' + parts.join('') + '.' + (S.lastZip ? ' Something was added since the last download, so this folder is made again with everything in it; it replaces ' + S.lastZip.filename + '.' : '') : (S.lastZip ? 'The last update folder was downloaded. Nothing new since.' : 'Nothing to download yet. Press Update database in step 2.');
  if (busy) msg = 'A run is going. Download the update folder when it is done.';
  if (p.running && !busy) msg += ' One run was left unfinished; it is included as far as it got.';
  if (S.endedLast && !busy) msg += ' The web search did not finish (see the red note in step 2).';
  const st = $('#stPackStatus'); if (st.textContent !== msg) st.textContent = msg;
  $('#stPack').disabled = busy || S.busyPack || !p.fresh;
  $('#stPackAgain').hidden = !S.lastZip;
}
async function pack() {
  if (S.busyPack) return null;
  try { await xdReconcile(); } catch (e) { console.warn('cross-source check failed', e); }   // N7: a story two sources found is in the folder once
  const p = pending(); if (!p.fresh) return null;
  const replaces = S.lastZip ? S.lastZip.filename : '';
  S.busyPack = true; updatePackUi(); $('#stPackWarn').hidden = true; $('#stPackWarn').innerHTML = '';
  const warns = [];
  try {
    const enc = new TextEncoder(), blobs = [], seen = new Set();
    const add = (coll, id, data) => {
      const name = 'db/' + coll + '/' + id + '.json';
      if (!ID_RX.test(id) || RESERVED.has(id.split('.')[0].toUpperCase())) { warns.push('Left out ' + coll + ' document “' + id + '”: its name is not allowed in an update folder.'); return false; }
      if (seen.has(name.toLowerCase())) { warns.push('Left out a second ' + coll + ' document named “' + id + '”.'); return false; }
      seen.add(name.toLowerCase()); blobs.push({ name, bytes: enc.encode(JSON.stringify(data)) }); return true;
    };
    const pdfBlobs = [];   // NEWSBANKPDF-v1: each NewsBank story's own PDF travels as files/<id>.pdf; the pages doc says which (nb.file) and its sha256
    for (const [, v] of p.runs) if (v.data && Array.isArray(v.data.extra_copies) && v.data.extra_copies.length) {   // ORIGCOPIES-v1: a run's extra_copies name their PDFs (files/<id>.pdf) themselves
      const keep = [];
      for (const x of v.data.extra_copies) {
        const fid = String(x.file || '').replace(/^files\//, '').replace(/\.pdf$/, ''), pf = S.nb && S.nb.pdfs.get(fid);
        if (!pf || pf.sha256 !== x.pdf_sha256) { warns.push('The PDF kept as an extra copy of ' + (x.aid || 'a row') + ' is not in this tab any more: it is left out.'); continue; }
        if (!pdfBlobs.some(b => b.name === 'files/' + fid + '.pdf')) pdfBlobs.push({ name: 'files/' + fid + '.pdf', bytes: pf.bytes, kind: 'pdf' });
        keep.push(x);
      }
      v.data = Object.assign({}, v.data, { extra_copies: keep });
    }
    const runIds = [];
    for (const [id, v] of p.runs) if (add('runs', id, v.data)) runIds.push(id);
    if (!runIds.length) throw new Error('No run could be packed.');
    for (const c of PACK_COLLS.filter(x => x !== 'runs')) for (const [id, v] of sess[c]) {
      let data = v.data;
      const srcKey = data && data.nb && data.nb.file ? 'nb' : data && data.pq && data.pq.file ? 'pq' : '';   // PROQUESTPDF-v1: a ProQuest story's own PDF travels the same way (pages doc pq.file)
      if (c === 'pages' && srcKey) {
        const fid = String(data[srcKey].file).replace(/^files\//, '').replace(/\.pdf$/, ''), pf = S[srcKey] && S[srcKey].pdfs.get(fid);
        if (!pf || pf.sha256 !== data[srcKey].pdf_sha256) { warns.push('The PDF of “' + (data.title || id) + '” is not in this tab any more: ' + (srcKey === 'nb' ? 'its row goes in without a saved copy.' : 'its text copy goes in without the PDF.')); data = Object.assign({}, data, { [srcKey]: Object.assign({}, data[srcKey], { file: '', pdf_sha256: '', pdf_bytes: 0 }) }); }
        else if (!pdfBlobs.some(b => b.name === 'files/' + fid + '.pdf')) pdfBlobs.push({ name: 'files/' + fid + '.pdf', bytes: pf.bytes, kind: 'pdf' });
      }
      add(c, id, data);
    }
    // STATIONNAMES (LIBFILES-v1 follow-up 2): every file in the folder gets its library name (NAMING-v2), numbers from the file's rows.next, the best o/r guess
    const names = nameFiles(p, enc, pdfBlobs, warns);
    blobs.push(...pdfBlobs);
    for (const nf of names.blobs) { if (seen.has(nf.name.toLowerCase())) { warns.push('Left out a second file named “' + nf.name + '”.'); continue; } seen.add(nf.name.toLowerCase()); blobs.push(nf); }
    const files = {};
    for (const b of blobs) files[b.name] = Object.assign({ sha256: await sha256Hex(b.bytes), bytes: b.bytes.length }, b.kind ? { kind: b.kind } : {});
    const manifest = { format: 'ajg-update-folder', format_version: 1, created_at: nowIso(), source: { workbook_sha256: S.file.fingerprint.workbook_sha256 },
      runs: runIds.slice().sort(), files, names: names.block, station_version: STATION_VERSION, replaces, folder_number: (S.packN || 0) + 1, for_update_created_at: S.file.created_at || '', for_update_name: S.fileName || '' };
    const entries = [{ name: 'manifest.json', bytes: enc.encode(JSON.stringify(manifest, null, 1) + '\n') }].concat(blobs);
    const zip = zipStore(entries), zsha = await sha256Hex(zip);
    const stamp = manifest.created_at.replace(/[-:]/g, '').replace('T', '-').slice(0, 13);
    S.packN = (S.packN || 0) + 1;
    const filename = 'ajg_update_' + stamp + '_' + S.file.fingerprint.workbook_sha256.slice(0, 8) + (S.packN > 1 ? '_v' + S.packN : '') + '.zip';
    S.lastZip = { filename, zip, sha256: zsha, files: blobs.length, runs: runIds, manifest };
    S.lastPacked = S.seq;
    S.packedInfo = { at: manifest.created_at, runs: runIds, zip: filename };
    await saveFile(filename, zip);
    await recordPacked(runIds, filename, zsha, blobs.length);
    for (const [, v] of p.runs) if (v.data && v.data.ended_early) warns.push('A web search in this folder did not finish: ' + v.data.ended_early.why + '. The folder holds what it found; press Update database again for the rest.');
    const w = $('#stPackWarn'); if (warns.length) { w.innerHTML = warns.map(x => '<li>' + esc(x) + '</li>').join(''); w.hidden = false; }
    const n = $('#stPackNote'); n.hidden = false;
    n.textContent = filename + ' · ' + fmtN(Math.round(zip.length / 1024)) + ' KB · ' + blobs.length + ' files · made from workbook ' + shortSha(S.file.fingerprint.workbook_sha256) + '. If your browser asked, confirm the save.' + (replaces ? ' This folder holds everything found so far and replaces ' + replaces + ': bring in this one, not the earlier one. If the earlier one is already saved in the tracker, the tracker refuses this one (same runs, so nothing is added twice): make a new “for Update” file and run again.' : '');
    return S.lastZip;
  } catch (e) {
    const w = $('#stPackWarn'); w.innerHTML = '<li>' + esc('The update folder could not be made: ' + (e && e.message ? e.message : e)) + '</li>'; w.hidden = false;
    return null;
  } finally { S.busyPack = false; updatePackUi(); }
}
/* the names block and the files under their library names. A PDF that travels under a library name is taken out of pdfBlobs (it is in the folder once). */
function nameFiles(p, enc, pdfBlobs, warns) {
  const pagesObj = {}; for (const [id, v] of sess.pages) pagesObj[id] = v.data;
  const byCode = new Map(); (S.file.stories || []).forEach(x => { if (x && x.code) byCode.set(String(x.code).toLowerCase(), x.id); });
  const today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' });
  const pl = AJGNames.plan({ next: (S.file.rows && S.file.rows.next) || {}, today, pages: pagesObj, existingStories: new Set((S.file.stories || []).map(x => x.id)), storyOfCode: c => byCode.get(c) || '',
    runs: p.runs.map(([id, v]) => ({ id, at: v.data.at || '', rows: v.data.rows || [], releases_new: v.data.releases_new || [] })) });
  const blobs = [], bad = new Set();
  for (const f of pl.files) {
    if (f.kind === 'html') { blobs.push({ name: f.path, bytes: enc.encode(f.text), kind: 'html' }); continue; }
    const i = pdfBlobs.findIndex(b => b.name === f.pdfFor);
    if (i < 0) { bad.add(f.path); continue; }
    blobs.push({ name: f.path, bytes: pdfBlobs[i].bytes, kind: 'pdf' });
  }
  for (const f of pl.files) if (f.kind === 'pdf' && !bad.has(f.path)) { const i = pdfBlobs.findIndex(b => b.name === f.pdfFor); if (i >= 0) pdfBlobs.splice(i, 1); }
  const block = AJGNames.manifestBlock(pl, today);
  for (const it of block.items) for (const k of ['copy', 'raw', 'pdf']) if (it[k] && bad.has(it[k])) { it[k] = ''; if (k === 'pdf' || k === 'copy') it.pdf_for = ''; }
  block.items.forEach(it => { if (!it.copy && !it.raw && !it.pdf) it.pdf_for = ''; });
  return { block, blobs, plan: pl };
}
async function saveFile(filename, bytes) {
  const blob = new Blob([bytes], { type: 'application/zip' });
  let dl = null; try { dl = realClaude && realClaude.use ? await realClaude.use('downloads') : null; } catch (e) { dl = null; }
  if (dl) { try { await dl.save({ filename, data: blob }); return; } catch (e) { if (e && e.code === 'declined') return; if (e && e.code === 'rate_limited') { toastMsg('A download is already waiting for you to confirm.'); return; } } }
  const u = URL.createObjectURL(blob), a = document.createElement('a'); a.href = u; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 5000);
}
/* ---------- N7: one story found by two sources in this session is offered once ----------
   After any run is finished (and before the update folder is made) the session's proposed rows are compared across sources (the plan is made by src/newsbank.js, which has the tracker's own
   duplicate tests). The web find's row stays and takes the other source's links and citation into its blank cells (a story from two PDF sources: the one added first); another outlet's copy
   becomes a reprint row of the story that ran first. The folded row, its saved page and its tone/author/translation documents leave the update, and the reason is listed under "left out". */
S.xdFolds = []; S.xdNotes = new Map(); S.xdLog = []; let xdTimer = 0, xdBusy = false;
const SRC_LABEL = { nb: 'NewsBank', pq: 'ProQuest', pp: 'a newspaper page', web: 'the web search' };
const xdSrcOf = row => /newsbank/i.test(row['Data Source'] || '') ? 'nb' : /proquest/i.test(row['Data Source'] || '') ? 'pq' : /^print page/i.test(row['Data Source'] || '') ? 'pp' : 'web';
const xdBlank = v => v === undefined || v === null || String(v).trim() === '';
function xdSoon() { if (S.recovering) return; clearTimeout(xdTimer); xdTimer = setTimeout(() => { xdReconcile().catch(e => console.warn('cross-source check failed', e)); }, 400); }
const xdNoteOf = it => { const c = it && it.r && it.r.id; return c && S.xdNotes.has(c) ? ' ' + S.xdNotes.get(c) : ''; };
const XD_RM = ['Topic', 'Tone', 'Tone note', 'Tone rated by', 'Bills', '# of reprints', 'Translated Headline', 'Story in English', 'Mentions "Gabriel" in text', 'File name', 'Saved Copy?'];
async function xdReconcile() {
  if (xdBusy || !S.loaded || !window.__nb || !window.__nb.xdPlan) return 0;
  if (trackerBusy()) { xdSoon(); return 0; }   // STFIX 5: never rewrite run documents while a web run is going; try again a moment later
  xdBusy = true;
  try {
    const work = new Map(), dirty = new Set();
    const doc = id => { if (!work.has(id)) { const v = sess.runs.get(id); work.set(id, v ? clone(v.data) : null); } return work.get(id); };
    for (const [id] of sess.runs) doc(id);
    // a folded cell the web run's own later save wiped out is put back (blank cells only)
    for (const f of S.xdFolds) { const d = work.get(f.run), row = d && (d.rows || []).find(r => r['Article ID'] === f.aid); if (!row) continue; for (const [c, v] of Object.entries(f.cells)) if (xdBlank(row[c])) { row[c] = v; dirty.add(f.run); } }
    const ops = window.__nb.xdPlan([...work].filter(([, d]) => d && Array.isArray(d.rows)).map(([id, d]) => ({ id, at: d.at || '', status: d.status, rows: d.rows })));
    const gone = { pages: new Set(), authors: new Set(), translations: new Set(), tones: new Set() };
    let n = 0;
    for (const op of ops) {
      const pd = work.get(op.p.run), sd = work.get(op.s.run); if (!pd || !sd) continue;
      const prow = pd.rows.find(r => r['Article ID'] === op.p.aid), srow = sd.rows.find(r => r['Article ID'] === op.s.aid); if (!prow || !srow) continue;
      const sSid = srow['Story ID'] || '', sCode = String(srow['Tracker story code'] || ''), pSid = prow['Story ID'] || '', pCode = String(prow['Tracker story code'] || '');
      const kids = sSid ? sd.rows.filter(r => r !== srow && r['Original or reprint'] === 'Reprint' && r['Story ID'] === sSid) : [];
      const toP = String(pd.at || '') < String(sd.at || '');   // P's run comes first: its Original is placed before S's run is read, so S's rows can stay where they are
      const hl = String(srow['Headline'] || '').slice(0, 120), sl = SRC_LABEL[xdSrcOf(srow)], pl = SRC_LABEL[xdSrcOf(prow)];
      const place = rows => { rows.forEach(r => { r['Story ID'] = pSid; if (!toP) { sd.rows = sd.rows.filter(x => x !== r); pd.rows.push(r); } }); };
      if (op.kind === 'same') {
        const cells = {};
        for (const c of window.__nb.xdFold) if (xdBlank(prow[c]) && !xdBlank(srow[c])) { prow[c] = srow[c]; cells[c] = srow[c]; }
        if (cells['Publisher link'] && xdBlank(prow['Link status']) && srow['Link status']) { prow['Link status'] = srow['Link status']; cells['Link status'] = srow['Link status']; }
        prow['Team note'] = [prow['Team note'], 'also found by ' + sl + ' (“' + hl.slice(0, 80) + '”, ' + (srow['Date'] || '') + '): that copy was merged into this row'].filter(Boolean).join('; ').slice(0, 900);
        if (Object.keys(cells).length) S.xdFolds.push({ run: op.p.run, aid: op.p.aid, cells });
        sd.rows = sd.rows.filter(r => r !== srow);
        place(kids);
        sd.left = (sd.left || []).concat([{ hl: hl.slice(0, 200), outlet: String(srow['Outlet'] || '').slice(0, 120), date: srow['Date'] || '', why: 'the same story as the one ' + pl + ' found (' + op.why + '): shown once, its links and citation were added to that row' }]).slice(0, 150);
        [sCode, srow._page].filter(Boolean).forEach(k => { gone.pages.add(k); gone.authors.add(k); gone.translations.add(k); gone.tones.add(k); });
        S.xdNotes.set(sCode, 'Same story as one ' + pl + ' found: shown once (' + op.why + ').');
      } else {
        // another outlet's copy: it becomes a Reprint row of the story that ran first
        XD_RM.forEach(c => { delete srow[c]; });
        Object.assign(srow, { 'Original or reprint': 'Reprint', 'Story ID': pSid, 'Tracker story code': '', _page: srow._page || sCode });
        delete srow._origin; delete srow._found_by;
        srow['Team note'] = [srow['Team note'], 'also found by ' + sl + ': filed as a reprint of the story ' + pl + ' found (' + op.why + ')'].filter(Boolean).join('; ').slice(0, 900);
        if (!toP) { sd.rows = sd.rows.filter(r => r !== srow); pd.rows.push(srow); }
        place(kids);
        [sCode].filter(Boolean).forEach(k => { gone.authors.add(k); gone.translations.add(k); gone.tones.add(k); });
        const rp = { story: pCode, outlet: String(srow['Outlet'] || '').slice(0, 120) };
        pd.reprints = (pd.reprints || []).concat([rp].concat(kids.map(k => ({ story: pCode, outlet: String(k['Outlet'] || '').slice(0, 120) }))));
        S.xdNotes.set(sCode, 'Another outlet’s copy of a story ' + pl + ' found: filed as its reprint.');
      }
      if (sCode) { sd.stories = (sd.stories || []).filter(x => x !== sCode); sd.reprints = (sd.reprints || []).filter(x => !(x && x.story === sCode)); }
      if (op.kind === 'same' && kids.length) pd.reprints = (pd.reprints || []).concat(kids.map(k => ({ story: pCode, outlet: String(k['Outlet'] || '').slice(0, 120) })));
      dirty.add(op.p.run); dirty.add(op.s.run); n++;
      S.xdLog.push((op.kind === 'same' ? 'Shown once: ' : 'Filed as a reprint: ') + hl + ' (' + sl + ' and ' + pl + ')');
    }
    if (!dirty.size) return 0;
    for (const id of dirty) { const d = work.get(id); if (d) await mem.collection('runs').doc(id).set(d); }
    for (const [c, ids] of Object.entries(gone)) for (const id of ids) if (sess[c].has(id)) await mem.collection(c).doc(id).delete();
    const el = $('#stDupNote'); if (el && S.xdLog.length) { el.innerHTML = S.xdLog.map(x => '<li>' + esc(x) + '</li>').join(''); el.hidden = false; }
    if (n) toastMsg(n === 1 ? 'One story found by two sources is shown once.' : n + ' stories found by two sources are shown once.');
    updatePackUi(); if (typeof nbDrawAll === 'function') { nbDrawAll(); if (typeof pqDrawAll === 'function') pqDrawAll(); }
    return n;
  } finally { xdBusy = false; }
}
/*NB_UI*/
/*PQ_UI*/
function toastMsg(t) { const el = document.getElementById('toast'); if (!el) return; el.textContent = t; el.hidden = false; setTimeout(() => { el.hidden = true; }, 4000); }
/* the station's own record that these runs were packed (kept in the artifact's db when it is there; nothing is deleted) */
async function recordPacked(runIds, filename, zsha, nfiles) {
  try {
    if (!S.realDb && realClaude && realClaude.use) S.realDb = await realClaude.use('db');
    if (!S.realDb) return;
    await S.realDb.collection('recoverstate').doc(fileKey()).set({ lastPackedSeq: S.seq, at: nowIso(), zip: filename });
    for (const id of runIds) await S.realDb.collection('packed').doc(id).set({ run: id, packed_at: nowIso(), zip: filename, zip_sha256: zsha, files: nfiles, workbook_sha256: S.file.fingerprint.workbook_sha256, station_version: STATION_VERSION });
  } catch (e) { console.warn('could not record the pack in the station db', e); }
}

/* the tracker's own sentences that send the user to a chat for saving to the sheet do not apply here */
const TAKE = 'Download the update folder in step 3 to take it to the PC tracker.';
const FIX = [
  [/as batch PDFs into Documents\/Gabriel press PDFs, then ask Claude to extract them\./g, 'as batch PDFs, then drop them into “Add NewsBank PDFs” below.'],
  [/The finds are saved in this tracker\. To put (?:it|them) in the (?:sheet|spreadsheet), ask Claude in chat to “save the last run to the sheet”\./g, 'The finds are kept in this page until you download the update folder (step 3) and take it to the PC tracker.'],
  [/The sheet step \(done in chat\) applies this test to/g, 'The PC tracker applies this test, when the update folder is taken in, to'],
  [/Saved in the tracker, not in the sheet yet\. Ask Claude in chat to “save the last run to the sheet”\./g, 'Kept in this page, not yet taken to the PC tracker. Download the update folder in step 3.'],
  [/Saved in the tracker\. To put it in the sheet, ask Claude in chat to “save the last run to the sheet”\./g, 'Kept for the update folder. Download it in step 3 to take it to the PC tracker.'],
  [/(Added .+?)\. To put it in the sheet, ask Claude in chat to “save the last run to the sheet”\./g, '$1. Download the update folder in step 3 to take it to the PC tracker.'],
  [/Removed\. Its rows move to the spreadsheet’s Removed tab when you ask Claude in chat to “save the last run to the sheet”\./g, 'Removed. The PC tracker removes it when the update folder (step 3) is taken in.'],
  [/Changes show in the tracker at once and go into the spreadsheet/g, 'Changes show here at once and are saved'],
  [/Removing a story takes it out of the tracker at once; when that is saved its rows move to the spreadsheet’s Removed tab\./g, 'Removing a story takes it out of this list at once; the PC tracker removes it when the update folder is taken in.'],
  [/Searches the web for new coverage of Gabriel and saves what it finds in this tracker\. To put it in the master spreadsheet, ask Claude in chat afterwards\./g, 'Searches the web for new coverage of Gabriel and keeps what it finds in this page. Download the update folder in step 3 afterwards to take it to the PC tracker.'],
  [/To put (?:it|them) in the (?:sheet|spreadsheet), ask Claude in chat to “save the last run to the sheet”\./g, TAKE],
  [/Ask Claude in chat to “save the last run to the sheet”\./g, TAKE],
  [/when you ask Claude in chat to “save the last run to the sheet”/g, 'when the update folder (step 3) is taken in on the PC tracker'],
  [/Done\. Saved in the tracker\./g, 'Done. Kept for the update folder.'],
  [/Save them in the tracker/g, 'Keep them for the update folder'],
  [/Saved in the tracker\. Download/g, 'Kept for the update folder. Download'],
  [/Saving in the tracker/g, 'Keeping them for the update folder'],
  [/Nothing new to write\./g, 'Nothing new to keep.'],
  [/^(Added .+) to the tracker$/g, '$1 to the update'],
  [/placeholder IDs, not yet in the spreadsheet/g, 'IDs are given when the PC tracker saves it'],
  [/edited, not yet in the spreadsheet/g, 'edited, not yet taken to the PC tracker'],
  [/ not yet in the spreadsheet\. They go in with the next update\./g, ' will go into the update folder in step 3.'],
  [/^Spreadsheet rows/g, 'Rows for the PC tracker'],
  [/^Not confirmed \(not in the spreadsheet\)/g, 'Not confirmed (not added)'],
  [/^Find & refresh$/g, 'Run an update'],
  [/They’re in Clips now\./g, 'They’re kept for the update folder.'],
  [/The stories’ reprints now include them\./g, 'The reprints are kept for the update folder.'],
  [/ or use Edit details in a story's panel\./g, '.'],
  [/Added 0 clips\. (The reprints are kept)/g, '$1'],
  [/\bsearchs\b/g, 'searches'],
  [/^Team note$/g, 'Note'],   // NOTE-v1: the spreadsheet column keeps its header; people see "Note"
  [/^Has a team note$/g, 'Has a note'],
  [/ a team note$/g, ' a note'],
  [/^This story has a team note$/g, 'This story has a note'],
  [/Finding stories needs the tracker open in Claude with the TinyFish connector\. The clips you see are still current as of the last rebuild\./g, 'TinyFish is not available on this page. In claude.ai, connect TinyFish (Settings, Connectors), allow it for this page, then reload it and press Update database again.'],
  [/Finding stories needs the tracker open in Claude with connectors available\./g, 'TinyFish is not available on this page. In claude.ai, connect TinyFish (Settings, Connectors), allow it for this page, then reload it and press Update database again.'],
  [/TinyFish wasn’t allowed for this tracker\. Allow it from the artifact’s Permissions menu/g, 'TinyFish wasn’t allowed for this page. Allow it from this page’s Permissions menu'],
];
const FIX_RX = /to the tracker|saves what it finds|save the last run to the sheet|Gabriel press PDFs|in the tracker|in the spreadsheet|Spreadsheet rows|sheet step|Find & refresh|Clips now|reprints now include|story's panel|searchs|Team note|team note|Nothing new to write|Finding stories needs|allowed for this tracker|Changes show in the tracker/;
function fixTexts(root) {
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const hits = []; for (let n = w.nextNode(); n; n = w.nextNode()) if (FIX_RX.test(n.nodeValue)) hits.push(n);
  hits.forEach(n => { let t = n.nodeValue; FIX.forEach(([a, b]) => { t = t.replace(a, b); }); if (t !== n.nodeValue) n.nodeValue = t; });
  // buttons and paragraphs that point at parts the station does not have (Clips tab, Refresh from files, "Write them in now")
  root.querySelectorAll('[data-goclips], [data-logpush]').forEach(e => { e.hidden = true; });
  root.querySelectorAll('#upd p').forEach(p => { if (/^Refresh from files doesn’t search/.test(p.textContent)) p.hidden = true; });
}

function init() {
  const host = $('#stUpdHost'), upd = $('#upd');
  if (upd && host) host.appendChild(upd);
  const f = $('#runFind'); if (f) f.disabled = true;
  const sub = $('#subline'); if (sub) sub.innerHTML = 'Update<br>station';
  wireStep1();
  nbWire();
  pqWire();
  $('#stPack').addEventListener('click', () => { pack(); });
  $('#stRecoverBtn').addEventListener('click', () => { recover(); });
  $('#stPackAgain').addEventListener('click', async () => { if (S.lastZip) await saveFile(S.lastZip.filename, S.lastZip.zip); });
  let moT = 0;
  const mo = new MutationObserver(() => { clearTimeout(moT); moT = setTimeout(() => { fixTexts($('#st')); const t = document.getElementById('toast'); if (t) fixTexts(t); updatePackUi(); }, 150); });
  mo.observe($('#st'), { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['aria-busy', 'class'] });
  const tn = document.getElementById('toast'); if (tn) mo.observe(tn, { subtree: true, childList: true, characterData: true });
  setInterval(() => { const rc = document.getElementById('rcScrim'); if (rc && !rc.hidden) fixTexts(rc); }, 200);   // the confirm dialog is built by the tracker code after start
  setInterval(updatePackUi, 1000);
  const au = $('#stAuto'); if (au) { au.checked = S.auto; au.addEventListener('change', () => { S.auto = au.checked; try { localStorage.setItem('ajg_station_auto', S.auto ? '1' : '0'); } catch (e) { /* no storage: the choice lasts for this page only */ } }); }
  setInterval(autoTick, 1000);
  window.__station = { state: S, sess, pack, pending, zipStore, loadFile, xdReconcile, mem, mirrorBusy: () => mirroring || mirrorQ.size > 0, mirrorFail: () => mirrorFail };   // for the tests
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
