/* "Tracker files" panel (station layer). Plain JavaScript, no libraries, talks only to this PC's own server (same origin).
   Injected by station_server.py; the tracker's own sources are not edited. */
(function () {
  if (window.__ajgFiles) return;
  window.__ajgFiles = true;
  var TOKEN = window.__LOCAL_TOKEN || '';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var el = function (tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'text') e.textContent = attrs[k]; else if (k === 'class') e.className = attrs[k];
      else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2), attrs[k]); else e.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (c) { e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return e;
  };
  // TIDY-v1: the button is a masthead button (class upd-btn, like Spreadsheet and Manage); the panel opens pinned under the masthead at the right
  var CSS = '#ajgf-btn .tf-dot{width:9px;height:9px;border-radius:50%;background:#f0b44c;flex:none}#ajgf-btn .tf-dot[hidden]{display:none}' +
    '#ajgf{position:fixed;top:calc(var(--hdr,128px) + 4px);right:16px;z-index:2147483001;width:min(440px,calc(100vw - 32px));max-height:calc(100vh - var(--hdr,128px) - 20px);overflow:auto;background:#fff;color:#1b1f24;border:1px solid #9aa4b0;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.3);font:14px/1.45 system-ui,Segoe UI,sans-serif;padding:14px 16px;display:none}' +
    '#ajgf.open{display:block}#ajgf h2{margin:0 0 6px;font-size:16px}#ajgf h3{margin:14px 0 4px;font-size:14px}#ajgf p{margin:4px 0}' +
    '#ajgf .ajgf-b{font:600 13px system-ui,Segoe UI,sans-serif;padding:7px 12px;border-radius:6px;border:1px solid #1d4f91;background:#1d4f91;color:#fff;cursor:pointer;margin:4px 6px 4px 0}' +
    '#ajgf .ajgf-b.alt{background:#fff;color:#1d4f91}#ajgf .ajgf-b.danger{background:#a15c00;border-color:#a15c00}#ajgf .ajgf-b[disabled]{opacity:.5;cursor:default}' +
    '#ajgf .ajgf-note{background:#eef3f9;border-radius:6px;padding:7px 9px;margin:6px 0}#ajgf .ajgf-bad{background:#fdecea;color:#7a1a12;border-radius:6px;padding:7px 9px;margin:6px 0}' +
    '#ajgf .ajgf-warn{background:#fff4dd;color:#6b4300;border-radius:6px;padding:7px 9px;margin:6px 0}#ajgf .ajgf-ok{background:#e6f4ea;color:#14532d;border-radius:6px;padding:7px 9px;margin:6px 0}' +
    '#ajgf ul{margin:4px 0 4px 18px;padding:0}#ajgf .ajgf-drop{border:2px dashed #7b8794;border-radius:8px;padding:14px;text-align:center;margin:6px 0;color:#44505c}' +
    '#ajgf .ajgf-drop.over{background:#eef3f9;border-color:#1d4f91}#ajgf .ajgf-x{float:right;background:none;border:0;font-size:20px;cursor:pointer;color:#44505c}' +
    '#ajgf details.ajgf-rep{margin:10px 0 0}#ajgf details.ajgf-rep>summary{cursor:pointer;font-weight:600;font-size:14px;color:#1d4f91}#ajgf details.ajgf-rep[open]>summary{margin-bottom:6px}' +
    '#ajgf small{color:#5b6672}#ajgf hr{border:0;border-top:1px solid #d5dbe2;margin:12px 0}#ajgf label{display:block;margin:6px 0}';
  document.head.appendChild(el('style', { text: CSS }));

  function api(path, opt) {
    opt = opt || {};
    var h = { 'X-Local-Token': TOKEN };
    if (opt.json) { h['Content-Type'] = 'application/json'; opt.body = JSON.stringify(opt.json); opt.method = opt.method || 'POST'; }
    return fetch('/_local/station/' + path, { method: opt.method || 'GET', headers: h, body: opt.body }).then(function (r) {
      return r.text().then(function (t) { var j = null; try { j = JSON.parse(t); } catch (e) { } return { status: r.status, json: j, text: t }; });
    });
  }
  function runJob(path, body, onTick) {
    return api(path, { json: body || {} }).then(function (r) {
      if (!r.json || !r.json.job) { return { ok: false, line: (r.json && (r.json.line || r.json.error)) || ('The tracker did not accept that (' + r.status + ').') }; }
      return new Promise(function (resolve) {
        var t0 = Date.now();
        (function poll() {
          api('job/' + r.json.job).then(function (j) {
            if (j.json && j.json.state === 'done') return resolve(j.json.result || { ok: false, line: 'No answer.' });
            if (onTick) onTick(Math.round((Date.now() - t0) / 1000), j.json);
            setTimeout(poll, 1000);
          }).catch(function () { setTimeout(poll, 2000); });
        })();
      });
    });
  }
  function bytes(n) { return n > 1e6 ? (n / 1e6).toFixed(1) + ' MB' : Math.round(n / 1e3) + ' KB'; }

  // the masthead button: directly left of Manage, same class as its neighbours (Spreadsheet, Manage). Kept for keeper and reader copies alike.
  var FOLDER = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" focusable="false"><path d="M2 4.5h4l1.5 1.5H14v6.5H2z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>';
  var btn = el('button', { id: 'ajgf-btn', class: 'upd-btn', type: 'button', title: 'Tracker files: updates, refresh files and repairs', 'aria-expanded': 'false' });
  btn.innerHTML = FOLDER + '<span class="lbl">Tracker files</span><span class="tf-dot" hidden></span>';
  var box = el('div', { id: 'ajgf', role: 'dialog', 'aria-label': 'Tracker files' });
  function mountBtn() {
    var mg = $('#updBtn'), acts = mg && mg.parentNode;
    if (!acts) return false;
    acts.insertBefore(btn, mg); return true;
  }
  // an empty tracker (no workbook yet) shows a one-screen page with no masthead: the button then sits at the top right of that page by itself
  function mountFallback() {
    if (!$('#ajg-nowb')) return false;
    btn.setAttribute('style', 'position:fixed;top:14px;right:16px;z-index:2147483000;display:inline-flex;align-items:center;gap:6px;font:600 14px system-ui,Segoe UI,sans-serif;padding:8px 14px;border-radius:8px;border:1px solid #1d4f91;background:#1d4f91;color:#fff;cursor:pointer');
    document.body.appendChild(btn); return true;
  }
  if (!mountBtn()) { var tries = 0, tm = setInterval(function () { if (mountBtn() || (tries > 15 && mountFallback()) || ++tries > 100) clearInterval(tm); }, 100); }
  document.body.appendChild(box);
  var state = { status: null, update: null, makeMsg: null, busy: false, init: false, rebuildMsg: null, edits: null };

  function openBox(open) {
    box.classList.toggle('open', open); btn.setAttribute('aria-expanded', String(open));
    if (open) {     // the Manage panel is also fixed at the right: only one of the two is open at a time
      var mgp = $('#upd'); if (mgp && !mgp.hidden) { var x = $('[data-uclose]', mgp); if (x) x.click(); }
      refresh(); render();
    }
  }
  document.addEventListener('click', function (e) { if (box.classList.contains('open') && e.target.closest && e.target.closest('#updBtn')) openBox(false); }, true);

  btn.addEventListener('click', function () { openBox(!box.classList.contains('open')); });

  function refresh() {
    return api('status').then(function (r) {
      if (r.json) { state.status = r.json; var s = r.json, warn = (s.lock && s.lock.held) || (s.workbook && (s.workbook.excel_open || (s.role === 'keeper' && s.workbook.baseline !== 'ok')));
        var dot = $('.tf-dot', btn); if (dot) dot.hidden = !warn;
        // LASTUPDATED-v1: "Last updated <date>" as a third line of the masthead subtitle (same small-caps style; the date is Pacific, from the save ledger or the refresh file)
        var sl = document.getElementById('subline'), lu = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s.last_updated || '');
        if (sl && lu) { var sp = document.getElementById('ajg-lastupd'); if (!sp) { sl.appendChild(document.createElement('br')); sp = document.createElement('span'); sp.id = 'ajg-lastupd'; sl.appendChild(sp); }
          sp.textContent = 'Last updated ' + ['Jan.', 'Feb.', 'March', 'April', 'May', 'June', 'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.'][+lu[2] - 1] + ' ' + (+lu[3]) + ', ' + lu[1]; }
        btn.title = warn ? 'Tracker files: needs attention (Excel has the workbook open, the workbook changed, or a save is running)' : 'Tracker files: updates, refresh files and repairs';
        var nm = $('#ajg-nowb-msg');
        if (nm && s.workbook && !s.workbook.exists) {
          nm.textContent = s.role === 'keeper' ? 'No workbook yet: use Set up from the Mac library (Tracker files, top right).' : 'No workbook yet: bring in the refresh file the keeper gave you (Tracker files, top right).';
          if (!state.autoOpened) { state.autoOpened = true; openBox(true); }
        }
        var ae = document.activeElement;
        if (box.classList.contains('open') && !state.busy && !(ae && box.contains(ae) && /^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName))) render(); }
    }).catch(function () { });
  }
  setInterval(function () { if (box.classList.contains('open') && !state.busy) refresh(); }, 5000);
  refresh();

  // ------------------------------------------------------------ render
  var drop;
  function banners(parent) {
    var s = state.status; if (!s) { parent.appendChild(el('p', { text: 'Checking the tracker folder...' })); return; }
    var w = s.workbook || {};
    if (!w.exists) parent.appendChild(el('div', { class: 'ajgf-bad', id: 'ajgf-nowb', text: s.role === 'keeper' ? 'No workbook yet: use Set up from the Mac library (below).' : 'No workbook yet: bring in the refresh file the keeper gave you (below).' }));
    else parent.appendChild(el('p', {}, [el('small', { text: 'Workbook: ' + w.name + ', ' + bytes(w.bytes) + ', fingerprint ' + (w.sha256 || '').slice(0, 8) })]));
    if (w.excel_open) parent.appendChild(el('div', { class: 'ajgf-bad', text: 'Excel has the workbook open. Close it before you save an update or accept the workbook.' }));
    if (s.lock && s.lock.held) parent.appendChild(el('div', { class: 'ajgf-warn', text: 'Another save is running (' + (s.lock.by || 'another PC') + ', ' + Math.round(s.lock.age_minutes || 0) + ' minutes so far). Wait for it to finish. Saving and accepting are switched off until then.' }));
    var isK = s.role === 'keeper';
    parent.appendChild(el('p', {}, [el('small', { text: isK ? 'This is the keeper copy.' : 'This is a reader copy: it takes refresh files from the keeper.' })]));
    if (isK && w.exists && w.baseline === 'missing') parent.appendChild(el('div', { class: 'ajgf-warn', text: 'The tracker has not been told which workbook to trust yet. Open Repairs below and use "Accept the workbook as it is now" once.' }));
    if (isK && w.exists && w.baseline === 'changed') parent.appendChild(el('div', { class: 'ajgf-warn', text: 'The workbook is not the one the tracker last saved. Someone changed it outside the tracker (for example in Excel). If that was on purpose, open Repairs below and use "Accept the workbook as it is now". Until then, saving is refused.' }));
    if (isK && w.exists && w.baseline === 'unconfirmed') parent.appendChild(el('div', { class: 'ajgf-warn', text: 'The last save was never confirmed. Saving is refused until it is sorted out.' }));
    if (s.job && s.job.state === 'running') parent.appendChild(el('div', { class: 'ajgf-note', text: 'The tracker is working on: ' + s.job.verb + '.' }));
  }
  function locked() { var s = state.status || {}; return !!(s.lock && s.lock.held) || !!(s.workbook && s.workbook.excel_open); }

  function render() {
    box.textContent = '';
    box.appendChild(el('button', { class: 'ajgf-x', type: 'button', 'aria-label': 'Close', text: '×', onclick: function () { openBox(false); } }));
    box.appendChild(el('h2', { text: 'Tracker files' }));
    banners(box);
    var w0 = (state.status && state.status.workbook) || {};
    if (state.status && !w0.exists && state.status.role === 'keeper') {      // an empty keeper copy: only the setup makes sense
      renderSetupSection(box, false);
      return;
    }
    if (state.status && !w0.exists) {                                          // an empty reader copy: only a refresh file makes sense
      box.appendChild(el('h3', { text: 'Bring in refresh file' }));
      box.appendChild(el('p', { text: 'The keeper sends you a refresh file (a zip). Drop it here to bring in the workbook, article pages and page data.' }));
      var rt0 = el('div', { id: 'ajgf-rtake' }); box.appendChild(rt0); renderRefreshTake(rt0);
      return;
    }
    if (sg.stage === 'done' && sg.res && sg.res.ok) {      // the setup just finished: its summary stays until the panel is closed and opened again
      var sbox = el('div', { id: 'ajgf-setup-done' });
      sbox.appendChild(el('div', { class: 'ajgf-ok' }, [el('b', { text: sg.res.line || '' })]));
      var sul = el('ul'); (sg.res.lines || []).forEach(function (l) { sul.appendChild(el('li', { text: l })); }); sbox.appendChild(sul);
      sbox.appendChild(el('button', { class: 'ajgf-b', type: 'button', text: 'Reload the tracker', onclick: function () { location.reload(); } }));
      box.appendChild(sbox); box.appendChild(el('hr'));
    }
    // 1. make for update
    box.appendChild(el('h3', { text: '1. Make "for Update" file' }));
    box.appendChild(el('p', { text: 'A small file listing the stories the tracker already has (no article text). Load it into the Update station before pressing Update.' }));
    var mk = el('button', { class: 'ajgf-b', type: 'button', text: 'Make "for Update" file', onclick: doMake });
    if (state.busy) mk.disabled = true;
    box.appendChild(mk);
    var mm = el('div', { id: 'ajgf-make' }); box.appendChild(mm);
    if (state.makeMsg) mm.appendChild(state.makeMsg);
    box.appendChild(el('hr'));
    var keeper = !state.status || state.status.role === 'keeper';
    if (keeper) {
    // 2. bring in update
    box.appendChild(el('h3', { text: '2. Bring in update' }));
    var up = el('div', { id: 'ajgf-update' }); box.appendChild(up);
    renderUpdate(up);
    box.appendChild(el('hr'));
    // 3. save my edits (PCEDITS-v1)
    var ne = state.status && state.status.edits_pending ? state.status.edits_pending.n : 0;
    box.appendChild(el('h3', { text: '3. Save my edits' + (ne ? ' (' + ne + ')' : ' (0)') }));
    box.appendChild(el('p', { text: 'Stories you removed or edited in this tracker (Manage) are written into the workbook the next time you bring in an update. To save them without an update, use this. You see what will change first.' }));
    var ed = el('div', { id: 'ajgf-edits' }); box.appendChild(ed);
    renderEdits(ed, ne);
    box.appendChild(el('hr'));
    // 4. refresh file: one button (TIDY-v1); a full one is made automatically when an incremental one could not be complete
    box.appendChild(el('h3', { text: '4. Make refresh file (for the other copies)' }));
    box.appendChild(el('p', { text: 'After you save an update, make a refresh file and pass it to the others. It carries the workbook, the new article pages and the page data. Never your notes or views. The tracker makes a full one by itself when a short one could not be complete (the first time, or if a save is missing from its record).' }));
    var rm = el('div', { id: 'ajgf-rmake' });
    var rb = el('button', { class: 'ajgf-b', type: 'button', text: 'Make refresh file', onclick: function () { doRefreshMake(false); } });
    if (refreshBlocked()) rb.disabled = true;
    rm.appendChild(rb);
    box.appendChild(rm);
    if (state.rmMsg && !state.rmFull) box.appendChild(state.rmMsg);
    } else {
    box.appendChild(el('h3', { text: '2. Bring in refresh file' }));
    box.appendChild(el('p', { text: 'The keeper sends you a refresh file (a zip). Drop it here to bring your workbook, article pages and page data up to date. Your notes and saved views stay as they are.' }));
    var ap = state.status && state.status.refresh_applied;
    box.appendChild(el('p', {}, [el('small', { text: ap ? 'This copy has refresh ' + ap.seq + ' (' + ap.kind + ', made ' + ap.created_at + ').' : 'This copy has not had a refresh yet.' })]));
    box.appendChild(el('p', {}, [el('small', { id: 'ajgf-reader-edits', text: 'Stories you edit or remove here stay in this copy only. They are not saved to the workbook; only the keeper\'s edits are.' })]));
    var rt = el('div', { id: 'ajgf-rtake' }); box.appendChild(rt);
    renderRefreshTake(rt);
    }
    // Repairs (closed unless asked for or needed): rarely used steps
    var w = (state.status && state.status.workbook) || {};
    var need = keeper && w.exists && (w.baseline === 'missing' || w.baseline === 'changed' || w.baseline === 'unconfirmed');
    var rep = el('details', { class: 'ajgf-rep', id: 'ajgf-repairs' });
    if (state.repOpen || need || state.init) rep.setAttribute('open', '');
    rep.addEventListener('toggle', function () { state.repOpen = rep.open; });
    rep.appendChild(el('summary', { text: 'Repairs' }));
    rep.appendChild(el('p', {}, [el('small', { text: 'Rarely needed.' })]));
    if (keeper) {
      rep.appendChild(el('h3', { text: 'Accept the workbook as it is now' }));
      rep.appendChild(el('p', { text: 'Use this after you edited the workbook in Excel yourself. It tells the tracker to trust the file exactly as it is.' }));
      renderInit(rep);
      rep.appendChild(el('h3', { text: 'Make a full refresh file (for a new person)' }));
      rep.appendChild(el('p', { text: 'Carries everything, including the whole library. Bigger than the usual refresh file, so use it only for a copy that has never had one.' }));
      var fb = el('button', { class: 'ajgf-b alt', type: 'button', id: 'ajgf-full', text: 'Make a FULL refresh file', onclick: function () { doRefreshMake(true); } });
      if (refreshBlocked()) fb.disabled = true;
      rep.appendChild(fb);
      if (state.rmMsg && state.rmFull) rep.appendChild(state.rmMsg);
    }
    rep.appendChild(el('h3', { text: 'Rebuild the tracker page' }));
    rep.appendChild(el('p', { text: 'Rebuilds the page you are looking at from the workbook. Needed after a new workbook is copied into the folder.' }));
    var rbd = el('button', { class: 'ajgf-b alt', type: 'button', text: 'Rebuild the page', onclick: doRebuild });
    if (state.busy || locked()) rbd.disabled = true;
    rep.appendChild(rbd);
    if (state.rebuildMsg) rep.appendChild(state.rebuildMsg);
    if (keeper) {
      rep.appendChild(el('h3', { text: 'Rebuild saved copies from the library' }));
      rep.appendChild(el('p', { text: 'Use this when a story shows a saved copy that will not open. It reads your own library, adds every saved copy the tracker\'s article data does not hold yet, and changes nothing that is already there. Setup and every save do this by themselves; this button is for a second try.' }));
      var rcb = el('button', { class: 'ajgf-b alt', type: 'button', id: 'ajgf-rebuild-copies', text: 'Rebuild saved copies', onclick: doRebuildCopies });
      if (state.busy || locked()) rcb.disabled = true;
      rep.appendChild(rcb);
      if (state.copiesMsg) rep.appendChild(state.copiesMsg);
    }
    box.appendChild(el('hr'));
    box.appendChild(rep);
  }
  function refreshBlocked() { return state.busy || locked() || !!(state.status && state.status.workbook && state.status.workbook.baseline !== 'ok'); }

  function busyNote(parent, id) { var d = el('div', { class: 'ajgf-note', id: id || 'ajgf-tick' }); parent.appendChild(d); return d; }

  // ---- set up from the Mac library (SWITCHOVER-v1)
  var sg = { folder: '', list: '', listFile: null, stage: 'form', res: null, again: false };
  function renderSetupSection(parent, again) {
    var box_ = el('div', { id: again ? 'ajgf-setup2' : 'ajgf-setup' }); parent.appendChild(box_);
    if (!again) {
      box_.appendChild(el('h3', { text: 'Set up from the Mac library' }));
      box_.appendChild(el('p', { text: 'Copy the Mac\'s "Tracker library" folder onto this PC first (downloaded fully, not in a OneDrive folder). Then tell the tracker where it is and which fingerprint list the Mac made. Nothing in that folder is changed or moved: the tracker copies what it needs and checks every file.' }));
    }
    var busy = state.busy || locked();
    if (sg.stage === 'working') { var tk = busyNote(box_); tk.textContent = sg.msg || 'Working...'; return; }
    if (sg.stage === 'done' && sg.res) {
      var r = sg.res;
      box_.appendChild(el('div', { class: r.ok ? 'ajgf-ok' : 'ajgf-bad' }, [el('b', { text: r.line || '' })]));
      var ul = el('ul'); (r.lines || []).forEach(function (l) { ul.appendChild(el('li', { text: l })); }); box_.appendChild(ul);
      if (r.ok) {
        box_.appendChild(el('button', { class: 'ajgf-b', type: 'button', text: 'Reload the tracker', onclick: function () { location.reload(); } }));
      } else box_.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Close this', onclick: function () { sg.stage = 'form'; render(); } }));
      return;
    }
    var f1 = el('input', { type: 'text', id: again ? 'ajgf-folder2' : 'ajgf-folder', style: 'width:100%;box-sizing:border-box;padding:6px', placeholder: 'C:\\AJG Tracker\\Tracker library' });
    f1.value = sg.folder; f1.addEventListener('input', function () { sg.folder = f1.value; });
    box_.appendChild(el('label', {}, ['Folder of the copied "Tracker library" (type or paste the path; in Explorer, Shift + right-click the folder and choose "Copy as path")', f1]));
    var f2 = el('input', { type: 'text', id: again ? 'ajgf-list2' : 'ajgf-list', style: 'width:100%;box-sizing:border-box;padding:6px', placeholder: 'leave empty to use the list inside the folder' });
    f2.value = sg.list; f2.addEventListener('input', function () { sg.list = f2.value; });
    var pick = el('input', { type: 'file', accept: '.sha256,.txt', id: again ? 'ajgf-listfile2' : 'ajgf-listfile', onchange: function (e) { sg.listFile = e.target.files[0] || null; if (sg.listFile) { sg.list = ''; f2.value = ''; } } });
    box_.appendChild(el('label', {}, ['Fingerprint list the Mac made ("Tracker library manifest.sha256"): choose the file, or type its path', pick, f2]));
    if (again) {
      var cf = el('input', { type: 'checkbox', id: 'ajgf-again-ok' }); cf.checked = !!sg.againOk; cf.addEventListener('change', function () { sg.againOk = cf.checked; render(); });
      box_.appendChild(el('label', {}, [cf, ' I understand this replaces the workbook of this tracker.']));
    }
    var chk = el('button', { class: 'ajgf-b', type: 'button', id: again ? 'ajgf-setup-check2' : 'ajgf-setup-check', text: 'Check the files', onclick: function () { doSetupCheck(again); } });
    if (busy || (again && !sg.againOk)) chk.disabled = true;
    box_.appendChild(chk);
    if (sg.check) {
      var c = sg.check;
      box_.appendChild(el('div', { class: c.ok ? 'ajgf-ok' : 'ajgf-bad' }, [el('b', { text: c.line || '' })]));
      var u2 = el('ul'); (c.lines || []).forEach(function (l) { u2.appendChild(el('li', { text: l })); }); box_.appendChild(u2);
      if (c.ok) {
        var go = el('button', { class: 'ajgf-b danger', type: 'button', id: again ? 'ajgf-setup-run2' : 'ajgf-setup-run', text: again ? 'Copy and replace the workbook' : 'Copy and set up', onclick: function () { doSetupRun(again); } });
        if (busy) go.disabled = true;
        box_.appendChild(go);
        box_.appendChild(el('p', {}, [el('small', { text: 'This copies about the size of the whole library and builds the page. It takes several minutes. Do not close the Terminal or command window.' })]));
      }
    }
  }
  function setupBody(again) {
    var b = { folder: sg.folder };
    if (!again) { } else b.repairs = true;
    return b;
  }
  function withList(b) {
    if (sg.listFile) {
      var fl = sg.listFile;
      return fetch('/_local/station/upload?kind=manifest&name=' + encodeURIComponent(fl.name), { method: 'POST', headers: { 'X-Local-Token': TOKEN }, body: fl })
        .then(function (r) { return r.json(); }).then(function (j) { if (!j || !j.ok) throw new Error((j && (j.error || j.line)) || 'The fingerprint list could not be sent.'); b.list_upload = j.file; return b; });
    }
    if (sg.list.trim()) b.list = sg.list.trim();
    return Promise.resolve(b);
  }
  function doSetupCheck(again) {
    sg.check = null; sg.stage = 'working'; sg.msg = 'Checking every file against the list. This takes a minute or two...'; state.busy = true; render();
    withList(setupBody(again)).then(function (b) {
      return runJob('setup_check', b, function (s) { sg.msg = 'Checking every file against the list... ' + s + ' s'; render(); });
    }).then(function (r) { state.busy = false; sg.stage = 'form'; sg.check = r; render(); })
      .catch(function (e) { state.busy = false; sg.stage = 'form'; sg.check = { ok: false, line: String(e.message || e) }; render(); });
  }
  function doSetupRun(again) {
    sg.stage = 'working'; sg.msg = 'Copying and checking. This takes several minutes. Do not close the Terminal or command window...'; state.busy = true; render();
    withList(setupBody(again)).then(function (b) {
      return runJob('setup_run', b, function (s) { sg.msg = 'Copying and checking... ' + s + ' s. Do not close the Terminal or command window.'; render(); });
    }).then(function (r) { state.busy = false; sg.stage = 'done'; sg.res = r; sg.check = null; refresh().then(render); })
      .catch(function (e) { state.busy = false; sg.stage = 'done'; sg.res = { ok: false, line: String(e.message || e) }; render(); });
  }

  // ---- make
  function doMake() {
    state.busy = true; state.makeMsg = null; render();
    var n = $('#ajgf-make'); var tick = busyNote(n); tick.textContent = 'Making the file. This takes about a minute...';
    runJob('make', {}, function (s) { tick.textContent = 'Making the file... ' + s + ' s'; }).then(function (r) {
      state.busy = false;
      if (!r.ok) { state.makeMsg = el('div', { class: 'ajgf-bad', text: r.line || 'The file could not be made.' }); render(); return; }
      return api('for_update/' + encodeURIComponent(r.name)).then(function (g) {
        // the file arrives as text; hand it to the browser as a normal download
        var a = el('a', { href: URL.createObjectURL(new Blob([g.text], { type: 'application/json' })), download: r.name });
        document.body.appendChild(a); a.click(); a.remove();
        var m = el('div', { class: 'ajgf-ok' }, [el('div', { text: r.line }), el('div', {}, [el('small', { text: 'Saved in your Downloads folder as ' + r.name + ' (also kept in data\\for_update).' })])]);
        (r.notes || []).slice(0, 3).forEach(function (t) { m.appendChild(el('div', {}, [el('small', { text: t })])); });
        state.makeMsg = m; render();
      });
    });
  }

  // ---- bring in update
  function renderUpdate(up) {
    var u = state.update;
    if (!u) {
      drop = el('div', { class: 'ajgf-drop' }, ['Drop the update zip here, or ', el('label', { style: 'display:inline;color:#1d4f91;text-decoration:underline;cursor:pointer' }, ['choose a file', el('input', { type: 'file', accept: '.zip', style: 'display:none', onchange: function (e) { if (e.target.files[0]) takeFile(e.target.files[0]); } })])]);
      ['dragenter', 'dragover'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('over'); }); });
      ['dragleave', 'drop'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('over'); }); });
      drop.addEventListener('drop', function (e) { var f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]; if (f) takeFile(f); });
      up.appendChild(drop);
      return;
    }
    if (u.working) { var t = busyNote(up); t.textContent = u.working; return; }
    if (u.error) { up.appendChild(el('div', { class: 'ajgf-bad', text: u.error })); up.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Start over', onclick: resetUpdate })); return; }
    if (u.stage === 'needs_confirm') {
      up.appendChild(el('div', { class: 'ajgf-warn' }, [el('b', { text: 'Warning. ' }), u.line]));
      up.appendChild(el('button', { class: 'ajgf-b danger', type: 'button', text: 'Use it anyway', onclick: function () { useAnyway(); } }));
      up.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Do not use it', onclick: function () { discard(); } }));
      return;
    }
    if (u.stage === 'previewed') {
      up.appendChild(el('div', { class: u.can_save ? 'ajgf-note' : 'ajgf-bad' }, [el('b', { text: u.headline || 'Preview' })]));
      if (u.accepted) up.appendChild(el('div', { class: 'ajgf-warn', text: 'You chose to use an update made from an older workbook. The save still runs all its checks.' }));
      var ul = el('ul'); (u.lines || []).forEach(function (l) { ul.appendChild(el('li', { text: l })); }); up.appendChild(ul);
      if ((u.needs_person || []).length) {
        up.appendChild(el('p', {}, [el('b', { text: 'Items that need a person (' + (u.needs_person_total || u.needs_person.length) + '):' })]));
        var ul2 = el('ul'); u.needs_person.forEach(function (l) { ul2.appendChild(el('li', { text: l })); }); up.appendChild(ul2);
        up.appendChild(el('p', {}, [el('small', { text: 'They are saved as they are and listed for you; the save does not decide them.' })]));
      }
      (u.warnings || []).forEach(function (w) { up.appendChild(el('div', { class: 'ajgf-warn', text: w })); });
      var sv = el('button', { class: 'ajgf-b', type: 'button', text: 'Save', onclick: doSave });
      if (!u.can_save || locked() || state.busy || (state.status && state.status.workbook && state.status.workbook.baseline !== 'ok')) sv.disabled = true;
      up.appendChild(sv);
      up.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Do not use this update', onclick: discard }));
      return;
    }
    if (u.stage === 'saved') {
      up.appendChild(el('div', { class: u.written ? 'ajgf-ok' : 'ajgf-bad' }, [el('b', { text: u.headline })]));
      var l3 = el('ul'); (u.lines || []).forEach(function (l) { l3.appendChild(el('li', { text: l })); }); up.appendChild(l3);
      (u.warnings || []).forEach(function (w) { up.appendChild(el('div', { class: 'ajgf-warn', text: w })); });
      if (u.written) { up.appendChild(el('p', { text: 'Reloading the tracker...' })); }
      else up.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Close this', onclick: resetUpdate }));
    }
  }
  function resetUpdate() { state.update = null; render(); refresh(); }
  function setUpdate(u) { state.update = u; render(); }

  function takeFile(file) {
    if (!/\.zip$/i.test(file.name)) { setUpdate({ error: 'That is not a .zip file. Drop the update zip from the Update station.' + (/\.[A-Za-z0-9]{1,5}$/.test(file.name) ? '' : ' If it is a folder, Safari may have unzipped it: use the .zip (turn off Safari > Settings > General > Open safe files after downloading).') }); return; }
    state.busy = true; setUpdate({ working: 'Sending ' + file.name + ' (' + bytes(file.size) + ') to the tracker...' });
    fetch('/_local/station/upload?name=' + encodeURIComponent(file.name), { method: 'POST', headers: { 'X-Local-Token': TOKEN }, body: file })
      .then(function (r) { return r.json().then(function (j) { return { status: r.status, j: j }; }); })
      .then(function (r) {
        if (!r.j || !r.j.ok) { state.busy = false; return setUpdate({ error: (r.j && (r.j.error || r.j.line)) || 'The file could not be sent.' }); }
        setUpdate({ working: 'Checking the update...' });
        return runJob('inspect', { file: r.j.file }, function (s) { setUpdate({ working: 'Checking the update and working out what it would change... ' + s + ' s' }); }).then(function (res) {
          state.busy = false; handleInspect(res);
        });
      }).catch(function () { state.busy = false; setUpdate({ error: 'The file could not be sent to the tracker. Is the tracker\'s Terminal or command window still open?' }); });
  }
  function handleInspect(res) {
    if (!res.ok) return setUpdate({ error: res.line || 'The update was refused.' });
    var u = Object.assign({}, res, { stage: res.stage });
    if (res.stage === 'needs_confirm') u.stage = 'needs_confirm';
    setUpdate(u);
  }
  function useAnyway() {
    var u = state.update; state.busy = true; setUpdate({ working: 'Working out what the update would change...' });
    runJob('preview', { update_id: u.update_id, accept_mismatch: true }, function (s) { setUpdate({ working: 'Working out what the update would change... ' + s + ' s' }); }).then(function (res) {
      state.busy = false;
      if (!res.ok) return setUpdate({ error: res.line || 'The preview failed.' });
      res.accepted = true; res.update_id = res.update_id || u.update_id; res.stage = 'previewed'; setUpdate(res);
    });
  }
  function discard() {
    var u = state.update; if (!u || !u.update_id) return resetUpdate();
    api('reject', { json: { update_id: u.update_id } }).then(function () { resetUpdate(); });
  }
  function doSave() {
    var u = state.update; state.busy = true; var keep = u;
    setUpdate({ working: 'Saving. The tracker backs up the workbook first, then writes. This can take a few minutes. Do not close the Terminal or command window...' });
    runJob('save', { update_id: u.update_id, token: u.token, accept_mismatch: !!u.accepted }, function (s) { setUpdate({ working: 'Saving... ' + s + ' s. Do not close the Terminal or command window.' }); }).then(function (res) {
      state.busy = false; res.stage = 'saved'; setUpdate(res); refresh();
      if (res.written) setTimeout(function () { location.reload(); }, 3500);
    });
  }

  // ---- save my edits (PCEDITS-v1): preview in words, then Save; same refusals as any save
  function renderEdits(parent, n) {
    var e = state.edits;
    if (!e) {
      var b = el('button', { class: 'ajgf-b', type: 'button', id: 'ajgf-edits-go', text: 'Save my edits (' + n + ')', onclick: doEditsPreview });
      if (!n || state.busy || locked() || (state.status && state.status.workbook && state.status.workbook.baseline !== 'ok')) b.disabled = true;
      parent.appendChild(b);
      if (!n) parent.appendChild(el('p', {}, [el('small', { text: 'No edits or removals are waiting.' })]));
      return;
    }
    if (e.working) { var t = busyNote(parent); t.textContent = e.working; return; }
    if (e.stage === 'previewed') {
      parent.appendChild(el('div', { class: e.can_save ? 'ajgf-note' : 'ajgf-bad' }, [el('b', { text: e.headline || 'Preview' })]));
      var ul = el('ul'); (e.lines || []).forEach(function (l) { ul.appendChild(el('li', { text: l })); }); parent.appendChild(ul);
      if ((e.needs_person || []).length) {
        parent.appendChild(el('p', {}, [el('b', { text: 'Items that need a person (' + (e.needs_person_total || e.needs_person.length) + '):' })]));
        var u2 = el('ul'); e.needs_person.forEach(function (l) { u2.appendChild(el('li', { text: l })); }); parent.appendChild(u2);
      }
      (e.warnings || []).forEach(function (w) { parent.appendChild(el('div', { class: 'ajgf-warn', text: w })); });
      var sv = el('button', { class: 'ajgf-b', type: 'button', id: 'ajgf-edits-save', text: 'Save', onclick: doEditsSave });
      if (!e.can_save || locked() || state.busy || (state.status && state.status.workbook && state.status.workbook.baseline !== 'ok')) sv.disabled = true;
      parent.appendChild(sv);
      parent.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Not now', onclick: function () { state.edits = null; render(); } }));
      return;
    }
    if (e.stage === 'saved') {
      parent.appendChild(el('div', { class: e.written ? 'ajgf-ok' : 'ajgf-bad' }, [el('b', { text: e.headline })]));
      var u3 = el('ul'); (e.lines || []).forEach(function (l) { u3.appendChild(el('li', { text: l })); }); parent.appendChild(u3);
      (e.warnings || []).forEach(function (w) { parent.appendChild(el('div', { class: 'ajgf-warn', text: w })); });
      if (e.written) parent.appendChild(el('p', { text: 'Reloading the tracker...' }));
      else parent.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Close this', onclick: function () { state.edits = null; render(); } }));
      return;
    }
    if (e.error) { parent.appendChild(el('div', { class: 'ajgf-bad', text: e.error })); parent.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Close this', onclick: function () { state.edits = null; render(); } })); }
  }
  function setEdits(e) { state.edits = e; render(); }
  function doEditsPreview() {
    state.busy = true; setEdits({ working: 'Working out what your edits would change...' });
    runJob('edits_preview', {}, function (s) { setEdits({ working: 'Working out what your edits would change... ' + s + ' s' }); }).then(function (res) {
      state.busy = false;
      if (!res.ok) return setEdits({ error: res.line || 'The preview failed.' });
      res.stage = 'previewed'; setEdits(res);
    });
  }
  function doEditsSave() {
    var e = state.edits; state.busy = true;
    setEdits({ working: 'Saving. The tracker backs up the workbook first, then writes. This can take a few minutes. Do not close the Terminal or command window...' });
    runJob('edits_save', { update_id: e.update_id, token: e.token }, function (s) { setEdits({ working: 'Saving... ' + s + ' s. Do not close the Terminal or command window.' }); }).then(function (res) {
      state.busy = false; res.stage = 'saved'; setEdits(res); refresh();
      if (res.written) setTimeout(function () { location.reload(); }, 3500);
    });
  }

  // ---- refresh (keeper makes, reader takes)
  function doRefreshMake(full) {
    state.busy = true; state.rmMsg = null; state.rmFull = !!full; if (full) state.repOpen = true; render();
    var tk = busyNote((full ? $('#ajgf-repairs') : $('#ajgf-rmake')) || box); tk.textContent = 'Making the refresh file. A full one can take several minutes...';
    runJob('refresh_make', { full: full }, function (s, jb) { tk.textContent = 'Making the refresh file... ' + s + ' s' + (jb && jb.stalled ? '. Nothing has moved for ' + jb.stalled + ' s. If it stays stuck the tracker will stop it by itself and say so.' : ''); }).then(function (r) {
      state.busy = false;
      if (!r.ok) { state.rmMsg = el('div', { class: 'ajgf-bad', text: r.line || 'The refresh file could not be made.' }); render(); return; }
      var href = '/_local/station/refresh_out/' + encodeURIComponent(r.name) + '?t=' + encodeURIComponent(TOKEN);
      var a = el('a', { href: href, download: r.name }); document.body.appendChild(a); a.click(); a.remove();
      state.rmMsg = el('div', { class: 'ajgf-ok' }, [el('div', { text: r.line }), el('div', {}, [el('small', { text: 'It downloads to your Downloads folder. A copy is kept in data\\refresh_out. Pass it to the others on the shared drive, OneDrive or a USB stick (it can be too big for email or Teams).' })])]);
      render();
    });
  }
  var rtState = null;
  function renderRefreshTake(parent) {
    if (rtState && rtState.working) { var t = busyNote(parent); t.textContent = rtState.working; return; }
    if (rtState && rtState.result) {
      var r = rtState.result;
      parent.appendChild(el('div', { class: r.ok ? 'ajgf-ok' : 'ajgf-bad', text: r.line || '' }));
      if (r.lines) { var ul = el('ul'); r.lines.forEach(function (l) { ul.appendChild(el('li', { text: l })); }); parent.appendChild(ul); }
      if (r.ok) parent.appendChild(el('p', { text: 'Reloading the tracker...' }));
      else parent.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Close this', onclick: function () { rtState = null; render(); } }));
      return;
    }
    var d = el('div', { class: 'ajgf-drop' }, ['Drop the refresh zip here, or ', el('label', { style: 'display:inline;color:#1d4f91;text-decoration:underline;cursor:pointer' }, ['choose a file', el('input', { type: 'file', accept: '.zip', style: 'display:none', onchange: function (e) { if (e.target.files[0]) takeRefresh(e.target.files[0]); } })])]);
    ['dragenter', 'dragover'].forEach(function (ev) { d.addEventListener(ev, function (e) { e.preventDefault(); d.classList.add('over'); }); });
    ['dragleave', 'drop'].forEach(function (ev) { d.addEventListener(ev, function (e) { e.preventDefault(); d.classList.remove('over'); }); });
    d.addEventListener('drop', function (e) { var f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]; if (f) takeRefresh(f); });
    if (locked() || (state.status && state.status.workbook && state.status.workbook.excel_open)) parent.appendChild(el('div', { class: 'ajgf-warn', text: 'Close Excel (and wait for any save to finish) before bringing in a refresh.' }));
    parent.appendChild(d);
  }
  function takeRefresh(file) {
    if (!/\.zip$/i.test(file.name)) { rtState = { result: { ok: false, line: 'That is not a .zip file. Drop the refresh zip the keeper gave you.' + (/\.[A-Za-z0-9]{1,5}$/.test(file.name) ? '' : ' If it is a folder, Safari may have unzipped it: use the .zip (turn off Safari > Settings > General > Open safe files after downloading).') } }; render(); return; }
    state.busy = true; rtState = { working: 'Sending ' + file.name + ' (' + bytes(file.size) + ') to the tracker...' }; render();
    fetch('/_local/station/upload?kind=refresh&name=' + encodeURIComponent(file.name), { method: 'POST', headers: { 'X-Local-Token': TOKEN }, body: file })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok) { state.busy = false; rtState = { result: { ok: false, line: (j && (j.error || j.line)) || 'The file could not be sent.' } }; return render(); }
        rtState = { working: 'Checking the refresh and bringing it in. A big one takes a few minutes. Do not close the Terminal or command window...' }; render();
        return runJob('refresh_take', { file: j.file }, function (s, jb) { rtState = { working: 'Bringing in the refresh... ' + s + ' s' + (jb && jb.stalled ? '. Nothing has moved for ' + jb.stalled + ' s. If it stays stuck the tracker will stop it by itself and say so.' : '. Do not close the Terminal or command window.') }; render(); }).then(function (res) {
          state.busy = false; rtState = { result: res }; render(); refresh();
          if (res.ok) setTimeout(function () { location.reload(); }, 3500);
        });
      }).catch(function () { state.busy = false; rtState = { result: { ok: false, line: 'The file could not be sent to the tracker. Is the tracker\'s Terminal or command window still open?' } }; render(); });
  }

  // ---- accept the workbook
  function renderInit(parent) {
    var w = (state.status && state.status.workbook) || {};
    var d = el('div'); parent.appendChild(d);
    if (state.init) {
      d.appendChild(el('div', { class: 'ajgf-warn' }, [el('b', { text: 'Are you sure? ' }), 'The tracker will trust the workbook exactly as it is now (fingerprint ' + (w.sha256 || '').slice(0, 8) + '). If another person edited it, their edits become part of the tracker. Excel must be closed.']));
      d.appendChild(el('button', { class: 'ajgf-b danger', type: 'button', text: 'Yes, accept it', onclick: function () {
        state.busy = true; state.init = false; var tk = busyNote(d); tk.textContent = 'Accepting...';
        runJob('init', { sha: w.sha256 }).then(function (r) { state.busy = false; state.initMsg = el('div', { class: r.ok ? 'ajgf-ok' : 'ajgf-bad', text: r.line }); refresh().then(render); });
      } }));
      d.appendChild(el('button', { class: 'ajgf-b alt', type: 'button', text: 'Cancel', onclick: function () { state.init = false; render(); } }));
    } else {
      var b = el('button', { class: 'ajgf-b alt', type: 'button', text: 'Accept the workbook as it is now', onclick: function () { state.init = true; state.initMsg = null; render(); } });
      if (state.busy || !w.exists || w.excel_open || (state.status.lock && state.status.lock.held)) b.disabled = true;
      d.appendChild(b);
      if (state.initMsg) d.appendChild(state.initMsg);
    }
  }
  // ---- rebuild saved copies from the library (A11)
  function doRebuildCopies() {
    state.busy = true; state.copiesMsg = null; render();
    var tk = busyNote(box); tk.textContent = 'Reading the library. This can take a few minutes...';
    runJob('rebuild_copies', {}, function (s) { tk.textContent = 'Reading the library... ' + s + ' s'; }).then(function (r) {
      state.busy = false;
      var kids = (r.lines && r.lines.length ? r.lines : [r.line || '']).map(function (t) { return el('div', { text: t }); });
      if (r.ok && r.added) kids.push(el('button', { class: 'ajgf-b', type: 'button', text: 'Reload the tracker', onclick: function () { location.reload(); } }));
      state.copiesMsg = el('div', { class: r.ok ? 'ajgf-ok' : 'ajgf-bad' }, kids);
      render();
    });
  }
  // ---- rebuild
  function doRebuild() {
    state.busy = true; state.rebuildMsg = null; render();
    var tk = busyNote(box); tk.textContent = 'Rebuilding the page. This takes about a minute...';
    runJob('rebuild', {}, function (s) { tk.textContent = 'Rebuilding the page... ' + s + ' s'; }).then(function (r) {
      state.busy = false;
      state.rebuildMsg = el('div', { class: r.ok ? 'ajgf-ok' : 'ajgf-bad' }, [r.line || '', r.ok ? el('button', { class: 'ajgf-b', type: 'button', text: 'Reload the tracker', onclick: function () { location.reload(); } }) : '']);
      render();
    });
  }
})();
