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
  var CSS = '#ajgf-btn{position:fixed;right:14px;bottom:14px;z-index:2147483000;font:600 13px system-ui,Segoe UI,sans-serif;padding:9px 14px;border-radius:20px;border:1px solid #1d4f91;background:#1d4f91;color:#fff;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)}' +
    '#ajgf-btn.warn{background:#a15c00;border-color:#a15c00}' +
    '#ajgf{position:fixed;right:14px;bottom:60px;z-index:2147483001;width:min(440px,calc(100vw - 28px));max-height:calc(100vh - 80px);overflow:auto;background:#fff;color:#1b1f24;border:1px solid #9aa4b0;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.3);font:14px/1.45 system-ui,Segoe UI,sans-serif;padding:14px 16px;display:none}' +
    '#ajgf.open{display:block}#ajgf h2{margin:0 0 6px;font-size:16px}#ajgf h3{margin:14px 0 4px;font-size:14px}#ajgf p{margin:4px 0}' +
    '#ajgf .ajgf-b{font:600 13px system-ui,Segoe UI,sans-serif;padding:7px 12px;border-radius:6px;border:1px solid #1d4f91;background:#1d4f91;color:#fff;cursor:pointer;margin:4px 6px 4px 0}' +
    '#ajgf .ajgf-b.alt{background:#fff;color:#1d4f91}#ajgf .ajgf-b.danger{background:#a15c00;border-color:#a15c00}#ajgf .ajgf-b[disabled]{opacity:.5;cursor:default}' +
    '#ajgf .ajgf-note{background:#eef3f9;border-radius:6px;padding:7px 9px;margin:6px 0}#ajgf .ajgf-bad{background:#fdecea;color:#7a1a12;border-radius:6px;padding:7px 9px;margin:6px 0}' +
    '#ajgf .ajgf-warn{background:#fff4dd;color:#6b4300;border-radius:6px;padding:7px 9px;margin:6px 0}#ajgf .ajgf-ok{background:#e6f4ea;color:#14532d;border-radius:6px;padding:7px 9px;margin:6px 0}' +
    '#ajgf ul{margin:4px 0 4px 18px;padding:0}#ajgf .ajgf-drop{border:2px dashed #7b8794;border-radius:8px;padding:14px;text-align:center;margin:6px 0;color:#44505c}' +
    '#ajgf .ajgf-drop.over{background:#eef3f9;border-color:#1d4f91}#ajgf .ajgf-x{float:right;background:none;border:0;font-size:20px;cursor:pointer;color:#44505c}' +
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
            if (onTick) onTick(Math.round((Date.now() - t0) / 1000));
            setTimeout(poll, 1000);
          }).catch(function () { setTimeout(poll, 2000); });
        })();
      });
    });
  }
  function bytes(n) { return n > 1e6 ? (n / 1e6).toFixed(1) + ' MB' : Math.round(n / 1e3) + ' KB'; }

  var btn = el('button', { id: 'ajgf-btn', type: 'button', text: 'Tracker files', 'aria-expanded': 'false' });
  var box = el('div', { id: 'ajgf', role: 'dialog', 'aria-label': 'Tracker files' });
  document.body.appendChild(btn); document.body.appendChild(box);
  var state = { status: null, update: null, makeMsg: null, busy: false, init: false, rebuildMsg: null };

  btn.addEventListener('click', function () {
    var open = !box.classList.contains('open'); box.classList.toggle('open', open); btn.setAttribute('aria-expanded', String(open));
    if (open) { refresh(); render(); }
  });

  function refresh() {
    return api('status').then(function (r) {
      if (r.json) { state.status = r.json; var s = r.json, warn = (s.lock && s.lock.held) || (s.workbook && (s.workbook.excel_open || (s.role === 'keeper' && s.workbook.baseline !== 'ok')));
        btn.classList.toggle('warn', !!warn); if (box.classList.contains('open') && !state.busy) render(); }
    }).catch(function () { });
  }
  setInterval(function () { if (box.classList.contains('open') && !state.busy) refresh(); }, 5000);
  refresh();

  // ------------------------------------------------------------ render
  var drop;
  function banners(parent) {
    var s = state.status; if (!s) { parent.appendChild(el('p', { text: 'Checking the tracker folder...' })); return; }
    var w = s.workbook || {};
    if (!w.exists) parent.appendChild(el('div', { class: 'ajgf-bad', text: 'The workbook is not in the tracker folder (data\\workbook). Ask Claude or Sammy to put it there.' }));
    else parent.appendChild(el('p', {}, [el('small', { text: 'Workbook: ' + w.name + ', ' + bytes(w.bytes) + ', fingerprint ' + (w.sha256 || '').slice(0, 8) })]));
    if (w.excel_open) parent.appendChild(el('div', { class: 'ajgf-bad', text: 'Excel has the workbook open. Close it before you save an update or accept the workbook.' }));
    if (s.lock && s.lock.held) parent.appendChild(el('div', { class: 'ajgf-warn', text: 'Another save is running (' + (s.lock.by || 'another PC') + ', ' + Math.round(s.lock.age_minutes || 0) + ' minutes so far). Wait for it to finish. Saving and accepting are switched off until then.' }));
    var isK = s.role === 'keeper';
    parent.appendChild(el('p', {}, [el('small', { text: isK ? 'This is the keeper copy.' : 'This is a reader copy: it takes refresh files from the keeper.' })]));
    if (isK && w.exists && w.baseline === 'missing') parent.appendChild(el('div', { class: 'ajgf-warn', text: 'The tracker has not been told which workbook to trust yet. Use "Accept the workbook as it is now" below once.' }));
    if (isK && w.exists && w.baseline === 'changed') parent.appendChild(el('div', { class: 'ajgf-warn', text: 'The workbook is not the one the tracker last saved. Someone changed it outside the tracker (for example in Excel). If that was on purpose, use "Accept the workbook as it is now" below. Until then, saving is refused.' }));
    if (isK && w.exists && w.baseline === 'unconfirmed') parent.appendChild(el('div', { class: 'ajgf-warn', text: 'The last save was never confirmed. Saving is refused until it is sorted out.' }));
    if (s.job && s.job.state === 'running') parent.appendChild(el('div', { class: 'ajgf-note', text: 'The tracker is working on: ' + s.job.verb + '.' }));
  }
  function locked() { var s = state.status || {}; return !!(s.lock && s.lock.held) || !!(s.workbook && s.workbook.excel_open); }

  function render() {
    box.textContent = '';
    box.appendChild(el('button', { class: 'ajgf-x', type: 'button', 'aria-label': 'Close', text: '×', onclick: function () { box.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); } }));
    box.appendChild(el('h2', { text: 'Tracker files' }));
    banners(box);
    // 1. make for update
    box.appendChild(el('h3', { text: '1. Make "for Update" file' }));
    box.appendChild(el('p', { text: 'A small file that tells Claude which stories the tracker already has (no article text). Drag it into the Update station.' }));
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
    // 3. accept workbook
    box.appendChild(el('h3', { text: '3. Accept the workbook as it is now' }));
    box.appendChild(el('p', { text: 'Use this after you edited the workbook in Excel yourself. It tells the tracker to trust the file exactly as it is.' }));
    renderInit(box);
    box.appendChild(el('hr'));
    box.appendChild(el('h3', { text: '4. Make refresh file (for the other copies)' }));
    box.appendChild(el('p', { text: 'After you save an update, make a refresh file and pass it to the others. It carries the workbook, the new article pages and the page data. Never your notes or views.' }));
    var rm = el('div', { id: 'ajgf-rmake' });
    [['Make refresh file', false], ['Make FULL refresh (for a new person)', true]].forEach(function (x) {
      var b = el('button', { class: 'ajgf-b' + (x[1] ? ' alt' : ''), type: 'button', text: x[0], onclick: function () { doRefreshMake(x[1]); } });
      if (state.busy || locked() || (state.status && state.status.workbook && state.status.workbook.baseline !== 'ok')) b.disabled = true;
      rm.appendChild(b);
    });
    box.appendChild(rm);
    if (state.rmMsg) box.appendChild(state.rmMsg);
    box.appendChild(el('hr'));
    } else {
    box.appendChild(el('h3', { text: '2. Bring in refresh file' }));
    box.appendChild(el('p', { text: 'The keeper sends you a refresh file (a zip). Drop it here to bring your workbook, article pages and page data up to date. Your notes and saved views stay as they are.' }));
    var ap = state.status && state.status.refresh_applied;
    box.appendChild(el('p', {}, [el('small', { text: ap ? 'This copy has refresh ' + ap.seq + ' (' + ap.kind + ', made ' + ap.created_at + ').' : 'This copy has not had a refresh yet.' })]));
    var rt = el('div', { id: 'ajgf-rtake' }); box.appendChild(rt);
    renderRefreshTake(rt);
    box.appendChild(el('hr'));
    }
    box.appendChild(el('h3', { text: keeper ? '5. Rebuild the tracker page' : '3. Rebuild the tracker page' }));
    box.appendChild(el('p', { text: 'Rebuilds the page you are looking at from the workbook. Needed after a new workbook is copied into the folder.' }));
    var rb = el('button', { class: 'ajgf-b alt', type: 'button', text: 'Rebuild the page', onclick: doRebuild });
    if (state.busy || locked()) rb.disabled = true;
    box.appendChild(rb);
    if (state.rebuildMsg) box.appendChild(state.rebuildMsg);
  }

  function busyNote(parent, id) { var d = el('div', { class: 'ajgf-note', id: id || 'ajgf-tick' }); parent.appendChild(d); return d; }

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
    if (!/\.zip$/i.test(file.name)) { setUpdate({ error: 'That is not a .zip file. Drop the update zip that Claude gave you.' }); return; }
    state.busy = true; setUpdate({ working: 'Sending ' + file.name + ' (' + bytes(file.size) + ') to the tracker...' });
    fetch('/_local/station/upload?name=' + encodeURIComponent(file.name), { method: 'POST', headers: { 'X-Local-Token': TOKEN }, body: file })
      .then(function (r) { return r.json().then(function (j) { return { status: r.status, j: j }; }); })
      .then(function (r) {
        if (!r.j || !r.j.ok) { state.busy = false; return setUpdate({ error: (r.j && (r.j.error || r.j.line)) || 'The file could not be sent.' }); }
        setUpdate({ working: 'Checking the update...' });
        return runJob('inspect', { file: r.j.file }, function (s) { setUpdate({ working: 'Checking the update and working out what it would change... ' + s + ' s' }); }).then(function (res) {
          state.busy = false; handleInspect(res);
        });
      }).catch(function () { state.busy = false; setUpdate({ error: 'The file could not be sent to the tracker. Is the black tracker window still open?' }); });
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
    setUpdate({ working: 'Saving. The tracker backs up the workbook first, then writes. This can take a few minutes. Do not close the black window...' });
    runJob('save', { update_id: u.update_id, token: u.token, accept_mismatch: !!u.accepted }, function (s) { setUpdate({ working: 'Saving... ' + s + ' s. Do not close the black window.' }); }).then(function (res) {
      state.busy = false; res.stage = 'saved'; setUpdate(res); refresh();
      if (res.written) setTimeout(function () { location.reload(); }, 3500);
    });
  }

  // ---- refresh (keeper makes, reader takes)
  function doRefreshMake(full) {
    state.busy = true; state.rmMsg = null; render();
    var tk = busyNote($('#ajgf-rmake') || box); tk.textContent = 'Making the refresh file. A full one can take several minutes...';
    runJob('refresh_make', { full: full }, function (s) { tk.textContent = 'Making the refresh file... ' + s + ' s'; }).then(function (r) {
      state.busy = false;
      if (!r.ok) { state.rmMsg = el('div', { class: 'ajgf-bad', text: r.line || 'The refresh file could not be made.' }); render(); return; }
      var href = '/_local/station/refresh_out/' + encodeURIComponent(r.name) + '?t=' + encodeURIComponent(TOKEN);
      var a = el('a', { href: href, download: r.name }); document.body.appendChild(a); a.click(); a.remove();
      state.rmMsg = el('div', { class: 'ajgf-ok' }, [el('div', { text: r.line }), el('div', {}, [el('small', { text: 'It downloads to your Downloads folder. A copy is kept in data\\refresh_out. Pass it to the others (shared drive, email or Teams).' })])]);
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
    if (!/\.zip$/i.test(file.name)) { rtState = { result: { ok: false, line: 'That is not a .zip file. Drop the refresh zip the keeper gave you.' } }; render(); return; }
    state.busy = true; rtState = { working: 'Sending ' + file.name + ' (' + bytes(file.size) + ') to the tracker...' }; render();
    fetch('/_local/station/upload?kind=refresh&name=' + encodeURIComponent(file.name), { method: 'POST', headers: { 'X-Local-Token': TOKEN }, body: file })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok) { state.busy = false; rtState = { result: { ok: false, line: (j && (j.error || j.line)) || 'The file could not be sent.' } }; return render(); }
        rtState = { working: 'Checking the refresh and bringing it in. A big one takes a few minutes. Do not close the black window...' }; render();
        return runJob('refresh_take', { file: j.file }, function (s) { rtState = { working: 'Bringing in the refresh... ' + s + ' s. Do not close the black window.' }; render(); }).then(function (res) {
          state.busy = false; rtState = { result: res }; render(); refresh();
          if (res.ok) setTimeout(function () { location.reload(); }, 3500);
        });
      }).catch(function () { state.busy = false; rtState = { result: { ok: false, line: 'The file could not be sent to the tracker. Is the black tracker window still open?' } }; render(); });
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
