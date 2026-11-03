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
            async set(data) { const d = clone(data); if (name === 'runs' && d && Array.isArray(d.rows)) prAnnotateRows(d.rows, pg => col('pages').docs.get(pg)); c.docs.set(id, d); track(name, id, d); notify(c); },
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
/* proposed rows of a web run: the decision for each find, from its text and Claude's answer; "Yes" fills Press release (the PC save fills blanks only) */
function prAnnotateRows(rows, pageDoc) {
  (rows || []).forEach(r => {
    if (!r || r._pr) return;
    let rec = S.pr.get(prKey(r['Publisher link']));
    if (!rec && r._page && pageDoc) { const pd = pageDoc(r._page); if (pd && pd.clean) rec = { text: String(pd.clean).replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 6000), title: pd.title || '', claude: null }; }   // a reprint candidate is not classified by Claude: its saved page text is judged by the text signals
    if (!rec) return;
    const j = PRJudge.judge({ text: rec.text, title: rec.title, outlet: r['Outlet'], url: r['Publisher link'], claude: rec.claude, rel: window.__prRel() });
    r._pr = { v: j.v, why: j.why, by: j.by };
    if (j.v === 'yes') { r['Press release'] = 'Yes'; r['Team note'] = ('press release: ' + j.why + (r['Team note'] ? '; ' + r['Team note'] : '')).slice(0, 600); }
  });
}
function sampleWatch(f) {
  return new Proxy(f, {
    apply(t, th, a) { return Promise.resolve(t.apply(th, a)).catch(e => { sampleDenied(e); throw e; }); },
    get(t, k) { const v = t[k]; if (k === 'json' && typeof v === 'function') return (...a) => prCall(v, t, a).catch(e => { sampleDenied(e); throw e; }); return typeof v === 'function' ? v.bind(t) : v; },
  });
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
const winProxy = new Proxy(window, {
  get(t, k) { if (k === 'claude') return claudeForTracker; const v = t[k]; return typeof v === 'function' && !/^[A-Z]/.test(String(k)) ? v.bind(t) : v; },
  set(t, k, v) { t[k] = v; return true; },
  has(t, k) { return k in t; },
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
  S.recoverable = null; $('#stRecover').hidden = true; updatePackUi();
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
  const content = has('rows') || has('bills_new') || has('releases_new') || has('print_pages') || has('lookups');
  if (d.status === 'running' || d.status === 'error') return content;
  return true;
}
function pending() {
  const runs = [...sess.runs].filter(([id, v]) => v.seq > S.lastPacked && runPackable(v.data));
  const stories = runs.reduce((a, [, v]) => a + ((v.data.stories || []).length), 0), reprints = runs.reduce((a, [, v]) => a + ((v.data.reprints || []).length), 0);
  const rows = runs.reduce((a, [, v]) => a + ((v.data.rows || []).length), 0);
  const running = runs.filter(([, v]) => v.data.status === 'running').length;
  return { runs, stories, reprints, rows, running };
}
function trackerBusy() { const f = $('#runFind'); return !!(f && (f.getAttribute('aria-busy') === 'true' || f.classList.contains('busy'))) || !!$('#updStop'); }
function updatePackUi() {
  if (!S.loaded) return;
  const p = pending(), busy = trackerBusy();
  const parts = [];
  const nbN = S.nb ? [...sess.pages].filter(([, v]) => v.seq > S.lastPacked && v.data && v.data.nb && v.data.nb.file).length : 0;
  const pqN = S.pq ? [...sess.pages].filter(([, v]) => v.seq > S.lastPacked && v.data && v.data.pq && v.data.pq.header).length : 0;   // PROQUESTPDF-v1: story text copies from ProQuest PDFs
  if (p.runs.length) parts.push(fmtN(p.runs.length) + (p.runs.length === 1 ? ' run' : ' runs') + (nbN ? ' (' + fmtN(nbN) + ' NewsBank story PDFs)' : '') + (pqN ? ' (' + fmtN(pqN) + ' ProQuest PDFs)' : '') + ': ' + fmtN(p.stories) + ' new ' + (p.stories === 1 ? 'story' : 'stories') + ', ' + fmtN(p.reprints) + (p.reprints === 1 ? ' reprint' : ' reprints') + ' (' + fmtN(p.rows) + ' spreadsheet rows)');
  let msg = p.runs.length ? 'Ready: ' + parts.join('') + '.' : (S.lastZip ? 'The last update folder was downloaded. Nothing new since.' : 'Nothing to download yet. Press Update database in step 2.');
  if (busy) msg = 'A run is going. Download the update folder when it is done.';
  if (p.running && !busy) msg += ' One run was left unfinished; it is included as far as it got.';
  const st = $('#stPackStatus'); if (st.textContent !== msg) st.textContent = msg;
  $('#stPack').disabled = busy || S.busyPack || !p.runs.length;
  $('#stPackAgain').hidden = !S.lastZip;
}
async function pack() {
  if (S.busyPack) return null;
  const p = pending(); if (!p.runs.length) return null;
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
    const runIds = [];
    for (const [id, v] of p.runs) if (add('runs', id, v.data)) runIds.push(id);
    if (!runIds.length) throw new Error('No run could be packed.');
    const pdfBlobs = [];   // NEWSBANKPDF-v1: each NewsBank story's own PDF travels as files/<id>.pdf; the pages doc says which (nb.file) and its sha256
    for (const c of PACK_COLLS.filter(x => x !== 'runs')) for (const [id, v] of sess[c]) if (v.seq > S.lastPacked) {
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
      runs: runIds.slice().sort(), files, names: names.block, station_version: STATION_VERSION, for_update_created_at: S.file.created_at || '', for_update_name: S.fileName || '' };
    const entries = [{ name: 'manifest.json', bytes: enc.encode(JSON.stringify(manifest, null, 1) + '\n') }].concat(blobs);
    const zip = zipStore(entries), zsha = await sha256Hex(zip);
    const stamp = manifest.created_at.replace(/[-:]/g, '').replace('T', '-').slice(0, 13);
    const filename = 'ajg_update_' + stamp + '_' + S.file.fingerprint.workbook_sha256.slice(0, 8) + '.zip';
    S.lastZip = { filename, zip, sha256: zsha, files: blobs.length, runs: runIds, manifest };
    S.lastPacked = S.seq;
    S.packedInfo = { at: manifest.created_at, runs: runIds, zip: filename };
    await saveFile(filename, zip);
    await recordPacked(runIds, filename, zsha, blobs.length);
    const w = $('#stPackWarn'); if (warns.length) { w.innerHTML = warns.map(x => '<li>' + esc(x) + '</li>').join(''); w.hidden = false; }
    const n = $('#stPackNote'); n.hidden = false;
    n.textContent = filename + ' · ' + fmtN(Math.round(zip.length / 1024)) + ' KB · ' + blobs.length + ' files · made from workbook ' + shortSha(S.file.fingerprint.workbook_sha256) + '. If your browser asked, confirm the save.';
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
  [/Finding stories needs the tracker open in Claude with the TinyFish connector\. The clips you see are still current as of the last rebuild\./g, 'TinyFish is not available on this page. In claude.ai, connect TinyFish (Settings, Connectors), allow it for this page, then reload it and press Update database again.'],
  [/Finding stories needs the tracker open in Claude with connectors available\./g, 'TinyFish is not available on this page. In claude.ai, connect TinyFish (Settings, Connectors), allow it for this page, then reload it and press Update database again.'],
  [/TinyFish wasn’t allowed for this tracker\. Allow it from the artifact’s Permissions menu/g, 'TinyFish wasn’t allowed for this page. Allow it from this page’s Permissions menu'],
];
const FIX_RX = /to the tracker|saves what it finds|save the last run to the sheet|Gabriel press PDFs|in the tracker|in the spreadsheet|Spreadsheet rows|sheet step|Find & refresh|Clips now|reprints now include|story's panel|searchs|Nothing new to write|Finding stories needs|allowed for this tracker|Changes show in the tracker/;
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
  window.__station = { state: S, sess, pack, pending, zipStore, loadFile, mirrorBusy: () => mirroring || mirrorQ.size > 0, mirrorFail: () => mirrorFail };   // for the tests
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
